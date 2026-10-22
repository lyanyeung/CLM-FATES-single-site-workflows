#!/usr/bin/env python3
"""Stage31: AmeriFlux BASE-derived ZBOT policy SCENARIOS, not DATM approval.

Rules authorized by user for Batch01:
- one candidate air-temperature height, no dated changes -> STATIC;
- confirmed-source dated sequence of heights -> DYNAMIC (provisional);
- before first dated TA epoch, use FIRST KNOWN TA height as a model ASSUMPTION;
- if a year/month date is incomplete, compare earliest vs latest possible
  change dates instead of silently fabricating an exact installation day;
- CA-Cbo, CA-Man or other multi-layer TA mappings without a unique candidate
  remain BLOCKED, never substitute EC/WS tower heights.

Source mapping is still a BASE-variable HYPOTHESIS, not verified FLUXNET TA_F.
Outputs policy JSON, audit CSV and annual sensitivity counts only. No 30-min
NetCDF, DATM, source, forcing, surface, CIME or Slurm files are modified.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path(__file__).resolve().parents[1]
BASE_CSV = HOME / "metadata" / "BASE_MeasurementHeight_20260908.csv"
SITES_TSV = HOME.parent / "AmeriFlux_MultiSite_10" / "sites.tsv"
REPORTS = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
SHA256 = "1c1e4171d295406a13d503f877b58661a651c88ffb6f0b6ec498f56bb1fcec5a"
SCENARIO = "PROVISIONAL_SOURCE_HEIGHT_ASSUMPTION_NOT_APPROVED"


def read(path: Path, sep=","):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        d=csv.DictReader(f,delimiter=sep)
        if not d.fieldnames:raise RuntimeError("CSV header missing: "+str(path))
        return set(d.fieldnames),list(d)


def write(path,rows,columns):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        w.writeheader();w.writerows(rows)


def hash_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(1024*1024),b""):h.update(buf)
    return h.hexdigest()


def numerical_height(v):
    try:x=float(v)
    except (ValueError,TypeError):return None
    return x if np.isfinite(x) and .5<=x<=150 else None


def window(v):
    raw=str(v or "").strip().replace("-","").replace("/","").replace(" ","")
    if not raw:return ("UNDATED",None,None)
    if not raw.isdigit():return ("BAD_DATE",None,None)
    try:
        if len(raw)==4:
            y=int(raw)
            return ("YEAR_ONLY",pd.Timestamp(y,1,1),pd.Timestamp(y+1,1,1))
        if len(raw)==6:
            y,m=int(raw[:4]),int(raw[4:6])
            start=pd.Timestamp(y,m,1)
            return ("MONTH_ONLY",start,start+pd.offsets.MonthBegin(1))
        if len(raw)==8:
            x=pd.to_datetime(raw,format="%Y%m%d",errors="raise")
            return ("DAY_EXACT",x,x)
        if len(raw)==12:
            x=pd.to_datetime(raw,format="%Y%m%d%H%M",errors="raise")
            return ("MINUTE_EXACT",x,x)
    except (OverflowError,ValueError,TypeError):
        pass
    return ("BAD_DATE",None,None)


def choose_candidate(groups):
    """A unique PI-style or exact TA variable is only a candidate crosswalk."""
    pi=sorted(v for v in groups if v=="TA_PI_F" or v.startswith("TA_PI_F_"))
    if len(pi)==1:return pi[0],"SINGLE_PI_ALIAS_HYPOTHESIS"
    if len(pi)>1:return None,"CONFLICTING_PI_ALIASES"
    if "TA" in groups:return "TA","DIRECT_TA_ALIAS_HYPOTHESIS"
    return None,"MULTI_LAYER_NO_TA_PI_OR_TA_ALIAS"


def records_for_site(site,rows):
    groups=defaultdict(list)
    for r in rows:
        if r["Site_ID"]==site and r["Variable"].upper().startswith("TA"):
            groups[r["Variable"].upper()].append(r)
    return groups


def events_from_records(site,variable,records):
    """Deduplicate identical metadata; retain event provenance and ambiguities."""
    missing=set()
    dates=defaultdict(set)
    duplicates=defaultdict(int)
    events=[]
    for r in records:
        h=numerical_height(r["Height"])
        if h is None:raise RuntimeError(site+": invalid chosen TA height")
        precision,earliest,latest=window(r["Start_Date"])
        if precision=="BAD_DATE":
            raise RuntimeError(site+": invalid date for "+variable+": "+r["Start_Date"])
        if precision=="UNDATED":
            missing.add(h)
            continue
        key=(precision,str(r["Start_Date"]).strip(),earliest,latest)
        dates[key].add(h)
        duplicates[(key,h)]+=1
    for key,heights in dates.items():
        if len(heights)!=1:
            raise RuntimeError(site+": conflicting heights at one start date: "+str(key))
        h=next(iter(heights))
        precision,raw,earliest,latest=key
        events.append(dict(site=site,variable=variable,
                           raw_Start_Date=raw,date_precision=precision,
                           earliest_possible=earliest,latest_upper_bound=latest,
                           height_m=h,source_duplicate_records=duplicates[(key,h)],
                           date_rule="EARLIEST_AND_LATEST_SENSITIVITY_NOT_EXACT_DATE"))
    events.sort(key=lambda r:r["earliest_possible"])
    if len(missing)>1:
        raise RuntimeError(site+": multiple mutually inconsistent undated baseline heights")
    if events:
        baseline=next(iter(missing)) if missing else events[0]["height_m"]
        baseline_type=("EXPLICIT_UNDATED_BASE_HEIGHT_CARRIED_OVER_ALL_EARLIER_YEARS"
                       if missing else "FIRST_DATED_HEIGHT_BACKFILLED_BEFORE_FIRST_EVENT")
    elif len(missing)==1:
        baseline=next(iter(missing))
        baseline_type="UNDATED_ONLY_STATIC_HEIGHT_ASSUMED_FOR_ALL_MODEL_YEARS"
    else:
        raise RuntimeError(site+": no baseline height")
    return baseline,baseline_type,events


def grid(start_year,end_year):
    t=pd.date_range(f"{start_year}-01-01",f"{end_year+1}-01-01",
                    freq="30min",inclusive="left")
    return t[~((t.month==2)&(t.day==29))]


def scenarios(timeline,baseline,events):
    """Use latest source event effective at/before each 30-minute forcing timestamp."""
    early=np.full(len(timeline),baseline,dtype=np.float64)
    late=np.full(len(timeline),baseline,dtype=np.float64)
    ts=timeline.to_numpy(dtype="datetime64[ns]")
    for e in events:
        first=e["earliest_possible"].to_datetime64()
        last=e["latest_upper_bound"].to_datetime64()
        early[ts>=first]=e["height_m"]
        late[ts>=last]=e["height_m"]
    return early,late


def main():
    p=argparse.ArgumentParser(description=__doc__)
    op=p.add_mutually_exclusive_group(required=True)
    op.add_argument("--check",action="store_true")
    op.add_argument("--run",action="store_true")
    p.add_argument("--height-csv",type=Path,default=BASE_CSV)
    p.add_argument("--sites-tsv",type=Path,default=SITES_TSV)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    a=p.parse_args()
    actual=hash_file(a.height_csv)
    if actual!=SHA256:raise RuntimeError("BASE snapshot SHA256 differs: "+actual)
    hdr,met=read(a.height_csv)
    if not {"Site_ID","Variable","Start_Date","Height"}<=hdr:
        raise RuntimeError("BASE schema missing required columns")
    mh,manifest=read(a.sites_tsv,"\t")
    if not {"site","first_year","last_year"}<=mh or not manifest:
        raise RuntimeError("Missing source site IDs and years")
    if len({r["site"] for r in manifest})!=len(manifest):
        raise RuntimeError("Duplicate manifest sites")
    sites=[]
    for r in manifest:
        groups=records_for_site(r["site"],met)
        if not groups:raise RuntimeError("No TA height source for "+r["site"])
        chosen,reason=choose_candidate(groups)
        sites.append((r,groups,chosen,reason))
    print("STAGE31 PREFLIGHT: sites=%d source SHA256=%s"%(len(sites),actual),flush=True)
    for r,groups,variable,why in sites:
        print("  %-7s %-19s  %s"%
              (r["site"],variable or "UNRESOLVED",why),flush=True)
    if a.check:
        print("CHECK ONLY: no ZBOT or report generated")
        return

    policies={};site_rows=[];event_rows=[];annual=[];blocks=[]
    for r,groups,variable,why in sites:
        site=r["site"]
        first,last=int(r["first_year"]),int(r["last_year"])
        if not variable:
            status="BLOCKED_TA_SENSOR_MAPPING"
            options=sorted({(key,numerical_height(row["Height"]))
                            for key,rs in groups.items() for row in rs})
            for key,h in options:
                blocks.append(dict(site=site,TA_variable=key,height_m=h,
                                   blocker=why,evidence="BASE_SOURCE_UNVERIFIED_TA_F_CROSSWALK"))
            site_rows.append(dict(site=site,ZBOT_candidate_mode="NONE",mapping="UNRESOLVED",
                earliest_vs_latest_difference_halfhours="",baseline_height_m="",
                baseline_source_assumption="",ZBOT_status=status,
                science_approval="NO"))
            print("  %-7s BLOCKED: ambiguous TA levels; height not assigned"%site,flush=True)
            continue
        baseline,backfill,events=events_from_records(site,variable,groups[variable])
        timeline=grid(first,last)
        earliest,latest=scenarios(timeline,baseline,events)
        changed=np.abs(earliest-latest)>1e-9
        htotal=int(changed.sum())
        heights=sorted({baseline,*[e["height_m"] for e in events]})
        mode="STATIC" if len(heights)==1 else "DYNAMIC"
        policy=dict(
            site=site,variable_BASE=variable,
            FLUXNET_TA_F_sensor_crosswalk="UNVERIFIED",
            source_snapshot_SHA256=actual,forcing_years=[first,last],
            candidate_ZBOT_mode=mode,
            baseline_m=baseline,baseline_source_assumption=backfill,
            early_history_assumption_user_selected=True,
            effective_date_uncertainty_rule=(
                "YEAR_ONLY: Jan01 vs following Jan01; MONTH_ONLY: month-start vs next-month-start; "
                "two bounds are modelling scenarios, NOT actual known change days"),
            dated_events=[dict(raw_Start_Date=e["raw_Start_Date"],
                               earliest_possible=str(e["earliest_possible"]),
                               latest_upper_bound=str(e["latest_upper_bound"]),
                               height_m=e["height_m"],date_precision=e["date_precision"],
                               source_duplicate_records=e["source_duplicate_records"])
                          for e in events],
            scenario_difference_halfhours=htotal,
            scientific_status="PROVISIONAL_NOT_APPROVED_FOR_DATM_OR_SPINUP")
        policies[site]=policy
        site_rows.append(dict(site=site,ZBOT_candidate_mode=mode,
            mapping=variable,baseline_height_m=baseline,
            baseline_source_assumption=backfill,
            candidate_heights_m=";".join(f"{h:g}" for h in heights),
            height_event_count=len(events),
            earliest_vs_latest_difference_halfhours=htotal,
            ZBOT_status="PROVISIONAL_SENSOR_MAPPING_UNVERIFIED",
            science_approval="NO"))
        for e in events:
            event_rows.append({k:(str(v) if k in ("earliest_possible","latest_upper_bound") else v)
                               for k,v in e.items()})
        ys=timeline.year.to_numpy()
        for y in range(first,last+1):
            mask=ys==y
            one=earliest[mask]
            two=latest[mask]
            annual.append(dict(site=site,year=y,
                model_halfhours=int(mask.sum()),
                earliest_scenario_distinct_heights_m=";".join(f"{v:g}" for v in sorted(set(one))),
                latest_scenario_distinct_heights_m=";".join(f"{v:g}" for v in sorted(set(two))),
                earliest_scenario_mean_height_m=round(float(one.mean()),5),
                latest_scenario_mean_height_m=round(float(two.mean()),5),
                uncertain_assignment_halfhours=int(np.count_nonzero(
                    np.abs(one-two)>1e-9)),
                model_height_status="PROVISIONAL_NOT_MEASURED_HISTORICAL_CONTINUITY"))
        print("  %-7s %-7s baseline=%g m dated_events=%d uncertainty_HH=%d"%
              (site,mode,baseline,len(events),htotal),flush=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=a.report_root/("stage31_provisional_ZBOT_scenarios_"+stamp)
    out.mkdir(parents=True,exist_ok=False)
    payload=dict(method="AmeriFlux_STAGE31_BASE_STATIC_DYNAMIC_POLICY_SCENARIOS",
                 created_utc=datetime.now(timezone.utc).isoformat(),
                 source=str(a.height_csv),source_sha256=actual,
                 noleap_calendar=True,atm_ncpl=48,
                 science_status="NOT_APPROVED_FOR_DATM_OR_SPINUP",
                 provisional_sensor_policy=policies,
                 unresolved_site_count=len({x["site"] for x in blocks}),
                 do_not_create_model_jobs=True)
    (out/"01_provisional_site_height_policies.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    write(out/"02_ten_site_policy_summary.csv",site_rows,
          ["site","ZBOT_candidate_mode","mapping","baseline_height_m",
           "baseline_source_assumption","candidate_heights_m","height_event_count",
           "earliest_vs_latest_difference_halfhours",
           "ZBOT_status","science_approval"])
    write(out/"03_dated_height_events_bounds.csv",event_rows,
          ["site","variable","raw_Start_Date","date_precision",
           "earliest_possible","latest_upper_bound","height_m",
           "source_duplicate_records","date_rule"])
    write(out/"04_annual_earliest_vs_latest_height_sensitivity.csv",annual,
          ["site","year","model_halfhours",
           "earliest_scenario_distinct_heights_m",
           "latest_scenario_distinct_heights_m",
           "earliest_scenario_mean_height_m",
           "latest_scenario_mean_height_m",
           "uncertain_assignment_halfhours","model_height_status"])
    write(out/"05_blocked_TA_sensor_mapping_options.csv",blocks,
          ["site","TA_variable","height_m","blocker","evidence"])
    print("STAGE31 SUMMARY: sites=%d provisional_static=%d provisional_dynamic=%d blocked=%d"%
          (len(site_rows),
           sum(x["ZBOT_candidate_mode"]=="STATIC" for x in site_rows),
           sum(x["ZBOT_candidate_mode"]=="DYNAMIC" for x in site_rows),
           sum(x["ZBOT_candidate_mode"]=="NONE" for x in site_rows)),flush=True)
    print("REPORT DIR:",out,flush=True)
    print("NO ZBOT/DATM NETCDF WRITTEN. EARLY HEIGHT EXTENSIONS ARE ASSUMED.")
    print("HEIGHT MAPPING SCIENTIFIC GATE: HOLD.")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Shared AmeriFlux Stage29: auditable TA_F-to-ZBOT sensor-mapping CANDIDATES.

Source: immutable BASE_MeasurementHeight_20260908.csv committed in metadata/.
Scope: any batch via --sites-tsv (Batch01 is default).

- Do not use the old ICOS VAR_INFO_* BIF parser for this BASE product.
- Never infer the FLUXNET TA_F reference from EC tower, WS, or canopy height.
- TA_PI_F can be a preferred VARIABLE-MAPPING HYPOTHESIS, not a proven match.
- Multiple levels without unambiguous TA mapping are blocked.
- Missing Start_Date does not prove historical constancy.
- YEAR/MONTH start dates become UNCERTAINTY INTERVALS, not invented days.
- No ZBOT vector / DATM NetCDF / forcing / model file written.
- --check: source and site manifest only; --audit: CSV decision aids only.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import hashlib
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"metadata"/"BASE_MeasurementHeight_20260908.csv"
BATCH01=ROOT.parent/"AmeriFlux_MultiSite_10"/"sites.tsv"
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
PINNED_SHA256="1c1e4171d295406a13d503f877b58661a651c88ffb6f0b6ec498f56bb1fcec5a"
REQUIRED={"Site_ID","Variable","Start_Date","Height","Instrument_Model","Comment"}


def load(path,sep=","):
    if not path.is_file():raise RuntimeError("Missing source: "+str(path))
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter=sep)
        if not rd.fieldnames:raise RuntimeError("Empty table header "+str(path))
        return set(rd.fieldnames),list(rd)


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(2**20),b""):
            h.update(chunk)
    return h.hexdigest()


def write(path,rows,fields):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def date_window(date):
    raw=str(date or "").strip()
    if not raw:return ("UNDATED","","")
    digits=re.sub(r"[-/ ]","",raw)
    try:
        if not digits.isdigit():return ("UNPARSEABLE","","")
        if len(digits)==4:
            y=int(digits)
            return ("YEAR_ONLY",f"{y:04d}-01-01",f"{y:04d}-12-31")
        if len(digits)==6:
            y,m=int(digits[:4]),int(digits[4:6])
            day=calendar.monthrange(y,m)[1]
            return ("MONTH_ONLY",f"{y:04d}-{m:02d}-01",f"{y:04d}-{m:02d}-{day:02d}")
        if len(digits)==8:
            stamp=dt.datetime.strptime(digits,"%Y%m%d")
            date=stamp.date().isoformat()
            return ("DAY_EXACT",date,date)
        if len(digits)==12:
            stamp=dt.datetime.strptime(digits,"%Y%m%d%H%M")
            time=stamp.strftime("%Y-%m-%d %H:%M")
            return ("MINUTE_EXACT",time,time)
    except (ValueError,OverflowError):
        return ("INVALID_DATE","","")
    return ("UNPARSEABLE","","")


def parse_height(raw):
    try:
        h=float(raw)
    except (TypeError,ValueError):
        return None
    return h if math.isfinite(h) and .5<=h<=150 else None


def sensor_rank(name):
    v=name.upper()
    if v=="TA_PI_F":return (0,v)
    if v.startswith("TA_PI_F_"):return (1,v)
    if v=="TA":return (2,v)
    if v.startswith("TA_"):return (3,v)
    return (9,v)


def describe_group(records):
    heights=sorted({r["height_m"] for r in records if r["height_m"] is not None})
    undated=sum(r["date_precision"]=="UNDATED" for r in records)
    dated=sum(r["date_precision"] not in ("UNDATED","INVALID_DATE","UNPARSEABLE") for r in records)
    uncertain=sum(r["date_precision"] in ("YEAR_ONLY","MONTH_ONLY") for r in records)
    invalid=sum(r["height_m"] is None or r["date_precision"] in ("INVALID_DATE","UNPARSEABLE") for r in records)
    return heights,undated,dated,uncertain,invalid


def process(site,records):
    ta=[r for r in records if r["Variable"].upper().startswith("TA")]
    ws=[r for r in records if r["Variable"].upper().startswith("WS")]
    grouped=defaultdict(list)
    for r in ta:grouped[r["Variable"].upper()].append(r)
    if not ta:
        raise RuntimeError(site+": no TA-family heights available")
    candidates=[]
    for v,rr in sorted(grouped.items(),key=lambda x:sensor_rank(x[0])):
        heights,undated,dated,uncertain,invalid=describe_group(rr)
        candidates.append(dict(site=site,variable=v,n_source_rows=len(rr),
            distinct_height_m=";".join(f"{h:g}" for h in heights),
            dated_records=dated,undated_records=undated,
            partial_date_records=uncertain,invalid_records=invalid,
            mapping_priority="PI_ALIAS_HYPOTHESIS" if v.startswith("TA_PI_F")
            else "EXACT_TA_VARIABLE_HYPOTHESIS" if v=="TA"
            else "MULTI_LEVEL_SENSOR_HYPOTHESIS",
            FLUXNET_TA_F_verified="NO",ZBOT_approved="NO"))
    pi=[x for x in candidates if x["variable"].startswith("TA_PI_F")]
    direct=[x for x in candidates if x["variable"]=="TA"]
    # This selection is for scientific inspection only, NEVER an approval.
    if len(pi)==1:
        selected=pi[0]["variable"]
        select_reason="SINGLE_PI_ALIAS_PREFERRED_FOR_MAPPING_REVIEW"
    elif len(pi)>1:
        selected=""
        select_reason="MULTIPLE_PI_ALIASES_MAPPING_BLOCKED"
    elif len(direct)==1:
        selected="TA"
        select_reason="DIRECT_TA_VARIABLE_MAPPING_REVIEW"
    else:
        selected=""
        select_reason="MULTIPLE_UNMAPPED_TA_LEVELS_BLOCKED"
    picked=grouped.get(selected,[])
    heights,undated,dated,partial,invalid=describe_group(picked)
    eventrows=[]
    events=defaultdict(set)
    for r in picked:
        events[(r["Start_Date"],r["date_precision"],
                r["date_earliest"],r["date_latest"])].add(r["height_m"])
    conflict=[]
    for (raw,precision,start,end),hv in sorted(events.items(),
                key=lambda q:(q[0][2] or "",q[0][0])):
        valid={x for x in hv if x is not None}
        if len(valid)>1:conflict.append((raw,sorted(valid)))
        for h in sorted(valid):
            eventrows.append(dict(site=site,selected_candidate_variable=selected,
                raw_start_date=raw,date_precision=precision,
                effective_earliest=start,effective_latest=end,height_m=h,
                action=("NEEDS_EFFECTIVE_DATE_DECISION" if precision in ("YEAR_ONLY","MONTH_ONLY")
                        else "NEEDS_BASELINE_DATE_EVIDENCE" if precision=="UNDATED"
                        else "SOURCE_DATE_INVALID" if precision in ("INVALID_DATE","UNPARSEABLE")
                        else "EXACT_DATE_CANDIDATE_REVIEW"),
                approved_for_DATM="NO"))
    allheights=sorted({x["height_m"] for x in ta if x["height_m"] is not None})
    if not selected:
        state="BLOCKED_MAPPING_MULTIPLE_TA_LAYERS"
    elif invalid or conflict:
        state="BLOCKED_SELECTED_HEIGHT_INVALID_OR_DATE_CONFLICT"
    elif len(heights)>1 and partial:
        state="DYNAMIC_CANDIDATE_PARTIAL_DATE_POLICY_REQUIRED"
    elif len(heights)>1:
        state="DYNAMIC_CANDIDATE_REQUIRES_DATE_AND_BASELINE_APPROVAL"
    elif undated:
        state="STATIC_CANDIDATE_HISTORICAL_COVERAGE_UNVERIFIED"
    else:
        state="STATIC_CANDIDATE_VERIFY_SOURCE_TIME_COVERAGE"
    summary=dict(site=site,TA_family_records=len(ta),WS_family_records=len(ws),
        all_TA_variables=";".join(sorted(grouped)),
        all_TA_height_options_m=";".join(f"{h:g}" for h in allheights),
        selected_mapping_CANDIDATE=selected,
        mapping_selection_reason=select_reason,
        selected_height_options_m=";".join(f"{h:g}" for h in heights),
        selected_date_undated_n=undated,selected_date_partial_n=partial,
        selected_date_dated_n=dated,selected_invalid_n=invalid,
        same_date_conflicts_n=len(conflict),
        ZBOT_proposed_mode=("NONE" if not selected else "DYNAMIC_CANDIDATE"
            if len(heights)>1 else "STATIC_CANDIDATE"),
        ZBOT_science_gate=state,
        FLUXNET_TA_F_mapping_confirmed="NO",
        earliest_source_period_coverage_confirmed="NO",
        human_review_action="VERIFY_TA_F_MAPPING_EFFECTIVE_DATES_AND_LAND_SURFACE",
        DATM_approved="NO")
    # Blank, editable SCIENTIFIC decision template; never auto-write final values.
    decision=dict(site=site,proposed_variable=selected,
        selected_variable_approved="",approved_TA_F_height_history_ref="",
        partial_month_year_effective_date_policy="",
        early_period_height_assumption_approved="",
        physical_site_sensor_evidence_ref="",
        approved_by="",approved_date="",
        state="HOLD_FOR_HUMAN_APPROVAL")
    return summary,candidates,eventrows,decision


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--audit",action="store_true")
    p.add_argument("--height-csv",type=Path,default=SOURCE)
    p.add_argument("--sites-tsv",type=Path,default=BATCH01)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    args=p.parse_args()
    source_sha=sha(args.height_csv)
    if source_sha!=PINNED_SHA256:
        raise RuntimeError("Wrong BASE snapshot SHA256: "+source_sha)
    hdr,source=load(args.height_csv)
    if not REQUIRED<=hdr:raise RuntimeError("BASE snapshot schema wrong: "+str(REQUIRED-hdr))
    h2,manifest=load(args.sites_tsv,"\t")
    if "site" not in h2 or not 1<=len(manifest)<=300:
        raise RuntimeError("Batch manifest missing 'site' column or invalid size")
    sites=[x["site"] for x in manifest]
    if len(set(sites))!=len(sites):raise RuntimeError("Duplicate site IDs in sites.tsv")
    wanted=set(sites)
    picked=[]
    for r in source:
        if r["Site_ID"] not in wanted:continue
        if not r["Variable"].upper().startswith(("TA","WS")):continue
        h=parse_height(r["Height"])
        precision,earliest,latest=date_window(r["Start_Date"])
        picked.append(dict(r,height_m=h,date_precision=precision,
                           date_earliest=earliest,date_latest=latest))
    grouped=defaultdict(list)
    for r in picked:grouped[r["Site_ID"]].append(r)
    missing=[site for site in sites if
             not any(r["Variable"].upper().startswith("TA") for r in grouped[site])]
    if missing:raise RuntimeError("No TA-family height metadata: "+str(missing))
    print("STAGE29 CHECK: snapshot SHA256",source_sha)
    print("SITE MATCH:",len(sites),"/",len(sites),"TA-family present")
    if args.check:
        print("CHECK ONLY; no policy or reports written")
        return

    summaries=[];options=[];epochs=[];decisions=[]
    for site in sites:
        s,o,e,d=process(site,grouped[site])
        summaries.append(s);options.extend(o);epochs.extend(e);decisions.append(d)
        print("  %-7s %-7s mapping=%-14s heights=%-16s %s"%
              (site,s["ZBOT_proposed_mode"],s["selected_mapping_CANDIDATE"] or "UNRESOLVED",
               s["selected_height_options_m"] or "AMBIGUOUS",
               s["ZBOT_science_gate"]),flush=True)
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=args.report_root/("stage29_BASE_ZBOT_mapping_candidates_"+stamp)
    out.mkdir(parents=True,exist_ok=False)
    write(out/"01_ten_site_mapping_candidate_summary.csv",summaries,list(summaries[0]))
    write(out/"02_all_TA_variable_mapping_options.csv",options,list(options[0]))
    write(out/"03_dated_height_candidates_with_date_uncertainty.csv",epochs,
          ["site","selected_candidate_variable","raw_start_date","date_precision",
           "effective_earliest","effective_latest","height_m","action","approved_for_DATM"])
    write(out/"04_BLANK_scientific_approval_template.csv",decisions,list(decisions[0]))
    print("STAGE29 SUMMARY: sites=%d static_candidates=%d dynamic_candidates=%d"
          " blocked_mapping=%d"%
          (len(summaries),
           sum(r["ZBOT_proposed_mode"]=="STATIC_CANDIDATE" for r in summaries),
           sum(r["ZBOT_proposed_mode"]=="DYNAMIC_CANDIDATE" for r in summaries),
           sum(r["ZBOT_proposed_mode"]=="NONE" for r in summaries)))
    print("REPORT DIR:",out)
    print("AUDIT-ONLY. No TA_F mapping approved; no ZBOT or DATM files created.")


if __name__=="__main__":
    main()

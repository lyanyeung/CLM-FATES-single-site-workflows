#!/usr/bin/env python3
"""AmeriFlux Batch01 Stage26: read-only BIF TA/WS heights for prospective ZBOT.

For each EXACT pinned AmeriFlux release from sites.tsv:
- read only its original *_BIF_* CSV, preserve source SHA256 and group IDs
- collect dated VAR_INFO_VARNAME=TA_F/WS_F, VAR_INFO_HEIGHT, VAR_INFO_DATE
- deduplicate source records without inventing new physical measurements
- flag conflicts, aliases, bad units/dates, undated epochs and missing height
- evaluate documented height coverage on NO_LEAP 30-minute forcing timeline
- flag TA/WS height differences only where *both* heights are documented
- NEVER presume EC tower/sonic height equals TA measurement reference height
- NEVER apply earliest-known-height backward without an explicit policy
- write ONLY timestamped reports; no ZBOT series, NetCDF, DATM or case editing

BIF events are not by themselves proof of historically constant instrumentation.
Official source timestamp time convention must be verified before DATM.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parents[2]
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
EXACT={"TA_F","WS_F"}
LIKELY_ALIASES={"TA","TA_F_MDS","TA_ERA","T_AIR","TA_1","TA_2",
                "WS","WS_ERA","WS_1","WS_2"}
FIELDS=("VAR_INFO_VARNAME","VAR_INFO_HEIGHT","VAR_INFO_DATE")


def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(2**20),b""):
            h.update(block)
    return h.hexdigest()


def manifest():
    with (HERE/"sites.tsv").open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if len(rows)!=10 or len({r["site"] for r in rows})!=10:
        raise RuntimeError("Pinned Batch01 manifest must contain ten unique releases")
    for row in rows:
        first,last=int(row["first_year"]),int(row["last_year"])
        if first<1980 or last>2030 or first>last:
            raise RuntimeError("Invalid release forcing-year window "+row["site"])
    return rows


def bif_file(root,row):
    d=root/row["site"]/"forcing"/"raw"/row["package"]
    choices=sorted(p for p in d.glob("*.csv") if "_BIF_" in p.name.upper())
    if len(choices)!=1:
        raise RuntimeError(row["site"]+": expected 1 exact-release *_BIF_* CSV; "
                           "found "+str(len(choices))+" in "+str(d))
    return choices[0]


def parse_date(value):
    raw=str(value or "").strip()
    if raw.endswith(".0") and raw[:-2].isdigit():raw=raw[:-2]
    forms={8:("%Y%m%d","DATE_ONLY_MIDNIGHT_ASSUMED"),
           12:("%Y%m%d%H%M","MINUTE_EXACT"),
           14:("%Y%m%d%H%M%S","SECOND_EXACT")}
    if len(raw) not in forms or not raw.isdigit():
        raise ValueError("unrecognized date (expected 8/12/14 digits): "+repr(value))
    fmt,precision=forms[len(raw)]
    return pd.to_datetime(raw,format=fmt,errors="raise"),precision


def source_entries(site,path):
    # Preserve multiple values within the same group; do not let last row win.
    groups=defaultdict(lambda:defaultdict(list))
    with path.open("r",newline="",encoding="utf-8-sig",errors="replace") as f:
        reader=csv.DictReader(f)
        required={"VARIABLE","DATAVALUE","GROUP_ID"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError("BIF missing columns: "+str(required))
        for row in reader:
            group=(str(row.get("VARIABLE_GROUP") or "").strip(),
                   str(row.get("GROUP_ID") or "").strip())
            key=str(row.get("VARIABLE") or "").strip().upper()
            value=str(row.get("DATAVALUE") or "").strip()
            if key:groups[group][key].append(value)
    epochs=[];issues=[];aliases=[]
    for group,values in groups.items():
        tag=":".join(group)
        scalar={}
        for field in (*FIELDS,"VAR_INFO_HEIGHT_UNIT"):
            candidates={v.strip() for v in values.get(field,[]) if v.strip()}
            if len(candidates)>1:
                issues.append(dict(site=site,variable=field,issue="CONFLICT_GROUP_FIELD",
                                   raw_date="",group=tag,details=";".join(sorted(candidates))))
            scalar[field]=next(iter(candidates)) if len(candidates)==1 else ""
        var=scalar["VAR_INFO_VARNAME"].upper().strip()
        if not var:
            continue
        if var not in EXACT:
            if var in LIKELY_ALIASES or var.startswith(("TA_","WS_","T_AIR")):
                aliases.append(dict(site=site,varname=var,
                    raw_height=scalar["VAR_INFO_HEIGHT"],
                    raw_date=scalar["VAR_INFO_DATE"],group=tag,
                    interpretation="UNVERIFIED_ALIAS_DO_NOT_USE_AS_ZBOT"))
            continue
        rawheight=scalar["VAR_INFO_HEIGHT"]
        rawdate=scalar["VAR_INFO_DATE"]
        unit=scalar["VAR_INFO_HEIGHT_UNIT"]
        if unit and unit.lower() not in ("m","meter","meters","metre","metres"):
            issues.append(dict(site=site,variable=var,issue="UNVERIFIED_HEIGHT_UNIT",
                               raw_date=rawdate,group=tag,details=unit))
            continue
        if not rawheight:
            issues.append(dict(site=site,variable=var,issue="MISSING_HEIGHT",
                               raw_date=rawdate,group=tag,details="No documented height"))
            continue
        if not rawdate:
            issues.append(dict(site=site,variable=var,issue="MISSING_EFFECTIVE_DATE",
                               raw_date="",group=tag,details="Height exists but date unknown; cannot assign epoch"))
            continue
        try:
            value=float(rawheight)
            if not math.isfinite(value) or not 0.5<=value<=150.0:
                raise ValueError("height outside conservative 0.5..150m screen")
            stamp,precision=parse_date(rawdate)
        except (TypeError,ValueError,OverflowError) as exc:
            issues.append(dict(site=site,variable=var,issue="INVALID_HEIGHT_OR_DATE",
                               raw_date=rawdate,group=tag,
                               details="height="+rawheight+"; "+str(exc)))
            continue
        epochs.append(dict(site=site,variable=var,
            effective_from=stamp,height_m=value,date_precision=precision,
            raw_date=rawdate,source_group=tag,source_path=str(path),
            source_height_unit=unit if unit else "BIF_EXPECTED_METERS_UNVERIFIED_UNIT_FIELD"))
    return epochs,issues,aliases


def dedup(site,epochs):
    grouped=defaultdict(list)
    for item in epochs:
        grouped[(item["variable"],item["effective_from"])].append(item)
    unique=[];issues=[]
    for (var,stamp),group in sorted(grouped.items()):
        heights=sorted({round(x["height_m"],6) for x in group})
        if len(heights)!=1:
            issues.append(dict(site=site,variable=var,
                issue="SAME_DATE_HEIGHT_CONFLICT",raw_date=str(stamp),
                group="|".join(x["source_group"] for x in group),
                details="Multiple heights: "+",".join(map(str,heights))))
            continue
        x=dict(group[0])
        x["raw_repeated_records"]=len(group)
        x["date_precisions"]="|".join(sorted({g["date_precision"] for g in group}))
        if len({g["date_precision"] for g in group})>1:
            issues.append(dict(site=site,variable=var,
                issue="DATE_PRECISION_CONFLICT",raw_date=str(stamp),
                group="|".join(g["source_group"] for g in group),
                details=x["date_precisions"]))
        unique.append(x)
    return unique,issues


def history_lookup(epochs,timeline,variable):
    recs=sorted((x for x in epochs if x["variable"]==variable),
                key=lambda r:r["effective_from"])
    n=len(timeline)
    heights=np.full(n,np.nan)
    known=np.zeros(n,dtype=bool)
    if recs:
        dates=np.array([x["effective_from"].to_datetime64() for x in recs],
                       dtype="datetime64[ns]")
        vals=np.array([x["height_m"] for x in recs],dtype=float)
        j=np.searchsorted(dates,timeline.to_numpy(dtype="datetime64[ns]"),side="right")-1
        known=j>=0
        heights[known]=vals[j[known]]
    return recs,heights,known


def csv_save(path,rows,columns):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    p.add_argument("--sites-root",type=Path,default=ROOT)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    args=p.parse_args()
    rows=manifest()
    selected=[]
    for row in rows:
        path=bif_file(args.sites_root,row)
        selected.append((row,path))
        print("CHECK OK %-7s BIF=%s" %(row["site"],path.name),flush=True)
    print("STAGE26 PREFLIGHT: 10/10 pinned BIF source files",flush=True)
    if args.check:
        print("CHECK ONLY; no height assumptions or reports written.")
        return

    summary=[];all_epochs=[];all_issues=[];all_aliases=[]
    annual=[];fingerprints=[]
    for row,path in selected:
        site=row["site"];first=int(row["first_year"]);last=int(row["last_year"])
        epochraw,issues,aliases=source_entries(site,path)
        epochs,conflicts=dedup(site,epochraw)
        issues.extend(conflicts)
        all_epochs.extend(epochs);all_aliases.extend(aliases)
        timeline=pd.date_range(f"{first}-01-01",f"{last+1}-01-01",
                               freq="30min",inclusive="left")
        timeline=timeline[~((timeline.month==2)&(timeline.day==29))]
        trecs,ta,ta_known=history_lookup(epochs,timeline,"TA_F")
        wrecs,ws,ws_known=history_lookup(epochs,timeline,"WS_F")
        missing_ta=~ta_known;missing_ws=~ws_known
        overlap=ta_known&ws_known
        mismatch=overlap&(np.abs(ta-ws)>3.0)
        if not trecs:
            issues.append(dict(site=site,variable="TA_F",
                issue="NO_VALID_TA_F_HEIGHT",raw_date="",group="",
                details="Cannot construct BIF-derived ZBOT from this source"))
        if not wrecs:
            issues.append(dict(site=site,variable="WS_F",
                issue="NO_VALID_WS_F_HEIGHT",raw_date="",group="",
                details="Keep wind measurement height unknown; not ZBOT"))
        early=int(missing_ta.sum())
        if early and trecs:
            issues.append(dict(site=site,variable="TA_F",
                issue="UNDOCUMENTED_EARLY_TA_HEIGHT",raw_date="",
                group="",details=str(early)+" NO_LEAP half-hours before first documented TA_F date; no backfill approved"))
        if mismatch.any():
            issues.append(dict(site=site,variable="TA_F/WS_F",
                issue="MEASURED_TA_WS_HEIGHT_MISMATCH_GT3M",raw_date="",
                group="",details=str(int(mismatch.sum()))+" documented overlapping half-hours; do not rescale WIND automatically"))
        blockers={"SAME_DATE_HEIGHT_CONFLICT","INVALID_HEIGHT_OR_DATE",
                  "UNVERIFIED_HEIGHT_UNIT","CONFLICT_GROUP_FIELD",
                  "DATE_PRECISION_CONFLICT"}
        if not trecs:status="BLOCKED_NO_DOCUMENTED_TA_HEIGHT"
        elif any(i["issue"] in blockers and
                 i["variable"] in ("TA_F","VAR_INFO_DATE","VAR_INFO_HEIGHT",
                                   "VAR_INFO_HEIGHT_UNIT","VAR_INFO_VARNAME")
                 for i in issues):status="BLOCKED_BIF_CONFLICT_OR_INVALID_TA_RECORD"
        elif early:status="EARLY_TA_HEIGHT_POLICY_NEEDED"
        else:status="BIF_TA_HISTORY_AVAILABLE_REVIEW_ONLY"
        all_issues.extend(issues)
        summary.append(dict(
            site=site,first_year=first,last_year=last,
            BIF_path=str(path),TA_epochs=len(trecs),WS_epochs=len(wrecs),
            first_TA_date=str(trecs[0]["effective_from"]) if trecs else "",
            first_TA_height_m=trecs[0]["height_m"] if trecs else "",
            first_WS_date=str(wrecs[0]["effective_from"]) if wrecs else "",
            first_WS_height_m=wrecs[0]["height_m"] if wrecs else "",
            total_NOLEAP_halfhours=len(timeline),
            documented_TA_halfhours=int(ta_known.sum()),
            undocumented_early_TA_halfhours=early,
            documented_WS_halfhours=int(ws_known.sum()),
            undocumented_early_WS_halfhours=int(missing_ws.sum()),
            documented_TA_WS_overlap_halfhours=int(overlap.sum()),
            TA_WS_height_difference_gt3m_halfhours=int(mismatch.sum()),
            raw_event_count=len(epochraw),
            unverified_aliases=len(aliases),
            BIF_issue_count=len(issues),status=status,
            ZBOT_policy="NOT_SELECTED_NOT_APPROVED",
            science_gate="PENDING_REVIEW"))
        for year in range(first,last+1):
            yearmask=timeline.year==year
            annual.append(dict(
                site=site,year=year,noleap_halfhours=int(yearmask.sum()),
                documented_TA_halfhours=int((ta_known&yearmask).sum()),
                undocumented_TA_halfhours=int((missing_ta&yearmask).sum()),
                dated_TA_height_values_m=";".join(
                    f"{h:g}" for h in sorted({float(x) for x in ta[yearmask] if np.isfinite(x)})),
                documented_WS_halfhours=int((ws_known&yearmask).sum()),
                documented_overlap_height_difference_gt3m=int((mismatch&yearmask).sum())))
        fingerprints.append(dict(site=site,BIF_path=str(path),SHA256=sha256(path)))
        print("  %-7s TA=%2d WS=%2d earlyTA=%7d mismatchTAWS=%7d  %s" %
              (site,len(trecs),len(wrecs),early,int(mismatch.sum()),status),flush=True)

    dest=args.report_root/("stage26_BIF_TA_WS_height_evidence_"+datetime.now(
        timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    dest.mkdir(parents=True,exist_ok=False)
    csv_save(dest/"01_ten_site_BIF_height_summary.csv",summary,list(summary[0]))
    csv_save(dest/"02_dated_TA_WS_height_events.csv",all_epochs,
             ["site","variable","effective_from","height_m","date_precision",
              "raw_date","source_group","source_path",
              "source_height_unit","raw_repeated_records","date_precisions"])
    csv_save(dest/"03_BIF_missing_conflicts_and_policy_requests.csv",all_issues,
             ["site","variable","issue","raw_date","group","details"])
    csv_save(dest/"04_annual_Noleap_TA_WS_documented_coverage.csv",annual,list(annual[0]))
    csv_save(dest/"05_unverified_sensor_aliases.csv",all_aliases,
             ["site","varname","raw_height","raw_date","group","interpretation"])
    csv_save(dest/"06_exact_BIF_source_SHA256.csv",fingerprints,list(fingerprints[0]))
    print("STAGE26 SUMMARY: sites=10 documented_TA=%d/"
          " early_policy_needed=%d missing_TA=%d" %
          (sum(bool(x["TA_epochs"]) for x in summary),
           sum(x["status"]=="EARLY_TA_HEIGHT_POLICY_NEEDED" for x in summary),
           sum(x["status"]=="BLOCKED_NO_DOCUMENTED_TA_HEIGHT" for x in summary)),
          flush=True)
    print("REPORT DIR:",dest,flush=True)
    print("BIF evidence ONLY; no assumptions for early heights, no ZBOT/DATM/forcing or spinup written.")


if __name__=="__main__":
    main()

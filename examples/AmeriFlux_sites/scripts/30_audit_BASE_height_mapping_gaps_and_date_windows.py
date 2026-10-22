#!/usr/bin/env python3
"""AmeriFlux shared Stage30: read-only ZBOT *decision support*, NOT approval.

Consumes the immutable BASE MeasurementHeight snapshot and Batch sites.tsv.
Targets two separate scientific problems before DATM:
  (1) Multi-layer TA arrays without independently verified FLUXNET TA_F mapping.
  (2) YEAR/MONTH effective-date uncertainty and undated pre-history.

Do not infer TA_F sensor mapping from PI qualifier or from WS/EC tower height.
Do not silently convert partial dates to January 1 or month day 1.
No source, QCv5 forcing, ZBOT time series, NetCDF, CIME or Slurm edits.
"""
from __future__ import annotations
import argparse
import calendar
import csv
import hashlib
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"metadata"/"BASE_MeasurementHeight_20260908.csv"
BATCH=ROOT.parent/"AmeriFlux_MultiSite_10"/"sites.tsv"
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
PINNED_SHA256="1c1e4171d295406a13d503f877b58661a651c88ffb6f0b6ec498f56bb1fcec5a"


def csv_read(p,delimiter=","):
    with p.open("r",newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f,delimiter=delimiter)
        if not reader.fieldnames:raise RuntimeError("Missing headers: "+str(p))
        return list(reader)


def csv_write(p,rows,headers):
    with p.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=headers,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()


def height(row):
    try:val=float(row["Height"])
    except (ValueError,TypeError):return None
    if not (0.5 <= val <= 150):return None
    return val


def interval(text):
    """Inclusive earliest/latest possible effective date, NOT a selected date."""
    raw=str(text or "").strip()
    if not raw:return ("UNDATED","","")
    digits=raw.replace("-","").replace("/","").replace(" ","")
    if not digits.isdigit():return ("UNPARSEABLE","","")
    try:
        if len(digits)==4:
            y=int(digits)
            return "YEAR_ONLY",date(y,1,1),date(y,12,31)
        if len(digits)==6:
            y,m=int(digits[:4]),int(digits[4:6])
            return "MONTH_ONLY",date(y,m,1),date(y,m,calendar.monthrange(y,m)[1])
        if len(digits)==8:
            d=datetime.strptime(digits,"%Y%m%d").date()
            return "DAY_EXACT",d,d
        if len(digits)==12:
            d=datetime.strptime(digits,"%Y%m%d%H%M").date()
            # Minute exact only for actual effective time; the CSV below
            # preserves raw timestamp and this date is only a comparison key.
            return "MINUTE_EXACT",d,d
    except (ValueError, OverflowError):pass
    return "INVALID_DATE","",""


def noleap_halfhours_between(left,right):
    if not left or not right:return ""
    days=(right-left).days+1
    for y in range(left.year,right.year+1):
        if calendar.isleap(y) and left<=date(y,2,29)<=right:days-=1
    return 48*days


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    ap.add_argument("--height-csv",type=Path,default=BASE)
    ap.add_argument("--sites-tsv",type=Path,default=BATCH)
    ap.add_argument("--report-root",type=Path,default=REPORTS)
    a=ap.parse_args()

    if sha256(a.height_csv)!=PINNED_SHA256:
        raise RuntimeError("Wrong BASE source snapshot SHA256")
    source=csv_read(a.height_csv)
    manifest=csv_read(a.sites_tsv,"\t")
    if len(manifest)!=len({r["site"] for r in manifest}):
        raise RuntimeError("Duplicate site IDs in manifest")
    by=defaultdict(list)
    for r in source:
        if r["Variable"].upper().startswith("TA"):
            by[r["Site_ID"]].append(r)
    missing=[r["site"] for r in manifest if not by[r["site"]]]
    if missing:raise RuntimeError("Missing TA height records "+str(missing))
    print("STAGE30 PREFLIGHT: sites=%d, BASE_SOURCE_SHA256=%s"%
          (len(manifest),PINNED_SHA256),flush=True)
    if a.check:
        print("CHECK ONLY: no files written")
        return

    site_status=[];multilevel=[];epochs=[];approvals=[]
    for row in manifest:
        site=row["site"]
        yr0=int(row["first_year"]);yr1=int(row["last_year"])
        rr=by[site]
        grouped=defaultdict(list)
        for r in rr:grouped[r["Variable"].upper()].append(r)
        pi=[v for v in grouped if v=="TA_PI_F" or v.startswith("TA_PI_F_")]
        # A single PI-prefixed series is a candidate, never verified TA_F.
        candidate=(pi[0] if len(pi)==1 else
                   "TA" if not pi and "TA" in grouped else "")
        selected=grouped.get(candidate,[])
        distinct=sorted({height(r) for r in selected if height(r) is not None})
        all_heights=sorted({height(r) for r in rr if height(r) is not None})
        undated=sum(not r["Start_Date"].strip() for r in selected)
        if not candidate:
            state="BLOCKED_MULTI_LEVEL_TA_SENSOR_MAPPING"
        elif len(distinct)>1:
            state="DYNAMIC_PROVISIONAL_DATE_POLICY_REQUIRED"
        else:
            state="STATIC_PROVISIONAL_HISTORICAL_COVERAGE_REQUIRED"
        site_status.append(dict(site=site,years=f"{yr0}-{yr1}",
            TA_family_variables=";".join(sorted(grouped)),
            all_TA_heights_m=";".join("%g"%z for z in all_heights),
            selected_provisional_TA_variable=candidate,
            selected_provisional_height_m=";".join("%g"%z for z in distinct),
            selected_TA_undated_records=undated,
            state=state,FLUXNET_TA_F_crosswalk_verified="NO",
            ZBOT_status="NOT_APPROVED",recommended_next_action=(
                "OBTAIN_OFFICIAL_TA_F_TO_BASE_SENSOR_MAPPING" if not candidate else
                "APPROVE_PARTIAL_EFFECTIVE_DATES_AND_HISTORICAL_HEIGHT" if len(distinct)>1
                else "VERIFY_SENSOR_AND_EARLY_HEIGHT_HISTORY")))
        for v,vr in sorted(grouped.items()):
            for x in vr:
                if candidate and v==candidate:continue
                multilevel.append(dict(site=site,
                    BASE_variable=v,height_m=x["Height"],raw_start=x["Start_Date"],
                    instrument=x.get("Instrument_Model",""),
                    comment=x.get("Comment",""),
                    possible_FLUXNET_TA_F_source="UNVERIFIED",
                    selection_status="NO_AUTO_MAPPING"))
        for x in selected:
            precision,left,right=interval(x["Start_Date"])
            if left and not (date(yr0,1,1)<=right and left<=date(yr1,12,31)):
                # Sensor metadata outside forcing span is still reported.
                overlap="OUTSIDE_SELECTED_FORCING_WINDOW"
            else:overlap="INTERSECTS_FORCING_OR_UNDATED"
            epochs.append(dict(site=site,BASE_variable=candidate,
                raw_Start_Date=x["Start_Date"],date_precision=precision,
                earliest_possible=str(left) if left else "",
                latest_possible=str(right) if right else "",
                unresolved_noleap_halfhours=noleap_halfhours_between(left,right),
                Height_m=x["Height"],instrument=x.get("Instrument_Model",""),
                comment=x.get("Comment",""),forcing_window_relation=overlap,
                mapping_validated="NO",date_policy_approved="NO"))
        approvals.append(dict(site=site,
            proposed_variable=candidate,proposed_height_m=";".join(map(str,distinct)),
            scientific_TA_F_sensor_crosswalk_evidence="",
            selected_effective_dates_and_height_policy="",
            first_height_applies_to_undated_early_years_approved="",
            alternative_height_sensitivity_required="",
            investigator_approval="",ZBOT_use_gate="HOLD_NOT_APPROVED"))
        print("  %-7s %-42s mapping=%-15s heights=%s"%
              (site,state,candidate or "UNRESOLVED",
               ",".join("%g"%v for v in distinct) or "MULTI_LAYER"),
              flush=True)
    tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=a.report_root/("stage30_ZBOT_mapping_date_decisions_"+tag)
    out.mkdir(parents=True,exist_ok=False)
    csv_write(out/"01_ten_site_ZBOT_decision_matrix.csv",
              site_status,list(site_status[0]))
    csv_write(out/"02_unmapped_TA_sensor_layers.csv",multilevel,
        ["site","BASE_variable","height_m","raw_start","instrument","comment",
         "possible_FLUXNET_TA_F_source","selection_status"])
    csv_write(out/"03_selected_TA_date_uncertainty_windows.csv",epochs,
        ["site","BASE_variable","raw_Start_Date","date_precision",
         "earliest_possible","latest_possible","unresolved_noleap_halfhours",
         "Height_m","instrument","comment","forcing_window_relation",
         "mapping_validated","date_policy_approved"])
    csv_write(out/"04_blank_height_approval_template.csv",
              approvals,list(approvals[0]))
    nbad=sum(r["state"].startswith("BLOCKED") for r in site_status)
    ndyn=sum(r["state"].startswith("DYNAMIC") for r in site_status)
    print("STAGE30 SUMMARY: sites=%d, blocked_mapping=%d, dynamic_policy_required=%d"%
          (len(site_status),nbad,ndyn))
    print("REPORT DIR:",out)
    print("SOURCE REVIEW ONLY. NO HEIGHT CHOICE APPROVED. NO ZBOT/DATM WRITTEN.")


if __name__=="__main__":
    main()

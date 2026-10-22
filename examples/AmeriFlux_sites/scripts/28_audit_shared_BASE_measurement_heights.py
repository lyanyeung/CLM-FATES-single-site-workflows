#!/usr/bin/env python3
"""Shared AmeriFlux BASE measurement-height audit: read-only and fail closed.

Reads committed snapshot examples/AmeriFlux_sites/metadata/
BASE_MeasurementHeight_20260908.csv plus a batch sites.tsv (default Batch01).
Lists all candidate TA and WS measurement heights, ISO-like partial start-date
precision, whether TA/TA_PI_F is uniquely selectable or multiple vertical
sensors coexist. NEVER assumes a TA alias equals FLUXNET TA_F, and NEVER
backfills undated or early sensor heights. No DATM/ZBOT or source edits.
"""
from __future__ import annotations
import argparse,csv,datetime,hashlib,math,re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
DEFAULT_CSV=HERE/"metadata"/"BASE_MeasurementHeight_20260908.csv"
DEFAULT_SITES=HERE.parent/"AmeriFlux_MultiSite_10"/"sites.tsv"
DEFAULT_REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
SITE_NAMES={"Site_ID","Variable","Start_Date","Height"}
def records(p,delimiter=","):
    with p.open(newline="",encoding="utf-8-sig") as f:
        x=csv.DictReader(f,delimiter=delimiter)
        if not x.fieldnames:raise RuntimeError("Header absent "+str(p))
        rows=list(x)
    return set(x.fieldnames),rows
def write(p,rs,cols):
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore")
        w.writeheader();w.writerows(rs)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1048576),b""):h.update(x)
    return h.hexdigest()
def date_kind(raw):
    s=str(raw or "").strip()
    if not s:return "UNDATED"
    digits=re.sub(r"[-/ ]","",s)
    if not digits.isdigit():return "UNPARSED_REVIEW"
    if len(digits)==4:return "YEAR_ONLY"
    if len(digits)==6:return "MONTH_ONLY"
    if len(digits)==8:
        try:datetime.datetime.strptime(digits,"%Y%m%d")
        except ValueError:return "INVALID_DATE"
        return "DAY_EXACT"
    if len(digits)==12:
        try:datetime.datetime.strptime(digits,"%Y%m%d%H%M")
        except ValueError:return "INVALID_DATE"
        return "MINUTE_EXACT"
    return "UNPARSED_REVIEW"
def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--check",action="store_true")
    m.add_argument("--audit",action="store_true")
    p.add_argument("--height-csv",type=Path,default=DEFAULT_CSV)
    p.add_argument("--sites-tsv",type=Path,default=DEFAULT_SITES)
    p.add_argument("--report-root",type=Path,default=DEFAULT_REPORTS)
    a=p.parse_args()
    headers,met=records(a.height_csv)
    if not SITE_NAMES<=headers:raise RuntimeError("Missing height CSV columns "+str(SITE_NAMES-headers))
    hs,manifest=records(a.sites_tsv,"\t")
    if "site" not in hs or len({r["site"] for r in manifest})!=len(manifest):
        raise RuntimeError("Manifest lacks unique site column")
    sites={r["site"] for r in manifest}
    chosen=[r for r in met if r["Site_ID"] in sites and
            (r["Variable"].upper().startswith(("TA","WS")))]
    ta_sites={r["Site_ID"] for r in chosen if r["Variable"].upper().startswith("TA")}
    if sites-ta_sites:raise RuntimeError("Missing TA-family metadata for "+str(sorted(sites-ta_sites)))
    print("SOURCE:",a.height_csv,"SHA256",sha(a.height_csv),flush=True)
    print("SITE MATCH:",len(ta_sites),"/",len(sites),"TA-family metadata; no ZBOT approved",flush=True)
    if a.check:return
    detailed=[];summaries=[]
    for r in chosen:
        s=r["Height"].strip()
        try:h=float(s)
        except ValueError:h=float("nan")
        fam="TA" if r["Variable"].upper().startswith("TA") else "WS"
        status=("REVIEW_NONPOSITIVE_OR_NONFINITE" if not math.isfinite(h) or h<=0
                else "MEASUREMENT_CANDIDATE_NOT_ZBOT")
        detailed.append(dict(site=r["Site_ID"],family=fam,variable=r["Variable"],
            start_date=r["Start_Date"],date_precision=date_kind(r["Start_Date"]),
            height_m=r["Height"],instrument_model=r.get("Instrument_Model",""),
            instrument_model2=r.get("Instrument_Model2",""),
            comment=r.get("Comment",""),BASE_version=r.get("BASE_Version",""),
            status=status))
    for site in sorted(sites):
        sub=[x for x in detailed if x["site"]==site]
        ta=[x for x in sub if x["family"]=="TA"]
        ws=[x for x in sub if x["family"]=="WS"]
        variables={x["variable"] for x in ta}
        vals={x["height_m"] for x in ta if x["status"]=="MEASUREMENT_CANDIDATE_NOT_ZBOT"}
        undated=sum(x["date_precision"]=="UNDATED" for x in ta)
        ambiguous=len(variables)>1 or len(vals)>1
        state="MULTI_SENSOR_OR_HEIGHT_REVIEW" if ambiguous else "SINGLE_TA_HEIGHT_CANDIDATE_REVIEW"
        summaries.append(dict(site=site,TA_records=len(ta),WS_records=len(ws),
            TA_variable_names=";".join(sorted(variables)),
            TA_distinct_height_m=";".join(sorted(vals,key=lambda z:float(z))),
            TA_undated_records=undated,TA_dated_records=len(ta)-undated,
            mapping_status=state,ZBOT_approved="NO",next_action=
            "VALIDATE_FLUXNET_TA_F_VARIABLE_AND_EFFECTIVE_DATES"))
        print("%-7s TA=%2d WS=%2d distinct_TA_height=%2d undated=%2d %s"%
              (site,len(ta),len(ws),len(vals),undated,state),flush=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=a.report_root/("BASE_height_snapshot_review_"+stamp)
    out.mkdir(parents=True,exist_ok=False)
    write(out/"01_all_TA_WS_height_candidates.csv",detailed,list(detailed[0]))
    write(out/"02_site_height_mapping_review.csv",summaries,list(summaries[0]))
    write(out/"03_source_manifest.csv",[dict(source=str(a.height_csv),sha256=sha(a.height_csv),
        rows=len(met),sites=len(sites),provenance="BASE_MeasurementHeight_20260908",
        height_approval="PENDING")],["source","sha256","rows","sites","provenance","height_approval"])
    print("REPORT DIR:",out)
    print("SOURCE HEIGHTS ONLY; NO ZBOT HEIGHT POLICY, DATM OR SPINUP.")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Batch02 Stage55: existing Stage19 CDS ERA5 / 4,884 Stage11 HOLD triage.

Read-only except for an isolated new report under --audit. Requires completed,
hash-linked Stage54 zero-overlap evidence and exact Stage11 timestamp/source
matches. Reuses existing Stage19 review data; never redownloads ERA5 and never
automatically approves station T, ERA5 RH, VPD, QBOT, or forcing.
US-Ho1 local UTC-5 remains provisional unless separately verified later.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S11=BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
S54=BASE/"reports/stage54_444_vs_4884_timestamp_crosswalk_20261024T101940Z_bac3a939"
PRODUCT="reanalysis-era5-single-levels-timeseries"
TOTALS={"US-EML":1327,"US-GLE":295,"US-Ho1":917,"US-ICh":169,"US-ICt":2176}
STAGE11CSV="cold_humidity_repair_proposals.csv"
STAGE19CSV="all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1048576),b""):h.update(block)
    return h.hexdigest()

def truth(series):
    return series.astype(str).str.lower().eq("true")

def identity(df,time_col):
    frame=df.copy()
    ts=pd.to_datetime(frame[time_col].astype(str),errors="raise")
    if ts.isna().any() or ts.dt.tz is not None:
        raise ValueError("Invalid original tower timestamp in "+time_col)
    frame["site_local_key"]=ts.dt.strftime("%Y%m%d%H%M")
    if frame.duplicated(["site","site_local_key"]).any():
        raise ValueError("Duplicate site/local timestamp in "+time_col)
    return frame

def load_stage54(stage54,stage11):
    m=json.loads((stage54/"crosswalk_manifest.json").read_text())
    if (m.get("schema")!="STAGE54_BATCH02_EXACT_SITE_LOCAL_TIME_CROSSWALK_v1" or
        m.get("stage11_count")!=4884 or m.get("stage53_count")!=444 or
        m.get("intersection_count")!=0 or m.get("stage11_only_count")!=4884 or
        m.get("stage53_only_count")!=444 or
        m.get("source_stage11")!=str(stage11) or
        m.get("approved_for_DATM") is not False or
        m.get("forcing_modified") is not False):
        raise ValueError("Stage54 exact zero-intersection proof absent")
    for name,digest in m.get("output_sha256",{}).items():
        if sha(stage54/name)!=digest:
            raise ValueError("Stage54 report checksum changed: "+name)
    if (m.get("input_sha256",{}).get("stage11_HOLD_sha256")!=
        sha(stage11/STAGE11CSV) or
        m.get("input_sha256",{}).get("stage11_manifest_sha256")!=
        sha(stage11/"manifest.json")):
        raise ValueError("Stage54 Stage11 source hashes no longer match")
    return m

def choose_stage19(user_path,stage11):
    if user_path is not None:return user_path.resolve(strict=True)
    found=[]
    pattern="AmeriFlux_Batch02_stage19_full_dewpoint_audit_*/manifest.json"
    for f in sorted(Path.home().glob(pattern)):
        try:
            m=json.loads(f.read_text())
            if (m.get("schema")=="STAGE19_ALL_4884_ERA5_DIAGNOSTIC_v1" and
                m.get("stage11_targets_sha256")==sha(stage11/STAGE11CSV) and
                m.get("stage11_manifest_sha256")==sha(stage11/"manifest.json") and
                m.get("n_target_rows")==4884):
                found.append(f.parent)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    if not found:
        raise FileNotFoundError(
          "NO EXISTING STAGE19 REPORT matches the pinned 4,884 targets. "
          "Run existing scripts/stage19/19_audit_all_era5_dewpoint_targets.py "
          "--check and --write-report first; do not redownload CDS ERA5.")
    if len(found)>1:
        print("STAGE55: multiple matching Stage19 reports; using most recent lexical directory")
        for p in found:print("MATCHING_STAGE19",p)
    return found[-1]

def load(stage19,stage11,stage54,verify_receipts):
    if not (stage11/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Original Stage11 HOLD marker missing")
    if not (stage19/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Original Stage19 science HOLD marker missing")
    m11=json.loads((stage11/"manifest.json").read_text())
    m19=json.loads((stage19/"manifest.json").read_text())
    if (m11.get("n_target_rows")!=4884 or
        m11.get("scientific_status")!="HOLD_INDEPENDENT_VALIDATION_REQUIRED" or
        m19.get("schema")!="STAGE19_ALL_4884_ERA5_DIAGNOSTIC_v1" or
        m19.get("n_target_rows")!=4884 or
        m19.get("scientifically_approved_rows")!=0 or
        m19.get("scientific_status")!="NUMERICAL_SENSITIVITY_ONLY_ALL_ROWS_HOLD" or
        m19.get("stage11_targets_sha256")!=sha(stage11/STAGE11CSV) or
        m19.get("stage11_manifest_sha256")!=sha(stage11/"manifest.json") or
        m19.get("US_Ho1_UTC_offset_status")!="PROVISIONAL_BADM_NOT_VERIFIED"):
        raise ValueError("Stage11 or Stage19 source/scientific contract changed")
    load_stage54(stage54,stage11)
    target=pd.read_csv(stage11/STAGE11CSV,dtype={"site":str,"time":str})
    detail=pd.read_csv(stage19/STAGE19CSV,dtype={"site":str,"local":str})
    required={"site","local","year","decision","UTC_offset_evidence",
      "ERA5_RH_water_pct","ERA5_T2M_C","ERA5_Td2M_C",
      "ERA5_surface_P_Pa","retained_TA_C","retained_PA_kPa",
      "TA_F_QC","VPD_F_QC","sensitivity_VPD_hPa",
      "sensitivity_QBOT_kgkg","sensitivity_numeric_valid",
      "cold_water_saturation_caution","original_Stage11_HOLD_preserved",
      "scientific_decision"}
    if not required.issubset(detail.columns):
        raise ValueError("Stage19 report missing required fields "+str(required-set(detail.columns)))
    if (len(detail)!=4884 or len(target)!=4884 or
        Counter(detail.site)!=Counter(TOTALS) or
        not detail.scientific_decision.astype(str).str.startswith("HOLD_").all()):
        raise ValueError("Stage19 4,884/source site contract changed")
    a=identity(target,"time")
    b=identity(detail,"local")
    if set(zip(a.site,a.site_local_key))!=set(zip(b.site,b.site_local_key)):
        raise ValueError("Stage19 exact source-local-time identities do not match Stage11")
    if (truth(b.original_Stage11_HOLD_preserved).sum()!=14 or
        m19.get("n_stage11_holds")!=14):
        raise ValueError("Stage19 14 explicit original Stage11 HOLD flags changed")
    if verify_receipts:
        receipt_map=m19.get("cds_receipt_sha256",{})
        netcdf_map=m19.get("verified_netcdf_sha256",{})
        if len(receipt_map)!=39 or len(netcdf_map)!=39:
            raise ValueError("Expected Stage19 39 verified ERA5 physical files")
        for p,digest in receipt_map.items():
            if sha(Path(p).resolve(strict=True))!=digest:
                raise ValueError("Original Stage19 external CDS receipt SHA changed")
        for p,digest in netcdf_map.items():
            if sha(Path(p).resolve(strict=True))!=digest:
                raise ValueError("Original Stage19 external CDS NetCDF SHA changed")
    return b,m19,{"stage11_targets_sha256":sha(stage11/STAGE11CSV),
        "stage11_manifest_sha256":sha(stage11/"manifest.json"),
        "stage19_report_sha256":sha(stage19/STAGE19CSV),
        "stage19_manifest_sha256":sha(stage19/"manifest.json"),
        "stage54_manifest_sha256":sha(stage54/"crosswalk_manifest.json")}

def route(row):
    if not row["num_valid"]:return "HOLD_NUMERICAL_OR_SOURCE_INPUT"
    if row["site"]=="US-Ho1":return "HOLD_HO1_PROVISIONAL_LOCAL_UTC_OFFSET"
    if row["T_QC_not0"]:return "HOLD_ORIGINAL_TEMPERATURE_QC"
    if row["large_T_delta"]:return "HOLD_TOWER_ERA5_T_DELTA_OVER_8C"
    if row["freezing"]:return "HOLD_WATER_ICE_SATURATION"
    if row["VPD_QC_not0"]:return "HOLD_ORIGINAL_VPD_QC"
    return "HOLD_FINAL_SCIENTIFIC_RELEASE_REQUIRED"

def self_test():
    assert sum(TOTALS.values())==4884
    assert route(dict(num_valid=True,site="US-Ho1",T_QC_not0=False,
         large_T_delta=False,freezing=False,VPD_QC_not0=False))==(
         "HOLD_HO1_PROVISIONAL_LOCAL_UTC_OFFSET")
    assert route(dict(num_valid=False,site="US-EML",T_QC_not0=False,
         large_T_delta=False,freezing=False,VPD_QC_not0=False))==(
         "HOLD_NUMERICAL_OR_SOURCE_INPUT")
    assert route(dict(num_valid=True,site="US-EML",T_QC_not0=False,
         large_T_delta=False,freezing=False,VPD_QC_not0=False))==(
         "HOLD_FINAL_SCIENTIFIC_RELEASE_REQUIRED")
    print("STAGE55 SELF-TEST PASS | exact 4884 and conservative multi-gate science routes")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--audit",action="store_true")
    p.add_argument("--stage19",type=Path)
    p.add_argument("--stage11",type=Path,default=S11)
    p.add_argument("--stage54",type=Path,default=S54)
    p.add_argument("--output-root",type=Path,default=BASE/"reports")
    p.add_argument("--skip-era5-rehash",action="store_true",
        help="Skip re-hashing large CDS payload NetCDFs; source report still checked")
    opts=p.parse_args()
    if opts.self_test:return self_test()
    s11=opts.stage11.resolve(strict=True)
    s54=opts.stage54.resolve(strict=True)
    s19=choose_stage19(opts.stage19,s11)
    d,m,pins=load(s19,s11,s54,not opts.skip_era5_rehash)
    d["num_valid"]=truth(d.sensitivity_numeric_valid)
    d["freezing"]=truth(d.cold_water_saturation_caution)
    original_t=pd.to_numeric(d.retained_TA_C,errors="coerce")
    era_t=pd.to_numeric(d.ERA5_T2M_C,errors="coerce")
    d["T_site_minus_ERA5_C"]=original_t-era_t
    d["large_T_delta"]=(original_t-era_t).abs()>8
    tq=pd.to_numeric(d.TA_F_QC,errors="coerce")
    vq=pd.to_numeric(d.VPD_F_QC,errors="coerce")
    d["T_QC_not0"]=tq.ne(0)
    d["VPD_QC_not0"]=vq.ne(0)
    d["science_route"]=d.apply(route,axis=1)
    if len(d)!=4884 or d.science_route.isna().any():
        raise ValueError("Stage55 complete-row science route contract failed")
    per_site=[]
    for site in TOTALS:
        rows=d.loc[d.site.eq(site)]
        per_site.append(dict(site=site,n_Stage11_HOLD=len(rows),
           invalid_numeric=int((~rows.num_valid).sum()),
           original_T_QC_not0=int(rows.T_QC_not0.sum()),
           original_VPD_QC_not0=int(rows.VPD_QC_not0.sum()),
           tower_vs_ERA_T_gt8C=int(rows.large_T_delta.sum()),
           water_vs_ice_caution=int(rows.freezing.sum()),
           preliminary_science_route_not_final=int(
               rows.science_route.eq("HOLD_FINAL_SCIENTIFIC_RELEASE_REQUIRED").sum())))
    print("STAGE55 SOURCE CHECK PASS | Stage11=4884, Stage19=4884, Stage54 overlap=0")
    print("REUSED_STAGE19",s19)
    print("SCIENCE_ROUTE_COUNTS",dict(Counter(d.science_route)))
    for row in per_site:print("SITE",row)
    print("IMPORTANT: ALL 4884 remain HOLD; Stage53 444 already separate, NOT re-applied")
    if opts.check:
        print("STAGE55 CHECK PASS | zero writes");return
    root=opts.output_root.resolve()
    if root in (s11,s19,s54) or any(src in root.parents for src in (s11,s19,s54)):
        raise ValueError("Report root overlaps protected upstream")
    dest=root/("stage55_4884_existing_ERA5_science_triage_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Stage55 science review report incomplete; not model-ready.\n")
    outputs={
       "4884_existing_ERA5_candidates_science_routes.csv":d,
       "five_site_4884_review_summary.csv":pd.DataFrame(per_site),
       "science_route_counts.csv":pd.DataFrame([
           {"route":k,"n":v} for k,v in sorted(Counter(d.science_route).items())])}
    shas={}
    for name,df in outputs.items():
        file=dest/name
        df.to_csv(file,index=False)
        shas[name]=sha(file)
    if (sha(s19/STAGE19CSV)!=pins["stage19_report_sha256"] or
        sha(s11/STAGE11CSV)!=pins["stage11_targets_sha256"] or
        sha(s54/"crosswalk_manifest.json")!=pins["stage54_manifest_sha256"]):
        raise ValueError("An upstream report changed during Stage55 triage")
    (dest/"science_triage_manifest.json").write_text(json.dumps({
       "schema":"STAGE55_4884_STAGE19_REVIEW_ONLY_v1",
       "stage11":str(s11),"stage19":str(s19),"stage54":str(s54),
       "input_sha256":pins,"output_sha256":shas,
       "n_stage11":4884,"n_stage53_separate":444,"overlap":0,
       "all_rows_scientific_hold":True,
       "automatic_replacement_approvals":0,"forcing_modified":False},indent=2,
       sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE55 AUDIT PASS | 4884 held external ERA5 candidates classified; zero auto-approved")
    print("REPORT",dest)
    print("NO ORIGINAL, STAGE19, STAGE53, STAGE54, DATM, CIME OR SLURM CHANGES")
if __name__=="__main__":
    main()

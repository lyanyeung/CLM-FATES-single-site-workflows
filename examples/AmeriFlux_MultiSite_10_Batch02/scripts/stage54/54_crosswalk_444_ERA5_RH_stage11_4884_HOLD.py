#!/usr/bin/env python3
"""Batch02 Stage54: read-only exact timestamp crosswalk Stage53 RH patch vs Stage11 HOLD.

Stage53 = 444 user-selected same-CDS ERA5 RH/VPD/QBOT row proposals.
Stage11 = 4,884 distinct HOLD temperature/humidity events, formerly
tracked through Stage08. Compare original tower local timestamps only:
Stage53 (site,timestamp_start) and Stage11 (site,time).
Never append the same input row twice or silently approve existing HOLD.
No raw input, model forcing, DATM, CIME, Slurm or old ledger writes.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib
import json
import pandas as pd

BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S53=BASE/"reports/stage53_444_ERA5_RH_only_staging_20261024T100652Z_543ef3f1"
S11=BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
PATCH="444_original_RH_zero_or_gt100_unified_ERA5_RH_VPD_QBOT.csv"
HOLD="cold_humidity_repair_proposals.csv"
SITE_COUNTS={"US-Ha1":398,"US-Ho2":7,"US-ICh":9,"US-ICt":30}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()

def site_time(frame,site_col,time_col,is_numeric_stamp=False):
    if is_numeric_stamp:
        parsed=pd.to_datetime(frame[time_col].astype(str),format="%Y%m%d%H%M",errors="raise")
    else:
        parsed=pd.to_datetime(frame[time_col].astype(str),errors="raise")
    if parsed.isna().any() or parsed.dt.tz is not None:
        raise ValueError("Unexpected missing or timezone-aware original tower time")
    out=frame.copy()
    out["local_timestamp_key"]=parsed.dt.strftime("%Y%m%d%H%M")
    if out.duplicated([site_col,"local_timestamp_key"]).any():
        raise ValueError("Duplicate site/local-time target in "+time_col)
    return out

def read_sources(s53,s11):
    if (s53/"INCOMPLETE_DO_NOT_USE").exists() or (
        s11/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file() is False:
        raise ValueError("Missing upstream HOLD marker or incomplete patch")
    m53=json.loads((s53/"ledger_provenance.json").read_text())
    m11=json.loads((s11/"manifest.json").read_text())
    p53=s53/PATCH
    p11=s11/HOLD
    if (m53.get("schema")!="STAGE53_USER_SELECTED_RH_ONLY_LEDGER_v1" or
        m53.get("row_count")!=444 or m53.get("original_RH_zero")!=39 or
        m53.get("original_RH_gt100")!=405 or
        m53.get("approved_for_DATM") is not False or
        m53.get("approved_for_spinup") is not False or
        m53.get("model_forcing_modified") is not False or
        m53.get("output_sha256")!=sha(p53)):
        raise ValueError("Stage53 immutable manifest/payload mismatch")
    if (m11.get("scientific_status")!="HOLD_INDEPENDENT_VALIDATION_REQUIRED" or
        int(m11.get("n_target_rows",0))!=4884):
        raise ValueError("Stage11 original 4,884-HOLD scientific status differs")
    for path,digest in m11.get("input_hashes",{}).items():
        if sha(path)!=digest:
            raise ValueError("Stage11 input altered: "+path)
    a=pd.read_csv(p53,dtype={"site":str,"timestamp_start":str})
    b=pd.read_csv(p11,dtype={"site":str,"time":str})
    if not {"site","timestamp_start","replacement_RH_pct",
            "replacement_VPD_hPa","replacement_QBOT_kg_kg",
            "approved_for_DATM"}.issubset(a) or not (
            {"site","time","decision"}.issubset(b)):
        raise ValueError("Missing exact Stage53/Stage11 source columns")
    if (len(a)!=444 or len(b)!=4884 or
        Counter(a.site)!=Counter(SITE_COUNTS) or
        a.approved_for_DATM.astype(str).str.lower().ne("false").any() or
        not b.decision.isin(("HOLD_NO_SUPPORTED_ANALOGUE",
                             "PROVISIONAL_ANALOGUE_REVIEW_REQUIRED")).all()):
        raise ValueError("Original patch or held cohort changed")
    a=site_time(a,"site","timestamp_start",True)
    b=site_time(b,"site","time")
    return a,b,{"stage53_patch_sha256":sha(p53),
                "stage53_manifest_sha256":sha(s53/"ledger_provenance.json"),
                "stage11_HOLD_sha256":sha(p11),
                "stage11_manifest_sha256":sha(s11/"manifest.json")}

def self_test():
    a=site_time(pd.DataFrame({"site":["US-ICh"],
        "timestamp_start":["200801020330"]}),"site","timestamp_start",True)
    b=site_time(pd.DataFrame({"site":["US-ICh"],
        "time":["2008-01-02 03:30:00"]}),"site","time")
    assert a.local_timestamp_key.iloc[0]==b.local_timestamp_key.iloc[0]
    assert sum(SITE_COUNTS.values())==444
    print("STAGE54 SELF-TEST PASS | native local-time identity and 444 exact targets")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mx=p.add_mutually_exclusive_group(required=True)
    mx.add_argument("--self-test",action="store_true")
    mx.add_argument("--check",action="store_true")
    mx.add_argument("--audit",action="store_true")
    p.add_argument("--stage53",type=Path,default=S53)
    p.add_argument("--stage11",type=Path,default=S11)
    p.add_argument("--report-root",type=Path,default=BASE/"reports")
    opt=p.parse_args()
    if opt.self_test:
        self_test()
        return
    s53=opt.stage53.resolve(strict=True)
    s11=opt.stage11.resolve(strict=True)
    a,b,pins=read_sources(s53,s11)
    overlap=a.merge(b,on=["site","local_timestamp_key"],how="inner",
                    suffixes=("_stage53","_stage11"),validate="one_to_one")
    ida=pd.MultiIndex.from_frame(a[["site","local_timestamp_key"]])
    idb=pd.MultiIndex.from_frame(b[["site","local_timestamp_key"]])
    aonly=a[~ida.isin(idb)].copy()
    bonly=b[~idb.isin(ida)].copy()
    shared=len(overlap)
    if len(aonly)+shared!=444 or len(bonly)+shared!=4884:
        raise ValueError("Crosswalk population arithmetic failed")
    site_summary=[]
    for s in sorted(set(a.site)|set(b.site)):
        site_summary.append(dict(site=s,
            Stage53_444_RH=int((a.site==s).sum()),
            Stage11_4884_HOLD=int((b.site==s).sum()),
            exact_timestamp_overlap=int((overlap.site==s).sum()),
            Stage53_unique_after_crosswalk=int((aonly.site==s).sum()),
            Stage11_HOLD_unique_after_crosswalk=int((bonly.site==s).sum())))
    print("STAGE54 SOURCE CHECK PASS | Stage53=444, Stage11=4884")
    print("EXACT SAME-SITE/TOWER-LOCAL-TIMESTAMP OVERLAP",shared)
    print("STAGE53 ONLY",len(aonly),"STAGE11 ONLY",len(bonly))
    for item in site_summary:
        print("SITE",item)
    print("OVERLAPS REQUIRE ONE REVIEW DECISION PER ORIGINAL SITE/TIME; NO AUTO-MERGE")
    if opt.check:
        print("STAGE54 CHECK PASS | no writes")
        return
    root=opt.report_root.resolve()
    if root in (s53,s11) or any(s in root.parents for s in (s53,s11)):
        raise ValueError("Output directory overlaps source")
    dest=root/("stage54_444_vs_4884_timestamp_crosswalk_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Incomplete review crosswalk; no source or forcing changes.\n")
    data={
       "Stage53_Stage11_exact_timestamp_overlap.csv":overlap,
       "Stage53_444_not_in_Stage11_HOLD.csv":aonly,
       "Stage11_4884_not_in_Stage53_patch.csv":bonly,
       "per_site_exact_overlap_summary.csv":pd.DataFrame(site_summary)}
    hashes={}
    for name,df in data.items():
        file=dest/name
        df.to_csv(file,index=False)
        hashes[name]=sha(file)
    if (sha(s53/PATCH)!=pins["stage53_patch_sha256"] or
        sha(s11/HOLD)!=pins["stage11_HOLD_sha256"]):
        raise ValueError("Source report mutated while writing crosswalk")
    manifest={"schema":"STAGE54_BATCH02_EXACT_SITE_LOCAL_TIME_CROSSWALK_v1",
        "source_stage53":str(s53),"source_stage11":str(s11),
        "input_sha256":pins,"output_sha256":hashes,
        "stage53_count":444,"stage11_count":4884,
        "intersection_count":shared,
        "stage53_only_count":len(aonly),
        "stage11_only_count":len(bonly),
        "no_automatic_conflict_resolution":True,
        "approved_for_DATM":False,"forcing_modified":False}
    (dest/"crosswalk_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE54 AUDIT PASS | exact 444-vs-4884 crosswalk")
    print("REPORT",dest)
    print("NO MODEL INPUT, ORIGINAL SOURCE, PRIOR PATCH OR SLURM CHANGES")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Batch02 Stage53: READ-ONLY staging of user's 444 same-CDS-ERA5 RH choices.

Use Stage50 independent ERA5 water RH for ALL original RH==0 / RH>100.
Retain EC air T and site P; recompute VPD and QBOT consistently.
27 US-ICt T QC1/QC2 and 405 supersaturation/phase cases stay flagged.
Writes ONLY a new sparse review ledger; no original or model-input edits.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib
import json
import numpy as np
import pandas as pd

BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S50=BASE/"reports/stage50_unified_external_ERA5_RH_20261024T094206Z_7d901572"
S52=BASE/"reports/stage52_RH_gt100_phase_and_ICt_QC_review_20261024T095901Z_9b4118ce"
F50="RH_zero_gt100_444_ERA5_candidate_patch.csv"
F52="444_original_RH_candidate_review_queue.csv"
PRODUCT="reanalysis-era5-single-levels-timeseries"
SITES={"US-Ha1":398,"US-Ho2":7,"US-ICh":9,"US-ICt":30}
ROUTES={"CANDIDATE_ONLY_REVIEW_ZERO_RH":12,
        "CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE":405,
        "MANUAL_JOINT_T_AND_HUMIDITY_REVIEW":27}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1048576),b""):
            h.update(block)
    return h.hexdigest()

def humidity(ta,rh,pa):
    t=np.asarray(ta,dtype=float)
    frac=np.asarray(rh,dtype=float)/100
    p=np.asarray(pa,dtype=float)*1000
    sat=6.112*np.exp(17.67*t/(t+243.5))
    actual=sat*frac
    return sat-actual,0.622*100*actual/(p-0.378*100*actual)

def self_test():
    v,q=humidity([20],[50],[100])
    assert 11.67<v[0]<11.70 and .007<q[0]<.008
    assert sum(SITES.values())==444 and sum(ROUTES.values())==444
    print("STAGE53 SELF-TEST PASS | 444 RH-only scope and paired water VPD/QBOT")

def load(s50,s52):
    if any((d/"INCOMPLETE_DO_NOT_USE").exists() for d in (s50,s52)):
        raise ValueError("Upstream report incomplete")
    m50=json.loads((s50/"candidate_provenance.json").read_text())
    m52=json.loads((s52/"audit_manifest.json").read_text())
    p50=s50/F50
    p52=s52/F52
    if (m50.get("schema")!="STAGE50_444_EXTERNAL_CDS_ERA5_REVIEW_v1" or
        m50.get("target_count")!=444 or m50.get("dataset")!=PRODUCT or
        m50.get("approved_replacements")!=0 or
        m50.get("patch_sha256")!=sha(p50)):
        raise ValueError("Stage50 provenanced candidate mismatch")
    pins=m52.get("pinned_inputs",{})
    if (m52.get("schema")!="STAGE52_BATCH02_PHASE_TQC_AUDIT_v1" or
        m52.get("stage50_path")!=str(s50) or
        m52.get("science_approved_replacements")!=0 or
        m52.get("forcing_modified") is not False or
        pins.get("stage50_patch_sha256")!=sha(p50) or
        pins.get("stage50_provenance_sha256")!=sha(s50/"candidate_provenance.json") or
        m52.get("output_sha256",{}).get(F52)!=sha(p52)):
        raise ValueError("Stage52 source SHA/science status mismatch")
    for name,digest in m52["output_sha256"].items():
        if sha(s52/name)!=digest:
            raise ValueError("Stage52 file SHA mismatch: "+name)
    dtype={"site":str,"timestamp_start":str,"source_sha256":str}
    a=pd.read_csv(p50,dtype=dtype)
    b=pd.read_csv(p52,dtype=dtype)
    required=("site","timestamp_start","source_csv_row","source_sha256",
              "original_RH_pct","candidate_RH_pct","original_TA_C",
              "original_PA_kPa","candidate_VPD_hPa",
              "candidate_QBOT_kg_kg","original_TA_QC",
              "candidate_status","ERA5_dataset","ERA5_netcdf_sha256")
    if not set(required).issubset(a) or not set(required).issubset(b):
        raise ValueError("Required input field missing")
    if (len(a)!=444 or len(b)!=444 or Counter(a.site)!=Counter(SITES) or
        Counter(a.candidate_status)!=Counter(ROUTES) or
        a.duplicated(["site","timestamp_start"]).any() or
        b.duplicated(["site","timestamp_start"]).any()):
        raise ValueError("Target count or timestamp scope mismatch")
    a=a.sort_values(["site","timestamp_start"]).reset_index(drop=True)
    b=b.sort_values(["site","timestamp_start"]).reset_index(drop=True)
    for field in ("site","timestamp_start","source_csv_row","source_sha256",
                  "candidate_status","ERA5_netcdf_sha256"):
        if not a[field].astype(str).equals(b[field].astype(str)):
            raise ValueError("Stage50/52 source identity mismatch "+field)
    if not a.ERA5_dataset.eq(PRODUCT).all():
        raise ValueError("Mixed CDS product")
    raw=pd.to_numeric(a.original_RH_pct,errors="coerce")
    rh=pd.to_numeric(a.candidate_RH_pct,errors="coerce")
    t=pd.to_numeric(a.original_TA_C,errors="coerce")
    p=pd.to_numeric(a.original_PA_kPa,errors="coerce")
    if (int(raw.eq(0).sum())!=39 or int(raw.gt(100).sum())!=405 or
        not rh.between(0.000001,100.05).all() or
        not t.between(-80,65).all() or
        not p.between(50,110).all()):
        raise ValueError("Original RH or retained T/P invalid")
    joint=a.candidate_status.eq("MANUAL_JOINT_T_AND_HUMIDITY_REVIEW")
    qc=pd.to_numeric(a.original_TA_QC,errors="coerce")
    if (int(joint.sum())!=27 or not a.loc[joint,"site"].eq("US-ICt").all()
        or int(qc[joint].eq(1).sum())!=14 or int(qc[joint].eq(2).sum())!=13):
        raise ValueError("Original US-ICt temperature QC1/QC2 differs")
    v,q=humidity(t.to_numpy(),rh.to_numpy(),p.to_numpy())
    if (not np.isfinite(v).all() or not np.isfinite(q).all() or
        (v < -0.005).any() or (q<=0).any() or (q>=.08).any() or
        not np.allclose(v,pd.to_numeric(a.candidate_VPD_hPa),rtol=1e-7,atol=1e-8) or
        not np.allclose(q,pd.to_numeric(a.candidate_QBOT_kg_kg),rtol=1e-7,atol=1e-9)):
        raise ValueError("Stage50 ERA5 RH paired Tsite/VPD/QBOT physics mismatch")
    digests={"stage50_patch":sha(p50),"stage50_manifest":sha(s50/"candidate_provenance.json"),
             "stage52_queue":sha(p52),"stage52_manifest":sha(s52/"audit_manifest.json")}
    return a,v,q,digests

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--stage",action="store_true")
    parser.add_argument("--stage50",type=Path,default=S50)
    parser.add_argument("--stage52",type=Path,default=S52)
    parser.add_argument("--output-root",type=Path,default=BASE/"reports")
    args=parser.parse_args()
    if args.self_test:return self_test()
    s50=args.stage50.resolve(strict=True)
    s52=args.stage52.resolve(strict=True)
    a,v,q,pins=load(s50,s52)
    print("STAGE53 INPUT VERIFIED | 444 same-CDS ERA5 RH; 405 RH>100; 39 RH=0")
    print("TOWER T PRESERVED | 27 ICt T_QC REVIEW = 14 QC1 + 13 QC2")
    if args.check:
        print("STAGE53 CHECK PASS | all original/forcing data untouched")
        return
    root=args.output_root.resolve()
    if root in (s50,s52) or any(s in root.parents for s in (s50,s52)):
        raise ValueError("Output root overlaps earlier-stage report")
    table=a.copy()
    table["replacement_RH_pct"]=pd.to_numeric(a.candidate_RH_pct,errors="raise")
    table["replacement_VPD_hPa"]=v
    table["replacement_QBOT_kg_kg"]=q
    table["retained_TA_C"]=pd.to_numeric(a.original_TA_C,errors="raise")
    table["retained_PA_kPa"]=pd.to_numeric(a.original_PA_kPa,errors="raise")
    table["T_QC_review_required"]=a.candidate_status.eq("MANUAL_JOINT_T_AND_HUMIDITY_REVIEW")
    table["RH_supersaturation_phase_review_required"]=a.candidate_status.eq("CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE")
    table["user_RH_policy"]="REPLACE_ALL_ORIGINAL_RH_0_OR_GT100_WITH_SAME_CDS_ERA5_RH"
    table["temperature_policy"]="RETAIN_EC_TOWER_TA_UNCHANGED"
    table["approved_for_DATM"]=False
    table["approved_for_spinup"]=False
    out=root/("stage53_444_ERA5_RH_only_staging_"+datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    mark=out/"INCOMPLETE_DO_NOT_USE"
    mark.write_text("Staged RH patch only: not model-ready or scientific QC approval.\n")
    patch=out/"444_original_RH_zero_or_gt100_unified_ERA5_RH_VPD_QBOT.csv"
    table.to_csv(patch,index=False)
    if sha(s50/F50)!=pins["stage50_patch"] or sha(s52/F52)!=pins["stage52_queue"]:
        raise ValueError("Original upstream inputs changed during staging")
    manifest={"schema":"STAGE53_USER_SELECTED_RH_ONLY_LEDGER_v1",
              "row_count":444,"original_RH_zero":39,"original_RH_gt100":405,
              "temperature_QC_review_count":27,"phase_review_count":405,
              "ERA5_dataset":PRODUCT,"RH_replacement_user_selected":True,
              "EC_temperature_replaced":False,"model_forcing_modified":False,
              "approved_for_DATM":False,"approved_for_spinup":False,
              "stage50":str(s50),"stage52":str(s52),"source_sha256":pins,
              "output_sha256":sha(patch)}
    (out/"ledger_provenance.json").write_text(
        json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    mark.unlink()
    print("STAGE53 STAGING PASS | all 444 same-ERA5 RH replacements with paired VPD/QBOT")
    print("REPORT",out)
    print("27 US-ICt T QC HOLD and 405 RH>100 phase flags retained")
    print("NO RAW, EXISTING CANDIDATE, DATM, SPINUP, OR SLURM CHANGES")
if __name__=="__main__":
    main()

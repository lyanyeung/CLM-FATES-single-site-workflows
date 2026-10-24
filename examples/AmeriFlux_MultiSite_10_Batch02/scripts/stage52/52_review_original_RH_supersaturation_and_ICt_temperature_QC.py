#!/usr/bin/env python3
"""Batch02 Stage52: read-only review of 405 original RH>100 and 27 US-ICt T-QC.

Stage50 generated 444 external CDS ERA5 water-RH candidates (all 10 grid-years
verified), Stage51 generated alternative joint ERA5 T/RH/VPD/QBOT for 27 cases.
Stage52 checks exact immutable Stage50/51 reports and their hashes, then
summarises the cold-season/phase and original T-QC evidence without authorising
any change to raw FLUXNET, surface, DATM, forcing, CIME or Slurm data.
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
STAGE50=BASE/"reports/stage50_unified_external_ERA5_RH_20261024T094206Z_7d901572"
STAGE51=BASE/"reports/stage51_444_RH_and_27_joint_T_review_20261024T094847Z_081665b1"
SITES=("US-Ha1","US-Ho2","US-ICh","US-ICt")
TOTALS={"US-Ha1":398,"US-Ho2":7,"US-ICh":9,"US-ICt":30}
DATASET="reanalysis-era5-single-levels-timeseries"
STATES={"CANDIDATE_ONLY_REVIEW_ZERO_RH":12,
        "CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE":405,
        "MANUAL_JOINT_T_AND_HUMIDITY_REVIEW":27}
CSV50="RH_zero_gt100_444_ERA5_candidate_patch.csv"
CSV51_JOINT="27_joint_ERA5_T_RH_QBOT_review.csv"
CSV51_PHASE="405_raw_RH_gt100_phase_review.csv"
CSV51_SITES="444_four_site_review_breakdown.csv"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def number(frame,name):
    return pd.to_numeric(frame[name],errors="coerce")

def rh_bin(raw):
    if raw==0:return "RH_ZERO"
    if 100<raw<=100.5:return "RH_GT100_TO100p5"
    if 100.5<raw<=101:return "RH_GT100p5_TO101"
    if 101<raw<=105:return "RH_GT101_TO105"
    if raw>105:return "RH_GT105"
    raise ValueError("Out-of-scope raw RH "+str(raw))

def qc_bin(value):
    if not np.isfinite(value):return "QC_MISSING"
    if value==0:return "QC0"
    if value==1:return "QC1"
    if value==2:return "QC2"
    if value==3:return "QC3"
    return "QC_OTHER_"+str(value)

def validate(source50,source51):
    if (source50/"INCOMPLETE_DO_NOT_USE").exists() or (
        source51/"INCOMPLETE_DO_NOT_USE").exists()):
        raise ValueError("An upstream stage has incomplete marker")
    p50=source50/"candidate_provenance.json"
    p51=source51/"review_provenance.json"
    m50=json.loads(p50.read_text())
    m51=json.loads(p51.read_text())
    f50=source50/CSV50
    if (m50.get("schema")!="STAGE50_444_EXTERNAL_CDS_ERA5_REVIEW_v1" or
        m50.get("dataset")!=DATASET or m50.get("target_count")!=444 or
        m50.get("approved_replacements")!=0 or
        m50.get("model_ready") is not False or
        m50.get("patch_sha256")!=sha(f50)):
        raise ValueError("Pinned Stage50 source/scientific state differs")
    if (m51.get("source_stage50")!=str(source50) or
        m51.get("stage50_patch_sha256")!=sha(f50) or
        m51.get("stage50_provenance_sha256")!=sha(p50) or
        m51.get("count")!=444 or m51.get("joint_T_RH")!=27 or
        m51.get("supersat_phase")!=405 or
        m51.get("original_zero_T_retained")!=12 or
        m51.get("approved_for_DATM") is not False or
        m51.get("model_input_modified") is not False):
        raise ValueError("Stage51 provenance mismatch")
    originals={CSV51_JOINT,CSV51_PHASE,CSV51_SITES}
    if set(m51.get("output_sha256",{}))!=originals:
        raise ValueError("Stage51 output set differs")
    for name in originals:
        if sha(source51/name)!=m51["output_sha256"][name]:
            raise ValueError("Stage51 report SHA256 changed "+name)
    cols={"site","timestamp_start","original_RH_pct","candidate_RH_pct",
          "original_TA_C","original_TA_QC","original_VPD_hPa",
          "ERA5_T2M_C","retained_T_minus_ERA5_T_C","candidate_status",
          "ERA5_netcdf_sha256","source_sha256","ERA5_dataset"}
    patch=pd.read_csv(f50,dtype={"site":str,"timestamp_start":str,
                                 "source_sha256":str,"ERA5_netcdf_sha256":str})
    if len(patch)!=444 or not cols.issubset(patch.columns):
        raise ValueError("Wrong Stage50 columns/scope")
    if Counter(patch.site)!=Counter(TOTALS) or Counter(
            patch.candidate_status)!=Counter(STATES):
        raise ValueError("Stage50 site/status counts differ")
    if patch.duplicated(["site","timestamp_start"]).any():
        raise ValueError("Duplicate Stage50 site timestamp")
    if not patch.ERA5_dataset.eq(DATASET).all():
        raise ValueError("Stage50 CDS dataset differs")
    if (int((number(patch,"original_RH_pct")==0).sum()),
        int((number(patch,"original_RH_pct")>100).sum()))!=(39,405):
        raise ValueError("Stage50 exact RH0/RH>100 split differs")
    phase=pd.read_csv(source51/CSV51_PHASE,dtype={"site":str,"timestamp_start":str})
    joint=pd.read_csv(source51/CSV51_JOINT,dtype={"site":str,"timestamp_start":str})
    per_site=pd.read_csv(source51/CSV51_SITES,dtype={"site":str})
    if len(phase)!=405 or len(joint)!=27 or len(per_site)!=4:
        raise ValueError("Stage51 row lengths differ")
    if set(joint.site)!={"US-ICt"} or set(phase.site)!={"US-Ha1","US-ICh"}:
        raise ValueError("Unexpected site for scientific-review cohort")
    for report,ident in [(phase,"CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE"),
                         (joint,"MANUAL_JOINT_T_AND_HUMIDITY_REVIEW")]:
        expected=set(map(tuple,patch.loc[
            patch.candidate_status==ident,["site","timestamp_start"]].to_numpy()))
        actual=set(map(tuple,report[["site","timestamp_start"]].to_numpy()))
        if expected!=actual or len(actual)!=len(report):
            raise ValueError("Stage50/Stage51 timestamp identity mismatch")
    if not np.isfinite(number(patch,"candidate_RH_pct")).all():
        raise ValueError("Stage50 ERA5 candidate RH nonfinite")
    return patch,phase,joint,per_site,{ "stage50_patch_sha256":sha(f50),
      "stage50_provenance_sha256":sha(p50),
      "stage51_provenance_sha256":sha(p51),
      "stage51_files_sha256":m51["output_sha256"]}

def self_test():
    examples=[(0,"RH_ZERO"),(100.2,"RH_GT100_TO100p5"),
              (100.75,"RH_GT100p5_TO101"),(102,"RH_GT101_TO105"),
              (120,"RH_GT105")]
    for value,expected in examples:
        assert rh_bin(value)==expected
    assert [qc_bin(x) for x in (0.,1.,2.,3.,np.nan)]==[
        "QC0","QC1","QC2","QC3","QC_MISSING"]
    assert sum(TOTALS.values())==444 and sum(STATES.values())==444
    print("STAGE52 SELF-TEST PASS | RH>100 severity, T-QC bins, 444 target contract")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--audit",action="store_true")
    ap.add_argument("--stage50",type=Path,default=STAGE50)
    ap.add_argument("--stage51",type=Path,default=STAGE51)
    ap.add_argument("--report-root",type=Path,default=BASE/"reports")
    args=ap.parse_args()
    if args.self_test:return self_test()
    src50=args.stage50.resolve(strict=True)
    src51=args.stage51.resolve(strict=True)
    patch,phase,joint,site51,pins=validate(src50,src51)
    patch=patch.copy()
    patch["original_RH_bin"]=number(patch,"original_RH_pct").map(rh_bin)
    patch["original_TA_QC_bin"]=number(patch,"original_TA_QC").map(qc_bin)
    patch["tower_T_below0"]=number(patch,"original_TA_C")<0
    patch["site_ERA_T_abs_delta_C"]=number(
        patch,"retained_T_minus_ERA5_T_C").abs()
    patch["ERA5_minus_raw_RH_pct"]=number(
        patch,"candidate_RH_pct")-number(patch,"original_RH_pct")
    patch["original_VPD_near_zero"]=number(
        patch,"original_VPD_hPa").abs()<=0.005
    patch["original_year"]=pd.to_datetime(
        patch.timestamp_start,format="%Y%m%d%H%M",errors="raise").dt.year

    site_rows=[]
    for site in SITES:
        x=patch.loc[patch.site==site]
        above=x[x.original_RH_pct>100]
        j=x[x.candidate_status=="MANUAL_JOINT_T_AND_HUMIDITY_REVIEW"]
        site_rows.append(dict(
            site=site,total=len(x),
            raw_RH_zero=int(x.original_RH_pct.eq(0).sum()),
            raw_RH_gt100=len(above),
            raw_RH_gt100_100_to100p5=int(above.original_RH_bin.eq(
                "RH_GT100_TO100p5").sum()),
            raw_RH_gt100_100p5_to101=int(above.original_RH_bin.eq(
                "RH_GT100p5_TO101").sum()),
            raw_RH_gt100_101_to105=int(above.original_RH_bin.eq(
                "RH_GT101_TO105").sum()),
            raw_RH_gt100_over105=int(above.original_RH_bin.eq(
                "RH_GT105").sum()),
            raw_RH_gt100_T_below0=int(above.tower_T_below0.sum()),
            raw_RH_gt100_original_VPD_near_zero=int(
                above.original_VPD_near_zero.sum()),
            raw_RH_gt100_original_max=float(above.original_RH_pct.max())
                if len(above) else None,
            joint_T_QC_review=len(j),
            joint_T_QC0=int(j.original_TA_QC_bin.eq("QC0").sum()),
            joint_T_QC1=int(j.original_TA_QC_bin.eq("QC1").sum()),
            joint_T_QC2=int(j.original_TA_QC_bin.eq("QC2").sum()),
            joint_T_QC3=int(j.original_TA_QC_bin.eq("QC3").sum()),
            joint_T_QC_missing=int(j.original_TA_QC_bin.eq("QC_MISSING").sum()),
            joint_T_abs_delta_max_C=float(j.site_ERA_T_abs_delta_C.max())
                if len(j) else None,
            joint_T_abs_delta_over8C=int(
                (j.site_ERA_T_abs_delta_C>8).sum()),
            original_years="|".join(map(str,sorted(x.original_year.unique())))
        ))
    severity=patch.loc[patch.original_RH_pct>100].sort_values(
        ["site","original_RH_pct"],ascending=[True,False]).copy()
    jointdetail=patch.loc[patch.candidate_status==
        "MANUAL_JOINT_T_AND_HUMIDITY_REVIEW"].sort_values(
        ["site","timestamp_start"]).copy()
    jcalc=joint[["site","timestamp_start","science_trigger","joint_ERA5_T_C",
                 "joint_ERA5_RH_pct","joint_ERA5_VPD_hPa",
                 "joint_ERA5_QBOT_kg_kg_grid_P",
                 "joint_ERA5_QBOT_kg_kg_site_P"]]
    jointdetail=jointdetail.merge(jcalc,on=["site","timestamp_start"],
                                  validate="one_to_one")
    if len(jointdetail)!=27 or not jointdetail.site.eq("US-ICt").all():
        raise ValueError("27-row joint merge failed")
    if (jointdetail.site_ERA_T_abs_delta_C>8).any():
        raise ValueError("Operator's 27-row T delta<=8°C finding changed")
    summaries=pd.DataFrame(site_rows)
    if (sum(summaries.raw_RH_gt100)!=405 or
        sum(summaries.raw_RH_zero)!=39 or
        sum(summaries.joint_T_QC_review)!=27):
        raise ValueError("Audit site totals inconsistent")
    print("=== STAGE52 ORIGINAL RH >100 PHASE SEVERITY ===")
    for row in site_rows:
        print("SITE",row)
    print("=== STAGE52 27 US-ICt TA QC BREAKDOWN ===")
    print("ORIGINAL TA QC",dict(Counter(jointdetail.original_TA_QC_bin)))
    print("ERA5 VS SITE |DELTA T| MAX_C",
          round(float(jointdetail.site_ERA_T_abs_delta_C.max()),3))
    print("SCIENCE: 27 non-QC0 site T require review, but not automatic joint replacement")
    report_root=args.report_root.resolve()
    if (report_root==src50 or report_root==src51 or
        src50 in report_root.parents or src51 in report_root.parents):
        raise ValueError("Report root overlaps immutable upstream outputs")
    root=report_root/("stage52_RH_gt100_phase_and_ICt_QC_review_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    root.mkdir(parents=True,exist_ok=False)
    marker=root/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Stage52 read-only report not yet complete.\n")
    outputs={
       "four_site_original_RH_TQC_summary.csv":summaries,
       "405_original_RH_gt100_severity_review.csv":severity,
       "27_US-ICt_original_T_QC_and_joint_ERA5_comparison.csv":jointdetail,
       "444_original_RH_candidate_review_queue.csv":patch,
    }
    shas={}
    for name,frame in outputs.items():
        outfile=root/name
        frame.to_csv(outfile,index=False)
        shas[name]=sha(outfile)
    if sha(src50/CSV50)!=pins["stage50_patch_sha256"] or \
       sha(src50/"candidate_provenance.json")!=pins["stage50_provenance_sha256"] or \
       sha(src51/"review_provenance.json")!=pins["stage51_provenance_sha256"]:
        raise ValueError("Upstream data changed during Stage52 run")
    proof={"schema":"STAGE52_BATCH02_PHASE_TQC_AUDIT_v1",
           "stage50_path":str(src50),"stage51_path":str(src51),
           "pinned_inputs":pins,"output_sha256":shas,
           "row_counts":{"stage50_ERA5_RH":444,"RH_gt100_phase":405,
                        "RH_zero":39,"joint_T_QC":27},
           "science_approved_replacements":0,
           "original_source_modified":False,"forcing_modified":False}
    (root/"audit_manifest.json").write_text(
        json.dumps(proof,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE52 AUDIT PASS | 405 RH>100 phase cases / 27 US-ICt T-QC cases")
    print("REPORT",root)
    print("NO SCIENCE APPROVAL; no source/forcing/Slurm/CIME changes")
if __name__=="__main__":
    main()

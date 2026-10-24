#!/usr/bin/env python3
"""Stage51: READ-ONLY validation of 444 external CDS ERA5 RH candidates.

Produces detailed four-site summary, the 405 raw RH>100 phase cases, and a
27-row joint ERA5 T/RH/VPD/QBOT alternative using the SAME Stage50 ERA5
RH, ERA5 T2m and ERA5 surface pressure. Does not approve or modify forcing.
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

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
SOURCE=EXP/"reports/stage50_unified_external_ERA5_RH_20261024T094206Z_7d901572"
EXPECTED={"US-Ha1":398,"US-Ho2":7,"US-ICh":9,"US-ICt":30}
DECISIONS={"CANDIDATE_ONLY_REVIEW_ZERO_RH":12,
           "CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE":405,
           "MANUAL_JOINT_T_AND_HUMIDITY_REVIEW":27}
DATASET="reanalysis-era5-single-levels-timeseries"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def es(t):
    x=np.asarray(t,float)
    return 6.112*np.exp(17.67*x/(x+243.5))

def joint_era(t,rh,p):
    t,rh,p=map(lambda x:np.asarray(x,float),(t,rh,p))
    vap=es(t)*(rh/100) # hPa, water basis
    vpd=es(t)-vap
    denom=p-0.378*(100*vap)
    q=0.622*(100*vap)/denom
    valid=(np.isfinite(t)&np.isfinite(rh)&np.isfinite(p)&
           (t>-90)&(t<65)&(rh>0)&(rh<=100.05)&
           (p>49000)&(p<111000)&(denom>0)&
           np.isfinite(vpd)&(vpd>=-0.005)&np.isfinite(q)&(q>0)&(q<0.08))
    return vpd,q,valid

def self_test():
    v,q,ok=joint_era([20],[50],[100000])
    assert ok.tolist()==[True] and abs(v[0]-11.6847)<0.02
    assert 0.007<q[0]<0.008
    _,_,bad=joint_era([10],[101],[100000])
    assert bad.tolist()==[False]
    assert sum(EXPECTED.values())==444
    print("STAGE51 SELF-TEST PASS | joint water-RH psychrometrics and exact 444 scope")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--audit",action="store_true")
    ap.add_argument("--stage50",type=Path,default=SOURCE)
    ap.add_argument("--output-root",type=Path,default=EXP/"reports")
    o=ap.parse_args()
    if o.self_test:return self_test()
    src=o.stage50.resolve(strict=True)
    if (src/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage50 marked incomplete")
    csv_file=src/"RH_zero_gt100_444_ERA5_candidate_patch.csv"
    meta_file=src/"candidate_provenance.json"
    proof=json.loads(meta_file.read_text())
    if (proof.get("schema")!="STAGE50_444_EXTERNAL_CDS_ERA5_REVIEW_v1" or
        proof.get("dataset")!=DATASET or proof.get("target_count")!=444 or
        proof.get("approved_replacements")!=0 or
        proof.get("model_ready") is not False or
        proof.get("patch_sha256")!=sha(csv_file)):
        raise ValueError("Stage50 original output or science gate has changed")
    cols={"site","timestamp_start","original_RH_pct","candidate_RH_pct",
          "original_TA_C","original_TA_QC","original_PA_kPa",
          "ERA5_T2M_C","ERA5_TD2M_C","ERA5_surface_pressure_Pa",
          "retained_T_minus_ERA5_T_C","candidate_status","source_sha256",
          "ERA5_receipt_file","ERA5_netcdf_sha256","ERA5_dataset"}
    tab=pd.read_csv(csv_file,dtype={"site":str,"timestamp_start":str,
        "ERA5_netcdf_sha256":str,"ERA5_receipt_file":str})
    if not cols.issubset(tab.columns):
        raise ValueError("Stage50 patch missing columns "+str(cols-set(tab.columns)))
    counts=Counter(tab.site)
    decisions=Counter(tab.candidate_status)
    raw=pd.to_numeric(tab.original_RH_pct,errors="coerce")
    rh=pd.to_numeric(tab.candidate_RH_pct,errors="coerce")
    if (len(tab)!=444 or dict(counts)!=EXPECTED or dict(decisions)!=DECISIONS or
        (int((raw==0).sum()),int((raw>100).sum()))!=(39,405) or
        tab.duplicated(["site","timestamp_start"]).any() or
        not tab.ERA5_dataset.eq(DATASET).all() or
        not rh.notna().all() or not rh.between(0.0000001,100.05).all()):
        raise ValueError("Stage50 science scope, origin or ERA5 RH invalid")
    if proof.get("statuses")!=dict(decisions):
        raise ValueError("Stage50 manifest science counts differ")
    receipt_hashes={}
    for site,sub in tab.groupby("site"):
        if not sub.source_sha256.eq(proof["source_sha256"][site]).all():
            raise ValueError("Stage50 tower-source SHA256 mismatch "+site)
    for _,row in tab[["ERA5_receipt_file","ERA5_netcdf_sha256"]].drop_duplicates().iterrows():
        receipt=Path(row.ERA5_receipt_file).resolve(strict=True)
        data=json.loads(receipt.read_text())
        netcdf=Path(data["netcdf_path"]).resolve(strict=True)
        original=Path(data["original_payload_path"]).resolve(strict=True)
        if (data.get("dataset",data.get("CDS_dataset"))!=DATASET or
            data.get("science_approval",data.get("science_approved")) is not False or
            sha(netcdf)!=row.ERA5_netcdf_sha256 or
            sha(netcdf)!=data["netcdf_sha256"] or
            sha(original)!=data["original_payload_sha256"]):
            raise ValueError("CDS ERA5 receipt/netcdf/original payload changed "+str(receipt))
        receipt_hashes[str(receipt)]=sha(receipt)
    joint=tab[tab.candidate_status=="MANUAL_JOINT_T_AND_HUMIDITY_REVIEW"].copy()
    phase=tab[tab.candidate_status=="CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE"].copy()
    if not joint.original_RH_pct.eq(0).all() or not phase.original_RH_pct.gt(100).all():
        raise ValueError("Stage50 27/405 event categories changed")
    qc=pd.to_numeric(joint.original_TA_QC,errors="coerce")
    delta=pd.to_numeric(joint.retained_T_minus_ERA5_T_C,errors="coerce")
    joint["science_trigger"]=[
        "|".join(x) if x else "RETAINED_T_OR_SITE_P_OTHER_GATE"
        for x in (
            (["ORIGINAL_T_QC_NOT_ZERO_OR_MISSING"] if not np.isfinite(q) or q!=0 else [])+
            (["T_SITE_VS_ERA5_DIFFERENCE_OVER_8C_OR_MISSING"]
             if not np.isfinite(d) or abs(d)>8 else [])
            for q,d in zip(qc,delta)
        )
    ]
    era_t=pd.to_numeric(joint.ERA5_T2M_C,errors="coerce").to_numpy()
    era_rh=pd.to_numeric(joint.candidate_RH_pct,errors="coerce").to_numpy()
    era_p=pd.to_numeric(joint.ERA5_surface_pressure_Pa,errors="coerce").to_numpy()
    vpd,q,valid=joint_era(era_t,era_rh,era_p)
    if not valid.all():
        raise ValueError("Some fully-ERA5 joint candidates fail numerical physics")
    joint["joint_ERA5_T_C"]=era_t
    joint["joint_ERA5_RH_pct"]=era_rh
    joint["joint_ERA5_VPD_hPa"]=vpd
    joint["joint_ERA5_QBOT_kg_kg_grid_P"]=q
    tower_p=pd.to_numeric(joint.original_PA_kPa,errors="coerce").to_numpy()*1000
    _,tower_q,tower_ok=joint_era(era_t,era_rh,tower_p)
    joint["joint_ERA5_QBOT_kg_kg_site_P"]=np.where(tower_ok,tower_q,np.nan)
    joint["joint_ERA5_P_source"]="CDS_ERA5_grid_surface_pressure"
    joint["scientific_approval"]=False
    phase["scientific_approval"]=False
    four=[]
    for site in EXPECTED:
        sub=tab[tab.site==site]
        focus=joint[joint.site==site]
        four.append(dict(site=site,n_original_RH_zero=int(sub.original_RH_pct.eq(0).sum()),
            n_original_RH_gt100=int(sub.original_RH_pct.gt(100).sum()),
            n_zero_RH_with_original_T_kept=int(sub.candidate_status.eq(
                "CANDIDATE_ONLY_REVIEW_ZERO_RH").sum()),
            n_joint_T_RH_review=len(focus),
            n_gt100_phase_review=int(sub.candidate_status.eq(
                "CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE").sum()),
            n_joint_original_T_QC_nonzero=int((
                pd.to_numeric(focus.original_TA_QC,errors="coerce")!=0).sum()),
            n_joint_site_vs_ERA_T_delta_gt8C=int((
                pd.to_numeric(focus.retained_T_minus_ERA5_T_C,
                              errors="coerce").abs()>8).sum())))
    outroot=o.output_root.resolve()
    if outroot==src or src in outroot.parents:
        raise ValueError("Unsafe output path overlaps Stage50")
    dest=outroot/("stage51_444_RH_and_27_joint_T_review_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("This is audit output, not forcing approval.\n")
    reports={
      "27_joint_ERA5_T_RH_QBOT_review.csv":joint,
      "405_raw_RH_gt100_phase_review.csv":phase,
      "444_four_site_review_breakdown.csv":pd.DataFrame(four),
    }
    hashes={}
    for name,frame in reports.items():
        file=dest/name
        frame.to_csv(file,index=False)
        hashes[name]=sha(file)
    if sha(csv_file)!=proof["patch_sha256"]:
        raise ValueError("Stage50 changed during audit")
    (dest/"review_provenance.json").write_text(json.dumps({
        "source_stage50":str(src),"stage50_patch_sha256":sha(csv_file),
        "stage50_provenance_sha256":sha(meta_file),
        "ERA5_CDS_receipt_sha256":receipt_hashes,
        "output_sha256":hashes,"count":444,"joint_T_RH":27,
        "supersat_phase":405,"original_zero_T_retained":12,
        "approved_for_DATM":False,"model_input_modified":False},indent=2,
        sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE51 AUDIT PASS | exact 444 source-pinned ERA5 RH candidates")
    print("27 joint ERA5 T/RH/QBOT numeric alternatives; 405 phase reviews; 12 zero-RH original-T candidates")
    for row in four:print("SITE",row)
    print("REPORT",dest)
    print("ALL SCIENTIFIC APPROVALS REMAIN FALSE. NO RAW OR FORCING CHANGES.")
if __name__=="__main__":
    main()

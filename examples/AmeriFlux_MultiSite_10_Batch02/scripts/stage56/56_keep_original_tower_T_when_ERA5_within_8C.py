#!/usr/bin/env python3
"""Stage56 — apply user T policy to the 4,884 distinct Stage11 humidity HOLD rows.

Keep ORIGINAL FLUXNET TA_F (including QC1/QC2) if it is physically valid and
abs(TA_F - same-source independent CDS ERA5 T2m) <= 8.0 deg C.
QC status is retained, NOT used alone as a reason to change plausible T.
Recalculate proposed VPD/QBOT from existing Stage19 independent ERA5 water RH,
ORIGINAL TA_F and ORIGINAL PA_F. Never replace T with ERA5 automatically.
US-Ho1 ERA5 alignment remains provisional: DO NOT release T comparison there.
All original humidity/ice phase QC HOLD flags remain for final forcing review.

Read-only with respect to original Stage07/08/11/19/53/54/55, DATM, NetCDF,
CIME, Slurm and model. --audit writes only a new SHA-pinned isolated report.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
HOME_REPO=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
STAGE55_SCRIPT=HOME_REPO/"scripts/stage55/55_triage_existing_stage19_4884_ERA5_science_HOLD.py"
STAGE55_GIT_BLOB="fed667b3f26bd36e4be01252a30a353c9d12d049"
STAGE55=BASE/"reports/stage55_4884_existing_ERA5_science_triage_20261024T102824Z_8a2c5021"
STAGE19=Path.home()/"AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
STAGE11=BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
STAGE54=BASE/"reports/stage54_444_vs_4884_timestamp_crosswalk_20261024T101940Z_bac3a939"
S55CSV="4884_existing_ERA5_candidates_science_routes.csv"
S19CSV="all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv"
THRESHOLD_C=8.0
COUNTS={"US-EML":1327,"US-GLE":295,"US-Ho1":917,"US-ICh":169,"US-ICt":2176}
ERA_DATASET="reanalysis-era5-single-levels-timeseries"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1048576),b""):
            h.update(part)
    return h.hexdigest()

def git_blob_sha(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def water_vpd_qbot(t,rh,p):
    """Water saturation basis as Stage19/Stage53; T Celsius, RH %, P kPa."""
    t=np.asarray(t,dtype=float)
    rh=np.asarray(rh,dtype=float)
    p=np.asarray(p,dtype=float)*1000
    sat=6.112*np.exp(17.67*t/(t+243.5))
    vapor=sat*rh/100
    return sat-vapor,.622*100*vapor/(p-.378*100*vapor)

def temp_choice(site,ta,era,qc):
    if not np.isfinite(ta) or not (-80 < ta < 65):
        return "HOLD_ORIGINAL_TA_NUMERIC_INVALID"
    if not np.isfinite(era) or not (-90 < era < 65):
        return "HOLD_ERA5_TEMPERATURE_INVALID"
    if site=="US-Ho1":
        return "HOLD_HO1_LOCAL_UTC_OFFSET_PROVISIONAL"
    if abs(ta-era)>THRESHOLD_C:
        return "HOLD_TA_DIFF_FROM_ERA5_GT8C"
    return "KEEP_ORIGINAL_TA_F_WITHIN8C"

def self_test():
    assert temp_choice("US-ICt",-12,-10,2)=="KEEP_ORIGINAL_TA_F_WITHIN8C"
    assert temp_choice("US-EML",5,-3,1)=="KEEP_ORIGINAL_TA_F_WITHIN8C"
    assert temp_choice("US-EML",5,-3.001,1)=="HOLD_TA_DIFF_FROM_ERA5_GT8C"
    assert temp_choice("US-Ho1",0,0,0)=="HOLD_HO1_LOCAL_UTC_OFFSET_PROVISIONAL"
    assert temp_choice("US-GLE",-9999,-10,2)=="HOLD_ORIGINAL_TA_NUMERIC_INVALID"
    assert temp_choice("US-EML",5,5,float("nan"))=="KEEP_ORIGINAL_TA_F_WITHIN8C"
    v,q=water_vpd_qbot([20],[50],[100])
    assert abs(v[0]-11.6847)<.02 and .007<q[0]<.008
    assert sum(COUNTS.values())==4884
    print("STAGE56 SELF-TEST PASS | <=8C keeps original TA_F regardless of QC code; Ho1 protected")

def load_existing():
    if git_blob_sha(STAGE55_SCRIPT)!=STAGE55_GIT_BLOB:
        raise ValueError("Stage55 on-cluster code changed; exact Git blob mismatch")
    spec=importlib.util.spec_from_file_location("pinned_batch02_stage55",str(STAGE55_SCRIPT))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for path in (STAGE11,STAGE19,STAGE54,STAGE55):
        if not path.is_dir():
            raise FileNotFoundError(str(path))
        if (path/"INCOMPLETE_DO_NOT_USE").exists():
            raise ValueError("Upstream incomplete marker: "+str(path))
    m55=json.loads((STAGE55/"science_triage_manifest.json").read_text())
    if (m55.get("schema")!="STAGE55_4884_STAGE19_REVIEW_ONLY_v1" or
        m55.get("n_stage11")!=4884 or m55.get("n_stage53_separate")!=444 or
        m55.get("overlap")!=0 or
        m55.get("stage11")!=str(STAGE11) or
        m55.get("stage19")!=str(STAGE19) or
        m55.get("stage54")!=str(STAGE54) or
        m55.get("automatic_replacement_approvals")!=0 or
        m55.get("forcing_modified") is not False):
        raise ValueError("Stage55 scientific provenance/status differs")
    for name,digest in m55.get("output_sha256",{}).items():
        if sha(STAGE55/name)!=digest:
            raise ValueError("Stage55 output changed: "+name)
    row55=pd.read_csv(STAGE55/S55CSV,dtype={"site":str,"site_local_key":str})
    d,manifest19,pins55=mod.load(STAGE19,STAGE11,STAGE54,True)
    if (len(row55)!=4884 or len(d)!=4884 or
        Counter(d.site)!=Counter(COUNTS) or
        Counter(row55.site)!=Counter(COUNTS) or
        not {"site_local_key","science_route"}.issubset(row55.columns)):
        raise ValueError("Stage19/55 target scope changed")
    stage55_keys=set(zip(row55.site,row55.site_local_key))
    stage19_keys=set(zip(d.site,d.site_local_key))
    if stage55_keys!=stage19_keys:
        raise ValueError("Stage55 and source Stage19 local times differ")
    pin=m55.get("input_sha256",{})
    for k in ("stage11_targets_sha256","stage11_manifest_sha256",
              "stage19_report_sha256","stage19_manifest_sha256",
              "stage54_manifest_sha256"):
        if pin.get(k)!=pins55[k]:
            raise ValueError("Stage55 pinned input changed: "+k)
    if (manifest19.get("n_numeric_invalid")!=0 or
        manifest19.get("scientifically_approved_rows")!=0):
        raise ValueError("Stage19 numeric or approval status unexpectedly changed")
    return d,{"stage55_manifest_sha256":sha(STAGE55/"science_triage_manifest.json"),
       "stage55_rows_sha256":sha(STAGE55/S55CSV),
       "stage19_rows_sha256":sha(STAGE19/S19CSV),
       "stage19_manifest_sha256":sha(STAGE19/"manifest.json"),
       "stage11_rows_sha256":sha(STAGE11/"cold_humidity_repair_proposals.csv"),
       "stage54_manifest_sha256":sha(STAGE54/"crosswalk_manifest.json"),
       "stage55_git_blob":STAGE55_GIT_BLOB}

def classify(data):
    x=data.copy()
    ta=pd.to_numeric(x.TA_F,errors="coerce").to_numpy(dtype=float)
    era=pd.to_numeric(x.ERA5_T2M_C,errors="coerce").to_numpy(dtype=float)
    qc=pd.to_numeric(x.TA_F_QC,errors="coerce").to_numpy(dtype=float)
    pressure=pd.to_numeric(x.PA_F,errors="coerce").to_numpy(dtype=float)
    rh=pd.to_numeric(x.ERA5_RH_water_pct,errors="coerce").to_numpy(dtype=float)
    x["TA_F_minus_ERA5_T2M_C"]=ta-era
    x["TA_F_abs_ERA5_delta_C"]=np.abs(ta-era)
    x["original_TA_F_QC_numeric"]=qc
    x["original_TA_QC_missing_or_nonstandard"]=~np.isin(qc,[0,1,2,3])
    x["original_TA_valid"]=np.isfinite(ta)&(ta>-80)&(ta<65)
    x["original_PA_valid"]=np.isfinite(pressure)&(pressure>50)&(pressure<110)
    x["temp_decision"]=[temp_choice(site,a,b,c) for site,a,b,c in
                         zip(x.site,ta,era,qc)]
    x["original_TA_retained"]=x.temp_decision.eq("KEEP_ORIGINAL_TA_F_WITHIN8C")
    x["T_QC_nonzero_but_retained"]=x.original_TA_retained&(qc!=0)
    x["original_TA_differs_from_Stage11_retained"]=~np.isclose(
        ta,pd.to_numeric(x.retained_TA_C,errors="coerce").to_numpy(dtype=float),
        rtol=0,atol=1e-8,equal_nan=True)
    x["ERA5_RH_source"]=ERA_DATASET
    x["ERA5_RH_water_pct_selected"]=rh
    if not (np.isfinite(rh).all() and (rh>0).all() and (rh<=100.05).all()):
        raise ValueError("Existing external CDS ERA5 RH invalid")
    with np.errstate(all="ignore"):
        vpd,q=water_vpd_qbot(ta,rh,pressure)
    complete=(x.original_TA_retained.to_numpy()&
              x.original_PA_valid.to_numpy()&
              np.isfinite(vpd)&(vpd>=-0.005)&np.isfinite(q)&
              (q>0)&(q<0.08))
    x["RH_VPD_QBOT_numeric_candidate"]=complete
    x["proposed_VPD_hPa_using_original_TA_F"]=np.where(complete,vpd,np.nan)
    x["proposed_QBOT_kgkg_using_original_TA_F_PA_F"]=np.where(complete,q,np.nan)
    x["phase_water_ice_review_required"]=x.cold_water_saturation_caution.astype(
        str).str.lower().eq("true")
    x["source_stage11_HOLD_preserved"]=x.original_Stage11_HOLD_preserved
    x["science_HOLD_forcing"]=True
    x["approved_for_DATM"]=False
    x["approved_for_spinup"]=False
    x["temperature_policy"]="PRESERVE_ORIGINAL_FLUXNET_TA_F_IF_ERA5_ABS_DELTA_LE8C"
    return x

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--audit",action="store_true")
    p.add_argument("--output-root",type=Path,default=BASE/"reports")
    args=p.parse_args()
    if args.self_test:return self_test()
    d,pins=load_existing()
    out=classify(d)
    if len(out)!=4884 or Counter(out.site)!=Counter(COUNTS):
        raise ValueError("Stage56 target identity or count mismatch")
    summary=[]
    for site in COUNTS:
        z=out.loc[out.site.eq(site)]
        summary.append(dict(site=site,total=len(z),
          original_TA_keep_under8C=int(z.original_TA_retained.sum()),
          original_TA_QC_nonzero_kept=int(z.T_QC_nonzero_but_retained.sum()),
          original_TA_gt8C_HOLD=int(z.temp_decision.eq(
              "HOLD_TA_DIFF_FROM_ERA5_GT8C").sum()),
          original_TA_or_ERA5_invalid_HOLD=int(z.temp_decision.isin([
              "HOLD_ORIGINAL_TA_NUMERIC_INVALID",
              "HOLD_ERA5_TEMPERATURE_INVALID"]).sum()),
          retained_TA_with_missing_or_nonstandard_QC=int((
              z.original_TA_retained & z.original_TA_QC_missing_or_nonstandard).sum()),
          HO1_offset_HOLD=int(z.temp_decision.eq(
              "HOLD_HO1_LOCAL_UTC_OFFSET_PROVISIONAL").sum()),
          original_pressure_invalid=int((~z.original_PA_valid).sum()),
          complete_RH_VPD_QBOT_numeric_candidate=int(
              z.RH_VPD_QBOT_numeric_candidate.sum()),
          original_TA_differs_from_Stage11_retained=int(
              z.original_TA_differs_from_Stage11_retained.sum()),
          water_ice_phase_caution=int(z.phase_water_ice_review_required.sum())))
    scounts=dict(Counter(out.temp_decision))
    assert sum(scounts.values())==4884
    print("STAGE56 SOURCE CHECK PASS | Stage11/19/54/55 4884 rows SHA-verified")
    print("RULE keep ORIGINAL TA_F if abs(original TA_F - CDS ERA5 T2m)<=8.0 C")
    print("TEMPERATURE_DECISIONS",scounts)
    print("RH+VPD+QBOT NUMERIC CANDIDATES",int(out.RH_VPD_QBOT_numeric_candidate.sum()))
    for z in summary: print("SITE",z)
    print("ALL 4884: model forcing HOLD retained (phase/UTC/other source QC)")
    if args.check:
        print("STAGE56 CHECK PASS | zero writes");return
    root=args.output_root.resolve()
    protected=(STAGE11,STAGE19,STAGE54,STAGE55)
    if root in protected or any(y in root.parents for y in protected):
        raise ValueError("Output location overlaps protected source report")
    dest=root/("stage56_original_T_if_ERA5_delta_le8C_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Stage56 conservative science candidate; not forcing ready.\n")
    payloads={
       "4884_keep_original_TA_under8C_with_ERA5_RH_VPD_QBOT.csv":out,
       "five_site_temperature_retain_gate_summary.csv":pd.DataFrame(summary),
       "temperature_decision_counts.csv":pd.DataFrame([
           {"temperature_decision":k,"n":v} for k,v in sorted(scounts.items())])}
    hashes={}
    for name,frame in payloads.items():
        f=dest/name
        frame.to_csv(f,index=False)
        hashes[name]=sha(f)
    if (sha(STAGE55/S55CSV)!=pins["stage55_rows_sha256"] or
        sha(STAGE19/S19CSV)!=pins["stage19_rows_sha256"] or
        sha(STAGE11/"cold_humidity_repair_proposals.csv")!=pins["stage11_rows_sha256"]):
        raise ValueError("Source data changed mid-audit")
    manifest=dict(schema="STAGE56_ORIGINAL_TA_UNDER8C_CDS_ERA5_POLICY_v1",
          temperature_abs_difference_threshold_C=THRESHOLD_C,
          source_CDS_ERA5_product=ERA_DATASET,
          original_TA_F_replacement_by_ERA5_count=0,
          all_science_forcing_HOLD=True, approved_for_DATM=False,
          source_STAGE55=str(STAGE55),source_STAGE19=str(STAGE19),
          source_sha256=pins,output_sha256=hashes,
          temperature_decision_counts=scounts,
          n_records=4884,no_original_or_forcing_changes=True)
    (dest/"policy_manifest.json").write_text(json.dumps(
         manifest,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE56 AUDIT PASS | original TA_F retained when valid and ERA5 delta<=8C")
    print("REPORT",dest)
    print("NO RAW, CANDIDATE, DATM, CIME, SPINUP OR SLURM CHANGES")
if __name__=="__main__":
    main()

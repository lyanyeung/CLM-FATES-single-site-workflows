#!/usr/bin/env python3
"""Batch02 Stage60: integrate 3967+444 distinct humidity corrections, no model writes.

Scientific policy explicitly delegated by user: retain accepted ORIGINAL EC air
T and station pressure, replace bad original humidity with independent CDS ERA5
water-reference RH, and compute a consistent vapour pressure, VPD and QBOT.
Subzero RH with respect to ice >100% is NOT a reason to clip water RH/QBOT.
Crosswalk original site/local timestamps; preserve 917 US-Ho1 UTC-offset HOLD.
Do not apply any corrections to original files, CLM DATM, CIME or spin-up.
Isolated output is input to subsequent complete-source and forcing QA gates.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import hashlib
import json
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S53=ROOT/"reports/stage53_444_ERA5_RH_only_staging_20261024T100652Z_543ef3f1"
S54=ROOT/"reports/stage54_444_vs_4884_timestamp_crosswalk_20261024T101940Z_bac3a939"
S58=ROOT/"reports/stage58_63_manual_T_approved_3967_T_total_20261024T110141Z_e65bde6c"
S59=ROOT/"reports/stage59_water_ice_review_3967_20261024T110624Z_2dc93fb4"
F53="444_original_RH_zero_or_gt100_unified_ERA5_RH_VPD_QBOT.csv"
F59="3967_water_vs_ice_humidity_sensitivity.csv"
F58="4884_final_original_tower_temperature_policy.csv"
PRODUCT="reanalysis-era5-single-levels-timeseries"
C53={"US-Ha1":398,"US-Ho2":7,"US-ICh":9,"US-ICt":30}
C59={"US-EML":1327,"US-GLE":295,"US-ICh":169,"US-ICt":2176}
ALL={"US-EML":1327,"US-GLE":295,"US-Ha1":398,"US-Ho2":7,
     "US-ICh":178,"US-ICt":2206}
ROUTES={"SUBZERO_NO_ICE_SUPERSAT_NUMERIC_FLAG":2257,
        "REVIEW_ICE_RH_100_TO105_PCT":687,
        "REVIEW_ICE_RH_OVER105_PCT":1013,
        "ABOVE_ZERO_WATER_REFERENCE":10}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as stream:
        for part in iter(lambda:stream.read(1048576),b""):
            h.update(part)
    return h.hexdigest()

def require_sha_entries(folder,dict_):
    if not dict_ or not isinstance(dict_,dict):
        raise ValueError("Missing immutable upstream digest manifest: "+str(folder))
    for name,digest in dict_.items():
        if sha(folder/name)!=digest:
            raise ValueError("Upstream digest differs: "+str(folder/name))

def source_data():
    for folder in (S53,S54,S58,S59):
        if not folder.is_dir() or (folder/"INCOMPLETE_DO_NOT_USE").exists():
            raise ValueError("Missing/incomplete prior stage: "+str(folder))
    m53=json.loads((S53/"ledger_provenance.json").read_text())
    m54=json.loads((S54/"crosswalk_manifest.json").read_text())
    m58=json.loads((S58/"manual_temperature_decision_manifest.json").read_text())
    m59=json.loads((S59/"phase_science_manifest.json").read_text())
    if (m53.get("schema")!="STAGE53_USER_SELECTED_RH_ONLY_LEDGER_v1" or
        m53.get("row_count")!=444 or
        m53.get("original_RH_zero")!=39 or
        m53.get("original_RH_gt100")!=405 or
        m53.get("ERA5_dataset")!=PRODUCT or
        m53.get("approved_for_DATM") is not False or
        m53.get("output_sha256")!=sha(S53/F53)):
        raise ValueError("Stage53 origin/approval/ERA5 identity altered")
    if (m54.get("schema")!="STAGE54_BATCH02_EXACT_SITE_LOCAL_TIME_CROSSWALK_v1" or
        m54.get("source_stage53")!=str(S53) or
        m54.get("intersection_count")!=0 or
        m54.get("stage53_only_count")!=444 or
        m54.get("stage11_only_count")!=4884 or
        m54.get("input_sha256",{}).get("stage53_patch_sha256")!=sha(S53/F53) or
        m54.get("input_sha256",{}).get("stage53_manifest_sha256")!=sha(S53/"ledger_provenance.json")):
        raise ValueError("Stage54 exact-overlap crosswalk invalid")
    require_sha_entries(S54,m54["output_sha256"])
    if (m58.get("schema")!="STAGE58_USER_MANUAL_EXTREME_COLD_TA_APPROVAL_ONLY_v1" or
        m58.get("n_total_original_T_retained")!=3967 or
        m58.get("n_Ho1_provisional_offset_hold")!=917 or
        m58.get("humidity_and_phase_science_HOLD") is not True or
        m58.get("approved_for_DATM") is not False or
        m58.get("report_sha256",{}).get(F58)!=sha(S58/F58)):
        raise ValueError("Stage58 T approvals/Ho1 science gate invalid")
    require_sha_entries(S58,m58["report_sha256"])
    if (m59.get("schema")!="STAGE59_3967_WATER_ICE_DIAGNOSTIC_v1" or
        m59.get("n_original_temperature_retained")!=3967 or
        m59.get("n_Ho1_time_offset_HOLD")!=917 or
        m59.get("all_humidity_science_HOLD") is not True or
        m59.get("water_vpd_qbot_unchanged") is not True or
        m59.get("stage58_report_sha256")!=sha(S58/F58) or
        m59.get("stage58_manifest_sha256")!=sha(S58/"manual_temperature_decision_manifest.json") or
        m59.get("report_sha256",{}).get(F59)!=sha(S59/F59)):
        raise ValueError("Stage59 water/ice source/sensitivity invalid")
    require_sha_entries(S59,m59["report_sha256"])
    a=pd.read_csv(S53/F53,dtype={"site":str,"timestamp_start":str})
    b=pd.read_csv(S59/F59,dtype={"site":str,"local_key":str})
    original=pd.read_csv(S58/F58,dtype={"site":str,"local_key":str})
    if (len(a)!=444 or len(b)!=3967 or len(original)!=4884 or
        Counter(a.site)!=Counter(C53) or Counter(b.site)!=Counter(C59) or
        original.final_temperature_decision.eq(
            "HOLD_HO1_LOCAL_UTC_OFFSET_PROVISIONAL").sum()!=917):
        raise ValueError("Source row totals differ; preserve Ho1 HOLD")
    expected_a={"site","timestamp_start","original_TA_C","original_PA_kPa",
                "replacement_RH_pct","replacement_VPD_hPa",
                "replacement_QBOT_kg_kg","ERA5_dataset"}
    expected_b={"site","local_key","TA_F","PA_F","ERA5_RH_water_pct_selected",
                "VPD_water_hPa_original_TA","QBOT_kgkg_original_TA_PA",
                "humidity_review_route","RH_over_ice_pct_diagnostic"}
    if not expected_a.issubset(a.columns) or not expected_b.issubset(b.columns):
        raise ValueError("Previous-stage schema fields changed")
    if not a.ERA5_dataset.eq(PRODUCT).all():
        raise ValueError("Stage53 candidates from unexpected CDS product")
    if Counter(b.humidity_review_route)!=Counter(ROUTES):
        raise ValueError("Stage59 3967 phase numerical census changed")
    at=pd.to_datetime(a.timestamp_start,format="%Y%m%d%H%M",errors="raise")
    bt=pd.to_datetime(b.local_key,errors="raise")
    if at.isna().any() or bt.isna().any() or at.dt.tz is not None or bt.dt.tz is not None:
        raise ValueError("Tower local-time conversion failed")
    a["local_timestamp_start"]=at.dt.strftime("%Y%m%d%H%M")
    b["local_timestamp_start"]=bt.dt.strftime("%Y%m%d%H%M")
    if (a.duplicated(["site","local_timestamp_start"]).any() or
        b.duplicated(["site","local_timestamp_start"]).any()):
        raise ValueError("Duplicate native tower timestamps")
    pa=set(zip(a.site,a.local_timestamp_start))
    pb=set(zip(b.site,b.local_timestamp_start))
    if pa & pb:
        raise ValueError("Overlap in proposed 444 + 3967 humidity corrections")
    return a,b,original,{
        "stage53_patch_sha256":sha(S53/F53),
        "stage53_manifest_sha256":sha(S53/"ledger_provenance.json"),
        "stage54_manifest_sha256":sha(S54/"crosswalk_manifest.json"),
        "stage58_full_sha256":sha(S58/F58),
        "stage58_manifest_sha256":sha(S58/"manual_temperature_decision_manifest.json"),
        "stage59_phase_sha256":sha(S59/F59),
        "stage59_manifest_sha256":sha(S59/"phase_science_manifest.json")}

def water_pair(t,rh,p):
    es=6.112*np.exp(17.67*t/(t+243.5))
    e=es*rh/100
    return es,e,es-e,.622*100*e/(p*1000-.378*100*e)

def unify(a,b):
    def build(source,rows,key,tcol,pcol,rcol,vcol,qcol):
        z=source.copy()
        out=pd.DataFrame({
          "site":z.site.astype(str),
          "tower_local_start":z.local_timestamp_start.astype(str),
          "candidate_cohort":rows,
          "original_TA_C_kept":pd.to_numeric(z[tcol],errors="raise"),
          "original_PA_kPa_kept":pd.to_numeric(z[pcol],errors="raise"),
          "replacement_RH_water_pct":pd.to_numeric(z[rcol],errors="raise"),
          "replacement_VPD_water_hPa":pd.to_numeric(z[vcol],errors="raise"),
          "replacement_QBOT_kgkg":pd.to_numeric(z[qcol],errors="raise")})
        if rows=="STAGE59_ACCEPTED_3967":
            out["ice_RH_pct_diagnostic"]=pd.to_numeric(
                 z["RH_over_ice_pct_diagnostic"],errors="coerce")
            out["ice_phase_review_route"]=z.humidity_review_route
        else:
            out["ice_RH_pct_diagnostic"]=np.nan
            out["ice_phase_review_route"]="STAGE53_RAW_RH_ZERO_GT100_REPLACEMENT"
        out["source_original_tower_T"]=True
        out["source_original_tower_PA"]=True
        out["selected_independent_CDS_dataset"]=PRODUCT
        out["candidate_selected_by_user_physical_rule"]=True
        out["approved_for_DATM"]=False
        out["approved_for_spinup"]=False
        return out
    x=build(a,"STAGE53_RH_REPAIR_444","timestamp_start",
            "original_TA_C","original_PA_kPa",
            "replacement_RH_pct","replacement_VPD_hPa",
            "replacement_QBOT_kg_kg")
    y=build(b,"STAGE59_ACCEPTED_3967","local_key","TA_F","PA_F",
            "ERA5_RH_water_pct_selected","VPD_water_hPa_original_TA",
            "QBOT_kgkg_original_TA_PA")
    out=pd.concat([x,y],ignore_index=True)
    out.sort_values(["site","tower_local_start"],inplace=True,ignore_index=True)
    if (len(out)!=4411 or Counter(out.site)!=Counter(ALL) or
        out.duplicated(["site","tower_local_start"]).any()):
        raise ValueError("Final 4411 unique site-local-time audit failed")
    t=out.original_TA_C_kept.to_numpy(dtype=float)
    p=out.original_PA_kPa_kept.to_numpy(dtype=float)
    r=out.replacement_RH_water_pct.to_numpy(dtype=float)
    es,e,v,q=water_pair(t,r,p)
    if (not np.isfinite(t).all() or not np.isfinite(p).all() or
        not np.isfinite(r).all() or (t<=-80).any() or (t>=65).any() or
        (p<=50).any() or (p>=110).any() or
        (r<=0).any() or (r>100.05).any() or
        not np.allclose(v,out.replacement_VPD_water_hPa,rtol=1e-7,atol=1e-8) or
        not np.allclose(q,out.replacement_QBOT_kgkg,rtol=1e-7,atol=1e-9)):
        raise ValueError("Mixed water-basis humidity/pressure/QBOT physics mismatch")
    out["water_saturation_vapour_pressure_hPa"]=es
    out["actual_vapour_pressure_hPa"]=e
    out["water_RH_gt100_numerical_caution"]=r>100
    out["water_VPD_negative_numerical_caution"]=v<0
    out["QBOT_mass_mixing_ratio_positive"]=q>0
    out["needs_climatological_source_and_DATM_full_QA"]=True
    return out

def self_test():
    _,e,v,q=water_pair(np.array([20.]),np.array([50.]),np.array([100.]))
    assert 11.67<v[0]<11.70 and .007<q[0]<.008 and e[0]>0
    assert sum(C53.values())==444 and sum(C59.values())==3967
    assert sum(ALL.values())==4411 and sum(ROUTES.values())==3967
    print("STAGE60 SELF-TEST PASS | 444+3967=4411 unique water-reference humidity patch policy")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--stage",action="store_true")
    args=ap.parse_args()
    if args.self_test:return self_test()
    a,b,original,pins=source_data()
    unified=unify(a,b)
    c=Counter(unified.candidate_cohort)
    print("STAGE60 SOURCE CHECK PASS | Stage53 444 + Stage59 3967 =4411 no overlap")
    print("SITE_COUNTS",dict(Counter(unified.site)))
    print("COHORT_COUNTS",dict(c))
    print("WATER_RH_GT100_CAUTION",int(unified.water_RH_gt100_numerical_caution.sum()))
    print("WATER_VPD_NEGATIVE_CAUTION",int(unified.water_VPD_negative_numerical_caution.sum()))
    print("ICE_RH_GT100_PHASE_CAUTION_STAGE59",int((b.RH_over_ice_pct_diagnostic>100).sum()))
    print("US-Ho1 917 UTC_OFFSET HOLD: not represented in these 4411 patch candidates")
    print("STAGE60 scientific policy selected; NOT YET MODEL-FORCING APPROVED")
    if args.check:
        print("STAGE60 CHECK PASS | no output writes");return
    dest=ROOT/"reports"/("stage60_4411_ERA5_water_RH_VPD_QBOT_unified_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Science policy selected; still requires full source coverage/model forcing QA.\n")
    patch=dest/"4411_unique_original_tower_time_ERA5_water_humidity_patch.csv"
    unified.to_csv(patch,index=False)
    recs=dest/"source_census_4411_by_site.csv"
    pd.DataFrame([{"site":s,"n":int((unified.site==s).sum())}
                  for s in ALL]).to_csv(recs,index=False)
    stats={"water_RH_gt100_n":int(unified.water_RH_gt100_numerical_caution.sum()),
           "water_VPD_negative_n":int(unified.water_VPD_negative_numerical_caution.sum()),
           "ice_RH_gt100_n_stage59":int((b.RH_over_ice_pct_diagnostic>100).sum())}
    if (sha(S53/F53)!=pins["stage53_patch_sha256"] or
        sha(S59/F59)!=pins["stage59_phase_sha256"]):
        raise ValueError("Immutable input changed during Stage60 staging")
    manifest={"schema":"STAGE60_UNIFIED_4411_ERA5_WATER_HUMIDITY_SELECTION_v1",
       "total_unique_rows":4411,"n_stage53_444":444,
       "n_stage59_3967":3967,"n_Ho1_UTC_HOLD_not_included":917,
       "crosswalk_Stage54_overlap":0,
       "independent_ERA5_dataset":PRODUCT,
       "tower_original_T_and_P_retained":True,
       "subzero_ice_RH_over100_not_automatically_clipped":True,
       "water_based_VPD_and_QBOT_physics_reproduced":True,
       "user_selected_substitution_policy":True,
       "science_water_RH_and_QBOT_candidate_ready_for_full_QA":True,
       "approved_for_DATM":False,
       "approved_for_spinup":False,
       "source_originals_modified":False,"forcing_modified":False,
       "input_sha256":pins,"output_sha256":{
           patch.name:sha(patch),recs.name:sha(recs)},
       "numeric_cautions":stats}
    (dest/"unified_science_policy_manifest.json").write_text(
       json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE60 STAGING PASS | 4411 source-unique ERA5 water-humidity replacements")
    print("REPORT",dest)
    print("NO RAW, NETCDF, DATM, CIME, SPINUP OR SLURM CHANGES")
if __name__=="__main__":
    main()

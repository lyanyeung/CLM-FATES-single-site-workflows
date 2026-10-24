#!/usr/bin/env python3
"""Stage64 Batch02: exact 26,332-hard-event census and 9,389 unique humidity candidates.

Merge SHA-verified Stage60 4,411, Stage62 4,801 and Stage63 177 cold
source-neighbor T-accepted water-reference RH/VPD/QBOT candidates.
Independently reconcile all site/native-timestamp identities to original
Stage61 26,332 hard humidity source events. 16,788 US-Ho1 original hard
events, 86 US-BZS BIF holds and 69 Stage63 T holds remain NOT corrected.
Stage49's 100 dry-only extra review events are outside the 26,332 hard
union and are not automatically replaced.

User authorized physical-rule-based repair, NOT model-forcing writes.
This isolated science ledger does not alter original EC, previous stages,
NETCDF forcing, DATM streams, CIME, Slurm jobs, or spin-up.
"""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
S61=REPORT/"stage61_stage49_vs_stage60_full_hard_coverage_20261024T114810Z_fc209bf8"
S60=REPORT/"stage60_4411_ERA5_water_RH_VPD_QBOT_unified_20261024T112137Z_950f7adf"
S62=REPORT/"stage62_nonHo1_5133_verified_CDS_stage_20261024T225848Z_db032320"
S63=REPORT/"stage63_246_temperature_auto_neighbor_QC_20261024T231206Z_b5fac2db"
F61="all_26432_original_review_events_stage60_status.csv"
F60="4411_unique_original_tower_time_ERA5_water_humidity_patch.csv"
F62="5133_uncovered_hard_events_CDS_candidate_status.csv"
F63="246_exact_original_temperature_neighbor_source_decisions.csv"
KEEP62="CANDIDATE_EXTERNAL_ERA5_WATER_HUMIDITY_ORIGINAL_T_PA"
HOLD62T="HOLD_ORIGINAL_TOWER_T_VS_ERA5_GT8C"
KEEP63="AUTO_KEEP_ORIGINAL_TA_F_SOURCE_NEIGHBOR_VALIDATED_COLD"
ERA="reanalysis-era5-single-levels-timeseries"
EXPECTED_HOLDS={"HOLD_ORIGINAL_TA_OUTSIDE_COLD_POLICY":48,
    "HOLD_TEMPORAL_JUMP_OR_NONSTATIONARY":12,
    "HOLD_NEIGHBOR_QC_UNVERIFIED":9}
N_PATCH=9389
N_HOLD=16943
N_HO1=16788
N_BZS=86

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()

def read_manifest(folder,name):
    if not folder.is_dir() or (folder/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Upstream report absent or incomplete "+str(folder))
    return json.loads((folder/name).read_text())

def verify_outputs(folder,checks):
    if not isinstance(checks,dict) or not checks:
        raise ValueError("Missing upstream content SHA256 "+str(folder))
    for name,digest in checks.items():
        if sha(folder/name)!=digest:
            raise ValueError("Upstream source checksum changed "+str(folder/name))

def normal_times(series):
    a=series.astype(str).str.strip().str.replace(r"\.0$","",regex=True)
    t=pd.to_datetime(a,format="%Y%m%d%H%M",errors="raise")
    if t.isna().any() or t.dt.tz is not None:
        raise ValueError("Original tower timestamp has invalid timezone or encoding")
    return t.dt.strftime("%Y%m%d%H%M")

def keys(frame):
    if frame.duplicated(["site","tower_local_start"]).any():
        raise ValueError("Duplicate site/native tower timestamp")
    return set(zip(frame.site,frame.tower_local_start))

def reproduce(t,r,p):
    sat=6.112*np.exp(17.67*t/(t+243.5))
    e=sat*r/100
    v=sat-e
    q=.622*100*e/(p*1000-.378*100*e)
    return v,q

def candidate_frame(source,cohort,site,local,t,p,r,v,q):
    out=pd.DataFrame({
        "site":source[site].astype(str),
        "tower_local_start":normal_times(source[local]),
        "candidate_cohort":cohort,
        "original_TA_C_kept":pd.to_numeric(source[t],errors="raise"),
        "original_PA_kPa_kept":pd.to_numeric(source[p],errors="raise"),
        "replacement_RH_water_pct":pd.to_numeric(source[r],errors="raise"),
        "replacement_VPD_water_hPa":pd.to_numeric(source[v],errors="raise"),
        "replacement_QBOT_kgkg":pd.to_numeric(source[q],errors="raise")})
    out["independent_ERA5_product"]=ERA
    out["approved_for_DATM"]=False
    out["approved_for_spinup"]=False
    return out

def load():
    m61=read_manifest(S61,"coverage_manifest.json")
    m60=read_manifest(S60,"unified_science_policy_manifest.json")
    m62=read_manifest(S62,"candidate_ledger_manifest.json")
    m63=read_manifest(S63,"source_and_science_manifest.json")
    if (m61.get("schema")!="STAGE61_BATCH02_ORIGINAL_STAGE49_HARD_VS_STAGE60_CROSSWALK_v1"
        or m61.get("original_hard_total")!=26332
        or m61.get("original_unique_review")!=26432
        or m61.get("stage60_total_candidate")!=4411
        or m61.get("approved_for_DATM") is not False
        or m60.get("schema")!="STAGE60_UNIFIED_4411_ERA5_WATER_HUMIDITY_SELECTION_v1"
        or m60.get("total_unique_rows")!=4411
        or m60.get("n_Ho1_UTC_HOLD_not_included")!=917
        or m60.get("approved_for_DATM") is not False
        or m60.get("forcing_modified") is not False
        or m62.get("schema")!="STAGE62_BATCH02_NONHO1_5133_CDS_ERA5_REUSE_OR_FETCH_v1"
        or m62.get("target_original_hard_nonHo1")!=5133
        or m62.get("missing_CDS_gridyears")!=0
        or m62.get("independently_verified_CDS_gridyears")!=50
        or m62.get("n_additional_independent_ERA5_candidates")!=4801
        or m62.get("approved_for_DATM") is not False
        or m63.get("schema")!="STAGE63_NONHO1_246_TOWER_T_NEIGHBOR_QC_v1"
        or m63.get("n_original_GT8C")!=246
        or m63.get("n_auto_temperature_accepted")!=177
        or m63.get("n_temperature_still_HOLD")!=69
        or m63.get("n_Stage62_other_ERA5_humidity_proposals")!=4801
        or m63.get("approved_for_DATM") is not False
        or m63.get("no_original_or_forcing_writes") is not True):
        raise ValueError("Incorrect Stage61/60/62/63 source scope or science gate")
    verify_outputs(S61,m61["output_sha256"])
    verify_outputs(S60,m60["output_sha256"])
    verify_outputs(S62,m62["outputs_SHA256"])
    verify_outputs(S63,m63["output_sha256"])
    if m63["input_sha256"]["stage62_report_sha256"]!=sha(S62/F62):
        raise ValueError("Stage63 original Stage62 source link changed")
    for name,expected in m63["input_sha256"].items():
        if name=="stage62_report_sha256": continue
        if name=="stage62_manifest_sha256" and expected!=sha(S62/"candidate_ledger_manifest.json"):
            raise ValueError("Stage63/62 manifest link changed")
    for name,expected in m62.get("source_SHA256",{}).items():
        if name=="Stage61_manifest_sha256" and expected!=sha(S61/"coverage_manifest.json"):
            raise ValueError("Stage62/61 original source link changed")
    a=pd.read_csv(S61/F61,dtype={"site":str,"timestamp_start":str})
    b=pd.read_csv(S60/F60,dtype={"site":str,"tower_local_start":str})
    c=pd.read_csv(S62/F62,dtype={"site":str,"timestamp_start":str,
                                 "source_sha256":str})
    d=pd.read_csv(S63/F63,dtype={"site":str,"timestamp_start":str,
                                 "source_sha256":str})
    a["tower_local_start"]=normal_times(a.timestamp_start)
    b["tower_local_start"]=normal_times(b.tower_local_start)
    c["tower_local_start"]=normal_times(c.timestamp_start)
    d["tower_local_start"]=normal_times(d.timestamp_start)
    for dataset in (a,b,c,d):
        keys(dataset)
    hard=a.loc[a.hard_original.astype(str).str.lower().eq("true")].copy()
    if len(a)!=26432 or len(hard)!=26332 or len(b)!=4411 or len(c)!=5133 or len(d)!=246:
        raise ValueError("Original Stage61/full cohort row census changed")
    if Counter(c.candidate_status)!={KEEP62:4801,
         HOLD62T:246,"HOLD_RELEASE_BIF_UNVERIFIED":86}:
        raise ValueError("Stage62 full source route counts changed")
    if Counter(d.original_tower_T_decision)!={KEEP63:177,**EXPECTED_HOLDS}:
        raise ValueError("Stage63 original source QC decision counts changed")
    if keys(d)!=keys(c.loc[c.candidate_status.eq(HOLD62T)]):
        raise ValueError("Stage63 246 not exactly the Stage62 >8C source identities")
    merged=c.merge(d[["site","tower_local_start","source_sha256",
        "source_csv_row","original_TA_C","source_PA_kPa","ERA5_RH_water_pct",
        "original_tower_T_decision"]],on=["site","tower_local_start"],
        suffixes=("_62","_63"),how="left",validate="one_to_one")
    focused=merged.loc[merged.candidate_status.eq(HOLD62T)]
    if (len(focused)!=246 or
        not focused.source_sha256_62.eq(focused.source_sha256_63).all() or
        not focused.source_csv_row_62.eq(focused.source_csv_row_63).all() or
        not np.allclose(focused.TA_C,focused.original_TA_C,rtol=0,atol=1.e-5) or
        not np.allclose(focused.PA_kPa,focused.source_PA_kPa,rtol=0,atol=1.e-5) or
        not np.allclose(focused.ERA5_RH_water_pct_62,
                        focused.ERA5_RH_water_pct_63,rtol=0,atol=1.e-6)):
        raise ValueError("Stage63 original source TA/PA/RH identity does not match Stage62")
    return hard,b,c,d,m61,m60,m62,m63

def build(hard,b,c,d):
    st60=candidate_frame(b,"STAGE60_4411","site","tower_local_start",
        "original_TA_C_kept","original_PA_kPa_kept",
        "replacement_RH_water_pct","replacement_VPD_water_hPa",
        "replacement_QBOT_kgkg")
    good62=c.loc[c.candidate_status.eq(KEEP62)].copy()
    st62=candidate_frame(good62,"STAGE62_4801","site","tower_local_start",
        "TA_C","PA_kPa","ERA5_RH_water_pct",
        "candidate_VPD_water_hPa","candidate_QBOT_kgkg")
    good63=d.loc[d.original_tower_T_decision.eq(KEEP63)].copy()
    if not (good63.original_TA_C.lt(0).all() and
        good63.neighbor_temporal_continuity.astype(str).str.lower().eq("true").all() and
        good63.neighbor_QC0_or_QC1.astype(str).str.lower().eq("true").all() and
        good63.neighbor_smooth_both_sides.astype(str).str.lower().eq("true").all()):
        raise ValueError("Stage63 177 cold auto-acceptances lost neighbor verification")
    st63=candidate_frame(good63,"STAGE63_177","site","tower_local_start",
        "original_TA_C","source_PA_kPa","ERA5_RH_water_pct",
        "independent_ERA5_water_VPD_hPa",
        "independent_ERA5_water_QBOT_kgkg")
    combined=pd.concat([st60,st62,st63],ignore_index=True)
    combined.sort_values(["site","tower_local_start"],inplace=True,ignore_index=True)
    if (len(combined)!=N_PATCH or
        Counter(combined.candidate_cohort)!={"STAGE60_4411":4411,
                                            "STAGE62_4801":4801,
                                            "STAGE63_177":177}):
        raise ValueError("The three sources do not add to 9389")
    selected=keys(combined)
    raw=keys(hard)
    if not selected.issubset(raw):
        raise ValueError("A proposed correction does not belong to original 26332 hard events")
    for name,part in (("Stage60",st60),("Stage62",st62),("Stage63",st63)):
        if len(keys(part))!=len(part):
            raise ValueError("Duplicate "+name+" original tower records")
    t=combined.original_TA_C_kept.to_numpy(float)
    p=combined.original_PA_kPa_kept.to_numpy(float)
    rh=combined.replacement_RH_water_pct.to_numpy(float)
    vpd=combined.replacement_VPD_water_hPa.to_numpy(float)
    q=combined.replacement_QBOT_kgkg.to_numpy(float)
    with np.errstate(all="ignore"):
        v_check,q_check=reproduce(t,rh,p)
    if (not np.isfinite(t).all() or not np.isfinite(p).all() or
        not np.isfinite(rh).all() or (t<=-80).any() or (t>=65).any() or
        (p<=50).any() or (p>=110).any() or
        (rh<=0).any() or (rh>100.05).any() or
        (vpd<-0.005).any() or (q<=0).any() or (q>=.08).any() or
        not np.allclose(vpd,v_check,rtol=1e-7,atol=1e-8) or
        not np.allclose(q,q_check,rtol=1e-7,atol=1e-9)):
        raise ValueError("9389 paired independent water RH/VPD/QBOT physical crosscheck FAILED")
    combined["phase_over_ice_reference_not_used_for_model"]=True
    combined["water_RH_numerically_physical"]=True
    combined["scientific_candidate_only_DATM_HOLD"]=True
    combined["approved_for_DATM"]=False
    combined["approved_for_spinup"]=False
    # Original hard physics statuses, complete site/time-disjoint population
    full=hard.copy()
    full["repair_status"]="MISSING_STATUS"
    for src,label in ((st60,"STAGE60_4411_CANDIDATE"),
                      (st62,"STAGE62_4801_CANDIDATE"),
                      (st63,"STAGE63_177_T_ACCEPTED_CANDIDATE")):
        k=set(zip(src.site,src.tower_local_start))
        match=[(site,when) in k for site,when in
                 zip(full.site,full.tower_local_start)]
        if full.loc[match,"repair_status"].ne("MISSING_STATUS").any():
            raise ValueError("Cross-cohort double accounting in original hard ledger")
        full.loc[match,"repair_status"]=label
    not_done=full.repair_status.eq("MISSING_STATUS")
    for key,route in (( "US-Ho1","HOLD_HO1_SOURCE_RELEASE_UTC_NOT_VERIFIED"),
                      ("US-BZS","HOLD_BZS_SOURCE_RELEASE_BIF_NOT_VERIFIED")):
        idx=not_done&full.site.eq(key)
        full.loc[idx,"repair_status"]=route
    rem=c.loc[c.candidate_status.eq(HOLD62T)]
    unresolved=d.loc[d.original_tower_T_decision.ne(KEEP63)]
    lookup={ (r.site,r.tower_local_start):str(r.original_tower_T_decision)
             for r in unresolved.itertuples(index=False)}
    for idx,row in full.loc[full.repair_status.eq("MISSING_STATUS")].iterrows():
        key=(row.site,row.tower_local_start)
        if key not in lookup:
            raise ValueError("Residual original hard event lacks Stage63 route "+str(key))
        full.at[idx,"repair_status"]=lookup[key]
    classes=Counter(full.repair_status)
    if (classes.get("HOLD_HO1_SOURCE_RELEASE_UTC_NOT_VERIFIED")!=N_HO1 or
        classes.get("HOLD_BZS_SOURCE_RELEASE_BIF_NOT_VERIFIED")!=N_BZS or
        sum(classes.get(name,0) for name in EXPECTED_HOLDS)!=69 or
        len(full)!=26332 or
        full.repair_status.eq("MISSING_STATUS").any()):
        raise ValueError("Full original hard 26332 = 9389 selected +16943 HOLD failed")
    holds=full.loc[~full.repair_status.str.contains("_CANDIDATE")].copy()
    if len(holds)!=N_HOLD:
        raise ValueError("Exact residual hard HOLD total differs from 16943")
    summary=[]
    for site,grp in full.groupby("site",sort=True):
        selections=grp.repair_status.str.contains("_CANDIDATE")
        summary.append({"site":site,"original_hard_event_count":len(grp),
            "selected_water_humidity_candidates":int(selections.sum()),
            "remaining_HOLD":int((~selections).sum()),
            "HOLD_Ho1_UTC":int(grp.repair_status.eq(
                "HOLD_HO1_SOURCE_RELEASE_UTC_NOT_VERIFIED").sum()),
            "HOLD_BZS_BIF":int(grp.repair_status.eq(
                "HOLD_BZS_SOURCE_RELEASE_BIF_NOT_VERIFIED").sum()),
            "HOLD_T_context":int(grp.repair_status.isin(EXPECTED_HOLDS).sum())})
    if sum(x["selected_water_humidity_candidates"] for x in summary)!=N_PATCH:
        raise ValueError("Site-level selected humidity census mismatch")
    return combined,full,holds,pd.DataFrame(summary)

def self_test():
    t=np.asarray([-32.,18.])
    rh=np.asarray([75.,48.])
    p=np.asarray([99.,101.])
    v,q=reproduce(t,rh,p)
    assert np.isfinite(v).all() and (v>=0).all() and (q>0).all()
    assert 4411+4801+177==9389
    assert 16788+86+69==16943
    assert 9389+16943==26332
    print("STAGE64 SELF-TEST PASS | 9389 candidate + 16943 explicit HOLD =26332")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    args=ap.parse_args()
    if args.self_test:return self_test()
    hard,b,c,d,m61,m60,m62,m63=load()
    selected,full,holds,summ=build(hard,b,c,d)
    print("STAGE64 SOURCE CHECK PASS | 26332 original hard site/time identities")
    print("CANDIDATE_COUNTS",dict(Counter(selected.candidate_cohort)))
    print("ORIGINAL_HARD_FINAL_STATUS",dict(Counter(full.repair_status)))
    print("SUMMARY_BY_SITE")
    print(summ.to_string(index=False))
    print("TOTAL SELECTED",len(selected),"/ 26332 original hard")
    print("TOTAL HOLD",len(holds),"/ 26332 original hard")
    print("STAGE49 POSITIVE_RH_LT1_ONLY_EXTRA 100 | separate review, not automatically repaired")
    print("MODEL/DATM APPROVAL false for all 26332")
    if args.check:
        print("STAGE64 CHECK PASS | no writes")
        return
    out=REPORT/("stage64_9389_unique_ERA5_humidity_candidates_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    marker=out/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Isolated candidate/hold original science ledger; NO DATM approval.\n")
    outputs={
        "9389_original_tower_time_unified_CDS_ERA5_humidity_candidates.csv":selected,
        "26332_original_hard_source_science_status.csv":full,
        "16943_original_hard_events_still_HOLD.csv":holds,
        "ten_site_26332_hard_status_summary.csv":summ,
        "69_nonHo1_source_temperature_cases_HOLD.csv":
            d.loc[d.original_tower_T_decision.ne(KEEP63)].copy()}
    checks={}
    for name,table in outputs.items():
        p=out/name
        table.to_csv(p,index=False)
        checks[name]=sha(p)
    if (sha(S60/F60)!=m60["output_sha256"][F60] or
        sha(S62/F62)!=m62["outputs_SHA256"][F62] or
        sha(S63/F63)!=m63["output_sha256"][F63]):
        raise ValueError("Source-stage content changed during Stage64 integration")
    manifest={
       "schema":"STAGE64_ORIGINAL_HARD_FULL_CENSUS_9389_CANDIDATES_16943_HOLD_v1",
       "original_stage49_hard_count":26332,
       "Stage60_accepted_candidates":4411,
       "Stage62_accepted_candidates":4801,
       "Stage63_accepted_cold_source_T_candidates":177,
       "total_selected_candidate_rows":9389,
       "remaining_hard_HOLD":16943,
       "Ho1_unverified_time_source_HOLD":16788,
       "BZS_unverified_original_BIF_HOLD":86,
       "remaining_other_original_T_QC_HOLD":69,
       "stage49_original_positive_RH_lt1_only_review":100,
       "source_sha256":{
          "Stage61_full_review_sha256":sha(S61/F61),
          "Stage61_manifest_sha256":sha(S61/"coverage_manifest.json"),
          "Stage60_patch_sha256":sha(S60/F60),
          "Stage60_manifest_sha256":sha(S60/"unified_science_policy_manifest.json"),
          "Stage62_events_sha256":sha(S62/F62),
          "Stage62_manifest_sha256":sha(S62/"candidate_ledger_manifest.json"),
          "Stage63_events_sha256":sha(S63/F63),
          "Stage63_manifest_sha256":sha(S63/"source_and_science_manifest.json")},
       "output_sha256":checks,
       "approved_for_DATM":False,"approved_for_spinup":False,
       "no_original_or_prior_stage_or_model_forcing_writes":True}
    (out/"unified_source_provenance_and_hold_manifest.json").write_text(
       json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE64 AUDIT PASS | 9389 unique humidity candidates; 16943 hard source HOLDs")
    print("REPORT",out)
    print("NO SOURCE, PREVIOUS-STAGE, DATM, NETCDF FORCING, CIME OR SLURM CHANGES")
if __name__=="__main__":
    main()

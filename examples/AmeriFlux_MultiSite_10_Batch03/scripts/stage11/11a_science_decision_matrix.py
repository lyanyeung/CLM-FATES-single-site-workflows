#!/usr/bin/env python3
"""Stage11a: SHA-pinned review-only humidity science decision matrix.

--self-test: synthetic data only, no IRIDIS accesses or outputs.
--check: verify previous evidence and build all matrices IN MEMORY, no writes.
--run: create a NEW reports/stage11a_* folder with event and site-year
        decision CSVs plus receipt. Never writes or approves forcing.

This produces REVIEW ROUTES, NOT SCIENTIFIC SIGN-OFF. No UTC offset, Post-v5,
DATM or CLM-FATES run is approved.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11a-v1-20261024"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
D=ROOT/"reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
H=ROOT/"reports/stage10h_original_source_provenance_20261024T054425Z_faf342a8"
K=ROOT/"reports/stage10k_exception_provenance_20261024T061150Z_13a3a08a"
G=ROOT/"reports/stage10g_source_qc0_7day_20261024T045334Z_691519c6"
KEYS=["site","source_csv_row","time"]
BLOCKED={"US-Kon":229,"US-MMS":18,"US-Me2":4,"US-Me6":1,
         "US-MtB":15,"US-NR1":173,"US-NR3":1484}
BATCH=["US-Kon","US-Me2","US-Me6","US-MMS","US-MOz","US-Mpj",
       "US-MtB","US-NC2","US-NR1","US-NR3"]
D_OUT={"all_1924_manual_review.csv","site_triage_summary.csv",
       "consecutive_event_clusters.csv","P0_high_priority_events.csv",
       "B_ice_supersaturation_78.csv","A_water_failure_27.csv"}
H_OUT={"original_qc_source_classes_at_1924_blockers.csv",
       "affected_years_source_qc_distributions.csv",
       "US-NR3_2017_2018_2023_source_qc.csv",
       "site_blocker_source_qc_summary.csv","primary_vs_ERA_timestamp_coverage.csv"}
K_OUT={"exception_2_US-NR3_events.csv","1924_counterfactual_science_gate.csv",
       "site_counterfactual_qc_reconciliation.csv",
       "site_year_counterfactual_qc_reconciliation.csv"}
G_OUT={"19_cluster_QC0_24_72_168h.csv","affected_years_raw_QC_coverage.csv",
       "site_QC0_gap_summary.csv"}


def safe_file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or unsafe file: "+str(p))
    return p


def safe_dir(path):
    p=Path(path)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing or unsafe directory: "+str(p))
    return p


def sha(path):
    h=hashlib.sha256()
    with safe_file(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(safe_file(path).read_text(encoding="utf-8"))


def boolean(df,name):
    s=df[name].astype(str).str.strip().str.lower()
    if not s.isin(["true","false","1","0"]).all():
        raise ValueError("Invalid boolean field: "+name)
    return s.isin(["true","1"]).to_numpy(dtype=bool)


def numeric(df,name):
    x=pd.to_numeric(df[name],errors="coerce").to_numpy(dtype=float)
    x[~np.isfinite(x)|(x<=-9990)]=np.nan
    return x


def ids(df):
    if len(df)!=1924 or df.duplicated(KEYS).any():
        raise ValueError("Source event identity is not unique 1924-row scope")
    return set(map(tuple,df[KEYS].to_numpy()))


def check_receipt(folder,receipt_name,sha_key,expected):
    item=read_json(folder/receipt_name)
    if set(item.get(sha_key,{}))!=expected:
        raise ValueError("Source report file manifest changed: "+str(folder))
    for name in expected:
        if sha(folder/name)!=item[sha_key][name]:
            raise ValueError("Source report SHA mismatch: "+str(folder/name))
    return item


def preflight():
    for folder in (ROOT,S07,D,H,K,G):
        safe_dir(folder)
    safe_file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    md=check_receipt(D,"read_only_provenance.json","output_sha256",D_OUT)
    mh=check_receipt(H,"read_only_provenance.json","output_sha256",H_OUT)
    mk=check_receipt(K,"scientific_hold_receipt.json","output_sha256",K_OUT)
    mg=check_receipt(G,"read_only_provenance.json","outputs_sha256",G_OUT)
    if (md.get("events")!=1924 or md.get("no_replacement_approved") is not True
        or md.get("priorities_are_approval") is not False
        or mh.get("selected_events")!=1924 or mh.get("selected_site_years")!=32
        or mh.get("source_era_alignment")!="EXACT_TIMESTAMP_ONLY_NO_POSITIONAL_JOIN_NO_TIME_SHIFT"
        or mh.get("stage10d_provenance_sha256")!=sha(D/"read_only_provenance.json")
        or mh.get("scientific_status")!="READ-ONLY SOURCE PROVENANCE; ALL 1924 REPAIRS UNAPPROVED"
        or mk.get("event_rows")!=1924 or mk.get("exception_rows")!=2
        or mk.get("repair_approvals")!=0 or mk.get("clock_approvals")!=0
        or mg.get("selected_events")!=89 or mg.get("clusters")!=19
        or mg.get("science_gate")!="NO TIMES/CLOCKS/REPAIRS APPROVED"):
        raise ValueError("Prior report review/approval status changed")
    manifest=read_json(S07/"exact_input_manifest.json")
    if mh.get("stage07_input_manifest_sha256")!=sha(S07/"exact_input_manifest.json"):
        raise ValueError("Stage10h does not pin Stage07 source manifest")
    items=manifest["sites"]
    if len(items)!=10 or set(str(item["site"]) for item in items)!=set(BATCH):
        raise ValueError("Stage07 10-site source inventory differs")
    pins={str(Path(p).resolve()):v for p,v in manifest["input_sha256"].items()}
    for item in items:
        for kind in ("primary","era"):
            path=safe_file(item[kind])
            if sha(path)!=pins.get(str(path.resolve())):
                raise ValueError("Stage07 original source modified: "+str(path))
    def read(folder,name):
        return pd.read_csv(safe_file(folder/name),dtype={k:str for k in KEYS},
                           keep_default_na=False,low_memory=False)
    d=read(D,"all_1924_manual_review.csv")
    h=read(H,"original_qc_source_classes_at_1924_blockers.csv")
    k=read(K,"1924_counterfactual_science_gate.csv")
    a=ids(d)
    if a!=ids(h) or a!=ids(k):
        raise ValueError("Stage10d/10h/10k source row identities disagree")
    for x in (d,h,k):
        if x.site.value_counts().to_dict()!=BLOCKED:
            raise ValueError("Wrong per-site blocker counts")
    return d,h,k,{
        "Stage07_manifest":sha(S07/"exact_input_manifest.json"),
        "Stage10d_receipt":sha(D/"read_only_provenance.json"),
        "Stage10h_receipt":sha(H/"read_only_provenance.json"),
        "Stage10k_receipt":sha(K/"scientific_hold_receipt.json"),
        "Stage10g_receipt":sha(G/"read_only_provenance.json"),
    }


def analyze(d,h,k,production=True):
    dr=KEYS+["review_priority","event_cluster_id",
             "flag_A_water_failure","flag_A_ice_supersaturation",
             "flag_B_ice_supersaturation","flag_tower_grid_T_gt5C",
             "independent_A_physical_pass","independent_B_physical_pass",
             "MDS_pair_physical_screen_pass","MDS_QC_both_0_or_1",
             "scientific_hold_required"]
    hr=KEYS+["TA_F_QC_raw","VPD_F_QC_raw","original_ERA_timestamp_matched"]
    kr=KEYS+["native_source_VPD_QC2","counterfactual_category",
             "VPD_only_nonnegative","T_only_nonnegative",
             "source_VPD_excess_over_es_hPa","source_T_minus_grid_T_C"]
    for name,frame,cols in (("Stage10d",d,dr),("Stage10h",h,hr),("Stage10k",k,kr)):
        if not set(cols).issubset(frame.columns):
            raise ValueError(name+" missing fields: "+str(set(cols)-set(frame.columns)))
        if frame.duplicated(KEYS).any():
            raise ValueError(name+" duplicate source event keys")
    joined=d[dr].merge(h[hr],on=KEYS,validate="one_to_one")
    joined=joined.merge(k[kr],on=KEYS,validate="one_to_one")
    if len(joined)!=len(d):
        raise ValueError("Event merge lost source records")
    if not boolean(joined,"scientific_hold_required").all():
        raise ValueError("Upstream report contains an approved event")
    if not boolean(joined,"original_ERA_timestamp_matched").all():
        raise ValueError("Source event lacks exact matched companion ERA timestamp")
    A_fail=boolean(joined,"flag_A_water_failure")
    B_ice=boolean(joined,"flag_B_ice_supersaturation")
    A_ice=boolean(joined,"flag_A_ice_supersaturation")
    grid_t=boolean(joined,"flag_tower_grid_T_gt5C")
    if np.any(A_fail==boolean(joined,"independent_A_physical_pass")):
        raise ValueError("A-fail markers contradict Stage10d physical flags")
    if not boolean(joined,"independent_B_physical_pass").all():
        raise ValueError("Stage10b B-liquid-water screen no longer passes")
    source_QC=numeric(joined,"VPD_F_QC_raw")
    source_TQC=numeric(joined,"TA_F_QC_raw")
    if not np.isin(source_QC,[0,1,2]).all() or not np.isin(source_TQC,[0,1,2]).all():
        raise ValueError("Unexpected native source QC class")
    if not np.array_equal(source_QC==2,boolean(joined,"native_source_VPD_QC2")):
        raise ValueError("Stage10h/10k VPD source provenance changed")
    if production and (len(joined)!=1924 or (source_QC==2).sum()!=1866 or
        (source_QC==1).sum()!=58 or (source_QC==0).sum()!=0 or
        A_fail.sum()!=27 or B_ice.sum()!=78 or A_ice.sum()!=170 or grid_t.sum()!=150):
        raise ValueError("Stage10k known QC and physics counts changed")
    me2=joined.site.eq("US-Me2").to_numpy()
    events=joined.copy()
    events["year"]=pd.to_datetime(events.time,errors="raise").dt.year
    events["VPD_origin"]=np.select([source_QC==0,source_QC==1,source_QC==2],
        ["QC0_MEASURED","QC1_GAPFILLED","QC2_DOWNSCALED_ERA"],"UNKNOWN")
    events["TA_origin"]=np.select([source_TQC==0,source_TQC==1,source_TQC==2],
        ["QC0_MEASURED","QC1_GAPFILLED","QC2_DOWNSCALED_ERA"],"UNKNOWN")
    events["review_route"]=np.select([me2,A_fail|B_ice|grid_t],
        ["CLOCK_METADATA_HOLD","PHYSICS_CONFLICT_HOLD"],
        "EVIDENCE_INSUFFICIENT_HOLD")
    events["method_B_status"]=np.where(B_ice,
        "ERA5LAND_B_ICE_PHASE_CAUTION_NO_APPROVAL",
        "ERA5LAND_B_DIAGNOSTIC_ONLY_NOT_INDEPENDENT")
    events["A_ice_phase_caution"]=A_ice
    events["B_ice_phase_caution"]=B_ice
    events["grid_temperature_caution"]=grid_t
    events["source_VPD_QC0_measured"]=source_QC==0
    events["MDS_physical_AND_QC01"]=(
        boolean(joined,"MDS_pair_physical_screen_pass")&
        boolean(joined,"MDS_QC_both_0_or_1"))
    events["grid_VPD_swap_math_nonnegative"]=boolean(joined,"VPD_only_nonnegative")
    events["approved_for_new_forcing"]=False
    events["clock_approved"]=False
    events["post_v5_approved"]=False
    events["reviewer_name"]=""
    events["review_notes"]=""
    events["next_review"]=np.select(
        [me2,A_fail,B_ice,grid_t],
        ["VERIFY_EXACT_RELEASE_CLOCK",
         "EVALUATE_SOURCE_WATER_PHYSICS_AND_ALTERNATIVE_E",
         "ASSESS_ICE_SUPERSATURATION_WITH_VALIDATED_PHASE",
         "ASSESS_TOWER_ERA_GRID_TEMPERATURE_ELEVATION_BIAS"],
        "SEEK_INDEPENDENT_HUMIDITY_EVIDENCE")
    if production and events.MDS_physical_AND_QC01.sum()!=0:
        raise ValueError("Stage10d source MDS QC conclusion changed")
    grouped=events.groupby(["site","year"],sort=True)
    year=grouped.agg(
        blockers=("site","size"),
        VPD_QC0=("source_VPD_QC0_measured","sum"),
        VPD_QC1=("VPD_origin",lambda x:int((x=="QC1_GAPFILLED").sum())),
        VPD_QC2=("VPD_origin",lambda x:int((x=="QC2_DOWNSCALED_ERA").sum())),
        A_water_fail=("flag_A_water_failure",lambda x:int(x.astype(str).str.lower().eq("true").sum())),
        B_ice_caution=("B_ice_phase_caution","sum"),
        A_ice_caution=("A_ice_phase_caution","sum"),
        grid_temp_gt5C=("grid_temperature_caution","sum"),
        clock_holds=("review_route",lambda x:int((x=="CLOCK_METADATA_HOLD").sum())),
        physics_holds=("review_route",lambda x:int((x=="PHYSICS_CONFLICT_HOLD").sum())),
        evidence_holds=("review_route",lambda x:int((x=="EVIDENCE_INSUFFICIENT_HOLD").sum())),
        VPD_swap_numerical_pass=("grid_VPD_swap_math_nonnegative","sum"),
    ).reset_index()
    year["clock_state"]=np.where(year.site=="US-Me2",
        "US_ME2_EXACT_RELEASE_BIF_NOT_AVAILABLE",
        "BIF_PUBLISHED_OFFSET_NOT_FORMALLY_APPROVED")
    year["independent_tower_humidity_validated"]=False
    year["ERA_grid_elevation_height_checked"]=False
    year["subzero_water_ice_phase_reviewed"]=False
    year["PFT_surface_science_approved"]=False
    year["review_status"]="HOLD_SCIENTIFIC_SIGNOFF_REQUIRED"
    year["approved_rows"]=0
    year["post_v5_ready"]=False
    year["science_reviewer"]=""
    year["science_rationale"]=""
    year["science_signoff_date"]=""
    year["required_action"]=np.where(year.site=="US-Me2",
        "RELEASE_CLOCK_AND_FULLSET_METADATA",
        np.where(year.A_water_fail.gt(0)|year.B_ice_caution.gt(0),
            "COLD_HUMIDITY_PHASE_AND_INDEPENDENT_SOURCE",
            np.where(year.grid_temp_gt5C.gt(0),
                "GRID_HEIGHT_TERRAIN_AND_INDEPENDENT_SOURCE",
                "SOURCE_PROVENANCE_UNCERTAINTY")))
    batch=pd.DataFrame([{
        "site":site,
        "stage07_state":("HUMIDITY_BLOCKED_NUMERIC_TRIAL" if site in BLOCKED
                         else "NUMERIC_ONLY_CANDIDATE_POSTV5_NOT_APPROVED"),
        "stage11a_blockers":BLOCKED.get(site,0),
        "affected_years":int(year.site.eq(site).sum()),
        "clock_approved":False,"PFT_science_approved":False,
        "CO2_protocol_approved":False,"post_v5_ready":False,
        "DATM_ready":False,"spinup_authorized":False,
    } for site in BATCH])
    if production and (len(year)!=32 or len(batch)!=10 or
        int(year.blockers.sum())!=1924 or int(year.VPD_QC2.sum())!=1866):
        raise ValueError("Stage11a year-site coverage differs from 32/10 sites")
    if (events.approved_for_new_forcing.any() or year.post_v5_ready.any()
        or batch.spinup_authorized.any()):
        raise ValueError("Unexpected auto-approval")
    return events,year,batch


def self_test():
    d=pd.DataFrame({
        "site":["US-Me2","US-NR3"],"source_csv_row":["5","10"],
        "time":["2014-01-01 00:00:00","2018-02-21 09:30:00"],
        "review_priority":["P0_US_ME2","P0_A_WATER"],
        "event_cluster_id":["x","y"],
        "flag_A_water_failure":[False,True],
        "flag_A_ice_supersaturation":[False,True],
        "flag_B_ice_supersaturation":[False,True],
        "flag_tower_grid_T_gt5C":[False,True],
        "independent_A_physical_pass":[True,False],
        "independent_B_physical_pass":[True,True],
        "MDS_pair_physical_screen_pass":[False,False],
        "MDS_QC_both_0_or_1":[False,False],
        "scientific_hold_required":[True,True]})
    h=d[KEYS].copy()
    h["TA_F_QC_raw"]=[0,2];h["VPD_F_QC_raw"]=[1,2]
    h["original_ERA_timestamp_matched"]=[True,True]
    k=d[KEYS].copy()
    k["native_source_VPD_QC2"]=[False,True]
    k["counterfactual_category"]=["GRID_VPD_ONLY_REMOVES_NEGATIVE_EA",
                                    "GRID_T_ONLY_REMOVES_NEGATIVE_EA"]
    k["VPD_only_nonnegative"]=[True,False]
    k["T_only_nonnegative"]=[False,True]
    k["source_VPD_excess_over_es_hPa"]=[0.2,0.3]
    k["source_T_minus_grid_T_C"]=[1.,-5.]
    events,year,batch=analyze(d,h,k,production=False)
    assert len(events)==2 and len(year)==2 and len(batch)==10
    assert events.loc[events.site=="US-Me2","review_route"].iloc[0]=="CLOCK_METADATA_HOLD"
    assert events.loc[events.site=="US-NR3","review_route"].iloc[0]=="PHYSICS_CONFLICT_HOLD"
    assert not events.approved_for_new_forcing.any() and not batch.DATM_ready.any()
    assert year.VPD_QC1.sum()==1 and year.VPD_QC2.sum()==1
    print("STAGE11A SELF-TEST PASS: clock/physics holds, QC1/QC2, 10-site inventory, zero approvals",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    opt=parser.add_mutually_exclusive_group(required=True)
    opt.add_argument("--self-test",action="store_true")
    opt.add_argument("--check",action="store_true")
    opt.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print("STAGE11A — SCIENCE DECISION MATRIX | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    d,h,k,pins=preflight()
    events,year,batch=analyze(d,h,k)
    print("\n========== SCIENCE ROUTE COUNTS ==========",flush=True)
    print(events.review_route.value_counts().to_string(),flush=True)
    print("\n========== AFFECTED SITE/YEAR DECISION MATRIX ==========",flush=True)
    cols=["site","year","blockers","VPD_QC1","VPD_QC2","A_water_fail",
          "B_ice_caution","grid_temp_gt5C","clock_holds","physics_holds",
          "evidence_holds","review_status"]
    print(year[cols].to_string(index=False),flush=True)
    print("\n========== BATCH 10-SITE READINESS ==========",flush=True)
    print(batch.to_string(index=False),flush=True)
    print(f"\nSTAGE11A SUMMARY: events={len(events)}/1924 site_years={len(year)}/32 "
          f"batch_sites={len(batch)}/10 source_QC2={int(year.VPD_QC2.sum())}/1866 "
          "repair_approvals=0 clock_approvals=0 postv5_approvals=0 spinup_authorizations=0",flush=True)
    if args.check:
        print("CHECK ONLY: zero report or forcing writes.",flush=True)
        return
    out=ROOT/"reports"/("stage11a_science_decision_matrix_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    exports={
        "1924_source_event_science_review.csv":events,
        "32_site_year_science_decision_matrix.csv":year,
        "10_site_post_v5_readiness.csv":batch,
    }
    for name,df in exports.items():
        df.to_csv(out/name,index=False)
    guide="""# Stage11a review guide

Review routes are **not** approvals. CLOCK_METADATA_HOLD is US-Me2; PHYSICS_CONFLICT_HOLD
contains water-physics failures, ice-saturation cautions or >5 C tower-grid
temperature mismatches; EVIDENCE_INSUFFICIENT_HOLD includes remaining rows
without independently measured source VPD. All original selected VPD
observations are QC1 (gapfill) or QC2 (ERA-downscaled), not QC0 measurement.

A physically passing ERA5-Land candidate is NOT an accepted humidity forcing.
Review exact-release clock, cold-air water/ice phase convention, true humidity
measurement evidence, source downscaling dependence, tower-grid height and
elevation, source uncertainty, and event continuity.

All 10 sites require independent Post-v5, PFT/surface, CO2 and DATM approval.
The 3 numeric-only Stage07 site candidates are not final. The 7 affected
sites have 1924 remaining science holds.

Reviewer/notes columns are deliberately blank. This hash-sealed result is
not a place to modify an approval flag; use a separately versioned signed
review decision after physical/source evidence has been independently checked.
DO NOT overwrite original forcing or delete Stage07 incomplete hold marker.
"""
    (out/"REVIEW_GUIDE.md").write_text(guide,encoding="utf-8")
    receipt={
        "script_version":VERSION,"events":1924,"affected_site_years":32,"batch_sites":10,
        "input_SHA256":pins,"zero_automatic_approvals":True,"clock_approvals":0,
        "humidity_repair_approvals":0,"post_v5_approvals":0,"DATM_ready_sites":0,
        "spinup_authorizations":0,"stage07_incomplete_marker_retained":True,
        "output_SHA256":{name:sha(out/name) for name in [*exports,"REVIEW_GUIDE.md"]}}
    (out/"scientific_hold_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE11A REPORT DIR:",out,flush=True)
    print("SCIENCE HOLD: no original forcing, DATM, model case or Slurm modifications.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE11A STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

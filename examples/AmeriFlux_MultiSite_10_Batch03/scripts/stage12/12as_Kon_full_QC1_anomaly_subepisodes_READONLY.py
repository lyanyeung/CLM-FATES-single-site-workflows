#!/usr/bin/env python3
"""Stage12as — classify complete original US-Kon QC1/MDS intervals, NOT just
the 31 preselected neighbor edits. Research-only native 30-min subepisode
triage, never an automatic forcing repair or physical source-of-truth claim.

Input: exact signed Stage12ar 436 native rows in 5 complete QC1 runs,
per-run nearby *measured QC0* versus ERA-RH diagnostic benchmarks.
Outputs: full 436-row read-only classification, contiguous potential-
anomaly subepisodes, 31 selected-row crosswalk and 5-run summaries.

Exploratory flags (not approvals):
 - PHYSICAL_RH_OUT_OF_BOUNDS: original MDS-derived RH <0 or >100%;
 - SEVERE_DRY_DISAGREEMENT: original RH in [0,25), ERA RH >=35%,
   original_minus_ERA <= -25 percentage points, and tower T QC0;
 - LARGE_DRY_DIFFERENCE / LARGE_MOIST_DIFFERENCE: >=25 pp;
 - other valid/unresolved.
Nearby QC0 comparison is contextual, overlapping and correlated. ERA is
not independently observed ground truth, nor are QC1 MDS values QC0.

--self-test: synthetic logic only, no source files and no writes.
--check: SHA-locked upstream audit and in-memory analysis, no writes.
--run: same + isolated signed research REPORTS ONLY. No original/forcing
or time/previous trial/DATM/spinup/model/Slurm changes.
"""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
V = "batch03-stage12as-v1-20261026-Kon-complete-QC1-scoped-subepisodes"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AR = ROOT / "reports/stage12ar_Kon_five_full_QC1_run_MDS_vs_ERA_science_review_20261026T114449Z_5412b997"
AQ = ROOT / "reports/stage12aq_Kon_full_QC1_run_and_14day_QC0_ERA_RH_review_20261026T113539Z_dcadacde"
FULL = "five_QC1_run_all_original_native_halhours_MDS_vs_ERA.csv"
RUNS = "five_run_original_MDS_vs_ERA_RH_and_local_QC0_error_summary.csv"
MARK = "SCIENTIFIC_HOLD_NO_APPROVAL_NO_DATM"
KEEP = {"201102220900", "201109291830"}
HALF_HOUR = pd.Timedelta(minutes=30)
UNAPPROVED_CENTERS = 48
UNAPPROVED_NEIGHBORS = 31
MAX_DELTA = 25.0

def safe(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink immutable science input: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def flag(value):
    return str(value).lower() == "true"

def classify(rh_mds,rh_era,t_qc):
    if not np.isfinite(rh_mds) or not np.isfinite(rh_era):
        return "NONFINITE_SOURCE_OR_ERA"
    if rh_mds < 0 or rh_mds > 100:
        return "PHYSICAL_RH_OUT_OF_BOUNDS"
    if rh_era < 0 or rh_era > 100:
        return "ERA_RH_OUT_OF_BOUNDS"
    if not np.isfinite(t_qc) or int(t_qc) != 0:
        return "TOWER_T_NOT_QC0_INDEPENDENT_HOLD"
    difference=float(rh_mds-rh_era)
    if rh_mds<25 and rh_era>=35 and difference<=-MAX_DELTA:
        return "SEVERE_DRY_DISAGREEMENT"
    if difference<=-MAX_DELTA:
        return "LARGE_DRY_DIFFERENCE"
    if difference>=MAX_DELTA:
        return "LARGE_MOIST_DIFFERENCE"
    return "LOWER_DISCREPANCY_NOT_VALIDATION"

def suspicious(k):
    return k in ("PHYSICAL_RH_OUT_OF_BOUNDS","SEVERE_DRY_DISAGREEMENT")

def selftest():
    assert classify(-0.2,50,0)=="PHYSICAL_RH_OUT_OF_BOUNDS"
    assert classify(5,60,0)=="SEVERE_DRY_DISAGREEMENT"
    assert classify(48,40,0)=="LOWER_DISCREPANCY_NOT_VALIDATION"
    assert classify(6,66,1)=="TOWER_T_NOT_QC0_INDEPENDENT_HOLD"
    assert classify(80,40,0)=="LARGE_MOIST_DIFFERENCE"
    assert classify(100.1,55,0)=="PHYSICAL_RH_OUT_OF_BOUNDS"
    assert classify(np.nan,55,0)=="NONFINITE_SOURCE_OR_ERA"
    assert pd.Timestamp("2011-10-17 23:30")+HALF_HOUR==pd.Timestamp("2011-10-18 00:00")
    print("STAGE12AS SELF-TEST PASS | disjoint QC1 subepisode triage; no writes",flush=True)

def pinned():
    a=json.loads(safe(AR/"stage12ar_five_original_QC1_runs_SHA_receipt.json").read_text())
    if not (a.get("version")==
        "batch03-stage12ar-v1-20261026-Kon-five-full-QC1-runs-original-MDS-ERA"
        and a.get("full_native_QC1_runs")==5
        and a.get("full_source_QC1_halfhours")==436
        and a.get("source_QC1_MDS_selected_neighbor_replacements_unapproved")==31
        and a.get("stage12an_centers_research_unapproved")==48
        and a.get("seven_events_still_held") is True
        and a.get("two_special_temperature_holds_protected") is True
        and a.get("operator_approval") is False
        and a.get("Postv5_approved") is False
        and a.get("DATM_ready") is False
        and a.get("spinup_authorized") is False
        and a.get("upstream_signed_stage12aq_SHA256")==sha(
          AQ/"stage12aq_QC1_QC0_ERA_skill_SHA_receipt.json")):
        raise ValueError("Stage12ar original signed evidence or science HOLD altered")
    for name in (FULL,RUNS,MARK):
        if a.get("output_SHA256",{}).get(name)!=sha(AR/name):
            raise ValueError("Stage12ar output changed or unsigned: "+name)
    return a

def audit():
    pinned()
    x=pd.read_csv(safe(AR/FULL),dtype={"native_key":str},low_memory=False)
    r=pd.read_csv(safe(AR/RUNS),dtype={"source_run_begin":str,"source_run_end":str},
                  low_memory=False)
    required={
      "run_id","native_key","original_VPD_F_QC","original_TA_F_QC",
      "original_QC1_MDS_derived_RH_pct","original_ERA_derived_RH_pct",
      "original_VPD_F_matches_VPD_F_MDS",
      "is_among_31_stage12an_finite_neighbor_proposals"
    }
    if not required.issubset(x.columns):
        raise ValueError("Original full 436-row Stage12ar classification schema changed")
    if len(x)!=436 or len(r)!=5 or x.native_key.duplicated().any() or \
            set(x.native_key)&KEEP:
        raise ValueError("Full original five QC1-source audit identity changed")
    if not x.original_VPD_F_QC.eq(1).all():
        raise ValueError("Not all 436 original source RH derived from source VPD QC1")
    if not x.original_VPD_F_matches_VPD_F_MDS.astype(str).str.lower().eq("true").all():
        raise ValueError("Original source VPD_F != native MDS reference")
    proposal=x.is_among_31_stage12an_finite_neighbor_proposals.astype(str).str.lower().eq("true")
    if int(proposal.sum())!=31:
        raise ValueError("31 signed source QC1 neighbor proposals lost")
    x["timestamp"]=pd.to_datetime(x.native_key,format="%Y%m%d%H%M",errors="raise")
    if len(set(x.run_id))!=5 or not set(x.run_id)==set(r.run_id):
        raise ValueError("Original five-run membership changed")
    x=x.sort_values(["run_id","timestamp"]).reset_index(drop=True)
    r=r.sort_values("run_id").reset_index(drop=True)
    x["source_rh_pct"]=pd.to_numeric(x.original_QC1_MDS_derived_RH_pct,errors="coerce")
    x["era_rh_pct"]=pd.to_numeric(x.original_ERA_derived_RH_pct,errors="coerce")
    x["tower_t_qc"]=pd.to_numeric(x.original_TA_F_QC,errors="coerce")
    x["difference_original_minus_ERA_RH_pp"]=x.source_rh_pct-x.era_rh_pct
    x["is_one_of_31_existing_value_change_proposals"]=(
        x.is_among_31_stage12an_finite_neighbor_proposals.astype(str).str.lower().eq("true"))
    x["exploratory_review_class"]=[
        classify(float(a),float(b),float(c))
        for a,b,c in zip(x.source_rh_pct,x.era_rh_pct,x.tower_t_qc)]
    x["candidate_relevance_flag"]=x.exploratory_review_class.apply(suspicious)
    x["operator_approval"]=False

    run_tables=[]
    intervals=[]
    for source_run_id, rows in x.groupby("run_id",sort=True):
        rr=r.loc[r.run_id.eq(source_run_id)]
        if len(rr)!=1:
            raise ValueError("Source run id duplicated in science summary")
        info=rr.iloc[0]
        interval=pd.date_range(pd.to_datetime(info.source_run_begin,format="%Y%m%d%H%M"),
          pd.to_datetime(info.source_run_end,format="%Y%m%d%H%M"),freq="30min")
        if len(interval)!=len(rows) or len(interval)!=int(info.original_run_halfhours) or \
                not (rows.timestamp.to_numpy()==interval.to_numpy()).all():
            raise ValueError("Original 30-minute source run missing or reordered")
        selected=rows.is_one_of_31_existing_value_change_proposals
        suspicious_rows=rows.candidate_relevance_flag
        ref_p90=float(info.QC0_14day_regime_obs_minus_ERA_RH_abs_P90_pp)
        large_discrepancy=rows.difference_original_minus_ERA_RH_pp.abs()
        count_exceed=int((selected & large_discrepancy.gt(ref_p90)).sum()) \
            if np.isfinite(ref_p90) else -1
        if count_exceed!=int(info.selected_neighbors_abs_MDS_minus_ERA_RH_gt_local_QC0_P90_N):
            raise ValueError("Selected 31 neighbor QC0 reference diagnostic drifted")
        invalid=int(rows.exploratory_review_class.eq("PHYSICAL_RH_OUT_OF_BOUNDS").sum())
        if invalid != int(info.full_run_original_RH_lt0_N)+int(info.full_run_original_RH_gt100_N):
            raise ValueError("Original physically impossible RH source counts changed")
        run_tables.append({
            "run_id":int(source_run_id),
            "run_begin":info.source_run_begin,
            "run_end":info.source_run_end,
            "native_halfhours":len(rows),
            "selected_original_QC1_neighbors":int(selected.sum()),
            "original_mds_RH_invalid_lt0_or_gt100_N":invalid,
            "source_T_QC0_N":int(rows.tower_t_qc.eq(0).sum()),
            "severe_dry_original_vs_ERA_QC0_T_N":int(rows.exploratory_review_class.eq(
              "SEVERE_DRY_DISAGREEMENT").sum()),
            "large_dry_original_vs_ERA_QC0_T_N":int(rows.exploratory_review_class.eq(
              "LARGE_DRY_DIFFERENCE").sum()),
            "large_moist_original_vs_ERA_QC0_T_N":int(rows.exploratory_review_class.eq(
              "LARGE_MOIST_DIFFERENCE").sum()),
            "not_QC0_source_T_and_physical_original_RH_N":int(rows.exploratory_review_class.eq(
              "TOWER_T_NOT_QC0_INDEPENDENT_HOLD").sum()),
            "suspicious_exploratory_N":int(suspicious_rows.sum()),
            "suspicious_fraction_percent":round(100*float(suspicious_rows.mean()),4),
            "selected31_flagged_in_run_N":int((selected & suspicious_rows).sum()),
            "selected31_unflagged_in_run_N":int((selected & ~suspicious_rows).sum()),
            "local_QC0_comparator_N":int(
                info.QC0_14day_regime_Twithin5C_original_tower_N),
            "local_QC0_reference_RH_abs_P90_pp":ref_p90,
            "selected31_abs_MDS_ERA_RH_gt_local_QC0_P90_N":count_exceed,
            "operator_approved":False})
        active=False
        begin_idx=0
        arr=rows.reset_index(drop=True)
        for j in range(len(arr)+1):
            is_act=(j<len(arr) and bool(arr.candidate_relevance_flag.iloc[j]))
            if is_act and not active:
                begin_idx=j
                active=True
            if active and not is_act:
                seg=arr.iloc[begin_idx:j]
                intervals.append({
                    "run_id":int(source_run_id),
                    "first_native_key":str(seg.native_key.iloc[0]),
                    "last_native_key":str(seg.native_key.iloc[-1]),
                    "consecutive_native_halfhours":len(seg),
                    "duration_hours":len(seg)/2,
                    "physical_invalid_RH_N":int(seg.exploratory_review_class.eq(
                      "PHYSICAL_RH_OUT_OF_BOUNDS").sum()),
                    "severe_dry_QC0_T_N":int(seg.exploratory_review_class.eq(
                      "SEVERE_DRY_DISAGREEMENT").sum()),
                    "source_T_not_QC0_N":int((~seg.tower_t_qc.eq(0)).sum()),
                    "source_median_original_RH_pct":float(seg.source_rh_pct.median()),
                    "source_median_ERA_RH_pct":float(seg.era_rh_pct.median()),
                    "selected_31_neighbor_proposals_N":int(
                      seg.is_one_of_31_existing_value_change_proposals.sum()),
                    "candidate_not_approved":True,
                })
                active=False
    five=pd.DataFrame(run_tables)
    segments=pd.DataFrame(intervals)
    selected=x.loc[x.is_one_of_31_existing_value_change_proposals].copy()
    if (len(five)!=5 or len(selected)!=31 or len(x)!=436 or
         int(five.selected_original_QC1_neighbors.sum())!=31 or
         int(five.original_mds_RH_invalid_lt0_or_gt100_N.sum())!=37 or
         int(five.selected31_flagged_in_run_N.sum()+five.selected31_unflagged_in_run_N.sum())!=31):
        raise ValueError("Original Stage12ar five-run QC1 source scientific invariants changed")
    if len(segments) and sum(segments.consecutive_native_halfhours)!=int(
          five.suspicious_exploratory_N.sum()):
        raise ValueError("Continuous anomaly candidate segmentation incomplete")
    return x.drop(columns="timestamp"),five,segments,selected.drop(columns="timestamp")

def main():
    p=argparse.ArgumentParser()
    grp=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):
        grp.add_argument("--"+opt,action="store_true")
    args=p.parse_args()
    print("STAGE12AS FIVE ORIGINAL QC1/MDS FULL-RUN SUBEPISODE AUDIT | "+V,flush=True)
    selftest()
    if args.self_test:return
    allrows,five,segments,selected=audit()
    print("\n======== FIVE QC1 RUN REVIEW CATEGORIES ========",flush=True)
    print(five.to_string(index=False),flush=True)
    print("\n======== SCIENCE-ONLY CONTIGUOUS SUSPECT SUBEPISODES ========",flush=True)
    print(segments.to_string(index=False),flush=True)
    print("\n======== 31 ORIGINAL FINITE NEIGHBOR EDIT PROPOSALS ========",flush=True)
    print(selected[["run_id","native_key","original_TA_F_QC","source_rh_pct",
       "era_rh_pct","difference_original_minus_ERA_RH_pp",
       "exploratory_review_class","candidate_relevance_flag"]].to_string(index=False),flush=True)
    print("STAGE12AS FULL_NATIVE_ROWS 436 FIVE_QC1_RUNS 5 ORIGINAL_FINITE_NEIGHBORS 31",
          "SOURCE_RH_INVALID 37 ORIGINAL_MISSING_CENTERS_UNAPPROVED 48",
          "7_BLOCKED_EVENTS+2_SPECIAL_T_HOLDS_RETAINED; NO FORCING OR MODEL APPROVAL",flush=True)
    if args.check:
        print("STAGE12AS CHECK ONLY | NO WRITES",flush=True)
        return
    folder=ROOT/"reports"/("stage12as_Kon_QC1_subepisode_science_only_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    outputs={
       "436_original_QC1_MDS_native_halfhours_exploratory_review_classes.csv":allrows,
       "five_full_QC1_run_exploratory_review_summary.csv":five,
       "original_QC1_MDS_contiguous_anomaly_subepisodes.csv":segments,
       "31_stage12an_neighbor_proposals_with_full_run_context.csv":selected
    }
    for name,df in outputs.items():
        df.to_csv(folder/name,index=False)
    note="SCIENCE_ONLY_48_CENTER_31_FINITE_HOLD_NO_POSTV5_DATM"
    (folder/note).write_text(
       "All labels in this report are exploratory evidence categories, not truth "
       "or operator approvals. A non-QC0 source cannot be independently verified "
       "from its own MDS value. Full five QC1 runs are NOT uniformly dry. "
       "Two original source temperature special events, seven prior failed "
       "episodes, 48 missing humidity centers and all 31 original finite QC1 "
       "neighbors remain operationally held/unapproved. Original tower files, "
       "forcing, clock, existing trials, DATM, CIME, spinup and Slurm unchanged.\n")
    hashes={name:sha(folder/name) for name in [*outputs,note]}
    (folder/"stage12as_original_QC1_subepisodes_SHA_receipt.json").write_text(
       json.dumps({
        "version":V,
        "stage12ar_signed_receipt_SHA256":sha(
            AR/"stage12ar_five_original_QC1_runs_SHA_receipt.json"),
        "original_source_full_QC1_runs":5,
        "original_source_halfhours_audited":436,
        "source_negative_or_gt100_RH_N":37,
        "stage12an_QC1_neighbors_unapproved":31,
        "stage12an_missing_centers_unapproved":48,
        "seven_original_blocked_events_preserved":True,
        "two_special_source_T_holds_preserved":True,
        "operator_approved":False,"Postv5_approved":False,
        "DATM_ready":False,"spinup_authorized":False,
        "output_SHA256":hashes},indent=2)+"\n")
    print("STAGE12AS SIGNED SCIENCE REPORT DIR:",folder,flush=True)
    print("NO ORIGINAL, PRIOR SCIENCE, SOURCE CLOCK, FORCING, DATM OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AS STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

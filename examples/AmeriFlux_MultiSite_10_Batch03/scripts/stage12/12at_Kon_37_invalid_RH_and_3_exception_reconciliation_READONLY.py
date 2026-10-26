#!/usr/bin/env python3
"""Stage12at — reconcile 37 source-invalid RH rows and three exception
neighbor replacements against actual signed Stage12ak/Stage12an input rows.

This is a strict, source-native, research-only audit. We do NOT assume the
37 invalid original FLUXMET QC1/MDS rows remain invalid in the selected
forcing: independently check their Stage12ak and Stage12an values.
Group Stage12an's 19 numerical PASS / 7 HOLD episodes by the source
provenance of their 31 finite-neighbor edit proposals. Identify precisely
the 3 original finite QC1 neighbor proposals that Stage12as did NOT flag.
No repair, no approve, no clock shifts, no CIME/DATM/Slurm/model edits.

--self-test: synthetic, no source reads/writes
--check: pinned signed original files and in-memory reconciliation only
--run: the same + isolated signed REPORTS ONLY (no forcing writes)
"""
import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

V="batch03-stage12at-v1-20261026-Kon-37-invalid-3-exceptions-reconcile"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AS=R/"reports/stage12as_Kon_QC1_subepisode_science_only_20261026T115015Z_a020a606"
AN=R/"science_trials/stage12an_Kon_55_center_connected_ERA_RH_science_only_20261026T040913Z_277a0364"
AK=R/"science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7"
AS_FULL="436_original_QC1_MDS_native_halfhours_exploratory_review_classes.csv"
AS_SUM="five_full_QC1_run_exploratory_review_summary.csv"
AS_INTERVAL="original_QC1_MDS_contiguous_anomaly_subepisodes.csv"
AS_SELECTED="31_stage12an_neighbor_proposals_with_full_run_context.csv"
AS_HOLD="SCIENCE_ONLY_48_CENTER_31_FINITE_HOLD_NO_POSTV5_DATM"
AN_INPUT="US-Kon_STAGE12AN_ERA_RH_CONNECTED_EPISODE_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv"
AN_PATCH="research_candidate_native_QC1_QC2_humidity_event_changes.csv"
AN_EVENT="connected_episode_pass_and_source_hold_reasons.csv"
AK_INPUT="US-Kon_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
SPECIAL={"201102220900","201109291830"}

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing/changed signed source or symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def native(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def asbool(series):
    return series.astype(str).str.strip().str.lower().eq("true")

def satwater(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        z=6.112*np.exp(17.67*t/(t+243.5))
    return np.where((t>-85)&(t<55),z,np.nan)

def rh(t,v):
    with np.errstate(divide="ignore",invalid="ignore"):
        return 100*(1-np.asarray(v,dtype=float)/satwater(t))

def verdict(v,q,r):
    if not np.isfinite(v) or not np.isfinite(q):
        return "RETAINED_HUMIDITY_MISSING"
    if not np.isfinite(r) or r<0 or r>100 or not (0<q<0.08):
        return "RESEARCH_SELECTED_PHYSICS_REVIEW_REQUIRED"
    return "RESEARCH_SELECTED_FINITE_PHYSICAL_NOT_APPROVED"

def selftest():
    assert verdict(np.nan,np.nan,np.nan)=="RETAINED_HUMIDITY_MISSING"
    assert verdict(8.0,0.005,-2)=="RESEARCH_SELECTED_PHYSICS_REVIEW_REQUIRED"
    assert verdict(8.0,0.005,40)=="RESEARCH_SELECTED_FINITE_PHYSICAL_NOT_APPROVED"
    assert abs(float(rh(20,0))-100)<1e-10
    assert native(pd.Series(["2011-10-18 01:30:00"])).iloc[0]=="201110180130"
    assert len(SPECIAL)==2
    print("STAGE12AT SELF-TEST PASS | source-invalid-vs-selected + event exception gates; NO WRITES",flush=True)

def verified():
    s=json.loads(safe(AS/"stage12as_original_QC1_subepisodes_SHA_receipt.json").read_text())
    n=json.loads(safe(AN/"stage12an_research_only_55_source_event_SHA_receipt.json").read_text())
    k=json.loads(safe(AK/"stage12ak_research_proposal_SHA_receipt.json").read_text())
    if not (s.get("version")=="batch03-stage12as-v1-20261026-Kon-complete-QC1-scoped-subepisodes"
      and s.get("original_source_full_QC1_runs")==5
      and s.get("original_source_halfhours_audited")==436
      and s.get("source_negative_or_gt100_RH_N")==37
      and s.get("stage12an_QC1_neighbors_unapproved")==31
      and s.get("stage12an_missing_centers_unapproved")==48
      and s.get("seven_original_blocked_events_preserved") is True
      and s.get("two_special_source_T_holds_preserved") is True
      and s.get("operator_approved") is False
      and s.get("DATM_ready") is False and s.get("spinup_authorized") is False
      and n.get("research_center_pass_numerical")==48
      and n.get("original_finite_QC1_QC2_neighbor_source_humidity_changes")==31
      and n.get("numerical_event_trial_PASSED")==19
      and n.get("numerical_event_trial_HELD")==7
      and set(n.get("source_t_disagreement_hard_holds",[]))==SPECIAL
      and n.get("operator_humidity_approval") is False
      and n.get("DATM_ready") is False and n.get("spinup_authorized") is False):
        raise ValueError("Historical Stage12as/an hold receipts or exact 436/79 science gates changed")
    for f in (AS_FULL,AS_SUM,AS_INTERVAL,AS_SELECTED,AS_HOLD):
        if s.get("output_SHA256",{}).get(f)!=sha(AS/f):
            raise ValueError("Stage12as signed science input changed: "+f)
    for f in (AN_INPUT,AN_PATCH,AN_EVENT):
        if n.get("output_SHA256",{}).get(f)!=sha(AN/f):
            raise ValueError("Stage12an signed trial changed: "+f)
    if k.get("output_SHA256",{}).get(AK_INPUT)!=sha(AK/AK_INPUT):
        raise ValueError("Stage12ak signed trial input changed")
    return s,n,k

def audit():
    verified()
    full=pd.read_csv(safe(AS/AS_FULL),dtype={"native_key":str},low_memory=False)
    selected=pd.read_csv(safe(AS/AS_SELECTED),dtype={"native_key":str},low_memory=False)
    patch=pd.read_csv(safe(AN/AN_PATCH),dtype={"native_key":str},low_memory=False)
    events=pd.read_csv(safe(AN/AN_EVENT),dtype={"seed_begin":str,"seed_end":str},low_memory=False)
    if len(full)!=436 or len(selected)!=31 or full.native_key.duplicated().any() or \
       len(events)!=26 or set(full.native_key)&SPECIAL or \
       not asbool(full.original_VPD_F_matches_VPD_F_MDS).all():
        raise ValueError("Original QC1 436 rows/31 selected and 26 events changed")
    invalid=full.loc[full.exploratory_review_class.eq("PHYSICAL_RH_OUT_OF_BOUNDS")].copy()
    if len(invalid)!=37 or int(asbool(selected.candidate_relevance_flag).sum())!=28:
        raise ValueError("Exactly 37 physically invalid source RH and 28/31 flagged neighbor records required")
    nonflag=selected.loc[~asbool(selected.candidate_relevance_flag)].copy()
    expected={"201104051030","201110170230","201110172330"}
    if set(nonflag.native_key)!=expected:
        raise ValueError("Three special unflagged source-neighbor timestamps changed")
    passes=patch.loc[asbool(patch.episode_numerical_pass)].copy()
    if len(passes)!=79 or passes.native_key.duplicated().any():
        raise ValueError("Stage12an 79 candidate proposal lineage changed")
    is_neighbor=passes.kind.eq("NEIGHBOR_ORIGINAL_VPD_QC1_QC2_PROPOSAL")
    neighbor=passes.loc[is_neighbor].copy()
    center=passes.loc[~is_neighbor].copy()
    if len(neighbor)!=31 or len(center)!=48 or \
       not center.kind.eq("ORIGINAL_55_VPD_HELD_CENTER").all() or \
       set(neighbor.native_key)!=set(selected.native_key) or \
       set(passes.native_key)&SPECIAL:
        raise ValueError("Stage12an original 48 center + 31 finite neighbor identity changed")
    neighbor=neighbor.merge(
       selected[["native_key","run_id","source_rh_pct","era_rh_pct",
                  "exploratory_review_class","candidate_relevance_flag",
                  "original_TA_F_QC"]],
       how="left",on="native_key",validate="one_to_one")
    if neighbor.exploratory_review_class.isna().any():
        raise ValueError("Unmapped signed source neighbor")
    # Check signed original source and current research branch row-by-row,
    # do not infer that original RH pathology survives in selected forcing.
    base=pd.read_csv(safe(AK/AK_INPUT),dtype={"time":str},
      usecols=["time","TA_USE","VPD_USE","QBOT"],low_memory=False)
    trial=pd.read_csv(safe(AN/AN_INPUT),dtype={"time":str},
      usecols=["time","TA_USE","VPD_USE","QBOT"],low_memory=False)
    if len(base)!=280320 or len(trial)!=280320:
        raise ValueError("Original NOLEAP Kon 280320 native rows changed")
    bkeys=native(base.time); tkeys=native(trial.time)
    if bkeys.duplicated().any() or not bkeys.equals(tkeys):
        raise ValueError("Original time source clock reordered")
    if not np.array_equal(base.TA_USE.to_numpy(dtype=float),
                          trial.TA_USE.to_numpy(dtype=float),equal_nan=True):
        raise ValueError("Protected TA_USE source changed in humidity research")
    ix=pd.Series(np.arange(len(bkeys)),index=bkeys.to_numpy())
    if not set(invalid.native_key).issubset(set(ix.index)):
        raise ValueError("Original 37 source-invalid rows missing from research clock")
    # Verify all 79 proposed edits are the only VPD/QBOT differences between branches.
    orig_v=base.VPD_USE.to_numpy(dtype=float)
    targ_v=trial.VPD_USE.to_numpy(dtype=float)
    orig_q=base.QBOT.to_numpy(dtype=float)
    targ_q=trial.QBOT.to_numpy(dtype=float)
    differs=(~np.isclose(orig_v,targ_v,rtol=0,atol=1e-10,equal_nan=True) |
             ~np.isclose(orig_q,targ_q,rtol=0,atol=1e-12,equal_nan=True))
    changed=set(bkeys.iloc[np.flatnonzero(differs)])
    if changed!=set(passes.native_key):
        raise ValueError("Signed trial changes not exactly the 79 research proposals")
    output=[]
    for row in invalid.itertuples(index=False):
        index=int(ix.loc[row.native_key])
        b_t=float(base.TA_USE.iat[index])
        a_t=float(trial.TA_USE.iat[index])
        b_v=float(orig_v[index]);a_v=float(targ_v[index])
        b_q=float(orig_q[index]);a_q=float(targ_q[index])
        b_r=float(rh(b_t,b_v));a_r=float(rh(a_t,a_v))
        output.append({
          "run_id":int(row.run_id),"native_key":row.native_key,
          "original_source_RH_pct":float(row.source_rh_pct),
          "original_ERA_RH_pct":float(row.era_rh_pct),
          "source_T_QC":float(row.original_TA_F_QC),
          "one_of_original_31_finite_neighbor_proposals":bool(
            str(row.is_one_of_31_existing_value_change_proposals).lower()=="true"),
          "Stage12ak_original_selected_T_C":b_t,
          "Stage12ak_research_selected_VPD_hPa":b_v,
          "Stage12ak_research_selected_QBOT_kgkg":b_q,
          "Stage12ak_selected_RH_pct":b_r,
          "Stage12ak_source_status":verdict(b_v,b_q,b_r),
          "Stage12an_research_selected_VPD_hPa":a_v,
          "Stage12an_research_selected_QBOT_kgkg":a_q,
          "Stage12an_selected_RH_pct":a_r,
          "Stage12an_source_status":verdict(a_v,a_q,a_r),
          "Stage12an_numerically_changed_this_row":row.native_key in changed,
          "operator_approved":False})
    invalid_report=pd.DataFrame(output).sort_values(["run_id","native_key"])
    # Site-wide 19 event numerical successes remain exploratory, and any
    # unflagged/TA-QC1 neighbor prohibits unrestricted acceptance.
    byepisode=[]
    for obj in events.itertuples(index=False):
        n=neighbor.loc[neighbor.episode.eq(obj.episode)]
        c=center.loc[center.episode.eq(obj.episode)]
        passed=str(obj.research_numerical_pass).lower()=="true"
        flagged=int(asbool(n.candidate_relevance_flag).sum()) if len(n) else 0
        nonflagged=len(n)-flagged
        if passed and len(c)!=int(obj.seed_original_55_target_count):
            raise ValueError("Signed event center count altered")
        if not passed and len(c):
            raise ValueError("Blocked episode got new research releases")
        if not passed:
            label="HOLD_PREVIOUS_BOUNDARY_OR_SOURCE"
        elif nonflagged:
            label="HOLD_FINITE_NEIGHBOR_INDEPENDENT_EVIDENCE"
        elif len(n):
            label="REVIEW_FLAGGED_QC1_EVENT_NOT_APPROVED"
        else:
            label="REVIEW_CENTER_ONLY_NOT_APPROVED"
        byepisode.append({
          "episode":int(obj.episode),"seed_begin":obj.seed_begin,"seed_end":obj.seed_end,
          "Stage12an_numerical_pass":bool(passed),
          "Stage12an_missing_center_candidate_count":len(c),
          "Stage12an_original_finite_neighbors_count":len(n),
          "original_finite_neighbor_exploratory_flagged":flagged,
          "original_finite_neighbor_unflagged":nonflagged,
          "selected_original_QC1_T_QC1_records":int(n.original_TA_F_QC.eq(1).sum()),
          "strict_science_review_route":label,
          "operator_approved":False,
          "Postv5_approved":False,
          "DATM_ready":False})
    event_report=pd.DataFrame(byepisode)
    if (len(invalid_report)!=37 or len(event_report)!=26 or
        int(event_report.Stage12an_original_finite_neighbors_count.sum())!=31 or
        int(event_report.Stage12an_missing_center_candidate_count.sum())!=48 or
        int(event_report.original_finite_neighbor_unflagged.sum())!=3 or
        int((~event_report.Stage12an_numerical_pass).sum())!=7):
        raise ValueError("Exactly 37 physical invalid, 3 exceptions, 48/31 proposals, 7 HOLS required")
    return invalid_report,nonflag,neighbor,event_report

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","run"):g.add_argument("--"+k,action="store_true")
    args=p.parse_args()
    print("STAGE12AT Kon 37 ORIGINAL INVALID RH AND 3 UNFLAGGED FINITE PATCHES | "+V,flush=True)
    selftest()
    if args.self_test:return
    invalid,exceptions,neighbors,events=audit()
    print("\n===== 37 ORIGINAL IMPOSSIBLE QC1/MDS RH ROWS vs SELECTED RESEARCH BRANCHES =====",flush=True)
    print(invalid.to_string(index=False),flush=True)
    print("\n===== ORIGINAL 3 UNFLAGGED 31-NEIGHBOR EXCEPTIONS =====",flush=True)
    print(exceptions[["native_key","run_id","source_rh_pct","era_rh_pct",
      "original_TA_F_QC","exploratory_review_class"]].to_string(index=False),flush=True)
    print("\n===== ORIGINAL 26 CONNECTED EVENT SOURCE-EVIDENCE REVIEW ROUTES =====",flush=True)
    print(events.to_string(index=False),flush=True)
    print("STAGE12AT SUMMARY 37_SOURCE_IMPOSSIBLE_RH; 3_UNFLAGGED_NEIGHBOR_PROPOSALS",
      "48_MISSING_CENTERS_31_FINITE_NEIGHBORS_UNAPPROVED;",
      "7_EVENTS_HELD; 2_SPECIAL_T_SOURCE_HOLDS; NO FORCING APPROVAL",flush=True)
    if args.check:
        print("STAGE12AT CHECK ONLY | ZERO WRITES",flush=True)
        return
    folder=R/"reports"/("stage12at_Kon_37_invalid_source_RH_three_exceptions_science_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
       "_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    tabs={
      "37_original_QC1_MDS_invalid_RH_vs_selected_stage12ak_stage12an.csv":invalid,
      "three_unflagged_original_QC1_neighbor_exceptions.csv":exceptions,
      "31_original_finite_neighbor_episode_source_evidence.csv":neighbors,
      "26_original_connected_episode_strict_science_review_routes.csv":events}
    for name,df in tabs.items():df.to_csv(folder/name,index=False)
    note="SCIENTIFIC_HOLD_ALL_79_NO_POSTV5_DATM"
    (folder/note).write_text(
      "READ-ONLY scientific evidence reconciliation. Original 37 physically "
      "impossible QC1/MDS-derived RH rows are not assumed to remain in selected "
      "forcing without checking actual Stage12ak/an VPD and QBOT. Neither original "
      "QC1 MDS nor native ERA is measured independent truth. The 31 finite "
      "replacement proposals and 48 missing center candidates, seven blocked "
      "events and two special temperature-hold native timestamps remain "
      "scientifically unapproved. Never run trial CSV as DATM input. "
      "No source, native clock, forcing, model, CIME or Slurm writes.\n")
    digests={name:sha(folder/name) for name in [*tabs,note]}
    (folder/"stage12at_reconciliation_SHA_receipt.json").write_text(
      json.dumps({
        "version":V,
        "signed_stage12as_SHA256":sha(
           AS/"stage12as_original_QC1_subepisodes_SHA_receipt.json"),
        "signed_stage12an_SHA256":sha(
           AN/"stage12an_research_only_55_source_event_SHA_receipt.json"),
        "source_invalid_RH_rows":37,
        "original_finite_neighbor_unflagged_exceptions":3,
        "Stage12an_missing_centers_proposals_unapproved":48,
        "Stage12an_finite_QC1_neighbor_proposals_unapproved":31,
        "seven_blocked_events_preserved":True,
        "two_source_T_special_holds_preserved":True,
        "operator_approved":False,"Postv5_approved":False,
        "DATM_ready":False,"spinup_authorized":False,
        "output_SHA256":digests},indent=2)+"\n")
    print("STAGE12AT SIGNED SCIENCE REPORT DIR:",folder,flush=True)
    print("NO ORIGINAL SOURCE, CLOCK, PREVIOUS TRIAL, DATM OR MODEL INPUT WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AT STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

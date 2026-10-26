#!/usr/bin/env python3
"""Batch03 Stage13b: print all 6 original source-QC0 edited values and full
actual Stage07 manual-review workload for three SHA-pinned numeric sites.

Do not ask the operator to review thousands of physical saturation readings.
Review EXACT original event records and the actual original manual_review
ledger instead. No changes/approval/submit; --check is strictly read-only;
--run creates one isolated compact decision package for science sign-off.

This does NOT imply that a numerically complete forcing is Post-v5,
source-clock, terrain, PFT, ZBOT, DATM or spinup ready. US-NC2's subsequent
Stage11 time/ERA concerns remain separate.
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
sys.dont_write_bytecode=True

VER="batch03-stage13b-v2-20261026-empty-manual-ledger-safe"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE13A=ROOT/"reports/stage13a_Batch03_NINE_SITE_FORCING_ADMISSION_20261026T163725Z_cc70d4c8"
SITE_COUNTS={"US-MOz":1,"US-Mpj":1,"US-NC2":4}
VARS={"TA_F","VPD_F","PA_F","SW_IN_F","LW_IN_F","WS_F","P_F"}

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Original SHA source absent or symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):
            h.update(x)
    return h.hexdigest()

def source_keys(frame):
    """Stable native event keys, including pandas EMPTY manual_review.csv.

    DataFrame.agg(axis=1) returns a DataFrame, not a Series, on empty frames
    in some pandas versions. Do not use it for any site review ledger.
    """
    if not {"time","variable"}.issubset(frame.columns):
        raise RuntimeError("Original manual/event key schema missing")
    return pd.Series(
        [str(t)+"|"+str(v) for t,v in zip(frame["time"],frame["variable"])],
        index=frame.index,dtype="object")

def selftest():
    assert sum(SITE_COUNTS.values())==6 and len(SITE_COUNTS)==3
    assert "VPD_F" in VARS
    empty=pd.DataFrame(columns=["time","variable","reason"])
    assert source_keys(empty).empty
    one=pd.DataFrame({"time":["2020-01-01 12:30:00"],"variable":["VPD_F"]})
    assert source_keys(one).tolist()==["2020-01-01 12:30:00|VPD_F"]
    # Preserve source row index for selected QC0 event membership.
    with_index=one.set_axis([17],axis=0)
    assert source_keys(with_index).index.tolist()==[17]
    print("STAGE13B SELF-TEST PASS | original QC0 event + manual ledgers, no source writes",flush=True)

def recorded(sha_manifest,path):
    rel=str(path.relative_to(STAGE07))
    if sha_manifest.get(rel)!=sha(path):
        raise RuntimeError("Signed Stage07 candidate output changed: "+rel)
    return path

def read():
    a=ROOT/"reports"
    old=pd.read_csv(safe(STAGE13A/"Batch03_nine_site_forcing_admission_readonly.csv"))
    if len(old)!=9 or old.site.duplicated().any():
        raise RuntimeError("Stage13a original 9-site report missing/duplicated")
    for site in SITE_COUNTS:
        row=old.loc[old.site.eq(site)]
        if len(row)!=1 or row.iloc[0].numeric_selected_candidate_screen!="CURRENT_NUMERIC_FIELDS_PASS_ONLY" or \
            row.iloc[0].DATM_ready not in (False,0):
            raise RuntimeError("Three numerically passed but unapproved Stage13a science results changed: "+site)
    sha_manifest=json.loads(safe(STAGE07/"output_sha256.json").read_text())
    inputcheck=json.loads(safe(STAGE07/"input_preservation_check.json").read_text())
    if inputcheck.get("unchanged") is not True or inputcheck.get("changed_inputs")!=[]:
        raise RuntimeError("Stage07 original source input preservation no longer valid")
    totals=[]
    allqc0=[]
    allreasons=[]
    allmanual=[]
    for site,want in SITE_COUNTS.items():
        qc=STAGE07/site/"forcing"/"qc_v5"
        events=pd.read_csv(recorded(sha_manifest,qc/(site+"_replacement_events.csv")),
                           dtype={"time":str},low_memory=False)
        manual=pd.read_csv(recorded(sha_manifest,qc/(site+"_manual_review.csv")),
                           dtype={"time":str},low_memory=False)
        independent=json.loads(recorded(
            sha_manifest,qc/(site+"_independent_audit.json")).read_text())
        status=json.loads(recorded(sha_manifest,qc/(site+"_status.json")).read_text())
        if not {"site","time","variable","original_value","final_value","official_qc","reason","final_source"}<=set(events):
            raise RuntimeError("Stage07 event signed schema unexpected "+site)
        if not {"site","time","variable","reason","official_qc"}<=set(manual):
            raise RuntimeError("Stage07 manual-event schema unexpected "+site)
        if independent.get("status")!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED" or \
           independent.get("site")!=site or independent.get("changed_QC0_records")!=want or \
           independent.get("manual_review_records")!=len(manual) or \
           status.get("manual_review_records")!=len(manual) or \
           int(status.get("changes",-1))!=len(events):
            raise RuntimeError("Exact Stage07 three-site historical signed audit changed "+site)
        if not events.site.eq(site).all() or (len(manual)>0 and not manual.site.eq(site).all()):
            raise RuntimeError("Candidate mixed site events "+site)
        selected=events.loc[pd.to_numeric(events.official_qc,errors="coerce").eq(0)].copy()
        if len(selected)!=want or not selected.variable.isin(VARS).all():
            raise RuntimeError("Original QC0 edits count or variable changed "+site)
        manual_keys=set(source_keys(manual).tolist())
        selected["also_in_original_manual_review"]=source_keys(selected).isin(manual_keys)
        for key in ["era_reference","original_value","final_value"]:
            if key in selected:
                selected[key]=pd.to_numeric(selected[key],errors="coerce")
        selected["change_delta"]=selected.final_value-selected.original_value
        selected["operator_decision"]="HOLD_UNTIL_QC0_SOURCE_REVIEW"
        allqc0.append(selected)
        breakdown=manual.groupby(["variable","reason"],dropna=False).size().reset_index(name="manual_records")
        breakdown.insert(0,"site",site)
        allreasons.append(breakdown)
        if len(manual):
            m=manual.copy()
            m["operator_decision"]="NOT_APPROVED_REVIEW_REQUIRED"
            allmanual.append(m)
        totals.append({
          "site":site,
          "number_original_QC0_changes":len(selected),
          "number_QC0_also_in_manual_ledger":int(selected.also_in_original_manual_review.sum()),
          "all_original_replacement_variable_events":len(events),
          "actual_original_manual_review_records":len(manual),
          "distinct_manual_review_reasons":manual.reason.nunique(dropna=False),
          "manual_review_underlying_same_time_variable":len(manual_keys),
          "Stage07_ERA_RH_floor_count":int(independent.get("ERA_RH_floor_records",0)),
          "Stage07_independent_min_RH_pct":float(independent.get("min_RH_pct",float("nan"))),
          "Stage07_Numeric":"PASS_ONLY",
          "additional_provenance_hold":(
               "US-NC2_STAGE11_TIME_AND_ERA2025_SOURCE_HOLD" if site=="US-NC2" else ""),
          "Postv5_approved":False,
          "DATM_ready":False,
          "spinup_authorized":False
        })
    qc0=pd.concat(allqc0,ignore_index=True)
    if len(qc0)!=6:
        raise RuntimeError("Original six QC0 candidates missing")
    # Important safety: no raw/QC0 changes are automatically approved.
    if qc0.operator_decision.ne("HOLD_UNTIL_QC0_SOURCE_REVIEW").any():
        raise RuntimeError("Unexpected original QC0 approval")
    reasons=pd.concat(allreasons,ignore_index=True)
    summary=pd.DataFrame(totals)
    manual=pd.concat(allmanual,ignore_index=True) if allmanual else pd.DataFrame(columns=[
        "site","time","variable","official_qc","reason","operator_decision"])
    return summary,qc0,reasons,manual

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):g.add_argument("--"+opt,action="store_true")
    a=p.parse_args()
    print("STAGE13B FINAL THREE NUMERIC SITES QC0 + MANUAL DECISION PACKAGE | "+VER,flush=True)
    selftest()
    if a.self_test:return
    summ,qc0,reasons,manual=read()
    fields=["site","time","variable","original_value","final_value","change_delta",
            "era_reference","official_qc","final_source","reason",
            "also_in_original_manual_review"]
    print("\n=== EXACT SIX ORIGINAL SOURCE QC0 MODIFICATIONS: HUMAN DECISION ===",flush=True)
    print(qc0.reindex(columns=fields).to_string(index=False),flush=True)
    print("\n=== TRUE ACTUAL ORIGINAL POST-QCV5 MANUAL REVIEW WORKLOAD ===",flush=True)
    print(summ.to_string(index=False),flush=True)
    print("\n=== MANUAL SCIENCE REASON COUNTS (TOP 5 PER SITE) ===",flush=True)
    for site in SITE_COUNTS:
        one=reasons.loc[reasons.site.eq(site)]
        print(site,flush=True)
        if len(one):print(one.nlargest(5,"manual_records").to_string(index=False),flush=True)
        else:print("  NO ORIGINAL MANUAL RECORDS",flush=True)
    print("STAGE13B QC0 approvals=0, source unchanged, three numeric-only site inputs not yet production ready",flush=True)
    if a.check:
        print("STAGE13B CHECK ONLY: NO FILE WRITES",flush=True)
        return
    root=ROOT/"reports"/("stage13b_THREE_NUMERIC_SITES_QC0_AND_MANUAL_DECISIONS_"+
                        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
                        "_"+uuid4().hex[:8])
    root.mkdir(parents=True,exist_ok=False)
    output={
      "THREE_numeric_site_exact_six_original_QC0_edits_TO_DECIDE.csv":qc0,
      "THREE_site_true_manual_review_summary.csv":summ,
      "THREE_site_manual_review_reason_counts.csv":reasons,
      "THREE_site_all_original_manual_review_records_TO_DECIDE.csv":manual}
    for name,frame in output.items():
        frame.to_csv(root/name,index=False)
    note="NO_PRODUCTION_APPROVAL_QC0_OR_MANUAL_HOLDS"
    (root/note).write_text(
       "These six exact original QC0 source modifications are NOT approved. "
       "The full original Stage07 manual review ledger is also NOT approved. "
       "No climate/ERA or source clock overrides, PFT/surface approvals, "
       "height/ZBOT acceptance, DATM configuration, Post-v5 or Slurm "
       "submissions are made by this evidence-only report.\n")
    receipt={
       "version":VER,
       "source_Stage13a_report_SHA256":sha(STAGE13A/"Batch03_nine_site_forcing_admission_readonly.csv"),
       "source_Stage07_output_SHA256_manifest":sha(STAGE07/"output_sha256.json"),
       "qc0_rows":6,"sites":list(SITE_COUNTS),
       "total_manual_ledger_records":len(manual),
       "all_original_QC0_and_manual_science_approved":False,
       "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
       "output_SHA256":{f:sha(root/f) for f in [*output,note]}}
    (root/"stage13b_three_site_decision_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13B ONE-PASS SCIENCE DECISION DIR:",root,flush=True)
    print("ZERO SOURCE, QC-V5, DATM, CASE, SLURM OR MODEL MODIFICATIONS",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13B STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

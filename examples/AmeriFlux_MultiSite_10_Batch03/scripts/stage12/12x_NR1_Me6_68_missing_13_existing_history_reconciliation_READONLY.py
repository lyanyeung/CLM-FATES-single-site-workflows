#!/usr/bin/env python3
"""Stage12x — isolate 68 Stage12g missing original-invalid MDS VPD records
and 13 previously finite Stage12g VPDs flagged by a DIFFERENT Stage12w
hypothetical original-companion ERA-RH source candidate.

Fully source-only: compare sealed Stage12w candidates to existing
Stage12c/d/e/g VPD source states and original D/E/G hold ledgers, inspect
the one Stage12w 'diagnostic pass' but Stage12g-missing row +/-6h.

Stage12w pass != forcing approval. Stage12w proposed companion-ERA RH
values need not equal previously sealed Stage12d/E/G values. Never
overwrite previous finite science shadow or release 86+233 science holds.

--self-test: synthetic partition / ancestry tests, NO filesystem reads.
--check: all original signed evidence SHA + analysis, ZERO file writes.
--run: same checks then NEW separate SHA-receipted REPORT ONLY.
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

VERSION="batch03-stage12x-v1-20261025-68missing-13oldfinite-original-CDEG-source-reasons"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
W=ROOT/"reports/stage12w_355_original_MDS_VPD_companion_ERA_RH_physics_triage_20261025T192422Z_10358cc7"
W_REC="stage12w_355_MDS_ERA_RH_science_report_SHA_receipt.json"
W_ROWS="355_original_QC1_MDS_VPD_ERA_RH_cautionary_candidate_evidence.csv"
STAGES={
  "C":(ROOT/"science_trials/stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e",
       "stage12c_research_shadow_SHA_receipt.json","STAGE12C_NOT_MODEL_READY_NOLEAP"),
  "D":(ROOT/"science_trials/stage12d_six_site_companion_RH_gap_recovery_20261024T121810Z_f1fa4cee",
       "stage12d_research_shadow_SHA_receipt.json","STAGE12D_NOT_MODEL_READY_NOLEAP"),
  "E":(ROOT/"science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97",
       "stage12e_research_only_sha_receipt.json","STAGE12E_INCOMPLETE_NOLEAP"),
  "G":(ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f",
       "stage12g_research_only_sha_receipt.json","STAGE12G_INCOMPLETE_NOLEAP"),
}
LEDGERS={
 "D_hold":("D","remaining_other_humidity_science_holds.csv","hold_reason"),
 "E_hold":("E","remaining_4372_source_second_ERA5Land_holds.csv","science_hold_reason"),
 "G_hold":("G","2810_original_missing_year_source_review_after_stage12g.csv","reason"),
 "D_candidate":("D","guarded_companion_ERA_RH_auto_candidate_timestamps.csv",None),
 "G_candidate":("G","new_ERA5Land_year_source_RH_repair_candidates.csv",None)
}
SITES=("US-Me6","US-NR1")
PASS="DIAGNOSTIC_PHYSICS_AND_AVAILABLE_EDGE_TEST_PASS_NOT_APPROVED"
TEMP="COMPANION_ERA_T_MISMATCH_GT5C"
JUMP="GT4HPA_JUMP_TO_EXISTING_STAGE12G_NEIGHBOR"
EXPECTED={(PASS,True):274,(PASS,False):1,
          (TEMP,True):12,(TEMP,False):32,
          (JUMP,True):1,(JUMP,False):35}

def file(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing or symlinked original SHA evidence: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def floatarray(values):
    x=pd.to_numeric(values,errors="coerce").to_numpy(dtype=float)
    x[~np.isfinite(x)|(x<=-9990)]=np.nan
    return x

def equal(x,y,eps=1e-6):
    if pd.isna(x) or pd.isna(y):
        return pd.isna(x) and pd.isna(y)
    return abs(float(x)-float(y))<=eps

def native_key(t):
    return t.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def verify():
    w=json.loads(file(W/W_REC).read_text())
    if (w.get("version")!="batch03-stage12w-v2-20261025-355-MDS-bad-VPD-ERA-RH-guarded-diagnostics"
        or w.get("source_355_original_invalid_MDS_QC1_preserved") is not True
        or w.get("tower_QC0_T_and_site_P_and_native_clock_unchanged") is not True
        or w.get("original_86_plus_233_science_holds_unchanged") is not True
        or w.get("new_source_or_forcing_repairs")!=0
        or w.get("Postv5_approved")!=0 or w.get("DATM_ready")!=0
        or w.get("spinup_authorized")!=0):
        raise ValueError("Stage12w sealed report science holds changed")
    for name, dig in w["output_SHA256"].items():
        if sha(W/name)!=dig:
            raise ValueError("Stage12w output source evidence SHA changed "+name)
    stages={}
    for k,(root,receipt_name,suffix) in STAGES.items():
        r=json.loads(file(root/receipt_name).read_text())
        if (r.get("Postv5_approved")!=0 or r.get("DATM_ready")!=0
            or r.get("spinup_authorized")!=0
            or r.get("INCOMPLETE_marker_present") is not True):
            raise ValueError("Stage12"+k+" incomplete scientific gate changed")
        file(root/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
        for site in SITES:
            name=f"{site}_{suffix}.csv"
            if sha(root/name)!=r["output_sha256"].get(name):
                raise ValueError("Original SHA-sealed Stage12"+k+" tower shadow edited")
        stages[k]=r
    gdir,gname,_=STAGES["G"]
    if w.get("verified_stage12g_source_receipt_sha256")!=sha(gdir/gname):
        raise ValueError("Stage12w original G report ancestor SHA changed")
    for label,(stage,name,_) in LEDGERS.items():
        root=STAGES[stage][0]
        if sha(root/name)!=stages[stage]["output_sha256"].get(name):
            raise ValueError("Original Stage12"+stage+" hold/candidate ledger SHA changed "+label)
    d=stages["D"];c=stages["C"];e=stages["E"];g=stages["G"]
    if (d.get("prior_Stage12c_SHA256")!=sha(STAGES["C"][0]/STAGES["C"][1])
        or e.get("source_Stage12d_receipt_SHA256")!=sha(STAGES["D"][0]/STAGES["D"][1])
        or g.get("pinned_Stage12e_SHA256")!=sha(STAGES["E"][0]/STAGES["E"][1])
        or c.get("physically_held_times_intentionally_missing")!=233):
        raise ValueError("Stage12c/d/e/g ancestor SHA or original 233 holds changed")
    return w

def selftest():
    values=[(PASS,True)]*274+[(PASS,False)]
    values +=[(TEMP,True)]*12+[(TEMP,False)]*32
    values +=[(JUMP,True)]+[(JUMP,False)]*35
    assert len(values)==355
    assert sum(not y for _,y in values)==68
    assert sum(x!=PASS and y for x,y in values)==13
    assert sum(x==PASS and not y for x,y in values)==1
    assert equal(np.nan,np.nan) and equal(2,2.+1e-8)
    assert native_key(pd.Series(["2017-07-05 06:30:00"])).iat[0]=="201707050630"
    print("STAGE12X SELF-TEST PASS: exact 68 missing / 13 existing finite warning / 1 diagnostic pass missing; NO WRITES",flush=True)

def load_snapshot(stage, site, keys):
    root,_,suffix=STAGES[stage]
    data=pd.read_csv(file(root/f"{site}_{suffix}.csv"),
           usecols=["time","VPD_USE","QBOT","TA_USE","PSRF"],
           dtype={"time":str},low_memory=False)
    data["native_key"]=native_key(data.time)
    if data.native_key.duplicated().any() or not set(keys)<=set(data.native_key):
        raise ValueError("Stage12"+stage+" original native keys duplicate/missing")
    for name in ("VPD_USE","QBOT","TA_USE","PSRF"):
        data[name]=floatarray(data[name])
    return data

def load_ledgers():
    out={}
    for label,(stage,name,reason) in LEDGERS.items():
        tab=pd.read_csv(file(STAGES[stage][0]/name),
                        dtype={"site":str,"native_key":str},low_memory=False)
        if not {"site","native_key"}<=set(tab.columns):
            raise ValueError("Signed "+label+" source ledger site/key absent")
        if reason is not None and reason not in tab:
            raise ValueError("Signed "+label+" exact hold reason absent")
        if tab.duplicated(["site","native_key"]).any():
            raise ValueError("Duplicate original "+label+" native source")
        out[label]={ (str(row["site"]),str(row["native_key"])):
                      str(row[reason]) if reason is not None else "SIGNED_CANDIDATE"
                      for row in tab.to_dict("records")}
    return out

def audit():
    verify()
    data=pd.read_csv(file(W/W_ROWS),dtype={"native_key":str},low_memory=False)
    needed={"site","year","native_key","screen_group_NOT_MODEL_APPROVAL",
            "Stage12g_same_timestamp_finite",
            "Stage12g_same_timestamp_existing_VPD_USE_hPa",
            "trial_VPD_USE_hPa","trial_QBOT_kgkg",
            "original_unchanged_QC0_tower_T_C","retained_Stage12g_PSRF_Pa",
            "immediate_finite_Stage12g_neighbor_count",
            "immediate_physically_valid_original_QC0_VPD_neighbor_count"}
    if (not needed<=set(data.columns) or len(data)!=355
        or data.duplicated(["site","native_key"]).any()
        or not data.site.isin(SITES).all()):
        raise ValueError("Original Stage12w 355 native source report differs")
    finite=data.Stage12g_same_timestamp_finite.map(
        lambda v:str(v).strip().lower() in ("true","1"))
    groups=data.screen_group_NOT_MODEL_APPROVAL
    count={(group,b):int(((groups==group)&(finite==b)).sum())
           for group,b in EXPECTED}
    if count!=EXPECTED or groups.isna().any():
        raise ValueError("Stage12w original 355 class x Stage12g retained-availability gate changed")
    history=load_ledgers()
    details=[]
    special_context=[]
    for site in SITES:
        records=data.loc[data.site.eq(site)].copy()
        ks=set(records.native_key)
        stages={k:load_snapshot(k,site,ks) for k in "CDEG"}
        snapshots={}
        for stage,frame in stages.items():
            d=frame.loc[frame.native_key.isin(ks)].set_index("native_key")
            snapshots[stage]=d
        g=stages["G"];positions={key:i for i,key in enumerate(g.native_key)}
        for row in records.to_dict("records"):
            key=row["native_key"]
            old={k:float(snapshots[k].loc[key,"VPD_USE"]) for k in "CDEG"}
            val=old["G"]
            present=np.isfinite(val)
            declared=str(row["Stage12g_same_timestamp_finite"]).lower() in ("true","1")
            if present!=declared or not equal(
                val,row["Stage12g_same_timestamp_existing_VPD_USE_hPa"]):
                raise ValueError("Stage12w retained G value differs from signed exact native G source "+key)
            for stage in "CDEG":
                if not equal(snapshots[stage].loc[key,"TA_USE"],
                             row["original_unchanged_QC0_tower_T_C"]):
                    raise ValueError("Signed Stage12"+stage+" would alter original QC0 air T at "+key)
                if not equal(snapshots[stage].loc[key,"PSRF"],
                             row["retained_Stage12g_PSRF_Pa"]):
                    raise ValueError("Signed Stage12"+stage+" source pressure changed at "+key)
            if present and not np.isfinite(old["E"]):
                provenance="FIRST_FINITE_IN_STAGE12G"
            elif present and not np.isfinite(old["D"]):
                provenance="FIRST_FINITE_IN_STAGE12E_OR_EARLIER"
            elif present and not np.isfinite(old["C"]):
                provenance="FIRST_FINITE_IN_STAGE12D"
            elif present:
                provenance="FINITE_ALREADY_IN_STAGE12C"
            else:
                provenance="STILL_MISSING_IN_STAGE12G"
            p=positions[key]
            center=pd.Timestamp(str(g.time.iat[p]))
            context=[]
            for delta in range(-12,13):
                i=p+delta
                if i<0 or i>=len(g):
                    continue
                tim=pd.Timestamp(str(g.time.iat[i]))
                if tim-center!=pd.Timedelta(minutes=delta*30):
                    continue
                context.append((delta,i))
            ref_before=[(delta,i) for delta,i in context
                        if delta<0 and np.isfinite(g.VPD_USE.iat[i])]
            ref_after=[(delta,i) for delta,i in context
                       if delta>0 and np.isfinite(g.VPD_USE.iat[i])]
            cvalue=float(row["trial_VPD_USE_hPa"])
            history_key=(site,key)
            record={
              "site":site,"year":int(row["year"]),"native_key":key,
              "Stage12w_diagnostic_group_NOT_APPROVED":row["screen_group_NOT_MODEL_APPROVAL"],
              "Stage12g_finite":present,
              "Stage12w_hypothetical_original_companion_VPD_hPa":cvalue,
              "Stage12w_hypothetical_QBOT_kgkg":float(row["trial_QBOT_kgkg"]),
              "historical_Stage12c_VPD_hPa":old["C"],
              "historical_Stage12d_VPD_hPa":old["D"],
              "historical_Stage12e_VPD_hPa":old["E"],
              "historical_Stage12g_VPD_hPa":old["G"],
              "first_finite_lineage":provenance,
              "Stage12w_hypothetical_minus_preexisting_G_VPD_hPa":(
                cvalue-val if present else np.nan),
              "Stage12d_original_hold_reason":history["D_hold"].get(history_key,"NO_D_HOLD_LEDGER_RECORD"),
              "Stage12e_original_hold_reason":history["E_hold"].get(history_key,"NO_E_HOLD_LEDGER_RECORD"),
              "Stage12g_original_missing_year_hold_reason":history["G_hold"].get(history_key,"NO_G_HOLD_LEDGER_RECORD"),
              "Stage12d_signed_candidate_ledger":history_key in history["D_candidate"],
              "Stage12g_signed_candidate_ledger":history_key in history["G_candidate"],
              "nearest_G_finite_before_minutes_within6h":(
                int(-ref_before[-1][0]*30) if ref_before else np.nan),
              "nearest_G_finite_after_minutes_within6h":(
                int(ref_after[0][0]*30) if ref_after else np.nan),
              "nearest_G_finite_before_VPD_hPa":(
                float(g.VPD_USE.iat[ref_before[-1][1]]) if ref_before else np.nan),
              "nearest_G_finite_after_VPD_hPa":(
                float(g.VPD_USE.iat[ref_after[0][1]]) if ref_after else np.nan),
              "available_G_finite_count_within6h_excluding_center":int(
                len(ref_before)+len(ref_after)),
              "original_86_plus_233_science_holds_preserved":True,
              "new_source_repair":False,
              "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False
            }
            if not present or row["screen_group_NOT_MODEL_APPROVAL"]!=PASS:
                details.append(record)
            if not present and row["screen_group_NOT_MODEL_APPROVAL"]==PASS:
                for delta,i in context:
                    special_context.append({
                        "site":site,"focal_native_key":key,
                        "relative_minutes":delta*30,
                        "source_native_key":str(g.native_key.iat[i]),
                        "source_Time_unchanged":str(g.time.iat[i]),
                        "historical_G_VPD_hPa":float(g.VPD_USE.iat[i]),
                        "historical_G_QBOT_kgkg":float(g.QBOT.iat[i]),
                        "historical_G_TA_USE_C":float(g.TA_USE.iat[i]),
                        "hypothetical_Stage12w_focal_candidate_VPD_hPa":cvalue,
                        "available_G_neighbor_trial_VPD_jump_hPa":(
                            abs(float(g.VPD_USE.iat[i])-cvalue)
                            if delta!=0 and np.isfinite(g.VPD_USE.iat[i])
                            else np.nan),
                        "not_science_approval":True
                    })
    flagged=pd.DataFrame(details).sort_values(["site","native_key"])
    missing=flagged.loc[~flagged.Stage12g_finite].copy()
    existing=flagged.loc[flagged.Stage12g_finite].copy()
    special=pd.DataFrame(special_context)
    if (len(flagged)!=81 or len(missing)!=68 or len(existing)!=13
        or len(special)!=25
        or missing.loc[missing.Stage12w_diagnostic_group_NOT_APPROVED.eq(PASS)].shape[0]!=1
        or existing.loc[existing.Stage12w_diagnostic_group_NOT_APPROVED.eq(PASS)].shape[0]!=0):
        raise ValueError("Original exact 68 G missing, 13 older finite warning and 1 pass-but-missing audit changed")
    summary=flagged.groupby(["site","year",
                             "Stage12w_diagnostic_group_NOT_APPROVED",
                             "Stage12g_finite","first_finite_lineage"],
                            dropna=False,as_index=False).agg(
           signed_original_native_source_rows=("native_key","size"),
           stage12d_held_ledger_matches=("Stage12d_original_hold_reason",
             lambda s:int(s.ne("NO_D_HOLD_LEDGER_RECORD").sum())),
           stage12e_held_ledger_matches=("Stage12e_original_hold_reason",
             lambda s:int(s.ne("NO_E_HOLD_LEDGER_RECORD").sum())),
           stage12g_held_ledger_matches=("Stage12g_original_missing_year_hold_reason",
             lambda s:int(s.ne("NO_G_HOLD_LEDGER_RECORD").sum())),
           median_hypothetical_minus_old_G_VPD=(
             "Stage12w_hypothetical_minus_preexisting_G_VPD_hPa","median"))
    return missing,existing,special,summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    options=parser.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):options.add_argument("--"+opt,action="store_true")
    args=parser.parse_args()
    print("STAGE12X — EXACT 68 MISSING / 13 EXISTING FINITE WARNINGS, ORIGINAL C-D-E-G SOURCE | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    missing,existing,context,summary=audit()
    print("\n========== EXACT 81 ORIGINAL NATIVE RECONCILIATIONS BY OLD SNAPSHOT AND NEW CANDIDATE ==========",flush=True)
    print(summary.to_string(index=False),flush=True)
    print("\n========== SOLE NEW ERA-COMPANION DIAGNOSTIC-PASS BUT STILL STAGE12G MISSING ==========",flush=True)
    one=missing.loc[missing.Stage12w_diagnostic_group_NOT_APPROVED.eq(PASS)]
    print(one.to_string(index=False),flush=True)
    print("\n========== 13 EXISTING FINITE STAGE12G WITH DIFFERENT NEW CANDIDATE WARNING ==========",flush=True)
    print(existing[["site","native_key","Stage12w_diagnostic_group_NOT_APPROVED",
                    "first_finite_lineage","historical_Stage12g_VPD_hPa",
                    "Stage12w_hypothetical_original_companion_VPD_hPa",
                    "Stage12w_hypothetical_minus_preexisting_G_VPD_hPa"]].to_string(index=False),flush=True)
    print("\nSTAGE12X SUMMARY: exact_missing_G=68 older_finite_G_with_new_candidate_warning=13 "
          "hypothetical_pass_but_G_missing=1 original_86_plus_233_science_holds=TRUE "
          "source_repairs=0 Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12X CHECK ONLY: ZERO REPORT, SOURCE, FORCING OR MODEL WRITES.",flush=True)
        return
    dest=ROOT/"reports"/(
        "stage12x_68missing_13historic_finite_stage12w_cross_candidate_"
        +datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        +"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    frames={
      "68_original_MDS_QC1_rejected_G_missing_native_with_CDEG_hold_ledger.csv":missing,
      "13_original_MDS_QC1_G_finite_other_hypothetical_candidate_warnings.csv":existing,
      "one_pass_but_G_missing_native_pm6h_context.csv":context,
      "81_G_missing_or_oldfinite_warning_stage_history_summary.csv":summary
    }
    for name,frame in frames.items():frame.to_csv(dest/name,index=False)
    (dest/"SCIENCE_HOLD.md").write_text(
      "The old Stage12g source value and new Stage12w original-companion "
      "hypothetical VPD candidate are methodologically distinct. Never "
      "replace/remove old finite Stage12g values based on an alternative "
      "candidate warning; original chronological E/D/G hold ledgers are "
      "separately preserved. One candidate-pass but missing record stays "
      "HOLD pending scientific source review. Original 86+233 scientific "
      "holds, T/P/clock, source, DATM/CIME/Slurm and spinup all unchanged.\n")
    output_sha={n:sha(dest/n) for n in [*frames,"SCIENCE_HOLD.md"]}
    receipt={
      "version":VERSION,
      "stage12w_SHA256":sha(W/W_REC),
      "original_355_signed_MDS_source_cases_preserved":True,
      "exact_68_missing_G":True,
      "exact_13_older_finite_G_candidate_warnings":True,
      "exact_1_pass_but_missing_G":True,
      "original_86_and_233_holds_preserved":True,
      "no_original_source_T_P_VPD_native_clock_change":True,
      "new_forcing_repairs":0,
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "output_SHA256":output_sha
    }
    (dest/"stage12x_source_history_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12X ORIGINAL SOURCE HISTORY SCIENCE REPORT DIR:",dest,flush=True)
    print("ZERO ORIGINAL DATA, SOURCE, FORCING, DATM, CIME, SLURM OR MODEL WRITES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE12X STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

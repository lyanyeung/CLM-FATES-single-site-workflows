#!/usr/bin/env python3
"""Batch03 Stage12a: consolidate VERIFIED Stage11q 3-site shadows and 7 blocked stations.

Audits existing Stage11a (1,924 source-native humidity blockers), preserved
Stage11h US-MOz/US-Mpj shadows, and final Stage11q US-NC2 research shadow.
Computes 7-site priority by P0 physics+clock, physical conflicts and source
evidence problems WITHOUT pretending source ERA/QC2 is observed tower RH.

--self-test synthetic counts, zero access/writes
--check   full immutable SHA source, full US-NC2 TA/TBOT/humidity mask,
          10-site gate and ranked 7 blocked sites; NO file writes.
--run     same checks; write ONLY new independent SHA-sealed review report.
DOES NOT change original data, approved event masks, Post-v5, DATM, CIME,
Slurm jobs, native clocks, temperature or PFT/CO2/surface files.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12a-v1-20261024-three-science-shadows-seven-blocked"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
REPO=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
A=REPO/"scripts/stage11/11a_science_decision_matrix.py"
A_BLOB="a83de59a907179429c1747977c1043ae01f9a7cf"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
H=ROOT/"science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd"
L=ROOT/"science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e"
Q=ROOT/"science_trials/stage11q_US-NC2_auto9_RH_only_20261024T112211Z_cd95c65a"
OLD="US-NC2_humidity_only_new_shadow_NOLEAP.csv"
NEW="US-NC2_humidity_only_auto9_shadow_NOLEAP.csv"
SITES=("US-Kon","US-Me2","US-Me6","US-MMS","US-MOz","US-Mpj",
       "US-MtB","US-NC2","US-NR1","US-NR3")
BLOCKED={"US-Kon":229,"US-Me2":4,"US-Me6":1,"US-MMS":18,
         "US-MtB":15,"US-NR1":173,"US-NR3":1484}
NINE={"202503181730","202503181800","202503230730","202503230800",
      "202503230830","202503231530","202503231600",
      "202503251030","202503251100"}
Q_FILES={NEW,"9_auto_candidate_provenance_RH.csv",
    "13_affected_halfhour_boundaries.csv",
    "2025_annual_mean_humidity_effect.csv",
    "unchanged_two_sites_stage11h_SHA_refs.json","SCIENTIFIC_HOLD.md"}

def regular(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Source missing or symlinked: "+str(p))
    return p

def directory(path):
    p=Path(path)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Source directory missing or symlinked: "+str(p))
    return p

def sha(path):
    h=hashlib.sha256()
    with regular(path).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):
            h.update(part)
    return h.hexdigest()

def gitblob(path):
    b=regular(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def load_11a():
    if gitblob(A)!=A_BLOB:
        raise ValueError("Stage11a tested source blob SHA changed")
    spec=importlib.util.spec_from_file_location("stage11a_pinned_stage12a",A)
    a=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    return a

def source_status():
    for folder in (ROOT,S07,H,L,Q):
        directory(folder)
    for folder in (S07,H,L,Q):
        regular(folder/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    h=json.loads(regular(H/"sha_sealed_shadow_trial_receipt.json").read_text())
    l=json.loads(regular(L/"stage11l_scientific_hold_receipt.json").read_text())
    q=json.loads(regular(Q/"stage11q_sha_science_hold_receipt.json").read_text())
    if (h.get("version")!="stage11h-v1-20261024-53-ERA-RH-isolated-trial"
        or h.get("human_decisions")!=62
        or h.get("ERA_RH_selected_target_rows")!=53
        or h.get("Postv5_approved")!=0
        or h.get("DATM_ready")!=0
        or h.get("spinup_authorizations")!=0
        or l.get("version")!="stage11l-v1-20261024-11-humidity-only-successor"
        or l.get("combined_ERA_RH_target_count")!=64
        or l.get("retained_EC_tower_TA_and_TBOT") is not True
        or l.get("Postv5_approved")!=0
        or q.get("version")!="stage11q-v1-20261024-automated-nine-source-humidity-shadow"
        or q.get("stage11l_source_receipt_SHA256")!=sha(L/"stage11l_scientific_hold_receipt.json")
        or q.get("input_stage11l_forcing_SHA256")!=sha(L/OLD)
        or q.get("prior_human_selected_ERA_RH_target_count")!=64
        or q.get("new_auto_science_candidate_ERA_RH_target_count")!=9
        or q.get("cumulative_shadow_ERA_RH_target_count")!=73
        or q.get("newly_individual_user_approved_nine") is not False
        or q.get("retained_EC_tower_TA_and_TBOT") is not True
        or q.get("noleap_source_rows")!=367920
        or q.get("event_boundaries_tested")!=13
        or q.get("all_touched_edges_below4hPa") is not True
        or q.get("new_edges_added_gt2hPa")!=0
        or q.get("Postv5_approved")!=0
        or q.get("DATM_ready")!=0 or q.get("spinup_authorized")!=0
        or q.get("INCOMPLETE_marker_present") is not True
        or set(q.get("output_sha256",{}))!=Q_FILES):
        raise ValueError("Prior three-site source / Stage11q science receipt mismatch")
    for name,dig in q["output_sha256"].items():
        if sha(Q/name)!=dig:
            raise ValueError("Stage11q output SHA changed: "+name)
    for site in ("US-MOz","US-Mpj"):
        name=f"{site}_shadow_companion_ERA_RH_NOLEAP.csv"
        if sha(H/name)!=h["output_sha256"][name]:
            raise ValueError("Other site SHA protected input changed "+site)
    notes=json.loads(regular(Q/"unchanged_two_sites_stage11h_SHA_refs.json").read_text())
    for site in ("US-MOz","US-Mpj"):
        name=f"{site}_shadow_companion_ERA_RH_NOLEAP.csv"
        if notes[site]["sha256"]!=h["output_sha256"][name]:
            raise ValueError("Q source reference changed: "+site)
    old=pd.read_csv(regular(L/OLD),low_memory=False)
    new=pd.read_csv(regular(Q/NEW),low_memory=False)
    if (len(old)!=367920 or len(new)!=367920
        or list(old.columns)!=list(new.columns)
        or not {"TA_USE","TBOT","VPD_USE","QBOT","time"}<=set(old.columns)):
        raise ValueError("Latest US-NC2 native forcing schema or row count changed")
    native=pd.to_datetime(old.time,errors="raise").dt.strftime("%Y%m%d%H%M")
    if native.duplicated().any() or not new.time.equals(old.time):
        raise ValueError("Native time index altered")
    mask=native.isin(NINE).to_numpy(dtype=bool)
    if mask.sum()!=9:
        raise ValueError("Nine exact Stage11q native target times missing")
    for col in old:
        if col in ("VPD_USE","QBOT"):
            if not np.allclose(old[col].to_numpy(dtype=float)[~mask],
                               new[col].to_numpy(dtype=float)[~mask],
                               rtol=0,atol=0,equal_nan=True):
                raise ValueError("Stage11q off-target humidity source changed: "+col)
        elif not old[col].equals(new[col]):
            raise ValueError("EC tower T, time or other forcing changed: "+col)
    changed=~np.isclose(old.VPD_USE.to_numpy(dtype=float),
                         new.VPD_USE.to_numpy(dtype=float),rtol=0,atol=1e-9)
    if int(changed.sum())!=9 or not np.array_equal(changed,mask):
        raise ValueError("Latest site nine actual VPD changes differ")
    e=vapour(old,new)
    return q,h,l,e

def vapour(old,new):
    t=new.TA_USE.to_numpy(dtype=float)
    sat=6.112*np.exp(17.67*t/(t+243.5))
    actual=sat-new.VPD_USE.to_numpy(dtype=float)
    p=new.PSRF.to_numpy(dtype=float)
    qb=0.622*actual*100/(p-.378*actual*100)
    if (not np.isfinite(qb).all() or not (actual>0).all() or
        not np.allclose(qb,new.QBOT.to_numpy(dtype=float),
                        rtol=1e-9,atol=1e-10)):
        raise ValueError("Latest US-NC2 full-site VPD/QBOT physical closure invalid")
    return {"noleap_halftime_rows":int(len(new)),
            "new_stage11q_native_events":9,
            "qbot_physics_verified":True,"EC_temperature_preserved":True}

def summarize():
    q,h,l,nc=source_status()
    a=load_11a()
    d,h10,k,sha_roots=a.preflight()
    events,years,batch=a.analyze(d,h10,k)
    if len(events)!=1924 or len(years)!=32 or len(batch)!=10:
        raise ValueError("Stage11a 10-site original held events matrix differs")
    if (set(events.site)!=set(BLOCKED) or
        set(events.groupby("site").size().to_dict().items())!=set(BLOCKED.items())):
        raise ValueError("Seven blocked-site event counts differ from SHA-pinned source")
    if not (events.review_route.value_counts().to_dict()=={
        "EVIDENCE_INSUFFICIENT_HOLD":1687,
        "PHYSICS_CONFLICT_HOLD":233,
        "CLOCK_METADATA_HOLD":4}):
        raise ValueError("Stage11a original blocker category counts differ")
    per=events.groupby(["site","review_route"],sort=True).size().unstack(fill_value=0)
    stage=per.reindex(list(BLOCKED),fill_value=0).reset_index()
    stage=stage.rename(columns={
      "CLOCK_METADATA_HOLD":"clock_metadata_hold",
      "PHYSICS_CONFLICT_HOLD":"physics_conflict_hold",
      "EVIDENCE_INSUFFICIENT_HOLD":"evidence_insufficient_hold"})
    for name in ("clock_metadata_hold","physics_conflict_hold",
                 "evidence_insufficient_hold"):
        if name not in stage:
            stage[name]=0
    stage["original_stage11a_humidity_hold_records"]=stage.site.map(BLOCKED)
    stage["VPD_original_QC1_or_QC2_no_direct_QC0"] = True
    stage["automatic_processing_route"]=np.select([
        stage.clock_metadata_hold.gt(0),
        stage.physics_conflict_hold.gt(0)],
        ["REVIEW_NATIVE_CLOCK_METADATA_BEFORE_AUTOMATION",
         "AUTO_GROUP_SOURCE_ERA_RH_SENSITIVITY_PLUS_PHYSICS_GATES"],
        "AUTO_GROUP_SOURCE_ERA_RH_SENSITIVITY_EVIDENCE_ONLY")
    stage["science_hold"]=True
    stage["post_v5_approved"]=False
    stage=stage.sort_values(
        ["original_stage11a_humidity_hold_records","site"],
        ascending=[False,True]).reset_index(drop=True)
    stage["blocker_priority_rank"]=np.arange(1,len(stage)+1)
    qstate=pd.DataFrame([{
        "site":site,
        "evidence_status":("SHA_SEALED_STAGE11Q_RESEARCH_SHADOW_73_ERA_RH_TARGETS"
                           if site=="US-NC2" else
                           "SHA_SEALED_STAGE11H_RESEARCH_SHADOW_53_CROSS_SITE_TARGETS"
                           if site in ("US-MOz","US-Mpj") else
                           "STAGE07_HUMIDITY_BLOCKED_11A_SOURCE_HOLDS"),
        "original_unresolved_11a_humidity_records":BLOCKED.get(site,0),
        "post_v5_approved":False,
        "DATM_ready":False,
        "spinup_authorized":False,
    } for site in SITES])
    assert qstate.original_unresolved_11a_humidity_records.sum()==1924
    totals={
        "version":VERSION,
        "site_count":10,"sealed_numeric_shadow_sites":3,
        "original_humidity_blocked_sites":7,
        "original_humidity_blockers":1924,
        "clock_holds":4,"physics_holds":233,
        "evidence_insufficient_holds":1687,
        "US_NC2_humidity_research_ERA_RH_target_count":73,
        "newly_auto_science_ERA_RH":9,
        "US_NC2_full_site":nc,
        "Postv5_approved_sites":0,"DATM_ready_sites":0,
        "spinup_authorized_sites":0,
        "next_bulk_processing_priority":"US-NR3 then US-Kon then US-NR1; US-Me2 clock separately",
        "science_status":"RESEARCH_EVIDENCE_ONLY_NOT_MODEL_READY"
    }
    return stage,qstate,years,totals

def self_test():
    assert len(SITES)==10 and len(BLOCKED)==7 and sum(BLOCKED.values())==1924
    assert len(NINE)==9 and 1484>229>173
    assert set(SITES)-set(BLOCKED)=={"US-MOz","US-Mpj","US-NC2"}
    print("STAGE12A SELF-TEST PASS: ten sites, seven blocked/1924, three protected humidity shadows, nine latest sources",flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE12A — BATCH03 TEN-SITE INTEGRITY AND SEVEN-SITE PRIORITIZATION | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    blocked,ten,years,totals=summarize()
    print("\n========== TEN SITE READINESS | 3 RESEARCH SHADOWS + 7 BLOCKED ==========",flush=True)
    print(ten.to_string(index=False),flush=True)
    print("\n========== SEVEN BLOCKED SITES RANKED FOR BULK AUTO SCIENCE QC ==========",flush=True)
    print(blocked.to_string(index=False),flush=True)
    print("\n========== 32 SITE-YEAR SCIENTIFIC HOLD SUMMARY ==========",flush=True)
    print(years[["site","year","blockers","VPD_QC1","VPD_QC2",
        "A_water_fail","B_ice_caution","grid_temp_gt5C",
        "clock_holds","physics_holds","evidence_holds"]].to_string(index=False),flush=True)
    print("\nSTAGE12A SUMMARY: "+json.dumps(totals,sort_keys=True),flush=True)
    if args.check:
        print("CHECK ONLY: no reports or original/forcing writes.",flush=True)
        return
    report=ROOT/"reports"/("stage12a_batch03_post11q_ten_site_status_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    report.mkdir(exist_ok=False)
    tables={
        "10_site_post_stage11q_status.csv":ten,
        "7_blocked_sites_ranked_priorities.csv":blocked,
        "32_original_source_site_year_hold_counts.csv":years
    }
    for name,data in tables.items():
        data.to_csv(report/name,index=False)
    (report/"status_and_next_work.json").write_text(json.dumps(totals,indent=2)+"\n")
    note="""# Stage12a is evidence/priority-only
The latest three site climate-forcing shadows remain INCOMPLETE.
Seven other sites have 1,924 original SHA-pinned humidity science holds,
dominated by US-NR3. Their original QC1/QC2 ERA/downscaled humidity
metadata cannot be represented as a direct measured tower RH source.
Later automatic science candidate generation must be restricted to
isolated shadow experiments with exact source/clock/phase and temperature
physics audits; avoid silent Post-v5 release.
This script does not modify any source, site temperature, forcing, PFT,
surface, CO2, DATM, CIME, Slurm, or human decision ledger.
"""
    (report/"SCIENTIFIC_HOLD.md").write_text(note)
    inputs={
        "Stage11q_receipt_SHA256":sha(Q/"stage11q_sha_science_hold_receipt.json"),
        "Stage11h_receipt_SHA256":sha(H/"sha_sealed_shadow_trial_receipt.json"),
        "Stage07_manifest_SHA256":sha(S07/"exact_input_manifest.json"),
        "Stage11a_script_Git_blob":A_BLOB
    }
    receipt={
        "version":VERSION,"inputs_SHA256":inputs,
        "batch_sites":10,"new_automatically_approved_for_model":0,
        "blocked_original_sites":7,"original_unresolved_records":1924,
        "existing_science_shadows":3,
        "science_signoffs":0,"postv5_approved":0,
        "DATM_ready":0,"spinup_authorized":0,
        "output_sha256":{filename:sha(report/filename) for filename in [
            *tables,"status_and_next_work.json","SCIENTIFIC_HOLD.md"]}
    }
    (report/"stage12a_science_hold_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12A REPORT DIR:",report,flush=True)
    print("NO FORCING, HUMAN DECISIONS OR MODEL JOBS MODIFIED.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE12A STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

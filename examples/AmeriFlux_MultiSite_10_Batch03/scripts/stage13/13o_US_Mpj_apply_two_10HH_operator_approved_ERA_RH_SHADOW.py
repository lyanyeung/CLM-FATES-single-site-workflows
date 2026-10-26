#!/usr/bin/env python3
"""Stage13o US-Mpj operator-approved 2014 two complete QC1 VPD episodes.

Exact SOURCE-NATIVE events: Oct11 01:30–06:00, Oct21 04:00–08:30
(10+10 HH). Original three Stage07-approved center VPD/QBOT values stay
bit-for-bit numeric unchanged. At the other 17 SOURCE VPD QC1 slots, transfer
paired source ERA RH to original retained Stage07 TA_USE; reconstruct site
VPD_USE and QBOT using original PSRF. No other original field/time changes.

Stage13m, Stage13d decisions and Stage13n signed science evidence are
strict prerequisites. Fail closed for the *entire* 20 rows if either
10-HH group fails source/QC0/physical/adjacent VPD steps <= 4 hPa.
ERA is reanalysis, not independent measured site humidity.

--self-test: standalone synthetic control, NO original files or writes.
--check: original/ERA SHA, exact source time and VPD QC, Stage13n receipt,
         both true QC0 bookends, 20 RH/QBOT checks, combined continuity,
         original 2018 and 2020 protected, NO WRITES.
--apply: identical checks and isolated 315360-row NOLEAP shadow with
         whole-file field/timestamp differential, reload & SHA receipt;
         no Slurm, CIME, DATM, PFT, ZBOT, Post-v5 or spinup.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VER = "batch03-stage13o-v1-20261026-two-full-QC1-source-runs"
HERE = Path(__file__).resolve().parent
M = HERE / "13m_US_Mpj_3_approved_2014_VPD_two_2018_PRESERVE_source_scoped.py"
M_BLOB = "2eae8663e64739db78ce9dd305ae3aa4b840b06d"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
EVID = (ROOT / "reports" /
       "stage13n_Mpj_original_QC1_ERA_RH_episode_READONLY_20261026T201029Z_3b42b67d")
EVID_SEAL = EVID / "stage13n_READONLY_source_evidence_SHA_receipt.json"
APPROVAL_SCHEMA = "batch03-stage13o-operator-approved-two-full-US-Mpj-QC1-20HH-v1"
SEGMENTS = (
    ("2014-10-11T01:30:00", "2014-10-11T06:00:00",
     "2014-10-11T01:00:00", "2014-10-11T06:30:00"),
    ("2014-10-21T04:00:00", "2014-10-21T08:30:00",
     "2014-10-21T03:30:00", "2014-10-21T09:00:00"),
)
RETAIN_CENTERS = {
    pd.Timestamp("2014-10-11T02:30:00"): 1.032,
    pd.Timestamp("2014-10-11T04:30:00"): 1.163,
    pd.Timestamp("2014-10-21T08:30:00"): 2.103,
}
HH = pd.Timedelta(minutes=30)
MAX_STEP = 4.0
SOURCE_T_ERA_MAX_C = 8.0
OUTFILE = "US-Mpj_CLM_forcing_2008_2025_STAGE13O_20HH_ERA_RH_RESEARCH_SHADOW.csv"

def require_file(p):
    p = Path(p)
    if p.is_symlink() or not p.is_file():
        raise RuntimeError("Required original evidence missing or unsafe symlink: " + str(p))
    return p

def sha(p):
    h = hashlib.sha256()
    with require_file(p).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def require(c, message):
    if not bool(c):
        raise RuntimeError("STAGE13O SCIENCE HOLD: " + message)

def fmt(ts):
    return pd.Timestamp(ts).strftime("%Y-%m-%dT%H:%M:%S")

def close(a, b, tol=1e-8):
    return bool(np.isfinite([float(a), float(b)]).all() and
                np.isclose(float(a), float(b), atol=tol, rtol=0))

def segment_times():
    sections = [pd.date_range(a,b,freq="30min")
                for a,b,_,_ in SEGMENTS]
    require(len(sections)==2 and all(len(x)==10 for x in sections),
            "approved two episodes not 10 halfhours each")
    all_times = sections[0].append(sections[1])
    require(len(all_times)==20 and all_times.is_unique, "operator scope 20 distinct")
    require(set(RETAIN_CENTERS).issubset(set(all_times)),
            "three center identities absent")
    return sections, all_times

def selftest():
    sections, times = segment_times()
    require(pd.Timestamp("2014-10-11T01:00:00")+HH==sections[0][0],
            "QC0 bookend first source cadence wrong")
    require(sections[0][-1]+HH==pd.Timestamp("2014-10-11T06:30:00"),
            "QC0 bookend after source cadence wrong")
    require(len(set(times).difference(RETAIN_CENTERS))==17, "not 17 new neighbors")
    arr = np.asarray([0.10, 1.4449, 1.4402, 1.032049, 2.0581, 1.2943,
                      1.1264, 1.163165, 1.4879, 1.5527, 1.6494, 0.235])
    require(np.diff(arr).size==11 and np.max(np.abs(np.diff(arr)))<MAX_STEP,
            "first event reconstructed source VPD must bridge measured QC0")
    t,v,pa = 5.,1.4449,97000.
    es=6.112*np.exp(17.67*t/(t+243.5))
    q=0.622*(es-v)*100/(pa-0.378*(es-v)*100)
    require(0<q<.08 and 0<v<es, "QBOT water thermodynamics test")
    require(not (np.max(np.abs(np.diff(np.asarray([0.1,8.282,8.263]))))<=MAX_STEP),
            "control must detect uncorrected QC1 discontinuity")
    print("STAGE13O SELF-TEST PASS | 20=10+10 source HH, 3 centers preserved, 17 new, whole-run VPD and QBOT guard", flush=True)

def load_m():
    p=require_file(M)
    blob=subprocess.run(["git","hash-object",str(p)],
                        check=True,capture_output=True,text=True).stdout.strip()
    require(blob==M_BLOB,"prior verified Stage13m source Git blob mismatch")
    spec=importlib.util.spec_from_file_location("verified_stage13m_for_stage13o", p)
    require(spec is not None and spec.loader is not None, "unable to load predecessor")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    require(m.VER=="batch03-stage13m-v1-20261026-three-Mpj-2014-manual-source-gate",
            "prior Stage13m science method changed")
    require(len(m.SCOPED)==3 and len(m.PRESERVE)==2,"protected Stage13m scope mismatch")
    return m

def approval_check(path,m,prior):
    d=json.loads(require_file(path).read_text())
    require(d.get("schema")==APPROVAL_SCHEMA and d.get("site")=="US-Mpj",
            "no exact operator Stage13o 20HH approval")
    require(d.get("status","").startswith("OPERATOR_APPROVED_EXACT_20HH"),
            "Stage13o user science permission not active")
    require(d.get("model_jobs_authorized") is False and
            d.get("DATM_ready") is False and d.get("Postv5_approved") is False,
            "operator model/DATM gate cannot be altered")
    groups=d.get("exact_original_source_native_events",[])
    require(len(groups)==2,"operator approved exact 2 distinct segments")
    for item,ref in zip(groups,SEGMENTS):
        a,b,before,after=ref
        require((item.get("start"),item.get("end"),
                 item.get("pre_QC0"),item.get("post_QC0"))==ref and
                 item.get("half_hours")==10 and
                 item.get("original_VPD_QC_required")==1,
                 "operator exact event / QC0 / QC1 bounds changed")
    centers=d.get("previous_three_approved_centers",[])
    require(len(centers)==3 and len(d.get("science_gates",[]))>=7,
            "operator prior three center approvals missing")
    for rec,(t,v) in zip(centers,RETAIN_CENTERS.items()):
        require(rec.get("native_time")==fmt(t) and
                close(rec.get("retain_existing_Stage07_VPD_hPa_rounded_3dp"),v,1e-9),
                "operator 2014 center selection changed")
    require(d.get("additional_neighbour_source_records_authorized")==17,
            "exactly 17 additional source records must be approved")
    base=d.get("signed_context",{})
    require(base.get("Stage07_US_Mpj_source_sha256")==sha(m.ORIGINAL),
            "approved original Stage07 selected source SHA changed")
    require(base.get("stage13n_evidence_report_dir")==str(EVID),
            "operator Stage13n report evidence target changed")
    # Prior Stage13d and Stage13m approvals are verified by m.audit itself.
    return d

def verify_stage13n(previous,prior,source,m):
    evidence=json.loads(require_file(EVID_SEAL).read_text())
    require(evidence.get("version")=="batch03-stage13n-v1-20261026-Mpj-original-QC1-VPD-segment-review",
            "original Stage13n report version differs")
    require(evidence.get("operator_conditionally_approved_centers")==3 and
            evidence.get("science_passed_stage13m")==0 and
            evidence.get("new_forcing_written") is False and
            evidence.get("original_2018_source_preserved") is True,
            "Stage13n did not report signed original three event HOLD")
    original_inputs=evidence.get("input_SHA256",{})
    expected_inputs={
       "Stage13m_source_Git_blob":M_BLOB,
       "operator_stage13m_decision_SHA256":sha(previous),
       "operator_stage13d_decision_SHA256":sha(prior),
       "original_FLUXMET_SHA256":sha(source["primary"]),
       "original_companion_ERA_SHA256":sha(source["era"]),
       "original_selected_Stage07_SHA256":sha(m.ORIGINAL)
    }
    require(original_inputs==expected_inputs,
            "Stage13n original signed source receipts inconsistent")
    expected_outputs={
      "THREE_original_native_VPD_centers_6h_source_QC_and_ERA_RH.csv",
      "THREE_source_original_QC1_full_run_and_unapproved_ERA_RH_episodes.json",
      "stage13m_original_holds_summary.json",
      "RESEARCH_ONLY_NO_APPROVAL_BEYOND_THREE_CENTERS"
    }
    outputs=evidence.get("output_SHA256",{})
    require(set(outputs)==expected_outputs,"Stage13n evidence set incomplete")
    for name,digest in outputs.items():
        require(sha(EVID/name)==digest,"Stage13n evidence mutated: "+name)
    findings=json.loads(require_file(EVID/
       "THREE_source_original_QC1_full_run_and_unapproved_ERA_RH_episodes.json").read_text())
    require(len(findings)==3,"Stage13n source QC1 report not 3 review centers")
    for idx,group in ((0,0),(1,0),(2,1)):
        record=findings[idx]["original_source_QC1_contiguous_run"]
        a,b,pre,post=SEGMENTS[group]
        require(record.get("status")=="QC1_RUN_VERIFIED" and
                record.get("source_start")==str(pd.Timestamp(a)) and
                record.get("source_end")==str(pd.Timestamp(b)) and
                record.get("source_QC1_HH")==10 and
                record.get("QC_before_run")==0 and
                record.get("QC_after_run")==0 and
                record.get("start_time_before_QC1")==str(pd.Timestamp(pre)) and
                record.get("end_time_after_QC1")==str(pd.Timestamp(post)),
                "Original evidence source QC1 run or measured QC0 boundaries changed")
    table=pd.read_csv(require_file(EVID/
       "THREE_original_native_VPD_centers_6h_source_QC_and_ERA_RH.csv"),
       low_memory=False)
    require(len(table)==75 and
            int(table.QC1_and_source_science_meets_basic_preview.sum())>=20,
            "Stage13n basic source preview ledger missing/corrupted")
    return {"receipt_SHA256":sha(EVID_SEAL),
            "original_original_science_input_SHA256":expected_inputs,
            "three_report_center_original_QC1_verified":True,
            "three_source_6h_windows_rows":75}

def validate(approval,previous,prior):
    m=load_m()
    # Signed raw source, 315360 selected source, previous 3 operator centers,
    # both protected 2018 records, signed operator-approved 2020 TA.
    selected,review,protected,summary=m.audit(previous,prior)
    require(int(summary["passed_science_adoptions"])==0 and
            int(summary["held_candidate_events"])==3,
            "Stage13m original point-only VPD HOLD proof changed")
    decision=approval_check(approval,m,prior)
    source=m.signed_sources(prior)
    evidence=verify_stage13n(previous,prior,source,m)
    tower=m.raw(source["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    era=m.raw(source["era"],["TA_ERA","VPD_ERA"])
    require(selected.index.equals(tower.index) and selected.index.equals(era.index),
            "original source time/ERA site NOLEAP mismatch")
    require(sha(source["primary"])==decision["signed_context"]["original_tower_sha256"] and
            sha(source["era"])==decision["signed_context"]["original_companion_ERA_sha256"],
            "Original operator source tower/companion ERA SHA changed")

    sections,alltimes=segment_times()
    edits=[]
    summaries=[]
    candidate_values={}
    for seq,(section,(a,b,pre,post)) in enumerate(zip(sections,SEGMENTS),1):
        require(section[0]-HH==pd.Timestamp(pre) and
                section[-1]+HH==pd.Timestamp(post),
                "original source native halfhour/bookend not exact")
        require(pd.Timestamp(pre) in selected.index and
                pd.Timestamp(post) in selected.index, "original true QC0 bookend absent")
        bookend_details=[]
        for tstr in (pre,post):
            t=pd.Timestamp(tstr)
            require(float(tower.at[t,"VPD_F_QC"])==0.,
                    "original source VPD QC0 bookend not measured: "+tstr)
            require(close(selected.at[t,"VPD_USE"],tower.at[t,"VPD_F"],1e-8),
                    "signed Stage07 source changed measured original QC0 VPD: "+tstr)
            require(np.isfinite([selected.at[t,"TA_USE"],selected.at[t,"VPD_USE"],
                                 selected.at[t,"QBOT"],selected.at[t,"PSRF"]]).all(),
                    "original source QC0 bookend model values nonfinite")
            tRH,tQ=m.rh_q(float(selected.at[t,"TA_USE"]),
                         float(selected.at[t,"VPD_USE"]),float(selected.at[t,"PSRF"]))
            require(0<tRH<100 and 0<tQ<.08,
                    "original VPD QC0 boundary physical humidity invalid "+tstr)
            bookend_details.append({
              "original_QC0_native_time":tstr,
              "original_tower_VPD_hPa":float(tower.at[t,"VPD_F"]),
              "retained_Stage07_VPD_hPa":float(selected.at[t,"VPD_USE"]),
              "original_TA_F_QC":float(tower.at[t,"TA_F_QC"]),
              "original_VPD_F_QC":0,
              "retained_stage07_RH_pct":float(tRH)
            })
        prospective=[]
        proposed=[]
        for ts in section:
            sourceVQC=float(tower.at[ts,"VPD_F_QC"])
            require(sourceVQC==1.,
                    "unauthorized native source QC0/QC2 inside 10HH operator scope "+str(ts))
            siteT=float(selected.at[ts,"TA_USE"])
            sourceT=float(tower.at[ts,"TA_F"])
            eraT=float(era.at[ts,"TA_ERA"])
            eraV=float(era.at[ts,"VPD_ERA"])
            pressure=float(selected.at[ts,"PSRF"])
            require(np.isfinite([siteT,sourceT,eraT,eraV,pressure]).all(),
                    "missing source T/ERA humidity/pressure "+str(ts))
            require(close(siteT,sourceT,1e-8),
                    "Stage07 original site temperature modified unexpectedly "+str(ts))
            require(45000<pressure<111000 and
                    abs(siteT-eraT)<=SOURCE_T_ERA_MAX_C,
                    "ERA/site T >8 C or PSRF outside limits "+str(ts))
            es_site=float(m.sat(siteT))
            es_era=float(m.sat(eraT))
            eraRH=100*(1-eraV/es_era)
            require(0<eraRH<100,
                    "source companion ERA RH invalid "+str(ts))
            proposedV=es_site*(1-eraRH/100)
            reconstructedRH,reconstructedQ=m.rh_q(siteT,proposedV,pressure)
            require(np.isfinite([proposedV,reconstructedRH,reconstructedQ]).all() and
                    0<proposedV<es_site and 0<reconstructedRH<100 and
                    0<reconstructedQ<0.08,
                    "reconstructed VPD/RH/QBOT physical failure "+str(ts))
            is_center=ts in RETAIN_CENTERS
            if is_center:
                # Reuse 3 existing Stage07 approvals, no new edited values.
                resultV=float(selected.at[ts,"VPD_USE"])
                resultQ=float(selected.at[ts,"QBOT"])
                require(close(resultV,RETAIN_CENTERS[ts],0.000501) and
                        close(resultV,proposedV,1e-7) and
                        close(resultQ,reconstructedQ,5e-8),
                        "previous approved 2014 source VPD/QBOT centers would be altered "+str(ts))
            else:
                resultV=float(proposedV)
                resultQ=float(reconstructedQ)
            require(0<resultV<es_site and 0<resultQ<.08 and
                    close(100*(1-resultV/es_site),eraRH,1e-4),
                    "full segment source RH and locked center consistency failure "+str(ts))
            require(close(float(selected.at[ts,"TBOT"]),siteT+273.15,1e-8),
                    "Stage07 original retained T/TBOT inconsistency "+str(ts))
            proposed.append(resultV)
            candidate_values[ts]=(resultV,resultQ,is_center)
            edits.append({
              "event_number":seq,
              "native_time":fmt(ts),
              "operator_authorized_QC1":True,
              "original_source_VPD_F_QC":sourceVQC,
              "original_source_TA_F_QC":float(tower.at[ts,"TA_F_QC"]),
              "retained_TA_USE_C":siteT,
              "source_ERA_T_C":eraT,
              "original_source_ERA_VPD_hPa":eraV,
              "paired_ERA_RH_percent":eraRH,
              "old_Stage07_VPD_USE_hPa":float(selected.at[ts,"VPD_USE"]),
              "approved_new_VPD_USE_hPa":resultV,
              "old_Stage07_QBOT_kgkg":float(selected.at[ts,"QBOT"]),
              "approved_new_QBOT_kgkg":resultQ,
              "PSRF_Pa_unchanged":pressure,
              "old_selected_site_RH_pct":float(100*(1-float(selected.at[ts,"VPD_USE"])/es_site)),
              "new_reconstructed_site_RH_pct":float(100*(1-resultV/es_site)),
              "previous_three_2014_centers_numerically_unchanged":is_center,
              "source_selected_new_value_passes_science":True
            })
        combined=np.asarray([float(selected.at[pd.Timestamp(pre),"VPD_USE"]),
                             *proposed,
                             float(selected.at[pd.Timestamp(post),"VPD_USE"])],dtype=float)
        jumps=np.abs(np.diff(combined))
        require(len(combined)==12 and len(jumps)==11 and
                np.isfinite(jumps).all() and np.all(jumps<=MAX_STEP),
                "whole 10HH source VPD continuity failed including original source QC0 bookends "+str(a)+" max="+str(float(np.nanmax(jumps))))
        summaries.append({
          "event":seq,"original_QC1_start":a,"original_QC1_end":b,
          "exact_original_source_QC1_HH":10,
          "reconstructed_n":sum(1 for t in section if t not in RETAIN_CENTERS),
          "preexisting_three_centers_retained_n":sum(1 for t in section if t in RETAIN_CENTERS),
          "all_ten_ERA_RH_physics_PASS":True,
          "original_source_QC0_bookends":bookend_details,
          "max_source_native_adjacent_VPD_jump_hPa":float(jumps.max()),
          "source_native_adjacent_VPD_steps_hPa":jumps.tolist(),
          "source_science_PASS":True
        })
    require(len(candidate_values)==20 and len(edits)==20 and len(summaries)==2,
            "only 20 exact source events can be science accepted")
    changes=[t for t in alltimes if t not in RETAIN_CENTERS]
    require(len(changes)==17, "requires exactly 17 new VPD+QBOT edits")
    for t in changes:
        oldV=float(selected.at[t,"VPD_USE"])
        oldQ=float(selected.at[t,"QBOT"])
        newV,newQ,_=candidate_values[t]
        require(not close(oldV,newV,1e-9) and not close(oldQ,newQ,1e-12),
                "expected new source-native paired 17 VPD and QBOT values not actually different "+str(t))
    quality={
       "version":VER,"site":"US-Mpj","source_native_scope":20,
       "new_17_source_native_VPD_and_QBOT_changes":17,
       "previous_three_center_VPD_and_QBOT_preserved":True,
       "two_2018_original_low_RH_source_values_preserved":True,
       "previous_approved_2020_TA_TBOT_preserved":True,
       "original_Stage07_selected_source_sha256":sha(m.ORIGINAL),
       "original_tower_sha256":sha(source["primary"]),
       "original_companion_ERA_sha256":sha(source["era"]),
       "signed_stage13n_evidence":evidence,
       "signed_operator_approval_sha256":sha(approval),
       "event_summaries":summaries,
       "ERA_RH_source_is_reanalysis_not_true_site_measurement":True,
       "postv5_approved":False,"DATM_ready":False,
       "spinup_authorized":False,"Slurm_jobs_submitted":False,
       "status":"SCIENTIFIC_20HH_SOURCE_GATES_PASS_NO_MODEL_AUTHORIZATION"
    }
    return m,selected,pd.DataFrame(edits),quality,candidate_values

def apply(m,original,edits,quality,candidate_values,approval,previous,prior):
    result=original.copy(deep=True)
    changed={t for t in candidate_values if t not in RETAIN_CENTERS}
    require(len(changed)==17 and len(candidate_values)==20,
            "at export cannot expand the two signed source 10HH events")
    for t in changed:
        v,q,_=candidate_values[t]
        result.at[t,"VPD_USE"]=v
        result.at[t,"QBOT"]=q
    # Enforce exact diff and original protection *before* writing anything.
    protected_columns=[c for c in original.columns if c not in ("VPD_USE","QBOT")]
    for col in protected_columns:
        require(original[col].equals(result[col]),
                "unapproved changed source field including time: "+col)
    changed_counts={}
    for col in ("VPD_USE","QBOT"):
        a=original[col].to_numpy(dtype=float)
        b=result[col].to_numpy(dtype=float)
        difference=~np.isclose(a,b,rtol=0,atol=1e-12,equal_nan=True)
        native_changed=set(result.index[difference])
        require(native_changed==changed,
                "unapproved changed source native times/count "+col)
        changed_counts[col]=int(difference.sum())
        require(changed_counts[col]==17,"source amendment count not 17 at "+col)
    for t in list(RETAIN_CENTERS)+[pd.Timestamp("2018-02-02T17:30:00"),
                                  pd.Timestamp("2018-02-02T19:00:00"),
                                  pd.Timestamp("2020-02-11T06:30:00")]:
        require(original.loc[t].equals(result.loc[t]),
                "operator protected 2014/2018/2020 source row altered "+str(t))
    require(sha(m.ORIGINAL)==quality["original_Stage07_selected_source_sha256"],
            "Original source Stage07 mutated before export")

    dest=m.ROOT/"science_trials"/(
        "stage13o_Mpj_20HH_operator_approved_ERA_RH_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    incomplete=dest/"INCOMPLETE_RESEARCH_SHADOW_NOT_DATM"
    incomplete.write_text("An unfinished source export is not scientifically admitted.\n")
    result.reset_index(drop=True).to_csv(dest/OUTFILE,index=False,float_format="%.17g")
    back=pd.read_csv(require_file(dest/OUTFILE),dtype={"time":str},low_memory=False)
    require(len(back)==m.EXPECTED_ROWS and
            back.time.equals(original.time.reset_index(drop=True)) and
            list(back.columns)==list(original.columns),
            "export altered the 315360 NOLEAP source chronology or schema")
    for col in result.columns:
        if col=="time": continue
        x=result[col].to_numpy(dtype=float)
        y=pd.to_numeric(back[col],errors="raise").to_numpy(dtype=float)
        require(np.allclose(x,y,atol=1e-12,rtol=1e-14,equal_nan=True),
                "source field output CSV roundtrip changed values "+col)
    # Independently ensure the protected 315360-row source original remains.
    require(sha(m.ORIGINAL)==quality["original_Stage07_selected_source_sha256"],
            "original Stage07 input SHA unexpectedly changed after write")
    ledger="exact_20_original_QC1_ERA_RH_VPD_QBOT_science_source_ledger.csv"
    edits.to_csv(dest/ledger,index=False,float_format="%.17g")
    summary_name="stage13o_science_summary.json"
    quality={**quality,
             "science_shadow_created":True,
             "actual_changed_selected_source_model_fields":changed_counts,
             "source_315360_NOLEAP_verified":True,
             "new_source_shadow_fully_verified":True,
             "status":"CREATED_ISOLATED_RESEARCH_SHADOW_NOT_DATM"}
    (dest/summary_name).write_text(json.dumps(quality,indent=2,default=str)+"\n")
    marker="NO_POSTV5_DATM_AD400_SLURM_AUTHORITY"
    (dest/marker).write_text(
        "Two 10HH original 2014 US-Mpj VPD QC1 source events; 17 new"
        " paired ERA-RH derived VPD/QBOT edits. Previous 3 VPD center values"
        " numerical values unchanged. Both original VPD QC0 bookends retained."
        " Two original Feb2018 VPD values (11.261/9.178) unchanged."
        " Already-approved Feb2020 TA=1.1795 unchanged."
        " Original source, ERA, Stage07, Stage11h, PFT, ZBOT, DATM, CIME,"
        " Post-v5, AD400, Normal400 and Slurm not modified/approved.\n")
    files=(OUTFILE,ledger,summary_name,marker)
    seal={
       "version":VER,"operator_Stage13o_approval_SHA256":sha(approval),
       "operator_previous_Stage13m_approval_SHA256":sha(previous),
       "operator_previous_Stage13d_approval_SHA256":sha(prior),
       "original_Stage07_sha256":sha(m.ORIGINAL),
       "stage13n_evidence_receipt_sha256":sha(EVID_SEAL),
       "original_source_and_sci_locked":True,
       "original_2018_and_2020_preserved":True,
       "full_run_20HH_operator_authorized":True,
       "new_edits":changed_counts,"production_Postv5_authorized":False,
       "DATM_ready":False,"spinup_authorized":False,
       "Slurm_jobs_submitted":False,
       "output_SHA256":{p:sha(dest/p) for p in files}
    }
    (dest/"stage13o_Mpj_20HH_ERA_RH_SHA_receipt.json").write_text(
         json.dumps(seal,indent=2)+"\n")
    incomplete.unlink()
    print("STAGE13O 20/20 SOURCE SCIENCE PASS; 17 NEW PAIRED VPD/QBOT SOURCE EDITS SUCCESS",dest,flush=True)
    print("NOLEAP SOURCE ROWS",len(back),
          "ACTUAL NEW NUMERIC CHANGES",changed_counts,flush=True)
    print("THREE 2014 PREEXISTING STAGE07 CENTER VALUES PRESERVED; TWO 2018 ORIGINAL VPD, 2020 TA PRESERVED",flush=True)
    print("NO SOURCE / PFT / ZBOT / DATM / MODEL / SLURM MODIFICATIONS",flush=True)

def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","apply"):
        mode.add_argument("--"+name,action="store_true")
    ap.add_argument("--approval",type=Path)
    ap.add_argument("--previous-approval",type=Path)
    ap.add_argument("--prior-qc0-approval",type=Path)
    a=ap.parse_args()
    print("STAGE13O TWO OPERATOR APPROVED QC1 ERA-RH FULL EPISODES | "+VER,flush=True)
    selftest()
    if a.self_test: return
    if not all([a.approval,a.previous_approval,a.prior_qc0_approval]):
        ap.error("Must supply Stage13o --approval, Stage13m --previous-approval, Stage13d --prior-qc0-approval")
    m,selected,edits,quality,values=validate(a.approval,a.previous_approval,a.prior_qc0_approval)
    print("\nSTAGE13O TWO FULL 10HH SCIENCE DECISIONS",flush=True)
    for r in quality["event_summaries"]:
        print(json.dumps(r,sort_keys=True),flush=True)
    print("STAGE13O EVENT PREVIEW (FIRST/FINAL AND EXISTING THREE CENTERS)",flush=True)
    wanted=set(RETAIN_CENTERS)|{pd.Timestamp(a) for a,_,_,_ in SEGMENTS}|{pd.Timestamp(b) for _,b,_,_ in SEGMENTS}
    shown=edits.loc[pd.to_datetime(edits.native_time).isin(wanted),
                    ["native_time","original_source_VPD_F_QC",
                     "old_Stage07_VPD_USE_hPa","approved_new_VPD_USE_hPa",
                     "old_Stage07_QBOT_kgkg","approved_new_QBOT_kgkg",
                     "previous_three_2014_centers_numerically_unchanged"]]
    print(shown.to_string(index=False,float_format=lambda x:f"{x:.9g}"),flush=True)
    if a.check:
        print("STAGE13O READONLY CHECK PASS | 20/20 RH/QBOT, both full episode VPD joins and 4 QC0 bookends; 17 actual new paired values; NO WRITES",flush=True)
        return
    apply(m,selected,edits,quality,values,a.approval,a.previous_approval,a.prior_qc0_approval)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print("STAGE13O SCIENCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

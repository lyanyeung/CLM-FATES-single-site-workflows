#!/usr/bin/env python3
"""Stage13m — operator-approved conditional US-Mpj three original-native
2014 Stage07 VPD candidates; preserve BOTH original 2018 low-RH VPD points.

The three candidate VPD numbers ALREADY EXIST in original Stage07 selected
model input: this code audits/adopts approved science; it never claims three
new Stage07-versus-shadow numerical changes. It specifically does NOT use
Stage11h, which changed later US-Mpj 2018 source humidity for study.

--self-test: no source I/O, no writes
--check: source SHA/QC/time, neighbors, RH/QBOT, user approval, NO WRITES
--apply: full audit repeated; if >=1 event passes creates NEW separate
         SHA-sealed research-only 18-year shadow. For any failed 2014 event,
         VPD_USE/QBOT are NaN (HOLD) in the new INCOMPLETE shadow, rather than
         silently carrying over unapproved Stage07 values. If all 3 fail,
         no shadow is created (HOLD). Two 2018 rows and 2020 approved TA
         remain exactly as original Stage07 selected; no original source edits.

Never promote to Post-v5, CIME/DATM, AD400, Normal400 or Slurm.
"""
import argparse, hashlib, json, sys, traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VER="batch03-stage13m-v1-20261026-three-Mpj-2014-manual-source-gate"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
SITE="US-Mpj"
YEARS=(2008,2025)
EXPECTED_ROWS=18*17520
STEPS=pd.Timedelta(minutes=30)
THRESHOLD=4.
SCOPED=(
 ("2014-10-11T02:30:00",8.245,1.032,1.065,6.654),
 ("2014-10-11T04:30:00",8.170,1.163,3.883,6.233),
 ("2014-10-21T08:30:00",11.018,2.103,8.530,8.473),
)
PRESERVE=(
 ("2018-02-02T17:30:00",11.261),
 ("2018-02-02T19:00:00",9.178),
)
TA2020=pd.Timestamp("2020-02-11T06:30:00")
APPROVAL_SCHEMA="batch03-stage13m-operator-conditional-US-Mpj-three-VPD-and-two-preserve-v1"
ORIGINAL=S07/SITE/"forcing"/"processed_v5"/"US-Mpj_CLM_forcing_2008_2025.csv"
EVENTS=S07/SITE/"forcing"/"qc_v5"/"US-Mpj_replacement_events.csv"
MANUAL=S07/SITE/"forcing"/"qc_v5"/"US-Mpj_manual_review.csv"
AUDIT=S07/SITE/"forcing"/"qc_v5"/"US-Mpj_independent_audit.json"
FIELDS=("time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE")
NAME="US-Mpj_CLM_forcing_2008_2025_STG13M_OPERATOR_SCIENCE_SHADOW.csv"

def file(path):
    path=Path(path)
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("Required immutable source absent or symlink "+str(path))
    return path

def sha(path):
    h=hashlib.sha256()
    with file(path).open("rb") as stream:
        for x in iter(lambda:stream.read(1<<20),b""):
            h.update(x)
    return h.hexdigest()

def sat(t):
    return 6.112*np.exp(17.67*t/(t+243.5))

def rh_q(t,v,p):
    """Tower/site T Celsius, VPD hPa, site PSRF Pa; water-saturation branch."""
    if not all(np.isfinite([t,v,p])) or p<=45000 or p>=111000:
        return float("nan"),float("nan")
    es=sat(t)
    ea=(es-v)*100
    return 100*ea/(es*100),0.622*ea/(p-0.378*ea)

def close(a,b,tol=0.000501):
    return bool(np.isfinite(a) and np.isfinite(b) and
                np.isclose(float(a),float(b),rtol=0,atol=tol))

def stamp(s):
    return pd.Timestamp(s).strftime("%Y-%m-%dT%H:%M:%S")

def selftest():
    assert len(SCOPED)==3 and len(PRESERVE)==2
    assert len({stamp(x[0]) for x in SCOPED+PRESERVE})==5
    assert all(pd.Timestamp(t).minute in (0,30) for t,*_ in SCOPED+PRESERVE)
    assert set(t for t,*_ in SCOPED).isdisjoint(t for t,*_ in PRESERVE)
    assert all(x[0].startswith("2014") for x in SCOPED)
    assert all(x[0].startswith("2018") for x in PRESERVE)
    r,q=rh_q(5,2,97000)
    assert 0<r<100 and 0<q<.08
    r,q=rh_q(5,100,97000)
    assert r<0 and q<0
    assert pd.Timestamp("2014-10-11 02:30")+STEPS==pd.Timestamp("2014-10-11 03:00")
    print("STAGE13M SELF-TEST PASS | exactly three 2014 VPD conditional, two 2018 protected, 2020 TA protected; zero writes",flush=True)

def decision(path):
    obj=json.loads(file(path).read_text())
    if obj.get("schema")!=APPROVAL_SCHEMA or obj.get("site")!=SITE:
        raise RuntimeError("Unrecognized operator approval JSON")
    entries=obj.get("scoped_2014_VPD",[])
    preserve=obj.get("keep_original_2018_VPD",[])
    if (len(entries)!=3 or len(preserve)!=2 or
        obj.get("status",{}).get("postv5_approved") is not False or
        obj.get("status",{}).get("Slurm_jobs_authorized") is not False):
        raise RuntimeError("Decision scope or Post-v5/Slurm hold changed")
    for record,canonical in zip(entries,SCOPED):
        time,sourcev,target,*_=canonical
        if (record.get("native_time")!=time or
            record.get("decision")!="CONDITIONAL_APPROVAL_ONLY" or
            not close(float(record["original_tower_VPD_hPa"]),sourcev,1e-8) or
            not close(float(record["candidate_stage07_VPD_hPa_3dp"]),target,1e-8)):
            raise RuntimeError("Approved three VPD values/time/order modified")
    for record,(time,value) in zip(preserve,PRESERVE):
        if (record.get("native_time")!=time or
            record.get("decision")!="NO_CHANGE_ORIGINAL" or
            not close(float(record["original_VPD_hPa_3dp"]),value,1e-8)):
            raise RuntimeError("Protected 2018 low-RH source change requested")
    t=obj.get("already_approved_2020_temperature",{})
    if (t.get("native_time")!=stamp(TA2020) or
        not close(float(t.get("interpolated_C",float("nan"))),1.1795,1e-8)):
        raise RuntimeError("Original approved 2020 source TA changed")
    return obj

def signed_sources(previous):
    checks=json.loads(file(S07/"output_sha256.json").read_text())
    manifest=json.loads(file(S07/"exact_input_manifest.json").read_text())
    preserved=json.loads(file(S07/"input_preservation_check.json").read_text())
    if preserved.get("unchanged") is not True or preserved.get("changed_inputs")!=[]:
        raise RuntimeError("Original Stage07 source preservation check failed")
    specs=[x for x in manifest["sites"] if x.get("site")==SITE]
    if len(specs)!=1 or int(specs[0]["native_minutes"])!=30:
        raise RuntimeError("Stage07 published native 30-minute site source absent")
    source=specs[0]
    pinned={str(Path(k).resolve()):v for k,v in manifest["input_sha256"].items()}
    for tag in ("primary","era"):
        p=file(source[tag])
        if sha(p)!=pinned.get(str(p.resolve())):
            raise RuntimeError("Original tower / paired ERA SHA changed "+tag)
    for p in (ORIGINAL,EVENTS,MANUAL,AUDIT):
        if sha(p)!=checks.get(str(p.relative_to(S07))):
            raise RuntimeError("Stage07 SHA sealed input altered: "+str(p))
    audit=json.loads(file(AUDIT).read_text())
    if audit.get("site")!=SITE or audit.get("status")!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED":
        raise RuntimeError("Historical Stage07 numeric audit not the expected one")
    prior=json.loads(file(previous).read_text())
    if prior.get("schema")!="batch03-stage13d-qc0-operator-approval-v1":
        raise RuntimeError("Previous approved six QC0 source temperature policy missing")
    ta=[x for x in prior.get("six_approved_specific_events",[]) if x.get("site")==SITE]
    if len(ta)!=1 or stamp(ta[0]["native_time"])!=stamp(TA2020) or \
       not close(float(ta[0]["approved_selected_TA_C"]),1.1795,1e-8):
        raise RuntimeError("Operator's original US-Mpj 2020 TA interpolation not authenticated")
    return source

def raw(p,columns):
    df=pd.read_csv(file(p),usecols=["TIMESTAMP_START",*columns],
       dtype={"TIMESTAMP_START":str},low_memory=False)
    time=pd.to_datetime(df.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    good=time.dt.year.between(*YEARS) & ~((time.dt.month==2)&(time.dt.day==29))
    df=df.loc[good].copy()
    df.index=pd.DatetimeIndex(time.loc[good],name="native_time")
    df.drop(columns=["TIMESTAMP_START"],inplace=True)
    if df.index.has_duplicates or df.index.hasnans or not df.index.is_monotonic_increasing:
        raise RuntimeError("Original source timestamps invalid")
    for key in columns:
        df[key]=pd.to_numeric(df[key],errors="coerce")
        df.loc[df[key]<=-9990,key]=np.nan
    return df

def full_source():
    df=pd.read_csv(file(ORIGINAL),dtype={"time":str},low_memory=False)
    idx=pd.to_datetime(df.time,errors="raise")
    df.index=pd.DatetimeIndex(idx,name="native_time")
    if len(df)!=EXPECTED_ROWS or df.index.has_duplicates or df.index.hasnans or not df.index.is_monotonic_increasing:
        raise RuntimeError("Stage07 original 18y NOLEAP site forcing not valid")
    if df.index[0]!=pd.Timestamp("2008-01-01 00:00") or df.index[-1]!=pd.Timestamp("2025-12-31 23:30"):
        raise RuntimeError("Stage07 source year endpoints wrong")
    if set(FIELDS).difference(df.columns):
        raise RuntimeError("Original Stage07 model source has missing fields")
    for col in FIELDS:
        if col=="time":continue
        df[col]=pd.to_numeric(df[col],errors="coerce")
        if not np.isfinite(df[col].to_numpy(dtype=float)).all():
            raise RuntimeError("Historical accepted numeric input unexpectedly has NaN in "+col)
    return df

def audit(approval,prior):
    decision(approval)
    source=signed_sources(prior)
    selected=full_source()
    tower=raw(source["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    era=raw(source["era"],["TA_ERA","VPD_ERA"])
    if not(tower.index.equals(era.index) and selected.index.equals(tower.index)):
        raise RuntimeError("Signed original FLUXMET and standalone ERA site native-time indexing differs")
    manual=pd.read_csv(file(MANUAL),dtype={"time":str},low_memory=False)
    events=pd.read_csv(file(EVENTS),dtype={"time":str},low_memory=False)
    if len(manual)!=5 or manual.variable.ne("VPD_F").any():
        raise RuntimeError("Original US-Mpj 5 exact manual VPD flags changed")
    manual.index=pd.DatetimeIndex(pd.to_datetime(manual.time,errors="raise"))
    if manual.index.has_duplicates or set(manual.index)!={pd.Timestamp(x[0]) for x in SCOPED+PRESERVE}:
        raise RuntimeError("Stage07 five original manual VPD time IDs changed")
    events.index=pd.DatetimeIndex(pd.to_datetime(events.time,errors="raise"))
    if not{"variable","final_value","original_value","official_qc"}.issubset(events.columns):
        raise RuntimeError("Stage07 signed replacement-event columns changed")
    if events.index.has_duplicates and not events.loc[events.index.duplicated(keep=False)].variable.isin(["TA_F","VPD_F"]).all():
        raise RuntimeError("Duplicate selected event timestamp unknown variable")
    ta_event=events.loc[(events.index==TA2020)&events.variable.eq("TA_F")]
    if len(ta_event)!=1 or not close(float(ta_event.iloc[0].final_value),1.1795,1e-8):
        raise RuntimeError("Previously approved 2020 selected TA event not preserved")
    if not close(float(selected.at[TA2020,"TA_USE"]),1.1795,1e-8) or \
       not close(float(selected.at[TA2020,"TBOT"]),274.3295,1e-8):
        raise RuntimeError("Previously approved US-Mpj 2020 TA/TBOT edited")
    if not close(float(tower.at[TA2020,"TA_F"]),-17.667,0.000501):
        raise RuntimeError("Original US-Mpj 2020 tower temperature changed")

    preview=[]
    def physics_at(ts,v=None):
        t=float(selected.at[ts,"TA_USE"])
        vv=float(selected.at[ts,"VPD_USE"]) if v is None else float(v)
        p=float(selected.at[ts,"PSRF"])
        rh,q=rh_q(t,vv,p)
        es=float(sat(t))
        return {"rh":rh,"q":q,"es":es,"vpd":vv,"T":t,"p":p,
                "physical":bool(np.isfinite([rh,q,es,vv,p,t]).all() and
                    0<rh<100 and 0<q<0.08 and 0<vv<es)}

    for stampstr,orig,vpd,torig,eraT in SCOPED:
        time=pd.Timestamp(stampstr)
        row=manual.loc[time]
        if isinstance(row,pd.DataFrame) or row.variable!="VPD_F":
            raise RuntimeError("Original signed manual source QC1/0 center invalid "+stampstr)
        actual_orig=float(tower.at[time,"VPD_F"])
        actual_t=float(tower.at[time,"TA_F"])
        companion_t=float(era.at[time,"TA_ERA"])
        current=float(selected.at[time,"VPD_USE"])
        ev=events.loc[(events.index==time)&events.variable.eq("VPD_F")]
        if len(ev)!=1:
            raise RuntimeError("Stage07 selected 2014 VPD event not in exact source ledger "+stampstr)
        event=ev.iloc[0]
        if not(close(actual_orig,orig,0.000501) and close(actual_t,torig,0.000501) and
               close(companion_t,eraT,0.000501)):
            raise RuntimeError("Stage13c original observed/raw temperature/VPD context changed "+stampstr)
        if not(close(float(event.original_value),orig,0.000501) and
               close(float(event.final_value),current,1e-7) and
               close(current,vpd,0.000501)):
            raise RuntimeError("Operator Stage07 approved source VPD value differs from signed selected candidate "+stampstr)
        if not(close(float(row.official_qc),float(tower.at[time,"VPD_F_QC"]),1e-8) and
               close(float(event.official_qc),float(tower.at[time,"VPD_F_QC"]),1e-8)):
            raise RuntimeError("Original source VPD QC disagrees with two signed review ledgers "+stampstr)
        before=time-STEPS
        after=time+STEPS
        old=physics_at(time)
        prev=physics_at(before)
        next_=physics_at(after)
        # An existing QA-approved Stage07 candidate must already be
        # thermodynamically paired with retained site temperature and pressure.
        q_existing=float(selected.at[time,"QBOT"])
        water_q_consistent=bool(old["physical"] and close(old["q"],q_existing,5e-8) and
                               close(float(selected.at[time,"TBOT"]),old["T"]+273.15,1e-8))
        era_rh=100*(1-float(era.at[time,"VPD_ERA"])/float(sat(companion_t)))
        source_ok=bool(0<era_rh<100 and np.isfinite(era_rh))
        left_jump=abs(current-prev["vpd"])
        right_jump=abs(next_["vpd"]-current)
        neighbor_good=bool(prev["physical"] and next_["physical"] and
                           left_jump<=THRESHOLD and right_jump<=THRESHOLD and
                           time-before==STEPS and after-time==STEPS)
        approved=bool(water_q_consistent and source_ok and neighbor_good)
        reasons=[]
        if not source_ok:reasons.append("PAIRED_ERA_HUMIDITY_UNPHYSICAL")
        if not water_q_consistent:reasons.append("STAGE07_SITE_T_RH_QBOT_PHYSICS_INVALID")
        if not neighbor_good:reasons.append("ORIGINAL_STAGE07_NEIGHBOR_VPD_OR_RH_CONTINUITY_HOLD")
        preview.append({
         "native_time":stampstr,"original_tower_VPD_hPa":actual_orig,
         "official_original_source_VPD_QC":float(tower.at[time,"VPD_F_QC"]),
         "tower_T_C":actual_t,"ERA5_T_C":companion_t,"ERA5_RH_pct":float(era_rh),
         "selected_Stage07_VPD_hPa":current,
         "selected_Stage07_RH_pct":old["rh"],
         "selected_Stage07_QBOT_kgkg":q_existing,
         "paired_formula_QBOT_kgkg":old["q"],
         "neighbor_before_time":str(before),"neighbor_after_time":str(after),
         "neighbor_before_VPD_hPa":prev["vpd"],
         "neighbor_after_VPD_hPa":next_["vpd"],
         "neighbor_before_original_VPD_QC":float(tower.at[before,"VPD_F_QC"]),
         "neighbor_after_original_VPD_QC":float(tower.at[after,"VPD_F_QC"]),
         "neighbor_before_RH_pct":prev["rh"],"neighbor_after_RH_pct":next_["rh"],
         "edge_left_jump_hPa":left_jump,"edge_right_jump_hPa":right_jump,
         "physics_QBOT_PASS":water_q_consistent,
         "paired_ERA_RH_PASS":source_ok,
         "both_neighbor_VPD_and_RH_PASS":neighbor_good,
         "conditional_OPERATOR_ADOPTION":approved,
         "HOLD_reason":";".join(reasons)
        })
    # 2018 low-but-positive RH originally must not be imported from
    # separately changed Stage11h research source.
    protect=[]
    for stampstr,original in PRESERVE:
        time=pd.Timestamp(stampstr)
        if not(close(float(tower.at[time,"VPD_F"]),original,0.000501) and
               close(float(selected.at[time,"VPD_USE"]),float(tower.at[time,"VPD_F"]),1e-8)):
            raise RuntimeError("2018 original low-RH user-preserve requirement violated "+stampstr)
        row=manual.loc[time]
        if not close(float(row.official_qc),float(tower.at[time,"VPD_F_QC"]),1e-8):
            raise RuntimeError("2018 original raw source VPD QC changed "+stampstr)
        q=physics_at(time)
        if not q["physical"]:
            raise RuntimeError("Protected original 2018 VPD physically invalid; science hold needed "+stampstr)
        protect.append({
          "native_time":stampstr,"original_tower_VPD_hPa":original,
          "Stage07_selected_VPD_hPa":float(selected.at[time,"VPD_USE"]),
          "source_VPD_QC":float(tower.at[time,"VPD_F_QC"]),
          "computed_RH_pct":q["rh"],
          "decision":"PRESERVE_ORIGINAL_SOURCE_NO_CHANGE",
          "Stage11h_not_used":True})
    summary={
      "site":SITE,"version":VER,"original_stage07_sha256":sha(ORIGINAL),
      "source_original_tower_sha256":sha(source["primary"]),
      "source_original_ERA_sha256":sha(source["era"]),
      "operator_approved_three_conditional":3,
      "passed_science_adoptions":sum(bool(row["conditional_OPERATOR_ADOPTION"]) for row in preview),
      "held_candidate_events":sum(not bool(row["conditional_OPERATOR_ADOPTION"]) for row in preview),
      "original_2018_low_RH_protected_unchanged":2,
      "approved_2020_temperature_unchanged":True,
      "input_18y_noleap_rows":len(selected),
      "Stage07_2014_VPD_candidates_preexist_and_are_not_new_changes":True,
      "Stage11h_potential_2018_values_excluded":True,
      "postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
      "Slurm_jobs_submitted":False}
    return selected,pd.DataFrame(preview),pd.DataFrame(protect),summary

def apply(selected,review,preserved,summary,approval,prior):
    if int(summary["passed_science_adoptions"])==0:
        print("STAGE13M SCIENCE HOLD: all three fail source science; no independent forcing written",flush=True)
        return 3
    next_=selected.copy(deep=True)
    held=[]
    for row in review.to_dict("records"):
        t=pd.Timestamp(row["native_time"])
        if not row["conditional_OPERATOR_ADOPTION"]:
            next_.at[t,"VPD_USE"]=np.nan
            next_.at[t,"QBOT"]=np.nan
            held.append(row["native_time"])
    for t in [pd.Timestamp(t) for t,*_ in PRESERVE]:
        for key in ("VPD_USE","QBOT","TA_USE","TBOT","PSRF"):
            a=selected.at[t,key]
            b=next_.at[t,key]
            if not np.isclose(float(a),float(b),rtol=0,atol=1e-12):
                raise RuntimeError("2018 original source was changed during adoption")
    for key in selected.columns:
        if key in ("VPD_USE","QBOT"):
            p=pd.to_numeric(selected[key],errors="raise").to_numpy(float)
            n=pd.to_numeric(next_[key],errors="coerce").to_numpy(float)
            changed=~np.isclose(p,n,rtol=0,atol=1e-12,equal_nan=True)
            if any(next_.index[i] not in {pd.Timestamp(v) for v in held}
                   for i in np.flatnonzero(changed)):
                raise RuntimeError("Source edit outside explicitly held 2014 event at "+key)
        elif not selected[key].equals(next_[key]):
            raise RuntimeError("Unapproved original source variable modified: "+key)
    folder=ROOT/"science_trials"/("stage13m_Mpj_2014_three_approved_VPD_science_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    status=folder/"INCOMPLETE_RESEARCH_NOT_POSTV5_OR_DATM"
    status.write_text("Audit/export not final; not approved for DATM, model, Slurm.\n")
    next_.reset_index(drop=True).to_csv(folder/NAME,index=False,float_format="%.17g")
    back=pd.read_csv(file(folder/NAME),dtype={"time":str},low_memory=False)
    if (len(back)!=EXPECTED_ROWS or not back.time.equals(selected.time.reset_index(drop=True))):
        raise RuntimeError("Output 18-year source-native NOLEAP timeline altered")
    allcols=[c for c in next_.columns if c!="time"]
    for col in allcols:
        exp=pd.to_numeric(next_[col],errors="coerce").to_numpy(float)
        got=pd.to_numeric(back[col],errors="coerce").to_numpy(float)
        if not np.allclose(exp,got,rtol=1e-14,atol=1e-12,equal_nan=True):
            raise RuntimeError("Output source changed beyond CSV precision: "+col)
    review.to_csv(folder/"three_2014_native_science_adoption_and_HOLD_decisions.csv",index=False)
    preserved.to_csv(folder/"two_2018_original_low_RH_VPD_PRESERVED.csv",index=False)
    report={**summary,
       "research_shadow_created":True,
       "additional_numeric_2014_adoptions_vs_Stage07":0,
       "deliberately_unfilled_held_2014_timestamps":held,
       "new_research_shadow_humidity_missing":len(held),
       "original_selected_2018_source_unchanged":True,
       "science_state":"ONLY_EXACT_PASSED_STAGE07_VPD_CANDIDATES_ADOPTED_RESEARCH"}
    (folder/"stage13m_operator_science_audit.json").write_text(json.dumps(report,indent=2)+"\n")
    status.write_text(
       "Research-only Stage13m new immutable independent full NOLEAP input. "
       "Exact three 2014 records are ALREADY numerically present in signed Stage07. "
       "Only source-vetted proposals adopted; failed rows explicitly blanked VPD/QBOT. "
       "Original two Feb2018 very-low-RH values untouched, signed Stage11h "
       "which changed 2018 was NOT used. Stage13d 2020 TA approved 1.1795 retained. "
       "No Post-v5/DATM/CIME/AD400/Slurm or PFT/surface change.\n")
    files=[NAME,"three_2014_native_science_adoption_and_HOLD_decisions.csv",
           "two_2018_original_low_RH_VPD_PRESERVED.csv",
           "stage13m_operator_science_audit.json",status.name]
    receipt={
       "version":VER,"site":SITE,"operator_stage13m_decision_SHA256":sha(approval),
       "previous_stage13d_QC0_decision_SHA256":sha(prior),
       "original_Stage07_selected_SHA256":sha(ORIGINAL),
       "original_Stage07_unchanged":True,
       "original_three_numeric_candidates_already_in_selected_Stage07":True,
       "science_vetted_2014_VPD_adopted":int(summary["passed_science_adoptions"]),
       "source_HOLD_count":len(held),"two_2018_original_source_unchanged":True,
       "DATM_ready":False,"spinup_authorized":False,"postv5_approved":False,
       "files_SHA256":{p:sha(folder/p) for p in files}}
    (folder/"stage13m_original_source_SHA_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE13M ISOLATED RESEARCH SHADOW SUCCESS",folder,flush=True)
    print("2014 CONDITIONALLY APPROVED PASS",summary["passed_science_adoptions"],
          "HOLD",held,"2018 ORIGINAL LOW RH PRESERVED 2/2; 2020 ORIGINAL APPROVED TA PRESERVED",flush=True)
    print("STAGE07 EXISTING 2014 NUMERIC VPD REPAIR IS REUSED, NOT TRIPLE-COUNTED",flush=True)
    print("NO POSTV5, DATM, MODEL, SLURM, ORIGINAL SOURCE OR STAGE11H CHANGES",flush=True)

def main():
    parser=argparse.ArgumentParser()
    pick=parser.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","apply"):pick.add_argument("--"+name,action="store_true")
    parser.add_argument("--approval",type=Path)
    parser.add_argument("--prior-qc0-approval",type=Path)
    args=parser.parse_args()
    print("STAGE13M US-Mpj THREE 2014 VPD + TWO ORIGINAL 2018 SOURCE HOLDS | "+VER,flush=True)
    selftest()
    if args.self_test:return
    if args.approval is None or args.prior_qc0_approval is None:
        parser.error("--approval Stage13m JSON and --prior-qc0-approval Stage13d JSON needed")
    selected,review,preserved,summary=audit(args.approval,args.prior_qc0_approval)
    print("\n=== US-MPJ THREE CONDITIONAL 2014 VPD SCIENCE DECISIONS ===",flush=True)
    print(review.to_string(index=False,float_format=lambda x:f"{x:.6f}"),flush=True)
    print("\n=== PROTECTED FEB2018 ORIGINAL SOURCE VPD ===",flush=True)
    print(preserved.to_string(index=False,float_format=lambda x:f"{x:.6f}"),flush=True)
    print("\nSTAGE13M SUMMARY",json.dumps(summary,indent=2),flush=True)
    if args.check:
        print("STAGE13M READONLY CHECK PASS | source and all 5 manual identities verified, no writes",flush=True)
        return
    apply(selected,review,preserved,summary,args.approval,args.prior_qc0_approval)

if __name__=="__main__":
    try:main()
    except Exception as err:
        print("STAGE13M STOP:",err,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

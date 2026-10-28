#!/usr/bin/env python3
"""Stage13AA US-Me6: exact operator-approved Run12 2015 Sep26 4HH research shadow.

Requires original SHA-verified Stage13S, Stage13Z v3 report and exact
2026-10-28 user science approval. Changes only VPD_USE and thermodynamically
derived QBOT at four original QC1 halfhours in a NEW, complete, noleap CSV.
Original tower, Stage12AC and Stage13S remain immutable. Research-only;
never modifies DATM/CIME/model, Post-v5, Slurm or AD400.
"""
import argparse, hashlib, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13aa-v1-20261028-Me6-Run12-4HH-user-approved-linear"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S=ROOT/"science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105"
SF="US-Me6_STAGE13S_12x2015_QC1_235HH_ERA_RH_OPERATOR_APPROVED_RESEARCH_ONLY_NOLEAP.csv"
SREC="stage13s_Me6_operator_235HH_SHA_receipt.json"
SSHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
Z=ROOT/"reports/stage13z_Me6_run12_full_boundary_method_GATE_READONLY_20261028T160506Z_a3e87f28"
ZREC="stage13z_science_SHA_receipt.json"
ZNODES="six_native_2015_QC0_QC1_VPD_QBOT_method_COMPARISON.csv"
ZEDGE="five_original_full_boundary_steps_ERA_VS_QC0_linear.csv"
ZINFO="stage13z_run12_science_decision_ONLY.json"
ZVER="batch03-stage13z-v3-20261027-Me6-explicit-native-time-output"
APPROVAL_GIT_BLOB="a9d7275590eb4c7f4294d324583c2455b52abec0"
TIMES=pd.date_range("2015-09-26 05:00",periods=4,freq="30min")
ENDS=[pd.Timestamp("2015-09-26 04:30"),pd.Timestamp("2015-09-26 07:00")]
EXPECTED=[5.624,5.835,6.046,6.257]
ALLOWED={"VPD_USE","QBOT"}

def need(ok,msg):
    if not bool(ok):raise RuntimeError("STAGE13AA SOURCE/APPROVAL HOLD: "+msg)

def file(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p));return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for v in iter(lambda:f.read(1<<20),b""):h.update(v)
    return h.hexdigest()

def git_blob(path):
    b=file(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def es(temp):
    return 6.112*np.exp(17.67*float(temp)/(float(temp)+243.5))

def water(vpd,temp,pressure):
    v,t,p=float(vpd),float(temp),float(pressure)
    sv=es(t);vapor=(sv-v)*100.;den=p-.378*vapor
    q=.622*vapor/den if den!=0 else float("nan")
    valid=bool(np.isfinite([v,t,p,sv,q]).all() and 50000<p<110000
               and 0<v<sv and 0<q<.08 and den>0)
    return q, valid

def keys(col):
    t=pd.to_datetime(col.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12],
                     format="%Y%m%d%H%M",errors="raise")
    need(t.is_unique and t.is_monotonic_increasing,"original source chronology")
    need(len(t)==280320 and not ((t.dt.month==2)&(t.dt.day==29)).any(),
         "16 years NOLEAP row count")
    return pd.DatetimeIndex(t)

def selftest():
    need(len(TIMES)==4 and len(ENDS)==2 and np.allclose(
        np.linspace(5.413,6.468,6)[1:-1],EXPECTED,atol=1e-12,rtol=0),
        "approved 4HH interpolation identities")
    need(np.all(np.diff([5.413,*EXPECTED,6.468])<=4.0),
         "full five-boundary VPD gate")
    q,ok=water(5.835,10,95000)
    need(ok and 0<q<.08 and not water(-1,10,95000)[1],
         "QBOT from site T/P, no negative VPD")
    need(len(set(TIMES))==4 and set(TIMES).isdisjoint(ENDS),
         "exact scope source times")
    print("STAGE13AA SELF-TEST PASS | exact 4HH approval, native QC0 anchors, water; NO WRITES",flush=True)

def audited(approval_path):
    need(git_blob(approval_path)==APPROVAL_GIT_BLOB,
         "pinned user approval JSON blob changed")
    approval=json.loads(file(approval_path).read_text())
    scope=approval.get("approved_scope",{})
    restriction=approval.get("restriction",{})
    need(approval.get("schema")=="ameriflux-batch03-user-science-method-approval-v1"
         and approval.get("site")=="US-Me6"
         and approval.get("status")=="USER_APPROVED_METHOD_EXACT_FOUR_HALF_HOURS_NOT_MODEL_READY"
         and scope.get("original_run_id")==12
         and scope.get("source_native_times")==[str(t) for t in TIMES]
         and np.allclose(scope.get("approved_candidate_VPD_USE_hPa",[]),EXPECTED,rtol=0,atol=1e-10)
         and set(scope.get("allowed_fields_to_change",[]))==ALLOWED
         and scope.get("forbidden_fields_to_change")==["TA_USE","PSRF","time"]
         and restriction.get("scientific_method_approved_for_exact_four_HH_only") is True
         and restriction.get("research_shadow_application_allowed_subject_to_sha_and_diff_safety_checks") is True
         and not any(restriction.get(k) for k in ("promote_postv5","enable_DATM","allow_AD400","allow_Slurm")),
         "exact user scientific approval scope or exclusions changed")
    need(sha(S/SF)==SSHA
         and approval["source_verification"]["protected_stage13s_235HH_full_forcing_sha256"]==SSHA,
         "protected Stage13S successful 235HH forcing source changed")
    srec=json.loads(file(S/SREC).read_text())
    need(srec.get("site")=="US-Me6" and srec.get("approved_original_source_halfhours")==235
         and srec.get("existing_2017_Stage12ac_five_source_values_preserved") is True
         and srec.get("output_SHA256",{}).get(SF)==SSHA,
         "old Stage13S source receipt invalid")
    zr=json.loads(file(Z/ZREC).read_text())
    need(zr.get("version")==ZVER and zr.get("site")=="US-Me6"
         and zr.get("operator_approval") is False and zr.get("forcing_written") is False,
         "Stage13Z was not strictly diagnostic")
    znames={ZNODES,ZEDGE,ZINFO,"NO_OPERATOR_APPROVAL_NO_FORCING_REPAIR"}
    need(set(zr.get("outputs_SHA256",{}))==znames,
         "Stage13Z receipt output count drift")
    for n,digest in zr["outputs_SHA256"].items():
        need(sha(Z/n)==digest,"Stage13Z source comparison SHA mismatch "+n)
    zinfo=json.loads(file(Z/ZINFO).read_text())
    need(zinfo.get("version")==ZVER and zinfo.get("site")=="US-Me6"
         and zinfo.get("preserved_original_Stage13s_SHA256")==SSHA
         and zinfo.get("run_id")==12
         and zinfo.get("QC1_native_halfhours")==4
         and zinfo.get("true_QC0_native_bookends")==2
         and zinfo.get("QC0_linear_all_nodes_physically_valid") is True
         and zinfo.get("QC0_linear_method_status")=="HUMAN_REVIEW_ONLY_NOT_APPROVED"
         and zinfo.get("ERA_RH_full_boundary_method_status")=="REJECT_GT4HPA"
         and zinfo.get("QC0_linear_full_six_node_max_step_hPa")<=.211000001
         and zinfo.get("new_operator_approval") is False
         and zinfo.get("source_or_forcing_written") is False,
         "Stage13Z original science candidate/holding result drift")
    nodes=pd.read_csv(file(Z/ZNODES),dtype={"native_time":str},low_memory=False)
    edges=pd.read_csv(file(Z/ZEDGE),low_memory=False)
    need(len(nodes)==6 and len(edges)==5
         and list(pd.to_datetime(nodes.native_time))==[ENDS[0],*TIMES,ENDS[1]]
         and (nodes.original_tower_VPD_F_QC.to_numpy()==[0,1,1,1,1,0]).all()
         and (nodes.original_tower_TA_F_QC.iloc[1:5].to_numpy()==0).all()
         and np.allclose(nodes.full_edge_QC0_anchor_linear_VPD_hPa.iloc[1:5],
                         EXPECTED,rtol=0,atol=1e-10)
         and np.all(edges.QC0_linear_full_edge_le_4hPa.astype(str).str.lower()=="true")
         and np.all(edges.QC0_anchor_linear_VPD_step_hPa.astype(float)<=4),
         "original signed six source nodes/five boundaries differ")
    for i,ts in [(0,ENDS[0]),(5,ENDS[1])]:
        measured=float(nodes.iloc[i].original_tower_VPD_F_hPa)
        retained=float(nodes.iloc[i].unchanged_Stage13s_selected_VPD_hPa)
        approved=float(scope["protected_QC0_bookends"][0 if i==0 else 1]["original_measured_VPD_hPa"])
        need(str(scope["protected_QC0_bookends"][0 if i==0 else 1]["time"])==str(ts)
             and np.isclose(measured,retained,atol=1e-8,rtol=0)
             and np.isclose(measured,approved,atol=1e-8,rtol=0),
             "protected measured original QC0 bookend mismatch "+str(ts))
    base=pd.read_csv(file(S/SF),dtype={"time":str},low_memory=False)
    ind=keys(base.time)
    base.index=ind
    need(set(TIMES).issubset(ind) and set(ENDS).issubset(ind),"approved 2015 times absent")
    need(base.columns.is_unique and ALLOWED.issubset(set(base.columns))
         and {"TA_USE","PSRF"}.issubset(set(base.columns)),
         "selected forcing missing original variables")
    trial=base.copy(deep=True)
    ledger=[]
    for i,ts in enumerate(TIMES):
        row=nodes.iloc[i+1]
        old=base.loc[ts]
        need(np.isclose(float(old.TA_USE),float(row.retained_original_site_TA_USE_C),atol=1e-7,rtol=0)
             and np.isclose(float(old.PSRF),float(row.retained_original_PSRF_Pa),atol=1e-7,rtol=0)
             and np.isclose(float(old.VPD_USE),
                            float(row.unchanged_Stage13s_selected_VPD_hPa),
                            atol=1e-8,rtol=0,equal_nan=True)
             and np.isclose(float(old.QBOT),
                            float(row.unchanged_Stage13s_selected_QBOT_kgkg),
                            atol=1e-11,rtol=0,equal_nan=True),
             "original frozen Stage13S raw QC1 T/P/VPD/QBOT differs "+str(ts))
        candidate=float(EXPECTED[i])
        q,ok=water(candidate,float(old.TA_USE),float(old.PSRF))
        need(ok and np.isclose(q,float(row.full_edge_QC0_anchor_linear_QBOT_kgkg),
                               atol=1e-11,rtol=0,equal_nan=False),
             "candidate QBOT from original tower T/P disagrees with Stage13Z "+str(ts))
        trial.at[ts,"VPD_USE"]=candidate
        trial.at[ts,"QBOT"]=q
        ledger.append({"native_time":str(ts),"source_original_VPD_F_QC":1,
                       "before_VPD_USE_hPa":float(old.VPD_USE),
                       "approved_linear_VPD_USE_hPa":candidate,
                       "before_QBOT_kgkg":float(old.QBOT),"thermodynamic_QBOT_kgkg":q,
                       "source_TA_USE_C_unchanged":float(old.TA_USE),
                       "source_PSRF_Pa_unchanged":float(old.PSRF)})
    for boundary in ENDS:
        need(trial.loc[boundary].equals(base.loc[boundary]),
             "true QC0 boundary changed "+str(boundary))
    need(np.allclose([float(trial.at[t,"VPD_USE"]) for t in
                      [ENDS[0],*TIMES,ENDS[1]]],
                     [5.413,*EXPECTED,6.468],atol=1e-10,rtol=0),
         "all 5 source full boundary VPD jumps after approved patch")
    need(max(abs(np.diff([5.413,*EXPECTED,6.468])))<=4,
         "repaired source 30min VPD continuity >4hPa")
    summary_changes={}
    for col in base.columns:
        if col=="time":
            need(base[col].equals(trial[col]),"original NOLEAP native clock changed")
            continue
        first=pd.to_numeric(base[col],errors="raise").to_numpy(float)
        second=pd.to_numeric(trial[col],errors="raise").to_numpy(float)
        where=np.flatnonzero(~np.isclose(first,second,atol=1e-12,rtol=0,equal_nan=True))
        if col in ALLOWED:
            need(set(trial.index[where]).issubset(set(TIMES)),
                 "forbidden timestamp change in "+col)
            summary_changes[col]=len(where)
        else:need(len(where)==0,"forbidden variable modified "+col)
    need(summary_changes.get("VPD_USE")==4
         and 1<=summary_changes.get("QBOT",0)<=4,
         "expected exact four VPD and QBOT change count")
    return base,trial,pd.DataFrame(ledger),summary_changes

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for key in ("self-test","check","apply"):mode.add_argument("--"+key,action="store_true")
    p.add_argument("--approval",type=Path)
    args=p.parse_args()
    selftest()
    if args.self_test:return
    need(args.approval is not None,"exact user approval JSON path required")
    original,candidate,ledger,deltas=audited(args.approval)
    print("STAGE13AA EXACT APPROVED SOURCE SCIENCE PRECHECK PASS",json.dumps(
        {"site":"US-Me6","run_id":12,"approved_HH":4,"changed_cells":deltas,
         "protected_Stage13S_SHA":SSHA,"postv5":False,"DATM":False,"AD400":False,"Slurm":False}),
        flush=True)
    if args.check:
        print("STAGE13AA READONLY CHECK PASS | one four-HH Run12 method, NO WRITES",flush=True)
        return
    out=ROOT/"science_trials"/("stage13aa_Me6_Run12_4HH_QC0_LINEAR_APPROVED_RESEARCH_ONLY_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    marker=out/"INCOMPLETE_REPORT_DO_NOT_USE_AS_FORCING"
    marker.write_text("Stage13AA scientific trial incomplete; never attach to DATM.\n")
    target="US-Me6_STAGE13AA_Run12_4HH_APPROVED_QC0_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
    candidate.to_csv(out/target,index=False,float_format="%.17g")
    reopened=pd.read_csv(file(out/target),dtype={"time":str},low_memory=False)
    need(len(reopened)==len(original)
         and list(reopened.columns)==list(original.columns)
         and reopened.time.equals(original.time.reset_index(drop=True)),
         "approved CSV exact schema/native chronology readback mismatch")
    for column in original.columns:
        if column=="time":continue
        want=candidate[column].to_numpy(dtype=float)
        got=pd.to_numeric(reopened[column],errors="raise").to_numpy(float)
        need(np.allclose(want,got,rtol=1e-14,atol=1e-12,equal_nan=True),
             "new separate shadow CSV numeric roundtrip mismatch "+column)
    need(sha(S/SF)==SSHA,"old Stage13S source hash changed after write")
    ledger_name="four_original_QC1_operator_approved_QC0_linear_VPD_QBOT.csv"
    info="stage13aa_user_approved_run12_shadow_manifest.json"
    notice="RESEARCH_ONLY_NO_POSTV5_DATM_AD400_SLURM"
    ledger.to_csv(out/ledger_name,index=False,float_format="%.17g")
    manifest={"version":VER,"site":"US-Me6","user_approval_blob":APPROVAL_GIT_BLOB,
              "user_approval_SHA256":sha(args.approval),
              "immutable_prior_Stage13S_forcing_SHA256":SSHA,
              "signed_source_Stage13Z_receipt_SHA256":sha(Z/ZREC),
              "original_Run12_approved_times":[str(t) for t in TIMES],
              "approved_field_change_counts":deltas,"previous_235HH_preserved":True,
              "old_2017_Stage12AC_five_preserved":True,
              "other_unapproved_original_runs_still_HOLD":[14,15,16,17,18],
              "source_original_changed":False,"postv5":False,"DATM":False,
              "AD400":False,"Slurm":False}
    (out/info).write_text(json.dumps(manifest,indent=2)+"\n")
    (out/notice).write_text("USER-APPROVED EXACT FOUR 2015 SEP26 QC1 HALF-HOURS ONLY.\n"
        "Source science research shadow, not Post-v5, DATM or model input.\n"
        "No original source, prior Stage13S 235HH, Stage12AC 2017 five or "
        "other QC1/QC2 source times changed.\n")
    receipt={"version":VER,"site":"US-Me6","original_Stage13S_SHA256":SSHA,
             "operator_approved_4HH":True,"postv5":False,"DATM":False,
             "Slurm":False,"outputs_SHA256":{
                 n:sha(out/n) for n in (target,ledger_name,info,notice)}}
    (out/"stage13aa_run12_approved_shadow_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    marker.unlink()
    print("STAGE13AA RESEARCH SHADOW DIR:",out,flush=True)
    print("STAGE13AA APPROVED FOUR-HH RESEARCH SHADOW COMPLETE; NO POSTV5/DATM/AD400/SLURM",
          flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13AA SCIENCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

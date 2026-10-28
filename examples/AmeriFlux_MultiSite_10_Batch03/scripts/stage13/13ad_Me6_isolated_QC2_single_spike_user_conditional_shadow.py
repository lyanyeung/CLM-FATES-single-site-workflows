#!/usr/bin/env python3
"""US-Me6 Stage13AD: strict user-conditional ONE isolated 2017 QC2 spike trial.

Target 2017-07-04 12:00 exactly, left original QC2 source boundary of Run18.
The user asked to interpolate a single anomalous value IF both immediate
neighbors are normal. For this case, neighboring VPD sources have QC1,
NOT measured QC0, so verify the entire 5-point local physical/continuity
context and preserve this weaker provenance in the report. This is a new
research-only shadow, NOT production, and not approval for other QC2 or QC1.
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ad-v1-20261028-Me6-single-QC2-context-guard"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AC=ROOT/"reports/stage13ac_Me6_original_tower_ERA_prepost_14T_9edges_5runs_READONLY_20261028T163544Z_31baa0aa"
AC_REC="stage13ac_readonly_SHA_receipt.json"
AC_CSV="5_held_runs_start_end_2h_before_after_QC2_tower_ERA.csv"
AA=ROOT/"science_trials/stage13aa_Me6_Run12_4HH_QC0_LINEAR_APPROVED_RESEARCH_ONLY_20261028T162945Z_25df5b3a"
AA_CSV="US-Me6_STAGE13AA_Run12_4HH_APPROVED_QC0_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
AA_REC="stage13aa_run12_approved_shadow_SHA_receipt.json"
AA_SHA="0da1d24f9b84d4c4a126d9a9d39ed107023d24914ed9ab122a10de0345e8ee80"
STAGE13S_SHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
APPROVAL_BLOB="a8b70432719798b15898039d4a4e6600dc18f533"
TARGET=pd.Timestamp("2017-07-04 12:00:00")
TIMES=pd.date_range(TARGET-pd.Timedelta(hours=1),periods=5,freq="30min")
VALS=np.array([27.711,28.983,21.840,29.150,28.664],dtype=float)
QC=[1,1,2,1,1]
PROTECTED=[pd.Timestamp("2017-07-04 06:00:00")+i*pd.Timedelta(minutes=30) for i in range(5)]
SEP26=list(pd.date_range("2015-09-26 05:00:00",periods=4,freq="30min"))
def need(ok,why):
    if not bool(ok):raise RuntimeError("STAGE13AD SOURCE/POLICY HOLD: "+why)
def must(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),"missing/unsafe SHA source "+str(p));return p
def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for piece in iter(lambda:f.read(1<<20),b""):h.update(piece)
    return h.hexdigest()
def blob(p):
    data=must(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def es(t):
    return 6.112*np.exp(17.67*float(t)/(float(t)+243.5))
def water(v,t,p):
    v,t,p=float(v),float(t),float(p)
    e=(es(t)-v)*100
    den=p-.378*e
    q=.622*e/den if np.isfinite(den) and den!=0 else float("nan")
    return q,bool(np.isfinite([v,t,p,q]).all() and 50000<p<110000
                  and 0<v<es(t) and 0<q<.08 and den>0)
def keys(s):
    x=s.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12]
    k=pd.DatetimeIndex(pd.to_datetime(x,format="%Y%m%d%H%M",errors="raise"))
    need(k.is_unique and k.is_monotonic_increasing and len(k)==280320
         and not ((k.month==2)&(k.day==29)).any(),"immutable 16-y NOLEAP source keys")
    return k
def selftest():
    predict=(VALS[1]+VALS[3])/2.
    need(len(TIMES)==5 and np.isclose(predict,29.0665,rtol=0,atol=1e-10)
         and abs(predict-VALS[2])>6.0
         and np.max(abs(np.diff([VALS[0],VALS[1],predict,VALS[3],VALS[4]])))<=2.0,
         "synthetic isolation source 5-node VPD pattern")
    need(len(PROTECTED)==5 and not set(PROTECTED).intersection({TARGET})
         and not set(SEP26).intersection({TARGET}),"protected original approvals")
    need(water(predict,28.99,95000)[1],"candidate T/P water physics")
    print("STAGE13AD SELF-TEST PASS | single 12:00 QC2 gap, two original QC1 contextual anchors, no writes",flush=True)
def audit(approval_path):
    need(blob(approval_path)==APPROVAL_BLOB,"explicit user conditional source decision SHA changed")
    approval=json.loads(must(approval_path).read_text())
    d=approval.get("demonstrated_target_for_strict_trial",{})
    need(approval.get("site")=="US-Me6"
         and approval.get("schema")=="user-conditional-single-spike-science-review-policy-v1"
         and d.get("native_time")==str(TARGET)
         and d.get("original_VPD_QC")==2
         and abs(d.get("expected_single_point_linear_vpd_hPa")-29.0665)<1e-10
         and d.get("neighbor_vpd_qc")==[1,1]
         and approval.get("strict_constraints",{}).get("write_only_separate_research_shadow") is True
         and approval.get("strict_constraints",{}).get("postv5") is False,
         "user conditional science method / exact target drift")
    ac=json.loads(must(AC/AC_REC).read_text())
    expected={"14_exact_source_T_abnormal_original_tower_ERA_and_both_candidates.csv",
              "14_T_abnormal_2h_before_after_tower_ERA_original_candidate.csv",
              "9_unique_30min_VPD_jump_edges_original_vs_two_candidates.csv",
              "9_unique_jump_edges_2h_before_after_tower_ERA_original_candidate.csv",
              AC_CSV,"stage13ac_science_review_summary.json",
              "READONLY_NO_REPAIR_APPROVAL_OR_FORCING"}
    need(ac.get("site")=="US-Me6" and ac.get("source_or_forcing_written") is False
         and ac.get("new_science_approval") is False
         and set(ac.get("outputs_SHA256",{}))==expected,
         "Stage13AC original tower/ERA context receipt changed")
    for name,digest in ac["outputs_SHA256"].items():
        need("/" not in name and "\\" not in name and sha(AC/name)==digest,
             "original Stage13AC SHA drift "+name)
    info=json.loads(must(AC/"stage13ac_science_review_summary.json").read_text())
    need(info.get("Stage13AA_approved_4HH_shadow_SHA256")==AA_SHA
         and info.get("Stage13S_original_235HH_SHA256")==STAGE13S_SHA
         and info.get("unique_30min_jump_edges")==9
         and info.get("source_modified") is False,
         "source research provenance changed")
    prior=json.loads(must(AA/AA_REC).read_text())
    need(prior.get("site")=="US-Me6" and prior.get("operator_approved_4HH") is True
         and prior.get("original_Stage13S_SHA256")==STAGE13S_SHA
         and prior.get("postv5") is False and prior.get("DATM") is False
         and sha(AA/AA_CSV)==AA_SHA
         and prior.get("outputs_SHA256",{}).get(AA_CSV)==AA_SHA,
         "original Run12 approved 4HH shadow changed")
    source=pd.read_csv(must(AC/AC_CSV),dtype={"native_time":str},low_memory=False)
    source["native_time"]=pd.to_datetime(source.native_time,errors="raise")
    need(source.native_time.is_unique,"original five-run boundary context timestamps duplicate")
    records=source.set_index("native_time").loc[TIMES]
    need(len(records)==5 and np.allclose(records.tower_VPD_F_hPa_source,
                                        VALS,atol=1e-9,rtol=0)
         and records.tower_VPD_F_QC.astype(int).tolist()==QC,
         "actual original source five native VPD/QC records changed")
    need((records.tower_TA_F_QC.astype(int)==0).all(),
         "five original tower temperatures must be measured QC0")
    measured_t=records.tower_TA_F_C.to_numpy(float)
    site_v=records.after_APPROVED_Stage13AA_VPD_USE_hPa.to_numpy(float)
    companion_v=records.paired_ERA_VPD_ERA_hPa.to_numpy(float)
    need(np.isfinite(measured_t).all() and np.max(abs(np.diff(measured_t)))<=3.5
         and np.allclose(site_v,VALS,atol=1e-8,rtol=0),
         "neighbor site temperature/retained VPD differs from original 5-source time context")
    need(np.isclose(companion_v[2],VALS[2],atol=1e-8,rtol=0),
         "QC2 center selected field not from same-native companion ERA")
    for i in [0,1,3,4]:
        v,t=VALS[i],measured_t[i]
        need(np.isfinite(v) and 0<v<es(t),"flanking original QC1 VPD unphysical")
    # Require two stable original QC1 observations on EACH side of a
    # single QC2 center; no extra outliers or another missing value.
    need(abs(VALS[1]-VALS[0])<=2.0
         and abs(VALS[4]-VALS[3])<=2.0
         and abs(VALS[3]-VALS[1])<=1.0
         and abs(VALS[2]-.5*(VALS[1]+VALS[3]))>=4.0,
         "one isolated spike between otherwise locally consistent source QC1 values not established")
    old=pd.read_csv(must(AA/AA_CSV),dtype={"time":str},low_memory=False)
    old.index=keys(old.time)
    need(set(TIMES).issubset(old.index),"five native source points absent")
    need(np.allclose(old.loc[TIMES,"TA_USE"].to_numpy(float),measured_t,
                     atol=1e-7,rtol=0)
         and np.allclose(old.loc[TIMES,"VPD_USE"].to_numpy(float),VALS,
                         atol=1e-8,rtol=0),
         "research shadow original source native T or VPD changed")
    p=float(old.at[TARGET,"PSRF"]);v=float(.5*(VALS[1]+VALS[3]))
    q,valid=water(v,float(old.at[TARGET,"TA_USE"]),p)
    need(valid and all(water(VALS[i],measured_t[i],
                   float(old.at[TIMES[i],"PSRF"]))[1] for i in [0,1,3,4]),
         "original QC1 anchors or interpolated candidate physically invalid at tower T/P")
    full=[VALS[0],VALS[1],v,VALS[3],VALS[4]]
    need(np.max(abs(np.diff(full)))<=4.0,
         "all four local native 30-minute VPD transitions must be <=4hPa")
    trial=old.copy(deep=True)
    trial.at[TARGET,"VPD_USE"]=v
    trial.at[TARGET,"QBOT"]=q
    changed={}
    for col in old.columns:
        if col=="time":
            need(old[col].equals(trial[col]),"original time column changed")
            continue
        a=pd.to_numeric(old[col],errors="raise").to_numpy(float)
        b=pd.to_numeric(trial[col],errors="raise").to_numpy(float)
        ix=np.flatnonzero(~np.isclose(a,b,atol=1e-12,rtol=0,equal_nan=True))
        if col in ("VPD_USE","QBOT"):
            need(len(ix)==1 and old.index[ix[0]]==TARGET,
                 "only source exact 12:00 VPD/QBOT may differ "+col)
            changed[col]=1
        else:need(len(ix)==0,"forbidden forcing field modified "+col)
    for t in PROTECTED+SEP26:
        need(old.loc[t].equals(trial.loc[t]),
             "preexisting user approved 2015/2017 records not preserved")
    detail={"version":VER,"site":"US-Me6",
        "isolated_native_time":str(TARGET),
        "original_center_QC":2,
        "previous_two_original_VPD_QC":[1,1],
        "following_two_original_VPD_QC":[1,1],
        "all_five_native_tower_T_QC0":True,
        "original_measured_QC0_VPD_bookends":False,
        "original_neighbor_QC1_not_independent_observed_QC0":True,
        "original_five_VPD_hPa":VALS.tolist(),
        "original_tower_T_C":measured_t.tolist(),
        "original_companion_ERA_VPD_hPa":companion_v.tolist(),
        "old_center_VPD_hPa":float(VALS[2]),
        "approved_conditional_isolated_linear_VPD_hPa":v,
        "rederived_QBOT_kgkg":q,
        "max_corrected_native_5node_VPD_step_hPa":float(np.max(abs(np.diff(full)))),
        "changed_cells":{"VPD_USE":1,"QBOT":1},
        "parent_Stage13AA_SHA256":AA_SHA,
        "source_original_Stage13S_SHA256":STAGE13S_SHA,
        "Stage13AC_receipt_SHA256":sha(AC/AC_REC),
        "user_policy_SHA256":sha(approval_path),
        "all_other_original_QC2_immediate_boundaries_unchanged":True,
        "all_unapproved_Run14_18_QC1_centers_unchanged":True,
        "source_tower_and_original_ERA_unchanged":True,
        "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    return old,trial,detail
def main():
    a=argparse.ArgumentParser()
    group=a.add_mutually_exclusive_group(required=True)
    for key in ("self-test","check","apply"):group.add_argument("--"+key,action="store_true")
    a.add_argument("--policy",type=Path)
    args=a.parse_args()
    selftest()
    if args.self_test:return
    need(args.policy is not None,"operator conditional written policy JSON required")
    old,trial,detail=audit(args.policy)
    print("STAGE13AD FIVE SOURCE NODES / SINGLE ISOLATED CENTER",
          json.dumps(detail,indent=2),flush=True)
    if args.check:
        print("STAGE13AD READONLY EXACT SINGLE-POINT PRECHECK PASS | NO WRITES",flush=True)
        return
    folder=ROOT/"science_trials"/("stage13ad_Me6_isolated_originalQC2_Jul04_1200_QC1_anchor_trial_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    guard=folder/"INCOMPLETE_DO_NOT_USE_AS_MODEL_FORCING"
    guard.write_text("Candidate research shadow incomplete. Never attach to DATM.\n")
    name="US-Me6_STAGE13AD_SingleQC2_20170704_1200_QC1_Neighbors_RESEARCH_ONLY_NOLEAP.csv"
    trial.to_csv(folder/name,index=False,float_format="%.17g")
    reread=pd.read_csv(must(folder/name),dtype={"time":str},low_memory=False)
    need(len(reread)==len(trial) and reread.time.tolist()==old.time.tolist()
         and list(reread.columns)==list(trial.columns),
         "full site noleap CSV output failed exact time/schema readback")
    for col in trial.columns:
        if col=="time":continue
        a=trial[col].to_numpy(float);b=reread[col].to_numpy(float)
        need(np.allclose(a,b,rtol=1e-14,atol=1e-12,equal_nan=True),
             "new research CSV numeric readback differs "+col)
    need(sha(AA/AA_CSV)==AA_SHA,"immutable Stage13AA source changed after output")
    info="stage13ad_isolated_spike_science_and_approval_SCOPE.json"
    note="RESEARCH_ONLY_QC1_ANCHORS_NOT_OBSERVED_QC0_NO_DATM"
    (folder/info).write_text(json.dumps(detail,indent=2)+"\n")
    (folder/note).write_text("Site source QC2 center interpolated using source QC1 (NOT directly measured QC0) physically screened neighbors. This is a separate research shadow and does not approve any other QC1/QC2 values or spin-up.\n")
    rec={"version":VER,"site":"US-Me6","forcings_production_written":False,
         "separate_research_only_csv":True,
         "parent_Stage13AA_SHA256":AA_SHA,"output_SHA256":{
            n:sha(folder/n) for n in [name,info,note]}}
    (folder/"stage13ad_approved_conditional_trial_SHA_receipt.json").write_text(json.dumps(rec,indent=2)+"\n")
    guard.unlink()
    print("STAGE13AD SEPARATE RESEARCH SHADOW:",folder,flush=True)
    print("STAGE13AD ISOLATED ONE-HH CONDITIONAL RESEARCH SHADOW COMPLETE | NO POSTV5/DATM/AD400/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13AD SCIENCE HOLD:",e,file=sys.stderr,flush=True)
        traceback.print_exc();raise SystemExit(2)

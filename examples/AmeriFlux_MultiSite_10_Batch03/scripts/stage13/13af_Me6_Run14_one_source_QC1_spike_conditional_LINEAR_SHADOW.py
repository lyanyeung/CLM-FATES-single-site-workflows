#!/usr/bin/env python3
"""Stage13AF — one operator-conditionally allowed US-Me6 2015 Run14 QC1 spike.

Only native 2015-11-12 13:30 VPD_USE (3.501 -> 7.513 hPa) and source
site-TA_USE/PSRF recomputed QBOT. Source 2015-11-12 12:30..14:30 original
tower VPD sequence and both QC0-or-QC1 neighbors independently read from
signed Stage13AE report. All prior approved 2015 and 2017 records remain
unchanged. Creates only a new research-only shadow, not DATM/production.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13af-v1-20261028-Me6-20151112-1330-only-conditional-linear"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AE=ROOT/"reports/stage13ae_Me6_five_held_runs_source_isolated_spike_scan_READONLY_20261028T172442Z_911b2468"
AE_REC="stage13ae_readonly_sha_receipt.json"
AE_SUM="stage13ae_summary.json"
AE_ALL="all_Run14_18_original_source_5node_context_and_flags.csv"
AE_CAN="strict_isolated_source_spike_candidate_REVIEW_ONLY.csv"
AE_COUNTS="five_run_source_anomaly_decision_counts.csv"
AE_VER="batch03-stage13ae-v2-20261028-Me6-SHA-locked-full-Stage13S-explicit-source"
AD=ROOT/"science_trials/stage13ad_Me6_isolated_originalQC2_Jul04_1200_QC1_anchor_trial_20261028T170952Z_4ac00fee"
AD_CSV="US-Me6_STAGE13AD_SingleQC2_20170704_1200_QC1_Neighbors_RESEARCH_ONLY_NOLEAP.csv"
AD_REC="stage13ad_approved_conditional_trial_SHA_receipt.json"
AD_SHA="8ea065e690b35cdbf2722c436211ab43627dfdcb2e202f159be9d22a7396241b"
AA_SHA="0da1d24f9b84d4c4a126d9a9d39ed107023d24914ed9ab122a10de0345e8ee80"
S_SHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
T=pd.Timestamp("2015-11-12 13:30:00")
TIMES=pd.date_range(T-pd.Timedelta(hours=1),periods=5,freq="30min")
V=np.array([8.028,8.373,3.501,6.653,5.542],float)
ERA=np.array([np.nan,5.037,5.714,6.392,np.nan])
EXPECTED=7.513
ALLOWED={"VPD_USE","QBOT"}
ORIGINAL_PROTECTED=set(pd.date_range("2015-09-26 05:00",periods=4,freq="30min")) | \
    set(pd.date_range("2017-07-04 06:00",periods=5,freq="30min")) | \
    {pd.Timestamp("2017-07-04 12:00:00")}
def need(ok,m):
    if not bool(ok):raise RuntimeError("STAGE13AF SCIENCE SOURCE HOLD: "+m)
def f(path):
    p=Path(path)
    need(p.is_file() and not p.is_symlink(),"missing or symlink "+str(p))
    return p
def sha(path):
    h=hashlib.sha256()
    with f(path).open("rb") as x:
        for q in iter(lambda:x.read(1<<20),b""):h.update(q)
    return h.hexdigest()
def es(t):
    return 6.112*np.exp(17.67*float(t)/(float(t)+243.5))
def q(v,t,p):
    v,t,p=float(v),float(t),float(p)
    sat=es(t);vapor=(sat-v)*100;den=p-.378*vapor
    qb=.622*vapor/den if den!=0 else float("nan")
    good=bool(np.isfinite([v,t,p,sat,vapor,qb]).all() and
        50000<p<110000 and 0<v<sat and 0<qb<.08 and den>0)
    return qb,good
def idx(s):
    x=s.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12]
    z=pd.DatetimeIndex(pd.to_datetime(x,format="%Y%m%d%H%M",errors="raise"))
    need(z.is_unique and z.is_monotonic_increasing and len(z)==280320
      and not ((z.month==2)&(z.day==29)).any(),"original site NOLEAP chronology changed")
    return z
def selftest():
    need(len(TIMES)==5 and T==TIMES[2] and
      np.isclose((V[1]+V[3])/2,EXPECTED,rtol=0,atol=1e-10) and
      abs(V[2]-EXPECTED)>4 and
      np.max(abs(np.diff([V[0],V[1],EXPECTED,V[3],V[4]])))<4 and
      T not in ORIGINAL_PROTECTED,"one-source-spike regression and original approvals")
    need(q(EXPECTED,12,95000)[1] and not q(-1,12,95000)[1],
      "thermodynamic QBOT source")
    print("STAGE13AF SELF-TEST PASS | exactly 2015-11-12 13:30 QC1 center, five original VPD and immutable prior records; NO WRITES",flush=True)
def check():
    ar=json.loads(f(AE/AE_REC).read_text())
    exp={AE_SUM,AE_ALL,AE_CAN,AE_COUNTS,"NO_NEW_SOURCE_METHOD_APPROVAL_NO_FORCING_OR_MODEL"}
    need(ar.get("site")=="US-Me6" and ar.get("version")==AE_VER and
         ar.get("forcing_or_model_written") is False and
         set(ar.get("outputs_SHA256",{}))==exp,"signed AE source/receipt/version mismatch")
    for n,d in ar["outputs_SHA256"].items():
        need("/" not in n and "\\" not in n and sha(AE/n)==d,
             "AE evidence file SHA changed: "+n)
    summ=json.loads(f(AE/AE_SUM).read_text())
    need(summ.get("site")=="US-Me6" and
         summ.get("five_original_QC1_run_HH")==778 and
         summ.get("review_screened_source_centers")==793 and
         summ.get("new_strict_isolated_source_spike_REVIEW_candidates")==1 and
         summ.get("QC0_both_side_candidates")==0 and
         summ.get("QC1_or_mixed_neighbors_candidates")==1 and
         summ.get("Stage13AD_latest_shadow_sha256")==AD_SHA and
         summ.get("original_Stage13S_SHA256")==S_SHA and
         summ.get("candidate_operator_approval") is False and
         summ.get("source_or_forcing_written") is False,
         "13AE original independent 793/1 candidate source facts differ")
    ca=pd.read_csv(f(AE/AE_CAN),dtype={"native_time":str},low_memory=False)
    allr=pd.read_csv(f(AE/AE_ALL),dtype={"native_time":str},low_memory=False)
    need(len(ca)==1 and len(allr)==793 and
         ca.iloc[0].run_id==14 and ca.iloc[0].native_time==str(T) and
         ca.iloc[0].decision=="REVIEW_QC1_ANCHORED_SINGLE_SPIKE_NO_AUTO_APPROVAL" and
         ca.iloc[0].center_original_tower_VPD_QC==1 and
         ca.iloc[0].direct_measured_QC0_VPD_both_immediate_neighbors==False,
         "one exact QC1/anchors conditional source candidate not established")
    r=ca.iloc[0]
    v=np.array([r.before_60min_source_tower_VPD_hPa,
                r.before_30min_source_tower_VPD_hPa,
                r.center_source_tower_VPD_hPa,
                r.after_30min_source_tower_VPD_hPa,
                r.after_60min_source_tower_VPD_hPa],float)
    need(np.allclose(v,V,atol=1e-8,rtol=0) and
         np.allclose([r.before_30min_source_ERA_VPD_hPa,
                      r.center_source_ERA_VPD_hPa,
                      r.after_30min_source_ERA_VPD_hPa],
                     ERA[1:4],atol=1e-8,rtol=0) and
         np.isclose(r.hypothetical_one_center_interpolated_VPD_hPa,EXPECTED,atol=1e-10,rtol=0) and
         r.original_site_T_QC0_five_times_and_consistent==True and
         r.flanking_original_VPD_QC0_OR_QC1==True and
         r.flanking_tower_VPD_at_site_TP_water_physically_valid==True and
         r.flanking_tower_VPD_matches_selected==True and
         r.center_original_site_T_vs_ERA_GT8C==False and
         r.method_operator_approved_for_this_center==False,
         "original 5-point contextual QC/source/physics exception changed")
    fiveQC=np.array([float(x) for x in r.five_original_source_tower_VPD_QC.split(",")])
    tQC=np.array([float(x) for x in r.five_native_source_tower_TA_QC.split(",")])
    temps=np.array([float(x) for x in r.five_native_source_tower_TA_F_C.split(",")])
    need((tQC==0).all() and fiveQC[2]==1 and
         np.isin(fiveQC[[0,1,3,4]],[0,1]).all() and
         not (fiveQC[1]==0 and fiveQC[3]==0) and
         np.isfinite(temps).all() and np.max(abs(np.diff(temps)))<=3.5,
         "QC1/0 mixed anchors and reliable tower measured temperature")
    need(abs(V[1]-V[0])<=2 and abs(V[4]-V[3])<=2 and
         abs(V[3]-V[1])<=2 and abs(V[2]-EXPECTED)>=4 and
         np.max(abs(np.diff([V[0],V[1],EXPECTED,V[3],V[4]])))<=4,
         "full native source step/isolated-single-point science gate")
    prior=json.loads(f(AD/AD_REC).read_text())
    need(prior.get("site")=="US-Me6" and
         prior.get("separate_research_only_csv") is True and
         prior.get("forcings_production_written") is False and
         prior.get("parent_Stage13AA_SHA256")==AA_SHA and
         prior.get("output_SHA256",{}).get(AD_CSV)==AD_SHA and
         sha(AD/AD_CSV)==AD_SHA,"parent Stage13AD actual approved research source SHA differs")
    before=pd.read_csv(f(AD/AD_CSV),dtype={"time":str},low_memory=False)
    before.index=idx(before.time)
    need({"VPD_USE","QBOT","TA_USE","PSRF"}.issubset(before.columns) and
         set(TIMES).issubset(before.index),"original full site 2015 source columns/times unavailable")
    need(np.allclose(before.loc[TIMES,"VPD_USE"],V,rtol=0,atol=1e-8) and
         np.allclose(before.loc[TIMES,"TA_USE"],temps,rtol=0,atol=1e-7),
         "actual parent forcing differs from original signed VPD or tower temperature")
    for j in (0,1,3,4):
        need(q(V[j],temps[j],before.at[TIMES[j],"PSRF"])[1],
             "original neighbor invalid site thermodynamics")
    candidate,ok=q(EXPECTED,before.at[T,"TA_USE"],before.at[T,"PSRF"])
    need(ok and np.isclose(candidate,float(r.hypothetical_one_center_rederived_QBOT_kgkg),
                           rtol=0,atol=1e-11),
         "single-point operator-conditional QBOT differs from signed AE science")
    after=before.copy(deep=True)
    after.at[T,"VPD_USE"]=EXPECTED
    after.at[T,"QBOT"]=candidate
    change_counts={}
    for col in before.columns:
        if col=="time":
            need(before[col].equals(after[col]),"source time changed")
            continue
        a=pd.to_numeric(before[col],errors="raise").to_numpy(float)
        b=pd.to_numeric(after[col],errors="raise").to_numpy(float)
        change=set(before.index[~np.isclose(a,b,atol=1e-12,rtol=0,equal_nan=True)])
        if col in ALLOWED:
            need(change=={T},"new VPD/QBOT change must be single exact native time "+col)
            change_counts[col]=1
        else:need(not change,"forbidden model or original source field changed "+col)
    for protected in ORIGINAL_PROTECTED:
        need(before.loc[protected].equals(after.loc[protected]),
             "previous approval time changed "+str(protected))
    details={"version":VER,"site":"US-Me6","original_Run14_source_VPD_QC":1,
      "source_native_time":str(T),"original_full_run_id":14,
      "source_5_native_VPD_hPa":V.tolist(),"source_5_native_VPD_QC":fiveQC.tolist(),
      "source_5_native_TA_F_C":temps.tolist(),"source_5_native_TA_QC":tQC.tolist(),
      "original_ERA_3_native_VPD_hPa":ERA[1:4].tolist(),
      "left_right_VPD_QC0_bookends_both":False,
      "original_raw_source_T_and_P_unchanged":True,
      "original_VPD_hPa":3.501,"conditional_one_native_HH_linear_VPD_hPa":EXPECTED,
      "conditional_recomputed_QBOT_kgkg":candidate,
      "corrected_full_5_native_max_step_hPa":float(np.max(abs(np.diff([V[0],V[1],EXPECTED,V[3],V[4]])))),
      "change_counts":change_counts,"original_Stage13AD_SHA256":AD_SHA,
      "source_Stage13AE_receipt_SHA256":sha(AE/AE_REC),
      "Stage13S_original_forcing_SHA256":S_SHA,
      "2015_and_2017_previous_operator_approved_times_protected":True,
      "all_other_held_source_runs_HOLD":[14,15,16,17,18],
      "scope":"ONLY_SINGLE_QC1_RESEARCH_TRIAL_USING_USER_CONDITIONAL_RULE",
      "model_ready":False,"Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    return before,after,details
def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","apply"):mode.add_argument("--"+k,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    before,after,info=check()
    print("STAGE13AF SINGLE SOURCE ISOLATED SPIKE SCIENCE GATE PASS",
          json.dumps(info,indent=2),flush=True)
    if args.check:
        print("STAGE13AF READONLY PRECHECK PASS | exact Run14 13:30 original QC1 single spike, NO WRITES",flush=True)
        return
    out=ROOT/"science_trials"/("stage13af_Me6_20151112_1330_originalQC1_single_spike_RESEARCH_ONLY_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    incomplete=out/"INCOMPLETE_NO_MODEL_USE"
    incomplete.write_text("Not validated output; never use as DATM input.\n")
    fname="US-Me6_STAGE13AF_20151112_1330_Run14_oneQC1_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
    after.to_csv(out/fname,index=False,float_format="%.17g")
    reopened=pd.read_csv(f(out/fname),dtype={"time":str},low_memory=False)
    need(len(reopened)==len(before) and
         reopened.time.tolist()==before.time.tolist() and
         list(reopened.columns)==list(before.columns),"complete model original schema/time roundtrip")
    for c in before.columns:
        if c=="time":continue
        need(np.allclose(after[c].to_numpy(float),
                         pd.to_numeric(reopened[c],errors="raise").to_numpy(float),
                         rtol=1e-14,atol=1e-12,equal_nan=True),
             "full-site model CSV roundtrip changed "+c)
    need(sha(AD/AD_CSV)==AD_SHA,"parent source changed after write")
    info_name="stage13af_exact_one_QC1_isolated_source_spike_science_SCOPE.json"
    msg="RESEARCH_ONLY_QC1_OR_MIXED_NEIGHBORS_NOT_DOUBLE_OBS_QC0"
    (out/info_name).write_text(json.dumps(info,indent=2)+"\n")
    (out/msg).write_text("User conditionally authorized genuinely isolated anomalous source"
        " halfhours. This one Run14 2015-11-12 13:30 original QC1 center is"
        " repaired in a separate research-only shadow. Neighbor QC are 0 or 1;"
        " both QC0 observations are NOT established. All other held times"
        " and existing user approved earlier source values remain unchanged."
        " Postv5/DATM/AD400/Slurm NOT allowed.\n")
    receipt={"version":VER,"site":"US-Me6","original_Stage13AD_SHA256":AD_SHA,
             "separate_research_only_shadow":True,
             "source_or_production_forcing_written":False,
             "outputs_SHA256":{n:sha(out/n) for n in (fname,info_name,msg)}}
    (out/"stage13af_one_QC1_science_shadow_SHA_receipt.json").write_text(
         json.dumps(receipt,indent=2)+"\n")
    incomplete.unlink()
    print("STAGE13AF NEW RESEARCH SHADOW:",out,flush=True)
    print("STAGE13AF ONE EXACT Run14 QC1 RESEARCH SHADOW COMPLETE; NO POSTV5/DATM/AD400/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as err:
        print("STAGE13AF SCIENCE HOLD:",err,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage12ah — US-Kon operator-approved EXACT 23 QC1 isolated temperature
interpolations and one 2008-09-26 05:30 original VPD QC0 interpolation.

These 24 exact science decisions are the ONLY modifications in a NEW
SHA-sealed INCOMPLETE source-native full NOLEAP derivative; raw files and
prior Stage12g/12ae/12ag are never modified.
- 23 QC1 original TA_F spikes, verified EXACT immediate QC0 anchors:
  linear mean of observed original tower neighbor temperature, full precision.
  Replace BOTH TA_USE and TBOT. Hold VPD_USE/QBOT at those 23 rows until
  coherent native ERA-RH event remediation is separately approved.
- ONE abnormal observed original VPD QC0 at 2008-09-26 05:30:
  neighbor QC0 VPD 2.744/2.858 hPa -> interpolation 2.801 hPa.
  Original unchanged observed T/P; QBOT recomputed thermodynamically.
- All 34 original Stage12g Kon >4hPa VPD-jump centers remain science HOLDS.
- Other 10 QC1 original T context rows NOT approved, untouched.
No source timestamps, atmospheric clock, source QCs, other sites, DATM,
CIME or Slurm modified. No model-ready promotion.

--self-test is synthetic, no input or writes
--check verifies all source SHA, exact original QC and 24 changes, no writes
--apply identical checks then ONE isolated immutable science successor
"""
import argparse, hashlib, json, sys, traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
VERSION="batch03-stage12ah-v1-20261026-user-approved-Kon-23-T-and-one-QC0-VPD"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
AG=ROOT/"reports/stage12ag_Kon_35_original_T_QC_native_pm2h_repair_decision_20261026T023414Z_2f65dcb1"
AE=ROOT/"reports/stage12ae_all_42_pending_original_tower_ERA_ERA5Land_neighbors_20261026T011243Z_c5cc64fe"
S=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
SITE="US-Kon"
NAME="US-Kon_STAGE12G_INCOMPLETE_NOLEAP.csv"
AG_CONTEXT="175_Kon_center_pm2_native_halfhours_full_original_source_evidence.csv"
QC0="200809260530"
APPROVED_T=(
 "201102211130","201102220830","201102220930","201103150930",
 "201103151030","201103241230","201103241330","201103241430",
 "201103271030","201103271130","201103271230","201103300930",
 "201103311530","201104011030","201104071430","201104071530",
 "201110170730","201110180530","201110182130","201110190130",
 "201110190630","201110191130","201203050830")
OTHER_10=(
 "201105261000","201105261030","201109291730","201109291830",
 "201109291930","201110150630","201202251100","201202251130",
 "201208050930","201208051000")
VPD_NEIGHBORS=(2.744,2.858)
VPD_ORIGINAL=18.334
FMT="%Y%m%d%H%M"

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise ValueError("missing/symlink source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def esw(c):
    a=np.asarray(c,dtype=float)
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*a/(a+243.5))

def nat(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def adjacent(k,step):
    return (pd.to_datetime(k,format=FMT)+pd.Timedelta(minutes=30*step)).strftime(FMT)

def q_from_vpd(t,p,v):
    e=(float(esw(t))-float(v))*100.
    return .622*e/(p-.378*e)

def selftest():
    assert len(APPROVED_T)==23 and len(set(APPROVED_T))==23
    assert len(OTHER_10)==10 and not set(OTHER_10)&set(APPROVED_T)
    assert abs((sum(VPD_NEIGHBORS)/2)-2.801)<1e-12
    assert adjacent("200809260530",-1)=="200809260500"
    assert adjacent("200809260530",1)=="200809260600"
    assert abs((4.919+3.969)/2-4.444)<1e-12
    assert abs((5.465+6.044)/2-5.7545)<1e-12
    assert 0<q_from_vpd(16.141,100000,2.801)<.08
    print("STAGE12AH SELF-TEST PASS: exactly 23 T and 1 QC0 VPD approved, isolated science shadow; NO WRITES",flush=True)

def source():
    gr=json.loads(safe(G/"stage12g_research_only_sha_receipt.json").read_text())
    ag=json.loads(safe(AG/"stage12ag_original_science_report_SHA_receipt.json").read_text())
    ae=json.loads(safe(AE/"stage12ae_review_only_SHA_receipt.json").read_text())
    if not (gr.get("original_233_physics_holds_untouched") is True
            and gr.get("INCOMPLETE_marker_present") is True
            and gr.get("Postv5_approved")==0 and gr.get("DATM_ready")==0
            and gr.get("spinup_authorized")==0
            and sha(G/NAME)==gr["output_sha256"][NAME]):
        raise ValueError("Sealed original Stage12g Kon SHA/protective gate mismatch")
    if not(ag.get("Kon_34_jump_centers")==34
           and ag.get("Kon_1_protected_original_QC0")==1
           and ag.get("source_Stage12ae_SHA256")==sha(AE/"75_high_priority_cases_x_five_native_halfhours_all_three_source_comparisons.csv")
           and ag.get("Postv5_approved")==0 and ag.get("DATM_ready")==0
           and ag.get("spinup_authorized")==0
           and sha(AG/AG_CONTEXT)==ag["output_SHA256"][AG_CONTEXT]
           and ae.get("pending_human_review")==42
           and ae.get("source_G_receipt_SHA256")==sha(G/"stage12g_research_only_sha_receipt.json")):
        raise ValueError("Verified original Stage12ag/12ae provenance changed")
    m=json.loads(safe(S/"exact_input_manifest.json").read_text())
    spec=next(x for x in m["sites"] if x["site"]==SITE)
    pins={str(Path(p).resolve()):h for p,h in m["input_sha256"].items()}
    raw=safe(spec["primary"])
    if sha(raw)!=pins.get(str(raw.resolve())):
        raise ValueError("Published original Kon tower source SHA changed")
    return raw,gr,ag

def audit():
    rawpath,gr,ag=source()
    orig=pd.read_csv(safe(G/NAME),dtype={"time":str},low_memory=False)
    cols=list(orig.columns)
    if not {"time","TA_USE","TBOT","PSRF","VPD_USE","QBOT"}<=set(cols):
        raise ValueError("Full original Kon Stage12g forcing columns incomplete")
    keys=nat(orig.time)
    if keys.duplicated().any():raise ValueError("Original Kon native timestamps duplicated")
    ix={k:i for i,k in enumerate(keys)}
    need=set(APPROVED_T)|{QC0}|set(OTHER_10)
    for k in APPROVED_T:
        need|={adjacent(k,-1),adjacent(k,1)}
    need|={adjacent(QC0,-1),adjacent(QC0,1)}
    if not need<=set(ix):raise ValueError("Original Kon NOLEAP missing approved source keys")
    rawcols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    rr=pd.read_csv(rawpath,usecols=rawcols,dtype={"TIMESTAMP_START":str},
                   low_memory=False)
    rr=rr.loc[rr.TIMESTAMP_START.isin(need)].copy()
    if rr.TIMESTAMP_START.duplicated().any() or set(rr.TIMESTAMP_START)!=need:
        raise ValueError("Original Kon signed source missing/duplicate event or anchor")
    rr.set_index("TIMESTAMP_START",inplace=True)
    preview=pd.read_csv(safe(AG/AG_CONTEXT),
                        dtype={"TIMESTAMP_START":str},low_memory=False)
    preview=preview.loc[preview.site.eq(SITE)&preview.TIMESTAMP_START.isin(need)].copy()
    if not need<=set(preview.TIMESTAMP_START):
        raise ValueError("Original Stage12ag 175-row source preview missing approved source keys")
    for k,subset in preview.groupby("TIMESTAMP_START"):
        for c in ("TA_F","TA_F_QC","VPD_F","VPD_F_QC"):
            nums=pd.to_numeric(subset[c],errors="coerce").to_numpy(dtype=float)
            nums[nums<=-9990]=np.nan
            if not np.allclose(nums,nums[0],atol=1e-8,rtol=0,equal_nan=True):
                raise ValueError("Original 35 event overlapping source evidence inconsistent "+k+" "+c)
            if not np.isclose(float(rr.loc[k,c]),nums[0],atol=1e-5,rtol=0,equal_nan=True):
                raise ValueError("Original Stage12ag source transcript changed "+k+" "+c)
    selected=orig.copy(deep=True)
    changes=[]
    for k in APPROVED_T:
        j=ix[k]
        a,b=adjacent(k,-1),adjacent(k,1)
        mid=rr.loc[k];lo=rr.loc[a];hi=rr.loc[b]
        if not (int(mid.TA_F_QC)==1 and int(lo.TA_F_QC)==0 and int(hi.TA_F_QC)==0):
            raise ValueError("User-approved 23 source T QC1 / adjacent QC0 evidence changed "+k)
        old=float(mid.TA_F)
        low=float(lo.TA_F);high=float(hi.TA_F)
        fresh=(low+high)/2.
        if (not np.isfinite([old,low,high,fresh]).all()
            or abs(old-fresh)<5
            or not np.isclose(float(orig.TA_USE.iat[j]),old,atol=1e-7,rtol=0)
            or not np.isclose(float(orig.TBOT.iat[j]),old+273.15,atol=1e-6,rtol=0)):
            raise ValueError("Operator approved Kon isolated spike no longer matches source "+k)
        # Source VPD/QBOT is not automatically transferable after changing T.
        # Explicitly hold BOTH until a separately approved full episode RH step.
        selected.loc[j,"TA_USE"]=fresh
        selected.loc[j,"TBOT"]=fresh+273.15
        selected.loc[j,"VPD_USE"]=np.nan
        selected.loc[j,"QBOT"]=np.nan
        changes.append({
           "site":SITE,"native_key":k,
           "original_source_TA_F_QC":int(mid.TA_F_QC),
           "previous_native_key":a,"next_native_key":b,
           "previous_source_TA_F_QC":int(lo.TA_F_QC),
           "next_source_TA_F_QC":int(hi.TA_F_QC),
           "previous_source_measured_T_C":low,
           "original_source_QC1_T_C":old,
           "next_source_measured_T_C":high,
           "user_approved_interpolated_T_C":fresh,
           "original_G_VPD_USE_hPa":float(orig.VPD_USE.iat[j]),
           "new_VPD_USE_hPa":np.nan,
           "original_G_QBOT_kgkg":float(orig.QBOT.iat[j]),
           "new_QBOT_kgkg":np.nan,
           "operator_approved_temperature":True,
           "new_humidity_replacement_approved":False})
    idxqc=ix[QC0]
    prior,nextt=adjacent(QC0,-1),adjacent(QC0,1)
    qraw=rr.loc[QC0];left=rr.loc[prior];right=rr.loc[nextt]
    if not (int(qraw.VPD_F_QC)==0 and
            int(left.VPD_F_QC)==0 and int(right.VPD_F_QC)==0 and
            int(qraw.TA_F_QC)==0 and
            all(int(rr.loc[k,"TA_F_QC"])==0 for k in (prior,nextt)) and
            np.isclose(float(qraw.VPD_F),VPD_ORIGINAL,atol=1e-8,rtol=0) and
            np.isclose(float(left.VPD_F),VPD_NEIGHBORS[0],atol=1e-8,rtol=0) and
            np.isclose(float(right.VPD_F),VPD_NEIGHBORS[1],atol=1e-8,rtol=0) and
            pd.isna(orig.VPD_USE.iat[idxqc]) and pd.isna(orig.QBOT.iat[idxqc]) and
            np.isclose(float(orig.TA_USE.iat[idxqc]),float(qraw.TA_F),
                       atol=1e-8,rtol=0)):
        raise ValueError("Protected original Kon QC0 observed 2008 exceptional source changed")
    vp=(float(left.VPD_F)+float(right.VPD_F))/2
    press=float(orig.PSRF.iat[idxqc])
    t=float(orig.TA_USE.iat[idxqc])
    vapor=float(esw(t))-vp
    q=q_from_vpd(t,press,vp)
    if not(0<vp<float(esw(t)) and 50000<press<110000 and
           vapor>0 and 0<q<.08):
        raise ValueError("QC0 exceptional interpolated VPD and paired QBOT physics invalid")
    selected.loc[idxqc,"VPD_USE"]=vp
    selected.loc[idxqc,"QBOT"]=q
    qchange=pd.DataFrame([{
        "site":SITE,"native_key":QC0,"source_VPD_F_QC":0,
        "source_TA_F_QC":0,"native_before":prior,"native_after":nextt,
        "before_QC0_VPD_hPa":float(left.VPD_F),
        "original_anomalous_QC0_VPD_hPa":float(qraw.VPD_F),
        "after_QC0_VPD_hPa":float(right.VPD_F),
        "approved_interpolated_VPD_hPa":vp,
        "unchanged_tower_T_C":t,"unchanged_site_PSRF_Pa":press,
        "approved_recalculated_QBOT_kgkg":q,
        "before_G_VPD_missing":True,"before_G_QBOT_missing":True,
        "operator_explicit_QC0_exception_approved":True}])
    allowed=set(APPROVED_T)|{QC0}
    mask=keys.isin(allowed).to_numpy(dtype=bool)
    for col in cols:
        if col not in ("TA_USE","TBOT","VPD_USE","QBOT"):
            if not orig[col].equals(selected[col]):
                raise ValueError("Unapproved Kon other model input changed: "+col)
        else:
            if not np.array_equal(orig.loc[~mask,col].to_numpy(dtype=float),
                                  selected.loc[~mask,col].to_numpy(dtype=float),
                                  equal_nan=True):
                raise ValueError("Unapproved Kon off-target T/humidity changed: "+col)
    for k in OTHER_10:
        j=ix[k]
        if not np.array_equal(orig.iloc[j].to_numpy(),selected.iloc[j].to_numpy(),equal_nan=True):
            raise ValueError("Unapproved 10 other QC1 source T changed "+k)
    protected_34=sorted(set(preview.loc[(preview.relative_halfhours==0)&
             (preview.center_reason=="HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"),
             "center_native_key"].astype(str)))
    if len(protected_34)!=34:
        # Complete 175 original science transcript, filtered only to keys
        # may not contain ALL centers. Fall back to all original AG context.
        full=pd.read_csv(safe(AG/AG_CONTEXT),
                    dtype={"center_native_key":str},low_memory=False)
        protected_34=sorted(set(full.loc[full.center_reason.eq(
                     "HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"),"center_native_key"]))
    if not(len(protected_34)==34 and all(pd.isna(orig.VPD_USE.iat[ix[k]])
                and pd.isna(selected.VPD_USE.iat[ix[k]]) for k in protected_34)):
        raise ValueError("34 original Kon VPD physical center holds unexpectedly released")
    return selected,pd.DataFrame(changes),qchange,{"original_G_sha256":sha(G/NAME),
            "stage12ag_science_source_SHA256":sha(AG/AG_CONTEXT)}

def main():
    parser=argparse.ArgumentParser()
    g=parser.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","apply"):g.add_argument("--"+k,action="store_true")
    args=parser.parse_args()
    print("STAGE12AH USER-APPROVED EXACT 23 Kon QC1 T + ONE OBSERVED QC0 VPD | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    result,temps,qc0,provenance=audit()
    print("\n====== 23 OPERATOR APPROVED US-KON QC1 T INTERPOLATIONS =====",flush=True)
    print(temps[["native_key","previous_source_measured_T_C",
       "original_source_QC1_T_C","next_source_measured_T_C",
       "user_approved_interpolated_T_C",
       "original_G_VPD_USE_hPa","new_VPD_USE_hPa"]].to_string(index=False),flush=True)
    print("\n====== ONE OPERATOR APPROVED SOURCE VPD QC0 PHYSICAL OUTLIER =====",flush=True)
    print(qc0.to_string(index=False),flush=True)
    new_missing=int(result.VPD_USE.isna().sum())
    old=pd.read_csv(G/NAME,usecols=["VPD_USE"])
    original_missing=int(old.VPD_USE.isna().sum())
    print("STAGE12AH SUMMARY: 23 T corrected, 1 QC0 VPD repaired, 34 OTHER Kon VPD center HOLDS preserved; VPD missing old",original_missing,"new",new_missing,"(new humidity gap count may rise until ERA-RH episode reconstruction)",flush=True)
    if args.check:
        print("STAGE12AH CHECK ONLY: ZERO WRITES.",flush=True);return
    out=ROOT/"science_trials"/("stage12ah_USER_APPROVED_Kon_23_T_one_QC0_VPD_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={
      "US-Kon_STAGE12AH_APPROVED_23T_QC0VPD_INCOMPLETE_NOLEAP.csv":result,
      "23_user_approved_original_native_T_interpolations.csv":temps,
      "one_user_approved_original_QC0_VPD_observation_exception.csv":qc0}
    for name,f in outputs.items():f.to_csv(out/name,index=False)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
      "US-Kon 23 user-approved original TA_F_QC1 isolated T spikes interpolated from "
      "exact previous+next measured QC0 half-hour sources (new TA_USE/TBOT). "
      "The 23 corresponding VPD_USE and QBOT are science HOLD to prevent "
      "physically inconsistent mixed T/VPD forcing until humidity episodes are approved. "
      "One explicit observed original VPD QC0 exception 2008-09-26 05:30 "
      "interpolated from QC0 neighbors; QBOT recomputed at unchanged measured "
      "tower T/P. Remaining 34 stage12g Kon source humidity center HOLDS and "
      "other 10 QC1 temperature review records untouched. Source files and "
      "Stage12g original preserved, no Post-v5/DATM/CIME/Slurm/spinup permission.\n")
    files=[*outputs,"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"]
    digest={name:sha(out/name) for name in files}
    (out/"stage12ah_approved_23T_QC0_SHA_receipt.json").write_text(
      json.dumps({"version":VERSION,"approved_T_count":23,
         "approved_original_QC0_VPD_exception_count":1,
         "all_34_original_stage12g_vpd_jumps_still_HOLD":True,
         "other_10_QC1_temperature_records_unchanged":True,
         "humidity_event_ERA_RH_repair_approved":False,
         "original_source_and_G_immutable":True,
         "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
         "input_SHA256":provenance,"output_SHA256":digest},indent=2)+"\n")
    print("STAGE12AH VERIFIED USER-APPROVED NEW DERIVATIVE DIR:",out,flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AH STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

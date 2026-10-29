#!/usr/bin/env python3
"""US-MOz operator's QC-aware Jan2005 27HH LEFT EDGE, isolated one-hour scenario.

Actual original QC: 2005-01-05 19:00 / 19:30 / 20:00 are TA_F_QC1
and VPD_F_QC1. Thus the 19:30 -> 20:00 5.884515 C T jump is
QC1->QC1, NOT QC0->QC1. Operator requests QC-class-matched
interpolation. Change ONLY 19:30 T and actual vapor e by linear
interpolation between untouched 19:00 QC1 and newly rebuilt
20:00 ERA5-Land research scenario; regenerate VPD/TBOT/QBOT at site
PSRF and assert 18y coupled vapor physics.

Actual right 2005-01-06 09:00 QC1 -> 09:30 QC2: keep original
because 1.44586 C / .009262 hPa joined values already pass.

Original FLUXMET, Stage13L approved 40HH, Stage14F actual 27HH and
all historical inputs unchanged. RESEARCH SENSITIVITY ONLY; NOT
OBSERVATIONALLY VALIDATED, POST-V5, DATM, AD400 OR SLURM APPROVED.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="US-MOz-QC1-1HH-operator-interpolate-T-e-v1-20261029"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
P=ROOT/"science_trials/US_MOz_Jan2005_first27_REANALYSIS_SENSITIVITY_20261029T041812Z_f629fa16"
L=ROOT/"science_trials/stage13l_US_MOz_40HH_user_approved_CDSEra5Land_20261026T193902Z_95631db8"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
PFILE="US-MOz_315360_research_ONLY_27_and_previous40.csv"
PRECEIPT="US_MOz_27_research_SHA_receipt.json"
LFILE="US-MOz_CLM_forcing_2004_2021_STG13L_40HH_REANALYSIS_SHADOW.csv"
LRECEIPT="stage13l_MOz_40HH_science_SHA_receipt.json"
COLS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
LEFT=pd.Timestamp("2005-01-05 19:00")
MID=pd.Timestamp("2005-01-05 19:30")
RIGHT=pd.Timestamp("2005-01-05 20:00")
R_END=pd.Timestamp("2005-01-06 09:00")
R_NEXT=pd.Timestamp("2005-01-06 09:30")
OLD40A=pd.Timestamp("2005-01-06 14:00")
OLD40B=pd.Timestamp("2005-01-07 09:30")

def require(x,reason):
    if not bool(x):
        raise RuntimeError("US-MOz 14G FAIL CLOSED: "+reason)
def safe(f):
    f=Path(f);require(f.is_file() and not f.is_symlink(),"missing signed source "+str(f))
    return f
def sha(f):
    h=hashlib.sha256()
    with safe(f).open("rb") as z:
        for b in iter(lambda:z.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def es(t):
    return 6.112*np.exp(17.67*np.asarray(t,float)/(np.asarray(t,float)+243.5))
def q(e,p):
    return .622*100*e/(p-.378*100*e)
def test():
    require(RIGHT-LEFT==pd.Timedelta(hours=1) and
            MID-LEFT==pd.Timedelta(minutes=30) and
            len(pd.date_range("2005-01-05 20:00","2005-01-06 09:00",
                              freq="30min"))==27 and
            es(-10)>0,"self test source times and saturation")
    print("US-MOz QC1 INTERPOLATION SELF-TEST PASS",flush=True)
def checked_source():
    pr=json.loads(safe(P/PRECEIPT).read_text())
    lr=json.loads(safe(L/LRECEIPT).read_text())
    require(pr.get("version")=="US-MOz-Jan2005-27QC1-reanalysis-numeric-sensitivity-v1-20261029"
            and pr.get("science_admission") is False and
            pr.get("source_Stage13L")==sha(L/LFILE),
            "actual Stage14F research source or parent lineage differs")
    require(lr.get("version")=="batch03-stage13l-v2-20261026-numpy-physical-gate-safe"
            and lr.get("operator_approved_source_native_events_modified")==40
            and lr.get("original_first27_and_Jan09_unchanged") is True
            and lr.get("Postv5_approved") is False
            and lr.get("DATM_ready") is False,
            "actual previous 40HH operator approval changed")
    for root,rec in ((P,pr),(L,lr)):
        require(bool(rec.get("output_SHA256")),"source receipt output missing")
        for name,h in rec["output_SHA256"].items():
            require(sha(root/name)==h,"signed parent output SHA mismatch "+name)
    m=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    site=[x for x in m["sites"] if x["site"]=="US-MOz"]
    require(len(site)==1 and int(site[0]["native_minutes"])==30,
            "exact original MOz release missing/clock altered")
    src=site[0]["primary"]
    require(sha(src)==m["input_sha256"][str(Path(src).resolve())],
            "original source tower FLUXMET SHA changed")
    original=pd.read_csv(src,usecols=["TIMESTAMP_START","TA_F_QC","VPD_F_QC"],
                         dtype={"TIMESTAMP_START":str},low_memory=False)
    keys=[t.strftime("%Y%m%d%H%M") for t in (LEFT,MID,RIGHT,R_END,R_NEXT)]
    focus=original.loc[original.TIMESTAMP_START.isin(keys)].copy()
    require(len(focus)==5 and focus.TIMESTAMP_START.is_unique,
            "five exact raw source boundary observations not found")
    focus=focus.set_index("TIMESTAMP_START")
    expected_tqc=[1,1,1,1,2]
    expected_vqc=[1,1,1,1,2]
    for ts,a,b in zip(keys,expected_tqc,expected_vqc):
        require(int(focus.at[ts,"TA_F_QC"])==a and
                int(focus.at[ts,"VPD_F_QC"])==b,
                "actual source quality differs from QC-aware operator decision "+ts)
    return focus

def assess():
    original_qc=checked_source()
    x=pd.read_csv(P/PFILE,dtype={"time":str},low_memory=False)
    require(len(x)==315360 and list(x.columns)==COLS,
            "full Stage14F selected forcing 315360x10 schema changed")
    idx=pd.to_datetime(x.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    exp=pd.date_range("2004-01-01","2021-12-31 23:30",freq="30min")
    exp=exp[~((exp.month==2)&(exp.day==29))]
    require(len(exp)==315360 and
            np.array_equal(idx.to_numpy(),exp.to_numpy()),
            "original 18-year NOLEAP source time differs")
    x.index=idx
    # Confirm original source before operation and signed 27 edited slots.
    require(int(x.loc[[LEFT,MID,RIGHT],"TA_USE"].notna().sum())==3,
            "missing original QC1 T data")
    before=(x.loc[[LEFT,MID,RIGHT,R_END,R_NEXT],COLS]).copy()
    orig_event=x.loc[pd.date_range(RIGHT,R_END,freq="30min"),COLS].copy()
    source40=x.loc[pd.date_range(OLD40A,OLD40B,freq="30min"),COLS].copy()
    require(len(orig_event)==27 and len(source40)==40,
            "previous signed 27+40 numeric research scope changed")
    left=x.loc[LEFT]
    right=x.loc[RIGHT]
    tL=float(left.TA_USE);tR=float(right.TA_USE)
    vL=float(left.VPD_USE);vR=float(right.VPD_USE)
    eL=float(es(tL)-vL);eR=float(es(tR)-vR)
    # Linear midpoint in TEMPERATURE and ACTUAL VAPOUR PRESSURE, not VPD:
    # VPD must be derived at the new temperature, then QBOT at site PSRF.
    tM=(tL+tR)/2
    eM=(eL+eR)/2
    vM=float(es(tM)-eM)
    pressure=float(x.at[MID,"PSRF"])
    qM=float(q(eM,pressure))
    require(np.isfinite([tM,eM,vM,pressure,qM]).all() and
            -80<tM<65 and 50000<pressure<110000 and
            eL>0 and eR>0 and eM>0 and
            0<=vM<float(es(tM)) and 0<qM<.08,
            "QC1-to-QC1 interpolated e or T produces physically invalid VPD/QBOT")
    y=x.copy(deep=True)
    for col,val in (("TA_USE",tM),("TBOT",tM+273.15),
                    ("VPD_USE",vM),("QBOT",qM)):
        y.at[MID,col]=val
    # Verify no data changes anywhere outside one native 30min.
    for col in COLS:
        if col not in ("TA_USE","TBOT","VPD_USE","QBOT"):
            require(x[col].equals(y[col]),"non-approved source variable altered "+col)
        else:
            require(x.loc[x.index!=MID,col].equals(y.loc[y.index!=MID,col]),
                    "original 315360 source values altered outside exact QC1 midpoint "+col)
    require(y.loc[pd.date_range(RIGHT,R_END,freq="30min"),COLS].equals(orig_event),
            "previous 27 native scenario source records changed")
    require(y.loc[pd.date_range(OLD40A,OLD40B,freq="30min"),COLS].equals(source40),
            "original operator-approved 40 source records changed")
    t=y.TA_USE.to_numpy(float);p=y.PSRF.to_numpy(float);v=y.VPD_USE.to_numpy(float)
    ea=es(t)-v;qc=q(ea,p)
    complete=np.logical_and.reduce([np.isfinite(pd.to_numeric(y[c],errors="raise")
                                                .to_numpy(float)) for c in COLS[1:]])
    closure=(complete&(v>=0)&(ea>0)&(v<es(t))&
             (p>50000)&(p<110000)&
             np.isclose(qc,y.QBOT.to_numpy(float),rtol=1e-6,atol=1e-8)&
             np.isclose(y.TBOT.to_numpy(float),t+273.15,rtol=0,atol=1e-8))
    require(bool(closure.all()),"full 315360 coupled T/VPD/QBOT closure failed")
    local=[]
    for a,b in ((LEFT,MID),(MID,RIGHT),(R_END,R_NEXT)):
        at=y.loc[a];bt=y.loc[b]
        dt=abs(float(bt.TA_USE)-float(at.TA_USE))
        dv=abs(float(bt.VPD_USE)-float(at.VPD_USE))
        local.append(dict(left=str(a),right=str(b),
                 original_T_left=float(x.at[a,"TA_USE"]),
                 original_T_right=float(x.at[b,"TA_USE"]),
                 corrected_T_left=float(at.TA_USE),corrected_T_right=float(bt.TA_USE),
                 corrected_dT_abs_C=dt,corrected_dVPD_abs_hPa=dv,
                 T_boundary_gt4C=bool(dt>4),VPD_boundary_gt4hPa=bool(dv>4),
                 physical_source_observed=False,scientific_approval=False))
    edge=pd.DataFrame(local)
    require(not edge.T_boundary_gt4C.any() and
            not edge.VPD_boundary_gt4hPa.any(),
            "QC-aware interpolation did not close all three 30min joins <=4")
    changed=pd.DataFrame([dict(native_time=str(MID),method=
         "QC1_ON_BOTH_SIDES_linear_T_and_actual_e_only_at_19_30",
         raw_left_T_QC=int(original_qc.at[LEFT.strftime("%Y%m%d%H%M"),"TA_F_QC"]),
         raw_mid_T_QC=int(original_qc.at[MID.strftime("%Y%m%d%H%M"),"TA_F_QC"]),
         raw_right_T_QC=int(original_qc.at[RIGHT.strftime("%Y%m%d%H%M"),"TA_F_QC"]),
         raw_mid_VPD_QC=int(original_qc.at[MID.strftime("%Y%m%d%H%M"),"VPD_F_QC"]),
         old_T_C=float(x.at[MID,"TA_USE"]),new_T_C=tM,
         old_VPD_hPa=float(x.at[MID,"VPD_USE"]),new_VPD_hPa=vM,
         old_QBOT=float(x.at[MID,"QBOT"]),new_QBOT=qM,
         interpolated_e_hPa=eM,
         source_ERA5Land_not_independent_tower_truth=True,
         bridging_to_original_QC1_ERA_scenario=True,
         original_or_approved_40_modified=False,Postv5_approved=False)] )
    summ=dict(site="US-MOz",version=VERSION,noleap_rows=315360,
         operator_request="QC1 source adjacent => interpolation anchored QC1 rather than invented QC0",
         true_left_class="QC1_to_QC1",true_right_class="QC1_to_QC2",
         modified_native_times=1,changed_variables=["TA_USE","TBOT","VPD_USE","QBOT"],
         previous_27_ERA5Land_sensitivity_preserved=True,
         original_40_operator_approved_preserved=True,
         native_30min_joins_over4C=0,native_30min_joins_over4hPa=0,
         whole_site_water_based_thermodynamic_closure=True,
         original_source_SHA256=sha(S07/"exact_input_manifest.json"),
         Stage14F_source_SHA256=sha(P/PFILE),
         Stage13L_source_SHA256=sha(L/LFILE),
         missing_after=0,source_is_independent_measured_RH=False,
         science_method_approved=False,Postv5=False,DATM=False,AD400=False,Slurm=False)
    print("US-MOz QC-AWARE FIRST LEFT EDGE: actual QC1 -> QC1; no original QC0 anchor",flush=True)
    print("US-MOz EXACT ONE NATIVE 19:30 QC1 MIDPOINT CHANGE:")
    print(changed.to_string(index=False),flush=True)
    print("US-MOz ALL 3 AFFECTED HALF-HOUR PHYSICAL BOUNDARIES:")
    print(edge.to_string(index=False),flush=True)
    print("US-MOz 27 ERA5 RECONSTRUCTIONS UNCHANGED + 40 OPERATOR-APPROVED UNCHANGED + ONE QC1 BRIDGE; 315360 FULL PHYSICS PASS",flush=True)
    return y.reset_index(drop=True),changed,edge,summ

def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):group.add_argument("--"+name,action="store_true")
    args=ap.parse_args()
    test()
    if args.self_test:return
    new,changes,edges,summary=assess()
    if args.check:
        print("US-MOz 14G CHECK PASS | NO SOURCE OR MODEL WRITES",flush=True)
        return
    out=ROOT/"science_trials"/("US_MOz_14G_QC1_LEFT_EDGE_ONE_HH_SENSITIVITY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={
      "US-MOz_315360_27ERA_plus1QC1bridge_and40approved_RESEARCH.csv":new,
      "US-MOz_1QC1_source_interpolated_midpoint.csv":changes,
      "US-MOz_3_QC1QC2_native_boundaries.csv":edges}
    hashes={}
    for name,df in docs.items():
        df.to_csv(out/name,index=False,float_format="%.17g")
        hashes[name]=sha(out/name)
    back=pd.read_csv(safe(out/list(docs)[0]),dtype={"time":str},low_memory=False)
    require(len(back)==315360 and list(back)==COLS and
            not back[COLS[1:]].isna().any().any(),
            "written research output 315360x10 roundtrip failed")
    (out/"RESEARCH_ONLY_NO_DATM_POSTV5_AD400").write_text(
      "QC1-to-QC1 bridging midpoint interpolation of T/e at Jan05 19:30. "
      "Local 0->1 assumed switch is FALSE. Science/method remains unvalidated by measured QC0. "
      "27 prior ERA5-Land source trial and original approved 40 source values preserved. "
      "No production, DATM, AD400 or Slurm jobs permitted.\n")
    hashes["RESEARCH_ONLY_NO_DATM_POSTV5_AD400"]=sha(out/"RESEARCH_ONLY_NO_DATM_POSTV5_AD400")
    (out/"US_MOz_QC1_bridge_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    hashes["US_MOz_QC1_bridge_summary.json"]=sha(out/"US_MOz_QC1_bridge_summary.json")
    (out/"US_MOz_QC1_bridge_SHA_receipt.json").write_text(json.dumps(
      {"version":VERSION,"source_Stage14F":summary["Stage14F_source_SHA256"],
       "source_Stage13L":summary["Stage13L_source_SHA256"],
       "output_SHA256":hashes,"science_approved":False},indent=2)+"\n")
    print("US-MOz QC1 BRIDGE NEW ISOLATED SOURCE:",out,flush=True)
    print("US-MOz 14G ONE QC1 MIDPOINT BRIDGE DONE | ALL 315360 CLOSED | ORIGINALS UNCHANGED | NO SLURM",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as err:
        print("US-MOz QC1 BRIDGE FAIL CLOSED:",err,file=sys.stderr,flush=True)
        raise

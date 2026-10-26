#!/usr/bin/env python3
"""Stage12af: US-NR1 2022-09-10 operator-approved 3 anomalous 11C TA_F
interpolation, separately preserving original source/Stage12g and six
unapproved humidity reconciliation proposals.

APPROVED: source-native 06:30 interpolate 06:00->07:00; 07:30 & 08:00
interpolate 07:00->08:30 at exact 30min intervals. Change TA_USE and
TBOT together only in new derivative. At each changed temperature, old
QC1 source VPD 8.427/8.383/9.319 hPa is physically impossible and cannot
remain: set VPD_USE and QBOT missing (HOLD) in temperature-only derivative.
This creates three extra *deliberate* humidity gaps. Six-record
06:00–08:30 companion source-native ERA-RH/VPD/QBOT consistency comparison
is a REPORT ONLY (NOT approved humidity repair).
No model-ready promotion, Postv5, DATM, spinup or Slurm.
--self-test: synthetic, no reads/writes
--check: source+SHA physics, no writes
--apply: a separate approved-T but INCOMPLETE research derivative plus
         unapproved six-record humidity candidate report with source SHA.
"""
import argparse, hashlib, json, sys, traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VERSION="batch03-stage12af-v1-20261026-NR1-three-T-approved-humidity-still-HOLD"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
S=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
SITE="US-NR1"
GFILE="US-NR1_STAGE12G_INCOMPLETE_NOLEAP.csv"
ANCHOR=("202209100600","202209100700","202209100830")
TARGET=("202209100630","202209100730","202209100800")
REVIEW=("202209100600","202209100630","202209100700",
        "202209100730","202209100800","202209100830")
T_ORIG={"202209100600":.762,"202209100630":11.297,
        "202209100700":1.720,"202209100730":11.196,
        "202209100800":11.787,"202209100830":1.230}
V_OLD={"202209100630":8.427,"202209100730":8.383,
       "202209100800":9.319}
TIMEFMT="%Y%m%d%H%M"

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing or unsafe prior input: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def es(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def tokey(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def interpolate(k,lower,upper,lowt,hight):
    start=pd.to_datetime(lower,format=TIMEFMT)
    end=pd.to_datetime(upper,format=TIMEFMT)
    at=pd.to_datetime(k,format=TIMEFMT)
    if not (start<at<end):
        raise ValueError("Invalid source interpolation interval")
    return float(lowt+(hight-lowt)*((at-start)/(end-start)))

def selftest():
    assert TARGET==("202209100630","202209100730","202209100800")
    assert abs(interpolate(TARGET[0],ANCHOR[0],ANCHOR[1],.762,1.720)-1.241)<1e-12
    assert abs(interpolate(TARGET[1],ANCHOR[1],ANCHOR[2],1.720,1.230)-1.55666666666667)<1e-12
    assert abs(interpolate(TARGET[2],ANCHOR[1],ANCHOR[2],1.720,1.230)-1.39333333333333)<1e-12
    assert all(V_OLD[k]>float(es(T_ORIG[k])) for k in TARGET)==False  # original warm T supports old VPD numerically
    assert all(V_OLD[k]>float(es({TARGET[0]:1.241,TARGET[1]:1.55666666666667,TARGET[2]:1.39333333333333}[k])) for k in TARGET)
    print("STAGE12AF SELF-TEST PASS: exact three native T interpolations, invalid retained QC1 humidity after correction; NO WRITES",flush=True)

def verify():
    g=json.loads(safe(G/"stage12g_research_only_sha_receipt.json").read_text())
    if not (g.get("original_233_physics_holds_untouched") is True
        and g.get("INCOMPLETE_marker_present") is True
        and g.get("Postv5_approved")==0 and g.get("DATM_ready")==0
        and g.get("spinup_authorized")==0
        and sha(G/GFILE)==g["output_sha256"][GFILE]):
        raise ValueError("Sealed original Stage12g source/science SHA changed")
    manifest=json.loads(safe(S/"exact_input_manifest.json").read_text())
    spec=next(item for item in manifest["sites"] if item["site"]==SITE)
    pins={str(Path(name).resolve()):h for name,h in manifest["input_sha256"].items()}
    for f in ("primary","era"):
        pp=safe(spec[f])
        if sha(pp)!=pins.get(str(pp.resolve())):
            raise ValueError("Original paired tower/source input SHA changed: "+f)
    return spec

def audit():
    spec=verify()
    base=pd.read_csv(safe(G/GFILE),dtype={"time":str},low_memory=False)
    origcols=list(base)
    assert {"time","TA_USE","TBOT","VPD_USE","QBOT","PSRF"}<=set(base)
    keys=tokey(base.time)
    if keys.duplicated().any() or not set(REVIEW)<=set(keys):
        raise ValueError("Exact 6 native times missing or duplicated in G")
    idx={v:i for i,v in enumerate(keys)}
    rawcols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    raw=pd.read_csv(safe(spec["primary"]),usecols=rawcols,dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(safe(spec["era"]),usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    raw=raw.loc[raw.TIMESTAMP_START.isin(REVIEW)].copy()
    era=era.loc[era.TIMESTAMP_START.isin(REVIEW)].copy()
    if len(raw)!=6 or len(era)!=6 or raw.TIMESTAMP_START.duplicated().any() or era.TIMESTAMP_START.duplicated().any():
        raise ValueError("Signed raw/paired ERA source 6 native rows not exactly present")
    data=(raw.merge(era,on="TIMESTAMP_START",validate="one_to_one")
          .sort_values("TIMESTAMP_START").reset_index(drop=True))
    selected=base.copy(deep=True)
    before_after=[]
    for k in REVIEW:
        r=data.loc[data.TIMESTAMP_START.eq(k)]
        if len(r)!=1:raise ValueError("Missing source native key "+k)
        r=r.iloc[0]
        i=idx[k]
        if not (abs(float(r.TA_F)-T_ORIG[k])<1e-5 and
            abs(float(base.TA_USE.iat[i])-T_ORIG[k])<1e-5 and
            abs(float(base.TBOT.iat[i])-(T_ORIG[k]+273.15))<1e-5):
            raise ValueError("Original signed raw or Stage12g T differs "+k)
        if k in ANCHOR and not (pd.notna(r.TA_F_QC) and float(r.TA_F_QC)==0):
            raise ValueError("An interpolation anchor is not original measured TA_F_QC0 "+k)
    for k in TARGET:
        i=idx[k]
        lower,upper=(ANCHOR[0],ANCHOR[1]) if k==TARGET[0] else (ANCHOR[1],ANCHOR[2])
        fresh=interpolate(k,lower,upper,T_ORIG[lower],T_ORIG[upper])
        if not np.isclose(float(base.VPD_USE.iat[i]),V_OLD[k],atol=1e-6,rtol=0):
            raise ValueError("Old QC1 source VPD at target differs "+k)
        if not float(base.VPD_USE.iat[i])>float(es(fresh)):
            raise ValueError("Old VPD no longer physically impossible after interpolated T "+k)
        # Only user-approved temperature changes are applied; old RH
        # derived from physically impossible source gapfill is HELD.
        selected.loc[i,"TA_USE"]=fresh
        selected.loc[i,"TBOT"]=fresh+273.15
        selected.loc[i,"VPD_USE"]=np.nan
        selected.loc[i,"QBOT"]=np.nan
        before_after.append({
            "site":SITE,"native_key":k,
            "source_TA_F_QC":int(data.loc[data.TIMESTAMP_START.eq(k),"TA_F_QC"].iloc[0]),
            "before_tower_T_C":T_ORIG[k],"approved_interpolated_T_C":fresh,
            "before_TBOT_K":float(base.TBOT.iat[i]),
            "after_TBOT_K":fresh+273.15,
            "before_VPD_USE_hPa":V_OLD[k],
            "after_VPD_USE_hPa":np.nan,
            "reason":"Operator-approved isolated 11C source T anomaly; original Stage12g QC1 VPD physically impossible under corrected T",
            "temperature_approved":True,
            "humidity_ERA_replacement_approved":False
        })
    target=keys.isin(TARGET).to_numpy(dtype=bool)
    for col in origcols:
        if col in ("TBOT","TA_USE","VPD_USE","QBOT"):
            if not np.array_equal(base.loc[~target,col].to_numpy(dtype=float),
                                  selected.loc[~target,col].to_numpy(dtype=float),equal_nan=True):
                raise ValueError("Original unapproved off-target forcing modified "+col)
        elif not base[col].equals(selected[col]):
            raise ValueError("Unapproved non-temperature/non-humidity field changed "+col)
    candidates=[]
    for k in REVIEW:
        i=idx[k]
        r=data.loc[data.TIMESTAMP_START.eq(k)].iloc[0]
        t=float(selected.TA_USE.iat[i])
        era_rh=100*(1-float(r.VPD_ERA)/float(es(float(r.TA_ERA))))
        cand_v=float(es(t)*(1-era_rh/100))
        ea=float(es(t)-cand_v)*100
        p=float(selected.PSRF.iat[i])
        cand_q=.622*ea/(p-.378*ea)
        if not (0<era_rh<100 and 0<=cand_v<float(es(t)) and 0<cand_q<.08
            and abs(float(r.TA_ERA)-t)<5):
            raise ValueError("Six-row source-paired ERA-RH comparison invalid at "+k)
        candidates.append({"native_key":k,
           "operator_approved_T_C":t,
           "paired_source_TA_ERA_C":float(r.TA_ERA),
           "paired_source_ERA_RH_pct":era_rh,
           "hypothetical_unapproved_ERA_RH_VPD_hPa":cand_v,
           "hypothetical_unapproved_ERA_RH_QBOT_kgkg":cand_q,
           "Stage12g_original_VPD_hPa":float(base.VPD_USE.iat[i]),
           "after_approved_temperature_only_VPD_hPa":float(selected.VPD_USE.iat[i]),
           "ERA_RH_for_humidity_repair_APPROVED":False})
    cands=pd.DataFrame(candidates)
    assert len(cands)==6 and len(before_after)==3
    assert not np.any(np.abs(np.diff(cands.hypothetical_unapproved_ERA_RH_VPD_hPa.to_numpy()))>4)
    return selected,pd.DataFrame(before_after),cands

def main():
    parser=argparse.ArgumentParser()
    g=parser.add_mutually_exclusive_group(required=True)
    for option in ("self-test","check","apply"):
        g.add_argument("--"+option,action="store_true")
    args=parser.parse_args()
    print("STAGE12AF US-NR1 OPERATOR APPROVED THREE T INTERPOLATIONS, ERA RH PROPOSAL REPORT ONLY | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    selected,changes,comparison=audit()
    print("\n===== USER-APPROVED EXACT THREE TEMPERATURE CORRECTIONS =====",flush=True)
    print(changes.to_string(index=False),flush=True)
    print("\n===== SIX ORIGINAL NATIVE RH CANDIDATES: PROPOSED ONLY, NOT USER-APPROVED =====",flush=True)
    print(comparison.round(6).to_string(index=False),flush=True)
    print("STATUS: original Stage12g unchanged; QC1 VPD/QBOT at 3 temperature-edited times held in NEW derivative; other 3 old humidity holds unchanged; six paired ERA-RH proposals NOT APPLIED; no model-ready promotion.",flush=True)
    if args.check:
        print("STAGE12AF CHECK ONLY: NO WRITES.",flush=True)
        return
    out=ROOT/"science_trials"/("stage12af_NR1_20220910_user_approved_three_T_only_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={
      "US-NR1_STAGE12AF_USER_APPROVED_T_ONLY_INCOMPLETE_NOLEAP.csv":selected,
      "three_user_approved_T_interpolation_original_native.csv":changes,
      "six_unapproved_same_native_ERA_RH_humidity_candidates.csv":comparison,
    }
    for name,frame in outputs.items():frame.to_csv(out/name,index=False)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
      "Original Stage12g is unmodified; 3 user-approved interpolated temperature corrections in new derived site NOLEAP. "
      "Corresponding old QC1 VPD/QBOT physically impossible at corrected temperatures, held missing. "
      "Six-row paired ERA-RH report-only proposal requires separate scientific approval before application.\n")
    h={k:sha(out/k) for k in [*outputs,"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"]}
    (out/"stage12af_three_temperature_SHA_receipt.json").write_text(json.dumps({
      "version":VERSION,"three_T_interpolation_operator_approved":True,
      "six_ERA_RH_humidity_proposal_APPROVED":False,
      "original_Stage12g_US_NR1_SHA256":sha(G/GFILE),
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "output_SHA256":h},indent=2)+"\n")
    print("STAGE12AF USER-APPROVED TEMPERATURE-DERIVED REPORT DIR:",out,flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AF STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

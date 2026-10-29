#!/usr/bin/env python3
"""US-Kon next Batch03: one-pass final 77 missing humidity source evidence.

Actual Stage12AY signed research output: exactly 77 VPD/QBOT missing
selected native HH. Preserve 9 source-event HARD HOLD keys, source T
and previous source-only trial; evaluate remaining 68 routine using:
  (A) selected e/VPD/QBOT end anchors as provenance, and
  (B) original paired ERA RH transposed to selected tower T+PSRF,
with real original source QC for all 77 & closest selected anchors.
No automatic replacement/approval: print complete class counts and
SHA-seal 77 source/QC/candidate matrix + contiguous episode inventory.
No old scientific source/case/Slurm writes; --run reports only.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np,pandas as pd
sys.dont_write_bytecode=True
V="batch03-US-Kon-77-source-QC-onepass-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
PARENT=R/"science_trials"
GLOB="stage12ay_Kon_FINAL_science_candidates_and_sealed_HOLDS_*"
REC="stage12ay_FINAL_research_HOLD_SHA_receipt.json"
F="US-Kon_STAGE12AY_FINAL_RESEARCH_ONLY_NOT_DATM_NOLEAP.csv"
HOLDS="FINAL_UNRESOLVED_HUMIDITY_SOURCE_HOLDS.csv"
def need(cond,message):
    if not bool(cond):raise RuntimeError("US-Kon STOP; NO DATA EDIT: "+message)
def valid_file(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),"source file absent "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with valid_file(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def esw(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def esi(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",invalid="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))
def qcalc(e,p):
    return .622*100*e/(p-.378*100*e)
def key(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def test():
    need(esw(-15)>esi(-15) and
         pd.Series(["abc",None]).equals(pd.Series(["abc",None])) and
         len("201102220900")==12,"native key and saturation unit tests")
    print("US-Kon 77 SOURCE-QC ONEPASS SELF-TEST PASS",flush=True)
def locate():
    dirs=sorted(p for p in PARENT.glob(GLOB) if p.is_dir() and not p.is_symlink())
    sealed=[]
    for d in dirs:
        receipt=d/REC
        if not receipt.is_file() or receipt.is_symlink():continue
        data=json.loads(receipt.read_text())
        if data.get("version")!="batch03-stage12ay-v1-20261026-Kon-seal-final-70-humidity-holds":
            continue
        for fn,digest in data["output_SHA256"].items():
            need(sha(d/fn)==digest,"Stage12AY signed output changed "+fn)
        need(data.get("new_research_missing")==77 and
             data.get("nine_protected_native_science_holds")==9 and
             data.get("operator_approved") is False and
             data.get("DATM_ready") is False and
             data.get("spinup_authorized") is False,
             "Stage12AY signed 77 source holds/production flags differ")
        sealed.append((d,data))
    need(len(sealed)==1,
         "must identify exactly one sealed actual Stage12AY 77-missing research trial; found "+
         str(len(sealed)))
    print("US-Kon EXACT SIGNED STAGE12AY SELECTED:",sealed[0][0],flush=True)
    return sealed[0]
def load():
    d,rec=locate()
    parent=pd.read_csv(valid_file(d/F),dtype={"time":str},low_memory=False)
    need(len(parent)==280320 and
         {"time","TBOT","TA_USE","QBOT","VPD_USE","PSRF"}<=set(parent.columns),
         "selected Stage12AY 280320 source HH/model columns missing")
    keys=key(parent.time)
    need(keys.str.len().eq(12).all() and keys.is_unique,
         "selected source timestamps not unique native 12digits")
    dt=pd.to_datetime(keys,format="%Y%m%d%H%M",errors="raise")
    need(dt.is_monotonic_increasing and
         not bool(((dt.dt.month==2)&(dt.dt.day==29)).any()),
         "selected native NOLEAP clock changed")
    nan=parent.VPD_USE.isna()
    need(nan.equals(parent.QBOT.isna()) and int(nan.sum())==77,
         "Stage12AY selected 77 paired VPD/QBOT missing changed")
    holds=pd.read_csv(valid_file(d/HOLDS),dtype={"native_key":str})
    need(len(holds)==77 and holds.native_key.nunique()==77 and
         set(holds.native_key)==set(keys[nan]),
         "original signed 77 exact protected/source missing ledger mismatch")
    hard=set(holds.loc[holds.hold_class.eq("NINE_SOURCE_EVENT_PROVENANCE_HARD_HOLD"),
                        "native_key"])
    need(len(hard)==9 and len(holds)-len(hard)==68 and
         {"201102220900","201109291830"}<=hard,
         "hard9/routine68 source-disposition differs")
    manifest=json.loads(valid_file(S07/"exact_input_manifest.json").read_text())
    info=[z for z in manifest["sites"] if z["site"]=="US-Kon"]
    need(len(info)==1 and int(info[0]["native_minutes"])==30,
         "original Kon site native clock source is not 30minutes")
    spec=info[0]
    for k in ("primary","era"):
        f=valid_file(spec[k])
        need(manifest["input_sha256"].get(str(f.resolve()))==sha(f),
             "original source "+k+" SHA changed")
    return d,parent,keys,dt,holds,hard,spec
def raw_subset(path,cols,require_keys):
    s=pd.read_csv(valid_file(path),usecols=["TIMESTAMP_START",*cols],
         dtype={"TIMESTAMP_START":str},low_memory=False)
    need(s.TIMESTAMP_START.is_unique,"original raw source timestamps duplicated")
    s=s.loc[s.TIMESTAMP_START.isin(require_keys)].copy()
    s.index=s.TIMESTAMP_START
    need(len(s)==len(require_keys) and set(s.index)==set(require_keys),
         "raw source missing one of exact 77 native timestamps")
    for c in cols:
        s[c]=pd.to_numeric(s[c],errors="coerce").mask(lambda x:x<=-9990)
    return s
def assess():
    d,p,keys,clock,holds,hard,spec=load()
    require_keys=list(keys[p.VPD_USE.isna()])
    raw=raw_subset(spec["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
                   require_keys)
    era=raw_subset(spec["era"],["TA_ERA","VPD_ERA"],require_keys)
    positions={k:i for i,k in enumerate(keys)}
    missing=set(require_keys)
    rows=[]
    for k in require_keys:
        i=positions[k]
        r=raw.loc[k];er=era.loc[k];tt=float(p.TA_USE.iat[i])
        pressure=float(p.PSRF.iat[i])
        ta=float(er.TA_ERA);evpd=float(er.VPD_ERA)
        rh=1-evpd/float(esw(ta)) if np.isfinite([ta,evpd]).all() else np.nan
        e=float(esw(tt))*rh
        v=float(esw(tt))-e
        q=float(qcalc(e,pressure))
        ratio=e/float(esi(tt)) if tt<0 else np.nan
        era_physical=bool(np.isfinite([tt,pressure,rh,e,v,q]).all() and
             50000<pressure<110000 and
             0<rh<1 and 0<v<float(esw(tt)) and 0<q<.08 and
             (tt>=0 or ratio<=1.02))
        left=i-1
        while left>=0 and keys.iat[left] in missing:left-=1
        right=i+1
        while right<len(keys) and keys.iat[right] in missing:right+=1
        neighbors=[]
        for loc in (left,right):
            if loc<0 or loc>=len(keys):
                neighbors.append((None,np.nan,np.nan,np.nan))
            else:
                neighbors.append((keys.iat[loc],float(p.VPD_USE.iat[loc]),
                    float(p.QBOT.iat[loc]),float(p.TA_USE.iat[loc])))
        l,rn=neighbors
        spacing=(pd.to_datetime(rn[0],format="%Y%m%d%H%M")-
            pd.to_datetime(l[0],format="%Y%m%d%H%M")).total_seconds()/3600 if l[0] and rn[0] else np.nan
        rows.append(dict(native_key=k,hard_science_HOLD=(k in hard),
            source_T_QC=r.TA_F_QC,source_VPD_QC=r.VPD_F_QC,
            source_tower_T_C=r.TA_F,source_VPD_F_hPa=r.VPD_F,
            source_companion_ERA_T_C=ta,source_companion_ERA_VPD_hPa=evpd,
            selected_T_C=tt,selected_PSRF_Pa=pressure,
            candidate_transferred_ERA_waterRH_pct=100*rh,
            candidate_ERA_RH_VPD_hPa=v if era_physical and k not in hard else np.nan,
            candidate_ERA_RH_QBOT=q if era_physical and k not in hard else np.nan,
            candidate_water_ice_physics_pass=era_physical,
            trusted_as_measured_tower_humidity=False,
            left_selected_anchor_key=l[0],left_selected_anchor_VPD_hPa=l[1],
            left_selected_anchor_QBOT=l[2],left_selected_anchor_T_C=l[3],
            right_selected_anchor_key=rn[0],right_selected_anchor_VPD_hPa=rn[1],
            right_selected_anchor_QBOT=rn[2],right_selected_anchor_T_C=rn[3],
            anchor_span_hours=spacing,
            original_T_minus_ERA_C=tt-ta,
            source_evidence_decision=(
                "NINE_HARD_SOURCE_HOLD_DO_NOT_AUTO_REPLACE" if k in hard else
                "ROUTINE_ERA_RH_ONLY_LOW_CONFIDENCE" if era_physical else
                "ROUTINE_PHYSICAL_OR_ERA_SOURCE_INVALID_HOLD"),
            operator_approved=False,postv5_DATM_approved=False))
    ledger=pd.DataFrame(rows)
    need(len(ledger)==77 and int(ledger.hard_science_HOLD.sum())==9 and
         set(ledger.native_key)==missing,"exact Kon 77 source ledger drift")
    # One row per contiguous native 30minute episode, not nominal year.
    ordered=[positions[k] for k in require_keys]
    episodes=[];start=last=int(ordered[0])
    for i in ordered[1:]+[None]:
        if i is not None and i==last+1 and (clock.iat[i]-clock.iat[last])==pd.Timedelta(minutes=30):
            last=i;continue
        part=ledger[ledger.native_key.isin(keys.iloc[start:last+1])]
        episodes.append(dict(start_native_time=keys.iat[start],
           end_native_time=keys.iat[last],half_hours=last-start+1,
           hard_source_hold=int(part.hard_science_HOLD.sum()),
           routine_candidate_possible=int(part.candidate_ERA_RH_VPD_hPa.notna().sum()),
           routine_source_physics_fail=int((~part.hard_science_HOLD&~part.candidate_water_ice_physics_pass).sum()),
           original_QC0_VPD_count=int(part.source_VPD_QC.eq(0).sum()),
           original_QC1_VPD_count=int(part.source_VPD_QC.eq(1).sum()),
           original_QC2_VPD_count=int(part.source_VPD_QC.eq(2).sum()),
           production_approved=False))
        if i is not None:start=int(i);last=int(i)
    episode_df=pd.DataFrame(episodes)
    counts=ledger.groupby("source_evidence_decision",dropna=False).size().to_dict()
    summary=dict(version=V,site="US-Kon",
      actual_original_signed_stage12ay=str(d),
      selected_source_receipt_SHA256=sha(d/REC),
      original_tower_SHA256=sha(spec["primary"]),
      original_companion_ERA_SHA256=sha(spec["era"]),
      native_model_rows=len(p),old_missing=77,
      protected_science_HOLD_n=9,routine_missing_n=68,
      routine_ERA_RH_numerically_possible=int(ledger.candidate_ERA_RH_VPD_hPa.notna().sum()),
      routine_physical_or_source_unavailable=int(
        ((~ledger.hard_science_HOLD)&ledger.candidate_ERA_RH_VPD_hPa.isna()).sum()),
      native_missing_episodes=len(episode_df),
      science_classes=counts,
      no_existing_science_input_or_model_writes=True,
      no_new_observational_humidity_truth=True,
      Postv5_approved=False,DATM_ready=False,AD400=False,Slurm=False)
    print("\nUS-Kon 77 ORIGINAL SCIENCE SOURCE/ERA ANCHOR SUMMARY:")
    print(json.dumps(summary,indent=2),flush=True)
    print("\nUS-Kon ALL 9 SPECIAL HARD ORIGINAL SOURCE HOLDS:")
    print(ledger.loc[ledger.hard_science_HOLD,[
      "native_key","source_T_QC","source_VPD_QC","selected_T_C",
      "original_T_minus_ERA_C","source_evidence_decision"]].to_string(index=False),flush=True)
    print("\nUS-Kon COMPLETE CONTIGUOUS 77 MISSING NATIVE EPISODES:")
    print(episode_df.to_string(index=False),flush=True)
    print("US-Kon 77 SCIENCE DECISION MATRIX COMPLETE; NO FORCING/SLURM CHANGE",flush=True)
    return summary,ledger,episode_df
def main():
    a=argparse.ArgumentParser()
    g=a.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):g.add_argument("--"+opt,action="store_true")
    args=a.parse_args()
    test()
    if args.self_test:return
    summary,ledger,episodes=assess()
    if args.check:
        print("US-Kon 77 READONLY CHECK COMPLETE",flush=True)
        return
    out=R/"reports"/("US_Kon_77_original_QC_and_ERA_research_candidates_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={"US_Kon_ALL77_exact_humidity_SOURCE_QC_ERA_anchor_decisions.csv":ledger,
             "US_Kon_ALL77_native_contiguous_episode_decisions.csv":episodes}
    hashes={}
    for filename,df in outputs.items():
        df.to_csv(out/filename,index=False,float_format="%.17g")
        hashes[filename]=sha(out/filename)
    (out/"US_Kon_77_science_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    hashes["US_Kon_77_science_summary.json"]=sha(out/"US_Kon_77_science_summary.json")
    (out/"US_Kon_77_SOURCE_HOLD_NOT_DATM").write_text(
        "This output only audits actual 77 remaining VPD/QBOT missing site records. "
        "Nine protected science anomalies unchanged; other 68 rows have exploratory "
        "paired ERA RH candidates when physically possible. Paired ERA is not observed "
        "humidity; no site-forcing modifications, automatic Postv5/DATM/AD400/Slurm approval.\n")
    hashes["US_Kon_77_SOURCE_HOLD_NOT_DATM"]=sha(out/"US_Kon_77_SOURCE_HOLD_NOT_DATM")
    (out/"US_Kon_77_READONLY_SHA_receipt.json").write_text(json.dumps(
       {"version":V,"output_SHA256":hashes,
        "source_inputs_modified":False,"science_approved":False},indent=2)+"\n")
    print("US-Kon 77 ONEPASS SCIENCE REPORT:",out,flush=True)
    print("US-Kon 77 SOURCE-QC MATRIX SUCCESS | ALL ORIGINAL SOURCE AND TRIALS UNCHANGED",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("US-Kon 77 SOURCE SCIENCE STOP:",exc,file=sys.stderr,flush=True)
        raise

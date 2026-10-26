#!/usr/bin/env python3
"""ONE FINAL Kon routine humidity-gap pass: VPD-linear bridge of 70 missing
source-native halfhours in 30 segments from immutable Stage12ax. Then seal
a signed, compact unresolved HOLD register rather than a sequence of new
manual micro-stages. Research-only candidate, NOT DATM forcing authorization.

Scope:
 - previous signed Stage12ax already filled 261 new research candidates;
 - 70 routine gaps not rescued by selected-anchor QBOT or RH interpolation;
 - try ONE third method: interpolate VPD itself between valid selected outer
   anchors; recover QBOT from selected tower T+P and vapor pressure.
 - require source-native halfhours, both endpoints real finite, selected
   humidity physical, paired VPD/QBOT agreement, VPD jumps <=4 hPa/30min,
   RH jumps <=20 pp/30min, QBOT jumps <=0.003 kg/kg/30min, water/ice physics;
 - leave seven failed-event-center and two original T conflict keys MISSING.
 - NO automatic operator approval of upstream 79+1+261 plus new candidates.
 - no source, DATM, model, Slurm, clock, scientific input mutation.

--self-test: independent synthetic physics checks.
--check: signed inputs + in-memory trial, no writes.
--finalize: one separate signed RESEARCH-ONLY candidate CSV + final HOLD
    report + batch03 site names/status (other nine NOT YET VERIFIED).
"""
import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VER="batch03-stage12ay-v1-20261026-Kon-seal-final-70-humidity-holds"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AX=ROOT/"science_trials/stage12ax_Kon_331_selected_anchor_humidity_RESEARCH_ONLY_20261026T131828Z_c5fcbf6b"
AV=ROOT/"science_trials/stage12av_Kon_341_ERA_RH_fasttrack_RESEARCH_ONLY_20261026T121557Z_8d23d4cf"
F="US-Kon_STAGE12AX_SELECTED_ANCHORS_NO_DATM_NOLEAP.csv"
P="9_protected_native_science_holds.csv"
SPECIAL={"201102220900","201109291830"}
SITES=["US-Kon","US-Me2","US-Me6","US-MMS","US-MOz","US-Mpj","US-MtB","US-NC2","US-NR1","US-NR3"]
MAX_VPD_JUMP=4.0
MAX_RH_JUMP=20.0
MAX_QBOT_JUMP=0.003
MAX_GAP=48

def file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise RuntimeError("Missing or symlink signed input: "+str(p))
    return p

def digest(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def keys(series):
    return series.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def satw(t):
    if not np.isfinite(t) or not (-85<t<55):
        return np.nan
    return 6.112*np.exp(17.67*t/(243.5+t))

def sati(t):
    if not np.isfinite(t) or not (-85<t<55):
        return np.nan
    return 6.112*np.exp(22.46*t/(272.62+t))

def from_vpd(t,p,v):
    if not np.isfinite([t,p,v]).all() or not (50000<p<110000):
        return None
    sw=satw(t)
    if not (np.isfinite(sw) and 0<v<sw):
        return None
    e=sw-v
    if t<0 and e>1.02*sati(t):
        return None
    q=.622*(e*100)/(p-.378*(e*100))
    rh=100*e/sw
    if not (np.isfinite([q,rh]).all() and 0<q<.08 and 0<rh<100):
        return None
    return (float(v),float(q),float(rh))

def pair_consistent(t,p,v,q):
    x=from_vpd(t,p,v)
    return x is not None and np.isfinite(q) and 0<q<0.08 and abs(x[1]-q)<=0.001

def adjacent(a,b):
    return pd.to_datetime(b,format="%Y%m%d%H%M")-pd.to_datetime(
        a,format="%Y%m%d%H%M")==pd.Timedelta(minutes=30)

def group(indices,allkeys):
    g=[];run=[]
    for ii in indices:
        i=int(ii)
        if run and (i!=run[-1]+1 or not adjacent(allkeys[run[-1]],allkeys[i])):
            g.append(run);run=[]
        run.append(i)
    if run:g.append(run)
    return g

def selftest():
    assert from_vpd(20,100000,5) is not None
    assert from_vpd(20,100000,50) is None
    assert from_vpd(20,100000,-1) is None
    assert adjacent("201110172330","201110180000")
    assert len(SITES)==10 and len(SPECIAL)==2
    print("STAGE12AY SELF-TEST PASS | physical VPD bridge + 9 hard source holds; no writes",flush=True)

def signed():
    ax=json.loads(file(AX/"stage12ax_selected_anchor_QBOT_RH_SHA_receipt.json").read_text())
    av=json.loads(file(AV/"stage12av_341_humidity_fasttrack_SHA_receipt.json").read_text())
    if not (
        ax.get("version")=="batch03-stage12ax-v1-20261026-Kon-selected-boundary-QBOT-RH-331"
        and ax.get("original_missing")==340
        and ax.get("original_routine_missing")==331
        and ax.get("nine_protected_source_holds")==9
        and ax.get("new_numerical_candidates_unapproved")==261
        and ax.get("trial_remaining_missing")==79
        and ax.get("stage12an_79_prior_proposals_unapproved") is True
        and ax.get("operator_approved") is False
        and ax.get("Postv5_approved") is False
        and ax.get("DATM_ready") is False
        and ax.get("spinup_authorized") is False
        and av.get("protected_count")==9
        and av.get("seven_failed_events_held") is True
        and av.get("two_hard_source_T_holds_held") is True
        and av.get("operator_approval") is False
        and av.get("DATM_ready") is False):
        raise RuntimeError("Stage12ax/av source science holds or exact 261/79 invariants changed")
    for name in (
        F,
        "124_remaining_routine_source_native_segments.csv",
        "new_science_only_source_native_VPD_QBOT_candidates.csv",
        "all_unresolved_original_missing_and_nine_protected.csv",
        "RESEARCH_HYPOTHESIS_NO_OPERATOR_APPROVAL_NO_DATM"
    ):
        if ax.get("output_SHA256",{}).get(name)!=digest(AX/name):
            raise RuntimeError("Unsigned changed Stage12ax file "+name)
    if av.get("output_SHA256",{}).get(P)!=digest(AV/P):
        raise RuntimeError("Original nine scientific hard holds changed")
    return ax

def assess():
    signed()
    source=pd.read_csv(file(AX/F),dtype={"time":str},low_memory=False)
    if len(source)!=280320 or not {"time","TA_USE","PSRF","VPD_USE","QBOT"}<=set(source):
        raise RuntimeError("Unexpected selected source-native 10y+ NOLEAP input schema")
    time=keys(source.time).tolist()
    if len(set(time))!=len(time) or not np.array_equal(source.VPD_USE.isna(),source.QBOT.isna()):
        raise RuntimeError("Source native clock or VPD/QBOT missing masks altered")
    protected=pd.read_csv(file(AV/P),dtype={"native_key":str})
    hard=set(protected.native_key)
    if len(hard)!=9 or len(protected)!=9 or not SPECIAL.issubset(hard):
        raise RuntimeError("Signed seven event / two source-T hard holds changed")
    idmap={k:i for i,k in enumerate(time)}
    if not hard.issubset(idmap):
        raise RuntimeError("Protected timestamp missing")
    original_missing=np.flatnonzero(source.VPD_USE.isna().to_numpy())
    unprotected=[int(i) for i in original_missing if time[int(i)] not in hard]
    if len(original_missing)!=79 or len(unprotected)!=70:
        raise RuntimeError("Expected 79 remaining, 70 routine, 9 hard original science holds")
    segments=group(unprotected,time)
    if len(segments)!=30:
        raise RuntimeError("Expected 30 remaining distinct routine source-time segments")
    # All 30 failed AX segments are exactly the ones we are allowed to test.
    prior=pd.read_csv(file(AX/"124_remaining_routine_source_native_segments.csv"),
                      dtype={"first_native_key":str,"last_native_key":str})
    priorheld=prior.loc[~prior.numeric_research_segment_pass.astype(str).str.lower().eq("true")]
    if len(priorheld)!=30 or set(priorheld.first_native_key)!=set(time[g[0]] for g in segments):
        raise RuntimeError("Original Stage12ax 30 held segment identities changed")
    trial=source.copy(deep=True)
    changed={}
    reports=[]
    for group_id,ids in enumerate(segments,1):
        reasons=set()
        a,b=ids[0]-1,ids[-1]+1
        if a<0 or b>=len(source):
            reasons.add("ORIGINAL_NATIVE_DOMAIN_EDGE")
        if len(ids)>MAX_GAP:
            reasons.add("GAP_OVER_24_HOURS")
        end={}
        if 0<=a<len(source) and 0<=b<len(source):
            if not adjacent(time[a],time[ids[0]]) or not adjacent(time[ids[-1]],time[b]):
                reasons.add("TIME_GRID_DISCONTINUITY")
            if time[a] in hard or time[b] in hard:
                reasons.add("ADJACENT_PROTECTED_SOURCE_HOLD")
            for side,i in (("left",a),("right",b)):
                t=float(source.TA_USE.iat[i])
                p=float(source.PSRF.iat[i])
                v=float(source.VPD_USE.iat[i])
                q=float(source.QBOT.iat[i])
                check=from_vpd(t,p,v)
                if check is None or not pair_consistent(t,p,v,q):
                    reasons.add("SELECTED_ANCHOR_VPD_QBOT_UNPHYSICAL_OR_INCONSISTENT")
                    continue
                end[side]=check
        candidates=[]
        max_jump_v=max_jump_q=max_jump_r=np.nan
        if not reasons and len(end)==2:
            start_v=end["left"][0]
            delta_v=end["right"][0]-start_v
            for i in ids:
                fraction=(i-a)/(b-a)
                v=start_v+fraction*delta_v
                t=float(source.TA_USE.iat[i])
                p=float(source.PSRF.iat[i])
                row=from_vpd(t,p,v)
                if row is None:
                    reasons.add("BRIDGED_VPD_WATER_ICE_QBOT_PHYSICS_FAIL")
                    break
                candidates.append((i,row))
            if len(candidates)==len(ids):
                allvalues=[end["left"]]+[row for _,row in candidates]+[end["right"]]
                vj=np.abs(np.diff([r[0] for r in allvalues]))
                qj=np.abs(np.diff([r[1] for r in allvalues]))
                rj=np.abs(np.diff([r[2] for r in allvalues]))
                max_jump_v=float(vj.max())
                max_jump_q=float(qj.max())
                max_jump_r=float(rj.max())
                if not (np.isfinite(vj).all() and np.all(vj<=MAX_VPD_JUMP)):
                    reasons.add("BRIDGE_VPD_30MIN_JUMP_GT4HPA")
                if not (np.isfinite(rj).all() and np.all(rj<=MAX_RH_JUMP)):
                    reasons.add("BRIDGE_RH_30MIN_JUMP_GT20PP")
                if not (np.isfinite(qj).all() and np.all(qj<=MAX_QBOT_JUMP)):
                    reasons.add("BRIDGE_QBOT_30MIN_JUMP_GT0.003")
            else:
                reasons.add("BRIDGE_SOURCE_SEGMENT_PARTIAL")
        else:
            reasons.add("BRIDGE_BOUNDARY_OR_SOURCE_UNAVAILABLE")
        passed=not reasons and len(candidates)==len(ids)
        if passed:
            for i,x in candidates:
                if i in changed or time[i] in hard:
                    raise RuntimeError("Overlapped prior change or protected original hold")
                changed[i]=x
                trial.loc[i,"VPD_USE"]=x[0]
                trial.loc[i,"QBOT"]=x[1]
        reports.append({
            "segment_id":group_id,"first_native_key":time[ids[0]],
            "last_native_key":time[ids[-1]],
            "original_missing_halfhours":len(ids),
            "local_bridge_numerical_pass":bool(passed),
            "new_humidity_candidates":len(ids) if passed else 0,
            "max_30min_VPD_jump_hPa":max_jump_v,
            "max_30min_RH_jump_pp":max_jump_r,
            "max_30min_QBOT_jump_kgkg":max_jump_q,
            "science_hold_reason":";".join(sorted(reasons)),
            "operator_approved":False,
        })
    original_v=source.VPD_USE.to_numpy(dtype=float)
    after_v=trial.VPD_USE.to_numpy(dtype=float)
    original_q=source.QBOT.to_numpy(dtype=float)
    after_q=trial.QBOT.to_numpy(dtype=float)
    altered=(~np.isclose(original_v,after_v,rtol=0,atol=1e-10,equal_nan=True) |
             ~np.isclose(original_q,after_q,rtol=0,atol=1e-12,equal_nan=True))
    if set(np.flatnonzero(altered))!=set(changed):
        raise RuntimeError("Unexpected humidity scientific change outside final 70 source missing")
    for c in source.columns:
        if c not in ("VPD_USE","QBOT") and not source[c].equals(trial[c]):
            raise RuntimeError("Nonhumidity source or time changed")
    if not np.array_equal(trial.VPD_USE.isna(),trial.QBOT.isna()):
        raise RuntimeError("VPD/QBOT new missing mask mismatch")
    if any(pd.notna(trial.VPD_USE.iat[idmap[k]]) for k in hard):
        raise RuntimeError("9 protected native source science holds filled in error")
    remaining=int(trial.VPD_USE.isna().sum())
    if remaining!=79-len(changed) or remaining<9:
        raise RuntimeError("79 source missing not conserved")
    event_df=pd.DataFrame(reports)
    if len(event_df)!=30 or event_df.original_missing_halfhours.sum()!=70:
        raise RuntimeError("Signed original 30 segments 70 routine halfhours not conserved")
    patches=pd.DataFrame([
        {"native_key":time[i],"candidate_VPD_hPa":p[0],
         "candidate_QBOT_kgkg":p[1],"candidate_RH_pct":p[2],
         "method":"LINEAR_SELECTED_VPD_PHYSICS_BRIDGE",
         "operator_approved":False}
        for i,p in sorted(changed.items())
    ],columns=["native_key","candidate_VPD_hPa","candidate_QBOT_kgkg",
               "candidate_RH_pct","method","operator_approved"])
    holds=pd.DataFrame([
        {"native_key":time[int(i)],
         "hold_class":("NINE_SOURCE_EVENT_PROVENANCE_HARD_HOLD"
                       if time[int(i)] in hard else
                       "FINAL_UNRESOLVED_ROUTINE_HUMIDITY_GAP"),
         "required_action":("INDEPENDENT_SOURCE_T_AND_EVENT_REVIEW"
                            if time[int(i)] in hard else
                            "RETAIN_MISSING_DO_NOT_USE_AS_DATM"),
         "operator_approved":False}
        for i in original_missing if int(i) not in changed
    ])
    sites=pd.DataFrame([
        {"site":s,"current_source_provenance":("STAGE12AY_RESEARCH_ONLY_NOT_DATM"
            if s=="US-Kon" else "OTHER_NINE_NOT_VERIFIED_BY_THIS_KON_AUDIT"),
         "production_forcing_approved":False if s=="US-Kon" else None,
         "spinup_authorized":False if s=="US-Kon" else None}
        for s in SITES
    ])
    return trial,event_df,patches,holds,sites

def main():
    parser=argparse.ArgumentParser()
    modes=parser.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","finalize"):
        modes.add_argument("--"+opt,action="store_true")
    a=parser.parse_args()
    print("STAGE12AY FINAL KON 70-HH VPD BRIDGE & HOLD MANIFEST | "+VER,flush=True)
    selftest()
    if a.self_test:return
    trial,events,patches,holds,sites=assess()
    print("KON STAGE12AX ROUTINE 70 | PROTECTED 9 | ORIGINAL MISSING 79",flush=True)
    print("FINAL BRIDGE PASSED EVENT_N",int(events.local_bridge_numerical_pass.sum()),
          "ADDITIONAL_CANDIDATE_HH",len(patches),
          "UNRESOLVED_ROUTINE_HH",len(holds)-9,
          "SPECIAL_HARD_HOLD_HH",9,
          "NEW_TRIAL_TOTAL_MISSING",len(holds),flush=True)
    for reason,n in events.loc[~events.local_bridge_numerical_pass,"science_hold_reason"].value_counts().items():
        print("FINAL HOLD",reason,"EVENT_N",int(n),flush=True)
    print("BATCH03 10 SITES: US-Kon RESEARCH HOLD; other nine require independent input checks.",flush=True)
    print("NO FURTHER US-Kon AUTO STAGES. NO OPERATOR APPROVAL, DATM OR SPINUP.",flush=True)
    if a.check:
        print("STAGE12AY CHECK ONLY: ZERO WRITES",flush=True)
        return
    out=ROOT/"science_trials"/("stage12ay_Kon_FINAL_science_candidates_and_sealed_HOLDS_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
         "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={
      "US-Kon_STAGE12AY_FINAL_RESEARCH_ONLY_NOT_DATM_NOLEAP.csv":trial,
      "30_remaining_gap_final_VPD_bridge_event_decisions.csv":events,
      "new_final_physical_VPD_QBOT_bridge_candidates.csv":patches,
      "FINAL_UNRESOLVED_HUMIDITY_SOURCE_HOLDS.csv":holds,
      "Batch03_10_site_forcing_admission_status_UNVERIFIED.csv":sites}
    for name,data in outputs.items():
        data.to_csv(out/name,index=False)
    note="DO_NOT_RUN_AS_DATM_OR_SPINUP_UNAPPROVED"
    (out/note).write_text(
        "Science-only final Kon numeric candidates and sealed HOLD registry. "
        "Previously 79 Stage12an humidity, 1 Stage12aw QC0 interpolated and "
        "261 Stage12ax selected-anchor interpolated source rows are also "
        "unapproved. Final bridge hypotheses are likewise unapproved. "
        "Any missing humidity or unverified model variable is NOT acceptable "
        "as forcing without an explicit validation/approval process. "
        "Nine protected source-T & blocked-event keys remain missing. "
        "No source, previous science trial, DATM, CIME, Slurm or model writes. "
        "Other nine Batch03 site readiness cannot be inferred from Kon.\n")
    checks={n:digest(out/n) for n in [*outputs,note]}
    (out/"stage12ay_FINAL_research_HOLD_SHA_receipt.json").write_text(json.dumps({
      "version":VER,"signed_stage12ax_SHA256":digest(
          AX/"stage12ax_selected_anchor_QBOT_RH_SHA_receipt.json"),
      "original_stage12ax_missing":79,
      "additional_final_bridged_science_candidates":len(patches),
      "new_research_missing":len(holds),
      "nine_protected_native_science_holds":9,
      "other_nine_sites_production_status":"NOT_ASSESSED",
      "operator_approved":False,"Postv5_approved":False,
      "DATM_ready":False,"spinup_authorized":False,
      "output_SHA256":checks},indent=2)+"\n")
    print("STAGE12AY FINAL SEALED RESEARCH REPORT:",out,flush=True)
    print("ZERO ORIGINAL SOURCE, CLOCK, PREVIOUS SCIENCE, DATM OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as error:
        print("STAGE12AY STOP:",error,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

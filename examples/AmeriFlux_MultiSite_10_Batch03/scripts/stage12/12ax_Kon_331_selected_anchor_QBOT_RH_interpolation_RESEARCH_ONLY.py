#!/usr/bin/env python3
"""Stage12ax: one-pass source-provenance-aware selected-anchor VPD/QBOT gap trial.

Stage12aw validated 1 short QC0-anchored gap and retained 331 routine
missing humidity rows, plus nine protected source-T / blocked-event holds.
Stage12ax uses both ADJACENT FINITE *SELECTED* VPD/QBOT humidity anchors,
not necessarily both original tower QC0, to evaluate:
 A: linear selected specific humidity QBOT, thermodynamically derive VPD;
 B: linear selected RH from selected VPD/T, derive physically consistent QBOT.
A is preferred; B only if A fails, both need no >4hPa jumps across entire
time run, physical water/ice saturation, and <=24-hour contiguous gaps.
Original source QC flags for anchors are explicitly recorded. A selected
non-QC0 anchor is an uncertainty, never proof/approval. No standalone
empirical ERA RH if station vs ERA temperature provenance disagrees.
Zero writes for --check; --trial writes isolated RESEARCH ONLY files.

The nine protected native keys remain missing; the 48 + 31 previous
science-only fixes and Stage12ak non-humidity proposals are NOT approved.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VER="batch03-stage12ax-v1-20261026-Kon-selected-boundary-QBOT-RH-331"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AW=ROOT/"science_trials/stage12aw_Kon_shortgap_QC0_interpolation_RESEARCH_ONLY_20261026T130121Z_c9f21685"
AV=ROOT/"science_trials/stage12av_Kon_341_ERA_RH_fasttrack_RESEARCH_ONLY_20261026T121557Z_8d23d4cf"
S=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
SOURCE="US-Kon_STAGE12AW_SHORT_QC0_INTERPOLATION_NOT_DATM_NOLEAP.csv"
PROTECT="9_protected_native_science_holds.csv"
SPECIAL={"201102220900","201109291830"}
MAX_GAP=48
MAX_JUMP=4.0

def file(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Unsigned input absent or symlink: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()
def key(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def num(s):
    x=pd.to_numeric(s,errors="coerce")
    return x.mask(x<=-9990)
def esw(t):
    if not np.isfinite(t) or not (-85<t<55):return np.nan
    return 6.112*np.exp(17.67*t/(243.5+t))
def esi(t):
    if not np.isfinite(t) or not (-85<t<55):return np.nan
    return 6.112*np.exp(22.46*t/(272.62+t))
def from_q(t,p,q):
    if not np.isfinite([t,p,q]).all() or not(50000<p<110000 and 0<q<.08):
        return None
    e=q*p/(.622+.378*q)/100
    v=esw(t)-e
    if not np.isfinite([e,v]).all() or not(0<v<esw(t)) or (t<0 and e>1.02*esi(t)):
        return None
    return float(v),float(q),float(100*e/esw(t))
def from_rh(t,p,rh):
    if not np.isfinite([t,p,rh]).all() or not(50000<p<110000 and 0<rh<100):
        return None
    e=esw(t)*rh/100
    q=.622*(e*100)/(p-.378*(e*100))
    return from_q(t,p,q)
def halfhour(a,b):
    return pd.to_datetime(b,format="%Y%m%d%H%M")-pd.to_datetime(
        a,format="%Y%m%d%H%M")==pd.Timedelta(minutes=30)
def synthetic():
    assert from_q(20,100000,0.006) is not None
    assert from_q(20,100000,-.1) is None
    assert from_rh(20,100000,50) is not None
    assert from_rh(20,100000,150) is None
    assert halfhour("201110172330","201110180000")
    print("STAGE12AX SELF-TEST PASS | thermodynamic QBOT/RH source-anchor gaps; NO WRITES",flush=True)

def pinned():
    a=json.loads(file(AW/"stage12aw_QC0_shortgap_science_SHA_receipt.json").read_text())
    v=json.loads(file(AV/"stage12av_341_humidity_fasttrack_SHA_receipt.json").read_text())
    if not (a.get("version")=="batch03-stage12aw-v1-20261026-Kon-QC0-anchor-shortgap-science"
        and a.get("original_missing")==341 and a.get("routine_missing")==332
        and a.get("local_QC0_shortgap_numeric_fills")==1
        and a.get("new_research_missing")==340
        and a.get("protected_science_HOLDs")==9
        and a.get("operator_approved") is False
        and a.get("DATM_ready") is False and a.get("spinup_authorized") is False
        and a.get("upstream_stage12av_SHA256")==
            sha(AV/"stage12av_341_humidity_fasttrack_SHA_receipt.json")
        and v.get("original_missing")==341 and v.get("protected_count")==9
        and v.get("routine_new_numeric_research_patches")==0
        and v.get("operator_approval") is False
        and v.get("DATM_ready") is False):
        raise ValueError("Signed Stage12aw/av source integrity or original HOLD changed")
    for n in (SOURCE,"125_source_native_gap_event_QC0_anchor_decisions.csv",
              "safe_shortgap_local_QC0_interpolated_science_proposals.csv",
              "remaining_protected_and_routine_missing_native_humidity.csv",
              "SCIENTIFIC_ONLY_NO_OPERATOR_APPROVAL_NO_DATM"):
        if a.get("output_SHA256",{}).get(n)!=sha(AW/n):
            raise ValueError("Stage12aw SHA mismatch: "+n)
    if v.get("output_SHA256",{}).get(PROTECT)!=sha(AV/PROTECT):
        raise ValueError("9 protected source keys changed")
    manifest=json.loads(file(S/"exact_input_manifest.json").read_text())
    spec=next((x for x in manifest["sites"] if x["site"]=="US-Kon"),None)
    if spec is None:raise ValueError("US-Kon original tower source absent")
    known={str(Path(p).resolve()):h for p,h in manifest["input_sha256"].items()}
    orig=file(spec["primary"])
    if sha(orig)!=known.get(str(orig.resolve())):
        raise ValueError("Original tower source SHA mismatch")
    return spec

def segments(ind,keys):
    chunks=[];one=[]
    for i in ind:
        i=int(i)
        if one and (i!=one[-1]+1 or not halfhour(keys[one[-1]],keys[i])):
            chunks.append(one);one=[]
        one.append(i)
    if one:chunks.append(one)
    return chunks

def audit():
    spec=pinned()
    df=pd.read_csv(file(AW/SOURCE),dtype={"time":str},low_memory=False)
    if len(df)!=280320 or not {"time","VPD_USE","QBOT","TA_USE","PSRF"}<=set(df):
        raise ValueError("Pinned Stage12aw original selected NOLEAP schema changed")
    ks=key(df.time).tolist()
    if len(set(ks))!=len(ks) or not np.array_equal(df.VPD_USE.isna(),df.QBOT.isna()):
        raise ValueError("Original source-native clock/paired VPD/QBOT missing mask changed")
    hold=pd.read_csv(file(AV/PROTECT),dtype={"native_key":str})
    hard=set(hold.native_key)
    if len(hold)!=9 or len(hard)!=9 or not SPECIAL.issubset(hard):
        raise ValueError("Nine protected original source holds modified")
    idx={k:i for i,k in enumerate(ks)}
    if not hard.issubset(idx):
        raise ValueError("Hard source-T and blocked-event times missing from selected clock")
    miss=np.flatnonzero(df.VPD_USE.isna().to_numpy())
    routine=[int(i) for i in miss if ks[int(i)] not in hard]
    if len(miss)!=340 or len(routine)!=331 or len(miss)-len(routine)!=9:
        raise ValueError("Expected source 340 missing / 331 routine / 9 hard science holds")
    chunks=segments(routine,ks)
    # The 1 new Stage12aw fill must reduce 125 original routine chunks to
    # 124, without merging any source clock segments.
    if len(chunks)!=124:
        raise ValueError("Unexpected routine native contiguous segment count "+str(len(chunks)))
    raw=pd.read_csv(file(spec["primary"]),dtype={"TIMESTAMP_START":str},
         usecols=["TIMESTAMP_START","TA_F_QC","VPD_F_QC"],low_memory=False)
    raw["native_key"]=key(raw.TIMESTAMP_START)
    if raw.native_key.duplicated().any():
        raise ValueError("Original tower native source has duplicate timestamps")
    raw=raw.set_index("native_key")
    for c in ("TA_F_QC","VPD_F_QC"):raw[c]=num(raw[c])
    selected=df.copy(deep=True)
    decisions=[];changes={};perrecord=[]
    for run_id,part in enumerate(chunks,1):
        blockers=set()
        first,last=part[0],part[-1]
        a=first-1;b=last+1
        boundaries={}
        if len(part)>MAX_GAP:blockers.add("LONGER_THAN_24H_GAP")
        if a<0 or b>=len(df):
            blockers.add("DOMAIN_BOUNDARY")
        else:
            if not halfhour(ks[a],ks[first]) or not halfhour(ks[last],ks[b]):
                blockers.add("SOURCE_TIME_GAP")
            if ks[a] in hard or ks[b] in hard:
                blockers.add("PROTECTED_NEIGHBOR")
            for side,j in (("left",a),("right",b)):
                t=float(df.TA_USE.iat[j])
                p=float(df.PSRF.iat[j])
                v=float(df.VPD_USE.iat[j])
                q=float(df.QBOT.iat[j])
                valid=from_q(t,p,q)
                if valid is None or not np.isfinite(v) or not (0<=v<esw(t)):
                    blockers.add("SELECTED_ANCHOR_THERMODYNAMIC_PHYSICS_FAIL")
                    continue
                # Do not pretend an original source-QC1 value is a measurement;
                # check consistency of the selected VPD and selected QBOT.
                qc=float(raw.loc[ks[j],"VPD_F_QC"]) if ks[j] in raw.index else np.nan
                boundaries[side]={
                   "VPD":v,"QBOT":q,"RH":100*(1-v/esw(t)),
                   "pair_delta":abs(v-valid[0]),"source_VPD_QC":qc}
                if not(0<boundaries[side]["RH"]<100):
                    blockers.add("SELECTED_ANCHOR_VPD_RH_OUT_OF_BOUNDS")
                if boundaries[side]["pair_delta"]>1:
                    blockers.add("SELECTED_ANCHOR_QBOT_VPD_CONFLICT_GT1HPA")
        outputs={}
        trials={}
        if len(boundaries)==2 and not blockers:
            for method in ("LINEAR_QBOT","LINEAR_RH"):
                rows={};fail=set()
                for j in part:
                    fraction=(j-a)/(b-a)
                    t=float(df.TA_USE.iat[j])
                    p=float(df.PSRF.iat[j])
                    if method=="LINEAR_QBOT":
                        q=boundaries["left"]["QBOT"]+(boundaries["right"]["QBOT"]-
                            boundaries["left"]["QBOT"])*fraction
                        x=from_q(t,p,q)
                    else:
                        rh=boundaries["left"]["RH"]+(boundaries["right"]["RH"]-
                            boundaries["left"]["RH"])*fraction
                        x=from_rh(t,p,rh)
                    if x is None:
                        fail.add("INTERIOR_WATER_ICE_VPD_QBOT_PHYSICS")
                        continue
                    rows[j]=x
                vmax=np.nan
                if len(rows)==len(part):
                    vv=[boundaries["left"]["VPD"]]+[rows[j][0] for j in part]+[
                        boundaries["right"]["VPD"]]
                    jump=np.abs(np.diff(vv))
                    vmax=float(np.max(jump))
                    if not (np.isfinite(jump).all() and np.all(jump<=MAX_JUMP)):
                        fail.add("ONE_OR_MORE_30MIN_VPD_JUMPS_GT4HPA")
                else:
                    fail.add("PARTIAL_SEGMENT_CANNOT_BE_USED")
                trials[method]={"rows":rows,"reasons":fail,"max_jump":vmax}
            for method in ("LINEAR_QBOT","LINEAR_RH"):
                if not trials[method]["reasons"]:
                    outputs=trials[method]["rows"]
                    selected_method=method
                    break
            else:
                selected_method="NONE"
                for candidate in trials.values():blockers.update(candidate["reasons"])
        else:
            selected_method="NONE"
        passed=bool(outputs) and not blockers
        if passed:
            for j,value in outputs.items():
                if j in changes or ks[j] in hard:
                    raise ValueError("Overlap/protected original native source row")
                changes[j]=value
                selected.loc[j,"VPD_USE"]=value[0]
                selected.loc[j,"QBOT"]=value[1]
                perrecord.append({
                  "run_id":run_id,"native_key":ks[j],
                  "method":selected_method,
                  "selected_research_VPD_hPa":value[0],
                  "selected_research_QBOT_kgkg":value[1],
                  "selected_research_RH_pct":value[2],
                  "original_left_VPD_source_QC":boundaries["left"]["source_VPD_QC"],
                  "original_right_VPD_source_QC":boundaries["right"]["source_VPD_QC"],
                  "operator_approved":False})
        decisions.append({
           "run_id":run_id,"first_native_key":ks[first],"last_native_key":ks[last],
           "consecutive_30min_missing":len(part),
           "left_original_source_VPD_QC":boundaries.get("left",{}).get("source_VPD_QC",np.nan),
           "right_original_source_VPD_QC":boundaries.get("right",{}).get("source_VPD_QC",np.nan),
           "both_source_QC0_anchors":bool(
              boundaries.get("left",{}).get("source_VPD_QC",np.nan)==0 and
              boundaries.get("right",{}).get("source_VPD_QC",np.nan)==0),
           "selected_anchor_QBOT_VPD_consistency_pass":len(boundaries)==2 and
              not any(s.startswith("SELECTED_ANCHOR") for s in blockers),
           "preferred_method":selected_method,
           "numeric_research_segment_pass":passed,
           "failure_reasons":";".join(sorted(blockers)),
           "operator_approved":False})
    if sum(x["consecutive_30min_missing"] for x in decisions)!=331:
        raise ValueError("Source gap accounting changed: 331 routine must be present")
    v0=df.VPD_USE.to_numpy(dtype=float)
    v1=selected.VPD_USE.to_numpy(dtype=float)
    q0=df.QBOT.to_numpy(dtype=float)
    q1=selected.QBOT.to_numpy(dtype=float)
    difference=(~np.isclose(v0,v1,rtol=0,atol=1e-10,equal_nan=True) |
                ~np.isclose(q0,q1,rtol=0,atol=1e-12,equal_nan=True))
    if set(np.flatnonzero(difference))!=set(changes):
        raise ValueError("Modification outside unprotected 331 source-native missing rows")
    for col in df.columns:
        if col not in ("VPD_USE","QBOT") and not df[col].equals(selected[col]):
            raise ValueError("Previously protected meteorological selected field changed "+col)
    if not np.array_equal(selected.VPD_USE.isna(),selected.QBOT.isna()):
        raise ValueError("Trial VPD/QBOT missing masks do not match")
    if any(pd.notna(selected.VPD_USE.iat[idx[k]]) for k in hard):
        raise ValueError("Previously protected original source HOLD mistakenly filled")
    newmissing=int(selected.VPD_USE.isna().sum())
    if newmissing!=340-len(changes) or newmissing<9:
        raise ValueError("Original source 340 gaps not conserved")
    leftover=pd.DataFrame([{
         "native_key":ks[j],
         "status":"NINE_PREVIOUS_SCIENTIFIC_HOLDS" if ks[j] in hard else
             "UNRESOLVED_NONPROTECTED_HUMIDITY_SEGMENT",
         "operator_approved":False
      } for j in miss if int(j) not in changes])
    runs=pd.DataFrame(decisions)
    added=pd.DataFrame(perrecord,columns=[
        "run_id","native_key","method","selected_research_VPD_hPa",
        "selected_research_QBOT_kgkg","selected_research_RH_pct",
        "original_left_VPD_source_QC","original_right_VPD_source_QC","operator_approved"])
    return selected,runs,added,leftover

def main():
    parser=argparse.ArgumentParser()
    g=parser.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","trial"):g.add_argument("--"+x,action="store_true")
    a=parser.parse_args()
    print("STAGE12AX Kon TWO SELECTED-HUMIDITY ANCHOR SCIENCE TRIAGE | "+VER,flush=True)
    synthetic()
    if a.self_test:return
    selected,events,added,missing=audit()
    n=len(added); passed=int(events.numeric_research_segment_pass.sum())
    print("STAGE12AX ORIGINAL_MISSING 340 | NINE_PROTECTED 9 | ROUTINE 331 | SEGMENTS 124",flush=True)
    print("STAGE12AX NUMERIC_RESEARCH_SEGMENTS_PASS",passed,
          "NEW_CANDIDATE_HALFHOURS",n,"REMAINING_ROUTINE",331-n,
          "TRIAL_TOTAL_MISSING",len(missing),flush=True)
    print("\n===== COMPACT FAILED SEGMENT CATEGORIES =====",flush=True)
    reasons={}
    for message in events.loc[~events.numeric_research_segment_pass,"failure_reasons"]:
        for r in str(message).split(";"):
            if r:reasons[r]=reasons.get(r,0)+1
    for r,c in sorted(reasons.items(),key=lambda x:-x[1]):print(r,c,flush=True)
    print("STAGE12AX PREVIOUS 9 PROTECTED SOURCE-EVENT HOLDS KEPT; THIS IS NOT DATM-READY",flush=True)
    if a.check:
        print("STAGE12AX CHECK ONLY | ZERO FILE WRITES",flush=True)
        return
    out=ROOT/"science_trials"/("stage12ax_Kon_331_selected_anchor_humidity_RESEARCH_ONLY_"+
           datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={
      "US-Kon_STAGE12AX_SELECTED_ANCHORS_NO_DATM_NOLEAP.csv":selected,
      "124_remaining_routine_source_native_segments.csv":events,
      "new_science_only_source_native_VPD_QBOT_candidates.csv":added,
      "all_unresolved_original_missing_and_nine_protected.csv":missing}
    for f,table in outputs.items():table.to_csv(out/f,index=False)
    note="RESEARCH_HYPOTHESIS_NO_OPERATOR_APPROVAL_NO_DATM"
    (out/note).write_text(
        "All interpolated humidity values are science hypotheses based on "
        "upstream selected VPD/QBOT source values, not independent observed QC0 "
        "measurements. The original 9 scientific source-T/boundary holds remain "
        "missing. Original 48+31 Stage12an humidity trials and Stage12ak "
        "nonhumidity proposals are NOT production-approved. No original "
        "met source, source clock, model, CIME/DATM, or Slurm edits.\n")
    dig={name:sha(out/name) for name in [*outputs,note]}
    (out/"stage12ax_selected_anchor_QBOT_RH_SHA_receipt.json").write_text(
       json.dumps({
          "version":VER,"upstream_stage12aw_SHA256":sha(
            AW/"stage12aw_QC0_shortgap_science_SHA_receipt.json"),
          "original_missing":340,"original_routine_missing":331,
          "nine_protected_source_holds":9,
          "new_numerical_candidates_unapproved":len(added),
          "trial_remaining_missing":len(missing),
          "stage12an_79_prior_proposals_unapproved":True,
          "operator_approved":False,"Postv5_approved":False,
          "DATM_ready":False,"spinup_authorized":False,
          "output_SHA256":dig},indent=2)+"\n")
    print("STAGE12AX SCIENTIFIC ONLY TRIAL DIR:",out,flush=True)
    print("NO SOURCE, CLOCK, PRIOR TRIAL, DATM, SPINUP OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AX STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

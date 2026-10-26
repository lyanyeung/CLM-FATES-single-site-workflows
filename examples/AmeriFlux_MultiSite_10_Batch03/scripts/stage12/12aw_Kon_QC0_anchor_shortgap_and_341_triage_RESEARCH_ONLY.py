#!/usr/bin/env python3
"""Stage12aw — one-pass US-Kon SHORT QC0-ANCHORED local-RH interpolation.

Stage12av returned zero of 332 routine ERA repairs because of 5C
tower/ERA T disagreement (307 rows), RH physics (3 rows), source
QC (3 rows), or 4hPa jump (19 rows). Instead of relaxing any thresholds
or repeatedly auditing those rows, attempt strictly local, short gap
interpolation with SOURCE MEASURED ORIGINAL QC0 VPD and TA on BOTH sides.

Requirements (all must hold):
  * contiguous 30-minute missing VPD/QBOT segment, <= 4 halfhours (2 h)
  * two neighbors both source TA_F_QC=0 and VPD_F_QC=0; selected VPD finite
  * all gap source TA_F_QC=0 and source VPD_F_QC in (1,2)
  * selected T,P physically valid and close to original source T (<=0.5C)
  * interpolate RH between the two QC0 anchors, NOT copy ERA RH
  * anchor RH both strictly between 0 and 100; total RH endpoint span <=20pp
  * interpolation valid water/ice QBOT physics and all VPD jumps <=4 hPa
  * NEVER touch any of seven blocked Stage12an events or two special T holds
  * do not modify prior 79 science candidates, selected T,P, other variables.

The output is scientific proposal, NOT operator-approved DATM input.
--self-test: only synthetic checks, no filesystem inputs/writes.
--check: SHA pin upstream and original source and audit, no writes.
--trial: output new signed RESEARCH ONLY shadow, compact shortgap and HOLD
         reports; no source, model, DATM, CIME, Slurm, or spinup changes.
"""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VER="batch03-stage12aw-v1-20261026-Kon-QC0-anchor-shortgap-science"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AV=R/"science_trials/stage12av_Kon_341_ERA_RH_fasttrack_RESEARCH_ONLY_20261026T121557Z_8d23d4cf"
AN=R/"science_trials/stage12an_Kon_55_center_connected_ERA_RH_science_only_20261026T040913Z_277a0364"
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
SOURCE="US-Kon_STAGE12AV_FASTTRACK_NOT_DATM_INCOMPLETE_NOLEAP.csv"
DECISIONS="routine_missing_segments_numerical_decisions.csv"
UNRESOLVED="unresolved_routine_native_missing_ERA_source_or_boundary.csv"
PROTECTED="9_protected_native_science_holds.csv"
RAW_CANDIDATES="all_332_routine_gap_source_native_ERA_science_candidates.csv"
MARK="INCOMPLETE_RESEARCH_ONLY_NO_DATM_NO_SPINUP"
AN_CSV="US-Kon_STAGE12AN_ERA_RH_CONNECTED_EPISODE_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv"
SPECIAL={"201102220900","201109291830"}
N_PROTECTED=9
MAX_GAP=4
MAX_RH_SPAN=20.0
MAX_JUMP=4.0

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Unsigned/missing input or symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def num(s):
    x=pd.to_numeric(s,errors="coerce")
    return x.mask(x<=-9990)

def stamp(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def satw(t):
    t=float(t)
    return 6.112*np.exp(17.67*t/(243.5+t))

def sati(t):
    t=float(t)
    return 6.112*np.exp(22.46*t/(272.62+t))

def rh_from(t,v):
    return 100*(1-float(v)/satw(float(t)))

def physical(t,p,rhpercent):
    if not np.isfinite([t,p,rhpercent]).all() or not(-85<t<55 and 50000<p<110000 and
              0<rhpercent<100):
        return None
    e=satw(t)*(rhpercent/100)
    v=satw(t)-e
    q=.622*e*100/(p-.378*e*100)
    if not(0<v<satw(t) and 0<q<0.08 and
            (t>=0 or e<=sati(t)*1.02)):
        return None
    return float(v),float(q)

def halfhour(a,b):
    return pd.to_datetime(b,format="%Y%m%d%H%M")-pd.to_datetime(
        a,format="%Y%m%d%H%M")==pd.Timedelta(minutes=30)

def selftest():
    assert physical(15,100000,50) is not None
    assert physical(15,100000,-1) is None
    assert halfhour("201110172330","201110180000")
    assert MAX_GAP==4 and len(SPECIAL)==2
    print("STAGE12AW SELF-TEST PASS | QC0 two-sided 30min RH interpolation; NO WRITES",flush=True)

def preflight():
    av=json.loads(safe(AV/"stage12av_341_humidity_fasttrack_SHA_receipt.json").read_text())
    an=json.loads(safe(AN/"stage12an_research_only_55_source_event_SHA_receipt.json").read_text())
    if not (av.get("version")=="batch03-stage12av-v1-20261026-Kon-341-missing-ERA-fasttrack-science"
        and av.get("original_missing")==341
        and av.get("routine_candidates")==332
        and av.get("protected_count")==9
        and av.get("routine_new_numeric_research_patches")==0
        and av.get("new_research_missing")==341
        and av.get("seven_failed_events_held") is True
        and av.get("two_hard_source_T_holds_held") is True
        and av.get("operator_approval") is False
        and av.get("DATM_ready") is False
        and av.get("spinup_authorized") is False
        and av.get("signed_stage12an_SHA256")==
            sha(AN/"stage12an_research_only_55_source_event_SHA_receipt.json")
        and an.get("Kon_stage12an_science_trial_VPD_missing")==341
        and an.get("research_center_pass_numerical")==48
        and an.get("original_finite_QC1_QC2_neighbor_source_humidity_changes")==31
        and an.get("operator_humidity_approval") is False
        and an.get("DATM_ready") is False):
        raise RuntimeError("Strict stage12av/an input lineage or science HOLD changed")
    for name in (SOURCE,DECISIONS,UNRESOLVED,PROTECTED,RAW_CANDIDATES,MARK):
        if av.get("output_SHA256",{}).get(name)!=sha(AV/name):
            raise RuntimeError("Stage12av signed input changed: "+name)
    if an.get("output_SHA256",{}).get(AN_CSV)!=sha(AN/AN_CSV):
        raise RuntimeError("Stage12an source shadow changed")
    manifest=json.loads(safe(S/"exact_input_manifest.json").read_text())
    spec=next((v for v in manifest["sites"] if v["site"]=="US-Kon"),None)
    if spec is None:raise RuntimeError("Kon original primary source absent")
    pin={str(Path(k).resolve()):v for k,v in manifest["input_sha256"].items()}
    p=safe(spec["primary"])
    if sha(p)!=pin.get(str(p.resolve())):
        raise RuntimeError("Original FLUXMET source sha mismatch")
    return spec

def make_segments(indices,keys):
    groups=[]
    curr=[]
    for j in indices:
        j=int(j)
        if curr and (j!=curr[-1]+1 or not halfhour(keys[curr[-1]],keys[j])):
            groups.append(curr)
            curr=[]
        curr.append(j)
    if curr:groups.append(curr)
    return groups

def assess():
    spec=preflight()
    base=pd.read_csv(safe(AV/SOURCE),dtype={"time":str},low_memory=False)
    av_original=pd.read_csv(safe(AN/AN_CSV),dtype={"time":str},
                            usecols=["time","VPD_USE","QBOT"],low_memory=False)
    if len(base)!=280320 or len(av_original)!=len(base):
        raise RuntimeError("Selected native NOLEAP time/row count changed")
    keys=stamp(base.time).tolist()
    if len(set(keys))!=len(keys) or keys!=stamp(av_original.time).tolist():
        raise RuntimeError("Original native key/time changed")
    if not {"VPD_USE","QBOT","TA_USE","PSRF"}.issubset(base.columns):
        raise RuntimeError("Original Stage12av selected variables unavailable")
    if not np.array_equal(base.VPD_USE.isna().to_numpy(),base.QBOT.isna().to_numpy()):
        raise RuntimeError("VPD/QBOT selected missing masks differ")
    for col in ("VPD_USE","QBOT"):
        if not np.array_equal(base[col].to_numpy(),av_original[col].to_numpy(),equal_nan=True):
            raise RuntimeError("Zero-patch Stage12av must equal signed Stage12an source "+col)
    raw=pd.read_csv(safe(spec["primary"]),
       usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
       dtype={"TIMESTAMP_START":str},low_memory=False)
    raw["TIMESTAMP_START"]=stamp(raw.TIMESTAMP_START)
    if raw.TIMESTAMP_START.duplicated().any():
        raise RuntimeError("Original tower duplicated native timestamps")
    raw.set_index("TIMESTAMP_START",inplace=True)
    for c in raw.columns:raw[c]=num(raw[c])
    holds=pd.read_csv(safe(AV/PROTECTED),dtype={"native_key":str},low_memory=False)
    held=set(holds.native_key)
    if len(held)!=9 or len(holds)!=9 or not SPECIAL.issubset(held):
        raise RuntimeError("Nine historic original science holds changed")
    idx={k:j for j,k in enumerate(keys)}
    if not held.issubset(idx):
        raise RuntimeError("Protected original science holds missing from native clock")
    original_missing=np.flatnonzero(base.VPD_USE.isna().to_numpy())
    if len(original_missing)!=341 or sum(keys[i] in held for i in original_missing)!=9:
        raise RuntimeError("Source 341 missing and 9 protected science holes changed")
    routine=[int(i) for i in original_missing if keys[i] not in held]
    if len(routine)!=332:
        raise RuntimeError("Routine missing count not 332")
    groups=make_segments(routine,keys)
    if len(groups)!=125:
        raise RuntimeError("Original Stage12av 125 separate held segments changed")
    selected=base.copy(deep=True)
    decisions=[]
    replaced={}
    for event,indices in enumerate(groups,1):
        reasons=set()
        proposed={}
        a=indices[0]-1
        b=indices[-1]+1
        if len(indices)>MAX_GAP:reasons.add("LONG_GAP_OVER_4_HALFHOURS")
        if a<0 or b>=len(keys):reasons.add("MISSING_BOTH_NATIVE_BOUNDARIES")
        else:
            if not halfhour(keys[a],keys[indices[0]]) or \
               not halfhour(keys[indices[-1]],keys[b]):
                reasons.add("NATIVE_HALF_HOUR_EDGE_UNMATCHED")
            if keys[a] in held or keys[b] in held:
                reasons.add("NEAR_HISTORIC_PROTECTED_HOLD")
        boundaries={}
        if a>=0 and b<len(keys):
            for side,j in (("left",a),("right",b)):
                k=keys[j]
                if k not in raw.index:
                    reasons.add("ORIGINAL_QC0_ANCHOR_NOT_AVAILABLE")
                    continue
                src=raw.loc[k]
                t=float(base.TA_USE.iat[j])
                v=float(base.VPD_USE.iat[j])
                if not (src.TA_F_QC==0 and src.VPD_F_QC==0 and
                        np.isfinite([t,v,src.TA_F,src.VPD_F]).all() and
                        abs(t-float(src.TA_F))<=0.5 and
                        abs(v-float(src.VPD_F))<=0.05):
                    reasons.add("BOTH_BOUNDARIES_MUST_BE_PRESERVED_ORIGINAL_QC0_T_VPD")
                    continue
                rh=rh_from(t,v)
                if not (0<rh<100):
                    reasons.add("QC0_BOUNDARY_RH_NOT_PHYSICAL")
                    continue
                boundaries[side]={"RH":rh,"VPD":v}
        if len(boundaries)==2 and \
             abs(boundaries["left"]["RH"]-boundaries["right"]["RH"])>MAX_RH_SPAN:
            reasons.add("QC0_BOUNDARY_RH_DIFFERENCE_OVER_20PP")
        for j in indices:
            k=keys[j]
            if k not in raw.index:
                reasons.add("GAP_ORIGINAL_TOWER_SOURCE_ABSENT")
                continue
            src=raw.loc[k]
            t=float(base.TA_USE.iat[j])
            p=float(base.PSRF.iat[j])
            if not(np.isfinite([t,p,src.TA_F,src.TA_F_QC,src.VPD_F_QC]).all()
                and int(src.TA_F_QC)==0
                and int(src.VPD_F_QC) in (1,2)
                and abs(t-float(src.TA_F))<=0.5):
                reasons.add("GAP_REQUIRES_ORIGINAL_T_QC0_AND_HUMIDITY_QC1_QC2")
                continue
            if len(boundaries)<2:continue
            fraction=(j-a)/(b-a)
            interp=boundaries["left"]["RH"]+(boundaries["right"]["RH"]-
                                             boundaries["left"]["RH"])*fraction
            pval=physical(t,p,interp)
            if pval is None:
                reasons.add("INTERPOLATED_RH_QBOT_WATER_ICE_PHYSICS_FAIL")
                continue
            proposed[j]={"VPD":pval[0],"QBOT":pval[1],"RH":interp}
        if len(proposed)!=len(indices):
            reasons.add("SOURCE_OR_PHYSICAL_CANDIDATES_INCOMPLETE")
        max_j=np.nan
        if len(proposed)==len(indices) and len(boundaries)==2:
            vals=[boundaries["left"]["VPD"]]+[proposed[j]["VPD"] for j in indices]+[
                boundaries["right"]["VPD"]]
            jumps=[abs(vals[i+1]-vals[i]) for i in range(len(vals)-1)]
            max_j=max(jumps)
            if not all(np.isfinite(j) and j<=4 for j in jumps):
                reasons.add("INTERPOLATED_VPD_30MIN_JUMP_GT4HPA")
        passed=not reasons
        if passed:
            for j in indices:
                if j in replaced or keys[j] in held:
                    raise RuntimeError("Overlap or protected original source hold overwritten")
                replaced[j]=proposed[j]
                selected.loc[j,"VPD_USE"]=proposed[j]["VPD"]
                selected.loc[j,"QBOT"]=proposed[j]["QBOT"]
        decisions.append({
            "segment":event,"first_native_key":keys[indices[0]],
            "last_native_key":keys[indices[-1]],
            "half_hour_count":len(indices),
            "both_endpoints_original_source_QC0_T_and_VPD":len(boundaries)==2,
            "local_QC0_interpolated_RH_numeric_pass":passed,
            "candidate_rows":len(proposed),
            "max_30min_VPD_jump_hPa":max_j,
            "held_reasons":";".join(sorted(reasons)),
            "operator_approved":False})
    count=len(replaced)
    before_v=base.VPD_USE.to_numpy(dtype=float)
    after_v=selected.VPD_USE.to_numpy(dtype=float)
    before_q=base.QBOT.to_numpy(dtype=float)
    after_q=selected.QBOT.to_numpy(dtype=float)
    differences=(~np.isclose(before_v,after_v,rtol=0,atol=1e-10,equal_nan=True) |
                 ~np.isclose(before_q,after_q,rtol=0,atol=1e-12,equal_nan=True))
    if set(np.flatnonzero(differences))!=set(replaced):
        raise RuntimeError("Extra changes to previously selected source humidity")
    for name in base.columns:
        if name not in ("VPD_USE","QBOT") and not base[name].equals(selected[name]):
            raise RuntimeError("Nonhumidity source T, P, clocks or fields changed")
    if any(pd.notna(selected.VPD_USE.iat[idx[k]]) for k in held):
        raise RuntimeError("Special 9 science HOLDs unexpectedly filled")
    if not np.array_equal(selected.VPD_USE.isna().to_numpy(),
                          selected.QBOT.isna().to_numpy()):
        raise RuntimeError("Selected VPD/QBOT missing mask diverged")
    remaining=int(selected.VPD_USE.isna().sum())
    if remaining!=341-count or remaining<9:
        raise RuntimeError("Gap count conservation failed")
    report=pd.DataFrame(decisions)
    if len(report)!=125 or int(report.half_hour_count.sum())!=332 or \
        int(report.loc[report.local_QC0_interpolated_RH_numeric_pass,"half_hour_count"].sum())!=count:
        raise RuntimeError("125 source segments / 332 routine gap counts altered")
    source_proposed=pd.DataFrame([{
      "native_key":keys[j],
      "research_RH_interpolated_pct":value["RH"],
      "research_VPD_hPa":value["VPD"],
      "research_QBOT_kgkg":value["QBOT"],
      "two_original_QC0_source_boundaries":True,
      "operator_approved":False} for j,value in sorted(replaced.items())],
      columns=["native_key","research_RH_interpolated_pct","research_VPD_hPa",
               "research_QBOT_kgkg","two_original_QC0_source_boundaries","operator_approved"])
    unfilled=pd.DataFrame([{
      "native_key":keys[j],
      "category":"PROTECTED_9_SCIENCE_HOLD" if keys[j] in held else
                 "ROUTINE_NOT_ELIGIBLE_FOR_LOCAL_QC0_INTERPOLATION",
      "operator_approved":False} for j in original_missing if j not in replaced],
      columns=["native_key","category","operator_approved"])
    return selected,report,source_proposed,unfilled

def main():
    parser=argparse.ArgumentParser()
    options=parser.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","trial"):
        options.add_argument("--"+name,action="store_true")
    a=parser.parse_args()
    print("STAGE12AW Kon SOURCE QC0 LOCAL RH SHORTGAP RESEARCH FASTTRACK | "+VER,flush=True)
    selftest()
    if a.self_test:return
    chosen,decisions,proposed,unfilled=assess()
    count=len(proposed)
    passed=int(decisions.local_QC0_interpolated_RH_numeric_pass.sum())
    print("STAGE12AW ORIGINAL_STAGE12AN_MISSING 341 | NINE PROTECTED 9 |",
          "ROUTINE 332 | SEGMENTS 125",flush=True)
    print("STAGE12AW LOCAL_QC0_SHORTGAP_SEGMENTS_PASS",passed,
          "NEW_NUMERIC_RESEARCH_ROWS",count,
          "ROUTINE_STILL_MISSING",332-count,
          "TOTAL_RESEARCH_MISSING",len(unfilled),flush=True)
    print("\n======= COMPACT REJECTION SUMMARY (EVENT COUNTS) =======",flush=True)
    fails=decisions.loc[~decisions.local_QC0_interpolated_RH_numeric_pass]
    flags={}
    for val in fails.held_reasons:
        for reason in str(val).split(";"):
            if reason:flags[reason]=flags.get(reason,0)+1
    for reason,n in sorted(flags.items(),key=lambda x:-x[1]):
        print(f"{reason} EVENT_N {n}",flush=True)
    if passed:
        print("\n======= ELIGIBLE SHORT QC0-ANCHORED EPISODES =======",flush=True)
        print(decisions.loc[decisions.local_QC0_interpolated_RH_numeric_pass].
              to_string(index=False),flush=True)
    print("STAGE12AW 7 EVENT CENTERS + 2 SOURCE T SPECIAL HOLDS ALWAYS PROTECTED;",
          "no Post-v5, DATM, or spinup approval",flush=True)
    if a.check:
        print("STAGE12AW CHECK ONLY | ZERO FILES WRITTEN",flush=True)
        return
    out=R/"science_trials"/(
       "stage12aw_Kon_shortgap_QC0_interpolation_RESEARCH_ONLY_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    output={
      "US-Kon_STAGE12AW_SHORT_QC0_INTERPOLATION_NOT_DATM_NOLEAP.csv":chosen,
      "125_source_native_gap_event_QC0_anchor_decisions.csv":decisions,
      "safe_shortgap_local_QC0_interpolated_science_proposals.csv":proposed,
      "remaining_protected_and_routine_missing_native_humidity.csv":unfilled}
    for n,df in output.items():
        df.to_csv(out/n,index=False)
    warning="SCIENTIFIC_ONLY_NO_OPERATOR_APPROVAL_NO_DATM"
    (out/warning).write_text(
        "No interpolation candidate, including numerically passed source-QC0 "
        "boundary hypotheses, is approved for production. No original source "
        "or Stage12an/Stage12av trial was modified. All 9 previously protected "
        "source-T/failed-event points remain held. Selected temporal order, "
        "original QC0 source values, all non-humidity met variables unchanged. "
        "No full forcing acceptance, no DATM, no CIME, no Slurm and no spinup.\n")
    hashes={n:sha(out/n) for n in [*output,warning]}
    (out/"stage12aw_QC0_shortgap_science_SHA_receipt.json").write_text(
       json.dumps({
          "version":VER,
          "upstream_stage12av_SHA256":sha(
              AV/"stage12av_341_humidity_fasttrack_SHA_receipt.json"),
          "original_missing":341,"routine_missing":332,
          "original_routine_segment_count":125,
          "local_QC0_shortgap_numeric_fills":count,
          "new_research_missing":len(unfilled),
          "protected_science_HOLDs":9,
          "operator_approved":False,"Postv5_approved":False,
          "DATM_ready":False,"spinup_authorized":False,
          "output_SHA256":hashes},indent=2)+"\n")
    print("STAGE12AW INCOMPLETE SCIENCE ONLY DIR:",out,flush=True)
    print("NO SOURCE, PRIOR TRIAL, CLOCK, DATM, CIME, SLURM OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AW STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

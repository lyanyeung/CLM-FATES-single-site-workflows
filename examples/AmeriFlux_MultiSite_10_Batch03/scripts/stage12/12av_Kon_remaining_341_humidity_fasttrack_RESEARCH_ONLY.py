#!/usr/bin/env python3
"""Stage12av — QUICK one-pass Kon remaining 341 VPD/QBOT missing triage.

Use SHA-signed Stage12an (79 physical ERA humidity candidate edits retained)
and ORIGINAL exact same-native FLUXMET + ERA companion to screen all 341
remaining missing rows once. NEVER repair two protected source-T timestamps
or the seven previously blocked Stage12an event centers.

Automatically propose only entire isolated or consecutive missing runs for
which:
 - original source VPD QC is 1/2 (never reinterpret QC0 truth);
 - original native tower/ERA timestamps match, |selected T - ERA T|<=5C;
 - paired ERA RH is 0-100%, water/ice saturation and QBOT physical;
 - every internal 30min candidate VPD jump <=4hPa and TWO existing outer
   original selected humidity endpoints are finite and <=4hPa to candidate.
 - maximum unprotected run 96 halfhours, no crossing protected timestamps.
Rejected/uncertain segments remain missing and are reported with reason.

--self-test: synthetic physics + grouping only, no I/O.
--check: verify signed immutable input; evaluate all gaps, NO WRITES.
--trial: output NEW isolated signed RESEARCH-ONLY shadow selected CSV and
         gap/held reports, but NEVER production or DATM inputs.
All 48 Stage12an center fills and 31 finite source neighbors remain science
candidates (numerically passed, not separately operator-approved).
All original source, QC0 values, other science trials, clocks, spinup and
Slurm inputs are unchanged.
"""
import argparse, hashlib, json, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage12av-v1-20261026-Kon-341-missing-ERA-fasttrack-science"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AN=R/"science_trials/stage12an_Kon_55_center_connected_ERA_RH_science_only_20261026T040913Z_277a0364"
AU=R/"reports/stage12au_Kon_3_original_QC1_neighbor_ablation_science_20261026T120933Z_ad73557d"
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
TRIAL="US-Kon_STAGE12AN_ERA_RH_CONNECTED_EPISODE_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv"
AN_EVENTS="connected_episode_pass_and_source_hold_reasons.csv"
SPECIAL={"201102220900","201109291830"}
MAX_RUN=96
MAX_JUMP=4.0

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Signed source absent or symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def native(series):
    return series.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def num(s):
    x=pd.to_numeric(s,errors="coerce")
    return x.mask(x<=-9990)

def satw(t):
    t=float(t)
    return 6.112*np.exp(17.67*t/(243.5+t))

def sati(t):
    t=float(t)
    return 6.112*np.exp(22.46*t/(272.62+t))

def candidate(t,p,era_t,era_vpd,qc):
    if not np.isfinite([t,p,era_t,era_vpd,qc]).all():
        return None,"SOURCE_OR_ERA_NONFINITE"
    if int(qc) not in (1,2):
        return None,"SOURCE_ORIGINAL_VPD_QC_NOT_1_OR_2"
    if abs(t-era_t)>5:
        return None,"SITE_MINUS_ERA_T_ABS_GT5C"
    if not(-85<t<55 and -85<era_t<55 and 50000<p<110000):
        return None,"T_OR_P_OUT_OF_DOMAIN"
    rh=1-era_vpd/satw(era_t)
    if not 0<rh<1:
        return None,"ERA_RH_OUT_OF_0_TO_100"
    e=satw(t)*rh
    v=satw(t)-e
    q=.622*e*100/(p-.378*e*100)
    if not(0<v<satw(t) and 0<q<.08 and (t>=0 or e<=sati(t)*1.02)):
        return None,"WATER_ICE_QBOT_PHYSICS"
    return {"VPD":float(v),"QBOT":float(q),"RH":float(rh*100),
            "TA_USE":float(t),"PSRF":float(p),"TA_ERA":float(era_t)},None

def halfhour(a,b):
    return (pd.to_datetime(b,format="%Y%m%d%H%M")-
            pd.to_datetime(a,format="%Y%m%d%H%M"))==pd.Timedelta(minutes=30)

def selftest():
    assert candidate(8,90000,8,4,1)[1] is None
    assert candidate(8,90000,8,4,0)[1]=="SOURCE_ORIGINAL_VPD_QC_NOT_1_OR_2"
    assert candidate(8,90000,16,4,1)[1]=="SITE_MINUS_ERA_T_ABS_GT5C"
    assert halfhour("201110172330","201110180000")
    assert len(SPECIAL)==2
    print("STAGE12AV SELF-TEST PASS | source-native candidate physics and edges; NO WRITES",flush=True)

def pin():
    an=json.loads(safe(AN/"stage12an_research_only_55_source_event_SHA_receipt.json").read_text())
    au=json.loads(safe(AU/"stage12au_three_neighbor_ablation_SHA_receipt.json").read_text())
    if not (an.get("version")=="batch03-stage12an-v1-20261026-Kon-connected-ERA-RH-55-centers"
        and an.get("Kon_stage12an_science_trial_VPD_missing")==341
        and an.get("research_center_pass_numerical")==48
        and an.get("original_finite_QC1_QC2_neighbor_source_humidity_changes")==31
        and an.get("numerical_event_trial_PASSED")==19
        and an.get("numerical_event_trial_HELD")==7
        and set(an.get("source_t_disagreement_hard_holds",[]))==SPECIAL
        and an.get("operator_humidity_approval") is False
        and an.get("DATM_ready") is False
        and an.get("spinup_authorized") is False
        and au.get("version")==
          "batch03-stage12au-v1-20261026-Kon-three-unflagged-neighbor-ablation"
        and au.get("stage12an_original_finite_neighbors_tested")==3
        and au.get("original_37_invalid_RH_stage12an_missing")==1
        and au.get("unresolved_native_key")=="201105261100"
        and au.get("seven_blocked_episodes_preserved") is True
        and au.get("two_special_source_T_holds_preserved") is True
        and au.get("operator_approved") is False
        and au.get("DATM_ready") is False):
        raise RuntimeError("Stage12an/AU signed research QC or HOLD status changed")
    for name in (TRIAL,AN_EVENTS,
                 "research_candidate_native_QC1_QC2_humidity_event_changes.csv",
                 "science_only_event_VPD_30min_boundaries.csv",
                 "INCOMPLETE_NUMERICAL_RESEARCH_HUMIDITY_NOT_OPERATOR_APPROVED_NO_DATM"):
        if an.get("output_SHA256",{}).get(name)!=sha(AN/name):
            raise RuntimeError("Stage12an signed source changed: "+name)
    if not(au.get("signed_stage12an_SHA256")==
           sha(AN/"stage12an_research_only_55_source_event_SHA_receipt.json")):
        raise RuntimeError("Stage12au chained original immutable Stage12an trial mismatch")
    manifest=json.loads(safe(S/"exact_input_manifest.json").read_text())
    spec=next((x for x in manifest["sites"] if x["site"]=="US-Kon"),None)
    if spec is None:raise RuntimeError("Kon source manifest absent")
    pins={str(Path(k).resolve()):v for k,v in manifest["input_sha256"].items()}
    for kind in ("primary","era"):
        path=safe(spec[kind])
        if sha(path)!=pins.get(str(path.resolve())):
            raise RuntimeError("Original "+kind+" native source SHA altered")
    return spec

def run():
    spec=pin()
    base=pd.read_csv(safe(AN/TRIAL),dtype={"time":str},low_memory=False)
    required={"time","VPD_USE","QBOT","TA_USE","PSRF"}
    if len(base)!=280320 or not required.issubset(base.columns):
        raise RuntimeError("Stage12an full Kon original-source NOLEAP schema changed")
    nkeys=native(base.time)
    if nkeys.duplicated().any():
        raise RuntimeError("Source native halfhour duplicate time")
    if not np.array_equal(base.VPD_USE.isna(),base.QBOT.isna()):
        raise RuntimeError("Paired VPD/QBOT Stage12an missing masks no longer equal")
    missing=np.flatnonzero(base.VPD_USE.isna().to_numpy())
    if len(missing)!=341:
        raise RuntimeError("Stage12an 341 remaining missing changed")
    events=pd.read_csv(safe(AN/AN_EVENTS),dtype={"seed_begin":str,"seed_end":str},low_memory=False)
    if len(events)!=26:
        raise RuntimeError("Original Stage12an science event table count changed")
    failed=events.loc[~events.research_numerical_pass.astype(str).str.lower().eq("true")]
    if len(failed)!=7 or not failed.seed_begin.equals(failed.seed_end):
        # seed_begin/seed_end Series equality also checks indexes (same selection)
        raise RuntimeError("Expected 7 one-time blocked centers; stop if more complex")
    failures=set(failed.seed_begin.astype(str))
    protected=failures|SPECIAL
    if len(protected)!=9:
        raise RuntimeError("Seven blocked event centers overlap two temperature exceptions")
    missingkeys=set(nkeys.iloc[missing])
    if not protected.issubset(missingkeys):
        raise RuntimeError("Protected source science holds are not still missing")
    rest=missingkeys-protected
    if len(rest)!=332:
        raise RuntimeError("341 remaining gaps did not resolve as 332 routine + 9 protected")
    ids=set(nkeys)
    tower=pd.read_csv(safe(spec["primary"]),
       usecols=["TIMESTAMP_START","VPD_F_QC"],dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(safe(spec["era"]),
       usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],dtype={"TIMESTAMP_START":str},low_memory=False)
    for d in (tower,era):
        d["TIMESTAMP_START"]=native(d.TIMESTAMP_START)
        if d.TIMESTAMP_START.duplicated().any():
            raise RuntimeError("Native original tower/ERA source duplicated")
        d.set_index("TIMESTAMP_START",inplace=True)
        for c in d.columns:d[c]=num(d[c])
    select=base.copy(deep=True)
    protected_idxs={int(i) for i in missing if nkeys.iat[i] in protected}
    chunks=[]
    cur=[]
    for idx in missing:
        idx=int(idx)
        if idx in protected_idxs:
            if cur:chunks.append(cur);cur=[]
            continue
        if cur and (idx!=cur[-1]+1 or not halfhour(nkeys.iat[cur[-1]],nkeys.iat[idx])):
            chunks.append(cur);cur=[]
        cur.append(idx)
    if cur:chunks.append(cur)
    decisions=[]
    gaps=[]
    patch_indices=set()
    for group,inds in enumerate(chunks,1):
        reason=set()
        candidates={}
        if len(inds)>MAX_RUN:
            reason.add("SEGMENT_EXCEEDS_96_HALFHOURS")
        for idx in inds:
            k=nkeys.iat[idx]
            s=tower.loc[k] if k in tower.index else None
            e=era.loc[k] if k in era.index else None
            try:
                qcf=float(s.VPD_F_QC) if s is not None else np.nan
                te=float(e.TA_ERA) if e is not None else np.nan
                ev=float(e.VPD_ERA) if e is not None else np.nan
                t=float(base.TA_USE.iat[idx])
                p=float(base.PSRF.iat[idx])
                new,why=candidate(t,p,te,ev,qcf)
            except (TypeError,ValueError,KeyError):
                new,why=None,"ORIGINAL_SOURCE_NONNUMERIC"
            if why:reason.add(why)
            if new:candidates[idx]=new
            gaps.append({
              "native_key":k,"segment":group,
              "original_source_VPD_QC":qcf if s is not None else np.nan,
              "original_selected_T_C":float(base.TA_USE.iat[idx]),
              "native_ERA_T_C":te if e is not None else np.nan,
              "native_ERA_VPD_hPa":ev if e is not None else np.nan,
              "ERA_RH_candidate_pct":new["RH"] if new else np.nan,
              "candidate_VPD_hPa":new["VPD"] if new else np.nan,
              "candidate_QBOT_kgkg":new["QBOT"] if new else np.nan,
              "candidate_cell_physics_pass":bool(new),
              "candidate_rejection_reason":why or "",
              "operator_approved":False})
        left=inds[0]-1
        right=inds[-1]+1
        if left<0 or right>=len(base):
            reason.add("NATIVE_DOMAIN_BOUNDARY")
        elif (not halfhour(nkeys.iat[left],nkeys.iat[inds[0]]) or
              not halfhour(nkeys.iat[inds[-1]],nkeys.iat[right])):
            reason.add("NATIVE_TIME_GAP_AT_SEGMENT_BOUNDARY")
        elif nkeys.iat[left] in protected or nkeys.iat[right] in protected:
            reason.add("NEIGHBOR_IS_PROTECTED_HOLD")
        elif (not np.isfinite(base.VPD_USE.iat[left]) or
              not np.isfinite(base.VPD_USE.iat[right])):
            reason.add("EXTERNAL_VPD_BOUNDARY_MISSING")
        if len(candidates)!=len(inds):
            reason.add("PARTIAL_SEGMENT_PHYSICS_OR_SOURCE")
        edges=[]
        if len(candidates)==len(inds) and left>=0 and right<len(base):
            values=[float(base.VPD_USE.iat[left])]+[candidates[i]["VPD"] for i in inds]+[
                 float(base.VPD_USE.iat[right])]
            edges=[abs(values[i+1]-values[i]) for i in range(len(values)-1)]
            if not all(np.isfinite(z) and z<=MAX_JUMP for z in edges):
                reason.add("OUTER_OR_INTERNAL_30MIN_VPD_JUMP_GT4HPA")
        pass_event=not reason
        if pass_event:
            for idx in inds:
                if idx in patch_indices:
                    raise RuntimeError("Overlapping source-native gap candidates")
                patch_indices.add(idx)
                select.loc[idx,"VPD_USE"]=candidates[idx]["VPD"]
                select.loc[idx,"QBOT"]=candidates[idx]["QBOT"]
        decisions.append({
          "segment":group,"first_native_key":nkeys.iat[inds[0]],
          "last_native_key":nkeys.iat[inds[-1]],
          "consecutive_native_halfhours":len(inds),
          "native_segment_duration_hours":len(inds)/2,
          "source_cell_physical_candidate_N":len(candidates),
          "local_VPD_jump_max_hPa":max(edges) if edges else np.nan,
          "numeric_source_and_boundary_pass":pass_event,
          "science_rejection_reasons":";".join(sorted(reason)),
          "operator_approved":False
        })
    if len(patch_indices)!=sum(
        d["consecutive_native_halfhours"] for d in decisions
        if d["numeric_source_and_boundary_pass"]):
        raise RuntimeError("Science proposed patch overlaps/gaps")
    if len(patch_indices)>332 or any(nkeys.iat[i] in protected for i in patch_indices):
        raise RuntimeError("Protected 9 source-T/boundary gaps released")
    changes=np.flatnonzero(
        ~np.isclose(select.VPD_USE.to_numpy(dtype=float),base.VPD_USE.to_numpy(dtype=float),
                    rtol=0,atol=1e-10,equal_nan=True) |
        ~np.isclose(select.QBOT.to_numpy(dtype=float),base.QBOT.to_numpy(dtype=float),
                    rtol=0,atol=1e-12,equal_nan=True))
    if set(changes)!=patch_indices:
        raise RuntimeError("Changes outside allowed 332 originally missing source-native cells")
    for c in base.columns:
        if c not in ("VPD_USE","QBOT") and not base[c].equals(select[c]):
            raise RuntimeError("Protected original selected forcing column changed "+c)
    if not np.array_equal(select.VPD_USE.isna().to_numpy(),
                           select.QBOT.isna().to_numpy()):
        raise RuntimeError("Selected VPD and QBOT missing masks diverge")
    remain=int(select.VPD_USE.isna().sum())
    if remain!=341-len(patch_indices) or remain<9:
        raise RuntimeError("Remaining humidity scientific held count changed")
    if any(pd.notna(select.VPD_USE.iat[i]) for i in protected_idxs):
        raise RuntimeError("Seven source events or two special T holds wrongly released")
    hold=pd.DataFrame([{
        "native_key":str(k),
        "science_hold_category":(
            "TWO_PROTECTED_ORIGINAL_SOURCE_T_HOLDS" if k in SPECIAL else
            "SEVEN_BLOCKED_STAGE12AN_NATIVE_EVENTS"),
        "approved":False} for k in sorted(protected)])
    decision=pd.DataFrame(decisions)
    gap_table=pd.DataFrame(gaps)
    hold_cases=pd.DataFrame([
        {"native_key":nkeys.iat[i],
         "status":"UNPROTECTED_ROUTINE_STILL_MISSING",
         "why":"SEGMENT_SOURCE_OR_BOUNDARY_FAIL",
         "approved":False}
        for i in missing if i not in protected_idxs and i not in patch_indices])
    return select,decision,gap_table,hold,hold_cases,len(patch_indices)

def main():
    p=argparse.ArgumentParser()
    a=p.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","trial"):
        a.add_argument("--"+k,action="store_true")
    args=p.parse_args()
    print("STAGE12AV Kon FASTTRACK 341 REMAINING HUMIDITY HOLDS | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    selected,events,gaps,protected,unresolved,n=run()
    passed=int(events.numeric_source_and_boundary_pass.astype(bool).sum())
    held=len(events)-passed
    print("\n===== BATCH03 KON NEW SCIENCE ONLY 341-GAP SUMMARY =====",flush=True)
    print("ORIGINAL_STAGE12AN_MISSING 341",
       "PROTECTED_MANUAL_SCIENCE_HOLDS 9 (7 EVENT CENTERS + 2 T EXCEPTIONS)",
       "ROUTINE_SCREENED 332",
       "FASTTRACK_GAPS_FILLED_NUMERICALLY",n,
       "ROUTINE_GAPS_HELD",len(unresolved),
       "TRIAL_TOTAL_STILL_MISSING",int(selected.VPD_USE.isna().sum()),flush=True)
    print("ROUTINE_SEGMENTS_PASS",passed,"ROUTINE_SEGMENTS_HELD",held,flush=True)
    print("\n===== HELD SEGMENTS (NO AUTO APPROVAL) =====",flush=True)
    if held:
        print(events.loc[~events.numeric_source_and_boundary_pass].to_string(index=False),flush=True)
    else:print("No routine segments held",flush=True)
    print("\n===== PROTECTED NATIVE SCIENCE HOLDS =====",flush=True)
    print(protected.to_string(index=False),flush=True)
    print("ALL Stage12an 48+31 science patches remain unapproved; prior Stage12ak",
          "non-humidity edits remain provisional; no Post-v5/DATM/spinup release",flush=True)
    if args.check:
        print("STAGE12AV CHECK ONLY | NO WRITE OR PRODUCTION",flush=True)
        return
    directory=R/"science_trials"/(
        "stage12av_Kon_341_ERA_RH_fasttrack_RESEARCH_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    directory.mkdir(parents=True,exist_ok=False)
    output={
       "US-Kon_STAGE12AV_FASTTRACK_NOT_DATM_INCOMPLETE_NOLEAP.csv":selected,
       "all_332_routine_gap_source_native_ERA_science_candidates.csv":gaps,
       "routine_missing_segments_numerical_decisions.csv":events,
       "9_protected_native_science_holds.csv":protected,
       "unresolved_routine_native_missing_ERA_source_or_boundary.csv":unresolved}
    for name,d in output.items():
        d.to_csv(directory/name,index=False)
    marker="INCOMPLETE_RESEARCH_ONLY_NO_DATM_NO_SPINUP"
    (directory/marker).write_text(
        "All changes are ERA humidity numerical candidates, not operator "
        "approvals. Stage12an 79 pass-science patches have no final Post-v5 "
        "release. Stage12ak non-humidity proposal also remains unapproved. "
        "Nine protected source-T and blocked-event science holds stay missing. "
        "Any other failed-source/boundary routine segments stay missing. "
        "Never use this research CSV as production DATM, CIME or spinup forcing. "
        "No original, native clock, previous trial, Slurm or model changes.\n")
    dig={k:sha(directory/k) for k in [*output,marker]}
    (directory/"stage12av_341_humidity_fasttrack_SHA_receipt.json").write_text(
        json.dumps({
          "version":VERSION,
          "signed_stage12an_SHA256":sha(AN/"stage12an_research_only_55_source_event_SHA_receipt.json"),
          "signed_stage12au_SHA256":sha(AU/"stage12au_three_neighbor_ablation_SHA_receipt.json"),
          "original_missing":341,"routine_candidates":332,"protected_count":9,
          "routine_new_numeric_research_patches":n,
          "new_research_missing":int(selected.VPD_USE.isna().sum()),
          "seven_failed_events_held":True,"two_hard_source_T_holds_held":True,
          "Stage12an_79_edits_still_unapproved":True,
          "operator_approval":False,"Postv5_approved":False,
          "DATM_ready":False,"spinup_authorized":False,
          "output_SHA256":dig},indent=2)+"\n")
    print("STAGE12AV SIGNED INCOMPLETE SCIENCE TRIAL DIR:",directory,flush=True)
    print("NO ORIGINAL, PRIOR RESEARCH, CLOCK, DATM, CIME OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE12AV STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

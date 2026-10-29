#!/usr/bin/env python3
"""US-Kon Batch03 Stage14K: 68 source-scoped paired ERA-RH research repairs.

Grounded in ACTUAL SHA-sealed Stage12AY 77 remaining missing HH and ACTUAL
Stage14J 77-row original-source/QC exact candidate receipt. Fill only 68
routine physical candidates into one NEW isolated model-format research CSV.
Leave all NINE signed special source/HOLD native hours VPD/QBOT missing,
and keep every previously finite input and ALL nonhumidity variables exact.
For each original missing source episode compute ALL 30min VPD, RH, QBOT
joins (including immediate source anchors) and original native source QC;
report discontinuities >4hPa VPD / >20 percentage points RH /
>0.003kgkg QBOT separately, not "corrected" by invented measurements.
Do not claim measured tower validation, Post-v5, DATM or spin-up readiness.
"""
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VER="batch03-US-Kon-68ERA-RH-research-9HOLD-v1-20261029"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
SOURCE=ROOT/"science_trials/stage12ay_Kon_FINAL_science_candidates_and_sealed_HOLDS_20261026T132804Z_87d94e7a"
J=ROOT/"reports/US_Kon_77_original_QC_and_ERA_research_candidates_20261029T044439Z_c1845aab"
SOURCE_CSV="US-Kon_STAGE12AY_FINAL_RESEARCH_ONLY_NOT_DATM_NOLEAP.csv"
SOURCE_RECEIPT="stage12ay_FINAL_research_HOLD_SHA_receipt.json"
J_RECEIPT="US_Kon_77_READONLY_SHA_receipt.json"
J_CSV="US_Kon_ALL77_exact_humidity_SOURCE_QC_ERA_anchor_decisions.csv"
HOLD_CSV="FINAL_UNRESOLVED_HUMIDITY_SOURCE_HOLDS.csv"
FIELDS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
LIMITS={"VPD_hPa":4.0,"RHwater_pp":20.0,"QBOT_kgkg":0.003}
def guard(x,s):
    if not bool(x):raise RuntimeError("US-Kon STAGE14K STOP NO SOURCE WRITE: "+str(s))
def file(p):
    p=Path(p)
    guard(p.is_file() and not p.is_symlink(),"signed source absent "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as b:
        for x in iter(lambda:b.read(1<<20),b""):h.update(x)
    return h.hexdigest()
def stamp(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def es(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(17.67*t/(t+243.5))
def eice(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(22.46*t/(t+272.62))
def water(q,t,p):
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        e=(q*p)/(.622+.378*q)/100
        rh=100*e/es(t)
    return e,rh
def test():
    guard(float(es(-20))>float(eice(-20)) and
      pd.Series(["abc",None]).equals(pd.Series(["abc",None])) and
      np.isclose(.622*100*8/(100000-.378*100*8),.005,atol=.00002),
      "mixed time / humidity thermodynamic self-test")
    print("US-Kon 68+9 PROTECTED SOURCE STAGE14K SELF-TEST PASS",flush=True)
def signed():
    sr=json.loads(file(SOURCE/SOURCE_RECEIPT).read_text())
    jr=json.loads(file(J/J_RECEIPT).read_text())
    guard(sr.get("version")=="batch03-stage12ay-v1-20261026-Kon-seal-final-70-humidity-holds" and
      sr.get("new_research_missing")==77 and
      sr.get("nine_protected_native_science_holds")==9 and
      sr.get("operator_approved") is False and sr.get("DATM_ready") is False,
      "Stage12AY original 77 missing/9 hard source receipt changed")
    guard(jr.get("version")=="batch03-US-Kon-77-source-QC-onepass-v1-20261029" and
      jr.get("science_approved") is False and
      jr.get("source_inputs_modified") is False,
      "Stage14J original full source/QC receipt changed")
    for root,rec in ((SOURCE,sr),(J,jr)):
        for name,h in rec["output_SHA256"].items():
            guard(sha(root/name)==h,"signed original output changed "+str(root/name))
    parent=pd.read_csv(file(SOURCE/SOURCE_CSV),dtype={"time":str},low_memory=False)
    ledger=pd.read_csv(file(J/J_CSV),dtype={"native_key":str},low_memory=False)
    hold=pd.read_csv(file(SOURCE/HOLD_CSV),dtype={"native_key":str},low_memory=False)
    guard(len(parent)==280320 and list(parent.columns)==FIELDS,
          "signed Stage12AY 280320 native selected schema changed")
    keys=stamp(parent.time)
    dt=pd.to_datetime(keys,format="%Y%m%d%H%M",errors="raise")
    guard(keys.is_unique and dt.is_monotonic_increasing and
          not bool(((dt.dt.month==2)&(dt.dt.day==29)).any()),
          "selected native original clock changed")
    empty=parent.VPD_USE.isna()
    guard(empty.equals(parent.QBOT.isna()) and empty.sum()==77,
          "Stage12AY original 77 paired humidity gaps changed")
    guard(len(ledger)==77 and ledger.native_key.is_unique and
          len(hold)==77 and hold.native_key.is_unique and
          set(ledger.native_key)==set(hold.native_key)==set(keys[empty]),
          "Stage14J 77 exact source/QC/hold times shifted")
    protected=set(hold.loc[hold.hold_class.eq(
       "NINE_SOURCE_EVENT_PROVENANCE_HARD_HOLD"),"native_key"])
    routine=ledger.loc[~ledger.hard_science_HOLD].copy()
    guard(len(protected)==9 and len(routine)==68 and
          set(ledger.loc[ledger.hard_science_HOLD,"native_key"])==protected and
          {"201102220900","201109291830"}<=protected,
          "nine operator protected native source science events changed")
    guard(routine.candidate_ERA_RH_VPD_hPa.notna().all() and
          routine.candidate_ERA_RH_QBOT.notna().all() and
          routine.candidate_water_ice_physics_pass.astype(str).str.lower().eq("true").all() and
          routine.source_evidence_decision.eq("ROUTINE_ERA_RH_ONLY_LOW_CONFIDENCE").all(),
          "68 original routine source physical candidates not fully signed")
    return parent,keys,dt,ledger,routine,protected
def joined_row(t,p,v,q):
    if not np.isfinite([t,p,v,q]).all():return None
    if not (50000<p<110000 and -80<t<65):return None
    ss=float(es(t));e=ss-v
    if not (0<v<ss and e>0 and 0<q<.08):return None
    qexpected=.622*100*e/(p-.378*100*e)
    if not np.isclose(q,qexpected,rtol=1e-6,atol=1e-8):return None
    rh=100*e/ss
    ri=100*e/float(eice(t)) if t<0 else np.nan
    return float(rh),float(ri)
def analyze():
    parent,keys,dt,ledger,routine,hard=signed()
    pos={key:i for i,key in enumerate(keys)}
    patch={}
    for row in routine.itertuples(index=False):
        key=row.native_key
        i=pos[key];t=float(parent.TA_USE.iat[i]);p=float(parent.PSRF.iat[i])
        v=float(row.candidate_ERA_RH_VPD_hPa)
        q=float(row.candidate_ERA_RH_QBOT)
        check=joined_row(t,p,v,q)
        guard(check is not None and (t>=0 or check[1]<=102.0),
              "routine ERA RH source candidate water/ice fails physical gate "+key)
        patch[i]=(v,q)
    guard(len(patch)==68 and all(keys.iat[i] not in hard for i in patch),
          "68 only original missing candidate scope")
    trial=parent.copy(deep=True)
    for i,(v,q) in patch.items():
        trial.at[i,"VPD_USE"]=v
        trial.at[i,"QBOT"]=q
    # No touched time, TA/TBOT, irradiance, pressure, rainfall, or previously
    # existing humidity: exact pandas equality for both numeric and strings.
    for c in FIELDS:
        if c not in ("VPD_USE","QBOT"):
            guard(parent[c].equals(trial[c]),"original source field modified "+c)
        else:
            preserved=np.ones(len(parent),bool)
            preserved[list(patch)]=False
            guard(parent.loc[preserved,c].reset_index(drop=True).equals(
                trial.loc[preserved,c].reset_index(drop=True)),
                "previously finite or protected original "+c+" modified")
    guard(trial.VPD_USE.isna().equals(trial.QBOT.isna()) and
          trial.VPD_USE.isna().sum()==9 and
          set(keys[trial.VPD_USE.isna()])==hard,
          "nine and ONLY nine original scientific hard holds must remain missing")
    # Check all 68 inserted source-native 30min water/QBOT/TA consistency.
    num=trial[FIELDS[1:]].apply(pd.to_numeric,errors="raise")
    all_non_humidity=list(set(FIELDS[1:])-{"VPD_USE","QBOT"})
    guard(not num[all_non_humidity].isna().any().any(),
          "non-humidity missing in full Stage12AY source")
    checkidx=np.array(sorted(patch))
    guard(np.isfinite(num.iloc[checkidx].to_numpy(float)).all(),
          "one of 68 candidate native fields remains missing")
    temp=num.TA_USE.to_numpy(float);p=num.PSRF.to_numpy(float)
    q=num.QBOT.to_numpy(float);v=num.VPD_USE.to_numpy(float)
    all_water_es=es(temp)
    reconstructed_e=all_water_es-v
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        expected_q=.622*100*reconstructed_e/(p-.378*100*reconstructed_e)
    inserted_all_closure=bool(np.all(np.isclose(
        q[checkidx],expected_q[checkidx],atol=1e-8,rtol=1e-6)))
    guard(inserted_all_closure,
          "new 68 water vapor pressure/QBOT model closure inconsistent")
    # Existing complete selected source rows need to be audited, not assumed
    # true due the new 68 numeric values.
    domain=np.flatnonzero(np.isfinite(q)&np.isfinite(v)&np.isfinite(temp)&np.isfinite(p))
    all_physics=(np.isclose(q[domain],expected_q[domain],atol=1e-8,rtol=1e-6)&
                 (v[domain]>=0)&(reconstructed_e[domain]>=0)&
                 np.isclose(num.TBOT.to_numpy(float)[domain],temp[domain]+273.15,
                            atol=1e-8,rtol=0))
    original_physics_fail=int((~all_physics).sum())
    missing_positions=set(np.flatnonzero(parent.VPD_USE.isna().to_numpy()))
    ordered=sorted(missing_positions)
    episode=[];start=prev=ordered[0]
    def make_episode(first,last):
        ids=list(range(first,last+1))
        kw=[keys.iat[i] for i in ids]
        before=first-1;after=last+1
        # Skip across missing protected source holds; never bridge them.
        chain=[i for i in [before]+ids+[after] if 0<=i<len(parent)]
        rows=[]
        for left,right in zip(chain,chain[1:]):
            if dt.iat[right]-dt.iat[left]!=pd.Timedelta(minutes=30):
                continue
            ra=joined_row(temp[left],p[left],v[left],q[left])
            rb=joined_row(temp[right],p[right],v[right],q[right])
            if ra is None or rb is None:
                rows.append((keys.iat[left],keys.iat[right],np.nan,np.nan,np.nan,
                             "MISSING_OR_UNPHYSICAL_ANCHOR"))
                continue
            jumps=(abs(v[right]-v[left]),abs(rb[0]-ra[0]),abs(q[right]-q[left]))
            reasons=[name for name,bad in (
                 ("VPD_JUMP_GT4",jumps[0]>4),
                 ("RH_JUMP_GT20PP",jumps[1]>20),
                 ("QBOT_JUMP_GT0.003",jumps[2]>.003)) if bad]
            rows.append((keys.iat[left],keys.iat[right],*jumps,
                         ";".join(reasons) if reasons else "PASS"))
        nHard=sum(k in hard for k in kw)
        nRoutine=len(kw)-nHard
        nNew=sum(i in patch for i in ids)
        valid=[x for x in rows if x[5]=="PASS"]
        flags=[x for x in rows if x[5]!="PASS"]
        return dict(start_native_key=kw[0],end_native_key=kw[-1],
           original_missing_n=len(ids),protected_science_HOLD=nHard,
           new_routine_ERA_RH_candidate=nNew,
           expected_routine_n=nRoutine,
           boundary_checks=len(rows),
           contiguous_water_boundaries_pass=len(valid),
           boundary_flags=len(flags),
           max_30min_VPD_jump_hPa=max((x[2] for x in rows if np.isfinite(x[2])),default=np.nan),
           max_30min_RH_jump_pp=max((x[3] for x in rows if np.isfinite(x[3])),default=np.nan),
           max_30min_QBOT_jump=max((x[4] for x in rows if np.isfinite(x[4])),default=np.nan),
           source_ERA_RH_not_independent_tower=True,
           scientific_approval=False),rows
    boundaries=[]
    for idx in ordered[1:]+[None]:
        if (idx is not None and idx==prev+1 and
            dt.iat[idx]-dt.iat[prev]==pd.Timedelta(minutes=30)):
            prev=idx;continue
        ep,ed=make_episode(start,prev)
        episode.append(ep)
        for la,lb,vjump,rjump,qjump,label in ed:
            boundaries.append(dict(episode_start_native_key=ep["start_native_key"],
              before_key=la,after_key=lb,
              jump_VPD_hPa=vjump,jump_RHwater_pp=rjump,
              jump_QBOT_kgkg=qjump,diagnostic=label,
              provenance_validated_by_QC0=False))
        if idx is not None:start=prev=idx
    events=pd.DataFrame(episode)
    edges=pd.DataFrame(boundaries)
    guard(len(events)==35 and events.original_missing_n.sum()==77 and
          events.protected_science_HOLD.sum()==9 and
          events.new_routine_ERA_RH_candidate.sum()==68,
          "35 original source episodes/77/68/9 accounting mismatch")
    trial_report=ledger.copy()
    trial_report["new_VPD_USE_hPa"]=trial_report.native_key.map(
       lambda k:float(trial.VPD_USE.iat[pos[k]]))
    trial_report["new_QBOT_kgkg"]=trial_report.native_key.map(
       lambda k:float(trial.QBOT.iat[pos[k]]))
    trial_report["new_science_status"]=trial_report.native_key.map(
       lambda k:"HOLD_ORIGINAL_SCIENCE" if k in hard else
       "ERA_RH_EXPLORATORY_RECONSTRUCTION_NOT_OBSERVED")
    summary={
      "version":VER,"site":"US-Kon",
      "Stage12AY_original_SHA256":sha(SOURCE/SOURCE_CSV),
      "Stage14J_original_science_QC_ledger_SHA256":sha(J/J_CSV),
      "model_halfhours":len(trial),
      "original_missing_VPD_QBOT":77,
      "routine_ERA_RH_inserted_research_only":68,
      "protected_original_science_missing":9,
      "new_numeric_missing":int(trial.VPD_USE.isna().sum()),
      "original_source_episodes":len(events),
      "new_68_physical_QBOT_closure_pass":inserted_all_closure,
      "selected_preexisting_or_new_numeric_thermodynamic_failures":original_physics_fail,
      "local_join_checks":len(edges),
      "local_join_flags_any_kind":int(edges.diagnostic.ne("PASS").sum()),
      "local_join_vpd_jump_gt4":int(edges.diagnostic.str.contains("VPD_JUMP_GT4",regex=False).sum()),
      "local_join_RH_jump_gt20pp":int(edges.diagnostic.str.contains("RH_JUMP_GT20PP",regex=False).sum()),
      "local_join_QBOT_jump_gt0p003":int(edges.diagnostic.str.contains("QBOT_JUMP_GT0.003",regex=False).sum()),
      "science_observational_independence_not_shown":True,
      "original_all_inputs_preserved":True,
      "postv5_DATM_AD400_Slurm_authorized":False}
    print("\nUS-Kon EXACT 77->9 SOURCE-HOLD SINGLE RESEARCH SENSITIVITY",flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    print("\nUS-Kon 35 SIGNED ORIGINAL EPISODES and ALL 30min EDGE WARNINGS",flush=True)
    print(events.to_string(index=False),flush=True)
    if edges.diagnostic.ne("PASS").any():
        print("\nUS-Kon EDGE SCIENCE WARNINGS (not automatic source repairs):")
        print(edges.loc[edges.diagnostic.ne("PASS")].to_string(index=False),flush=True)
    print("US-Kon ERA-RH 68 RESEARCH CANDIDATES ONLY; NINE PROTECTED UNKNOWN SOURCE REMAIN MISSING",flush=True)
    return trial,trial_report,events,edges,summary
def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    for n in ("self-test","check","run"):group.add_argument("--"+n,action="store_true")
    args=parser.parse_args()
    test()
    if args.self_test:return
    trial,ledger,events,edges,summary=analyze()
    if args.check:
        print("US-Kon RESEARCH 68 PREVIEW PASS | NO REPORT OR SOURCE WRITES",flush=True)
        return
    out=ROOT/"science_trials"/("US_Kon_68_ERA_RH_9HARD_HOLD_SCENARIO_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    products={
      "US-Kon_280320_ERA_RH68_9HOLD_RESEARCH_ONLY_NOT_DATM.csv":trial,
      "US-Kon_77_original_QC_ERA_RH_68_numeric_9HOLD.csv":ledger,
      "US-Kon_35_original_missing_episode_boundary_summary.csv":events,
      "US-Kon_77_native_source_boundary_comparisons.csv":edges}
    outputs={}
    for fn,df in products.items():
        df.to_csv(out/fn,index=False,float_format="%.17g")
        outputs[fn]=sha(out/fn)
    reread=pd.read_csv(file(out/"US-Kon_280320_ERA_RH68_9HOLD_RESEARCH_ONLY_NOT_DATM.csv"))
    guard(len(reread)==280320 and list(reread.columns)==FIELDS and
          reread.VPD_USE.isna().sum()==9 and
          reread.QBOT.isna().sum()==9,
          "serialized 280320 candidate lost original nine native HOLDs")
    note="NOT_APPROVED_DATM_AD400_OR_OVERWRITE"
    (out/note).write_text(
      "68 source-ERA-RH source-native low-confidence numerical candidates, NOT "
      "independently observed tower RH and not operator-approved forcing; "
      "9 scientifically protected source-event VPD/QBOT left intentionally NaN. "
      "Do not use incomplete file as production DATM. All prior source "
      "approved and research input files remain unchanged.\n")
    outputs[note]=sha(out/note)
    (out/"US_Kon_68_9_source_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    outputs["US_Kon_68_9_source_summary.json"]=sha(out/"US_Kon_68_9_source_summary.json")
    (out/"US_Kon_68_9_SHA_receipt.json").write_text(json.dumps(
      {"version":VER,"source_Stage12AY_SHA256":summary["Stage12AY_original_SHA256"],
       "source_Stage14J_SHA256":summary["Stage14J_original_science_QC_ledger_SHA256"],
       "output_SHA256":outputs,"DATM_ready":False,
       "postv5_authorized":False,"Slurm_submitted":False},indent=2)+"\n")
    print("US-Kon 68 LOW-CONFIDENCE RESEARCH OUTPUT:",out,flush=True)
    print("US-Kon 68/68 NUMERICALLY RECONSTRUCTED; EXACT 9 HARD SCIENCE HOLDS PRESERVED; NO SOURCE/DATM/SLURM WRITES",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("US-Kon 68 RESEARCH STOP:",e,file=sys.stderr,flush=True)
        raise

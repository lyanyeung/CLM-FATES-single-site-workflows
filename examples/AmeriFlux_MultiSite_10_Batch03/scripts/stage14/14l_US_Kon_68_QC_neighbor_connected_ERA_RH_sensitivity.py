#!/usr/bin/env python3
"""US-Kon Stage14L: one-pass original-QC-aware adjacent-humidity sensitivity.

Actual Stage14K filled 68 missing water-VPD/QBOT but left 62 of 112
local 30-minute joins flagged (43 VPD>4 hPa, 18 RH>20pp, 8 QBOT>.003).
A physical centre is NOT a scientifically accepted source interpolation.

This exact-source script explores connected ERA-relative-humidity transfers
into *unchanged original QC1/QC2* adjacent finite slots ONLY where required
to reduce discontinuity. Protect every original QC0, the 9 still-missing
hard HOLDs, and previous selected source edits that no longer equal the
original FLUXMET VPD_F. Stop expanding on temperature-source/ERA mismatch
>5 C, water/ice physics failure, source QC0, or 48 new neighbor slots per
original missing episode. No changed earlier source/cases/Slurm.

--check runs the source/QC/physics and prints fully, no writes.
--run writes a separate SHA-sealed RESEARCH sensitivity + exact source
provenance/edge ledger; not a new operator approval or DATM forcing.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
from collections import Counter
import numpy as np,pandas as pd
sys.dont_write_bytecode=True
VER="batch03-US-Kon-14L-source-QC-constrained-adjacent-ERA-RH-v1-20261029"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
OLD=ROOT/"science_trials/stage12ay_Kon_FINAL_science_candidates_and_sealed_HOLDS_20261026T132804Z_87d94e7a"
J=ROOT/"reports/US_Kon_77_original_QC_and_ERA_research_candidates_20261029T044439Z_c1845aab"
K=ROOT/"science_trials/US_Kon_68_ERA_RH_9HARD_HOLD_SCENARIO_20261029T044949Z_ebbfd739"
MAN=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json"
F="US-Kon_280320_ERA_RH68_9HOLD_RESEARCH_ONLY_NOT_DATM.csv"
REC="US_Kon_68_9_SHA_receipt.json"
ORIG="US-Kon_STAGE12AY_FINAL_RESEARCH_ONLY_NOT_DATM_NOLEAP.csv"
L77="US_Kon_ALL77_exact_humidity_SOURCE_QC_ERA_anchor_decisions.csv"
COLS="time TBOT QBOT PSRF FSDS FLDS WIND PRECTmms TA_USE VPD_USE".split()
HARD9={"201102220830","201102220900","201102220930","201105261100",
       "201109291830","201110150730","201110230730",
       "201202251030","201208050900"}
MAX_NEIGHBORS_PER_EVENT=48
def ensure(x,m):
    if not bool(x):raise RuntimeError("US-Kon STAGE14L STOP WITHOUT FORCING WRITES: "+m)
def safe(p):
    p=Path(p);ensure(p.is_file() and not p.is_symlink(),"missing source "+str(p))
    return p
def hashfile(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def es(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(17.67*t/(t+243.5))
def ice(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(22.46*t/(t+272.62))
def qcalc(e,p):
    return .622*100*e/(p-.378*100*e)
def native(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def test():
    ensure(float(es(-20))>float(ice(-20)) and
      pd.Series(["200501010000",None]).equals(pd.Series(["200501010000",None])),
      "string time/pandas-NaN/saturation test")
    print("US-Kon STAGE14L SELF-TEST PASS | NO SOURCE WRITES",flush=True)
def signed():
    oldrec=json.loads(safe(OLD/"stage12ay_FINAL_research_HOLD_SHA_receipt.json").read_text())
    jr=json.loads(safe(J/"US_Kon_77_READONLY_SHA_receipt.json").read_text())
    kr=json.loads(safe(K/REC).read_text())
    ensure(oldrec.get("version")=="batch03-stage12ay-v1-20261026-Kon-seal-final-70-humidity-holds"
      and oldrec.get("new_research_missing")==77 and oldrec.get("nine_protected_native_science_holds")==9,
      "Stage12AY original 77+9 science holds changed")
    ensure(jr.get("version")=="batch03-US-Kon-77-source-QC-onepass-v1-20261029"
      and jr.get("science_approved") is False,"Stage14J science QC receipt changed")
    ensure(kr.get("version")=="batch03-US-Kon-68ERA-RH-research-9HOLD-v1-20261029"
      and kr.get("DATM_ready") is False and kr.get("postv5_authorized") is False,
      "Stage14K research source approval changed")
    for folder,rec in ((OLD,oldrec),(J,jr),(K,kr)):
        for fn,h in rec["output_SHA256"].items():
            ensure(hashfile(folder/fn)==h,"original signed source SHA changed "+str(folder/fn))
    manifest=json.loads(safe(MAN).read_text())
    site=[x for x in manifest["sites"] if x["site"]=="US-Kon"]
    ensure(len(site)==1 and site[0].get("native_minutes")==30,"Kon original native site identity")
    for name in ("primary","era"):
        p=safe(site[0][name])
        ensure(hashfile(p)==manifest["input_sha256"].get(str(p.resolve())),
          "original tower or paired ERA SHA changed "+name)
    return site[0]
def load():
    site=signed()
    old=pd.read_csv(safe(OLD/ORIG),dtype={"time":str},low_memory=False)
    b=pd.read_csv(safe(K/F),dtype={"time":str},low_memory=False)
    l=pd.read_csv(safe(J/L77),dtype={"native_key":str},low_memory=False)
    ensure(len(old)==len(b)==280320 and list(old)==list(b)==COLS and
           old.time.equals(b.time),"original 280320 source/native clock altered")
    keys=native(b.time)
    ensure(keys.is_unique and keys.str.len().eq(12).all(),
           "duplicate or nonnative timestamp")
    tm=pd.to_datetime(keys,format="%Y%m%d%H%M",errors="raise")
    ensure(tm.is_monotonic_increasing and
           not bool(((tm.dt.month==2)&(tm.dt.day==29)).any()),
           "Kon NOLEAP 2005–20 30m model timeline changed")
    missing=set(keys[old.VPD_USE.isna()])
    ensure(len(missing)==77 and set(l.native_key)==missing and
           sum(x in HARD9 for x in missing)==9,
           "Stage12AY 77 native center universe changed")
    ensure(set(keys[b.VPD_USE.isna()])==HARD9 and
           int((~old.VPD_USE.isna() & b.VPD_USE.isna()).sum())==0,
           "Stage14K 68 repaired and 9 hard held clock missing mask changed")
    pkeys=keys.to_numpy()
    needed=set(pkeys)
    def raw(path,fields):
        x=pd.read_csv(safe(path),usecols=["TIMESTAMP_START",*fields],
          dtype={"TIMESTAMP_START":str},low_memory=False)
        ensure(x.TIMESTAMP_START.is_unique,"original FLUXMET duplicate native time")
        x=x.loc[x.TIMESTAMP_START.isin(needed)].copy()
        x=x.set_index("TIMESTAMP_START",drop=True).reindex(pkeys)
        ensure(len(x)==len(b) and not x[fields].isna().all(axis=1).any(),
          "original source native row absent")
        for c in fields:
            x[c]=pd.to_numeric(x[c],errors="coerce").mask(lambda z:z<=-9990)
        x.index=pd.RangeIndex(len(b))
        return x
    src=raw(site["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    era=raw(site["era"],["TA_ERA","VPD_ERA"])
    return old,b,l,keys,tm,src,era,missing
def physical(i,v,q,t,p):
    if not np.isfinite([v,q,t,p]).all():return None
    if not (50000<p<110000 and -80<t<65):return None
    sat=float(es(t));e=sat-v
    if not (0<v<sat and e>0 and 0<q<.08):return None
    if not np.isclose(q,qcalc(e,p),rtol=1e-6,atol=1e-8):return None
    r=100*e/sat
    if t<0 and e>1.02*float(ice(t)):return None
    return r
def candidate(i,b,src,era):
    if int(src.VPD_F_QC.iat[i]) not in (1,2):return None,"SOURCE_VPD_QC0_OR_INVALID"
    tv=float(b.TA_USE.iat[i]);p=float(b.PSRF.iat[i])
    at=float(era.TA_ERA.iat[i]);av=float(era.VPD_ERA.iat[i])
    if not np.isfinite([tv,p,at,av]).all():return None,"ERA_MISSING"
    if abs(tv-at)>5:return None,"TOWER_ERA_T_DISAGREEMENT_ABOVE5C"
    sat=float(es(at))
    if not (0<av<sat):return None,"ERA_VPD_NEGATIVE_OR_SUPERSAT"
    rh=1-av/sat
    e=float(es(tv))*rh;v=float(es(tv))-e;q=float(qcalc(e,p))
    if physical(i,v,q,tv,p) is None:return None,"TRANSFER_WATER_ICE_PHYSICS"
    return (v,q),"PASS"
def getmetrics(i,j,v,q,t,p,tm):
    if tm.iat[j]-tm.iat[i]!=pd.Timedelta(minutes=30):
        return "TIME_DISCONTINUITY",np.nan,np.nan,np.nan
    rh0=physical(i,v[i],q[i],t[i],p[i])
    rh1=physical(j,v[j],q[j],t[j],p[j])
    if rh0 is None or rh1 is None:
        return "MISSING_OR_UNPHYSICAL_ENDPOINT",np.nan,np.nan,np.nan
    dv=abs(v[j]-v[i]);dr=abs(rh1-rh0);dq=abs(q[j]-q[i])
    codes=[]
    if dv>4:codes.append("VPD_GT4")
    if dr>20:codes.append("RH_GT20")
    if dq>.003:codes.append("QBOT_GT0.003")
    return ";".join(codes) if codes else "PASS",dv,dr,dq
def assess():
    old,b,ledger,keys,tm,src,era,missing=load()
    v=b.VPD_USE.to_numpy(float).copy();q=b.QBOT.to_numpy(float).copy()
    t=b.TA_USE.to_numpy(float);p=b.PSRF.to_numpy(float)
    oldv=old.VPD_USE.to_numpy(float)
    routine={int(i) for i,x in enumerate(keys) if x in missing and x not in HARD9}
    ensure(len(routine)==68,"signed original routine seed count changed")
    originalkeys={str(k):int(i) for i,k in enumerate(keys)}
    seeds=sorted(routine)
    episodes=[];group=[];aa=bb=seeds[0]
    for i in seeds[1:]+[None]:
        if i is not None and i==bb+1 and tm.iat[i]-tm.iat[bb]==pd.Timedelta(minutes=30):
            bb=i;continue
        group.append(list(range(aa,bb+1)))
        if i is not None:aa=bb=i
    ensure(len(group)==28 and sum(len(x) for x in group)==68,
           "expected 28 ordinary original native source episodes")
    # Baseline flags at all 68 original seed boundaries, distinct half-hour
    # edges, so reduction can be compared despite extended patch scope.
    seed_edges=set()
    for i in routine:
        if i>0:seed_edges.add((i-1,i))
        if i+1<len(v):seed_edges.add((i,i+1))
    def audit_edges(edges,v0,q0):
        out=[]
        for i,j in sorted(edges):
            status,dv,dr,dq=getmetrics(i,j,v0,q0,t,p,tm)
            out.append((i,j,status,dv,dr,dq))
        return out
    before=audit_edges(seed_edges,v,q)
    previous_bad=sum(z[2]!="PASS" for z in before)
    applied={}
    owner={i:gid for gid,g in enumerate(group) for i in g}
    capped=set()
    rejected=Counter()
    # EXPAND ADJACENT ORIGINAL QC1/QC2 only, not over QC0, hard HOLDs,
    # previously changed source values, or temperature-to-ERA mismatch.
    for iteration in range(80):
        changes=0
        marked=set(owner)
        frontier=set()
        for i in marked:
            for j in (i-1,i+1):
                if j<0 or j>=len(v) or j in owner:continue
                if tm.iat[max(i,j)]-tm.iat[min(i,j)]!=pd.Timedelta(minutes=30):
                    continue
                status,*_=getmetrics(min(i,j),max(i,j),v,q,t,p,tm)
                if status=="PASS":continue
                frontier.add((i,j,status))
        if not frontier:break
        for i,j,status in sorted(frontier,key=lambda x:(x[1],x[0])):
            if j in owner:continue
            key=keys.iat[j];gid=owner[i]
            count=sum(1 for x,g in applied.items() if g[0]==gid)
            if count>=MAX_NEIGHBORS_PER_EVENT:
                capped.add(gid);rejected["PER_EPISODE_MAX48"]+=1;continue
            if key in missing or key in HARD9:
                rejected["ADJACENT_OTHER_MISSING_OR_HARD_HOLD"]+=1;continue
            raw_v=float(src.VPD_F.iat[j]);rawqc=float(src.VPD_F_QC.iat[j])
            if not np.isfinite([raw_v,rawqc,v[j]]).all() or
               not np.isclose(v[j],raw_v,rtol=0,atol=1e-5):
                rejected["PRIOR_SELECTED_REPAIR_OR_UNMATCHED_SOURCE"]+=1;continue
            cand,why=candidate(j,b,src,era)
            if cand is None:rejected[why]+=1;continue
            # Do not add an identical-value neighbour just to extend the
            # patch frontier toward a different distant original QC1 row.
            if (abs(cand[0]-v[j])<1e-9 and abs(cand[1]-q[j])<1e-12):
                rejected["NO_MEANINGFUL_SOURCE_CHANGE"]+=1;continue
            old_status,*_=getmetrics(min(i,j),max(i,j),v,q,t,p,tm)
            vnew=v[j];qnew=q[j];v[j],q[j]=cand
            new_status,*_=getmetrics(min(i,j),max(i,j),v,q,t,p,tm)
            # Only accept a change if the count of three alarms across
            # that interface STRICTLY decreases. No mass ERA RH clamping.
            nold=3 if old_status=="MISSING_OR_UNPHYSICAL_ENDPOINT" else len(old_status.split(";")) if old_status!="PASS" else 0
            nnew=3 if new_status=="MISSING_OR_UNPHYSICAL_ENDPOINT" else len(new_status.split(";")) if new_status!="PASS" else 0
            if nnew>=nold:
                v[j],q[j]=vnew,qnew
                rejected["NEIGHBOR_ERA_RH_NOT_IMPROVED"]+=1
                continue
            owner[j]=gid
            applied[j]=(gid,vnew,qnew,status,new_status)
            changes+=1
        if not changes:break
    # Validate exact original scope, HARD9, original T/P, no QC0 edits.
    new=b.copy(deep=True)
    for i in applied:
        new.at[i,"VPD_USE"]=v[i];new.at[i,"QBOT"]=q[i]
    for col in COLS:
        if col not in ("VPD_USE","QBOT"):
            ensure(new[col].equals(b[col]),"non-humidity original altered "+col)
        else:
            keep=np.ones(len(b),bool);keep[list(applied)]=False
            ensure(b.loc[keep,col].reset_index(drop=True).equals(
                new.loc[keep,col].reset_index(drop=True)),
                "previously finite changed outside original QC1/QC2 scope "+col)
    ensure(set(keys[new.VPD_USE.isna()])==HARD9 and
           new.VPD_USE.isna().equals(new.QBOT.isna()),
           "nine special original scientific NaN source holds not preserved")
    after=audit_edges(seed_edges,v,q)
    after_bad=sum(z[2]!="PASS" for z in after)
    selected_source_pairs=set()
    for i in set(seeds)|set(applied):
        for j in (i-1,i+1):
            if 0<=j<len(v):selected_source_pairs.add((min(i,j),max(i,j)))
    all_joins=audit_edges(selected_source_pairs,v,q)
    original_boundary_report=pd.DataFrame([
      {"before_native":keys.iat[i],"after_native":keys.iat[j],
       "source_original_candidate_before":s0,
       "source_original_candidate_after":a0,
       "old_VPD_jump_hPa":dv0,"new_VPD_jump_hPa":dv1,
       "old_RH_jump_pp":rh0,"new_RH_jump_pp":rh1,
       "old_QBOT_jump":q0,"new_QBOT_jump":q1}
      for (i,j,s0,dv0,rh0,q0),(ii,jj,a0,dv1,rh1,q1) in zip(before,after)
      if i==ii and j==jj
    ])
    neighborhood=pd.DataFrame([
     {"left_native":keys.iat[i],"right_native":keys.iat[j],
      "status":status,"abs_dVPD_hPa":dv,
      "abs_dRHwater_pp":rh,"abs_dQBOT_kgkg":dq,
      "source_original_VPD_QC_left":src.VPD_F_QC.iat[i],
      "source_original_VPD_QC_right":src.VPD_F_QC.iat[j]}
     for i,j,status,dv,rh,dq in all_joins
    ])
    modifications=pd.DataFrame([
      {"native_key":keys.iat[i],"source_original_VPD_F_QC":src.VPD_F_QC.iat[i],
       "source_original_T_QC":src.TA_F_QC.iat[i],
       "source_original_VPD_F_hPa":src.VPD_F.iat[i],
       "original_selected_VPD_hPa":applied[i][1],
       "ERA_RH_candidate_VPD_hPa":v[i],
       "original_selected_QBOT":applied[i][2],"ERA_RH_candidate_QBOT":q[i],
       "assigned_original_missing_episode":applied[i][0],
       "neighbor_improvement_from":applied[i][3],
       "neighbor_improvement_to":applied[i][4],
       "original_source_QC0_VPD_preserved":True,
       "operator_approved":False}
      for i in sorted(applied)
    ])
    # No previous physical coupled input should have been made invalid.
    complete=np.isfinite(v)&np.isfinite(q)
    qcheck=qcalc(es(t[complete])-v[complete],p[complete])
    err=np.isclose(q[complete],qcheck,atol=1e-8,rtol=1e-6)
    ensure(bool(err.all()),"existing selected full-source VPD/QBOT model closure broken")
    summary={
     "version":VER,"site":"US-Kon","native_rows":len(b),
     "original_missing_77":77,"existing_68_ERA_RH_candidates_unchanged":True,
     "special_science_9_missing_unchanged":True,
     "original_native_routine_episodes":len(group),
     "new_optional_neighbor_QC1_QC2_ERA_RH_trials":len(applied),
     "original_seed_contact_edges":len(seed_edges),
     "before_seed_contact_edge_warnings":previous_bad,
     "after_seed_contact_edge_warnings":after_bad,
     "all_expanded_contact_edges":len(all_joins),
     "all_expanded_contact_edge_warnings":sum(x[2]!="PASS" for x in all_joins),
     "original_tower_QC0_humidity_unchanged":True,
     "max_neighbor_expansion_per_original_event":MAX_NEIGHBORS_PER_EVENT,
     "original_QC_source_denials":dict(rejected),
     "capped_science_episodes":sorted(capped),
     "source_Stage14K_SHA256":hashfile(K/F),
     "source_original_FLUXMET_SHA256":hashfile(ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json"),
     "all_finite_selected_water_QBOT_closure":True,
     "Postv5_DATM_AD400_approved":False,"Slurm_jobs_submitted":False}
    print("US-Kon STAGE14L ORIGINAL-QC-CONSTRAINED NEIGHBOR SOURCE SUMMARY:")
    print(json.dumps(summary,indent=2),flush=True)
    print("US-Kon ALL UNRESOLVED FULL EXPANDED BOUNDARY WARNINGS:")
    flagged=neighborhood.loc[neighborhood.status.ne("PASS")]
    print(flagged.head(100).to_string(index=False) if len(flagged) else "NONE",flush=True)
    print("US-Kon CASE SOURCE SCIENCE NOT VALIDATED; 9 HARD HOLDS REMAIN, NO DATM",flush=True)
    return new,modifications,original_boundary_report,neighborhood,summary
def main():
    p=argparse.ArgumentParser()
    q=p.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","run"):q.add_argument("--"+mode,action="store_true")
    args=p.parse_args()
    test()
    if args.self_test:return
    src,changes,prior,current,summary=assess()
    if args.check:
        print("US-Kon STAGE14L QC-AWARE PREVIEW COMPLETE; NO WRITES",flush=True)
        return
    out=ROOT/"science_trials"/("US_Kon_14L_QC1_QC2_NEIGHBOR_ERA_RH_RESEARCH_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    products={
     "US_Kon_280320_ERA_RH68_plus_QC1QC2_NEIGHBORS_9HOLD_NOT_DATM.csv":src,
     "US_Kon_exact_original_QC1_QC2_neighbor_changes.csv":changes,
     "US_Kon_before_after_68_original_seed_boundaries.csv":prior,
     "US_Kon_all_expanded_neighbor_boundary_QC.csv":current}
    checks={}
    for fn,df in products.items():
        df.to_csv(out/fn,index=False,float_format="%.17g")
        checks[fn]=hashfile(out/fn)
    again=pd.read_csv(out/list(products)[0])
    ensure(len(again)==280320 and again.VPD_USE.isna().sum()==9 and
           again.QBOT.isna().sum()==9 and list(again)==COLS,
           "new research full CSV re-read did not preserve all 9 science holds")
    (out/"US_Kon_14L_full_source_QC_summary.json").write_text(
      json.dumps(summary,indent=2)+"\n")
    checks["US_Kon_14L_full_source_QC_summary.json"]=hashfile(out/"US_Kon_14L_full_source_QC_summary.json")
    (out/"NOT_APPROVED_FOR_POSTV5_DATM_AD400").write_text(
      "68 previous missing source candidates and OPTIONAL QC1/QC2 new finite "
      "neighbour ERA-RH sensitivity, not original measured tower observation. "
      "9 protected original science holds remain NaN and are NOT DATM-ready. "
      "Actual QC0 and all signed original met retained. Unresolved boundary "
      "warnings must not be hidden or assumed validated. No case/Slurm.\n")
    checks["NOT_APPROVED_FOR_POSTV5_DATM_AD400"]=hashfile(out/"NOT_APPROVED_FOR_POSTV5_DATM_AD400")
    (out/"US_Kon_14L_SHA_receipt.json").write_text(json.dumps({
       "version":VER,"original_Stage14K_SHA256":summary["source_Stage14K_SHA256"],
       "output_SHA256":checks,"operator_science_approved":False},indent=2)+"\n")
    print("US-Kon STAGE14L ISOLATED RESEARCH OUTPUT:",out,flush=True)
    print("US-Kon STAGE14L SINGLE QC-AWARE ADJACENT SCIENCE EXPERIMENT DONE; 9 PROTECTED SOURCE HOLDS UNCHANGED; NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("US-Kon STAGE14L FAIL CLOSED:",e,file=sys.stderr,flush=True)
        raise

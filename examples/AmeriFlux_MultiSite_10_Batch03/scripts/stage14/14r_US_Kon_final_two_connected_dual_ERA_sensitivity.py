#!/usr/bin/env python3
"""US-Kon 14R — exactly the last two humidity HOLDs; isolated research only.

MAY-26 2011 11:00: joint original QC1 warm-T correction using VERIFIED
2011 ERA5-Land T2m, ERA5-Land RH transferred to selected T at original
QC1-VPD records, and measured T-QC0 11:00 unchanged. Review originally
09:00–11:00, optionally extend backwards <=12 native QC1/2 VPD slots
only when the left external 30min join fails. Never cross VPD QC0.
SEP-29 2011 18:30: original QC2 VPD is derived from FLUXNET companion
ERA T. Transfer original companion ERA RH (NOT absolute ERA VPD) to
selected tower T in a bounded 17:00–20:00 continuous native QC2 episode;
propose original QC1 tower T corrections at 17:30 and 18:30 from
IMMEDIATE measured T QC0 neighbours. Verify with separate true downloaded
ERA5-Land RH; protect all original QC0 and source receipt hashes.

Both groups are atomic; candidate only accepted if all internal+external
30min T/VPD/RH/QBOT jumps & source thermodynamics pass. No clipped data,
automatic threshold relax, or source edits if group fails. Print all
before/after raw tower QC, selected, companion ERA, grid T/RH, proposals,
and failed edges. No DATM/Postv5/AD400/Slurm approval.
"""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-Kon-14R-last-two-dual-ERA-connected-source-research-v1-20261029"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
Q=ROOT/"science_trials/US_Kon_14Q_two_remaining_bounded_humidity_research_20261029T070830Z_ffcea3a8"
QFILE="US-Kon_14Q_280320_original_QC0_preserved_research_NOT_DATM.csv"
QREC="US-Kon_14Q_SHA_receipt.json"
M=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json"
READER=Path.home()/"US_Kon_nine_tower_ERA5Land_pm2h.py"
READER_BLOB="dabc868924ec46a5a2905ad3505a100fd1974e52"
COLS="time TBOT QBOT PSRF FSDS FLDS WIND PRECTmms TA_USE VPD_USE".split()
LAST={"201105261100","201109291830"}
MAY_CENTER="201105261100"
SEP_CENTER="201109291830"
BIF_UTC_OFFSET=-6
def guard(ok,why):
    if not bool(ok):raise RuntimeError("Kon Stage14R SOURCE STOP (NO FORCING WRITES): "+str(why))
def regular(p):
    p=Path(p);guard(p.is_file() and not p.is_symlink(),"missing immutable source "+str(p));return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def gitblob(p):
    b=regular(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def es(t):
    return float(6.112*np.exp(17.67*float(t)/(float(t)+243.5)))
def ice(t):
    return float(6.112*np.exp(22.46*float(t)/(float(t)+272.62)))
def q_from_e(e,p):
    return .622*100*e/(p-.378*100*e)
def physical(t,p,v,q):
    if not np.isfinite([t,p,v,q]).all():return None
    if not (-75<t<65 and 50000<p<110000 and 0<=v<es(t) and 0<q<.08):return None
    e=es(t)-v
    if e<=0 or not np.isclose(q,q_from_e(e,p),atol=1e-8,rtol=1e-6):return None
    if t<0 and 100*e/ice(t)>102:return None
    return 100*e/es(t)
def keys(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def test():
    guard(len(LAST)==2 and
          np.isclose(q_from_e(8,100000),.005,atol=.00002) and
          abs(es(20)-23.369471)<.01,
          "native two-case humidity regression")
    print("US-Kon 14R TWO FINAL SOURCE EVENTS SELF-TEST PASS",flush=True)
def read():
    qr=json.loads(regular(Q/QREC).read_text())
    guard(qr.get("version")=="batch03-Kon-14Q-two-bounded-remaining-low-confidence-research-v1-20261029" and
          qr.get("operator_science_approved") is False and qr.get("DATM_ready") is False and
          qr.get("output_SHA256",{}).get(QFILE)==sha(Q/QFILE),
          "actual Stage14Q signed two-HOLD source/approval differs")
    for n,h in qr["output_SHA256"].items():
        guard(sha(Q/n)==h,"actual Stage14Q original report hash differs "+n)
    mf=json.loads(regular(M).read_text())
    site=[x for x in mf["sites"] if x["site"]=="US-Kon"]
    guard(len(site)==1 and int(site[0]["first_year"])==2004 and
          int(site[0]["last_year"])==2019 and int(site[0]["native_minutes"])==30,
          "US-Kon original source metadata changed")
    src=site[0]
    for typ in ("primary","era"):
        f=regular(src[typ])
        guard(sha(f)==mf["input_sha256"].get(str(f.resolve())),
              "original tower/paired ERA raw source hash differs "+typ)
    a=pd.read_csv(regular(Q/QFILE),dtype={"time":str},low_memory=False)
    guard(len(a)==280320 and list(a)==COLS,"actual Q 280320 selected schema differs")
    kk=keys(a.time)
    ts=pd.to_datetime(kk,format="%Y%m%d%H%M",errors="raise")
    guard(kk.is_unique and ts.is_monotonic_increasing and
          kk.iat[0]=="200401010000" and kk.iat[-1]=="201912312330" and
          not bool(((ts.dt.month==2)&(ts.dt.day==29)).any()),
          "selected actual native clock changed")
    guard(set(kk[a.VPD_USE.isna()])==LAST and
          set(kk[a.QBOT.isna()])==LAST,"two original protected sources changed")
    needed=pd.date_range("2011-05-26 00:00","2011-05-26 12:30",freq="30min").strftime("%Y%m%d%H%M").tolist()
    needed+=pd.date_range("2011-09-29 15:30","2011-09-29 21:00",freq="30min").strftime("%Y%m%d%H%M").tolist()
    def frame(p,cs):
        r=pd.read_csv(regular(p),usecols=["TIMESTAMP_START",*cs],
                      dtype={"TIMESTAMP_START":str},low_memory=False)
        guard(r.TIMESTAMP_START.is_unique,"original source duplicate native key")
        r=r.set_index("TIMESTAMP_START").reindex(needed)
        guard(not r[cs].isna().all(axis=1).any(),"original source year/local record absent")
        for col in cs:
            r[col]=pd.to_numeric(r[col],errors="coerce").mask(lambda x:x<=-9990)
        return r
    raw=frame(src["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    era=frame(src["era"],["TA_ERA","VPD_ERA"])
    guard(gitblob(READER)==READER_BLOB,"verified Stage14O grid reader changed at HOME")
    module=importlib.util.spec_from_file_location("signed_kon_14o_reader",str(READER))
    obj=importlib.util.module_from_spec(module)
    module.loader.exec_module(obj)
    grid,status=obj.read_grid(2011)
    guard(grid is not None and "VERIFIED_" in status,"original ERA5-Land 2011 SHA file not verified")
    hours,ge=grid
    tt=pd.to_datetime(needed,format="%Y%m%d%H%M")
    utc=tt+pd.Timedelta(minutes=15)-pd.Timedelta(hours=BIF_UTC_OFFSET)
    guard(utc.min()>=hours[0] and utc.max()<=hours[-1],
          "ERA5-Land native midpoint→UTC clock outside signed hourly source")
    xp=hours.asi8.astype(float)/1e9
    x=utc.asi8.astype(float)/1e9
    gv=pd.DataFrame(index=needed)
    gv["ERA5_T_C"]=np.interp(x,xp,ge["t2m"])-273.15
    gv["ERA5_D_C"]=np.interp(x,xp,ge["d2m"])-273.15
    gv["ERA5_P_Pa"]=np.interp(x,xp,ge["sp"])
    gv["ERA5_RHwater_pct"]=[
        100*es(d)/es(t) for t,d in zip(gv.ERA5_T_C,gv.ERA5_D_C)]
    guard(np.isfinite(gv.to_numpy(float)).all() and
          (gv.ERA5_D_C<=gv.ERA5_T_C+.1).all() and
          gv.ERA5_RHwater_pct.between(0,100.05).all(),
          "original ERA5-Land spatial/physical evidence invalid")
    idx={z:i for i,z in enumerate(kk)}
    return a,kk,ts,idx,raw,era,gv,sha(src["primary"]),sha(src["era"]),status
def analyze():
    a,kk,ts,idx,raw,era,gv,towersha,erasha,gridstatus=read()
    out=a.copy(deep=True)
    changes_v=set();changes_t=set();groups=[];details=[];edges=[]
    def obs(k):return raw.loc[k]
    def rd(k):return era.loc[k]
    def grid(k):return gv.loc[k]
    def source_rh(k):
        z=rd(k)
        return 100*(1-float(z.VPD_ERA)/es(z.TA_ERA))
    def proposal(k,method):
        i=idx[k];z=obs(k);g=grid(k)
        tq=int(z.TA_F_QC);vq=int(z.VPD_F_QC)
        guard(tq in (0,1) and vq in (1,2),
              "method cannot edit original T/VPD QC0 or missing source flags "+k)
        prev_t=float(a.TA_USE.iat[i]);prev_v=float(a.VPD_USE.iat[i])
        if tq==0:
            guard(np.isclose(prev_t,float(z.TA_F),atol=1e-8,rtol=0),
                  "original measured tower T QC0 selected mismatch "+k)
            t=prev_t
        elif method=="MAY_ERA5_RH":
            guard(np.isclose(prev_t,float(z.TA_F),atol=1e-8,rtol=0),
                  "MAY original QC1 selected T has prior source modification "+k)
            t=float(g.ERA5_T_C)
        else:
            guard(vq==2 and
                  np.isclose(prev_t,float(z.TA_F),atol=1e-8,rtol=0),
                  "SEP historical T source changed or VPD not original QC2 "+k)
            before="201109291700" if k=="201109291730" else "201109291800" if k=="201109291830" else None
            after ="201109291800" if k=="201109291730" else "201109291900" if k=="201109291830" else None
            if before and after:
                guard(int(obs(before).TA_F_QC)==int(obs(after).TA_F_QC)==0,
                      "SEP original measured T QC0 30min anchors lost "+k)
                t=(float(obs(before).TA_F)+float(obs(after).TA_F))/2
            else:
                # 19:30 original T-QC1 requires original paired ERA5-Land
                # comparison; only preserve its original T if it is already
                # physically admissible at transferred companion ERA RH.
                t=prev_t
        if method=="MAY_ERA5_RH":
            rh=float(g.ERA5_RHwater_pct)
        else:
            rh=source_rh(k)
        other=source_rh(k) if method=="MAY_ERA5_RH" else float(g.ERA5_RHwater_pct)
        guard(np.isfinite([t,rh,other]).all() and
              0<rh<=100 and 0<other<=100 and abs(rh-other)<=15,
              "separately downloaded ERA5 RH / companion ERA RH disagreement >15pp at "+k)
        pressure=float(a.PSRF.iat[i])
        e=es(t)*rh/100
        v=es(t)-e
        q=q_from_e(e,pressure)
        guard(physical(t,pressure,v,q) is not None,
              "proposed source at site T/P not thermodynamically physical "+k)
        return (t,v,q,rh,other,tq,vq,prev_t,prev_v,
                float(z.TA_F),float(z.VPD_F),float(rd(k).TA_ERA),
                float(rd(k).VPD_ERA),float(g.ERA5_T_C))
    def check_group(name,scope,left,right,method):
        patches={}
        invalid=[]
        for k in scope:
            try:patches[idx[k]]=proposal(k,method)
            except Exception as ex:invalid.append(str(ex));break
        chain=[left,*scope,right]
        worst={"VPD_hPa":0.0,"RH_pp":0.0,"QBOT_kgkg":0.0,"T_C":0.0}
        if not invalid:
            for la,rb in zip(chain,chain[1:]):
                u,v=idx[la],idx[rb]
                if ts.iat[v]-ts.iat[u]!=pd.Timedelta(minutes=30):
                    invalid.append("SOURCE_TIMELINE_BROKEN "+la+" "+rb);continue
                def sample(i):
                    if i in patches:return patches[i][:4]
                    t=float(a.TA_USE.iat[i]);p=float(a.PSRF.iat[i])
                    v=float(a.VPD_USE.iat[i]);q=float(a.QBOT.iat[i])
                    return t,v,q,physical(t,p,v,q)
                t1,v1,q1,rh1=sample(u)
                t2,v2,q2,rh2=sample(v)
                if rh1 is None or rh2 is None:
                    invalid.append("ORIGINAL_EXTERNAL_OR_CANDIDATE_UNPHYSICAL "+la+" "+rb);continue
                d={"VPD_hPa":abs(v2-v1),"RH_pp":abs(rh2-rh1),
                   "QBOT_kgkg":abs(q2-q1),"T_C":abs(t2-t1)}
                for nm,val in d.items():worst[nm]=max(worst[nm],val)
                fail=(d["VPD_hPa"]>4 or d["RH_pp"]>20 or
                      d["QBOT_kgkg"]>.003 or d["T_C"]>4)
                edges.append(dict(group=name,left_native=la,right_native=rb,
                                  **d,warning=bool(fail)))
                if fail:invalid.append("HALFHOUR_BOUNDARY "+la+" "+rb+" "+json.dumps(d))
        return patches,invalid,worst
    # MAY: Original 09:00–11:00 QC1 warm-temperature source; bounded
    # search leftward up to 12 additional original QC1/QC2 VPD records,
    # stopping before ever crossing a published VPD QC0 or time gap.
    start=idx["201105260900"];end=idx[MAY_CENTER]
    may_start=start
    max_extra=12
    may_patches={};may_invalid=[];may_worst={}
    for iteration in range(max_extra+1):
        scope=kk.iloc[may_start:end+1].tolist()
        left=kk.iat[may_start-1];right=kk.iat[end+1]
        before_edges=len(edges)
        patches,invalid,worst=check_group("MAY26_ERA5_RH",
                                          scope,left,right,"MAY_ERA5_RH")
        # retain only last-iteration comparison edges
        edges[:]=edges[:before_edges]
        may_patches,may_invalid,may_worst=patches,invalid,worst
        if not invalid:break
        # Expansion only for a genuine previous left source-edge
        # anomaly; reject expansion for internal, right or QC0 issues.
        if not any("HALFHOUR_BOUNDARY "+left+" "+kk.iat[may_start] in z
                   for z in invalid):break
        old=may_start-1
        if old<=0 or int(obs(kk.iat[old]).VPD_F_QC) not in (1,2):
            may_invalid.append("MAY_LEFT_QC0_OR_SOURCE_BOUNDARY_PROTECTED");break
        may_start-=1
    may_scope=kk.iloc[may_start:end+1].tolist()
    may_left=kk.iat[may_start-1];may_right=kk.iat[end+1]
    may_patches,may_invalid,may_worst=check_group(
         "MAY26_ERA5_RH",may_scope,may_left,may_right,"MAY_ERA5_RH")
    # SEP: 17:00–20:00 original native source VPD QC2.
    sep_scope=pd.date_range("2011-09-29 17:00","2011-09-29 20:00",
                      freq="30min").strftime("%Y%m%d%H%M").tolist()
    sep_patches,sep_invalid,sep_worst=check_group(
         "SEP29_COMPANION_ERA_RH",sep_scope,"201109291630",
         "201109292030","SEP_COMPANION_RH")
    plans=[
        ("MAY26_ERA5_RH",may_scope,may_patches,may_invalid,may_worst),
        ("SEP29_COMPANION_ERA_RH",sep_scope,sep_patches,sep_invalid,sep_worst)]
    for name,scope,patches,invalid,worst in plans:
        accepted=not invalid and len(patches)==len(scope)
        if accepted:
            for i,vals in patches.items():
                t,v,q=vals[:3]
                out.at[i,"VPD_USE"]=v
                out.at[i,"QBOT"]=q
                changes_v.add(i)
                if abs(t-float(a.TA_USE.iat[i]))>1e-10:
                    guard(int(obs(kk.iat[i]).TA_F_QC)==1,
                          "cannot revise any real observed TA QC0 "+kk.iat[i])
                    out.at[i,"TA_USE"]=t;out.at[i,"TBOT"]=t+273.15
                    changes_t.add(i)
        groups.append(dict(group=name,scope_first=scope[0],scope_last=scope[-1],
            attempted_original_QC1_or_QC2_VPD_HH=len(scope),
            original_center=MAY_CENTER if name.startswith("MAY") else SEP_CENTER,
            original_center_research_FILLED=accepted,
            group_NUMERICAL_PASS=accepted,
            failure_reasons=";".join(invalid),
            **{"max_"+k:val for k,val in worst.items()}))
        for i,vals in sorted(patches.items()):
            t,v,q,rh,other,tq,vq,old_t,old_v,ot,ov,et,ev,gt=vals
            details.append(dict(group=name,native_key=kk.iat[i],
                source_T_QC=tq,source_VPD_QC=vq,
                source_original_T_C=ot,original_selected_T_C=old_t,
                proposed_selected_T_C=t,source_original_VPD_hPa=ov,
                original_selected_VPD_hPa=old_v,
                proposed_VPD_hPa=v,proposed_QBOT_kgkg=q,
                proposed_RHwater_pct=rh,
                alternative_ERA_RHwater_pct=other,
                source_companion_ERA_T_C=et,source_companion_ERA_VPD_hPa=ev,
                ERA5Land_T2m_C=gt,group_NUMERICAL_PASS=accepted,
                candidate_is_measured_tower_RH=False,
                production_DATM_AD400_approved=False))
        print("US-Kon Stage14R SOURCE GROUP",name,
              "PASS",accepted,"N",len(scope),"jumps",worst,
              "reasons",invalid,flush=True)
    # Do not change any original fields outside strictly accepted patches.
    for col in COLS:
        locs=(changes_v if col in ("VPD_USE","QBOT") else
              changes_t if col in ("TA_USE","TBOT") else set())
        mask=np.ones(len(a),bool)
        if locs:mask[list(locs)]=False
        guard(a.loc[mask,col].reset_index(drop=True).equals(
              out.loc[mask,col].reset_index(drop=True)),
              "out-of-scope original scientific input modified "+col)
    missing=set(kk[out.VPD_USE.isna()])
    guard(missing==set(kk[out.QBOT.isna()]) and missing<=LAST,
          "exact two pre-existing source science holds changed outside scope")
    status=dict(version=VER,site="US-Kon",
        source_Stage14Q_SHA256=sha(Q/QFILE),
        original_tower_SHA256=towersha,original_companion_ERA_SHA256=erasha,
        gridded_ERA5Land_2011_signed_evidence=gridstatus,
        total_selected_native_HH=len(a),
        original_two_science_HOLD=sorted(LAST),
        accepted_research_groups=sum(z["group_NUMERICAL_PASS"] for z in groups),
        remaining_HOLD_keys=sorted(missing),
        remaining_HOLD_count=len(missing),
        newly_filled_HOLD_count=2-len(missing),
        revised_extra_finite_VPD_QC1_QC2_HH=len(changes_v)-(2-len(missing)),
        revised_original_QC1_temperature_HH=len(changes_t),
        scientifically_observed_RH_at_missing_centers=False,
        original_QC0_temperature_and_VPD_untouched=True,
        no_DATM_Postv5_AD400_Slurm_approval=True)
    print("\nUS-Kon Stage14R TWO SOURCE SCIENCE GROUPS",flush=True)
    print(pd.DataFrame(groups).to_string(index=False),flush=True)
    print("\nUS-Kon Stage14R ALL PROPOSED ORIGINAL VPD/T SOURCE ROWS",flush=True)
    print(pd.DataFrame(details).round(5).to_string(index=False),flush=True)
    print("\nUS-Kon Stage14R UNCHANGED/NEW 30min EDGE DIAGNOSTICS",flush=True)
    print(pd.DataFrame(edges).round(5).to_string(index=False),flush=True)
    print("\nUS-Kon Stage14R FINAL INCOMPLETE/NUMERICAL SOURCE STATUS",
          json.dumps(status,indent=2),flush=True)
    return out,pd.DataFrame(groups),pd.DataFrame(details),pd.DataFrame(edges),status
def main():
    p=argparse.ArgumentParser()
    a=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):
        a.add_argument("--"+name,action="store_true")
    args=p.parse_args()
    test()
    if args.self_test:return
    out,groups,details,edges,status=analyze()
    if args.check:
        print("US-Kon Stage14R READONLY PREVIEW PASS | NO OUTPUT WRITES",flush=True)
        return
    folder=ROOT/"science_trials"/("US_Kon_14R_last_two_reanalysis_source_RESEARCH_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    tables={
      "US-Kon_280320_final_two_science_ERA5_research_NOT_DATM.csv":out,
      "US-Kon_14R_two_group_source_decisions.csv":groups,
      "US-Kon_14R_original_QC1_QC2_proposed_VPD_T_RH_values.csv":details,
      "US-Kon_14R_all_local_30min_boundary_diagnostics.csv":edges}
    hashes={}
    for n,data in tables.items():
        data.to_csv(folder/n,index=False,float_format="%.17g")
        hashes[n]=sha(folder/n)
    reread=pd.read_csv(folder/next(iter(tables)))
    guard(len(reread)==280320 and list(reread)==COLS and
          int(reread.VPD_USE.isna().sum())==status["remaining_HOLD_count"] and
          int(reread.QBOT.isna().sum())==status["remaining_HOLD_count"],
          "serialized research candidate lost original missing/clock")
    (folder/"US-Kon_14R_scientific_summary.json").write_text(json.dumps(status,indent=2)+"\n")
    hashes["US-Kon_14R_scientific_summary.json"]=sha(folder/"US-Kon_14R_scientific_summary.json")
    (folder/"NOT_APPROVED_FOR_DATM_OR_AD400").write_text(
       "Original QC0 and parent full input unchanged. Paired FLUXNET ERA "
       "and ERA5-Land humidity are reanalysis, not independently measured "
       "tower RH at source missing times. Group success is numerical "
       "continuity ONLY; entire source science still requires validation "
       "including old unrelated QC1/QC2 VPD jumps and PFT/forcing. "
       "No DATM, AD400, model cases or Slurm jobs.\n")
    hashes["NOT_APPROVED_FOR_DATM_OR_AD400"]=sha(folder/"NOT_APPROVED_FOR_DATM_OR_AD400")
    (folder/"US-Kon_14R_SHA_receipt.json").write_text(json.dumps({
        "version":VER,"source_Stage14Q_sha256":status["source_Stage14Q_SHA256"],
        "output_SHA256":hashes,"operator_approved":False,"DATM_ready":False,
        "Slurm_submitted":False},indent=2)+"\n")
    print("US-Kon Stage14R ISOLATED SCIENCE OUTPUT:",folder,flush=True)
    print("US-Kon Stage14R TWO ORIGINAL SCIENCE EPISODES TESTED; QC0 AND PREVIOUS INPUTS IMMUTABLE; NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("US-Kon Stage14R HALTED, NO SOURCE/CIME WRITES:",exc,file=sys.stderr,flush=True)
        raise

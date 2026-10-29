#!/usr/bin/env python3
"""US-MMS ONE-PASS MANUAL science triage: 16 hourly selected gaps vs 18 raw bad ERA episodes.

Reads exact original Stage07 SHA-pinned source, selected Stage12G source (SHA
receipt), signed 15 missing-ERA5-Land-years ledger, and original Stage10D
18-event source physics review. Prints each missing native hourly record and
its +/-2 real hours; writes optional new independent report only.
Never changes tower, reanalysis, shadows, PFT, DATM, or runs Slurm.
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from uuid import uuid4
from datetime import datetime,timezone
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-US-MMS-onepass-manual-16-v1-20261029"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S12=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
S10=ROOT/"reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
SITE="US-MMS"
SELECT="US-MMS_STAGE12G_INCOMPLETE_NOLEAP.csv"
HELD="2810_original_missing_year_source_review_after_stage12g.csv"
ORIG="all_1924_manual_review.csv"
STEP=pd.Timedelta(hours=1)
def need(test,why):
    if not bool(test):raise RuntimeError("US-MMS MANUAL AUDIT STOP: "+str(why))
def safe(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p))
    return p
def digest(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def js(p):return json.loads(safe(p).read_text())
def water(t):
    t=np.asarray(t,float)
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def ice(t):
    t=np.asarray(t,float)
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))
def val(x):
    try:
        f=float(x)
        return f if np.isfinite(f) and f > -9000 else np.nan
    except (TypeError,ValueError):return np.nan
def hum(t,p,v):
    t,p,v=map(val,(t,p,v))
    if not all(np.isfinite([t,p,v])):return dict(ok=False,e=np.nan,q=np.nan,rhw=np.nan,rhi=np.nan)
    ew=float(water(t));ei=float(ice(t))
    ea=ew-v
    qp=.622*(100*ea)/(p-.378*100*ea) if p-.378*100*ea>0 else np.nan
    ok=bool(50000<=p<=110000 and 0<=v<ew and 0<qp<.08)
    return dict(ok=ok,e=float(ea),q=float(qp),rhw=float(100*ea/ew),rhi=float(100*ea/ei))
def selftest():
    assert 25*365*24==219000
    a=hum(-8,95000,.5)
    assert a["ok"] and 0<a["e"]<5 and 0<a["q"]<.01
    assert not hum(-17,95000,2.5)["ok"]
    assert val(-9999)!=val(-9999) and STEP==pd.Timedelta(minutes=60)
    print("US-MMS 16HR MANUAL SELF-TEST PASS | exact HR, physical water/ice, NO FORCING WRITES",flush=True)
def load():
    for d in (ROOT,S07,S12,S10):need(d.is_dir() and not d.is_symlink(),"source dir "+str(d))
    need(safe(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"),"original scientific hold missing")
    need(safe(S12/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"),"selected scientific hold missing")
    r=js(S12/"stage12g_research_only_sha_receipt.json")
    need(r.get("version")=="batch03-stage12g-v1-20261025-sha-verified-new-year-gridRH" and
         r.get("Postv5_approved")==0 and r.get("DATM_ready")==0 and
         r.get("spinup_authorized")==0 and
         r.get("original_233_physics_holds_untouched") is True,
         "Stage12G signed no-approval source receipt")
    for name in (SELECT,HELD,"six_site_stage12g_science_status.csv"):
        need(r["output_sha256"].get(name)==digest(S12/name),
             "Stage12G source receipt SHA "+name)
    s=js(S07/"exact_input_manifest.json")
    info=[x for x in s["sites"] if x["site"]==SITE]
    need(len(info)==1 and int(info[0]["native_minutes"])==60
         and int(info[0]["first_year"])==1999
         and int(info[0]["last_year"])==2023,
         "Original US-MMS 1999-2023 native hourly exact manifest")
    rec=info[0];pins=s["input_sha256"]
    for fname in (rec["primary"],rec["era"]):
        f=safe(fname)
        need(pins.get(str(f.resolve()))==digest(f),
             "Original raw FLUXMET/ERA input SHA changed: "+str(f))
    d=js(S10/"read_only_provenance.json")
    need(d.get("events")==1924 and d.get("no_replacement_approved") is True
         and d["output_sha256"].get(ORIG)==digest(S10/ORIG),
         "Stage10D 1924 original event source/review receipt changed")
    selected=pd.read_csv(S12/SELECT,low_memory=False)
    need(list(selected.columns)==["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"],
         "Stage12G actual selected source field inventory changed")
    ts=pd.to_datetime(selected.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    need(len(ts)==219000 and ts.is_unique and
         (ts.diff().dropna().isin([STEP,pd.Timedelta(hours=25)]).all()),
         "selected NOLEAP 219000-hour timeline integrity")
    # 25h rollover is permitted only at skipped Feb29; no other missing hour.
    breaks=ts.diff().fillna(STEP)
    if (breaks!=STEP).any():
        br=ts[breaks!=STEP]
        need(len(br)==6 and all(t.month==3 and t.day==1 and t.hour==0
             and t.year%4==0 for t in br),
             "hourly NOLEAP Feb29-only jump")
    need(ts.dt.year.min()==1999 and ts.dt.year.max()==2023 and
         ts.dt.year.nunique()==25,
         "1999-2023 site native period")
    h=selected[["VPD_USE","QBOT"]].isna()
    need(int(h.VPD_USE.sum())==16 and int(h.QBOT.sum())==16 and
         h.VPD_USE.equals(h.QBOT) and
         int(selected.drop(columns=["time"]).isna().any(axis=1).sum())==16,
         "actual current missing inventory is not exactly 16 humidity-only hours")
    selected=selected.assign(dt=ts).set_index("dt",drop=False)
    held=pd.read_csv(S12/HELD,dtype={"site":str,"native_key":str},low_memory=False)
    prior=held[held.site.eq(SITE)].copy()
    need(len(prior)==15 and prior.native_key.nunique()==15 and
         prior.reason.eq("MISSING_VERIFIED_STAGE12F_SOURCE_YEAR").all(),
         "Stage12G 15 source-missing native hours not exact")
    keys=ts.loc[h.VPD_USE].dt.strftime("%Y%m%d%H%M")
    need(set(prior.native_key).issubset(set(keys)) and len(set(keys)-set(prior.native_key))==1,
         "15 source-missing versus 1 distinct original-protected science HOLD")
    source=pd.read_csv(rec["primary"],dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(rec["era"],dtype={"TIMESTAMP_START":str},low_memory=False)
    must1={"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"}
    must2={"TIMESTAMP_START","TA_ERA","VPD_ERA"}
    need(must1<=set(source) and must2<=set(era),
         "original tower/companion ERA columns not available")
    for frame,kind in ((source,"tower"),(era,"ERA")):
        ss=frame.TIMESTAMP_START
        dt=pd.to_datetime(ss,format="%Y%m%d%H%M",errors="raise")
        need(ss.is_unique and dt.is_monotonic_increasing and
             (dt.diff().dropna()==STEP).all(),
             "original "+kind+" exact hourly chronology invalid")
    target=set(keys)
    context=set()
    anomalies=pd.read_csv(S10/ORIG,dtype={"site":str,"source_csv_row":str},
                          low_memory=False)
    anomalies=anomalies[anomalies.site.eq(SITE)].copy()
    need(len(anomalies)==18 and anomalies.time.nunique()==18,
         "original US-MMS 18 selected Stage10 cold source anomalies changed")
    anomalies["key"]=pd.to_datetime(anomalies.time,errors="raise").dt.strftime("%Y%m%d%H%M")
    need(anomalies.key.nunique()==18,"18 source anomalies collapse under hourly keys")
    for key in target | set(anomalies.key):
        dt=pd.to_datetime(key,format="%Y%m%d%H%M")
        for offset in (-2,-1,0,1,2):context.add((dt+offset*STEP).strftime("%Y%m%d%H%M"))
    raw=source[source.TIMESTAMP_START.isin(context)].copy()
    exact=era[era.TIMESTAMP_START.isin(context)][list(must2)].copy()
    raw=raw.merge(exact,on="TIMESTAMP_START",how="left",validate="one_to_one")
    raw["dt"]=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M")
    raw=raw.set_index("dt",drop=False)
    need(set(target | set(anomalies.key))<=set(raw.TIMESTAMP_START),
         "original raw exact-native events unavailable")
    return selected,raw,keys,prior,anomalies,r
def report():
    selected,raw,keys,prior,anomalies,r=load()
    pending=set(prior.native_key)
    anomaly=set(anomalies.key)
    gaps=[]
    cts=[]
    for key in sorted(set(keys)):
        dt=pd.to_datetime(key,format="%Y%m%d%H%M")
        z=raw.loc[dt]
        t=val(selected.at[dt,"TA_USE"]);p=val(selected.at[dt,"PSRF"])
        sourcev=val(z.VPD_F);source_t=val(z.TA_F);erav=val(z.VPD_ERA);era_t=val(z.TA_ERA)
        qc=val(z.VPD_F_QC);tc=val(z.TA_F_QC)
        original_tower=hum(t,p,sourcev)
        paired=hum(era_t,p,erav)
        # Do not assume source ERA has a physically valid RH where VPD_ERA > eSat(TA_ERA).
        rh_era=paired["rhw"] if paired["ok"] else np.nan
        proposed=float(water(t))*(1-rh_era/100) if np.isfinite(rh_era) else np.nan
        mapped=hum(t,p,proposed)
        in_18=key in anomaly
        if in_18 and paired["ok"]:
            # Prior Stage10D/10I says original 18 have negative paired ERA e:
            raise RuntimeError("Stage10D original negative-vapour event unexpectedly positive at "+key)
        label="ORIGINAL_PHYSICS_HOLD" if key not in pending else "EXTERNAL_YEAR_SOURCE_MISSING"
        if in_18:
            disposition="MANUAL_HOLD_ORIGINAL_ERA_NEGATIVE_VAPOUR"
        elif qc==0 and tc==0 and original_tower["ok"]:
            disposition="REVIEW_TOWER_MEASURED_QC0_POTENTIAL_ONLY"
        elif paired["ok"] and mapped["ok"]:
            disposition="RESEARCH_ONLY_COMPANION_RH_PHYSICALLY_POSSIBLE"
        else:
            disposition="HOLD_NO_DEFENSIBLE_NATIVE_SOURCE"
        nearby={}
        for off in (-2,-1,1,2):
            ndt=dt+off*STEP
            near=selected.loc[ndt] if ndt in selected.index else None
            nraw=raw.loc[ndt] if ndt in raw.index else None
            nearby[f"{off:+d}h_selected_VPD_hPa"]=val(near.VPD_USE) if near is not None else np.nan
            nearby[f"{off:+d}h_original_VPD_QC"]=val(nraw.VPD_F_QC) if nraw is not None else np.nan
            cts.append({"target":str(dt),"hour_offset":off,"native_time":str(ndt),
               "selected_T_C":val(near.TA_USE) if near is not None else np.nan,
               "selected_VPD_hPa":val(near.VPD_USE) if near is not None else np.nan,
               "original_tower_T_C":val(nraw.TA_F) if nraw is not None else np.nan,
               "original_tower_T_QC":val(nraw.TA_F_QC) if nraw is not None else np.nan,
               "original_tower_VPD_hPa":val(nraw.VPD_F) if nraw is not None else np.nan,
               "original_tower_VPD_QC":val(nraw.VPD_F_QC) if nraw is not None else np.nan,
               "companion_ERA_T_C":val(nraw.TA_ERA) if nraw is not None else np.nan,
               "companion_ERA_VPD_hPa":val(nraw.VPD_ERA) if nraw is not None else np.nan})
        gaps.append({"native_key":key,"native_time":str(dt),"source_reason":label,
          "overlap_original_18_ERA_negative_events":in_18,
          "selected_TA_C":t,"selected_PSRF_Pa":p,
          "original_TA_F_C":source_t,"TA_F_QC":tc,
          "original_VPD_F_hPa":sourcev,"VPD_F_QC":qc,
          "original_tower_VPD_physically_valid":original_tower["ok"],
          "companion_TA_ERA_C":era_t,"companion_VPD_ERA_hPa":erav,
          "companion_ERA_water_e_hPa":paired["e"],
          "companion_ERA_RHwater_pct":paired["rhw"],
          "companion_ERA_RHice_pct":paired["rhi"],
          "paired_ERA_water_physical":paired["ok"],
          "companion_RH_at_towerT_PREVIEW_VPD_hPa":proposed,
          "companion_RH_at_towerT_PREVIEW_QBOT_kgkg":mapped["q"],
          "companion_RH_at_towerT_PREVIEW_water_physical":mapped["ok"],
          "companion_RH_at_towerT_PREVIEW_ice_RH_pct":mapped["rhi"],
          "preliminary_human_disposition":disposition,
          "actual_repair_approved":False,**nearby})
    gaps=pd.DataFrame(gaps)
    conflicts=[]
    for key in sorted(anomaly):
        dt=pd.to_datetime(key,format="%Y%m%d%H%M")
        v=raw.loc[dt]
        pt=val(v.TA_ERA);pv=val(v.VPD_ERA)
        paired=hum(pt,val(selected.at[dt,"PSRF"]) if dt in selected.index else np.nan,pv)
        conflicts.append({"native_key":key,"original_source_row":str(anomalies.loc[anomalies.key.eq(key),"source_csv_row"].iloc[0]),
          "native_time":str(dt),"TA_ERA_C":pt,"VPD_ERA_hPa":pv,
          "paired_ERA_implied_vapour_e_hPa":float(water(pt)-pv) if np.isfinite(pt+pv) else np.nan,
          "Stage12G_16_missing_overlap":bool(key in set(keys)),
          "historical_science_review_only":True,"approved_repair":False})
    conflicts=pd.DataFrame(conflicts)
    need(len(gaps)==16 and gaps.native_key.nunique()==16 and
         int(gaps.source_reason.eq("EXTERNAL_YEAR_SOURCE_MISSING").sum())==15 and
         int(gaps.source_reason.eq("ORIGINAL_PHYSICS_HOLD").sum())==1 and
         len(conflicts)==18 and conflicts.native_key.nunique()==18 and
         (conflicts.paired_ERA_implied_vapour_e_hPa<0).all() and
         gaps.actual_repair_approved.eq(False).all(),
         "science source classification failed closed")
    print("\nUS-MMS EXACT 16 ORIGINAL 60MIN HUMIDITY HOLDS — FULL MANUAL DECISION DATA",flush=True)
    show=["native_key","source_reason","overlap_original_18_ERA_negative_events",
          "selected_TA_C","original_TA_F_C","TA_F_QC","original_VPD_F_hPa","VPD_F_QC",
          "companion_TA_ERA_C","companion_VPD_ERA_hPa","companion_ERA_water_e_hPa",
          "companion_RH_at_towerT_PREVIEW_VPD_hPa","companion_RH_at_towerT_PREVIEW_QBOT_kgkg",
          "preliminary_human_disposition"]
    print(gaps[show].to_string(index=False),flush=True)
    print("\nUS-MMS HISTORICAL 18 SOURCE-ERA NEGATIVE-VAPOUR EVENTS / CURRENT-16 OVERLAP",flush=True)
    print(conflicts.to_string(index=False),flush=True)
    print("\nUS-MMS MANUAL DISPOSITION COUNTS",flush=True)
    print(gaps.preliminary_human_disposition.value_counts().to_string(),flush=True)
    print("US-MMS SOURCE RECONCILIATION:",
          "selected_missing=16 source_year_missing=15 protected_original_physics=1",
          "historical_original_ERA_negative_e=18",
          "overlap="+str(int(gaps.overlap_original_18_ERA_negative_events.sum())),
          "original_and_selected_unchanged=True",
          "scientific_model_approval=False DATM=False AD400=False Slurm=False",flush=True)
    return gaps,pd.DataFrame(cts),conflicts
def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","run"):group.add_argument("--"+k,action="store_true")
    args=ap.parse_args()
    selftest()
    if args.self_test:return
    gaps,contexts,conflicts=report()
    if args.check:
        print("US-MMS MANUAL ONEPASS CHECK PASS | 16 hourly holds, 18 historical source events, NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("us_mms_16hour_onepass_manual_science_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={"US_MMS_16_missing_hour_manual_science_decisions.csv":gaps,
          "US_MMS_16_hour_neighbours_plusminus2h_original_ERA.csv":contexts,
          "US_MMS_18_historical_negative_ERA_e_overlap.csv":conflicts}
    outputs={}
    for name,df in docs.items():
        df.to_csv(out/name,index=False,float_format="%.17g")
        outputs[name]=digest(out/name)
    note={"version":VER,"site":"US-MMS","selected_60min_missing":16,
          "missing_external_verified_year_records":15,"original_physics_hold":1,
          "historical_source_ERA_negative_vapour":18,
          "overlap_current_16_historical_18":int(gaps.overlap_original_18_ERA_negative_events.sum()),
          "candidate_only_not_independent_tower_truth":True,
          "scientific_method_or_repair_approved":False,
          "original_source_or_shadow_or_forcing_written":False,
          "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    summary="US_MMS_onepass_16hour_manual_evidence_summary.json"
    (out/summary).write_text(json.dumps(note,indent=2)+"\n")
    outputs[summary]=digest(out/summary)
    (out/"US_MMS_NO_AUTOMATIC_REPAIR_OR_MODEL_ADMISSION").write_text(
       "Human science decision support only. 16 source gaps remain unfilled. ERA5/ERA5-Land are not measured tower truth.\n")
    outputs["US_MMS_NO_AUTOMATIC_REPAIR_OR_MODEL_ADMISSION"]=digest(out/"US_MMS_NO_AUTOMATIC_REPAIR_OR_MODEL_ADMISSION")
    (out/"US_MMS_readonly_source_science_SHA_receipt.json").write_text(
       json.dumps({"version":VER,"site":SITE,"outputs_SHA256":outputs,
                   "no_source_or_forcing_writes":True,
                   "no_repair_approvals":True},indent=2)+"\n")
    print("US-MMS MANUAL ONEPASS REPORT DIR:",out,flush=True)
    print("US-MMS 16-HOUR MANUAL ONEPASS SUCCESS | ALL 16/18 REVIEWED, NO ORIGINAL/FORCING/SLURM WRITES",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("US-MMS MANUAL ONEPASS STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage13AL: do actual QC0 support both held -17C AND -9.53C donor T bias?

SHA-check actual Stage13AK 2010–2025 QC0 report, original sources and
current Stage13AI shadow. Compare same winter original measured QC0 tower
VPD/T under joint site-temperature and tower-minus-ERA-temperature matches.
Also test raw ERA water-RH donor and empirical-bias adjustment with
leave-one-year-out, measured-QC0-only, with explicit 0-support safeguards.
SCIENTIFIC AUDIT ONLY: no source/forcing/shadow changes, no acceptance.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13al-v1-20261028-Me6-joint-cold-ERA-deltaT-QC0-LOYO"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
AK_CODE=HERE/"13ak_Me6_19HH_multi_year_QC0_winter_temperature_donor_READONLY.py"
AK_BLOB="5e82bd31484a3949a43829264f3ceb4d6c0f7832"
AK=ROOT/"reports/stage13ak_Me6_19HH_16year_QC0_ERA_temp_donor_READONLY_20261028T195450Z_758c2c85"
AK_REC="stage13ak_READONLY_science_SHA_receipt.json"
AK_SUM="stage13ak_19HH_16year_original_QC0_winter_science_summary.json"
AK_FILES={
 "19_source_tower_ERA_T_deltas_no_orography_claim.csv",
 "yearly_full_original_measured_QC0_and_winter_T_context.csv",
 "stratified_16year_measured_QC0_ERA_water_RH_transfer_skill.csv",
 AK_SUM,"NO_NEW_ERA_REPAIR_APPROVAL_OR_DATM_SOURCE_CHANGE"}
AK_VER="batch03-stage13ak-v2-20261028-Me6-19HH-16year-original-QC0-temperature-donor-syntax"
AI_SHA="b193388d4f82b47a7727c6ef9b2fdc25b37a56e4867d319224d1fc9327326f40"
START=pd.Timestamp("2014-12-31 23:30")
END=pd.Timestamp("2015-01-01 08:30")
H=pd.Timedelta(minutes=30)
EVENT=pd.date_range(START,END,freq="30min")
def need(ok,msg):
    if not bool(ok): raise RuntimeError("STAGE13AL SCIENCE SOURCE HOLD: "+str(msg))
def must(path):
    p=Path(path)
    need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p))
    return p
def sha(path):
    h=hashlib.sha256()
    with must(path).open("rb") as fp:
        for chunk in iter(lambda:fp.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def gitblob(path):
    b=must(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def es(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def metric(err):
    e=np.asarray(err,float)
    e=e[np.isfinite(e)]
    if not len(e):return {"n":0,"bias_hPa":None,"MAE_hPa":None,"p90_abs_hPa":None,
                          "fraction_abs_GT0p5":None}
    return {"n":len(e),"bias_hPa":float(e.mean()),
        "MAE_hPa":float(np.mean(abs(e))),
        "p90_abs_hPa":float(np.percentile(abs(e),90)),
        "fraction_abs_GT0p5":float(np.mean(abs(e)>.5))}
def loyo(years,err):
    """One year wholly excluded from its empirical source bias training."""
    yrs=np.asarray(years,int)
    e=np.asarray(err,float)
    out=np.full(len(e),np.nan)
    tests=0
    for yr in sorted(set(yrs.tolist())):
        held=yrs==yr
        train=~held
        # Require independent date/year support from OTHER YEARS.
        if not held.any() or train.sum()<96 or len(set(yrs[train]))<3:continue
        adjustment=np.median(e[train])
        out[held]=e[held]-adjustment
        tests+=1
    return out,tests
def selftest():
    need(len(EVENT)==19 and len(set(EVENT))==19,"19 exact native timestamps")
    orig=metric([1.,2.,3.])
    cv,n=loyo(np.array([2010]*50+[2011]*50+[2012]*50+[2013]*50),
              np.ones(200)*.7)
    need(orig["n"]==3 and n==4 and np.allclose(cv,0,atol=1e-12),
         "no-in-sample bias use; leave full year out cross-test")
    empty,n0=loyo(np.array([2010,2011]),np.array([.5,.5]))
    need(n0==0 and np.isnan(empty).all() and metric([])["MAE_hPa"] is None,
         "tiny source QC0 support cannot become validation")
    print("STAGE13AL SELF-TEST PASS | 19 HH joint source matching and independent leave-year-out bias tests, NO WRITES",flush=True)
def audit():
    need(gitblob(AK_CODE)==AK_BLOB,"actual source Stage13AK script blob changed")
    spec=importlib.util.spec_from_file_location("stage13ak_for_stage13al",must(AK_CODE))
    need(spec is not None and spec.loader is not None,"Stage13AK source import unavailable")
    ak=importlib.util.module_from_spec(spec);spec.loader.exec_module(ak)
    need(ak.VER==AK_VER,"Stage13AK actual science version changed")
    r=json.loads(must(AK/AK_REC).read_text())
    need(r.get("site")=="US-Me6" and r.get("version")==AK_VER
         and r.get("new_science_approval") is False
         and r.get("source_or_forcing_written") is False
         and set(r.get("outputs_SHA256",{}))==AK_FILES,
         "actual AK complete QC0 report SHA receipt mismatch")
    for nm,d in r["outputs_SHA256"].items():
        need("/" not in nm and "\\" not in nm and sha(AK/nm)==d,
             "Stage13AK original QC0 report SHA mismatch "+nm)
    summ=json.loads(must(AK/AK_SUM).read_text())
    need(summ.get("site")=="US-Me6" and
         summ.get("nineteen_native_19HH_with_site_ERA_T_gt8C")==19 and
         summ.get("nineteen_original_ERA_equal_source_QC2_VPD")==19 and
         summ.get("latest_Stage13AI_research_shadow_SHA256")==AI_SHA and
         summ.get("model_or_science_approved") is False and
         summ.get("original_tower_measured_QC0_eligible_16_years_HH")==247416,
         "actual Stage13AK 16y source facts changed")
    aj,raw,site,_=ak.audit()
    need(len(raw)==len(site)==280320 and raw.index.equals(site.index),
         "full original 16-year native data changed")
    need(raw.index.year.min()==2010 and raw.index.year.max()==2025,
         "actual original source data years no longer 2010–2025")
    need(site.VPD_USE.isna().sum()==45 and site.loc[EVENT,"VPD_USE"].isna().all(),
         "latest original Stage13AI 45 missing HH or held event changed")
    return raw,site,summ,r
def analyze():
    raw,site,prev,receipt=audit()
    x=raw.loc[EVENT]
    event_T=x.TA_F.to_numpy(float)
    event_dT=(x.TA_F-x.TA_ERA).to_numpy(float)
    need(np.all(np.isfinite([*event_T,*event_dT])) and
         np.all(np.abs(event_dT)>8) and x.VPD_F_QC.eq(2).all(),
         "actual event original tower-vs-ERA mismatch/QC changed")
    target_T=float(np.median(event_T))
    target_delta=float(np.median(event_dT))
    t=raw.TA_F.to_numpy(float)
    vt=raw.VPD_F.to_numpy(float)
    te=raw.TA_ERA.to_numpy(float)
    ve=raw.VPD_ERA.to_numpy(float)
    st=site.TA_USE.to_numpy(float)
    sv=site.VPD_USE.to_numpy(float)
    p=site.PSRF.to_numpy(float)
    esT=es(t); esERA=es(te)
    era_fraction=np.divide(ve,esERA,
                          out=np.full(len(ve),np.nan),
                          where=np.isfinite(ve)&np.isfinite(esERA)&(esERA>0))
    trial=esT*era_fraction
    with np.errstate(divide="ignore",invalid="ignore"):
        evap=100*(esT-trial)
        q=.622*evap/(p-.378*evap)
    valid=(raw.TA_F_QC.to_numpy(float)==0)&
          (raw.VPD_F_QC.to_numpy(float)==0)
    valid=(valid&np.isfinite([t,vt,te,ve,st,sv,p,q]).all(axis=0)&
           np.isclose(t,st,rtol=0,atol=1e-7)&
           np.isclose(vt,sv,rtol=0,atol=1e-7)&
           (vt>0)&(vt<esT)&(era_fraction>0)&(era_fraction<1)&
           (trial>0)&(trial<esT)&(q>0)&(q<.08)&(p>50000)&(p<110000))
    # The 19 event HH and surrounding two days never enter QC0 validation.
    dates=raw.index.normalize()
    winter=raw.index.month.isin([12,1,2])
    embargo=(raw.index>=pd.Timestamp("2014-12-30"))&(
             raw.index<pd.Timestamp("2015-01-03"))
    valid=valid&winter&(~embargo)
    yr=np.asarray(raw.index.year)
    err=trial-vt
    delta=t-te
    rows=[]
    donor_idx=[]
    for temp_tol in (3.,5.):
        for delta_tol in (1.,2.,3.,5.):
            mask=valid&(abs(t-target_T)<=temp_tol)&(
                       abs(delta-target_delta)<=delta_tol)
            counts=int(mask.sum())
            m=metric(err[mask])
            residual,heldyears=loyo(yr[mask],err[mask])
            c=metric(residual)
            days=int(dates[mask].nunique())
            years=int(np.unique(yr[mask]).size)
            assessable=counts>=96 and days>=5 and years>=3
            rows.append({
                "season":"Dec-Jan-Feb","tower_temperature_match_plusminus_C":temp_tol,
                "tower_minus_ERA_temperature_match_plusminus_C":delta_tol,
                "target_event_tower_median_C":target_T,
                "target_event_tower_minus_ERA_median_C":target_delta,
                "real_QC0_source_rows":counts,
                "real_QC0_unique_days":days,
                "real_QC0_years":years,
                "raw_ERA_RH_transfer_bias_hPa":m["bias_hPa"],
                "raw_ERA_RH_transfer_MAE_hPa":m["MAE_hPa"],
                "raw_ERA_RH_transfer_p90_abs_hPa":m["p90_abs_hPa"],
                "raw_ERA_RH_transfer_fraction_abs_GT0p5":m["fraction_abs_GT0p5"],
                "bias_adjustment_LOYO_test_HH":c["n"],
                "bias_adjustment_LOYO_test_years":heldyears,
                "bias_adjustment_LOYO_MAE_hPa":c["MAE_hPa"],
                "bias_adjustment_LOYO_p90_abs_hPa":c["p90_abs_hPa"],
                "joint_original_QC0_support_adequate_for_method_assessment":assessable,
                "may_use_for_missing_humidity_or_model":False})
            # Preserve all actual QC0 provenance for conditional samples.
            for j in np.where(mask)[0]:
                donor_idx.append({
                  "bin_siteT_tolerance_C":temp_tol,
                  "bin_site_minus_ERA_T_tolerance_C":delta_tol,
                  "native_original_time":str(raw.index[j]),
                  "tower_original_TA_F_C":float(t[j]),
                  "source_tower_T_QC":0,
                  "tower_original_VPD_F_hPa":float(vt[j]),
                  "source_tower_VPD_QC":0,
                  "companion_ERA_TA_C":float(te[j]),
                  "companion_ERA_VPD_hPa":float(ve[j]),
                  "tower_minus_ERA_T_C":float(delta[j]),
                  "raw_ERA_RH_transferred_site_VPD_hPa":float(trial[j]),
                  "donor_minus_original_measured_VPD_error_hPa":float(err[j]),
                  "original_source_and_model_unchanged":True})
    bands=pd.DataFrame(rows)
    donor=pd.DataFrame(donor_idx)
    need(len(bands)==8 and bands.may_use_for_missing_humidity_or_model.eq(False).all(),
         "all eight original QC0 conditional bins required, no approval")
    metrics={
      "version":VER,"site":"US-Me6",
      "actual_model_original_years":"2010–2025",
      "event_native_start":str(START),"event_native_end":str(END),
      "19_HH_event_held":19,
      "event_tower_T_median_C":target_T,
      "event_tower_minus_source_ERA_T_median_C":target_delta,
      "actual_16year_measured_QC0_original_rows":247416,
      "actual_parent_AK_receipt_SHA256":sha(AK/AK_REC),
      "true_site_and_ERA_joint_QC0_support_group_count":int(bands.joint_original_QC0_support_adequate_for_method_assessment.sum()),
      "study_has_not_established_safe_repair":True,
      "leave_one_year_out_bias_adjustment_exploratory_only":True,
      "original_VPD_QC0_is_measured_not_QC1_gapfilled":True,
      "independent_grid_elevation_or_ERA5_land_not_verified":True,
      "current_research_shadow_VPD_QBOT_missing_HH":45,
      "new_method_approval":False,"new_source_or_shadow_written":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AL ACTUAL 2010-2025 JOINT TOWER-T AND ERA-TDIFF MEASURED QC0 SUPPORT",flush=True)
    print(bands.to_string(index=False),flush=True)
    print("STAGE13AL EVENT-SPECIFIC SOURCE SUPPORT AND APPROVAL",
          json.dumps(metrics,indent=2),flush=True)
    return bands,donor,metrics
def main():
    p=argparse.ArgumentParser()
    opts=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):opts.add_argument("--"+opt,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    bands,donor,info=analyze()
    if args.check:
        print("STAGE13AL ORIGINAL SOURCE JOINT QC0 SUPPORT READONLY CHECK PASS; NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13al_Me6_19HH_2010_2025_joint_QC0_TandTdiff_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={
        "8_conditioned_actual_measured_QC0_ERA_RH_skill_LOYO.csv":bands,
        "actual_source_QC0_joint_matched_native_ERA_donor_records.csv":donor}
    for name,tab in docs.items():tab.to_csv(out/name,index=False,float_format="%.17g")
    name="stage13al_science_joint_temperature_donor_support_summary.json"
    flag="NO_HUMIDITY_REPAIR_OR_DONOR_SCIENCE_APPROVAL"
    (out/name).write_text(json.dumps(info,indent=2)+"\n")
    (out/flag).write_text("Temperature-plus-donor-bias joint QC0 support only; "
        "no source repair, candidate forcing or model use approved.\n")
    rec={"version":VER,"site":"US-Me6","new_method_approved":False,
        "source_or_forcing_written":False,
        "output_SHA256":{k:sha(out/k) for k in [*docs,name,flag]}}
    (out/"stage13al_READONLY_science_SHA_receipt.json").write_text(
         json.dumps(rec,indent=2)+"\n")
    print("STAGE13AL READONLY SCIENCE REPORT DIR:",out,flush=True)
    print("STAGE13AL 19HH TRUE QC0 JOINT SOURCE TEMPERATURE DONOR REVIEW COMPLETE; NO REPAIR/DATM/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AL SOURCE SCIENCE HOLD:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

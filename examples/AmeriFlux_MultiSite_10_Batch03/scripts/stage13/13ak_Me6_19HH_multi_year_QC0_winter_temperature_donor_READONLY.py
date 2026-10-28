#!/usr/bin/env python3
"""Stage13AK US-Me6 19-HH winter ERA donor validity; no repairs.

Use the *actual* source SHA-verified Stage13AJ and Stage13AI shadow. Study
original source VPD_F_QC=0 and TA_F_QC=0 measured halfhours over the
complete 2009-2024 site timeline, and donor same-release ERA temperature
bias around the -17C held event vs other winter years. Compare the raw
ERA-RH→tower-T hypothesis to true QC0 observations stratified by
temperature matching, season, and years. Zero eligible rows == NO SKILL.
No ERA5-Land independent data, elevation, or model acceptance is asserted.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ak-v2-20261028-Me6-19HH-16year-original-QC0-temperature-donor-syntax"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
AJ_CODE=HERE/"13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py"
AJ_CODE_GIT="62fb8b5225157f989d58c7a31d6a0a61237d4646"
AJ=ROOT/"reports/stage13aj_Me6_2015_crossyear_19HH_ERA_water_ice_QC0_READONLY_20261028T194649Z_103ef877"
AJ_REC="stage13aj_READONLY_science_SHA_receipt.json"
AJ_SUM="stage13aj_original_19HH_science_coverage_and_QC0_summary.json"
AJ_EXPECT={
 "19_original_native_tower_ERA_water_ice_candidate_NOT_APPROVED.csv",
 "19HH_2h_before_after_source_tower_ERA_NO_REPAIR.csv",
 "nearby_original_QC0_independent_ERA_RH_transfer_analogues.csv",
 AJ_SUM,"NO_19HH_ERA_REPAIR_OR_SCIENCE_APPROVAL"}
AJ_VER="batch03-stage13aj-v1-20261028-Me6-19HH-2015-cold-water-ice-QC0"
AI_SHA="b193388d4f82b47a7727c6ef9b2fdc25b37a56e4867d319224d1fc9327326f40"
START=pd.Timestamp("2014-12-31 23:30:00")
END=pd.Timestamp("2015-01-01 08:30:00")
EVENT=pd.date_range(START,END,freq="30min")
def need(ok,message):
    if not bool(ok):raise RuntimeError("STAGE13AK ORIGINAL SOURCE/SCIENCE HOLD: "+str(message))
def must(path):
    p=Path(path)
    need(p.is_file() and not p.is_symlink(),"file missing/symlink "+str(p))
    return p
def sha(path):
    h=hashlib.sha256()
    with must(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def gitblob(path):
    b=must(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def stats(values):
    x=np.asarray(values,dtype=float)
    x=x[np.isfinite(x)]
    if not len(x):return {"n":0,"median":None,"mean":None,"p10":None,"p90":None}
    return {"n":len(x),"median":float(np.median(x)), "mean":float(np.mean(x)),
      "p10":float(np.percentile(x,10)),"p90":float(np.percentile(x,90))}
def scores(values,actual):
    error=np.asarray(values,float)-np.asarray(actual,float)
    error=error[np.isfinite(error)]
    if not len(error):
        return {"n_source_QC0":0,"bias_hPa":None,"MAE_hPa":None,
            "P90_abs_error_hPa":None,"fraction_abs_error_gt_0p5hPa":None,
            "fraction_abs_error_gt_1hPa":None}
    return {"n_source_QC0":len(error),"bias_hPa":float(np.mean(error)),
        "MAE_hPa":float(np.mean(np.abs(error))),
        "P90_abs_error_hPa":float(np.percentile(np.abs(error),90)),
        "fraction_abs_error_gt_0p5hPa":float(np.mean(abs(error)>.5)),
        "fraction_abs_error_gt_1hPa":float(np.mean(abs(error)>1))}
def selftest():
    need(len(EVENT)==19 and np.array_equal([START,END],[EVENT[0],EVENT[-1]]),
         "actual winter original 19 HH scope changed")
    need(scores([1,2],[1,3])["MAE_hPa"]==.5 and
         scores([],[])["MAE_hPa"] is None,
         "reference QC0 evaluation must not invent samples")
    print("STAGE13AK SELF-TEST PASS | 19 source winter records, 16y real QC0 temperature-match/ERA donor research only; NO WRITES",flush=True)
def audit():
    need(gitblob(AJ_CODE)==AJ_CODE_GIT,
         "independent original Stage13AJ source code SHA drift")
    spec=importlib.util.spec_from_file_location("me6_stage13aj_for_13ak",must(AJ_CODE))
    need(spec is not None and spec.loader is not None,
         "original Stage13AJ source audit module unavailable")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    need(mod.VER==AJ_VER,"actual Stage13AJ original source science version drift")
    r=json.loads(must(AJ/AJ_REC).read_text())
    need(r.get("site")=="US-Me6" and r.get("version")==AJ_VER
         and r.get("source_or_forcing_written") is False and
         r.get("model_approval") is False and
         set(r.get("outputs_SHA256",{}))==AJ_EXPECT,
         "actual Stage13AJ 19HH research receipt changed")
    for n,d in r["outputs_SHA256"].items():
        need("/" not in n and "\\" not in n and sha(AJ/n)==d,
             "19HH scientific source SHA mismatch "+n)
    summ=json.loads(must(AJ/AJ_SUM).read_text())
    need(summ.get("site")=="US-Me6" and
         summ.get("original_native_HH")==19 and
         summ.get("nineteen_original_VPD_F_QC2_HH")==19 and
         summ.get("nineteen_original_VPD_invalid_at_site_temperature_wrt_water_count")==19 and
         summ.get("hypothetical_ERA_RHwater_transfer_physically_valid_count")==19 and
         summ.get("QC0_independent_source_temperature_conditioned_validation",{}).get(
               "all_within_21days_QC0",{}).get("matched_source_QC0_HH")==0 and
         summ.get("preexisting_Stage13AI_full_source_SHA256")==AI_SHA and
         summ.get("new_repair_or_approval") is False,
         "actual Stage13AJ validated source conditions changed")
    raw,site,_,_,_=mod.verify()
    need(len(raw)==len(site)==280320 and raw.index.equals(site.index) and
         (site.VPD_USE.isna().to_numpy()==site.QBOT.isna().to_numpy()).all() and
         site.VPD_USE.isna().sum()==45,
         "current exact 45 native missing source shadow differs")
    source=raw.loc[EVENT]
    need(source.VPD_F_QC.eq(2).all() and
         np.allclose(source.VPD_F,source.VPD_ERA,atol=1e-8,rtol=0) and
         site.loc[EVENT,"VPD_USE"].isna().all(),
         "nineteen original source ERA-derived VPD QCs or current HOLD changed")
    return mod,raw,site,summ
def run():
    mod,raw,site,summ=audit()
    ta=raw.TA_F.to_numpy(float)
    tq=raw.TA_F_QC.to_numpy(float)
    vpd=raw.VPD_F.to_numpy(float)
    vqc=raw.VPD_F_QC.to_numpy(float)
    et=raw.TA_ERA.to_numpy(float)
    ev=raw.VPD_ERA.to_numpy(float)
    st=site.TA_USE.to_numpy(float)
    sv=site.VPD_USE.to_numpy(float)
    goodt=(np.isfinite(ta)&(tq==0)&np.isfinite(et)&
         np.isfinite(st)&np.isclose(ta,st,atol=1e-7,rtol=0))
    nqc0=(goodt&(vqc==0)&np.isfinite(vpd)&np.isfinite(ev)&
          np.isfinite(sv)&np.isclose(vpd,sv,atol=1e-7,rtol=0))
    esobs=mod.ew(ta)
    esera=mod.ew(et)
    rh_raw=np.divide(ev,esera,out=np.full(len(ev),np.nan),
                      where=np.isfinite(ev)&np.isfinite(esera)&(esera>0))
    transfer=esobs*rh_raw
    # VPD is e_sat - actual vapor; ERA source RHwater is 1 - ev/e_sat(ERA).
    original_valid=(np.isfinite(esobs)&(vpd>0)&(vpd<esobs))
    raw_rh_valid=(np.isfinite(rh_raw)&(rh_raw>0)&(rh_raw<1))
    transfer_q,physical=mod.qfrom(transfer,ta,site.PSRF.to_numpy(float))
    obs_mask=nqc0&original_valid&raw_rh_valid&physical
    # Same actual season-year calendar day across 2009-2024. Exclude
    # 2014-12-30 through 2015-01-02 as embargo, no training or fitting.
    idx=raw.index
    ordinal=idx.dayofyear.to_numpy()
    winter=idx.month.isin((12,1,2))
    embargo=(idx>=pd.Timestamp("2014-12-30")) & (idx<pd.Timestamp("2015-01-03"))
    obs_mask &= ~embargo
    median_event_t=float(np.median(raw.loc[EVENT,"TA_F"]))
    tempdiff=abs(ta-median_event_t)
    tempbands=(3,5,8,12)
    matched=[]
    for yr in sorted(set(idx.year)):
        yy=(idx.year==yr)
        yy_q=yy&obs_mask
        yy_temp=yy&goodt
        yy_winter=yy_temp&winter
        matched.append({
          "year":int(yr),"original_source_tower_T_QC0_HH":int(yy_temp.sum()),
          "winter_tower_T_QC0_HH":int(yy_winter.sum()),
          "original_tower_VPD_QC0_and_T_QC0_physically_valid_HH":int(yy_q.sum()),
          "winter_QC0_eligible_source_HH":int((yy_q&winter).sum()),
          "cold_within_3C_eligible_QC0_HH":int((yy_q&(tempdiff<=3)).sum()),
          "cold_within_5C_eligible_QC0_HH":int((yy_q&(tempdiff<=5)).sum()),
          "winter_tower_minus_ERA_T_C_median":
             stats((ta-et)[yy_winter])["median"],
          "all_QC0_tower_minus_ERA_T_C_median":
             stats((ta-et)[yy_q])["median"]})
    rows=[]
    subsets={
      "ALL_16YEAR_ORIGINAL_MEASURED_QC0":obs_mask,
      "DEC_JAN_FEB_ORIGINAL_MEASURED_QC0":obs_mask&winter,
      "DEC_JAN_FEB_COLD_WITHIN_3C":obs_mask&winter&(tempdiff<=3),
      "DEC_JAN_FEB_COLD_WITHIN_5C":obs_mask&winter&(tempdiff<=5),
      "ALL_YEARS_COLD_WITHIN_3C":obs_mask&(tempdiff<=3),
      "ALL_YEARS_COLD_WITHIN_5C":obs_mask&(tempdiff<=5),
      "ALL_YEARS_COLD_WITHIN_8C":obs_mask&(tempdiff<=8),
      "ALL_YEARS_COLD_WITHIN_12C":obs_mask&(tempdiff<=12)}
    for key,mask in subsets.items():
        results=scores(transfer[mask],vpd[mask])
        results.update({
          "sample":key,"source_QC0_native_dates":
              int(idx[mask].normalize().nunique()),
          "source_QC0_distinct_years":int(np.unique(idx[mask].year).size),
          "median_site_tower_C":stats(ta[mask])["median"],
          "median_tower_minus_source_ERA_T_C":stats((ta-et)[mask])["median"],
          "validation_has_adequate_evidence": bool(results["n_source_QC0"]>=96
                 and idx[mask].normalize().nunique()>=5
                 and results["MAE_hPa"] is not None
                 and results["P90_abs_error_hPa"] is not None
                 and results["P90_abs_error_hPa"]<=1.0
                 and results["fraction_abs_error_gt_1hPa"]<=.10)})
        rows.append(results)
    diagnostic=pd.DataFrame(rows)
    source_event=raw.loc[EVENT]
    temp_era_gap=source_event.TA_F.to_numpy(float)-source_event.TA_ERA.to_numpy(float)
    winter_ta=(goodt&winter)
    winter_all=(np.isfinite(ta)&np.isfinite(et)&winter)
    diffs=pd.DataFrame({
      "native_time":[str(t) for t in EVENT],
      "source_tower_T_C":source_event.TA_F.to_numpy(float),
      "source_tower_T_QC":source_event.TA_F_QC.to_numpy(float),
      "source_companion_ERA_T_C":source_event.TA_ERA.to_numpy(float),
      "tower_minus_ERA_T_C":temp_era_gap,
      "abs_T_difference_exceeds_8C":abs(temp_era_gap)>8,
      "no_local_ERA5_Land_or_grid_geopotential_verified":True})
    details={
      "version":VER,"site":"US-Me6",
      "nineteen_original_ERA_equal_source_QC2_VPD":19,
      "nineteen_native_19HH_with_site_ERA_T_gt8C":int((abs(temp_era_gap)>8).sum()),
      "event_tower_minus_ERA_T_C":stats(temp_era_gap),
      "matched_QC0_tower_minus_ERA_T_C":stats((ta-et)[obs_mask]),
      "full_winter_tower_minus_ERA_T_C_at_T_QC0":stats((ta-et)[winter_ta]),
      "full_winter_tower_minus_ERA_T_C_any_T":stats((ta-et)[winter_all]),
      "original_tower_measured_QC0_eligible_16_years_HH":int(obs_mask.sum()),
      "full_16year_original_true_QC0_empirical_sample_groups":rows,
      "threshold_choices_not_inherited_science_approval":True,
      "nineteen_ERA_RH_to_site_physically_valid_not_skill_proof":True,
      "independent_ERA5_Land_grid_elevation_or_station_pressure_NOT_VERIFIED":True,
      "latest_Stage13AI_research_shadow_SHA256":AI_SHA,
      "new_research_shadow_written":False,"model_or_science_approved":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AK 19 NATIVE TOWER-ERA COLD TEMPERATURE DIFFERENCES",flush=True)
    print(diffs.to_string(index=False),flush=True)
    print("STAGE13AK YEARLY ORIGINAL MEASURED QC0 VS ERA SOURCE AVAILABILITY",flush=True)
    print(pd.DataFrame(matched).to_string(index=False),flush=True)
    print("STAGE13AK EXTENDED 2009-2024 REAL QC0 EMPIRICAL ERA-RH TRANSFER VALIDATION",flush=True)
    print(diagnostic.to_string(index=False),flush=True)
    print("STAGE13AK SCIENCE SUMMARY",json.dumps(details,indent=2),flush=True)
    return diffs,pd.DataFrame(matched),diagnostic,details
def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","run"):group.add_argument("--"+mode,action="store_true")
    args=ap.parse_args()
    selftest()
    if args.self_test:return
    diffs,yearly,metrics,s=run()
    if args.check:
        print("STAGE13AK ORIGINAL 16YEAR QC0/T-WINTER SOURCE CHECK PASS; NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13ak_Me6_19HH_16year_QC0_ERA_temp_donor_READONLY_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={
      "19_source_tower_ERA_T_deltas_no_orography_claim.csv":diffs,
      "yearly_full_original_measured_QC0_and_winter_T_context.csv":yearly,
      "stratified_16year_measured_QC0_ERA_water_RH_transfer_skill.csv":metrics}
    for name,df in docs.items():df.to_csv(out/name,index=False,float_format="%.17g")
    name="stage13ak_19HH_16year_original_QC0_winter_science_summary.json"
    note="NO_NEW_ERA_REPAIR_APPROVAL_OR_DATM_SOURCE_CHANGE"
    (out/name).write_text(json.dumps(s,indent=2)+"\n")
    (out/note).write_text("Original 16-year tower QC0 measured source vs same-release"
       " companion ERA. No ERA5-Land station or elevation proof; all 19 winter"
       " original QC2 site forcing remain HOLD. No source/forcing writes.\n")
    rec={"version":VER,"site":"US-Me6","new_science_approval":False,
       "source_or_forcing_written":False,
       "outputs_SHA256":{nm:sha(out/nm) for nm in [*docs,name,note]}}
    (out/"stage13ak_READONLY_science_SHA_receipt.json").write_text(json.dumps(rec,indent=2)+"\n")
    print("STAGE13AK READONLY OUTPUT:",out,flush=True)
    print("STAGE13AK 19HH 16YEAR ORIGINAL QC0 ERA TEMPERATURE DONOR REVIEW COMPLETE; NO FORCING/DATM/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AK SOURCE SCIENCE HOLD:",exc,file=sys.stderr,flush=True)
        traceback.print_exc();raise SystemExit(2)

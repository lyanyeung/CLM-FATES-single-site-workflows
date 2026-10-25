#!/usr/bin/env python3
"""Stage12k: investigate Stage12j GRID_RH QC0 validation tail errors, read-only.

Stage12j passed syntactically and ran but NONE of four methods passed
predeclared all-three-year cold-observation science gate. GRID_RH had
small signed bias and <=1.5 hPa MAE, but 10.3%-15.3% of valid measured
QC0 cold analogues had |error|>2hPa (maximum acceptable 10%).

Do NOT lower the threshold. This science-only diagnostic precisely
reproduces the Stage12j QC0 cold-gridRH aggregate results from the
three SHA-sealed original FLUXMET plus new ERA5-Land years. Disaggregate
valid and invalid original measured QC0 cold observations by year,
month, original native clock hour, 5C-cold tower T bins and original
observed VPD bins. Separately classify error>2 hPa episodes and compare
the original 1,035 Stage12g held native events' T/month distributions
to those of observed QC0 cold analogues, without using held events for
training, replacing tower measurements or inferring a clock change.

--self-test: synthetic bin/error/hold identity QA without source reads.
--check: full original Stage12j/I/H/G/ERA source SHA receipts and
         in-memory cold QC0 validation; ZERO file writes.
--run: same verification, one NEW SHA-receipted science REPORT ONLY.
No altered VPD, QBOT, TA, PA, site timestamps, source or CLM-FATES.
No Post-v5, DATM or spinup approval.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12k-v1-20261025-US-MtB-verified-GRID_RH-QC0-tail"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
J=ROOT/"science_trials/stage12j_US-MtB_QC0_elevation_aware_humidity_trial_20261025T065237Z_699cdb7f"
I=ROOT/"reports/stage12i_US-MtB_orography_pressure_20261025T064222Z_2944f5f6"
JS=BASE/"scripts/stage12/12j_us_mtb_elevation_aware_QC0_humidity_crossvalidation.py"
JS_BLOB="92ac1fed33967d5a6af24cbd3bbab0e7b150c499"
YEARS=(2020,2022,2024)
N_TARGET={2020:300,2022:328,2024:407}
T_BINS=(-100.,-15.,-10.,-5.,0.,5.000001)
T_LABELS=("<-15","-15:-10","-10:-5","-5:0","0:5")
V_BINS=(-.000001,.25,.5,1.,2.,5.,1000.)
V_LABELS=("0:0.25","0.25:0.5","0.5:1","1:2","2:5",">5")
REPORTS={
  "three_year_QC0_GRID_RH_reproduced_gate.csv",
  "cold_QC0_observed_error_by_month.csv",
  "cold_QC0_observed_error_by_tower_temperature.csv",
  "cold_QC0_observed_error_by_original_VPD.csv",
  "QC0_HIGH2_contiguous_native_halfhour_episodes.csv",
  "held_1035_tower_temperature_and_month_analogue_coverage.csv",
  "three_year_QC0_cold_physics_disposition.csv",
  "SCIENCE_HOLD.md"
}

def normal_file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/symlink previously verified source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with normal_file(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def blob(p):
    a=normal_file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(a)).encode()+b"\0"+a).hexdigest()
def numeric(x):
    a=pd.to_numeric(x,errors="coerce").to_numpy(dtype=float)
    a[(~np.isfinite(a))|(a<=-9990)]=np.nan
    return a
def tbins(vals):
    return pd.cut(vals,bins=T_BINS,labels=T_LABELS,
                  include_lowest=True).astype("object")
def vbins(vals):
    return pd.cut(vals,bins=V_BINS,labels=V_LABELS,
                  include_lowest=True).astype("object")
def self_test():
    assert sum(N_TARGET.values())==1035 and len(YEARS)==3
    assert len(T_LABELS)==len(T_BINS)-1 and len(V_LABELS)==len(V_BINS)-1
    assert list(tbins(np.array([-20.,-12.,-7.,-2.,3.])))==list(T_LABELS)
    assert list(vbins(np.array([.1,.3,.7,1.4,3.,6.])))==list(V_LABELS)
    print("STAGE12K SELF-TEST PASS: 3 original years, 1035 immutable holds, fixed QC0 temp/VPD bins, >2hPa error threshold unchanged, NO WRITES",flush=True)
def prior():
    if not J.is_dir() or J.is_symlink():
        raise ValueError("SHA-sealed Stage12j research trial missing")
    normal_file(J/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    r=json.loads(normal_file(J/"stage12j_science_only_sha_receipt.json").read_text())
    expected={
      "three_year_original_VPD_QC0_cold_validation.csv",
      "four_method_three_year_independent_QC0_gates.csv",
      "all_1035_held_times_four_method_proposals_NO_APPROVAL.csv",
      "selected_method_held_target_candidate_event_ledger.csv",
      "selected_method_unresolved_target_events.csv",
      "SCIENCE_HOLD.md"
    }
    if (r.get("version")!="batch03-stage12j-v1-20261025-QC0-elevation-aware-RH"
        or r.get("Stage12i_original_receipt_SHA256")!=sha(I/"stage12i_pressure_science_receipt.json")
        or r.get("original_1035_held_time_events")!=1035
        or r.get("validated_method") is not None
        or r.get("new_candidate_research_repair_events")!=0
        or r.get("source_T_P_UTC_changed") is not False
        or r.get("previous_QC0_observations_modified")!=0
        or r.get("Postv5_approved")!=0 or r.get("DATM_ready")!=0
        or r.get("spinup_authorized")!=0
        or r.get("INCOMPLETE_marker_present") is not True
        or set(r.get("output_sha256",{}))!=expected):
        raise ValueError("Original Stage12j FAIL-CLOSED science receipt changed")
    for name,dig in r["output_sha256"].items():
        if sha(J/name)!=dig:
            raise ValueError("Stage12j SHA-sealed original output differs: "+name)
    if blob(JS)!=JS_BLOB:
        raise ValueError("Reviewed Stage12j Python source Git blob differs")
    spec=importlib.util.spec_from_file_location("stage12j_pinned_for_stage12k",JS)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    h,src,specinfo,catalog,held,full=mod.upstream()
    if len(held)!=1035:
        raise ValueError("Stage12j 1035 original held target source events changed")
    old=pd.read_csv(normal_file(J/"three_year_original_VPD_QC0_cold_validation.csv"))
    gate=pd.read_csv(normal_file(J/"four_method_three_year_independent_QC0_gates.csv"))
    if (len(old)!=12 or len(gate)!=4 or
        not gate.all_three_QC0_validation_years_pass.astype(str).str.lower().eq("false").all()):
        raise ValueError("Stage12j original rejection decision changed")
    return mod,src,specinfo,catalog,held,old
def summary(frame,fields):
    result=[]
    for key,group in frame.groupby(fields,dropna=False,observed=True,sort=True):
        if not isinstance(key,tuple):
            key=(key,)
        valid=group.loc[group.valid_GRID_RH]
        errs=valid.error_hpa.abs()
        row=dict(zip(fields,key))
        row.update({
           "measured_QC0_cold_N":len(group),
           "physically_valid_candidate_N":len(valid),
           "physically_valid_fraction":len(valid)/len(group),
           "GRID_RH_MAE_hPa":float(errs.mean()) if len(valid) else np.nan,
           "GRID_RH_bias_hPa":float(valid.error_hpa.mean()) if len(valid) else np.nan,
           "large_abs_error_gt2hPa_count":int((errs>2.).sum()),
           "large_abs_error_gt2hPa_fraction_of_valid":float((errs>2.).mean()) if len(valid) else np.nan,
           "median_original_site_T_C":float(group.source_T_C.median()),
           "median_original_QC0_VPD_hPa":float(group.measured_VPD_hPa.median())
        })
        result.append(row)
    return pd.DataFrame(result)
def evaluate():
    mod,src,spec,catalog,held,original_results=prior()
    wanted=set(held.native_key)
    complete=[];profiles=[];episodes=[]
    for year in YEARS:
        print("STAGE12K SOURCE YEAR:",year,flush=True)
        names=["TIMESTAMP_START","TA_F","PA_F","VPD_F","VPD_F_QC","TA_F_QC"]
        data=pd.read_csv(normal_file(spec["primary"]),usecols=names,
             dtype={"TIMESTAMP_START":str},low_memory=False)
        date=pd.to_datetime(data.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        mask=date.dt.year.eq(year)&~((date.dt.month==2)&(date.dt.day==29))
        data=data.loc[mask].reset_index(drop=True)
        if len(data)!=17520:
            raise ValueError("Original source noleap native year length mismatch")
        native=pd.to_datetime(data.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        originalT=numeric(data.TA_F);siteP=numeric(data.PA_F)*1000
        observed=numeric(data.VPD_F)
        qcv=numeric(data.VPD_F_QC);qct=numeric(data.TA_F_QC)
        plan,source=catalog[("US-MtB",year)]
        if sha(source["path"])!=source["sha256"]:
            raise ValueError("New Stage12f year source SHA changed")
        loc=plan["request"]["location"]
        hours,grid,coord=src.grid_fields(normal_file(source["path"]),year,
                       (loc["latitude"],loc["longitude"]))
        dt=native+pd.Timedelta(minutes=int(spec["native_minutes"])/2)-pd.Timedelta(hours=src.BIF_OFFSET["US-MtB"])
        tempgrid=src.interpolate(hours,grid["t2m"],dt)-273.15
        dewgrid=src.interpolate(hours,grid["d2m"],dt)-273.15
        pg=src.interpolate(hours,grid["sp"],dt)
        dz=287.05*((tempgrid+originalT)/2+273.15)/9.80665*np.log(pg/siteP)
        temp_norm=tempgrid-mod.LAPSE_K_KM*dz/1000.
        original_good=(np.isfinite(originalT)&np.isfinite(siteP)&
            np.isfinite(tempgrid)&np.isfinite(dewgrid)&np.isfinite(pg)&
            (siteP>45000)&(siteP<110000)&(pg>45000)&(pg<110000)&
            (dewgrid<=tempgrid+.1)&(np.abs(dz)<4500))
        qc0=(qcv==0)&(qct==0)&(observed>=0)&(observed<mod.esw(originalT))&(
             mod.physical(originalT,siteP,mod.esw(originalT)-observed))&original_good
        cold=qc0&(originalT<=5)
        candidate_e=mod.dewpoint_model(originalT,tempgrid,dewgrid,pg,siteP)["GRID_RH"]
        phys=mod.physical(originalT,siteP,candidate_e)&original_good
        terrain=np.isfinite(temp_norm)&(np.abs(originalT-temp_norm)<=5)
        eligible=phys&terrain
        candidate_v=mod.esw(originalT)-candidate_e
        err=candidate_v-observed
        if int(cold.sum())<50:
            raise ValueError("Fewer than 50 independent cold measured QC0 observations")
        year_table=pd.DataFrame({
          "native_key":native.dt.strftime("%Y%m%d%H%M").to_numpy(),
          "year":year,"month":native.dt.month.to_numpy(),
          "native_clock_hour":native.dt.hour.to_numpy(),
          "source_T_C":originalT,
          "measured_VPD_hPa":observed,
          "GRID_RH_predicted_VPD_hPa":candidate_v,
          "source_QC0_cold":cold,
          "physically_valid_candidate":eligible,
          "valid_GRID_RH":cold&eligible,
          "error_hpa":err,
          "target_original_1035_hold":np.isin(
              native.dt.strftime("%Y%m%d%H%M").to_numpy(),list(wanted))
        })
        subsets=year_table.loc[year_table.source_QC0_cold].copy()
        valid=subsets.loc[subsets.valid_GRID_RH]
        from_old=original_results.loc[
           original_results.year.eq(year)&original_results.method.eq("GRID_RH")]
        if len(from_old)!=1:
            raise ValueError("Missing signed Stage12j baseline GRID_RH year")
        truth=from_old.iloc[0]
        calculated={
           "QC0_cold_source_N":len(subsets),
           "QC0_cold_physically_valid_model_N":len(valid),
           "QC0_cold_pred_VPD_MAE_hPa":valid.error_hpa.abs().mean(),
           "QC0_cold_VPD_bias_hPa":valid.error_hpa.mean(),
           "QC0_cold_fraction_abs_error_over2hPa":(valid.error_hpa.abs()>2).mean()
        }
        for field,value in calculated.items():
            if not np.isclose(value,float(truth[field]),rtol=1e-8,atol=1e-7):
                raise ValueError("Original signed Stage12j GRID_RH metrics NOT reproducible: "+str((year,field,value,truth[field])))
        if int(year_table.target_original_1035_hold.sum())!=N_TARGET[year]:
            raise ValueError("Original source target native identity unexpectedly changed")
        subsets["temperature_bin"]=tbins(subsets.source_T_C.to_numpy())
        subsets["measured_VPD_bin"]=vbins(subsets.measured_VPD_hPa.to_numpy())
        subsets["large_error_gt2"]=subsets.valid_GRID_RH & subsets.error_hpa.abs().gt(2.)
        complete.append(subsets)
        target=year_table.loc[year_table.target_original_1035_hold].copy()
        target["temperature_bin"]=tbins(target.source_T_C.to_numpy())
        target["measured_VPD_bin"]="NOT_VALIDATED_TARGET"
        profiles.append(target)
        # Consecutive source-native half-hours of verified QC0 error >2 hPa.
        high=subsets.loc[subsets.large_error_gt2].copy()
        high["timestamp"]=pd.to_datetime(high.native_key,format="%Y%m%d%H%M")
        high["break"]=(high.timestamp.diff()!=pd.Timedelta(minutes=30)).cumsum()
        for block,g in high.groupby("break"):
            episodes.append({
                "year":year,"start_native_key":g.native_key.iloc[0],
                "end_native_key":g.native_key.iloc[-1],
                "consecutive_halfhours":len(g),
                "duration_hours":len(g)*.5,
                "median_original_site_T_C":float(g.source_T_C.median()),
                "median_measured_QC0_VPD_hPa":float(g.measured_VPD_hPa.median()),
                "median_abs_GRID_RH_error_hPa":float(g.error_hpa.abs().median()),
                "max_abs_GRID_RH_error_hPa":float(g.error_hpa.abs().max())
            })
    clean=pd.concat(complete,ignore_index=True)
    pending=pd.concat(profiles,ignore_index=True)
    if len(pending)!=1035:
        raise ValueError("Incorrect signed original Stage12j target row count")
    summary_year=summary(clean,["year"])
    observed_month=summary(clean,["year","month"])
    obs_temp=summary(clean,["year","temperature_bin"])
    obs_vpd=summary(clean,["year","measured_VPD_bin"])
    episodes_df=pd.DataFrame(episodes).sort_values(
        ["consecutive_halfhours","year","start_native_key"],ascending=[False,True,True])
    counts=clean.groupby(["year","month","temperature_bin"],observed=True).size().rename("QC0_cold_analogue_N")
    target_counts=pending.groupby(["year","month","temperature_bin"],observed=True).size().rename("held_target_N")
    joined=pd.concat([counts,target_counts],axis=1).fillna(0).astype(int).reset_index()
    joined["QC0_cold_analogue_support_gt0"]=joined.QC0_cold_analogue_N.gt(0)
    joined["QC0_cold_analogue_support_at_least20"]=joined.QC0_cold_analogue_N.ge(20)
    if summary_year.measured_QC0_cold_N.sum()!=int(clean.shape[0]):
        raise ValueError("Stage12k cold QC0 source group count differs")
    if int(joined.held_target_N.sum())!=1035:
        raise ValueError("Stage12k target source-year month/temperature count differs")
    rows_without20=int(joined.loc[joined.QC0_cold_analogue_N.lt(20),"held_target_N"].sum())
    return summary_year,observed_month,obs_temp,obs_vpd,episodes_df,joined,rows_without20
def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=p.parse_args()
    print("STAGE12K — US-MtB GRID_RH MEASURED QC0 ERROR-TAIL SOURCES | "+VERSION,flush=True)
    self_test()
    if args.self_test:return
    yearly,monthly,temp,vpd,episodes,coverage,without20=evaluate()
    print("\n========== SIGNED STAGE12J GRID_RH QC0 REPRODUCED ==========",flush=True)
    print(yearly.to_string(index=False),flush=True)
    print("\n========== COLD T-BIN QC0 ERROR REGIMES ==========",flush=True)
    print(temp.to_string(index=False),flush=True)
    print("\n========== COLD VPD-BIN QC0 ERROR REGIMES ==========",flush=True)
    print(vpd.to_string(index=False),flush=True)
    print("\n========== LARGE-ERROR CONTIGUOUS QC0 EPISODES: TOP 15 ==========",flush=True)
    print(episodes.head(15).to_string(index=False),flush=True)
    print("\n========== 1035 HELD TARGETS VS MEASURED QC0 TEMPERATURE/MONTH SUPPORT ==========",flush=True)
    print(coverage.to_string(index=False),flush=True)
    print("\nSTAGE12K SUMMARY: prior_1035_original_Stage12g_HOLD=1035 "
          "original_Stage12j_safety_gate_failed=True "
          f"contiguous_QC0_error_gt2hPa_episodes={len(episodes)} "
          f"held_targets_with_less_than20_analogues_in_same_year_month_Tbin={without20} "
          "new_RH_repairs=0 original_tower_T_P_clock_changes=0 "
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12K CHECK ONLY: NO SOURCE/REPORT/MODEL WRITES.",flush=True)
        return
    path=ROOT/"reports"/("stage12k_US-MtB_GRID_RH_QC0_error_regime_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    path.mkdir(parents=True,exist_ok=False)
    reports={
       "three_year_QC0_GRID_RH_reproduced_gate.csv":yearly,
       "cold_QC0_observed_error_by_month.csv":monthly,
       "cold_QC0_observed_error_by_tower_temperature.csv":temp,
       "cold_QC0_observed_error_by_original_VPD.csv":vpd,
       "QC0_HIGH2_contiguous_native_halfhour_episodes.csv":episodes,
       "held_1035_tower_temperature_and_month_analogue_coverage.csv":coverage,
       "three_year_QC0_cold_physics_disposition.csv":yearly
    }
    for name,data in reports.items():
        data.to_csv(path/name,index=False)
    (path/"SCIENCE_HOLD.md").write_text(
        "Stage12k read-only original measured QC0 error-tail SOURCE DIAGNOSTIC. "
        "No observed QC0 VPD/F/T/pressure/time data replaced or used as a "
        "new humidity release. The source GRID_RH method FAILED original "
        "Stage12j all-three-year acceptance threshold for >2hPa VPD "
        "outlier frequency; threshold is deliberately unchanged. Original "
        "source timestamps and BIF UTC offset are provisional. All 1035 "
        "Stage12g targets and 233 older scientific holds remain BLOCKED. "
        "No Post-v5, DATM, CIME, Slurm or spinup authorization.\n")
    report_receipt={
      "version":VERSION,
      "Stage12j_original_SHA256":sha(J/"stage12j_science_only_sha_receipt.json"),
      "measurements_original_QC0_unchanged":True,
      "original_target_1035_holds_unchanged":True,
      "previous_science_gate_failed":True,
      "source_clock_approved":False,
      "new_humidity_repair_count":0,
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "output_sha256":{name:sha(path/name) for name in [*reports,"SCIENCE_HOLD.md"]}
    }
    (path/"stage12k_source_error_regime_SHA_receipt.json").write_text(
         json.dumps(report_receipt,indent=2)+"\n")
    print("STAGE12K QC0 SOURCE ERROR REPORT DIR:",path,flush=True)
    print("NO EXISTING STAGE12B THROUGH STAGE12J, SITE ORIGINAL FORCING OR MODEL JOB WRITES.",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12K STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

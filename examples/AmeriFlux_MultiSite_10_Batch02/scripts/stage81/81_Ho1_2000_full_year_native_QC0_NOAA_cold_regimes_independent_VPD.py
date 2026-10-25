#!/usr/bin/env python3
"""Stage81 original-source full-year native Ho1 TA_F(QC0) versus NOAA audit.

WHY: Stage80 PASS 36/36 VPD-selected temperature-HOLD episodes; at their
boundaries, original native T rarely jumps while NOAA-Ho1 discrepancy
usually persists on either side. The 36 VPD-selected episodes must NOT
be mistaken for actual air-temperature residual episode boundaries.

Science question: across ALL 17,568 source-native Ho1 year-2000 HH,
when do QC0 native measured T and source-QC-screened NOAA Bangor airport
T differ? Detect persistent residual regimes WITHOUT first selecting
VPD hard events or using the earlier 505 source-case mask to define
the run. Partition residuals by full year/month/day/source VPD status.

Original Ho1 air temperature is NOT automatically wrong when it
differs from a ground station ~46 km away (Bangor airport). NOAA
meteorological sources and ERA5 may not be statistically independent;
forest canopy, observation height, stable inversions, snow and local
microclimate are science limitations. Residual thresholds +/-8C are
exploratory; no auto T correction, no historical BIF offset approval.

Dependencies: exact Git-blob SHA pinned Stage80 Python for verifying
Stage79, Stage78, original Stage49 primary HH file, Stage74 humidity
science HOLD, Stage77 archived original NOAA year-2000 source; AND the
actual Stage80 operator PASS SHA-verified report. No network.

--self-test: pure source-free synthetic 30min episode partition test.
--check: prove all source/report/Code SHA and exact Stage80/505/36 gates,
         NO WRITES or network.
--audit: read original Ho1 2000 source-native HH, source-QC-screened NOAA
         at nominal unapproved UTC-5, compute raw per-HH residuals,
         full-year monthly/daily diagnostics and *actual* continuous
         >+8C cold and <-8C warm NOAA-Ho1 residual runs, then write
         a NEW isolated science report. All original HOLDs remain.
"""
import argparse,hashlib,json
from collections import Counter
from datetime import datetime, timezone
from importlib import util
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
PARENT=BASE/"scripts/stage80/80_Ho1_2000_original_T_QC0_episode_boundary_and_NOAA_transition_audit.py"
PARENT_BLOB="945ca08b393d15fd8f710619d60a001dd9a1e9ad"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORTS=ROOT/"reports"
PREVIOUS=REPORTS/"stage80_Ho1_2000_505_QC0_episode_boundary_original_NOAA_20261025T184904Z_7a1491db"
NOAA_SHA="2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620"
EXPECTED_ROWS=17568
EXPECTED_505=505
EXPECTED_VPD_HARD=1069
EXPECTED_36=36
THRESHOLD_C=8.0

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def git_blob(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Stage80 pinned code missing/symlinked")
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def load_parent():
    if git_blob(PARENT)!=PARENT_BLOB:
        raise ValueError("Stage80 original source-code Git blob differs")
    spec=util.spec_from_file_location("pinned_stage80_original_Ho1",PARENT)
    mod=util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def validate_operator_pass():
    m=json.loads((PREVIOUS/"stage80_source_science_manifest.json").read_text())
    if ((PREVIOUS/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE80_HO1_2000_QC0_FLUXNET_NOAA_EPISODE_BOUNDARY_TRIAGE_v1" or
        m.get("source_2000_QC0_hard_T_CDS_disagreement_HH")!=505 or
        m.get("n_source_consecutive_episodes")!=36 or
        m.get("original_hourly_source_full_2000_HH")!=EXPECTED_ROWS or
        m.get("original_stage74_humidity_shadow_15199_untouched") is not True or
        m.get("original_1675_temperature_HOLDs_unchanged") is not True or
        m.get("original_16874_humidity_HOLDs_unchanged") is not True or
        m.get("official_historical_UTC_BIF_effective_date_approved") is not False or
        m.get("native_source_T_replacements_approved") is not False or
        m.get("approved_for_DATM") is not False or
        m.get("source_SHA256",{}).get("stage78_original_script_git_blob")!=
            "002b6fb491b1d9dd6e570feed31a3c041f0aae2a" or
        m.get("source_SHA256",{}).get("stage77_NOAA_GHCNh_2000_raw_SHA256")!=NOAA_SHA):
        raise ValueError("Stage80 original science/operator PASS manifest changed")
    for filename,digest in m.get("outputs_SHA256",{}).items():
        if sha(PREVIOUS/filename)!=digest:
            raise ValueError("Stage80 independent SHA evidence mutated: "+filename)
    if set(m.get("outputs_SHA256",{}))!={
         "505_original_QC0_episode_plusminus6h_FLUXNET_NOAA_provenance.csv",
         "35_original_QC0_episode_2h_boundary_and_T_shift_review.csv"}:
        raise ValueError("Stage80 original output filenames unexpectedly changed")
    old=pd.read_csv(PREVIOUS/
        "35_original_QC0_episode_2h_boundary_and_T_shift_review.csv")
    if (len(old)!=36 or int(old["source_HH"].sum())!=505 or
        old["episode_id"].duplicated().any() or
        old["start_boundary_GT8C_diagnostic_only"].astype(str).str.lower().eq("true").any() or
        old["end_boundary_GT8C_diagnostic_only"].astype(str).str.lower().eq("true").any()):
        raise ValueError("Original Stage80 36 episodes, 505 sources or boundary checks altered")
    return m,old

def inputs(parent):
    proof,summary=validate_operator_pass()
    mod78,eps,m79,native=parent.checked_input()
    if (len(eps)!=EXPECTED_36 or len(native)!=EXPECTED_ROWS or
        native["tower_local_start"].duplicated().any() or
        not native["native_dt"].is_monotonic_increasing or
        int(native["original_2000_hard_VPD"].sum())!=EXPECTED_VPD_HARD or
        int(native["original_505_T_QC0_CDS_disagreement"].sum())!=EXPECTED_505 or
        len(set(native["native_dt"].dt.month))!=12 or
        not native.loc[native["original_505_T_QC0_CDS_disagreement"],
                       "TA_QC"].eq(0).all()):
        raise ValueError("Original Ho1 full-year physical HH and VPD/HOLD cohort changed")
    # Period continuity, not just unique timestamps.
    full=pd.date_range("2000-01-01 00:00","2000-12-31 23:30",freq="30min")
    if not pd.DatetimeIndex(native["native_dt"]).equals(full):
        raise ValueError("Year-2000 native source HH timestamps incomplete or misordered")
    if sha(mod78.S77/mod78.RAW77)!=NOAA_SHA:
        raise ValueError("NOAA primary source SHA changed since Stage77")
    return proof,summary,parent,mod78,native

def all_year_pairs(parent,mod78,source):
    # Stage80 scans each original HH using Stage78's pinned accelerated
    # Stage40 parser and source-QC tie-rejection method.
    matched=parent.nearest_noaa(mod78,source)
    y=source.copy()
    y["NOAA_source_QC_status"]=[r[0] for r in matched]
    y["NOAA_report_UTC"]=[r[1] for r in matched]
    y["NOAA_T_C"]=[r[2] for r in matched]
    y["TA_C"]=pd.to_numeric(y["TA_C"],errors="coerce")
    y["TA_QC"]=pd.to_numeric(y["TA_QC"],errors="coerce")
    y["original_VPD_F_QC"]=pd.to_numeric(y["original_VPD_F_QC"],errors="coerce")
    # Preserve raw original TA_C as-is; label source validity.
    y["original_measured_T_QC0"]=y["TA_QC"].eq(0)&y["TA_C"].between(
        -80,65,inclusive="both")
    y["NOAA_QC_source_available"]=y["NOAA_source_QC_status"].eq(
        "PROVISIONAL_SOURCE_QC")
    y["temperature_residual_pair_valid"]=(
        y["original_measured_T_QC0"]&
        y["NOAA_QC_source_available"]&
        np.isfinite(y["NOAA_T_C"]))
    y["NOAA_minus_original_Ho1_T_C"]=(
        y["NOAA_T_C"]-y["TA_C"]).where(
            y["temperature_residual_pair_valid"])
    residual=y["NOAA_minus_original_Ho1_T_C"]
    y["NOAA_warmer_than_Ho1_GT8C"]=residual.gt(THRESHOLD_C)
    y["NOAA_colder_than_Ho1_GT8C"]=residual.lt(-THRESHOLD_C)
    y["original_hard_VPD_nonhard_group"]=np.where(
        y["original_2000_hard_VPD"],"ORIGINAL_VPD_HARD",
        "NOT_ORIGINAL_VPD_HARD")
    y["original_505_T_delta_selected"]=y[
        "original_505_T_QC0_CDS_disagreement"]
    y["historical_BIF_UTC_effective_dates_approved"]=False
    y["NOAA_ground_truth_for_Ho1"]=False
    y["Ho1_T_correction_approved"]=False
    y["approved_for_DATM"]=False
    cases=y.loc[y["original_505_T_delta_selected"]]
    if (len(y)!=EXPECTED_ROWS or
        len(cases)!=505 or
        cases["NOAA_QC_source_available"].sum()!=498 or
        cases["NOAA_report_UTC"].loc[cases[
            "temperature_residual_pair_valid"]].nunique()!=306 or
        not cases["TA_QC"].eq(0).all() or
        y["NOAA_report_UTC"].loc[y["temperature_residual_pair_valid"]].eq("").any()):
        raise ValueError("Original Stage77 505/498/306 source match validation failed")
    return y

def summarize_per_group(df,group_cols):
    summary=[]
    for key,g in df.groupby(group_cols,sort=True,dropna=False):
        if not isinstance(key,tuple):key=(key,)
        valid=g.loc[g["temperature_residual_pair_valid"]]
        residual=valid["NOAA_minus_original_Ho1_T_C"]
        # Report-equal MAE: one original NOAA source report may
        # contribute to 2 separate native HH.
        distinct=valid.groupby("NOAA_report_UTC")[
            "NOAA_minus_original_Ho1_T_C"].apply(
                lambda s:s.abs().mean())
        rec=dict(zip(group_cols,key))
        rec.update({
          "native_source_HH":len(g),
          "original_measured_T_QC0_HH":int(g["original_measured_T_QC0"].sum()),
          "original_source_QC0_NOAA_paired_HH":len(valid),
          "distinct_NOAA_source_reports":len(distinct),
          "NOAA_warmer_than_Ho1_GT8C_HH":int(
            g["NOAA_warmer_than_Ho1_GT8C"].sum()),
          "NOAA_colder_than_Ho1_GT8C_HH":int(
            g["NOAA_colder_than_Ho1_GT8C"].sum()),
          "VPD_hard_HH":int(g["original_2000_hard_VPD"].sum()),
          "original_selected_505_HH":int(
            g["original_505_T_delta_selected"].sum()),
          "NOAA_minus_Ho1_signed_median_C":float(
            residual.median()) if len(valid) else np.nan,
          "NOAA_minus_Ho1_QC0_HH_abs_MAE_C":float(
            residual.abs().mean()) if len(valid) else np.nan,
          "NOAA_report_equal_abs_MAE_C":float(
            distinct.mean()) if len(distinct) else np.nan,
          "NOAA_not_local_tower_ground_truth":True,
          "historical_BIF_UTC_approved":False,
          "DATM_approved":False})
        summary.append(rec)
    return pd.DataFrame(summary)

def classify_runs(df,flag,label):
    """Whole-year temperature-residual runs, NOT VPD-selected runs."""
    subset=df.loc[df[flag]].copy()
    if not len(subset):
        return pd.DataFrame(columns=[
            "temperature_residual_regime","native_start","native_end",
            "n_native_30min_QC0_NOAA_matched_HH"])
    subset["run_id"]=(subset["native_dt"].diff()!=pd.Timedelta(
        minutes=30)).cumsum()
    out=[]
    for run,part in subset.groupby("run_id",sort=True):
        res=part["NOAA_minus_original_Ho1_T_C"]
        out.append({
          "temperature_residual_regime":label,
          "native_start":str(part["tower_local_start"].iloc[0]),
          "native_end":str(part["tower_local_start"].iloc[-1]),
          "n_native_30min_QC0_NOAA_matched_HH":len(part),
          "consecutive_duration_hours":len(part)*0.5,
          "NOAA_source_unique_reports":int(part["NOAA_report_UTC"].nunique()),
          "native_QC0_T_median_C":float(part["TA_C"].median()),
          "NOAA_source_QC_T_median_C":float(part["NOAA_T_C"].median()),
          "NOAA_minus_Ho1_signed_median_C":float(res.median()),
          "native_VPD_hard_HH_inside":int(part["original_2000_hard_VPD"].sum()),
          "native_VPD_nonhard_HH_inside":int(
               (~part["original_2000_hard_VPD"]).sum()),
          "original_505_VPD_selected_Tdelta_cases_inside":int(
               part["original_505_T_delta_selected"].sum()),
          "original_VPD_source_QC0_HH":int(part["original_VPD_F_QC"].eq(0).sum()),
          "original_VPD_source_QC1_HH":int(part["original_VPD_F_QC"].eq(1).sum()),
          "original_VPD_source_QC2_HH":int(part["original_VPD_F_QC"].eq(2).sum()),
          "year_start_or_end_may_truncate_regime":bool(
             part["native_dt"].iloc[0]==df["native_dt"].iloc[0] or
             part["native_dt"].iloc[-1]==df["native_dt"].iloc[-1]),
          "historical_BIF_UTC_approved":False,
          "T_source_replacement_approved":False,
          "DATM_approved":False})
    return pd.DataFrame(out).sort_values(
        ["n_native_30min_QC0_NOAA_matched_HH","native_start"],
        ascending=[False,True]).reset_index(drop=True)

def calculate(full):
    x=full.copy()
    x["source_month"]=x["native_dt"].dt.month
    x["source_day"]=x["native_dt"].dt.strftime("%Y-%m-%d")
    x["source_local_3hour_bin_start"]=(x["native_dt"].dt.hour//3)*3
    bymonth=summarize_per_group(x,["source_month"])
    bymonth_vpd=summarize_per_group(x,[
        "source_month","original_hard_VPD_nonhard_group"])
    byday=summarize_per_group(x,["source_day"])
    byhour=summarize_per_group(x,[
        "source_month","source_local_3hour_bin_start",
        "original_hard_VPD_nonhard_group"])
    cold=classify_runs(x,"NOAA_warmer_than_Ho1_GT8C",
                      "SOURCE_QC0_HO1_COLDER_THAN_NOAA_GT8C")
    warm=classify_runs(x,"NOAA_colder_than_Ho1_GT8C",
                      "SOURCE_QC0_HO1_WARMER_THAN_NOAA_GT8C")
    runs=pd.concat([cold,warm],ignore_index=True)
    if (int(bymonth["native_source_HH"].sum())!=EXPECTED_ROWS or
        int(bymonth_vpd["native_source_HH"].sum())!=EXPECTED_ROWS or
        int(byday["native_source_HH"].sum())!=EXPECTED_ROWS or
        int(byhour["native_source_HH"].sum())!=EXPECTED_ROWS or
        int(cold["n_native_30min_QC0_NOAA_matched_HH"].sum())!=
            int(x["NOAA_warmer_than_Ho1_GT8C"].sum()) or
        int(warm["n_native_30min_QC0_NOAA_matched_HH"].sum())!=
            int(x["NOAA_colder_than_Ho1_GT8C"].sum())):
        raise ValueError("Full-year direct source residual annual/monthly/day/run closure changed")
    print("STAGE81 FULL 2000 original native source HH",len(x),
          "QC0 valid",int(x["original_measured_T_QC0"].sum()),
          "original VPD hard",int(x["original_2000_hard_VPD"].sum()),
          "QC0 + matched NOAA",int(x["temperature_residual_pair_valid"].sum()))
    print("STAGE81 FULL YEAR NOAA-Ho1 QC0 residual > +8C",
          int(x["NOAA_warmer_than_Ho1_GT8C"].sum()),
          "including original 505 selected",int(
             x.loc[x["NOAA_warmer_than_Ho1_GT8C"],
                   "original_505_T_delta_selected"].sum()))
    print("STAGE81 FULL YEAR NOAA-Ho1 QC0 residual < -8C",
          int(x["NOAA_colder_than_Ho1_GT8C"].sum()))
    print("STAGE81 SOURCE MONTHLY REANALYSIS-FREE ORIGINAL T/NOAA RESIDUAL CENSUS")
    print(bymonth.to_string(index=False))
    print("STAGE81 FULL YEAR SPLIT ORIGINAL HARD-VPD VS NONHARD MONTHS")
    print(bymonth_vpd.to_string(index=False))
    print("STAGE81 TRUE FULL-SOURCE QC0 COLD RESIDUAL RUNS",len(cold),
          "TOP 30")
    print(cold.head(30).to_string(index=False))
    print("STAGE81 TRUE FULL-SOURCE QC0 WARM RESIDUAL RUNS",len(warm),
          "TOP 15")
    print(warm.head(15).to_string(index=False))
    print("STAGE81 NO HISTORICAL TIME, SOURCE T, NOAA/TRUTH OR FORCING APPROVAL")
    return x,bymonth,bymonth_vpd,byday,byhour,runs

def self_test():
    assert EXPECTED_ROWS==366*48
    assert EXPECTED_505==505 and EXPECTED_36==36 and EXPECTED_VPD_HARD==1069
    t=pd.date_range("2000-01-01",periods=9,freq="30min")
    x=pd.DataFrame({"native_dt":t,
        "flag":[True,True,False,True,True,True,False,False,True]})
    marked=x.loc[x["flag"]].copy()
    ids=(marked["native_dt"].diff()!=pd.Timedelta(minutes=30)).cumsum()
    assert marked.groupby(ids).size().tolist()==[2,3,1]
    assert THRESHOLD_C==8.0
    print("STAGE81 SELF-TEST PASS | full-year 17568 native HH and VPD-independent temperature-residual episodes")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    opt=p.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","audit"):
        opt.add_argument("--"+mode,action="store_true")
    a=p.parse_args()
    if a.self_test:
        return self_test()
    parent=load_parent()
    proof,original_summary,mod80,mod78,native=inputs(parent)
    if a.check:
        print("STAGE81 CHECK PASS | Stage80 operator report SHA, Stage79/78/77/74 science, Stage49 original FLUXNET and NOAA source verified; no network/writes")
        return
    observed=all_year_pairs(mod80,mod78,native)
    full,month,month_vpd,day,hour,runs=calculate(observed)
    dest=REPORTS/("stage81_Ho1_2000_full_year_QC0_NOAA_temperature_regimes_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Original native source T regime only: no historical clock or forcing approval.\n")
    outputs={}
    for name,frame in {
       "17568_original_Ho1_2000_full_year_source_HH_NOAA_QC0_temperature.csv":full,
       "2000_source_month_T_QC0_NOAA_residual_population.csv":month,
       "2000_source_month_VPD_hard_vs_nonhard_QC0_temperature.csv":month_vpd,
       "2000_source_daily_T_QC0_NOAA_residual_population.csv":day,
       "2000_source_month_3hour_VPD_hard_nonhard_temperature.csv":hour,
       "2000_source_contiguous_QC0_NOAA_temperature_residual_GT8C_runs.csv":runs
    }.items():
        dst=dest/name;frame.to_csv(dst,index=False);outputs[name]=sha(dst)
    for filename,digest in proof["outputs_SHA256"].items():
        if sha(PREVIOUS/filename)!=digest:
            raise ValueError("Upstream Stage80 original source changed mid-audit")
    manifest={
      "schema":"STAGE81_HO1_2000_ORIGINAL_NATIVE_QC0_FULL_YEAR_NOAA_T_REGIMES_v1",
      "full_year_original_source_HH":EXPECTED_ROWS,
      "source_selection_VPD_independent":True,
      "original_VPD_hard_2000_HH":EXPECTED_VPD_HARD,
      "original_505_QC0_CDS_Tdiff_event_HH":EXPECTED_505,
      "original_36_VPD_selected_episodes":EXPECTED_36,
      "original_505_source_QC_NOAA_pairs":498,
      "original_505_source_QC_unique_NOAA_reports":306,
      "full_year_derived_NOAA_plus8C_episodes":int(runs[
         "temperature_residual_regime"].eq(
          "SOURCE_QC0_HO1_COLDER_THAN_NOAA_GT8C").sum()),
      "noaa_ground_station_not_forest_canopy_ground_truth":True,
      "annual_air_temperature_residual_cutoff_diagnostic_only":True,
      "historical_site_BIF_UTC_offset_effectiveness_approved":False,
      "all_previous_16874_source_hard_HOLDs_unchanged":True,
      "15199_original_humidity_numerical_candidates_untouched":True,
      "1675_original_temperature_QC_and_Tdelta_HOLDs_untouched":True,
      "prior_stage64_9389_independent_humidity_candidates_untouched":True,
      "original_tower_T_replacement_approved":False,
      "approved_for_DATM":False,
      "source_SHA256":{
         "stage80_script_git_blob":PARENT_BLOB,
         "stage80_operator_manifest":sha(
           PREVIOUS/"stage80_source_science_manifest.json"),
         "stage80_operator_summary":sha(
           PREVIOUS/"35_original_QC0_episode_2h_boundary_and_T_shift_review.csv"),
         "NOAA_archived_GHCNh_2000_SHA256":NOAA_SHA},
      "outputs_SHA256":outputs,
      "no_original_FLUXNET_NOAA_CDS_NetCDF_DATM_CIME_Slurm_edits":True}
    (dest/"stage81_source_science_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE81 AUDIT PASS | source-pinned full-year Ho1 2000 measured QC0 air-T and NOAA residual regimes independent of VPD selection")
    print("REPORT",dest)
    print("NO ORIGINAL EC, NOAA, CDS, STAGE49-80, NETCDF FORCING, DATM, CIME OR SLURM WRITES")
if __name__=="__main__":
    main()

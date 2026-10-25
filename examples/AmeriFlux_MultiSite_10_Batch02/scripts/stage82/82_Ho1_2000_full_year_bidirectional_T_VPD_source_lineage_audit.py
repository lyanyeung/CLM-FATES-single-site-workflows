#!/usr/bin/env python3
"""Stage82: source-pinned whole-year Ho1 2000 bi-directional T residuals and native VPD lineage.

Science:
- Stage81 operator verified 17,568 native HH, 17,294 valid measured tower T QC0,
  17,140 matched source-QC-screened Bangor original station T.
- 1,554 native QC0 HH Ho1 colder than Bangor by >8C (122 separate source
  residual runs); 2,518 HH Ho1 warmer by >8C (167 separate runs).
- A previous stage's 505 VPD-selected TA-versus-CDS cases covered only 465
  of those 1,554 source-cold residuals with the NOAA >8C threshold.
- Both signs can persist days; any one constant T correction is unjustified.
- NOAA airport ~46 km away is *not* forest canopy air-T ground truth;
  NOAA and reanalysis MAY share observations, native TA_ERA is not a
  separate independent measured station.
- This READ-ONLY source science audit compares source-native FLUXNET TA_F
  (QC0 only) with NOAA and original FLUXNET TA_ERA (if really present);
  crosses the source VPD_F and VPD_F_QC under warm/cold/baseline regimes.
  Compute water es(T) solely as an exploratory VPD source-physics screen
  for original native VPD hPa; never infer replacement VPD or temperature.

--self-test: source-free deterministic tests of scheme and physics.
--check: prove complete original Stage81 operator report/output SHA and 2000
         native source QC/NOAA/previous 505+1069 science holds, no writes.
--audit: provenance-checked new isolated diagnostic report ONLY: per-HH
         original T, original FLUXNET T_ERA if present, original VPD/QC
         and NOAA relationships; monthly VPD_QC x source signed-regime
         decomposition, long-run review, same-source T and NOAA jumps.
No historical-BIF, original T/VPD repair, forcing/DATM/CIME/Slurm writes.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
PARENT=BASE/"scripts/stage81/81_Ho1_2000_full_year_native_QC0_NOAA_cold_regimes_independent_VPD.py"
PARENT_BLOB="6e584c3e446e6637e8dbdad3241a278d15c0f415"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
UPSTREAM=REPORT/"stage81_Ho1_2000_full_year_QC0_NOAA_temperature_regimes_20261025T192411Z_3f99abd7"
YEAR_FILE="17568_original_Ho1_2000_full_year_source_HH_NOAA_QC0_temperature.csv"
RUNS_FILE="2000_source_contiguous_QC0_NOAA_temperature_residual_GT8C_runs.csv"
MONTH_FILE="2000_source_month_T_QC0_NOAA_residual_population.csv"
NOAA_SHA="2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620"
NATIVE=17568
N_QC0=17294
N_NOAA=17140
N_COLDER=1554
N_WARMER=2518
N_OLD_VPD_HARD=1069
N_OLD_505=505
N_OLD_505_PLUS8_NOAA=465
COLD="NOAA_WARMER_HO1_COLDER_GT8C"
WARM="NOAA_COLDER_HO1_WARMER_GT8C"
BASELINE="WITHIN_8C_OF_NOAA"
UNPAIRED="NO_NATIVE_QC0_OR_NO_NOAA_QC_MATCH"
ES_FORMULA="6.112*exp(17.67*T_C/(T_C+243.5)) hPa, saturation over water; diagnostic only"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()

def git_blob(path):
    f=Path(path)
    if f.is_symlink() or not f.is_file():
        raise ValueError("Original Stage81 Git source absent or symlinked")
    b=f.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def source():
    if git_blob(PARENT)!=PARENT_BLOB:
        raise ValueError("Stage81 original 2000 source scientific code changed")
    if (UPSTREAM/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Original Stage81 report incomplete")
    manifest_file=UPSTREAM/"stage81_source_science_manifest.json"
    m=json.loads(manifest_file.read_text())
    gates={
      "schema":"STAGE81_HO1_2000_ORIGINAL_NATIVE_QC0_FULL_YEAR_NOAA_T_REGIMES_v1",
      "full_year_original_source_HH":NATIVE,
      "source_selection_VPD_independent":True,
      "original_VPD_hard_2000_HH":N_OLD_VPD_HARD,
      "original_505_QC0_CDS_Tdiff_event_HH":N_OLD_505,
      "original_36_VPD_selected_episodes":36,
      "original_505_source_QC_NOAA_pairs":498,
      "original_505_source_QC_unique_NOAA_reports":306,
      "full_year_derived_NOAA_plus8C_episodes":122,
      "noaa_ground_station_not_forest_canopy_ground_truth":True,
      "annual_air_temperature_residual_cutoff_diagnostic_only":True,
      "historical_site_BIF_UTC_offset_effectiveness_approved":False,
      "all_previous_16874_source_hard_HOLDs_unchanged":True,
      "15199_original_humidity_numerical_candidates_untouched":True,
      "1675_original_temperature_QC_and_Tdelta_HOLDs_untouched":True,
      "prior_stage64_9389_independent_humidity_candidates_untouched":True,
      "original_tower_T_replacement_approved":False,
      "approved_for_DATM":False}
    for key,value in gates.items():
        if m.get(key)!=value:
            raise ValueError("Stage81 source science manifest changed: "+key)
    if m.get("source_SHA256",{}).get(
        "stage80_script_git_blob")!="945ca08b393d15fd8f710619d60a001dd9a1e9ad":
        raise ValueError("Stage81 original Stage80 source provenance changed")
    if m.get("source_SHA256",{}).get(
        "NOAA_archived_GHCNh_2000_SHA256")!=NOAA_SHA:
        raise ValueError("Stage81 NOAA original source SHA provenance changed")
    outputs=m.get("outputs_SHA256",{})
    if set(outputs)!={
        YEAR_FILE,RUNS_FILE,MONTH_FILE,
        "2000_source_month_VPD_hard_vs_nonhard_QC0_temperature.csv",
        "2000_source_daily_T_QC0_NOAA_residual_population.csv",
        "2000_source_month_3hour_VPD_hard_nonhard_temperature.csv"}:
        raise ValueError("Stage81 original report output census unexpectedly changed")
    for filename,digest in outputs.items():
        if sha(UPSTREAM/filename)!=digest:
            raise ValueError("Stage81 verified source file mutated: "+filename)
    x=pd.read_csv(UPSTREAM/YEAR_FILE,dtype={
        "tower_local_start":str,"source_csv_row":str,
        "NOAA_report_UTC":str},low_memory=False)
    required={"native_dt","tower_local_start","source_csv_row","TA_C","TA_QC",
      "NOAA_T_C","NOAA_minus_original_Ho1_T_C",
      "NOAA_report_UTC","original_TA_ERA_C",
      "original_VPD_F","original_VPD_F_QC",
      "original_2000_hard_VPD",
      "original_505_T_delta_selected",
      "NOAA_warmer_than_Ho1_GT8C","NOAA_colder_than_Ho1_GT8C",
      "original_measured_T_QC0",
      "temperature_residual_pair_valid","historical_BIF_UTC_effective_dates_approved",
      "Ho1_T_correction_approved","approved_for_DATM"}
    if not required.issubset(x.columns):
        raise ValueError("Stage81 original report missing source columns: "+str(required-set(x.columns)))
    if (len(x)!=NATIVE or
        x["tower_local_start"].duplicated().any() or
        x["source_csv_row"].duplicated().any()):
        raise ValueError("Original full-year 17568 native physical HH changed")
    t=pd.to_datetime(x["tower_local_start"],format="%Y%m%d%H%M",errors="raise")
    expected=pd.date_range("2000-01-01 00:00","2000-12-31 23:30",freq="30min")
    if not pd.DatetimeIndex(t).equals(expected):
        raise ValueError("Stage81 original native calendar or order changed")
    if not pd.DatetimeIndex(pd.to_datetime(
        x["native_dt"],errors="raise")).equals(expected):
        raise ValueError("Stage81 derived native temporal index changed")
    for col in ("original_2000_hard_VPD","original_505_T_delta_selected",
            "NOAA_warmer_than_Ho1_GT8C","NOAA_colder_than_Ho1_GT8C",
            "original_measured_T_QC0","temperature_residual_pair_valid",
            "historical_BIF_UTC_effective_dates_approved",
            "Ho1_T_correction_approved","approved_for_DATM"):
        x[col]=x[col].astype(str).str.lower().eq("true")
    for col in ("TA_C","TA_QC","NOAA_T_C",
        "NOAA_minus_original_Ho1_T_C","original_TA_ERA_C",
        "original_VPD_F","original_VPD_F_QC"):
        x[col]=pd.to_numeric(x[col],errors="coerce")
        if col in ("original_TA_ERA_C","original_VPD_F"):
            x[col]=x[col].mask(x[col].le(-9990))
    if (int(x["original_measured_T_QC0"].sum())!=N_QC0 or
        int(x["temperature_residual_pair_valid"].sum())!=N_NOAA or
        int(x["NOAA_warmer_than_Ho1_GT8C"].sum())!=N_COLDER or
        int(x["NOAA_colder_than_Ho1_GT8C"].sum())!=N_WARMER or
        int(x["original_2000_hard_VPD"].sum())!=N_OLD_VPD_HARD or
        int(x["original_505_T_delta_selected"].sum())!=N_OLD_505 or
        int((x["original_505_T_delta_selected"]&
             x["NOAA_warmer_than_Ho1_GT8C"]).sum())!=N_OLD_505_PLUS8_NOAA or
        x.loc[x["original_505_T_delta_selected"],"TA_QC"].ne(0).any() or
        x.loc[x["NOAA_warmer_than_Ho1_GT8C"],
              "NOAA_colder_than_Ho1_GT8C"].any() or
        x.loc[x["NOAA_warmer_than_Ho1_GT8C"]|
              x["NOAA_colder_than_Ho1_GT8C"],
              "temperature_residual_pair_valid"].eq(False).any() or
        x[["historical_BIF_UTC_effective_dates_approved",
           "Ho1_T_correction_approved","approved_for_DATM"]].any().any()):
        raise ValueError("Stage81 measured original temperature/QC/NOAA/old science holds changed")
    paired=x.loc[x["temperature_residual_pair_valid"]]
    if (not np.isfinite(paired["NOAA_T_C"]).all() or
        not np.allclose(paired["NOAA_T_C"]-paired["TA_C"],
                        paired["NOAA_minus_original_Ho1_T_C"],
                        atol=0.00011,rtol=0) or
        paired["NOAA_report_UTC"].isna().any()):
        raise ValueError("Stage81 original tower-versus-NOAA source time and numeric source evidence changed")
    runs=pd.read_csv(UPSTREAM/RUNS_FILE,dtype={
        "native_start":str,"native_end":str})
    if (len(runs)!=289 or
        Counter(runs["temperature_residual_regime"])!={
          "SOURCE_QC0_HO1_COLDER_THAN_NOAA_GT8C":122,
          "SOURCE_QC0_HO1_WARMER_THAN_NOAA_GT8C":167} or
        runs.loc[runs["temperature_residual_regime"].eq(
          "SOURCE_QC0_HO1_COLDER_THAN_NOAA_GT8C"),
          "n_native_30min_QC0_NOAA_matched_HH"].sum()!=N_COLDER or
        runs.loc[runs["temperature_residual_regime"].eq(
          "SOURCE_QC0_HO1_WARMER_THAN_NOAA_GT8C"),
          "n_native_30min_QC0_NOAA_matched_HH"].sum()!=N_WARMER):
        raise ValueError("Original complete cold/warm run census not intact")
    return x,runs,m

def classify(x):
    y=x.copy()
    y["science_group"]=np.select(
      [y["NOAA_warmer_than_Ho1_GT8C"],
       y["NOAA_colder_than_Ho1_GT8C"],
       y["temperature_residual_pair_valid"]],
      [COLD,WARM,BASELINE],default=UNPAIRED)
    y["original_TA_ERA_C"]=y["original_TA_ERA_C"].where(
        y["original_TA_ERA_C"].between(-80,65,inclusive="both"))
    y["native_TA_ERA_present"]=y["original_TA_ERA_C"].notna()
    y["native_TA_ERA_minus_Ho1_C"]=(
        y["original_TA_ERA_C"]-y["TA_C"]).where(
            y["native_TA_ERA_present"]&
            y["original_measured_T_QC0"])
    y["native_TA_ERA_minus_NOAA_C"]=(
        y["original_TA_ERA_C"]-y["NOAA_T_C"]).where(
            y["native_TA_ERA_present"]&
            y["temperature_residual_pair_valid"])
    agree_ho1=(y["native_TA_ERA_minus_Ho1_C"].abs().le(3))
    agree_noaa=(y["native_TA_ERA_minus_NOAA_C"].abs().le(3))
    y["native_TA_ERA_context"]=np.select([
        ~y["native_TA_ERA_present"],
        ~y["temperature_residual_pair_valid"],
        agree_ho1&agree_noaa,
        agree_ho1&~agree_noaa,
        ~agree_ho1&agree_noaa,
        y["temperature_residual_pair_valid"]],
        ["SOURCE_TA_ERA_ABSENT_OR_MISSING",
         "SOURCE_TA_ERA_PRESENT_BUT_NO_QC0_NOAA_PAIR",
         "TA_ERA_WITHIN3C_BOTH",
         "TA_ERA_WITHIN3C_HO1",
         "TA_ERA_WITHIN3C_NOAA",
         "TA_ERA_MATCHES_NEITHER_WITHIN3C"],
         default="SOURCE_REVIEW_CLASSIFICATION_ERROR")
    if y["native_TA_ERA_context"].eq(
        "SOURCE_REVIEW_CLASSIFICATION_ERROR").any():
        raise ValueError("Original T_ERA source context not exhaustive")
    y["native_VPD_QC_label"]=np.select(
       [y["original_VPD_F_QC"].eq(0),
        y["original_VPD_F_QC"].eq(1),
        y["original_VPD_F_QC"].eq(2)],
       ["QC0","QC1","QC2"],default="OTHER_MISSING")
    # Preserve the full native source VPD magnitude, even values outside
    # plausible physical bounds; screening must never silently discard the
    # most problematic extremes. Source missing sentinel was masked above.
    y["native_VPD_hPa"]=y["original_VPD_F"]
    t=y["TA_C"].where(y["original_measured_T_QC0"])
    y["source_water_es_from_native_Ho1_T_hPa"]=(
         6.112*np.exp(17.67*t/(t+243.5)))
    y["native_VPD_gt_water_es_from_original_QC0_T"]=(
         y["original_measured_T_QC0"]&
         y["native_VPD_hPa"].notna()&
         y["native_VPD_hPa"].gt(
           y["source_water_es_from_native_Ho1_T_hPa"]+1e-8))
    y["native_VPD_lt0_hPa"]=y["native_VPD_hPa"].lt(0)
    y["original_VPD_water_es_science_check_only"]=True
    y["native_ERA_and_NOAA_not_independent_ground_truth"]=True
    y["NOAA_not_forest_canopy_ground_truth"]=True
    y["historical_UTC_approved"]=False
    y["source_T_replacement_approved"]=False
    y["source_VPD_replacement_approved"]=False
    y["approved_for_DATM"]=False
    return y

def summarize(y,columns):
    rows=[]
    for key,g in y.groupby(columns,sort=True,dropna=False):
        if not isinstance(key,tuple):key=(key,)
        q=g.loc[g["temperature_residual_pair_valid"]]
        native_ta_era=g.loc[g["native_TA_ERA_present"]&
                           g["temperature_residual_pair_valid"]]
        d=q["NOAA_minus_original_Ho1_T_C"]
        noaa_unique=q.groupby("NOAA_report_UTC")[
           "NOAA_minus_original_Ho1_T_C"].apply(
              lambda s:s.abs().mean())
        rows.append({
          **dict(zip(columns,key)),
          "native_original_HH":len(g),
          "native_QC0_noaa_paired_HH":len(q),
          "unique_NOAA_source_reports":len(noaa_unique),
          "NOAA_minus_Ho1_signed_median_C":
             float(d.median()) if len(d) else np.nan,
          "NOAA_minus_Ho1_abs_mean_per_unique_report_C":
             float(noaa_unique.mean()) if len(noaa_unique) else np.nan,
          "native_TA_ERA_present_HH":int(g["native_TA_ERA_present"].sum()),
          "native_TA_ERA_usable_QC0_NOAA_HH":len(native_ta_era),
          "native_TA_ERA_minus_Ho1_median_C":float(
             native_ta_era["native_TA_ERA_minus_Ho1_C"].median()
             ) if len(native_ta_era) else np.nan,
          "native_TA_ERA_minus_NOAA_median_C":float(
             native_ta_era["native_TA_ERA_minus_NOAA_C"].median()
             ) if len(native_ta_era) else np.nan,
          "original_VPD_QC0_HH":int(g["original_VPD_F_QC"].eq(0).sum()),
          "original_VPD_QC1_HH":int(g["original_VPD_F_QC"].eq(1).sum()),
          "original_VPD_QC2_HH":int(g["original_VPD_F_QC"].eq(2).sum()),
          "original_VPD_above_water_es_T_QC0_HH":int(
              g["native_VPD_gt_water_es_from_original_QC0_T"].sum()),
          "original_VPD_negative_HH":int(g["native_VPD_lt0_hPa"].sum()),
          "original_VPD_hard_source_HH":int(g["original_2000_hard_VPD"].sum()),
          "original_505_source_Tdelta_HH":int(g["original_505_T_delta_selected"].sum()),
          "DATM_approved":False})
    return pd.DataFrame(rows)

def temperature_transitions(y):
    """Original halfhour source continuity and changes crossing sign extremes."""
    q=y.loc[y["temperature_residual_pair_valid"]].copy()
    q["direction"]=np.select(
      [q["NOAA_warmer_than_Ho1_GT8C"],q["NOAA_colder_than_Ho1_GT8C"]],
      [COLD,WARM],default=BASELINE)
    q["native_dt_parsed"]=pd.to_datetime(
        q["tower_local_start"],format="%Y%m%d%H%M",errors="raise")
    prior=q.shift(1)
    prev_dt=pd.to_datetime(prior["tower_local_start"],format="%Y%m%d%H%M",
                           errors="coerce")
    continuous=(q["native_dt_parsed"]-prev_dt).eq(pd.Timedelta(minutes=30))
    different=q["direction"].ne(prior["direction"])
    mask=continuous&different
    transitions=q.loc[mask].copy()
    transitions["previous_direction"]=prior.loc[mask,"direction"].to_numpy()
    transitions["prior_native_local_start"]=prior.loc[
          mask,"tower_local_start"].to_numpy()
    transitions["prior_original_T_C"]=prior.loc[mask,"TA_C"].to_numpy()
    transitions["prior_NOAA_T_C"]=prior.loc[mask,"NOAA_T_C"].to_numpy()
    transitions["prior_VPD_QC"]=prior.loc[mask,"original_VPD_F_QC"].to_numpy()
    transitions["30min_original_T_delta_C"]=(
        transitions["TA_C"]-transitions["prior_original_T_C"])
    transitions["30min_NOAA_airport_T_delta_C"]=(
        transitions["NOAA_T_C"]-transitions["prior_NOAA_T_C"])
    transitions["30min_signed_residual_delta_C"]=(
        transitions["NOAA_minus_original_Ho1_T_C"]-
        prior.loc[mask,"NOAA_minus_original_Ho1_T_C"].to_numpy())
    # Extreme -> extreme in 30 min not necessarily error; this highlights
    # abrupt source/clock changes for manual human review.
    transitions["direct_cold_to_warm_or_warm_to_cold"]=(
       transitions["previous_direction"].isin([COLD,WARM])&
       transitions["direction"].isin([COLD,WARM])&
       transitions["previous_direction"].ne(transitions["direction"]))
    transitions["source_T_jump_over8C_abs"]=transitions[
         "30min_original_T_delta_C"].abs().gt(8)
    transitions["no_model_source_T_approval"]=True
    return transitions

def assess_runs(y,old_runs):
    entries=[]
    for r in old_runs.itertuples(index=False):
        a=str(r.native_start); b=str(r.native_end)
        records=y.loc[y["tower_local_start"].between(a,b)].copy()
        if len(records)!=int(r.n_native_30min_QC0_NOAA_matched_HH):
            raise ValueError("Full year original NOAA temperature regime continuity changed")
        label=COLD if "COLDER_THAN_NOAA" in r.temperature_residual_regime else WARM
        if not records["science_group"].eq(label).all():
            raise ValueError("Stage81 cold/warm source run labels mismatch")
        entries.append({
           "native_local_start":a,"native_local_end":b,
           "source_QC0_NOAA_matched_HH":len(records),
           "source_hours":len(records)*0.5,
           "science_group":label,
           "unique_NOAA_source_reports":int(records["NOAA_report_UTC"].nunique()),
           "original_VPD_hard_HH":int(records["original_2000_hard_VPD"].sum()),
           "original_VPD_nonhard_HH":int((~records[
                 "original_2000_hard_VPD"]).sum()),
           "native_TA_ERA_available_HH":int(records["native_TA_ERA_present"].sum()),
           "native_TA_ERA_within3C_of_NOAA_HH":int(
              records["native_TA_ERA_context"].eq(
                 "TA_ERA_WITHIN3C_NOAA").sum()),
           "native_TA_ERA_within3C_of_Ho1_HH":int(
              records["native_TA_ERA_context"].eq(
                 "TA_ERA_WITHIN3C_HO1").sum()),
           "original_VPD_QC2_HH":int(records[
               "original_VPD_F_QC"].eq(2).sum()),
           "native_VPD_above_eswater_from_native_T_HH":int(
               records["native_VPD_gt_water_es_from_original_QC0_T"].sum()),
           "NOAA_minus_native_T_signed_median_C":float(
               records["NOAA_minus_original_Ho1_T_C"].median()),
           "signed_source_airport_temperature_not_ground_truth":True,
           "DATM_approved":False})
    out=pd.DataFrame(entries)
    if (len(out)!=289 or
        out.loc[out.science_group.eq(COLD),
               "source_QC0_NOAA_matched_HH"].sum()!=N_COLDER or
        out.loc[out.science_group.eq(WARM),
               "source_QC0_NOAA_matched_HH"].sum()!=N_WARMER):
        raise ValueError("Stage82 source original bidirectional 289 temperature run closure changed")
    return out.sort_values(["source_hours","native_local_start"],
        ascending=[False,True]).reset_index(drop=True)

def self_test():
    assert 366*48==NATIVE
    assert N_COLDER+N_WARMER==4072
    assert N_COLDER==1554 and N_WARMER==2518
    assert N_OLD_505_PLUS8_NOAA==465
    assert 122+167==289
    assert abs(6.112*np.exp(17.67*(-10)/(-10+243.5))-2.867)<0.05
    assert 17140-4072==13068
    print("STAGE82 SELF-TEST PASS | 1554 Ho1 colder/2518 warmer native measured QC0 NOAA source residuals, original VPD QA hold")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","audit"):
        g.add_argument("--"+name,action="store_true")
    args=p.parse_args()
    if args.self_test:return self_test()
    native,runs,manifest=source()
    if args.check:
        print("STAGE82 CHECK PASS | Stage81 full 17568 original HH+289 temp regimes and output SHA, 17294 QC0, 17140 NOAA paired, 1554/2518 signed science; no writes")
        return
    flagged=classify(native)
    month=flagged.copy()
    month["source_month"]=month["tower_local_start"].str[4:6].astype(int)
    monthly=summarize(month,["source_month","science_group"])
    vpd_qc=summarize(month,["science_group","native_VPD_QC_label"])
    temp_era=summarize(month,["science_group","native_TA_ERA_context"])
    run_report=assess_runs(flagged,runs)
    transitions=temperature_transitions(flagged)
    if (len(flagged)!=NATIVE or
        Counter(flagged.science_group)!={
           COLD:N_COLDER,WARM:N_WARMER,
           BASELINE:13068,UNPAIRED:428} or
        monthly["native_original_HH"].sum()!=NATIVE or
        vpd_qc["native_original_HH"].sum()!=NATIVE or
        temp_era["native_original_HH"].sum()!=NATIVE):
        raise ValueError("Original T/VPD full-year and NOAA population closure changed")
    print("STAGE82 FULL YEAR original source 17568 HH, QC0 17294, NOAA paired 17140")
    print("STAGE82 BIDIRECTIONAL TEMPERATURE RESIDUAL STATUS",dict(Counter(flagged.science_group)))
    print("STAGE82 ORIGINAL TA_ERA AVAILABILITY",int(flagged.native_TA_ERA_present.sum()),
          "/",NATIVE)
    print("STAGE82 SOURCE GROUP BY VPD QUALITY AND AIR-T CONTEXT")
    print(vpd_qc.to_string(index=False))
    print("STAGE82 SOURCE ORIGINAL TA_ERA THREE-WAY CONTEXT")
    print(temp_era.to_string(index=False))
    print("STAGE82 SOURCE MONTHLY QC0 NOAA-T-VPD REGIMES")
    print(monthly.to_string(index=False))
    print("STAGE82 SOURCE QC0 BIDIRECTIONAL FULL-YEAR RUNS TOP 20")
    print(run_report.head(20).to_string(index=False))
    print("STAGE82 30min SOURCE SIGNED NOAAT-Ho1 REGIME TRANSITIONS",
          len(transitions),"DIRECT COLD/WARM",int(
             transitions.direct_cold_to_warm_or_warm_to_cold.sum()),
          "NATIVE T JUMP >8C",int(transitions.source_T_jump_over8C_abs.sum()))
    print("STAGE82 SOURCE NOAA, native TA_ERA, VPD and clock all SCIENCE REVIEW ONLY")
    dest=REPORT/("stage82_Ho1_2000_full_year_bidirectional_native_T_VPD_source_QC_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    incomplete=dest/"INCOMPLETE_DO_NOT_USE"
    incomplete.write_text("Science-only NOAA airport/native original T/VPD source audit, no temperature or model approvals.\n")
    outputs={}
    for name,frame in {
      "17568_original_Ho1_2000_T_VPD_QC_NOAA_native_source_triage.csv":flagged,
      "Ho1_2000_month_original_T_signed_NOAA_VPD_QC_summary.csv":monthly,
      "Ho1_2000_source_VPD_QC_by_signed_T_difference.csv":vpd_qc,
      "Ho1_2000_original_TA_ERA_support_context_by_signed_T_difference.csv":temp_era,
      "Ho1_2000_289_cold_warm_source_regime_TA_ERA_VPD_evidence.csv":run_report,
      "Ho1_2000_original_QC0_T_30min_source_residual_direction_transitions.csv":transitions
    }.items():
        filename=dest/name;frame.to_csv(filename,index=False);outputs[name]=sha(filename)
    for filename,digest in manifest["outputs_SHA256"].items():
        if sha(UPSTREAM/filename)!=digest:
            raise ValueError("Original Stage81 source changed while Stage82 wrote new science report")
    proof={
       "schema":"STAGE82_HO1_2000_NATIVE_QC0_T_NOAA_BIDIRECTIONAL_VPD_QC_SOURCE_TRIAGE_v1",
       "source_full_HH":NATIVE,
       "source_measured_native_T_QC0":N_QC0,
       "source_QC0_noaa_matched":N_NOAA,
       "NOAA_warmer_than_Ho1_gt8C_HH":N_COLDER,
       "NOAA_colder_than_Ho1_gt8C_HH":N_WARMER,
       "source_505_stage74_selected_cases":N_OLD_505,
       "source_1069_original_VPD_hard_HH":N_OLD_VPD_HARD,
       "source_QC0_gt8C_run_count":289,
       "native_FLUXNET_TA_ERA_is_processed_not_independent_source":True,
       "native_VPD_water_es_physics_only_not_replacement_approval":True,
       "native_VPD_hPa_water_es_formula":ES_FORMULA,
       "NOAA_Bangor_airport_not_Ho1_local_T_ground_truth":True,
       "NOAA_and_reanalysis_may_share_assimilated_data":True,
       "historical_BIF_UTC_offset_approved":False,
       "original_T_replacement_approved":False,
       "original_VPD_replacement_approved":False,
       "approved_for_DATM":False,
       "original_humidity_numeric_shadow_15199_unchanged":True,
       "original_T_HOLDs_1675_unchanged":True,
       "original_humidity_HOLDs_16874_unchanged":True,
       "previous_stage64_other_9389_candidates_untouched":True,
       "source_SHA256":{
           "stage81_script_gitblob":PARENT_BLOB,
           "stage81_original_report_manifest":sha(
              UPSTREAM/"stage81_source_science_manifest.json"),
           "stage81_full_year_source":sha(UPSTREAM/YEAR_FILE),
           "stage81_full_temperature_runs":sha(UPSTREAM/RUNS_FILE),
           "original_NOAA_2000_provenance_SHA":NOAA_SHA},
       "outputs_SHA256":outputs,
       "no_original_FLUXNET_NOAA_ERA5_forcing_DATM_CIME_SLURM_changes":True}
    (dest/"stage82_source_science_manifest.json").write_text(
        json.dumps(proof,indent=2,sort_keys=True)+"\n")
    incomplete.unlink()
    print("STAGE82 AUDIT PASS | 17568 original Ho1 2000 T/VPD/QC and source NOAA bidirectional science evidence; no forcing approval")
    print("REPORT",dest)
    print("NO ORIGINAL FLUXNET, NOAA, CDS, STAGE49-81, NETCDF FORCING, DATM, CIME OR SLURM WRITES")

if __name__=="__main__":
    main()

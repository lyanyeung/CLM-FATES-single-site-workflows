#!/usr/bin/env python3
"""Read-only review of CH-Aws very dry *measured/QC1* VPD_F records.

Why: Stage29 edited only 77 VPD_F_QC==2, EUF_F, RH<10% values. Existing
RH25A contains another 71 VPD_F_QC==1 (good MDS gapfill) and 25 QC==0
(measured) values below 10%. Do NOT overwrite measured values or blindly
replace high-quality gapfills with reanalysis.

Compare CH-Aws site-inferred RH against cached hourly Open-Meteo ERA5 and
ERA5-Land T/Td (interpolated to local standard UTC+1, no DST). Some years
may have NO cached reference: preserve as missing, NOT zero. Does not
download data, write forcing, edit a CIME case, or submit Slurm jobs.
Only two small CSV reports under HOME are written.

FLUXNET2015 VPD_F_QC convention at half-hourly resolution:
0 measured, 1 good MDS gapfill, 2 downscaled ERA.
https://fluxnet.org/data/fluxnet2015-dataset/subset-data-product/
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing")
SOURCE = ROOT / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
OUT = Path.home() / "FLUXNET_MultiSite_11/stage33_CH_Aws_QC01_evidence"
EVENT = pd.Timestamp("2007-05-17 13:00")

def check(condition, message):
    if not condition:
        raise RuntimeError("STOP: " + message)

def sat(t):
    t = np.asarray(t, dtype=float)
    return 6.112 * np.exp(np.clip(17.67*t/(t+243.5), -100, 100))

def reference(model, year, desired):
    path = CACHE / f"{model}_{year}.json"
    if not path.is_file():
        return pd.Series(np.nan, index=desired, dtype=float)
    raw = json.loads(path.read_text())
    check(raw.get("utc_offset_seconds") == 0,
          f"{path}: expected UTC reference with zero offset")
    hourly = raw.get("hourly", {})
    for col in ("time", "temperature_2m", "dew_point_2m"):
        check(col in hourly, f"{path}: missing {col}")
    utc = pd.DatetimeIndex(pd.to_datetime(hourly["time"], errors="raise"))
    expected = pd.date_range(f"{year}-01-01",
                             f"{year}-12-31 23:00", freq="h")
    check(utc.equals(expected), f"{path}: incorrect full-year hourly timestamps")
    temp = pd.to_numeric(pd.Series(hourly["temperature_2m"]),
                         errors="coerce").to_numpy(float)
    dew = pd.to_numeric(pd.Series(hourly["dew_point_2m"]),
                        errors="coerce").to_numpy(float)
    local = pd.DataFrame({"T_air":temp, "T_dew":dew},
                         index=utc + pd.Timedelta(hours=1))
    local = (local.reindex(local.index.union(desired)).sort_index()
             .interpolate(method="time", limit=1,
                          limit_area="inside").reindex(desired))
    vals = 100*sat(local["T_dew"].to_numpy(float)) / sat(local["T_air"].to_numpy(float))
    return pd.Series(vals, index=desired)

def main():
    check(SOURCE.is_file(), f"Missing original candidate: {SOURCE}")
    fields = ["time","TA_F","VPD_F","PA_F","RH_IMPLIED_PCT",
              "VPD_F_QC","VPD_F_SOURCE","PAIR_STATUS"]
    df = pd.read_csv(SOURCE, usecols=fields, low_memory=False)
    df["time"] = pd.to_datetime(df["time"], errors="raise")
    check(len(df)==332880 and df["time"].is_unique,
          "Unexpected RH25A full-period timeline")
    df["VPD_F_QC"] = pd.to_numeric(df["VPD_F_QC"], errors="coerce")
    df["RH_IMPLIED_PCT"] = pd.to_numeric(df["RH_IMPLIED_PCT"], errors="coerce")
    df["RH_previous"] = df["RH_IMPLIED_PCT"].shift(1)
    df["RH_next"] = df["RH_IMPLIED_PCT"].shift(-1)
    df["source_previous"] = df["VPD_F_SOURCE"].shift(1)
    df["source_next"] = df["VPD_F_SOURCE"].shift(-1)

    small = df.loc[df["RH_IMPLIED_PCT"]<10].copy().sort_values("time")
    check(len(small)==173, f"Previous audit reported 173 low-RH rows, got {len(small)}")
    qc2 = small["VPD_F_QC"].eq(2) & small["VPD_F_SOURCE"].eq("EUF_F")
    check(int(qc2.sum())==77, "Stage29 QC2 cohort different from 77")
    pending = small.loc[~qc2].copy()
    check(len(pending)==96, "Expected 96 remaining <10% RH records")
    check(int(pending["VPD_F_QC"].eq(1).sum())==71
          and int(pending["VPD_F_QC"].eq(0).sum())==25,
          "Unexpected QC0/QC1 counts; inspect source schema")
    pending = pending.set_index("time")
    for model in ("era5","era5_land"):
        col = model + "_RH_pct"
        pending[col] = np.nan
        for yr in sorted(set(pending.index.year)):
            idx = pending.index[pending.index.year==yr]
            pending.loc[idx, col] = reference(model, int(yr), idx).to_numpy()
    pending["ERA_gap_pp"] = abs(pending["era5_RH_pct"]-pending["era5_land_RH_pct"])
    pending["ERA5Land_minus_input_pp"] = (pending["era5_land_RH_pct"] - pending["RH_IMPLIED_PCT"])
    pending["RH_jump_before_abs_pp"] = abs(pending["RH_IMPLIED_PCT"]-pending["RH_previous"])
    pending["RH_jump_after_abs_pp"] = abs(pending["RH_IMPLIED_PCT"]-pending["RH_next"])
    pending["is_source_seam"] = ((pending["VPD_F_SOURCE"]!=pending["source_previous"]) |
                                  (pending["VPD_F_SOURCE"]!=pending["source_next"]))
    available = pending[["era5_RH_pct","era5_land_RH_pct"]].notna().all(axis=1)
    proposed = (
        pending["VPD_F_QC"].eq(1) & available
        & pending["era5_RH_pct"].ge(30) & pending["era5_land_RH_pct"].ge(30)
        & pending["ERA_gap_pp"].le(15)
        & pending["ERA5Land_minus_input_pp"].ge(20)
    )
    # A conservative *review* classification; NOT selection for edits.
    pending["review_priority"] = "LOW_RH_NEEDS_SOURCE_REVIEW"
    pending.loc[~available, "review_priority"] = "REFERENCE_NOT_CACHED"
    pending.loc[proposed, "review_priority"] = "P2_QC1_TWO_REANALYSES_DIFFER"
    pending.loc[proposed & (pending["RH_IMPLIED_PCT"] < 1), "review_priority"] = "P1_QC1_EXTREME_RH"
    pending.loc[pending["VPD_F_QC"].eq(0), "review_priority"] = "QC0_MEASURED_REQUIRES_RAW_VALIDATION"
    pending["candidate_for_manual_review_only"] = proposed
    pending = pending.sort_values("time")

    print("=== WHO WAS OMITTED BY THE STAGE29 QC=2 SCREEN? ===")
    print(f"All RH25A RH<10%: {len(small)}")
    print(f"Already Stage29 QC2 cohort: {int(qc2.sum())}")
    print(f"Unchanged QC1 fill: {int(pending['VPD_F_QC'].eq(1).sum())}")
    print(f"Unchanged QC0 measured: {int(pending['VPD_F_QC'].eq(0).sum())}")
    print("\n=== UNCHANGED QC0/QC1 BY YEAR ===")
    print(pending.groupby([pending.index.year,"VPD_F_QC"]).size().to_string())
    print("\n=== REANALYSIS REFERENCE COVERAGE ===")
    print(pending.groupby(pending.index.year).agg(
        n=("RH_IMPLIED_PCT","size"),
        ERA5_available=("era5_RH_pct","count"),
        ERA5Land_available=("era5_land_RH_pct","count")).to_string())
    print("\n=== HIGH-PRIORITY QC1 EVIDENCE (NOT APPROVED EDITS) ===")
    print("QC1 records meeting conservative two-reanalysis review screen:", int(proposed.sum()))
    cols=["RH_IMPLIED_PCT","VPD_F_QC","VPD_F_SOURCE","RH_previous","RH_next",
          "era5_RH_pct","era5_land_RH_pct","ERA_gap_pp",
          "is_source_seam","review_priority"]
    top = pending.loc[proposed].sort_values("RH_IMPLIED_PCT").head(30)
    print(top[cols].to_string(float_format=lambda f:f"{f:.3f}"))
    print("\n=== CRITICAL MAY 17 EVENT ===")
    check(EVENT in pending.index, "Missing key QC1 event 2007-05-17 13:00")
    print(pending.loc[[EVENT],cols].to_string(float_format=lambda f:f"{f:.4f}"))
    print("\n=== MEASURED QC0 LOW-RH RECORDS: DO NOT BLINDLY REPLACE ===")
    print(pending.loc[pending["VPD_F_QC"].eq(0),cols].head(30).to_string(float_format=lambda f:f"{f:.3f}"))

    OUT.mkdir(parents=True, exist_ok=True)
    detail=OUT/"01_all_96_QC01_reanalysis_review.csv"
    group=OUT/"02_QC01_yearly_review_summary.csv"
    pending.to_csv(detail, index_label="time", float_format="%.12g")
    summary=pending.groupby([pending.index.year,"VPD_F_QC"]).agg(
        n=("RH_IMPLIED_PCT","size"),
        min_input_RH_pct=("RH_IMPLIED_PCT","min"),
        ref_ERA5=("era5_RH_pct","count"),
        ref_ERA5Land=("era5_land_RH_pct","count"),
        strong_QC1_reference=("candidate_for_manual_review_only","sum"))
    summary.to_csv(group, index_label=["year","VPD_F_QC"])
    print("\nReports:",detail,group,sep="\n")
    print("NO forcing edits, no CIME changes, no Slurm jobs.")
    print("Scientific note: RH input is not RH diagnosed at 2m by CLM.")

if __name__=="__main__":
    main()

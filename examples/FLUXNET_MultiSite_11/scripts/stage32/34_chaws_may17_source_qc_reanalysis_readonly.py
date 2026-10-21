#!/usr/bin/env python3
"""CH-Aws RH29A post-mortem Stage32: examine missing 2007-05-17 low-RH input.

Read-only: site RH25A CSV, existing Stage29 v5 2007 DATM, cached 2007
ERA5/ERA5-Land T/Td and the existing failed land log.  Writes ONLY small
CSV reports under HOME. No forcing edits, CIME changes, model or Slurm jobs.

Failure clock inferred from final history nstep may differ from exact abort.
Swiss FLUXNET timestamps are assumed local standard UTC+1 (no DST).
Reference RH is model-derived, not field validation, and ERA5/ERA5-Land
are related reanalyses (not independent observations).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

SITE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing")
SRC = SITE / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
DATM = SITE / "datm_11_stage29_all77_rh_sensitivity_v5/CH-Aws_DATM_2007.nc"
CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
RUN = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/CH-Aws_FATES_SPINUP1000_RH29A/run")
OUT = Path.home() / "FLUXNET_MultiSite_11/stage32_CH_Aws_May17_source_and_reference"
EVENT = pd.Timestamp("2007-05-17 13:00:00")
MODELS = ("era5", "era5_land")
SOURCE_COLS = ("time", "TA_F", "PA_F", "VPD_F", "VPD_F_SOURCE",
               "VPD_F_QC", "RH_IMPLIED_PCT", "PAIR_STATUS",
               "RH_LAND_TRIAL_FLAG", "STAGE21_RH_TRIAL_FLAG",
               "STAGE25_RH_TRIAL_FLAG", "TA_F_SOURCE", "TA_F_QC",
               "PA_F_SOURCE", "PA_F_QC")

def check(ok, msg):
    if not ok:
        raise RuntimeError("STOP: " + msg)

def sat(tc):
    tc = np.asarray(tc, dtype=float)
    return 6.112 * np.exp(np.clip(17.67 * tc / (tc + 243.5), -100, 100))

def load_reference(model, target):
    f = CACHE / f"{model}_2007.json"
    check(f.is_file(), f"Missing 2007 cached reference: {f}")
    raw = json.loads(f.read_text())
    check(raw.get("utc_offset_seconds") == 0,
          f"{model}: reference not UTC, check timing")
    hours = raw.get("hourly", {})
    for key in ("time", "temperature_2m", "dew_point_2m"):
        check(key in hours and len(hours[key]) == 8760,
              f"{model}: missing/invalid hourly {key}")
    utc = pd.DatetimeIndex(pd.to_datetime(hours["time"], errors="raise"))
    required = pd.date_range("2007-01-01", "2007-12-31 23:00", freq="h")
    check(utc.equals(required), f"{model}: reference timestamps changed")
    tab = pd.DataFrame({
        "T": pd.to_numeric(pd.Series(hours["temperature_2m"]),
                           errors="coerce").to_numpy(float),
        "Td": pd.to_numeric(pd.Series(hours["dew_point_2m"]),
                            errors="coerce").to_numpy(float),
    }, index=utc + pd.Timedelta(hours=1))
    interpolated = (tab.reindex(tab.index.union(target)).sort_index()
                    .interpolate(method="time", limit=1,
                                 limit_area="inside")
                    .reindex(target))
    check(interpolated.notna().all().all(),
          f"{model}: incomplete T/Td reference in target window")
    return 100 * sat(interpolated["Td"].to_numpy()) / sat(interpolated["T"].to_numpy())

def main():
    check(SRC.is_file() and DATM.is_file(), "Candidate source or Stage29 2007 DATM missing")
    source = pd.read_csv(SRC, usecols=lambda s: s in SOURCE_COLS, low_memory=False)
    check(set(SOURCE_COLS[:7]).issubset(source.columns), "Missing required source columns")
    source["time"] = pd.to_datetime(source["time"], errors="raise")
    check(source["time"].is_unique, "Duplicate candidate timestamps")
    source["VPD_F_QC"] = pd.to_numeric(source["VPD_F_QC"], errors="coerce")
    source["RH_IMPLIED_PCT"] = pd.to_numeric(source["RH_IMPLIED_PCT"], errors="coerce")
    source = source.set_index("time").sort_index()

    with Dataset(DATM) as nc:
        times = pd.DatetimeIndex([
            str(t)[:19] for t in num2date(
                nc["time"][:], nc["time"].units,
                calendar=getattr(nc["time"], "calendar", "noleap"))
        ])
        check(len(times) == 17520 and times.is_unique,
              "2007 Stage29 DATM timing not expected")
        tbot = np.asarray(nc["TBOT"][:, 0, 0], dtype=float) - 273.15
        pres = np.asarray(nc["PSRF"][:, 0, 0], dtype=float)
        hum = np.asarray(nc["QBOT"][:, 0, 0], dtype=float)
        zbot = np.asarray(nc["ZBOT"][:, 0, 0], dtype=float)
        wind = np.asarray(nc["WIND"][:, 0, 0], dtype=float)
    ea = hum * pres / (0.622 + 0.378 * hum)
    input_rh = 100 * ea / (100 * sat(tbot))
    actual = pd.DataFrame({
        "time": times, "QBOT_v5_kgkg": hum, "TBOT_v5_C": tbot,
        "PSRF_v5_Pa": pres, "RH_v5_pct": input_rh,
        "ZBOT_v5_m": zbot, "WIND_v5_ms": wind
    }).set_index("time")
    start = EVENT - pd.Timedelta(days=2)
    end = EVENT + pd.Timedelta(days=2)
    span = actual.loc[start:end].join(source, how="left", validate="one_to_one")
    check(EVENT in span.index, "Suspected event not found")
    check(span["VPD_F_SOURCE"].notna().all(), "Source metadata missing in event window")
    for model in MODELS:
        span[f"{model}_RH_pct"] = load_reference(model, span.index)
    span["v5_minus_era5_land_pp"] = span["RH_v5_pct"] - span["era5_land_RH_pct"]
    span["era5_minus_land_abs_pp"] = abs(span["era5_RH_pct"] - span["era5_land_RH_pct"])
    # Classify only the original Stage29 selection condition.
    span["would_match_stage29_original_screen"] = (
        span["VPD_F_SOURCE"].eq("EUF_F") &
        span["VPD_F_QC"].eq(2) &
        span["RH_IMPLIED_PCT"].lt(10))
    crit = span.loc[EVENT]
    context = span.loc[EVENT-pd.Timedelta(hours=4):
                       EVENT+pd.Timedelta(hours=3)]
    out_fields = ["TBOT_v5_C", "QBOT_v5_kgkg", "RH_v5_pct",
                  "RH_IMPLIED_PCT", "VPD_F_SOURCE", "VPD_F_QC",
                  "VPD_F", "era5_RH_pct", "era5_land_RH_pct",
                  "era5_minus_land_abs_pp", "ZBOT_v5_m",
                  "would_match_stage29_original_screen"]
    print("=== SUSPECTED 2007-05-17 13:00 INPUT ===")
    print(crit[out_fields].to_string())
    print("\n=== +/- 4h / 3h EVENT CONTEXT (INCLUDES ORIGINAL SOURCE/QC) ===")
    print(context[out_fields].to_string(float_format=lambda x: f"{x:.6g}"))
    print("\n=== EVENT SOURCE FLAGS (IF PRESENT) ===")
    optional = [c for c in ("PAIR_STATUS", "RH_LAND_TRIAL_FLAG",
                            "STAGE21_RH_TRIAL_FLAG", "STAGE25_RH_TRIAL_FLAG",
                            "TA_F_SOURCE", "TA_F_QC", "PA_F_SOURCE", "PA_F_QC")
                if c in span.columns]
    if optional:
        print(crit[optional].to_string())
    print("NOTE: Candidate CSV RH source and QC are not observational validation.")
    print("NOTE: The CLM 2-m RH diagnostic differs from input RH.")

    # Count the full RH25A parent source's low RH by provenance to show
    # what the narrow 77-record screening DID and DID NOT cover.
    check(source.index.size == 332880, "Unexpected 19-year candidate row count")
    low = source[source["RH_IMPLIED_PCT"] < 10].copy()
    low["screened_by_stage29"] = (
        low["VPD_F_SOURCE"].eq("EUF_F") &
        low["VPD_F_QC"].eq(2))
    print("\n=== ENTIRE RH25A PARENT CSV: LOW RH BY SOURCE/QC ===")
    for threshold in (1, 5, 10):
        sample = low[low["RH_IMPLIED_PCT"] < threshold]
        print(f"RH below {threshold}%: {len(sample)}, matching Stage29 narrow screen: "
              f"{int(sample['screened_by_stage29'].sum())}")
    table = (low.groupby(["VPD_F_SOURCE", "VPD_F_QC"], dropna=False)
             .agg(n=("RH_IMPLIED_PCT", "size"),
                  min_RH_pct=("RH_IMPLIED_PCT", "min"))
             .sort_values("n", ascending=False))
    print(table.head(25).to_string())

    logs = sorted(RUN.glob("lnd.log.4508890.*"))
    if logs:
        txt = max(logs, key=lambda f: f.stat().st_mtime).read_text(errors="replace")
        nsteps = re.findall(r"at nstep\s*=\s*(\d+)", txt)
        if nsteps:
            step = int(nsteps[-1])
            last_output_date = datetime(2006, 1, 1) + timedelta(minutes=30*step)
            print("\nFinal history write nstep:", step)
            print("Date inferred from history writing (not exact fatal timestep):",
                  last_output_date)
    OUT.mkdir(parents=True, exist_ok=True)
    report = OUT / "01_event_source_QC_and_reference.csv"
    counts = OUT / "02_parent_low_RH_source_QC_counts.csv"
    span.to_csv(report, index_label="time")
    table.to_csv(counts)
    print("\nReports (small CSV, only HOME):", report, counts, sep="\n")
    print("READ-ONLY SOURCE DATA, FORCING AND MODEL. NO Slurm or CIME activity.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Stage36: read-only CH-Aws RH34A 2017 negative *model-diagnostic* RH investigation.

Context: job 4594995 aborted near model date 2017-09-02, in
HumanIndexMod.F90 Wet_BulbS (2 m RH=-2.04867%). Stage29 v5 edited 77
QC2 source records, Stage34 v6 added 27 QC1 records only in 2007/2008.
Do not assume negative 2 m RH implies negative forcing RH or a bad QC0
measurement. Report full 2017 and an event window; do not apply RH floors.

--audit (default) only reads source/forcing/log/reference and writes small
CSV/JSON reports under HOME; no DATM/CIME/Slurm changes.
--fetch-references explicitly downloads and caches 2017-only UTC hourly
ERA5 and ERA5-Land T/Td from Open-Meteo, without overwriting caches,
then audits. Reanalysis is contextual evidence, NOT tower validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing")
V6 = ROOT / "datm_11_stage34_qc1_27rh_sensitivity_v6/CH-Aws_DATM_2017.nc"
V5 = ROOT / "datm_11_stage29_all77_rh_sensitivity_v5/CH-Aws_DATM_2017.nc"
SOURCE = ROOT / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
OUT = Path.home() / "FLUXNET_MultiSite_11/stage36_CH_Aws_RH34A_2017_audit"
RUN = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/CH-Aws_FATES_SPINUP1000_RH34A/run")
DATE = pd.Timestamp("2017-09-02")  # model-log vicinity, NOT a proven exact failing half-hour
LAT, LON = 46.583111, 9.790639
VARS = ("TBOT", "PSRF", "QBOT", "ZBOT", "WIND", "FSDS", "FLDS", "PRECTmms")


def require(ok, why):
    if not ok:
        raise RuntimeError("STOP: " + why)


def sat_hpa(temp_c):
    x = np.asarray(temp_c, dtype=float)
    return 6.112 * np.exp(np.clip(17.67 * x / (x + 243.5), -100, 100))


def check_reference(obj, model):
    require(obj.get("utc_offset_seconds") == 0, model + ": UTC offset not zero")
    hourly = obj.get("hourly", {})
    keys = ("time", "temperature_2m", "dew_point_2m")
    require(all(k in hourly and len(hourly[k]) == 8760 for k in keys),
            model + ": incomplete 2017 hourly reference")
    idx = pd.DatetimeIndex(pd.to_datetime(hourly["time"], errors="raise"))
    expected = pd.date_range("2017-01-01", "2017-12-31 23:00", freq="h")
    require(idx.equals(expected), model + ": unexpected timestamp sequence")
    for k in keys[1:]:
        vals = pd.to_numeric(pd.Series(hourly[k]), errors="coerce").to_numpy(float)
        require(np.isfinite(vals).all(), model + ": invalid " + k)
    return hourly, idx


def fetch_2017():
    CACHE.mkdir(parents=True, exist_ok=True)
    for model in ("era5", "era5_land"):
        dest = CACHE / (model + "_2017.json")
        if dest.exists():
            check_reference(json.loads(dest.read_text()), model)
            print("Already cached and verified:", dest)
            continue
        args = dict(latitude=LAT, longitude=LON, start_date="2017-01-01",
                    end_date="2017-12-31",
                    hourly="temperature_2m,dew_point_2m,relative_humidity_2m",
                    timezone="GMT", models=model)
        url = "https://archive-api.open-meteo.com/v1/archive?" + urlencode(args)
        print("Downloading contextual reanalysis:", model, flush=True)
        req = Request(url, headers={"User-Agent": "CH-Aws-stage36-research-audit/1.0"})
        with urlopen(req, timeout=90) as response:
            raw = response.read()
        obj = json.loads(raw)
        require(not obj.get("error"), model + ": API error")
        check_reference(obj, model)
        # Write only after the entire response has passed validation.
        with tempfile.NamedTemporaryFile(mode="wb", dir=CACHE, prefix=".stage36_",
                                         delete=False) as tmp:
            tmp.write(raw)
            temp = Path(tmp.name)
        try:
            require(not dest.exists(), "Refusing to overwrite cached reference: " + str(dest))
            temp.rename(dest)
        finally:
            temp.unlink(missing_ok=True)
        print("Cached:", dest)


def reference_at(model, desired):
    path = CACHE / (model + "_2017.json")
    if not path.is_file():
        return None
    hourly, utc = check_reference(json.loads(path.read_text()), model)
    arr = pd.DataFrame({
        "T": pd.to_numeric(pd.Series(hourly["temperature_2m"]),
                           errors="coerce").to_numpy(float),
        "Td": pd.to_numeric(pd.Series(hourly["dew_point_2m"]),
                            errors="coerce").to_numpy(float),
    }, index=utc + pd.Timedelta(hours=1))  # FLUXNET local standard UTC+1, no DST
    arr = (arr.reindex(arr.index.union(desired)).sort_index()
           .interpolate(method="time", limit=1, limit_area="inside")
           .reindex(desired))
    # UTC+1 conversion leaves the first two local-standard half hours outside
    # a single calendar-year UTC cache; preserve them as NaN, not zero.
    window = arr.loc[DATE - pd.Timedelta(days=3):DATE + pd.Timedelta(days=3, hours=23, minutes=30)]
    require(window.notna().all().all(), model + ": missing reference inside failure window")
    return 100 * sat_hpa(arr["Td"]) / sat_hpa(arr["T"])


def annual_forcing(path):
    require(path.is_file(), "Missing 2017 DATM: " + str(path))
    with Dataset(path) as ds:
        time = ds["time"]
        axis = pd.DatetimeIndex([
            str(t)[:19] for t in num2date(
                time[:], units=time.units,
                calendar=getattr(time, "calendar", "noleap"))
        ])
        require(len(axis) == 17520 and axis.is_unique
                and (axis.year == 2017).all(), "Incorrect 2017 noleap DATM axis")
        data = {"time": axis}
        for var in VARS:
            require(var in ds.variables, "Missing DATM variable " + var)
            a = np.ma.asarray(ds[var][:, 0, 0])
            require(not np.ma.getmaskarray(a).any(), "Masked DATM data in " + var)
            data[var] = np.asarray(a, dtype=float)
            require(np.isfinite(data[var]).all(), "Nonfinite DATM variable " + var)
    return pd.DataFrame(data).set_index("time")


def main():
    manifest = V6.parent / "stage34_manifest.json"
    require(manifest.is_file(), "Missing Stage34 v6 manifest")
    m = json.loads(manifest.read_text())
    require(m.get("version") == "STAGE34_QC1_27ROW_SENSITIVITY_V6"
            and m.get("modified_vs_v5") == 27, "Unexpected Stage34 parent")
    current, parent = annual_forcing(V6), annual_forcing(V5)
    require(current.index.equals(parent.index), "v5-v6 year axis mismatch")
    change_count = int((current["QBOT"].to_numpy() != parent["QBOT"].to_numpy()).sum())
    require(change_count == 0, "Stage34 claims 2017 unchanged, but v6 differs from v5")
    require(V6.is_symlink() and V6.resolve() == V5.resolve(),
            "Expected 2017 v6 symlink to v5")
    print("STAGE34 verified: 2017 v6 is an unchanged v5 symlink")

    require(SOURCE.is_file(), "Missing original source CSV " + str(SOURCE))
    requested = {"time", "RH_IMPLIED_PCT", "TA_F", "PA_F", "VPD_F",
                 "VPD_F_SOURCE", "VPD_F_QC", "PAIR_STATUS",
                 "TA_F_SOURCE", "TA_F_QC", "PA_F_SOURCE", "PA_F_QC"}
    src = pd.read_csv(SOURCE, usecols=lambda c: c in requested, low_memory=False)
    require({"time", "RH_IMPLIED_PCT", "VPD_F_SOURCE", "VPD_F_QC"}
            .issubset(src.columns), "Source CSV lacks required QC/meteorology")
    src["time"] = pd.to_datetime(src["time"], errors="raise")
    require(src["time"].is_unique and len(src) == 332880,
            "Unexpected source timeline")
    src = src.set_index("time").reindex(current.index)
    require(src["VPD_F_SOURCE"].notna().all(), "2017 source metadata missing")
    for col in ("RH_IMPLIED_PCT", "TA_F", "PA_F", "VPD_F", "VPD_F_QC"):
        if col in src:
            src[col] = pd.to_numeric(src[col], errors="coerce")

    result = current.join(src, validate="one_to_one")
    q, p, t = result.QBOT.to_numpy(), result.PSRF.to_numpy(), result.TBOT.to_numpy()
    require((p > 0).all(), "DATM contains PSRF<=0")
    es_pa = sat_hpa(t - 273.15) * 100
    e_pa = q * p / (0.622 + 0.378 * q)
    result["input_RH_water_pct"] = 100 * e_pa / es_pa
    result["dRH_prev30min_pp"] = result["input_RH_water_pct"].diff()
    result["dQBOT_prev30min"] = result["QBOT"].diff()
    result["input_RH_water_invalid"] = (
        (result["input_RH_water_pct"] < 0) | (result["input_RH_water_pct"] > 100))
    result["forcing_QBOT_invalid"] = (result["QBOT"] < 0) | (result["QBOT"] >= 0.08)
    # Source RH can differ from v6 RH after earlier exploratory edits.
    for model in ("era5", "era5_land"):
        vals = reference_at(model, result.index)
        if vals is None:
            result[model + "_RH_pct"] = np.nan
            print("REFERENCE NOT CACHED:", CACHE / (model + "_2017.json"))
        else:
            result[model + "_RH_pct"] = vals
            print("Verified 2017 contextual reanalysis:", model)
    result["ERA5_ERA5Land_gap_pp"] = (
        result["era5_RH_pct"] - result["era5_land_RH_pct"]).abs()
    result["land_minus_input_pp"] = (
        result["era5_land_RH_pct"] - result["input_RH_water_pct"])
    result["QC1or2_priority_for_manual_review"] = (
        result["VPD_F_QC"].isin((1, 2))
        & result["era5_RH_pct"].ge(30)
        & result["era5_land_RH_pct"].ge(30)
        & result["ERA5_ERA5Land_gap_pp"].le(15)
        & result["land_minus_input_pp"].ge(20))
    # This flag is NOT authorisation to alter the forcing or observed QC0 values.

    lo = DATE - pd.Timedelta(days=3)
    hi = DATE + pd.Timedelta(days=3, hours=23, minutes=30)
    window = result.loc[lo:hi].copy()
    require(not window.empty, "2017-09-02 window missing")
    print("\n=== MODEL ABORT ===")
    logs = list(RUN.glob("lnd.log.4594995.*"))
    if logs:
        log = max(logs, key=lambda f: f.stat().st_mtime)
        contents = log.read_text(errors="replace")
        print("Land log:", log)
        print("Negative RH abort:", "ERROR RH is negative" in contents)
        negs = re.findall(r"rh\s*=\s*(-?[0-9.]+(?:[eEdD][+-]?[0-9]+)?)", contents)
        print("Last negative diagnostic RH:", negs[-1] if negs else "not located")
    print("MODEL incident near 2017-09-02; final history nstep is NOT an exact abort clock.")
    print("Important: input RH (calculated from QBOT) is NOT CLM 2-m diagnostic RH.")
    print("\n=== ANNUAL FORCING AND QC SCREEN ===")
    for thresh in (5, 10, 15, 20, 30):
        n = int((result["input_RH_water_pct"] < thresh).sum())
        print(f"2017 input RH < {thresh}%: {n}")
    print("2017 negative QBOT records:", int((result["QBOT"] < 0).sum()))
    print("2017 invalid input RH:", int(result.input_RH_water_invalid.sum()))
    print("2017 forcing QC1/2 manual-review priority:", int(result.QC1or2_priority_for_manual_review.sum()))
    print("2017 VPD_F_QC counts:", result.VPD_F_QC.value_counts(dropna=False).to_dict())
    print("\n=== 7-DAY INCIDENT WINDOW ===")
    print("Datetime range:", window.index[0], "to", window.index[-1])
    print("Input RH min/max:", float(window.input_RH_water_pct.min()),
          float(window.input_RH_water_pct.max()))
    print("QBOT min/max:", float(window.QBOT.min()), float(window.QBOT.max()))
    print("30-min RH jump min/max:", float(window.dRH_prev30min_pp.min()),
          float(window.dRH_prev30min_pp.max()))
    cols = ["QBOT", "TBOT", "PSRF", "ZBOT", "WIND", "input_RH_water_pct",
            "RH_IMPLIED_PCT", "VPD_F_QC", "VPD_F_SOURCE",
            "era5_RH_pct", "era5_land_RH_pct", "ERA5_ERA5Land_gap_pp",
            "QC1or2_priority_for_manual_review"]
    print("\n25 driest INPUT half-hours in incident window:")
    print(window.nsmallest(25, "input_RH_water_pct")[cols].to_string(
        float_format=lambda x: f"{x:.5g}"))
    print("\nLargest negative 30-minute RH changes:")
    print(window.nsmallest(15, "dRH_prev30min_pp")[
        ["input_RH_water_pct", "dRH_prev30min_pp", "VPD_F_QC",
         "VPD_F_SOURCE", "era5_RH_pct", "era5_land_RH_pct"]
    ].to_string(float_format=lambda x: f"{x:.5g}"))
    print("\nWindow QC/source and low-RH counts:")
    tab = window.assign(low10=window.input_RH_water_pct < 10,
                        low20=window.input_RH_water_pct < 20).groupby(
        ["VPD_F_SOURCE", "VPD_F_QC"], dropna=False
    ).agg(n=("QBOT", "size"), low10=("low10", "sum"),
          low20=("low20", "sum"),
          priority=("QC1or2_priority_for_manual_review", "sum"))
    print(tab.to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    window.to_csv(OUT / "01_failure_window_2017_v6_and_sources.csv",
                  index_label="time", float_format="%.12g")
    result.loc[result["input_RH_water_pct"] < 30].to_csv(
        OUT / "02_full2017_low30_inputRH.csv", index_label="time",
        float_format="%.12g")
    summary = {
        "site": "CH-Aws", "case": "CH-Aws_FATES_SPINUP1000_RH34A",
        "job": "4594995", "event_near": str(DATE.date()),
        "fatal_model_RH_pct": -2.04867089950063,
        "forcing_v6_2017": str(V6),
        "forcing_v6_equals_v5_2017": True,
        "2017_input_RH_min_pct": float(result.input_RH_water_pct.min()),
        "2017_QBOT_negative": int((result.QBOT < 0).sum()),
        "2017_QC1or2_manual_review": int(result.QC1or2_priority_for_manual_review.sum()),
        "reanalysis_cached": {
            model: (CACHE / (model + "_2017.json")).is_file()
            for model in ("era5", "era5_land")},
        "scientific_status": "READ_ONLY_DIAGNOSTIC_NOT_FORCING_CORRECTION",
        "note": "Never infer input RH from negative model 2m RH; exact model abort timestep unknown"
    }
    (OUT / "03_stage36_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("\nREPORTS (HOME ONLY):", OUT)
    print("READ-ONLY: No forcing, restart, CIME configuration or Slurm job was modified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="Default: read-only")
    parser.add_argument("--fetch-references", action="store_true",
                        help="Explicitly cache 2017 ERA5 and ERA5-Land before audit")
    args = parser.parse_args()
    if args.fetch_references:
        fetch_2017()
    main()

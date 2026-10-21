#!/usr/bin/env python3
"""Stage41: read-only investigation of CH-Aws RH38A negative 2-m RH in 2020.

RH38A job 4602421 branched successfully from RH34A 2016-01-01 and got
past the 2017-09-02 incident after Stage38 v7 21-row humidity sensitivity.
It then failed with rh=-1.99582396411208 in HumanIndexMod.F90:1019.
Last successful land-history nstep=255600; at ATM_NCPL=48, NO_LEAP,
origin 2006-01-01, this corresponds to 2020-08-04 00:00 (approximate
failure vicinity, NOT the proven fatal model timestep).

Modes:
  --audit (default): inspect cached data/forcings and emit small CSV under HOME.
  --fetch-references: download UTC hourly 2020 ERA5 + ERA5-Land T/Td via
      Open-Meteo if not yet cached (never overwrite), then run the audit.

No CIME case, archive, restart, Slurm job or NetCDF forcing is modified.
Reanalyses are correlated contextual estimates, not tower observations.
QC1 candidate flags mean REVIEW ONLY, not authorized data corrections.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing")
V6 = ROOT / "datm_11_stage34_qc1_27rh_sensitivity_v6/CH-Aws_DATM_2020.nc"
V7 = ROOT / "datm_11_stage38_qc1_21rh_sensitivity_v7/CH-Aws_DATM_2020.nc"
SOURCE = ROOT / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
OUT = Path.home() / "FLUXNET_MultiSite_11/stage41_CH_Aws_RH38A_2020_failure"
RUN = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/CH-Aws_FATES_SPINUP1000_RH38A_CONT2016/run")
JOB = "4602421"
YEAR = 2020
EVENT = pd.Timestamp("2020-08-04 00:00")
LAT, LON = 46.583111, 9.790639
VARS = ("QBOT", "TBOT", "PSRF", "ZBOT", "WIND", "FSDS", "FLDS", "PRECTmms")


def require(cond, reason):
    if not cond:
        raise RuntimeError("STOP: " + reason)


def saturation_hpa(ta_c):
    ta = np.asarray(ta_c, dtype=float)
    return 6.112 * np.exp(np.clip(17.67 * ta / (ta + 243.5), -100, 100))


def validate_reference(data, model):
    require(data.get("utc_offset_seconds") == 0, "UTC offset not zero: " + model)
    raw = data.get("hourly", {})
    fields = ("time", "temperature_2m", "dew_point_2m")
    require(all(f in raw and len(raw[f]) == 8784 for f in fields),
            "Incomplete 2020 hourly reference: " + model)
    idx = pd.DatetimeIndex(pd.to_datetime(raw["time"], errors="raise"))
    expected = pd.date_range("2020-01-01", "2020-12-31 23:00", freq="h")
    require(idx.equals(expected), "Incorrect 2020 UTC timeline: " + model)
    for f in fields[1:]:
        vals = pd.to_numeric(pd.Series(raw[f]), errors="coerce").to_numpy(float)
        require(np.isfinite(vals).all(), "Nonfinite reference " + f + " " + model)
    return raw, idx


def fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    for model in ("era5", "era5_land"):
        dst = CACHE / f"{model}_2020.json"
        if dst.is_file():
            validate_reference(json.loads(dst.read_text()), model)
            print("VERIFIED CACHED:", dst)
            continue
        args = dict(latitude=LAT, longitude=LON,
                    start_date="2020-01-01", end_date="2020-12-31",
                    hourly="temperature_2m,dew_point_2m,relative_humidity_2m",
                    timezone="GMT", models=model)
        url = "https://archive-api.open-meteo.com/v1/archive?" + urlencode(args)
        req = Request(url, headers={"User-Agent": "CH-Aws-stage41-rh-research/1.0"})
        print("DOWNLOADING REANALYSIS:", model, flush=True)
        with urlopen(req, timeout=90) as response:
            body = response.read()
        data = json.loads(body)
        require(not data.get("error"), "Open-Meteo returned error: " + model)
        validate_reference(data, model)
        with tempfile.NamedTemporaryFile(dir=CACHE, prefix=".stage41_", delete=False) as f:
            f.write(body)
            temp = Path(f.name)
        try:
            require(not dst.exists(), "Reference cache appeared during download: " + str(dst))
            temp.rename(dst)
        finally:
            temp.unlink(missing_ok=True)
        print("CACHED:", dst)


def reference_rh(model, desired):
    path = CACHE / f"{model}_2020.json"
    if not path.is_file():
        print("MISSING REFERENCE:", path, "(no priority classification until cached)")
        return pd.Series(np.nan, index=desired, dtype=float)
    raw, utc = validate_reference(json.loads(path.read_text()), model)
    df = pd.DataFrame({
        "T": pd.to_numeric(pd.Series(raw["temperature_2m"]),
                           errors="coerce").to_numpy(float),
        "Td": pd.to_numeric(pd.Series(raw["dew_point_2m"]),
                            errors="coerce").to_numpy(float),
    }, index=utc + pd.Timedelta(hours=1))
    aligned = (df.reindex(df.index.union(desired)).sort_index()
               .interpolate(method="time", limit=1, limit_area="inside")
               .reindex(desired))
    # Preserve the first two missing local half-hours due to previous UTC year.
    # 2020 is Gregorian leap year in ERA5 but NO_LEAP in the model;
    # the Feb 29 ERA records are NOT treated as forcing samples.
    event_window = aligned.loc["2020-08-02":"2020-08-06"]
    require(event_window.notna().all().all(),
            "ERA reference incomplete around crash: " + model)
    values = (100 * saturation_hpa(aligned["Td"].to_numpy(float))
              / saturation_hpa(aligned["T"].to_numpy(float)))
    return pd.Series(values, index=desired, dtype=float)


def forcing():
    require(V7.is_symlink() and V7.resolve() == V6.resolve(),
            "v7 2020 annual file should link unchanged v6; investigate before audit")
    require(V7.is_file(), "Broken/missing 2020 v7 forcing")
    with Dataset(V7) as ds:
        tv = ds["time"]
        times = pd.DatetimeIndex([
            str(t)[:19] for t in num2date(
                tv[:], tv.units, calendar=getattr(tv, "calendar", "noleap"))
        ])
        require(len(times) == 17520 and times.is_unique
                and (times.year == YEAR).all()
                and not ((times.month == 2) & (times.day == 29)).any(),
                "Unexpected model NO_LEAP 2020 time axis")
        vals = {}
        for key in VARS:
            require(key in ds.variables, "Missing DATM variable " + key)
            v = np.ma.asarray(ds[key][:, 0, 0])
            require(not np.ma.getmaskarray(v).any(), "Masked DATM data: " + key)
            vals[key] = np.asarray(v, dtype=float)
            require(np.isfinite(vals[key]).all(), "Nonfinite DATM data: " + key)
    return pd.DataFrame(vals, index=times)


def model_clock(step):
    # Assumes first clock instant = 2006-01-01, NO_LEAP, ATM_NCPL=48.
    whole, remainder = divmod(step, 48)
    year = 2006
    while whole >= 365:
        whole -= 365
        year += 1
    # Use the nonleap calendar year 2021 as month/day template.
    t = datetime(2021, 1, 1) + timedelta(days=whole, minutes=30 * remainder)
    return t.replace(year=year)


def main():
    a = forcing()
    require(SOURCE.is_file(), "Original RH25A source CSV missing")
    cols = {"time", "TA_F", "PA_F", "VPD_F", "VPD_F_SOURCE",
            "VPD_F_QC", "RH_IMPLIED_PCT", "PAIR_STATUS",
            "TA_F_SOURCE", "TA_F_QC", "PA_F_SOURCE", "PA_F_QC"}
    source = pd.read_csv(SOURCE, usecols=lambda x: x in cols, low_memory=False)
    source["time"] = pd.to_datetime(source["time"], errors="raise")
    require(source.time.is_unique and len(source) == 332880,
            "Unexpected 19-year source timestamps")
    source = source.set_index("time").reindex(a.index)
    require(source.VPD_F_SOURCE.notna().all(), "Missing 2020 source provenance")
    for col in ("TA_F", "PA_F", "VPD_F", "VPD_F_QC", "RH_IMPLIED_PCT"):
        if col in source:
            source[col] = pd.to_numeric(source[col], errors="coerce")
    a = a.join(source, validate="one_to_one")
    q = a["QBOT"].to_numpy(float)
    p = a["PSRF"].to_numpy(float)
    temp_c = a["TBOT"].to_numpy(float) - 273.15
    require((p > 0).all(), "Invalid PSRF in 2020 forcing")
    ea_pa = q * p / (0.622 + 0.378 * q)
    a["input_RH_pct"] = 100 * ea_pa / (100 * saturation_hpa(temp_c))
    a["rh_jump_pp"] = a.input_RH_pct.diff()
    for model in ("era5", "era5_land"):
        a[f"{model}_RH_pct"] = reference_rh(model, a.index)
    a["reference_gap_pp"] = abs(a.era5_RH_pct - a.era5_land_RH_pct)
    a["land_minus_input_pp"] = a.era5_land_RH_pct - a.input_RH_pct
    a["strict_QC1_candidate"] = (
        a.VPD_F_SOURCE.eq("EUF_F")
        & a.VPD_F_QC.eq(1)
        & a.RH_IMPLIED_PCT.lt(10)
        & a.input_RH_pct.lt(10)
        & a.era5_RH_pct.ge(30)
        & a.era5_land_RH_pct.ge(30)
        & a.reference_gap_pp.le(15)
        & a.land_minus_input_pp.ge(20)
    )
    a["low_RH_QC0_DO_NOT_AUTO_EDIT"] = a.VPD_F_QC.eq(0) & a.input_RH_pct.lt(10)

    print("========== STAGE41 CH-AWS RH38A 2020 RESTART-TO-ABORT REVIEW ==========")
    logs = list(RUN.glob("lnd.log." + JOB + ".*"))
    if logs:
        log = max(logs, key=lambda f: f.stat().st_mtime)
        body = log.read_text(errors="replace")
        hits = [int(x) for x in re.findall(r"\bnstep\s*=\s*(\d+)", body)]
        fail = re.findall(r"\brh\s*=\s*(-?[0-9.]+(?:[eEdD][+-]?[0-9]+)?)", body)
        print("Land log:", log)
        print("Negative RH fatal:", "ERROR RH is negative" in body)
        print("Last fatal RH value:", fail[-1] if fail else "not located")
        if hits:
            step = max(hits)
            print("Last logged model step:", step,
                  "=> NO_LEAP ~", model_clock(step))
            require(step >= 255600, "Unexpected older log nstep; investigate clock")
    print("Failure time NOT EXACTLY known; history output boundary is an approximation.")
    print("v7 forcing 2020 links unchanged v6: VERIFIED")
    print("2020 INPUT RH below 5 / 10 / 20 / 30%:",
          *[int((a.input_RH_pct < n).sum()) for n in (5, 10, 20, 30)])
    print("2020 negative QBOT:", int((a.QBOT < 0).sum()))
    print("2020 invalid input RH <0 or >100:",
          int(((a.input_RH_pct < 0) | (a.input_RH_pct > 100)).sum()))
    print("2020 strict QC1 review candidates:",
          int(a.strict_QC1_candidate.sum()))
    print("2020 QC0 with input RH<10% (preserve):",
          int(a.low_RH_QC0_DO_NOT_AUTO_EDIT.sum()))

    display = ["QBOT", "TBOT", "PSRF", "ZBOT", "WIND", "input_RH_pct",
               "VPD_F_QC", "VPD_F_SOURCE", "RH_IMPLIED_PCT",
               "era5_RH_pct", "era5_land_RH_pct", "reference_gap_pp",
               "rh_jump_pp", "strict_QC1_candidate"]
    win = a.loc["2020-08-02":"2020-08-06"]
    print("\n=== 2020-08-03 18:00 to 2020-08-05 06:00 every half-hour ===")
    print(a.loc["2020-08-03 18:00":"2020-08-05 06:00", display]
          .to_string(float_format=lambda z: f"{z:.6g}"))
    print("\n=== 25 DRIEST 2020-08-02..06 RECORDS ===")
    print(win.nsmallest(25, "input_RH_pct")[display]
          .to_string(float_format=lambda z: f"{z:.6g}"))
    print("\n=== FULL 2020 STRICT QC1 CANDIDATE TIMESTAMPS ===")
    print(a.loc[a.strict_QC1_candidate, display]
          .to_string(float_format=lambda z: f"{z:.6g}"))
    print("\n=== 2020 QC0 LOW-RH (PRESERVE AND SOURCE VALIDATE) ===")
    print(a.loc[a.low_RH_QC0_DO_NOT_AUTO_EDIT, display]
          .to_string(float_format=lambda z: f"{z:.6g}"))

    OUT.mkdir(parents=True, exist_ok=True)
    win.to_csv(OUT / "01_20200804_failure_window.csv", index_label="time",
               float_format="%.12g")
    a.loc[a.strict_QC1_candidate].to_csv(
        OUT / "02_2020_strict_QC1_review_only.csv",
        index_label="time", float_format="%.12g")
    a.loc[a.input_RH_pct.lt(30)].to_csv(
        OUT / "03_2020_input_RH_below30_review_only.csv",
        index_label="time", float_format="%.12g")
    summary = {
        "case": "CH-Aws_FATES_SPINUP1000_RH38A_CONT2016",
        "failed_job": JOB, "fatal_model_RH_pct": -1.99582396411208,
        "approx_last_history_step": 255600,
        "approx_model_time_noleap": str(model_clock(255600)),
        "strict_QC1_candidates_2020": int(a.strict_QC1_candidate.sum()),
        "QC0_low_RH_records_2020": int(a.low_RH_QC0_DO_NOT_AUTO_EDIT.sum()),
        "v7_2020_same_as_v6": True,
        "reanalysis_cached": {
            m: (CACHE / f"{m}_2020.json").is_file()
            for m in ("era5", "era5_land")
        },
        "status": "READ_ONLY_NO_FORCING_CHANGES",
        "warning": "Fatal timestep not exact; reanalysis is not observational proof"
    }
    (OUT / "04_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("\nREPORTS:", OUT)
    print("READ ONLY. No DATM, CIME, restart or Slurm modification.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="read-only default")
    parser.add_argument("--fetch-references", action="store_true",
                        help="cache ERA5 and ERA5-Land 2020 then audit")
    args = parser.parse_args()
    if args.fetch_references:
        fetch()
    main()

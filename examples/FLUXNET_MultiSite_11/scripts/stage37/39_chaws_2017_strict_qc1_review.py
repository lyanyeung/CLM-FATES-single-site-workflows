#!/usr/bin/env python3
"""Stage37: conservative, read-only CH-Aws 2017 RH34A QC1 event review.

Stage29/v5 changed 77 QC2 half-hours (full forcing period); Stage34/v6
changed 27 QC1 half-hours (2007/08). Current 2017 v6 is a symlink to v5.
Job 4594995 crashed with model-diagnostic 2m RH -2.04867% near 2017-09-02.
The last known logged warning nstep=204457 corresponds to 2017-09-02
12:30 for NO_LEAP/48 steps per day from 2006-01-01; the exact fatal
timestep and input alignment are not independently established.

This script reuses Stage34's *strict* QC1 selection rather than the
Stage36 broad flag (1211 records). It prepares evidence, NOT edits.
ERA5/ERA5-Land are related reanalyses, not independent tower observations.
No forcing, CIME, Slurm, or restart files are modified.
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
V6 = SITE / "datm_11_stage34_qc1_27rh_sensitivity_v6/CH-Aws_DATM_2017.nc"
V5 = SITE / "datm_11_stage29_all77_rh_sensitivity_v5/CH-Aws_DATM_2017.nc"
CSV = SITE / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
LOGDIR = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/CH-Aws_FATES_SPINUP1000_RH34A/run")
OUT = Path.home() / "FLUXNET_MultiSite_11/stage37_CH_Aws_2017_strict_QC1_review"
EVENT = pd.Timestamp("2017-09-02 12:30")


def require(ok, why):
    if not ok:
        raise RuntimeError("STOP: " + why)


def es_hpa(t_c):
    t_c = np.asarray(t_c, dtype=float)
    return 6.112 * np.exp(np.clip(17.67 * t_c / (t_c + 243.5), -100, 100))


def forcing():
    require(V6.is_symlink() and V6.resolve() == V5.resolve(),
            "2017 v6 is not the unchanged v5 symlink")
    require(V6.is_file(), "2017 v6 input missing/broken symlink")
    m = json.loads((V6.parent / "stage34_manifest.json").read_text())
    require(m.get("version") == "STAGE34_QC1_27ROW_SENSITIVITY_V6"
            and m.get("modified_vs_v5") == 27,
            "Unexpected v6 provenance manifest")
    with Dataset(V6) as ds:
        v = ds["time"]
        times = pd.DatetimeIndex([
            str(t)[:19] for t in num2date(
                v[:], v.units, calendar=getattr(v, "calendar", "noleap"))])
        require(len(times) == 17520 and times.is_unique
                and (times.year == 2017).all(), "Wrong noleap 2017 time axis")
        out = {}
        for name in ("QBOT", "TBOT", "PSRF", "ZBOT", "WIND"):
            require(name in ds.variables, "Missing " + name)
            vals = np.ma.asarray(ds[name][:, 0, 0])
            require(not np.ma.getmaskarray(vals).any(), "Masked " + name)
            out[name] = np.asarray(vals, dtype=float)
            require(np.isfinite(out[name]).all(), "Non-finite " + name)
    return pd.DataFrame(out, index=times)


def reference(model, desired):
    f = CACHE / f"{model}_2017.json"
    require(f.is_file(), "Missing reference " + str(f) +
            "; run Stage36 --fetch-references first")
    raw = json.loads(f.read_text())
    require(raw.get("utc_offset_seconds") == 0,
            "Reference timezone is not UTC: " + str(f))
    hourly = raw["hourly"]
    keys = ("time", "temperature_2m", "dew_point_2m")
    require(all(k in hourly and len(hourly[k]) == 8760 for k in keys),
            "Incomplete reference " + str(f))
    utc = pd.DatetimeIndex(pd.to_datetime(hourly["time"], errors="raise"))
    require(utc.equals(pd.date_range("2017-01-01", "2017-12-31 23:00",
                                      freq="h")), "Wrong reference time axis")
    tmp = pd.DataFrame({
        "T": pd.to_numeric(pd.Series(hourly["temperature_2m"]),
                           errors="coerce").to_numpy(float),
        "Td": pd.to_numeric(pd.Series(hourly["dew_point_2m"]),
                            errors="coerce").to_numpy(float),
    }, index=utc + pd.Timedelta(hours=1))
    require(np.isfinite(tmp.to_numpy()).all(), "Non-finite " + model + " values")
    tmp = (tmp.reindex(tmp.index.union(desired)).sort_index()
           .interpolate(method="time", limit=1, limit_area="inside")
           .reindex(desired))
    # 2017-01-01 00:00 and 00:30 require the previous UTC year.
    # Preserve missing values as NaN; never extrapolate or fill with zero.
    require(tmp.loc["2017-09-01":"2017-09-04"].notna().all().all(),
            model + " event-window reference missing")
    return pd.Series(100 * es_hpa(tmp.Td.to_numpy())
                     / es_hpa(tmp.T.to_numpy()), index=desired)


def noleap_clock(step):
    """Time coordinate implied by nstep, if nstep zero = 2006-01-01 00:00."""
    days, half_hours = divmod(step, 48)
    year = 2006
    while days >= 365:
        days -= 365
        year += 1
    return datetime(year, 1, 1) + timedelta(
        days=days, minutes=30 * half_hours)


def main():
    f = forcing()
    require(CSV.is_file(), "Missing source candidate CSV")
    cols = {"time", "RH_IMPLIED_PCT", "TA_F", "PA_F", "VPD_F",
            "VPD_F_SOURCE", "VPD_F_QC", "PAIR_STATUS",
            "TA_F_SOURCE", "TA_F_QC", "PA_F_SOURCE", "PA_F_QC"}
    src = pd.read_csv(CSV, usecols=lambda name: name in cols, low_memory=False)
    src["time"] = pd.to_datetime(src["time"], errors="raise")
    require(len(src) == 332880 and src.time.is_unique,
            "Unexpected source CSV timeline")
    src = src.set_index("time").reindex(f.index)
    require(src.VPD_F_SOURCE.notna().all(), "Missing source provenance")
    for name in ("RH_IMPLIED_PCT", "TA_F", "PA_F", "VPD_F", "VPD_F_QC"):
        src[name] = pd.to_numeric(src[name], errors="coerce")
    a = f.join(src, validate="one_to_one")

    q, p, tc = a.QBOT.to_numpy(), a.PSRF.to_numpy(), a.TBOT.to_numpy() - 273.15
    require((p > 0).all(), "Nonphysical pressure")
    ea = q * p / (.622 + .378 * q)
    a["input_RH_pct"] = 100 * ea / (100 * es_hpa(tc))
    require(np.isfinite(a.input_RH_pct).all(), "Nonfinite input RH")
    a["era5_RH_pct"] = reference("era5", a.index)
    a["era5_land_RH_pct"] = reference("era5_land", a.index)
    a["reanalysis_gap_pp"] = abs(a.era5_RH_pct - a.era5_land_RH_pct)
    a["land_minus_input_pp"] = a.era5_land_RH_pct - a.input_RH_pct
    a["jump_from_previous_pp"] = a.input_RH_pct.diff()

    # Use Stage34 strict criteria, but apply to 2017 and actual v6 forcing.
    # The source/QC/low-RH conditions restrict modifications far more
    # strongly than Stage36's general 1211 manual-review flags.
    strict = (
        a.VPD_F_SOURCE.eq("EUF_F")
        & a.VPD_F_QC.eq(1)
        & a.RH_IMPLIED_PCT.lt(10)
        & a.input_RH_pct.lt(10)
        & a.era5_RH_pct.ge(30)
        & a.era5_land_RH_pct.ge(30)
        & a.reanalysis_gap_pp.le(15)
        & a.land_minus_input_pp.ge(20)
    )
    a["stage37_strict_QC1_candidate"] = strict
    flagged = a.loc[strict].copy()
    require(EVENT in a.index, "Critical 2017-09-02 12:30 missing")

    # Candidate calculation mirrors Stage34 for *review only*.
    if len(flagged):
        es_site = es_hpa(flagged.TA_F.to_numpy(float))
        ea_new = es_site * flagged.era5_land_RH_pct.to_numpy(float)
        pressure_pa = flagged.PA_F.to_numpy(float) * 1000
        qnew = .622 * ea_new / (pressure_pa - .378 * ea_new)
        require(np.isfinite(qnew).all() and ((qnew > 0) & (qnew < .08)).all(),
                "Potential QBOT candidate has invalid values")
        flagged["QBOT_stage37_review_only"] = qnew
        flagged["QBOT_change_review_only"] = qnew - flagged.QBOT
    else:
        flagged["QBOT_stage37_review_only"] = pd.Series(dtype=float)
        flagged["QBOT_change_review_only"] = pd.Series(dtype=float)

    print("========== STAGE37 STRICT QC1 REVIEW ==========")
    print("2017 v6 forcing is a symlink to v5: VERIFIED")
    print("Critical model abort RH: -2.04867089950063% (2m diagnostic)")
    print("2017 QC1 records:", int(a.VPD_F_QC.eq(1).sum()))
    print("Strict Stage34-like QC1 candidates:", int(strict.sum()))
    print("Input RH below 10%:", int((a.input_RH_pct < 10).sum()))
    print("Invalid input RH below 0%:", int((a.input_RH_pct < 0).sum()))
    print("Invalid input RH above 100%:", int((a.input_RH_pct > 100).sum()))
    print("Critical 2017-09-02 12:30 passes strict screen:",
          bool(strict.loc[EVENT]))
    files = list(LOGDIR.glob("lnd.log.4594995.*"))
    if files:
        log = max(files, key=lambda x: x.stat().st_mtime)
        body = log.read_text(errors="replace")
        steps = [int(x) for x in re.findall(r"\bnstep\s*=\s*(\d+)", body)]
        if steps:
            last = max(steps)
            print("Last logged nstep:", last,
                  "=> implied NO_LEAP model time", noleap_clock(last))
            print("Not proof of exact fatal timestep / forcing timestamp.")
        print("Negative RH abort:", "ERROR RH is negative" in body)
    display = [
        "QBOT", "input_RH_pct", "RH_IMPLIED_PCT",
        "VPD_F_SOURCE", "VPD_F_QC", "TA_F", "PA_F", "VPD_F",
        "era5_RH_pct", "era5_land_RH_pct", "reanalysis_gap_pp",
        "land_minus_input_pp", "jump_from_previous_pp",
        "stage37_strict_QC1_candidate"
    ]
    window = a.loc["2017-09-02 10:00":"2017-09-02 16:00"]
    print("\n=== CRITICAL 10:00-16:00 SOURCE + REANALYSIS ===")
    print(window[display].to_string(float_format=lambda x: f"{x:.5g}"))
    print("\n=== STRICT 2017 CANDIDATE RECORDS (EVIDENCE ONLY) ===")
    print(flagged[display + ["QBOT_stage37_review_only"]].to_string(
        float_format=lambda x: f"{x:.5g}"))
    print("\n=== 2017 INVALID INPUT RH (DO NOT EDIT BLINDLY) ===")
    bad = a.loc[(a.input_RH_pct < 0) | (a.input_RH_pct > 100)]
    print(bad[display].to_string(float_format=lambda x: f"{x:.5g}"))
    OUT.mkdir(parents=True, exist_ok=True)
    window.to_csv(OUT / "01_20170902_critical_source_and_reanalysis.csv",
                  index_label="time", float_format="%.12g")
    flagged.to_csv(OUT / "02_strict_QC1_candidate_review_only.csv",
                   index_label="time", float_format="%.12g")
    bad.to_csv(OUT / "03_2017_invalid_input_RH_review_only.csv",
               index_label="time", float_format="%.12g")
    (OUT / "04_summary.json").write_text(json.dumps({
        "status": "READ_ONLY_REVIEW_NOT_APPROVED_EDIT",
        "stage": 37, "case": "CH-Aws_FATES_SPINUP1000_RH34A",
        "job": "4594995",
        "strict_qc1_candidate_count": int(strict.sum()),
        "critical_2017_09_02_1230_matches_strict_screen": bool(strict.loc[EVENT]),
        "candidate_records": [str(x) for x in flagged.index],
        "fatal_model_RH_pct": -2.04867089950063,
        "source_year": 2017,
        "note": "Reanalysis is contextual, not tower validation. No files changed."
    }, indent=2) + "\n")
    print("\nReports:", OUT)
    print("READ-ONLY. No forcing, restart, CIME, or Slurm modifications.")


if __name__ == "__main__":
    main()

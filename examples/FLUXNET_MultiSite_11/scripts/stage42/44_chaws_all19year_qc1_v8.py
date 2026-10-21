#!/usr/bin/env python3
"""Stage42 CH-Aws all-19-year low-RH QC1 sensitivity, from verified v7 parent.

2006-2024 cyclic DATM: scan *all* years to avoid one-crash-one-year repairs.
Only residual source EUF_F, VPD_F_QC=1, forcing+source RH<10%, consensus
ERA5 and ERA5-Land>=30%, abs(reference gap)<=15pp, ERA5-Land minus
forcing RH>=20pp are eligible. Already corrected v5/v6/v7 rows cannot
be selected again because their ACTUAL parent v7 RH is no longer <10%.
Never edit QC0 or other forcing variables.

Modes:
  --audit --fetch-references: fetch reanalysis for years containing candidate
      RH<10% QC1 values; print full counts and differences, no NetCDF edits.
  --write --fetch-references: same preflight, then create NEW stage42 v8
      directory with independent NetCDF for changed years and parent symlinks
      for all other years. Refuses overwrite.
  --verify: verify existing output ledger and all original-vs-v8 variables.

This is an exploratory correlated-reanalysis sensitivity, NOT proof
the QC1 source records are erroneous. Does NOT submit Slurm/CIME work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing")
V7 = ROOT / "datm_11_stage38_qc1_21rh_sensitivity_v7"
V8 = ROOT / "datm_11_stage42_all19year_qc1_low10_sensitivity_v8"
SOURCE = ROOT / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
REPORT = Path.home() / "FLUXNET_MultiSite_11/stage42_CH_Aws_global_QC1_review"
LAT, LON = 46.583111, 9.790639
YEARS = tuple(range(2006, 2025))
VERSION = "STAGE42_ALL19YEAR_QC1_LOW10_SENSITIVITY_V8"
EVENT_2020 = pd.Timestamp("2020-08-04 12:00")
MAX_GLOBAL_EDITS = 400


def need(cond, msg):
    if not cond:
        raise RuntimeError("STOP: " + msg)


def digest(file):
    h = hashlib.sha256()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def es(tc):
    tc = np.asarray(tc, dtype=float)
    return 6.112 * np.exp(np.clip(17.67 * tc / (tc + 243.5), -100, 100))


def yearly_axis(ds, year):
    t = ds["time"]
    idx = pd.DatetimeIndex([str(v)[:19] for v in
        num2date(t[:], units=t.units, calendar=getattr(t, "calendar", "noleap"))])
    need(len(idx) == 17520 and idx.is_unique
         and (idx.year == year).all()
         and not ((idx.month == 2) & (idx.day == 29)).any(),
         f"{year} not 17520 half-hour NO_LEAP timestamps")
    return idx


def ref_validate(raw, model, year):
    need(raw.get("utc_offset_seconds") == 0, f"{model} {year}: timezone not UTC")
    h = raw.get("hourly", {})
    names = ("time", "temperature_2m", "dew_point_2m")
    n = len(pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h"))
    need(all(name in h and len(h[name]) == n for name in names),
         f"{model} {year}: incomplete hourly data")
    times = pd.DatetimeIndex(pd.to_datetime(h["time"], errors="raise"))
    need(times.equals(pd.date_range(f"{year}-01-01",
                                   f"{year}-12-31 23:00", freq="h")),
         f"{model} {year}: wrong hourly UTC clock")
    for name in names[1:]:
        need(np.isfinite(np.asarray(h[name], float)).all(),
             f"{model} {year}: nonfinite {name}")
    return times


def get_reference(model, year, fetch):
    path = CACHE / f"{model}_{year}.json"
    if path.is_file():
        raw = json.loads(path.read_text())
        ref_validate(raw, model, year)
        return raw, digest(path)
    need(fetch, f"Missing {model} {year}. Rerun with --fetch-references")
    CACHE.mkdir(parents=True, exist_ok=True)
    params = dict(latitude=LAT, longitude=LON,
                  start_date=f"{year}-01-01", end_date=f"{year}-12-31",
                  hourly="temperature_2m,dew_point_2m,relative_humidity_2m",
                  timezone="GMT", models=model)
    url = "https://archive-api.open-meteo.com/v1/archive?" + urlencode(params)
    last_error = None
    for attempt in range(3):
        try:
            print(f"DOWNLOAD {model} {year} attempt={attempt+1}", flush=True)
            req = Request(url, headers={"User-Agent": "CH-Aws-QC1-global-v8/1.0"})
            with urlopen(req, timeout=120) as r:
                blob = r.read()
            raw = json.loads(blob)
            need(not raw.get("error"), str(raw.get("reason", "API error")))
            ref_validate(raw, model, year)
            need(not path.exists(), f"Cache unexpectedly appeared: {path}")
            with tempfile.NamedTemporaryFile(dir=CACHE, prefix=".qc1_v8_",
                                             delete=False) as f:
                temp = Path(f.name)
                f.write(blob)
            try:
                need(not path.exists(), "Refusing cache overwrite")
                os.link(temp, path)  # O_EXCL equivalent; never replace cache
            finally:
                temp.unlink(missing_ok=True)
            return raw, digest(path)
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt+1))
    raise RuntimeError(f"Failed fetching {model} {year}: {last_error}")


def rh_reference(raw, model, year, desired):
    utc = ref_validate(raw, model, year)
    h = raw["hourly"]
    df = pd.DataFrame({
        "T": np.asarray(h["temperature_2m"], float),
        "Td": np.asarray(h["dew_point_2m"], float),
    }, index=utc + pd.Timedelta(hours=1))
    half = (df.reindex(df.index.union(desired)).sort_index()
            .interpolate(method="time", limit=1, limit_area="inside")
            .reindex(desired))
    return pd.Series(100 * es(half["Td"].to_numpy(float)) /
                     es(half["T"].to_numpy(float)), index=desired)


def read_year(year):
    path = V7 / f"CH-Aws_DATM_{year}.nc"
    need(path.is_file(), f"Missing v7 forcing: {path}")
    with Dataset(path) as ds:
        idx = yearly_axis(ds, year)
        data = {}
        for var in ("QBOT", "TBOT", "PSRF"):
            need(var in ds.variables, f"{year}: missing {var}")
            vals = np.ma.asarray(ds[var][:, 0, 0])
            need(not np.ma.getmaskarray(vals).any(), f"{year}: masked {var}")
            data[var] = np.asarray(vals, float)
            need(np.isfinite(data[var]).all(), f"{year}: nonfinite {var}")
        need((data["PSRF"] > 0).all(), "Nonphysical pressure " + str(year))
        return pd.DataFrame(data, index=idx)


def scan(fetch):
    need(V7.is_dir() and SOURCE.is_file(), "Verified v7/source forcing missing")
    parent_manifest = json.loads((V7 / "stage38_manifest.json").read_text())
    need(parent_manifest.get("version") ==
         "STAGE38_QC1_21ROW_SENSITIVITY_V7" and
         parent_manifest.get("modified_vs_v6") == 21,
         "Unexpected v7 parent provenance")
    need(digest(V7 / "stage38_21_QC1_ledger.csv") ==
         parent_manifest["ledger_sha256"], "Stage38 ledger changed")

    source = pd.read_csv(SOURCE,
                         usecols=["time", "TA_F", "PA_F", "VPD_F_SOURCE",
                                  "VPD_F_QC", "RH_IMPLIED_PCT"],
                         low_memory=False)
    source["time"] = pd.to_datetime(source["time"], errors="raise")
    need(source.time.is_unique and len(source) == 332880,
         "Unexpected source timestamp coverage")
    source = source.set_index("time")
    for k in ("TA_F", "PA_F", "VPD_F_QC", "RH_IMPLIED_PCT"):
        source[k] = pd.to_numeric(source[k], errors="coerce")

    all_selected = []
    summary = []
    refsha = {}
    parent_sha = {}
    all_lowqc0 = []
    for year in YEARS:
        dat = read_year(year)
        path = V7 / f"CH-Aws_DATM_{year}.nc"
        parent_sha[str(year)] = digest(path)
        src = source.reindex(dat.index)
        need(src.VPD_F_SOURCE.notna().all(),
             f"Source provenance missing {year}")
        actual_rh = (dat.QBOT.to_numpy() * dat.PSRF.to_numpy()
                     / (.622 + .378 * dat.QBOT.to_numpy()) /
                     es(dat.TBOT.to_numpy() - 273.15))
        dat["RH_input_pct"] = actual_rh
        dat = dat.join(src, validate="one_to_one")
        pre = (dat.VPD_F_SOURCE.eq("EUF_F") &
               dat.VPD_F_QC.eq(1) &
               dat.RH_IMPLIED_PCT.lt(10) &
               dat.RH_input_pct.lt(10))
        qc0 = dat.VPD_F_QC.eq(0) & dat.RH_input_pct.lt(10)
        lowqc0 = dat.loc[qc0, ["RH_input_pct", "VPD_F_QC", "VPD_F_SOURCE"]]
        if len(lowqc0):
            all_lowqc0.append(lowqc0)
        valid_era = {"era5": pd.Series(np.nan, index=dat.index),
                     "era5_land": pd.Series(np.nan, index=dat.index)}
        if pre.any():
            for model in ("era5", "era5_land"):
                raw, hashval = get_reference(model, year, fetch)
                refsha[f"{model}_{year}"] = hashval
                # Align the full year once, then select precise timestamps.
                valid_era[model] = rh_reference(raw, model, year, dat.index)
        era, land = valid_era["era5"], valid_era["era5_land"]
        strict = (
            pre & era.ge(30) & land.ge(30) &
            (era - land).abs().le(15) &
            (land - dat.RH_input_pct).ge(20)
        )
        selected = dat.loc[strict].copy()
        if not selected.empty:
            selected["era5_RH_pct"] = era.loc[strict].to_numpy(float)
            selected["era5_land_RH_pct"] = land.loc[strict].to_numpy(float)
            need(np.isfinite(selected[["TA_F", "PA_F", "era5_land_RH_pct"]].
                             to_numpy(float)).all(),
                 f"{year}: nonfinite QC1 selection values")
            positions = dat.index.get_indexer(selected.index)
            need(np.allclose(selected.TA_F.to_numpy(float),
                             selected.TBOT.to_numpy(float) - 273.15, rtol=0,
                             atol=.05),
                 f"{year}: selected TA source vs v7 mismatched")
            need(np.allclose(selected.PA_F.to_numpy(float) * 1000,
                             selected.PSRF.to_numpy(float), rtol=0, atol=100),
                 f"{year}: selected PA source vs v7 mismatched")
            need(np.allclose(selected.RH_IMPLIED_PCT.to_numpy(float),
                             selected.RH_input_pct.to_numpy(float),
                             rtol=0, atol=.05),
                 f"{year}: selected source RH vs v7 mismatched")
            # Same physical specific-humidity conversion as Stage38.
            vapor_pa = es(selected.TA_F.to_numpy(float)) * (
                selected.era5_land_RH_pct.to_numpy(float))
            ps_pa = selected.PA_F.to_numpy(float) * 1000
            newq = .622 * vapor_pa / (ps_pa - .378 * vapor_pa)
            need(np.isfinite(newq).all() and np.all(newq > 0)
                 and np.all(newq < .08), f"{year}: bad candidate QBOT")
            selected["QBOT_v8_candidate_kgkg"] = newq
            selected["delta_QBOT_kgkg"] = newq - selected.QBOT
            need(np.all(selected.delta_QBOT_kgkg > 0),
                 f"{year}: candidate humidity lower than parent")
            selected["year"] = year
            all_selected.append(selected)
        summary.append({
            "year": year, "source_QC1_low10_unfixed": int(pre.sum()),
            "strict_QC1_eligible": int(strict.sum()),
            "QC0_RH_below10_preserved": int(qc0.sum()),
            "forcing_RH_below10": int((dat.RH_input_pct < 10).sum()),
        })
        print(f"{year}: source QC1 low10={int(pre.sum())}, "
              f"strict={int(strict.sum())}, QC0 low10 preserved={int(qc0.sum())}",
              flush=True)

    selected = pd.concat(all_selected) if all_selected else pd.DataFrame()
    summary_frame = pd.DataFrame(summary)
    need(len(selected) <= MAX_GLOBAL_EDITS,
         f"Too many edits {len(selected)} > {MAX_GLOBAL_EDITS}, manual review required")
    twenty = selected.loc["2020"] if not selected.empty and
        any(selected.index.year == 2020) else pd.DataFrame()
    need(len(twenty) == 14,
         f"Expected 2020 Stage41 exact 14 strict rows, got {len(twenty)}")
    need(EVENT_2020 in selected.index,
         "2020-08-04 12:00 negative-RH precursor missing from strict selection")
    need(selected.index.is_unique,
         "Duplicate selected timestamps")

    return selected.sort_index(), summary_frame, refsha, parent_sha, (
        pd.concat(all_lowqc0) if all_lowqc0 else pd.DataFrame())


def manifest_of(selected, refsha, parent_sha, ledger_sha, original_sha):
    byyear = {str(y): int((selected.index.year == y).sum()) for y in YEARS}
    return {
        "site": "CH-Aws", "version": VERSION,
        "method": "Stage34 strict QC1, full 2006-2024 residual scan",
        "scientific_status": "EXPLORATORY_REANALYSIS_SENSITIVITY",
        "model_validation": "NOT RUN",
        "parent_version": "Stage38 v7", "modified_vs_v7": len(selected),
        "by_year": byyear,
        "source_csv_sha256": original_sha,
        "reference_sha256": refsha,
        "parent_annual_sha256": parent_sha,
        "ledger_sha256": ledger_sha,
        "candidate_event_times": [str(t) for t in selected.index],
        "note": "Original QC0 unchanged; all other forcing vars unchanged."
    }


def verify(selected, refsha, parentsha):
    need(V8.is_dir(), "No v8 output to verify")
    man = json.loads((V8 / "stage42_manifest.json").read_text())
    need(man.get("version") == VERSION and
         man.get("modified_vs_v7") == len(selected) and
         man.get("candidate_event_times") == [str(t) for t in selected.index],
         "v8 manifest version/count/timestamps mismatch")
    need(man["ledger_sha256"] == digest(V8 / "stage42_QC1_ledger.csv"),
         "v8 ledger hash changed")
    need(man["source_csv_sha256"] == digest(SOURCE),
         "Source candidate file changed")
    need(man["parent_annual_sha256"] == parentsha and
         man["reference_sha256"] == refsha,
         "Parent forcing or reanalysis hash changed since v8 write")
    for year in YEARS:
        name = f"CH-Aws_DATM_{year}.nc"
        p = V7 / name
        child = V8 / name
        need(child.is_file(), "Broken v8 annual path: " + name)
        selected_y = selected.loc[selected.index.year == year]
        if selected_y.empty:
            need(child.is_symlink() and child.resolve() == p.resolve(),
                 "Unchanged year must be parent symlink " + str(year))
            continue
        need(not child.is_symlink(), "Edited year is symlink " + str(year))
        with Dataset(p) as before, Dataset(child) as after:
            idx = yearly_axis(before, year)
            need(set(before.variables) == set(after.variables),
                 f"{year}: variable inventory changed")
            for var in before.variables:
                need(before[var].shape == after[var].shape,
                     f"{year}: dimension change {var}")
                if var != "QBOT":
                    need(np.ma.allequal(before[var][:], after[var][:]),
                         f"{year}: changed non-QBOT variable: {var}")
            a = np.asarray(before["QBOT"][:, 0, 0], np.float32)
            b = np.asarray(after["QBOT"][:, 0, 0], np.float32)
            expected_indices = set(idx.get_indexer(selected_y.index))
            changed_indices = set(np.flatnonzero(a != b))
            need(changed_indices == expected_indices,
                 f"{year}: unexpected QBOT modifications: "
                 f"expected {len(expected_indices)}, got {len(changed_indices)}")
            need(np.allclose(b[sorted(changed_indices)],
                             selected_y.QBOT_v8_candidate_kgkg.to_numpy(np.float32),
                             atol=1e-8, rtol=0),
                 f"{year}: QBOT numerical changes disagree with ledger")
    print(f"VERIFIED v8 all 19 years: {len(selected)} exact QBOT QC1 edits, "
          "all other variables preserved.")
    print("VERIFIED: all other years symlink unchanged to original v7 lineage.")


def write(selected, refsha, parentsha):
    need(not V8.exists() and not V8.is_symlink(),
         "v8 already exists; refusing overwrite")
    stage = Path(tempfile.mkdtemp(dir=ROOT, prefix=".CH_Aws_stage42_"))
    try:
        ledger = stage / "stage42_QC1_ledger.csv"
        selected.to_csv(ledger, index_label="time", float_format="%.12g")
        for year in YEARS:
            p = V7 / f"CH-Aws_DATM_{year}.nc"
            dst = stage / p.name
            subset = selected.loc[selected.index.year == year]
            if subset.empty:
                dst.symlink_to(p)
                continue
            shutil.copy2(p, dst)
            with Dataset(dst, "r+") as ds:
                idx = yearly_axis(ds, year)
                positions = idx.get_indexer(subset.index)
                need((positions >= 0).all(), "Missing selected time " + str(year))
                q = np.asarray(ds["QBOT"][:, 0, 0], np.float32)
                q[positions] = subset.QBOT_v8_candidate_kgkg.to_numpy(np.float32)
                ds["QBOT"][:, 0, 0] = q
                ds.setncattr("stage42_status", "EXPLORATORY_REANALYSIS_SENSITIVITY")
                ds.setncattr("stage42_modified_QBOT_rows_vs_v7", len(subset))
                ds.setncattr("stage42_parent_year_sha256", parentsha[str(year)])
        m = manifest_of(selected, refsha, parentsha, digest(ledger),
                        digest(SOURCE))
        (stage / "stage42_manifest.json").write_text(json.dumps(m, indent=2) + "\n")
        # Atomic rename only AFTER independent annual variable-by-variable
        # verification in the temporary output folder.
        for year in YEARS:
            p = V7 / f"CH-Aws_DATM_{year}.nc"
            dst = stage / p.name
            subset = selected.loc[selected.index.year == year]
            if subset.empty:
                need(dst.is_symlink() and dst.resolve() == p.resolve(),
                     "Unchanged link failure")
                continue
            with Dataset(p) as before, Dataset(dst) as after:
                idx = yearly_axis(before, year)
                for var in before.variables:
                    if var != "QBOT":
                        need(np.ma.allequal(before[var][:], after[var][:]),
                             f"{year}: non-QBOT variable changed {var}")
                x = np.asarray(before["QBOT"][:, 0, 0], np.float32)
                y = np.asarray(after["QBOT"][:, 0, 0], np.float32)
                need(set(np.flatnonzero(x != y)) ==
                     set(idx.get_indexer(subset.index)),
                     f"{year}: wrong modified half-hours")
        need(not V8.exists(), "Refusing overwrite: v8 created during preparation")
        os.rename(stage, V8)
        print("CREATED NEW STAGE42 V8:", V8)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--audit", action="store_true")
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    ap.add_argument("--fetch-references", action="store_true")
    args = ap.parse_args()
    selected, summary, refsha, parentsha, qc0 = scan(args.fetch_references)
    REPORT.mkdir(parents=True, exist_ok=True)
    summary.to_csv(REPORT / "01_global_yearly_summary.csv", index=False)
    selected.to_csv(REPORT / "02_selected_QC1_review_only.csv",
                    index_label="time", float_format="%.12g")
    qc0.to_csv(REPORT / "03_QC0_lowRH_preserved.csv",
               index_label="time", float_format="%.12g")
    print("\n=== GLOBAL REVIEW ===")
    print(summary.to_string(index=False))
    print("Existing v7 kept untouched. Total NEW candidate QC1 half-hours:",
          len(selected))
    print("2020 strictly screened records:",
          int((selected.index.year == 2020).sum()))
    print("QC0 low RH preserved for separate source review:", len(qc0))
    print("Reports in HOME:", REPORT)
    if args.write:
        write(selected, refsha, parentsha)
        verify(selected, refsha, parentsha)
    elif args.verify:
        verify(selected, refsha, parentsha)
    else:
        print("AUDIT ONLY: no new forcing created")
    print("No original forcing, CIME, restart, or Slurm job modified.")


if __name__ == "__main__":
    main()

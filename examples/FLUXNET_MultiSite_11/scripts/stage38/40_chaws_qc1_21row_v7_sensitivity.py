#!/usr/bin/env python3
"""Stage38: provisional, non-overwriting CH-Aws 2017 QC1 humidity sensitivity v7.

This follows Stage29 v5 (77 QC2 rows) and Stage34 v6 (27 QC1 rows in
2007/2008). Stage37 identified exactly 21 low-RH QC1 half-hours in
2017, including 2017-09-02 12:30 (near the RH34A negative 2m-RH abort).

--audit: read-only preflight, list candidate records. DEFAULT.
--write --acknowledge-reanalysis-uncertainty: create a NEW v7 directory
  (2017 independent NetCDF + 18 symlinks to v6), never overwrite.
--verify: read-only comparison of v7 to parent v6; assert exactly 21
  QBOT half-hours changed and no other variable changed.

ERA5 and ERA5-Land are related reanalyses, NOT station observations.
This is a scientifically PROVISIONAL forcing SENSITIVITY, not proof of
faulty QC1 measurements or of success in the CLM-FATES model.
The current RH34A CIME case, restarts and Slurm jobs are NEVER touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing")
V6 = ROOT / "datm_11_stage34_qc1_27rh_sensitivity_v6"
V7 = ROOT / "datm_11_stage38_qc1_21rh_sensitivity_v7"
SOURCE = ROOT / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
YEARS = range(2006, 2025)
TARGET_YEAR = 2017
FNAME = "CH-Aws_DATM_2017.nc"
EXPECTED = tuple(pd.to_datetime([
    "2017-05-20 10:30", "2017-08-12 09:30", "2017-08-12 10:00",
    "2017-09-02 12:00", "2017-09-02 12:30",
    "2017-09-02 13:30", "2017-09-02 14:00", "2017-09-02 14:30",
    "2017-09-03 09:30", "2017-10-22 16:00", "2017-10-22 16:30",
    "2017-10-22 17:00", "2017-10-22 17:30",
    "2017-10-23 02:30", "2017-10-23 03:00", "2017-10-23 03:30",
    "2017-10-23 04:00", "2017-10-23 04:30", "2017-10-23 05:00",
    "2017-10-23 15:00", "2017-10-23 15:30",
]))


def require(ok, reason):
    if not ok:
        raise RuntimeError("STOP: " + reason)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def es_hpa(tc):
    tc = np.asarray(tc, dtype=float)
    return 6.112 * np.exp(np.clip(17.67 * tc / (tc + 243.5), -100, 100))


def annual_axis(nc, year):
    tv = nc["time"]
    idx = pd.DatetimeIndex([
        str(v)[:19] for v in num2date(
            tv[:], units=tv.units, calendar=getattr(tv, "calendar", "noleap"))
    ])
    require(len(idx) == 17520 and idx.is_unique and (idx.year == year).all(),
            f"{year}: unexpected noleap half-hour axis")
    return idx


def reference(model, desired):
    path = CACHE / f"{model}_2017.json"
    require(path.is_file(), "2017 reanalysis reference missing: " + str(path))
    obj = json.loads(path.read_text())
    require(obj.get("utc_offset_seconds") == 0, "Reanalysis not UTC: " + str(path))
    hourly = obj["hourly"]
    keys = ("time", "temperature_2m", "dew_point_2m")
    require(all(k in hourly and len(hourly[k]) == 8760 for k in keys),
            "Incomplete reanalysis year: " + str(path))
    utc = pd.DatetimeIndex(pd.to_datetime(hourly["time"], errors="raise"))
    require(utc.equals(pd.date_range("2017-01-01", "2017-12-31 23:00", freq="h")),
            "Unexpected reanalysis hourly clock: " + str(path))
    hourly_df = pd.DataFrame({
        "T": pd.to_numeric(pd.Series(hourly["temperature_2m"]),
                           errors="coerce").to_numpy(float),
        "Td": pd.to_numeric(pd.Series(hourly["dew_point_2m"]),
                            errors="coerce").to_numpy(float),
    }, index=utc + pd.Timedelta(hours=1))
    require(np.isfinite(hourly_df.to_numpy()).all(), "Nonfinite reanalysis " + model)
    x = (hourly_df.reindex(hourly_df.index.union(desired)).sort_index()
         .interpolate(method="time", limit=1, limit_area="inside")
         .reindex(desired))
    require(x.loc["2017-09-01":"2017-09-04"].notna().all().all(),
            model + " missing data in critical event window")
    # At 2017-01-01 00:00/00:30 local standard time, 2016 UTC
    # would be needed; keep absent endpoints NaN, never invent values.
    return pd.Series(100 * es_hpa(x["Td"].to_numpy(float))
                     / es_hpa(x["T"].to_numpy(float)),
                     index=desired, dtype=float)


def assess():
    require(V6.is_dir() and SOURCE.is_file(), "Missing v6 or original source")
    meta = json.loads((V6 / "stage34_manifest.json").read_text())
    require(meta.get("version") == "STAGE34_QC1_27ROW_SENSITIVITY_V6"
            and meta.get("modified_vs_v5") == 27,
            "Unexpected v6 parent manifest")
    require((V6 / FNAME).is_symlink(), "2017 v6 parent is not expected symlink")
    for y in YEARS:
        require((V6 / f"CH-Aws_DATM_{y}.nc").is_file(),
                f"Missing parent v6 year {y}")
    status_path = SOURCE.parent / "status.json"
    require(status_path.is_file(), "Source CSV status.json missing")
    source_sha = sha256(SOURCE)
    require(json.loads(status_path.read_text()).get("candidate_sha256") == source_sha,
            "RH25A original source CSV hash changed")

    with Dataset(V6 / FNAME) as nc:
        axis = annual_axis(nc, TARGET_YEAR)
        q = np.asarray(nc["QBOT"][:, 0, 0], dtype=float)
        temp = np.asarray(nc["TBOT"][:, 0, 0], dtype=float)
        pressure = np.asarray(nc["PSRF"][:, 0, 0], dtype=float)
        require(np.isfinite(q).all() and np.isfinite(temp).all()
                and np.isfinite(pressure).all() and (pressure > 0).all(),
                "2017 parent forcing includes nonfinite or nonphysical input")

    usecols = ["time", "TA_F", "PA_F", "VPD_F_SOURCE", "VPD_F_QC",
               "RH_IMPLIED_PCT"]
    source = pd.read_csv(SOURCE, usecols=usecols, low_memory=False)
    source["time"] = pd.to_datetime(source["time"], errors="raise")
    require(len(source) == 332880 and source.time.is_unique,
            "Original 19-year source timeline changed")
    source = source.set_index("time").reindex(axis)
    require(source.VPD_F_SOURCE.notna().all(), "2017 source flags missing")
    for k in ("TA_F", "PA_F", "VPD_F_QC", "RH_IMPLIED_PCT"):
        source[k] = pd.to_numeric(source[k], errors="coerce")
    input_rh = 100 * (q * pressure / (.622 + .378 * q)) / (100 * es_hpa(temp - 273.15))
    a = source.copy()
    a["QBOT_v6_kgkg"] = q
    a["input_RH_v6_pct"] = input_rh
    a["era5_RH_pct"] = reference("era5", axis).to_numpy(float)
    a["era5_land_RH_pct"] = reference("era5_land", axis).to_numpy(float)
    a["reference_gap_pp"] = abs(a.era5_RH_pct - a.era5_land_RH_pct)
    a["land_minus_input_pp"] = a.era5_land_RH_pct - a.input_RH_v6_pct
    strict = (
        a.VPD_F_SOURCE.eq("EUF_F")
        & a.VPD_F_QC.eq(1)
        & a.RH_IMPLIED_PCT.lt(10)
        & a.input_RH_v6_pct.lt(10)
        & a.era5_RH_pct.ge(30)
        & a.era5_land_RH_pct.ge(30)
        & a.reference_gap_pp.le(15)
        & a.land_minus_input_pp.ge(20)
    )
    selected = a.loc[strict].copy()
    require(len(selected) == len(EXPECTED) == 21,
            f"Wrong strict 2017 QC1 selection: {len(selected)} instead of 21")
    require(tuple(selected.index) == EXPECTED,
            "Stage37 candidate event timestamps differ; STOP without edits")
    require(np.isfinite(selected[["TA_F", "PA_F", "RH_IMPLIED_PCT"]].to_numpy(float)).all(),
            "Selected source meteorology nonfinite")
    positions = axis.get_indexer(selected.index)
    require((positions >= 0).all(), "Selected event missing from NetCDF")
    require(np.allclose(selected.TA_F.to_numpy(float),
                        temp[positions] - 273.15, rtol=0, atol=.05),
            "Selected source TA disagrees with actual v6 TBOT")
    require(np.allclose(selected.PA_F.to_numpy(float) * 1000,
                        pressure[positions], rtol=0, atol=100),
            "Selected source pressure disagrees with actual v6 PSRF")
    require(np.allclose(selected.RH_IMPLIED_PCT.to_numpy(float),
                        input_rh[positions], rtol=0, atol=.05),
            "Selected source RH differs from v6 QBOT")

    site_es = es_hpa(selected.TA_F.to_numpy(float))  # hPa
    reference_rh = selected.era5_land_RH_pct.to_numpy(float)
    ea_pa = site_es * reference_rh  # hPa * percentage = Pa
    pressure_pa = selected.PA_F.to_numpy(float) * 1000
    newq = .622 * ea_pa / (pressure_pa - .378 * ea_pa)
    require(np.isfinite(newq).all() and ((newq > 0) & (newq < .08)).all(),
            "Nonphysical candidate QBOT")
    selected["QBOT_v7_candidate_kgkg"] = newq
    selected["delta_QBOT_kgkg"] = newq - selected.QBOT_v6_kgkg
    require((selected.delta_QBOT_kgkg > 0).all(),
            "Stage38 candidate would unexpectedly dry some records")
    return selected, source_sha


def verify(selected, source_sha):
    require(V7.is_dir(), "No Stage38 v7 candidate written: " + str(V7))
    mpath = V7 / "stage38_manifest.json"
    require(mpath.is_file(), "v7 manifest missing")
    m = json.loads(mpath.read_text())
    require(m.get("version") == "STAGE38_QC1_21ROW_SENSITIVITY_V7"
            and m.get("modified_vs_v6") == 21
            and m.get("source_sha256") == source_sha,
            "Unexpected v7 manifest")
    require(m.get("parent_2017_sha256") == sha256(V6 / FNAME),
            "Parent 2017 v6 changed since candidate creation")
    require(m.get("candidate_event_times") == [str(t) for t in selected.index],
            "Candidate timestamps changed since write")
    require(m.get("ledger_sha256") == sha256(V7 / "stage38_21_QC1_ledger.csv"),
            "Candidate ledger changed")
    for y in YEARS:
        parent = V6 / f"CH-Aws_DATM_{y}.nc"
        candidate = V7 / parent.name
        require(candidate.is_file(), f"Broken v7 annual forcing: {y}")
        if y != 2017:
            require(candidate.is_symlink() and candidate.resolve() == parent.resolve(),
                    f"{y}: v7 should link unchanged v6 file")
            continue
        require(not candidate.is_symlink(), "2017 v7 must be an independent NetCDF")
        with Dataset(parent) as old, Dataset(candidate) as new:
            axis = annual_axis(new, 2017)
            require(set(old.variables) == set(new.variables),
                    "v7 unexpected variable inventory")
            for var in old.variables:
                if var == "QBOT":
                    continue
                require(np.ma.allequal(old[var][:], new[var][:]),
                        "Unexpected change to " + var + " in 2017")
            x = np.asarray(old["QBOT"][:, 0, 0], dtype=np.float32)
            yvals = np.asarray(new["QBOT"][:, 0, 0], dtype=np.float32)
            changed = set(np.flatnonzero(x != yvals))
            expected_indices = set(axis.get_indexer(selected.index))
            require(changed == expected_indices,
                    f"Unexpected QBOT edits, expected 21 got {len(changed)}")
            require(np.allclose(yvals[list(sorted(changed))],
                                selected.QBOT_v7_candidate_kgkg.to_numpy(
                                    dtype=np.float32), rtol=0, atol=1e-8),
                    "Candidate QBOT values disagree with Stage38 calculation")
    print("VERIFIED: 2017 has exactly 21 QC1 QBOT edits; all other variables unchanged.")
    print("VERIFIED: 18 other annual files are symlinks to v6.")
    print("VERIFIED: source/parent SHA256 and ledger unchanged.")
    print("VALIDATION STATUS: forcing overlay verified, CLM-FATES model not yet run.")


def write(selected, source_sha):
    require(not V7.exists(), "Refusing to overwrite existing v7 directory: " + str(V7))
    stage = Path(tempfile.mkdtemp(prefix=".CH_Aws_stage38_", dir=ROOT))
    try:
        ledger = stage / "stage38_21_QC1_ledger.csv"
        selected.to_csv(ledger, index_label="time", float_format="%.12g")
        for year in YEARS:
            name = f"CH-Aws_DATM_{year}.nc"
            parent = V6 / name
            dst = stage / name
            if year != 2017:
                dst.symlink_to(parent)
                continue
            # copy2 follows the v6->v5 2017 symlink; parent remains read-only
            shutil.copy2(parent, dst)
            require(not dst.is_symlink(), "Unexpected copied 2017 symlink")
            with Dataset(dst, "r+") as ds:
                ix = annual_axis(ds, 2017).get_indexer(selected.index)
                require((ix >= 0).all(), "2017 candidate times missing")
                q = np.asarray(ds["QBOT"][:, 0, 0], dtype=np.float32)
                q[ix] = selected.QBOT_v7_candidate_kgkg.to_numpy(np.float32)
                ds["QBOT"][:, 0, 0] = q
                ds.setncattr("stage38_status", "PROVISIONAL_REANALYSIS_SENSITIVITY_NOT_VALIDATED")
                ds.setncattr("stage38_parent_2017_sha256", sha256(parent))
                ds.setncattr("stage38_ledger_sha256", sha256(ledger))
                ds.setncattr("stage38_modified_QBOT_rows_vs_v6", 21)
                ds.setncattr("stage38_note",
                              "Only 2017 QC1 QBOT changed; parent v6 and QC0 preserved")
        m = {
            "site": "CH-Aws", "version": "STAGE38_QC1_21ROW_SENSITIVITY_V7",
            "scientific_status": "EXPLORATORY_NOT_TOWER_VALIDATED",
            "modified_vs_v6": 21, "year_modified": 2017,
            "cumulative_prior_candidates_v5_plus_v6": 104,
            "source_sha256": source_sha,
            "parent_2017_sha256": sha256(V6 / FNAME),
            "reference_sha256": {
                model: sha256(CACHE / f"{model}_2017.json")
                for model in ("era5", "era5_land")
            },
            "candidate_event_times": [str(t) for t in selected.index],
            "ledger_sha256": sha256(ledger),
            "dependency": "18 annual symlinks refer to Stage34 v6, which itself depends on v5/v3. Do not delete parents.",
            "model_validation": "NOT RUN",
            "note": "No RH floor, no QC0 edits, no automatic CIME/Slurm action."
        }
        (stage / "stage38_manifest.json").write_text(json.dumps(m, indent=2) + "\n")
        # Before rename, verify the 2017 NetCDF locally.
        with Dataset(V6 / FNAME) as old, Dataset(stage / FNAME) as new:
            orig = np.asarray(old["QBOT"][:, 0, 0], np.float32)
            newer = np.asarray(new["QBOT"][:, 0, 0], np.float32)
            expect = set(annual_axis(new, 2017).get_indexer(selected.index))
            require(set(np.flatnonzero(orig != newer)) == expect,
                    "Unexpected QBOT modification before finalizing output")
            for name in old.variables:
                if name != "QBOT":
                    require(np.ma.allequal(old[name][:], new[name][:]),
                            "Unexpected non-QBOT modifications: " + name)
        # Fail closed if output path appeared while processing.
        require(not V7.exists(), "v7 appeared during preparation: abort")
        os.rename(stage, V7)
        print("NEW STAGE38 V7 candidate created:", V7)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--audit", action="store_true", help="Default: read-only")
    group.add_argument("--write", action="store_true", help="Create new v7, never overwrite")
    group.add_argument("--verify", action="store_true", help="Read-only full v7 verification")
    ap.add_argument("--acknowledge-reanalysis-uncertainty", action="store_true")
    args = ap.parse_args()
    selected, source_sha = assess()
    print("=== STAGE38 PROVISIONAL CH-AWS 2017 RH SENSITIVITY ===")
    print("Stage34 v6 -> Stage38 v7 candidate: exactly", len(selected), "QC1 half-hours.")
    cols = ["RH_IMPLIED_PCT", "era5_RH_pct", "era5_land_RH_pct",
            "QBOT_v6_kgkg", "QBOT_v7_candidate_kgkg"]
    print(selected[cols].to_string(float_format=lambda z: f"{z:.7g}"))
    if args.verify:
        verify(selected, source_sha)
    elif args.write:
        require(args.acknowledge_reanalysis_uncertainty,
                "--write requires --acknowledge-reanalysis-uncertainty")
        write(selected, source_sha)
        verify(selected, source_sha)
    else:
        print("AUDIT ONLY: no files written; use explicit --write flag to create an independent v7 sensitivity.")
    print("No case, restart, executable, existing forcing or Slurm job was modified.")


if __name__ == "__main__":
    main()

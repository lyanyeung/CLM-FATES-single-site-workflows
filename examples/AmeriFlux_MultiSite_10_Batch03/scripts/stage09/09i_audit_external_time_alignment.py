#!/usr/bin/env python3
"""Batch03 Stage09i: strictly READ-ONLY, 32-site-year clock sensitivity audit.

Compare tower TA_F and release-provided ERA5 TA_ERA to the 32 independently
downloaded ERA5-Land UTC t2m products at native-interval midpoints. Test only
documented BIF UTC_OFFSET +/- 1 hour; US-Me2 tests -9/-8/-7 as UNAPPROVED
hypotheses because this exact FULLSET has no release BIF.

A lower temperature mismatch is NOT authorization to select a timezone:
terrain, grid-cell mismatch, missing observations and ERA5 dependencies may
bias the comparison. No external dewpoint is used to repair any variable.
Neither mode writes a file, modifies sources/cases/DATM, or starts model jobs.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

sys.dont_write_bytecode = True
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE09A = ROOT / "reports/stage09a_external_dewpoint_plan_20261022T034051Z_437c9c0c"
SITES_TSV = Path(__file__).resolve().parents[2] / "sites.tsv"
QUEUE = Path(__file__).with_name("09f_incremental_dewpoint_queue.py")
PUBLISHED = {
    "US-Kon": -6, "US-MMS": -5, "US-Me6": -8,
    "US-MtB": -7, "US-NR1": -7, "US-NR3": -7
}
BIF_SHA = {
    "US-Kon": "d9e6548567558b89968ebd3986e436a7651be1fe8435b11f7c714aef87fe66d0",
    "US-MMS": "1f8581489a2b5bdbc4d0aecd8ae78dcefd8c5ab809a5300da6b146038d9ccc58",
    "US-Me6": "e8db4c98b646d730a371d37e6046a3c8e02ffd719ae81f3f3dab9a4ee895d554",
    "US-MtB": "0843108555fc2ebfffefb076a54b657291874822d38bbee6fa6891b184a5f275",
    "US-NR1": "8e97de15995f85f3d438ef3b1c076ec100fd39d1fb565ef9dc1614b85efa1232",
    "US-NR3": "e02c9b6b97ba89ac9e1a70faeb73eeec06d96455d3b6d3dc7c537b774f578d44",
}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def require_file(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing/symlink file: " + str(path))
    return path


def load_queue():
    require_file(QUEUE)
    spec = importlib.util.spec_from_file_location("batch03_stage09f_clock", QUEUE)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load Stage09f")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_manifest():
    with require_file(SITES_TSV).open(encoding="utf-8", newline="") as f:
        items = list(csv.DictReader(f, delimiter="\t"))
    if len(items) != 10 or len({r["site"] for r in items}) != 10:
        raise ValueError("Unexpected Batch03 site manifest")
    return {r["site"]: r for r in items}


def verify_sources():
    if not (STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage07 scientific hold marker missing")
    obj = json.loads(require_file(STAGE07 / "exact_input_manifest.json").read_text())
    sel = {s["site"]: s for s in obj["sites"]}
    pins = {str(Path(p).resolve()): d for p, d in obj["input_sha256"].items()}
    manifests = read_manifest()
    if set(sel) != set(manifests) or not set(PUBLISHED).issubset(sel) or "US-Me2" not in sel:
        raise ValueError("Selected release manifest does not match the ten-site scope")
    for site in sorted(set(PUBLISHED) | {"US-Me2"}):
        info = sel[site]
        if info["release"] != manifests[site]["package"]:
            raise ValueError("Selected package mismatch: " + site)
        original = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE") / site / "forcing/raw" / info["release"]
        if original.is_symlink() or not original.is_dir():
            raise ValueError("Expected release directory missing: " + site)
        for kind in ("primary", "era"):
            path = require_file(Path(info[kind]))
            if path.resolve().parent != original.resolve():
                raise ValueError("Source outside exact release: " + str(path))
            expected = pins.get(str(path.resolve()))
            if expected is None or expected != sha(path):
                raise ValueError("Pinned Stage07 source SHA changed: " + str(path))
        bifs = sorted(original.glob(f"AMF_{site}_FLUXNET_BIF_*.csv"))
        if site == "US-Me2":
            if bifs:
                raise ValueError("US-Me2 release now has a BIF; first review metadata before continuation")
        else:
            if len(bifs) != 1 or sha(require_file(bifs[0])) != BIF_SHA[site]:
                raise ValueError("Published BIF SHA or count changed for: " + site)
            with bifs[0].open(encoding="utf-8-sig", newline="") as f:
                entries = [r for r in csv.DictReader(f)
                           if (r.get("VARIABLE") or "").strip().upper() == "UTC_OFFSET"]
            if len(entries) != 1 or float(entries[0]["DATAVALUE"]) != PUBLISHED[site]:
                raise ValueError("BIF UTC_OFFSET changed or ambiguous: " + site)
    return sel


def grid_t2m(path, year):
    wanted = pd.date_range(
        f"{year-1}-12-29 00:00:00", f"{year+1}-01-03 23:00:00", freq="h")
    got = []
    def take(ds):
        var = ds.variables.get("valid_time", ds.variables.get("time"))
        if var is None:
            raise ValueError("Grid time coordinate missing")
        dates = num2date(
            var[:], var.units, calendar=getattr(var, "calendar", "standard"),
            only_use_cftime_datetimes=False, only_use_python_datetimes=True)
        index = pd.DatetimeIndex(pd.to_datetime([str(x) for x in dates]))
        if not index.equals(wanted):
            raise ValueError("ERA5-Land clock does not match verified UTC hourly grid")
        if "t2m" not in ds.variables:
            return
        fld = ds.variables["t2m"]
        if getattr(fld, "units", "") != "K":
            raise ValueError("Grid t2m is not Kelvin")
        values = np.asarray(np.ma.asarray(fld[:]).filled(np.nan), dtype=float).reshape(-1)
        if len(values) != len(wanted) or not np.isfinite(values).all():
            raise ValueError("Invalid hourly grid t2m")
        got.append(values - 273.15)

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise ValueError("ZIP CRC failure")
            for member in z.infolist():
                if not member.filename.endswith(".nc"):
                    continue
                if member.file_size > 100_000_000 or member.filename.startswith("/") or ".." in Path(member.filename).parts:
                    raise ValueError("Unsafe ZIP member")
                with Dataset("memory.nc", "r", memory=z.read(member)) as ds:
                    take(ds)
    elif path.suffix == ".nc":
        with Dataset(str(path)) as ds:
            take(ds)
    else:
        raise ValueError("Unrecognized verified ERA5-Land product")
    if len(got) != 1:
        raise ValueError("Expected exactly one verified t2m field: " + str(path))
    return wanted, got[0]


def raw_temperature(info, year, kind):
    path = Path(info[kind])
    raw_header = set(pd.read_csv(path, nrows=0).columns)
    temp = "TA_F" if kind == "primary" else "TA_ERA"
    qc = "TA_F_QC" if kind == "primary" and "TA_F_QC" in raw_header else None
    columns = ["TIMESTAMP_START", temp] + ([qc] if qc else [])
    if not set(columns).issubset(raw_header):
        raise ValueError("Selected source lacks required columns: " + str(path))
    frame = pd.read_csv(path, usecols=columns, dtype={"TIMESTAMP_START": str}, low_memory=False)
    frame = frame.loc[frame["TIMESTAMP_START"].str[:4] == str(year)].copy()
    frame["time"] = pd.to_datetime(frame["TIMESTAMP_START"], format="%Y%m%d%H%M", errors="raise")
    # Fixed native 3-hour sampling avoids weighting HH sites 2x HR sites.
    samples = frame.loc[(frame["time"].dt.hour % 3 == 0) & (frame["time"].dt.minute == 0)].copy()
    samples["t"] = pd.to_numeric(samples[temp], errors="coerce")
    samples = samples.loc[np.isfinite(samples["t"]) & samples["t"].between(-65, 55)]
    method = "VALID_FIELD_NOT_INDEPENDENT_QC"
    if qc:
        qc0 = samples.loc[pd.to_numeric(samples[qc], errors="coerce") == 0].copy()
        if len(qc0) >= 60:
            samples = qc0
            method = "QC0_ONLY"
        else:
            method = f"QC0_INSUFFICIENT_{len(qc0)}_USING_VALID_FIELD_FOR_SENSITIVITY"
    if samples.time.duplicated().any():
        raise ValueError("Unexpected duplicated native timestamp")
    return samples[["time", "t"]].set_index("time"), method


def interpolate_at(grid_index, grid_values, local_index, native_minutes, offset):
    target = pd.DatetimeIndex(local_index) + pd.Timedelta(minutes=native_minutes / 2)
    target = target - pd.Timedelta(hours=offset)
    grid_seconds = grid_index.asi8.astype(np.float64) / 1e9
    target_seconds = target.asi8.astype(np.float64) / 1e9
    if len(target_seconds) and (target_seconds.min() < grid_seconds.min() or target_seconds.max() > grid_seconds.max()):
        raise ValueError("Provisional midpoint outside downloaded UTC grid")
    return np.interp(target_seconds, grid_seconds, grid_values)


def median_absolute(a, b):
    if len(a) == 0:
        return None
    return float(np.median(np.abs(a-b)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Verify source pins and all 32 downloaded products; read-only")
    mode.add_argument("--analyze", action="store_true", help="Read-only all-site-year hourly alignment sensitivities")
    args = ap.parse_args()
    print("STAGE09I — READ-ONLY RELEASE CLOCK SENSITIVITY", flush=True)
    print("No timestamps altered; no forcing/DATM/case/restart/slurm writes.", flush=True)
    src = verify_sources()
    queue = load_queue()
    plan = queue.read_source()
    clock = json.loads(require_file(STAGE09A / "site_utc_offset_inventory.json").read_text())
    clk = {r["site"]: r for r in clock}
    if len(plan) != 32 or sum(int(x["blocked_native_records"]) for x in plan) != 1924 or set(clk) != set(PUBLISHED) | {"US-Me2"}:
        raise ValueError("Unexpected pinned Stage09a source scope")
    for site, row in clk.items():
        offsets = {str(x).strip() for x in row.get("published_utc_offsets", [])}
        if site in PUBLISHED:
            if offsets != {str(PUBLISHED[site])} or row["status"] != "ONE_PUBLISHED_OFFSET_PENDING_VALIDATION":
                raise ValueError("Stage09a clock metadata changed: " + site)
        elif offsets or row["status"] != "NO_RELEASE_BIF_FULLSET_SITE_METADATA_REQUIRED":
            raise ValueError("US-Me2 missing-BIF clock status changed")

    statuses = []
    for r in plan:
        state, meta = queue.check_artifact(r)
        if state != "VERIFIED":
            raise ValueError(f"Stage09f artifact not verified: {r['site']} {r['year']} ({state})")
        statuses.append((r, meta))
    print("STAGE09I PREFLIGHT: 7/7 source clocks inventoried, 14/14 met/ERA source SHA verified, "
          "32/32 ERA5-Land archives verified, evidence 1924/1924.", flush=True)
    print("CLOCK STATUS: BIF-published=6; formally approved=0; US-Me2=-8 is a hypothesis only.", flush=True)
    if args.check:
        print("CHECK ONLY: no reports, files, conversions, or jobs created.")
        return

    aggregate = {}
    for site in sorted(clk):
        records = [(r, m) for r, m in statuses if r["site"] == site]
        base = PUBLISHED.get(site, -8)
        offsets = [base-1, base, base+1]
        acc = {o: {"tower": [], "era": [], "tower_n": 0, "era_n": 0} for o in offsets}
        year_summary = []
        for r, meta in sorted(records, key=lambda z: int(z[0]["year"])):
            year = int(r["year"])
            info = src[site]
            primary, pmethod = raw_temperature(info, year, "primary")
            companion, _ = raw_temperature(info, year, "era")
            product = queue.ARCHIVE / site / str(year) / meta["name"]
            grid_times, grid_t = grid_t2m(require_file(product), year)
            for offset in offsets:
                for label, source in (("tower", primary), ("era", companion)):
                    predicted = interpolate_at(grid_times, grid_t, source.index, int(info["native_minutes"]), offset)
                    valid = np.isfinite(predicted) & np.isfinite(source["t"].to_numpy(dtype=float))
                    if valid.any():
                        residual = source["t"].to_numpy(dtype=float)[valid] - predicted[valid]
                        acc[offset][label].append(np.abs(residual))
                        acc[offset][label + "_n"] += len(residual)
            year_summary.append((year, len(primary), len(companion), pmethod))
            print(f"  VERIFIED {site} {year}: evidence_blockers={r['blocked_native_records']} "
                  f"tower_samples={len(primary)} ERA_samples={len(companion)} method={pmethod}", flush=True)
        print(f"\n=== {site} | native={src[site]['native_minutes']} min | "
              f"BIF_OFFSET={'NONE' if site == 'US-Me2' else base} "
              f"| years={len(records)} ===")
        ranking = []
        for offset in offsets:
            item = acc[offset]
            metrics = {}
            for kind in ("tower", "era"):
                parts = item[kind]
                value = float(np.median(np.concatenate(parts))) if parts else float("nan")
                metrics[kind] = value
            ranking.append((offset, item["tower_n"], metrics["tower"], item["era_n"], metrics["era"]))
            print(f"  HYPOTHETICAL_OFFSET={offset:+d} | tower n={item['tower_n']} "
                  f"median_abs_T_C={metrics['tower']:.3f} | native_ERA5 n={item['era_n']} "
                  f"median_abs_T_C={metrics['era']:.3f}")
        aggregate[site] = ranking
        print("  INTERPRETATION: diagnostics only; grid elevation, coverage/QC and shared ERA5 provenance prevent automatic clock selection.")
    print("\n" + "="*100)
    print(f"STAGE09I SUMMARY: sites={len(aggregate)} site_years={len(statuses)}/32 "
          "source_event_evidence=1924/1924 offsets_approved=0")
    print("US-Me2: -9/-8/-7 remain UNAPPROVED hypotheses; obtain exact site BADM/release clock metadata.")
    print("NO FORCING REPAIRED. NO DATM, CASE, MODEL OR FILE WRITES. Science hold remains.")
    print("="*100)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE09I STOP:", str(exc), file=sys.stderr, flush=True)
        sys.exit(2)

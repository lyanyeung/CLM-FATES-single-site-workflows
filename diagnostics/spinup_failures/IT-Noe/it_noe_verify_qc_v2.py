#!/usr/bin/env python3
"""Read-only post-write verification of IT-Noe 22-year QC-v2 candidate.

This script validates provenance, changes, annual model forcing and physical
bounds. It NEVER approves forcing or touches CIME, restart, NetCDF, or Slurm.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from netCDF4 import Dataset

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing")
OLD = BASE / "datm_11_provisional_dynamic_zbot_v1"
FIELDS = ("TBOT", "QBOT", "PSRF")

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1048576), b""):
            h.update(c)
    return h.hexdigest()

def values(ds, key):
    return np.ma.asarray(ds.variables[key][:]).filled(np.nan)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--forcing", type=Path, required=True)
    p.add_argument("--original", type=Path, default=OLD)
    p.add_argument("--max-temperature-jump", type=float, default=8)
    a = p.parse_args()
    problems, notes, summary = [], [], []
    root = a.forcing
    manifest = root / "CANDIDATE_PROVENANCE.json"
    if not root.is_dir() or not manifest.is_file():
        p.error("Missing candidate directory or provenance")
    receipt = json.loads(manifest.read_text())
    if receipt.get("status") != "UNAPPROVED_QC_SENSITIVITY":
        problems.append("Unexpected candidate provenance status")
    if Path(receipt.get("forcing_directory", "/missing")).resolve() != root.resolve():
        problems.append("Candidate path does not match provenance")
    hashes = receipt.get("year_sha256", {})
    if set(hashes) != {str(y) for y in range(2004, 2026)}:
        problems.append("Expected all 22 annual hashes")
    edits_path = root / "edited_rows.csv"
    annual_path = root / "annual_qc.csv"
    if not edits_path.is_file() or not annual_path.is_file():
        p.error("Missing edit ledger or annual QC summary")
    edits = pd.read_csv(edits_path, parse_dates=["time"])
    annual = pd.read_csv(annual_path)
    if len(edits) != 4097 or edits.time.duplicated().any() or set(annual.year) != set(range(2004, 2026)):
        problems.append("Edit log length, year or time uniqueness mismatch")
    if not edits.empty and (edits.year != edits.time.dt.year).any():
        problems.append("Edit log year disagrees with timestamp")
    for year in range(2004, 2026):
        file = root / f"IT-Noe_DATM_{year}.nc"
        original = a.original / file.name
        year_edits = edits.loc[edits.year == year]
        try:
            if file.is_symlink() or not file.is_file() or not original.is_file():
                raise ValueError("missing file or candidate symlink")
            if digest(file) != hashes.get(str(year)):
                raise ValueError("NetCDF SHA256 mismatch")
            with Dataset(file) as nc, Dataset(original) as old:
                if len(nc.dimensions["time"]) != 17520:
                    raise ValueError("wrong no-leap time length")
                if not np.allclose(values(nc, "time"), np.arange(17520)/48, atol=1e-5):
                    raise ValueError("wrong time coordinate")
                if f"{year}-01-01" not in str(nc.variables["time"].units):
                    raise ValueError("wrong year in NetCDF time units")
                if getattr(nc, "provenance_status", "") != "UNAPPROVED_QC_SENSITIVITY":
                    raise ValueError("missing candidate status")
                if set(nc.variables) != set(old.variables):
                    raise ValueError("model variables added or removed")
                for k in old.variables:
                    if k not in FIELDS:
                        if not np.array_equal(values(nc, k), values(old, k), equal_nan=True):
                            raise ValueError("unintended change to variable " + k)
                originals = {k: values(old, k).reshape(-1) for k in FIELDS}
                current = {k: values(nc, k).reshape(-1) for k in FIELDS}
                if any(len(current[k]) != 17520 for k in FIELDS):
                    raise ValueError("wrong forcing field dimensions")
                index = pd.date_range(f"{year}-01-01",f"{year+1}-01-01",freq="30min",inclusive="left")
                index = index[~((index.month == 2) & (index.day == 29))]
                locations = index.get_indexer(pd.DatetimeIndex(year_edits.time))
                if (locations < 0).any() or len(set(locations)) != len(locations):
                    raise ValueError("edits outside year or duplicate")
                touched = np.zeros(17520, dtype=bool)
                touched[locations] = True
                for k in FIELDS:
                    x, y = originals[k], current[k]
                    if not np.isfinite(y).all():
                        raise ValueError("nonfinite " + k)
                    if not np.array_equal(x[~touched], y[~touched]):
                        raise ValueError("unlogged change outside edited times for " + k)
                if not np.allclose(current["TBOT"][locations]-273.15,
                                   year_edits.TA_after.to_numpy(float),atol=0.01):
                    raise ValueError("edit ledger TA does not match NetCDF")
                temp,q,press = [current[k] for k in FIELDS]
                e_sat = 611.2*np.exp(17.67*(temp-273.15)/(temp-29.65))
                e_actual = q*press/(0.622+0.378*q)
                rh = 100*e_actual/e_sat
                if not (np.isfinite(rh).all() and np.min(rh)>0 and
                        np.isfinite(temp).all() and np.min(temp)>220 and np.max(temp)<330 and
                        np.min(q)>0 and np.max(q)<0.08 and
                        np.min(press)>50000 and np.max(press)<110000):
                    raise ValueError("unphysical reconstructed forcing")
                jump = float(np.max(np.abs(np.diff(temp))))
                if jump > a.max_temperature_jump+1e-5:
                    problems.append(f"{year}: max half-hour TA jump {jump:.4f}C")
                if np.max(rh) > 100.5:
                    notes.append(f"{year}: RH exceeds 100.5% at some records; inspect saturation")
                stats = annual.loc[annual.year == year].iloc[0]
                if int(stats.modified) != len(year_edits):
                    raise ValueError("annual_QC and edit-log mismatch")
                summary.append(dict(year=year,edited=len(year_edits),
                    min_rh_pct=round(float(np.min(rh)),3),
                    max_rh_pct=round(float(np.max(rh)),3),
                    max_halfhour_jump_C=round(jump,3)))
        except Exception as exc:
            problems.append(f"{year}: {exc}")
    print("IT-Noe 2004-2025 post-write verification; READ ONLY")
    print(f"EXPECTED=22 years, 208 event brackets, 4097 logged candidate edits")
    print(pd.DataFrame(summary).to_string(index=False))
    print("CANDIDATE_STATUS=UNAPPROVED_QC_SENSITIVITY")
    print("SCIENCE_REVIEW_FLAGS=source_review_complete=false; boundary_review_complete=false; full_cycle_qc_complete=false")
    for note in notes:
        print("REVIEW:",note)
    for problem in problems:
        print("FAIL:",problem)
    print("INTEGRITY_GATE=" + ("PASS" if not problems else "FAIL"))
    print("READY_FOR_PRODUCTION=NO (this check is structural and physical, not scientific approval)")
    print("NO CIME, Slurm, source or candidate data modified")
    return int(bool(problems))

if __name__ == "__main__":
    sys.exit(main())

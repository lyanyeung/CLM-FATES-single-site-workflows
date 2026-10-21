#!/usr/bin/env python3
"""Build a VERSIONED *diagnostic* IT-Noe annual DATM trial, never production forcing.

Default mode: preflight only. --write-trial explicitly creates a NEW directory:
21 read-only symlinks to unchanged annual DATM inputs and one COPY of 2010.nc,
whose TBOT/QBOT/PSRF are replaced by a consistent ICOS ERA5 TA/VPD/PA triplet
during the specified time window. The original DATM and CIME case are untouched.

This tests sensitivity to forcing and DOES NOT fix / prove the negative RH cause.
"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing")
SOURCE_NAME = "datm_11_provisional_dynamic_zbot_v1"
ERA_NAME = "raw_multisource_v1/ICOS/ICOS_IT-Noe_FLUXNET_ERA5_HH_1981-2026_v1.3_r1.csv"
DEFAULT_WINDOWS = {
    "abort_window": ("2010-05-27 18:00", "2010-05-28 10:30"),
    "may2010": ("2010-05-01 00:00", "2010-06-01 00:00"),
}
FIELDS = ("TBOT", "QBOT", "PSRF")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_era(era, start, end):
    columns = pd.read_csv(era, nrows=0).columns
    tcol = "TIMESTAMP_START" if "TIMESTAMP_START" in columns else (
        "TIMESTAMP_END" if "TIMESTAMP_END" in columns else None)
    if tcol is None:
        raise RuntimeError("ERA file lacks TIMESTAMP_START/TIMESTAMP_END")
    required = ["TA_ERA", "VPD_ERA", "PA_ERA"]
    if any(c not in columns for c in required):
        raise RuntimeError("ERA file missing one of TA_ERA/VPD_ERA/PA_ERA")
    pieces = []
    for part in pd.read_csv(era, usecols=[tcol, *required],
                            dtype={tcol: "string"}, chunksize=100000):
        dates = pd.to_datetime(
            part[tcol].str.strip().str.replace(r"\.0$", "", regex=True),
            format="%Y%m%d%H%M", errors="coerce")
        if dates.isna().any():
            raise RuntimeError("ERA time parse failed")
        if tcol == "TIMESTAMP_END":
            dates -= pd.Timedelta(minutes=30)
        selected = (dates >= start) & (dates < end)
        if selected.any():
            p = part.loc[selected, required].copy()
            p.insert(0, "time", dates.loc[selected].to_numpy())
            pieces.append(p)
    if not pieces:
        raise RuntimeError("No ERA observations in requested window")
    e = pd.concat(pieces).sort_values("time").reset_index(drop=True)
    expected = pd.date_range(start, end - pd.Timedelta(minutes=30), freq="30min")
    if not pd.DatetimeIndex(e.time).equals(expected):
        raise RuntimeError("ERA dates are missing, duplicate, or out of sequence")
    for field in required:
        e[field] = pd.to_numeric(e[field], errors="coerce")
    ta = e.TA_ERA.to_numpy(float)
    vpd = e.VPD_ERA.to_numpy(float)
    pa = e.PA_ERA.to_numpy(float)
    if not np.all(np.isfinite(ta) & np.isfinite(vpd) & np.isfinite(pa)):
        raise RuntimeError("Missing or nonfinite ERA triplet")
    if not (np.all((-40 < ta) & (ta < 55)) and
            np.all((0 <= vpd) & (vpd < 100)) and
            np.all((50 < pa) & (pa < 110))):
        raise RuntimeError("ERA triplets outside conservative screening bounds")
    es = 6.112 * np.exp(17.67 * ta / (ta + 243.5))   # hPa
    ea = es - vpd                                   # hPa
    rh = 100 * ea / es
    q = (0.622 * (100 * ea)) / (1000 * pa - 0.378 * (100 * ea))
    if not np.all((ea > 0) & (rh > 0) & (rh <= 100.001) &
                  np.isfinite(q) & (q > 0) & (q < 0.08)):
        raise RuntimeError("ERA triplet produces nonphysical humidity")
    offsets = (e.time - pd.Timestamp("2010-01-01")).dt.total_seconds() / 1800
    if not np.all(offsets == offsets.astype(int)):
        raise RuntimeError("ERA not on 2010 half-hour axis")
    indices = offsets.astype(int).to_numpy()
    if np.any(indices < 0) or np.any(indices >= 17520):
        raise RuntimeError("ERA trial out of annual bounds")
    return e, indices, {
        "TBOT": ta + 273.15, "QBOT": q, "PSRF": pa * 1000,
    }, rh


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=BASE)
    p.add_argument("--mode", choices=sorted(DEFAULT_WINDOWS), default="abort_window")
    p.add_argument("--out", type=Path, help="New trial folder, not the original DATM folder")
    p.add_argument("--write-trial", action="store_true",
                   help="Explicitly create a new scenario directory; default = preflight")
    a = p.parse_args()
    start, end = map(pd.Timestamp, DEFAULT_WINDOWS[a.mode])
    original_dir = a.root / SOURCE_NAME
    era = a.root / ERA_NAME
    out = a.out or a.root / ("datm_11_IT-Noe_ERA5_sensitivity_" + a.mode + "_20261021")
    if out.resolve() == original_dir.resolve():
        p.error("Refusing to overwrite original DATM directory")
    if out.exists():
        p.error("Trial output already exists; choose a NEW --out directory: " + str(out))
    if not era.is_file():
        p.error("Missing ERA CSV: " + str(era))
    inputs = [original_dir / f"IT-Noe_DATM_{y}.nc" for y in range(2004, 2026)]
    missing = [str(f) for f in inputs if not f.is_file()]
    if missing:
        p.error("Missing original annual DATM files: " + repr(missing[:5]))
    from netCDF4 import Dataset
    e, indices, replacements, rh = load_era(era, start, end)
    source_2010 = original_dir / "IT-Noe_DATM_2010.nc"
    with Dataset(source_2010) as ds:
        t = np.asarray(ds.variables["time"][:])
        if len(t) != 17520 or not np.allclose(t[indices], indices / 48):
            raise RuntimeError("Original 2010 NetCDF time axis inconsistent")
        if "2010-01-01" not in ds.variables["time"].units:
            raise RuntimeError("Unexpected 2010 time coordinate units")
        prior = {k: np.asarray(ds.variables[k][indices, 0, 0]) for k in FIELDS}
    for k in FIELDS:
        if not np.all(np.isfinite(prior[k])):
            raise RuntimeError("Original DATM non-finite " + k)
    print("MODE:", a.mode, "TIME WINDOW:", start, "to", end, "(end exclusive)")
    print("HALF-HOUR RECORDS TO CHANGE:", len(indices))
    print("SOURCE 2010 SHA256:", sha256(source_2010))
    print("ERA CSV SHA256:", sha256(era))
    for k in FIELDS:
        x = replacements[k]
        print(f"{k}: original min={prior[k].min():.7g} max={prior[k].max():.7g}; "
              f"trial min={x.min():.7g} max={x.max():.7g}; "
              f"max abs delta={np.max(np.abs(prior[k] - x)):.7g}")
    print("TRIAL RH RANGE (%):", float(rh.min()), float(rh.max()))
    print("OUTPUT DIRECTORY:", out)
    if not a.write_trial:
        print("PREFLIGHT ONLY. No file written. Add --write-trial to create this diagnostic trial.")
        return
    out.mkdir(parents=True, exist_ok=False)
    for y, source in zip(range(2004, 2026), inputs):
        dest = out / source.name
        if y == 2010:
            shutil.copy2(source, dest)
        else:
            dest.symlink_to(source.resolve())
    trial_file = out / source_2010.name
    with Dataset(trial_file, "r+") as ds:
        for k in FIELDS:
            ds.variables[k][indices, 0, 0] = replacements[k].astype("f4")
        ds.provenance_status = "DIAGNOSTIC_SENSITIVITY_TRIAL_NOT_APPROVED_FOR_PRODUCTION"
        ds.trial_policy = f"ICOS ERA5 consistent TA/VPD/PA triplet; {start} <= time < {end}"
        ds.original_2010_sha256 = sha256(source_2010)
        ds.era_input_sha256 = sha256(era)
        ds.sync()
    with Dataset(trial_file) as ds:
        for k in FIELDS:
            actual = np.asarray(ds.variables[k][indices, 0, 0])
            if not np.allclose(actual, replacements[k], rtol=1e-5, atol=1e-5):
                raise RuntimeError("POSTWRITE verification failed: " + k)
        if ds.provenance_status != "DIAGNOSTIC_SENSITIVITY_TRIAL_NOT_APPROVED_FOR_PRODUCTION":
            raise RuntimeError("Trial metadata check failed")
    if sha256(source_2010) == sha256(trial_file):
        raise RuntimeError("Trial unexpectedly identical to original")
    receipt = {
        "mode": a.mode, "status": "DIAGNOSTIC_ONLY_NOT_PRODUCTION",
        "start_inclusive": str(start), "end_exclusive": str(end),
        "modified_records": len(indices),
        "source_2010_file": str(source_2010),
        "source_2010_sha256": sha256(source_2010),
        "era_file": str(era), "era_sha256": sha256(era),
        "trial_2010_sha256": sha256(trial_file),
        "untouched_years_symlinked": [y for y in range(2004, 2026) if y != 2010],
        "notes": [
            "Requires a separately cloned CIME test case; no original case changes.",
            "Full-cycle bad observations in other years remain unchanged.",
            "Does not prove ERA is accurate or that RH abort is resolved."
        ]
    }
    (out / "TRIAL_PROVENANCE.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("TRIAL CREATED AND VERIFIED:", trial_file)
    print("2010 TRIAL SHA256:", receipt["trial_2010_sha256"])
    print("OTHER 21 YEARS: symlinked to original annual NetCDFs")
    print("NO ORIGINAL FILES OR CASES MODIFIED; NO JOBS SUBMITTED.")


if __name__ == "__main__":
    main()

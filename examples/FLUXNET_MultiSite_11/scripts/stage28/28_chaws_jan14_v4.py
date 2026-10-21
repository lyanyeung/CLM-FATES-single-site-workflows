#!/usr/bin/env python3
"""CH-Aws Stage28: reproduce or verify a nine-row January 2006 QBOT sensitivity trial.

Default: --audit (read-only). --verify checks the existing independent v4
NetCDF against RH25A v3. --write requires an explicit science-uncertainty
acknowledgment and REFUSES to overwrite an existing v4 directory.

This is NOT observation-based QC approval, a model fix, or a spin-up submission.
No CIME case, namelist, input height, executable or Slurm job is changed.
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
PARENT = ROOT / "datm_11_landrh25a_dynamic_zbot_v3/CH-Aws_DATM_2006.nc"
CANDIDATE = ROOT / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
PARENT_STATUS = CANDIDATE.parent / "status.json"
REFERENCE = (Path.home() / "FLUXNET_MultiSite_11"
             / "stage20_CH_Aws_RH_QC_expansion_audit/01_low_and_boundary_events_review.csv")
OUT = ROOT / "datm_11_stage28_jan14_trial_v4"
OUTFILE = "CH-Aws_DATM_2006.nc"
LEDGER = "CH-Aws_stage28_9row_ledger.csv"
START = "2006-01-14 14:30"
END = "2006-01-14 18:30"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError("STOP: " + message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for piece in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def sat_hpa(temp_c):
    x = np.asarray(temp_c, dtype=float)
    return 6.112 * np.exp(np.clip(17.67 * x / (x + 243.5), -100, 100))


def time_axis(nc):
    v = nc["time"]
    dates = num2date(v[:], v.units, calendar=getattr(v, "calendar", "noleap"))
    return pd.DatetimeIndex([str(x)[:19] for x in dates])


def build_proposal():
    for f in (PARENT, CANDIDATE, REFERENCE):
        require(f.is_file(), f"Missing prerequisite: {f}")
    if PARENT_STATUS.is_file():
        meta = json.loads(PARENT_STATUS.read_text())
        require(sha256(CANDIDATE) == meta.get("candidate_sha256"),
                "RH25A CSV does not match recorded source hash")

    columns = ["time", "TA_F", "PA_F", "VPD_F", "RH_IMPLIED_PCT",
               "VPD_F_SOURCE", "VPD_F_QC"]
    df = pd.read_csv(CANDIDATE, usecols=columns, low_memory=False)
    df["time"] = pd.to_datetime(df["time"])
    require(df["time"].is_unique, "Duplicate candidate timestamps")
    need = pd.date_range(START, END, freq="30min")
    require(len(need) == 9, "Expected nine records")
    rows = df.set_index("time").reindex(need)
    require(rows.notna(subset=["TA_F", "PA_F", "VPD_F", "RH_IMPLIED_PCT"]).all().all(),
            "Missing forcing values")
    require((rows["VPD_F_SOURCE"] == "EUF_F").all()
            and pd.to_numeric(rows["VPD_F_QC"], errors="coerce").eq(2).all()
            and rows["RH_IMPLIED_PCT"].lt(10).all(),
            "Selected records no longer match QC2/EUF_F low-RH provenance")

    ref = pd.read_csv(REFERENCE, low_memory=False)
    ref["time"] = pd.to_datetime(ref["time_local_standard_UTCplus1"])
    require(ref["time"].is_unique, "Duplicate Stage20 reference timestamps")
    ref = ref.set_index("time").reindex(need)
    for key in ("era5_RH_pct", "era5_land_RH_pct"):
        require(pd.to_numeric(ref[key], errors="coerce").notna().all(),
                f"Missing historical reference: {key}")
    rland = ref["era5_land_RH_pct"].to_numpy(dtype=float)
    require(np.all((rland > 0) & (rland < 100)), "Invalid ERA5-Land RH")
    ta = rows["TA_F"].to_numpy(dtype=float)
    pa = rows["PA_F"].to_numpy(dtype=float) * 1000.0
    es_hpa = sat_hpa(ta)
    ea_pa = es_hpa * rland
    new_q = 0.622 * ea_pa / (pa - 0.378 * ea_pa)
    require(np.all(np.isfinite(new_q) & (new_q > 0) & (new_q < 0.08)),
            "Nonphysical candidate QBOT")
    rows["ERA5_RH_pct"] = ref["era5_RH_pct"].to_numpy(dtype=float)
    rows["ERA5_Land_RH_pct"] = rland
    rows["ERA5_minus_Land_abs_pp"] = np.abs(
        rows["ERA5_RH_pct"] - rows["ERA5_Land_RH_pct"])
    rows["VPD_stage28_hPa"] = es_hpa * (1 - rland / 100)
    rows["QBOT_stage28_kgkg"] = new_q
    rows["decision"] = "9_ROW_ERA5_LAND_SENSITIVITY_NOT_OBSERVATION_VALIDATED"
    rows.index.name = "time"

    with Dataset(PARENT) as nc:
        require(len(nc.dimensions["time"]) == 17520, "2006 DATM length differs")
        require(nc["QBOT"].shape == (17520, 1, 1), "Unexpected QBOT layout")
        axis = time_axis(nc)
        require(axis.is_unique, "Duplicate DATM timestamps")
        ix = axis.get_indexer(need)
        require(np.all(ix >= 0), "Stage28 times not in DATM")
        qold = np.asarray(nc["QBOT"][:, 0, 0], dtype=np.float32)
        tbot = np.asarray(nc["TBOT"][ix, 0, 0], dtype=float)
        psrf = np.asarray(nc["PSRF"][ix, 0, 0], dtype=float)
        rh_from_nc = (100 * (qold[ix] * psrf
                      / (0.622 + 0.378 * qold[ix]))
                      / (sat_hpa(tbot - 273.15) * 100))
        require(np.allclose(rh_from_nc, rows["RH_IMPLIED_PCT"].to_numpy(),
                            rtol=0, atol=0.25),
                "Candidate CSV and parent DATM times/humidity do not agree")
    print("Proposed nine records:")
    print(rows[["RH_IMPLIED_PCT", "ERA5_RH_pct", "ERA5_Land_RH_pct",
                "VPD_stage28_hPa", "QBOT_stage28_kgkg"]].to_string())
    return rows, ix, qold


def verify_existing(rows, indices, old_q):
    f = OUT / OUTFILE
    require(f.is_file(), f"Missing independent trial NetCDF: {f}")
    changed_set = set(map(int, indices))
    with Dataset(PARENT) as old, Dataset(f) as new:
        require(set(old.variables) == set(new.variables),
                "Variable inventory differs")
        for name in old.variables:
            x, y = np.ma.asarray(old[name][:]), np.ma.asarray(new[name][:])
            require(x.shape == y.shape, f"{name}: shape differs")
            if name == "QBOT":
                xo, yn = np.asarray(x, dtype=np.float32).reshape(-1), np.asarray(y, dtype=np.float32).reshape(-1)
                changed = set(map(int, np.flatnonzero(xo != yn)))
                require(changed == changed_set, f"Unexpected QBOT edits: {sorted(changed)}")
                expected = rows["QBOT_stage28_kgkg"].to_numpy(dtype=np.float32)
                require(np.array_equal(yn[indices], expected),
                        "Edited QBOT differs from ERA5-Land proposal")
                print(f"Verified QBOT changes: {len(changed)} / 17520")
            else:
                require(np.ma.allequal(x, y), f"{name}: changed unexpectedly")
    if (OUT / "stage28_manifest.json").is_file():
        manifest = json.loads((OUT / "stage28_manifest.json").read_text())
        require(manifest.get("changed_records") == 9,
                "Manifest edited-count mismatch")
        require(manifest.get("parent_DATM_sha256") == sha256(PARENT),
                "Original v3 differs from recorded manifest parent")
    print("VERIFY SUCCESS: 9 QBOT edits; all other variables identical.")
    print("Stage28 remains exploratory; no run success is claimed.")


def create_trial(rows, indices, old_q):
    require(not OUT.exists(), f"Will NOT overwrite existing v4: {OUT}")
    work = Path(tempfile.mkdtemp(prefix=".CH_Aws_stage28_", dir=ROOT))
    try:
        ledger = work / LEDGER
        rows.to_csv(ledger)
        target = work / OUTFILE
        shutil.copy2(PARENT, target)
        with Dataset(target, "r+") as nc:
            q = np.asarray(nc["QBOT"][:, 0, 0], dtype=np.float32)
            q[indices] = rows["QBOT_stage28_kgkg"].to_numpy(dtype=np.float32)
            nc["QBOT"][:, 0, 0] = q
            nc.setncattr("source_candidate_tag", "stage28_jan14_trial_v4")
            nc.setncattr("stage28_scientific_status", "EXPLORATORY_NOT_OBSERVATION_VALIDATED")
            nc.setncattr("stage28_changed_QBOT_records", 9)
            nc.setncattr("stage28_parent_DATM_sha256", sha256(PARENT))
        with Dataset(target) as nc:
            q = np.asarray(nc["QBOT"][:, 0, 0], dtype=np.float32)
            changed = set(map(int, np.flatnonzero(q != old_q)))
            require(changed == set(map(int, indices)), "Changed indices unexpectedly")
        manifest = {
            "site": "CH-Aws", "stage": "STAGE28_JAN14_9ROW_TRIAL",
            "scientific_status": "EXPLORATORY_ONLY", "year": 2006,
            "changed_variable": "QBOT", "changed_records": 9,
            "parent_DATM": str(PARENT), "parent_DATM_sha256": sha256(PARENT),
            "parent_CSV_sha256": sha256(CANDIDATE),
            "reference_review_sha256": sha256(REFERENCE),
            "revision_ledger_sha256": sha256(ledger),
            "other_years": "Unchanged RH25A v3",
            "warning": "ERA5-Land reanalysis is not an observation or demonstrated model fix"
        }
        (work / "stage28_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        os.rename(work, OUT)
        print("WROTE non-overwriting independent v4:", OUT)
    finally:
        if work.exists():
            shutil.rmtree(work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--audit", action="store_true", help="Default; read-only proposed changes")
    mode.add_argument("--verify", action="store_true", help="Read-only existing v4 verification")
    mode.add_argument("--write", action="store_true", help="Write NEW v4 only if absent")
    parser.add_argument("--acknowledge-reanalysis-uncertainty", action="store_true")
    a = parser.parse_args()
    rows, idx, original = build_proposal()
    if a.write:
        require(a.acknowledge_reanalysis_uncertainty,
                "--write requires --acknowledge-reanalysis-uncertainty")
        create_trial(rows, idx, original)
        verify_existing(rows, idx, original)
    elif a.verify:
        verify_existing(rows, idx, original)
    else:
        print("AUDIT ONLY; no forcing changes, case operations, or Slurm jobs.")


if __name__ == "__main__":
    main()

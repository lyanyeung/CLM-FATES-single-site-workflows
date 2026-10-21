#!/usr/bin/env python3
"""READ-ONLY preflight for an isolated IT-Noe May-2010 ERA5 CIME model test.

Does NOT clone, configure, submit, cancel, resubmit, stage, or modify a CIME
case; does not edit forcing or restarts. It verifies the supplied versioned
May 2010 trial against the original and inspects the 2054 checkpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
from netCDF4 import Dataset

FORCING = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing")
CASE_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases")
ARCH_ROOT = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive")
DEFAULT_CASE = "IT-Noe_ERA5_ABW_BRANCH2009"
DEFAULT_TRIAL = "datm_11_IT-Noe_ERA5_may2010_diagnostic_20261021_214215"
ORIGINAL = "datm_11_provisional_dynamic_zbot_v1"
STAMP = "2054-01-01-00000"
VARIABLES = ("TBOT", "QBOT", "PSRF")


def digest(file: Path) -> str:
    h = hashlib.sha256()
    with file.open("rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def info(kind: str, message: str) -> None:
    print(f"{kind:>5}: {message}")


def xml(case: Path, key: str) -> str:
    tool = case / "xmlquery"
    if not tool.is_file():
        return "UNAVAILABLE"
    try:
        call = subprocess.run(
            [str(tool), key, "--value"], cwd=case, capture_output=True,
            text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return "QUERY_FAILED"
    if call.returncode != 0:
        return "NOT_DEFINED"
    return call.stdout.strip().splitlines()[-1] if call.stdout.strip() else "EMPTY"


def array(ds: Dataset, key: str) -> np.ndarray:
    if key not in ds.variables:
        raise ValueError(f"Missing NetCDF variable {key}")
    data = np.ma.asarray(ds.variables[key][:, 0, 0])
    if np.ma.is_masked(data) and np.any(np.ma.getmaskarray(data)):
        raise ValueError(f"Masked values in NetCDF {key}")
    a = np.asarray(data, dtype=np.float64)
    if a.ndim != 1 or len(a) != 17520 or not np.isfinite(a).all():
        raise ValueError(f"Unexpected shape/nonfinite NetCDF {key}: {a.shape}")
    return a


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial", type=Path, default=FORCING / DEFAULT_TRIAL)
    parser.add_argument("--original", type=Path, default=FORCING / ORIGINAL)
    parser.add_argument("--case", type=Path, default=CASE_ROOT / DEFAULT_CASE)
    parser.add_argument("--archive", type=Path, default=ARCH_ROOT / DEFAULT_CASE / "rest" / STAMP)
    a = parser.parse_args()
    errors = []
    warns = []

    print("========== IT-Noe ISOLATED MAY-2010 TEST PREFLIGHT ==========")
    print("READ ONLY; NEVER modifies a case, forcing or restart.")
    print("TRIAL: ", a.trial)
    print("ORIGINAL: ", a.original)
    print("CASE: ", a.case)
    print("ARCHIVE: ", a.archive)

    if not a.trial.is_dir() or a.trial.is_symlink():
        errors.append("Trial folder missing or is a symlink")
    if not a.original.is_dir():
        errors.append("Original forcing folder missing")
    if a.trial.resolve() == a.original.resolve():
        errors.append("Trial and original are same directory")
    if not a.case.is_dir():
        errors.append("Production branch CIME case not found")
    if not a.archive.is_dir():
        errors.append("2054 checkpoint directory not found")

    trial_2010 = a.trial / "IT-Noe_DATM_2010.nc"
    original_2010 = a.original / "IT-Noe_DATM_2010.nc"
    if not trial_2010.is_file() or trial_2010.is_symlink():
        errors.append("2010 trial must be an existing physical .nc copy")
    if not original_2010.is_file():
        errors.append("2010 original .nc missing")
    if a.trial.is_dir() and a.original.is_dir():
        for year in range(2004, 2026):
            dst = a.trial / f"IT-Noe_DATM_{year}.nc"
            src = a.original / dst.name
            if not src.is_file() or not dst.is_file():
                errors.append(f"Missing forcing NetCDF year {year}")
            elif year != 2010 and (not dst.is_symlink() or dst.resolve() != src.resolve()):
                errors.append(f"Year {year} is not a symlink to original")
    if trial_2010.is_file() and original_2010.is_file():
        try:
            first = 120 * 48  # zero-based day of 2010-05-01
            last = 151 * 48   # exclusive 2010-06-01
            modified = np.zeros(17520, dtype=bool)
            modified[first:last] = True
            with Dataset(original_2010) as original, Dataset(trial_2010) as trial:
                for key in VARIABLES:
                    aa, bb = array(original, key), array(trial, key)
                    changed = np.count_nonzero(aa[modified] != bb[modified])
                    unchanged_ok = bool(np.array_equal(aa[~modified], bb[~modified]))
                    info("DATA", f"{key}: modified within May={changed}/1488; unchanged outside May={unchanged_ok}")
                    if changed == 0 or not unchanged_ok:
                        errors.append(f"{key}: no May change, or changes outside May")
                ot = np.ma.asarray(original.variables["time"][:])
                tt = np.ma.asarray(trial.variables["time"][:])
                if not (np.array_equal(ot, tt) and len(tt) == 17520):
                    errors.append("Trial and original time coordinate differ")
                if "2010-01-01" not in str(trial.variables["time"].units):
                    errors.append("Unexpected trial time units")
                status = getattr(trial, "provenance_status", "")
                if status != "DIAGNOSTIC_SENSITIVITY_TRIAL_NOT_APPROVED_FOR_PRODUCTION":
                    errors.append("Missing trial diagnostic-only metadata")
            info("HASH", f"original 2010 sha256={digest(original_2010)}")
            info("HASH", f"trial 2010 sha256={digest(trial_2010)}")
        except Exception as exc:
            errors.append(f"Trial NetCDF verification error: {exc}")

    receipt = a.trial / "TRIAL_PROVENANCE.json"
    if receipt.is_file():
        try:
            record = json.loads(receipt.read_text())
            if (record.get("trial_2010_sha256") != digest(trial_2010)
                    or record.get("source_2010_sha256") != digest(original_2010)):
                errors.append("Trial provenance SHA256 mismatch")
            if record.get("mode") != "may2010":
                errors.append("Trial provenance mode is not may2010")
            info("META", "Trial provenance hashes and mode checked")
        except Exception as exc:
            errors.append(f"Trial provenance error: {exc}")
    else:
        errors.append("Missing TRIAL_PROVENANCE.json")

    print("========== EXISTING CASE CONFIGURATION (READ ONLY) ==========")
    if a.case.is_dir():
        for key in (
            "RUN_TYPE", "RUN_STARTDATE", "RUN_REFCASE", "RUN_REFDATE",
            "RUN_REFDIR", "CONTINUE_RUN", "RESUBMIT",
            "STOP_OPTION", "STOP_N", "REST_OPTION", "REST_N",
            "ATM_NCPL", "DATM_YR_START", "DATM_YR_END", "DATM_YR_ALIGN",
            "RUNDIR", "DOUT_S_ROOT", "DIN_LOC_ROOT",
        ):
            info("XML", f"{key}={xml(a.case, key)}")
        case_status = a.case / "CaseStatus"
        if case_status.is_file():
            lines = case_status.read_text(errors="replace").splitlines()[-14:]
            for line in lines:
                print("STATUS:", line[:220])
        # CIME streams may contain DATM filenames/configurable paths.
        hits = []
        dirs = (a.case, a.case / "CaseDocs")
        for folder in dirs:
            if not folder.is_dir():
                continue
            for file in sorted(folder.iterdir()):
                if (not file.is_file() or file.is_symlink() or
                        file.stat().st_size > 1024 * 1024):
                    continue
                if not (file.name.startswith("user_nl_datm")
                        or "streams" in file.name.lower()
                        or file.name in ("datm_in", "atm_in")):
                    continue
                try:
                    for ln, line in enumerate(file.read_text(errors="replace").splitlines(), 1):
                        if any(term in line for term in (
                            "datm_11_", "IT-Noe_DATM", "stream", "datafiles")):
                            hits.append((str(file), ln, line.strip()[:220]))
                except OSError:
                    warns.append(f"Could not read {file}")
        print("========== DATM STREAM / FILE REFERENCES ==========")
        for fname, line, contents in hits[:45]:
            print(f"{fname}:{line}: {contents}")
        if not hits:
            warns.append("No DATM stream source references found in case root/CaseDocs; check runtime datm.streams files")

    print("========== 2054 THREE-COMPONENT RESTART ==========")
    if a.archive.is_dir():
        for component in ("clm2", "cpl", "datm"):
            matches = sorted(a.archive.glob(f"*{component}.r.{STAMP}.nc"))
            matches = [f for f in matches if f.is_file() and f.stat().st_size > 0]
            if not matches:
                errors.append(f"Missing/nonzero {component} restart at 2054")
            else:
                for f in matches:
                    info("REST", f"{f.name} ({f.stat().st_size} bytes)")
        for component in ("atm", "cpl", "lnd"):
            name = a.archive / f"rpointer.{component}.{STAMP}"
            if not name.is_file() or name.stat().st_size <= 0:
                errors.append(f"Missing rpointer: {name.name}")
            else:
                info("POINT", f"{name.name} ({name.stat().st_size} bytes)")
    print("========== SLURM USER QUEUE (READ ONLY) ==========")
    try:
        q = subprocess.run(
            ["squeue", "-h", "-u", os.environ.get("USER", "ly3n24"),
             "-o", "%i|%j|%T|%R"],
            capture_output=True, text=True, timeout=20, check=False)
        if q.returncode:
            warns.append("squeue query failed: " + q.stderr.strip()[:120])
        else:
            active = [line for line in q.stdout.splitlines()
                      if DEFAULT_CASE in line]
            for line in active[:15]:
                info("QUEUE", line)
            if active:
                warns.append("Related Slurm jobs exist (may include permanently blocked archive dependency); do not modify or submit production case")
            else:
                info("QUEUE", "No exact current case name found in user queue")
    except (OSError, subprocess.TimeoutExpired) as exc:
        warns.append(f"Slurm queue check failed: {exc}")

    print("========== PREFLIGHT RESULT ==========")
    for w in warns:
        info("WARN", w)
    for e in errors:
        info("FAIL", e)
    if errors:
        print("RESULT=FAIL. NO model test should be submitted until corrected.")
        return 2
    print("RESULT=INPUTS_PRESENT. 2010 trial is isolated from originals; 2054 restart files are present.")
    print("IMPORTANT: Presence and hash checks do NOT verify restart scientific consistency.")
    print("NEXT: prepare a separate CIME test case with these verified paths, NEVER submit the production case.")
    print("NO FILES OR JOBS CHANGED.")
    return 0


if __name__ == "__main__":
    sys.exit(run())

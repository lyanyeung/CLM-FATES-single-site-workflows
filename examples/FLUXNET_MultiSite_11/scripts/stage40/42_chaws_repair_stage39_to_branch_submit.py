#!/usr/bin/env python3
"""Stage40: repair the ALREADY CREATED CH-Aws RH38A case; submit full 990-yr branch.

Stage39 created a new RH38A_CONT2016 case and copied complete RH34A
2016-01-01 cpl/datm/clm2 restart files, but case.submit refused the
old casename prefix because CONTINUE_RUN was TRUE. That is a CIME
pre-submit check, not a Slurm failure.

CORRECT: first segment is RUN_TYPE=branch, CONTINUE_RUN=FALSE,
RUN_REFCASE=CH-Aws_FATES_SPINUP1000_RH34A, RUN_REFDATE=2016-01-01,
RUN_REFTOD=00000, GET_REFCASE=FALSE (files already staged).
After the initial five-year segment, CIME automatic RESUBMIT sets
CONTINUE_RUN=TRUE and uses NEW-case restarts. 198 x 5 years=990.
No short test job or additional 1000-year startup.

Usage:
  python3 42_chaws_repair_stage39_to_branch_submit.py audit   # no changes
  python3 42_chaws_repair_stage39_to_branch_submit.py launch  # fix and submit once
  python3 42_chaws_repair_stage39_to_branch_submit.py status  # no changes
Old RH34A case, originals and archived restart MUST NOT be changed.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

USER = "ly3n24"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
OUT = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
OLDNAME = "CH-Aws_FATES_SPINUP1000_RH34A"
NAME = "CH-Aws_FATES_SPINUP1000_RH38A_CONT2016"
OLD = ROOT / "cases" / OLDNAME
CASE = ROOT / "cases" / NAME
RUN = OUT / NAME / "run"
ARCHIVE = OUT / "archive" / OLDNAME / "rest" / "2016-01-01-00000"
FORCING = ROOT / "sites/MY_EC_SITE/CH-Aws/forcing/datm_11_stage38_qc1_21rh_sensitivity_v7"
STAMP = "2016-01-01-00000"
MPI = "srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"
KINDS = {"cpl": "cpl.r", "atm": "datm.r", "lnd": "clm2.r"}
MARKER = CASE / ".STAGE40_BRANCH_SUBMISSION_ATTEMPTED"
LOCK = Path.home() / ".CH_Aws_stage40_branch_submit.lock"


def stop(why):
    raise RuntimeError("STOP: " + why)


def need(cond, why):
    if not cond:
        stop(why)


def cmd(*args, cwd=None):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if p.returncode:
        stop("FAILED: " + " ".join(str(a) for a in args)
             + "\n" + (p.stdout + p.stderr)[-5000:])
    return p.stdout.strip()


def val(key):
    return cmd("./xmlquery", key, "--value", cwd=CASE).strip()


def oldval(key):
    return cmd("./xmlquery", key, "--value", cwd=OLD).strip()


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ptr(path):
    need(path.is_file(), "Missing rpointer: " + str(path))
    name = path.read_text(errors="replace").strip().removeprefix("./")
    need(re.fullmatch(r"[A-Za-z0-9_.-]+", name) is not None,
         "Unexpected rpointer content " + str(path) + ": " + repr(name))
    return name


def queue():
    return cmd("squeue", "-h", "-u", USER, "-o", "%j|%T|%i").splitlines()


def no_active():
    for line in queue():
        jobname = line.split("|", 1)[0]
        need(jobname not in ("run." + NAME, "st_archive." + NAME,
                             "run." + OLDNAME),
             "Existing running/queued old/new job; do not duplicate: " + line)


def inspect():
    need(os.environ.get("USER") == USER, "Wrong IRIDIS6 user")
    no_active()
    need(CASE.is_dir() and (CASE / "xmlquery").is_file(),
         "Stage39 case does not exist; this is a repair script, NOT create_clone")
    need((CASE / ".STAGE39_SUBMISSION_ATTEMPTED").is_file(),
         "No evidence of the failed Stage39 submission")
    need(not MARKER.exists(), "Stage40 already attempted submission; use status")
    need((CASE / ".stage39_restart_provenance.json").is_file(),
         "Missing Stage39 source restart provenance")
    record = json.loads((CASE / ".stage39_restart_provenance.json").read_text())
    need(record.get("source_case") == OLDNAME
         and record.get("case") == NAME
         and record.get("source_checkpoint") == STAMP
         and record.get("five_year_segments") == 198
         and record.get("initial_RESUBMIT") == 197,
         "Stage39 source case/checkpoint/segments are not expected")
    need((OLD / "xmlquery").exists() and oldval("CASE") == OLDNAME,
         "Original RH34A case missing")
    need(val("CASE") == NAME, "New CIME CASE mismatch")
    expected = {
        "RUN_STARTDATE": "2006-01-01",
        "CALENDAR": "NO_LEAP", "ATM_NCPL": "48",
        "STOP_OPTION": "nyears", "STOP_N": "5",
        "REST_OPTION": "nyears", "REST_N": "5",
        "RESUBMIT": "197", "DOUT_S": "TRUE",
        "BUILD_COMPLETE": "TRUE", "RUNDIR": str(RUN),
        "DOUT_S_ROOT": str(OUT / "archive" / NAME),
        "MPI_RUN_COMMAND": MPI,
        "CLM_CO2_TYPE": "constant",
    }
    for key, wanted in expected.items():
        need(val(key) == wanted,
             f"Unexpected {key}: {val(key)!r} != {wanted!r}")
    need(abs(float(val("CCSM_CO2_PPMV")) - 381.15) < 0.011,
         "CH-Aws constant CO2 differs")
    need(val("RUN_TYPE") in ("startup", "branch"),
         "Unrecognized RUN_TYPE")
    need(val("CONTINUE_RUN") == ("TRUE" if val("RUN_TYPE") == "startup"
                                   else "FALSE"),
         "Unexpected RUN_TYPE / CONTINUE_RUN pairing")
    status = (CASE / "CaseStatus").read_text(errors="replace")
    need("case.submit success" not in status and "model execution starting" not in status,
         "Case may already have submitted or run; do not repeat")
    need(FORCING.is_dir(), "v7 forcing missing")
    m = json.loads((FORCING / "stage38_manifest.json").read_text())
    need(m.get("version") == "STAGE38_QC1_21ROW_SENSITIVITY_V7"
         and m.get("modified_vs_v6") == 21, "Unexpected v7 manifest")
    stream = (CASE / "user_nl_datm_streams").read_text()
    need(stream.count(str(FORCING / "CH-Aws_DATM_")) == 19,
         "New case does not use exactly 19 v7 forcing annual NetCDF files")
    need((RUN / "rpointer.cpl").is_file(), "No staged coupler pointer")
    for component, kind in KINDS.items():
        fname = f"{OLDNAME}.{kind}.{STAMP}.nc"
        source = ARCHIVE / fname
        staged = RUN / fname
        need(source.is_file() and staged.is_file(),
             "Missing staged checkpoint: " + fname)
        need(sha(staged) == sha(source) == record["source_restart_SHA256"][component],
             "Source/staged/Stage39 checkpoint SHA256 mismatch: " + component)
        need(ptr(RUN / ("rpointer." + component)) == fname,
             "Active pointer must reference OLD case restart: " + component)
    for p in RUN.glob("*.clm2.h*.nc"):
        stop("New case already has output history; inspect before resubmitting: " + str(p))
    need((CASE / ".case.run").is_file() and
         (CASE / "case.st_archive").is_file(), "Batch files missing")
    exe = Path(val("EXEROOT")) / "cesm.exe"
    need(exe.is_file() and os.access(exe, os.X_OK),
         "Shared executable missing")
    print("STAGE40 PREFLIGHT PASSED: original 2016 restarts unchanged; new case idle.")
    print("Current RUN_TYPE:", val("RUN_TYPE"),
          "CONTINUE_RUN:", val("CONTINUE_RUN"))
    print("Will use BRANCH from", OLDNAME, STAMP, "with v7 forcing.")
    print("198 x 5 model years, first RESUBMIT=197, to 3006-01-01.")
    return exe


def repair():
    # Run only on NEW case, keep original restart filenames and file bytes.
    settings = {
        "RUN_TYPE": "branch", "CONTINUE_RUN": "FALSE",
        "RUN_REFCASE": OLDNAME, "RUN_REFDATE": "2016-01-01",
        "RUN_REFTOD": "00000", "GET_REFCASE": "FALSE",
    }
    for key, value in settings.items():
        cmd("./xmlchange", f"{key}={value}", cwd=CASE)
    cmd("./preview_namelists", cwd=CASE)
    cmd("./check_input_data", cwd=CASE)
    for key, expected in settings.items():
        need(val(key) == expected, f"Branch configuration failed: {key}")
    need(val("RESUBMIT") == "197" and val("STOP_N") == "5" and
         val("CONTINUE_RUN") == "FALSE", "Auto-chain configuration lost")
    need(ptr(RUN / "rpointer.cpl") ==
         f"{OLDNAME}.cpl.r.{STAMP}.nc",
         "Original cpl pointer unexpectedly changed")
    text = (CASE / "CaseDocs/datm.streams.xml").read_text()
    for year in range(2006, 2025):
        need(str(FORCING / f"CH-Aws_DATM_{year}.nc") in text,
             "Compiled DATM stream lost v7: " + str(year))
    print("REPAIRED: RUN_TYPE=branch, CONTINUE_RUN=FALSE, ", flush=True)
    print("RUN_REFCASE=" + OLDNAME + ", RUN_REFDATE=2016-01-01", flush=True)
    print("Original restarts preserved verbatim; 990-year resubmit chain unchanged.", flush=True)


def launch():
    exe = inspect()
    repair()
    no_active()
    run_preview = cmd("./preview_run", cwd=CASE)
    need(MPI + " " + str(exe) in run_preview,
         "Wrong shared executable or MPI command in preview_run")
    need("case.submit success" not in
         (CASE / "CaseStatus").read_text(errors="replace"),
         "Unexpected prior successful submission")
    MARKER.write_text(datetime.now().isoformat() + "\n")
    print("SUBMITTING DIRECTLY: 990 model years = 198 five-year segments.", flush=True)
    try:
        output = cmd("./case.submit", cwd=CASE)
    except Exception:
        print("Stage40 marker retained: do NOT re-submit blindly.", file=sys.stderr)
        raise
    print(output, flush=True)
    print("case.submit returned 0; model not yet completed.", flush=True)
    print("NEW JOBS:")
    for line in queue():
        if NAME in line:
            print(line)


def status_mode():
    if not CASE.is_dir():
        print("New RH38A case not found")
        return
    for key in ("CASE", "RUN_TYPE", "CONTINUE_RUN", "RUN_REFCASE",
                "RUN_REFDATE", "GET_REFCASE", "RESUBMIT", "STOP_N",
                "RUNDIR", "DOUT_S_ROOT"):
        try:
            print(key, val(key))
        except Exception as e:
            print(key, str(e))
    status = CASE / "CaseStatus"
    if status.is_file():
        print("=== Latest CaseStatus ===")
        print("\n".join(status.read_text(errors="replace").splitlines()[-22:]))
    print("=== Slurm new-case jobs ===")
    for line in queue():
        if NAME in line:
            print(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", nargs="?", choices=("audit", "launch", "status"),
                    default="audit")
    args = ap.parse_args()
    if args.mode == "status":
        status_mode()
        return
    with LOCK.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.mode == "audit":
            inspect()
        else:
            launch()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

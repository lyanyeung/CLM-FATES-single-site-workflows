#!/usr/bin/env python3
"""DE-Hai-only checkpoint-safe CIME continuation after the 2026-10-18 failure.

Modes: inspect (read-only), prepare (backup + stage, NO submission),
       submit SESSION (one-shot CIME submission).
Pin: archived model-clock checkpoint 2810-01-01-00000 (810 / 1000 years).
Review this script and IRIDIS6 state before running. Never run on another site.
Standard library only; execute on IRIDIS6, not on a local workstation.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime

SITE = "DE-Hai"
NAME = "DE-Hai_FATES_SPINUP500"
STAMP = "2810-01-01-00000"
FIRST = 2000
TARGET = 1000
REMAINING_SEGMENTS = (TARGET - (int(STAMP[:4]) - FIRST)) // 5
EXPECTED_RESUBMIT = REMAINING_SEGMENTS - 1
CASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases") / NAME
BASE = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
RUN = BASE / NAME / "run"
RESTROOT = BASE / "archive" / NAME / "rest"
SRC = RESTROOT / STAMP
BACKUPROOT = BASE / "recovery_backups/FLUXNET_MultiSite_6/DE-Hai"
KINDS = {"cpl": "cpl.r", "atm": "datm.r", "lnd": "clm2.r"}
MPI = "srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"

def stop(message):
    raise SystemExit("STOP: " + message)

def cmd(*args, cwd=None, check=True):
    p = subprocess.run(args, cwd=str(cwd) if cwd else None,
                       text=True, capture_output=True)
    if check and p.returncode:
        stop("Command failed: " + " ".join(map(str, args)) +
             "\n" + (p.stdout + p.stderr)[-2500:])
    return p.stdout.strip()

def xml(key):
    return cmd("./xmlquery", key, "--value", cwd=CASE).strip()

def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def expected_name(component):
    return NAME + "." + KINDS[component] + "." + STAMP + ".nc"

def read_pointer(path):
    if not path.is_file():
        stop("Missing pointer " + str(path))
    return path.read_text(errors="replace").strip().removeprefix("./")

def ensure_idle():
    rows = cmd("squeue", "-h", "-u", "ly3n24", "-o", "%i|%j|%T|%R")
    active = [r for r in rows.splitlines() if NAME in r]
    if active:
        stop("DE-Hai Slurm jobs still queued/running; do not submit twice:\n" +
             "\n".join(active))

def preflight(check_idle=True):
    if os.environ.get("USER") != "ly3n24":
        stop("Run as IRIDIS6 user ly3n24")
    if not CASE.is_dir() or not RUN.is_dir() or not RESTROOT.is_dir():
        stop("DE-Hai CIME case, run directory or archive directory missing")
    if check_idle:
        ensure_idle()
    if (CASE / ".git/index.lock").exists():
        stop("Git index.lock exists: first confirm no live Git/CIME process")
    fields = {
        "CASE": NAME, "RUN_STARTDATE": "2000-01-01",
        "RUN_TYPE": "startup", "CONTINUE_RUN": "TRUE",
        "STOP_OPTION": "nyears", "STOP_N": "5",
        "REST_OPTION": "nyears", "REST_N": "5",
        "RESUBMIT": str(EXPECTED_RESUBMIT),
        "BUILD_COMPLETE": "TRUE", "DOUT_S": "TRUE",
        "RUNDIR": str(RUN), "DOUT_S_ROOT": str(RESTROOT.parent),
        "MPI_RUN_COMMAND": MPI, "CLM_CO2_TYPE": "constant",
        "CALENDAR": "NO_LEAP", "ATM_NCPL": "48",
    }
    for key, expected in fields.items():
        value = xml(key)
        if value != expected:
            stop(f"{key}={value!r}; expected {expected!r}. Review manually")
    if abs(float(xml("CCSM_CO2_PPMV")) - 368.96) > 0.011:
        stop("Original fixed CO2 concentration changed")
    exe = Path(xml("EXEROOT")) / "cesm.exe"
    if not exe.is_file() or not os.access(exe, os.X_OK):
        stop("Original compiled cesm.exe missing or not executable")
    stamps = sorted(p.name for p in RESTROOT.iterdir()
                    if p.is_dir() and re.fullmatch(r"\d{4}-01-01-00000", p.name))
    if not stamps or stamps[-1] != STAMP:
        stop("Latest archive is " + (stamps[-1] if stamps else "NONE") +
             " (expected " + STAMP + "); do not roll back newer results")
    source_sha = {}
    for component in KINDS:
        ref = expected_name(component)
        if read_pointer(SRC / ("rpointer." + component + "." + STAMP)) != ref:
            stop("Archive pointer mismatch for " + component)
        source = SRC / ref
        if not source.is_file() or source.is_symlink() or source.stat().st_size < 1024:
            stop("Archive restart missing or implausibly small: " + str(source))
        with source.open("rb") as f:
            magic = f.read(8)
        if not (magic.startswith(b"CDF\x01") or magic.startswith(b"CDF\x02") or
                magic.startswith(b"CDF\x05") or
                magic == b"\x89HDF\r\n\x1a\n"):
            stop("Restart not recognised as NetCDF/HDF5: " + str(source))
        source_sha[component] = sha(source)
    # A newer unarchived model restart might contain useful state. Never
    # overwrite or discard it without independent evaluation.
    pattern = re.compile(re.escape(NAME) + r"\.(?:clm2|datm|cpl)\.r\.(\d{4})-")
    newer = []
    for p in RUN.iterdir():
        m = pattern.search(p.name)
        if m and int(m.group(1)) > int(STAMP[:4]):
            newer.append(p.name)
    if newer:
        stop("Newer unarchived restart(s) found; inspect before rollback:\n" +
             "\n".join(newer[:25]))
    if not (CASE / "CaseStatus").is_file():
        stop("CaseStatus missing")
    print(f"CHECK OK: {NAME}; archived {STAMP} = 810 / 1000 years")
    print(f"REMAINING: {REMAINING_SEGMENTS} x 5-year runs; RESUBMIT={EXPECTED_RESUBMIT}")
    print("Existing active pointers:")
    for component in KINDS:
        p = RUN / ("rpointer." + component)
        print(f"  {p.name}: {read_pointer(p) if p.is_file() else 'MISSING'}")
    print("Archive restarts SHA256 verified as readable NetCDF/HDF5 files.")
    print("This does not verify full scientific/numerical restart integrity.")
    return source_sha

def inspect():
    print("===== DE-HAI READ-ONLY PREFLIGHT =====")
    preflight()
    print("Latest CaseStatus:")
    print("\n".join((CASE / "CaseStatus").read_text(errors="replace").splitlines()[-18:]))
    print("Check the failed cesm.log and current 'myfiles' quota before prepare.")

def atomic_pointer(path, value):
    tmp = path.with_name(path.name + ".stage-2810-tmp")
    with open(tmp, "w") as f:
        f.write(value + "\n")
    os.replace(tmp, path)

def prepare():
    sums = preflight()
    # Create a unique human-readable audit session; do not overwrite an earlier one.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    session = BACKUPROOT / ("recover_" + stamp)
    session.mkdir(parents=True, exist_ok=False)
    (session / "case").mkdir()
    (session / "run_pointers").mkdir()
    (session / "partial_history").mkdir()
    print("SESSION=" + str(session), flush=True)
    # Save all CIME science/run settings and existing active pointers first.
    saved = ["CaseStatus", ".case.run", "case.st_archive",
             "env_run.xml", "env_batch.xml", "env_case.xml",
             "env_build.xml", "env_archive.xml", "env_mach_pes.xml",
             "user_nl_clm", "user_nl_datm_streams"]
    for name in saved:
        p = CASE / name
        if p.is_file():
            shutil.copy2(p, session / "case" / name)
    for component in KINDS:
        p = RUN / ("rpointer." + component)
        if p.is_file():
            shutil.copy2(p, session / "run_pointers" / p.name)
    # Failed 2810-2815 segment may have generated incomplete history.
    # Preserve it in same-filesystem recovery area rather than deleting it.
    partial = []
    hist_pattern = re.compile(re.escape(NAME) + r"\.clm2\.h[^.]*\.(\d{4})-")
    for p in RUN.iterdir():
        m = hist_pattern.match(p.name)
        if m and int(m.group(1)) >= int(STAMP[:4]):
            if not p.is_file() or p.is_symlink():
                stop("Unusual partial-history path: " + str(p))
            partial.append(p)
    (session / "partial_history_manifest.txt").write_text(
        "\n".join(p.name for p in partial) + ("\n" if partial else ""))
    for p in partial:
        shutil.move(str(p), str(session / "partial_history" / p.name))
    print(f"Preserved {len(partial)} failed-segment history files.")
    # Stage all three coordinated component restarts BEFORE updating pointers.
    for component in KINDS:
        ref = expected_name(component)
        dest = RUN / ref
        if dest.is_symlink():
            stop("Refusing to overwrite symlink: " + str(dest))
        if dest.exists() and sha(dest) != sums[component]:
            stop("Conflicting existing run restart: " + str(dest))
        if not dest.exists():
            temp = RUN / (ref + ".stage-2810-tmp")
            shutil.copy2(SRC / ref, temp)
            if sha(temp) != sums[component]:
                stop("Failed to verify staged restart: " + ref)
            os.replace(temp, dest)
    for component in KINDS:
        atomic_pointer(RUN / ("rpointer." + component), expected_name(component))
    for component in KINDS:
        if read_pointer(RUN / ("rpointer." + component)) != expected_name(component):
            stop("Pointer verification failed for " + component)
        if sha(RUN / expected_name(component)) != sums[component]:
            stop("Restart SHA256 mismatch: " + component)
    # Do not run case.setup --reset, rebuild, or alter forcing/CO2.
    preview = subprocess.run(["./preview_run"], cwd=CASE, text=True,
                             capture_output=True)
    (session / "preview_run.log").write_text(preview.stdout + "\n" + preview.stderr)
    if preview.returncode:
        stop("preview_run failed; inspect " + str(session / "preview_run.log"))
    record = {
        "name": NAME, "checkpoint": STAMP, "completed_model_years": 810,
        "target_model_years": 1000, "resubmit": EXPECTED_RESUBMIT,
        "source_restart_sha256": sums,
        "case_status_sha256": sha(CASE / "CaseStatus"),
        "user_nl_clm_sha256": sha(CASE / "user_nl_clm"),
        "user_nl_datm_streams_sha256": sha(CASE / "user_nl_datm_streams"),
    }
    (session / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    (session / "PREPARED").write_text("No jobs submitted.\n")
    print("PREPARED ONLY: no jobs submitted.")
    print("SESSION=" + str(session))
    print("NEXT: python3 SCRIPT submit " + str(session))

def submit(session):
    session = Path(session).resolve()
    if session.parent != BACKUPROOT.resolve() or not session.is_dir():
        stop("SESSION must be a prepare-generated DE-Hai recovery folder")
    if not (session / "PREPARED").is_file():
        stop("Session is not PREPARED")
    if (session / "SUBMIT_STARTED").exists():
        stop("This session already attempted submission. Never submit twice.")
    record = json.loads((session / "manifest.json").read_text())
    if record["checkpoint"] != STAMP or record["name"] != NAME:
        stop("Session belongs to a different site/checkpoint")
    sums = preflight()
    if sums != record["source_restart_sha256"]:
        stop("Archived restart hashes changed since prepare")
    for key, filename in (("case_status_sha256", "CaseStatus"),
                          ("user_nl_clm_sha256", "user_nl_clm"),
                          ("user_nl_datm_streams_sha256", "user_nl_datm_streams")):
        if sha(CASE / filename) != record[key]:
            stop(filename + " changed since prepare")
    for component in KINDS:
        if read_pointer(RUN / ("rpointer." + component)) != expected_name(component):
            stop("Active restart pointer mismatch: " + component)
        if sha(RUN / expected_name(component)) != sums[component]:
            stop("Staged restart hash mismatch: " + component)
    # One-shot marker BEFORE calling CIME prevents accidental duplicate submissions.
    (session / "SUBMIT_STARTED").write_text(datetime.now().isoformat() + "\n")
    print("SUBMITTING ONE EXISTING DE-HAI CASE (no other sites)...", flush=True)
    p = subprocess.run(["./case.submit"], cwd=CASE, text=True,
                       capture_output=True)
    (session / "case_submit.log").write_text(p.stdout + "\n" + p.stderr)
    print(p.stdout)
    if p.stderr:
        print(p.stderr, file=sys.stderr)
    if p.returncode:
        stop("case.submit returned failure; do not retry blindly. Inspect " +
             str(session / "case_submit.log"))
    (session / "SUBMITTED").write_text("case.submit returned zero; verify Slurm.\n")
    print("case.submit returned 0; this is NOT proof of model success.")
    print("Verify squeue, CaseStatus, sacct and the next 2815 checkpoint.")

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "inspect":
        inspect()
    elif len(sys.argv) == 2 and sys.argv[1] == "prepare":
        prepare()
    elif len(sys.argv) == 3 and sys.argv[1] == "submit":
        submit(sys.argv[2])
    else:
        stop("Usage: python3 SCRIPT inspect | prepare | submit SESSION")

if __name__ == "__main__":
    main()

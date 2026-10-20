#!/usr/bin/env python3
"""Stage38: guarded DE-Lnf Slurm 8G memory repair for existing S30SHARED spin-up.

Usage:
  python3 38_fix_DE_Lnf_batch_memory_after_quota.py audit
  python3 38_fix_DE_Lnf_batch_memory_after_quota.py repair

This code NEVER submits/cancels Slurm jobs, changes science inputs or resets
RESUBMIT. Repair snapshots CIME case inputs then updates the authoritative
env_batch.xml and regenerates batch scripts with case.setup --reset. Run only
after verifying all model/archive jobs for this case have left the queue.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SITE = "DE-Lnf"
NAME = "DE-Lnf_FATES_SPINUP1000_S30SHARED"
CASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases") / NAME
OUT = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
BACKUP_ROOT = OUT / "recovery_backups" / "FLUXNET_MultiSite_13" / "post_inode_quota"
EXPECTED_MPI = "srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"
FLAGS = ("--nodes=1", "--ntasks-per-node=1", "--cpus-per-task=1", "--mem=8G")
CHECK_KEYS = ("CASE", "RUN_STARTDATE", "RUN_TYPE", "CONTINUE_RUN", "RESUBMIT",
              "STOP_N", "REST_N", "CALENDAR", "ATM_NCPL", "RUNDIR",
              "DOUT_S_ROOT", "EXEROOT", "CLM_CO2_TYPE", "CCSM_CO2_PPMV",
              "MPI_RUN_COMMAND")


def cmd(args, cwd=None, timeout=240):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"{args!r} rc={p.returncode}: {(p.stdout+p.stderr)[-2000:]}")
    return p.stdout.strip()


def xml(key):
    return cmd(["./xmlquery", key, "--value"], cwd=CASE, timeout=30)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def queue_ok():
    lines = cmd(["squeue", "-h", "-u", "ly3n24", "-o", "%i|%j|%T|%R"]).splitlines()
    active = [x for x in lines if len(x.split("|", 3)) == 4
              and x.split("|", 3)[1] in ("run." + NAME, "st_archive." + NAME)]
    if active:
        raise RuntimeError("DE-Lnf already has Slurm jobs; STOP: " + "; ".join(active))


def batch_flags(p):
    if not p.is_file():
        raise RuntimeError(f"Missing batch script: {p}")
    txt = p.read_text(errors="replace")
    return [flag for flag in FLAGS
            if not re.search(r"(?m)^\s*#SBATCH\s+" + re.escape(flag) + r"\s*$", txt)]


def authoritative_edit(s):
    needle = "<directive>--cpus-per-task={{ thread_count }}</directive>"
    mem = "<directive>--mem=8G</directive>"
    if s.count(needle) != 1:
        raise RuntimeError("Unexpected env_batch.xml CPU template; refuse edit")
    existing = re.findall(r"<directive>\s*--mem(?:=|\s+)[^<]*</directive>", s)
    if existing and (len(existing) != 1 or existing[0] != mem):
        raise RuntimeError(f"Conflicting memory directive(s): {existing}")
    if "--exclusive" in s:
        raise RuntimeError("Unexpected --exclusive in env_batch.xml")
    updated = s if existing else s.replace(needle, needle + "\n        " + mem, 1)
    ET.fromstring(updated)
    return updated


def audit():
    queue_ok()
    if not (CASE / "xmlquery").is_file():
        raise RuntimeError(f"Original CIME case missing: {CASE}")
    values = {key: xml(key) for key in CHECK_KEYS}
    if values["CASE"] != NAME:
        raise RuntimeError("Unexpected CASE name")
    if values["MPI_RUN_COMMAND"] != EXPECTED_MPI:
        raise RuntimeError("Unexpected PMIx launcher; fix separately before Stage38")
    if values["RUN_STARTDATE"] != "2002-01-01":
        raise RuntimeError("Unexpected original start year")
    if values["CONTINUE_RUN"].upper() != "TRUE":
        raise RuntimeError("This is not an existing restart continuation")
    if values["RESUBMIT"] != "189":
        raise RuntimeError("Resubmission state changed; investigate before repair")
    if not (Path(values["EXEROOT"]) / "cesm.exe").is_file():
        raise RuntimeError("Missing existing compiled cesm.exe")
    if (CASE / ".git/index.lock").exists():
        raise RuntimeError("Case .git/index.lock exists; stop and inspect")
    p = CASE / "env_batch.xml"
    if not p.is_file():
        raise RuntimeError("Missing env_batch.xml")
    old = p.read_text()
    new = authoritative_edit(old)
    for filename in (".case.run", "case.st_archive"):
        print(f"{filename}: missing flags {batch_flags(CASE / filename)}")
    print("env_batch.xml:", "needs --mem=8G" if old != new
          else "already requests --mem=8G")
    print("CASE", values["CASE"])
    print("RESUBMIT", values["RESUBMIT"], "CONTINUE_RUN", values["CONTINUE_RUN"])
    print("MPI_RUN_COMMAND", values["MPI_RUN_COMMAND"])
    print("AUDIT PASS. No case files or jobs changed.")
    return values, old, new


def repair():
    before, old, new = audit()
    needs = any(batch_flags(CASE / f) for f in (".case.run", "case.st_archive"))
    if not needs and new == old:
        print("Batch directives already valid; no repair needed.")
        return
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix="DE-Lnf_mem8G_", dir=BACKUP_ROOT))
    print("BACKUP=", backup, sep="", flush=True)
    for fname in ("env_batch.xml", "env_run.xml", "env_mach_specific.xml",
                  "env_case.xml", "env_build.xml", "env_workflow.xml",
                  ".case.run", "case.st_archive", "CaseStatus",
                  "user_nl_clm", "user_nl_datm_streams"):
        f = CASE / fname
        if f.is_file():
            shutil.copy2(f, backup / fname)
    if (CASE / "LockedFiles").is_dir():
        shutil.copytree(CASE / "LockedFiles", backup / "LockedFiles", symlinks=True)
    science = {n: sha(CASE / n) for n in ("user_nl_clm", "user_nl_datm_streams")
               if (CASE / n).is_file()}
    queue_ok()
    (CASE / "env_batch.xml").write_text(new)
    (backup / "case_setup.log").write_text(
        cmd(["./case.setup", "--reset"], cwd=CASE) + "\n"
    )
    # case.setup --reset may invalidate the build-complete CIME flag. Reuse
    # the unchanged, already compiled executable; do not rebuild model physics.
    if xml("BUILD_COMPLETE").upper() != "TRUE":
        if xml("EXEROOT") != before["EXEROOT"] or not (
                Path(before["EXEROOT"]) / "cesm.exe").is_file():
            raise RuntimeError("Executable provenance changed; stop")
        cmd(["./xmlchange", "BUILD_COMPLETE=TRUE"], cwd=CASE)
    for key, expected in before.items():
        if xml(key) != expected:
            raise RuntimeError(f"{key} unexpectedly changed; backup at {backup}")
    for name, checksum in science.items():
        if sha(CASE / name) != checksum:
            raise RuntimeError(f"{name} changed; backup at {backup}")
    for filename in (".case.run", "case.st_archive"):
        missing = batch_flags(CASE / filename)
        if missing:
            raise RuntimeError(f"{filename} still missing {missing}; backup at {backup}")
        if "--exclusive" in (CASE / filename).read_text(errors="replace"):
            raise RuntimeError(f"Unexpected --exclusive in {filename}")
    preview = cmd(["./preview_run"], cwd=CASE)
    (backup / "preview_run.txt").write_text(preview + "\n")
    if EXPECTED_MPI not in preview:
        raise RuntimeError("preview_run does not show expected launcher; inspect backup")
    (backup / "MEMORY_REPAIR_VALIDATED").write_text(
        datetime.now(timezone.utc).isoformat() + "\n")
    print("REPAIRED: DE-Lnf model+archive jobs request 1 CPU/8G, no exclusive.")
    print("No Slurm job submitted or canceled. Re-run Stage37 inspect.")
    print("BACKUP=", backup, sep="")


if __name__ == "__main__":
    try:
        if os.environ.get("USER") != "ly3n24":
            raise RuntimeError("Wrong user")
        if sys.argv[1:] == ["audit"]:
            audit()
        elif sys.argv[1:] == ["repair"]:
            repair()
        else:
            raise RuntimeError("Usage: SCRIPT audit | repair")
    except Exception as exc:
        print("STAGE38 STOP:", exc, file=sys.stderr)
        sys.exit(1)

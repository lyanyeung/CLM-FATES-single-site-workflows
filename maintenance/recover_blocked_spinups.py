#!/usr/bin/env python3
"""Checkpoint-safe, one-command recovery for four CLM-FATES multisite batches.

On IRIDIS6:
  python3 maintenance/recover_blocked_spinups.py inspect
  python3 maintenance/recover_blocked_spinups.py run

Restarts existing CIME cases from complete three-component short-term archives.
Only cancels exact-match PENDING DependencyNeverSatisfied Slurm jobs; does not
cancel running/pending healthy jobs or delete scientific output. Each site's
failure is isolated. case.submit success is NOT scientific completion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from check_four_spinups import (
    BATCHES, CASE_ROOT, OUTPUT_ROOT, case_name, restart_status,
    unarchived_success,
)

ACCOUNT = "ly3n24"
MPI = "srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"
BACKUPS = OUTPUT_ROOT / "recovery_backups/four_batches_dependency_20261021"
PARTS = {"cpl": "cpl.r", "atm": "datm.r", "lnd": "clm2.r"}
SCIENCE = ("user_nl_clm", "user_nl_datm_streams")
CASE_BACKUPS = (
    "CaseStatus", "env_run.xml", "env_batch.xml", "env_build.xml",
    "env_case.xml", "env_archive.xml", ".case.run", "case.st_archive",
    *SCIENCE,
)


class Stop(Exception):
    pass


def cmd(args, cwd=None, timeout=180, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True,
                       timeout=timeout)
    if check and p.returncode:
        raise Stop(f"{args!r} returned {p.returncode}: "
                   f"{(p.stdout + p.stderr)[-1200:]}")
    return p


def xval(case, key):
    return cmd(["./xmlquery", key, "--value"], cwd=case).stdout.strip()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda: fd.read(2 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def jobs_for(name):
    raw = cmd(["squeue", "-h", "-u", ACCOUNT,
               "-o", "%i|%.150j|%T|%R"], timeout=60).stdout
    found = []
    for line in raw.splitlines():
        a = [x.strip() for x in line.split("|", 3)]
        if len(a) == 4 and a[1] in ("run." + name, "st_archive." + name):
            found.append(dict(id=a[0], name=a[1], state=a[2], reason=a[3]))
    return found


def dead_dependency(job):
    return (job["state"] == "PENDING"
            and "DependencyNeverSatisfied" in job["reason"])


def dismiss_dead_dependencies(name):
    found = jobs_for(name)
    if any(not dead_dependency(j) for j in found):
        raise Stop(f"Active/healthy jobs exist: {found}")
    for j in found:
        cmd(["scancel", j["id"]], timeout=60)
    for _ in range(30):
        if not jobs_for(name):
            return found
        time.sleep(1)
    raise Stop("Slurm still lists old jobs after scancel; do not submit")


def pointer(path):
    if path.is_symlink() or not path.is_file():
        raise Stop(f"Missing/symlinked pointer: {path}")
    lines = path.read_text(errors="replace").splitlines()
    if not lines:
        raise Stop(f"Empty pointer: {path}")
    return lines[0].strip().removeprefix("./")


def valid_nc(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size < 1024:
        return False
    with path.open("rb") as fd:
        header = fd.read(8)
    return header[:3] == b"CDF" or header == b"\x89HDF\r\n\x1a\n"


def inspect_case(batch, site, check_jobs=True):
    start, target = BATCHES[batch][site]
    name = case_name(batch, site)
    case = CASE_ROOT / name
    run = OUTPUT_ROOT / name / "run"
    rest = OUTPUT_ROOT / "archive" / name / "rest"
    if not case.is_dir() or not run.is_dir() or not rest.is_dir():
        raise Stop("Missing case, run or archive directory: " + name)
    if (case / ".git/index.lock").exists():
        raise Stop("CIME Git index.lock exists; investigate before editing")
    if check_jobs and jobs_for(name):
        raise Stop("Other Slurm jobs still queued for this case")
    for f in ("xmlquery", "xmlchange", "case.submit", "preview_run",
              ".case.run", "case.st_archive", "CaseStatus", *SCIENCE):
        if not (case / f).is_file():
            raise Stop(f"Case file missing: {f}")
    checks = {
        "CASE": name, "RUN_STARTDATE": f"{start}-01-01",
        "STOP_OPTION": "nyears", "STOP_N": "5",
        "REST_OPTION": "nyears", "REST_N": "5",
        "CONTINUE_RUN": "TRUE", "BUILD_COMPLETE": "TRUE",
        "DOUT_S": "TRUE", "CALENDAR": "NO_LEAP", "ATM_NCPL": "48",
        "RUNDIR": str(run), "DOUT_S_ROOT": str(rest.parent),
    }
    for key, expected in checks.items():
        actual = xval(case, key)
        if actual.upper() != expected.upper():
            raise Stop(f"{name}: {key}={actual!r} expected {expected!r}")
    expected_type = ("branch" if (batch, site) ==
                     ("FLUXNET_MultiSite_11", "IT-Noe") else "startup")
    if xval(case, "RUN_TYPE").lower() != expected_type:
        raise Stop(f"RUN_TYPE mismatch for {name}")
    if expected_type == "branch" and xval(case, "RUN_REFDATE") != "2009-01-01":
        raise Stop("IT-Noe branch RUN_REFDATE unexpectedly changed")
    if xval(case, "MPILIB").lower() != "openmpi":
        raise Stop("Unexpected MPILIB")
    for component in ("ATM", "LND", "CPL"):
        if (xval(case, "NTASKS_" + component) != "1"
                or xval(case, "NTHRDS_" + component) != "1"):
            raise Stop(f"Unexpected processor layout: {component}")
    if not (Path(xval(case, "EXEROOT")) / "cesm.exe").is_file():
        raise Stop("Compiled cesm.exe is missing")
    if unarchived_success(case):
        raise Stop("Newer model success without successful archive: inspect first")
    done, stamp, warning = restart_status(rest, name, start)
    if done is None or stamp is None or warning:
        raise Stop(f"No unambiguous complete archived checkpoint: {warning}")
    if done >= target:
        return dict(complete=True, name=name, done=done, target=target)
    if done < 5 or done % 5 or (target - done) % 5:
        raise Stop(f"Invalid checkpoint count {done}/{target}")
    refs = {}
    for comp, kind in PARTS.items():
        fname = f"{name}.{kind}.{stamp}.nc"
        source = rest / stamp / fname
        ptr = rest / stamp / f"rpointer.{comp}.{stamp}"
        if pointer(ptr) != fname or not valid_nc(source):
            raise Stop(f"Invalid {comp} archived checkpoint at {stamp}")
        refs[comp] = (source, run / fname, fname)
    newer = []
    newer_components = {}
    for comp, kind in PARTS.items():
        regex = re.compile(re.escape(f"{name}.{kind}.") +
                           r"(\d{4}-\d\d-\d\d-\d{5})\.nc$")
        for p in run.glob(f"{name}.{kind}.*.nc"):
            m = regex.fullmatch(p.name)
            if m and m[1] > stamp:
                if p.is_symlink() or not p.is_file():
                    raise Stop(f"Unexpected newer file: {p}")
                newer.append(p)
                newer_components.setdefault(m[1], set()).add(comp)
    if any(v == set(PARTS) for v in newer_components.values()):
        raise Stop("Newer full unarchived checkpoint exists; preserve it")
    partial = []
    hrx = re.compile(re.escape(name) + r"\.clm2\.h[^.]*\.(\d{4})-")
    for p in run.glob(f"{name}.clm2.h*.nc"):
        match = hrx.match(p.name)
        if not match:
            raise Stop("Unexpected history filename: " + p.name)
        if int(match[1]) >= int(stamp[:4]):
            if p.is_symlink() or not p.is_file():
                raise Stop(f"Unexpected history file: {p}")
            partial.append(p)
    return dict(batch=batch, site=site, name=name, case=case, run=run,
                done=done, target=target, stamp=stamp, refs=refs,
                newer=newer, partial=partial,
                resubmit=(target - done) // 5 - 1)


def atomic_copy(src, dst):
    if dst.is_symlink():
        raise Stop(f"Refusing symlink overwrite: {dst}")
    fd, tmp = tempfile.mkstemp(prefix=".recover_", dir=dst.parent)
    os.close(fd)
    try:
        shutil.copy2(src, tmp)
        if sha(Path(tmp)) != sha(src):
            raise Stop(f"Failed to copy verified checkpoint {src}")
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def atomic_pointer(content, dst):
    if dst.is_symlink():
        raise Stop(f"Refusing symlink overwrite: {dst}")
    fd, tmp = tempfile.mkstemp(prefix=".pointer_", dir=dst.parent, text=True)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def stage_and_submit(info, session):
    case, run = info["case"], info["run"]
    snapshots = session / "original_case"
    snapshots.mkdir()
    for name in CASE_BACKUPS:
        src = case / name
        if src.is_file():
            shutil.copy2(src, snapshots / name)
    oldptr = session / "original_pointers"
    oldptr.mkdir()
    for comp in PARTS:
        p = run / f"rpointer.{comp}"
        if p.is_symlink():
            raise Stop(f"Runtime pointer is symlink: {p}")
        if p.is_file():
            shutil.copy2(p, oldptr / p.name)
    science_hash = {x: sha(case / x) for x in SCIENCE}
    source_hash = {c: sha(src) for c, (src, _, _) in info["refs"].items()}
    isolated = session / "interrupted_output"
    isolated.mkdir()
    for p in info["newer"] + info["partial"]:
        # Same scratch filesystem: rename preserves interrupted output.
        os.replace(p, isolated / p.name)
    for comp, (src, dst, fname) in info["refs"].items():
        if dst.is_symlink():
            raise Stop(f"Unexpected checkpoint symlink: {dst}")
        if dst.is_file() and sha(dst) != source_hash[comp]:
            backups = session / "replaced_runtime_restarts"
            backups.mkdir(exist_ok=True)
            os.replace(dst, backups / dst.name)
        if not dst.is_file():
            atomic_copy(src, dst)
        if sha(dst) != source_hash[comp]:
            raise Stop("Staged checkpoint checksum mismatch: " + comp)
        active_ptr = run / f"rpointer.{comp}"
        atomic_pointer(fname + "\n", active_ptr)
        if pointer(active_ptr) != fname:
            raise Stop("Active pointer mismatch: " + comp)
    if xval(case, "MPI_RUN_COMMAND") != MPI:
        cmd(["./xmlchange", "MPI_RUN_COMMAND=" + MPI], cwd=case)
    if xval(case, "RESUBMIT") != str(info["resubmit"]):
        cmd(["./xmlchange", "RESUBMIT=" + str(info["resubmit"])], cwd=case)
    if (xval(case, "RESUBMIT") != str(info["resubmit"])
            or xval(case, "MPI_RUN_COMMAND") != MPI):
        raise Stop("Failed to set RESUBMIT or PMIx launcher")
    if {x: sha(case / x) for x in SCIENCE} != science_hash:
        raise Stop("Scientific namelist changed unexpectedly")
    preview = cmd(["./preview_run"], cwd=case, check=False)
    (session / "preview_run.log").write_text(preview.stdout + "\n" +
                                              preview.stderr)
    if preview.returncode or MPI not in preview.stdout + preview.stderr:
        raise Stop("CIME preview_run failed; do not submit")
    hashes = dict(checkpoint=source_hash,
                  casestatus=sha(case / "CaseStatus"),
                  env_run=sha(case / "env_run.xml"))
    manifest = dict(site=info["site"], batch=info["batch"],
                    case=info["name"], checkpoint=info["stamp"],
                    done=info["done"], target=info["target"],
                    resubmit=info["resubmit"], checksums=hashes)
    (session / "manifest.json").write_text(json.dumps(manifest, indent=2) +
                                           "\n")
    (session / "PREPARED").write_text(datetime.now(timezone.utc).isoformat())
    if jobs_for(info["name"]):
        raise Stop("New Slurm job appeared before case.submit")
    if (sha(case / "CaseStatus") != hashes["casestatus"]
            or sha(case / "env_run.xml") != hashes["env_run"]):
        raise Stop("CIME case changed between preparation and submission")
    for comp, (_, dst, fname) in info["refs"].items():
        if (pointer(run / f"rpointer.{comp}") != fname
                or sha(dst) != source_hash[comp]):
            raise Stop("Prepared restart changed before submission")
    # One-shot marker, written before any possible Slurm side effect.
    (session / "SUBMIT_ATTEMPTED").write_text(
        datetime.now(timezone.utc).isoformat() + "\n")
    submitted = cmd(["./case.submit"], cwd=case, timeout=240, check=False)
    (session / "submit.log").write_text(
        submitted.stdout + "\n" + submitted.stderr +
        f"\nRETURN_CODE={submitted.returncode}\n")
    if submitted.returncode:
        raise Stop(f"case.submit failed; see {session / 'submit.log'}")
    (session / "SUBMITTED").write_text(
        "CIME accepted submission; model and archive not yet verified.\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("inspect", "run"))
    ap.add_argument("--batch", choices=("all", *BATCHES), default="all")
    ap.add_argument("--site", default=None)
    args = ap.parse_args()
    if (os.geteuid() == 0 or os.environ.get("USER") != ACCOUNT
            or cmd(["id", "-un"]).stdout.strip() != ACCOUNT):
        raise SystemExit("Run on IRIDIS6 as ly3n24, not as root")
    # Avoid two overlapping bulk submissions from separate SSH sessions.
    with (Path.home() / ".four_batch_dependency_recovery.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Another bulk recovery is still active")
        selected = [(batch, site) for batch, group in BATCHES.items()
                    if args.batch in ("all", batch) for site in group
                    if args.site is None or site == args.site]
        if not selected:
            raise SystemExit("No matching site")
        if args.mode == "inspect":
            for batch, site in selected:
                name = case_name(batch, site)
                old = jobs_for(name)
                if old and all(dead_dependency(j) for j in old):
                    job_block = False
                else:
                    job_block = bool(old)
                try:
                    d = inspect_case(batch, site, check_jobs=job_block)
                    phase = ("COMPLETE" if d.get("complete")
                             else "READY_AFTER_CANCEL" if old else "READY")
                    desc = f"{d['done']}/{d['target']}"
                except Exception as exc:
                    phase, desc = "REVIEW", str(exc)
                print(f"{batch:21} {site:8} {phase:20} {desc}", flush=True)
            print("READ ONLY: no CIME case or Slurm job changed.")
            return 0
        BACKUPS.mkdir(parents=True, exist_ok=True)
        session = Path(tempfile.mkdtemp(prefix="bulk_", dir=BACKUPS))
        print("BULK_SESSION=" + str(session), flush=True)
        counts = {}
        for index, (batch, site) in enumerate(selected, 1):
            name = case_name(batch, site)
            dest = session / batch / site
            dest.mkdir(parents=True)
            result = dict(batch=batch, site=site, case=name)
            try:
                result["cancelled"] = dismiss_dead_dependencies(name)
                d = inspect_case(batch, site)
                result["progress"] = f"{d['done']}/{d['target']}"
                if d.get("complete"):
                    result["status"] = "COMPLETE"
                else:
                    site_session = dest / "recovery"
                    site_session.mkdir()
                    result["recovery_session"] = str(site_session)
                    stage_and_submit(d, site_session)
                    result["status"] = "SUBMITTED"
            except Exception as exc:
                result["status"] = "REVIEW"
                result["reason"] = str(exc)
            counts[result["status"]] = counts.get(result["status"], 0) + 1
            (dest / "result.json").write_text(
                json.dumps(result, indent=2, ensure_ascii=False) + "\n")
            print(f"[{index}/{len(selected)}] {batch}/{site} "
                  f"{result['status']} {result.get('progress', '')} "
                  f"{result.get('reason', '')[:250]}", flush=True)
        print("SUMMARY=" + json.dumps(counts, sort_keys=True))
        print("BULK_SESSION=" + str(session))
        print("SUBMITTED means case.submit succeeded; check future MODEL/ARCHIVE.")
        return 1 if counts.get("REVIEW") else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Stop, OSError, subprocess.TimeoutExpired) as exc:
        print("FATAL: " + str(exc), file=sys.stderr)
        sys.exit(2)

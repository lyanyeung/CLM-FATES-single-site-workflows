#!/usr/bin/env python3
"""Single-site, checkpoint-safe NL-Loo restart after failed run 4459256.

Modes: inspect, cancel-blocked, prepare-test, promote-test TEST_SESSION,
       verify-test, prepare-continuation, submit SESSION.
Only 'cancel-blocked' invokes scancel; only 'submit' starts a CIME job.
The optional test runs ONE 5-year segment with RESUBMIT=0.
'promote-test' converts a never-submitted prepared test to a guarded
direct 1370->3000 continuation (RESUBMIT=325); no intervening model run.
The standard continuation follows a tested 3372 checkpoint.
No other site is readied, edited, submitted, or cancelled.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

USER = "ly3n24"
NAME = "NL-Loo_FATES_SPINUP500"
START = 1997
CASE = Path(f"/iridisfs/scratch/{USER}/CLM_FATES/cases/{NAME}")
OUTPUT = Path(f"/scratch/{USER}/CTSM_FATES_OUTPUTS")
RUN = OUTPUT / NAME / "run"
REST = OUTPUT / "archive" / NAME / "rest"
BACKUP = Path.home() / "NL_Loo_recovery_20261021"
PARTS = {"cpl": "cpl.r", "atm": "datm.r", "lnd": "clm2.r"}
OLD_ARCHIVE = "4459257"
OLD_FAILED_RUN = "4459256"


class Stop(Exception):
    pass


def command(argv, cwd=None, timeout=120):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise Stop(f"{argv}: exit {p.returncode}\n{p.stderr[-2200:]} {p.stdout[-800:]}")
    return p.stdout.strip()


def xml(key):
    return command([str(CASE / "xmlquery"), key, "--value"], cwd=CASE).strip()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def queue():
    raw = command(["squeue", "-h", "-u", USER, "-o", "%i|%j|%T|%R"])
    rows = [x.split("|", 3) for x in raw.splitlines()]
    return [r for r in rows if len(r) == 4 and r[1] in
            (f"run.{NAME}", f"st_archive.{NAME}")]


def latest():
    if not REST.is_dir():
        raise Stop("Archive rest directory missing")
    dates = sorted(p.name for p in REST.iterdir()
                   if p.is_dir() and re.fullmatch(r"\d{4}-01-01-00000", p.name))
    if not dates:
        raise Stop("No archive checkpoints")
    return dates[-1]


def checkpoint(stamp):
    refs = {}
    folder = REST / stamp
    for comp, suffix in PARTS.items():
        filename = f"{NAME}.{suffix}.{stamp}.nc"
        nc = folder / filename
        ptr = folder / f"rpointer.{comp}.{stamp}"
        if not nc.is_file() or nc.stat().st_size < 1024 or not ptr.is_file():
            raise Stop(f"Missing archived restart or pointer: {nc} / {ptr}")
        pointed = ptr.read_text(errors="replace").splitlines()[0].strip().removeprefix("./")
        if pointed != filename:
            raise Stop(f"Archived {comp} pointer mismatch: {pointed}")
        command(["ncdump", "-k", str(nc)])
        refs[comp] = {"filename": filename, "nc": str(nc), "ptr": str(ptr),
                      "sha256": digest(nc)}
    return refs


def case_check():
    if os.environ.get("USER") not in (USER, None):
        raise Stop("Wrong IRIDIS user")
    for f in ("CaseStatus", "env_run.xml", "case.submit", "xmlquery", "xmlchange"):
        if not (CASE / f).is_file():
            raise Stop(f"Missing CIME case file: {f}")
    if not RUN.is_dir():
        raise Stop("CIME run directory missing")
    expected = {
        "CASE": NAME, "RUN_TYPE": "startup", "RUN_STARTDATE": "1997-01-01",
        "CONTINUE_RUN": "TRUE", "STOP_OPTION": "nyears", "STOP_N": "5",
        "REST_OPTION": "nyears", "REST_N": "5", "BUILD_COMPLETE": "TRUE",
        "DOUT_S": "TRUE", "DOUT_S_ROOT": str(OUTPUT / "archive" / NAME),
        "RUNDIR": str(RUN), "CALENDAR": "NO_LEAP", "ATM_NCPL": "48",
    }
    for key, value in expected.items():
        if xml(key) != value:
            raise Stop(f"Unexpected {key}={xml(key)!r} (expected {value!r})")
    mpi = xml("MPI_RUN_COMMAND")
    if not mpi.startswith("srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"):
        raise Stop(f"Unexpected MPI_RUN_COMMAND: {mpi}")
    if not (Path(xml("EXEROOT")) / "cesm.exe").is_file():
        raise Stop("Shared model executable missing")


def partial_files(stamp):
    year = int(stamp[:4])
    files = []
    for f in RUN.glob(f"{NAME}.clm2.h*.nc"):
        m = re.search(r"\.h[^.]*\.(\d{4})-", f.name)
        if m and int(m.group(1)) >= year:
            files.append(str(f))
    for f in RUN.glob(f"{NAME}.*.r.????-01-01-00000.nc"):
        m = re.search(r"\.r\.(\d{4})-01-01-00000\.nc$", f.name)
        if m and int(m.group(1)) > year:
            files.append(str(f))
    return sorted(files)


def preflight(stamp):
    case_check()
    jobs = queue()
    if jobs:
        raise Stop(f"NL-Loo has queued/running jobs: {jobs}; do not touch")
    found = latest()
    if found != stamp:
        raise Stop(f"Archive changed: expected {stamp}, found {found}")
    refs = checkpoint(stamp)
    partial = partial_files(stamp)
    if partial:
        raise Stop("Possible partial/unarchived model files (preserve for manual review):\n"
                   + "\n".join(partial[:25]))
    return refs


def inspect():
    case_check()
    stamp = latest()
    refs = checkpoint(stamp)
    done = int(stamp[:4]) - START
    print(f"NL-Loo ARCHIVED={done}/3000 LEFT={3000-done} CHECKPOINT={stamp}")
    print(f"RESUBMIT={xml('RESUBMIT')} SLURM={queue() or 'NONE'}")
    for comp, r in refs.items():
        print(f"ARCHIVE {comp}: {r['filename']}  SHA256={r['sha256']}")
    print("POTENTIAL_PARTIAL_OUTPUT:", partial_files(stamp) or "NONE")
    print("CASESTATUS TAIL:\n" + "\n".join(
          (CASE / "CaseStatus").read_text(errors="replace").splitlines()[-18:]))
    print("READ ONLY.")


def cancel_blocked():
    case_check()
    jobs = queue()
    if not jobs:
        print("No NL-Loo jobs remain; no cancellation needed")
        return
    if len(jobs) != 1 or jobs[0][:3] != [
            OLD_ARCHIVE, f"st_archive.{NAME}", "PENDING"] or (
            "DependencyNeverSatisfied" not in jobs[0][3]):
        raise Stop(f"Unexpected NL-Loo jobs; refused to cancel: {jobs}")
    details = command(["scontrol", "show", "job", OLD_ARCHIVE, "-o"])
    for required in (f"JobId={OLD_ARCHIVE}", f"JobName=st_archive.{NAME}",
                     "Reason=DependencyNeverSatisfied",
                     f"Dependency=afterok:{OLD_FAILED_RUN}(failed)"):
        if required not in details:
            raise Stop(f"Unexpected dependency: {details}")
    accounting = command(["sacct", "-n", "-X", "-j", OLD_FAILED_RUN,
                          "--format=JobID,State", "-P"])
    if f"{OLD_FAILED_RUN}|FAILED" not in accounting:
        raise Stop(f"Upstream FAILED status not verified: {accounting}")
    command(["scancel", OLD_ARCHIVE])
    print(f"Cancelled ONLY stale archive job {OLD_ARCHIVE}; verify queue again")


def prepare(mode):
    stamp = "3367-01-01-00000" if mode == "test" else "3372-01-01-00000"
    refs = preflight(stamp)
    done = int(stamp[:4]) - START
    left = 3000 - done
    if left <= 0 or left % 5:
        raise Stop("Invalid 5-year segment count")
    resubmit = 0 if mode == "test" else left // 5 - 1
    if mode == "test" and xml("RESUBMIT") not in ("325", "0"):
        raise Stop("Unexpected RESUBMIT before one-segment test")
    if mode == "continuation" and xml("RESUBMIT") != "0":
        raise Stop("Test not finished with RESUBMIT=0")
    session = BACKUP / (mode + "_" +
                        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                        + "_" + str(os.getpid()))
    session.mkdir(parents=True, exist_ok=False)
    print(f"SESSION={session}", flush=True)
    for f in ("CaseStatus", "env_run.xml", "env_batch.xml",
              "env_mach_specific.xml"):
        src = CASE / f
        if src.is_file():
            shutil.copy2(src, session / f)
    (session / "old_pointers").mkdir()
    for comp in PARTS:
        pointer = RUN / f"rpointer.{comp}"
        if pointer.is_file():
            shutil.copy2(pointer, session / "old_pointers" / pointer.name)
    for comp, d in refs.items():
        dst = RUN / d["filename"]
        if dst.is_file() and digest(dst) != d["sha256"]:
            sub = session / "replaced_runtime_restarts"
            sub.mkdir(exist_ok=True)
            shutil.copy2(dst, sub / dst.name)
        shutil.copy2(d["nc"], dst)
        if digest(dst) != d["sha256"]:
            raise Stop(f"Checksum failure restaging {comp}")
        shutil.copy2(d["ptr"], RUN / f"rpointer.{comp}")
    command([str(CASE / "xmlchange"), f"RESUBMIT={resubmit}"], cwd=CASE)
    if xml("RESUBMIT") != str(resubmit):
        raise Stop("RESUBMIT xmlchange failed")
    preview = command([str(CASE / "preview_run")], cwd=CASE, timeout=120)
    (session / "preview_run.log").write_text(preview + "\n")
    manifest = {
        "case": NAME, "mode": mode, "checkpoint": stamp, "done": done,
        "target": 3000, "left_segments": left // 5, "resubmit": resubmit,
        "restarts": refs, "env_run_sha256": digest(CASE / "env_run.xml"),
        "casestatus_sha256": digest(CASE / "CaseStatus"),
    }
    (session / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (session / "PREPARED").write_text(
        datetime.now(timezone.utc).isoformat() + "\n")
    print(f"PREPARED NL-Loo {done}/3000, resubmit={resubmit}; NO JOB SUBMITTED")
    print(f"Review: cat '{session}/manifest.json'")
    print(f"Then: python3 {Path(__file__).resolve()} submit '{session}'")



def promote_test(test_session_arg):
    """Convert an UNSUBMITTED prepared 3367 test into a direct 3000-y plan.

    Validate its recorded CIME and restart state, retire the old TEST session,
    change only RESUBMIT=325, and issue a NEW one-shot direct session.
    No Slurm job submitted here.
    """
    test_session = Path(test_session_arg).resolve()
    if (test_session.parent != BACKUP.resolve()
            or not (test_session / "PREPARED").is_file()):
        raise Stop("Not a valid prepared NL-Loo test session")
    m = json.loads((test_session / "manifest.json").read_text())
    if (m.get("case") != NAME or m.get("mode") != "test" or
            m.get("checkpoint") != "3367-01-01-00000" or
            m.get("done") != 1370 or m.get("resubmit") != 0 or
            m.get("left_segments") != 326):
        raise Stop("Test manifest is not the expected 1370-year one-segment preparation")
    if (test_session / "SUBMIT_ATTEMPTED").exists():
        raise Stop("Test session may already have been submitted; refusing promotion")
    if (test_session / "SUPERSEDED_BY").exists():
        raise Stop("Test session already superseded; refusing repeat promotion")

    refs = preflight(m["checkpoint"])
    if xml("RESUBMIT") != "0":
        raise Stop("Current RESUBMIT must still be 0 from prepare-test")
    if (digest(CASE / "env_run.xml") != m["env_run_sha256"] or
            digest(CASE / "CaseStatus") != m["casestatus_sha256"]):
        raise Stop("Case changed since prepare-test; refusing promotion")
    for comp, d in refs.items():
        if d["sha256"] != m["restarts"][comp]["sha256"]:
            raise Stop(f"Archived {comp} restart changed")
        staged = RUN / d["filename"]
        if not staged.is_file() or digest(staged) != d["sha256"]:
            raise Stop(f"Staged {comp} restart mismatch")
        pointer = RUN / f"rpointer.{comp}"
        if (not pointer.is_file() or
                pointer.read_text(errors="replace").splitlines()[0].strip().removeprefix("./")
                != d["filename"]):
            raise Stop(f"Staged {comp} pointer mismatch")

    new_session = BACKUP / ("direct_" +
                            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                            + "_" + str(os.getpid()))
    new_session.mkdir(parents=True, exist_ok=False)
    # Retire the old TEST session BEFORE changing the XML so it cannot be
    # submitted accidentally even if a later operation fails.
    old_marker = test_session / "SUPERSEDED_BY"
    fd = os.open(old_marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write(str(new_session) + "\n")
    for fname in ("CaseStatus", "env_run.xml", "env_batch.xml",
                  "env_mach_specific.xml"):
        src = CASE / fname
        if src.is_file():
            shutil.copy2(src, new_session / fname)

    command([str(CASE / "xmlchange"), "RESUBMIT=325"], cwd=CASE)
    if xml("RESUBMIT") != "325":
        raise Stop("RESUBMIT=325 change failed; do not submit")
    preview = command([str(CASE / "preview_run")], cwd=CASE, timeout=120)
    (new_session / "preview_run.log").write_text(preview + "\n")
    # Recheck after CIME's setup before recording a prepared session.
    preflight("3367-01-01-00000")
    manifest = {
        "case": NAME, "mode": "direct", "checkpoint": "3367-01-01-00000",
        "done": 1370, "target": 3000, "left_segments": 326,
        "resubmit": 325, "restarts": refs,
        "superseded_test_session": str(test_session),
        "env_run_sha256": digest(CASE / "env_run.xml"),
        "casestatus_sha256": digest(CASE / "CaseStatus"),
    }
    (new_session / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (new_session / "PREPARED").write_text(datetime.now(timezone.utc).isoformat() + "\n")
    print(f"SESSION={new_session}", flush=True)
    print("DIRECT PREPARED: 1370/3000, 326 five-year segments, RESUBMIT=325")
    print("NO JOB SUBMITTED. Prior test session is superseded.")
    print(f"Review: cat '{new_session}/manifest.json'")
    print(f"Then: python3 {Path(__file__).resolve()} submit '{new_session}'")


def submit(session_arg):
    session = Path(session_arg).resolve()
    if session.parent != BACKUP.resolve() or not (session / "PREPARED").is_file():
        raise Stop("Not a valid NL-Loo PREPARED session")
    m = json.loads((session / "manifest.json").read_text())
    if m["case"] != NAME or m["mode"] not in ("test", "continuation", "direct"):
        raise Stop("Unexpected session")
    if (session / "SUPERSEDED_BY").exists():
        raise Stop("TEST SESSION SUPERSEDED: use the new direct session instead")
    if (session / "SUBMIT_ATTEMPTED").exists():
        raise Stop("SUBMIT ALREADY ATTEMPTED: do not retry blindly")
    refs = preflight(m["checkpoint"])
    if xml("RESUBMIT") != str(m["resubmit"]):
        raise Stop("RESUBMIT changed since prepare")
    if digest(CASE / "env_run.xml") != m["env_run_sha256"] or (
            digest(CASE / "CaseStatus") != m["casestatus_sha256"]):
        raise Stop("Case configuration/status changed since prepare")
    for comp, d in refs.items():
        if d["sha256"] != m["restarts"][comp]["sha256"]:
            raise Stop("Archive checkpoint changed since prepare")
        target = RUN / d["filename"]
        if not target.is_file() or digest(target) != d["sha256"]:
            raise Stop(f"Staged {comp} restart changed")
        ptr = RUN / f"rpointer.{comp}"
        if not ptr.is_file() or ptr.read_text(errors="replace").splitlines()[0].strip().removeprefix("./") != d["filename"]:
            raise Stop(f"Staged {comp} rpointer changed")
    marker = session / "SUBMIT_ATTEMPTED"
    fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(datetime.now(timezone.utc).isoformat() + "\n")
    p = subprocess.run([str(CASE / "case.submit")], cwd=CASE,
                       capture_output=True, text=True, timeout=180)
    (session / "submit.stdout").write_text(p.stdout)
    (session / "submit.stderr").write_text(p.stderr)
    print(p.stdout[-3500:])
    if p.stderr:
        print(p.stderr[-2000:], file=sys.stderr)
    if p.returncode:
        raise Stop(f"case.submit returned {p.returncode}; inspect queue and logs, don't resubmit")
    print("Submission accepted. Check squeue, CaseStatus and archive success.")
    if m["mode"] == "test":
        print("TEST MODE: only one 5-year segment (RESUBMIT=0).")
    elif m["mode"] == "direct":
        print("DIRECT CONTINUATION: 326 five-year segments to 3000; RESUBMIT=325.")
        print("If the first run fails again, inspect logs; do not resubmit blindly.")


def verify_test():
    preflight("3372-01-01-00000")
    if xml("RESUBMIT") != "0":
        raise Stop("Unexpected RESUBMIT after one-segment test")
    status = (CASE / "CaseStatus").read_text(errors="replace")
    if "st_archive success" not in status or "model execution success" not in status:
        raise Stop("No model/archive successes recorded in CaseStatus")
    print("1375/3000 structurally verified at 3372; 1625 years = 325 segments remain")
    print("Next continuation RESUBMIT=324. Not a scientific convergence test.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="mode", required=True)
    for mode in ("inspect", "cancel-blocked", "prepare-test",
                 "verify-test", "prepare-continuation"):
        sp.add_parser(mode)
    sp.add_parser("promote-test").add_argument("test_session")
    sp.add_parser("submit").add_argument("session")
    args = p.parse_args()
    try:
        if args.mode == "inspect":
            inspect()
        elif args.mode == "cancel-blocked":
            cancel_blocked()
        elif args.mode == "prepare-test":
            prepare("test")
        elif args.mode == "prepare-continuation":
            prepare("continuation")
        elif args.mode == "promote-test":
            promote_test(args.test_session)
        elif args.mode == "submit":
            submit(args.session)
        elif args.mode == "verify-test":
            verify_test()
    except (Stop, OSError, IndexError, KeyError,
            ValueError, subprocess.TimeoutExpired) as e:
        print("STOP:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

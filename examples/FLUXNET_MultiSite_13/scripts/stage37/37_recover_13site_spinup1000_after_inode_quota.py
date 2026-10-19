#!/usr/bin/env python3
"""Stage37: guarded continuation of existing 13-site S30SHARED 1000-year spin-ups.

Modes:
  inspect                     READ ONLY, all 13 sites
  fix-mpi DE-Lnf              Backed-up PMIx launcher correction; no submission
  prepare SITE                Isolate incomplete files; restore last complete archived restart
  submit SESSION_DIRECTORY    One case.submit attempt for the prepared site

This is NOT an initial submission script. No restart => no automatic recovery.
Never edits CIME XML, RESUBMIT, forcing, surface or CO2; never cancels jobs.
Run on IRIDIS6 only. Follow docs/SPINUP1000_INODE_QUOTA_RECOVERY_2026-10-20.md.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ACCOUNT = "ly3n24"
SITES = {
    "DE-Lnf": 2002, "DE-Obe": 2008, "ES-Agu": 2006,
    "ES-LJu": 2004, "IT-Col": 1996, "DE-Gri": 2004,
    "DE-RuR": 2011, "FI-Hyy": 1997, "FI-Let": 2010,
    "FR-Pue": 2000, "GF-Guy": 2004, "IT-MBo": 2003,
    "IT-Tor": 2008,
}
SUFFIX = "_FATES_SPINUP1000_S30SHARED"
CASES = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases")
OUT = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
BACKUP = OUT / "recovery_backups" / "FLUXNET_MultiSite_13" / "post_inode_quota"
PARTS = {"cpl": "cpl.r", "atm": "datm.r", "lnd": "clm2.r"}
TARGET = 1000
STAMP_RE = re.compile(r"^\d{4}-01-01-00000$")


class Stop(RuntimeError):
    pass


def command(args, cwd=None, timeout=50):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if p.returncode:
        raise Stop(f"{args!r}: rc={p.returncode}; {(p.stdout+p.stderr)[-1200:]}")
    return p.stdout.strip()


def xml(case, name):
    return command(["./xmlquery", name, "--value"], cwd=case)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda: fd.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ref(path):
    if not path.is_file() or not path.stat().st_size:
        raise Stop(f"Missing/empty restart pointer: {path}")
    return path.read_text(errors="replace").splitlines()[0].strip().removeprefix("./")


def slurm():
    rows = command(["squeue", "-h", "-u", ACCOUNT, "-o", "%i|%j|%T|%R"])
    return [r.split("|", 3) for r in rows.splitlines() if r.count("|") == 3]


def check(site, jobs):
    name = site + SUFFIX
    case = CASES / name
    run = OUT / name / "run"
    archive = OUT / "archive" / name
    result = dict(site=site, name=name, case=case, run=run, archive=archive,
                  stamp=None, done=0, refs={}, partial=[], newer=[],
                  blockers=[], notes=[], status_sha=None)
    bad, notes = result["blockers"], result["notes"]

    if not (case / "xmlquery").is_file() or not (case / "case.submit").is_file():
        bad.append("Existing CIME case missing")
        return result
    if not run.is_dir():
        bad.append("Original run directory missing")
        return result
    matched = [r for r in jobs if r[1] in ("run." + name, "st_archive." + name)]
    if matched:
        bad.append("Slurm job still queued, running or dependency-blocked: " +
                   "; ".join(" ".join(x[:3]) for x in matched))
    try:
        settings = {k: xml(case, k) for k in (
            "CASE", "RUN_TYPE", "RUN_STARTDATE", "CONTINUE_RUN",
            "STOP_OPTION", "STOP_N", "REST_N", "RESUBMIT", "CALENDAR",
            "ATM_NCPL", "DOUT_S", "DOUT_S_ROOT", "RUNDIR", "BUILD_COMPLETE",
            "MPI_RUN_COMMAND")}
        wanted = {
            "CASE": name, "RUN_TYPE": "startup",
            "RUN_STARTDATE": f"{SITES[site]}-01-01",
            "STOP_OPTION": "nyears", "STOP_N": "5", "REST_N": "5",
            "CALENDAR": "NO_LEAP", "ATM_NCPL": "48", "DOUT_S": "TRUE",
            "DOUT_S_ROOT": str(archive), "RUNDIR": str(run),
            "BUILD_COMPLETE": "TRUE",
        }
        for k, v in wanted.items():
            if settings[k].upper() != v.upper():
                bad.append(f"{k}={settings[k]!r}; expected {v!r}")
        if "srun --mpi=pmix" not in settings["MPI_RUN_COMMAND"]:
            bad.append("MPI_RUN_COMMAND not validated PMIx srun")
            notes.append(f"Actual MPI_RUN_COMMAND: {settings['MPI_RUN_COMMAND']!r}")
    except Exception as e:
        bad.append(f"CIME XML unreadable: {e}")
        return result

    dirs = sorted(d for d in (archive / "rest").glob("*")
                  if d.is_dir() and STAMP_RE.fullmatch(d.name))
    if not dirs:
        result["notes"].append("No archived restart: first-segment or archive-failure recovery is manual")
        bad.append("NO_COORDINATED_ARCHIVED_RESTART")
        return result

    latest = dirs[-1]
    stamp = latest.name
    done = int(stamp[:4]) - SITES[site]
    result["stamp"], result["done"] = stamp, done
    if not (5 <= done <= TARGET and done % 5 == 0):
        bad.append(f"Unexpected checkpoint elapsed years={done}")
    if done == TARGET:
        notes.append("Already has 1000-year archive checkpoint; do not resubmit")
        return result

    if settings["CONTINUE_RUN"].upper() != "TRUE":
        bad.append("CONTINUE_RUN not TRUE for existing restart")
    expected_resub = (TARGET - done) // 5 - 1
    if settings["RESUBMIT"] != str(expected_resub):
        bad.append(f"RESUBMIT={settings['RESUBMIT']}, expected {expected_resub} "
                   "before the NEXT case.submit; review CIME state, do not reset blindly")
    notes.append(f"Next segment: model years {done+1}–{done+5}; "
                 f"expected RESUBMIT={expected_resub}")

    status = case / "CaseStatus"
    if not status.is_file():
        bad.append("Missing CaseStatus")
    else:
        result["status_sha"] = digest(status)
        lines = status.read_text(errors="replace").splitlines()
        last_run = max((i for i, line in enumerate(lines)
                        if "model execution success" in line), default=-1)
        last_arc = max((i for i, line in enumerate(lines)
                        if "st_archive success" in line), default=-1)
        if last_run > last_arc:
            bad.append("Model success later than archive success; possible recoverable unarchived run")
        notes.append(f"CaseStatus last model/archive success line: {last_run+1}/{last_arc+1}")

    for comp, kind in PARTS.items():
        filename = f"{name}.{kind}.{stamp}.nc"
        source = latest / filename
        ptr = latest / f"rpointer.{comp}.{stamp}"
        active = run / f"rpointer.{comp}"
        try:
            if ref(ptr) != filename:
                bad.append(f"Archived rpointer.{comp} mismatches {filename}")
            if not source.is_file() or not source.stat().st_size:
                bad.append(f"Archived {comp} restart missing: {filename}")
            if not active.is_file():
                # CIME short-term archive can move runtime rpointer files;
                # verified archived pointers are the source of truth.
                notes.append(f"run rpointer.{comp} absent; Stage37 prepare can restore it")
            else:
                current = ref(active)
                notes.append(f"run rpointer.{comp}: {current}")
        except Exception as e:
            bad.append(str(e))
        result["refs"][comp] = (ptr, source, active, run / filename)

    # Never discard a possible newer coordinated restart without review.
    newer = {}
    for comp, kind in PARTS.items():
        rx = re.compile(re.escape(name + "." + kind + ".") +
                        r"(\d{4}-\d{2}-\d{2}-\d{5})\.nc$")
        for f in run.glob(f"{name}.{kind}.*.nc"):
            m = rx.fullmatch(f.name)
            if m and m.group(1) > stamp:
                newer.setdefault(m.group(1), set()).add(comp)
                result["newer"].append(f)
    complete_newer = [d for d, components in newer.items()
                      if components == set(PARTS)]
    if complete_newer:
        bad.append("Potential newer coordinated run restart: " +
                   ", ".join(sorted(complete_newer)) + "; manually inspect")

    rx = re.compile(re.escape(name) + r"\.clm2\.h[^.]*\.(\d{4})-")
    for f in run.glob(f"{name}.clm2.h*.nc"):
        m = rx.match(f.name)
        if not m:
            bad.append(f"Unrecognized history filename: {f.name}")
        elif int(m.group(1)) >= int(stamp[:4]):
            result["partial"].append(f)

    notes.append(f"Unarchived h*={len(result['partial'])}, "
                 f"newer run restarts={len(result['newer'])}")
    return result


def atomic_copy(source, destination):
    fd, temp = tempfile.mkstemp(prefix=".fates_stage37_", dir=destination.parent)
    os.close(fd)
    try:
        shutil.copy2(source, temp)
        if digest(Path(temp)) != digest(source):
            raise Stop(f"Checksum mismatch copying {source}")
        os.replace(temp, destination)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def inspect():
    jobs = slurm()
    results = []
    print(f"{'SITE':<9} {'YEARS':>6} {'LEFT':>6}  STATE")
    print("-" * 68)
    for site in SITES:
        d = check(site, jobs)
        state = "BLOCKED" if d["blockers"] else (
            "DONE" if d["done"] == TARGET else "REPAIRABLE")
        print(f"{site:<9} {d['done']:>6} {max(0,TARGET-d['done']):>6}  {state}")
        for b in d["blockers"]:
            print("  BLOCK:", b)
        for n in d["notes"]:
            print("  NOTE:", n)
        results.append(d)
    return results


def prepare(site):
    if site not in SITES:
        raise Stop(f"Unknown site: {site}")
    d = check(site, slurm())
    if d["blockers"] or d["done"] == TARGET:
        raise Stop(f"{site}: not safe to prepare: {d['blockers']}; elapsed={d['done']}")
    BACKUP.mkdir(parents=True, exist_ok=True)
    session = Path(tempfile.mkdtemp(prefix=f"{site}_", dir=BACKUP))
    print(f"SESSION={session}", flush=True)
    try:
        copydir = session / "original_case"
        copydir.mkdir()
        for filename in ("CaseStatus", "env_run.xml", "env_batch.xml",
                         "user_nl_clm", "user_nl_datm_streams", ".case.run"):
            src = d["case"] / filename
            if src.is_file():
                shutil.copy2(src, copydir / filename)
        original = session / "original_pointers"
        original.mkdir()
        for comp, (_, _, ptr, _) in d["refs"].items():
            if ptr.is_file():
                shutil.copy2(ptr, original / ptr.name)
            else:
                (original / (ptr.name + ".MISSING")).write_text(
                    "This rpointer was absent before restoration; "
                    "original archive checkpoint pointers are preserved.\n"
                )
        isolated = session / "interrupted_output"
        isolated.mkdir()
        for f in d["partial"] + d["newer"]:
            os.rename(f, isolated / f.name)
        for comp, (arch_ptr, src, ptr, dst) in d["refs"].items():
            if dst.is_file() and digest(dst) != digest(src):
                alt = session / "replaced_checkpoint_files"
                alt.mkdir(exist_ok=True)
                shutil.copy2(dst, alt / dst.name)
            if not dst.is_file() or digest(dst) != digest(src):
                atomic_copy(src, dst)
            atomic_copy(arch_ptr, ptr)
            if ref(ptr) != src.name or digest(dst) != digest(src):
                raise Stop(f"Checkpoint staging failed: {site} {comp}")
        manifest = {
            "site": site, "stamp": d["stamp"], "years": d["done"],
            "casestatus_sha256": d["status_sha"],
            "checkpoint_hashes": {
                comp: digest(entry[1]) for comp, entry in d["refs"].items()
            },
            "isolated": [f.name for f in d["partial"] + d["newer"]],
        }
        (session / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (session / "PREPARED").write_text(datetime.now(timezone.utc).isoformat())
    except Exception:
        print(f"INCOMPLETE SESSION={session}; preserve for manual recovery", file=sys.stderr)
        raise
    print(f"PREPARED {site}: archived checkpoint at {d['done']} years")
    print(f"NEXT: python3 {Path(__file__).resolve()} submit '{session}'")


def submit(session):
    manifest = session / "manifest.json"
    if not (session / "PREPARED").is_file() or not manifest.is_file():
        raise Stop("Missing valid prepared recovery session")
    record = json.loads(manifest.read_text())
    site = record["site"]
    if site not in SITES:
        raise Stop("Unknown site in manifest")
    one_shot = session / "SUBMIT_ATTEMPTED"
    if one_shot.exists():
        raise Stop("Submission already attempted; inspect existing jobs, do not retry")
    d = check(site, slurm())
    if d["blockers"] or d["stamp"] != record["stamp"]:
        raise Stop(f"Recovery preflight changed: {d['blockers']} / stamp={d['stamp']}")
    if digest(d["case"] / "CaseStatus") != record["casestatus_sha256"]:
        raise Stop("CaseStatus changed since checkpoint preparation")
    if d["partial"] or d["newer"]:
        raise Stop("New output appeared in run directory; stop")
    for comp, (_, source, ptr, staged) in d["refs"].items():
        if (ref(ptr) != source.name or not staged.is_file() or
                digest(staged) != record["checkpoint_hashes"][comp]):
            raise Stop(f"Restored {comp} pointer/restart changed")
    one_shot.write_text(datetime.now(timezone.utc).isoformat() + "\n")
    p = subprocess.run(["./case.submit"], cwd=d["case"], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=240)
    (session / "submit.log").write_text(
        p.stdout + f"\nRETURN_CODE={p.returncode}\n")
    print(f"Submitted existing CIME case once: {site}; rc={p.returncode}")
    print(p.stdout[-2500:])
    print("Verify sacct, CaseStatus, model execution and next archived checkpoint.")
    if p.returncode:
        raise Stop("case.submit failed/uncertain. DO NOT rerun blindly.")


def fix_mpi(site):
    """Explicit, guarded DE-Lnf-only CIME launcher fix; does not submit or reset."""
    if site != "DE-Lnf":
        raise Stop("fix-mpi is limited to DE-Lnf; inspect other sites separately")
    d = check(site, slurm())
    if not d["blockers"] or any(
            not issue.startswith("MPI_RUN_COMMAND not validated")
            for issue in d["blockers"]):
        raise Stop(f"Not a clean MPI-only correction candidate: {d['blockers']}")
    if d["done"] == TARGET:
        raise Stop("Already completed target; no launcher change needed")
    case = d["case"]
    xml_keys = ("RESUBMIT", "STOP_N", "REST_N", "CONTINUE_RUN",
                "RUN_STARTDATE", "RUNDIR", "DOUT_S_ROOT", "CLM_CO2_TYPE")
    original = {key: xml(case, key) for key in xml_keys}
    src_files = ("env_mach_specific.xml", "env_run.xml", "env_batch.xml",
                 ".case.run", "CaseStatus", "user_nl_clm", "user_nl_datm_streams")
    source_hashes = {k: digest(case / k) for k in
                     ("user_nl_clm", "user_nl_datm_streams")
                     if (case / k).is_file()}
    BACKUP.mkdir(parents=True, exist_ok=True)
    session = Path(tempfile.mkdtemp(prefix="DE-Lnf_mpi_", dir=BACKUP))
    for filename in src_files:
        candidate = case / filename
        if candidate.is_file():
            shutil.copy2(candidate, session / filename)
    (session / "previous_mpi.txt").write_text(
        xml(case, "MPI_RUN_COMMAND") + "\n")
    if any(r[1] in ("run." + d["name"], "st_archive." + d["name"])
           for r in slurm()):
        raise Stop("A Slurm job appeared before MPI correction")
    new_command = "srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"
    command(["./xmlchange", f"MPI_RUN_COMMAND={new_command}"], cwd=case)
    if xml(case, "MPI_RUN_COMMAND") != new_command:
        raise Stop(f"xmlchange verification failed; backup at {session}")
    for key, previous in original.items():
        if xml(case, key) != previous:
            raise Stop(f"CIME setting {key} changed unexpectedly; backup at {session}")
    for filename, previous_hash in source_hashes.items():
        if digest(case / filename) != previous_hash:
            raise Stop(f"Science input {filename} changed; backup at {session}")
    preview = command(["./preview_run"], cwd=case)
    (session / "preview_run.txt").write_text(preview + "\n")
    if new_command not in preview:
        raise Stop(f"preview_run did not confirm expected PMIx launcher; {session}")
    print(f"MPI_FIXED DE-Lnf; BACKUP={session}")
    print("No case.setup --reset, job cancellation, or job submission performed.")
    print("Next: rerun inspect, then prepare DE-Lnf only if REPAIRABLE.")


def main():
    if os.environ.get("USER") != ACCOUNT:
        raise Stop("Run as ly3n24 on IRIDIS6")
    if len(sys.argv) == 2 and sys.argv[1] == "inspect":
        inspect()
    elif len(sys.argv) == 3 and sys.argv[1] == "fix-mpi":
        fix_mpi(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "prepare":
        prepare(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "submit":
        submit(Path(sys.argv[2]).resolve())
    else:
        raise Stop("Usage: SCRIPT inspect | fix-mpi DE-Lnf | prepare SITE | submit SESSION_DIRECTORY")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE37 STOP:", exc, file=sys.stderr)
        sys.exit(1)

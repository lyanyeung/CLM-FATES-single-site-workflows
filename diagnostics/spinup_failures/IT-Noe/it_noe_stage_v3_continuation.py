#!/usr/bin/env python3
"""Safely stage v3 DATM streams for the EXISTING IT-Noe 2054->3004 run.

No job submission, cancellation, restart staging or science approval.
INSPECT is read-only. PREPARE requires explicit acknowledgements and backs up
the original stream. Existing recover_blocked_spinups.py performs the later,
separate checkpoint-safe Slurm submission. This remains a legacy-state
UNAPPROVED-FORCING sensitivity continuation, not a clean spinup from 2004.
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

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing")
CASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases/IT-Noe_ERA5_ABW_BRANCH2009")
V3 = BASE / "datm_11_IT-Noe_QC_v3_RHcap_20261021_230447"
ARCH = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/IT-Noe_ERA5_ABW_BRANCH2009/rest/2054-01-01-00000")
NAME = "IT-Noe_ERA5_ABW_BRANCH2009"
STAMP = "2054-01-01-00000"
YEAR_SET = set(range(2004, 2026))
REF_RX = re.compile(r"/[^\s,\\<>\"']+/IT-Noe_DATM_(\d{4})\.nc")
ROOT = Path.home() / "IT-Noe_source_diagnosis" / "continuation_preparations"

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(2**20), b""):
            h.update(block)
    return h.hexdigest()

def command(args, cwd, timeout=120) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, check=False)

def xml(key: str) -> str:
    p = command(["./xmlquery", key, "--value"], CASE)
    if p.returncode:
        raise RuntimeError("xmlquery failed: " + key + " " + p.stderr[-300:])
    return p.stdout.strip()

def references(content: str) -> list[str]:
    refs = re.findall(r"/[^\s,\\<>\"']+/IT-Noe_DATM_\d{4}\.nc", content)
    years = [int(REF_RX.fullmatch(item).group(1)) for item in refs]
    if len(refs) != 22 or set(years) != YEAR_SET or len(set(years)) != 22:
        raise RuntimeError("DATM stream must list exactly one 2004-2025 file per year")
    return refs

def check_jobs() -> list[str]:
    p = subprocess.run(["squeue", "-h", "-u", "ly3n24",
                        "-o", "%i|%j|%T|%R"], text=True,
                       capture_output=True, timeout=30, check=False)
    if p.returncode:
        raise RuntimeError("Cannot read Slurm queue; refusing to alter case")
    jobs = [line for line in p.stdout.splitlines()
            if len(line.split("|", 3)) == 4
            and line.split("|", 3)[1] in ("run."+NAME, "st_archive."+NAME)]
    for j in jobs:
        fields = j.split("|", 3)
        if (fields[1] != "st_archive."+NAME or fields[2] != "PENDING"
                or "DependencyNeverSatisfied" not in fields[3]):
            raise RuntimeError("Active/unexpected IT-Noe job: " + j)
    return jobs

def checks(forcing: Path) -> dict:
    if os.environ.get("USER") != "ly3n24" or os.geteuid() == 0:
        raise RuntimeError("Run as ly3n24 on IRIDIS6")
    if not CASE.is_dir() or not forcing.is_dir() or not ARCH.is_dir():
        raise RuntimeError("Case, forcing or 2054 archive does not exist")
    manifest_file = forcing / "CANDIDATE_PROVENANCE.json"
    if not manifest_file.is_file():
        raise RuntimeError("Missing v3 provenance")
    receipt = json.loads(manifest_file.read_text())
    if (receipt.get("status") != "UNAPPROVED_RH_CAP_CANDIDATE"
            or receipt.get("rh_capped_rows") != 20
            or Path(receipt.get("forcing_directory", "/missing")).resolve()
               != forcing.resolve()
            or any(receipt.get(k) is not False for k in
                   ("source_review_complete", "boundary_review_complete",
                    "full_cycle_qc_complete"))):
        raise RuntimeError("Unexpected v3 provenance. Do not label it approved.")
    expected = receipt.get("year_sha256", {})
    if set(expected) != {str(y) for y in YEAR_SET}:
        raise RuntimeError("Missing year SHA256 values for v3")
    for year in sorted(YEAR_SET):
        f = forcing / f"IT-Noe_DATM_{year}.nc"
        if f.is_symlink() or not f.is_file() or digest(f) != expected[str(year)]:
            raise RuntimeError(f"Missing or altered v3 file for year {year}")
    settings = {
        "RUN_TYPE": "branch", "RUN_REFDATE": "2009-01-01",
        "RUN_STARTDATE": "2004-01-01", "CONTINUE_RUN": "TRUE",
        "STOP_OPTION": "nyears", "STOP_N": "5",
        "REST_OPTION": "nyears", "REST_N": "5",
        "RESUBMIT": "189", "ATM_NCPL": "48", "BUILD_COMPLETE": "TRUE",
    }
    for key, value in settings.items():
        actual = xml(key)
        if actual.lower() != value.lower():
            raise RuntimeError(f"{key}={actual!r}; expected {value!r}")
    for component, pointer in (("clm2", "lnd"), ("cpl", "cpl"),
                               ("datm", "atm")):
        fname = f"{NAME}.{component}.r.{STAMP}.nc"
        nc = ARCH / fname
        pt = ARCH / f"rpointer.{pointer}.{STAMP}"
        if not nc.is_file() or nc.stat().st_size < 1024 or not pt.is_file():
            raise RuntimeError("Missing 2054 restart or dated pointer: " + fname)
        if pt.read_text(errors="replace").splitlines()[0].strip().removeprefix("./") != fname:
            raise RuntimeError("2054 pointer mismatch: " + fname)
    stream = CASE / "user_nl_datm_streams"
    if stream.is_symlink() or not stream.is_file():
        raise RuntimeError("Cannot safely edit user_nl_datm_streams")
    refs = references(stream.read_text())
    directories = {str(Path(x).parent) for x in refs}
    old_dir = BASE / "datm_11_IT-Noe_ERA5_sensitivity_abort_window_20261021"
    if directories not in ({str(old_dir)}, {str(forcing)}):
        raise RuntimeError(f"Unexpected current stream directory: {directories}")
    jobs = check_jobs()
    return dict(stream=stream, old_dir=str(old_dir),
                current_dir=next(iter(directories)), jobs=jobs,
                manifest_sha256=digest(manifest_file),
                status=receipt["status"])

def prepare(forcing: Path, info: dict) -> None:
    if info["current_dir"] == str(forcing):
        print("ALREADY_STAGED. No changes. Run recovery INSPECT next.")
        return
    stream = info["stream"]
    previous = stream.read_text()
    old_refs = references(previous)
    edits = {src: str(forcing / Path(src).name) for src in old_refs}
    new = previous
    for before, after in edits.items():
        new = new.replace(before, after)
    updated = references(new)
    if len(updated) != 22 or {str(Path(x).parent) for x in updated} != {str(forcing)}:
        raise RuntimeError("Retargeted CIME stream has unexpected file list")
    ROOT.mkdir(parents=True, exist_ok=True)
    sess = ROOT / ("v3_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    sess.mkdir(exist_ok=False)
    b = sess / "case_before"
    b.mkdir()
    prior_streams = [stream, CASE / "CaseDocs/datm.streams.xml",
                     CASE / "CaseDocs/datm_in", CASE / "CaseStatus"]
    for f in prior_streams:
        if f.is_file():
            shutil.copy2(f, b / f.name)
    m = {
        "case": str(CASE), "forcing": str(forcing),
        "unapproved_sensitivity": True,
        "2054_archive": str(ARCH), "manifest_sha256": info["manifest_sha256"],
        "original_stream_sha256": digest(stream),
        "old_stream_dir": info["current_dir"],
        "original_job_queue": info["jobs"],
        "backup": str(sess),
        "note": "The 2054 state reflects old forcing. Not approved clean 1000-year spinup."
    }
    (sess/"PREPARE_METADATA.json").write_text(json.dumps(m,indent=2)+"\n")
    fd, tmp = tempfile.mkstemp(prefix=".itnoe_v3_stream_", dir=CASE)
    try:
        with os.fdopen(fd, "w") as outf:
            outf.write(new)
        os.chmod(tmp, stream.stat().st_mode & 0o777)
        os.replace(tmp, stream)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    proc = command(["./preview_namelists"], CASE, timeout=180)
    (sess/"preview_namelists.log").write_text(proc.stdout+"\n"+proc.stderr)
    if proc.returncode:
        print("PREVIEW_FAILED; backup available: "+str(sess))
        raise RuntimeError("preview_namelists failed. Inspect backup; do not submit")
    docs = CASE/"CaseDocs/datm.streams.xml"
    if not docs.is_file():
        raise RuntimeError("Missing CaseDocs/datm.streams.xml after preview")
    confirmed = references(docs.read_text())
    if {str(Path(x).parent) for x in confirmed} != {str(forcing)}:
        raise RuntimeError("Effective CaseDocs DATM streams do not point to v3")
    if check_jobs() != info["jobs"]:
        raise RuntimeError("Slurm queue changed during preparation; inspect before submit")
    (sess/"STAGED_VERIFIED").write_text(
        "All 22 effective DATM files reference the v3 unapproved sensitivity candidate.\n"
    )
    print("PREPARED_CASE_STREAM=YES")
    print("EFFECTIVE_22_YEARS=2004-2025")
    print("BACKUP="+str(sess))
    print("UNCHANGED: XML RUN settings, restarts, and Slurm queue")
    print("NEXT: download maintenance/check_four_spinups.py and "
          "maintenance/recover_blocked_spinups.py; run recovery inspect first.")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("inspect", "prepare"))
    ap.add_argument("--forcing", type=Path, default=V3)
    ap.add_argument("--acknowledge-unapproved-v3", action="store_true")
    ap.add_argument("--acknowledge-legacy-2054-state", action="store_true")
    a = ap.parse_args()
    info = checks(a.forcing)
    print("SOURCE_SCIENCE_STATUS="+info["status"])
    print("CURRENT_DATM="+info["current_dir"])
    print("TARGET_DATM="+str(a.forcing))
    print("ARCHIVED_CHECKPOINT=2054-01-01; RUN_REMAINING=950, RESUBMIT=189")
    print("QUEUE="+json.dumps(info["jobs"]))
    print("NO production scientific approval. This is a legacy-state sensitivity run.")
    if a.mode == "inspect":
        print("INSPECT_ONLY: no files/jobs changed.")
        return 0
    if not (a.acknowledge_unapproved_v3 and
            a.acknowledge_legacy_2054_state):
        raise RuntimeError("PREPARE requires both explicit sensitivity acknowledgements")
    ROOT.mkdir(parents=True, exist_ok=True)
    with (ROOT/".prepare.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prepare(a.forcing, checks(a.forcing))
    print("NO SLURM JOB SUBMITTED.")
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as ex:
        print("STOP: "+str(ex), file=sys.stderr)
        sys.exit(2)

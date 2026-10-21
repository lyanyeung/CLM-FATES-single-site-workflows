#!/usr/bin/env python3
"""Stage39: directly submit CH-Aws v7 from the 2016 restart to 1000 TOTAL years.

No diagnostic run: 2006--2015 (10 years) are reused from the RH34A
checkpoint. Submit 2016 onward: 198 x five-year CIME segments,
initial RESUBMIT=197, final model date 3006-01-01 (1000 elapsed years).

Creates a new case CH-Aws_FATES_SPINUP1000_RH38A_CONT2016 with a
separate run/archive directory, and copies the three matching archived
RH34A checkpoint restart files, leaving RH34A fully untouched.

--audit: default, read-only; must find exact 2016 checkpoint.
--launch: prepare and SUBMIT once without a diagnostic short job.
--status: inspect created case and Slurm queue, read-only.

Scientific caveat: v7 QBOT changes are unvalidated reanalysis sensitivities;
successful file verification does not guarantee a successful model run.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

UID = "ly3n24"
BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
CASES = BASE / "cases"
OUT = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
OLD_NAME = "CH-Aws_FATES_SPINUP1000_RH34A"
NEW_NAME = "CH-Aws_FATES_SPINUP1000_RH38A_CONT2016"
OLD = CASES / OLD_NAME
NEW = CASES / NEW_NAME
NEW_RUN = OUT / NEW_NAME / "run"
NEW_ARCH = OUT / "archive" / NEW_NAME
V6 = BASE / "sites/MY_EC_SITE/CH-Aws/forcing/datm_11_stage34_qc1_27rh_sensitivity_v6"
V7 = BASE / "sites/MY_EC_SITE/CH-Aws/forcing/datm_11_stage38_qc1_21rh_sensitivity_v7"
CTSM = BASE / "CTSM"
STAMP = "2016-01-01-00000"
SEGMENTS = 198
RESUBMIT = SEGMENTS - 1
MPI = "srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"
PARTS = {"cpl": "cpl.r", "atm": "datm.r", "lnd": "clm2.r"}
MAGIC = (b"CDF\x01", b"CDF\x02", b"CDF\x05", b"\x89HDF\r\n\x1a\n")


def stop(why):
    raise RuntimeError("STOP: " + why)


def require(condition, why):
    if not condition:
        stop(why)


def run(*args, cwd=None, capture=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=capture)
    if proc.returncode:
        stop("Command failed: " + " ".join(str(a) for a in args)
             + "\n" + ((proc.stdout or "") + (proc.stderr or ""))[-4000:])
    return (proc.stdout or "").strip()


def xml(casedir, key):
    return run("./xmlquery", key, "--value", cwd=casedir).strip()


def update_xml(key, value):
    run("./xmlchange", f"{key}={value}", cwd=NEW)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def get_ptr(path):
    require(path.is_file(), "Missing restart pointer " + str(path))
    data = path.read_text(errors="replace").strip().removeprefix("./")
    require("\n" not in data and "/" not in data
            and re.fullmatch(r"[A-Za-z0-9_.-]+", data) is not None,
            "Unexpected pointer format " + str(path) + ": " + repr(data))
    return data


def queue():
    return run("squeue", "-h", "-u", UID, "-o", "%j|%T|%i").splitlines()


def no_conflicting_jobs():
    for line in queue():
        jobname = line.split("|", 1)[0]
        require(jobname not in (f"run.{OLD_NAME}", f"run.{NEW_NAME}",
                                f"st_archive.{NEW_NAME}"),
                "Model/submission still active: " + line)


def verify_v7():
    require(V7.is_dir() and V6.is_dir(), "v6/v7 forcing directory missing")
    m = json.loads((V7 / "stage38_manifest.json").read_text())
    require(m.get("version") == "STAGE38_QC1_21ROW_SENSITIVITY_V7"
            and m.get("modified_vs_v6") == 21
            and m.get("model_validation") == "NOT RUN",
            "Unexpected v7 candidate manifest")
    year17 = V7 / "CH-Aws_DATM_2017.nc"
    require(year17.is_file() and not year17.is_symlink(),
            "Independent 2017 v7 forcing missing")
    require(sha(V6 / "CH-Aws_DATM_2017.nc") == m["parent_2017_sha256"],
            "Source v6 2017 changed after writing v7")
    require(sha(V7 / "stage38_21_QC1_ledger.csv") == m["ledger_sha256"],
            "v7 ledger hash mismatch")
    for model in ("era5", "era5_land"):
        original = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo" / f"{model}_2017.json"
        require(sha(original) == m["reference_sha256"][model],
                "v7 reanalysis source changed " + model)
    for year in range(2006, 2025):
        name = f"CH-Aws_DATM_{year}.nc"
        f = V7 / name
        require(f.is_file(), "Missing/broken v7 annual forcing: " + name)
        if year != 2017:
            require(f.is_symlink() and f.resolve() == (V6 / name).resolve(),
                    "Unexpected v7 symlink year " + str(year))


def old_case():
    require(OLD.is_dir() and (OLD / "xmlquery").is_file(),
            "Original RH34A case missing")
    expected = {
        "CASE": OLD_NAME, "RUN_TYPE": "startup", "RUN_STARTDATE": "2006-01-01",
        "CALENDAR": "NO_LEAP", "ATM_NCPL": "48", "STOP_OPTION": "nyears",
        "STOP_N": "5", "REST_OPTION": "nyears", "REST_N": "5",
        "CLM_CO2_TYPE": "constant", "DOUT_S": "TRUE",
        "BUILD_COMPLETE": "TRUE",
    }
    for key, value in expected.items():
        actual = xml(OLD, key)
        require(actual == value, f"RH34A {key}={actual!r}, expected {value!r}")
    require(abs(float(xml(OLD, "CCSM_CO2_PPMV")) - 381.15) < .011,
            "Original CH-Aws CO2 unexpectedly differs")
    executable = Path(xml(OLD, "EXEROOT")) / "cesm.exe"
    require(executable.is_file() and os.access(executable, os.X_OK),
            "Original shared executable not available")
    require((OLD / "user_nl_datm_streams").is_file()
            and (OLD / "user_nl_clm").is_file(), "Original input namelists missing")
    stream = (OLD / "user_nl_datm_streams").read_text()
    require(stream.count(str(V6 / "CH-Aws_DATM_")) == 19
            and "CLM_USRDAT.UNSET:taxmode = cycle" in stream,
            "Original v6 stream not exactly 19 annual files / cycle")
    require(re.search(r"(?im)^\s*calc_human_stress_indices\s*=\s*'FAST'",
                      (OLD / "user_nl_clm").read_text()) is not None,
            "Old source RH34A no longer has FAST human index")
    return executable


def checkpoint():
    # Prefer complete archived restart; accept a complete 2016 RUNDIR
    # checkpoint only if archived directory is unavailable.
    archived = OUT / "archive" / OLD_NAME / "rest" / STAMP
    old_run = OUT / OLD_NAME / "run"
    candidates = [archived, old_run]
    diagnostics = []
    for loc in candidates:
        if not loc.is_dir():
            diagnostics.append(str(loc) + ": directory absent")
            continue
        files = {}
        try:
            for comp, kind in PARTS.items():
                if loc == archived:
                    p = loc / f"rpointer.{comp}.{STAMP}"
                else:
                    # The active pointer may have moved past 2016; use
                    # dated pointers only for a historical checkpoint.
                    p = loc / f"rpointer.{comp}.{STAMP}"
                expected_name = f"{OLD_NAME}.{kind}.{STAMP}.nc"
                require(get_ptr(p) == expected_name,
                        "Pointer mismatch " + str(p))
                f = loc / expected_name
                require(f.is_file() and not f.is_symlink()
                        and f.stat().st_size >= 1024,
                        "Incomplete checkpoint file: " + str(f))
                with open(f, "rb") as stream:
                    require(stream.read(8).startswith(MAGIC),
                            "Not NetCDF/HDF5: " + str(f))
                files[comp] = f
            return loc, files
        except Exception as exc:
            diagnostics.append(str(loc) + ": " + str(exc))
    stop("No complete 2016 three-component checkpoint found:\n"
         + "\n".join(diagnostics))


def check_new_does_not_exist():
    for p in (NEW, OUT / NEW_NAME, NEW_ARCH):
        require(not p.exists() and not p.is_symlink(),
                "New case/output already exists, refusing duplicate: " + str(p))


def batch_patch():
    p = NEW / "env_batch.xml"
    body = p.read_text()
    body, n = re.subn(
        r"(?m)^[ \t]*<directive>[ \t]*--exclusive[ \t]*</directive>[ \t]*\r?\n",
        "", body)
    require(n <= 2 and "--exclusive" not in body,
            "Unusual exclusive batch directive, stop")
    needle = "<directive>--cpus-per-task={{ thread_count }}</directive>"
    require(body.count(needle) == 1, "Unexpected batch template")
    mem = "<directive>--mem=8G</directive>"
    matches = re.findall(r"<directive>\s*--mem(?:=|\s).*?</directive>", body)
    if not matches:
        body = body.replace(needle, needle + "\n        " + mem, 1)
    else:
        require(len(matches) == 1 and matches[0] == mem,
                "Unexpected memory request in batch template")
    ET.fromstring(body)
    p.write_text(body)


def verify_new(executable, staged_files=None):
    req = {
        "CASE": NEW_NAME, "RUN_TYPE": "startup", "CONTINUE_RUN": "TRUE",
        "RUN_STARTDATE": "2006-01-01", "CALENDAR": "NO_LEAP",
        "ATM_NCPL": "48", "STOP_OPTION": "nyears", "STOP_N": "5",
        "REST_OPTION": "nyears", "REST_N": "5", "RESUBMIT": str(RESUBMIT),
        "BUILD_COMPLETE": "TRUE", "DOUT_S": "TRUE",
        "DOUT_S_ROOT": str(NEW_ARCH), "RUNDIR": str(NEW_RUN),
        "CLM_CO2_TYPE": "constant", "MPI_RUN_COMMAND": MPI,
        "EXEROOT": str(executable.parent),
    }
    for key, expected in req.items():
        actual = xml(NEW, key)
        require(actual == expected,
                f"New {key}={actual!r}, expected {expected!r}")
    require(abs(float(xml(NEW, "CCSM_CO2_PPMV")) - 381.15) < .011,
            "New constant CO2 unexpectedly changed")
    for comp in ("ATM", "LND", "CPL"):
        require(xml(NEW, "NTASKS_" + comp) == "1"
                and xml(NEW, "NTHRDS_" + comp) == "1",
                "Unexpected parallelism " + comp)
    for batch in (NEW / ".case.run", NEW / "case.st_archive"):
        require(batch.is_file() and "--exclusive" not in batch.read_text(),
                "Invalid batch resource sharing " + str(batch))
        for directive in ("--nodes=1", "--ntasks-per-node=1",
                          "--cpus-per-task=1", "--mem=8G"):
            require(re.search(r"(?m)^#SBATCH\s+" + re.escape(directive)
                              + r"\s*$", batch.read_text()) is not None,
                    "Missing batch directive " + directive + " in " + str(batch))
    lnd = (NEW / "CaseDocs/lnd_in").read_text()
    require(re.search(r"(?im)^\s*calc_human_stress_indices\s*=\s*'FAST'",
                      lnd) is not None, "HumanIndex FAST setting changed")
    for y in range(2006, 2025):
        require(str(V7 / f"CH-Aws_DATM_{y}.nc") in
                (NEW / "CaseDocs/datm.streams.xml").read_text(),
                "Generated DATM does not use v7 for " + str(y))
    preview = run("./preview_run", cwd=NEW)
    require(MPI + " " + str(executable) in preview,
            "Run preview does not use original compiled executable and srun")
    if staged_files is not None:
        for comp, src in staged_files.items():
            dst = NEW_RUN / src.name
            require(dst.is_file() and sha(dst) == sha(src),
                    "Copied restart checksum mismatch " + comp)
            require(get_ptr(NEW_RUN / ("rpointer." + comp)) == src.name,
                    "Active rpointer mismatch " + comp)


def prepare(executable, restart_files):
    print("Cloning independent case; no original case or output is modified", flush=True)
    run(str(CTSM / "cime/scripts/create_clone"),
        "--case", str(NEW), "--clone", str(OLD), "--keepexe",
        cwd=CTSM / "cime/scripts")
    require(NEW.is_dir(), "New CIME case was not created")
    shutil.copy2(OLD / "user_nl_clm", NEW / "user_nl_clm")
    stream = (OLD / "user_nl_datm_streams").read_text()
    stream = stream.replace(str(V6), str(V7))
    (NEW / "user_nl_datm_streams").write_text(stream)
    require(stream.count(str(V7 / "CH-Aws_DATM_")) == 19,
            "Replacement stream does not point to 19 v7 years")
    for key, val in {
        "DIN_LOC_ROOT": str(BASE / "inputdata"),
        "RUN_TYPE": "startup", "CONTINUE_RUN": "TRUE",
        "RUN_STARTDATE": "2006-01-01", "CALENDAR": "NO_LEAP",
        "ATM_NCPL": "48", "CLM_CO2_TYPE": "constant",
        "CCSM_CO2_PPMV": "381.15",
        "STOP_OPTION": "nyears", "STOP_N": "5",
        "REST_OPTION": "nyears", "REST_N": "5",
        "RESUBMIT": str(RESUBMIT), "DOUT_S": "TRUE",
        "DOUT_S_ROOT": str(NEW_ARCH), "RUNDIR": str(NEW_RUN),
        "MPI_RUN_COMMAND": MPI,
    }.items():
        update_xml(key, val)
    batch_patch()
    if (NEW / ".case.run").exists():
        run("./case.setup", "--reset", cwd=NEW)
    else:
        run("./case.setup", cwd=NEW)
    update_xml("MPI_RUN_COMMAND", MPI)
    update_xml("CONTINUE_RUN", "TRUE")
    if xml(NEW, "BUILD_COMPLETE") != "TRUE":
        update_xml("BUILD_COMPLETE", "TRUE")
    run("./preview_namelists", cwd=NEW)
    run("./check_input_data", cwd=NEW)
    NEW_RUN.mkdir(parents=True, exist_ok=True)
    for comp, src in restart_files.items():
        dst = NEW_RUN / src.name
        require(not dst.exists(), "Restart destination unexpectedly occupied: " + str(dst))
        shutil.copy2(src, dst)
        require(sha(dst) == sha(src), "Restart copy digest differs: " + str(src))
        (NEW_RUN / f"rpointer.{comp}").write_text(src.name + "\n")
        (NEW_RUN / f"rpointer.{comp}.{STAMP}").write_text(src.name + "\n")
    verify_new(executable, staged_files=restart_files)
    info = {
        "case": NEW_NAME, "source_case": OLD_NAME, "source_checkpoint": STAMP,
        "elapsed_original_years": 10, "remaining_years": 990,
        "five_year_segments": SEGMENTS, "initial_RESUBMIT": RESUBMIT,
        "expected_final_clock": "3006-01-01-00000",
        "forcing": str(V7),
        "source_restart_SHA256": {k: sha(f) for k, f in restart_files.items()},
        "scientific_status": "PROVISIONAL_REANALYSIS_SENSITIVITY",
    }
    (NEW / ".stage39_restart_provenance.json").write_text(
        json.dumps(info, indent=2) + "\n")
    print("READY: new independent case verified; restart copies verified.", flush=True)


def launch():
    preflight_info = audit()
    executable, rest, components = preflight_info
    check_new_does_not_exist()
    prepare(executable, components)
    no_conflicting_jobs()
    marker = NEW / ".STAGE39_SUBMISSION_ATTEMPTED"
    require(not marker.exists(), "Submission already attempted")
    history = (NEW / "CaseStatus").read_text(errors="replace")
    require(not re.search(r"case.submit (starting|success)", history),
            "New case may have been submitted already")
    marker.write_text(datetime.now().isoformat() + "\n")
    print("SUBMITTING NOW: remaining 990 years, 198 x 5yr segments, RESUBMIT=197",
          flush=True)
    output = run("./case.submit", cwd=NEW)
    print(output)
    print("case.submit returned success; this is NOT model completion.", flush=True)
    print("Queue:", flush=True)
    for line in queue():
        if NEW_NAME in line:
            print(line)


def audit():
    require(os.environ.get("USER") == UID,
            f"Expected IRIDIS username {UID}")
    no_conflicting_jobs()
    check_new_does_not_exist()
    verify_v7()
    executable = old_case()
    rest, components = checkpoint()
    require(SEGMENTS == 198 and RESUBMIT == 197, "Segment arithmetic mismatch")
    print("=== CH-AWS STAGE39 PRE-FLIGHT PASSED ===")
    print("v7 validated at forcing-file level; no model success claimed.")
    print("RH34A restart source:", rest)
    for comp, f in components.items():
        print("  ", comp, f.name, "SHA256", sha(f))
    print("Original completed years: 10; resume 2016; remaining: 990.")
    print("Auto chain: 198 x 5-year model segments; initial RESUBMIT=197.")
    print("Target model clock: 3006-01-01-00000 (1000 TOTAL model years).")
    print("New case:", NEW)
    print("No diagnostic run. --launch creates case and submits initial job.")
    return executable, rest, components


def status():
    if NEW.exists():
        for key in ("CASE", "RUN_TYPE", "CONTINUE_RUN", "RUN_STARTDATE",
                    "STOP_N", "RESUBMIT", "RUNDIR", "DOUT_S_ROOT"):
            print(key, xml(NEW, key))
        f = NEW / "CaseStatus"
        if f.is_file():
            print("\n".join(f.read_text(errors="replace").splitlines()[-18:]))
    else:
        print("New case not created.")
    for line in queue():
        if NEW_NAME in line:
            print(line)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("audit", "launch", "status"), nargs="?",
                   default="audit")
    args = p.parse_args()
    if args.mode == "status":
        status()
        return
    lockpath = Path.home() / ".CH_Aws_Stage39_v7_continue.lock"
    with open(lockpath, "a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.mode == "audit":
            audit()
        else:
            launch()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

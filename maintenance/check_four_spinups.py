#!/usr/bin/env python3
"""Read-only IRIDIS6 status report for four CLM-FATES FLUXNET spin-up batches.

Recreates the detailed check_four_spinups.py-style terminal table:
SITE, DONE/TARGET, LEFT, CHECKPOINT, RESUB, SLURM, JOB IDs / NOTE.

Uses archived coordinated cpl/datm/clm2 restart components AND their dated
rpointer files to count completed model years; queued/running Slurm jobs
represent activity, not completed years. No case.submit, xmlchange, cleanup,
or output-file writes. Python standard library only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

OUTPUT_ROOT = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
CASE_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases")
USER = "ly3n24"

# Each entry is SITE: (RUN_START_YEAR, TOTAL_TARGET_YEARS).
# These are cumulative simulation years, not forcing years.
BATCHES = {
    "FLUXNET_MultiSite_6": {
        "DE-Hai": (2000, 1000), "RU-Fyo": (1998, 3000),
        "DE-Tha": (1996, 3000), "DK-Sor": (1996, 3000),
        "NL-Loo": (1997, 3000), "IL-Yat": (2000, 3000),
    },
    "FLUXNET_MultiSite_8": {
        "CZ-BK1": (2004, 1000), "IT-Ren": (1999, 1000),
        "FR-Hes": (1997, 500), "FR-FBn": (2008, 1000),
        "DE-Hzd": (2010, 1000), "CH-Dav": (1997, 1000),
        "BE-Vie": (1996, 1000), "IT-Lav": (2003, 1000),
    },
    "FLUXNET_MultiSite_11": {
        "BE-Bra": (1996, 1000), "FR-Fon": (2005, 1000),
        "GL-ZaH": (2000, 1000), "IT-Noe": (2004, 1000),
        "AT-Neu": (2002, 1000), "FI-Sod": (2001, 1000),
        "CH-Aws": (2006, 1000), "CH-Cha": (2005, 1000),
        "CH-Fru": (2005, 1000), "CH-Lae": (2004, 1000),
        "CZ-Stn": (2010, 1000),
    },
    "FLUXNET_MultiSite_13": {
        "DE-Lnf": (2002, 1000), "DE-Obe": (2008, 1000),
        "ES-Agu": (2006, 1000), "ES-LJu": (2004, 1000),
        "IT-Col": (1996, 1000), "DE-Gri": (2004, 1000),
        "DE-RuR": (2011, 1000), "FI-Hyy": (1997, 1000),
        "FI-Let": (2010, 1000), "FR-Pue": (2000, 1000),
        "GF-Guy": (2004, 1000), "IT-MBo": (2003, 1000),
        "IT-Tor": (2008, 1000),
    },
}
PARTS = {"cpl": "cpl", "atm": "datm", "lnd": "clm2"}
DATE_RX = re.compile(r"^\d{4}-01-01-00000$")


def case_name(batch: str, site: str) -> str:
    if batch.endswith("_11"):
        return site + "_FATES_SPINUP500_11P"
    if batch.endswith("_13"):
        return site + "_FATES_SPINUP1000_S30SHARED"
    return site + "_FATES_SPINUP500"


def slurm_jobs() -> list[dict]:
    # Fail closed on a broken squeue query: no rows must not be mistaken for IDLE.
    command = ["squeue", "-h", "-u", USER, "-o", "%i|%j|%T|%R"]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    records = []
    for line in result.stdout.splitlines():
        fields = line.split("|", 3)
        if len(fields) == 4:
            records.append(dict(jobid=fields[0], name=fields[1],
                                state=fields[2], reason=fields[3]))
    return records


def xml_value(case: Path, key: str) -> str:
    env = case / "env_run.xml"
    if not env.is_file():
        return "-"
    try:
        root = ET.parse(env).getroot()
        for entry in root.iter("entry"):
            if entry.get("id") == key:
                return entry.get("value") or "-"
    except (OSError, ET.ParseError):
        return "XML_ERR"
    return "-"


def restart_status(rest: Path, name: str, start: int) -> tuple:
    """Return last verified coordinated checkpoint, plus newest-dir warning.

    Dated archived rpointer.<component>.<date> files are intentionally checked;
    never use an undated run/rpointer.* (which can be stale after a failure).
    """
    if not rest.is_dir():
        return None, None, "NO_ARCHIVE"
    try:
        stamps = sorted((p.name for p in rest.iterdir()
                         if p.is_dir() and DATE_RX.fullmatch(p.name)),
                        reverse=True)
    except OSError:
        return None, None, "ARCHIVE_IO_ERROR"
    if not stamps:
        return None, None, "NO_ARCHIVE"
    first_bad = None
    for stamp in stamps:
        year = int(stamp[:4])
        done = year - start
        if done < 0 or done % 5:
            if first_bad is None:
                first_bad = stamp + ":INVALID_DATE"
            continue
        folder = rest / stamp
        errors = []
        for comp, prefix in PARTS.items():
            filename = f"{name}.{prefix}.r.{stamp}.nc"
            restart = folder / filename
            pointer = folder / f"rpointer.{comp}.{stamp}"
            try:
                if not restart.is_file() or restart.stat().st_size < 1024:
                    errors.append(comp + "_NC")
                    continue
                if not pointer.is_file():
                    errors.append(comp + "_PTR")
                    continue
                value = pointer.read_text(errors="replace").splitlines()[0]
                if value.strip().removeprefix("./") != filename:
                    errors.append(comp + "_PTR")
            except (OSError, IndexError):
                errors.append(comp + "_IO")
        if errors:
            if first_bad is None:
                first_bad = stamp + ":" + ",".join(errors)
            continue
        warn = "NEWER_INCOMPLETE:" + first_bad if first_bad else ""
        return done, stamp, warn
    return None, None, "NO_VALID_CHECKPOINT:" + (first_bad or "UNKNOWN")


def unarchived_success(case: Path) -> bool:
    path = case / "CaseStatus"
    if not path.is_file():
        return False
    try:
        # These are ordered lines in the append-only CIME case status record.
        last_model = last_archive = -1
        with path.open(errors="replace") as handle:
            for i, line in enumerate(handle):
                if "model execution success" in line:
                    last_model = i
                if "st_archive success" in line:
                    last_archive = i
        return last_model > last_archive
    except OSError:
        return False


def site_report(batch: str, site: str, start: int, target: int,
                jobs: list[dict]) -> dict:
    name = case_name(batch, site)
    case = CASE_ROOT / name
    rest = OUTPUT_ROOT / "archive" / name / "rest"
    done, stamp, warning = restart_status(rest, name, start)
    matched = [job for job in jobs
               if job["name"] in ("run." + name, "st_archive." + name)]
    notes = []
    if warning:
        notes.append(warning)
    if done is not None and done > target:
        notes.append("PAST_TARGET")
    # A completed CIME run without a newer successful archive is not yet a
    # new archived checkpoint. This is especially important after quota errors.
    if not matched and unarchived_success(case):
        notes.append("UNARCHIVED_RUN_SUCCESS")
    if matched:
        if any(job["state"] == "RUNNING" for job in matched):
            state = "RUNNING"
        elif any("DependencyNeverSatisfied" in job["reason"]
                 or "JobHeld" in job["reason"] for job in matched):
            state = "BLOCKED"
        elif any(job["state"] == "PENDING" for job in matched):
            state = "PENDING"
        else:
            state = matched[0]["state"]
    elif done is not None and done >= target and not warning:
        state = "COMPLETE"
    elif "UNARCHIVED_RUN_SUCCESS" in notes or warning.startswith(
            ("NEWER_INCOMPLETE", "NO_VALID_CHECKPOINT", "ARCHIVE_IO_ERROR")):
        state = "REVIEW"
    else:
        state = "IDLE"
    # A missing archive is unknown, not "0 simulated years".
    status_jobs = ", ".join(f"{j['jobid']}:{j['state']}" for j in matched)
    note_text = status_jobs
    if notes:
        note_text += (" | " if note_text else "") + "; ".join(notes)
    return dict(site=site, target=target, completed=done, remaining=(
                max(target - done, 0) if done is not None else None),
                checkpoint=stamp or "-", resubmit=xml_value(case, "RESUBMIT"),
                slurm=state, note=note_text or "-")


def render(batch: str, rows: list[dict]) -> None:
    print("=" * 116)
    print(f"{batch} | {len(rows)} sites")
    print("=" * 116)
    print(f"{'SITE':<9} {'DONE/TARGET':>12} {'LEFT':>7} "
          f"{'CHECKPOINT':>23} {'RESUB':>7} {'SLURM':>12}  JOB IDs / NOTE")
    counts = Counter()
    for r in rows:
        counts[r["slurm"]] += 1
        progress = (str(r["completed"]) if r["completed"] is not None else "?")
        left = str(r["remaining"]) if r["remaining"] is not None else "?"
        print(f"{r['site']:<9} {progress + '/' + str(r['target']):>12} "
              f"{left:>7} {r['checkpoint']:>23} {r['resubmit']:>7} "
              f"{r['slurm']:>12}  {r['note']}")
    print("SUMMARY: " + ", ".join(f"{k}={counts[k]}" for k in (
        "COMPLETE", "BLOCKED", "REVIEW", "IDLE", "PENDING", "RUNNING")
        if counts[k]) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", default="all",
                        choices=["all", *BATCHES],
                        help="Select one batch (default: all four)")
    args = parser.parse_args()
    try:
        jobs = slurm_jobs()
    except (OSError, subprocess.CalledProcessError) as exc:
        print("ERROR: squeue query failed; refusing a misleading IDLE report:",
              exc, file=sys.stderr)
        return 1
    print("READ-ONLY four-batch CLM-FATES progress")
    print("UTC:", datetime.now(timezone.utc).isoformat())
    print("Checkpoint: latest archived restart with 3 components + dated pointers.")
    print("RUNNING/PENDING describe Slurm jobs, not a completed model year.\n")
    batches = BATCHES if args.batch == "all" else {
        args.batch: BATCHES[args.batch]}
    for batch, sites in batches.items():
        render(batch, [site_report(batch, site, *config, jobs)
                       for site, config in sites.items()])
    print("No model cases, restart files, Slurm jobs or scratch archives modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

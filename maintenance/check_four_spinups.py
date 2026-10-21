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
    # Other Slurm jobs for the SAME STATION may belong to distinct cases.
    # Never count a branch run as progress of the canonical batch case.
    related = [job for job in jobs if job not in matched and
               job["name"].startswith(("run." + site + "_",
                                       "st_archive." + site + "_"))]
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
    # A branch/sensitivity case should be visible, without mislabeling the
    # original SPINUP500_11P case as actually running.
    if related and not matched and state in ("IDLE", "REVIEW"):
        if any(j["state"] == "RUNNING" for j in related):
            state = "RELATED_RUN"
        elif any("DependencyNeverSatisfied" in j["reason"]
                 or "JobHeld" in j["reason"] for j in related):
            state = "RELATED_BLOCK"
        else:
            state = "RELATED_WAIT"
    # A missing archive is unknown, not "0 simulated years".
    status_jobs = ", ".join(f"{j['jobid']}:{j['state']}" for j in matched)
    note_text = status_jobs
    if related:
        related_text = ", ".join(
            f"{j['jobid']}:{j['state']}:{j['name']} [{j['reason']}]"
            for j in related)
        note_text += (" | " if note_text else "") + "OTHER_CASE: " + related_text
    if notes:
        note_text += (" | " if note_text else "") + "; ".join(notes)
    return dict(site=site, target=target, completed=done, remaining=(
                max(target - done, 0) if done is not None else None),
                checkpoint=stamp or "-", resubmit=xml_value(case, "RESUBMIT"),
                slurm=state, note=note_text or "-")


# Specific independent campaigns the operator wants tracked even after jobs finish.
# Any other active same-station Slurm cases are discovered automatically.
KNOWN_EXTRA_CASES = {
    "IT-Noe": ("IT-Noe_ERA5_ABW_BRANCH2009",),
    "CH-Aws": ("CH-Aws_FATES_SPINUP1000_RH34A",
               "CH-Aws_FATES_SPINUP1000_RH29A"),
}


def last_cime_cycle(case: Path) -> dict:
    """Read latest submitted run/archive PAIR; don't mistake prior success for it.

    This is a log-event check, not a proof of scientific model equilibrium.
    """
    cycle = {}
    path = case / "CaseStatus"
    if not path.is_file():
        return cycle
    try:
        with path.open(errors="replace") as handle:
            for line in handle:
                found = re.search(
                    r"case\.submit success case\.run:(\d+), "
                    r"case\.st_archive:(\d+)", line)
                if found:
                    cycle = {
                        "run_id": found.group(1), "archive_id": found.group(2),
                        "run_ok": False, "run_error": False,
                        "archive_ok": False, "archive_error": False,
                    }
                    continue
                if not cycle:
                    continue
                rid, aid = cycle["run_id"], cycle["archive_id"]
                if re.search(r"\bcase\.run success " + re.escape(rid) + r"\b", line):
                    cycle["run_ok"] = True
                if "case.run error" in line and not cycle["run_ok"]:
                    cycle["run_error"] = True
                if re.search(r"\bst_archive success " + re.escape(aid) + r"\b", line):
                    cycle["archive_ok"] = True
                if ("st_archive error" in line and not cycle["archive_ok"]):
                    cycle["archive_error"] = True
    except OSError:
        return {}
    return cycle


def extra_case_report(site: str, name: str, jobs: list[dict]) -> dict:
    case = CASE_ROOT / name
    case_exists = case.is_dir()
    start_value = xml_value(case, "RUN_STARTDATE") if case_exists else "-"
    start_match = re.match(r"^(\d{4})-\d\d-\d\d$", start_value)
    start_year = int(start_match.group(1)) if start_match else None
    archive_root = xml_value(case, "DOUT_S_ROOT") if case_exists else "-"
    if archive_root == "-" or not archive_root.startswith("/"):
        archive_root = str(OUTPUT_ROOT / "archive" / name)
    # This independent case's 3-component restarts only. Never borrow
    # the site's canonical _11P archive or its archived model years.
    if start_year is not None:
        done, stamp, warning = restart_status(Path(archive_root) / "rest",
                                              name, start_year)
    else:
        done, stamp, warning = None, None, "RUN_STARTDATE_UNKNOWN"
    matched = [j for j in jobs
               if j["name"] in ("run." + name, "st_archive." + name)]
    run_jobs = [j for j in matched if j["name"] == "run." + name]
    arc_jobs = [j for j in matched if j["name"] == "st_archive." + name]
    cycle = last_cime_cycle(case)
    run_ok, arc_ok = cycle.get("run_ok", False), cycle.get("archive_ok", False)
    run_err, arc_err = cycle.get("run_error", False), cycle.get("archive_error", False)
    archive_blocked = any(
        "DependencyNeverSatisfied" in j["reason"] or "JobHeld" in j["reason"]
        for j in arc_jobs)
    if any(j["state"] == "RUNNING" for j in run_jobs):
        phase = "MODEL_RUNNING"
    elif any(j["state"] == "PENDING" for j in run_jobs):
        phase = "MODEL_QUEUED"
    elif archive_blocked:
        phase = "ARCHIVE_BLOCKED"
    elif run_ok and not arc_ok and arc_jobs:
        phase = ("ARCHIVING" if any(j["state"] == "RUNNING" for j in arc_jobs)
                 else "MODEL_OK_ARCH_WAIT")
    elif arc_err:
        phase = "ARCHIVE_ERROR"
    elif run_err and not run_ok:
        phase = "MODEL_ERROR"
    elif arc_ok and done is not None and not warning:
        phase = "ARCHIVED"
    elif arc_ok:
        phase = "ARCHIVE_OK_VERIFY"
    elif run_ok and not arc_ok:
        phase = "MODEL_OK_ARCH_CHECK"
    elif arc_jobs:
        phase = "ARCHIVE_QUEUED"
    elif not case_exists:
        phase = "CASE_MISSING"
    else:
        phase = "NO_ACTIVE_JOB"

    def job_text(which: str, active: list[dict], ok: bool, error: bool) -> str:
        if active:
            return ",".join(j["jobid"] + ":" + (
                "R" if j["state"] == "RUNNING" else
                "PD" if j["state"] == "PENDING" else j["state"])
                for j in active)
        ident = cycle.get(which + "_id", "-")
        return ident + (":OK" if ok else ":ERROR" if error else ":?")
    job_run = job_text("run", run_jobs, run_ok, run_err)
    job_arc = job_text("archive", arc_jobs, arc_ok, arc_err)
    notes = []
    for j in arc_jobs + run_jobs:
        if j["state"] == "PENDING":
            notes.append(j["jobid"] + ":" + j["reason"])
    if warning and warning != "NO_ARCHIVE":
        notes.append(warning)
    if start_year is not None and xml_value(case, "RUN_TYPE") == "branch":
        notes.append("BRANCH_MODEL_YEARS_ONLY")
    return {
        "site": site, "case": name, "start": start_value,
        "archived_years": done, "checkpoint": stamp or "-",
        "resubmit": xml_value(case, "RESUBMIT") if case_exists else "-",
        "model_job": job_run, "archive_job": job_arc,
        "phase": phase, "notes": "; ".join(notes) or "-",
    }


def discover_extra_cases(sites: set[str], jobs: list[dict]) -> list[tuple[str, str]]:
    canonical = {
        case_name(batch, site)
        for batch, group in BATCHES.items()
        for site in group
    }
    found = set()
    for site in sites:
        for extra in KNOWN_EXTRA_CASES.get(site, ()):
            # Keep known monitoring targets visible even after Slurm finishes.
            found.add((site, extra))
    for j in jobs:
        for prefix in ("run.", "st_archive."):
            if not j["name"].startswith(prefix):
                continue
            name = j["name"][len(prefix):]
            if name in canonical:
                continue
            # Match a site boundary, not merely an overlapping name prefix.
            for site in sites:
                if name.startswith(site + "_"):
                    found.add((site, name))
                    break
    return sorted(found)


def render_extra_cases(sites: set[str], jobs: list[dict]) -> None:
    extras = discover_extra_cases(sites, jobs)
    if not extras:
        return
    print("=" * 116)
    print(f"ADDITIONAL / BRANCH CASES | {len(extras)} distinct CIME cases")
    print("=" * 116)
    print("These are NOT the canonical batch cases. ARCHIVED means years since")
    print("that case's RUN_STARTDATE, NOT inherited spin-up years or a 1000-y target.")
    print(f"{'SITE':<9} {'CASE':<40} {'YEARS':>6} {'CHECKPOINT':>22} "
          f"{'RESUB':>5}  {'PHASE':<22}")
    for site, name in extras:
        r = extra_case_report(site, name, jobs)
        elapsed = str(r["archived_years"]) if r["archived_years"] is not None else "?"
        print(f"{site:<9} {name:<40} {elapsed:>6} "
              f"{r['checkpoint']:>22} {r['resubmit']:>5}  {r['phase']}")
        print(f"{'':9} MODEL={r['model_job']} ARCHIVE={r['archive_job']} "
              f"RUN_STARTDATE={r['start']} | {r['notes']}")
    print("MODEL_OK_ARCH_WAIT = CIME case.run success, archive job pending/running;")
    print("no new years are credited until archived 3-component restart is present.\n")


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
        "COMPLETE", "BLOCKED", "REVIEW", "IDLE", "PENDING", "RUNNING",
        "RELATED_RUN", "RELATED_WAIT", "RELATED_BLOCK")
        if counts[k]) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", default="all",
                        choices=["all", *BATCHES],
                        help="Select one batch (default: all four)")
    parser.add_argument("--no-extra-cases", action="store_true",
                        help="Hide independent branch/sensitivity case details")
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
    print("RUNNING/PENDING refer to this specific batch case, not completed years.")
    print("RELATED_* means a DIFFERENT case is active for the same site.\n")
    batches = BATCHES if args.batch == "all" else {
        args.batch: BATCHES[args.batch]}
    for batch, sites in batches.items():
        render(batch, [site_report(batch, site, *config, jobs)
                       for site, config in sites.items()])
    if not args.no_extra_cases:
        render_extra_cases({site for group in batches.values() for site in group}, jobs)
    print("No model cases, restart files, Slurm jobs or scratch archives modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

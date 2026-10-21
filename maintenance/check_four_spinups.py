#!/usr/bin/env python3
"""Read-only, unified four-batch IRIDIS6 CLM-FATES spin-up monitoring.

Exactly one explicitly selected, current CIME case per site in each main table.
For IT-Noe use ERA5 branch case; for CH-Aws use active RH34A case.
Legacy _11P and RH29A may be displayed separately (--show-alternates).
Reports independent MODEL/ARCHIVE phases and archived restart progress.
Neither runs nor queue presence count as archived years. Python stdlib only.
No case.submit, xmlchange, cleanup or filesystem writes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
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


PRIMARY_CASE_OVERRIDES = {
    # These are the CURRENT experiments to monitor in the 11-site slot.
    # Their older _11P cases remain untouched, and may be inspected with
    # --show-alternates, but must not replace the active run in summary tables.
    "FLUXNET_MultiSite_11": {
        "IT-Noe": ("IT-Noe_ERA5_ABW_BRANCH2009", "ERA5-BR"),
        "CH-Aws": ("CH-Aws_FATES_SPINUP1000_RH34A", "RH34A"),
    }
}


def case_name(batch: str, site: str) -> str:
    override = PRIMARY_CASE_OVERRIDES.get(batch, {}).get(site)
    if override:
        return override[0]
    if batch.endswith("_11"):
        return site + "_FATES_SPINUP500_11P"
    if batch.endswith("_13"):
        return site + "_FATES_SPINUP1000_S30SHARED"
    return site + "_FATES_SPINUP500"


def variant(batch: str, site: str) -> str:
    return PRIMARY_CASE_OVERRIDES.get(batch, {}).get(site, ("", "-"))[1]


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


def current_case_phase(case: Path, name: str, jobs: list[dict],
                       archived: int | None, warning: str) -> dict:
    """Diagnose model and archive jobs independently for the SAME case."""
    matched = [j for j in jobs
               if j["name"] in ("run." + name, "st_archive." + name)]
    run_jobs = [j for j in matched if j["name"] == "run." + name]
    arch_jobs = [j for j in matched if j["name"] == "st_archive." + name]
    cycle = last_cime_cycle(case)
    model_ok, archive_ok = cycle.get("run_ok", False), cycle.get("archive_ok", False)
    model_error = cycle.get("run_error", False)
    archive_error = cycle.get("archive_error", False)
    running = any(j["state"] == "RUNNING" for j in run_jobs)
    queued = any(j["state"] == "PENDING" for j in run_jobs)
    archive_running = any(j["state"] == "RUNNING" for j in arch_jobs)
    archive_pending = any(j["state"] == "PENDING" for j in arch_jobs)
    blocked = any(("DependencyNeverSatisfied" in j["reason"]
                   or "JobHeld" in j["reason"]) for j in matched)
    if running:
        phase = "RUNNING"
    elif queued:
        phase = "PENDING"
    elif blocked:
        phase = "BLOCKED"
    elif model_ok and not archive_ok and (archive_pending or archive_running):
        phase = "ARCH_WAIT" if archive_pending else "ARCHIVING"
    elif model_error and not model_ok:
        phase = "MODEL_FAIL"
    elif archive_error:
        phase = "ARCH_FAIL"
    elif archive_running:
        phase = "ARCHIVING"
    elif archive_pending:
        phase = "ARCH_WAIT"
    elif archived is not None and archived >= 0 and not warning and archive_ok:
        phase = "IDLE"  # caller converts to COMPLETE if at target
    elif model_ok and not archive_ok:
        phase = "CHECK_ARCHIVE"
    elif warning and warning != "NO_ARCHIVE":
        phase = "REVIEW"
    else:
        phase = "IDLE"

    def describe(items, kind, success, error):
        if items:
            return ",".join(
                j["jobid"] + ":" + (
                    "R" if j["state"] == "RUNNING" else
                    "PD" if j["state"] == "PENDING" else
                    j["state"]) for j in items)
        job_id = cycle.get(kind + "_id")
        if job_id:
            return job_id + (":OK" if success else ":ERR" if error else ":?")
        return "-"
    return {
        "phase": phase,
        "run_job": describe(run_jobs, "run", model_ok, model_error),
        "arch_job": describe(arch_jobs, "archive", archive_ok, archive_error),
        "queue_reasons": ";".join(
            j["jobid"] + ":" + j["reason"]
            for j in matched if j["state"] == "PENDING"),
    }


def site_report(batch: str, site: str, configured_start: int, target: int,
                jobs: list[dict]) -> dict:
    name = case_name(batch, site)
    case = CASE_ROOT / name
    live_start = xml_value(case, "RUN_STARTDATE") if case.is_dir() else "-"
    match = re.match(r"^(\d{4})-\d{2}-\d{2}$", live_start)
    # Never borrow the old canonical start if a new case has a different one.
    start = int(match.group(1)) if match else (
        configured_start if variant(batch, site) == "-" else None)
    archive_root = xml_value(case, "DOUT_S_ROOT") if case.is_dir() else "-"
    if archive_root == "-" or not archive_root.startswith("/"):
        archive_root = str(OUTPUT_ROOT / "archive" / name)
    if start is not None:
        done, stamp, warning = restart_status(Path(archive_root) / "rest",
                                              name, start)
    else:
        done, stamp, warning = None, None, "UNKNOWN_START_DATE"
    phase = current_case_phase(case, name, jobs, done, warning)
    status = phase["phase"]
    if status == "IDLE" and done is not None and done >= target and not warning:
        status = "COMPLETE"
    if not case.is_dir():
        status = "NO_CASE"
    if done is None:
        left = None
    else:
        left = max(0, target - done)
    notes = []
    if warning:
        notes.append(warning)
    if phase["queue_reasons"]:
        notes.append(phase["queue_reasons"])
    if done is not None and done > target:
        notes.append("PAST_TARGET")
    runtype = xml_value(case, "RUN_TYPE")
    branch_years = None
    if runtype.lower() == "branch" and stamp:
        refdate = xml_value(case, "RUN_REFDATE")
        refmatch = re.match(r"^(\d{4})-\d{2}-\d{2}$", refdate)
        if refmatch and int(stamp[:4]) >= int(refmatch.group(1)):
            branch_years = int(stamp[:4]) - int(refmatch.group(1))
            notes.append(f"BRANCH_YEARS={branch_years} FROM={refdate}")
        else:
            notes.append("BRANCH_YEARS=UNKNOWN (check RUN_REFDATE)")
    if status == "IDLE" and unarchived_success(case):
        status = "CHECK_ARCHIVE"
        notes.append("MODEL_SUCCESS_AFTER_LAST_ARCHIVE")
    return {
        "site": site, "variant": variant(batch, site), "case": name,
        "target": target, "completed": done, "remaining": left,
        "checkpoint": stamp or "-", "resubmit": xml_value(case, "RESUBMIT"),
        "status": status, "model": phase["run_job"], "archive": phase["arch_job"],
        "branch_years": branch_years, "note": "; ".join(notes) or "-",
    }


def render(batch: str, rows: list[dict]) -> None:
    print("=" * 147)
    print(f"{batch} | {len(rows)} sites | CURRENT MONITORED CASE for each site")
    print("=" * 147)
    print(f"{'SITE':<9} {'CASE':<9} {'DONE/TARGET':>12} {'LEFT':>7} "
          f"{'CHECKPOINT':>21} {'RESUB':>6} {'PHASE':<14} "
          f"{'MODEL':<15} {'ARCHIVE':<15} NOTE")
    counts = Counter()
    for r in rows:
        counts[r["status"]] += 1
        progress = str(r["completed"]) if r["completed"] is not None else "?"
        remaining = str(r["remaining"]) if r["remaining"] is not None else "?"
        print(f"{r['site']:<9} {r['variant']:<9} "
              f"{progress + '/' + str(r['target']):>12} "
              f"{remaining:>7} {r['checkpoint']:>21} "
              f"{r['resubmit']:>6} {r['status']:<14} "
              f"{r['model']:<15} {r['archive']:<15} {r['note']}")
        if r["variant"] != "-":
            print(" " * 11 + "CASE=" + r["case"])
    print("SUMMARY: " + ", ".join(f"{key}={count}" for key, count in sorted(
        counts.items())) + "\n")


def show_alternates(batches: dict, jobs: list[dict]) -> None:
    """Optional separate legacy incidents, never included in primary summary."""
    print("=" * 117)
    print("OTHER / HISTORIC CASES (not counted in four-batch main status)")
    print("=" * 117)
    recorded = set()
    for batch, sites in batches.items():
        for site, (config_start, target) in sites.items():
            primary = case_name(batch, site)
            if (batch, site) not in [
                ("FLUXNET_MultiSite_11", "IT-Noe"),
                ("FLUXNET_MultiSite_11", "CH-Aws")
            ]:
                continue
            extra_names = (
                [site + "_FATES_SPINUP500_11P"]
                + (["CH-Aws_FATES_SPINUP1000_RH29A"] if site == "CH-Aws" else [])
            )
            for name in extra_names:
                if name == primary or name in recorded:
                    continue
                recorded.add(name)
                case = CASE_ROOT / name
                live_start = xml_value(case, "RUN_STARTDATE")
                m = re.match(r"^(\d{4})-", live_start)
                start = int(m.group(1)) if m else config_start
                done, stamp, warning = restart_status(
                    OUTPUT_ROOT / "archive" / name / "rest", name, start)
                info = current_case_phase(case, name, jobs, done, warning)
                print(f"{site:<9} {name}: archived={done if done is not None else '?'} "
                      f"checkpoint={stamp or '-'} phase={info['phase']}"
                      f" model={info['run_job']} archive={info['arch_job']}"
                      f" note={warning or info['queue_reasons'] or '-'}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", default="all", choices=["all", *BATCHES],
                        help="Select one batch (default all four)")
    parser.add_argument("--show-alternates", action="store_true",
                        help="Show older IT-Noe/CH-Aws cases in a separate section")
    parser.add_argument("--no-extra-cases", action="store_true",
                        help="Deprecated legacy option; no effect on unified output")
    args = parser.parse_args()
    try:
        jobs = slurm_jobs()
    except (OSError, subprocess.CalledProcessError) as exc:
        print("ERROR: squeue unavailable; refusing misleading IDLE statuses:",
              exc, file=sys.stderr)
        return 1
    print("READ-ONLY CLM-FATES PROGRESS |", datetime.now(timezone.utc).isoformat())
    print("ONE current case per station. MODEL and ARCHIVE states are independent.")
    print("DONE = archived three-component checkpoint years from that case's"
          " RUN_STARTDATE.")
    print("For BRANCH runs, BRANCH_YEARS (if RUN_REFDATE is valid) is separately"
          " reported; not added to DONE.")
    batches = BATCHES if args.batch == "all" else {args.batch: BATCHES[args.batch]}
    for batch, sites in batches.items():
        render(batch, [site_report(batch, site, start, target, jobs)
                       for site, (start, target) in sites.items()])
    if args.show_alternates:
        show_alternates(batches, jobs)
    print("READ ONLY: no model files, CIME configuration, or jobs modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

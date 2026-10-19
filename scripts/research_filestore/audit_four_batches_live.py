#!/usr/bin/env python3
"""READ-ONLY: audit four FLUXNET multi-site CIME campaigns on IRIDIS6.

Never submits jobs, changes model files, or writes reports unless --json is set.
A 1000-year milestone requires consecutive h0a history AND archived restart
at/after the model-year-1000 boundary. This is not a convergence assessment.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

SCRATCH = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
CASES = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases")
FILSTORE = Path("/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives")
BATCHES = {
    "FLUXNET_MultiSite_6": {
        "DE-Hai": 2000, "RU-Fyo": 1998, "DE-Tha": 1996,
        "DK-Sor": 1996, "NL-Loo": 1997, "IL-Yat": 2000},
    "FLUXNET_MultiSite_8": {
        "CZ-BK1": 2004, "IT-Ren": 1999, "FR-Hes": 1997,
        "FR-FBn": 2008, "DE-Hzd": 2010, "CH-Dav": 1997,
        "BE-Vie": 1996, "IT-Lav": 2003},
    "FLUXNET_MultiSite_11": {
        "BE-Bra": 1996, "FR-Fon": 2005, "GL-ZaH": 2000,
        "IT-Noe": 2004, "AT-Neu": 2002, "FI-Sod": 2001,
        "CH-Aws": 2006, "CH-Cha": 2005, "CH-Fru": 2005,
        "CH-Lae": 2004, "CZ-Stn": 2010},
    "FLUXNET_MultiSite_13": {
        "DE-Lnf": 2002, "DE-Obe": 2008, "ES-Agu": 2006,
        "ES-LJu": 2004, "IT-Col": 1996, "DE-Gri": 2004,
        "DE-RuR": 2011, "FI-Hyy": 1997, "FI-Let": 2010,
        "FR-Pue": 2000, "GF-Guy": 2004, "IT-MBo": 2003,
        "IT-Tor": 2008},
}


def case_name(batch, site):
    if batch.endswith("_11"):
        return site + "_FATES_SPINUP500_11P"
    if batch.endswith("_13"):
        return site + "_FATES_SPINUP1000_S30SHARED"
    return site + "_FATES_SPINUP500"


def history(root, case, first):
    rx = re.compile(re.escape(case) + r"\.clm2\.h0a\.(\d{4})-\d{2}-\d{2}-\d{5}\.nc$")
    years = []
    if root.is_dir():
        for p in root.glob("*.nc"):
            m = rx.fullmatch(p.name)
            if m and p.is_file():
                years.append(int(m.group(1)))
    continuous = 0
    present = set(years)
    while first + continuous in present:
        continuous += 1
    return len(years), len(present), continuous


def restart(root, first):
    if not root.is_dir():
        return 0, "NONE"
    years = [
        int(p.name[:4]) for p in root.iterdir()
        if p.is_dir() and re.fullmatch(r"\d{4}-01-01-00000", p.name)
    ]
    if not years:
        return 0, "NONE"
    y = max(years)
    return max(0, y - first), f"{y}-01-01-00000"


def inspect(batch, site, first, jobs):
    case = case_name(batch, site)
    archive = SCRATCH / "archive" / case
    n, uniq, continuous = history(archive / "lnd/hist", case, first)
    elapsed, stamp = restart(archive / "rest", first)
    active = [name + "(" + state + ")" for name, state in jobs if case in name]
    # History and restart evidence are separate; neither is inferred from RESUBMIT.
    milestone = continuous >= 1000 and elapsed >= 1000
    if milestone:
        state = "1000_YEAR_MILESTONE"
    elif continuous >= 500 and elapsed >= 500:
        state = "500_PLUS"
    elif continuous or elapsed:
        state = "PARTIAL_OR_MISMATCH"
    else:
        state = "NO_ARCHIVED_PROGRESS"
    cstat = CASES / case / "CaseStatus"
    last = "NONE"
    if cstat.is_file():
        lines = cstat.read_text(errors="replace").splitlines()
        last = next((s.strip()[:170] for s in reversed(lines) if s.strip()), "NONE")
    dest = FILSTORE / batch / site / case
    return dict(batch=batch, site=site, case=case, history_files=n,
                unique_years=uniq, continuous_h0a_years=continuous,
                archived_restart_model_year=elapsed, restart_date=stamp,
                milestone_1000=milestone, status=state,
                slurm_jobs=",".join(active) if active else "NONE",
                research_receipt_present=(dest / "verification_receipt.json").is_file(),
                last_case_status=last)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", choices=["all", *BATCHES], default="all")
    parser.add_argument("--json", help="Optional operator-owned report path; refuses overwrite")
    args = parser.parse_args()
    p = subprocess.run(["squeue", "-h", "-u", "ly3n24", "-o", "%j|%t"],
                       text=True, capture_output=True, check=True)
    jobs = [line.split("|", 1) for line in p.stdout.splitlines() if "|" in line]
    selected = BATCHES if args.batch == "all" else {args.batch: BATCHES[args.batch]}
    rows = []
    print("READ-ONLY four-batch CIME archive progress; 1000 years != carbon convergence")
    for batch, sites in selected.items():
        print("\n" + batch)
        print(f"{'Site':<9} {'Hist':>5} {'Contig':>6} {'Rest':>6} {'Progress':<24} {'Queue'}")
        for site, first in sites.items():
            r = inspect(batch, site, first, jobs)
            rows.append(r)
            print(f"{site:<9} {r['history_files']:>5} "
                  f"{r['continuous_h0a_years']:>6} "
                  f"{r['archived_restart_model_year']:>6} "
                  f"{r['status']:<24} {r['slurm_jobs']}")
        print("1000-year milestones:", sum(r["milestone_1000"] for r in rows
                                            if r["batch"] == batch), "/", len(sites))
    if args.json:
        dest = Path(args.json).expanduser()
        if dest.exists():
            parser.error(f"Report already exists, refusing overwrite: {dest}")
        dest.write_text(json.dumps({
            "audit_utc": datetime.now(timezone.utc).isoformat(),
            "rows": rows}, indent=2) + "\n", encoding="utf-8")
        print("\nOperator report:", dest)
    print("\nNo CIME cases, model output, or Slurm jobs modified.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read-only preflight for five 1000->3000-year spin-ups after Scratch inode exhaustion.

Does not alter CIME, Slurm, restart files, or history. The separately distributed
recover_five_site_spinup3000_after_quota.py must be reviewed before running repair.
"""
from pathlib import Path
import subprocess

BASE = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
CASES = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases")
SITES = {"RU-Fyo": 1998, "DE-Tha": 1996, "DK-Sor": 1996,
         "NL-Loo": 1997, "IL-Yat": 2000}
COMPONENTS = {"atm": "datm.r", "lnd": "clm2.r", "cpl": "cpl.r"}

def run(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
    return p.stdout.strip() if p.returncode == 0 else "ERROR:" + p.stderr.strip()

jobs = run(["squeue", "-h", "-u", "ly3n24", "-o", "%j|%T|%R"]).splitlines()
print(f"{'SITE':<9} {'ARCHIVED':>8} {'LEFT':>7} {'RESUB':>6} {'STATE'}")
for site, first in SITES.items():
    name = site + "_FATES_SPINUP500"
    case, arch = CASES / name, BASE / "archive" / name / "rest"
    work = BASE / name / "run"
    stamps = sorted(d for d in arch.glob("????-01-01-00000") if d.is_dir())
    errors = []
    if not stamps or not (case / "xmlquery").is_file():
        print(f"{site:<9} {'-':>8} {'-':>7} {'-':>6} CASE/CHECKPOINT MISSING")
        continue
    stamp = stamps[-1].name
    years = int(stamp[:4]) - first
    resub = run(["./xmlquery", "RESUBMIT", "--value"], cwd=case)
    expected = (3000 - years) // 5 - 1
    if resub != str(expected) and years < 3000:
        errors.append(f"RESUBMIT={resub} expected={expected}")
    for comp, kind in COMPONENTS.items():
        fname = f"{name}.{kind}.{stamp}.nc"
        source = stamps[-1] / fname
        pointer = work / f"rpointer.{comp}"
        if not source.is_file() or source.stat().st_size == 0:
            errors.append(f"missing archived {comp}")
        if not pointer.is_file() or fname not in pointer.read_text(errors="replace"):
            errors.append(f"run {comp} pointer mismatch")
    if any(name in j for j in jobs):
        errors.append("active/queued Slurm job")
    if not (1000 <= years <= 3000 and years % 5 == 0):
        errors.append("unexpected checkpoint year")
    h = [p for p in work.glob(name + ".clm2.h*.nc")
         if any(p.name.startswith(name + ".clm2." + kind) for kind in ("h0a.", "h0i."))]
    print(f"{site:<9} {years:>8} {max(0,3000-years):>7} {resub:>6} "
          + ("REVIEW" if errors else "CHECKPOINT OK"))
    for e in errors:
        print("   WARNING:", e)
    print("   run history NetCDF files:", len(h))
print("READ ONLY; this does not certify coordinated restart integrity or approve submission.")

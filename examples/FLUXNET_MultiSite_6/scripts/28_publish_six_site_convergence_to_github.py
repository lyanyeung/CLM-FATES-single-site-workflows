#!/usr/bin/env python3
"""Validate and publish one completed six-site convergence snapshot to GitHub.

RUN ONLY AFTER script 27 has succeeded for ALL SIX sites (Status=OK).
Uploads derived PNG/CSV/JSON only. No raw EC, input NetCDF, restart, or model files.
Clones a fresh short-lived checkout rather than relying on the user's possibly
conflicted working tree. Staged content is limited to one new snapshot folder.

Usage:
  python3 28_publish_six_site_convergence_to_github.py --snapshot /research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots/<timestamp>_archive_snapshot
Optional --dry-run for validation without Git changes.

No automatic execution or background upload: operator must invoke explicitly.
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path.home() / "CLM-FATES-single-site-workflows"
RFS_ROOT = Path("/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots")
SITES = ("DE-Hai", "RU-Fyo", "DE-Tha", "DK-Sor", "NL-Loo", "IL-Yat")
PUBLISH_PARENT = Path("examples/FLUXNET_MultiSite_6/figures/convergence_snapshots")
EXTENSIONS = {".png", ".csv", ".json"}
REQUIRED_PER_SITE = (
    "_01_carbon_pools_annual_mean.png",
    "_02_carbon_pools_last250years.png",
    "_04_FATES_PFT_VEGC_evolution.png",
    "_GPP_NEE_monthly_overview.png",
    "_carbon_annual_means.csv",
    "_convergence_metrics.csv",
    "_FATES_PFT_VEGC_annual_pct.csv",
    "_monthly_FATES_vs_EC.csv",
    "_monthly_metrics.csv",
    "_metadata.json",
)
def run(*argv, cwd=None):
    p = subprocess.run(argv, cwd=str(cwd) if cwd else None, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError("Command failed: " + " ".join(argv) +
                           "\n" + (p.stdout + p.stderr)[-1800:])
    return p.stdout.strip()

def safe_regular(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError("Missing, empty or symlink file: " + str(path))
    if path.suffix not in EXTENSIONS:
        raise RuntimeError("Unsupported file extension: " + str(path))
    if path.stat().st_size > 20 * 1024 * 1024:
        raise RuntimeError("Refusing file >20 MiB: " + str(path))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    snapshot = args.snapshot.resolve(strict=True)
    if snapshot.parent != RFS_ROOT.resolve():
        raise RuntimeError("Snapshot must be an immediate child of designated RFS snapshots root")
    summary = snapshot / "six_site_latest_checkpoint_convergence_summary.csv"
    safe_regular(summary)
    rows = list(csv.DictReader(summary.open(newline="")))
    if len(rows) != len(SITES) or {r["Site"] for r in rows} != set(SITES):
        raise RuntimeError("Snapshot does not contain exactly the expected six sites")
    failed = {r["Site"]: r["Status"] for r in rows if r["Status"] != "OK"}
    if failed:
        raise RuntimeError("Not all six sites fully succeeded: " + str(failed))
    files = [summary, snapshot / "RUN_INFO.json"]
    for site in SITES:
        d = snapshot / site
        if not d.is_dir() or d.is_symlink():
            raise RuntimeError("Missing or symlink station folder: " + str(d))
        for suffix in REQUIRED_PER_SITE:
            files.append(d / (site + suffix))
    # Publish only explicit allowlist, no accidental original EC data.
    for f in files:
        safe_regular(f)
        f.relative_to(snapshot)
    runinfo = json.loads((snapshot / "RUN_INFO.json").read_text())
    if {x["Site"] for x in runinfo.get("results", [])} != set(SITES):
        raise RuntimeError("RUN_INFO does not match six-site summary")
    print("VALIDATION PASS:",len(files),"small derived artifacts for",len(SITES),"sites")
    print("Source:",snapshot)
    print("Publish target:",PUBLISH_PARENT / snapshot.name)
    if args.dry_run:
        print("DRY RUN: no Git operation performed.")
        return 0
    remote = run("git","-C",str(REPO),"remote","get-url","origin")
    with tempfile.TemporaryDirectory(prefix="six_site_publish_",dir=str(Path.home())) as temp:
        clone = Path(temp) / "checkout"
        run("git","clone","--depth","1","--single-branch","--branch","main",
            remote,str(clone))
        dest = clone / PUBLISH_PARENT / snapshot.name
        if dest.exists():
            raise RuntimeError("GitHub destination already exists; refusing overwrite: "+str(dest))
        for f in files:
            target = dest / f.relative_to(snapshot)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(f,target)
        checksum = []
        for f in files:
            h=hashlib.sha256()
            with f.open("rb") as fd:
                for chunk in iter(lambda:fd.read(1048576),b""):
                    h.update(chunk)
            checksum.append(h.hexdigest()+"  "+f.relative_to(snapshot).as_posix())
        (dest/"SHA256SUMS.txt").write_text("\n".join(checksum)+"\n")
        run("git","add","--",str(PUBLISH_PARENT / snapshot.name),cwd=clone)
        staged = run("git","diff","--cached","--name-only",cwd=clone)
        if not staged:
            raise RuntimeError("No Git files staged; check .gitignore before pushing.")
        run("git","-c","user.name=IRIDIS6 CLM-FATES",
            "-c","user.email=lyanyeung@users.noreply.github.com",
            "commit","-m","Publish validated six-site archived convergence snapshot "+snapshot.name,cwd=clone)
        print("Pushing derived plots and tables to origin/main...")
        run("git","push","origin","HEAD:main",cwd=clone)
        print("GITHUB PUBLISH SUCCESS")
        print("Commit:",run("git","rev-parse","HEAD",cwd=clone))
        print("Path:",PUBLISH_PARENT / snapshot.name)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

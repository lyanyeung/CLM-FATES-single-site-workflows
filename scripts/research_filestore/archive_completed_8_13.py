#!/usr/bin/env python3
"""Non-destructive archiving of individually verified 1000-year sites in batches 8 and 13.

Use on IRIDIS6 login nodes. This tool NEVER deletes Scratch data, changes CIME
cases, calls case.submit, or invokes rsync --delete. It copies the complete
short-term archive, complete final run directory, and selected case metadata.

Modes:
  inspect -- read-only validation of 1000 annual h0a files and locations
  copy    -- check Slurm + NFS, rsync data, then SHA-256 source/dest verification
  verify  -- independently hash-check the existing copies (no transfer)
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

BATCHES = {
    "FLUXNET_MultiSite_8": {
        "CZ-BK1": 2004, "IT-Ren": 1999, "FR-Hes": 1997,
        "FR-FBn": 2008, "DE-Hzd": 2010, "CH-Dav": 1997,
        "BE-Vie": 1996, "IT-Lav": 2003},
    "FLUXNET_MultiSite_13": {
        "DE-Lnf": 2002, "DE-Obe": 2008, "ES-Agu": 2006,
        "ES-LJu": 2004, "IT-Col": 1996, "DE-Gri": 2004,
        "DE-RuR": 2011, "FI-Hyy": 1997, "FI-Let": 2010,
        "FR-Pue": 2000, "GF-Guy": 2004, "IT-MBo": 2003,
        "IT-Tor": 2008},
}
SCRATCH = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
CASES = Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases")
RESEARCH_MOUNT = Path("/research/xclimatetbm")
DEST_BASE = RESEARCH_MOUNT / "ly3n24/CLM_FATES/Spinup_Archives"
USER = "ly3n24"
BATCH = None
START = {}
DEST = None


def case_name(site):
    return site + ("_FATES_SPINUP500" if BATCH == "FLUXNET_MultiSite_8" else "_FATES_SPINUP1000_S30SHARED")


def paths(site):
    name = case_name(site)
    return (
        SCRATCH / "archive" / name,
        SCRATCH / name / "run",
        CASES / name,
        DEST / site / name,
    )


def validate_history(site):
    name = case_name(site)
    archive, run, case, dest = paths(site)
    hist = archive / "lnd/hist"
    if not hist.is_dir():
        raise RuntimeError(f"{site}: missing historical output directory: {hist}")
    pattern = re.compile(re.escape(name) + r"\.clm2\.h0a\.(\d{4})(?:-|[.])")
    files = sorted(hist.glob(name + ".clm2.h0a.*.nc"))
    years = []
    for p in files:
        m = pattern.search(p.name)
        if not m:
            raise RuntimeError(f"{site}: unexpected h0a filename: {p.name}")
        years.append(int(m.group(1)))
    expected = set(range(START[site], START[site] + 1000))
    actual = set(years)
    if len(files) != 1000 or actual != expected or len(actual) != len(files):
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(
            f"{site}: expected exactly 1000 unique h0a years; "
            f"found {len(files)} files, {len(actual)} unique years; "
            f"missing={missing[:12]}, extra={extra[:12]}"
        )
    if not run.is_dir() or not case.is_dir():
        raise RuntimeError(f"{site}: run or CIME case directory missing")
    print(f"[OK] {site}: {years[0]}-{years[-1]}, 1000 annual files; "
          f"archive={archive}; run={run}", flush=True)
    return archive, run, case, dest


def ensure_safe_to_copy(selected):
    target = RESEARCH_MOUNT / "ly3n24"
    # Resolve the actual destination to trigger autofs before checking its FS.
    if not target.is_dir():
        raise RuntimeError(f"Research Filestore destination not accessible: {target}")
    # GNU stat -f reports the actual backing filesystem. On IRIDIS6,
    # findmnt can intermittently list autofs only even when the backing NFS
    # is mounted and working, so do not use its first/only line as a gate.
    fs_type = subprocess.run(
        ["stat", "-f", "-c", "%T", str(target)],
        capture_output=True, text=True, check=True,
    ).stdout.strip().lower()
    if fs_type not in ("nfs", "nfs4"):
        raise RuntimeError(
            f"Refusing transfer: {target} filesystem is {fs_type!r}, not NFS"
        )
    job_result = subprocess.run(
        ["squeue", "-h", "-u", USER, "-o", "%j"],
        capture_output=True, text=True, check=True,
    )
    job_names = job_result.stdout.splitlines()
    active = [j for j in job_names if any(case_name(s) in j for s in selected)]
    if active:
        raise RuntimeError("Refusing transfer while selected case has Slurm jobs: "
                           + ", ".join(active))
    print(
        f"Research filesystem: {fs_type} at {target}; "
        "no selected-site Slurm jobs found",
        flush=True,
    )


def copy_dir(src, dst):
    if not src.is_dir():
        raise RuntimeError(f"Missing source directory: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    # No --delete; don't follow or dereference symlinks; restartable rsync.
    subprocess.run(
        ["rsync", "-a", "--partial", "--info=progress2",
         str(src) + "/", str(dst) + "/"],
        check=True,
    )


def snapshot_case(case, dest):
    dest.mkdir(parents=True, exist_ok=True)
    files = []
    for pattern in ("env_*.xml", "user_nl_*", "*streams*"):
        files.extend(p for p in case.glob(pattern) if p.is_file())
    for name in ("CaseStatus", "README.case", "case.run", "case.st_archive"):
        p = case / name
        if p.is_file():
            files.append(p)
    result = {}
    for p in sorted(set(files)):
        target = dest / p.name
        shutil.copy2(p, target)
        result[p.name] = p
    return result


def inventory(root):
    entries = {}
    if not root.is_dir():
        raise RuntimeError(f"Directory missing: {root}")
    for p in root.rglob("*"):
        key = p.relative_to(root).as_posix()
        if p.is_symlink():
            entries[key] = ("link", os.readlink(p), p)
        elif p.is_file():
            entries[key] = ("file", p.stat().st_size, p)
    return entries


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(4 * 1024 * 1024)
            if not b:
                return h.hexdigest()
            h.update(b)


def verify_pair(source, target, prefix):
    left, right = inventory(source), inventory(target)
    if set(left) != set(right):
        missing = sorted(set(left) - set(right))
        extra = sorted(set(right) - set(left))
        raise RuntimeError(f"{prefix} inventory mismatch: missing={missing[:10]}, "
                           f"extra={extra[:10]}")
    manifest = []
    for number, key in enumerate(sorted(left), 1):
        kind_a, value_a, path_a = left[key]
        kind_b, value_b, path_b = right[key]
        if (kind_a, value_a) != (kind_b, value_b):
            raise RuntimeError(f"{prefix}/{key}: file size or symlink target mismatch")
        if kind_a == "file":
            digest = sha256(path_a)
            if digest != sha256(path_b):
                raise RuntimeError(f"{prefix}/{key}: SHA256 MISMATCH")
            manifest.append((digest, prefix + "/" + key))
        else:
            manifest.append(("SYMLINK:" + value_a, prefix + "/" + key))
        if number % 250 == 0:
            print(f"  {prefix}: verified {number}/{len(left)} entries", flush=True)
    return manifest


def verify_site(site):
    archive, run, case, dest = validate_history(site)
    copied_case = dest / "case_snapshot"
    if not copied_case.is_dir():
        raise RuntimeError(f"Missing CIME case snapshot: {copied_case}")
    metadata = []
    for p in copied_case.iterdir():
        if p.is_file():
            source = case / p.name
            if not source.is_file() or sha256(source) != sha256(p):
                raise RuntimeError(f"{site}: case snapshot mismatch: {p.name}")
            metadata.append((sha256(p), "case_snapshot/" + p.name))
    if not metadata:
        raise RuntimeError(f"{site}: empty case snapshot")
    result = verify_pair(archive, dest / "archive", "archive")
    result += verify_pair(run, dest / "run_snapshot", "run_snapshot")
    result += metadata
    # Manifests live ONLY on Research Filestore, never on Scratch.
    manifest = dest / "manifest_sha256.tsv"
    manifest.write_text(
        "sha256_or_symlink\tpath_relative_to_site_case\n"
        + "".join(f"{digest}\t{path}\n" for digest, path in sorted(result)),
        encoding="utf-8",
    )
    receipt = {
        "site": site, "case": case_name(site), "model_years": 1000,
        "first_model_year": START[site],
        "last_model_year": START[site] + 999,
        "verification_utc": datetime.now(timezone.utc).isoformat(),
        "verified_entries": len(result),
        "source_archive": str(archive),
        "source_run": str(run),
        "source_case": str(case),
        "destination": str(dest),
        "scratch_deleted": False,
        "convergence_assessed": False,
    }
    (dest / "verification_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[VERIFIED] {site}: {len(result)} files/links checked; "
          f"manifest={manifest}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "copy", "verify"))
    parser.add_argument("--batch", required=True, choices=list(BATCHES))
    parser.add_argument("--sites", nargs="+", default=None)
    args = parser.parse_args()
    global BATCH, START, DEST
    BATCH = args.batch
    START = BATCHES[BATCH]
    DEST = DEST_BASE / BATCH
    selected = list(dict.fromkeys(args.sites if args.sites is not None else START))
    unknown = [site for site in selected if site not in START]
    if unknown:
        parser.error("Unknown site(s) for " + BATCH + ": " + ", ".join(unknown))
    print("Research Filestore destination:", DEST, flush=True)
    for site in selected:
        validate_history(site)
    if args.mode == "inspect":
        print("INSPECT ONLY: no file modifications", flush=True)
        return
    if args.mode == "copy":
        ensure_safe_to_copy(selected)
        for site in selected:
            archive, run, case, dest = paths(site)
            print(f"\nCOPY {site}: complete archive and run; CIME metadata only",
                  flush=True)
            copy_dir(archive, dest / "archive")
            copy_dir(run, dest / "run_snapshot")
            snapshot_case(case, dest / "case_snapshot")
            verify_site(site)
    else:
        for site in selected:
            verify_site(site)
    print("\nALL SELECTED SITES VERIFIED. Originals remain on Scratch.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

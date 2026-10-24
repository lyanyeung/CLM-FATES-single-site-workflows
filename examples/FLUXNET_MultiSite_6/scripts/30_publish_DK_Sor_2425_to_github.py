#!/usr/bin/env python3
"""Publish the validated DK-Sor 2425-year convergence snapshot to GitHub.

Only uploads explicitly allowlisted derived PNG, CSV, JSON, and Markdown files.
The original EC/forcing input, case, history NetCDF, and restart are read-only.
Requires a successful Stage 29 run, and preserves other sites' snapshots.

Examples on IRIDIS6 (no local git pull needed):
    python3 -B ~/DK_Sor_2425_publisher.py --dry-run
    python3 -B ~/DK_Sor_2425_publisher.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path.home() / "CLM-FATES-single-site-workflows"
RFS_ROOT = Path("/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots")
SNAPSHOT = "20261024T100510Z_DK_Sor_2425_archive_snapshot"
SITE = "DK-Sor"
PUBLISH_PARENT = Path("examples/FLUXNET_MultiSite_6/figures/convergence_snapshots")
SITE_NAMES = [
    "DK-Sor_01_carbon_pools_annual_mean.png",
    "DK-Sor_02_carbon_pools_last250years.png",
    "DK-Sor_04_FATES_PFT_VEGC_evolution.png",
    "DK-Sor_GPP_NEE_monthly_overview.png",
    "DK-Sor_carbon_annual_means.csv",
    "DK-Sor_convergence_metrics.csv",
    "DK-Sor_FATES_PFT_VEGC_annual_pct.csv",
    "DK-Sor_monthly_FATES_vs_EC.csv",
    "DK-Sor_monthly_metrics.csv",
    "DK-Sor_metadata.json",
    "DK-Sor_2425yr_REPORT.md",
]
TOP_NAMES = ["six_site_latest_checkpoint_convergence_summary.csv", "RUN_INFO.json"]
EXTENSIONS = {".png", ".csv", ".json", ".md"}
MAX_FILE_BYTES = 25 * 1024 * 1024


def run(*cmd, cwd=None):
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                            text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            "Command failed: " + " ".join(map(str, cmd)) +
            "\n" + (result.stdout + "\n" + result.stderr)[-3000:]
        )
    return result.stdout.strip()


def safe_source(path: Path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing or symlink input: " + str(path))
    size = path.stat().st_size
    if not 0 < size <= MAX_FILE_BYTES or path.suffix.lower() not in EXTENSIONS:
        raise ValueError("Empty, oversized, or forbidden file: " + str(path))
    if path.suffix == ".png":
        with path.open("rb") as file:
            if file.read(8) != b"\x89PNG\r\n\x1a\n":
                raise ValueError("Invalid PNG magic: " + str(path))


def validate_snapshot(snapshot: Path):
    if snapshot != RFS_ROOT / SNAPSHOT or not snapshot.is_dir() or snapshot.is_symlink():
        raise ValueError("Refusing unexpected snapshot path " + str(snapshot))
    site_dir = snapshot / SITE
    if site_dir.is_symlink() or not site_dir.is_dir():
        raise ValueError("Missing DK-Sor directory")
    files = [snapshot / name for name in TOP_NAMES]
    files += [site_dir / name for name in SITE_NAMES]
    for path in files:
        safe_source(path)

    with (snapshot / TOP_NAMES[0]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1 or rows[0].get("Site") != SITE or rows[0].get("Status") != "OK":
        raise ValueError("Snapshot site summary is not exactly one DK-Sor Status=OK")
    if (rows[0].get("ArchivedYears") != "2425" or
            rows[0].get("MissingHistYears") != "0" or
            rows[0].get("LastCheckpointElapsedYears") != "2425"):
        raise ValueError("2425-year exact-coverage gate failed")

    meta = json.loads((site_dir / "DK-Sor_metadata.json").read_text(encoding="utf-8"))
    expected = {
        "site": SITE, "case": "DK-Sor_FATES_SPINUP500",
        "source_model_years": [1996, 4420],
        "archived_history_count": 2425,
        "last_three_component_checkpoint_modelyear": 4421,
        "missing_years_total": 0, "flux_error": None,
    }
    for key, val in expected.items():
        if meta.get(key) != val:
            raise ValueError(f"DK-Sor metadata mismatch {key}: {meta.get(key)!r} != {val!r}")
    if meta.get("flux", {}).get("cycle_model_years") != [4374, 4402]:
        raise ValueError("EC comparison did not use the last complete 29-year cycle")

    with (snapshot / "RUN_INFO.json").open(encoding="utf-8") as handle:
        info = json.load(handle)
    if info.get("requested_sites") != [SITE] or len(info.get("results", [])) != 1:
        raise ValueError("RUN_INFO must have exactly DK-Sor")
    if info["results"][0].get("Status") != "OK":
        raise ValueError("RUN_INFO site result is not successful")

    with (site_dir / "DK-Sor_monthly_metrics.csv").open(newline="", encoding="utf-8") as handle:
        scores = list(csv.DictReader(handle))
    if {r.get("Flux") for r in scores} != {"GPP", "NEE"}:
        raise ValueError("Missing GPP/NEE scores")
    if any(r.get("N") != "340" for r in scores):
        raise ValueError("Unexpected paired-month counts")
    print(f"VALIDATION PASS: {len(files)} allowlisted derived files")
    print("Snapshot:", snapshot)
    print("Destination:", PUBLISH_PARENT / SNAPSHOT)
    return files


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def publish(files, snapshot, dry_run):
    for source in files:
        print(f"  {source.relative_to(snapshot)} | {source.stat().st_size:,} bytes | SHA256 {checksum(source)}")
    if dry_run:
        print("DRY RUN PASS: no Git changes and no file deletions")
        return
    remote = run("git", "-C", str(REPO), "remote", "get-url", "origin")
    if "lyanyeung/CLM-FATES-single-site-workflows" not in remote:
        raise ValueError("Unexpected origin remote: " + remote)
    with tempfile.TemporaryDirectory(prefix="dk_sor_2425_publish_", dir=str(Path.home())) as tmp:
        clone = Path(tmp) / "checkout"
        run("git", "clone", "--depth", "1", "--single-branch", "--branch",
            "main", remote, str(clone))
        target = clone / PUBLISH_PARENT / SNAPSHOT
        if target.exists():
            raise FileExistsError("Refusing to overwrite GitHub snapshot " + str(target))
        staged = []
        for source in files:
            relative = source.relative_to(snapshot)
            dest = target / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            staged.append(str(PUBLISH_PARENT / SNAPSHOT / relative))
        hashes = "\n".join(
            checksum(source) + "  " + source.relative_to(snapshot).as_posix()
            for source in files
        ) + "\n"
        manifest = target / "SHA256SUMS.txt"
        manifest.write_text(hashes, encoding="utf-8")
        staged.append(str(PUBLISH_PARENT / SNAPSHOT / "SHA256SUMS.txt"))
        run("git", "add", "-f", "--", *staged, cwd=clone)
        actual = set(run("git", "diff", "--cached", "--name-only", cwd=clone).splitlines())
        if actual != set(staged):
            raise ValueError(f"Unexpected Git staging: {sorted(actual ^ set(staged))}")
        run("git", "-c", "user.name=IRIDIS6 CLM-FATES",
            "-c", "user.email=lyanyeung@users.noreply.github.com",
            "commit", "-m", f"Publish DK-Sor 2425-year convergence and EC comparison {SNAPSHOT}",
            cwd=clone)
        run("git", "push", "origin", "HEAD:main", cwd=clone)
        print("GITHUB PUBLISH SUCCESS")
        print("Commit:", run("git", "rev-parse", "HEAD", cwd=clone))
        print("Published:", f"https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/{PUBLISH_PARENT}/{SNAPSHOT}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    snapshot = RFS_ROOT / SNAPSHOT
    files = validate_snapshot(snapshot)
    publish(files, snapshot, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

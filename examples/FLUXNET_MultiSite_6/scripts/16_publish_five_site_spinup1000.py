#!/usr/bin/env python3
"""Publish reviewed 1000-year five-site figures and summary statistics.

Run on IRIDIS6 where ~/six_site_spinup1000_final exists.
Publishes model diagnostics, NOT raw/derived tower time series, NetCDFs or logs.
Requires an authenticated git remote with permission to push to main.
"""
from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path

SITES = ("RU-Fyo", "DE-Tha", "DK-Sor", "NL-Loo", "IL-Yat")
ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples" / "FLUXNET_MultiSite_6"
SOURCE = Path.home() / "six_site_spinup1000_final"
DEST = EXAMPLE / "figures" / "spinup1000_final"
START = "<!-- SPINUP1000_FINAL_RESULTS_START -->"
END = "<!-- SPINUP1000_FINAL_RESULTS_END -->"


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          check=True, text=True, capture_output=True).stdout.strip()


def fail(msg):
    raise SystemExit("ERROR: " + msg)


def csv_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fmt(number):
    try:
        return f"{float(number):.3f}"
    except (ValueError, TypeError):
        return "N/A"


def main():
    if not (ROOT / ".git").exists():
        fail("Repository checkout not found: " + str(ROOT))
    if git("branch", "--show-current") != "main":
        fail("Switch to the main branch before publishing.")
    remote = git("remote", "get-url", "origin").lower().removesuffix(".git")
    if not (remote.endswith("github.com/lyanyeung/clm-fates-single-site-workflows")
            or remote.endswith("github.com:lyanyeung/clm-fates-single-site-workflows")):
        fail("Unexpected origin remote: " + remote)
    if git("status", "--porcelain", "--untracked-files=no"):
        fail("Tracked files have local modifications; save/review them before publishing.")
    if not SOURCE.is_dir():
        fail("Missing result directory " + str(SOURCE))

    overview_path = SOURCE / "five_site_spinup1000_summary.csv"
    if not overview_path.is_file():
        fail("Missing summary: " + str(overview_path))
    overview = {r["Site"]: r for r in csv_rows(overview_path)}
    if set(overview) != set(SITES) or any(
        overview[s].get("Status") != "OK" or
        overview[s].get("ArchiveYears") != "1000" for s in SITES
    ):
        fail("Site summary must contain exactly 5 OK sites, each with 1000 archived years.")

    files = {}
    for site in SITES:
        base = SOURCE / site
        names = [
            f"{site}_01_carbon_pools_annual_mean.png",
            f"{site}_02_carbon_pools_last250years.png",
            f"{site}_GPP_NEE_monthly_overview.png",
            f"{site}_carbon_annual_means.csv",
            f"{site}_convergence_metrics.csv",
            f"{site}_monthly_metrics.csv",
        ]
        for name in names:
            p = base / name
            if not p.is_file() or p.stat().st_size == 0:
                fail(f"Missing or empty: {p}")
            files[f"{site}/{name}"] = p
        converg = csv_rows(base / f"{site}_convergence_metrics.csv")
        monthly = csv_rows(base / f"{site}_monthly_metrics.csv")
        if not converg or {r.get("Flux") for r in monthly} != {"GPP", "NEE"}:
            fail(f"Incomplete statistics for {site}")

    for name in ("14_plot_five_site_spinup1000.py",
                 "15_submit_five_site_spinup1000_plots.sh"):
        src = Path.home() / name
        if not src.is_file():
            fail(f"Missing reproducibility script: {src}")

    # Keep the entire publication fast-forwarded to the current remote main.
    print("Pulling latest main (fast-forward only)...", flush=True)
    git("pull", "--ff-only", "origin", "main")
    DEST.mkdir(parents=True, exist_ok=True)
    staged = []
    for rel, src in files.items():
        dst = DEST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        staged.append(dst.relative_to(ROOT).as_posix())

    summary_dst = DEST / "five_site_spinup1000_summary.csv"
    # Remove cluster-specific absolute paths from the public summary.
    cols = ["Site", "Status", "ArchiveYears", "ModelCycleStart", "ModelCycleEnd",
            "GPP_monthly_R2", "NEE_monthly_R2"]
    with summary_dst.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=cols)
        writer.writeheader()
        for site in SITES:
            writer.writerow({col: overview[site][col] for col in cols})
    staged.append(summary_dst.relative_to(ROOT).as_posix())

    for name in ("14_plot_five_site_spinup1000.py",
                 "15_submit_five_site_spinup1000_plots.sh"):
        dst = EXAMPLE / "scripts" / name
        shutil.copy2(Path.home() / name, dst)
        if name.endswith(".sh"):
            # IRIDIS6 requires an explicit --nodes Slurm directive.
            body = dst.read_text()
            if "#SBATCH --nodes=" not in body:
                body = body.replace("#!/usr/bin/env bash\n",
                                    "#!/usr/bin/env bash\n#SBATCH --nodes=1\n", 1)
                dst.write_text(body)
        staged.append(dst.relative_to(ROOT).as_posix())

    block = [
        START,
        "",
        "## Five-site 1000-year spin-up results (18 October 2026)",
        "",
        "Five sites successfully archived **1000 continuous annual h0a files**",
        "and completed read-only carbon and flux diagnostics. **DE-Hai is",
        "excluded** from this release. These are diagnostics, not evidence",
        "that any site has reached carbon-pool or demographic equilibrium.",
        "",
        "All model cases retain the original \`<SITE>_FATES_SPINUP500\` name",
        "despite continuing from 500 to 1000 elapsed model years.",
        "",
        "| Site | Latest complete model forcing cycle | Monthly GPP R² | Monthly NEE R² |",
        "|---|---|---:|---:|",
    ]
    for site in SITES:
        r = overview[site]
        block.append(f"| {site} | {r['ModelCycleStart']}–{r['ModelCycleEnd']} "
                     f"| {fmt(r['GPP_monthly_R2'])} | {fmt(r['NEE_monthly_R2'])} |")
    block += [
        "",
        "GPP and NEE comparisons use the last **complete, phase-aligned** forcing",
        "cycle mapped back onto the original EC observation years; they do",
        "not necessarily cover the simulation's final 100 model years.",
        "",
        "Convergence CSVs report last-30/100-year trends, paired forcing-cycle",
        "changes, and phase-aligned 500-vs-1000-year cycle means. These",
        "metrics are not automatic convergence pass/fail thresholds.",
        "",
        "[Five-site numerical summary](figures/spinup1000_final/five_site_spinup1000_summary.csv)",
        " · [Reproducible Python analysis](scripts/14_plot_five_site_spinup1000.py)",
        " · [IRIDIS6 Slurm job](scripts/15_submit_five_site_spinup1000_plots.sh)",
        " · [Result publishing script](scripts/16_publish_five_site_spinup1000.py)",
        "",
    ]
    for site in SITES:
        prefix = f"figures/spinup1000_final/{site}/{site}"
        block += [
            f"### {site} — 1000 years",
            "",
            "**Carbon pools, years 1–1000**",
            "",
            f"![{site} 1000-year carbon pools]({prefix}_01_carbon_pools_annual_mean.png)",
            "",
            "**Carbon pools, last 250 years**",
            "",
            f"![{site} last 250 years]({prefix}_02_carbon_pools_last250years.png)",
            "",
            "**Latest complete forcing-cycle GPP/NEE versus EC**",
            "",
            f"![{site} GPP NEE monthly comparison]({prefix}_GPP_NEE_monthly_overview.png)",
            "",
            f"[Carbon annual means]({prefix}_carbon_annual_means.csv) · "
            f"[Convergence statistics]({prefix}_convergence_metrics.csv) · "
            f"[Monthly GPP/NEE skill statistics]({prefix}_monthly_metrics.csv)",
            "",
        ]
    block += [
        "The published CSV files contain simulated carbon pools and",
        "aggregate diagnostics. Raw EC time series, paired monthly EC/model",
        "flux tables, original flux packages, NetCDF history and restarts,",
        "cluster paths, and job logs are deliberately excluded.",
        "",
        END,
    ]
    readme = EXAMPLE / "README.md"
    original = readme.read_text(encoding="utf-8")
    section = "\n".join(block)
    if START in original or END in original:
        if original.count(START) != 1 or original.count(END) != 1:
            fail("Ambiguous 1000-year README markers; inspect README manually.")
        a = original.index(START)
        b = original.index(END, a) + len(END)
        updated = original[:a] + section + original[b:]
    else:
        updated = original.rstrip() + "\n\n" + section + "\n"
    readme.write_text(updated, encoding="utf-8")
    staged.append(readme.relative_to(ROOT).as_posix())

    # The repository intentionally ignores *.png and *.csv: force-add only
    # this explicit allowlist, never force-add a directory or raw observations.
    for rel in staged:
        git("add", "-f", "--", rel)
    changed = git("diff", "--cached", "--name-only")
    if not changed:
        print("No changes to publish.")
        return
    print("\nFiles staged for publication:\n" + changed, flush=True)
    git("commit", "-m", "Add five-site 1000-year spin-up diagnostics and figures")
    print("\nPushing to origin/main...", flush=True)
    git("push", "origin", "main")
    print("\nSUCCESS: https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/examples/FLUXNET_MultiSite_6")
    print("Commit: " + git("rev-parse", "--short", "HEAD"))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Git command failed: {exc.cmd}\n{exc.stderr or exc.stdout}", file=sys.stderr)
        sys.exit(exc.returncode)

#!/usr/bin/env python3
"""Prepare and stage seven-site 500-year figures, metrics and README on IRIDIS6.

Only publishes selected derived products. Never includes downloaded EC data,
full model NetCDF, restarts, private metadata, raw paired flux CSVs or logs.
Does not run CIME or push to GitHub automatically.
"""
from __future__ import annotations
import csv
import json
import shutil
import subprocess
from pathlib import Path

HOME = Path.home()
REPO = HOME / "CLM-FATES-single-site-workflows"
BASE = REPO / "examples/FLUXNET_MultiSite_8"
SOURCE = HOME / "seven_site_spinup500_final"
DEST = BASE / "figures/spinup500_final"
SITES = ("CZ-BK1", "IT-Ren", "FR-FBn", "DE-Hzd", "CH-Dav", "BE-Vie", "IT-Lav")
BEGIN = "<!-- EIGHT_SITE_SPINUP500_RESULTS_START -->"
END = "<!-- EIGHT_SITE_SPINUP500_RESULTS_END -->"


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True,
                          capture_output=True, text=True).stdout


def read_scores(path):
    result = {}
    with path.open(newline="") as stream:
        for record in csv.DictReader(stream):
            if record.get("Flux") in ("GPP", "NEE"):
                try:
                    result[record["Flux"]] = f"{float(record['R2']):.3f}"
                except (KeyError, TypeError, ValueError):
                    result[record["Flux"]] = "NA"
    return result


def main():
    if not (REPO / ".git").exists() or not SOURCE.is_dir():
        raise SystemExit("Missing repository or ~/seven_site_spinup500_final")
    if git("branch", "--show-current").strip() != "main":
        raise SystemExit("Use main branch")
    if git("diff", "--cached", "--name-only").strip():
        raise SystemExit("Commit or unstage your existing staged changes first")
    readme = BASE / "README.md"
    if git("diff", "--", str(readme.relative_to(REPO))).strip():
        raise SystemExit("README already locally modified; inspect it first")

    staged = []
    rows = []
    published = []
    for site in SITES:
        directory = SOURCE / site
        meta_path = directory / f"{site}_metadata.json"
        carbon = [f"{site}_01_carbon_pools_annual_mean.png",
                  f"{site}_02_carbon_pools_last100years.png",
                  f"{site}_carbon_annual_means.csv",
                  f"{site}_convergence_metrics.csv"]
        if not meta_path.is_file():
            print(f"SKIP {site}: no plotting metadata")
            rows.append((site, "Not verified", "—", "—", "—"))
            continue
        info = json.loads(meta_path.read_text())
        if info.get("archive_years_verified") != 500 or any(
            not (directory / filename).is_file() for filename in carbon
        ):
            print(f"SKIP {site}: missing 500-year archive verification or output")
            rows.append((site, "Not verified", "—", "—", "—"))
            continue
        ec = [f"{site}_GPP_NEE_monthly_overview.png",
              f"{site}_monthly_metrics.csv"]
        ec_ok = info.get("status") == "OK" and all(
            (directory / filename).is_file() for filename in ec)
        target_dir = DEST / site
        target_dir.mkdir(parents=True, exist_ok=True)
        for filename in carbon + (ec if ec_ok else []):
            dest_path = target_dir / filename
            shutil.copy2(directory / filename, dest_path)
            staged.append(dest_path)
        scores = read_scores(directory / ec[1]) if ec_ok else {}
        cycle = info.get("last_complete_model_cycle", ["?", "?"])
        rows.append((site, "500 verified years", f"{cycle[0]}–{cycle[1]}",
                     scores.get("GPP", "—"), scores.get("NEE", "—")))
        published.append((site, ec_ok))
        print(f"READY {site}: carbon plots, EC comparison={ec_ok}")
    if not published:
        raise SystemExit("No verified plots found; nothing was staged")

    summary = DEST / "seven_site_spinup500_summary.csv"
    with summary.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("Site", "ArchiveStatus", "LatestCompleteModelCycle",
                         "MonthlyGPP_R2", "MonthlyNEE_R2"))
        writer.writerows(rows)
    staged.append(summary)

    lines = [
        BEGIN,
        "## Stage 09 — Seven-site 500-year spin-up diagnostics (18 October 2026)",
        "",
        "This seven-site subset uses the original SITE_FATES_SPINUP500 cases.",
        "**FR-Hes is excluded** until its 500-year completion is verified.",
        "Every published carbon diagnostic was made from 500 consecutive annual",
        "h0a history files. Finishing 500 model years does NOT imply convergence.",
        "",
        "| Site | Carbon archive | Last complete model forcing cycle | GPP monthly R² | NEE monthly R² |",
        "|---|---|---|---:|---:|",
    ]
    lines.extend(f"| {site} | {status} | {cycle} | {gpp} | {nee} |"
                 for site, status, cycle, gpp, nee in rows)
    lines.extend([
        "",
        "Carbon pool diagnostics reuse the",
        "[six-site plotting reference](../FLUXNET_MultiSite_6/scripts/14_plot_five_site_spinup1000.py).",
        "Fluxes use the last complete, phase-aligned forcing cycle mapped to",
        "the original EC years: GPP=FATES_GPP, NEE=-FATES_NEP (EC NEE=NEE_VUT_REF).",
        "R² is 1 - SSE/SST (negative values are possible).",
        "",
        "Code: [plotter](scripts/18_plot_seven_site_spinup500.py),",
        "[Slurm job](scripts/19_submit_seven_site_spinup500.sbatch),",
        "[publishing utility](scripts/20_publish_seven_site_spinup500.py).",
        "[Derived result summary](figures/spinup500_final/seven_site_spinup500_summary.csv).",
        "",
        "Only model-derived figures and limited carbon/skill CSVs are committed;",
        "downloaded flux records, raw paired tower data, model archives,",
        "restart data and local machine paths are not redistributed.",
        "",
    ])
    for site, ec_ok in published:
        directory = f"figures/spinup500_final/{site}"
        lines += [
            f"### {site}", "",
            f"![{site} carbon pools]({directory}/{site}_01_carbon_pools_annual_mean.png)", "",
            f"[Last 100 years]({directory}/{site}_02_carbon_pools_last100years.png)",
            f" · [Convergence metrics]({directory}/{site}_convergence_metrics.csv)", "",
        ]
        if ec_ok:
            lines += [
                f"![{site} monthly GPP and NEE]({directory}/{site}_GPP_NEE_monthly_overview.png)",
                "", f"[Monthly metrics]({directory}/{site}_monthly_metrics.csv)", ""
            ]
        else:
            lines += ["*EC comparison not available for this site.*", ""]
    lines += [
        "Convergence requires separate assessment of slow carbon pools,",
        "the aligned forcing-cycle changes, FATES demography and input QC.",
        END
    ]
    section = "\n".join(lines)
    original = readme.read_text()
    if BEGIN in original:
        prefix, following = original.split(BEGIN, 1)
        if END not in following:
            raise SystemExit("README result markers incomplete: not overwriting")
        _, suffix = following.split(END, 1)
        updated = prefix.rstrip() + "\n\n" + section + suffix
    else:
        updated = original.rstrip() + "\n\n" + section + "\n"
    readme.write_text(updated)
    staged.append(readme)
    for name in ("18_plot_seven_site_spinup500.py",
                 "19_submit_seven_site_spinup500.sbatch",
                 "20_publish_seven_site_spinup500.py",
                 "README_seven_site_spinup500.txt"):
        file = BASE / "scripts" / name
        if file.is_file():
            staged.append(file)
    git("add", "-f", "--", *(str(file.relative_to(REPO)) for file in staged))
    print("\nSTAGED CHANGES:\n" + git("diff", "--cached", "--stat"))
    print('Run: git commit -m "Publish seven-site 500-year spin-up diagnostics"')
    print('Then: git push origin main')


if __name__ == "__main__":
    main()

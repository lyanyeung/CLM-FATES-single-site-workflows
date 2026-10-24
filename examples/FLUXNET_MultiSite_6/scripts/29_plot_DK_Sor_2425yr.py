#!/usr/bin/env python3
"""Read-only DK-Sor 2425-year convergence and original EC GPP/NEE analysis.

Reuses repository stage 27 unchanged. Validates the exact annual-history range
1996-4420 and (when present) the coordinated three-component 4421 restart.
Does not submit jobs, edit model files, or change original EC data.

Use on IRIDIS6:
  python3 -B examples/FLUXNET_MultiSite_6/scripts/29_plot_DK_Sor_2425yr.py --check-only
  python3 -B examples/FLUXNET_MultiSite_6/scripts/29_plot_DK_Sor_2425yr.py
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SITE = "DK-Sor"
CASE = "DK-Sor_FATES_SPINUP500"
START = 1996
ELAPSED = 2425
CAP = START + ELAPSED  # checkpoint 4421, last archived model year 4420
FORCING = 29
CYCLE_START = START + ((ELAPSED // FORCING) - 1) * FORCING
CYCLE_END = CYCLE_START + FORCING - 1
RFS_PARENT = Path("/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots")


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(value):
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "N/A"


def preflight(repo, stage):
    spec = importlib.util.spec_from_file_location("existing_stage27_dk_sor", stage)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    found, _ = module.index_history(SITE, CASE)
    actual = set(found)
    expected = set(range(START, CAP))
    missing = sorted(expected - actual)
    unexpected = sorted(y for y in actual if y >= CAP)
    checkpoint = module.coordinated_checkpoint(CASE)

    print(f"DK-Sor archived h0a: {len(actual)} unique years")
    print(f"Expected: model years {START}-{CAP - 1} ({ELAPSED} elapsed)")
    print(f"Last complete forcing cycle: {CYCLE_START}-{CYCLE_END}")
    print(f"Original EC years: 1996-2024; unused final model tail: {CYCLE_END + 1}-{CAP - 1}")
    print(f"Coordinated Scratch restart: {checkpoint}")
    if missing:
        raise RuntimeError(f"Missing {len(missing)} h0a model years, first 20: {missing[:20]}")
    if unexpected:
        raise RuntimeError(f"Found model years after requested 2425-year limit: {unexpected[:20]}; "
                           "refusing to silently analyse a different horizon.")
    if checkpoint is not None and checkpoint[0] != CAP:
        raise RuntimeError(f"Latest coordinated Scratch restart is {checkpoint[0]}, "
                           f"but requested 2425-year checkpoint is {CAP}.")
    if checkpoint is None:
        print("WARNING: no three-component Scratch restart found; h0a coverage alone "
              "does not prove the 2425-year restart is usable.")
    if len(actual) != ELAPSED:
        raise RuntimeError("Unexpected unique h0a inventory size")
    print("PRE-FLIGHT PASS: all 2425 annual histories present (read only).")
    return checkpoint


def create_report(dest, checkpoint):
    site_dir = dest / SITE
    summary = csv_rows(dest / "six_site_latest_checkpoint_convergence_summary.csv")
    if len(summary) != 1 or summary[0]["Site"] != SITE or summary[0]["Status"] != "OK":
        raise RuntimeError(f"DK-Sor plotting/EC comparison did not fully succeed: {summary}")
    meta = json.loads((site_dir / f"{SITE}_metadata.json").read_text())
    flux_years = meta.get("flux", {}).get("cycle_model_years")
    if flux_years != [CYCLE_START, CYCLE_END]:
        raise RuntimeError(f"Incorrect EC alignment: {flux_years}, expected "
                           f"{[CYCLE_START, CYCLE_END]}")
    if meta.get("archived_history_count") != ELAPSED or meta.get("missing_years_total") != 0:
        raise RuntimeError("Stage 27 analysed a different or incomplete history inventory")
    conv = csv_rows(site_dir / f"{SITE}_convergence_metrics.csv")
    monthly = csv_rows(site_dir / f"{SITE}_monthly_metrics.csv")
    selected = {"TOTECOSYSC", "TOTSOMC", "TOTLITC", "FATES_VEGC",
                "FATES_STOREC", "FATES_STRUCTC"}
    lines = [
        "# DK-Sor — 2425-year spin-up diagnostics",
        "",
        "Generated from original stage-27 repository analysis on archived annual h0a NetCDF.",
        "No model or EC source data modified.",
        "",
        f"- Elapsed spin-up: {ELAPSED} years; annual model histories: {START}-{CAP - 1}",
        f"- Latest available coordinated three-component Scratch checkpoint: "
        f"{checkpoint[0] if checkpoint else 'not verified on Scratch'}",
        f"- Last **complete** 29-year forcing cycle: model {CYCLE_START}-{CYCLE_END}, "
        "mapped onto original EC years 1996-2024",
        f"- Incomplete tail excluded from EC comparison: model {CYCLE_END + 1}-{CAP - 1}",
        "- Model flux definitions: GPP = FATES_GPP; NEE = -FATES_NEP",
        "- EC definitions: GPP_DT_VUT_REF; NEE_VUT_REF",
        "- EC comparison unit: g C m^-2 d^-1; model vs EC matched monthly mean values",
        "",
        "## Carbon-pool trends and phase-aligned convergence",
        "",
        "| Variable | Last 100y trend (%) | Last 250y trend (%) | Adjacent-cycle mean absolute change (%) | Stage-27 1% exploratory screen |",
        "|---|---:|---:|---:|---|",
    ]
    for row in conv:
        if row["Variable"] not in selected:
            continue
        lines.append(
            f"| {row['Variable']} | {fmt(row.get('Last100y_trend_pct'))} | "
            f"{fmt(row.get('Last250y_trend_pct'))} | "
            f"{fmt(row.get('AlignedCycleMeanAbsChange_pct'))} | "
            f"{row.get('Exploratory_1pct_100yr_and_cycle_screen', 'N/A')} |"
        )
    lines += [
        "",
        "Stage-27 thresholds are project-specific screening criteria, not a scientific "
        "certificate of full ecosystem equilibrium. Always inspect the trajectories.",
        "",
        "## Last full cycle vs original EC tower",
        "",
        "| Flux | Matched months | Correlation (R) | Skill R2 | RMSE | Model minus EC bias |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in monthly:
        lines.append(
            f"| {row.get('Flux', 'unknown')} | {row.get('N', 'N/A')} | "
            f"{fmt(row.get('R'))} | {fmt(row.get('R2'))} | "
            f"{fmt(row.get('RMSE'))} | {fmt(row.get('Bias'))} |"
        )
    lines += [
        "",
        "RMSE and bias are in g C m^-2 d^-1. R2 = 1 - SSE/SST (not R squared).",
        "Results reflect the original dynamic-competition Full FATES configuration; "
        "a good flux fit does not independently establish realistic PFT, soil or "
        "carbon-pool equilibrium.",
        "",
        "## Figures",
        "",
        "- DK-Sor_01_carbon_pools_annual_mean.png",
        "- DK-Sor_02_carbon_pools_last250years.png",
        "- DK-Sor_04_FATES_PFT_VEGC_evolution.png",
        "- DK-Sor_GPP_NEE_monthly_overview.png",
        "",
        "Full source provenance and quantitative tables are in the companion "
        "metadata.json and CSV files.",
        "",
    ]
    out = site_dir / "DK-Sor_2425yr_REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"REPORT: {out}")
    print(f"FIGURES: {site_dir}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path,
                        default=Path.home() / "CLM-FATES-single-site-workflows")
    parser.add_argument("--check-only", action="store_true",
                        help="Inspect NetCDF archive/checkpoint only. Do not generate outputs.")
    args = parser.parse_args()
    repo = args.repo.resolve()
    # Load the exact fetched GitHub stage-27 file without touching a potentially
    # conflicted local repository worktree. Stage 27 itself pins its helpers.
    rel = "examples/FLUXNET_MultiSite_6/scripts/27_plot_six_site_latest_archived_convergence_to_RFS.py"
    with tempfile.TemporaryDirectory(prefix="dk_sor_stage27_") as temp:
        stage = Path(temp) / "27_plot_six_site_latest_archived_convergence_to_RFS.py"
        with stage.open("w", encoding="utf-8") as output:
            subprocess.run(["git", "-C", str(repo), "show", "origin/main:" + rel],
                           check=True, stdout=output)
        checkpoint = preflight(repo, stage)
        if args.check_only:
            return 0
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = RFS_PARENT / (stamp + "_DK_Sor_2425_archive_snapshot")
        cmd = [sys.executable, "-B", str(stage), "--repo", str(repo),
               "--sites", SITE, "--output-root", str(dest)]
        print("Executing the original stage-27 science pipeline (DK-Sor only)", flush=True)
        subprocess.run(cmd, check=True)
        create_report(dest, checkpoint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only diagnostics for nine completed 1000-year FLUXNET_MultiSite_11 cases.

Adapts the *actual* FLUXNET_MultiSite_6 diagnostics by importing their
reference implementations, not by changing any simulation, restart or input.
Needs a local clone of lyanyeung/CLM-FATES-single-site-workflows and
clm_fates_env (netCDF4, numpy, pandas, matplotlib).

Output MUST be explicitly selected on writable Research Filestore (or non-scratch staging):
  <output-root>/<site>/
  <site>_01_carbon_pools_annual_mean.png
  <site>_02_carbon_pools_last250years.png
  <site>_GPP_NEE_monthly_overview.png [if EC source is available]
  <site>_carbon_annual_means.csv
  <site>_convergence_metrics.csv
  <site>_monthly_FATES_vs_EC.csv [if EC source is available]
  <site>_monthly_metrics.csv [if EC source is available]
  <site>_metadata.json
  <output-root>/nine_site_spinup1000_summary.csv

IT-Noe and CH-Aws are excluded (not completed in the 20 Oct 2026 audit).
Require precisely 1000 continuous annual h0a files per named site.
This script reads input under scratch but NEVER creates files there.
Finishing 1000 years alone is NOT proof of ecological convergence.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Site forcing periods are sourced from FLUXNET_MultiSite_8's actual run script.
SITES = {
    "BE-Bra": (1996, 2025),
    "FR-Fon": (2005, 2025),
    "GL-ZaH": (2000, 2025),
    "AT-Neu": (2002, 2020),
    "FI-Sod": (2001, 2025),
    "CH-Cha": (2005, 2024),
    "CH-Fru": (2005, 2024),
    "CH-Lae": (2004, 2024),
    "CZ-Stn": (2010, 2024),
}
YEARS = 1000


def load_script(path: Path, module_name: str):
    if not path.is_file():
        raise FileNotFoundError(f"Reference script not found: {path}; git pull on IRIDIS6")
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def locate_ec_sources(forcing: Path, preference: str, override: str | None):
    """Discover original HH tower carbon flux files from raw* directories.

    Stage03's real eleven-site policy reads forcing/raw* (not forcing/raw
    exclusively). Meteorological merge candidates and ERA are NOT EC data.
    Priority for overlapping valid days is ICOS, ICOSETC, EUF, then FLX.
    Missing individual daily values may fall back to a lower-priority source.
    """
    def inspect(path: Path):
        with path.open("r", encoding="latin-1", newline="") as stream:
            cols = set(next(csv.reader(stream)))
        if not {"TIMESTAMP_START", "NEE_VUT_REF"}.issubset(cols):
            return None
        gpp = preference if preference in cols else next(
            (v for v in ("GPP_DT_VUT_REF", "GPP_NT_VUT_REF") if v in cols), None
        )
        return gpp

    if override:
        chosen = Path(override).expanduser()
        if not chosen.is_file():
            raise FileNotFoundError(f"Explicit EC override not found: {chosen}")
        gpp = inspect(chosen)
        if not gpp:
            raise ValueError(f"EC override lacks TIMESTAMP_START/NEE/GPP: {chosen}")
        return [(chosen, gpp)]

    if not forcing.is_dir():
        raise FileNotFoundError(f"Missing forcing directory: {forcing}")
    rawdirs = sorted(
        p for p in forcing.iterdir()
        if p.is_dir() and p.name.lower().startswith("raw")
    )
    candidates = []
    for rawdir in rawdirs:
        for path in sorted(rawdir.rglob("*.csv")):
            upper = path.name.upper()
            if not any(label in upper for label in
                       ("FULLSET_HH", "FLUXMET_HH", "FLUXES_HH", "FLUX_HH")):
                continue
            # Never substitute ERA5, met-only merged series or flux coverage reports.
            if any(label in upper for label in ("ERA5", "ERAI", "AUX", "BIF")):
                continue
            try:
                gpp = inspect(path)
            except (OSError, UnicodeError, StopIteration):
                continue
            if not gpp:
                continue
            prefix = upper.split("_", 1)[0]
            priority = {"ICOS": 0, "ICOSETC": 1, "EUF": 2, "FLX": 3}.get(prefix, 4)
            candidates.append((priority, path, gpp))
    if not candidates:
        raise FileNotFoundError(
            f"No HH tower carbon flux CSV with NEE_VUT_REF and GPP DT/NT "
            f"under raw* directories of {forcing}; checked {len(rawdirs)} raw dirs"
        )
    # Exact duplicates are ignored; otherwise keep complementary historical
    # releases, recording their source priority in output metadata.
    seen = set()
    sources = []
    for _, path, gpp in sorted(candidates, key=lambda rec: (rec[0], str(rec[1]))):
        if path in seen:
            continue
        sources.append((path, gpp))
        seen.add(path)
    return sources


def merged_ec_daily(core, sources, first, last, min_halfhour):
    """Pair original daily tower flux products; retain missing days as missing.

    When releases overlap, use the higher-priority valid daily measurement
    for each flux. This method does not fabricate observations or fill a
    partially observed day using hourly values from unrelated releases.
    """
    combined = None
    provenance = []
    for path, gpp in sources:
        one = core.ec_daily(path, gpp, first, last, min_halfhour)
        data = one.set_index("date")[["EC_GPP", "EC_NEE"]]
        provenance.append({
            "path": str(path), "gpp_column": gpp,
            "valid_GPP_days": int(data["EC_GPP"].notna().sum()),
            "valid_NEE_days": int(data["EC_NEE"].notna().sum()),
        })
        combined = data if combined is None else combined.combine_first(data)
    if combined is None or combined.empty:
        raise ValueError("No daily tower observations overlap forcing years")
    return combined.sort_index().reset_index(), provenance


def plot_carbon(df, selected, units, site, dest, begin, end, suffix, title):
    """Same 2-column carbon panel layout as six-site spinup1000_final."""
    selected = selected[:6]
    nrow = math.ceil(len(selected) / 2)
    fig, axes = plt.subplots(nrow, 2, figsize=(16, 4 * nrow),
                             sharex=True, squeeze=False)
    x = df["SpinupYear"].to_numpy(dtype=float)
    for ax, var in zip(axes.flat, selected):
        ax.plot(x, df[var].to_numpy(dtype=float), lw=1.35)
        if begin == 1:
            ax.axvline(500, ls="--", lw=1.0, color="0.45", label="500-year checkpoint")
        ax.axvspan(900, 1000, color="0.8", alpha=0.15)
        ax.set(xlim=(begin, end), title=var)
        ax.set_ylabel(units[var]["plot_units"])
        ax.grid(alpha=0.22)
    for ax in list(axes.flat)[len(selected):]:
        ax.set_visible(False)
    for ax in axes[-1]:
        ax.set_xlabel("Spin-up year (elapsed model years)")
    fig.suptitle(f"{site} | {title}\nFinal 100 model years shaded; "
                 "year 1000 is not proof of equilibrium", fontsize=14)
    fig.tight_layout()
    path = dest / f"{site}_{suffix}.png"
    fig.savefig(path, dpi=230, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_monthly(monthly, site, cycle, forcing, dest, core):
    fig, axes = plt.subplots(2, 1, figsize=(16, 8), sharex=True)
    records = []
    for ax, flux in zip(axes, ("GPP", "NEE")):
        obs, mod = f"EC_{flux}", f"FATES_{flux}"
        score = core.metrics(monthly[obs], monthly[mod])
        records.append({"Site": site, "Scale": "monthly", "Flux": flux,
                        "ModelCycleFirst": cycle[0], "ModelCycleLast": cycle[-1],
                        "ECFirst": forcing[0], "ECLast": forcing[1], **score})
        ax.plot(monthly["date"], monthly[obs], lw=1.45, label="FLUXNET EC")
        ax.plot(monthly["date"], monthly[mod], lw=1.45, label="CLM-FATES")
        if flux == "NEE":
            ax.axhline(0, ls="--", lw=0.8, color="0.5")
        ax.set_ylabel(f"{flux} (g C m$^{{-2}}$ d$^{{-1}}$)")
        ax.set_title(f"{flux} | N={score['N']}, R²={score['R2']:.3f}, "
                     f"RMSE={score['RMSE']:.3f}")
        ax.grid(alpha=0.2)
        ax.legend(frameon=False)
    axes[-1].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[-1].set_xlim(pd.Timestamp(forcing[0], 1, 1),
                      pd.Timestamp(forcing[1] + 1, 1, 1))
    axes[-1].set_xlabel("Observed FLUXNET year (forcing chronology)")
    fig.suptitle(
        f"{site} | 1000-year spin-up: last COMPLETE forcing cycle\n"
        f"Model years {cycle[0]}–{cycle[-1]} mapped to EC years "
        f"{forcing[0]}–{forcing[1]}", fontsize=13)
    fig.tight_layout()
    path = dest / f"{site}_GPP_NEE_monthly_overview.png"
    fig.savefig(path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(records), path


def process_site(site, args, base, core):
    first, last = SITES[site]
    case = f"{site}_FATES_SPINUP500_11P"
    core.verify_stream(args.cases_root / case, first, last)
    found = core.history_index(args.archive_root, case)
    sequence = base.contiguous_found(found, first, YEARS)
    # Restrict comparison to the verified FIRST 1000 model years.
    found1000 = {year: found[year] for year in sequence}
    dest = args.output_root / site
    dest.mkdir(parents=True, exist_ok=True)
    print(f"  Verified 1000/1000 consecutive annual h0a files: "
          f"{sequence[0]}–{sequence[-1]} | archive index has {len(found)} years", flush=True)

    carbon, selected, units = base.extract_annual_carbon(found1000, sequence, site)
    carbon.to_csv(dest / f"{site}_carbon_annual_means.csv", index=False)
    metric = base.compute_convergence(carbon, selected, units, last - first + 1)
    metric.to_csv(dest / f"{site}_convergence_metrics.csv", index=False)
    plot_carbon(carbon, selected, units, site, dest, 1, 1000,
                "01_carbon_pools_annual_mean", "annual mean carbon pools, years 1–1000")
    plot_carbon(carbon, selected, units, site, dest, 751, 1000,
                "02_carbon_pools_last250years", "annual mean carbon pools, years 751–1000")

    _, model_cycle = core.latest_complete_cycle(found1000, first, last)
    print(f"  Last complete forcing cycle: model {model_cycle[0]}–{model_cycle[-1]} "
          f"<=> EC {first}–{last}", flush=True)
    status, ec_error, ec_path, gpp_col, scores = "CARBON_OK_EC_NOT_RUN", "", "", "", None
    ec_sources_used = []
    if not args.carbon_only:
        try:
            forcing = args.sites_root / site / "forcing"
            ec_sources = locate_ec_sources(
                forcing, args.gpp_preference, args.obs_csv.get(site)
            )
            ec_path = "; ".join(str(path) for path, _ in ec_sources)
            gpp_col = "; ".join(dict.fromkeys(col for _, col in ec_sources))
            print(f"  EC source count: {len(ec_sources)}; "
                  f"overlap priority is ICOS > ICOSETC > EUF > FLX", flush=True)
            for ecfile, ecol in ec_sources:
                print(f"    {ecfile} [GPP={ecol}]", flush=True)
            model = core.fates_daily([(y, found1000[y]) for y in model_cycle], first, last)
            obs, ec_sources_used = merged_ec_daily(
                core, ec_sources, first, last, args.min_halfhour
            )
            daily = model.merge(obs, on="date", how="left", validate="one_to_one")
            if len(daily) != (last - first + 1) * 365:
                raise ValueError("Model–EC mapped cycle has wrong number of noleap days")
            gpp = core.paired_monthly(daily, "EC_GPP", "FATES_GPP", args.min_days)
            nee = core.paired_monthly(daily, "EC_NEE", "FATES_NEE", args.min_days)
            monthly = gpp.merge(nee, on="date", how="outer", validate="one_to_one")
            for flux in ("GPP", "NEE"):
                n = int((monthly[f"EC_{flux}"].notna() &
                         monthly[f"FATES_{flux}"].notna()).sum())
                if n < 2:
                    raise RuntimeError(f"Insufficient paired monthly {flux}: N={n}")
            monthly.to_csv(dest / f"{site}_monthly_FATES_vs_EC.csv", index=False)
            scores, _ = plot_monthly(monthly, site, model_cycle, (first, last), dest, core)
            scores.to_csv(dest / f"{site}_monthly_metrics.csv", index=False)
            print(scores[["Flux", "N", "R2", "RMSE", "Bias"]].to_string(index=False),
                  flush=True)
            status = "OK"
        except Exception as exc:
            ec_error = f"{type(exc).__name__}: {exc}"
            status = "CARBON_OK_EC_ERROR"
            print(f"  EC comparison skipped (carbon figures retained): {ec_error}",
                  file=sys.stderr, flush=True)
    metadata = {
        "site": site, "case": case, "status": status, "ec_error": ec_error,
        "archive_years_verified": YEARS, "archive_start_end": [sequence[0], sequence[-1]],
        "forcing_first_last": [first, last], "last_complete_model_cycle":
            [model_cycle[0], model_cycle[-1]],
        "ec_csv": ec_path, "ec_gpp_column": gpp_col,
        "ec_source_daily_provenance": ec_sources_used,
        "ec_merge_policy": "ICOS > ICOSETC > EUF > FLX; valid daily values only",
        "carbon_units": units, "carbon_variables": selected,
        "flux_units": "g C m-2 d-1", "model_nee": "-FATES_NEP",
        "ec_nee": "NEE_VUT_REF", "model_gpp": "FATES_GPP",
        "sci_caveat": "1000 years does not imply carbon-pool or demographic convergence; "
                      "inspect aligned cycle metrics and long-term trends",
        "output_files": sorted(x.name for x in dest.iterdir() if x.is_file()),
    }
    (dest / f"{site}_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    report = {"Site": site, "Status": status, "ArchiveYears": YEARS,
              "ModelCycleStart": model_cycle[0], "ModelCycleEnd": model_cycle[-1],
              "ECError": ec_error, "Directory": str(dest)}
    for flux in ("GPP", "NEE"):
        report[f"{flux}_monthly_R2"] = (float(scores.loc[scores.Flux == flux, "R2"].iloc[0])
                                         if scores is not None else float("nan"))
    print("  Carbon diagnostic summary:\n" +
          metric.loc[metric.Variable.isin(["TOTECOSYSC", "TOTVEGC", "TOTSOMC",
                                          "TOTLITC", "FATES_VEGC"]),
                     ["Variable", "Last100y_relative_trend_pct_per_100y",
                      "Last_two_complete_cycles_mean_abs_change_pct"]].to_string(index=False),
          flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites", nargs="+", choices=list(SITES), default=list(SITES))
    parser.add_argument("--user", default="ly3n24")
    parser.add_argument("--repo", type=Path,
                        default=Path.home() / "CLM-FATES-single-site-workflows")
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--cases-root", type=Path)
    parser.add_argument("--sites-root", type=Path)
    parser.add_argument("--output-root", required=True, type=Path,
                        help="Required writable directory on Research Filestore; NEVER scratch")
    parser.add_argument("--preflight", action="store_true",
                        help="Read-only inventory of 1000-year h0a, stream and EC source (no output)")
    parser.add_argument("--obs-csv", nargs="*", default=[], metavar="SITE=/absolute/HH.csv")
    parser.add_argument("--gpp-preference", choices=["GPP_DT_VUT_REF", "GPP_NT_VUT_REF"],
                        default="GPP_DT_VUT_REF")
    parser.add_argument("--min-halfhour", type=int, default=40)
    parser.add_argument("--min-days", type=int, default=20)
    parser.add_argument("--carbon-only", action="store_true",
                        help="Make carbon figures without looking for FLUXNET EC files")
    args = parser.parse_args()
    if args.archive_root is None:
        args.archive_root = Path(f"/scratch/{args.user}/CTSM_FATES_OUTPUTS/archive")
    if args.cases_root is None:
        args.cases_root = Path(f"/iridisfs/scratch/{args.user}/CLM_FATES/cases")
    if args.sites_root is None:
        args.sites_root = Path(f"/iridisfs/scratch/{args.user}/CLM_FATES/sites/MY_EC_SITE")
    args.repo = args.repo.expanduser().resolve()
    for item in args.obs_csv:
        site, sep, path = item.partition("=")
        if not sep or site not in SITES or not path:
            parser.error(f"Invalid --obs-csv {item}: expected SITE=/absolute/path.csv")
    args.obs_csv = {item.partition("=")[0]: item.partition("=")[2]
                    for item in args.obs_csv}
    if not args.output_root.is_absolute():
        parser.error("--output-root must be an absolute RFS (or home staging) path")
    args.output_root = args.output_root.expanduser().resolve()
    # Check symlinks, too; prevent even accidental output under scratch.
    for scratch in (Path("/scratch"), Path("/iridisfs/scratch")):
        if args.output_root == scratch or scratch in args.output_root.parents:
            parser.error("REFUSING to write under scratch: " + str(args.output_root))
    if not args.preflight:
        parent = args.output_root if args.output_root.is_dir() else args.output_root.parent
        if not parent.is_dir() or not parent.exists():
            parser.error("Output directory (or its parent) must already exist; check RFS mount")
        if not __import__("os").access(parent, __import__("os").W_OK):
            parser.error("Output directory/parent is not writable: " + str(parent))
    script_dir = args.repo / "examples" / "FLUXNET_MultiSite_6" / "scripts"
    base = load_script(script_dir / "14_plot_five_site_spinup1000.py", "six_plot_ref")
    core = load_script(script_dir / "10_compare_six_site_latest_complete_cycle.py",
                       "six_ec_ref")
    if args.preflight:
        bad = 0
        for site in args.sites:
            case = f"{site}_FATES_SPINUP500_11P"
            first, last = SITES[site]
            try:
                core.verify_stream(args.cases_root / case, first, last)
                found = core.history_index(args.archive_root, case)
                years = base.contiguous_found(found, first, YEARS)
                print(f"OK {site}: {len(years)} consecutive h0a years "
                      f"{years[0]}–{years[-1]}", flush=True)
                if not args.carbon_only:
                    try:
                        ec_sources = locate_ec_sources(
                            args.sites_root / site / "forcing",
                            args.gpp_preference, args.obs_csv.get(site))
                        print(f"  EC: {len(ec_sources)} usable HH source files", flush=True)
                        for ecpath, gpp in ec_sources:
                            print(f"    {ecpath} [{gpp}]", flush=True)
                    except Exception as err:
                        print(f"  EC NEEDS REVIEW: {type(err).__name__}: {err}", flush=True)
            except Exception as err:
                bad += 1
                print(f"FAIL {site}: {type(err).__name__}: {err}", file=sys.stderr)
        raise SystemExit(1 if bad else 0)
    args.output_root.mkdir(parents=True, exist_ok=True)
    results = []
    for site in args.sites:
        print("\n" + "=" * 18 + f" {site} " + "=" * 18, flush=True)
        try:
            results.append(process_site(site, args, base, core))
        except Exception as exc:
            print(f"ERROR {site}: {type(exc).__name__}: {exc}",
                  file=sys.stderr, flush=True)
            traceback.print_exc()
            results.append({"Site": site, "Status": "ERROR", "Error": str(exc)})
    summary = pd.DataFrame(results)
    summary.to_csv(args.output_root / "nine_site_spinup1000_summary.csv", index=False)
    print("\nFINAL SUMMARY\n" + summary.to_string(index=False), flush=True)
    print(f"\nResults: {args.output_root}", flush=True)
    if any(x["Status"] == "ERROR" for x in results):
        raise SystemExit(1)
    if any(x["Status"] == "CARBON_OK_EC_ERROR" for x in results):
        raise SystemExit(2)


if __name__ == "__main__":
    main()

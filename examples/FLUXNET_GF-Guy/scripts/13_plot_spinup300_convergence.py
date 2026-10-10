#!/usr/bin/env python3
"""GF-Guy: read 300 annual CLM-FATES h0a files and plot carbon-pool convergence.
Read-only: never changes CIME case or model NetCDF output.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Remote HPC: no display needed.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

DEFAULT_ARCHIVE = Path(
    "/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/"
    "GF-Guy_FATES_SPINUP300_CO2405/lnd/hist"
)
DEFAULT_OUTPUT = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/"
    "GF-Guy/spinup300_diagnostics"
)
SITE_PREFIX = "GF-Guy_FATES_SPINUP300_CO2405.clm2.h0a."
POOLS = {
    "TOTECOSYSC": ("Total ecosystem C", 1.0),  # gC/m2
    "TOTSOMC": ("Soil organic C", 1.0),  # gC/m2
    "FATES_VEGC": ("FATES vegetation C", 1000.0),  # kgC/m2 -> gC/m2
}
FLUXES = {
    "FATES_GPP": ("GPP", 86400.0 * 1000.0),  # kgC/m2/s -> gC/m2/day
    "FATES_NEP": ("NEP", 86400.0 * 1000.0),
}

def annual_mean(ds: xr.Dataset, var: str, factor: float) -> float:
    if var not in ds:
        return float("nan")
    da = ds[var]
    if "time" not in da.dims:
        raise ValueError(f"{var}: expected time dimension, got {da.dims}")
    # Single-site case, one spatial value per time step.
    if any(da.sizes[d] != 1 for d in da.dims if d != "time"):
        raise ValueError(f"{var}: expected one point, got {da.shape}")
    a = np.asarray(da.values, dtype="float64").copy()
    a[~np.isfinite(a) | (np.abs(a) >= 1e30)] = np.nan
    if a.size == 0 or not np.isfinite(a).any():
        return float("nan")
    return float(np.nanmean(a) * factor)


def percent_delta(new: pd.Series, old: pd.Series) -> pd.Series:
    denom = old.abs().where(old.abs() > 1e-8)
    return (new - old) / denom * 100.0


def plot_lines(df: pd.DataFrame, cols: list[str], title: str,
               ylabel: str, dest: Path, *, xcol: str = "model_year",
               zero: bool = False, xlim=None) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    for col in cols:
        if col in df and df[col].notna().any():
            ax.plot(df[xcol], df[col], linewidth=1.6, label=col)
    if zero:
        ax.axhline(0, color="gray", ls="--", lw=0.8)
    ax.set(xlabel="Model year (nominal)", ylabel=ylabel, title=title)
    if xlim is not None:
        ax.set_xlim(*xlim)
    ax.grid(alpha=0.2)
    ax.legend(fontsize=9, loc="best")
    fig.tight_layout()
    fig.savefig(dest, dpi=180)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    archive, output = args.archive, args.output
    output.mkdir(parents=True, exist_ok=True)

    pat = re.compile(r"\.clm2\.h0a\.(\d{4})-\d\d-\d\d-\d{5}\.nc$")
    paths = {}
    for p in archive.glob(SITE_PREFIX + "*.nc"):
        m = pat.search(p.name)
        if m:
            year = int(m.group(1))
            if year in paths:
                raise RuntimeError(f"Duplicate model year {year}: {p}")
            paths[year] = p
    years = sorted(paths)
    if not years:
        raise RuntimeError(f"No h0a history files found under {archive}")
    expected = set(range(2017, 2317))
    got = set(years)
    print(f"Found {len(paths)} yearly h0a files: {years[0]}–{years[-1]}", flush=True)
    if got != expected:
        missing = sorted(expected - got)
        outside = sorted(got - expected)
        raise RuntimeError(
            f"Expected 2017–2316 (300 years); missing={missing[:15]} "
            f"(total {len(missing)}); unexpected={outside[:15]}"
        )

    rows = []
    for i, year in enumerate(years, 1):
        with xr.open_dataset(paths[year], decode_times=False) as ds:
            ntime = int(ds.sizes.get("time", 0))
            if ntime != 365:
                raise ValueError(f"History {year}: expected 365 NO_LEAP daily records, got {ntime}")
            for v in POOLS:
                if v not in ds:
                    raise KeyError(f"Missing required carbon pool {v} in {paths[year]}")
            if i == 1:
                print("Available requested variables:",
                      [v for v in (*POOLS, *FLUXES) if v in ds], flush=True)
            row = {"model_year": year, "spinup_year": i,
                   "forcing_year": 2017 + ((year - 2017) % 5),
                   "forcing_cycle": 1 + ((year - 2017) // 5)}
            for v, (_, f) in POOLS.items():
                row[v] = annual_mean(ds, v, f)
            for v, (_, f) in FLUXES.items():
                row[v] = annual_mean(ds, v, f)
            if "time" in ds.dims:
                row["n_time_records"] = ds.sizes["time"]
        rows.append(row)
        if i % 50 == 0:
            print(f"Read {i}/300 years...", flush=True)

    df = pd.DataFrame(rows).sort_values("model_year").reset_index(drop=True)
    for variable in POOLS:
        if not np.isfinite(df[variable].to_numpy(dtype=float)).all():
            raise ValueError(f"Invalid or missing data in required pool {variable}; aborting plots")
    df["NEE"] = -df["FATES_NEP"]
    pool_vars = list(POOLS)
    for v in pool_vars:
        df[v + "_pct_annual"] = percent_delta(df[v], df[v].shift(1))
        df[v + "_pct_same_forcing_5yr"] = percent_delta(df[v], df[v].shift(5))
        df[v + "_abs_same_forcing_5yr"] = df[v] - df[v].shift(5)

    df.to_csv(output / "GF-Guy_annual_spinup300.csv", index=False, float_format="%.9g")

    # Scientific metadata: all pools converted to gC m-2; fluxes to gC m-2 d-1.
    plot_lines(df, pool_vars,
               "GF-Guy | 300-year spin-up | annual mean carbon pools",
               "Annual mean carbon stock (g C m$^{-2}$)",
               output / "01_carbon_pools_annual_mean.png")
    plot_lines(df, [v + "_pct_annual" for v in pool_vars],
               "GF-Guy | annual carbon-pool changes (different forcing years)",
               "Year-on-year change (%)", output / "02_annual_pct_change.png",
               zero=True)
    plot_lines(df, [v + "_pct_same_forcing_5yr" for v in pool_vars],
               "GF-Guy | change relative to same forcing year 5 years earlier",
               "5-year same-phase change (%)",
               output / "03_same_forcing_5yr_pct_change.png", zero=True)
    plot_lines(df, ["FATES_GPP", "NEE"],
               "GF-Guy | annual mean GPP and NEE (NEE = -FATES_NEP)",
               "Annual mean daily rate (g C m$^{-2}$ d$^{-1}$)",
               output / "04_annual_GPP_NEE.png", zero=True)

    last = df.tail(30).copy()
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    for ax, v in zip(axes, pool_vars):
        ax.plot(last.model_year, last[v], marker=".", linewidth=1.5)
        # End-to-end least-squares linear drift, plotted for descriptive context.
        good = last[v].notna()
        if good.sum() >= 2:
            slope, intercept = np.polyfit(last.loc[good, "model_year"],
                                           last.loc[good, v], 1)
            ax.plot(last.model_year, slope * last.model_year + intercept,
                    linestyle="--", linewidth=1, label=f"trend: {slope:.3g} gC m⁻² yr⁻¹")
            ax.legend(fontsize=8)
        ax.set(ylabel=v + "\n(g C m$^{-2}$)")
        ax.grid(alpha=0.2)
    axes[-1].set_xlabel("Model year (nominal)")
    fig.suptitle("GF-Guy | final 30 model years: carbon-pool drift")
    fig.tight_layout()
    fig.savefig(output / "05_last_30_years_drift.png", dpi=180)
    plt.close(fig)

    cycle = df.groupby("forcing_cycle", as_index=False).agg(
        cycle_start=("model_year", "min"),
        cycle_end=("model_year", "max"),
        **{v: (v, "mean") for v in pool_vars},
    )
    for v in pool_vars:
        cycle[v + "_pct_change_prev_cycle"] = percent_delta(cycle[v], cycle[v].shift(1))
        cycle[v + "_gC_m2_per_year_drift"] = (cycle[v] - cycle[v].shift(1)) / 5
    cycle.to_csv(output / "GF-Guy_5yr_cycle_means.csv", index=False, float_format="%.9g")

    # Summary retains numbers without prescribing a universal convergence threshold.
    summary = []
    for v in pool_vars:
        last30 = df.tail(30).dropna(subset=[v])
        if len(last30) >= 2:
            slope = float(np.polyfit(last30.model_year, last30[v], 1)[0])
        else:
            slope = np.nan
        prev_cycle = cycle.iloc[-2][v]
        last_cycle = cycle.iloc[-1][v]
        denom = abs(prev_cycle)
        p = (last_cycle - prev_cycle) / denom * 100 if denom > 1e-8 else np.nan
        summary.append({
            "variable": v,
            "units": "g C m-2",
            "year_2316_mean": df.iloc[-1][v],
            "last_5yr_cycle_mean": last_cycle,
            "previous_5yr_cycle_mean": prev_cycle,
            "last_cycle_minus_previous_gC_m2": last_cycle - prev_cycle,
            "last_cycle_change_pct": p,
            "last_cycle_drift_gC_m2_per_model_year": (last_cycle - prev_cycle) / 5,
            "last_30yr_linear_trend_gC_m2_per_model_year": slope,
            "last_30yr_same_forcing_pct_mean_abs":
                df[v + "_pct_same_forcing_5yr"].tail(30).abs().mean(),
        })
    sm = pd.DataFrame(summary)
    sm.to_csv(output / "GF-Guy_final_convergence_summary.csv", index=False,
              float_format="%.9g")
    print("\n=== Last-cycle convergence diagnostics (no universal pass/fail applied) ===")
    print(sm.to_string(index=False, float_format=lambda x: f"{x:.5g}"))
    print("\nWrote plots and CSVs to:", output)
    for p in sorted(output.glob("*.png")):
        print("  ", p.name)
    for p in sorted(output.glob("*.csv")):
        print("  ", p.name)
    print("Important: a low drift rate does not itself demonstrate FATES demographic equilibrium.")
    print("Note: Only history-file annual means were analyzed; restart end-state")
    print("      may be better for exact pool-at-boundary convergence analysis.")

if __name__ == "__main__":
    main()

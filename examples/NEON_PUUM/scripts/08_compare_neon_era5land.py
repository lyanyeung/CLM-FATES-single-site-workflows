#!/usr/bin/env python3

import numpy as np
import pandas as pd
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE = Path("/iridisfs/scratch/ly3n24/NEON/PUUM")
PROC = BASE / "processed"

NEON_FILE = PROC / "PUUM_forcing_stage1_2020_2025_noleap.csv"
ERA_FILE  = PROC / "PUUM_ERA5Land_30min_2020_2025_noleap.csv"

OUT_OVERALL = PROC / "PUUM_NEON_vs_ERA5_overall_metrics.csv"
OUT_MONTHLY = PROC / "PUUM_NEON_vs_ERA5_monthly_metrics.csv"
OUT_PRECIP  = PROC / "PUUM_NEON_vs_ERA5_precip_monthly_totals.csv"


VARS = [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
    "PRECTmms",
]


# ============================================================
# Helpers
# ============================================================

def read_time_csv(path):

    df = pd.read_csv(path)

    time_col = None

    for c in [
        "time",
        "timestamp",
        "datetime",
        "TIMESTAMP",
        "TIMESTAMP_START",
    ]:
        if c in df.columns:
            time_col = c
            break

    if time_col is None:
        raise RuntimeError(
            f"Could not find time column in {path}\n"
            f"Columns: {list(df.columns)}"
        )

    df[time_col] = pd.to_datetime(
        df[time_col],
        utc=True
    )

    df = df.set_index(time_col)

    return df


def metrics(obs, mod):

    ok = obs.notna() & mod.notna()

    x = obs[ok].astype(float)
    y = mod[ok].astype(float)

    if len(x) < 2:
        return {
            "n": len(x),
            "obs_mean": np.nan,
            "era_mean": np.nan,
            "bias_era_minus_neon": np.nan,
            "mae": np.nan,
            "rmse": np.nan,
            "correlation": np.nan,
            "ratio_era_over_neon": np.nan,
        }

    diff = y - x

    obs_mean = x.mean()
    era_mean = y.mean()

    if obs_mean != 0:
        ratio = era_mean / obs_mean
    else:
        ratio = np.nan

    return {
        "n": len(x),
        "obs_mean": obs_mean,
        "era_mean": era_mean,
        "bias_era_minus_neon": diff.mean(),
        "mae": np.abs(diff).mean(),
        "rmse": np.sqrt(np.mean(diff ** 2)),
        "correlation": x.corr(y),
        "ratio_era_over_neon": ratio,
    }


# ============================================================
# Read
# ============================================================

print("=" * 80)
print("READING DATA")
print("=" * 80)

neon = read_time_csv(NEON_FILE)
era  = read_time_csv(ERA_FILE)

print("\nNEON:")
print(neon.index.min(), "->", neon.index.max())
print("rows =", len(neon))

print("\nERA5-Land:")
print(era.index.min(), "->", era.index.max())
print("rows =", len(era))


# ============================================================
# Check exact time alignment
# ============================================================

if not neon.index.equals(era.index):
    raise RuntimeError(
        "NEON and ERA5-Land timestamps are not identical."
    )

if len(neon) != 105120:
    raise RuntimeError(
        f"Unexpected NEON row count: {len(neon)}"
    )

if len(era) != 105120:
    raise RuntimeError(
        f"Unexpected ERA row count: {len(era)}"
    )

print("\nTime alignment: PERFECT")


# ============================================================
# Overall comparison
# ============================================================

overall_rows = []

print("\n" + "=" * 80)
print("OVERALL NEON vs ERA5-LAND")
print("=" * 80)

for var in VARS:

    if var not in neon.columns:
        raise RuntimeError(
            f"{var} missing from NEON file"
        )

    if var not in era.columns:
        raise RuntimeError(
            f"{var} missing from ERA file"
        )

    obs = neon[var]
    mod = era[var]

    # For FSDS, exclude nighttime zeros from main radiation comparison
    if var == "FSDS":

        daylight = (
            (obs > 10) |
            (mod > 10)
        )

        m = metrics(
            obs.where(daylight),
            mod.where(daylight)
        )

        comparison_type = "daylight_only"

    else:

        m = metrics(obs, mod)
        comparison_type = "all_overlap"

    m["variable"] = var
    m["comparison_type"] = comparison_type

    overall_rows.append(m)

    print(f"\n{var}")
    print(f"  N overlap        = {m['n']}")
    print(f"  NEON mean        = {m['obs_mean']:.6f}")
    print(f"  ERA5 mean        = {m['era_mean']:.6f}")
    print(f"  ERA5 - NEON bias = {m['bias_era_minus_neon']:.6f}")
    print(f"  MAE              = {m['mae']:.6f}")
    print(f"  RMSE             = {m['rmse']:.6f}")
    print(f"  correlation      = {m['correlation']:.4f}")
    print(f"  ERA/NEON ratio   = {m['ratio_era_over_neon']:.4f}")


overall = pd.DataFrame(overall_rows)

overall = overall[
    [
        "variable",
        "comparison_type",
        "n",
        "obs_mean",
        "era_mean",
        "bias_era_minus_neon",
        "mae",
        "rmse",
        "correlation",
        "ratio_era_over_neon",
    ]
]

overall.to_csv(
    OUT_OVERALL,
    index=False
)


# ============================================================
# Monthly comparison
#
# Month means across ALL years:
# Jan, Feb, ..., Dec
# ============================================================

monthly_rows = []

for var in VARS:

    obs = neon[var]
    mod = era[var]

    for month in range(1, 13):

        mask = neon.index.month == month

        o = obs[mask]
        e = mod[mask]

        if var == "FSDS":

            daylight = (
                (o > 10) |
                (e > 10)
            )

            o = o.where(daylight)
            e = e.where(daylight)

        m = metrics(o, e)

        m["variable"] = var
        m["month"] = month

        monthly_rows.append(m)


monthly = pd.DataFrame(monthly_rows)

monthly = monthly[
    [
        "variable",
        "month",
        "n",
        "obs_mean",
        "era_mean",
        "bias_era_minus_neon",
        "mae",
        "rmse",
        "correlation",
        "ratio_era_over_neon",
    ]
]

monthly.to_csv(
    OUT_MONTHLY,
    index=False
)


# ============================================================
# Precipitation:
# 30-min comparison is NOT the most meaningful comparison
# because ERA5 timing can differ from gauge timing.
#
# Compare monthly precipitation totals instead.
#
# PRECTmms = mm s-1
#
# 30 min total:
#   mm s-1 * 1800 s = mm
# ============================================================

neon_p = neon["PRECTmms"] * 1800.0
era_p  = era["PRECTmms"] * 1800.0

precip = pd.DataFrame({
    "NEON_mm": neon_p,
    "ERA5_mm": era_p,
})

# Only calculate NEON monthly total when sufficient observed coverage exists
precip["NEON_valid"] = neon["PRECTmms"].notna()

rows = []

for period, g in precip.groupby(
    precip.index.to_period("M")
):

    n_total = len(g)
    n_neon = g["NEON_valid"].sum()

    coverage = n_neon / n_total

    # ERA always complete
    era_total = g["ERA5_mm"].sum()

    # NEON total only meaningful with high coverage
    neon_total_observed = g["NEON_mm"].sum(
        min_count=1
    )

    if coverage >= 0.90 and neon_total_observed > 0:

        ratio = (
            era_total /
            neon_total_observed
        )

    else:
        ratio = np.nan

    rows.append({
        "year": period.year,
        "month": period.month,
        "NEON_coverage": coverage,
        "NEON_observed_total_mm": neon_total_observed,
        "ERA5_total_mm": era_total,
        "ERA5_over_NEON_ratio": ratio,
    })


precip_monthly = pd.DataFrame(rows)

precip_monthly.to_csv(
    OUT_PRECIP,
    index=False
)


# ============================================================
# Print monthly biases
# ============================================================

print("\n" + "=" * 80)
print("MONTHLY MEAN BIAS: ERA5 - NEON")
print("=" * 80)

pivot_bias = monthly.pivot(
    index="month",
    columns="variable",
    values="bias_era_minus_neon"
)

print(
    pivot_bias.round(6).to_string()
)


print("\n" + "=" * 80)
print("MONTHLY ERA5 / NEON MEAN RATIO")
print("=" * 80)

pivot_ratio = monthly.pivot(
    index="month",
    columns="variable",
    values="ratio_era_over_neon"
)

print(
    pivot_ratio.round(4).to_string()
)


# ============================================================
# Precip months with good NEON coverage
# ============================================================

good_precip = precip_monthly[
    precip_monthly["NEON_coverage"] >= 0.90
].copy()

print("\n" + "=" * 80)
print("PRECIPITATION MONTHS WITH >=90% NEON COVERAGE")
print("=" * 80)

print(
    good_precip[
        [
            "year",
            "month",
            "NEON_coverage",
            "NEON_observed_total_mm",
            "ERA5_total_mm",
            "ERA5_over_NEON_ratio",
        ]
    ].to_string(index=False)
)


# ============================================================
# Files
# ============================================================

print("\n" + "=" * 80)
print("FILES WRITTEN")
print("=" * 80)

print(OUT_OVERALL)
print(OUT_MONTHLY)
print(OUT_PRECIP)

print("\nSUCCESS")

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

OUT_FILE = PROC / "PUUM_forcing_final_2020_2025_noleap.csv"

OUT_CORR = PROC / "PUUM_ERA5Land_monthly_corrections.csv"


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
# Read files
# ============================================================

def read_file(path):

    df = pd.read_csv(path)

    if "time" not in df.columns:
        raise RuntimeError(
            f"'time' column not found in {path}"
        )

    df["time"] = pd.to_datetime(
        df["time"],
        utc=True
    )

    return df.set_index("time")


neon = read_file(NEON_FILE)
era  = read_file(ERA_FILE)


# ============================================================
# Check alignment
# ============================================================

if not neon.index.equals(era.index):
    raise RuntimeError(
        "NEON and ERA5 timestamps do not match."
    )

if len(neon) != 105120:
    raise RuntimeError(
        f"Expected 105120 NEON rows, got {len(neon)}"
    )


print("=" * 80)
print("PUUM STAGE-2 GAP FILLING")
print("=" * 80)

print("\nRows:", len(neon))
print(
    neon.index.min(),
    "->",
    neon.index.max()
)


# ============================================================
# Short-gap interpolation
#
# Only fills COMPLETE missing runs <= max_steps.
#
# 30 min timestep:
#   6 steps = 3 h
#   2 steps = 1 h
# ============================================================

def fill_short_runs(series, max_steps):

    original = series.copy()

    if max_steps <= 0:

        mask = pd.Series(
            False,
            index=series.index
        )

        return original, mask

    missing = original.isna()

    # Full interpolation candidate
    candidate = original.interpolate(
        method="time",
        limit_area="inside"
    )

    groups = (
        missing != missing.shift()
    ).cumsum()

    fill_mask = pd.Series(
        False,
        index=series.index
    )

    for _, idx in series.groupby(groups).groups.items():

        idx = pd.Index(idx)

        if not missing.loc[idx[0]]:
            continue

        if len(idx) <= max_steps:

            # Must have interpolation available
            if candidate.loc[idx].notna().all():

                fill_mask.loc[idx] = True

    result = original.copy()

    result.loc[fill_mask] = (
        candidate.loc[fill_mask]
    )

    return result, fill_mask


# ============================================================
# Monthly additive correction
#
# corrected ERA =
# ERA + mean(NEON - ERA)
# ============================================================

def additive_correction(obs, era_series):

    correction = {}
    nobs = {}

    for month in range(1, 13):

        mask = (
            (obs.index.month == month)
            & obs.notna()
            & era_series.notna()
        )

        correction[month] = (
            obs.loc[mask] -
            era_series.loc[mask]
        ).mean()

        nobs[month] = int(mask.sum())

    return correction, nobs


# ============================================================
# Monthly multiplicative correction
#
# corrected ERA =
# ERA * NEON_mean / ERA_mean
# ============================================================

def multiplicative_correction(
    obs,
    era_series,
    daylight=False,
    clip_min=None,
    clip_max=None,
):

    correction = {}
    nobs = {}

    for month in range(1, 13):

        mask = (
            (obs.index.month == month)
            & obs.notna()
            & era_series.notna()
        )

        if daylight:

            mask &= (
                (obs > 10.0)
                | (era_series > 10.0)
            )

        o = obs.loc[mask]
        e = era_series.loc[mask]

        factor = (
            o.mean() / e.mean()
        )

        if clip_min is not None:
            factor = max(
                factor,
                clip_min
            )

        if clip_max is not None:
            factor = min(
                factor,
                clip_max
            )

        correction[month] = factor
        nobs[month] = int(mask.sum())

    return correction, nobs


# ============================================================
# Precipitation correction
#
# Do NOT use half-hour correlation.
#
# For each year-month with >=90% NEON coverage:
#
# ratio =
# NEON monthly total /
# ERA monthly total
#
# Then take MEDIAN ratio for each calendar month.
# ============================================================

def precipitation_correction(obs, era_series):

    rows = []

    for year in range(2020, 2026):

        for month in range(1, 13):

            mask = (
                (obs.index.year == year)
                & (obs.index.month == month)
            )

            o = obs.loc[mask]
            e = era_series.loc[mask]

            coverage = (
                o.notna().mean()
            )

            # convert mm/s -> mm per 30 min
            obs_total = (
                o * 1800.0
            ).sum(min_count=1)

            era_total = (
                e * 1800.0
            ).sum()

            if (
                coverage >= 0.90
                and obs_total > 10.0
                and era_total > 10.0
            ):

                ratio = (
                    obs_total /
                    era_total
                )

                rows.append({
                    "year": year,
                    "month": month,
                    "coverage": coverage,
                    "obs_total": obs_total,
                    "era_total": era_total,
                    "ratio": ratio,
                })


    monthly = pd.DataFrame(rows)

    global_factor = (
        monthly["ratio"].median()
    )

    factors = {}
    nsamples = {}

    for month in range(1, 13):

        x = monthly.loc[
            monthly["month"] == month,
            "ratio"
        ]

        if len(x) >= 2:

            f = x.median()

        else:

            f = global_factor

        # Prevent pathological scaling
        f = np.clip(
            f,
            0.25,
            4.0
        )

        factors[month] = f
        nsamples[month] = len(x)

    return factors, nsamples, monthly


# ============================================================
# Build corrections
# ============================================================

corrections = {}
correction_rows = []


# ------------------------------------------------------------
# Additive variables
# ------------------------------------------------------------

for var in [
    "TBOT",
    "PSRF",
    "FLDS",
]:

    corr, nobs = additive_correction(
        neon[var],
        era[var]
    )

    corrections[var] = (
        "additive",
        corr
    )

    for month in range(1, 13):

        correction_rows.append({
            "variable": var,
            "month": month,
            "method": "additive",
            "correction": corr[month],
            "n": nobs[month],
        })


# ------------------------------------------------------------
# QBOT
# ------------------------------------------------------------

corr, nobs = multiplicative_correction(
    neon["QBOT"],
    era["QBOT"],
    clip_min=0.5,
    clip_max=1.5,
)

corrections["QBOT"] = (
    "multiplicative",
    corr
)

for month in range(1, 13):

    correction_rows.append({
        "variable": "QBOT",
        "month": month,
        "method": "multiplicative",
        "correction": corr[month],
        "n": nobs[month],
    })


# ------------------------------------------------------------
# FSDS daylight correction
# ------------------------------------------------------------

corr, nobs = multiplicative_correction(
    neon["FSDS"],
    era["FSDS"],
    daylight=True,
    clip_min=0.5,
    clip_max=1.5,
)

corrections["FSDS"] = (
    "multiplicative",
    corr
)

for month in range(1, 13):

    correction_rows.append({
        "variable": "FSDS",
        "month": month,
        "method": "multiplicative_daylight",
        "correction": corr[month],
        "n": nobs[month],
    })


# ------------------------------------------------------------
# WIND
# ------------------------------------------------------------

corr, nobs = multiplicative_correction(
    neon["WIND"],
    era["WIND"],
    clip_min=0.5,
    clip_max=2.0,
)

corrections["WIND"] = (
    "multiplicative",
    corr
)

for month in range(1, 13):

    correction_rows.append({
        "variable": "WIND",
        "month": month,
        "method": "multiplicative",
        "correction": corr[month],
        "n": nobs[month],
    })


# ------------------------------------------------------------
# PRECTmms
# ------------------------------------------------------------

precip_corr, precip_n, precip_samples = (
    precipitation_correction(
        neon["PRECTmms"],
        era["PRECTmms"]
    )
)

corrections["PRECTmms"] = (
    "multiplicative",
    precip_corr
)

for month in range(1, 13):

    correction_rows.append({
        "variable": "PRECTmms",
        "month": month,
        "method": "monthly_total_median_ratio",
        "correction": precip_corr[month],
        "n": precip_n[month],
    })


# ============================================================
# Save correction table
# ============================================================

corr_table = pd.DataFrame(
    correction_rows
)

corr_table.to_csv(
    OUT_CORR,
    index=False
)


# ============================================================
# Apply corrections to complete ERA5 series
# ============================================================

era_corrected = era[VARS].copy()

for var in VARS:

    method, corr = corrections[var]

    for month in range(1, 13):

        mask = (
            era_corrected.index.month
            == month
        )

        if method == "additive":

            era_corrected.loc[
                mask, var
            ] = (
                era.loc[mask, var]
                + corr[month]
            )

        elif method == "multiplicative":

            era_corrected.loc[
                mask, var
            ] = (
                era.loc[mask, var]
                * corr[month]
            )


# ============================================================
# Physical constraints
# ============================================================

era_corrected["QBOT"] = (
    era_corrected["QBOT"]
    .clip(lower=1e-8)
)

era_corrected["FSDS"] = (
    era_corrected["FSDS"]
    .clip(lower=0.0)
)

era_corrected["FLDS"] = (
    era_corrected["FLDS"]
    .clip(lower=0.0)
)

era_corrected["WIND"] = (
    era_corrected["WIND"]
    .clip(lower=0.0)
)

era_corrected["PRECTmms"] = (
    era_corrected["PRECTmms"]
    .clip(lower=0.0)
)


# ============================================================
# Short-gap limits
# ============================================================

short_limits = {

    # 3 hours
    "TBOT": 6,
    "QBOT": 6,
    "PSRF": 6,
    "FLDS": 6,

    # 1 hour
    "WIND": 2,

    # use ERA5 directly for missing radiation
    "FSDS": 0,

    # never interpolate precipitation
    "PRECTmms": 0,
}


# ============================================================
# Build final forcing
# ============================================================

final = pd.DataFrame(
    index=neon.index
)

summary = []


for var in VARS:

    raw = neon[var].astype(float)

    filled, interp_mask = fill_short_runs(
        raw,
        short_limits[var]
    )

    era_mask = filled.isna()

    filled.loc[era_mask] = (
        era_corrected.loc[
            era_mask,
            var
        ]
    )

    final[var] = filled


    # --------------------------------------------------------
    # Source provenance
    # --------------------------------------------------------

    source_col = f"{var}_source"

    if source_col in neon.columns:

        source = (
            neon[source_col]
            .astype("object")
            .copy()
        )

    else:

        source = pd.Series(
            np.nan,
            index=neon.index,
            dtype="object"
        )


    # raw NEON
    raw_mask = raw.notna()

    source.loc[
        raw_mask & source.isna()
    ] = "NEON_RAW"

    source.loc[
        raw_mask & (source == "MISSING")
    ] = "NEON_RAW"


    # short interpolation
    source.loc[
        interp_mask
    ] = "INTERPOLATED_SHORT"


    # corrected ERA5
    source.loc[
        era_mask
    ] = "ERA5LAND_BIASCORR"


    final[
        f"{var}_source"
    ] = source


    summary.append({
        "variable": var,
        "NEON_raw": int(
            raw_mask.sum()
        ),
        "interpolated_short": int(
            interp_mask.sum()
        ),
        "ERA5Land_corrected": int(
            era_mask.sum()
        ),
        "remaining_missing": int(
            filled.isna().sum()
        ),
    })


# ============================================================
# Final QC
# ============================================================

print("\n" + "=" * 80)
print("FINAL QC")
print("=" * 80)

print("\nRows:")
print(len(final))

print("\nMissing values:")

print(
    final[VARS]
    .isna()
    .sum()
)


if final[VARS].isna().any().any():

    raise RuntimeError(
        "Final forcing still contains missing values."
    )


if len(final) != 105120:

    raise RuntimeError(
        f"Expected 105120 rows, got {len(final)}"
    )


print("\nVariable ranges:")

for var in VARS:

    print(
        f"{var:9s}"
        f" min={final[var].min():12.6f}"
        f" mean={final[var].mean():12.6f}"
        f" max={final[var].max():12.6f}"
    )


# ============================================================
# Source summary
# ============================================================

summary = pd.DataFrame(summary)

print("\n" + "=" * 80)
print("GAP-FILL SUMMARY")
print("=" * 80)

print(
    summary.to_string(index=False)
)


print("\n" + "=" * 80)
print("SOURCE FRACTIONS")
print("=" * 80)

for var in VARS:

    source_col = f"{var}_source"

    print(f"\n{var}")

    print(
        final[source_col]
        .value_counts(
            normalize=True,
            dropna=False
        )
        .round(4)
        .to_string()
    )


# ============================================================
# Save
# ============================================================

final.index.name = "time"

final.to_csv(
    OUT_FILE
)

print("\n" + "=" * 80)
print("FILES WRITTEN")
print("=" * 80)

print(OUT_FILE)
print(OUT_CORR)

print("\nSUCCESS")

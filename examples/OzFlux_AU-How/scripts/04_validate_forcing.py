#!/usr/bin/env python3

from pathlib import Path
import os
import numpy as np
import pandas as pd

USER = os.environ.get("IRIDIS_USER", "ly3n24")

ROOT = Path(
    f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/AU-How"
)

F = ROOT / "forcing/processed/AU-How_CLM_forcing_2003_2025.csv"

df = pd.read_csv(F)
df["time"] = pd.to_datetime(df["time"])

VARS = [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
    "PRECTmms",
    "ZBOT",
]

# ============================================================
# 1. Structural checks
# ============================================================

assert len(df) == 403248, f"Unexpected total row count: {len(df)}"

assert not df["time"].duplicated().any(), \
    "Duplicate timestamps found"

dt = df["time"].diff().dropna()

assert (dt == pd.Timedelta(minutes=30)).all(), \
    "Time axis is not continuous 30-minute data"

assert not df[VARS].isna().any().any(), \
    df[VARS].isna().sum()

# ============================================================
# 2. Broad physical checks
# These are alarms, not automatic corrections.
# ============================================================

physical_bounds = {
    "TBOT":      (230, 330),
    "QBOT":      (0, 0.05),
    "PSRF":      (50000, 110000),
    "FSDS":      (-50, 2000),
    "FLDS":      (0, 800),
    "WIND":      (0, 50),
    "PRECTmms":  (0, 0.2),
}

print("\n===== BROAD PHYSICAL RANGE CHECK =====")

for var, (lo, hi) in physical_bounds.items():

    bad = df[
        (df[var] < lo) |
        (df[var] > hi)
    ]

    print(
        f"{var:10s}: "
        f"{len(bad)} values outside [{lo}, {hi}]"
    )

    if len(bad):
        print(
            bad[
                ["time", var]
            ].head(20).to_string(index=False)
        )

assert np.allclose(df["ZBOT"], 23.0), \
    "ZBOT is not constant 23 m"

# ============================================================
# 3. Detailed ranges
# ============================================================

print("\n===== VARIABLE RANGES =====")

for var in VARS:

    print(
        f"{var:10s} "
        f"min={df[var].min():.8g} "
        f"max={df[var].max():.8g} "
        f"mean={df[var].mean():.8g} "
        f"missing={df[var].isna().sum()}"
    )

# ============================================================
# 4. Check isolated spikes against neighbouring records
#
# This DOES NOT modify data.
# It only reports suspicious points for manual inspection.
# ============================================================

print("\n===== ISOLATED-SPIKE DIAGNOSTICS =====")

# Difference between current value and mean of previous/next
# 30-minute observations.
thresholds = {
    "TBOT": 10.0,          # K
    "QBOT": 0.010,         # kg/kg
    "PSRF": 5000.0,        # Pa
    "FSDS": 600.0,         # W/m2
    "FLDS": 150.0,         # W/m2
    "WIND": 10.0,          # m/s
}

for var, threshold in thresholds.items():

    x = df[var]

    neighbour_mean = (
        x.shift(1) + x.shift(-1)
    ) / 2.0

    delta = (x - neighbour_mean).abs()

    suspicious = df.loc[
        delta > threshold,
        ["time", var]
    ].copy()

    suspicious["previous"] = x.shift(1)[delta > threshold].values
    suspicious["next"] = x.shift(-1)[delta > threshold].values
    suspicious["delta_from_neighbour_mean"] = \
        delta[delta > threshold].values

    print(
        f"\n{var}: "
        f"{len(suspicious)} candidate isolated spikes "
        f"(threshold={threshold})"
    )

    if len(suspicious):

        suspicious = suspicious.sort_values(
            "delta_from_neighbour_mean",
            ascending=False
        )

        print(
            suspicious.head(30).to_string(index=False)
        )

# ============================================================
# 5. Largest 30-minute changes
# ============================================================

print("\n===== LARGEST STEP CHANGES =====")

for var in [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
]:

    step = df[var].diff().abs()

    idx = step.nlargest(20).index

    out = pd.DataFrame({
        "time": df.loc[idx, "time"],
        "value": df.loc[idx, var],
        "previous": df[var].shift(1).loc[idx],
        "abs_step": step.loc[idx],
    })

    print(f"\n--- {var} ---")
    print(out.to_string(index=False))

# ============================================================
# 6. Check suspicious zeros
# ============================================================

print("\n===== ZERO-VALUE CHECK =====")

for var in [
    "QBOT",
    "PSRF",
    "FLDS",
    "WIND",
]:

    z = df[df[var] == 0]

    print(
        f"{var:10s}: {len(z)} exact zero values"
    )

    if len(z):
        print(
            z[
                ["time", var]
            ].head(20).to_string(index=False)
        )

# FSDS=0 at night is normal, so report only count.
print(
    f"FSDS exact zeros: "
    f"{(df['FSDS'] == 0).sum()} "
    "(normally expected at night)"
)

# ============================================================
# 7. Leap/no-leap consistency
# ============================================================

noleap = df[
    ~(
        (df["time"].dt.month == 2) &
        (df["time"].dt.day == 29)
    )
].copy()

assert len(noleap) == 402960, \
    f"Unexpected noleap rows: {len(noleap)}"

counts = (
    noleap
    .groupby(noleap["time"].dt.year)
    .size()
)

assert (counts == 17520).all(), counts

print("\n===== NOLEAP CHECK =====")
print("Rows before removing Feb29:", len(df))
print("Rows after removing Feb29 :", len(noleap))

print("\nAU-How enhanced forcing diagnostic completed.")
print("No data have been modified.")
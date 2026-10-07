#!/usr/bin/env python3

import pandas as pd
import numpy as np
from pathlib import Path

INFILE = Path(
    "/iridisfs/scratch/ly3n24/NEON/PUUM/processed/"
    "PUUM_forcing_stage1_2020_2025_noleap.csv"
)

OUTFILE = Path(
    "/iridisfs/scratch/ly3n24/NEON/PUUM/processed/"
    "PUUM_stage1_gap_runs_2020_2025.csv"
)

VARS = [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
    "PRECTmms",
]

df = pd.read_csv(INFILE)

# ------------------------------------------------------------
# Find timestamp column
# ------------------------------------------------------------
candidate_names = [
    "time", "timestamp", "datetime", "DateTime",
    "TIMESTAMP", "TIMESTAMP_START", "date"
]

time_col = None

for c in candidate_names:
    if c in df.columns:
        time_col = c
        break

if time_col is None:
    # Fall back to first column that can be parsed as datetime
    for c in df.columns:
        test = pd.to_datetime(df[c], errors="coerce", utc=True)
        if test.notna().mean() > 0.95:
            time_col = c
            break

if time_col is None:
    raise RuntimeError(
        "Could not identify timestamp column.\n"
        f"Available columns:\n{list(df.columns)}"
    )

df[time_col] = pd.to_datetime(df[time_col], utc=True)

print(f"Time column: {time_col}")
print(f"Start: {df[time_col].min()}")
print(f"End:   {df[time_col].max()}")
print(f"Rows:  {len(df)}")

# ------------------------------------------------------------
# Identify consecutive missing-data runs
# ------------------------------------------------------------
all_gaps = []

for var in VARS:

    if var not in df.columns:
        print(f"WARNING: {var} not found")
        continue

    missing = df[var].isna()

    # Group consecutive True/False runs
    grp = (missing != missing.shift()).cumsum()

    temp = df.loc[missing, [time_col]].copy()
    temp["group"] = grp[missing].values

    for _, g in temp.groupby("group"):

        start = g[time_col].iloc[0]
        end = g[time_col].iloc[-1]

        n_steps = len(g)
        hours = n_steps * 0.5
        days = hours / 24.0

        all_gaps.append({
            "variable": var,
            "start": start,
            "end": end,
            "n_halfhours": n_steps,
            "hours": hours,
            "days": days
        })

gaps = pd.DataFrame(all_gaps)

gaps = gaps.sort_values(
    ["variable", "n_halfhours"],
    ascending=[True, False]
)

gaps.to_csv(OUTFILE, index=False)

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
print("\n" + "=" * 80)
print("LONGEST GAPS BY VARIABLE")
print("=" * 80)

for var in VARS:

    vg = gaps[gaps["variable"] == var].copy()

    if len(vg) == 0:
        print(f"\n{var}: no gaps")
        continue

    print(f"\n{var}")
    print(
        vg.head(10)[
            ["start", "end", "n_halfhours", "hours", "days"]
        ].to_string(index=False)
    )

print("\n" + "=" * 80)
print("GAP COUNTS")
print("=" * 80)

for var in VARS:

    vg = gaps[gaps["variable"] == var]

    if len(vg) == 0:
        continue

    print(
        f"{var:9s} "
        f"total gaps={len(vg):5d}   "
        f">3h={(vg['hours'] > 3).sum():4d}   "
        f">24h={(vg['hours'] > 24).sum():4d}   "
        f">7d={(vg['days'] > 7).sum():3d}"
    )

print("\nWritten:")
print(OUTFILE)

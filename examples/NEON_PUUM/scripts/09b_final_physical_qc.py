#!/usr/bin/env python3

import pandas as pd
from pathlib import Path


BASE = Path("/iridisfs/scratch/ly3n24/NEON/PUUM")
PROC = BASE / "processed"

FINAL_FILE = PROC / "PUUM_forcing_final_2020_2025_noleap.csv"
ERA_FILE   = PROC / "PUUM_ERA5Land_30min_2020_2025_noleap.csv"
CORR_FILE  = PROC / "PUUM_ERA5Land_monthly_corrections.csv"

OUT_FILE = PROC / "PUUM_forcing_final_QC_2020_2025_noleap.csv"


# ============================================================
# Read
# ============================================================

final = pd.read_csv(
    FINAL_FILE,
    parse_dates=["time"]
).set_index("time")

era = pd.read_csv(
    ERA_FILE,
    parse_dates=["time"]
).set_index("time")

corr = pd.read_csv(CORR_FILE)


# ============================================================
# Reconstruct monthly bias-corrected ERA5 QBOT
# ============================================================

qbot_era_corrected = era["QBOT"].copy()

qbot_corr = corr[
    corr["variable"] == "QBOT"
].set_index("month")["correction"]

for month in range(1, 13):

    mask = qbot_era_corrected.index.month == month

    qbot_era_corrected.loc[mask] = (
        era.loc[mask, "QBOT"]
        * qbot_corr.loc[month]
    )


# ============================================================
# Diagnose bad values
# ============================================================

bad_qbot = final["QBOT"] < 0
bad_fsds = final["FSDS"] < 0

print("=" * 80)
print("PHYSICAL QC")
print("=" * 80)

print("\nNegative QBOT values:")
print(bad_qbot.sum())

if bad_qbot.any():

    print("\nQBOT source of negative values:")

    print(
        final.loc[
            bad_qbot,
            "QBOT_source"
        ].value_counts()
    )


print("\nNegative FSDS values:")
print(bad_fsds.sum())

if bad_fsds.any():

    print("\nFSDS source of negative values:")

    print(
        final.loc[
            bad_fsds,
            "FSDS_source"
        ].value_counts()
    )


# ============================================================
# Correct physically impossible values
# ============================================================

# QBOT:
# Negative humidity is impossible.
# Replace with bias-corrected ERA5-Land rather than clipping to zero.

final.loc[
    bad_qbot,
    "QBOT"
] = qbot_era_corrected.loc[bad_qbot]

final.loc[
    bad_qbot,
    "QBOT_source"
] = "ERA5LAND_BIASCORR_INVALID_NEON"


# FSDS:
# Small nighttime negative radiation is sensor zero-offset.
# Set to zero.

final.loc[
    bad_fsds,
    "FSDS"
] = 0.0

final.loc[
    bad_fsds,
    "FSDS_source"
] = (
    final.loc[
        bad_fsds,
        "FSDS_source"
    ].astype(str)
    + "_NEGATIVE_TO_ZERO"
)


# ============================================================
# Final physical checks
# ============================================================

VARS = [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
    "PRECTmms",
]

print("\n" + "=" * 80)
print("FINAL CHECK")
print("=" * 80)

print("\nMissing:")
print(final[VARS].isna().sum())

print("\nRanges:")

for var in VARS:

    print(
        f"{var:9s}"
        f" min={final[var].min():12.6f}"
        f" mean={final[var].mean():12.6f}"
        f" max={final[var].max():12.6f}"
    )


assert len(final) == 105120

assert not final[VARS].isna().any().any()

assert (final["QBOT"] >= 0).all()
assert (final["PSRF"] > 0).all()
assert (final["FSDS"] >= 0).all()
assert (final["FLDS"] >= 0).all()
assert (final["WIND"] >= 0).all()
assert (final["PRECTmms"] >= 0).all()


# ============================================================
# Save
# ============================================================

final.to_csv(OUT_FILE)

print("\nWritten:")
print(OUT_FILE)

print("\nSUCCESS")

#!/usr/bin/env python3
from pathlib import Path
import os
import numpy as np
import pandas as pd

USER = os.environ.get("IRIDIS_USER", "ly3n24")
SITE = "US-Ha1"

ROOT = Path(
    f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/{SITE}"
)

F = ROOT / "forcing/processed/US-Ha1_CLM_forcing_1991_2025.csv"
Q = ROOT / "forcing/processed/US-Ha1_forcing_replacements.csv"

df = pd.read_csv(F)
df["time"] = pd.to_datetime(df["time"])

vars_ = [
    "TBOT", "QBOT", "PSRF", "FSDS",
    "FLDS", "WIND", "PRECTmms", "ZBOT",
]

EXPECTED_ROWS = 35 * 365 * 24

assert len(df) == EXPECTED_ROWS, (
    f"Unexpected total rows: {len(df)}"
)
assert not df["time"].duplicated().any()
assert not (
    (df["time"].dt.month == 2) &
    (df["time"].dt.day == 29)
).any()

counts = df.groupby(df["time"].dt.year).size()

assert list(counts.index) == list(range(1991, 2026))
assert (counts == 8760).all(), counts

assert not df[vars_].isna().any().any()

# Broad physical bounds.
assert df["TBOT"].between(230, 330).all()
assert df["QBOT"].between(0, 0.05).all()
assert df["PSRF"].between(80000, 110000).all()
assert df["FSDS"].between(0, 1500).all()
assert df["FLDS"].between(100, 600).all()
assert df["WIND"].between(0, 60).all()
assert df["PRECTmms"].between(0, 0.1).all()
assert np.allclose(df["ZBOT"], 27.9)

# Verify the known successful QC/replacement result.
qc = pd.read_csv(Q)

actual = qc.groupby(
    ["method", "variable"]
).size().to_dict()

expected = {
    ("mean_of_adjacent_hours", "LW_IN_F"): 2,
    ("mean_of_adjacent_hours", "PA_F"): 1,
    ("replace_TA_VPD_pair_with_ERA", "TA_F"): 29,
    ("replace_TA_VPD_pair_with_ERA", "VPD_F"): 29,
}

assert actual == expected, (
    f"Unexpected forcing replacement counts:\n"
    f"actual={actual}\nexpected={expected}"
)

assert len(qc) == 61

print("US-Ha1 forcing QC PASSED")
print("Rows:", len(df))
print("Years:", df["time"].dt.year.min(), "-", df["time"].dt.year.max())

print("\nForcing ranges:")
for c in vars_:
    print(
        f"{c:10s}",
        float(df[c].min()),
        "to",
        float(df[c].max())
    )

print("\nReplacement counts:")
for k, v in actual.items():
    print(k, v)

print("\nTotal correction-log rows:", len(qc))

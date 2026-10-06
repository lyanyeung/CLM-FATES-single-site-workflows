#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd
import numpy as np

USER = os.environ.get("IRIDIS_USER", "ly3n24")
SITE = "ES-LJu"
ROOT = Path(f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/{SITE}")

F = ROOT / "forcing/processed/ES-LJu_CLM_forcing_2004_2024.csv"

df = pd.read_csv(F)
df["time"] = pd.to_datetime(df["time"])

vars_ = [
    "TBOT", "QBOT", "PSRF", "FSDS",
    "FLDS", "WIND", "PRECTmms", "ZBOT",
]

assert len(df) == 367920, f"Unexpected total rows: {len(df)}"
assert not df["time"].duplicated().any(), "Duplicate timestamps found"
assert not ((df["time"].dt.month == 2) & (df["time"].dt.day == 29)).any()

counts = df.groupby(df["time"].dt.year).size()
assert list(counts.index) == list(range(2004, 2025))
assert (counts == 17520).all(), counts

assert not df[vars_].isna().any().any(), df[vars_].isna().sum()

# Broad physical sanity checks; these are intentionally wider than the
# observed ES-LJu ranges.
assert df["TBOT"].between(230, 330).all()
assert df["QBOT"].between(0, 0.05).all()
assert df["PSRF"].between(50000, 110000).all()
assert (df["FSDS"] >= 0).all()
assert (df["FLDS"] >= 0).all()
assert (df["WIND"] >= 0).all()
assert (df["PRECTmms"] >= 0).all()
assert np.allclose(df["ZBOT"], 2.5)

print("Rows:", len(df))
print()
for c in vars_:
    print(
        f"{c:10s}",
        float(df[c].min()),
        "to",
        float(df[c].max()),
        "missing =",
        int(df[c].isna().sum()),
    )

print("\nPer-year counts:")
print(counts.to_string())

print("\n10 lowest QBOT:")
print(
    df.nsmallest(10, "QBOT")[
        ["time", "TBOT", "QBOT", "PSRF"]
    ].to_string(index=False)
)

print("\nForcing QC PASSED")

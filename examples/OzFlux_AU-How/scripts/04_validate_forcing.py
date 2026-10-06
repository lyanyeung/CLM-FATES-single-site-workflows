#!/usr/bin/env python3
from pathlib import Path
import os
import numpy as np
import pandas as pd

USER = os.environ.get("IRIDIS_USER", "ly3n24")
ROOT = Path(f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/AU-How")

F = ROOT / "forcing/processed/AU-How_CLM_forcing_2003_2025.csv"

df = pd.read_csv(F)
df["time"] = pd.to_datetime(df["time"])

VARS = [
    "TBOT", "QBOT", "PSRF", "FSDS",
    "FLDS", "WIND", "PRECTmms", "ZBOT",
]

assert len(df) == 403248, f"Unexpected total row count: {len(df)}"
assert not df["time"].duplicated().any(), "Duplicate timestamps found"

dt = df["time"].diff().dropna()
assert (dt == pd.Timedelta(minutes=30)).all(), "Time axis is not continuous 30-min"

counts = df.groupby(df["time"].dt.year).size()
expected = {}
for y in range(2003, 2026):
    leap = (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))
    expected[y] = 17568 if leap else 17520

for y, n in expected.items():
    assert counts.loc[y] == n, f"{y}: expected {n}, got {counts.loc[y]}"

assert not df[VARS].isna().any().any(), df[VARS].isna().sum()

# Broad physical sanity checks. These are QC alarms, not data cleaning.
assert df["TBOT"].between(230, 330).all(), "TBOT outside broad physical range"
assert df["QBOT"].between(0, 0.05).all(), "QBOT outside broad physical range"
assert df["PSRF"].between(50000, 110000).all(), "PSRF outside broad physical range"
assert df["FSDS"].between(-50, 2000).all(), "FSDS outside broad physical range"
assert df["FLDS"].between(0, 800).all(), "FLDS outside broad physical range"
assert df["WIND"].between(0, 50).all(), "WIND outside broad physical range"
assert df["PRECTmms"].between(0, 0.2).all(), "PRECTmms outside broad physical range"
assert np.allclose(df["ZBOT"], 23.0), "ZBOT is not constant 23 m"

noleap = df[
    ~((df["time"].dt.month == 2) & (df["time"].dt.day == 29))
].copy()

assert len(noleap) == 402960, f"Unexpected noleap rows: {len(noleap)}"

noleap_counts = noleap.groupby(noleap["time"].dt.year).size()
assert (noleap_counts == 17520).all(), noleap_counts

print("Rows before removing Feb29:", len(df))
print("Rows after removing Feb29 :", len(noleap))
print()
for c in VARS:
    print(
        f"{c:10s}",
        float(df[c].min()),
        "to",
        float(df[c].max()),
        "missing =",
        int(df[c].isna().sum()),
    )

print("\nPer-year noleap counts:")
print(noleap_counts.to_string())

print("\n10 lowest QBOT:")
print(
    df.nsmallest(10, "QBOT")[
        ["time", "TBOT", "QBOT", "PSRF"]
    ].to_string(index=False)
)

print("\nAU-How forcing QC PASSED")

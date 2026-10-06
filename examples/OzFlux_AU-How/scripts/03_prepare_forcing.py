#!/usr/bin/env python3
"""
Prepare the successful AU-How CLM/FATES 30-minute forcing and EC-validation CSVs
from OzFlux HowardSprings_L6.nc.

Historical workflow conventions reproduced here:
- Use OzFlux L6 timestamps directly as decoded from the NetCDF time coordinate.
- Do NOT apply the earlier TCCAS local-time -> UTC conversion or -30 min shift.
- Retain 2003-2025 in the processed CSV.
- Keep leap days here; 05_make_datm.py removes Feb 29 for NO_LEAP DATM files.
- OzFlux L6 meteorological variables are already gap-filled; this script does
  not invent an additional interpolation step.
"""

from pathlib import Path
import os
import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

USER = os.environ.get("IRIDIS_USER", "ly3n24")
SITE = "AU-How"

ROOT = Path(f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/{SITE}")
RAW = ROOT / "forcing/raw/HowardSprings_L6.nc"
PROCESSED = ROOT / "forcing/processed"
OBS = ROOT / "obs"

PROCESSED.mkdir(parents=True, exist_ok=True)
OBS.mkdir(parents=True, exist_ok=True)

OUT_FORCING = PROCESSED / "AU-How_CLM_forcing_2003_2025.csv"
OUT_OBS = OBS / "AU-How_EC_GPP_NEE_LT_2003_2025.csv"
OUT_QC = PROCESSED / "AU-How_forcing_source_QC_summary.csv"

START_YEAR = 2003
END_YEAR = 2025
ZBOT = 23.0

REQUIRED = [
    "time",
    "Ta",
    "SH",
    "ps",
    "Fsd",
    "Fld",
    "Ws",
    "Precip",
    "GPP_LT",
    "NEE_LT",
]

def read_series(ds, name):
    if name not in ds.variables:
        raise KeyError(f"Missing required OzFlux variable: {name}")

    a = ds.variables[name][:]
    if np.ma.isMaskedArray(a):
        a = a.filled(np.nan)

    a = np.asarray(a, dtype=float).squeeze()

    if a.ndim != 1:
        raise ValueError(
            f"{name}: expected a 1-D site time series after squeeze, got {a.shape}"
        )

    # Common OzFlux / flux-product fill values if they survive masking.
    a[np.isclose(a, -9999.0)] = np.nan
    a[np.isclose(a, -99999.0)] = np.nan
    a[a <= -9990] = np.nan
    return a

with Dataset(RAW) as ds:
    missing = [v for v in REQUIRED if v not in ds.variables]
    if missing:
        raise RuntimeError(f"Required variables missing from {RAW}: {missing}")

    t = ds.variables["time"]
    dates = num2date(
        t[:],
        units=t.units,
        calendar=getattr(t, "calendar", "standard"),
        only_use_cftime_datetimes=False,
    )

    time = pd.DatetimeIndex([
        pd.Timestamp(
            x.year, x.month, x.day,
            x.hour, x.minute, x.second
        )
        for x in dates
    ])

    src = {
        name: read_series(ds, name)
        for name in REQUIRED
        if name != "time"
    }

n = len(time)
for name, arr in src.items():
    if len(arr) != n:
        raise RuntimeError(f"{name}: length {len(arr)} != time length {n}")

df = pd.DataFrame({"time": time, **src})

df = df[
    (df["time"].dt.year >= START_YEAR)
    & (df["time"].dt.year <= END_YEAR)
].copy()

df = df.sort_values("time").reset_index(drop=True)

if df["time"].duplicated().any():
    raise RuntimeError("Duplicate timestamps found after selecting 2003-2025")

dt = df["time"].diff().dropna()
if not (dt == pd.Timedelta(minutes=30)).all():
    print("Non-30-minute timestamp differences:")
    print(dt[dt != pd.Timedelta(minutes=30)].head(20))
    raise RuntimeError("Selected OzFlux time axis is not continuous 30-minute data")

# 2003-2025 inclusive, including the six leap days:
# 23*365*48 + 6*48 = 403248
EXPECTED_WITH_LEAP = 403248
if len(df) != EXPECTED_WITH_LEAP:
    raise RuntimeError(
        f"Expected {EXPECTED_WITH_LEAP} rows for 2003-2025 before noleap "
        f"conversion, got {len(df)}"
    )

# Successful AU-How mapping used in the CLM/FATES run.
forcing = pd.DataFrame({
    "time": df["time"],
    "TBOT": df["Ta"] + 273.15,     # degC -> K
    "QBOT": df["SH"],              # kg/kg, direct
    "PSRF": df["ps"] * 1000.0,     # kPa -> Pa
    "FSDS": df["Fsd"],             # W/m2
    "FLDS": df["Fld"],             # W/m2
    "WIND": df["Ws"],              # m/s
    "PRECTmms": df["Precip"] / 1800.0,  # mm per 30 min -> mm/s
    "ZBOT": ZBOT,
})

forcing_vars = [
    "TBOT", "QBOT", "PSRF", "FSDS",
    "FLDS", "WIND", "PRECTmms", "ZBOT",
]

if forcing[forcing_vars].isna().any().any():
    raise RuntimeError(
        "Missing values remain in forcing variables:\n"
        + str(forcing[forcing_vars].isna().sum())
    )

forcing.to_csv(OUT_FORCING, index=False)

# EC observations are kept at native half-hourly resolution.
obs = df[["time", "GPP_LT", "NEE_LT"]].copy()
for c in ["GPP_LT", "NEE_LT"]:
    obs.loc[obs[c] <= -9990, c] = np.nan

obs.to_csv(OUT_OBS, index=False)

summary_rows = []
for c in ["Ta", "SH", "ps", "Fsd", "Fld", "Ws", "Precip", "GPP_LT", "NEE_LT"]:
    x = df[c]
    summary_rows.append({
        "variable": c,
        "n": len(x),
        "missing": int(x.isna().sum()),
        "min": float(x.min()) if x.notna().any() else np.nan,
        "max": float(x.max()) if x.notna().any() else np.nan,
    })

pd.DataFrame(summary_rows).to_csv(OUT_QC, index=False)

print("Wrote:", OUT_FORCING)
print("Wrote:", OUT_OBS)
print("Wrote:", OUT_QC)
print("Rows before noleap conversion:", len(forcing))
print()
for c in forcing_vars:
    print(
        f"{c:10s}",
        float(forcing[c].min()),
        "to",
        float(forcing[c].max()),
        "missing =",
        int(forcing[c].isna().sum()),
    )

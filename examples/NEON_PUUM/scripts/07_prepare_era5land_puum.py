#!/usr/bin/env python3

import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE = Path("/iridisfs/scratch/ly3n24/NEON/PUUM")

INDIR = BASE / "ERA5Land" / "netcdf"
OUTDIR = BASE / "processed"

OUTDIR.mkdir(parents=True, exist_ok=True)

OUT_HOURLY = OUTDIR / "PUUM_ERA5Land_hourly_2020_2025.csv"
OUT_30MIN = OUTDIR / "PUUM_ERA5Land_30min_2020_2025_noleap.csv"


# ============================================================
# Read all ERA5-Land NetCDF files
# ============================================================

files = sorted(INDIR.glob("*.nc"))

if len(files) == 0:
    raise RuntimeError(f"No NetCDF files found in {INDIR}")

print("=" * 80)
print("READING ERA5-LAND")
print("=" * 80)

frames = []

for f in files:

    ds = xr.open_dataset(f)

    print(f"\nFILE: {f.name}")
    print("Variables:", list(ds.data_vars))
    print("Dimensions:", dict(ds.sizes))

    if "valid_time" in ds.coords:
        tname = "valid_time"
    elif "time" in ds.coords:
        tname = "time"
    else:
        raise RuntimeError(
            f"Cannot find time coordinate in {f.name}"
        )

    time = pd.to_datetime(
        ds[tname].values,
        utc=True
    )

    tmp = pd.DataFrame(index=time)

    for var in ds.data_vars:

        da = ds[var].squeeze(drop=True)

        if da.ndim != 1:
            raise RuntimeError(
                f"{var} in {f.name} is not 1-D after squeeze: "
                f"dims={da.dims}"
            )

        tmp[var] = da.values

        units = ds[var].attrs.get("units", "UNKNOWN")
        print(f"  {var:10s} units={units}")

    frames.append(tmp)

    ds.close()


# Merge all parameter groups
era = pd.concat(frames, axis=1)

# Protect against accidental duplicated variables
if era.columns.duplicated().any():
    duplicates = era.columns[era.columns.duplicated()].tolist()
    raise RuntimeError(
        f"Duplicated ERA5 variables found: {duplicates}\n"
        "Check whether old and new NetCDF files are mixed together."
    )

era = era.sort_index()

print("\nERA5 merged period:")
print(era.index.min(), "->", era.index.max())
print("Rows:", len(era))
print("Columns:", list(era.columns))


# ============================================================
# Helper for expected ERA variable names
# ============================================================

def find_var(*candidates):

    for c in candidates:
        if c in era.columns:
            return era[c].astype(float)

    raise RuntimeError(
        f"Could not find any of {candidates}\n"
        f"Available variables: {list(era.columns)}"
    )


t2m = find_var("t2m", "2m_temperature")
d2m = find_var("d2m", "2m_dewpoint_temperature")
sp = find_var("sp", "surface_pressure")

ssrd = find_var(
    "ssrd",
    "surface_solar_radiation_downwards"
)

strd = find_var(
    "strd",
    "surface_thermal_radiation_downwards"
)

u10 = find_var(
    "u10",
    "10m_u_component_of_wind"
)

v10 = find_var(
    "v10",
    "10m_v_component_of_wind"
)

tp = find_var(
    "tp",
    "total_precipitation"
)


# ============================================================
# Convert ERA5-Land variables to CLM forcing variables
# ============================================================

hourly = pd.DataFrame(index=era.index)

# ------------------------------------------------------------
# TBOT
# ERA5 t2m is already K
# ------------------------------------------------------------

hourly["TBOT"] = t2m


# ------------------------------------------------------------
# PSRF
# ERA5 surface pressure already Pa
# ------------------------------------------------------------

hourly["PSRF"] = sp


# ------------------------------------------------------------
# QBOT
# derive specific humidity from dew-point temperature
#
# vapour pressure from Bolton-type formulation
# Td in deg C
#
# q = epsilon * e / (p - (1-epsilon)*e)
# ------------------------------------------------------------

Td_C = d2m - 273.15

e = 611.2 * np.exp(
    17.67 * Td_C /
    (Td_C + 243.5)
)

epsilon = 0.622

hourly["QBOT"] = (
    epsilon * e /
    (sp - (1.0 - epsilon) * e)
)


# ------------------------------------------------------------
# WIND
# ------------------------------------------------------------

hourly["WIND"] = np.sqrt(
    u10 ** 2 +
    v10 ** 2
)


# ------------------------------------------------------------
# Radiation
#
# ERA5-Land time-series product provides ssrd/strd as
# hourly DE-ACCUMULATED J m-2.
#
# Convert hourly energy to mean W m-2:
#
# J m-2 / 3600 s = W m-2
# ------------------------------------------------------------

hourly["FSDS"] = ssrd.clip(lower=0.0) / 3600.0
hourly["FLDS"] = strd.clip(lower=0.0) / 3600.0


# ------------------------------------------------------------
# Precipitation
#
# tp:
#     m of water during hour
#
# m -> mm = ×1000
# hourly total -> mm s-1 = /3600
# ------------------------------------------------------------

hourly["PRECTmms"] = (
    tp.clip(lower=0.0)
    * 1000.0
    / 3600.0
)


# ============================================================
# Save standardized hourly ERA5
#
# NOTE:
# FSDS / FLDS / PRECTmms timestamp refers to END of hourly
# accumulation interval.
# ============================================================

hourly_save = hourly.loc[
    "2020-01-01 00:00:00+00:00":
    "2025-12-31 23:00:00+00:00"
].copy()

hourly_save.index.name = "valid_time"
hourly_save.to_csv(OUT_HOURLY)


# ============================================================
# Convert to NEON / CLM 30-minute timeline
# ============================================================

target_full = pd.date_range(
    start="2020-01-01 00:00:00",
    end="2025-12-31 23:30:00",
    freq="30min",
    tz="UTC"
)

out = pd.DataFrame(index=target_full)


# ============================================================
# Instantaneous/state variables
#
# ERA5 values at HH:00 are point-in-time values.
# Linear interpolation provides HH:30.
# Need 2026-01-01 00:00 for final 2025-12-31 23:30.
# ============================================================

state_vars = [
    "TBOT",
    "QBOT",
    "PSRF",
    "WIND",
]

state_index = pd.date_range(
    start="2020-01-01 00:00:00",
    end="2026-01-01 00:00:00",
    freq="30min",
    tz="UTC"
)

for var in state_vars:

    s = hourly[var].reindex(state_index)

    s = s.interpolate(
        method="time",
        limit_direction="both"
    )

    out[var] = s.reindex(target_full)


# ============================================================
# Interval variables
#
# ERA5-Land de-accumulated value at time T represents
# the interval ending at T:
#
#     T-1h -----> T
#
# Our NEON/CLM timestamps represent 30-min interval starts,
# so shift ERA value back by 1 hour:
#
# ERA 01:00 -> applies to:
#     00:00
#     00:30
#
# Then hold the hourly mean rate for both half-hours.
# ============================================================

interval_vars = [
    "FSDS",
    "FLDS",
    "PRECTmms",
]

for var in interval_vars:

    s = hourly[var].copy()

    # Move interval-end timestamp to interval-start timestamp
    s.index = s.index - pd.Timedelta(hours=1)

    # Reindex to 30 min
    s30 = s.reindex(target_full)

    # One hourly value applies to two half-hours
    s30 = s30.ffill(limit=1)

    out[var] = s30


# ============================================================
# Put columns in CLM forcing order
# ============================================================

out = out[
    [
        "TBOT",
        "QBOT",
        "PSRF",
        "FSDS",
        "FLDS",
        "WIND",
        "PRECTmms",
    ]
]


# ============================================================
# Remove Feb 29
# Same convention as PUUM Stage-1 NEON forcing
# ============================================================

leap_day = (
    (out.index.month == 2) &
    (out.index.day == 29)
)

out = out.loc[~leap_day].copy()


# ============================================================
# QC
# ============================================================

print("\n" + "=" * 80)
print("ERA5-LAND 30-MIN PREPARATION COMPLETE")
print("=" * 80)

print("\nPeriod:")
print(out.index.min(), "->", out.index.max())

print("\nRows:")
print(len(out))

print("Expected:")
print(105120)

if len(out) != 105120:
    raise RuntimeError(
        f"Expected 105120 rows, got {len(out)}"
    )


print("\nMissing values:")
print(out.isna().sum())

if out.isna().any().any():

    print("\nERROR: ERA5 forcing still contains missing values.")

    bad = out[out.isna().any(axis=1)]

    print(bad.head(20))

    raise RuntimeError(
        "ERA5-Land 30-min forcing contains NaNs."
    )


print("\nVariable ranges:")

for var in out.columns:

    print(
        f"{var:9s} "
        f"min={out[var].min():12.6f} "
        f"mean={out[var].mean():12.6f} "
        f"max={out[var].max():12.6f}"
    )


# Additional physical checks

if (out["QBOT"] < 0).any():
    raise RuntimeError("Negative QBOT detected.")

if (out["PSRF"] <= 0).any():
    raise RuntimeError("Non-positive PSRF detected.")

if (out["FSDS"] < 0).any():
    raise RuntimeError("Negative FSDS detected.")

if (out["FLDS"] < 0).any():
    raise RuntimeError("Negative FLDS detected.")

if (out["WIND"] < 0).any():
    raise RuntimeError("Negative WIND detected.")

if (out["PRECTmms"] < 0).any():
    raise RuntimeError("Negative PRECTmms detected.")


# ============================================================
# Save
# ============================================================

out.index.name = "time"

out.to_csv(OUT_30MIN)

print("\nFiles written:")
print(OUT_HOURLY)
print(OUT_30MIN)

print("\nSUCCESS")

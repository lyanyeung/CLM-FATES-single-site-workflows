#!/usr/bin/env python3

import numpy as np
import pandas as pd
from pathlib import Path
from netCDF4 import Dataset


# ============================================================
# Configuration
# ============================================================

BASE = Path("/iridisfs/scratch/ly3n24/NEON/PUUM")

INPUT = (
    BASE
    / "processed"
    / "PUUM_forcing_final_QC_2020_2025_noleap.csv"
)

OUTDIR = (
    BASE
    / "CLM_forcing"
    / "1x1pt_PUUM"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)


# PUUM official NEON coordinates
LAT = 19.55309
LON = -155.31731

# NEON PUUM flux/met tower height
ZBOT = 32.0


VARS = [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
    "PRECTmms",
]


UNITS = {
    "TBOT": "K",
    "QBOT": "kg/kg",
    "PSRF": "Pa",
    "FSDS": "W/m2",
    "FLDS": "W/m2",
    "WIND": "m/s",
    "PRECTmms": "mm/s",
}


LONG_NAMES = {
    "TBOT":
        "temperature at the lowest atmospheric level",

    "QBOT":
        "specific humidity at the lowest atmospheric level",

    "PSRF":
        "surface pressure",

    "FSDS":
        "incident downward shortwave radiation",

    "FLDS":
        "incident downward longwave radiation",

    "WIND":
        "wind speed at the lowest atmospheric level",

    "PRECTmms":
        "total precipitation rate",
}


# ============================================================
# Read final forcing
# ============================================================

df = pd.read_csv(INPUT)

df["time"] = pd.to_datetime(
    df["time"],
    utc=True
)

df = df.set_index("time")


print("=" * 80)
print("BUILDING PUUM CLM/DATM FORCING")
print("=" * 80)

print("\nInput:")
print(INPUT)

print("\nPeriod:")
print(df.index.min(), "->", df.index.max())

print("\nRows:")
print(len(df))


if len(df) != 105120:
    raise RuntimeError(
        f"Expected 105120 rows, got {len(df)}"
    )


# ============================================================
# Final input QC
# ============================================================

if df[VARS].isna().any().any():
    raise RuntimeError(
        "Input contains missing forcing values."
    )

if (df["QBOT"] < 0).any():
    raise RuntimeError("Negative QBOT found.")

if (df["PSRF"] <= 0).any():
    raise RuntimeError("Invalid PSRF found.")

if (df["FSDS"] < 0).any():
    raise RuntimeError("Negative FSDS found.")

if (df["FLDS"] < 0).any():
    raise RuntimeError("Negative FLDS found.")

if (df["WIND"] < 0).any():
    raise RuntimeError("Negative WIND found.")

if (df["PRECTmms"] < 0).any():
    raise RuntimeError("Negative precipitation found.")


# ============================================================
# No-leap month lengths
# ============================================================

MONTH_DAYS = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}


# ============================================================
# Write monthly files
# ============================================================

total_written = 0
nfiles = 0


for year in range(2020, 2026):

    for month in range(1, 13):

        subset = df[
            (df.index.year == year)
            &
            (df.index.month == month)
        ].copy()


        expected = (
            MONTH_DAYS[month]
            * 48
        )

        if len(subset) != expected:

            raise RuntimeError(
                f"{year}-{month:02d}: "
                f"expected {expected} rows, "
                f"got {len(subset)}"
            )


        outfile = (
            OUTDIR
            / f"{year:04d}-{month:02d}.nc"
        )


        # Remove existing file
        if outfile.exists():
            outfile.unlink()


        nc = Dataset(
            outfile,
            "w",
            format="NETCDF4_CLASSIC"
        )


        # ----------------------------------------------------
        # Dimensions
        # ----------------------------------------------------

        nc.createDimension(
            "lat",
            1
        )

        nc.createDimension(
            "lon",
            1
        )

        # Unlimited time dimension
        nc.createDimension(
            "time",
            None
        )


        # ----------------------------------------------------
        # Global attributes
        # ----------------------------------------------------

        nc.title = (
            "PUUM single-point atmospheric forcing "
            "for CLM-FATES"
        )

        nc.site_code = "PUUM"

        nc.site_name = (
            "NEON Pu'u Maka'ala Natural Area Reserve"
        )

        nc.Conventions = "CF-1.6"

        nc.calendar = "noleap"

        nc.source = (
            "NEON observations with short-gap interpolation "
            "and bias-corrected ERA5-Land gap filling"
        )

        nc.latitude = LAT
        nc.longitude = LON
        nc.tower_height_m = ZBOT


        # ----------------------------------------------------
        # Coordinates
        # ----------------------------------------------------

        lat = nc.createVariable(
            "lat",
            "f8",
            ("lat",)
        )

        lon = nc.createVariable(
            "lon",
            "f8",
            ("lon",)
        )

        lat[:] = [LAT]
        lon[:] = [LON]

        lat.units = "degrees_north"
        lon.units = "degrees_east"


        # ----------------------------------------------------
        # LATIXY / LONGXY
        # Classic DATM coordinate fields
        # ----------------------------------------------------

        latixy = nc.createVariable(
            "LATIXY",
            "f8",
            ("lat", "lon")
        )

        longxy = nc.createVariable(
            "LONGXY",
            "f8",
            ("lat", "lon")
        )

        latixy[:, :] = LAT
        longxy[:, :] = LON

        latixy.units = "degrees_north"
        longxy.units = "degrees_east"

        latixy.long_name = "latitude"
        longxy.long_name = "longitude"


        # ----------------------------------------------------
        # Time
        #
        # 30-min no-leap forcing:
        #
        # 00:00 -> 0
        # 00:30 -> 1/48 day
        # 01:00 -> 2/48 day
        # ...
        # ----------------------------------------------------

        time = nc.createVariable(
            "time",
            "f8",
            ("time",)
        )

        time[:] = (
            np.arange(
                len(subset),
                dtype=np.float64
            )
            / 48.0
        )

        time.units = (
            f"days since "
            f"{year:04d}-{month:02d}-01 "
            f"00:00:00"
        )

        time.calendar = "noleap"

        time.long_name = "Time axis"


        # ----------------------------------------------------
        # Atmospheric forcing variables
        # ----------------------------------------------------

        for var in VARS:

            v = nc.createVariable(
                var,
                "f4",
                ("time", "lat", "lon")
            )

            values = (
                subset[var]
                .to_numpy(dtype=np.float32)
                [:, None, None]
            )

            v[:, :, :] = values

            v.units = UNITS[var]
            v.long_name = LONG_NAMES[var]


        # ----------------------------------------------------
        # ZBOT
        # reference measurement height
        # ----------------------------------------------------

        zbot = nc.createVariable(
            "ZBOT",
            "f4",
            ("time", "lat", "lon")
        )

        zbot[:, :, :] = np.full(
            (
                len(subset),
                1,
                1
            ),
            ZBOT,
            dtype=np.float32
        )

        zbot.units = "m"

        zbot.long_name = (
            "atmospheric forcing measurement height"
        )


        nc.close()


        print(
            f"Wrote {outfile.name}: "
            f"{len(subset)} records"
        )

        total_written += len(subset)
        nfiles += 1


# ============================================================
# Final checks
# ============================================================

print("\n" + "=" * 80)
print("CLM/DATM NETCDF COMPLETE")
print("=" * 80)

print("\nFiles:")
print(nfiles)

print("Expected files:")
print(72)

print("\nTotal records:")
print(total_written)

print("Expected records:")
print(105120)

if nfiles != 72:
    raise RuntimeError(
        f"Expected 72 files, got {nfiles}"
    )

if total_written != 105120:
    raise RuntimeError(
        f"Expected 105120 records, got {total_written}"
    )


print("\nOutput directory:")
print(OUTDIR)

print("\nSUCCESS")

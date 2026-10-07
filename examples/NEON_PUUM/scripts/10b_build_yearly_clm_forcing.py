#!/usr/bin/env python3

import numpy as np
import pandas as pd
from pathlib import Path
from netCDF4 import Dataset

BASE = Path("/iridisfs/scratch/ly3n24/NEON/PUUM")

INPUT = (
    BASE / "processed"
    / "PUUM_forcing_final_QC_2020_2025_noleap.csv"
)

OUTDIR = BASE / "CLM_forcing" / "yearly"
OUTDIR.mkdir(parents=True, exist_ok=True)

LAT = 19.55309
LON = -155.31731
ZBOT = 32.0

VARS = [
    "PRECTmms",
    "FSDS",
    "ZBOT",
    "TBOT",
    "WIND",
    "QBOT",
    "PSRF",
    "FLDS",
]

UNITS = {
    "PRECTmms": "mm/s",
    "FSDS": "W/m2",
    "ZBOT": "m",
    "TBOT": "K",
    "WIND": "m/s",
    "QBOT": "kg/kg",
    "PSRF": "Pa",
    "FLDS": "W/m2",
}

# ------------------------------------------------------------
# Read
# ------------------------------------------------------------

df = pd.read_csv(INPUT)

df["time"] = pd.to_datetime(
    df["time"],
    utc=True
)

df = df.set_index("time")

if len(df) != 105120:
    raise RuntimeError(
        f"Expected 105120 rows, got {len(df)}"
    )

print("=" * 80)
print("BUILDING YEARLY PUUM DATM FILES")
print("=" * 80)

# ------------------------------------------------------------
# Each year
# ------------------------------------------------------------

for year in range(2020, 2026):

    x = df[df.index.year == year].copy()

    # no-leap
    if len(x) != 17520:
        raise RuntimeError(
            f"{year}: expected 17520 records, got {len(x)}"
        )

    outfile = OUTDIR / f"PUUM_forcing_{year}.nc"

    if outfile.exists():
        outfile.unlink()

    nc = Dataset(
        outfile,
        "w",
        format="NETCDF4_CLASSIC"
    )

    nc.createDimension("lat", 1)
    nc.createDimension("lon", 1)
    nc.createDimension("time", None)

    # --------------------------------------------------------
    # coordinates
    # --------------------------------------------------------

    lat = nc.createVariable(
        "lat", "f8", ("lat",)
    )

    lon = nc.createVariable(
        "lon", "f8", ("lon",)
    )

    lat[:] = [LAT]
    lon[:] = [LON]

    lat.units = "degrees_north"
    lon.units = "degrees_east"

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

    # --------------------------------------------------------
    # time
    # --------------------------------------------------------

    time = nc.createVariable(
        "time",
        "f8",
        ("time",)
    )

    time[:] = (
        np.arange(
            len(x),
            dtype=np.float64
        )
        / 48.0
    )

    time.units = (
        f"days since {year}-01-01 00:00:00"
    )

    time.calendar = "noleap"
    time.long_name = "time"

    # --------------------------------------------------------
    # forcing
    # --------------------------------------------------------

    for var in VARS:

        v = nc.createVariable(
            var,
            "f4",
            ("time", "lat", "lon")
        )

        if var == "ZBOT":

            values = np.full(
                len(x),
                ZBOT,
                dtype=np.float32
            )

        else:

            values = (
                x[var]
                .to_numpy(dtype=np.float32)
            )

        v[:, 0, 0] = values
        v.units = UNITS[var]

    # --------------------------------------------------------
    # global attributes
    # --------------------------------------------------------

    nc.title = (
        "PUUM single-site CLM-FATES forcing"
    )

    nc.site_code = "PUUM"
    nc.calendar = "noleap"

    nc.source = (
        "NEON observations with short-gap interpolation "
        "and bias-corrected ERA5-Land gap filling"
    )

    nc.close()

    print(
        f"{year}: {outfile.name} "
        f"({len(x)} records)"
    )

print("\nOutput:")
print(OUTDIR)

print("\nSUCCESS")

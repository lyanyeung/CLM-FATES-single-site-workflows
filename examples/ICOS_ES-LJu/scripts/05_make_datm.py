#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd
import numpy as np
from netCDF4 import Dataset

USER = os.environ.get("IRIDIS_USER", "ly3n24")
SITE = "ES-LJu"
ROOT = Path(f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/{SITE}")

CSV = ROOT / "forcing/processed/ES-LJu_CLM_forcing_2004_2024.csv"
OUTDIR = ROOT / "forcing/datm"
OUTDIR.mkdir(parents=True, exist_ok=True)

LAT = 36.926594
LON = -2.752115
ZBOT = 2.5

df = pd.read_csv(CSV)
df["time"] = pd.to_datetime(df["time"])

forcing_vars = [
    "TBOT", "QBOT", "PSRF", "FSDS",
    "FLDS", "WIND", "PRECTmms", "ZBOT",
]

if len(df) != 367920:
    raise RuntimeError(f"Expected 367920 total records, found {len(df)}")

if df[forcing_vars].isna().any().any():
    raise RuntimeError(
        "Missing forcing values:\n"
        + str(df[forcing_vars].isna().sum())
    )

for f in OUTDIR.glob("ES-LJu_DATM_*.nc"):
    f.unlink()

for year in range(2004, 2025):
    x = (
        df[df["time"].dt.year == year]
        .sort_values("time")
        .reset_index(drop=True)
    )

    if len(x) != 17520:
        raise RuntimeError(f"{year}: expected 17520 records, found {len(x)}")

    outfile = OUTDIR / f"ES-LJu_DATM_{year}.nc"
    print("Writing", outfile)

    nc = Dataset(outfile, "w", format="NETCDF4_CLASSIC")

    nc.createDimension("time", 17520)
    nc.createDimension("lat", 1)
    nc.createDimension("lon", 1)

    time = nc.createVariable("time", "f8", ("time",))
    time.units = f"days since {year}-01-01 00:00:00"
    time.calendar = "noleap"
    time[:] = np.arange(17520, dtype=np.float64) / 48.0

    lat = nc.createVariable("lat", "f8", ("lat",))
    lat.units = "degrees_north"
    lat[:] = LAT

    lon = nc.createVariable("lon", "f8", ("lon",))
    lon.units = "degrees_east"
    lon[:] = LON

    def make_float_var(name, long_name, units):
        v = nc.createVariable(
            name,
            "f4",
            ("time", "lat", "lon"),
            fill_value=np.float32(1.0e36),
        )
        v.long_name = long_name
        v.units = units
        return v

    vars_nc = {
        "TBOT": make_float_var("TBOT", "air temperature", "K"),
        "QBOT": make_float_var("QBOT", "specific humidity", "kg/kg"),
        "PSRF": make_float_var("PSRF", "surface atmospheric pressure", "Pa"),
        "FSDS": make_float_var("FSDS", "downward shortwave radiation", "W/m2"),
        "FLDS": make_float_var("FLDS", "downward longwave radiation", "W/m2"),
        "WIND": make_float_var("WIND", "wind speed", "m/s"),
        "PRECTmms": make_float_var("PRECTmms", "precipitation rate", "mm/s"),
    }

    latixy = nc.createVariable("LATIXY", "f8", ("lat", "lon"))
    latixy.units = "degrees_north"
    latixy[:, :] = LAT

    longxy = nc.createVariable("LONGXY", "f8", ("lat", "lon"))
    longxy.units = "degrees_east"
    longxy[:, :] = LON

    zbot = nc.createVariable("ZBOT", "f8", ("time", "lat", "lon"))
    zbot.long_name = "atmospheric forcing measurement height"
    zbot.units = "m"

    for name, var in vars_nc.items():
        var[:, 0, 0] = x[name].to_numpy(dtype=np.float32)

    zbot[:, 0, 0] = ZBOT

    nc.title = "ES-LJu half-hourly forcing for CTSM/FATES"
    nc.site = "ES-LJu"
    nc.source = "EUF ES-LJu FLUXNET 2004-2024 v1.3 r1"
    nc.calendar = "noleap"
    nc.time_resolution = "30 minutes"
    nc.latitude = LAT
    nc.longitude = LON
    nc.forcing_year = year

    nc.close()

print("\nDATM generation complete.")
print("Files:", len(list(OUTDIR.glob("ES-LJu_DATM_*.nc"))))

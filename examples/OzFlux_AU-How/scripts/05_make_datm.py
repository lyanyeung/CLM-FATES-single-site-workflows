#!/usr/bin/env python3
from pathlib import Path
import os
import numpy as np
import pandas as pd
from netCDF4 import Dataset

USER = os.environ.get("IRIDIS_USER", "ly3n24")
ROOT = Path(f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/AU-How")

CSV = ROOT / "forcing/processed/AU-How_CLM_forcing_2003_2025.csv"
OUTDIR = ROOT / "forcing/datm"
OUTDIR.mkdir(parents=True, exist_ok=True)

LAT = -12.4952
LON = 131.15005
ZBOT = 23.0

df = pd.read_csv(CSV)
df["time"] = pd.to_datetime(df["time"])

# CTSM case uses NO_LEAP.
df = df[
    ~((df["time"].dt.month == 2) & (df["time"].dt.day == 29))
].copy()

forcing_vars = [
    "TBOT", "QBOT", "PSRF", "FSDS",
    "FLDS", "WIND", "PRECTmms", "ZBOT",
]

if len(df) != 23 * 17520:
    raise RuntimeError(f"Expected {23*17520} noleap records, found {len(df)}")

if df[forcing_vars].isna().any().any():
    raise RuntimeError(
        "Missing forcing values:\n" + str(df[forcing_vars].isna().sum())
    )

for f in OUTDIR.glob("AU-How_DATM_*.nc"):
    f.unlink()

for year in range(2003, 2026):
    x = (
        df[df["time"].dt.year == year]
        .sort_values("time")
        .reset_index(drop=True)
    )

    if len(x) != 17520:
        raise RuntimeError(f"{year}: expected 17520 records, found {len(x)}")

    outfile = OUTDIR / f"AU-How_DATM_{year}.nc"
    print("Writing", outfile)

    nc = Dataset(outfile, "w", format="NETCDF4_CLASSIC")

    nc.createDimension("time", 17520)
    nc.createDimension("lat", 1)
    nc.createDimension("lon", 1)

    time = nc.createVariable("time", "f8", ("time",))
    time.units = f"days since {year}-01-01 00:00:00"
    time.calendar = "noleap"

    # Historical successful AU-How writer placed 30-min forcing at
    # interval centers: 00:15, 00:45, ...
    time[:] = (np.arange(17520, dtype=np.float64) + 0.5) / 48.0

    lat = nc.createVariable("lat", "f8", ("lat",))
    lat.units = "degrees_north"
    lat[:] = LAT

    lon = nc.createVariable("lon", "f8", ("lon",))
    lon.units = "degrees_east"
    lon[:] = LON

    def make_float(name, long_name, units):
        v = nc.createVariable(
            name, "f4", ("time", "lat", "lon"),
            fill_value=np.float32(1.0e36)
        )
        v.long_name = long_name
        v.units = units
        return v

    vv = {
        "TBOT": make_float("TBOT", "air temperature", "K"),
        "QBOT": make_float("QBOT", "specific humidity", "kg/kg"),
        "PSRF": make_float("PSRF", "surface atmospheric pressure", "Pa"),
        "FSDS": make_float("FSDS", "downward shortwave radiation", "W/m2"),
        "FLDS": make_float("FLDS", "downward longwave radiation", "W/m2"),
        "WIND": make_float("WIND", "wind speed", "m/s"),
        "PRECTmms": make_float("PRECTmms", "precipitation rate", "mm/s"),
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

    for name, var in vv.items():
        var[:, 0, 0] = x[name].to_numpy(dtype=np.float32)

    zbot[:, 0, 0] = ZBOT

    nc.title = "AU-How half-hourly forcing for CTSM/FATES"
    nc.site = "AU-How"
    nc.source = "OzFlux HowardSprings_L6.nc"
    nc.calendar = "noleap"
    nc.time_resolution = "30 minutes"
    nc.latitude = LAT
    nc.longitude = LON
    nc.forcing_year = year

    nc.close()

print("\nDATM generation complete.")
print("Files:", len(list(OUTDIR.glob("AU-How_DATM_*.nc"))))

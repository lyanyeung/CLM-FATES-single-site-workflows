import os
import numpy as np
import pandas as pd
from netCDF4 import Dataset

SITE = "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Ha1"

INPUT = os.path.join(
    SITE,
    "forcing/processed/US-Ha1_CLM_forcing_1991_2025.csv"
)

OUTDIR = os.path.join(
    SITE,
    "datm"
)

LAT = 42.5378
LON = -72.1715

START_YEAR = 1991
END_YEAR = 2025

os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(INPUT)
df["time"] = pd.to_datetime(df["time"])

vars_out = [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
    "PRECTmms",
    "ZBOT",
]

units = {
    "TBOT": "K",
    "QBOT": "kg/kg",
    "PSRF": "Pa",
    "FSDS": "W/m2",
    "FLDS": "W/m2",
    "WIND": "m/s",
    "PRECTmms": "mm/s",
    "ZBOT": "m",
}

long_names = {
    "TBOT": "air temperature at reference height",
    "QBOT": "specific humidity at reference height",
    "PSRF": "surface atmospheric pressure",
    "FSDS": "downward shortwave radiation",
    "FLDS": "downward longwave radiation",
    "WIND": "wind speed at reference height",
    "PRECTmms": "precipitation rate",
    "ZBOT": "reference height",
}

print("Input rows:", len(df))

for year in range(START_YEAR, END_YEAR + 1):

    d = df[df["time"].dt.year == year].copy()
    d = d.sort_values("time").reset_index(drop=True)

    if len(d) != 8760:
        raise RuntimeError(
            f"{year}: expected 8760 rows, found {len(d)}"
        )

    if d[vars_out].isna().any().any():
        print(d[vars_out].isna().sum())
        raise RuntimeError(
            f"{year}: missing forcing values found"
        )

    outfile = os.path.join(
        OUTDIR,
        f"US-Ha1_forcing_{year}.nc"
    )

    with Dataset(
        outfile,
        "w",
        format="NETCDF4_CLASSIC"
    ) as nc:

        # ------------------------------
        # Dimensions
        # ------------------------------
        nc.createDimension("time", None)
        nc.createDimension("lat", 1)
        nc.createDimension("lon", 1)
        nc.createDimension("nbnd", 2)

        # ------------------------------
        # Coordinates
        # ------------------------------
        time = nc.createVariable(
            "time",
            "f8",
            ("time",)
        )

        time_bnds = nc.createVariable(
            "time_bnds",
            "f8",
            ("time", "nbnd")
        )

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

        LATIXY = nc.createVariable(
            "LATIXY",
            "f8",
            ("lat", "lon")
        )

        LONGXY = nc.createVariable(
            "LONGXY",
            "f8",
            ("lat", "lon")
        )

        lat[:] = LAT
        lon[:] = LON

        LATIXY[:, :] = LAT
        LONGXY[:, :] = LON

        lat.units = "degrees_north"
        lon.units = "degrees_east"

        LATIXY.units = "degrees_north"
        LONGXY.units = "degrees_east"

        # ------------------------------
        # Time
        # Each forcing record is an
        # hourly interval centred at
        # 00:30, 01:30, ...
        # ------------------------------
        n = len(d)

        time[:] = (
            np.arange(n, dtype=float) + 0.5
        ) / 24.0

        time_bnds[:, 0] = (
            np.arange(n, dtype=float)
        ) / 24.0

        time_bnds[:, 1] = (
            np.arange(n, dtype=float) + 1.0
        ) / 24.0

        time.units = (
            f"days since {year}-01-01 00:00:00"
        )

        time.calendar = "noleap"
        time.long_name = "time"
        time.bounds = "time_bnds"

        # ------------------------------
        # Forcing variables
        # ------------------------------
        for v in vars_out:

            x = nc.createVariable(
                v,
                "f4",
                ("time", "lat", "lon"),
                zlib=True,
                complevel=1
            )

            x[:, 0, 0] = d[v].to_numpy(
                dtype=np.float32
            )

            x.units = units[v]
            x.long_name = long_names[v]

        # ------------------------------
        # Global attributes
        # ------------------------------
        nc.title = (
            f"US-Ha1 hourly CLM-FATES forcing {year}"
        )

        nc.site_id = "US-Ha1"
        nc.latitude = LAT
        nc.longitude = LON
        nc.calendar = "noleap"
        nc.temporal_resolution = "hourly"

    print(
        f"{year}: wrote {outfile} "
        f"({len(d)} records)"
    )

print("\nDone.")
print(
    f"Created {END_YEAR - START_YEAR + 1} "
    f"annual DATM files."
)

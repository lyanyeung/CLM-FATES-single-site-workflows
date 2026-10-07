#!/usr/bin/env python3

from pathlib import Path
import cdsapi
import zipfile

# ============================================================
# PUUM
# ============================================================

LAT = 19.5531
LON = -155.3173

START_DATE = "2020-01-01"
END_DATE   = "2026-01-01"

OUTDIR = Path(
    "/iridisfs/scratch/ly3n24/NEON/PUUM/ERA5Land"
)

OUTDIR.mkdir(parents=True, exist_ok=True)

ZIPFILE = OUTDIR / "PUUM_ERA5Land_2020_2026-01-01.zip"


# ============================================================
# ERA5-Land variables needed for CLM-FATES
# ============================================================

variables = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "surface_pressure",

    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",

    "10m_u_component_of_wind",
    "10m_v_component_of_wind",

    "total_precipitation",
]


# ============================================================
# CDS request
# ============================================================

dataset = "reanalysis-era5-land-timeseries"

request = {
    "variable": variables,

    "location": {
        "longitude": LON,
        "latitude": LAT,
    },

    "date": [
        f"{START_DATE}/{END_DATE}"
    ],

    "data_format": "netcdf",
}


print("=" * 70)
print("Downloading ERA5-Land for PUUM")
print("=" * 70)

print(f"Location: {LAT}, {LON}")
print(f"Period:   {START_DATE} -> {END_DATE}")
print(f"Output:   {ZIPFILE}")

client = cdsapi.Client()

client.retrieve(
    dataset,
    request,
    str(ZIPFILE)
)

print("\nDownload complete.")


# ============================================================
# Extract NetCDF files
# ============================================================

EXTRACT_DIR = OUTDIR / "netcdf"
EXTRACT_DIR.mkdir(exist_ok=True)

if zipfile.is_zipfile(ZIPFILE):

    print("\nExtracting NetCDF files...")

    with zipfile.ZipFile(ZIPFILE, "r") as z:
        z.extractall(EXTRACT_DIR)

    print(f"Extracted to:")
    print(EXTRACT_DIR)

else:

    print("\nWARNING:")
    print("Downloaded object is not a ZIP archive.")
    print("Check file type manually.")


print("\nFinished.")

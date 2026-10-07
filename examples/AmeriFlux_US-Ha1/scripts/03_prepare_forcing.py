import os
import numpy as np
import pandas as pd

SITE = "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Ha1"

RAW = os.path.join(
    SITE,
    "forcing/raw/AMF_US-Ha1_FLUXNET_FLUXMET_HR_1991-2025_v1.3_r1.csv"
)

OUT_FORCING = os.path.join(
    SITE,
    "forcing/processed/US-Ha1_CLM_forcing_1991_2025.csv"
)

OUT_OBS = os.path.join(
    SITE,
    "obs/US-Ha1_EC_GPP_NEE_DT_1991_2025.csv"
)

OUT_QC = os.path.join(
    SITE,
    "forcing/processed/US-Ha1_forcing_replacements.csv"
)

ZBOT = 27.9
EXPECTED_ROWS = 35 * 365 * 24

# --------------------------------------------------
# Read
# --------------------------------------------------
df = pd.read_csv(RAW)

df["time"] = pd.to_datetime(
    df["TIMESTAMP_START"].astype(str),
    format="%Y%m%d%H%M"
)

numeric_cols = [
    "TA_F", "TA_ERA",
    "VPD_F", "VPD_ERA",
    "PA_F",
    "SW_IN_F",
    "LW_IN_F",
    "WS_F",
    "P_F",
    "GPP_DT_VUT_REF",
    "NEE_VUT_REF",
    "NEE_VUT_REF_QC",
]

for c in numeric_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# AmeriFlux missing flag
for c in numeric_cols:
    if c != "NEE_VUT_REF_QC":
        df.loc[df[c] <= -9990, c] = np.nan

qc_records = []

# --------------------------------------------------
# Fix three known isolated forcing errors
# --------------------------------------------------
def replace_adjacent_mean(column, timestamp):
    t = pd.Timestamp(timestamp)

    idx = df.index[df["time"] == t]

    if len(idx) != 1:
        raise RuntimeError(
            f"{timestamp}: expected one row, found {len(idx)}"
        )

    i = idx[0]

    old = df.loc[i, column]
    before = df.loc[i - 1, column]
    after = df.loc[i + 1, column]

    if pd.isna(before) or pd.isna(after):
        raise RuntimeError(
            f"Cannot interpolate {column} at {timestamp}"
        )

    new = (before + after) / 2.0

    df.loc[i, column] = new

    qc_records.append({
        "time": t,
        "variable": column,
        "old_value": old,
        "new_value": new,
        "method": "mean_of_adjacent_hours",
    })


replace_adjacent_mean(
    "LW_IN_F",
    "2004-12-04 00:00"
)

replace_adjacent_mean(
    "PA_F",
    "2004-12-04 01:00"
)

replace_adjacent_mean(
    "LW_IN_F",
    "2016-10-09 19:00"
)

# --------------------------------------------------
# Remove Feb 29
# --------------------------------------------------
is_feb29 = (
    (df["time"].dt.month == 2) &
    (df["time"].dt.day == 29)
)

df = df.loc[~is_feb29].copy()
df = df.reset_index(drop=True)

if len(df) != EXPECTED_ROWS:
    raise RuntimeError(
        f"Rows after removing Feb29 = {len(df)}, "
        f"expected {EXPECTED_ROWS}"
    )

annual_counts = df.groupby(df["time"].dt.year).size()

bad_years = annual_counts[annual_counts != 8760]

if len(bad_years) > 0:
    raise RuntimeError(
        "Years not containing 8760 hours:\n"
        + bad_years.to_string()
    )

# --------------------------------------------------
# Joint TA-VPD physical QC
# --------------------------------------------------
TA_USE = df["TA_F"].copy()
VPD_USE = df["VPD_F"].copy()

es_f = 6.112 * np.exp(
    17.67 * TA_USE /
    (TA_USE + 243.5)
)

ea_f = es_f - VPD_USE

RH_f = 100.0 * ea_f / es_f

# Joint physical QC:
# replace TA and VPD together when actual vapour pressure is
# non-positive OR relative humidity is unrealistically low.
bad_tv = (
    (ea_f <= 0) |
    (RH_f < 1.0)
)

print(
    "\nTA/VPD combinations requiring ERA replacement:",
    bad_tv.sum()
)

# Check ERA replacement itself
es_era = 6.112 * np.exp(
    17.67 * df["TA_ERA"] /
    (df["TA_ERA"] + 243.5)
)

ea_era = es_era - df["VPD_ERA"]
RH_era = 100.0 * ea_era / es_era

bad_era = (
    bad_tv &
    (
        df["TA_ERA"].isna() |
        df["VPD_ERA"].isna() |
        (ea_era <= 0) |
        (RH_era < 1.0)
    )
)

if bad_era.any():
    raise RuntimeError(
        "ERA replacement is invalid for some TA/VPD rows:\n"
        + df.loc[
            bad_era,
            ["time", "TA_F", "VPD_F", "TA_ERA", "VPD_ERA"]
        ].to_string(index=False)
    )

# Log and replace both TA and VPD together
for i in df.index[bad_tv]:
    qc_records.append({
        "time": df.loc[i, "time"],
        "variable": "TA_F",
        "old_value": df.loc[i, "TA_F"],
        "new_value": df.loc[i, "TA_ERA"],
        "method": "replace_TA_VPD_pair_with_ERA",
    })

    qc_records.append({
        "time": df.loc[i, "time"],
        "variable": "VPD_F",
        "old_value": df.loc[i, "VPD_F"],
        "new_value": df.loc[i, "VPD_ERA"],
        "method": "replace_TA_VPD_pair_with_ERA",
    })

TA_USE.loc[bad_tv] = df.loc[bad_tv, "TA_ERA"]
VPD_USE.loc[bad_tv] = df.loc[bad_tv, "VPD_ERA"]

# --------------------------------------------------
# Build CLM forcing
# --------------------------------------------------

# deg C -> K
TBOT = TA_USE + 273.15

# kPa -> Pa
PSRF = df["PA_F"] * 1000.0

# Actual vapour pressure
es_hPa = 6.112 * np.exp(
    17.67 * TA_USE /
    (TA_USE + 243.5)
)

ea_hPa = es_hPa - VPD_USE

RH = 100.0 * ea_hPa / es_hPa

if (ea_hPa <= 0).any():
    raise RuntimeError(
        "Non-positive vapour pressure remains after QC."
    )

if (RH < 1.0).any():
    raise RuntimeError(
        "Relative humidity below 1% remains after QC."
    )

ea_Pa = ea_hPa * 100.0

# specific humidity kg kg-1
QBOT = (
    0.622 * ea_Pa /
    (PSRF - 0.378 * ea_Pa)
)

FSDS = df["SW_IN_F"]
FLDS = df["LW_IN_F"]
WIND = df["WS_F"]

# P_F is mm per hourly interval
PRECTmms = df["P_F"] / 3600.0

forcing = pd.DataFrame({
    "time": df["time"],
    "TBOT": TBOT,
    "QBOT": QBOT,
    "PSRF": PSRF,
    "FSDS": FSDS,
    "FLDS": FLDS,
    "WIND": WIND,
    "PRECTmms": PRECTmms,
    "ZBOT": ZBOT,
})

# --------------------------------------------------
# Observation file
# --------------------------------------------------
obs = df[
    [
        "time",
        "GPP_DT_VUT_REF",
        "NEE_VUT_REF",
        "NEE_VUT_REF_QC",
    ]
].copy()

obs.to_csv(OUT_OBS, index=False)

# --------------------------------------------------
# Final QC
# --------------------------------------------------
forcing_vars = [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
    "PRECTmms",
    "ZBOT",
]

missing = forcing[forcing_vars].isna().sum()

if missing.sum() != 0:
    raise RuntimeError(
        "Missing forcing values remain:\n"
        + missing.to_string()
    )

checks = {
    "TBOT": (180, 330),
    "QBOT": (0, 0.05),
    "PSRF": (80000, 110000),
    "FSDS": (0, 1500),
    "FLDS": (100, 600),
    "WIND": (0, 60),
    "PRECTmms": (0, 0.1),
}

for v, (lo, hi) in checks.items():

    bad = (
        (forcing[v] < lo) |
        (forcing[v] > hi)
    )

    if bad.any():
        print(
            f"\nWARNING: {v} outside nominal range "
            f"({bad.sum()} rows)"
        )

        print(
            forcing.loc[
                bad,
                ["time", v]
            ].head(20).to_string(index=False)
        )

# RH already calculated above

forcing.to_csv(
    OUT_FORCING,
    index=False
)

pd.DataFrame(qc_records).to_csv(
    OUT_QC,
    index=False
)

# --------------------------------------------------
# Report
# --------------------------------------------------
print("\n==========================================")
print("US-Ha1 forcing preparation complete")
print("==========================================")

print("\nRows after Feb29 removal:")
print(len(forcing))

print("\nExpected rows:")
print(EXPECTED_ROWS)

print("\nPeriod:")
print(
    forcing["time"].iloc[0],
    "to",
    forcing["time"].iloc[-1]
)

print("\nForcing ranges:")

for v in forcing_vars:
    print(
        f"{v:10s}"
        f" min={forcing[v].min():.8g}"
        f" max={forcing[v].max():.8g}"
    )

print("\nHumidity diagnostics:")
print("ea_hPa min =", ea_hPa.min())
print("RH min (%) =", RH.min())
print("RH max (%) =", RH.max())

print("\nCorrections summary:")
print(
    pd.DataFrame(qc_records)
    .groupby(["method", "variable"])
    .size()
)

print("\nTotal correction log rows:")
print(len(qc_records))

print("\nFiles written:")
print(OUT_FORCING)
print(OUT_OBS)
print(OUT_QC)

#!/usr/bin/env python3

from pathlib import Path
import zipfile
import re
import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/NEON/PUUM")
PROC = ROOT / "processed"
PROC.mkdir(exist_ok=True)

MASTER = PROC / "PUUM_master_30min_2019_2026.csv"

ZBOT = 32.76


# ============================================================
# Helpers
# ============================================================

def load_neon_csv_series(
    folder,
    dpid,
    table_token,
    hor,
    ver,
    value_col,
    qf_col,
):
    """
    Load one exact NEON sensor position from all monthly ZIPs.
    Only finalQF == 0 is retained.
    """

    folder = ROOT / folder
    frames = []

    pattern = re.compile(
        re.escape(dpid)
        + rf"\.{hor}\.{ver}\.030\."
    )

    for zp in sorted(folder.glob("*.zip")):

        with zipfile.ZipFile(zp) as z:

            matches = [
                name for name in z.namelist()
                if name.lower().endswith(".csv")
                and table_token in name
                and pattern.search(name)
            ]

            if not matches:
                continue

            for name in matches:

                with z.open(name) as f:
                    d = pd.read_csv(f)

                if value_col not in d.columns:
                    continue

                d["time"] = pd.to_datetime(
                    d["startDateTime"],
                    utc=True,
                    errors="coerce",
                )

                value = pd.to_numeric(
                    d[value_col],
                    errors="coerce",
                )

                qf = pd.to_numeric(
                    d[qf_col],
                    errors="coerce",
                )

                value = value.where(qf == 0)

                frames.append(
                    pd.DataFrame({
                        "time": d["time"],
                        "value": value,
                    })
                )

    if not frames:
        raise RuntimeError(
            f"No data found for {dpid} "
            f"{hor}.{ver} {value_col}"
        )

    out = pd.concat(
        frames,
        ignore_index=True
    )

    out = (
        out
        .dropna(subset=["time"])
        .sort_values("time")
        .drop_duplicates("time")
        .reset_index(drop=True)
    )

    return out.set_index("time")["value"]


def combine_sources(index, sources):
    """
    sources = [
        ("SOURCE_NAME", pandas_series),
        ...
    ]

    Fill only missing values, in priority order.
    """

    value = pd.Series(
        np.nan,
        index=index,
        dtype=float,
    )

    source = pd.Series(
        "MISSING",
        index=index,
        dtype="object",
    )

    for name, series in sources:

        s = series.reindex(index)

        use = (
            value.isna()
            & s.notna()
        )

        value.loc[use] = s.loc[use]
        source.loc[use] = name

    is_raw = (
        source != "MISSING"
    ).astype(int)

    return value, source, is_raw


def buck_q_from_rh(T_K, RH_pct, P_Pa):
    """
    Convert RH + temperature + pressure to specific humidity.

    Buck saturation vapour pressure approximation.

    Returns kg H2O / kg moist air.
    """

    T_C = T_K - 273.15

    RH = RH_pct.clip(
        lower=0.0,
        upper=100.0,
    )

    # saturation vapour pressure, kPa
    es = (
        0.61121
        * np.exp(
            (
                18.678
                - T_C / 234.5
            )
            * (
                T_C
                / (257.14 + T_C)
            )
        )
    )

    e = (RH / 100.0) * es

    p = P_Pa / 1000.0

    q = (
        0.622 * e
        / (p - 0.378 * e)
    )

    return q


# ============================================================
# Load existing EC extraction
# ============================================================

print("Loading EC/master data...")

master = pd.read_csv(
    MASTER,
    parse_dates=["time"],
)

master["time"] = pd.to_datetime(
    master["time"],
    utc=True,
)

master = (
    master
    .sort_values("time")
    .drop_duplicates("time")
    .set_index("time")
)

idx = master.index


# ============================================================
# Standalone NEON meteorology
# ============================================================

print("Loading standalone TBOT...")

ta_top = load_neon_csv_series(
    "filesToStack00003",
    "DP1.00003.001",
    "TAAT_30min",
    "000",
    "060",
    "tempTripleMean",
    "finalQF",
)

ta_top = ta_top + 273.15


print("Loading standalone pressure...")

pa = load_neon_csv_series(
    "filesToStack00004",
    "DP1.00004.001",
    "BP_30min",
    "000",
    "025",
    "staPresMean",
    "staPresFinalQF",
)

pa = pa * 1000.0


print("Loading radiation...")

sw_top = load_neon_csv_series(
    "filesToStack00023",
    "DP1.00023.001",
    "SLRNR_30min",
    "000",
    "060",
    "inSWMean",
    "inSWFinalQF",
)

lw_top = load_neon_csv_series(
    "filesToStack00023",
    "DP1.00023.001",
    "SLRNR_30min",
    "000",
    "060",
    "inLWMean",
    "inLWFinalQF",
)

lw_ground = load_neon_csv_series(
    "filesToStack00023",
    "DP1.00023.001",
    "SLRNR_30min",
    "002",
    "000",
    "inLWMean",
    "inLWFinalQF",
)


print("Loading wind...")

wind_050 = load_neon_csv_series(
    "filesToStack00001",
    "DP1.00001.001",
    "2DWSD_30min",
    "000",
    "050",
    "windSpeedMean",
    "windSpeedFinalQF",
)

wind_040 = load_neon_csv_series(
    "filesToStack00001",
    "DP1.00001.001",
    "2DWSD_30min",
    "000",
    "040",
    "windSpeedMean",
    "windSpeedFinalQF",
)


print("Loading RH...")

rh_top = load_neon_csv_series(
    "filesToStack00098",
    "DP1.00098.001",
    "RH_30min",
    "000",
    "060",
    "RHMean",
    "RHFinalQF",
)

rh_ground = load_neon_csv_series(
    "filesToStack00098",
    "DP1.00098.001",
    "RH_30min",
    "002",
    "000",
    "RHMean",
    "RHFinalQF",
)


# ============================================================
# Build TBOT
# ============================================================

forcing = pd.DataFrame(index=idx)

(
    forcing["TBOT"],
    forcing["TBOT_source"],
    forcing["TBOT_is_raw"],
) = combine_sources(
    idx,
    [
        ("NEON_STANDALONE_TOP", ta_top),
        ("NEON_EC_TOP", master["TBOT"]),
    ],
)


# ============================================================
# Build PSRF
# ============================================================

(
    forcing["PSRF"],
    forcing["PSRF_source"],
    forcing["PSRF_is_raw"],
) = combine_sources(
    idx,
    [
        ("NEON_STANDALONE_BARO", pa),
        ("NEON_EC_BARO", master["PSRF"]),
    ],
)


# ============================================================
# Build FSDS
# ============================================================

(
    forcing["FSDS"],
    forcing["FSDS_source"],
    forcing["FSDS_is_raw"],
) = combine_sources(
    idx,
    [
        ("NEON_STANDALONE_TOP", sw_top),
        ("NEON_EC_TOP", master["FSDS"]),
    ],
)


# ============================================================
# Build FLDS
# ============================================================

(
    forcing["FLDS"],
    forcing["FLDS_source"],
    forcing["FLDS_is_raw"],
) = combine_sources(
    idx,
    [
        ("NEON_STANDALONE_TOP", lw_top),
        ("NEON_EC_TOP", master["FLDS"]),
        ("NEON_STANDALONE_GROUND", lw_ground),
    ],
)


# ============================================================
# Build WIND
#
# Following NCAR-NEON logic:
# EC sonic first, then tower levels 050 and 040.
# ============================================================

(
    forcing["WIND"],
    forcing["WIND_source"],
    forcing["WIND_is_raw"],
) = combine_sources(
    idx,
    [
        ("NEON_EC_SONIC_060", master["WIND"]),
        ("NEON_STANDALONE_050", wind_050),
        ("NEON_STANDALONE_040", wind_040),
    ],
)


# ============================================================
# Build QBOT
#
# Primary:
# direct EC H2O dry mole ratio already converted in master
#
# Secondary:
# tower-top RH + TBOT + PSRF
#
# Tertiary:
# soil-array RH + TBOT + PSRF
# ============================================================

q_rh_top = buck_q_from_rh(
    forcing["TBOT"],
    rh_top.reindex(idx),
    forcing["PSRF"],
)

q_rh_ground = buck_q_from_rh(
    forcing["TBOT"],
    rh_ground.reindex(idx),
    forcing["PSRF"],
)

(
    forcing["QBOT"],
    forcing["QBOT_source"],
    forcing["QBOT_is_raw"],
) = combine_sources(
    idx,
    [
        ("NEON_EC_H2O_060", master["QBOT"]),
        ("NEON_RH_TOP_DERIVED", q_rh_top),
        ("NEON_RH_GROUND_DERIVED", q_rh_ground),
    ],
)


# ============================================================
# Precipitation
# ============================================================

forcing["PRECTmms"] = master["PRECTmms"]

forcing["PRECTmms_source"] = np.where(
    forcing["PRECTmms"].notna(),
    "NEON_PRIMARY_PRECIP",
    "MISSING",
)

forcing["PRECTmms_is_raw"] = (
    forcing["PRECTmms"].notna()
).astype(int)


# ============================================================
# ZBOT
# ============================================================

forcing["ZBOT"] = ZBOT
forcing["ZBOT_source"] = "NEON_METADATA"


# ============================================================
# EC provenance
# ============================================================

ec = pd.DataFrame(index=idx)

for var in ["NEE", "LE", "H", "USTAR"]:

    if var not in master.columns:
        continue

    ec[f"{var}_raw"] = master[var]

    ec[f"{var}_is_raw"] = (
        master[var].notna()
    ).astype(int)

    ec[f"{var}_source"] = np.where(
        master[var].notna(),
        "NEON_RAW_QC_PASS",
        "MISSING",
    )


# ============================================================
# Monthly raw fractions
# ============================================================

quality = pd.DataFrame(index=idx)

forcing_vars = [
    "TBOT",
    "QBOT",
    "PSRF",
    "FSDS",
    "FLDS",
    "WIND",
    "PRECTmms",
]

for var in forcing_vars:
    quality[f"{var}_raw_fraction"] = (
        forcing[f"{var}_is_raw"]
    )

if "NEE_is_raw" in ec.columns:
    quality["NEE_raw_fraction"] = (
        ec["NEE_is_raw"]
    )

if "LE_is_raw" in ec.columns:
    quality["LE_raw_fraction"] = (
        ec["LE_is_raw"]
    )

if "H_is_raw" in ec.columns:
    quality["H_raw_fraction"] = (
        ec["H_is_raw"]
    )

if "USTAR_is_raw" in ec.columns:
    quality["USTAR_raw_fraction"] = (
        ec["USTAR_is_raw"]
    )


monthly_quality = (
    quality
    .resample("MS")
    .mean()
)

monthly_quality.index.name = "month"


# ============================================================
# Annual raw fractions
# ============================================================

annual_quality = (
    quality
    .resample("YS")
    .mean()
)

annual_quality.index.name = "year"


# ============================================================
# Write outputs
# ============================================================

forcing_out = (
    PROC
    / "PUUM_forcing_stage1_raw_sources_2019_2026.csv"
)

ec_out = (
    PROC
    / "PUUM_EC_raw_with_provenance_2019_2026.csv"
)

monthly_out = (
    PROC
    / "PUUM_monthly_raw_fraction_2019_2026.csv"
)

annual_out = (
    PROC
    / "PUUM_annual_raw_fraction_2019_2026.csv"
)


forcing.reset_index().to_csv(
    forcing_out,
    index=False,
)

ec.reset_index().to_csv(
    ec_out,
    index=False,
)

monthly_quality.reset_index().to_csv(
    monthly_out,
    index=False,
)

annual_quality.reset_index().to_csv(
    annual_out,
    index=False,
)


# ============================================================
# 2020-2025 no-leap forcing candidate
# ============================================================

f = forcing.loc[
    (forcing.index >= "2020-01-01")
    & (forcing.index < "2026-01-01")
].copy()

f = f[
    ~(
        (f.index.month == 2)
        & (f.index.day == 29)
    )
]

forcing_noleap_out = (
    PROC
    / "PUUM_forcing_stage1_2020_2025_noleap.csv"
)

f.reset_index().to_csv(
    forcing_noleap_out,
    index=False,
)


# ============================================================
# Report
# ============================================================

print("\n" + "=" * 78)
print("PUUM STAGE-1 RAW FORCING COMPLETE")
print("=" * 78)

print("\nRaw observation coverage:")

for var in forcing_vars:

    frac = forcing[f"{var}_is_raw"].mean()

    missing = forcing[var].isna().sum()

    print(
        f"{var:10s} "
        f"raw_fraction={frac:7.4f}  "
        f"missing={missing:7d}"
    )


print("\nEC raw observation coverage:")

for var in ["NEE", "LE", "H", "USTAR"]:

    col = f"{var}_is_raw"

    if col in ec.columns:

        print(
            f"{var:10s} "
            f"raw_fraction="
            f"{ec[col].mean():7.4f}"
        )


print("\n2020-2025 no-leap rows:")
print(len(f))

print("Expected:")
print(6 * 365 * 48)


print("\nSource fractions:")

for var in forcing_vars:

    print("\n", var)

    print(
        forcing[f"{var}_source"]
        .value_counts(normalize=True)
        .round(4)
        .to_string()
    )


print("\nFiles written:")
print(forcing_out)
print(ec_out)
print(monthly_out)
print(annual_out)
print(forcing_noleap_out)

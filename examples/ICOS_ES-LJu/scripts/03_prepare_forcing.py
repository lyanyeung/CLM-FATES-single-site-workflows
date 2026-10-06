#!/usr/bin/env python3
from pathlib import Path
import os
import numpy as np
import pandas as pd

USER = os.environ.get("IRIDIS_USER", "ly3n24")
SITE = "ES-LJu"

ROOT = Path(f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/{SITE}")
RAW = ROOT / "forcing/raw/EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1"
PROCESSED = ROOT / "forcing/processed"
OBS = ROOT / "obs"

PROCESSED.mkdir(parents=True, exist_ok=True)
OBS.mkdir(parents=True, exist_ok=True)

FLUXMET = RAW / "EUF_ES-LJu_FLUXNET_FLUXMET_HH_2004-2024_v1.3_r1.csv"
ERA = RAW / "EUF_ES-LJu_FLUXNET_ERA5_HH_1981-2025_v1.3_r1.csv"

OUT_FORCING = PROCESSED / "ES-LJu_CLM_forcing_2004_2024.csv"
OUT_OBS = OBS / "ES-LJu_EC_GPP_NEE_DT_2004_2024.csv"
OUT_QC = PROCESSED / "ES-LJu_TA_VPD_ERA_replacements.csv"

START_YEAR = 2004
END_YEAR = 2024
ZBOT = 2.5

required_fluxmet = [
    "TIMESTAMP_START",
    "TA_F", "VPD_F", "PA_F",
    "SW_IN_F", "LW_IN_F", "WS_F", "P_F",
    "GPP_DT_VUT_REF", "NEE_VUT_REF",
]

print("Reading:", FLUXMET)
df = pd.read_csv(FLUXMET, low_memory=False)

missing = [c for c in required_fluxmet if c not in df.columns]
if missing:
    raise RuntimeError(f"Required FLUXMET columns missing: {missing}")

# ERA variables are often already carried in FLUXMET. If not, merge them
# from the companion ERA5 HH file by TIMESTAMP_START.
if "TA_ERA" not in df.columns or "VPD_ERA" not in df.columns:
    print("TA_ERA/VPD_ERA not in FLUXMET; merging companion ERA5 HH file")
    era = pd.read_csv(ERA, low_memory=False)
    need = ["TIMESTAMP_START", "TA_ERA", "VPD_ERA"]
    miss = [c for c in need if c not in era.columns]
    if miss:
        raise RuntimeError(f"ERA5 columns missing: {miss}")
    df = df.merge(
        era[need],
        on="TIMESTAMP_START",
        how="left",
        validate="one_to_one",
    )

keep_numeric = [
    "TA_F", "VPD_F", "PA_F",
    "SW_IN_F", "LW_IN_F", "WS_F", "P_F",
    "TA_ERA", "VPD_ERA",
    "GPP_DT_VUT_REF", "NEE_VUT_REF",
]

for c in keep_numeric:
    df[c] = pd.to_numeric(df[c], errors="coerce")
    df.loc[df[c] <= -9990, c] = np.nan

df["time"] = pd.to_datetime(
    df["TIMESTAMP_START"].astype(str),
    format="%Y%m%d%H%M",
)

df = df[
    (df["time"].dt.year >= START_YEAR)
    & (df["time"].dt.year <= END_YEAR)
].copy()

# CTSM case uses NO_LEAP.
df = df[
    ~((df["time"].dt.month == 2) & (df["time"].dt.day == 29))
].copy()

df = df.sort_values("time").reset_index(drop=True)

# ---------------------------------------------------------------------
# Site-specific TA / VPD QC
# ---------------------------------------------------------------------
df["TA_USE"] = df["TA_F"]
df["VPD_USE"] = df["VPD_F"]

bad_ta = (
    df["TA_USE"].isna()
    | (df["TA_USE"] < -20.0)
    | (df["TA_USE"] > 40.0)
    | (
        (df["time"].dt.year == 2023)
        & ((df["TA_USE"] - df["TA_ERA"]).abs() >= 15.0)
    )
)

qc_reason = pd.Series("", index=df.index, dtype="object")
qc_reason.loc[bad_ta] = "TA_rule"

df.loc[bad_ta, "TA_USE"] = df.loc[bad_ta, "TA_ERA"]
df.loc[bad_ta, "VPD_USE"] = df.loc[bad_ta, "VPD_ERA"]

def es_hpa(temp_c):
    return 6.112 * np.exp(17.67 * temp_c / (temp_c + 243.5))

es0 = es_hpa(df["TA_USE"])
ea0 = es0 - df["VPD_USE"]
rh0 = 100.0 * ea0 / es0

bad_vpd = (
    df["TA_USE"].isna()
    | df["VPD_USE"].isna()
    | (df["VPD_USE"] < 0.0)
    | (ea0 <= 0.0)
    | (rh0 < 1.0)
)

qc_reason.loc[bad_vpd & (qc_reason == "")] = "VPD/RH_rule"
qc_reason.loc[bad_vpd & (qc_reason != "")] += "+VPD/RH_rule"

# Important: replace BOTH TA and VPD to keep them physically consistent.
df.loc[bad_vpd, "TA_USE"] = df.loc[bad_vpd, "TA_ERA"]
df.loc[bad_vpd, "VPD_USE"] = df.loc[bad_vpd, "VPD_ERA"]

es = es_hpa(df["TA_USE"])
ea_hpa = es - df["VPD_USE"]
rh = 100.0 * ea_hpa / es

if (ea_hpa <= 0).any():
    bad = df.loc[ea_hpa <= 0, ["time", "TA_USE", "VPD_USE", "TA_ERA", "VPD_ERA"]]
    raise RuntimeError(f"Final non-positive vapor pressure remains:\n{bad.head(20)}")

if (rh < 1.0).any():
    bad = df.loc[rh < 1.0, ["time", "TA_USE", "VPD_USE", "TA_ERA", "VPD_ERA"]]
    raise RuntimeError(f"Final RH < 1% remains:\n{bad.head(20)}")

# ---------------------------------------------------------------------
# DATM variables
# ---------------------------------------------------------------------
out = pd.DataFrame()
out["time"] = df["time"]
out["TBOT"] = df["TA_USE"] + 273.15
out["PSRF"] = df["PA_F"] * 1000.0

ea_pa = ea_hpa * 100.0
out["QBOT"] = 0.622 * ea_pa / (out["PSRF"] - 0.378 * ea_pa)

out["FSDS"] = df["SW_IN_F"]
out["FLDS"] = df["LW_IN_F"]
out["WIND"] = df["WS_F"]
out["PRECTmms"] = df["P_F"].clip(lower=0.0) / 1800.0
out["ZBOT"] = ZBOT

forcing_cols = [
    "TBOT", "QBOT", "PSRF", "FSDS",
    "FLDS", "WIND", "PRECTmms", "ZBOT",
]

if out[forcing_cols].isna().any().any():
    raise RuntimeError(
        "Missing values remain in forcing:\n"
        + str(out[forcing_cols].isna().sum())
    )

expected_rows = (END_YEAR - START_YEAR + 1) * 365 * 48
if len(out) != expected_rows:
    raise RuntimeError(
        f"Expected {expected_rows} rows after noleap filtering, got {len(out)}"
    )

year_counts = out.groupby(out["time"].dt.year).size()
if not (year_counts == 17520).all():
    raise RuntimeError(f"Unexpected per-year counts:\n{year_counts}")

out.to_csv(OUT_FORCING, index=False)

obs = df[
    ["time", "GPP_DT_VUT_REF", "NEE_VUT_REF"]
].copy()
obs.to_csv(OUT_OBS, index=False)

qc = pd.DataFrame({
    "time": df["time"],
    "reason": qc_reason,
    "TA_F_original": df["TA_F"],
    "VPD_F_original": df["VPD_F"],
    "TA_ERA": df["TA_ERA"],
    "VPD_ERA": df["VPD_ERA"],
    "TA_USE": df["TA_USE"],
    "VPD_USE": df["VPD_USE"],
    "RH_final_pct": rh,
})
qc = qc[qc["reason"] != ""]
qc.to_csv(OUT_QC, index=False)

print("Wrote:", OUT_FORCING)
print("Wrote:", OUT_OBS)
print("Wrote:", OUT_QC)
print("Rows:", len(out))
print("Replacements:", len(qc))
print()
for c in forcing_cols:
    print(
        f"{c:10s}",
        float(out[c].min()),
        "to",
        float(out[c].max()),
        "missing =",
        int(out[c].isna().sum()),
    )

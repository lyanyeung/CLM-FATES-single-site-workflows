#!/usr/bin/env python3

from pathlib import Path
from netCDF4 import Dataset, num2date

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# ============================================================
# Config
# ============================================================

USER = os.environ.get("USER", "ly3n24")

CASE_DIR = Path(
    f"/iridisfs/scratch/{USER}/CLM_FATES/cases/PUUM_FATES_1PT"
)

HIST_DIR = Path(
    f"/scratch/{USER}/CTSM_FATES_OUTPUTS/archive/PUUM_FATES_1PT/lnd/hist"
)

EC_FILE = Path(
    f"/iridisfs/scratch/{USER}/NEON/PUUM/processed/"
    "PUUM_EC_raw_with_provenance_2019_2026.csv"
)

OUT_DIR = CASE_DIR / "EC_comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2020
END_YEAR = 2025

# EC NEE: umol CO2 m-2 s-1 -> g C m-2 d-1
EC_FACTOR = 86400.0 * 12.0107e-6

# FATES NEE uses FATES_NEP, where NEE = -NEP
# kg C m-2 s-1 -> g C m-2 d-1
FATES_FACTOR = 86400.0 * 1000.0


# ============================================================
# Helpers
# ============================================================

def extract_point(var):
    a = var[:]
    if np.ma.isMaskedArray(a):
        a = a.filled(np.nan)
    a = np.asarray(a, dtype=float)

    dims = list(var.dimensions)
    if "time" not in dims:
        raise RuntimeError(f"{var.name}: no time dimension")

    tidx = dims.index("time")
    a = np.moveaxis(a, tidx, 0)
    a = a.reshape(a.shape[0], -1)

    if a.shape[1] != 1:
        raise RuntimeError(f"{var.name}: expected one grid point, got shape {a.shape}")

    return a[:, 0]


def get_dates(ds):
    t = ds.variables["time"]

    if "time_bounds" in ds.variables:
        vals = ds.variables["time_bounds"][:, 0]
    elif "time_bnds" in ds.variables:
        vals = ds.variables["time_bnds"][:, 0]
    else:
        vals = t[:]

    dates = num2date(
        vals,
        t.units,
        calendar=getattr(t, "calendar", "noleap"),
        only_use_cftime_datetimes=True,
    )

    return pd.DatetimeIndex([
        pd.Timestamp(x.year, x.month, x.day)
        for x in dates
    ])


def calc_metrics(obs, mod):
    obs = np.asarray(obs, dtype=float)
    mod = np.asarray(mod, dtype=float)

    good = np.isfinite(obs) & np.isfinite(mod)
    obs = obs[good]
    mod = mod[good]

    if len(obs) < 2:
        return {
            "N": len(obs),
            "R": np.nan,
            "R2": np.nan,
            "RMSE": np.nan,
            "MAE": np.nan,
            "Bias": np.nan,
        }

    resid = mod - obs
    ss_res = np.sum((mod - obs) ** 2)
    ss_tot = np.sum((obs - np.mean(obs)) ** 2)

    return {
        "N": len(obs),
        "R": np.corrcoef(obs, mod)[0, 1],
        "R2": 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan,
        "RMSE": np.sqrt(np.mean(resid ** 2)),
        "MAE": np.mean(np.abs(resid)),
        "Bias": np.mean(resid),
    }


# ============================================================
# 1. Read FATES history
# ============================================================

files = sorted(HIST_DIR.glob("*.clm2.h0a.*.nc"))

if not files:
    raise FileNotFoundError(f"No FATES history files found in {HIST_DIR}")

print("=" * 80)
print("FATES HISTORY FILES")
print("=" * 80)
print("Count:", len(files))
print("First:", files[0].name)
print("Last :", files[-1].name)

parts = []

for f in files:
    with Dataset(f) as ds:
        if "FATES_NEP" not in ds.variables:
            raise RuntimeError(f"FATES_NEP not found in {f}")

        dates = get_dates(ds)
        nep = extract_point(ds.variables["FATES_NEP"])

        temp = pd.DataFrame({
            "date": dates,
            "FATES_NEE": -nep * FATES_FACTOR,
        })

        parts.append(temp)

model = pd.concat(parts, ignore_index=True)
model = model.groupby("date", as_index=False)["FATES_NEE"].mean()

model = model[
    (model["date"].dt.year >= START_YEAR) &
    (model["date"].dt.year <= END_YEAR)
].copy()

# Remove leap day to match noleap
model = model[
    ~((model["date"].dt.month == 2) & (model["date"].dt.day == 29))
].copy()

print("\nModel period:")
print(model["date"].min(), "->", model["date"].max())
print("Model daily rows:", len(model))


# ============================================================
# 2. Read EC NEE
# ============================================================

ec = pd.read_csv(EC_FILE)

if "time" not in ec.columns:
    raise RuntimeError("time column not found in EC file")

if "NEE_raw" not in ec.columns:
    raise RuntimeError("NEE_raw column not found in EC file")

ec["time"] = pd.to_datetime(ec["time"], utc=True).dt.tz_convert(None)
ec["NEE_raw"] = pd.to_numeric(ec["NEE_raw"], errors="coerce")

ec = ec[
    (ec["time"].dt.year >= START_YEAR) &
    (ec["time"].dt.year <= END_YEAR)
].copy()

# Remove leap day
ec = ec[
    ~((ec["time"].dt.month == 2) & (ec["time"].dt.day == 29))
].copy()

print("\n" + "=" * 80)
print("EC NEE")
print("=" * 80)
print("Valid half-hours:", ec["NEE_raw"].notna().sum())

ec = ec.set_index("time").sort_index()

# Half-hourly -> daily mean
# 这里先不做太严格筛选，只要求至少 1 个值就先画出来
ec_daily = ec["NEE_raw"].resample("D").mean() * EC_FACTOR
ec_daily_n = ec["NEE_raw"].resample("D").count()

obs_daily = pd.DataFrame({
    "date": ec_daily.index,
    "EC_NEE": ec_daily.values,
    "EC_NEE_nhh": ec_daily_n.values,
})

print("EC daily rows:", len(obs_daily))
print("EC daily valid:", np.isfinite(obs_daily["EC_NEE"]).sum())


# ============================================================
# 3. Merge daily
# ============================================================

daily = pd.merge(
    model,
    obs_daily,
    on="date",
    how="left",
).sort_values("date").reset_index(drop=True)

daily.to_csv(
    OUT_DIR / "PUUM_daily_FATES_vs_EC_NEE_2020_2025.csv",
    index=False,
)


# ============================================================
# 4. Monthly means
# ============================================================

monthly = (
    daily
    .set_index("date")[["FATES_NEE", "EC_NEE"]]
    .resample("MS")
    .mean()
    .reset_index()
)

monthly.to_csv(
    OUT_DIR / "PUUM_monthly_FATES_vs_EC_NEE_2020_2025.csv",
    index=False,
)

print("\nMonthly valid overlap:")
good_mon = monthly["FATES_NEE"].notna() & monthly["EC_NEE"].notna()
print(good_mon.sum())


# ============================================================
# 5. Metrics
# ============================================================

daily_metrics = calc_metrics(
    daily["EC_NEE"],
    daily["FATES_NEE"],
)
daily_metrics["Scale"] = "daily"
daily_metrics["Flux"] = "NEE"

monthly_metrics = calc_metrics(
    monthly["EC_NEE"],
    monthly["FATES_NEE"],
)
monthly_metrics["Scale"] = "monthly"
monthly_metrics["Flux"] = "NEE"

metrics_df = pd.DataFrame([daily_metrics, monthly_metrics])
metrics_df.to_csv(
    OUT_DIR / "PUUM_FATES_vs_EC_NEE_metrics.csv",
    index=False,
)

print("\n" + "=" * 80)
print("METRICS")
print("=" * 80)
print(metrics_df.to_string(index=False))


# ============================================================
# 6. Plot: daily
# ============================================================

fig, ax = plt.subplots(figsize=(15, 5))

ax.plot(
    daily["date"],
    daily["EC_NEE"],
    label="EC tower (raw QC-passed)",
    linewidth=1.0,
)

ax.plot(
    daily["date"],
    daily["FATES_NEE"],
    label="FATES",
    linewidth=1.0,
)

ax.axhline(0, linestyle="--", linewidth=0.8)

ax.set_title("PUUM daily NEE: EC tower vs FATES (2020-2025)")
ax.set_xlabel("Year")
ax.set_ylabel(r"NEE (g C m$^{-2}$ d$^{-1}$)")
ax.grid(alpha=0.2)
ax.legend(frameon=False)

ax.xaxis.set_major_locator(mdates.YearLocator(1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

fig.tight_layout()
fig.savefig(
    OUT_DIR / "PUUM_daily_NEE_EC_vs_FATES_2020_2025.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ============================================================
# 7. Plot: monthly
# ============================================================

fig, ax = plt.subplots(figsize=(15, 5))

ax.plot(
    monthly["date"],
    monthly["EC_NEE"],
    label="EC tower (raw QC-passed)",
    linewidth=1.5,
)

ax.plot(
    monthly["date"],
    monthly["FATES_NEE"],
    label="FATES",
    linewidth=1.5,
)

ax.axhline(0, linestyle="--", linewidth=0.8)

ax.set_title("PUUM monthly NEE: EC tower vs FATES (2020-2025)")
ax.set_xlabel("Year")
ax.set_ylabel(r"NEE (g C m$^{-2}$ d$^{-1}$)")
ax.grid(alpha=0.2)
ax.legend(frameon=False)

ax.xaxis.set_major_locator(mdates.YearLocator(1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

fig.tight_layout()
fig.savefig(
    OUT_DIR / "PUUM_monthly_NEE_EC_vs_FATES_2020_2025.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ============================================================
# 8. Plot: monthly scatter
# ============================================================

m = monthly.dropna(subset=["EC_NEE", "FATES_NEE"]).copy()

fig, ax = plt.subplots(figsize=(6, 6))

ax.scatter(
    m["EC_NEE"],
    m["FATES_NEE"],
    s=18,
)

if len(m) > 0:
    xymin = np.nanmin([m["EC_NEE"].min(), m["FATES_NEE"].min()])
    xymax = np.nanmax([m["EC_NEE"].max(), m["FATES_NEE"].max()])
    pad = 0.05 * (xymax - xymin if xymax > xymin else 1.0)

    ax.plot(
        [xymin - pad, xymax + pad],
        [xymin - pad, xymax + pad],
        linestyle="--",
        linewidth=0.8,
    )

    ax.set_xlim(xymin - pad, xymax + pad)
    ax.set_ylim(xymin - pad, xymax + pad)

ax.set_xlabel(r"EC NEE (g C m$^{-2}$ d$^{-1}$)")
ax.set_ylabel(r"FATES NEE (g C m$^{-2}$ d$^{-1}$)")
ax.set_title("PUUM monthly NEE: FATES vs EC")
ax.grid(alpha=0.2)

fig.tight_layout()
fig.savefig(
    OUT_DIR / "PUUM_monthly_NEE_scatter_2020_2025.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)

print("\nSaved outputs to:")
print(OUT_DIR)

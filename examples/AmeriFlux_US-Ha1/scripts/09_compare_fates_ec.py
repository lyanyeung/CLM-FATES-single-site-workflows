#!/usr/bin/env python3
from pathlib import Path
import os
from netCDF4 import Dataset, num2date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

USER = os.environ.get("IRIDIS_USER", "ly3n24")
SITE = "US-Ha1"

SITE_ROOT = Path(
    f"/iridisfs/scratch/{USER}/CLM_FATES/sites/MY_EC_SITE/{SITE}"
)
HIST = Path(
    f"/scratch/{USER}/CTSM_FATES_OUTPUTS/archive/{SITE}_FATES_1PT/lnd/hist"
)
OBS = SITE_ROOT / "obs/US-Ha1_EC_GPP_NEE_DT_1991_2025.csv"
OUT = SITE_ROOT / "validation"
OUT.mkdir(parents=True, exist_ok=True)

EC_GPP = "GPP_DT_VUT_REF"
EC_NEE = "NEE_VUT_REF"
MODEL_GPP = "FATES_GPP"
MODEL_NEP = "FATES_NEP"

EC_FACTOR = 86400.0 * 12.0107e-6
FATES_FACTOR = 86400.0 * 1000.0
YLABEL = r"g C m$^{-2}$ d$^{-1}$"

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
        raise RuntimeError(f"{var.name}: expected 1 point, got {a.shape}")

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

def parse_time(x):
    x = x.astype(str).str.strip()
    if x.str.match(r"^\d{12}$").all():
        return pd.to_datetime(x, format="%Y%m%d%H%M")
    return pd.to_datetime(x)

def metrics(obs, mod):
    obs = np.asarray(obs, dtype=float)
    mod = np.asarray(mod, dtype=float)
    good = np.isfinite(obs) & np.isfinite(mod)
    obs = obs[good]
    mod = mod[good]

    if len(obs) < 2:
        return dict(N=len(obs), R=np.nan, R2=np.nan, RMSE=np.nan,
                    MAE=np.nan, Bias=np.nan)

    resid = mod - obs
    ss_res = np.sum((mod - obs) ** 2)
    ss_tot = np.sum((obs - np.mean(obs)) ** 2)

    return dict(
        N=len(obs),
        R=np.corrcoef(obs, mod)[0, 1],
        R2=(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan,
        RMSE=np.sqrt(np.mean(resid ** 2)),
        MAE=np.mean(np.abs(resid)),
        Bias=np.mean(resid),
    )

# ---------------------------------------------------------------------
# FATES daily history: IMPORTANT: h0a, not h0
# ---------------------------------------------------------------------
files = sorted(HIST.glob("*.clm2.h0a.*.nc"))
if not files:
    raise FileNotFoundError(f"No *.clm2.h0a.*.nc files found in {HIST}")

print("FATES history files:", len(files))
print("First:", files[0].name)
print("Last :", files[-1].name)

parts = []
for f in files:
    with Dataset(f) as ds:
        dates = get_dates(ds)
        gpp = extract_point(ds.variables[MODEL_GPP])
        nep = extract_point(ds.variables[MODEL_NEP])

        parts.append(pd.DataFrame({
            "date": dates,
            "FATES_GPP": gpp * FATES_FACTOR,
            "FATES_NEE": -nep * FATES_FACTOR,
        }))

model = pd.concat(parts, ignore_index=True)
model = (
    model.groupby("date", as_index=False)[["FATES_GPP", "FATES_NEE"]]
    .mean()
)
model = model[
    (model["date"].dt.year >= 1991)
    & (model["date"].dt.year <= 2025)
].copy()
model = model[
    ~((model["date"].dt.month == 2) & (model["date"].dt.day == 29))
].copy()

# ---------------------------------------------------------------------
# EC hourly -> daily
# ---------------------------------------------------------------------
ec = pd.read_csv(OBS)
timecol = "time" if "time" in ec.columns else "TIMESTAMP_START"
ec["time"] = parse_time(ec[timecol])

for v in [EC_GPP, EC_NEE]:
    ec[v] = pd.to_numeric(ec[v], errors="coerce")
    ec.loc[ec[v] <= -9990, v] = np.nan

ec = ec[
    ~((ec["time"].dt.month == 2) & (ec["time"].dt.day == 29))
].copy()
ec = ec.set_index("time").sort_index()

def daily_ec(var):
    r = ec[var].resample("D")
    mean = r.mean()
    count = r.count()
    mean[count < 20] = np.nan
    mean *= EC_FACTOR
    return pd.DataFrame({"date": mean.index, var: mean.values})

gpp_d = daily_ec(EC_GPP).rename(columns={EC_GPP: "EC_GPP"})
nee_d = daily_ec(EC_NEE).rename(columns={EC_NEE: "EC_NEE"})
obs_daily = pd.merge(gpp_d, nee_d, on="date", how="outer")

daily = pd.merge(model, obs_daily, on="date", how="inner")
daily = daily.sort_values("date").reset_index(drop=True)
daily.to_csv(
    OUT / "US-Ha1_daily_FATES_vs_EC_DT_1991_2025.csv",
    index=False,
)

# ---------------------------------------------------------------------
# Daily -> monthly: at least 20 matched valid days
# ---------------------------------------------------------------------
def monthly_pair(df, obs, mod):
    x = df[["date", obs, mod]].dropna().set_index("date")
    m = x.resample("MS").mean()
    n = x[obs].resample("MS").count()
    m.loc[n < 20, [obs, mod]] = np.nan
    m[f"{obs}_NDAY"] = n
    return m.reset_index()

gpp_m = monthly_pair(daily, "EC_GPP", "FATES_GPP")
nee_m = monthly_pair(daily, "EC_NEE", "FATES_NEE")
monthly = pd.merge(gpp_m, nee_m, on="date", how="outer")

monthly.to_csv(
    OUT / "US-Ha1_monthly_FATES_vs_EC_DT_1991_2025.csv",
    index=False,
)

# Metrics
rows = []
for scale, data in [("daily", daily), ("monthly", monthly)]:
    for flux, obs, mod in [
        ("GPP", "EC_GPP", "FATES_GPP"),
        ("NEE", "EC_NEE", "FATES_NEE"),
    ]:
        row = metrics(data[obs], data[mod])
        row.update(Scale=scale, Flux=flux)
        rows.append(row)

metrics_df = pd.DataFrame(rows)
metrics_df.to_csv(OUT / "US-Ha1_FATES_vs_EC_metrics.csv", index=False)
print("\nMETRICS")
print(metrics_df.to_string(index=False))

# ---------------------------------------------------------------------
# Plot exactly in <=10-year windows
# Both EC and FATES are SOLID lines.
# ---------------------------------------------------------------------
def plot_period(df, obs, mod, flux, start_year, end_year):
    start = pd.Timestamp(f"{start_year}-01-01")
    end = pd.Timestamp(f"{end_year}-12-31")

    x = df[(df["date"] >= start) & (df["date"] <= end)].copy()

    fig, ax = plt.subplots(figsize=(15, 5))

    ax.plot(
        x["date"],
        x[obs],
        label="EC tower",
        linewidth=1.5,
    )

    ax.plot(
        x["date"],
        x[mod],
        label="FATES",
        linewidth=1.5,
    )

    if flux == "NEE":
        ax.axhline(
            0,
            linestyle="--",
            linewidth=0.8,
        )

    ax.set_xlabel("Year")
    ax.set_ylabel(f"{flux} ({YLABEL})")

    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(start, pd.Timestamp(f"{end_year + 1}-01-01"))

    ax.legend(frameon=False)
    ax.grid(alpha=0.2)

    ax.set_title(
        f"US-Ha1 monthly {flux}: EC tower vs FATES ({start_year}-{end_year})"
    )

    fig.tight_layout()

    outfile = OUT / f"US-Ha1_{flux}_monthly_{start_year}_{end_year}.png"
    fig.savefig(outfile, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Saved:", outfile)

PERIODS = [
    (1991, 2000),
    (2001, 2010),
    (2011, 2020),
    (2021, 2025),
]

for y1, y2 in PERIODS:
    plot_period(monthly, "EC_GPP", "FATES_GPP", "GPP", y1, y2)
    plot_period(monthly, "EC_NEE", "FATES_NEE", "NEE", y1, y2)
    
# ---------------------------------------------------------------------
# Combined monthly plots: all <=10-year windows in one vertical figure
# ---------------------------------------------------------------------
def plot_all_periods(df, obs, mod, flux):
    fig, axes = plt.subplots(
        nrows=len(PERIODS),
        ncols=1,
        figsize=(15, 4 * len(PERIODS)),
        squeeze=False,
    )

    axes = axes[:, 0]

    # Use one common y-axis range across all panels
    values = pd.concat(
        [df[obs], df[mod]],
        ignore_index=True,
    ).replace([np.inf, -np.inf], np.nan).dropna()

    if len(values) == 0:
        raise RuntimeError(f"No valid monthly {flux} values available for plotting")

    if flux == "NEE":
        lim = np.nanmax(np.abs(values))
        ylim = (-1.05 * lim, 1.05 * lim)
    else:
        ymin = min(0.0, float(values.min()))
        ymax = float(values.max())
        span = ymax - ymin

        if span == 0:
            span = 1.0

        ylim = (
            ymin - 0.03 * span if ymin < 0 else 0,
            ymax + 0.05 * span,
        )

    for ax, (start_year, end_year) in zip(axes, PERIODS):
        start = pd.Timestamp(f"{start_year}-01-01")
        end = pd.Timestamp(f"{end_year}-12-31")

        x = df[
            (df["date"] >= start)
            & (df["date"] <= end)
        ].copy()

        ax.plot(
            x["date"],
            x[obs],
            label="EC tower",
            linewidth=1.5,
        )

        ax.plot(
            x["date"],
            x[mod],
            label="FATES",
            linewidth=1.5,
        )

        if flux == "NEE":
            ax.axhline(
                0,
                linestyle="--",
                linewidth=0.8,
            )

        ax.set_ylabel(
            f"{flux}\n({YLABEL})"
        )

        ax.set_title(
            f"{start_year}-{end_year}",
            loc="left",
            fontsize=12,
        )

        ax.set_ylim(*ylim)

        ax.set_xlim(
            start,
            pd.Timestamp(f"{end_year + 1}-01-01"),
        )

        ax.xaxis.set_major_locator(
            mdates.YearLocator(1)
        )

        ax.xaxis.set_major_formatter(
            mdates.DateFormatter("%Y")
        )

        ax.tick_params(
            axis="x",
            rotation=45,
        )

        ax.grid(alpha=0.2)

    # One legend for the complete figure
    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=2,
        frameon=False,
    )

    fig.suptitle(
        f"US-Ha1 monthly {flux}: EC tower vs FATES",
        fontsize=16,
        y=0.995,
    )

    fig.tight_layout(
        rect=[0, 0, 1, 0.97]
    )

    outfile = (
        OUT
        / f"US-Ha1_{flux}_monthly_all_10year_panels.png"
    )

    fig.savefig(
        outfile,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("Saved:", outfile)


plot_all_periods(
    monthly,
    "EC_GPP",
    "FATES_GPP",
    "GPP",
)

plot_all_periods(
    monthly,
    "EC_NEE",
    "FATES_NEE",
    "NEE",
)
print("\nComparison complete.")

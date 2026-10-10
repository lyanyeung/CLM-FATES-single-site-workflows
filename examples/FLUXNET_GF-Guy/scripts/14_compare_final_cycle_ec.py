#!/usr/bin/env python3
"""GF-Guy: compare last 5-year FATES spin-up cycle with EC observations.

Plot conventions and QC follow the ES-LJu example:
https://github.com/lyanyeung/CLM-FATES-single-site-workflows/blob/main/examples/ICOS_ES-LJu/scripts/09_compare_fates_ec.py

Model years 2312-2316 are mapped onto observation years 2017-2021.
All outputs are read-only with respect to the archived model and original EC data.
"""
from __future__ import annotations

import argparse
import re
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # HPC: no graphics display required
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

USER = "ly3n24"
MODEL_FIRST, MODEL_LAST = 2312, 2316
OBS_FIRST, OBS_LAST = 2017, 2021
EC_FACTOR = 86400.0 * 12.0107e-6  # umol CO2 m-2 s-1 -> gC m-2 d-1
FATES_FACTOR = 86400.0 * 1000.0    # kgC m-2 s-1 -> gC m-2 d-1
Y_LABEL = r"g C m$^{-2}$ d$^{-1}$"


def arguments():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--user", default=USER, help="IRIDIS username (default: ly3n24)")
    p.add_argument("--hist", type=Path, default=None, help="Spin-up lnd/hist archive directory")
    p.add_argument("--obs", type=Path, default=None, help="GF-Guy half-hourly EC CSV; default is ICOSETC_GF-Guy_FLUXNET_HH_L2.csv")
    p.add_argument("--out", type=Path, default=None, help="Output folder")
    p.add_argument("--gpp-col", default="auto", help="EC GPP column; auto prefers GPP_DT_VUT_REF")
    p.add_argument("--nee-col", default="NEE_VUT_REF", help="EC NEE column")
    p.add_argument("--time-col", default="auto", help="EC timestamp-start column")
    return p.parse_args()


def ec_columns(path: Path) -> list[str]:
    try:
        return list(pd.read_csv(path, nrows=0, low_memory=False).columns)
    except (OSError, ValueError, UnicodeError, pd.errors.ParserError):
        return []


def resolve_obs(path: Path | None, site_root: Path, nee_col: str, gpp_col: str) -> Path:
    if path is not None:
        if not path.is_file():
            raise FileNotFoundError(f"EC CSV not found: {path}")
        return path
    # Proven GF-Guy source: choose the half-hourly product explicitly.
    # The L2 archive also contains DD/MM/WW/YY versions: auto-detection
    # across all those files previously caused an ambiguous-CSV error.
    default = (site_root / "forcing/raw/ICOSETC_GF-Guy_ARCHIVE_L2/"
               "ICOSETC_GF-Guy_FLUXNET_HH_L2.csv")
    if default.is_file():
        return default
    candidates = []
    for sub in ("obs", "forcing/raw", "processed", "validation"):
        folder = site_root / sub
        if not folder.is_dir():
            continue
        for csv in folder.rglob("*FLUXNET_HH*.csv"):
            cols = ec_columns(csv)
            has_gpp = gpp_col in cols if gpp_col != "auto" else any(
                c in cols for c in ("GPP_DT_VUT_REF", "GPP_NT_VUT_REF")
            )
            if has_gpp and nee_col in cols and any(
                c in cols for c in ("TIMESTAMP_START", "time", "TIMESTAMP", "timestamp")
            ):
                candidates.append(csv)
    if not candidates:
        raise FileNotFoundError(
            "No EC half-hourly CSV with GPP/NEE/timestamps found below "
            f"{site_root}. Specify --obs /absolute/path/to/EC.csv"
        )
    if len(candidates) != 1:
        print("Found multiple HH EC CSVs:")
        for p in sorted(candidates):
            print("  ", p)
        raise RuntimeError("Ambiguous EC data: rerun with --obs /absolute/path/to/EC.csv")
    return candidates[0]


def extract_point(ds: xr.Dataset, name: str) -> np.ndarray:
    if name not in ds:
        raise KeyError(f"Missing FATES variable {name!r} in {ds.encoding.get('source')}")
    da = ds[name]
    if "time" not in da.dims:
        raise ValueError(f"{name} has no time dimension: {da.dims}")
    da = da.transpose("time", *[d for d in da.dims if d != "time"])
    vals = np.asarray(da.values, dtype=float).reshape(da.sizes["time"], -1)
    if vals.shape[1] != 1:
        raise ValueError(f"{name} is not single-point data: {vals.shape}")
    vals[~np.isfinite(vals) | (np.abs(vals) >= 1e35)] = np.nan
    return vals[:, 0]


def verify_daily_time(ds: xr.Dataset, year: int):
    if "time" not in ds.dims or int(ds.sizes["time"]) != 365:
        raise ValueError(f"History {year}: expected 365 daily values; got {ds.sizes.get('time')}")
    # Verify daily spacing if the archive's time coordinate has numeric intervals.
    t = np.asarray(ds["time"].values, dtype=float)
    if len(t) > 1:
        delta = np.diff(t)
        if not np.all(np.isfinite(delta)) or not np.allclose(delta, delta[0], rtol=1e-6, atol=1e-5):
            raise ValueError(f"History {year}: nonuniform time steps; cannot align daily by position")
        units = str(ds["time"].attrs.get("units", "")).lower()
        expected = 24.0 if "hour" in units else 86400.0 if "second" in units else 1.0 if "day" in units else None
        if expected is not None and not np.isclose(delta[0], expected, rtol=1e-5):
            raise ValueError(f"History {year}: time interval {delta[0]} inconsistent with units {units}")
    _verify_cf_daily_dates(ds, year)


def _noleap_ordinal(year: int, month: int, day: int) -> int:
    """Days since an arbitrary year-zero in a 365-day NO_LEAP calendar."""
    mdays = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not (1 <= month <= 12 and 1 <= day <= mdays[month - 1]):
        raise ValueError(f"Invalid noleap calendar date: {year}-{month}-{day}")
    return 365 * year + sum(mdays[:month - 1]) + day - 1


def _verify_cf_daily_dates(ds: xr.Dataset, year: int) -> None:
    """Verify dates using the lower time bound, as in ES-LJu.

    History timestamps typically mark END of averaging interval and thus
    the first daily file is named YYYY-01-02. The first *lower bound* must
    still represent YYYY-01-01. No conversion into pandas' far-future dates.
    """
    t = ds["time"]
    units = str(t.attrs.get("units", ""))
    parsed = re.match(
        r"^\s*(days?|hours?|seconds?) since "
        r"(\d{1,4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2}):(\d{2}))?",
        units, re.IGNORECASE,
    )
    if not parsed:
        warnings.warn(f"History {year}: cannot decode numeric CF time units {units!r}; "
                      "checking 365 records and daily spacing only")
        return
    unit, yy, mm, dd, hh, mi, ss = parsed.groups()
    factor = 86400.0 if unit.lower().startswith("day") else 3600.0 if unit.lower().startswith("hour") else 1.0
    origin = _noleap_ordinal(int(yy), int(mm), int(dd))
    origin += (int(hh or 0) * 3600 + int(mi or 0) * 60 + int(ss or 0)) / 86400.0
    # The official ES-LJu script uses the lower bounds rather than the
    # time end-coordinate. This verifies that our positional mapping agrees.
    bound_name = str(t.attrs.get("bounds", ""))
    for candidate in (bound_name, "time_bounds", "time_bnds"):
        if candidate and candidate in ds:
            bounds = np.asarray(ds[candidate].values, dtype=float)
            if bounds.ndim == 2 and bounds.shape[0] == 365 and bounds.shape[1] >= 2:
                times = bounds[:, 0]
                break
    else:
        times = np.asarray(t.values, dtype=float) - 86400.0 / factor
    day_of_year = origin + times * factor / 86400.0 - _noleap_ordinal(year, 1, 1)
    expected = np.arange(365, dtype=float)
    if not np.allclose(day_of_year, expected, rtol=0, atol=2e-4):
        raise ValueError(
            f"History {year}: daily CF dates do not match Jan 1-Dec 31 "
            f"(first offset={day_of_year[0]:.4f}, last={day_of_year[-1]:.4f})"
        )


def model_daily(hist: Path) -> pd.DataFrame:
    records = []
    for model_year in range(MODEL_FIRST, MODEL_LAST + 1):
        files = sorted(hist.glob(f"*.clm2.h0a.{model_year}-*.nc"))
        if len(files) != 1:
            raise FileNotFoundError(
                f"Expected exactly 1 h0a annual file for model year {model_year} in {hist}; found {len(files)}"
            )
        obs_year = OBS_FIRST + model_year - MODEL_FIRST
        print(f"FATES model year {model_year} -> EC year {obs_year}: {files[0].name}")
        with xr.open_dataset(files[0], decode_times=False) as ds:
            verify_daily_time(ds, model_year)
            gpp = extract_point(ds, "FATES_GPP") * FATES_FACTOR
            nee = -extract_point(ds, "FATES_NEP") * FATES_FACTOR
            for key in ("FATES_GPP", "FATES_NEP"):
                unit = str(ds[key].attrs.get("units", "")).replace(" ", "").lower()
                if "kg" not in unit or "s-1" not in unit:
                    raise ValueError(f"Unexpected {key} units {ds[key].attrs.get('units')!r}")
        # NO_LEAP calendar: positional days Jan 1 through Dec 31, excluding Feb 29 in 2020.
        dates = pd.date_range(f"{obs_year}-01-01", f"{obs_year}-12-31", freq="D")
        dates = dates[~((dates.month == 2) & (dates.day == 29))]
        if len(dates) != 365:
            raise AssertionError(f"Wrong noleap day count for {obs_year}")
        records.append(pd.DataFrame({
            "date": dates, "model_year": model_year,
            "FATES_GPP": gpp, "FATES_NEE": nee,
        }))
    out = pd.concat(records, ignore_index=True)
    if out["date"].duplicated().any() or len(out) != 1825:
        raise ValueError("Model time remapping unexpectedly duplicated or lost days")
    return out


def parse_time(s: pd.Series) -> pd.Series:
    vals = s.astype("string").str.strip()
    if vals.dropna().str.fullmatch(r"\d{12}").all():
        return pd.to_datetime(vals, format="%Y%m%d%H%M", errors="coerce")
    if vals.dropna().str.fullmatch(r"\d{14}").all():
        return pd.to_datetime(vals, format="%Y%m%d%H%M%S", errors="coerce")
    return pd.to_datetime(vals, errors="coerce")


def ec_daily(path: Path, gpp_name: str, nee_name: str, time_name: str):
    cols = ec_columns(path)
    if gpp_name == "auto":
        for option in ("GPP_DT_VUT_REF", "GPP_NT_VUT_REF"):
            if option in cols:
                gpp_name = option
                break
        else:
            raise ValueError(f"No GPP_DT_VUT_REF / GPP_NT_VUT_REF in {path}; specify --gpp-col")
    if time_name == "auto":
        for option in ("TIMESTAMP_START", "time", "TIMESTAMP", "timestamp"):
            if option in cols:
                time_name = option
                break
        else:
            raise ValueError(f"No recognized timestamp column in {path}; specify --time-col")
    for name in (time_name, gpp_name, nee_name):
        if name not in cols:
            raise ValueError(f"Missing EC column {name!r} in {path}")
    print(f"EC data: {path}\nEC timestamp: {time_name}; GPP: {gpp_name}; NEE: {nee_name}")
    ec = pd.read_csv(path, usecols=[time_name, gpp_name, nee_name], low_memory=False)
    ec["date_time"] = parse_time(ec[time_name])
    ec = ec.dropna(subset=["date_time"])
    ec = ec[(ec["date_time"].dt.year >= OBS_FIRST) & (ec["date_time"].dt.year <= OBS_LAST)]
    ec = ec[~((ec["date_time"].dt.month == 2) & (ec["date_time"].dt.day == 29))].copy()
    if ec.empty:
        raise ValueError("No EC records in 2017-2021")
    if ec["date_time"].duplicated().any():
        raise ValueError("Duplicate EC timestamp records: please provide a unique half-hourly EC CSV")
    if len(ec) >= 3:
        d = ec["date_time"].sort_values().diff().dropna()
        most_common = d.mode()
        if not most_common.empty and most_common.iloc[0] != pd.Timedelta(minutes=30):
            raise ValueError(f"Expected 30-min EC data (ES-LJu 40/48 rule), got mode interval {most_common.iloc[0]}")
    for name in (gpp_name, nee_name):
        ec[name] = pd.to_numeric(ec[name], errors="coerce")
        ec.loc[(ec[name] <= -9990) | (~np.isfinite(ec[name])), name] = np.nan
    ec = ec.set_index("date_time").sort_index()
    result = []
    for src, dest in ((gpp_name, "EC_GPP"), (nee_name, "EC_NEE")):
        avg = ec[src].resample("D").mean()
        cnt = ec[src].resample("D").count()
        avg[cnt < 40] = np.nan
        result.append((avg * EC_FACTOR).rename(dest))
    daily = pd.concat(result, axis=1).reset_index().rename(columns={"date_time": "date"})
    daily = daily[~((daily["date"].dt.month == 2) & (daily["date"].dt.day == 29))]
    return daily, gpp_name


def monthly_pair(df: pd.DataFrame, obs: str, mod: str) -> pd.DataFrame:
    x = df[["date", obs, mod]].dropna().set_index("date")
    monthly = x.resample("MS").mean()
    ndays = x[obs].resample("MS").count()
    monthly.loc[ndays < 20, [obs, mod]] = np.nan
    monthly[f"{obs}_NDAY"] = ndays
    return monthly.reset_index()


def metrics(obs, mod):
    a = np.asarray(obs, dtype=float)
    b = np.asarray(mod, dtype=float)
    valid = np.isfinite(a) & np.isfinite(b)
    a, b = a[valid], b[valid]
    if len(a) < 2:
        return dict(N=len(a), R=np.nan, R2=np.nan, RMSE=np.nan, MAE=np.nan, Bias=np.nan)
    residual = b - a
    ss_tot = np.sum((a - a.mean()) ** 2)
    var1, var2 = np.std(a), np.std(b)
    eps = 1e-12 * max(1.0, np.max(np.abs(a)), np.max(np.abs(b)))
    meaningful_obs_variance = var1 > eps
    return dict(
        N=len(a),
        R=float(np.corrcoef(a, b)[0, 1]) if meaningful_obs_variance and var2 > eps else np.nan,
        R2=float(1 - np.sum(residual**2) / ss_tot) if meaningful_obs_variance else np.nan,
        RMSE=float(np.sqrt(np.mean(residual**2))),
        MAE=float(np.mean(np.abs(residual))),
        Bias=float(np.mean(residual)),
    )


def plot_flux(monthly: pd.DataFrame, obs: str, mod: str, flux: str, out: Path):
    fig, ax = plt.subplots(figsize=(15, 5))
    # Exactly as ES-LJu: two solid lines, no markers, 0 dashed only for NEE.
    ax.plot(monthly["date"], monthly[obs], label="EC tower", linewidth=1.5)
    ax.plot(monthly["date"], monthly[mod], label="FATES (final spin-up cycle)", linewidth=1.5)
    if flux == "NEE":
        ax.axhline(0, linestyle="--", linewidth=0.8, color="0.35")
    ax.set_xlabel("Year")
    ax.set_ylabel(f"{flux} ({Y_LABEL})")
    ax.set_title(f"GF-Guy monthly {flux}: EC vs FATES final cycle (2017-2021)")
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(pd.Timestamp("2017-01-01"), pd.Timestamp("2022-01-01"))
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    p = out / f"GF-Guy_{flux}_monthly_EC2017-2021_FATES2312-2316.png"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", p)


def main():
    a = arguments()
    site_root = Path(f"/iridisfs/scratch/{a.user}/CLM_FATES/sites/MY_EC_SITE/GF-Guy")
    hist = a.hist or Path(f"/scratch/{a.user}/CTSM_FATES_OUTPUTS/archive/GF-Guy_FATES_SPINUP300_CO2405/lnd/hist")
    out = a.out or site_root / "spinup300_diagnostics" / "EC_final_cycle"
    if not hist.is_dir():
        raise FileNotFoundError(f"Cannot locate model history: {hist}")
    obs_path = resolve_obs(a.obs, site_root, a.nee_col, a.gpp_col)
    model = model_daily(hist)
    obs, gpp_name = ec_daily(obs_path, a.gpp_col, a.nee_col, a.time_col)
    daily = pd.merge(model, obs, on="date", how="left").sort_values("date")
    monthly = pd.merge(
        monthly_pair(daily, "EC_GPP", "FATES_GPP"),
        monthly_pair(daily, "EC_NEE", "FATES_NEE"),
        on="date", how="outer",
    ).sort_values("date")
    if monthly["EC_GPP"].notna().sum() == 0 or monthly["EC_NEE"].notna().sum() == 0:
        raise ValueError(
            "No valid matched GPP or NEE months (>=20 days each). "
            "Check the EC CSV, variable names, record frequency and missing values."
        )
    stats = []
    for scale, frame in (("daily", daily), ("monthly", monthly)):
        for flux in ("GPP", "NEE"):
            row = metrics(frame[f"EC_{flux}"], frame[f"FATES_{flux}"])
            row.update(Scale=scale, Flux=flux, Obs_GPP_column=gpp_name, Model_years="2312-2316", EC_years="2017-2021")
            stats.append(row)
    out.mkdir(parents=True, exist_ok=True)
    daily.to_csv(out / "GF-Guy_final_cycle_daily_FATES_vs_EC.csv", index=False)
    monthly.to_csv(out / "GF-Guy_final_cycle_monthly_FATES_vs_EC.csv", index=False)
    pd.DataFrame(stats).to_csv(out / "GF-Guy_final_cycle_FATES_vs_EC_metrics.csv", index=False)
    for flux in ("GPP", "NEE"):
        plot_flux(monthly, f"EC_{flux}", f"FATES_{flux}", flux, out)
    print("\nMetrics (R2 is model efficiency 1-SSE/SST, following ES-LJu):")
    print(pd.DataFrame(stats).to_string(index=False))
    print(f"\nFinished: {out}")


if __name__ == "__main__":
    main()

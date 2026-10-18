#!/usr/bin/env python3
"""Audit ICOS FLUXMET_HH DK-Sor CO2_F_MDS and conditionally make a candidate
monthly tower-CO2 CDEPS forcing file (1996-2024).

This does NOT create or submit a CIME case, modify source data, or silently
substitute background CO2 for missing station data. Local source data and
forcing NetCDF must NOT be committed to a public repository.

Usage: python scripts/19_audit_DK_Sor_tower_CO2_and_make_forcing.py
"""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, date2num

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/DK-Sor/forcing")
CSV = (ROOT / "raw/ICOS_DK-Sor_FLUXNET_1996-2024_v1.3_r1"
       / "ICOS_DK-Sor_FLUXNET_FLUXMET_HH_1996-2024_v1.3_r1.csv")
OUT = ROOT / "tower_co2_experiment"
NC = OUT / "DK-Sor_tower_CO2_monthly_daytime_QC0_1996_2024.nc"
START, END = 1996, 2024
CO2_LO, CO2_HI = 300.0, 600.0
MIN_DAYS, MIN_POINTS = 10, 40
LAT, LON = 55.4858694, 11.6446444


def stop(message, code=3):
    print(f"\nSTOP: {message}", file=sys.stderr)
    raise SystemExit(code)


def main():
    if not CSV.is_file():
        stop(f"Missing expected ICOS source: {CSV}")
    OUT.mkdir(parents=True, exist_ok=True)
    print("Source:", CSV, flush=True)
    # Only read 4 fields; keep full provenance of observed vs filled data.
    d = pd.read_csv(CSV, usecols=["TIMESTAMP_START", "TIMESTAMP_END",
                                  "CO2_F_MDS", "CO2_F_MDS_QC"],
                    dtype={"TIMESTAMP_START": str, "TIMESTAMP_END": str},
                    low_memory=False)
    if not len(d):
        stop("Empty CO2 file")
    d["time"] = pd.to_datetime(d["TIMESTAMP_START"].str.strip(),
                               format="%Y%m%d%H%M", errors="coerce")
    d["time_end"] = pd.to_datetime(d["TIMESTAMP_END"].str.strip(),
                                   format="%Y%m%d%H%M", errors="coerce")
    if d["time"].isna().any() or d["time_end"].isna().any():
        stop("Malformed timestamp fields; inspect raw source")
    if d["time"].duplicated().any():
        stop("Duplicate TIMESTAMP_START; inspect raw source")
    if (d["time_end"] - d["time"] != pd.Timedelta(minutes=30)).any():
        stop("Unexpected temporal interval; expected 30-min records")
    d = d[(d.time.dt.year >= START) & (d.time.dt.year <= END)].copy()
    if d.empty:
        stop("No records for 1996-2024")
    v = pd.to_numeric(d["CO2_F_MDS"], errors="coerce")
    qc = pd.to_numeric(d["CO2_F_MDS_QC"], errors="coerce")
    valid = v.notna() & (v > -9990) & v.between(CO2_LO, CO2_HI)
    measured = valid & qc.eq(0)          # QC=0: non-gapfilled by provider
    day = d["time"].dt.hour.between(10, 15)  # fixed station clock; exploratory
    d["co2"] = v.where(valid)
    d["measured_day"] = measured & day
    d["date"] = d.time.dt.normalize()
    d["month"] = d.time.dt.to_period("M")
    expected_months = pd.period_range(f"{START}-01", f"{END}-12", freq="M")
    # Retain a numerical QC histogram; missing remains a distinct category.
    hist = qc.value_counts(dropna=False).sort_index().to_dict()
    print("QC histogram:", hist)
    print("Overall valid:", int(valid.sum()), "/", len(d),
          "| provider QC0:", int(measured.sum()),
          "| daytime provider QC0:", int((measured & day).sum()), flush=True)

    summaries = []
    for period in expected_months:
        x = d[d.month == period]
        y = x[x.measured_day]
        vals = y["co2"].dropna().to_numpy(dtype=float)
        days = int(y.loc[y.co2.notna(), "date"].nunique())
        candidate = float(np.median(vals)) if len(vals) else np.nan
        # Month-level QC thresholds, not independent measurements of
        # uncertainty or sensor sampling height.
        pass_month = (len(vals) >= MIN_POINTS and days >= MIN_DAYS
                      and np.isfinite(candidate)
                      and 300 <= candidate <= 500)
        summaries.append({
            "month": str(period),
            "all_halfhour_rows": len(x),
            "valid_co2_rows": int(x.co2.notna().sum()),
            "provider_QC0_rows": int(measured.loc[x.index].sum()),
            "daytime_QC0_points": len(vals),
            "daytime_QC0_distinct_days": days,
            "tower_monthly_daytime_median_ppm": candidate,
            "QC_pass": bool(pass_month),
        })
    report = pd.DataFrame(summaries)
    report_file = OUT / "DK-Sor_tower_CO2_monthly_QC_audit_1996_2024.csv"
    report.to_csv(report_file, index=False)
    annual = report.assign(year=report.month.str[:4]).groupby("year").agg(
        good_months=("QC_pass", "sum"),
        months=("QC_pass", "size"),
        daytime_points=("daytime_QC0_points", "sum"),
        daytime_median_ppm=("tower_monthly_daytime_median_ppm", "median"),
    )
    annual.to_csv(OUT / "DK-Sor_tower_CO2_annual_QC_summary.csv")
    print("\nANNUAL AUDIT:\n" + annual.to_string(), flush=True)
    bad = report.loc[~report.QC_pass]
    print(f"\nMonths passing QC: {len(report)-len(bad)}/{len(report)}", flush=True)
    if len(bad):
        print("Failed months (first 35):\n" +
              bad[["month", "daytime_QC0_points",
                   "daytime_QC0_distinct_days"]].head(35).to_string(index=False))
        if NC.exists():
            stop("Earlier forcing file exists but CURRENT audit failed. "
                 "Remove/move stale candidate manually; no simulation prepared.")
        stop(f"{len(bad)} months lack enough QC0 daytime CO2. "
             f"QC report: {report_file}. Need a documented fallback "
             "or a shorter common observation window; no synthetic data created.")

    # Flag implausible jumps between successive month medians for review.
    monthly = report.tower_monthly_daytime_median_ppm.to_numpy(dtype=float)
    large_jumps = np.flatnonzero(np.abs(np.diff(monthly)) > 25)
    if len(large_jumps):
        stop(f"{len(large_jumps)} neighbouring monthly medians jump >25 ppm. "
             "Inspect instrument/provenance before creating climate forcing.")

    if NC.exists():
        stop(f"Target forcing already exists: {NC}; refusing overwrite")
    # One file with 348 monthly samples; only a candidate sensitivity forcing.
    with Dataset(NC, "w", format="NETCDF4_CLASSIC") as f:
        f.createDimension("time", None)
        f.createDimension("lat", 1)
        f.createDimension("lon", 1)
        t = f.createVariable("time", "f8", ("time",))
        lat = f.createVariable("lat", "f8", ("lat",))
        lon = f.createVariable("lon", "f8", ("lon",))
        co2 = f.createVariable("CO2", "f4", ("time", "lat", "lon"),
                               zlib=True, complevel=2, fill_value=-9999.)
        t.units = "days since 1996-01-01 00:00:00"
        t.calendar = "noleap"
        t.long_name = "time"
        t.axis = "T"
        lat.units = "degrees_north"
        lon.units = "degrees_east"
        lat.axis = "Y"
        lon.axis = "X"
        co2.units = "ppmv"
        co2.long_name = "Monthly median daytime QC0 EC tower CO2 mole fraction"
        f.source = str(CSV)
        f.method = ("Median of CO2_F_MDS provider-QC0 records, local clock "
                    "10:00-15:59; require >=40 samples across >=10 days/month. "
                    "No gap filling. Not atmospheric background measurement.")
        f.scientific_limitations = ("CO2_F_MDS may have inlet-height, local "
                                    "canopy and wet/dry-air effects. Confirm "
                                    "ICOS sensor metadata before interpretation.")
        t[:] = date2num(
            [datetime(int(period.year), int(period.month), 15)
             for period in expected_months],
            units=t.units, calendar=t.calendar,
        )
        lat[:] = [LAT]
        lon[:] = [LON]
        co2[:, 0, 0] = monthly.astype("f4")

    with Dataset(NC) as f:
        assert len(f.dimensions["time"]) == 348
        assert np.isfinite(f.variables["CO2"][:]).all()
    manifest = {
        "source": str(CSV),
        "output": str(NC),
        "method": "daytime median of provider QC=0, 10:00-15:59 local station clock",
        "sampling_months": 348,
        "min_days_per_month": MIN_DAYS,
        "min_points_per_month": MIN_POINTS,
        "raw_co2_value_range_filter_ppm": [CO2_LO, CO2_HI],
        "monthly_co2_min_max_ppm": [float(monthly.min()), float(monthly.max())],
        "note": "Experimental site CO2 sensitivity, not automatically equivalent to dry-air background CO2",
    }
    (OUT / "DK-Sor_tower_CO2_candidate_manifest.json").write_text(
        json.dumps(manifest, indent=2))
    print("\nCANDIDATE FORCING READY:", NC, flush=True)
    print("Monthly CO2 range:", round(monthly.min(), 2),
          "to", round(monthly.max(), 2), "ppm")
    print("NOT SUBMITTED. Inspect CO2 tower height and dry/wet convention.")


if __name__ == "__main__":
    main()

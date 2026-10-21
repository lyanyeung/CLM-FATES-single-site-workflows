#!/usr/bin/env python3
"""Stage 04b: read-only FLUXMET_HH + ERA5_HH coverage and source-QC screening.

Uses exact release names; processes CSV in chunks. Screens missing records,
range anomalies, pressure/humidity consistency, QC-code counts, and timestamps.
No gap filling or meteorological source edits are performed.
"""
import argparse
import csv
import math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

BATCH = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DEFAULT_REPORT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
PARAMS = {
    "TA": (-80, 65),
    "VPD": (-0.1, 125),
    "PA": (50, 110),
    "SW_IN": (-5, 1600),
    "LW_IN": (60, 800),
    "WS": (-0.1, 75),
    "P": (-0.001, 300),
}


def load_sites():
    with (BATCH / "sites.tsv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 10:
        raise RuntimeError("Expected exactly ten release manifest rows")
    return rows


def get_file(folder, kind):
    found = sorted(p for p in folder.glob("*.csv") if kind in p.name.upper())
    if len(found) != 1:
        raise RuntimeError("Expected 1 " + kind + " CSV, found " + str(len(found)) +
                           " in " + str(folder))
    return found[0]


def audit_product(site, row, source, suffix, kind, chunksize):
    first, last = int(row["first_year"]), int(row["last_year"])
    filename = get_file(source, kind)
    header = list(pd.read_csv(filename, nrows=0).columns)
    required = ["TIMESTAMP_START"] + [name + suffix for name in PARAMS]
    absent = sorted(set(required) - set(header))
    if absent:
        raise RuntimeError(kind + " missing columns: " + ", ".join(absent))
    qc = [name + suffix + "_QC" for name in PARAMS
          if name + suffix + "_QC" in header]
    chosen = required + qc
    yearly = {year: {"site":site, "source":kind, "year":year,
                     "file":str(filename), "records":0,
                     "duplicate_timestamps":0, "unique_timestamps":0,
                     "invalid_timestamps":0, "outside_release_records":0,
                     "humidity_invalid":0} for year in range(first, last + 1)}
    stamps = {year:set() for year in yearly}
    for r in yearly.values():
        for var in PARAMS:
            r[var + "_valid"] = 0
            r[var + "_missing"] = 0
            r[var + "_range_bad"] = 0
            r[var + "_qc0"] = 0
            r[var + "_qc1"] = 0
            r[var + "_qc2"] = 0
            r[var + "_qc_other"] = 0
    outside_count = 0
    timestamp_bad = 0
    for part in pd.read_csv(filename, usecols=chosen,
                            dtype={"TIMESTAMP_START": "string"},
                            chunksize=chunksize, low_memory=False):
        stamps_str = part["TIMESTAMP_START"].str.strip().str.replace(
            r"\.0$", "", regex=True)
        times = pd.to_datetime(stamps_str, format="%Y%m%d%H%M", errors="coerce")
        timestamp_bad += int(times.isna().sum())
        years = times.dt.year
        outside_count += int((times.notna() & ~years.between(first, last)).sum())
        mask = times.notna() & years.between(first, last)
        # Ignore leap-day records only for an eventual NO_LEAP calendar.
        mask &= ~((times.dt.month == 2) & (times.dt.day == 29))
        if not bool(mask.any()):
            continue
        work = part.loc[mask].copy()
        work["_dt"] = times.loc[mask].to_numpy()
        work["_year"] = work["_dt"].dt.year
        numeric = {}
        for key in PARAMS:
            col = key + suffix
            x = pd.to_numeric(work[col], errors="coerce").to_numpy(dtype=float)
            x[(~np.isfinite(x)) | (x <= -9990)] = np.nan
            numeric[key] = x
        # Source humidity check: TA °C, VPD hPa, PA kPa.
        with np.errstate(all="ignore"):
            t, v, p = numeric["TA"], numeric["VPD"], numeric["PA"] * 1000.0
            es = 611.2 * np.exp(np.clip(17.67 * t / (t + 243.5), -40, 40))
            ea = es - v * 100.0
            specific_humidity = 0.622 * ea / (p - 0.378 * ea)
            testable = np.isfinite(t) & np.isfinite(v) & np.isfinite(p)
            invalid_rh = testable & (
                (ea <= 0) | (ea > es * 1.01) |
                (specific_humidity < 0) | (specific_humidity > 0.08) |
                (~np.isfinite(specific_humidity)))
        for year in sorted(work["_year"].unique()):
            y = int(year)
            take = (work["_year"].to_numpy() == y)
            rec = yearly[y]
            rec["records"] += int(take.sum())
            stamps_in_year = work.loc[take, "_dt"].values.astype(
                "datetime64[m]").astype("int64")
            unique_batch = set(stamps_in_year.tolist())
            rec["duplicate_timestamps"] += len(stamps_in_year) - len(unique_batch)
            rec["duplicate_timestamps"] += len(unique_batch.intersection(stamps[y]))
            stamps[y].update(unique_batch)
            rec["humidity_invalid"] += int(invalid_rh[take].sum())
            for name, (lo, hi) in PARAMS.items():
                values = numeric[name][take]
                valid = np.isfinite(values)
                bad = valid & ((values < lo) | (values > hi))
                rec[name + "_valid"] += int(valid.sum())
                rec[name + "_missing"] += int((~valid).sum())
                rec[name + "_range_bad"] += int(bad.sum())
                qc_name = name + suffix + "_QC"
                if qc_name in work:
                    q = pd.to_numeric(work.loc[take, qc_name],
                                      errors="coerce").to_numpy(dtype=float)
                    for level in (0, 1, 2):
                        rec[name + "_qc" + str(level)] += int((q == level).sum())
                    rec[name + "_qc_other"] += int((~np.isin(q, [0, 1, 2])).sum())
    report = []
    for year, rec in yearly.items():
        rec["unique_timestamps"] = len(stamps[year])
        rec["expected_noleap"] = 17520
        rec["missing_timestamps"] = 17520 - len(stamps[year])
        rec["invalid_timestamps"] = timestamp_bad
        rec["outside_release_records"] = outside_count
        coverages = []
        flagged = []
        if rec["missing_timestamps"] != 0:
            flagged.append("missing timestamps=" + str(rec["missing_timestamps"]))
        if rec["duplicate_timestamps"]:
            flagged.append("duplicate timestamps=" + str(rec["duplicate_timestamps"]))
        for name in PARAMS:
            pct = 100.0 * rec[name + "_valid"] / 17520
            rec[name + "_valid_pct"] = round(pct, 3)
            coverages.append(pct)
            if rec[name + "_range_bad"]:
                flagged.append(name + " out-of-range=" + str(rec[name + "_range_bad"]))
        rec["min_variable_coverage_pct"] = round(min(coverages), 3)
        if min(coverages) < 95.0:
            flagged.append("variable coverage <95%")
        if rec["humidity_invalid"]:
            flagged.append("humidity-invalid=" + str(rec["humidity_invalid"]))
        if timestamp_bad:
            flagged.append("unparseable timestamps=" + str(timestamp_bad))
        rec["issues"] = " | ".join(flagged)
        rec["status"] = "REVIEW" if flagged else "COVERAGE_CANDIDATE"
        report.append(rec)
    print("  %-11s %s: %d annual rows; %d REVIEW years; unparseable=%d; outside-window=%d" %
          (kind, site, len(report),
           sum(r["status"] == "REVIEW" for r in report),
           timestamp_bad, outside_count), flush=True)
    return report


def save(path, rows):
    if not rows:
        return
    cols = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--chunksize", type=int, default=120000)
    args = parser.parse_args()
    if args.chunksize < 1000:
        parser.error("chunksize must be >=1000")
    all_rows, failed = [], []
    for row in load_sites():
        site, package = row["site"], row["package"]
        raw = args.root / site / "forcing" / "raw" / package
        print("\n====", site, "====", flush=True)
        for kind, suffix in (("FLUXMET_HH", "_F"), ("ERA5_HH", "_ERA")):
            try:
                all_rows.extend(audit_product(
                    site, row, raw, suffix, kind, args.chunksize))
            except Exception as exc:
                failed.append(dict(site=site, source=kind, error=str(exc)))
                print("  FAILED:", kind, str(exc), flush=True)
    report_dir = args.report_root / ("stage04b_met_" +
                  datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    report_dir.mkdir(parents=True, exist_ok=False)
    save(report_dir / "annual_source_coverage_and_QC.csv", all_rows)
    save(report_dir / "source_failures.csv", failed)
    print("\nSTAGE04B SUMMARY: %d annual source/year records; %d source failures; %d REVIEW source-years" %
          (len(all_rows), len(failed),
           sum(x["status"] == "REVIEW" for x in all_rows)))
    print("REPORT DIR:", report_dir)
    print("Raw FLUXMET and ERA5 files unchanged; NO fixes or DATM produced.")
    print("Flagged records require source-by-source scientific investigation.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

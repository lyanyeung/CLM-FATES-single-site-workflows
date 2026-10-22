#!/usr/bin/env python3
"""Stage04b: full-release source meteorology inventory and screening, no repairs.

Preserve native HH/HR (US-MMS hourly). Screen FLUXMET/FULLSET and paired ERA5
separately. Write reports only; do not modify sources, surfaces or model cases.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from uuid import uuid4
import numpy as np
import pandas as pd

BATCH = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("FLUXNET_SITES_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
# Same broad numerical review bounds as Batch01, not official acceptance limits.
BOUNDS = {"TA": (-80, 65), "VPD": (-0.1, 125), "PA": (50, 110),
          "SW_IN": (-5, 1600), "LW_IN": (60, 800), "WS": (-0.1, 75), "P": (-0.001, 300)}
UNITS = {"TA": "degC", "VPD": "hPa", "PA": "kPa", "SW_IN": "W m-2",
         "LW_IN": "W m-2", "WS": "m s-1", "P": "mm per native interval"}
EVENT_FIELDS = ["site", "source", "file", "source_csv_row", "TIMESTAMP_START", "TIMESTAMP_END",
                "flags", "RH_liquid_pct", "specific_humidity_kgkg"] + list(BOUNDS) + [v + "_QC" for v in BOUNDS]
TIME_FIELDS = ["site", "source", "file", "source_csv_row", "TIMESTAMP_START", "TIMESTAMP_END", "flags"]
GAP_FIELDS = ["site", "source", "year", "variable", "reason", "start", "end", "records", "hours"]


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(data)
    return value.hexdigest()


def save_csv(path, rows, fields=None):
    if not rows and fields is None:
        path.write_text("", encoding="utf-8")
        return
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_sites():
    with (BATCH / "sites.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != 10 or len({r["site"] for r in rows}) != 10:
        raise ValueError("Expected ten unique Batch03 releases")
    for row in rows:
        if not re.fullmatch(r"US-[A-Za-z0-9]+", row["site"]) or not re.fullmatch(
                r"AMF_" + re.escape(row["site"]) + r"_FLUXNET_[A-Za-z0-9_.-]+", row["package"]):
            raise ValueError("Invalid manifest site/package")
    return rows


def resolve(row, root, companion):
    site, package = row["site"], row["package"]
    raw = root / site / "forcing/raw" / package
    resolution = "HR" if site == "US-MMS" else "HH"  # Confirmed Batch03 Stage02 native formats.
    product = "ERA5" if companion else ("FULLSET" if "_FULLSET_" in package else "FLUXMET")
    source = product + "_" + resolution
    version = package.split(row["first_year"] + "-" + row["last_year"] + "_", 1)[1]
    pattern = re.compile(r"^AMF_" + re.escape(site) + "_FLUXNET_" + product + "_" + resolution
                         + r"_(\d{4})-(\d{4})_" + re.escape(version) + r"\.csv$", re.I)
    found = [p for p in raw.glob("*.csv") if pattern.fullmatch(p.name)]
    if len(found) != 1 or found[0].is_symlink():
        raise ValueError("Expected exactly one exact-release {} file, found {} in {}".format(source, len(found), raw))
    filename = found[0]
    if not companion and pattern.fullmatch(filename.name).groups() != (row["first_year"], row["last_year"]):
        raise ValueError("Primary file year label differs from pinned release")
    header = list(pd.read_csv(filename, nrows=0).columns)
    if not {"TIMESTAMP_START", "TIMESTAMP_END"}.issubset(header):
        raise ValueError("Missing start/end timestamps: " + str(filename))
    columns, qc = {}, {}
    for key in BOUNDS:
        candidates = [key + "_ERA"] if companion else [key + "_F", key + "_F_MDS"]
        column = next((c for c in candidates if c in header), None)
        if column is None:
            raise ValueError("{} missing {}; considered {}".format(filename.name, key, candidates))
        columns[key] = column
        qc[key] = column + "_QC" if column + "_QC" in header else None
    return {"site": site, "source": source, "file": str(filename), "columns": columns,
            "qc_columns": qc, "header": header, "resolution": resolution,
            "interval_minutes": 60 if resolution == "HR" else 30,
            "first_year": int(row["first_year"]), "last_year": int(row["last_year"]),
            "units_assumption": UNITS, "column_selection": "one column per variable; no row-wise fallback"}


def times(series):
    strings = series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    strings = strings.where(strings.str.fullmatch(r"\d{12}", na=False))
    return pd.to_datetime(strings, format="%Y%m%d%H%M", errors="coerce")


def numeric(series):
    result = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    result[(~np.isfinite(result)) | (result <= -9990)] = np.nan
    return result


def gap_rows(writer, spec, year, variable, mask, index, reason):
    positions = np.flatnonzero(mask)
    if not len(positions):
        return 0
    groups = np.split(positions, np.flatnonzero(np.diff(positions) > 1) + 1)
    for group in groups:
        writer.writerow({"site": spec["site"], "source": spec["source"], "year": year,
                         "variable": variable, "reason": reason,
                         "start": index[group[0]].strftime("%Y%m%d%H%M"),
                         "end": index[group[-1]].strftime("%Y%m%d%H%M"),
                         "records": len(group), "hours": len(group) * spec["interval_minutes"] / 60})
    return len(groups)


def audit(spec, chunksize, events, time_events, gaps):
    path = Path(spec["file"])
    before = (path.stat().st_size, path.stat().st_mtime_ns)
    first, last, step = spec["first_year"], spec["last_year"], spec["interval_minutes"]
    yearly = {year: [] for year in range(first, last + 1)}
    totals = dict(source_records=0, invalid_start=0, invalid_end=0, bad_interval=0,
                  outside_release_records=0, leap_day_records_in_release=0, nonincreasing_source_records=0)
    usecols = ["TIMESTAMP_START", "TIMESTAMP_END"] + list(spec["columns"].values())
    usecols += [column for column in spec["qc_columns"].values() if column]
    previous = None
    for part in pd.read_csv(path, usecols=list(dict.fromkeys(usecols)), dtype="string", chunksize=chunksize):
        start, end = times(part["TIMESTAMP_START"]), times(part["TIMESTAMP_END"])
        valid = start.notna()
        interval_good = start.notna() & end.notna() & ((end - start).dt.total_seconds() == step * 60)
        totals["invalid_start"] += int((~valid).sum())
        totals["invalid_end"] += int(end.isna().sum())
        totals["bad_interval"] += int((valid & end.notna() & ~interval_good).sum())
        raw_positions = np.flatnonzero(valid.to_numpy())
        ordered = start.iloc[raw_positions].astype("int64").to_numpy()
        out_of_order = np.zeros(len(part), dtype=bool)
        if len(ordered):
            bad = np.r_[previous is not None and ordered[0] <= previous, np.diff(ordered) <= 0]
            out_of_order[raw_positions] = bad
            totals["nonincreasing_source_records"] += int(bad.sum())
            previous = ordered[-1]
        timing_bad = (~valid | end.isna() | (valid & end.notna() & ~interval_good)).to_numpy() | out_of_order
        for i in np.flatnonzero(timing_bad):
            flags = []
            if pd.isna(start.iloc[i]): flags.append("INVALID_START")
            if pd.isna(end.iloc[i]): flags.append("INVALID_END")
            if pd.notna(start.iloc[i]) and pd.notna(end.iloc[i]) and not interval_good.iloc[i]: flags.append("WRONG_NATIVE_INTERVAL")
            if out_of_order[i]: flags.append("NONINCREASING_SOURCE_TIME")
            time_events.writerow({"site": spec["site"], "source": spec["source"], "file": str(path),
                                  "source_csv_row": totals["source_records"] + i + 2,
                                  "TIMESTAMP_START": part["TIMESTAMP_START"].iloc[i],
                                  "TIMESTAMP_END": part["TIMESTAMP_END"].iloc[i], "flags": "|".join(flags)})
        years = start.dt.year
        within = valid & years.between(first, last)
        leap = (start.dt.month == 2) & (start.dt.day == 29)
        totals["outside_release_records"] += int((valid & ~years.between(first, last)).sum())
        totals["leap_day_records_in_release"] += int((within & leap).sum())
        keep = within & ~leap
        if bool(keep.any()):
            work = pd.DataFrame({"start": start.loc[keep], "end": end.loc[keep],
                                 "interval_good": interval_good.loc[keep]})
            work["csv_row"] = totals["source_records"] + np.flatnonzero(keep.to_numpy()) + 2
            for key, column in spec["columns"].items():
                work[key] = numeric(part.loc[keep, column])
                qcol = spec["qc_columns"][key]
                work[key + "_QC"] = numeric(part.loc[keep, qcol]) if qcol else np.nan
            for year, group in work.groupby(work["start"].dt.year):
                yearly[int(year)].append(group)
        totals["source_records"] += len(part)
    result = []
    for year, pieces in yearly.items():
        index = pd.date_range(str(year) + "-01-01", str(year + 1) + "-01-01", freq=str(step) + "min")[:-1]
        index = index[~((index.month == 2) & (index.day == 29))]
        expected = len(index)
        work = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(
            columns=["start", "end", "interval_good", "csv_row"] + list(BOUNDS) + [v + "_QC" for v in BOUNDS])
        positions = index.get_indexer(pd.DatetimeIndex(work["start"]))
        aligned = positions >= 0
        counts = np.bincount(positions[aligned], minlength=expected)
        good_interval = work["interval_good"].to_numpy(dtype=bool)
        rec = {"site": spec["site"], "source": spec["source"], "year": year, "file": str(path),
               "native_minutes": step, "records": len(work), "expected_noleap": expected,
               "unique_on_grid": int((counts > 0).sum()), "missing_timestamps": int((counts == 0).sum()),
               "duplicate_timestamps": int(np.maximum(counts - 1, 0).sum()),
               "off_grid_timestamps": int((~aligned).sum()), "invalid_intervals": int((~good_interval).sum())}
        rec["timestamp_gap_episodes"] = gap_rows(gaps, spec, year, "TIMESTAMP", counts == 0, index, "absent_native_timestamp")
        for i in np.flatnonzero(~aligned):
            time_events.writerow({"site": spec["site"], "source": spec["source"], "file": str(path),
                                  "source_csv_row": int(work["csv_row"].iloc[i]),
                                  "TIMESTAMP_START": work["start"].iloc[i].strftime("%Y%m%d%H%M"),
                                  "TIMESTAMP_END": work["end"].iloc[i], "flags": "OFF_NATIVE_TIME_GRID"})
        flags = {}
        values = {}
        for key, (lo, hi) in BOUNDS.items():
            x = work[key].to_numpy(dtype=float)
            values[key] = x
            valid_x = np.isfinite(x)
            bad = valid_x & ((x < lo) | (x > hi))
            flags[key + "_RANGE"] = bad
            usable = np.zeros(expected, dtype=bool)
            take = valid_x & aligned & good_interval
            usable[positions[take]] = True
            rec[key + "_finite_records"] = int(valid_x.sum())
            rec[key + "_missing_records"] = int((~valid_x).sum())
            rec[key + "_range_bad"] = int(bad.sum())
            rec[key + "_valid_unique_pct"] = round(float(usable.mean() * 100), 5)
            rec[key + "_min"] = float(x[valid_x].min()) if valid_x.any() else None
            rec[key + "_max"] = float(x[valid_x].max()) if valid_x.any() else None
            rec[key + "_gap_episodes"] = gap_rows(gaps, spec, year, key, ~usable, index, "no_finite_value_at_valid_native_interval")
            q = work[key + "_QC"].to_numpy(dtype=float)
            rec[key + "_qc_available"] = bool(spec["qc_columns"][key])
            for code in (0, 1, 2): rec[key + "_qc" + str(code)] = int((q == code).sum())
            rec[key + "_qc_missing"] = int((~np.isfinite(q)).sum())
            rec[key + "_qc_other"] = int((np.isfinite(q) & ~np.isin(q, [0, 1, 2])).sum())
        with np.errstate(all="ignore"):
            t, v, p = values["TA"], values["VPD"], values["PA"] * 1000
            es = 611.2 * np.exp(np.clip(17.67 * t / (t + 243.5), -40, 40))
            ea = es - v * 100
            rh = ea / es * 100
            denominator = p - 0.378 * ea
            q = 0.622 * ea / denominator
            testable = np.isfinite(t) & np.isfinite(v) & np.isfinite(p) & (p > 0) & (t > -150)
            flags["HUMIDITY_INVALID"] = testable & ((ea <= 0) | (rh > 101) | (denominator <= 0) | (q < 0) | (q > 0.08) | ~np.isfinite(q))
            for threshold in (1, 5, 10):
                flags["RH_LT" + str(threshold)] = testable & (rh > 0) & (rh < threshold)
        for key in ("HUMIDITY_INVALID", "RH_LT1", "RH_LT5", "RH_LT10"):
            rec[key] = int(flags[key].sum())
        flagged = np.logical_or.reduce(list(flags.values()))
        rec["flagged_source_records"] = int(flagged.sum())
        for i in np.flatnonzero(flagged):
            event = {"site": spec["site"], "source": spec["source"], "file": str(path),
                     "source_csv_row": int(work["csv_row"].iloc[i]),
                     "TIMESTAMP_START": work["start"].iloc[i].strftime("%Y%m%d%H%M"),
                     "TIMESTAMP_END": work["end"].iloc[i].strftime("%Y%m%d%H%M") if pd.notna(work["end"].iloc[i]) else "",
                     "flags": "|".join(key for key, mask in flags.items() if mask[i]),
                     "RH_liquid_pct": float(rh[i]) if testable[i] and np.isfinite(rh[i]) else "",
                     "specific_humidity_kgkg": float(q[i]) if testable[i] and np.isfinite(q[i]) else ""}
            for key in BOUNDS:
                for column in (key, key + "_QC"):
                    val = float(work[column].iloc[i]); event[column] = val if np.isfinite(val) else ""
            events.writerow(event)
        needs_review = (any(rec[key] for key in ("missing_timestamps", "duplicate_timestamps", "off_grid_timestamps", "invalid_intervals", "flagged_source_records"))
                        or any(rec[key + "_valid_unique_pct"] < 100 for key in BOUNDS)
                        or totals["invalid_start"] > 0 or totals["invalid_end"] > 0 or totals["nonincreasing_source_records"] > 0)
        rec["status"] = "REVIEW" if needs_review else "NO_FLAGS_IN_THIS_SCREEN"
        result.append(rec)
    if before != (path.stat().st_size, path.stat().st_mtime_ns):
        raise RuntimeError("Source changed during audit; reports must not be used: " + str(path))
    spec.update(totals)
    spec["sha256"] = digest(path)
    spec["review_years"] = sum(r["status"] == "REVIEW" for r in result)
    spec["flagged_source_records"] = sum(r["flagged_source_records"] for r in result)
    print("  {} {}: {} source-years; REVIEW={}; flagged native records={}; native={}min".format(
        spec["site"], spec["source"], len(result), spec["review_years"], spec["flagged_source_records"], step), flush=True)
    return result


def main():
    rows = load_sites()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--sites", nargs="+", choices=[r["site"] for r in rows])
    parser.add_argument("--chunksize", type=int, default=120000)
    parser.add_argument("--check", action="store_true", help="Check pinned source files/headers only; write nothing")
    args = parser.parse_args()
    if args.chunksize < 1000: parser.error("chunksize must be >=1000")
    root = args.root.expanduser()
    chosen = [row for row in rows if not args.sites or row["site"] in args.sites]
    specs, failures = [], []
    print("PYTHON:", sys.executable, flush=True)
    for row in chosen:
        for companion in (False, True):
            try:
                spec = resolve(row, root, companion)
                specs.append(spec)
                print("PINNED:", spec["site"], spec["source"], spec["file"], spec["columns"], flush=True)
            except (OSError, ValueError, KeyError, IndexError) as exc:
                failures.append({"site": row["site"], "source": "ERA5" if companion else "PRIMARY", "error": str(exc)})
                print("SOURCE CHECK FAILED:", failures[-1], flush=True)
    if args.check:
        print("SOURCE PREFLIGHT: {}/{} sources; {} failures; no data/reports written".format(len(specs), 2 * len(chosen), len(failures)))
        return 2 if failures else 0
    report_root = args.report_root.expanduser() if args.report_root else root.parent.parent / "experiments/AmeriFlux_MultiSite_10_Batch03/reports"
    run = report_root / ("stage04b_met_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    all_rows, completed = [], []
    with (run / "physical_anomaly_records.csv").open("x", newline="") as ef, (run / "timestamp_issues.csv").open("x", newline="") as tf, (run / "missing_episodes.csv").open("x", newline="") as gf:
        events, time_events, gaps = (csv.DictWriter(ef, fieldnames=EVENT_FIELDS), csv.DictWriter(tf, fieldnames=TIME_FIELDS), csv.DictWriter(gf, fieldnames=GAP_FIELDS))
        for writer in (events, time_events, gaps): writer.writeheader()
        for spec in specs:
            try:
                all_rows.extend(audit(spec, args.chunksize, events, time_events, gaps))
                completed.append(spec)
            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
                failures.append({"site": spec["site"], "source": spec["source"], "error": str(exc)})
                print("AUDIT FAILED:", failures[-1], flush=True)
    save_csv(run / "annual_source_coverage_and_QC.csv", all_rows)
    save_csv(run / "source_failures.csv", failures, ["site", "source", "error"])
    with (run / "source_inventory.json").open("x", encoding="utf-8") as stream:
        json.dump({"completed": completed, "failures": failures, "scope": "NO_LEAP screening at native site timestamps; no time-zone conversion or source repairs",
                   "caveats": "Screening bounds are exploratory; RH uses liquid-water saturation. ERA5 companion is not assumed independent ground truth. QC codes are counted without universal provenance interpretation."}, stream, indent=2, allow_nan=False)
    print("\nSTAGE04B SUMMARY: {}/{} sources audited; {} source failures; {} REVIEW source-years; {} flagged native records".format(
        len(completed), 2 * len(chosen), len(failures), sum(r["status"] == "REVIEW" for r in all_rows), sum(r["flagged_source_records"] for r in all_rows)))
    print("REPORT DIR:", run)
    print("Source data and surfaces unchanged. No interpolation, ERA replacement, ERA5-Land download, forcing/DATM or model jobs performed.")
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

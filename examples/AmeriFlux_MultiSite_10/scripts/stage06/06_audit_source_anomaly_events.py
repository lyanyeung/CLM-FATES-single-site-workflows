#!/usr/bin/env python3
"""AmeriFlux Stage 06: inspect exact timestamps of Stage 04 source anomalies.

Input CSVs and NetCDF surfaces are read-only. Uses original 10 pinned releases
and only source-years previously flagged REVIEW. Does not gap-fill or create DATM.
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BATCH = Path(__file__).resolve().parents[2]
SITE_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORT_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
LIMITS = {
    "TA": (-80.0, 65.0), "VPD": (-0.1, 125.0),
    "PA": (50.0, 110.0), "SW_IN": (-5.0, 1600.0),
    "LW_IN": (60.0, 800.0), "WS": (-0.1, 75.0),
    "P": (-0.001, 300.0),
}
SOURCES = {"FLUXMET_HH": "_F", "ERA5_HH": "_ERA"}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t" if path.suffix == ".tsv" else ","))


def unique_file(folder, token):
    matches = sorted(p for p in folder.glob("*.csv") if token in p.name.upper())
    if len(matches) != 1:
        raise RuntimeError("Expected one %s under %s, found %d" %
                           (token, folder, len(matches)))
    return matches[0]


def numeric(values):
    a = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    a[~np.isfinite(a) | (a <= -9990)] = np.nan
    return a


def audit_source(site, source, suffix, path, years, chunksize):
    header = list(pd.read_csv(path, nrows=0).columns)
    variables = ["TIMESTAMP_START"] + [v + suffix for v in LIMITS]
    missing = sorted(set(variables) - set(header))
    if missing:
        raise RuntimeError("Missing required columns: %s" % missing)
    qcs = [v + suffix + "_QC" for v in LIMITS if v + suffix + "_QC" in header]
    fields = variables + qcs
    target = set(years)
    counts = defaultdict(Counter)
    events = []
    for chunk in pd.read_csv(path, usecols=fields, chunksize=chunksize,
                             dtype={"TIMESTAMP_START": "string"}, low_memory=False):
        rawtime = chunk["TIMESTAMP_START"].str.strip().str.replace(
            r"\.0$", "", regex=True)
        stamps = pd.to_datetime(rawtime, format="%Y%m%d%H%M", errors="coerce")
        choose = stamps.dt.year.isin(target)
        if not bool(choose.any()):
            continue
        work = chunk.loc[choose].reset_index(drop=True)
        time = stamps.loc[choose].reset_index(drop=True)
        yr = time.dt.year.to_numpy(dtype=int)
        vals = {v: numeric(work[v + suffix]) for v in LIMITS}
        with np.errstate(all="ignore"):
            es = 611.2 * np.exp(np.clip(
                17.67 * vals["TA"] / (vals["TA"] + 243.5), -40, 40))
            ea = es - vals["VPD"] * 100.0
            pa = vals["PA"] * 1000.0
            q = 0.622 * ea / (pa - 0.378 * ea)
            rh = 100.0 * ea / es
            testable = np.isfinite(vals["TA"]) & np.isfinite(vals["VPD"]) & np.isfinite(pa)
            bad_rh = testable & (
                (ea <= 0) | (ea > 1.01 * es) | (q < 0) |
                (q > 0.08) | (~np.isfinite(q)))
        ranges = {}
        for v, (lo, hi) in LIMITS.items():
            x = vals[v]
            ranges[v] = np.isfinite(x) & ((x < lo) | (x > hi))
        anybad = bad_rh.copy()
        for b in ranges.values():
            anybad |= b
        if not anybad.any():
            continue
        for i in np.flatnonzero(anybad):
            y = int(yr[i])
            flags = []
            if bad_rh[i]:
                counts[y]["humidity_invalid"] += 1
                if ea[i] <= 0:
                    flags.append("EA_NONPOSITIVE")
                if ea[i] > 1.01 * es[i]:
                    flags.append("SUPERSATURATION")
                if not np.isfinite(q[i]) or q[i] < 0 or q[i] > 0.08:
                    flags.append("Q_SPECIFIC_INVALID")
            for v, b in ranges.items():
                if b[i]:
                    counts[y][v + "_range_bad"] += 1
                    flags.append(v + "_RANGE")
            record = {
                "site":site, "source":source,
                "timestamp":time.iloc[i].strftime("%Y-%m-%d %H:%M"),
                "year":y, "flags":"|".join(flags),
                "derived_RH_pct":float(rh[i]) if np.isfinite(rh[i]) else "",
                "derived_ea_hPa":float(ea[i] / 100) if np.isfinite(ea[i]) else "",
                "derived_Q_kgkg":float(q[i]) if np.isfinite(q[i]) else "",
            }
            for v in LIMITS:
                number = vals[v][i]
                record[v] = float(number) if np.isfinite(number) else ""
                qc = v + suffix + "_QC"
                record[v + "_QC"] = (
                    str(work.at[i, qc]) if qc in qcs and pd.notna(work.at[i, qc]) else "")
            events.append(record)
    return events, counts


def write_csv(path, data, columns):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sites-root", type=Path, default=SITE_ROOT)
    p.add_argument("--report-root", type=Path, default=REPORT_ROOT)
    p.add_argument("--stage04-dir", type=Path,
                   help="Use a specific stage04b_met_* directory instead of latest")
    p.add_argument("--sites", nargs="+", help="Subset of the ten site codes")
    p.add_argument("--chunksize", type=int, default=80000)
    args = p.parse_args()
    if args.chunksize < 1000:
        p.error("--chunksize must be >=1000")
    manifest = read_csv(BATCH / "sites.tsv")
    if len(manifest) != 10 or len({r["site"] for r in manifest}) != 10:
        raise RuntimeError("Expected exactly ten unique sites in manifest")
    names = {r["site"] for r in manifest}
    if args.sites and not set(args.sites).issubset(names):
        p.error("Unknown site in --sites")
    selected = set(args.sites or names)
    if args.stage04_dir:
        report = args.stage04_dir
    else:
        found = sorted(x for x in args.report_root.glob("stage04b_met_*")
                       if (x / "annual_source_coverage_and_QC.csv").is_file())
        if not found:
            raise RuntimeError("Stage04b annual report not found")
        report = found[-1]
    annual = read_csv(report / "annual_source_coverage_and_QC.csv")
    review = {(r["site"], r["source"], int(r["year"])):r
              for r in annual if r["status"] == "REVIEW" and r["site"] in selected}
    # Input preflight: ensure all selected exact-release sources are available
    # before expensive scans or report output.
    jobs = []
    for row in manifest:
        site = row["site"]
        if site not in selected:
            continue
        raw = args.sites_root / site / "forcing" / "raw" / row["package"]
        for source, suffix in SOURCES.items():
            years = sorted(y for (s, src, y) in review if s == site and src == source)
            if years:
                jobs.append((site, source, suffix, unique_file(raw, source), years))
    events, summary, mismatch = [], [], []
    for site, source, suffix, file, years in jobs:
        print("AUDIT %-7s %-11s %d REVIEW years" % (site, source, len(years)), flush=True)
        found, counts = audit_source(
            site, source, suffix, file, years, args.chunksize)
        events.extend(found)
        summary.append({"site":site, "source":source,
                        "review_years":len(years), "anomaly_timestamps":len(found)})
        for year in years:
            expected = review[(site, source, year)]
            for col in ("humidity_invalid",) + tuple(v + "_range_bad" for v in LIMITS):
                actual = counts[year][col]
                original = int(float(expected.get(col) or 0))
                if actual != original:
                    mismatch.append(
                        "%s %s %s %s: Stage04=%d Stage06=%d" %
                        (site, source, year, col, original, actual))
    # Compare exact local-standard timestamps across different sites;
    # shared timestamps are signals for investigation, not proof of a shared bug.
    clusters = defaultdict(lambda: {"sites":set(), "flags":set()})
    for e in events:
        key = (e["source"], e["timestamp"])
        clusters[key]["sites"].add(e["site"])
        clusters[key]["flags"].update(e["flags"].split("|"))
    shared = [
        {"source":source, "timestamp":ts,
         "site_count":len(info["sites"]),
         "sites":",".join(sorted(info["sites"])),
         "flags":",".join(sorted(info["flags"]))}
        for (source, ts), info in clusters.items()
        if len(info["sites"]) >= 3
    ]
    events.sort(key=lambda x:(x["timestamp"],x["site"],x["source"]))
    shared.sort(key=lambda x:(-x["site_count"],x["timestamp"],x["source"]))
    folder = args.report_root / ("stage06_anomalies_" +
             datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    folder.mkdir(parents=True, exist_ok=False)
    event_fields = (
        ["site","source","timestamp","year","flags",
         "derived_RH_pct","derived_ea_hPa","derived_Q_kgkg"] +
        list(LIMITS) + [v + "_QC" for v in LIMITS])
    write_csv(folder / "flagged_source_timestamps.csv", events, event_fields)
    write_csv(folder / "cross_site_timestamp_clusters.csv", shared,
              ["source","timestamp","site_count","sites","flags"])
    write_csv(folder / "source_summary.csv", summary,
              ["site","source","review_years","anomaly_timestamps"])
    if mismatch:
        (folder / "audit_mismatch.txt").write_text(
            "\n".join(mismatch) + "\n", encoding="utf-8")
    print("\nSTAGE06:",len(events),"source/site/timestamp events;",
          len(shared),"multi-site same-time groups (>=3 sites)")
    print("Stage04 / Stage06 discrepancy count:",len(mismatch))
    if mismatch:
        print("MISMATCH examples:", " | ".join(mismatch[:6]))
    print("REPORT DIR:",folder)
    print("No changes to original FLUXMET/ERA5, CTSM surfaces, DATM or Slurm jobs.")
    return 2 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())

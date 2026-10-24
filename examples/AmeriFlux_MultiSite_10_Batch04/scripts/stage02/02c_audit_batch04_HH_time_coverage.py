#!/usr/bin/env python3
"""Batch04 Stage02C: read-only full native FLUXMET_HH timeline/basic QC inventory.

No repairs, UTC offset assignments, coordinate selection, forcing, surface,
PFT/ZBOT choices, CIME cases or Slurm jobs. Printed flags require human review.
"""
import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
import math

BASE = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
FIELDS = {
    "TA": ("TA_F", "TA_F_MDS", "TA"),
    "VPD": ("VPD_F", "VPD_F_MDS", "VPD"),
    "PA": ("PA_F", "PA_F_MDS", "PA"),
    "RH": ("RH_F", "RH"),
    "P": ("P_F", "P_F_MDS", "P"),
    "WS": ("WS_F", "WS"),
    "SW_IN": ("SW_IN_F", "SW_IN"),
    "LW_IN": ("LW_IN_F", "LW_IN"),
}
MISSING = {"", "NA", "NAN", "-9999", "-9999.0", "-6999", "-6999.0"}


def read_manifest():
    with (BASE / "sites.tsv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != 10 or len({r["site"] for r in rows}) != 10:
        raise ValueError("Expected ten unique Batch04 sites")
    return rows


def stamp(s):
    s = s.strip()
    if len(s) != 12 or not s.isdigit():
        raise ValueError("Invalid timestamp " + repr(s))
    return datetime.strptime(s, "%Y%m%d%H%M")


def numeric(raw):
    s = raw.strip()
    if s.upper() in MISSING:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) and v not in (-9999, -6999) else None


def inspect(site, package, sites_root):
    raw = sites_root / site / "forcing" / "raw" / package
    if not raw.is_dir() or raw.is_symlink():
        raise ValueError("Missing or symlinked raw directory " + str(raw))
    files = list(raw.glob("AMF_" + site + "_FLUXNET_FLUXMET_HH_*.csv"))
    if len(files) != 1 or files[0].is_symlink() or not files[0].is_file():
        raise ValueError("Expected one regular source FLUXMET_HH file")
    path = files[0]
    counts, available, missing = Counter(), Counter(), Counter()
    minima, maxima = {}, {}
    first_start = last_end = previous_end = None
    print("\n=== {} | {} ===".format(site, path.name), flush=True)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if len(set(header)) != len(header):
            raise ValueError("Duplicate CSV header names")
        indices = {name: i for i, name in enumerate(header)}
        if "TIMESTAMP_START" not in indices or "TIMESTAMP_END" not in indices:
            raise ValueError("Missing timestamp columns")
        chosen = {}
        for kind, alternatives in FIELDS.items():
            for name in alternatives:
                if name in indices:
                    chosen[kind] = (name, indices[name])
                    break
        print("SELECTED COLUMNS:", " ".join(
            "{}={}".format(k, chosen[k][0] if k in chosen else "NOT_FOUND")
            for k in FIELDS))
        for row in reader:
            counts["rows"] += 1
            if len(row) != len(header):
                counts["bad_width"] += 1
                continue
            try:
                start = stamp(row[indices["TIMESTAMP_START"]])
                end = stamp(row[indices["TIMESTAMP_END"]])
            except ValueError:
                counts["invalid_timestamp"] += 1
                continue
            if first_start is None:
                first_start = start
            last_end = end
            if (end - start).total_seconds() != 1800:
                counts["non_30_min_rows"] += 1
            if previous_end is not None:
                if start > previous_end:
                    counts["gaps"] += 1
                    counts["missing_HH_slots"] += max(0, int(
                        (start - previous_end).total_seconds() // 1800))
                elif start < previous_end:
                    counts["overlap_or_order_error"] += 1
            previous_end = end
            for kind, (_, i) in chosen.items():
                v = numeric(row[i])
                if v is None:
                    missing[kind] += 1
                    continue
                available[kind] += 1
                minima[kind] = min(v, minima.get(kind, v))
                maxima[kind] = max(v, maxima.get(kind, v))
                if kind == "VPD" and v < 0:
                    counts["negative_VPD"] += 1
                if kind == "RH":
                    if v < 0:
                        counts["negative_RH"] += 1
                    if v < 1:
                        counts["RH_below_1pct"] += 1
                if kind == "PA" and v <= 0:
                    counts["nonpositive_PA"] += 1
                if kind == "WS" and v < 0:
                    counts["negative_WS"] += 1
                if kind == "P" and v < 0:
                    counts["negative_P"] += 1
    print("TIMELINE: first_start={} last_end={} rows={}".format(
        first_start, last_end, counts["rows"]))
    timeflags = ("bad_width", "invalid_timestamp", "non_30_min_rows", "gaps",
                 "missing_HH_slots", "overlap_or_order_error")
    for key in timeflags:
        print("TIME_FLAG {}={}".format(key, counts[key]))
    for kind in FIELDS:
        if kind not in chosen:
            print("VALUE {}: NOT_FOUND (not a scientific missing-data conclusion)".format(kind))
        else:
            print("VALUE {}: {} valid={} missing={} min={} max={}".format(
                kind, chosen[kind][0], available[kind], missing[kind],
                minima.get(kind, "NA"), maxima.get(kind, "NA")))
    for key in ("negative_VPD", "negative_RH", "RH_below_1pct",
                "nonpositive_PA", "negative_WS", "negative_P"):
        print("SCIENCE_REVIEW_FLAG {}={}".format(key, counts[key]))
    review = any(counts[k] for k in timeflags)
    print("TIME_GATE:", "REVIEW" if review else "PASS")
    print("No edits, conversions, repairs or model jobs.")
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--sites", nargs="+")
    args = parser.parse_args()
    manifest = read_manifest()
    catalog = {r["site"]: r for r in manifest}
    selected = args.sites or [r["site"] for r in manifest]
    if len(set(selected)) != len(selected) or set(selected) - set(catalog):
        parser.error("Sites must be distinct Batch04 site IDs")
    passed, review, failed = [], [], []
    print("BATCH04 STAGE02C READ-ONLY FULL HH TIMELINE AND BASIC QC")
    for site in selected:
        try:
            if inspect(site, catalog[site]["package"], args.sites_root):
                review.append(site)
            else:
                passed.append(site)
        except (OSError, ValueError, csv.Error) as error:
            failed.append(site)
            print("FAILED {}: {}".format(site, error), flush=True)
    print("\nSTAGE02C SUMMARY: time_pass={} review={} failed={}".format(
        len(passed), ",".join(review) or "none", ",".join(failed) or "none"))
    print("Time PASS is not scientific QC approval; no repairs are authorized.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Batch04 Stage04: read-only lineage and neighbour audit for extreme met values.

Compare original FLUXMET_HH and packaged ERA5_HH values at exactly matching
timestamp labels, showing a +/-1 hour neighbourhood and native QC fields.
The packaged *_ERA columns may be downscaled/regressed FLUXNET products, not
independent ECMWF ERA5. Never treat equality as independent validation.
No edits, UTC shifts, ERA replacement, mixing or forcing generation.
"""
import argparse
import csv
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
ANCHORS = {
    "US-SP1": ("200412040100", "201610091930", "201610092000", "201610092030"),
    "US-Syv": ("200412032330", "200412040000", "200412040030",
               "202102091800", "202505160230"),
    "US-Ton": ("200302270430", "200412032130", "200412032200",
               "200412032230", "202511161000"),
}
COLUMNS = (
    "TA", "TA_F_MDS", "TA_F_MDS_QC", "TA_F", "TA_F_QC", "TA_ERA",
    "PA", "PA_F", "PA_F_QC", "PA_ERA",
    "VPD", "VPD_F_MDS", "VPD_F_MDS_QC", "VPD_F", "VPD_F_QC", "VPD_ERA",
    "RH", "RH_F", "RH_ERA"
)


def selected_times(anchors):
    needed = set()
    for a in anchors:
        origin = datetime.strptime(a, "%Y%m%d%H%M")
        for step in (-2, -1, 0, 1, 2):
            needed.add((origin + timedelta(minutes=30 * step)).strftime("%Y%m%d%H%M"))
    return sorted(needed)


def read_manifest():
    with (HERE / "sites.tsv").open(encoding="utf-8-sig", newline="") as stream:
        data = list(csv.DictReader(stream, delimiter="\t"))
    if len(data) != 10 or len({r["site"] for r in data}) != 10:
        raise ValueError("Expected exact ten-site Batch04 manifest")
    return {r["site"]: r["package"] for r in data}


def source_file(site, package, product, root):
    folder = root / site / "forcing" / "raw" / package
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Missing original source directory: " + str(folder))
    files = list(folder.glob("AMF_" + site + "_FLUXNET_" + product + "_HH_*.csv"))
    if len(files) != 1 or files[0].is_symlink() or not files[0].is_file():
        raise ValueError("Expected exactly one regular " + product + "_HH CSV")
    return files[0]


def collect(path, needed):
    rows = {}
    counts = Counter()
    cols = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "TIMESTAMP_START" not in reader.fieldnames:
            raise ValueError("Missing TIMESTAMP_START in " + str(path))
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Duplicate header in " + str(path))
        cols = set(reader.fieldnames)
        for record in reader:
            counts["scanned"] += 1
            key = record["TIMESTAMP_START"].strip()
            if key not in needed:
                continue
            if key in rows:
                counts["duplicate_timestamps"] += 1
            else:
                rows[key] = {c: record[c] for c in COLUMNS if c in record}
                counts["matched"] += 1
    return rows, counts, cols


def fmt(record, fields):
    if not record:
        return "NO_EXACT_TIMESTAMP"
    return " ".join("{}={}".format(c, record.get(c, "NO_COLUMN")) for c in fields)


def is_equal(a, b):
    if a is None or b is None or a.strip() in ("-9999", "") or b.strip() in ("-9999", ""):
        return False
    try:
        return abs(float(a) - float(b)) <= 1e-8
    except ValueError:
        return False


def run(site, package, root):
    native_path = source_file(site, package, "FLUXMET", root)
    era_path = source_file(site, package, "ERA5", root)
    needed = set(selected_times(ANCHORS[site]))
    original, n_stats, n_header = collect(native_path, needed)
    derived, e_stats, e_header = collect(era_path, needed)
    print("\n" + "=" * 70)
    print("SITE:", site)
    print("NATIVE:", native_path.name, "| scanned", n_stats["scanned"])
    print("PACKAGED ERA5:", era_path.name, "| scanned", e_stats["scanned"])
    print("NATIVE HEADERS:", [v for v in COLUMNS if v in n_header])
    print("PACKAGED ERA HEADERS:", [v for v in COLUMNS if v in e_header])
    print("TARGETS native={} packaged={} expected={} duplicate_native={} duplicate_era={}".format(
        len(original), len(derived), len(needed), n_stats["duplicate_timestamps"],
        e_stats["duplicate_timestamps"]))
    if n_stats["duplicate_timestamps"] or e_stats["duplicate_timestamps"]:
        raise ValueError("Duplicate timestamps in source around requested anomalies")
    matches = Counter()
    for timestamp in sorted(needed):
        a, b = original.get(timestamp), derived.get(timestamp)
        print("TS", timestamp)
        print(" NATIVE:", fmt(a, COLUMNS))
        print(" PACKAGED_ERA:", fmt(b, ("TA_ERA", "PA_ERA", "VPD_ERA",
                                        "TA", "PA", "VPD")))
        if not a or not b:
            print(" FLAG: MISSING_EXACT_LABEL in one of the products")
            continue
        for v, component in (("TA_F", "TA_ERA"), ("PA_F", "PA_ERA"), ("VPD_F", "VPD_ERA")):
            if is_equal(a.get(v), b.get(component)):
                matches[v + "_equals_" + component] += 1
                print(" FLAG: EXACT_EQUAL {} vs {} (NOT independent confirmation)".format(
                    v, component))
        for key in ("TA_ERA", "PA_ERA", "VPD_ERA"):
            x, y = a.get(key), b.get(key)
            if x is not None and y is not None and not is_equal(x, y):
                print(" FLAG: NATIVE_ERA_COLUMN_DISAGREES_WITH_PACKAGED", key, x, y)
    print("EXACT_EQUALS:", dict(matches))
    print("No original CSV, ERA5, forcing, site coordinate or model modifications.")


def self_test():
    times = selected_times(("200412040100",))
    assert len(times) == 5
    assert times[0] == "200412040000"
    assert times[-1] == "200412040200"
    assert is_equal("1.499", "1.499")
    assert not is_equal("-9999", "-9999")
    assert not is_equal("1.499", "85.123")
    print("STAGE04 SELF-TEST PASS (timestamp neighbours and conservative equality)")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sites-root", type=Path, default=ROOT)
    p.add_argument("--sites", nargs="+", choices=sorted(ANCHORS))
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    packages = read_manifest()
    requested = args.sites or list(ANCHORS)
    if len(set(requested)) != len(requested):
        p.error("Duplicate site argument")
    failed = []
    print("STAGE04 READ-ONLY TRACE: FLUXMET vs packaged ERA5 are NOT independent reference")
    for site in requested:
        try:
            run(site, packages[site], args.sites_root)
        except (OSError, ValueError, csv.Error) as err:
            failed.append(site)
            print("FAILED:", site, err, flush=True)
    print("\nSTAGE04 SUMMARY: examined={}/{} failed={}".format(
        len(requested) - len(failed), len(requested), ",".join(failed) or "none"))
    print("SCIENCE HOLD: do not substitute unverified packaged *_ERA variables.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

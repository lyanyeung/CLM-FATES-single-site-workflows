#!/usr/bin/env python3
"""Stage11N: READ-ONLY US-NC2 source clock and existing external grid evidence preflight.

Does NOT retrieve ERA5-Land, set a UTC offset, invent a tower location,
change the approved 11 Stage11L source timestamps, modify Stage07/11h/11l,
or write any report/forcing/DATM/model job. Evidence of availability is NOT
proof of correct temporal alignment, spatial interpretation or humidity QC.
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BATCH = Path(__file__).resolve().parents[2]
SITE_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
EXP = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
SITE = "US-NC2"
DATE = "2025-03"
EDGES = (
    ("MAR18_NEW_START", "202503181800", "202503181830"),
    ("MAR23_OLD_START", "202503230830", "202503230900"),
    ("MAR23_NEW_END", "202503231500", "202503231530"),
    ("MAR25_NEW_END", "202503251000", "202503251030"),
)
CLOCK_KEYS = {
    "UTC_OFFSET", "LOCATION_LAT", "LOCATION_LONG", "LOCATION_ELEV",
    "LOCATION_DATE_START", "LOCATION_DATE_END", "TIMEZONE",
    "UTC_OFFSET_COMMENT", "LOCATION_COMMENT",
}

def require_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing/unsafe regular source: " + str(path))
    return path

def self_test():
    assert len(EDGES) == 4
    assert len({x[0] for x in EDGES}) == 4
    for label, left, right in EDGES:
        d0 = datetime.strptime(left, "%Y%m%d%H%M")
        d1 = datetime.strptime(right, "%Y%m%d%H%M")
        assert d1-d0 == timedelta(minutes=30), label
    print("STAGE11N SELF-TEST PASS: 4 exact native half-hour boundary contracts; no writes")

def get_package():
    with require_file(BATCH / "sites.tsv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    found = [r for r in rows if r.get("site") == SITE]
    if len(rows) != 10 or len(found) != 1:
        raise ValueError("Unexpected Batch03 manifest/site membership")
    if found[0]["package"] != "AMF_US-NC2_FLUXNET_2005-2025_v1.3_r1":
        raise ValueError("Unexpected US-NC2 source package, stop")
    return found[0]["package"]

def source_paths(root, package):
    folder = root / SITE / "forcing" / "raw" / package
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Missing/untrusted raw original package directory")
    def one(pattern):
        files = sorted(folder.glob(pattern))
        if len(files) != 1:
            raise ValueError("Expected unique original " + pattern)
        return require_file(files[0])
    return (
        one("AMF_US-NC2_FLUXNET_BIF_*.csv"),
        one("AMF_US-NC2_FLUXNET_FLUXMET_HH_*.csv"),
        one("AMF_US-NC2_FLUXNET_ERA5_HH_*.csv"),
    )

def audit_bif(path):
    group = defaultdict(dict)
    matches = Counter()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not {"VARIABLE", "DATAVALUE", "GROUP_ID"}.issubset(reader.fieldnames):
            raise ValueError("Unexpected BIF schema")
        for linenum, row in enumerate(reader, 2):
            if row.get("SITE_ID", SITE).strip() not in ("", SITE):
                raise ValueError("BIF SITE_ID changed at " + str(linenum))
            variable = (row.get("VARIABLE") or "").strip().upper()
            if variable in CLOCK_KEYS or variable.startswith("UTC_OFFSET"):
                gid = (row.get("GROUP_ID") or "").strip()
                val = (row.get("DATAVALUE") or "").strip()
                group[gid][variable] = group[gid].get(variable, []) + [val]
                matches[variable] += 1
    print("SOURCE_BIF:", path)
    print("CLOCK/COORDINATE RECORD COUNTS:", dict(matches))
    for gid, records in sorted(group.items()):
        print("BIF GROUP_ID", gid, "CLOCK/LOCATION METADATA:", records)
    offsets = [
        v for records in group.values() for v in records.get("UTC_OFFSET", [])
    ]
    print("PUBLISHED UTC_OFFSET:", offsets or "MISSING")
    print("UTC OFFSET DECISION: NOT APPROVED FROM THIS AUDIT")
    return bool(offsets)

def source_context(path):
    wanted = {
        key for _, a, b in EDGES for key in (a, b)
    }
    records = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        need = {"TIMESTAMP_START", "TIMESTAMP_END", "TA_F", "VPD_F", "VPD_F_QC"}
        if not reader.fieldnames or not need.issubset(reader.fieldnames):
            raise ValueError("FLUXMET missing Stage11M boundary fields")
        for row in reader:
            stamp = (row.get("TIMESTAMP_START") or "").strip()
            if stamp in wanted:
                if stamp in records:
                    raise ValueError("Duplicate native boundary stamp " + stamp)
                records[stamp] = {k: row.get(k, "") for k in need}
    if set(records) != wanted:
        raise ValueError("Missing source-native Stage11M boundary timestamps: " +
                         repr(sorted(wanted - set(records))))
    print("BOUNDARY EXACT NATIVE SOURCE RECORDS: {}/{}".format(
        len(records), len(wanted)))
    for label, left, right in EDGES:
        a, b = records[left], records[right]
        if a["TIMESTAMP_END"] != right:
            raise ValueError("Boundary not adjacent in original source: " + label)
        print("BOUNDARY", label, left, "->", right,
              "SOURCE_LEFT TA/VPD/QC:", a["TA_F"], a["VPD_F"], a["VPD_F_QC"],
              "SOURCE_RIGHT TA/VPD/QC:", b["TA_F"], b["VPD_F"], b["VPD_F_QC"])

def grid_inventory(root):
    specific = root / "US-NC2" / "2025"
    print("PREVIOUS STAGE09 ERA5-LAND EVIDENCE ROOT:", root)
    if not specific.exists():
        print("US-NC2 2025 GRID STATUS: NO STANDARD STAGE09 BUNDLE FOUND")
        print("NEED: independently obtained ERA5-Land 2025 T2m/Td2m/surface pressure,")
        print("      paired valid coordinates and source-clock review BEFORE boundary comparison")
        return False
    if specific.is_symlink() or not specific.is_dir():
        raise ValueError("External evidence path is unsafe/non-directory")
    files = sorted(x for x in specific.iterdir() if x.is_file() and not x.is_symlink())
    print("US-NC2 2025 EXTERNAL FILE INVENTORY:",
          [(p.name, p.stat().st_size) for p in files])
    markers = [p for p in files if p.suffix.lower() in (".nc", ".zip")]
    print("US-NC2 2025 FILE AVAILABILITY:",
          "CANDIDATE_PRESENT_UNVALIDATED" if markers else "NO_NETCDF_OR_ZIP")
    print("File presence does not establish independent gridded meteorology, UTC")
    print("alignment, dewpoint physical validity, or source SHA verification")
    return bool(markers)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites-root", type=Path, default=SITE_ROOT)
    ap.add_argument("--external-root", type=Path,
                    default=EXP / "external_evidence/era5land_timeseries")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    self_test()
    if args.self_test:
        return
    package = get_package()
    bif, native, era = source_paths(args.sites_root, package)
    print("STAGE11N: US-NC2 2025 READ-ONLY NATIVE CLOCK/GRID AVAILABILITY")
    print("Original source:", native)
    print("Original paired ERA:", era)
    clock = audit_bif(bif)
    source_context(native)
    grid = grid_inventory(args.external_root)
    print("STAGE11N SUMMARY: 4/4 native boundaries checked;",
          "published_offset_present={}; grid_2025_candidate_present={};".format(clock, grid),
          "offset_authorized=0; boundary_repair_authorized=0;",
          "Postv5_approved=0; DATM_ready=0; spinup=0")
    print("READ ONLY. No source, stage11l ledger, shadow forcing, reports or jobs modified.")

if __name__ == "__main__":
    main()

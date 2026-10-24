#!/usr/bin/env python3
"""Stage02B: read-only provenance audit of US-Seg conflicting release BIF coordinates.

Never change original CSVs, choose a surface coordinate or approve model input.
External current and team coordinates are comparisons, not replacements.
"""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

DEFAULT_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
HERE = Path(__file__).resolve().parents[2]
SITE = "US-Seg"
EXTERNAL = (
    ("RESEARCH_TEAM", 34.3623, -106.7019,
     "https://www.litvaklab.org/grassland---us-seg.html"),
    ("CURRENT_AMERIFLUX_PAGE", 34.3603, -106.7003,
     "https://ameriflux.lbl.gov/sites/siteinfo/US-Seg"),
)

def distance_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return 2 * 6371008.8 * math.asin(min(1.0, math.sqrt(a)))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sites-root", type=Path, default=DEFAULT_ROOT)
    args = p.parse_args()
    with (HERE / "sites.tsv").open(encoding="utf-8-sig", newline="") as handle:
        records = list(csv.DictReader(handle, delimiter="\t"))
    matching = [x for x in records if x["site"] == SITE]
    if len(records) != 10 or len(matching) != 1:
        raise RuntimeError("Stage02B requires exact 10-site Batch04 manifest")
    raw = args.sites_root / SITE / "forcing" / "raw" / matching[0]["package"]
    if not raw.is_dir() or raw.is_symlink():
        raise RuntimeError("Missing or symlinked raw package directory: " + str(raw))
    bifs = list(raw.glob("AMF_US-Seg_FLUXNET_BIF_*.csv"))
    if len(bifs) != 1 or bifs[0].is_symlink() or not bifs[0].is_file():
        raise RuntimeError("Exactly one regular original US-Seg BIF required")
    bif = bifs[0]
    groups = defaultdict(list)
    lat, lon, labels = set(), set(), set()
    with bif.open(encoding="utf-8-sig", newline="") as handle:
        for line, record in enumerate(csv.DictReader(handle), 2):
            site = (record.get("SITE_ID") or SITE).strip()
            if site != SITE:
                raise RuntimeError("Unexpected SITE_ID on line {}: {}".format(line, site))
            group = (record.get("GROUP_ID") or "").strip() or "(MISSING_GROUP_ID)"
            key = (record.get("VARIABLE") or "").strip().upper()
            value = (record.get("DATAVALUE") or "").strip()
            groups[group].append((line, key, value, record))
            if key == "LOCATION_LAT" and value:
                lat.add(value)
            elif key == "LOCATION_LONG" and value:
                lon.add(value)
            elif key in ("IGBP", "IGBP_CLASS", "IGBP_VEGTYPE") and value:
                labels.add(value)
    if not lat or not lon:
        raise RuntimeError("Missing original coordinate values: read full BIF")
    print("READ-ONLY STAGE02B | US-Seg | source:", bif)
    print("ALL ORIGINAL LATITUDES:", sorted(lat))
    print("ALL ORIGINAL LONGITUDES:", sorted(lon))
    print("ORIGINAL IGBP LABELS:", sorted(labels))
    print("SOURCE RECORDS BY BIF GROUP_ID:")
    involved = [
        (group, rows) for group, rows in groups.items()
        if any(key in ("LOCATION_LAT", "LOCATION_LONG") for _, key, _, _ in rows)
    ]
    for group, rows in sorted(involved):
        print("\nGROUP_ID:", group)
        glat = {v for _, k, v, _ in rows if k == "LOCATION_LAT" and v}
        glon = {v for _, k, v, _ in rows if k == "LOCATION_LONG" and v}
        print("GROUP LAT:", sorted(glat), "GROUP LON:", sorted(glon))
        for line, key, value, record in rows:
            if (key.startswith("LOCATION") or key in
                ("IGBP", "IGBP_CLASS", "IGBP_VEGTYPE")
                or key.endswith("_DATE") or key.startswith("SITE_")):
                print("  BIF line {}: {}".format(
                    line, json.dumps({k: v for k, v in record.items() if k and v},
                                     ensure_ascii=True, sort_keys=True)))
        if len(glat) != 1 or len(glon) != 1:
            print("  GROUP PAIRING: AMBIGUOUS / INCOMPLETE")
    print("\nINDEPENDENT PUBLIC REFERENCE COMPARISONS (NO SELECTION):")
    for label, rlat, rlon, url in EXTERNAL:
        print(label, rlat, rlon, url)
        for latitude in sorted(lat):
            for longitude in sorted(lon):
                try:
                    metres = distance_m(float(latitude), float(longitude), rlat, rlon)
                    print("  Cartesian BIF candidate ({}, {}) distance {:.1f} m".format(
                        latitude, longitude, metres))
                except ValueError:
                    print("  INVALID BIF numeric candidate:", latitude, longitude)
    print("\nIMPORTANT: Cartesian BIF candidates are NOT proven paired;")
    print("compare the original GROUP_ID records and source dates.")
    print("NO automatic coordinate decision. Original sources unchanged.")
    print("US-Seg remains in STAGE02 REVIEW; 9/10 Batch04 preflight PASS.")

if __name__ == "__main__":
    main()

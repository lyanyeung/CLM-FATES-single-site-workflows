#!/usr/bin/env python3
"""Read-only audit of conflicting BIF LOCATION_* metadata for Batch03 sites.

No coordinate is selected. Never modifies a BIF, surface, forcing or case.
"""
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
DEFAULT_SITES_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
OFFICIAL = {
    "US-Mpj": (34.4382, -106.2385, "WSA"),
    "US-MtB": (32.4160, -110.7256, "ENF"),
}
SOURCE_URL = "https://ameriflux.lbl.gov/sites/site-search/"


def haversine_m(lat1, lon1, lat2, lon2):
    radius = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    v = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(v)))


def read_manifest():
    with (HERE / "sites.tsv").open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream, delimiter="\t"))
    return {r["site"]: r["package"] for r in manifest}


def diagnostic(site, package, sites_root):
    raw = sites_root / site / "forcing" / "raw" / package
    path = raw / ("AMF_" + site + "_FLUXNET_BIF_" + package.split("_FLUXNET_")[1] + ".csv")
    # The exact BIF suffix is release-dependent; discover within the exact package directory.
    matches = sorted(raw.glob("AMF_" + site + "_FLUXNET_BIF_*.csv"))
    if len(matches) != 1:
        raise RuntimeError("{}: expected one BIF CSV, found {}".format(site, len(matches)))
    path = matches[0]
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("BIF is not a regular file: " + str(path))
    print("\n" + "=" * 75)
    print("SITE:", site, "| BIF:", path)
    records = defaultdict(list)
    lat_vals, lon_vals, labels = set(), set(), set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row_number, row in enumerate(reader, start=2):
            if row.get("SITE_ID", site).strip() != site:
                raise RuntimeError("Wrong SITE_ID on line {}".format(row_number))
            key = (row.get("VARIABLE") or "").strip().upper()
            value = (row.get("DATAVALUE") or "").strip()
            group = (row.get("GROUP_ID") or "").strip() or "(missing)"
            records[group].append((row_number, key, value))
            if key == "LOCATION_LAT":
                lat_vals.add(value)
            if key == "LOCATION_LONG":
                lon_vals.add(value)
            if key in ("IGBP", "IGBP_CLASS", "IGBP_VEGTYPE"):
                labels.add(value)
    print("IGBP labels in BIF:", sorted(labels))
    print("All distinct LOCATION_LAT:", sorted(lat_vals))
    print("All distinct LOCATION_LONG:", sorted(lon_vals))
    coordinate_groups = []
    for group, rows in records.items():
        if any(k in ("LOCATION_LAT", "LOCATION_LONG") for _, k, _ in rows):
            coordinate_groups.append(group)
            print("\nGROUP_ID:", group)
            for line, key, value in rows:
                if (key.startswith("LOCATION") or key.startswith("SITE_")
                        or key.startswith("TOWER") or key.endswith("_DATE")
                        or key in ("IGBP", "IGBP_CLASS", "IGBP_VEGTYPE")):
                    print("  line {:>5}: {:<34} {}".format(line, key, value[:250]))
            print("  coordinate-related entries in group:", sum(
                k.startswith("LOCATION") for _, k, _ in rows))
    official_lat, official_lon, official_igbp = OFFICIAL[site]
    print("\nOFFICIAL CURRENT SITE LIST: LAT={} LON={} IGBP={}".format(
        official_lat, official_lon, official_igbp))
    print("SOURCE:", SOURCE_URL)
    print("Comparison of independent BIF coordinate values to CURRENT official point")
    for latitude in sorted(lat_vals):
        for longitude in sorted(lon_vals):
            try:
                dist = haversine_m(float(latitude), float(longitude),
                                  official_lat, official_lon)
                print("  BIF ({}, {}) -> official: {:.1f} m".format(
                    latitude, longitude, dist))
            except ValueError:
                print("  Non-numeric BIF coordinate:", latitude, longitude)
    print("NOTE: Cartesian comparisons above do not establish which")
    print("      latitude and longitude were recorded as a paired site location.")
    print("REVIEW REQUIRED: inspect coordinate GROUP_ID provenance, dates,")
    print("  tower history and current-versus-release location before selecting.")
    print("NO coordinates were changed or selected.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites-root", type=Path, default=DEFAULT_SITES_ROOT)
    args = parser.parse_args()
    manifest = read_manifest()
    for site in OFFICIAL:
        if site not in manifest:
            parser.error("Site not in batch manifest: " + site)
        diagnostic(site, manifest[site], args.sites_root.expanduser())
    print("\nDIAGNOSTIC COMPLETE: US-Mpj and US-MtB | READ ONLY")
    print("STAGE02 remains 8/10 until discrepancies are explicitly resolved.")


if __name__ == "__main__":
    main()

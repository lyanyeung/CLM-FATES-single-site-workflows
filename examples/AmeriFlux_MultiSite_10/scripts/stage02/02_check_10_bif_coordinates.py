#!/usr/bin/env python3
"""Stage 02: BIF coordinate preflight for AmeriFlux 10-site point surfaces.
Read-only: checks exact metadata and prints suggested CTSM coordinates.
No changes to source data, case directories, surfaces, DATM or Slurm.
"""
import argparse
import csv
import math
import os
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("FLUXNET_SITES_ROOT",
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites-root", type=Path, default=ROOT)
    args = parser.parse_args()
    with (HERE / "sites.tsv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 10:
        raise SystemExit("ERROR: expected exactly 10 manifest entries")
    errors = []
    for r in rows:
        site, pkg = r["site"], r["package"]
        raw = args.sites_root / site / "forcing" / "raw" / pkg
        bifs = [p for p in raw.glob("*.csv") if "_BIF_" in p.name.upper()]
        print(f"\n========== {site} ==========")
        if len(bifs) != 1:
            errors.append(f"{site}: expected one BIF, found {len(bifs)}")
            continue
        vals = {"LOCATION_LAT": set(), "LOCATION_LONG": set()}
        land = set()
        with bifs[0].open(newline="", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or not {"VARIABLE","DATAVALUE"}.issubset(reader.fieldnames):
                errors.append(f"{site}: invalid BIF schema")
                continue
            for row in reader:
                k = (row.get("VARIABLE") or "").strip().upper()
                v = (row.get("DATAVALUE") or "").strip()
                if k in vals and v:
                    try:
                        n = float(v)
                        if math.isfinite(n): vals[k].add(n)
                    except ValueError:
                        pass
                if k in ("IGBP","IGBP_CLASS","IGBP_VEGTYPE") and v:
                    land.add(v)
        if any(len(x) != 1 for x in vals.values()):
            errors.append(f"{site}: missing/ambiguous BIF coordinates: {vals}")
            continue
        lat = next(iter(vals["LOCATION_LAT"]))
        lon = next(iter(vals["LOCATION_LONG"]))
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            errors.append(f"{site}: invalid coordinates: {lat},{lon}")
            continue
        print(f"COORDINATES: LAT={lat} LON={lon}")
        print(f"IGBP LABELS: {','.join(sorted(land)) or 'NOT FOUND'}")
        print(f"BIF FILE: {bifs[0]}")
        print("STATUS: PRECHECK PASS — land-cover/PFT representativeness NOT verified")
    print(f"\nSUMMARY: {10-len(errors)}/10 BIF coordinate checks PASS")
    if errors:
        for error in errors: print("ERROR:",error)
        raise SystemExit(1)
    print("NEXT: scientific evaluation of surface PFT and forcing coverage; no surfaces written.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Stage 04a: read-only audit of ten generated CTSM point surfaces.

CLM natural PFT fractions are NOT equivalent to a scientifically verified
FATES configuration or to a flux-tower footprint classification.
"""
import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from netCDF4 import Dataset

BATCH = Path(__file__).resolve().parents[2]
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DEFAULT_REPORT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
EXPECTED_IGBP = {
    "BR-Ma2": "EBF", "CA-Ca3": "ENF", "CA-Cbo": "DBF",
    "CA-LP1": "ENF", "CA-Man": "ENF", "CA-TP1": "ENF",
    "CA-TP3": "ENF", "CA-TP4": "ENF", "US-Aud": "GRA",
    "US-Bar": "DBF",
}
LAND_KEYS = ("PCT_NATVEG", "PCT_CROP", "PCT_LAKE",
             "PCT_WETLAND", "PCT_GLACIER", "PCT_URBAN")
NAT_NAMES = (
    "bare_ground", "needleleaf_evergreen_temperate_tree",
    "needleleaf_evergreen_boreal_tree", "needleleaf_deciduous_boreal_tree",
    "broadleaf_evergreen_tropical_tree",
    "broadleaf_evergreen_temperate_tree",
    "broadleaf_deciduous_tropical_tree",
    "broadleaf_deciduous_temperate_tree",
    "broadleaf_deciduous_boreal_tree",
    "broadleaf_evergreen_temperate_shrub",
    "broadleaf_deciduous_temperate_shrub",
    "broadleaf_deciduous_boreal_shrub",
    "c3_arctic_grass", "c3_non_arctic_grass", "c4_grass",
    "extra_index_needs_review",
)


def read_values(nc, name):
    if name not in nc.variables:
        return None
    a = np.ma.filled(nc.variables[name][:], np.nan)
    return np.asarray(a, dtype=np.float64).ravel()


def number(a, field):
    if a is None or a.size != 1 or not math.isfinite(float(a[0])):
        raise ValueError(field + ": expected a single finite percentage")
    return float(a[0])


def one_site(site, root):
    issues, reviews = [], []
    folder = root / site / "subset_data"
    matches = sorted(folder.glob("surfdata*.nc"))
    record = dict(site=site, igbp=EXPECTED_IGBP[site],
                  surface_files=len(matches), surface=str(matches[0]) if len(matches) == 1 else "")
    pfts = []
    if len(matches) != 1:
        issues.append("expected exactly one surfdata*.nc, found " + str(len(matches)))
    if not (folder / "user_mods").is_dir():
        issues.append("missing user_mods")
    if not (root / site / (site + "_data.cfg")).is_file():
        issues.append("missing CTSM site cfg")
    if len(matches) == 1:
        try:
            with Dataset(matches[0]) as nc:
                units = {}
                for key in LAND_KEYS:
                    a = read_values(nc, key)
                    if a is None:
                        reviews.append(key + " absent (check surface schema)")
                        continue
                    if key == "PCT_URBAN":
                        val = float(np.nansum(a))
                        if not np.all(np.isfinite(a)):
                            issues.append("PCT_URBAN has NaN/Inf")
                    else:
                        val = number(a, key)
                    if not -0.01 <= val <= 100.01:
                        issues.append(key + " outside 0-100")
                    record[key] = round(val, 5)
                    units[key] = val
                if all(k in units for k in LAND_KEYS):
                    total = sum(units.values())
                    record["landunit_total_pct"] = round(total, 5)
                    if abs(total - 100) > 0.5:
                        issues.append("landunit fractions sum to %.2f not 100" % total)
                nat = read_values(nc, "PCT_NAT_PFT")
                if nat is None:
                    issues.append("PCT_NAT_PFT missing")
                elif nat.size not in (15, 16):
                    issues.append("unexpected PCT_NAT_PFT length " + str(nat.size))
                elif not np.all(np.isfinite(nat)) or np.min(nat) < -0.01 or np.max(nat) > 100.01:
                    issues.append("PCT_NAT_PFT has NaN/out-of-range percentages")
                else:
                    record["pft_count"] = int(nat.size)
                    total = float(nat.sum())
                    record["natural_pft_total_pct"] = round(total, 5)
                    if abs(total - 100) > 0.5:
                        issues.append("PCT_NAT_PFT sum %.2f not 100" % total)
                    forest = float(nat[1:9].sum())
                    shrubs = float(nat[9:12].sum())
                    grass = float(nat[12:15].sum())
                    record.update(forest_natural_pct=round(forest, 3),
                                  shrub_natural_pct=round(shrubs, 3),
                                  grass_natural_pct=round(grass, 3),
                                  bare_natural_pct=round(float(nat[0]), 3))
                    for i, pct in enumerate(nat):
                        pfts.append(dict(site=site, index=i,
                                         clm_natural_pft=NAT_NAMES[i],
                                         pct_of_natural=float(pct)))
                    if nat.size == 16:
                        reviews.append("16 PCT_NAT_PFT values; confirm final slot meaning")
                    if EXPECTED_IGBP[site] == "GRA" and grass < 50:
                        reviews.append("GRA BIF but gridded natural grass fraction <50%")
                    if EXPECTED_IGBP[site] in {"ENF", "DBF", "EBF"} and forest < 50:
                        reviews.append("forest BIF but gridded natural tree fraction <50%")
                if record.get("PCT_CROP", 0) > 20:
                    reviews.append("gridded cropland >20% near EC tower")
                if record.get("PCT_NATVEG", 100) < 50:
                    reviews.append("gridded natural vegetation <50%")
        except (OSError, RuntimeError, ValueError, IndexError) as exc:
            issues.append("NetCDF read/structure error: " + str(exc))
    reviews.append("CTSM grid surface is not a verified tower-footprint/FATES PFT representation")
    record["result"] = "STRUCTURAL_FAIL" if issues else "STRUCTURE_OK_SCIENCE_REVIEW"
    record["issues"] = " | ".join(issues)
    record["review"] = " | ".join(reviews)
    return record, pfts


def write_csv(path, records, cols):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--report-root", type=Path, default=DEFAULT_REPORT)
    args = p.parse_args()
    summary, pfts = [], []
    for site in EXPECTED_IGBP:
        item, details = one_site(site, args.root)
        summary.append(item)
        pfts.extend(details)
        print("%-7s %-26s NAT=%-7s CROP=%-7s TREE=%-7s GRASS=%-7s %s" % (
            site, item["result"], item.get("PCT_NATVEG", "?"),
            item.get("PCT_CROP", "?"), item.get("forest_natural_pct", "?"),
            item.get("grass_natural_pct", "?"), item["issues"]), flush=True)
        if item["review"]:
            print("  REVIEW:", item["review"], flush=True)
    run_dir = args.report_root / ("stage04a_surface_" +
                datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    run_dir.mkdir(parents=True, exist_ok=False)
    fields = list(dict.fromkeys(k for row in summary for k in row))
    write_csv(run_dir / "surface_summary.csv", summary, fields)
    write_csv(run_dir / "natural_pft_detail.csv", pfts,
              ["site", "index", "clm_natural_pft", "pct_of_natural"])
    with (run_dir / "surface_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print("\nSUMMARY: %d/10 structural passes; %d structural failures" %
          (sum(r["result"] != "STRUCTURAL_FAIL" for r in summary),
           sum(r["result"] == "STRUCTURAL_FAIL" for r in summary)))
    print("REPORT DIR:", run_dir)
    print("READ-ONLY inputs: no surface was changed. Scientific validation still required.")
    return 2 if any(r["result"] == "STRUCTURAL_FAIL" for r in summary) else 0


if __name__ == "__main__":
    raise SystemExit(main())

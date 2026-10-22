#!/usr/bin/env python3
"""Stage 04a: audit ten isolated Batch 03 point surfaces, writing only reports.

CLM natural PFT fractions are NOT equivalent to a scientifically verified
FATES configuration or to a flux-tower footprint classification.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from uuid import uuid4

try:
    from netCDF4 import Dataset
    BACKEND = "netCDF4"
except ImportError:
    from scipy.io import netcdf_file
    BACKEND = "scipy (classic NetCDF only; install/use netCDF4 for NetCDF4/HDF5)"
    def Dataset(path):
        return netcdf_file(str(path), mode="r", mmap=False)

BATCH = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("FLUXNET_SITES_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
EXPECTED_IGBP = {
    "US-Kon": "GRA", "US-Me2": "ENF", "US-Me6": "ENF",
    "US-MMS": "DBF", "US-MOz": "DBF", "US-Mpj": "WSA",
    "US-MtB": "ENF", "US-NC2": "ENF", "US-NR1": "ENF",
    "US-NR3": "GRA",
}
# WSA for US-Mpj denotes the current AmeriFlux site listing; the BIF
# itself includes ENF/OSH/WSA. No single vegetation class is assumed final.

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
    var = nc.variables[name]
    a = np.ma.asarray(var[:], dtype=np.float64).filled(np.nan)
    for key in ("_FillValue", "missing_value"):
        if hasattr(var, key):
            for value in np.asarray(getattr(var, key)).ravel():
                a = np.where(a == value, np.nan, a)
    if BACKEND.startswith("scipy"):
        a = a * float(getattr(var, "scale_factor", 1)) + float(getattr(var, "add_offset", 0))
    return np.asarray(a, dtype=np.float64).ravel()


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def check_receipt(folder, site, package):
    path = folder / "batch03_surface_receipt.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing/invalid Stage03 completion receipt")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    request = receipt["request"]
    if (request["site"] != site or request["package"] != package
            or request["batch"] != "AmeriFlux_MultiSite_10_Batch03"
            or request["surf_year"] != 2000 or request["dompft"] is not False):
        raise ValueError("Stage03 receipt site/package/year/settings mismatch")
    expected = receipt["files"]
    actual = {}
    for entry in sorted(folder.rglob("*")):
        name = str(entry.relative_to(folder))
        if name == path.name:
            continue
        if entry.is_symlink():
            actual[name] = {"symlink": os.readlink(entry)}
        elif entry.is_file():
            actual[name] = {"sha256": sha256(entry), "bytes": entry.stat().st_size}
    if expected != actual:
        raise ValueError("Generated file inventory/checksums differ from Stage03 receipt")
    cfg = folder / (site + "_data.cfg")
    if sha256(cfg) != request["config_sha256"]:
        raise ValueError("Config differs from Stage03 request")
    return receipt


def number(a, field):
    if a is None or a.size != 1 or not math.isfinite(float(a[0])):
        raise ValueError(field + ": expected a single finite percentage")
    return float(a[0])


def one_site(site, package, root):
    issues, reviews = [], []
    folder = root / site / "subset_data_batch03_surf2000"
    matches = sorted(folder.glob("surfdata*.nc"))
    record = dict(site=site, igbp=EXPECTED_IGBP[site],
                  surface_files=len(matches), surface=str(matches[0]) if len(matches) == 1 else "")
    pfts = []
    if folder.is_symlink():
        issues.append("batch surface directory is a symlink")
    if len(matches) != 1:
        issues.append("expected exactly one surfdata*.nc, found " + str(len(matches)))
    if not (folder / "user_mods").is_dir():
        issues.append("missing user_mods")
    if not (folder / (site + "_data.cfg")).is_file():
        issues.append("missing CTSM site cfg")
    try:
        receipt = check_receipt(folder, site, package)
        record["receipt_verified"] = True
        record["metadata_source"] = receipt["metadata_source"]
        record["coordinate_source"] = receipt.get("coordinate_source", "")
        record["bif_igbp_labels"] = "/".join(receipt.get("igbp_labels", []))
        if site == "US-Mpj":
            labels = set(receipt.get("igbp_labels", []))
            if labels != {"ENF", "OSH", "WSA"}:
                issues.append("US-Mpj IGBP provenance changed: inspect BIF conflict")
            reviews.append("US-Mpj BIF has ENF/OSH/WSA; current AmeriFlux WSA is not an approved FATES mapping")
        if site == "US-Me2":
            reviews.append("US-Me2 year-2000 surface predates fire and logging; review time-varying cover and 2020 disturbance")
        if site in {"US-Kon", "US-NR3"}:
            reviews.append("GRA tower: assess grassland FATES support and comparison against gridded PFTs")
        record["native_met_resolution"] = "/".join(m["resolution"] for m in receipt["native_meteorology"])
        record["requested_lat"] = receipt["request"]["latitude"]
        record["requested_lon"] = receipt["request"]["longitude"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        record["receipt_verified"] = False
        issues.append("Receipt verification: " + str(exc))
    if len(matches) == 1:
        try:
            with Dataset(matches[0]) as nc:
                units = {}
                record["surface_sha256"] = sha256(matches[0])
                for key in ("LATIXY", "LONGXY"):
                    coord = read_values(nc, key)
                    if coord is not None:
                        value = number(coord, key)
                        record[key] = value
                        if (key == "LATIXY" and not -90 <= value <= 90) or (key == "LONGXY" and not -180 <= value <= 360):
                            issues.append(key + " outside valid geographic range")
                        requested = record.get("requested_lat" if key == "LATIXY" else "requested_lon")
                        if requested is not None:
                            difference = abs(value - requested) if key == "LATIXY" else abs((value - requested + 180) % 360 - 180)
                            if difference > 0.05:
                                reviews.append(key + " differs from requested point by >0.05 degrees; inspect point/grid metadata")
                    else:
                        reviews.append(key + " absent; inspect coordinate schema")
                for key in LAND_KEYS:
                    a = read_values(nc, key)
                    if a is None:
                        issues.append(key + " absent (incomplete landunit audit)")
                        continue
                    if key == "PCT_URBAN":
                        val = float(np.nansum(a))
                        if not np.all(np.isfinite(a)):
                            raise ValueError("PCT_URBAN has NaN/Inf")
                        if a.size not in (1, 3) or np.any(a < -0.01) or np.any(a > 100.01):
                            issues.append("PCT_URBAN shape or component percentages invalid for one point")
                        urban = nc.variables[key]
                        if any(size != 1 for dim, size in zip(urban.dimensions, urban.shape) if dim != "numurbl"):
                            issues.append("PCT_URBAN has more than one spatial point")
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
                    var = nc.variables["PCT_NAT_PFT"]
                    if ("natpft" not in var.dimensions
                            or any(size != 1 for dim, size in zip(var.dimensions, var.shape) if dim != "natpft")):
                        raise ValueError("PCT_NAT_PFT must contain one natpft vector at one spatial point")
                    index = read_values(nc, "natpft")
                    if index is not None and not np.array_equal(index, np.arange(nat.size)):
                        raise ValueError("Nonstandard natpft coordinate labels; index mapping needs review")
                    record["pft_count"] = int(nat.size)
                    total = float(nat.sum())
                    record["natural_pft_total_pct"] = round(total, 5)
                    if record.get("PCT_NATVEG", 0) > 0.01 and abs(total - 100) > 0.5:
                        issues.append("PCT_NAT_PFT sum %.2f not 100" % total)
                    forest = float(nat[1:9].sum())
                    shrubs = float(nat[9:12].sum())
                    grass = float(nat[12:15].sum())
                    record.update(forest_natural_pct=round(forest, 3),
                                  shrub_natural_pct=round(shrubs, 3),
                                  grass_natural_pct=round(grass, 3),
                                  bare_natural_pct=round(float(nat[0]), 3))
                    record["enf_natural_pct"] = round(float(nat[1:3].sum()), 3)
                    record["dbf_natural_pct"] = round(float(nat[6:9].sum()), 3)
                    if "PCT_NATVEG" in record:
                        for group, value in (("tree", forest), ("shrub", shrubs), ("grass", grass), ("bare", float(nat[0]))):
                            record[group + "_grid_pct"] = round(record["PCT_NATVEG"] * value / 100, 5)
                    for i, pct in enumerate(nat):
                        pfts.append(dict(site=site, index=i,
                                         clm_natural_pft=NAT_NAMES[i],
                                         pct_of_natural=float(pct),
                                         pct_of_grid=(record["PCT_NATVEG"] * float(pct) / 100
                                                      if "PCT_NATVEG" in record else None)))
                    if nat.size == 16:
                        reviews.append("16 PCT_NAT_PFT values; confirm final slot meaning")
                        record["extra_index15_natural_pct"] = float(nat[15])
                    if EXPECTED_IGBP[site] == "GRA" and grass < 50:
                        reviews.append("GRA BIF but gridded natural grass fraction <50%")
                    if EXPECTED_IGBP[site] in {"ENF", "DBF", "EBF"} and forest < 50:
                        reviews.append("forest BIF but gridded natural tree fraction <50%")
                    if EXPECTED_IGBP[site] == "ENF" and record["enf_natural_pct"] < 50:
                        reviews.append("ENF tower label but CLM natural evergreen needleleaf fraction <50%; exploratory mismatch screen")
                    if EXPECTED_IGBP[site] == "DBF" and record["dbf_natural_pct"] < 50:
                        reviews.append("DBF tower label but CLM natural deciduous broadleaf fraction <50%; exploratory mismatch screen")
                    if EXPECTED_IGBP[site] == "OSH":
                        reviews.append("OSH tower: inspect shrub/grass/tree mixture and tundra representation; no majority-shrub requirement or automatic FATES mapping")
                    if EXPECTED_IGBP[site] == "WSA":
                        reviews.append("WSA tower: inspect tree/shrub/grass mixture; current-site IGBP is not validated FATES PFT composition")
                if record.get("PCT_CROP", 0) > 20:
                    reviews.append("gridded cropland >20% near EC tower")
                if record.get("PCT_NATVEG", 100) < 50:
                    reviews.append("gridded natural vegetation <50%")
                if record.get("PCT_LAKE", 0) + record.get("PCT_WETLAND", 0) > 0.01:
                    reviews.append("nonzero gridded lake/wetland fraction; inspect tower footprint and landunit representation")
        except (OSError, RuntimeError, ValueError, IndexError, TypeError, KeyError) as exc:
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
    p.add_argument("--report-root", type=Path)
    p.add_argument("--stdout-only", action="store_true", help="Print results without writing any reports")
    args = p.parse_args()
    args.root = args.root.expanduser()
    with (BATCH / "sites.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != 10 or {r["site"] for r in rows} != set(EXPECTED_IGBP):
        p.error("Expected exactly the ten Batch03 manifest sites")
    packages = {r["site"]: r["package"] for r in rows}
    print("PYTHON:", sys.executable, "| NetCDF backend:", BACKEND, flush=True)
    summary, pfts = [], []
    for site in EXPECTED_IGBP:
        item, details = one_site(site, packages[site], args.root)
        summary.append(item)
        pfts.extend(details)
        print("%-7s %-26s NAT=%-7s CROP=%-7s TREE_nat=%-7s SHRUB_nat=%-7s GRASS_nat=%-7s %s" % (
            site, item["result"], item.get("PCT_NATVEG", "?"),
            item.get("PCT_CROP", "?"), item.get("forest_natural_pct", "?"),
            item.get("shrub_natural_pct", "?"),
            item.get("grass_natural_pct", "?"), item["issues"]), flush=True)
        if item["review"]:
            print("  REVIEW:", item["review"], flush=True)
    if not args.stdout_only:
        report_root = args.report_root.expanduser() if args.report_root else (
            args.root.parent.parent / "experiments/AmeriFlux_MultiSite_10_Batch03/reports")
        run_dir = report_root / ("stage04a_surface_" +
                    datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
        run_dir.mkdir(parents=True, exist_ok=False)
        fields = list(dict.fromkeys(k for row in summary for k in row))
        write_csv(run_dir / "surface_summary.csv", summary, fields)
        write_csv(run_dir / "natural_pft_detail.csv", pfts,
                  ["site", "index", "clm_natural_pft", "pct_of_natural", "pct_of_grid"])
        with (run_dir / "surface_summary.json").open("w") as f:
            json.dump(summary, f, indent=2, allow_nan=False)
        print("REPORT DIR:", run_dir)
    print("\nSTAGE04A SUMMARY: %d/10 structural passes; %d structural failures" %
          (sum(r["result"] != "STRUCTURAL_FAIL" for r in summary),
           sum(r["result"] == "STRUCTURAL_FAIL" for r in summary)))
    print("READ-ONLY inputs: no surface was changed. Scientific validation still required.")
    return 2 if any(r["result"] == "STRUCTURAL_FAIL" for r in summary) else 0


if __name__ == "__main__":
    raise SystemExit(main())

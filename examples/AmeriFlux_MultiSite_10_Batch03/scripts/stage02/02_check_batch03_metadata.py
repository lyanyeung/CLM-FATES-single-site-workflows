#!/usr/bin/env python3
"""Read-only Batch 03 coordinates, vegetation labels and native time-step preflight.

Use release BIF where present. Only the US-Me2 FULLSET site may use explicitly
cited metadata_fallbacks.tsv entries. No source, surface, forcing or case writes.
This is not full time-series QC or a FATES PFT/measurement-height selection.
"""
import argparse
import csv
from datetime import datetime
import json
import math
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path(os.environ.get(
    "FLUXNET_SITES_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
IGBP_CODES = {"ENF", "EBF", "DNF", "DBF", "MF", "CSH", "OSH", "WSA",
              "SAV", "GRA", "WET", "CRO", "URB", "CVM", "SNO", "BSV", "WAT"}


def table(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def coordinates(lat, lon):
    lat, lon = float(lat), float(lon)
    if not (math.isfinite(lat) and math.isfinite(lon)
            and -90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Invalid latitude/longitude: {}, {}".format(lat, lon))
    return lat, lon


def vegetation_codes(labels):
    result = set()
    for label in labels:
        match = re.match(r"^([A-Z]{2,3})(?:\b|_)", label.strip().upper())
        if match and match.group(1) in IGBP_CODES:
            result.add(match.group(1))
    return sorted(result)


def bif_metadata(path, site, selected=None):
    vals = {"LOCATION_LAT": set(), "LOCATION_LONG": set()}
    labels, heights = set(), []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"VARIABLE", "DATAVALUE"}.issubset(reader.fieldnames):
            raise ValueError("BIF must have VARIABLE and DATAVALUE columns: " + str(path))
        for row in reader:
            row_site = (row.get("SITE_ID") or "").strip()
            if row_site and row_site != site:
                raise ValueError("Wrong SITE_ID in BIF: " + row_site)
            key = (row.get("VARIABLE") or "").strip().upper()
            value = (row.get("DATAVALUE") or "").strip()
            if key in vals and value:
                number = float(value)
                if math.isfinite(number) and number != -9999:
                    vals[key].add(number)
            if key in ("IGBP", "IGBP_CLASS", "IGBP_VEGTYPE") and value and value != "-9999":
                labels.add(value)
            if ("HEIGHT" in key or key == "HEIGHTC") and value and value != "-9999":
                heights.append({k: v for k, v in row.items() if k and v})
    if selected is None:
        if any(len(values) != 1 for values in vals.values()):
            raise ValueError("Missing or ambiguous BIF coordinates: " + repr(vals))
        lat, lon = coordinates(next(iter(vals["LOCATION_LAT"])), next(iter(vals["LOCATION_LONG"])))
        coord_source = "RELEASE_BIF"
    else:
        lat, lon = coordinates(selected["latitude"], selected["longitude"])
        if lat not in vals["LOCATION_LAT"] or lon not in vals["LOCATION_LONG"]:
            raise ValueError("Selected coordinates missing from original BIF: " + repr(selected))
        matched = {"LOCATION_LAT": set(), "LOCATION_LONG": set()}
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for record in csv.DictReader(stream):
                if (record.get("GROUP_ID") or "").strip() != selected["group_id"]:
                    continue
                variable = (record.get("VARIABLE") or "").strip().upper()
                if variable in matched:
                    v = (record.get("DATAVALUE") or "").strip()
                    if v and v != "-9999":
                        matched[variable].add(float(v))
        if matched["LOCATION_LAT"] != {lat} or matched["LOCATION_LONG"] != {lon}:
            raise ValueError("Selected coordinates not paired in specified BIF GROUP_ID: " + repr(matched))
        coord_source = "RELEASE_BIF_EXPLICIT_GROUP_" + selected["group_id"]
    return {"latitude": lat, "longitude": lon, "igbp_labels": sorted(labels),
            "igbp_codes": vegetation_codes(labels), "height_records": heights,
            "coordinate_source": coord_source, "source": str(path)}


def inspect_met(raw, site, package):
    product = "FULLSET" if "_FULLSET_" in package else "FLUXMET"
    pattern = re.compile(r"^AMF_" + re.escape(site) + r"_FLUXNET_" + product
                         + r"_(HH|HR)_.*\.csv$", re.I)
    files = sorted(p for p in raw.iterdir() if pattern.fullmatch(p.name))
    if not files:
        raise ValueError("No site-specific {} HH/HR CSV".format(product))
    result = []
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Non-regular meteorology CSV: " + str(path))
        resolution = pattern.fullmatch(path.name).group(1).upper()
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            sample = next(reader, None)
        if not sample:
            raise ValueError("Empty meteorology CSV: " + path.name)
        start = sample.get("TIMESTAMP_START", "")
        end = sample.get("TIMESTAMP_END", "")
        interval = (datetime.strptime(end, "%Y%m%d%H%M")
                    - datetime.strptime(start, "%Y%m%d%H%M")).total_seconds() / 60
        expected = 60 if resolution == "HR" else 30
        if interval != expected:
            raise ValueError("{}: first interval {} min disagrees with {} label".format(
                path.name, interval, resolution))
        result.append({"file": path.name, "product": product, "resolution": resolution,
                       "first_interval_minutes": interval,
                       "first_timestamp_start": start, "first_timestamp_end": end})
    return result


def inspect(row, root, fallbacks, decisions):
    site, package = row["site"], row["package"]
    raw = root / site / "forcing" / "raw" / package
    if not raw.is_dir() or raw.is_symlink():
        raise ValueError("Raw directory missing or symlink: " + str(raw))
    bifs = sorted(p for p in raw.iterdir() if p.suffix.lower() == ".csv"
                  and re.search(r"(?:^|_)" + re.escape(site) + r"_", p.name, re.I)
                  and "_BIF_" in p.name.upper())
    if len(bifs) > 1:
        raise ValueError("Multiple BIF files; choose metadata explicitly")
    if bifs:
        if bifs[0].is_symlink() or not bifs[0].is_file():
            raise ValueError("Non-regular BIF: " + str(bifs[0]))
        info = bif_metadata(bifs[0], site, decisions.get(site))
    else:
        if site != "US-Me2" or "_FULLSET_" not in package:
            raise ValueError("Missing release BIF; no permitted metadata fallback")
        fallback = fallbacks.get(site)
        if not fallback or fallback["package"] != package:
            raise ValueError("Missing or mismatched FULLSET fallback entry")
        lat, lon = coordinates(fallback["latitude"], fallback["longitude"])
        expected_url = "https://ameriflux.lbl.gov/sites/siteinfo/" + site
        if fallback["source_url"] != expected_url or fallback["igbp"] not in IGBP_CODES:
            raise ValueError("Invalid official fallback source or IGBP code")
        info = {"latitude": lat, "longitude": lon,
                "igbp_labels": [fallback["igbp"]], "igbp_codes": [fallback["igbp"]],
                "height_records": [], "coordinate_source": "OFFICIAL_SITE_PAGE_FALLBACK",
                "source": fallback["source_url"], "retrieved_date": fallback["retrieved_date"],
                "source_notes": fallback["notes"]}
    info.update({"site": site, "package": package, "meteorology": inspect_met(raw, site, package)})
    notes = []
    if len(info["igbp_codes"]) != 1:
        notes.append("Missing/ambiguous IGBP label; vegetation review required; Stage02 coordinate PASS is not vegetation acceptance")
    if any(code in ("CRO", "CVM", "WET", "WAT", "URB") for code in info["igbp_codes"]):
        notes.append("Study-inclusion review required for this IGBP class; site not automatically excluded")
    if any(code in ("OSH", "CSH", "GRA", "SAV", "WSA") for code in info["igbp_codes"]):
        notes.append("Non-forest vegetation: evaluate FATES representation before selecting PFTs")
    if not info["height_records"]:
        notes.append("Measurement/canopy height metadata not established; no ZBOT chosen")
    if any(met["resolution"] == "HR" for met in info["meteorology"]):
        notes.append("Hourly source retained; do not assume 48 source records per day")
    if len(info["meteorology"]) > 1:
        notes.append("Multiple HH/HR files present; source selection remains unresolved")
    info["review_notes"] = notes
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    rows = table(HERE / "sites.tsv")
    if len(rows) != 10 or len({r["site"] for r in rows}) != 10:
        parser.error("Expected exactly ten unique manifest sites")
    for row in rows:
        if (not re.fullmatch(r"US-[A-Za-z0-9]+", row["site"])
                or not re.fullmatch(r"AMF_" + re.escape(row["site"])
                                    + r"_FLUXNET_[A-Za-z0-9_.-]+", row["package"])):
            parser.error("Invalid manifest site/package")
    decision_rows = table(HERE / "coordinate_decisions.tsv")
    if len(decision_rows) != 2 or {r["site"] for r in decision_rows} != {"US-Mpj", "US-MtB"}:
        parser.error("Expected two explicit coordinate decisions")
    decisions = {r["site"]: r for r in decision_rows}
    for site, decision in decisions.items():
        matched = next((r for r in rows if r["site"] == site), None)
        if not matched or matched["package"] != decision["package"]:
            parser.error("Coordinate decision release mismatch: " + site)
    fallback_rows = table(HERE / "metadata_fallbacks.tsv")
    if len(fallback_rows) != 1 or {r["site"] for r in fallback_rows} != {"US-Me2"}:
        parser.error("Expected exactly one explicit US-Me2 FULLSET fallback record")
    fallbacks = {r["site"]: r for r in fallback_rows}
    passed, failed = [], []
    print("READ-ONLY BATCH03 STAGE02: coordinates, IGBP, height inventory, first source interval")
    for row in rows:
        print("\n========== {} ==========".format(row["site"]), flush=True)
        try:
            info = inspect(row, args.sites_root.expanduser(), fallbacks, decisions)
            passed.append(info)
            print("COORDINATES: LAT={} LON={}".format(info["latitude"], info["longitude"]))
            print("IGBP LABELS:", ", ".join(info["igbp_labels"]) or "NOT FOUND")
            print("COORDINATE SOURCE:", info["coordinate_source"], info["source"])
            if "source_notes" in info:
                print("SOURCE NOTES:", info["source_notes"])
            for met in info["meteorology"]:
                print("MET:", met["file"], "|", met["resolution"], "| first interval",
                      met["first_interval_minutes"], "min (not full time-series QC)")
            print("HEIGHT METADATA RECORDS:", len(info["height_records"]))
            for record in info["height_records"][:8]:
                print("  ", json.dumps(record, ensure_ascii=True))
            if len(info["height_records"]) > 8:
                print("  Additional height records remain in the BIF for later review")
            for note in info["review_notes"]:
                print("NOTE:", note)
            print("PASS: coordinate + first-interval preflight only", flush=True)
        except (OSError, ValueError, KeyError, TypeError, csv.Error) as exc:
            failed.append(row["site"])
            print("FAILED:", row["site"], str(exc), flush=True)
    print("\n{:<8} {:>10} {:>11} {:<10} {:<8} {}".format(
        "SITE", "LAT", "LON", "IGBP", "MET", "COORDINATE SOURCE"))
    for item in passed:
        print("{:<8} {:>10.4f} {:>11.4f} {:<10} {:<8} {}".format(
            item["site"], item["latitude"], item["longitude"],
            "/".join(item["igbp_codes"]) or "REVIEW",
            "/".join(m["resolution"] for m in item["meteorology"]), item["coordinate_source"]))
    print("\nSTAGE02 SUMMARY: {}/10 coordinate + first-interval checks PASS; failures: {}".format(
        len(passed), ", ".join(failed) or "none"))
    print("PASS does not approve surface/PFT representation, measurement height, coverage or forcing quality.")
    print("No raw data, surfaces, forcing, model cases, Slurm jobs or reports written.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

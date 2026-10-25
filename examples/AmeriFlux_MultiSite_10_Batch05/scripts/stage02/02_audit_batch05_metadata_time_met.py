#!/usr/bin/env python3
"""Batch05 Stage02: read-only original metadata, full HH/HR time and met screen.

Standard library only. No repairs, clock changes, unit conversions, coordinate
choices, ZBOT/PFT assignments, reports, forcing or jobs. Shell tee may save stdout.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path(os.environ.get(
    "FLUXNET_SITES_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
EXPECTED = (
    ("US-UiD", "2008", "2024"), ("US-UMB", "2007", "2021"),
    ("US-UMd", "2007", "2025"), ("US-Var", "2000", "2025"),
    ("US-Vcm", "2007", "2025"), ("US-Vcp", "2007", "2025"),
    ("US-WCr", "1999", "2025"), ("US-Whs", "2007", "2025"),
    ("US-Wjs", "2007", "2025"), ("US-Wkg", "2004", "2025"),
)
FIELDS = {
    "TA": ("TA_F", "TA_F_MDS", "TA"),
    "VPD": ("VPD_F", "VPD_F_MDS", "VPD"),
    "PA": ("PA_F", "PA_F_MDS", "PA"),
    "RH": ("RH_F", "RH"), "WS": ("WS_F", "WS"),
    "P": ("P_F", "P"), "SW_IN": ("SW_IN_F", "SW_IN"),
    "LW_IN": ("LW_IN_F", "LW_IN"),
}
TIME_FLAGS = ("empty", "bad_width", "invalid_timestamp", "bad_duration",
              "gaps", "overlap_or_order_error")


def manifest():
    with (BASE / "sites.tsv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    expected = []
    for site, first, last in EXPECTED:
        suffix = "FULLSET_2007-2021_3-5" if site == "US-UMB" else first + "-" + last + "_v1.3_r1"
        expected.append(dict(site=site, package="AMF_" + site + "_FLUXNET_" + suffix,
                             first_year=first, last_year=last))
    if rows != expected:
        raise ValueError("Manifest differs from exact Batch05 ten-site release cohort")
    return rows


def number(value):
    try:
        val = float(value)
        return val if math.isfinite(val) and val not in (-9999, -6999) else None
    except (ValueError, TypeError):
        return None


def stamp(value):
    if not re.fullmatch(r"\d{12}", value):
        raise ValueError("Invalid timestamp " + repr(value))
    return datetime.strptime(value, "%Y%m%d%H%M")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected regular non-symlink file: " + str(path))
    return path


def metadata(stream, site):
    reader = csv.DictReader(stream)
    if not reader.fieldnames or not {"VARIABLE", "DATAVALUE"}.issubset(reader.fieldnames):
        raise ValueError("BIF lacks VARIABLE/DATAVALUE")
    values, groups, height = defaultdict(set), defaultdict(dict), []
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("BIF row width error")
        if row.get("SITE_ID", "").strip() not in ("", site):
            raise ValueError("BIF SITE_ID mismatch")
        key, value = row["VARIABLE"].strip().upper(), row["DATAVALUE"].strip()
        if not value or value.upper() in ("NA", "NAN") or value in ("-9999", "-9999.0"):
            continue
        if key.startswith("LOCATION_") or key.startswith("IGBP") or "UTC" in key or "TIME_ZONE" in key:
            values[key].add(value)
            group = row.get("GROUP_ID", "").strip() or "NO_GROUP_ID"
            groups[group].setdefault(key, set()).add(value)
        if "HEIGHT" in key or key == "HEIGHTC":
            height.append({k: v for k, v in row.items() if k and v})
    lat = {number(v) for v in values.get("LOCATION_LAT", ())}
    lon = {number(v) for v in values.get("LOCATION_LONG", ())}
    coord_ok = (len(lat) == len(lon) == 1 and None not in lat and None not in lon
                and -90 <= next(iter(lat)) <= 90 and -180 <= next(iter(lon)) <= 180)
    # Even a unique pair is only a metadata candidate, never an input selection.
    return {"coordinate_candidates_unique_valid": coord_ok,
            "values": {k: sorted(v) for k, v in sorted(values.items())},
            "groups": {g: {k: sorted(v) for k, v in sorted(r.items())}
                       for g, r in sorted(groups.items())},
            "height_records": height}


def analyze(stream, minutes):
    reader = csv.reader(stream)
    header = next(reader, [])
    if len(set(header)) != len(header) or not {"TIMESTAMP_START", "TIMESTAMP_END"}.issubset(header):
        raise ValueError("Missing/duplicate timestamp headers")
    idx = {name: i for i, name in enumerate(header)}
    selected = {kind: next((name for name in options if name in idx), None)
                for kind, options in FIELDS.items()}
    counts, valid, missing, qc = Counter(), Counter(), Counter(), defaultdict(Counter)
    minima, maxima, examples = {}, {}, defaultdict(list)
    first = last = previous = None

    def flag(key, when, payload):
        counts[key] += 1
        if len(examples[key]) < 3:
            examples[key].append({"time": when, **payload})

    for row in reader:
        counts["rows"] += 1
        if counts["rows"] % 200000 == 0:
            print("  SCANNED", counts["rows"], "rows", flush=True)
        if len(row) != len(header):
            flag("bad_width", "row=" + str(counts["rows"]), {})
            continue
        label = row[idx["TIMESTAMP_START"]]
        try:
            start, end = stamp(label), stamp(row[idx["TIMESTAMP_END"]])
        except ValueError:
            flag("invalid_timestamp", label, {})
            previous = None
        else:
            if first is None:
                first = start
            last = end
            if (end - start).total_seconds() != minutes * 60:
                flag("bad_duration", label, {"end": str(end)})
            if previous is not None:
                if start > previous:
                    flag("gaps", label, {"previous_end": str(previous),
                                         "gap_minutes": (start - previous).total_seconds() / 60})
                elif start < previous:
                    flag("overlap_or_order_error", label, {"previous_end": str(previous)})
            previous = end
        vals, qvals = {}, {}
        for kind, column in selected.items():
            if column is None:
                continue
            val = number(row[idx[column]])
            qcol = column + "_QC"
            quality = row[idx[qcol]] if qcol in idx else "NO_QC_COLUMN"
            qc[kind][quality] += 1
            vals[kind], qvals[kind] = val, quality
            if val is None:
                missing[kind] += 1
                continue
            valid[kind] += 1
            minima[kind], maxima[kind] = min(val, minima.get(kind, val)), max(val, maxima.get(kind, val))
            flags = []
            if kind == "VPD" and val < 0:
                flags.append("negative_VPD")
            if kind == "RH":
                if val < 1:
                    flags.append("native_RH_lt1pct")
                if val < 0:
                    flags.append("native_RH_negative")
                if val > 100:
                    flags.append("native_RH_gt100pct")
            if kind == "TA" and (val < -80 or val > 60):
                flags.append("TA_outside_minus80_plus60_C")
            if kind == "PA" and (val <= 0 or val < 50 or val > 115):
                flags.append("PA_outside_50_115_kPa")
            if kind in ("WS", "P") and val < 0:
                flags.append("negative_" + kind)
            for key in flags:
                flag(key, label, {"column": column, "value": val, "QC": quality})
        ta, vpd = vals.get("TA"), vals.get("VPD")
        # Screening assumption only: TA in degC, VPD in hPa, saturation over water.
        # This diagnostic is not a verified units/ice-phase conversion or a repair.
        if ta is not None and vpd is not None and -80 <= ta <= 60:
            rh = 100 * (1 - vpd / (6.112 * math.exp(17.67 * ta / (ta + 243.5))))
            for key, condition in (("derived_water_RH_lt1pct", rh < 1),
                                   ("derived_water_RH_negative", rh < 0),
                                   ("derived_water_RH_gt100pct", rh > 100)):
                if condition:
                    flag(key, label, {"RH_water_screen_pct": rh, "TA": ta, "VPD": vpd,
                                      "TA_QC": qvals.get("TA"), "VPD_QC": qvals.get("VPD")})
    counts["empty"] = int(counts["rows"] == 0)
    return {"selected": selected, "counts": dict(counts), "valid": dict(valid),
            "missing": dict(missing), "QC": {k: dict(v) for k, v in qc.items()},
            "minima": minima, "maxima": maxima, "examples": dict(examples),
            "first": str(first) if first else None, "last": str(last) if last else None,
            "time_pass": first is not None and not any(counts[k] for k in TIME_FLAGS)}


def inspect(row, root):
    site, package = row["site"], row["package"]
    raw = root / site / "forcing" / "raw" / package
    if not raw.is_dir() or raw.is_symlink():
        raise ValueError("Missing/symlink raw directory " + str(raw))
    prefix = "AMF_" + site + "_FLUXNET_"
    files = sorted(p for p in raw.iterdir() if p.name.startswith(prefix) and p.suffix.lower() == ".csv")
    bifs = [p for p in files if "_BIF_" in p.name.upper()]
    meta_review = False
    if len(bifs) == 1:
        with regular(bifs[0]).open(encoding="utf-8-sig", newline="") as stream:
            info = metadata(stream, site)
        print("BIF_SHA256", sha256(bifs[0]))
        print("BIF_METADATA", json.dumps(info, sort_keys=True, ensure_ascii=True))
        meta_review = not info["coordinate_candidates_unique_valid"]
        if not any(k.startswith("IGBP") for k in info["values"]):
            print("METADATA_REVIEW: IGBP not found")
            meta_review = True
        labels = [v for k, vs in info["values"].items() if k.startswith("IGBP") for v in vs]
        if any(re.match(r"^(CRO|CVM|WET|WAT|URB)(?:\b|_)", v.upper()) for v in labels):
            print("METADATA_REVIEW: study-inclusion class found; preserve original label for review")
            meta_review = True
        if not info["height_records"]:
            print("HEIGHT_NOTE: no release BIF height records; no ZBOT inferred")
    else:
        print("METADATA_REVIEW: expected one original BIF; found", len(bifs), "(FULLSET may lack BIF)")
        meta_review = True
    product = "FULLSET" if "_FULLSET_" in package else "FLUXMET"
    pattern = re.compile(re.escape(prefix + product) + r"_(HH|HR)_.*\.csv$", re.I)
    mets = [p for p in files if pattern.fullmatch(p.name)]
    if not mets:
        raise ValueError("No original " + product + " HH/HR source")
    if len(mets) > 1:
        print("SOURCE_REVIEW: multiple native HH/HR files; all inspected, none selected as forcing")
    print("ERA_COMPANIONS", [p.name for p in files if re.search(r"_ERA5_(HH|HR)_", p.name, re.I)])
    time_ok, science = True, False
    for path in mets:
        regular(path)
        resolution = pattern.fullmatch(path.name).group(1).upper()
        print("MET_SOURCE", path.name, "NATIVE_LABEL", resolution, flush=True)
        before = path.stat()
        digest = sha256(path)
        with path.open(encoding="utf-8-sig", newline="") as stream:
            result = analyze(stream, 60 if resolution == "HR" else 30)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("Source changed during scan")
        print("MET_SHA256", digest)
        print("MET_RESULT", json.dumps(result, sort_keys=True, ensure_ascii=True))
        expected_start = row["first_year"] + "-01-01 00:00:00"
        expected_end = str(int(row["last_year"]) + 1) + "-01-01 00:00:00"
        print("LABEL_BOUNDARY_SCREEN", "FULL_LABEL_YEARS" if
              (result["first"], result["last"]) == (expected_start, expected_end)
              else "PARTIAL_OR_DIFFERENT_LABEL_COVERAGE_REVIEW", flush=True)
        time_ok = time_ok and result["time_pass"]
        science = science or any(v for k, v in result["counts"].items() if k not in TIME_FLAGS and k != "rows")
        science = science or any(result["missing"].values()) or any(v is None for v in result["selected"].values())
    return time_ok, meta_review, science


def self_test():
    header = "TIMESTAMP_START,TIMESTAMP_END,TA_F,VPD_F,TA_F_QC,VPD_F_QC\n"
    rows = "202002282330,202002290000,0,7,0,2\n202002290000,202002290030,0,-1,0,1\n"
    result = analyze(io.StringIO(header + rows), 30)
    assert result["time_pass"] and result["counts"]["derived_water_RH_negative"] == 1
    assert result["counts"]["negative_VPD"] == 1
    hourly = "200701010000,200701010100,10,1,0,0\n"
    assert analyze(io.StringIO(header + hourly), 60)["time_pass"]
    assert not analyze(io.StringIO(header + hourly), 30)["time_pass"]
    gap = rows + "202002290100,202002290130,0,-9999,0,2\n"
    assert analyze(io.StringIO(header + gap), 30)["counts"]["gaps"] == 1
    assert analyze(io.StringIO(header + rows + rows), 30)["counts"]["overlap_or_order_error"] == 1
    assert not analyze(io.StringIO(header), 30)["time_pass"]
    assert number("-9999.00") is None and number("nan") is None
    bif = "SITE_ID,GROUP_ID,VARIABLE,DATAVALUE\nUS-UMB,1,LOCATION_LAT,45\nUS-UMB,1,LOCATION_LONG,-84\n"
    assert metadata(io.StringIO(bif), "US-UMB")["coordinate_candidates_unique_valid"]
    assert not metadata(io.StringIO(bif + "US-UMB,2,LOCATION_LONG,-85\n"), "US-UMB")["coordinate_candidates_unique_valid"]
    print("STAGE02 SELF-TEST PASS: HH/HR, Gregorian leap day, gap/overlap, empty, missing sentinels, negative VPD/derived RH, ambiguous BIF; NO WRITES")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--sites", nargs="+")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    rows = manifest()
    if args.self_test:
        self_test()
        return 0
    catalog = {row["site"]: row for row in rows}
    selected = args.sites or list(catalog)
    if len(set(selected)) != len(selected) or set(selected) - set(catalog):
        parser.error("Select distinct Batch05 sites only")
    print("BATCH05 STAGE02 READ-ONLY METADATA / COMPLETE NATIVE HH-HR / BASIC MET SCREEN")
    print("SCREENING UNIT ASSUMPTIONS: TA degC; VPD hPa; PA kPa; RH percent. Verify release units before repairs.")
    print("Derived RH uses saturation over water: subfreezing/ice flags need separate science review.")
    time_pass, time_review, meta_review, science_review, failed = [], [], [], [], []
    for site in selected:
        print("\n==========", site, "==========", flush=True)
        try:
            time_ok, meta, science = inspect(catalog[site], args.sites_root.expanduser())
            (time_pass if time_ok else time_review).append(site)
            if meta:
                meta_review.append(site)
            if science:
                science_review.append(site)
            print("SITE_STATUS", site, "TIME", "PASS" if time_ok else "REVIEW",
                  "METADATA", "REVIEW" if meta else "CANDIDATES_AVAILABLE", flush=True)
        except (OSError, ValueError, KeyError, csv.Error) as exc:
            failed.append(site)
            print("FAILED", site, str(exc), flush=True)
    print("\nSTAGE02 SUMMARY: examined={}/{} time_pass={} time_review={} metadata_review={} science_review={} failed={}".format(
        len(selected) - len(failed), len(selected), len(time_pass), ",".join(time_review) or "none",
        ",".join(meta_review) or "none", ",".join(science_review) or "none", ",".join(failed) or "none"))
    print("NO WRITES. Time PASS is internal chronology only; metadata candidates, QC/missingness and unit/clock science remain separate.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

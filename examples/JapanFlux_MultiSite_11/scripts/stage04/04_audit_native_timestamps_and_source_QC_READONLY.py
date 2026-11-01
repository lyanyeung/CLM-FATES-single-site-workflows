#!/usr/bin/env python3
"""JapanFlux Stage04: read-only native time-axis and meteorological source-QC screen.

Full CSV stream for one or all 11 stations. Original tower and ERA values are NOT
replaced. No extraction to filesystem, output is JSON on stdout, no model jobs.
Flags are *screens* (not corrections or scientific approvals), and numeric
thresholds are explicitly conditional on conventional FLUXNET units.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import io
import json
import math
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
JPF = {"JP-Api", "JP-Fhk", "JP-Fjy", "JP-Khw", "JP-Spp", "JP-Tak", "JP-Tef", "JP-Tmd", "JP-Yms"}
SPECIAL = {"JP-Tom", "JP-Tgf"}
FIELDS = ("TA_F", "RH_F", "VPD_F", "PA_F", "SW_IN_F", "LW_IN_F", "P_F", "WS_F")
# These are provisional diagnostics only, pending BIF, metadata and units.
SCREENS = {
    "TA_F": [("LT_-70_C", -70.0, "lt"), ("GT_60_C", 60.0, "gt")],
    "RH_F": [("LT_0_pct", 0.0, "lt"), ("LT_1_pct", 1.0, "lt"), ("GT_100_pct", 100.0, "gt")],
    "VPD_F": [("LT_0_hPa", 0.0, "lt")],
    "PA_F": [("LT_50_kPa", 50.0, "lt"), ("GT_115_kPa", 115.0, "gt")],
    "SW_IN_F": [("LT_-20_W_m2", -20.0, "lt"), ("GT_1500_W_m2", 1500.0, "gt")],
    "LW_IN_F": [("LT_50_W_m2", 50.0, "lt"), ("GT_700_W_m2", 700.0, "gt")],
    "P_F": [("LT_0_native_precip_unit", 0.0, "lt")],
    "WS_F": [("LT_0_m_s", 0.0, "lt"), ("GT_70_m_s", 70.0, "gt")],
}
BAD = {"", "NA", "NAN", "NULL", "NONE", "INF", "+INF", "-INF", "-9999", "-9999.0", "-6999", "-6999.0"}


def timestamp(value: str) -> datetime:
    s = value.strip()
    if len(s) != 12 or not s.isdigit():
        raise ValueError("expected YYYYMMDDHHMM")
    return datetime(int(s[:4]), int(s[4:6]), int(s[6:8]),
                    int(s[8:10]), int(s[10:12]))


def number(value: str) -> float | None:
    v = value.strip()
    if v.upper() in BAD:
        return None
    try:
        n = float(v)
        if not math.isfinite(n) or n <= -6999.0:
            return None
        return n
    except ValueError:
        return None


def safe_relative(s: str) -> bool:
    p = PurePosixPath(s.replace("\\", "/"))
    return not p.is_absolute() and ".." not in p.parts and not any(":" in x for x in p.parts)


def expected_files(site: str, zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    items = [i for i in zf.infolist() if not i.is_dir() and safe_relative(i.filename)]
    if site in JPF:
        match = [i for i in items if "_FLUXMET_HH_" in PurePosixPath(i.filename).name
                 and i.filename.lower().endswith(".csv")]
        if len(match) != 1:
            raise ValueError(f"Expected one FLUXMET_HH source, found {len(match)}")
        return match
    if site == "JP-Tgf":
        match = [i for i in items if "_COREVARS_HH_" in PurePosixPath(i.filename).name
                 and i.filename.lower().endswith(".csv")]
        if len(match) != 1:
            raise ValueError(f"Expected one COREVARS_HH source, found {len(match)}")
        return match
    if site == "JP-Tom":
        hr = [i for i in items if "_COREVARS_HR_" in PurePosixPath(i.filename).name
              and i.filename.lower().endswith(".csv")]
        hh = [i for i in items if "_COREVARS_HH_" in PurePosixPath(i.filename).name
              and i.filename.lower().endswith(".csv")]
        if len(hr) != 1 or len(hh) != 1:
            raise ValueError(f"Expected one COREVARS_HR and one COREVARS_HH, found {len(hr)}/{len(hh)}")
        return hr + hh
    raise ValueError("Unknown JapanFlux site")


def scan_csv(zf: zipfile.ZipFile, member: zipfile.ZipInfo, max_rows: int, event_limit: int) -> dict:
    label = PurePosixPath(member.filename).name
    expected_minutes = 60 if "_HR_" in label else 30
    out = {"member": member.filename, "expected_minutes": expected_minutes,
           "mode": "READONLY_RAW_NATIVE_TIMESTAMP_UNVERIFIED_TIMEZONE",
           "source_QC_semantics": "RAW_LABELS_NOT_INTERPRETED",
           "rows": 0, "first_interval": None, "last_interval": None,
           "years": {}, "time": {
               "timestamp_parse_errors": 0, "nonpositive_intervals": 0,
               "wrong_length_intervals": 0, "duplicate_start": 0,
               "gaps": 0, "overlaps": 0, "nonmonotonic_starts": 0,
               "examples": [],
           }, "fields": {}, "status": "OK"}
    with zf.open(member) as stream:
        with io.TextIOWrapper(stream, encoding="utf-8-sig", newline="", errors="replace") as text:
            reader = csv.reader(text)
            cols = next(reader)
            if len(cols) != len(set(cols)):
                raise ValueError("Duplicate CSV columns")
            names = {c: k for k, c in enumerate(cols)}
            if "TIMESTAMP_START" not in names or "TIMESTAMP_END" not in names:
                raise ValueError("Missing interval timestamps")
            out["column_count"] = len(cols)
            out["missing_fields"] = [v for v in FIELDS if v not in names]
            out["available_QC_columns"] = [c for c in cols if c.endswith("_QC")]
            active = [field for field in FIELDS if field in names]
            stats = {}
            for field in active:
                stats[field] = {"available": True, "valid": 0, "missing": 0,
                                "min": None, "max": None, "raw_QC_counts": {},
                                "screen_counts": {}, "screen_samples": [],
                                "by_year": {}}
            tstat = out["time"]
            counts = {f: Counter() for f in active}
            flags = {f: Counter() for f in active}
            yrs = {f: defaultdict(lambda: [0, 0]) for f in active}
            samples = {f: [] for f in active}
            qc_indexes = {f: names.get(f + "_QC") for f in active}
            prev_start = prev_end = None
            years = Counter()
            for raw in reader:
                if max_rows and out["rows"] >= max_rows:
                    break
                out["rows"] += 1
                rowid = out["rows"]
                if len(raw) != len(cols):
                    raise ValueError(f"ROW_WIDTH_MISMATCH at data row {rowid}: {len(raw)} != {len(cols)}")
                a = raw[names["TIMESTAMP_START"]]
                b = raw[names["TIMESTAMP_END"]]
                try:
                    st, en = timestamp(a), timestamp(b)
                except ValueError:
                    tstat["timestamp_parse_errors"] += 1
                    if len(tstat["examples"]) < event_limit:
                        tstat["examples"].append({"row": rowid, "issue": "BAD_TIMESTAMP", "start": a, "end": b})
                    prev_start = prev_end = None
                    continue
                year = st.year
                years[year] += 1
                if out["first_interval"] is None:
                    out["first_interval"] = [a, b]
                out["last_interval"] = [a, b]
                step = (en - st).total_seconds() / 60
                if step <= 0:
                    tstat["nonpositive_intervals"] += 1
                if step != expected_minutes:
                    tstat["wrong_length_intervals"] += 1
                    if len(tstat["examples"]) < event_limit:
                        tstat["examples"].append({"row": rowid, "issue": "INTERVAL_LENGTH",
                                                   "start": a, "end": b, "minutes": step})
                if prev_start is not None:
                    if st == prev_start:
                        tstat["duplicate_start"] += 1
                    if st < prev_start:
                        tstat["nonmonotonic_starts"] += 1
                    if st > prev_end:
                        tstat["gaps"] += 1
                        if len(tstat["examples"]) < event_limit:
                            tstat["examples"].append({"row": rowid, "issue": "GAP",
                                                       "previous_end": prev_end.strftime("%Y%m%d%H%M"),
                                                       "next_start": a,
                                                       "minutes": (st-prev_end).total_seconds()/60})
                    if st < prev_end:
                        tstat["overlaps"] += 1
                        if len(tstat["examples"]) < event_limit:
                            tstat["examples"].append({"row": rowid, "issue": "OVERLAP",
                                                       "previous_end": prev_end.strftime("%Y%m%d%H%M"),
                                                       "next_start": a})
                prev_start, prev_end = st, en
                for f in active:
                    stat = stats[f]
                    value = number(raw[names[f]])
                    if value is None:
                        stat["missing"] += 1
                        yrs[f][year][1] += 1
                        continue
                    stat["valid"] += 1
                    yrs[f][year][0] += 1
                    if stat["min"] is None or value < stat["min"]:
                        stat["min"] = value
                    if stat["max"] is None or value > stat["max"]:
                        stat["max"] = value
                    qi = qc_indexes[f]
                    if qi is not None:
                        q = raw[qi].strip()
                        counts[f][q if q else "<blank>"] += 1
                    for tag, bound, op in SCREENS.get(f, []):
                        if (value < bound if op == "lt" else value > bound):
                            flags[f][tag] += 1
                            if len(samples[f]) < event_limit:
                                samples[f].append({"start": a, "end": b,
                                                   "field": f, "value": value,
                                                   "QC_raw": raw[qi] if qi is not None else None,
                                                   "screen": tag})
            for f in active:
                stats[f]["raw_QC_counts"] = dict(counts[f].most_common())
                stats[f]["screen_counts"] = dict(flags[f])
                stats[f]["screen_samples"] = samples[f]
                stats[f]["by_year"] = {str(y): {"valid": c[0], "missing": c[1]}
                                       for y, c in sorted(yrs[f].items())}
            out["fields"] = stats
            out["years"] = {str(y): n for y, n in sorted(years.items())}
            out["truncated_by_max_rows"] = bool(max_rows and out["rows"] >= max_rows)
    return out


def inspect_site(row: dict, root: Path, limit_bytes: int, max_rows: int, event_limit: int) -> dict:
    site, pkg = row["site"], row["package"]
    path = root / site / "forcing" / "packages" / (pkg + ".zip")
    report = {"site": site, "path": str(path), "source_release_year_labels":
              [row["first_year"], row["last_year"]], "files": []}
    if not path.is_file() or path.is_symlink():
        return {**report, "status": "ERROR", "error": "Missing or symlinked ZIP"}
    try:
        with zipfile.ZipFile(path) as outer:
            if site in JPF:
                members = [i for i in outer.infolist() if i.filename == pkg + ".zip" and not i.is_dir()]
                if len(members) != 1:
                    raise ValueError("Missing exact inner ZIP")
                inner_info = members[0]
                if inner_info.file_size > limit_bytes:
                    raise ValueError("Nested ZIP over RAM cap")
                with io.BytesIO() as memory:
                    with outer.open(inner_info) as source:
                        copied = 0
                        while True:
                            buf = source.read(4 * 1024 * 1024)
                            if not buf:
                                break
                            copied += len(buf)
                            if copied > limit_bytes:
                                raise ValueError("Nested ZIP exceeded RAM cap")
                            memory.write(buf)
                    memory.seek(0)
                    with zipfile.ZipFile(memory) as inner:
                        report["files"] = [scan_csv(inner, i, max_rows, event_limit)
                                           for i in expected_files(site, inner)]
                report["zip_layer"] = "DOUBLE"
            else:
                report["files"] = [scan_csv(outer, i, max_rows, event_limit)
                                   for i in expected_files(site, outer)]
                report["zip_layer"] = "DIRECT"
        report["status"] = "READONLY_SCREEN_DONE"
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, EOFError,
            UnicodeError, MemoryError, csv.Error) as exc:
        report["status"] = "ERROR"
        report["error"] = str(exc)
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--site", choices=sorted(JPF | SPECIAL))
    p.add_argument("--max-nested-mib", type=int, default=256)
    p.add_argument("--max-rows", type=int, default=0, help="0 means ALL rows; >0 is a partial pilot only")
    p.add_argument("--example-limit", type=int, default=12)
    a = p.parse_args()
    if not 64 <= a.max_nested_mib <= 1024 or not 0 <= a.max_rows <= 10_000_000 or not 0 <= a.example_limit <= 50:
        p.error("Invalid limits")
    with a.manifest.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 11 or {r["site"] for r in rows} != JPF | SPECIAL:
        p.error("Manifest must contain exact 11 JapanFlux sites")
    chosen = [r for r in rows if a.site is None or r["site"] == a.site]
    report = {"stage": "JapanFlux Stage04", "read_only": True, "full_scan_requested": a.max_rows == 0,
              "time_zone": "NOT_INFERRED", "units": "CONVENTIONAL_UNVERIFIED",
              "science_approval": "NOT_APPROVED", "sites": [
                  inspect_site(r, a.root, a.max_nested_mib * 1024 * 1024,
                               a.max_rows, a.example_limit) for r in chosen]}
    report["screened"] = sum(s["status"] == "READONLY_SCREEN_DONE" for s in report["sites"])
    report["expected"] = len(chosen)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["screened"] == report["expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

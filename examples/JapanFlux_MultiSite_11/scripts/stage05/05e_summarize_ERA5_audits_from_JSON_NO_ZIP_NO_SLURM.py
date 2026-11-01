#!/usr/bin/env python3
"""JapanFlux Stage05E: compare Stage05D saved JSON reports, without rereading ZIPs.

No Slurm, no source writes, no physical repair. Accepts partial 3-site
inventory or complete 9-site inventory; reports site-by-year *screen* counts.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

SITES = ("JP-Api", "JP-Fhk", "JP-Fjy", "JP-Khw", "JP-Spp",
         "JP-Tak", "JP-Tef", "JP-Tmd", "JP-Yms")
FIELDS = ("TA_ERA", "PA_ERA", "LW_IN_ERA", "SW_IN_ERA",
          "VPD_ERA", "P_ERA", "WS_ERA")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", type=Path, required=True, help="Folder of JP-*_ERA5_audit.json")
    p.add_argument("--events", action="store_true", help="Print deduplicated stored event examples")
    p.add_argument("--check", action="store_true", help="Check all 9 saved JSON files; do not summarize or fail on an invalid file")
    p.add_argument("--ignore-invalid", action="store_true", help="Explicitly exclude invalid files and summarize VALID reports only (INCOMPLETE)")
    a = p.parse_args()
    reports = {}
    bad = {}
    for site in SITES:
        f = a.dir / (site + "_ERA5_audit.json")
        if not f.is_file():
            bad[site] = "MISSING"
            continue
        size = f.stat().st_size
        if size == 0:
            bad[site] = "EMPTY (0 bytes; likely interrupted/failed redirected output)"
            continue
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(r, dict):
                raise ValueError("JSON root is not an object")
            if r.get("stage") != "JapanFlux Stage05D" or r.get("site") != site:
                raise ValueError("Unexpected stage/site identity")
            if r.get("status") != "ERA5_FULL_SCAN_COMPLETED" or r.get("read_only") is not True:
                raise ValueError("Incomplete or non-read-only audit")
            if not isinstance(r.get("rows"), int) or r["rows"] < 1:
                raise ValueError("Missing or invalid scanned row count")
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, OSError) as exc:
            bad[site] = f"INVALID ({size} bytes; {type(exc).__name__}: {exc})"
            continue
        reports[site] = r
    if a.check:
        print("STAGE05E VALIDATE SAVED REPORTS ONLY: NO ZIP, NO SLURM, NO CHANGES")
        for site in SITES:
            if site in reports:
                r = reports[site]
                print(site, "VALID", "rows=" + str(r["rows"]),
                      "unique_screen_flags=" + str(r.get("flagged_unique_native_starts")))
            else:
                print(site, bad[site])
        print("VALID", len(reports), "/9", "MISSING_OR_INVALID", len(bad))
        return 0
    bad_files = {site: problem for site, problem in bad.items() if not problem.startswith("MISSING")}
    if bad_files and not a.ignore_invalid:
        p.error("Cannot summarize invalid existing JSON files; run --check to identify: "
                + "; ".join(f"{s}: {problem}" for s, problem in bad_files.items())
                + ". Rerun Stage05D ONLY for invalid sites; no existing valid file needs rescanning.")
    if not reports:
        p.error("No valid Stage05D station reports in --dir")
    if bad_files:
        print("WARNING: INCOMPLETE SUMMARY; INVALID REPORTS EXCLUDED BY --ignore-invalid")
        for site, problem in bad_files.items():
            print("INVALID_REPORT", site, problem)

    print("STAGE05E READ-ONLY SUMMARIES FROM SAVED ERA5_HH JSON; NO ZIP OR SLURM")
    print("STATIONS_LOADED", len(reports), "/9", ",".join(reports))
    print("UNSCANNED", ",".join(s for s in SITES if s not in reports) or "NONE")
    print("Time-label timezone and variable units not independently verified.")
    print("Station source files from same JPF release, not independent ECMWF validation.")

    grouped_by_year = defaultdict(Counter)
    for site, r in reports.items():
        f = r.get("fields", {})
        flags = {v: int(f.get(v, {}).get("flag_count", 0)) for v in FIELDS}
        first, last = r.get("first_interval"), r.get("last_interval")
        print("\nSITE", site, "SOURCE_ROWS", r.get("rows"),
              "UNIQUE_FLAGGED_INTERVALS", r.get("flagged_unique_native_starts"),
              "FIRST_LAST", first, last)
        print("  SCREEN_COUNTS", json.dumps({k: n for k, n in flags.items() if n},
                                        sort_keys=True))
        print("  TIME_ERRORS", json.dumps({k: v for k, v in r.get("time_errors", {}).items() if v},
                                        sort_keys=True) or "{}")
        by_year = r.get("flag_counts_by_year", {})
        for year, c in sorted(by_year.items()):
            year_flags = {k.removesuffix(":flagged"): n
                          for k, n in c.items() if k.endswith(":flagged") and n}
            if not year_flags:
                continue
            grouped_by_year[year][site] += sum(year_flags.values())
            print("  YEAR", year, json.dumps(year_flags, sort_keys=True))
        if a.events:
            # The original Stage05D script limits examples per variable.
            # Its watched date records can supply later years. Never present
            # these stored samples as an exhaustive abnormal-time ledger.
            sample = defaultdict(dict)
            for v, rows in r.get("examples_by_flag", {}).items():
                for item in rows:
                    sample[(item["start"], item["end"])][v] = item["value"]
            for rows in r.get("watched_dates", {}).values():
                for item in rows:
                    if not item.get("flags"):
                        continue
                    key = item["start"], item["end"]
                    for flag in item["flags"]:
                        sample[key][flag["variable"]] = flag["value"]
            print("  STAGE05D_STORED_SAMPLED_FLAGS_ONLY", len(sample))
            for (start, end), values in sorted(sample.items()):
                print("    EVENT", start, end, json.dumps(values, sort_keys=True))
    print("\nCROSS_SITE_SCREEN_YEAR_COUNTS")
    for year, sites in sorted(grouped_by_year.items()):
        print("YEAR", year, "N_SITES_WITH_FLAGS", len(sites),
              "SITES", json.dumps(dict(sites), sort_keys=True))
    print("\nCAVEAT: Stage05D examples may be capped at 12 per variable;")
    print("watched dates only cover 20050812, 20111217 and 20220409.")
    print("NO SCIENTIFIC APPROVAL, NO ORIGINAL-SOURCE CHANGES, NO AD400.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""JapanFlux Stage05G: aggregate eight Stage05F source-event impact JSON files.

No ZIP reading, no Slurm, no original source edits, no repair, no model work.
Creates derived audit TSV and JSON in operator-selected output directory.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

SITES = ("JP-Fhk", "JP-Fjy", "JP-Khw", "JP-Spp", "JP-Tak",
         "JP-Tef", "JP-Tmd", "JP-Yms")
VARIABLES = ("TA", "PA", "LW_IN", "SW_IN", "VPD", "P", "WS")
FIELDS = ("site", "native_start", "variable", "source_ERA_flagged",
          "source_ERA_value_from_stage05d", "source_selected_F_value",
          "embedded_ERA_value", "selected_F_QC_raw", "selected_F_MDS_value",
          "selected_F_screen_nonphysical", "selected_F_vs_flagged_ERA",
          "classification")


def classified(flag_era: bool, flag_f: bool, comparison: str) -> str:
    if flag_era and flag_f and comparison == "EQUAL":
        return "FLAGGED_ERA_EQUALS_NONPHYSICAL_SELECTED_F"
    if flag_era and not flag_f and comparison == "DIFFERENT":
        return "FLAGGED_ERA_SELECTED_F_DIFFERS_AND_NOT_THRESHOLD_FLAGGED"
    if flag_era and flag_f:
        return "FLAGGED_ERA_AND_NONPHYSICAL_SELECTED_F_REVIEW"
    if flag_era:
        return "FLAGGED_ERA_SELECTED_F_SOURCE_OR_VALUES_UNRESOLVED"
    if flag_f:
        return "NONPHYSICAL_SELECTED_F_IN_CONTEXT_NO_SAME_FIELD_ERA_FLAG"
    raise ValueError("Not a ledger event")


def analyse(folder: Path) -> tuple[list[dict], dict]:
    records: list[dict] = []
    per_site: dict = {}
    across = Counter()
    all_event = set()
    f_nonphysical = set()
    for site in SITES:
        file = folder / f"{site}_impact.json"
        r = json.loads(file.read_text(encoding="utf-8"))
        if (r.get("stage") != "JapanFlux Stage05F" or r.get("site") != site or
                r.get("status") != "READONLY_SOURCE_IMPACT_SCREEN_COMPLETE" or
                r.get("science_decision") != "NOT_APPROVED_NO_REPLACEMENTS"):
            raise ValueError(f"Invalid or unapproved site report {file}")
        total_ERA = r.get("ERA5_HH_unique_flagged_starts_full_period")
        inside = r.get("ERA5_event_starts_inside_FLUXMET_source")
        outside = r.get("ERA5_event_starts_outside_FLUXMET_source")
        if not isinstance(inside, int) or not isinstance(outside, list) or total_ERA != inside + len(outside):
            raise ValueError(f"Stage05F event overlap accounting mismatch: {site}")
        row_list = r.get("rows_selected", [])
        if not isinstance(row_list, list):
            raise ValueError(f"Missing rows_selected: {site}")
        site_events = set()
        flagged_counts = Counter()
        per_class = Counter()
        site_F_times = set()
        time_seen = set()
        site_source_ERA_flags = Counter()
        for row in row_list:
            t = row["native_start"]
            if t in time_seen:
                raise ValueError(f"Duplicate selected row in {site} at {t}")
            time_seen.add(t)
            eflags = row.get("source_event_ERA_flags", {})
            fflags = set(row.get("selected_F_physical_flags", []))
            comp = row.get("selected_F_vs_embedded_ERA_when_source_flagged", {})
            cells = row.get("cells", {})
            if eflags:
                site_events.add(t)
                all_event.add((site, t))
            for variable in VARIABLES:
                eflag = variable + "_ERA" in eflags
                fflag = variable + "_F" in fflags
                if eflag:
                    site_source_ERA_flags[variable] += 1
                if fflag:
                    flagged_counts[variable] += 1
                    f_nonphysical.add((site, t))
                    site_F_times.add(t)
                if not eflag and not fflag:
                    continue
                match = comp.get(variable, "NOT_TESTED_SOURCE_NOT_FLAGGED")
                cl = classified(eflag, fflag, match)
                per_class[cl] += 1
                records.append({
                    "site": site, "native_start": t, "variable": variable,
                    "source_ERA_flagged": int(eflag),
                    "source_ERA_value_from_stage05d": eflags.get(variable + "_ERA", ""),
                    "source_selected_F_value": cells.get(variable + "_F", ""),
                    "embedded_ERA_value": cells.get(variable + "_ERA", ""),
                    "selected_F_QC_raw": cells.get(variable + "_F_QC", ""),
                    "selected_F_MDS_value": cells.get(variable + "_F_MDS", ""),
                    "selected_F_screen_nonphysical": int(fflag),
                    "selected_F_vs_flagged_ERA": match,
                    "classification": cl,
                })
        if len(site_events) != inside:
            raise ValueError(f"Site stored source event times != inside count for {site}")
        actual = r.get("selected_F_screen_flagged_by_field", {})
        if dict(flagged_counts) != actual:
            raise ValueError(f"Selected F flagged count mismatch for {site}: {dict(flagged_counts)} != {actual}")
        counts = {"source_anomaly_time_points_in_tower_era": inside,
                  "source_anomaly_time_points_outside_tower_era": len(outside),
                  "selected_F_variable_flags_in_event_context": dict(flagged_counts),
                  "selected_F_unique_time_points_in_event_context": len(site_F_times),
                  "source_ERA_flags_inside_by_variable": dict(site_source_ERA_flags),
                  "classification_counts": dict(per_class)}
        per_site[site] = counts
        across.update(flagged_counts)
    records.sort(key=lambda r: (r["site"], r["native_start"], r["variable"]))
    summary = {"stage": "JapanFlux Stage05G",
               "status": "READONLY_SOURCE_IMPACT_AGGREGATED",
               "sites_completed": len(per_site),
               "sites": per_site,
               "all_selected_F_variable_flag_counts": dict(across),
               "all_selected_F_variable_flag_occurrences": sum(across.values()),
               "selected_F_unique_site_native_times_in_event_context": len(f_nonphysical),
               "source_ERA_flagged_site_native_times_inside_tower_era": len(all_event),
               "source_ERA_flagged_site_native_times_outside_tower_era": sum(
                   d["source_anomaly_time_points_outside_tower_era"] for d in per_site.values()),
               "ledger_rows": len(records),
               "interpretation": "Candidate physical threshold flags; not repair approval. Site/time/variable exact.",
               "clock": "Original JPF source clock, timezone unverified",
               "upstream_ERA5": "Same released source only; independent ECMWF source not checked",
               "writes": "Only derived TSV/JSON audit outputs, never source ZIP or selected forcing"}
    return records, summary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    if args.input_dir.resolve() == args.output_dir.resolve():
        p.error("Output directory must differ from input to protect the original audit JSONs")
    records, summary = analyse(args.input_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tsv = args.output_dir / "stage05g_source_selected_event_ledger.tsv"
    js = args.output_dir / "stage05g_source_selected_summary.json"
    # Prevent silently replacing a previously generated audit: run in new dir.
    if tsv.exists() or js.exists():
        p.error("Output already exists, use a NEW output directory")
    with tsv.open("x", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t")
        w.writeheader()
        w.writerows(records)
    with js.open("x", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("STAGE05G READ-ONLY AUDIT AGGREGATION COMPLETE (NO SLURM)")
    print("VERIFIED", summary["sites_completed"], "/ 8")
    print("ERA_EVENT_INSIDE_TOWER", summary["source_ERA_flagged_site_native_times_inside_tower_era"])
    print("ERA_EVENT_OUTSIDE_TOWER", summary["source_ERA_flagged_site_native_times_outside_tower_era"])
    print("SELECTED_F_VARIABLE_FLAGS", summary["all_selected_F_variable_flag_counts"])
    print("SELECTED_F_UNIQUE_SITE_TIMES", summary["selected_F_unique_site_native_times_in_event_context"])
    for name, s in summary["sites"].items():
        print("SITE", name, "F_FLAGS", s["selected_F_variable_flags_in_event_context"],
              "UNIQUE_F_FLAGGED_TIMES", s["selected_F_unique_time_points_in_event_context"])
    print("LEDGER", tsv)
    print("SUMMARY", js)
    print("NO APPROVED REPAIR OR ORIGINAL DATA CHANGES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

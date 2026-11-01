#!/usr/bin/env python3
"""JapanFlux Stage05A: summarize the EXISTING Stage04 QC JSON without ZIP reads.

Read-only; no Slurm, no ZIP reads, no tower file edits, no forcing or repairs.
Output includes actual time-labelled Stage04 anomaly samples with raw QC labels.
Samples were capped at Stage04 creation time: these are NOT all flagged rows.
"""
import argparse
import json
import math
from pathlib import Path

ORDER = [
    "JP-Khw", "JP-Tmd", "JP-Fjy", "JP-Yms", "JP-Tef",
    "JP-Tom", "JP-Tgf", "JP-Api", "JP-Fhk", "JP-Spp", "JP-Tak"
]
SEVERE = {
    "LT_-70_C", "LT_50_kPa", "LT_50_W_m2", "LT_-20_W_m2",
    "GT_100_pct", "LT_0_hPa"
}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, required=True, help="Stage04 full11_raw_source_qc.json")
    ap.add_argument("--site", default=None, help="Optional JP-* site ID")
    ap.add_argument("--samples-per-flag", type=int, default=4)
    a = ap.parse_args()
    if not 0 <= a.samples_per_flag <= 20:
        ap.error("--samples-per-flag must be 0..20")
    r = json.loads(a.json.read_text(encoding="utf-8"))
    if r.get("stage") != "JapanFlux Stage04":
        ap.error("Not a Stage04 audit JSON")
    if r.get("screened") != 11 or r.get("expected") != 11 or not r.get("full_scan_requested"):
        ap.error("Expected complete eleven-site, full-row Stage04 screen")
    sites = {s["site"]: s for s in r["sites"]}
    if a.site and a.site not in sites:
        ap.error("Unknown site")
    print("STAGE05A — original Stage04 results only; no re-scan; NO REPAIRS")
    print("All source QC labels printed verbatim; QC semantics NOT inferred.")
    print("No claims of UTC/JST/units proof or scientific forcing acceptance.")
    for name in ORDER:
        if a.site and a.site != name:
            continue
        s = sites[name]
        print("\n" + "=" * 72)
        print("SITE", name, "STATUS", s.get("status"))
        for part in s.get("files", []):
            print("SOURCE", Path(part["member"]).name)
            yrs = list(part.get("years", {}))
            print("ROWS", part.get("rows"),
                  "NATIVE_FIRST_LAST_INTERVAL", part.get("first_interval"), part.get("last_interval"),
                  "START_YEARS", (yrs[0], yrs[-1]) if yrs else "?")
            problems = {k: v for k, v in part.get("time", {}).items()
                        if k != "examples" and isinstance(v, int) and v}
            print("TIME_ERRORS", problems or "NONE")
            print("MISSING_COLUMN", ",".join(part.get("missing_fields", [])) or "NONE")
            total_flags = 0
            for field, q in part.get("fields", {}).items():
                raw = q.get("screen_counts", {})
                if not raw:
                    continue
                grouped = {}
                for flag, count in raw.items():
                    # Tiny negative precipitation is a floating point artefact candidate;
                    # numerical tolerance is not an approved data modification.
                    if field == "P_F" and flag == "LT_0_native_precip_unit":
                        mn = q.get("min")
                        classification = ("TINY_NEGATIVE_ROUNDOFF_CANDIDATE"
                                          if isinstance(mn, (int, float))
                                          and -1e-9 < mn < 0
                                          else "NEGATIVE_PRECIP_REVIEW")
                    else:
                        classification = "SOURCE_SCIENCE_REVIEW"
                    grouped[flag] = {"count": count, "classification": classification}
                    total_flags += count
                print("FIELD", field, "range=", [q.get("min"), q.get("max")],
                      "valid=", q.get("valid"), "missing=", q.get("missing"))
                print(" FLAG_COUNTS", json.dumps(grouped, ensure_ascii=False))
                print(" ALL_ROWS_RAW_QC_LABEL_COUNTS",
                      json.dumps(q.get("raw_QC_counts", {}), ensure_ascii=False))
                shown = {tag: 0 for tag in raw}
                for ev in q.get("screen_samples", []):
                    tag = ev["screen"]
                    if tag not in shown or shown[tag] >= a.samples_per_flag:
                        continue
                    print(" SOURCE_EVENT", ev["start"], ev["end"],
                          field, ev["value"], "QC_RAW", ev.get("QC_raw"), "RULE", tag)
                    shown[tag] += 1
            print("VARIABLE_FLAG_OCCURRENCES", total_flags,
                  "(not unique time steps; threshold screen, not scientific approval)")
    print("\nNEXT: inspect exact flagged original rows together with contemporaneous")
    print("ERA5/ERA columns, native source channels and QC provenance;")
    print("do not overwrite or automatically approve any outlier.")
if __name__ == "__main__":
    main()

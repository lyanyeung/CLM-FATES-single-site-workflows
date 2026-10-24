#!/usr/bin/env python3
"""Stage61b: reproducible, strictly read-only P1 source-evidence summary.

Join Stage60's largest_step_timestamp to Stage61's source evidence using
(site, episode_id). This script never creates reports or modifies forcing.
All source/clock comparisons remain provisional.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

N_EXPECTED = 96

def rows(path, required):
    if not path.is_file():
        raise RuntimeError("Missing required input: " + str(path))
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        if len(cols) != len(set(cols)):
            raise RuntimeError("Duplicate CSV column name: " + str(path))
        missing = set(required) - set(cols)
        if missing:
            raise RuntimeError(str(path) + ": missing fields " + str(sorted(missing)))
        return list(reader)

def finite(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def key(row):
    return row["site"], row["episode_id"]

def data(stage60, stage61):
    p60 = stage60 / "prioritized_temperature_episodes.csv"
    p61 = stage61 / "P1_episode_source_evidence.csv"
    r60 = rows(p60, {"site", "episode_id", "priority", "largest_step_timestamp",
                     "max_abs_step_C", "start_time"})
    r61 = rows(p61, {"site", "episode_id", "source_evidence",
                     "candidate_delta30_C", "FLUXMET_delta30_C",
                     "ERA5_delta30_C", "FLUXMET_TA_QC", "provisional_lag_status",
                     "science_decision", "step_agrees_with_FLUXMET",
                     "step_agrees_with_ERA5", "source_stamp_used"})
    p1 = [row for row in r60 if row["priority"] == "P1_BATCH_REVIEW"]
    if len(p1) != N_EXPECTED or len(r61) != N_EXPECTED:
        raise RuntimeError("Unexpected P1 row counts: Stage60="
                           + str(len(p1)) + " Stage61=" + str(len(r61)))
    index = {}
    for row in p1:
        k = key(row)
        if k in index:
            raise RuntimeError("Duplicate Stage60 episode: " + str(k))
        index[k] = row
    seen = set()
    merged = []
    for row in r61:
        k = key(row)
        if k in seen:
            raise RuntimeError("Duplicate Stage61 episode: " + str(k))
        seen.add(k)
        other = index.get(k)
        if other is None:
            raise RuntimeError("Stage61 episode missing from Stage60: " + str(k))
        item = dict(row)
        item["largest_step_timestamp"] = other["largest_step_timestamp"]
        item["max_abs_step_C"] = other["max_abs_step_C"]
        item["episode_start"] = other["start_time"]
        merged.append(item)
    if set(index) != seen:
        raise RuntimeError("Stage60/Stage61 P1 episode sets differ")

    with (stage60 / "manifest.json").open(encoding="utf-8") as f:
        manifest60 = json.load(f)
    with (stage61 / "manifest.json").open(encoding="utf-8") as f:
        manifest61 = json.load(f)
    if manifest60.get("stage") != 60 or manifest60.get("grouped_episodes") != 280:
        raise RuntimeError("Unexpected Stage60 manifest")
    if manifest61.get("stage") != 61 or manifest61.get("P1_event_groups") != 96:
        raise RuntimeError("Unexpected Stage61 manifest")
    return merged, manifest61

def present(events, manifest):
    print("=" * 88)
    print("STAGE61B P1 SOURCE-EVIDENCE SUMMARY | STRICTLY READ ONLY")
    print("=" * 88)
    print("P1 episode groups:", len(events))
    counts = Counter(row["source_evidence"] for row in events)
    print("\n=== 1. EVIDENCE CATEGORIES ===")
    for group, n in counts.most_common():
        print(f"{group:57s} {n:3d}")

    print("\n=== 2. EVIDENCE BY SITE ===")
    by_site = defaultdict(list)
    for row in events:
        by_site[row["site"]].append(row)
    for site, items in sorted(by_site.items()):
        print(f"\n{site}: {len(items)} P1 episode groups")
        for group, n in Counter(x["source_evidence"] for x in items).most_common():
            print(f"  {group}: {n}")

    print("\n=== 3. CLOCK ALIGNMENT STATUS ===")
    for group, n in Counter(x["provisional_lag_status"] for x in events).most_common():
        print(f"{group}: {n}")

    print("\n=== 4. FLUXMET QC DISTRIBUTION AT LARGEST STEP ===")
    for qc, n in Counter((x["FLUXMET_TA_QC"].strip() or "MISSING") for x in events).most_common():
        print(f"QC={qc}: {n}")

    print("\n=== 5. SOURCE STEP AGREEMENT (PROVISIONAL) ===")
    for variable in ("step_agrees_with_FLUXMET", "step_agrees_with_ERA5"):
        print(variable)
        for state, n in Counter(x[variable] for x in events).most_common():
            print(f"  {state or 'UNSPECIFIED'}: {n}")

    print("\n=== 6. TOP EVENTS BY EVIDENCE CATEGORY ===")
    for group, n in counts.most_common():
        print(f"\nCATEGORY: {group} ({n})")
        matches = sorted(
            (r for r in events if r["source_evidence"] == group),
            key=lambda r: abs(finite(r["candidate_delta30_C"]) or 0),
            reverse=True
        )
        for r in matches[:5]:
            print(
                f"  {r['site']:7s} {r['largest_step_timestamp']} "
                f"episode={r['episode_id']} "
                f"candidate_dT={r['candidate_delta30_C'] or 'NA'} "
                f"FLUXMET_dT={r['FLUXMET_delta30_C'] or 'NA'} "
                f"ERA5_dT={r['ERA5_delta30_C'] or 'NA'} "
                f"QC={r['FLUXMET_TA_QC'] or 'NA'}"
            )

    print("\n=== 7. REPORT MANIFEST SAFETY GATES ===")
    for label in ("P1_event_groups", "auto_repair", "science_approved",
                  "source_time_alignment_validated"):
        print(f"{label}: {manifest.get(label)}")
    print("\nREAD ONLY COMPLETE - NO FORCING OR SOURCE WRITES")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage60-dir", type=Path, required=True)
    parser.add_argument("--stage61-dir", type=Path, required=True)
    args = parser.parse_args()
    events, manifest = data(args.stage60_dir, args.stage61_dir)
    present(events, manifest)

if __name__ == "__main__":
    main()

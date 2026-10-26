#!/usr/bin/env python3
"""Batch02 Stage89: immediate decision-ready terminal table from Stage88.

READ ONLY. Exact source SHA checks. Prints 24 original source-QC0
changed-variable records and groups 274 original non-QC0 Ho1 temperatures
into consecutive native half-hour episodes, preserving all original QC
and ERA temperatures. Does not modify source / candidate / model / Slurm.
"""
import argparse
import csv
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

REPORT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage88_Batch02_exact_manual_science_review_20261026T004817Z_d9022864")
EDIT = "24_original_QC0_modified_variable_records_REVIEW.csv"
HOLD = "274_Ho1_2000_nonQC0_temperature_neighbor_context_REVIEW.csv"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def read(path):
    with path.open(newline="", encoding="utf8") as fh:
        return list(csv.DictReader(fh))

def val(r, field):
    try:
        return float(r[field])
    except (ValueError, TypeError, KeyError):
        return float("nan")

def timestamp(row):
    return datetime.strptime(row["tower_local_start"], "%Y%m%d%H%M")

def preflight():
    m = json.loads((REPORT / "review_summary.json").read_text())
    for name in (EDIT, HOLD):
        if name not in m.get("output_sha256", {}):
            raise ValueError("Missing exact Stage88 SHA in manifest: " + name)
        if not (REPORT / name).is_file() or sha(REPORT / name) != m["output_sha256"][name]:
            raise ValueError("Stage88 source SHA mismatch: " + name)
    edits, rows = read(REPORT / EDIT), read(REPORT / HOLD)
    if len(edits) != 24 or len(rows) != 274:
        raise ValueError("Stage88 row counts changed")
    expected = {"US-BZS": 1, "US-CMW": 2, "US-Ha1": 2, "US-Ho2": 19, "US-Ho3": 0}
    got = Counter(r["site"] for r in edits)
    if any(got[s] != n for s, n in expected.items()) or set(got) - set(expected):
        raise ValueError("Stage88 exact site-QC0 edit population changed")
    for r in rows:
        if val(r, "native_TA_F_original_QC") == 0:
            raise ValueError("Ho1 non-QC0 source accidentally classified as measured QC0")
        if r["review_status"] != "ORIGINAL_NON_QC0_GAPFILLED_T_SOURCE_POLICY_UNAPPROVED":
            raise ValueError("Ho1 source QC policy already changed unexpectedly")
    rows.sort(key=timestamp)
    times = [timestamp(r) for r in rows]
    if len(set(times)) != len(times):
        raise ValueError("Duplicate Ho1 native timestamp")
    return edits, rows

def periods(rows):
    groups, current = [], []
    for r in rows:
        if current and timestamp(r) - timestamp(current[-1]) != timedelta(minutes=30):
            groups.append(current)
            current = []
        current.append(r)
    if current:
        groups.append(current)
    return groups

def fmt(x):
    return "" if x != x else f"{x:.2f}"

def print_edits(edits):
    print("\n=== A: ALL 24 ORIGINAL QC0 MODIFIED VARIABLE RECORDS ===")
    print("Site | time | variable | ORIGINAL TOWER | ERA reference | candidate final | final source | reason")
    for r in sorted(edits, key=lambda r: (r["site"], r["time"], r["variable"])):
        print(" | ".join(str(r.get(k, "")) for k in (
            "site", "time", "variable", "original_value", "era_reference",
            "final_value", "final_source", "reason")))
    print("A: exactly 24 candidate changes only; science NOT approved")

def print_periods(rows, show_all=False):
    groups = periods(rows)
    counts = Counter(str(r["native_TA_F_original_QC"]) for r in rows)
    print("\n=== B: 274 Ho1 2000 ORIGINAL NON-QC0 TA_F HALF-HOURS ===")
    print("QC label counts:", dict(sorted(counts.items())))
    print("Consecutive 30-min episodes:", len(groups))
    print("Episode | first | last | HH | QC labels | T original range C | ERA_T range C | max abs(T-ERA) C | previous/next measured QC0 T C | nearest QC0 gaps min")
    for k, gp in enumerate(groups, 1):
        ts = [val(x, "native_TA_F_original_preserved_C") for x in gp]
        era = [val(x, "native_T_ERA") for x in gp]
        good_t = [x for x in ts if x == x]
        good_era = [x for x in era if x == x]
        diffs = [abs(a-b) for a,b in zip(ts,era) if a == a and b == b]
        left,right = gp[0],gp[-1]
        t_range = (f"{min(good_t):.2f}..{max(good_t):.2f}" if good_t else "NONE")
        e_range = (f"{min(good_era):.2f}..{max(good_era):.2f}" if good_era else "NONE")
        labels = ",".join(sorted({str(x["native_TA_F_original_QC"]) for x in gp}))
        context = (f"{left.get('prev_nearest_original_QC0_T_C','')}/"
                   f"{right.get('next_nearest_original_QC0_T_C','')}")
        gaps = (f"{left.get('prev_QC0_gap_minutes','')}/"
                f"{right.get('next_QC0_gap_minutes','')}")
        print(" | ".join(map(str, (k, left["tower_local_start"],
            right["tower_local_start"], len(gp), labels, t_range,e_range,
            fmt(max(diffs)) if diffs else "NONE",context,gaps))))
    print("B: episode diagnostics only; gapfilled QC1/QC2 never relabeled tower-measured")
    if show_all:
        print("\n=== EVERY 274 ORIGINAL SOURCE ROW (no changes) ===")
        print("time | QC | original TA_F C | ERA_T C | prev QC0 T C | next QC0 T C | preceding/following QC0 gaps min")
        for r in rows:
            print(" | ".join(str(r.get(k, "")) for k in (
                "tower_local_start","native_TA_F_original_QC",
                "native_TA_F_original_preserved_C","native_T_ERA",
                "prev_nearest_original_QC0_T_C","next_nearest_original_QC0_T_C",
                "prev_QC0_gap_minutes","next_QC0_gap_minutes")))
    return len(groups)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--full-274",action="store_true",help="Print every source QC!=0 Ho1 row after the episode summary")
    args = p.parse_args()
    if args.self_test:
        rows = [{"tower_local_start":x} for x in ("200001010000","200001010030","200001010130")]
        assert [len(g) for g in periods(rows)] == [2,1]
        assert len(rows)==3
        print("STAGE89 SELF-TEST PASS | consecutive native 30min grouping; no writes")
        return
    edits,rows=preflight()
    print("STAGE89 Stage88 original review source SHA VERIFIED | 24 QC0 edits, 274 Ho1 nonQC0 T")
    print_edits(edits)
    n=print_periods(rows,show_all=args.full_274)
    print("\nSTAGE89 REVIEW TABLES PASS | Ho1 episodes",n,"| total Ho1 records 274 | zero source/model writes")
    print("Decision pending: quality-coded non-QC0 original Ho1 TA_F acceptance AND exact original QC0 changed-variable approvals.")
    print("DO NOT re-review approved Ho1 17294 QC0 tower T, 1068 humidity transfers, 32 retained VPD.")
if __name__ == "__main__":
    main()

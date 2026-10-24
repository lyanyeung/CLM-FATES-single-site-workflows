#!/usr/bin/env python3
"""Stage58: pinned, READ-ONLY Batch01 forcing candidate inventory and audit.

The ten selected inputs are REVIEW CANDIDATES, never production approval.
No forcing, source, CIME, surface, DATM, PFT, Slurm or ledger writes.
Use --check for existence and --audit for SHA256, NOLEAP, physics and version diffs.
Python standard library only. Writes nothing (redirect stdout explicitly if desired).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from itertools import zip_longest
from pathlib import Path

DEFAULT_EXPERIMENT = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10"
)
OLD = "qcv5_trial_20261021T232839Z"
S51 = "stage51_scoped_era_rh7_candidate"
S54 = "stage54_era_vapour_2_candidate"
BAR = "usbar_scoped_trial_20261021T234357Z"
SITES = (
    ("BR-Ma2", 1999, 2016, OLD, "processed_v5"),
    ("CA-Ca3", 2001, 2024, OLD, "processed_v5"),
    ("CA-Cbo", 1996, 2024, OLD, "processed_v5"),
    ("CA-LP1", 2007, 2024, S51, "processed_v6_era_rh7"),
    ("CA-Man", 1994, 2008, S54, "processed_v7_era_vapour2"),
    ("CA-TP1", 2002, 2023, OLD, "processed_v5"),
    ("CA-TP3", 2002, 2023, OLD, "processed_v5"),
    ("CA-TP4", 2002, 2023, OLD, "processed_v5"),
    ("US-Aud", 2002, 2024, OLD, "processed_v5"),
    ("US-Bar", 2004, 2023, BAR, "processed_v5"),
)
COLS = ("time", "TBOT", "QBOT", "PSRF", "FSDS", "FLDS",
        "WIND", "PRECTmms", "TA_USE", "VPD_USE")
BOUNDS = {
    "TBOT": (180, 340), "QBOT": (0, 0.08), "PSRF": (49000, 111000),
    "FSDS": (0, 1600), "FLDS": (0, 800), "WIND": (0, 75),
    "PRECTmms": (0, 300 / 1800),
}
EXPECTED_HASHES = {
    ("CA-Man", "stage51"):
        "c87c8d44381e29f17bf3ccee074afb27ff526b4dd5b92b951e0a990ba4a5ee3e",
    ("CA-Man", "selected"):
        "fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705",
}
HOLD = "2007-07-03 20:00:00"
TWO_EDITS = {"1999-05-09 13:00:00", "2005-05-09 14:00:00"}


def relpath(site, first, last, root, ver):
    return (Path(root) / site / "forcing" / ver /
            f"{site}_CLM_forcing_{first}_{last}.csv")


def file_list():
    result = {}
    for site, first, last, root, ver in SITES:
        result[(site, "selected")] = relpath(site, first, last, root, ver)
    result[("CA-LP1", "qcv5")] = relpath("CA-LP1", 2007, 2024, OLD, "processed_v5")
    result[("CA-Man", "qcv5")] = relpath("CA-Man", 1994, 2008, OLD, "processed_v5")
    result[("CA-Man", "stage51")] = relpath(
        "CA-Man", 1994, 2008, S51, "processed_v6_era_rh7"
    )
    return result


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_time(value):
    return datetime.fromisoformat(value.strip().replace("Z", ""))


def number(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def following(t):
    new = t + timedelta(minutes=30)
    if new.month == 2 and new.day == 29:
        return new.replace(month=3, day=1)
    return new


def scan(path, first, last):
    counts = Counter()
    samples = {}
    expected = datetime(first, 1, 1)
    previous = None
    previous_t = None
    first_time = last_time = None
    with path.open(newline="", encoding="utf-8-sig") as src:
        reader = csv.DictReader(src)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not set(COLS).issubset(fields):
            raise ValueError("Required columns missing or duplicated: " + str(fields))
        for row in reader:
            counts["rows"] += 1
            stamp = row.get("time") or ""
            try:
                t = parse_time(stamp)
            except (TypeError, ValueError):
                t = None
            if first_time is None:
                first_time = stamp
            last_time = stamp
            if t != expected:
                counts["bad_calendar"] += 1
                samples.setdefault("bad_calendar", stamp)
            expected = following(expected)
            if t is None:
                counts["unparseable_time"] += 1
            elif t.month == 2 and t.day == 29:
                counts["leap_day"] += 1
            vals = {name: number(row.get(name)) for name in COLS if name != "time"}
            invalid = [k for k, v in vals.items() if v is None]
            if invalid:
                counts["nonfinite_rows"] += 1
                samples.setdefault("nonfinite_rows", f"{stamp}: {invalid}")
                previous = previous_t = None
                continue
            for col, (lo, hi) in BOUNDS.items():
                if not lo <= vals[col] <= hi:
                    counts["out_of_range_" + col] += 1
                    samples.setdefault("out_of_range_" + col, stamp)
            temp = vals["TBOT"] - 273.15
            if abs(temp - vals["TA_USE"]) > 0.02:
                counts["tbot_ta_disagreement"] += 1
            p, q = vals["PSRF"], vals["QBOT"]
            try:
                es = 6.112 * math.exp(17.67 * temp / (temp + 243.5))
                e = q * (p / 100.0) / (0.622 + 0.378 * q)
                rh = 100.0 * e / es
                vpd = es - e
            except (OverflowError, ZeroDivisionError):
                counts["invalid_humidity"] += 1
                previous = previous_t = None
                continue
            if not math.isfinite(rh) or not math.isfinite(vpd):
                counts["invalid_humidity"] += 1
            elif rh <= 0:
                counts["rh_nonpositive"] += 1
            elif rh < 1:
                counts["rh_below1"] += 1
            elif rh > 100.1:
                counts["rh_above100"] += 1
            if abs(vals["VPD_USE"] - vpd) > 0.2:
                counts["vpd_closure_warning"] += 1
            if previous is not None and t is not None and previous_t is not None:
                if t - previous_t == timedelta(minutes=30) and abs(temp - previous) > 10:
                    counts["ta_step_over10C"] += 1
                    samples.setdefault("ta_step_over10C", stamp)
            previous, previous_t = temp, t
    n_expected = (last - first + 1) * 365 * 48
    if counts["rows"] != n_expected:
        counts["unexpected_row_count"] = 1
    return {
        "rows": counts["rows"], "expected_rows": n_expected,
        "first_time": first_time, "last_time": last_time,
        "flags": dict(counts), "first_examples": samples,
        "structural_gate": ("FAIL" if (
            counts["unexpected_row_count"] or counts["bad_calendar"] or
            counts["nonfinite_rows"] or counts["invalid_humidity"] or
            counts["rh_nonpositive"] or counts["rh_above100"] or
            any(counts["out_of_range_" + name] for name in BOUNDS)
        ) else "PASS_REVIEW_ONLY"),
        "science_gate": "HOLD_NOT_APPROVED",
    }


def compare_versions(left, right):
    row_changes = 0
    field_changes = Counter()
    changed = []
    first_examples = []
    with left.open(newline="", encoding="utf-8-sig") as fa, right.open(
        newline="", encoding="utf-8-sig"
    ) as fb:
        a, b = csv.DictReader(fa), csv.DictReader(fb)
        if a.fieldnames != b.fieldnames:
            return {"comparable": False, "reason": "CSV_COLUMN_MISMATCH"}
        for old, new in zip_longest(a, b):
            if old is None or new is None or old.get("time") != new.get("time"):
                return {"comparable": False, "reason": "ROW_OR_TIME_MISMATCH"}
            diffs = []
            for col in a.fieldnames:
                if col == "time":
                    continue
                x, y = old.get(col), new.get(col)
                if x == y:
                    continue
                vx, vy = number(x), number(y)
                if vx is not None and vy is not None and math.isclose(
                    vx, vy, rel_tol=1e-8, abs_tol=1e-10
                ):
                    continue
                diffs.append(col)
                field_changes[col] += 1
            if diffs:
                row_changes += 1
                if len(first_examples) < 12:
                    first_examples.append({"time": old["time"], "columns": diffs})
                changed.append((old["time"], tuple(sorted(diffs))))
    return {
        "comparable": True, "materially_changed_rows": row_changes,
        "material_field_changes": dict(field_changes),
        "first_examples": first_examples,
        "changed_entries": changed if row_changes <= 20 else [],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment-root", type=Path, default=DEFAULT_EXPERIMENT)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    root = args.experiment_root.resolve(strict=True)
    paths = file_list()
    print("STAGE58 BATCH01 PINNED FORCING AUDIT | READ ONLY")
    print("Experiment:", root)
    print("Pinned files:", len(paths), "selected stations:", len(SITES))
    missing = []
    for (site, version), relative in paths.items():
        path = root / relative
        if not path.is_file() or not path.resolve().is_relative_to(root):
            missing.append(str(relative))
        else:
            print(f"FOUND {site:8s} {version:8s} {path.stat().st_size} bytes {relative}")
    risk = root / "stage56_batch01_met_triage/CA-Man_2007_accepted_risk.json"
    if not risk.is_file():
        missing.append(str(risk))
    if missing:
        raise SystemExit("STOP missing/untrusted required file(s):\n" + "\n".join(missing))
    if args.check:
        print("CHECK PASS: exact 13 inputs and risk ledger exist. Nothing written.")
        return
    results = {}
    for (site, version), relative in paths.items():
        digest = sha256(root / relative)
        expected_hash = EXPECTED_HASHES.get((site, version))
        if expected_hash is not None and digest != expected_hash:
            raise SystemExit(f"STOP SHA256 mismatch {site}/{version}: {digest}")
        results[f"{site}/{version}"] = {
            "path": str(relative), "sha256": digest,
            "bytes": (root / relative).stat().st_size,
            "sha256_matches_known": expected_hash is not None,
        }
    ledger = json.loads(risk.read_text(encoding="utf-8"))
    if not (
        ledger.get("site") == "CA-Man" and ledger.get("timestamp") == HOLD and
        ledger.get("decision") == "ACCEPTED_RISK" and
        ledger.get("candidate_sha256") == EXPECTED_HASHES[("CA-Man", "selected")]
    ):
        raise SystemExit("STOP Stage56 risk ledger unexpected; no approval inferred")
    summaries = {}
    for site, first, last, _, _ in SITES:
        selected = root / paths[(site, "selected")]
        stats = scan(selected, first, last)
        summaries[site] = stats
        f = stats["flags"]
        print(f"SCAN {site:8s} {stats['structural_gate']:16s} "
              f"rows={stats['rows']}/{stats['expected_rows']} "
              f"rh_lt1={f.get('rh_below1',0)} TA_gt10C={f.get('ta_step_over10C',0)} "
              f"VPD_closure={f.get('vpd_closure_warning',0)} "
              f"calendar={f.get('bad_calendar',0)}")
    comparisons = {}
    for label, a, b in (
        ("CA-LP1_qcv5_vs_stage51", ("CA-LP1", "qcv5"), ("CA-LP1", "selected")),
        ("CA-Man_qcv5_vs_stage51", ("CA-Man", "qcv5"), ("CA-Man", "stage51")),
        ("CA-Man_stage51_vs_stage54", ("CA-Man", "stage51"), ("CA-Man", "selected")),
    ):
        result = compare_versions(root / paths[a], root / paths[b])
        comparisons[label] = result
        print("COMPARE", label, result.get("materially_changed_rows"),
              result.get("material_field_changes"), result.get("reason", ""))
    strict = comparisons["CA-Man_stage51_vs_stage54"]
    expected_edits = {(t, ("QBOT", "VPD_USE")) for t in TWO_EDITS}
    if not strict["comparable"] or set(strict["changed_entries"]) != expected_edits:
        raise SystemExit("STOP: Stage54 does not match exactly two expected scoped edits")
    if any(s["structural_gate"] != "PASS_REVIEW_ONLY" for s in summaries.values()):
        print("NUMERICAL / CHRONOLOGY GATE: FAIL; inspect flagged sites.")
    else:
        print("NUMERICAL / CHRONOLOGY GATE: PASS (science HOLD).")
    report = {
        "audit": "Stage58", "mode": "READ_ONLY", "source": "PINNED_CANDIDATES",
        "selected_versions": results, "selected_scans": summaries,
        "version_comparisons": comparisons,
        "stage56_risk_ledger": str(risk.relative_to(root)),
        "stage56_risk_ledger_sha256": sha256(risk),
        "remaining_gates": [
            "Scientific review of RH and TA events and official QC0 changes",
            "Unresolved source-to-TA_F/ZBOT mapping and date policy",
            "EC tower footprint, active FATES PFT and host landunit approval",
            "No validated final DATM or submitted production spinup",
        ],
        "production_approved": False,
    }
    print("BEGIN_STAGE58_JSON")
    print(json.dumps(report, sort_keys=True, indent=2))
    print("END_STAGE58_JSON")
    print("READ ONLY: no file created, modified or deleted; no jobs submitted.")


if __name__ == "__main__":
    main()

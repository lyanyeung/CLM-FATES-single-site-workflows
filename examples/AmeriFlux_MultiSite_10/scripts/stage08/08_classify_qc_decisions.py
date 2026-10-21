#!/usr/bin/env python3
"""Stage 08: read-only event-level QC decision ledger for AmeriFlux Batch 01.

Consumes Stage 07 paired FLUXMET/ERA5 events; it never treats a clean ERA5
counterpart as permission to replace tower observations. Output comprises
review priorities, source-QC provenance, paired source/event counts, and
2004/2016 same-calendar-time patterns. No forcing/surface/model edits.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
MET = ("TA", "VPD", "PA", "SW_IN", "LW_IN", "WS", "P")
HUMIDITY = {"EA_NONPOSITIVE", "SUPERSATURATION",
            "Q_SPECIFIC_INVALID", "HUMIDITY_UNCOMPUTABLE"}
CLASS_NAMES = {
    "SAME_PHYSICAL_FLAG_IN_BOTH": "SHARED_PHYSICAL_REVIEW",
    "COUNTERPART_PASSES_SAME_CHECKS": "SOURCE_SPECIFIC_REVIEW",
    "COUNTERPART_TIMESTAMP_MISSING": "COUNTERPART_MISSING",
    "COUNTERPART_REQUIRED_VALUE_MISSING": "COUNTERPART_VALUE_MISSING",
    "COUNTERPART_HUMIDITY_INPUT_MISSING": "COUNTERPART_HUMIDITY_MISSING",
    "DIFFERENT_VARIABLE_RANGE_FLAG_IN_COUNTERPART": "DIFFERENT_RANGE_ISSUES",
    "BOTH_HUMIDITY_PHYSICALLY_FLAGGED": "BOTH_HUMIDITY_REVIEW",
}


def rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(path, data, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)


def number(v):
    try:
        n = float(v)
    except (ValueError, TypeError):
        return None
    return n if math.isfinite(n) else None


def flags(v):
    return set(x for x in (v or "").split("|") if x)


def kind(f):
    hum = bool(f & HUMIDITY)
    rng = any(x.endswith("_RANGE") for x in f)
    if hum and rng:
        return "HUMIDITY_AND_RANGE"
    if hum:
        return "HUMIDITY"
    if rng:
        return "RANGE"
    return "OTHER"


def qc_labels(row, f):
    affected = set()
    if f & HUMIDITY:
        affected.update(("TA", "VPD", "PA"))
    for v in MET:
        if v + "_RANGE" in f:
            affected.add(v)
    return ";".join(v + ":" + (
        str(number(row.get("source_" + v + "_QC")))
        if number(row.get("source_" + v + "_QC")) is not None else "NA")
        for v in sorted(affected))


def priority(row, f, counterpart_class):
    if counterpart_class in ("SHARED_PHYSICAL_REVIEW", "BOTH_HUMIDITY_REVIEW"):
        return "P1_SHARED_ANOMALY"
    if counterpart_class.startswith("COUNTERPART_MISSING") or counterpart_class == "COUNTERPART_VALUE_MISSING":
        return "P1_MISSING_COMPARATOR"
    rh = number(row.get("source_RH_pct"))
    if "EA_NONPOSITIVE" in f or "Q_SPECIFIC_INVALID" in f:
        return "P1_HUMIDITY_PHYSICAL"
    if rh is not None and rh > 105:
        return "P1_SUPERSAT_GT105"
    if any(v + "_RANGE" in f for v in ("TA", "PA", "LW_IN")):
        return "P1_HARD_RANGE"
    if "SUPERSATURATION" in f and rh is not None and 101 < rh <= 105:
        return "P2_SUPERSAT_101_105"
    return "P2_REVIEW_UNCLASSIFIED"


def newest(report_root, explicit):
    if explicit:
        p = explicit.expanduser()
    else:
        dirs = sorted(x for x in report_root.glob("stage07_counterpart_*")
                      if (x / "paired_anomaly_events.csv").is_file())
        if not dirs:
            raise RuntimeError("No Stage07 paired event report found")
        p = dirs[-1]
    if not (p / "paired_anomaly_events.csv").is_file():
        raise RuntimeError("Missing Stage07 events in " + str(p))
    return p


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report-root", type=Path, default=ROOT)
    p.add_argument("--stage07-dir", type=Path)
    p.add_argument("--max-examples", type=int, default=15)
    args = p.parse_args()
    if args.max_examples < 0:
        p.error("--max-examples must be >=0")
    input_dir = newest(args.report_root, args.stage07_dir)
    events = rows(input_dir / "paired_anomaly_events.csv")
    if not events:
        raise RuntimeError("Stage07 report has no events")
    required = {"site", "timestamp", "source_flagged", "flagged_categories",
                "counterpart_categories", "comparison_class"}
    if not required.issubset(events[0]):
        raise RuntimeError("Stage07 CSV columns missing: " + str(required-set(events[0])))
    keys = set()
    ledger = []
    classes = Counter()
    priorities = Counter()
    sites = defaultdict(Counter)
    stamps = defaultdict(set)
    origin = defaultdict(set)
    repeated = defaultdict(set)
    qc_counts = defaultdict(Counter)
    for row in events:
        site, stamp, source = row["site"], row["timestamp"], row["source_flagged"]
        unique_key = (site, stamp, source)
        if unique_key in keys:
            raise RuntimeError("Duplicate Stage07 event for " + str(unique_key))
        keys.add(unique_key)
        f = flags(row["flagged_categories"])
        other = flags(row["counterpart_categories"])
        comp = CLASS_NAMES.get(row["comparison_class"], "UNCLASSIFIED_COMPARISON")
        category = kind(f)
        prio = priority(row, f, comp)
        qcs = qc_labels(row, f)
        record = {
            "site": site, "timestamp_local": stamp, "flagged_source": source,
            "comparison": comp, "priority": prio,
            "physical_group": category,
            "source_flags": "|".join(sorted(f)),
            "counterpart_flags": "|".join(sorted(other)),
            "source_RH_pct": row.get("source_RH_pct", ""),
            "counterpart_RH_pct": row.get("other_RH_pct", ""),
            "affected_variable_QC": qcs,
            "decision": "HOLD_NO_AUTOMATIC_REPLACEMENT",
            "independent_evidence": "NOT_YET_ESTABLISHED",
        }
        ledger.append(record)
        classes[comp] += 1
        priorities[prio] += 1
        sites[site]["events"] += 1
        sites[site][source] += 1
        sites[site][prio] += 1
        stamps[site].add(stamp)
        origin[(site, stamp)].add(source)
        if stamp[:4] in ("2004", "2016"):
            repeated[(site, source, stamp[5:])].add(stamp[:4])
        if qcs:
            qc_counts[(site, source)][qcs] += 1

    both = sum(len(sources)==2 for sources in origin.values())
    single = sum(len(sources)==1 for sources in origin.values())
    if single + 2*both != len(ledger):
        raise RuntimeError("Event-pair accounting mismatch")
    same_clock = [
        {"site":key[0], "source":key[1],
         "month_day_local_time":key[2], "years":"2004,2016"}
        for key, years in repeated.items() if years == {"2004","2016"}
    ]
    same_clock.sort(key=lambda x:(x["site"],x["source"],x["month_day_local_time"]))
    qc_rows = [
        {"site":site,"source":source,"triggered_QC_pattern":pattern,"events":n}
        for (site,source), patterns in qc_counts.items() for pattern,n in patterns.items()
    ]
    qc_rows.sort(key=lambda x:(x["site"],x["source"],-x["events"]))
    summaries = [
        {"site":site,"flagged_event_rows":c["events"],
         "unique_site_timestamps":len(stamps[site]),
         "flagged_FLUXMET_HH":c["FLUXMET_HH"],
         "flagged_ERA5_HH":c["ERA5_HH"],
         "P1_shared":c["P1_SHARED_ANOMALY"],
         "P1_humidity":c["P1_HUMIDITY_PHYSICAL"],
         "P1_hard_range":c["P1_HARD_RANGE"]}
        for site,c in sorted(sites.items())
    ]
    out = args.report_root / ("stage08_decisions_" +
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    save(out / "review_decision_ledger.csv", ledger,
         list(ledger[0]))
    save(out / "site_priorities.csv", summaries,
         ["site","flagged_event_rows","unique_site_timestamps",
          "flagged_FLUXMET_HH","flagged_ERA5_HH","P1_shared",
          "P1_humidity","P1_hard_range"])
    save(out / "trigger_variable_qc_patterns.csv", qc_rows,
         ["site","source","triggered_QC_pattern","events"])
    save(out / "2004_2016_repeat_clock_patterns.csv", same_clock,
         ["site","source","month_day_local_time","years"])

    print("STAGE08 SUMMARY: %d flagged-source rows; %d unique site-local timestamps" %
          (len(ledger),len(origin)))
    print("  Single-source-flagged times:",single)
    print("  Both-source-flagged times:",both)
    print("  Stage07 comparison categories:",dict(classes))
    print("  Review priorities:",dict(priorities))
    print("  Same station/source calendar day+clock time in 2004 AND 2016:",
          len(same_clock))
    for site in sorted(sites):
        c = sites[site]
        print("  %-7s events=%4d unique_timestamps=%4d FLUXMET=%4d ERA5=%4d" %
              (site,c["events"],len(stamps[site]),
               c["FLUXMET_HH"],c["ERA5_HH"]))
    if same_clock:
        print("  Example repeated local-clock patterns (NOT proof of a common fault):")
        for rec in same_clock[:args.max_examples]:
            print("    %s %s %s" %
                  (rec["site"],rec["source"],rec["month_day_local_time"]))
    print("REPORT DIR:",out)
    print("All decisions remain HOLD. No automatic replacement or changes to inputs.")
    print("NOTE: QC=2 represents source provenance where supplied, not a failure verdict.")
    print("NOTE: equal local clock time across years/sites is not necessarily equal UTC.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

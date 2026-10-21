#!/usr/bin/env python3
"""Stage 07: compare flagged AmeriFlux FLUXMET/ERA5 events at identical timestamps.

Reads the Stage06 event ledger and the exact pinned original FLUXMET_HH and
ERA5_HH CSVs. Crucially, the counterpart may be unflagged and must be fetched
from its source file; comparing Stage06 flagged rows alone would be biased.

The comparison is DIAGNOSTIC ONLY: FLUXNET ERA5_HH and *_ERA values are not
guaranteed independent validation, nor an approved replacement for observations.
Does not modify source data, surface, derived forcing, DATM or Slurm jobs.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
HERE = Path(__file__).resolve().parents[2]
KINDS = {"FLUXMET_HH": "_F", "ERA5_HH": "_ERA"}
VARS = ("TA", "VPD", "PA", "SW_IN", "LW_IN", "WS", "P")
BOUNDS = {
    "TA":(-80, 65), "VPD":(-.1, 125), "PA":(50, 110),
    "SW_IN":(-5, 1600), "LW_IN":(60, 800),
    "WS":(-.1, 75), "P":(-.001, 300),
}


def csv_rows(path, delim=","):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delim))


def numeric(v):
    try:
        z = float(v)
    except (ValueError, TypeError):
        return None
    return z if math.isfinite(z) and z > -9990 else None


def zip_source(site, package, kind, root):
    raw = root / site / "forcing" / "raw" / package
    choices = sorted(p for p in raw.glob("*.csv") if kind in p.name.upper())
    if len(choices) != 1:
        raise RuntimeError("%s %s expected 1 source CSV, got %d" %
                           (site, kind, len(choices)))
    return choices[0]


def latest_report(report_root, given):
    if given:
        path = given
    else:
        choices = sorted(p for p in report_root.glob("stage06_anomalies_*")
                         if (p / "flagged_source_timestamps.csv").is_file())
        if not choices:
            raise RuntimeError("Stage06 event report not found under " + str(report_root))
        path = choices[-1]
    if not (path / "flagged_source_timestamps.csv").is_file():
        raise RuntimeError("Stage06 event CSV missing in " + str(path))
    return path


def normalize_event_stamp(stamp):
    return datetime.strptime(stamp, "%Y-%m-%d %H:%M").strftime("%Y%m%d%H%M")


def obtain_matching_records(path, kind, selected, chunksize):
    """Read only requested rows while streaming a full source file once."""
    suffix = KINDS[kind]
    header = pd.read_csv(path, nrows=0).columns.tolist()
    needed = ["TIMESTAMP_START"] + [v + suffix for v in VARS]
    missing = [k for k in needed if k not in header]
    if missing:
        raise RuntimeError(str(path) + " missing columns: " + ",".join(missing))
    qc = [v + suffix + "_QC" for v in VARS
          if v + suffix + "_QC" in header]
    matched = {}
    for chunk in pd.read_csv(path, usecols=needed + qc,
                             dtype={"TIMESTAMP_START":"string"},
                             chunksize=chunksize, low_memory=False):
        stamps = chunk["TIMESTAMP_START"].str.strip().str.replace(
            r"\.0$", "", regex=True)
        hits = chunk.loc[stamps.isin(selected)].copy()
        if hits.empty:
            continue
        hits["_key"] = stamps.loc[hits.index]
        for rec in hits.to_dict("records"):
            key = rec.pop("_key")
            rec.pop("TIMESTAMP_START", None)
            if key in matched:
                raise RuntimeError("Duplicate matched source timestamp " + str(path) + ":" + key)
            values = {v: numeric(rec.get(v + suffix)) for v in VARS}
            qc_values = {v: numeric(rec.get(v + suffix + "_QC")) for v in VARS}
            matched[key] = (values, qc_values)
    return matched


def source_physics(values):
    flags = set()
    for v, (lo, hi) in BOUNDS.items():
        z = values.get(v)
        if z is not None and (z < lo or z > hi):
            flags.add(v + "_RANGE")
    t, vpd, pa = values.get("TA"), values.get("VPD"), values.get("PA")
    rh = None
    if None not in (t, vpd, pa):
        try:
            es = 611.2 * math.exp(max(-40, min(40, 17.67*t/(t+243.5))))
            ea = es - 100*vpd
            p = 1000*pa
            q = .622*ea/(p-.378*ea)
            rh = 100*ea/es
            if ea <= 0: flags.add("EA_NONPOSITIVE")
            if ea > 1.01*es: flags.add("SUPERSATURATION")
            if not math.isfinite(q) or q < 0 or q > .08:
                flags.add("Q_SPECIFIC_INVALID")
        except (ZeroDivisionError, OverflowError, ValueError):
            flags.add("HUMIDITY_UNCOMPUTABLE")
    else:
        flags.add("HUMIDITY_INPUT_MISSING")
    return flags, rh


def issue_family(flags):
    return {x for x in flags if x.endswith("_RANGE") or x in {
        "EA_NONPOSITIVE", "SUPERSATURATION", "Q_SPECIFIC_INVALID",
        "HUMIDITY_UNCOMPUTABLE"}}


def counterpart_status(event_flags, counterpart, other_flags):
    if counterpart is None:
        return "COUNTERPART_TIMESTAMP_MISSING"
    physical_flags = issue_family(event_flags)
    if any(counterpart[0].get(v) is None for v in VARS
           if v + "_RANGE" in physical_flags):
        return "COUNTERPART_REQUIRED_VALUE_MISSING"
    if (physical_flags & {"EA_NONPOSITIVE", "SUPERSATURATION",
                          "Q_SPECIFIC_INVALID", "HUMIDITY_UNCOMPUTABLE"}) and any(
        counterpart[0].get(v) is None for v in ("TA","VPD","PA")):
        return "COUNTERPART_HUMIDITY_INPUT_MISSING"
    if issue_family(other_flags) & physical_flags:
        return "SAME_PHYSICAL_FLAG_IN_BOTH"
    if (any(f.endswith("_RANGE") for f in physical_flags) and
            any(f.endswith("_RANGE") for f in other_flags)):
        return "DIFFERENT_VARIABLE_RANGE_FLAG_IN_COUNTERPART"
    if (physical_flags & {"EA_NONPOSITIVE", "SUPERSATURATION",
                          "Q_SPECIFIC_INVALID", "HUMIDITY_UNCOMPUTABLE"} and
            other_flags & {"EA_NONPOSITIVE", "SUPERSATURATION",
                           "Q_SPECIFIC_INVALID", "HUMIDITY_UNCOMPUTABLE"}):
        return "BOTH_HUMIDITY_PHYSICALLY_FLAGGED"
    return "COUNTERPART_PASSES_SAME_CHECKS"


def output_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--reports", type=Path, default=REPORTS)
    ap.add_argument("--stage06-dir", type=Path)
    ap.add_argument("--sites", nargs="+", help="Optional subset of site codes")
    ap.add_argument("--chunksize", type=int, default=120000)
    args = ap.parse_args()
    if args.chunksize < 1000:
        ap.error("chunksize must be >=1000")
    manifest = csv_rows(HERE / "sites.tsv", "\t")
    packages = {x["site"]: x["package"] for x in manifest}
    if len(manifest) != 10 or len(packages) != 10:
        raise RuntimeError("Manifest must contain ten distinct sites")
    if args.sites and not set(args.sites).issubset(packages):
        ap.error("Unknown site in --sites")
    wanted = set(args.sites or packages)
    report_dir = latest_report(args.reports, args.stage06_dir)
    events = [r for r in csv_rows(report_dir / "flagged_source_timestamps.csv")
              if r["site"] in wanted]
    if not events:
        raise RuntimeError("No Stage06 events found for selected sites")
    groups = defaultdict(list)
    for row in events:
        if row["source"] not in KINDS:
            raise RuntimeError("Unexpected source: " + row["source"])
        key = normalize_event_stamp(row["timestamp"])
        row["stamp_key"] = key
        groups[row["site"]].append(row)
    print("EVENTS:",len(events),"sites:",len(groups), "Stage06 source:",report_dir, flush=True)

    results = []
    comparisons = Counter()
    pair_counts = Counter()
    for site in sorted(groups):
        selected = {x["stamp_key"] for x in groups[site]}
        pairs = {}
        for kind in KINDS:
            path = zip_source(site, packages[site], kind, args.root)
            pairs[kind] = obtain_matching_records(path, kind, selected,
                                                  args.chunksize)
            print("%-7s %-11s matched=%d/%d source=%s" % (
                site, kind, len(pairs[kind]), len(selected), path), flush=True)
        for event in groups[site]:
            kind = event["source"]
            other = "ERA5_HH" if kind == "FLUXMET_HH" else "FLUXMET_HH"
            original = pairs[kind].get(event["stamp_key"])
            counterpart = pairs[other].get(event["stamp_key"])
            if original is None:
                raise RuntimeError("Stage06 event timestamp not in original %s %s %s" %
                                   (site,kind,event["timestamp"]))
            orig_flags, orig_rh = source_physics(original[0])
            other_flags, other_rh = (source_physics(counterpart[0])
                                     if counterpart else (set(),None))
            saved_flags = set(filter(None, event["flags"].split("|")))
            if orig_flags != saved_flags:
                # A source anomaly already validated by Stage06 may still differ
                # due to revised source logic or subtle floating-point thresholds.
                comparisons["STAGE06_FLAG_REPRODUCTION_MISMATCH"] += 1
            label = counterpart_status(saved_flags,counterpart,other_flags)
            comparisons[label] += 1
            pair_counts[(site,kind,label)] += 1
            row = {
                "site":site, "timestamp":event["timestamp"],
                "source_flagged":kind, "other_source":other,
                "flagged_categories":event["flags"],
                "counterpart_categories":"|".join(sorted(other_flags)),
                "comparison_class":label,
                "source_reproduced_categories":"|".join(sorted(orig_flags)),
                "source_RH_pct":orig_rh, "other_RH_pct":other_rh,
            }
            for var in VARS:
                a = original[0][var]
                b = counterpart[0][var] if counterpart else None
                row["source_"+var] = a
                row["other_"+var] = b
                row["source_"+var+"_QC"] = original[1][var]
                row["other_"+var+"_QC"] = counterpart[1][var] if counterpart else None
                row["delta_"+var] = (a-b) if a is not None and b is not None else None
            results.append(row)

    out_dir = args.reports / ("stage07_counterpart_" +
              datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out_dir.mkdir(parents=True, exist_ok=False)
    fields = list(results[0])
    output_csv(out_dir / "paired_anomaly_events.csv", results, fields)
    counts = [{"site":site,"flagged_source":kind,"comparison_class":label,"events":n}
              for (site,kind,label),n in sorted(pair_counts.items())]
    output_csv(out_dir / "paired_event_summary.csv", counts,
               ["site","flagged_source","comparison_class","events"])
    print("\\nSTAGE07 SUMMARY:",len(results),"paired source events",flush=True)
    for label, n in comparisons.most_common():
        print("  %-44s %d" % (label,n),flush=True)
    print("REPORT DIR:",out_dir,flush=True)
    print("SOURCE-PROVENANCE COMPARISON ONLY; DO NOT AUTO-REPLACE WITH ERA5.",flush=True)
    print("Same-time across stations is only same LOCAL clock, not necessarily same UTC instant.",flush=True)
    return 2 if comparisons["STAGE06_FLAG_REPRODUCTION_MISMATCH"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

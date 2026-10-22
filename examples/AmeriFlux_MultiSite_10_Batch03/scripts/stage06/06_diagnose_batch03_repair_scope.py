#!/usr/bin/env python3
"""Diagnose primary-product repair scope from the exact Stage04b/05 snapshots.

Produces evidence and review queues only. Never changes or fills forcing.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import csv as stdcsv
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

BATCH = Path(__file__).resolve().parents[2]
EXPERIMENT = "AmeriFlux_MultiSite_10_Batch03"
BOUNDS = {"TA": (-80, 65), "VPD": (-0.1, 125), "PA": (50, 110),
          "SW_IN": (-5, 1600), "LW_IN": (60, 800), "WS": (-0.1, 75), "P": (-0.001, 300)}
SOURCE_FILES = ("source_inventory.json", "physical_anomaly_records.csv",
                "annual_source_coverage_and_QC.csv", "missing_episodes.csv", "timestamp_issues.csv")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def csv(data):
    return pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False)


def number(column):
    return pd.to_numeric(column, errors="coerce").to_numpy(dtype=float)


def diagnose(frame, prefix):
    """Use exactly the previous liquid-water screen; expose each predicate."""
    values = {v: number(frame[prefix + v]) for v in BOUNDS}
    t, v, p = values["TA"], values["VPD"], values["PA"] * 1000
    testable = np.isfinite(t) & np.isfinite(v) & np.isfinite(p) & (p > 0) & (t > -150)
    with np.errstate(all="ignore"):
        es = 611.2 * np.exp(np.clip(17.67 * t / (t + 243.5), -40, 40))
        ea = es - v * 100
        denominator = p - 0.378 * ea
        rh = ea / es * 100
        q = 0.622 * ea / denominator
    causes = {}
    for key, (lo, hi) in BOUNDS.items():
        causes[key + "_BELOW_SCREEN"] = np.isfinite(values[key]) & (values[key] < lo)
        causes[key + "_ABOVE_SCREEN"] = np.isfinite(values[key]) & (values[key] > hi)
    causes.update({
        "HUM_VAPOR_NONPOSITIVE": testable & (ea <= 0),
        "HUM_RH_ABOVE_101": testable & (rh > 101),
        "HUM_DENOMINATOR_NONPOSITIVE": testable & (denominator <= 0),
        "HUM_Q_BELOW_0": testable & (q < 0),
        "HUM_Q_ABOVE_0_08": testable & (q > 0.08),
        "HUM_Q_NONFINITE": testable & ~np.isfinite(q),
    })
    humidity_bad = np.logical_or.reduce([a for k, a in causes.items() if k.startswith("HUM_")])
    flags = [set() for _ in range(len(frame))]
    for key in BOUNDS:
        bad = causes[key + "_BELOW_SCREEN"] | causes[key + "_ABOVE_SCREEN"]
        for i in np.flatnonzero(bad): flags[i].add(key + "_RANGE")
    for i in np.flatnonzero(humidity_bad): flags[i].add("HUMIDITY_INVALID")
    for limit in (1, 5, 10):
        for i in np.flatnonzero(testable & (rh > 0) & (rh < limit)):
            flags[i].add("RH_LT" + str(limit))
    return dict(values=values, causes=causes, flags=flags, testable=testable,
                humidity_bad=humidity_bad, rh=np.where(testable, rh, np.nan),
                ea=np.where(testable, ea, np.nan), q=np.where(testable, q, np.nan),
                denominator=np.where(testable, denominator, np.nan))


def priority(flags):
    if "HUMIDITY_INVALID" in flags or any(f.endswith("_RANGE") for f in flags): return "P0_NUMERICAL_SCREEN"
    for flag, rank in (("RH_LT1", "P1_RH_LT1"), ("RH_LT5", "P2_RH_1_TO5"), ("RH_LT10", "P3_RH_5_TO10")):
        if flag in flags: return rank
    raise ValueError("Unrecognized or empty event flag set: " + repr(flags))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-report", required=True, type=Path)
    parser.add_argument("--review-report", required=True, type=Path)
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--check", action="store_true",
                        help="Verify report provenance and counts without writing any files")
    args = parser.parse_args()
    source, review = args.source_report.expanduser().resolve(), args.review_report.expanduser().resolve()
    # Restrict this audit to the exact Batch03 reports; never silently borrow
    # another batch's data or use reports outside the experiment root.
    if (source.parent.name != "reports" or source.parent.parent.name != EXPERIMENT
            or review.parent != source.parent
            or not source.name.startswith("stage04b_met_")
            or not review.name.startswith("stage05_event_review_")):
        raise ValueError("Expected Stage04b and Stage05 reports from the same Batch03 reports root")
    paths = [source / f for f in SOURCE_FILES] + [review / f for f in ("review_summary.json", "paired_event_review.csv", "source_quality_summary.csv", "event_episodes.csv")]
    snapshots = {p: p.read_bytes() for p in paths}
    summary = json.loads(snapshots[review / "review_summary.json"])
    if Path(summary["source_report"]).resolve() != source:
        raise ValueError("Stage05 was made from a different Stage04b report")
    if summary["ledger_mismatches"] or summary["events"] != summary["verified_source_rows"]:
        raise ValueError("Stage05 source-row verification is incomplete")
    for name in SOURCE_FILES:
        if digest(snapshots[source / name]) != summary["input_report_sha256"][name]:
            raise ValueError("Stage04b report changed since Stage05: " + name)
    inventory = json.loads(snapshots[source / "source_inventory.json"])
    specs = {(r["site"], r["source"]): r for r in inventory["completed"]}
    sites = sorted({s for s, _ in specs})
    if inventory["failures"] or len(specs) != 20 or len(sites) != 10:
        raise ValueError("Expected complete twenty-source, ten-site inventory")
    with (BATCH / "sites.tsv").open(encoding="utf-8", newline="") as stream:
        manifest = list(stdcsv.DictReader(stream, delimiter="\t"))
    rows = {r["site"]: r for r in manifest}
    if len(manifest) != 10 or len(rows) != 10 or set(sites) != set(rows):
        raise ValueError("Stage04b source sites differ from ten-site Batch03 manifest")
    for (site, source_name), spec in specs.items():
        package = rows[site]["package"]
        if Path(spec["file"]).parent.name != package:
            raise ValueError("Source filename package mismatches manifest: " + site)
        native = "HR" if site == "US-MMS" else "HH"
        primary_type = "FULLSET" if site == "US-Me2" else "FLUXMET"
        if source_name not in (primary_type + "_" + native, "ERA5_" + native):
            raise ValueError("Batch03 source type/resolution mismatch: " + site)
        if int(spec["interval_minutes"]) != (60 if native == "HR" else 30):
            raise ValueError("Batch03 timestamp interval mismatch: " + site)
        if (int(spec["first_year"]) != int(rows[site]["first_year"])
                or int(spec["last_year"]) != int(rows[site]["last_year"])):
            raise ValueError("Batch03 pinned release years differ from manifest: " + site)
    for site in sites:
        sources = [s for s0, s in specs if s0 == site]
        if len(sources) != 2 or sum(s.startswith("ERA5_") for s in sources) != 1:
            raise ValueError("Expected primary/ERA5 pair at " + site)

    pairs = csv(snapshots[review / "paired_event_review.csv"])
    ledger = csv(snapshots[source / "physical_anomaly_records.csv"])
    keys = ["site", "source", "source_csv_row"]
    if len(pairs) != summary["events"] or len(ledger) != len(pairs):
        raise ValueError("Event count differs from verified Stage05 summary")
    if set(zip(pairs.site, pairs.source)) - set(specs): raise ValueError("Unknown paired source")
    merged = pairs.merge(ledger, on=keys, how="outer", suffixes=("_pair", "_ledger"), validate="one_to_one", indicator=True)
    if not merged["_merge"].eq("both").all(): raise ValueError("Paired/Stage04b source-row keys differ")
    for a, b in (("TIMESTAMP_START_pair", "TIMESTAMP_START_ledger"), ("source_flags", "flags")):
        if not merged[a].eq(merged[b]).all(): raise ValueError("Paired/Stage04b mismatch: " + a)
    for v in list(BOUNDS) + [v + "_QC" for v in BOUNDS]:
        if not np.isclose(number(merged["source_" + v]), number(merged[v]), rtol=1e-12, atol=1e-12, equal_nan=True).all():
            raise ValueError("Paired/Stage04b value mismatch: " + v)
    if not pairs.source_row_verified.str.lower().eq("true").all(): raise ValueError("Unverified paired rows")
    actual = pairs.groupby(["site", "source", "review_status"]).size().rename("records").reset_index()
    expected = pd.DataFrame(summary["review_status_counts"], columns=actual.columns)
    sorter = ["site", "source", "review_status"]
    if not actual.sort_values(sorter).reset_index(drop=True).equals(expected.sort_values(sorter).reset_index(drop=True)):
        raise ValueError("Paired statuses differ from Stage05 summary")
    own, other = diagnose(pairs, "source_"), diagnose(pairs, "counterpart_")
    if own["flags"] != [set(f.split("|")) if f else set() for f in pairs.source_flags]:
        raise ValueError("Recomputed primary/ERA5 flags differ from Stage05")
    if [priority(f) for f in own["flags"]] != pairs.priority.tolist():
        raise ValueError("Priority differs from recomputed screen")
    for i, row in pairs.iterrows():
        opposite = next(s for s0, s in specs if s0 == row.site and s != row.source)
        if row.counterpart_source != opposite: raise ValueError("Wrong counterpart source")
        if row.counterpart_rows == "1" and other["flags"][i] != (set(row.counterpart_flags.split("|")) if row.counterpart_flags else set()):
            raise ValueError("Recomputed counterpart flags differ from Stage05")

    pairs["role"] = np.where(pairs.source.str.startswith("ERA5_"), "ERA5", "PRIMARY")
    direction = pairs.groupby(["site", "role", "priority", "review_status"]).size().rename("source_records").reset_index()
    primary = pairs.role.eq("PRIMARY")
    issue_rows, event_rows = [], []
    structural_holds = {"HOLD_DUPLICATE_TIMESTAMP", "HOLD_COUNTERPART_TIMESTAMP_MISSING", "HOLD_NATIVE_TIME_INTERVAL", "HOLD_LEDGER_MISMATCH"}
    for i in np.flatnonzero(primary):
        row = pairs.iloc[i]
        causes = [k for k, mask in own["causes"].items() if mask[i]] if row.priority.startswith("P0") else [row.priority]
        availability = []
        for cause in causes:
            humidity = cause.startswith(("HUM_", "P1_", "P2_", "P3_"))
            variables = ("TA", "VPD", "PA") if humidity else (cause.rsplit("_", 2)[0],)
            if row.review_status in structural_holds or row.counterpart_rows != "1":
                state = "HOLD_TIME_OR_ROW_IDENTITY"
            elif not all(np.isfinite(other["values"][v][i]) for v in variables):
                state = "HOLD_RELEVANT_VARIABLE_MISSING"
            elif humidity:
                clear = (other["testable"][i] and not other["humidity_bad"][i] and other["rh"][i] >= 10
                         and all(BOUNDS[v][0] <= other["values"][v][i] <= BOUNDS[v][1] for v in variables))
                state = "REVIEW_GROUP_SCREEN_CLEAR" if clear else "HOLD_RELEVANT_GROUP_SCREEN"
            else:
                v = variables[0]
                state = "REVIEW_VARIABLE_SCREEN_CLEAR" if BOUNDS[v][0] <= other["values"][v][i] <= BOUNDS[v][1] else "HOLD_RELEVANT_VARIABLE_SCREEN"
            availability.append(state.startswith("REVIEW_"))
            qc = ";".join(v + "=" + (row["source_" + v + "_QC"] or "MISSING") for v in variables)
            metric, basis = ("rh", "RH_liquid_pct") if humidity else (None, variables[0])
            if cause == "HUM_VAPOR_NONPOSITIVE": metric, basis = "ea", "vapor_Pa"
            elif cause == "HUM_DENOMINATOR_NONPOSITIVE": metric, basis = "denominator", "humidity_denominator_Pa"
            elif cause.startswith("HUM_Q_"): metric, basis = "q", "specific_humidity_kgkg"
            issue_rows.append(dict(site=row.site, source=row.source, source_csv_row=row.source_csv_row,
                TIMESTAMP_START=row.TIMESTAMP_START, priority=row.priority, cause=cause,
                variables="|".join(variables), comparison_status=state, source_relevant_QC=qc,
                any_relevant_QC0=any(float(row["source_" + v + "_QC"] or "nan") == 0 for v in variables),
                source_value=own[metric][i] if metric else own["values"][variables[0]][i],
                counterpart_value=other[metric][i] if metric else other["values"][variables[0]][i],
                value_basis=basis,
                source_vapor_Pa=own["ea"][i] if humidity else np.nan,
                source_specific_humidity_kgkg=own["q"][i] if humidity else np.nan,
                source_TA_C=own["values"]["TA"][i], counterpart_TA_C=other["values"]["TA"][i],
                original_paired_status=row.review_status))
        if row.priority.startswith("P0"):
            action = "REVIEW_P0_ALL_FLAGGED_FIELDS_HAVE_SCREEN_CLEAR_COUNTERPART" if all(availability) else (
                "REVIEW_P0_PARTIAL_COUNTERPART_SUPPORT" if any(availability) else "REVIEW_P0_NO_SCREEN_CLEAR_COUNTERPART")
        else:
            action = "REVIEW_P1_EXTREME_DRYNESS" if row.priority.startswith("P1") else "RETAIN_PENDING_LOW_RH_REVIEW"
        event_rows.append(dict(site=row.site, source=row.source, source_csv_row=row.source_csv_row,
            TIMESTAMP_START=row.TIMESTAMP_START, priority=row.priority, review_queue=action))
    issues = pd.DataFrame(issue_rows, columns=["site", "source", "source_csv_row", "TIMESTAMP_START", "priority", "cause", "variables", "comparison_status", "source_relevant_QC", "any_relevant_QC0", "source_value", "counterpart_value", "value_basis", "source_vapor_Pa", "source_specific_humidity_kgkg", "source_TA_C", "counterpart_TA_C", "original_paired_status"])
    events = pd.DataFrame(event_rows, columns=["site", "source", "source_csv_row", "TIMESTAMP_START", "priority", "review_queue"])
    causes = issues.groupby(["site", "cause", "variables", "comparison_status", "value_basis"], as_index=False).agg(
        source_records=("source_csv_row", "size"), any_relevant_QC0_records=("any_relevant_QC0", "sum"),
        source_min=("source_value", "min"), source_median=("source_value", "median"), source_max=("source_value", "max"))
    queues = events.groupby(["site", "priority", "review_queue"]).size().rename("source_records").reset_index()
    gaps = csv(snapshots[source / "missing_episodes.csv"])
    gaps = gaps[~gaps.source.str.startswith("ERA5_")].copy()
    gaps["hours"] = pd.to_numeric(gaps.hours, errors="raise")
    gaps["records"] = pd.to_numeric(gaps.records, errors="raise")
    gaps["duration_band"] = pd.cut(gaps.hours, [0, 1, 3, 6, 24, np.inf], labels=["LE_1H", "GT_1_TO_3H", "GT_3_TO_6H", "GT_6_TO_24H", "GT_24H"])
    gap_summary = gaps.groupby(["site", "variable", "duration_band"], observed=True, as_index=False).agg(
        episodes=("records", "size"), affected_records=("records", "sum"), affected_hours=("hours", "sum"), longest_hours=("hours", "max"))
    quality = csv(snapshots[review / "source_quality_summary.csv"])
    quality = quality[~quality.source.str.startswith("ERA5_")]
    episodes = csv(snapshots[review / "event_episodes.csv"])
    episodes = episodes[~episodes.source.str.startswith("ERA5_")].copy()
    episodes["hours"] = pd.to_numeric(episodes.hours, errors="raise")
    # Validate snapshots again before creating outputs. No live raw-file claim.
    for p, data in snapshots.items():
        if digest(p.read_bytes()) != digest(data): raise ValueError("Input report changed during diagnosis: " + str(p))
    if args.check:
        print("STAGE06 PREFLIGHT: 20/20 sources, {} verified events, {} primary events, {} companion events; no reports written".format(
            len(pairs), len(pairs), len(events), int((~primary).sum())))
        print("SOURCE REPORT:", source)
        print("STAGE05 REPORT:", review)
        return 0
    root = args.report_root.expanduser() if args.report_root else source.parent
    out = root / ("stage06_repair_scope_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    for name, frame in {"direction_summary": direction, "primary_issue_details": issues, "primary_cause_summary": causes,
                        "primary_event_review_queue": events, "primary_review_summary": queues,
                        "primary_missing_episodes": gaps, "primary_gap_summary": gap_summary,
                        "primary_source_quality": quality, "primary_priority_episodes": episodes}.items():
        frame.to_csv(out / (name + ".csv"), index=False)
    clear_status = pairs.review_status.isin(["REVIEW_HIGH_PRIORITY_COUNTERPART_NUMERICALLY_CLEAR", "REVIEW_LOW_RH_DO_NOT_AUTOREPLACE"])
    era_primary_clear = int((pairs.role.eq("ERA5") & clear_status).sum())
    result = dict(source_report=str(source), review_report=str(review), events=len(pairs), primary_events=len(events),
        companion_events=int((~primary).sum()), companion_events_with_primary_screen_clear=era_primary_clear,
        primary_issue_rows=len(issues), primary_gap_episodes=len(gaps),
        input_report_sha256={str(p): digest(data) for p, data in snapshots.items()},
        scope="Diagnosis of verified report snapshots only; no raw recheck, variable replacement, interpolation, surfaces, DATM or jobs.",
        interpretation=["All comparison statuses are review evidence, not repair authorization or model-readiness approval.",
            "Humidity predicates and range thresholds are the exploratory Stage04b liquid-water screen, not conclusive instrument errors.",
            "Humidity causes overlap: nonpositive vapor can also yield negative specific humidity. Never sum cause counts as unique events.",
            "RH>101 or q>0.08 requires context; a humidity flag does not identify which of TA/VPD/PA is wrong.",
            "Relevant-variable screening allows unrelated companion flags but retains native-time/identity holds. QC0 remains reviewable, not auto-discarded.",
            "Positive low RH is retained pending review. Duration bands are descriptive, not interpolation rules.",
            "Timestamp gaps and per-variable gaps overlap; do not sum them as elapsed outage hours.",
            "No source-event count includes all normal source timestamps. ERA5-only anomalies are backup-source issues."])
    (out / "repair_scope_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    ranks = ["P0_NUMERICAL_SCREEN", "P1_RH_LT1", "P2_RH_1_TO5", "P3_RH_5_TO10"]
    print("PRIMARY ONLY: mutually exclusive native source records")
    table = events.groupby(["site", "priority"]).size().unstack(fill_value=0).reindex(index=sites, columns=ranks, fill_value=0)
    print(table.to_string())
    print("\nPRIMARY P0 CAUSES (overlap; values use value_basis):")
    p0 = causes[causes.cause.str.contains("_SCREEN$|^HUM_", regex=True)]
    print(p0.sort_values(["site", "source_records"], ascending=[True, False]).to_string(index=False) if len(p0) else "none")
    print("\nPRIMARY EVENT REVIEW QUEUES (mutually exclusive):")
    print(queues.groupby("review_queue").source_records.sum().to_string())
    print("\nPRIMARY TIMESTAMP / VARIABLE COVERAGE:")
    print(quality.to_string(index=False))
    print("\nLONGEST PRIMARY GAPS (timestamp/variable rows may overlap):")
    print(gaps.sort_values("hours", ascending=False).head(15).to_string(index=False) if len(gaps) else "none")
    print("\nERA5 events with primary numerically clear:", era_primary_clear, "(not primary repair events)")
    print("STAGE06 SUMMARY: primary_events={} companion_events={} primary_issue_rows={} primary_gap_episodes={}".format(len(events), int((~primary).sum()), len(issues), len(gaps)))
    print("REPORT DIR:", out)
    print("No interpolation, source replacement, forcing generation, surface changes, DATM or model jobs performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

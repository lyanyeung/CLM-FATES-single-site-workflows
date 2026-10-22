#!/usr/bin/env python3
"""Stage05: classify Stage04b events, gaps and paired source evidence; no repairs.

Read exact reports and checksum-pinned raw products. Separate dry-condition
review from numerical flags. A clear companion screen never authorizes edits.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
BATCH = Path(__file__).resolve().parents[2]


def helper_module():
    path = BATCH / "scripts/stage04/04b_audit_batch03_met_sources.py"
    spec = importlib.util.spec_from_file_location("batch03_source_audit", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def value(item):
    try:
        number = float(item)
        return number if np.isfinite(number) else np.nan
    except (TypeError, ValueError):
        return np.nan


def screen(record, bounds):
    flags = {key + "_RANGE" for key, (lo, hi) in bounds.items()
             if np.isfinite(record[key]) and not lo <= record[key] <= hi}
    t, v, p = np.float64(record["TA"]), np.float64(record["VPD"]), np.float64(record["PA"]) * 1000
    rh, q = np.nan, np.nan
    if np.isfinite(t) and np.isfinite(v) and np.isfinite(p) and p > 0 and t > -150:
        with np.errstate(all="ignore"):
            es = 611.2 * np.exp(np.clip(17.67 * t / (t + 243.5), -40, 40))
            ea = es - v * 100
            rh = ea / es * 100
            denominator = p - 0.378 * ea
            q = 0.622 * ea / denominator
            if ea <= 0 or rh > 101 or denominator <= 0 or q < 0 or q > 0.08 or not np.isfinite(q):
                flags.add("HUMIDITY_INVALID")
            for limit in (1, 5, 10):
                if 0 < rh < limit:
                    flags.add("RH_LT" + str(limit))
    return flags, float(rh), float(q)


def priority(flags):
    if "HUMIDITY_INVALID" in flags or any(f.endswith("_RANGE") for f in flags):
        return "P0_NUMERICAL_SCREEN"
    if "RH_LT1" in flags:
        return "P1_RH_LT1"
    if "RH_LT5" in flags:
        return "P2_RH_1_TO5"
    if "RH_LT10" in flags:
        return "P3_RH_5_TO10"
    raise ValueError("Unrecognized event flags: " + repr(flags))


def relevant_variables(flags):
    result = {flag[:-6] for flag in flags if flag.endswith("_RANGE")}
    if "HUMIDITY_INVALID" in flags or any(f.startswith("RH_LT") for f in flags):
        result.update(("TA", "VPD", "PA"))
    return sorted(result)


def native_good(record, step):
    start = pd.to_datetime(record["start"], format="%Y%m%d%H%M", errors="coerce")
    end = pd.to_datetime(record["end"], format="%Y%m%d%H%M", errors="coerce")
    return (pd.notna(start) and pd.notna(end) and (end - start).total_seconds() == step * 60
            and start.minute % step == 0)


def target_rows(spec, targets, module, chunksize):
    path = Path(spec["file"])
    if module.digest(path) != spec["sha256"]:
        raise ValueError("Raw source checksum changed since Stage04b: " + str(path))
    before = (path.stat().st_size, path.stat().st_mtime_ns)
    columns = ["TIMESTAMP_START", "TIMESTAMP_END"] + list(spec["columns"].values())
    columns += [c for c in spec["qc_columns"].values() if c]
    result, offset = {}, 0
    for part in pd.read_csv(path, usecols=list(dict.fromkeys(columns)), dtype="string", chunksize=chunksize):
        start = part["TIMESTAMP_START"].str.strip().str.replace(r"\.0$", "", regex=True)
        take = start.isin(targets).to_numpy()
        if take.any():
            selected = part.loc[take]
            data = {key: module.numeric(selected[column]) for key, column in spec["columns"].items()}
            for key, column in spec["qc_columns"].items():
                data[key + "_QC"] = module.numeric(selected[column]) if column else np.full(len(selected), np.nan)
            for j, position in enumerate(np.flatnonzero(take)):
                stamp = str(start.iloc[position])
                record = {key: float(values[j]) for key, values in data.items()}
                record.update(start=stamp, end=str(part["TIMESTAMP_END"].iloc[position]).strip().removesuffix(".0"),
                              csv_row=offset + int(position) + 2)
                result.setdefault(stamp, []).append(record)
        offset += len(part)
    if before != (path.stat().st_size, path.stat().st_mtime_ns):
        raise ValueError("Source changed during paired read: " + str(path))
    return result


def episode_table(events, specs):
    rows = []
    for (site, source, rank), group in events.groupby(["site", "source", "priority"], sort=True):
        dates = pd.DatetimeIndex(pd.to_datetime(sorted(set(group["TIMESTAMP_START"])), format="%Y%m%d%H%M"))
        step = specs[(site, source)]["interval_minutes"]
        # Consecutiveness on the intended NO_LEAP grid, including Feb28/Mar1.
        day = (dates.year - 1970) * 365 + dates.dayofyear - 1 - (dates.is_leap_year & (dates.month > 2)).astype(int)
        position = np.asarray(day * 1440 + dates.hour * 60 + dates.minute)
        groups = np.split(np.arange(len(dates)), np.flatnonzero(np.diff(position) != step) + 1)
        for indices in groups:
            rows.append({"site": site, "source": source, "priority": rank,
                         "start": dates[indices[0]].strftime("%Y%m%d%H%M"),
                         "last_start": dates[indices[-1]].strftime("%Y%m%d%H%M"),
                         "unique_timestamps": len(indices), "native_minutes": step,
                         "hours": len(indices) * step / 60})
    return pd.DataFrame(rows, columns=["site", "source", "priority", "start", "last_start", "unique_timestamps", "native_minutes", "hours"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-report", required=True, type=Path)
    parser.add_argument("--check", action="store_true", help="Read-only ledger, manifest and source preflight; no output files")
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--chunksize", type=int, default=120000)
    args = parser.parse_args()
    if args.chunksize < 1000: parser.error("chunksize must be >=1000")
    source_report = args.source_report.expanduser().resolve()
    if (source_report.parent.name != "reports"
            or source_report.parent.parent.name != "AmeriFlux_MultiSite_10_Batch03"
            or not source_report.name.startswith("stage04b_met_")):
        raise ValueError("Refusing Stage04b report outside the Batch03 experiment reports folder")
    module = helper_module()
    inventory = json.loads((source_report / "source_inventory.json").read_text())
    if inventory["failures"]:
        raise ValueError("Stage04b has incomplete sources; resolve source failures first")
    specs = {(r["site"], r["source"]): r for r in inventory["completed"]}
    if len(specs) != 20 or len({key[0] for key in specs}) != 10:
        raise ValueError("Expected completed Stage04b audit of ten sites and twenty sources")
    # Pin the exact Batch03 manifest, release names, and HH/HR identity.
    manifest = module.load_sites()
    manifest_by_site = {entry["site"]: entry for entry in manifest}
    if set(manifest_by_site) != {key[0] for key in specs}:
        raise ValueError("Source report site set differs from Batch03 manifest")
    for (site, source), entry in specs.items():
        expected = manifest_by_site[site]
        path = Path(entry["file"])
        if path.parent.name != expected["package"] or path.parent.parent.name != "raw":
            raise ValueError("Source report package path mismatch: " + site + " " + source)
        native = "HR" if site == "US-MMS" else "HH"
        primary = "FULLSET" if site == "US-Me2" else "FLUXMET"
        expected_sources = {primary + "_" + native, "ERA5_" + native}
        if source not in expected_sources or entry["interval_minutes"] != (60 if native == "HR" else 30):
            raise ValueError("Source/resolution mismatches Batch03: " + site + " " + source)
        if (entry["first_year"] != int(expected["first_year"]) or
                entry["last_year"] != int(expected["last_year"])):
            raise ValueError("Release-year mismatch: " + site + " " + source)
    events = read_csv(source_report / "physical_anomaly_records.csv")
    annual = pd.read_csv(source_report / "annual_source_coverage_and_QC.csv")
    gaps = pd.read_csv(source_report / "missing_episodes.csv")
    times = read_csv(source_report / "timestamp_issues.csv")
    if events.duplicated(["site", "source", "source_csv_row"]).any():
        raise ValueError("Duplicate source row IDs in Stage04b event ledger")
    counts = events.groupby(["site", "source"]).size().to_dict()
    for key, spec in specs.items():
        total = int(annual.loc[(annual.site == key[0]) & (annual.source == key[1]), "flagged_source_records"].sum())
        if total != counts.get(key, 0) or total != spec["flagged_source_records"]:
            raise ValueError("Inconsistent source/annual/ledger event counts: " + repr(key))
    if set(zip(events.site, events.source)) - set(specs):
        raise ValueError("Event source absent from pinned inventory")
    events["priority"] = [priority(set(text.split("|"))) for text in events["flags"]]
    priority_rows = events.groupby(["site", "source", "priority"]).size().rename("source_records").reset_index()
    issues = events.assign(flag=events["flags"].str.split("|")).explode("flag")
    issue_rows = issues.groupby(["site", "source", "flag"]).size().rename("source_records").reset_index()
    episodes = episode_table(events, specs)
    source_summary = []
    for key, spec in specs.items():
        subset = annual[(annual.site == key[0]) & (annual.source == key[1])]
        record = {"site": key[0], "source": key[1], "native_minutes": spec["interval_minutes"],
                  "flagged_source_records": counts.get(key, 0), "review_source_years": spec["review_years"],
                  "source_invalid_start": spec["invalid_start"], "source_invalid_end": spec["invalid_end"],
                  "source_nonincreasing_time": spec["nonincreasing_source_records"]}
        for column in ["missing_timestamps", "duplicate_timestamps", "off_grid_timestamps", "invalid_intervals"] + [v + "_missing_records" for v in module.BOUNDS]:
            record[column] = int(subset[column].sum())
        source_summary.append(record)
    gap_summary = gaps.groupby(["site", "source", "variable"], as_index=False).agg(
        episodes=("records", "size"), affected_records=("records", "sum"),
        affected_hours=("hours", "sum"), longest_hours=("hours", "max")) if len(gaps) else pd.DataFrame(
            columns=["site", "source", "variable", "episodes", "affected_records", "affected_hours", "longest_hours"])
    if args.check:
        print("STAGE05 PREFLIGHT: 20/20 Batch03 sources pinned; {} anomaly ledger rows reconciled; no reports or source files written".format(len(events)))
        print("Input:", source_report)
        print("Full paired source-row checks and checksum verification are performed without --check.")
        return 0
    root = args.report_root.expanduser() if args.report_root else source_report.parent
    out = root / ("stage05_event_review_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    pair_path = out / "paired_event_review.csv"
    policy_counts, qc_counts = Counter(), Counter()
    verified, mismatch, paired_both_flagged, identical_tvp = 0, 0, 0, 0
    fields = ["site", "source", "source_csv_row", "TIMESTAMP_START", "priority", "source_flags", "source_row_verified",
              "source_rows_at_timestamp", "counterpart_source", "counterpart_rows", "counterpart_flags", "counterpart_missing_variables",
              "TA_VPD_PA_identical", "review_status", "relevant_source_QC"]
    fields += [prefix + variable for prefix in ("source_", "counterpart_") for variable in list(module.BOUNDS) + [v + "_QC" for v in module.BOUNDS]]
    import csv
    with pair_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for site in sorted({key[0] for key in specs}):
            group = events[events.site == site]
            chosen = {source: spec for (s, source), spec in specs.items() if s == site}
            if len(chosen) != 2 or sum(s.startswith("ERA5") for s in chosen) != 1:
                raise ValueError("Expected one primary and one ERA5 source: " + site)
            targets = set(group["TIMESTAMP_START"])
            raw = {}
            for source, spec in chosen.items():
                raw[source] = target_rows(spec, targets, module, args.chunksize)
            for event in group.to_dict("records"):
                source, stamp = event["source"], event["TIMESTAMP_START"]
                counterpart = next(s for s in chosen if s != source)
                own_rows, other_rows = raw[source].get(stamp, []), raw[counterpart].get(stamp, [])
                own = next((r for r in own_rows if r["csv_row"] == int(event["source_csv_row"])), None)
                other = other_rows[0] if len(other_rows) == 1 else None
                flags = set(event["flags"].split("|"))
                own_ok = own is not None and all(np.isclose(own[v], value(event[v]), rtol=1e-12, atol=1e-12, equal_nan=True)
                                                    for v in list(module.BOUNDS) + [v + "_QC" for v in module.BOUNDS])
                if own_ok:
                    own_end = pd.to_datetime(own["end"], format="%Y%m%d%H%M", errors="coerce")
                    ledger_end = pd.to_datetime(event["TIMESTAMP_END"], format="%Y%m%d%H%M", errors="coerce")
                    own_ok = bool((pd.isna(own_end) and pd.isna(ledger_end)) or own_end == ledger_end)
                if own_ok: own_ok = screen(own, module.BOUNDS)[0] == flags
                verified += int(own_ok); mismatch += int(not own_ok)
                other_flags = screen(other, module.BOUNDS)[0] if other else set()
                missing = [v for v in module.BOUNDS if not np.isfinite(other[v])] if other else list(module.BOUNDS)
                same = bool(own is not None and other is not None and all(
                    np.isfinite(own[v]) and np.isfinite(other[v]) and np.isclose(own[v], other[v], rtol=1e-12, atol=1e-12)
                    for v in ("TA", "VPD", "PA")))
                identical_tvp += int(same)
                paired_both_flagged += int(bool(other_flags))
                if not own_ok: status = "HOLD_LEDGER_MISMATCH"
                elif len(own_rows) != 1 or len(other_rows) > 1: status = "HOLD_DUPLICATE_TIMESTAMP"
                elif not other_rows: status = "HOLD_COUNTERPART_TIMESTAMP_MISSING"
                elif not native_good(own, chosen[source]["interval_minutes"]) or not native_good(other, chosen[counterpart]["interval_minutes"]): status = "HOLD_NATIVE_TIME_INTERVAL"
                elif missing: status = "HOLD_COUNTERPART_VARIABLE_MISSING"
                elif other_flags: status = "HOLD_COUNTERPART_FLAGGED"
                elif event["priority"].startswith(("P2", "P3")): status = "REVIEW_LOW_RH_DO_NOT_AUTOREPLACE"
                else: status = "REVIEW_HIGH_PRIORITY_COUNTERPART_NUMERICALLY_CLEAR"
                relevant = relevant_variables(flags)
                qc_text = ";".join(v + "=" + (str(own[v + "_QC"]) if own is not None and np.isfinite(own[v + "_QC"]) else "MISSING") for v in relevant)
                for variable in relevant:
                    code = str(own[variable + "_QC"]) if own is not None and np.isfinite(own[variable + "_QC"]) else "MISSING"
                    qc_counts[(site, source, event["priority"], variable, code)] += 1
                output = {"site": site, "source": source, "source_csv_row": event["source_csv_row"], "TIMESTAMP_START": stamp,
                          "priority": event["priority"], "source_flags": event["flags"], "source_row_verified": own_ok,
                          "source_rows_at_timestamp": len(own_rows), "counterpart_source": counterpart,
                          "counterpart_rows": len(other_rows), "counterpart_flags": "|".join(sorted(other_flags)),
                          "counterpart_missing_variables": "|".join(missing), "TA_VPD_PA_identical": same,
                          "review_status": status, "relevant_source_QC": qc_text}
                for prefix, record in (("source_", own), ("counterpart_", other)):
                    for variable in list(module.BOUNDS) + [v + "_QC" for v in module.BOUNDS]:
                        output[prefix + variable] = record[variable] if record is not None and np.isfinite(record[variable]) else ""
                writer.writerow(output); policy_counts[(site, source, status)] += 1
            print("PAIRED:", site, "events=", len(group), "unique native timestamps=", len(targets), flush=True)
    priority_rows.to_csv(out / "priority_summary.csv", index=False)
    issue_rows.to_csv(out / "flag_type_summary.csv", index=False)
    episodes.to_csv(out / "event_episodes.csv", index=False)
    pd.DataFrame(source_summary).to_csv(out / "source_quality_summary.csv", index=False)
    gap_summary.to_csv(out / "missing_episode_summary.csv", index=False)
    pd.DataFrame([dict(site=k[0], source=k[1], priority=k[2], variable=k[3], QC_code=k[4], records=v) for k, v in qc_counts.items()],
                 columns=["site", "source", "priority", "variable", "QC_code", "records"]).to_csv(out / "relevant_QC_summary.csv", index=False)
    policies = pd.DataFrame([dict(site=k[0], source=k[1], review_status=k[2], records=v) for k, v in policy_counts.items()],
                            columns=["site", "source", "review_status", "records"])
    policies.to_csv(out / "paired_review_summary.csv", index=False)
    with (out / "review_summary.json").open("x", encoding="utf-8") as stream:
        json.dump({"source_report": str(source_report), "events": len(events), "verified_source_rows": verified,
                   "ledger_mismatches": mismatch, "source_events_with_flagged_counterpart": paired_both_flagged,
                   "events_with_identical_TA_VPD_PA": identical_tvp,
                   "input_report_sha256": {name: module.digest(source_report / name) for name in (
                       "source_inventory.json", "physical_anomaly_records.csv", "annual_source_coverage_and_QC.csv", "missing_episodes.csv", "timestamp_issues.csv")},
                   "review_status_counts": policies.to_dict("records"),
                   "scope": "evidence review only; no repair candidates applied or approved; companion ERA5 not independent truth"}, stream, indent=2)
    print("\nPRIORITIES (mutually exclusive; native source records):")
    print(priority_rows.pivot_table(index=["site", "source"], columns="priority", values="source_records", fill_value=0, aggfunc="sum").to_string())
    print("\nPAIRED REVIEW STATUS:")
    print(policies.groupby("review_status")["records"].sum().to_string())
    print("\nSTAGE05 SUMMARY: events={} verified_source_rows={} ledger_mismatches={} episodes={}".format(len(events), verified, mismatch, len(episodes)))
    print("REPORT DIR:", out)
    print("No interpolation, ERA5/ERA5-Land repair, source/surface changes, DATM or model runs performed.")
    return 2 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())

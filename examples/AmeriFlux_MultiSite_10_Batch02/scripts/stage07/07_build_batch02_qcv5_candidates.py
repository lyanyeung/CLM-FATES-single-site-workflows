#!/usr/bin/env python3
"""Build isolated native HH/HR QC-v5 candidates and reconcile their event ledger.

Requires the exact completed Stage06 snapshot. Raw files, existing reports,
surfaces and cases remain inputs. A completed candidate is not model approval.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
BATCH = Path(__file__).resolve().parents[2]
DEFAULT_EXPERIMENT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
ENGINE = Path(__file__).with_name("qcv5_native.py")
VARS = ("TA_F", "VPD_F", "PA_F", "SW_IN_F", "LW_IN_F", "WS_F", "P_F")
HISTORICAL_ENGINE_BLOB = "f82e43c7d379bfaea370a349e7fe9f842bdc93b3"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(2**20), b""): h.update(block)
    return h.hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_engine():
    spec = importlib.util.spec_from_file_location("batch02_qcv5_native", ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = {"TA_F": 4, "VPD_F": 4, "PA_F": 4, "SW_IN_F": 2, "LW_IN_F": 4, "WS_F": 4, "P_F": 0}
    if module.INTERPOLATE != policy: raise ValueError("Unexpected QC-v5 interpolation policy")
    return module


def manifest_rows():
    with (BATCH / "sites.tsv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != 10 or len({r["site"] for r in rows}) != 10:
        raise ValueError("Expected ten distinct manifest sites")
    return rows


def preflight(scope_folder, rows):
    scope_file = scope_folder / "repair_scope_summary.json"
    scope = json.loads(scope_file.read_text())
    hashes = {Path(p).resolve(): h for p, h in scope["input_report_sha256"].items()}
    hashes[scope_file] = sha(scope_file)
    hashes[BATCH / "sites.tsv"] = sha(BATCH / "sites.tsv")
    hashes[ENGINE] = sha(ENGINE)
    hashes[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    for path, expected in hashes.items():
        if sha(path) != expected: raise ValueError("Pinned report or code changed: " + str(path))
    source_report = Path(scope["source_report"]).resolve()
    review_report = Path(scope["review_report"]).resolve()
    inv_path = source_report / "source_inventory.json"
    if inv_path not in hashes: raise ValueError("Stage06 did not pin its source inventory")
    inventory = json.loads(inv_path.read_text())
    specs = {(r["site"], r["source"]): r for r in inventory["completed"]}
    if inventory["failures"] or len(specs) != 20 or {s for s, _ in specs} != {r["site"] for r in rows}:
        raise ValueError("Incomplete or mismatched source inventory")
    prior = json.loads((review_report / "review_summary.json").read_text())
    if (review_report / "review_summary.json") not in hashes or prior["ledger_mismatches"] or prior["events"] != prior["verified_source_rows"]:
        raise ValueError("Stage05 verification incomplete or not pinned by Stage06")
    annual = pd.read_csv(source_report / "annual_source_coverage_and_QC.csv")
    if (source_report / "annual_source_coverage_and_QC.csv") not in hashes:
        raise ValueError("Annual source report not pinned")
    if annual[["missing_timestamps", "duplicate_timestamps", "off_grid_timestamps", "invalid_intervals"]].sum().sum() != 0:
        raise ValueError("Resolve source chronology/interval issues before native QC-v5")
    primary_events = sum(s["flagged_source_records"] for (site, name), s in specs.items() if not name.startswith("ERA5_"))
    if primary_events != scope["primary_events"]: raise ValueError("Stage06 primary event total differs from inventory")
    chosen = []
    for row in rows:
        site = row["site"]
        group = [s for (name, _), s in specs.items() if name == site]
        primary = [s for s in group if not s["source"].startswith("ERA5_")]
        companion = [s for s in group if s["source"].startswith("ERA5_")]
        if len(primary) != 1 or len(companion) != 1: raise ValueError("Expected primary/ERA5 pair: " + site)
        met, era = primary[0], companion[0]
        step = int(met["interval_minutes"])
        if step not in (30, 60) or era["interval_minutes"] != step: raise ValueError("Native intervals differ: " + site)
        expected_step = 60 if site == "US-Ha1" else 30
        if step != expected_step: raise ValueError("Unexpected site native interval: " + site)
        for product in group:
            path = Path(product["file"]).resolve()
            if path.parent.name != row["package"] or path.parent.parent.name != "raw" or path.parents[3].name != site:
                raise ValueError("Raw product is outside exact site release: " + str(path))
            if (product["first_year"], product["last_year"]) != (int(row["first_year"]), int(row["last_year"])):
                raise ValueError("Source window differs from manifest: " + site)
            if any(product[k] for k in ("invalid_start", "invalid_end", "nonincreasing_source_records")):
                raise ValueError("Source has unresolved timestamp defects: " + str(path))
            print("SHA256 CHECK:", site, product["source"], flush=True)
            if sha(path) != product["sha256"]: raise ValueError("Raw source changed since Stage04b: " + str(path))
            hashes[path] = product["sha256"]
        header = set(met["header"])
        if not {"TIMESTAMP_START", *VARS}.issubset(header): raise ValueError("Missing canonical primary _F columns: " + site)
        if not {"TIMESTAMP_START", *[v.removesuffix("_F") + "_ERA" for v in VARS]}.issubset(era["header"]):
            raise ValueError("Missing standalone ERA5 fields: " + site)
        rh_columns = sorted(c for c in header if c == "RH" or c.startswith("RH_"))
        info = dict(site=site, release=row["package"], first_year=int(row["first_year"]), last_year=int(row["last_year"]),
                    native_minutes=step, primary=str(Path(met["file"]).resolve()), era=str(Path(era["file"]).resolve()),
                    RH_columns=rh_columns)
        chosen.append(info)
        print("CHECK OK", site, "native_minutes=", step, "RH_COLUMNS=", rh_columns, flush=True)
    return chosen, hashes


def numeric(frame, col):
    x = pd.to_numeric(frame[col], errors="coerce")
    return x.where(np.isfinite(x) & (x > -9990)).to_numpy(dtype=float)


def independent_audit(info, out):
    """Independent conversions, humidity, chronology and raw-to-ledger matching."""
    site, step, first, last = info["site"], info["native_minutes"], info["first_year"], info["last_year"]
    folder = out / site / "forcing"
    forcing = folder / "processed_v5" / f"{site}_CLM_forcing_{first}_{last}.csv"
    qc = folder / "qc_v5"
    event_path, manual_path, status_path = [qc / f"{site}_{name}" for name in ("replacement_events.csv", "manual_review.csv", "status.json")]
    header = set(pd.read_csv(info["primary"], nrows=0).columns)
    qcols = [v + "_QC" for v in VARS if v + "_QC" in header]
    raw = pd.read_csv(info["primary"], usecols=["TIMESTAMP_START", *VARS, *qcols], dtype={"TIMESTAMP_START": str})
    times = pd.to_datetime(raw.TIMESTAMP_START, format="%Y%m%d%H%M", errors="raise")
    raw = raw.loc[times.dt.year.between(first, last) & ~((times.dt.month == 2) & (times.dt.day == 29))].copy()
    raw["time"] = pd.to_datetime(raw.TIMESTAMP_START, format="%Y%m%d%H%M")
    raw = raw.sort_values("time").reset_index(drop=True)
    expected = pd.date_range(f"{first}-01-01", f"{last+1}-01-01", freq=f"{step}min", inclusive="left")
    expected = expected[~((expected.month == 2) & (expected.day == 29))]
    force = pd.read_csv(forcing)
    if len(raw) != len(expected) or not np.array_equal(raw.time.to_numpy(), expected.to_numpy()):
        raise ValueError("Independent source calendar audit failed")
    if len(force) != len(expected) or not np.array_equal(pd.to_datetime(force.time).to_numpy(), expected.to_numpy()):
        raise ValueError("Candidate calendar audit failed")
    ranges = {"TBOT": (180, 340), "QBOT": (0, .08), "PSRF": (49000, 111000), "FSDS": (0, 1600),
              "FLDS": (0, 800), "WIND": (0, 75), "PRECTmms": (0, 300 / (step * 60))}
    for col, (lo, hi) in ranges.items():
        if not (np.isfinite(force[col]) & force[col].between(lo, hi)).all(): raise ValueError("Candidate field fails: " + col)
    values = {"TA_F": force.TA_USE.to_numpy(), "VPD_F": force.VPD_USE.to_numpy(), "PA_F": force.PSRF.to_numpy() / 1000,
              "SW_IN_F": force.FSDS.to_numpy(), "LW_IN_F": force.FLDS.to_numpy(), "WS_F": force.WIND.to_numpy(),
              "P_F": force.PRECTmms.to_numpy() * (step * 60)}
    if not np.isclose(force.TBOT, values["TA_F"] + 273.15, rtol=1e-10, atol=1e-9).all(): raise ValueError("TBOT conversion mismatch")
    t, v, p = values["TA_F"], values["VPD_F"], force.PSRF.to_numpy()
    with np.errstate(all="ignore"):
        es = 611.2 * np.exp(17.67 * t / (t + 243.5))
        ea = es - v * 100
        rh = 100 * ea / es
        q = .622 * ea / (p - .378 * ea)
    if not (np.isfinite(rh) & (rh > 0) & (rh <= 100.05)).all(): raise ValueError("Candidate humidity remains impossible")
    if not np.isclose(q, force.QBOT, rtol=1e-6, atol=1e-10).all(): raise ValueError("QBOT reconstruction mismatch")
    events, manual = pd.read_csv(event_path), pd.read_csv(manual_path)
    status = json.loads(status_path.read_text())
    if status["site"] != site or status["changes"] != len(events) or status["manual_review_records"] != len(manual):
        raise ValueError("Candidate status/event counts differ")
    original = {v: numeric(raw, v) for v in VARS}
    official_qc = {v: numeric(raw, v + "_QC") if v + "_QC" in header else np.full(len(raw), np.nan) for v in VARS}
    changed = {var: ~np.isclose(original[var], values[var], rtol=1e-10, atol=1e-9, equal_nan=True) for var in VARS}
    positions = {str(t): i for i, t in enumerate(expected)}
    seen, qc0 = set(), 0
    for event in events.to_dict("records"):
        variable, stamp = event["variable"], str(pd.Timestamp(event["time"]))
        key = (stamp, variable)
        if key in seen or stamp not in positions or variable not in VARS: raise ValueError("Duplicate or unknown replacement event")
        seen.add(key)
        i = positions[stamp]
        if not changed[variable][i]: raise ValueError("Logged event has no independently detected change")
        if not np.isclose(event["final_value"], values[variable][i], rtol=1e-10, atol=1e-9): raise ValueError("Event final value differs from candidate")
        if not np.isclose(event["original_value"], original[variable][i], equal_nan=True, rtol=1e-10, atol=1e-9):
            raise ValueError("Event original value differs from pinned raw source")
        rawqc = official_qc[variable][i]
        if not np.isclose(rawqc, event["official_qc"], equal_nan=True): raise ValueError("Event official QC differs from pinned raw source")
        qc0 += int(rawqc == 0)
    count = sum(int(mask.sum()) for mask in changed.values())
    if count != len(events): raise ValueError("Unlogged raw-to-candidate changes")
    for var, mask in changed.items():
        if int(mask.sum()) != int(events.variable.eq(var).sum()): raise ValueError("Per-variable change count mismatch: " + var)
    floor_count = int(events.reason.fillna("").str.contains("ERA_RH_below_1pct_clipped_requires_review").sum())
    bin_rh = rh.copy()
    for edge in (1, 5, 10):
        bin_rh[np.isclose(bin_rh, edge, rtol=0, atol=1e-9)] = edge
    result = dict(site=site, status="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED", native_minutes=step,
        noleap_rows=len(force), changes=count, changed_QC0_records=qc0, manual_review_records=len(manual),
        ERA_RH_floor_records=floor_count, positive_RH_lt1=int(((bin_rh > 0) & (bin_rh < 1)).sum()),
        RH_1_to5=int(((bin_rh >= 1) & (bin_rh < 5)).sum()), RH_5_to10=int(((bin_rh >= 5) & (bin_rh < 10)).sum()),
        RH_bin_tolerance_pct=1e-9,
        min_RH_pct=float(rh.min()), forcing_csv=str(forcing), error="")
    result["short_interpolation_variable_records"] = int(events.final_source.eq("local_short_interpolation").sum())
    result["ERA_replacement_variable_records"] = int(events.final_source.eq("secondary_era_replacement").sum())
    result["ERA_RH_reconstruction_variable_records"] = int(events.final_source.str.contains("RH|rh", regex=True).sum())
    write_json(qc / f"{site}_independent_audit.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--scope-report", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, help="New absent directory; defaults to a fresh Batch02 experiment trial")
    args = parser.parse_args()
    print("PYTHON:", sys.executable, "| numpy:", np.__version__, "| pandas:", pd.__version__, flush=True)
    rows = manifest_rows()
    scope_folder = args.scope_report.expanduser().resolve()
    chosen, hashes = preflight(scope_folder, rows)
    print("PREFLIGHT: 10/10 exact releases, 20/20 raw SHA256 verified", flush=True)
    if args.check:
        print("CHECK ONLY: no outputs created")
        return 0
    out = args.output_root.expanduser().resolve() if args.output_root else DEFAULT_EXPERIMENT / (
        "qcv5_native_trial_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    forbidden = {BATCH.resolve(), scope_folder}
    forbidden.update(Path(s["primary"]).parents[4] for s in chosen)
    forbidden.update(p.parent for p in hashes if p.suffix in (".json", ".csv") and "/reports/" in str(p))
    if out.exists() or any(out == p or p in out.parents for p in forbidden):
        raise ValueError("Refusing existing or input-tree output destination: " + str(out))
    engine = load_engine()
    engine.SITE_YEARS = {s["site"]: (s["first_year"], s["last_year"]) for s in chosen}
    by_site = {s["site"]: s for s in chosen}
    def exact_selector(raw_folder, pattern):
        site = raw_folder.parent.parent.name
        if pattern == "*FLUXMET_HH*.csv": return Path(by_site[site]["primary"])
        if pattern == "*ERA5_HH*.csv": return Path(by_site[site]["era"])
        raise ValueError("Unknown engine source selector: " + pattern)
    engine.get_one = exact_selector
    out.mkdir(parents=True, exist_ok=False)
    marker = out / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"
    marker.write_text("Inspect run summary and failed sites. Outputs are isolated candidates.\n")
    write_json(out / "exact_input_manifest.json", dict(created_utc=datetime.now(timezone.utc).isoformat(),
        scope_report=str(scope_folder), algorithm="HISTORICAL_QCV5_NATIVE_HH_HR_ADAPTATION",
        historical_engine_git_blob=HISTORICAL_ENGINE_BLOB, native_engine_sha256=hashes[ENGINE], sites=chosen,
        input_sha256={str(p): h for p, h in hashes.items()},
        adaptations=["Native 30/60-minute complete NO_LEAP calendar; no hourly upsampling.",
            "Short interpolation: complete runs <=120min, SW<=60min; no P interpolation; same-year valid boundaries.",
            "Joint plateau >=180 native minutes; precipitation divided by native seconds.",
            "Standalone ERA5 companion takes precedence over embedded ERA columns, matching Stage04b-06 evidence."],
        method_notes=["Other historical thresholds and repair ordering retained.",
            "When final humidity reconciliation uses ERA RH, its allowed raw range is [-2,100.05]%; used RH is clipped to [1,100]%, with floor changes recorded for review.",
            "Positive low RH alone is not a replacement rule; strong corroborating QC-v5 rules can modify a subset.",
            "All QC0 changes and floor adjustments remain reviewable in event/manual ledgers.",
            "No independently downloaded ERA5-Land, ZBOT, DATM, surface/case changes or Slurm jobs."]))
    results = []
    for info in chosen:
        site = info["site"]
        print("\n========== BUILD + AUDIT", site, "==========", flush=True)
        try:
            engine.parse_site(site, Path(info["primary"]).parents[4], out,
                              native_minutes=info["native_minutes"], standalone_era=True)
            result = independent_audit(info, out)
            print("VERIFIED", site, "rows=", result["noleap_rows"], "changes=", result["changes"],
                  "QC0_changes=", result["changed_QC0_records"], "RH_floor=", result["ERA_RH_floor_records"], flush=True)
        except Exception as exc:
            result = dict(site=site, status="FAIL", native_minutes=info["native_minutes"], error=str(exc))
            print("SITE FAILED:", site, str(exc), flush=True)
        results.append(result)
        pd.DataFrame(results).to_csv(out / "candidate_run_summary.csv", index=False)
    print("\nREVERIFY ALL INPUT SHA256", flush=True)
    changed_inputs = [str(p) for p, expected in hashes.items() if sha(p) != expected]
    write_json(out / "input_preservation_check.json", dict(unchanged=not changed_inputs, changed_inputs=changed_inputs))
    files = sorted(p for p in out.rglob("*") if p.is_file() and p != marker)
    write_json(out / "output_sha256.json", {str(p.relative_to(out)): sha(p) for p in files})
    failed = [r["site"] for r in results if r["status"] == "FAIL"]
    print("\nSTAGE07 SUMMARY: numeric_candidates={}/10 failed={} inputs_unchanged={}".format(10 - len(failed), len(failed), not changed_inputs))
    print(pd.DataFrame(results).to_string(index=False))
    print("CANDIDATE OUTPUT:", out)
    print("This command writes candidate outputs only; no DATM or model jobs started.")
    if failed or changed_inputs:
        print("INCOMPLETE marker retained; failed sites:", ", ".join(failed) or "input verification failure")
        return 2
    marker.unlink()
    (out / "COMPLETE_NUMERIC_CANDIDATES_REVIEW_REQUIRED").write_text(
        "Ten native-resolution candidates independently reconciled. Inspect QC0/floor/manual review records before further use.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

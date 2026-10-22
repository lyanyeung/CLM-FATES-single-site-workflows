#!/usr/bin/env python3
"""Same-release RH sensitivity for the seven humidity-blocked Stage07 sites.

Preserve Stage07 successes by hash and path. Rerun blocked sites separately;
only their reproduced unresolved rows may use RH. No new RH floor is added.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
BATCH = Path(__file__).resolve().parents[2]
HELPER = BATCH / "scripts/stage07/07_build_batch03_qcv5_candidates.py"
ENGINE = Path(__file__).with_name("qcv5_raw_rh.py")
DEFAULT_EXPERIMENT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BLOCKED = {"US-Kon", "US-Me2", "US-Me6", "US-MMS", "US-MtB", "US-NR1", "US-NR3"}
ORIGIN = "same_release_RH_at_retained_TA"
REVIEW_REASON = "same_release_RH_sensitivity_quality_unverified_review_required"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(2**20), b""): h.update(part)
    return h.hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def numeric(series):
    x = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    x[(~np.isfinite(x)) | (x <= -9990)] = np.nan
    return x


def preflight(old):
    if not (old / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Expected preserved incomplete Stage07 trial")
    manifest_file = old / "exact_input_manifest.json"
    manifest = json.loads(manifest_file.read_text())
    if manifest["algorithm"] != "BATCH03_HISTORICAL_QCV5_NATIVE_HH_HR_ADAPTATION": raise ValueError("Wrong Stage07 algorithm")
    pins = {Path(p).resolve(): h for p, h in manifest["input_sha256"].items()}
    if HELPER.resolve() not in pins: raise ValueError("Stage07 helper is not pinned by this trial")
    # Validate code before import and every raw/report input before any output.
    for path, expected in pins.items():
        print("INPUT SHA256:", path.name, flush=True)
        if sha(path) != expected: raise ValueError("Stage07 pinned input changed: " + str(path))
    out_manifest = old / "output_sha256.json"
    for relative, expected in json.loads(out_manifest.read_text()).items():
        path = (old / relative).resolve()
        if old not in path.parents or sha(path) != expected: raise ValueError("Stage07 output changed: " + relative)
        pins[path] = expected
    for path in (manifest_file, out_manifest, old / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"):
        pins[path] = sha(path)
    for path in (ENGINE, Path(__file__).resolve()): pins[path] = sha(path)
    preservation = json.loads((old / "input_preservation_check.json").read_text())
    if not preservation["unchanged"]: raise ValueError("Stage07 input preservation failed")
    helper = load(HELPER, "batch03_stage07_preserved")
    rows = helper.manifest_rows()
    info = {r["site"]: r for r in manifest["sites"]}
    states = pd.read_csv(old / "candidate_run_summary.csv", dtype=str, keep_default_na=False)
    if len(states) != 10 or states.site.duplicated().any() or set(states.site) != set(info): raise ValueError("Stage07 site summary mismatch")
    if set(states.loc[states.status.eq("FAIL"), "site"]) != BLOCKED: raise ValueError("Expected the five documented humidity-blocked sites")
    blockers, preserved = {}, []
    for row in rows:
        s = row["site"]
        item = info[s]
        if (item["release"], item["first_year"], item["last_year"]) != (row["package"], int(row["first_year"]), int(row["last_year"])):
            raise ValueError("Manifest selection differs from Stage07: " + s)
        record = states.loc[states.site.eq(s)].iloc[0]
        if s in BLOCKED:
            match = re.match(r"^(\d+) impossible humidity pairs require manual resolution; examples (.+)$", record.error)
            if not match: raise ValueError("Unsupported Stage07 failure type: " + s)
            blockers[s] = dict(records=int(match[1]), examples=ast.literal_eval(match[2]))
            if blockers[s]["records"] <= 0: raise ValueError("Empty blocker scope")
            print("BLOCKER SCOPE:", s, blockers[s]["records"], flush=True)
        else:
            if record.status != "CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED": raise ValueError("Unverified preserved site: " + s)
            audit_path = old / s / "forcing/qc_v5" / f"{s}_independent_audit.json"
            prior = json.loads(audit_path.read_text())
            force = old / s / "forcing/processed_v5" / f"{s}_CLM_forcing_{item['first_year']}_{item['last_year']}.csv"
            if force.resolve() not in pins or audit_path.resolve() not in pins: raise ValueError("Unpinned preserved candidate")
            preserved.append(dict(site=s, candidate_origin="PRESERVED_STAGE07", forcing_csv=str(force), forcing_sha256=pins[force.resolve()],
                                  status=prior["status"], RH_fallback_records=0))
            print("PRESERVE:", s, "SHA256=", pins[force.resolve()], flush=True)
    return helper, info, blockers, preserved, pins


def audit_attempts(item, out, expected, candidate_complete):
    site = item["site"]
    qc = out / site / "forcing/qc_v5"
    attempts_file = qc / f"{site}_native_RH_resolution_attempts.csv"
    attempts = pd.read_csv(attempts_file)
    if len(attempts) != expected["records"] or attempts.time.duplicated().any(): raise ValueError("Reproduced blocker scope count differs from Stage07")
    # Reproduce the original failure prefix, not just a total of unrelated rows.
    for row, (stamp, t, v) in zip(attempts.itertuples(), expected["examples"]):
        if pd.Timestamp(row.time) != pd.Timestamp(stamp) or not np.isclose(row.TA_before_fallback_C, t) or not np.isclose(row.VPD_before_fallback_hPa, v):
            raise ValueError("Reproduced blocker examples differ from Stage07")
    header = set(pd.read_csv(item["primary"], nrows=0).columns)
    cols = ["TIMESTAMP_START", "TA_F", "VPD_F"] + [c for c in ("RH", "RH_QC", "VPD_F_QC") if c in header]
    raw = pd.read_csv(item["primary"], usecols=cols, dtype={"TIMESTAMP_START": str})
    ids = attempts.source_csv_row.to_numpy(dtype=int) - 2
    if (ids < 0).any() or (ids >= len(raw)).any(): raise ValueError("Invalid original source CSV row")
    selected = raw.iloc[ids]
    stamps = pd.to_datetime(selected.TIMESTAMP_START.str.strip().str.replace(r"\.0$", "", regex=True), format="%Y%m%d%H%M")
    if not np.array_equal(stamps.to_numpy(), pd.to_datetime(attempts.time).to_numpy()): raise ValueError("RH source row/timestamp mismatch")
    rh = numeric(selected.RH) if "RH" in raw else np.full(len(attempts), np.nan)
    rhqc = numeric(selected.RH_QC) if "RH_QC" in raw else np.full(len(attempts), np.nan)
    qc0 = numeric(selected.VPD_F_QC) if "VPD_F_QC" in raw else np.full(len(attempts), np.nan)
    for actual, recorded in ((rh, attempts.RH_raw_pct), (rhqc, attempts.RH_QC_raw), (qc0, attempts.VPD_original_QC),
                             (numeric(selected.TA_F), attempts.TA_original_C), (numeric(selected.VPD_F), attempts.VPD_original_hPa)):
        if not np.isclose(actual, recorded, rtol=1e-10, atol=1e-9, equal_nan=True).all(): raise ValueError("Raw RH/value/QC provenance mismatch")
    eligible = attempts.decision.eq("CANDIDATE_RAW_RH").to_numpy()
    t, p = attempts.TA_before_fallback_C.to_numpy(), attempts.PA_before_fallback_kPa.to_numpy() * 1000
    with np.errstate(all="ignore"):
        es = 6.112 * np.exp(17.67 * t / (t + 243.5))
        vpd = es * (1 - rh / 100)
        ea = (es - vpd) * 100
        q = .622 * ea / (p - .378 * ea)
        implied_rh = 100 * (es - vpd) / es
    valid = (np.isfinite(rh) & (rh > 0) & (rh <= 100) & np.isfinite(t) & (t >= -80) & (t <= 65) &
             np.isfinite(p) & (p >= 50000) & (p <= 110000) & np.isfinite(vpd) & (vpd >= -.1) & (vpd <= 125) &
             np.isfinite(q) & (q > 0) & (q <= .08) & np.isfinite(implied_rh) & (implied_rh > 0) & (implied_rh <= 100.05))
    if not np.array_equal(eligible, valid): raise ValueError("RH reconstruction eligibility audit mismatch")
    if not np.isclose(attempts.candidate_VPD_hPa.to_numpy()[eligible], vpd[eligible], rtol=1e-10, atol=1e-9).all(): raise ValueError("RH-to-VPD formula mismatch")
    if candidate_complete:
        events = pd.read_csv(qc / f"{site}_replacement_events.csv")
        native = events.loc[events.final_source.eq(ORIGIN)]
        if set(pd.to_datetime(native.time)) != set(pd.to_datetime(attempts.loc[eligible, "time"])) or len(native) != int(eligible.sum()):
            raise ValueError("Native-RH changes escaped reproduced blocker scope")
        if not native.variable.eq("VPD_F").all(): raise ValueError("Raw-RH fallback changed a different variable")
        force = pd.read_csv(out / site / "forcing/processed_v5" / f"{site}_CLM_forcing_{item['first_year']}_{item['last_year']}.csv")
        force.index = pd.to_datetime(force.time)
        at = force.loc[pd.to_datetime(attempts.loc[eligible, "time"])]
        if not np.isclose(at.TA_USE, t[eligible], rtol=1e-10, atol=1e-9).all() or not np.isclose(at.PSRF, p[eligible], rtol=1e-10, atol=1e-9).all():
            raise ValueError("RH fallback did not preserve pre-fallback TA/PA")
        if not np.isclose(at.VPD_USE, vpd[eligible], rtol=1e-10, atol=1e-9).all(): raise ValueError("Candidate differs from raw-RH reconstruction")
        manual = pd.read_csv(qc / f"{site}_manual_review.csv")
        tagged = manual[manual.reason.eq(REVIEW_REASON)]
        if len(tagged) != int(eligible.sum()) or set(pd.to_datetime(tagged.time)) != set(pd.to_datetime(attempts.loc[eligible, "time"])):
            raise ValueError("Missing native-RH manual review entries")
    result = dict(site=site, reproduced_blockers=len(attempts), raw_RH_eligible=int(eligible.sum()), remaining=int((~eligible).sum()),
                  eligible_RH_QC_unavailable=int((eligible & ~np.isfinite(rhqc)).sum()),
                  eligible_original_VPD_QC0=int((eligible & (qc0 == 0)).sum()),
                  RH_quality_status="UNVERIFIED_SAME_RELEASE_RH", attempts_csv=str(attempts_file))
    save(qc / f"{site}_RH_provenance_audit.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage07-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()
    print("PYTHON:", sys.executable, "| numpy:", np.__version__, "| pandas:", pd.__version__, flush=True)
    old = args.stage07_root.expanduser().resolve()
    helper, info, blockers, selection, pins = preflight(old)
    print("STAGE08 PREFLIGHT: preserved={} blocked={} unresolved_records={}".format(
        len(selection), len(blockers), sum(r["records"] for r in blockers.values())), flush=True)
    if args.check:
        print("CHECK ONLY: no outputs created")
        return 0
    out = args.output_root.expanduser().resolve() if args.output_root else DEFAULT_EXPERIMENT / (
        "raw_RH_sensitivity_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    forbidden = {old, BATCH.resolve()}
    forbidden.update(Path(r["primary"]).parents[4] for r in info.values())
    forbidden.update(p.parent for p in pins if "/reports/" in str(p))
    if out.exists() or any(p == out or p in out.parents for p in forbidden): raise ValueError("Refusing existing/input-tree output destination")
    engine = load(ENGINE, "batch03_same_release_rh_sensitivity")
    baseline = helper.load_engine()
    if engine.HARD != baseline.HARD or engine.INTERPOLATE != baseline.INTERPOLATE: raise ValueError("QC-v5 baseline policy differs")
    engine.SITE_YEARS = {s: (r["first_year"], r["last_year"]) for s, r in info.items()}
    def exact(raw_folder, pattern):
        site = raw_folder.parent.parent.name
        if pattern == "*FLUXMET_HH*.csv": return Path(info[site]["primary"])
        if pattern == "*ERA5_HH*.csv": return Path(info[site]["era"])
        raise ValueError("Unexpected source selector")
    engine.get_one = exact
    out.mkdir(parents=True, exist_ok=False)
    marker = out / "INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM"
    marker.write_text("Three preserved inputs plus partial RH sensitivity. Inspect final selection and failures.\n")
    save(out / "exact_input_manifest.json", dict(stage07_root=str(old), algorithm="STAGE07_BLOCKERS_SAME_RELEASE_RAW_RH_SENSITIVITY",
        input_sha256={str(p): h for p, h in pins.items()}, sites=list(info.values()), blocker_scopes=blockers,
        rules=["Only reproduced Stage07 unresolved humidity rows can use RH; modify VPD only, preserve current TA/PA.",
            "Raw RH must be finite in (0,100]%; reconstructed VPD/QBOT must pass screens. No added RH floor or RH gap filling.",
            "RH QC/provenance remains unverified, even if a QC column exists. Every reconstruction requires manual review.",
            "All other QC-v5 rules, including inherited ERA-RH reconciliation, remain as in Stage07.",
            "Three successful Stage07 candidates are referenced by checksum, never rebuilt or copied."]))
    results = []
    for site in sorted(blockers):
        item, expected = info[site], blockers[site]
        print("\n========== RAW RH SENSITIVITY", site, "==========", flush=True)
        completed, error = False, ""
        try:
            engine.parse_site(site, Path(item["primary"]).parents[4], out, native_minutes=item["native_minutes"], standalone_era=True)
            completed = True
        except Exception as exc:
            error = str(exc)
        try:
            details = audit_attempts(item, out, expected, completed)
            if completed:
                stats = helper.independent_audit(item, out)
                stats.update(details)
                stats["status"] = "RAW_RH_SENSITIVITY_NUMERIC_OK_REVIEW_REQUIRED"
                selection.append(dict(site=site, candidate_origin="STAGE08_RAW_RH_SENSITIVITY", forcing_csv=stats["forcing_csv"],
                                      forcing_sha256=sha(Path(stats["forcing_csv"])), status=stats["status"], RH_fallback_records=details["raw_RH_eligible"]))
            else:
                stats = dict(**details, status="FAIL", error=error)
        except Exception as exc:
            stats = dict(site=site, status="FAIL", error=error + " | evidence audit: " + str(exc))
        results.append(stats)
        print("SITE RESULT:", site, stats["status"], "RH_eligible=", stats.get("raw_RH_eligible", "UNKNOWN"),
              "remaining=", stats.get("remaining", "UNKNOWN"), "error=", stats.get("error", ""), flush=True)
        pd.DataFrame(results).to_csv(out / "raw_RH_run_summary.csv", index=False)
    print("\nREVERIFY ALL INPUTS AND PRESERVED CANDIDATES", flush=True)
    changed = [str(p) for p, h in pins.items() if sha(p) != h]
    save(out / "input_preservation_check.json", dict(unchanged=not changed, changed_inputs=changed))
    selection.sort(key=lambda r: r["site"])
    save(out / "selected_candidates.json", dict(complete=len(selection) == 10 and not changed, candidates=selection,
        scope="Path/checksum selection only; same-release RH sensitivity and all QC0/floor changes require scientific review; no DATM or model approval."))
    pd.DataFrame(selection).to_csv(out / "selected_candidates.csv", index=False)
    save(out / "output_sha256.json", {str(p.relative_to(out)): sha(p) for p in out.rglob("*") if p.is_file() and p != marker})
    failed = [r["site"] for r in results if r["status"] == "FAIL"]
    print("\nSTAGE08 SUMMARY: preserved=3 sensitivity_pass={} failed={} selected={}/10 inputs_unchanged={}".format(len(blockers)-len(failed), len(failed), len(selection), not changed))
    columns = ["site", "status", "reproduced_blockers", "raw_RH_eligible", "remaining", "eligible_RH_QC_unavailable", "eligible_original_VPD_QC0", "error"]
    print(pd.DataFrame(results).reindex(columns=columns).to_string(index=False))
    print("SENSITIVITY OUTPUT:", out)
    print("Stage07 trial and incomplete marker are preserved. No DATM, case changes or model jobs.")
    if failed or changed:
        print("INCOMPLETE sensitivity marker retained; failed:", ", ".join(failed))
        return 2
    marker.unlink()
    (out / "COMPLETE_TEN_SELECTED_CANDIDATES_REVIEW_REQUIRED").write_text("Three preserved Stage07 candidates and seven raw-RH sensitivity candidates; not scientifically approved.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

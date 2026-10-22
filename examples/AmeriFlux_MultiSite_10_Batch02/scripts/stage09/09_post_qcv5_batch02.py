#!/usr/bin/env python3
"""Batch02 Post-v5: numeric/provenance audit, then extremes/source review.

Follows Batch01 Stages21/22, using the exact ten Stage08 selections and their
native HH/HR intervals. Writes new reports only. Findings never repair data.
"""
import argparse
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
HELPER = BATCH / "scripts/stage07/07_build_batch02_qcv5_candidates.py"
REPORTS = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports")
SITES = {"US-BZS", "US-CMW", "US-EML", "US-GLE", "US-Ha1", "US-Ho1", "US-Ho2", "US-Ho3", "US-ICh", "US-ICt"}
MET = ("TA", "VPD", "PA", "SW_IN", "LW_IN", "WS", "P")
FINAL = ("TA_USE", "VPD_USE", "TBOT", "QBOT", "PSRF", "FSDS", "FLDS", "WIND", "PRECTmms")
BATCH01_REFERENCE_BLOBS = {
    "stage21_numeric_ledger": "e7a283cc55cfdaf4d52f34a7bfbede6e2dae953a",
    "stage22_extremes_sources_v2": "57507500b410f5c693fe3433d6f7f0e276307eed",
    "stage23_postv5_runner": "a0429f7112affa32668ee2aad299f9829afff66d",
}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(2**20), b""): h.update(data)
    return h.hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def preflight(root):
    if not (root / "COMPLETE_TEN_SELECTED_CANDIDATES_REVIEW_REQUIRED").is_file():
        raise ValueError("Stage08 ten-site selection is incomplete; resolve remaining failures before Post-v5")
    selected = json.loads((root / "selected_candidates.json").read_text())
    manifest = json.loads((root / "exact_input_manifest.json").read_text())
    preservation = json.loads((root / "input_preservation_check.json").read_text())
    if not selected["complete"] or not preservation["unchanged"]:
        raise ValueError("Stage08 selection or input preservation did not pass")
    if manifest["algorithm"] != "STAGE07_BLOCKERS_SAME_RELEASE_RAW_RH_SENSITIVITY": raise ValueError("Wrong Stage08 trial")
    pins = {Path(p).resolve(): digest for p, digest in manifest["input_sha256"].items()}
    if HELPER.resolve() not in pins: raise ValueError("Numeric audit helper is not pinned")
    for relative, digest in json.loads((root / "output_sha256.json").read_text()).items():
        path = (root / relative).resolve()
        if root not in path.parents: raise ValueError("Output manifest path escaped Stage08 root")
        pins[path] = digest
    required = [root / name for name in ("selected_candidates.json", "exact_input_manifest.json", "input_preservation_check.json")]
    if any(p not in pins for p in required): raise ValueError("Stage08 selection metadata is not checksum-pinned")
    for path in (root / "output_sha256.json", root / "COMPLETE_TEN_SELECTED_CANDIDATES_REVIEW_REQUIRED", Path(__file__).resolve()):
        pins[path] = sha(path)
    for path, digest in pins.items():
        if sha(path) != digest: raise ValueError("Post-v5 input checksum mismatch: " + str(path))
    info = {r["site"]: r for r in manifest["sites"]}
    choices = selected["candidates"]
    if len(choices) != 10 or len({r["site"] for r in choices}) != 10 or set(info) != SITES or {r["site"] for r in choices} != SITES:
        raise ValueError("Expected exactly the ten Batch02 site selections")
    inventory_paths = [p for p in pins if p.name == "source_inventory.json"]
    if len(inventory_paths) != 1: raise ValueError("Expected one pinned Stage04b source inventory")
    inventory = json.loads(inventory_paths[0].read_text())
    if inventory["failures"] or len(inventory["completed"]) != 20: raise ValueError("Incomplete source inventory")
    spec_by_path = {Path(r["file"]).resolve(): r for r in inventory["completed"]}
    jobs = []
    origins = []
    for choice in sorted(choices, key=lambda r: r["site"]):
        site = choice["site"]
        item = info[site]
        origin = choice["candidate_origin"]
        if origin not in ("PRESERVED_STAGE07", "STAGE08_RAW_RH_SENSITIVITY"): raise ValueError("Unknown candidate origin")
        trial = Path(manifest["stage07_root"]).resolve() if origin == "PRESERVED_STAGE07" else root
        force = trial / site / "forcing/processed_v5" / f"{site}_CLM_forcing_{item['first_year']}_{item['last_year']}.csv"
        if force != Path(choice["forcing_csv"]).resolve() or force not in pins or pins[force] != choice["forcing_sha256"]:
            raise ValueError("Candidate selection path/hash mismatch: " + site)
        if item["native_minutes"] != (60 if site == "US-Ha1" else 30): raise ValueError("Unexpected native interval")
        for kind in ("primary", "era"):
            path = Path(item[kind]).resolve()
            spec = spec_by_path[path]
            if (spec["site"], spec["first_year"], spec["last_year"], spec["interval_minutes"]) != (
                    site, item["first_year"], item["last_year"], item["native_minutes"]):
                raise ValueError("Candidate metadata differs from pinned source inventory")
            if pins.get(path) != spec["sha256"]: raise ValueError("Source inventory hash differs from selection")
        qc = trial / site / "forcing/qc_v5"
        for name in ("replacement_events.csv", "manual_review.csv", "status.json"):
            if (qc / f"{site}_{name}").resolve() not in pins: raise ValueError("Unpinned provenance file: " + site)
        jobs.append((item, trial, force))
        origins.append(origin)
        print("CHECK OK", site, "native_minutes=", item["native_minutes"], origin, flush=True)
    if origins.count("PRESERVED_STAGE07") != 5: raise ValueError("Expected five preserved and five sensitivity candidates")
    return jobs, pins


def read_frame(path, columns, item, raw=False):
    time_column = "TIMESTAMP_START" if raw else "time"
    header = set(pd.read_csv(path, nrows=0).columns)
    if not set(columns).issubset(header): raise ValueError("Missing columns in " + str(path))
    frame = pd.read_csv(path, usecols=columns, dtype={time_column: str})
    text = frame.pop(time_column).str.strip()
    time = pd.to_datetime(text.str.replace(r"\.0$", "", regex=True), format="%Y%m%d%H%M", errors="raise") if raw else pd.to_datetime(text, errors="raise")
    frame.insert(0, "time", time)
    first, end_year, step = item["first_year"], item["last_year"], item["native_minutes"]
    frame = frame.loc[time.dt.year.between(first, end_year) & ~((time.dt.month == 2) & (time.dt.day == 29))].reset_index(drop=True)
    expected = pd.date_range(f"{first}-01-01", f"{end_year+1}-01-01", freq=f"{step}min", inclusive="left")
    expected = expected[~((expected.month == 2) & (expected.day == 29))]
    if len(frame) != len(expected) or not np.array_equal(frame.time.to_numpy(), expected.to_numpy()): raise ValueError("Wrong native NO_LEAP timeline: " + str(path))
    for col in frame.columns.drop("time"):
        x = pd.to_numeric(frame[col], errors="coerce")
        frame[col] = x.where(np.isfinite(x) & (x > -9990))
    return frame


def jump(values, limit):
    return np.r_[False, np.isfinite(np.diff(values)) & (np.abs(np.diff(values)) > limit)]


def spike(values, limit):
    left, right = np.r_[np.nan, np.diff(values)], np.r_[np.diff(values), np.nan]
    return np.isfinite(left) & np.isfinite(right) & (np.abs(left) > limit) & (np.abs(right) > limit) & (np.sign(left) != np.sign(right))


def science_review(item, trial, force_path):
    site, step = item["site"], item["native_minutes"]
    header = set(pd.read_csv(item["primary"], nrows=0).columns)
    qcols = [v + "_F_QC" for v in MET if v + "_F_QC" in header]
    raw = read_frame(Path(item["primary"]), ["TIMESTAMP_START", *[v + "_F" for v in MET], *qcols], item, True)
    era = read_frame(Path(item["era"]), ["TIMESTAMP_START", *[v + "_ERA" for v in MET]], item, True)
    final = read_frame(force_path, ["time", *FINAL], item)
    events = pd.read_csv(trial / site / "forcing/qc_v5" / f"{site}_replacement_events.csv")
    qc0 = events.loc[pd.to_numeric(events.official_qc, errors="coerce").eq(0)].copy()
    old_t, new_t, era_t = raw.TA_F.to_numpy(), final.TA_USE.to_numpy(), era.TA_ERA.to_numpy()
    new_v, pressure = final.VPD_USE.to_numpy(), final.PSRF.to_numpy()
    rain = final.PRECTmms.to_numpy() * (step * 60)
    qc_t = raw.TA_F_QC.to_numpy() if "TA_F_QC" in raw else np.full(len(raw), np.nan)
    qc_v = raw.VPD_F_QC.to_numpy() if "VPD_F_QC" in raw else np.full(len(raw), np.nan)
    with np.errstate(all="ignore"):
        es = 6.112 * np.exp(np.clip(17.67 * new_t / (new_t + 243.5), -40, 40))
        rh = 100 * (es - new_v) / es
    bin_rh = rh.copy()
    for edge in (1, 5, 10): bin_rh[np.isclose(bin_rh, edge, atol=1e-9, rtol=0)] = edge
    # Same HH thresholds as Batch01; HR uses the equivalent nominal hourly rate.
    scale = step / 30
    old_jump, new_jump = jump(old_t, 8 * scale), jump(new_t, 8 * scale)
    qc_switch = np.r_[False, np.isfinite(qc_t[1:]) & np.isfinite(qc_t[:-1]) & (qc_t[1:] != qc_t[:-1])]
    source_t = np.array(["SOURCE_QC=" + (str(x) if np.isfinite(x) else "MISSING") for x in qc_t], dtype=object)
    source_v = np.array(["SOURCE_QC=" + (str(x) if np.isfinite(x) else "MISSING") for x in qc_v], dtype=object)
    positions = {pd.Timestamp(t): i for i, t in enumerate(final.time)}
    by_time, qc0_by_time = {}, {}
    for event in events.to_dict("records"):
        stamp = pd.Timestamp(event["time"])
        i = positions[stamp]
        by_time.setdefault(stamp, []).append(event)
        if event["official_qc"] == 0: qc0_by_time.setdefault(stamp, []).append(event)
        if event["variable"] == "TA_F": source_t[i] = event["final_source"]
        if event["variable"] == "VPD_F": source_v[i] = event["final_source"]
    ta_switch = np.r_[False, source_t[1:] != source_t[:-1]]
    vpd_switch = np.r_[False, source_v[1:] != source_v[:-1]]
    vpd_jump = jump(new_v, 5 * scale)
    flags = {
        "NEW_TA_NATIVE_STEP_RATE_GT16C_H": new_jump & ~old_jump,
        "CANDIDATE_TA_NATIVE_STEP_RATE_GT16C_H": new_jump,
        "ISOLATED_TA_SPIKE_RATE_GT16C_H": spike(new_t, 8 * scale),
        "TA_VS_ERA_GT15C": np.isfinite(era_t) & (np.abs(new_t - era_t) > 15),
        "TA_EXTREME_LT_MINUS25_OR_GT45": (new_t < -25) | (new_t > 45),
        "TA_ORIGINAL_QC_SWITCH_WITH_JUMP": qc_switch & new_jump,
        "TA_FINAL_SOURCE_SWITCH_WITH_JUMP": ta_switch & new_jump,
        "VPD_NATIVE_STEP_RATE_GT10HPA_H": vpd_jump,
        "VPD_FINAL_SOURCE_SWITCH_WITH_JUMP": vpd_switch & vpd_jump,
        "PSRF_NATIVE_STEP_RATE_GT10000PA_H": jump(pressure, 5000 * scale),
        "PRECIP_RATE_GT36MM_H": rain > 18 * scale,
        "POSITIVE_RH_LT1PCT": (bin_rh > 0) & (bin_rh < 1),
        "RH_NONPOSITIVE": ~np.isfinite(rh) | (rh <= 0),
        "QBOT_OUTSIDE_0_TO008": ~np.isfinite(final.QBOT.to_numpy()) | (final.QBOT.to_numpy() < 0) | (final.QBOT.to_numpy() > .08),
    }
    touched = np.logical_or.reduce(list(flags.values()))
    touched |= final.time.isin(qc0_by_time).to_numpy()
    details = []
    episode, previous_flagged_time = 0, None
    for i in np.flatnonzero(touched):
        stamp = pd.Timestamp(final.time.iloc[i])
        if previous_flagged_time is None or (stamp - previous_flagged_time).total_seconds() > 7200: episode += 1
        previous_flagged_time = stamp
        labels = [name for name, mask in flags.items() if mask[i]]
        if stamp in qc0_by_time: labels.append("SOURCE_QC0_EDIT")
        details.append(dict(site=site, episode_id=episode, timestamp_local=str(stamp), native_minutes=step,
            review_flags="|".join(labels), original_TA_C=old_t[i], candidate_TA_C=new_t[i], ERA_TA_C=era_t[i],
            original_TA_QC=qc_t[i], original_VPD_QC=qc_v[i], original_VPD_hPa=raw.VPD_F.iloc[i],
            candidate_VPD_hPa=new_v[i], candidate_RH_pct=rh[i], candidate_PSRF_Pa=pressure[i],
            original_rain_mm_native=raw.P_F.iloc[i], candidate_rain_mm_native=rain[i], ERA_rain_mm_native=era.P_ERA.iloc[i],
            final_TA_source=source_t[i], final_VPD_source=source_v[i],
            source_clock_gap_minutes=(stamp - pd.Timestamp(final.time.iloc[i-1])).total_seconds()/60 if i else np.nan,
            modification_variables="|".join(sorted(r["variable"] for r in by_time.get(stamp, []))),
            QC0_modification_count=len(qc0_by_time.get(stamp, [])), science_decision="REVIEW_NO_AUTOMATIC_REPLACEMENT"))
    annual = []
    years = final.time.dt.year.to_numpy()
    for year in range(item["first_year"], item["last_year"] + 1):
        take = years == year
        annual.append(dict(site=site, year=year, native_minutes=step, **{name: int((mask & take).sum()) for name, mask in flags.items()}))
    summary = {name: int(mask.sum()) for name, mask in flags.items()}
    summary.update(site=site, native_minutes=step, records=len(final), QC0_edits=len(qc0), review_timestamps=len(details), review_episodes=episode,
        positive_RH_1_to5=int(((bin_rh >= 1) & (bin_rh < 5)).sum()), positive_RH_5_to10=int(((bin_rh >= 5) & (bin_rh < 10)).sum()),
        native_rain_threshold_mm=18 * scale, native_TA_step_threshold_C=8 * scale,
        science_status="REVIEW_PRE_DATM", RH_bin_tolerance_pct=1e-9)
    qc0.insert(0, "timestamp_local", pd.to_datetime(qc0.time).astype(str))
    qc0["science_decision"] = "REVIEW_ORIGINAL_SOURCE_QC0_CHANGE"
    return summary, pd.DataFrame(details, columns=["site", "episode_id", "timestamp_local", "native_minutes", "review_flags", "original_TA_C", "candidate_TA_C", "ERA_TA_C", "original_TA_QC", "original_VPD_QC", "original_VPD_hPa", "candidate_VPD_hPa", "candidate_RH_pct", "candidate_PSRF_Pa", "original_rain_mm_native", "candidate_rain_mm_native", "ERA_rain_mm_native", "final_TA_source", "final_VPD_source", "source_clock_gap_minutes", "modification_variables", "QC0_modification_count", "science_decision"]), qc0, annual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-root", required=True, type=Path)
    parser.add_argument("--report-root", type=Path, default=REPORTS)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    root = args.selection_root.expanduser().resolve()
    jobs, pins = preflight(root)
    print("POST-V5 PREFLIGHT: 10/10 exact candidates, HH/HR and input SHA256 verified", flush=True)
    if args.check:
        print("CHECK ONLY: no reports or candidate writes")
        return 0
    dest = args.report_root.expanduser().resolve() / ("stage09_postqcv5_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    if any(parent == dest or parent in dest.parents for parent in {p.parent for p in pins} | {root, BATCH.resolve()}):
        raise ValueError("Report destination is inside an input tree")
    dest.mkdir(parents=True, exist_ok=False)
    numeric_dir = dest / "numeric_audits"
    numeric_dir.mkdir()
    save(dest / "input_manifest.json", dict(selection_root=str(root), input_sha256={str(p): h for p, h in pins.items()},
        Batch01_reference_git_blobs=BATCH01_REFERENCE_BLOBS,
        workflow="Batch01 Stage21 numeric/ledger then Stage22 science/source checks, adapted to Batch02 selection and native HH/HR",
        rate_thresholds={"TA_C_per_nominal_hour": 16, "VPD_hPa_per_nominal_hour": 10, "PSRF_Pa_per_nominal_hour": 10000, "P_mm_per_nominal_hour": 36},
        scope="Reports only. HR rates do not resolve within-hour events. Cold/dry extremes and QC0 flags are not automatic repair rules."))
    spec = importlib.util.spec_from_file_location("batch02_postv5_numeric", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    # The checksum-pinned helper's only audit write is redirected to this new report.
    def report_only_writer(path, obj):
        if path.name != obj["site"] + "_independent_audit.json": raise ValueError("Unexpected numeric helper write")
        save(numeric_dir / path.name, obj)
    helper.write_json = report_only_writer
    numeric_rows, science_rows, event_frames, qc0_frames, annual_rows = [], [], [], [], []
    failed = []
    for item, trial, forcing in jobs:
        site = item["site"]
        print("\nPOST-V5 NUMERIC + LEDGER:", site, flush=True)
        try:
            stats = helper.independent_audit(item, trial)
            numeric_rows.append(stats)
            print("POST-V5 EXTREMES + SOURCES:", site, flush=True)
            summary, events, qc0, annual = science_review(item, trial, forcing)
            if summary["QC0_edits"] != stats["changed_QC0_records"]: raise ValueError("Numeric/science QC0 count mismatch")
            if summary["RH_NONPOSITIVE"] or summary["QBOT_OUTSIDE_0_TO008"]: raise ValueError("Residual impossible humidity")
            science_rows.append(summary); event_frames.append(events); qc0_frames.append(qc0); annual_rows.extend(annual)
            print("  VERIFIED", site, "QC0_edits=", summary["QC0_edits"], "new_TA_jumps=", summary["NEW_TA_NATIVE_STEP_RATE_GT16C_H"],
                  "positive_RH_lt1=", summary["POSITIVE_RH_LT1PCT"], "review_times=", summary["review_timestamps"], flush=True)
        except Exception as exc:
            failed.append(dict(site=site, error=str(exc)))
            print("  POST-V5 FAILURE:", site, str(exc), flush=True)
    pd.DataFrame(numeric_rows).to_csv(dest / "numeric_and_ledger_summary.csv", index=False)
    pd.DataFrame(science_rows).to_csv(dest / "site_extremes_and_sources_summary.csv", index=False)
    pd.DataFrame(annual_rows).to_csv(dest / "annual_extreme_counts.csv", index=False)
    if event_frames: pd.concat(event_frames, ignore_index=True).to_csv(dest / "timestamped_event_context.csv", index=False)
    if qc0_frames: pd.concat(qc0_frames, ignore_index=True).to_csv(dest / "all_original_QC0_edits.csv", index=False)
    pd.DataFrame(failed, columns=["site", "error"]).to_csv(dest / "site_failures.csv", index=False)
    changed = [str(p) for p, digest in pins.items() if sha(p) != digest]
    save(dest / "input_preservation_check.json", dict(unchanged=not changed, changed_inputs=changed))
    result = dict(numeric_pass=10-len(failed), failed=len(failed), inputs_unchanged=not changed,
        QC0_edits=sum(r["QC0_edits"] for r in science_rows), review_timestamps=sum(r["review_timestamps"] for r in science_rows),
        new_TA_native_rate_jumps=sum(r["NEW_TA_NATIVE_STEP_RATE_GT16C_H"] for r in science_rows),
        positive_RH_lt1=sum(r["POSITIVE_RH_LT1PCT"] for r in science_rows),
        science_status="REVIEW_PRE_DATM", scope="Post-v5 reports only; no source/candidate/DATM/surface/case/job changes")
    save(dest / "postv5_summary.json", result)
    print("\nPOST-V5 SUMMARY:", json.dumps(result), flush=True)
    print("REPORT DIR:", dest, flush=True)
    print("No source or candidate modified. Numeric PASS does not approve scientific flags, ZBOT, surface/PFT or model use.")
    return 2 if failed or changed else 0


if __name__ == "__main__":
    raise SystemExit(main())

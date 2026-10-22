#!/usr/bin/env python3
"""Batch03 Stage08b: diagnose RH holds without changing any forcing.

Reads the exact incomplete Stage08 trial and verifies its report SHA256s.
Does not authorize use of same-release RH or ERA5 as verified sensor data.
--check: read-only summary. --run: write ONLY a new isolated report folder.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

EXPECTED = {
    "US-Kon": 359, "US-MMS": 22, "US-Me2": 4, "US-Me6": 1,
    "US-MtB": 15, "US-NR1": 173, "US-NR3": 1699,
}
PRESERVED = {"US-MOz", "US-Mpj", "US-NC2"}
EXP = "AmeriFlux_MultiSite_10_Batch03"
STAGE07 = "qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE08 = "raw_RH_sensitivity_20261022T025645Z_3c43eb8b"
REQUIRED = [
    "site", "time", "source_csv_row", "TA_before_fallback_C",
    "VPD_before_fallback_hPa", "PA_before_fallback_kPa",
    "RH_raw_pct", "RH_QC_raw", "VPD_original_QC", "TA_ERA_C",
    "VPD_ERA_hPa", "ERA_RH_pct", "decision", "RH_quality_status",
]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def checked_file(root, ledger, relative):
    if relative not in ledger:
        raise ValueError("File not SHA256-pinned by Stage08: " + relative)
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file():
        raise ValueError("Missing or unsafe report path: " + relative)
    if sha(path) != ledger[relative]:
        raise ValueError("Stage08 report changed since run: " + relative)
    return path


def num(series):
    return pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage08-root", required=True, type=Path)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--run", action="store_true")
    args = p.parse_args()
    root = args.stage08_root.expanduser().resolve()
    if (root.name != STAGE08 or root.parent.name != EXP or not root.is_dir()
            or not (root / "INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM").is_file()):
        p.error("Expected the exact preserved incomplete Batch03 Stage08 trial")
    ledger = json.loads((root / "output_sha256.json").read_text(encoding="utf-8"))
    manifest = json.loads(checked_file(root, ledger, "exact_input_manifest.json").read_text())
    if (manifest["algorithm"] != "STAGE07_BLOCKERS_SAME_RELEASE_RAW_RH_SENSITIVITY"
            or Path(manifest["stage07_root"]).resolve().name != STAGE07):
        raise ValueError("Unexpected Stage07/08 provenance")
    preserve = json.loads(checked_file(root, ledger, "input_preservation_check.json").read_text())
    if preserve.get("unchanged") is not True:
        raise ValueError("Stage08 input preservation did not pass")
    selected = json.loads(checked_file(root, ledger, "selected_candidates.json").read_text())
    selected_sites = {row["site"] for row in selected["candidates"]}
    if selected_sites != PRESERVED or selected.get("complete") is not False:
        raise ValueError("Unexpected selected candidate scope")
    summary = pd.read_csv(checked_file(root, ledger, "raw_RH_run_summary.csv"),
                          dtype=str, keep_default_na=False)
    if len(summary) != 7 or set(summary.site) != set(EXPECTED):
        raise ValueError("Unexpected failed-site inventory")
    if not summary.status.eq("FAIL").all():
        raise ValueError("Expected all seven RH sensitivity sites to remain blocked")
    frames, totals = [], []
    for site, expected in EXPECTED.items():
        relative = f"{site}/forcing/qc_v5/{site}_native_RH_resolution_attempts.csv"
        frame = pd.read_csv(checked_file(root, ledger, relative),
                            dtype=str, keep_default_na=False)
        if any(name not in frame.columns for name in REQUIRED):
            raise ValueError("Required RH attempt evidence missing: " + site)
        if len(frame) != expected or frame.source_csv_row.duplicated().any():
            raise ValueError("Stage08 blocker count/row IDs mismatch: " + site)
        if not frame.site.eq(site).all():
            raise ValueError("Attempt ledger contains wrong site: " + site)
        if not frame.RH_quality_status.eq("UNVERIFIED_SAME_RELEASE_RH").all():
            raise ValueError("Unexpected RH provenance status: " + site)
        provenance_rel = f"{site}/forcing/qc_v5/{site}_RH_provenance_audit.json"
        provenance = json.loads(checked_file(root, ledger, provenance_rel).read_text())
        eligible = frame.decision.eq("CANDIDATE_RAW_RH")
        unresolved = ~eligible
        if (int(provenance["reproduced_blockers"]) != expected
                or int(provenance["raw_RH_eligible"]) != int(eligible.sum())
                or int(provenance["remaining"]) != int(unresolved.sum())):
            raise ValueError("RH audit and attempted-event counts differ: " + site)
        subset = summary.loc[summary.site.eq(site)].iloc[0]
        if (int(subset.raw_RH_eligible) != int(eligible.sum())
                or int(subset.remaining) != int(unresolved.sum())):
            raise ValueError("Run summary and attempt count mismatch: " + site)
        if int(provenance["eligible_RH_QC_unavailable"]) != int(eligible.sum()):
            raise ValueError("Review RH_QC provenance; expected all candidates to be unverified: " + site)

        t = num(frame["TA_before_fallback_C"])
        v = num(frame["VPD_before_fallback_hPa"])
        raw_rh = num(frame["RH_raw_pct"])
        era_rh = num(frame["ERA_RH_pct"])
        era_t = num(frame["TA_ERA_C"])
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            es = 6.112 * np.exp(np.clip(17.67 * t / (t + 243.5), -40, 40))
            ea = es - v
        frame["site_es_water_hPa"] = es
        frame["site_ea_implied_hPa"] = ea
        frame["site_ea_nonpositive"] = np.isfinite(ea) & (ea <= 0)
        frame["TA_below_zero_C"] = np.isfinite(t) & (t < 0)
        frame["ERA_RH_outside_0_100_or_missing"] = (
            ~np.isfinite(era_rh) | (era_rh <= 0) | (era_rh > 100.05))
        frame["TA_site_minus_ERA_C"] = t - era_t
        frame["RH_raw_missing"] = ~np.isfinite(raw_rh)
        frame["RH_raw_not_in_0_100"] = np.isfinite(raw_rh) & (
            (raw_rh <= 0) | (raw_rh > 100))
        frame["year"] = pd.to_datetime(frame.time, errors="raise").dt.year
        frames.append(frame)
        counter = Counter(frame.loc[unresolved, "decision"])
        totals.append(dict(site=site, blockers=expected,
            RH_eligible=int(eligible.sum()), remaining=int(unresolved.sum()),
            missing_raw_RH=int(frame.loc[unresolved, "RH_raw_missing"].sum()),
            raw_RH_outside_0_100=int(frame.loc[unresolved, "RH_raw_not_in_0_100"].sum()),
            cold_remaining=int(frame.loc[unresolved, "TA_below_zero_C"].sum()),
            nonpositive_ea_remaining=int(frame.loc[unresolved, "site_ea_nonpositive"].sum()),
            invalid_ERA_RH_remaining=int(
                frame.loc[unresolved, "ERA_RH_outside_0_100_or_missing"].sum()),
            QC0_eligible=int((num(frame.VPD_original_QC)[eligible] == 0).sum()),
            **{f"hold_{key}": int(count) for key, count in counter.items()}))
        print(f"{site:<7} blocker={expected:4d} RH_eligible={int(eligible.sum()):4d}"
              f" unresolved={int(unresolved.sum()):4d} reasons={dict(counter)}", flush=True)
    all_rows = pd.concat(frames, ignore_index=True)
    total = int(all_rows.decision.ne("CANDIDATE_RAW_RH").sum())
    if len(all_rows) != 2273 or total != 1924:
        raise ValueError("Expected exactly 2273 input blockers and 1924 unresolved")
    print("STAGE08B PREFLIGHT: 7/7 failed sites; 2273 traced blockers;"
          " 349 RH-eligible sensitivity rows; 1924 unresolved; RH_QC unverified", flush=True)
    if args.check:
        print("CHECK ONLY: no report files, forcing or model jobs written")
        return 0

    report_root = root.parent / "reports"
    if not report_root.is_dir() or report_root.is_symlink():
        raise ValueError("Batch03 reports directory is absent or unsafe")
    out = report_root / ("stage08b_rh_cause_" +
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    pd.DataFrame(totals).fillna(0).to_csv(out / "site_hold_summary.csv", index=False)
    all_rows.to_csv(out / "all_original_blocker_evidence.csv", index=False)
    unresolved = all_rows.loc[all_rows.decision.ne("CANDIDATE_RAW_RH")].copy()
    unresolved.to_csv(out / "unresolved_rh_records.csv", index=False)
    unresolved.groupby(["site", "year", "decision"]).size().rename(
        "records").reset_index().to_csv(out / "unresolved_by_year_and_reason.csv", index=False)
    (out / "diagnostic_scope.json").write_text(json.dumps({
        "stage08_root": str(root), "input_sha256": sha(root / "output_sha256.json"),
        "input_blocks": 2273, "rh_numerically_eligible": 349,
        "remaining": 1924,
        "scope": "Evidence-only classification; no RH/ERA5 replacement approved.",
        "limitations": [
            "RH data are same-release with no RH_QC on all eligible samples.",
            "Saturation formula uses liquid water; cold-season vapor-pressure"
            " discrepancy does not independently identify the faulty source field.",
            "ERA5 and primary data may share underlying meteorological inputs.",
            "This audit does not recheck the original raw CSV independently;"
            " Stage07/08 immutable input attestations are relied upon.",
            "No candidate, forcing, DATM, case or Slurm job is changed."]},
        indent=2) + "\n", encoding="utf-8")
    print("STAGE08B SUMMARY: 7/7 sites; remaining=1924; report_only=True")
    print("REPORT DIR:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

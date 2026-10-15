#!/usr/bin/env python3
"""ES-LJu suspected -40 C air-temperature artifact: isolated v6 trial.

--check: read-only audit on the exact pinned official source.
--run: perform candidate TA substitutions IN MEMORY, then rerun the existing
        eight-site QC-v5 algorithm on original VPD and all other raw variables.

Crucial: no original FLUXNET csv, existing 13-site v5 candidate, DATM, CESM case,
spin-up, surface file, or other site's forcing is modified. Output is a NEW
isolated experiment. ERA substitution is a TRIAL, not an endorsed correction.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SITE = "ES-LJu"
RELEASE = "EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1"
FIRST, LAST = 2004, 2024
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DEFAULT_OUT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_qc_v6_ES-LJu_TA40_trial_20261014")
DEFAULT_V5 = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_qc_v5_candidate_20261014")
EXPECTED_REFERENCE_SHA = "61be3c46b69ee77739019fab499c94dd1fc1f66a77b1c830815e33baf5351a35"
COLS = ["TIMESTAMP_START", "TA_F", "TA_F_QC", "TA_ERA", "VPD_F", "VPD_F_QC", "VPD_ERA"]
OPTIONAL_CONTEXT_COLS = ["TA_F_MDS", "TA_F_MDS_QC", "RH"]


def find_exact(directory, pattern):
    matches = list(directory.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {pattern} in {directory}; got {len(matches)}")
    return matches[0].resolve()


def ts_strings(x):
    return x.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def sat_hpa(t):
    return 6.112 * np.exp(17.67 * t / (t + 243.5))


def check_reference(path):
    if not path.is_file():
        raise RuntimeError(f"Missing eight-site QC-v5 reference: {path}")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != EXPECTED_REFERENCE_SHA:
        raise RuntimeError(f"Reference v5 SHA256 changed: {sha}. Do not silently change the QC method.")
    return sha


def read_audit(primary):
    header = set(pd.read_csv(primary, nrows=0).columns)
    missing = sorted(set(COLS) - header)
    if missing:
        raise RuntimeError(f"Official source missing key fields: {missing}")
    read_cols = COLS + [c for c in OPTIONAL_CONTEXT_COLS if c in header]
    x = pd.read_csv(primary, usecols=read_cols, low_memory=False,
                    dtype={"TIMESTAMP_START": "str"})
    x["timestamp"] = ts_strings(x["TIMESTAMP_START"])
    if x.timestamp.duplicated().any():
        raise RuntimeError("Duplicate official source timestamps")
    years = pd.to_numeric(x.timestamp.str.slice(0, 4), errors="raise")
    x = x.loc[years.between(FIRST, LAST)].copy()
    for c in [c for c in x.columns if c not in ("TIMESTAMP_START", "timestamp")]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
        x.loc[x[c] <= -9990, c] = np.nan
    # Site-specific, strong anomaly criterion; NEVER generalize it to other sites.
    x["suspect_cold"] = x.TA_F.lt(-25)
    x["strong_TA40_artifact"] = (x["suspect_cold"] & x.TA_ERA.gt(-10)
                                 & (x.TA_ERA - x.TA_F).ge(25)
                                 & x.TA_ERA.between(-20, 55))
    strong = x[x.strong_TA40_artifact].copy()
    strong["year"] = strong.timestamp.str.slice(0, 4)
    strong["temperature_difference_C"] = strong.TA_ERA - strong.TA_F
    strong["original_RH_pct"] = 100 * (1 - strong.VPD_F / sat_hpa(strong.TA_F))
    strong["RH_if_ERA_T_and_original_VPD_pct"] = 100 * (1 - strong.VPD_F / sat_hpa(strong.TA_ERA))
    strong["candidate_TA_F_C"] = strong.TA_ERA
    strong["candidate_TA_F_QC"] = 2
    strong["decision"] = "TRIAL_only_use_FLUXNET_downscaled_TA_ERA_for_TA40_artifact"
    return x, strong


def preflight(source_root, ref_path, out):
    release_dir = source_root / SITE / "forcing/raw" / RELEASE
    if not release_dir.is_dir():
        raise RuntimeError(f"Missing pinned release: {release_dir}")
    primary = find_exact(release_dir, "*FLUXMET_HH*.csv")
    companion = find_exact(release_dir, "*ERA5_HH*.csv")
    if out == source_root or out == source_root.parent or source_root in out.parents:
        raise RuntimeError("REFUSED: candidate output is inside the original MY_EC_SITE hierarchy")
    if source_root.resolve() == out.resolve():
        raise RuntimeError("Source and output cannot match")
    sha = check_reference(ref_path)
    return primary, companion, sha


class ReadCSVProxy:
    """Only mask TA_F in-memory for the pinned primary file, preserving other fields."""
    def __init__(self, pandas_module, primary, substitutions):
        self._pd = pandas_module
        self.primary = primary.resolve()
        self.subs = substitutions
        self.times_touched = set()
        self.calls_touched = 0

    def __getattr__(self, name):
        return getattr(self._pd, name)

    def read_csv(self, filepath_or_buffer, *args, **kwargs):
        result = self._pd.read_csv(filepath_or_buffer, *args, **kwargs)
        if not isinstance(filepath_or_buffer, (str, Path)):
            return result
        if Path(filepath_or_buffer).resolve() != self.primary:
            return result
        if kwargs.get("nrows") == 0 or "TA_F" not in result.columns:
            return result
        if "TIMESTAMP_START" not in result.columns or "TA_F_QC" not in result.columns:
            raise RuntimeError("Unexpected v5 loading columns; cannot track TA correction")
        if self.calls_touched:
            raise RuntimeError("Unexpected repeated v5 primary CSV read; protect provenance")
        result = result.copy()
        stamp = ts_strings(result["TIMESTAMP_START"])
        hit = stamp.isin(self.subs)
        touched = set(stamp[hit].tolist())
        if touched != set(self.subs):
            raise RuntimeError("All suspected timestamps must be present in original v5 input")
        # All substituted temperatures use official station-downscaled TA_ERA.
        # Mark QC as 2 *inside the trial*, not as measured QC=0.
        result.loc[hit, "TA_F"] = stamp[hit].map(self.subs)
        result.loc[hit, "TA_F_QC"] = 2
        self.times_touched = touched
        self.calls_touched += 1
        print(f"  IN-MEMORY TA_F/TA_F_QC overrides: {len(touched)} (source file untouched)", flush=True)
        return result


def run_v5_trial(ref, primary, companion, source_root, output_root, strong):
    spec = importlib.util.spec_from_file_location("reference_eightsite_qc_v5", str(ref))
    if not spec or not spec.loader:
        raise RuntimeError("Cannot load original QC v5 module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "parse_site", None)):
        raise RuntimeError("Not the expected eight-site QC v5 script")
    module.SITE_YEARS = {SITE: (FIRST, LAST)}

    def pinned_locator(_root, pattern):
        if pattern == "*FLUXMET_HH*.csv":
            return primary
        if pattern == "*ERA5_HH*.csv":
            return companion
        raise RuntimeError(f"Unexpected v5 input pattern: {pattern}")

    module.get_one = pinned_locator
    substitutions = dict(zip(strong.timestamp, strong.TA_ERA.astype(float)))
    proxy = ReadCSVProxy(pd, primary, substitutions)
    module.pd = proxy
    status = module.parse_site(SITE, source_root, output_root)
    if proxy.calls_touched != 1 or len(proxy.times_touched) != len(substitutions):
        raise RuntimeError("TA override injection failed to cover all suspected timestamps")
    if status["status"] == "FAIL":
        raise RuntimeError("Original v5 QC returned FAIL")
    return status


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Read only, audit suspect temperatures")
    mode.add_argument("--run", action="store_true", help="Create a separate v6 trial candidate")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--previous-v5", type=Path, default=DEFAULT_V5)
    ap.add_argument("--base-script", type=Path, default=Path.home() / "CLM_FATES_scripts/FLUXNET_13_reference_v5.py")
    args = ap.parse_args()
    root, out, ref = args.root.resolve(), args.out.resolve(), args.base_script.resolve()
    primary, companion, sha = preflight(root, ref, out)
    x, strong = read_audit(primary)
    unmatched = x.loc[x.suspect_cold & ~x.strong_TA40_artifact]
    print("Source:", primary)
    print("Companion:", companion)
    print("Reference SHA256:", sha)
    print("Strong site-specific TA40 suspect records:", len(strong))
    print("Original QC=0 among suspect records:", int(strong.TA_F_QC.eq(0).sum()))
    print("Other TA<-25C not matching strong rule:", len(unmatched))
    print("Suspect years:", strong.timestamp.str.slice(0, 4).value_counts().sort_index().to_dict())
    if len(strong):
        print("Sample original TA / ERA / VPD / original RH:")
        show_cols = ["timestamp", "TA_F", "TA_ERA", "TA_F_QC", "VPD_F", "VPD_F_QC", "original_RH_pct"]
        show_cols += [c for c in OPTIONAL_CONTEXT_COLS if c in strong.columns]
        print(strong[show_cols].head(8).to_string(index=False))
    if len(unmatched):
        print("UNMATCHED EXTREME COLD: needs manual inspection:")
        print(unmatched[["timestamp", "TA_F", "TA_ERA", "TA_F_QC"]].head(10).to_string(index=False))
    if args.check:
        print("CHECK COMPLETE: read-only. No files written.")
        return 0
    if not len(strong):
        raise RuntimeError("Nothing matches the strong anomaly rule; no v6 trial created")
    if len(unmatched):
        raise RuntimeError("Unmatched extreme-cold records remain. Inspect and adjust rule before running")
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"REFUSED: output already contains files: {out}. Specify a NEW --out.")
    out.mkdir(parents=True, exist_ok=True)
    strong.to_csv(out / "ES-LJu_TA40_trial_overrides_original_vs_ERA.csv", index=False)
    (strong.groupby("year").agg(records=("timestamp", "size"),
                                 original_QC0=("TA_F_QC", lambda v: int(v.eq(0).sum())),
                                 median_difference_C=("temperature_difference_C", "median"))
           .reset_index().to_csv(out / "ES-LJu_TA40_trial_by_year.csv", index=False))
    manifest = {
        "site": SITE, "pinned_release": RELEASE, "source_file": str(primary),
        "companion_file": str(companion), "algorithm_reference": str(ref),
        "reference_sha256": sha, "created_utc": datetime.now(timezone.utc).isoformat(),
        "strong_rule": "TA_F<-25 degC AND TA_ERA>-10 degC AND (TA_ERA-TA_F)>=25 degC, site ES-LJu only",
        "method": "TA_F overwritten IN MEMORY by official downscaled TA_ERA, TA_F_QC set to 2; original VPD_F and all other variables unchanged before rerunning exact v5 algorithm",
        "science_status": "TRIAL: review temperature source, VPD, QBOT, ERA reliability, other sites, and PFT/ZBOT before DATM",
        "n_overrides": len(strong), "n_original_QC0_overridden": int(strong.TA_F_QC.eq(0).sum()),
    }
    (out / "experiment_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("\nSTART independent trial, never modifying existing candidate files.", flush=True)
    status = run_v5_trial(ref, primary, companion, root, out, strong)
    qc_path = out / SITE / "forcing/qc_v5" / f"{SITE}_status.json"
    qc = json.loads(qc_path.read_text())
    qc.update({
        "status_v5_on_trial_input": qc["status"], "status": "REVIEW",
        "candidate_v6": True, "temperature_override_count": len(strong),
        "original_QC0_temperature_overrides": int(strong.TA_F_QC.eq(0).sum()),
        "temperature_provenance_csv": str(out / "ES-LJu_TA40_trial_overrides_original_vs_ERA.csv"),
        "note": "Temperature substitutions are scientifically provisional and must be reviewed. Never treat ERA as original tower observations.",
    })
    qc_path.write_text(json.dumps(qc, indent=2))
    processed = out / SITE / "forcing/processed_v5" / f"{SITE}_CLM_forcing_{FIRST}_{LAST}.csv"
    recent = pd.read_csv(processed, usecols=["time", "TA_USE", "VPD_USE", "TBOT", "QBOT"], low_memory=False)
    recent["timestamp"] = pd.to_datetime(recent.time).dt.strftime("%Y%m%d%H%M")
    check = strong[["timestamp", "TA_F", "TA_ERA", "VPD_F", "TA_F_QC"]].merge(
        recent, on="timestamp", how="left", validate="one_to_one")
    if check.TA_USE.isna().any() or not np.allclose(check.TA_USE.to_numpy(), check.TA_ERA.to_numpy(), atol=1e-8, rtol=0):
        raise RuntimeError("Trial forcing temperature does not agree with exact TA_ERA override; investigate")
    prior = args.previous_v5 / SITE / "forcing/processed_v5" / f"{SITE}_CLM_forcing_{FIRST}_{LAST}.csv"
    if prior.is_file():
        old = pd.read_csv(prior, usecols=["time", "TA_USE", "VPD_USE", "QBOT"], low_memory=False)
        old["timestamp"] = pd.to_datetime(old.time).dt.strftime("%Y%m%d%H%M")
        check = check.merge(old.drop(columns="time").rename(columns={
            "TA_USE": "v5_TA_USE", "VPD_USE": "v5_VPD_USE", "QBOT": "v5_QBOT"}),
            on="timestamp", how="left", validate="one_to_one")
    check.to_csv(out / "ES-LJu_TA40_v5_vs_v6_trial_comparison.csv", index=False)
    print("\nTRIAL COMPLETE. Exact candidate output:", out)
    print("Reference v5's assessment on revised input:", status["status"])
    print("Scientific gate: REVIEW (manual authorization required)")
    print("Replaced original temperature records:", len(strong))
    print("Official QC=0 records overridden (provisional):", int(strong.TA_F_QC.eq(0).sum()))
    print("v6 TA range for previously bad records:", round(float(check.TA_USE.min()), 3), round(float(check.TA_USE.max()), 3))
    print("v6 VPD range for previously bad records:", round(float(check.VPD_USE.min()), 3), round(float(check.VPD_USE.max()), 3))
    print("No original raw source, existing v5 output, DATM or active spin-up was modified.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)
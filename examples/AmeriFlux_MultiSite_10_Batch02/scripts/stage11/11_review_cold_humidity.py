#!/usr/bin/env python3
"""Batch02 Stage11: non-destructive cold-humidity repair proposals, NOT DATM forcing.

Only the exact Stage08 unresolved RH rows are examined. Proposed VPD uses
valid ERA-companion RH analogues at the same site, month, and temperature bin.
This is a non-independent climatological sensitivity, not observed humidity.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

DEFAULT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/raw_RH_sensitivity_20261022T013805Z_aadaffee")
SITES = ("US-EML", "US-GLE", "US-Ho1", "US-ICh", "US-ICt")
EXPECTED = {"US-EML": 1327, "US-GLE": 295, "US-Ho1": 917, "US-ICh": 169, "US-ICt": 2176}

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def vapor(t):
    return 6.112 * np.exp(17.67 * t / (t + 243.5))

def original_time(s):
    return pd.to_datetime(s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True), format="%Y%m%d%H%M")

def run(root, output, min_donors, window, audit_only):
    root = root.resolve()
    if not (root / "INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM").is_file():
        raise ValueError("Expected the original incomplete Stage08, not a selected forcing directory")
    manifest = json.loads((root / "exact_input_manifest.json").read_text())
    selected = json.loads((root / "selected_candidates.json").read_text())
    if manifest["algorithm"] != "STAGE07_BLOCKERS_SAME_RELEASE_RAW_RH_SENSITIVITY":
        raise ValueError("Not the pinned Stage08 algorithm")
    if selected["complete"] or {x["site"] for x in selected["candidates"]} != {
        "US-BZS", "US-CMW", "US-Ha1", "US-Ho2", "US-Ho3"
    }:
        raise ValueError("Unexpected selection: do not proceed")
    pins = {}
    for relative, digest in json.loads((root / "output_sha256.json").read_text()).items():
        p = (root / relative).resolve()
        if root not in p.parents or sha(p) != digest:
            raise ValueError("Stage08 output hash mismatch: " + relative)
        pins[str(p)] = digest
    for original, digest in manifest["input_sha256"].items():
        p = Path(original).resolve()
        if sha(p) != digest:
            raise ValueError("Pinned Stage08 input changed: " + original)
        pins[str(p)] = digest
    info = {x["site"]: x for x in manifest["sites"]}
    if set(SITES) - set(info):
        raise ValueError("Five blocked sites not in Stage08 manifest")
    rows = []
    summary = []
    for site in SITES:
        item = info[site]
        file = root / site / "forcing/qc_v5" / f"{site}_native_RH_resolution_attempts.csv"
        attempts = pd.read_csv(file)
        attempts["time"] = pd.to_datetime(attempts["time"])
        held = attempts[attempts.decision != "CANDIDATE_RAW_RH"].copy()
        if len(held) != EXPECTED[site] or not held.decision.eq("HOLD_RH_MISSING_OR_NONFINITE").all():
            raise ValueError(f"Unanticipated Stage08 blocker scope for {site}")
        if held.time.duplicated().any():
            raise ValueError(f"Duplicate Stage08 target time: {site}")
        primary = Path(item["primary"])
        companion = Path(item["era"])
        if sha(primary) != pins.get(str(primary.resolve())) or sha(companion) != pins.get(str(companion.resolve())):
            raise ValueError("Raw source is not pinned/unchanged: " + site)
        ec = pd.read_csv(companion, usecols=["TIMESTAMP_START", "TA_ERA", "VPD_ERA"],
                         dtype={"TIMESTAMP_START": str})
        ec["time"] = original_time(ec.TIMESTAMP_START)
        ec = ec[ec.time.dt.year.between(item["first_year"], item["last_year"])]
        ec = ec[~((ec.time.dt.month == 2) & (ec.time.dt.day == 29))]
        if ec.time.duplicated().any():
            raise ValueError("Duplicate ERA counterpart time: " + site)
        ec["TA_ERA"] = pd.to_numeric(ec.TA_ERA, errors="coerce")
        ec["VPD_ERA"] = pd.to_numeric(ec.VPD_ERA, errors="coerce")
        ec.loc[ec.TA_ERA <= -9990, "TA_ERA"] = np.nan
        ec.loc[ec.VPD_ERA <= -9990, "VPD_ERA"] = np.nan
        with np.errstate(all="ignore"):
            ec["RH_valid"] = 100 * (1 - ec.VPD_ERA / vapor(ec.TA_ERA))
        valid = ec.TA_ERA.between(-80, 0, inclusive="left") & ec.RH_valid.between(5, 100)
        ec = ec.loc[valid].copy()
        ec["month"] = ec.time.dt.month
        n_ok = 0
        for target in held.itertuples():
            t = float(target.TA_before_fallback_C)
            pressure = float(target.PA_before_fallback_kPa)
            month = int(target.time.month)
            donor = ec.loc[
                ec.month.eq(month) & ec.TA_ERA.sub(t).abs().le(window),
                "RH_valid"
            ]
            n = len(donor)
            rh = float(donor.median()) if n else np.nan
            lo = float(donor.quantile(.25)) if n else np.nan
            hi = float(donor.quantile(.75)) if n else np.nan
            eligible = (n >= min_donors and -80 <= t < 0 and
                        50 <= pressure <= 110 and np.isfinite(rh) and 5 <= rh < 100)
            with np.errstate(all="ignore"):
                vpd = float(vapor(t) * (1-rh/100)) if eligible else np.nan
                ea = float((vapor(t)-vpd)*100) if eligible else np.nan
                q = float(.622*ea/(pressure*1000-.378*ea)) if eligible else np.nan
            eligible = bool(eligible and np.isfinite(vpd) and 0 <= vpd <= 125 and
                            np.isfinite(q) and 0 < q <= .08)
            n_ok += eligible
            rows.append(dict(site=site, time=str(target.time), source_csv_row=int(target.source_csv_row),
                original_TA_C=float(target.TA_original_C), retained_TA_C=t,
                retained_PA_kPa=pressure, prior_VPD_hPa=float(target.VPD_before_fallback_hPa),
                ERA_RH_impossible_pct=float(target.ERA_RH_pct),
                source_VPD_QC=float(target.VPD_original_QC) if pd.notna(target.VPD_original_QC) else None,
                source_RH_missing=True, donor_count=n, donor_month=month,
                donor_temperature_window_C=window, donor_RH_median_pct=rh,
                donor_RH_q25_pct=lo, donor_RH_q75_pct=hi,
                proposed_VPD_hPa=vpd if eligible else None,
                proposed_QBOT_kgkg=q if eligible else None,
                decision="PROVISIONAL_ANALOGUE_REVIEW_REQUIRED" if eligible else "HOLD_NO_SUPPORTED_ANALOGUE",
                caveat="Not independently validated; same site-downscaled ERA5 companion"))
        summary.append(dict(site=site, blocked=len(held), provisional=n_ok,
                            hold=len(held)-n_ok))
        print(f"{site}: {n_ok}/{len(held)} proposed, {len(held)-n_ok} held", flush=True)
    if sum(r["blocked"] for r in summary) != 4884 or len(rows) != 4884:
        raise ValueError("Expected exactly 4,884 Stage08 unresolved records")
    changed = [p for p, digest in pins.items() if sha(Path(p)) != digest]
    if changed:
        raise ValueError("Inputs changed during Stage11: " + str(changed))
    print("STAGE11 SUMMARY", json.dumps(summary), flush=True)
    if audit_only:
        print("CHECK ONLY: no output created")
        return
    if output.exists() or output == root or output in root.parents or root in output.parents:
        raise ValueError("Refusing existing or nested output directory")
    output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(rows).to_csv(output / "cold_humidity_repair_proposals.csv", index=False)
    pd.DataFrame(summary).to_csv(output / "site_summary.csv", index=False)
    (output / "DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Unapproved sensitivity proposals, NOT forcing. Verify independent dewpoint or humidity before any model use.\n")
    (output / "manifest.json").write_text(json.dumps(dict(
        source_stage08=str(root), input_hashes=pins, script_hash=sha(Path(__file__)),
        n_target_rows=len(rows), min_donors=min_donors, temperature_window_C=window,
        scientific_status="HOLD_INDEPENDENT_VALIDATION_REQUIRED",
        no_forcing_written=True, source_files_preserved=True,
        donor_warning="Companion ERA5 RH from TA_ERA and VPD_ERA is not an independent measurement"
    ), indent=2)+"\n")
    print("STAGE11 REPORT:", output, flush=True)
    print("No forcing, DATM, CIME or Slurm files modified.", flush=True)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage08-root", type=Path, default=DEFAULT)
    p.add_argument("--output-root", type=Path)
    p.add_argument("--min-donors", type=int, default=60)
    p.add_argument("--temperature-window-C", type=float, default=10)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    if not 1 <= args.min_donors <= 10000 or not 1 <= args.temperature_window_C <= 20:
        p.error("Donors or temperature window outside supported range")
    output = args.output_root or DEFAULT.parent / (
        "stage11_cold_humidity_review_" +
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    run(args.stage08_root, output.resolve(), args.min_donors,
        args.temperature_window_C, args.check)

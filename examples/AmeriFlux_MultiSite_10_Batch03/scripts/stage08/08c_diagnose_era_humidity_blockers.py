#!/usr/bin/env python3
"""Batch03 Stage08c: read-only diagnosis of ERA5 humidity support at 1924 RH holds.

Uses exact checksum-linked Stage08 / Stage08b reports. No automatic corrections,
RH clipping, precipitation changes, forcing, DATM, or model job submission.
--check writes nothing; --run writes only isolated evidence reports.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE08 = "raw_RH_sensitivity_20261022T025645Z_3c43eb8b"
STAGE08B = "stage08b_rh_cause_20261022T030908Z_f8927638"
EXPECTED = {"US-Kon": 229, "US-MMS": 18, "US-Me2": 4, "US-Me6": 1,
            "US-MtB": 15, "US-NR1": 173, "US-NR3": 1484}
COLUMNS = ("site", "time", "source_csv_row", "decision",
           "TA_before_fallback_C", "VPD_before_fallback_hPa",
           "PA_before_fallback_kPa", "TA_ERA_C", "VPD_ERA_hPa",
           "ERA_RH_pct", "RH_raw_pct", "VPD_original_QC")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def read_checked(report, relative, sha_manifest=None):
    path = report / relative
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected regular evidence file: " + str(path))
    if sha_manifest is not None:
        if relative not in sha_manifest or sha(path) != sha_manifest[relative]:
            raise ValueError("Missing or altered Stage08 report evidence: " + relative)
    return path


def as_numbers(data, name):
    a = pd.to_numeric(data[name], errors="coerce").to_numpy(dtype=float)
    a[(~np.isfinite(a)) | (a <= -9990)] = np.nan
    return a


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    opts = parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--check", action="store_true")
    opts.add_argument("--run", action="store_true")
    args = parser.parse_args()

    stage08 = ROOT / STAGE08
    report = ROOT / "reports" / STAGE08B
    if any(not p.is_dir() or p.is_symlink() for p in (ROOT, stage08, report)):
        parser.error("Expected existing, real Stage08/Stage08b directories")
    if not (stage08 / "INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM").is_file():
        raise ValueError("Stage08 incomplete marker missing: do not proceed")

    doc = json.loads(read_checked(report, "diagnostic_scope.json").read_text())
    if (Path(doc["stage08_root"]).resolve() != stage08
            or doc["remaining"] != 1924 or doc["input_blocks"] != 2273
            or doc["rh_numerically_eligible"] != 349):
        raise ValueError("Stage08b scope or lineage differs from expected trial")
    ledger_file = read_checked(stage08, "output_sha256.json")
    if sha(ledger_file) != doc["input_sha256"]:
        raise ValueError("Stage08b source SHA256 receipt has changed")
    ledger = json.loads(ledger_file.read_text())

    f = read_checked(report, "unresolved_rh_records.csv")
    records = pd.read_csv(f, dtype=str, keep_default_na=False)
    if any(c not in records.columns for c in COLUMNS):
        raise ValueError("Stage08b evidence schema missing required fields")
    if (len(records) != 1924 or set(records.site) != set(EXPECTED)
            or not records.decision.eq("HOLD_RH_MISSING_OR_NONFINITE").all()):
        raise ValueError("Residual record scope changed")
    for site, expected in EXPECTED.items():
        subset = records.loc[records.site.eq(site)]
        if len(subset) != expected or subset.source_csv_row.duplicated().any():
            raise ValueError("Residual site counts/row identity changed: " + site)
        entry = f"{site}/forcing/qc_v5/{site}_native_RH_resolution_attempts.csv"
        old = pd.read_csv(read_checked(stage08, entry, ledger),
                          dtype=str, keep_default_na=False)
        previous = old.loc[old.decision.ne("CANDIDATE_RAW_RH")]
        if len(previous) != expected:
            raise ValueError("Original Stage08 residual count differs: " + site)
        key = ["source_csv_row", "time", "decision"]
        if set(map(tuple, subset[key].to_numpy())) != set(map(tuple, previous[key].to_numpy())):
            raise ValueError("Stage08b residual row identity differs from Stage08: " + site)

    rawrh = as_numbers(records, "RH_raw_pct")
    if np.isfinite(rawrh).any():
        raise ValueError("Residual raw RH unexpectedly contains a finite valid value")

    t = as_numbers(records, "TA_ERA_C")
    v = as_numbers(records, "VPD_ERA_hPa")
    rh = as_numbers(records, "ERA_RH_pct")
    site_t = as_numbers(records, "TA_before_fallback_C")
    site_vpd = as_numbers(records, "VPD_before_fallback_hPa")
    site_pa = as_numbers(records, "PA_before_fallback_kPa")
    qc = as_numbers(records, "VPD_original_QC")

    era_t_good = np.isfinite(t) & (t >= -80) & (t <= 65)
    era_v_good = np.isfinite(v) & (v >= -.1) & (v <= 125)
    era_rh_good = np.isfinite(rh) & (rh >= -2) & (rh <= 100.05)
    ta_good = np.isfinite(site_t)
    allowed = era_t_good & era_v_good & era_rh_good & ta_good
    if allowed.any():
        raise ValueError("A Stage07/08 humidity-blocked record is unexpectedly ERA-eligible")

    # Same liquid-water saturation used in the original QCv5 engine.
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        es_era = 6.112 * np.exp(17.67 * t / (t + 243.5))
        rh_rebuilt = 100 * (es_era - v) / es_era
        es_site_water = 6.112 * np.exp(17.67 * site_t / (site_t + 243.5))
        ea_site_water = es_site_water - site_vpd
        es_site_ice = 6.112 * np.exp(22.46 * site_t / (site_t + 272.62))
        es_site_ice = np.where(site_t < 0, es_site_ice, es_site_water)
        ea_site_ice = es_site_ice - site_vpd

    overlap = np.isfinite(rh) & np.isfinite(rh_rebuilt) & np.isfinite(t) & np.isfinite(v)
    if not np.isclose(rh[overlap], rh_rebuilt[overlap], rtol=1e-8, atol=1e-6).all():
        raise ValueError("Recorded companion ERA RH disagrees with recomputed values")

    reason = np.full(len(records), "", dtype=object)
    # Mutually exclusive primary reason; other conditions remain visible separately.
    for mask, name in (
        (~ta_good, "SOURCE_TA_MISSING"),
        (~era_t_good, "ERA_TA_MISSING_OR_OUT_OF_RANGE"),
        (~era_v_good, "ERA_VPD_MISSING_OR_OUT_OF_RANGE"),
        (~np.isfinite(rh), "ERA_RH_NONFINITE"),
        (rh < -2, "ERA_RH_BELOW_MINUS2_PCT"),
        (rh > 100.05, "ERA_RH_ABOVE_100_05_PCT"),
    ):
        reason[(reason == "") & mask] = name
    if (reason == "").any():
        raise ValueError("Companion ERA rejection reason was not classified")

    detail = records[list(COLUMNS)].copy()
    detail["year"] = pd.to_datetime(detail.time, errors="raise").dt.year
    detail["rejection_primary_reason"] = reason
    detail["source_VPD_QC0"] = qc == 0
    detail["ERA_TA_valid"] = era_t_good
    detail["ERA_VPD_valid"] = era_v_good
    detail["ERA_RH_within_minus2_to_100_05"] = era_rh_good
    detail["ERA_RH_nonfinite"] = ~np.isfinite(rh)
    detail["ERA_RH_below_minus2"] = np.isfinite(rh) & (rh < -2)
    detail["ERA_RH_above_100_05"] = np.isfinite(rh) & (rh > 100.05)
    detail["site_TA_below_0C"] = np.isfinite(site_t) & (site_t < 0)
    detail["site_implied_ea_water_hPa"] = ea_site_water
    detail["site_implied_ea_ice_hPa"] = ea_site_ice
    detail["site_ea_water_nonpositive"] = np.isfinite(ea_site_water) & (ea_site_water <= 0)
    detail["site_ea_ice_nonpositive"] = np.isfinite(ea_site_ice) & (ea_site_ice <= 0)
    detail["site_TA_minus_ERA_C"] = site_t - t
    detail["site_PA_kPa"] = site_pa

    grouped = detail.groupby(["site", "rejection_primary_reason"], sort=True).agg(
        native_records=("source_csv_row", "count"),
        QC0_records=("source_VPD_QC0", "sum"),
        subzero_site_records=("site_TA_below_0C", "sum"),
        nonpositive_site_ea_water=("site_ea_water_nonpositive", "sum"),
        nonpositive_site_ea_ice=("site_ea_ice_nonpositive", "sum"),
    ).reset_index()
    annual = detail.groupby(["site", "year", "rejection_primary_reason"], sort=True).size().rename("native_records").reset_index()

    print("STAGE08C: exact linked Stage08 and Stage08b evidence verified")
    print("\nERA REJECTION REASONS BY SITE (mutually exclusive):")
    print(grouped.to_string(index=False))
    print("\nSUMMARIES:")
    print("Residual:", len(detail), "| original VPD QC0:", int(detail.source_VPD_QC0.sum()))
    print("Site temperatures <0 C:", int(detail.site_TA_below_0C.sum()))
    print("Site water-saturation ea <=0:", int(detail.site_ea_water_nonpositive.sum()))
    print("Site ice-saturation ea <=0:", int(detail.site_ea_ice_nonpositive.sum()))
    if args.check:
        print("STAGE08C PREFLIGHT: 1924/1924 classified; no reports/data changed")
        return 0

    root = ROOT / "reports"
    out = root / ("stage08c_era_humidity_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    detail.to_csv(out / "era_humidity_residual_details.csv", index=False)
    grouped.to_csv(out / "era_rejection_by_site.csv", index=False)
    annual.to_csv(out / "era_rejection_by_year.csv", index=False)
    (out / "evidence_scope.json").write_text(json.dumps({
        "stage08_root": str(stage08), "stage08b_report": str(report),
        "stage08_sha256_manifest": sha(ledger_file),
        "stage08b_unresolved_csv_sha256": sha(f), "residual_records": len(detail),
        "policy": "READ ONLY; no ERA/RH replacement, no RH floor change, no DATM",
        "notes": [
            "ERA rejection reasons are algorithmic under historical QCv5; not proof ERA is physically wrong.",
            "Below-freezing ice saturation is a diagnostic sensitivity, not an authorized forcing conversion.",
            "Primary reason categories are exclusive; other screening indicators may overlap.",
            "Raw RH and same-site VPD may share processing provenance.",
            "A numerical reconstruction is not independent meteorological validation."
        ]}, indent=2) + "\n")
    print("STAGE08C SUMMARY: 1924/1924 classified, report_only=True")
    print("REPORT DIR:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

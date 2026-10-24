#!/usr/bin/env python3
"""AmeriFlux Batch03 Stage10c: independent science audit of Stage10b report.

Read-only --check verifies the pinned 1,924-event ledger, recalculates the
thermodynamics from recorded interpolated grid values, checks the 27 absolute
transfer failures, compares both transfers to ice saturation at subzero T,
and restores an MDS VPD comparison from the ORIGINAL Stage08f evidence.

--run saves only an isolated, new report in reports/stage10c_*. It NEVER edits
Stage10b, Stage08f, raw tower data, QCv5, DATM, cases, restarts or Slurm.
Physical plausibility and the source checks DO NOT approve humidity repair.
Site clocks remain provisional (particularly US-Me2).
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
DEFAULT_10B = ROOT / "reports/stage10b_external_humidity_20261024T040142Z_be6a9d78"
STAGE07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE08C = ROOT / "reports/stage08c_era_humidity_20261022T031437Z_512e8731"
STAGE08E = ROOT / "reports/stage08e_alternatives_20261022T032727Z_b122e5b0"
STAGE08F = ROOT / "reports/stage08f_mds_pairs_20261022T033321Z_7591f948"
STAGE09A = ROOT / "reports/stage09a_external_dewpoint_plan_20261022T034051Z_437c9c0c"
COUNTS = {"US-Kon": 229, "US-MMS": 18, "US-Me2": 4, "US-Me6": 1,
          "US-MtB": 15, "US-NR1": 173, "US-NR3": 1484}
CLOCKS = {"US-Kon": -6, "US-MMS": -5, "US-Me2": -8, "US-Me6": -8,
          "US-MtB": -7, "US-NR1": -7, "US-NR3": -7}
KEYS = ["site", "source_csv_row", "time"]


def regular(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Expected regular non-symlink file: " + str(path))
    return path


def real_dir(path):
    path = Path(path)
    if not path.is_dir() or path.is_symlink():
        raise ValueError("Expected non-symlink directory: " + str(path))
    return path


def digest(path):
    h = hashlib.sha256()
    with regular(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    return json.loads(regular(path).read_text(encoding="utf-8"))


def bool_array(df, field):
    vals = df[field].astype(str).str.strip().str.lower()
    if not vals.isin(["true", "false", "1", "0"]).all():
        raise ValueError("Non-boolean evidence field: " + field)
    return vals.isin(["true", "1"]).to_numpy(dtype=bool)


def numbers(df, field):
    value = pd.to_numeric(df[field], errors="coerce").to_numpy(dtype=float)
    value[(~np.isfinite(value)) | (value <= -9990)] = np.nan
    return value


def close(field, recorded, expected, rtol=3e-7, atol=1e-7):
    mask = np.isclose(recorded, expected, rtol=rtol, atol=atol, equal_nan=True)
    if not mask.all():
        mismatches = np.flatnonzero(~mask)
        raise ValueError(f"Independent numeric mismatch {field}: {len(mismatches)} "
                         f"rows, first row index {mismatches[0]}")


def water_saturation(t):
    with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
        return 6.112 * np.exp(17.67 * t / (t + 243.5))


def ice_saturation(t):
    with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
        return 6.112 * np.exp(22.46 * t / (t + 272.62))


def humidity_specific(e_hpa, pressure_pa):
    e_pa = e_hpa * 100.0
    with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
        return 0.622 * e_pa / (pressure_pa - 0.378 * e_pa)


def verify_provenance(report):
    real_dir(report)
    for folder in (ROOT, STAGE07, STAGE08C, STAGE08E, STAGE08F, STAGE09A):
        real_dir(folder)
    regular(STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    policy = load_json(report / "provenance_and_science_hold.json")
    if (policy.get("decision") != "ALL ROWS SCIENTIFIC HOLD; NO REPLACEMENTS APPROVED"
            or set(policy.get("offsets_tested_provisionally_only", {})) != set(CLOCKS)
            or policy.get("offsets_tested_provisionally_only") != CLOCKS):
        raise ValueError("Stage10b provenance no longer describes provisional scientific hold")
    paths = ("humidity_external_sensitivity_1924.csv",
             "site_science_review_summary.csv",
             "site_year_science_review_summary.csv")
    if set(policy.get("output_SHA256", {})) != set(paths):
        raise ValueError("Stage10b report SHA manifest differs")
    for p in paths:
        if digest(report / p) != policy["output_SHA256"][p]:
            raise ValueError("Stage10b report changed: " + p)
    upstream = {
        "stage08c": STAGE08C / "era_humidity_residual_details.csv",
        "stage08f": STAGE08F / "mds_pair_at_1924_blockers.csv",
        "stage09a_receipt": STAGE09A / "evidence_receipt.json",
    }
    for key, path in upstream.items():
        if digest(path) != policy["original_provenance"].get(key):
            raise ValueError("Stage10b pinned source report changed: " + key)
    e_policy = load_json(STAGE08E / "evidence_policy.json")
    f_policy = load_json(STAGE08F / "policy.json")
    if (e_policy.get("records") != 1924
            or digest(upstream["stage08c"]) != e_policy["stage08c_sha256"]
            or f_policy.get("records") != 1924
            or Path(f_policy["stage08e_evidence"]).resolve() != STAGE08E
            or digest(STAGE08E / "raw_alternatives_at_blockers.csv") !=
            f_policy["stage08e_evidence_sha256"]):
        raise ValueError("Stage08c–08f upstream evidence SHA chain differs")
    stage07 = load_json(STAGE07 / "exact_input_manifest.json")
    selected = {r["site"]: r for r in stage07["sites"]}
    if len(selected) != 10 or not set(COUNTS).issubset(selected):
        raise ValueError("Stage07 site release inventory changed")
    pins = {str(Path(p).resolve()): h for p, h in stage07["input_sha256"].items()}
    source_digests = policy.get("pinned_source_SHA256", {})
    if len(source_digests) != 14:
        raise ValueError("Expected 14 pinned raw sources in Stage10b report")
    for site in COUNTS:
        for kind in ("primary", "era"):
            path = regular(selected[site][kind])
            expected = pins.get(str(path.resolve()))
            if not expected or expected != digest(path):
                raise ValueError("Stage07 source not SHA-pinned or modified: " + str(path))
            if source_digests.get(str(path.resolve())) != expected:
                raise ValueError("Stage10b source hashes differ from Stage07: " + str(path))
    products = policy.get("external_product_SHA256", {})
    if len(products) != 32:
        raise ValueError("Expected 32 SHA-pinned ERA5-Land products")
    for key, expected_hash in products.items():
        parts = key.split(":")
        if len(parts) != 2 or parts[0] not in COUNTS or not parts[1].isdigit():
            raise ValueError("Unexpected external product reference: " + key)
        site, year = parts
        folder = real_dir(ROOT / "external_evidence/era5land_timeseries" / site / year)
        basename = f"ERA5Land_{site}_{year}_t2m_d2m_sp"
        existing = [p for p in (folder/(basename+".zip"), folder/(basename+".nc")) if p.exists()]
        if len(existing) != 1 or digest(existing[0]) != expected_hash:
            raise ValueError("Stage10b external ZIP/NetCDF checksum changed: " + key)
    return policy


def verify_event_keys(df, record_source, mds):
    for v in (df, record_source, mds):
        if len(v) != 1924 or v.duplicated(KEYS).any():
            raise ValueError("One of the Stage08/Stage10b ledgers is incomplete or has duplicate keys")
        if v.site.value_counts().to_dict() != COUNTS:
            raise ValueError("Unexpected event counts for site")
    upstream_keys = set(map(tuple, record_source[KEYS].to_numpy()))
    joined_keys = set(map(tuple, df[KEYS].to_numpy()))
    mds_keys = set(map(tuple, mds[KEYS].to_numpy()))
    if joined_keys != upstream_keys or mds_keys != upstream_keys:
        a_missing = sorted(upstream_keys - joined_keys)[:3]
        a_extra = sorted(joined_keys - upstream_keys)[:3]
        m_missing = sorted(upstream_keys - mds_keys)[:3]
        m_extra = sorted(mds_keys - upstream_keys)[:3]
        raise ValueError(
            "Stage08c/08f/Stage10b event identities differ after literal string-key read; "
            f"Stage10b missing={a_missing} extra={a_extra}; "
            f"Stage08f missing={m_missing} extra={m_extra}. "
            "No automatic normalization or record substitution is permitted."
        )
    if not set(df["review_class_stage10b"]) <= {
        "REVIEW_BOTH_PHYSICAL", "REVIEW_RELATIVE_ONLY_PHYSICAL",
        "REVIEW_ABSOLUTE_ONLY_PHYSICAL", "HOLD_INVALID_SITE_T_OR_P",
        "HOLD_INVALID_GRID_PHYSICS", "HOLD_BOTH_TRANSFER_SCREENS_FAIL", "HOLD_UNCLASSIFIED"
    }:
        raise ValueError("Unknown Stage10b review category")


def independent_science(df, mds):
    n = len(df)
    needed = ["TA_before_fallback_C", "PA_before_fallback_kPa",
              "VPD_before_fallback_hPa", "grid_temperature_C",
              "grid_dewpoint_C", "grid_pressure_Pa",
              "grid_relative_humidity_pct",
              "grid_dewpoint_absolute_e_hPa",
              "absolute_vpd_at_tower_T_hPa", "absolute_rh_at_tower_T_pct",
              "absolute_qbot_at_tower_P_kgkg",
              "relative_vpd_at_tower_T_hPa", "relative_rh_at_tower_T_pct",
              "relative_qbot_at_tower_P_kgkg", "absolute_transfer_physical_pass",
              "relative_transfer_physical_pass", "clock_approved",
              "clock_offset_hours_hypothesis", "native_minutes",
              "utc_midpoint_hypothesis", "absolute_transfer_ice_supersaturation_caution"]
    if not set(needed).issubset(df.columns):
        raise ValueError("Stage10b event output missing required independent-QC variables")
    t = numbers(df, "TA_before_fallback_C")
    pressure = numbers(df, "PA_before_fallback_kPa") * 1000.0
    gt = numbers(df, "grid_temperature_C")
    gd = numbers(df, "grid_dewpoint_C")
    gp = numbers(df, "grid_pressure_Pa")
    es_site = water_saturation(t)
    es_grid = water_saturation(gt)
    ea_grid = water_saturation(gd)
    rh_grid = 100.0 * ea_grid / es_grid
    ea_relative = es_site * rh_grid / 100.0
    vpd_absolute = es_site - ea_grid
    vpd_relative = es_site - ea_relative
    rh_absolute = 100.0 * ea_grid / es_site
    q_absolute = humidity_specific(ea_grid, pressure)
    q_relative = humidity_specific(ea_relative, pressure)
    for name, expected in (
        ("grid_relative_humidity_pct", rh_grid),
        ("grid_dewpoint_absolute_e_hPa", ea_grid),
        ("absolute_vpd_at_tower_T_hPa", vpd_absolute),
        ("absolute_rh_at_tower_T_pct", rh_absolute),
        ("absolute_qbot_at_tower_P_kgkg", q_absolute),
        ("relative_vpd_at_tower_T_hPa", vpd_relative),
        ("relative_rh_at_tower_T_pct", rh_grid),
        ("relative_qbot_at_tower_P_kgkg", q_relative),
    ):
        atol = 1e-10 if "qbot" in name else 1e-7
        close(name, numbers(df, name), expected, atol=atol)
    valid_site = (np.isfinite(t) & (t >= -80) & (t <= 65) &
                  np.isfinite(pressure) & (pressure >= 50000) & (pressure <= 110000))
    valid_grid = ((gd <= gt + .1) & (rh_grid > 0) & (rh_grid <= 100.05)
                  & np.isfinite(rh_grid) & np.isfinite(gp))
    a_ok = (valid_site & valid_grid & np.isfinite(vpd_absolute) &
            (vpd_absolute >= 0) & (vpd_absolute <= 125) &
            np.isfinite(rh_absolute) & (rh_absolute > 0) & (rh_absolute <= 100.05) &
            np.isfinite(q_absolute) & (q_absolute > 0) & (q_absolute <= .08))
    b_ok = (valid_site & valid_grid & np.isfinite(vpd_relative) &
            (vpd_relative >= 0) & (vpd_relative <= 125) &
            np.isfinite(rh_grid) & (rh_grid > 0) & (rh_grid <= 100.05) &
            np.isfinite(q_relative) & (q_relative > 0) & (q_relative <= .08))
    if not np.array_equal(bool_array(df, "absolute_transfer_physical_pass"), a_ok):
        raise ValueError("Stage10b absolute-transfer physical flags disagree with independent audit")
    if not np.array_equal(bool_array(df, "relative_transfer_physical_pass"), b_ok):
        raise ValueError("Stage10b relative-transfer physical flags disagree with independent audit")
    if bool_array(df, "clock_approved").any():
        raise ValueError("Unexpected clock approval; this report must stay provisional")
    offset = pd.to_numeric(df["clock_offset_hours_hypothesis"], errors="raise").to_numpy(dtype=int)
    native = pd.to_numeric(df["native_minutes"], errors="raise").to_numpy(dtype=int)
    stamps = pd.to_datetime(df["time"], errors="raise")
    mid_utc = pd.to_datetime(df["utc_midpoint_hypothesis"], errors="raise")
    computed_mid_utc = pd.DatetimeIndex(stamps) + pd.to_timedelta(native/2.0, unit="m") - pd.to_timedelta(offset, unit="h")
    if not pd.DatetimeIndex(mid_utc).equals(computed_mid_utc):
        raise ValueError("Stage10b local-interval to UTC midpoint mismatch")
    for site in COUNTS:
        sub = df.site.to_numpy() == site
        if not np.all(offset[sub] == CLOCKS[site]) or not np.all(native[sub] == (60 if site=="US-MMS" else 30)):
            raise ValueError("Stage10b offset/step changed: " + site)

    ice_es = np.where(t < 0, ice_saturation(t), es_site)
    ice_rh_a = 100.0 * ea_grid / ice_es
    ice_rh_b = 100.0 * ea_relative / ice_es
    ice_a_warn = (t < 0) & np.isfinite(ice_rh_a) & (ice_rh_a > 100)
    ice_b_warn = (t < 0) & np.isfinite(ice_rh_b) & (ice_rh_b > 100)
    if not np.array_equal(bool_array(df, "absolute_transfer_ice_supersaturation_caution"), ice_a_warn):
        raise ValueError("Stage10b ice supersaturation warning differs from independent formula")
    # Do not equate ice supersaturation to impossible physics (can occur in air).
    fail = ~a_ok
    fail_reasons = []
    for i in range(n):
        r = []
        if not valid_site[i]: r.append("SITE_T_OR_PRESSURE_INVALID")
        if not valid_grid[i]: r.append("GRID_T_DEWPOINT_OR_RH_INVALID")
        if not np.isfinite(vpd_absolute[i]) or vpd_absolute[i] < 0:
            r.append("ABS_VPD_NEGATIVE_OR_NONFINITE")
        elif vpd_absolute[i] > 125:
            r.append("ABS_VPD_ABOVE_LIMIT")
        if not np.isfinite(rh_absolute[i]) or rh_absolute[i] <= 0 or rh_absolute[i] > 100.05:
            r.append("ABS_RH_WATER_OUTSIDE_LIMIT")
        if not np.isfinite(q_absolute[i]) or q_absolute[i] <= 0 or q_absolute[i] > .08:
            r.append("ABS_QBOT_OUTSIDE_LIMIT")
        fail_reasons.append(";".join(r) if fail[i] else "")
    if np.any(fail & np.array([reason=="" for reason in fail_reasons])):
        raise ValueError("An absolute transfer fail was not independently explained")

    md = mds[KEYS + ["VPD_F_MDS", "MDS_pair_physical_screen_pass",
                     "MDS_VPD_valid_at_retained_TA"]].copy()
    flags = df.merge(md, on=KEYS, how="inner", validate="one_to_one",
                     suffixes=("", "_original_stage08f"))
    if len(flags) != len(df):
        raise ValueError("Stage08f MDS comparison join lost source rows")
    mds_vpd = numbers(flags, "VPD_F_MDS")
    flags["independent_absolute_VPD_minus_MDS_hPa"] = vpd_absolute - mds_vpd
    flags["independent_relative_VPD_minus_MDS_hPa"] = vpd_relative - mds_vpd
    flags["independent_A_ice_RH_pct"] = ice_rh_a
    flags["independent_B_ice_RH_pct"] = ice_rh_b
    flags["independent_A_ice_supersaturation_caution"] = ice_a_warn
    flags["independent_B_ice_supersaturation_caution"] = ice_b_warn
    flags["independent_A_physical_pass"] = a_ok
    flags["independent_B_physical_pass"] = b_ok
    flags["independent_A_failure_reasons"] = fail_reasons
    flags["A_minus_B_VPD_hPa"] = vpd_absolute - vpd_relative
    flags["A_minus_B_QBOT_kgkg"] = q_absolute - q_relative
    flags["source_temperature_below_0C"] = t < 0
    flags["independent_tower_grid_delta_gt5C"] = np.isfinite(t-gt) & (np.abs(t-gt) > 5)
    flags["scientific_hold_required"] = True
    flags["ice_rh_is_conditional_on_water_dewpoint_interpretation"] = True

    print("INDEPENDENT THERMODYNAMIC AUDIT: PASS; UTC midpoints and original MDS event keys: PASS")
    if "absolute_minus_mds_vpd_hPa" in df.columns:
        old = numbers(df, "absolute_minus_mds_vpd_hPa")
        if not np.isfinite(old).any() and np.isfinite(mds_vpd).any():
            print("STAGE10B GAP: absolute_minus_mds_vpd_hPa is unpopulated; Stage10c recomputes this from Stage08f.")
    return flags


def summarise(flags):
    result = []
    for site, data in flags.groupby("site", sort=True):
        a = bool_array(data, "independent_A_physical_pass")
        b = bool_array(data, "independent_B_physical_pass")
        ia = bool_array(data, "independent_A_ice_supersaturation_caution")
        ib = bool_array(data, "independent_B_ice_supersaturation_caution")
        temp_gap = bool_array(data, "independent_tower_grid_delta_gt5C")
        result.append({
            "site": site,
            "blockers": len(data),
            "A_physical_pass": int(a.sum()),
            "B_physical_pass": int(b.sum()),
            "A_fail_B_pass": int((~a & b).sum()),
            "A_ice_RH_gt_100": int(ia.sum()),
            "B_ice_RH_gt_100": int(ib.sum()),
            "tower_grid_delta_gt5C": int(temp_gap.sum()),
            "MDS_VPD_valid": int(np.isfinite(numbers(data, "VPD_F_MDS")).sum()),
            "offset_status": "US_ME2_HYPOTHESIS_UNVERIFIED" if site=="US-Me2" else "BIF_PUBLISHED_NOT_FORMALLY_APPROVED",
            "approved_forcing_records": 0
        })
    return pd.DataFrame(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Read-only science and provenance audit")
    group.add_argument("--run", action="store_true", help="Create only a new isolated Stage10c diagnostic report")
    parser.add_argument("--stage10b-root", type=Path, default=DEFAULT_10B,
                        help="Exact finished Stage10b report directory")
    args = parser.parse_args()

    report = real_dir(args.stage10b_root)
    print("STAGE10C — INDEPENDENT COLD-HUMIDITY SCIENCE AUDIT", flush=True)
    provenance = verify_provenance(report)
    src = pd.read_csv(regular(STAGE08C / "era_humidity_residual_details.csv"), dtype=str, keep_default_na=False)
    mds = pd.read_csv(regular(STAGE08F / "mds_pair_at_1924_blockers.csv"), dtype=str, keep_default_na=False)
    # Preserve event identity: pandas numeric inference converts source_csv_row
    # to integer while Stage08c/08f read their source-row keys as strings.
    # String dtype only for identifier fields; scientific numeric data remain numeric.
    df = pd.read_csv(
        regular(report / "humidity_external_sensitivity_1924.csv"),
        dtype={key: str for key in KEYS}, low_memory=False,
        keep_default_na=False,
    )
    verify_event_keys(df, src, mds)
    if len(provenance["external_product_SHA256"]) != 32:
        raise ValueError("Not all 32 external original products accounted for")
    flags = independent_science(df, mds)
    site_summary = summarise(flags)
    bad = flags.loc[~bool_array(flags, "independent_A_physical_pass")].copy()
    if len(site_summary) != 7 or int(site_summary.blockers.sum()) != 1924:
        raise ValueError("Independent audit site totals do not add to 1,924")
    print("\n========== STAGE10C INDEPENDENT SITE SUMMARY ==========")
    print(site_summary.to_string(index=False))
    print("\n========== A TRANSFER FAILURE REASONS ==========")
    print(bad.groupby(["site", "independent_A_failure_reasons"], sort=True).size().to_string())
    print(f"\nSTAGE10C SUMMARY: sites=7/7 source_rows={len(flags)}/1924 "
          f"A_failed={len(bad)} B_failed={int((~bool_array(flags,'independent_B_physical_pass')).sum())} "
          f"ice_A={int(bool_array(flags,'independent_A_ice_supersaturation_caution').sum())} "
          f"ice_B={int(bool_array(flags,'independent_B_ice_supersaturation_caution').sum())} "
          "repair_approvals=0", flush=True)

    if args.check:
        print("CHECK ONLY: no new files, no DATM/forcing/cases/Slurm changes.")
        return

    output = ROOT / "reports" / ("stage10c_independent_cold_humidity_" +
                                 datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
                                 "_" + uuid4().hex[:8])
    output.mkdir(exist_ok=False)
    details = output / "cold_humidity_independent_review_1924.csv"
    failures = output / "absolute_transfer_27_failure_investigation.csv"
    sites = output / "site_independent_science_summary.csv"
    flags.to_csv(details, index=False)
    bad.to_csv(failures, index=False)
    site_summary.to_csv(sites, index=False)
    receipt = {
        "source_10b_report": str(report),
        "source_10b_manifest_sha256": digest(report/"provenance_and_science_hold.json"),
        "source_10b_event_sha256": digest(report/"humidity_external_sensitivity_1924.csv"),
        "source_08f_mds_sha256": digest(STAGE08F/"mds_pair_at_1924_blockers.csv"),
        "numerical_policy": "Independent recalculation from Stage10b interpolated t2m/d2m/sp and original Stage08f MDS. Liquid-water dewpoint assumption, with both transfers checked against ice saturation as CAUTION.",
        "all_clocks_formally_approved": False,
        "MDS_is_independent_observation": False,
        "ice_supersaturation_is_automatic_rejection": False,
        "repair_approvals": 0,
        "science_hold": "ALL EVENT ROWS RETAIN SCIENTIFIC HOLD. DO NOT WRITE FORCING.",
        "output_SHA256": {p.name: digest(p) for p in (details, failures, sites)}
    }
    (output / "provenance_and_science_hold.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("STAGE10C REPORT DIR:", output, flush=True)
    print("REPORT ONLY: originals, QC-v5, DATM and model inputs are unchanged.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("STAGE10C STOP:", str(error), file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Batch03 Stage12r — exact 32 QC1 VPD neighbor forensic source/physics review.

The signed Stage12q verified 24 retained Stage12d matched-companion ERA-RH
VPD values differing from original source and 8 original-raw-only values
still missing in Stage12e. Explain why Stage12c had no VPD for these times,
recompute the 24 signed Stage12d transfers, and report exact original
Stage12d/Stage12e reason strings for the 8 still missing.

Source-only evidence. Original QC1 gap-filled VPD is NOT independent QC0
tower humidity truth; ERA companion is NOT automatically truth either.
Do not relax 4hPa jump guard or 5C site-grid T guard. Original 86+233
science holds and all source, forcing, DATM and model states stay unchanged.

--self-test regression physics only, no input or output filesystem actions
--check     signed native input + ledger audit, NO REPORT FILE WRITES
--run       same audit + new isolated SHA-receipted science REPORT ONLY
"""
import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode = True

VERSION = "batch03-stage12r-v1-20261025-32-QC1-edge-Stage12c-12d-native-source-physics"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
Q = ROOT / "reports/stage12q_76_original_VPD_edge_CDEG_lineage_20261025T093514Z_044390c3"
S07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
C = ROOT / "science_trials/stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e"
D = ROOT / "science_trials/stage12d_six_site_companion_RH_gap_recovery_20261024T121810Z_f1fa4cee"
E = ROOT / "science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
G = ROOT / "science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
STAGES = {
    "C": (C, "stage12c_research_shadow_SHA_receipt.json"),
    "D": (D, "stage12d_research_shadow_SHA_receipt.json"),
    "E": (E, "stage12e_research_only_sha_receipt.json"),
    "G": (G, "stage12g_research_only_sha_receipt.json"),
}
SITES = ("US-Me6", "US-NR1")
KEY = ["site", "neighbor_native_key"]

def file(path):
    p = Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing/symlink signed source: " + str(p))
    return p

def sha(path):
    h = hashlib.sha256()
    with file(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()

def val(x):
    try:
        y = float(x)
        return y if np.isfinite(y) and y > -9990 else np.nan
    except (ValueError, TypeError):
        return np.nan

def sat(t):
    if not np.isfinite(t):
        return np.nan
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return float(6.112 * np.exp(17.67 * t / (t + 243.5)))

def same(x, y, atol=1e-7):
    if not np.isfinite(x) or not np.isfinite(y):
        return not np.isfinite(x) and not np.isfinite(y)
    return abs(x - y) <= atol

def initial_screen(rawv, erav, tc, pa):
    """Replicate Stage12c baseline source choice, hard limits, water/Q closure."""
    sourceok = np.isfinite(rawv) and 0 <= rawv <= 125
    eraok = np.isfinite(erav) and 0 <= erav <= 125
    initial = rawv if sourceok else erav if eraok else np.nan
    source = "RAW_VPD_F" if sourceok else "COMPANION_VPD_ERA" if eraok else "NO_VALID_VPD"
    es = sat(tc)
    if not np.isfinite(initial):
        return source, initial, "C_BASELINE_VPD_ABSENT_OR_OUT_OF_HARD_BOUNDS", np.nan
    if not (np.isfinite(tc) and np.isfinite(pa) and pa > 49000):
        return source, initial, "C_SITE_T_OR_P_MISSING_OR_INVALID", np.nan
    if not (0 <= initial < es):
        return source, initial, "C_VPD_NEGATIVE_OR_AT_ABOVE_WATER_SATURATION", np.nan
    ea = 100 * (es - initial)
    q = 0.622 * ea / (pa - 0.378 * ea)
    if not np.isfinite(q) or not 0 < q < 0.08:
        return source, initial, "C_QBOT_WATER_VAPOUR_PHYSICS_INVALID", q
    return source, initial, "C_BASELINE_BASIC_PHYSICS_VALID_CHECK_PROTECTED_HOLD", q

def selftest():
    assert initial_screen(12., 1., 5., 90000.)[2] == "C_VPD_NEGATIVE_OR_AT_ABOVE_WATER_SATURATION"
    assert initial_screen(-4., 1., 5., 90000.)[0] == "COMPANION_VPD_ERA"
    assert initial_screen(2., 1., 20., 90000.)[2] == "C_BASELINE_BASIC_PHYSICS_VALID_CHECK_PROTECTED_HOLD"
    assert initial_screen(np.nan, np.nan, 20., 90000.)[2] == "C_BASELINE_VPD_ABSENT_OR_OUT_OF_HARD_BOUNDS"
    assert same(np.nan, np.nan) and same(1.0, 1.0 + 1e-8)
    t = 15.0
    te = 16.0
    ve = 4.0
    rh = 100 * (sat(te) - ve) / sat(te)
    reconstructed = sat(t) * (1 - rh / 100)
    assert abs(reconstructed - sat(t) * ve / sat(te)) < 1e-12
    print("STAGE12R SELF-TEST PASS: exact water saturation, Stage12c source precedence and ERA-RH transfer; NO WRITES", flush=True)

def signed_inputs():
    q_receipt_path = file(Q / "stage12q_science_report_SHA_receipt.json")
    r = json.loads(q_receipt_path.read_text())
    if (r.get("version") != "batch03-stage12q-v2-20261025-preserve-upstream-merge-CDEG-VPD-lineage"
        or r.get("original_86_holds_unchanged") is not True
        or r.get("original_233_protected_holds_unchanged") is not True
        or r.get("new_source_or_forcing_repairs") != 0
        or r.get("Postv5_approved") != 0 or r.get("DATM_ready") != 0
        or r.get("spinup_authorized") != 0):
        raise ValueError("Original Stage12q policy SHA receipt differs")
    for name, digest in r["output_SHA256"].items():
        if sha(Q / name) != digest:
            raise ValueError("Signed Stage12q output edited: " + name)
    receipts = {}
    for stage, (directory, name) in STAGES.items():
        receipt = json.loads(file(directory / name).read_text())
        if (sha(directory / name) != r["stage12c_d_e_g_receipt_SHA256"].get(stage)
            or receipt.get("Postv5_approved") != 0
            or receipt.get("DATM_ready") != 0
            or receipt.get("spinup_authorized") != 0):
            raise ValueError("Signed native predecessor receipt changed: " + stage)
        receipts[stage] = receipt
    inputs = json.loads(file(S07 / "exact_input_manifest.json").read_text())
    if (sha(S07 / "exact_input_manifest.json") != receipts["C"].get("stage07_manifest_SHA256")):
        raise ValueError("Stage07 original input manifest changed")
    specs = {x["site"]: x for x in inputs["sites"]}
    digests = {str(Path(p).resolve()): d for p, d in inputs["input_sha256"].items()}
    for site in SITES:
        if site not in specs:
            raise ValueError("Original site source missing: " + site)
        for column in ("primary", "era"):
            p = file(specs[site][column])
            if sha(p) != digests.get(str(p.resolve())):
                raise ValueError("Original release source SHA changed: " + str(p))
    for stage, name in [
        ("D", "guarded_companion_ERA_RH_auto_candidate_timestamps.csv"),
        ("D", "remaining_other_humidity_science_holds.csv"),
        ("E", "remaining_4372_source_second_ERA5Land_holds.csv")]:
        directory = STAGES[stage][0]
        digest = receipts[stage].get("output_sha256", {}).get(name)
        if not digest or sha(directory / name) != digest:
            raise ValueError("Original stage evidence ledger SHA changed: " + stage + " " + name)
    for site in SITES:
        name = site + "_STAGE12C_NOT_MODEL_READY_NOLEAP.csv"
        if sha(C / name) != receipts["C"]["output_sha256"][name]:
            raise ValueError("Stage12c original source temperature/provenance changed")
    return specs, r

def evidence_by_site(specs, selected):
    """Read only original FLUXMET/ERA rows and Stage12c baseline T/P rows."""
    native = {}
    for site in SITES:
        keys = set(selected.loc[selected.site.eq(site), "neighbor_native_key"])
        assert keys
        spec = specs[site]
        primary = pd.read_csv(file(spec["primary"]), usecols=[
            "TIMESTAMP_START", "TA_F", "PA_F", "VPD_F", "VPD_F_QC"],
            dtype={"TIMESTAMP_START": str}, low_memory=False)
        era = pd.read_csv(file(spec["era"]), usecols=[
            "TIMESTAMP_START", "TA_ERA", "VPD_ERA"],
            dtype={"TIMESTAMP_START": str}, low_memory=False)
        primary = primary.loc[primary.TIMESTAMP_START.isin(keys)].copy()
        era = era.loc[era.TIMESTAMP_START.isin(keys)].copy()
        if (len(primary) != len(keys) or len(era) != len(keys)
            or primary.TIMESTAMP_START.duplicated().any()
            or era.TIMESTAMP_START.duplicated().any()):
            raise ValueError("Unsigned or duplicate original half-hour source native keys " + site)
        original = primary.merge(era, on="TIMESTAMP_START",
                                 how="inner", validate="one_to_one")
        ctime = pd.read_csv(file(C / (site + "_STAGE12C_NOT_MODEL_READY_NOLEAP.csv")),
                            usecols=["time", "TA_USE", "PSRF", "VPD_USE"],
                            dtype={"time": str}, low_memory=False)
        ctime["TIMESTAMP_START"] = ctime.time.str.replace(
            r"[^0-9]", "", regex=True).str.slice(0, 12)
        ctime = ctime.loc[ctime.TIMESTAMP_START.isin(keys)].copy()
        if len(ctime) != len(keys) or ctime.TIMESTAMP_START.duplicated().any():
            raise ValueError("Stage12c original-site T/P native timestamps missing " + site)
        aligned = original.merge(ctime, on="TIMESTAMP_START", validate="one_to_one")
        if len(aligned) != len(keys):
            raise ValueError("Original timestamp mismatched source and Stage12c")
        for row in aligned.to_dict("records"):
            native[(site, row["TIMESTAMP_START"])] = row
    return native

def load_ledger(directory, name):
    return pd.read_csv(file(directory / name), dtype={"native_key": str}, low_memory=False)

def classify():
    specs, receipt = signed_inputs()
    q = pd.read_csv(file(Q / "32_QC1_nonmatch_source_values_and_repair_stage.csv"),
                    dtype={"held_native_key": str,
                           "neighbor_native_key": str}, low_memory=False)
    if (len(q) != 32 or q.duplicated(KEY).any()
        or not q.site.isin(SITES).all()
        or not q.original_FLUXMET_VPD_F_QC.eq("QC1").all()
        or q.source_origin_class.eq("BOTH_FINITE_DIFFER").sum() != 24
        or q.source_origin_class.eq("RAW_ONLY_FINITE").sum() != 8):
        raise ValueError("Stage12q exact 32 unique native QC1 sources changed")
    native = evidence_by_site(specs, q)
    d_good = load_ledger(D, "guarded_companion_ERA_RH_auto_candidate_timestamps.csv")
    d_hold = load_ledger(D, "remaining_other_humidity_science_holds.csv")
    e_hold = load_ledger(E, "remaining_4372_source_second_ERA5Land_holds.csv")
    for label, frame in [("Stage12d repair", d_good),
                         ("Stage12d hold", d_hold),
                         ("Stage12e hold", e_hold)]:
        if frame.duplicated(["site", "native_key"]).any():
            raise ValueError("Duplicate original " + label + " ledger native keys")
    dg = {(r.site, str(r.native_key)): r
          for r in d_good.itertuples(index=False) if r.site in SITES}
    dh = {(r.site, str(r.native_key)): r
          for r in d_hold.itertuples(index=False) if r.site in SITES}
    eh = {(r.site, str(r.native_key)): r
          for r in e_hold.itertuples(index=False) if r.site in SITES}
    rows = []
    for x in q.itertuples(index=False):
        key = (x.site, x.neighbor_native_key)
        a = native[key]
        raw_t = val(a["TA_F"])
        raw_p = val(a["PA_F"])
        raw_v = val(a["VPD_F"])
        raw_qc = val(a["VPD_F_QC"])
        era_t = val(a["TA_ERA"])
        era_v = val(a["VPD_ERA"])
        c_t = val(a["TA_USE"])
        c_p = val(a["PSRF"])
        c_v = val(a["VPD_USE"])
        d_v = val(x.D_VPD_hPa)
        e_v = val(x.E_VPD_hPa)
        g_v = val(x.G_VPD_hPa)
        if (not same(raw_v, val(x.original_FLUXMET_VPD_F_hPa))
            or raw_qc != 1 or not same(c_v, val(x.C_VPD_hPa))
            or np.isfinite(c_v)):
            raise ValueError("Original RAW/C source key or initial C missing condition changed " + str(key))
        source, baseline, creason, qb = initial_screen(raw_v, era_v, c_t, c_p)
        rh = (100 * (sat(era_t) - era_v) / sat(era_t)
              if np.isfinite(era_t) and np.isfinite(era_v) else np.nan)
        candidate = (sat(c_t) * (1 - rh / 100)
                     if np.isfinite(c_t) and np.isfinite(rh) else np.nan)
        is_d = x.source_origin_class == "BOTH_FINITE_DIFFER"
        if is_d:
            if (key not in dg or key in dh or key in eh
                or not np.isfinite(d_v) or not same(d_v, e_v)
                or not same(d_v, candidate)):
                raise ValueError("24 signed Stage12d candidate stage/source formula mismatch: " + str(key))
            held_d = ""
            held_e = ""
            dv = val(dg[key].new_VPD_USE_hPa)
            if not same(dv, d_v):
                raise ValueError("Stage12d repair ledger VPD != held reference " + str(key))
        else:
            if (key not in dh or key not in eh or key in dg
                or np.isfinite(d_v) or np.isfinite(e_v)):
                raise ValueError("Eight original-only Stage12d/e held source references changed " + str(key))
            held_d = str(dh[key].hold_reason)
            held_e = str(eh[key].science_hold_reason)
        rows.append({
            "site": x.site, "held_native_key": x.held_native_key,
            "neighbor_native_key": x.neighbor_native_key,
            "neighbor_side": x.neighbor_side,
            "source_origin_class": x.source_origin_class,
            "source_VPD_F_QC": int(raw_qc),
            "original_FLUXMET_VPD_F_hPa": raw_v,
            "original_FLUXMET_TA_F_C": raw_t,
            "original_FLUXMET_PA_F_kPa": raw_p,
            "paired_native_TA_ERA_C": era_t,
            "paired_native_VPD_ERA_hPa": era_v,
            "Stage12c_source_TA_USE_C": c_t,
            "Stage12c_source_PSRF_Pa": c_p,
            "original_RAW_VPD_vs_C_site_saturation_hPa": sat(c_t),
            "original_RAW_VPD_minus_C_saturation_hPa": raw_v - sat(c_t),
            "Stage12c_baseline_source": source,
            "Stage12c_prephysics_candidate_VPD_hPa": baseline,
            "Stage12c_precise_basic_source_screen": creason,
            "Stage12c_baseline_QBOT_if_valid": qb,
            "Stage12c_VPD_USE_hPa": c_v,
            "companion_ERA_implied_water_RH_pct": rh,
            "companion_ERA_transferred_VPD_at_site_T_hPa": candidate,
            "tower_minus_native_companion_ERA_T_C": c_t - era_t,
            "Stage12d_signed_VPD_USE_hPa": d_v,
            "Stage12e_signed_VPD_USE_hPa": e_v,
            "Stage12g_final_signed_VPD_USE_hPa": g_v,
            "raw_minus_Stage12d_hPa": raw_v - d_v,
            "Stage12d_science_hold_reason": held_d,
            "Stage12e_science_hold_reason": held_e,
            "Stage12g_new_final_shadow_value_only": bool(np.isfinite(g_v) and not np.isfinite(e_v)),
            "new_source_or_forcing_repairs": 0,
            "original_86_science_holds_preserved": True
        })
    df = pd.DataFrame(rows).sort_values(["site", "neighbor_native_key"])
    finite = df.loc[df.source_origin_class.eq("BOTH_FINITE_DIFFER")]
    absent = df.loc[df.source_origin_class.eq("RAW_ONLY_FINITE")]
    if (len(finite) != 24 or len(absent) != 8
        or absent.Stage12g_new_final_shadow_value_only.sum() != 2):
        raise ValueError("Expected exactly 24 Stage12d finite changes, 8 E missing, 2 G finite")
    a = df.groupby(["site", "source_origin_class",
                    "Stage12c_precise_basic_source_screen"],
                   dropna=False, as_index=False).agg(
        neighbor_sides=("neighbor_native_key", "size"),
        unique_held_times=("held_native_key", "nunique"),
        Stage12g_new_finite=("Stage12g_new_final_shadow_value_only", "sum"))
    b = absent.groupby(["site", "Stage12d_science_hold_reason",
                        "Stage12e_science_hold_reason"],
                       dropna=False, as_index=False).agg(
        original_RAW_only_neighbor_sides=("neighbor_native_key", "size"),
        Stage12g_new_finite=("Stage12g_new_final_shadow_value_only", "sum"))
    return df, finite, absent, a, b

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    for flag in ("self-test", "check", "run"):
        group.add_argument("--" + flag, action="store_true")
    args = ap.parse_args()
    print("STAGE12R — ORIGINAL 32 QC1 EDGE VPD INITIAL SCREEN / 12D ERA / 12E HOLDS | " + VERSION, flush=True)
    selftest()
    if args.self_test:
        return
    df, finite, absent, summary, reasons = classify()
    print("\n========== ORIGINAL 32 QC1 EDGE STAGE12C PHYSICS / SOURCE PRECEDENCE ==========", flush=True)
    print(summary.to_string(index=False), flush=True)
    print("\n========== 8 RAW-ONLY SOURCE STAGE12D/E SCIENCE HOLD REASONS ==========", flush=True)
    print(reasons.to_string(index=False), flush=True)
    print("\n========== 24 STAGE12D COMPANION ERA RH TRANSFER: ORIGINAL VS RECOMPUTED ==========", flush=True)
    print(finite[["site", "neighbor_native_key", "original_FLUXMET_VPD_F_hPa",
                  "paired_native_VPD_ERA_hPa", "companion_ERA_implied_water_RH_pct",
                  "Stage12d_signed_VPD_USE_hPa",
                  "Stage12c_precise_basic_source_screen"]].to_string(index=False), flush=True)
    print("\nSTAGE12R SUMMARY: original_QC1_edges=32 Stage12d_companion_ERA_finite_differences=24 "
          "Stage12e_RAW_only_missing=8 Stage12g_later_new_finite=2 "
          "new_source_or_forcing_repairs=0 86_original_science_holds_preserved=TRUE "
          "233_original_physics_holds_preserved=TRUE Postv5_approved=0 DATM_ready=0 spinup=0",
          flush=True)
    if args.check:
        print("STAGE12R CHECK ONLY: NO SOURCE, REPORT OR MODEL WRITES.", flush=True)
        return
    dest = ROOT / "reports" / (
        "stage12r_32_QC1_native_VPD_source_physics_and_ERA_RH_"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_"
        + uuid4().hex[:8])
    dest.mkdir(parents=True, exist_ok=False)
    tables = {
        "32_exact_source_QC1_VPD_native_C_D_E_G_science_triage.csv": df,
        "24_Stage12d_companion_ERA_VPD_transfers.csv": finite,
        "8_original_raw_only_unresolved_VPD_edges.csv": absent,
        "stage12c_native_VPD_failure_screen_summary.csv": summary,
        "stage12d_and_stage12e_hold_reason_8_edge_summary.csv": reasons,
    }
    for name, tab in tables.items():
        tab.to_csv(dest / name, index=False)
    (dest / "SCIENCE_HOLD.md").write_text(
        "Exact 32 QC1 original source neighboring sides: Stage12c initial water-VPD "
        "physics and Stage12d exact native ERA-RH transfer forensic analysis. "
        "The 24 companion ERA products are not independent measured tower truth; "
        "the 8 missing Stage12e reference values cannot be filled by merely "
        "trusting source QC1. Original VPD 4hPa jump criterion, tower-grid 5C "
        "guard, 86 held native events, original 233 protected physical holds, "
        "all original source releases/clock/forcing/model jobs unchanged. "
        "Post-v5, DATM and spinup NOT APPROVED.\n")
    sigs = {name: sha(dest / name) for name in [*tables, "SCIENCE_HOLD.md"]}
    record = {
        "version": VERSION,
        "original_stage12q_SHA256": sha(Q / "stage12q_science_report_SHA_receipt.json"),
        "original_32_QC1_edges": True,
        "original_24_stage12d_candidates_provenance_verified": True,
        "original_8_missing_Stage12e_reference_edges_protected": True,
        "original_86_science_holds_preserved": True,
        "original_233_source_physics_holds_preserved": True,
        "original_tower_T_P_clock_unchanged": True,
        "new_source_or_forcing_repairs": 0,
        "Postv5_approved": 0, "DATM_ready": 0,
        "spinup_authorized": 0, "output_SHA256": sigs
    }
    (dest / "stage12r_science_only_SHA_receipt.json").write_text(
        json.dumps(record, indent=2) + "\n")
    print("STAGE12R SOURCE-ONLY SHA REPORT DIR:", dest, flush=True)
    print("NO ORIGINAL SOURCE, FORCING, DATM, CIME OR SLURM WRITES.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12R STOP:", exc, file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

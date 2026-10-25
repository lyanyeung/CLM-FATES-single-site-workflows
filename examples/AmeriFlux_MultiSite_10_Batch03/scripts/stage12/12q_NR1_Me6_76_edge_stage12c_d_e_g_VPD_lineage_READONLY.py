#!/usr/bin/env python3
"""Batch03 Stage12q: forensic origin of 76 held-VPD adjacent reference sides.

Read only: compare signed Stage12p sources with the EXACT Stage12c/d/e/g
native timestamps and complete lineage for US-Me6 and US-NR1. Attribute
the 24 both-finite but differing QC1 source/Stage12e VPD values to the
latest actual upstream row-changing stage (12b/c, 12d, or 12e).
Determine when eight original-finite QC1 values became Stage12e-missing.

The report is about SOURCE PROVENANCE, not authorising a hypothetical
VPD jump. Stage12g can mask rejected trial neighbours. Original 86
held temperature/VPD cases, 233 earlier science holds, QC0 tower TA,
original VPD/pressure/time, Post-v5, DATM and spinup remain protected.

--self-test: synthetic classification only (no filesystem IO).
--check: verify signed inputs, calculate comparison, ZERO FILE WRITES.
--run: exactly one fresh isolated SHA-receipted science REPORT ONLY.
"""
import argparse
import hashlib
import json
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode = True

VERSION = "batch03-stage12q-v1-20261025-76-edge-CDEG-native-VPD-source-lineage"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
P = ROOT / "reports/stage12p_NR1_Me6_QC1_VPD_neighbor_origin_and_jump_sensitivity_20261025T091906Z_d349135a"
P_RECEIPT = "stage12p_QC1_source_provenance_SHA_receipt.json"
P_TABLE = "76_native_edge_rejected_candidate_RAW_vs_Stage12e_vs_final.csv"
SNAPSHOTS = {
    "C": ("stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e",
          "stage12c_research_shadow_SHA_receipt.json", "STAGE12C_NOT_MODEL_READY_NOLEAP"),
    "D": ("stage12d_six_site_companion_RH_gap_recovery_20261024T121810Z_f1fa4cee",
          "stage12d_research_shadow_SHA_receipt.json", "STAGE12D_NOT_MODEL_READY_NOLEAP"),
    "E": ("stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97",
          "stage12e_research_only_sha_receipt.json", "STAGE12E_INCOMPLETE_NOLEAP"),
    "G": ("stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f",
          "stage12g_research_only_sha_receipt.json", "STAGE12G_INCOMPLETE_NOLEAP"),
}
SITES = ("US-Me6", "US-NR1")
PROVENANCE = {
    "B": ("C", "1687_exact_native_RH_patch_provenance.csv"),
    "D": ("D", "guarded_companion_ERA_RH_auto_candidate_timestamps.csv"),
    "E": ("E", "new_site_year_gridRH_repair_candidates.csv"),
}

def safe(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or symlinked signed evidence: " + str(path))
    return path

def sha(path):
    h = hashlib.sha256()
    with safe(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()

def same(a, b):
    if pd.isna(a) or pd.isna(b):
        return pd.isna(a) and pd.isna(b)
    return np.isclose(float(a), float(b), atol=1e-7, rtol=0)

def origin_class(raw, prior):
    if np.isfinite(raw) and np.isfinite(prior):
        return "BOTH_FINITE_MATCH" if same(raw, prior) else "BOTH_FINITE_DIFFER"
    if np.isfinite(raw):
        return "RAW_ONLY_FINITE"
    if np.isfinite(prior):
        return "STAGE12E_ONLY_FINITE"
    return "BOTH_MISSING"

def lineage(c, d, e, is_b, is_d, is_e):
    """Stage of retained Stage12e value, not claimed tower ground truth."""
    if not np.isfinite(e):
        return "STAGE12E_MISSING"
    if not same(d, e):
        if not is_e:
            raise ValueError("Stage12e value changed without Stage12e signed repair key")
        return "STAGE12E_GRID_RH_CANDIDATE"
    if not same(c, d):
        if not is_d:
            raise ValueError("Stage12d value changed without Stage12d signed repair key")
        return "STAGE12D_COMPANION_ERA_RH_CANDIDATE"
    return ("STAGE12B_GRID_RH_IMPORTED_IN_12C" if is_b
            else "STAGE12C_RAW_OR_COMPANION_BASELINE")

def selftest():
    assert origin_class(5, 5) == "BOTH_FINITE_MATCH"
    assert origin_class(5, 4) == "BOTH_FINITE_DIFFER"
    assert origin_class(5, np.nan) == "RAW_ONLY_FINITE"
    assert origin_class(np.nan, 2) == "STAGE12E_ONLY_FINITE"
    assert origin_class(np.nan, np.nan) == "BOTH_MISSING"
    assert lineage(np.nan, 3, 3, False, True, False).startswith("STAGE12D")
    assert lineage(np.nan, np.nan, 2, False, False, True).startswith("STAGE12E")
    assert lineage(4, 4, 4, True, False, False).startswith("STAGE12B")
    assert lineage(4, 4, 4, False, False, False).startswith("STAGE12C")
    assert lineage(4, 4, np.nan, False, False, False) == "STAGE12E_MISSING"
    for args in ((np.nan, np.nan, 2, False, False, False),
                 (np.nan, 2, 2, False, False, False)):
        try:
            lineage(*args)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsigned Stage12d/e value modification allowed")
    print("STAGE12Q SELF-TEST PASS: strict native VPD-stage attribution, missing and conflicting values; NO WRITES", flush=True)

def verify():
    rp = json.loads(safe(P / P_RECEIPT).read_text())
    if (rp.get("version") != "batch03-stage12p-v1-20261025-NR1-Me6-VPD-QC1-neighbor-provenance"
        or rp.get("original_86_T_or_VPD_holds_unchanged") is not True
        or rp.get("original_38_VPD_jump_holds_unchanged") is not True
        or rp.get("original_76_source_neighbors_unchanged") is not True
        or rp.get("new_humidity_repair_candidates") != 0):
        raise ValueError("Pinned Stage12p science-only receipt changed")
    for name, digest in rp["output_SHA256"].items():
        if sha(P / name) != digest:
            raise ValueError("Stage12p signed source output changed: " + name)

    folders, receipts = {}, {}
    for label, (dirname, receiptname, suffix) in SNAPSHOTS.items():
        folder = ROOT / "science_trials" / dirname
        receipt = json.loads(safe(folder / receiptname).read_text())
        if (receipt.get("Postv5_approved") != 0
            or receipt.get("DATM_ready") != 0
            or receipt.get("spinup_authorized") != 0
            or receipt.get("INCOMPLETE_marker_present") is not True):
            raise ValueError("Original incomplete scientific forcing release gate changed: " + label)
        entries = receipt.get("output_sha256")
        if not isinstance(entries, dict):
            raise ValueError("Missing upstream complete SHA manifest: " + label)
        for site in SITES:
            name = site + "_" + suffix + ".csv"
            if name not in entries or sha(folder / name) != entries[name]:
                raise ValueError("Unsigned or modified original native site research shadow " + label + ": " + site)
        folders[label] = folder
        receipts[label] = (receipt, sha(folder / receiptname))

    c, d, e, g = (receipts[s][0] for s in "CDEG")
    if (d.get("prior_Stage12c_SHA256") != receipts["C"][1]
        or e.get("source_Stage12d_receipt_SHA256") != receipts["D"][1]
        or g.get("pinned_Stage12e_SHA256") != receipts["E"][1]
        or c.get("physically_held_times_intentionally_missing") != 233
        or d.get("original_233_physics_holds_as_NaN") is not True
        or e.get("original_233_science_holds_unchanged") is not True
        or g.get("original_233_physics_holds_untouched") is not True
        or g.get("new_numerical_ERA5Land_RH_only_research_repairs") != 138):
        raise ValueError("Science archive C-D-E-G upstream receipt chain or 233 holds differed")
    for label, (folderlabel, fname) in PROVENANCE.items():
        r = receipts[folderlabel][0]
        if fname not in r["output_sha256"] or sha(folders[folderlabel] / fname) != r["output_sha256"][fname]:
            raise ValueError("Original signed stage provenance ledger changed: " + label)
    return folders, receipts

def native_key(times):
    if not times.str.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d").all():
        raise ValueError("Research native calendar serialisation changed")
    return times.str.replace(r"[^0-9]", "", regex=True).str.slice(0, 12)

def analyse():
    folders, receipts = verify()
    frame = pd.read_csv(safe(P / P_TABLE), dtype={
        "held_native_key": str, "neighbor_native_key": str}, low_memory=False)
    if (len(frame) != 76 or frame.site.isin(SITES).sum() != 76
        or len(frame[["site", "held_native_key"]].drop_duplicates()) != 38
        or frame.original_FLUXMET_VPD_F_QC.eq("QC1").sum() != 71
        or frame.original_FLUXMET_VPD_F_QC.eq("QC0").sum() != 5):
        raise ValueError("Source-native 76-side 38-held-event identity changed")
    if frame.duplicated(["site", "held_native_key", "neighbor_native_key", "neighbor_side"]).any():
        raise ValueError("Duplicate signed source-side ID")

    stageframes = {}
    for stage in "CDEG":
        pieces = []
        for site in SITES:
            fname = site + "_" + SNAPSHOTS[stage][2] + ".csv"
            full = pd.read_csv(safe(folders[stage] / fname),
                               usecols=["time", "VPD_USE"],
                               dtype={"time": str}, low_memory=False)
            keys = native_key(full.time)
            if keys.duplicated().any():
                raise ValueError("Duplicate source-native stage time " + stage + " " + site)
            pieces.append(pd.DataFrame({
                "site": site,
                "neighbor_native_key": keys,
                stage + "_VPD_hPa": pd.to_numeric(full.VPD_USE, errors="coerce")}))
        stageframes[stage] = pd.concat(pieces, ignore_index=True)
        frame = frame.merge(stageframes[stage], on=["site", "neighbor_native_key"],
                            how="left", validate="many_to_one", indicator=True)
        if not frame.pop("_merge").eq("both").all():
            raise ValueError("Source-native original neighbor not in " + stage + " snapshot")

    raw = pd.to_numeric(frame.original_FLUXMET_VPD_F_hPa, errors="coerce")
    e = pd.to_numeric(frame.E_VPD_hPa, errors="coerce")
    g = pd.to_numeric(frame.G_VPD_hPa, errors="coerce")
    olde = pd.to_numeric(frame.original_stage12e_repaired_neighbor_VPD_USE_hPa, errors="coerce")
    oldg = pd.to_numeric(frame.final_stage12g_neighbor_VPD_USE_hPa, errors="coerce")
    if (not all(same(x, y) for x, y in zip(e, olde))
        or not all(same(x, y) for x, y in zip(g, oldg))):
        raise ValueError("Exact Stage12p preserved VPD does not equal signed Stage12e/G native row")
    if not all(same(x, y) for x, y in zip(e[e.notna()], g[e.notna()])):
        raise ValueError("Stage12g changed already finite Stage12e VPD")
    stageclasses = [origin_class(x, y) for x, y in zip(raw, e)]
    if stageclasses != frame.source_origin_class.tolist():
        raise ValueError("Stage12p original source/QC1 VPD classes no longer reproduce")
    qc1 = frame.original_FLUXMET_VPD_F_QC.eq("QC1")
    cls = frame.source_origin_class
    if (int((qc1 & cls.eq("BOTH_FINITE_MATCH")).sum()) != 39
        or int((qc1 & cls.eq("BOTH_FINITE_DIFFER")).sum()) != 24
        or int((qc1 & cls.eq("RAW_ONLY_FINITE")).sum()) != 8):
        raise ValueError("Stage12p exact 39/24/8 source partition changed")

    memberships = {}
    for label, (stage, name) in PROVENANCE.items():
        report = pd.read_csv(safe(folders[stage] / name),
                             usecols=["site", "native_key"],
                             dtype={"native_key": str}, low_memory=False)
        if report.duplicated(["site", "native_key"]).any():
            raise ValueError("Signed stage repair provenance duplicated " + label)
        memberships[label] = set(zip(report.site, report.native_key))

    classified = []
    for row in frame.itertuples(index=False):
        key = (row.site, row.neighbor_native_key)
        classified.append(lineage(row.C_VPD_hPa, row.D_VPD_hPa, row.E_VPD_hPa,
                                  key in memberships["B"],
                                  key in memberships["D"],
                                  key in memberships["E"]))
    frame["stage12e_retained_VPD_value_lineage"] = classified
    frame["stage12b_signed_patch_key"] = [
        (s, k) in memberships["B"] for s, k in zip(frame.site, frame.neighbor_native_key)]
    frame["stage12d_signed_patch_key"] = [
        (s, k) in memberships["D"] for s, k in zip(frame.site, frame.neighbor_native_key)]
    frame["stage12e_signed_patch_key"] = [
        (s, k) in memberships["E"] for s, k in zip(frame.site, frame.neighbor_native_key)]
    frame["original_source_raw_VPD_finite"] = raw.notna()
    frame["Stage12e_reference_finite"] = e.notna()
    frame["stage12g_final_reference_finite"] = g.notna()
    frame["SCIENTIFIC_HOLD_UNCHANGED"] = True

    summary = frame.groupby(["site", "original_FLUXMET_VPD_F_QC",
                             "source_origin_class",
                             "stage12e_retained_VPD_value_lineage"],
                            dropna=False, as_index=False).agg(
        neighbor_sides=("held_native_key", "size"),
        unique_held_event_times=("held_native_key", "nunique"),
        final_reference_finite_sides=("stage12g_final_reference_finite", "sum"))
    target = frame.loc[qc1 & cls.ne("BOTH_FINITE_MATCH")].copy()
    if len(target) != 32:
        raise ValueError("Lost original 32 QC1 disagreement sides")
    return frame, target, summary, receipts

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    flags = ap.add_mutually_exclusive_group(required=True)
    for flag in ("self-test", "check", "run"):
        flags.add_argument("--" + flag, action="store_true")
    a = ap.parse_args()
    print("STAGE12Q — EXACT 76 SOURCE VPD EDGES VS 12C/D/E/G | " + VERSION, flush=True)
    selftest()
    if a.self_test:
        return
    full, target, summary, receipts = analyse()
    print("\n========== 32 ORIGINAL QC1 NONMATCHED SIDES BY VALUE ORIGIN ==========", flush=True)
    print(target.groupby(["site", "source_origin_class",
                          "stage12e_retained_VPD_value_lineage"]).size().to_string(), flush=True)
    print("\n========== EXACT 76 SIDES BY VERIFIED SOURCE STAGE ==========", flush=True)
    print(summary.to_string(index=False), flush=True)
    print("\nSTAGE12Q SUMMARY: 76_sides=TRUE 38_jump_holds=TRUE "
          "QC1_finite_differ=24 QC1_raw_only_finite=8 QC1_matches=39 "
          "original_86_holds_preserved=TRUE old_233_phys_holds=TRUE "
          "threshold_relaxation=FALSE extra_source_repairs=0 "
          "Postv5_approved=0 DATM_ready=0 spinup=0", flush=True)
    if a.check:
        print("STAGE12Q CHECK ONLY: NO SOURCE, REPORT OR MODEL WRITES.", flush=True)
        return
    dst = ROOT / "reports" / (
        "stage12q_76_original_VPD_edge_CDEG_lineage_"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "_" + uuid4().hex[:8])
    dst.mkdir(parents=True, exist_ok=False)
    tables = {
        "76_original_source_neighbor_stage12c_d_e_g_lineage.csv": full,
        "32_QC1_nonmatch_source_values_and_repair_stage.csv": target,
        "verified_VPD_source_lineage_76_side_summary.csv": summary}
    for name, val in tables.items():
        val.to_csv(dst / name, index=False)
    (dst / "SCIENCE_HOLD.md").write_text(
        "VALUE ORIGIN ONLY. Stage12c earlier raw/companion baseline and "
        "Stage12b/12d/12e research RH patches are NOT independent tower "
        "observations. Each of 38 original source-native Stage12g jump "
        "HOLDs remains. 48 measured tower T discrepancy holds remain. "
        "No physics cutoff, source QC, T/P/clock, previous stage "
        "input/output, DATM, CIME, Slurm or spinup modifications.\n")
    hashes = {name: sha(dst / name) for name in [*tables, "SCIENCE_HOLD.md"]}
    rec = {
        "version": VERSION,
        "original_stage12p_SHA256": sha(P / P_RECEIPT),
        "stage12c_d_e_g_receipt_SHA256": {k: v[1] for k, v in receipts.items()},
        "original_86_holds_unchanged": True,
        "original_233_protected_holds_unchanged": True,
        "original_native_T_P_clock_unchanged": True,
        "new_source_or_forcing_repairs": 0,
        "Postv5_approved": 0, "DATM_ready": 0,
        "spinup_authorized": 0,
        "output_SHA256": hashes}
    (dst / "stage12q_science_report_SHA_receipt.json").write_text(
        json.dumps(rec, indent=2) + "\n")
    print("STAGE12Q SOURCE PROVENANCE REPORT DIR:", dst, flush=True)
    print("ZERO ORIGINAL SOURCE, FORCE OR MODEL INPUT EDITS.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12Q STOP:", exc, file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

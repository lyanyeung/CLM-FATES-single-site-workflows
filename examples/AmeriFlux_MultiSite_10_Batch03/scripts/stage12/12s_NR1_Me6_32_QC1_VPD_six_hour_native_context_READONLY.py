#!/usr/bin/env python3
"""Stage12s: exact 32 QC1 VPD sides, original-source +/-6h chronology.

Input: SHA-sealed Stage12r 32-side physics report, Stage12q predecessor,
Stage12c -> original Stage07 input SHA manifest and original FLUXMET/ERA
source files. Compare original source QC0/QC1 air T and VPD, native
paired ERA air T/VPD, water saturation, implied RH, and continuity
without changing or smoothing any source/research value.

--self-test synthetic only; --check NO WRITES; --run creates only a
separate new signed SCIENCE REPORT (never a model forcing).
"""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode = True

VERSION = "batch03-stage12s-v3-20261025-QC1-VPD-QC0-physical-reference-pm6h"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
R = ROOT / "reports/stage12r_32_QC1_native_VPD_source_physics_and_ERA_RH_20261025T094639Z_a770eeb8"
Q = ROOT / "reports/stage12q_76_original_VPD_edge_CDEG_lineage_20261025T093514Z_044390c3"
C = ROOT / "science_trials/stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e"
S07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
R_INPUT = "32_exact_source_QC1_VPD_native_C_D_E_G_science_triage.csv"
SITES = {"US-Me6": {2015, 2017}, "US-NR1": {2022}}
RAW_COLS = ["TIMESTAMP_START", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC"]
ERA_COLS = ["TIMESTAMP_START", "TA_ERA", "VPD_ERA"]
SIDES = ["site", "held_native_key", "neighbor_native_key", "neighbor_side"]
WINDOW_HH = 12

def file(path):
    p = Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Original SHA-signed file missing or symlinked " + str(p))
    return p

def sha(path):
    h = hashlib.sha256()
    with file(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def number(col):
    a = pd.to_numeric(col, errors="coerce").to_numpy(dtype=float)
    a[~np.isfinite(a) | (a <= -9990)] = np.nan
    return a

def es(t):
    t = np.asarray(t, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return 6.112 * np.exp(17.67 * t / (t + 243.5))

def implied_rh(t, v):
    sat = es(t)
    with np.errstate(divide="ignore", invalid="ignore"):
        return 100 * (sat - v) / sat

def same(a, b):
    if pd.isna(a) or pd.isna(b):
        return pd.isna(a) and pd.isna(b)
    return abs(float(a) - float(b)) <= 1e-7

def contiguous_center(flag, center=WINDOW_HH):
    if not bool(flag[center]):
        return 0
    a = b = center
    while a > 0 and bool(flag[a-1]):
        a -= 1
    while b+1 < len(flag) and bool(flag[b+1]):
        b += 1
    return b-a+1

def selftest():
    assert abs(float(es(20)) - 23.369471234) < 0.01
    assert float(implied_rh(20, 30)) < 0
    assert 0 < float(implied_rh(20, 3)) < 100
    assert contiguous_center([False]*12+[True]*5+[False]*8) == 5
    assert contiguous_center([False]*25) == 0
    assert same(np.nan, np.nan) and same(2., 2. + 1e-8)
    print("STAGE12S SELF-TEST PASS: 30min native +/-6h window, RH/physics, QC continuity; NO WRITES", flush=True)

def verify():
    rpath = R / "stage12r_science_only_SHA_receipt.json"
    receipt = json.loads(file(rpath).read_text())
    if (receipt.get("version") !=
            "batch03-stage12r-v1-20261025-32-QC1-sides-reused-native-Stage12c-12d-source-physics"
        or receipt.get("original_32_QC1_edges") is not True
        or receipt.get("original_86_science_holds_preserved") is not True
        or receipt.get("original_233_source_physics_holds_preserved") is not True
        or receipt.get("new_source_or_forcing_repairs") != 0
        or receipt.get("Postv5_approved") != 0
        or receipt.get("DATM_ready") != 0
        or receipt.get("spinup_authorized") != 0):
        raise ValueError("Stage12r science HOLD receipt changed")
    for name, digest in receipt["output_SHA256"].items():
        if sha(R / name) != digest:
            raise ValueError("Stage12r output SHA changed " + name)
    if (receipt.get("original_stage12q_SHA256") !=
            sha(Q / "stage12q_science_report_SHA_receipt.json")):
        raise ValueError("Stage12q signed ancestor SHA changed")
    qrec = json.loads(file(Q / "stage12q_science_report_SHA_receipt.json").read_text())
    if qrec.get("stage12c_d_e_g_receipt_SHA256", {}).get("C") != sha(
            C / "stage12c_research_shadow_SHA_receipt.json"):
        raise ValueError("Stage12c sealed ancestor changed")
    c = json.loads(file(C / "stage12c_research_shadow_SHA_receipt.json").read_text())
    if (c.get("stage07_manifest_SHA256") != sha(S07 / "exact_input_manifest.json")
        or c.get("physically_held_times_intentionally_missing") != 233
        or c.get("Postv5_approved") != 0):
        raise ValueError("Original Stage07 manifest or Stage12c science policy changed")
    manifest = json.loads(file(S07 / "exact_input_manifest.json").read_text())
    specs = {r["site"]: r for r in manifest["sites"]}
    pins = {str(Path(p).resolve()): digest for p, digest in manifest["input_sha256"].items()}
    for site in SITES:
        if site not in specs:
            raise ValueError("Source site absent in signed Stage07 manifest " + site)
        for field in ("primary", "era"):
            f = file(specs[site][field])
            if sha(f) != pins.get(str(f.resolve())):
                raise ValueError("Original source SHA changed " + site + " " + field)
    return specs, receipt

def load_years(spec, site):
    def take(path, cols):
        df = pd.read_csv(file(path), usecols=cols,
                         dtype={"TIMESTAMP_START": str}, low_memory=False)
        # Original release native labels: selected source years only.
        df = df.loc[df.TIMESTAMP_START.str.slice(0,4).isin(
            [str(y) for y in SITES[site]])].copy()
        if df.TIMESTAMP_START.isna().any() or df.TIMESTAMP_START.duplicated().any():
            raise ValueError("Source native timestamp duplicate or absent " + site)
        dt = pd.to_datetime(df.TIMESTAMP_START, format="%Y%m%d%H%M", errors="raise")
        if ((dt.dt.month == 2) & (dt.dt.day == 29)).any():
            raise ValueError("Unexpected leap day in selected three non-leap source years")
        return df.sort_values("TIMESTAMP_START").reset_index(drop=True)
    a = take(spec["primary"], RAW_COLS)
    b = take(spec["era"], ERA_COLS)
    if (len(a) != sum(17520 for _ in SITES[site])
        or len(b) != len(a)
        or not a.TIMESTAMP_START.equals(b.TIMESTAMP_START)):
        raise ValueError("Exact native FLUXMET/companion ERA selected years differ " + site)
    t = pd.DatetimeIndex(pd.to_datetime(a.TIMESTAMP_START,
                                      format="%Y%m%d%H%M", errors="raise"))
    native = pd.DataFrame({"site":site, "native_key":a.TIMESTAMP_START.copy()})
    for col in RAW_COLS[1:]:
        native[col] = number(a[col])
    for col in ERA_COLS[1:]:
        native[col] = number(b[col])
    native["dt"] = t
    return native

def analyse():
    specs, receipt = verify()
    targets = pd.read_csv(file(R / R_INPUT), dtype={
        "held_native_key": str, "neighbor_native_key": str}, low_memory=False)
    if (len(targets) != 32 or targets.duplicated(SIDES).any()
        or not targets.site.isin(SITES).all()
        or int(targets.source_origin_class.eq("BOTH_FINITE_DIFFER").sum()) != 24
        or int(targets.source_origin_class.eq("RAW_ONLY_FINITE").sum()) != 8
        or not targets.source_VPD_F_QC.eq(1).all()):
        raise ValueError("Original 32 signed native source-side identities changed")
    long = []
    short = []
    for site in SITES:
        a = load_years(specs[site], site)
        keys = a.native_key.tolist()
        pos = {k:i for i,k in enumerate(keys)}
        assert len(pos) == len(a)
        src_t = a.TA_F.to_numpy(dtype=float)
        src_v = a.VPD_F.to_numpy(dtype=float)
        src_tqc = a.TA_F_QC.to_numpy(dtype=float)
        src_vqc = a.VPD_F_QC.to_numpy(dtype=float)
        era_t = a.TA_ERA.to_numpy(dtype=float)
        era_v = a.VPD_ERA.to_numpy(dtype=float)
        native_times = a.dt.to_numpy()
        bound = es(src_t)
        phys_valid = (np.isfinite(src_t) & np.isfinite(src_v) &
                      np.isfinite(bound) & (src_v >= 0) & (src_v < bound))
        invalid = (np.isfinite(src_t) & np.isfinite(src_v) &
                   np.isfinite(bound) & ~phys_valid)
        derived_rh = implied_rh(src_t, src_v)
        era_rh = implied_rh(era_t, era_v)
        for event in targets.loc[targets.site.eq(site)].itertuples(index=False):
            key = event.neighbor_native_key
            if key not in pos:
                raise ValueError("Original held VPD native side missing " + site + " " + key)
            i = pos[key]
            if (not same(src_t[i], event.original_FLUXMET_TA_F_C)
                or not same(src_v[i], event.original_FLUXMET_VPD_F_hPa)
                or not same(era_t[i], event.paired_native_TA_ERA_C)
                or not same(era_v[i], event.paired_native_VPD_ERA_hPa)
                or src_vqc[i] != 1):
                raise ValueError("Original Stage12r source values/QC changed " + site + " " + key)
            left, right = i-WINDOW_HH, i+WINDOW_HH+1
            if left < 0 or right > len(a):
                raise ValueError("Original native context crosses absent year boundary " + key)
            idx = np.arange(left, right)
            times = native_times[idx]
            if len(idx) != 25 or not (
                np.diff(times).astype("timedelta64[m]").astype(int) == 30
            ).all():
                raise ValueError("Original full +/-6h half-hour chronology irregular " + key)
            near_qc0 = (src_vqc[idx] == 0) & phys_valid[idx]
            before = idx[(idx < i) & near_qc0]
            after = idx[(idx > i) & near_qc0]
            prev_i = int(before[-1]) if len(before) else None
            next_i = int(after[0]) if len(after) else None
            for j in idx:
                long.append({
                    "site":site, "held_native_key":event.held_native_key,
                    "neighbor_native_key":key, "neighbor_side":event.neighbor_side,
                    "source_origin_class":event.source_origin_class,
                    "native_key":keys[j],
                    "relative_minutes_to_neighbor":int((j-i)*30),
                    "source_TA_F_C":src_t[j], "source_TA_F_QC":src_tqc[j],
                    "source_VPD_F_hPa":src_v[j], "source_VPD_F_QC":src_vqc[j],
                    "water_es_at_source_T_hPa":bound[j],
                    "original_VPD_minus_water_es_hPa":src_v[j]-bound[j],
                    "implied_original_water_RH_pct":derived_rh[j],
                    "source_original_VPD_physically_impossible":bool(invalid[j]),
                    "paired_native_TA_ERA_C":era_t[j],
                    "paired_native_VPD_ERA_hPa":era_v[j],
                    "paired_native_water_RH_pct":era_rh[j],
                    "tower_minus_companion_ERA_T_C":src_t[j]-era_t[j],
                    "original_clock_unchanged":True
                })
            short.append({
                "site":site, "held_native_key":event.held_native_key,
                "neighbor_native_key":key, "neighbor_side":event.neighbor_side,
                "source_origin_class":event.source_origin_class,
                "focal_source_TA_F_C":src_t[i],
                "focal_source_TA_F_QC":src_tqc[i],
                "focal_source_VPD_F_QC":src_vqc[i],
                "focal_source_VPD_F_hPa":src_v[i],
                "focal_source_VPD_minus_es_hPa":src_v[i]-bound[i],
                "focal_source_implied_RH_pct":derived_rh[i],
                "focal_Stage12c_RAW_VPD_minus_es_at_TA_USE_hPa":
                    event.original_RAW_VPD_minus_C_saturation_hPa,
                "focal_paired_TA_ERA_C":era_t[i],
                "focal_paired_VPD_ERA_hPa":era_v[i],
                "focal_paired_water_RH_pct":era_rh[i],
                "focal_source_minus_ERA_T_C":src_t[i]-era_t[i],
                "focal_Stage12c_TA_USE_C":event.Stage12c_source_TA_USE_C,
                "focal_TA_F_equals_Stage12c_TA_USE":same(
                    src_t[i],event.Stage12c_source_TA_USE_C),
                "focal_Stage12d_retained_VPD_hPa":event.Stage12d_signed_VPD_USE_hPa,
                "focal_Stage12e_retained_VPD_hPa":event.Stage12e_signed_VPD_USE_hPa,
                "focal_Stage12g_final_VPD_hPa":event.Stage12g_final_signed_VPD_USE_hPa,
                "Stage12d_science_hold_reason":event.Stage12d_science_hold_reason,
                "Stage12e_science_hold_reason":event.Stage12e_science_hold_reason,
                "context_original_QC0_T_halfhours":int((src_tqc[idx]==0).sum()),
                "context_original_QC0_physically_valid_VPD_halfhours":int(near_qc0.sum()),
                "context_original_QC1_VPD_halfhours":int((src_vqc[idx]==1).sum()),
                "context_original_impossible_VPD_halfhours":int(invalid[idx].sum()),
                "context_original_QC1_impossible_VPD_halfhours":int(
                    (invalid[idx] & (src_vqc[idx]==1)).sum()),
                "context_original_QC0_impossible_VPD_halfhours":int(
                    (invalid[idx] & (src_vqc[idx]==0)).sum()),
                "context_center_impossible_consecutive_halfhours":int(
                    contiguous_center(invalid[idx])),
                "nearest_prior_QC0_valid_VPD_native_key": (
                    keys[prev_i] if prev_i is not None else ""),
                "nearest_prior_QC0_valid_VPD_hPa": (
                    src_v[prev_i] if prev_i is not None else np.nan),
                "nearest_next_QC0_valid_VPD_native_key": (
                    keys[next_i] if next_i is not None else ""),
                "nearest_next_QC0_valid_VPD_hPa": (
                    src_v[next_i] if next_i is not None else np.nan),
                "hold_released":False
            })
    windows = pd.DataFrame(long).sort_values(
        ["site","held_native_key","neighbor_native_key","relative_minutes_to_neighbor"])
    focal = pd.DataFrame(short).sort_values(
        ["site","neighbor_native_key","held_native_key"])
    if (len(focal) != 32 or len(windows) != 800
        or not all(same(x,y) for x,y in zip(
            focal.focal_source_VPD_minus_es_hPa.values,
            focal.focal_source_VPD_F_hPa.values - es(focal.focal_source_TA_F_C.values)))
        or not focal.focal_Stage12c_RAW_VPD_minus_es_at_TA_USE_hPa.ge(-1e-7).all()):
        raise ValueError("32 Stage12c source physics holds or exact 25 rows/window changed")
    summary = focal.groupby(["site","source_origin_class"],
                            as_index=False).agg(
        source_sides=("neighbor_native_key","size"),
        focal_tower_T_QC0=("focal_source_TA_F_QC", lambda s:int(s.eq(0).sum())),
        median_excess_rawVPD_over_es_hPa=("focal_source_VPD_minus_es_hPa","median"),
        median_tower_minus_companionT_C=("focal_source_minus_ERA_T_C","median"),
        median_impossible_HH_in_pm6h=("context_original_impossible_VPD_halfhours","median"),
        with_QC0_valid_VPD_before=("nearest_prior_QC0_valid_VPD_native_key",
                                   lambda s:int(s.ne("").sum())),
        with_QC0_valid_VPD_after=("nearest_next_QC0_valid_VPD_native_key",
                                  lambda s:int(s.ne("").sum())))
    return windows, focal, summary

def main():
    p = argparse.ArgumentParser(description=__doc__)
    gr = p.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):
        gr.add_argument("--"+x,action="store_true")
    args = p.parse_args()
    print("STAGE12S — SOURCE-NATIVE ORIGINAL QC0/QC1 VPD/TA +/-6H CONTEXT | "+VERSION,flush=True)
    selftest()
    if args.self_test:
        return
    windows, focal, summary = analyse()
    print("\n========== 32 QC1 VPD SOURCE-NEIGHBOR CONTEXT SUMMARY ==========",flush=True)
    print(summary.to_string(index=False),flush=True)
    print("\n========== 8 RAW-ONLY SCIENCE HOLDS: ORIGINAL SOURCE TEMP/VPD CONTEXT ==========",flush=True)
    print(focal.loc[focal.source_origin_class.eq("RAW_ONLY_FINITE"),[
       "site","neighbor_native_key","focal_source_TA_F_C","focal_source_TA_F_QC",
       "focal_source_VPD_F_hPa","focal_source_VPD_minus_es_hPa",
       "focal_source_minus_ERA_T_C","context_original_impossible_VPD_halfhours",
       "nearest_prior_QC0_valid_VPD_native_key",
       "nearest_next_QC0_valid_VPD_native_key",
       "Stage12d_science_hold_reason"]].to_string(index=False),flush=True)
    print("\nSTAGE12S SUMMARY: 32_original_QC1_source_sides=TRUE "
          "800_native_source_context_rows=TRUE "
          "signed_Stage12r_QC1_tower_source_verified=TRUE "
          "new_source_or_forcing_repairs=0 Postv5_approved=0 DATM_ready=0 spinup=0",
          flush=True)
    if args.check:
        print("STAGE12S CHECK ONLY: NO REPORT, SOURCE OR MODEL WRITES.",flush=True)
        return
    dest = ROOT / "reports" / (
        "stage12s_32_QC1_native_VPD_pm6h_source_context_"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "_" + uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    outputs = {
        "800_original_halfhour_VPD_T_QC_and_native_ERA_context.csv":windows,
        "32_original_QC1_edge_physics_and_nearest_QC0_reference.csv":focal,
        "32_source_edge_pm6h_context_summary.csv":summary
    }
    for name, df in outputs.items():
        df.to_csv(dest/name,index=False)
    (dest/"SCIENCE_HOLD.md").write_text(
        "Exact original native-time +/-6-hour source-only diagnostic for "
        "32 QC1 VPD neighboring sides of 38 previously held Stage12g VPD "
        "events. QC0 VPD values are contextual references, not permission "
        "to overwrite QC1 sources. No source RH/temperature/VPD, native "
        "clock, threshold, preceding shadow, Post-v5/DATM/spinup or model "
        "jobs were changed. All 86 original holds and 233 protected older "
        "science holds remain.\n")
    hashes = {n:sha(dest/n) for n in [*outputs,"SCIENCE_HOLD.md"]}
    receipt = {
        "version":VERSION,
        "original_stage12r_SHA256":sha(R/"stage12r_science_only_SHA_receipt.json"),
        "original_32_QC1_sides_unchanged":True,
        "original_86_holds_unchanged":True,
        "original_233_physics_holds_unchanged":True,
        "original_source_T_VPD_P_clock_unchanged":True,
        "new_humidity_repairs":0,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
        "output_SHA256":hashes
    }
    (dest/"stage12s_science_context_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12S SOURCE-ONLY SCIENCE REPORT DIR:",dest,flush=True)
    print("ZERO SOURCE, FORCING, CIME, SLURM OR MODEL MUTATIONS.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12S STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

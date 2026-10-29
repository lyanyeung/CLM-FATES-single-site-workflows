#!/usr/bin/env python3
"""MtB03 (Claude workstream, US-MtB only): multi-level BASE fill candidates. READ ONLY.

User-approved order (2026-10-29), all rules fixed here BEFORE the first run:

TEMPERATURE (FLUXMET TA_F = BASE TA_1_1_1, 31 m)
  Plausible level value: -30 C <= T <= 45 C.
  Reference REF = median of plausible TA at 24 m (TA_1_2_1), 16 m (TA_1_3_1), 8.75 m (TA_1_4_1),
  only when >= 2 such levels exist and their spread (max - min) <= 1.5 C ("consensus").
  FAULT_31M  = TA_F < -30 C; or consensus and TA_F - REF < -5 C (31 m much COLDER than the levels
               below is unphysical in any regime); or consensus INCLUDING 24 m and TA_F - REF > 5 C
               (31 m much WARMER can be a real night inversion over a cold canopy/sub-canopy layer,
               so it is only called a fault when the 24 m sensor, 7 m below, disagrees too).
               [v1 design note: the warm-side 24 m requirement was added after a local dry run on the
               BASE file alone (2022-01-02, 2024-02-12 inversions with 24 m missing), before any IRIDIS run.]
  CLIP_31M   = BASE TA_1_1_1 missing, FLUXMET TA_F gap-filled (QC != 0), consensus REF <= -9.5 C
               (the 31/24 m sensors stop below -10 C in 2013-2020).
  Candidate  = TA_1_3_1 (16 m, consensus member) + offset, offset linearly interpolated between the
               mean (TA_31 - TA_16) of valid pairs in the 4 HH before / after (>= 2 each side; else
               12 HH); else the (month, hour) mean offset of all valid pairs (>= 20); else ERA-shape
               bridge if the run is <= 5 HH (MtB02 validated length); else HOLD.
  Validation: synthetic 31 m gaps of 1, 5, 22 HH where consensus holds, 2000 each, seed 20261029.
               Gate per length: MAE <= 1.0 C, |bias| <= 0.3 C, fraction |error| > 2 C <= 0.05.

HUMIDITY (targets: every Stage12g gap + every FAULT_31M row, whose 31 m VPD is not credible)
  Level transfer L24 / L16: e_L = RH_L/100 * esw(TA_L) (RH_L within [2, 103] %, TA_L plausible),
  vapour pressure kept, VPD at the 31 m temperature used (candidate T where replaced).
  Validated on FLUXMET truth (VPD_F_QC = TA_F_QC = 0, faults removed) where level L exists:
  Stage12j thresholds (N >= 50, valid >= 0.60, MAE <= 1.5 hPa, |bias| <= 0.7 hPa, > 2 hPa <= 0.10)
  per year (N >= 50) and pooled; LEVEL_PASS = pooled pass AND all gated years pass AND >= 3 gated
  years. The gap regime (TA_F - TA_ERA <= -5 C) is reported separately.
  Fill order per target: L24 (if LEVEL_PASS and formable) -> L16 (same) -> COMPANION_E
  (user-approved option B, 2026-10-28; in regime and formable) -> HOLD with reason.

Inputs: MtB01 loaders (pinned) for FLUXMET/ERA/Stage12g, and the user-supplied BASE 5-5 file
(--base, sha256 pinned). BASE TA_1_1_1 must equal FLUXMET TA_F at >= 99 % of QC0 rows.

--self-test synthetic only. --check full computation, prints, NO writes. --run writes ONE new
reports/mtb03_* folder (candidate tables + SHA receipt). Nothing is written to forcing; adoption
into a new research shadow is a separate, user-approved step.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-MtB03-v1-20261029-multilevel-BASE-fill-candidates-READONLY"
HERE = Path(__file__).resolve().parent
P_SCRIPT = HERE / "MtB02_temperature_fault_bridge_and_humidity_confirmation_READONLY.py"
P_BLOB = "b4649a824da07d99e5340ed521956be6fb66f44f"
BASE_SHA = "75be85401d1f7a3c8c1efff60244e60745a2ef19f3af2b4f71b7bb8c7c71d8ee"
BASE_DEFAULT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-MtB/forcing/raw/AMF_US-MtB_BASE_HH_5-5.csv")
LV_T = {"31": "TA_1_1_1", "24": "TA_1_2_1", "16": "TA_1_3_1", "8.75": "TA_1_4_1", "1.5": "TA_1_5_1"}
LV_RH = {"31": "RH_1_1_1", "24": "RH_1_2_1", "16": "RH_1_3_1"}
T_LO, T_HI = -30.0, 45.0
SPREAD_C, FAULT_DIFF_C, CLIP_REF_C = 1.5, 5.0, -9.5
OFF_HH, OFF_WIDE_HH, OFF_MIN, CLIM_MIN = 4, 12, 2, 20
BRIDGE_MAX_HH = 5
SYN_LENGTHS, SYN_N, SEED = (1, 5, 22), 2000, 20261029
T_GATE = dict(MAE=1.0, BIAS=0.3, BAD2=0.05)
RH_LO, RH_HI = 2.0, 103.0
MIN_LEVEL_YEARS = 3
REGIME_DT = -5.0


def load_mtb02():
    b = P_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != P_BLOB:
        raise ValueError("Pinned MtB02 Git blob mismatch: " + str(P_SCRIPT))
    spec = importlib.util.spec_from_file_location("mtb02_for_mtb03", P_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


P = load_mtb02()
M = P.M


# ----------------------------------------------------------------- BASE
def read_base(path, check_sha=True):
    if check_sha and M.sha(path) != BASE_SHA: raise ValueError("BASE 5-5 sha256 differs from the pinned file")
    cols = ["TIMESTAMP_START"] + list(LV_T.values()) + list(LV_RH.values()) + ["T_SONIC"]
    b = pd.read_csv(path, comment="#", usecols=cols, dtype={"TIMESTAMP_START": str}, low_memory=False)
    for c in cols[1:]: b[c] = M.num(b[c])
    if b.TIMESTAMP_START.duplicated().any(): raise ValueError("BASE duplicated timestamps")
    return b


def attach_base(df, base):
    x = df[["native_key"]].merge(base, left_on="native_key", right_on="TIMESTAMP_START", how="left", validate="one_to_one")
    if len(x) != len(df): raise ValueError("BASE merge changed row count")
    out = df.copy()
    for c in list(LV_T.values()) + list(LV_RH.values()) + ["T_SONIC"]: out[c] = x[c].to_numpy()
    q0 = (out.TA_F_QC == 0).to_numpy() & np.isfinite(out.TA_1_1_1.to_numpy()) & np.isfinite(out.TA_F.to_numpy())
    agree = float(np.mean(np.abs(out.TA_F.to_numpy()[q0] - out.TA_1_1_1.to_numpy()[q0]) <= 0.005)) if q0.any() else 0.0
    if agree < 0.99: raise ValueError(f"BASE TA_1_1_1 matches FLUXMET TA_F at only {agree:.3f} of QC0 rows")
    return out, agree


def plausible(a): a = np.asarray(a, float); return np.isfinite(a) & (a >= T_LO) & (a <= T_HI)


def consensus(df):
    L = np.column_stack([np.where(plausible(df[c]), df[c].to_numpy(float), np.nan) for c in ("TA_1_2_1", "TA_1_3_1", "TA_1_4_1")])
    n = np.isfinite(L).sum(1)
    with np.errstate(all="ignore"):
        spread = np.nanmax(L, 1) - np.nanmin(L, 1); ref = np.nanmedian(L, 1)
    ok = (n >= 2) & (spread <= SPREAD_C) & plausible(df.TA_1_3_1)
    return np.where(ok, ref, np.nan), ok


def t_targets(df, ref, ok):
    T = df.TA_F.to_numpy()
    has24 = ok & plausible(df.TA_1_2_1)
    with np.errstate(invalid="ignore"):
        cold = ok & np.isfinite(T) & (T - ref < -FAULT_DIFF_C)
        warm = has24 & np.isfinite(T) & (T - ref > FAULT_DIFF_C)
    fault = (np.isfinite(T) & (T < T_LO)) | cold | warm
    clip = (~np.isfinite(df.TA_1_1_1.to_numpy())) & (df.TA_F_QC.to_numpy() != 0) & ok & (ref <= CLIP_REF_C)
    return fault, clip & ~fault


def offsets(df, ok, exclude):
    T31, T16 = df.TA_1_1_1.to_numpy(), df.TA_1_3_1.to_numpy()
    pair = plausible(T31) & ok & ~exclude
    d = np.where(pair, T31 - T16, np.nan)
    clim = pd.DataFrame({"m": df.month, "h": df.hour, "d": d}).dropna().groupby(["m", "h"]).d.agg(["mean", "count"])
    return pair, d, clim


def level_fill(df, targets, ok, pair, d, clim):
    T16 = df.TA_1_3_1.to_numpy(); n = len(df)
    val = np.full(n, np.nan); how = np.full(n, "", dtype=object)
    for st, ln in M.runs(targets):
        i1 = st + ln - 1
        for w in (OFF_HH, OFF_WIDE_HH):
            b = [k for k in range(max(0, st - w), st) if pair[k]]; a = [k for k in range(i1 + 1, min(n, i1 + 1 + w)) if pair[k]]
            if len(b) >= OFF_MIN and len(a) >= OFF_MIN:
                ob, oa = float(np.mean(d[b])), float(np.mean(d[a])); fr = (np.arange(ln) + 1) / (ln + 1)
                seg = T16[st:i1 + 1] + ob + (oa - ob) * fr
                good = ok[st:i1 + 1]
                val[st:i1 + 1] = np.where(good, seg, np.nan); how[st:i1 + 1] = np.where(good, f"L16_local_offset_{w}HH", "")
                break
        for k in range(st, i1 + 1):
            if not np.isfinite(val[k]) and ok[k]:
                key = (int(df.month.iloc[k]), int(df.hour.iloc[k]))
                if key in clim.index and clim.loc[key, "count"] >= CLIM_MIN:
                    val[k] = T16[k] + float(clim.loc[key, "mean"]); how[k] = "L16_month_hour_offset"
    return val, how


def t_candidates(df):
    ref, ok = consensus(df)
    fault, clip = t_targets(df, ref, ok)
    pair, d, clim = offsets(df, ok, fault | clip)
    targets = fault | clip
    val, how = level_fill(df, targets, ok, pair, d, clim)
    # fallback: MtB02 ERA-shape bridge for short fault runs without level candidate
    T, Te = df.TA_F.to_numpy(), df.TA_ERA.to_numpy()
    valid = (df.TA_F_QC == 0).to_numpy() & ~targets & np.isfinite(T) & np.isfinite(Te)
    for st, ln in M.runs(targets & ~np.isfinite(val)):
        if ln <= BRIDGE_MAX_HH:
            b = P.bridge_run(T, Te, valid, st, st + ln - 1)
            if b is not None: val[st:st + ln] = b; how[st:st + ln] = "ERA_shape_bridge_le5HH"
    how = np.where(targets & ~np.isfinite(val), "HOLD_NO_T_CANDIDATE", how)
    return dict(ref=ref, ok=ok, fault=fault, clip=clip, val=val, how=how, pair=pair, d=d, clim=clim)


def t_validation(df, tc):
    pair, d, ok = tc["pair"], tc["d"], tc["ok"]
    T31 = df.TA_1_1_1.to_numpy(); n = len(df); rng = np.random.default_rng(SEED); rows = []
    for L in SYN_LENGTHS:
        good = np.convolve(pair.astype(int), np.ones(L, int), "valid") == L
        starts = np.flatnonzero(good); starts = starts[(starts >= OFF_WIDE_HH) & (starts + L + OFF_WIDE_HH < n)]
        rng.shuffle(starts); errs = []; used = 0; cold = []
        for s in starts:
            if used >= SYN_N: break
            mask = np.zeros(n, bool); mask[s:s + L] = True
            p2 = pair & ~mask
            v, _ = level_fill(df.iloc[max(0, s - OFF_WIDE_HH - 1): s + L + OFF_WIDE_HH + 1].reset_index(drop=True),
                              mask[max(0, s - OFF_WIDE_HH - 1): s + L + OFF_WIDE_HH + 1],
                              ok[max(0, s - OFF_WIDE_HH - 1): s + L + OFF_WIDE_HH + 1],
                              p2[max(0, s - OFF_WIDE_HH - 1): s + L + OFF_WIDE_HH + 1],
                              d[max(0, s - OFF_WIDE_HH - 1): s + L + OFF_WIDE_HH + 1], tc["clim"])
            o = s - max(0, s - OFF_WIDE_HH - 1)
            seg = v[o:o + L]
            if not np.isfinite(seg).all(): continue
            e = seg - T31[s:s + L]; errs.append(e); used += 1
            if np.nanmean(tc["ref"][s:s + L]) <= -5: cold.append(e)
        e = np.concatenate(errs) if errs else np.array([np.nan]); c = np.concatenate(cold) if cold else np.array([np.nan])
        r = {"length_HH": L, "synthetic_gaps": used, "MAE_C": float(np.nanmean(np.abs(e))), "bias_C": float(np.nanmean(e)),
             "P95_abs_C": float(np.nanpercentile(np.abs(e), 95)), "frac_abs_gt2C": float(np.nanmean(np.abs(e) > 2)),
             "cold_ref_le_-5_N": int(len(cold)), "cold_MAE_C": float(np.nanmean(np.abs(c)))}
        r["gate_pass"] = bool(used >= 100 and r["MAE_C"] <= T_GATE["MAE"] and abs(r["bias_C"]) <= T_GATE["BIAS"]
                              and r["frac_abs_gt2C"] <= T_GATE["BAD2"])
        rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------- humidity
def level_e(df, lev):
    rh, ta = df[LV_RH[lev]].to_numpy(float), df[LV_T[lev]].to_numpy(float)
    ok = np.isfinite(rh) & (rh >= RH_LO) & (rh <= RH_HI) & plausible(ta)
    return np.where(ok, rh / 100.0 * M.esw(ta), np.nan)


def humidity(df, fault, Tused):
    d = df.copy(); d.loc[fault, "truth"] = False
    T, P_ = d.TA_F.to_numpy(), d.P_Pa.to_numpy(); truth = d.truth.to_numpy()
    reg = d.dT.to_numpy() <= REGIME_DT
    yearly, verdict, e_lv = [], [], {}
    for lev in ("24", "16"):
        e = level_e(d, lev); e_lv[lev] = e
        okp = M.physical(T, P_, e); err = np.where(okp, M.esw(T) - e, np.nan) - d.VPD_F.to_numpy()
        has = truth & np.isfinite(e); passes = []
        for y in sorted(d.year.unique()):
            s = has & (d.year.to_numpy() == y)
            r = M.metrics(err[s], s.sum()); r.update(level=lev, year=int(y)); r["gate_pass"] = M.gate(r) if r["N"] >= 50 else None
            yearly.append(r)
            if r["gate_pass"] is not None: passes.append(r["gate_pass"])
        pooled = M.metrics(err[has], has.sum()); rg = M.metrics(err[has & reg], (has & reg).sum())
        verdict.append({"level_m": lev, "N": pooled["N"], "MAE_hPa": pooled["MAE_hPa"], "bias_hPa": pooled["bias_hPa"],
                        "frac_gt2hPa": pooled["frac_abs_err_gt2hPa"], "pooled_pass": bool(M.gate(pooled)),
                        "REGIME_N": rg["N"], "REGIME_MAE_hPa": rg["MAE_hPa"], "REGIME_bias_hPa": rg["bias_hPa"],
                        "REGIME_frac_gt2hPa": rg["frac_abs_err_gt2hPa"], "gated_years": len(passes),
                        "gated_years_pass": int(sum(passes)),
                        "LEVEL_PASS": bool(M.gate(pooled) and passes and all(passes) and len(passes) >= MIN_LEVEL_YEARS)})
    return e_lv, pd.DataFrame(yearly), pd.DataFrame(verdict)


def fill_humidity(df, gap, fault, Tused, e_lv, verdict):
    targets = gap | fault
    P_ = df.P_Pa.to_numpy(); Te = df.TA_ERA.to_numpy(); n = len(df)
    with np.errstate(invalid="ignore"):
        e_c = M.esw(Te) - df.VPD_ERA.to_numpy()
    e_c = np.where(np.isfinite(e_c) & (e_c > 0) & (e_c <= M.esw(Te)), e_c, np.nan)
    src = np.full(n, "", dtype=object); e_out = np.full(n, np.nan)
    passing = set(verdict.loc[verdict.LEVEL_PASS, "level_m"])
    T = Tused
    for lev in ("24", "16"):
        if lev not in passing: continue
        can = targets & (src == "") & M.physical(T, P_, e_lv[lev])
        src[can] = f"L{lev}_measured_RH_transfer"; e_out[can] = e_lv[lev][can]
    reg = (T - Te) <= REGIME_DT
    can = targets & (src == "") & reg & M.physical(T, P_, e_c)
    src[can] = "COMPANION_E_user_option_B"; e_out[can] = e_c[can]
    src = np.where(targets & (src == ""), np.where(~np.isfinite(T), "HOLD_NO_TEMPERATURE",
                   np.where(~reg, "HOLD_OUT_OF_REGIME", "HOLD_NOT_FORMABLE")), src)
    rows = pd.DataFrame({"native_key": df.native_key, "year": df.year, "month": df.month, "in_Stage12g_gap": gap,
                         "T_fault_31m": fault, "TA_used_C": T, "source": src,
                         "e_hPa": e_out, "VPD_hPa": np.where(np.isfinite(e_out), M.esw(T) - e_out, np.nan),
                         "QBOT_kgkg": np.where(np.isfinite(e_out), M.q_from_e(e_out, P_), np.nan),
                         "RH_water_pct": np.where(np.isfinite(e_out), 100 * e_out / M.esw(T), np.nan),
                         "RH_ice_pct": np.where(np.isfinite(e_out) & (T < 0), 100 * e_out / M.esi(T), np.nan)}).loc[targets]
    return rows.reset_index(drop=True)


def compute(df, gap):
    tc = t_candidates(df)
    tval = t_validation(df, tc)
    Tused = np.where((tc["fault"] | tc["clip"]) & np.isfinite(tc["val"]), tc["val"], df.TA_F.to_numpy())
    Tused = np.where(tc["fault"] & ~np.isfinite(tc["val"]), np.nan, Tused)
    e_lv, hy, hv = humidity(df, tc["fault"], Tused)
    hrows = fill_humidity(df, gap, tc["fault"], Tused, e_lv, hv)
    trows = pd.DataFrame({"native_key": df.native_key, "year": df.year, "class": np.where(tc["fault"], "FAULT_31M", np.where(tc["clip"], "CLIP_31M", "")),
                          "TA_F_C": df.TA_F, "TA_F_QC": df.TA_F_QC, "TA_31m": df.TA_1_1_1, "TA_24m": df.TA_1_2_1, "TA_16m": df.TA_1_3_1,
                          "TA_8.75m": df.TA_1_4_1, "T_SONIC": df.T_SONIC, "consensus_ref_C": tc["ref"], "TA_ERA_C": df.TA_ERA,
                          "candidate_TA_C": tc["val"], "method": tc["how"]}).loc[tc["fault"] | tc["clip"]].reset_index(drop=True)
    return dict(tc=tc, tval=tval, trows=trows, hy=hy, hv=hv, hrows=hrows)


def show(res):
    pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30)
    tr = res["trows"]
    print("\n=== TEMPERATURE targets ===")
    print(tr.groupby(["class", "method"]).size().rename("HH").reset_index().to_string(index=False) if len(tr) else "none")
    print(tr.groupby(["class", "year"]).size().unstack(fill_value=0).to_string() if len(tr) else "")
    f = tr.loc[tr["class"].eq("FAULT_31M")]
    if len(f): print(f.drop(columns=["year"]).head(40).round(2).to_string(index=False))
    print("\n=== TEMPERATURE validation (synthetic 31 m gaps; predeclared gate) ===")
    print(res["tval"].to_string(index=False))
    print("\n=== HUMIDITY level transfer validation (FLUXMET QC0 truth) ===")
    print(res["hv"].to_string(index=False))
    print(res["hy"][["level", "year", "N", "MAE_hPa", "bias_hPa", "frac_abs_err_gt2hPa", "gate_pass"]].to_string(index=False))
    h = res["hrows"]
    print("\n=== HUMIDITY fill of Stage12g gaps + FAULT_31M rows ===")
    print(h.groupby("source").size().rename("HH").reset_index().to_string(index=False))
    print(h.groupby(["year", "source"]).size().unstack(fill_value=0).to_string())


def self_test():
    n = 48 * 365 * 2
    ts = pd.date_range("2022-01-01", periods=n, freq="30min"); n = len(ts)
    rng = np.random.default_rng(4)
    t16 = 5 + 8 * np.sin(np.arange(n) / 48 * 2 * np.pi) + rng.normal(0, .3, n)
    t31 = t16 - 0.5 + rng.normal(0, .2, n); t31[1000:1022] = -39.3; t31[2000:2002] = -12.5
    Te = t16 + 6; rh = rng.uniform(40, 90, n); e = rh / 100 * M.esw(t16)
    flux = pd.DataFrame({"TIMESTAMP_START": ts.strftime("%Y%m%d%H%M"), "TA_F": t31, "TA_F_QC": 0,
                         "VPD_F": np.clip(M.esw(t31) - e, 0.01, None), "VPD_F_QC": 0, "PA_F": 74.5})
    era = pd.DataFrame({"TIMESTAMP_START": flux.TIMESTAMP_START, "TA_ERA": Te, "VPD_ERA": M.esw(Te) - e, "PA_ERA": 84.5})
    df = M.frame_from(flux, era)
    base = pd.DataFrame({"TIMESTAMP_START": flux.TIMESTAMP_START, "TA_1_1_1": t31, "TA_1_2_1": t16 + 0.1, "TA_1_3_1": t16,
                         "TA_1_4_1": t16 - 0.1, "TA_1_5_1": t16, "RH_1_1_1": np.nan, "RH_1_2_1": rh, "RH_1_3_1": rh, "T_SONIC": t31})
    base.loc[1000:1021, "TA_1_2_1"] = -39.3
    df, agree = attach_base(df, base)
    gap = np.zeros(n, bool); gap[5000:5040] = True
    res = compute(df, gap)
    tc = res["tc"]
    assert tc["fault"][1000:1022].all() and tc["fault"][2000:2002].all() and int(tc["fault"].sum()) == 24, int(tc["fault"].sum())
    # warm 31 m with 24 m missing (possible inversion) must NOT be a fault; with 24 m disagreeing it is
    d2 = df.copy(); d2.loc[3000:3003, "TA_F"] = d2.TA_1_3_1[3000:3004] + 6; d2.loc[3000:3003, "TA_1_2_1"] = np.nan
    d2.loc[4000:4001, "TA_F"] = d2.TA_1_3_1[4000:4002] + 6
    f2, _ = t_targets(d2, *consensus(d2))
    assert not f2[3000:3004].any() and f2[4000:4002].all(), "warm-side inversion rule"

    assert np.nanmax(np.abs(tc["val"][1000:1022] - (t16[1000:1022] - 0.5))) < 1.0
    assert set(res["hrows"].source) <= {"L24_measured_RH_transfer", "L16_measured_RH_transfer", "COMPANION_E_user_option_B",
                                       "HOLD_OUT_OF_REGIME", "HOLD_NOT_FORMABLE", "HOLD_NO_TEMPERATURE"}
    assert len(res["hrows"]) == 40 + 24 and len(res["tval"]) == 3
    print("MtB03 SELF-TEST PASS: consensus fault/clip, 16 m level transfer + offsets, synthetic T validation, RH level transfer, fill order")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--base", default=str(BASE_DEFAULT)); ap.add_argument("--stage12g", default=str(M.STAGE12G_DEFAULT))
    a = ap.parse_args()
    print("MtB03 US-MtB MULTI-LEVEL BASE FILL CANDIDATES | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    df, gap, reasons, land, era5l, info = M.load_inputs(a.stage12g)
    df, agree = attach_base(df, read_base(a.base))
    info.update(base=str(a.base), base_sha256=BASE_SHA, base_TA_matches_FLUXMET_QC0=agree)
    res = compute(df, gap)
    print("\n=== INPUTS ===\n" + json.dumps(info, indent=1, default=str))
    show(res)
    hv, tv = res["hv"], res["tval"]
    print("\nMtB03 SUMMARY: T targets", len(res["trows"]), "| T gate", "PASS" if tv.gate_pass.all() else "FAIL(" + ",".join(str(x) for x in tv.loc[~tv.gate_pass, "length_HH"]) + "HH)",
          "| RH levels passing:", ",".join(hv.loc[hv.LEVEL_PASS, "level_m"] + "m") or "NONE",
          "| humidity HOLD:", int(res["hrows"].source.str.startswith("HOLD").sum()), "| forcing writes 0", flush=True)
    if a.check: print("MtB03 CHECK ONLY: no files written.", flush=True); return
    out = M.ROOT / "reports" / ("mtb03_US-MtB_multilevel_fill_candidates_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"T_candidates.csv": res["trows"], "T_validation.csv": res["tval"], "H_level_yearly.csv": res["hy"],
             "H_level_verdict.csv": res["hv"], "H_fill_candidates.csv": res["hrows"]}
    for k, d in files.items(): d.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("MtB03 candidates only (user-approved fill order 2026-10-29). Not written to any forcing; "
                                           "building a research shadow from them is a separate approved step.\n")
    names = [*files, "SCIENTIFIC_HOLD.md"]
    rec = {"version": VERSION, "inputs": info, "MtB02_blob": P_BLOB, "T_gate": tv.to_dict("records"),
           "RH_levels_passing": hv.loc[hv.LEVEL_PASS, "level_m"].tolist(),
           "humidity_sources": res["hrows"].source.value_counts().to_dict(), "forcing_writes": 0,
           "Postv5_approved": 0, "DATM_ready": 0, "spinup_authorized": 0,
           "output_sha256": {n: M.sha(out / n) for n in names}}
    (out / "mtb03_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("MtB03 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("MtB03 STOP:", exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

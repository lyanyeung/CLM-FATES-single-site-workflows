#!/usr/bin/env python3
"""MtB02 (Claude workstream, US-MtB only): predeclared confirmation. READ ONLY.

All rules below were fixed BEFORE this script was run. They follow from MtB01 (--check
2026-10-28) and the user's criterion (28 Oct): a tower value is plausibly real only if the
same period of the record has comparable values AND it is not a constant reading.

Part T1  temperature fault screen over the whole release (no edits)
  FAULT_FLATLINE   >= 4 consecutive HH with TA_F max-min <= 0.1 C AND every |TA_F - TA_ERA| > 10 C
  REVIEW_NO_ANALOGUE  TA_F below (minimum TA_F of the same calendar month in all OTHER years,
                   excluding FAULT rows) - 5 C, and not FAULT. Reported with context, not excluded.
  Floor check: 0.1 C histogram of TA_F in [-10.5, -9.0) per year and QC, plus counts < -10 C.

Part T2  candidate replacement for FAULT rows (a candidate for the user, never written)
  ERA-shape bridge: TA_ERA(t) + offset(t), offset linearly interpolated between the mean
  (TA_F - TA_ERA) of valid tower QC0 anchors in the 4 HH before and the 4 HH after the run
  (>= 2 anchors each side; else 12 HH; else HOLD).
  Validation on synthetic gaps cut from valid QC0 tower runs of the same lengths as the faults
  (5 and 22 HH), 2000 each, seed 20261028. Gate per length: MAE <= 1.5 C, |bias| <= 0.5 C,
  fraction |error| > 3 C <= 0.10.

Part H   humidity confirmation in the gap regime (tower colder than the companion ERA)
  Truth = VPD_F_QC=0 & TA_F_QC=0 physical records, FAULT rows (and their VPD) removed.
  REGIME = truth with TA_F - TA_ERA <= -5 C (2812 of the 2840 gaps lie here).
  Primary COMPANION_E (companion vapour pressure kept, VPD at tower TA_F); runner-up EMP_ADJ_RH.
  Gates (Stage12j thresholds): N >= 50, valid fraction >= 0.60, VPD MAE <= 1.5 hPa,
  |bias| <= 0.7 hPa, fraction |error| > 2 hPa <= 0.10.
  METHOD_PASS = pooled REGIME passes AND every year with N >= 50 passes AND >= 5 such years.
  Also reported: cold subset (T <= 5 C), season, 3-h block, QC0 bad-error runs.
  Coverage of every gap: candidate-if-approved vs HOLD (out of regime / not formable), with
  FAULT rows treated as humidity gaps at their bridged temperature.

--self-test synthetic only. --check full computation, prints, NO writes. --run writes ONE new
reports/mtb02_* folder with CSVs and an SHA receipt. Nothing edits source, earlier stages,
the 233 holds, clocks, Post-v5, DATM, CIME or Slurm. Every adoption is the user's decision.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-MtB02-v1-20261028-T-fault-bridge-and-regime-humidity-READONLY"
HERE = Path(__file__).resolve().parent
M_SCRIPT = HERE / "MtB01_regime_matched_QC0_humidity_census_READONLY.py"
M_BLOB = "3bcead9445dca3ec3485f390d51264492f40cdf0"
FLAT_MIN_HH, FLAT_RANGE_C, FLAT_ABS_DT_C = 4, 0.1, 10.0
ANALOGUE_MARGIN_C = 5.0
ANCHOR_HH, ANCHOR_WIDE_HH, ANCHOR_MIN = 4, 12, 2
SYN_LENGTHS, SYN_N, SEED = (5, 22), 2000, 20261028
T_GATE = dict(MAE=1.5, BIAS=0.5, BAD3=0.10)
REGIME_DT = -5.0
H_METHODS = ("COMPANION_E", "EMP_ADJ_RH")
MIN_YEARS = 5
WINDOW_HH = 4


def load_mtb01():
    b = M_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != M_BLOB:
        raise ValueError("Pinned MtB01 Git blob mismatch: " + str(M_SCRIPT))
    spec = importlib.util.spec_from_file_location("mtb01_for_mtb02", M_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


M = load_mtb01()


# ----------------------------------------------------------------- T1 fault screen
def flat_faults(df):
    T, dT = df.TA_F.to_numpy(), df.dT.to_numpy()
    n = len(T); fault = np.zeros(n, bool); i = 0
    while i < n:
        if not np.isfinite(T[i]) or not (abs(dT[i]) > FLAT_ABS_DT_C if np.isfinite(dT[i]) else False):
            i += 1; continue
        j = i; lo = hi = T[i]
        while j + 1 < n and np.isfinite(T[j + 1]) and np.isfinite(dT[j + 1]) and abs(dT[j + 1]) > FLAT_ABS_DT_C \
                and max(hi, T[j + 1]) - min(lo, T[j + 1]) <= FLAT_RANGE_C:
            j += 1; lo = min(lo, T[j]); hi = max(hi, T[j])
        if j - i + 1 >= FLAT_MIN_HH: fault[i:j + 1] = True
        i = j + 1
    return fault


def no_analogue(df, fault):
    ok = (df.TA_F_QC == 0).to_numpy() & ~fault & np.isfinite(df.TA_F.to_numpy())
    mins = df.loc[ok].groupby(["month", "year"]).TA_F.min().unstack()      # month x year
    flag = np.zeros(len(df), bool); ref = np.full(len(df), np.nan)
    for (mo, yr), idx in df.groupby(["month", "year"]).groups.items():
        others = mins.loc[mo].drop(labels=[yr], errors="ignore").dropna() if mo in mins.index else pd.Series(dtype=float)
        if len(others) == 0: continue
        r = float(others.min()); ix = np.asarray(idx)
        ref[ix] = r
        flag[ix] = (df.TA_F.to_numpy()[ix] < r - ANALOGUE_MARGIN_C) & ~fault[ix]
    return flag, ref


def run_table(df, mask, label, ref=None, bridge=None):
    rows = []
    for st, ln in M.runs(mask):
        s = df.iloc[st:st + ln]
        r = {"class": label, "start": s.native_key.iloc[0], "end": s.native_key.iloc[-1], "length_HH": ln,
             "TA_F_min": float(s.TA_F.min()), "TA_F_max": float(s.TA_F.max()),
             "TA_F_range": float(s.TA_F.max() - s.TA_F.min()), "TA_ERA_mean": float(s.TA_ERA.mean()),
             "TA_F_QC": ",".join(sorted({str(int(x)) for x in s.TA_F_QC.dropna()})),
             "VPD_F_QC": ",".join(sorted({str(int(x)) for x in s.VPD_F_QC.dropna()})), "start_row": st}
        if ref is not None: r["other_year_same_month_min_C"] = float(np.nanmin(ref[st:st + ln]))
        if bridge is not None: r["bridge_mean_C"] = float(np.nanmean(bridge[st:st + ln]))
        rows.append(r)
    return pd.DataFrame(rows)


def floor_check(df):
    T = df.TA_F.to_numpy()
    edges = np.round(np.arange(-10.5, -8.95, 0.1), 2)
    rows = []
    for y, g in df.groupby("year"):
        t = g.TA_F.to_numpy(); q = g.TA_F_QC.to_numpy()
        r = {"year": int(y), "N_lt_-10": int((t < -10).sum()), "N_lt_-10_QC0": int(((t < -10) & (q == 0)).sum())}
        h, _ = np.histogram(t[np.isfinite(t)], bins=edges)
        for a, c in zip(edges[:-1], h): r[f"[{a:.1f},{a + .1:.1f})"] = int(c)
        rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------- T2 bridge
def anchors_offset(T, Te, valid, i0, i1, width):
    b = [k for k in range(max(0, i0 - width), i0) if valid[k]]
    a = [k for k in range(i1 + 1, min(len(T), i1 + 1 + width)) if valid[k]]
    if len(b) < ANCHOR_MIN or len(a) < ANCHOR_MIN: return None
    return float(np.mean(T[b] - Te[b])), float(np.mean(T[a] - Te[a]))


def bridge_run(T, Te, valid, i0, i1):
    off = anchors_offset(T, Te, valid, i0, i1, ANCHOR_HH) or anchors_offset(T, Te, valid, i0, i1, ANCHOR_WIDE_HH)
    if off is None: return None
    L = i1 - i0 + 1; frac = (np.arange(L) + 1) / (L + 1)
    return Te[i0:i1 + 1] + off[0] + (off[1] - off[0]) * frac


def bridge_faults(df, fault):
    T, Te = df.TA_F.to_numpy(), df.TA_ERA.to_numpy()
    valid = (df.TA_F_QC == 0).to_numpy() & ~fault & np.isfinite(T) & np.isfinite(Te)
    out = np.full(len(df), np.nan); held = []
    for st, ln in M.runs(fault):
        v = bridge_run(T, Te, valid, st, st + ln - 1)
        if v is None: held.append(df.native_key.iloc[st])
        else: out[st:st + ln] = v
    return out, held


def bridge_validation(df, fault):
    T, Te = df.TA_F.to_numpy(), df.TA_ERA.to_numpy()
    valid = (df.TA_F_QC == 0).to_numpy() & ~fault & np.isfinite(T) & np.isfinite(Te)
    rng = np.random.default_rng(SEED); res = []; per = []
    for L in SYN_LENGTHS:
        ok = np.convolve(valid.astype(int), np.ones(L, int), "valid") == L      # start s: valid[s:s+L]
        starts = np.flatnonzero(ok)
        starts = starts[(starts >= ANCHOR_WIDE_HH) & (starts + L + ANCHOR_WIDE_HH < len(T))]
        rng.shuffle(starts); errs = []; used = 0
        for s in starts:
            if used >= SYN_N: break
            v2 = valid.copy(); v2[s:s + L] = False
            b = bridge_run(T, Te, v2, s, s + L - 1)
            if b is None: continue
            e = b - T[s:s + L]; errs.append(e); used += 1
            per.append({"length_HH": L, "start": df.native_key.iloc[s], "month": int(df.month.iloc[s]),
                        "MAE_C": float(np.mean(np.abs(e))), "bias_C": float(np.mean(e))})
        e = np.concatenate(errs) if errs else np.array([np.nan])
        r = {"length_HH": L, "synthetic_gaps": used, "MAE_C": float(np.nanmean(np.abs(e))), "bias_C": float(np.nanmean(e)),
             "P95_abs_C": float(np.nanpercentile(np.abs(e), 95)), "frac_abs_gt3C": float(np.nanmean(np.abs(e) > 3))}
        r["gate_pass"] = bool(used >= 100 and r["MAE_C"] <= T_GATE["MAE"] and abs(r["bias_C"]) <= T_GATE["BIAS"]
                              and r["frac_abs_gt3C"] <= T_GATE["BAD3"])
        res.append(r)
    return pd.DataFrame(res), pd.DataFrame(per)


# ----------------------------------------------------------------- H humidity
def season(m): return np.select([np.isin(m, [12, 1, 2]), np.isin(m, [3, 4, 5]), np.isin(m, [6, 7, 8])], ["DJF", "MAM", "JJA"], "SON")


def humidity(df, fault):
    d = df.copy()
    d.loc[fault, "truth"] = False; d.loc[fault, "RH_obs"] = np.nan
    e, meta = M.candidates(d)
    T, P = d.TA_F.to_numpy(), d.P_Pa.to_numpy()
    truth = d.truth.to_numpy(); reg = truth & (d.dT.to_numpy() <= REGIME_DT)
    yearly, verdict, tails = [], [], []
    for m in H_METHODS:
        ok = M.physical(T, P, e[m]); err = np.where(ok, M.esw(T) - e[m], np.nan) - d.VPD_F.to_numpy()
        passes = []
        for y in sorted(d.year.unique()):
            s = reg & (d.year.to_numpy() == y)
            r = M.metrics(err[s], s.sum()); r.update(method=m, year=int(y))
            r["gate_pass"] = M.gate(r) if r["N"] >= 50 else None
            yearly.append(r)
            if r["gate_pass"] is not None: passes.append(r["gate_pass"])
        pooled = M.metrics(err[reg], reg.sum()); cold = M.metrics(err[reg & (T <= 5)], (reg & (T <= 5)).sum())
        rr = M.runs(reg & np.isfinite(err) & (np.abs(err) > 2))
        verdict.append({"method": m, "REGIME_N": pooled["N"], "REGIME_valid_fraction": pooled["valid_fraction"],
                        "REGIME_MAE_hPa": pooled["MAE_hPa"], "REGIME_bias_hPa": pooled["bias_hPa"],
                        "REGIME_frac_gt2hPa": pooled["frac_abs_err_gt2hPa"], "REGIME_pass": bool(M.gate(pooled)),
                        "COLD_REGIME_MAE_hPa": cold["MAE_hPa"], "COLD_REGIME_frac_gt2hPa": cold["frac_abs_err_gt2hPa"],
                        "gated_years": len(passes), "gated_years_pass": int(sum(passes)),
                        "bad_runs": len(rr), "longest_bad_run_HH": max([x[1] for x in rr], default=0),
                        "METHOD_PASS": bool(M.gate(pooled) and passes and all(passes) and len(passes) >= MIN_YEARS)})
        for lab, key in (("season", season(d.month.to_numpy())), ("hblock", d.hblock.to_numpy()), ("dT_bin", d.dT_bin.to_numpy())):
            for k in pd.unique(key[reg]):
                s = reg & (key == k); t = M.metrics(err[s], s.sum()); t.update(method=m, by=lab, bin=str(k)); tails.append(t)
    return e, pd.DataFrame(yearly), pd.DataFrame(verdict), pd.DataFrame(tails)


def coverage(df, gap, fault, bridge, e):
    T = np.where(fault & np.isfinite(bridge), bridge, df.TA_F.to_numpy())
    P = df.P_Pa.to_numpy(); Te = df.TA_ERA.to_numpy()
    with np.errstate(invalid="ignore"):
        e_era = M.esw(Te) - df.VPD_ERA.to_numpy()
    rh_ok = np.isfinite(e_era) & (e_era > 0) & (e_era <= M.esw(Te))
    eC = np.where(rh_ok, e_era, np.nan)                      # COMPANION_E at the (bridged) tower T
    target = gap | fault
    dT = T - Te; inreg = dT <= REGIME_DT
    form = M.physical(T, P, eC)
    cls = np.where(~target, "", np.where(fault & ~np.isfinite(bridge), "HOLD_FAULT_T_NO_BRIDGE",
                   np.where(~inreg, "HOLD_OUT_OF_REGIME", np.where(~form, "HOLD_NOT_FORMABLE", "CANDIDATE_IF_APPROVED"))))
    g = pd.DataFrame({"native_key": df.native_key, "year": df.year, "in_Stage12g_gap": gap, "T_fault": fault,
                      "TA_used_C": T, "dT_used": dT, "class": cls,
                      "COMPANION_E_VPD_hPa": np.where(cls == "CANDIDATE_IF_APPROVED", M.esw(T) - eC, np.nan),
                      "COMPANION_E_QBOT_kgkg": np.where(cls == "CANDIDATE_IF_APPROVED", M.q_from_e(eC, P), np.nan),
                      "COMPANION_E_RH_ice_pct": np.where((cls == "CANDIDATE_IF_APPROVED") & (T < 0), 100 * eC / M.esi(T), np.nan)})
    g = g.loc[target].reset_index(drop=True)
    tab = g.groupby(["class"]).size().rename("N").reset_index()
    tab_y = g.groupby(["year", "class"]).size().unstack(fill_value=0).reset_index()
    return g, tab, tab_y


def context(df, fault, review, bridge):
    rows = []
    for lab, mask in (("FAULT", fault), ("REVIEW_NO_ANALOGUE", review)):
        for st, ln in M.runs(mask)[:12]:
            for i in range(max(0, st - WINDOW_HH), min(len(df), st + ln + WINDOW_HH)):
                r = df.iloc[i]
                rows.append({"run_class": lab, "run_start": df.native_key.iloc[st], "native_key": r.native_key,
                             "in_run": bool(mask[i]), "TA_F_C": r.TA_F, "TA_F_QC": r.TA_F_QC, "TA_ERA_C": r.TA_ERA,
                             "bridge_candidate_C": bridge[i], "VPD_F_hPa": r.VPD_F, "VPD_F_QC": r.VPD_F_QC,
                             "VPD_ERA_hPa": r.VPD_ERA, "SW_IN_F": r.SW_IN_F, "LW_IN_F": r.LW_IN_F, "WS_F": r.WS_F})
    return pd.DataFrame(rows)


def compute(df, gap):
    fault = flat_faults(df)
    review, ref = no_analogue(df, fault)
    bridge, held = bridge_faults(df, fault)
    bval, bper = bridge_validation(df, fault)
    e, hy, hv, ht = humidity(df, fault)
    cov, ctab, cy = coverage(df, gap, fault, bridge, e)
    return dict(fault=fault, review=review, bridge=bridge, bridge_held=held,
                fault_runs=run_table(df, fault, "FAULT_FLATLINE", ref, bridge),
                review_runs=run_table(df, review, "REVIEW_NO_ANALOGUE", ref),
                floor=floor_check(df), bridge_validation=bval, bridge_synthetic=bper,
                h_yearly=hy, h_verdict=hv, h_tails=ht, coverage=cov, coverage_tab=ctab, coverage_year=cy,
                context=context(df, fault, review, bridge))


def show(res, gap):
    pd.set_option("display.width", 230); pd.set_option("display.max_columns", 40)
    print(f"\n=== T1 FAULT_FLATLINE rows: {int(res['fault'].sum())} ===")
    print(res["fault_runs"].drop(columns="start_row").to_string(index=False) if len(res["fault_runs"]) else "none")
    print(f"\n=== T1 REVIEW_NO_ANALOGUE rows: {int(res['review'].sum())} (reported, not excluded) ===")
    rr = res["review_runs"]
    print(rr.drop(columns="start_row").head(20).to_string(index=False) if len(rr) else "none")
    print("\n=== T1 floor check: TA_F 0.1 C bins near -10 C ===")
    print(res["floor"].to_string(index=False))
    print("\n=== T2 bridge validation (synthetic gaps; predeclared gate) ===")
    print(res["bridge_validation"].to_string(index=False))
    print("bridge HOLD runs (no anchors):", res["bridge_held"] or "none")
    print("\n=== H humidity in gap regime (TA_F - TA_ERA <= -5 C), FAULT rows removed from truth ===")
    print(res["h_verdict"].to_string(index=False))
    y = res["h_yearly"]
    print(y[["method", "year", "N", "valid_fraction", "MAE_hPa", "bias_hPa", "frac_abs_err_gt2hPa", "gate_pass"]].to_string(index=False))
    t = res["h_tails"]
    print(t.loc[t.by.eq("season"), ["method", "bin", "N", "MAE_hPa", "bias_hPa", "frac_abs_err_gt2hPa"]].to_string(index=False))
    print(f"\n=== coverage of {int(gap.sum())} Stage12g gaps + FAULT rows (COMPANION_E) ===")
    print(res["coverage_tab"].to_string(index=False))
    print(res["coverage_year"].to_string(index=False))


def self_test():
    n = 48 * 365 * 3
    ts = pd.date_range("2020-01-01", periods=n, freq="30min"); ts = ts[~((ts.month == 2) & (ts.day == 29))]; n = len(ts)
    rng = np.random.default_rng(2)
    Te = 5 + 8 * np.sin(np.arange(n) / 48 * 2 * np.pi); T = Te - 3 + rng.normal(0, .5, n)
    T[5000:5022] = -39.3; T[9000:9005] = -39.27
    T[20000:20010] = T[20000:20010] - 30                      # varying extreme -> review, not fault
    rh = rng.uniform(.3, .9, n); ea = M.esw(Te) * rh
    flux = pd.DataFrame({"TIMESTAMP_START": ts.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0,
                         "VPD_F": np.clip(M.esw(T) - ea, 0.01, None), "VPD_F_QC": 0, "PA_F": 74.5})
    era = pd.DataFrame({"TIMESTAMP_START": flux.TIMESTAMP_START, "TA_ERA": Te, "VPD_ERA": M.esw(Te) - ea, "PA_ERA": 84.5})
    df = M.frame_from(flux, era)
    f = flat_faults(df)
    assert f[5000:5022].all() and f[9000:9005].all() and int(f.sum()) == 27, int(f.sum())
    rv, _ = no_analogue(df, f)
    assert not rv[5000:5022].any() and rv[20000:20010].any()
    b, held = bridge_faults(df, f)
    assert not held and np.nanmax(np.abs(b[5000:5022] - (Te[5000:5022] - 3))) < 1.0
    gap = np.zeros(n, bool); gap[30000:30010] = True
    res = compute(df, gap)
    assert set(res["h_verdict"].method) == set(H_METHODS) and len(res["bridge_validation"]) == 2
    assert res["coverage"].T_fault.sum() == 27
    print("MtB02 SELF-TEST PASS: flatline faults, no-analogue review, ERA-shape bridge, synthetic validation, regime humidity, coverage")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--stage12g", default=str(M.STAGE12G_DEFAULT))
    a = ap.parse_args()
    print("MtB02 US-MtB T FAULT / BRIDGE / REGIME HUMIDITY CONFIRMATION | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    df, gap, reasons, land, era5l, info = M.load_inputs(a.stage12g)
    res = compute(df, gap)
    show(res, gap)
    hv = res["h_verdict"]; bv = res["bridge_validation"]
    print("\nMtB02 SUMMARY: FAULT rows", int(res["fault"].sum()), "| bridge gate",
          "PASS" if bv.gate_pass.all() else "FAIL", "| humidity METHOD_PASS:",
          ",".join(hv.loc[hv.METHOD_PASS, "method"]) or "NONE", "| repairs written 0 | Post-v5 0 | DATM 0 | spinup 0", flush=True)
    if a.check: print("MtB02 CHECK ONLY: no files written.", flush=True); return
    out = M.ROOT / "reports" / ("mtb02_US-MtB_T_fault_bridge_regime_humidity_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"T1_fault_runs.csv": res["fault_runs"], "T1_review_no_analogue_runs.csv": res["review_runs"],
             "T1_floor_check.csv": res["floor"], "T2_bridge_validation.csv": res["bridge_validation"],
             "T2_bridge_synthetic_gaps.csv": res["bridge_synthetic"], "H_yearly.csv": res["h_yearly"],
             "H_verdict.csv": res["h_verdict"], "H_tails.csv": res["h_tails"], "C_gap_coverage_rows.csv": res["coverage"],
             "C_coverage_summary.csv": res["coverage_tab"], "C_coverage_by_year.csv": res["coverage_year"],
             "X_context_pm2h.csv": res["context"]}
    for k, d in files.items(): d.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("MtB02 is read-only. FAULT/bridge/humidity values are candidates for the user's decision; "
                                           "nothing is written to forcing. Rules were predeclared in the script header.\n")
    names = [*files, "SCIENTIFIC_HOLD.md"]
    rec = {"version": VERSION, "inputs": info, "MtB01_blob": M_BLOB, "fault_rows": int(res["fault"].sum()),
           "bridge_gate_pass": bool(bv.gate_pass.all()), "humidity_methods_passing": hv.loc[hv.METHOD_PASS, "method"].tolist(),
           "repairs_written": 0, "Postv5_approved": 0, "DATM_ready": 0, "spinup_authorized": 0,
           "output_sha256": {n: M.sha(out / n) for n in names}}
    (out / "mtb02_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("MtB02 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("MtB02 STOP:", exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

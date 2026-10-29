#!/usr/bin/env python3
"""CL07 (Claude, US-Me2 only): site-calibrated ERA vapour pressure for the 243 CL05/CL06 HOLD rows. READ ONLY.

User decision 2026-10-29 07:14: calibrate ERA against the tower's own normal (measured) periods and use it; if the
error is ~2 hPa, still use it (labelled low confidence), as for US-NR1 / US-Me6.

Imports CL06 (pinned blob 8f3a3a0c...) -> CL05 -> CL04 (all pinned); re-runs CL05 (must give 243 HOLD / 122 EMP).
Rules fixed before the run:
  predictor  e_ERA = esw(TA_ERA) - VPD_ERA (> 0 only); dT = TA_F - TA_ERA (tower minus ERA temperature)
  models     M1: e_tower = a + b e_ERA            M2: e_tower = a + b e_ERA + c dT
             fitted by least squares on dual-QC0 rows separately for every (month, 3-h block), each prediction from
             a fit that EXCLUDES the predicted row's whole year (leave-one-year-out); e capped at DATM sat at TA_F.
  validate   LOYO errors on dual-QC0 in the hierarchy (month, TA_F bin) -> (season, bin) -> (bin), N_valid >= 100,
             Stage12j gates; per year; compared with the uncalibrated CEC.
  choose     per HOLD row the model with the lower stratum MAE (finer level first). Label ERA_E_CAL_M1/M2 if the
             stratum passes, else ERA_E_CAL_M1/M2_LOW_CONFIDENCE (user rule). If the calibrated e is not > 0 or e_ERA is
             not formable: EMP_LOYO_LOW_CONFIDENCE; else HOLD. Temperature is never changed. Nothing is approved.
--self-test; --check prints; --run also writes ONE reports/cl07_US-Me2_ERA_E_calibrated_* folder.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-CL07-v1-20261029-Me2-site-calibrated-ERA-e-READONLY"
HERE = Path(__file__).resolve().parent
C6_SCRIPT = HERE / "CL06.py" if (HERE / "CL06.py").is_file() else HERE / "CL06_Me2_HOLD_companion_e_and_long_interp_READONLY.py"
C6_BLOB = "8f3a3a0cb07ba644f78e9e2ccbef7c37aeb3a955"


def load_c6():
    b = C6_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != C6_BLOB:
        raise ValueError("Pinned CL06 Git blob mismatch: " + str(C6_SCRIPT))
    spec = importlib.util.spec_from_file_location("cl06_for_cl07", C6_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


C6 = load_c6()
C5, C4 = C6.C5, C6.C4
esw, esi, datm, tbin, stats, gate = C4.esw, C4.esi, C4.datm, C4.tbin, C4.stats, C4.gate


def loyo_fit_predict(X, y, fit_mask, group, year):
    """least squares per group, leave-one-year-out; returns prediction for every row with finite X."""
    k = X.shape[1]; pred = np.full(len(y), np.nan)
    ok = np.isfinite(X).all(1)
    fm = fit_mask & ok & np.isfinite(y)
    for g in np.unique(group[ok]):
        gi = ok & (group == g); fi = fm & (group == g)
        if fi.sum() < 50: continue
        Xf, yf, yr = X[fi], y[fi], year[fi]
        XtX = Xf.T @ Xf; Xty = Xf.T @ yf
        for yy in np.unique(year[gi]):
            s = yr == yy
            A = XtX - Xf[s].T @ Xf[s]; bvec = Xty - Xf[s].T @ yf[s]
            if fi.sum() - s.sum() < 50 or np.linalg.cond(A) > 1e10: continue
            beta = np.linalg.solve(A, bvec); r = gi & (year == yy)
            pred[r] = X[r] @ beta
    return pred


def analyse(f, D5):
    T, V, et, nonphys, dry, qc, truth, target = C5.scan(f)
    with np.errstate(invalid="ignore"):
        eE = esw(f.TA_ERA.to_numpy(float)) - f.VPD_ERA.to_numpy(float)
    eE = np.where(eE > 0, eE, np.nan); dT = T - f.TA_ERA.to_numpy(float)
    group = (f.month.to_numpy() * 10 + f.hblock.to_numpy()).astype(int); year = f.year.to_numpy()
    preds = {}
    for nm, X in (("M1", np.column_stack([np.ones(len(f)), eE])), ("M2", np.column_stack([np.ones(len(f)), eE, dT]))):
        p = loyo_fit_predict(X, et, truth, group, year)
        preds[nm] = np.where(np.isfinite(p) & (p > 0), np.minimum(p, datm(T)), np.nan); preds[nm + "_raw"] = p
    cec = np.where(np.isfinite(eE), np.minimum(eE, datm(T)), np.nan)
    ST = {m: C6.strata_table(f, T, et, truth, preds[m]) for m in ("M1", "M2")}; ST["CEC"] = C6.strata_table(f, T, et, truth, cec)
    # summary validation
    summ = []
    warm = truth & (T > 5) & f.month.isin([6, 7, 8, 9, 10]).to_numpy()
    morning = warm & np.isin(f.hour.to_numpy(), [4, 5, 6, 7, 8, 9, 10, 11])
    for m, est in (("M1", preds["M1"]), ("M2", preds["M2"]), ("CEC", cec)):
        for nm, s in (("POOLED", truth), ("WARM_JunOct_TA_gt5", warm), ("WARM_MORNING_04_12h", morning)):
            r = stats((est - et)[s], et[s]); r.update(method=m, stratum=nm); r["gate"] = gate(r) if r.get("N_valid") else False; summ.append(r)
    S = pd.DataFrame(summ)
    yrs = []
    for m in ("M1", "M2"):
        for y in sorted(np.unique(year)):
            s = morning & (year == y)
            if s.sum() >= 50: r = stats((preds[m] - et)[s], et[s]); yrs.append(dict(method=m, year=int(y), N=r["N_valid"], MAE=r.get("MAE_hPa"), bias=r.get("bias_hPa"), gate=gate(r) if r.get("N_valid") else False))
    Y = pd.DataFrame(yrs)
    hold = D5.loc[D5.decision == "HOLD"]; pos = {k: i for i, k in enumerate(f.TIMESTAMP_START)}
    pool = f.loc[truth, ["month", "hblock"]].assign(Tb=tbin(T[truth]))
    emp = C4.emp_loyo(pool, et[truth] / esw(T[truth]), year[truth], f[["month", "hblock"]].assign(Tb=tbin(T)), year) * esw(T)
    rows = []
    for r in hold.to_dict("records"):
        i = pos[r["TIMESTAMP_START"]]; x = {k: r[k] for k in ("TIMESTAMP_START", "source_row", "year", "month", "TA_F", "VPD_F", "VPD_F_QC", "e_tower", "flag", "run_HH")}
        x.update(TA_ERA=f.TA_ERA.iloc[i], e_ERA=eE[i], dT=dT[i], CEC_e=cec[i], M1_e=preds["M1"][i], M2_e=preds["M2"][i], EMP_e=emp[i])
        opts = []
        for m in ("M1", "M2"):
            lvl, st = C5.pick(ST[m], i); x[m + "_level"] = lvl; x[m + "_MAE"] = st.get("MAE_hPa", np.nan); x[m + "_gate"] = bool(st and gate(st))
            if np.isfinite(preds[m][i]) and lvl: opts.append((C5.RANK[lvl], st["MAE_hPa"], m, x[m + "_gate"]))
        lvl, st = C5.pick(ST["CEC"], i); x["CEC_MAE"] = st.get("MAE_hPa", np.nan)
        if opts:
            _, mae, m, g = sorted(opts)[0]; e = preds[m][i]; dec = f"ERA_E_CAL_{m}" + ("" if g else "_LOW_CONFIDENCE"); why = f"{m} LOYO stratum MAE {mae:.3f} ({x[m + '_level']})"
        elif np.isfinite(emp[i]) and emp[i] > 0:
            e = min(emp[i], float(datm(T[i]))); dec = "EMP_LOYO_LOW_CONFIDENCE"; why = "no calibrated ERA; climatology"
        else:
            e, dec, why = np.nan, "HOLD", "nothing formable"
        x.update(decision=dec, rationale=why, e_proposed=e, VPD_proposed=esw(T[i]) - e if np.isfinite(e) else np.nan,
                 RH_proposed_pct=100 * e / esw(T[i]) if np.isfinite(e) else np.nan, APPROVED_FOR_NEW_VERSION=False)
        rows.append(x)
    return pd.DataFrame(rows), S, Y


def self_test():
    rng = np.random.default_rng(4); n = 48 * 365 * 3; t = pd.date_range("2006-01-01", periods=n, freq="30min")
    T = 8 + 10 * np.sin(2 * np.pi * (t.dayofyear - 110) / 365) + 5 * np.sin(2 * np.pi * t.hour / 24); e = np.clip(0.55 * esw(T) + rng.normal(0, .3, n), .1, None)
    TE = T + 2; eE = 1.3 * e + 0.5
    f = pd.DataFrame({"TIMESTAMP_START": t.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0, "VPD_F": esw(T) - e, "VPD_F_QC": 0, "grid_D": np.nan,
                      "TA_ERA": TE, "VPD_ERA": esw(TE) - eE, "row": np.arange(n) + 2})
    f["year"], f["month"], f["hour"] = t.year, t.month, t.hour; f["hblock"] = f.hour // 3
    f.loc[20000:20009, "VPD_F"] = esw(T[20000:20010]) + .5; f.loc[20000:20009, "VPD_F_QC"] = 1
    D5 = pd.DataFrame({"TIMESTAMP_START": f.TIMESTAMP_START[20000:20010], "source_row": 0, "year": 2007, "month": 2, "TA_F": T[20000:20010], "VPD_F": 0, "VPD_F_QC": 1,
                       "e_tower": 0, "flag": "NONPHYSICAL", "run_HH": 10, "decision": "HOLD"})
    D, S, Y = analyse(f, D5)
    m1 = S.set_index(["method", "stratum"]).loc[("M1", "POOLED"), "MAE_hPa"]; cec = S.set_index(["method", "stratum"]).loc[("CEC", "POOLED"), "MAE_hPa"]
    assert m1 < cec and D.decision.str.startswith("ERA_E_CAL").all() and (abs(D.e_proposed - e[20000:20010]) < 1.5).all(), (m1, cec, D.decision)
    print("CL07 SELF-TEST PASS: leave-one-year-out calibration beats raw ERA, decision labels", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--root", type=Path, default=C4.ROOT)
    a = ap.parse_args()
    print("CL07 US-Me2 SITE-CALIBRATED ERA VAPOUR PRESSURE | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    f, info, bcols = C4.load(a.root)
    D5, s5, I5 = C5.analyse(f)
    if int((D5.decision == "HOLD").sum()) != 243 or int((D5.decision == "EMP_LOYO").sum()) != 122: raise ValueError("CL05 result not reproduced (243 HOLD / 122 EMP)")
    D, S, Y = analyse(f, D5)
    pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    print("CL07_VALIDATION (leave-one-year-out, dual-QC0)\n" + S[["method", "stratum", "N", "N_valid", "MAE_hPa", "bias_hPa", "P95_abs_hPa", "median_rel", "share_gt2hPa", "gate"]].round(3).to_string(index=False))
    if len(Y): print("\n=== warm-morning LOYO error by year ===\n" + Y.round(3).to_string(index=False))
    print("\n=== decisions ===\n" + D.groupby(["year", "decision"]).size().rename("HH").reset_index().to_string(index=False))
    r = D.assign(dt=pd.to_datetime(D.TIMESTAMP_START, format="%Y%m%d%H%M")); r["run"] = r.dt.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    runs = r.groupby("run").agg(start=("TIMESTAMP_START", "first"), HH=("TIMESTAMP_START", "size"), TA=("TA_F", "mean"), dT=("dT", "mean"), old_VPD=("VPD_F", "mean"),
                                new_VPD=("VPD_proposed", "mean"), RH=("RH_proposed_pct", "mean"), M1_MAE=("M1_MAE", "first"), M2_MAE=("M2_MAE", "first"), CEC_MAE=("CEC_MAE", "first"),
                                decision=("decision", lambda x: ",".join(f"{k}:{v}" for k, v in x.value_counts().items())))
    print("\n=== runs ===\n" + runs.round(2).to_string(index=False))
    print(f"\nCL07 SUMMARY: {len(D)} former HOLD | " + " | ".join(f"{k}={v}" for k, v in D.decision.value_counts().items()) + " | approved 0", flush=True)
    for p, h in C4.READS.items():
        if C4.sha(p) != h: raise ValueError("input changed during audit: " + p)
    if a.check: print("CL07 CHECK ONLY: no files written.", flush=True); return
    out = a.root / "reports" / ("cl07_US-Me2_ERA_E_calibrated_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"Me2_243_calibrated_ERA_decisions.csv": D, "CL07_validation.csv": S, "CL07_warm_morning_by_year.csv": Y, "CL07_runs.csv": runs}
    for k, v in files.items(): v.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("Read-only candidate ledger. Nothing approved; no Me2 forcing was written.\n")
    rec = {"version": VERSION, "c6_blob": C6_BLOB, "inputs_sha256": C4.READS, "decisions": D.decision.value_counts().to_dict(), "approved": 0,
           "output_sha256": {n: C4.sha(out / n) for n in [*files, "SCIENTIFIC_HOLD.md"]}}
    (out / "cl07_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("CL07 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("CL07 STOP:", type(exc).__name__, exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

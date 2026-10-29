#!/usr/bin/env python3
"""CL02 (Claude, US-Me6 / US-NR1): side-by-side validated alternatives for every non-measured gap,
plus a source-coverage audit. READ ONLY. Rules fixed here before the first run.

Builds on CL01 (pinned) for the ledger, BASE sources and classes. For every gap HH:
  MEASURED      CL01 MEASURED_SUPPORTED (validated BASE level transfer) - kept as is
  CEC           COMPANION_E capped: companion vapour pressure, limited to the DATM saturation at the
                shadow TA_USE (CDEPS datm_eSat, Flatau; ice when T < 0 C)
  EMP           measured-only climatology: block-excluded mean RH_water of QC0 truth in the same
                (month, 3-h block, tower-T bin), then (month, T bin), then (T bin); >= 20 analogues;
                the 10-day block of the predicted time is excluded; e capped at DATM saturation
  SAT           DATM saturation at TA_USE
Validation on QC0 truth (VPD_F_QC = TA_F_QC = 0) for CEC, EMP and SAT: pooled, per year, and per
tower-T bin (<=-15, -15:-10, -10:-5, -5:0, 0:5, 5:15, >15 C), Stage12j thresholds.
Recommendation per HH (predeclared):
  1 MEASURED if CL01 measured;
  2 else among CEC / EMP, those that PASS the five thresholds in the row's T bin (bin N >= 100),
    the one with the lower bin MAE;
  3 else SAT_LOW_CONFIDENCE when the companion e is at or above saturation (reanalysis itself says
    saturated);
  4 else HOLD_NO_VALIDATED_METHOD (values of all alternatives still listed).
  Any row whose tower TA_F is ERA-filled (TA_F_QC = 2) is flagged T_IS_REANALYSIS.
Coverage audit: per year and month, the fraction of each FLUXMET *_F_QC met variable that is 0
(measured) and 2 (ERA), and whether any BASE TA/RH exists - to decide e.g. whether NR1 1998 is a
measured year at all.

--self-test synthetic; --check prints, NO writes; --run writes ONE reports/cl02_<site>_* folder.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-CL02-v1-20261029-Me6-NR1-alternatives-READONLY"
HERE = Path(__file__).resolve().parent
C_SCRIPT = HERE / "CL01.py" if (HERE / "CL01.py").is_file() else HERE / "CL01_Me6_NR1_gap_ledger_BASE_evidence_decision_matrix_READONLY.py"
C_BLOB = "b7c46cb9890bf0bc9077a1e913303c77312b10bb"
A = (6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04, 3.031240396e-06, 2.034080948e-08, 6.136820929e-11)
B = (6.109177956, 5.034698970e-01, 1.886013408e-02, 4.176223716e-04, 5.824720280e-06, 4.838803174e-08, 1.838826904e-10)
BIN_MIN = 100
QC_VARS = ("TA_F_QC", "VPD_F_QC", "SW_IN_F_QC", "LW_IN_F_QC", "PA_F_QC", "WS_F_QC", "P_F_QC")


def load_c():
    b = C_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != C_BLOB:
        raise ValueError("Pinned CL01 v2 Git blob mismatch: " + str(C_SCRIPT))
    spec = importlib.util.spec_from_file_location("cl01_for_cl02", C_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


C = load_c()
M = C.M


def esat_datm(t):
    t = np.asarray(t, float); tc = np.clip(t, -50, 50)
    p = lambda k: k[0] + tc * (k[1] + tc * (k[2] + tc * (k[3] + tc * (k[4] + tc * (k[5] + tc * k[6])))))
    return np.where(t < 0, p(B), p(A))


def alternatives(df):
    """e (hPa) of CEC, EMP, SAT at every row, using the shadow TA_USE where present."""
    T = np.where(np.isfinite(df.S_TA_USE.to_numpy(float)), df.S_TA_USE.to_numpy(float), df.TA_F.to_numpy(float))
    d = df.copy(); d["Tb"] = M.cut(T, M.T_EDGES, M.T_LABELS)
    sat = esat_datm(T)
    with np.errstate(invalid="ignore"):
        ec = M.esw(df.TA_ERA.to_numpy(float)) - df.VPD_ERA.to_numpy(float)
    cec = np.where(np.isfinite(ec) & (ec > 0), np.minimum(ec, sat), np.nan)
    rh, lev, n = M.block_excluded_mean(d, d.RH_obs.to_numpy(float), [("month", "hblock", "Tb"), ("month", "Tb"), ("Tb",)], np.ones(len(d), bool))
    emp = np.where(np.isfinite(rh), np.minimum(rh * M.esw(T), sat), np.nan)
    return dict(T=T, Tb=d.Tb.to_numpy(), CEC=cec, EMP=emp, SAT=sat, ec=ec, emp_level=lev, emp_n=n)


def validate(df, alt):
    T = df.TA_F.to_numpy(float); P = df.P_Pa.to_numpy(float); truth = df.truth.to_numpy()
    tb = M.cut(T, M.T_EDGES, M.T_LABELS); out, binrows = [], []
    for k in ("CEC", "EMP", "SAT"):
        e = alt[k]; ok = np.isfinite(e) & (e > 0); err = np.where(ok, M.esw(T) - e, np.nan) - df.VPD_F.to_numpy()
        has = truth & np.isfinite(err); passes = []
        for y in sorted(df.year.unique()):
            s = has & (df.year.to_numpy() == y)
            if s.sum() >= 50: passes.append(M.gate(M.metrics(err[s], s.sum())))
        p = M.metrics(err[has], has.sum())
        out.append({"method": k, "N": p["N"], "MAE_hPa": p["MAE_hPa"], "bias_hPa": p["bias_hPa"], "frac_gt2hPa": p["frac_abs_err_gt2hPa"],
                    "pooled_pass": bool(M.gate(p)), "years_pass": f"{sum(passes)}/{len(passes)}"})
        for b in M.T_LABELS:
            s = truth & (tb == b)
            r = M.metrics(err[s], s.sum()); r.update(method=k, T_bin=b); r["bin_pass"] = bool(r["N"] >= BIN_MIN and M.gate(r)); binrows.append(r)
    return pd.DataFrame(out), pd.DataFrame(binrows)


def decide(df, L, alt, bins):
    pos = {k: i for i, k in enumerate(df.native_key)}
    P = df.S_PSRF.to_numpy(float); rows = []
    bp = bins.set_index(["method", "T_bin"])
    for r in L.to_dict("records"):
        i = pos[r["native_key"]]; T = alt["T"][i]; tb = alt["Tb"][i]
        rec = {"native_key": r["native_key"], "year": r["year"], "episode": r["episode"], "CL01_class": r["class"], "TA_USE_C": T,
               "T_bin": tb, "T_IS_REANALYSIS": bool(r["TA_F_QC"] == 2)}
        for k in ("CEC", "EMP", "SAT"):
            e = alt[k][i]; rec[f"{k}_VPD_hPa"] = M.esw(T) - e if np.isfinite(e) else np.nan
            rec[f"{k}_RHice_pct"] = 100 * e / M.esi(T) if np.isfinite(e) and T < 0 else np.nan
            if k != "SAT":
                ok = (k, tb) in bp.index and bp.loc[(k, tb), "bin_pass"]
                rec[f"{k}_bin_pass"] = bool(ok); rec[f"{k}_bin_MAE"] = float(bp.loc[(k, tb), "MAE_hPa"]) if (k, tb) in bp.index else np.nan
        if r["class"] == "MEASURED_SUPPORTED":
            choice, e = "MEASURED:" + r["proposed_source"], r.get("e_" + r["proposed_source"], np.nan)
        else:
            cand = [k for k in ("EMP", "CEC") if rec[f"{k}_bin_pass"] and np.isfinite(alt[k][i])]
            if cand:
                k = min(cand, key=lambda k: rec[f"{k}_bin_MAE"]); choice, e = k, alt[k][i]
            elif np.isfinite(alt["ec"][i]) and alt["ec"][i] >= alt["SAT"][i]:
                choice, e = "SAT_LOW_CONFIDENCE", alt["SAT"][i]
            else:
                choice, e = "HOLD_NO_VALIDATED_METHOD", np.nan
        rec["recommended"] = choice
        rec["rec_VPD_hPa"] = M.esw(T) - e if np.isfinite(e) else np.nan
        rec["rec_QBOT_kgkg"] = float(M.q_from_e(e, P[i])) if np.isfinite(e) else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def coverage(site, df):
    stage10, spec = C.stage12g_sources(site)
    hdr = set(pd.read_csv(M.regular(spec["primary"]), nrows=0).columns)
    cols = ["TIMESTAMP_START"] + [c for c in QC_VARS if c in hdr]
    f = pd.read_csv(M.regular(spec["primary"]), usecols=cols, dtype={"TIMESTAMP_START": str}, low_memory=False)
    ts = pd.to_datetime(f.TIMESTAMP_START, format="%Y%m%d%H%M"); f["year"], f["month"] = ts.dt.year, ts.dt.month
    bta = [c for c in df.columns if c.startswith("B_TA")]; brh = [c for c in df.columns if c.startswith("B_RH")]
    b = pd.DataFrame({"native_key": df.native_key, "BASE_TA_any": df[bta].notna().any(axis=1) if bta else False,
                      "BASE_RH_any": df[brh].notna().any(axis=1) if brh else False})
    f = f.merge(b, left_on="TIMESTAMP_START", right_on="native_key", how="left")
    agg = {}
    for c in cols[1:]:
        v = pd.to_numeric(f[c], errors="coerce"); f[c + "_is0"] = v.eq(0); f[c + "_is2"] = v.eq(2)
        agg[c.replace("_F_QC", "") + "_QC0"] = (c + "_is0", "mean"); agg[c.replace("_F_QC", "") + "_QC2"] = (c + "_is2", "mean")
    agg["BASE_TA_any"] = ("BASE_TA_any", "mean"); agg["BASE_RH_any"] = ("BASE_RH_any", "mean")
    yr = f.groupby("year").agg(**agg).reset_index()
    y0 = int(f.year.min())
    mo = f.loc[f.year <= y0 + 1].groupby(["year", "month"]).agg(**agg).reset_index()
    return yr, mo


def ta_anomaly(df):
    """Every HH where tower or shadow T differs from the companion TA_ERA by > 30 C (e.g. NR1 2004 dT ~ 110)."""
    m = ((df.TA_F - df.TA_ERA).abs() > 30) | ((df.S_TA_USE - df.TA_ERA).abs() > 30)
    return df.loc[m, ["native_key", "year", "TA_F", "TA_F_QC", "S_TA_USE", "TA_ERA", "VPD_F", "VPD_F_QC", "VPD_ERA", "S_VPD_USE", "PA_F", "PA_ERA"]].reset_index(drop=True)


def compute(site, df, cols):
    res = C.compute(df, cols, C.SITES[site]["missing"])
    alt = alternatives(df)
    vs, vb = validate(df, alt)
    D = decide(df, res["ledger"], alt, vb)
    return res, vs, vb, D


def show(site, vs, vb, D, yr, mo, an):
    pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 300)
    print(f"\n=== {site} validation of alternatives (QC0 truth) ===\n" + vs.round(3).to_string(index=False))
    print(vb.pivot_table(index="T_bin", columns="method", values=["N", "MAE_hPa", "frac_abs_err_gt2hPa", "bin_pass"], aggfunc="first").reindex(list(M.T_LABELS)).to_string())
    print(f"\n=== {site} recommendation counts ===")
    print(D.groupby(["CL01_class", "recommended"]).size().rename("HH").reset_index().to_string(index=False))
    print("rows with reanalysis tower T:", int(D.T_IS_REANALYSIS.sum()))
    e = D.groupby("episode").agg(start=("native_key", "first"), HH=("native_key", "size"), T_min=("TA_USE_C", "min"), T_max=("TA_USE_C", "max"),
                                 recommended=("recommended", lambda s: ",".join(f"{k}:{v}" for k, v in s.value_counts().items())),
                                 rec_VPD_range=("rec_VPD_hPa", lambda s: f"{s.min():.2f}-{s.max():.2f}" if s.notna().any() else "-"),
                                 CEC_VPD=("CEC_VPD_hPa", lambda s: f"{s.min():.2f}-{s.max():.2f}" if s.notna().any() else "-"),
                                 EMP_VPD=("EMP_VPD_hPa", lambda s: f"{s.min():.2f}-{s.max():.2f}" if s.notna().any() else "-"),
                                 SAT_VPD=("SAT_VPD_hPa", lambda s: f"{s.min():.2f}-{s.max():.2f}")).reset_index()
    print(f"\n=== {site} per episode ===\n" + e.to_string(index=False))
    print(f"\n=== {site} source coverage by year (fraction) ===\n" + yr.round(3).to_string(index=False))
    print(f"\n=== {site} first two years by month ===\n" + mo.round(3).to_string(index=False))
    print(f"\n=== {site} |T - TA_ERA| > 30 C anomaly rows: {len(an)} ===")
    if len(an): print(an.groupby("year").size().rename("HH").to_string()); print(an.head(40).round(3).to_string(index=False))


def self_test():
    n = 48 * 365 * 3
    ts = pd.date_range("2014-01-01", periods=n, freq="30min"); ts = ts[~((ts.month == 2) & (ts.day == 29))]; n = len(ts)
    rng = np.random.default_rng(9)
    T = -5 + 12 * np.sin(np.arange(n) / 48 * 2 * np.pi) + rng.normal(0, 1, n); rh = np.clip(0.6 + 0.1 * rng.normal(size=n), .1, .95); e = rh * M.esw(T)
    flux = pd.DataFrame({"TIMESTAMP_START": ts.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0, "VPD_F": M.esw(T) - e, "VPD_F_QC": 0, "PA_F": 85.0})
    era = pd.DataFrame({"TIMESTAMP_START": flux.TIMESTAMP_START, "TA_ERA": T + 2, "VPD_ERA": M.esw(T + 2) - e, "PA_ERA": 85.0})
    df = M.frame_from(flux, era)
    for c, v in (("S_TA_USE", T), ("S_VPD_USE", M.esw(T) - e), ("S_QBOT", M.q_from_e(e, 85000.0)), ("S_PSRF", np.full(n, 85000.0))): df[c] = v
    df.loc[1000:1009, ["S_VPD_USE", "S_QBOT"]] = np.nan; df.loc[1000:1009, "truth"] = False
    C.SITES["TEST"] = dict(missing=10)
    res, vs, vb, D = compute("TEST", df, dict(ta=[], rh=[], h2o=[]))
    assert len(D) == 10 and set(vs.method) == {"CEC", "EMP", "SAT"}
    assert (D.SAT_VPD_hPa >= -1e-9).all() and D.recommended.isin(["EMP", "CEC", "SAT_LOW_CONFIDENCE", "HOLD_NO_VALIDATED_METHOD"]).all()
    assert abs(float(esat_datm(-8.39)) - 2.9929) < 2e-4 and len(ta_anomaly(df)) == 0
    del C.SITES["TEST"]
    print("CL02 SELF-TEST PASS: CEC/EMP/SAT alternatives, T-bin validation, predeclared recommendation")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--site", choices=sorted(C.SITES)); ap.add_argument("--base")
    a = ap.parse_args()
    print("CL02 ALTERNATIVES / VALIDATED DECISION TABLE | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    df, cols, info = C.frame(a.site, a.base or C.SITES[a.site]["base"])
    res, vs, vb, D = compute(a.site, df, cols)
    yr, mo = coverage(a.site, df); an = ta_anomaly(df)
    show(a.site, vs, vb, D, yr, mo, an)
    cnt = D.recommended.value_counts().to_dict()
    print(f"\nCL02 SUMMARY {a.site}: gaps {len(D)} | " + " | ".join(f"{k}={v}" for k, v in cnt.items()) + " | forcing writes 0", flush=True)
    if a.check: print("CL02 CHECK ONLY: no files written.", flush=True); return
    out = C.ROOT / "reports" / (f"cl02_{a.site}_alternatives_decision_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"decision_table.csv": D, "validation_summary.csv": vs, "validation_by_T_bin.csv": vb, "coverage_by_year.csv": yr, "coverage_first_two_years_by_month.csv": mo, "TA_ERA_anomaly_rows.csv": an}
    for k, d in files.items(): d.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("CL02 read-only alternatives and predeclared recommendations; adoption is the user's decision.\n")
    names = [*files, "SCIENTIFIC_HOLD.md"]
    rec = {"version": VERSION, "inputs": info, "recommendation_counts": cnt, "forcing_writes": 0,
           "output_sha256": {n: M.sha(out / n) for n in names}}
    (out / "cl02_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("CL02 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("CL02 STOP:", exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

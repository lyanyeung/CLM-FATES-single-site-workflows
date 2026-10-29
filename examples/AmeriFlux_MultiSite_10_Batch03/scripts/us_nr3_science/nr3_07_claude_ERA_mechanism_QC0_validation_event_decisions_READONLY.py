#!/usr/bin/env python3
"""US-NR3 Stage07 (Claude): metadata, ERA-pair mechanism, real-QC0 validation and per-event decisions.

READ ONLY. It builds on the operator-verified Stage01 inventory, imported from its pinned Git blob
(nr3-01-v2, blob 83e3643e...), which re-verifies the Stage07/10/12G SHA lineage and the
238 = 172 + 66 reconciliation. Original BASE v6-5 is SHA-pinned. Nothing original is written.

A  METADATA     FLUXNET BIF (ERA/UTC/height rows) and BIFVARINFO groups for TA/RH/VPD/PA/T_SONIC/H2O;
                any AUXMETEO / BASE-BADM file found next to the sources (listed and parsed if CSV/XLSX).
B  ERA PAIR     every FLUXMET-clock TA_ERA/VPD_ERA pair: e_ERA = esw(TA_ERA) - VPD_ERA. Census by year
   MECHANISM    and TA_ERA bin; the VPD_ERA lower envelope (floor) overall and per year; where the
                existing ERA5-Land files exist, OLS of VPD_ERA on grid VPD and TA_ERA on grid T2M
                (FLUXNET downscaling is an independent linear regression per variable, Vuichard &
                Papale 2015: VPD^d = s*VPD + i, T^d = s'*T + i'); counts of negative e with
                esw(TA_ERA) below the fitted VPD intercept (intercept alone exceeds saturation).
C  QC0          truth = simultaneous TA_F_QC = VPD_F_QC = 0, e_truth = esw(TA_F) - VPD_F > 0.
   VALIDATION   Fixed (unfitted) methods for the vapour pressure e that QBOT needs:
                  RH_SONIC   BASE RH x esw(T*), T* = humidity-corrected sonic T (Ts = T(1+0.51q))
                  RH_ERA_T   BASE RH x esw(TA_ERA)
                  COMP_E     esw(TA_ERA) - VPD_ERA (non-positive -> not formable)
                  GRID_A     esw(ERA5-Land d2m) (absolute e; existing years only)
                  EMP_LOYO   QC0 RH climatology (month, 3-h block, TA_ERA bin) x esw(TA_ERA), the
                             predicted row's WHOLE YEAR excluded (leave-one-year-out), >= 20 analogues
                Lineage check: RH x esw(TA_F) vs e_truth (VPD_F derived from the same RH sensor?).
                Strata: pooled, year, month, TA_F regime, COLD44 = Dec/Jan with TA_F <= -10 C, and
                COLD44 per year; e error N/MAE/bias/P95/share>0.5 hPa/median relative error.
D  EVENTS       all 238 Stage12G missing HH with ancestor reasons, BASE channels, candidates, phase and
                DATM-cap flags, edge continuity, and a class (rules fixed here, before any run):
   SOURCE_MEASURED_SUPPORTED   BASE RH+T_SONIC+PA present; RH_SONIC passes the COLD44 criteria
                               (pooled and every year with N >= 50: MAE_e <= 0.15 hPa, |bias_e| <= 0.10,
                               median relative error <= 10 %, MAE below every ERA-family method);
                               for a year without QC0 truth (2017) the e envelope from the
                               cross-year COLD44 sonic-T bias range must be <= 0.15 hPa half-width;
                               |T* - TA_USE| <= 5 C; e <= esi(TA_USE) (no ice supersaturation at the
                               forcing temperature).
   PHYSICS_CONFLICT_HOLD       any of those fails for a BASE row; original mixed-QC negative-e rows;
                               ERA/grid-only rows whose candidates are non-physical or unvalidated.
   EXTERNAL_ERA_CANDIDATE_UNCERTAIN  no BASE triplet, at least one of GRID_A / EMP_LOYO physical at
                               TA_USE/PSRF and passing Stage12j gates in its (month, TA_ERA regime)
                               stratum (N >= 100). Sensitivity only.
   EVIDENCE_INSUFFICIENT_HOLD  nothing formable.
   APPROVED_FOR_NEW_VERSION = False for every row.
E  MIXED QC     +-3 h context of the original QC0-TA / QC1-VPD negative-e rows (2011, 2021).
F  MODEL        installed DATM source excerpts (Stage01 helper); saturation over water/ice vs DATM.

--self-test synthetic; --check prints only; --run additionally writes ONE new
reports/nr3_07_claude_* folder (CSV tables + SHA receipt). No source/shadow/forcing/model writes.
"""
import argparse, hashlib, importlib.util, json, re, sys, traceback
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "nr3-07-claude-v1-20261029"
HERE = Path(__file__).resolve().parent
S1_SCRIPT = HERE / "nr3_01_source_inventory_READONLY.py"
S1_BLOB = "83e3643ee6a3ae430d10fa046724e3812936bd38"
BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-NR3/forcing/raw/AMF_US-NR3_BASE_HH_6-5.csv")
SHA_BASE = "85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b"
BWANT = ["TIMESTAMP_START", "TA", "RH", "PA", "T_SONIC", "H2O", "VPD_PI", "WS"]
A_FL = (6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04, 3.031240396e-06, 2.034080948e-08, 6.136820929e-11)
B_FL = (6.109177956, 5.034698970e-01, 1.886013408e-02, 4.176223716e-04, 5.824720280e-06, 4.838803174e-08, 1.838826904e-10)
T_EDGES = (-np.inf, -25, -20, -15, -10, -5, 0, np.inf)
T_LAB = ("<=-25", "-25:-20", "-20:-15", "-15:-10", "-10:-5", "-5:0", ">0")
GATE = dict(N=100, MAE=1.5, BIAS=0.7, BAD2=0.10)
COLD = dict(MAE=0.15, BIAS=0.10, REL=0.10, ENVELOPE=0.15, YEAR_N=50)
MIN_ANALOGUES = 20
MIXED_QC_KEYS = ("201111291400", "202105310930")


def load_s1():
    b = S1_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != S1_BLOB:
        raise ValueError("Pinned nr3_01 v2 Git blob mismatch: " + str(S1_SCRIPT))
    spec = importlib.util.spec_from_file_location("nr3_01_for_nr3_07", S1_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


S1 = load_s1()
esw, esi = S1.esw, S1.esi


def say(label, obj):
    print(label, json.dumps(obj, ensure_ascii=True, default=lambda x: None if isinstance(x, float) and not np.isfinite(x) else str(x)), flush=True)


def table(label, df, n=200):
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", n + 10)
    print(f"\n=== {label} ===\n" + (df.head(n).to_string(index=False) if len(df) else "(none)"), flush=True)


def esat_datm(t):
    t = np.asarray(t, float); tc = np.clip(t, -50, 50)
    p = lambda k: k[0] + tc * (k[1] + tc * (k[2] + tc * (k[3] + tc * (k[4] + tc * (k[5] + tc * k[6])))))
    return np.where(t < 0, p(B_FL), p(A_FL))


def q_from_e(e_hpa, p_pa):
    e = 100 * np.asarray(e_hpa, float); return 0.622 * e / (np.asarray(p_pa, float) - 0.378 * e)


def tbin(t):
    return pd.cut(np.asarray(t, float), T_EDGES, labels=T_LAB).astype(str)


def sonic_inverse(ts, rh, p_kpa):
    """T* from sonic Ts = T (1 + 0.51 q), q from RH at T*; fixed physics, no fitted offset."""
    ts, rh, p = (np.asarray(x, float) for x in (ts, rh, p_kpa))
    t = ts.copy()
    for _ in range(50):
        q = q_from_e(esw(t) * rh / 100, p * 1000)
        new = (ts + 273.15) / (1 + 0.51 * q) - 273.15
        if np.nanmax(np.abs(new - t), initial=0) < 1e-10: return new
        t = new
    return t


def err_stats(err, truth_e):
    err = np.asarray(err, float); ok = np.isfinite(err); e = err[ok]
    n = int(ok.size); nv = int(ok.sum())
    if nv == 0: return dict(N=n, N_valid=0)
    rel = np.abs(e) / np.asarray(truth_e, float)[ok]
    return dict(N=n, N_valid=nv, valid_fraction=nv / n if n else 0.0, MAE_hPa=float(np.mean(np.abs(e))), bias_hPa=float(np.mean(e)),
                RMSE_hPa=float(np.sqrt(np.mean(e ** 2))), P95_abs_hPa=float(np.quantile(np.abs(e), .95)),
                share_gt0p5hPa=float(np.mean(np.abs(e) > .5)), share_gt2hPa=float(np.mean(np.abs(e) > 2)), median_rel=float(np.median(rel)))


def gate(s):
    return bool(s.get("N_valid", 0) >= GATE["N"] and s.get("valid_fraction", 0) >= .6 and s["MAE_hPa"] <= GATE["MAE"]
                and abs(s["bias_hPa"]) <= GATE["BIAS"] and s["share_gt2hPa"] <= GATE["BAD2"])


def emp_loyo(pool_keys, pool_rh, pool_year, pred_keys, pred_year):
    """Mean QC0 RH of the same (month, hblock, Tbin) cell, excluding the predicted row's whole year;
    falls back to (month, Tbin) then (Tbin)."""
    P = pool_keys.assign(_v=pool_rh, _y=pool_year)
    out = np.full(len(pred_keys), np.nan); lev = np.full(len(pred_keys), "", dtype=object)
    todo = np.ones(len(pred_keys), bool)
    for keys in (["month", "hblock", "Tb"], ["month", "Tb"], ["Tb"]):
        if not todo.any(): break
        cell = P.groupby(keys)._v.agg(["sum", "count"])
        cy = P.groupby(keys + ["_y"])._v.agg(["sum", "count"]).rename(columns={"sum": "sy", "count": "ny"})
        q = pred_keys.loc[todo, keys].assign(_y=np.asarray(pred_year)[todo])
        m = q.join(cell, on=keys).join(cy, on=keys + ["_y"])
        S = m["sum"].fillna(0).to_numpy() - m.sy.fillna(0).to_numpy(); N = m["count"].fillna(0).to_numpy() - m.ny.fillna(0).to_numpy()
        ok = N >= MIN_ANALOGUES; idx = np.flatnonzero(todo)[ok]
        out[idx] = S[ok] / N[ok]; lev[idx] = "+".join(keys); todo[idx] = False
    return out, lev


# ------------------------------------------------------------------ A metadata
def metadata(spec):
    d = Path(spec["primary"]).parent
    bif = v = pd.DataFrame()
    try:
        bif = pd.read_csv(S1.pin(next(d.glob("*_BIF_*.csv")), S1.RAW_SHA["bif"]), keep_default_na=False)
        table("A1 FLUXNET BIF rows (ERA / UTC / elevation / product)", bif.loc[bif.VARIABLE.str.contains("ERA|UTC|ELEV|PRODUCT|HEIGHT|TOWER", regex=True)])
        vi = pd.read_csv(S1.pin(next(d.glob("*_BIFVARINFO_HH_*.csv")), S1.RAW_SHA["varinfo"]), keep_default_na=False)
        ids = vi.loc[vi.VARIABLE.eq("VAR_INFO_VARNAME") & vi.DATAVALUE.str.match(r"^(TA|RH|VPD|PA|T_SONIC|H2O|TS)(_|$)"), "GROUP_ID"]
        v = vi.loc[vi.GROUP_ID.isin(ids)].pivot_table(index="GROUP_ID", columns="VARIABLE", values="DATAVALUE", aggfunc="first").reset_index()
        table("A2 FLUXNET BIFVARINFO groups for TA/RH/VPD/PA/T_SONIC/H2O", v)
    except (StopIteration, ValueError, KeyError) as exc:
        say("A1_A2_METADATA_UNAVAILABLE", type(exc).__name__ + ": " + str(exc))
    found = sorted({*d.glob("*AUXMETEO*"), *d.glob("*AUX*"), *BASE.parent.glob("*BIF*"), *BASE.parent.glob("*BADM*"), *BASE.parent.glob("*.xlsx"), *BASE.parent.glob("*.zip")})
    say("A3_FILES_NEAR_SOURCES", [str(x) for x in found])
    aux = []
    for f in found:
        if f.suffix == ".csv" and "AUX" in f.name.upper():
            x = pd.read_csv(S1.pin(f), keep_default_na=False)
            sel = x.loc[x.apply(lambda r: r.astype(str).str.contains(r"^(TA|VPD|PA)(_|$)").any(), axis=1)]
            table(f"A4 {f.name} rows for TA/VPD/PA", sel, 60); aux.append(sel.assign(file=f.name))
        if f.suffix == ".xlsx":
            try:
                x = pd.read_excel(S1.pin(f), sheet_name=None)
                for sh, df in x.items():
                    s = df.loc[df.apply(lambda r: r.astype(str).str.contains(r"^(TA|RH|PA|T_SONIC|H2O|VPD)(_[0-9]|$)|HMP|CSAT|LI-?7|HEIGHT|INSTRUMENT", regex=True).any(), axis=1)]
                    table(f"A5 {f.name} [{sh}] variable/instrument rows", s, 120); aux.append(s.assign(file=f.name, sheet=sh))
            except Exception as exc:
                say("A5_XLSX_UNREADABLE", dict(file=str(f), error=type(exc).__name__ + ": " + str(exc)))
    return bif, v, (pd.concat(aux, ignore_index=True) if aux else pd.DataFrame())


# ------------------------------------------------------------------ data
def load(root):
    S1.COMPACT = True
    raw, selected, missing, verified, external = S1.audit(root, Namespace(emit_missing=False, emit_anomalies=False))
    hdr = list(pd.read_csv(BASE, comment="#", nrows=0).columns)
    cols = [c for c in BWANT if c in hdr]
    b = pd.read_csv(S1.pin(BASE, SHA_BASE), comment="#", usecols=cols, na_values=-9999, dtype={"TIMESTAMP_START": str}, low_memory=False)
    b = b.rename(columns={c: "B_" + c for c in cols if c != "TIMESTAMP_START"})
    d = raw.merge(b, left_on="native_key", right_on="TIMESTAMP_START", how="left", validate="one_to_one", suffixes=("", "_base"))
    if int(d["B_RH" if "B_RH" in d else cols[1]].notna().sum()) == 0: raise ValueError("BASE join produced no RH")
    if len(d) != len(raw) or d.TIMESTAMP_START_base.isna().any(): raise ValueError("BASE/FLUXMET native join incomplete")
    d["hour"] = d.native_key.str[8:10].astype(int); d["hblock"] = d.hour // 3
    for c in ("grid_T", "grid_D", "grid_P"): d[c] = np.nan
    grid_years = []
    try:
        for rec in external:
            if "year" not in rec: continue
            times, values = S1.read_grid(rec)
            ix = d.index[d.year.eq(int(rec["year"]))]
            g = S1.interpolate_grid(times, values, S1.native_times(d.loc[ix], "TIMESTAMP_START"))
            d.loc[ix, ["grid_T", "grid_D", "grid_P"]] = np.column_stack([g["t2m"], g["d2m"], g["sp"]]); grid_years.append(int(rec["year"]))
    except ImportError as exc:
        say("GRID_UNAVAILABLE", str(exc))
    say("DATA", dict(rows=len(d), BASE_columns=cols, grid_years=grid_years, missing=len(missing), anomalies=len(verified)))
    return d, selected, missing, verified, external, grid_years


# ------------------------------------------------------------------ B mechanism
def mechanism(d, verified, missing):
    d = d.copy(); d["eERA"] = esw(d.TA_ERA) - d.VPD_ERA; d["neg"] = d.eERA < 0; d["Tb_ERA"] = tbin(d.TA_ERA)
    a84 = set(verified.native_key); m238 = set(missing.native_key)
    d["in1484"] = d.native_key.isin(a84); d["in238"] = d.native_key.isin(m238)
    yr = d.groupby("year").agg(rows=("neg", "size"), negative_e=("neg", "sum"), neg_in_1484=("in1484", "sum"),
                               VPD_ERA_min=("VPD_ERA", "min"), VPD_ERA_p01=("VPD_ERA", lambda x: x.quantile(.01)), TA_ERA_min=("TA_ERA", "min")).reset_index()
    tb = d.groupby("Tb_ERA").agg(rows=("neg", "size"), negative_e=("neg", "sum"), frac_negative=("neg", "mean"),
                                 esw_TA_ERA_median=("TA_ERA", lambda x: float(np.median(esw(x)))), VPD_ERA_p01=("VPD_ERA", lambda x: x.quantile(.01)),
                                 VPD_ERA_median=("VPD_ERA", "median")).reindex(list(T_LAB)).reset_index()
    v = d.VPD_ERA.dropna(); floor = float(v.min())
    low = v.round(3).value_counts().sort_index().head(15).rename_axis("VPD_ERA_rounded").rename("HH").reset_index()
    tot = dict(rows=len(d), negative_e_all=int(d.neg.sum()), negative_in_1484=int((d.neg & d.in1484).sum()),
               negative_outside_1484=int((d.neg & ~d.in1484).sum()), negative_in_238=int((d.neg & d.in238).sum()),
               VPD_ERA_floor=floor, rows_within_0p01_of_floor=int((v <= floor + .01).sum()),
               T_star_esw_equals_floor_C=float(243.5 * np.log(floor / 6.112) / (17.67 - np.log(floor / 6.112))))
    fit = []
    g = d.loc[d[["grid_T", "grid_D"]].notna().all(axis=1) & d.VPD_ERA.notna() & d.TA_ERA.notna()].copy()
    if len(g):
        g["VPD_grid"] = esw(g.grid_T) - esw(g.grid_D)
        for scope, s in [("ALL", g), *[(int(y), x) for y, x in g.groupby("year")]]:
            for yv, xv, nm in (("VPD_ERA", "VPD_grid", "VPD"), ("TA_ERA", "grid_T", "TA")):
                X = s[xv].to_numpy(float); Y = s[yv].to_numpy(float)
                b1, b0 = np.polyfit(X, Y, 1); r = Y - (b0 + b1 * X)
                fit.append(dict(scope=scope, variable=nm, n=len(s), slope=b1, intercept=b0, R2=1 - r.var() / Y.var(), resid_sd=r.std(),
                                mean_VPD_ERA_when_grid_VPD_lt_0p1=float(s.loc[s.VPD_grid < .1, "VPD_ERA"].mean()) if nm == "VPD" else np.nan))
        fit = pd.DataFrame(fit)
        a = float(fit.loc[(fit.scope == "ALL") & (fit.variable == "VPD"), "intercept"].iloc[0])
        tot.update(fitted_VPD_intercept_ALL=a, negative_with_esw_TA_ERA_below_intercept=int((d.neg & (esw(d.TA_ERA) < a)).sum()),
                   rows_with_esw_TA_ERA_below_intercept=int((esw(d.TA_ERA) < a).sum()),
                   grid_dewpoint_gt_T=int((g.grid_D > g.grid_T + .1).sum()), grid_rows=len(g))
    else:
        fit = pd.DataFrame()
    return d, yr, tb, low, tot, fit


# ------------------------------------------------------------------ C validation
def candidates(d, base_ok):
    """e (hPa) of every method at every row, using TA_ERA as the only temperature known at gaps."""
    rh = d.B_RH.to_numpy(float) if "B_RH" in d else np.full(len(d), np.nan)
    ts = d.B_T_SONIC.to_numpy(float) if "B_T_SONIC" in d else np.full(len(d), np.nan)
    pa = d.B_PA.to_numpy(float) if "B_PA" in d else np.full(len(d), np.nan)
    ok = base_ok
    tstar = np.where(ok, sonic_inverse(np.where(ok, ts, 0.0), np.where(ok, rh, 50.0), np.where(ok, pa, 65.0)), np.nan)
    with np.errstate(invalid="ignore"):
        ce = esw(d.TA_ERA) - d.VPD_ERA.to_numpy(float)
    out = dict(T_star=tstar, RH_SONIC=np.where(ok, rh / 100 * esw(tstar), np.nan),
               RH_ERA_T=np.where(ok, rh / 100 * esw(d.TA_ERA.to_numpy(float)), np.nan),
               COMP_E=np.where(ce > 0, ce, np.nan), GRID_A=esw(d.grid_D.to_numpy(float)))
    return out


def validate(d, cand):
    T = d.TA_F.to_numpy(float); V = d.VPD_F.to_numpy(float)
    et = esw(T) - V
    truth = (d.TA_F_QC.eq(0) & d.VPD_F_QC.eq(0)).to_numpy() & np.isfinite(et) & (et > 0) & (V >= 0) & (T > -60) & (T < 50)
    pool = d.loc[truth, ["month", "hblock"]].assign(Tb=tbin(T[truth]))
    rh_truth = et[truth] / esw(T[truth])
    pk = d[["month", "hblock"]].assign(Tb=tbin(d.TA_ERA))
    emp, lev = emp_loyo(pool, rh_truth, d.year.to_numpy()[truth], pk, d.year.to_numpy())
    cand["EMP_LOYO"] = emp * esw(d.TA_ERA.to_numpy(float)); cand["EMP_level"] = lev
    rh = d.B_RH.to_numpy(float) if "B_RH" in d else np.full(len(d), np.nan)
    lineage = err_stats((rh / 100 * esw(T) - et)[truth], et[truth])
    say("C0_LINEAGE_RH_x_esw(TA_F)_vs_QC0_e", lineage)
    methods = ["RH_SONIC", "RH_ERA_T", "COMP_E", "GRID_A", "EMP_LOYO"]
    cold44 = truth & d.month.isin([12, 1]).to_numpy() & (T <= -10)
    strata = [("POOLED", truth), ("COLD44_DecJan_TAF_le_-10", cold44)]
    strata += [(f"MONTH_{m:02d}", truth & (d.month.to_numpy() == m)) for m in range(1, 13)]
    strata += [(f"TAF_{b}", truth & (tbin(T) == b)) for b in T_LAB]
    strata += [("ABS_TAF_minus_TAERA_gt5", truth & (np.abs(T - d.TA_ERA.to_numpy(float)) > 5))]
    rows = []
    for k in methods:
        err = cand[k] - et
        for nm, s in strata:
            r = err_stats(err[s], et[s]); r.update(method=k, stratum=nm); r["Stage12j_gate"] = gate(r) if r.get("N_valid") else False; rows.append(r)
        for y in sorted(d.year.unique()):
            for nm, s in (("YEAR", truth), ("COLD44_YEAR", cold44)):
                s2 = s & (d.year.to_numpy() == y)
                if s2.sum() == 0: continue
                r = err_stats(err[s2], et[s2]); r.update(method=k, stratum=f"{nm}_{y}"); r["Stage12j_gate"] = gate(r) if r.get("N_valid") else False; rows.append(r)
    V_ = pd.DataFrame(rows)
    # sonic temperature error where truth exists (diagnostic, never applied as a correction)
    tsr = []
    for y in sorted(d.year.unique()):
        s = cold44 & (d.year.to_numpy() == y) & np.isfinite(cand["T_star"])
        if s.sum(): dT = cand["T_star"][s] - T[s]; tsr.append(dict(year=int(y), N=int(s.sum()), bias_C=float(dT.mean()), MAE_C=float(np.abs(dT).mean())))
    TS = pd.DataFrame(tsr)
    # stratum lookup for gap rows: (month, TA_ERA regime) Stage12j gate
    sg = []
    for k in ("GRID_A", "EMP_LOYO"):
        err = cand[k] - et; tb = tbin(d.TA_ERA)
        for m in range(1, 13):
            for b in T_LAB:
                s = truth & (d.month.to_numpy() == m) & (tb == b)
                r = err_stats(err[s], et[s]); r.update(method=k, month=m, TA_ERA_bin=b); r["gate"] = gate(r) if r.get("N_valid") else False; sg.append(r)
    return truth, et, V_, TS, pd.DataFrame(sg)


def cold_criteria(V_, TS):
    v = V_.set_index(["method", "stratum"])
    c = v.loc[("RH_SONIC", "COLD44_DecJan_TAF_le_-10")]
    yrs = V_.loc[(V_.method == "RH_SONIC") & V_.stratum.str.startswith("COLD44_YEAR_") & (V_.N_valid >= COLD["YEAR_N"])]
    ok_y = ((yrs.MAE_hPa <= COLD["MAE"]) & (yrs.bias_hPa.abs() <= COLD["BIAS"]) & (yrs.median_rel <= COLD["REL"])).all() and len(yrs) > 0
    others = [v.loc[(m, "COLD44_DecJan_TAF_le_-10"), "MAE_hPa"] for m in ("RH_ERA_T", "COMP_E", "GRID_A", "EMP_LOYO") if (m, "COLD44_DecJan_TAF_le_-10") in v.index]
    others = [x for x in others if np.isfinite(x)]
    pooled = bool(c.MAE_hPa <= COLD["MAE"] and abs(c.bias_hPa) <= COLD["BIAS"] and c.median_rel <= COLD["REL"])
    beats = bool(all(c.MAE_hPa < x for x in others))
    env = (float(TS.bias_C.min()), float(TS.bias_C.max())) if len(TS) else (np.nan, np.nan)
    res = dict(pooled_pass=pooled, every_year_pass=bool(ok_y), years_tested=int(len(yrs)), beats_ERA_family=beats,
               cold44_MAE=float(c.MAE_hPa), cold44_bias=float(c.bias_hPa), cold44_median_rel=float(c.median_rel),
               sonic_bias_envelope_C=env, RH_SONIC_SUPPORTED=bool(pooled and ok_y and beats))
    say("C2_RH_SONIC_COLD44_CRITERIA", res)
    return res


# ------------------------------------------------------------------ D events
def events(d, selected, missing, cand, sg, crit, truth_years):
    pos = {k: i for i, k in enumerate(d.native_key)}
    sel = selected.copy(); sel["native_key"] = S1.keys(sel, "time")
    se = (esw(sel.TA_USE) - sel.VPD_USE).to_numpy(float); skey = {k: i for i, k in enumerate(sel.native_key)}
    fin = np.isfinite(se)
    lo_env, hi_env = crit["sonic_bias_envelope_C"]
    sgi = sg.set_index(["method", "month", "TA_ERA_bin"]).gate
    rows = []
    for r in missing.to_dict("records"):
        k = r["native_key"]; i = pos[k]; T = float(r["TA_USE"]); P = float(r["PSRF"])
        x = {c: r.get(c) for c in ("native_key", "year", "month", "episode", "missing_fields", "TA_USE", "PSRF", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC",
                                    "TA_ERA", "VPD_ERA", "HOLD_class", "Stage12B_reason", "Stage12E_reason", "Stage12G_reason", "in_1484_source_anomalies")}
        for c in ("B_TA", "B_RH", "B_T_SONIC", "B_PA", "B_H2O"): x[c] = d[c].iloc[i] if c in d else np.nan
        x["e_ERA_pair"] = esw(d.TA_ERA.iloc[i]) - d.VPD_ERA.iloc[i]
        x["T_star_C"] = cand["T_star"][i]; x["dT_star_minus_TA_USE"] = x["T_star_C"] - T
        triplet = bool(np.isfinite(x["B_RH"]) and 0 <= x["B_RH"] <= 100 and np.isfinite(x["B_T_SONIC"]) and -70 <= x["B_T_SONIC"] <= 60
                       and np.isfinite(x["B_PA"]) and 40 <= x["B_PA"] <= 110)
        x["BASE_triplet"] = triplet
        for m in ("RH_SONIC", "RH_ERA_T", "GRID_A", "EMP_LOYO"):
            e = cand[m][i]; x[f"{m}_e_hPa"] = e
            x[f"{m}_VPD_at_TA_USE"] = esw(T) - e if np.isfinite(e) else np.nan
            x[f"{m}_RHice_at_TA_USE_pct"] = 100 * e / esi(T) if np.isfinite(e) and T < 0 else np.nan
            x[f"{m}_DATM_would_cap"] = bool(np.isfinite(e) and q_from_e(e, P) > q_from_e(esat_datm(T), P))
        if triplet and np.isfinite(lo_env):
            ts = d.B_T_SONIC.iloc[i]; rh = x["B_RH"]; pa = x["B_PA"]
            ea = [rh / 100 * esw(sonic_inverse(np.array([ts]), np.array([rh]), np.array([pa]))[0] - b) for b in (lo_env, hi_env)]
            x["RH_SONIC_envelope_halfwidth_hPa"] = abs(ea[0] - ea[1]) / 2
        else:
            x["RH_SONIC_envelope_halfwidth_hPa"] = np.nan
        j = skey[k]; b_ = j - 1
        while b_ >= 0 and not fin[b_]: b_ -= 1
        a_ = j + 1
        while a_ < len(se) and not fin[a_]: a_ += 1
        x["edge_e_before_hPa"] = se[b_] if b_ >= 0 else np.nan; x["edge_e_after_hPa"] = se[a_] if a_ < len(se) else np.nan
        mixed = bool(r.get("TA_F_QC") == 0 and r.get("VPD_F_QC") == 1 and np.isfinite(r.get("VPD_F", np.nan)) and esw(r["TA_F"]) - r["VPD_F"] < 0)
        why = []
        if mixed:
            cls = "PHYSICS_CONFLICT_HOLD"; why.append("original QC0 TA with QC1 VPD gives negative e; manual source review")
        elif triplet:
            e = x["RH_SONIC_e_hPa"]
            if not crit["RH_SONIC_SUPPORTED"]: why.append("RH_SONIC fails the COLD44 validation criteria")
            if int(r["year"]) not in truth_years and not (x["RH_SONIC_envelope_halfwidth_hPa"] <= COLD["ENVELOPE"]): why.append("no in-year QC0 and sonic-bias e envelope too wide")
            if not abs(x["dT_star_minus_TA_USE"]) <= 5: why.append("|T* - TA_USE| > 5 C: forcing temperature unresolved")
            if T < 0 and not e <= esi(T): why.append("e above ice saturation at forcing TA_USE")
            if not (np.isfinite(e) and 0 < e < esw(T)): why.append("e not physical at TA_USE")
            cls = "SOURCE_MEASURED_SUPPORTED" if not why else "PHYSICS_CONFLICT_HOLD"
            if not why: why.append("measured RH + sonic T*; validated in COLD44; physical at TA_USE")
        else:
            ok = []
            tb = tbin(np.array([d.TA_ERA.iloc[i]]))[0]
            for m in ("GRID_A", "EMP_LOYO"):
                e = x[f"{m}_e_hPa"]
                phys = np.isfinite(e) and 0 < e < esw(T) and (T >= 0 or e <= esi(T))
                g = bool(sgi.get((m, int(r["month"]), tb), False))
                if phys and g: ok.append(m)
            x["validated_physical_external"] = "|".join(ok)
            if ok:
                cls = "EXTERNAL_ERA_CANDIDATE_UNCERTAIN"; why.append("no tower humidity; " + "/".join(ok) + " physical at TA_USE and gated in its month x TA_ERA stratum")
            elif not np.isfinite(x["GRID_A_e_hPa"]) and not np.isfinite(x["EMP_LOYO_e_hPa"]):
                cls = "EVIDENCE_INSUFFICIENT_HOLD"; why.append("no tower humidity, no ERA5-Land year, no climatology")
            else:
                cls = "PHYSICS_CONFLICT_HOLD"; why.append("external candidates non-physical at TA_USE or unvalidated in stratum")
        x["class"] = cls; x["rationale"] = "; ".join(why); x["APPROVED_FOR_NEW_VERSION"] = False
        rows.append(x)
    return pd.DataFrame(rows)


def mixed_context(d):
    out = []
    for k in MIXED_QC_KEYS:
        j = np.flatnonzero(d.native_key.to_numpy() == k)
        if not len(j): continue
        s = d.iloc[max(0, j[0] - 6): j[0] + 7]
        c = [x for x in ("native_key", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "RH", "TA_F_MDS", "TA_F_MDS_QC", "VPD_F_MDS", "VPD_F_MDS_QC",
                         "TA_ERA", "VPD_ERA", "B_TA", "B_RH", "B_T_SONIC", "B_H2O", "B_PA", "B_WS") if x in s]
        s = s[c].copy(); s["e_TAF_VPDF"] = esw(s.TA_F) - s.VPD_F; out.append(s.assign(focus=k))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def sat_table():
    t = np.array([-35, -30, -25, -20, -15, -10, -5, -1.0])
    return pd.DataFrame({"T_C": t, "esw_Magnus_hPa": esw(t), "esi_Magnus_hPa": esi(t), "DATM_Flatau_hPa": esat_datm(t),
                         "RHw_at_ice_saturation_pct": 100 * esi(t) / esw(t)})


def self_test():
    t = sonic_inverse(np.array([-20., 5.]), np.array([80., 50.]), np.array([65., 65.]))
    assert (t < np.array([-20., 5.])).all() and abs(float(esat_datm(-8.39)) - 2.9929) < 2e-4
    pk = pd.DataFrame({"month": [1] * 60, "hblock": [0] * 60, "Tb": ["x"] * 60})
    rh = np.r_[np.full(30, .5), np.full(30, .9)]; yr = np.r_[np.full(30, 2010), np.full(30, 2011)]
    e, lev = emp_loyo(pk, rh, yr, pk.iloc[:2], np.array([2010, 2011]))
    assert abs(e[0] - .9) < 1e-12 and abs(e[1] - .5) < 1e-12, "leave-one-year-out"
    s = err_stats(np.array([.1, -.1, np.nan]), np.array([1., 1., 1.])); assert s["N_valid"] == 2 and abs(s["MAE_hPa"] - .1) < 1e-12
    assert tbin(np.array([-30, -12, 3]))[1] == "-15:-10"
    print("NR3_07 SELF-TEST PASS: sonic inverse, DATM esat, leave-one-year-out climatology, error stats, bins", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--root", type=Path, default=S1.ROOT); ap.add_argument("--model-root", type=Path, default=S1.ROOT.parent.parent / "CTSM")
    a = ap.parse_args()
    print("NR3_07 CLAUDE ERA-MECHANISM / QC0 VALIDATION / EVENT DECISIONS | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    d, selected, missing, verified, external, gy = load(a.root)
    manifest = json.loads((a.root / S1.S07 / "exact_input_manifest.json").read_text())
    spec = [x for x in manifest["sites"] if x["site"] == S1.SITE][0]
    bif, varinfo, aux = metadata(spec)
    d, yr, tb, low, tot, fit = mechanism(d, verified, missing)
    say("B0_ERA_PAIR_TOTALS", tot)
    table("B1 ERA pair negative e by year", yr); table("B2 ERA pair by TA_ERA bin", tb); table("B3 lowest VPD_ERA values (floor)", low)
    table("B4 OLS against ERA5-Land (existing years)", fit, 80)
    base_ok = (d.get("B_RH", pd.Series(np.nan, index=d.index)).between(0, 100) & d.get("B_T_SONIC", pd.Series(np.nan, index=d.index)).between(-70, 60)
               & d.get("B_PA", pd.Series(np.nan, index=d.index)).between(40, 110)).to_numpy()
    cand = candidates(d, base_ok)
    truth, et, V_, TS, sg = validate(d, cand)
    key = V_.stratum.isin(["POOLED", "COLD44_DecJan_TAF_le_-10", "ABS_TAF_minus_TAERA_gt5"]) | V_.stratum.str.startswith("TAF_")
    table("C1 validation of e on real QC0 (pooled, COLD44, T regimes, |dT|>5)", V_.loc[key, ["method", "stratum", "N", "N_valid", "MAE_hPa", "bias_hPa", "P95_abs_hPa", "share_gt0p5hPa", "median_rel", "Stage12j_gate"]].round(3), 80)
    table("C1b COLD44 by year", V_.loc[V_.stratum.str.startswith("COLD44_YEAR_"), ["method", "stratum", "N_valid", "MAE_hPa", "bias_hPa", "P95_abs_hPa", "median_rel"]].round(3), 120)
    table("C1c sonic T* minus TA_F in COLD44 by year (diagnostic, never applied)", TS.round(3))
    crit = cold_criteria(V_, TS)
    truth_years = set(int(y) for y in d.loc[truth, "year"].unique())
    E = events(d, selected, missing, cand, sg, crit, truth_years)
    if int(E.BASE_triplet.sum()) != 44: raise ValueError(f"BASE triplet rows {int(E.BASE_triplet.sum())} != 44 (Stage04/05)")
    say("D0_CLASS_COUNTS", E["class"].value_counts().to_dict())
    table("D1 classes by year", E.groupby(["year", "class"]).size().rename("HH").reset_index())
    table("D2 classes by inherited reason", E.groupby(["HOLD_class", "Stage12E_reason", "class"], dropna=False).size().rename("HH").reset_index())
    c44 = ["native_key", "TA_USE", "T_star_C", "dT_star_minus_TA_USE", "B_RH", "RH_SONIC_e_hPa", "RH_SONIC_RHice_at_TA_USE_pct", "RH_SONIC_envelope_halfwidth_hPa",
           "RH_ERA_T_e_hPa", "GRID_A_e_hPa", "EMP_LOYO_e_hPa", "e_ERA_pair", "edge_e_before_hPa", "edge_e_after_hPa", "class", "rationale"]
    table("D3 the 44 BASE-triplet rows", E.loc[E.BASE_triplet, c44].round(3), 50)
    table("D4 non-BASE rows not in the 1484 (2011/2021 and others)", E.loc[~E.BASE_triplet & ~E.in_1484_source_anomalies.astype(bool),
          ["native_key", "TA_USE", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "Stage12E_reason", "GRID_A_e_hPa", "EMP_LOYO_e_hPa", "class", "rationale"]].round(3), 80)
    MX = mixed_context(d); table("E1 mixed-QC context (+-3 h)", MX.round(3), 40)
    ST = sat_table(); table("F1 saturation over water / ice / DATM", ST.round(4))
    S1.installed_source_review(a.model_root)
    print(f"\nNR3_07 SUMMARY: 238 missing | " + " | ".join(f"{k}={v}" for k, v in E["class"].value_counts().items())
          + f" | ERA negative-e pairs {tot['negative_e_all']} (1484 selected) | approved 0 | writes: {'report only' if a.run else 'none'}", flush=True)
    for p, h in S1.READS.items():
        if S1.digest(p) != h: raise ValueError("input changed during audit: " + p)
    if a.check: print("NR3_07 CHECK ONLY: no files written.", flush=True); return
    out = a.root / "reports" / ("nr3_07_claude_event_science_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    A84 = d.loc[d.in1484, ["native_key", "source_csv_row", "year", "month", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "TA_ERA", "VPD_ERA", "eERA",
                           "grid_T", "grid_D", "grid_P", "in238"]].copy()
    A84["es_w"] = esw(A84.TA_ERA); A84["es_i"] = esi(A84.TA_ERA); A84["RH_w_pct"] = 100 * A84.eERA / A84.es_w; A84["RH_i_pct"] = 100 * A84.eERA / A84.es_i
    A84["GRID_A_e"] = esw(A84.grid_D); A84["dT_ERA_minus_grid"] = A84.TA_ERA - A84.grid_T
    A84["esw_TA_ERA_below_VPD_intercept"] = esw(A84.TA_ERA) < tot.get("fitted_VPD_intercept_ALL", np.nan)
    files = {"US_NR3_238_missing_event_decisions.csv": E, "US_NR3_1484_source_ERA_pair_matrix.csv": A84, "B_negative_e_by_year.csv": yr,
             "B_ERA_pair_by_TA_ERA_bin.csv": tb, "B_VPD_ERA_floor.csv": low, "B_OLS_vs_ERA5Land.csv": fit, "C_validation_e.csv": V_,
             "C_sonic_T_bias_COLD44.csv": TS, "C_external_stratum_gates.csv": sg, "E_mixed_QC_context.csv": MX, "F_saturation.csv": ST,
             "A_BIFVARINFO_selected.csv": varinfo, "A_aux_metadata.csv": aux}
    for k, v in files.items(): v.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("Read-only evidence. APPROVED_FOR_NEW_VERSION = False for all 238; any adoption needs separate user approval.\n")
    rec = {"version": VERSION, "s1_blob": S1_BLOB, "inputs_sha256": dict(S1.READS), "totals": tot, "criteria": crit,
           "class_counts": E["class"].value_counts().to_dict(), "approved": 0,
           "output_sha256": {n: S1.digest(out / n) for n in [*files, "SCIENTIFIC_HOLD.md"]}}
    (out / "nr3_07_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("NR3_07 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("NR3_07 STOP:", type(exc).__name__, exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

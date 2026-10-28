#!/usr/bin/env python3
"""MtB01 (Claude workstream, US-MtB only): regime-matched QC0 humidity evidence. READ ONLY.

Why: Stage12d (companion TA_ERA/VPD_ERA RH) and Stage12g/12j (independent ERA5-Land) both stop
at the same place: at the remaining US-MtB humidity gaps the measured tower TA_F (QC0) is
>5 C colder than the reanalysis (Stage12d: 2821 MtB rows). Stage12j validated transfer methods
on ALL cold QC0 humidity, most of which has small tower-ERA temperature differences. This
stage asks whether measured tower truth exists in the TARGET regime and how methods behave there.

Sections (one pass over the SHA-verified original release; inputs re-verified through the
pinned Stage12j -> 12i -> 12h -> 12g chain):
 A  Census of every US-MtB humidity gap in the sealed Stage12g timeline: year, Stage12g
    ledger reason, original TA_F_QC / VPD_F_QC, local hour, month, dT = TA_F - TA_ERA bin,
    gap run length, QC0 humidity anchors within +-2 h.
 B  Measured truth by regime: VPD_F_QC=0 & TA_F_QC=0 humidity counts per year x dT bin.
 C  Predeclared candidates, validated ONLY against that truth (never against QC1/QC2/MDS):
      COMPANION_RH   release-paired TA_ERA/VPD_ERA water RH at tower TA_F (Stage12d formula)
      COMPANION_E    release-paired vapour pressure kept, VPD at tower TA_F
      EMP_BIN_RH     mean measured RH_w of QC0 in the same (month, 3-h block, dT bin) cell,
                     falling back to (month, dT bin) then (dT bin); >=20 analogues required;
                     10-day blocks: the block containing the predicted time is ALWAYS excluded
      EMP_ADJ_RH     COMPANION_RH + block-excluded mean (RH_obs - RH_companion) per
                     (month, dT bin), same fallback and >=20 rule
    Gates, identical to Stage12j and fixed here BEFORE any result:
      per year (cold QC0, tower T <= 5 C): N >= 50, valid fraction >= 0.60, VPD MAE <= 1.5 hPa,
      |bias| <= 0.7 hPa, fraction |error| > 2 hPa <= 0.10
      REGIME gate (new, pooled over years, all T): QC0 with |dT| > 5 C, same five thresholds
      method PASS = every year with N >= 50 passes AND >= 3 such years AND REGIME passes
    Error tails: by dT bin, tower T bin, month, measured VPD bin (descriptive only), runs of
    consecutive |error| > 2 hPa.
 D  Temperature plausibility: yearly TA_F extremes and QC, contiguous episodes TA_F < -25 C
    with TA_ERA (no edits; QC0 is not deleted).
 E  +-2 h context: 2024-02-11 05:00-06:30 frozen-phase events and the first 10 extreme-cold
    episodes: TA_F/VPD_F/PA_F + QC class, TA_ERA/VPD_ERA/PA_ERA, independent ERA5-Land
    T2m/D2m/SP where a verified Stage12f year exists, RH_water/RH_ice and VPD/QBOT for each
    candidate. Classes: QC0 measured, QC1/QC2/QC3 gap-filled, external, computed.
 F  Installed model evidence: CTSM/CDEPS git HEADs and the humidity lines (shum, forc_q, qsat,
    rh) in the installed DATM CLMNCEP mode, lnd_import_export, atm2lndMod and QSatMod.
 G  ERA5-Land evidence files: variables present (a geopotential field would allow true grid
    orography; the Stage12i height is a hydrostatic PROXY) and grid coordinates.

--self-test synthetic only, no file access. --check full computation, prints, NO writes.
--run same, then ONE new reports/mtb01_* folder with CSVs, code evidence and SHA receipt.
Nothing here edits source, Stage12g/12j/12k, the 233 holds, TA_F, clocks, Post-v5, DATM,
CIME or Slurm, and no candidate is a repair approval: the user decides.
"""
import argparse, hashlib, importlib.util, json, re, subprocess, sys, traceback, zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-MtB01-v1-20261028-regime-matched-QC0-humidity-READONLY"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE = Path.home() / "CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
CTSM = Path("/iridisfs/scratch/ly3n24/CLM_FATES/CTSM")
J_SCRIPT = BASE / "scripts/stage12/12j_us_mtb_elevation_aware_QC0_humidity_crossvalidation.py"
J_BLOB = "92ac1fed33967d5a6af24cbd3bbab0e7b150c499"
SITE = "US-MtB"
METHODS = ("COMPANION_RH", "COMPANION_E", "EMP_BIN_RH", "EMP_ADJ_RH")
DT_EDGES = (-np.inf, -8, -5, -2, 2, 5, np.inf)
DT_LABELS = ("<=-8", "-8:-5", "-5:-2", "-2:2", "2:5", ">5")
T_EDGES = (-np.inf, -15, -10, -5, 0, 5, 15, np.inf)
T_LABELS = ("<=-15", "-15:-10", "-10:-5", "-5:0", "0:5", "5:15", ">15")
V_EDGES = (-np.inf, 0.25, 1, 2, 5, 10, np.inf)
V_LABELS = ("0-0.25", "0.25-1", "1-2", "2-5", "5-10", ">10")
MIN_ANALOGUES = 20
GATE = dict(N=50, FRAC=0.60, MAE=1.5, BIAS=0.7, BAD2=0.10)
MIN_GATED_YEARS = 3
REGIME_ABS_DT = 5.0
COLD_T = 5.0
EXTREME_COLD = -25.0
ICE_EVENTS = ("202402110500", "202402110530", "202402110600", "202402110630")
WINDOW_HH = 4
QC_CLASS = {0: "QC0_measured", 1: "QC1_gapfilled", 2: "QC2_gapfilled", 3: "QC3_gapfilled_poor"}
CODE_FILES = ("datm_datamode_clmncep_mod.F90", "lnd_import_export.F90", "atm2lndMod.F90", "QSatMod.F90")
CODE_RE = re.compile(r"shum|forc_q\b|forc_q_|qsat|forc_rh|\brh\b|tdew|esat|e_sat|supersat", re.I)


# ----------------------------------------------------------------- physics (same as Stage12j)
def esw(t):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        t = np.asarray(t, dtype=float); return 6.112 * np.exp(17.67 * t / (t + 243.5))


def esi(t):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        t = np.asarray(t, dtype=float); return 6.112 * np.exp(22.46 * t / (t + 272.62))


def q_from_e(e_hpa, p_pa):
    e = 100 * np.asarray(e_hpa, dtype=float)
    return 0.622 * e / (np.asarray(p_pa, dtype=float) - 0.378 * e)


def physical(t, p, e):
    t = np.asarray(t, dtype=float); e = np.asarray(e, dtype=float); p = np.asarray(p, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        q = q_from_e(e, p)
        return (np.isfinite(e) & np.isfinite(t) & np.isfinite(p) & (e > 0) & (e < esw(t)) & (q > 0) & (q < .08)
                & ((t >= 0) | (e <= esi(t))))


def num(s):
    a = np.array(pd.to_numeric(s, errors="coerce"), dtype=float, copy=True)
    a[(~np.isfinite(a)) | (a <= -9990)] = np.nan
    return a


def regular(p):
    p = Path(p)
    if not p.is_file() or p.is_symlink(): raise ValueError("Missing or symlinked source: " + str(p))
    return p


def sha(p):
    h = hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def gitblob(p):
    b = regular(p).read_bytes()
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def cut(x, edges, labels):
    out = pd.cut(pd.Series(np.asarray(x, dtype=float)), bins=list(edges), labels=list(labels)).astype(object)
    return out.where(out.notna(), "MISSING").astype(str).to_numpy()


def runs(mask):
    """(start, length) of consecutive True runs in a boolean array."""
    m = np.asarray(mask, dtype=bool)
    if not m.any(): return []
    d = np.diff(np.concatenate(([0], m.astype(int), [0])))
    s, e = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    return list(zip(s.tolist(), (e - s).tolist()))


# ----------------------------------------------------------------- frame construction
def frame_from(flux, era):
    """Merge original FLUXMET and release-paired ERA columns on the native clock; NOLEAP."""
    for need, d, nm in ((("TIMESTAMP_START", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "PA_F"), flux, "FLUXMET"),
                        (("TIMESTAMP_START", "TA_ERA", "VPD_ERA", "PA_ERA"), era, "ERA")):
        miss = [c for c in need if c not in d]
        if miss: raise ValueError(f"{nm} columns missing: {miss}")
    if flux.TIMESTAMP_START.duplicated().any() or era.TIMESTAMP_START.duplicated().any():
        raise ValueError("duplicated native timestamps")
    df = flux.merge(era, on="TIMESTAMP_START", how="inner", validate="one_to_one")
    if len(df) != len(flux) or len(df) != len(era): raise ValueError("FLUXMET and ERA native clocks differ")
    ts = pd.to_datetime(df.TIMESTAMP_START, format="%Y%m%d%H%M", errors="raise")
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df = df.loc[keep].reset_index(drop=True); ts = ts.loc[keep].reset_index(drop=True)
    out = pd.DataFrame({"native_key": df.TIMESTAMP_START.astype(str), "stamp": ts,
                        "year": ts.dt.year, "month": ts.dt.month, "hour": ts.dt.hour, "doy": ts.dt.dayofyear})
    for c in ("TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "PA_F", "TA_ERA", "VPD_ERA", "PA_ERA",
              "WS_F", "SW_IN_F", "LW_IN_F"):
        out[c] = num(df[c]) if c in df else np.nan
    out["P_Pa"] = out.PA_F * 1000.0
    out["dT"] = out.TA_F - out.TA_ERA
    out["dT_bin"] = cut(out.dT, DT_EDGES, DT_LABELS)
    out["T_bin"] = cut(out.TA_F, T_EDGES, T_LABELS)
    out["block"] = out.year * 100 + (out.doy - 1) // 10
    out["hblock"] = out.hour // 3
    e_obs = esw(out.TA_F) - out.VPD_F
    out["truth"] = ((out.VPD_F_QC == 0) & (out.TA_F_QC == 0) & (out.VPD_F >= 0) & (out.VPD_F < esw(out.TA_F))
                    & physical(out.TA_F, out.P_Pa, e_obs) & (out.P_Pa > 45000) & (out.P_Pa < 110000))
    with np.errstate(invalid="ignore", divide="ignore"):
        out["RH_obs"] = np.where(out.truth, e_obs / esw(out.TA_F), np.nan)
    return out


def block_excluded_mean(df, value, levels, pred_rows):
    """Mean of `value` over pool rows sharing a cell, excluding the predicted row's 10-day block.
    levels: list of key-column tuples, tried in order; >= MIN_ANALOGUES required."""
    pool = df.loc[np.isfinite(value)].assign(_v=value[np.isfinite(value)])
    pred = np.full(len(df), np.nan); level = np.full(len(df), "", dtype=object); nused = np.zeros(len(df))
    todo = np.asarray(pred_rows, dtype=bool).copy()
    for keys in levels:
        if not todo.any(): break
        k = list(keys)
        cell = pool.groupby(k)._v.agg(["sum", "count"]).rename(columns={"sum": "S", "count": "N"})
        cb = pool.groupby(k + ["block"])._v.agg(["sum", "count"]).rename(columns={"sum": "Sb", "count": "Nb"})
        q = df.loc[todo, k + ["block"]]
        m = q.join(cell, on=k).join(cb, on=k + ["block"])
        S = m.S.fillna(0).to_numpy() - m.Sb.fillna(0).to_numpy()
        N = m.N.fillna(0).to_numpy() - m.Nb.fillna(0).to_numpy()
        ok = N >= MIN_ANALOGUES
        idx = np.flatnonzero(todo)[ok]
        pred[idx] = S[ok] / N[ok]; level[idx] = "+".join(k); nused[idx] = N[ok]
        todo[idx] = False
    return pred, level, nused


def candidates(df):
    """Vapour pressure e (hPa) for each method at every row (NaN when not formable)."""
    T, Te = df.TA_F.to_numpy(), df.TA_ERA.to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        e_era = esw(Te) - df.VPD_ERA.to_numpy()
        rh_c = e_era / esw(Te)
    rh_c = np.where(np.isfinite(rh_c) & (rh_c > 0) & (rh_c <= 1.0), rh_c, np.nan)
    e = {"COMPANION_RH": rh_c * esw(T), "COMPANION_E": np.where(np.isfinite(rh_c), e_era, np.nan)}
    lv1 = [("month", "hblock", "dT_bin"), ("month", "dT_bin"), ("dT_bin",)]
    rows = np.ones(len(df), dtype=bool)
    rh_emp, lev_emp, n_emp = block_excluded_mean(df, df.RH_obs.to_numpy(), lv1, rows)
    e["EMP_BIN_RH"] = rh_emp * esw(T)
    resid = df.RH_obs.to_numpy() - rh_c
    adj, lev_adj, n_adj = block_excluded_mean(df, resid, [("month", "dT_bin"), ("dT_bin",)], rows)
    e["EMP_ADJ_RH"] = (rh_c + adj) * esw(T)
    meta = {"companion_RH": rh_c, "EMP_BIN_RH_level": lev_emp, "EMP_BIN_RH_N": n_emp,
            "EMP_ADJ_RH_level": lev_adj, "EMP_ADJ_RH_N": n_adj}
    return e, meta


def metrics(err, n_sample):
    nv = int(np.isfinite(err).sum()); e = err[np.isfinite(err)]
    return {"N": int(n_sample), "N_valid": nv, "valid_fraction": nv / n_sample if n_sample else 0.0,
            "MAE_hPa": float(np.mean(np.abs(e))) if nv else np.nan,
            "bias_hPa": float(np.mean(e)) if nv else np.nan,
            "frac_abs_err_gt2hPa": float(np.mean(np.abs(e) > 2)) if nv else 1.0}


def gate(m):
    return (m["N"] >= GATE["N"] and m["valid_fraction"] >= GATE["FRAC"] and m["MAE_hPa"] <= GATE["MAE"]
            and abs(m["bias_hPa"]) <= GATE["BIAS"] and m["frac_abs_err_gt2hPa"] <= GATE["BAD2"])


def validate(df, e):
    T, P = df.TA_F.to_numpy(), df.P_Pa.to_numpy()
    truth = df.truth.to_numpy(); cold = truth & (T <= COLD_T)
    regime = truth & (np.abs(df.dT.to_numpy()) > REGIME_ABS_DT)
    yearly, verdict, tails, badruns, errors = [], [], [], [], {}
    for m in METHODS:
        ok = physical(T, P, e[m])
        vpd = np.where(ok, esw(T) - e[m], np.nan)
        err = vpd - df.VPD_F.to_numpy()
        errors[m] = np.where(truth, err, np.nan)
        passes = []
        for y in sorted(df.year.unique()):
            s = cold & (df.year.to_numpy() == y)
            r = metrics(err[s], s.sum()); r.update(method=m, year=int(y), sample="QC0_cold_T<=5")
            r["gate_pass"] = gate(r) if r["N"] >= GATE["N"] else None
            yearly.append(r)
            if r["gate_pass"] is not None: passes.append(r["gate_pass"])
        rg = metrics(err[regime], regime.sum()); rg_pass = gate(rg)
        allt = metrics(err[truth], truth.sum())
        verdict.append({"method": m, "gated_years": len(passes), "gated_years_pass": int(sum(passes)),
                        "REGIME_absdT_gt5_N": rg["N"], "REGIME_MAE_hPa": rg["MAE_hPa"], "REGIME_bias_hPa": rg["bias_hPa"],
                        "REGIME_frac_gt2hPa": rg["frac_abs_err_gt2hPa"], "REGIME_valid_fraction": rg["valid_fraction"],
                        "REGIME_pass": bool(rg_pass), "ALL_QC0_MAE_hPa": allt["MAE_hPa"],
                        "ALL_QC0_frac_gt2hPa": allt["frac_abs_err_gt2hPa"],
                        "METHOD_PASS": bool(len(passes) >= MIN_GATED_YEARS and all(passes) and rg_pass)})
        for col, lab in (("dT_bin", "dT"), ("T_bin", "tower_T"), ("month", "month")):
            for k, g in df.loc[truth].groupby(col):
                t = metrics(err[g.index.to_numpy()], len(g)); t.update(method=m, by=lab, bin=str(k)); tails.append(t)
        vb = cut(df.VPD_F, V_EDGES, V_LABELS)
        for k in V_LABELS:
            s = truth & (vb == k)
            t = metrics(err[s], s.sum()); t.update(method=m, by="measured_VPD_descriptive_only", bin=k); tails.append(t)
        big = truth & np.isfinite(err) & (np.abs(err) > 2)
        rr = runs(big)
        for st, ln in sorted(rr, key=lambda x: -x[1])[:15]:
            badruns.append({"method": m, "start": df.native_key.iloc[st], "length_HH": ln,
                            "max_abs_err_hPa": float(np.nanmax(np.abs(err[st:st + ln]))),
                            "dT_median": float(np.nanmedian(df.dT.to_numpy()[st:st + ln]))})
        verdict[-1]["QC0_bad_runs"] = len(rr); verdict[-1]["QC0_longest_bad_run_HH"] = max([x[1] for x in rr], default=0)
    return pd.DataFrame(yearly), pd.DataFrame(verdict), pd.DataFrame(tails), pd.DataFrame(badruns), errors


def census(df, gapmask, reasons, e):
    T, P = df.TA_F.to_numpy(), df.P_Pa.to_numpy()
    g = df.loc[gapmask].copy()
    g["Stage12g_reason"] = g.native_key.map(reasons).fillna("NOT_IN_STAGE12G_2810_LEDGER")
    rl = np.zeros(len(df), dtype=int)
    for st, ln in runs(gapmask): rl[st:st + ln] = ln
    g["gap_run_HH"] = rl[gapmask]
    truth = df.truth.to_numpy(); idx = np.flatnonzero(gapmask)
    before = np.array([truth[max(0, i - WINDOW_HH):i].any() for i in idx])
    after = np.array([truth[i + 1:i + 1 + WINDOW_HH].any() for i in idx])
    g["QC0_anchor_both_sides_2h"] = before & after
    for m in METHODS:
        g[m + "_formable"] = physical(T[gapmask], P[gapmask], e[m][gapmask])
    with np.errstate(invalid="ignore"):
        rw = e["COMPANION_RH"][gapmask] / esw(T[gapmask])
        g["COMPANION_RH_ice_supersat_only"] = (np.isfinite(rw) & (rw <= 1) & (T[gapmask] < 0)
                                              & (e["COMPANION_RH"][gapmask] > esi(T[gapmask])))
    g["gap_run_bin"] = pd.cut(g.gap_run_HH, [0, 4, 12, 48, 336, 10**7], labels=["1-4", "5-12", "13-48", "49-336", ">336"]).astype(str)
    tabs = {}
    for col in ("year", "Stage12g_reason", "TA_F_QC", "VPD_F_QC", "dT_bin", "T_bin", "month", "hour", "gap_run_bin"):
        agg = {"N": ("native_key", "size"), "anchors_2h": ("QC0_anchor_both_sides_2h", "sum"),
               "ice_only_COMPANION_RH": ("COMPANION_RH_ice_supersat_only", "sum")}
        agg.update({m + "_formable": (m + "_formable", "sum") for m in METHODS})
        t = g.groupby(col, dropna=False).agg(**agg).reset_index().rename(columns={col: "bin"})
        t.insert(0, "by", col); tabs[col] = t
    return g, pd.concat(tabs.values(), ignore_index=True)


def regime_truth(df):
    t = df.loc[df.truth].groupby(["year", "dT_bin"]).size().unstack(fill_value=0)
    return t.reindex(columns=[c for c in DT_LABELS if c in t.columns]).reset_index()


def temperature_plausibility(df):
    yr = []
    for y, g in df.groupby("year"):
        yr.append({"year": int(y), "TA_F_min": float(np.nanmin(g.TA_F)), "TA_F_p001": float(np.nanpercentile(g.TA_F, 0.1)),
                   "TA_ERA_min": float(np.nanmin(g.TA_ERA)), "N_lt_-20": int((g.TA_F < -20).sum()),
                   "N_lt_-25": int((g.TA_F < -25).sum()), "N_lt_-30": int((g.TA_F < -30).sum()),
                   "N_lt_-25_QC0": int(((g.TA_F < -25) & (g.TA_F_QC == 0)).sum()),
                   "N_dT_lt_-8": int((g.dT < -8).sum()), "N_dT_gt_8": int((g.dT > 8).sum())})
    ep = []
    for st, ln in runs((df.TA_F < EXTREME_COLD).to_numpy()):
        s = df.iloc[st:st + ln]
        ep.append({"start": s.native_key.iloc[0], "end": s.native_key.iloc[-1], "length_HH": ln,
                   "TA_F_min": float(s.TA_F.min()), "TA_ERA_mean": float(s.TA_ERA.mean()),
                   "TA_F_QC_values": ",".join(sorted({str(int(x)) for x in s.TA_F_QC.dropna()})),
                   "start_row": st})
    return pd.DataFrame(yr), pd.DataFrame(ep)


def context(df, e, gapmask, reasons, land, windows):
    rows = []
    T, P = df.TA_F.to_numpy(), df.P_Pa.to_numpy()
    for label, c0, c1 in windows:
        for i in range(max(0, c0 - WINDOW_HH), min(len(df), c1 + WINDOW_HH + 1)):
            r = df.iloc[i]
            d = {"window": label, "native_key": r.native_key, "in_gap": bool(gapmask[i]),
                 "Stage12g_reason": reasons.get(r.native_key, "") if gapmask[i] else "",
                 "TA_F_C": r.TA_F, "TA_F_QC": r.TA_F_QC, "TA_class": QC_CLASS.get(int(r.TA_F_QC), "unknown") if np.isfinite(r.TA_F_QC) else "unknown",
                 "VPD_F_hPa": r.VPD_F, "VPD_F_QC": r.VPD_F_QC,
                 "VPD_class": QC_CLASS.get(int(r.VPD_F_QC), "unknown") if np.isfinite(r.VPD_F_QC) else "unknown",
                 "PA_F_Pa": r.P_Pa, "TA_ERA_C_companion": r.TA_ERA, "VPD_ERA_hPa_companion": r.VPD_ERA,
                 "PA_ERA_kPa_companion": r.PA_ERA, "dT_C": r.dT}
            for k in ("ERA5Land_T2m_C", "ERA5Land_D2m_C", "ERA5Land_SP_Pa"):
                d[k + "_external"] = land.get(r.native_key, {}).get(k, np.nan)
            eo = esw(T[i]) - r.VPD_F
            d["orig_RH_water_pct_computed"] = 100 * eo / esw(T[i]) if np.isfinite(eo) else np.nan
            d["orig_RH_ice_pct_computed"] = 100 * eo / esi(T[i]) if np.isfinite(eo) and T[i] < 0 else np.nan
            cand = dict(e)
            if np.isfinite(d["ERA5Land_T2m_C_external"]):
                cand = {**e, "GRID_RH": None}
            for m, arr in cand.items():
                if m == "GRID_RH":
                    ev = esw(d["ERA5Land_D2m_C_external"]) / esw(d["ERA5Land_T2m_C_external"]) * esw(T[i])
                else:
                    ev = arr[i]
                d[m + "_RH_water_pct"] = 100 * ev / esw(T[i]) if np.isfinite(ev) else np.nan
                d[m + "_RH_ice_pct"] = 100 * ev / esi(T[i]) if np.isfinite(ev) and T[i] < 0 else np.nan
                d[m + "_VPD_hPa"] = esw(T[i]) - ev if np.isfinite(ev) else np.nan
                d[m + "_QBOT_kgkg"] = float(q_from_e(ev, P[i])) if np.isfinite(ev) else np.nan
                d[m + "_passes_physical_incl_ice"] = bool(physical(np.array([T[i]]), np.array([P[i]]), np.array([ev]))[0]) if np.isfinite(ev) else False
            rows.append(d)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------- HPC inputs
def upstream():
    if gitblob(J_SCRIPT) != J_BLOB: raise ValueError("Pinned Stage12j Git blob mismatch (update the clone): " + str(J_SCRIPT))
    spec = importlib.util.spec_from_file_location("stage12j_for_mtb01", J_SCRIPT)
    j = importlib.util.module_from_spec(spec); spec.loader.exec_module(j)
    h, src, specinfo, catalog, held, original_1038 = j.upstream()
    return j, src, specinfo, catalog, held


def load_inputs():
    j, src, spec, catalog, held = upstream()
    hdr = set(pd.read_csv(regular(spec["primary"]), nrows=0).columns)
    want = ["TIMESTAMP_START", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "PA_F"] + [c for c in ("WS_F", "SW_IN_F", "LW_IN_F") if c in hdr]
    flux = pd.read_csv(regular(spec["primary"]), usecols=want, dtype={"TIMESTAMP_START": str}, low_memory=False)
    era = pd.read_csv(regular(spec["era"]), usecols=["TIMESTAMP_START", "TA_ERA", "VPD_ERA", "PA_ERA"],
                      dtype={"TIMESTAMP_START": str}, low_memory=False)
    df = frame_from(flux, era)
    g = pd.read_csv(regular(j.G / "US-MtB_STAGE12G_INCOMPLETE_NOLEAP.csv"), low_memory=False)
    gk = pd.to_datetime(g.time, format="%Y-%m-%d %H:%M:%S", errors="raise").dt.strftime("%Y%m%d%H%M")
    if len(g) != len(df) or not np.array_equal(gk.to_numpy(), df.native_key.to_numpy()):
        raise ValueError("Stage12g timeline differs from the original native clock")
    if not np.allclose(g.TA_USE.to_numpy(float), df.TA_F.to_numpy(), atol=1e-6, rtol=0, equal_nan=True):
        raise ValueError("Stage12g TA_USE differs from original TA_F")
    gap = (~np.isfinite(g.QBOT.to_numpy(float))) | (~np.isfinite(g.VPD_USE.to_numpy(float)))
    led = pd.read_csv(regular(j.G / "2810_original_missing_year_source_review_after_stage12g.csv"),
                      dtype={"site": str, "native_key": str}, low_memory=False)
    reasons = dict(led.loc[led.site.eq(SITE), ["native_key", "reason"]].itertuples(index=False, name=None))
    land, era5l = {}, []
    for (site, year), (plan, meta) in sorted(catalog.items()):
        loc = plan["request"]["location"]
        hours, field, coord = src.grid_fields(regular(meta["path"]), year, (loc["latitude"], loc["longitude"]))
        sel = (df.year == year).to_numpy()
        utc = (df.stamp[sel] + pd.Timedelta(minutes=int(spec["native_minutes"]) / 2)
               - pd.Timedelta(hours=src.BIF_OFFSET[SITE]))
        t2 = src.interpolate(hours, field["t2m"], utc) - 273.15
        d2 = src.interpolate(hours, field["d2m"], utc) - 273.15
        sp = src.interpolate(hours, field["sp"], utc)
        for k, a, b, c in zip(df.native_key[sel], t2, d2, sp):
            land[k] = {"ERA5Land_T2m_C": a, "ERA5Land_D2m_C": b, "ERA5Land_SP_Pa": c}
        era5l.append({"year": year, "file": str(meta["path"]), "sha256": meta["sha256"], "grid_lat": coord[0],
                      "grid_lon": coord[1], "variables": ";".join(nc_variables(meta["path"])),
                      "has_geopotential": "z" in nc_variables(meta["path"])})
    info = {"primary": str(spec["primary"]), "primary_sha256": sha(spec["primary"]), "era": str(spec["era"]),
            "era_sha256": sha(spec["era"]), "native_minutes": int(spec["native_minutes"]),
            "BIF_UTC_offset_h": float(src.BIF_OFFSET[SITE]), "Stage12g": str(j.G),
            "Stage12g_timeline_sha256": sha(j.G / "US-MtB_STAGE12G_INCOMPLETE_NOLEAP.csv"),
            "Stage12j_blob": J_BLOB, "stage12j_held_1035": int(len(held))}
    return df, gap, reasons, land, pd.DataFrame(era5l), info


def nc_variables(path):
    from netCDF4 import Dataset
    path = Path(path); names = set()
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for m in z.infolist():
                if m.filename.endswith(".nc"):
                    with Dataset("m.nc", "r", memory=z.read(m)) as ds: names |= set(ds.variables)
    else:
        with Dataset(str(path)) as ds: names |= set(ds.variables)
    return sorted(names)


def code_evidence():
    lines = []
    for sub in ("", "components/cdeps"):
        p = CTSM / sub if sub else CTSM
        try:
            head = subprocess.run(["git", "-C", str(p), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip()
            desc = subprocess.run(["git", "-C", str(p), "describe", "--tags", "--always"], capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception as ex:
            head, desc = "unavailable", str(ex)
        lines.append(f"# git {p}: HEAD={head} describe={desc}")
    found = {}
    for root in (CTSM / "components/cdeps", CTSM / "src"):
        if root.is_dir():
            for name in CODE_FILES:
                for p in root.rglob(name):
                    found.setdefault(name, []).append(p)
    for name in CODE_FILES:
        for p in found.get(name, []):
            lines.append(f"\n## {p}  sha256={sha(p)}")
            hits = [(i, l.rstrip()) for i, l in enumerate(p.read_text(errors="replace").splitlines(), 1) if CODE_RE.search(l)]
            lines += [f"{i:6d}: {l}" for i, l in hits[:120]]
            if len(hits) > 120: lines.append(f"... {len(hits) - 120} more matching lines")
        if name not in found: lines.append(f"\n## {name}: NOT FOUND under {CTSM}")
    return "\n".join(lines) + "\n"


def compute(df, gap, reasons, land):
    e, meta = candidates(df)
    yearly, verdict, tails, badruns, errors = validate(df, e)
    g, ctab = census(df, gap, reasons, e)
    truth_tab = regime_truth(df)
    yrT, cold_ep = temperature_plausibility(df)
    pos = {k: i for i, k in enumerate(df.native_key)}
    windows = []
    ice = [pos[k] for k in ICE_EVENTS if k in pos]
    if ice: windows.append(("2024-02-11_frozen_phase", min(ice), max(ice)))
    for r in cold_ep.head(10).itertuples():
        windows.append((f"cold_episode_{r.start}", int(r.start_row), int(r.start_row) + int(r.length_HH) - 1))
    ctx = context(df, e, gap, reasons, land, windows)
    gapcols = ["native_key", "year", "month", "hour", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "PA_F", "TA_ERA", "VPD_ERA",
               "dT", "dT_bin", "Stage12g_reason", "gap_run_HH", "QC0_anchor_both_sides_2h", "COMPANION_RH_ice_supersat_only"] + \
              [m + "_formable" for m in METHODS]
    return dict(yearly=yearly, verdict=verdict, tails=tails, badruns=badruns, census=ctab, gaps=g[gapcols],
                truth=truth_tab, yearT=yrT, cold=cold_ep.drop(columns=["start_row"]) if len(cold_ep) else cold_ep, context=ctx)


def show(res, gap, info, era5l):
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    print("\n=== INPUTS ===\n" + json.dumps(info, indent=1))
    print(f"\n=== A  US-MtB humidity gaps in Stage12g timeline: {int(gap.sum())} ===")
    c = res["census"]
    for by in ("year", "Stage12g_reason", "VPD_F_QC", "TA_F_QC", "dT_bin", "gap_run_bin"):
        print(c.loc[c.by.eq(by)].drop(columns="by").to_string(index=False))
    print("\n=== B  measured truth (VPD_F_QC=0 & TA_F_QC=0) per year x dT=TA_F-TA_ERA bin ===")
    print(res["truth"].to_string(index=False))
    print("\n=== C  method verdicts (predeclared gates; no repair) ===")
    print(res["verdict"].to_string(index=False))
    t = res["tails"]
    print("\n--- error by dT bin (all QC0) ---")
    print(t.loc[t.by.eq("dT"), ["method", "bin", "N", "N_valid", "MAE_hPa", "bias_hPa", "frac_abs_err_gt2hPa"]].to_string(index=False))
    print("\n=== D  temperature plausibility ===")
    print(res["yearT"].to_string(index=False))
    print(f"extreme-cold episodes (TA_F < {EXTREME_COLD} C): {len(res['cold'])}")
    if len(res["cold"]): print(res["cold"].head(10).to_string(index=False))
    print("\n=== E  context rows:", len(res["context"]), "(frozen-phase window + first cold episodes) ===")
    ice = res["context"].loc[res["context"].window.eq("2024-02-11_frozen_phase") & res["context"].in_gap]
    cols = [c for c in ("native_key", "TA_F_C", "PA_F_Pa", "TA_ERA_C_companion", "ERA5Land_T2m_C_external",
                        "COMPANION_RH_RH_water_pct", "COMPANION_RH_RH_ice_pct", "GRID_RH_RH_water_pct", "GRID_RH_RH_ice_pct",
                        "GRID_RH_QBOT_kgkg") if c in ice]
    if len(ice): print(ice[cols].to_string(index=False))
    print("\n=== G  ERA5-Land evidence files ===")
    print(era5l.to_string(index=False))


def self_test():
    n = 24 * 2 * 365 * 3
    ts = pd.date_range("2020-01-01", periods=n, freq="30min")
    ts = ts[~((ts.month == 2) & (ts.day == 29))]
    rng = np.random.default_rng(1); n = len(ts)
    T = 5 + 10 * np.sin(np.arange(n) / 48 * 2 * np.pi) + rng.normal(0, 2, n)
    Te = T + rng.normal(2, 3, n); rh = np.clip(rng.uniform(.2, .9, n), .05, .95)
    flux = pd.DataFrame({"TIMESTAMP_START": ts.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0,
                         "VPD_F": esw(T) * (1 - rh), "VPD_F_QC": np.where(rng.uniform(size=n) < .1, 2, 0), "PA_F": 74.5})
    era = pd.DataFrame({"TIMESTAMP_START": flux.TIMESTAMP_START, "TA_ERA": Te, "VPD_ERA": esw(Te) * (1 - rh), "PA_ERA": 84.5})
    df = frame_from(flux, era)
    e, meta = candidates(df)
    ok = np.isfinite(e["COMPANION_RH"]) & df.truth.to_numpy()
    assert np.allclose(e["COMPANION_RH"][ok] / esw(df.TA_F.to_numpy()[ok]), rh[ok], atol=1e-9), "companion RH formula"
    # block exclusion: a single-row block must not see itself
    tiny = df.iloc[:200].copy(); v = np.full(len(tiny), np.nan); v[0] = 9.0
    p, lev, nn = block_excluded_mean(tiny, v, [("dT_bin",)], np.ones(len(tiny), bool))
    assert np.isnan(p[0]), "block exclusion leak"
    yearly, verdict, tails, badruns, _ = validate(df, e)
    assert set(verdict.method) == set(METHODS) and len(yearly) == 4 * 3
    gap = (df.VPD_F_QC == 2).to_numpy()
    g, ctab = census(df, gap, {}, e)
    assert len(g) == int(gap.sum()) and (ctab.loc[ctab.by.eq("year"), "N"].sum() == gap.sum())
    assert esi(-10) < esw(-10) and 100 * 0.95 * esw(-10) / esi(-10) > 100, "ice supersaturation at RH_w 95% / -10 C"
    assert runs(np.array([0, 1, 1, 0, 1], bool)) == [(1, 2), (4, 1)]
    print("MtB01 SELF-TEST PASS: companion formula, block-excluded empirical means, gates, census, ice algebra; no file access")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    a = ap.parse_args()
    print("MtB01 US-MtB REGIME-MATCHED QC0 HUMIDITY EVIDENCE | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    df, gap, reasons, land, era5l, info = load_inputs()
    res = compute(df, gap, reasons, land)
    code = code_evidence()
    show(res, gap, info, era5l)
    print("\n=== F  installed model humidity code (first lines) ===\n" + "\n".join(code.splitlines()[:40]))
    print("\nMtB01 SUMMARY: read-only; methods passing all predeclared gates:",
          ",".join(res["verdict"].loc[res["verdict"].METHOD_PASS, "method"]) or "NONE",
          "| repairs written 0 | Post-v5 0 | DATM 0 | spinup 0", flush=True)
    if a.check:
        print("MtB01 CHECK ONLY: no files written.", flush=True); return
    out = ROOT / "reports" / ("mtb01_US-MtB_regime_matched_QC0_humidity_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"A_gap_census_tables.csv": res["census"], "A_all_gap_rows.csv": res["gaps"],
             "B_QC0_truth_by_year_dT.csv": res["truth"], "C_method_yearly_QC0_cold.csv": res["yearly"],
             "C_method_verdicts.csv": res["verdict"], "C_error_tails.csv": res["tails"],
             "C_longest_QC0_bad_runs.csv": res["badruns"], "D_yearly_temperature_extremes.csv": res["yearT"],
             "D_extreme_cold_episodes.csv": res["cold"], "E_context_pm2h.csv": res["context"],
             "G_ERA5Land_evidence_files.csv": era5l}
    for k, d in files.items(): d.to_csv(out / k, index=False)
    (out / "F_installed_model_humidity_code.txt").write_text(code)
    (out / "SCIENTIFIC_HOLD.md").write_text(
        "MtB01 is read-only evidence. No candidate here is a repair or an approval. Validation truth is original "
        "VPD_F_QC=0 & TA_F_QC=0 only; empirical methods exclude the predicted time's 10-day block. Gates were fixed in "
        "the script before results. Original TA_F (QC0) is never replaced; Post-v5/DATM/spinup remain 0.\n")
    names = [*files, "F_installed_model_humidity_code.txt", "SCIENTIFIC_HOLD.md"]
    receipt = {"version": VERSION, "inputs": info, "gaps": int(gap.sum()),
               "methods_passing": res["verdict"].loc[res["verdict"].METHOD_PASS, "method"].tolist(),
               "gates": GATE, "regime_abs_dT_C": REGIME_ABS_DT, "min_gated_years": MIN_GATED_YEARS,
               "repairs_written": 0, "Postv5_approved": 0, "DATM_ready": 0, "spinup_authorized": 0,
               "output_sha256": {n: sha(out / n) for n in names}}
    (out / "mtb01_receipt.json").write_text(json.dumps(receipt, indent=2, default=str) + "\n")
    print("MtB01 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("MtB01 STOP:", exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

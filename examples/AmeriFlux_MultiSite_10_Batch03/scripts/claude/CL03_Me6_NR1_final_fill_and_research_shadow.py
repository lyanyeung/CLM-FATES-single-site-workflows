#!/usr/bin/env python3
"""CL03 (Claude, US-Me6 / US-NR1): the last evidence step plus the RESEARCH SHADOW, applying the
user decisions of 2026-10-29 ("按照你的建议搞"; NR1 forcing starts 1999; the 23 HOLD as proposed).

Rules, fixed before the first run:
 0 NR1 FORCING START 1999-01-01. Jan-Oct 1998 is 100 % ERA-filled (TA/VPD/SW/LW QC 2, no BASE);
   every 1998 row is removed from the NR1 shadow; its gaps are DROPPED, not filled.
 1 SOURCE QC0 RESTORED. A gap row whose own FLUXMET TA_F and VPD_F are both QC0 and physical at
   the shadow PSRF keeps its measured VPD_F (the user rule: never silently change source QC0).
   Expected exactly NR1 2004-12-03 22:30/23:00/23:30 (corrupt companion ERA: TA_ERA -112/-217 C,
   PA -8/31 kPa); any other set STOPS the run.
 2 CL02 predeclared recommendation (pinned CL02 v1): MEASURED BASE level transfer, EMP
   (block-excluded QC0 RH climatology) or CEC (COMPANION_E capped at DATM saturation).
 3 CL02 HOLD -> INTERP when formable and validated, else CEC_LOW_CONFIDENCE.
   INTERP: vapour pressure e interpolated linearly in time between the nearest anchor before and
   after the gap (anchor = QC0 truth row whose shadow values equal the source), each at most 4 HH
   from the gap edge; gap <= 3 HH; e capped at DATM saturation; VPD at the row's own temperature.
   Validation on QC0 truth by pseudo-gaps: every truth row is predicted with itself and its two
   neighbours removed (a 3-HH gap, the longest real HOLD gap, row in the middle = hardest case)
   using the same anchor rule; Stage12j five gates per tower-T bin (bin N >= 100) and pooled; the
   1-HH pseudo-gap is reported for information only. A HOLD row uses INTERP only when the 3-HH
   validation passes in its T bin.
 Rows whose tower TA_F is ERA-filled are labelled +T_REANALYSIS. Temperature is never changed.
 VPD_USE = esw(TA_USE) - e, QBOT = 0.622 e / (PSRF - 0.378 e): the shadow's own closure, proven on
 its existing rows first (rtol 1e-8; TBOT = TA_USE + 273.15). A new QBOT at most 1 % above the DATM
 saturation (Magnus vs Flatau) is set to it and listed; more stops the run. Every non-gap row and
 every other column must be bit-identical to the approved input shadow (so all previously
 approved edits survive); NR1 Stage12AF 2022-09-10 TA values are additionally checked by value.

--self-test synthetic; --check computes and prints everything, NO writes; --run writes ONE new
science_trials/cl03_<site>_research_shadow_* folder with the INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP
marker. Original FLUXMET/ERA/BASE files and the input shadows are only read.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-CL03-v1-20261029-Me6-NR1-final-fill-research-shadow"
HERE = Path(__file__).resolve().parent
K_SCRIPT = HERE / "CL02.py" if (HERE / "CL02.py").is_file() else HERE / "CL02_Me6_NR1_alternatives_validated_decision_table_READONLY.py"
K_BLOB = "5af937a6bb7b1f427220d8e9f70ffd50a010f1c2"
TKFRZ = 273.15
CAP_REL = 0.01
W_ANCHOR = 4
MAX_INTERP_GAP = 3
START_YEAR = {"US-NR1": 1999}
EXPECT_RESTORE = {"US-NR1": {"200412032230", "200412032300", "200412032330"}, "US-Me6": set()}
APPROVED_TA = {"US-NR1": {"202209100630": 1.241, "202209100730": 1.556666667, "202209100800": 1.393333333}}


def load_k():
    b = K_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != K_BLOB:
        raise ValueError("Pinned CL02 v1 Git blob mismatch: " + str(K_SCRIPT))
    spec = importlib.util.spec_from_file_location("cl02_for_cl03", K_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


K = load_k()
C, M = K.C, K.M
sat = K.esat_datm


def last_idx(mask):
    n = len(mask); return np.maximum.accumulate(np.where(mask, np.arange(n), -1))


def next_idx(mask):
    n = len(mask); return np.minimum.accumulate(np.where(mask, np.arange(n), n)[::-1])[::-1]


def interp(e_anchor, anchor, lo, hi, i, T):
    """e at rows i inside gaps [lo, hi]; NaN when no anchor within W_ANCHOR HH on either side."""
    n = len(anchor); la, na = last_idx(anchor), next_idx(anchor)
    lo, hi, i = np.asarray(lo), np.asarray(hi), np.asarray(i)
    inside = (lo >= 1) & (hi <= n - 2)
    a = np.where(inside, la[np.clip(lo - 1, 0, n - 1)], -1); b = np.where(inside, na[np.clip(hi + 1, 0, n - 1)], n)
    ok = inside & (a >= 0) & (b < n) & (a >= lo - W_ANCHOR) & (b <= hi + W_ANCHOR)
    ac, bc = np.clip(a, 0, n - 1), np.clip(b, 0, n - 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        e = e_anchor[ac] + (e_anchor[bc] - e_anchor[ac]) * (i - ac) / (bc - ac)
    e = np.where(ok & np.isfinite(e) & (e > 0), np.minimum(e, sat(T)), np.nan)
    return e, a, b


def interp_validate(df):
    T = df.TA_F.to_numpy(float); V = df.VPD_F.to_numpy(float); truth = df.truth.to_numpy()
    e_obs = np.where(truth, M.esw(T) - V, np.nan); tb = M.cut(T, M.T_EDGES, M.T_LABELS)
    summ, bins = [], []
    for h in (1, 0):
        i = np.flatnonzero(truth); e, _, _ = interp(e_obs, truth, i - h, i + h, i, T[i])
        err = np.full(len(df), np.nan); err[i] = (M.esw(T[i]) - e) - V[i]
        tag = f"INTERP_{2 * h + 1}HH"; passes = []
        for y in sorted(df.year.unique()):
            s = truth & (df.year.to_numpy() == y)
            if s.sum() >= 50: passes.append(M.gate(M.metrics(err[s], s.sum())))
        p = M.metrics(err[truth], truth.sum())
        summ.append({"method": tag, "N": p["N"], "valid_fraction": p["valid_fraction"], "MAE_hPa": p["MAE_hPa"], "bias_hPa": p["bias_hPa"],
                     "frac_gt2hPa": p["frac_abs_err_gt2hPa"], "pooled_pass": bool(M.gate(p)), "years_pass": f"{sum(passes)}/{len(passes)}"})
        for b in M.T_LABELS:
            s = truth & (tb == b); r = M.metrics(err[s], s.sum()); r.update(method=tag, T_bin=b)
            r["bin_pass"] = bool(r["N"] >= K.BIN_MIN and M.gate(r)); bins.append(r)
    return pd.DataFrame(summ), pd.DataFrame(bins)


def decide(site, df, res, alt, D, ib):
    pos = {k: i for i, k in enumerate(df.native_key)}
    led = res["ledger"].set_index("native_key")
    n = len(df); gap = (~np.isfinite(df.S_VPD_USE.to_numpy(float))) | (~np.isfinite(df.S_QBOT.to_numpy(float)))
    lo = np.zeros(n, int); hi = np.zeros(n, int)
    for s, ln in M.runs(gap): lo[s:s + ln] = s; hi[s:s + ln] = s + ln - 1
    T = alt["T"]; P = df.S_PSRF.to_numpy(float)
    truth = df.truth.to_numpy()
    agree = (np.abs(df.S_TA_USE.to_numpy(float) - df.TA_F.to_numpy(float)) < 1e-6) & (np.abs(df.S_VPD_USE.to_numpy(float) - df.VPD_F.to_numpy(float)) < 1e-6)
    anchor = truth & agree
    e_anchor = np.where(anchor, M.esw(df.S_TA_USE.to_numpy(float)) - df.S_VPD_USE.to_numpy(float), np.nan)
    ipass = ib.loc[ib.method == "INTERP_3HH"].set_index("T_bin").bin_pass.to_dict()
    start = START_YEAR.get(site)
    rows, restored = [], set()
    gi = np.array([pos[k] for k in D.native_key], int)
    EI, AI, BI = interp(e_anchor, anchor, lo[gi], hi[gi], gi, T[gi])
    for j, r in enumerate(D.to_dict("records")):
        k = r["native_key"]; i = pos[k]; t = T[i]
        x = {"native_key": k, "year": r["year"], "episode": r["episode"], "gap_HH": int(hi[i] - lo[i] + 1), "TA_USE_C": t, "T_bin": r["T_bin"],
             "PSRF_Pa": P[i], "CL01_class": r["CL01_class"], "CL02_recommended": r["recommended"],
             "CEC_VPD_hPa": r["CEC_VPD_hPa"], "EMP_VPD_hPa": r["EMP_VPD_hPa"], "SAT_VPD_hPa": r["SAT_VPD_hPa"]}
        ei, a, b = EI[j:j + 1], AI[j:j + 1], BI[j:j + 1]
        x["INTERP_VPD_hPa"] = M.esw(t) - ei[0] if np.isfinite(ei[0]) else np.nan
        x["INTERP_anchors"] = f"{df.native_key.iloc[a[0]]}/{df.native_key.iloc[b[0]]}" if np.isfinite(ei[0]) else ""
        x["INTERP_bin_pass_3HH"] = bool(ipass.get(r["T_bin"], False))
        vf = float(df.VPD_F.iloc[i]); e_src = M.esw(t) - vf if np.isfinite(vf) else np.nan
        src_ok = (df.TA_F_QC.iloc[i] == 0 and df.VPD_F_QC.iloc[i] == 0 and np.isfinite(e_src) and vf >= 0
                  and abs(t - df.TA_F.iloc[i]) < 1e-9 and bool(M.physical(np.array([t]), np.array([P[i]]), np.array([e_src]))[0]))
        if start and r["year"] < start:
            src, e = f"DROPPED_BEFORE_FORCING_START_{start}", np.nan
        elif src_ok:
            src, e = "SOURCE_QC0_VPD_F_RESTORED", e_src; restored.add(k)
        elif r["recommended"].startswith("MEASURED:"):
            m = r["recommended"].split(":", 1)[1]; src, e = "MEASURED_" + m, float(led.loc[k, "e_" + m])
        elif r["recommended"] in ("EMP", "CEC"):
            src, e = r["recommended"], alt[r["recommended"]][i]
        elif r["recommended"] == "HOLD_NO_VALIDATED_METHOD":
            if np.isfinite(ei[0]) and x["gap_HH"] <= MAX_INTERP_GAP and x["INTERP_bin_pass_3HH"]:
                src, e = "INTERP", ei[0]
            elif np.isfinite(alt["CEC"][i]):
                src, e = "CEC_LOW_CONFIDENCE", alt["CEC"][i]
            else:
                raise ValueError("HOLD row without INTERP or CEC: " + k)
        else:
            raise ValueError(f"unexpected CL02 recommendation {r['recommended']} at {k}")
        if not src.startswith("DROPPED") and df.TA_F_QC.iloc[i] == 2: src += "+T_REANALYSIS"
        if not src.startswith("DROPPED") and not (np.isfinite(e) and e > 0): raise ValueError("no positive vapour pressure for " + k)
        x["final_source"] = src; x["e_hPa"] = e; x["final_VPD_hPa"] = M.esw(t) - e if np.isfinite(e) else np.nan
        rows.append(x)
    exp = EXPECT_RESTORE.get(site, set())
    if restored != exp: raise ValueError(f"source-QC0 restore set {sorted(restored)} differs from the approved {sorted(exp)}")
    return pd.DataFrame(rows)


def check_conventions(s):
    T, P = s.TA_USE.to_numpy(float), s.PSRF.to_numpy(float); V, Q = s.VPD_USE.to_numpy(float), s.QBOT.to_numpy(float)
    nT = 0
    if "TBOT" in s:
        TB = s.TBOT.to_numpy(float); f = np.isfinite(T) & np.isfinite(TB); nT = int(f.sum())
        if not np.allclose(TB[f], T[f] + TKFRZ, rtol=0, atol=1e-6): raise ValueError("shadow TBOT != TA_USE + 273.15")
    h = np.isfinite(V) & np.isfinite(Q) & np.isfinite(T) & np.isfinite(P)
    if not np.allclose(M.q_from_e(M.esw(T[h]) - V[h], P[h]), Q[h], rtol=1e-8, atol=1e-10):
        raise ValueError("shadow QBOT closure differs from 0.622e/(p-0.378e) with Magnus esw")
    return nT, int(h.sum())


def build(site, s, df, F):
    out = s.copy(); pos = {k: i for i, k in enumerate(df.native_key)}
    T, P = out.TA_USE.to_numpy(float), out.PSRF.to_numpy(float)
    V, Q = out.VPD_USE.to_numpy(float).copy(), out.QBOT.to_numpy(float).copy()
    pmed = np.nanmedian(P); fill = F.loc[~F.final_source.str.startswith("DROPPED")]
    idx = np.array([pos[k] for k in fill.native_key], int); e = fill.e_hPa.to_numpy(float); src = fill.final_source.to_numpy(object).copy()
    if not (np.isfinite(T[idx]).all() and np.isfinite(P[idx]).all()): raise ValueError("gap row without TA_USE or PSRF")
    if ((P[idx] < 0.85 * pmed) | (P[idx] > 1.15 * pmed)).any(): raise ValueError("implausible PSRF at a gap row")
    qn = M.q_from_e(e, P[idx]); qs = M.q_from_e(sat(T[idx]), P[idx]); rel = qn / qs - 1.0
    if (rel > CAP_REL).any(): raise ValueError(f"{int((rel > CAP_REL).sum())} new QBOT more than {CAP_REL:.0%} above DATM saturation")
    capped = []
    for j in np.flatnonzero(rel > 1e-12):
        capped.append(dict(native_key=fill.native_key.iloc[j], source=src[j], TA_C=T[idx[j]], excess_pct=100 * rel[j]))
        e[j] = sat(T[idx[j]]); src[j] = src[j] + "+CAPPED_TO_DATM_SAT"
    V[idx] = M.esw(T[idx]) - e; Q[idx] = M.q_from_e(e, P[idx])
    out["VPD_USE"] = V; out["QBOT"] = Q
    touched = np.zeros(len(out), bool); touched[idx] = True
    for c in out.columns:
        if c in ("VPD_USE", "QBOT"):
            a, b = s[c].to_numpy(), out[c].to_numpy(); same = (a == b) | (pd.isna(a) & pd.isna(b))
            if not same[~touched].all(): raise ValueError("untouched row changed in " + c)
        elif not s[c].equals(out[c]): raise ValueError("column changed that must not change: " + c)
    prov = pd.DataFrame({"native_key": fill.native_key.to_numpy(), "field": "VPD_USE/QBOT", "old_VPD": s.VPD_USE.to_numpy(float)[idx],
                         "old_QBOT": s.QBOT.to_numpy(float)[idx], "new_VPD": V[idx], "new_QBOT": Q[idx], "source": src})
    keep = np.ones(len(out), bool); start = START_YEAR.get(site)
    if start: keep = df.year.to_numpy() >= start
    out = out.loc[keep].reset_index(drop=True)
    for k, v in APPROVED_TA.get(site, {}).items():
        j = np.flatnonzero(df.native_key.to_numpy()[keep] == k)
        if len(j) != 1 or abs(out.TA_USE.iloc[j[0]] - v) > 1e-6: raise ValueError("approved TA edit not preserved at " + k)
    nan = {c: int(out[c].isna().sum()) for c in out.columns if c != "time"}
    counts = pd.Series(src).value_counts().rename_axis("source").rename("HH").reset_index()
    return out, prov, counts, nan, pd.DataFrame(capped), int((~keep).sum())


def self_test():
    n = 48 * 365 * 3
    ts = pd.date_range("2014-01-01", periods=n, freq="30min"); ts = ts[~((ts.month == 2) & (ts.day == 29))]; n = len(ts)
    rng = np.random.default_rng(3)
    T = 5 + 12 * np.sin(np.arange(n) / 48 * 2 * np.pi) + rng.normal(0, .5, n)
    e = np.clip(0.6 + 0.05 * np.sin(np.arange(n) / 300), .1, .95) * M.esw(T)
    flux = pd.DataFrame({"TIMESTAMP_START": ts.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0, "VPD_F": M.esw(T) - e, "VPD_F_QC": 0, "PA_F": 85.0})
    era = pd.DataFrame({"TIMESTAMP_START": flux.TIMESTAMP_START, "TA_ERA": T + 1, "VPD_ERA": M.esw(T + 1) - e, "PA_ERA": 85.0})
    gaps = [100, 101, 30000, 40000, 40001, 40002]; flux.loc[[100, 101, 40000, 40001, 40002], "VPD_F_QC"] = 1; flux.loc[30000, "PA_F"] = 30.0
    df = M.frame_from(flux, era)
    s = pd.DataFrame({"time": ts.strftime("%Y-%m-%d %H:%M:%S"), "TBOT": T + TKFRZ, "QBOT": M.q_from_e(e, 85000.0), "PSRF": 85000.0,
                      "FSDS": 0.0, "TA_USE": T, "VPD_USE": M.esw(T) - e})
    s.loc[gaps, ["VPD_USE", "QBOT"]] = np.nan
    for c in ("TA_USE", "VPD_USE", "QBOT", "PSRF"): df["S_" + c] = s[c].to_numpy(float)
    C.SITES["TEST"] = dict(missing=len(gaps)); START_YEAR["TEST"] = 2015
    EXPECT_RESTORE["TEST"] = {df.native_key[30000]}
    try:
        check_conventions(s)
        res, vs, vb, D = K.compute("TEST", df, dict(ta=[], rh=[], h2o=[]))
        D.loc[D.native_key == df.native_key[40001], "recommended"] = "HOLD_NO_VALIDATED_METHOD"
        alt = K.alternatives(df); isumm, ib = interp_validate(df)
        assert isumm.set_index("method").loc["INTERP_3HH", "pooled_pass"], isumm
        F = decide("TEST", df, res, alt, D, ib)
        f = F.set_index("native_key")
        assert f.loc[df.native_key[100], "final_source"].startswith("DROPPED")
        assert f.loc[df.native_key[40001], "final_source"] == "INTERP" and f.loc[df.native_key[30000], "final_source"] == "SOURCE_QC0_VPD_F_RESTORED"
        assert abs(f.loc[df.native_key[40001], "final_VPD_hPa"] - df.VPD_F[40001]) < 1.0
        out, prov, counts, nan, cap, dropped = build("TEST", s, df, F)
        assert dropped == 17520 and len(out) == n - 17520 and nan["QBOT"] == 0 and nan["VPD_USE"] == 0
        EXPECT_RESTORE["TEST"] = {"x"}
        try: decide("TEST", df, res, alt, D, ib); raise AssertionError("restore guard")
        except ValueError: pass
    finally:
        for d in (C.SITES, START_YEAR, EXPECT_RESTORE): d.pop("TEST", None)
    print("CL03 SELF-TEST PASS: interpolation validation, drop-before-start, restore guard, HOLD->INTERP, closure, untouched guard")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--site", choices=sorted(C.SITES)); ap.add_argument("--base")
    a = ap.parse_args()
    print("CL03 FINAL FILL + RESEARCH SHADOW | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    site = a.site
    df, cols, info = C.frame(site, a.base or C.SITES[site]["base"])
    s, sinfo = C.shadow(site)
    if not np.array_equal(pd.to_datetime(s.time).dt.strftime("%Y%m%d%H%M").to_numpy(), df.native_key.to_numpy()): raise ValueError("shadow order")
    nT, nH = check_conventions(s)
    res, vs, vb, D = K.compute(site, df, cols)
    alt = K.alternatives(df)
    isumm, ib = interp_validate(df)
    F = decide(site, df, res, alt, D, ib)
    out, prov, counts, nan, cap, dropped = build(site, s, df, F)
    pd.set_option("display.width", 240); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    print(f"\nconventions verified: TBOT on {nT} rows, QBOT closure on {nH} rows")
    print(f"\n=== {site} INTERP validation on QC0 truth (pseudo-gaps) ===\n" + isumm.round(3).to_string(index=False))
    print(ib.pivot_table(index="T_bin", columns="method", values=["N", "valid_fraction", "MAE_hPa", "bias_hPa", "frac_abs_err_gt2hPa", "bin_pass"],
                         aggfunc="first").reindex(list(M.T_LABELS)).round(3).to_string())
    h = F.loc[F.CL02_recommended.eq("HOLD_NO_VALIDATED_METHOD") | F.final_source.str.startswith("SOURCE_QC0")]
    print(f"\n=== {site} HOLD and restored rows ===\n" + h[["native_key", "gap_HH", "TA_USE_C", "T_bin", "INTERP_anchors", "INTERP_bin_pass_3HH",
          "INTERP_VPD_hPa", "CEC_VPD_hPa", "EMP_VPD_hPa", "final_source", "final_VPD_hPa"]].round(3).to_string(index=False))
    print(f"\n=== {site} final sources (gap rows) ===\n" + F.final_source.value_counts().rename("HH").to_string())
    print(f"\n=== {site} written changes ===\n" + counts.to_string(index=False))
    print("capped to DATM saturation (Magnus vs Flatau):", len(cap))
    if len(cap): print(cap.round(5).to_string(index=False))
    left = {k: v for k, v in nan.items() if v}
    print(f"\nCL03 SUMMARY {site}: shadow rows {len(out)} ({out.time.iloc[0]} .. {out.time.iloc[-1]}) | dropped rows {dropped} | "
          f"filled {len(prov)} | remaining NaN {left or 'NONE'} | approved edits preserved | DATM/Post-v5/spinup 0", flush=True)
    if a.check: print("CL03 CHECK ONLY: no files written.", flush=True); return
    dest = C.ROOT / "science_trials" / (f"cl03_{site}_research_shadow_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    dest.mkdir(parents=True, exist_ok=False)
    tag = site.replace("-", "_")
    names = {f"{site}_CL03_RESEARCH_SHADOW_NOLEAP.csv": out, "CL03_final_decision_table.csv": F, "CL03_change_provenance.csv": prov,
             "CL03_change_counts.csv": counts, "CL03_interp_validation_summary.csv": isumm, "CL03_interp_validation_by_T_bin.csv": ib,
             "CL03_capped_to_DATM_saturation.csv": cap}
    for k, d in names.items(): d.to_csv(dest / k, index=False)
    (dest / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text("Research shadow. DATM/Post-v5/spinup use needs a separate user decision.\n")
    note = (f"{site} research shadow from the approved input shadow with user-approved CL03 rules (2026-10-29): "
            "measured BASE transfer, block-excluded QC0 RH climatology (EMP), capped COMPANION_E (CEC), validated time interpolation "
            "(INTERP) or CEC_LOW_CONFIDENCE for the former HOLD rows. Temperature unchanged; all other rows bit-identical. ")
    if site in START_YEAR: note += f"Forcing starts {START_YEAR[site]}-01-01: the ERA-only rows before it are removed (see docs/US_NR1_FORCING_START_1999_DECISION_20261029.md). "
    if EXPECT_RESTORE.get(site): note += "Source QC0 VPD_F restored at 2004-12-03 22:30-23:30 (corrupt companion ERA). "
    (dest / "SCIENTIFIC_STATUS.md").write_text(note + "\n")
    files = [*names, "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP", "SCIENTIFIC_STATUS.md"]
    rec = {"version": VERSION, "site": site, "inputs": info, "input_shadow": sinfo, "rows": len(out), "first_time": out.time.iloc[0],
           "last_time": out.time.iloc[-1], "rows_dropped_before_start": dropped, "forcing_start_year": START_YEAR.get(site),
           "changes": counts.to_dict("records"), "remaining_nan": nan, "capped_to_DATM_sat": len(cap),
           "Postv5_approved": 0, "DATM_ready": 0, "spinup_authorized": 0, "output_sha256": {n: M.sha(dest / n) for n in files}}
    (dest / f"cl03_{tag}_research_shadow_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("CL03 RESEARCH SHADOW:", dest, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("CL03 STOP:", exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

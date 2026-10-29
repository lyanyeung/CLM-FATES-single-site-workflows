#!/usr/bin/env python3
"""US-NR3 Stage08 (Claude): better-evidence alternatives for the Stage07 HOLD rows, and where the gaps are.

READ ONLY. Imports Stage07 (pinned blob 0ed9b8e4...), which imports Stage01 (pinned) and re-verifies the
SHA lineage. User decisions of 2026-10-29 ("按照你的建议"): the 27 BASE rows that failed only the 2011 year
criterion are accepted as SOURCE_MEASURED_SUPPORTED (research exception); 17 BASE temperature-conflict
rows, 31 non-BASE conflicts stay HOLD; the 163 EMP rows are sensitivity-only. This stage asks only
whether better-evidenced alternatives exist. Rules below are fixed before the run; nothing is approved.

P0 LOCATION   every Stage12G missing episode: start/end, HH, month, TA_USE range, missing fields, source QC,
              BASE triplet HH and Stage07 class mix.
P1 T* AS AIR  humidity-corrected sonic T* (no fitted offset) vs TA_ERA as estimates of the QC0 tower TA_F:
   TEMPERATURE pooled, COLD44 (Dec/Jan, TA_F <= -10), COLD44 by year, |TA_F - TA_ERA| > 5. Also the error of the
              complete measured pair (T*, RH): e and VPD at T* vs QC0. Criterion T*_BETTER: COLD44 pooled
              MAE(T*) <= 1.0 C and MAE(T*) < MAE(TA_ERA) in every COLD44 year with N >= 50.
P2 INTERP     vapour pressure e interpolated in time between QC0 anchors <= 4 HH from the gap edge (gap <= 3 HH),
              capped at DATM saturation; validated on NR3 QC0 with 3-HH pseudo-gaps (row in the middle) per TA_F
              regime with the Stage12j gates (N >= 100).
P3 STRATA     EMP_LOYO and GRID_A validated with a hierarchy (month, TA_ERA bin) -> (season, bin) -> (bin), first
              level with N_valid >= 100; GRID_A scored only on rows of grid years (removes the Stage07 coverage
              artefact). Stage12j gates + median relative error reported.
P4 ICE CAP    if the chosen e exceeds ice saturation at TA_USE by <= 5 %, e := DATM esat(TA_USE) (exactly what DATM
              would apply); larger excess stays HOLD.
P5 SCOPE      every QC2-temperature row with a BASE RH+sonic+PA triplet (not only gaps): current shadow TA_USE vs T*,
              shadow e vs RH x esw(T*); and the dry artefact: share of QC2 cold rows with ice RH < 10 % in the shadow
              vs the same share in QC0 truth.
Alternatives per HOLD row (predeclared):
   17 BASE T-conflict -> MEASURED_PAIR_CANDIDATE (TA := T*, e := RH x esw(T*)) iff T*_BETTER and e <= esi(T*);
                         a temperature repair, separate approval.
   31 non-BASE        -> INTERP if formable and its regime passes; else the P3-passing method with the lower MAE
                         (P4 cap allowed); else HOLD. 2011-11-29 14:00 additionally carries the QC0 TA spike flag.
--self-test; --check prints; --run also writes ONE reports/nr3_08_claude_* folder. No source/shadow/model writes.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "nr3-08-claude-v1-20261029"
HERE = Path(__file__).resolve().parent
S7_SCRIPT = HERE / "nr3_07.py" if (HERE / "nr3_07.py").is_file() else HERE / "nr3_07_claude_ERA_mechanism_QC0_validation_event_decisions_READONLY.py"
S7_BLOB = "0ed9b8e45579a7c50540a4d3583bd3cb620e1cfc"
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM", 6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
W_ANCHOR, MAX_GAP, CAP_EXCESS = 4, 3, 0.05
ONLY_2011 = "RH_SONIC fails the COLD44 validation criteria"
SPIKE_KEY = "201111291400"


def load_s7():
    b = S7_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != S7_BLOB:
        raise ValueError("Pinned nr3_07 Git blob mismatch: " + str(S7_SCRIPT))
    spec = importlib.util.spec_from_file_location("nr3_07_for_nr3_08", S7_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


S7 = load_s7()
S1, esw, esi, tbin, err_stats, gate, table, say = S7.S1, S7.esw, S7.esi, S7.tbin, S7.err_stats, S7.gate, S7.table, S7.say


def runs(mask):
    m = np.asarray(mask, bool); d = np.diff(np.r_[0, m.astype(int), 0]); s = np.flatnonzero(d == 1); e = np.flatnonzero(d == -1)
    return list(zip(s, e - s))


def interp_e(e_anchor, anchor, lo, hi, i, T):
    n = len(anchor)
    la = np.maximum.accumulate(np.where(anchor, np.arange(n), -1)); na = np.minimum.accumulate(np.where(anchor, np.arange(n), n)[::-1])[::-1]
    lo, hi, i = (np.asarray(x) for x in (lo, hi, i))
    inside = (lo >= 1) & (hi <= n - 2)
    a = np.where(inside, la[np.clip(lo - 1, 0, n - 1)], -1); b = np.where(inside, na[np.clip(hi + 1, 0, n - 1)], n)
    ok = inside & (a >= 0) & (b < n) & (a >= lo - W_ANCHOR) & (b <= hi + W_ANCHOR)
    ac, bc = np.clip(a, 0, n - 1), np.clip(b, 0, n - 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        e = e_anchor[ac] + (e_anchor[bc] - e_anchor[ac]) * (i - ac) / (bc - ac)
    return np.where(ok & np.isfinite(e) & (e > 0), np.minimum(e, S7.esat_datm(T)), np.nan)


def p1_temperature(d, cand, truth, et):
    T = d.TA_F.to_numpy(float); Ts = cand["T_star"]; Te = d.TA_ERA.to_numpy(float)
    tq = d.TA_F_QC.eq(0).to_numpy() & np.isfinite(T)
    cold = d.month.isin([12, 1]).to_numpy() & (T <= -10)
    rows = []
    def add(nm, s):
        for k, x in (("T_STAR", Ts), ("TA_ERA", Te)):
            e = (x - T)[s]; e = e[np.isfinite(e)]
            rows.append(dict(stratum=nm, estimate=k, N=len(e), MAE_C=float(np.mean(np.abs(e))) if len(e) else np.nan,
                             bias_C=float(np.mean(e)) if len(e) else np.nan, P95_abs_C=float(np.quantile(np.abs(e), .95)) if len(e) else np.nan))
    both = tq & np.isfinite(Ts)
    add("POOLED", both); add("COLD44", both & cold); add("ABS_TAF_minus_TAERA_gt5", both & (np.abs(T - Te) > 5))
    for y in sorted(d.year.unique()):
        s = both & cold & (d.year.to_numpy() == y)
        if s.sum(): add(f"COLD44_{y}", s)
    P = pd.DataFrame(rows)
    piv = P.pivot_table(index="stratum", columns="estimate", values=["N", "MAE_C"], aggfunc="first")
    yrs = [x for x in piv.index if x.startswith("COLD44_") and piv.loc[x, ("N", "T_STAR")] >= 50]
    better_years = all(piv.loc[y, ("MAE_C", "T_STAR")] < piv.loc[y, ("MAE_C", "TA_ERA")] for y in yrs)
    pooled = float(piv.loc["COLD44", ("MAE_C", "T_STAR")])
    crit = dict(T_STAR_COLD44_MAE_C=pooled, TA_ERA_COLD44_MAE_C=float(piv.loc["COLD44", ("MAE_C", "TA_ERA")]),
                years=len(yrs), better_every_year=bool(better_years), T_STAR_BETTER=bool(pooled <= 1.0 and better_years and len(yrs) > 0))
    # full measured pair at T*
    rh = d.B_RH.to_numpy(float)
    vp = esw(Ts) * (1 - rh / 100)
    pr = []
    for nm, s in (("POOLED", truth & np.isfinite(vp)), ("COLD44", truth & np.isfinite(vp) & cold)):
        r = err_stats((vp - d.VPD_F.to_numpy(float))[s], et[s]); r.update(stratum=nm, quantity="VPD_at_T*_vs_QC0_VPD"); pr.append(r)
    say("P1_T_STAR_CRITERION", crit)
    return P, pd.DataFrame(pr), crit


def p2_interp(d, truth, et):
    T = d.TA_F.to_numpy(float); e_obs = np.where(truth, et, np.nan); i = np.flatnonzero(truth)
    e = interp_e(e_obs, truth, i - 1, i + 1, i, T[i]); err = np.full(len(d), np.nan); err[i] = e - et[i]
    rows = []
    for b in S7.T_LAB:
        s = truth & (tbin(T) == b); r = err_stats(err[s], et[s]); r.update(T_bin=b); r["gate"] = gate(r) if r.get("N_valid") else False; rows.append(r)
    r = err_stats(err[truth], et[truth]); r.update(T_bin="POOLED"); r["gate"] = gate(r); rows.append(r)
    return pd.DataFrame(rows)


def p3_strata(d, cand, truth, et, grid_years):
    tb = tbin(d.TA_ERA); se = d.month.map(SEASON).to_numpy(); mo = d.month.to_numpy()
    gy = d.year.isin(grid_years).to_numpy()
    out = {}
    for k in ("EMP_LOYO", "GRID_A"):
        err = cand[k] - et; base = truth & (gy if k == "GRID_A" else True)
        tabs = {}
        for lvl, key in (("month+bin", lambda: pd.Series(list(zip(mo, tb)))), ("season+bin", lambda: pd.Series(list(zip(se, tb)))), ("bin", lambda: pd.Series(tb))):
            kk = key().to_numpy(); res = {}
            df = pd.DataFrame({"k": kk[base], "err": err[base], "et": et[base]})
            for g, x in df.groupby("k"):
                r = err_stats(x.err.to_numpy(), x.et.to_numpy()); r["gate"] = gate(r) if r.get("N_valid") else False; res[g] = r
            tabs[lvl] = (kk, res)
        out[k] = tabs
    return out


def pick_stratum(tabs, i):
    for lvl in ("month+bin", "season+bin", "bin"):
        kk, res = tabs[lvl]; r = res.get(kk[i])
        if r and r.get("N_valid", 0) >= 100: return lvl, r
    return "", {}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--root", type=Path, default=S1.ROOT)
    a = ap.parse_args()
    print("NR3_08 CLAUDE HOLD ALTERNATIVES + GAP LOCATIONS | " + VERSION, flush=True)
    S7.self_test()
    n = 40; m = np.zeros(n, bool); m[[5, 6, 7, 20, 21, 22]] = True
    e = interp_e(np.where(m, np.arange(n) * .1 + 1, np.nan), m, np.array([10]), np.array([12]), np.array([11]), np.array([-5.]))
    assert np.isnan(e[0]), "anchors beyond 4 HH must not be used"
    m2 = np.zeros(n, bool); m2[[7, 11]] = True
    e = interp_e(np.where(m2, 1.0, np.nan), m2, np.array([8]), np.array([10]), np.array([9]), np.array([5.])); assert abs(e[0] - 1) < 1e-12
    print("NR3_08 SELF-TEST PASS: interpolation anchor rule", flush=True)
    if a.self_test: return
    d, selected, missing, verified, external, gy = S7.load(a.root)
    d, yr, tb_, low, tot, fit = S7.mechanism(d, verified, missing)
    base_ok = (d.B_RH.between(0, 100) & d.B_T_SONIC.between(-70, 60) & d.B_PA.between(40, 110)).to_numpy()
    cand = S7.candidates(d, base_ok)
    truth, et, V_, TS, sg = S7.validate(d, cand)
    crit7 = S7.cold_criteria(V_, TS)
    E = S7.events(d, selected, missing, cand, sg, crit7, set(int(y) for y in d.loc[truth, "year"].unique()))
    pos = {k: i for i, k in enumerate(d.native_key)}
    # ---------------- P0 location
    E["dt"] = pd.to_datetime(E.native_key, format="%Y%m%d%H%M")
    E = E.sort_values("dt").reset_index(drop=True); E["ep"] = E.dt.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    E["group"] = np.where(E.BASE_triplet & (E.rationale == ONLY_2011), "BASE27_ACCEPTED", np.where(E.BASE_triplet, "BASE17_T_CONFLICT",
                 np.where(E["class"] == "EXTERNAL_ERA_CANDIDATE_UNCERTAIN", "EMP163_SENSITIVITY", "NONBASE31_HOLD")))
    say("P0_MISSING_FIELDS", E.missing_fields.value_counts().to_dict())
    loc = E.groupby("ep").agg(start=("native_key", "first"), end=("native_key", "last"), HH=("native_key", "size"), TA_USE_min=("TA_USE", "min"),
                              TA_USE_max=("TA_USE", "max"), TA_QC=("TA_F_QC", lambda s: "/".join(str(int(x)) for x in sorted(s.dropna().unique()))),
                              VPD_QC=("VPD_F_QC", lambda s: "/".join(str(int(x)) for x in sorted(s.dropna().unique()))), BASE=("BASE_triplet", "sum"),
                              groups=("group", lambda s: ",".join(f"{k}:{v}" for k, v in s.value_counts().items()))).reset_index(drop=True)
    table("P0 all missing episodes (native LST, UTC-7)", loc.round(1), 80)
    # ---------------- P1
    P1, P1pair, critT = p1_temperature(d, cand, truth, et)
    table("P1 T* and TA_ERA vs QC0 TA_F", P1.round(3), 60); table("P1b measured pair VPD at T*", P1pair.round(3))
    # ---------------- P2 / P3
    P2 = p2_interp(d, truth, et); table("P2 INTERP 3-HH pseudo-gap validation", P2[["T_bin", "N", "N_valid", "valid_fraction", "MAE_hPa", "bias_hPa", "P95_abs_hPa", "median_rel", "gate"]].round(3))
    ipass = P2.set_index("T_bin").gate.to_dict()
    st = p3_strata(d, cand, truth, et, gy)
    anchor = truth
    e_anchor = np.where(truth, et, np.nan)
    gapmask = np.zeros(len(d), bool); gapmask[[pos[k] for k in E.native_key]] = True
    lo = np.zeros(len(d), int); hi = np.zeros(len(d), int)
    for s, ln in runs(gapmask): lo[s:s + ln] = s; hi[s:s + ln] = s + ln - 1
    rows = []
    for r in E.to_dict("records"):
        i = pos[r["native_key"]]; T = float(r["TA_USE"]); x = dict(native_key=r["native_key"], group=r["group"], TA_USE=T, gap_HH=int(hi[i] - lo[i] + 1))
        x["T_star"] = cand["T_star"][i]
        if r["group"] == "BASE17_T_CONFLICT":
            ts = x["T_star"]; e = r["B_RH"] / 100 * esw(ts)
            x.update(alt_e=e, alt_TA=ts, alt_RHice_at_alt_TA=100 * e / esi(ts) if ts < 0 else np.nan)
            ok = critT["T_STAR_BETTER"] and np.isfinite(e) and (ts >= 0 or e <= esi(ts))
            x["alternative"] = "MEASURED_PAIR_CANDIDATE_T_REPAIR" if ok else "HOLD"
            x["why"] = "T* better than ERA in COLD44 every year; measured RH at T*; needs temperature approval" if ok else "T* criterion fails or e above ice at T*"
        elif r["group"] == "NONBASE31_HOLD":
            ei = interp_e(e_anchor, anchor, np.array([lo[i]]), np.array([hi[i]]), np.array([i]), np.array([T]))[0]
            reg = tbin(np.array([T]))[0]
            x["INTERP_e"] = ei; x["INTERP_regime_pass"] = bool(ipass.get(reg, False))
            if np.isfinite(ei) and x["gap_HH"] <= MAX_GAP and x["INTERP_regime_pass"]:
                x.update(alternative="INTERP", alt_e=ei, why="QC0 anchors <= 4 HH; regime validated")
            else:
                best = []
                for k in ("GRID_A", "EMP_LOYO"):
                    e = cand[k][i]
                    if not np.isfinite(e): continue
                    lvl, sr = pick_stratum(st[k], i)
                    x[f"{k}_e"] = e; x[f"{k}_level"] = lvl; x[f"{k}_MAE"] = sr.get("MAE_hPa", np.nan); x[f"{k}_rel"] = sr.get("median_rel", np.nan)
                    x[f"{k}_RHice"] = 100 * e / esi(T) if T < 0 else np.nan
                    if sr.get("gate"): best.append((0 if (T >= 0 or e <= esi(T)) else 1, sr["MAE_hPa"], k, e))
                if best:
                    _, mae, k, e = sorted(best)[0]
                    excess = e / esi(T) - 1 if T < 0 else -1
                    if excess <= 0:
                        x.update(alternative=k + "_STRATUM_VALIDATED", alt_e=e, why=f"{k} passes at {x[k + '_level']}")
                    elif excess <= CAP_EXCESS:
                        x.update(alternative=k + "_CAPPED_TO_ICE_SAT", alt_e=float(S7.esat_datm(T)), why=f"{k} {100 * excess:.1f}% above ice saturation; DATM-equivalent cap")
                    else:
                        x.update(alternative="HOLD", why=f"{k} {100 * excess:.0f}% above ice saturation")
                else:
                    x.update(alternative="HOLD", why="no validated stratum at any level")
            if r["native_key"] == SPIKE_KEY: x["why"] = x.get("why", "") + "; QC0 TA -34.87 C isolated spike (sonic -1.8 C) - source-QA flag"
        else:
            continue
        x["alt_VPD_at_alt_TA"] = esw(x.get("alt_TA", T)) - x["alt_e"] if np.isfinite(x.get("alt_e", np.nan)) else np.nan
        rows.append(x)
    A = pd.DataFrame(rows)
    table("ALT 17 BASE temperature-conflict rows", A.loc[A.group == "BASE17_T_CONFLICT", ["native_key", "TA_USE", "alt_TA", "alt_e", "alt_RHice_at_alt_TA", "alt_VPD_at_alt_TA", "alternative"]].round(2))
    c31 = [c for c in ["native_key", "TA_USE", "gap_HH", "INTERP_e", "INTERP_regime_pass", "GRID_A_e", "GRID_A_level", "GRID_A_MAE", "GRID_A_RHice", "EMP_LOYO_e", "EMP_LOYO_level", "EMP_LOYO_MAE", "EMP_LOYO_RHice", "alternative", "alt_e", "why"] if c in A]
    table("ALT 31 non-BASE rows", A.loc[A.group == "NONBASE31_HOLD", c31].round(2), 40)
    # ---------------- P5 scope
    sel = selected.copy(); sel["native_key"] = S1.keys(sel, "time")
    s_idx = sel.set_index("native_key")
    dd = d[["native_key", "year", "month", "TA_F_QC", "VPD_F_QC"]].join(s_idx[["TA_USE", "VPD_USE"]], on="native_key")
    se_ = esw(dd.TA_USE) - dd.VPD_USE; rhice = 100 * se_ / esi(dd.TA_USE)
    w = base_ok & dd.TA_F_QC.eq(2).to_numpy() & np.isfinite(dd.TA_USE.to_numpy(float))
    sc = pd.DataFrame({"year": dd.year[w], "month": dd.month[w], "dT_shadow_minus_Tstar": (dd.TA_USE.to_numpy(float) - cand["T_star"])[w],
                       "de_shadow_minus_RH_Tstar": (se_.to_numpy(float) - cand["RH_SONIC"])[w]})
    P5 = sc.groupby(["year", "month"]).agg(HH=("year", "size"), dT_bias=("dT_shadow_minus_Tstar", "mean"), dT_MAE=("dT_shadow_minus_Tstar", lambda x: x.abs().mean()),
                                            de_bias=("de_shadow_minus_RH_Tstar", "mean"), de_MAE=("de_shadow_minus_RH_Tstar", lambda x: x.abs().mean())).reset_index()
    table("P5a QC2-temperature rows that have a BASE RH+sonic+PA triplet (whole record, not only gaps)", P5.round(2), 80)
    cold = (dd.TA_USE < -10).to_numpy()
    qc2 = dd.VPD_F_QC.eq(2).to_numpy() & cold & np.isfinite(rhice.to_numpy())
    tr = truth & (d.TA_F.to_numpy(float) < -10)
    rh_t = 100 * et / esi(d.TA_F.to_numpy(float))
    dry = pd.DataFrame([dict(population="shadow QC2 VPD, TA_USE<-10", HH=int(qc2.sum()), share_RHice_lt10=float((rhice.to_numpy()[qc2] < 10).mean()),
                             share_RHice_lt30=float((rhice.to_numpy()[qc2] < 30).mean()), median_RHice=float(np.median(rhice.to_numpy()[qc2]))),
                        dict(population="QC0 truth, TA_F<-10", HH=int(tr.sum()), share_RHice_lt10=float((rh_t[tr] < 10).mean()),
                             share_RHice_lt30=float((rh_t[tr] < 30).mean()), median_RHice=float(np.median(rh_t[tr])))])
    table("P5b dry artefact: ice RH distribution, shadow QC2 cold rows vs QC0 truth", dry.round(3))
    say("ALT_COUNTS", A.groupby(["group", "alternative"]).size().rename("HH").reset_index().to_dict("records"))
    print("\nNR3_08 SUMMARY: groups " + json.dumps(E.group.value_counts().to_dict()) + " | alternatives " +
          json.dumps(A.alternative.value_counts().to_dict()) + " | approved 0", flush=True)
    for p, h in S1.READS.items():
        if S1.digest(p) != h: raise ValueError("input changed during audit: " + p)
    if a.check: print("NR3_08 CHECK ONLY: no files written.", flush=True); return
    out = a.root / "reports" / ("nr3_08_claude_HOLD_alternatives_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"P0_missing_episodes.csv": loc, "P0_238_rows_with_groups.csv": E.drop(columns=["dt"]), "P1_temperature.csv": P1, "P1_pair.csv": P1pair,
             "P2_interp_validation.csv": P2, "ALT_hold_rows.csv": A, "P5a_triplet_QC2_scope.csv": P5, "P5b_dry_artefact.csv": dry}
    for k, v in files.items(): v.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("Read-only alternatives. Nothing approved; temperature repair and any fill need separate user approval.\n")
    rec = {"version": VERSION, "s7_blob": S7_BLOB, "inputs_sha256": dict(S1.READS), "T_star_criterion": critT,
           "alternatives": A.alternative.value_counts().to_dict(), "approved": 0, "output_sha256": {n: S1.digest(out / n) for n in [*files, "SCIENTIFIC_HOLD.md"]}}
    (out / "nr3_08_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("NR3_08 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("NR3_08 STOP:", type(exc).__name__, exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

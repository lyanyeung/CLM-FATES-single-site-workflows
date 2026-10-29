#!/usr/bin/env python3
"""US-NR3 Stage09 (Claude): RESEARCH SHADOW applying the user decisions of 2026-10-29
("那就都按照你说的建议弄，ERA5-Land其实也是可以的"). Reads Stage12G and the originals; writes only a NEW folder.

Imports Stage07 (pinned blob 0ed9b8e4...) -> Stage01 (pinned), which re-verifies the SHA lineage.

MAIN shadow, rules fixed before the first run, applied in this order to a copy of Stage12G:
 1 MEASURED-PAIR WINDOW  every row with a BASE triplet (RH 0-100, T_SONIC -70..60, PA 40..110 kPa) whose FLUXMET
                         TA_F_QC == 2: TA_USE := T* (humidity-corrected sonic, no fitted offset; cold-season MAE
                         0.58 C vs ERA 4.17 C on QC0), TBOT := TA_USE + 273.15, e := RH/100 * esw(T*).
                         Includes all 44 BASE gap rows (27 accepted + 17 temperature conflict).
 2 TA SPIKE              2011-11-29 13:30 (MDS, contaminated) and 14:00 (QC0 -34.87 C, isolated spike): TA_USE :=
                         raw T_SONIC (humidity correction < 0.5 K not applied; no RH), humidity by rule 3 at that T.
 3 OTHER GAPS            remaining Stage12G missing rows: e := ERA5-Land absolute e (esw(d2m)) where available,
                         else the leave-one-year-out QC0 RH climatology RH_emp x esw(TA_USE). If the chosen e
                         exceeds DATM saturation at TA_USE by > 5 % and the other method is within 5 %, the other
                         method is used. Any e above DATM saturation is set to it (what DATM does) and recorded.
 Every changed humidity: VPD_USE = esw(TA_USE) - e, QBOT = 0.622 e / (PSRF - 0.378 e) (the Stage12G closure, proven
 on its existing rows first; TBOT = TA_USE + 273.15 also proven). All other columns and all untouched rows are
 bit-identical to Stage12G. No NaN may remain in MAIN.
SENSITIVITY shadow = MAIN plus rule 4 (not for the main line):
 4 DRY-QC2 HUMIDITY      every remaining row with VPD_F_QC == 2 and TA_USE < 0 C (the 1.449 hPa VPD-floor regime):
                         humidity by rule 3 at the retained TA_USE. Temperature unchanged.
Labels: 1 MEASURED_PAIR_TSTAR_RH; 2 TSONIC_SPIKE_REPLACEMENT; 3 ERA5LAND_E / EMP_CLIMATOLOGY (+_CAPPED / _LOW_CONF).
--self-test synthetic; --check computes and prints, NO writes; --run writes ONE science_trials/nr3_09_claude_* folder
with INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP. No DATM/AD400/Slurm.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "nr3-09-claude-v1-20261029-research-shadow"
HERE = Path(__file__).resolve().parent
S7_SCRIPT = HERE / "nr3_07.py" if (HERE / "nr3_07.py").is_file() else HERE / "nr3_07_claude_ERA_mechanism_QC0_validation_event_decisions_READONLY.py"
S7_BLOB = "0ed9b8e45579a7c50540a4d3583bd3cb620e1cfc"
SPIKE = ("201111291330", "201111291400")
EXCESS_OK = 0.05


def load_s7():
    b = S7_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != S7_BLOB:
        raise ValueError("Pinned nr3_07 Git blob mismatch: " + str(S7_SCRIPT))
    spec = importlib.util.spec_from_file_location("nr3_07_for_nr3_09", S7_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


S7 = load_s7()
S1, esw, esi, q_from_e, sat = S7.S1, S7.esw, S7.esi, S7.q_from_e, S7.esat_datm


def check_conventions(s):
    T, P, V, Q = (s[c].to_numpy(float) for c in ("TA_USE", "PSRF", "VPD_USE", "QBOT"))
    if "TBOT" in s:
        f = np.isfinite(T) & np.isfinite(s.TBOT.to_numpy(float))
        if not np.allclose(s.TBOT.to_numpy(float)[f], T[f] + 273.15, rtol=0, atol=1e-6): raise ValueError("Stage12G TBOT != TA_USE + 273.15")
    h = np.isfinite(V) & np.isfinite(Q) & np.isfinite(T) & np.isfinite(P)
    if not np.allclose(q_from_e(esw(T[h]) - V[h], P[h]), Q[h], rtol=1e-8, atol=1e-10): raise ValueError("Stage12G QBOT closure differs")
    return int(h.sum())


def humidity_rule3(T, grid_e, rh_emp):
    """returns e, label for one row at temperature T (rule 3)."""
    es = float(sat(T)); opts = []
    if np.isfinite(grid_e) and grid_e > 0: opts.append(("ERA5LAND_E", grid_e))
    if np.isfinite(rh_emp) and rh_emp > 0: opts.append(("EMP_CLIMATOLOGY", rh_emp * float(esw(T))))
    if not opts: return np.nan, "NONE"
    lab, e = opts[0]
    if e > es * (1 + EXCESS_OK) and len(opts) > 1 and opts[1][1] <= es * (1 + EXCESS_OK): lab, e = opts[1]
    if e > es:
        lab += "_CAPPED" if e <= es * (1 + EXCESS_OK) else "_LARGE_CAP"; e = es
    return e, lab


def build(s, keys, d, cand, gap_keys, sens):
    """s: Stage12G copy; keys: its native keys; d: raw+BASE frame; cand: Stage07 candidates."""
    out = s.copy(); pos = {k: i for i, k in enumerate(keys)}; dpos = {k: i for i, k in enumerate(d.native_key)}
    T = out.TA_USE.to_numpy(float).copy(); P = out.PSRF.to_numpy(float)
    e_new = np.full(len(out), np.nan); lab = np.full(len(out), "", dtype=object); tchg = np.zeros(len(out), bool)
    rh_emp = cand["EMP_LOYO"] / esw(d.TA_ERA.to_numpy(float))
    base_ok = (d.B_RH.between(0, 100) & d.B_T_SONIC.between(-70, 60) & d.B_PA.between(40, 110)).to_numpy()
    win = base_ok & d.TA_F_QC.eq(2).to_numpy()
    for j in np.flatnonzero(win):                                                     # rule 1
        k = d.native_key.iloc[j]
        if k not in pos: continue                                                      # Feb 29 not in NOLEAP
        i = pos[k]; ts = cand["T_star"][j]
        if not np.isfinite(ts): continue
        T[i] = ts; tchg[i] = True; e_new[i] = d.B_RH.iloc[j] / 100 * esw(ts); lab[i] = "MEASURED_PAIR_TSTAR_RH"
    for k in SPIKE:                                                                    # rule 2
        if k in pos and k in dpos and np.isfinite(d.B_T_SONIC.iloc[dpos[k]]):
            i = pos[k]; T[i] = float(d.B_T_SONIC.iloc[dpos[k]]); tchg[i] = True; lab[i] = "TSONIC_SPIKE_REPLACEMENT"
    gset = set(gap_keys)
    targets = [k for k in gap_keys if not lab[pos[k]].startswith("MEASURED")]
    if sens:
        q2 = d.VPD_F_QC.eq(2).to_numpy()
        extra = [d.native_key.iloc[j] for j in np.flatnonzero(q2) if d.native_key.iloc[j] in pos]
        extra = [k for k in extra if not lab[pos[k]].startswith("MEASURED") and T[pos[k]] < 0 and k not in gset]
        targets = targets + extra
    for k in targets:                                                                  # rule 3 / 4
        i = pos[k]; j = dpos[k]
        e, l = humidity_rule3(T[i], cand["GRID_A"][j], rh_emp[j])
        e_new[i] = e; lab[i] = (lab[i] + "+" if lab[i] else "") + l + ("_SENS_DRYQC2" if k not in gset else "")
    sel = np.isfinite(e_new)
    for i in np.flatnonzero(sel & np.char.startswith(lab.astype(str), "MEASURED")):    # measured pair cap (frost)
        es = float(sat(T[i]))
        if e_new[i] > es: e_new[i] = es; lab[i] += "_CAPPED"
    if (e_new[sel] <= 0).any(): raise ValueError("non-positive vapour pressure")
    V = out.VPD_USE.to_numpy(float).copy(); Q = out.QBOT.to_numpy(float).copy()
    V[sel] = esw(T[sel]) - e_new[sel]; Q[sel] = q_from_e(e_new[sel], P[sel])
    if (q_from_e(e_new[sel], P[sel]) > q_from_e(sat(T[sel]), P[sel]) * (1 + 1e-9)).any(): raise ValueError("QBOT above DATM saturation")
    old = {c: s[c].to_numpy() for c in s.columns}
    out["TA_USE"] = np.where(tchg, T, old["TA_USE"])
    if "TBOT" in out: out["TBOT"] = np.where(tchg, T + 273.15, old["TBOT"])
    out["VPD_USE"] = np.where(sel, V, old["VPD_USE"]); out["QBOT"] = np.where(sel, Q, old["QBOT"])
    touched = tchg | sel
    for c in out.columns:
        a, b = old[c], out[c].to_numpy(); same = (a == b) | (pd.isna(a) & pd.isna(b))
        if c in ("TA_USE", "TBOT", "VPD_USE", "QBOT"):
            if not same[~touched].all(): raise ValueError("untouched row changed in " + c)
        elif not same.all(): raise ValueError("column changed that must not change: " + c)
    idx = np.flatnonzero(touched)
    prov = pd.DataFrame({"native_key": np.asarray(keys)[idx], "label": lab[idx], "T_changed": tchg[idx],
                         "old_TA_USE": old["TA_USE"][idx], "new_TA_USE": out.TA_USE.to_numpy()[idx],
                         "old_VPD_USE": old["VPD_USE"][idx], "new_VPD_USE": out.VPD_USE.to_numpy()[idx],
                         "old_QBOT": old["QBOT"][idx], "new_QBOT": out.QBOT.to_numpy()[idx], "in_238": np.isin(np.asarray(keys)[idx], list(gset))})
    # edge jumps of the measured-pair window
    w = np.zeros(len(out), bool); w[[pos[k] for k in d.native_key[win] if k in pos]] = True
    edges = np.flatnonzero(np.diff(w.astype(int)) != 0)
    jumps = np.abs(out.TA_USE.to_numpy(float)[edges + 1] - out.TA_USE.to_numpy(float)[edges])
    nan = {c: int(out[c].isna().sum()) for c in out.columns if c != "time"}
    return out, prov, nan, dict(window_edges=int(len(edges)), edge_jump_gt3C=int((jumps > 3).sum()), edge_jump_max_C=float(np.nanmax(jumps)) if len(jumps) else 0.0)


def self_test():
    t = pd.date_range("2016-12-01", periods=200, freq="30min"); keys = t.strftime("%Y%m%d%H%M")
    T = np.full(200, -20.0); P = np.full(200, 65000.0); V = np.full(200, 0.3)
    s = pd.DataFrame({"time": t.strftime("%Y-%m-%d %H:%M:%S"), "TBOT": T + 273.15, "QBOT": q_from_e(esw(T) - V, P), "PSRF": P, "FSDS": 0.0, "TA_USE": T, "VPD_USE": V})
    s.loc[[50, 51, 120], ["VPD_USE", "QBOT"]] = np.nan
    check_conventions(s)
    d = pd.DataFrame({"native_key": keys, "TA_F_QC": 2, "VPD_F_QC": 2, "TA_ERA": T, "B_RH": np.nan, "B_T_SONIC": np.nan, "B_PA": np.nan})
    d.loc[40:60, ["B_RH", "B_T_SONIC", "B_PA"]] = [60.0, -15.0, 65.0]
    cand = {"T_star": np.where(d.B_T_SONIC.notna(), -15.2, np.nan), "GRID_A": np.full(200, 0.5), "EMP_LOYO": np.full(200, 0.8)}
    cand["GRID_A"][120] = 5.0
    out, prov, nan, ed = build(s, keys, d, cand, [keys[50], keys[51], keys[120]], False)
    assert nan["QBOT"] == 0 and abs(out.TA_USE[50] + 15.2) < 1e-12 and abs(out.TBOT[45] - (273.15 - 15.2)) < 1e-12
    assert prov.set_index("native_key").loc[keys[120], "label"].startswith("EMP_CLIMATOLOGY"), "fallback when ERA5-Land far above ice"
    assert ed["window_edges"] == 2 and ed["edge_jump_gt3C"] == 2
    out2, prov2, _, _ = build(s, keys, d, cand, [keys[50], keys[51], keys[120]], True)
    assert len(prov2) > len(prov) and (out2.TA_USE[~out2.index.isin(range(40, 61))] == -20).all()
    print("NR3_09 SELF-TEST PASS: conventions, measured-pair window, rule-3 fallback/cap, sensitivity, untouched guard", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--root", type=Path, default=S1.ROOT)
    a = ap.parse_args()
    print("NR3_09 CLAUDE RESEARCH SHADOW | " + VERSION, flush=True)
    S7.self_test(); self_test()
    if a.self_test: return
    d, selected, missing, verified, external, gy = S7.load(a.root)
    base_ok = (d.B_RH.between(0, 100) & d.B_T_SONIC.between(-70, 60) & d.B_PA.between(40, 110)).to_numpy()
    cand = S7.candidates(d, base_ok)
    truth, et, V_, TS, sg = S7.validate(d, cand)
    keys = S1.keys(selected, "time").to_numpy()
    nH = check_conventions(selected)
    gap_keys = list(missing.native_key)
    res = {}
    for nm, sens in (("MAIN", False), ("SENSITIVITY", True)):
        out, prov, nan, ed = build(selected, keys, d, cand, gap_keys, sens)
        res[nm] = (out, prov, nan, ed)
        cnt = prov.groupby(["label", "in_238"]).size().rename("HH").reset_index()
        S7.table(f"{nm} changes by label", cnt, 60)
        S7.say(f"{nm}_SUMMARY", dict(rows=len(out), changed=len(prov), T_changed=int(prov.T_changed.sum()), gaps_filled=int(prov.in_238.sum()),
                                     remaining_NaN={k: v for k, v in nan.items() if v}, **ed))
    main_nan = {k: v for k, v in res["MAIN"][2].items() if v}
    if main_nan: raise ValueError(f"MAIN still has NaN: {main_nan}")
    p = res["MAIN"][1].set_index("native_key")
    show = p.loc[[k for k in ("201612080230", "201612170400", "201701050230", "201701060300", "200912030400", "201110251430", "201111291400", "202310300200") if k in p.index]]
    S7.table("MAIN examples (old vs new)", show.reset_index().round(3))
    filled = int(res["MAIN"][1].in_238.sum())
    if filled != len(gap_keys): raise ValueError(f"MAIN filled {filled} of {len(gap_keys)} gaps")
    print(f"\nNR3_09 SUMMARY: closure verified on {nH} rows | MAIN changed {len(res['MAIN'][1])} ({filled}/{len(gap_keys)} gaps filled, NaN 0) | "
          f"SENSITIVITY changed {len(res['SENSITIVITY'][1])} | DATM/Post-v5/spinup 0", flush=True)
    for pth, h in S1.READS.items():
        if S1.digest(pth) != h: raise ValueError("input changed during run: " + pth)
    if a.check: print("NR3_09 CHECK ONLY: no files written.", flush=True); return
    dest = a.root / "science_trials" / ("nr3_09_claude_research_shadow_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    dest.mkdir(parents=True, exist_ok=False)
    files = {"US-NR3_NR3_09_MAIN_RESEARCH_SHADOW_NOLEAP.csv": res["MAIN"][0], "NR3_09_MAIN_provenance.csv": res["MAIN"][1],
             "US-NR3_NR3_09_SENSITIVITY_DRY_QC2_SHADOW_NOLEAP.csv": res["SENSITIVITY"][0], "NR3_09_SENSITIVITY_provenance.csv": res["SENSITIVITY"][1]}
    for k, v in files.items(): v.to_csv(dest / k, index=False)
    (dest / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text("Research shadows. DATM/Post-v5/spinup use needs a separate user decision.\n")
    (dest / "SCIENTIFIC_STATUS.md").write_text(
        "US-NR3 research shadows from Stage12G with the user decisions of 2026-10-29: MAIN = measured pair (T* + BASE RH) for every "
        "QC2-temperature row with a BASE triplet (incl. all 44 BASE gaps), sonic T for the 2011-11-29 TA spike, ERA5-Land e else QC0 RH "
        "climatology for the other gaps (DATM-equivalent saturation cap). SENSITIVITY = MAIN + the same humidity rule for remaining "
        "VPD_F_QC=2 rows below 0 C (VPD-floor dry bias). Evidence: docs/US_NR3_CLAUDE_STAGE07_EVENT_DECISION_REPORT_20261029.md.\n")
    names = [*files, "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP", "SCIENTIFIC_STATUS.md"]
    rec = {"version": VERSION, "s7_blob": S7_BLOB, "inputs_sha256": dict(S1.READS), "rows": len(res["MAIN"][0]),
           "MAIN": dict(changed=len(res["MAIN"][1]), labels=res["MAIN"][1].label.value_counts().to_dict(), edges=res["MAIN"][3]),
           "SENSITIVITY": dict(changed=len(res["SENSITIVITY"][1]), labels=res["SENSITIVITY"][1].label.value_counts().to_dict()),
           "Postv5_approved": 0, "DATM_ready": 0, "spinup_authorized": 0, "output_sha256": {n: S1.digest(dest / n) for n in names}}
    (dest / "nr3_09_research_shadow_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("NR3_09 RESEARCH SHADOW:", dest, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("NR3_09 STOP:", type(exc).__name__, exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

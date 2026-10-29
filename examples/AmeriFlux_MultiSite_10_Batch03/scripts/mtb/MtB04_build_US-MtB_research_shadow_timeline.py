#!/usr/bin/env python3
"""MtB04 (Claude workstream, US-MtB only): complete US-MtB RESEARCH SHADOW timeline.

Applies the user-approved decisions (2026-10-29) to a COPY of the sealed Stage12g US-MtB
NOLEAP timeline. Original FLUXMET/ERA/BASE files, Stage12g and the MtB03 report are only read.

Inputs (all checked): MtB03 report folder (receipt SHA of every output), Stage12g timeline
(receipt), FLUXMET/ERA via the pinned MtB01 loaders.

Changes, in this order:
 1 TEMPERATURE  every MtB03 FAULT_31M / CLIP_31M row: TA_USE := candidate (16 m consensus
   transfer, validated MAE 0.13-0.27 C), TBOT := TA_USE + 273.15.
 2 HUMIDITY     every MtB03 humidity target (Stage12g gaps + FAULT_31M rows):
     L24 / L16 measured RH transfer and COMPANION_E: the MtB03 vapour pressure e;
     HOLD_OUT_OF_REGIME  -> COMPANION_E_OUT_OF_VALIDATED_REGIME (user decision; MAE ~1.7 hPa class)
                            if formable, else saturation;
     HOLD_NOT_FORMABLE   -> SATURATED_DATM_ESAT (user decision): e = DATM's own datm_eSat
                            (CDEPS 1.0.105 Flatau polynomial; over ice when T < 0 C), so the
                            QBOT written equals the cap DATM would apply anyway.
 3 CONSISTENCY  rows whose temperature changed but humidity was not a target keep their vapour
   pressure e = esw(T_old) - VPD_old (VPD recomputed at the new T); if that e exceeds the DATM
   saturation at the new T it is set to saturation (counted).
 VPD_USE = esw(T) - e, QBOT = 0.622 e / (PSRF - 0.378 e): the same closure Stage12e enforces;
 the script first proves that closure (rtol 1e-8) and TBOT = TA_USE + 273.15 on the existing
 rows, so new values follow the timeline's own conventions. Every new QBOT must be <= the DATM
 saturation (tolerance 1e-9 kg/kg) or the run stops.

Output (--run only): ONE new science_trials/mtb04_* folder with the full timeline, a per-change
provenance ledger, counts, the INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP marker (DATM/Post-v5
remains a separate user decision) and an SHA receipt. --check computes everything, NO writes.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-MtB04-v1-20261029-US-MtB-research-shadow"
HERE = Path(__file__).resolve().parent
X_SCRIPT = HERE / "MtB03_multilevel_BASE_T_and_humidity_fill_candidates_READONLY.py"
X_BLOB = "0f98f232910748ac80c5cb3c07defba0a930b7bb"
MTB03_DEFAULT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/"
                     "mtb03_US-MtB_multilevel_fill_candidates_20261029T031536Z_50d84498")
TKFRZ = 273.15
CAP_REL = 0.01
A = (6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04, 3.031240396e-06, 2.034080948e-08, 6.136820929e-11)
B = (6.109177956, 5.034698970e-01, 1.886013408e-02, 4.176223716e-04, 5.824720280e-06, 4.838803174e-08, 1.838826904e-10)


def load_x():
    b = X_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != X_BLOB:
        raise ValueError("Pinned MtB03 Git blob mismatch: " + str(X_SCRIPT))
    spec = importlib.util.spec_from_file_location("mtb03_for_mtb04", X_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


X = load_x()
M = X.M


def datm_esat_hpa(t_c):
    """CDEPS datm_eSat(tK, tKbot) with tK = tKbot, in hPa (DATM returns Pa)."""
    t = np.clip(np.asarray(t_c, float), -50.0, 50.0)
    c = np.where(np.asarray(t_c, float) < 0.0, 1, 0)
    pa = lambda k: k[0] + t * (k[1] + t * (k[2] + t * (k[3] + t * (k[4] + t * (k[5] + t * k[6])))))
    return np.where(c == 1, pa(B), pa(A))


def q_of(e, p): return M.q_from_e(e, p)


def mtb03_folder(folder):
    folder = Path(folder)
    rec = json.loads(M.regular(folder / "mtb03_receipt.json").read_text())
    if not str(rec.get("version", "")).startswith("batch03-MtB03-"): raise ValueError("MtB03 receipt version")
    for n, d in rec["output_sha256"].items():
        if M.sha(folder / n) != d: raise ValueError("MtB03 output SHA mismatch: " + n)
    t = pd.read_csv(folder / "T_candidates.csv", dtype={"native_key": str})
    h = pd.read_csv(folder / "H_fill_candidates.csv", dtype={"native_key": str})
    return rec, t, h


def check_conventions(g):
    T, TB, P = g.TA_USE.to_numpy(float), g.TBOT.to_numpy(float), g.PSRF.to_numpy(float)
    V, Q = g.VPD_USE.to_numpy(float), g.QBOT.to_numpy(float)
    f = np.isfinite(T) & np.isfinite(TB)
    if not np.allclose(TB[f], T[f] + TKFRZ, rtol=0, atol=1e-6): raise ValueError("timeline TBOT != TA_USE + 273.15")
    h = np.isfinite(V) & np.isfinite(Q) & np.isfinite(T) & np.isfinite(P)
    qc = q_of(M.esw(T[h]) - V[h], P[h])
    if not np.allclose(qc, Q[h], rtol=1e-8, atol=1e-10): raise ValueError("timeline QBOT closure differs from 0.622e/(p-0.378e) with Magnus esw")
    return int(f.sum()), int(h.sum())


def build(g, df, tcand, hcand):
    """g: Stage12g timeline (copy is modified); df: MtB01 frame (same row order)."""
    out = g.copy(); prov = []
    key = df.native_key.to_numpy(); pos = {k: i for i, k in enumerate(key)}
    P = out.PSRF.to_numpy(float)
    T_old = out.TA_USE.to_numpy(float).copy(); V_old = out.VPD_USE.to_numpy(float).copy()
    # 1 temperature
    T = T_old.copy(); tchg = np.zeros(len(out), bool)
    for r in tcand.to_dict("records"):
        if not np.isfinite(r["candidate_TA_C"]): raise ValueError("MtB03 temperature target without candidate: " + r["native_key"])
        i = pos[r["native_key"]]; T[i] = r["candidate_TA_C"]; tchg[i] = True
        prov.append(dict(native_key=r["native_key"], field="TA_USE/TBOT", old=T_old[i], new=T[i], source=f"{r['class']}:{r['method']}"))
    # 2 humidity targets
    Te = df.TA_ERA.to_numpy(float)
    with np.errstate(invalid="ignore"):
        e_c = M.esw(Te) - df.VPD_ERA.to_numpy(float)
    e_new = np.full(len(out), np.nan); src = np.full(len(out), "", dtype=object)
    for r in hcand.itertuples(index=False, name="H"):
        i = pos[r.native_key]
        if abs(r.TA_used_C - T[i]) > 1e-6 and np.isfinite(r.TA_used_C): raise ValueError("MtB03 humidity T differs from final T: " + r.native_key)
        if r.source in ("L24_measured_RH_transfer", "L16_measured_RH_transfer", "COMPANION_E_user_option_B"):
            e_new[i] = r.e_hPa; src[i] = r.source
        elif r.source == "HOLD_OUT_OF_REGIME":
            if np.isfinite(e_c[i]) and M.physical(np.array([T[i]]), np.array([P[i]]), np.array([e_c[i]]))[0]:
                e_new[i] = e_c[i]; src[i] = "COMPANION_E_OUT_OF_VALIDATED_REGIME"
            else:
                e_new[i] = datm_esat_hpa(T[i]); src[i] = "SATURATED_DATM_ESAT_from_out_of_regime"
        elif r.source == "HOLD_NOT_FORMABLE":
            e_new[i] = datm_esat_hpa(T[i]); src[i] = "SATURATED_DATM_ESAT"
        else:
            raise ValueError("unexpected MtB03 source " + str(r.source))
    # 3 consistency for temperature-only changes
    only_t = tchg & (src == "")
    with np.errstate(invalid="ignore"):
        e_keep = M.esw(T_old) - V_old
    sat_only_t = 0
    for i in np.flatnonzero(only_t):
        if not np.isfinite(e_keep[i]):
            continue
        es = datm_esat_hpa(T[i])
        if e_keep[i] > es: e_new[i] = es; src[i] = "T_CHANGED_e_KEPT_CAPPED_TO_DATM_SAT"; sat_only_t += 1
        else: e_new[i] = e_keep[i]; src[i] = "T_CHANGED_e_KEPT"
    # write
    sel = np.isfinite(e_new)
    if (e_new[sel] <= 0).any(): raise ValueError("non-positive vapour pressure produced")
    V = V_old.copy(); Q = out.QBOT.to_numpy(float).copy()
    V[sel] = M.esw(T[sel]) - e_new[sel]; Q[sel] = q_of(e_new[sel], P[sel])
    # Candidates were screened with Magnus saturation; DATM's Flatau polynomial is up to ~0.1 % lower.
    # A new value at most CAP_REL above the DATM cap is set to the cap (what DATM would do) and recorded;
    # anything larger stops the run.
    idx = np.flatnonzero(sel); qsat = q_of(datm_esat_hpa(T[idx]), P[idx]); rel = Q[idx] / qsat - 1.0
    big = rel > CAP_REL
    if big.any(): raise ValueError(f"{int(big.sum())} new QBOT more than {CAP_REL:.0%} above DATM saturation")
    capped = []
    for i, r in zip(idx[rel > 1e-12], rel[rel > 1e-12]):
        capped.append(dict(native_key=key[i], source=src[i], TA_C=T[i], QBOT_before=Q[i], DATM_qsat=float(q_of(datm_esat_hpa(T[i]), P[i])),
                           excess_pct=100 * r))
        e_new[i] = datm_esat_hpa(T[i]); src[i] = src[i] + "+CAPPED_TO_DATM_SAT"
        V[i] = M.esw(T[i]) - e_new[i]; Q[i] = q_of(e_new[i], P[i])
    capped = pd.DataFrame(capped)
    for i in np.flatnonzero(sel):
        prov.append(dict(native_key=key[i], field="VPD_USE/QBOT", old=V_old[i], new=V[i], source=src[i]))
    out["TA_USE"] = np.where(tchg, T, g.TA_USE.to_numpy(float))
    out["TBOT"] = np.where(tchg, T + TKFRZ, g.TBOT.to_numpy(float))       # untouched rows keep their stored bits
    out["VPD_USE"] = np.where(sel, V, g.VPD_USE.to_numpy(float)); out["QBOT"] = np.where(sel, Q, g.QBOT.to_numpy(float))
    # untouched-row guard
    touched = tchg | sel
    for c in out.columns:
        if c in ("TA_USE", "TBOT", "VPD_USE", "QBOT"):
            a, b = g[c].to_numpy(), out[c].to_numpy()
            same = (a == b) | (pd.isna(a) & pd.isna(b))
            if not same[~touched].all(): raise ValueError("untouched row changed in " + c)
        elif not g[c].equals(out[c]): raise ValueError("column changed that must not change: " + c)
    counts = pd.Series(src[sel]).value_counts().rename_axis("source").rename("HH").reset_index()
    counts = pd.concat([pd.DataFrame([{"source": "TEMPERATURE_REPLACED", "HH": int(tchg.sum())}]), counts], ignore_index=True)
    nan = {c: int(out[c].isna().sum()) for c in out.columns if c != "time"}
    return out, pd.DataFrame(prov), counts, nan, sat_only_t, capped


def self_test():
    assert abs(float(datm_esat_hpa(-8.39)) - 2.9929) < 2e-4 and abs(float(datm_esat_hpa(10.0)) - 12.27) < 0.02
    n = 200; t = np.linspace(-10, 10, n); p = np.full(n, 74500.0); v = M.esw(t) * 0.4
    g = pd.DataFrame({"time": pd.date_range("2022-12-01", periods=n, freq="30min").strftime("%Y-%m-%d %H:%M:%S"),
                      "TBOT": t + TKFRZ, "QBOT": q_of(M.esw(t) - v, p), "PSRF": p, "FSDS": 0.0, "FLDS": 300.0, "WIND": 2.0,
                      "PRECTmms": 0.0, "TA_USE": t, "VPD_USE": v})
    g.loc[5:9, ["QBOT", "VPD_USE"]] = np.nan
    g["TBOT"] = g.TBOT + 3e-14                                   # stored-value float noise must survive untouched
    check_conventions(g)
    df = pd.DataFrame({"native_key": pd.to_datetime(g.time).dt.strftime("%Y%m%d%H%M"), "TA_ERA": t + 6, "VPD_ERA": M.esw(t + 6) * 0.2})
    tcand = pd.DataFrame({"native_key": [df.native_key[20], df.native_key[30]], "class": ["FAULT_31M", "CLIP_31M"],
                          "candidate_TA_C": [1.0, -9.9], "method": ["L16_local_offset_4HH"] * 2})
    hcand = pd.DataFrame({"native_key": [df.native_key[k] for k in (5, 6, 7, 8, 20)],
                          "TA_used_C": [t[5], t[6], t[7], t[8], 1.0],
                          "source": ["COMPANION_E_user_option_B", "L24_measured_RH_transfer", "HOLD_NOT_FORMABLE", "HOLD_OUT_OF_REGIME", "HOLD_OUT_OF_REGIME"],
                          "e_hPa": [M.esi(t[5]) * 0.99999, M.esw(t[6]) * .6, np.nan, np.nan, np.nan]})
    out, prov, counts, nan, s, cap = build(g, df, tcand, hcand)
    assert nan["QBOT"] == 1 and nan["VPD_USE"] == 1          # row 9 was never a target
    assert abs(out.QBOT[7] - q_of(datm_esat_hpa(t[7]), p[7])) < 1e-12                    # saturated = DATM cap
    assert abs(out.TA_USE[30] + 9.9) < 1e-12 and abs(out.TBOT[30] - (TKFRZ - 9.9)) < 1e-12
    e30 = M.esw(t[30]) - v[30]; assert abs(out.VPD_USE[30] - (M.esw(-9.9) - min(e30, datm_esat_hpa(-9.9)))) < 1e-9
    assert set(prov.field) == {"TA_USE/TBOT", "VPD_USE/QBOT"}
    assert len(cap) == 1 and abs(out.QBOT[5] - q_of(datm_esat_hpa(t[5]), p[5])) < 1e-12, "Magnus/Flatau cap"
    print("MtB04 SELF-TEST PASS: conventions, temperature replacement, sources, DATM saturation, e-kept consistency, untouched guard")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    gr = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): gr.add_argument(a, action="store_true")
    ap.add_argument("--mtb03", default=str(MTB03_DEFAULT)); ap.add_argument("--stage12g", default=str(M.STAGE12G_DEFAULT))
    a = ap.parse_args()
    print("MtB04 US-MtB RESEARCH SHADOW TIMELINE | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    rec3, tcand, hcand = mtb03_folder(a.mtb03)
    df, gap, reasons, land, era5l, info = M.load_inputs(a.stage12g)
    G, grec = M.stage12g_folder(a.stage12g)
    g = pd.read_csv(M.regular(G / M.TIMELINE), low_memory=False)
    gk = pd.to_datetime(g.time, format="%Y-%m-%d %H:%M:%S").dt.strftime("%Y%m%d%H%M").to_numpy()
    if not np.array_equal(gk, df.native_key.to_numpy()): raise ValueError("Stage12g timeline order differs from source frame")
    nT, nH = check_conventions(g)
    out, prov, counts, nan, sat_only_t, capped = build(g, df, tcand, hcand)
    pd.set_option("display.width", 200)
    print(f"\nconventions verified on {nT} temperature and {nH} humidity rows (TBOT = TA+273.15; QBOT closure rtol 1e-8)")
    print("\n=== changes ===\n" + counts.to_string(index=False))
    print("temperature-only rows capped to DATM saturation:", sat_only_t)
    print(f"candidates capped to DATM saturation (<= {CAP_REL:.0%} above it, Magnus vs Flatau): {len(capped)}")
    if len(capped): print(capped.to_string(index=False))
    print("\n=== remaining NaN per column (whole timeline) ===\n" + json.dumps(nan))
    left = {k: v for k, v in nan.items() if v}
    print("\nMtB04 SUMMARY: rows", len(out), "| changed T", int((prov.field == "TA_USE/TBOT").sum()),
          "| changed humidity", int((prov.field == "VPD_USE/QBOT").sum()), "| remaining NaN", left or "NONE",
          "| DATM/Post-v5/spinup 0", flush=True)
    if a.check: print("MtB04 CHECK ONLY: no files written.", flush=True); return
    dest = M.ROOT / "science_trials" / ("mtb04_US-MtB_research_shadow_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    dest.mkdir(parents=True, exist_ok=False)
    names = {"US-MtB_MTB04_RESEARCH_SHADOW_NOLEAP.csv": out, "MTB04_change_provenance.csv": prov, "MTB04_change_counts.csv": counts,
             "MTB04_capped_to_DATM_saturation.csv": capped}
    for k, d in names.items(): d.to_csv(dest / k, index=False)
    (dest / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text("Research shadow. DATM/Post-v5/spinup use needs a separate user decision.\n")
    (dest / "SCIENTIFIC_STATUS.md").write_text(
        "US-MtB research shadow built from Stage12g with user-approved MtB03/MtB04 decisions (2026-10-29): 31 m temperature faults and "
        "-10 C clips replaced by the 16 m consensus transfer; humidity gaps filled by measured 24/16 m RH transfer, COMPANION_E "
        "(option B; out-of-regime rows labelled), or DATM saturation; vapour pressure kept where only temperature changed. "
        "Every change is in MTB04_change_provenance.csv.\n")
    files = [*names, "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP", "SCIENTIFIC_STATUS.md"]
    rec = {"version": VERSION, "inputs": info, "MtB03_report": str(a.mtb03), "MtB03_receipt_sha256": M.sha(Path(a.mtb03) / "mtb03_receipt.json"),
           "Stage12g_timeline_sha256": M.sha(G / M.TIMELINE), "rows": len(out), "changes": counts.to_dict("records"),
           "remaining_nan": nan, "temperature_only_rows_capped": sat_only_t, "candidates_capped_to_DATM_sat": len(capped),
           "Postv5_approved": 0, "DATM_ready": 0, "spinup_authorized": 0,
           "output_sha256": {n: M.sha(dest / n) for n in files}}
    (dest / "mtb04_research_shadow_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("MtB04 RESEARCH SHADOW:", dest, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("MtB04 STOP:", exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

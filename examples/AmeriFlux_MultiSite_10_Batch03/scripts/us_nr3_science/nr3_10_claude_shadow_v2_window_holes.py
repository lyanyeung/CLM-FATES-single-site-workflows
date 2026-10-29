#!/usr/bin/env python3
"""US-NR3 Stage10 (Claude): research shadow v2 - fill short holes inside measured-pair windows.
User decision 2026-10-29 ("是的，按照你的建议这么做"). Reads the verified Stage09 folder (receipt SHA checked);
writes only a NEW folder. Rules fixed before the run:

HOLE   a run of <= 2 HH that is not MEASURED_PAIR in Stage09 provenance and is bounded on BOTH sides by
       MEASURED_PAIR rows (a short BASE-triplet dropout inside a measured window).
FILL   TA_USE := linear interpolation in time of the bounding measured T*; e := linear interpolation of the
       bounding measured e; e capped at DATM saturation; VPD_USE = esw(TA_USE) - e; QBOT = 0.622e/(PSRF-0.378e);
       TBOT = TA_USE + 273.15. Label WINDOW_HOLE_INTERP (+_CAPPED).
GATE   applied only if 1- and 2-HH pseudo-holes inside measured windows (a measured row removed, rebuilt from
       its measured neighbours) give, for Dec-Mar rows: T MAE <= 0.5 C and e MAE <= 0.10 hPa. Otherwise STOP.
Every other row and column stays bit-identical to Stage09 (MAIN and SENSITIVITY each). Provenance v2 = Stage09
provenance with hole rows updated/added (old values = Stage12G values), so the handback verifier logic applies.
--self-test; --check prints; --run writes ONE science_trials/nr3_10_claude_research_shadow_v2_* folder.
"""
import argparse, hashlib, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "nr3-10-claude-v1-20261029-shadow-v2-window-holes"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S09 = "science_trials/nr3_09_claude_research_shadow_20261029T063921Z_6fdb9945"
NAMES = {"MAIN": ("US-NR3_NR3_09_MAIN_RESEARCH_SHADOW_NOLEAP.csv", "NR3_09_MAIN_provenance.csv"),
         "SENSITIVITY": ("US-NR3_NR3_09_SENSITIVITY_DRY_QC2_SHADOW_NOLEAP.csv", "NR3_09_SENSITIVITY_provenance.csv")}
MAX_HOLE = 2
A = (6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04, 3.031240396e-06, 2.034080948e-08, 6.136820929e-11)
B = (6.109177956, 5.034698970e-01, 1.886013408e-02, 4.176223716e-04, 5.824720280e-06, 4.838803174e-08, 1.838826904e-10)


def esw(t): t = np.asarray(t, float); return 6.112 * np.exp(17.67 * t / (t + 243.5))
def q_from_e(e, p): e = 100 * np.asarray(e, float); return 0.622 * e / (np.asarray(p, float) - 0.378 * e)
def datm(t):
    t = np.asarray(t, float); tc = np.clip(t, -50, 50); f = lambda k: k[0] + tc * (k[1] + tc * (k[2] + tc * (k[3] + tc * (k[4] + tc * (k[5] + tc * k[6])))))
    return np.where(t < 0, f(B), f(A))
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def holes(meas):
    """(start, length) of non-measured runs <= MAX_HOLE bounded by measured rows on both sides."""
    m = np.asarray(meas, bool); d = np.diff(np.r_[0, (~m).astype(int), 0]); s = np.flatnonzero(d == 1); e = np.flatnonzero(d == -1)
    return [(a, b - a) for a, b in zip(s, e) if b - a <= MAX_HOLE and a >= 1 and b <= len(m) - 1 and m[a - 1] and m[b]]


def fill(T, E, a, ln):
    """linear interpolation between rows a-1 and a+ln."""
    i0, i1 = a - 1, a + ln; w = (np.arange(a, a + ln) - i0) / (i1 - i0)
    return T[i0] + (T[i1] - T[i0]) * w, E[i0] + (E[i1] - E[i0]) * w


def pseudo(T, E, meas, month):
    """remove 1 or 2 measured rows with measured neighbours; rebuild; errors for Dec-Mar rows."""
    out = []
    for ln in (1, 2):
        ok = np.ones(len(T) - ln - 1, bool)
        for k in range(ln + 2): ok &= meas[k: len(T) - ln - 1 + k]
        a = np.flatnonzero(ok) + 1
        for k in range(ln):
            i = a + k; w = (k + 1) / (ln + 1)
            tp = T[a - 1] + (T[a + ln] - T[a - 1]) * w; ep = E[a - 1] + (E[a + ln] - E[a - 1]) * w
            cold = np.isin(month[i], [12, 1, 2, 3])
            out.append(pd.DataFrame({"hole_HH": ln, "cold": cold, "dT": tp - T[i], "de": ep - E[i]}))
    P = pd.concat(out, ignore_index=True)
    r = P.groupby(["hole_HH", "cold"]).agg(N=("dT", "size"), T_MAE=("dT", lambda x: x.abs().mean()), T_bias=("dT", "mean"),
                                          e_MAE=("de", lambda x: x.abs().mean()), e_bias=("de", "mean")).reset_index()
    c = P.loc[P.cold]
    return r, dict(T_MAE_cold=float(c.dT.abs().mean()), e_MAE_cold=float(c.de.abs().mean()), N_cold=int(len(c)))


def build(s, prov, keys):
    out = s.copy(); pos = {k: i for i, k in enumerate(keys)}
    meas = np.zeros(len(s), bool); meas[[pos[k] for k in prov.loc[prov.label.str.startswith("MEASURED"), "native_key"]]] = True
    T = s.TA_USE.to_numpy(float).copy(); P = s.PSRF.to_numpy(float); E = esw(T) - s.VPD_USE.to_numpy(float)
    H = holes(meas); rows = []
    Tn, En = T.copy(), E.copy(); lab = {}
    for a, ln in H:
        t, e = fill(T, E, a, ln)
        for k in range(ln):
            i = a + k; es = float(datm(t[k])); cap = e[k] > es
            Tn[i] = t[k]; En[i] = min(e[k], es); lab[i] = "WINDOW_HOLE_INTERP" + ("_CAPPED" if cap else "")
    idx = np.array(sorted(lab), int)
    if len(idx):
        out.loc[idx, "TA_USE"] = Tn[idx]
        if "TBOT" in out: out.loc[idx, "TBOT"] = Tn[idx] + 273.15
        out.loc[idx, "VPD_USE"] = esw(Tn[idx]) - En[idx]; out.loc[idx, "QBOT"] = q_from_e(En[idx], P[idx])
    touched = np.zeros(len(s), bool); touched[idx] = True
    for c in s.columns:
        a_, b_ = s[c].to_numpy(), out[c].to_numpy(); same = (a_ == b_) | (pd.isna(a_) & pd.isna(b_))
        if not same[~touched].all(): raise ValueError("untouched Stage09 row changed in " + c)
    V = out.VPD_USE.to_numpy(float); Q = out.QBOT.to_numpy(float)
    if not np.allclose(q_from_e(esw(Tn[idx]) - V[idx], P[idx]), Q[idx], rtol=1e-8): raise ValueError("closure")
    if (Q[idx] > q_from_e(datm(Tn[idx]), P[idx]) * (1 + 1e-9)).any() or (V[idx] < -1e-9).any(): raise ValueError("saturation")
    pv = prov.set_index("native_key").copy()
    for i in idx:
        k = keys[i]
        if k in pv.index:
            pv.loc[k, ["label", "T_changed", "new_TA_USE", "new_VPD_USE", "new_QBOT"]] = [pv.loc[k, "label"] + ">" + lab[i], True, Tn[i], V[i], Q[i]]
        else:
            pv.loc[k] = dict(label=lab[i], T_changed=True, old_TA_USE=T[i], new_TA_USE=Tn[i], old_VPD_USE=s.VPD_USE.iloc[i], new_VPD_USE=V[i],
                             old_QBOT=s.QBOT.iloc[i], new_QBOT=Q[i], in_238=False)
    pv = pv.reset_index().rename(columns={"index": "native_key"})
    # edge steps before / after
    def steps(TT, m):
        e = np.flatnonzero(np.diff(m.astype(int)) != 0); j = np.abs(TT[e + 1] - TT[e]); return dict(edges=int(len(e)), gt3C=int((j > 3).sum()), max_C=float(j.max()) if len(j) else 0.0)
    m2 = meas.copy(); m2[idx] = True
    return out, pv, dict(holes=len(H), hole_rows=int(len(idx)), capped=int(sum(v.endswith("CAPPED") for v in lab.values())),
                         in_238=int(np.isin(keys[idx], prov.loc[prov.in_238, "native_key"]).sum()),
                         before=steps(T, meas), after=steps(out.TA_USE.to_numpy(float), m2)), (T, E, meas)


def self_test():
    n = 40; t = pd.date_range("2017-01-01", periods=n, freq="30min"); k = np.asarray(t.strftime("%Y%m%d%H%M"))
    T = np.full(n, -12.0); T[[10, 20, 21]] = -25.0; P = np.full(n, 65000.0); V = esw(T) * 0.2
    s = pd.DataFrame({"time": t.strftime("%Y-%m-%d %H:%M:%S"), "TBOT": T + 273.15, "QBOT": q_from_e(esw(T) - V, P), "PSRF": P, "TA_USE": T, "VPD_USE": V})
    lab = np.array(["MEASURED_PAIR_TSTAR_RH"] * n, dtype=object); lab[[10, 20, 21]] = "X"; lab[30:34] = "X"
    prov = pd.DataFrame({"native_key": k, "label": lab, "T_changed": True, "old_TA_USE": T, "new_TA_USE": T, "old_VPD_USE": V, "new_VPD_USE": V,
                         "old_QBOT": 0.0, "new_QBOT": 0.0, "in_238": False}).loc[lambda x: x.label.str.startswith("MEASURED")]
    out, pv, st, _ = build(s, prov, k)
    assert st["holes"] == 2 and st["hole_rows"] == 3 and abs(out.TA_USE[10] + 12) < 1e-12 and abs(out.TA_USE[31] - T[31]) < 1e-12
    assert st["before"]["gt3C"] == 4 and st["after"]["gt3C"] == 0
    print("NR3_10 SELF-TEST PASS: hole detection (<= 2 HH, bounded), interpolation, untouched guard, provenance", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args()
    print("NR3_10 CLAUDE SHADOW v2 (WINDOW HOLES) | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    d9 = a.root / S09
    rec = json.loads((d9 / "nr3_09_research_shadow_receipt.json").read_text())
    for n_, h in rec["output_sha256"].items():
        if sha(d9 / n_) != h: raise ValueError("Stage09 output SHA mismatch: " + n_)
    res = {}
    for nm, (csv, pcsv) in NAMES.items():
        s = pd.read_csv(d9 / csv, low_memory=False); prov = pd.read_csv(d9 / pcsv, dtype={"native_key": str})
        keys = np.asarray(pd.to_datetime(s.time.str.replace("T", " ")).dt.strftime("%Y%m%d%H%M"))
        out, pv, st, (T, E, meas) = build(s, prov, keys)
        if nm == "MAIN":
            R, gstat = pseudo(T, E, meas, pd.to_datetime(s.time.str.replace("T", " ")).dt.month.to_numpy())
            print("\n=== pseudo-hole validation inside measured windows ===\n" + R.round(3).to_string(index=False))
            print("GATE", json.dumps(gstat))
            if not (gstat["T_MAE_cold"] <= 0.5 and gstat["e_MAE_cold"] <= 0.10): raise ValueError("pseudo-hole gate fails; v2 not applied: " + json.dumps(gstat))
        print(f"{nm}_V2", json.dumps(st)); res[nm] = (out, pv, st)
    h = res["MAIN"][1].loc[res["MAIN"][1].label.str.contains("WINDOW_HOLE")]
    ex = h.loc[h.native_key.isin(["201702260030", "201612080630", "201612080730", "201901020930"])]
    print("\n=== examples ===\n" + ex[["native_key", "label", "old_TA_USE", "new_TA_USE", "new_VPD_USE", "in_238"]].round(3).to_string(index=False))
    print(f"\nNR3_10 SUMMARY: MAIN hole rows {res['MAIN'][2]['hole_rows']} | edges >3 C {res['MAIN'][2]['before']['gt3C']} -> {res['MAIN'][2]['after']['gt3C']} "
          f"| max step {res['MAIN'][2]['before']['max_C']:.2f} -> {res['MAIN'][2]['after']['max_C']:.2f} C | DATM 0", flush=True)
    if a.check: print("NR3_10 CHECK ONLY: no files written.", flush=True); return
    dest = a.root / "science_trials" / ("nr3_10_claude_research_shadow_v2_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    dest.mkdir(parents=True, exist_ok=False)
    files = {"US-NR3_NR3_10_MAIN_RESEARCH_SHADOW_V2_NOLEAP.csv": res["MAIN"][0], "NR3_10_MAIN_provenance.csv": res["MAIN"][1],
             "US-NR3_NR3_10_SENSITIVITY_DRY_QC2_SHADOW_V2_NOLEAP.csv": res["SENSITIVITY"][0], "NR3_10_SENSITIVITY_provenance.csv": res["SENSITIVITY"][1]}
    for k, v in files.items(): v.to_csv(dest / k, index=False)
    (dest / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text("Research shadows v2. DATM/Post-v5/spinup use needs a separate user decision.\n")
    (dest / "SCIENTIFIC_STATUS.md").write_text("Stage09 shadows plus WINDOW_HOLE_INTERP: <= 2 HH BASE-triplet dropouts inside measured windows filled by linear "
                                               "interpolation of the bounding measured T* and e. All other rows bit-identical to Stage09.\n")
    names = [*files, "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP", "SCIENTIFIC_STATUS.md"]
    r2 = {"version": VERSION, "stage09_folder": str(d9), "stage09_receipt_sha256": sha(d9 / "nr3_09_research_shadow_receipt.json"),
          "MAIN": res["MAIN"][2], "SENSITIVITY": res["SENSITIVITY"][2], "Postv5_approved": 0, "DATM_ready": 0, "spinup_authorized": 0,
          "output_sha256": {n_: sha(dest / n_) for n_ in names}}
    (dest / "nr3_10_research_shadow_v2_receipt.json").write_text(json.dumps(r2, indent=2, default=str) + "\n")
    print("NR3_10 RESEARCH SHADOW V2:", dest, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("NR3_10 STOP:", type(exc).__name__, exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

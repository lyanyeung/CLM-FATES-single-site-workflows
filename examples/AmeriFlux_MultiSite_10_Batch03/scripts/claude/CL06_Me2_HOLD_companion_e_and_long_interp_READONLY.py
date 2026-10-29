#!/usr/bin/env python3
"""CL06 (Claude, US-Me2 only): candidates for the CL05 HOLD rows (warm-season non-physical / implausibly dry MDS or
ERA humidity). User decision 2026-10-29 ("是的，按照你的建议这么做"). READ ONLY.

Imports CL05 (pinned blob 15473b52...), which imports CL04 (pinned) for the SHA-pinned FULLSET/ERA5-Land loader;
re-runs the CL05 scan (must reproduce its HOLD set) and adds, with rules fixed before the run:
  CEC        companion ERA vapour pressure e = esw(TA_ERA) - VPD_ERA (> 0 only) paired with the retained tower TA_F,
             capped at DATM saturation at TA_F. Validated on Me2 dual-QC0 truth in the first of (month, TA_F bin) ->
             (season, bin) -> (bin) with N_valid >= 100, Stage12j gates (incl. valid fraction >= 0.6).
  INTERP_L   e interpolated across the actual run (length L HH) between dual-QC0 anchors <= 4 HH from both edges,
             capped at DATM saturation; validated with pseudo-gaps of the same length L, all L rows scored, per TA_F
             bin, Stage12j gates (N >= 100).
DECISION per HOLD row: among the formable methods that pass, the lower validation MAE; else HOLD. Temperature is
never changed. APPROVED_FOR_NEW_VERSION = False.
--self-test; --check prints; --run also writes ONE reports/cl06_US-Me2_HOLD_alternatives_* folder.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-CL06-v1-20261029-Me2-HOLD-CEC-longINTERP-READONLY"
HERE = Path(__file__).resolve().parent
C5_SCRIPT = HERE / "CL05.py" if (HERE / "CL05.py").is_file() else HERE / "CL05_Me2_full_record_nonphysical_humidity_scan_READONLY.py"
C5_BLOB = "15473b52e509e03f73a44d78b04533a5aec2114d"


def load_c5():
    b = C5_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != C5_BLOB:
        raise ValueError("Pinned CL05 Git blob mismatch: " + str(C5_SCRIPT))
    spec = importlib.util.spec_from_file_location("cl05_for_cl06", C5_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


C5 = load_c5()
C4 = C5.C4
esw, esi, datm, tbin, stats, gate = C4.esw, C4.esi, C4.datm, C4.tbin, C4.stats, C4.gate
RANK = C5.RANK


def strata_table(f, T, et, truth, est):
    tb = tbin(T); mo = f.month.to_numpy(); se = f.month.map(C5.SEASON).to_numpy(); err = est - et; res = {}
    for lvl, key in (("month+bin", list(zip(mo, tb))), ("season+bin", list(zip(se, tb))), ("bin", list(tb))):
        kk = np.empty(len(key), dtype=object); kk[:] = key
        df = pd.DataFrame({"k": kk[truth], "err": err[truth], "et": et[truth]})
        res[lvl] = (kk, {g: stats(x.err.to_numpy(), x.et.to_numpy()) for g, x in df.groupby("k")})
    return res


def interp_L_validation(T, et, truth, L):
    n = len(T); e_obs = np.where(truth, et, np.nan); ok = np.ones(n - L + 1, bool)
    for k in range(L): ok &= truth[k: n - L + 1 + k]
    s0 = np.flatnonzero(ok); err = np.full(n, np.nan)
    for k in range(L):
        i = s0 + k; e = C4.interp(e_obs, truth.copy(), s0, s0 + L - 1, i, T[i]); err[i] = np.where(np.isnan(err[i]), e - et[i], err[i])
    tb = tbin(T); out = {}
    for b in C4.T_LAB:
        s = truth & (tb == b); r = stats(err[s], et[s]); r["gate"] = gate(r) if r.get("N_valid") else False; out[b] = r
    return out


def analyse(f, D5):
    T, V, et, nonphys, dry, qc, truth, target = C5.scan(f)
    hold = D5.loc[D5.decision == "HOLD"].copy()
    pos = {k: i for i, k in enumerate(f.TIMESTAMP_START)}
    hi_idx = np.array([pos[k] for k in hold.TIMESTAMP_START], int)
    with np.errstate(invalid="ignore"):
        ec = esw(f.TA_ERA.to_numpy(float)) - f.VPD_ERA.to_numpy(float)
    cec = np.where(ec > 0, np.minimum(ec, datm(T)), np.nan)
    ST = strata_table(f, T, et, truth, cec)
    lo = np.zeros(len(f), int); hi = np.zeros(len(f), int)
    for s, ln in C5.runs(target): lo[s:s + ln] = s; hi[s:s + ln] = s + ln - 1
    Ls = sorted(set(int(hi[i] - lo[i] + 1) for i in hi_idx))
    IV = {L: interp_L_validation(T, et, truth, L) for L in Ls}
    e_obs = np.where(truth, et, np.nan)
    e_int = C4.interp(e_obs, truth.copy(), lo[hi_idx], hi[hi_idx], hi_idx, T[hi_idx])
    tb = tbin(T); rows = []
    for j, i in enumerate(hi_idx):
        L = int(hi[i] - lo[i] + 1); x = hold.iloc[j][["TIMESTAMP_START", "source_row", "year", "month", "TA_F", "VPD_F", "VPD_F_QC", "e_tower", "flag", "run_HH"]].to_dict()
        x.update(TA_ERA=f.TA_ERA.iloc[i], VPD_ERA=f.VPD_ERA.iloc[i], e_ERA_pair=ec[i], CEC_e=cec[i], INTERP_e=e_int[j], T_bin=tb[i])
        opts = []
        lvl, r = C5.pick(ST, i); x["CEC_level"] = lvl; x["CEC_MAE"] = r.get("MAE_hPa", np.nan); x["CEC_rel"] = r.get("median_rel", np.nan); x["CEC_gate"] = bool(r and gate(r))
        if np.isfinite(cec[i]) and x["CEC_gate"]: opts.append((r["MAE_hPa"], "CEC", cec[i]))
        iv = IV[L][tb[i]]; x["INTERP_MAE"] = iv.get("MAE_hPa", np.nan); x["INTERP_gate"] = bool(iv["gate"])
        if np.isfinite(e_int[j]) and iv["gate"]: opts.append((iv["MAE_hPa"], f"INTERP_{L}HH", e_int[j]))
        if opts:
            mae, dec, e = sorted(opts)[0]; why = f"{dec} validated (MAE {mae:.3f})"
        else:
            dec, e = "HOLD", np.nan
            why = "; ".join([("CEC not formable" if not np.isfinite(cec[i]) else ("CEC stratum fails" if not x["CEC_gate"] else "")),
                             ("INTERP not formable (anchors)" if not np.isfinite(e_int[j]) else ("INTERP fails" if not iv["gate"] else ""))]).strip("; ")
        x.update(decision=dec, rationale=why, e_proposed=e, VPD_proposed=esw(T[i]) - e if np.isfinite(e) else np.nan,
                 RH_proposed_pct=100 * e / esw(T[i]) if np.isfinite(e) else np.nan, APPROVED_FOR_NEW_VERSION=False)
        rows.append(x)
    D = pd.DataFrame(rows)
    IVt = pd.DataFrame([dict(L=L, T_bin=b, **r) for L, d in IV.items() for b, r in d.items()])
    cs = pd.DataFrame([dict(level=l, key=str(k), **r) for l, (kk, d) in ST.items() for k, r in d.items()])
    return D, IVt, cs


def self_test():
    n = 4000; t = pd.date_range("2011-07-01", periods=n, freq="30min")
    T = 12 + 6 * np.sin(np.arange(n) / 48 * 2 * np.pi); e = 0.5 * esw(T)
    f = pd.DataFrame({"TIMESTAMP_START": t.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0, "VPD_F": esw(T) - e, "VPD_F_QC": 0, "grid_D": np.nan,
                      "TA_ERA": T + 1, "VPD_ERA": esw(T + 1) - e * 1.02, "row": np.arange(n) + 2})
    f["year"], f["month"], f["hour"] = t.year, t.month, t.hour; f["hblock"] = f.hour // 3
    f.loc[2000:2009, "VPD_F"] = esw(T[2000:2010]) + .3; f.loc[2000:2009, "VPD_F_QC"] = 1
    D5, s, I = C5.analyse(f); D5["decision"] = "HOLD"
    D, IVt, cs = analyse(f, D5)
    assert len(D) == 10 and D.decision.isin(["CEC", "INTERP_10HH"]).all(), D[["decision", "rationale"]]
    print("CL06 SELF-TEST PASS: CEC stratum validation, length-L pseudo-gap INTERP, decision", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--root", type=Path, default=C4.ROOT)
    a = ap.parse_args()
    print("CL06 US-Me2 HOLD ALTERNATIVES (CEC / LONG INTERP) | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    f, info, bcols = C4.load(a.root)
    D5, s5, I5 = C5.analyse(f)
    if int((D5.decision == "HOLD").sum()) != 243 or int((D5.decision == "EMP_LOYO").sum()) != 122: raise ValueError("CL05 result not reproduced (243 HOLD / 122 EMP)")
    D, IVt, cs = analyse(f, D5)
    pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    print("\nCL06_INPUT", json.dumps(dict(hold=len(D), cl05_emp=122)), flush=True)
    print("\n=== decisions ===\n" + D.groupby(["flag", "decision"]).size().rename("HH").reset_index().to_string(index=False))
    print("\n=== decisions by year ===\n" + D.pivot_table(index="year", columns="decision", values="source_row", aggfunc="count", fill_value=0).to_string())
    r = D.assign(dt=pd.to_datetime(D.TIMESTAMP_START, format="%Y%m%d%H%M")); r["run"] = r.dt.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    runs = r.groupby("run").agg(start=("TIMESTAMP_START", "first"), end=("TIMESTAMP_START", "last"), HH=("TIMESTAMP_START", "size"), TA_min=("TA_F", "min"), TA_max=("TA_F", "max"),
                                CEC_MAE=("CEC_MAE", "first"), CEC_gate=("CEC_gate", "first"), INTERP_MAE=("INTERP_MAE", "first"),
                                decisions=("decision", lambda x: ",".join(f"{k}:{v}" for k, v in x.value_counts().items())),
                                VPD_new=("VPD_proposed", lambda x: f"{x.min():.2f}-{x.max():.2f}" if x.notna().any() else "-"))
    print("\n=== runs ===\n" + runs.round(3).to_string(index=False))
    print("\n=== INTERP_L validation (L used) ===\n" + IVt[["L", "T_bin", "N_valid", "MAE_hPa", "bias_hPa", "median_rel", "gate"]].dropna(subset=["MAE_hPa"]).round(3).to_string(index=False))
    print(f"\nCL06 SUMMARY: {len(D)} former HOLD | " + " | ".join(f"{k}={v}" for k, v in D.decision.value_counts().items()) + " | approved 0", flush=True)
    for p, h in C4.READS.items():
        if C4.sha(p) != h: raise ValueError("input changed during audit: " + p)
    if a.check: print("CL06 CHECK ONLY: no files written.", flush=True); return
    out = a.root / "reports" / ("cl06_US-Me2_HOLD_alternatives_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"Me2_HOLD_alternatives.csv": D, "Me2_HOLD_runs.csv": runs, "INTERP_L_validation.csv": IVt, "CEC_strata_validation.csv": cs}
    for k, v in files.items(): v.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("Read-only alternatives ledger. Nothing approved; no Me2 forcing was written.\n")
    rec = {"version": VERSION, "c5_blob": C5_BLOB, "inputs_sha256": C4.READS, "decisions": D.decision.value_counts().to_dict(), "approved": 0,
           "output_sha256": {n: C4.sha(out / n) for n in [*files, "SCIENTIFIC_HOLD.md"]}}
    (out / "cl06_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("CL06 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("CL06 STOP:", type(exc).__name__, exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

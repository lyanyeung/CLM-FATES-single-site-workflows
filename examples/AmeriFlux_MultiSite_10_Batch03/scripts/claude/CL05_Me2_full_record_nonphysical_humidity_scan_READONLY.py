#!/usr/bin/env python3
"""CL05 (Claude, US-Me2 only): full-record scan of non-physical tower humidity pairs and predeclared candidates.
READ ONLY. Imports CL04 (pinned blob a15cd5ce...) for the SHA-pinned FULLSET/ERA5-Land loader and helpers.

User decision 2026-10-29: the four legacy events use EMP_LOYO (CL04); scan the whole 2002-2022 record the same way.

FLAGS (every row, e = esw(TA_F) - VPD_F; phase saturation = esi below 0 C, esw above):
  NONPHYSICAL      e <= 0 or VPD_F < 0
  IMPLAUSIBLY_DRY  0 < e and e / esat_phase < 0.05 (RH below 5 %)
  Rows with VPD_F_QC = 0 are counted separately (measured; never proposed for change).
CANDIDATES for flagged VPD_F_QC in {1, 2} rows (rule fixed here; temperature never changed):
  1 INTERP    run <= 4 HH, dual-QC0 anchors <= 4 HH from both edges, its TA_F bin passes the 4-HH pseudo-gap
              validation (Stage12j gates, N >= 100)
  2 STRATUM   EMP_LOYO (QC0 RH climatology, whole year excluded) or GRID_A (ERA5-Land, where the file exists),
              validated on dual-QC0 in the first of (month, TA_F bin) -> (season, bin) -> (bin) with N_valid >= 100
              (Stage12j gates incl. valid fraction >= 0.6); the finer validated level wins, MAE breaks ties within a level; e above DATM saturation is set to it (DATM-equivalent, flagged)
  3 HOLD
The four CL04 events must come out as EMP_LOYO, else STOP (consistency with the decided values).
--self-test; --check prints; --run also writes ONE reports/cl05_US-Me2_nonphysical_scan_* folder. No forcing writes.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-CL05-v1-20261029-Me2-full-record-scan-READONLY"
HERE = Path(__file__).resolve().parent
C4_SCRIPT = HERE / "CL04.py" if (HERE / "CL04.py").is_file() else HERE / "CL04_Me2_four_humidity_events_READONLY.py"
C4_BLOB = "a15cd5ceb8f1806e5349a253602adfc97c7356ac"
RANK = {"month+bin": 0, "season+bin": 1, "bin": 2}   # finer validated stratum wins; MAE only compared within a level
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM", 6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}


def load_c4():
    b = C4_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != C4_BLOB:
        raise ValueError("Pinned CL04 Git blob mismatch: " + str(C4_SCRIPT))
    spec = importlib.util.spec_from_file_location("cl04_for_cl05", C4_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


C4 = load_c4()
esw, esi, datm, tbin, stats, gate = C4.esw, C4.esi, C4.datm, C4.tbin, C4.stats, C4.gate


def runs(mask):
    m = np.asarray(mask, bool); d = np.diff(np.r_[0, m.astype(int), 0]); s = np.flatnonzero(d == 1); e = np.flatnonzero(d == -1)
    return list(zip(s, e - s))


def scan(f):
    T = f.TA_F.to_numpy(float); V = f.VPD_F.to_numpy(float); e = esw(T) - V
    es_ph = np.where(T < 0, esi(T), esw(T))
    nonphys = np.isfinite(e) & ((e <= 0) | (V < 0))
    dry = np.isfinite(e) & (e > 0) & (e / es_ph < 0.05) & ~nonphys
    qc = f.VPD_F_QC.to_numpy(float)
    truth = (f.TA_F_QC == 0).to_numpy() & (qc == 0) & np.isfinite(e) & (e > 0) & (V >= 0)
    target = (nonphys | dry) & np.isin(qc, [1, 2])
    return T, V, e, nonphys, dry, qc, truth, target


def validate(f, T, e, truth, cand):
    tb = tbin(T); mo = f.month.to_numpy(); se = f.month.map(SEASON).to_numpy()
    out = {}
    for k in ("EMP_LOYO", "GRID_A"):
        err = cand[k] - e; res = {}
        for lvl, key in (("month+bin", list(zip(mo, tb))), ("season+bin", list(zip(se, tb))), ("bin", list(tb))):
            kk = np.empty(len(key), dtype=object); kk[:] = key
            df = pd.DataFrame({"k": kk[truth], "err": err[truth], "et": e[truth]})
            res[lvl] = (kk, {g: stats(x.err.to_numpy(), x.et.to_numpy()) for g, x in df.groupby("k")})
        out[k] = res
    return out


def pick(res, i):
    for lvl in ("month+bin", "season+bin", "bin"):
        kk, d = res[lvl]; r = d.get(kk[i])
        if r and r.get("N_valid", 0) >= 100: return lvl, r
    return "", {}


def analyse(f):
    T, V, e, nonphys, dry, qc, truth, target = scan(f)
    pool = f.loc[truth, ["month", "hblock"]].assign(Tb=tbin(T[truth]))
    cand = {"EMP_LOYO": C4.emp_loyo(pool, e[truth] / esw(T[truth]), f.year.to_numpy()[truth], f[["month", "hblock"]].assign(Tb=tbin(T)), f.year.to_numpy()) * esw(T),
            "GRID_A": esw(f.grid_D.to_numpy(float))}
    # 4-HH pseudo-gap INTERP validation by TA_F bin
    e_obs = np.where(truth, e, np.nan); n = len(f); s0 = np.flatnonzero(truth[:-3] & truth[1:-2] & truth[2:-1] & truth[3:])
    ip = np.full(n, np.nan)
    for k in range(4):
        i = s0 + k; ip[i] = np.where(np.isnan(ip[i]), C4.interp(e_obs, truth.copy(), s0, s0 + 3, i, T[i]), ip[i])
    tb = tbin(T); ival = {}
    for b in C4.T_LAB:
        s = truth & (tb == b); r = stats((ip - e)[s], e[s]); r["gate"] = gate(r) if r.get("N_valid") else False; ival[b] = r
    VS = validate(f, T, e, truth, cand)
    lo = np.zeros(n, int); hi = np.zeros(n, int)
    for s, ln in runs(target): lo[s:s + ln] = s; hi[s:s + ln] = s + ln - 1
    anchor = truth.copy()
    rows = []
    idx = np.flatnonzero(target)
    e_int = C4.interp(e_obs, anchor, lo[idx], hi[idx], idx, T[idx])
    for j, i in enumerate(idx):
        L = int(hi[i] - lo[i] + 1); x = dict(TIMESTAMP_START=f.TIMESTAMP_START.iloc[i], source_row=int(f.row.iloc[i]), year=int(f.year.iloc[i]), month=int(f.month.iloc[i]),
                                           TA_F=T[i], TA_F_QC=f.TA_F_QC.iloc[i], VPD_F=V[i], VPD_F_QC=qc[i], e_tower=e[i], flag="NONPHYSICAL" if nonphys[i] else "IMPLAUSIBLY_DRY",
                                           run_HH=L, T_bin=tb[i])
        dec, ee, why = "HOLD", np.nan, "no validated candidate"
        if L <= 4 and np.isfinite(e_int[j]) and ival[tb[i]]["gate"]:
            dec, ee, why = "INTERP", e_int[j], f"dual-QC0 anchors <= 4 HH; bin {tb[i]} pseudo-gap MAE {ival[tb[i]]['MAE_hPa']:.3f}"
        else:
            ok = []
            for k in ("EMP_LOYO", "GRID_A"):
                if not np.isfinite(cand[k][i]): continue
                lvl, r = pick(VS[k], i); x[k + "_e"] = cand[k][i]; x[k + "_level"] = lvl; x[k + "_MAE"] = r.get("MAE_hPa", np.nan); x[k + "_rel"] = r.get("median_rel", np.nan)
                if r and gate(r): ok.append((RANK[lvl], r["MAE_hPa"], k, lvl))
            if ok:
                _, mae, k, lvl = sorted(ok)[0]; dec, ee, why = k, cand[k][i], f"{k} validated at {lvl} (MAE {mae:.3f})"
        cap = ""
        if np.isfinite(ee) and ee > float(datm(T[i])): cap = f"CAPPED_{100 * ee / float(datm(T[i])) - 100:.1f}%"; ee = float(datm(T[i]))
        x.update(decision=dec, rationale=why, cap_flag=cap, e_proposed=ee, VPD_proposed=esw(T[i]) - ee if np.isfinite(ee) else np.nan,
                 RH_phase_proposed_pct=100 * ee / (esi(T[i]) if T[i] < 0 else esw(T[i])) if np.isfinite(ee) else np.nan, APPROVED_FOR_NEW_VERSION=False)
        rows.append(x)
    D = pd.DataFrame(rows)
    summ = dict(rows=n, dual_QC0_truth=int(truth.sum()), nonphysical_all=int(nonphys.sum()), implausibly_dry_all=int(dry.sum()),
                flagged_QC0=int(((nonphys | dry) & (qc == 0)).sum()), flagged_QC1=int(((nonphys | dry) & (qc == 1)).sum()), flagged_QC2=int(((nonphys | dry) & (qc == 2)).sum()),
                targets=int(target.sum()), target_runs=len(runs(target)))
    I = pd.DataFrame([dict(T_bin=b, **{k: v for k, v in r.items()}) for b, r in ival.items()])
    return D, summ, I


def self_test():
    n = 3000; t = pd.date_range("2013-12-01", periods=n, freq="30min")
    T = -8 + 3 * np.sin(np.arange(n) / 48 * 2 * np.pi); e = 0.8 * esw(T)
    f = pd.DataFrame({"TIMESTAMP_START": t.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0, "VPD_F": esw(T) - e, "VPD_F_QC": 0, "grid_D": T - 2, "row": np.arange(n) + 2})
    f["year"], f["month"], f["hour"] = t.year, t.month, t.hour; f["hblock"] = f.hour // 3
    f.loc[1000:1001, "VPD_F"] = esw(T[1000:1002]) + .2; f.loc[1000:1001, "VPD_F_QC"] = 1                 # short nonphysical run -> INTERP
    f.loc[2000:2019, "VPD_F"] = esw(T[2000:2020]) * .999; f.loc[2000:2019, "VPD_F_QC"] = 1               # long implausibly dry run -> stratum
    f.loc[500, "VPD_F"] = esw(T[500]) + .1                                                               # QC0 nonphysical: counted, never targeted
    D, s, I = analyse(f)
    assert s["flagged_QC0"] == 1 and s["targets"] == 22 and set(D.flag) == {"NONPHYSICAL", "IMPLAUSIBLY_DRY"}
    assert (D.loc[D.run_HH == 2, "decision"] == "INTERP").all() and D.loc[D.run_HH == 20, "decision"].isin(["EMP_LOYO", "GRID_A"]).all(), D[["run_HH", "decision"]]
    print("CL05 SELF-TEST PASS: flags, QC0 protection, INTERP vs stratum decision", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--root", type=Path, default=C4.ROOT)
    a = ap.parse_args()
    print("CL05 US-Me2 FULL-RECORD NONPHYSICAL HUMIDITY SCAN | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    f, info, bcols = C4.load(a.root)
    D, s, I = analyse(f)
    ev = D.loc[D.TIMESTAMP_START.isin(C4.EVENTS)]
    if len(ev) != 4 or not (ev.decision == "EMP_LOYO").all(): raise ValueError("the four CL04 events are not reproduced as EMP_LOYO: " + ev.decision.tolist().__repr__())
    pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    print("CL05_SCAN", json.dumps(s), flush=True)
    print("\n=== flagged QC1/QC2 targets by year ===\n" + D.pivot_table(index="year", columns="flag", values="source_row", aggfunc="count", fill_value=0).to_string())
    print("\n=== decisions ===\n" + D.groupby(["flag", "decision"]).size().rename("HH").reset_index().to_string(index=False))
    print("\n=== decisions by year ===\n" + D.pivot_table(index="year", columns="decision", values="source_row", aggfunc="count", fill_value=0).to_string())
    print("\n=== INTERP 4-HH pseudo-gap validation by TA_F bin ===\n" + I[["T_bin", "N_valid", "MAE_hPa", "bias_hPa", "median_rel", "gate"]].round(3).to_string(index=False))
    r = D.assign(dt=pd.to_datetime(D.TIMESTAMP_START, format="%Y%m%d%H%M")); r["run"] = r.dt.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    top = r.groupby("run").agg(start=("TIMESTAMP_START", "first"), end=("TIMESTAMP_START", "last"), HH=("TIMESTAMP_START", "size"), TA_min=("TA_F", "min"), TA_max=("TA_F", "max"),
                               QC=("VPD_F_QC", lambda x: "/".join(str(int(v)) for v in sorted(x.unique()))), decisions=("decision", lambda x: ",".join(f"{k}:{v}" for k, v in x.value_counts().items()))).sort_values("HH", ascending=False)
    print("\n=== 20 longest flagged runs ===\n" + top.head(20).round(1).to_string(index=False))
    print("\n=== the four CL04 events (must equal CL04) ===\n" + ev[["TIMESTAMP_START", "decision", "e_proposed", "VPD_proposed", "RH_phase_proposed_pct"]].round(3).to_string(index=False))
    print(f"\nCL05 SUMMARY: targets {len(D)} in {s['target_runs']} runs | " + " | ".join(f"{k}={v}" for k, v in D.decision.value_counts().items())
          + f" | QC0 flagged (not targeted) {s['flagged_QC0']} | approved 0", flush=True)
    for p, h in C4.READS.items():
        if C4.sha(p) != h: raise ValueError("input changed during audit: " + p)
    if a.check: print("CL05 CHECK ONLY: no files written.", flush=True); return
    out = a.root / "reports" / ("cl05_US-Me2_nonphysical_scan_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"Me2_flagged_rows_decisions.csv": D, "Me2_flagged_runs.csv": top, "INTERP_validation_by_bin.csv": I}
    for k, v in files.items(): v.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("Read-only scan and candidate ledger. Nothing approved; no Me2 forcing was written.\n")
    rec = {"version": VERSION, "c4_blob": C4_BLOB, "inputs_sha256": C4.READS, "scan": s, "decisions": D.decision.value_counts().to_dict(), "approved": 0,
           "output_sha256": {n: C4.sha(out / n) for n in [*files, "SCIENTIFIC_HOLD.md"]}}
    (out / "cl05_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("CL05 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("CL05 STOP:", type(exc).__name__, exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

#!/usr/bin/env python3
"""CL04 (Claude, US-Me2 only): the four legacy humidity events, local 2014-12-31 20:30-22:00 LST
(= UTC 2015-01-01 04:30-06:30; Stage14a, BADM UTC_OFFSET -8, no DST). READ ONLY.

Known before this script: original VPD_F is QC1 (MDS) at all four; the paired companion TA_ERA/VPD_ERA gives
negative water vapour pressure; the retained tower TA was ~9.5 C colder than TA_ERA (Stage10i). There is no
Me2 Stage12 NOLEAP shadow; the output here is a per-event research decision ledger, not a forcing file.

A  CONTEXT     original FULLSET (SHA-pinned via the Stage07 manifest) +-24 h: TA_F/QC, TA_F_MDS, TA_ERA, VPD_F/QC,
               VPD_F_MDS/QC, VPD_ERA, RH (if in release), PA_F, SW_IN_F, WS_F; e for every pair; ice/water RH.
               Optional original BASE (any AMF_US-Me2_BASE_HH_*.csv next to the release): every TA_*/RH_*/H2O_*/
               T_SONIC/PA level at the events.
B  CANDIDATES  vapour pressure e at the tower temperature for each event:
                 BASE_RH_<level>   RH_level x esw(TA_level)           (measured, other height/sensor)
                 BASE_H2O_<level>  H2O x PA                            (measured, wet-air mole fraction)
                 INTERP            e between dual-QC0 anchors <= 4 HH from the 4-HH gap
                 GRID_A            esw(ERA5-Land d2m) at the UTC midpoint (existing SHA receipt only)
                 EMP_LOYO          QC0 RH climatology (month, 3-h block, TA_F bin), whole year excluded, x esw(TA_F)
                 SAT_ICE           DATM saturation at TA_F (bound only)
C  VALIDATION  on Me2 truth (TA_F_QC = VPD_F_QC = 0, e > 0): pooled, per year, COLD = Dec/Jan nights (SW_IN_F < 5)
               with TA_F <= -5 C, and the event TA_F bin; e error N/MAE/bias/P95/median relative; Stage12j gates.
               INTERP with 4-HH pseudo-gaps (all four rows scored).
D  DECISION    (fixed before the run) per event: 1 a BASE measured level that passes Stage12j pooled and in >= 80 %
               of years with N >= 50, and is not the same sensor as VPD_F (MAE vs truth >= 0.01 hPa); else
               2 INTERP if formable and its COLD stratum passes; else 3 the COLD-passing method among GRID_A/EMP_LOYO
               with the lower COLD MAE; any e above DATM saturation at TA_F is set to it (DATM-equivalent) and
               flagged; else HOLD. APPROVED_FOR_NEW_VERSION = False for all.
--self-test; --check prints; --run also writes ONE reports/cl04_US-Me2_four_events_* folder.
"""
import argparse, hashlib, json, sys, traceback, zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-CL04-v1-20261029-Me2-four-events-READONLY"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
SITE = "US-Me2"
RAW = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Me2/forcing/raw")
SHA = {"primary": "5b29b04da37960a1640c19b75fc2a8ffbffd703ada89ba6c36689d86f834ae3e",
       "era": "ad0ce6a1d934bb965d939375c1c8588ed643f3513c3ac7e31afed6ca993d3115"}
EVENTS = {"201412312030": 227899, "201412312100": 227900, "201412312130": 227901, "201412312200": 227902}
UTC_OFFSET_H = 8
A = (6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04, 3.031240396e-06, 2.034080948e-08, 6.136820929e-11)
B = (6.109177956, 5.034698970e-01, 1.886013408e-02, 4.176223716e-04, 5.824720280e-06, 4.838803174e-08, 1.838826904e-10)
T_EDGES = (-np.inf, -15, -10, -5, 0, 5, np.inf); T_LAB = ("<=-15", "-15:-10", "-10:-5", "-5:0", "0:5", ">5")
GATE = dict(N=100, MAE=1.5, BIAS=0.7, BAD2=0.10)
READS = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def pin(p, expected=None):
    p = Path(p)
    if not p.is_file() or p.is_symlink(): raise ValueError("missing/unsafe file " + str(p))
    a = sha(p)
    if expected and a != expected: raise ValueError(f"SHA mismatch {p}: {a}")
    READS[str(p)] = a; return p


def esw(t): t = np.asarray(t, float); return 6.112 * np.exp(17.67 * t / (t + 243.5))
def esi(t): t = np.asarray(t, float); return 6.112 * np.exp(22.46 * t / (t + 272.62))
def q_from_e(e, p): e = 100 * np.asarray(e, float); return 0.622 * e / (np.asarray(p, float) - 0.378 * e)
def datm(t):
    t = np.asarray(t, float); tc = np.clip(t, -50, 50); f = lambda k: k[0] + tc * (k[1] + tc * (k[2] + tc * (k[3] + tc * (k[4] + tc * (k[5] + tc * k[6])))))
    return np.where(t < 0, f(B), f(A))
def tbin(t): return pd.cut(np.asarray(t, float), T_EDGES, labels=T_LAB).astype(str)
def num(s): a = pd.to_numeric(s, errors="coerce").to_numpy(float).copy(); a[a <= -9990] = np.nan; return a


def stats(err, et):
    err = np.asarray(err, float); ok = np.isfinite(err); n = ok.size; e = err[ok]
    if not len(e): return dict(N=n, N_valid=0, valid_fraction=0.0)
    return dict(N=n, N_valid=int(ok.sum()), valid_fraction=ok.sum() / n if n else 0, MAE_hPa=float(np.abs(e).mean()), bias_hPa=float(e.mean()),
                P95_abs_hPa=float(np.quantile(np.abs(e), .95)), share_gt2hPa=float((np.abs(e) > 2).mean()), median_rel=float(np.median(np.abs(e) / np.asarray(et, float)[ok])))


def gate(s):
    return bool(s.get("N_valid", 0) >= GATE["N"] and s.get("valid_fraction", 0) >= .6 and s["MAE_hPa"] <= GATE["MAE"] and abs(s["bias_hPa"]) <= GATE["BIAS"] and s["share_gt2hPa"] <= GATE["BAD2"])


def emp_loyo(pool, rh, py, pred, yr, minn=20):
    P = pool.assign(_v=rh, _y=py); out = np.full(len(pred), np.nan); todo = np.ones(len(pred), bool)
    for keys in (["month", "hblock", "Tb"], ["month", "Tb"], ["Tb"]):
        if not todo.any(): break
        c = P.groupby(keys)._v.agg(["sum", "count"]); cy = P.groupby(keys + ["_y"])._v.agg(["sum", "count"]).rename(columns={"sum": "sy", "count": "ny"})
        m = pred.loc[todo, keys].assign(_y=np.asarray(yr)[todo]).join(c, on=keys).join(cy, on=keys + ["_y"])
        S = m["sum"].fillna(0).to_numpy() - m.sy.fillna(0).to_numpy(); N = m["count"].fillna(0).to_numpy() - m.ny.fillna(0).to_numpy()
        ok = N >= minn; idx = np.flatnonzero(todo)[ok]; out[idx] = S[ok] / N[ok]; todo[idx] = False
    return out


def interp(e_anchor, anchor, lo, hi, i, T, w=4):
    n = len(anchor)
    la = np.maximum.accumulate(np.where(anchor, np.arange(n), -1)); na = np.minimum.accumulate(np.where(anchor, np.arange(n), n)[::-1])[::-1]
    lo, hi, i = (np.asarray(x) for x in (lo, hi, i)); inside = (lo >= 1) & (hi <= n - 2)
    a = np.where(inside, la[np.clip(lo - 1, 0, n - 1)], -1); b = np.where(inside, na[np.clip(hi + 1, 0, n - 1)], n)
    ok = inside & (a >= 0) & (b < n) & (a >= lo - w) & (b <= hi + w); ac, bc = np.clip(a, 0, n - 1), np.clip(b, 0, n - 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        e = e_anchor[ac] + (e_anchor[bc] - e_anchor[ac]) * (i - ac) / (bc - ac)
    return np.where(ok & np.isfinite(e) & (e > 0), np.minimum(e, datm(T)), np.nan)


def load(root):
    man = json.loads(pin(root / S07.name / "exact_input_manifest.json").read_text())
    spec = [x for x in man["sites"] if x["site"] == SITE]
    if len(spec) != 1: raise ValueError("US-Me2 not exactly once in Stage07 manifest")
    spec = spec[0]
    for r in ("primary", "era"):
        if man["input_sha256"].get(str(spec[r])) != SHA[r]: raise ValueError("Stage07 manifest SHA differs: " + r)
    p = pin(spec["primary"], SHA["primary"])
    hdr = list(pd.read_csv(p, nrows=0).columns)
    want = ["TIMESTAMP_START", "TIMESTAMP_END", "TA_F", "TA_F_QC", "TA_F_MDS", "TA_F_MDS_QC", "TA_ERA", "VPD_F", "VPD_F_QC", "VPD_F_MDS", "VPD_F_MDS_QC",
            "VPD_ERA", "RH", "PA_F", "PA_F_QC", "SW_IN_F", "WS_F", "LW_IN_F"]
    f = pd.read_csv(p, usecols=[c for c in want if c in hdr], dtype={"TIMESTAMP_START": str, "TIMESTAMP_END": str}, low_memory=False)
    for c in f.columns[2:]: f[c] = num(f[c])
    f["row"] = np.arange(len(f)) + 2
    for k, r in EVENTS.items():
        if int(f.loc[f.TIMESTAMP_START == k, "row"].iloc[0]) != r: raise ValueError("event source row differs: " + k)
    ts = pd.to_datetime(f.TIMESTAMP_START, format="%Y%m%d%H%M"); f["year"], f["month"], f["hour"] = ts.dt.year, ts.dt.month, ts.dt.hour; f["hblock"] = f.hour // 3
    f["utc_mid"] = ts + pd.Timedelta(hours=UTC_OFFSET_H, minutes=15)
    info = dict(primary=str(p), primary_cols=[c for c in want if c in hdr], missing_cols=[c for c in want if c not in hdr])
    base = sorted(RAW.glob("AMF_US-Me2_BASE_HH_*.csv")) + sorted((RAW / spec.get("release", "")).glob("AMF_US-Me2_BASE_HH_*.csv") if spec.get("release") else [])
    info["base_files"] = [str(x) for x in base]
    bcols = []
    if base:
        bp = pin(base[-1]); bh = list(pd.read_csv(bp, comment="#", nrows=0).columns)
        bcols = [c for c in bh if c.split("_")[0] in ("TA", "RH", "H2O", "PA", "T") and "_PI_F" not in c and not c.endswith("_F") and "SIGMA" not in c and "QC" not in c
                 and (c.startswith(("TA_", "RH_", "H2O_")) or c in ("TA", "RH", "H2O", "PA", "T_SONIC"))]
        b = pd.read_csv(bp, comment="#", usecols=["TIMESTAMP_START"] + bcols, dtype={"TIMESTAMP_START": str}, low_memory=False)
        for c in bcols: b[c] = num(b[c])
        f = f.merge(b.rename(columns={c: "B_" + c for c in bcols}), on="TIMESTAMP_START", how="left", validate="one_to_one")
        info["base_columns"] = bcols
    f["grid_T"] = np.nan; f["grid_D"] = np.nan
    info["grid"] = read_grid(root, f)
    return f, info, bcols


def read_grid(root, f):
    out = []
    d = root / "external_evidence/era5land_timeseries" / SITE
    if not d.is_dir(): return [dict(status="NO_ME2_ERA5LAND_DIRECTORY")]
    try:
        from netCDF4 import Dataset, num2date
    except ImportError as exc:
        return [dict(status="NETCDF4_UNAVAILABLE", error=str(exc))]
    for rp in sorted(d.glob("*/*.receipt.json")):
        r = json.loads(pin(rp).read_text()); fp = pin(r["response_file"], r["response_sha256"]); vals = {}; times = None
        def one(ds):
            nonlocal times
            tv = ds.variables["valid_time"] if "valid_time" in ds.variables else ds.variables["time"]
            tt = pd.DatetimeIndex(pd.to_datetime([str(x) for x in num2date(tv[:], tv.units, only_use_cftime_datetimes=False, only_use_python_datetimes=True)]))
            times = tt
            for v in ("t2m", "d2m"):
                if v in ds.variables: vals[v] = np.asarray(np.ma.asarray(ds.variables[v][:]).filled(np.nan), float).reshape(-1)
        if zipfile.is_zipfile(fp):
            with zipfile.ZipFile(fp) as z:
                for m in [x for x in z.infolist() if x.filename.endswith(".nc")]:
                    with Dataset("mem.nc", "r", memory=z.read(m)) as ds: one(ds)
        else:
            with Dataset(str(fp)) as ds: one(ds)
        if {"t2m", "d2m"} - set(vals): out.append(dict(file=str(fp), status="INCOMPLETE")); continue
        x = times.asi8 / 1e9; y = f.utc_mid.values.astype("datetime64[ns]").astype(np.int64) / 1e9
        inside = (y >= x[0]) & (y <= x[-1]) & np.isnan(f.grid_T.to_numpy())
        f.loc[inside, "grid_T"] = np.interp(y[inside], x, vals["t2m"]) - 273.15
        f.loc[inside, "grid_D"] = np.interp(y[inside], x, vals["d2m"]) - 273.15
        out.append(dict(file=str(fp), year=r.get("year"), hours=len(times), first=str(times[0]), last=str(times[-1]), rows_filled=int(inside.sum())))
    return out


def analyse(f, bcols):
    T = f.TA_F.to_numpy(float); V = f.VPD_F.to_numpy(float); et = esw(T) - V
    truth = (f.TA_F_QC == 0).to_numpy() & (f.VPD_F_QC == 0).to_numpy() & np.isfinite(et) & (et > 0) & (V >= 0)
    ev = f.TIMESTAMP_START.isin(EVENTS).to_numpy(); ei = np.flatnonzero(ev)
    night = f.SW_IN_F.to_numpy(float) < 5 if "SW_IN_F" in f else np.ones(len(f), bool)
    cold = truth & f.month.isin([12, 1]).to_numpy() & night & (T <= -5)
    evbin = set(tbin(T[ei]))
    strata = {"POOLED": truth, "COLD_DecJan_night_le_-5": cold, "EVENT_TBIN_DecJan_night": truth & f.month.isin([12, 1]).to_numpy() & night & np.isin(tbin(T), list(evbin))}
    cand = {}
    lev = []
    for c in bcols:
        if c.startswith("RH"):
            t = "TA" + c[2:]
            if "B_" + t in f:
                rh = f["B_" + c].to_numpy(float); ta = f["B_" + t].to_numpy(float); ok = (rh > 1) & (rh <= 103) & (ta > -45) & (ta < 50)
                cand["BASE_RH_" + c] = np.where(ok, rh / 100 * esw(ta), np.nan); lev.append("BASE_RH_" + c)
        if c.startswith("H2O") and "B_PA" in f:
            w = f["B_" + c].to_numpy(float); ok = (w > .01) & (w < 60)
            cand["BASE_H2O_" + c] = np.where(ok, w * f.B_PA.to_numpy(float) / 100, np.nan); lev.append("BASE_H2O_" + c)
    cand["GRID_A"] = esw(f.grid_D.to_numpy(float))
    pool = f.loc[truth, ["month", "hblock"]].assign(Tb=tbin(T[truth]))
    cand["EMP_LOYO"] = emp_loyo(pool, et[truth] / esw(T[truth]), f.year.to_numpy()[truth], f[["month", "hblock"]].assign(Tb=tbin(T)), f.year.to_numpy()) * esw(T)
    # INTERP 4-HH pseudo-gaps, all four rows scored
    e_obs = np.where(truth, et, np.nan); n = len(f); s0 = np.flatnonzero(truth[:-3] & truth[1:-2] & truth[2:-1] & truth[3:])
    ip = np.full(n, np.nan)
    for k in range(4):
        i = s0 + k; e = interp(e_obs, truth.copy(), s0, s0 + 3, i, T[i]); ip[i] = np.where(np.isnan(ip[i]), e, ip[i])
    cand["INTERP_pseudo"] = ip
    rows, yrs = [], []
    for m, e in cand.items():
        err = e - et
        for nm, s in strata.items():
            r = stats(err[s], et[s]); r.update(method=m, stratum=nm); r["gate"] = gate(r) if r.get("N_valid") else False; rows.append(r)
        for y in sorted(f.year.unique()):
            s = truth & (f.year.to_numpy() == y)
            if s.sum() >= 50 and np.isfinite(err[s]).sum() >= 50:
                r = stats(err[s], et[s]); yrs.append(dict(method=m, year=int(y), N=r["N_valid"], MAE=r["MAE_hPa"], bias=r["bias_hPa"], gate=gate(r)))
    Vt = pd.DataFrame(rows); Y = pd.DataFrame(yrs)
    # event values
    lo, hi = ei.min(), ei.max(); anchor = truth.copy(); anchor[ei] = False
    e_int = interp(e_obs, anchor, np.full(4, lo), np.full(4, hi), ei, T[ei])
    vt = Vt.set_index(["method", "stratum"])
    dec = []
    for j, i in enumerate(ei):
        x = dict(TIMESTAMP_START=f.TIMESTAMP_START.iloc[i], source_row=int(f.row.iloc[i]), utc_mid=str(f.utc_mid.iloc[i]), TA_F=T[i], TA_F_QC=f.TA_F_QC.iloc[i],
                 VPD_F=V[i], VPD_F_QC=f.VPD_F_QC.iloc[i], e_tower_pair=et[i], TA_ERA=f.TA_ERA.iloc[i], VPD_ERA=f.VPD_ERA.iloc[i],
                 e_ERA_pair=esw(f.TA_ERA.iloc[i]) - f.VPD_ERA.iloc[i], esw_TA_F=esw(T[i]), esi_TA_F=esi(T[i]), DATM_sat=float(datm(T[i])),
                 grid_T=f.grid_T.iloc[i], grid_D=f.grid_D.iloc[i])
        for m in [*lev, "GRID_A", "EMP_LOYO"]:
            x[m + "_e"] = cand[m][i]; x[m + "_RHice_pct"] = 100 * cand[m][i] / esi(T[i]) if T[i] < 0 else np.nan
        x["INTERP_e"] = e_int[j]
        pick, why = None, ""
        for m in lev:
            if not np.isfinite(cand[m][i]): continue
            p = vt.loc[(m, "POOLED")]; yy = Y.loc[Y.method == m]
            same = p.get("MAE_hPa", 1) < 0.01
            if gate(p) and len(yy) and yy.gate.mean() >= .8 and not same: pick, why = m, f"measured level; pooled MAE {p.MAE_hPa:.3f}, {int(yy.gate.sum())}/{len(yy)} years"; break
        if pick is None and np.isfinite(e_int[j]) and vt.loc[("INTERP_pseudo", "COLD_DecJan_night_le_-5"), "gate"]:
            pick, why = "INTERP", "dual-QC0 anchors <= 4 HH; COLD 4-HH pseudo-gap validated"
        if pick is None:
            ok = [(vt.loc[(m, "COLD_DecJan_night_le_-5"), "MAE_hPa"], m) for m in ("GRID_A", "EMP_LOYO")
                  if np.isfinite(cand[m][i]) and vt.loc[(m, "COLD_DecJan_night_le_-5"), "gate"]]
            if ok: m = sorted(ok)[0][1]; pick, why = m, f"no measured level / INTERP; {m} passes COLD (MAE {sorted(ok)[0][0]:.3f})"
        e = (e_int[j] if pick == "INTERP" else cand[pick][i]) if pick else np.nan
        flag = ""
        if np.isfinite(e) and e > float(datm(T[i])): flag = f"CAPPED_FROM_{100 * e / float(datm(T[i])) - 100:.1f}%_ABOVE_DATM_SAT"; e = float(datm(T[i]))
        x.update(decision=pick or "HOLD", rationale=why or "no validated candidate", cap_flag=flag, e_proposed=e,
                 VPD_proposed=esw(T[i]) - e if np.isfinite(e) else np.nan, QBOT_proposed=float(q_from_e(e, f.PA_F.iloc[i] * 1000)) if np.isfinite(e) else np.nan,
                 RHice_proposed_pct=100 * e / esi(T[i]) if np.isfinite(e) and T[i] < 0 else np.nan, APPROVED_FOR_NEW_VERSION=False)
        dec.append(x)
    ctx = f.loc[max(0, lo - 48): hi + 48].copy()
    ctx["e_tower_pair"] = esw(ctx.TA_F) - ctx.VPD_F; ctx["e_ERA_pair"] = esw(ctx.TA_ERA) - ctx.VPD_ERA
    if "VPD_F_MDS" in ctx: ctx["e_MDS_pair"] = esw(ctx.TA_F) - ctx.VPD_F_MDS
    ctx["dual_QC0"] = truth[max(0, lo - 48): hi + 49]
    return Vt, Y, pd.DataFrame(dec), ctx, dict(truth_rows=int(truth.sum()), cold_rows=int(cold.sum()), event_T_bins=sorted(evbin), levels=lev)


def self_test():
    n = 2000; t = pd.date_range("2013-12-01", periods=n, freq="30min")
    T = -8 + 3 * np.sin(np.arange(n) / 48 * 2 * np.pi); e = 0.8 * esw(T)
    f = pd.DataFrame({"TIMESTAMP_START": t.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0, "VPD_F": esw(T) - e, "VPD_F_QC": 0, "TA_ERA": T + 9, "VPD_ERA": esw(T + 9),
                      "PA_F": 85.0, "SW_IN_F": 0.0, "grid_T": T, "grid_D": T - 2, "row": np.arange(n) + 2})
    f["year"], f["month"], f["hour"] = t.year, t.month, t.hour; f["hblock"] = f.hour // 3; f["utc_mid"] = t + pd.Timedelta(hours=8, minutes=15)
    keys = list(EVENTS); f.loc[1000:1003, "TIMESTAMP_START"] = keys; f.loc[1000:1003, "VPD_F_QC"] = 1
    Vt, Y, D, ctx, s = analyse(f, [])
    assert len(D) == 4 and D.decision.isin(["INTERP", "GRID_A", "EMP_LOYO", "HOLD"]).all()
    assert abs(D.INTERP_e.iloc[0] - e[1000]) < .1, D.INTERP_e
    print("CL04 SELF-TEST PASS: event extraction, interpolation, climatology, decision rule", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): g.add_argument(a, action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args()
    print("CL04 US-Me2 FOUR HUMIDITY EVENTS | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    f, info, bcols = load(a.root)
    print("CL04_INPUTS", json.dumps(info, default=str), flush=True)
    Vt, Y, D, ctx, s = analyse(f, bcols)
    print("CL04_SCOPE", json.dumps(s), flush=True)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
    c = [x for x in ["TIMESTAMP_START", "TA_F", "TA_F_QC", "TA_F_MDS", "TA_ERA", "VPD_F", "VPD_F_QC", "VPD_F_MDS", "VPD_F_MDS_QC", "VPD_ERA", "RH", "PA_F", "SW_IN_F", "WS_F",
                         "e_tower_pair", "e_MDS_pair", "e_ERA_pair", "dual_QC0", "grid_T", "grid_D"] + ["B_" + b for b in bcols] if x in ctx]
    w = ctx.loc[ctx.TIMESTAMP_START.between("201412311200", "201501010600"), c]
    print("\n=== A context 2014-12-31 12:00 -> 2015-01-01 06:00 LST ===\n" + w.round(3).to_string(index=False))
    print("\n=== C validation of e on Me2 QC0 ===\n" + Vt[["method", "stratum", "N", "N_valid", "MAE_hPa", "bias_hPa", "P95_abs_hPa", "median_rel", "gate"]].round(3).to_string(index=False))
    if len(Y): print("\n=== C years passing per method ===\n" + Y.groupby("method").agg(years=("year", "size"), pass_=("gate", "sum"), MAE_min=("MAE", "min"), MAE_max=("MAE", "max")).round(3).to_string())
    print("\n=== D four-event decisions ===\n" + D.T.to_string(header=False), flush=True)
    print("\nCL04 SUMMARY: " + " | ".join(f"{r.TIMESTAMP_START}:{r.decision}" for r in D.itertuples()) + " | approved 0", flush=True)
    for p, h in READS.items():
        if sha(p) != h: raise ValueError("input changed during audit: " + p)
    if a.check: print("CL04 CHECK ONLY: no files written.", flush=True); return
    out = a.root / "reports" / ("cl04_US-Me2_four_events_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"D_four_event_decisions.csv": D, "C_validation.csv": Vt, "C_validation_years.csv": Y, "A_context_pm24h.csv": ctx}
    for k, v in files.items(): v.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("Read-only per-event research ledger. Nothing approved; no Me2 forcing exists or was written.\n")
    rec = {"version": VERSION, "inputs": info, "inputs_sha256": READS, "scope": s, "decisions": D.decision.tolist(), "approved": 0,
           "output_sha256": {n: sha(out / n) for n in [*files, "SCIENTIFIC_HOLD.md"]}}
    (out / "cl04_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("CL04 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("CL04 STOP:", type(exc).__name__, exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

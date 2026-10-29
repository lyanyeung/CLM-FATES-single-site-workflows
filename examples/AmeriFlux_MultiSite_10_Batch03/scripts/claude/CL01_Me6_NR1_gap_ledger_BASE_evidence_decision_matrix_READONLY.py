#!/usr/bin/env python3
"""CL01 (Claude, US-Me6 and US-NR1 handoffs 2026-10-29): one-pass gap ledger, independent BASE
evidence and decision matrix. READ ONLY.

For --site US-Me6 (latest signed Stage13AI shadow, 45 missing) or US-NR1 (Stage13P shadow, 234):

 A  LEDGER   every shadow row with VPD_USE or QBOT missing, joined to original FLUXMET TA_F/QC,
             VPD_F/QC, PA_F and release-paired TA_ERA/VPD_ERA (pinned Stage12g sources()), episode
             id (consecutive native rows), length, year, dT = TA_USE - TA_ERA, QC0 anchors +-2 h,
             physics flags. Count must equal the handoff's figure (45 / 234) or the run stops.
 B  BASE     original AmeriFlux BASE channels (--base, sha256 printed): every TA_*, RH_* and H2O*
             column (PI gap-filled "_PI_F"/"_F" columns excluded). Humidity sources:
               RH:<col>   e = RH/100 * esw(T of the paired probe)  (pairing: TA column with the same
                          suffix, else the TA column that best matches FLUXMET TA_F at QC0)
               H2O:<col>  e = H2O [mmol mol-1] / 1000 * P   (IRGA mole fraction; P from BASE PA or PA_F)
             Temperature evidence at each gap: every BASE TA column and T_SONIC vs the shadow TA_USE.
 C  VALIDATE every source against FLUXMET truth (VPD_F_QC = TA_F_QC = 0, physical), its e carried
             to TA_F: Stage12j thresholds (N >= 50, valid >= 0.60, VPD MAE <= 1.5 hPa, |bias| <= 0.7,
             > 2 hPa <= 0.10) per year (N >= 50) and pooled; SOURCE_PASS = pooled pass AND every gated
             year passes AND >= 3 gated years. Also reported (not gated): cold subset TA_F <= -10 C,
             |dT| > 5 C subset. A source whose validation is trivially the FLUXMET source itself
             (MAE < 0.01 hPa) is labelled SAME_AS_FLUXMET.
 D  CLASSIFY each gap HH (handoff classes), using the shadow TA_USE:
             MEASURED_SUPPORTED          a SOURCE_PASS source present and physical at TA_USE
             ERA_RH_SENSITIVITY_ONLY     no measured source; companion e (TA_ERA/VPD_ERA) physical
             PHYSICS_CONFLICT_HOLD       candidates exist but none is physical at TA_USE
             EVIDENCE_INSUFFICIENT_HOLD  nothing usable
             plus T_SOURCE_FLAG where TA_F_QC != 0 and a BASE measured T differs by > 3 C.
 E  ROOT CAUSE per year: gaps, FLUXMET QC mix, BASE RH/H2O availability, companion formability.

Approved prior edits are never touched (only missing rows are examined). --self-test synthetic;
--check prints everything, NO writes; --run writes ONE reports/cl01_<site>_* folder + SHA receipt.
No forcing, shadow, Post-v5, DATM, CIME or Slurm change.
"""
import argparse, hashlib, importlib.util, json, re, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-CL01-v2-20261029-Me6-NR1-ledger-BASE-decision-READONLY"
HERE = Path(__file__).resolve().parent
M_SCRIPT = HERE.parent / "mtb" / "MtB01_regime_matched_QC0_humidity_census_READONLY.py"
M_BLOB = "3bcead9445dca3ec3485f390d51264492f40cdf0"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
RAW = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SITES = {
    "US-Me6": dict(folder=ROOT / "science_trials/stage13ai_Me6_20151111_0900_VPD_GT_ESphysically_invalid_QC1_SINGLE_RESEARCH_ONLY_20261028T193928Z_0eaab8b2",
                   csv="US-Me6_STAGE13AI_Run14_20151111_0900_physically_invalid_QC1_SINGLE_ONLY_NOLEAP.csv",
                   receipt="stage13ai_one_invalid_source_HH_SHA_receipt.json", missing=45,
                   base=RAW / "US-Me6/forcing/raw/AMF_US-Me6_BASE_HH_21-5.csv"),
    "US-NR1": dict(folder=ROOT / "science_trials/stage13p_NR1_6ERA_RH_5_PSRF_FLDS_OPERATOR_APPROVED_20261026T223628Z_6b3f07eb",
                   csv="US-NR1_STAGE13P_APPROVED_2022_ERA_RH_AND_2004_PSRF_FLDS_RESEARCH_ONLY_NOLEAP.csv",
                   receipt="stage13p_operator_approved_NR1_SHA_receipt.json", missing=234,
                   base=RAW / "US-NR1/forcing/raw/AMF_US-NR1_BASE_HH_26-5.csv"),
}
COLD_C, DT_C, T_FLAG_C = -10.0, 5.0, 3.0
MIN_SOURCE_YEARS = 3
WINDOW_HH = 4


def load_m():
    b = M_SCRIPT.read_bytes()
    if hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() != M_BLOB:
        raise ValueError("Pinned MtB01 Git blob mismatch: " + str(M_SCRIPT))
    spec = importlib.util.spec_from_file_location("mtb01_for_cl01", M_SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


M = load_m()


# ----------------------------------------------------------------- inputs
def stage12g_sources(site):
    if M.gitblob(M.G_SCRIPT) != M.G_BLOB: raise ValueError("Pinned Stage12g Git blob mismatch")
    spec = importlib.util.spec_from_file_location("stage12g_for_cl01", M.G_SCRIPT)
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    stage10, specs, *_ = g.sources()
    if site not in specs: raise ValueError(site + " not in Stage12g sources()")
    return stage10, specs[site]


def shadow(site):
    c = SITES[site]; f = c["folder"]
    rec = json.loads(M.regular(f / c["receipt"]).read_text())
    shamap = next((v for k, v in rec.items() if isinstance(v, dict) and "sha256" in k.lower()), None)
    if not shamap or c["csv"] not in shamap: raise ValueError("shadow receipt does not list " + c["csv"])
    for n, d in shamap.items():
        if (f / n).is_file() and M.sha(f / n) != d: raise ValueError("shadow SHA mismatch: " + n)
    s = pd.read_csv(M.regular(f / c["csv"]), low_memory=False)
    return s, {"shadow": str(f / c["csv"]), "shadow_sha256": shamap[c["csv"]], "receipt_version": rec.get("version")}


def base_columns(hdr):
    excl = re.compile(r"(_PI_F_|_F_|_F$|_PI_F$|_SIGMA|_QC)")
    ta = [c for c in hdr if re.match(r"^TA(_|$)", c) and not excl.search(c)]
    rh = [c for c in hdr if re.match(r"^RH(_|$)", c) and not excl.search(c)]
    h2o = [c for c in hdr if re.match(r"^H2O(_|$)", c) and not excl.search(c)]
    extra = [c for c in ("T_SONIC", "PA") if c in hdr]
    return ta, rh, h2o, extra


def read_base(path):
    hdr = list(pd.read_csv(path, comment="#", nrows=0).columns)
    ta, rh, h2o, extra = base_columns(hdr)
    b = pd.read_csv(path, comment="#", usecols=["TIMESTAMP_START"] + ta + rh + h2o + extra, dtype={"TIMESTAMP_START": str}, low_memory=False)
    for c in b.columns[1:]: b[c] = M.num(b[c])
    if b.TIMESTAMP_START.duplicated().any(): raise ValueError("BASE duplicated timestamps")
    return b, ta, rh, h2o


def frame(site, base_path):
    stage10, spec = stage12g_sources(site)
    hdr = set(pd.read_csv(M.regular(spec["primary"]), nrows=0).columns)
    want = ["TIMESTAMP_START", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "PA_F"]
    flux = pd.read_csv(M.regular(spec["primary"]), usecols=want, dtype={"TIMESTAMP_START": str}, low_memory=False)
    era = pd.read_csv(M.regular(spec["era"]), usecols=["TIMESTAMP_START", "TA_ERA", "VPD_ERA", "PA_ERA"], dtype={"TIMESTAMP_START": str}, low_memory=False)
    df = M.frame_from(flux, era, spec.get("first_year"), spec.get("last_year"))
    s, sinfo = shadow(site)
    sk = pd.to_datetime(s.time, format="%Y-%m-%d %H:%M:%S", errors="raise").dt.strftime("%Y%m%d%H%M").to_numpy()
    if len(s) != len(df) or not np.array_equal(sk, df.native_key.to_numpy()):
        raise ValueError(f"shadow timeline ({len(s)}) differs from the FLUXMET native clock ({len(df)})")
    for c in ("TA_USE", "VPD_USE", "QBOT", "PSRF"): df["S_" + c] = s[c].to_numpy(float)
    info = {"site": site, "primary": str(spec["primary"]), "primary_sha256": M.sha(spec["primary"]), "era": str(spec["era"]),
            "era_sha256": M.sha(spec["era"]), "native_minutes": int(spec["native_minutes"]), "BIF_UTC_offset_h": float(stage10.BIF_OFFSET[site]), **sinfo}
    cols = dict(ta=[], rh=[], h2o=[])
    bp = Path(base_path)
    if bp.is_file():
        b, ta, rh, h2o = read_base(bp)
        x = df[["native_key"]].merge(b, left_on="native_key", right_on="TIMESTAMP_START", how="left", validate="one_to_one")
        for c in b.columns[1:]: df["B_" + c] = x[c].to_numpy()
        cols = dict(ta=ta, rh=rh, h2o=h2o)
        info.update(base=str(bp), base_sha256=M.sha(bp), base_TA=ta, base_RH=rh, base_H2O=h2o,
                    base_rows_matched=int(x.TIMESTAMP_START.notna().sum()))
    else:
        info.update(base="NOT_PROVIDED: " + str(bp))
    return df, cols, info


# ----------------------------------------------------------------- sources
def pair_ta(df, rhcol, ta):
    suf = rhcol[2:]
    if "TA" + suf in ta: return "TA" + suf, "same_suffix"
    q0 = (df.TA_F_QC == 0).to_numpy() & np.isfinite(df.TA_F.to_numpy())
    best, score = None, -1.0
    for t in ta:
        v = df["B_" + t].to_numpy(float); ok = q0 & np.isfinite(v)
        if ok.sum() < 100: continue
        sc = float(np.mean(np.abs(v[ok] - df.TA_F.to_numpy()[ok]) <= 0.05))
        if sc > score: best, score = t, sc
    return best, f"best_TA_F_match_{score:.3f}" if best else "none"


def sources(df, cols):
    out = {}; meta = {}
    P = np.where(np.isfinite(df.get("B_PA", pd.Series(np.nan, index=df.index)).to_numpy(float)),
                 df.get("B_PA", pd.Series(np.nan, index=df.index)).to_numpy(float) * 10.0, df.PA_F.to_numpy(float) * 10.0)
    for r in cols["rh"]:
        t, how = pair_ta(df, r, cols["ta"])
        if not t: continue
        rh, T = df["B_" + r].to_numpy(float), df["B_" + t].to_numpy(float)
        ok = np.isfinite(rh) & (rh >= 2) & (rh <= 103) & np.isfinite(T) & (T > -45) & (T < 50)
        out["RH:" + r] = np.where(ok, rh / 100.0 * M.esw(T), np.nan); meta["RH:" + r] = f"T={t} ({how})"
    for h in cols["h2o"]:
        w = df["B_" + h].to_numpy(float)
        ok = np.isfinite(w) & (w > 0.01) & (w < 60) & np.isfinite(P)
        out["H2O:" + h] = np.where(ok, w / 1000.0 * P, np.nan); meta["H2O:" + h] = "P=" + ("BASE PA" if "B_PA" in df else "PA_F")
    return out, meta


def validate(df, src):
    T, P = df.TA_F.to_numpy(float), df.P_Pa.to_numpy(float); truth = df.truth.to_numpy()
    cold = T <= COLD_C; big = np.abs(df.dT.to_numpy()) > DT_C
    yearly, summ = [], []
    for k, e in src.items():
        ok = M.physical(T, P, e); err = np.where(ok, M.esw(T) - e, np.nan) - df.VPD_F.to_numpy()
        has = truth & np.isfinite(e); passes = []
        for y in sorted(df.year.unique()):
            s = has & (df.year.to_numpy() == y)
            if not s.any(): continue
            r = M.metrics(err[s], s.sum()); r.update(source=k, year=int(y)); r["gate_pass"] = M.gate(r) if r["N"] >= 50 else None
            yearly.append(r)
            if r["gate_pass"] is not None: passes.append(r["gate_pass"])
        p = M.metrics(err[has], has.sum()); c = M.metrics(err[has & cold], (has & cold).sum()); d = M.metrics(err[has & big], (has & big).sum())
        same = bool(p["N"] >= 50 and p["MAE_hPa"] < 0.01)
        summ.append({"source": k, "N": p["N"], "MAE_hPa": p["MAE_hPa"], "bias_hPa": p["bias_hPa"], "frac_gt2hPa": p["frac_abs_err_gt2hPa"],
                     "pooled_pass": bool(M.gate(p)), "gated_years": len(passes), "gated_years_pass": int(sum(passes)),
                     "COLD_le_-10C_N": c["N"], "COLD_MAE_hPa": c["MAE_hPa"], "COLD_bias_hPa": c["bias_hPa"], "COLD_frac_gt2hPa": c["frac_abs_err_gt2hPa"],
                     "absdT_gt5_N": d["N"], "absdT_MAE_hPa": d["MAE_hPa"],
                     "SAME_AS_FLUXMET": same,
                     "SOURCE_PASS": bool(M.gate(p) and passes and all(passes) and len(passes) >= MIN_SOURCE_YEARS)})
    return pd.DataFrame(yearly), pd.DataFrame(summ)


# ----------------------------------------------------------------- ledger / classes
def ledger(df, src, summ, cols):
    gap = (~np.isfinite(df.S_VPD_USE.to_numpy())) | (~np.isfinite(df.S_QBOT.to_numpy()))
    T = df.S_TA_USE.to_numpy(float); P = df.S_PSRF.to_numpy(float); Te = df.TA_ERA.to_numpy(float)
    with np.errstate(invalid="ignore"):
        e_c = M.esw(Te) - df.VPD_ERA.to_numpy(float)
    passing = list(summ.loc[summ.SOURCE_PASS & ~summ.SAME_AS_FLUXMET & ~summ.source.str.startswith("ERA:"), "source"]) if len(summ) else []
    idx = np.flatnonzero(gap); rows = []
    ep = np.zeros(len(df), int); eplen = np.zeros(len(df), int)
    for n, (st, ln) in enumerate(M.runs(gap), 1): ep[st:st + ln] = n; eplen[st:st + ln] = ln
    truth = df.truth.to_numpy()
    for i in idx:
        r = {"native_key": df.native_key.iloc[i], "year": int(df.year.iloc[i]), "episode": int(ep[i]), "episode_HH": int(eplen[i]),
             "VPD_USE_missing": not np.isfinite(df.S_VPD_USE.iloc[i]), "QBOT_missing": not np.isfinite(df.S_QBOT.iloc[i]),
             "TA_USE_C": T[i], "TA_F_C": df.TA_F.iloc[i], "TA_F_QC": df.TA_F_QC.iloc[i], "VPD_F_hPa": df.VPD_F.iloc[i],
             "VPD_F_QC": df.VPD_F_QC.iloc[i], "VPD_F_gt_esw_TA_USE": bool(np.isfinite(df.VPD_F.iloc[i]) and df.VPD_F.iloc[i] >= M.esw(T[i])),
             "TA_ERA_C": Te[i], "VPD_ERA_hPa": df.VPD_ERA.iloc[i], "dT_C": T[i] - Te[i],
             "QC0_anchor_before_2h": bool(truth[max(0, i - WINDOW_HH):i].any()), "QC0_anchor_after_2h": bool(truth[i + 1:i + 1 + WINDOW_HH].any())}
        bt = [df["B_" + t].iloc[i] for t in cols["ta"] if np.isfinite(df["B_" + t].iloc[i])]
        if "B_T_SONIC" in df and np.isfinite(df.B_T_SONIC.iloc[i]): r["T_SONIC_C"] = df.B_T_SONIC.iloc[i]
        r["BASE_TA_median_C"] = float(np.median(bt)) if bt else np.nan
        r["T_SOURCE_FLAG"] = bool(bt and df.TA_F_QC.iloc[i] != 0 and abs(np.median(bt) - T[i]) > T_FLAG_C)
        avail, phys = [], []
        for k, e in src.items():
            if np.isfinite(e[i]):
                avail.append(k); r["e_" + k] = e[i]
                if M.physical(np.array([T[i]]), np.array([P[i]]), np.array([e[i]]))[0]: phys.append(k)
        r["BASE_sources_present"] = ";".join(avail); r["BASE_sources_physical"] = ";".join(phys)
        ok_c = np.isfinite(e_c[i]) and M.physical(np.array([T[i]]), np.array([P[i]]), np.array([e_c[i]]))[0]
        r["companion_e_hPa"] = e_c[i]; r["companion_physical"] = bool(ok_c)
        best = next((k for k in passing if k in phys), None)
        if best: cls, prop = "MEASURED_SUPPORTED", best
        elif ok_c: cls, prop = "ERA_RH_SENSITIVITY_ONLY", "COMPANION_E"
        elif avail or np.isfinite(e_c[i]): cls, prop = "PHYSICS_CONFLICT_HOLD", ""
        else: cls, prop = "EVIDENCE_INSUFFICIENT_HOLD", ""
        r["class"] = cls; r["proposed_source"] = prop
        e_p = r.get("e_" + prop, e_c[i] if prop == "COMPANION_E" else np.nan) if prop else np.nan
        r["proposed_VPD_hPa"] = M.esw(T[i]) - e_p if np.isfinite(e_p) else np.nan
        r["proposed_QBOT_kgkg"] = float(M.q_from_e(e_p, P[i])) if np.isfinite(e_p) else np.nan
        r["proposed_RH_ice_pct"] = 100 * e_p / M.esi(T[i]) if np.isfinite(e_p) and T[i] < 0 else np.nan
        rows.append(r)
    L = pd.DataFrame(rows)
    return gap, L


def episodes(L):
    if not len(L): return pd.DataFrame()
    g = L.groupby("episode")
    E = g.agg(start=("native_key", "first"), end=("native_key", "last"), HH=("native_key", "size"), year=("year", "first"),
              TA_USE_min=("TA_USE_C", "min"), TA_USE_max=("TA_USE_C", "max"), dT_median=("dT_C", "median"),
              VPD_F_QC=("VPD_F_QC", lambda s: ",".join(sorted({str(int(x)) for x in s.dropna()}))),
              TA_F_QC=("TA_F_QC", lambda s: ",".join(sorted({str(int(x)) for x in s.dropna()}))),
              VPD_F_gt_esw=("VPD_F_gt_esw_TA_USE", "sum"), T_SOURCE_FLAG=("T_SOURCE_FLAG", "sum"),
              anchors_before=("QC0_anchor_before_2h", "first"), anchors_after=("QC0_anchor_after_2h", "last")).reset_index()
    cls = L.pivot_table(index="episode", columns="class", values="native_key", aggfunc="count", fill_value=0)
    E = E.merge(cls, left_on="episode", right_index=True, how="left")
    def change(row):
        need = []
        if row.get("PHYSICS_CONFLICT_HOLD", 0) or row.get("EVIDENCE_INSUFFICIENT_HOLD", 0):
            need.append("an independently measured humidity channel at these times (BASE RH/H2O, nearby station)")
        if row.get("ERA_RH_SENSITIVITY_ONLY", 0): need.append("measured humidity to replace reanalysis-only sensitivity")
        if row.get("T_SOURCE_FLAG", 0): need.append("resolution of the TA_F gap-fill vs BASE measured temperature")
        return "; ".join(need) or "none (measured support)"
    E["evidence_that_would_change_decision"] = E.apply(change, axis=1)
    return E


def rootcause(L):
    if not len(L): return pd.DataFrame()
    def avail(s, key): return int(s.str.contains(key, regex=False).sum())
    rows = []
    for y, g in L.groupby("year"):
        rows.append({"year": int(y), "gaps": len(g), "episodes": g.episode.nunique(),
                     "VPD_F_QC0": int((g.VPD_F_QC == 0).sum()), "VPD_F_QC1": int((g.VPD_F_QC == 1).sum()), "VPD_F_QC2": int((g.VPD_F_QC == 2).sum()),
                     "VPD_F_gt_esw": int(g.VPD_F_gt_esw_TA_USE.sum()), "TA_F_QCnot0": int((g.TA_F_QC != 0).sum()),
                     "BASE_RH_present": avail(g.BASE_sources_present, "RH:"), "BASE_H2O_present": avail(g.BASE_sources_present, "H2O:"),
                     "companion_physical": int(g.companion_physical.sum()), "median_dT_C": float(g.dT_C.median()),
                     **{c: int((g["class"] == c).sum()) for c in ("MEASURED_SUPPORTED", "ERA_RH_SENSITIVITY_ONLY", "PHYSICS_CONFLICT_HOLD", "EVIDENCE_INSUFFICIENT_HOLD")}})
    return pd.DataFrame(rows)


def era_sources(df):
    """Reanalysis-only references, validated the same way but never classed as measured."""
    Te, Ve, T = df.TA_ERA.to_numpy(float), df.VPD_ERA.to_numpy(float), df.TA_F.to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        e = M.esw(Te) - Ve; rh = e / M.esw(Te)
    ok = np.isfinite(e) & (e > 0) & (rh <= 1.0)
    return {"ERA:COMPANION_E": np.where(ok, e, np.nan), "ERA:COMPANION_RH": np.where(ok, rh * M.esw(T), np.nan)}


def compute(df, cols, expected):
    src, meta = sources(df, cols)
    vy, vs = validate(df, {**src, **era_sources(df)})
    gap, L = ledger(df, src, vs, cols)
    if expected is not None and int(gap.sum()) != expected:
        raise ValueError(f"shadow has {int(gap.sum())} missing VPD_USE/QBOT rows, handoff states {expected}")
    E = episodes(L); R = rootcause(L)
    matrix = L.groupby(["class", "proposed_source"]).size().rename("HH").reset_index() if len(L) else pd.DataFrame()
    return dict(src_meta=meta, val_year=vy, val=vs, ledger=L, episodes=E, rootcause=R, matrix=matrix)


def show(res, info):
    pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
    print("\n=== INPUTS ===\n" + json.dumps(info, indent=1, default=str))
    print("\n=== BASE humidity sources ===\n" + (json.dumps(res["src_meta"], indent=1) if res["src_meta"] else "none (BASE not provided)"))
    if len(res["val"]): print("\n=== C validation vs FLUXMET QC0 truth ===\n" + res["val"].to_string(index=False))
    print("\n=== D decision matrix ===\n" + (res["matrix"].to_string(index=False) if len(res["matrix"]) else "no gaps"))
    print("\n=== episodes ===")
    if len(res["episodes"]): print(res["episodes"].to_string(index=False))
    print("\n=== E root cause by year ===")
    if len(res["rootcause"]): print(res["rootcause"].to_string(index=False))
    L = res["ledger"]
    if len(L):
        keep = [c for c in ("native_key", "class", "TA_USE_C", "TA_F_QC", "BASE_TA_median_C", "T_SONIC_C", "TA_ERA_C", "VPD_F_hPa", "VPD_F_QC",
                            "VPD_ERA_hPa", "companion_e_hPa", "BASE_sources_present", "proposed_VPD_hPa") if c in L]
        print("\n=== HOLD rows (first 60) ===")
        print(L.loc[L["class"].str.endswith("HOLD"), keep].head(60).round(3).to_string(index=False))


def self_test():
    n = 48 * 365 * 4
    ts = pd.date_range("2014-01-01", periods=n, freq="30min"); ts = ts[~((ts.month == 2) & (ts.day == 29))]; n = len(ts)
    rng = np.random.default_rng(7)
    T = -5 + 12 * np.sin(np.arange(n) / 48 * 2 * np.pi) + rng.normal(0, 1, n); rh = rng.uniform(30, 90, n); e = rh / 100 * M.esw(T)
    flux = pd.DataFrame({"TIMESTAMP_START": ts.strftime("%Y%m%d%H%M"), "TA_F": T, "TA_F_QC": 0, "VPD_F": M.esw(T) - e, "VPD_F_QC": 0, "PA_F": 85.0})
    era = pd.DataFrame({"TIMESTAMP_START": flux.TIMESTAMP_START, "TA_ERA": T + 3, "VPD_ERA": M.esw(T + 3) - e, "PA_ERA": 85.0})
    df = M.frame_from(flux, era)
    for c, v in (("S_TA_USE", T), ("S_VPD_USE", M.esw(T) - e), ("S_QBOT", M.q_from_e(e, 85000.0)), ("S_PSRF", np.full(n, 85000.0))): df[c] = v
    gapi = np.r_[1000:1019, 5000:5003, 9000:9004]; df.loc[gapi, ["S_VPD_USE", "S_QBOT"]] = np.nan
    df.loc[gapi, "truth"] = False
    df["B_TA_1_1_1"] = T; df["B_RH"] = rh; df["B_H2O"] = (e + rng.normal(0, 0.1, n)) / 850.0 * 1000; df["B_PA"] = 85.0
    df.loc[9000:9003, ["B_RH", "B_H2O"]] = np.nan; df.loc[9000:9003, "VPD_ERA"] = np.nan
    cols = dict(ta=["TA_1_1_1"], rh=["RH"], h2o=["H2O"])
    res = compute(df, cols, 26)
    v = res["val"].set_index("source")
    assert v.loc["H2O:H2O", "SOURCE_PASS"] and v.loc["RH:RH", "SAME_AS_FLUXMET"]
    m = res["matrix"].set_index(["class", "proposed_source"]).HH
    assert m[("MEASURED_SUPPORTED", "H2O:H2O")] == 22 and m[("EVIDENCE_INSUFFICIENT_HOLD", "")] == 4, m
    assert len(res["episodes"]) == 3 and res["rootcause"].gaps.sum() == 26
    print("CL01 SELF-TEST PASS: ledger, BASE RH/H2O sources, QC0 validation, SAME_AS_FLUXMET, classes, episodes, root cause")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    gr = ap.add_mutually_exclusive_group(required=True)
    for a in ("--self-test", "--check", "--run"): gr.add_argument(a, action="store_true")
    ap.add_argument("--site", choices=sorted(SITES)); ap.add_argument("--base")
    a = ap.parse_args()
    print("CL01 GAP LEDGER / BASE EVIDENCE / DECISION MATRIX | " + VERSION, flush=True)
    self_test()
    if a.self_test: return
    if not a.site: raise ValueError("--site required")
    df, cols, info = frame(a.site, a.base or SITES[a.site]["base"])
    res = compute(df, cols, SITES[a.site]["missing"])
    show(res, info)
    m = res["matrix"]
    print(f"\nCL01 SUMMARY {a.site}: gaps {len(res['ledger'])} | " + " | ".join(f"{r['class']}:{r['proposed_source'] or '-'}={r['HH']}" for r in m.to_dict('records'))
          + " | forcing writes 0", flush=True)
    if a.check: print("CL01 CHECK ONLY: no files written.", flush=True); return
    out = ROOT / "reports" / (f"cl01_{a.site}_gap_ledger_BASE_decision_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {"A_gap_ledger.csv": res["ledger"], "A_episodes.csv": res["episodes"], "C_validation_summary.csv": res["val"],
             "C_validation_yearly.csv": res["val_year"], "D_decision_matrix.csv": res["matrix"], "E_root_cause_by_year.csv": res["rootcause"]}
    for k, d in files.items(): d.to_csv(out / k, index=False)
    (out / "SCIENTIFIC_HOLD.md").write_text("CL01 read-only evidence and proposals. No class is an approval; protected prior edits untouched.\n")
    names = [*files, "SCIENTIFIC_HOLD.md"]
    rec = {"version": VERSION, "inputs": info, "source_pairing": res["src_meta"], "matrix": m.to_dict("records"),
           "forcing_writes": 0, "Postv5": 0, "DATM": 0, "AD400": 0, "output_sha256": {n: M.sha(out / n) for n in names}}
    (out / "cl01_receipt.json").write_text(json.dumps(rec, indent=2, default=str) + "\n")
    print("CL01 READ-ONLY REPORT:", out, flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("CL01 STOP:", exc, file=sys.stderr, flush=True); traceback.print_exc(); raise SystemExit(2)

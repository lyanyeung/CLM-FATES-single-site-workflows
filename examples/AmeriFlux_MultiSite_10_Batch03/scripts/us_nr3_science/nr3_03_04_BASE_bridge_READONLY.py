#!/usr/bin/env python3
"""US-NR3 BASE 6-5 / FLUXNET v1.3_r1 source bridge, stage03 + stage04.

READ ONLY. stdout only; no download, data repair, output-file, Slurm or DATM mode.
Stage03 repeats provenance and year-blocked QC0 comparisons; Stage04 examines
2017/2018/2023 native co-observations, pressure provenance and Stage12G overlap.
Sonic correction is an uncalibrated physical diagnostic, NEVER an approved TA.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

VERSION = "nr3-03-04-v1.1-20261029"
BASE_SHA = "85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b"
FLUX_SHA = "dbc365368a492285ea73193b1ff1dbb0336673f9448c18d734e82fb7717087a2"
STAGE12G_SHA = "b16f81d125944c47cf6d1886d51461053091cd819cb3d5048cea49247bccc48f"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-NR3/forcing/raw/AMF_US-NR3_BASE_HH_6-5.csv")
MANIFEST = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json"
STAGE12G = ROOT / ("science_trials/"
    "stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/"
    "US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv")
B = ["TIMESTAMP_START", "TIMESTAMP_END", "TA", "RH", "VPD_PI",
     "PA", "T_SONIC", "H2O", "WS", "CO2"]
F = ["TIMESTAMP_START", "TIMESTAMP_END", "TA_F", "TA_F_QC", "VPD_F",
     "VPD_F_QC", "TA_ERA", "VPD_ERA", "PA", "PA_F", "PA_F_QC", "RH"]

def require(ok, message):
    if not bool(ok):
        raise ValueError("NR3_STOP: " + message)

def readonly_guard(event, args):
    if event == "open":
        mode = args[1] if len(args)>1 else None
        flags = args[2] if len(args)>2 else 0
        mask = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if (isinstance(mode, str) and any(x in mode for x in "wax+")) or \
                (isinstance(flags, int) and flags & mask):
            raise RuntimeError("READONLY guard blocked file write")
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.rename",
                 "os.link", "os.symlink", "os.system", "os.truncate",
                 "os.chmod", "os.utime"} or event.startswith("subprocess."):
        raise RuntimeError("READONLY guard blocked mutation/subprocess")

def pin(path, expected):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "missing/unsafe file: "+str(path))
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1<<20), b""):
            h.update(chunk)
    require(h.hexdigest() == expected, "SHA mismatch: "+str(path)+" got "+h.hexdigest())
    print("NR3_SHA_PASS", path.name, h.hexdigest(), flush=True)
    return path

def emit(label, value):
    print(label, json.dumps(value, ensure_ascii=True, allow_nan=False, default=str), flush=True)

def native_keys(frame):
    keys = frame["TIMESTAMP_START"].astype(str)
    require(keys.str.fullmatch(r"[0-9]{12}").all(), "malformed native key")
    dt = pd.to_datetime(keys, format="%Y%m%d%H%M", errors="raise")
    require(dt.dt.minute.mod(30).eq(0).all(), "off-grid timestamp")
    require(not keys.duplicated().any(), "duplicate native timestamp")
    require(dt.diff().iloc[1:].eq(pd.Timedelta(minutes=30)).all(),
            "source native time has a gap/reordering")
    return dt

def esw(t):
    t = np.asarray(t, dtype=float)
    return 6.112*np.exp(17.67*t/(t+243.5))

def esi(t):
    t = np.asarray(t, dtype=float)
    return 6.112*np.exp(22.46*t/(t+272.62))

def sonic_inverse(ts, rh, p):
    # CSAT approximation Ts_K=T_K*(1+0.51q), no fitted offsets
    ts, rh, p = (np.asarray(a, dtype=float) for a in (ts, rh, p))
    t = ts.copy()
    for _ in range(40):
        e_kpa = esw(t)*rh/1000.0
        q = 0.622*e_kpa/(p-0.378*e_kpa)
        new = (ts+273.15)/(1+0.51*q)-273.15
        if np.max(np.abs(new-t), initial=0)<1e-10:
            return new
        t = new
    e_kpa = esw(t)*rh/1000.0
    q = 0.622*e_kpa/(p-0.378*e_kpa)
    closure = (t+273.15)*(1+0.51*q)-(ts+273.15)
    require(np.max(np.abs(closure), initial=0)<1e-8,
            "sonic humidity inverse did not converge")
    return t

def base_column_map():
    """One source of truth for BASE column aliases used in both stages."""
    return {x: ("BASE_SONIC" if x == "T_SONIC" else "BASE_" + x)
            for x in B if x not in ("TIMESTAMP_START", "TIMESTAMP_END")}

def self_test():
    require(len(BASE_SHA)==64 and len(FLUX_SHA)==64 and len(STAGE12G_SHA)==64,
            "expected digest length")
    aliases = base_column_map()
    require(aliases["T_SONIC"] == "BASE_SONIC", "T_SONIC alias regression")
    require(set(aliases.values()) == {"BASE_" + x for x in B[2:] if x!="T_SONIC"} | {"BASE_SONIC"},
            "BASE aliases incomplete or conflicting")
    probe = pd.DataFrame({"T_SONIC": [1.25], "RH": [50.0], "PA": [65.0]}).rename(columns=aliases)
    require({"BASE_SONIC","BASE_RH","BASE_PA"} <= set(probe.columns) and
            np.isfinite(probe["BASE_SONIC"].iat[0]), "BASE rename smoke-test")
    x = np.array([-20., 0., 15.])
    require(np.all(esw(x)>0), "esw")
    require(np.all(esi(x)>0), "esi")
    for rh in (15.0, 50.0, 95.0):
        t = sonic_inverse(np.array([0., 15.]), np.array([rh, rh]), np.array([65., 65.]))
        require(np.all(np.isfinite(t)) and np.all(t<np.array([0., 15.])),
                "sonic inverse plausibility")
    print("NR3_STAGE03_04_SELF_TEST_PASS no writes", flush=True)

def load_sources(base_path, manifest_path):
    base_path = pin(base_path, BASE_SHA)
    with base_path.open(encoding="utf-8-sig") as stream:
        comments = [stream.readline().strip(), stream.readline().strip()]
    require(comments == ["# Site: US-NR3", "# Version: 6-5"], "BASE identity")
    b = pd.read_csv(base_path, comment="#", usecols=B,
                    na_values=-9999,
                    dtype={"TIMESTAMP_START": str, "TIMESTAMP_END": str})
    tb = native_keys(b)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    sites = [x for x in manifest["sites"] if x.get("site")=="US-NR3"]
    require(len(sites)==1 and
            sites[0].get("release")=="AMF_US-NR3_FLUXNET_2007-2024_v1.3_r1",
            "Stage07 source identity")
    primary = Path(sites[0]["primary"])
    require(manifest["input_sha256"].get(str(primary))==FLUX_SHA,
            "Stage07 primary receipt SHA changed")
    primary = pin(primary, FLUX_SHA)
    f = pd.read_csv(primary, usecols=F, na_values=-9999,
                    dtype={"TIMESTAMP_START": str, "TIMESTAMP_END": str})
    tf = native_keys(f)
    require(len(b)==len(f)==315600, "source length changed")
    require(b["TIMESTAMP_START"].equals(f["TIMESTAMP_START"]),
            "BASE/FLUXNET native keys differ")
    for frame, clock in ((b,tb),(f,tf)):
        ends = pd.to_datetime(frame.TIMESTAMP_END, format="%Y%m%d%H%M", errors="raise")
        require((ends-clock).eq(pd.Timedelta(minutes=30)).all(),
                "non-30min source interval")
    b = b.rename(columns=base_column_map())
    require({"BASE_SONIC", "BASE_PA", "BASE_RH", "BASE_TA"} <= set(b.columns),
            "BASE exact source alias schema is incomplete")
    f = f.rename(columns={"PA":"FLUX_PA", "RH":"FLUX_RH"})
    d = f.merge(b.drop(columns="TIMESTAMP_END"), on="TIMESTAMP_START",
                how="left", validate="one_to_one", indicator=True)
    require(d._merge.eq("both").all(), "time join failed")
    d["year"] = tf.dt.year.to_numpy()
    d["month"] = tf.dt.month.to_numpy()
    d["date"] = f.TIMESTAMP_START.str[:8].to_numpy()
    d["QC0_TRUTH"] = (d.TA_F_QC.eq(0) & d.VPD_F_QC.eq(0) &
                       d.TA_F.between(-80,65) & d.VPD_F.ge(0) &
                       (esw(d.TA_F)-d.VPD_F).ge(0))
    d["BASE_SONIC_TRIPLET"] = (d.BASE_SONIC.between(-70,60) &
                               d.BASE_RH.between(0,100) &
                               d.BASE_PA.between(40,110))
    emit("NR3_SOURCE_JOIN", dict(base_rows=len(b), fluxnet_rows=len(f),
         exact_matches=int(d._merge.eq("both").sum()), unmatched=0))
    return d

def stage03(d):
    print("=== STAGE03 ORIGINAL YEAR COVERAGE ===")
    for year,g in d.groupby("year", sort=True):
        emit("NR3_YEAR", dict(year=int(year), BASE_TA=int(g.BASE_TA.notna().sum()),
             BASE_RH=int(g.BASE_RH.notna().sum()),
             BASE_VPD_PI=int(g.BASE_VPD_PI.notna().sum()),
             BASE_PA=int(g.BASE_PA.notna().sum()),
             BASE_SONIC=int(g.BASE_SONIC.notna().sum()),
             BASE_H2O=int(g.BASE_H2O.notna().sum()),
             BASE_WS=int(g.BASE_WS.notna().sum()),
             BASE_CO2=int(g.BASE_CO2.notna().sum()),
             dual_QC0=int(g.QC0_TRUTH.sum()),
             pressure_QC2_with_BASE=int((g.BASE_PA.notna() & g.PA_F_QC.eq(2)).sum())))
    d["SONIC_HUMIDITY_ONLY"] = np.nan
    valid = d.BASE_SONIC_TRIPLET
    if valid.any():
        d.loc[valid,"SONIC_HUMIDITY_ONLY"] = sonic_inverse(
            d.loc[valid,"BASE_SONIC"].to_numpy(),
            d.loc[valid,"BASE_RH"].to_numpy(),
            d.loc[valid,"BASE_PA"].to_numpy())
    d["BASE_VPD_FROM_T_RH"] = np.where(
        d.BASE_TA.notna() & d.BASE_RH.between(0,100),
        esw(d.BASE_TA)*(1.0-d.BASE_RH/100.0), np.nan)
    for method,target in (("BASE_TA","TA_F"),
                          ("BASE_VPD_FROM_T_RH","VPD_F"),
                          ("SONIC_HUMIDITY_ONLY","TA_F")):
        cohort = d.loc[d.QC0_TRUTH & d[method].notna() & d[target].notna()].copy()
        cohort["error"] = cohort[method]-cohort[target]
        cohort["abs_error"] = cohort.error.abs()
        year_scores = []
        for year,g in cohort.groupby("year", sort=True):
            days = g.groupby("date").abs_error.mean()
            row = dict(year=int(year), method=method, n=len(g), days=len(days),
                       MAE=float(g.abs_error.mean()), bias=float(g.error.mean()),
                       P95=float(g.abs_error.quantile(.95)),
                       equal_date_MAE=float(days.mean()))
            emit("NR3_QC0_CHECK", row)
            year_scores.append(row)
        if year_scores:
            emit("NR3_VALIDATION_YEAR_EQUAL", dict(method=method,
                 years=len(year_scores),
                 equal_year_of_date_MAE=float(np.mean(
                     [r["equal_date_MAE"] for r in year_scores]))))
    show_exceptions(d)
    print("NR3_STAGE03_READONLY_COMPLETE approved_repairs=0 HOLD=238")

def show_exceptions(d):
    cols = ["TIMESTAMP_START","BASE_TA","BASE_RH","BASE_PA","BASE_SONIC",
            "BASE_VPD_PI","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
            "TA_ERA","VPD_ERA","PA_F","PA_F_QC"]
    for key in ("201111291400","201802210930","201802211000"):
        g = d.loc[d.TIMESTAMP_START.eq(key), cols]
        require(len(g)==1, "exception key absent: "+key)
        emit("NR3_EXCEPTION", g.to_dict("records")[0])
    # Source 2011 incident: QC0 applies to TA, NOT VPD (which has QC1).
    row = d.loc[d.TIMESTAMP_START.eq("201111291400")].iloc[0]
    emit("NR3_2011_PHASE_CONFLICT", dict(
         native_time="201111291400", temperature_QC=int(row.TA_F_QC),
         VPD_QC=int(row.VPD_F_QC),
         es_water_hPa=float(esw(row.TA_F)),
         implied_e_hPa=float(esw(row.TA_F)-row.VPD_F),
         BASE_RH_missing=bool(pd.isna(row.BASE_RH)),
         disposition="HOLD; no independent absolute temperature verification"))

def stage04(d, stage12g_path):
    print("=== STAGE04 2017 MONTHLY SOURCE COCOVERAGE ===")
    for month,g in d.loc[d.year.eq(2017)].groupby("month"):
        emit("NR3_2017_MONTH", dict(month=int(month),
             RH=int(g.BASE_RH.notna().sum()),
             SONIC=int(g.BASE_SONIC.notna().sum()),
             PA=int(g.BASE_PA.notna().sum()),
             triplet=int(g.BASE_SONIC_TRIPLET.sum()),
             RH_out_of_0_100=int((g.BASE_RH.notna() & ~g.BASE_RH.between(0,100)).sum())))
    g = d.loc[d.year.eq(2017) & d.BASE_SONIC_TRIPLET].copy()
    if len(g):
        dt = pd.to_datetime(g.TIMESTAMP_START, format="%Y%m%d%H%M")
        group = dt.diff().ne(pd.Timedelta(minutes=30)).cumsum()
        windows = (g.groupby(group).agg(
            start=("TIMESTAMP_START","first"), end=("TIMESTAMP_START","last"),
            n=("TIMESTAMP_START","size")).sort_values("n", ascending=False))
        emit("NR3_2017_TRIPLET_WINDOWS",
             dict(total=len(g), episodes=len(windows),
                  longest=windows.head(12).to_dict("records")))
    else:
        emit("NR3_2017_TRIPLET_WINDOWS", dict(total=0, episodes=0, longest=[]))
    print("=== STAGE04 PRESSURE PROVENANCE (kPa) ===")
    for year in (2011,2016,2017,2018,2019,2023,2024):
        g=d.loc[d.year.eq(year)]
        info=dict(year=year, base_pressure=int(g.BASE_PA.notna().sum()),
                  raw_FLUXNET_PA=int(g.FLUX_PA.notna().sum()),
                  PA_F_QC2=int(g.PA_F_QC.eq(2).sum()))
        for name in ("FLUX_PA","PA_F"):
            z = g.loc[g.BASE_PA.notna() & g[name].notna()]
            if len(z):
                dif = z[name]-z.BASE_PA
                info["BASE_vs_"+name] = dict(
                    n=len(z), MAE_kPa=float(dif.abs().mean()),
                    bias_kPa=float(dif.mean()),
                    P95_abs_kPa=float(dif.abs().quantile(.95)))
        emit("NR3_PRESSURE", info)
    g = d.loc[d.year.eq(2017)]
    matched = g.BASE_RH.notna() & g.FLUX_RH.notna()
    diff = (g.loc[matched,"BASE_RH"]-g.loc[matched,"FLUX_RH"]).abs()
    emit("NR3_2017_RH_PRODUCT", dict(
        BASE_RH=int(g.BASE_RH.notna().sum()),
        FLUXNET_RH=int(g.FLUX_RH.notna().sum()),
        matched=int(matched.sum()),
        MAE=float(diff.mean()) if len(diff) else None,
        max_abs=float(diff.max()) if len(diff) else None))
    print("=== STAGE04 ORIGINAL TA/VPD PAIR PHYSICS ===")
    e = esw(d.TA_F)-d.VPD_F
    for year,g in d.groupby("year", sort=True):
        if year in (2017,2018,2023):
            require(len(g)==17520 and
                    (g.TA_F_QC.eq(2)&g.VPD_F_QC.eq(2)).all(),
                    "all-QC2 year changed "+str(year))
        v = e[g.index]<0
        n00 = int((v & g.TA_F_QC.eq(0) & g.VPD_F_QC.eq(0)).sum())
        n01 = int((v & g.TA_F_QC.eq(0) & g.VPD_F_QC.eq(1)).sum())
        if n00 or n01:
            emit("NR3_SOURCE_PHYSICS_CONFLICT", dict(
                year=int(year), negative_e_dual_QC0=n00,
                negative_e_T_QC0_VPD_QC1=n01))
    print("=== STAGE04 EXACT 238 STAGE12G MISSING CROSS-JOIN ===")
    selected = pd.read_csv(pin(stage12g_path, STAGE12G_SHA), low_memory=False)
    require("time" in selected.columns, "Stage12G missing 'time'")
    require(len(selected)==315360, "Stage12G NOLEAP length changed")
    time = selected.time.astype(str).str.replace("T"," ", regex=False)
    require(time.str.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}").all(),
            "Stage12G invalid naive timestamp")
    dt = pd.to_datetime(time,format="%Y-%m-%d %H:%M:%S", errors="raise")
    require((dt.dt.second.eq(0)&dt.dt.minute.mod(30).eq(0)).all(),
            "Stage12G off-grid time")
    nan = selected.drop(columns=["time"]).isna().any(axis=1)
    keys = dt.loc[nan].dt.strftime("%Y%m%d%H%M")
    require(len(keys)==238 and not keys.duplicated().any(),
            "Stage12G 238 identity changed")
    m = pd.DataFrame({"TIMESTAMP_START": keys})
    j = m.merge(d[["TIMESTAMP_START","year","BASE_TA","BASE_RH",
                    "BASE_PA","BASE_SONIC","BASE_SONIC_TRIPLET",
                    "TA_F_QC","VPD_F_QC"]],
                on="TIMESTAMP_START", how="left", validate="one_to_one",
                indicator=True)
    require(j._merge.eq("both").all(), "Stage12G native key missing from source")
    for year,g in j.groupby("year",sort=True):
        emit("NR3_STAGE12G_MISSING_COCOVERAGE", dict(
            year=int(year), n=len(g),
            BASE_TA=int(g.BASE_TA.notna().sum()),
            BASE_RH=int(g.BASE_RH.notna().sum()),
            BASE_PA=int(g.BASE_PA.notna().sum()),
            BASE_SONIC=int(g.BASE_SONIC.notna().sum()),
            BASE_triplet=int(g.BASE_SONIC_TRIPLET.sum()),
            dual_QC2=int((g.TA_F_QC.eq(2)&g.VPD_F_QC.eq(2)).sum())))
    emit("NR3_STAGE04_DECISION", dict(stage12g_missing=238, approved_repairs=0,
         status="ALL_HOLD", note="triplets count availability, not QA-approved fixes"))
    print("NR3_STAGE04_READONLY_COMPLETE no files written; no Slurm")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--stage03",action="store_true")
    mode.add_argument("--stage04",action="store_true")
    mode.add_argument("--both",action="store_true")
    ap.add_argument("--base",type=Path,default=BASE)
    ap.add_argument("--manifest",type=Path,default=MANIFEST)
    ap.add_argument("--stage12g",type=Path,default=STAGE12G)
    args = ap.parse_args()
    sys.addaudithook(readonly_guard)
    self_test()
    if args.self_test:
        return
    d=load_sources(args.base,args.manifest)
    if args.stage03 or args.both:
        stage03(d)
    if args.stage04 or args.both:
        stage04(d,args.stage12g)
    print("NR3_READONLY_DONE VERSION",VERSION, "APPROVED_REPAIRS=0")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""US-NR3 Stage05: genuine BASE H2O availability, 44 missing-row co-observations,
paired pressure/temperature provenance and the 2011/2021 QC0/QC1 conflicts.

Read-only / stdout only. Not a calibration, repair, DATM, model or Slurm tool.
H2O is a WET-AIR mole fraction (mmol/mol), not a dry-air mixing ratio.
All raw, Stage10 and Stage12G sources are SHA-pinned.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
sys.dont_write_bytecode = True

import numpy as np
import pandas as pd

VERSION = "nr3-stage05-v1-20261029"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-NR3/forcing/raw/AMF_US-NR3_BASE_HH_6-5.csv")
MANIFEST = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json"
STAGE12G = ROOT / ("science_trials/stage12g_six_site_new_year_gridRH_science_"
                  "20261025T083234Z_e168f29f/US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv")
STAGE10 = ROOT / ("reports/stage10d_humidity_manual_triage_"
                  "20261024T042016Z_7fa50aaa/all_1924_manual_review.csv")
SHA_BASE = "85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b"
SHA_FLUX = "dbc365368a492285ea73193b1ff1dbb0336673f9448c18d734e82fb7717087a2"
SHA_G = "b16f81d125944c47cf6d1886d51461053091cd819cb3d5048cea49247bccc48f"
SHA_ANOM = "701f5e7bb42e97448607f6cc63265d80889ce94347e5f6109b89ec282dfac06e"
BCOLS = ["TIMESTAMP_START", "TIMESTAMP_END", "TA", "RH", "PA",
         "T_SONIC", "VPD_PI", "H2O", "CO2", "WS"]
FCOLS = ["TIMESTAMP_START", "TIMESTAMP_END", "TA_F", "TA_F_QC",
         "VPD_F", "VPD_F_QC", "TA_ERA", "VPD_ERA",
         "PA", "PA_F", "PA_F_QC", "RH"]

def require(condition, message):
    if not bool(condition):
        raise ValueError("NR3_STOP: " + message)

def deny_writes(event, args):
    if event == "open":
        mode = args[1] if len(args)>1 else None
        flags = args[2] if len(args)>2 else 0
        mask = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if ((isinstance(mode, str) and any(c in mode for c in "wax+"))
                or (isinstance(flags, int) and flags & mask)):
            raise RuntimeError("READONLY file write rejected")
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.rename",
                 "os.link", "os.symlink", "os.system", "os.truncate",
                 "os.chmod", "os.utime"} or event.startswith("subprocess."):
        raise RuntimeError("READONLY mutation/subprocess rejected")

def pin(path, expected):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "missing/unsafe file "+str(path))
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1<<20), b""):
            h.update(b)
    actual = h.hexdigest()
    require(actual==expected, "SHA mismatch "+str(path)+": "+actual)
    print("NR3_STAGE05_SHA_PASS",path.name,actual,flush=True)
    return path

def emit(label, obj):
    print(label,json.dumps(obj,ensure_ascii=True,allow_nan=False,
                           default=str),flush=True)

def esw(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(17.67*t/(t+243.5))

def esi(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(22.46*t/(t+272.62))

def wet_h2o_to_e(h2o_mmol_per_mol, pressure_kpa):
    # mole fraction in WET AIR: x_v = H2O_mmol_per_mol/1000.
    # e_hPa = x_v * P_kPa * 10 = H2O * P_kPa / 100.
    return np.asarray(h2o_mmol_per_mol,dtype=float)*np.asarray(pressure_kpa,dtype=float)/100.0

def q_from_e(e_hpa, pressure_kpa):
    p=np.asarray(pressure_kpa,dtype=float)
    e=np.asarray(e_hpa,dtype=float)/10.0
    return 0.622*e/(p-0.378*e)

def sonic_inverse(ts,rh,p):
    ts,rh,p=(np.asarray(v,dtype=float) for v in (ts,rh,p))
    t=ts.copy()
    for _ in range(40):
        e=esw(t)*rh/100
        q=q_from_e(e,p)
        new=(ts+273.15)/(1+0.51*q)-273.15
        if np.max(np.abs(new-t),initial=0)<1e-10:
            return new
        t=new
    e=esw(t)*rh/100
    q=q_from_e(e,p)
    require(np.max(np.abs((t+273.15)*(1+.51*q)-(ts+273.15)),
                   initial=0)<1e-8,"uncalibrated sonic inverse closure")
    return t

def native_key(series):
    txt=series.astype(str)
    require(txt.str.fullmatch(r"[0-9]{12}").all(), "malformed native HH key")
    dt=pd.to_datetime(txt,format="%Y%m%d%H%M",errors="raise")
    require(dt.dt.minute.mod(30).eq(0).all(), "off-grid native HH key")
    require(not txt.duplicated().any(), "duplicate native HH key")
    return dt

def self_test():
    require(all(len(x)==64 for x in (SHA_BASE,SHA_FLUX,SHA_G,SHA_ANOM)),
            "expected SHA length")
    require(np.isclose(wet_h2o_to_e(1.0,65.0),.65), "wet-air H2O conversion")
    require(np.isclose(q_from_e(.65,65.),.000622,
                       rtol=.003), "mass specific humidity conversion")
    require(np.all(esw(np.array([-20.,0.,20.]))>0),"saturation water")
    require(np.all(esi(np.array([-20.,0.,20.]))>0),"saturation ice")
    x=sonic_inverse(np.array([-5.,10.]),np.array([20.,80.]),np.array([65.,65.]))
    require(np.isfinite(x).all() and np.all(x<np.array([-5.,10.])),
            "sonic inverse temperature sense")
    d=pd.DataFrame({"TIMESTAMP_START":["201701010000","201701010030"]})
    require(len(native_key(d.TIMESTAMP_START))==2,"native timestamp test")
    a=pd.Series(["2017-01-01T00:00:00","2017-01-01 00:30:00"])
    t=stage12g_time(a)
    require(t.dt.strftime("%Y%m%d%H%M").tolist()==d.TIMESTAMP_START.tolist(),
            "Stage12G ISO format variants")
    for event,args in (("open",("x","w",os.O_WRONLY)),
                       ("os.mkdir",("x",0,-1))):
        try:
            deny_writes(event,args)
        except RuntimeError:
            pass
        else:
            raise AssertionError("write guard regression")
    print("NR3_STAGE05_SELF_TEST_PASS wet H2O units, no fitted model, date and read-only guards")

def stage12g_time(series):
    text=series.astype(str).str.replace("T"," ",regex=False)
    require(text.str.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}").all(),
            "Stage12G timestamp format")
    dt=pd.to_datetime(text,format="%Y-%m-%d %H:%M:%S",errors="raise")
    require((dt.dt.second.eq(0)&dt.dt.minute.mod(30).eq(0)).all(),
            "Stage12G off-grid times")
    return dt

def source(args):
    path=pin(args.base,SHA_BASE)
    with path.open(encoding="utf-8-sig") as f:
        require([f.readline().strip(),f.readline().strip()]==
                ["# Site: US-NR3","# Version: 6-5"],"BASE identity")
    b=pd.read_csv(path,comment="#",na_values=-9999,usecols=BCOLS,
                  dtype={"TIMESTAMP_START":str,"TIMESTAMP_END":str})
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    spec=[v for v in manifest["sites"] if v.get("site")=="US-NR3"]
    require(len(spec)==1 and spec[0].get("release")==
            "AMF_US-NR3_FLUXNET_2007-2024_v1.3_r1","Stage07 source identity")
    raw=Path(spec[0]["primary"])
    require(manifest["input_sha256"].get(str(raw))==SHA_FLUX,
            "Stage07 original FLUXMET receipt changed")
    f=pd.read_csv(pin(raw,SHA_FLUX),na_values=-9999,usecols=FCOLS,
                  dtype={"TIMESTAMP_START":str,"TIMESTAMP_END":str})
    tb=native_key(b.TIMESTAMP_START)
    tf=native_key(f.TIMESTAMP_START)
    require(len(b)==len(f)==315600,"expected original full native rows")
    require(b.TIMESTAMP_START.equals(f.TIMESTAMP_START),
            "BASE and FLUXNET native timestamps differ")
    for d,t in ((b,tb),(f,tf)):
        end=pd.to_datetime(d.TIMESTAMP_END,format="%Y%m%d%H%M",errors="raise")
        require((end-t).eq(pd.Timedelta(minutes=30)).all(),
                "source interval is not 30 minutes")
    b=b.rename(columns={
        "TA":"BASE_TA","RH":"BASE_RH","PA":"BASE_PA",
        "T_SONIC":"BASE_SONIC","VPD_PI":"BASE_VPD_PI",
        "H2O":"BASE_H2O","CO2":"BASE_CO2","WS":"BASE_WS"})
    f=f.rename(columns={"PA":"FLUX_PA","RH":"FLUX_RH"})
    d=f.merge(b.drop(columns="TIMESTAMP_END"),on="TIMESTAMP_START",
              how="left",validate="one_to_one",indicator=True)
    require(d._merge.eq("both").all(),"original exact native join")
    d["year"]=tf.dt.year.to_numpy()
    d["date"]=f.TIMESTAMP_START.str[:8].to_numpy()
    d["BASE_TRIPLET"]=(d.BASE_RH.between(0,100)&
                       d.BASE_PA.between(40,110)&
                       d.BASE_SONIC.between(-70,60))
    d["BASE_H2O_PHYS"]=(d.BASE_H2O.between(0,1000,inclusive="left")&
                        d.BASE_PA.between(40,110))
    d["BASE_H2O_e_hPa"]=np.where(
        d.BASE_H2O_PHYS,wet_h2o_to_e(d.BASE_H2O,d.BASE_PA),np.nan)
    d["true_QC0"]=(d.TA_F_QC.eq(0)&d.VPD_F_QC.eq(0)&
                   d.TA_F.between(-80,65)&d.VPD_F.ge(0)&
                   (esw(d.TA_F)-d.VPD_F).ge(0))
    emit("NR3_STAGE05_SOURCE_JOIN",dict(rows=len(d),matched=int(d._merge.eq("both").sum())))
    return d

def h2o_year_coverage(d):
    print("=== BASE H2O (wet air mmol/mol) SOURCE-YEAR COVERAGE ===")
    for year,g in d.groupby("year",sort=True):
        x=g.BASE_H2O.dropna()
        emit("NR3_STAGE05_H2O_YEAR",dict(
            year=int(year), source_H2O_numeric=len(x),
            positive_H2O=int(g.BASE_H2O.gt(0).sum()),
            negative_H2O=int(g.BASE_H2O.lt(0).sum()),
            H2O_with_BASE_PA=int(g.BASE_H2O_PHYS.sum()),
            H2O_with_triplet=int((g.BASE_H2O_PHYS&g.BASE_TRIPLET).sum()),
            H2O_min=float(x.min()) if len(x) else None,
            H2O_median=float(x.median()) if len(x) else None,
            H2O_max=float(x.max()) if len(x) else None,
            RH=int(g.BASE_RH.notna().sum()),
            SONIC=int(g.BASE_SONIC.notna().sum()),
            CO2=int(g.BASE_CO2.notna().sum())))
    print("=== WET H2O vs ORIGINAL SIMULTANEOUS T/VPD QC0 (NOT INDEPENDENT UNTIL SENSOR QA) ===")
    d["true_e_hPa"]=esw(d.TA_F)-d.VPD_F
    d["H2O_e_error"]=d.BASE_H2O_e_hPa-d.true_e_hPa
    matched=d.loc[d.true_QC0 & d.BASE_H2O_PHYS].copy()
    matched["abs_error"]=matched.H2O_e_error.abs()
    if matched.empty:
        emit("NR3_STAGE05_H2O_VALIDATION",dict(status="NO_DUAL_QC0_H2O_COOBS"))
    for year,g in matched.groupby("year",sort=True):
        days=g.groupby("date").abs_error.mean()
        emit("NR3_STAGE05_H2O_VALIDATION",dict(
            year=int(year), n=len(g), days=len(days),
            MAE_e_hPa=float(g.abs_error.mean()),
            bias_e_hPa=float(g.H2O_e_error.mean()),
            RMSE_e_hPa=float(np.sqrt(np.mean(g.H2O_e_error.to_numpy()**2))),
            P95_abs_e_hPa=float(g.abs_error.quantile(.95)),
            error_gt1hPa_share=float(g.abs_error.gt(1).mean()),
            date_equal_MAE_e_hPa=float(days.mean()),
            source_lineage="H2O and RH/VPD may share instrumentation; no independent validation claim"))
    if len(matched):
        m=np.asarray([float(g.groupby("date").abs_error.mean().mean())
                      for _,g in matched.groupby("year")], dtype=float)
        emit("NR3_STAGE05_H2O_YEAR_BLOCK_SUMMARY",dict(
            valid_years=len(m), equal_year_of_equal_date_MAE_hPa=float(m.mean()),
            warning="No fitted parameters or absent-year measured truth inferred"))

def ledger(args,d):
    stage=pd.read_csv(pin(args.stage12g,SHA_G),low_memory=False)
    require(len(stage)==315360,"Stage12G NOLEAP rows changed")
    require({"time","TA_USE","PSRF","VPD_USE","QBOT"}<=set(stage.columns),
            "Stage12G scientific field set changed")
    dt=stage12g_time(stage.time)
    keys=dt.dt.strftime("%Y%m%d%H%M")
    require(not keys.duplicated().any(),"Stage12G duplicated keys")
    missing=stage.drop(columns=["time"]).isna()
    focus=stage.loc[missing.any(axis=1)].copy()
    focus["TIMESTAMP_START"]=keys.loc[focus.index].to_numpy()
    focus["missing_fields"]=missing.loc[focus.index].apply(
        lambda r:"|".join(r.index[r].tolist()),axis=1)
    require(len(focus)==238 and not focus.TIMESTAMP_START.duplicated().any(),
            "Stage12G source missing identity changed")
    columns=["TIMESTAMP_START","year","date","TA_F","TA_F_QC",
             "VPD_F","VPD_F_QC","TA_ERA","VPD_ERA","PA_F","PA_F_QC",
             "BASE_TA","BASE_RH","BASE_PA","BASE_SONIC",
             "BASE_H2O","BASE_CO2","BASE_H2O_PHYS","BASE_H2O_e_hPa",
             "BASE_TRIPLET"]
    j=focus.merge(d[columns],on="TIMESTAMP_START",
                  how="left",validate="one_to_one",indicator=True)
    require(j._merge.eq("both").all(),"Stage12G missing native key not in BASE/FLUX")
    return j

def anomalies(args,j):
    events=pd.read_csv(pin(args.anomaly_ledger,SHA_ANOM),low_memory=False)
    require("site" in events.columns,"Stage10D site column missing")
    g=events.loc[events.site.eq("US-NR3")].copy()
    require(len(g)==1484,"Stage10D 1484 population changed")
    if "native_key" in g:
        txt=g.native_key.astype(str)
        require(txt.str.fullmatch(r"\d{12}").all(),"Stage10D native_key format")
        key=txt
    elif "time" in g:
        key=stage12g_time(g.time).dt.strftime("%Y%m%d%H%M")
    else:
        raise ValueError("NR3_STOP: Stage10D native/time missing")
    require(not key.duplicated().any(),"Stage10D repeated native event")
    ids=set(key)
    j["IN_1484_SOURCE_ANOMALY"]=j.TIMESTAMP_START.isin(ids)
    require(int(j.IN_1484_SOURCE_ANOMALY.sum())==172,
            "Stage10D/12G overlap changed (historically 172)")
    emit("NR3_STAGE05_STAGE10_OVERLAP",dict(
        Stage10D_source_anomalies=1484, Stage12G_missing=238,
        intersection=int(j.IN_1484_SOURCE_ANOMALY.sum()),
        Stage12G_triplets=int(j.BASE_TRIPLET.sum()),
        triplets_with_anomaly=int((j.BASE_TRIPLET&j.IN_1484_SOURCE_ANOMALY).sum())))

def event_review(j):
    print("=== EXACT 238 MISSING ANNUAL H2O/TRIPLET MATRIX ===")
    for year,g in j.groupby("year",sort=True):
        emit("NR3_STAGE05_MISSING_YEAR",dict(
            year=int(year), missing=len(g),
            triplet=int(g.BASE_TRIPLET.sum()),
            H2O_numeric=int(g.BASE_H2O.notna().sum()),
            H2O_with_PA=int(g.BASE_H2O_PHYS.sum()),
            H2O_with_triplet=int((g.BASE_TRIPLET&g.BASE_H2O_PHYS).sum()),
            source_QC2=int((g.TA_F_QC.eq(2)&g.VPD_F_QC.eq(2)).sum()),
            overlap_1484=int(g.IN_1484_SOURCE_ANOMALY.sum())))
    with_triplet=j.loc[j.BASE_TRIPLET].copy().sort_values("TIMESTAMP_START")
    require(len(with_triplet)==44 and
            (with_triplet.year.eq(2016).sum()==11) and
            (with_triplet.year.eq(2017).sum()==33),
            "44 triplet identity changed")
    sonic=sonic_inverse(with_triplet.BASE_SONIC.to_numpy(),
                        with_triplet.BASE_RH.to_numpy(),
                        with_triplet.BASE_PA.to_numpy())
    with_triplet["SONIC_HUMIDITY_ONLY_T_C"]=sonic
    with_triplet["DELTA_SONIC_MINUS_TA_USE_C"]=sonic-with_triplet.TA_USE
    with_triplet["e_RH_sonic_hPa"]=esw(sonic)*with_triplet.BASE_RH.to_numpy()/100
    with_triplet["e_RH_at_TA_USE_hPa"]=esw(with_triplet.TA_USE)*with_triplet.BASE_RH/100
    with_triplet["VPD_RH_at_TA_USE_hPa"]=esw(with_triplet.TA_USE)-with_triplet.e_RH_at_TA_USE_hPa
    with_triplet["RH_ice_sonic_pct"]=100*with_triplet.e_RH_sonic_hPa/esi(sonic)
    with_triplet["RH_ice_at_TA_USE_pct"]=100*with_triplet.e_RH_at_TA_USE_hPa/esi(with_triplet.TA_USE)
    with_triplet["e_BASE_H2O_minus_RH_sonic_hPa"]=(
        with_triplet.BASE_H2O_e_hPa-with_triplet.e_RH_sonic_hPa)
    emit("NR3_STAGE05_44_PHYSICS_SUMMARY",dict(
        records=len(with_triplet),
        H2O_supported=int(with_triplet.BASE_H2O_PHYS.sum()),
        H2O_with_missing=int(with_triplet.BASE_H2O.notna().sum()),
        RH_ice_sonic_over100=int((with_triplet.RH_ice_sonic_pct>100).sum()),
        RH_ice_at_TA_USE_over100=int((with_triplet.RH_ice_at_TA_USE_pct>100).sum()),
        abs_delta_sonic_TA_USE_gt5C=int(
            (with_triplet.DELTA_SONIC_MINUS_TA_USE_C.abs()>5).sum()),
        no_approved_repair=True))
    cols=["TIMESTAMP_START","year","missing_fields","TA_USE","PSRF",
          "VPD_USE","QBOT","TA_F_QC","VPD_F_QC","TA_ERA","VPD_ERA",
          "BASE_RH","BASE_SONIC","BASE_PA","BASE_H2O","BASE_CO2",
          "SONIC_HUMIDITY_ONLY_T_C","DELTA_SONIC_MINUS_TA_USE_C",
          "e_RH_sonic_hPa","VPD_RH_at_TA_USE_hPa",
          "RH_ice_sonic_pct","RH_ice_at_TA_USE_pct",
          "BASE_H2O_e_hPa","e_BASE_H2O_minus_RH_sonic_hPa",
          "IN_1484_SOURCE_ANOMALY"]
    with_triplet=with_triplet.replace([np.inf,-np.inf],np.nan)
    for row in with_triplet[cols].to_dict("records"):
        clean={k:(None if pd.isna(v) else
                  (v.item() if isinstance(v,np.generic) else v))
               for k,v in row.items()}
        emit("NR3_STAGE05_44_EXACT_ROW",clean)

def qc01_exceptions(d):
    print("=== 2011/2021 ORIGINAL QC0 TA + QC1 VPD PHYSICS CONFLICT ===")
    e=esw(d.TA_F)-d.VPD_F
    mask=(d.TA_F_QC.eq(0)&d.VPD_F_QC.eq(1)&e.lt(0))
    chosen=d.loc[mask]
    require(len(chosen)==2 and set(chosen.year)=={2011,2021},
            "historical 2011/2021 QC0/QC1 exceptions changed")
    cols=["TIMESTAMP_START","year","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
          "TA_ERA","VPD_ERA","BASE_TA","BASE_RH","BASE_SONIC",
          "BASE_PA","BASE_H2O","BASE_H2O_e_hPa"]
    for index,row in chosen.iterrows():
        emit("NR3_STAGE05_QC01_PHYSICS_EXCEPTION",dict(
            native_key=row.TIMESTAMP_START,
            es_water_at_TA_F_hPa=float(esw(row.TA_F)),
            implied_source_e_hPa=float(esw(row.TA_F)-row.VPD_F),
            values={c:(None if pd.isna(row[c]) else row[c])
                    for c in cols if c!="TIMESTAMP_START"}))
        neighbors=d.iloc[max(0,index-2):min(len(d),index+3)]
        for item in neighbors[cols].to_dict("records"):
            emit("NR3_STAGE05_QC01_NEIGHBOR",
                 {k:(None if pd.isna(v) else v) for k,v in item.items()})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--self-test",action="store_true")
    m.add_argument("--audit",action="store_true")
    p.add_argument("--base",type=Path,default=BASE)
    p.add_argument("--manifest",type=Path,default=MANIFEST)
    p.add_argument("--stage12g",type=Path,default=STAGE12G)
    p.add_argument("--anomaly-ledger",type=Path,default=STAGE10)
    args=p.parse_args()
    sys.addaudithook(deny_writes)
    self_test()
    if args.self_test:
        return
    d=source(args)
    h2o_year_coverage(d)
    j=ledger(args,d)
    anomalies(args,j)
    event_review(j)
    qc01_exceptions(d)
    emit("NR3_STAGE05_DECISION",dict(
        stage12g_missing=238, current_approved_repair_count=0,
        hold=238, source_measurement_approved=0,
        H2O_not_assumed_independent=True,
        requested_next="Sensor BADM/QC provenance, 44 source episodes, matched QC0 validation; manual decision only",
        version=VERSION))
    print("NR3_STAGE05_READONLY_COMPLETE no files written; no DATM or Slurm")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("NR3_STAGE05_STOP",type(exc).__name__,str(exc),file=sys.stderr,flush=True)
        raise SystemExit(2)

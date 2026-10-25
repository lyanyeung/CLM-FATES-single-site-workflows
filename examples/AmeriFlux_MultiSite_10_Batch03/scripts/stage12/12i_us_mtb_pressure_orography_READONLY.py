#!/usr/bin/env python3
"""Stage12i: no-write high elevation US-MtB air temperature source diagnosis.
Compare original FLUXMET PA_F, source-paired PA_ERA, and ERA5-Land SP;
calculate an APPROXIMATE hypsometric grid-vs-tower height proxy.
Test only diagnostic 4/6.5/9 K km-1 lapse sensitivities at unchanged
original source-native midpoint + provisional BIF UTC offset. No edits.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
V="batch03-stage12i-v1-20261025-pressure-altitude-T-diagnostic"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
B=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
H=R/"reports/stage12h_US-MtB_temperature_and_clock_three_year_diagnostics_20261025T054717Z_58c34b41"
G=R/"science_trials/stage12g_six_site_new_year_gridRH_science_20261024T233640Z_b3d74fae"
E=R/"science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
P=B/"scripts/stage12/12h_us_mtb_temperature_source_offset_diagnosis_READONLY.py"
PIN="e24ada43292eb479a082acdde4082e29daa0fdb7"
YEARS=(2020,2022,2024)
COUNT={2020:302,2022:328,2024:408}
SITE_LAT,SITE_LON,SITE_ELEV=32.4160,-110.7256,2573.
FILES={"1038_US-MtB_original_source_temperature_cases.csv",
"three_year_full_vs_events_temperature_statistics.csv",
"36_site_year_month_temperature_diagnostics.csv",
"13_clock_hypotheses_by_year_and_original_T_QC.csv",
"best_shift_sensitivity_not_a_clock_approval.csv","SCIENCE_HOLD.md"}
def f(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise ValueError("Source missing/symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with f(p).open("rb") as inp:
        for chunk in iter(lambda:inp.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def module():
    b=f(P).read_bytes()
    dig=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    if dig!=PIN:raise ValueError("Stage12h source Git blob changed")
    spec=importlib.util.spec_from_file_location("stage12h_stage12i_pinned",P)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
def num(s):
    a=pd.to_numeric(s,errors="coerce").to_numpy(dtype=float)
    a[(~np.isfinite(a))|(a<=-9990)]=np.nan
    return a
def height(pg,ps,tg,ts):
    with np.errstate(divide="ignore",invalid="ignore"):
        return 287.05*((np.asarray(tg)+np.asarray(ts))/2.)/9.80665*np.log(np.asarray(pg)/np.asarray(ps))
def selftest():
    assert sum(COUNT.values())==1038
    assert 900<float(height(90000,80000,280,274))<1100
    assert len(FILES)==6
    print("STAGE12I SELF-TEST PASS: 3 year original source / pressure proxy / 1038 events / no writes",flush=True)
def check_sources():
    for folder in (H,G,E):
        if not folder.is_dir() or folder.is_symlink():raise ValueError("Missing prior stage "+str(folder))
    record=json.loads(f(H/"stage12h_temperature_source_science_receipt.json").read_text())
    if (record.get("version")!="batch03-stage12h-v1-20261025-US-MtB-T-source-13clock-hypotheses" or
        record.get("Stage12g_source_receipt_SHA256")!=sha(G/"stage12g_research_only_sha_receipt.json") or
        record.get("source_native_target_count")!=1038 or
        record.get("original_Stage12g_T_delta_gt5C_holds")!=1031 or
        record.get("new_tower_clock_approved") is not False or
        record.get("new_tower_temperature_edits")!=0 or
        record.get("new_humidity_edits")!=0 or
        record.get("Postv5_approved")!=0 or
        set(record.get("output_sha256",{}))!=FILES):
        raise ValueError("Stage12h signed source receipt differs")
    for name,digest in record["output_sha256"].items():
        if sha(H/name)!=digest:raise ValueError("Stage12h signed report SHA mismatch: "+name)
    m=module()
    t,spec,catalog,bad,good,_=m.evidence()
    if set(catalog)!={("US-MtB",y) for y in YEARS}:raise ValueError("Source-year catalog unexpected")
    reference=pd.read_csv(f(H/"1038_US-MtB_original_source_temperature_cases.csv"),dtype={"native_key":str})
    if len(reference)!=1038 or reference.native_key.duplicated().any():raise ValueError("Stage12h 1038 source-native list differs")
    for year in YEARS:
        plan,_=catalog[("US-MtB",year)]
        coord=plan["request"]["location"]
        if abs(float(coord["latitude"])-SITE_LAT)>.025 or abs(float(coord["longitude"])-SITE_LON)>.025:
            raise ValueError("Original gridded evidence requested away from US-MtB published location")
    return m,t,spec,catalog,reference
def compute():
    mod,src,spec,catalog,reference=check_sources()
    original=pd.read_csv(f(E/"US-MtB_STAGE12E_INCOMPLETE_NOLEAP.csv"))
    years=pd.to_datetime(original.time,format="%Y-%m-%d %H:%M:%S",errors="raise").dt.year
    wanted=set(reference.native_key)
    annual=[];months=[];targets=[];lapse=[]
    for year in YEARS:
        print("STAGE12I YEAR:",year,flush=True)
        raw=mod.native(spec["primary"],year)
        paired=mod.paired(spec["era"],year)
        vpd=pd.read_csv(f(spec["primary"]),usecols=["TIMESTAMP_START","PA_F"],dtype={"TIMESTAMP_START":str})
        era=pd.read_csv(f(spec["era"]),usecols=["TIMESTAMP_START","PA_ERA"],dtype={"TIMESTAMP_START":str})
        for df in (vpd,era):
            dt=pd.to_datetime(df.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
            df.drop(index=df.index[dt.dt.year.ne(year)],inplace=True)
            df.reset_index(drop=True,inplace=True)
        shadow=original.loc[years.eq(year)].reset_index(drop=True)
        times=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        if (len(raw)!=17520 or len(paired)!=17520 or len(vpd)!=17520 or len(era)!=17520
            or len(shadow)!=17520 or
            not raw.TIMESTAMP_START.equals(paired.TIMESTAMP_START) or
            not raw.TIMESTAMP_START.equals(vpd.TIMESTAMP_START) or
            not raw.TIMESTAMP_START.equals(era.TIMESTAMP_START) or
            not np.array_equal(times.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy(),shadow.time.to_numpy())):
            raise ValueError("Original source-native time mismatches "+str(year))
        ta=num(raw.TA_F);pc=num(vpd.PA_F)*1000
        per=num(era.PA_ERA)*1000
        tcomp=num(paired.TA_ERA)
        if not np.allclose(ta,shadow.TA_USE.to_numpy(dtype=float),atol=1e-6,rtol=0,equal_nan=True):
            raise ValueError("Stage12e tower TA changed from raw source")
        if not np.allclose(pc,shadow.PSRF.to_numpy(dtype=float),atol=1e-3,rtol=0,equal_nan=True):
            raise ValueError("Stage12e tower PSRF differs from original PA_F")
        plan,meta=catalog[("US-MtB",year)]
        position=plan["request"]["location"]
        dt,field,coord=src.grid_fields(f(meta["path"]),year,(position["latitude"],position["longitude"]))
        if abs(coord[0]-SITE_LAT)>.151 or abs(coord[1]-SITE_LON)>.151:
            raise ValueError("ERA5-Land gridpoint unexpectedly distant from tower")
        utc=times+pd.Timedelta(minutes=int(spec["native_minutes"])/2)-pd.Timedelta(hours=src.BIF_OFFSET["US-MtB"])
        tg=src.interpolate(dt,field["t2m"],utc)-273.15
        pg=src.interpolate(dt,field["sp"],utc)
        dz=height(pg,pc,tg+273.15,ta+273.15)
        if not np.isfinite(np.column_stack([ta,tg,pc,pg,dz])).all():
            raise ValueError("Nonfinite full native source T/P/hydrostatic proxy")
        if not ((pc>45000)&(pc<110000)&(pg>45000)&(pg<110000)).all():
            raise ValueError("Site/grid pressure physical source bounds fail")
        frame=pd.DataFrame({"site":"US-MtB","year":year,
            "native_key":times.dt.strftime("%Y%m%d%H%M"),
            "tower_T_C":ta,"grid_T_C":tg,"companion_T_ERA_C":tcomp,
            "tower_P_Pa":pc,"grid_surface_P_Pa":pg,"companion_P_ERA_Pa":per,
            "pressure_height_proxy_m":dz,
            "site_minus_grid_T_C":ta-tg,
            "grid_lat":coord[0],"grid_lon":coord[1]})
        mask=frame.native_key.isin(wanted).to_numpy()
        if mask.sum()!=COUNT[year]:raise ValueError("Source subset year count differs")
        targets.append(frame.loc[mask].copy())
        for name,sel in (("WHOLE_YEAR",np.ones(len(frame),dtype=bool)),
                         ("HELD_1038_TARGET_SUBSET",mask)):
            d=frame.loc[sel]
            annual.append({"year":year,"scope":name,"N":len(d),
                "published_tower_elevation_m":SITE_ELEV,"ERA_grid_lat":coord[0],"ERA_grid_lon":coord[1],
                "tower_P_median_Pa":float(d.tower_P_Pa.median()),
                "ERA5Land_SP_median_Pa":float(d.grid_surface_P_Pa.median()),
                "tower_minus_grid_height_proxy_median_m":float(d.pressure_height_proxy_m.median()),
                "ERA5Land_grid_elevation_proxy_m":float(SITE_ELEV-d.pressure_height_proxy_m.median()),
                "site_minus_grid_T_median_C":float(d.site_minus_grid_T_C.median()),
                "T_delta_gt5C_fraction":float((d.site_minus_grid_T_C.abs()>5).mean())})
            for gradient in (4.,6.5,9.):
                corrected=tg[sel]-dz[sel]*gradient/1000.
                residual=ta[sel]-corrected
                lapse.append({"year":year,"scope":name,"lapse_K_per_km":gradient,"N":len(residual),
                  "raw_grid_to_tower_T_MAE_C":float(np.mean(np.abs(ta[sel]-tg[sel]))),
                  "proxy_adjusted_T_MAE_C":float(np.mean(np.abs(residual))),
                  "fraction_residual_gt5C":float((np.abs(residual)>5).mean()),
                  "adjusted_T_written_to_model":False,"clock_approved":False})
        for mon in range(1,13):
            subset=times.dt.month.eq(mon).to_numpy()
            months.append({"year":year,"month":mon,
                "tower_minus_grid_T_median_C":float(np.median((ta-tg)[subset])),
                "tower_minus_grid_height_proxy_median_m":float(np.median(dz[subset])),
                "tower_P_median_Pa":float(np.median(pc[subset])),
                "grid_P_median_Pa":float(np.median(pg[subset]))})
    cases=pd.concat(targets,ignore_index=True)
    check=cases.merge(reference[["native_key","source_original_tower_TA_F_C",
         "ERA5Land_T2M_C_base_offset"]],on="native_key",validate="one_to_one")
    if (len(cases)!=1038 or len(check)!=1038 or
        not np.allclose(check.tower_T_C,check.source_original_tower_TA_F_C,atol=1e-6,rtol=0) or
        not np.allclose(check.grid_T_C,check.ERA5Land_T2M_C_base_offset,atol=1e-6,rtol=0)):
        raise ValueError("Original Stage12h signed source T disagrees with pressure diagnostic")
    assert len(annual)==6 and len(lapse)==18 and len(months)==36
    return pd.DataFrame(annual),pd.DataFrame(lapse),pd.DataFrame(months),cases
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE12I US-MTB TOWER VS GRID OROGRAPHY AND PRESSURE | "+V,flush=True)
    selftest()
    if args.self_test:return
    annual,lapse,monthly,cases=compute()
    print("\n========== SOURCE PRESSURES AND HEIGHT PROXY ==========",flush=True)
    print(annual.to_string(index=False),flush=True)
    print("\n========== HEIGHT-ADJUSTED TEMPERATURE SENSITIVITY ONLY ==========",flush=True)
    print(lapse.to_string(index=False),flush=True)
    print("STAGE12I SUMMARY: 3 source years, 1038 source cases, 2573m published tower altitude, 4/6.5/9Kkm lapse sensitivity ONLY; no original tower T, P, UTC clock or humidity edits; Postv5=0 DATM=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12I CHECK ONLY: no reports, forcing or model writes.",flush=True)
        return
    out=R/"reports"/("stage12i_US-MtB_orography_pressure_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    tables={"six_year_scope_pressure_height_statistics.csv":annual,
      "18_lapse_sensitivities_NO_FORCING_CHANGES.csv":lapse,
      "36_month_temperature_pressure_stats.csv":monthly,
      "1038_native_source_event_pressure_evidence.csv":cases}
    for name,d in tables.items():d.to_csv(out/name,index=False)
    (out/"SCIENTIFIC_HOLD.md").write_text(
      "Pressure-derived relative altitude is a hydrostatic PROXY, not an ERA5-Land grid geopotential measurement. Reported site altitude 2573m from AmeriFlux; gridded T lapse tests are NOT temperature correction or humidity source approval. Original 1031 T mismatch and 4 ice holds persist. Time basis remains provisional; no Postv5/DATM/spinup.\n")
    files=[*tables,"SCIENTIFIC_HOLD.md"]
    receipt={"version":V,
      "upstream_Stage12h_receipt_SHA256":sha(H/"stage12h_temperature_source_science_receipt.json"),
      "original_source_events":1038,"grid_geopotential_not_measured":True,
      "tower_altitude_published_m":SITE_ELEV,
      "original_T_P_clock_changed":False,"new_humidity_changes":0,
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "output_sha256":{name:sha(out/name) for name in files}}
    (out/"stage12i_pressure_science_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE12I READ-ONLY PRESSURE REPORT:",out,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12I STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

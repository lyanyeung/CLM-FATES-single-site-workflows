#!/usr/bin/env python3
"""Batch03 Stage09e: US-NR3 2022 external dewpoint vs retained tower TA.

Strict evidence-only analysis: pinned 2022 pilot + Stage09d checks, 295
Stage08c blockers, BIF UTC-7 local standard time. Uses the interval MIDPOINT
of FLUXNET TIMESTAMP_START native HH intervals (not nearest-hour shortcut).
Compares (A) grid dewpoint absolute vapor pressure at tower TA, versus
(B) transferring grid RH onto tower TA. Both are research SENSITIVITIES,
neither is accepted forcing. Also compares +/- one-hour clock shifts.

--check writes nothing; --run creates ONLY an isolated report directory.
No source edits, interpolation of historical tower fields, DATM or jobs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import zipfile

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
SITE="US-NR3"
YEAR=2022
ZIPROOT=ROOT/"external_evidence/era5land_timeseries/US-NR3/2022"
NAME="ERA5Land_US-NR3_2022_t2m_d2m_sp"
DREPORT=ROOT/"reports/stage09d_nr3_2022_dewpoint_20261023T001334Z_93ee713f"
SOURCE=ROOT/"reports/stage08c_era_humidity_20261022T031437Z_512e8731/era_humidity_residual_details.csv"
FREPORT=ROOT/"reports/stage08f_mds_pairs_20261022T033321Z_7591f948/mds_pair_at_1924_blockers.csv"
OFFSET=-7
COORD=(40.1,-105.6)
URLS=[
    "https://ameriflux.lbl.gov/data/aboutdata/data-variables/",
    "https://gmd-prod.cmdl.noaa.gov/dv/site/index.php?stacode=NWR",
    "https://ameriflux.lbl.gov/sites/siteinfo/US-NR3",
]
EXPECTED=pd.date_range("2021-12-29T00:00:00","2023-01-03T23:00:00",freq="h")


def hash_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()


def water_es(t):
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))


def grid_fields(zpath):
    fields={}
    times={}
    with zipfile.ZipFile(zpath) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        for member in archive.infolist():
            if not member.filename.lower().endswith(".nc"):continue
            if member.file_size>100_000_000:
                raise ValueError("Unusually large NetCDF ZIP member")
            with Dataset("inmemory.nc",mode="r",memory=archive.read(member)) as ds:
                if "valid_time" not in ds.variables:raise ValueError("Missing valid_time")
                v=ds.variables["valid_time"]
                dt=num2date(v[:],v.units,calendar=getattr(v,"calendar","standard"),
                           only_use_cftime_datetimes=False,only_use_python_datetimes=True)
                index=pd.DatetimeIndex(pd.to_datetime([str(x) for x in dt]))
                if not index.equals(EXPECTED):
                    raise ValueError("Grid time axis is not complete, unique, ordered hourly UTC")
                latitude=float(np.asarray(ds.variables["latitude"][:]).reshape(-1)[0])
                longitude=float(np.asarray(ds.variables["longitude"][:]).reshape(-1)[0])
                if abs(latitude-COORD[0])>1e-5 or abs(longitude-COORD[1])>1e-5:
                    raise ValueError("Grid point no longer matches Stage09d")
                for key in ("t2m","d2m","sp"):
                    if key not in ds.variables:continue
                    if key in fields:raise ValueError("Duplicate field: "+key)
                    val=ds.variables[key]
                    expected_units="Pa" if key=="sp" else "K"
                    if getattr(val,"units","")!=expected_units:
                        raise ValueError("Wrong units for "+key)
                    x=np.asarray(np.ma.asarray(val[:]).filled(np.nan),dtype=float).reshape(-1)
                    if len(x)!=len(index) or not np.isfinite(x).all():
                        raise ValueError("Missing or unequal hourly samples for "+key)
                    fields[key]=x
                    times[key]=index
    if set(fields)!={"t2m","d2m","sp"}:
        raise ValueError("Missing one of the three grid variables")
    return fields


def interp_hourly(x, targets):
    origin=EXPECTED.asi8.astype(np.float64)
    times=pd.DatetimeIndex(targets).asi8.astype(np.float64)
    if len(times)==0 or times.min()<origin[0] or times.max()>origin[-1]:
        raise ValueError("Target lies outside ERA5-Land hourly evidence range")
    return np.interp(times,origin,x)


def q_from_e(e_hpa,p_pa):
    numerator=e_hpa*100
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 0.622*numerator/(p_pa-0.378*numerator)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=ap.parse_args()

    for folder in (ROOT,ZIPROOT,DREPORT):
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Required preserved evidence folder missing")
    z=ZIPROOT/(NAME+".zip")
    receipt=json.loads((ZIPROOT/(NAME+".receipt.json")).read_text())
    prior=json.loads((DREPORT/"audit_summary.json").read_text())
    if (receipt.get("response_sha256")!=hash_file(z)
            or prior["pilot_sha256"]!=hash_file(z)
            or prior["source_sha256"]!=hash_file(SOURCE)
            or prior["source_blocker_rows_2022"]!=295
            or prior["UTC_offset_assumed_hours"]!=OFFSET
            or prior["clock_validated"] is not False):
        raise ValueError("ZIP or Stage09d evidence has changed")
    if receipt["request"]["date"]!=["2021-12-29","2023-01-03"]:
        raise ValueError("Downloaded request date window differs")

    original=pd.read_csv(SOURCE,low_memory=False)
    df=original.loc[(original.site==SITE)&
                    (original.time.astype(str).str.startswith("2022-"))].copy()
    if len(df)!=295 or df.source_csv_row.duplicated().any():
        raise ValueError("Expected 295 unique Stage08c 2022 US-NR3 blockers")
    ref=pd.read_csv(DREPORT/"us_nr3_2022_dewpoint_blocker_comparison.csv")
    a=set(zip(df.source_csv_row.astype(str),df.time.astype(str)))
    b=set(zip(ref.source_csv_row.astype(str),ref.time.astype(str)))
    if a!=b:raise ValueError("Stage09d source-row identities differ")
    mds=pd.read_csv(FREPORT,low_memory=False)
    mds=mds.loc[(mds.site==SITE)&mds.time.astype(str).str.startswith("2022-"),
        ["source_csv_row","time","MDS_pair_physical_screen_pass",
         "MDS_VPD_valid_at_retained_TA","review_class"]].copy()
    if len(mds)!=295:
        raise ValueError("Stage08f MDS 2022 evidence incomplete")
    df=df.merge(mds,on=["source_csv_row","time"],validate="one_to_one")

    fields=grid_fields(z)
    local_start=pd.DatetimeIndex(pd.to_datetime(df.time))
    mid_local=local_start+pd.Timedelta(minutes=15)
    utc_mid=mid_local-pd.Timedelta(hours=OFFSET)
    if any(v not in df.columns for v in
        ("TA_before_fallback_C","VPD_before_fallback_hPa","PA_before_fallback_kPa")):
        raise ValueError("Required source temperature, pressure or VPD missing")
    tsite=pd.to_numeric(df.TA_before_fallback_C,errors="coerce").to_numpy(float)
    vsite=pd.to_numeric(df.VPD_before_fallback_hPa,errors="coerce").to_numpy(float)
    psite=pd.to_numeric(df.PA_before_fallback_kPa,errors="coerce").to_numpy(float)*1000
    if (not np.isfinite(tsite).all() or not np.isfinite(vsite).all()
        or not np.isfinite(psite).all() or not ((psite>50000)&(psite<110000)).all()):
        raise ValueError("Source site physical inputs missing")
    gridT=interp_hourly(fields["t2m"],utc_mid)-273.15
    gridD=interp_hourly(fields["d2m"],utc_mid)-273.15
    gridP=interp_hourly(fields["sp"],utc_mid)
    esgrid=water_es(gridT)
    ea=water_es(gridD)
    es_tower=water_es(tsite)
    RHgrid=100*ea/esgrid
    gridVPD=esgrid-ea
    vpd_abs=es_tower-ea
    rh_abs=100*ea/es_tower
    q_abs=q_from_e(ea,psite)
    e_trans=es_tower*RHgrid/100
    vpd_trans=es_tower-e_trans
    q_trans=q_from_e(e_trans,psite)
    rh_trans=RHgrid
    grid_ok=(gridD<=gridT+0.1)&(gridVPD>=-0.02)&(RHgrid>0)&(RHgrid<=100.05)
    abs_ok=grid_ok&(vpd_abs>=0)&(vpd_abs<=125)&np.isfinite(q_abs)&(q_abs>0)&(q_abs<=0.08)
    rh_ok=grid_ok&(vpd_trans>=0)&(vpd_trans<=125)&np.isfinite(q_trans)&(q_trans>0)&(q_trans<=0.08)
    if not grid_ok.all():
        raise ValueError("One or more interpolated grid T/dewpoint pairs is not physical")

    df["native_local_start"]=local_start
    df["comparison_local_midpoint"]=mid_local
    df["comparison_utc_midpoint_provisional"]=utc_mid
    df["grid_t2m_C_interpolated"]=gridT
    df["grid_d2m_C_interpolated"]=gridD
    df["grid_sp_Pa_interpolated"]=gridP
    df["tower_minus_grid_T_C"]=tsite-gridT
    df["tower_minus_grid_P_Pa"]=psite-gridP
    df["grid_RH_pct"]=RHgrid
    df["grid_VPD_hPa"]=gridVPD
    df["grid_dewpoint_absolute_e_hPa"]=ea
    df["dewpoint_absolute_VPD_at_tower_T_hPa"]=vpd_abs
    df["dewpoint_absolute_RH_at_tower_T_pct"]=rh_abs
    df["dewpoint_absolute_QBOT_at_tower_P"]=q_abs
    df["absolute_e_transfer_physical_pass"]=abs_ok
    df["grid_RH_transferred_VPD_at_tower_T_hPa"]=vpd_trans
    df["grid_RH_transferred_QBOT_at_tower_P"]=q_trans
    df["grid_RH_transfer_physical_pass"]=rh_ok
    df["grid_dewpoint_physical_pass"]=grid_ok

    shifts=[]
    for offset in (-8,-7,-6):
        hrs=mid_local-pd.Timedelta(hours=offset)
        Tshift=interp_hourly(fields["t2m"],hrs)-273.15
        delta=np.abs(tsite-Tshift)
        shifts.append(dict(hypothetical_utc_offset_hours=offset,
            median_abs_tower_grid_T_C=float(np.median(delta)),
            p90_abs_tower_grid_T_C=float(np.quantile(delta,0.9)),
            warning="NOT A CLOCK SELECTION METRIC; all offsets hypotheses only"))
    shiftframe=pd.DataFrame(shifts)
    delta=tsite-gridT
    print("STAGE09E VERIFIED: 3 complete 8904-hour fields; raw ZIP SHA256 unchanged")
    print("US-NR3 2022 native humidity blockers:",len(df))
    print("PROVISIONAL CLOCK: local standard UTC-7 from BIF and nearby NOAA Niwot Ridge; interval MIDPOINT")
    print("GRID: latitude 40.1 longitude -105.6, not tower location or elevation")
    print("tower minus grid T (C): median",round(float(np.median(delta)),3),
        "p10",round(float(np.quantile(delta,0.1)),3),
        "p90",round(float(np.quantile(delta,0.9)),3))
    print("tower minus grid P (Pa): median",round(float(np.median(psite-gridP)),1))
    print("grid RH range pct:",round(float(np.min(RHgrid)),3),round(float(np.max(RHgrid)),3))
    print("grid VPD negative:",int(np.sum(gridVPD<0)))
    print("absolute dewpoint-to-tower physics pass:",int(abs_ok.sum()),"/",len(df))
    print("grid RH transfer-to-tower physics pass:",int(rh_ok.sum()),"/",len(df))
    print("MDS paired physical pass:",int(df.MDS_pair_physical_screen_pass.sum()))
    print("MDS VPD valid at retained TA:",int(df.MDS_VPD_valid_at_retained_TA.sum()))
    print("\nOFFSET SENSITIVITY (not time approval)")
    print(shiftframe.to_string(index=False))
    print("STAGE09E PREFLIGHT: 295 source blockers traced; no input or output modified")
    if args.check:
        print("CHECK ONLY: no reports created")
        return
    out=ROOT/"reports"/("stage09e_nr3_2022_tower_dewpoint_"+
             datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    df.to_csv(out/"nr3_2022_two_dewpoint_transfer_sensitivities.csv",index=False)
    shiftframe.to_csv(out/"offset_sensitivity.csv",index=False)
    (out/"provenance_and_policy.json").write_text(json.dumps({
        "pilot_raw_zip":str(z),"pilot_SHA256":hash_file(z),
        "stage09d_sha256":hash_file(DREPORT/"audit_summary.json"),
        "stage08c_sha256":hash_file(SOURCE),
        "native_blockers":len(df),
        "timezone_assumption":"LST UTC-7, supported by BIF and nearby NOAA Niwot Ridge; independent full workflow validation pending",
        "time_sample_policy":"Linear interpolation of RAW grid hourly T2m/D2m/SP to FLUXNET interval midpoint; evidence only",
        "spatial_limitation":"0.1 degree gridded reanalysis differs from tower position and elevation; no elevation/measurement-height correction",
        "methods":["absolute dewpoint vapor pressure transferred to retained tower T and P",
                   "gridded RH transferred to retained tower T and P"],
        "approvals":"NONE. Neither method may overwrite tower/ERA sources or be used to generate DATM; independent QC and scientific review required.",
        "external_clock_and_site_references":URLS,
        "output_scope":"Isolated report only, no changes to any candidates, source, GitHub input receipts or Slurm jobs"
    },indent=2)+"\n")
    print("STAGE09E SUMMARY: 295/295 tower/dewpoint comparison rows; report_only=True")
    print("REPORT DIR:",out)


if __name__=="__main__":
    main()

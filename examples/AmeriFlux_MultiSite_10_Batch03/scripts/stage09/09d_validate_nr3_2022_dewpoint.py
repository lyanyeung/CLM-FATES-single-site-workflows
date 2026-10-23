#!/usr/bin/env python3
"""Read-only Stage09d full hourly validation and US-NR3 2022 dewpoint comparison.

Do not use as a forcing replacement. Confirms archived pilot ZIP and receipt,
each NetCDF's complete hourly UTC axis, grid, dewpoint/temperature/pressure
ranges, and evaluates humidity physics at previously flagged native timestamps
using BIF UTC-7 (still pending independent clock approval).
--check: only prints; --run: writes an isolated report directory.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import hashlib, io, json, zipfile
from uuid import uuid4
import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
PILOT=ROOT/"external_evidence/era5land_timeseries/US-NR3/2022"
NAME="ERA5Land_US-NR3_2022_t2m_d2m_sp"
SOURCE=ROOT/"reports/stage08c_era_humidity_20261022T031437Z_512e8731/era_humidity_residual_details.csv"
EXPECTED_START=pd.Timestamp("2021-12-29 00:00")
EXPECTED_END=pd.Timestamp("2023-01-03 23:00")
LAT,LON=40.1,-105.6
CLOCK_HOURS=-7

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as s:
        for buf in iter(lambda:s.read(1<<20),b""):h.update(buf)
    return h.hexdigest()

def open_vars(zip_path):
    fields={}; clock={}
    with zipfile.ZipFile(zip_path) as zf:
        if zf.testzip() is not None:raise ValueError("ZIP CRC failure")
        for member in zf.infolist():
            if not member.filename.endswith(".nc"):continue
            if member.file_size>100_000_000:raise ValueError("Unexpected large member")
            with Dataset("mem.nc","r",memory=zf.read(member)) as ds:
                if "valid_time" not in ds.variables:raise ValueError("Missing valid_time")
                t=ds.variables["valid_time"]
                converted=num2date(t[:],t.units,calendar=getattr(t,"calendar","standard"),
                                  only_use_cftime_datetimes=False,only_use_python_datetimes=True)
                idx=pd.DatetimeIndex(pd.to_datetime([str(x) for x in converted]))
                expected=pd.date_range(EXPECTED_START,EXPECTED_END,freq="h")
                if len(idx)!=len(expected) or not idx.equals(expected):
                    raise ValueError("Incomplete, non-hourly, duplicate or out-of-order UTC axis")
                lat=float(np.asarray(ds.variables["latitude"][:]).reshape(-1)[0])
                lon=float(np.asarray(ds.variables["longitude"][:]).reshape(-1)[0])
                if abs(lat-LAT)>0.00001 or abs(lon-LON)>0.00001:
                    raise ValueError("Unexpected grid cell")
                for v in ["t2m","d2m","sp"]:
                    if v not in ds.variables:continue
                    if v in fields:raise ValueError("Duplicate field: "+v)
                    var=ds.variables[v]
                    units=getattr(var,"units","")
                    if units!=("Pa" if v=="sp" else "K"):
                        raise ValueError("Unexpected "+v+" units "+units)
                    arr=np.ma.asarray(var[:]).filled(np.nan).astype(float).reshape(-1)
                    if len(arr)!=len(idx) or not np.isfinite(arr).all():
                        raise ValueError("Missing data in "+v)
                    fields[v]=arr
                    clock[v]=idx
                    print("COMPLETE UTC:",v,"records",len(idx),"from",idx[0],"to",idx[-1],flush=True)
    if set(fields)!={"t2m","d2m","sp"}:
        raise ValueError("One of t2m,d2m,sp is absent")
    return fields,clock

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=p.parse_args()
    zip_path=PILOT/(NAME+".zip")
    receipt=json.loads((PILOT/(NAME+".receipt.json")).read_text())
    if (not zip_path.is_file() or zip_path.is_symlink() or
       receipt["response_sha256"]!=sha(zip_path) or
       Path(receipt["response_file"]).resolve()!=zip_path):
        raise ValueError("ZIP/receipt checksum or path mismatch")
    if receipt["request"]["date"]!=["2021-12-29","2023-01-03"]:
        raise ValueError("Pilot request dates unexpectedly different")
    f,clock=open_vars(zip_path)
    t=f["t2m"]; d=f["d2m"]; pressure=f["sp"]
    if not ((t>170)&(t<340)).all() or not ((d>160)&(d<340)).all():
        raise ValueError("Gross temperature ranges invalid")
    if not ((pressure>40000)&(pressure<110000)).all():
        raise ValueError("Gross pressure ranges invalid")
    dew_above=int((d>t+0.1).sum())
    TC=t-273.15; DC=d-273.15
    with np.errstate(over="ignore",invalid="ignore"):
        es=6.112*np.exp(17.67*TC/(TC+243.5))
        ea=6.112*np.exp(17.67*DC/(DC+243.5))
        rh=100*ea/es
        vpd=es-ea
        q=.622*(ea*100)/(pressure-.378*(ea*100))
    print("GRID:",LAT,LON,"dewpoint_t2m_excess_gt_0p1K",dew_above)
    print("MET RANGES: T_C",float(TC.min()),float(TC.max()),
          "D_C",float(DC.min()),float(DC.max()),
          "SP_Pa",float(pressure.min()),float(pressure.max()))
    print("Derived RH min/max:",float(rh.min()),float(rh.max()),
          "VPD min/max hPa:",float(vpd.min()),float(vpd.max()))
    original=pd.read_csv(SOURCE,usecols=["site","time","source_csv_row",
       "TA_before_fallback_C","VPD_before_fallback_hPa","ERA_RH_pct"],dtype={"site":str,"time":str})
    src=original[(original.site=="US-NR3")&(original.time.str.startswith("2022-"))].copy()
    if src.empty:raise ValueError("No 2022 US-NR3 source humidity blockers")
    # Time convention (local standard time, UTC-7) is PROVISIONAL until
    # cross-confirmed with independent AmeriFlux BIF/site metadata.
    native=pd.to_datetime(src.time)
    utc=native-pd.Timedelta(hours=CLOCK_HOURS)
    axis=clock["t2m"]
    idx=axis.get_indexer(utc,method="nearest",tolerance=pd.Timedelta(minutes=30))
    if (idx<0).any():raise ValueError("Source timestamps outside retrieved coverage")
    # Native half-hour timestamps may fall exactly between gridded hours;
    # nearest-neighbor is ONLY evidence comparison, not resampling policy.
    src["utc_assuming_bif_minus7"]=utc.to_numpy()
    src["grid_utc_nearest"]=axis[idx].to_numpy()
    src["grid_t2m_C"]=TC[idx]
    src["grid_d2m_C"]=DC[idx]
    src["grid_sp_Pa"]=pressure[idx]
    src["grid_vpd_hPa"]=vpd[idx]
    src["grid_RH_pct"]=rh[idx]
    src["grid_QBOT_kgkg"]=q[idx]
    src["grid_dewpoint_above_t2m"]=d[idx]>t[idx]+0.1
    src["grid_vpd_nonnegative"]=vpd[idx]>=0
    print("2022 US-NR3 original blocker native rows:",len(src))
    print("2022 source event time window:",src.time.min(),src.time.max())
    print("2022 sampled grid RH pct min/max:",float(src.grid_RH_pct.min()),float(src.grid_RH_pct.max()))
    print("2022 grid VPD negative rows:",int((src.grid_vpd_hPa<0).sum()))
    print("CLOCK STATUS: UTC-7 derived from BIF, independent validation PENDING")
    print("STAGE09D PREFLIGHT: 8904 unique continuous hours per variable; evidence only")
    if args.check:
        print("CHECK ONLY: no report or forcing files written")
        return
    out=ROOT/"reports"/("stage09d_nr3_2022_dewpoint_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    src.to_csv(out/"us_nr3_2022_dewpoint_blocker_comparison.csv",index=False)
    (out/"audit_summary.json").write_text(json.dumps({
        "pilot_zip":str(zip_path),"pilot_sha256":sha(zip_path),
        "source_stage08c":str(SOURCE),"source_sha256":sha(SOURCE),
        "grid_lat":LAT,"grid_lon":LON,"UTC_offset_assumed_hours":CLOCK_HOURS,
        "clock_validated":False,"CDS_download_reused":True,
        "all_hourly_fields":list(f),"unique_hours_each":len(axis),
        "grid_t2m_below_d2m_over_0p1K":dew_above,
        "source_blocker_rows_2022":len(src),
        "notes":["No modifications to any forcing or prior results.",
                 "Grid values are not independent tower observations.",
                 "Nearest hourly times are for evidence screening only.",
                 "No interpolation, temporal alignment approval or spinup." ]
    },indent=2)+"\n")
    print("STAGE09D SUMMARY: UTC full-coverage and provisional evidence report only")
    print("REPORT DIR:",out)

if __name__=="__main__":main()

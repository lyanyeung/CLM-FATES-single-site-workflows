#!/usr/bin/env python3
"""Stage15: five *one-year* ERA5 dewpoint control experiments for Batch02.

Read the exact pinned Stage13 location plan. Download one diagnostic year for
each of five sites: EML 2009, GLE 2005, Ho1 1996, ICh 2007, ICt 2007.
Three UTC buffer days on each side support later timezone alignment. No conversion
to tower local time, no half-hour interpolation, no forced humidity replacement,
and no DATM, CIME or Slurm model changes.

Modes: --check (no CDS, no writes); --download (explicit CDS requests).
CDS may return NetCDF in a ZIP container. Preserve both exact payload and an
extracted NetCDF. Never overwrite an existing download; per-site receipts
permit safe resumption after a partial retrieval.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

import numpy as np
import pandas as pd

PLAN=Path.home()/"AmeriFlux_Batch02_stage13_plan_20261022T023406Z_7614f826"/"request_plan.json"
EXPECTED_PLAN_SHA="0785bb8b85b5e8c9fee7b64d6f63016e58e12db03e31cf53c20e265e803f9523"
DATASET="reanalysis-era5-single-levels-timeseries"
VARIABLES=["2m_temperature","2m_dewpoint_temperature","surface_pressure"]
FOCUS={"US-EML":2009,"US-GLE":2005,"US-Ho1":1996,"US-ICh":2007,"US-ICt":2007}
OUTPUT=Path.home()/"AmeriFlux_Batch02_ERA5_five_one_year_controls"
MAX_NETCDF_SIZE=100*1024*1024

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def signature(path):
    with Path(path).open("rb") as f:b=f.read(8)
    if b==b"\x89HDF\r\n\x1a\n":return "NETCDF4_HDF5"
    if b[:4] in (b"CDF\x01",b"CDF\x02",b"CDF\x05"):return "NETCDF3"
    if b[:4]==b"PK\x03\x04":return "ZIP"
    return "UNRECOGNIZED"

def check_plan():
    if sha(PLAN)!=EXPECTED_PLAN_SHA:
        raise ValueError("Stage13 point/date/coordinates plan hash differs. Refuse request.")
    manifest=json.loads(PLAN.read_text())
    if manifest.get("schema")!="Stage13_ERA5_TD2M_REQUEST_PLAN_v1" or manifest.get("dataset")!=DATASET:
        raise ValueError("Stage13 schema mismatch")
    if manifest.get("science_status")!="RETRIEVAL_PLAN_ONLY_NO_HUMIDITY_APPROVAL":
        raise ValueError("Not an unapproved Stage13 plan")
    entries={s["site"]:s for s in manifest["sites"]}
    if set(entries)!=set(FOCUS):
        raise ValueError("Stage13 site list differs")
    for site,entry in entries.items():
        if entry["cds_request"]["variable"]!=VARIABLES:
            raise ValueError("Stage13 variable contract differs: "+site)
        coords=entry["metadata"]
        if entry["cds_request"]["location"]!={"latitude":coords["latitude"],
                                               "longitude":coords["longitude"]}:
            raise ValueError("Stage13 coordinates differ in plan: "+site)
        if coords["tower_local_standard_to_UTC_offset_hours"]!="UNRESOLVED_MANUAL_VERIFICATION_REQUIRED":
            raise ValueError("Stage13 time zone status unexpectedly changed")
        if not entry["first_year"]<=FOCUS[site]<=entry["last_year"]:
            raise ValueError("Focus year outside AmeriFlux coverage: "+site)
    return entries

def request(entry,year):
    start=f"{year-1}-12-29"
    end=f"{year+1}-01-03"
    req=dict(variable=VARIABLES,
             location=dict(latitude=entry["metadata"]["latitude"],
                           longitude=entry["metadata"]["longitude"]),
             date=[start,end],data_format="netcdf")
    return req,start,end

def unpack(payload,folder):
    kind=signature(payload)
    if kind in ("NETCDF4_HDF5","NETCDF3"):
        # Not in a ZIP. Keep the exact source under its original filename.
        return payload,kind
    if kind!="ZIP" or not zipfile.is_zipfile(payload):
        raise ValueError("CDS result does not contain readable NetCDF or ZIP")
    with zipfile.ZipFile(payload) as z:
        items=[x for x in z.infolist() if not x.is_dir()]
        if len(items)!=1:
            raise ValueError("Expected one NetCDF member inside point-timeseries ZIP")
        one=items[0]
        p=PurePosixPath(one.filename)
        if len(p.parts)!=1 or p.name in (".","..") or not p.name.lower().endswith(".nc"):
            raise ValueError("Unexpected ZIP member path/name; refuse extraction")
        if not 0<one.file_size<MAX_NETCDF_SIZE:
            raise ValueError("Unexpected ZIP member size")
        dest=folder/"era5_dewpoint_hourly_UTC.nc"
        if dest.exists():raise FileExistsError(str(dest))
        with z.open(one) as src, dest.open("xb") as dst:
            shutil.copyfileobj(src,dst,1024*1024)
        if dest.stat().st_size!=one.file_size or signature(dest) not in ("NETCDF4_HDF5","NETCDF3"):
            raise ValueError("Extracted file length/magic mismatch")
        return dest,kind

def verify(path,entry,start,end):
    import xarray as xr
    with xr.open_dataset(path,engine="netcdf4") as ds:
        if set(ds.data_vars)!={"t2m","d2m","sp"}:
            raise ValueError("Unexpected ERA5 variables")
        for var,units in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if ds[var].attrs.get("units")!=units or tuple(ds[var].dims)!=("valid_time",):
                raise ValueError("Wrong ERA5 units/shape: "+var)
        ts=pd.to_datetime(ds.valid_time.values,utc=True)
        exp=pd.date_range(start+" 00:00",end+" 23:00",freq="h",tz="UTC")
        if len(ts)!=len(exp) or not np.array_equal(ts.asi8,exp.asi8):
            raise ValueError("Missing, duplicate or unexpected UTC timestamps")
        lat=float(np.asarray(ds.latitude.values).ravel()[0])
        lon=float(np.asarray(ds.longitude.values).ravel()[0])
        desired=entry["metadata"]
        if (abs(lat-desired["latitude"])>.126 or abs(lon-desired["longitude"])>.126):
            raise ValueError("ERA5 is not the requested nearest 0.25-degree point")
        temp=ds.t2m.to_numpy().astype(float)-273.15
        dew=ds.d2m.to_numpy().astype(float)-273.15
        pressure=ds.sp.to_numpy().astype(float)
    if not (np.isfinite(temp).all() and np.isfinite(dew).all()
            and np.isfinite(pressure).all()
            and ((temp>-90)&(temp<65)).all()
            and ((dew>-100)&(dew<65)).all()
            and ((pressure>49000)&(pressure<111000)).all()):
        raise ValueError("ERA5 numeric/range checks failed")
    with np.errstate(all="ignore"):
        sat=lambda t:6.112*np.exp(17.67*t/(t+243.5))
        ea=sat(dew)
        rh=100*ea/sat(temp)
        vpd=sat(temp)-ea
        q=.622*ea*100/(pressure-.378*ea*100)
    invalid=~(np.isfinite(rh)&(rh>0)&(rh<=100.05)&
              np.isfinite(q)&(q>0)&(q<.08)&
              np.isfinite(vpd)&(vpd>=-.005))
    return dict(utc_hours=len(ts),first_utc=str(ts.min()),last_utc=str(ts.max()),
        grid_lat=lat,grid_lon=lon,temperature_min_C=float(temp.min()),
        temperature_max_C=float(temp.max()),dewpoint_min_C=float(dew.min()),
        dewpoint_max_C=float(dew.max()),RH_min_pct=float(rh.min()),
        RH_max_pct=float(rh.max()),invalid_water_RH_QBOT=int(invalid.sum()),
        Td_gt_T_005C=int(((dew-temp)>.05).sum()),
        status="NUMERIC_QC_REVIEW_REQUIRED" if invalid.sum() else "NUMERIC_QC_OK_NOT_FOR_DATM")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root",type=Path,default=OUTPUT)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--download",action="store_true")
    args=parser.parse_args()
    sites=check_plan()
    print("STAGE15 PLAN SHA256 VERIFIED:",EXPECTED_PLAN_SHA,flush=True)
    for site,year in FOCUS.items():
        req,start,end=request(sites[site],year)
        hours=len(pd.date_range(start,end+" 23:00",freq="h"))
        print("YEARLY REVIEW:",site,year,"UTC",start,"through",end,
              "hours=",hours,json.dumps(req,sort_keys=True),flush=True)
    if args.check:
        print("CHECK ONLY. No files or CDS requests written.")
        return 0
    out=args.output_root.expanduser().resolve()
    if out==PLAN or out in PLAN.parents or PLAN in out.parents:
        raise ValueError("Refusing an output directory that encloses the Stage13 plan")
    if out.is_symlink():raise ValueError("Refuse symlink output root")
    if out.exists():
        if not (out/"STAGE15_PARTIAL_OR_COMPLETE_REVIEW_ONLY").is_file():
            raise ValueError("Existing output not recognized as this Stage15 run")
        old=json.loads((out/"config.json").read_text())
        if old.get("stage13_plan_sha256")!=EXPECTED_PLAN_SHA or old.get("focus_years")!=FOCUS:
            raise ValueError("Existing output belongs to another study")
    else:
        out.mkdir(parents=True,exist_ok=False)
        (out/"STAGE15_PARTIAL_OR_COMPLETE_REVIEW_ONLY").write_text(
            "Full-year ERA5 raw controls only, not DATM forcing.\n")
        (out/"config.json").write_text(json.dumps(dict(
            dataset=DATASET,variables=VARIABLES,stage13_plan=str(PLAN),
            stage13_plan_sha256=EXPECTED_PLAN_SHA,focus_years=FOCUS,
            status="ONE_YEAR_ERA5_COMPARISON_NO_MODEL_APPROVAL"
        ),indent=2)+"\n")
    import cdsapi
    client=cdsapi.Client()
    for site,year in FOCUS.items():
        folder=out/f"{site}_{year}"
        folder.mkdir(parents=True,exist_ok=True)
        receipt=folder/"verified_receipt.json"
        if receipt.exists():
            old=json.loads(receipt.read_text())
            nc=Path(old["netcdf_path"]).resolve()
            source=Path(old["original_payload_path"]).resolve()
            req,start,end=request(sites[site],year)
            if not nc.is_file() or not source.is_file() or \
               sha(nc)!=old["netcdf_sha256"] or sha(source)!=old["original_payload_sha256"]:
                raise ValueError("Previously verified download changed: "+site)
            print("ALREADY VERIFIED, SKIP CDS:",site,year,flush=True)
            continue
        req,start,end=request(sites[site],year)
        payload=folder/"original_cds_response.bin"
        if payload.exists():
            print("RECOVERING PREVIOUS CDS PAYLOAD:",site,year,flush=True)
        else:
            print("CDS REQUEST:",site,year,flush=True)
            client.retrieve(DATASET,req,str(payload))
        if not payload.is_file() or payload.stat().st_size<100:
            raise ValueError("CDS response missing/empty for "+site)
        nc,format_name=unpack(payload,folder)
        summary=verify(nc,sites[site],start,end)
        data=dict(site=site,year=year,requested_date=[start,end],
            dataset=DATASET,request=req,
            stage13_plan_sha256=EXPECTED_PLAN_SHA,
            cds_response_format=format_name,
            original_payload_path=str(payload),original_payload_sha256=sha(payload),
            netcdf_path=str(nc),netcdf_sha256=sha(nc),
            science_approval=False,
            time_zone_validation="Needs site BIF/BADM interpretation before aligning with tower",
            no_forcing_or_model_changes=True,**summary)
        receipt.write_text(json.dumps(data,indent=2)+"\n")
        print("VERIFIED ONE-YEAR ERA5:",site,"hours=",summary["utc_hours"],
              "RH",round(summary["RH_min_pct"],2),"-",round(summary["RH_max_pct"],2),
              "invalid=",summary["invalid_water_RH_QBOT"],
              "NETCDF:",nc,flush=True)
    verified=sorted(out.glob("US-*/verified_receipt.json"))
    print("STAGE15 VERIFIED:",len(verified),"/5",flush=True)
    print("STAGE15 ROOT:",out,flush=True)
    print("Only ERA5 one-year controls; NO forcing, DATM, CIME or Slurm changes.")
    return 0 if len(verified)==5 else 2

if __name__=="__main__":
    raise SystemExit(main())

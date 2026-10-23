#!/usr/bin/env python3
"""Batch03 Stage09f: verified incremental download queue for the 32 Stage09a site-years.

--check: READ ONLY; inspect downloaded receipt/ZIP/NC coverage, list next jobs.
--run --max-new 1..3: run up to 3 CDS point-year requests serially using the
already-reviewed Stage09b pilot, and audit every output before continuing.

Existing results and SHA receipts are NEVER overwritten or deleted. No forcing,
RH/QBOT replacement, DATM, PFT/case edits, Slurm jobs, or UTC conversion here.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
EVIDENCE=ROOT/"reports/stage09a_external_dewpoint_plan_20261022T034051Z_437c9c0c"
ARCHIVE=ROOT/"external_evidence/era5land_timeseries"
PILOT=Path(__file__).with_name("09b_download_era5land_pilot.py")
FIELDS={"t2m":"K","d2m":"K","sp":"Pa"}
EXT="reanalysis-era5-land-timeseries"
SITES={"US-Kon","US-MMS","US-Me2","US-Me6","US-MtB","US-NR1","US-NR3"}


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()


def read_source():
    if not EVIDENCE.is_dir() or EVIDENCE.is_symlink():
        raise ValueError("Stage09a pinned plan directory unavailable")
    receipts=json.loads((EVIDENCE/"evidence_receipt.json").read_text())
    plan=json.loads((EVIDENCE/"era5land_request_plan.json").read_text())
    clock=json.loads((EVIDENCE/"site_utc_offset_inventory.json").read_text())
    if (len(plan)!=32 or receipts["requests"]!=32
        or receipts["event_count"]!=1924
        or set(x["site"] for x in plan)!=SITES
        or set(x["site"] for x in clock)!=SITES):
        raise ValueError("Unexpected pinned Stage09a plan")
    entries=set()
    for item in plan:
        key=(item["site"],int(item["year"]))
        req=item["request"]
        if key in entries or item["dataset"]!=EXT:
            raise ValueError("Duplicate/invalid plan entry")
        entries.add(key)
        if (req.get("variable")!=["2m_temperature","2m_dewpoint_temperature","surface_pressure"]
                or req.get("data_format")!="netcdf"
                or req.get("date")!=[f"{key[1]-1}-12-29",f"{key[1]+1}-01-03"]
                or not all(isinstance(req["location"][x],(float,int)) for x in ("latitude","longitude"))
                or int(item["blocked_native_records"])<=0):
            raise ValueError("Unexpected request form: "+str(key))
    if sum(int(x["blocked_native_records"]) for x in plan)!=1924:
        raise ValueError("Source event count changed")
    return plan


def read_one(ds,wanted,found,coordinates):
    if "valid_time" in ds.variables:
        t=ds.variables["valid_time"]
    elif "time" in ds.variables:
        t=ds.variables["time"]
    else:
        raise ValueError("NetCDF missing CF time coordinate")
    vals=num2date(t[:],getattr(t,"units",""),
                 calendar=getattr(t,"calendar","standard"),
                 only_use_cftime_datetimes=False,
                 only_use_python_datetimes=True)
    got=pd.DatetimeIndex(pd.to_datetime([str(v) for v in vals]))
    if not got.equals(wanted):
        raise ValueError("Missing, duplicate, unordered or shifted UTC hours")
    latitude=float(np.asarray(ds.variables["latitude"][:]).reshape(-1)[0])
    longitude=float(np.asarray(ds.variables["longitude"][:]).reshape(-1)[0])
    if abs(latitude-coordinates[0])>.151 or abs(longitude-coordinates[1])>.151:
        raise ValueError("Unexpected gridded latitude/longitude")
    for field,unit in FIELDS.items():
        if field not in ds.variables:continue
        if field in found:raise ValueError("Duplicate NetCDF field "+field)
        var=ds.variables[field]
        if getattr(var,"units","")!=unit:raise ValueError("Units mismatch: "+field)
        arr=np.asarray(np.ma.asarray(var[:]).filled(np.nan),dtype=float).reshape(-1)
        if len(arr)!=len(wanted) or not np.isfinite(arr).all():
            raise ValueError("Missing/nonfinite NetCDF values in "+field)
        if field in ("t2m","d2m") and ((arr<160)|(arr>340)).any():
            raise ValueError("Temperature outside gross screening range")
        if field=="sp" and ((arr<40000)|(arr>110000)).any():
            raise ValueError("Pressure outside gross screening range")
        found[field]=arr
    return latitude,longitude


def check_artifact(item):
    site,year=item["site"],int(item["year"])
    directory=ARCHIVE/site/str(year)
    name=f"ERA5Land_{site}_{year}_t2m_d2m_sp"
    receipt=directory/(name+".receipt.json")
    candidates=[directory/(name+".zip"), directory/(name+".nc")]
    partial=directory/(name+".download.partial")
    existing=[x for x in candidates if x.is_file()]
    if not receipt.exists() and not existing and not partial.exists():
        return "MISSING",None
    if (not receipt.is_file() or receipt.is_symlink()
        or partial.exists() or len(existing)!=1
        or existing[0].is_symlink()):
        raise RuntimeError("Incomplete or ambiguous historical output at "+str(directory))
    file=existing[0]
    obj=json.loads(receipt.read_text(encoding="utf-8"))
    if (obj.get("site")!=site or int(obj.get("year",-1))!=year
        or obj.get("dataset")!=EXT or obj.get("request")!=item["request"]
        or obj.get("status")!="DOWNLOADED_ONLY_NOT_QC_ACCEPTED"
        or Path(obj["response_file"]).resolve()!=file.resolve()
        or obj.get("response_sha256")!=sha(file)):
        raise RuntimeError("Receipt or SHA256 mismatch: "+str(directory))

    wanted=pd.date_range(f"{year-1}-12-29 00:00:00",
        f"{year+1}-01-03 23:00:00",freq="h")
    loc=item["request"]["location"]
    coords=(float(loc["latitude"]),float(loc["longitude"]))
    found={}
    locations=[]
    if zipfile.is_zipfile(file):
        with zipfile.ZipFile(file) as zf:
            if zf.testzip() is not None:raise ValueError("ZIP CRC failure")
            infos=[x for x in zf.infolist() if x.filename.endswith(".nc")]
            if not infos or len(infos)>6:raise ValueError("Unexpected ZIP NetCDF structure")
            for info in infos:
                if (info.file_size>100_000_000 or info.filename.startswith("/")
                        or ".." in Path(info.filename).parts):
                    raise ValueError("Unsafe ZIP member")
                with Dataset("inmemory.nc","r",memory=zf.read(info)) as ds:
                    locations.append(read_one(ds,wanted,found,coords))
    elif file.suffix==".nc":
        with Dataset(str(file),"r") as ds:
            locations.append(read_one(ds,wanted,found,coords))
    else:
        raise ValueError("Not a recognizable NetCDF or ZIP: "+str(file))

    if set(found)!=set(FIELDS):
        raise ValueError("Missing t2m/d2m/sp variables in "+str(file))
    if any(abs(la-locations[0][0])>1e-5 or abs(lo-locations[0][1])>1e-5
           for la,lo in locations):
        raise ValueError("Temperature/pressure members have different grid locations")
    # An inventory-level scientific sanity check, not acceptance for tower forcing.
    if int((found["d2m"]>found["t2m"]+.1).sum())>0:
        raise ValueError("Dewpoint exceeds temperature by >0.1 K")
    return "VERIFIED",dict(name=file.name,sha256=sha(file),hours=len(wanted),
                          grid_lat=locations[0][0],grid_lon=locations[0][1])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    p.add_argument("--max-new",type=int,default=3)
    p.add_argument("--site",choices=sorted(SITES),default=None,
                   help="Optional focus; other downloaded sites are still audited")
    a=p.parse_args()
    if not 1<=a.max_new<=3:
        p.error("--max-new must be between 1 and 3 (CDS workload guard)")
    plan=read_source()
    if not PILOT.is_file():raise ValueError("Missing local Stage09b pilot script")
    statuses=[]
    for row in plan:
        status,meta=check_artifact(row)
        statuses.append((row,status,meta))
    verified=[(r,m) for r,status,m in statuses if status=="VERIFIED"]
    todo=[r for r,status,_ in statuses if status=="MISSING" and
          (a.site is None or r["site"]==a.site)]
    # Cover different sites first, while favoring years with larger source event counts.
    todo.sort(key=lambda r:(-int(r["blocked_native_records"]),r["site"],int(r["year"])))
    selected=todo[:a.max_new]
    print("STAGE09F PINNED PLAN: 32 site-years; original blockers=1924")
    print("EXISTING VALIDATED:",len(verified),"| UNDOWNLOADED:",sum(s=="MISSING" for _,s,_ in statuses))
    for r,m in verified:
        print("EXISTS VERIFIED:",r["site"],r["year"],"hours",m["hours"],
              "grid",m["grid_lat"],m["grid_lon"])
    print("NEXT REQUESTS: up to",a.max_new)
    for r in selected:
        print("QUEUE:",r["site"],r["year"],
              "source_events",r["blocked_native_records"],
              "date",r["request"]["date"])
    print("WARNING: ERA5-Land is an ERA5-driven reanalysis, not independent tower evidence.")
    print("WARNING: UTC_OFFSET still pending; no hourly join/forcing repair.")
    print("STAGE09F PREFLIGHT: pre-existing receipts and all variables independently checked")
    if a.check:
        print("CHECK ONLY: no API calls, reports, data or jobs created")
        return
    if not selected:
        print("NO NEW DOWNLOADS REQUIRED for selected scope.")
        return
    for r in selected:
        cmd=[sys.executable,"-B",str(PILOT),"--site",r["site"],
             "--year",str(r["year"]),"--run"]
        print("STAGE09F CDS START:",r["site"],r["year"],flush=True)
        subprocess.run(cmd,check=True)
        status,meta=check_artifact(r)
        if status!="VERIFIED":
            raise RuntimeError("New CDS retrieval did not pass physical/time/receipt verification")
        print("STAGE09F VERIFIED NEW:",r["site"],r["year"],meta,flush=True)
    print("STAGE09F SUMMARY: validated_new=",len(selected),
          "previously_validated=",len(verified),
          "all_inputs_unchanged=True; no DATM or forcing writes",sep="")


if __name__=="__main__":
    main()

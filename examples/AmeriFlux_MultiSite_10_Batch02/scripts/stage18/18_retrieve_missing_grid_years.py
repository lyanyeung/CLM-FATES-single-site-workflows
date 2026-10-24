#!/usr/bin/env python3
"""Stage18: verified, resumable ERA5 dewpoint GRID-YEAR retrieval for Batch02.

Stage17 partitions 4,884 source humidity blockers into 42 site-years, of which
five Stage15 site-years are already downloaded. Two tower sites may share
a 0.25-degree ERA5 grid point, so the remaining 37 site-years should require
fewer than 37 independent CDS downloads.

--check: inspect exact plan, original hashes, existing receipts; NO writes.
--download: fetch at most --max-new GRID-YEARS (default 3), validate each, and
            persist receipts for safe incremental repetition. No forcing edits.

Each grid-year's request preserves the FULL UTC calendar year with a three-day
buffer on both ends, so later local-standard tower time alignment is possible.
US-Ho1 UTC-5 remains provisional pending same-release BADM confirmation.
Never interpret the resulting hourly netCDF as native half-hour forcing.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

import numpy as np
import pandas as pd

PLAN = (Path.home() /
    "AmeriFlux_Batch02_stage17_anomaly_year_plan_20261022T034021Z_5704060a" /
    "CDS_anomaly_site_year_plan.json")
STAGE13 = (Path.home() /
    "AmeriFlux_Batch02_stage13_plan_20261022T023406Z_7614f826" / "request_plan.json")
STAGE15 = Path.home() / "AmeriFlux_Batch02_ERA5_five_one_year_controls"
STAGE11 = (Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02") /
    "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b")
OUTPUT = Path.home() / "AmeriFlux_Batch02_ERA5_missing_grid_years"
STAGE13_SHA = "0785bb8b85b5e8c9fee7b64d6f63016e58e12db03e31cf53c20e265e803f9523"
DATASET = "reanalysis-era5-single-levels-timeseries"
VARS = ["2m_temperature","2m_dewpoint_temperature","surface_pressure"]
YEARS = {"US-EML":(2008,2023),"US-GLE":(2005,2020),
         "US-Ho1":(1996,2023),"US-ICh":(2007,2025),"US-ICt":(2007,2025)}
FOCUS = {"US-EML":2009,"US-GLE":2005,"US-Ho1":1996,
         "US-ICh":2007,"US-ICt":2007}
MAX_NETCDF_BYTES = 128 * 1024 * 1024

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1 << 20),b""): h.update(b)
    return h.hexdigest()

def dump_json(path,value):
    # Atomic new receipt: do not silently replace an existing verified receipt.
    with Path(path).open("x",encoding="utf-8") as f:
        json.dump(value,f,indent=2)
        f.write("\n")

def identity(row):
    return (float(row["ERA_grid_lat_expected"]),
            float(row["ERA_grid_lon_expected"]),int(row["year"]))

def foldername(key):
    lat,lon,year=key
    return f"ERA5_{year}_lat{lat:+07.2f}_lon{lon:+08.2f}"

def load_plan():
    if sha(STAGE13)!=STAGE13_SHA:
        raise ValueError("Pinned Stage13 plan SHA256 differs")
    if not (PLAN.parent/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage17 review-only marker absent")
    info=json.loads(PLAN.read_text(encoding="utf-8"))
    if info.get("schema")!="STAGE17_ANOMALY_YEAR_RETRIEVAL_PLAN_v1" or \
       info.get("science_status")!="ONLY_RETRIEVAL_PLAN_NO_DATM_APPROVAL" or \
       info.get("stage13_plan_sha256")!=STAGE13_SHA:
        raise ValueError("Stage17 plan schema/science-status differs")
    stage11_manifest=STAGE11/"manifest.json"
    proposals=STAGE11/"cold_humidity_repair_proposals.csv"
    if not (STAGE11/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage11 not marked unapproved")
    if sha(stage11_manifest)!=info["original_stage11_manifest_sha256"] or \
       sha(proposals)!=info["original_stage11_sha256"]:
        raise ValueError("Stage17 references changed Stage11 manifest/target CSV")
    original=pd.read_csv(proposals)
    if len(original)!=4884 or original.duplicated(["site","time"]).any():
        raise ValueError("Stage11 target count/identity changed")
    original["year"]=pd.to_datetime(original.time,errors="raise").dt.year
    counts=original.groupby(["site","year"],sort=True).agg(
        n=("time","size"),
        provisional=("decision",lambda x:int(x.eq("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED").sum())),
        holds=("decision",lambda x:int(x.eq("HOLD_NO_SUPPORTED_ANALOGUE").sum()))
    )
    if counts.n.sum()!=4884 or counts.provisional.sum()!=4870 or counts.holds.sum()!=14:
        raise ValueError("Unexpected Stage11 distribution")
    entries=info["site_years"]
    if len(entries)!=42 or set(x["site"] for x in entries)!=set(YEARS):
        raise ValueError("Site-year list differs from Stage17")
    prior=json.loads(STAGE13.read_text())
    metadata={r["site"]:r for r in prior["sites"]}
    seen=set()
    preexisting=[]
    for r in entries:
        site,year=r["site"],int(r["year"])
        if (site,year) in seen or not YEARS[site][0]<=year<=YEARS[site][1]:
            raise ValueError("Site-year repeated or outside full release")
        seen.add((site,year))
        if (site,year) not in counts.index:
            raise ValueError("Planned site-year has no Stage11 blockers")
        c=counts.loc[(site,year)]
        if (int(c["n"]),int(c["provisional"]),int(c["holds"])) != (
           r["n_stage11_targets"],r["n_stage11_provisional"],r["n_stage11_holds"]):
            raise ValueError("Site-year count changed: "+site+" "+str(year))
        req=r["CDS_request"]
        coord=metadata[site]["metadata"]
        if req.get("variable")!=VARS or req.get("data_format")!="netcdf" or \
           req.get("location")!={"latitude":coord["latitude"],
                                  "longitude":coord["longitude"]} or \
           req.get("date")!=[f"{year-1}-12-29",f"{year+1}-01-03"] or \
           r.get("CDS_dataset")!=DATASET:
            raise ValueError("Unpinned CDS request: "+site+" "+str(year))
        if (round(4*float(coord["latitude"]))/4,
            round(4*float(coord["longitude"]))/4) != identity(r)[:2]:
            raise ValueError("Nearest ERA grid unexpectedly changed: "+site)
        existing=bool(r["existing_Stage15_verified"])
        if existing != (year==FOCUS[site]):
            raise ValueError("Unexpected Stage15 site-year reuse scope")
        if existing:
            pr=r["original_stage15_receipt"]
            p=Path(pr["receipt_path"]).resolve()
            if STAGE15.resolve() not in p.parents or sha(p)!=pr["receipt_sha256"]:
                raise ValueError("Pinned Stage15 receipt differs: "+site)
            receipt=json.loads(p.read_text())
            if receipt["site"]!=site or receipt["year"]!=year or \
               receipt["netcdf_sha256"]!=pr["netcdf_sha256"] or \
               sha(receipt["netcdf_path"])!=pr["netcdf_sha256"]:
                raise ValueError("Stage15 previously downloaded bytes differ")
            preexisting.append(r)
    if set(counts.index)!=seen or sum(x["n_stage11_targets"] for x in entries)!=4884:
        raise ValueError("Site-year coverage incomplete")
    keys={identity(x) for x in entries}
    prior_grid={identity(x) for x in preexisting}
    missing_group=keys-prior_grid
    missing_rows=[x for x in entries if not x["existing_Stage15_verified"]]
    if len(preexisting)!=5 or len(missing_rows)!=37 or len(keys)!=38 or \
       len(prior_grid)!=4 or len(missing_group)!=34:
        raise ValueError("Expected 42 site-years / 38 unique grids / 34 missing grid-years")
    grouped={key:[x for x in entries if identity(x)==key]
             for key in sorted(missing_group,key=lambda x:(x[2],x[0],x[1]))}
    # For a shared grid-year, representative coordinate must actually
    # select the same 0.25-degree grid cell. Select the largest anomaly count.
    for key in grouped:
        grouped[key].sort(key=lambda x:(-x["n_stage11_targets"],x["site"]))
    return info, grouped, preexisting

def filetype(path):
    with Path(path).open("rb") as f:b=f.read(8)
    if b==b"\x89HDF\r\n\x1a\n":return "NETCDF4"
    if b[:4] in (b"CDF\x01",b"CDF\x02",b"CDF\x05"):return "NETCDF3"
    if b[:4]==b"PK\x03\x04":return "ZIP"
    return "UNKNOWN"

def unpack(payload,out):
    kind=filetype(payload)
    if kind in {"NETCDF4","NETCDF3"}:return payload,kind
    if kind!="ZIP" or not zipfile.is_zipfile(payload):
        raise ValueError("Original CDS payload is not NetCDF or a safe ZIP: "+str(payload))
    with zipfile.ZipFile(payload) as z:
        parts=[m for m in z.infolist() if not m.is_dir()]
        if len(parts)!=1:raise ValueError("Expected one point-series NetCDF ZIP member")
        member=parts[0]
        name=PurePosixPath(member.filename)
        if len(name.parts)!=1 or not name.name.lower().endswith(".nc") or \
           not 0<member.file_size<MAX_NETCDF_BYTES:
            raise ValueError("Unexpected NetCDF ZIP member path/length")
        dest=out/"era5_dewpoint_hourly_UTC.nc"
        if dest.exists():
            if dest.stat().st_size!=member.file_size or \
               filetype(dest) not in ("NETCDF4","NETCDF3"):
                raise ValueError("Existing extracted NetCDF is incomplete; manually review")
            return dest,kind
        with z.open(member) as src, dest.open("xb") as target:
            shutil.copyfileobj(src,target,1024*1024)
        if dest.stat().st_size!=member.file_size or \
           filetype(dest) not in ("NETCDF4","NETCDF3"):
            raise ValueError("Extracted bytes invalid (original retained)")
        return dest,kind

def verify_netcdf(path,year,expected_lat,expected_lon):
    import xarray as xr
    with xr.open_dataset(path,engine="netcdf4") as ds:
        if set(ds.data_vars)!={"t2m","d2m","sp"}:
            raise ValueError("Wrong ERA5 variables")
        for field,unit in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if ds[field].attrs.get("units")!=unit or \
               tuple(ds[field].dims)!=("valid_time",):
                raise ValueError("Wrong ERA5 unit/dimensions for "+field)
        t=pd.to_datetime(ds.valid_time.values,utc=True)
        exp=pd.date_range(f"{year-1}-12-29 00:00",
                          f"{year+1}-01-03 23:00",freq="h",tz="UTC")
        if len(t)!=len(exp) or not np.array_equal(t.asi8,exp.asi8):
            raise ValueError("ERA5 missing/extra/duplicate UTC hours")
        lat=float(np.asarray(ds.latitude.values).ravel()[0])
        lon=float(np.asarray(ds.longitude.values).ravel()[0])
        a=ds.t2m.to_numpy().astype(float)-273.15
        d=ds.d2m.to_numpy().astype(float)-273.15
        pressure=ds.sp.to_numpy().astype(float)
    if abs(lat-expected_lat)>.001 or abs(lon-expected_lon)>.001:
        raise ValueError("ERA5 actual grid does not match Stage17 grid")
    if not (np.isfinite(a).all() and np.isfinite(d).all() and
            np.isfinite(pressure).all() and ((a>-90)&(a<65)).all() and
            ((d>-100)&(d<65)).all() and
            ((pressure>49000)&(pressure<111000)).all()):
        raise ValueError("ERA5 temperature/dewpoint/pressure outside screen")
    with np.errstate(all="ignore"):
        vapor=lambda x:6.112*np.exp(17.67*x/(x+243.5))
        e=vapor(d)
        rh=100*e/vapor(a)
        q=.622*e*100/(pressure-.378*e*100)
        vpd=vapor(a)-e
    invalid=~(np.isfinite(rh)&(rh>0)&(rh<=100.05)&
              np.isfinite(q)&(q>0)&(q<.08)&
              np.isfinite(vpd)&(vpd>=-.005))
    return dict(n_hourly_UTC=len(t),first_UTC=str(t.min()),last_UTC=str(t.max()),
                grid_lat=lat,grid_lon=lon,
                RH_min=float(rh.min()),RH_max=float(rh.max()),
                invalid_water_RH_QBOT=int(invalid.sum()),
                T_min_C=float(a.min()),T_max_C=float(a.max()),
                Td_min_C=float(d.min()),Td_max_C=float(d.max()),
                status="REANALYSIS_NUMERIC_SCREEN_ONLY_NOT_FOR_DATM")

def read_receipt(path,folder,key,plan_sha):
    data=json.loads(path.read_text())
    if data.get("stage17_plan_sha256")!=plan_sha or \
       tuple(data.get("grid_year_key",[]))!=key or data.get("year")!=key[2] or \
       data.get("science_approved") is not False:
        raise ValueError("Receipt identity or science status differs: "+str(path))
    for field,digest_field in (("netcdf_path","netcdf_sha256"),
                              ("original_payload_path","original_payload_sha256")):
        p=Path(data[field]).resolve()
        if folder.resolve() not in p.parents or not p.is_file() or \
           sha(p)!=data[digest_field]:
            raise ValueError("A previously verified file was modified: "+str(p))
    return data

def main():
    global PLAN
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--check",action="store_true")
    m.add_argument("--download",action="store_true")
    p.add_argument("--plan",type=Path,default=PLAN)
    p.add_argument("--output-root",type=Path,default=OUTPUT)
    p.add_argument("--max-new",type=int,default=3,
                   help="Maximum new unique grid-year CDS requests this run (1-10, default 3)")
    args=p.parse_args()
    PLAN=args.plan.expanduser().resolve(strict=True)
    if not 1<=args.max_new<=10:
        raise ValueError("--max-new must be between 1 and 10")
    plan,groups,done=load_plan()
    plan_sha=sha(PLAN)
    out=args.output_root.expanduser().resolve()
    forbidden=[STAGE11.resolve(),STAGE15.resolve(),STAGE13.parent.resolve(),PLAN.parent]
    if any(out==x or out in x.parents or x in out.parents for x in forbidden):
        raise ValueError("Unsafe output location: cannot overlap protected input trees")
    if out.is_symlink():raise ValueError("Output may not be symlink")
    completed={}
    for key,rows in groups.items():
        folder=out/foldername(key)
        receipt=folder/"verified_receipt.json"
        if receipt.is_file():
            completed[key]=read_receipt(receipt,folder,key,plan_sha)
        elif folder.exists():
            if not folder.is_dir() or not (folder/"INCOMPLETE_REVIEW_ONLY").is_file():
                raise ValueError("Unexpected pre-existing output folder: "+str(folder))
    new_keys=sorted([k for k in groups if k not in completed],
        key=lambda k:(-sum(r["n_stage11_targets"] for r in groups[k]),k[2],k[0],k[1]))
    print("========== STAGE18 PINNED ERA5 GRID-YEAR QUEUE ==========",flush=True)
    print("Stage17 plan SHA256:",plan_sha,flush=True)
    print("Stage15 original site-years: 5 / five; distinct existing grids: 4")
    print("Additional missing site-years: 37; unique grid-year downloads: 34")
    print("New grid-years VERIFIED so far:",len(completed),"/34",flush=True)
    print("Additional grid-years remaining:",len(new_keys),flush=True)
    print("Next grid-years this invocation: at most",args.max_new,flush=True)
    for key in new_keys[:args.max_new]:
        print("QUEUE",foldername(key),"sites=",
              ",".join(sorted({x["site"] for x in groups[key]})),
              "targets=",sum(r["n_stage11_targets"] for r in groups[key]),flush=True)
    if args.check:
        print("CHECK ONLY: no CDS requests, files or model changes")
        return 0
    if out.exists():
        config=json.loads((out/"config.json").read_text())
        if config.get("stage17_plan_sha256")!=plan_sha or \
           config.get("schema")!="STAGE18_GRID_YEAR_RETRIEVAL_v1":
            raise ValueError("Stage18 output config belongs to a different study")
    else:
        out.mkdir(parents=True,exist_ok=False)
        dump_json(out/"config.json",dict(
            schema="STAGE18_GRID_YEAR_RETRIEVAL_v1",
            stage17_plan=str(PLAN),stage17_plan_sha256=plan_sha,
            max_expected_new_gridyears=34,science_status="CDS_ONLY_NOT_FOR_DATM"))
        (out/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
            "CDS retrieval and physical screening only, no forcing approval.\n")
    if not new_keys:
        print("STAGE18: all 34 new grid-years verified; CDS SKIPPED.")
        return 0
    import cdsapi
    client=cdsapi.Client()
    for key in new_keys[:args.max_new]:
        group=groups[key]
        selected=group[0] # highest number of Stage11 targets
        req=selected["CDS_request"]
        folder=out/foldername(key)
        folder.mkdir(exist_ok=True)
        marker=folder/"INCOMPLETE_REVIEW_ONLY"
        if not marker.exists():marker.write_text("Unverified CDS payload; not for DATM.\n")
        raw=folder/"original_cds_response.bin"
        if raw.exists():
            print("REUSING PREVIOUS PAYLOAD:",foldername(key),flush=True)
        else:
            print("CDS REQUEST:",foldername(key),
                  "primary site=",selected["site"],flush=True)
            client.retrieve(DATASET,req,str(raw))
        if not raw.is_file() or raw.stat().st_size<100:
            raise ValueError("CDS payload missing or empty; preserve original for review")
        nc,fmt=unpack(raw,folder)
        stats=verify_netcdf(nc,key[2],key[0],key[1])
        if stats["invalid_water_RH_QBOT"]:
            raise ValueError("Numerically suspicious ERA5 year; no receipt written")
        data=dict(schema="STAGE18_VERIFIED_GRIDYEAR_v1",
            stage17_plan_sha256=plan_sha,
            grid_year_key=list(key),
            year=key[2],
            all_sites_sharing_grid=[x["site"] for x in group],
            individual_target_counts={x["site"]:x["n_stage11_targets"] for x in group},
            CDS_dataset=DATASET,CDS_request=req,
            original_payload_path=str(raw.resolve()),original_payload_sha256=sha(raw),
            netcdf_path=str(nc.resolve()),netcdf_sha256=sha(nc),
            cds_response_format=fmt,science_approved=False,
            interpolated_to_half_hour=False,
            US_Ho1_timezone_status="EXTERNAL_STANDARD_TIME_EVIDENCE_ONLY_BADM_PENDING",
            **stats)
        dump_json(folder/"verified_receipt.json",data)
        print("GRID-YEAR VERIFIED:",foldername(key),
              "hours=",stats["n_hourly_UTC"],
              "RH=",round(stats["RH_min"],2),"to",round(stats["RH_max"],2),
              "sites=",data["all_sites_sharing_grid"],flush=True)
    print("STAGE18 BATCH FINISHED: run --check for next queue, then --download again.")
    print("OUTPUT ROOT:",out)
    print("NO DATM, CIME, model case, raw source or Slurm jobs modified.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

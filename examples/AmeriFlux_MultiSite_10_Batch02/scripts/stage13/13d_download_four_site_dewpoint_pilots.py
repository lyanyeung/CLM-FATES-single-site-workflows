#!/usr/bin/env python3
"""Stage13d: four AmeriFlux Batch02 ERA5 dewpoint PILOT downloads and validation.

Fetch only five short event windows across the four OTHER humidity-blocked
sites, NOT historical full-series data. The Stage13 coordinate plan is required.
CDS may return ZIP even for a NetCDF request. Keep downloaded payload and
extracted NetCDF separately, never overwrite. Do not interpret a UTC timestamp
as a tower-local time or infer the timezone from RMSE. Nothing here modifies
raw forcing, Stage07-13c, CIME/DATM, model experiments, or Slurm jobs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
from uuid import uuid4
import zipfile

import numpy as np
import pandas as pd

PLAN = Path.home() / "AmeriFlux_Batch02_stage13_plan_20261022T023406Z_7614f826" / "request_plan.json"
DATASET = "reanalysis-era5-single-levels-timeseries"
VARS = ["2m_temperature", "2m_dewpoint_temperature", "surface_pressure"]
# Chosen to include documented Stage08/11 humidity failures; pad days
# accommodate any plausible continental US standard UTC offset.
EVENTS = (
    ("US-GLE", "winter_2005", "2005-12-05", "2005-12-09"),
    ("US-Ho1", "winter_1996", "1996-12-25", "1996-12-29"),
    ("US-ICh", "winter_2007", "2007-02-19", "2007-03-02"),
    ("US-ICt", "winter_2007_jan", "2006-12-31", "2007-01-04"),
    ("US-ICt", "mild_2007_dec", "2007-11-30", "2007-12-04"),
)
MAX_UNCOMPRESSED = 50 * 1024 * 1024

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def magic(blob):
    if blob.startswith(b"\x89HDF\r\n\x1a\n"): return "NETCDF4"
    if blob.startswith(b"CDF\x01") or blob.startswith(b"CDF\x02"): return "NETCDF3"
    if blob.startswith(b"PK\x03\x04"): return "ZIP"
    return "UNKNOWN"

def plan_check(path):
    p = Path(path).expanduser().resolve(strict=True)
    x = json.loads(p.read_text(encoding="utf-8"))
    if x.get("schema") != "Stage13_ERA5_TD2M_REQUEST_PLAN_v1" or x.get("dataset") != DATASET:
        raise ValueError("Not the original Stage13 point-timeseries request plan")
    if x.get("science_status") != "RETRIEVAL_PLAN_ONLY_NO_HUMIDITY_APPROVAL":
        raise ValueError("Unexpected Stage13 approval state")
    sites = {s["site"]:s for s in x["sites"]}
    if len(sites) != 5 or set(sites) != {"US-EML","US-GLE","US-Ho1","US-ICh","US-ICt"}:
        raise ValueError("Stage13 location list differs")
    for site, row in sites.items():
        if row.get("cds_dataset") != DATASET:
            raise ValueError("Unexpected dataset for "+site)
        meta = row["metadata"]
        lat, lon = float(meta["latitude"]), float(meta["longitude"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Invalid coordinates for "+site)
        if meta["tower_local_standard_to_UTC_offset_hours"] != "UNRESOLVED_MANUAL_VERIFICATION_REQUIRED":
            raise ValueError("Do not assume a verified local time offset")
        if row["cds_request"]["variable"] != VARS:
            raise ValueError("Unexpected climate variable list")
        if row["cds_request"]["location"] != {"latitude":lat, "longitude":lon}:
            raise ValueError("Coordinate mismatch within Stage13 manifest")
    return x, sites, p

def request_for(row, start, end):
    return dict(variable=list(VARS),
        location=dict(latitude=float(row["metadata"]["latitude"]),
                      longitude=float(row["metadata"]["longitude"])),
        date=[start,end], data_format="netcdf")

def extract_payload(payload, subdir):
    with payload.open("rb") as f: kind=magic(f.read(8))
    if kind in {"NETCDF4","NETCDF3"}:
        return payload, kind
    if kind != "ZIP" or not zipfile.is_zipfile(payload):
        raise RuntimeError(f"Unrecognized CDS response; preserved at {payload}")
    with zipfile.ZipFile(payload) as z:
        items=[i for i in z.infolist() if not i.is_dir()]
        if len(items)!=1:
            raise RuntimeError("Expected exactly one NetCDF payload in point-series ZIP")
        info=items[0]
        pp=PurePosixPath(info.filename)
        if len(pp.parts)!=1 or ".." in pp.parts or not pp.name.endswith(".nc"):
            raise RuntimeError("Unsafe or non-NetCDF ZIP member")
        if not 0 < info.file_size < MAX_UNCOMPRESSED:
            raise RuntimeError("ZIP member size out of safe range")
        extracted=subdir/"era5_point_extracted.nc"
        if extracted.exists():
            raise FileExistsError("Refusing to overwrite extracted NetCDF")
        with z.open(info) as src, extracted.open("xb") as dst:
            shutil.copyfileobj(src,dst,1024*1024)
        if extracted.stat().st_size!=info.file_size:
            raise RuntimeError("Extraction size mismatch")
    with extracted.open("rb") as f:
        if magic(f.read(8)) not in {"NETCDF4","NETCDF3"}:
            raise RuntimeError("Extracted file is not NetCDF")
    return extracted, kind

def validate_netcdf(path, site, row, start, end):
    import xarray as xr
    with xr.open_dataset(path, engine="netcdf4") as d:
        if set(d.data_vars)!={"t2m","d2m","sp"}:
            raise ValueError("ERA5 variable schema differs")
        if any(tuple(d[key].dims)!=("valid_time",) for key in ("t2m","d2m","sp")):
            raise ValueError("Expected single grid point hourly timeseries")
        for field, unit in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if d[field].attrs.get("units")!=unit:
                raise ValueError("Wrong units for "+field)
        t=pd.to_datetime(d.valid_time.values,utc=True)
        expected=pd.date_range(start+"T00:00",end+"T23:00",freq="h",tz="UTC")
        if len(t)!=len(expected) or not np.array_equal(t.asi8,expected.asi8):
            raise ValueError("Missing/duplicate or unexpected UTC time stamps")
        ta=np.asarray(d.t2m.values,dtype=float)
        td=np.asarray(d.d2m.values,dtype=float)
        ps=np.asarray(d.sp.values,dtype=float)
        if not (np.isfinite(ta).all() and np.isfinite(td).all() and np.isfinite(ps).all()):
            raise ValueError("Missing/non-finite ERA5 values")
        if not ((ta>180).all() and (ta<340).all() and
                (td>170).all() and (td<340).all() and
                (ps>49000).all() and (ps<111000).all()):
            raise ValueError("ERA5 unit/physical screening failed")
        lat=float(np.asarray(d.latitude.values).ravel()[0])
        lon=float(np.asarray(d.longitude.values).ravel()[0])
        if abs(lat-float(row["metadata"]["latitude"]))>0.126 or \
           abs(lon-float(row["metadata"]["longitude"]))>0.126:
            raise ValueError("Grid point not nearest expected coordinate")
        with np.errstate(all="ignore"):
            s=lambda k: 6.112*np.exp(17.67*(k-273.15)/((k-273.15)+243.5))
            relative=100*s(td)/s(ta)
            q=.622*s(td)*100/(ps-.378*s(td)*100)
        invalid=int(((relative<=0)|(relative>100.05)|~np.isfinite(relative)).sum())
        supersaturated=int(((td-ta)>.05).sum())
        stats=dict(site=site, first_utc=str(t.min()), last_utc=str(t.max()),
            utc_records=len(t), latitude=lat, longitude=lon,
            t2m_min_C=float(ta.min()-273.15), t2m_max_C=float(ta.max()-273.15),
            d2m_min_C=float(td.min()-273.15), d2m_max_C=float(td.max()-273.15),
            rh_min_pct=float(relative.min()), rh_max_pct=float(relative.max()),
            relative_humidity_invalid_count=invalid,
            dewpoint_exceeds_temperature_gt005C=supersaturated,
            qbot_min_kgkg=float(q.min()), qbot_max_kgkg=float(q.max()),
            status="PILOT_REVIEW_ONLY_NO_DATM")
    return stats

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan",type=Path,default=PLAN)
    p.add_argument("--output-root",type=Path)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--download",action="store_true")
    args=p.parse_args()
    manifest, sites, plan_file=plan_check(args.plan)
    pinned_plan_hash=sha(plan_file)
    print("STAGE13d PRECHECK: original Stage13 plan SHA256",pinned_plan_hash,flush=True)
    for site, tag, start, end in EVENTS:
        req=request_for(sites[site],start,end)
        print("PILOT",site,tag,json.dumps(req,sort_keys=True),flush=True)
    if args.check:
        print("CHECK ONLY: 5 small event windows, four sites, no CDS requests or files")
        return 0
    from cdsapi import Client
    if not (Path.home()/".cdsapirc").is_file():
        raise ValueError("Missing ~/.cdsapirc (credentials will never be printed)")
    out=args.output_root.expanduser().resolve() if args.output_root else (
        Path.home()/("AmeriFlux_Batch02_ERA5_four_site_pilots_"+
                     datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
                     "_"+uuid4().hex[:8]))
    if out.exists() or out==plan_file or out in plan_file.parents or plan_file in out.parents:
        raise ValueError("Unsafe or existing output folder")
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_REVIEW_ONLY_NO_DATM").write_text("Partial retrieval; not approved.\n")
    client=Client()
    summaries=[]
    for site, tag, start, end in EVENTS:
        sub=out/(site+"_"+tag)
        sub.mkdir(exist_ok=False)
        target=sub/"original_cds_response.bin"
        req=request_for(sites[site],start,end)
        print("CDS SUBMIT:",site,tag,start,end,flush=True)
        client.retrieve(DATASET,req,str(target))
        if not target.is_file() or target.stat().st_size<100:
            raise RuntimeError("CDS returned no substantive file for "+site)
        netcdf,fmt=extract_payload(target,sub)
        audit=validate_netcdf(netcdf,site,sites[site],start,end)
        audit.update(event=tag,requested_start=start,requested_end=end,
                     cds_payload_format=fmt, cds_payload_sha256=sha(target),
                     netcdf_sha256=sha(netcdf), netcdf_path=str(netcdf))
        (sub/"audit.json").write_text(json.dumps(audit,indent=2)+"\n")
        summaries.append(audit)
        print("PILOT VERIFIED:",site,tag,"n=",audit["utc_records"],
              "RH",round(audit["rh_min_pct"],2),"-",round(audit["rh_max_pct"],2),
              "invalid=",audit["relative_humidity_invalid_count"],flush=True)
    if sha(plan_file)!=pinned_plan_hash:
        raise RuntimeError("Stage13 plan changed during download")
    (out/"manifest.json").write_text(json.dumps(dict(
        source_stage13_plan=str(plan_file),stage13_plan_sha256=pinned_plan_hash,
        script_sha256=sha(Path(__file__)),dataset=DATASET,
        pilot_windows=summaries,
        science_status="PILOT_DIAGNOSTIC_ONLY_HUMIDITY_NOT_APPROVED",
        note="Tower local standard time UTC offset unresolved; ERA5 UTC hourly only",
        model_output_created=False),indent=2)+"\n")
    (out/"INCOMPLETE_REVIEW_ONLY_NO_DATM").unlink()
    (out/"COMPLETE_PILOT_DATA_NOT_FOR_DATM_OR_SPINUP").write_text(
        "Five pilot ERA5 time windows downloaded; no science/model approval.\n")
    print("STAGE13d PILOT ROOT:",out,flush=True)
    print("All outputs are independent CDS pilot data; no existing forcing or model touched.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

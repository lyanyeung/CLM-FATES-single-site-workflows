#!/usr/bin/env python3
"""JapanFlux Stage05T: inspect actual CDS 2005-08-11 JP-Khw pilot ZIP, NO repairs.

Uses the downloaded original CDS ZIP file and Stage05R SOURCE-VERIFIED UTC
request TSV only. Read-only, no CDS request, no original ZIP or forcing edits,
no Slurm. Verify expected exact pilot file SHA256 before parsing ANY member.
Inspect CSV schemas/time/grid, preserve raw data and produce context preview.
UTC hourly ERA5-Land is NOT directly interchangeable with half-hour JPF
downscaled *_ERA; extracted numeric conversions are provisional, not repairs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import zipfile

EXPECTED_SHA="111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0"
TARGET_SITE="JP-Khw"
TARGET_DATE="2005-08-11"
TARGET_BIF_SHA="eef29bcb9bd97874dad32469b1821b61760f3111cbc3836ad6300350b18217b4"
EXPECTED_VARIABLES={
    "2m_temperature":("K","degC",lambda n:n-273.15,(-90,65)),
    "surface_pressure":("Pa","kPa",lambda n:n/1000,(0,120)),
    "surface_thermal_radiation_downwards":("J m-2 in previous hourly interval",
                                           "W m-2 hourly mean",lambda n:n/3600,(0,1500)),
}
ALIASES={
    "2m_temperature":{"2m_temperature","t2m"},
    "surface_pressure":{"surface_pressure","sp"},
    "surface_thermal_radiation_downwards":{"surface_thermal_radiation_downwards","strd"},
}
TIME_HEADERS={"time","valid_time","date","datetime","timestamp"}
LAT_HEADERS={"latitude","lat"}
LON_HEADERS={"longitude","lon"}
EXPECTED_HOURS={"14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"}
CONTEXT_FIELDS=("UTC_hour","CDS_member","ERA5L_grid_latitude","ERA5L_grid_longitude",
                "variable","raw_value","assumed_raw_units","converted_value",
                "converted_units","in_Stage05R_requested_hours","comparison_status")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b=f.read(1024*1024)
            if not b:break
            h.update(b)
    return h.hexdigest()

def read_stage05r(path:Path)->dict:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    relevant=[r for r in rows if r.get("site")==TARGET_SITE and r.get("UTC_day")==TARGET_DATE]
    keys=set()
    for r in relevant:
        if r["original_BIF_SHA256"]!=TARGET_BIF_SHA or r["coordinate_source_status"]!="ORIGINAL_BIF_VERIFIED":
            raise ValueError("Original JP-Khw BIF source not verified")
        if (r["tower_latitude"]!="33.13658" or r["tower_longitude"]!="130.70834"
            or r["tower_elevation_m"]!="196.0"):
            raise ValueError("Pilot source tower coordinates unexpectedly changed")
        key=(r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"])
        if key in keys:raise ValueError("Duplicate Stage05R requested UTC hour/variable")
        keys.add(key)
        if r["returned_ERA5L_grid_cell_status"]!="NOT_RETRIEVED_NEAREST_0p1_GRID_NOT_VERIFIED":
            raise ValueError("Stage05R pilot grid not in expected HOLD")
        if r["independent_ERA5L_values_status"]!="NOT_DOWNLOADED":
            raise ValueError("Stage05R provenance changed")
        dt=datetime.strptime(r["UTC_hour"],"%Y%m%d%H%M")
        if dt.strftime("%Y-%m-%d")!=TARGET_DATE:
            raise ValueError("Pilot UTC-date mismatch")
    hours={datetime.strptime(t,"%Y%m%d%H%M").strftime("%H:%M") for t,v in keys}
    if hours!=EXPECTED_HOURS or set(v for t,v in keys)!=set(EXPECTED_VARIABLES):
        raise ValueError("Unexpected Stage05R JP-Khw 2005-08-11 time/variable scope")
    return {"requested_site_hour_variable_keys":keys,
            "requested_UTC_hours":sorted(hours),
            "original_BIF_SHA256":TARGET_BIF_SHA}

def normalize_header(s:str)->str:
    return s.strip().strip("\ufeff").lower().replace(" ","_").replace("-","_")

def parse_time(s:str)->str|None:
    raw=(s or "").strip()
    if not raw:return None
    # ISO 8601, including trailing Z / UTC and explicit offsets.
    try:
        dt=datetime.fromisoformat(raw.replace("Z","+00:00"))
    except ValueError:
        dt=None
    if dt is None:
        for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M",
                    "%Y/%m/%d %H:%M:%S","%Y%m%d%H%M"):
            try:
                dt=datetime.strptime(raw,fmt)
                break
            except ValueError:
                pass
    if dt is None:return None
    if dt.tzinfo is not None:
        dt=dt.astimezone(timezone.utc).replace(tzinfo=None)
    if dt.minute!=0 or dt.second!=0 or dt.microsecond:
        return None
    return dt.strftime("%Y-%m-%dT%H:%MZ")

def maybe_float(raw:str)->float|None:
    try:
        v=float(raw)
    except (ValueError,TypeError):
        return None
    return v if math.isfinite(v) else None

def one_csv(member_name:str,text:str)->tuple[dict,list[dict]]:
    reader=csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return {"member":member_name,"status":"NO_CSV_HEADER","headers":[]},[]
    original_headers=reader.fieldnames
    headers={normalize_header(h):h for h in original_headers if h is not None}
    timecol=next((headers[n] for n in TIME_HEADERS if n in headers),None)
    latcol=next((headers[n] for n in LAT_HEADERS if n in headers),None)
    loncol=next((headers[n] for n in LON_HEADERS if n in headers),None)
    vars_={}
    for var,aliases in ALIASES.items():
        matches=[headers[n] for n in sorted(aliases) if n in headers]
        if len(matches)>1:
            raise ValueError("Multiple data columns for "+var+" in "+member_name)
        if matches:vars_[var]=matches[0]
    records=list(reader)
    if len(records)>1000:
        raise ValueError("Unexpected >1000 rows in one-day time-series CSV")
    info={
        "member":member_name,"status":"CSV_SCANNED_SCHEMA_ONLY_WHEN_UNKNOWN",
        "headers":original_headers,"rows":len(records),
        "time_column":timecol,"latitude_column":latcol,
        "longitude_column":loncol,"variables_recognized":vars_,
        "first_two_raw_rows":records[:2], "time_parse_success":0,
    }
    extracted=[]
    if timecol is None:
        info["status"]="NO_RECOGNIZED_UTC_TIME_COLUMN_HOLD"
        return info,extracted
    for row in records:
        utc=parse_time(row.get(timecol,""))
        if not utc:continue
        info["time_parse_success"]+=1
        if not utc.startswith(TARGET_DATE):
            continue
        for var,col in vars_.items():
            raw=maybe_float(row.get(col))
            if raw is None:continue
            src_unit,unit,convert,expected_range=EXPECTED_VARIABLES[var]
            converted=convert(raw)
            lat=maybe_float(row.get(latcol)) if latcol else None
            lon=maybe_float(row.get(loncol)) if loncol else None
            grid_status=(
                "GRID_LATLON_FROM_CSV_UNVERIFIED_ELEVATION"
                if lat is not None and lon is not None else
                "CSV_HAS_NO_NUMERIC_GRID_LATLON_HOLD")
            if (lat is not None and lon is not None
                and not (abs(lat-33.13658)<=0.11 and abs(lon-130.70834)<=0.11)):
                grid_status="GRID_FAR_FROM_ORIGINAL_TOWER_HOLD"
            clock=utc[11:16]
            bad=not (expected_range[0]<=converted<=expected_range[1])
            extracted.append({
                "UTC_hour":utc,"CDS_member":member_name,
                "ERA5L_grid_latitude":lat if lat is not None else "",
                "ERA5L_grid_longitude":lon if lon is not None else "",
                "variable":var,"raw_value":raw,
                "assumed_raw_units":src_unit,
                "converted_value":round(converted,6),
                "converted_units":unit,
                "in_Stage05R_requested_hours":int(clock in EXPECTED_HOURS),
                "comparison_status":(
                    ("NUMERIC_OUT_OF_BROAD_SCREEN_HOLD" if bad else grid_status)
                    + "_NO_REPLACEMENT_APPROVAL")
            })
    if info["time_parse_success"]==0:
        info["status"]="UNRECOGNIZED_TIME_VALUE_FORMAT_HOLD"
    return info,extracted

def inspect_zip(path:Path)->tuple[list[dict],list[dict],dict]:
    source_sha=sha256(path)
    if source_sha!=EXPECTED_SHA:
        raise ValueError("CDS raw response SHA mismatch. Do not inspect an unpinned file: "+source_sha)
    if not zipfile.is_zipfile(path):
        raise ValueError("Expected original CDS response to be ZIP")
    metadata=[]; rows=[]
    total_uncompressed=0
    with zipfile.ZipFile(path) as z:
        members=z.infolist()
        if not 1<=len(members)<=12:
            raise ValueError("Unexpected CDS ZIP member count")
        for inf in members:
            if inf.is_dir():
                continue
            name=inf.filename
            # No extraction, but reject dangerous archive names anyway.
            pure=PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "\\" in name:
                raise ValueError("Unsafe archive member name")
            if inf.file_size>1_000_000:
                raise ValueError("One-day CSV unexpectedly large")
            total_uncompressed+=inf.file_size
            if total_uncompressed>5_000_000:
                raise ValueError("Uncompressed archive > 5 MB")
            if not name.lower().endswith(".csv"):
                metadata.append({"member":name,"status":"NON_CSV_MEMBER_NOT_EXTRACTED",
                                 "uncompressed_bytes":inf.file_size})
                continue
            with z.open(inf) as fh:
                content=fh.read(1_000_001)
            if len(content)>1_000_000:raise ValueError("CDS member exceeded CSV cap")
            info,parsed=one_csv(name,content.decode("utf-8-sig",errors="replace"))
            info["uncompressed_bytes"]=inf.file_size
            info["raw_csv_sha256"]=hashlib.sha256(content).hexdigest()
            metadata.append(info);rows.extend(parsed)
    return metadata,rows,{"pilot_zip_sha256":source_sha,
                          "pilot_zip_bytes":path.stat().st_size,
                          "zip_member_count":len(metadata),
                          "raw_csv_member_count":sum(m["member"].lower().endswith(".csv") for m in metadata),
                          "total_decoded_variable_hour_records":len(rows)}

def self_test():
    csvbody="time,latitude,longitude,t2m,sp,strd\n2005-08-11T18:00:00,33.1,130.7,299.15,100000,1350000\n"
    md,records=one_csv("sample.csv",csvbody)
    assert md["time_parse_success"]==1 and len(records)==3
    assert next(x for x in records if x["variable"]=="2m_temperature")["converted_value"]==26.0
    assert next(x for x in records if x["variable"]=="surface_pressure")["converted_value"]==100.0
    assert next(x for x in records if x["variable"]=="surface_thermal_radiation_downwards")["converted_value"]==375.0
    assert parse_time("2005-08-11T18:00:00Z")=="2005-08-11T18:00Z"
    print("STAGE05T SELF-TEST PASS | ZIP/CSV sample, source UTC, PA/TA/LW conversions; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--pilot-zip",type=Path)
    p.add_argument("--stage05r-hours",type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.pilot_zip,a.stage05r_hours,a.out_dir)):
        p.error("--pilot-zip --stage05r-hours --out-dir required")
    if not a.pilot_zip.is_file() or a.pilot_zip.is_symlink():
        p.error("Missing or symlinked original CDS response")
    source_plan=read_stage05r(a.stage05r_hours)
    members,parsed,zip_meta=inspect_zip(a.pilot_zip)
    keys={("JP-Khw",x["UTC_hour"],x["variable"]) for x in parsed}
    decoded_vars=Counter(x["variable"] for x in parsed)
    unique_times=sorted({x["UTC_hour"] for x in parsed})
    grid_cells=sorted({(x["ERA5L_grid_latitude"],x["ERA5L_grid_longitude"]) for x in parsed})
    audit={
      "stage":"JapanFlux Stage05T",
      "status":"CDS_ZIP_SOURCE_READONLY_STRUCTURE_INSPECTED",
      "CDS_dataset":"reanalysis-era5-land-timeseries",
      "CDS_original_member_sha256":EXPECTED_SHA,
      "source_site":"JP-Khw","source_UTC_date":"2005-08-11",
      "tower_latitude":33.13658,"tower_longitude":130.70834,"tower_elevation_m":196.0,
      "original_BIF_SHA256":TARGET_BIF_SHA,
      "source_plan_expected_UTC_hours":source_plan["requested_UTC_hours"],
      "CSV_members":members,
      "file_info":zip_meta,
      "decoded_variable_counts":dict(decoded_vars),
      "decoded_unique_UTC_hours":unique_times,
      "reported_grid_lat_lon_pairs":grid_cells,
      "DATASET_GRID_CELL_ELEVATION":"NOT_ASSESSED",
      "longitude_latitude_from_file":"UNKNOWN_IF_BLANK_OR_UNPARSEABLE",
      "hourly_interval_alignment":"NOT_FINALIZED",
      "CDS_downloads_performed":0,"source_or_forcing_modified":False,
      "physical_repair_approved":False,
      "notes":[
       "Raw CDS ZIP SHA verified before opening.",
       "CSV column names/time/coordinates are preserved as-is and reported.",
       "Parsed numeric conversions assume ERA5-Land published source units; need inspect official file metadata.",
       "Hourly radiation energy conversion to W/m² is a prior-hour interval mean, NOT instantaneous half-hour flux.",
       "Do not fabricate or interpolate missing raw data. Site/time reference is not a repair.",
       "Do not use this output to authorize FATES AD400 or Normal400."
      ]
    }
    out=a.out_dir
    if out.exists():p.error("Choose a fresh output dir; do not overwrite")
    out.mkdir(parents=True)
    j=out/"stage05t_CDS_zip_and_CSV_structure_audit.json"
    t=out/"stage05t_20050811_JP_Khw_independent_hourly_values_PROVISIONAL.tsv"
    with j.open("x",encoding="utf-8") as f:
        json.dump(audit,f,indent=2,ensure_ascii=False);f.write("\n")
    with t.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=CONTEXT_FIELDS,delimiter="\t")
        w.writeheader()
        w.writerows(sorted(parsed,key=lambda x:(x["UTC_hour"],x["variable"],x["CDS_member"])))
    print("STAGE05T CDS PILOT READ-ONLY INSPECTION COMPLETE")
    print("CDS_RAW_ZIP_SHA_VERIFIED",zip_meta["pilot_zip_sha256"],
          "BYTES",zip_meta["pilot_zip_bytes"])
    print("ZIP_MEMBERS",zip_meta["zip_member_count"],"CSV_MEMBERS",zip_meta["raw_csv_member_count"])
    for m in members:
        print("MEMBER",m["member"],"STATUS",m["status"],"ROWS",m.get("rows","NA"))
        print("HEADERS",m.get("headers",[]))
        print("RECOGNIZED_VARIABLES",m.get("variables_recognized",{}))
        print("FIRST_RAW_ROWS",m.get("first_two_raw_rows",[]))
    print("DECODED_VAR_COUNTS",dict(decoded_vars))
    print("OBSERVED_GRID_COORDS",grid_cells)
    print("TARGET_SOURCE_HOURS",source_plan["requested_UTC_hours"])
    sample=[r for r in parsed if r["in_Stage05R_requested_hours"]==1
            and r["UTC_hour"].endswith(("17:00Z","18:00Z","19:00Z"))]
    print("=== SOURCE-GATED UTC 17-19 HOUR PHYSICAL CONTEXT (PROVISIONAL) ===")
    for r in sorted(sample,key=lambda x:(x["UTC_hour"],x["variable"])):
        print("ERA5L",r["UTC_hour"],r["variable"],
              "RAW",r["raw_value"],r["assumed_raw_units"],
              "CONVERTED",r["converted_value"],r["converted_units"],
              "GRID",r["ERA5L_grid_latitude"],r["ERA5L_grid_longitude"],
              "QC",r["comparison_status"])
    print("AUDIT",j)
    print("INDEPENDENT_NUMERIC_PREVIEW",t)
    print("NO AUTOMATIC JPF REPAIR; ALL 45 ORIGINAL SOURCE FIELD CANDIDATES HOLD")

if __name__=="__main__":
    main()

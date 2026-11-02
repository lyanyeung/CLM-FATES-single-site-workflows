#!/usr/bin/env python3
"""JapanFlux Stage05W: inspect second actual independent CDS ERA5-Land ZIP (JP-Yms 2005-08-11 UTC).

Checks Stage05V pending original site/date, Stage05R original-BIF geolocated
87-hour-variable plan, and user-pinned SHA256 of the actual newly downloaded
CDS raw ZIP. Reads 2 CSVs × 24 hours (sp and strd); no ZIP extraction,
new CDS requests, Slurm, model forcing changes, interpolation or repair.
Not executable on real original until user submits & pins a real ZIP hash.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import zipfile

SITE="JP-Yms"
DAY="2005-08-11"
BIF_SHA="7c0a5ba5f137e28518f69ed14b255834fb5b223ac325556719abe5a55e8b0f56"
LAT=34.790278
LON=135.840939
ELEV=220.0
VARIABLES={"sp":("surface_pressure","Pa","kPa"),
           "strd":("surface_thermal_radiation_downwards","J m-2/hour","W m-2 hourly mean")}
SOURCE_REQUIRED_HOURS={f"{h:02d}:00" for h in range(14,23)}
OUT_FIELDS=("UTC_valid_time","variable","independent_raw_value","independent_raw_units",
            "independent_converted_hourly_value","converted_units","CDS_grid_lat",
            "CDS_grid_lon","source_required_hour","science_status")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b=f.read(2*1024*1024)
            if not b:break
            h.update(b)
    return h.hexdigest()

def read_rows(path:Path)->list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if not rows:raise ValueError("Empty original Stage05R source plan")
    return rows

def validate_origin(rem:dict,rows:list[dict])->dict:
    if (rem.get("stage")!="JapanFlux Stage05V"
        or rem.get("status")!="NO_SUBMISSIONS_EIGHT_DAYS_PREVIEW_ONLY"
        or rem.get("remaining_count")!=8
        or rem.get("independent_CDS_requests_this_stage")!=0):
        raise ValueError("Expected exact eight-pending-days Stage05V provenance")
    windows=rem.get("remaining_site_day_requests",[])
    if len(windows)!=8 or len({(x["site"],x["utc_day"]) for x in windows})!=8:
        raise ValueError("Stage05V pending day entries changed")
    match=[x for x in windows if (x["site"],x["utc_day"])==(SITE,DAY)]
    if len(match)!=1:
        raise ValueError("JP-Yms 2005-08-11 not uniquely pending in Stage05V")
    item=match[0]
    if (set(item["variable_scope"])!=set(v[0] for v in VARIABLES.values())
        or set(item["requested_source_UTC_hours"])!=SOURCE_REQUIRED_HOURS
        or item["source_bif_sha256"]!=BIF_SHA):
        raise ValueError("Unexpected Stage05V Yms original variable/hour/BIF scope")
    if (abs(float(item["original_tower_coordinates"]["latitude"])-LAT)>1e-8
        or abs(float(item["original_tower_coordinates"]["longitude"])-LON)>1e-8):
        raise ValueError("Stage05V original tower coordinates unexpectedly changed")
    if len(rows)!=87:
        raise ValueError("Expected original 87 row Stage05R external reference plan")
    subset=[r for r in rows if r["site"]==SITE and r["UTC_day"]==DAY]
    expected={(f"{DAY.replace('-','')}{hour.replace(':','')}",v[0])
              for hour in SOURCE_REQUIRED_HOURS for v in VARIABLES.values()}
    keys={(r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"]) for r in subset}
    if len(subset)!=18 or len(keys)!=18 or keys!=expected:
        raise ValueError("Exact JP-Yms UTC 9-hour × 2-variable source scope not matched")
    for r in subset:
        if (r["original_BIF_SHA256"]!=BIF_SHA
            or abs(float(r["tower_latitude"])-LAT)>1e-8
            or abs(float(r["tower_longitude"])-LON)>1e-8
            or abs(float(r["tower_elevation_m"])-ELEV)>1e-8
            or r["coordinate_source_status"]!="ORIGINAL_BIF_VERIFIED"
            or r["independent_ERA5L_values_status"]!="NOT_DOWNLOADED"):
            raise ValueError("Stage05R source coordinates/provenance wrong")
    return item

def parse_csv(name:str,body:bytes)->tuple[dict,list[dict]]:
    decoded=body.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(decoded))
    fields=reader.fieldnames or []
    if len(fields)!=4 or len(set(fields))!=4 or set(fields)-{"valid_time","latitude","longitude"} not in ({"sp"},{"strd"}):
        raise ValueError("Unexpected single-variable CDS CSV headers "+repr(fields))
    variable=(set(fields)-{"valid_time","latitude","longitude"}).pop()
    vname,rawunit,unit=VARIABLES[variable]
    records=list(reader)
    if len(records)!=24:
        raise ValueError("Expected 24 hourly source rows in "+name)
    output=[]
    seen=set()
    coords=set()
    for row in records:
        dt=datetime.strptime(row["valid_time"],"%Y-%m-%d %H:%M:%S")
        if dt.date().isoformat()!=DAY or dt.minute!=0 or dt.second!=0 or dt.hour in seen:
            raise ValueError("Unexpected CDS original UTC valid_time sequence in "+name)
        seen.add(dt.hour)
        lat=float(row["latitude"]);lon=float(row["longitude"]);n=float(row[variable])
        if not all(math.isfinite(x) for x in (lat,lon,n)):
            raise ValueError("Nonfinite CDS numeric field")
        if abs(lat-LAT)>0.11 or abs(lon-LON)>0.11:
            raise ValueError("ERA5-Land grid too far from original BIF tower coords")
        coords.add((lat,lon))
        conv=n/1000 if variable=="sp" else n/3600
        if not (0<conv<120 if variable=="sp" else 0<=conv<1500):
            raise ValueError("Independent reference gross physical screen failed: "+repr(n))
        output.append({
            "UTC_valid_time":dt.strftime("%Y-%m-%dT%H:%MZ"),
            "variable":vname,"independent_raw_value":n,
            "independent_raw_units":rawunit,
            "independent_converted_hourly_value":round(conv,6),
            "converted_units":unit,
            "CDS_grid_lat":lat,"CDS_grid_lon":lon,
            "source_required_hour":int(dt.strftime("%H:%M") in SOURCE_REQUIRED_HOURS),
            "science_status":"INDEPENDENT_ERA5L_HOURLY_REFERENCE_ONLY_NOT_APPROVED_FOR_REPLACEMENT"
        })
    if seen!=set(range(24)) or len(coords)!=1:
        raise ValueError("CDS CSV missing hours or has multiple grids")
    return {
        "member":name,"raw_CSV_sha256":hashlib.sha256(body).hexdigest(),
        "original_headers":fields,"variable_name":vname,
        "source_rows":24,"CDS_valid_time_UTC_min":min(x["UTC_valid_time"] for x in output),
        "CDS_valid_time_UTC_max":max(x["UTC_valid_time"] for x in output),
        "grid_lat_lon":[list(c) for c in coords]
    },output

def inspect_zip(path:Path,expected_sha:str)->tuple[list[dict],list[dict]]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected original downloaded real-file ZIP")
    if sha256(path)!=expected_sha:
        raise ValueError("Actual downloaded CDS ZIP SHA does not match user-pinned original")
    if not zipfile.is_zipfile(path):
        raise ValueError("CDS original response not a ZIP file")
    meta=[];values=[]; size=0
    with zipfile.ZipFile(path) as z:
        members=[i for i in z.infolist() if not i.is_dir()]
        if len(members)!=2:
            raise ValueError("Expect two CDS source CSV members, PA and LW only")
        for info in members:
            pure=PurePosixPath(info.filename)
            if (pure.is_absolute() or ".." in pure.parts or "\\" in info.filename
                or not info.filename.endswith(".csv") or info.file_size>200_000):
                raise ValueError("Unexpected CDS source member/size/path")
            size+=info.file_size
            if size>400_000:raise ValueError("Unexpected total original CSV size")
            with z.open(info) as f:
                raw=f.read(200_001)
            if len(raw)>200_000:
                raise ValueError("Unexpected original CDS CSV member length")
            m,v=parse_csv(info.filename,raw)
            meta.append(m);values.extend(v)
    if set(m["variable_name"] for m in meta)!=set(v[0] for v in VARIABLES.values()):
        raise ValueError("Expected independent surface pressure + downward thermal radiation")
    if len(values)!=48:
        raise ValueError("Expected 2 × 24 independent CDS values")
    unique_coords={(r["CDS_grid_lat"],r["CDS_grid_lon"]) for r in values}
    if len(unique_coords)!=1:
        raise ValueError("Multiple locations across variable files")
    return meta,values

def self_test():
    for v in VARIABLES:
        text=("valid_time,"+v+",latitude,longitude\n"+
              "\n".join(f"{DAY} {h:02d}:00:00,{97000 if v=='sp' else 1400000},34.8,135.8" for h in range(24))+"\n")
        m,rows=parse_csv("synthetic.csv",text.encode())
        assert len(rows)==24 and m["source_rows"]==24
        assert rows[17]["source_required_hour"]==1
    assert len(SOURCE_REQUIRED_HOURS)==9
    print("STAGE05W SELF-TEST PASS | original Yms BIF, 2×24 CDS hours, ZIP SHA pin; NO WRITES")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--stage05v-remaining",type=Path)
    ap.add_argument("--stage05r-hours",type=Path)
    ap.add_argument("--cds-zip",type=Path)
    ap.add_argument("--expected-sha256")
    ap.add_argument("--out-dir",type=Path)
    a=ap.parse_args()
    if a.self_test:
        self_test();return
    if any(x is None for x in (a.stage05v_remaining,a.stage05r_hours,a.cds_zip,a.expected_sha256,a.out_dir)):
        ap.error("Require Stage05V pending plan, Stage05R hours, original CDS ZIP, user-pinned ZIP SHA and new out dir")
    if len(a.expected_sha256)!=64 or any(c not in "0123456789abcdef" for c in a.expected_sha256):
        ap.error("Expected exact lowercase 64-char original CDS SHA256")
    item=validate_origin(json.loads(a.stage05v_remaining.read_text(encoding="utf-8")),read_rows(a.stage05r_hours))
    meta,values=inspect_zip(a.cds_zip,a.expected_sha256)
    if a.out_dir.exists():
        ap.error("Choose fresh out dir (no overwrites)")
    a.out_dir.mkdir(parents=True)
    output=a.out_dir/"stage05w_Yms_20050811_independent_ERA5L_2x24_HOURLY_HOLD.tsv"
    audit=a.out_dir/"stage05w_original_CDS_source_zip_and_grid_audit.json"
    with output.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=OUT_FIELDS,delimiter="\t")
        w.writeheader();w.writerows(sorted(values,key=lambda r:(r["UTC_valid_time"],r["variable"])))
    report={
        "stage":"JapanFlux Stage05W",
        "status":"SOURCE_BIF_GATED_SECOND_SITE_CDS_PILOT_PARSED",
        "site":SITE,"UTC_date":DAY,
        "tower_original_BIF_lat_lon":[LAT,LON],
        "tower_original_BIF_elevation_m":ELEV,"original_BIF_SHA256":BIF_SHA,
        "original_CDS_ZIP_SHA256":a.expected_sha256,
        "original_CDS_ZIP_bytes":a.cds_zip.stat().st_size,
        "independent_ERA5L_CSV_members":meta,
        "independent_ERA5L_numeric_hourly_records":len(values),
        "independent_ERA5L_grid_lat_lon":[values[0]["CDS_grid_lat"],values[0]["CDS_grid_lon"]],
        "original_source_UTC_required_hours":sorted(SOURCE_REQUIRED_HOURS),
        "CDS_source_actual_submitted_request_scope":item["variable_scope"],
        "ERA5L_grid_elevation":"NOT_AVAILABLE",
        "source_selected_F_repair_approval":False,
        "hourly_reference_vs_30min_radiation":"NOT_A_HALF_HOUR_REPLACEMENT",
        "source_originals_and_model_forcing_modified":False,
        "CDS_new_requests_this_stage":0,"Slurm_jobs":0,
        "all_45_flagged_JPF_source_fields_remain_HOLD":True
    }
    with audit.open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05W SECOND CDS SITE READONLY SCIENCE INSPECTION PASS | NO CDS / ZIP WRITES / SLURM")
    print("SITE",SITE,"DATE_UTC",DAY,"ZIP_SHA256",a.expected_sha256)
    print("MEMBERS",len(meta),"HOURLY_VARIABLE_RECORDS",len(values),"HOURS_PER_VARIABLE",24)
    print("CDS_GRID",report["independent_ERA5L_grid_lat_lon"],"TOWER",LAT,LON,ELEV)
    for r in values:
        if r["UTC_valid_time"].endswith(("17:00Z","18:00Z","19:00Z")):
            print("ERA5L",r["UTC_valid_time"],r["variable"],
                  "RAW",r["independent_raw_value"],r["independent_raw_units"],
                  "CONVERTED",r["independent_converted_hourly_value"],r["converted_units"])
    print("INDEPENDENT_CDS_TABLE",output)
    print("ORIGINAL_CDS_AUDIT",audit)
    print("NO SOURCE/ERA5L HALF-HOUR REPLACEMENT; ALL 45 ORIGINAL FIELDS HOLD")

if __name__=="__main__":
    main()

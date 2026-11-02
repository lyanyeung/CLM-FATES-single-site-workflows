#!/usr/bin/env python3
"""JapanFlux Stage05AB: read-only six-day CDS archive discovery and science gate.

Sources: actual Stage05AA 16-field science-HOLD/6-day manifest, and the
original Stage05R 87 source-BIF-verified hourly-variable provenance table.
Survey only the ORIGINAL Stage05S downloads directory for each of the six
remaining JP-Fjy/Khw/Yms Dec-2011 site×UTC-day requests. Stage05S may leave
.zip, .zip.partial, .csv, or .nc/.partial. Do not erase/re-download files.

Existing ZIP content is strictly checked for CRC, complete UTC 00:00–23:00
valid_time, requested variable columns, unchanged grid across variables,
geographic proximity, physically broad hourly unit limits, and original
site/date/source requested scope. This verifies a compatible SOURCE PAYLOAD,
NOT the original CDS request transaction or approval for 30min repair.

No CDS/network, Slurm, original ZIP extraction, any changes to original
source/forcing/model cases, automatic physical correction, or approvals.
The only writes are new derived TSV/JSON under --out-dir.
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
import stat
import zipfile

DAYS={"2011-12-16","2011-12-17"}
SITES={"JP-Fjy","JP-Khw","JP-Yms"}
SIX={(s,d) for s in SITES for d in DAYS}
VARS={"surface_pressure":("sp","Pa","kPa",1000.0),
      "surface_thermal_radiation_downwards":("strd","J m-2 hourly","W m-2 hourly mean",3600.0)}
EXPECTED_BY_SITE={"JP-Fjy":{"surface_pressure"},
                  "JP-Khw":{"surface_pressure"},
                  "JP-Yms":{"surface_pressure","surface_thermal_radiation_downwards"}}
EXPECTED_BIF={
    "JP-Fjy":"b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62",
    "JP-Khw":"eef29bcb9bd97874dad32469b1821b61760f3111cbc3836ad6300350b18217b4",
    "JP-Yms":"7c0a5ba5f137e28518f69ed14b255834fb5b223ac325556719abe5a55e8b0f56",
}
TOWERS={"JP-Fjy":(35.45454,138.76225,1043.0),
        "JP-Khw":(33.13658,130.70834,196.0),
        "JP-Yms":(34.790278,135.840939,220.0)}
TABLE_FIELDS=("site","UTC_date","requested_variables","original_source_UTC_hours",
              "ZIP_state","partial_state","other_payload_state","ZIP_bytes",
              "ZIP_SHA256","CRC_and_csv_status","source_csv_members",
              "independent_hourly_values_count","ERA5L_grid_lat",
              "ERA5L_grid_lon","source_representativeness","recommendation",
              "archive_path")
MAX_ZIP_SIZE=25*1024*1024
MAX_CSV_MEMBER_SIZE=1000000

def read_tsv(path:Path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):
            raise ValueError("Stage05R TSV column names missing or duplicate")
        records=list(reader)
    if not records:raise ValueError("Empty original Stage05R 87-row source table")
    return records

def sha256(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def verify_sources(six:dict,science:dict,rows:list[dict]):
    if (six.get("stage")!="JapanFlux Stage05AA"
        or six.get("status")!="SIX_FUTURE_SITE_DAYS_PREVIEW_ONLY"
        or six.get("remaining_site_day_count")!=6
        or six.get("source_days_with_validated_CDS_style_hourly_contents")!=3
        or six.get("observed_CDS_successful_request_logs")!=2
        or six.get("third_day_original_request_id")!="NOT_AVAILABLE"
        or six.get("CDS_requests_by_this_stage")!=0
        or six.get("model_forcing_modified") is not False):
        raise ValueError("Actual Stage05AA six-day provenance not approved for inventory")
    if (science.get("stage")!="JapanFlux Stage05AA"
        or science.get("status")!="SIXTEEN_SOURCE_QC2_CONTEXT_ERRORS_EVIDENCED_NOT_APPROVED_FOR_REPAIR"
        or science.get("original_source_HOLD_fields")!=45
        or science.get("independent_hourly_context_supported_fields")!=16
        or science.get("UTC_verified_source_fields_pending_independent_reference")!=11
        or science.get("original_solar_time_clock_HOLD_fields")!=18
        or science.get("remaining_CDS_site_days_not_yet_verified")!=6
        or science.get("half_hour_replacement_values_approved") is not False
        or science.get("all_45_original_source_fields_HOLD") is not True):
        raise ValueError("Actual Stage05AA total scientific HOLD/coverage gate changed")
    pending=six.get("remaining",[])
    if len(pending)!=6 or {(r["site"],r["UTC_day"]) for r in pending}!=SIX:
        raise ValueError("Unexpected six site/date scope or duplicate")
    if len(rows)!=87:
        raise ValueError("Stage05R original global 87 variable-hour source plan changed")
    allkeys=set(); by_day={}
    for r in rows:
        k=r["site"],r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"]
        if k in allkeys:raise ValueError("Original Stage05R duplicate variable/hour")
        allkeys.add(k)
        dt=datetime.strptime(r["UTC_hour"],"%Y%m%d%H%M")
        if (dt.minute!=0 or dt.strftime("%Y-%m-%d")!=r["UTC_day"]
            or dt.strftime("%H:%M")!=r["UTC_clock"]):
            raise ValueError("Stage05R original UTC timestamp invalid")
        if r["site"] not in SITES or r["CDS_ERA5_Land_timeseries_variable"] not in VARS and r["CDS_ERA5_Land_timeseries_variable"]!="2m_temperature":
            raise ValueError("Unexpected original Stage05R site/variable")
    for r in pending:
        site=r["site"];day=r["UTC_day"]
        if (r["source_BIF_SHA256"]!=EXPECTED_BIF[site]
            or r["CDS_dataset"]!="reanalysis-era5-land-timeseries"
            or set(r["variable_scope"])!=EXPECTED_BY_SITE[site]):
            raise ValueError("Stage05AA date/variable/source SHA scope changed")
        coords=r["original_tower_coordinates"]
        if (abs(float(coords["latitude"])-TOWERS[site][0])>1e-7
            or abs(float(coords["longitude"])-TOWERS[site][1])>1e-7):
            raise ValueError("Original source BIF tower coordinates changed")
        scoped=[x for x in rows if x["site"]==site and x["UTC_day"]==day]
        actual={(x["UTC_hour"],x["CDS_ERA5_Land_timeseries_variable"]) for x in scoped}
        for x in scoped:
            if (x["original_BIF_SHA256"]!=EXPECTED_BIF[site]
                or abs(float(x["tower_latitude"])-TOWERS[site][0])>1e-7
                or abs(float(x["tower_longitude"])-TOWERS[site][1])>1e-7
                or abs(float(x["tower_elevation_m"])-TOWERS[site][2])>1e-7
                or x["coordinate_source_status"]!="ORIGINAL_BIF_VERIFIED"
                or x["independent_ERA5L_values_status"]!="NOT_DOWNLOADED"
                or not x["source_UTC_halfhour_event_starts"]):
                raise ValueError("Stage05R BIF or original source time association changed")
        clocks={datetime.strptime(a,"%Y%m%d%H%M").strftime("%H:%M") for a,b in actual}
        names={v for a,v in actual}
        if (not scoped or len(scoped)!=len(actual)
            or clocks!=set(r["source_UTC_hours"])
            or names!=set(r["variable_scope"])):
            raise ValueError("Stage05AA/Stage05R exact day-specific source hour/variable scope conflict")
        by_day[site,day]=r
    return by_day

def describe_file(path:Path):
    # lstat avoids following a symlink or accepting a directory as a CDS payload
    try:
        mode=path.lstat().st_mode
    except FileNotFoundError:
        return "ABSENT"
    if stat.S_ISLNK(mode):return "SYMLINK_HOLD"
    if stat.S_ISREG(mode):return "REGULAR"
    return "NONREGULAR_HOLD"

def inspect_existing_zip(path:Path,site:str,day:str,expected_vars:set[str]):
    """Return content status + audit metadata, never alter raw data."""
    if describe_file(path)!="REGULAR":
        return "NOT_REGULAR",{}
    length=path.stat().st_size
    digest=sha256(path)
    result={"ZIP_bytes":length,"ZIP_SHA256":digest,"source_csv_members":0,
            "independent_hourly_values_count":0,
            "ERA5L_grid_lat":"","ERA5L_grid_lon":""}
    if not 0<length<=MAX_ZIP_SIZE:
        return "BAD_OR_OVERSIZE_ARCHIVE",result
    if not zipfile.is_zipfile(path):
        return "NOT_ZIP_FILE",result
    try:
        observations=[]; grids=set(); foundvars=set(); names=[]
        with zipfile.ZipFile(path) as z:
            files=[v for v in z.infolist() if not v.is_dir()]
            if len(files)!=len(expected_vars):
                return "UNEXPECTED_CSV_MEMBER_COUNT",result
            for info in files:
                pure=PurePosixPath(info.filename)
                if (pure.is_absolute() or ".." in pure.parts or "\\" in info.filename
                    or not info.filename.lower().endswith(".csv")
                    or info.file_size>MAX_CSV_MEMBER_SIZE):
                    return "SUSPICIOUS_OR_OVERSIZE_CSV_MEMBER",result
            crc_bad=z.testzip()
            if crc_bad is not None:
                return "ZIP_CRC_FAIL",result
            for info in files:
                data=z.read(info)
                rd=csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
                if (not rd.fieldnames or len(rd.fieldnames)!=4
                    or len(set(rd.fieldnames))!=4
                    or set(rd.fieldnames)-{"valid_time","latitude","longitude"} not in ({"sp"},{"strd"})):
                    return "UNEXPECTED_ORIGINAL_CDS_CSV_SCHEMA",result
                var=(set(rd.fieldnames)-{"valid_time","latitude","longitude"}).pop()
                matching=[v for v in expected_vars if VARS[v][0]==var]
                if len(matching)!=1 or var in foundvars:
                    return "MISMATCHED_OR_DUPLICATE_CDS_VARIABLE",result
                foundvars.add(var);names.append(info.filename)
                readings=list(rd)
                if len(readings)!=24:return "CSV_NOT_24_HOURLY_ROWS",result
                seen=set(); memberset=set()
                for rec in readings:
                    dt=datetime.strptime(rec["valid_time"],"%Y-%m-%d %H:%M:%S")
                    if (dt.date().isoformat()!=day or dt.minute or dt.second
                        or dt.hour in seen):
                        return "CSV_UTC_DAY_OR_HOUR_INVALID",result
                    seen.add(dt.hour)
                    lat=float(rec["latitude"]);lon=float(rec["longitude"])
                    val=float(rec[var])
                    if any(not math.isfinite(x) for x in (lat,lon,val)):
                        return "NONFINITE_CDS_DATA",result
                    if (abs(lat-TOWERS[site][0])>0.11 or abs(lon-TOWERS[site][1])>0.11):
                        return "RETURNED_GRID_NOT_NEAR_ORIGINAL_TOWER",result
                    converted=val/(1000 if var=="sp" else 3600)
                    if not (0<converted<120 if var=="sp" else 0<=converted<1500):
                        return "GROSS_INDEPENDENT_NUMERIC_SCREEN_FAIL",result
                    memberset.add((lat,lon));grids.add((lat,lon))
                    observations.append((var,dt.hour,converted))
                if seen!=set(range(24)) or len(memberset)!=1:
                    return "CSV_MISSING_HOURS_OR_MULTIPLE_GRIDS",result
        if len(grids)!=1 or len(foundvars)!=len(expected_vars):
            return "MULTIPLE_RETURNED_GRIDS_OR_VARIABLE_MISMATCH",result
        (lat,lon),=grids
        result.update({"source_csv_members":len(names),
                       "member_names":names,
                       "independent_hourly_values_count":len(observations),
                       "ERA5L_grid_lat":lat,"ERA5L_grid_lon":lon})
        return "COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR",result
    except (OSError,ValueError,UnicodeError,RuntimeError,zipfile.BadZipFile,KeyError,OverflowError) as e:
        result["error_type"]=type(e).__name__
        return "CDS_ZIP_OR_CSV_PARSE_ERROR_HOLD",result

def self_test():
    assert len(SIX)==6
    assert set(EXPECTED_BY_SITE)==SITES
    assert len(VARS)==2
    assert (datetime.strptime("201112170000","%Y%m%d%H%M").strftime("%Y-%m-%d") in DAYS)
    assert sum(len(EXPECTED_BY_SITE[s]) for s,d in SIX)==8
    print("STAGE05AB SELF-TEST PASS | 6 exact site-days, 8 expected CSV members, hold existing .zip/.partial/.csv; NO NETWORK/WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage05aa-remaining",type=Path)
    p.add_argument("--stage05aa-summary",type=Path)
    p.add_argument("--stage05r-hours",type=Path)
    p.add_argument("--download-dir",type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if any(x is None for x in (a.stage05aa_remaining,a.stage05aa_summary,
                               a.stage05r_hours,a.download_dir,a.out_dir)):
        p.error("Require source Stage05AA 6-day JSON/summary, Stage05R TSV, original downloads directory and new output directory")
    provenance=verify_sources(
        json.loads(a.stage05aa_remaining.read_text(encoding="utf-8")),
        json.loads(a.stage05aa_summary.read_text(encoding="utf-8")),
        read_tsv(a.stage05r_hours))
    if a.download_dir.is_symlink() or not a.download_dir.is_dir():
        p.error("Original CDS downloads directory must exist and must not be a symlink")
    status=[];detail=[]
    for site,day in sorted(SIX):
        target=a.download_dir/(f"{site}_ERA5Land_timeseries_{day.replace('-','')}_CSV_response.zip")
        paths={"ZIP":target,"PARTIAL":Path(str(target)+".partial"),
               "CSV":target.with_suffix(".csv"),
               "NC":target.with_suffix(".nc")}
        states={label:describe_file(path) for label,path in paths.items()}
        inspected={}
        zipped="ABSENT"
        if states["ZIP"]=="REGULAR":
            zipped,inspected=inspect_existing_zip(target,site,day,EXPECTED_BY_SITE[site])
        others={k:v for k,v in states.items() if k!="ZIP" and v!="ABSENT"}
        present={k:v for k,v in states.items() if v!="ABSENT"}
        if not present:
            recommendation="NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT"
        elif (zipped=="COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR"
              and len(present)==1):
            recommendation="REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD"
        else:
            recommendation="SCIENCE_HOLD_COLLISION_OR_INVALID_PAYLOAD_NO_DELETE_NO_OVERWRITE"
        row={
            "site":site,"UTC_date":day,
            "requested_variables":",".join(provenance[site,day]["variable_scope"]),
            "original_source_UTC_hours":",".join(provenance[site,day]["source_UTC_hours"]),
            "ZIP_state":states["ZIP"],"partial_state":states["PARTIAL"],
            "other_payload_state":json.dumps(others,sort_keys=True),
            "ZIP_bytes":inspected.get("ZIP_bytes",""),
            "ZIP_SHA256":inspected.get("ZIP_SHA256",""),
            "CRC_and_csv_status":zipped,
            "source_csv_members":inspected.get("source_csv_members",""),
            "independent_hourly_values_count":inspected.get("independent_hourly_values_count",""),
            "ERA5L_grid_lat":inspected.get("ERA5L_grid_lat",""),
            "ERA5L_grid_lon":inspected.get("ERA5L_grid_lon",""),
            "source_representativeness":"GRID_ELEVATION_UNVERIFIED_HOURLY_NOT_30MIN",
            "recommendation":recommendation,
            "archive_path":str(target),
        }
        status.append(row)
        detail.append({"site":site,"UTC_day":day,
                       "original_BIF_SHA256":EXPECTED_BIF[site],
                       "original_tower_coords":TOWERS[site],
                       "original_request_variables":provenance[site,day]["variable_scope"],
                       "source_UTC_hours":provenance[site,day]["source_UTC_hours"],
                       "files":{k:{"path":str(paths[k]),"status":states[k]}
                                for k in paths},
                       "zip_inspection":inspected,"content_status":zipped,
                       "recommendation":recommendation})
    if a.out_dir.exists():
        p.error("Fresh output dir required; no report overwrite")
    a.out_dir.mkdir(parents=True)
    table=a.out_dir/"stage05ab_six_2011_CDS_archive_existing_payload_inventory_HOLD.tsv"
    audit=a.out_dir/"stage05ab_six_2011_CDS_original_archive_science_audit.json"
    with table.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,delimiter="\t",fieldnames=TABLE_FIELDS)
        writer.writeheader();writer.writerows(status)
    counts=Counter(row["recommendation"] for row in status)
    with audit.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05AB",
                   "status":"SIX_ORIGINAL_2011_DAY_PAYLOADS_READONLY_INVENTORIED",
                   "original_45_source_fields_HOLD":True,
                   "previous_16_strong_context_source_fields_verified":True,
                   "unreviewed_UTC_verified_source_fields":11,
                   "timebase_conflict_source_fields":18,
                   "original_downloads_directory":str(a.download_dir),
                   "six_site_day_inventory":detail,
                   "result_counts":dict(counts),
                   "new_CDS_requests":0,"ZIP_extractions":0,
                   "original_source_or_forcing_modified":False,
                   "science_repair_approved":False,
                   "Slurm_jobs":0},f,indent=2,ensure_ascii=False)
        f.write("\n")
    print("STAGE05AB SIX 2011-CDS DAY EXISTING FILES/CRC/TIME/GRID SOURCE INVENTORY PASS | NO CDS / SLURM / REPAIR")
    for row in status:
        print("DAY",row["site"],row["UTC_date"],
              "ZIP",row["ZIP_state"],"PARTIAL",row["partial_state"],
              "CSV_ZIP_STATUS",row["CRC_and_csv_status"],
              "SHA256",row["ZIP_SHA256"] or "NONE",
              "GRID",row["ERA5L_grid_lat"] or "NONE",row["ERA5L_grid_lon"] or "NONE",
              "NEXT",row["recommendation"])
    print("COUNTS",dict(counts))
    print("INVENTORY",table)
    print("SOURCE_AUDIT",audit)
    print("NO CDS CALLS, NO ORIGINAL ZIP/SOURCE/FORCING CHANGES; ALL 45 FIELDS HOLD")

if __name__=="__main__":
    main()

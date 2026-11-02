#!/usr/bin/env python3
"""JapanFlux Stage05Z: JP-Fjy 2005-08-11 provenance preflight + independent CDS pressure audit.

Default mode --preflight is PURE READ-ONLY and makes no CDS request.
Optional --inspect-cds-zip requires an actual user-observed SHA256 after the
separate explicit Stage05S JP-Fjy one-day download. Exact original source
Stage05O QC2 timestamps -> Stage05P +/-3h variable-specific windows must
match Stage05R original geolocated 87-row source request plan and Stage05Y's
seven not-yet-downloaded site-days.

Never writes original JPF sources, zip, forcing, model cases or Slurm jobs.
The independent ERA5-Land gridded surface pressure is hourly and an input
context reference, NOT a certified half-hour tower correction. JP-Fjy original
tower elevation is 1043m and CDS grid elevation has NOT been validated.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime,timedelta
import hashlib
import io
import json
import math
from pathlib import Path,PurePosixPath
import zipfile

SITE="JP-Fjy"
UTC_DATE="2005-08-11"
BIF_SHA="b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62"
TOWER=(35.45454,138.76225,1043.0)
ORIG_COUNTS=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
CDS_PRODUCT="reanalysis-era5-land-timeseries"
CDS_VARIABLE="surface_pressure"
SOURCE_HOURS={f"{h:02d}:00" for h in range(14,23)}
CSV_FIELDS=("UTC_valid_time","surface_pressure_raw_Pa","surface_pressure_kPa",
            "CDS_grid_lat","CDS_grid_lon","hour_in_source_request_window",
            "status")
JOIN_FIELDS=("site","original_JST_halfhour_start","UTC_halfhour_start",
             "source_variable","JPF_F_QC","original_JPF_F_kPa",
             "same_release_JPF_ERA_kPa","CDS_three_hour_valid_times",
             "CDS_three_hour_pressure_kPa","independent_hourly_min_kPa",
             "independent_hourly_max_kPa","outside_hourly_context",
             "source_to_nearest_context_edge_abs_kPa",
             "science_gate")

def tsv(path:Path)->list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or len(rd.fieldnames)!=len(set(rd.fieldnames)):
            raise ValueError("Source TSV must have unique column names")
        rows=list(rd)
    if not rows:raise ValueError("Source TSV empty")
    return rows

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block=f.read(1024*1024)
            if not block:break
            h.update(block)
    return h.hexdigest()

def inspect_sources(source_rows:list[dict],hours_rows:list[dict],seven:dict,yreport:dict):
    if (yreport.get("stage")!="JapanFlux Stage05Y"
        or yreport.get("status")!="THIRTEEN_SOURCE_FIELDS_STRONGLY_CONTRADICTED_BY_SEPARATE_ERA5L_CONTEXT_NOT_REPAIRED"
        or yreport.get("independently_evidenced_source_fields")!=13
        or yreport.get("UTC_verified_fields_not_yet_independently_compared")!=14
        or yreport.get("unresolved_solar_vs_standard_time_source_fields")!=18
        or yreport.get("independent_CDS_site_days_downloaded")!=2
        or yreport.get("independent_CDS_site_days_not_yet_downloaded")!=7
        or yreport.get("no_forcing_or_model_write") is not True):
        raise ValueError("Stage05Y actual science coverage provenance invalid")
    if (seven.get("stage")!="JapanFlux Stage05Y"
        or seven.get("status")!="SEVEN_UNREQUESTED_SITE_DAYS_PREVIEW_ONLY"
        or seven.get("remaining_count")!=7
        or seven.get("CDS_downloads_this_stage")!=0
        or seven.get("source_or_model_changes") is not False):
        raise ValueError("Require original Stage05Y seven-day no-download plan")
    remaining=seven.get("remaining",[])
    if len(remaining)!=7 or len({(r["site"],r["UTC_day"]) for r in remaining})!=7:
        raise ValueError("Original seven site-day list has duplicates")
    selection=[r for r in remaining if r["site"]==SITE and r["UTC_day"]==UTC_DATE]
    if len(selection)!=1:
        raise ValueError("JP-Fjy 2005-08-11 not uniquely in pending seven days")
    req=selection[0]
    if (req["source_BIF_SHA256"]!=BIF_SHA
        or req["CDS_dataset"]!=CDS_PRODUCT
        or set(req["variable_scope"])!={CDS_VARIABLE}
        or set(req["source_UTC_hours"])!=SOURCE_HOURS
        or abs(float(req["original_tower_coordinates"]["latitude"])-TOWER[0])>1e-8
        or abs(float(req["original_tower_coordinates"]["longitude"])-TOWER[1])>1e-8):
        raise ValueError("Stage05Y requested site/day source BIF or variables changed")
    if len(source_rows)!=27 or Counter(r["site"] for r in source_rows)!=ORIG_COUNTS:
        raise ValueError("Stage05O original UTC-verified 27 field count/three-site provenance changed")
    original_bykey=set()
    requested=defaultdict(set)
    sources=[]
    for r in source_rows:
        k=(r["site"],r["native_start"],r["variable"])
        if k in original_bykey:
            raise ValueError("Duplicated Stage05O source QC2 candidate")
        original_bykey.add(k)
        native=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        if native-utc!=timedelta(hours=9):
            raise ValueError("Original JP-Fjy local standard time source UTC offset changed")
        if r["raw_F_QC"]!="2" or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED":
            raise ValueError("Original source science QC2/HOLD guard mismatch")
        if r["site"]!=SITE:continue
        if r["variable"]!="PA" or r["unit"]!="kPa":
            raise ValueError("JP-Fjy original source variable is not pressure in kPa")
        x=float(r["selected_F"])
        y=float(r["ERA_in_same_release"])
        if not (math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,abs_tol=1e-9,rel_tol=1e-12)):
            raise ValueError("JP-Fjy source F value no longer equals same-release ERA")
        if utc.date().isoformat()==UTC_DATE:
            sources.append(r)
        for j in range(-3,5):  # Stage05P context-hours = 3
            stamp=utc.replace(minute=0)+timedelta(hours=j)
            if stamp.date().isoformat()==UTC_DATE:
                requested[(stamp.strftime("%Y%m%d%H%M"),CDS_VARIABLE)].add(r["utc_start"])
    if not sources:
        raise ValueError("No JP-Fjy original source fields on requested UTC date")
    if len(hours_rows)!=87:
        raise ValueError("Stage05R geolocated full original 87 variable-hour rows changed")
    selected_rows=[r for r in hours_rows if r["site"]==SITE and r["UTC_day"]==UTC_DATE]
    observed={}
    for r in selected_rows:
        k=(r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"])
        if k in observed:raise ValueError("Stage05R duplicate hour/variable")
        if (r["original_BIF_SHA256"]!=BIF_SHA
            or abs(float(r["tower_latitude"])-TOWER[0])>1e-8
            or abs(float(r["tower_longitude"])-TOWER[1])>1e-8
            or abs(float(r["tower_elevation_m"])-TOWER[2])>1e-8
            or r["coordinate_source_status"]!="ORIGINAL_BIF_VERIFIED"
            or r["independent_ERA5L_values_status"]!="NOT_DOWNLOADED"):
            raise ValueError("Stage05R original site BIF or historical reference status changed")
        observed[k]=set(r["source_UTC_halfhour_event_starts"].split(","))
    if observed!=dict(requested):
        raise ValueError("Exact per-original-event Stage05P hour+variable mapping mismatch "
                         +repr({"missing_keys":sorted(set(requested)-set(observed)),
                                "extra_keys":sorted(set(observed)-set(requested)),
                                "counts_expected_actual":(len(requested),len(observed))}))
    union={datetime.strptime(t,"%Y%m%d%H%M").strftime("%H:%M") for t,v in observed}
    if union!=SOURCE_HOURS or set(v for t,v in observed)!={CDS_VARIABLE}:
        raise ValueError("Stage05O original source hour union differs from Stage05Y source plan")
    return req,sorted(sources,key=lambda r:r["utc_start"]),len(observed)

def read_cds_zip(path:Path,expected_sha:str):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected real original CDS downloaded ZIP, not symlink")
    if len(expected_sha)!=64 or any(c not in "0123456789abcdef" for c in expected_sha):
        raise ValueError("Supply actual 64-char lowercase SHA256 from CDS download")
    calculated=sha256(path)
    if calculated!=expected_sha:
        raise ValueError("Original CDS raw ZIP SHA256 does not match operator-pinned actual file")
    if not zipfile.is_zipfile(path):
        raise ValueError("Expected ZIP response (do not infer CSV or fabricates)")
    with zipfile.ZipFile(path) as z:
        infos=[i for i in z.infolist() if not i.is_dir()]
        if len(infos)!=1:
            raise ValueError("One-variable CDS request must contain exactly one CSV member")
        info=infos[0]
        pure=PurePosixPath(info.filename)
        if (pure.is_absolute() or ".." in pure.parts or "\\" in info.filename
            or not info.filename.lower().endswith(".csv") or info.file_size>200000):
            raise ValueError("Suspicious CDS raw member name/type/size")
        raw=z.read(info)
    rd=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if set(rd.fieldnames or [])!={"valid_time","sp","latitude","longitude"}:
        raise ValueError("Unknown independent ERA5-Land CSV headers; inspect raw schema first")
    results={};cells=set()
    for row in rd:
        dt=datetime.strptime(row["valid_time"],"%Y-%m-%d %H:%M:%S")
        if dt.date().isoformat()!=UTC_DATE or dt.minute or dt.second or dt.hour in results:
            raise ValueError("Duplicate/missing/invalid CDS original UTC hour")
        lat=float(row["latitude"]);lon=float(row["longitude"]);rawpa=float(row["sp"])
        if any(not math.isfinite(v) for v in (lat,lon,rawpa)):
            raise ValueError("Nonfinite independent original grid/pressure value")
        if abs(lat-TOWER[0])>0.11 or abs(lon-TOWER[1])>0.11:
            raise ValueError("Independent ERA5-Land land grid unexpectedly far from source tower")
        cells.add((lat,lon))
        converted=rawpa/1000
        if not 0<converted<120:
            raise ValueError("Independent ERA5-Land surface pressure broad physical screen failed")
        results[dt.hour]={
            "UTC_valid_time":dt.strftime("%Y-%m-%dT%H:%MZ"),
            "surface_pressure_raw_Pa":rawpa,"surface_pressure_kPa":round(converted,6),
            "CDS_grid_lat":lat,"CDS_grid_lon":lon,
            "hour_in_source_request_window":int(dt.strftime("%H:%M") in SOURCE_HOURS),
            "status":"INDEPENDENT_HOURLY_CONTEXT_NO_APPROVED_HALF_HOUR_REPAIR"}
    if set(results)!=set(range(24)) or len(cells)!=1:
        raise ValueError("Original independent CDS 24 hourly timestamps or grid location incomplete")
    return results, sorted(cells),info.filename,hashlib.sha256(raw).hexdigest()

def compare_source(sources:list[dict],hourly:dict):
    review=[]
    for r in sources:
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        points=[utc.replace(minute=0)+timedelta(hours=j) for j in (0,1,2)]
        if any(p.date().isoformat()!=UTC_DATE for p in points):
            raise ValueError("3-hour original source context crosses CDS day; need exact additional day")
        vals=[hourly[p.hour]["surface_pressure_kPa"] for p in points]
        v=float(r["selected_F"])
        lo=min(vals);hi=max(vals)
        outside=int(not (lo<=v<=hi))
        distance=round(lo-v if v<lo else v-hi if v>hi else 0.0,6)
        review.append({
            "site":SITE,
            "original_JST_halfhour_start":r["native_start"],
            "UTC_halfhour_start":utc.strftime("%Y-%m-%dT%H:%MZ"),
            "source_variable":"PA","JPF_F_QC":"2",
            "original_JPF_F_kPa":r["selected_F"],
            "same_release_JPF_ERA_kPa":r["ERA_in_same_release"],
            "CDS_three_hour_valid_times":";".join(p.strftime("%Y-%m-%dT%H:%MZ") for p in points),
            "CDS_three_hour_pressure_kPa":";".join(str(val) for val in vals),
            "independent_hourly_min_kPa":round(lo,6),
            "independent_hourly_max_kPa":round(hi,6),
            "outside_hourly_context":outside,
            "source_to_nearest_context_edge_abs_kPa":distance,
            "science_gate":"HOLD_GRID_ALTITUDE_UNVERIFIED_NO_POINTWISE_HALF_HOUR_REPLACEMENT"
        })
    return review

def self_test():
    assert (datetime.strptime("200508120230","%Y%m%d%H%M")-timedelta(hours=9)).strftime("%Y%m%d%H%M")=="200508111730"
    start=datetime.strptime("200508111730","%Y%m%d%H%M").replace(minute=0)
    req={start+timedelta(hours=j) for j in range(-3,5)}
    assert len(req)==8 and len(SOURCE_HOURS)==9
    assert len(ORIG_COUNTS)==3 and sum(ORIG_COUNTS.values())==27
    print("STAGE05Z SELF-TEST PASS | source-specific UTC+9 QC2/ERA equality, one-variable 24-hour independent ZIP; NO WRITES")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--stage05y-remaining",type=Path)
    ap.add_argument("--stage05y-summary",type=Path)
    ap.add_argument("--stage05o-source-utc",type=Path)
    ap.add_argument("--stage05r-hours",type=Path)
    ap.add_argument("--preflight",action="store_true")
    ap.add_argument("--inspect-cds-zip",type=Path)
    ap.add_argument("--expected-sha256")
    ap.add_argument("--out-dir",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test();return
    if any(x is None for x in (args.stage05y_remaining,args.stage05y_summary,
                               args.stage05o_source_utc,args.stage05r_hours)):
        ap.error("Need the original Stage05Y remaining/summary and Stage05O/Stage05R source tables")
    req,sources,npairs=inspect_sources(
        tsv(args.stage05o_source_utc),tsv(args.stage05r_hours),
        json.loads(args.stage05y_remaining.read_text(encoding="utf-8")),
        json.loads(args.stage05y_summary.read_text(encoding="utf-8")))
    print("STAGE05Z JP-FJY ORIGINAL SOURCE/PENDING CDS DAY PREFLIGHT PASS")
    print("SITE",SITE,"UTC_DATE",UTC_DATE,"VARIABLE",CDS_VARIABLE)
    print("SOURCE_ORIGINAL_QC2_FIELDS_ON_DAY",len(sources),
          "REQUIRED_SOURCE_VARIABLE_HOUR_PAIRS",npairs)
    print("TOWER_BIF_LAT_LON_ELEV",TOWER,"BIF_SHA",BIF_SHA)
    print("CDS_REQUEST_ELIGIBLE_SOURCE_HOURS",",".join(sorted(SOURCE_HOURS)))
    if args.preflight:
        if args.inspect_cds_zip or args.expected_sha256 or args.out_dir:
            ap.error("--preflight is read-only, may not include CDS-zip/output parameters")
        print("NO CDS, NO ZIP, NO WRITES. One operator-authenticated Stage05S CDS request may be submitted separately.")
        return
    if args.inspect_cds_zip is None or args.expected_sha256 is None or args.out_dir is None:
        ap.error("For raw ZIP inspection provide --inspect-cds-zip --expected-sha256 --out-dir")
    hourly,cells,member,member_sha=read_cds_zip(args.inspect_cds_zip,args.expected_sha256)
    review=compare_source(sources,hourly)
    if args.out_dir.exists():
        ap.error("Choose a new output report directory; do not overwrite")
    args.out_dir.mkdir(parents=True)
    values_path=args.out_dir/"stage05z_Fjy_20050811_CDS_surface_pressure_24h_HOLD.tsv"
    comp_path=args.out_dir/"stage05z_Fjy_20050811_original_JPF_vs_independent_hourly_CONTEXT_HOLD.tsv"
    audit_path=args.out_dir/"stage05z_independent_CDS_original_source_audit.json"
    for path,fields,records in (
        (values_path,CSV_FIELDS,[hourly[i] for i in range(24)]),
        (comp_path,JOIN_FIELDS,review)):
        with path.open("x",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
            w.writeheader();w.writerows(records)
    audit={
        "stage":"JapanFlux Stage05Z",
        "status":"SOURCE_EXACT_FJY_INDEPENDENT_HOURLY_PRESSURE_CONTEXT_AUDITED",
        "site":SITE,"UTC_date":UTC_DATE,
        "source_BIF_SHA256":BIF_SHA,"tower_location_lat_lon_alt":list(TOWER),
        "original_CDS_ZIP_sha256":args.expected_sha256,
        "original_CDS_ZIP_bytes":args.inspect_cds_zip.stat().st_size,
        "original_CDS_member":member,"member_sha256":member_sha,
        "independent_hourly_count":len(hourly),"CDS_grid_coordinates":[list(x) for x in cells],
        "original_site_source_QC2_field_count":len(sources),
        "source_requested_variable_hour_pairs":npairs,
        "source_fields_outside_hourly_context":sum(r["outside_hourly_context"] for r in review),
        "pressure_grid_altitude":"UNKNOWN_NEEDS_INDEPENDENT_GEOPOTENTIAL",
        "source_halfhour_pressure_replacement_approved":False,
        "original_source_or_forcing_changed":False,"CDS_request_this_stage":False,
        "Slurm_jobs":0,"all_45_JPF_source_candidate_fields_still_HOLD":True
    }
    with audit_path.open("x",encoding="utf-8") as f:
        json.dump(audit,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05Z INDEPENDENT JP-FJY CDS ZIP/SOURCE CONTEXT AUDIT PASS | NO CDS / SLURM / REPAIR")
    print("CDS_GRID",cells,"RAW_ZIP_SHA256",args.expected_sha256,"HOURLY_ROWS",len(hourly))
    for hour in (17,18,19):
        print("CDS_UTC_HOUR",hour,"SP_KPA",hourly[hour]["surface_pressure_kPa"])
    for r in review:
        print("ORIGINAL_SOURCE",r["original_JST_halfhour_start"],
              "F_PA_KPA",r["original_JPF_F_kPa"],
              "CDS_CONTEXT_KPA",r["CDS_three_hour_pressure_kPa"],
              "OUTSIDE",r["outside_hourly_context"],"STATUS",r["science_gate"])
    print("INDEPENDENT_PRESSURE_HOURS",values_path)
    print("SOURCE_COMPARISON",comp_path)
    print("AUDIT",audit_path)
    print("ALL_45_SOURCE_FIELDS_REMAIN_HOLD; GRID_HEIGHT_UNKNOWN; NO APPROVED HALF_HOUR_REPAIR")

if __name__=="__main__":
    main()

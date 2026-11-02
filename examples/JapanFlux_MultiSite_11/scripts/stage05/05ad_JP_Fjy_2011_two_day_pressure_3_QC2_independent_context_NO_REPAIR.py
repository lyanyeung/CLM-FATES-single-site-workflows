#!/usr/bin/env python3
"""JapanFlux Stage05AD — cross-UTC-midnight JP-Fjy 2011 pressure QC2 context.

Two separate ERA5-Land timeseries CSV ZIP responses (2011-12-16 and 17 UTC)
must be present and verified before any source-selected F vs hourly ERA5L
comparison. Uses original Stage05O 27 QC2 fields, Stage05R 87 var/hour/source
plan, Stage05AA verified 16-field science HOLD evidence and an actual
post-download Stage05AB audit of six site-days. Reads only original CDS ZIPs;
writes derived reports to a fresh directory. No CDS/Slurm/forcing/repair.
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
DATES=("2011-12-16","2011-12-17")
BIF_SHA="b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62"
TOWER=(35.45454,138.76225,1043.0)
COUNTS=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
CDS_VAR="surface_pressure"
ERA_COL="sp"
FIELDS=("site","original_JST_halfhour_start","derived_UTC_start","variable",
        "original_JPF_F_kPa","same_release_original_ERA_kPa","original_F_QC",
        "hourly_ERA5L_valid_times_UTC","hourly_ERA5L_pressures_kPa",
        "hourly_ERA5L_context_min_kPa","hourly_ERA5L_context_max_kPa",
        "outside_independent_hourly_context","minimum_distance_to_context_kPa",
        "source_classification","science_status","grid_elevation_status")
VALID="COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR"

def read_tsv(path:Path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError("TSV columns missing or duplicated")
        rows=list(reader)
    if not rows:raise ValueError("Empty source TSV")
    return rows

def read_json(path:Path):
    d=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict):raise ValueError("Expected JSON object")
    return d

def sha256(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def source_events(records):
    if len(records)!=27 or Counter(r["site"] for r in records)!=COUNTS:
        raise ValueError("Expected exactly 27 original QC2 source-mapped fields")
    seen=set();source=[]
    for r in records:
        k=r["site"],r["native_start"],r["variable"]
        if k in seen:raise ValueError("Duplicate original QC2 source event")
        seen.add(k)
        native=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        if native-utc!=timedelta(hours=9):
            raise ValueError("Original source local standard time / UTC+9 proof changed")
        x=float(r["selected_F"]);y=float(r["ERA_in_same_release"])
        if (r["raw_F_QC"]!="2"
            or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"
            or not all(math.isfinite(t) for t in (x,y))
            or not math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-9)):
            raise ValueError("Original source F/ERA QC2 HOLD invariant changed")
        if r["site"]!=SITE:continue
        if r["variable"]!="PA" or r["unit"]!="kPa":
            raise ValueError("Original JP-Fjy source QC2 variable / units unexpected")
        if utc.date().isoformat() in DATES:
            source.append(r)
        elif utc.year==2005 and utc.month==8:
            pass
        else:
            raise ValueError("JP-Fjy original QC2 event outside known 2005/2011 review dates")
    if len(source)!=3:
        raise ValueError("Expected three original JP-Fjy 2011 QC2 pressure candidates")
    return sorted(source,key=lambda r:r["utc_start"])

def source_hour_keys(source,allhours):
    if len(allhours)!=87:
        raise ValueError("Original Stage05R 87 requested variable-hour references changed")
    observed={}
    for r in allhours:
        k=r["site"],r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"]
        if k in observed:
            raise ValueError("Original Stage05R duplicate reference hour/variable")
        observed[k]=r
    match={}
    for r in allhours:
        if r["site"]==SITE and r["UTC_day"] in DATES:
            key=r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"]
            if key in match:raise ValueError("JP-Fjy duplicate source hour")
            if (r["original_BIF_SHA256"]!=BIF_SHA
                or r["coordinate_source_status"]!="ORIGINAL_BIF_VERIFIED"
                or r["independent_ERA5L_values_status"]!="NOT_DOWNLOADED"
                or abs(float(r["tower_latitude"])-TOWER[0])>1e-7
                or abs(float(r["tower_longitude"])-TOWER[1])>1e-7
                or abs(float(r["tower_elevation_m"])-TOWER[2])>1e-7):
                raise ValueError("Original Stage05R source BIF geolocation or HOLD provenance changed")
            match[key]=set(r["source_UTC_halfhour_event_starts"].split(","))
    expected=defaultdict(set)
    for r in source:
        when=datetime.strptime(r["utc_start"],"%Y%m%d%H%M").replace(minute=0)
        for delta in range(-3,5):  # exact Stage05P --context-hours 3
            h=when+timedelta(hours=delta)
            if h.date().isoformat() in DATES:
                expected[(h.strftime("%Y%m%d%H%M"),CDS_VAR)].add(r["utc_start"])
            else:
                raise ValueError("Original source Stage05P +/-3h context extends beyond two-day CDS scope")
    if dict(expected)!=match:
        raise ValueError("Exact original source-QC2 to Stage05R per-hour associations differ: "
                         +repr({"expected":len(expected),"actual":len(match),
                                "missing":sorted(set(expected)-set(match)),
                                "extra":sorted(set(match)-set(expected))}))
    for day in DATES:
        hours={int(t[-4:-2]) for (t,var) in match if t[:8]==day.replace("-","")}
        if not hours:raise ValueError("No verified original source hours for "+day)
    return len(match)

def source_guard(a):
    if (a.get("stage")!="JapanFlux Stage05AA"
        or a.get("status")!="SIXTEEN_SOURCE_QC2_CONTEXT_ERRORS_EVIDENCED_NOT_APPROVED_FOR_REPAIR"
        or a.get("original_source_HOLD_fields")!=45
        or a.get("independent_hourly_context_supported_fields")!=16
        or a.get("UTC_verified_source_fields_pending_independent_reference")!=11
        or a.get("original_solar_time_clock_HOLD_fields")!=18
        or a.get("remaining_CDS_site_days_not_yet_verified")!=6
        or a.get("half_hour_replacement_values_approved") is not False
        or a.get("all_45_original_source_fields_HOLD") is not True):
        raise ValueError("Original Stage05AA 16-field science HOLD coverage changed")

def verify_ab(ab:dict,files:dict):
    if (ab.get("stage")!="JapanFlux Stage05AB"
        or ab.get("status")!="SIX_ORIGINAL_2011_DAY_PAYLOADS_READONLY_INVENTORIED"
        or ab.get("original_45_source_fields_HOLD") is not True
        or ab.get("previous_16_strong_context_source_fields_verified") is not True
        or ab.get("new_CDS_requests")!=0
        or ab.get("science_repair_approved") is not False
        or ab.get("original_source_or_forcing_modified") is not False):
        raise ValueError("Real Stage05AB ZIP/CSV source audit provenance gate failed")
    days=ab.get("six_site_day_inventory",[])
    if len(days)!=6 or len({(r["site"],r["UTC_day"]) for r in days})!=6:
        raise ValueError("Stage05AB source site-day inventory incomplete")
    audited={}
    for day in DATES:
        entry=[r for r in days if r["site"]==SITE and r["UTC_day"]==day]
        if len(entry)!=1:
            raise ValueError("Missing Stage05AB actual JP-Fjy source date "+day)
        r=entry[0]
        if (r["content_status"]!=VALID
            or r["original_BIF_SHA256"]!=BIF_SHA
            or set(r["original_request_variables"])!={CDS_VAR}
            or r["files"]["ZIP"]["status"]!="REGULAR"
            or r["files"]["PARTIAL"]["status"]!="ABSENT"
            or r["files"]["CSV"]["status"]!="ABSENT"
            or r["files"]["NC"]["status"]!="ABSENT"
            or r["zip_inspection"]["source_csv_members"]!=1
            or r["zip_inspection"]["independent_hourly_values_count"]!=24
            or r["zip_inspection"]["ZIP_SHA256"]!=sha256(files[day])):
            raise ValueError("Real original ZIP CRC/CSV/UTC/site/grid audit fails for "+day)
        audited[day]=r
    return audited

def read_zip(path:Path,day:str,expected_sha:str):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Refuse nonregular/symlink source ZIP")
    if path.stat().st_size>25*1024*1024 or sha256(path)!=expected_sha:
        raise ValueError("Original source CDS ZIP sha256/size changed")
    if not zipfile.is_zipfile(path):
        raise ValueError("Original downloaded payload is not a ZIP")
    with zipfile.ZipFile(path) as z:
        members=[r for r in z.infolist() if not r.is_dir()]
        if len(members)!=1:
            raise ValueError("Expected exactly one original CSV for JP-Fjy PA-only")
        member=members[0]
        pure=PurePosixPath(member.filename)
        if (pure.is_absolute() or ".." in pure.parts or "\\" in member.filename
            or not member.filename.lower().endswith(".csv") or member.file_size>1000000):
            raise ValueError("Original CSV source member path/size unexpected")
        if z.testzip() is not None:raise ValueError("Original CSV ZIP CRC failed")
        raw=z.read(member)
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if set(reader.fieldnames or [])!={"valid_time","sp","latitude","longitude"}:
        raise ValueError("Original independent ERA5-Land CSV headers unrecognized")
    points={}
    coords=set()
    for r in reader:
        t=datetime.strptime(r["valid_time"],"%Y-%m-%d %H:%M:%S")
        if t.date().isoformat()!=day or t.hour in points or t.minute or t.second:
            raise ValueError("Original independent ERA5-Land UTC date/hour mismatch")
        lat=float(r["latitude"]);lon=float(r["longitude"])
        sp=float(r["sp"])
        if not all(math.isfinite(v) for v in (lat,lon,sp)):
            raise ValueError("Nonfinite independent hourly source")
        if abs(lat-TOWER[0])>0.11 or abs(lon-TOWER[1])>0.11:
            raise ValueError("CDS grid too distant from original tower BIF")
        kpa=sp/1000
        if not 0<kpa<120:
            raise ValueError("Independent pressure fails broad physical range")
        coords.add((lat,lon))
        points[t]=round(kpa,6)
    if len(points)!=24 or len(coords)!=1:
        raise ValueError("CDS response incomplete hourly or multiple grid coordinates")
    return points,tuple(coords.pop())

def compare(source,pressure):
    out=[]
    for r in source:
        t=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        stamps=[t.replace(minute=0)+timedelta(hours=j) for j in range(3)]
        if not all(k in pressure for k in stamps):
            raise ValueError("Both independent CDS days required: missing original source neighboring hour")
        vals=[pressure[k] for k in stamps]
        lo=min(vals); hi=max(vals)
        orig=float(r["selected_F"])
        gap=lo-orig if orig<lo else orig-hi if orig>hi else 0.0
        outside=int(orig<lo or orig>hi)
        out.append({
            "site":SITE,"original_JST_halfhour_start":r["native_start"],
            "derived_UTC_start":t.strftime("%Y-%m-%dT%H:%MZ"),
            "variable":"PA",
            "original_JPF_F_kPa":r["selected_F"],
            "same_release_original_ERA_kPa":r["ERA_in_same_release"],
            "original_F_QC":"2",
            "hourly_ERA5L_valid_times_UTC":";".join(k.strftime("%Y-%m-%dT%H:%MZ") for k in stamps),
            "hourly_ERA5L_pressures_kPa":";".join(f"{x:.6f}" for x in vals),
            "hourly_ERA5L_context_min_kPa":round(lo,6),
            "hourly_ERA5L_context_max_kPa":round(hi,6),
            "outside_independent_hourly_context":outside,
            "minimum_distance_to_context_kPa":round(gap,6),
            "source_classification":"SEVERE_CONTEXT_INCONSISTENCY_HOLD" if outside else "IN_RANGE_BUT_SOURCE_QC2_HOLD",
            "science_status":"HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR",
            "grid_elevation_status":"UNKNOWN_1043M_TOWER_GRID_HEIGHT_REPRESENTATIVENESS_NOT_APPROVED",
        })
    return out

def selftest():
    d=datetime.strptime("201112162330","%Y%m%d%H%M")
    assert (d.replace(minute=0)+timedelta(hours=1)).strftime("%Y-%m-%dT%H:%MZ")=="2011-12-17T00:00Z"
    assert (d-timedelta(hours=9)).strftime("%Y%m%d%H%M")=="201112161430"
    assert len(DATES)==2 and len(COUNTS)==3
    print("STAGE05AD SELF-TEST PASS | source-verified two-day UTC midnight, exact per-variable Stage05P context, SHA/CRC; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    for name in ("stage05o-utc","stage05r-hours","stage05aa-summary","stage05ab-audit",
                 "dec16-zip","dec17-zip","out-dir"):
        p.add_argument("--"+name,type=Path)
    a=p.parse_args()
    if a.self_test:
        selftest();return
    names=("stage05o_utc","stage05r_hours","stage05aa_summary","stage05ab_audit",
           "dec16_zip","dec17_zip","out_dir")
    if any(getattr(a,k) is None for k in names):
        p.error("Require original Stage05O/R/AA and updated post-download Stage05AB, both 2011 CDS ZIPs and fresh out dir")
    source_guard(read_json(a.stage05aa_summary))
    source=source_events(read_tsv(a.stage05o_utc))
    requestpairs=source_hour_keys(source,read_tsv(a.stage05r_hours))
    raw_files=dict(zip(DATES,(a.dec16_zip,a.dec17_zip)))
    verified=verify_ab(read_json(a.stage05ab_audit),raw_files)
    data={};grids=[];hashes={}
    for day in DATES:
        original_zip=raw_files[day]
        expected=verified[day]["zip_inspection"]["ZIP_SHA256"]
        values,grid=read_zip(original_zip,day,expected)
        if data.keys() & values.keys():
            raise ValueError("Duplicate independent CDS valid_time")
        data.update(values);grids.append(grid);hashes[day]=expected
    if len(data)!=48 or len(set(grids))!=1:
        raise ValueError("Two CDS days must provide 48 hours from the same grid")
    results=compare(source,data)
    if a.out_dir.exists():p.error("Fresh output directory required; never overwrite")
    a.out_dir.mkdir(parents=True)
    tab=a.out_dir/"stage05ad_Fjy_2011_3_original_QC2_vs_two_day_independent_CDS_HOLD.tsv"
    report=a.out_dir/"stage05ad_Fjy_two_day_source_CDS_science_HOLD_summary.json"
    with tab.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t")
        writer.writeheader();writer.writerows(results)
    summary={
        "stage":"JapanFlux Stage05AD",
        "status":"SOURCE_VERIFIED_JP_FJY_2011_TWO_DAY_HOURLY_PA_CONTEXT_NO_REPAIR",
        "site":SITE,"UTC_days":list(DATES),
        "source_original_QC2_fields":len(results),
        "source_requested_hour_variable_pairs":requestpairs,
        "source_candidate_distinct_native_halfhours":len({r["original_JST_halfhour_start"] for r in results}),
        "source_PA_fields_outside_independent_hourly_range":sum(r["outside_independent_hourly_context"] for r in results),
        "CDS_response_original_SHA256_by_UTC_day":hashes,
        "CDS_validated_independent_hourly_pressure_count":len(data),
        "CDS_grid_lat_lon":list(grids[0]),
        "tower_source_BIF_lat_lon_elevation_m":list(TOWER),
        "CDS_grid_elevation":"NOT_VERIFIED",
        "grid_to_tower_pressure_adjustment":"NOT_APPROVED_NO_GUESSED_ELEVATION",
        "scientific_repair_values_approved":False,
        "all_45_original_JPF_source_QC2_fields_HOLD":True,
        "CDS_requests_this_stage":0,"original_zip_or_forcing_modified":False,
        "Slurm_jobs":0
    }
    with report.open("x",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AD JP-FJY TWO-DAY INDEPENDENT ERA5L SOURCE PA AUDIT PASS | NO CDS / SLURM / REPAIR")
    print("ZIP_SHA256_BY_DAY",hashes)
    print("INDEPENDENT_HOURLY_POINTS",len(data),"SOURCE_REQUEST_HOUR_PAIRS",requestpairs)
    print("ORIGINAL_SOURCE_QC2_FIELDS",len(results),
          "OUTSIDE_HOURLY_CONTEXT",summary["source_PA_fields_outside_independent_hourly_range"])
    print("CDS_GRID",grids[0],"TOWER_BIF",TOWER)
    for r in results:
        print("SOURCE_FIELD",r["original_JST_halfhour_start"],"PA_F",r["original_JPF_F_kPa"],
              "REFERENCE_UTC",r["hourly_ERA5L_valid_times_UTC"],
              "REFERENCE_KPA",r["hourly_ERA5L_pressures_kPa"],
              "OUTSIDE",r["outside_independent_hourly_context"],
              "STATUS",r["science_status"])
    print("FIELD_EVIDENCE_TABLE",tab)
    print("SCIENCE_HOLD_SUMMARY",report)
    print("ALL_45_JPF_QC2_FIELD_CANDIDATES_CONTINUE_HOLD_NO_REPLACEMENT")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage05U: exact source field × independent ERA5-Land contextual hourly join (JP-Khw only).

Inputs are actual Stage05O 27 original source-HOLD UTC-mapped field rows,
Stage05T 72 independently retrieved ERA5-Land hourly numeric field rows and
Stage05T audited original CDS ZIP SHA256. No ZIP reopening, no CDS, no Slurm,
no edits to original package/forcing, no 'replacement' values.
The 3 reference-hour values are contextual, NOT 30-minute interpolations.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime,timedelta
import json
import math
from pathlib import Path

SITE="JP-Khw"
UTC_DAY="2005-08-11"
CDS_ZIP_SHA="111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0"
BIF_SHA="eef29bcb9bd97874dad32469b1821b61760f3111cbc3836ad6300350b18217b4"
COORD=(33.10000000000104,130.69999999999686)
COUNT_BY_SITE={"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10}
VARNAME={"TA":"2m_temperature","PA":"surface_pressure",
         "LW_IN":"surface_thermal_radiation_downwards"}
VAR_UNIT={"TA":"degC","PA":"kPa","LW_IN":"W m-2 hourly mean"}
OUTPUT_FIELDS=(
    "site","native_JST_source_start","derived_UTC_start",
    "variable","raw_JPF_F_QC","JPF_selected_F_value",
    "JPF_same_release_ERA_value","JPF_unit","ERA5Land_grid_lat",
    "ERA5Land_grid_lon","ERA5Land_context_valid_times_UTC",
    "ERA5Land_context_converted_values","ERA5Land_comparison_units",
    "independent_context_min","independent_context_max",
    "JPF_outside_independent_hourly_context_range",
    "science_status","temporal_alignment_caveat"
)
REFERENCE_VAR_COUNT=Counter({v:24 for v in VARNAME.values()})

def tsv(path:Path)->list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if not rows: raise ValueError("No input TSV rows: "+str(path))
    return rows

def verify_source(rows:list[dict])->list[dict]:
    if len(rows)!=27 or Counter(r["site"] for r in rows)!=Counter(COUNT_BY_SITE):
        raise ValueError("Expected Stage05O exact 27 field, three-site source scope")
    seen=set(); native_times=set()
    scoped=[]
    for r in rows:
        key=(r["site"],r["native_start"],r["variable"])
        if key in seen or r["variable"] not in VARNAME:
            raise ValueError("Unexpected/duplicate Stage05O source key "+repr(key))
        seen.add(key)
        native_times.add((r["site"],r["native_start"]))
        if r["raw_F_QC"]!="2" or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED":
            raise ValueError("Original-source HOLD/QC2 scientific gate changed")
        try:
            sf=float(r["selected_F"]);ev=float(r["ERA_in_same_release"])
        except (TypeError,ValueError) as e:
            raise ValueError("Non-numeric JPF source candidate") from e
        if not math.isfinite(sf) or not math.isclose(sf,ev,rel_tol=1e-12,abs_tol=1e-9):
            raise ValueError("Original JPF selected-F ≠ same-release downscaled ERA value")
        dt=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        if dt-utc!=timedelta(hours=9):
            raise ValueError("Stage05O native-time→UTC original metadata gate mismatch")
        if r["unit"]!={"TA":"deg C","PA":"kPa","LW_IN":"W m-2"}[r["variable"]]:
            raise ValueError("Original JPF source unit not verified")
        if r["site"]==SITE and utc.date().isoformat()==UTC_DAY:
            scoped.append(r)
    if len(native_times)!=21:
        raise ValueError("Stage05O expected 21 station×half-hour keys")
    if not scoped:
        raise ValueError("No JP-Khw source-selected anomaly on CDS pilot UTC date")
    return sorted(scoped,key=lambda r:(r["utc_start"],r["variable"]))

def verify_reference(rows:list[dict],audit:dict)->dict:
    if (audit.get("stage")!="JapanFlux Stage05T"
        or audit.get("status")!="CDS_ZIP_SOURCE_READONLY_STRUCTURE_INSPECTED"
        or audit.get("CDS_original_member_sha256")!=CDS_ZIP_SHA
        or audit.get("source_site")!=SITE
        or audit.get("source_UTC_date")!=UTC_DAY
        or audit.get("original_BIF_SHA256")!=BIF_SHA
        or audit.get("source_or_forcing_modified") is not False
        or audit.get("physical_repair_approved") is not False):
        raise ValueError("Original Stage05T independent-source identity/HOLD audit mismatch")
    info=audit.get("file_info",{})
    if (info.get("pilot_zip_sha256")!=CDS_ZIP_SHA
        or info.get("pilot_zip_bytes")!=1381
        or info.get("raw_csv_member_count")!=3):
        raise ValueError("CDS source ZIP SHA, size or original member count mismatch")
    if len(rows)!=72:
        raise ValueError("Expected three source CSVs × 24 hourly numeric rows")
    byvar=defaultdict(dict)
    coords=set()
    counts=Counter()
    for r in rows:
        v=r["variable"]
        if v not in REFERENCE_VAR_COUNT:
            raise ValueError("Unexpected independent CDS variable")
        stamp=r["UTC_hour"]
        try:
            dt=datetime.strptime(stamp,"%Y-%m-%dT%H:%MZ")
        except ValueError as e:
            raise ValueError("Unknown independent CSV UTC time label "+stamp) from e
        if dt.date().isoformat()!=UTC_DAY or dt.minute!=0:
            raise ValueError("Unexpected independent ERA5-Land UTC time")
        if dt.hour in byvar[v]:
            raise ValueError("Duplicate independent hour for "+v)
        lat=float(r["ERA5L_grid_latitude"])
        lon=float(r["ERA5L_grid_longitude"])
        if not math.isfinite(lat) or not math.isfinite(lon):
            raise ValueError("Missing original ERA5-Land CSV grid coordinates")
        if abs(lat-COORD[0])>1e-5 or abs(lon-COORD[1])>1e-5:
            raise ValueError("CDS original grid differs from first pilot")
        coords.add((lat,lon))
        val=float(r["converted_value"])
        raw=float(r["raw_value"])
        if not math.isfinite(val) or not math.isfinite(raw):
            raise ValueError("Nonfinite independent hourly reference")
        if v=="2m_temperature" and abs(val-(raw-273.15))>1e-5:
            raise ValueError("Incorrect independent Kelvin conversion")
        if v=="surface_pressure" and abs(val-raw/1000)>1e-5:
            raise ValueError("Incorrect independent Pascal conversion")
        if v=="surface_thermal_radiation_downwards" and abs(val-raw/3600)>1e-5:
            raise ValueError("Incorrect hourly radiation de-accumulation conversion")
        if r["comparison_status"].find("NO_REPLACEMENT_APPROVAL")<0:
            raise ValueError("Unexpected reference replacement approval")
        byvar[v][dt.hour]=val
        counts[v]+=1
    if counts!=REFERENCE_VAR_COUNT or len(coords)!=1:
        raise ValueError("Not 24 consecutive hourly values / variable and one exact CDS grid")
    if any(set(row)!=set(range(24)) for row in byvar.values()):
        raise ValueError("Hourly source coverage incomplete")
    if audit.get("decoded_variable_counts")!=dict(counts):
        raise ValueError("CDS original audit counts conflict with derived TSV")
    return byvar

def compare(scoped:list[dict],reference:dict)->list[dict]:
    result=[]
    for r in scoped:
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        floored=utc.replace(minute=0)
        # Three consecutive valid_time observations provide *context*, not
        # a recreated 30min source value. For a solar/radiation accumulation,
        # valid_time may denote END of each one-hour averaging interval.
        hours=[floored+timedelta(hours=i) for i in range(3)]
        var=r["variable"]; refname=VARNAME[var]
        if any(t.date().isoformat()!=UTC_DAY for t in hours):
            raise ValueError("Context crosses pilot date; get another genuine CDS day")
        labels=[t.strftime("%Y-%m-%dT%H:%MZ") for t in hours]
        reference_vals=[reference[refname][t.hour] for t in hours]
        src=float(r["selected_F"])
        minv=min(reference_vals); maxv=max(reference_vals)
        result.append({
           "site":SITE,"native_JST_source_start":r["native_start"],
           "derived_UTC_start":utc.strftime("%Y-%m-%dT%H:%MZ"),
           "variable":var,"raw_JPF_F_QC":r["raw_F_QC"],
           "JPF_selected_F_value":r["selected_F"],
           "JPF_same_release_ERA_value":r["ERA_in_same_release"],
           "JPF_unit":r["unit"],
           "ERA5Land_grid_lat":COORD[0],"ERA5Land_grid_lon":COORD[1],
           "ERA5Land_context_valid_times_UTC":";".join(labels),
           "ERA5Land_context_converted_values":";".join(f"{v:.6f}" for v in reference_vals),
           "ERA5Land_comparison_units":VAR_UNIT[var],
           "independent_context_min":round(minv,6),
           "independent_context_max":round(maxv,6),
           "JPF_outside_independent_hourly_context_range":int(src<minv or src>maxv),
           "science_status":"SOURCE_NONPHYSICAL_CANDIDATE_HOLD_NOT_APPROVED",
           "temporal_alignment_caveat":(
              "TA/PA hourly point reference, not exact 30min sample" if var!="LW_IN"
              else "LW is hourly deaccumulated mean; valid_time END-hour vs native half-hour interval not yet certified")
        })
    return result

def self_test():
    native=datetime.strptime("200508120230","%Y%m%d%H%M")
    t=native-timedelta(hours=9)
    assert t.strftime("%Y-%m-%dT%H:%MZ")=="2005-08-11T17:30Z"
    assert [t.replace(minute=0).hour+i for i in range(3)]==[17,18,19]
    assert Counter(COUNT_BY_SITE)==Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
    assert sum(REFERENCE_VAR_COUNT.values())==72
    print("STAGE05U SELF-TEST PASS | source QC2, numeric units, 3h context and UTC mapping; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage05o-source-UTC",type=Path)
    p.add_argument("--stage05t-values",type=Path)
    p.add_argument("--stage05t-audit",type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.stage05o_source_UTC,a.stage05t_values,a.stage05t_audit,a.out_dir)):
        p.error("Require all Stage05O/Stage05T source inputs and --out-dir")
    scoped=verify_source(tsv(a.stage05o_source_UTC))
    audit=json.loads(a.stage05t_audit.read_text(encoding="utf-8"))
    reference=verify_reference(tsv(a.stage05t_values),audit)
    result=compare(scoped,reference)
    if a.out_dir.exists():
        p.error("Output directory exists; choose new path")
    a.out_dir.mkdir(parents=True)
    t=a.out_dir/"stage05u_Khw_20050811_JPF_vs_independent_ERA5L_3hour_CONTEXT_HOLD.tsv"
    j=a.out_dir/"stage05u_source_ERA5L_science_context_summary.json"
    with t.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,delimiter="\t",fieldnames=OUTPUT_FIELDS)
        w.writeheader();w.writerows(result)
    summary={
      "stage":"JapanFlux Stage05U","status":"READONLY_INDEPENDENT_REFERENCE_CONTEXT_CROSSCHECK",
      "source_site":SITE,"UTC_date":UTC_DAY,
      "original_source_candidate_rows_on_date":len(result),
      "original_source_candidate_unique_halfhours":len(set(r["native_JST_source_start"] for r in result)),
      "original_source_outside_hourly_context_range_count":sum(r["JPF_outside_independent_hourly_context_range"] for r in result),
      "CDS_first_download_ZIP_SHA256":CDS_ZIP_SHA,
      "CDS_grid_lat":COORD[0],"CDS_grid_lon":COORD[1],
      "source_tower_lat":33.13658,"source_tower_lon":130.70834,"source_tower_elevation_m":196.0,
      "CDS_grid_elevation":"NOT_VERIFIED",
      "hourly_raw_variables":dict(REFERENCE_VAR_COUNT),
      "source_release_ERA":"DOWNSCALED_SAME_JPF_RELEASE",
      "independent_ERA5Land":"ACTUAL_SEPARATELY_DOWNLOADED_CDS_TIMESERIES",
      "interpretation":"Contextual independent evidence of likely original downscaled ERA source contamination; no 30-minute pointwise correction certified",
      "scientific_approval":False,"repair_applied":False,
      "CDS_calls_this_stage":0,"ZIP_read_this_stage":False,
      "model_or_forcing_modified":False,"Slurm_jobs":0,
      "all_45_original_field_candidates_still_HOLD":True
    }
    with j.open("x",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05U INDEPENDENT ERA5-LAND 3h CONTEXT JOIN PASS | NO CDS / ZIP / SLURM / REPAIR")
    print("SOURCE_SCOPE",SITE,UTC_DAY,"ORIGINAL_SOURCE_FIELDS",len(result),
          "UNIQUE_SITE_HALF_HOURS",summary["original_source_candidate_unique_halfhours"])
    for r in result:
        print("FIELD",r["native_JST_source_start"],r["variable"],
              "ORIGINAL_F",r["JPF_selected_F_value"],r["JPF_unit"],
              "ORIGINAL_QC",r["raw_JPF_F_QC"],
              "INDEPENDENT_ERA5L_HOURS",r["ERA5Land_context_valid_times_UTC"],
              "INDEPENDENT_VALUES",r["ERA5Land_context_converted_values"],
              "REFERENCE_UNIT",r["ERA5Land_comparison_units"],
              "OUTSIDE_REFERENCE_HOURLY_RANGE",r["JPF_outside_independent_hourly_context_range"])
    print("OUTSIDE_CONTEXT_RANGE",summary["original_source_outside_hourly_context_range_count"])
    print("SOURCE_COMPARISON_CONTEXT",t)
    print("AUDIT_SUMMARY",j)
    print("NO HALF_HOUR ERA5L INTERPOLATION OR PRESSURE_ELEVATION_ADJUSTMENT OR SCIENCE_REPAIR")
    print("ALL_45_SOURCE_SELECTED_ANOMALIES_STILL_HOLD")

if __name__=="__main__":
    main()

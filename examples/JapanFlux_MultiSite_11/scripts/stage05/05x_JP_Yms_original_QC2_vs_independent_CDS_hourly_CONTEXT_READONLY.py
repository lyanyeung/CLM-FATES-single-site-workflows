#!/usr/bin/env python3
"""Stage05X: exact JP-Yms original QC2 selected F vs independent CDS hourly context.

Inputs only Stage05O original 27 verified-UTC source fields plus actual
Stage05W2 independently-downloaded JP-Yms ERA5-Land 2×24 hourly TSV + audit.
No CDS request, ZIP input, native JPF source, Slurm, forcing edits or repair.
Compares original half-hour source flags with 3 nearby hourly *context*
values of the SAME variable; no inferred 30-minute replacement values.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import json
import math
from pathlib import Path

SITE = "JP-Yms"
DAY = "2005-08-11"
CDS_SHA = "4bf228a3a53ab7fc6751b8e7438fb459570536ce6f54af2f81de5afc083b59d5"
BIF_SHA = "7c0a5ba5f137e28518f69ed14b255834fb5b223ac325556719abe5a55e8b0f56"
GRID = (34.80000000000106, 135.79999999999654)
TOWER = (34.790278, 135.840939, 220.0)
COUNTS = Counter({"JP-Fjy":6, "JP-Khw":11, "JP-Yms":10})
VARS = {
    "PA": ("surface_pressure", "kPa", "kPa"),
    "LW_IN": ("surface_thermal_radiation_downwards", "W m-2", "W m-2 hourly mean"),
}
FIELDS = (
    "site", "native_start_JST", "UTC_start",
    "variable", "original_F", "original_same_release_ERA",
    "original_F_QC", "original_units", "CDS_grid_lat", "CDS_grid_lon",
    "independent_UTC_hour_valid_times", "independent_hourly_values",
    "independent_reference_units", "independent_context_min",
    "independent_context_max", "original_outside_hourly_context_range",
    "minimum_abs_gap_to_hourly_context", "science_qualification",
    "source_and_model_status",
)

def read_tsv(path:Path)->list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError("Missing/duplicate input column names")
        rows=list(reader)
    if not rows:
        raise ValueError("No input rows "+str(path))
    return rows

def check_orig(records:list[dict])->list[dict]:
    if len(records)!=27 or Counter(r["site"] for r in records)!=COUNTS:
        raise ValueError("Stage05O original UTC-approved field scope changed (27, 6/11/10)")
    seen=set(); source_time_pairs=set(); original_yms=Counter(); selected=[]
    for r in records:
        key=(r["site"],r["native_start"],r["variable"])
        if key in seen:
            raise ValueError("Duplicate original QC2 site/native/variable "+repr(key))
        seen.add(key);source_time_pairs.add((r["site"],r["native_start"]))
        if (r["raw_F_QC"]!="2"
            or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"):
            raise ValueError("Original JPF QC2 or HOLD status was changed")
        native=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        if native-utc!=timedelta(hours=9):
            raise ValueError("Original local standard time UTC offset not +9")
        original=float(r["selected_F"]); internal=float(r["ERA_in_same_release"])
        if not (math.isfinite(original) and math.isfinite(internal)
                and math.isclose(original,internal,abs_tol=1e-9,rel_tol=1e-12)):
            raise ValueError("Original source selected-F and same-release embedded ERA differ")
        if r["site"]!=SITE:continue
        original_yms[r["variable"]]+=1
        if r["variable"] not in VARS or r["unit"]!=VARS[r["variable"]][1]:
            raise ValueError("Unexpected original JP-Yms variable/units")
        if utc.date().isoformat()==DAY:
            selected.append(r)
    if len(source_time_pairs)!=21 or original_yms!=Counter({"PA":6,"LW_IN":4}):
        raise ValueError("Stage05O 21 site×halfhour/JP-Yms 6 PA+4 LW provenance changed")
    if not selected:
        raise ValueError("No original JP-Yms 2005-08-11 UTC candidate fields")
    if len(selected)>=10:
        raise ValueError("Expected at least one later-date Yms candidate; confirm actual source")
    return sorted(selected,key=lambda r:(r["utc_start"],r["variable"]))

def check_cds(records:list[dict],audit:dict)->dict[str,dict[int,float]]:
    if (audit.get("stage")!="JapanFlux Stage05W2"
        or audit.get("status")!="PASS_SOURCE_SPARSE_HOURS_AND_SECOND_REAL_CDS_ZIP"
        or audit.get("site")!=SITE
        or audit.get("UTC_date")!=DAY
        or audit.get("raw_CDS_ZIP_SHA256")!=CDS_SHA
        or audit.get("original_source_BIF_SHA256")!=BIF_SHA
        or audit.get("original_CDS_zip_bytes")!=936
        or audit.get("hourly_independent_variable_records")!=48
        or audit.get("source_specific_scope",{}).get("source_variable_hour_pairs")!=17
        or audit.get("source_specific_scope",{}).get("variable_hour_counts")
           !={"surface_pressure":9,"surface_thermal_radiation_downwards":8}
        or audit.get("false_cartesian_gate_in_old_stage05w")
           !="REMOVED_BY_SOURCE_VERIFIED_EXACT_KEYS"
        or audit.get("CDS_calls_this_stage")!=0
        or audit.get("original_source_or_model_forcing_modified") is not False
        or audit.get("half_hour_replacement_approved") is not False
        or audit.get("all_45_JPF_original_flagged_fields_HOLD") is not True):
        raise ValueError("Actual independently sourced Stage05W2 audit gate changed")
    if len(records)!=48:
        raise ValueError("Expected complete 24-hour × 2-variable independent ERA5-Land rows")
    valid_refs={v[0] for v in VARS.values()}
    grouped=defaultdict(dict); grids=set()
    for r in records:
        v=r["variable"]
        if v not in valid_refs:
            raise ValueError("Unknown downloaded CDS original variable "+v)
        t=datetime.strptime(r["UTC_valid_time"],"%Y-%m-%dT%H:%MZ")
        if t.date().isoformat()!=DAY or t.minute!=0 or t.second!=0:
            raise ValueError("CDS UTC timestamp differs from 2005-08-11 hourly contract")
        if t.hour in grouped[v]:
            raise ValueError("CDS duplicate UTC hour")
        lat=float(r["CDS_grid_lat"]);lon=float(r["CDS_grid_lon"])
        if not all(math.isfinite(x) for x in (lat,lon)) or (
            abs(lat-GRID[0])>1e-5 or abs(lon-GRID[1])>1e-5):
            raise ValueError("Downloaded CDS grid coordinate changed")
        grids.add((lat,lon))
        x=float(r["independent_converted_hourly_value"])
        original=float(r["independent_raw_value"])
        if not (math.isfinite(x) and math.isfinite(original)):
            raise ValueError("Independent ERA5-Land numeric is nonfinite")
        expected_raw_unit="Pa" if v=="surface_pressure" else "J m-2/hour"
        expected_unit="kPa" if v=="surface_pressure" else "W m-2 hourly mean"
        if (r["independent_raw_units"]!=expected_raw_unit
            or r["converted_units"]!=expected_unit):
            raise ValueError("Independent source units mismatched")
        reconstructed=original/(1000 if v=="surface_pressure" else 3600)
        if not math.isclose(x,reconstructed,abs_tol=1e-5,rel_tol=1e-7):
            raise ValueError("Incorrect independent reference unit conversion")
        if r["science_status"]!="INDEPENDENT_ERA5L_HOURLY_REFERENCE_ONLY_NOT_APPROVED_FOR_REPLACEMENT":
            raise ValueError("Unexpected source repair approval in Stage05W2 TSV")
        if not (0<x<120 if v=="surface_pressure" else 0<=x<1500):
            raise ValueError("Independent ERA5-Land value fails broad physical screen")
        grouped[v][t.hour]=x
    if len(grids)!=1 or set(grouped)!=valid_refs or any(set(x)!=set(range(24)) for x in grouped.values()):
        raise ValueError("Independent grid/24-hour coverage incomplete")
    return grouped

def compare(scoped:list[dict],ref:dict)->list[dict]:
    results=[]
    for r in scoped:
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        clock=utc.replace(minute=0)
        times=[clock+timedelta(hours=h) for h in range(3)]
        if any(t.date().isoformat()!=DAY for t in times):
            raise ValueError("Independent 3-hour context goes past checked CDS day")
        var=r["variable"]
        cdsvar=VARS[var][0]
        vals=[ref[cdsvar][t.hour] for t in times]
        source=float(r["selected_F"])
        lo=min(vals);hi=max(vals)
        outside=source<lo or source>hi
        distance=lo-source if source<lo else source-hi if source>hi else 0.0
        results.append({
            "site":SITE,
            "native_start_JST":r["native_start"],
            "UTC_start":utc.strftime("%Y-%m-%dT%H:%MZ"),
            "variable":var,"original_F":r["selected_F"],
            "original_same_release_ERA":r["ERA_in_same_release"],
            "original_F_QC":"2","original_units":r["unit"],
            "CDS_grid_lat":GRID[0],"CDS_grid_lon":GRID[1],
            "independent_UTC_hour_valid_times":";".join(t.strftime("%Y-%m-%dT%H:%MZ") for t in times),
            "independent_hourly_values":";".join(f"{v:.6f}" for v in vals),
            "independent_reference_units":VARS[var][2],
            "independent_context_min":round(lo,6),
            "independent_context_max":round(hi,6),
            "original_outside_hourly_context_range":int(outside),
            "minimum_abs_gap_to_hourly_context":round(distance,6),
            "science_qualification":(
                "STRONG_CONTEXTUAL_INCONSISTENCY_PENDING_PHYSICS_REVIEW"
                if outside else "INSIDE_HOURLY_CONTEXT_BUT_ORIGINAL_SOURCE_QC2_REMAINS_HOLD"),
            "source_and_model_status":"ORIGINAL_QC2_HOLD_NO_HALF_HOUR_INTERPOLATION_NO_FORCING_WRITES",
        })
    return results

def self_test():
    x=datetime.strptime("200508120230","%Y%m%d%H%M")
    utc=x-timedelta(hours=9)
    assert utc.strftime("%Y-%m-%dT%H:%MZ")=="2005-08-11T17:30Z"
    assert [t.hour for t in [utc.replace(minute=0)+timedelta(hours=k) for k in range(3)]]==[17,18,19]
    assert sum(COUNTS.values())==27
    assert math.isclose(97_800/1000,97.8) and math.isclose(1_440_000/3600,400)
    print("STAGE05X SELF-TEST PASS | Yms original source F=ERA QC2, independent 24x2 hourly source context; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage05o-source-UTC",type=Path)
    p.add_argument("--stage05w2-values",type=Path)
    p.add_argument("--stage05w2-audit",type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if any(x is None for x in (a.stage05o_source_UTC,a.stage05w2_values,
                               a.stage05w2_audit,a.out_dir)):
        p.error("Require verified Stage05O TSV, Stage05W2 TSV+JSON and fresh output dir")
    src=check_orig(read_tsv(a.stage05o_source_UTC))
    audit=json.loads(a.stage05w2_audit.read_text(encoding="utf-8"))
    vals=check_cds(read_tsv(a.stage05w2_values),audit)
    review=compare(src,vals)
    if a.out_dir.exists():
        p.error("Output directory exists; no overwrite")
    a.out_dir.mkdir(parents=True)
    t=a.out_dir/"stage05x_JP_Yms_20050811_original_F_vs_independent_ERA5L_3h_CONTEXT_HOLD.tsv"
    j=a.out_dir/"stage05x_original_source_and_independent_ERA5L_review.json"
    with t.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t")
        w.writeheader();w.writerows(review)
    summary={
        "stage":"JapanFlux Stage05X",
        "status":"READONLY_SOURCE_QC2_VS_SEPARATELY_RETRIEVED_CDS_HOURLY_CONTEXT",
        "site":SITE,"UTC_date":DAY,
        "source_fields_on_checked_UTC_day":len(review),
        "source_unique_halfhour_times":len(set(r["native_start_JST"] for r in review)),
        "source_variable_counts":dict(Counter(r["variable"] for r in review)),
        "fields_outside_independent_3hour_context":sum(r["original_outside_hourly_context_range"] for r in review),
        "original_source_selected_F_QC":"2",
        "original_same_release_ERA":"SOURCE_DOWNSCALED_NOT_INDEPENDENT",
        "independently_downloaded_CDS_original_ZIP_SHA256":CDS_SHA,
        "independent_variable_hourly_rows":48,
        "tower_original_BIF_location":list(TOWER),
        "independent_ERA5L_grid":list(GRID),
        "ERA5L_grid_elevation":"NOT_VERIFIED",
        "source_native_halfhour_vs_CDS_hourly":"CONTEXT_ONLY_NO_POINTWISE_VALUE",
        "remaining_original_fields_not_checked_here":45-len(review),
        "original_45_source_fields_status":"ALL_HOLD",
        "CDS_downloads_this_stage":0,"raw_source_ZIPs_read_this_stage":False,
        "scientific_half_hour_repair_approved":False,
        "forcing_or_model_modified":False,"Slurm_jobs":0,
    }
    with j.open("x",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05X JP-YMS ORIGINAL QC2 VS INDEPENDENT ERA5L CONTEXT PASS | NO CDS / SLURM / REPAIR")
    print("SITE",SITE,"UTC_DATE",DAY,"SOURCE_FIELDS",len(review),
          "UNIQUE_SOURCE_HALF_HOURS",summary["source_unique_halfhour_times"])
    print("BY_VARIABLE",summary["source_variable_counts"])
    print("OUTSIDE_3H_CONTEXT",summary["fields_outside_independent_3hour_context"])
    for r in review:
        print("FIELD",r["native_start_JST"],r["variable"],
              "JPF_F",r["original_F"],"SOURCE_QC",r["original_F_QC"],
              "CDS_HOURS",r["independent_UTC_hour_valid_times"],
              "CDS_VALUES",r["independent_hourly_values"],
              "CONTEXT_RANGE",r["independent_context_min"],r["independent_context_max"],
              "OUTSIDE",r["original_outside_hourly_context_range"],
              "SCIENTIFIC_STATUS",r["science_qualification"])
    print("SOURCE_TO_REFERENCE_EVIDENCE",t)
    print("SUMMARY",j)
    print("ALL_45_ORIGINAL_QC2_FIELDS_REMAIN_HOLD_NO_APPROVED_REPLACEMENTS")

if __name__=="__main__":
    main()

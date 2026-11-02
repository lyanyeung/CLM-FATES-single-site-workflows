#!/usr/bin/env python3
"""JapanFlux Stage05AA: merge 13 previously evidenced + 3 JP-Fjy 2005 PA contexts.

Strict READ-ONLY, sourced solely from observed Stage05Y/05Z/05O derived TSV/JSON.
Original JP-Fjy CDS-compatible ZIP was already present: its CRC and source/time/
grid/schema were verified, but there is NO observed earlier CDS submission ID.
Thus classify it as validated existing external reference file, NOT evidence
that a new CDS request was submitted by Stage05Z.

No CDS, ZIP reading, Slurm, original forcing/model edits, 30min replacement,
or automated approval. Keep all 45 original source anomaly candidates HOLD.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from datetime import datetime,timedelta
import hashlib
import json
import math
from pathlib import Path

JPF_ZIP_SHA="0c51e921a3c35b15dae2c33576517e93ca49b2e0ab584212fc8d505fa3efaad3"
FJY_SOURCE_BIF="b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62"
FJY_GRID=(35.50000000000107,138.79999999999643)
COUNTS=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
CLOCK_HOLD_COUNTS=Counter({"JP-Tef":4,"JP-Tmd":14})
FJY_KEYS={("JP-Fjy","200508120230","PA"),
          ("JP-Fjy","200508120300","PA"),
          ("JP-Fjy","200508120330","PA")}
OUT_FIELDS=("site","native_JST_halfhour_start","UTC_halfhour_start","variable",
 "original_JPF_F","source_same_release_ERA","source_QC","source_units",
 "independent_CDS_ZIP_SHA256","reference_provenance_class",
 "independent_hourly_context_min","independent_hourly_context_max",
 "independent_reference_units","minimum_gap_to_hourly_context",
 "context_outside","evidence_label","repair_status",
 "time_grid_and_representativeness_limit")
REMAINING_SIX={
 ("JP-Fjy","2011-12-16"),("JP-Fjy","2011-12-17"),
 ("JP-Khw","2011-12-16"),("JP-Khw","2011-12-17"),
 ("JP-Yms","2011-12-16"),("JP-Yms","2011-12-17")}

def tsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as stream:
        rd=csv.DictReader(stream,delimiter="\t")
        if not rd.fieldnames or len(rd.fieldnames)!=len(set(rd.fieldnames)):
            raise ValueError("Invalid input TSV column schema")
        rows=list(rd)
    if not rows:raise ValueError("Empty input "+str(p))
    return rows

def js(p:Path):
    obj=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):raise ValueError("Expected provenance JSON object")
    return obj

def sha(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def original_registry(src,native):
    if len(src)!=27 or Counter(r["site"] for r in src)!=COUNTS:
        raise ValueError("Original 27 verified UTC source QC2 records changed")
    if len(native)!=18 or Counter(r["site"] for r in native)!=CLOCK_HOLD_COUNTS:
        raise ValueError("Original 18 solar-time HOLD source records changed")
    bykey={}
    native_keys=set()
    for r in src:
        k=r["site"],r["native_start"],r["variable"]
        if k in bykey:raise ValueError("Duplicate original UTC candidate")
        if r["raw_F_QC"]!="2" or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED":
            raise ValueError("Original source QC2/HOLD gate changed")
        start=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        if start-utc!=timedelta(hours=9):
            raise ValueError("Original UTC+9 local standard time proof changed")
        x=float(r["selected_F"]); y=float(r["ERA_in_same_release"])
        if not all(math.isfinite(v) for v in (x,y)) or not math.isclose(x,y,abs_tol=1e-9,rel_tol=1e-12):
            raise ValueError("Original F differs from same-release embedded ERA")
        bykey[k]=r
    for r in native:
        k=r["site"],r["native_start"],r["variable"]
        if k in bykey or k in native_keys:
            raise ValueError("Duplicate original source/native-only candidate")
        native_keys.add(k)
        if (r["raw_F_QC"]!="2" or r["utc_start"]!="UNRESOLVED"
            or r["source_status"]!="HOLD_LOCAL_SOLAR_VS_STANDARD_TIME_PROVENANCE"):
            raise ValueError("Never silently convert original Tef/Tmd clock")
    if len({(s,t) for s,t,v in bykey})!=21 or len({(s,t) for s,t,v in native_keys})!=14:
        raise ValueError("Original 45-field/35-site-native-time count changed")
    return bykey

def verify_05y(rows,summary,registry):
    if (summary.get("stage")!="JapanFlux Stage05Y"
        or summary.get("status")!="THIRTEEN_SOURCE_FIELDS_STRONGLY_CONTRADICTED_BY_SEPARATE_ERA5L_CONTEXT_NOT_REPAIRED"
        or summary.get("original_source_total_HOLD_fields")!=45
        or summary.get("independently_evidenced_source_fields")!=13
        or summary.get("independently_evidenced_unique_site_halfhours")!=8
        or summary.get("independent_CDS_site_days_downloaded")!=2
        or summary.get("independent_CDS_site_days_not_yet_downloaded")!=7
        or summary.get("UTC_verified_fields_not_yet_independently_compared")!=14
        or summary.get("unresolved_solar_vs_standard_time_source_fields")!=18
        or summary.get("no_repair_value_approved") is not True
        or summary.get("no_forcing_or_model_write") is not True):
        raise ValueError("Actual Stage05Y source science/coverage gates changed")
    if len(rows)!=13 or Counter(r["site"] for r in rows)!=Counter({"JP-Khw":8,"JP-Yms":5}):
        raise ValueError("Expected 13 prior source fields at Khw/Yms")
    results=[]
    seen=set()
    for r in rows:
        k=r["site"],r["native_JST_halfhour_start"],r["variable"]
        if k in seen or k not in registry:raise ValueError("Prior evidence unknown or duplicate original source key")
        seen.add(k)
        a=registry[k]
        if (r["source_QC"]!="2" or
            r["repair_status"]!="SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT"
            or str(r["context_outside"])!="1"):
            raise ValueError("Stage05Y original 13 evidence/HOLD changed")
        src=float(r["original_JPF_F"]);internal=float(r["source_same_release_ERA"])
        if not (math.isclose(src,float(a["selected_F"]),rel_tol=1e-12,abs_tol=1e-9)
                and math.isclose(internal,float(a["ERA_in_same_release"]),rel_tol=1e-12,abs_tol=1e-9)):
            raise ValueError("Prior evidence no longer matches source QC2")
        if r["UTC_halfhour_start"]!=datetime.strptime(a["utc_start"],"%Y%m%d%H%M").strftime("%Y-%m-%dT%H:%MZ"):
            raise ValueError("Prior source original UTC event mismatch")
        low=float(r["independent_hourly_context_min"])
        high=float(r["independent_hourly_context_max"])
        if not (math.isfinite(low) and math.isfinite(high) and low<=high
                and (src<low or src>high)):
            raise ValueError("Prior independently evidenced source outside reference gate failed")
        converted=dict(r)
        converted["reference_provenance_class"]="CDS_SUCCESSFUL_SUBMISSION_LOG_AND_PAYLOAD_VERIFIED"
        results.append(converted)
    return results

def verify_05z(rows,audit,registry):
    if (audit.get("stage")!="JapanFlux Stage05Z"
        or audit.get("status")!="SOURCE_EXACT_FJY_INDEPENDENT_HOURLY_PRESSURE_CONTEXT_AUDITED"
        or audit.get("site")!="JP-Fjy" or audit.get("UTC_date")!="2005-08-11"
        or audit.get("source_BIF_SHA256")!=FJY_SOURCE_BIF
        or audit.get("original_CDS_ZIP_sha256")!=JPF_ZIP_SHA
        or audit.get("original_CDS_ZIP_bytes")!=484
        or audit.get("independent_hourly_count")!=24
        or audit.get("original_site_source_QC2_field_count")!=3
        or audit.get("source_requested_variable_hour_pairs")!=9
        or audit.get("source_fields_outside_hourly_context")!=3
        or audit.get("pressure_grid_altitude")!="UNKNOWN_NEEDS_INDEPENDENT_GEOPOTENTIAL"
        or audit.get("source_halfhour_pressure_replacement_approved") is not False
        or audit.get("original_source_or_forcing_changed") is not False
        or audit.get("CDS_request_this_stage") is not False
        or audit.get("all_45_JPF_source_candidate_fields_still_HOLD") is not True):
        raise ValueError("Actual Stage05Z independently verified old ZIP/pressure source status changed")
    grids=audit.get("CDS_grid_coordinates")
    if (len(grids)!=1 or abs(float(grids[0][0])-FJY_GRID[0])>1e-5
        or abs(float(grids[0][1])-FJY_GRID[1])>1e-5):
        raise ValueError("Original JP-Fjy reference land-grid coordinates changed")
    if len(rows)!=3:
        raise ValueError("Expected exactly three JP-Fjy original source QC2 PA records")
    records=[]
    keys=set()
    for r in rows:
        k=r["site"],r["original_JST_halfhour_start"],r["source_variable"]
        if k in keys or k not in FJY_KEYS or k not in registry:
            raise ValueError("Stage05Z source PA key out of original source registry")
        keys.add(k)
        orig=registry[k]
        v=float(r["original_JPF_F_kPa"])
        internal=float(r["same_release_JPF_ERA_kPa"])
        if not (r["JPF_F_QC"]=="2"
            and math.isclose(v,float(orig["selected_F"]),abs_tol=1e-9,rel_tol=1e-12)
            and math.isclose(internal,float(orig["ERA_in_same_release"]),abs_tol=1e-9,rel_tol=1e-12)
            and orig["unit"]=="kPa"):
            raise ValueError("Stage05Z original JPF source F=ERA QC2 mismatch")
        utc=datetime.strptime(orig["utc_start"],"%Y%m%d%H%M")
        if r["UTC_halfhour_start"]!=utc.strftime("%Y-%m-%dT%H:%MZ"):
            raise ValueError("JP-Fjy source UTC time provenance changed")
        labels=r["CDS_three_hour_valid_times"].split(";")
        vals=[float(x) for x in r["CDS_three_hour_pressure_kPa"].split(";")]
        expected=[(utc.replace(minute=0)+timedelta(hours=j)).strftime("%Y-%m-%dT%H:%MZ") for j in range(3)]
        if labels!=expected or len(vals)!=3 or any(not math.isfinite(x) for x in vals):
            raise ValueError("Stage05Z original CDS neighboring UTC hour values mismatch")
        low=min(vals);high=max(vals)
        if (not math.isclose(low,float(r["independent_hourly_min_kPa"]),abs_tol=1e-5)
            or not math.isclose(high,float(r["independent_hourly_max_kPa"]),abs_tol=1e-5)
            or r["outside_hourly_context"]!="1"
            or not (v<low or v>high)
            or r["science_gate"]!="HOLD_GRID_ALTITUDE_UNVERIFIED_NO_POINTWISE_HALF_HOUR_REPLACEMENT"):
            raise ValueError("Stage05Z science/independent source context gate differs")
        gap=low-v if v<low else v-high
        if not math.isclose(gap,float(r["source_to_nearest_context_edge_abs_kPa"]),abs_tol=1e-5):
            raise ValueError("Stage05Z independent reference gap unexpected")
        records.append({
            "site":r["site"],"native_JST_halfhour_start":r["original_JST_halfhour_start"],
            "UTC_halfhour_start":r["UTC_halfhour_start"],
            "variable":"PA","original_JPF_F":orig["selected_F"],
            "source_same_release_ERA":orig["ERA_in_same_release"],
            "source_QC":"2","source_units":"kPa",
            "independent_CDS_ZIP_SHA256":JPF_ZIP_SHA,
            "reference_provenance_class":"EXISTING_CDS_FORMAT_ZIP_CONTENT_SHA_CRC_VERIFIED_REQUEST_LOG_NOT_OBSERVED",
            "independent_hourly_context_min":round(low,6),
            "independent_hourly_context_max":round(high,6),
            "independent_reference_units":"kPa",
            "minimum_gap_to_hourly_context":round(gap,6),
            "context_outside":1,
            "evidence_label":"STRONGLY_INCONSISTENT_EXTREME_SURFACE_PRESSURE_CONTEXT",
            "repair_status":"SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT",
            "time_grid_and_representativeness_limit":(
                "ERA5-Land 0.1 degree grid vs 1043m original JP-Fjy tower; "
                "grid relief/geopotential NOT checked, no pointwise 30min adjustment or repair")
        })
    if keys!=FJY_KEYS:raise ValueError("Original JP-Fjy three candidate keys changed")
    return records

def six_days(remaining):
    if (remaining.get("stage")!="JapanFlux Stage05Y"
        or remaining.get("status")!="SEVEN_UNREQUESTED_SITE_DAYS_PREVIEW_ONLY"
        or remaining.get("remaining_count")!=7
        or remaining.get("CDS_downloads_this_stage")!=0
        or remaining.get("source_or_model_changes") is not False):
        raise ValueError("Require original Stage05Y seven-day no-CDS history")
    entries=remaining.get("remaining",[])
    if len(entries)!=7 or len({(r["site"],r["UTC_day"]) for r in entries})!=7:
        raise ValueError("Old CDS site/day keys missing or duplicated")
    target=("JP-Fjy","2005-08-11")
    ids={(r["site"],r["UTC_day"]) for r in entries}
    if target not in ids or ids-{target}!=REMAINING_SIX:
        raise ValueError("Unexpected original Stage05Y site/day scope")
    result=[]
    for r in entries:
        if (r["site"],r["UTC_day"])==target:continue
        if (r["CDS_dataset"]!="reanalysis-era5-land-timeseries"
            or not r["variable_scope"] or not r["source_UTC_hours"]
            or len(r["source_BIF_SHA256"])!=64):
            raise ValueError("Remaining source day provenance changed")
        result.append(r)
    return sorted(result,key=lambda r:(r["site"],r["UTC_day"]))

def self_test():
    assert len(FJY_KEYS)==3 and len(REMAINING_SIX)==6
    assert 13+3+11+18==45
    assert 8+3==11
    assert ("JP-Fjy","200508120300","PA") in FJY_KEYS
    print("STAGE05AA SELF-TEST PASS | prior13 + Fjy3, existing ZIP provenance distinction, six days; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    for name in ("stage05o-utc","stage05o-native-hold","stage05y-evidence",
                 "stage05y-summary","stage05y-remaining",
                 "stage05z-comparison","stage05z-audit"):
        p.add_argument("--"+name,type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    names=("stage05o_utc","stage05o_native_hold","stage05y_evidence",
           "stage05y_summary","stage05y_remaining","stage05z_comparison",
           "stage05z_audit","out_dir")
    if any(getattr(a,n) is None for n in names):
        p.error("Require all original Stage05O/Y/Z read-only inputs and fresh output dir")
    registry=original_registry(tsv(a.stage05o_utc),tsv(a.stage05o_native_hold))
    prior=verify_05y(tsv(a.stage05y_evidence),js(a.stage05y_summary),registry)
    new=verify_05z(tsv(a.stage05z_comparison),js(a.stage05z_audit),registry)
    allrows=sorted(prior+new,key=lambda r:(r["site"],r["native_JST_halfhour_start"],r["variable"]))
    keys={(r["site"],r["native_JST_halfhour_start"],r["variable"]) for r in allrows}
    if len(allrows)!=16 or len(keys)!=16 or len({(s,t) for s,t,v in keys})!=11:
        raise ValueError("Combined 16 fields / 11 original site×native halfhours changed")
    remaining_utc=set(registry)-keys
    if len(remaining_utc)!=11 or Counter(s for s,t,v in remaining_utc)!=Counter({"JP-Fjy":3,"JP-Khw":3,"JP-Yms":5}):
        raise ValueError("11 remaining UTC-verified source anomalies differ")
    outstanding=six_days(js(a.stage05y_remaining))
    if a.out_dir.exists():p.error("New output directory required; never overwrite reports")
    a.out_dir.mkdir(parents=True)
    evidence=a.out_dir/"stage05aa_16_JPF_source_fields_ERA5L_context_HOLD.tsv"
    six=a.out_dir/"stage05aa_6_remaining_CDS_site_UTC_days_PREVIEW_ONLY.json"
    summary=a.out_dir/"stage05aa_45_source_field_independent_evidence_portfolio.json"
    with evidence.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=OUT_FIELDS,delimiter="\t")
        writer.writeheader();writer.writerows(allrows)
    with six.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05AA","status":"SIX_FUTURE_SITE_DAYS_PREVIEW_ONLY",
            "source_days_with_validated_CDS_style_hourly_contents":3,
            "observed_CDS_successful_request_logs":2,
            "third_day_original_archive_preexisting":True,
            "third_day_original_request_id":"NOT_AVAILABLE",
            "remaining_site_day_count":6,
            "remaining":outstanding,
            "CDS_requests_by_this_stage":0,"model_forcing_modified":False
        },f,indent=2,ensure_ascii=False);f.write("\n")
    cov={
       "stage":"JapanFlux Stage05AA",
       "status":"SIXTEEN_SOURCE_QC2_CONTEXT_ERRORS_EVIDENCED_NOT_APPROVED_FOR_REPAIR",
       "original_source_HOLD_fields":45,
       "independent_hourly_context_supported_fields":16,
       "independent_context_supported_site_native_halfhours":11,
       "supported_fields_by_site":{"JP-Fjy":3,"JP-Khw":8,"JP-Yms":5},
       "UTC_verified_source_fields_pending_independent_reference":11,
       "original_solar_time_clock_HOLD_fields":18,
       "source_reference_site_UTC_days_with_payloads_validated":3,
       "CDS_request_success_logs_observed_for_two_site_days":True,
       "JP_Fjy_preexisting_ZIP_has_observed_original_CDS_request_log":False,
       "JP_Fjy_preexisting_original_ZIP_SHA256":JPF_ZIP_SHA,
       "remaining_CDS_site_days_not_yet_verified":6,
       "source_grid_elevation_for_Fjy":"NOT_VERIFIED",
       "half_hour_replacement_values_approved":False,
       "original_source_ZIP_or_forcing_modified":False,
       "CDS_requests_this_stage":0,"Slurm_jobs_this_stage":0,
       "all_45_original_source_fields_HOLD":True,
       "next_recommended_single_CDS_day":"JP-Fjy 2011-12-16 UTC, pressure only; check previous files first",
       "input_sha256":{n:sha(getattr(a,n)) for n in names if n!="out_dir"}
    }
    with summary.open("x",encoding="utf-8") as f:
        json.dump(cov,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AA 16-FIELD EXTERNAL ERA5L CONTEXT EVIDENCE MERGE PASS | NO CDS / SLURM / REPAIR")
    print("SOURCE_FIELDS_WITH_STRONG_INDEPENDENT_CONTEXT",16,"/45")
    print("BY_SITE",cov["supported_fields_by_site"],
          "DISTINCT_ORIGINAL_SITE_HALF_HOURS",cov["independent_context_supported_site_native_halfhours"])
    print("FJY_REQUEST_LOG_PROVENANCE","PREEXISTING_ZIP_ONLY_NO_ORIGINAL_CDS_SUBMISSION_LOG")
    print("OTHER_UTC_VERIFIED_FIELDS_PENDING",11,"CLOCK_CONFLICT_FIELDS_HOLD",18)
    print("CDS_SITE_DAYS_WITH_VERIFIED_CONTENT",3,
          "SUCCESSFUL_REQUEST_LOGS_OBSERVED",2,"REMAINING_DAYS",len(outstanding))
    for r in outstanding:
        print("CDS_STILL_PENDING",r["site"],r["UTC_day"],
              "VARIABLES",",".join(r["variable_scope"]))
    print("UNIFIED_16_FIELD_SOURCE_EVIDENCE",evidence)
    print("SIX_REMAINING_SOURCE_GATED_DAYS",six)
    print("SCIENCE_COVERAGE_SUMMARY",summary)
    print("ALL_45_SOURCE_QC2_FIELDS_STILL_HOLD_NO_APPROVED_REPAIR")
if __name__=="__main__":
    main()

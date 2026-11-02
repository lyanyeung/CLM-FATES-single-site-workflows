#!/usr/bin/env python3
"""JapanFlux Stage05Y: merge actual JP-Khw 8 + JP-Yms 5 independently evidenced anomalies.

Provenance-gated evidence registry, 7 remaining CDN/CDS site×UTC-day request PREVIEW.
Inputs: original Stage05O QC2 source registry (27 UTC+18 native time HOLD);
actual Stage05V original source-vs-independent 8 evidence/summary and 8 pending days;
actual Stage05X 5 source-vs-independent evidence/summary;
actual Stage05W2 CDS 936-byte ZIP audit.
Only report derived records. NO CDS/ZIP reads, Slurm, forcing/model edits,
automatic interpolation, pressure elevation adjustment or scientific repair approval.
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

CDS_KHW="111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0"
CDS_YMS="4bf228a3a53ab7fc6751b8e7438fb459570536ce6f54af2f81de5afc083b59d5"
EXPECTED_13={
    ("JP-Khw","200508120200","LW_IN"),
    ("JP-Khw","200508120230","LW_IN"),
    ("JP-Khw","200508120230","PA"),
    ("JP-Khw","200508120230","TA"),
    ("JP-Khw","200508120300","PA"),
    ("JP-Khw","200508120300","TA"),
    ("JP-Khw","200508120330","PA"),
    ("JP-Khw","200508120330","TA"),
    ("JP-Yms","200508120200","LW_IN"),
    ("JP-Yms","200508120230","LW_IN"),
    ("JP-Yms","200508120230","PA"),
    ("JP-Yms","200508120300","PA"),
    ("JP-Yms","200508120330","PA"),
}
BY_SOURCE_SITE=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
BY_PENDING_SITE=Counter({"JP-Tef":4,"JP-Tmd":14})
NATIVE_ONLY_STATUS="HOLD_LOCAL_SOLAR_VS_STANDARD_TIME_PROVENANCE"
SOURCE_STATUS="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"
SOURCE_UNITS={"TA":"deg C","PA":"kPa","LW_IN":"W m-2"}
INDEPENDENT_UNITS={"TA":"degC","PA":"kPa","LW_IN":"W m-2 hourly mean"}
COLS=("site","native_JST_halfhour_start","UTC_halfhour_start","variable",
      "original_JPF_F","source_same_release_ERA","source_QC","source_units",
      "independent_CDS_ZIP_SHA256","independent_hourly_context_min",
      "independent_hourly_context_max","independent_reference_units",
      "minimum_gap_to_hourly_context","context_outside","evidence_label",
      "repair_status","time_grid_and_representativeness_limit")
EXPECTED_REMAINING={
    ("JP-Fjy","2005-08-11"),("JP-Fjy","2011-12-16"),("JP-Fjy","2011-12-17"),
    ("JP-Khw","2011-12-16"),("JP-Khw","2011-12-17"),
    ("JP-Yms","2011-12-16"),("JP-Yms","2011-12-17"),
}

def read_tsv(path:Path)->list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or len(rd.fieldnames)!=len(set(rd.fieldnames)):
            raise ValueError("Missing or duplicate source headers")
        rows=list(rd)
    if not rows:raise ValueError("Empty source TSV: "+str(path))
    return rows

def read_json(path:Path)->dict:
    d=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict):raise ValueError("Source JSON must be an object")
    return d

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b=f.read(1024*1024)
            if not b:break
            h.update(b)
    return h.hexdigest()

def base_source(mappable:list[dict], native:list[dict], meta:dict)->dict:
    if (len(mappable)!=27 or len(native)!=18
        or Counter(r["site"] for r in mappable)!=BY_SOURCE_SITE
        or Counter(r["site"] for r in native)!=BY_PENDING_SITE
        or meta.get("stage")!="JapanFlux Stage05O"
        or meta.get("status")!="3_SITE_SCOPED_UTC_ONLY"
        or meta.get("mapped_field_records")!=27
        or meta.get("mapped_unique_site_halfhours")!=21
        or meta.get("unresolved_field_records")!=18
        or meta.get("unresolved_unique_site_halfhours")!=14
        or meta.get("total_field_records")!=45
        or meta.get("total_unique_site_halfhours")!=35
        or meta.get("repair_approved") is not False
        or meta.get("original_source_or_model_modified") is not False):
        raise ValueError("Original Stage05O 45 source-field science gate not met")
    indexed={}; native_keys=set()
    for r in mappable:
        k=(r["site"],r["native_start"],r["variable"])
        if k in indexed or r["variable"] not in SOURCE_UNITS:
            raise ValueError("Duplicate or unexpected original UTC source field")
        if r["raw_F_QC"]!="2" or r["source_status"]!=SOURCE_STATUS:
            raise ValueError("Source QC2/HOLD gate changed")
        if r["unit"]!=SOURCE_UNITS[r["variable"]]:
            raise ValueError("Original BIF source units changed")
        src=float(r["selected_F"]);embedded=float(r["ERA_in_same_release"])
        if not all(math.isfinite(v) for v in (src,embedded)) or not math.isclose(src,embedded,rel_tol=1e-12,abs_tol=1e-9):
            raise ValueError("Original source selected F no longer equals same-release ERA")
        native_dt=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc_dt=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        if native_dt-utc_dt!=timedelta(hours=9):
            raise ValueError("Original verified local-standard-time/UTC+9 source join changed")
        indexed[k]=r
    for r in native:
        k=(r["site"],r["native_start"],r["variable"])
        if k in native_keys or k in indexed or r["variable"] not in SOURCE_UNITS:
            raise ValueError("Duplicate/unexpected native-only HOLD field")
        native_keys.add(k)
        if (r["raw_F_QC"]!="2" or r["source_status"]!=NATIVE_ONLY_STATUS
            or r["utc_start"]!="UNRESOLVED"):
            raise ValueError("Original solar-time ambiguity may not be silently UTC resolved")
    if len({(k[0],k[1]) for k in indexed})!=21 or len({(k[0],k[1]) for k in native_keys})!=14:
        raise ValueError("Source site×native halfhour numbers changed")
    return indexed

def check_evidence_meta(v:dict,x:dict,w:dict)->None:
    if (v.get("stage")!="JapanFlux Stage05V"
        or v.get("status")!="JP_KHW_8_OF_8_STRONG_INDEPENDENT_SOURCE_DEFECT_EVIDENCE_NOT_REPAIR"
        or v.get("original_source_fields_reviewed")!=8
        or v.get("other_source_HOLD_fields")!=37
        or v.get("total_original_HOLD_fields")!=45
        or v.get("science_repair_approved") is not False
        or x.get("stage")!="JapanFlux Stage05X"
        or x.get("status")!="READONLY_SOURCE_QC2_VS_SEPARATELY_RETRIEVED_CDS_HOURLY_CONTEXT"
        or x.get("site")!="JP-Yms" or x.get("UTC_date")!="2005-08-11"
        or x.get("source_fields_on_checked_UTC_day")!=5
        or x.get("source_unique_halfhour_times")!=4
        or x.get("source_variable_counts")!={"LW_IN":2,"PA":3}
        or x.get("fields_outside_independent_3hour_context")!=5
        or x.get("independently_downloaded_CDS_original_ZIP_SHA256")!=CDS_YMS
        or x.get("scientific_half_hour_repair_approved") is not False
        or x.get("original_45_source_fields_status")!="ALL_HOLD"
        or w.get("stage")!="JapanFlux Stage05W2"
        or w.get("status")!="PASS_SOURCE_SPARSE_HOURS_AND_SECOND_REAL_CDS_ZIP"
        or w.get("raw_CDS_ZIP_SHA256")!=CDS_YMS
        or w.get("hourly_independent_variable_records")!=48
        or w.get("source_specific_scope",{}).get("source_variable_hour_pairs")!=17
        or w.get("CDS_calls_this_stage")!=0
        or w.get("half_hour_replacement_approved") is not False
        or w.get("all_45_JPF_original_flagged_fields_HOLD") is not True):
        raise ValueError("Original Stage05V/05X/05W2 independent evidence science-HOLD gate mismatch")

def unified(v_rows:list[dict],x_rows:list[dict],source:dict)->list[dict]:
    if len(v_rows)!=8 or len(x_rows)!=5:
        raise ValueError("Require exact actual 8+5 source fields")
    evidence={};seen=set()
    for origin, rows in (("STAGE05V_JP_KHW",v_rows),("STAGE05X_JP_YMS",x_rows)):
        for r in rows:
            site=r["site"]
            native=r["source_native_start_JST"] if origin.startswith("STAGE05V") else r["native_start_JST"]
            var=r["variable"]
            key=(site,native,var)
            if key in seen or key not in EXPECTED_13 or key not in source:
                raise ValueError("Unknown/duplicate original source candidate: "+repr(key))
            seen.add(key)
            original=source[key]
            src=float(r["JPF_selected_F"] if origin.startswith("STAGE05V") else r["original_F"])
            internal=float(r["same_release_ERA"] if origin.startswith("STAGE05V") else r["original_same_release_ERA"])
            reference_min=float(r["independent_hourly_context_min"] if origin.startswith("STAGE05V") else r["independent_context_min"])
            reference_max=float(r["independent_hourly_context_max"] if origin.startswith("STAGE05V") else r["independent_context_max"])
            if not all(math.isfinite(t) for t in (src,internal,reference_min,reference_max)):
                raise ValueError("Nonfinite original or independent values")
            if reference_min>reference_max or not math.isclose(src,internal,rel_tol=1e-12,abs_tol=1e-9):
                raise ValueError("Source JPF selected F vs same-release ERA comparison invalid")
            if not math.isclose(src,float(original["selected_F"]),rel_tol=1e-12,abs_tol=1e-9):
                raise ValueError("Stage05O actual original F values conflict with evidence")
            if (not math.isclose(internal,float(original["ERA_in_same_release"]),rel_tol=1e-12,abs_tol=1e-9)
                or original["raw_F_QC"]!="2"):
                raise ValueError("Original source F=ERA+QC2 gate mismatch")
            source_utc=original["utc_start"]
            formatted=datetime.strptime(source_utc,"%Y%m%d%H%M").strftime("%Y-%m-%dT%H:%MZ")
            actual_utc=(r["source_UTC_start"] if origin.startswith("STAGE05V") else r["UTC_start"])
            if actual_utc!=formatted:
                raise ValueError("Original native-to-UTC provenance differs from evidence")
            if origin.startswith("STAGE05V"):
                if (site!="JP-Khw" or r["original_F_QC"]!="2"
                    or r["repair_status"]!="HOLD_NOT_APPROVED_DO_NOT_WRITE_FORCING"):
                    raise ValueError("Stage05V original source or repair status mismatch")
                units=r["independent_hourly_context_units"]
                label=r["evidence_strength"]
                reported_distance=float(r["minimum_distance_to_context_interval"])
                original_units=source[key]["unit"]
                zipsha=CDS_KHW
            else:
                if (site!="JP-Yms" or r["original_F_QC"]!="2"
                    or r["original_outside_hourly_context_range"]!="1"
                    or r["source_and_model_status"]!="ORIGINAL_QC2_HOLD_NO_HALF_HOUR_INTERPOLATION_NO_FORCING_WRITES"
                    or r["science_qualification"]!="STRONG_CONTEXTUAL_INCONSISTENCY_PENDING_PHYSICS_REVIEW"):
                    raise ValueError("Stage05X source status/candidate classification changed")
                units=r["independent_reference_units"]
                label=r["science_qualification"]
                reported_distance=float(r["minimum_abs_gap_to_hourly_context"])
                original_units=r["original_units"]
                zipsha=CDS_YMS
            if original_units!=SOURCE_UNITS[var] or units!=INDEPENDENT_UNITS[var]:
                raise ValueError("Original and independent reference source units not equivalent")
            if not (src<reference_min or src>reference_max):
                raise ValueError("Original source no longer outside independent nearby-hour range")
            gap=reference_min-src if src<reference_min else src-reference_max
            if not math.isclose(gap,reported_distance,rel_tol=1e-6,abs_tol=1e-5):
                raise ValueError("Independent context gap disagrees with Stage05V/X")
            evidence[key]={
                "site":site,"native_JST_halfhour_start":native,
                "UTC_halfhour_start":formatted,"variable":var,
                "original_JPF_F":original["selected_F"],
                "source_same_release_ERA":original["ERA_in_same_release"],
                "source_QC":"2","source_units":original_units,
                "independent_CDS_ZIP_SHA256":zipsha,
                "independent_hourly_context_min":reference_min,
                "independent_hourly_context_max":reference_max,
                "independent_reference_units":units,
                "minimum_gap_to_hourly_context":round(gap,6),
                "context_outside":1,"evidence_label":label,
                "repair_status":"SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT",
                "time_grid_and_representativeness_limit":(
                    "Original 30min source vs independent nearest-grid ERA5L hourly values, "
                    "grid elevation and radiation accumulation interval not harmonized")
            }
    if set(evidence)!=EXPECTED_13:
        raise ValueError("Combined independently evidenced 13 original source variable keys differ")
    unique_times={(s,t) for s,t,v in evidence}
    if len(unique_times)!=8 or Counter(k[0] for k in evidence)!=Counter({"JP-Khw":8,"JP-Yms":5}):
        raise ValueError("Combined 13 field / 8 site-native-halfhour scope changed")
    return [evidence[k] for k in sorted(evidence)]

def remaining_request_plan(old:dict)->list[dict]:
    if (old.get("stage")!="JapanFlux Stage05V"
        or old.get("status")!="NO_SUBMISSIONS_EIGHT_DAYS_PREVIEW_ONLY"
        or old.get("remaining_count")!=8
        or old.get("independent_CDS_requests_this_stage")!=0
        or old.get("model_forcing_changes") is not False):
        raise ValueError("Require original Stage05V 8 not-yet-requested preview")
    entries=old["remaining_site_day_requests"]
    if len(entries)!=8 or len({(r["site"],r["utc_day"]) for r in entries})!=8:
        raise ValueError("Original Stage05V pending date keys ambiguous")
    yms=("JP-Yms","2005-08-11")
    oldset={(r["site"],r["utc_day"]) for r in entries}
    if yms not in oldset or oldset-{yms}!=EXPECTED_REMAINING:
        raise ValueError("Unexpected Stage05V original remaining date scope")
    remaining=[]
    for row in entries:
        if (row["site"],row["utc_day"])==yms:
            continue
        if (row["CDS_dataset"]!="reanalysis-era5-land-timeseries"
            or not row["requested_source_UTC_hours"]
            or not row["variable_scope"]):
            raise ValueError("Stage05V source constrained date request changed")
        remaining.append({
            "site":row["site"],"UTC_day":row["utc_day"],
            "source_BIF_SHA256":row["source_bif_sha256"],
            "original_tower_coordinates":row["original_tower_coordinates"],
            "variable_scope":row["variable_scope"],
            "source_UTC_hours":row["requested_source_UTC_hours"],
            "CDS_dataset":"reanalysis-era5-land-timeseries",
            "status":"NOT_REPORTED_AS_DOWNLOADED_IN_OPERATOR_STAGE05X_LOG_NO_ACTION_THIS_STAGE"
        })
    return sorted(remaining,key=lambda r:(r["site"],r["UTC_day"]))

def self_test():
    assert len(EXPECTED_13)==13
    assert len({(s,t) for s,t,v in EXPECTED_13})==8
    assert len(EXPECTED_REMAINING)==7
    assert 13+14+18==45
    assert Counter(s for s,t,v in EXPECTED_13)==Counter({"JP-Khw":8,"JP-Yms":5})
    print("STAGE05Y SELF-TEST PASS | 8+5=13 original QC2 fields, 7 remaining CDS site-days, all 45 HOLD; NO WRITES")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    for name in ("stage05o-utc","stage05o-native-hold","stage05o-summary",
                 "stage05v-evidence","stage05v-summary","stage05v-remaining",
                 "stage05x-evidence","stage05x-summary","stage05w2-audit"):
        ap.add_argument("--"+name,type=Path,required=False)
    ap.add_argument("--out-dir",type=Path)
    a=ap.parse_args()
    if a.self_test:
        self_test();return
    attrs=("stage05o_utc","stage05o_native_hold","stage05o_summary",
           "stage05v_evidence","stage05v_summary","stage05v_remaining",
           "stage05x_evidence","stage05x_summary","stage05w2_audit","out_dir")
    if any(getattr(a,name) is None for name in attrs):
        ap.error("Require all source Stage05O/V/X/W2 documents and fresh --out-dir")
    source=base_source(read_tsv(a.stage05o_utc),
                       read_tsv(a.stage05o_native_hold),read_json(a.stage05o_summary))
    meta_v=read_json(a.stage05v_summary);meta_x=read_json(a.stage05x_summary)
    audit_w2=read_json(a.stage05w2_audit)
    check_evidence_meta(meta_v,meta_x,audit_w2)
    evidence=unified(read_tsv(a.stage05v_evidence),read_tsv(a.stage05x_evidence),source)
    outstanding=remaining_request_plan(read_json(a.stage05v_remaining))
    future_keys=set(source)-EXPECTED_13
    if len(future_keys)!=14 or Counter(s for s,t,v in future_keys)!=Counter({"JP-Fjy":6,"JP-Khw":3,"JP-Yms":5}):
        raise ValueError("14 unreviewed but UTC-verified original QC2 fields changed")
    if a.out_dir.exists():
        ap.error("No output overwrite permitted; choose new report directory")
    a.out_dir.mkdir(parents=True)
    t=a.out_dir/"stage05y_13_source_fields_independent_CDS_context_HOLD.tsv"
    o=a.out_dir/"stage05y_7_remaining_CDS_site_UTC_days_PREVIEW_ONLY.json"
    s=a.out_dir/"stage05y_45_source_field_science_coverage_summary.json"
    with t.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=COLS,delimiter="\t")
        w.writeheader();w.writerows(evidence)
    with o.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05Y","status":"SEVEN_UNREQUESTED_SITE_DAYS_PREVIEW_ONLY",
                   "completed_site_days_as_observed":[
                       {"site":"JP-Khw","UTC_day":"2005-08-11","raw_CDS_ZIP_SHA256":CDS_KHW},
                       {"site":"JP-Yms","UTC_day":"2005-08-11","raw_CDS_ZIP_SHA256":CDS_YMS}],
                   "remaining_count":7,"remaining":outstanding,
                   "CDS_downloads_this_stage":0,"source_or_model_changes":False},f,indent=2)
        f.write("\n")
    outmeta={
        "stage":"JapanFlux Stage05Y",
        "status":"THIRTEEN_SOURCE_FIELDS_STRONGLY_CONTRADICTED_BY_SEPARATE_ERA5L_CONTEXT_NOT_REPAIRED",
        "original_source_total_HOLD_fields":45,
        "independently_evidenced_source_fields":13,
        "independently_evidenced_unique_site_halfhours":8,
        "independent_CDS_site_days_downloaded":2,
        "independent_CDS_site_days_not_yet_downloaded":7,
        "UTC_verified_fields_not_yet_independently_compared":14,
        "unresolved_solar_vs_standard_time_source_fields":18,
        "independently_evidenced_site_fields":{"JP-Khw":8,"JP-Yms":5},
        "UTC_unverified_original_sites":["JP-Tef","JP-Tmd"],
        "remaining_UTC_verified_by_site":{"JP-Fjy":6,"JP-Khw":3,"JP-Yms":5},
        "independent_reference_CDS_ZIP_SHA256_by_site_day":{
            "JP-Khw:2005-08-11":CDS_KHW,"JP-Yms:2005-08-11":CDS_YMS},
        "no_repair_value_approved":True,
        "no_CD_Scalls":True,"no_original_ZIP_read":True,
        "no_forcing_or_model_write":True,"no_Slurm":True,
        "input_sha256":{name:sha256(getattr(a,name)) for name in attrs if name!="out_dir"},
        "next_recommended_site_day":"JP-Fjy 2005-08-11 (surface_pressure; third source-verified site)",
        "note":"Independent hourly nearest-grid physics supports gross source defects, not scientifically approved half-hour replacements. All original 45 records remain source HOLD."
    }
    with s.open("x",encoding="utf-8") as f:
        json.dump(outmeta,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05Y 13-FIELD INDEPENDENT CDS EVIDENCE MERGE PASS | NO CDS / ZIP / SLURM / REPAIR")
    print("INDEPENDENTLY_EVIDENCED",len(evidence),"/45 ORIGINAL_QC2_FIELDS")
    print("EVIDENCED_BY_SITE",dict(Counter(r["site"] for r in evidence)))
    print("EVIDENCED_UNIQUE_SITE_HALF_HOURS",outmeta["independently_evidenced_unique_site_halfhours"])
    print("UTC_VERIFIED_NOT_YET_COMPARED",len(future_keys),"TIME_BASIS_HOLD",18)
    print("CDS_DOWNLOADED_SITE_DAYS",2,"REMAINING_SITE_DAYS",len(outstanding))
    for row in outstanding:
        print("CDS_REMAINING",row["site"],row["UTC_day"],
              "VARIABLES",",".join(row["variable_scope"]))
    print("MERGED_SOURCE_EVIDENCE",t)
    print("REMAINING_CDS_PREVIEW",o)
    print("SOURCE_COVERAGE_SUMMARY",s)
    print("ALL_45_SOURCE_QC2_FIELDS_HOLD; NO SCIENTIFICALLY_APPROVED_REPLACEMENT VALUES")

if __name__=="__main__":
    main()

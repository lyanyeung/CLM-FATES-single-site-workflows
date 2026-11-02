#!/usr/bin/env python3
"""Stage05AE: merge 16 source-backed context fields + 3 Dec-2011 JP-Fjy PA.

Strict read-only provenance: original Stage05O 27 UTC+9 QC2 source rows and
18 unresolved native-time holds; Stage05AA original 16-field evidence/6-day
scope/summary; Stage05AD actual 3-field cross-UTC-midnight source contexts;
latest Stage05AB inventory containing 2 verified Fjy Dec days and 4 absent
Khw/Yms dates. Output 19-field HOLD register and 4-day pending PREVIEW.
No CDS/API, ZIP, original forcing, Slurm, model, interpolation or repair.
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

BIF_FJY="b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62"
SHA16="cc172d7c18e7b7b5199aa7cccc8b941c6115863861860f0618d8b33d4f577c9a"
SHA17="f553e574a72e409c988460f7052100496c264321a65a46e5a80a636982d3deed"
FJY_DAYS=("2011-12-16","2011-12-17")
FJY_KEYS={
 ("JP-Fjy","201112170630","PA"),
 ("JP-Fjy","201112170700","PA"),
 ("JP-Fjy","201112170730","PA")
}
PENDING_DAYS={
 ("JP-Khw","2011-12-16"),("JP-Khw","2011-12-17"),
 ("JP-Yms","2011-12-16"),("JP-Yms","2011-12-17")
}
COUNTS=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
OUT_FIELDS=("site","native_JST_halfhour_start","UTC_halfhour_start","variable",
            "original_JPF_F","source_same_release_ERA","source_QC","source_units",
            "independent_CDS_ZIP_SHA256","reference_provenance_class",
            "independent_hourly_context_min","independent_hourly_context_max",
            "independent_reference_units","minimum_gap_to_hourly_context",
            "context_outside","evidence_label","repair_status",
            "time_grid_and_representativeness_limit")

def read_tsv(path:Path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or len(set(rd.fieldnames))!=len(rd.fieldnames):
            raise ValueError("Original file has missing/duplicate TSV header")
        rows=list(rd)
    if not rows:
        raise ValueError("Original source TSV was empty")
    return rows

def read_json(path:Path):
    d=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict):raise ValueError("Expected actual source JSON object")
    return d

def sha256(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def source_registry(rows,native):
    if len(rows)!=27 or Counter(r["site"] for r in rows)!=COUNTS:
        raise ValueError("Original 27 UTC-mapped QC2 source field scope changed")
    if (len(native)!=18 or Counter(r["site"] for r in native)
        !=Counter({"JP-Tef":4,"JP-Tmd":14})):
        raise ValueError("Original native-only clock-ambiguous 18 field scope changed")
    src={}; clock=set()
    for r in rows:
        k=r["site"],r["native_start"],r["variable"]
        if k in src or r["variable"] not in ("PA","LW_IN","TA"):
            raise ValueError("Duplicate or unexpected original JPF field")
        t=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        u=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        a=float(r["selected_F"]);b=float(r["ERA_in_same_release"])
        if (t-u!=timedelta(hours=9)
            or r["raw_F_QC"]!="2"
            or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"
            or not all(math.isfinite(q) for q in (a,b))
            or not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9)):
            raise ValueError("Original JPF selected F / ERA / QC2 / UTC+9 science provenance changed")
        src[k]=r
    for r in native:
        k=r["site"],r["native_start"],r["variable"]
        if (k in src or k in clock
            or r["raw_F_QC"]!="2"
            or r["utc_start"]!="UNRESOLVED"
            or r["source_status"]!="HOLD_LOCAL_SOLAR_VS_STANDARD_TIME_PROVENANCE"):
            raise ValueError("Original JP-Tef/Tmd clock conflict may not be resolved silently")
        clock.add(k)
    if len({(s,t) for s,t,v in src})!=21 or len({(s,t) for s,t,v in clock})!=14:
        raise ValueError("Original site native time counts changed")
    return src

def verify_prior(rows,summary,registry):
    if (summary.get("stage")!="JapanFlux Stage05AA"
        or summary.get("status")!="SIXTEEN_SOURCE_QC2_CONTEXT_ERRORS_EVIDENCED_NOT_APPROVED_FOR_REPAIR"
        or summary.get("original_source_HOLD_fields")!=45
        or summary.get("independent_hourly_context_supported_fields")!=16
        or summary.get("independent_context_supported_site_native_halfhours")!=11
        or summary.get("UTC_verified_source_fields_pending_independent_reference")!=11
        or summary.get("original_solar_time_clock_HOLD_fields")!=18
        or summary.get("remaining_CDS_site_days_not_yet_verified")!=6
        or summary.get("half_hour_replacement_values_approved") is not False
        or summary.get("all_45_original_source_fields_HOLD") is not True):
        raise ValueError("Actual Stage05AA 16 original fields provenance invalid")
    if len(rows)!=16 or Counter(r["site"] for r in rows)!=Counter({"JP-Fjy":3,"JP-Khw":8,"JP-Yms":5}):
        raise ValueError("Stage05AA actual 16 original fields unexpectedly changed")
    keys=set()
    for r in rows:
        key=r["site"],r["native_JST_halfhour_start"],r["variable"]
        if key in keys or key not in registry or key in FJY_KEYS:
            raise ValueError("Stage05AA original source candidate unknown/overlapping new three")
        keys.add(key)
        orig=registry[key]
        src=float(r["original_JPF_F"])
        internal=float(r["source_same_release_ERA"])
        lo=float(r["independent_hourly_context_min"])
        hi=float(r["independent_hourly_context_max"])
        if (r["source_QC"]!="2" or r["context_outside"]!="1"
            or r["repair_status"]!="SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT"
            or r["source_units"]!=orig["unit"]
            or r["UTC_halfhour_start"]!=datetime.strptime(orig["utc_start"],"%Y%m%d%H%M").strftime("%Y-%m-%dT%H:%MZ")
            or not math.isclose(src,float(orig["selected_F"]),rel_tol=1e-12,abs_tol=1e-9)
            or not math.isclose(internal,float(orig["ERA_in_same_release"]),rel_tol=1e-12,abs_tol=1e-9)
            or not (lo<=hi and (src<lo or src>hi))):
            raise ValueError("Original source/independent evidence science gate fails")
    if len({(s,t) for s,t,v in keys})!=11:
        raise ValueError("Stage05AA distinct original source half-hour count changed")
    return keys

def verify_2011(adrows,adsummary,registry):
    if (adsummary.get("stage")!="JapanFlux Stage05AD"
        or adsummary.get("status")!="SOURCE_VERIFIED_JP_FJY_2011_TWO_DAY_HOURLY_PA_CONTEXT_NO_REPAIR"
        or adsummary.get("site")!="JP-Fjy"
        or adsummary.get("UTC_days")!=list(FJY_DAYS)
        or adsummary.get("source_original_QC2_fields")!=3
        or adsummary.get("source_candidate_distinct_native_halfhours")!=3
        or adsummary.get("source_PA_fields_outside_independent_hourly_range")!=3
        or adsummary.get("CDS_validated_independent_hourly_pressure_count")!=48
        or adsummary.get("CDS_response_original_SHA256_by_UTC_day")
           !={FJY_DAYS[0]:SHA16,FJY_DAYS[1]:SHA17}
        or adsummary.get("CDS_grid_elevation")!="NOT_VERIFIED"
        or adsummary.get("scientific_repair_values_approved") is not False
        or adsummary.get("all_45_original_JPF_source_QC2_fields_HOLD") is not True
        or adsummary.get("CDS_requests_this_stage")!=0):
        raise ValueError("Stage05AD actual 48-hour science QC2 source provenance changed")
    if len(adrows)!=3:return fail("Expected exactly 3 actual 2011 JP-Fjy PA events")
    seen=set();out=[]
    for r in adrows:
        k=r["site"],r["original_JST_halfhour_start"],r["variable"]
        if k not in FJY_KEYS or k in seen or k not in registry:
            raise ValueError("Stage05AD unknown/duplicate original JPF source field")
        seen.add(k)
        source=registry[k]
        x=float(r["original_JPF_F_kPa"])
        y=float(r["same_release_original_ERA_kPa"])
        vals=[float(v) for v in r["hourly_ERA5L_pressures_kPa"].split(";")]
        utc=datetime.strptime(source["utc_start"],"%Y%m%d%H%M")
        expected_times=[(utc.replace(minute=0)+timedelta(hours=j)).strftime("%Y-%m-%dT%H:%MZ") for j in range(3)]
        times=r["hourly_ERA5L_valid_times_UTC"].split(";")
        if len(vals)!=3 or not all(math.isfinite(v) for v in vals) or times!=expected_times:
            raise ValueError("Stage05AD independent source hour alignment differs")
        lo=min(vals);hi=max(vals)
        distance=lo-x if x<lo else x-hi if x>hi else 0.0
        if (r["original_F_QC"]!="2" or source["unit"]!="kPa"
            or not math.isclose(x,float(source["selected_F"]),rel_tol=1e-12,abs_tol=1e-9)
            or not math.isclose(y,float(source["ERA_in_same_release"]),rel_tol=1e-12,abs_tol=1e-9)
            or r["derived_UTC_start"]!=utc.strftime("%Y-%m-%dT%H:%MZ")
            or not math.isclose(lo,float(r["hourly_ERA5L_context_min_kPa"]),abs_tol=1e-6)
            or not math.isclose(hi,float(r["hourly_ERA5L_context_max_kPa"]),abs_tol=1e-6)
            or not math.isclose(distance,float(r["minimum_distance_to_context_kPa"]),abs_tol=1e-6)
            or r["outside_independent_hourly_context"]!="1" or not (x<lo or x>hi)
            or r["science_status"]!="HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR"
            or r["grid_elevation_status"]!="UNKNOWN_1043M_TOWER_GRID_HEIGHT_REPRESENTATIVENESS_NOT_APPROVED"):
            raise ValueError("Stage05AD QC2/source/independent-hour science HOLD gate failed")
        out.append({
            "site":"JP-Fjy","native_JST_halfhour_start":r["original_JST_halfhour_start"],
            "UTC_halfhour_start":r["derived_UTC_start"],"variable":"PA",
            "original_JPF_F":source["selected_F"],
            "source_same_release_ERA":source["ERA_in_same_release"],
            "source_QC":"2","source_units":"kPa",
            "independent_CDS_ZIP_SHA256":SHA16+";"+SHA17,
            "reference_provenance_class":"TWO_REAL_SUCCESSFUL_CDS_REQUEST_LOGS_AND_TWO_SHA_CRC_VERIFIED_24H_ZIPS",
            "independent_hourly_context_min":round(lo,6),
            "independent_hourly_context_max":round(hi,6),
            "independent_reference_units":"kPa",
            "minimum_gap_to_hourly_context":round(distance,6),
            "context_outside":1,"evidence_label":"SEVERE_2011_JPF_QC2_PA_INCONSISTENT_WITH_INDEPENDENT_HOURLY_CONTEXT",
            "repair_status":"SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT",
            "time_grid_and_representativeness_limit":"JP-Fjy tower BIF 1043m, independent ERA5L model grid geopotential unknown; 48-hourly context not a 30-minute direct replacement"
        })
    if seen!=FJY_KEYS:raise ValueError("Stage05AD source native time keys changed")
    return out

def verify_inventory_and_pending(inv,pending):
    if (inv.get("stage")!="JapanFlux Stage05AB"
        or inv.get("status")!="SIX_ORIGINAL_2011_DAY_PAYLOADS_READONLY_INVENTORIED"
        or inv.get("new_CDS_requests")!=0
        or inv.get("original_source_or_forcing_modified") is not False
        or inv.get("science_repair_approved") is not False
        or inv.get("original_45_source_fields_HOLD") is not True):
        raise ValueError("Stage05AB actual read-only inventory invalid")
    days=inv.get("six_site_day_inventory",[])
    if len(days)!=6 or len({(r["site"],r["UTC_day"]) for r in days})!=6:
        raise ValueError("Stage05AB six input day inventory incomplete")
    actual={(r["site"],r["UTC_day"]):r for r in days}
    checked={"JP-Fjy":{FJY_DAYS[0]:SHA16,FJY_DAYS[1]:SHA17}}
    for day,sha in checked["JP-Fjy"].items():
        r=actual["JP-Fjy",day]
        if (r["content_status"]!="COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR"
            or r["zip_inspection"]["ZIP_SHA256"]!=sha
            or r["zip_inspection"]["source_csv_members"]!=1
            or r["zip_inspection"]["independent_hourly_values_count"]!=24
            or r["files"]["PARTIAL"]["status"]!="ABSENT"):
            raise ValueError("JP-Fjy actual December source data not verified in Stage05AB")
    for k in PENDING_DAYS:
        r=actual[k]
        if (r["content_status"]!="ABSENT"
            or any(x["status"]!="ABSENT" for x in r["files"].values())):
            raise ValueError("Some December 2011 remaining date has a ZIP/partial; inventory not current")
    if (pending.get("stage")!="JapanFlux Stage05AA"
        or pending.get("status")!="SIX_FUTURE_SITE_DAYS_PREVIEW_ONLY"
        or pending.get("remaining_site_day_count")!=6
        or pending.get("CDS_requests_by_this_stage")!=0):
        raise ValueError("Source original Stage05AA six-day preview changed")
    entries=pending.get("remaining",[])
    if len(entries)!=6 or {(r["site"],r["UTC_day"]) for r in entries}!=set(actual):
        raise ValueError("Stage05AA planned six-day source scope changed")
    nextdays=[]
    for r in entries:
        if (r["site"],r["UTC_day"]) in PENDING_DAYS:
            if (r["CDS_dataset"]!="reanalysis-era5-land-timeseries"
                or not r["source_BIF_SHA256"] or not r["source_UTC_hours"]
                or set(r["variable_scope"])!=(
                   {"surface_pressure"} if r["site"]=="JP-Khw"
                   else {"surface_pressure","surface_thermal_radiation_downwards"})):
                raise ValueError("Remaining original source-selected variables/time invalid")
            nextdays.append(r)
    return sorted(nextdays,key=lambda x:(x["site"],x["UTC_day"]))

def self_test():
    assert len(FJY_KEYS)==3 and len(PENDING_DAYS)==4
    assert 16+3+8+18==45
    assert len(set((s,t) for s,t,v in FJY_KEYS))==3
    t=datetime.strptime("201112162200","%Y%m%d%H%M")
    assert (t+timedelta(hours=2)).strftime("%Y-%m-%dT%H:%MZ")=="2011-12-17T00:00Z"
    print("STAGE05AE SELF-TEST PASS | 16+3=19 source-QC2 fields, cross-midnight exact source event clocks, four pending days; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    names=("stage05o_utc","stage05o_native_hold","stage05aa_evidence",
           "stage05aa_summary","stage05aa_remaining","stage05ad_evidence",
           "stage05ad_summary","stage05ab_audit")
    for name in names:
        p.add_argument("--"+name.replace("_","-"),type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if any(getattr(a,n) is None for n in names) or a.out_dir is None:
        p.error("Need all verified Stage05O/AA/AD/AB science files and fresh out dir")
    registry=source_registry(read_tsv(a.stage05o_utc),read_tsv(a.stage05o_native_hold))
    old=read_tsv(a.stage05aa_evidence)
    oldkeys=verify_prior(old,read_json(a.stage05aa_summary),registry)
    extra=verify_2011(read_tsv(a.stage05ad_evidence),read_json(a.stage05ad_summary),registry)
    nextdays=verify_inventory_and_pending(read_json(a.stage05ab_audit),read_json(a.stage05aa_remaining))
    combined=[{field:r[field] for field in OUT_FIELDS} for r in old]+extra
    keys={(r["site"],r["native_JST_halfhour_start"],r["variable"]) for r in combined}
    if (len(oldkeys)!=16 or len(combined)!=19 or len(keys)!=19
        or Counter(s for s,t,v in keys)!=Counter({"JP-Fjy":6,"JP-Khw":8,"JP-Yms":5})
        or len({(s,t) for s,t,v in keys})!=14):
        raise ValueError("Actual combined 19 records/14 station×native time invariant failed")
    pending=set(registry)-keys
    if (len(pending)!=8 or Counter(s for s,t,v in pending)!=Counter({"JP-Khw":3,"JP-Yms":5})
        or len(nextdays)!=4):
        raise ValueError("Original remaining eight UTC-verified field/4-day scope invalid")
    if a.out_dir.exists():p.error("Fresh report directory required")
    a.out_dir.mkdir(parents=True)
    tab=a.out_dir/"stage05ae_19_JPF_source_QC2_independent_ERA5L_context_HOLD.tsv"
    four=a.out_dir/"stage05ae_4_remaining_2011_CDS_site_UTC_days_PREVIEW_ONLY.json"
    report=a.out_dir/"stage05ae_45_original_source_fields_independent_context_coverage.json"
    with tab.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,delimiter="\t",fieldnames=OUT_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(combined,key=lambda r:(r["site"],r["native_JST_halfhour_start"],r["variable"])))
    with four.open("x",encoding="utf-8") as f:
        json.dump({
            "stage":"JapanFlux Stage05AE",
            "status":"FOUR_CDS_SITE_UTC_DAYS_SOURCE_SCOPE_PREVIEW_ONLY",
            "completed_2005_and_2011_site_days_with_verified_payloads":5,
            "remaining_site_day_count":4,
            "remaining":nextdays,
            "JP_Fjy_2011_UTC_days_done":[FJY_DAYS[0],FJY_DAYS[1]],
            "CDS_requests_this_stage":0,
            "model_forcing_modified":False
        },f,indent=2,ensure_ascii=False);f.write("\n")
    summary={
        "stage":"JapanFlux Stage05AE",
        "status":"NINETEEN_ORIGINAL_SOURCE_QC2_VARIABLES_STRONGLY_INCONSISTENT_WITH_INDEPENDENT_HOURLY_ERA5L_HOLD",
        "original_source_anomaly_fields_total":45,
        "source_field_evidence_count":19,
        "distinct_original_site_native_halfhours_evidenced":14,
        "independent_context_by_site":{"JP-Fjy":6,"JP-Khw":8,"JP-Yms":5},
        "UTC_verified_original_source_fields_unreviewed":8,
        "original_native_clock_conflict_fields_HOLD":18,
        "reference_site_UTC_days_with_payloads_verified":5,
        "reference_CDS_request_logs_observed_count":4,
        "Fjy_2005_existing_payload_no_original_request_ID":True,
        "remaining_site_UTC_days_without_reference_payload":4,
        "JP_Fjy_2011_CDS_ZIP_SHA256":{"2011-12-16":SHA16,"2011-12-17":SHA17},
        "JP_Fjy_2011_grid_elevation":"NOT_VERIFIED",
        "no_replacement_value_approved":True,
        "all_45_original_field_candidates_HOLD":True,
        "CDS_requests_this_stage":0,
        "original_source_ZIP_or_forcing_changed":False,
        "Slurm_jobs":0,
        "input_SHA256":{n:sha256(getattr(a,n)) for n in names},
        "next_single_source_day":"JP-Khw 2011-12-16 UTC surface_pressure, with fresh existing-file collision check"
    }
    with report.open("x",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AE MERGED 19-FIELD INDEPENDENT ERA5L CONTEXT EVIDENCE PASS | NO CDS / SLURM / REPAIR")
    print("INDEPENDENT_PHYSICAL_CONTEXT_SOURCE_FIELDS",19,"/45",
          "BY_SITE",summary["independent_context_by_site"],
          "DISTINCT_SITE_NATIVE_HALF_HOURS",14)
    print("UTC_VERIFIED_AWAITING_EXTERNAL_CONTEXT",len(pending),
          "CLOCK_SOURCE_CONFLICT_HOLD",18)
    print("CDS_SITE_DAYS_VERIFIED",5,"PENDING_DAYS",len(nextdays))
    for r in nextdays:
        print("CDS_PENDING",r["site"],r["UTC_day"],"VARS",",".join(r["variable_scope"]))
    print("UNIFIED_19_FIELD_EVIDENCE",tab)
    print("SOURCE_SCOPED_4_DAY_REQUESTS_PREVIEW",four)
    print("SOURCE_45_FIELD_COVERAGE",report)
    print("ALL_45_SOURCE_SELECTED_F_QC2_ANOMALIES_HOLD_NO_APPROVED_REPLACEMENTS")

if __name__=="__main__":
    main()

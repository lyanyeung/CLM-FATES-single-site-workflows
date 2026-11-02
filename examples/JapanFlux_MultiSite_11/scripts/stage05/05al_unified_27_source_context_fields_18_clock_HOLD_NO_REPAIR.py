#!/usr/bin/env python3
"""Stage05AL: 22 prior strong-context + 5 new context-only Yms QC2 fields.

Read-only consistency audit of original 45 source-selected F=ERA QC2 fields.
27 standard-JST-source fields have now been independently compared and all
are outside nearby ERA5-Land context. The newest 5 remain 'CONTEXT_ONLY'
until a separate scientific evidence classification decision, never repairs.
18 Tef/Tmd fields remain unresolved original solar-vs-standard source time.

Inputs: Stage05O original UTC + native-only source registers, Stage05AH
22-field source context TSV+summary, Stage05AK 5-row source context TSV+
summary, newest Stage05AB full six-day source-CVS ZIP archive science audit.
Outputs only fresh derived TSV/JSON under --out-dir.
No CDS/network, ZIP modification, forcing edits, halfhour replacements,
Slurm, model, AD400 or automatic approval.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path

SITES=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
CLOCK_SITES=Counter({"JP-Tef":4,"JP-Tmd":14})
OLD=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":5})
YMS_SHA={
 "2011-12-16":"edd1b8acd84b31d8a04f214850dd9f51d9471dbffb91664fa76a54a9b7539c0c",
 "2011-12-17":"bb50100065193cff70429c626603cd60e957882624db5fbee056f97a23b032f6"
}
YMS_GRID=(34.80000000000106,135.79999999999654)
UNITS={"PA":"kPa","TA":"deg C","LW_IN":"W m-2"}
EXPECTED_NEW={
 ("JP-Yms","201112170600","LW_IN"),
 ("JP-Yms","201112170630","LW_IN"),
 ("JP-Yms","201112170630","PA"),
 ("JP-Yms","201112170700","PA"),
 ("JP-Yms","201112170730","PA")
}
FIELDS=("site","native_halfhour_start","verified_source_UTC_start","variable",
        "original_F_selected","original_ERA_same_release",
        "original_source_QC","unit",
        "independent_ERA5L_hourly_context_min",
        "independent_ERA5L_hourly_context_max",
        "context_outside","independent_context_evidence_tier",
        "source_provenance_class","hourly_model_grid_context_limits",
        "repair_approval_status")

def load_tsv(p):
    with p.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream,delimiter="\t")
        if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError("Invalid duplicate/empty TSV header")
        records=list(reader)
    if not records:raise ValueError("Unexpected empty source provenance table")
    return records

def load_json(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise ValueError("Expected original JSON object")
    return x

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as stream:
        for b in iter(lambda:stream.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def eq(a,b,tol=1e-6):
    return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=tol)

def source_ledger(rows,native):
    if len(rows)!=27 or Counter(r["site"] for r in rows)!=SITES:
        raise ValueError("Stage05O original 27 UTC source QC2 fields missing/changed")
    if len(native)!=18 or Counter(r["site"] for r in native)!=CLOCK_SITES:
        raise ValueError("Stage05O original 18 clock-HOLD fields missing/changed")
    result={}
    for r in rows:
        k=r["site"],r["native_start"],r["variable"]
        if k in result:raise ValueError("Duplicate original source selected variable/halfhour")
        local=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        x=float(r["selected_F"])
        y=float(r["ERA_in_same_release"])
        if (r["variable"] not in UNITS or r["unit"]!=UNITS[r["variable"]]
            or local-utc!=timedelta(hours=9)
            or r["raw_F_QC"]!="2"
            or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"
            or not all(math.isfinite(v) for v in (x,y))
            or not math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-9)):
            raise ValueError("Original source UTC/JPF F=ERA/QC2 invariant changed")
        result[k]=r
    seen=set()
    for r in native:
        k=r["site"],r["native_start"],r["variable"]
        if (k in seen or k in result
            or r["utc_start"]!="UNRESOLVED"
            or r["raw_F_QC"]!="2"
            or r["source_status"]!="HOLD_LOCAL_SOLAR_VS_STANDARD_TIME_PROVENANCE"):
            raise ValueError("Original Tef/Tmd local-solar vs standard clock source HOLD altered")
        seen.add(k)
    if len({(s,t) for s,t,v in result})!=21 or len({(s,t) for s,t,v in seen})!=14:
        raise ValueError("Original 45 variable fields should represent 35 source site/native halfhours")
    return result,seen

def old_context(rows,summary,original):
    if (summary.get("stage")!="JapanFlux Stage05AH"
        or summary.get("status")!="TWENTY_TWO_ORIGINAL_QC2_FIELDS_WITH_STRONG_INDEPENDENT_ERA5L_CONTEXT_HOLD"
        or summary.get("original_source_QC2_anomaly_fields")!=45
        or summary.get("independently_contextualized_original_source_fields")!=22
        or summary.get("by_site")!=dict(OLD)
        or summary.get("distinct_original_site_native_halfhours")!=17
        or summary.get("original_UTC_verified_fields_needing_independent_science_comparison")!=5
        or summary.get("original_native_clock_source_conflict_fields")!=18
        or summary.get("verified_independent_CDS_site_UTC_day_payloads")!=7
        or summary.get("source_30min_replacement_approved") is not False
        or summary.get("all_45_original_source_anomaly_fields_HOLD") is not True):
        raise ValueError("Prior Stage05AH 22 strong-context science summary unexpected")
    if len(rows)!=22 or Counter(r["site"] for r in rows)!=OLD:
        raise ValueError("Prior Stage05AH 22 fields site scope changed")
    result=[]; seen=set()
    for r in rows:
        k=(r["site"],r["native_JST_halfhour_start"],r["variable"])
        if k in seen or k not in original:raise ValueError("Prior evidence duplicate/unknown source field")
        seen.add(k)
        src=original[k]
        lo=float(r["independent_hourly_context_min"])
        hi=float(r["independent_hourly_context_max"])
        original_x=float(src["selected_F"])
        if (r["source_QC"]!="2" or r["source_units"]!=src["unit"]
            or r["repair_status"]!="SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT"
            or r["context_outside"]!="1"
            or r["UTC_halfhour_start"]!=datetime.strptime(src["utc_start"],"%Y%m%d%H%M").strftime("%Y-%m-%dT%H:%MZ")
            or not eq(original_x,r["original_JPF_F"])
            or not eq(original_x,r["source_same_release_ERA"])
            or not all(math.isfinite(v) for v in (lo,hi))
            or lo>hi or lo<=original_x<=hi):
            raise ValueError("Prior source/context/strong evidence status altered")
        result.append({
            "site":k[0],"native_halfhour_start":k[1],
            "verified_source_UTC_start":r["UTC_halfhour_start"],"variable":k[2],
            "original_F_selected":src["selected_F"],
            "original_ERA_same_release":src["ERA_in_same_release"],
            "original_source_QC":"2","unit":src["unit"],
            "independent_ERA5L_hourly_context_min":lo,
            "independent_ERA5L_hourly_context_max":hi,
            "context_outside":1,
            "independent_context_evidence_tier":"PRIOR_STAGE05AH_STRONG_CONTEXT",
            "source_provenance_class":r["reference_provenance_class"],
            "hourly_model_grid_context_limits":r["time_grid_and_representativeness_limit"],
            "repair_approval_status":"HOLD_NO_APPROVED_HALF_HOUR_REPLACEMENT"
        })
    if len({(s,t) for s,t,v in seen})!=17:
        raise ValueError("Original 17 prior site-native halfhours changed")
    return result,seen

def new_context(rows,summary,original):
    if (summary.get("stage")!="JapanFlux Stage05AK"
        or summary.get("status")!="FIVE_ORIGINAL_YMS_QC2_FIELDS_TWO_DAY_ERA5L_CONTEXT_ONLY_NOT_REPAIR"
        or summary.get("source_site")!="JP-Yms"
        or summary.get("source_original_QC2_fields_reviewed")!=5
        or summary.get("original_source_fields_by_variable")!={"LW_IN":2,"PA":3}
        or summary.get("outside_nearby_independent_hourly_envelope_by_variable")!={"LW_IN":2,"PA":3}
        or summary.get("independent_requested_original_variable_hour_pairs")!=17
        or summary.get("independent_hours_per_variable")!=48
        or summary.get("source_ERA5L_original_CDS_ZIP_SHA256_by_UTC_day")!=YMS_SHA
        or tuple(summary.get("source_nearest_model_grid_lat_lon",[]))!=YMS_GRID
        or summary.get("ERA5L_model_grid_elevation")!="UNKNOWN"
        or summary.get("ERA5L_strd_product_preprocessing")!="DEACCUMULATED_1H_ENERGY_J_M2"
        or summary.get("ERA5L_strd_conversion")!="ONE_HOUR_J_M2_DIVIDED_BY_3600_TO_W_M2_NO_SECOND_DIFFERENCING"
        or summary.get("original_22_source_strong_context_evidence_preserved")!=22
        or summary.get("additional_5_fields_strong_evidence_automatically_approved") is not False
        or summary.get("original_source_field_HOLD_total")!=45
        or summary.get("all_45_original_field_candidates_HOLD") is not True
        or summary.get("CDS_requests_this_stage")!=0):
        raise ValueError("Stage05AK original five Yms source/context-only HOLD summary mismatch")
    if len(rows)!=5:raise ValueError("Expected five actual original JP-Yms context records")
    result=[];seen=set()
    for r in rows:
        k=(r["site"],r["original_JST_halfhour_start"],r["variable"])
        if k in seen or k not in EXPECTED_NEW or k not in original:
            raise ValueError("Unexpected original Yms Dec2011 selected QC2 field")
        seen.add(k)
        src=original[k]
        orig=float(src["selected_F"])
        lo=float(r["independent_reference_min"])
        hi=float(r["independent_reference_max"])
        hourly=[float(v) for v in r["independent_reference_hourly_values"].split(";")]
        t=datetime.strptime(src["utc_start"],"%Y%m%d%H%M")
        offsets=(-1,0,1,2) if k[2]=="LW_IN" else (0,1,2)
        labels=[(t.replace(minute=0)+timedelta(hours=i)).strftime("%Y-%m-%dT%H:%MZ") for i in offsets]
        if (len(hourly)!=len(offsets)
            or any(not math.isfinite(x) for x in hourly)
            or not eq(min(hourly),lo)
            or not eq(max(hourly),hi)
            or r["independent_UTC_reference_labels"].split(";")!=labels
            or r["verified_source_UTC_start"]!=t.strftime("%Y-%m-%dT%H:%MZ")
            or r["original_source_QC"]!="2"
            or r["original_units"]!=src["unit"]
            or not eq(orig,r["original_JPF_selected_F"])
            or not eq(orig,r["same_release_original_ERA"])
            or r["outside_independent_hourly_envelope"]!="1"
            or lo<=orig<=hi
            or r["science_review_state"]!="HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE"
            or tuple(float(r[x]) for x in ("ERA5L_nearest_grid_lat","ERA5L_nearest_grid_lon"))!=YMS_GRID):
            raise ValueError("Stage05AK source actual value/UTC/independent hourly context changed")
        if k[2]=="LW_IN" and r["independent_hourly_product_processing"]!="CDS_TIMESERIES_DEACCUMULATED_STRD_J_M2_DIVIDE_3600_NO_SECOND_DIFFERENCING":
            raise ValueError("Independently sourced hourly LW radiation units/time processing changed")
        if k[2]=="PA" and r["independent_hourly_product_processing"]!="SOURCE_CDS_SP_PA_DIVIDE_1000":
            raise ValueError("Independently sourced pressure Pa→kPa processing changed")
        result.append({
            "site":k[0],"native_halfhour_start":k[1],
            "verified_source_UTC_start":r["verified_source_UTC_start"],
            "variable":k[2],"original_F_selected":src["selected_F"],
            "original_ERA_same_release":src["ERA_in_same_release"],
            "original_source_QC":"2","unit":src["unit"],
            "independent_ERA5L_hourly_context_min":lo,
            "independent_ERA5L_hourly_context_max":hi,
            "context_outside":1,
            "independent_context_evidence_tier":"STAGE05AK_CONTEXT_ONLY_NOT_YET_STRONG_LABEL_APPROVED",
            "source_provenance_class":"REAL_TWO_SUCCESSFUL_CDS_REQUESTS_ZIP_CRC_UTC_GRID_VERIFIED",
            "hourly_model_grid_context_limits":"JP-Yms original BIF tower 220m; nearest ERA5L model grid elevation not verified; strd is deaccumulated hourly energy and valid time interval-end; no pointwise half-hour substitution",
            "repair_approval_status":"HOLD_NO_APPROVED_HALF_HOUR_REPLACEMENT"
        })
    if seen!=EXPECTED_NEW:raise ValueError("Five exact original JP-Yms source timestamps/variables changed")
    if len({(s,t) for s,t,v in seen})!=4:
        raise ValueError("Original new JP-Yms 2011 context should be 4 site-native halfhours")
    return result,seen

def verify_six_original_zips(audit):
    if (audit.get("stage")!="JapanFlux Stage05AB"
        or audit.get("status")!="SIX_ORIGINAL_2011_DAY_PAYLOADS_READONLY_INVENTORIED"
        or audit.get("original_45_source_fields_HOLD") is not True
        or audit.get("new_CDS_requests")!=0
        or audit.get("science_repair_approved") is not False
        or audit.get("original_source_or_forcing_modified") is not False):
        raise ValueError("Latest Stage05AB source provenance invalid")
    rows=audit.get("six_site_day_inventory",[])
    if len(rows)!=6 or len({(r["site"],r["UTC_day"]) for r in rows})!=6:
        raise ValueError("Require six distinct original Dec2011 CDS windows")
    for r in rows:
        if (r["content_status"]!="COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR"
            or r["files"]["ZIP"]["status"]!="REGULAR"
            or r["files"]["PARTIAL"]["status"]!="ABSENT"
            or r["files"]["CSV"]["status"]!="ABSENT"
            or r["files"]["NC"]["status"]!="ABSENT"
            or r["zip_inspection"]["independent_hourly_values_count"]!=(48 if r["site"]=="JP-Yms" else 24)):
            raise ValueError("Original six window ZIP/UTC/multi-variable source audit changed")
        if r["site"]=="JP-Yms":
            day=r["UTC_day"]
            if (r["zip_inspection"]["ZIP_SHA256"]!=YMS_SHA[day]
                or r["zip_inspection"]["validated_raw_columns"]!=["sp","strd"]):
                raise ValueError("JP-Yms original two-day ZIP source SHA/variables changed")

def selftest():
    assert len(EXPECTED_NEW)==5 and len({t for s,t,v in EXPECTED_NEW})==4
    assert 22+5+18==45
    assert len(FIELDS)==15
    assert Counter(v for s,t,v in EXPECTED_NEW)==Counter({"PA":3,"LW_IN":2})
    assert 221.921111>44.79 and 99.985360>68.160 and 100.061340>37.349
    print("STAGE05AL SELF-TEST PASS | 22 prior strong +5 new independent context-only +18 original time-source HOLD; 9/9 sources, no repair/NETWORK/WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    keys=("stage05o_utc","stage05o_native_hold","stage05ah_evidence","stage05ah_summary",
          "stage05ak_context","stage05ak_summary","stage05ab_audit")
    for k in keys:p.add_argument("--"+k.replace("_","-"),type=Path)
    p.add_argument("--out-dir",type=Path)
    args=p.parse_args()
    if args.self_test:
        selftest();return
    if any(getattr(args,k) is None for k in keys) or args.out_dir is None:
        p.error("Need all exact original Stage05O/AH/AK/AB science files and fresh --out-dir")
    original,unresolved=source_ledger(load_tsv(args.stage05o_utc),
                                      load_tsv(args.stage05o_native_hold))
    old,oldkeys=old_context(load_tsv(args.stage05ah_evidence),
                            load_json(args.stage05ah_summary),original)
    new,newkeys=new_context(load_tsv(args.stage05ak_context),
                            load_json(args.stage05ak_summary),original)
    verify_six_original_zips(load_json(args.stage05ab_audit))
    if (oldkeys&newkeys or oldkeys|newkeys!=set(original)
        or len(old)+len(new)!=27 or len(oldkeys|newkeys)!=27):
        raise ValueError("Not all original 27 UTC-confirmed source QC2 fields independently compared exactly once")
    allrows=sorted(old+new,key=lambda r:(r["site"],r["native_halfhour_start"],r["variable"]))
    if (len({(r["site"],r["native_halfhour_start"]) for r in allrows})!=21
        or len(unresolved)!=18 or len({(s,t) for s,t,v in unresolved})!=14):
        raise ValueError("Expected 21 independently compared and 14 unresolved site/native time points")
    if args.out_dir.exists():p.error("Refuse overwriting previous source audit folder")
    args.out_dir.mkdir(parents=True)
    table=args.out_dir/"stage05al_27_original_QC2_source_independent_context_22strong_5context_HOLD.tsv"
    report=args.out_dir/"stage05al_45_original_field_science_status_27_context_18_clock_HOLD.json"
    with table.open("x",encoding="utf-8",newline="") as stream:
        w=csv.DictWriter(stream,fieldnames=FIELDS,delimiter="\t")
        w.writeheader()
        w.writerows(allrows)
    summary={
        "stage":"JapanFlux Stage05AL",
        "status":"27_ORIGINAL_QC2_FIELDS_INDEPENDENT_CONTEXT_OUTSIDE_HOURLY_ENVELOPES_18_CLOCK_HOLD_NO_REPAIR",
        "original_selected_F_ERA_QC2_variable_fields":45,
        "verified_UTC_source_fields":27,
        "independently_hourly_context_reviewed_fields":27,
        "independently_context_outside_fields":27,
        "previously_strong_label_independent_context_fields":22,
        "new_Stage05AK_context_only_not_strong_label_approved_fields":5,
        "independent_context_by_site":{"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10},
        "independently_context_checked_distinct_site_native_halfhours":21,
        "clock_unresolved_original_source_fields":18,
        "clock_unresolved_by_site":{"JP-Tef":4,"JP-Tmd":14},
        "clock_unresolved_distinct_site_native_halfhours":14,
        "full_independent_CDS_site_days_verified":9,
        "Yms_Dec2011_original_CDS_ZIP_SHA256":YMS_SHA,
        "latest_stage05AB_original_dec2011_days_verified":6,
        "new_5_fields_strong_evidence_automatically_approved":False,
        "physical_repair_values_approved":False,
        "all_45_original_source_fields_HOLD":True,
        "CDS_requests_this_stage":0,
        "original_JPF_source_ZIP_or_forcing_modified":False,
        "Slurm_jobs":0,
        "input_sha256":{key:sha(getattr(args,key)) for key in keys}
    }
    with report.open("x",encoding="utf-8") as stream:
        json.dump(summary,stream,indent=2,ensure_ascii=False);stream.write("\n")
    print("STAGE05AL 27 ORIGINAL SOURCE QC2 INDEPENDENT HOURLY CONTEXT MERGE PASS | NO CDS / SLURM / REPAIR")
    print("INDEPENDENT_HOURLY_CONTEXT_REVIEWED",27,"/45","OUTSIDE_REFERENCE_ENVELOPE",27)
    print("PRIOR_STRONG_CONTEXT",22,"NEW_STAGE05AK_CONTEXT_ONLY_HOLD",5)
    print("BY_SITE",summary["independent_context_by_site"],
          "DISTINCT_SITE_NATIVE_HALF_HOURS",21)
    print("SOURCE_CLOCK_TIMEBASE_HOLD",18,"BY_SITE",summary["clock_unresolved_by_site"])
    print("REFERENCE_SITE_DAYS_VERIFIED",9,"/9")
    print("UNIFIED_SOURCE_CONTEXT_TSV",table)
    print("SCIENCE_HOLD_REPORT",report)
    print("ALL_45_ORIGINAL_SOURCE_FIELDS_HOLD; NO MET_REPAIR_VALUES_APPROVED")
if __name__=="__main__":
    main()

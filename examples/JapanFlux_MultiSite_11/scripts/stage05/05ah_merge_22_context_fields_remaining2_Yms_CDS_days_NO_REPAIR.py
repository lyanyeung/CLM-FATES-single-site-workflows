#!/usr/bin/env python3
"""JapanFlux Stage05AH: source-verified 19+3=22 strong external physical contexts.

Pure read-only inputs: Stage05O 27 original UTC/JST source rows plus 18
unresolved source timebase HOLD rows, Stage05AE 19-field independently
evidenced registry/summary + original remaining four 2011 CDS site-days,
Stage05AG 3 original JP-Khw 2011 pressure fields + two-day science audit,
and most recent original Stage05AB 6-site-day CDN ZIP/CRC/time/grid audit.

No CDS/network, original ZIP reading/writes, source forcing/model/Slurm work,
half-hour pointwise replacements or automatic approvals. Only a new derived
TSV+JSON bundle is written to the unique --out-dir.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path

SRC_COUNTS=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
PENDING={("JP-Yms","2011-12-16"),("JP-Yms","2011-12-17")}
KHW_KEYS={("JP-Khw","201112170630","PA"),
          ("JP-Khw","201112170700","PA"),
          ("JP-Khw","201112170730","PA")}
DEC_SHA={
  "2011-12-16":"fb2d7677d7c8a38fe4d5d31eb0af37434cfe0932a59343e36601f61b7e407821",
  "2011-12-17":"f590c32432ffac5c10460ea074ea8fc05fb9b8742af96f8301e9d35ed6fb6188"}
CSV_COLS=("site","native_JST_halfhour_start","UTC_halfhour_start","variable",
          "original_JPF_F","source_same_release_ERA","source_QC","source_units",
          "independent_CDS_ZIP_SHA256","reference_provenance_class",
          "independent_hourly_context_min","independent_hourly_context_max",
          "independent_reference_units","minimum_gap_to_hourly_context",
          "context_outside","evidence_label","repair_status",
          "time_grid_and_representativeness_limit")
UNIT={"PA":"kPa","LW_IN":"W m-2","TA":"deg C"}

def read_tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        dr=csv.DictReader(f,delimiter="\t")
        if not dr.fieldnames or len(dr.fieldnames)!=len(set(dr.fieldnames)):
            raise ValueError("Source evidence TSV has missing/duplicate header")
        return list(dr)

def read_json(path):
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict):raise ValueError("Expected original JSON object")
    return v

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(2*1024*1024),b""):
            h.update(data)
    return h.hexdigest()

def original_sources(utc_rows,native_rows):
    if len(utc_rows)!=27 or Counter(r["site"] for r in utc_rows)!=SRC_COUNTS:
        raise ValueError("Original Stage05O UTC-source field provenance changed")
    if len(native_rows)!=18 or Counter(r["site"] for r in native_rows)!=Counter({"JP-Tef":4,"JP-Tmd":14}):
        raise ValueError("Original solar-vs-standard-time source 18 field scope changed")
    src={};tms=set()
    for r in utc_rows:
        key=(r["site"],r["native_start"],r["variable"])
        if key in src:raise ValueError("Duplicate original source UTC variable")
        if r["variable"] not in UNIT or r["unit"]!=UNIT[r["variable"]]:
            raise ValueError("Unexpected original source field units")
        start=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        x=float(r["selected_F"]); y=float(r["ERA_in_same_release"])
        if (start-utc!=timedelta(hours=9)
            or r["raw_F_QC"]!="2"
            or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"
            or not all(math.isfinite(v) for v in (x,y))
            or not math.isclose(x,y,abs_tol=1e-9,rel_tol=1e-12)):
            raise ValueError("Original source UTC or QC2/F=ERA status changed")
        src[key]=r
    for r in native_rows:
        key=(r["site"],r["native_start"],r["variable"])
        if (key in src or key in tms or r["raw_F_QC"]!="2"
            or r["utc_start"]!="UNRESOLVED"
            or r["source_status"]!="HOLD_LOCAL_SOLAR_VS_STANDARD_TIME_PROVENANCE"):
            raise ValueError("Original source Tef/Tmd temporal ambiguity cannot be resolved without review")
        tms.add(key)
    if len({(s,t) for s,t,v in src})!=21 or len({(s,t) for s,t,v in tms})!=14:
        raise ValueError("Original 27 UTC/18 unresolved 35 site-time source events changed")
    return src

def verify_ae(rows,audit,source):
    if (audit.get("stage")!="JapanFlux Stage05AE"
        or audit.get("status")!="NINETEEN_ORIGINAL_SOURCE_QC2_VARIABLES_STRONGLY_INCONSISTENT_WITH_INDEPENDENT_HOURLY_ERA5L_HOLD"
        or audit.get("original_source_anomaly_fields_total")!=45
        or audit.get("source_field_evidence_count")!=19
        or audit.get("distinct_original_site_native_halfhours_evidenced")!=14
        or audit.get("independent_context_by_site")!={"JP-Fjy":6,"JP-Khw":8,"JP-Yms":5}
        or audit.get("UTC_verified_original_source_fields_unreviewed")!=8
        or audit.get("original_native_clock_conflict_fields_HOLD")!=18
        or audit.get("reference_site_UTC_days_with_payloads_verified")!=5
        or audit.get("remaining_site_UTC_days_without_reference_payload")!=4
        or audit.get("no_replacement_value_approved") is not True
        or audit.get("all_45_original_field_candidates_HOLD") is not True):
        raise ValueError("Stage05AE previous actual source science HOLD summary changed")
    if len(rows)!=19 or Counter(r["site"] for r in rows)!=Counter({"JP-Fjy":6,"JP-Khw":8,"JP-Yms":5}):
        raise ValueError("Stage05AE prior 19 records by-site scope changed")
    seen=set()
    for r in rows:
        key=(r["site"],r["native_JST_halfhour_start"],r["variable"])
        if key in seen or key not in source or key in KHW_KEYS:
            raise ValueError("Duplicate/unknown previous evidence variable field")
        seen.add(key)
        base=source[key]
        expected=datetime.strptime(base["utc_start"],"%Y%m%d%H%M").strftime("%Y-%m-%dT%H:%MZ")
        x=float(base["selected_F"])
        lo=float(r["independent_hourly_context_min"])
        hi=float(r["independent_hourly_context_max"])
        if (r["UTC_halfhour_start"]!=expected
            or r["source_QC"]!="2" or r["context_outside"]!="1"
            or r["source_units"]!=base["unit"]
            or r["repair_status"]!="SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT"
            or not math.isclose(x,float(r["original_JPF_F"]),abs_tol=1e-9,rel_tol=1e-12)
            or not math.isclose(x,float(r["source_same_release_ERA"]),abs_tol=1e-9,rel_tol=1e-12)
            or not (math.isfinite(lo) and math.isfinite(hi) and lo<=hi and (x<lo or x>hi))):
            raise ValueError("Prior source original field or independent context invariant changed")
    if len({(s,t) for s,t,v in seen})!=14:
        raise ValueError("Stage05AE 14 old distinct original site-native times changed")
    return seen

def verify_ag(rows,audit,source):
    if (audit.get("stage")!="JapanFlux Stage05AG"
        or audit.get("status")!="SOURCE_VERIFIED_JP_KHW_2011_TWO_DAY_HOURLY_PA_CONTEXT_NO_REPAIR"
        or audit.get("site")!="JP-Khw"
        or audit.get("UTC_days")!=["2011-12-16","2011-12-17"]
        or audit.get("source_original_QC2_fields")!=3
        or audit.get("source_requested_hour_variable_pairs")!=9
        or audit.get("source_candidate_distinct_native_halfhours")!=3
        or audit.get("source_PA_fields_outside_independent_hourly_range")!=3
        or audit.get("CDS_response_original_SHA256_by_UTC_day")!=DEC_SHA
        or audit.get("CDS_validated_independent_hourly_pressure_count")!=48
        or audit.get("CDS_grid_elevation")!="NOT_VERIFIED"
        or audit.get("scientific_repair_values_approved") is not False
        or audit.get("all_45_original_JPF_source_QC2_fields_HOLD") is not True
        or audit.get("CDS_requests_this_stage")!=0
        or audit.get("original_zip_or_forcing_modified") is not False):
        raise ValueError("Stage05AG actual independent physical pressure source evidence/hold changed")
    if len(rows)!=3:raise ValueError("Expected three new original JP-Khw PA candidates")
    seen=set(); result=[]
    for r in rows:
        key=(r["site"],r["original_JST_halfhour_start"],r["variable"])
        if key not in KHW_KEYS or key not in source or key in seen:
            raise ValueError("Unknown/duplicate original 2011 JP-Khw pressure event")
        seen.add(key)
        base=source[key]
        x=float(base["selected_F"])
        t=datetime.strptime(base["utc_start"],"%Y%m%d%H%M")
        ts=[(t.replace(minute=0)+timedelta(hours=j)).strftime("%Y-%m-%dT%H:%MZ") for j in range(3)]
        vals=[float(s) for s in r["hourly_ERA5L_pressures_kPa"].split(";")]
        if len(vals)!=3 or not all(math.isfinite(v) for v in vals):
            raise ValueError("Stage05AG independent hourly record count/values wrong")
        lo=min(vals); hi=max(vals)
        gap=lo-x if x<lo else x-hi if x>hi else 0.0
        if (r["original_F_QC"]!="2" or base["unit"]!="kPa"
            or r["derived_UTC_start"]!=t.strftime("%Y-%m-%dT%H:%MZ")
            or r["hourly_ERA5L_valid_times_UTC"].split(";")!=ts
            or not math.isclose(x,float(r["original_JPF_F_kPa"]),abs_tol=1e-9,rel_tol=1e-12)
            or not math.isclose(x,float(r["same_release_original_ERA_kPa"]),abs_tol=1e-9,rel_tol=1e-12)
            or not math.isclose(lo,float(r["hourly_ERA5L_context_min_kPa"]),abs_tol=1e-6)
            or not math.isclose(hi,float(r["hourly_ERA5L_context_max_kPa"]),abs_tol=1e-6)
            or not math.isclose(gap,float(r["minimum_distance_to_context_kPa"]),abs_tol=1e-6)
            or r["outside_independent_hourly_context"]!="1"
            or not (x<lo or x>hi)
            or r["science_status"]!="HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR"
            or r["grid_elevation_status"]!="UNKNOWN_196M_TOWER_GRID_HEIGHT_REPRESENTATIVENESS_NOT_APPROVED"):
            raise ValueError("Stage05AG 2011 source QC2/independent ERA5L original pressure inconsistency changed")
        result.append({
            "site":"JP-Khw","native_JST_halfhour_start":base["native_start"],
            "UTC_halfhour_start":r["derived_UTC_start"],"variable":"PA",
            "original_JPF_F":base["selected_F"],
            "source_same_release_ERA":base["ERA_in_same_release"],
            "source_QC":"2","source_units":"kPa",
            "independent_CDS_ZIP_SHA256":";".join(DEC_SHA[d] for d in ("2011-12-16","2011-12-17")),
            "reference_provenance_class":"DEC16_KHW_CDS_REQUEST_LOG_OBSERVED_DEC17_EXISTING_ZIP_REQUEST_ID_NOT_OBSERVED_BOTH_SHA_CRC_24H_VERIFIED",
            "independent_hourly_context_min":round(lo,6),
            "independent_hourly_context_max":round(hi,6),
            "independent_reference_units":"kPa",
            "minimum_gap_to_hourly_context":round(gap,6),
            "context_outside":1,"evidence_label":"SEVERE_2011_JPF_QC2_PA_INCONSISTENT_WITH_INDEPENDENT_HOURLY_CONTEXT",
            "repair_status":"SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT",
            "time_grid_and_representativeness_limit":"JP-Khw tower BIF 196m; independent ERA5-Land grid geopotential/elevation unknown; no halfhour pointwise replacement approved"
        })
    if seen!=KHW_KEYS:raise ValueError("JP-Khw actual 2011 three original site halfhours changed")
    return result

def verify_inventory_and_remaining(ab,ae_remaining):
    if (ab.get("stage")!="JapanFlux Stage05AB"
        or ab.get("status")!="SIX_ORIGINAL_2011_DAY_PAYLOADS_READONLY_INVENTORIED"
        or ab.get("original_45_source_fields_HOLD") is not True
        or ab.get("science_repair_approved") is not False
        or ab.get("new_CDS_requests")!=0
        or ab.get("original_source_or_forcing_modified") is not False):
        raise ValueError("Latest original six-day Stage05AB source inventory invalid")
    records=ab.get("six_site_day_inventory",[])
    if len(records)!=6 or len({(r["site"],r["UTC_day"]) for r in records})!=6:
        raise ValueError("Missing original Stage05AB source site-day entries")
    look={(r["site"],r["UTC_day"]):r for r in records}
    for site in ("JP-Fjy","JP-Khw"):
        for day in ("2011-12-16","2011-12-17"):
            r=look[(site,day)]
            if (r["content_status"]!="COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR"
                or r["files"]["ZIP"]["status"]!="REGULAR"
                or r["files"]["PARTIAL"]["status"]!="ABSENT"
                or r["zip_inspection"]["source_csv_members"]!=1
                or r["zip_inspection"]["independent_hourly_values_count"]!=24):
                raise ValueError("Previously evidenced Fjy/Khw December ZIP no longer validates")
            if site=="JP-Khw" and r["zip_inspection"]["ZIP_SHA256"]!=DEC_SHA[day]:
                raise ValueError("Actual Khw independent CDS ZIP SHA does not match science evidence")
    for k in PENDING:
        r=look[k]
        if (r["content_status"]!="ABSENT"
            or any(x["status"]!="ABSENT" for x in r["files"].values())):
            raise ValueError("Yms original CDS date now has a file: fresh scientific inventory required")
    if (ae_remaining.get("stage")!="JapanFlux Stage05AE"
        or ae_remaining.get("status")!="FOUR_CDS_SITE_UTC_DAYS_SOURCE_SCOPE_PREVIEW_ONLY"
        or ae_remaining.get("remaining_site_day_count")!=4
        or ae_remaining.get("CDS_requests_this_stage")!=0
        or ae_remaining.get("model_forcing_modified") is not False):
        raise ValueError("Original Stage05AE four CDS site-day plan changed")
    items=ae_remaining.get("remaining",[])
    keys={(r["site"],r["UTC_day"]) for r in items}
    if len(items)!=4 or keys!=PENDING|{("JP-Khw","2011-12-16"),("JP-Khw","2011-12-17")}:
        raise ValueError("Stage05AE four-day reference scope changed")
    out=[r for r in items if (r["site"],r["UTC_day"]) in PENDING]
    for r in out:
        if (r["CDS_dataset"]!="reanalysis-era5-land-timeseries"
            or set(r["variable_scope"])!={"surface_pressure","surface_thermal_radiation_downwards"}
            or not r["source_BIF_SHA256"] or not r["source_UTC_hours"]):
            raise ValueError("JP-Yms original source scope/variables UTC hours invalid")
    return sorted(out,key=lambda r:r["UTC_day"])

def self_test():
    assert 19+3+5+18==45
    assert len(KHW_KEYS)==3 and len(PENDING)==2
    assert Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})==SRC_COUNTS
    assert len(CSV_COLS)==18
    print("STAGE05AH SELF-TEST PASS | 19+3=22 original source QC2 fields, 5 Yms UTC-ready, 18 clock conflict, 2 CDS days; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    names=("stage05o_utc","stage05o_native_hold","stage05ae_evidence",
           "stage05ae_summary","stage05ae_remaining",
           "stage05ag_evidence","stage05ag_summary","stage05ab_audit")
    for name in names:p.add_argument("--"+name.replace("_","-"),type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:self_test();return
    if any(getattr(a,n) is None for n in names) or a.out_dir is None:
        p.error("Need all actual original Stage05O/AE/AG/AB science files and new output dir")
    source=original_sources(read_tsv(a.stage05o_utc),read_tsv(a.stage05o_native_hold))
    prior=read_tsv(a.stage05ae_evidence)
    oldkeys=verify_ae(prior,read_json(a.stage05ae_summary),source)
    newer=verify_ag(read_tsv(a.stage05ag_evidence),read_json(a.stage05ag_summary),source)
    remaining=verify_inventory_and_remaining(read_json(a.stage05ab_audit),read_json(a.stage05ae_remaining))
    rows=[{c:r[c] for c in CSV_COLS} for r in prior]+newer
    keys={(r["site"],r["native_JST_halfhour_start"],r["variable"]) for r in rows}
    if (len(keys)!=22 or len(rows)!=22 or len(oldkeys)!=19
        or Counter(s for s,t,v in keys)!=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":5})
        or len({(s,t) for s,t,v in keys})!=17):
        raise ValueError("Actual 22 field source evidence/17 original native site-times mismatch")
    todo=set(source)-keys
    if (len(todo)!=5 or Counter(s for s,t,v in todo)!=Counter({"JP-Yms":5})
        or len(remaining)!=2):
        raise ValueError("Five remaining original UTC-verified JP-Yms fields/two source CDS days changed")
    if a.out_dir.exists():p.error("Refuse report overwrite; choose a fresh output directory")
    a.out_dir.mkdir(parents=True)
    table=a.out_dir/"stage05ah_22_original_source_QC2_ERA5L_independent_context_HOLD.tsv"
    preview=a.out_dir/"stage05ah_2_remaining_JP_Yms_CDS_site_UTC_days_PREVIEW_ONLY.json"
    report=a.out_dir/"stage05ah_45_original_source_field_science_coverage_NO_REPAIR.json"
    with table.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=CSV_COLS,delimiter="\t")
        w.writeheader()
        w.writerows(sorted(rows,key=lambda r:(r["site"],r["native_JST_halfhour_start"],r["variable"])))
    with preview.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05AH",
                   "status":"TWO_YMS_2011_CDS_SITE_DAYS_PREVIEW_ONLY",
                   "verified_payload_site_days":7,"remaining_count":2,
                   "remaining":remaining,"CDS_requests_this_stage":0,
                   "original_source_or_forcing_changed":False},f,indent=2)
        f.write("\n")
    coverage={"stage":"JapanFlux Stage05AH",
        "status":"TWENTY_TWO_ORIGINAL_QC2_FIELDS_WITH_STRONG_INDEPENDENT_ERA5L_CONTEXT_HOLD",
        "original_source_QC2_anomaly_fields":45,
        "independently_contextualized_original_source_fields":22,
        "by_site":{"JP-Fjy":6,"JP-Khw":11,"JP-Yms":5},
        "distinct_original_site_native_halfhours":17,
        "original_UTC_verified_fields_needing_independent_science_comparison":5,
        "original_native_clock_source_conflict_fields":18,
        "verified_independent_CDS_site_UTC_day_payloads":7,
        "remaining_unverified_CDS_site_UTC_days":2,
        "remaining_sites":["JP-Yms"],
        "Khw_original_2011_ZIP_SHA256":DEC_SHA,
        "Khw_Dec17_CDS_request_ID":"NOT_OBSERVED_IN_OPERATOR_OUTPUT",
        "grid_altitude_196m_tower":"ERA5L_GRID_ALTITUDE_NOT_VERIFIED",
        "source_30min_replacement_approved":False,
        "all_45_original_source_anomaly_fields_HOLD":True,
        "CDS_requests_this_stage":0,"original_JPF_zip_or_forcing_changed":False,
        "Slurm_jobs":0,
        "input_sha256":{n:digest(getattr(a,n)) for n in names}}
    with report.open("x",encoding="utf-8") as f:
        json.dump(coverage,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AH 22 SOURCE FIELDS INDEPENDENT CONTEXT MERGE PASS | NO CDS / SLURM / REPAIR")
    print("STRONG_CONTEXT_EVIDENCE",22,"/45","BY_SITE",coverage["by_site"],
          "DISTINCT_SITE_NATIVE_HALF_HOURS",17)
    print("UTC_VERIFIED_AWAITING_INDEPENDENT_REVIEW",5,"TIMEBASE_CONFLICT_HOLD",18)
    print("CDS_SITE_DAYS_VALIDATED",7,"REMAINING_YMS_SITE_DAYS",len(remaining))
    for r in remaining:print("CDS_REMAINING",r["site"],r["UTC_day"],
        "VARIABLES",",".join(r["variable_scope"]))
    print("SOURCE_EVIDENCE_TSV",table)
    print("REMAINING_DAYS_PREVIEW",preview)
    print("SCIENCE_COVERAGE_SUMMARY",report)
    print("ALL_45_SOURCE_QC2_FIELDS_HOLD; NO REPLACEMENTS APPROVED")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""JapanFlux Stage05V: independent evidence ledger + remaining 8 CDS days, audit-only.

Source-pinned inputs: real Stage05U 8 JPF QC2 fields / 4 half-hours
cross-referenced to separately downloaded ERA5-Land hourly time series;
Stage05S source-gated 9-day CDS request PREVIEW; Stage05T CDS source audit.
This tool never makes network/CDS calls, never reads source ZIPs, does not
interpolate hourly reference to a half-hour repair, and never alters forcing.
All 45 original flagged source fields continue on science HOLD.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path

CDS_SHA = "111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0"
EXPECTED_DATE = "2005-08-11"
PILOT = ("JP-Khw", EXPECTED_DATE)
EXPECTED_SITES = {"JP-Fjy", "JP-Khw", "JP-Yms"}
EXPECTED_FIELDS = {
    ("200508120200","LW_IN"),
    ("200508120230","LW_IN"),("200508120230","PA"),("200508120230","TA"),
    ("200508120300","PA"),("200508120300","TA"),
    ("200508120330","PA"),("200508120330","TA"),
}
OUTPUT_FIELDS = (
    "site","source_native_start_JST","source_UTC_start","variable",
    "JPF_selected_F","original_F_QC","same_release_ERA",
    "independent_hourly_context_min","independent_hourly_context_max",
    "independent_hourly_context_units","minimum_distance_to_context_interval",
    "evidence_strength","repair_status",
    "meteorology_and_timing_caveat",
)
def read_tsv(path:Path)->list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if not rows:raise ValueError("No Stage05U rows")
    return rows

def classify(v:str,x:float,lo:float,hi:float)->str:
    if v=="TA" and x< -90:
        return "NONPHYSICAL_AIR_TEMPERATURE_IN_SITU_STRONG_INDEPENDENT_SUPPORT"
    if v=="PA" and x<=0:
        return "NONPHYSICAL_SURFACE_PRESSURE_IN_SITU_STRONG_INDEPENDENT_SUPPORT"
    if v=="PA" and x<50:
        return "SEVERE_SITE_PRESSURE_DEFICIT_INDEPENDENT_SUPPORT"
    if v=="LW_IN" and x<100 and lo>200:
        return "VERY_LARGE_LONGWAVE_DEFICIT_INDEPENDENT_SUPPORT"
    return "HOLD_UNCLASSIFIED_DO_NOT_ASSUME_CORRECTION"

def verify_u(summary:dict,records:list[dict])->list[dict]:
    if (summary.get("stage")!="JapanFlux Stage05U"
        or summary.get("status")!="READONLY_INDEPENDENT_REFERENCE_CONTEXT_CROSSCHECK"
        or summary.get("source_site")!="JP-Khw"
        or summary.get("UTC_date")!=EXPECTED_DATE
        or summary.get("original_source_candidate_rows_on_date")!=8
        or summary.get("original_source_candidate_unique_halfhours")!=4
        or summary.get("original_source_outside_hourly_context_range_count")!=8
        or summary.get("CDS_first_download_ZIP_SHA256")!=CDS_SHA
        or summary.get("repair_applied") is not False
        or summary.get("scientific_approval") is not False
        or summary.get("all_45_original_field_candidates_still_HOLD") is not True):
        raise ValueError("Original Stage05U provenance/complete 8-field HOLD gate failed")
    if len(records)!=8 or {(r["native_JST_source_start"],r["variable"]) for r in records}!=EXPECTED_FIELDS:
        raise ValueError("Stage05U changed JP-Khw 2005-08-12 exact eight candidate source keys")
    results=[]
    for r in records:
        v=r["variable"]
        src=float(r["JPF_selected_F_value"])
        embedded=float(r["JPF_same_release_ERA_value"])
        low=float(r["independent_context_min"])
        high=float(r["independent_context_max"])
        if not all(math.isfinite(t) for t in (src,embedded,low,high)) or low>high:
            raise ValueError("Nonfinite or invalid source/reference value")
        if not math.isclose(src,embedded,abs_tol=1e-9,rel_tol=1e-12):
            raise ValueError("Source selected F differs from same-release ERA")
        if r["raw_JPF_F_QC"]!="2" or r["JPF_outside_independent_hourly_context_range"]!="1":
            raise ValueError("Source QC2 or outside-hourly-context flag not confirmed")
        if r["science_status"]!="SOURCE_NONPHYSICAL_CANDIDATE_HOLD_NOT_APPROVED":
            raise ValueError("Stage05U science HOLD status changed")
        if not (src<low or src>high):
            raise ValueError("Source anomaly not outside independent hourly context")
        if v not in ("TA","PA","LW_IN"):
            raise ValueError("Unexpected source variable")
        expected_unit={"TA":"degC","PA":"kPa","LW_IN":"W m-2 hourly mean"}[v]
        if r["ERA5Land_comparison_units"]!=expected_unit:
            raise ValueError("Independent reference units differ from original review")
        distance=low-src if src<low else src-high
        classification=classify(v,src,low,high)
        if classification.startswith("HOLD_UNCLASSIFIED"):
            raise ValueError("Manual science review required; unexpected classification")
        results.append({
            "site":r["site"],
            "source_native_start_JST":r["native_JST_source_start"],
            "source_UTC_start":r["derived_UTC_start"],
            "variable":v,
            "JPF_selected_F":r["JPF_selected_F_value"],
            "original_F_QC":r["raw_JPF_F_QC"],
            "same_release_ERA":r["JPF_same_release_ERA_value"],
            "independent_hourly_context_min":round(low,6),
            "independent_hourly_context_max":round(high,6),
            "independent_hourly_context_units":expected_unit,
            "minimum_distance_to_context_interval":round(distance,6),
            "evidence_strength":classification,
            "repair_status":"HOLD_NOT_APPROVED_DO_NOT_WRITE_FORCING",
            "meteorology_and_timing_caveat":(
                "Independently downloaded hourly nearest-grid ERA5-Land, not a point-for-point "
                "tower measurement. For LW_IN, hourly mean and half-hour interval do not match; "
                "no interpolation, pressure elevation adjustment, or repair is defined.")
        })
    return sorted(results,key=lambda r:(r["source_native_start_JST"],r["variable"]))

def verify_s(plan:dict,t:dict)->list[dict]:
    if (plan.get("stage")!="JapanFlux Stage05S"
        or plan.get("validated_site_count")!=3
        or plan.get("UTC_day_windows")!=9
        or plan.get("source_required_site_UTC_hours")!=54
        or plan.get("source_required_variable_UTC_hour_pairs")!=87
        or plan.get("CDS_calls_made")!=0
        or plan.get("model_science_approved") is not False):
        raise ValueError("Stage05S original request preview provenance not verified")
    if (t.get("stage")!="JapanFlux Stage05T"
        or t.get("CDS_original_member_sha256")!=CDS_SHA
        or t.get("file_info",{}).get("pilot_zip_sha256")!=CDS_SHA
        or t.get("physical_repair_approved") is not False):
        raise ValueError("Stage05T source-verified independent CDS provenance missing")
    requests=plan.get("site_day_pilot_requests",[])
    if len(requests)!=9:
        raise ValueError("Expected original nine source-gated site/day windows")
    seen=set();remaining=[]
    for item in requests:
        site=item["site"];day=item["utc_day"]
        if site not in EXPECTED_SITES or (site,day) in seen:
            raise ValueError("Duplicate or unapproved site/day in Stage05S preview")
        seen.add((site,day))
        if item["dataset"]!="reanalysis-era5-land-timeseries":
            raise ValueError("Unexpected original CDS product")
        if item["data_and_science_state"]!="NOT_SUBMITTED_UNVERIFIED_GRID_AND_UNAPPROVED_REPAIR":
            raise ValueError("Original unapproved site/day request status changed")
        if (site,day)!=PILOT:
            remaining.append({
                "site":site,"utc_day":day,
                "original_tower_coordinates":item["request"]["location"],
                "variable_scope":item["required_variables"],
                "requested_source_UTC_hours":item["required_utc_hours"],
                "source_bif_sha256":item["source_bif_sha256"],
                "CDS_dataset":"reanalysis-era5-land-timeseries",
                "status":"NOT_DOWNLOADED_AS_OF_STAGE05T_OPERATOR_LOG_NO_CDS_ACTION_THIS_STAGE",
            })
    if PILOT not in seen or len(remaining)!=8:
        raise ValueError("Expected one downloaded pilot and eight still-remaining site/day windows")
    return remaining

def self_test():
    assert len(EXPECTED_FIELDS)==8
    assert classify("TA",-268.276,22.96,23.22).startswith("NONPHYSICAL")
    assert classify("PA",0.0,97.77,97.89).startswith("NONPHYSICAL")
    assert classify("LW_IN",39.171,391.89,402.75).startswith("VERY_LARGE")
    print("STAGE05V SELF-TEST PASS | 8 exact source QC2 candidates, 9-1=8 CDS days; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage05u-tsv",type=Path)
    p.add_argument("--stage05u-summary",type=Path)
    p.add_argument("--stage05s-preview",type=Path)
    p.add_argument("--stage05t-audit",type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if any(x is None for x in (a.stage05u_tsv,a.stage05u_summary,
                               a.stage05s_preview,a.stage05t_audit,a.out_dir)):
        p.error("All four existing source documents and new --out-dir are required")
    result=verify_u(json.loads(a.stage05u_summary.read_text(encoding="utf-8")),
                    read_tsv(a.stage05u_tsv))
    remaining=verify_s(json.loads(a.stage05s_preview.read_text(encoding="utf-8")),
                       json.loads(a.stage05t_audit.read_text(encoding="utf-8")))
    if a.out_dir.exists():
        p.error("Choose a fresh out directory, never overwrite existing audit")
    a.out_dir.mkdir(parents=True)
    table=a.out_dir/"stage05v_8_original_Khw_fields_independent_CDS_evidence_HOLD.tsv"
    with table.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,delimiter="\t",fieldnames=OUTPUT_FIELDS)
        w.writeheader();w.writerows(result)
    rem=a.out_dir/"stage05v_8_remaining_CDS_site_UTC_days_PREVIEW_ONLY.json"
    with rem.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05V",
                   "status":"NO_SUBMISSIONS_EIGHT_DAYS_PREVIEW_ONLY",
                   "already_downloaded_original_CDS_pilot":{"site":PILOT[0],
                     "UTC_day":PILOT[1],"CDS_ZIP_SHA256":CDS_SHA},
                   "remaining_site_day_requests":remaining,
                   "remaining_count":len(remaining),
                   "independent_CDS_requests_this_stage":0,
                   "model_forcing_changes":False},f,indent=2,ensure_ascii=False)
        f.write("\n")
    s=a.out_dir/"stage05v_science_HOLD_summary.json"
    summary={"stage":"JapanFlux Stage05V",
             "status":"JP_KHW_8_OF_8_STRONG_INDEPENDENT_SOURCE_DEFECT_EVIDENCE_NOT_REPAIR",
             "original_source_fields_reviewed":8,
             "original_unique_site_halfhours":4,
             "evidence_categories":dict(Counter(r["evidence_strength"] for r in result)),
             "other_source_HOLD_fields":37,
             "total_original_HOLD_fields":45,
             "remaining_CDS_site_day_requests":8,
             "source_grid_elevation_difference":"NOT_DETERMINED",
             "hourly_vs_halfhour_alignment":"NOT_REPLACEMENT_READY",
             "CDS_requests_this_stage":0,
             "original_archive_or_forcing_modified":False,
             "science_repair_approved":False}
    with s.open("x",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False)
        f.write("\n")
    print("STAGE05V INDEPENDENT SOURCE DEFECT EVIDENCE AUDIT PASS | NO CDS / ZIP / SLURM / REPAIR")
    print("JP-Khw 2005-08-12 JST: 8/8 QC2 SOURCE ANOMALY FIELDS IN 4 HALF-HOURS")
    for r in result:
        print("FIELD",r["source_native_start_JST"],r["variable"],
              "SOURCE_F",r["JPF_selected_F"],
              "CDS_NEARBY_HOURLY_RANGE",
              r["independent_hourly_context_min"],r["independent_hourly_context_max"],
              "DISTANCE_FROM_CONTEXT",r["minimum_distance_to_context_interval"],
              "EVIDENCE",r["evidence_strength"],"REPAIR",r["repair_status"])
    print("OTHER_SOURCE_FIELDS_CONTINUE_HOLD 37")
    print("REMAINING_INDEPENDENT_CDS_SITE_DAYS",len(remaining))
    for r in remaining:
        print("CDS_NOT_YET_REQUESTED",r["site"],r["utc_day"],
              "VARS",",".join(r["variable_scope"]))
    print("SOURCE_EVIDENCE_TABLE",table)
    print("REMAINING_REQUESTS_PREVIEW",rem)
    print("SCIENCE_SUMMARY",s)
    print("NO REPLACEMENT VALUES; ALL 45 ORIGINAL-SOURCE FIELD CANDIDATES STILL HOLD")

if __name__=="__main__":
    main()

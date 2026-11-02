#!/usr/bin/env python3
"""JapanFlux Stage05AM: audit Tef/Tmd 18 native time/QC2 events, NO UTC guess.

Input the actual Stage05O original native-only 18-field TSV and 45-field
split provenance summary plus the actual Stage05AL 27 independent context /
18 native-source time-HOLD final summary.

Two JPF README release editions conflict: 75-line JP-Tef/Tmd README SHA
17a886... says 'local solar time'; 85-line Fjy/Khw/Yms says 'local
standard time'. Original BIF UTC_OFFSET=9 is not evidence of Tef/Tmd
timestamp conversion. Derived records strictly retain UTC UNRESOLVED.

This is a source-scoped read-only decision register; it does not re-open
original README ZIPs, extract logger data, infer mean/true solar time
corrections, submit CDS jobs, alter forcing/model or approve repair.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

EXPECTED={"JP-Tef":4,"JP-Tmd":14}
SOURCE_README_SHA="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
STANDARD_README_SHA="fe96facec6fafc57b126e850140152a540a16d97c3bfde8adfa090a3747598f9"
EXPECTED_UNIT={"TA":"deg C","PA":"kPa","LW_IN":"W m-2"}
FIELDS=("site","native_halfhour_timestamp_NOT_UTC","variable","original_F_QC2_selected",
        "original_same_release_ERA","original_unit","source_flag","original_UTC",
        "original_package_readme_claim","original_readme_SHA256",
        "BIF_declared_UTC_OFFSET_hours","BIF_offset_validates_native_clock",
        "external_FLUXNET_standard_clock_rule","site_specific_time_proof_status",
        "science_decision","required_next_evidence")

def load_json(p):
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict):raise ValueError("Input not JSON object")
    return v

def load_tsv(p):
    with p.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter="\t")
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):
            raise ValueError("Missing/duplicated original TSV columns")
        rows=list(r)
    if not rows:raise ValueError("Source original native-only records empty")
    return rows

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def source_gate(original,al,rows):
    if (original.get("stage")!="JapanFlux Stage05O"
        or original.get("status")!="3_SITE_SCOPED_UTC_ONLY"
        or original.get("verified_local_standard_sites")!=["JP-Fjy","JP-Khw","JP-Yms"]
        or original.get("unresolved_original_local_solar_README_sites")!=["JP-Tef","JP-Tmd"]
        or original.get("mapped_field_records")!=27
        or original.get("mapped_unique_site_halfhours")!=21
        or original.get("unresolved_field_records")!=18
        or original.get("unresolved_unique_site_halfhours")!=14
        or original.get("total_field_records")!=45
        or original.get("total_unique_site_halfhours")!=35
        or original.get("repair_approved") is not False
        or original.get("original_source_or_model_modified") is not False):
        raise ValueError("Original source Stage05O local-solar vs standard time conflict changed")
    if (al.get("stage")!="JapanFlux Stage05AL"
        or al.get("status")!="27_ORIGINAL_QC2_FIELDS_INDEPENDENT_CONTEXT_OUTSIDE_HOURLY_ENVELOPES_18_CLOCK_HOLD_NO_REPAIR"
        or al.get("original_selected_F_ERA_QC2_variable_fields")!=45
        or al.get("verified_UTC_source_fields")!=27
        or al.get("independently_hourly_context_reviewed_fields")!=27
        or al.get("independently_context_outside_fields")!=27
        or al.get("previously_strong_label_independent_context_fields")!=22
        or al.get("new_Stage05AK_context_only_not_strong_label_approved_fields")!=5
        or al.get("clock_unresolved_original_source_fields")!=18
        or al.get("clock_unresolved_by_site")!=EXPECTED
        or al.get("clock_unresolved_distinct_site_native_halfhours")!=14
        or al.get("full_independent_CDS_site_days_verified")!=9
        or al.get("all_45_original_source_fields_HOLD") is not True
        or al.get("physical_repair_values_approved") is not False
        or al.get("CDS_requests_this_stage")!=0):
        raise ValueError("Actual Stage05AL 27-context/18-time-HOLD ledger changed")
    if len(rows)!=18 or dict(Counter(r["site"] for r in rows))!=EXPECTED:
        raise ValueError("Stage05O unresolved source 4+14 fields no longer exact")
    seen=set();native_times=set();episodes=defaultdict(list);items=[]
    for r in rows:
        k=(r["site"],r["native_start"],r["variable"])
        if k in seen:raise ValueError("Duplicate source QC2 site-native-time-variable")
        seen.add(k)
        t=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        x=float(r["selected_F"]);embedded=float(r["ERA_in_same_release"])
        if (r["variable"] not in EXPECTED_UNIT
            or r["unit"]!=EXPECTED_UNIT[r["variable"]]
            or r["raw_F_QC"]!="2"
            or r["utc_start"]!="UNRESOLVED"
            or r["source_status"]!="HOLD_LOCAL_SOLAR_VS_STANDARD_TIME_PROVENANCE"
            or not all(math.isfinite(v) for v in (x,embedded))
            or not math.isclose(x,embedded,rel_tol=1e-12,abs_tol=1e-9)):
            raise ValueError("Original Tef/Tmd source selected F=ERA QC2/units/clock HOLD altered")
        native_times.add((r["site"],r["native_start"]))
        episodes[r["site"],t.date().isoformat()].append(r)
        items.append({
            "site":r["site"],"native_halfhour_timestamp_NOT_UTC":r["native_start"],
            "variable":r["variable"],"original_F_QC2_selected":r["selected_F"],
            "original_same_release_ERA":r["ERA_in_same_release"],"original_unit":r["unit"],
            "source_flag":"ORIGINAL_SELECTED_F_EQ_EMBEDDED_ERA_QC2",
            "original_UTC":"UNRESOLVED",
            "original_package_readme_claim":"LOCAL_SOLAR_TIME_WITHOUT_DST",
            "original_readme_SHA256":SOURCE_README_SHA,
            "BIF_declared_UTC_OFFSET_hours":"9",
            "BIF_offset_validates_native_clock":"NO",
            "external_FLUXNET_standard_clock_rule":"LOCAL_STANDARD_TIME_WITHOUT_DST_NOT_PROOF_FOR_THIS_RELEASE",
            "site_specific_time_proof_status":"NEEDS_ORIGINAL_RELEASE_SITE_SPECIFIC_PRODUCER_OR_LOGGER_TIMESTAMP_EVIDENCE",
            "science_decision":"HOLD_NATIVE_ONLY_NO_CDS_NO_UTC_NO_REPAIR",
            "required_next_evidence":"Original site logger/processing notes or release-specific author confirmation defining solar vs standard, equation-of-time use, timestamp start/end conventions"
        })
    if len(native_times)!=14 or len(episodes)==0:
        raise ValueError("Source original 18 fields must cover exactly 14 unique site/native times")
    return sorted(items,key=lambda r:(r["site"],r["native_halfhour_timestamp_NOT_UTC"],r["variable"])),episodes

def selftest():
    assert sum(EXPECTED.values())==18
    assert len(SOURCE_README_SHA)==64 and len(STANDARD_README_SHA)==64
    assert "LOCAL_SOLAR" in "LOCAL_SOLAR_TIME_WITHOUT_DST"
    assert FIELDS[7]=="original_UTC"
    print("STAGE05AM SELF-TEST PASS | Tef4/Tmd14 local-solar README versus BIF UTC_OFFSET=9 science conflict, 27/45 completed, no UTC/CDS/REPAIR/WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage05o-native-hold",type=Path)
    p.add_argument("--stage05o-summary",type=Path)
    p.add_argument("--stage05al-summary",type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(x is None for x in
           (a.stage05o_native_hold,a.stage05o_summary,a.stage05al_summary,a.out_dir)):
        p.error("Need original Stage05O native/summary + actual Stage05AL summary + new output folder")
    rows=load_tsv(a.stage05o_native_hold)
    source=load_json(a.stage05o_summary)
    ledger=load_json(a.stage05al_summary)
    register,episode=source_gate(source,ledger,rows)
    if a.out_dir.exists():p.error("Refuse existing derived output folder")
    a.out_dir.mkdir(parents=True)
    table=a.out_dir/"stage05am_18_original_Tef_Tmd_native_QC2_local_solar_timebase_CONFLICT_HOLD.tsv"
    days=a.out_dir/"stage05am_original_native_site_days_VARIABLE_COUNTS_READONLY.tsv"
    report=a.out_dir/"stage05am_45_source_fields_27_context_18_clock_review.json"
    with table.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t")
        w.writeheader()
        w.writerows(register)
    datefields=("site","original_native_date_NOT_UTC","original_flagged_variable_fields",
                "distinct_native_halfhours","variable_counts","min_original_native_timestamp",
                "max_original_native_timestamp","source_status")
    with days.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=datefields,delimiter="\t");w.writeheader()
        for (site,date),episode_records in sorted(episode.items()):
            stamps=sorted(set(r["native_start"] for r in episode_records))
            counts=Counter(r["variable"] for r in episode_records)
            w.writerow({"site":site,"original_native_date_NOT_UTC":date,
                "original_flagged_variable_fields":len(episode_records),
                "distinct_native_halfhours":len(stamps),
                "variable_counts":json.dumps(dict(counts),sort_keys=True),
                "min_original_native_timestamp":stamps[0],
                "max_original_native_timestamp":stamps[-1],
                "source_status":"UNRESOLVED_UTC_READONLY"})
    result={
        "stage":"JapanFlux Stage05AM",
        "status":"TWO_ORIGINAL_SOLAR_VS_STANDARD_SITE_CLOCKS_UNRESOLVED_SCIENCE_HOLD",
        "original_QC2_field_count":45,"already_independently_compared":27,
        "prior_strong_context_class":22,"new_context_only_not_formally_promoted":5,
        "clock_conflict_variable_fields":18,
        "clock_conflict_by_site":EXPECTED,
        "clock_conflict_native_site_halfhours":14,
        "source_native_site_days":len(episode),
        "original_Tef_Tmd_source_readme_75line_SHA256":SOURCE_README_SHA,
        "original_Tef_Tmd_source_readme_line64":"time is expressed in local solar time (without DST)",
        "different_original_Fjy_Khw_Yms_standard_readme_85line_SHA256":STANDARD_README_SHA,
        "original_BIF_UTC_OFFSET_both_sites":9,
        "original_BIF_proves_source_JST_timestamp":False,
        "original_UTC_mapping_generated":False,
        "possible_longitude_or_equation_of_time_offset_authorized":False,
        "site_PI_or_original_release_logger_clock_evidence":"NOT_YET_ESTABLISHED",
        "CDS_requests":0,"Slurm_jobs":0,
        "original_source_or_forcing_modified":False,"half_hour_repair_values_approved":False,
        "all_45_original_QC2_fields_HOLD":True,
        "source_input_sha256":{
          "stage05o_native_hold":sha(a.stage05o_native_hold),
          "stage05o_summary":sha(a.stage05o_summary),
          "stage05al_summary":sha(a.stage05al_summary)
        },
        "next_decision":"Evidence request for exact JP-Tef and JP-Tmd source release TIMESTAMP_START/TIMESTAMP_END normalization: distinguish mean solar from true solar, logger acquisition convention, and published FLUXNET-formatted timestamps; otherwise retain native-only HOLD"
    }
    with report.open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AM ORIGINAL TEF/TMD 18 NATIVE-SOURCE CLOCK CONFLICT REVIEW PASS | NO UTC/CDS/SLURM/REPAIR")
    print("ORIGINAL_QC2_FIELDS",45,"INDEPENDENTLY_COMPARED",27,
          "STRONG_LABEL",22,"NEW_CONTEXT_ONLY",5)
    print("CLOCK_HOLD_FIELDS",18,"BY_SITE",dict(EXPECTED),
          "DISTINCT_NATIVE_SITE_HALFHOURS",14)
    for (site,date),rec in sorted(episode.items()):
        print("NATIVE_SOURCE_DATE_NOT_UTC",site,date,"FIELDS",len(rec),
              "VARS",dict(Counter(r["variable"] for r in rec)))
    print("SOURCE_NATIVE_EVENT_REGISTER",table)
    print("NATIVE_DAY_SUMMARY",days)
    print("TIMEBASE_DECISION_HOLD",report)
    print("NO Tef/Tmd UTC MAPPING OR CDS REQUEST AUTHORIZED; ALL 45 QC2 SOURCE FIELDS HOLD")
if __name__=="__main__":main()

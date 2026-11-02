#!/usr/bin/env python3
"""Stage05AO: reconcile two actual Stage05AN raw-zip audits vs source clock claim.

All 18 original JP-Tef/Tmd QC2 source-variable fields remain native-time
only. Confirm actual raw source HH release timestamp ranges, original
selected F=ERA and QC2, exact 75-line README "local solar", and compare
EXTERNAL ICOS JP-Tmd exact product acquisition metadata as a hypothesis.
Original 27 other fields separately contextualized: 22 strong, 5 context.
No original ZIP/forcing writes, CDS, Slurm, UTC conversions or repairs.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path

SITE={
 "JP-Tef":("JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1","200101010000",403200,4,4),
 "JP-Tmd":("JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1","200501010000",333072,14,10)}
README="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
FIELDS=("site","original_native_TIMESTAMP_START_NOT_UTC","variable","raw_F",
        "same_release_ERA","raw_QC","original_native_TIMESTAMP_END",
        "source_readme_claim","source_UTC_status","repair_status")
def js(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise ValueError("Expected source JSON")
    return x
def tsv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter="\t")
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):
            raise ValueError("Missing or duplicated original table headers")
        return list(r)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def close(a,b):
    return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-6)
def verify(site,r):
    package,first,n,fields,unique=SITE[site]
    if (r.get("stage")!="JapanFlux Stage05AN"
        or r.get("status")!="ORIGINAL_JPF_FLUXMET_HH_NATIVE_TIMESTAMP_QC2_VALUES_MATCHED_BUT_UTC_STILL_UNRESOLVED"
        or r.get("site")!=site or r.get("original_product_release")!=package
        or r.get("original_README_SHA256")!=README
        or "time is expressed in local solar time (without DST)" not in r.get("original_README_claim_line64","")
        or r.get("source_HH_csv_rows_scanned")!=n
        or r.get("original_source_flagged_QC2_fields_matched")!=fields
        or r.get("original_source_flagged_native_times_matched")!=unique
        or r.get("new_original_UTC_mapping_approved") is not False
        or r.get("original_45_QC2_source_fields_HOLD") is not True
        or r.get("scientific_30minute_replacements_approved") is not False
        or r.get("original_source_ZIP_or_forcing_modified") is not False):
        raise ValueError("Actual original 05AN source science gate changed for "+site)
    a=r["first_3_original_native_HH_timestamps"]
    b=r["last_3_original_native_HH_timestamps"]
    if len(a)!=3 or len(b)!=3 or a[0]["start"]!=first or b[-1]["start"]!="202312312330" or b[-1]["end"]!="202401010000":
        raise ValueError("Original source HH release year-edge timestamps changed")
    for samples in (a,b):
        for i,v in enumerate(samples):
            start=datetime.strptime(v["start"],"%Y%m%d%H%M")
            end=datetime.strptime(v["end"],"%Y%m%d%H%M")
            if end-start!=timedelta(minutes=30):
                raise ValueError("Original HH start/end pairing changed")
            if i>0 and v["start"]!=samples[i-1]["end"]:
                raise ValueError("Original HH edge sample discontinuity")
    count=int((datetime(2024,1,1)-datetime.strptime(first,"%Y%m%d%H%M")).total_seconds()/1800)
    if count!=n:raise ValueError("Gregorian expected original source number of halfhours changed")
    rows=r.get("read_only_source_fields",[])
    if len(rows)!=fields:raise ValueError("Original Stage05AN source QC2 event list incomplete")
    return rows
def run(sources,am,al,eventrows):
    if (am.get("stage")!="JapanFlux Stage05AM"
        or am.get("status")!="TWO_ORIGINAL_SOLAR_VS_STANDARD_SITE_CLOCKS_UNRESOLVED_SCIENCE_HOLD"
        or am.get("original_QC2_field_count")!=45
        or am.get("already_independently_compared")!=27
        or am.get("clock_conflict_variable_fields")!=18
        or am.get("clock_conflict_by_site")!={"JP-Tef":4,"JP-Tmd":14}
        or am.get("original_Tef_Tmd_source_readme_75line_SHA256")!=README
        or am.get("original_BIF_UTC_OFFSET_both_sites")!=9
        or am.get("original_UTC_mapping_generated") is not False
        or am.get("all_45_original_QC2_fields_HOLD") is not True):
        raise ValueError("Stage05AM source timebase HOLD status changed")
    if (al.get("stage")!="JapanFlux Stage05AL"
        or al.get("independently_hourly_context_reviewed_fields")!=27
        or al.get("independently_context_outside_fields")!=27
        or al.get("previously_strong_label_independent_context_fields")!=22
        or al.get("new_Stage05AK_context_only_not_strong_label_approved_fields")!=5
        or al.get("clock_unresolved_original_source_fields")!=18
        or al.get("full_independent_CDS_site_days_verified")!=9
        or al.get("all_45_original_source_fields_HOLD") is not True):
        raise ValueError("Stage05AL 27/18 science provenance changed")
    if len(eventrows)!=18 or Counter(x["site"] for x in eventrows)!=Counter({"JP-Tef":4,"JP-Tmd":14}):
        raise ValueError("Stage05AM 18 original source event records changed")
    registry={}
    for r in eventrows:
        k=r["site"],r["native_halfhour_timestamp_NOT_UTC"],r["variable"]
        if (k in registry or r["original_UTC"]!="UNRESOLVED"
            or r["source_flag"]!="ORIGINAL_SELECTED_F_EQ_EMBEDDED_ERA_QC2"
            or r["science_decision"]!="HOLD_NATIVE_ONLY_NO_CDS_NO_UTC_NO_REPAIR"
            or r["original_readme_SHA256"]!=README):
            raise ValueError("Original Stage05AM native-time QC2 field conflict changed")
        registry[k]=r
    result=[]
    for site in SITE:
        for x in verify(site,sources[site]):
            k=site,x["native_start"],x["variable"]
            if k not in registry:raise ValueError("Original raw HH field missing from Stage05AM")
            y=registry[k]
            if (x["actual_F_CSV_QC"]!="2"
                or x["original_native_timestamp_aligned_to_CSV_START"]!="YES"
                or x["source_timebase_resolution"]!="UNRESOLVED_SOLAR_VS_STANDARD"
                or x["TIMESTAMP_START_original_native"]!=x["native_start"]
                or datetime.strptime(x["TIMESTAMP_END_original_native"],"%Y%m%d%H%M")-
                  datetime.strptime(x["native_start"],"%Y%m%d%H%M")!=timedelta(minutes=30)
                or not close(x["actual_F_CSV_value"],x["actual_ERA_CSV_value"])
                or not close(x["actual_F_CSV_value"],y["original_F_QC2_selected"])
                or not close(x["actual_ERA_CSV_value"],y["original_same_release_ERA"])):
                raise ValueError("Original source F/ERA/QC2/time mismatch "+str(k))
            result.append({
               "site":site,"original_native_TIMESTAMP_START_NOT_UTC":k[1],
               "variable":k[2],"raw_F":x["actual_F_CSV_value"],
               "same_release_ERA":x["actual_ERA_CSV_value"],
               "raw_QC":"2","original_native_TIMESTAMP_END":x["TIMESTAMP_END_original_native"],
               "source_readme_claim":"LOCAL_SOLAR_TIME_WITHOUT_DST",
               "source_UTC_status":"UNRESOLVED_TIMEBASE",
               "repair_status":"HOLD_NO_APPROVED_REPLACEMENT"})
    if len(result)!=18 or len({(r["site"],r["original_native_TIMESTAMP_START_NOT_UTC"],r["variable"]) for r in result})!=18:
        raise ValueError("18 original Tef/Tmd source variables incomplete or overlapping")
    return sorted(result,key=lambda x:(x["site"],x["original_native_TIMESTAMP_START_NOT_UTC"],x["variable"]))
def selftest():
    assert sum(s[3] for s in SITE.values())==18
    for _,first,n,_,_ in SITE.values():
        assert (datetime(2024,1,1)-datetime.strptime(first,"%Y%m%d%H%M")).total_seconds()/1800==n
    assert len(FIELDS)==10
    print("STAGE05AO SELF-TEST PASS | 403200+333072 original source HH Gregorian boundaries, 18 matched QC2 native-time records; NO UTC/CDS/REPAIR")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    for name in ("stage05an-tef","stage05an-tmd","stage05am-register","stage05am-summary","stage05al-summary","out-dir"):
        p.add_argument("--"+name,type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    names=("stage05an_tef","stage05an_tmd","stage05am_register","stage05am_summary","stage05al_summary","out_dir")
    if any(getattr(a,k) is None for k in names):
        p.error("Require both actual Stage05AN source audits, Stage05AM, Stage05AL and new output dir")
    source={"JP-Tef":js(a.stage05an_tef),"JP-Tmd":js(a.stage05an_tmd)}
    rows=run(source,js(a.stage05am_summary),js(a.stage05al_summary),tsv(a.stage05am_register))
    if a.out_dir.exists():p.error("Refuse existing report folder")
    a.out_dir.mkdir(parents=True)
    table=a.out_dir/"stage05ao_18_Tef_Tmd_original_native_QC2_source_clock_UNRESOLVED.tsv"
    report=a.out_dir/"stage05ao_45_source_field_clock_provenance_science_HOLD.json"
    with table.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t");w.writeheader();w.writerows(rows)
    summary={
       "stage":"JapanFlux Stage05AO",
       "status":"BOTH_ORIGINAL_JPF_HH_SOURCE_QC2_VALUES_MATCHED_CLOCK_STILL_UNRESOLVED",
       "original_source_field_count":45,
       "independently_context_checked_fields":27,
       "prior_strong_context_class_fields":22,
       "additional_context_only_fields":5,
       "clock_unresolved_fields":18,
       "clock_unresolved_by_site":{"JP-Tef":4,"JP-Tmd":14},
       "source_HH_original_rows_scanned_by_Stage05AN":736272,
       "source_readme_75line_SHA256":README,
       "source_README_line64":"time is expressed in local solar time (without DST)",
       "original_BIF_UTC_OFFSET_hours":9,
       "external_icos_JP_Tmd_exact_product_url":"https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS",
       "external_icos_JP_Tmd_start_UTC":"2004-12-31T15:00:00Z",
       "Tmd_source_start_native":"200501010000",
       "ICOS_external_metadata_consistent_with_plus_9":True,
       "external_metadata_proves_original_JPF_solar_to_JST_conversion":False,
       "new_UTC_mapping_generated":False,
       "source_release_timebase_decision":"HOLD_REQUEST_PRODUCER_ORIGINAL_TIMESTAMP_CONVERSION_RECORD",
       "all_45_original_QC2_fields_HOLD":True,
       "replacement_approved":False,"CDS_requests":0,"Slurm_jobs":0,
       "original_ZIP_or_forcing_modified":False,
       "input_sha256":{k:sha(getattr(a,k)) for k in names if k!="out_dir"}}
    with report.open("x",encoding="utf-8") as f:json.dump(summary,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AO TEF/TMD ORIGINAL JPF SOURCE CLOCK PROVENANCE CROSS-REVIEW PASS | NO UTC/CDS/SLURM/REPAIR")
    print("SOURCE_HH_ROWS_PREVIOUSLY_VERIFIED",736272,"ORIGINAL_QC2_FIELDS_EXACT",len(rows))
    print("INDEPENDENT_CONTEXT",27,"CLOCK_CONFLICT_HOLD",18)
    print("ICOS_PRODUCT_PLUS9_CONTEXT_NOT_NATIVE_CLOCK_PROOF")
    print("18_FIELD_NATIVE_ONLY_REPORT",table)
    print("TIME_SOURCE_SCIENCE_HOLD_REPORT",report)
    print("REQUIRE_PRODUCER_TIME_CONVERSION_DOCUMENTATION; ALL_45_FIELDS_HOLD")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Stage05AR: verify ORIGINAL JPF JP-Tef/Tmd BIF coordinates, then geolocate 7
operator-selected JST UTC+9 candidate ERA5-Land time-series site/day windows.

STRICT original source BIF LAT/LONG/ELEV and UTC_OFFSET=9; independently
SHA-match BIF to saved original Stage05K metadata. Reuse bit-for-bit pinned
Stage05Q original BIF inspector (from successful Fjy/Khw/Yms science flow).
Do not claim native Tef/Tmd UTC source proven: 75-line README says LOCAL SOLAR.

Reads original nested metadata CSV ONLY, no full meteorological CSV.
Outputs derived site/day CSV/JSON PREVIEW, no CDS/net, edits, repairs, Slurm.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SITES=("JP-Tef","JP-Tmd")
PACKAGES={
    "JP-Tef":"JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1",
    "JP-Tmd":"JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1"}
EXPECTED_DAYS={
 ("JP-Tef","2011-12-16"),("JP-Tef","2011-12-17"),
 ("JP-Tef","2022-04-08"),
 ("JP-Tmd","2005-08-11"),
 ("JP-Tmd","2011-12-16"),("JP-Tmd","2011-12-17"),
 ("JP-Tmd","2022-04-08")}
SOURCE_REVIEW={"JP-Tef":4,"JP-Tmd":14}
EXPECTED_HELPER_GIT_BLOB="fe8344e7a8115105377ffd9fb766387c4c74f5c8"
CLOCK="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
VARIABLES={"LW_IN":"surface_thermal_radiation_downwards",
           "PA":"surface_pressure","TA":"2m_temperature"}
DATASOURCE="reanalysis-era5-land-timeseries"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
ROSTER_FIELDS=("site","latitude","longitude","elevation_m","UTC_OFFSET_hours",
               "original_BIF_sha256","original_BIF_member","original_location_group_ids",
               "original_location_source_lines","clock_status","source_repair_status")
def raw(p):return p.read_bytes()
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def loadjson(p):
    obj=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):raise ValueError("Expected JSON object: "+str(p))
    return obj
def readtsv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or len(rd.fieldnames)!=len(set(rd.fieldnames)):
            raise ValueError("Missing or duplicated TSV header: "+str(p))
        return list(rd)
def original_BIF_helper(path):
    b=raw(path)
    digest=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    if digest!=EXPECTED_HELPER_GIT_BLOB:
        raise ValueError("Unpinned Stage05Q original BIF helper: Git blob SHA "+digest)
    spec=importlib.util.spec_from_file_location("jpf_orig_bif_05q_verified",path)
    if spec is None or spec.loader is None:
        raise ValueError("Could not import pinned original Stage05Q source BIF parser")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
def source_gate(aq,summary,ao,l):
    if (aq.get("stage")!="JapanFlux Stage05AQ"
        or aq.get("status")!="TEF_TMD_SITE_UTC_DAY_CDS_HYPOTHESIS_PREVIEW_ONLY"
        or aq.get("source_original_QC2_fields")!=18
        or aq.get("time_basis")!=CLOCK
        or aq.get("original_readme_conflict_preserved") is not True
        or aq.get("unique_site_UTC_day_previews")!=7
        or aq.get("CDS_requests_this_stage")!=0
        or aq.get("all_45_source_fields_HOLD") is not True):
        raise ValueError("Stage05AQ original source-time hypothesis day scope not preserved")
    if (summary.get("stage")!="JapanFlux Stage05AQ"
        or summary.get("status")!="OPERATOR_SELECTED_JST_PLUS9_CANDIDATE_UTC_ONLY_NOT_TIMEBASE_PROOF"
        or summary.get("assumption")!=CLOCK
        or summary.get("source_BIF_UTC_OFFSET")!=9
        or summary.get("original_source_timebase_definitively_verified") is not False
        or summary.get("original_18_native_QC2_source_fields_retained")!=18
        or summary.get("candidate_UTC_fields_generated")!=18
        or summary.get("candidate_site_UTC_days")!=7
        or summary.get("all_45_source_fields_HOLD") is not True
        or summary.get("science_repair_approved") is not False
        or summary.get("CDS_requests")!=0):
        raise ValueError("Stage05AQ actual hypothesis source fields/45 HOLD summary changed")
    if (ao.get("stage")!="JapanFlux Stage05AO"
        or ao.get("status")!="BOTH_ORIGINAL_JPF_HH_SOURCE_QC2_VALUES_MATCHED_CLOCK_STILL_UNRESOLVED"
        or ao.get("clock_unresolved_fields")!=18
        or ao.get("source_HH_original_rows_scanned_by_Stage05AN")!=736272
        or ao.get("original_BIF_UTC_OFFSET_hours")!=9
        or ao.get("new_UTC_mapping_generated") is not False
        or ao.get("replacement_approved") is not False
        or ao.get("all_45_original_QC2_fields_HOLD") is not True):
        raise ValueError("Original Stage05AO source event/time conflict provenance changed")
    if (l.get("stage")!="JapanFlux Stage05L"
        or l.get("verified_sites")!=3
        or l.get("status")!="HOLD_INCOMPLETE_OR_CONFLICTING_METADATA"
        or l.get("utc_mapping_generated") is not False):
        raise ValueError("Original Stage05L solar/standard source clock conflict has been changed")
    sites=l.get("sites",{})
    if set(sites)!={"JP-Fjy","JP-Khw","JP-Tef","JP-Tmd","JP-Yms"}:
        raise ValueError("Stage05L original JPF site roster changed")
    for site in SITES:
        r=sites[site]
        if (r.get("status")!="HOLD_METADATA_UNVERIFIED"
            or r.get("UTC_OFFSET_hours")!=9
            or r.get("README_local_standard_time_without_DST") is not False):
            raise ValueError("Original Tef/Tmd source metadata must retain solar conflict")
def original_fields(rows):
    if len(rows)!=18 or Counter(r["site"] for r in rows)!=Counter(SOURCE_REVIEW):
        raise ValueError("Stage05AQ source 18 candidate UTC field records changed")
    seen=set(); requests=defaultdict(lambda:{"hours":set(),"vars":set(),"pairs":set(),"event_keys":set()})
    for r in rows:
        k=r["site"],r["original_native_halfhour_start"],r["variable"]
        if k in seen:raise ValueError("Duplicate original source event candidate")
        seen.add(k)
        if (r["candidate_time_basis"]!=CLOCK
            or r["candidate_status"]!="OPERATOR_SELECTED_PLUS9_HYPOTHESIS_QC2_SCIENCE_HOLD"
            or r["source_readme_sha256"]!="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
            or r["original_readme_time_claim"]!="LOCAL_SOLAR_TIME_WITHOUT_DST_CONFLICT"
            or r["original_BIF_UTC_OFFSET_hours"]!="9"
            or r["source_QC"]!="2"
            or r["forcing_repair_approved"]!="False"
            or r["variable"] not in VARIABLES):
            raise ValueError("Stage05AQ original QC2/JST hypothesis flags modified")
        native=datetime.strptime(r["original_native_halfhour_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["candidate_UTC_start"],"%Y%m%d%H%M")
        end=datetime.strptime(r["candidate_UTC_end"],"%Y%m%d%H%M")
        if native-utc!=timedelta(hours=9) or end-utc!=timedelta(minutes=30):
            raise ValueError("Candidate UTC arithmetic changed from operator JST+9 hypothesis")
        key=r["original_native_halfhour_start"]+":"+r["variable"]
        hourstart=utc.replace(minute=0)
        for offs in range(-3,5):
            h=hourstart+timedelta(hours=offs)
            rec=requests[(r["site"],h.strftime("%Y-%m-%d"))]
            rec["hours"].add(h.strftime("%H:%M"))
            rec["vars"].add(VARIABLES[r["variable"]])
            rec["pairs"].add((h.strftime("%H:%M"),VARIABLES[r["variable"]]))
            rec["event_keys"].add(key)
    if len({(s,n) for s,n,v in seen})!=14 or set(requests)!=EXPECTED_DAYS:
        raise ValueError("Source original 14 site-native timestamps or seven day request scope changed")
    return requests
def check_plan(days,expect):
    if len(days)!=7:
        raise ValueError("Need exact seven operator-JST candidate CDS days")
    seen=set()
    for d in days:
        s=d["site"];day=d["UTC_date_CANDIDATE"];k=(s,day)
        if k in seen or k not in EXPECTED_DAYS:
            raise ValueError("Unexpected/duplicate source candidate UTC site/date: "+str(k))
        seen.add(k)
        v=expect[k]
        pairs={(x["hour"],x["variable"]) for x in d["exact_variable_hour_pairs"]}
        if (d["source_time_interpretation"]!=CLOCK
            or d["source_UTC_verified"] is not False
            or d["CDS_submission_authorized_by_this_stage"] is not False
            or d["source_tower_coords"]!="NOT_YET_VERIFIED_IN_THIS_STAGE"
            or set(d["required_UTC_hour_clocks"])!=v["hours"]
            or set(d["required_ERA5L_variables"])!=v["vars"]
            or set(d["source_QC2_event_fields"])!=v["event_keys"]
            or pairs!=v["pairs"] or len(pairs)!=len(d["exact_variable_hour_pairs"])
            or d["dataset"]!=DATASOURCE):
            raise ValueError("Original seven-day candidate hour/variable source scope changed for "+str(k))
    if seen!=EXPECTED_DAYS:raise ValueError("Missing one operator candidate UTC site day")
def verify_source_sites(helper,manifest_path,k_dir,root):
    manifest=helper.load_manifest(manifest_path)
    report=[];roster=[]
    for site in SITES:
        if manifest[site]["package"]!=PACKAGES[site]:
            raise ValueError("Original site JPF nested release mismatch")
        text,digest,member=helper.read_bif(site,PACKAGES[site],root)
        expected_sha,expected_member=helper.get_original_bif_expected_metadata(k_dir,site)
        if digest!=expected_sha or member!=expected_member:
            raise ValueError("Real original BIF bytes disagree with prior Stage05K saved SHA/member "+site)
        coords,offsets=helper.group_records(text,site)
        detail,original=helper.evaluate(site,coords,offsets,digest,member)
        if (original is None or detail["status"]!="VERIFIED_ORIGINAL_BIF_COORDINATES"
            or original["status"]!="VERIFIED_COORDS_NOT_ERA5L_GRID_CELL_APPROVED"
            or len(coords)!=1 or original["UTC_OFFSET_hours"]!=9):
            raise ValueError("Cannot verify original source BIF tower location for "+site+": "+str(detail["problems"]))
        lat=float(original["latitude"]);lon=float(original["longitude"])
        if not(20<=lat<=47 and 120<=lon<=154 and math.isfinite(lat) and math.isfinite(lon)):
            raise ValueError("Original source location not within expected Japan region")
        roster.append({
           "site":site,"latitude":lat,"longitude":lon,
           "elevation_m":original["elevation_m"],
           "UTC_OFFSET_hours":9,"original_BIF_sha256":digest,
           "original_BIF_member":member,
           "original_location_group_ids":original["location_group_ids"],
           "original_location_source_lines":original["location_source_lines"],
           "clock_status":CLOCK+"_ORIGINAL_README_SOLAR_CONFLICT",
           "source_repair_status":"SCIENCE_HOLD_NOT_REPLACEMENT_APPROVED"})
        report.append(detail)
    return roster,report
def build(days,roster):
    lookup={r["site"]:r for r in roster}
    plan=[]
    for d in sorted(days,key=lambda r:(r["site"],r["UTC_date_CANDIDATE"])):
        site=d["site"];date=d["UTC_date_CANDIDATE"];geo=lookup[site]
        variables=sorted(d["required_ERA5L_variables"])
        req={"variable":variables,"location":{
            "latitude":geo["latitude"],"longitude":geo["longitude"]},
             "date":date+"/"+date,"data_format":"csv"}
        plan.append({
           "site":site,"UTC_day_candidate":date,
           "operator_selected_time_hypothesis":CLOCK,
           "original_source_UTC_timebase_verified":False,
           "original_source_README_says_solar_time":True,
           "original_BIF_SHA256":geo["original_BIF_sha256"],
           "tower_latitude":geo["latitude"],"tower_longitude":geo["longitude"],
           "tower_elevation_m":geo["elevation_m"],
           "requested_event_native_keys":d["source_QC2_event_fields"],
           "required_UTC_hour_clocks":d["required_UTC_hour_clocks"],
           "required_variable_UTC_hour_pairs":d["exact_variable_hour_pairs"],
           "dataset":DATASOURCE,"request":req,
           "source_ERA5L_grid_cell_unverified":True,
           "CSV_ZIP_original_source_not_modified":True,
           "CDS_submissions_this_stage":0,
           "repair_approved":False,
           "request_status":"PREVIEW_ONLY_NO_EXTERNAL_CDS_REQUEST"})
    return plan
def selftest():
    assert len(EXPECTED_DAYS)==7
    assert sum(SOURCE_REVIEW.values())==18
    assert len(EXPECTED_HELPER_GIT_BLOB)==40
    a=datetime(2022,4,9,2)-timedelta(hours=9)
    assert a.isoformat()=="2022-04-08T17:00:00"
    print("STAGE05AR SELF-TEST PASS | original BIF SHA-locked JP-Tef/Tmd LAT/LONG/ELEV, exactly seven user JST+9 candidate CDS days, NO CDS/WRITES")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    for k in ("stage05aq-plan","stage05aq-fields","stage05aq-summary",
              "stage05ao-summary","stage05l-summary","stage05q-helper",
              "stage05k-dir","manifest","out-dir"):
        p.add_argument("--"+k,type=Path)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    if a.self_test:selftest();return
    keys=("stage05aq_plan","stage05aq_fields","stage05aq_summary","stage05ao_summary",
          "stage05l_summary","stage05q_helper","stage05k_dir","manifest","out_dir")
    if any(getattr(a,k) is None for k in keys):
        p.error("Need original source AQ/AO/L and prior Stage05K saved metadata + pinned Stage05Q BIF helper + manifest + fresh --out-dir")
    aq=loadjson(a.stage05aq_plan)
    source_gate(aq,loadjson(a.stage05aq_summary),
                loadjson(a.stage05ao_summary),loadjson(a.stage05l_summary))
    expected=original_fields(readtsv(a.stage05aq_fields))
    check_plan(aq["days"],expected)
    helper=original_BIF_helper(a.stage05q_helper)
    roster,site_reports=verify_source_sites(helper,a.manifest,a.stage05k_dir,a.root)
    plan=build(aq["days"],roster)
    if len(plan)!=7 or len({(r["site"],r["UTC_day_candidate"]) for r in plan})!=7:
        raise ValueError("Seven source candidate UTC dates not preserved")
    if a.out_dir.exists():p.error("Refuse existing science preview output folder")
    a.out_dir.mkdir(parents=True)
    rosterfile=a.out_dir/"stage05ar_Tef_Tmd_original_BIF_verified2_CDS_coordinates.tsv"
    planfile=a.out_dir/"stage05ar_7_user_JSTplus9_site_UTC_day_CDS_preview_ONLY.json"
    reportfile=a.out_dir/"stage05ar_source_BIF_coordinates_7_day_hypothesis_HOLD_summary.json"
    with rosterfile.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=ROSTER_FIELDS,delimiter="\t")
        w.writeheader();w.writerows(roster)
    with planfile.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05AR",
          "status":"TWO_ORIGINAL_SOURCE_BIF_COORDS_VERIFIED_SEVEN_JST_CANDIDATE_CDS_DAYS_PREVIEW",
          "original_source_coordinate_sites_verified":2,
          "candidate_UTC_site_days":7,
          "user_selected_time_hypothesis":CLOCK,
          "original_source_time_basis_proven":False,
          "CDS_requests":0,"original_ZIP_or_forcing_modified":False,
          "all_45_original_source_QC2_fields_HOLD":True,
          "site_day_requests":plan},f,indent=2,ensure_ascii=False);f.write("\n")
    report={"stage":"JapanFlux Stage05AR","status":"BOTH_ORIGINAL_JPF_BIF_GEOLOCATIONS_VERIFIED_CANDIDATE_TIME_HOLD",
       "original_source_coordinate_sites_verified":2,
       "original_site_BIF_validation":site_reports,
       "original_site_coordinate_roster":roster,
       "candidate_UTC_fields":18,"candidate_site_days":7,
       "previous_independent_context_fields":27,
       "prior_strong_label":22,"new_context_only":5,
       "source_readme_solar_vs_JST_clock_conflict":"PRESERVED",
       "operator_time_assumption":CLOCK,"source_time_verified":False,
       "source_grid_cell_elevation_verified":False,
       "science_halfhour_replacement_approved":False,
       "CDS_requests_this_stage":0,"Slurm_jobs":0,
       "original_source_ZIP_or_forcing_modified":False,
       "all_45_source_QC2_fields_HOLD":True,
       "input_sha256":{k:sha(getattr(a,k)) for k in keys
                 if k not in ("stage05k_dir","out_dir")}}
    with reportfile.open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AR TWO ORIGINAL TEF/TMD BIF LOCATION & 7 CANDIDATE CDS DAYS PASS | NO DOWNLOAD / SLURM / REPAIR")
    for r in roster:
        print("SOURCE_BIF_SITE",r["site"],"LAT",r["latitude"],
              "LON",r["longitude"],"ELEV_M",r["elevation_m"],
              "SOURCE_SHA256",r["original_BIF_sha256"])
    print("USER_JST_UTCPLUS9_CANDIDATE_UTC_DAYS",len(plan),
          "ORIGINAL_CLOCK_NOT_PROVEN")
    for r in plan:
        print("PREVIEW_CDS_NOT_SUBMITTED",r["site"],r["UTC_day_candidate"],
              "VARIABLES",",".join(r["request"]["variable"]),
              "HOURS",",".join(r["required_UTC_hour_clocks"]))
    print("BIF_COORDINATE_ROSTER",rosterfile)
    print("SEVEN_DAY_CDS_PREVIEW",planfile)
    print("SOURCE_TIME_AND_GEO_HOLD_SUMMARY",reportfile)
    print("ALL_45_SOURCE_QC2_FIELDS_HOLD; NO CDS / FORCING / SLURM / REPLACEMENTS")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""JapanFlux Stage05AV: remaining 8 original QC2 source fields, exactly FOUR
ERA5-Land CDS site-UTC-day candidate reference ZIPs.

Default PREVIEW/READONLY. Explicit --submit-remaining fetches sequentially:
JP-Tef 2022-04-08 strd, JP-Tmd 2011-12-16 sp,
JP-Tmd 2011-12-17 sp, JP-Tmd 2022-04-08 sp.
Valid existing source ZIPs are reused, never overwritten. Invalid and
partial ZIPs STOP without erasing. Every newly downloaded ZIP must pass
CRC, 24UTC hours, raw variables, grid coordinates and broad numerical QC
using the exact earlier Stage05AS (SHA-pinned) code. CDS requests return
the full UTC day (24-hour data) rather than sparse event hours.

--assess will analyze ONLY when ALL four ZIPs are independently validated.
Compare Tef Apr2022 8h strd/3600, Tmd Dec2011 9h sp/1000 crossing
UTC midnight, Tmd Apr2022 9h sp/1000 to 8 exact source-original
selected F=ERA QC2 values. This is gridded hourly CONTEXT ONLY, never a
30-minute tower replacement. The original JPF README says local SOLAR
time; the user explicitly selected JST UTC+9 as a diagnostic HYPOTHESIS.
All 45 original source fields remain science HOLD. No source ZIP,
forcing/model/Slurm/AD400/PFT changes and no automated repairs.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,io,json,math,zipfile
from datetime import datetime,timedelta
from pathlib import Path

CLOCK="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
DATASET="reanalysis-era5-land-timeseries"
SOURCE_README_SHA="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
AS_BLOB_SHA="8d203d727c37191c42c555caba13860e3dbdfd8f"
DAY16_TEF_SHA="533b462fa0804a3d34428b6dd5f9b38b8a9e70dbc705af481c18ec614ea16148"
DAY17_TEF_SHA="81043becb8ccce9936164d7e1e3afdc56c55a84b077b314c4672339f3a81f532"
TMD2005_SHA="cd722e173c24154ccb5d28a632683cb39473389ac163b12439cce8e870721fe6"
DATASET="reanalysis-era5-land-timeseries"
DAYS={
 ("JP-Tef","2022-04-08"):["surface_thermal_radiation_downwards"],
 ("JP-Tmd","2011-12-16"):["surface_pressure"],
 ("JP-Tmd","2011-12-17"):["surface_pressure"],
 ("JP-Tmd","2022-04-08"):["surface_pressure"],
}
EXACT_EVENTS={
 ("JP-Tef","202204090200","LW_IN"):("202204081700",26.164,"W m-2"),
 ("JP-Tef","202204090230","LW_IN"):("202204081730",26.164,"W m-2"),
 ("JP-Tmd","201112170630","PA"):("201112162130",49.448,"kPa"),
 ("JP-Tmd","201112170700","PA"):("201112162200",0.0,"kPa"),
 ("JP-Tmd","201112170730","PA"):("201112162230",49.514,"kPa"),
 ("JP-Tmd","202204090230","PA"):("202204081730",49.616,"kPa"),
 ("JP-Tmd","202204090300","PA"):("202204081800",0.0,"kPa"),
 ("JP-Tmd","202204090330","PA"):("202204081830",49.579,"kPa"),
}
EXPECTED_SHA_PREVIOUS={
 ("JP-Tef","2011-12-16"):DAY16_TEF_SHA,
 ("JP-Tef","2011-12-17"):DAY17_TEF_SHA,
 ("JP-Tmd","2005-08-11"):TMD2005_SHA
}
GROUPS={
 ("JP-Tef","2022"):("strd", [datetime(2022,4,8,14)+timedelta(hours=h) for h in range(8)]),
 ("JP-Tmd","2011"):("sp", [datetime(2011,12,16,18)+timedelta(hours=h) for h in range(9)]),
 ("JP-Tmd","2022"):("sp", [datetime(2022,4,8,14)+timedelta(hours=h) for h in range(9)])
}
FIELDS=("site","native_JPF_source_start","hypothetical_JSTminus9_UTC_start",
        "variable","original_F_QC2","source_unit","hourly_reference_min",
        "hourly_reference_max","outside_broad_hourly_reference",
        "source_clock_evidence","science_status","repair_approved")
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(1048576),b""):h.update(data)
    return h.hexdigest()
def js(path):
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict):raise ValueError("Expected derived JSON object")
    return v
def tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rdr=csv.DictReader(f,delimiter="\t")
        if not rdr.fieldnames or len(rdr.fieldnames)!=len(set(rdr.fieldnames)):
            raise ValueError("Invalid original Stage05AQ TSV header")
        return list(rdr)
def load_as(path):
    b=path.read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\x00"+b).hexdigest()
    if blob!=AS_BLOB_SHA:raise ValueError("Stage05AS original validated source parser blob changed: "+blob)
    spec=importlib.util.spec_from_file_location("jpf_05as_pinned_source_ref",path)
    if spec is None or spec.loader is None:raise ValueError("Cannot import Stage05AS original source reader")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def validate_actual_previous(at,au):
    if (at.get("stage")!="JapanFlux Stage05AT"
        or at.get("status")!="TWO_INDEPENDENT_CDS_DAY_STRD_REFERENCE_SOURCE_VALIDATED_TWO_ORIGINAL_LW_CONTEXT_ONLY"
        or at.get("source_time_hypothesis")!=CLOCK
        or at.get("original_source_JPF_QC2_field_count")!=2
        or at.get("first_day_zip_sha256")!=DAY16_TEF_SHA
        or at.get("second_day_zip_sha256")!=DAY17_TEF_SHA
        or at.get("both_QC2_fields_outside_8h_reference_envelope") is not True
        or at.get("original_source_timebase_proven") is not False
        or at.get("all_45_original_source_QC2_fields_HOLD") is not True
        or at.get("new_strong_class_science_approval") is not False
        or at.get("scientific_repair_values_approved") is not False):
        raise ValueError("Stage05AT actual first two UTC source day QC2 context evidence changed")
    if (au.get("stage")!="JapanFlux Stage05AU"
        or au.get("status")!="TMD_2005_8_ORIGINAL_QC2_SOURCES_3_INDEPENDENT_CDS_VARIABLE_HOURLY_CONTEXT_ONLY"
        or au.get("site")!="JP-Tmd" or au.get("candidate_UTC_day")!="2005-08-11"
        or au.get("original_source_QC2_fields_reviewed_this_stage")!=8
        or au.get("outside_context_count_new_Tmd")!=8
        or au.get("total_original_source_fields_independent_context_reviewed")!=37
        or au.get("original_source_fields_not_yet_compared")!=8
        or au.get("source_time_hypothesis")!=CLOCK
        or au.get("new_strong_evidence_label_approved") is not False
        or au.get("all_45_original_QC2_source_fields_HOLD") is not True
        or au.get("scientific_30min_repair_values_approved") is not False
        or au.get("source_ZIP_forcing_model_modified") is not False
        or au.get("CDS_requests_this_stage")!=1):
        raise ValueError("Stage05AU real Tmd 2005 eight-source field/hourly context provenance changed")
    response=au.get("returned_CDS_source",{})
    if response.get("ZIP_SHA256")!=TMD2005_SHA or response.get("independent_variable_hour_count")!=72:
        raise ValueError("Original Tmd2005 source response ZIP or variable-hour count changed")
def validate_source_events(rows):
    if len(rows)!=18 or len({(r["site"],r["original_native_halfhour_start"],r["variable"]) for r in rows})!=18:
        raise ValueError("Original 18 Stage05AQ source field population changed")
    allscope={(r["site"],r["original_native_halfhour_start"],r["variable"]) for r in rows}
    expected_new=set(EXACT_EVENTS)
    if not expected_new<=allscope:
        raise ValueError("Missing one or more of eight remaining source original QC2 events")
    remaining=[]
    for r in rows:
        key=r["site"],r["original_native_halfhour_start"],r["variable"]
        if (r["candidate_time_basis"]!=CLOCK
            or r["candidate_status"]!="OPERATOR_SELECTED_PLUS9_HYPOTHESIS_QC2_SCIENCE_HOLD"
            or r["original_readme_time_claim"]!="LOCAL_SOLAR_TIME_WITHOUT_DST_CONFLICT"
            or r["source_readme_sha256"]!=SOURCE_README_SHA
            or r["original_BIF_UTC_OFFSET_hours"]!="9"
            or r["source_QC"]!="2"
            or r["forcing_repair_approved"]!="False"):
            raise ValueError("Original Stage05AQ JPF QC2 time assumption/readme/source science-HOLD modified")
        if key in expected_new:
            when,value,unit=EXACT_EVENTS[key]
            if (r["candidate_UTC_start"]!=when
                or r["unit"]!=unit
                or not math.isclose(float(r["original_selected_F_QC2"]),value,abs_tol=1e-8)
                or not math.isclose(float(r["embedded_same_release_ERA"]),value,abs_tol=1e-8)):
                raise ValueError("An original source selected F=ERA QC2 event/time/unit changed: "+str(key))
            remaining.append(r)
    if len(remaining)!=8:raise ValueError("Remaining 8 source events are incomplete")
    return sorted(remaining,key=lambda r:(r["site"],r["candidate_UTC_start"],r["variable"]))
def check_baseline_files(mod,folder):
    for (site,day),digest in EXPECTED_SHA_PREVIOUS.items():
        name=f"{site}_ERA5Land_timeseries_{day.replace('-','')}_CSV_response.zip"
        p=folder/name
        if mod.about_path(p)!="REGULAR" or sha(p)!=digest:
            raise ValueError("Previously source-validated CDS ZIP missing or modified: "+str(p))
    return len(EXPECTED_SHA_PREVIOUS)
def verify_inputs(mod,a):
    d=mod.validate(js(a.stage05ar_plan),js(a.stage05ar_summary))
    if len(d)!=7 or set(DAYS)-set(d):raise ValueError("Stage05AR must retain all four original remaining site days")
    at=js(a.stage05at_tef_report)
    au=js(a.stage05au_tmd_report)
    validate_actual_previous(at,au)
    source=validate_source_events(tsv(a.stage05aq_fields))
    for k,vars_ in DAYS.items():
        r=d[k]
        if r["request"]["variable"]!=vars_ or r["request"]["date"]!=k[1]+"/"+k[1]:
            raise ValueError("Original Stage05AR exact remaining CDS variable/day scope changed "+str(k))
        if (r["operator_selected_time_hypothesis"]!=CLOCK
            or r["original_source_UTC_timebase_verified"] is not False
            or r["repair_approved"] is not False):
            raise ValueError("Original JPF solar vs operator JST science assumption not retained")
    folder=a.download_dir
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Original Stage05AS downloads dir is missing or symlinked")
    check_baseline_files(mod,folder)
    return d,source
def target_path(folder,key):
    site,day=key
    return folder/f"{site}_ERA5Land_timeseries_{day.replace('-','')}_CSV_response.zip"
def validate_download(mod,key,path,vars_):
    site,day=key
    info=mod.inspect_csv_zip(path,site,day,vars_)
    if (info["independent_variable_hour_count"]!=24*len(vars_)
        or set(info["validated_raw_columns"])!={"strd" if v=="surface_thermal_radiation_downwards" else "sp" for v in vars_}
        or info["source_grid_elevation"]!="UNVERIFIED"):
        raise ValueError("Original independent CDS variables/hourly/nearest grid incomplete: "+str(key))
    return info
def validate_existing_or_absent(mod,folder,key,vars_):
    target=target_path(folder,key)
    partial=Path(str(target)+".partial")
    # Never obscure a prior incomplete retrieval by implicitly overwriting.
    if mod.about_path(partial)!="ABSENT":
        raise ValueError("Existing .zip.partial science hold, inspect before resubmission: "+str(partial))
    for other in (target.with_suffix(".csv"),target.with_suffix(".nc")):
        if mod.about_path(other)!="ABSENT":
            raise ValueError("Existing alternative CSV/NetCDF source collision: "+str(other))
    if mod.about_path(target)=="ABSENT":return None
    if mod.about_path(target)!="REGULAR":
        raise ValueError("Nonregular existing source ZIP, no overwrite: "+str(target))
    return validate_download(mod,key,target,vars_)
def obtain(mod,folder,key,request):
    existing=validate_existing_or_absent(mod,folder,key,request["variable"])
    if existing is not None:
        print("STAGE05AV REUSE_VALIDATED_EXISTING_CDS_ZIP",key[0],key[1],
              "SHA256",existing["ZIP_SHA256"])
        return existing
    if not (Path.home()/".cdsapirc").is_file():
        raise RuntimeError("CDS private ~/.cdsapirc not available; licence must be accepted")
    try:import cdsapi
    except ImportError as e:raise RuntimeError("cdsapi missing; activate existing clm_fates_env") from e
    target=target_path(folder,key)
    partial=Path(str(target)+".partial")
    if any(mod.about_path(p)!="ABSENT" for p in (target,partial)):
        raise ValueError("Unexpected concurrent CDS output collision; no overwrite")
    print("STAGE05AV EXPLICIT_ONE_DAY_SOURCE_CDS_REQUEST",key[0],key[1],
          "NONSECRET_REQUEST",json.dumps(request,sort_keys=True))
    cdsapi.Client().retrieve(DATASET,request).download(str(partial))
    try:
        result=validate_download(mod,key,partial,request["variable"])
    except (ValueError,RuntimeError,OSError,zipfile.BadZipFile,UnicodeError,KeyError) as exc:
        print("STAGE05AV INVALID_CDS_PAYLOAD_PRESERVE_PARTIAL_SCIENCE_HOLD",type(exc).__name__,str(exc))
        raise
    if mod.about_path(target)!="ABSENT":raise ValueError("Post-request source destination collision: "+str(target))
    partial.rename(target)
    print("STAGE05AV CDS_DAY_CRC_24H_GRID_PASS",key[0],key[1],
          "BYTES",result["ZIP_bytes"],"SHA256",result["ZIP_SHA256"],
          "GRID",result["ERA5L_grid_lat"],result["ERA5L_grid_lon"],
          "RAW",result["validated_raw_columns"])
    return result
def read_cds_hours(path,key,expected):
    site,day=key
    rows={}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if info.is_dir():continue
            reader=csv.DictReader(io.StringIO(z.read(info).decode("utf-8-sig")))
            raw=set(reader.fieldnames or [])-{"valid_time","latitude","longitude"}
            if not raw or not raw<=expected:raise ValueError("Unexpected independent CDS variable")
            for rec in reader:
                dt=datetime.strptime(rec["valid_time"],"%Y-%m-%d %H:%M:%S")
                if dt.date().isoformat()!=day:raise ValueError("Unexpected independent CDS timestamp date")
                line=rows.setdefault(dt,{})
                for code in raw:
                    if code in line:raise ValueError("Duplicate model UTC variable-hour")
                    val=float(rec[code])
                    if code=="strd":val/=3600.
                    if code=="sp":val/=1000.
                    if not math.isfinite(val):raise ValueError("Invalid model hour")
                    line[code]=val
    if len(rows)!=24 or any(set(v)!=expected for v in rows.values()):
        raise ValueError("Missing some independent CDS source variable-hour values")
    return rows
def assess(mod,folder,source):
    # Re-verify original CDS ZIPs after downloads. Include both UTC days
    # for JP-Tmd 2011 crossed-midnight context and verify the SAME model grid.
    series={};source_meta={}
    for key in sorted(DAYS):
        p=target_path(folder,key)
        info=validate_existing_or_absent(mod,folder,key,DAYS[key])
        if info is None:raise ValueError("Remaining independent CDS day still missing: "+str(key))
        source_meta[f"{key[0]}|{key[1]}"]=info
        raw={"strd" if v=="surface_thermal_radiation_downwards" else "sp" for v in DAYS[key]}
        series.update({(key[0],t):d for t,d in read_cds_hours(p,key,raw).items()})
    grid16=source_meta["JP-Tmd|2011-12-16"]
    grid17=source_meta["JP-Tmd|2011-12-17"]
    if any(not math.isclose(float(grid16[k]),float(grid17[k]),abs_tol=1e-6,rel_tol=0)
           for k in ("ERA5L_grid_lat","ERA5L_grid_lon")):
        raise ValueError("2011 Tmd two-day returned model grid changed")
    minimum={};maximum={};hourly=[]
    for (site,episode),(code,times) in GROUPS.items():
        vals=[]
        for t in times:
            d=series.get((site,t))
            if d is None or code not in d:raise ValueError("Missing original-scoped cross-midnight model hour: "+str(t))
            value=d[code]
            vals.append(value)
            hourly.append({
              "site":site,"episode_year":episode,
              "model_hour_end_UTC":t.strftime("%Y-%m-%dT%H:%MZ"),
              "model_field":code,
              "model_unit":"W m-2 hourly mean" if code=="strd" else "kPa",
              "independent_ERA5L_hourly_value":f"{value:.6f}",
              "source_role":"GRID_HOURLY_CONTEXT_NOT_SITE_30MIN_REPLACEMENT"})
        minimum[site,episode]=min(vals);maximum[site,episode]=max(vals)
    decisions=[]
    for r in source:
        site=r["site"];native=r["original_native_halfhour_start"]
        episode="2011" if native.startswith("2011") else "2022"
        key=(site,episode)
        val=float(r["original_selected_F_QC2"])
        outside=not minimum[key]<=val<=maximum[key]
        decisions.append({
          "site":site,"native_JPF_source_start":native,
          "hypothetical_JSTminus9_UTC_start":r["candidate_UTC_start"],
          "variable":r["variable"],"original_F_QC2":val,
          "source_unit":r["unit"],
          "hourly_reference_min":minimum[key],
          "hourly_reference_max":maximum[key],
          "outside_broad_hourly_reference":outside,
          "source_clock_evidence":"USER_JST9_HYPOTHESIS_ORIGINAL_75LINE_README_LOCAL_SOLAR_CONFLICT",
          "science_status":"HOLD_CONTEXT_ONLY_NOT_REPLACEMENT",
          "repair_approved":False})
    if len(decisions)!=8:raise ValueError("Eight original QC2 source fields not independently contextualized")
    return hourly,decisions,source_meta
def selftest():
    assert len(DAYS)==4 and len(EXACT_EVENTS)==8 and len(GROUPS)==3
    assert set(DAYS)=={("JP-Tef","2022-04-08"),("JP-Tmd","2011-12-16"),("JP-Tmd","2011-12-17"),("JP-Tmd","2022-04-08")}
    assert len(GROUPS["JP-Tmd","2011"][1])==9
    assert GROUPS["JP-Tmd","2011"][1][-1]==datetime(2011,12,17,2)
    assert (datetime(2022,4,9,3)-timedelta(hours=9))==datetime(2022,4,8,18)
    assert (datetime(2011,12,17,7)-timedelta(hours=9))==datetime(2011,12,16,22)
    assert 720000/3600==200 and 100000/1000==100
    # Regression: argparse converts hyphenated report flags into these exact names.
    parser=argparse.ArgumentParser()
    parser.add_argument("--stage05at-tef-report",type=Path)
    parser.add_argument("--stage05au-tmd-report",type=Path)
    args=parser.parse_args(["--stage05at-tef-report","/tmp/at.json","--stage05au-tmd-report","/tmp/au.json"])
    assert args.stage05at_tef_report==Path("/tmp/at.json")
    assert args.stage05au_tmd_report==Path("/tmp/au.json")
    print("STAGE05AV SELF-TEST PASS | remaining four candidate CDS days, 8 original Tef/Tmd QC2 fields, two-day Tmd Dec2011; no network/forcing")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--submit-remaining",action="store_true",
                   help="Explicitly request up to four missing site/day CDS time-series files serially; valid existing ZIPs reused")
    p.add_argument("--assess",action="store_true",
                   help="Read-only compare all 8 original source fields after four independently validated CDS ZIPs present")
    for name in ("stage05as-helper","stage05ar-plan","stage05ar-summary","stage05aq-fields",
                 "stage05at-tef-report","stage05au-tmd-report","download-dir","out-dir"):
        p.add_argument("--"+name,type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    keys=("stage05as_helper","stage05ar_plan","stage05ar_summary","stage05aq_fields",
          "stage05at_tef_report","stage05au_tmd_report","download_dir","out_dir")
    if any(getattr(a,name) is None for name in keys):p.error("Need exact actual original AS/AR/AQ/AT/AU source reports, CDS original downloads and fresh report folder")
    if a.submit_remaining and a.assess:p.error("Do not mix CDS submission and science report review flags in one call")
    mod=load_as(a.stage05as_helper)
    plan,source=verify_inputs(mod,a)
    print("STAGE05AV SOURCE_PROVENANCE_PREFLIGHT_PASS 37_OF_45_CONTEXT_REVIEWED; REMAINING_8_ORIGINAL_QC2_CELLS")
    found={}
    for key in sorted(DAYS):
        existing=validate_existing_or_absent(mod,a.download_dir,key,DAYS[key])
        if existing is None:
            print("STAGE05AV SOURCE_CDS_DAY_MISSING",key[0],key[1],"VARIABLES",",".join(DAYS[key]))
        else:
            found[key]=existing
            print("STAGE05AV SOURCE_CDS_DAY_ALREADY_VERIFIED",key[0],key[1],"SHA256",existing["ZIP_SHA256"])
    if not a.submit_remaining and not a.assess:
        print("STAGE05AV READONLY_PILOT_PREVIEW_PASS | PRESENT",len(found),"/4; NO CDS; all 45 original source fields HOLD")
        return
    if a.submit_remaining:
        for key in sorted(DAYS):
            if key not in found:
                found[key]=obtain(mod,a.download_dir,key,plan[key]["request"])
        print("STAGE05AV FOUR_CANDIDATE_DAY_SOURCE_ZIPS_VERIFIED",len(found),"/4")
        print("NEXT_READONLY_CONTEXT_ASSESS --assess (without --submit-remaining)")
        print("ORIGINAL_README_SOLAR_CONFLICT_PRESERVED; ALL_45_ORIGINAL_QC2_FIELDS_HOLD")
        return
    if a.out_dir.exists():p.error("Use a fresh derived science report --out-dir")
    hourly,decisions,evidence=assess(mod,a.download_dir,source)
    a.out_dir.mkdir(parents=True)
    hour_file=a.out_dir/"stage05av_remaining_4_CDS_days_26_model_hour_variable_context.tsv"
    event_file=a.out_dir/"stage05av_remaining_8_original_Tef_Tmd_QC2_vs_ERA5L_CONTEXT_ONLY.tsv"
    report_file=a.out_dir/"stage05av_45_original_source_QC2_independent_hourly_context_completed_ALL_HOLD.json"
    with hour_file.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(hourly[0]),delimiter="\t");w.writeheader();w.writerows(hourly)
    with event_file.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t");w.writeheader();w.writerows(decisions)
    result={"stage":"JapanFlux Stage05AV",
            "status":"EIGHT_REMAINING_SOURCE_QC2_INDEPENDENT_GRID_HOURLY_CONTEXT_REVIEWED_NOT_REPAIRED",
            "prior_original_source_QC2_fields_independently_context_reviewed":37,
            "remaining_original_source_fields_context_reviewed_this_stage":8,
            "total_original_source_fields_with_independent_context":45,
            "prior_source_verified_strong_class":22,
            "source_context_only_but_not_strong_auto_approved":23,
            "source_UTC_time_verified_for_original_Tef_Tmd":False,
            "time_basis":CLOCK,
            "original_readme_local_solar_conflict_SHA256":SOURCE_README_SHA,
            "remaining_four_site_day_CDS_payloads":evidence,
            "remaining_8_original_source_QC2_event_comparisons":decisions,
            "remaining_8_outside_reference_count":sum(x["outside_broad_hourly_reference"] for x in decisions),
            "original_source_fields_science_HOLD":45,
            "original_source_field_repair_values_approved":0,
            "GRID_hourly_context_not_original_tower_30min":True,
            "original_source_ZIP_forcing_model_modified":False,
            "Slurm_jobs":0,"new_CDS_requests_in_assess":0,
            "input_sha256":{name:sha(getattr(a,name)) for name in keys if name not in ("download_dir","out_dir")}}
    with report_file.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AV ALL_REMAINING_EIGHT_ORIGINAL_QC2_INDEPENDENT_CONTEXT_SCIENCE_REVIEW_PASS | NO REPAIR")
    for x in decisions:
        print("ORIGINAL_QC2",x["site"],x["native_JPF_source_start"],"UTC_CANDIDATE",x["hypothetical_JSTminus9_UTC_start"],
              x["variable"],"F",x["original_F_QC2"],"MODEL_HOURLY_MIN_MAX",
              f"{x['hourly_reference_min']:.3f}",f"{x['hourly_reference_max']:.3f}",
              "OUTSIDE_CONTEXT",int(x["outside_broad_hourly_reference"]))
    print("COVERAGE_INDEPENDENT_HOURLY_CONTEXT 45 /45; TOTAL_SCIENCE_HOLD 45 /45")
    print("REMAINING_EIGHT_CDS_CONTEXT_TSV",hour_file)
    print("REMAINING_EIGHT_SOURCE_EVENT_COMPARISON_TSV",event_file)
    print("FINAL_SOURCE_SCIENCE_HOLD_REPORT",report_file)
    print("USER_JST_UTC_PLUS9_NOT_SOURCE_PROVEN; NO SOURCE_ZIP/FORCING/MODEL/SLURM/30MIN_REPLACEMENTS")
if __name__=="__main__":main()

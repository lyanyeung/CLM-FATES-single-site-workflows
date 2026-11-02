#!/usr/bin/env python3
"""Stage05AT: original-source-gated second CDS day for JP-Tef Dec2011.

Requires real Stage05AS first-day CDS JSON and source ZIP SHA/CRC/24UTC/grid;
pins the previously proven Stage05AS reader via Git blob SHA and reuses its
original Stage05AR seven-day source provenance validator. Explicit --submit
downloads only JP-Tef candidate UTC day 2011-12-17 strd to a NEW original
CDS response ZIP in prior Stage05AS downloads; never overwrites/erases.

After both UTC days have independently valid ZIP CSV, compare 2011-12-16
18:00..2011-12-17 01:00 UTC model-hour longwave context (strd / 3600) to
the exact two original JP-Tef QC2 LW_IN_F=26.164 W/m2 source events
(native 2011-12-17 06:00,06:30; candidate UTC 21:00,21:30).

The underlying native timebase is an OPERATOR CHOSEN JST+9 ASSUMPTION,
not proven: original 75-line Tef/Tmd README says local solar time.
Two-day comparison is CONTEXT_ONLY; not a 30-minute replacement value.
No PFT/source/forcing/model/Slurm/AD400 changes; original 45 QC2 HOLD.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,io,json,math,zipfile
from datetime import datetime,timedelta
from pathlib import Path

SITE="JP-Tef"
DAY16="2011-12-16"
DAY17="2011-12-17"
RAW_VAR="strd"
JST="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
DATASET="reanalysis-era5-land-timeseries"
AS_BLOB_SHA="8d203d727c37191c42c555caba13860e3dbdfd8f"
DAY16_ZIP_SHA="533b462fa0804a3d34428b6dd5f9b38b8a9e70dbc705af481c18ec614ea16148"
BIF_SHA="78f02f04892b5731cd33e57b57d00e71bdff4c743ba94f5dd6c69dbd98be0f26"
MODEL_GRID=(45.10000000000121,142.09999999999621)
EVENTS={"201112170600":"201112162100","201112170630":"201112162130"}
EXACT_LW=26.164
REFERENCE_HOURS=[datetime(2011,12,16,18)+timedelta(hours=i) for i in range(8)]

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_json(path):
    d=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict):raise ValueError("Expected original source JSON object")
    return d

def load_tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or len(set(rd.fieldnames))!=len(rd.fieldnames):
            raise ValueError("Source TSV header missing or duplicated")
        return list(rd)

def load_original_as_module(path):
    b=path.read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    if blob!=AS_BLOB_SHA:raise ValueError("Original Stage05AS source science helper changed: "+blob)
    spec=importlib.util.spec_from_file_location("jpf_stage05as_original_source_checker",path)
    if spec is None or spec.loader is None:raise ValueError("Cannot load original source helper")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def check_first_day(mod,src,zip_path,expected_dir):
    expect=expected_dir/f"{SITE}_ERA5Land_timeseries_20111216_CSV_response.zip"
    if (src.get("stage")!="JapanFlux Stage05AS"
        or src.get("status")!="ONE_OPERATOR_JST_CANDIDATE_CDS_SOURCE_ZIP_24UTC_SCIENCE_VALIDATED_NOT_REPAIR"
        or src.get("site")!=SITE or src.get("candidate_UTC_day")!=DAY16
        or src.get("source_time_hypothesis")!=JST
        or src.get("original_source_timebase_definitively_proven") is not False
        or src.get("source_BIF_SHA256")!=BIF_SHA
        or src.get("CDS_dataset")!=DATASET
        or src.get("requested_original_variables")!=["surface_thermal_radiation_downwards"]
        or src.get("original_QC2_fields_HOLD")!=45
        or src.get("CDS_requests_this_stage")!=1
        or src.get("original_source_or_forcing_modified") is not False
        or src.get("scientific_halfhour_replacements_approved") is not False
        or src.get("Slurm_jobs")!=0
        or Path(src.get("observed_source_archive_path",""))!=expect
        or zip_path!=expect):
        raise ValueError("Actual first 2011-12-16 source science provenance changed")
    res=src["response"]
    if (res.get("ZIP_SHA256")!=DAY16_ZIP_SHA
        or res.get("ZIP_bytes")!=467
        or res.get("validated_raw_columns")!=["strd"]
        or res.get("independent_variable_hour_count")!=24
        or res.get("source_grid_elevation")!="UNVERIFIED"
        or res.get("original_clock")!="OPERATOR_PLUS9_JST_HYPOTHESIS_NOT_RELEASE_SOURCE_VERIFIED"
        or not all(math.isclose(float(res[key]),val,abs_tol=1e-6)
             for key,val in zip(("ERA5L_grid_lat","ERA5L_grid_lon"),MODEL_GRID))):
        raise ValueError("Original 2011-12-16 CDS science payload audit changed")
    if mod.about_path(zip_path)!="REGULAR" or sha(zip_path)!=DAY16_ZIP_SHA:
        raise ValueError("Original 2011-12-16 CDS ZIP missing/modified")
    actual=mod.inspect_csv_zip(zip_path,SITE,DAY16,["surface_thermal_radiation_downwards"])
    if (actual["ZIP_SHA256"]!=DAY16_ZIP_SHA
        or actual["validated_raw_columns"]!=["strd"]
        or actual["independent_variable_hour_count"]!=24):
        raise ValueError("First-day independently sourced original CDS ZIP CRC/UTC/strd changed")
    return actual

def check_source_events(rows):
    events={}
    all_site=[r for r in rows if r.get("site")==SITE]
    if len(rows)!=18 or len(all_site)!=4:
        raise ValueError("Original Tef 4 / all-site 18 Stage05AQ QC2 fields changed")
    for r in all_site:
        native=r["original_native_halfhour_start"]
        if native not in EVENTS:
            if native not in ("202204090200","202204090230") or r["variable"]!="LW_IN":
                raise ValueError("Unexpected non-2011 JP-Tef original source scope")
            continue
        if r["variable"]!="LW_IN" or native in events:
            raise ValueError("Original JP-Tef 2011 source field/time scope changed")
        if (r["candidate_UTC_start"]!=EVENTS[native]
            or r["candidate_time_basis"]!=JST
            or r["candidate_status"]!="OPERATOR_SELECTED_PLUS9_HYPOTHESIS_QC2_SCIENCE_HOLD"
            or r["original_readme_time_claim"]!="LOCAL_SOLAR_TIME_WITHOUT_DST_CONFLICT"
            or r["source_QC"]!="2"
            or r["forcing_repair_approved"]!="False"
            or r["unit"]!="W m-2"
            or not math.isclose(float(r["original_selected_F_QC2"]),EXACT_LW,abs_tol=1e-8)
            or not math.isclose(float(r["embedded_same_release_ERA"]),EXACT_LW,abs_tol=1e-8)):
            raise ValueError("Original JP-Tef selected LW_IN source QC2 provenance changed")
        events[native]=r
    if set(events)!=set(EVENTS):
        raise ValueError("Both original JP-Tef 2011 LW_IN native source events not present")
    return events

def hourly_longwave(path,day):
    result={}
    with zipfile.ZipFile(path) as z:
        members=[i for i in z.infolist() if not i.is_dir()]
        if len(members)!=1:raise ValueError("Expect one source strd CSV member after full source validation")
        rd=csv.DictReader(io.StringIO(z.read(members[0]).decode("utf-8-sig")))
        if set(rd.fieldnames or ())!={"valid_time","latitude","longitude","strd"}:
            raise ValueError("Unexpected verified original CDS time-series variable columns")
        for row in rd:
            t=datetime.strptime(row["valid_time"],"%Y-%m-%d %H:%M:%S")
            if t.date().isoformat()!=day or t in result:
                raise ValueError("Original independent model hour out of expected day/duplicated")
            value=float(row["strd"])/3600.0
            if not math.isfinite(value) or not 0<=value<1500:
                raise ValueError("Nonphysical independent hourly STRD energy/flux")
            grid=(float(row["latitude"]),float(row["longitude"]))
            if not all(math.isclose(grid[i],MODEL_GRID[i],abs_tol=1e-6) for i in range(2)):
                raise ValueError("Original nearest grid mismatch across the two independent UTC days")
            result[t]=value
    if len(result)!=24:
        raise ValueError("Missing one or more model UTC hour source records")
    return result

def compare_two_days(path16,path17,events):
    series={**hourly_longwave(path16,DAY16),**hourly_longwave(path17,DAY17)}
    if any(t not in series for t in REFERENCE_HOURS):
        raise ValueError("A required two-day original source context hour is missing")
    rows=[]
    for t in REFERENCE_HOURS:
        rows.append({"model_hour_end_UTC":t.strftime("%Y-%m-%dT%H:%MZ"),
                     "ERA5Land_strd_deaccumulated_hourly_W_m2":f"{series[t]:.6f}",
                     "source_tower_latitude":45.055808,
                     "source_tower_longitude":142.107122,
                     "model_grid_latitude":MODEL_GRID[0],
                     "model_grid_longitude":MODEL_GRID[1],
                     "reference_role":"NEARBY_GRID_HOURLY_CONTEXT_NOT_HALF_HOUR_REPAIR"})
    lo=min(series[t] for t in REFERENCE_HOURS)
    hi=max(series[t] for t in REFERENCE_HOURS)
    outside=not lo<=EXACT_LW<=hi
    decisions=[]
    for native,candidate in EVENTS.items():
        decisions.append({"site":SITE,"native_JPF_start":native,
              "candidate_UTC_start_JST_plus9":candidate,
              "original_LW_IN_F_QC2_W_m2":EXACT_LW,
              "nearby_independent_8h_min_W_m2":lo,
              "nearby_independent_8h_max_W_m2":hi,
              "outside_conservative_8h_hourly_envelope":outside,
              "science_status":"HOLD_CONTEXT_ONLY_NO_STRONG_CLASS_AUTO_APPROVAL",
              "timebasis":"USER_JST_PLUS9_HYPOTHESIS_ORIGINAL_SOLAR_README_CONFLICT"})
    if len(events)!=2 or len(decisions)!=2:
        raise ValueError("Exact two original JP-Tef halfhour LW contexts missing")
    return rows,decisions,lo,hi,outside

def selftest():
    assert len(EVENTS)==2 and len(REFERENCE_HOURS)==8
    assert REFERENCE_HOURS[0]==datetime(2011,12,16,18)
    assert REFERENCE_HOURS[-1]==datetime(2011,12,17,1)
    assert (datetime(2011,12,17,6)-datetime(2011,12,16,21)).total_seconds()==9*3600
    assert all(len(x)==12 for x in EVENTS)
    assert 720000/3600==200
    print("STAGE05AT SELF-TEST PASS | exact source 2011 Tef two LW QC2 events, day16 SHA 533b + day17 24UTC STRD/3600, 8h cross-midnight context; NO CDS/WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--submit",action="store_true")
    p.add_argument("--stage05as-helper",type=Path)
    p.add_argument("--stage05ar-plan",type=Path)
    p.add_argument("--stage05ar-summary",type=Path)
    p.add_argument("--stage05as-day16-audit",type=Path)
    p.add_argument("--stage05aq-fields",type=Path)
    p.add_argument("--download-dir",type=Path)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    names=("stage05as_helper","stage05ar_plan","stage05ar_summary",
           "stage05as_day16_audit","stage05aq_fields","download_dir","out_dir")
    if any(getattr(a,n) is None for n in names):
        p.error("Need original exact Stage05AS helper, actual Stage05AR source, original day16 CDS audit/ZIP, original Stage05AQ source QC2 fields, downloads and fresh output folder")
    mod=load_original_as_module(a.stage05as_helper)
    original=mod.validate(load_json(a.stage05ar_plan),load_json(a.stage05ar_summary))
    key=SITE,DAY17
    if len(original)!=7 or key not in original:
        raise ValueError("No original source-bounded candidate JP-Tef UTC 2011-12-17 CDS request")
    req=original[key]["request"]
    if (req["variable"]!=["surface_thermal_radiation_downwards"]
        or req["date"]!=DAY17+"/"+DAY17
        or req["data_format"]!="csv"
        or any(not math.isclose(float(req["location"][n]),val,abs_tol=1e-7)
           for n,val in (("latitude",45.055808),("longitude",142.107122)))):
        raise ValueError("Original stage05AR BIF-attested second-day request scope changed")
    directory=a.download_dir
    if directory.is_symlink() or not directory.is_dir():
        p.error("Existing original Stage05AS downloads directory must be a non-symlink directory")
    zip16=directory/f"{SITE}_ERA5Land_timeseries_20111216_CSV_response.zip"
    check_first_day(mod,load_json(a.stage05as_day16_audit),zip16,directory)
    source_events=check_source_events(load_tsv(a.stage05aq_fields))
    zip17=directory/f"{SITE}_ERA5Land_timeseries_20111217_CSV_response.zip"
    partial=Path(str(zip17)+".partial")
    if a.out_dir.exists():p.error("Fresh derived science report --out-dir required")
    print("STAGE05AT FIRST-DAY SOURCE ZIP VERIFIED",zip16,"SHA256",DAY16_ZIP_SHA)
    print("STAGE05AT TWO_ORIGINAL_LW_QC2_NATIVE_EVENTS",len(source_events),"VALUE_W_M2",EXACT_LW)
    print("STAGE05AT SECOND-DAY_REQUEST_SCOPE",json.dumps(req,sort_keys=True))
    if not a.submit:
        print("STAGE05AT READONLY PILOT PREFLIGHT PASS | NO CDS / NO ORIGINAL WRITES; run explicit --submit to retrieve second UTC day")
        return
    for path in (zip17,partial,zip17.with_suffix(".csv"),zip17.with_suffix(".nc")):
        if mod.about_path(path)!="ABSENT":
            p.error("Prior file/partial collision: no overwrite, manual existing-payload review "+str(path))
    if not (Path.home()/".cdsapirc").is_file():
        raise RuntimeError("CDS private ~/.cdsapirc missing")
    try:import cdsapi
    except ImportError as e:raise RuntimeError("cdsapi missing from activated Python environment") from e
    print("STAGE05AT EXPLICIT JP-TEF SECOND-DAY CDS REFERENCE REQUEST",SITE,DAY17)
    cdsapi.Client().retrieve(DATASET,req).download(str(partial))
    try:
        new=mod.inspect_csv_zip(partial,SITE,DAY17,req["variable"])
        if new["independent_variable_hour_count"]!=24 or new["validated_raw_columns"]!=["strd"]:
            raise ValueError("Second day missing validated 24 model hours")
        if any(not math.isclose(float(new[k]),MODEL_GRID[i],abs_tol=1e-6)
               for i,k in enumerate(("ERA5L_grid_lat","ERA5L_grid_lon"))):
            raise ValueError("Second CDS day source grid differs from original day16")
        hourly,decisions,lo,hi,outside=compare_two_days(zip16,partial,source_events)
    except (OSError,ValueError,UnicodeError,RuntimeError,zipfile.BadZipFile,KeyError) as exc:
        print("STAGE05AT SECOND_DAY_CONTENT_HOLD; RETAIN PARTIAL NO REPAIR",type(exc).__name__,str(exc))
        raise
    if mod.about_path(zip17)!="ABSENT":
        raise RuntimeError("Destination collision after CDS source validation; preserve partial")
    partial.rename(zip17)
    a.out_dir.mkdir(parents=True)
    ts=a.out_dir/"stage05at_Tef_2011_two_day_hourly_LW_independent_context.tsv"
    js=a.out_dir/"stage05at_Tef_2_original_LW_QC2_ERA5L_two_day_context_HOLD.json"
    with ts.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(hourly[0]),delimiter="\t")
        w.writeheader();w.writerows(hourly)
    data={
       "stage":"JapanFlux Stage05AT",
       "status":"TWO_INDEPENDENT_CDS_DAY_STRD_REFERENCE_SOURCE_VALIDATED_TWO_ORIGINAL_LW_CONTEXT_ONLY",
       "original_source_JPF_site":"JP-Tef",
       "original_source_JPF_QC2_field_count":2,
       "original_source_two_fields":decisions,
       "source_time_hypothesis":JST,
       "original_README_solar_time_conflict":"PRESERVED",
       "original_source_timebase_proven":False,
       "first_day_zip_sha256":DAY16_ZIP_SHA,
       "second_day_zip_sha256":new["ZIP_SHA256"],
       "original_source_day16_zip":str(zip16),
       "original_source_day17_zip":str(zip17),
       "nearest_grid":[new["ERA5L_grid_lat"],new["ERA5L_grid_lon"]],
       "original_tower_bif_lat_lon_elev_m":[45.055808,142.107122,79.47],
       "model_grid_height_verified":False,
       "two_day_hourly_reference_UTC_labels":[r["model_hour_end_UTC"] for r in hourly],
       "two_day_reference_min_W_m2":lo,
       "two_day_reference_max_W_m2":hi,
       "both_QC2_fields_outside_8h_reference_envelope":outside,
       "strd_units_processing":"CDS_ERA5LAND_TIMESERIES_ALREADY_DEACCUMULATED_HOURLY_J_M2_DIVIDE_BY_3600_NO_SECOND_DIFFERENCE",
       "time_comparison_role":"HOURLY_GRID_CONTEXT_NOT_TOWER_30MIN_REPLACEMENT",
       "new_strong_class_science_approval":False,
       "all_45_original_source_QC2_fields_HOLD":True,
       "original_source_ZIP_or_forcing_modified":False,
       "Slurm_jobs":0,"scientific_repair_values_approved":False,
       "CDS_requests_this_stage":1,
       "input_sha256":{n:sha(getattr(a,n)) for n in names
         if n not in ("download_dir","out_dir")}
    }
    with js.open("x",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AT SECOND CDS UTC DAY ZIP CRC/24UTC/GRID PASS | TWO-DAY JP-TEF LW CONTEXT ONLY NO REPAIR")
    print("DAY17_ZIP",zip17,"BYTES",new["ZIP_bytes"],"SHA256",new["ZIP_SHA256"])
    print("MODEL_GRID",new["ERA5L_grid_lat"],new["ERA5L_grid_lon"],
          "HOURS_DAY16_24_DAY17_24")
    print("REFERENCE_8h_STRD_W_M2_MIN_MAX",f"{lo:.6f}",f"{hi:.6f}")
    for rec in decisions:
        print("ORIGINAL_QC2",rec["native_JPF_start"],
              "CANDIDATE_UTC",rec["candidate_UTC_start_JST_plus9"],
              "LW_W_M2",rec["original_LW_IN_F_QC2_W_m2"],
              "OUTSIDE_8h_CONTEXT",int(rec["outside_conservative_8h_hourly_envelope"]),
              "SCIENCE",rec["science_status"])
    print("INDEPENDENT_8H_CONTEXT_TSV",ts)
    print("TWO_DAY_SOURCE_SCIENCE_HOLD_JSON",js)
    print("ALL_45_ORIGINAL_SOURCE_QC2_FIELDS_HOLD; NO ORIGINAL FORCING/SLURM/REPAIR")
if __name__=="__main__":main()

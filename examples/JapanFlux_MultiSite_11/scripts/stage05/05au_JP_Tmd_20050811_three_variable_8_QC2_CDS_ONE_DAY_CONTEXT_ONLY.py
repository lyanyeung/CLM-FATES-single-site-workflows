#!/usr/bin/env python3
"""JapanFlux Stage05AU: JP-Tmd 2005-08-11 single-day CDS time-series pilot.

Verify Stage05AR original JPF BIF source geolocation and seven candidate
UTC-day request plan through SHA-pinned Stage05AS source module.
Verify Stage05AQ 18-field source provenance including exactly 8 Tmd
2005-08-12 original selected F=embedded-ERA QC2 variable fields.
Verify real Stage05AT two-day JP-Tef source-context previous 2 (not
an approval), and no re-download of the two previous Tef source days.

Request only operator JST+9 diagnostic candidate UTC day 2005-08-11:
t2m K -> °C (subtract 273.15); sp Pa -> kPa (divide 1000);
strd ERA5-Land timeseries ALREADY hourly-deaccumulated J m-2 -> hourly
W m-2 (divide 3600, NEVER difference neighbouring hours).
Compare conservative 14:00–22:00 UTC hourly source context to the eight
original selected Tmd F=ERA QC2 field records at candidate 17:00–18:30.
This IS NOT a reconstructed 30-min site observation. No correction,
source clock proof, source/forcing/model change, Slurm or AD400 approval.
All 45 original JPF QC2 fields remain science HOLD.

Usage: same source arguments without --submit for read-only preflight.
Add --submit for explicit ONE day CDS download, ZIP CRC/24UTC/3 vars/grid
science audit, and new derived TSV/JSON source context.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,io,json,math,zipfile
from datetime import datetime,timedelta
from pathlib import Path

SITE="JP-Tmd"; DAY="2005-08-11"; DATASET="reanalysis-era5-land-timeseries"
CLOCK="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
AS_BLOB="8d203d727c37191c42c555caba13860e3dbdfd8f"
BIF_SHA="d5d99b265b6f4eaa29a059f7cc13ceb0e5f101979276ea090c4ec6cf5dc5c87b"
TEF16_SHA="533b462fa0804a3d34428b6dd5f9b38b8a9e70dbc705af481c18ec614ea16148"
TEF17_SHA="81043becb8ccce9936164d7e1e3afdc56c55a84b077b314c4672339f3a81f532"
REQ_VARS=["2m_temperature","surface_pressure","surface_thermal_radiation_downwards"]
SOURCE_EVENTS={
 ("200508120200","LW_IN"):("200508111700",28.519),
 ("200508120230","LW_IN"):("200508111730",28.519),
 ("200508120230","PA"):("200508111730",49.502),
 ("200508120230","TA"):("200508111730",-132.399),
 ("200508120300","PA"):("200508111800",0.0),
 ("200508120300","TA"):("200508111800",-284.222),
 ("200508120330","PA"):("200508111830",49.506),
 ("200508120330","TA"):("200508111830",-132.688)
}
MODEL_HOURS=[datetime(2005,8,11,14)+timedelta(hours=h) for h in range(9)]
UNIT={"TA":"deg C","PA":"kPa","LW_IN":"W m-2"}
SOURCE_CDS={"TA":"t2m","PA":"sp","LW_IN":"strd"}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def readjson(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise ValueError("Source JSON object required "+str(p))
    return x
def readtsv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or len(rd.fieldnames)!=len(set(rd.fieldnames)):
            raise ValueError("Malformed original source Stage05AQ TSV")
        return list(rd)
def use_as_helper(p):
    b=p.read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\x00"+b).hexdigest()
    if blob!=AS_BLOB:
        raise ValueError("Stage05AS source helper not pinned to original already-run code: "+blob)
    spec=importlib.util.spec_from_file_location("jpf_stage05as_source_science",p)
    if spec is None or spec.loader is None:raise ValueError("Could not load original Stage05AS science helper")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def verify_tef_context(p):
    d=readjson(p)
    if (d.get("stage")!="JapanFlux Stage05AT"
        or d.get("status")!="TWO_INDEPENDENT_CDS_DAY_STRD_REFERENCE_SOURCE_VALIDATED_TWO_ORIGINAL_LW_CONTEXT_ONLY"
        or d.get("original_source_JPF_site")!="JP-Tef"
        or d.get("original_source_JPF_QC2_field_count")!=2
        or d.get("source_time_hypothesis")!=CLOCK
        or d.get("original_source_timebase_proven") is not False
        or d.get("original_README_solar_time_conflict")!="PRESERVED"
        or d.get("first_day_zip_sha256")!=TEF16_SHA
        or d.get("second_day_zip_sha256")!=TEF17_SHA
        or d.get("both_QC2_fields_outside_8h_reference_envelope") is not True
        or d.get("new_strong_class_science_approval") is not False
        or d.get("all_45_original_source_QC2_fields_HOLD") is not True
        or d.get("scientific_repair_values_approved") is not False
        or d.get("CDS_requests_this_stage")!=1):
        raise ValueError("Previously real JP-Tef two-day 2-source-QC2 context evidence changed")
    events=d.get("original_source_two_fields",[])
    if len(events)!=2 or {e.get("native_JPF_start") for e in events}!={"201112170600","201112170630"}:
        raise ValueError("Stage05AT Tef original source context event population changed")
    return d
def verify_tmd_sources(rows):
    if len(rows)!=18:
        raise ValueError("Stage05AQ exact 18 original source fields changed")
    subset=[r for r in rows if r["site"]==SITE]
    if len(subset)!=14:raise ValueError("Stage05AQ all 14 Tmd source events no longer present")
    events={}
    for r in subset:
        key=r["original_native_halfhour_start"],r["variable"]
        if key in events:raise ValueError("Duplicate original Tmd QC2 key")
        if (r["candidate_time_basis"]!=CLOCK
            or r["candidate_status"]!="OPERATOR_SELECTED_PLUS9_HYPOTHESIS_QC2_SCIENCE_HOLD"
            or r["original_readme_time_claim"]!="LOCAL_SOLAR_TIME_WITHOUT_DST_CONFLICT"
            or r["source_readme_sha256"]!="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
            or r["original_BIF_UTC_OFFSET_hours"]!="9"
            or r["source_QC"]!="2"
            or r["forcing_repair_approved"]!="False"
            or r["variable"] not in UNIT or r["unit"]!=UNIT[r["variable"]]):
            raise ValueError("Original Tmd Stage05AQ operator/JST/source QC2 time/units/HOLD provenance changed")
        if key in SOURCE_EVENTS:
            candidate,orig=SOURCE_EVENTS[key]
            if (r["candidate_UTC_start"]!=candidate
                or not math.isclose(float(r["original_selected_F_QC2"]),orig,abs_tol=1e-8)
                or not math.isclose(float(r["embedded_same_release_ERA"]),orig,abs_tol=1e-8)):
                raise ValueError("Original source Tmd Aug2005 QC2 selected F and ERA values/time changed")
            events[key]=r
        else:
            # Protected six Tmd PA source fields in 2011 and 2022:
            if r["variable"]!="PA" or not (
              r["original_native_halfhour_start"].startswith("20111217")
              or r["original_native_halfhour_start"].startswith("20220409")):
                raise ValueError("Unexpected original Tmd non-2005 source population")
    if len(events)!=8 or len({t for t,v in events})!=4:
        raise ValueError("Expected exactly eight 2005 QC2 original Tmd fields at four source HH times")
    return events
def source_hourly(path,site,day):
    hours={}
    with zipfile.ZipFile(path) as z:
        files=[x for x in z.infolist() if not x.is_dir()]
        for info in files:
            rd=csv.DictReader(io.StringIO(z.read(info).decode("utf-8-sig")))
            cols=set(rd.fieldnames or [])-{"valid_time","latitude","longitude"}
            if not cols or not cols<={"sp","t2m","strd"}:
                raise ValueError("Unexpected raw independent CDS field")
            for row in rd:
                t=datetime.strptime(row["valid_time"],"%Y-%m-%d %H:%M:%S")
                if t.date().isoformat()!=day:raise ValueError("Unexpected UTC label")
                entry=hours.setdefault(t,{})
                for variable in cols:
                    if variable in entry:raise ValueError("Duplicate independent source hour")
                    raw=float(row[variable])
                    conv={"sp":raw/1000.0,"t2m":raw-273.15,"strd":raw/3600.0}[variable]
                    if not math.isfinite(conv):raise ValueError("Nonfinite independent converted source")
                    entry[variable]=conv
    if len(hours)!=24 or any(set(v)!={"sp","t2m","strd"} for v in hours.values()):
        raise ValueError("Independent CDS source not complete over 24UTC hours/three variables")
    return hours
def compare_hourly(hours,events):
    rows=[]
    vmin={};vmax={}
    for code in ("sp","t2m","strd"):
        x=[hours[t][code] for t in MODEL_HOURS]
        vmin[code]=min(x);vmax[code]=max(x)
    for t in MODEL_HOURS:
        r=hours[t]
        rows.append({
            "UTC_hour_end":t.strftime("%Y-%m-%dT%H:%MZ"),
            "ERA5Land_sp_kPa":f"{r['sp']:.6f}",
            "ERA5Land_t2m_C":f"{r['t2m']:.6f}",
            "ERA5Land_strd_hourly_W_m2":f"{r['strd']:.6f}",
            "reference_role":"INDEPENDENT_NEARBY_GRID_HOURLY_CONTEXT_NOT_TOWER_HALF_HOUR_REPLACEMENT"
        })
    comparisons=[]
    for (native,var),(candidate,x) in sorted(SOURCE_EVENTS.items()):
        code=SOURCE_CDS[var]
        out=not vmin[code]<=x<=vmax[code]
        comparisons.append({
           "site":SITE,"original_native_start":native,
           "candidate_UTC_start":candidate,
           "variable":var,"source_original_selected_F_QC2":x,
           "source_original_unit":UNIT[var],"ERA5L_raw_field":code,
           "independent_hourly_context_min":vmin[code],
           "independent_hourly_context_max":vmax[code],
           "outside_9h_reference_envelope":out,
           "evidence_label":"HOLD_CONTEXT_ONLY_OPERATOR_JST9_SOURCE_SOLAR_README_CONFLICT",
           "repair_approved":False
        })
    if len(events)!=len(comparisons):raise ValueError("Unexpected original source QC2 population")
    return rows,comparisons,vmin,vmax
def selftest():
    assert len(SOURCE_EVENTS)==8 and len({t for t,var in SOURCE_EVENTS})==4
    assert len(MODEL_HOURS)==9 and MODEL_HOURS[0]==datetime(2005,8,11,14)
    assert MODEL_HOURS[-1]==datetime(2005,8,11,22)
    assert 101000/1000==101 and abs((293.15-273.15)-20)<1e-10
    assert 720000/3600==200
    assert (datetime(2005,8,12,3)-datetime(2005,8,11,18)).total_seconds()==9*3600
    print("STAGE05AU SELF-TEST PASS | Tmd original 8 QC2 TA3 PA3 LW2, 2005-08-11 9h UTC 3-variable source, strd hourly deaccumulated, no CDS/writes")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--submit",action="store_true")
    for name in ("stage05as-helper","stage05ar-plan","stage05ar-summary",
                 "stage05aq-fields","stage05at-tef-report","download-dir","out-dir"):
        p.add_argument("--"+name,type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    required=("stage05as_helper","stage05ar_plan","stage05ar_summary","stage05aq_fields",
              "stage05at_tef_report","download_dir","out_dir")
    if any(getattr(a,name) is None for name in required):
        p.error("Need real original Stage05AR plan/summary, AQ fields, Stage05AT Tef two-day report, pinned Stage05AS helper, downloads folder, fresh output folder")
    helper=use_as_helper(a.stage05as_helper)
    plan=helper.validate(readjson(a.stage05ar_plan),readjson(a.stage05ar_summary))
    if len(plan)!=7 or (SITE,DAY) not in plan:
        raise ValueError("Original seven candidate CDS site-day plan invalid")
    ref=plan[SITE,DAY]; req=ref["request"]
    if (req["variable"]!=REQ_VARS
        or req["date"]!=DAY+"/"+DAY
        or req["data_format"]!="csv"
        or not math.isclose(float(req["location"]["latitude"]),42.735911,abs_tol=1e-7)
        or not math.isclose(float(req["location"]["longitude"]),141.523147,abs_tol=1e-7)
        or ref["original_BIF_SHA256"]!=BIF_SHA
        or ref["required_UTC_hour_clocks"]!=[f"{n:02d}:00" for n in range(14,23)]):
        raise ValueError("Original source Stage05AR Tmd 2005-08-11 BIF/hour/variable scope altered")
    tef=verify_tef_context(a.stage05at_tef_report)
    events=verify_tmd_sources(readtsv(a.stage05aq_fields))
    folder=a.download_dir
    if folder.is_symlink() or not folder.is_dir():
        p.error("Existing original Stage05AS downloads must be non-symlink directory")
    for day,digest in (("20111216",TEF16_SHA),("20111217",TEF17_SHA)):
        t=folder/f"JP-Tef_ERA5Land_timeseries_{day}_CSV_response.zip"
        if helper.about_path(t)!="REGULAR" or sha(t)!=digest:
            raise ValueError("Original already validated JP-Tef CDS source ZIP missing or altered: "+str(t))
    target=folder/f"{SITE}_ERA5Land_timeseries_{DAY.replace('-','')}_CSV_response.zip"
    partial=Path(str(target)+".partial")
    print("STAGE05AU ORIGINAL JP-TEF 2-DAY EVIDENCE/ZIP SHA RETAINED PASS | NO REDOWNLOAD")
    print("STAGE05AU ORIGINAL TMD_2005 8_QC2_SOURCE_FIELDS VERIFIED",len(events))
    print("STAGE05AU ONE_DAY_REQUEST",json.dumps(req,sort_keys=True))
    if not a.submit:
        print("STAGE05AU READONLY SOURCE/UTC/BIF/CDS PREFLIGHT PASS | NO CDS / NO ORIGINAL WRITES")
        return
    if a.out_dir.exists():p.error("Fresh science report directory required; no overwrite")
    for x in (target,partial,target.with_suffix(".csv"),target.with_suffix(".nc")):
        if helper.about_path(x)!="ABSENT":
            p.error("Existing independent CDS ZIP/CSV/NC/partial collision, no overwrites: "+str(x))
    if not (Path.home()/".cdsapirc").is_file():
        raise RuntimeError("Missing private CDS credentials, dataset licence must have been accepted")
    try:import cdsapi
    except ImportError as e:raise RuntimeError("cdsapi unavailable in selected environment") from e
    print("STAGE05AU EXPLICIT JP-TMD 2005 SINGLE-DAY CDS INDEPENDENT REFERENCE REQUEST")
    print("CDS_SITE",SITE,"CANDIDATE_UTC_DATE",DAY,"SOURCE_BIF",BIF_SHA)
    print("NO_SECRET_CDS_REQUEST",json.dumps(req,sort_keys=True))
    cdsapi.Client().retrieve(DATASET,req).download(str(partial))
    try:
        response=helper.inspect_csv_zip(partial,SITE,DAY,REQ_VARS)
        if (response["independent_variable_hour_count"]!=72
            or response["validated_raw_columns"]!=["sp","strd","t2m"]):
            raise ValueError("CDS original data missing one or more 3×24 hours")
        points=source_hourly(partial,SITE,DAY)
        hourly,comp,vmin,vmax=compare_hourly(points,events)
    except (OSError,ValueError,UnicodeError,RuntimeError,zipfile.BadZipFile,KeyError) as e:
        print("STAGE05AU SOURCE_PAYLOAD_HOLD_KEEP_PARTIAL_NO_REPAIR",type(e).__name__,str(e))
        raise
    if helper.about_path(target)!="ABSENT":
        raise RuntimeError("Destination collision after independent CDS audit")
    partial.rename(target)
    a.out_dir.mkdir(parents=True)
    table=a.out_dir/"stage05au_Tmd_20050811_9h_three_variable_ERA5Land_hourly_context.tsv"
    eventfile=a.out_dir/"stage05au_Tmd_2005_8_original_QC2_vs_three_variable_hourly_CONTEXT_ONLY.tsv"
    summary=a.out_dir/"stage05au_Tmd_2005_8_original_QC2_ERA5Land_independent_context_HOLD.json"
    with table.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,delimiter="\t",fieldnames=list(hourly[0]));w.writeheader();w.writerows(hourly)
    with eventfile.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,delimiter="\t",fieldnames=list(comp[0]));w.writeheader();w.writerows(comp)
    obj={
       "stage":"JapanFlux Stage05AU",
       "status":"TMD_2005_8_ORIGINAL_QC2_SOURCES_3_INDEPENDENT_CDS_VARIABLE_HOURLY_CONTEXT_ONLY",
       "site":SITE,"candidate_UTC_day":DAY,
       "original_source_QC2_fields_reviewed_this_stage":8,
       "original_Tmd_2005_source_fields":comp,
       "prior_strong_class_fields":22,"prior_source_verified_context_only":5,
       "prior_Tef_operator_JST_context_only":2,
       "new_Tmd_operator_JST_context_only":8,
       "total_original_source_fields_independent_context_reviewed":37,
       "original_source_fields_not_yet_compared":8,
       "outside_context_count_new_Tmd":sum(x["outside_9h_reference_envelope"] for x in comp),
       "strd_conversion":"ALREADY_DEACCUMULATED_CDS_TIMESERIES_J_M2_DIVIDE_3600_NOT_DIFFERENCE",
       "model_t2m_conversion":"K_MINUS_273_15_TO_DEG_C",
       "model_sp_conversion":"PASCALS_DIVIDE_1000_TO_KPA",
       "nearby_UTC_hour_end_clock":[r["UTC_hour_end"] for r in hourly],
       "reference_min_by_source_code":vmin,"reference_max_by_source_code":vmax,
       "returned_CDS_ZIP":str(target),"returned_CDS_source":response,
       "source_tower_BIF_geolocation":[42.735911,141.523147,117.0],
       "original_readme_source_clock_conflict":"SOLAR_VS_OPERATOR_JST_PLUS9_NOT_VERIFIED",
       "source_time_hypothesis":CLOCK,"model_grid_elevation_verified":False,
       "scientific_30min_repair_values_approved":False,
       "new_strong_evidence_label_approved":False,
       "all_45_original_QC2_source_fields_HOLD":True,
       "source_ZIP_forcing_model_modified":False,"Slurm_jobs":0,"CDS_requests_this_stage":1,
       "input_sha256":{name:sha(getattr(a,name)) for name in required if name not in ("download_dir","out_dir")}
    }
    with summary.open("x",encoding="utf-8") as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AU TMD 2005 CDS 3×24 UTC/CRC/GRID SOURCE PASS | EIGHT ORIGINAL QC2 SOURCE FIELDS CONTEXT ONLY NO REPAIR")
    print("CDS_ZIP",target,"BYTES",response["ZIP_bytes"],"SHA256",response["ZIP_SHA256"])
    print("RETURNED_CDS_NEAREST_GRID",response["ERA5L_grid_lat"],response["ERA5L_grid_lon"])
    print("NINE_HOUR_CONTEXT_TA_C_MIN_MAX",f"{vmin['t2m']:.3f}",f"{vmax['t2m']:.3f}")
    print("NINE_HOUR_CONTEXT_PA_KPA_MIN_MAX",f"{vmin['sp']:.3f}",f"{vmax['sp']:.3f}")
    print("NINE_HOUR_CONTEXT_LW_WM2_MIN_MAX",f"{vmin['strd']:.3f}",f"{vmax['strd']:.3f}")
    for r in comp:
        print("ORIGINAL_QC2",r["original_native_start"],"UTC_CANDIDATE",r["candidate_UTC_start"],
              r["variable"],"ORIGINAL_F",r["source_original_selected_F_QC2"],
              "MODEL_REFERENCE_ENVELOPE",f"{r['independent_hourly_context_min']:.3f}",f"{r['independent_hourly_context_max']:.3f}",
              "OUTSIDE_CONTEXT",int(r["outside_9h_reference_envelope"]))
    print("COVERAGE_INDEPENDENT_CONTEXT",37,"/45; REMAINING",8,"ALL_45_ORIGINAL_SOURCE_QC2_FIELDS_HOLD")
    print("SOURCE_CDS_HOURLY_REFERENCE_TABLE",table)
    print("EIGHT_SOURCE_QC2_EVENT_CONTEXT",eventfile)
    print("EIGHT_FIELD_SCIENCE_HOLD_REPORT",summary)
    print("NO ORIGINAL ZIP / FORCING / MODEL / SLURM / AD400 OR REPAIR")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Stage05AS: opt-in one-day CDS ERA5-Land TIMESERIES download for the
operator-selected JST+9 hypothesis of 18 JP-Tef/Tmd original QC2 fields.

Strict inputs: ACTUAL Stage05AR original BIF SHA-verified geolocated
seven site/day preview and its science HOLD summary. First one-day pilot:
  --submit --site JP-Tef --utc-date 2011-12-16

All seven days are candidates only because the original 75-line Tef/Tmd
README explicitly says "local solar time", despite source BIF UTC_OFFSET=9.
This uses the USER-SELECTED JST+9 diagnostic interpretation, not a
new scientifically proven timebase or a 30-minute replacement authority.

CDS product "reanalysis-era5-land-timeseries" produces original ZIP CSV.
The timeseries product already DEACCUMULATES hourly STRD energy J/m2;
for contextual flux use strd / 3600 W/m2, do not difference hours.
Only genuine requested variable columns and 24 00..23 UTC hours, original
BIF-near grid, physical bounds, ZIP CRC are permitted. Bad response
preserved at .zip.partial for forensic review (no clobber/retry).
No original data/forcing/model/Slurm/AD400 changes or repairs.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,stat,zipfile
from datetime import date,datetime
from pathlib import Path,PurePosixPath

CLOCK="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
DATASET="reanalysis-era5-land-timeseries"
ORIGINAL_SITES={
 "JP-Tef":{"latitude":45.055808,"longitude":142.107122,
            "elevation_m":79.47,
            "bif_sha":"78f02f04892b5731cd33e57b57d00e71bdff4c743ba94f5dd6c69dbd98be0f26"},
 "JP-Tmd":{"latitude":42.735911,"longitude":141.523147,
            "elevation_m":117.0,
            "bif_sha":"d5d99b265b6f4eaa29a059f7cc13ceb0e5f101979276ea090c4ec6cf5dc5c87b"}
}
# Only these seven original Stage05AQ/AR sourced candidate UTC site-days:
VARS={
 ("JP-Tef","2011-12-16"):("surface_thermal_radiation_downwards",),
 ("JP-Tef","2011-12-17"):("surface_thermal_radiation_downwards",),
 ("JP-Tef","2022-04-08"):("surface_thermal_radiation_downwards",),
 ("JP-Tmd","2005-08-11"):("2m_temperature","surface_pressure","surface_thermal_radiation_downwards"),
 ("JP-Tmd","2011-12-16"):("surface_pressure",),
 ("JP-Tmd","2011-12-17"):("surface_pressure",),
 ("JP-Tmd","2022-04-08"):("surface_pressure",)
}
RAW={"surface_pressure":("sp","Pa",1000.0),
     "2m_temperature":("t2m","K",1.0),
     "surface_thermal_radiation_downwards":("strd","J m-2 hourly deaccumulated",3600.0)}
REQUIRED_HOURS={
 ("JP-Tef","2011-12-16"):"18:00,19:00,20:00,21:00,22:00,23:00",
 ("JP-Tef","2011-12-17"):"00:00,01:00",
 ("JP-Tef","2022-04-08"):"14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00",
 ("JP-Tmd","2005-08-11"):"14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00",
 ("JP-Tmd","2011-12-16"):"18:00,19:00,20:00,21:00,22:00,23:00",
 ("JP-Tmd","2011-12-17"):"00:00,01:00,02:00",
 ("JP-Tmd","2022-04-08"):"14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00"
}
MAX_SIZE=25*1024*1024
MAX_CSV=1000000
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()
def load_json(path):
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict):raise ValueError("Expected original Stage05AR JSON dictionary")
    return v
def about_path(p):
    try:m=p.lstat().st_mode
    except FileNotFoundError:return "ABSENT"
    if stat.S_ISLNK(m):return "SYMLINK_HOLD"
    return "REGULAR" if stat.S_ISREG(m) else "NONREGULAR_HOLD"
def validate(plan,science):
    if (plan.get("stage")!="JapanFlux Stage05AR"
        or plan.get("status")!="TWO_ORIGINAL_SOURCE_BIF_COORDS_VERIFIED_SEVEN_JST_CANDIDATE_CDS_DAYS_PREVIEW"
        or plan.get("original_source_coordinate_sites_verified")!=2
        or plan.get("candidate_UTC_site_days")!=7
        or plan.get("user_selected_time_hypothesis")!=CLOCK
        or plan.get("original_source_time_basis_proven") is not False
        or plan.get("CDS_requests")!=0
        or plan.get("original_ZIP_or_forcing_modified") is not False
        or plan.get("all_45_original_source_QC2_fields_HOLD") is not True):
        raise ValueError("Actual Stage05AR source BIF and user-time science gate altered")
    if (science.get("stage")!="JapanFlux Stage05AR"
        or science.get("status")!="BOTH_ORIGINAL_JPF_BIF_GEOLOCATIONS_VERIFIED_CANDIDATE_TIME_HOLD"
        or science.get("original_source_coordinate_sites_verified")!=2
        or science.get("candidate_UTC_fields")!=18
        or science.get("candidate_site_days")!=7
        or science.get("previous_independent_context_fields")!=27
        or science.get("prior_strong_label")!=22
        or science.get("new_context_only")!=5
        or science.get("source_readme_solar_vs_JST_clock_conflict")!="PRESERVED"
        or science.get("operator_time_assumption")!=CLOCK
        or science.get("source_time_verified") is not False
        or science.get("science_halfhour_replacement_approved") is not False
        or science.get("CDS_requests_this_stage")!=0
        or science.get("all_45_source_QC2_fields_HOLD") is not True):
        raise ValueError("Stage05AR exact original science-hold summary altered")
    roster=science.get("original_site_coordinate_roster",[])
    if len(roster)!=2 or {r["site"] for r in roster}!=set(ORIGINAL_SITES):
        raise ValueError("Stage05AR original source Tef/Tmd roster missing")
    for r in roster:
        ex=ORIGINAL_SITES[r["site"]]
        if (r["original_BIF_sha256"]!=ex["bif_sha"]
            or r["UTC_OFFSET_hours"]!=9
            or r["clock_status"]!=CLOCK+"_ORIGINAL_README_SOLAR_CONFLICT"
            or r["source_repair_status"]!="SCIENCE_HOLD_NOT_REPLACEMENT_APPROVED"
            or not all(math.isclose(float(r[name]),ex[name],abs_tol=1e-7)
                       for name in ("latitude","longitude","elevation_m"))):
            raise ValueError("Stage05AR original SHA-attested source position changed "+r["site"])
    days=plan.get("site_day_requests",[])
    if len(days)!=7:raise ValueError("Need all seven source-attested candidate UTC dates")
    verified={}
    for r in days:
        site=r["site"];day=r["UTC_day_candidate"]
        k=site,day
        if k in verified or k not in VARS or date.fromisoformat(day).isoformat()!=day:
            raise ValueError("Unexpected/duplicate original candidate site UTC-day")
        ex=ORIGINAL_SITES[site]
        request=r["request"]
        assert_vars=sorted(VARS[k])
        if (r["operator_selected_time_hypothesis"]!=CLOCK
            or r["original_source_UTC_timebase_verified"] is not False
            or r["original_source_README_says_solar_time"] is not True
            or r["original_BIF_SHA256"]!=ex["bif_sha"]
            or r["source_ERA5L_grid_cell_unverified"] is not True
            or r["CDS_submissions_this_stage"]!=0
            or r["repair_approved"] is not False
            or r["request_status"]!="PREVIEW_ONLY_NO_EXTERNAL_CDS_REQUEST"
            or r["dataset"]!=DATASET
            or request.get("data_format")!="csv"
            or request.get("date")!=day+"/"+day
            or request.get("variable")!=assert_vars
            or sorted(r["required_UTC_hour_clocks"])!=REQUIRED_HOURS[k].split(",")
            or not r["required_variable_UTC_hour_pairs"]
            or not r["requested_event_native_keys"]
            or not all(math.isclose(float(r["tower_"+dim]),ex[name],abs_tol=1e-7)
                 for dim,name in (("latitude","latitude"),("longitude","longitude")))
            or not math.isclose(float(r["tower_elevation_m"]),ex["elevation_m"],abs_tol=1e-7)
            or any(not math.isclose(float(request["location"][dim]),ex[dim],abs_tol=1e-7)
                   for dim in ("latitude","longitude"))):
            raise ValueError("Stage05AR original date/variable/hour/BIF coordinate evidence changed "+str(k))
        pairs={(p["hour"],p["variable"]) for p in r["required_variable_UTC_hour_pairs"]}
        if (len(pairs)!=len(r["required_variable_UTC_hour_pairs"])
            or {a for a,b in pairs}!=set(r["required_UTC_hour_clocks"])
            or {b for a,b in pairs}!=set(assert_vars)):
            raise ValueError("Stage05AR exact variable-hour pair integrity changed "+str(k))
        verified[k]=r
    if set(verified)!=set(VARS):raise ValueError("Original seven-day source roster incomplete")
    return verified
def inspect_csv_zip(path,site,day,requested_vars):
    if about_path(path)!="REGULAR" or not 0<path.stat().st_size<MAX_SIZE:
        raise ValueError("Returned original CDS payload not a reasonable regular ZIP")
    if not zipfile.is_zipfile(path):raise ValueError("CDS response was not a ZIP; retain partial")
    expected={RAW[v][0] for v in requested_vars}
    base={"valid_time","latitude","longitude"}
    seen=set();grids=set();members=[]
    with zipfile.ZipFile(path) as z:
        files=[info for info in z.infolist() if not info.is_dir()]
        if not 1<=len(files)<=len(expected):raise ValueError("Unexpected number of CDS CSV files")
        if z.testzip() is not None:raise ValueError("Returned CDS ZIP CRC failure")
        for info in files:
            n=PurePosixPath(info.filename)
            if (n.is_absolute() or ".." in n.parts or "\\" in info.filename
                or not info.filename.lower().endswith(".csv")
                or info.file_size>MAX_CSV):
                raise ValueError("Unsafe or oversized CDS CSV member")
            reader=csv.DictReader(io.StringIO(z.read(info).decode("utf-8-sig")))
            fields=reader.fieldnames or []
            if len(fields)!=len(set(fields)):
                raise ValueError("Duplicate CDS original CSV columns")
            cols=set(fields)-base
            if not base<=set(fields) or not cols or not cols<=expected or len(fields)!=len(base)+len(cols):
                raise ValueError("CDS original CSV variables/schema not requested")
            rows=list(reader)
            if len(rows)!=24:raise ValueError("CDS original CSV needs 24 whole UTC hours")
            for rec in rows:
                instant=datetime.strptime(rec["valid_time"],"%Y-%m-%d %H:%M:%S")
                if instant.date().isoformat()!=day or instant.minute or instant.second:
                    raise ValueError("CDS original returned wrong UTC day or fractional hour")
                lat=float(rec["latitude"]);lon=float(rec["longitude"])
                ex=ORIGINAL_SITES[site]
                if (not all(math.isfinite(x) for x in (lat,lon))
                    or abs(lat-ex["latitude"])>0.11 or abs(lon-ex["longitude"])>0.11):
                    raise ValueError("Returned CDS grid not near original source tower")
                grids.add((lat,lon))
                for var in cols:
                    key=var,instant.hour
                    if key in seen:raise ValueError("CDS duplicate variable x UTC hour")
                    seen.add(key)
                    x=float(rec[var])
                    if not math.isfinite(x):raise ValueError("CDS nonfinite variable")
                    if (var=="sp" and not 0<x/1000<120) or (
                       var=="t2m" and not 180<x<340) or (
                       var=="strd" and not 0<=x/3600<1500):
                        raise ValueError("CDS nonphysical source model hour "+var)
            members.append(info.filename)
    if seen!={(v,h) for v in expected for h in range(24)} or len(grids)!=1:
        raise ValueError("Missing requested variable×24 UTC hours or incoherent source grid")
    lat,lon=next(iter(grids))
    return {"ZIP_bytes":path.stat().st_size,
       "ZIP_SHA256":sha(path),
       "original_CDS_CSV_members":members,
       "validated_raw_columns":sorted(expected),
       "independent_variable_hour_count":len(seen),
       "ERA5L_grid_lat":lat,"ERA5L_grid_lon":lon,
       "source_tower_lat":ORIGINAL_SITES[site]["latitude"],
       "source_tower_lon":ORIGINAL_SITES[site]["longitude"],
       "source_tower_elevation_m":ORIGINAL_SITES[site]["elevation_m"],
       "strd_units_if_requested":"CDS_TIMESERIES_ALREADY_DEACCUMULATED_J_M2_HOURLY_DIVIDE_3600_TO_W_M2_NOT_DIFFERENCE",
       "source_grid_elevation":"UNVERIFIED",
       "original_clock":"OPERATOR_PLUS9_JST_HYPOTHESIS_NOT_RELEASE_SOURCE_VERIFIED"}
def selftest():
    assert len(VARS)==len(REQUIRED_HOURS)==7 and sum(len(v) for v in VARS.values())==9
    assert len(ORIGINAL_SITES)==2
    assert "JP-Tef" in ORIGINAL_SITES and "JP-Tmd" in ORIGINAL_SITES
    assert set(v for values in VARS.values() for v in values)==set(RAW)
    assert 720000/3600==200
    assert (datetime(2011,12,17,6)-datetime(2011,12,16,21)).total_seconds()==9*3600
    # In-memory regression of original CDS zip data; no filesystem/network.
    mem=io.BytesIO()
    site,day="JP-Tef","2011-12-16"
    rows=[{"valid_time":f"{day} {hour:02d}:00:00",
            "latitude":45.1,"longitude":142.1,"strd":720000+hour*200}
          for hour in range(24)]
    s=io.StringIO()
    writer=csv.DictWriter(s,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    with zipfile.ZipFile(mem,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("cds.csv",s.getvalue())
    # Can only inspect ZIP from a path in the real run. In-memory field test:
    with zipfile.ZipFile(mem) as z:
        rd=csv.DictReader(io.StringIO(z.read("cds.csv").decode()))
        obs=list(rd)
        assert len(obs)==24 and float(obs[0]["strd"])/3600==200
    print("STAGE05AS SELF-TEST PASS | seven exact source BIF sites/days, one-day CDS ZIP 24UTC/units/grid, already deaccumulated STRD; NO NETWORK/WRITES")
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--stage05ar-plan",type=Path)
    ap.add_argument("--stage05ar-summary",type=Path)
    ap.add_argument("--output-dir",type=Path)
    ap.add_argument("--submit",action="store_true")
    ap.add_argument("--site",choices=tuple(ORIGINAL_SITES))
    ap.add_argument("--utc-date")
    a=ap.parse_args()
    if a.self_test:selftest();return
    if any(p is None for p in (a.stage05ar_plan,a.stage05ar_summary,a.output_dir)):
        ap.error("Both actual Stage05AR plan/summary and output-dir required")
    valid=validate(load_json(a.stage05ar_plan),load_json(a.stage05ar_summary))
    if not a.submit:
        if a.site or a.utc_date:ap.error("--site/--utc-date only with explicit --submit")
        print("STAGE05AS SEVEN-DAY VERIFIED SOURCE-BIF AND JST-HYPOTHESIS PREVIEW PASS | NO CDS / SLURM")
        for (site,day),item in sorted(valid.items()):
            print("PILOT_ELIGIBLE_NOT_SUBMITTED",site,day,"VARIABLES",",".join(item["request"]["variable"]),
              "ORIGINAL_HOURS",",".join(item["required_UTC_hour_clocks"]))
        print("NO CDS REQUEST; ALL 45 ORIGINAL QC2 FIELDS HOLD")
        return
    if not a.site or not a.utc_date or (a.site,a.utc_date) not in valid:
        ap.error("Explicit --submit requires one of exact seven original source site/date combinations")
    # Initial opt-in pilot MUST first verify that a sole-site/day returned file
    # matches known original request. Later dates may be submitted after pilot.
    k=a.site,a.utc_date
    if k!=("JP-Tef","2011-12-16"):
        ap.error("Initial Stage05AS CDS pilot is JP-Tef 2011-12-16 only; verify before other days")
    item=valid[k]
    output=a.output_dir
    if output.is_symlink():ap.error("CDS output root cannot be symlink")
    target=output/"downloads"/f"{a.site}_ERA5Land_timeseries_{a.utc_date.replace('-','')}_CSV_response.zip"
    partial=Path(str(target)+".partial")
    extras=(target,target.with_suffix(".csv"),target.with_suffix(".nc"),partial)
    if any(about_path(x)!="ABSENT" for x in extras):
        ap.error("Existing CDS ZIP/CSV/NC/partial: refuse overwrite; investigate first")
    if about_path(output)!="ABSENT" and not output.is_dir():
        ap.error("Output root must be normal directory or absent")
    if not (Path.home()/".cdsapirc").is_file():
        raise RuntimeError("Missing private CDS ~/.cdsapirc credentials or licence acceptance")
    try:import cdsapi
    except ImportError as e:raise RuntimeError("cdsapi unavailable; activate existing clm_fates_env") from e
    target.parent.mkdir(parents=True,exist_ok=True)
    print("STAGE05AS EXPLICIT ONE-DAY CANDIDATE JST+9 DIAGNOSTIC CDS REQUEST | NO MODEL / REPAIR")
    print("DATASET",DATASET,"SITE",a.site,"CANDIDATE_UTC_DAY",a.utc_date)
    print("ORIGINAL_BIF_SHA256",item["original_BIF_SHA256"])
    print("ORIGINAL_TOWER",item["tower_latitude"],item["tower_longitude"],item["tower_elevation_m"])
    print("REQUEST_NONSECRET",json.dumps(item["request"],sort_keys=True))
    print("OUTPUT_ZIP_TARGET",target)
    # The CDS library uses credentials privately, not written into reports.
    cdsapi.Client().retrieve(DATASET,item["request"]).download(str(partial))
    if about_path(partial)!="REGULAR":
        raise RuntimeError("CDS retrieval did not return a regular staging file")
    print("CDS_RETURNED_PARTIAL_BYTES",partial.stat().st_size)
    try:meta=inspect_csv_zip(partial,a.site,a.utc_date,item["request"]["variable"])
    except (OSError,ValueError,UnicodeError,RuntimeError,zipfile.BadZipFile,KeyError) as e:
        print("CDS_RETURNED_PAYLOAD_CONTENT_SCIENCE_HOLD_PARTIAL_RETAINED",type(e).__name__,str(e))
        raise
    # Only after ALL data source checks succeed commit new response by rename.
    if any(about_path(x)!="ABSENT" for x in (target,target.with_suffix(".csv"),target.with_suffix(".nc"))):
        raise RuntimeError("Existing source payload conflict post-download; retain .zip.partial")
    partial.rename(target)
    # Reports exist in derived user HOME only; no original JPF data changed.
    result=output/f"stage05as_{a.site}_{a.utc_date}_original_CDS_source_payload_VALIDATED_NOT_REPAIR.json"
    if result.exists():raise RuntimeError("Report collision: ZIP verified but prior report exists; no overwrite")
    obj={"stage":"JapanFlux Stage05AS",
         "status":"ONE_OPERATOR_JST_CANDIDATE_CDS_SOURCE_ZIP_24UTC_SCIENCE_VALIDATED_NOT_REPAIR",
         "site":a.site,"candidate_UTC_day":a.utc_date,
         "source_time_hypothesis":CLOCK,
         "original_source_timebase_definitively_proven":False,
         "source_BIF_SHA256":item["original_BIF_SHA256"],
         "requested_original_variables":item["request"]["variable"],
         "CDS_dataset":DATASET,"observed_source_archive_path":str(target),
         "response":meta,
         "original_QC2_fields_HOLD":45,
         "CDS_requests_this_stage":1,
         "original_source_or_forcing_modified":False,
         "scientific_halfhour_replacements_approved":False,
         "Slurm_jobs":0}
    with result.open("x",encoding="utf-8") as f:
        json.dump(obj,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AS ORIGINAL CDS ZIP CRC / 24UTC / VARIABLE / GRID SCIENCE PASS | NO REPAIR")
    print("RETURNED_ZIP",target,"BYTES",meta["ZIP_bytes"],"SHA256",meta["ZIP_SHA256"])
    print("VERIFIED_HOURLY_VALUES",meta["independent_variable_hour_count"],
          "RAW_COLUMNS",meta["validated_raw_columns"])
    print("MODEL_GRID",meta["ERA5L_grid_lat"],meta["ERA5L_grid_lon"],
          "ORIGINAL_TOWER",item["tower_latitude"],item["tower_longitude"])
    print("ORIGINAL_CDS_SOURCE_AUDIT",result)
    print("ORIGINAL_CLOCK_STILL_USER_JST_ASSUMPTION; ALL 45 QC2 FIELDS HOLD; NO FORCING/MODEL/SLURM")
if __name__=="__main__":main()

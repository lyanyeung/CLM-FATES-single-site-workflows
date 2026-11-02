#!/usr/bin/env python3
"""JapanFlux Stage05S — verified ERA5-Land timeseries CDS single-day PILOT.

Default: purely local PREVIEW of 9 source-verified site×UTC-date windows.
Optional: one explicit --submit --site JP-Khw --utc-date YYYY-MM-DD requests
one site's one *entire UTC day*, not just sparse 54 required hours.
CDS dataset: reanalysis-era5-land-timeseries
Request: {variable, location:{latitude,longitude}, date:"YYYY-MM-DD/YYYY-MM-DD", data_format:"csv"}
API form & licence must be checked by operator; no secrets ever printed or stored.
NO original source, forcing, model cases or Slurm changes, NO automated repairs.
JP-Tef and JP-Tmd time basis remains unresolved and are never permitted.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path

SITES=("JP-Fjy","JP-Khw","JP-Yms")
VARIABLES=("surface_pressure","2m_temperature","surface_thermal_radiation_downwards")
DATASET="reanalysis-era5-land-timeseries"
EXPECTED_COUNT=87

def file_sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            data=f.read(1024*1024)
            if not data:break
            h.update(data)
    return h.hexdigest()

def validate(windows:list[dict], provenance:dict)->list[dict]:
    if (provenance.get("stage")!="JapanFlux Stage05R"
        or provenance.get("status")!="SOURCE_VERIFIED_3SITE_87_VAR_HOUR_REFERENCE_PLAN_NO_CDS"
        or provenance.get("site_count")!=3
        or provenance.get("requested_site_UTC_hours")!=54
        or provenance.get("requested_variable_hour_pairs")!=87
        or provenance.get("site_UTC_day_windows")!=9
        or provenance.get("CDS_submissions")!=0
        or provenance.get("independent_ERA5L_acquired") is not False
        or provenance.get("time_conflict_sites_excluded")!=["JP-Tef","JP-Tmd"]
        or provenance.get("repair_scientifically_approved") is not False):
        raise ValueError("Require actual science-gated Stage05R 3/5 provenance summary")
    if len(windows)!=9:
        raise ValueError("Expected 9 site×UTC-date windows")
    keys=set(); sites=set(); output=[]
    source_hours=set(); source_vhours=set()
    for w in windows:
        site=w["site"];day=w["UTC_date"]
        if site not in SITES or (site,day) in keys:
            raise ValueError("Unexpected/duplicate site+UTC date")
        keys.add((site,day)); sites.add(site)
        parsed=date.fromisoformat(day)
        if parsed.isoformat()!=day:
            raise ValueError("Bad UTC date")
        lat=float(w["tower_latitude"]);lon=float(w["tower_longitude"])
        if not (math.isfinite(lat) and math.isfinite(lon) and
                20<=lat<=47 and 120<=lon<=154):
            raise ValueError("Tower coordinates missing/not geographically Japanese")
        if w.get("coordinates_are_tower_not_ERA5L_grid") is not True:
            raise ValueError("Cannot treat tower coordinate as matched ERA5-Land grid")
        if w.get("CDS_submission_approved") is not False:
            raise ValueError("Source request has unexpected submit approval")
        if not isinstance(w.get("original_source_BIF_SHA256"),str) or len(w["original_source_BIF_SHA256"])!=64:
            raise ValueError("Original source BIF sha missing")
        vars_=w.get("required_variables_this_day")
        hours=w.get("UTC_hours")
        if not isinstance(vars_,list) or len(vars_)!=len(set(vars_)) or not set(vars_)<=set(VARIABLES) or not vars_:
            raise ValueError("Invalid original science-selected variable names")
        if not isinstance(hours,list) or len(hours)!=len(set(hours)) or not hours:
            raise ValueError("Invalid requested UTC hours")
        for clock in hours:
            dt=datetime.strptime(day+" "+clock,"%Y-%m-%d %H:%M")
            if dt.minute!=0 or dt.date()!=parsed:
                raise ValueError("Non-hourly or inconsistent UTC clock")
            source_hours.add((site,day,clock))
        # Important: original variable scope may differ by hour. The input summary
        # establishes 87 exact variable-hour pairs, not the date-wide Cartesian product.
        query={
            "variable": sorted(vars_),
            "location":{"latitude":lat,"longitude":lon},
            "date":day+"/"+day,
            "data_format":"csv",
        }
        output.append({
            "site":site,"utc_day":day,"source_bif_sha256":w["original_source_BIF_SHA256"],
            "tower_elevation_m":w["tower_elevation_m"],
            "required_utc_hours":sorted(hours),"required_variables":sorted(vars_),
            "required_utc_hours_count":len(hours),
            "dataset":DATASET,"request":query,
            "request_scope_warning":"CDS timeseries date-range returns FULL 24h UTC day, not only requested event hours. Extract exactly Stage05R matched hours afterwards.",
            "data_and_science_state":"NOT_SUBMITTED_UNVERIFIED_GRID_AND_UNAPPROVED_REPAIR"
        })
    if sites!=set(SITES) or len(source_hours)!=54:
        raise ValueError("3-site membership or 54 site×UTC-hour invariant failed")
    if EXPECTED_COUNT != provenance["requested_variable_hour_pairs"]:
        raise ValueError("87 field hour provenance changed")
    return sorted(output,key=lambda v:(v["site"],v["utc_day"]))

def safe_target(out:Path,site:str,day:str)->Path:
    safe=day.replace("-","")
    return out/"downloads"/f"{site}_ERA5Land_timeseries_{safe}_CSV_response.zip"

def submit_one(item:dict,out:Path)->None:
    try:
        import cdsapi
    except ImportError as exc:
        raise RuntimeError("No cdsapi package in current Python; install in isolated scientific conda env") from exc
    # No API key or .cdsapirc contents are printed by this script.
    if not (Path.home()/".cdsapirc").is_file():
        raise RuntimeError("~/.cdsapirc not found: configure CDS API credentials privately and accept dataset licence first")
    site=item["site"];day=item["utc_day"]
    target=safe_target(out,site,day)
    if target.exists() or target.with_suffix(target.suffix+".partial").exists():
        raise RuntimeError("Target already exists: refuse overwrite "+str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_suffix(target.suffix+".partial")
    print("STAGE05S EXPLICIT ONE-DAY CDS PILOT | NO MODEL/SLURM")
    print("DATASET",item["dataset"],"SITE",site,"UTC_DATE",day)
    print("REQUEST_NONSECRET",json.dumps(item["request"],sort_keys=True))
    print("DOWNLOAD_TARGET",str(target))
    # Operator's real API token is managed by cdsapi through ~/.cdsapirc.
    # API access is external and may fail if user has not accepted licence.
    client=cdsapi.Client()
    client.retrieve(item["dataset"],item["request"]).download(str(temporary))
    if not temporary.is_file() or temporary.stat().st_size==0:
        raise RuntimeError("CDS response missing or empty")
    # CDS timeseries with CSV may return archive or plain CSV depending on
    # response packaging. Detect the returned payload; never mislabel a CSV.
    with temporary.open("rb") as f:
        magic=f.read(8)
    if magic.startswith(b"PK\x03\x04"):
        actual=target
        payload="ZIP"
    elif magic.startswith(b"CDF") or magic.startswith(b"\x89HDF"):
        actual=target.with_suffix(".nc")
        payload="NetCDF_UNEXPECTED_REVIEW"
    else:
        actual=target.with_suffix(".csv")
        payload="CSV_OR_OTHER_TEXT_REVIEW"
    if actual.exists():
        raise RuntimeError("Detected output already exists; will not overwrite")
    temporary.rename(actual)
    print("CDS_PILOT_RESPONSE_WRITTEN",actual)
    print("DETECTED_PAYLOAD",payload,"BYTES",actual.stat().st_size,"SHA256",file_sha256(actual))
    print("SCIENCE_HOLD: No field contents have yet been verified for UTC, units, grid coordinates or physical plausibility")
    print("NO ORIGINAL DATA / FORCING / MODEL CHANGES")

def self_test()->None:
    assert safe_target(Path("/tmp/test"),"JP-Khw","2005-08-11").name=="JP-Khw_ERA5Land_timeseries_20050811_CSV_response.zip"
    assert date.fromisoformat("2005-08-11").isoformat()=="2005-08-11"
    assert set(SITES).isdisjoint(("JP-Tef","JP-Tmd"))
    print("STAGE05S SELF-TEST PASS | 3-site/9-day source gates, explicit pilot only, NO NETWORK OR WRITES")

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage05r-windows",type=Path)
    p.add_argument("--stage05r-summary",type=Path)
    p.add_argument("--output-dir",type=Path)
    p.add_argument("--submit",action="store_true",help="EXPLICITLY submit one site+date to CDS")
    p.add_argument("--site",choices=SITES)
    p.add_argument("--utc-date")
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.stage05r_windows,a.stage05r_summary,a.output_dir)):
        p.error("Need Stage05R windows JSON, summary JSON and --output-dir")
    windows=json.loads(a.stage05r_windows.read_text(encoding="utf-8"))
    provenance=json.loads(a.stage05r_summary.read_text(encoding="utf-8"))
    plan=validate(windows,provenance)
    out=a.output_dir
    if a.submit:
        if a.site is None or a.utc_date is None:
            p.error("--submit requires --site AND --utc-date; never batch-submit")
        selection=[v for v in plan if v["site"]==a.site and v["utc_day"]==a.utc_date]
        if len(selection)!=1:
            p.error("Pilot site/date absent from original Stage05R science-verified windows")
        submit_one(selection[0],out)
        return
    if a.site is not None or a.utc_date is not None:
        p.error("--site/--utc-date are only supported with explicit --submit")
    if out.exists():
        p.error("Preview output dir already exists, use fresh output dir")
    out.mkdir(parents=True)
    planpath=out/"stage05s_9_CDS_timeseries_one_day_requests_PREVIEW_ONLY.json"
    with planpath.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05S","dataset":DATASET,
                   "validated_site_count":3,"UTC_day_windows":len(plan),
                   "source_required_site_UTC_hours":54,
                   "source_required_variable_UTC_hour_pairs":87,
                   "model_science_approved":False,
                   "CDS_calls_made":0,
                   "site_day_pilot_requests":plan},f,indent=2,ensure_ascii=False)
        f.write("\n")
    print("STAGE05S PREVIEW VALIDATION PASS | NO CDS / ZIP / SLURM / FORCING")
    print("VERIFIED_SITES",",".join(SITES),"UTC_DAY_REQUESTS",len(plan))
    print("SOURCE_SCOPE_SITE_HOURS 54 VARIABLE_HOURS 87")
    for it in plan:
        print("PILOT",it["site"],it["utc_day"],"VARS",",".join(it["required_variables"]),
              "UTC_HOURS",",".join(it["required_utc_hours"]))
    print("PREVIEW_REQUEST_JSON",planpath)
    print("NEXT: only after CDS licence/credential verification run --submit --site <one_approved_site> --utc-date YYYY-MM-DD")
    print("NOTE: CDS time-series returns full 24-hour days, not a sparse 87-row dataset")
    print("NO DATA RETRIEVED; ALL 45 SOURCE VARIABLES REMAIN HOLD")

if __name__=="__main__":
    main()

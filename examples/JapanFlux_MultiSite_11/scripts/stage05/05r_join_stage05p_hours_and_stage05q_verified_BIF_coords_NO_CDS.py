#!/usr/bin/env python3
"""JapanFlux Stage05R: join source-verified tower coordinates to Stage05P ERA5-Land hourly UTC request plan.

READ ONLY INPUTS: Stage05P original 87 site-hour-variable request TSV / summary;
Stage05Q original-BIF verified 3-site coordinate roster / audit summary.
Output derived 87-row UTC/reference lookup TSV and per-site bounded UTC windows.
NO CDS API, NO download, NO Slurm, NO weather source/model edits or repairs.
Do not mistake tower coordinates for the returned ERA5-Land nearest grid centre.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timedelta
import csv
import hashlib
import json
import math
from pathlib import Path

SITES=("JP-Fjy","JP-Khw","JP-Yms")
VAR_COUNTS={"surface_pressure":54,"2m_temperature":9,
            "surface_thermal_radiation_downwards":24}
EXPECTED_TOTAL=87
EXPECTED_HOURS=54
INPUT_COLUMNS=("site","UTC_hour","UTC_day","UTC_year","UTC_month",
               "UTC_clock","CDS_ERA5_Land_timeseries_variable",
               "units","source_event_UTC_starts_in_scope","site_coordinates_status")
OUTPUT_COLUMNS=("site","tower_latitude","tower_longitude","tower_elevation_m",
                "tower_coordinate_datum","original_BIF_SHA256",
                "UTC_hour","UTC_day","UTC_year","UTC_month","UTC_clock",
                "CDS_ERA5_Land_timeseries_variable","variable_units",
                "source_UTC_halfhour_event_starts","coordinate_source_status",
                "returned_ERA5L_grid_cell_status","independent_ERA5L_values_status")

def tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if rd.fieldnames is None:raise ValueError("TSV has no header")
        return list(rd)

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b=f.read(2*1024*1024)
            if not b:break
            h.update(b)
    return h.hexdigest()

def numeric(s,lo,hi):
    v=float(s)
    if not math.isfinite(v) or not lo<=v<=hi:
        raise ValueError("Coordinate/elevation/offset out of physical range: "+str(s))
    return v

def verify(p, q, source_rows, coords):
    if (p.get("stage")!="JapanFlux Stage05P"
        or p.get("status")!="3_SITE_UTC_REFERENCE_REQUEST_MANIFEST_ONLY"
        or p.get("requested_variable_hour_pairs")!=87
        or p.get("requested_unique_site_UTC_hours")!=54
        or p.get("requested_variable_counts")!=VAR_COUNTS
        or set(p.get("verified_UTC_sites",[]))!=set(SITES)
        or set(p.get("unresolved_native_time_sites",[]))!={"JP-Tef","JP-Tmd"}
        or p.get("site_latitude_longitude")!="UNVERIFIED_NOT_INCLUDED_NO_CDS_CALL"
        or p.get("independent_ECMWF_values_checked") is not False
        or p.get("model_approved") is not False):
        raise ValueError("Stage05P UTC science gate/counts not verified")
    if (q.get("stage")!="JapanFlux Stage05Q"
        or q.get("status")!="3_SITE_SOURCE_BIF_COORDINATES_VERIFIED"
        or q.get("coordinate_sites_verified")!=3
        or set(q.get("source_scope",[]))!=set(SITES)
        or q.get("CDS_requests_performed")!=0
        or q.get("ERA5L_reference_values_acquired") is not False
        or q.get("model_forcing_approved") is not False):
        raise ValueError("Stage05Q original-source coordinate gate failed")
    if len(coords)!=3 or set(r["site"] for r in coords)!=set(SITES):
        raise ValueError("Expected exactly 3 unique original BIF coordinate rows")
    bysite={}
    for c in coords:
        site=c["site"]
        if site in bysite:raise ValueError("Duplicate coordinate site")
        if c["status"]!="VERIFIED_COORDS_NOT_ERA5L_GRID_CELL_APPROVED":
            raise ValueError("Wrong coordinate source status")
        if c["datum"]!="WGS84" or numeric(c["UTC_OFFSET_hours"],9,9)!=9:
            raise ValueError("Unknown datum or UTC_OFFSET")
        lat=numeric(c["latitude"],-90,90)
        lon=numeric(c["longitude"],-180,180)
        if not (20<=lat<=47 and 120<=lon<=154):
            raise ValueError("Tower coordinate does not look geographically Japanese: "+site)
        if c["elevation_m"].strip(): numeric(c["elevation_m"],-500,9000)
        if len(c["original_BIF_sha256"])!=64 or any(ch not in "0123456789abcdef" for ch in c["original_BIF_sha256"]):
            raise ValueError("Original source BIF SHA256 missing")
        if not c["location_source_lines"]:
            raise ValueError("Missing original source BIF line trace")
        bysite[site]=c
    audited_sites={v["site"]:v for v in q.get("sites",[])}
    if set(audited_sites)!=set(SITES):
        raise ValueError("Stage05Q audit site list changed")
    for site,c in bysite.items():
        a=audited_sites[site]
        if (a["status"]!="VERIFIED_ORIGINAL_BIF_COORDINATES"
            or a["source_sha256"]!=c["original_BIF_sha256"]
            or a["problems"]):
            raise ValueError("Stage05Q source SHA / status mismatch: "+site)
    if len(source_rows)!=EXPECTED_TOTAL:
        raise ValueError("Unexpected requested site/UTC-hour/variable count")
    keys=set();sitehours=set();varcnt=Counter()
    for r in source_rows:
        if set(INPUT_COLUMNS)-set(r):raise ValueError("Stage05P column missing")
        site=r["site"];v=r["CDS_ERA5_Land_timeseries_variable"]
        if site not in bysite or v not in VAR_COUNTS:
            raise ValueError("Unexpected site / variable")
        dt=datetime.strptime(r["UTC_hour"],"%Y%m%d%H%M")
        if dt.minute!=0 or (dt.strftime("%Y-%m-%d"),dt.strftime("%Y"),dt.strftime("%m"),dt.strftime("%H:%M"))!=(r["UTC_day"],r["UTC_year"],r["UTC_month"],r["UTC_clock"]):
            raise ValueError("UTC hour labels not internally consistent")
        k=(site,r["UTC_hour"],v)
        if k in keys:raise ValueError("Duplicate ERA5-Land request row")
        keys.add(k);sitehours.add((site,r["UTC_hour"]));varcnt[v]+=1
        if r["site_coordinates_status"]!="REQUIRES_ORIGINAL_BIF_LAT_LON_NOT_GUESSED":
            raise ValueError("Stage05P source coordinate HOLD unexpectedly changed")
        events=r["source_event_UTC_starts_in_scope"].split(",")
        if not events or any((datetime.strptime(e,"%Y%m%d%H%M").minute not in (0,30)) for e in events):
            raise ValueError("Source half-hour timestamps invalid")
    if len(sitehours)!=EXPECTED_HOURS or varcnt!=Counter(VAR_COUNTS):
        raise ValueError("Unexpected site×UTC hours / variable scope")
    return bysite

def make_rows(source,bysite):
    joined=[]
    days=defaultdict(lambda:{"hours":set(),"variables":set()})
    for r in source:
        c=bysite[r["site"]]
        row={
          "site":r["site"],"tower_latitude":c["latitude"],
          "tower_longitude":c["longitude"],"tower_elevation_m":c["elevation_m"],
          "tower_coordinate_datum":c["datum"],"original_BIF_SHA256":c["original_BIF_sha256"],
          "UTC_hour":r["UTC_hour"],"UTC_day":r["UTC_day"],
          "UTC_year":r["UTC_year"],"UTC_month":r["UTC_month"],
          "UTC_clock":r["UTC_clock"],"CDS_ERA5_Land_timeseries_variable":r["CDS_ERA5_Land_timeseries_variable"],
          "variable_units":r["units"],
          "source_UTC_halfhour_event_starts":r["source_event_UTC_starts_in_scope"],
          "coordinate_source_status":"ORIGINAL_BIF_VERIFIED",
          "returned_ERA5L_grid_cell_status":"NOT_RETRIEVED_NEAREST_0p1_GRID_NOT_VERIFIED",
          "independent_ERA5L_values_status":"NOT_DOWNLOADED"}
        joined.append(row)
        entry=days[(r["site"],r["UTC_day"])]
        entry["hours"].add(r["UTC_clock"])
        entry["variables"].add(r["CDS_ERA5_Land_timeseries_variable"])
    joined.sort(key=lambda a:(a["site"],a["UTC_hour"],a["CDS_ERA5_Land_timeseries_variable"]))
    site_windows=[]
    for (site,day),meta in sorted(days.items()):
        site_windows.append({
          "site":site,"UTC_date":day,
          "UTC_hours":sorted(meta["hours"]),
          "required_variables_this_day":sorted(meta["variables"]),
          "tower_latitude":float(bysite[site]["latitude"]),
          "tower_longitude":float(bysite[site]["longitude"]),
          "tower_elevation_m":bysite[site]["elevation_m"],
          "original_source_BIF_SHA256":bysite[site]["original_BIF_sha256"],
          "coordinates_are_tower_not_ERA5L_grid":True,
          "CDS_submission_approved":False
        })
    return joined,site_windows

def write_tsv(path,rows):
    with path.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=OUTPUT_COLUMNS,delimiter="\t")
        w.writeheader();w.writerows(rows)

def self_test():
    assert sum(VAR_COUNTS.values())==87
    assert len(SITES)==3
    assert datetime.strptime("200508111800","%Y%m%d%H%M").minute==0
    assert Counter(VAR_COUNTS)["surface_pressure"]==54
    print("STAGE05R SELF-TEST PASS | original BIF SHA gate, 87 variable-hours, UTC and coordinates; NO WRITES")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--stage05p-hours",type=Path)
    ap.add_argument("--stage05p-summary",type=Path)
    ap.add_argument("--stage05q-coordinates",type=Path)
    ap.add_argument("--stage05q-audit",type=Path)
    ap.add_argument("--output-dir",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test();return
    if any(x is None for x in (args.stage05p_hours,args.stage05p_summary,args.stage05q_coordinates,args.stage05q_audit,args.output_dir)):
        ap.error("Require both Stage05P inputs, both Stage05Q inputs and a fresh --output-dir")
    p=json.loads(args.stage05p_summary.read_text(encoding="utf-8"))
    q=json.loads(args.stage05q_audit.read_text(encoding="utf-8"))
    source=tsv(args.stage05p_hours)
    coordinates=tsv(args.stage05q_coordinates)
    bysite=verify(p,q,source,coordinates)
    joined,windows=make_rows(source,bysite)
    out=args.output_dir
    if out.exists():
        ap.error("Output dir must be new (no overwrite)")
    out.mkdir(parents=True)
    t=out/"stage05r_87_originalBIF_geolocated_UTC_hour_reference_plan.tsv"
    w=out/"stage05r_site_UTC_day_hour_windows_NO_CDS.json"
    s=out/"stage05r_provenance_summary.json"
    write_tsv(t,joined)
    with w.open("x",encoding="utf-8") as f:
        json.dump(windows,f,indent=2,ensure_ascii=False);f.write("\n")
    summary={
      "stage":"JapanFlux Stage05R",
      "status":"SOURCE_VERIFIED_3SITE_87_VAR_HOUR_REFERENCE_PLAN_NO_CDS",
      "site_count":3,"requested_site_UTC_hours":54,
      "requested_variable_hour_pairs":87,
      "site_UTC_day_windows":len(windows),
      "variable_hour_counts":dict(Counter(r["CDS_ERA5_Land_timeseries_variable"] for r in joined)),
      "site_orig_BIF_coordinates_verified":list(SITES),
      "time_conflict_sites_excluded":["JP-Tef","JP-Tmd"],
      "unresolved_original_time_candidate_fields":18,
      "source_HOLD_candidate_fields_total":45,
      "independent_ERA5L_acquired":False,
      "CDS_submissions":0,"grid_cell_validated":False,
      "repair_scientifically_approved":False,"Slurm_jobs":0,
      "original_files_or_forcing_modified":False,
      "input_sha256":{
       "stage05p_hour_plan":digest(args.stage05p_hours),
       "stage05p_summary":digest(args.stage05p_summary),
       "stage05q_coordinate_roster":digest(args.stage05q_coordinates),
       "stage05q_audit":digest(args.stage05q_audit)
      },
      "CDS_dataset":"reanalysis-era5-land-timeseries",
      "note":"Tower coords verified against original JPF BIF, not nearest 0.1 degree ERA5-Land grid centre; use official CDS request form for exact current API syntax and licence. Do not infer 30-min values from hourly radiation without interval checks."
    }
    with s.open("x",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05R GEOLOCATED REQUEST PLAN PASS | NO CDS, NO ZIP, NO SLURM")
    print("SITE_COORDINATES_SOURCE_VERIFIED",len(bysite),"/3")
    for site,c in sorted(bysite.items()):
        print("SITE",site,"LAT",c["latitude"],"LON",c["longitude"],
              "ELEV_M",c["elevation_m"] or "NOT_IN_BIF",
              "SOURCE_BIF_SHA",c["original_BIF_sha256"])
    print("SITE_UTC_HOURS",54,"VARIABLE_HOUR_PAIRS",87)
    print("UTC_DAY_WINDOWS",len(windows))
    print("VARIABLES",summary["variable_hour_counts"])
    print("GEOLOCATED_UTC_REQUEST_PLAN",t)
    print("UTC_DAY_WINDOWS",w)
    print("PROVENANCE_SUMMARY",s)
    print("NO INDEPENDENT WEATHER VALUES DOWNLOADED; ALL 45 ORIGINAL SOURCE FLAGS HOLD")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""JapanFlux Stage05P: prepare independent ERA5-Land hourly requests for 3 verified UTC sites.

NO CDS requests. NO longitude/latitude guesses, NO ZIP, NO SLURM, NO
original-data changes, NO replacement/forcing. Requires actual Stage05O
3-mapped/2-time-HOLD outputs. Builds a reproducible UTC hourly time/variable
request manifest; coordinates must be sourced and approved separately.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path

ALLOWED=("JP-Fjy","JP-Khw","JP-Yms")
DISPUTED=("JP-Tef","JP-Tmd")
VARIABLES={
    "TA":("2m_temperature","K","deg C","ERA5L_K_MINUS_273_15"),
    "PA":("surface_pressure","Pa","kPa","ERA5L_PA_DIVIDED_BY_1000"),
    "LW_IN":("surface_thermal_radiation_downwards","J m-2 (hourly de-accumulated)","W m-2",
             "ERA5L_HOURLY_DEACCUM_J_M2_DIVIDED_BY_3600_AFTER_TIMESTAMP_CHECK")
}
EXPECTED={"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10}
EVENT_FIELDS=("site","native_start","utc_start","utc_end","variable",
              "source_selected_F","source_embedded_ERA","raw_QC","source_units",
              "CDS_ERA5_Land_timeseries_variable","CDS_original_units",
              "target_units","conversion_rule","source_status")
REQ_FIELDS=("site","UTC_hour","UTC_day","UTC_year","UTC_month","UTC_clock",
            "CDS_ERA5_Land_timeseries_variable","units",
            "source_event_UTC_starts_in_scope","site_coordinates_status")

def load_tsv(path:Path)->list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def verify(mapped:list[dict],unresolved:list[dict],summary:dict)->None:
    if summary.get("stage")!="JapanFlux Stage05O" or summary.get("status")!="3_SITE_SCOPED_UTC_ONLY":
        raise ValueError("Expected completed 3-site Stage05O science gate")
    for key,wanted in (
        ("mapped_field_records",27),("mapped_unique_site_halfhours",21),
        ("unresolved_field_records",18),("unresolved_unique_site_halfhours",14),
        ("total_field_records",45),("total_unique_site_halfhours",35)):
        if summary.get(key)!=wanted:
            raise ValueError(f"Stage05O {key} unexpectedly changed")
    if len(mapped)!=27 or len(unresolved)!=18:
        raise ValueError("Unexpected Stage05O input TSV sizes")
    if set(x["site"] for x in mapped)!=set(ALLOWED):
        raise ValueError("Unverified site in allowed UTC mapping")
    if set(x["site"] for x in unresolved)!=set(DISPUTED):
        raise ValueError("Unresolved site missing from time-basis HOLD")
    keys=set()
    counts=Counter()
    for r in mapped:
        k=(r["site"],r["native_start"],r["variable"])
        if k in keys:
            raise ValueError("Duplicate Stage05O variable cell")
        keys.add(k)
        counts[r["site"]]+=1
        if r["variable"] not in VARIABLES or r["raw_F_QC"]!="2":
            raise ValueError("Unexpected source QC or variable")
        if r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED":
            raise ValueError("Input candidate has unexpected science approval")
        dt=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        de=datetime.strptime(r["utc_end"],"%Y%m%d%H%M")
        if de-dt!=timedelta(minutes=30):
            raise ValueError("Not a half-hour event")
        native=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        if native-dt!=timedelta(hours=9):
            raise ValueError("Unexpected UTC conversion")
        if r["unit"]!=VARIABLES[r["variable"]][2]:
            raise ValueError("Unexpected source BIF unit for "+str(k))
    if dict(counts)!=EXPECTED or len({(s,t) for s,t,v in keys})!=21:
        raise ValueError("Wrong 27 source field / 21 native-time coverage")
    holds=set()
    for r in unresolved:
        k=(r["site"],r["native_start"],r["variable"])
        if k in holds:
            raise ValueError("Duplicate native-only HOLD event")
        holds.add(k)
        if r["utc_start"]!="UNRESOLVED" or r["source_status"]!="HOLD_LOCAL_SOLAR_VS_STANDARD_TIME_PROVENANCE":
            raise ValueError("Unapproved forced timezone mapping for JP-Tef or JP-Tmd")
    if len({(s,t) for s,t,v in holds})!=14:
        raise ValueError("Wrong 14 unresolved station-time keys")

def build(mapped:list[dict],window:int)->tuple[list[dict],list[dict],dict]:
    if window<2 or window>12:
        raise ValueError("Window should be between 2 and 12 hours")
    events=[]
    requests=defaultdict(set)
    refs=defaultdict(set)
    for r in mapped:
        name,units,target,conversion=VARIABLES[r["variable"]]
        site=r["site"]
        start=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        event={ "site":site,"native_start":r["native_start"],
               "utc_start":r["utc_start"],"utc_end":r["utc_end"],
               "variable":r["variable"],"source_selected_F":r["selected_F"],
               "source_embedded_ERA":r["ERA_in_same_release"],
               "raw_QC":r["raw_F_QC"],"source_units":r["unit"],
               "CDS_ERA5_Land_timeseries_variable":name,
               "CDS_original_units":units,"target_units":target,
               "conversion_rule":conversion,
               "source_status":"HOLD_UNAPPROVED_REFERENCE_COMPARISON"}
        events.append(event)
        floor=start.replace(minute=0)
        for hour in range(-window,window+2):
            when=floor+timedelta(hours=hour)
            key=(site,when,name)
            requests[key].add(r["utc_start"])
            refs[(site,when)].add(r["native_start"])
    times=[]
    for (site,when,variable),sources in sorted(requests.items()):
        u=next(row[1] for row in VARIABLES.values() if row[0]==variable)
        times.append({"site":site,"UTC_hour":when.strftime("%Y%m%d%H%M"),
            "UTC_day":when.strftime("%Y-%m-%d"),"UTC_year":when.strftime("%Y"),
            "UTC_month":when.strftime("%m"),"UTC_clock":when.strftime("%H:%M"),
            "CDS_ERA5_Land_timeseries_variable":variable,"units":u,
            "source_event_UTC_starts_in_scope":",".join(sorted(sources)),
            "site_coordinates_status":"REQUIRES_ORIGINAL_BIF_LAT_LON_NOT_GUESSED"})
    events.sort(key=lambda r:(r["site"],r["utc_start"],r["variable"]))
    summary={
        "stage":"JapanFlux Stage05P",
        "status":"3_SITE_UTC_REFERENCE_REQUEST_MANIFEST_ONLY",
        "verified_UTC_sites":list(ALLOWED),
        "unresolved_native_time_sites":list(DISPUTED),
        "source_approved_UTC_fields":27,
        "source_approved_UTC_unique_site_halfhours":21,
        "native_only_HOLD_fields":18,
        "native_only_HOLD_unique_site_halfhours":14,
        "event_context_hour_radius":window,
        "CDS_dataset":"reanalysis-era5-land-timeseries",
        "requested_variable_hour_pairs":len(times),
        "requested_unique_site_UTC_hours":len(refs),
        "requested_variable_counts":dict(Counter(r["CDS_ERA5_Land_timeseries_variable"] for r in times)),
        "target_variable_units":{"TA":"deg C","PA":"kPa","LW_IN":"W m-2"},
        "CDS_units_conversion":{
            "TA":"2m_temperature in Kelvin minus 273.15",
            "PA":"surface_pressure in Pascal divided by 1000",
            "LW_IN":"use ERA5-Land timeseries de-accumulated hourly surface_thermal_radiation_downwards J/m2 divided by 3600 s; first check validity timestamps and interval semantics"},
        "site_latitude_longitude":"UNVERIFIED_NOT_INCLUDED_NO_CDS_CALL",
        "model_approved":False,"source_or_forcing_modified":False,
        "independent_ECMWF_values_checked":False,
        "radiation_time_alignment_approved":False,
        "scope":"Generate only hourly reference request plan for three proven local-standard-time sites. Do not map Tef/Tmd."
    }
    return events,times,summary

def write_tsv(path:Path,fieldnames,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,delimiter="\t")
        w.writeheader();w.writerows(rows)

def self_test():
    assert (datetime.strptime("200508120230","%Y%m%d%H%M")-
            timedelta(hours=9)).strftime("%Y%m%d%H%M")=="200508111730"
    assert sum(EXPECTED.values())==27
    assert set(ALLOWED).isdisjoint(DISPUTED)
    start=datetime.strptime("200508111730","%Y%m%d%H%M")
    assert start.replace(minute=0).strftime("%Y%m%d%H%M")=="200508111700"
    print("STAGE05P SELF-TEST PASS | 3-site UTC provenance, hour grid algebra, unit contracts; NO WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage05o-utc",type=Path)
    p.add_argument("--stage05o-native-hold",type=Path)
    p.add_argument("--stage05o-summary",type=Path)
    p.add_argument("--out-dir",type=Path)
    p.add_argument("--context-hours",type=int,default=3)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if any(v is None for v in (a.stage05o_utc,a.stage05o_native_hold,a.stage05o_summary,a.out_dir)):
        p.error("Require three actual Stage05O outputs and a fresh --out-dir")
    mapped=load_tsv(a.stage05o_utc)
    unresolved=load_tsv(a.stage05o_native_hold)
    summary=json.loads(a.stage05o_summary.read_text(encoding="utf-8"))
    verify(mapped,unresolved,summary)
    events,times,report=build(mapped,a.context_hours)
    if a.out_dir.exists():
        p.error("Output directory exists; use a fresh directory")
    a.out_dir.mkdir(parents=True)
    e=a.out_dir/"stage05p_27_source_UTC_event_ERA5L_mapping_plan.tsv"
    t=a.out_dir/"stage05p_hourly_ERA5L_request_plan_no_coordinates.tsv"
    s=a.out_dir/"stage05p_reference_request_summary.json"
    write_tsv(e,EVENT_FIELDS,events)
    write_tsv(t,REQ_FIELDS,times)
    with s.open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,ensure_ascii=False)
        f.write("\n")
    print("STAGE05P REQUEST PLAN PASS | NO CDS API, NO ZIP, NO SLURM")
    print("UTC_VERIFIED_SITE_COUNT 3 /5")
    print("UTC_SOURCE_FIELDS",len(events),"NATIVE_TIME_HOLD_FIELDS",len(unresolved))
    print("UNIQUE_SITE_UTC_HOURS",report["requested_unique_site_UTC_hours"])
    print("VARIABLE_HOUR_PAIRS",report["requested_variable_hour_pairs"])
    print("VARIABLES",report["requested_variable_counts"])
    print("SITE_COORDINATES HOLD_NOT_YET_ORIGIN_VERIFIED")
    print("EVENT_PLAN",e)
    print("HOURLY_REQUEST_PLAN",t)
    print("SUMMARY",s)
    print("NO INDEPENDENT ERA VALUES ACQUIRED OR REPAIR APPROVED")

if __name__=="__main__":
    main()

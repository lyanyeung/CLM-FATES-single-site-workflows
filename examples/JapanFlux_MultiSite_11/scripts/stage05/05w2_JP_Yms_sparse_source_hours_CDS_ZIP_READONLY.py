#!/usr/bin/env python3
"""Stage05W2: correct Stage05W's false Cartesian 9-hour × 2-variable gate.

Read-only science audit of independently downloaded JP-Yms 2005-08-11 ERA5-Land
CDS ZIP. Stage05P's source-variable-specific ±3h windows form a UNION, not
a complete 9×2 Cartesian product. Rebuild exact site/hour/variable/source-event
keys from Stage05O QC2 +9 UTC source, compare to Stage05R provenance, and
reuse the previously SHA-pinned Stage05W CDS ZIP parser. NO new CDS calls,
ZIP extraction, raw/source/forcing changes, Slurm, or repairs.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import hashlib
import importlib.util
import json
import math
from pathlib import Path

SITE="JP-Yms"
DAY="2005-08-11"
SOURCE_SITE_COUNTS={"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10}
VARS={"PA":("surface_pressure","kPa"),"LW_IN":("surface_thermal_radiation_downwards","W m-2")}
BIF_SHA="7c0a5ba5f137e28518f69ed14b255834fb5b223ac325556719abe5a55e8b0f56"
TOWER=(34.790278,135.840939,220.0)
ZIP_SHA="4bf228a3a53ab7fc6751b8e7438fb459570536ce6f54af2f81de5afc083b59d5"
OLD_STAGE05W_BLOB="c953a2d28a5dbc634179296e78c0b58ffa3be1df"

def tsv(path:Path)->list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        data=list(csv.DictReader(f,delimiter="\t"))
    if not data:
        raise ValueError("Empty source TSV")
    return data

def expect_from_stage05o(records:list[dict])->dict[tuple[str,str],set[str]]:
    if len(records)!=27 or Counter(x["site"] for x in records)!=Counter(SOURCE_SITE_COUNTS):
        raise ValueError("Original Stage05O 27 fields/3 sites invariant failed")
    wanted=defaultdict(set)
    all_keys=set()
    yms_count=Counter()
    for r in records:
        ident=(r["site"],r["native_start"],r["variable"])
        if ident in all_keys:
            raise ValueError("Duplicate original source event "+repr(ident))
        all_keys.add(ident)
        if r["raw_F_QC"]!="2" or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED":
            raise ValueError("Stage05O QC2/HOLD failed: "+repr(ident))
        native=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        if native-utc!=timedelta(hours=9):
            raise ValueError("Original source BIF+README UTC+9 mismatch")
        if r["site"]!=SITE:
            continue
        yms_count[r["variable"]]+=1
        if r["variable"] not in VARS:
            raise ValueError("Unexpected JP-Yms source selected variable")
        name,unit=VARS[r["variable"]]
        if r["unit"]!=unit:
            raise ValueError("Stage05O JPF original selected source units mismatch")
        a=float(r["selected_F"]);b=float(r["ERA_in_same_release"])
        if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9):
            raise ValueError("JPF source F/ERA numeric equality check failed")
        for hour in range(-3,5):  # stage05p --context-hours 3
            stamp=utc.replace(minute=0)+timedelta(hours=hour)
            if stamp.date().isoformat()==DAY:
                wanted[(stamp.strftime("%Y%m%d%H%M"),name)].add(r["utc_start"])
    if len(all_keys)!=27 or yms_count!=Counter({"PA":6,"LW_IN":4}):
        raise ValueError("JP-Yms source-variable 6 pressure /4 longwave original QC2 fields changed")
    if not wanted:
        raise ValueError("No original JP-Yms source-based UTC-hour reference keys")
    return dict(wanted)

def verify_source_keys(rem:dict, stage05r:list[dict], from05o:dict)->dict:
    if (rem.get("stage")!="JapanFlux Stage05V"
        or rem.get("status")!="NO_SUBMISSIONS_EIGHT_DAYS_PREVIEW_ONLY"
        or rem.get("remaining_count")!=8
        or rem.get("independent_CDS_requests_this_stage")!=0):
        raise ValueError("Original Stage05V site-day science gate not met")
    pending=rem["remaining_site_day_requests"]
    if len(pending)!=8 or len({(r["site"],r["utc_day"]) for r in pending})!=8:
        raise ValueError("Stage05V pending site/day list changed")
    selected=[r for r in pending if r["site"]==SITE and r["utc_day"]==DAY]
    if len(selected)!=1:
        raise ValueError("JP-Yms day absent or duplicate in original Stage05V")
    entry=selected[0]
    if (entry["source_bif_sha256"]!=BIF_SHA
        or set(entry["variable_scope"])!=set(x[0] for x in VARS.values())
        or set(entry["requested_source_UTC_hours"])!={f"{h:02d}:00" for h in range(14,23)}
        or abs(float(entry["original_tower_coordinates"]["latitude"])-TOWER[0])>1e-8
        or abs(float(entry["original_tower_coordinates"]["longitude"])-TOWER[1])>1e-8):
        raise ValueError("Stage05V JP-Yms source location/variable/time gate changed")
    if len(stage05r)!=87:
        raise ValueError("Stage05R exact original overall 87 variable-hour requests changed")
    scoped=[r for r in stage05r if r["site"]==SITE and r["UTC_day"]==DAY]
    actual={}
    for r in scoped:
        k=(r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"])
        if k in actual:
            raise ValueError("Duplicate original Stage05R source variable/hour")
        if (r["original_BIF_SHA256"]!=BIF_SHA
            or r["coordinate_source_status"]!="ORIGINAL_BIF_VERIFIED"
            or r["independent_ERA5L_values_status"]!="NOT_DOWNLOADED"
            or abs(float(r["tower_latitude"])-TOWER[0])>1e-8
            or abs(float(r["tower_longitude"])-TOWER[1])>1e-8
            or abs(float(r["tower_elevation_m"])-TOWER[2])>1e-8):
            raise ValueError("Stage05R original BIF location/source provenance changed")
        actual[k]=set(r["source_UTC_halfhour_event_starts"].split(","))
    missing=set(from05o)-set(actual)
    extra=set(actual)-set(from05o)
    if missing or extra:
        raise ValueError("Stage05R hours not identical to Stage05O-derived variable-specific source context. "
                         +repr({"missing":sorted(missing),"extra":sorted(extra)}))
    for k in from05o:
        if actual[k]!=from05o[k]:
            raise ValueError("Stage05R per-variable source-halfhour provenance mismatch "+repr(k))
    actual_hours={datetime.strptime(stamp,"%Y%m%d%H%M").strftime("%H:%M") for stamp,var in actual}
    if actual_hours!=set(entry["requested_source_UTC_hours"]):
        raise ValueError("Stage05V UNION of requested hours differs from Stage05R")
    counts=dict(Counter(v for _,v in actual))
    return {"source_variable_hour_pairs":len(actual),"variable_hour_counts":counts,
            "union_UTC_hours":sorted(actual_hours),
            "original_source_halfhour_field_count":10,
            "original_source_halfhour_event_counts":dict(Counter(x for k,v in actual.items() for x in v)),
            "source_reference_pairs_are_full_cartesian":len(actual)==len(actual_hours)*len(VARS)}

def original_parser(path:Path):
    raw=path.read_bytes()
    calculated=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
    if calculated!=OLD_STAGE05W_BLOB:
        raise ValueError("Old Stage05W original Git blob SHA changed; refuse unverified ZIP parser")
    spec=importlib.util.spec_from_file_location("original_stage05w_sha_pinned",path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.SITE!=SITE or mod.DAY!=DAY:
        raise ValueError("Original Stage05W parser source parameters changed")
    return mod

def self_test():
    x=datetime.strptime("200508111730","%Y%m%d%H%M").replace(minute=0)
    y=datetime.strptime("200508111830","%Y%m%d%H%M").replace(minute=0)
    a={x+timedelta(hours=j) for j in range(-3,5)}
    b={y+timedelta(hours=j) for j in range(-3,5)}
    assert len(a)==8 and len(b)==8 and len(a|b)==9
    assert len({(v,"pressure") for v in a}|{(v,"longwave") for v in b})==16
    print("STAGE05W2 SELF-TEST PASS | 9-hour UNION is not necessarily 18 variable-hour pairs; source-QC2 checks; NO WRITES")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--original-stage05w",type=Path)
    ap.add_argument("--stage05o-source-UTC",type=Path)
    ap.add_argument("--stage05v-remaining",type=Path)
    ap.add_argument("--stage05r-hours",type=Path)
    ap.add_argument("--cds-zip",type=Path)
    ap.add_argument("--expected-sha256",default=ZIP_SHA)
    ap.add_argument("--out-dir",type=Path)
    a=ap.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.original_stage05w,a.stage05o_source_UTC,a.stage05v_remaining,
                a.stage05r_hours,a.cds_zip,a.out_dir)):
        ap.error("Require original source-backed Stage05W, Stage05O/V/R data, raw CDS ZIP and fresh out dir")
    if a.expected_sha256!=ZIP_SHA:
        ap.error("Refuse any CDS ZIP SHA differing from the observed operator 936-byte original SHA")
    parser=original_parser(a.original_stage05w)
    from05o=expect_from_stage05o(tsv(a.stage05o_source_UTC))
    meta=verify_source_keys(
        json.loads(a.stage05v_remaining.read_text(encoding="utf-8")),
        tsv(a.stage05r_hours),from05o)
    if a.cds_zip.stat().st_size!=936:
        raise ValueError("Expected original actual JP-Yms CDS ZIP 936 bytes")
    csv_metadata,values=parser.inspect_zip(a.cds_zip,ZIP_SHA)
    if a.out_dir.exists():
        ap.error("Choose a new output directory, no overwriting prior reports")
    a.out_dir.mkdir(parents=True)
    t=a.out_dir/"stage05w2_Yms_20050811_independent_ERA5L_2x24_HOLD.tsv"
    j=a.out_dir/"stage05w2_CDS_source_and_sparse_hour_scope_audit.json"
    with t.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=parser.OUT_FIELDS,delimiter="\t")
        w.writeheader()
        w.writerows(sorted(values,key=lambda r:(r["UTC_valid_time"],r["variable"])))
    audit={
      "stage":"JapanFlux Stage05W2","status":"PASS_SOURCE_SPARSE_HOURS_AND_SECOND_REAL_CDS_ZIP",
      "site":SITE,"UTC_date":DAY,
      "raw_CDS_ZIP_SHA256":ZIP_SHA,
      "original_source_BIF_SHA256":BIF_SHA,
      "original_source_location":{"lat":TOWER[0],"lon":TOWER[1],"elevation_m":TOWER[2]},
      "original_CDS_zip_bytes":936,"CSV_members":csv_metadata,
      "hourly_independent_variable_records":len(values),
      "CDS_grid_lat_lon": [values[0]["CDS_grid_lat"],values[0]["CDS_grid_lon"]],
      "source_specific_scope":meta,
      "false_cartesian_gate_in_old_stage05w":"REMOVED_BY_SOURCE_VERIFIED_EXACT_KEYS",
      "independent_grid_elevation":"UNVERIFIED",
      "half_hour_replacement_approved":False,
      "original_source_or_model_forcing_modified":False,
      "CDS_calls_this_stage":0,"Slurm_submissions":0,
      "all_45_JPF_original_flagged_fields_HOLD":True
    }
    with j.open("x",encoding="utf-8") as f:
        json.dump(audit,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05W2 SOURCE-EXACT SPARSE-HOUR AND SECOND CDS ZIP AUDIT PASS | NO CDS / SLURM / REPAIR")
    print("ORIGINAL_JP_YMS_SOURCE_HOURS",",".join(meta["union_UTC_hours"]))
    print("ORIGINAL_VARIABLE_HOUR_PAIRS",meta["source_variable_hour_pairs"],
          "BY_VARIABLE",meta["variable_hour_counts"])
    print("CDS_ZIP_SHA256",ZIP_SHA,"CSV_MEMBERS",len(csv_metadata),"HOURLY_NUMERIC_VALUES",len(values))
    print("CDS_GRID",audit["CDS_grid_lat_lon"])
    for r in values:
        if r["UTC_valid_time"].endswith(("17:00Z","18:00Z","19:00Z")):
            print("ERA5L",r["UTC_valid_time"],r["variable"],
                  r["independent_converted_hourly_value"],r["converted_units"])
    print("CDS_VALUES",t)
    print("AUDIT_REPORT",j)
    print("NO JPF HALF-HOUR REPAIR; ALL 45 SOURCE FLAGS HOLD")

if __name__=="__main__":
    main()

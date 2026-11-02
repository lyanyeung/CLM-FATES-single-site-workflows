#!/usr/bin/env python3
"""JapanFlux Stage05AK — JP-Yms five original 2011 QC2 fields vs independent CDS.

Use only original Stage05O 27 UTC/JST source flags, Stage05R 87 original
source variable-hour plan, Stage05AH 22-strong-physical-context source-HOLD
coverage, latest Stage05AB six-day original ZIP CRC/grid audit, and BOTH
unaltered JP-Yms Dec16/17 CDS CSV ZIPs.

The specific "reanalysis-era5-land-timeseries" product already delivers
de-accumulated hourly strd [J m-2]. Therefore strd /3600 gives the MEAN
W m-2 over the preceding hour. DO NOT differ the hourly strd CSV samples.

Compare a source half-hour to nearby independent model hourly ENVELOPES;
this is physical-context diagnosis, NOT a pointwise observation substitute,
nor an automatic claim of new strong evidence or a science-approved repair.

ECMWF source: https://confluence.ecmwf.int/pages/viewpage.action?pageId=699689224
No CDS/network, Slurm, edits to source ZIP/forcing/model or replacements.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path,PurePosixPath

SITE="JP-Yms"
BIF_SHA="7c0a5ba5f137e28518f69ed14b255834fb5b223ac325556719abe5a55e8b0f56"
TOWER=(34.790278,135.840939,220.0)
DATES=("2011-12-16","2011-12-17")
SHA_BY_DAY={
    "2011-12-16":"edd1b8acd84b31d8a04f214850dd9f51d9471dbffb91664fa76a54a9b7539c0c",
    "2011-12-17":"bb50100065193cff70429c626603cd60e957882624db5fbee056f97a23b032f6"
}
SRC_COUNTS=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})
VARIABLES={"PA":("surface_pressure","sp","kPa",1000.0),
           "LW_IN":("surface_thermal_radiation_downwards","strd","W m-2",3600.0)}
COLUMN_NAMES=(
    "site","original_JST_halfhour_start","verified_source_UTC_start","variable",
    "original_JPF_selected_F","same_release_original_ERA","original_source_QC",
    "original_units","independent_hourly_units",
    "ERA5L_nearest_grid_lat","ERA5L_nearest_grid_lon",
    "independent_UTC_reference_labels","independent_reference_hourly_values",
    "independent_reference_min","independent_reference_max",
    "original_minus_nearest_hourly_envelope_gap",
    "outside_independent_hourly_envelope",
    "temporal_comparison_rule","independent_hourly_product_processing",
    "science_review_state","model_grid_elevation_status","CDS_source_ZIP_SHA256"
)
PASS="COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR"

def read_tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter="\t")
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):
            raise ValueError("Duplicate/missing original source TSV headers")
        items=list(r)
    if not items:raise ValueError("Source records empty")
    return items

def read_json(path):
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict):raise ValueError("Expected original JSON object")
    return v

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def science_source_guard(ah):
    if (ah.get("stage")!="JapanFlux Stage05AH"
        or ah.get("status")!="TWENTY_TWO_ORIGINAL_QC2_FIELDS_WITH_STRONG_INDEPENDENT_ERA5L_CONTEXT_HOLD"
        or ah.get("original_source_QC2_anomaly_fields")!=45
        or ah.get("independently_contextualized_original_source_fields")!=22
        or ah.get("by_site")!={"JP-Fjy":6,"JP-Khw":11,"JP-Yms":5}
        or ah.get("distinct_original_site_native_halfhours")!=17
        or ah.get("original_UTC_verified_fields_needing_independent_science_comparison")!=5
        or ah.get("original_native_clock_source_conflict_fields")!=18
        or ah.get("verified_independent_CDS_site_UTC_day_payloads")!=7
        or ah.get("remaining_unverified_CDS_site_UTC_days")!=2
        or ah.get("source_30min_replacement_approved") is not False
        or ah.get("all_45_original_source_anomaly_fields_HOLD") is not True
        or ah.get("CDS_requests_this_stage")!=0):
        raise ValueError("Stage05AH prior 22/45 evidence registry science hold changed")

def select_exact_source_fields(source,old22):
    if len(source)!=27 or Counter(r["site"] for r in source)!=SRC_COUNTS:
        raise ValueError("Original Stage05O 27-source UTC-verified field population changed")
    if len(old22)!=22 or Counter(r["site"] for r in old22)!=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":5}):
        raise ValueError("Stage05AH verified 22-original-field evidence population changed")
    bykey={}
    for r in source:
        k=(r["site"],r["native_start"],r["variable"])
        if k in bykey:raise ValueError("Duplicated source QC2 field")
        local=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        v=float(r["selected_F"]); embedded=float(r["ERA_in_same_release"])
        if (local-utc!=timedelta(hours=9)
            or r["raw_F_QC"]!="2"
            or r["source_status"]!="HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"
            or not all(math.isfinite(x) for x in (v,embedded))
            or not math.isclose(v,embedded,rel_tol=1e-12,abs_tol=1e-9)):
            raise ValueError("Original Stage05O JPF F=ERA/QC2/UTC source invariant changed")
        bykey[k]=r
    oldkeys=set()
    for r in old22:
        k=(r["site"],r["native_JST_halfhour_start"],r["variable"])
        if k not in bykey or k in oldkeys or r["source_QC"]!="2" or r["context_outside"]!="1":
            raise ValueError("Prior strong independent-context evidence or original site QC2 population changed")
        orig=bykey[k]
        if (not math.isclose(float(orig["selected_F"]),float(r["original_JPF_F"]),abs_tol=1e-9,rel_tol=1e-12)
            or r["repair_status"]!="SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT"):
            raise ValueError("Prior JPF source 22-field evidence altered")
        oldkeys.add(k)
    if len(oldkeys)!=22:raise ValueError("Prior source keys incomplete")
    newkeys=set(bykey)-oldkeys
    if len(newkeys)!=5 or {s for s,t,v in newkeys}!={SITE}:
        raise ValueError("Exact five new original JP-Yms source variable records missing")
    picked=[]
    for k in sorted(newkeys):
        r=bykey[k]
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        if (r["variable"] not in VARIABLES
            or r["unit"]!=VARIABLES[r["variable"]][2]
            or utc.date().isoformat() not in DATES):
            raise ValueError("JP-Yms new source date/variable/units not in science-approved scope")
        picked.append(r)
    historical=[r for r in source if r["site"]==SITE and
                (r["site"],r["native_start"],r["variable"]) in oldkeys]
    if len(historical)!=5:
        raise ValueError("JP-Yms historical original field evidence no longer five")
    return picked

def verify_stage05r_hours(source,rows):
    if len(rows)!=87:raise ValueError("Original Stage05R 87 variable-hour plan changed")
    allseen=set()
    for r in rows:
        key=r["site"],r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"]
        if key in allseen:raise ValueError("Duplicate original source reference variable-hour")
        allseen.add(key)
    observed={}
    for r in rows:
        if r["site"]==SITE and r["UTC_day"] in DATES:
            k=r["UTC_hour"],r["CDS_ERA5_Land_timeseries_variable"]
            if (r["original_BIF_SHA256"]!=BIF_SHA
                or r["coordinate_source_status"]!="ORIGINAL_BIF_VERIFIED"
                or r["independent_ERA5L_values_status"]!="NOT_DOWNLOADED"
                or abs(float(r["tower_latitude"])-TOWER[0])>1e-7
                or abs(float(r["tower_longitude"])-TOWER[1])>1e-7
                or abs(float(r["tower_elevation_m"])-TOWER[2])>1e-7):
                raise ValueError("Original Stage05R Yms source BIF/UTC-hour reference changed")
            observed[k]=set(r["source_UTC_halfhour_event_starts"].split(","))
    expected=defaultdict(set)
    for r in source:
        var=VARIABLES[r["variable"]][0]
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        start=utc.replace(minute=0)
        for offset in range(-3,5):
            h=start+timedelta(hours=offset)
            if h.date().isoformat() not in DATES:
                raise ValueError("Original JP-Yms +/-3 to +4 UTC reference window goes outside downloaded two days")
            expected[(h.strftime("%Y%m%d%H%M"),var)].add(r["utc_start"])
    if dict(expected)!=observed:
        raise ValueError("Original Stage05R and source-selected JP-Yms exact variable-hour events differ: "+
                         repr({"expected":len(expected),"actual":len(observed),
                               "missing":list(set(expected)-set(observed))[:8],
                               "extra":list(set(observed)-set(expected))[:8]}))
    return len(expected)

def verify_stage05ab(ab,zip_paths):
    if (ab.get("stage")!="JapanFlux Stage05AB"
        or ab.get("status")!="SIX_ORIGINAL_2011_DAY_PAYLOADS_READONLY_INVENTORIED"
        or ab.get("original_45_source_fields_HOLD") is not True
        or ab.get("previous_16_strong_context_source_fields_verified") is not True
        or ab.get("new_CDS_requests")!=0
        or ab.get("original_source_or_forcing_modified") is not False
        or ab.get("science_repair_approved") is not False):
        raise ValueError("Original Stage05AB six source site-days need latest validated read-only audit")
    entries=ab.get("six_site_day_inventory",[])
    if len(entries)!=6 or len({(r["site"],r["UTC_day"]) for r in entries})!=6:
        raise ValueError("Original Stage05AB scope should be six unique dates")
    for day in DATES:
        matched=[r for r in entries if r["site"]==SITE and r["UTC_day"]==day]
        if len(matched)!=1:raise ValueError("Missing JP-Yms source date "+day)
        r=matched[0]
        if (r["content_status"]!=PASS
            or r["original_BIF_SHA256"]!=BIF_SHA
            or set(r["original_request_variables"])!=set(x[0] for x in VARIABLES.values())
            or r["files"]["ZIP"]["status"]!="REGULAR"
            or r["files"]["PARTIAL"]["status"]!="ABSENT"
            or r["files"]["CSV"]["status"]!="ABSENT"
            or r["files"]["NC"]["status"]!="ABSENT"
            or r["zip_inspection"]["ZIP_SHA256"]!=SHA_BY_DAY[day]
            or r["zip_inspection"]["independent_hourly_values_count"]!=48
            or r["zip_inspection"]["validated_raw_columns"]!=["sp","strd"]
            or not 1<=r["zip_inspection"]["source_csv_members"]<=2
            or sha256(zip_paths[day])!=SHA_BY_DAY[day]):
            raise ValueError("Original JP-Yms CDS source ZIP/CRC/48 raw variable-hour gate failed for "+day)

def extract_unmodified_original_CDS(zip_path,day,expected_sha):
    if zip_path.is_symlink() or not zip_path.is_file():
        raise ValueError("Source ZIP must be real regular file, no symlinks")
    if not 0<zip_path.stat().st_size<25*1024*1024 or sha256(zip_path)!=expected_sha:
        raise ValueError("Real CDS source ZIP SHA/size changed")
    if not zipfile.is_zipfile(zip_path):
        raise ValueError("Original source archive not ZIP")
    data={};grids=set();fields=set()
    with zipfile.ZipFile(zip_path) as z:
        files=[v for v in z.infolist() if not v.is_dir()]
        if not 1<=len(files)<=2 or z.testzip() is not None:
            raise ValueError("CDS ZIP member count/CRC failed")
        for info in files:
            pure=PurePosixPath(info.filename)
            if (pure.is_absolute() or ".." in pure.parts or "\\" in info.filename
                or not info.filename.lower().endswith(".csv") or info.file_size>1000000):
                raise ValueError("Source original CDS CSV member unsafe")
            reader=csv.DictReader(io.StringIO(z.read(info).decode("utf-8-sig")))
            names=reader.fieldnames
            base={"valid_time","latitude","longitude"}
            if not names or len(names)!=len(set(names)):
                raise ValueError("Missing/duplicated original CDS CSV header")
            actual=set(names)-base
            if (not base<=set(names) or not actual or not actual<={"sp","strd"}
                or actual & fields or len(names)!=len(base)+len(actual)):
                raise ValueError("Unexpected CDS CSV variable/schema; duplicate pressure/LW")
            fields.update(actual)
            rrows=list(reader)
            if len(rrows)!=24:raise ValueError("CDS original member must contain 24 UTC hours")
            for row in rrows:
                t=datetime.strptime(row["valid_time"],"%Y-%m-%d %H:%M:%S")
                if t.date().isoformat()!=day or t.minute or t.second:
                    raise ValueError("Wrong source day/non-hourly CDS time")
                lat=float(row["latitude"]);lon=float(row["longitude"])
                if (not math.isfinite(lat) or not math.isfinite(lon)
                    or abs(lat-TOWER[0])>0.11 or abs(lon-TOWER[1])>0.11):
                    raise ValueError("Independent returned grid not near original source tower")
                grids.add((lat,lon))
                for raw in actual:
                    val=float(row[raw])
                    v=val/(1000 if raw=="sp" else 3600)
                    if not math.isfinite(v) or not (0<v<120 if raw=="sp" else 0<=v<1500):
                        raise ValueError("Nonphysical independent source grid measurement")
                    key=(raw,t)
                    if key in data:raise ValueError("Duplicate exact variable/valid UTC hour")
                    data[key]=v
    if fields!={"sp","strd"} or len(data)!=48 or len(grids)!=1:
        raise ValueError("Both authorized variables require 24 hourly values same grid each day")
    return data,next(iter(grids))

def compare(source,values,grid):
    out=[]
    for r in source:
        utc=datetime.strptime(r["utc_start"],"%Y%m%d%H%M")
        var=r["variable"]
        full,raw,unit,divisor=VARIABLES[var]
        floor=utc.replace(minute=0)
        # Model pressure instantaneous at valid time: floor and next two hours.
        # Product strd is DE-ACCUMULATED interval energy and valid_time is
        # an hourly interval END. Includes previous hour for conservative
        # source-30min vs source-independent temporal uncertainty.
        offsets=(-1,0,1,2) if var=="LW_IN" else (0,1,2)
        stamps=[floor+timedelta(hours=i) for i in offsets]
        if any((raw,t) not in values for t in stamps):
            raise ValueError("Missing genuine independent hourly data for source field "+str(r))
        refs=[values[raw,t] for t in stamps]
        lo=min(refs);hi=max(refs)
        original=float(r["selected_F"])
        signed=original-lo if original<lo else original-hi if original>hi else 0.0
        outside=int(original<lo or original>hi)
        out.append({
            "site":SITE,
            "original_JST_halfhour_start":r["native_start"],
            "verified_source_UTC_start":utc.strftime("%Y-%m-%dT%H:%MZ"),
            "variable":var,
            "original_JPF_selected_F":r["selected_F"],
            "same_release_original_ERA":r["ERA_in_same_release"],
            "original_source_QC":"2",
            "original_units":r["unit"],
            "independent_hourly_units":unit,
            "ERA5L_nearest_grid_lat":grid[0],
            "ERA5L_nearest_grid_lon":grid[1],
            "independent_UTC_reference_labels":";".join(t.strftime("%Y-%m-%dT%H:%MZ") for t in stamps),
            "independent_reference_hourly_values":";".join(f"{v:.6f}" for v in refs),
            "independent_reference_min":round(lo,6),
            "independent_reference_max":round(hi,6),
            "original_minus_nearest_hourly_envelope_gap":round(signed,6),
            "outside_independent_hourly_envelope":outside,
            "temporal_comparison_rule":("STRD_HOURLY_END_LABEL_CONSERVATIVE_PREVIOUS_CURRENT_NEXT_TWO_INTERVALS" if var=="LW_IN"
                                       else "PRESSURE_INSTANTANEOUS_FLOOR_NEXT_TWO_HOURS"),
            "independent_hourly_product_processing":(
                "CDS_TIMESERIES_DEACCUMULATED_STRD_J_M2_DIVIDE_3600_NO_SECOND_DIFFERENCING"
                if var=="LW_IN" else "SOURCE_CDS_SP_PA_DIVIDE_1000"),
            "science_review_state":"HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE",
            "model_grid_elevation_status":"ORIGINAL_YMS_TOWER_220M_ERA5L_GRID_ALTITUDE_UNVERIFIED",
            "CDS_source_ZIP_SHA256":";".join(SHA_BY_DAY[day] for day in DATES)
        })
    return out

def selftest():
    assert len(SHA_BY_DAY)==2 and len(VARIABLES)==2
    assert all(len(s)==64 for s in SHA_BY_DAY.values())
    assert Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10})==SRC_COUNTS
    assert set(x[1] for x in VARIABLES.values())=={"sp","strd"}
    # ERA5-Land *time-series* strd is ALREADY de-accumulated hourly energy.
    assert 1080000/3600==300
    assert datetime.strptime("201112170000","%Y%m%d%H%M")-timedelta(hours=1)==datetime(2011,12,16,23)

    # Regression: originally 27 variable fields, including 2005 historically
    # validated Yms fields, but only FIVE December 2011 source rows remain.
    source=[]
    old22=[]
    units={"PA":"kPa","LW_IN":"W m-2","TA":"deg C"}
    def insert(site,iso,var,existing,value):
        utc=datetime.strptime(iso,"%Y%m%d%H%M")
        native=utc+timedelta(hours=9)
        r={"site":site,"native_start":native.strftime("%Y%m%d%H%M"),
           "utc_start":iso,"variable":var,"selected_F":str(value),
           "ERA_in_same_release":str(value),"raw_F_QC":"2",
           "unit":units[var],
           "source_status":"HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"}
        source.append(r)
        if existing:
            old22.append({"site":site,"native_JST_halfhour_start":r["native_start"],
                          "variable":var,"source_QC":"2","context_outside":"1",
                          "original_JPF_F":str(value),
                          "repair_status":"SOURCE_QC2_HOLD_NO_SCIENTIFICALLY_APPROVED_REPLACEMENT"})
    for i in range(6):
        utc=datetime(2005,8,11,12)+timedelta(minutes=i*30)
        insert("JP-Fjy",utc.strftime("%Y%m%d%H%M"),"PA",True,45)
    for i,var in enumerate(["LW_IN"]*2+["PA"]*6+["TA"]*3):
        utc=datetime(2005,8,11,14)+timedelta(minutes=i*30)
        insert("JP-Khw",utc.strftime("%Y%m%d%H%M"),var,True,49)
    for i in range(5):
        utc=datetime(2005,8,11,19)+timedelta(minutes=i*30)
        insert("JP-Yms",utc.strftime("%Y%m%d%H%M"),"PA",True,43)
    for i,var in enumerate(["PA","PA","LW_IN","LW_IN","PA"]):
        utc=datetime(2011,12,16,21)+timedelta(minutes=i*30)
        insert("JP-Yms",utc.strftime("%Y%m%d%H%M"),var,False,0 if var=="PA" else 5)
    picked=select_exact_source_fields(source,old22)
    assert len(picked)==5 and Counter(r["variable"] for r in picked)==Counter({"PA":3,"LW_IN":2})
    samples={}
    for h in range(48):
        utc=datetime(2011,12,16)+timedelta(hours=h)
        samples["sp",utc]=99.0
        samples["strd",utc]=300.0
    out=compare(picked,samples,(34.8,135.8))
    assert len(out)==5 and all(r["outside_independent_hourly_envelope"]==1 for r in out)
    assert all(r["science_review_state"]=="HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE" for r in out)
    assert sum(r["variable"]=="LW_IN" for r in out)==2
    # Off-hour LW interval envelope MUST include previous-end valid time.
    lw=next(r for r in out if r["variable"]=="LW_IN")
    assert len(lw["independent_UTC_reference_labels"].split(";"))==4
    assert lw["independent_hourly_product_processing"].startswith("CDS_TIMESERIES_DEACCUMULATED")
    print("STAGE05AK SELF-TEST PASS | original 27/22+5 mixed Yms PA/LW source scope, CDS 1h DEACCUMULATED strd/3600, cross-midnight UTC and HOLD; NO NETWORK/WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    for arg in ("stage05o-utc","stage05r-hours","stage05ah-evidence",
                "stage05ah-summary","stage05ab-audit","dec16-zip","dec17-zip","out-dir"):
        p.add_argument("--"+arg,type=Path)
    args=p.parse_args()
    if args.self_test:selftest();return
    names=("stage05o_utc","stage05r_hours","stage05ah_evidence",
           "stage05ah_summary","stage05ab_audit","dec16_zip","dec17_zip","out_dir")
    if any(getattr(args,n) is None for n in names):
        p.error("Require original source O/R/AH/AB plus both original Yms December ZIPs and fresh --out-dir")
    science_source_guard(read_json(args.stage05ah_summary))
    source=select_exact_source_fields(read_tsv(args.stage05o_utc),
                                      read_tsv(args.stage05ah_evidence))
    planned_pairs=verify_stage05r_hours(source,read_tsv(args.stage05r_hours))
    files=dict(zip(DATES,(args.dec16_zip,args.dec17_zip)))
    verify_stage05ab(read_json(args.stage05ab_audit),files)
    data={};grids=set()
    for day in DATES:
        values,grid=extract_unmodified_original_CDS(files[day],day,SHA_BY_DAY[day])
        if set(data)&set(values):raise ValueError("Duplicate variable-hour across original CDS days")
        data.update(values);grids.add(grid)
    if len(data)!=96 or len(grids)!=1:
        raise ValueError("Require 48 hourly samples for EACH variable, same nearest-grid 2 days")
    grid,=grids
    reviewed=compare(source,data,grid)
    if len(reviewed)!=5:raise ValueError("Missing one of five original source selected QC2 Yms fields")
    if args.out_dir.exists():p.error("Refuse existing derived report output dir")
    args.out_dir.mkdir(parents=True)
    table=args.out_dir/"stage05ak_5_JP_Yms_2011_QC2_PA_LW_vs_ERA5L_hourly_CONTEXT_HOLD.tsv"
    report=args.out_dir/"stage05ak_2011_Yms_5_original_source_fields_science_context_REVIEW_ONLY.json"
    with table.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,delimiter="\t",fieldnames=COLUMN_NAMES)
        writer.writeheader();writer.writerows(reviewed)
    counts=Counter(r["variable"] for r in reviewed)
    outside=Counter(r["variable"] for r in reviewed if r["outside_independent_hourly_envelope"]==1)
    result={
        "stage":"JapanFlux Stage05AK",
        "status":"FIVE_ORIGINAL_YMS_QC2_FIELDS_TWO_DAY_ERA5L_CONTEXT_ONLY_NOT_REPAIR",
        "source_site":SITE,"source_original_QC2_fields_reviewed":len(reviewed),
        "original_source_fields_by_variable":dict(counts),
        "outside_nearby_independent_hourly_envelope_by_variable":dict(outside),
        "independent_requested_original_variable_hour_pairs":planned_pairs,
        "independent_hours_per_variable":48,
        "source_ERA5L_original_CDS_ZIP_SHA256_by_UTC_day":SHA_BY_DAY,
        "source_nearest_model_grid_lat_lon":list(grid),
        "original_source_tower_BIF_lat_lon_elevation_m":list(TOWER),
        "ERA5L_model_grid_elevation":"UNKNOWN",
        "ERA5L_strd_product_preprocessing":"DEACCUMULATED_1H_ENERGY_J_M2",
        "ERA5L_strd_conversion":"ONE_HOUR_J_M2_DIVIDED_BY_3600_TO_W_M2_NO_SECOND_DIFFERENCING",
        "ERA5L_strd_time_axis":"VALID_TIME_IS_HOURLY_INTERVAL_END_NOT_JPF_HALF_HOUR_POINT",
        "original_22_source_strong_context_evidence_preserved":22,
        "additional_5_fields_strong_evidence_automatically_approved":False,
        "original_source_field_HOLD_total":45,
        "all_45_original_field_candidates_HOLD":True,
        "CDS_requests_this_stage":0,
        "original_source_ZIP_or_forcing_changed":False,
        "Slurm_jobs":0
    }
    with report.open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AK JP-YMS TWO-DAY PA+LW INDEPENDENT HOURLY CONTEXT PASS | NO CDS / SLURM / REPAIR")
    print("ORIGINAL_YMS_SOURCE_FIELDS",len(reviewed),"BY_VARIABLE",dict(counts))
    print("OUTSIDE_HOURLY_ENVELOPE",dict(outside),
          "SOURCE_REFERENCE_PAIRS",planned_pairs)
    print("TWO_DAY_INDEPENDENT_HOURLY_VALUES_PER_VARIABLE",48,
          "GRID",grid,"TOWER_BIF",TOWER)
    for r in reviewed:
        print("SOURCE_FIELD",r["original_JST_halfhour_start"],
              r["variable"],"ORIGINAL_F",r["original_JPF_selected_F"],
              "UNIT",r["original_units"],
              "REFERENCE_UTC",r["independent_UTC_reference_labels"],
              "REFERENCE_VALUES",r["independent_reference_hourly_values"],
              "OUTSIDE",r["outside_independent_hourly_envelope"],
              "SCIENCE",r["science_review_state"])
    print("FIVE_FIELD_CONTEXT_TSV",table)
    print("SCIENCE_CONTEXT_JSON",report)
    print("PRESERVE_22_PRIOR_STRONG_EVIDENCE; ALL_45_ORIGINAL_FIELD_CANDIDATES_HOLD_NO_REPAIR")
if __name__=="__main__":
    main()

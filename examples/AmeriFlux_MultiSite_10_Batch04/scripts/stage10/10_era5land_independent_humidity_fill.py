#!/usr/bin/env python3
"""Batch04 Stage10: ACTUAL external ERA5-Land fallback on 689 unresolved HH records.

--self-test: pure physics/time checks.
--check: report exact candidate years and original BIF point/UTC offset, no writes.
--run: retrieve at most N MISSING site-years from CDS, verify 3 NetCDF
       variable groups + UTC hours, then write two NEW full native-length
       derived FLUXMET HH CSVs, amendment ledger, remaining HOLDs, SHA receipt.
--apply-existing: same full derived outputs using ONLY completed past downloads.

Stage09: 688 US-Rpf, 1 US-SRM source VPD invalid; packaged ERA invalid too.
FLUXNET native clock is local standard time, not DST. Use original BIF
UTC_OFFSET, lat/lon; STOP if ambiguous. ERA5-Land dewpoint/T provides
water-reference RH; transfer that humidity ratio to native tower TA and
derive new native VPD. Hourly external RH interpolated to native half-hours.
All other Stage07-09 and original files kept immutable.
Incomplete research candidate, NEVER production CIME/DATM/spinup approval.
"""
import argparse
import csv
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
from uuid import uuid4
import zipfile

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S08=EXP/"qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z"
S09=EXP/"qcv5_stage09_native_humidity_fallback/candidate_20261024T121412Z_94cc703f"
GRID_ROOT=EXP/"external_evidence/stage10_era5land"
SITES={"US-Rpf":(298080,688),"US-SRM":(385728,1)}
VARIABLES=["2m_temperature","2m_dewpoint_temperature","surface_pressure"]
DATASET="reanalysis-era5-land-timeseries"
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}

def regular(p):
    if p.is_symlink() or not p.is_file():raise ValueError("Missing/symlink source "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for buf in iter(lambda:f.read(1<<20),b""):h.update(buf)
    return h.hexdigest()

def number(v):
    s=str(v if v is not None else "").strip()
    if s.upper() in MISSING:return None
    try:x=float(s)
    except ValueError:return None
    return x if math.isfinite(x) else None

def fmt(x):return "%.12g"%x

def sat_c(t):
    if t is None or not -80<=t<=65:return None
    return 6.112*math.exp(17.67*t/(243.5+t))

def local_to_utc(native,offset):
    return (datetime.strptime(native,"%Y%m%d%H%M")
            -timedelta(hours=offset)).replace(tzinfo=timezone.utc)

def dates(year):
    return [f"{year-1}-12-29",f"{year+1}-01-03"]

def request(lat,lon,year):
    return {"variable":list(VARIABLES),"date":dates(year),
            "location":{"latitude":lat,"longitude":lon},"data_format":"netcdf"}

def read_inputs():
    meta=json.loads(regular(S08/"report.json").read_text())
    r9=json.loads(regular(S09/"stage09_sha_receipt.json").read_text())
    if sha(S08/"report.json")!=r9["source_stage08_report_sha256"]:
        raise ValueError("Stage08 immutable report changed")
    if sha(S08/"unresolved_hold.csv")!=r9["source_stage08_holds_sha256"]:
        raise ValueError("Stage08 immutable HOLD set changed")
    if r9["targeted_original_holds"]!=689 or r9["unresolved_remaining_stage08_holds"]!=696 or r9["new_variable_patches"]!=0:
        raise ValueError("Unexpected Stage09 zero-repair baseline")
    if set(meta.get("sites",{}))!={"US-Rpf","US-Seg","US-Ses","US-Slt","US-SRG","US-SRM","US-Uaf"}:
        raise ValueError("Unexpected Stage08 site census")
    holds={}
    with regular(S08/"unresolved_hold.csv").open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not {"site","TIMESTAMP_START","TIMESTAMP_END","reason"}.issubset(rd.fieldnames):
            raise ValueError("Unexpected Stage08 hold schema")
        for row in rd:
            if row["site"] in SITES:
                site,k=row["site"],row["TIMESTAMP_START"]
                if row["reason"]!="ERA_PAIR_HUMIDITY_INVALID":
                    raise ValueError("Unexpected Stage10 source HOLD reason")
                if (site,k) in holds:raise ValueError("Duplicate Stage08 HOLD")
                holds[site,k]=row
    for site,(n,expected) in SITES.items():
        count=sum(s==site for s,_ in holds)
        if count!=expected or meta["sites"][site]["rows"]!=n:
            raise ValueError("Unexpected exact Stage10 source HOLD count "+site)
        path=Path(meta["sites"][site]["paths"]["native"])
        if sha(path)!=meta["sites"][site]["source_provenance"]["native"]["sha256"]:
            raise ValueError("Original source SHA mismatch "+site)
        r9path=Path(r9["derived_files"][site]["derived_file"])
        if not str(r9path).startswith(str(S09)+"/") or sha(r9path)!=r9["derived_files"][site]["sha256"]:
            raise ValueError("Derived Stage09 source SHA mismatch "+site)
    return meta,r9,holds

def bif(meta,site):
    raw=Path(meta["sites"][site]["paths"]["native"])
    folder=raw.parent
    files=list(folder.glob(f"AMF_{site}_FLUXNET_BIF_*.csv"))
    if len(files)!=1:raise ValueError("Expected exactly one original BIF file "+site)
    records=defaultdict(list)
    with regular(files[0]).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not {"VARIABLE","DATAVALUE","GROUP_ID"}.issubset(rd.fieldnames):
            raise ValueError("Unexpected BIF schema "+site)
        for row in rd:
            if row.get("SITE_ID",site).strip() not in (site,""):
                raise ValueError("Mixed BIF site metadata "+site)
            k=row["VARIABLE"].strip().upper()
            if k in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET","LOCATION_DATE_START","LOCATION_DATE_END"):
                records[k].append((row["GROUP_ID"].strip(),row["DATAVALUE"].strip()))
    out={}
    for field in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET"):
        vals=set(number(v) for _,v in records[field])
        vals.discard(None)
        if len(vals)!=1:
            print("AMBIGUOUS ORIGINAL BIF",site,field,records[field],flush=True)
            raise ValueError("No unambiguous BIF point/offset; refuse CDS and repair")
        out[field]=vals.pop()
    lat,lon,offset=(out[k] for k in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET"))
    if not (-90<=lat<=90 and -180<=lon<=180 and
            -12<=offset<=14 and float(offset).is_integer()):
        raise ValueError("Invalid BIF coordinate or integer standard UTC offset")
    print("BIF SITE",site,"latitude",lat,"longitude",lon,
          "UTC_OFFSET",offset,"native_local_standard_clock",flush=True)
    return {"latitude":lat,"longitude":lon,"offset_hours":int(offset),
            "BIF_file":str(files[0]),"BIF_sha256":sha(files[0])}

def grouped_targets(holds):
    result=defaultdict(list)
    for (site,k),row in holds.items():
        dt=datetime.strptime(k,"%Y%m%d%H%M")
        result[site,dt.year].append(k)
    return dict(result)

def response_path(site,year):
    folder=GRID_ROOT/site/str(year)
    stem=f"ERA5Land_{site}_{year}_T2M_D2M_SP_Stage10"
    return folder,stem

def response_receipt(site,year):
    d,stem=response_path(site,year)
    p=d/(stem+".receipt.json")
    if not p.exists():return None
    rec=json.loads(regular(p).read_text())
    if rec.get("site")!=site or rec.get("year")!=year or rec.get("dataset")!=DATASET:
        raise ValueError("External artifact receipt site/year mismatch")
    filepath=Path(rec["file"])
    if filepath.parent!=d or filepath.name not in (stem+".zip",stem+".nc"):
        raise ValueError("External artifact path not valid")
    if sha(filepath)!=rec["sha256"]:
        raise ValueError("External artifact SHA mismatch")
    return filepath

def classify(p):
    if p.stat().st_size<1024:raise ValueError("CDS response too small")
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as zf:
            members=[x for x in zf.infolist() if not x.is_dir()]
            if not members or len(members)>8 or zf.testzip() is not None:
                raise ValueError("Invalid CDS NetCDF ZIP")
            if any(not x.filename.endswith(".nc") or x.filename.startswith("/")
                   or ".." in Path(x.filename).parts or x.file_size>250_000_000
                   for x in members):
                raise ValueError("Unsafe/non-NC ZIP member")
        return ".zip"
    with p.open("rb") as f:magic=f.read(8)
    if magic.startswith(b"CDF") or magic==b"\x89HDF\r\n\x1a\n":return ".nc"
    raise ValueError("Unrecognized CDS response payload")

def expected_hours(year):
    start=datetime(year-1,12,29,tzinfo=timezone.utc)
    end=datetime(year+1,1,3,23,tzinfo=timezone.utc)
    n=int((end-start).total_seconds()//3600)+1
    return [start+timedelta(hours=i) for i in range(n)]

def grid_read(path,year,point):
    import numpy as np
    from netCDF4 import Dataset,num2date
    wanted=expected_hours(year)
    data={}
    locations=[]
    def read_group(ds,label):
        tim=ds.variables.get("valid_time")
        if tim is None:tim=ds.variables.get("time")
        if tim is None:raise ValueError("NetCDF missing time group "+label)
        vals=num2date(tim[:],getattr(tim,"units",""),
              calendar=getattr(tim,"calendar","standard"),
              only_use_cftime_datetimes=False,
              only_use_python_datetimes=True)
        times=[datetime(x.year,x.month,x.day,x.hour,x.minute,x.second,
                        tzinfo=timezone.utc) for x in vals]
        if times!=wanted:raise ValueError("ERA5-Land missing/reordered UTC hour "+label)
        la=float(np.asarray(ds.variables["latitude"][:]).reshape(-1)[0])
        lo=float(np.asarray(ds.variables["longitude"][:]).reshape(-1)[0])
        if abs(la-point["latitude"])>.151 or abs(lo-point["longitude"])>.151:
            raise ValueError("ERA5-Land wrong grid location "+repr((la,lo)))
        locations.append((la,lo))
        for short,unit in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if short not in ds.variables:continue
            if short in data:raise ValueError("Duplicate NetCDF atmospheric field "+short)
            v=ds.variables[short]
            if getattr(v,"units","")!=unit:raise ValueError("Unexpected unit for "+short)
            arr=np.asarray(np.ma.asarray(v[:]).filled(np.nan),dtype=float).reshape(-1)
            if len(arr)!=len(wanted) or not np.isfinite(arr).all():
                raise ValueError("Missing NetCDF hourly values")
            if short in ("t2m","d2m") and ((arr<160)|(arr>340)).any():
                raise ValueError("Invalid temperature in ERA5-Land")
            if short=="sp" and ((arr<40000)|(arr>110000)).any():
                raise ValueError("Invalid grid surface pressure")
            data[short]=arr
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            if zf.testzip() is not None:raise ValueError("Bad ZIP CRC")
            for item in zf.infolist():
                if item.is_dir():continue
                with Dataset("inmemory.nc","r",memory=zf.read(item)) as ds:
                    read_group(ds,item.filename)
    else:
        with Dataset(str(path),"r") as ds:read_group(ds,path.name)
    if set(data)!={"t2m","d2m","sp"}:
        raise ValueError("Missing required ERA5-Land T/d2m/sp")
    if ((data["d2m"]-data["t2m"])>.1).any():
        raise ValueError("Grid dewpoint exceeds T by >0.1 K")
    if any(abs(x[0]-locations[0][0])>1e-5 or abs(x[1]-locations[0][1])>1e-5
           for x in locations):
        raise ValueError("ERA variables not sampled from same grid point")
    values={"t2m":data["t2m"],"d2m":data["d2m"],"sp":data["sp"]}
    return {"start_utc":wanted[0],"values":values,
            "grid_latitude":locations[0][0],"grid_longitude":locations[0][1],
            "hours":len(wanted)}

def download_one(site,year,point):
    if importlib.util.find_spec("cdsapi") is None:
        raise ValueError("cdsapi not installed; stop before requesting")
    if not (Path.home()/".cdsapirc").is_file() and not os.getenv("CDSAPI_KEY"):
        raise ValueError("Missing CDSAPI credentials; stop before requesting")
    if GRID_ROOT.is_symlink():raise ValueError("Grid root symlink not permitted")
    folder,stem=response_path(site,year)
    if folder.is_symlink():raise ValueError("Output folder symlink not permitted")
    for suffix in (".zip",".nc",".receipt.json",".download.partial"):
        if (folder/(stem+suffix)).exists():
            raise FileExistsError("Ambiguous/reused CDS artifact "+str(folder/(stem+suffix)))
    folder.mkdir(parents=True,exist_ok=True)
    request_data=request(point["latitude"],point["longitude"],year)
    print("CDS REQUEST START",site,year,request_data,flush=True)
    import cdsapi
    partial=folder/(stem+".download.partial")
    cdsapi.Client().retrieve(DATASET,request_data).download(str(partial))
    suffix=classify(partial)
    proof=grid_read(partial,year,point)
    dest=folder/(stem+suffix)
    partial.rename(dest)
    receipt={"site":site,"year":year,"dataset":DATASET,
             "request":request_data,"file":str(dest),"sha256":sha(dest),
             "bytes":dest.stat().st_size,"BIF_sha256":point["BIF_sha256"],
             "grid_latitude":proof["grid_latitude"],
             "grid_longitude":proof["grid_longitude"],
             "hours":proof["hours"],
             "status":"INDEPENDENT_CDS_DOWNLOADED_HOUR_GRID_VALID_NOT_MODEL_APPROVED",
             "created_utc":datetime.now(timezone.utc).isoformat()}
    (folder/(stem+".receipt.json")).write_text(json.dumps(receipt,indent=2)+"\n")
    print("CDS VERIFIED",site,year,receipt["sha256"],flush=True)
    return dest

def rh_hour(grid,utc):
    start=grid["start_utc"]
    diff=(utc-start).total_seconds()/3600
    i=int(math.floor(diff));fraction=diff-i
    data=grid["values"]
    def calc(j):
        t=float(data["t2m"][j])-273.15
        dew=float(data["d2m"][j])-273.15
        sp=float(data["sp"][j])
        if not(-60<=t<=55 and -80<=dew<=55 and 40000<=sp<=110000):
            return None
        a,b=sat_c(t),sat_c(dew)
        if a is None or b is None or dew>t+0.1:return None
        return max(0.,min(100.,100*b/a))
    if i<0 or i+1>=len(data["t2m"]):return None
    rh_a,rh_b=calc(i),calc(i+1)
    if rh_a is None or rh_b is None:return None
    return rh_a+(rh_b-rh_a)*fraction

def site_repairs(site,targets,point,grids,baseline,n):
    decisions={}
    origv={}
    with regular(baseline).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        needed={"TIMESTAMP_START","TIMESTAMP_END","TA_F","VPD_F","PA_F"}
        if not rd.fieldnames or not needed.issubset(rd.fieldnames):
            raise ValueError("Stage09 derived CSV missing humidity/pressure columns")
        count=0
        for row in rd:
            count+=1;k=row["TIMESTAMP_START"]
            if k not in targets:continue
            origv[k]=row
        if count!=n or set(origv)!=targets:
            raise ValueError("Missing exact native targets in Stage09 "+site)
    blocked=Counter()
    for k,row in sorted(origv.items()):
        stamp=datetime.strptime(k,"%Y%m%d%H%M")
        grid=grids.get(stamp.year)
        if grid is None:
            blocked["ERA5LAND_SITE_YEAR_NOT_DOWNLOADED"]+=1
            continue
        utc=local_to_utc(k,point["offset_hours"])
        gridrh=rh_hour(grid,utc)
        t=number(row["TA_F"])
        press=number(row["PA_F"])
        vap=number(row["VPD_F"])
        es=sat_c(t)
        if gridrh is None or not 1<=gridrh<=100:
            blocked["ERA5LAND_HUMIDITY_INVALID_OR_HOUR_NOT_FOUND"]+=1
            continue
        if es is None or t is None or not -55<=t<=52 or press is None or not 65<=press<=110:
            blocked["TOWER_T_OR_PA_UNUSABLE"]+=1
            continue
        newv=es*(1-gridrh/100)
        if newv<0 or newv>es:
            blocked["RECONSTRUCTED_VPD_INVALID"]+=1
            continue
        if vap is not None and 0<=vap<=es:
            blocked["ORIGINAL_TOWER_VPD_NOW_VALID_PRESERVE"]+=1
            continue
        decisions[k]={"VPD_F":newv,"RH":gridrh,
                      "utc":utc.isoformat(),"grid_site_year":stamp.year}
    return decisions,blocked

def write_site(site,baseline,updates,destination,expected):
    count=0;mutated=0;used=set()
    with regular(baseline).open(encoding="utf-8-sig",newline="") as f, \
         destination.open("x",encoding="utf-8",newline="") as out:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not {"TIMESTAMP_START","VPD_F"}.issubset(rd.fieldnames):
            raise ValueError("Incomplete source schema")
        cols=list(rd.fieldnames)
        if "RH" not in cols and updates:cols.append("RH")
        wr=csv.DictWriter(out,fieldnames=cols);wr.writeheader()
        for row in rd:
            count+=1;k=row["TIMESTAMP_START"]
            if k in updates:
                if k in used:raise ValueError("Duplicate native timestamp "+site)
                used.add(k)
                for var in ("VPD_F","RH"):
                    row[var]=fmt(updates[k][var])
                mutated+=1
            wr.writerow(row)
    if count!=expected or used!=set(updates):
        raise ValueError("Incomplete full derived output")
    return {"rows":count,"modified_native_half_hours":mutated,
            "file":str(destination),"sha256":sha(destination)}

def self_test():
    p={"latitude":35.0,"longitude":-120.0,"offset_hours":-8}
    assert local_to_utc("202501010000",p["offset_hours"]).isoformat()=="2025-01-01T08:00:00+00:00"
    assert dates(2020)==["2019-12-29","2021-01-03"]
    assert len(expected_hours(2020))==372*24
    # Same-water saturation ratio e_s(5 C)/e_s(10 C) is ~71.1%, not >80%.
    ratio = 100 * sat_c(5) / sat_c(10)
    assert 70 < ratio < 73, "water saturation-pressure regression: {}".format(ratio)
    assert abs(sat_c(0)-6.112) < 1e-9
    assert sat_c(5) < sat_c(10)
    assert len(expected_hours(2021)) == 371 * 24
    assert rh_hour({"start_utc":datetime(2025,1,1,tzinfo=timezone.utc),
                    "values":{"t2m":[283.15,283.15],"d2m":[278.15,278.15],
                              "sp":[100000,100000]}},
                   datetime(2025,1,1,0,30,tzinfo=timezone.utc)) is not None
    print("STAGE10 SELF-TEST PASS: FLUXNET standard clock, leap-year windows, T/D2M humidity interpolation")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    mode.add_argument("--apply-existing",action="store_true")
    p.add_argument("--max-downloads",type=int,default=3)
    a=p.parse_args()
    self_test()
    if a.self_test:return
    if not 1<=a.max_downloads<=5:raise ValueError("max-downloads must be 1..5")
    meta,r9,holds=read_inputs()
    byyear=grouped_targets(holds)
    coords={s:bif(meta,s) for s in SITES}
    years=sorted(byyear,key=lambda k:(-len(byyear[k]),k[0],k[1]))
    print("STAGE10 TARGET CENSUS",len(holds),"site_years",len(years))
    for (site,year) in years:
        status="PRESENT" if response_receipt(site,year) else "NEEDS_INDEPENDENT_ERA5LAND"
        print("TARGET",site,year,"n",len(byyear[site,year]),status)
    if a.check:
        print("CHECK ONLY: zero CDS requests, zero writes")
        return
    if a.run:
        done=0
        for site,year in years:
            if response_receipt(site,year):continue
            if done>=a.max_downloads:break
            download_one(site,year,coords[site])
            done+=1
        print("STAGE10 NEW CDS SITE-YEARS DOWNLOADED",done)
    cache={}
    grid_shas={}
    for site,year in years:
        f=response_receipt(site,year)
        if f:
            cache[site,year]=grid_read(f,year,coords[site])
            grid_shas[f"{site}-{year}"]=sha(f)
    results={}
    blocked={}
    for site,(expected,total) in SITES.items():
        relevant={k for s,k in holds if s==site}
        origin=Path(r9["derived_files"][site]["derived_file"])
        entries={year:grid for (s,year),grid in cache.items() if s==site}
        results[site],blocked[site]=site_repairs(site,relevant,coords[site],entries,origin,expected)
        print("STAGE10 REPAIR RESULT",site,"changed",len(results[site]),
              "still_unrepaired",total-len(results[site]),
              "reasons",dict(blocked[site]),flush=True)
    out=EXP/"qcv5_stage10_independent_era5land"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage10 independent ERA5-Land humidity research trial; incomplete years/other Batch04 holds not resolved.\n")
    fixes=[]
    remaining=[]
    outcomes={}
    for site,(n,total) in SITES.items():
        baseline=Path(r9["derived_files"][site]["derived_file"])
        name=site+"_Stage10_ERA5Land_humidity_derived_FLUXMET_HH.csv"
        outcomes[site]=write_site(site,baseline,results[site],out/name,n)
        for k,item in sorted(results[site].items()):
            fixes.append({"site":site,"TIMESTAMP_START":k,
                          "new_VPD_hPa":fmt(item["VPD_F"]),
                          "new_RH_pct":fmt(item["RH"]),
                          "matched_UTC":item["utc"],
                          "grid_source_year":item["grid_site_year"]})
        still=sorted(k for s,k in holds if s==site and k not in results[site])
        for k in still:
            reason="ERA5LAND_NOT_READY_OR_FAILED_PHYSICAL_SCREEN"
            remaining.append({"site":site,"TIMESTAMP_START":k,"reason":reason})
    def table(path,cols,rows):
        with path.open("x",encoding="utf-8",newline="") as f:
            wr=csv.DictWriter(f,fieldnames=cols);wr.writeheader();wr.writerows(rows)
    table(out/"stage10_applied_ERA5Land_humidity.csv",
          ("site","TIMESTAMP_START","new_VPD_hPa","new_RH_pct","matched_UTC","grid_source_year"),fixes)
    table(out/"stage10_remaining_689_holds.csv",
          ("site","TIMESTAMP_START","reason"),remaining)
    proof={
        "input_stage08_SHA256":sha(S08/"report.json"),
        "input_stage09_SHA256":sha(S09/"stage09_sha_receipt.json"),
        "original_BIF":coords,"grid_source_SHA256":grid_shas,
        "known_targets":len(holds),"candidate_fixes":len(fixes),
        "unfixed":len(remaining),"site_files":outcomes,
        "remaining_reasons_by_site":{s:dict(v) for s,v in blocked.items()},
        "model_ready":False,"DATM_ready":False,"spinup":False,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "output_SHA256":{
            x.name:sha(x) for x in (
               out/"stage10_applied_ERA5Land_humidity.csv",
               out/"stage10_remaining_689_holds.csv")}}
    (out/"stage10_receipt.json").write_text(json.dumps(proof,indent=2)+"\n")
    print("STAGE10 NEW FULL DERIVED DATA",out)
    print("STAGE10 RESULT:",len(fixes),"repaired,",len(remaining),"remaining of",len(holds))
    print("NO ORIGINAL SOURCE, STAGE07/08/09, DATM OR MODEL WRITES")

if __name__=="__main__":
    main()

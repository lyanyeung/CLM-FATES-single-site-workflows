#!/usr/bin/env python3
"""OzFlux AU-ASM 2013-2018: audit-only preflight or guarded PROVISIONAL DATM.

Default mode (--preflight): reads original source and Stage11 report, writes
only a small JSON evidence report. Production mode (--write-candidate) requires
human-reviewed ZBOT, source time interval, and precipitation evidence plus an
exact explicit confirmation. Writes 6 NEW standalone provisional DATM NetCDF
files to a unique output directory, never deletes or overwrites any file.
Neither mode approves final science, changes original data or submits Slurm.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys

import netCDF4
import numpy as np

SOURCE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/AU-ASM/forcing/raw/AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc")
YEARS=tuple(range(2013,2019))
SITE="AU-ASM"
LAT=-22.2828
LON=133.2493
N=17520
SHIFT_MIN=585.0    # PROVISIONAL: Darwin 570 min, END->CENTER 15 min
CONFIRM="BUILD_AU_ASM_PROVISIONAL_2013_2018"
MET=("Ta","SH","ps","Fsd","Fld","Ws","Precip")
EXPECTED_UNITS={"Ta":"degC","SH":"kg/kg","ps":"kPa","Fsd":"W/m^2",
                "Fld":"W/m^2","Ws":"m/s","Precip":"mm"}
MINMAX={"Ta":(-55,65),"SH":(0,0.055),"ps":(45,115),"Fsd":(-50,1600),
        "Fld":(0,850),"Ws":(-0.1,65),"Precip":(0,None)}
FIELDS={
    "TBOT":("Ta","K","air temperature"),
    "QBOT":("SH","kg/kg","specific humidity"),
    "PSRF":("ps","Pa","surface atmospheric pressure"),
    "FSDS":("Fsd","W/m2","downward shortwave radiation"),
    "FLDS":("Fld","W/m2","downward longwave radiation"),
    "WIND":("Ws","m/s","wind speed"),
    "PRECTmms":("Precip","mm/s","precipitation rate"),
}


def attr(v,key):
    if key not in v.ncattrs(): return None
    val=v.getncattr(key)
    if hasattr(val,"tolist"):val=val.tolist()
    return str(val)[:1400]


def read_field(ds,key,dim,number):
    v=ds.variables[key]
    if not np.issubdtype(v.dtype,np.number) or v.dimensions.count(dim)!=1:
        raise ValueError("Unsupported shape/dtype for "+key)
    if v.shape[v.dimensions.index(dim)]!=number or any(
        d!=dim and v.shape[i]!=1 for i,d in enumerate(v.dimensions)):
        raise ValueError("Unexpected non-time dimensions for "+key)
    x=np.ma.asarray(v[:],dtype=np.float64).filled(np.nan).reshape(-1)
    if len(x)!=number:raise ValueError("Length mismatch "+key)
    return x


def good(x):
    return np.isfinite(x)&(x>-9990)


def qsat(t,p):
    es=0.6112*np.exp(np.clip(17.67*t/(t+243.5),-50,30))
    return 0.622*es/(p-0.378*es)


def time_seconds(v):
    prefix=str(v.units).lower().split(" since ",1)[0].strip()
    units={"days":86400,"day":86400,"hours":3600,"hour":3600,
           "minutes":60,"minute":60,"seconds":1,"second":1}
    if prefix not in units:raise ValueError("Unexpected source time units")
    return float(units[prefix])


def year_bounds(t,year):
    c=getattr(t,"calendar","standard")
    a=netCDF4.date2num(dt.datetime(year,1,1),t.units,calendar=c)
    b=netCDF4.date2num(dt.datetime(year+1,1,1),t.units,calendar=c)
    return float(a),float(b)


def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def validate_original(ds):
    if "time" not in ds.variables:
        raise ValueError("No time variable")
    t=ds.variables["time"]
    if t.ndim!=1:raise ValueError("Time is not one-dimensional")
    source=np.ma.asarray(t[:],dtype=np.float64).filled(np.nan)
    if not np.isfinite(source).all() or np.any(np.diff(source)<=0):
        raise ValueError("Original source timestamps invalid")
    dim=t.dimensions[0]
    data={k:read_field(ds,k,dim,len(source)) for k in MET}
    for k in MET:
        unit=attr(ds.variables[k],"units")
        if unit!=EXPECTED_UNITS[k]:
            raise ValueError("Unit differs from audited source "+k+": "+str(unit))
    metadata={
        "global":{name:str(ds.getncattr(name))[:600] for name in ds.ncattrs()
                  if any(word in name.lower() for word in (
                      "time","site","lat","lon","height","tower","soil",
                      "vegetation","history","processing"))},
        "variables":{k:{name:attr(ds.variables[k],name) for name in (
              "units","height","instrument","long_name","statistic_type",
              "source","description_L3","description_L4","description_L6")}
              for k in MET},
        "time":{name:attr(t,name) for name in t.ncattrs()},
    }
    for d,k in ((LAT,"latitude"),(LON,"longitude")):
        val=metadata["global"].get(k)
        if val is not None:
            try:
                if abs(float(val)-d)>0.05:
                    raise ValueError(k+" inconsistent with OzFlux site coordinates")
            except ValueError:
                if re.search(r"[A-Za-z]",val):
                    raise ValueError(k+" unparseable in source global metadata")
                raise
    view=source-SHIFT_MIN*60/time_seconds(t)
    selected={}
    summaries=[]
    step=1800/time_seconds(t)
    for year in YEARS:
        low,high=year_bounds(t,year)
        a=int(np.searchsorted(view,low,"left"))
        b=int(np.searchsorted(view,high,"left"))
        ix=np.arange(a,b,dtype=int)
        if len(ix)!=(17568 if year==2016 else 17520):
            raise ValueError("Wrong provisional UTC year source count "+str(year))
        if not np.all(np.abs(np.diff(view[a:b])-step)*time_seconds(t)<1):
            raise ValueError("Source timestep discontinuity in UTC preview "+str(year))
        if abs((view[a]-low-step/2)*time_seconds(t))>1 or abs(
                (view[b-1]-high+step/2)*time_seconds(t))>1:
            raise ValueError("UTC preview boundary does not match interval centers "+str(year))
        datetimes=netCDF4.num2date(view[ix],t.units,
                            calendar=getattr(t,"calendar","standard"))
        retain=np.array([not (x.month==2 and x.day==29) for x in datetimes],dtype=bool)
        ix=ix[retain]
        if len(ix)!=N:raise ValueError("NOLEAP record count failure "+str(year))
        for k in MET:
            x=data[k][ix]
            if not good(x).all():
                raise ValueError("Missing met record "+str(year)+"/"+k)
            lo,hi=MINMAX[k]
            if np.any(x<lo) or (hi is not None and np.any(x>hi)):
                raise ValueError("Broad physics failure "+str(year)+"/"+k)
        sat=qsat(data["Ta"][ix],data["ps"][ix])
        if np.any(data["SH"][ix]>1.05*sat):
            raise ValueError("SH >105% qsat in AU-ASM "+str(year))
        selected[year]=ix
        summaries.append({"year":year,"original_full_UTC_records":b-a,
                          "UTC_noLeap_halfhours":len(ix),
                          "source_Feb29_removed":b-a-len(ix),
                          "provisional_first_time":str(netCDF4.num2date(
                              float(view[ix[0]]),t.units,
                              calendar=getattr(t,"calendar","standard"))),
                          "provisional_last_time":str(netCDF4.num2date(
                              float(view[ix[-1]]),t.units,
                              calendar=getattr(t,"calendar","standard"))),
                          "provisional_only":True})
    return data,selected,metadata,summaries


def validate_stage11(path):
    with (path/"stage11_science_evidence.json").open(encoding="utf-8") as f:
        obj=json.load(f)
    if (obj.get("science_approval") is not False or obj.get("candidate_DATM_generated") is not False
            or obj.get("source_read_only") is not True):
        raise ValueError("Stage11 provenance not a completed unapproved source audit")
    with (path/"stage11_ASM_UTC_NOLEAP_preview.tsv").open(encoding="utf-8") as f:
        import csv
        rows=list(csv.DictReader(f,delimiter="\t"))
    if len(rows)!=6 or {int(r["year"]) for r in rows}!=set(YEARS):
        raise ValueError("Stage11 ASM 6-year output incomplete")
    for row in rows:
        if (int(row["candidate_NOLEAP_records"])!=N or
                row["candidate_UTC_centers_consistent"]!="True" or
                row["no_missing_met_values"]!="True" or
                int(row["RHratio_gt1p05"])!=0):
            raise ValueError("Stage11 ASM science preflight blocked "+row["year"])
    return rows


def ensure_reviewed(args,metadata):
    if not args.write_candidate:return
    if args.confirm!=CONFIRM:
        raise ValueError("Candidate write requires exact --confirm "+CONFIRM)
    if args.zbot_m is None or not 2<=args.zbot_m<=50:
        raise ValueError("Candidate write requires reviewed, physically plausible --zbot-m")
    for key in ("zbot_evidence","precip_evidence","time_evidence"):
        value=getattr(args,key)
        if not value or len(value.strip())<18:
            raise ValueError("Candidate write requires substantive --"+key.replace("_","-"))
    precipitation_type=(metadata["variables"]["Precip"].get("statistic_type") or "")
    if not precipitation_type:
        raise ValueError("Cannot confirm Precip is interval accumulation from source statistic_type; manual metadata audit required before writing")
    if not any(word in precipitation_type.lower() for word in ("sum","accum","total")):
        raise ValueError("Source Precip statistic_type does not confirm time-interval amount")
    source_timezone=metadata["global"].get("time_zone") or metadata["global"].get("timezone")
    if source_timezone not in ("Australia/Darwin","Australia/Darwin (UTC+09:30)"):
        raise ValueError("Source timezone missing/unexpected; manual time-source validation first")


def write_datm(out,data,selected,args,source_hash):
    paths=[]
    for year,ix in selected.items():
        destination=out/f"AU-ASM_PROVISIONAL_DATM_{year}.nc"
        if destination.exists():raise FileExistsError(destination)
        with netCDF4.Dataset(str(destination),"w",format="NETCDF4_CLASSIC") as nc:
            nc.createDimension("time",N)
            nc.createDimension("lat",1)
            nc.createDimension("lon",1)
            t=nc.createVariable("time","f8",("time",))
            t.units=f"days since {year}-01-01 00:00:00"
            t.calendar="noleap"
            t[:]=(np.arange(N,dtype=float)+0.5)/48
            lat=nc.createVariable("lat","f8",("lat",));lat.units="degrees_north";lat[:]=LAT
            lon=nc.createVariable("lon","f8",("lon",));lon.units="degrees_east";lon[:]=LON
            latixy=nc.createVariable("LATIXY","f8",("lat","lon"));latixy[:,:]=LAT
            longxy=nc.createVariable("LONGXY","f8",("lat","lon"));longxy[:,:]=LON
            zbot=nc.createVariable("ZBOT","f8",("time","lat","lon"))
            zbot.units="m";zbot.long_name="reviewed atmospheric forcing reference height"
            zbot[:,0,0]=args.zbot_m
            for target,(src,unit,longname) in FIELDS.items():
                vals=data[src][ix]
                if target=="TBOT": vals=vals+273.15
                elif target=="PSRF":vals=vals*1000
                elif target=="PRECTmms":vals=vals/1800.
                v=nc.createVariable(target,"f4",("time","lat","lon"),
                                  fill_value=np.float32(1e36))
                v.units=unit;v.long_name=longname
                v[:,0,0]=vals.astype(np.float32)
            nc.title="UNAPPROVED AU-ASM standalone provisional DATM candidate"
            nc.site=SITE
            nc.science_approval="FALSE"
            nc.model_submission_authorised="FALSE"
            nc.source_sha256=source_hash
            nc.native_label_interpretation="PROVISIONAL local Australia/Darwin END -> UTC interval center"
            nc.source_timestamp_shift_minutes=SHIFT_MIN
            nc.time_evidence=args.time_evidence
            nc.zbot_evidence=args.zbot_evidence
            nc.precipitation_evidence=args.precip_evidence
            nc.calendar="noleap"
            nc.forcing_year=year
        paths.append(str(destination))
        print("PROVISIONAL_DATM_WRITTEN",destination)
    return paths


def self_test():
    assert SHIFT_MIN==585 and N==17520
    assert np.allclose(qsat(np.array([25.]),np.array([100.])),0.020,atol=0.002)
    assert good(np.array([np.nan,-9999.,0.])).tolist()==[False,False,True]
    assert set(FIELDS)=={"TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms"}
    print("STAGE12 SELF-TEST PASS: mapping, source fill guard and provisional clock; NO WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        self_test();return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--stage11",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight",action="store_true")
    mode.add_argument("--write-candidate",action="store_true")
    p.add_argument("--confirm")
    p.add_argument("--zbot-m",type=float)
    p.add_argument("--zbot-evidence")
    p.add_argument("--precip-evidence")
    p.add_argument("--time-evidence")
    args=p.parse_args()
    source=args.source.resolve()
    out=args.out.resolve()
    source_tree=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE").resolve()
    if (args.out.is_symlink() or source==out or source_tree==out
            or source_tree in out.parents or out.exists()):
        raise ValueError("Must use a new output directory outside all original source trees")
    if args.source.is_symlink() or not source.is_file():
        raise ValueError("Original source not found or symlinked")
    validate_stage11(args.stage11)
    with netCDF4.Dataset(str(source),mode="r") as ds:
        data,selected,metadata,summaries=validate_original(ds)
    ensure_reviewed(args,metadata)
    src_hash=sha256(source)
    out.mkdir(parents=True,exist_ok=False)
    paths=write_datm(out,data,selected,args,src_hash) if args.write_candidate else []
    report={
      "stage":"OzFlux Stage12 first ASM candidate DATM guard",
      "operation":"PROVISIONAL_NETCDF_WRITTEN" if paths else "SOURCE_PREFLIGHT_ONLY",
      "source_path":str(source),"source_sha256":src_hash,
      "original_source_modified":False,"science_approval":False,
      "model_submission_authorised":False,
      "source_time_conversion_hypothesis_NOT_finally_approved":True,
      "year_summaries":summaries,"native_source_metadata":metadata,
      "provisional_DATM_files":paths,
      "measurement_height_selected_m":args.zbot_m if paths else None,
      "PFT_soil_surface_assessment_pending":True,
      "precip_rate_convention_reviewed_for_trial_only":bool(paths),
    }
    (out/"stage12_ASM_candidate_manifest.json").write_text(
       json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    for item in summaries:
        print("ASM_UTC_NOLEAP",item["year"],item["UTC_noLeap_halfhours"],
              "FEB29_REMOVED",item["source_Feb29_removed"])
    print("STAGE12",report["operation"],"FILES",len(paths))
    print("OUTPUT_DIR",out)
    print("SCIENCE_APPROVAL FALSE; NO MODEL RUN")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

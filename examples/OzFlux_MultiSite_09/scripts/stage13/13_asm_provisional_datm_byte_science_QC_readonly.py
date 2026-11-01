#!/usr/bin/env python3
"""Stage13: AU-ASM Mulga1 provisional DATM source-to-output independent audit.

READ-ONLY on original L6 NetCDF and all six provisional DATM NetCDFs.
The only writes are new JSON/TSV report files in a fresh HOME directory.
Never clips/replaces FSDS; does not build source/PFT/surface/cases or Slurm.
All solar classifications use UNAPPROVED local-end -> UTC-centre hypothesis.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys

import netCDF4
import numpy as np

SOURCE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/AU-ASM/forcing/raw/AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc")
EXPECTED_SHA="b9381c4ed0744d03ae609cfbf3805e30bbb9223851a05f4e5b63b149dd0b10eb"
CANDIDATES=Path("/iridisfs/home/ly3n24/ozflux_ASM_PROVISIONAL_DATM_20261101T182517Z")
SOURCE_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
YEARS=range(2013,2019)
N=17520
LAT=-22.2828
LON=133.2493
ZBOT=11.6
SHIFT_SECONDS=585*60
VARS={
    "TBOT":("Ta","K"),
    "QBOT":("SH","kg/kg"),
    "PSRF":("ps","Pa"),
    "FSDS":("Fsd","W/m2"),
    "FLDS":("Fld","W/m2"),
    "WIND":("Ws","m/s"),
    "PRECTmms":("Precip","mm/s"),
}
YEAR_FIELDS=[
    "year","source_UTC_view_records","source_Feb29_removed","verified_NOLEAP_records",
    "exact_f32_source_mapping_all_7","time_axis_match","coordinates_match",
    "candidate_SHA256","FSDS_negative_rows","FSDS_negative_min_Wm2",
    "FSDS_negative_QC0_count","FSDS_negative_QC10_count",
    "FSDS_negative_QC50_count","FSDS_negative_QC410_count",
    "FSDS_negative_QC420_count","FSDS_negative_QC440_count",
    "FSDS_negative_QC_other_count","FSDS_negative_solar_below_minus6deg",
    "FSDS_negative_solar_minus6_to0deg","FSDS_negative_solar_above0deg",
    "wind_gt15_ms","wind_max_ms","precip_source_sum_mm",
    "precip_candidate_sum_mm","science_approval",
]
NEG_FIELDS=[
    "year","source_index","original_local_label","hypothetical_UTC_center",
    "candidate_index","source_Fsd_Wm2","candidate_FSDS_Wm2",
    "source_Fsd_QCFlag","source_Ta_degC","source_SH_kgkg","source_Ws_ms",
    "source_PreCIP_mm","source_PreCIP_QCFlag",
    "solar_elevation_deg_under_hypothesis","solar_regime_hypothesis",
    "is_candidate_repair_approved",
]
HIGHWIND_FIELDS=[
    "year","candidate_index","source_index","local_label","hypothetical_UTC_center",
    "wind_ms","source_Ws_QCFlag","source_Ta_degC","source_Fsd_Wm2",
]


def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as fd:
        for part in iter(lambda:fd.read(8*1024*1024),b""):
            h.update(part)
    return h.hexdigest()


def duration(v):
    k=str(v.units).split(" since ",1)[0].lower().strip()
    vals={"days":86400,"day":86400,"hours":3600,"hour":3600,
          "minutes":60,"minute":60,"seconds":1,"second":1}
    if k not in vals:raise ValueError("Unexpected time unit "+str(v.units))
    return vals[k]


def source_series(ds,name,dim,n):
    if name not in ds.variables:raise ValueError("Missing source field: "+name)
    v=ds.variables[name]
    if not np.issubdtype(v.dtype,np.number) or v.dimensions.count(dim)!=1:
        raise ValueError("Source field shape/type invalid "+name)
    if v.shape[v.dimensions.index(dim)]!=n or any(
        d!=dim and v.shape[i]!=1 for i,d in enumerate(v.dimensions)):
        raise ValueError("Source non-time dimensions invalid "+name)
    a=np.ma.asarray(v[:],dtype=np.float64).filled(np.nan).reshape(-1)
    if len(a)!=n:raise ValueError("Source field count invalid "+name)
    return a


def source_year_indexes(t,numeric_time,year):
    scale=duration(t)
    view=numeric_time-SHIFT_SECONDS/scale
    cal=getattr(t,"calendar","standard")
    lo=float(netCDF4.date2num(dt.datetime(year,1,1),t.units,calendar=cal))
    hi=float(netCDF4.date2num(dt.datetime(year+1,1,1),t.units,calendar=cal))
    first=int(np.searchsorted(view,lo,"left"))
    end=int(np.searchsorted(view,hi,"left"))
    raw=np.arange(first,end,dtype=int)
    expected_raw=17568 if year==2016 else N
    if len(raw)!=expected_raw:raise ValueError(f"{year}: original year does not contain {expected_raw} UTC view records")
    step=1800/scale
    if not np.all(np.abs(np.diff(view[raw])-step)*scale<1):
        raise ValueError(f"{year}: source UTC hypothesis has inconsistent cadence")
    if abs(view[first]-(lo+step/2))*scale>1 or abs(view[end-1]-(hi-step/2))*scale>1:
        raise ValueError(f"{year}: first/last source UTC-center stamps mismatch")
    dates=netCDF4.num2date(view[raw],t.units,calendar=cal)
    retained=np.array([not (x.month==2 and x.day==29) for x in dates],dtype=bool)
    srcix=raw[retained]
    if len(srcix)!=N or len(raw)-len(srcix)!=(48 if year==2016 else 0):
        raise ValueError(f"{year}: NOLEAP selection inconsistent")
    return raw,srcix,view


def jd_solar_cos(ts,lat=LAT,lon=LON):
    # NOAA short-form solar geometry, only a diagnostic at hypothesised UTC times.
    doy=ts.timetuple().tm_yday
    nday=366 if (ts.year%4==0 and (ts.year%100!=0 or ts.year%400==0)) else 365
    h=ts.hour+ts.minute/60.+ts.second/3600.
    gamma=2*math.pi/nday*(doy-1+(h-12)/24.)
    eq=229.18*(0.000075+0.001868*math.cos(gamma)-0.032077*math.sin(gamma)
               -0.014615*math.cos(2*gamma)-0.040849*math.sin(2*gamma))
    decl=(0.006918-0.399912*math.cos(gamma)+0.070257*math.sin(gamma)
          -0.006758*math.cos(2*gamma)+0.000907*math.sin(2*gamma)
          -0.002697*math.cos(3*gamma)+0.00148*math.sin(3*gamma))
    ha=math.radians(((h*60+eq+4*lon)%1440)/4.-180.)
    phi=math.radians(lat)
    return math.sin(phi)*math.sin(decl)+math.cos(phi)*math.cos(decl)*math.cos(ha)


def time_label(t,value):
    return str(netCDF4.num2date(float(value),t.units,calendar=getattr(t,"calendar","standard")))


def get_float(v):
    a=np.ma.asarray(v[:],dtype=np.float32).filled(np.nan)
    return np.asarray(a,dtype=np.float32)


def audit_one(original,time,source_values,source_data,idx,view,year,root,sha):
    candidate=root/f"AU-ASM_PROVISIONAL_DATM_{year}.nc"
    if candidate.is_symlink() or not candidate.is_file():
        raise FileNotFoundError(f"Missing or symlinked candidate file {candidate}")
    with netCDF4.Dataset(str(candidate),mode="r") as nc:
        if getattr(nc,"science_approval",None)!="FALSE" or getattr(nc,"model_submission_authorised",None)!="FALSE":
            raise ValueError(f"{year}: candidate flags must remain explicitly unapproved")
        if getattr(nc,"source_sha256",None)!=sha:
            raise ValueError(f"{year}: source lineage SHA mismatch")
        if len(nc.dimensions["time"])!=N:
            raise ValueError(f"{year}: candidate length mismatch")
        tc=nc.variables["time"]
        if tc.calendar!="noleap" or tc.units!=f"days since {year}-01-01 00:00:00":
            raise ValueError(f"{year}: candidate calendar/time units incorrect")
        expected=(np.arange(N,dtype=np.float64)+0.5)/48.
        tvals=np.ma.asarray(tc[:]).filled(np.nan)
        time_ok=bool(np.allclose(tvals,expected,atol=1e-12,rtol=0))
        if not time_ok:raise ValueError(f"{year}: candidate timestamp mismatch")
        lat=float(nc.variables["lat"][:][0])
        lon=float(nc.variables["lon"][:][0])
        lat2=float(nc.variables["LATIXY"][:][0,0])
        lon2=float(nc.variables["LONGXY"][:][0,0])
        coordinates_ok=all(abs(a-b)<1e-8 for a,b in ((lat,LAT),(lon,LON),(lat2,LAT),(lon2,LON)))
        if not coordinates_ok:raise ValueError(f"{year}: coordinate mismatch")
        z=np.ma.asarray(nc.variables["ZBOT"][:]).filled(np.nan)
        if z.shape!=(N,1,1) or not np.allclose(z,ZBOT,atol=1e-12,rtol=0):
            raise ValueError(f"{year}: provisional ZBOT inconsistent")
        mapped={}
        for target,(native,unit) in VARS.items():
            v=nc.variables[target]
            if getattr(v,"units","")!=unit:
                raise ValueError(f"{year}/{target}: units differ from candidate writer")
            actual=get_float(v).reshape(-1)
            if actual.size!=N or not np.isfinite(actual).all():
                raise ValueError(f"{year}/{target}: wrong shape or nonfinite values")
            x=source_data[native][idx]
            if target=="TBOT":x=x+273.15
            elif target=="PSRF":x=x*1000.
            elif target=="PRECTmms":x=x/1800.
            expected_x=np.asarray(x,dtype=np.float32)
            if not np.array_equal(actual,expected_x):
                bad=np.flatnonzero(actual!=expected_x)
                raise ValueError(f"{year}/{target}: not exact f32 source mapping, {len(bad)} rows; first {bad[:5].tolist()}")
            mapped[target]=actual
        sourceFsd=source_data["Fsd"][idx]
        negpos=np.flatnonzero(mapped["FSDS"]<0)
        qfsd=source_data["Fsd_QCFlag"][idx]
        flags={"qc0":0,"qc10":0,"qc50":0,"qc410":0,
               "qc420":0,"qc440":0,"other":0}
        solar={"below_minus6":0,"minus6_to0":0,"above0":0}
        negrows=[]
        for j in negpos:
            source_i=int(idx[j])
            utcobj=netCDF4.num2date(float(view[source_i]),time.units,
                                  calendar=getattr(time,"calendar","standard"))
            utcdt=dt.datetime(int(utcobj.year),int(utcobj.month),int(utcobj.day),
                              int(utcobj.hour),int(utcobj.minute),int(utcobj.second))
            cosine=np.clip(jd_solar_cos(utcdt),-1,1)
            elev=math.degrees(math.asin(cosine))
            regime=("below_minus6" if elev<=-6 else
                    "minus6_to0" if elev<=0 else "above0")
            solar[regime]+=1
            q=qfsd[j]
            code=("qc"+str(int(q))) if np.isfinite(q) and q in (0,10,50,410,420,440) else "other"
            flags[code]+=1
            negrows.append({
                "year":year,"source_index":source_i,
                "original_local_label":time_label(time,source_values[source_i]),
                "hypothetical_UTC_center":time_label(time,view[source_i]),
                "candidate_index":int(j),
                "source_Fsd_Wm2":float(sourceFsd[j]),
                "candidate_FSDS_Wm2":float(mapped["FSDS"][j]),
                "source_Fsd_QCFlag":float(q) if np.isfinite(q) else None,
                "source_Ta_degC":float(source_data["Ta"][source_i]),
                "source_SH_kgkg":float(source_data["SH"][source_i]),
                "source_Ws_ms":float(source_data["Ws"][source_i]),
                "source_PreCIP_mm":float(source_data["Precip"][source_i]),
                "source_PreCIP_QCFlag":float(source_data["Precip_QCFlag"][source_i]),
                "solar_elevation_deg_under_hypothesis":float(elev),
                "solar_regime_hypothesis":regime,
                "is_candidate_repair_approved":False,
            })
        windpos=np.flatnonzero(mapped["WIND"]>15)
        windrows=[]
        for j in windpos:
            i=int(idx[j])
            windrows.append({
                "year":year,"candidate_index":int(j),"source_index":i,
                "local_label":time_label(time,source_values[i]),
                "hypothetical_UTC_center":time_label(time,view[i]),
                "wind_ms":float(source_data["Ws"][i]),
                "source_Ws_QCFlag":float(source_data["Ws_QCFlag"][i]),
                "source_Ta_degC":float(source_data["Ta"][i]),
                "source_Fsd_Wm2":float(source_data["Fsd"][i]),
            })
        annual_mm=float(np.sum(source_data["Precip"][idx],dtype=np.float64))
        output_rain_mm=float(np.sum(mapped["PRECTmms"].astype(np.float64)*1800))
        if abs(annual_mm-output_rain_mm)>0.01:
            raise ValueError(f"{year}: annual precip not conserved under f32 conversion")
        row={
            "year":year,"source_UTC_view_records":17568 if year==2016 else N,
            "source_Feb29_removed":48 if year==2016 else 0,
            "verified_NOLEAP_records":N,
            "exact_f32_source_mapping_all_7":True,"time_axis_match":True,
            "coordinates_match":True,
            "candidate_SHA256":sha256(candidate),
            "FSDS_negative_rows":len(negrows),
            "FSDS_negative_min_Wm2":float(np.min(mapped["FSDS"][negpos])) if len(negpos) else None,
            "FSDS_negative_QC0_count":flags["qc0"],
            "FSDS_negative_QC10_count":flags["qc10"],
            "FSDS_negative_QC50_count":flags["qc50"],
            "FSDS_negative_QC410_count":flags["qc410"],
            "FSDS_negative_QC420_count":flags["qc420"],
            "FSDS_negative_QC440_count":flags["qc440"],
            "FSDS_negative_QC_other_count":flags["other"],
            "FSDS_negative_solar_below_minus6deg":solar["below_minus6"],
            "FSDS_negative_solar_minus6_to0deg":solar["minus6_to0"],
            "FSDS_negative_solar_above0deg":solar["above0"],
            "wind_gt15_ms":len(windrows),
            "wind_max_ms":float(np.max(mapped["WIND"])),
            "precip_source_sum_mm":annual_mm,
            "precip_candidate_sum_mm":output_rain_mm,
            "science_approval":False,
        }
        return row,negrows,windrows


def emit_csv(path,headers,records):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=headers,delimiter="\t",extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def selftest():
    atnoon=jd_solar_cos(dt.datetime(2020,3,20,12),lat=0,lon=0)
    atmidnight=jd_solar_cos(dt.datetime(2020,3,20,0),lat=0,lon=0)
    assert atnoon>0.95 and atmidnight<-.95
    assert SHIFT_SECONDS==585*60
    assert len(VARS)==7 and N==17520
    assert set(YEARS)==set(range(2013,2019))
    print("STAGE13 SELF-TEST PASS: sun position, source mapping and calendar constants; NO SOURCE WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest()
        return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--candidates",type=Path,default=CANDIDATES)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    source=a.source.resolve()
    candidates=a.candidates.resolve()
    out=a.out.resolve()
    sourceroot=SOURCE_ROOT.resolve()
    if (a.out.is_symlink() or out.exists() or out==sourceroot
            or sourceroot in out.parents or out==candidates
            or candidates in out.parents):
        raise ValueError("New report output must be outside original and candidate data trees")
    if a.source.is_symlink() or not source.is_file():
        raise ValueError("Original source missing or symlinked")
    manifest_file=candidates/"stage12_ASM_candidate_manifest.json"
    if not manifest_file.is_file():raise FileNotFoundError(manifest_file)
    manifest=json.loads(manifest_file.read_text(encoding="utf-8"))
    if (manifest.get("operation")!="PROVISIONAL_NETCDF_WRITTEN"
            or manifest.get("science_approval") is not False
            or manifest.get("model_submission_authorised") is not False
            or manifest.get("source_sha256")!=EXPECTED_SHA):
        raise ValueError("Stage12 provisional manifest not approved for inspection")
    expected_set={str(candidates/f"AU-ASM_PROVISIONAL_DATM_{y}.nc") for y in YEARS}
    if set(manifest.get("provisional_DATM_files",[]))!=expected_set:
        raise ValueError("Manifest has wrong candidates or paths")
    original_hash=sha256(source)
    if original_hash!=EXPECTED_SHA:raise ValueError("Original source SHA256 changed")
    with netCDF4.Dataset(str(source),mode="r") as ds:
        t=ds.variables["time"]
        times=np.ma.asarray(t[:],dtype=np.float64).filled(np.nan)
        if t.ndim!=1 or not np.isfinite(times).all() or not np.all(np.diff(times)>0):
            raise ValueError("Original time coordinate changed or invalid")
        dim=t.dimensions[0]
        names={b for b,_ in VARS.values()}|{"Fsd_QCFlag","Ws_QCFlag","Precip_QCFlag"}
        data={name:source_series(ds,name,dim,len(times)) for name in names}
        yearrows=[]
        neglines=[]
        windlines=[]
        for y in YEARS:
            raw,ix,view=source_year_indexes(t,times,y)
            row,neg,wind=audit_one(ds,t,times,data,ix,view,y,candidates,original_hash)
            yearrows.append(row)
            neglines.extend(neg)
            windlines.extend(wind)
            print("YEAR",y,"EXACT_MAP",row["exact_f32_source_mapping_all_7"],
                  "FSDS_NEG",row["FSDS_negative_rows"],
                  "SOLAR_ABOVE0",row["FSDS_negative_solar_above0deg"],
                  "WIND_GT15",row["wind_gt15_ms"])
    if len(neglines)!=360 or (
            {x["year"]:x["FSDS_negative_rows"] for x in yearrows}.get(2014)!=359 or
            {x["year"]:x["FSDS_negative_rows"] for x in yearrows}.get(2016)!=1):
        raise ValueError("User-confirmed negative-FSDS counts not reproduced")
    if sha256(source)!=EXPECTED_SHA:raise ValueError("Original source changed during audit")
    out.mkdir(parents=True,exist_ok=False)
    emit_csv(out/"stage13_ASM_annual_exact_validation.tsv",YEAR_FIELDS,yearrows)
    emit_csv(out/"stage13_ASM_360_negative_FSDS.tsv",NEG_FIELDS,neglines)
    emit_csv(out/"stage13_ASM_wind_gt15.tsv",HIGHWIND_FIELDS,windlines)
    report={
      "stage":"OzFlux Stage13 AU-ASM candidate independent source-to-DATM science QC",
      "source_file_sha256":EXPECTED_SHA,
      "original_source_read_only":True,"candidate_files_read_only":True,
      "science_approval":False,"model_submission_authorised":False,
      "Fsd_negative_repair_authorised":False,
      "time_hypothesis":"Australia/Darwin LOCAL END minus 585 minutes to UTC CENTER; source convention remains under review",
      "number_of_candidate_files":len(yearrows),
      "number_of_negative_FSDS_records":len(neglines),
      "negative_FSDS_2014_and_2016_source_QC_and_solar":{
          str(y):{"negative":r["FSDS_negative_rows"],
                  "qc0":r["FSDS_negative_QC0_count"],
                  "qc420":r["FSDS_negative_QC420_count"],
                  "qc440":r["FSDS_negative_QC440_count"],
                  "solar_above0":r["FSDS_negative_solar_above0deg"],
                  "solar_below_minus6":r["FSDS_negative_solar_below_minus6deg"]}
          for y,r in zip(YEARS,yearrows) if r["FSDS_negative_rows"]>0
      },
      "annual":yearrows,
      "next_manual_science_gates":["Investigate negative FSDS original QC and solar elevation; no automatic clipping",
          "Check source time interval semantics and precipitation source histogram",
          "Confirm sensor heights and ZBOT basis (SH height missing; source ps lists 23m)",
          "Approve site-specific PFT fractions, bare-ground, sandy loam soil and surface file",
          "Independently confirm DATM streams and NOLEAP calendar against CIME cases"],
    }
    (out/"stage13_ASM_candidate_QC_summary.json").write_text(
       json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("STAGE13 PASS 6/6 SOURCE_TO_DATM_EXACT",len(neglines),"NEGATIVE_FSDS",
          len(windlines),"WIND_GT15")
    print("REPORT_DIR",out)
    print("SOURCE AND DATM UNCHANGED; MODEL NOT SUBMITTED; SCIENCE APPROVAL FALSE")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

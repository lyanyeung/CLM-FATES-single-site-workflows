#!/usr/bin/env python3
"""OzFlux 9-site Stage07: native-year forcing-readiness and QC provenance, READ ONLY.

Pure inventory: NOT an approval to create forcing, change time coordinates,
interpolate gaps, merge AU-ASM releases, or submit model jobs. Original source
NetCDFs opened in mode "r" only; reports are written under HOME.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
import sys

import netCDF4
import numpy as np

SOURCE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SITES = {"AU-ASM": 2, "AU-Cow": 1, "AU-Cpr": 1, "AU-DaS": 1,
         "AU-Dry": 1, "AU-Gin": 1, "AU-How": 1, "AU-Stp": 1, "AU-Tum": 1}
MET = ("Ta", "SH", "ps", "Fsd", "Fld", "Ws", "Precip")
QC_CODES = (0, 10, 50, 400, 410, 420, 430, 440)
CODEBOOK = {
    "0": "PyFluxPro Flag00 Good data (verify actual product lineage)",
    "10": "PyFluxPro Flag10 linear correction (verify actual product lineage)",
    "50": "PyFluxPro Flag50 interpolation (verify actual product lineage)",
    "400": "PyFluxPro GapFillFromAlternate unspecified",
    "410": "PyFluxPro GapFillFromAlternate AWS",
    "420": "PyFluxPro GapFillFromAlternate ACCESS",
    "430": "PyFluxPro GapFillFromAlternate ERA-Interim",
    "440": "PyFluxPro GapFillFromAlternate ERA5",
}
CODE_REF = [
    "https://github.com/OzFlux/PyFluxPro/blob/main/scripts/pfp_ts.py",
    "https://github.com/OzFlux/PyFluxPro/blob/main/scripts/pfp_gf.py",
]
INFO_KEYS = ("site_name", "fluxnet_id", "site", "latitude", "longitude",
             "altitude", "tower_height", "time_step", "time_zone",
             "timezone", "time_coverage_start", "time_coverage_end",
             "vegetation", "processing_level", "source", "history")
DETAIL_KEYS = ("units", "long_name", "height", "instrument", "source",
               "description_L2", "description_L3", "description_L4",
               "description_L5", "description_L6", "coverage_L6")
FILE_COLS = ("site","filename","status","n_records","first_native_time",
             "last_native_time","median_step_seconds","nonstandard_steps",
             "timezone_metadata","lat_metadata","lon_metadata")
YEAR_COLS = ("site","filename","year","native_year_count","expected_count",
             "time_count_matches","native_label_boundaries_match",
             "missing_met_rows_across_fields","physical_alarm_met_rows_across_fields",
             "flagged_nonzero_met_cell_count","candidate_status")
VAR_COLS = ("site","filename","year","variable","units","records",
            "finite_nonfill","missing","physical_alarm","qc_missing",
            "qc0","qc10","qc50","qc400","qc410","qc420",
            "qc430","qc440","qc_other_finite","qc_flag_source_unknown")


def manifest_rows(path):
    with path.open(encoding="utf-8-sig",newline="") as h:
        reader=csv.DictReader(h,delimiter="\t")
        if reader.fieldnames!=["site","filename"]:
            raise ValueError("Expected exact site<TAB>filename header")
        rows=list(reader)
    counts=dict.fromkeys(SITES,0)
    seen=set()
    for row in rows:
        site,name=row["site"],row["filename"]
        if site not in SITES or not name.endswith(".nc") or any(x in name for x in ("/","\\","..")):
            raise ValueError("Invalid source manifest row")
        if (site,name) in seen:
            raise ValueError("Duplicate source")
        seen.add((site,name))
        counts[site]+=1
    if len(rows)!=10 or counts!=SITES:
        raise ValueError("Expected 9 sites and 10 NetCDF files")
    return rows


def attr(v,name):
    if name not in v.ncattrs():
        return None
    x=v.getncattr(name)
    if hasattr(x,"tolist"):
        x=x.tolist()
    return str(x)[:500]


def field(ds,name,time_dim,n):
    if name not in ds.variables:
        raise KeyError(name)
    v=ds.variables[name]
    if not np.issubdtype(v.dtype,np.number) or v.dimensions.count(time_dim)!=1:
        raise ValueError("Unsupported numeric/time shape "+name)
    if v.shape[v.dimensions.index(time_dim)]!=n or any(
            d!=time_dim and v.shape[i]!=1 for i,d in enumerate(v.dimensions)):
        raise ValueError("Non-singleton variable shape "+name)
    result=np.ma.asarray(v[:],dtype=float).filled(np.nan).reshape(-1)
    if len(result)!=n:
        raise ValueError("Data length mismatch "+name)
    return result


def valid(arr):
    return np.isfinite(arr)&(arr>-9990)


def bounds(name,units):
    u=(units or "").lower().replace(" ","").replace("_","")
    if name=="Ta" and u in ("degc","degreecelsius","celsius","c"):
        return (-55.0,65.0)
    if name=="SH" and u in ("kg/kg","kgkg-1","kgkg^-1"):
        return (0.0,0.055)
    if name=="ps" and u=="kpa":
        return (45.0,115.0)
    if name in ("Fsd","Fld") and u in (
            "w/m^2","w/m2","wm-2","wm^-2","wm**-2"):
        return (-50.0,1600.0) if name=="Fsd" else (0.0,850.0)
    if name=="Ws" and u in ("m/s","ms-1","ms^-1"):
        return (-0.1,65.0)
    if name=="Precip" and u=="mm":
        return (0.0,None)
    return None


def physical_alarms(name,units,arr):
    limit=bounds(name,units)
    if limit is None:
        return None
    lo,hi=limit
    bad=valid(arr)&(arr<lo)
    if hi is not None:
        bad|=valid(arr)&(arr>hi)
    return bad


def unit_seconds(units):
    prefix=units.lower().split(" since ",1)[0].strip()
    options={"days":86400.0,"day":86400.0,"hours":3600.0,
             "hour":3600.0,"minutes":60.0,"minute":60.0,
             "seconds":1.0,"second":1.0}
    if prefix not in options:
        raise ValueError("Unsupported time scale "+units)
    return options[prefix]


def label(t,values,index):
    return str(netCDF4.num2date(float(values[index]),t.units,
                                calendar=getattr(t,"calendar","standard")))


def year_bounds(t,year):
    cal=getattr(t,"calendar","standard")
    return (
        float(netCDF4.date2num(dt.datetime(year,1,1),t.units,calendar=cal)),
        float(netCDF4.date2num(dt.datetime(year+1,1,1),t.units,calendar=cal)),
    )


def summarize_qc(q,index):
    if q is None:
        return {"qc_missing":len(index),"qc_other_finite":0,
                **{"qc"+str(k):0 for k in QC_CODES}}
    values=q[index]
    finite=np.isfinite(values)
    used=np.zeros(len(values),dtype=bool)
    data={"qc_missing":int((~finite).sum())}
    for k in QC_CODES:
        match=finite&(values==k)
        used|=match
        data["qc"+str(k)]=int(match.sum())
    data["qc_other_finite"]=int((finite&(~used)).sum())
    return data


def inspect_one(path,row):
    site,name=row["site"],row["filename"]
    with netCDF4.Dataset(str(path),mode="r") as ds:
        if "time" not in ds.variables:
            raise ValueError("Missing time axis")
        t=ds.variables["time"]
        if t.ndim!=1:
            raise ValueError("Time not 1-D")
        values=np.ma.asarray(t[:],dtype=float).filled(np.nan).reshape(-1)
        if not len(values) or not np.isfinite(values).all():
            raise ValueError("Missing or nonfinite times")
        step=np.diff(values)*unit_seconds(str(t.units))
        if not len(step) or np.any(step<=0):
            raise ValueError("Time not strictly increasing")
        median=float(np.median(step))
        unusual=int(np.sum(np.abs(step-median)>max(1.0,median*0.001)))
        first,last=label(t,values,0),label(t,values,len(values)-1)
        first_year,last_year=int(first[:4]),int(last[:4])
        if last_year<first_year or last_year-first_year>100:
            raise ValueError("Unreasonable year range")
        globals_={key:attr(ds,key) for key in INFO_KEYS if key in ds.ncattrs()}
        dim=t.dimensions[0]
        file_row={"site":site,"filename":name,"status":"AUDITED_SOURCE_ONLY",
                  "n_records":int(len(values)),"first_native_time":first,
                  "last_native_time":last,"median_step_seconds":median,
                  "nonstandard_steps":unusual,
                  "timezone_metadata":globals_.get("time_zone") or globals_.get("timezone"),
                  "lat_metadata":globals_.get("latitude"),
                  "lon_metadata":globals_.get("longitude")}
        data={}
        qc={}
        metadata={}
        for var in MET:
            data[var]=field(ds,var,dim,len(values))
            qcvar=var+"_QCFlag"
            qc[var]=(field(ds,qcvar,dim,len(values))
                     if qcvar in ds.variables else None)
            metadata[var]={key:attr(ds.variables[var],key) for key in DETAIL_KEYS
                           if key in ds.variables[var].ncattrs()}
        years=[]
        vars_=[]
        for year in range(first_year,last_year+1):
            lo,hi=year_bounds(t,year)
            a=int(np.searchsorted(values,lo,"left"))
            b=int(np.searchsorted(values,hi,"left"))
            ix=slice(a,b)
            n=b-a
            expected=int(round((hi-lo)*unit_seconds(str(t.units))/median))
            step_units=median/unit_seconds(str(t.units))
            label_start_ok=(n>0 and abs(values[a]-lo)*unit_seconds(str(t.units))<1.0)
            label_end_ok=(n>0 and abs(values[b-1]-(hi-step_units))*unit_seconds(str(t.units))<1.0)
            boundary=bool(label_start_ok and label_end_ok)
            missing_sum=0
            alarm_sum=0
            nonzero_flag_count=0
            unsupported_range=[]
            for v in MET:
                x=data[v][ix]
                good=valid(x)
                missing=int((~good).sum())
                alarm=physical_alarms(v,metadata[v].get("units"),x)
                if alarm is None:
                    unsupported_range.append(v)
                nq=int(alarm.sum()) if alarm is not None else 0
                histogram=summarize_qc(qc[v],ix)
                nonzero_flag_count+=n-histogram["qc0"]-histogram["qc_missing"]
                missing_sum+=missing
                alarm_sum+=nq
                vars_.append({"site":site,"filename":name,"year":year,
                              "variable":v,"units":metadata[v].get("units"),
                              "records":n,"finite_nonfill":int(good.sum()),
                              "missing":missing,"physical_alarm":nq if alarm is not None else None,
                              "qc_flag_source_unknown":True,**histogram})
            # Count, boundaries, range checks are *not* a timezone or L6-source approval.
            if n!=expected or unusual or not boundary:
                status="TIME_LABEL_OR_COUNT_REVIEW"
            elif missing_sum or alarm_sum or unsupported_range:
                status="HOLD_FORCING_PHYSICS_OR_UNITS"
            else:
                status="STRUCTURAL_CANDIDATE_ONLY_QC_UNAPPROVED"
            years.append({
                "site":site,"filename":name,"year":year,
                "native_year_count":n,"expected_count":expected,
                "time_count_matches":bool(n==expected),
                "native_label_boundaries_match":boundary,
                "missing_met_rows_across_fields":missing_sum,
                "physical_alarm_met_rows_across_fields":alarm_sum,
                "flagged_nonzero_met_cell_count":nonzero_flag_count,
                "candidate_status":status,
                "unrecognised_bounds_variables":unsupported_range,
            })
        return {"file":file_row,"years":years,"variables":vars_,
                "global_metadata":globals_,"variable_metadata":metadata,
                "time_units":str(t.units),
                "time_calendar":getattr(t,"calendar","standard"),
                "native_time_semantics_approval":False,
                "timezone_approval":False}


def write_table(path,cols,rows):
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=cols,delimiter="\t",extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def selftest():
    assert bounds("Fsd","W/m^2")==(-50,1600)
    assert bounds("Fld","W/m^2")==(0,850)
    assert bounds("SH","kg/kg")==(0,0.055)
    assert physical_alarms("SH","kg/kg",np.array([0.1,-0.01,0.005])).tolist()==[True,True,False]
    assert summarize_qc(np.array([0.,0.,410.,440.,np.nan]),slice(0,5))["qc410"]==1
    assert summarize_qc(np.array([0.,0.,410.,440.,np.nan]),slice(0,5))["qc_missing"]==1
    assert unit_seconds("days since 1800-01-01 00:00:00.0")==86400
    print("STAGE07 SELF-TEST PASS: radiation/negative-humidity alarm, native-year QC flags and time units; NO SOURCE WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest()
        return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--root",type=Path,default=SOURCE)
    args=p.parse_args()
    root,out=args.root.resolve(),args.out.resolve()
    if args.out.is_symlink() or out==root or root in out.parents:
        raise ValueError("Output must be outside all original NetCDF source trees")
    if out.exists():
        raise FileExistsError("Use a new timestamped output directory")
    rows=manifest_rows(args.manifest)
    file_rows,year_rows,variable_rows,extended=[],[],[],[]
    for row in rows:
        path=root/row["site"]/"forcing"/"raw"/row["filename"]
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError("Missing source or symlink: "+str(path))
        result=inspect_one(path,row)
        file_rows.append(result["file"])
        year_rows.extend(result["years"])
        variable_rows.extend(result["variables"])
        extended.append({"site":row["site"],"filename":row["filename"],
                         "global_metadata":result["global_metadata"],
                         "variable_metadata":result["variable_metadata"],
                         "time_units":result["time_units"],
                         "time_calendar":result["time_calendar"]})
        candidates=sum(y["candidate_status"]=="STRUCTURAL_CANDIDATE_ONLY_QC_UNAPPROVED"
                       for y in result["years"])
        print("SOURCE",row["site"],row["filename"],"ANNUAL_STRUCTURAL_CANDIDATES",
              candidates,"/",len(result["years"]))
    out.mkdir(parents=True)
    payload={
        "stage":"OzFlux Stage07 original native-year forcing readiness",
        "read_only":True,"science_approval":False,"forcing_generated":False,
        "native_timestamp_timezone_unapproved":True,
        "codebook_software_mapping_requires_source_specific_confirmation":CODEBOOK,
        "codebook_references":CODE_REF,"original_files_checked":len(file_rows),
        "files":extended,"native_year_summary":year_rows,
    }
    (out/"stage07_native_year_provenance.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
    write_table(out/"stage07_file_summary.tsv",FILE_COLS,file_rows)
    write_table(out/"stage07_year_status.tsv",YEAR_COLS,year_rows)
    write_table(out/"stage07_year_variable_qc.tsv",VAR_COLS,variable_rows)
    print("STAGE07 SOURCES",len(file_rows),"/10; NATIVE_YEAR_ROWS",len(year_rows))
    print("REPORT_DIR",out)
    print("YEAR CANDIDATE IS NOT FORCING OR QC APPROVAL")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

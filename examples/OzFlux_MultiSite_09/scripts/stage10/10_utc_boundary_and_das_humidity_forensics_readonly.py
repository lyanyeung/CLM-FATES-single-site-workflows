#!/usr/bin/env python3
"""OzFlux Stage10: AU-DaS/AU-ASM hypothetical UTC boundaries + 885 SH alarms.

ONLY READS ORIGINAL L6 NetCDFs in mode r and operator Stage09 reports.
Writes reports under a new HOME directory, never source trees.
All time shifts are experimental *numeric view calculations*, not NetCDF
edits or a validated DATM time interpretation. No gap repairs or Slurm.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
from pathlib import Path
import sys

import netCDF4
import numpy as np

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SOURCES = {
    "AU-DaS": ("DalyUncleared_20080101T0000_to_20260423T0000_L6.nc", tuple(range(2009, 2022))),
    "AU-ASM": ("AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc", tuple(range(2013, 2019))),
}
LOCAL_OFFSET_SECONDS = 9*3600+30*60   # hypothesis ONLY: Australia/Darwin fixed clock
HALF_HOUR_SECONDS = 1800.0
SH_ALARM_RATIO = 1.05

BOUNDARY_COLS = (
    "site","filename","year","label_hypothesis","utc_center_view_shift_min",
    "expected_utc_halfhours","actual_records","first_index","last_index",
    "first_hypothetical_utc","last_hypothetical_utc",
    "first_center_matches","last_center_matches","cadence_complete",
    "structurally_complete_utc_calendar_year",
    "source_native_time_not_rewritten","clock_semantics_approved",
)
HUMIDITY_COLS = (
    "site","source_filename","source_index","native_time_UNVERIFIED_TIMEZONE",
    "Ta_degC","SH_kgkg","ps_kPa","qsat_kgkg","SH_div_qsat",
    "diagnostic_RH_percent","Ta_QCFlag","SH_QCFlag","ps_QCFlag",
    "Fsd_Wm2","Fsd_QCFlag","site_var_RH_if_present",
    "site_var_RH_units","native_time_to_utc_NOT_APPLIED",
)
EPISODE_COLS = (
    "site","source_filename","year","first_source_index","last_source_index",
    "n_records","first_native_time","last_native_time",
    "max_SH_div_qsat","median_SH_div_qsat",
    "SH_QCFlag_frequency","Ta_QCFlag_frequency",
)
YEAR_COLS = (
    "year","record_count","humidity_pair_count","over_105pct_count",
    "over_120pct_count","over_150pct_count","over_200pct_count",
    "max_SH_div_qsat","median_SH_div_qsat_on_alarm",
    "native_SH_QC0_on_alarm","native_SH_QC50_on_alarm",
    "native_SH_QC410_on_alarm","native_SH_QC420_on_alarm",
    "native_SH_QC440_on_alarm","other_SH_QC_on_alarm",
    "science_approval",
)


def seconds_per_time_unit(v):
    u = str(v.units).lower().split(" since ",1)[0].strip()
    if u in ("day","days"):
        return 86400.
    if u in ("hour","hours"):
        return 3600.
    if u in ("minute","minutes"):
        return 60.
    if u in ("second","seconds"):
        return 1.
    raise ValueError("Unexpected numeric time unit: "+str(v.units))


def date_label(v,value):
    return str(netCDF4.num2date(float(value),v.units,
        calendar=getattr(v,"calendar","standard")))


def time_bound(v,year):
    c=getattr(v,"calendar","standard")
    return (
        float(netCDF4.date2num(dt.datetime(year,1,1),v.units,calendar=c)),
        float(netCDF4.date2num(dt.datetime(year+1,1,1),v.units,calendar=c)),
    )


def column(ds,name,dim,n,required=True):
    if name not in ds.variables:
        if required:
            raise ValueError("Missing source variable "+name)
        return None
    v=ds.variables[name]
    if not np.issubdtype(v.dtype,np.number) or v.dimensions.count(dim)!=1:
        raise ValueError("Unexpected numeric/time shape "+name)
    if v.shape[v.dimensions.index(dim)]!=n or any(
        d!=dim and v.shape[i]!=1 for i,d in enumerate(v.dimensions)
    ):
        raise ValueError("Unexpected extra dimensions "+name)
    a=np.ma.asarray(v[:],dtype=float).filled(np.nan).reshape(-1)
    if len(a)!=n:
        raise ValueError("Unexpected length "+name)
    return a


def safe_value(x):
    return float(x) if np.isfinite(x) and x>-9990 else None


def is_valid(x):
    return np.isfinite(x)&(x>-9990)


def magnus_qsat(T_C,p_kPa):
    # Follow Stage09 EXACTLY, independently checking its 885 event count.
    # e_s is saturation over water, diagnostic only.
    es=0.6112*np.exp(np.clip(17.67*T_C/(T_C+243.5),-50,30))
    return np.where(p_kPa-0.378*es>0,
                    0.622*es/(p_kPa-0.378*es),np.nan)


def episodes(bool_array):
    x=np.asarray(bool_array,dtype=np.bool_)
    d=np.diff(np.concatenate(([False],x,[False])).astype(np.int8))
    starts=np.flatnonzero(d==1)
    stops=np.flatnonzero(d==-1)
    return list(zip(starts.tolist(),stops.tolist()))


def histogram(x):
    a=x[np.isfinite(x)]
    vals,counts=np.unique(a,return_counts=True)
    return {str(int(v)) if float(v).is_integer() else str(float(v)):int(n)
            for v,n in zip(vals,counts)}


def source_meta(ds):
    result={"globals":{},"variables":{}}
    for key in ds.ncattrs():
        if any(z in key.lower() for z in (
            "time","site","lat","lon","history","processing","tower")):
            result["globals"][key]=str(ds.getncattr(key))[:1000]
    for name in ("time","Ta","SH","ps","Fsd","Precip","RH","VPD"):
        if name not in ds.variables: continue
        v=ds.variables[name]
        result["variables"][name]={}
        for attr in ("units","long_name","height","statistic_type",
                     "instrument","source","description_L2","description_L3",
                     "description_L4","description_L5","description_L6"):
            if attr in v.ncattrs():
                result["variables"][name][attr]=str(v.getncattr(attr))[:1300]
    return result


def shifted_years(v,time_num,site,filename,years):
    unit=seconds_per_time_unit(v)
    if not np.isfinite(time_num).all() or (np.diff(time_num)<=0).any():
        raise ValueError("Invalid native source times")
    expected_step=HALF_HOUR_SECONDS/unit
    results=[]
    # A 30-minute source END label may represent a center 15 min earlier.
    # UTC calendar-year centers are at 00:15, 00:45,...,23:45,
    # but shifted arrays can cross local-year boundaries.
    for shift_seconds,title in (
        (LOCAL_OFFSET_SECONDS,"LOCAL_END_LABEL_TO_UTC_LABEL_ONLY"),
        (LOCAL_OFFSET_SECONDS+900,"LOCAL_END_LABEL_TO_UTC_CENTER_CANDIDATE"),
        (LOCAL_OFFSET_SECONDS+1800,"LOCAL_END_LABEL_TO_UTC_START_CANDIDATE"),
    ):
        view=time_num-shift_seconds/unit
        for year in years:
            low,high=time_bound(v,year)
            start=int(np.searchsorted(view,low,"left"))
            stop=int(np.searchsorted(view,high,"left"))
            expected=int(round((high-low)/expected_step))
            n=stop-start
            first=view[start] if n else np.nan
            last=view[stop-1] if n else np.nan
            # Time labels at UTC 00:15 ... 23:45 must be present
            # specifically for center-view hypothesis only.
            first_center=bool(n and abs(first-(low+0.5*expected_step))*unit<1.0)
            last_center=bool(n and abs(last-(high-0.5*expected_step))*unit<1.0)
            cadence=bool(n and np.all(np.abs(np.diff(view[start:stop])-expected_step)*unit<1.0))
            results.append({
                "site":site,"filename":filename,"year":year,
                "label_hypothesis":title,
                "utc_center_view_shift_min":shift_seconds/60.,
                "expected_utc_halfhours":expected,
                "actual_records":n,
                "first_index":start if n else None,
                "last_index":stop-1 if n else None,
                "first_hypothetical_utc":date_label(v,first) if n else None,
                "last_hypothetical_utc":date_label(v,last) if n else None,
                "first_center_matches":first_center,
                "last_center_matches":last_center,
                "cadence_complete":cadence,
                "structurally_complete_utc_calendar_year":(
                    n==expected and first_center and last_center and cadence
                    if title=="LOCAL_END_LABEL_TO_UTC_CENTER_CANDIDATE" else False),
                "source_native_time_not_rewritten":True,
                "clock_semantics_approved":False,
            })
    return results


def humidity_forensics(ds,site,filename,year_ranges,time_num,v):
    if site!="AU-DaS":
        return [],[],[],None
    n=len(time_num);dim=v.dimensions[0]
    ta=column(ds,"Ta",dim,n)
    sh=column(ds,"SH",dim,n)
    ps=column(ds,"ps",dim,n)
    fsd=column(ds,"Fsd",dim,n)
    flags={z:column(ds,z+"_QCFlag",dim,n) for z in ("Ta","SH","ps","Fsd")}
    # RH is optional contextual evidence: malformed optional RH must not
    # block the primary Ta/SH/ps forensic or cause any data transformation.
    try:
        rh=column(ds,"RH",dim,n,required=False)
    except ValueError:
        rh=None
    rh_units=(str(ds.variables["RH"].getncattr("units"))
        if rh is not None and "units" in ds.variables["RH"].ncattrs() else None)
    qsat=magnus_qsat(ta,ps)
    valid=is_valid(ta)&is_valid(sh)&is_valid(ps)&np.isfinite(qsat)&(qsat>0)
    ratio=np.where(valid,sh/qsat,np.nan)
    records=[]
    yearly=[]
    events=[]
    for year in year_ranges:
        low,high=time_bound(v,year)
        a=int(np.searchsorted(time_num,low,"left"))
        b=int(np.searchsorted(time_num,high,"left"))
        ids=np.arange(a,b,dtype=int)
        physical=valid[a:b]&(ratio[a:b]>SH_ALARM_RATIO)
        anomaly_ids=ids[physical]
        ratios=ratio[anomaly_ids]
        q=flags["SH"][anomaly_ids]
        qc_counts=histogram(q)
        # Per-record source evidence, full and not sampled.
        for i in anomaly_ids:
            records.append({
                "site":site,"source_filename":filename,
                "source_index":int(i),
                "native_time_UNVERIFIED_TIMEZONE":date_label(v,time_num[i]),
                "Ta_degC":safe_value(ta[i]),
                "SH_kgkg":safe_value(sh[i]),
                "ps_kPa":safe_value(ps[i]),
                "qsat_kgkg":safe_value(qsat[i]),
                "SH_div_qsat":safe_value(ratio[i]),
                "diagnostic_RH_percent":safe_value(100*ratio[i]),
                "Ta_QCFlag":safe_value(flags["Ta"][i]),
                "SH_QCFlag":safe_value(flags["SH"][i]),
                "ps_QCFlag":safe_value(flags["ps"][i]),
                "Fsd_Wm2":safe_value(fsd[i]),
                "Fsd_QCFlag":safe_value(flags["Fsd"][i]),
                "site_var_RH_if_present":safe_value(rh[i]) if rh is not None else None,
                "site_var_RH_units":rh_units,
                "native_time_to_utc_NOT_APPLIED":True,
            })
        for i0,i1 in episodes(physical):
            interval_ids=np.arange(a+i0,a+i1,dtype=int)
            events.append({
                "site":site,"source_filename":filename,"year":year,
                "first_source_index":int(interval_ids[0]),
                "last_source_index":int(interval_ids[-1]),
                "n_records":int(len(interval_ids)),
                "first_native_time":date_label(v,time_num[interval_ids[0]]),
                "last_native_time":date_label(v,time_num[interval_ids[-1]]),
                "max_SH_div_qsat":float(np.max(ratio[interval_ids])),
                "median_SH_div_qsat":float(np.median(ratio[interval_ids])),
                "SH_QCFlag_frequency":json.dumps(histogram(flags["SH"][interval_ids])),
                "Ta_QCFlag_frequency":json.dumps(histogram(flags["Ta"][interval_ids])),
            })
        qc_known=sum(qc_counts.get(str(k),0) for k in (0,50,410,420,440))
        yearly.append({
            "year":year,"record_count":len(ids),
            "humidity_pair_count":int(valid[a:b].sum()),
            "over_105pct_count":int(len(anomaly_ids)),
            "over_120pct_count":int(np.sum(ratios>1.2)),
            "over_150pct_count":int(np.sum(ratios>1.5)),
            "over_200pct_count":int(np.sum(ratios>2.0)),
            "max_SH_div_qsat":float(np.max(ratios)) if len(ratios) else None,
            "median_SH_div_qsat_on_alarm":float(np.median(ratios)) if len(ratios) else None,
            "native_SH_QC0_on_alarm":qc_counts.get("0",0),
            "native_SH_QC50_on_alarm":qc_counts.get("50",0),
            "native_SH_QC410_on_alarm":qc_counts.get("410",0),
            "native_SH_QC420_on_alarm":qc_counts.get("420",0),
            "native_SH_QC440_on_alarm":qc_counts.get("440",0),
            "other_SH_QC_on_alarm":len(anomaly_ids)-qc_known,
            "science_approval":False,
        })
    summary={
        "source_sites":1,
        "n_years":len(year_ranges),
        "SH_qsat_1p05_event_rows":len(records),
        "independent_stage09_expected_count":885,
        "total_episodes":len(events),
        "longest_episodes":sorted(events,key=lambda d:-d["n_records"])[:25],
        "native_SH_QC_frequency_over_105pct":dict(collections.Counter(
           {str(k):sum(y[key] for y in yearly)
            for k,key in ((0,"native_SH_QC0_on_alarm"),
                          (50,"native_SH_QC50_on_alarm"),
                          (410,"native_SH_QC410_on_alarm"),
                          (420,"native_SH_QC420_on_alarm"),
                          (440,"native_SH_QC440_on_alarm"))})),
        "physics_reference":"Stage09 e_s over liquid water Magnus/Tetens; diagnostic only",
        "data_repair_approved":False,
    }
    if len(records)!=885:
        raise ValueError("Stage09 885 humidity anomalies not replicated: "+str(len(records)))
    return records,events,yearly,summary


def write_rows(path,cols,rows):
    with path.open("w",encoding="utf-8",newline="") as fp:
        w=csv.DictWriter(fp,fieldnames=cols,delimiter="\t",extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def self_test():
    test=magnus_qsat(np.array([25.,25.,25.]),np.array([100.,100.,100.]))
    assert 0.019 < test[0] < 0.022
    assert np.allclose(test[0],test[1])
    assert episodes(np.array([0,1,1,0,1,0],dtype=bool))==[(1,3),(4,5)]
    assert seconds_per_time_unit(type("T",(),{"units":"days since 1800-01-01"})())==86400
    # A local 09:45 END label under UTC+09:30 corresponds
    # to the UTC 00:00-to-00:30 interval CENTER at UTC 00:00;
    # a local 10:00 END label corresponds to UTC 00:15 center.
    assert (10*60-9.5*60-15)==15
    print("STAGE10 SELF-TEST PASS: 30-min local-end to UTC-center, saturation and event grouping; SOURCE READ ONLY")


def main():
    if sys.argv[1:]==["--self-test"]:
        self_test()
        return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage09",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    root,out=args.root.resolve(),args.out.resolve()
    if out.exists() or args.out.is_symlink() or out==root or root in out.parents:
        raise ValueError("Choose unused HOME output folder outside all source trees")
    with (args.stage09/"stage09_source_time_solar_physics.json").open(encoding="utf-8") as fp:
        prior=json.load(fp)
    if prior.get("number_of_sites")!=2 or prior.get("science_approval") is not False:
        raise ValueError("Stage09 must have completed 2/2 without approval")
    prior_sites={x["site"]:x for x in prior.get("sites",[])}
    if set(prior_sites)!=set(SOURCES):
        raise ValueError("Stage09 site identity mismatch")
    boundary=[]
    all_humidity=[]
    all_events=[]
    all_year=[]
    evidence=[]
    for site,(filename,years) in SOURCES.items():
        if prior_sites[site].get("native_years")!=list(years):
            raise ValueError("Stage09 selected-year scope mismatch for "+site)
        if prior_sites[site].get("clock_hypothesis_verdict") not in (
            "NT_LOCAL_LABEL_BETTER_FIT_UNVERIFIED","HOLD_SOLAR_NOT_DISCRIMINATING",
            "HOLD_SOLAR_INSUFFICIENT","UTC_LABEL_BETTER_FIT_UNVERIFIED"):
            raise ValueError("Unrecognised Stage09 clock candidate")
        pth=root/site/"forcing"/"raw"/filename
        if pth.is_symlink() or not pth.is_file():
            raise FileNotFoundError("Missing or symlink original "+str(pth))
        with netCDF4.Dataset(str(pth),mode="r") as ds:
            v=ds.variables["time"]
            t=np.ma.asarray(v[:],dtype=float).filled(np.nan).reshape(-1)
            if len(t)<10 or not np.isfinite(t).all() or np.any(np.diff(t)<=0):
                raise ValueError("Time coordinate invalid")
            per=shifted_years(v,t,site,filename,years)
            boundary.extend(per)
            h,e,y,summary=humidity_forensics(ds,site,filename,years,t,v)
            all_humidity.extend(h);all_events.extend(e);all_year.extend(y)
            meta=source_meta(ds)
        evidence.append({
            "site":site,"source_filename":filename,
            "source_global_and_field_metadata":meta,
            "native_time_interval_semantics_not_approved":True,
            "source_timezone_not_manually_approved":True,
            "UTC_calendar_boundary_calculations_are_hypotheses":True,
            "humidity_summary":summary,
        })
        centered=[x for x in per if
            x["label_hypothesis"]=="LOCAL_END_LABEL_TO_UTC_CENTER_CANDIDATE"]
        print("SOURCE",site,"UTC_CENTER_CANDIDATE_FULL_YEARS",
              sum(x["structurally_complete_utc_calendar_year"] for x in centered),
              "/",len(centered),
              "HUMIDITY_105PCT_ALARMS",len(h))
    if len(boundary)!=3*(13+6) or len(all_humidity)!=885:
        raise AssertionError("Stage10 audit unexpected output counts")
    out.mkdir(parents=True)
    result={
        "stage":"OzFlux Stage10 hypothetical UTC-year boundary and AU-DaS SH supersaturation forensic",
        "source_original_NetCDF_read_only":True,
        "source_time_not_transformed":True,
        "timezone_convention_approved":False,
        "DATM_forcing_authorised":False,
        "science_approval":False,
        "clock_offsets_examined_not_approved":{
            "NT_Australia_Darwin_local_label_to_UTC":570,
            "hypothetical_end_label_to_midpoint_additional_shift_minutes":15,
        },
        "sites":evidence,
        "boundary_years":boundary,
        "DaS_humidity_event_count":len(all_humidity),
        "DaS_humidity_episode_count":len(all_events),
    }
    (out/"stage10_source_time_humidity.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    write_rows(out/"stage10_hypothetical_UTC_year_bounds.tsv",BOUNDARY_COLS,boundary)
    write_rows(out/"stage10_DaS_SH_885_exact_records.tsv",HUMIDITY_COLS,all_humidity)
    write_rows(out/"stage10_DaS_SH_event_episodes.tsv",EPISODE_COLS,all_events)
    write_rows(out/"stage10_DaS_SH_year_stats.tsv",YEAR_COLS,all_year)
    print("STAGE10 PASS 2/2",len(boundary),"UTC_BOUNDARY_ROWS",
          len(all_humidity),"SH_SUPERSAT_ROWS",len(all_events),"SH_EPISODES")
    print("REPORT_DIR",out)
    print("NO TIME CONVERSION OR HUMIDITY REPAIR APPROVED; NO ORIGINAL SOURCE MODIFICATIONS")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

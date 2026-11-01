#!/usr/bin/env python3
"""OzFlux Stage09: first-cohort source-time/solar/physics science gate, READ ONLY.

For AU-DaS 2009-2021 and AU-ASM Mulga1 2013-2018 ONLY.
Uses official OzFlux site coords as independent solar-reference constraints.
Does not infer exact timestamp interval convention or approve any forcing.
Does not alter source, fill gaps, create DATM, or submit Slurm.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path
import sys

import netCDF4
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
CASES={
    "AU-DaS":{
        "filename":"DalyUncleared_20080101T0000_to_20260423T0000_L6.nc",
        "years":list(range(2009,2022)),
        "lat":-14.1592,"lon":131.3881,
        "coord_ref":"https://www.ozflux.org.au/monitoringsites/dalyuncleared/dalyuncleared_description.html",
    },
    "AU-ASM":{
        "filename":"AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc",
        "years":list(range(2013,2019)),
        "lat":-22.2828,"lon":133.2493,
        "coord_ref":"https://ozflux.org.au/monitoringsites/alicesprings/alicesprings_description.html",
    },
}
MET=("Ta","SH","ps","Fsd","Fld","Ws","Precip")
CANDIDATE="STRUCTURAL_CANDIDATE_ONLY_QC_UNAPPROVED"
TIMEROW=("site","year","status","records","expected_records","missing_met","broad_physics_alarms",
         "physical_SH_negative","physical_SH_supersaturation_gt_105pct",
         "QCflag0_count","QCflag410_count","QCflag420_count","QCflag440_count",
         "science_approval")


def manifest_check(path):
    with path.open(encoding="utf-8-sig", newline="") as h:
        r=list(csv.DictReader(h,delimiter="\t"))
    if len(r)!=10:
        raise ValueError("Manifest should have 10 files")
    for site,cfg in CASES.items():
        if sum(x["site"]==site and x["filename"]==cfg["filename"] for x in r)!=1:
            raise ValueError("Expected source file not unique in manifest: "+site)
    return True


def load_years(path):
    with path.open(encoding="utf-8",newline="") as h:
        r=list(csv.DictReader(h,delimiter="\t"))
    index={}
    for row in r:
        key=(row["site"],row["filename"],int(row["year"]))
        if key in index:
            raise ValueError("Duplicate Stage07 status row")
        index[key]=row
    for site,cfg in CASES.items():
        for year in cfg["years"]:
            key=(site,cfg["filename"],year)
            if key not in index or index[key]["candidate_status"]!=CANDIDATE:
                raise ValueError("Blocked first-cohort year: "+str(key))
    return index


def attr(v, key):
    if key not in v.ncattrs():
        return None
    val=v.getncattr(key)
    if hasattr(val,"tolist"):
        val=val.tolist()
    return str(val)[:1000]


def data(ds,name,time_dim,n):
    if name not in ds.variables:
        raise ValueError("Missing source series "+name)
    v=ds.variables[name]
    if not np.issubdtype(v.dtype,np.number) or v.dimensions.count(time_dim)!=1:
        raise ValueError("Non-numeric or non-1D time series "+name)
    if v.shape[v.dimensions.index(time_dim)]!=n:
        raise ValueError("Different time length "+name)
    if any(d!=time_dim and v.shape[i]!=1 for i,d in enumerate(v.dimensions)):
        raise ValueError("Non-singleton extra dimensions "+name)
    x=np.ma.asarray(v[:],dtype=np.float64).filled(np.nan).reshape(-1)
    if len(x)!=n:
        raise ValueError("Reshape different from time length")
    return x


def good(x):
    return np.isfinite(x)&(x>-9990)


def header_coord(ds, direction):
    for key in (direction, direction+"_deg", "site_"+direction):
        if key in ds.ncattrs():
            try:
                return float(ds.getncattr(key)),key
            except (ValueError,TypeError):
                pass
    for key in (direction,"LATIXY" if direction=="latitude" else "LONGXY",
                "lat" if direction=="latitude" else "lon"):
        if key in ds.variables:
            arr=np.ma.asarray(ds.variables[key][:],dtype=np.float64).filled(np.nan)
            if arr.size==1 and np.isfinite(arr.reshape(-1)[0]):
                return float(arr.reshape(-1)[0]),"variable:"+key
    return None,None


def local_solar_cos(dates, lat_deg, lon_deg):
    # NOAA-style analytic solar position, a coarse QC diagnostic only.
    # dates are UTC datetimes, not arbitrary source-native datetimes.
    frac=np.array([p.timetuple().tm_yday-1+(p.hour+p.minute/60+p.second/3600-12)/24
                   for p in dates],dtype=float)
    yr=np.array([366 if p.year%4==0 and (p.year%100!=0 or p.year%400==0) else 365
                 for p in dates],dtype=float)
    gamma=2*np.pi*frac/yr
    eqtime=229.18*(0.000075+0.001868*np.cos(gamma)-0.032077*np.sin(gamma)
                   -0.014615*np.cos(2*gamma)-0.040849*np.sin(2*gamma))
    decl=(0.006918-0.399912*np.cos(gamma)+0.070257*np.sin(gamma)
          -0.006758*np.cos(2*gamma)+0.000907*np.sin(2*gamma)
          -0.002697*np.cos(3*gamma)+0.00148*np.sin(3*gamma))
    utc_minutes=np.array([p.hour*60+p.minute+p.second/60 for p in dates],dtype=float)
    t_solar=(utc_minutes+eqtime+4*lon_deg)%1440
    angle=np.radians(t_solar/4-180)
    lat=np.radians(lat_deg)
    return np.sin(lat)*np.sin(decl)+np.cos(lat)*np.cos(decl)*np.cos(angle)


def decode_sampled_times(v, time_numeric, selected, upper=18000):
    # Full source-time audits already done in Stage02. Limit expensive Python
    # cftime object conversions for each solar hypothesis.
    step=max(1,int(math.ceil(len(selected)/upper)))
    idx=np.asarray(selected[::step],dtype=int)
    dates_raw=netCDF4.num2date(time_numeric[idx],v.units,
             calendar=getattr(v,"calendar","standard"))
    dates=[dt.datetime(int(d.year),int(d.month),int(d.day),int(d.hour),
                       int(d.minute),int(d.second)) for d in dates_raw]
    return idx,dates


def solar_trials(native, rad, lat, lon):
    trials=[]
    valid=good(rad)
    for utc_offset in (0.0,9.5):
        for midpoint_shift in (-30,-15,0,15,30):
            dates=[t-dt.timedelta(hours=utc_offset)+dt.timedelta(minutes=midpoint_shift)
                   for t in native]
            cosz=local_solar_cos(dates,lat,lon)
            x=np.asarray(rad,dtype=float)
            mask=valid&np.isfinite(cosz)
            high=mask&(x>50)
            solar=np.maximum(cosz,0)
            rho=(float(np.corrcoef(x[mask],solar[mask])[0,1])
                 if mask.sum()>30 and np.std(x[mask])>0 and np.std(solar[mask])>0 else None)
            trials.append({
                "source_label_utc_offset_hours_hypothesis":utc_offset,
                "source_label_to_interval_midpoint_minutes_hypothesis":midpoint_shift,
                "valid_sample_count":int(mask.sum()),
                "irradiance_above_50_n":int(high.sum()),
                "high_Fsd_modelled_night_count":int(np.sum(high&(cosz<=0))),
                "high_Fsd_modelled_night_fraction":(
                    float(np.sum(high&(cosz<=0))/high.sum()) if high.sum() else None),
                "Fsd_vs_positive_solar_cos_correlation":rho,
                "time_semantics_approved":False,
            })
    trials.sort(key=lambda d:(-(d["Fsd_vs_positive_solar_cos_correlation"]
                        if d["Fsd_vs_positive_solar_cos_correlation"] is not None else -2),
                            d["high_Fsd_modelled_night_count"]))
    return trials


def physics(t, p, sh):
    # Saturation specific humidity from Magnus/Tetens approximation.
    # For audit only; does not rewrite humidity or temperature.
    e=0.6112*np.exp(np.clip(17.67*t/(t+243.5),-50,30))
    denom=p-0.378*e
    qs=np.where(denom>0,0.622*e/denom,np.nan)
    ok=good(t)&good(p)&good(sh)&np.isfinite(qs)&(qs>0)
    return {
        "humidity_pair_count":int(ok.sum()),
        "SH_negative_records":int(np.sum(ok&(sh<0))),
        "SH_above_1p05_qsat_records":int(np.sum(ok&(sh>1.05*qs))),
        "SH_above_1p2_qsat_records":int(np.sum(ok&(sh>1.20*qs))),
        "calculation_note":"Magnus e_s in kPa, Ta in degC, ps in kPa, SH in kg/kg; diagnostic threshold only",
    }


def inspect_file(root,site,cfg,stage_years):
    source=root/site/"forcing"/"raw"/cfg["filename"]
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError("Missing or symlink source: "+str(source))
    with netCDF4.Dataset(str(source),mode="r") as ds:
        v=ds.variables["time"]
        nums=np.ma.asarray(v[:],dtype=float).filled(np.nan).reshape(-1)
        dim=v.dimensions[0];n=len(nums)
        if n<10 or not np.isfinite(nums).all() or not np.all(np.diff(nums)>0):
            raise ValueError("Original time axis not increasing")
        src_lat,lat_kind=header_coord(ds,"latitude")
        src_lon,lon_kind=header_coord(ds,"longitude")
        if src_lat is not None and abs(src_lat-cfg["lat"])>0.05:
            raise ValueError("Source latitude disagrees with official site coords")
        if src_lon is not None and abs(src_lon-cfg["lon"])>0.05:
            raise ValueError("Source longitude disagrees with official site coords")
        meta={key:attr(ds,key) for key in ds.ncattrs()
              if any(x in key.lower() for x in ("time","latitude","longitude","height",
                  "site","instrument","history","processing"))}
        fields={}
        qcs={}
        field_meta={}
        for key in MET:
            fields[key]=data(ds,key,dim,n)
            qcs[key]=data(ds,key+"_QCFlag",dim,n)
            field_meta[key]={key2:attr(ds.variables[key],key2) for key2 in (
                "units","height","instrument","source","long_name","statistic_type",
                "description_L4","description_L5","description_L6","coverage_L6")}
        if (field_meta["Ta"]["units"]!="degC" or field_meta["SH"]["units"]!="kg/kg"
                or field_meta["ps"]["units"]!="kPa"
                or field_meta["Fsd"]["units"] not in ("W/m^2","W/m2")
                or field_meta["Precip"]["units"]!="mm"):
            raise ValueError("Unexpected source forcing units; do not assume previous AU-How conversions")
        all_indices=[]
        per_year=[]
        for year in cfg["years"]:
            start=netCDF4.date2num(dt.datetime(year,1,1),v.units,
                                    calendar=getattr(v,"calendar","standard"))
            stop=netCDF4.date2num(dt.datetime(year+1,1,1),v.units,
                                    calendar=getattr(v,"calendar","standard"))
            a=int(np.searchsorted(nums,start,"left"))
            b=int(np.searchsorted(nums,stop,"left"))
            expected=stage_years[(site,cfg["filename"],year)]
            if b-a != int(expected["native_year_count"]):
                raise ValueError("Stage07 and original source year count mismatch")
            ix=np.arange(a,b,dtype=int)
            all_indices.extend(ix)
            missing=sum(int(np.sum(~good(fields[key][ix]))) for key in MET)
            q0=sum(int(np.sum(qcs[key][ix]==0)) for key in MET)
            q410=sum(int(np.sum(qcs[key][ix]==410)) for key in MET)
            q420=sum(int(np.sum(qcs[key][ix]==420)) for key in MET)
            q440=sum(int(np.sum(qcs[key][ix]==440)) for key in MET)
            ph=physics(fields["Ta"][ix],fields["ps"][ix],fields["SH"][ix])
            per_year.append({
                "site":site,"year":year,"status":"TIME_AND_PHYSICS_SOURCE_REVIEW",
                "records":b-a,"expected_records":int(expected["expected_count"]),
                "missing_met":missing,
                "broad_physics_alarms":int(expected["physical_alarm_met_rows_across_fields"]),
                "physical_SH_negative":ph["SH_negative_records"],
                "physical_SH_supersaturation_gt_105pct":ph["SH_above_1p05_qsat_records"],
                "QCflag0_count":q0,"QCflag410_count":q410,
                "QCflag420_count":q420,"QCflag440_count":q440,
                "science_approval":False,
            })
        subset=np.array(all_indices,dtype=int)
        idx,raw_dates=decode_sampled_times(v,nums,subset)
        rad=fields["Fsd"][idx]
        trials=solar_trials(raw_dates,rad,cfg["lat"],cfg["lon"])
        winner=trials[0]
        scores={}
        for off in (0.0,9.5):
            selections=[x for x in trials if x["source_label_utc_offset_hours_hypothesis"]==off]
            scores[str(off)]=max(
                (x["Fsd_vs_positive_solar_cos_correlation"]
                 for x in selections if x["Fsd_vs_positive_solar_cos_correlation"] is not None),
                default=None)
        if scores["0.0"] is None or scores["9.5"] is None:
            verdict="HOLD_SOLAR_INSUFFICIENT"
        elif abs(scores["0.0"]-scores["9.5"])<0.10:
            verdict="HOLD_SOLAR_NOT_DISCRIMINATING"
        else:
            verdict=("UTC_LABEL_BETTER_FIT_UNVERIFIED" if scores["0.0"]>scores["9.5"]
                     else "NT_LOCAL_LABEL_BETTER_FIT_UNVERIFIED")
        return {
            "site":site,"filename":cfg["filename"],
            "site_reference":cfg["coord_ref"],
            "reference_lat":cfg["lat"],"reference_lon":cfg["lon"],
            "source_lat":src_lat,"source_lon":src_lon,
            "source_lat_provenance":lat_kind,"source_lon_provenance":lon_kind,
            "solar_reference_position_is_NOT_a_forcing_geometry_approval":True,
            "global_metadata":meta,"variable_metadata":field_meta,
            "source_native_clock_convention_not_approved":True,
            "time_shift_or_resampling_authorised":False,
            "candidate_solar_scores_best_by_clock_offset":scores,
            "clock_hypothesis_verdict":verdict,
            "solar_trials":trials,
            "sampled_solar_rows":len(idx),
            "all_year_native_rows":len(subset),
            "native_years":list(cfg["years"]),
            "source_precip_mm_interval_semantics_not_approved":True,
        },per_year


def table(path,rows):
    with path.open("w",encoding="utf-8",newline="") as h:
        writer=csv.DictWriter(h,fieldnames=TIMEROW,delimiter="\t",
                              extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def self_test():
    test=[dt.datetime(2020,3,20,12,0),dt.datetime(2020,3,20,0,0)]
    sun=local_solar_cos(test,0,0)
    assert sun[0]>0.95 and sun[1]<-0.95
    x=physics(np.array([25.,25.,25.]),np.array([100.,100.,100.]),
              np.array([0.01,-0.01,0.05]))
    assert x["SH_negative_records"]==1
    assert x["SH_above_1p05_qsat_records"]==1
    assert good(np.array([np.nan,-9999.,0.,1.])).tolist()==[False,False,True,True]
    print("STAGE09 SELF-TEST PASS: equinox solar geometry, saturation humidity, masked source values; NO SOURCE WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        self_test()
        return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--stage07",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    root=a.root.resolve()
    out=a.out.resolve()
    if out.exists() or a.out.is_symlink() or root in out.parents or out==root:
        raise ValueError("Use an unused output folder outside source trees")
    manifest_check(a.manifest)
    years=load_years(a.stage07/"stage07_year_status.tsv")
    results=[]
    annual=[]
    for site,cfg in CASES.items():
        record,sub=inspect_file(root,site,cfg,years)
        results.append(record)
        annual.extend(sub)
        print("SOLAR",site,record["clock_hypothesis_verdict"],
              "SCORES",record["candidate_solar_scores_best_by_clock_offset"],
              "PHYSICAL_SH_gt1p05",sum(x["physical_SH_supersaturation_gt_105pct"] for x in sub))
    out.mkdir(parents=True)
    report={
        "stage":"OzFlux Stage09 first-cohort solar/time/physics",
        "source_read_only":True,"science_approval":False,
        "number_of_sites":len(results),
        "no_NetCDF_created":True,"no_DATM_or_Slurm":True,
        "native_clock_test_hypotheses":"UTC label vs fixed NT local UTC+09:30; interval shifts exploratory only",
        "science_gate_remaining":["verify source time metadata and timestamp interval semantics",
          "confirm solar hypothesis independently","confirm Precip units per timestep",
          "confirm sensor measurement height for ZBOT","verify PFT soil surface and prescribed simulation periods"],
        "sites":results,
        "annual":annual,
    }
    (out/"stage09_source_time_solar_physics.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    table(out/"stage09_year_physics.tsv",annual)
    print("STAGE09 AUDITED",len(results),"/2; NATIVE_YEAR_RECORDS",len(annual))
    print("REPORT_DIR",out)
    print("NO SOURCE EDITS; NO TIME TRANSFORM APPROVED; NO FORCING GENERATED")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

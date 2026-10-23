#!/usr/bin/env python3
"""Stage19: READ-ONLY ERA5 dewpoint sensitivity audit for ALL 4,884 Stage11 targets.

Use the 5 hash-verified Stage15 site-years and 34 verified Stage18 grid-years
(42 site-years; 38 unique ERA5 grid-years, with ICh/ICt shared). Verify the
unchanged original tower meteorology, Stage11/17 plans and all CDS receipts.
Convert tower-local STANDARD timestamps to UTC, interpolate hourly ERA5 RH
to half-hours, and derive review-only VPD/QBOT at Stage11's retained tower T/P.

NO observations are invented; NO original Stage11 HOLD is overridden;
NO scientific approval, DATM, source forcing, CIME, or Slurm modification.
US-Ho1 UTC-5 remains PROVISIONAL until independent release BADM confirmation.
RH saturation formula is OVER WATER: sub-zero records require further review.
--check makes no files; --write-report writes only isolated HOME CSV/JSON reports.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
import xarray as xr

BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE11=BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
STAGE13=Path.home()/"AmeriFlux_Batch02_stage13_plan_20261022T023406Z_7614f826"/"request_plan.json"
STAGE15=Path.home()/"AmeriFlux_Batch02_ERA5_five_one_year_controls"
STAGE17=Path.home()/"AmeriFlux_Batch02_stage17_anomaly_year_plan_20261022T034021Z_5704060a"/"CDS_anomaly_site_year_plan.json"
STAGE18=Path.home()/"AmeriFlux_Batch02_ERA5_missing_grid_years"
SHA13="0785bb8b85b5e8c9fee7b64d6f63016e58e12db03e31cf53c20e265e803f9523"
SHA17="84f680fb67030d374bb8a02abd4fce5a4a2c5d4abe7c59a30acf7bb5948488d4"
OFFSETS={"US-EML":-9,"US-GLE":-7,"US-Ho1":-5,"US-ICh":-9,"US-ICt":-9}
FOCUS={"US-EML":2009,"US-GLE":2005,"US-Ho1":1996,"US-ICh":2007,"US-ICt":2007}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def require_marker(directory,name):
    if not (directory/name).is_file():
        raise ValueError("Missing review-only marker: "+str(directory/name))

def es(t):
    return 6.112*np.exp(17.67*np.asarray(t,dtype=float)/
                        (np.asarray(t,dtype=float)+243.5)) # hPa, over WATER

def num(col):
    a=pd.to_numeric(col,errors="coerce")
    return a.mask((a<=-9990)|~np.isfinite(a))

def parse_local(col):
    return pd.to_datetime(col.astype(str).str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M",errors="raise")

def key(row):
    return (float(row["ERA_grid_lat_expected"]),
            float(row["ERA_grid_lon_expected"]),int(row["year"]))

def folder(key_):
    la,lo,yr=key_
    return f"ERA5_{yr}_lat{la:+07.2f}_lon{lo:+08.2f}"

def check_offset(primary,site):
    bifs=sorted(primary.parent.glob("*_BIF_*.csv"))
    if site=="US-Ho1":
        if bifs:
            raise ValueError("US-Ho1 release BIF appeared: verify UTC_OFFSET first")
        return "PROVISIONAL_US_Ho1_UTC_MINUS_5_BADM_PENDING"
    if len(bifs)!=1:raise ValueError("Exactly one release BIF required: "+site)
    matches=[]
    with bifs[0].open(encoding="utf-8-sig",newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("VARIABLE","").strip().upper()=="UTC_OFFSET":
                if row.get("SITE_ID","").strip() not in ("",site):
                    raise ValueError("BIF site mismatch: "+site)
                matches.append(float(row["DATAVALUE"]))
    if matches!=[OFFSETS[site]]:
        raise ValueError("BIF offset mismatch: "+site)
    return "ORIGINAL_RELEASE_BIF_CONFIRMED"

def checked_receipt(path,scope,expected_site,year,grid,plan_sha):
    r=json.loads(path.read_text())
    if scope=="15":
        if r.get("site")!=expected_site or r.get("year")!=year or \
           r.get("stage13_plan_sha256")!=SHA13 or r.get("science_approval") is not False:
            raise ValueError("Invalid Stage15 receipt metadata: "+str(path))
    else:
        if r.get("schema")!="STAGE18_VERIFIED_GRIDYEAR_v1" or \
           r.get("stage17_plan_sha256")!=plan_sha or \
           tuple(r.get("grid_year_key",[]))!=grid or \
           r.get("science_approved") is not False:
            raise ValueError("Invalid Stage18 receipt metadata: "+str(path))
    for name,checksum in (("netcdf_path","netcdf_sha256"),
                           ("original_payload_path","original_payload_sha256")):
        f=Path(r[name]).resolve(strict=True)
        home=STAGE15 if scope=="15" else STAGE18
        if home.resolve() not in f.parents or sha(f)!=r[checksum]:
            raise ValueError("CDS original or NetCDF SHA256 differs: "+str(f))
    return r

def read_era(path,yr,grid,cache):
    f=str(path)
    if f in cache:return cache[f]
    with xr.open_dataset(path,engine="netcdf4") as ds:
        if set(ds.data_vars)!={"t2m","d2m","sp"}:
            raise ValueError("ERA5 variable list changed: "+f)
        for var,unit in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if ds[var].attrs.get("units")!=unit or \
               tuple(ds[var].dims)!=("valid_time",):
                raise ValueError("ERA5 variable units/dims changed: "+f)
        times=pd.to_datetime(ds.valid_time.values,utc=True).tz_localize(None)
        t=np.asarray(ds.t2m.values,float)-273.15
        d=np.asarray(ds.d2m.values,float)-273.15
        p=np.asarray(ds.sp.values,float)
        lat=float(np.ravel(ds.latitude.values)[0])
        lon=float(np.ravel(ds.longitude.values)[0])
    exp=pd.date_range(f"{yr-1}-12-29",f"{yr+1}-01-03 23:00",freq="h")
    if not np.array_equal(times.values,exp.values) or \
       abs(lat-grid[0])>.001 or abs(lon-grid[1])>.001:
        raise ValueError("ERA5 UTC hourly calendar or grid incorrect: "+f)
    if not (np.isfinite(t).all() and np.isfinite(d).all() and np.isfinite(p).all()):
        raise ValueError("ERA5 contains NaN/Inf: "+f)
    with np.errstate(all="ignore"):
        rh=100*es(d)/es(t)
    if not (np.isfinite(rh)&(rh>0)&(rh<=100.05)).all():
        raise ValueError("ERA5 water RH numerical screen failed: "+f)
    data=(times,np.asarray(t),np.asarray(d),np.asarray(p),np.asarray(rh))
    cache[f]=data
    return data

def tower_source(path):
    header=set(pd.read_csv(path,nrows=0).columns)
    required={"TIMESTAMP_START","TA_F","PA_F","VPD_F"}
    if not required.issubset(header):
        raise ValueError("Original meteorology missing: "+str(required-header))
    fields=sorted(required|({"TA_F_QC","VPD_F_QC","RH","RH_QC"}&header))
    a=pd.read_csv(path,usecols=fields,dtype={"TIMESTAMP_START":str})
    a["local"]=parse_local(a.TIMESTAMP_START)
    if a.local.duplicated().any():
        raise ValueError("Original tower source duplicates native time")
    for col in fields:
        if col!="TIMESTAMP_START":a[col]=num(a[col])
    for col in ("TA_F_QC","VPD_F_QC","RH","RH_QC"):
        if col not in a:a[col]=np.nan
    a.sort_values("local",inplace=True)
    return a

def select_native(a,year):
    part=a.loc[a.local.dt.year.eq(year)].copy()
    part=part.loc[~(part.local.dt.month.eq(2)&part.local.dt.day.eq(29))]
    full=pd.date_range(f"{year}-01-01",f"{year+1}-01-01",
                       freq="30min",inclusive="left")
    full=full[~((full.month==2)&(full.day==29))]
    if len(part)!=17520 or len(full)!=17520 or \
       not np.array_equal(part.local.values,full.values):
        raise ValueError("Original tower year incomplete 17,520-row NO_LEAP: "+str(year))
    return part

def audit_year(row,pp,a,era_path,cache,offset_evidence):
    site=row["site"]; year=int(row["year"])
    rr=pp.loc[pp.site.eq(site)&pp.year.eq(year)].copy()
    if len(rr)!=row["n_stage11_targets"]:
        raise ValueError("Stage11 target year count differs: "+site+" "+str(year))
    native=select_native(a,year)
    target=native.merge(rr,left_on="local",right_on="local",
                        how="inner",validate="one_to_one",suffixes=("","_stage11"))
    if len(target)!=len(rr):
        raise ValueError("Source tower/native timestamp join failed: "+site+" "+str(year))
    times,t,d,p,rh=read_era(era_path,year,key(row),cache)
    utc=target.local-pd.Timedelta(hours=OFFSETS[site])
    era_seconds=(times.astype("int64")//10**9).to_numpy(dtype=float)
    q_seconds=(utc.astype("int64")//10**9).to_numpy(dtype=float)
    if (q_seconds<era_seconds[0]).any() or (q_seconds>era_seconds[-1]).any():
        raise ValueError("ERA5 UTC buffer does not enclose all anomaly timestamps")
    if not np.isin(utc.dt.minute.to_numpy(),[0,30]).all():
        raise ValueError("Tower samples not on 30-minute clock")
    rh_from_hourly=np.interp(q_seconds,era_seconds,rh)
    era_t=np.interp(q_seconds,era_seconds,t)
    era_d=np.interp(q_seconds,era_seconds,d)
    era_pressure=np.interp(q_seconds,era_seconds,p)
    with np.errstate(all="ignore"):
        rh_interp_components=100*es(era_d)/es(era_t)
        temp=num(target.retained_TA_C).to_numpy(dtype=float)
        pressure_kpa=num(target.retained_PA_kPa).to_numpy(dtype=float)
        sat=es(temp)
        vapor=sat*rh_from_hourly/100
        vpd=sat-vapor
        specific=.622*vapor*100/(pressure_kpa*1000-.378*vapor*100)
        original_rh=100*(1-target.VPD_F.to_numpy(dtype=float)/
                          es(target.TA_F.to_numpy(dtype=float)))
        analogue=num(target.proposed_VPD_hPa).to_numpy(dtype=float)
    numerical=(np.isfinite(temp)&np.isfinite(pressure_kpa)&
               (pressure_kpa>49)&(pressure_kpa<111)&
               np.isfinite(vpd)&(vpd>=-.005)&
               np.isfinite(specific)&(specific>0)&(specific<.08)&
               np.isfinite(rh_from_hourly)&(rh_from_hourly>0)&
               (rh_from_hourly<=100.05))
    valid_qc0=(native.TA_F_QC.eq(0)&native.VPD_F_QC.eq(0)&
               np.isfinite(native.TA_F)&np.isfinite(native.VPD_F))
    with np.errstate(all="ignore"):
        derived=100*(1-native.VPD_F/es(native.TA_F))
    valid_qc0 &= np.isfinite(derived)&(derived>0)&(derived<=100.05)
    good_times=(native.loc[valid_qc0,"local"].astype("int64")//10**9).to_numpy()
    secs=(target.local.astype("int64")//10**9).to_numpy()
    near=np.searchsorted(good_times,secs+86400,side="right")-np.searchsorted(
        good_times,secs-86400,side="left")
    if (near<0).any():raise ValueError("Invalid QC0 neighbour counts")
    same=np.isclose(target.TA_F.to_numpy(dtype=float),temp,
                    equal_nan=True,atol=1e-8,rtol=0)
    target["site"]=site
    target["year"]=year
    target["era5_utc"]=utc.astype(str)
    target["UTC_offset_local_minus_UTC"]=OFFSETS[site]
    target["UTC_offset_evidence"]=offset_evidence
    target["ERA5_grid_lat"]=key(row)[0]
    target["ERA5_grid_lon"]=key(row)[1]
    target["ERA5_temporal_method"]=np.where(
        utc.dt.minute.eq(0),"EXACT_HOURLY","LINEAR_INTERPOLATION_HALFHOUR")
    target["ERA5_RH_water_pct"]=rh_from_hourly
    target["ERA5_T2M_C"]=era_t
    target["ERA5_Td2M_C"]=era_d
    target["ERA5_surface_P_Pa"]=era_pressure
    target["ERA5_RH_water_interp_components_pct"]=rh_interp_components
    target["ERA5_RH_method_difference_pct"]=rh_from_hourly-rh_interp_components
    target["sensitivity_VPD_hPa"]=vpd
    target["sensitivity_QBOT_kgkg"]=specific
    target["Stage11_minus_ERA5_VPD_hPa"]=analogue-vpd
    target["raw_tower_VPD_implied_RH_pct"]=original_rh
    target["raw_tower_T_equals_Stage11_retained_T"]=same
    target["nearby_QC0_T_and_VPD_24h_n"]=near
    target["sensitivity_numeric_valid"]=numerical
    target["cold_water_saturation_caution"]=(
        (era_t<0)|(temp<0))
    target["original_Stage11_HOLD_preserved"]=target.decision.eq(
        "HOLD_NO_SUPPORTED_ANALOGUE")
    target["scientific_decision"]=np.where(
        numerical,"HOLD_INDEPENDENT_VALIDATION_REQUIRED",
        "HOLD_NUMERIC_OR_INPUT_INVALID")
    result=target[["site","year","local","era5_utc","decision",
        "UTC_offset_local_minus_UTC","UTC_offset_evidence",
        "ERA5_grid_lat","ERA5_grid_lon","ERA5_temporal_method",
        "retained_TA_C","retained_PA_kPa","TA_F","PA_F",
        "TA_F_QC","VPD_F","VPD_F_QC","RH","RH_QC",
        "proposed_VPD_hPa","donor_count",
        "ERA5_T2M_C","ERA5_Td2M_C","ERA5_surface_P_Pa",
        "ERA5_RH_water_pct","ERA5_RH_water_interp_components_pct",
        "ERA5_RH_method_difference_pct",
        "sensitivity_VPD_hPa","sensitivity_QBOT_kgkg",
        "Stage11_minus_ERA5_VPD_hPa","raw_tower_VPD_implied_RH_pct",
        "raw_tower_T_equals_Stage11_retained_T",
        "nearby_QC0_T_and_VPD_24h_n",
        "sensitivity_numeric_valid","cold_water_saturation_caution",
        "original_Stage11_HOLD_preserved","scientific_decision"]].copy()
    if result.local.duplicated().any():
        raise ValueError("Duplicate source-target local timestamp")
    summary=dict(site=site,year=year,n_targets=len(result),
        n_stage11_holds=int(result.original_Stage11_HOLD_preserved.sum()),
        n_numeric_invalid=int((~result.sensitivity_numeric_valid).sum()),
        n_halfhour_interpolated=int(result.ERA5_temporal_method.eq(
            "LINEAR_INTERPOLATION_HALFHOUR").sum()),
        n_subzero_water_formula_caution=int(result.cold_water_saturation_caution.sum()),
        n_retained_T_diff_raw=int((~result.raw_tower_T_equals_Stage11_retained_T).sum()),
        n_targets_with_neighbor_QC0_24h=int(
            result.nearby_QC0_T_and_VPD_24h_n.gt(0).sum()),
        original_QC0_T_VPD_in_whole_year=int(valid_qc0.sum()),
        median_abs_stage11_vs_ERA5_VPD_hPa=float(
            result.Stage11_minus_ERA5_VPD_hPa.abs().median())
            if result.Stage11_minus_ERA5_VPD_hPa.notna().any() else None,
        review_status="NO_APPROVAL")
    return result,summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--check",action="store_true")
    m.add_argument("--write-report",action="store_true")
    p.add_argument("--output-root",type=Path)
    args=p.parse_args()
    if sha(STAGE13)!=SHA13 or sha(STAGE17)!=SHA17:
        raise ValueError("Stage13 or Stage17 pinned plan SHA256 differs")
    for d,marker in ((STAGE11,"DO_NOT_USE_FOR_DATM_OR_SPINUP"),
                     (STAGE15,"STAGE15_PARTIAL_OR_COMPLETE_REVIEW_ONLY"),
                     (STAGE17.parent,"DO_NOT_USE_FOR_DATM_OR_SPINUP"),
                     (STAGE18,"DO_NOT_USE_FOR_DATM_OR_SPINUP")):
        require_marker(d,marker)
    info=json.loads(STAGE17.read_text())
    if info.get("schema")!="STAGE17_ANOMALY_YEAR_RETRIEVAL_PLAN_v1" or \
       info.get("science_status")!="ONLY_RETRIEVAL_PLAN_NO_DATM_APPROVAL":
        raise ValueError("Stage17 review plan contract changed")
    csvp=STAGE11/"cold_humidity_repair_proposals.csv"
    manifest=STAGE11/"manifest.json"
    if sha(csvp)!=info["original_stage11_sha256"] or \
       sha(manifest)!=info["original_stage11_manifest_sha256"]:
        raise ValueError("Stage11 pinned input changed")
    m11=json.loads(manifest.read_text())
    if m11.get("n_target_rows")!=4884 or \
       m11.get("scientific_status")!="HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Stage11 scope changed")
    config=json.loads((STAGE18/"config.json").read_text())
    if config.get("stage17_plan_sha256")!=SHA17 or \
       config.get("schema")!="STAGE18_GRID_YEAR_RETRIEVAL_v1":
        raise ValueError("Stage18 config does not belong to Stage17")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    source={r["site"]:r for r in m08["sites"]}
    proposals=pd.read_csv(csvp)
    if len(proposals)!=4884 or proposals.duplicated(["site","time"]).any():
        raise ValueError("Wrong Stage11 row count/duplicate")
    proposals["local"]=pd.to_datetime(proposals.time,errors="raise")
    proposals["year"]=proposals.local.dt.year
    if proposals.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE").sum()!=14 or \
       proposals.decision.eq("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED").sum()!=4870:
        raise ValueError("Original HOLD/provisional contract changed")
    planned=info["site_years"]
    if len(planned)!=42 or len({(r["site"],int(r["year"])) for r in planned})!=42:
        raise ValueError("Stage17 site-year plan changed")
    if sum(int(r["n_stage11_targets"]) for r in planned)!=4884 or \
       sum(int(r["n_stage11_holds"]) for r in planned)!=14:
        raise ValueError("Stage17 total changed")
    receipt_map={}
    checked_nc_sha={}
    for row in planned:
        site=row["site"];yr=int(row["year"]);grid=key(row)
        if row["existing_Stage15_verified"]:
            rp=STAGE15/f"{site}_{yr}"/"verified_receipt.json"
            if sha(rp)!=row["original_stage15_receipt"]["receipt_sha256"]:
                raise ValueError("Stage15 pinned receipt modified")
            receipt=checked_receipt(rp,"15",site,yr,grid,SHA17)
        else:
            rp=STAGE18/folder(grid)/"verified_receipt.json"
            receipt=checked_receipt(rp,"18",site,yr,grid,SHA17)
            if site not in receipt["all_sites_sharing_grid"]:
                raise ValueError("Missing site membership in grid-year receipt")
        nc=Path(receipt["netcdf_path"]).resolve()
        if str(nc) in checked_nc_sha and \
           checked_nc_sha[str(nc)]!=receipt["netcdf_sha256"]:
            raise ValueError("Conflicting shared grid-year checksums")
        checked_nc_sha[str(nc)]=receipt["netcdf_sha256"]
        receipt_map[(site,yr)]=(nc,grid)
    if len({grid for _,grid in receipt_map.values()})!=38 or \
       len(checked_nc_sha)!=38:
        raise ValueError("Expected exactly 38 unique verified ERA5 grid-year NetCDFs")
    original={}; offset_evidence={}
    for site in OFFSETS:
        path=Path(source[site]["primary"]).resolve(strict=True)
        if sha(path)!=m11["input_hashes"].get(str(path)):
            raise ValueError("Original source SHA256 changed: "+site)
        offset_evidence[site]=check_offset(path,site)
        original[site]=tower_source(path)
        print("SOURCE VERIFIED:",site,"time rows=",len(original[site]),
              "UTC offset evidence=",offset_evidence[site],flush=True)
    print("STAGE19 PREFLIGHT: 5 Stage15 + 34 Stage18 receipts, 38 distinct "
          "ERA5 grid-year files; original raw site files SHA256 verified.",flush=True)
    details=[];summaries=[];cache={}
    for row in sorted(planned,key=lambda x:(x["site"],x["year"])):
        site=row["site"];yr=int(row["year"])
        nc,_=receipt_map[(site,yr)]
        d,s=audit_year(row,proposals,original[site],nc,cache,offset_evidence[site])
        details.append(d);summaries.append(s)
        print("AUDIT",site,yr,"records=",len(d),
              "HOLDs=",s["n_stage11_holds"],
              "numeric_invalid=",s["n_numeric_invalid"],
              "freezing_caution=",s["n_subzero_water_formula_caution"],flush=True)
    result=pd.concat(details,ignore_index=True)
    siteyears=pd.DataFrame(summaries)
    if len(result)!=4884 or len(siteyears)!=42 or \
       result.duplicated(["site","local"]).any() or \
       int(result.original_Stage11_HOLD_preserved.sum())!=14 or \
       not result.scientific_decision.str.startswith("HOLD_").all():
        raise ValueError("Stage19 full-coverage HOLD audit contract failed")
    print("========== STAGE19 ALL-TARGET REVIEW SUMMARY ==========")
    print("TARGETS AUDITED:",len(result),"/4884; site-years:",len(siteyears),"/42")
    print("ORIGINAL HOLDS RETAINED:",int(result.original_Stage11_HOLD_preserved.sum()),"/14")
    print("NUMERICALLY INVALID CANDIDATES:",int((~result.sensitivity_numeric_valid).sum()))
    print("HALFHOURLY INTERPOLATED:",int(result.ERA5_temporal_method.eq(
          "LINEAR_INTERPOLATION_HALFHOUR").sum()))
    print("FREEZING WATER-SATURATION CAUTIONS:",
          int(result.cold_water_saturation_caution.sum()))
    print("US-Ho1 UTC-5 STILL PROVISIONAL; ICh/ICt same grid NOT independent.")
    print("SCIENTIFICALLY APPROVED:",0,"(by design, independent QC still required)")
    print(siteyears.groupby("site",as_index=False)[[
        "n_targets","n_stage11_holds","n_numeric_invalid",
        "n_subzero_water_formula_caution"]].sum().to_string(index=False))
    if args.check:
        print("CHECK ONLY: no CSV/JSON/forcing/netCDF written")
        return 0
    out=args.output_root.expanduser().resolve() if args.output_root else (
        Path.home()/("AmeriFlux_Batch02_stage19_full_dewpoint_audit_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]))
    protected=[BASE.resolve(),STAGE11.resolve(),STAGE15.resolve(),
               STAGE17.parent.resolve(),STAGE18.resolve(),STAGE13.parent.resolve()]
    if out.exists() or out.is_symlink() or \
       any(out==r or out in r.parents or r in out.parents for r in protected):
        raise ValueError("Output root exists, is symlink, or overlaps protected data")
    out.mkdir(parents=True,exist_ok=False)
    (out/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage19 row-wise numerical sensitivity only. NO scientific approval.\n")
    result.to_csv(out/"all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv",index=False)
    siteyears.to_csv(out/"42_site_year_review_summary.csv",index=False)
    receipt_hashes={
        str(STAGE15/f"{s}_{yr}"/"verified_receipt.json"):
            sha(STAGE15/f"{s}_{yr}"/"verified_receipt.json")
        for s,yr in FOCUS.items()}
    for r in planned:
        if not r["existing_Stage15_verified"]:
            f=STAGE18/folder(key(r))/"verified_receipt.json"
            receipt_hashes[str(f)]=sha(f)
    report=dict(schema="STAGE19_ALL_4884_ERA5_DIAGNOSTIC_v1",
        stage17_plan_sha256=SHA17,stage13_plan_sha256=SHA13,
        stage11_targets_sha256=sha(csvp),stage11_manifest_sha256=sha(manifest),
        script_sha256=sha(Path(__file__)),
        original_source_sha256={s:m11["input_hashes"][str(
            Path(source[s]["primary"]).resolve())] for s in OFFSETS},
        cds_receipt_sha256=receipt_hashes,verified_netcdf_sha256=checked_nc_sha,
        number_site_years=42,distinct_grid_years=38,n_target_rows=len(result),
        n_stage11_holds=14,n_numeric_invalid=int((~result.sensitivity_numeric_valid).sum()),
        n_half_hour_interpolations=int(result.ERA5_temporal_method.eq(
            "LINEAR_INTERPOLATION_HALFHOUR").sum()),
        n_freezing_water_saturation_cautions=int(result.cold_water_saturation_caution.sum()),
        UTC_offsets_local_minus_UTC=OFFSETS,
        US_Ho1_UTC_offset_status="PROVISIONAL_BADM_NOT_VERIFIED",
        ERA5_ICh_ICt_shared_grid_not_independent=True,
        scientifically_approved_rows=0,
        scientific_status="NUMERICAL_SENSITIVITY_ONLY_ALL_ROWS_HOLD",
        no_forcing_DATM_CIME_Slurm_changes=True)
    (out/"manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print("STAGE19 REPORT:",out,flush=True)
    print("READ-ONLY INPUTS; ONLY ISOLATED REVIEW OUTPUTS WRITTEN. NO FORCING APPROVED.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

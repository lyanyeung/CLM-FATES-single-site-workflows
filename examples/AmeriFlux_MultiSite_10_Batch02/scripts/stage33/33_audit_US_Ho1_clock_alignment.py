#!/usr/bin/env python3
"""Stage33: US-Ho1 UTC-offset sensitivity, independent source check only.

Uses EXACT Stage19 anomaly site-years with SHA-pinned ERA5 NetCDF and original
tower QC0 temperature. Tests hypothetical local-minus-UTC offsets -7..-3 h.
A minimum temperature error NEVER establishes a legitimate UTC_OFFSET.
No writes, downloads, forcing, DATM, CIME, or Slurm activity.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
import xarray as xr

H=Path.home()
B=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S11=B/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
S19=H/"AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
PLAN=H/"AmeriFlux_Batch02_stage17_anomaly_year_plan_20261022T034021Z_5704060a"/"CDS_anomaly_site_year_plan.json"
S15=H/"AmeriFlux_Batch02_ERA5_five_one_year_controls"
S18=H/"AmeriFlux_Batch02_ERA5_missing_grid_years"
OFFSETS=(-7,-6,-5,-4,-3)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def verify_ledger_file(path, ledger, label):
    """Verify the SAME file by its SHA256, even when /home and realpath differ.

    Stage19 stored receipt dictionary keys with Path.home() spelling *before*
    resolving symlinks, whereas Stage33 originally resolved before lookup.
    Identity aliases are permitted; mismatched hashes NEVER are.
    """
    actual_path=Path(path).resolve(strict=True)
    candidates=[]
    for name,expected in ledger.items():
        try:
            is_same=(Path(name).resolve(strict=True)==actual_path)
        except (FileNotFoundError,NotADirectoryError):
            is_same=False
        if is_same:
            candidates.append((name,expected))
    if not candidates:
        raise ValueError(label+" not found in Stage19 checksum ledger: "+
                         str(actual_path)+" (original spelling: "+str(path)+")")
    hashes={expected for _,expected in candidates}
    if len(hashes)!=1:
        raise ValueError(label+" has conflicting SHA256 for aliases: "+
                         str([name for name,_ in candidates]))
    expected=next(iter(hashes))
    actual=sha(actual_path)
    if actual!=expected:
        raise ValueError(label+" real SHA256 mismatch: "+str(actual_path)+
                         " expected="+expected+" actual="+actual)
    chosen=next((name for name,_ in candidates if name==str(path)),
                candidates[0][0])
    if chosen!=str(actual_path):
        print("LEDGER PATH ALIAS VERIFIED:",label,
              "manifest="+chosen,"resolved="+str(actual_path),flush=True)
    return actual_path

def epoch(times):
    return pd.DatetimeIndex(times).asi8.astype(float)/1e9

def esw(t):
    with np.errstate(all="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def numeric(series):
    x=pd.to_numeric(series,errors="coerce")
    return x.mask((x<=-9990)|~np.isfinite(x))

def raw_tower(path):
    a=pd.read_csv(path,usecols=["TIMESTAMP_START","TA_F","TA_F_QC"],
                  dtype={"TIMESTAMP_START":str})
    a["local"]=pd.to_datetime(a.TIMESTAMP_START.str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M",errors="raise")
    a["TA_F"]=numeric(a.TA_F)
    a["TA_F_QC"]=numeric(a.TA_F_QC)
    if a.local.duplicated().any() or not a.local.is_monotonic_increasing:
        raise ValueError("Raw tower timestamps not unique/increasing")
    return a[["local","TA_F","TA_F_QC"]]

def open_grid(path,year,lat,lon):
    with xr.open_dataset(path,engine="netcdf4") as ds:
        if set(ds.data_vars)!={"t2m","d2m","sp"}:raise ValueError("Unexpected ERA5 fields")
        for name,unit in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if ds[name].attrs.get("units")!=unit or tuple(ds[name].dims)!=("valid_time",):
                raise ValueError("ERA5 units/dims mismatch "+name)
        times=pd.to_datetime(ds.valid_time.values,utc=True).tz_localize(None)
        t=np.asarray(ds.t2m.values,float)-273.15
        d=np.asarray(ds.d2m.values,float)-273.15
        la=float(np.ravel(ds.latitude.values)[0])
        lo=float(np.ravel(ds.longitude.values)[0])
    ref=pd.date_range(f"{year-1}-12-29",f"{year+1}-01-03 23:00",freq="h")
    if not np.array_equal(times.values,ref.values) or \
       abs(la-lat)>.001 or abs(lo-lon)>.001:
        raise ValueError("ERA5 UTC time/grid mismatch")
    if not np.isfinite(t).all() or not np.isfinite(d).all():
        raise ValueError("Non-finite ERA5 T/Td")
    return epoch(times),t,d

def interp(local,off,utc,t):
    q=epoch(pd.DatetimeIndex(local)-pd.Timedelta(hours=off))
    if (q<utc[0]).any() or (q>utc[-1]).any():
        raise ValueError("Requested offset outside ERA5 UTC buffer")
    return np.interp(q,utc,t)

def sums(observed,pred,cohort,offset,year):
    err=np.asarray(pred,dtype=float)-np.asarray(observed,dtype=float)
    if not np.isfinite(err).all():raise ValueError("Non-finite paired error")
    return dict(cohort=cohort,offset=offset,year=year,n=len(err),
                sum_abs=float(np.abs(err).sum()),
                sum_error=float(err.sum()),
                sum_sq=float(np.square(err).sum()))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    p.add_argument("--stage11-root",type=Path,default=S11)
    p.add_argument("--stage19-root",type=Path,default=S19)
    p.add_argument("--stage17-plan",type=Path,default=PLAN)
    p.add_argument("--stage15-root",type=Path,default=S15)
    p.add_argument("--stage18-root",type=Path,default=S18)
    args=p.parse_args()
    s11,s19=args.stage11_root,args.stage19_root
    for folder in (s11,s19):
        if not (folder/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
            raise ValueError("Required scientific HOLD marker absent: "+str(folder))
    m11=json.loads((s11/"manifest.json").read_text())
    m19=json.loads((s19/"manifest.json").read_text())
    if m19.get("n_target_rows")!=4884 or m19.get("scientifically_approved_rows")!=0:
        raise ValueError("Stage19 original HOLD scope differs")
    if m19.get("US_Ho1_UTC_offset_status")!="PROVISIONAL_BADM_NOT_VERIFIED" or \
       m19.get("UTC_offsets_local_minus_UTC",{}).get("US-Ho1")!=-5:
        raise ValueError("Nominal US-Ho1 offset changed; stop for metadata review")
    if sha(args.stage17_plan)!=m19["stage17_plan_sha256"]:
        raise ValueError("Stage17 plan SHA256 mismatch")
    plan=json.loads(args.stage17_plan.read_text())
    if plan.get("schema")!="STAGE17_ANOMALY_YEAR_RETRIEVAL_PLAN_v1":
        raise ValueError("Unexpected Stage17 plan schema")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    entry=[a for a in m08["sites"] if a["site"]=="US-Ho1"]
    if len(entry)!=1:raise ValueError("Missing original US-Ho1 release")
    source=Path(entry[0]["primary"]).resolve(strict=True)
    if sha(source)!=m19["original_source_sha256"]["US-Ho1"] or \
       m11["input_hashes"].get(str(source))!=m19["original_source_sha256"]["US-Ho1"]:
        raise ValueError("US-Ho1 source checksum mismatch")
    if list(source.parent.glob("*_BIF_*.csv")):
        raise ValueError("US-Ho1 release BIF found; check published clock metadata first")
    held_all=pd.read_csv(s19/"all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv",
         usecols=["site","local","ERA5_T2M_C","ERA5_Td2M_C","retained_TA_C","TA_F_QC"],
         parse_dates=["local"])
    held=held_all.loc[held_all.site.eq("US-Ho1")].copy()
    if len(held)!=917 or held.local.duplicated().any():
        raise ValueError("Stage19 held-site target count changed")
    years=sorted((r for r in plan["site_years"] if r["site"]=="US-Ho1"),
                 key=lambda r:int(r["year"]))
    if not years or sum(int(r["n_stage11_targets"]) for r in years)!=917 or \
       {int(r["year"]) for r in years}!=set(held.local.dt.year):
        raise ValueError("Stage17/19 site-year mismatch")
    receipt_rows=[]
    for r in years:
        y=int(r["year"])
        lat=float(r["ERA_grid_lat_expected"])
        lon=float(r["ERA_grid_lon_expected"])
        if r["existing_Stage15_verified"]:
            path=args.stage15_root/f"US-Ho1_{y}"/"verified_receipt.json"
        else:
            path=args.stage18_root/f"ERA5_{y}_lat{lat:+07.2f}_lon{lon:+08.2f}"/"verified_receipt.json"
        path=verify_ledger_file(path,m19["cds_receipt_sha256"],
                                "Stage19 receipt for US-Ho1 "+str(y))
        obj=json.loads(path.read_text())
        nc=verify_ledger_file(
            obj["netcdf_path"],m19["verified_netcdf_sha256"],
            "Stage19 ERA5 NetCDF for US-Ho1 "+str(y))
        if sha(nc)!=obj["netcdf_sha256"]:
            raise ValueError("Receipt-pinned ERA5 NetCDF SHA256 mismatch: "+str(nc))
        group=args.stage15_root.resolve() if r["existing_Stage15_verified"] else args.stage18_root.resolve()
        if group not in nc.parents:raise ValueError("ERA5 path escaped source group")
        if r["existing_Stage15_verified"]:
            if obj.get("site")!="US-Ho1" or int(obj.get("year",-1))!=y:
                raise ValueError("Stage15 receipt site/year mismatch")
        else:
            if tuple(obj.get("grid_year_key",[]))!=(lat,lon,y) or \
               "US-Ho1" not in obj.get("all_sites_sharing_grid",[]):
                raise ValueError("Stage18 receipt grid-year/source mismatch")
        receipt_rows.append((y,lat,lon,nc,int(r["n_stage11_targets"])))
        print("SOURCE ERA5 VERIFIED",y,nc.name,flush=True)
    print("STAGE33 PREFLIGHT: 917 held US-Ho1 rows;",
          len(receipt_rows),"pinned ERA5 grid-years; source hashes valid")
    print("US-Ho1 FULLSET BIF absent. UTC-5 PROVISIONAL.")
    if args.check:
        print("CHECK ONLY | zero writes / zero model jobs")
        return

    raw=raw_tower(source)
    records=[]
    negative={o:0 for o in OFFSETS}
    nominal_delta=[]
    held_qc0_count=0
    for yr,lat,lon,nc,ntarget in receipt_rows:
        utc,t,d=open_grid(nc,yr,lat,lon)
        row=raw.loc[raw.local.dt.year.eq(yr)]
        row=row.loc[~(row.local.dt.month.eq(2)&row.local.dt.day.eq(29))]
        ref=pd.date_range(f"{yr}-01-01",f"{yr+1}-01-01",freq="30min",inclusive="left")
        ref=ref[~((ref.month==2)&(ref.day==29))]
        if len(row)!=17520 or len(ref)!=17520 or \
           not np.array_equal(row.local.to_numpy(),ref.to_numpy()):
            raise ValueError("Tower source NO_LEAP native grid failed for "+str(yr))
        observed=row.loc[row.TA_F_QC.eq(0)&row.TA_F.notna()]
        target=held.loc[held.local.dt.year.eq(yr)]
        if len(target)!=ntarget:raise ValueError("Stage17 target-year count differs")
        obs_held=target.merge(observed[["local","TA_F"]],on="local",
                              how="inner",validate="one_to_one")
        held_qc0_count+=len(obs_held)
        winter=observed.local.dt.month.isin([12,1,2,3]).to_numpy()
        for offset in OFFSETS:
            a=interp(observed.local,offset,utc,t)
            b=interp(obs_held.local,offset,utc,t)
            records.append(sums(observed.TA_F,a,"ALL_QC0",offset,yr))
            records.append(sums(observed.TA_F.to_numpy()[winter],a[winter],"WINTER_QC0",offset,yr))
            records.append(sums(obs_held.TA_F,b,"HELD_QC0",offset,yr))
            ea=interp(target.local,offset,utc,t)
            ed=interp(target.local,offset,utc,d)
            negative[offset]+=int((esw(target.retained_TA_C.to_numpy(float))-esw(ed)<-.005).sum())
            if offset==-5:
                nominal_delta.extend(np.maximum(
                    np.abs(ea-target.ERA5_T2M_C.to_numpy(float)),
                    np.abs(ed-target.ERA5_Td2M_C.to_numpy(float))).tolist())
        print("YEAR",yr,"QC0 source",len(observed),"QC0 held",len(obs_held),
              "target",len(target),flush=True)
    if held_qc0_count!=216 or not nominal_delta or max(nominal_delta)>1e-5:
        raise ValueError("Historical Stage19/30 baseline not reproduced")
    if negative[-5]!=425:
        raise ValueError("Stage32 nominal 425 negative Td-transfer cases not reproduced")
    result=pd.DataFrame(records)
    print("\nSTAGE33 | QC0 SOURCE-TEMPERATURE OFFSET COMPARISON")
    for cohort in ("ALL_QC0","WINTER_QC0","HELD_QC0"):
        print("\n"+cohort)
        for off in OFFSETS:
            part=result.loc[result.cohort.eq(cohort)&result.offset.eq(off)]
            n=int(part.n.sum())
            if n==0:print(off,"no observations");continue
            print("local_minus_UTC",off,"hours","n",n,
                  "MAE",round(part.sum_abs.sum()/n,3),
                  "bias",round(part.sum_error.sum()/n,3),
                  "RMSE",round(np.sqrt(part.sum_sq.sum()/n),3))
    print("\nSTAGE33 | NEGATIVE Td-TRANSFER VPD AMONG THE 917 HELD RECORDS")
    for off in OFFSETS:print("local_minus_UTC",off,"negative VPD",negative[off])
    print("\nSTAGE33 | YEARLY WINTER QC0 ERROR (MINIMUM IS NOT CLOCK VALIDATION)")
    subset=result.loc[result.cohort.eq("WINTER_QC0")]
    for year,g in subset.groupby("year"):
        base=g.loc[g.offset.eq(-5)].iloc[0]
        if base.n<48:print(year,"winter QC0 n",int(base.n),"INSUFFICIENT");continue
        best=g.assign(mae=g.sum_abs/g.n).sort_values("mae").iloc[0]
        print(year,"winter n",int(base.n),
              "nominal_MAE",round(base.sum_abs/base.n,3),
              "min_sample_MAE_offset",int(best.offset),
              "min_sample_MAE",round(best.mae,3))
    print("\nOFFICIAL SITE REFERENCE: https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1")
    print("Site location 45.2040 N, -68.7402 E/W; elevation 60m")
    print("NO INDEPENDENT UTC_OFFSET/BADM OR ERA5 GRID ELEVATION CERTIFICATION")
    print("ALL 917 US-Ho1 / ALL 4,884 Batch02 SCIENTIFIC HOLD")
    print("NO WRITES, CDS DOWNLOADS, FORCING, DATM, CIME OR SLURM CHANGES")

if __name__=="__main__":
    main()

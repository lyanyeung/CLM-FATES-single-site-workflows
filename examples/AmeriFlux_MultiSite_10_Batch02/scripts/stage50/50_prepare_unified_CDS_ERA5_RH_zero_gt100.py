#!/usr/bin/env python3
"""Batch02 Stage50: unified external CDS ERA5 RH candidates for 444 raw RH defects.

Scope is ONLY raw original RH=0 or >100%: Ha1=398, Ho2=7, ICh=9, ICt=30.
The algorithm uses one product, reanalysis-era5-single-levels-timeseries,
and t2m/d2m/sp from one exact ERA5 UTC time-series grid-year (never
in-package FLUXNET *_ERA). Hourly ERA5 water RH is linearly interpolated
to native tower start timestamps using the original release BIF UTC_OFFSET.
RH, VPD and QBOT candidate columns are generated together. Never overwrite
a raw CSV, Stage07/08 output, DATM, NetCDF source, Slurm/CIME/model input.

Modes: --self-test; --plan; --fetch [--max-new N]; --build.
--fetch uses CDS credentials/license already set up on the operator host,
or reuses SHA256-checked Stage15/18 time-series receipts. Network activity
occurs ONLY in --fetch. Missing/ambiguous BIF or ERA evidence fails closed.
--build yields a sparse patch ledger and science HOLDs, not runnable forcing.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile
from uuid import uuid4

import numpy as np
import pandas as pd

SITES=("US-Ha1","US-Ho2","US-ICh","US-ICt")
EXPECTED={"US-Ha1":398,"US-Ho2":7,"US-ICh":9,"US-ICt":30}
DATASET="reanalysis-era5-single-levels-timeseries"
VARIABLES=["2m_temperature","2m_dewpoint_temperature","surface_pressure"]
EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
INVENTORY=EXP/"reports/stage04b_met_20261021T233344Z_ff3b9f20/source_inventory.json"
STAGE49=EXP/"reports/stage49_original_humidity_review_20261024T090809Z_eac34e13"
CACHE=Path.home()/"AmeriFlux_Batch02_Stage50_external_CDS_ERA5"
STAGE15=Path.home()/"AmeriFlux_Batch02_ERA5_five_one_year_controls"
STAGE18=Path.home()/"AmeriFlux_Batch02_ERA5_missing_grid_years"
OUT=EXP/"reports"
MAX_NC=128*1024*1024

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda:f.read(1<<20),b""):h.update(data)
    return h.hexdigest()

def es(t):
    a=np.asarray(t,dtype=float)
    return 6.112*np.exp(17.67*a/(a+243.5))

def grid_of(lat,lon):
    return (round(float(lat)*4)/4,round(float(lon)*4)/4)

def grid_name(k):
    la,lo,y=k
    return "ERA5_%04d_lat%+07.2f_lon%+08.2f"%(y,la,lo)

def site_bif(spec):
    site=spec["site"]
    src=Path(spec["file"])
    matches=list(src.parent.glob("*_BIF_*.csv"))
    if len(matches)!=1:
        raise ValueError(site+": require ONE release BIF for station coordinate and UTC offset")
    bif=matches[0]
    if bif.is_symlink():raise ValueError("Refuse symlink BIF")
    values=defaultdict(set)
    with bif.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        if not {"VARIABLE","DATAVALUE"}.issubset(r.fieldnames or []):
            raise ValueError("BIF schema missing")
        for item in r:
            if (item.get("SITE_ID") or "").strip() not in ("",site):
                raise ValueError("Wrong BIF SITE_ID")
            k=(item.get("VARIABLE") or "").strip().upper()
            if k not in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET"):continue
            raw=(item.get("DATAVALUE") or "").strip()
            if raw and raw!="-9999":values[k].add(float(raw))
    if any(len(values[k])!=1 for k in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET")):
        raise ValueError(site+": BIF coordinate/UTC_OFFSET missing or ambiguous")
    lat=next(iter(values["LOCATION_LAT"]))
    lon=next(iter(values["LOCATION_LONG"]))
    offset=next(iter(values["UTC_OFFSET"]))
    if not (-90<=lat<=90 and -180<=lon<=180 and -12<=offset<=14
            and offset*2==int(offset*2)):
        raise ValueError(site+": invalid BIF coordinate/UTC_OFFSET")
    return dict(site=site,lat=lat,lon=lon,utc_offset=offset,
                grid=grid_of(lat,lon),bif=str(bif),bif_sha256=sha(bif),
                offset_provenance="ORIGINAL_RELEASE_BIF")

def load_targets(stage49,inventory):
    if (stage49/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage49 incomplete")
    p=stage49/"provenance_and_hold.json"
    proof=json.loads(p.read_text())
    if proof.get("status")!="REVIEW_ONLY_NO_DATM_APPROVAL":
        raise ValueError("Stage49 not completed or scientific status changed")
    if proof.get("inventory_sha256")!=sha(inventory):
        raise ValueError("Stage49 inventory SHA changed")
    entries=json.loads(inventory.read_text()).get("completed",[])
    if len(entries)!=20:raise ValueError("Wrong original Stage04b inventory")
    specs={}
    for site in SITES:
        sources=[x for x in entries if x["site"]==site and
                 not x["source"].startswith("ERA5")]
        if len(sources)!=1:raise ValueError("Ambiguous original primary "+site)
        spec=sources[0]
        if sha(spec["file"])!=spec["sha256"] or (
                proof.get("primary_sha256_by_site",{}).get(site)!=spec["sha256"]):
            raise ValueError("Original primary changed: "+site)
        specs[site]=spec
    rows=pd.read_csv(stage49/"original_humidity_event_review.csv",
                     dtype={"timestamp_start":str,"timestamp_end":str,"source_sha256":str})
    for c in ("site","source","source_csv_row","timestamp_start",
              "timestamp_end","RH_raw_pct","TA_C","PA_kPa","TA_original_QC"):
        if c not in rows:raise ValueError("Stage49 event column missing: "+c)
    selected=rows[rows.site.isin(SITES)].copy()
    selected["RH_raw_pct"]=pd.to_numeric(selected.RH_raw_pct,errors="coerce")
    selected=selected[(selected.RH_raw_pct==0)|(selected.RH_raw_pct>100)].copy()
    counts=selected.groupby("site").size().to_dict()
    raw_zero=int((selected.RH_raw_pct==0).sum())
    raw_over=int((selected.RH_raw_pct>100).sum())
    if counts!=EXPECTED or len(selected)!=444 or (raw_zero,raw_over)!=(39,405):
        raise ValueError("Expected 444 original RH targets (39 zero, 405 >100): "+
                         str((counts,raw_zero,raw_over)))
    if selected.duplicated(["site","timestamp_start"]).any():
        raise ValueError("Duplicate original site/time target")
    for site,part in selected.groupby("site"):
        if not part.source_sha256.eq(specs[site]["sha256"]).all():
            raise ValueError("Stage49 original primary SHA identity mismatch")
        if not part.source.eq(specs[site]["source"]).all():
            raise ValueError("Stage49 original source type mismatch")
    selected["local_time"]=pd.to_datetime(
        selected.timestamp_start,format="%Y%m%d%H%M",errors="raise")
    selected["year"]=selected.local_time.dt.year
    return selected, specs, dict(stage49_sha256=sha(stage49/"original_humidity_event_review.csv"),
                                 original_inventory_sha256=sha(inventory),
                                 stage49_provenance_sha256=sha(p))

def plan(targets,specs):
    siteinfo={site:site_bif(specs[site]) for site in SITES}
    rows=[]
    for (site,year),part in targets.groupby(["site","year"]):
        meta=siteinfo[site]
        grid=(meta["grid"][0],meta["grid"][1],int(year))
        rows.append((site,int(year),len(part),grid))
    rows.sort()
    return siteinfo, rows

def requests(allrows,meta):
    jobs={}
    for site,yr,n,k in allrows:
        if k not in jobs:
            jobs[k]=dict(representative_site=site,latitude=meta[site]["lat"],
                         longitude=meta[site]["lon"],sites=[])
        jobs[k]["sites"].append(site)
        # Multiple sites can reuse only an EXACT verified 0.25-degree grid.
        if grid_of(jobs[k]["latitude"],jobs[k]["longitude"]) != meta[site]["grid"]:
            raise ValueError("Incorrect shared-grid identity")
    return jobs

def verify_nc(path,year,grid):
    import xarray as xr
    with xr.open_dataset(path,engine="netcdf4") as ds:
        if set(ds.data_vars)!={"t2m","d2m","sp"}:
            raise ValueError("CDS dataset fields mismatch: "+str(path))
        for n,u in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if ds[n].attrs.get("units")!=u or tuple(ds[n].dims)!=("valid_time",):
                raise ValueError("CDS field units/dims mismatch "+n)
        times=pd.to_datetime(ds.valid_time.values,utc=True).tz_localize(None)
        expected=pd.date_range(f"{year-1}-12-29",
                               f"{year+1}-01-03 23:00",freq="h")
        if len(times)!=len(expected) or not np.array_equal(times.values,expected.values):
            raise ValueError("CDS full UTC buffered year incomplete "+str(path))
        lat=float(np.asarray(ds.latitude.values).ravel()[0])
        lon=float(np.asarray(ds.longitude.values).ravel()[0])
        if abs(lat-grid[0])>0.001 or abs(lon-grid[1])>0.001:
            raise ValueError("CDS grid coordinate mismatch")
        t=np.asarray(ds.t2m.values,float)-273.15
        td=np.asarray(ds.d2m.values,float)-273.15
        p=np.asarray(ds.sp.values,float)
    if not (np.isfinite(t).all() and np.isfinite(td).all()
            and np.isfinite(p).all() and ((t>-90)&(t<65)).all()
            and ((td>-100)&(td<65)).all() and ((p>49000)&(p<111000)).all()):
        raise ValueError("CDS numeric range failure")
    rh=100*es(td)/es(t)
    if not (np.isfinite(rh)&(rh>0)&(rh<=100.05)).all():
        raise ValueError("CDS physical RH failed")
    return times,t,td,p,rh

def read_receipt(path,key,site_membership=None):
    if not path.is_file():return None
    r=json.loads(path.read_text())
    # Fail closed on source or scope mismatch; an unverified NetCDF may not
    # be supplied as an ad-hoc command argument.
    if r.get("dataset",r.get("CDS_dataset"))!=DATASET:
        raise ValueError("Not the same CDS ERA5 dataset: "+str(path))
    if r.get("science_approval",r.get("science_approved")) is not False:
        raise ValueError("Unverified receipt state")
    if "grid_year_key" in r:
        if tuple(r["grid_year_key"])!=key:raise ValueError("CDS grid-year key mismatch")
        if r.get("schema") not in (
           "STAGE18_VERIFIED_GRIDYEAR_v1","STAGE50_VERIFIED_CDS_ERA5_GRIDYEAR_v1"):
            raise ValueError("Unknown CDS receipt schema")
        # The NetCDF grid and calendar are revalidated directly; Stage18
        # membership is the historic Stage17 target subset and must not
        # exclude a new site sharing exactly the same verified ERA5 grid.
        if r.get("schema")=="STAGE50_VERIFIED_CDS_ERA5_GRIDYEAR_v1" and not (
           set(site_membership or []) & set(r.get("sites",[]))):
            raise ValueError("Stage50 receipt site membership mismatch")
    elif "year" in r:
        if r["year"]!=key[2] or r.get("site") not in (site_membership or []):
            raise ValueError("Stage15 site/year mismatch")
    else:
        if tuple(r.get("grid_year_key",[]))!=key:raise ValueError("Stage50 key mismatch")
    for field,digest in (("original_payload_path","original_payload_sha256"),
                         ("netcdf_path","netcdf_sha256")):
        f=Path(r[field]).resolve(strict=True)
        if sha(f)!=r[digest]:raise ValueError("CDS source SHA256 mismatch "+str(f))
    nc=Path(r["netcdf_path"]).resolve()
    # Full NetCDF dimensions/times/grid values are checked in all modes.
    verify_nc(nc,key[2],key[:2])
    return r

def resolve_receipt(key,jobs,cache):
    folder=cache/grid_name(key)
    rfile=folder/"verified_receipt.json"
    if rfile.exists():
        return read_receipt(rfile,key,jobs[key]["sites"]),str(rfile)
    for site in jobs[key]["sites"]:
        old=STAGE15/f"{site}_{key[2]}"/"verified_receipt.json"
        if old.exists():
            return read_receipt(old,key,jobs[key]["sites"]),str(old)
    older=STAGE18/grid_name(key)/"verified_receipt.json"
    if older.exists():
        return read_receipt(older,key,jobs[key]["sites"]),str(older)
    return None,None

def request_payload(key,job,folder):
    import cdsapi
    req=dict(variable=VARIABLES,
             location=dict(latitude=job["latitude"],longitude=job["longitude"]),
             date=[f"{key[2]-1}-12-29",f"{key[2]+1}-01-03"],
             data_format="netcdf")
    target=folder/"original_CDS_payload"
    if target.exists():raise FileExistsError("Unverified pre-existing CDS payload")
    cdsapi.Client().retrieve(DATASET,req,str(target))
    return target,req

def extract(payload,folder):
    with payload.open("rb") as f:magic=f.read(8)
    if magic[:4] in (b"CDF\x01",b"CDF\x02",b"CDF\x05") or magic==b"\x89HDF\r\n\x1a\n":
        return payload
    if magic[:4]!=b"PK\x03\x04" or not zipfile.is_zipfile(payload):
        raise ValueError("CDS payload is not NetCDF or ZIP")
    with zipfile.ZipFile(payload) as z:
        members=[m for m in z.infolist() if not m.is_dir()]
        if len(members)!=1 or not 0<members[0].file_size<MAX_NC:
            raise ValueError("Unexpected CDS ZIP members")
        p=PurePosixPath(members[0].filename)
        if len(p.parts)!=1 or not p.name.endswith(".nc"):
            raise ValueError("Unsafe CDS ZIP member")
        out=folder/"era5_dewpoint_hourly_UTC.nc"
        with z.open(members[0]) as src,out.open("xb") as dst:
            shutil.copyfileobj(src,dst)
        if out.stat().st_size!=members[0].file_size:
            raise ValueError("Truncated CDS NetCDF extraction")
        return out

def candidate_rows(targets,siteinfo,jobs,receipts):
    cache={}
    for site,part in targets.groupby("site",sort=True):
        meta=siteinfo[site]
        for year,yearpart in part.groupby("year",sort=True):
            k=(*meta["grid"],int(year))
            receipt,_=receipts[k]
            nc=receipt["netcdf_path"]
            if nc not in cache:
                cache[nc]=verify_nc(nc,year,meta["grid"])
            times,t,td,p,rh=cache[nc]
            d=yearpart.copy()
            utc=d.local_time-pd.to_timedelta(meta["utc_offset"],unit="h")
            # No year rollover shortcuts: use real UTC instantaneous times.
            ts=times.view("int64")/1e9
            x=utc.astype("int64")/1e9
            if np.any(x<ts.min()) or np.any(x>ts.max()):
                raise ValueError("ERA5 UTC does not bracket native time")
            t_era=np.interp(x,ts,t);td_era=np.interp(x,ts,td)
            p_era=np.interp(x,ts,p);rh_era=np.interp(x,ts,rh)
            if np.any(~np.isfinite(rh_era)) or np.any((rh_era<=0)|(rh_era>100.05)):
                raise ValueError("ERA5 interpolated RH invalid")
            for i,(_,row) in enumerate(d.iterrows()):
                ta=float(row.TA_C);pak=float(row.PA_kPa)
                tq=pd.to_numeric(row.TA_original_QC,errors="coerce")
                r=float(rh_era[i])/100.
                valid=(np.isfinite(ta) and -80<ta<65 and
                       np.isfinite(pak) and 50<pak<110)
                vpd=q=np.nan
                if valid:
                    vap=float(es(ta))*r
                    vpd=float(es(ta))*(1-r)
                    den=pak*1000-.378*vap*100
                    q=.622*vap*100/den if den>0 else np.nan
                    valid=(np.isfinite(vpd) and vpd>=-.005 and
                           np.isfinite(q) and 0<q<.08)
                if not valid:
                    status="HOLD_INVALID_RETAINED_T_OR_PRESSURE"
                elif not np.isfinite(tq) or tq!=0 or abs(ta-t_era[i])>8:
                    status="MANUAL_JOINT_T_AND_HUMIDITY_REVIEW"
                elif row.RH_raw_pct>100:
                    status="CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE"
                else:
                    status="CANDIDATE_ONLY_REVIEW_ZERO_RH"
                # Note: no unconditional science approval from QC0 or ERA.
                yield dict(site=site,timestamp_start=row.timestamp_start,
                   timestamp_end=row.timestamp_end,
                   source_csv_row=int(row.source_csv_row),
                   source_sha256=row.source_sha256,
                   native_minutes=60 if site=="US-Ha1" else 30,
                   original_RH_pct=float(row.RH_raw_pct),
                   original_TA_C=ta,original_PA_kPa=pak,
                   original_VPD_hPa=row.VPD_hPa,
                   original_TA_QC=row.TA_original_QC,
                   local_minus_UTC_hours=meta["utc_offset"],
                   ERA5_UTC_time=str(utc.iloc[i]),
                   ERA5_grid_lat=meta["grid"][0],
                   ERA5_grid_lon=meta["grid"][1],
                   ERA5_dataset=DATASET,
                   ERA5_netcdf_sha256=receipt["netcdf_sha256"],
                   ERA5_receipt_file=receipts[k][1],
                   ERA5_interp="linear_of_hourly_water_RH",
                   ERA5_T2M_C=float(t_era[i]),
                   ERA5_TD2M_C=float(td_era[i]),
                   ERA5_surface_pressure_Pa=float(p_era[i]),
                   candidate_RH_pct=float(rh_era[i]),
                   candidate_VPD_hPa=vpd,
                   candidate_QBOT_kg_kg=q,
                   retained_T_minus_ERA5_T_C=ta-float(t_era[i]),
                   candidate_status=status,
                   approved_for_DATM=False)

def self_test():
    assert sum(EXPECTED.values())==444
    assert grid_of(44.12,-68.73)==(44.0,-68.75)
    assert grid_name((44.0,-68.75,2007))=="ERA5_2007_lat+044.00_lon-0068.75"
    assert abs(float(es(20))-23.3695)<.02
    t=pd.date_range("2007-01-01",periods=3,freq="h")
    x=(t.view("int64")/1e9)
    assert abs(np.interp((x[0]+x[1])/2,x,[40,60,80])-50)<1e-9
    print("STAGE50 SELF-TEST PASS | 444 target contract, grid/year, RH physics, hourly-HH interpolation")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    a=ap.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","plan","fetch","build"):
        a.add_argument("--"+opt,action="store_true")
    ap.add_argument("--stage49",type=Path,default=STAGE49)
    ap.add_argument("--inventory",type=Path,default=INVENTORY)
    ap.add_argument("--cache-root",type=Path,default=CACHE)
    ap.add_argument("--report-root",type=Path,default=OUT)
    ap.add_argument("--max-new",type=int,default=2)
    opt=ap.parse_args()
    if opt.self_test:
        self_test();return
    if opt.max_new<1:ap.error("--max-new must be >=1")
    targets,specs,pins=load_targets(opt.stage49,opt.inventory)
    meta,rows=plan(targets,specs)
    jobs=requests(rows,meta)
    print("STAGE50 RH_ZERO_OR_GT100 ORIGINAL TARGETS",len(targets))
    for site in SITES:
        print("STATION",site,"targets",EXPECTED[site],
              "BIF",meta[site]["lat"],meta[site]["lon"],
              "UTC_OFFSET",meta[site]["utc_offset"],
              "BIF_SHA256",meta[site]["bif_sha256"])
    print("CDS DATASET:",DATASET,"variables:",VARIABLES,
          "shared grid-years:",len(jobs))
    cache=opt.cache_root.expanduser().resolve()
    receipts={}
    missing=[]
    for k,info in sorted(jobs.items(),key=lambda x:(x[0][2],x[0][0],x[0][1])):
        r,path=resolve_receipt(k,jobs,cache)
        receipts[k]=(r,path)
        if r is None:missing.append(k)
        print("GRID-YEAR",grid_name(k),"sites",info["sites"],
              "status","VERIFIED_REUSE" if r else "CDS_DOWNLOAD_REQUIRED")
    if opt.plan:
        print("STAGE50 PLAN PASS | missing grid-years",len(missing),
              "| zero source/model writes")
        return
    if opt.fetch:
        if not missing:
            print("STAGE50 FETCH SKIPPED: all required receipts already verified");return
        cache.mkdir(parents=True,exist_ok=True)
        for k in missing[:opt.max_new]:
            folder=cache/grid_name(k)
            folder.mkdir(parents=True,exist_ok=True)
            marker=folder/"INCOMPLETE_DO_NOT_USE"
            if (folder/"verified_receipt.json").exists():
                raise ValueError("Receipt present but not accepted: "+str(folder))
            if not marker.exists():
                if any(folder.iterdir()):
                    raise ValueError("Unrecognized pre-existing CDS folder: "+str(folder))
                marker.write_text("CDS request pending independent verification.\n")
            if not marker.is_file():
                raise ValueError("Expected recovery marker absent")
            payload=folder/"original_CDS_payload"
            request=dict(variable=VARIABLES,
                location=dict(latitude=jobs[k]["latitude"],
                              longitude=jobs[k]["longitude"]),
                date=[f"{k[2]-1}-12-29",f"{k[2]+1}-01-03"],
                data_format="netcdf")
            if payload.is_file() and payload.stat().st_size>100:
                print("STAGE50 RECOVERING EXISTING CDS PAYLOAD",grid_name(k))
            elif payload.exists():
                raise ValueError("Incomplete CDS payload requires manual inspection: "+str(payload))
            else:
                payload,request=request_payload(k,jobs[k],folder)
            nc_file=folder/"era5_dewpoint_hourly_UTC.nc"
            nc=nc_file if nc_file.is_file() else extract(payload,folder)
            verify_nc(nc,k[2],k[:2])
            receipt=dict(schema="STAGE50_VERIFIED_CDS_ERA5_GRIDYEAR_v1",
                grid_year_key=list(k),dataset=DATASET,variables=VARIABLES,
                sites=jobs[k]["sites"],request=request,science_approved=False,
                original_payload_path=str(payload.resolve()),
                original_payload_sha256=sha(payload),
                netcdf_path=str(nc.resolve()),netcdf_sha256=sha(nc),
                no_model_approval=True)
            with (folder/"verified_receipt.json").open("x") as f:
                json.dump(receipt,f,indent=2);f.write("\n")
            marker.unlink()
            print("STAGE50 VERIFIED CDS",grid_name(k),"sha",receipt["netcdf_sha256"],flush=True)
        print("STAGE50 FETCH COMPLETE | rerun --plan then --fetch until missing=0")
        return
    if missing:
        raise ValueError("STAGE50 BUILD BLOCKED: missing "+str(len(missing))+
                         " grid-years; run --fetch with approved CDS credentials first")
    root=opt.report_root.expanduser().resolve()
    inputs=[Path(x["file"]).resolve() for x in specs.values()]
    if any(root==p or root in p.parents for p in inputs):
        raise ValueError("Output root overlaps input file")
    result=list(candidate_rows(targets,meta,jobs,receipts))
    if len(result)!=444 or Counter(x["site"] for x in result)!=Counter(EXPECTED):
        raise ValueError("Candidate target count mismatch")
    if any(not np.isfinite(x["candidate_RH_pct"]) for x in result):
        raise ValueError("ERA5 candidate RH missing")
    dest=root/("stage50_unified_external_ERA5_RH_"+datetime.now(timezone.utc).strftime(
               "%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    mark=dest/"INCOMPLETE_DO_NOT_USE"
    mark.write_text("Unverified candidate, not model-ready.\n")
    table=dest/"RH_zero_gt100_444_ERA5_candidate_patch.csv"
    pd.DataFrame(result).to_csv(table,index=False)
    if sha(opt.inventory)!=pins["original_inventory_sha256"] or \
       sha(opt.stage49/"original_humidity_event_review.csv")!=pins["stage49_sha256"]:
        raise ValueError("Stage49/input changed during candidate build")
    for s in SITES:
        if sha(specs[s]["file"])!=specs[s]["sha256"] or \
           sha(meta[s]["bif"])!=meta[s]["bif_sha256"]:
            raise ValueError("Original source or BIF changed during build")
    for k,(r,path) in receipts.items():
        read_receipt(Path(path),k,jobs[k]["sites"])
    counts=Counter(x["candidate_status"] for x in result)
    proof=dict(schema="STAGE50_444_EXTERNAL_CDS_ERA5_REVIEW_v1",
         dataset=DATASET,variables=VARIABLES,target_count=444,
         original_RH_eq0_count=39,original_RH_gt100_count=405,
         stage49_pins=pins,source_sha256={s:specs[s]["sha256"] for s in SITES},
         site_BIF=meta,CDS_receipts={grid_name(k):path for k,(r,path) in receipts.items()},
         statuses=dict(counts),patch_sha256=sha(table),
         approved_replacements=0,model_ready=False)
    (dest/"candidate_provenance.json").write_text(json.dumps(
        proof,indent=2,sort_keys=True)+"\n")
    mark.unlink()
    print("STAGE50 BUILD PASS | exactly 444 CDS ERA5 RH patch candidates",flush=True)
    print("REPORT",dest,flush=True)
    print("DECISIONS",dict(counts),flush=True)
    print("SCIENCE HOLD: no source / prior candidate / DATM / spinup modified")
if __name__=="__main__":
    main()

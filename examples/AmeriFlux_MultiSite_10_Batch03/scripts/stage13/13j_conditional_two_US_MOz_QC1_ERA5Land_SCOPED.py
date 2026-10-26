#!/usr/bin/env python3
"""Stage13j conditional source-QC1 repair for exactly 2 operator-approved
US-MOz 2005 events / 67 half-hours. No other source time or variable edits.

Stages:
 --self-test   synthetic arithmetic / exact two event identities; NO writes
 --check       SHA + BIF UTC + original-event preflight, independently CDS
               downloaded grid verification if available; NO writes
 --fetch       DOWNLOAD a single separate CDS ERA5-Land Jan03-Jan11 point
               response to *new* separate evidence folder, SHA receipt only
 --apply       repeat all prior SHA/clock/grid/QC0/physics/boundary gates,
               write new isolated science forcing ONLY for PASSING scoped events;
               failed events remain unchanged

The CDS ERA5-Land source is distinct but ERA5-driven, not independent
ground truth. We insist on measured source QC0 clock and event-boundary checks.
No source/native time/Stage07/Stage13g/PFT/ZBOT/CIME/DATM/Slurm edits.
"""
import argparse,csv,hashlib,io,json,os,sys,traceback,zipfile
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VER="batch03-stage13j-v4-20261026-UTC-coverage-QC0-edge-census"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
SITE="US-MOz"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13G=ROOT/"science_trials/stage13g_US_MOz_approved_native_T_VPD_20261026T180756Z_f75518a5"
S13I=ROOT/"reports/stage13i_US_MOz_Jan2005_QC1_multiday_episode_20261026T182923Z_bc9d9b34"
ORIGINAL=S07/"US-MOz/forcing/processed_v5/US-MOz_CLM_forcing_2004_2021.csv"
CURRENT=S13G/"US-MOz_CLM_forcing_2004_2021_STG13G_RESEARCH_SHADOW.csv"
SEAL=S13G/"stage13g_MOz_approved_T_VPD_science_shadow_SHA_receipt.json"
EVID=ROOT/"external_evidence/era5land_timeseries/US-MOz/2005_stage13j"
EVID_BASENAME="ERA5Land_US-MOz_Jan03_Jan11_2005_t2m_d2m_sp"
RECEIPT=EVID/(EVID_BASENAME+".receipt.json")
DECISION_NAME="STAGE13J_OPERATOR_CONDITIONAL_US_MOz_2005_TWO_QC1_EVENTS_20261026.json"
SCOPE=(
 ("2005-01-05T20:00:00","2005-01-06T09:00:00",27),
 ("2005-01-06T14:00:00","2005-01-07T09:30:00",40),
)
START=pd.Timestamp("2005-01-03")
END=pd.Timestamp("2005-01-11")
HH=pd.Timedelta(minutes=30)
COLS=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE")

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise RuntimeError("Missing / symlink source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def saturation(t):return 6.112*np.exp(17.67*t/(t+243.5))

def original(p,cols):
    x=pd.read_csv(safe(p),usecols=["TIMESTAMP_START",*cols],
        dtype={"TIMESTAMP_START":str},low_memory=False)
    ti=pd.to_datetime(x.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    mask=ti.dt.year.between(2004,2021)&~((ti.dt.month==2)&(ti.dt.day==29))
    x=x.loc[mask].copy()
    x.index=pd.DatetimeIndex(ti.loc[mask],name="native_time")
    x.drop(columns=["TIMESTAMP_START"],inplace=True)
    if not x.index.is_monotonic_increasing or x.index.has_duplicates:
        raise RuntimeError("Native source timeline not sorted unique")
    for k in cols:
        x[k]=pd.to_numeric(x[k],errors="coerce")
        x.loc[x[k]<=-9990,k]=np.nan
    return x

def forcing(p):
    x=pd.read_csv(safe(p),dtype={"time":str},low_memory=False)
    idx=pd.to_datetime(x.time,errors="raise")
    x.index=pd.DatetimeIndex(idx,name="native_time")
    if len(x)!=315360 or x.index.has_duplicates or x.index.hasnans or not x.index.is_monotonic_increasing:
        raise RuntimeError("Expected 315360 unique NOLEAP source halfhours")
    if set(COLS).difference(x.columns):raise RuntimeError("Missing required Stage13g forcing fields")
    for k in COLS:
        x[k]=pd.to_numeric(x[k],errors="coerce")
        if not np.isfinite(x[k].to_numpy(dtype=float)).all():raise RuntimeError("Nonfinite Stage13g "+k)
    return x

def metadata(spec):
    # Source release BIF (not canopy HEIGHTC) is the UTC offset/coordinate authority.
    raw=Path(spec["primary"]).parent
    found=list(raw.rglob("AMF_US-MOz_FLUXNET_BIF_*.csv"))
    if len(found)!=1:
        raise RuntimeError("HOLD_NO_EXACT_US_MOz_RELEASE_BIF_CSV found "+str(len(found)))
    bif=safe(found[0])
    with bif.open(encoding="utf-8-sig",newline="") as f:
        lines=list(csv.DictReader(f))
    if not lines:raise RuntimeError("Release BIF is empty")
    def scalar(keys):
        raw=[r.get("DATAVALUE","") for r in lines
             if r.get("VARIABLE","").strip().upper() in keys]
        nums=[]
        for value in raw:
            try:nums.append(float(value))
            except (ValueError,TypeError):pass
        unique={round(v,8) for v in nums if np.isfinite(v)}
        if len(unique)!=1:raise RuntimeError(
            "HOLD_BIF_VARIABLE_COUNT_OR_CONFLICT "+str(sorted(keys))+" "+str(len(unique)))
        return float(next(iter(unique)))
    lat=scalar({"LOCATION_LAT","LATITUDE","LAT"})
    lon=scalar({"LOCATION_LONG","LOCATION_LON","LONGITUDE","LON"})
    utc=scalar({"UTC_OFFSET"})
    if not (-90<=lat<=90 and -180<=lon<=180 and -12<=utc<=14):
        raise RuntimeError("Release BIF coordinates or clock offset invalid")
    if abs(utc-round(utc))>1e-8:
        raise RuntimeError("HOLD_HALF_HOUR_OR_FRACTIONAL_BIF_UTC_OFFSET")
    # Cross-checked against user-provided official AMF_US-MOz_BIF_20230331.xlsx,
    # AMF-BIF rows 174, 175 and 439, independently of raw surface data.
    if not(np.isclose(lat,38.7441,atol=1e-5,rtol=0) and
           np.isclose(lon,-92.2000,atol=1e-5,rtol=0) and
           np.isclose(utc,-6.0,atol=1e-8,rtol=0)):
        raise RuntimeError("BIF original source coordinates or UTC_OFFSET differ from verified official spreadsheet")
    return {"bif":str(bif),"bif_sha256":sha(bif),
            "latitude":lat,"longitude":lon,"utc_offset_hours":int(utc),
            "native_time":"FLUXNET-local-standard TIMESTAMP_START, verify by QC0",
            "height_source":"NO tower variable sensor height verified; NEVER use canopy HEIGHTC as ZBOT"}

def signed_data(decision):
    d=json.loads(safe(decision).read_text())
    if d.get("schema")!="batch03-stage13j-operator-conditional-two-QC1-episodes-v1":
        raise RuntimeError("Unrecognized operator science decision")
    items=d.get("scoped_events",[])
    if len(items)!=2 or [(x["native_start"],x["native_end"],x["half_hours"]) for x in items]!=list(SCOPE):
        raise RuntimeError("Operator event scope changed")
    assert d["science_status"]["model_spinup_authorized"] is False
    assert d["science_status"]["postv5_production_authorized"] is False
    signed=json.loads(safe(SEAL).read_text())
    if signed.get("approved_model_field_edit_rows")!=9 or \
       signed.get("source_review",{}).get("2005_Jan06_05_09_source_HOLD_unchanged") is not True or \
       signed.get("source_review",{}).get("Postv5_approved") is not False:
        raise RuntimeError("Stage13g previous approval source altered")
    if sha(CURRENT)!=signed.get("all_output_SHA256",{}).get(CURRENT.name):
        raise RuntimeError("Stage13g original completed science forcing not SHA-verified")
    if sha(ORIGINAL)!=signed["source_review"]["original_Stage07_selected_SHA256"]:
        raise RuntimeError("Original approved Stage07 candidate changed")
    doc=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    spec=next(x for x in doc["sites"] if x["site"]==SITE)
    refs={str(Path(x).resolve()):v for x,v in doc["input_sha256"].items()}
    for name in ("primary","era"):
        if sha(spec[name])!=refs.get(str(Path(spec[name]).resolve())):
            raise RuntimeError("Original tower/FLUXNET companion ERA SHA modified: "+name)
    last=json.loads(safe(S13I/"stage13i_MOz_source_QC1_2005_multiday_SHA_receipt.json").read_text())
    if last.get("science",{}).get("all_2005_QC1_T_count")!=361 or \
       last.get("science",{}).get("Jan6_total_source_tower_QC1_T_halfhours")!=42 or \
       last.get("science",{}).get("no_requested_replacement_applied") is not True:
        raise RuntimeError("Previous signed Stage13i review changed")
    if last.get("Stage13g_signed_original_SHA256")!=sha(CURRENT):
        raise RuntimeError("Stage13i and current forcing disagree")
    return spec

def load_native(decision):
    spec=signed_data(decision)
    t=original(spec["primary"],["TA_F","VPD_F","TA_F_QC","VPD_F_QC"])
    e=original(spec["era"],["TA_ERA","VPD_ERA"])
    curr=forcing(CURRENT)
    if not (curr.index.equals(t.index) and curr.index.equals(e.index)):
        raise RuntimeError("Raw/native/ERA/approved forcing index mismatch")
    selected=[]
    for a,b,count in SCOPE:
        tix=pd.date_range(a,b,freq="30min")
        if len(tix)!=count or not tix.isin(t.index).all():
            raise RuntimeError("Exact user-authorized native time window truncated")
        if not(t.loc[tix,"TA_F_QC"].eq(1).all() and
               t.loc[tix,"VPD_F_QC"].eq(1).all()):
            raise RuntimeError("Operator approved QC1 ONLY, original source QC differs")
        delta=(t.loc[tix,"TA_F"]-e.loc[tix,"TA_ERA"]).abs()
        if not(delta.gt(5).all()):
            raise RuntimeError("Stage13i original signed QC1 >5C interval changed")
        if not(np.allclose(curr.loc[tix,"TA_USE"].to_numpy(float),
                            t.loc[tix,"TA_F"].to_numpy(float),rtol=0,atol=1e-8)
               and np.allclose(curr.loc[tix,"VPD_USE"].to_numpy(float),
                               t.loc[tix,"VPD_F"].to_numpy(float),rtol=0,atol=1e-8)):
            raise RuntimeError("Current Stage13g changed an explicitly held source point")
        selected.append(tix)
    return spec,t,e,curr,selected

def evidence_filename():
    r=json.loads(safe(RECEIPT).read_text())
    if (r.get("dataset")!="reanalysis-era5-land-timeseries" or
        r.get("site")!=SITE or r.get("status")!="CDS_DOWNLOADED_ONLY_NOT_SCIENCE_ACCEPTED" or
        r.get("request",{}).get("date")!=["2005-01-03","2005-01-11"]):
        raise RuntimeError("Unrecognized Stage13j isolated CDS source evidence")
    p=safe(r["response_file"])
    if p.parent.resolve()!=EVID.resolve() or sha(p)!=r.get("response_sha256"):
        raise RuntimeError("ERA5-Land downloaded response SHA/path mismatch")
    if r.get("metadata",{}).get("bif_sha256")!=sha(r["metadata"]["bif"]):
        raise RuntimeError("BIF evidence changed since CDS source acquisition")
    return p,r

def latlon_validate(ds,site_lat,site_lon):
    for key,target in (("latitude",site_lat),("longitude",site_lon)):
        labels=("latitude","lat") if key=="latitude" else ("longitude","lon")
        names=[x for x in labels if x in ds.variables]
        if len(names)!=1:raise RuntimeError("ERA5-Land grid coordinate "+key+" absent/ambiguous")
        vals=np.asarray(ds.variables[names[0]][:]).reshape(-1)
        if len(vals)!=1 or not np.isfinite(vals).all() or abs(float(vals[0])-target)>0.3:
            raise RuntimeError("ERA5-Land gridpoint location mismatch/variable spatial grid "+key)

def verify_utc_coverage(index):
    """Coverage bounds mean earliest sample <= required start, latest >= end.
    The original Stage13j v2 mistakenly reversed the earliest inequality and
    rejected a perfectly valid CDS Jan03 start as 'not covering Jan04'.
    """
    if len(index)<2:
        raise RuntimeError("CDS hourly UTC time axis empty/too short")
    req_start=pd.Timestamp("2005-01-04 00:00:00")
    req_end=pd.Timestamp("2005-01-10 23:00:00")
    actual_start=pd.Timestamp(index.min())
    actual_end=pd.Timestamp(index.max())
    if not(actual_start<=req_start and actual_end>=req_end):
        raise RuntimeError("CDS response incomplete for UTC Jan04-Jan10 inclusive:"
            +" actual first="+str(actual_start)+" last="+str(actual_end)
            +" required first<="+str(req_start)+" last>="+str(req_end))
    return True

def nc_data(raw,meta):
    from netCDF4 import Dataset,num2date
    obs={}
    def read_ds(ds):
        latlon_validate(ds,meta["latitude"],meta["longitude"])
        timekey=next((x for x in ("valid_time","time") if x in ds.variables),None)
        if timekey is None:raise RuntimeError("ERA5-Land hourly UTC coordinate missing")
        tv=ds.variables[timekey]
        units=getattr(tv,"units",None)
        if not units or "since" not in str(units):
            raise RuntimeError("Non CF-time in signed CDS netCDF")
        times=num2date(tv[:],units,calendar=getattr(tv,"calendar","standard"),
            only_use_cftime_datetimes=False,only_use_python_datetimes=True)
        ts=pd.DatetimeIndex(pd.to_datetime([str(v) for v in times],utc=True)).tz_convert(None)
        if ts.has_duplicates or ts.hasnans:
            raise RuntimeError("Repeated/missing CDS UTC hourly timestamp")
        mapping={"t2m":("t2m","2m_temperature"),
                 "d2m":("d2m","2m_dewpoint_temperature"),
                 "sp":("sp","surface_pressure")}
        for k,aliases in mapping.items():
            matches=[v for v in aliases if v in ds.variables]
            if not matches:continue
            var=ds.variables[matches[0]]
            arrays=np.ma.asarray(var[:]).filled(np.nan)
            if arrays.shape[0]!=len(ts):raise RuntimeError("ERA5-Land NetCDF time axis wrong")
            if np.prod(arrays.shape[1:],dtype=int)!=1:
                raise RuntimeError("ERA5-Land returns >1 gridpoint; no arbitrary spatial selection")
            arr=arrays.reshape(len(ts)).astype(float)
            units=str(getattr(var,"units","")).lower()
            if k in ("t2m","d2m") and units not in ("k","kelvin"):
                raise RuntimeError("ERA5-Land T/D source not explicitly Kelvin")
            if k=="sp" and units not in ("pa","pascal","pascals"):
                raise RuntimeError("ERA5-Land SP source not explicitly Pa")
            x=pd.Series(arr,index=ts,name=k)
            if k in obs:raise RuntimeError("Duplicate ERA variable "+k)
            obs[k]=x
    if raw.suffix.lower()==".zip":
        with zipfile.ZipFile(raw) as z:
            if z.testzip() is not None:raise RuntimeError("Corrupted downloaded CDS ZIP")
            members=[v for v in z.infolist() if v.filename.lower().endswith(".nc") and not v.is_dir()]
            if not members or len(members)>10:raise RuntimeError("ERA5-Land source netcdf members absent/unexpected")
            for item in members:
                if item.file_size>400_000_000:raise RuntimeError("Unsafe ZIP member size")
                with Dataset("inmem.nc",mode="r",memory=z.read(item)) as ds:read_ds(ds)
    else:
        with Dataset(str(raw)) as ds:read_ds(ds)
    if set(obs)!={"t2m","d2m","sp"}:raise RuntimeError("CDS source t2m/d2m/sp incomplete")
    if not obs["t2m"].index.equals(obs["d2m"].index) or not obs["t2m"].index.equals(obs["sp"].index):
        raise RuntimeError("Different ERA variable UTC grids; no implied alignment")
    v=pd.DataFrame(obs).sort_index()
    verify_utc_coverage(v.index)
    print("STAGE13J VERIFIED CDS HOURLY UTC COVERAGE",
          str(v.index.min()),"through",str(v.index.max()),"hours",len(v),flush=True)
    if not np.allclose(np.diff(v.index.values).astype("timedelta64[m]").astype(float),60):
        raise RuntimeError("Incomplete hourly ERA5-Land source timestamps")
    if (v.t2m<180).any() or (v.t2m>335).any() or (v.d2m>v.t2m+0.1).any() or \
       (v.sp<45000).any() or (v.sp>111000).any():
        raise RuntimeError("Downloaded ERA5-Land met values outside defensible bounds")
    v["grid_T_C"]=v.t2m-273.15
    v["grid_VPD_hPa"]=saturation(v.grid_T_C)-saturation(v.d2m-273.15)
    return v

def at_native(grid,ix,utc_off):
    # FLUXNET time is standard local TIMESTAMP_START; native hour midpoint.
    utc=pd.DatetimeIndex(ix)+pd.Timedelta(minutes=15)-pd.Timedelta(hours=utc_off)
    if utc.min()<grid.index.min() or utc.max()>grid.index.max():
        raise RuntimeError("No CDS hourly UTC coverage at proposed BIF native interval midpoints")
    needed=["grid_T_C","grid_VPD_hPa","sp"]
    union=grid[needed].reindex(grid.index.union(utc)).sort_index().interpolate(
         method="time",limit_area="inside").reindex(utc)
    union.index=pd.DatetimeIndex(ix)
    if not np.isfinite(union.to_numpy(float)).all():
        raise RuntimeError("CDS interpolation yielded missing source-native climate")
    return union

def qc0_clock_and_boundary(t,e,grid,meta,segments):
    # Local QC0 measured analogues, independent of original FLUXNET QC1 gapfill.
    span=t.loc[START:END-pd.Timedelta(microseconds=1)]
    candidates=span.TA_F_QC.eq(0)&span.VPD_F_QC.eq(0)
    idx=span.index[candidates]
    # Always expose evidence for EACH event, even when the broad QC0 clock
    # calibration fails: otherwise the user cannot distinguish a missing
    # measured QC0 boundary from time-offset or ERA-Land incompatibility.
    context={"measured_both_QC0":int(len(idx))}
    for a,b,n in SCOPE:
        left=pd.Timestamp(a);right=pd.Timestamp(b)
        before=idx[(idx<left)&(idx>=left-pd.Timedelta(hours=6))]
        after=idx[(idx>right)&(idx<=right+pd.Timedelta(hours=6))]
        context[a+"/"+b]={
            "original_measured_QC0_T_and_VPD_6h_before":int(len(before)),
            "original_measured_QC0_T_and_VPD_6h_after":int(len(after)),
            "closest_QC0_before":str(before[-1]) if len(before) else None,
            "closest_QC0_after":str(after[0]) if len(after) else None,
            "status":"PENDING_GRID_TEST" if len(before) and len(after)
                     else "HOLD_MISSING_ORIGINAL_QC0_BOUNDARY"}
    if len(idx)<12:
        return False,{"status":"HOLD_QC0_ANALOGUES_INSUFFICIENT",**context}
    clock={}
    for off in (meta["utc_offset_hours"]-1,meta["utc_offset_hours"],
                meta["utc_offset_hours"]+1):
        g=at_native(grid,idx,off)
        diff=np.abs(t.loc[idx,"TA_F"].to_numpy(float)-g.grid_T_C.to_numpy(float))
        vpd=np.abs(t.loc[idx,"VPD_F"].to_numpy(float)-g.grid_VPD_hPa.to_numpy(float))
        clock[str(off)]={"T_MAE_C":float(np.mean(diff)),
                         "T_medianAE_C":float(np.median(diff)),
                         "VPD_MAE_hPa":float(np.mean(vpd)),
                         "analog_n":int(len(idx))}
    target=clock[str(meta["utc_offset_hours"])]
    neighbors=[clock[str(meta["utc_offset_hours"]+v)] for v in (-1,1)]
    clock_pass=(target["T_MAE_C"]<=3.0 and target["VPD_MAE_hPa"]<=2.0 and
                all(target["T_MAE_C"]+1.0<=p["T_MAE_C"] for p in neighbors))
    detail={"status":"PASS" if clock_pass else "HOLD_BIF_OFFSET_NOT_CONFIDENTLY_VALIDATED_BY_QC0",
            **context,"clock_candidates":clock}
    if not clock_pass:return False,detail
    # Both ends must have measured original QC0 T+VPD within 6h.
    passed=0
    for a,b,n in SCOPE:
        t0=pd.Timestamp(a);t1=pd.Timestamp(b)
        before=idx[(idx<t0)&(idx>=t0-pd.Timedelta(hours=6))]
        after=idx[(idx>t1)&(idx<=t1+pd.Timedelta(hours=6))]
        label=a+"/"+b
        if not len(before) or not len(after):
            detail[label]={"status":"HOLD_NO_QC0_T_VPD_BOTH_ENDS_WITHIN_6H",
                           "before":len(before),"after":len(after)}
            continue
        edges=[before[-1],after[0]]
        coords=at_native(grid,pd.DatetimeIndex(edges),meta["utc_offset_hours"])
        mism=np.abs(t.loc[edges,"TA_F"].to_numpy(float)-coords.grid_T_C.to_numpy(float))
        hum=np.abs(t.loc[edges,"VPD_F"].to_numpy(float)-coords.grid_VPD_hPa.to_numpy(float))
        acceptable=bool((mism<=2.5).all() and (hum<=2.5).all())
        detail[label]={"status":"PASS" if acceptable else "HOLD_QC0_BOUNDARY_INCONSISTENT",
                       "edge_times":[str(z) for z in edges],
                       "edge_T_abs_C":mism.tolist(),"edge_VPD_abs_hPa":hum.tolist()}
        if acceptable:passed+=1
    detail["eligible_event_count_with_QC0_boundaries"]=passed
    return True,detail

def science(decision,strict=False):
    spec,t,e,c,segments=load_native(decision)
    meta=metadata(spec)
    if not RECEIPT.is_file():
        return None,{"overall":"HOLD_MISSING_DISTINCT_CDS_ERA5LAND_SOURCE",
             "metadata":meta,"source_signed":True,"target_HH":67}
    p,r=evidence_filename()
    if r["metadata"]!=meta:
        raise RuntimeError("CDS evidence source BIF / UTC / coords altered")
    grid=nc_data(p,meta)
    ok,anchors=qc0_clock_and_boundary(t,e,grid,meta,segments)
    audit={"source_signed":True,"target_HH":67,"CDS_receipt":str(RECEIPT),
           "CDS_sha256":sha(p),"meta":meta,"QC0_clock_and_boundaries":anchors}
    if not ok:
        audit["overall"]="HOLD_MEASURED_QC0_CLOCK_OR_BOUNDARY"
        return None,audit
    events=[]
    for idx in segments:
        g=at_native(grid,idx,meta["utc_offset_hours"])
        dT=np.abs(g.grid_T_C.to_numpy(float)-e.loc[idx,"TA_ERA"].to_numpy(float))
        # ERA5-Land is not statistically independent; cross-product agreement
        # plus measured QC0 references is required. Compare water vapour RH.
        sat_comp=saturation(e.loc[idx,"TA_ERA"].to_numpy(float))
        rh_comp=100*(1-e.loc[idx,"VPD_ERA"].to_numpy(float)/sat_comp)
        sat_grid=saturation(g.grid_T_C.to_numpy(float))
        rh_grid=100*(1-g.grid_VPD_hPa.to_numpy(float)/sat_grid)
        gridV=g.grid_VPD_hPa.to_numpy(float)
        pa=c.loc[idx,"PSRF"].to_numpy(float)
        ea=(sat_grid-gridV)*100
        q=0.622*ea/(pa-0.378*ea)
        met_ok=(np.isfinite(q)&(q>0)&(q<0.08)&np.isfinite(rh_grid)&
                (rh_grid>0)&(rh_grid<100)&(gridV>0)&(gridV<sat_grid)&
                (dT<=3.5)&(np.abs(rh_grid-rh_comp)<=15)&
                (np.abs(g.sp.to_numpy(float)-pa)<=12000))
        left=idx[0]-HH;right=idx[-1]+HH
        # First and last rewritten point may not differ from protected immediate
        # neighbors by implausible step (>4 C / >4 hPa).
        immediate=[
          (left,gridV[0],float(g.grid_T_C.iloc[0])),
          (right,gridV[-1],float(g.grid_T_C.iloc[-1])),
        ]
        transition_ok=all((abs(float(c.at[boundary,"TA_USE"])-newtemp)<=4 and
                           abs(float(c.at[boundary,"VPD_USE"])-newvpd)<=4)
                          for boundary,newvpd,newtemp in immediate)
        qc0_edges_ok=anchors.get(str(idx[0])+"/"+str(idx[-1]),{}).get("status")=="PASS"
        for i,when in enumerate(idx):
            events.append({
              "site":SITE,"source_native_time":str(when),
              "event_start":str(idx[0]),"event_end":str(idx[-1]),
              "original_Stage13g_TA_C":float(c.at[when,"TA_USE"]),
              "original_Stage13g_VPD_hPa":float(c.at[when,"VPD_USE"]),
              "original_source_tower_QC_T":int(t.at[when,"TA_F_QC"]),
              "original_source_tower_QC_VPD":int(t.at[when,"VPD_F_QC"]),
              "paired_ERA_T_C":float(e.at[when,"TA_ERA"]),
              "CDS_grid_ERA5Land_T_C":float(g.grid_T_C.iloc[i]),
              "CDS_grid_ERA5Land_VPD_hPa":float(gridV[i]),
              "paired_ERA_RH_pct":float(rh_comp[i]),
              "CDS_grid_water_RH_pct":float(rh_grid[i]),
              "recalculated_TBOT_K":float(g.grid_T_C.iloc[i]+273.15),
              "recalculated_QBOT_kgkg":float(q[i]),
              "grid_vs_source_ERA_absT_C":float(dT[i]),
              "grid_vs_source_ERA_abs_RH_pct":float(abs(rh_grid[i]-rh_comp[i])),
              "source_native_physics_pass":bool(met_ok[i]),
              "source_event_boundary_continuity_pass":bool(transition_ok),
              "event_QC0_boundary_pass":bool(qc0_edges_ok),
              "event_science_pass":bool(qc0_edges_ok and met_ok.all() and transition_ok),
              "operator_approval_is_conditional":True,
            })
    patch=pd.DataFrame(events)
    if len(patch)!=67:raise RuntimeError("Signed science-target cardinality 67 changed")
    audit["eligible_event_times"]=int(patch.event_science_pass.sum())
    audit["held_event_times"]=int((~patch.event_science_pass).sum())
    audit["events"]=[{"start":start,"end":end,"event_science_pass":bool(g.event_science_pass.all()),
                      "HH":len(g)} for (start,end),g in patch.groupby(["event_start","event_end"])]
    if not patch.event_science_pass.any():
        audit["overall"]="HOLD_ALL_EVENTS_NO_SOURCE_REPLACEMENT"
        return patch,audit
    audit["overall"]="SCIENCE_SCOPE_PASS_ELIGIBLE_EVENTS_ONLY"
    return patch,audit

def download(decision):
    spec=signed_data(decision)
    meta=metadata(spec)
    if RECEIPT.exists() or any(EVID.glob(EVID_BASENAME+"*")):
        raise FileExistsError("Stage13j CDS output exists: never overwrite signed external source")
    try:import cdsapi
    except ImportError:raise RuntimeError("CDSAPI missing; activate clm_fates_env/install cdsapi first")
    if not((Path.home()/".cdsapirc").is_file() or os.getenv("CDSAPI_KEY")):
        raise RuntimeError("CDS credentials missing in IRIDIS6; obtain ~/.cdsapirc")
    EVID.mkdir(parents=True,exist_ok=True)
    req={"data_format":"netcdf","date":["2005-01-03","2005-01-11"],
         "location":{"latitude":meta["latitude"],"longitude":meta["longitude"]},
         "variable":["2m_temperature","2m_dewpoint_temperature","surface_pressure"]}
    temp=EVID/(EVID_BASENAME+".download.partial")
    if temp.exists():raise FileExistsError("CDS partial exists; inspect; never overwrite")
    print("STAGE13J CDS distinct-source only; NO FORCING REPAIRS",json.dumps(req),flush=True)
    cdsapi.Client().retrieve("reanalysis-era5-land-timeseries",req).download(str(temp))
    with temp.open("rb") as f:magic=f.read(8)
    if magic.startswith(b"PK"):suffix=".zip"
    elif magic.startswith(b"CDF") or magic==b"\x89HDF\r\n\x1a\n":suffix=".nc"
    else:raise RuntimeError("Unrecognized CDS downloaded response; partial retained")
    end=EVID/(EVID_BASENAME+suffix)
    if end.exists():raise FileExistsError("Already downloaded; never overwrite")
    temp.rename(end)
    obj={"version":VER,"site":SITE,"dataset":"reanalysis-era5-land-timeseries",
         "request":req,"metadata":meta,"response_file":str(end),
         "response_sha256":sha(end),"status":"CDS_DOWNLOADED_ONLY_NOT_SCIENCE_ACCEPTED",
         "created_utc":datetime.now(timezone.utc).isoformat(),
         "independent_tower_truth":False}
    with RECEIPT.open("x") as f:f.write(json.dumps(obj,indent=2)+"\n")
    print("STAGE13J CDS RECEIPT ONLY",RECEIPT,sha(end),flush=True)

def apply(decision,patch,audit):
    if audit.get("overall")!="SCIENCE_SCOPE_PASS_ELIGIBLE_EVENTS_ONLY":
        print("STAGE13J SCIENCE HOLD; no forcing output",json.dumps(audit,indent=2),flush=True)
        return 3
    c=forcing(CURRENT)
    out=c.copy(deep=True)
    eligible_patch=patch.loc[patch.event_science_pass].copy()
    p=eligible_patch.set_index(pd.to_datetime(eligible_patch.source_native_time),drop=False)
    for when,row in p.iterrows():
        for col,value in (("TA_USE",row.CDS_grid_ERA5Land_T_C),
                          ("VPD_USE",row.CDS_grid_ERA5Land_VPD_hPa),
                          ("TBOT",row.recalculated_TBOT_K),
                          ("QBOT",row.recalculated_QBOT_kgkg)):
            out.at[when,col]=float(value)
    eligible=set(p.index)
    for col in COLS:
        x=c[col].to_numpy(float)
        y=out[col].to_numpy(float)
        changed=np.flatnonzero(~np.isclose(x,y,atol=1e-12,rtol=0))
        if col not in ("TA_USE","VPD_USE","TBOT","QBOT") and len(changed):
            raise RuntimeError("Unapproved source variable modified: "+col)
        if any(out.index[i] not in eligible for i in changed):
            raise RuntimeError("Unapproved native timestamp changed: "+col)
    all_scoped={pd.Timestamp(t) for a,b,n in SCOPE for t in pd.date_range(a,b,freq="30min")}
    if not eligible or not eligible.issubset(all_scoped):
        raise RuntimeError("Unexpected Stage13j conditional source candidate times")
    if sha(CURRENT)!=audit.get("prior_sha",sha(CURRENT)):
        raise RuntimeError("Stage13g source changed while auditing")
    dest=ROOT/"science_trials"/("stage13j_MOz_ONLY_67_conditional_QC1_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_NO_PRODUCTION_USE"
    marker.write_text("Preflight export; no DATM/CIME approval.\n")
    name="US-MOz_CLM_forcing_2004_2021_STG13J_SCIENCE_SHADOW.csv"
    out.reset_index(drop=True).to_csv(dest/name,index=False)
    check=forcing(dest/name)
    for t in p.index:
        for col in ("TA_USE","VPD_USE","TBOT","QBOT"):
            if not np.isclose(check.at[t,col],out.at[t,col],rtol=0,atol=1e-9):
                raise RuntimeError("Reload signed science output not exact")
    patch.to_csv(dest/"exact_67_science_approved_source_replacement_ledger.csv",index=False)
    (dest/"stage13j_operator_science_summary.json").write_text(json.dumps(audit,indent=2)+"\n")
    hold="SCIENCE_SHADOW_NOT_DATM_OR_SPINUP_AUTHORIZED"
    (dest/hold).write_text(
         "Conditional operator source selection passed all specified automated"
         " gates; CDA ERA5-Land is ERA5-driven reanalysis, not independent tower"
         " evidence. Jan09 negative anomalies and all unapproved source times"
         " unchanged. Stage07 and Stage13g signed inputs preserved."
         " No PFT/ZBOT/model/Slurm changes; Post-v5 gate remains separate.\n")
    paths=[name,"exact_67_science_approved_source_replacement_ledger.csv",
           "stage13j_operator_science_summary.json",hold]
    receipt={"version":VER,"operator_decision_SHA256":sha(decision),
             "original_Stage13g_SHA256":sha(CURRENT),
             "original_Stage07_SHA256":sha(ORIGINAL),
             "ERA5Land_download_receipt_SHA256":sha(RECEIPT),
             "total_exact_scope_timestamps":67,
             "total_exact_conditionally_repaired_timestamps":len(eligible),
             "held_scoped_timestamps_untouched":67-len(eligible),
             "source_raw_and_Stage07_Stage13g_untouched":True,
             "postv5_production_approved":False,"spinup_authorized":False,
             "output_SHA256":{x:sha(dest/x) for x in paths}}
    (dest/"stage13j_SCIENCE_SHADOW_SHA_receipt.json").write_text(
         json.dumps(receipt,indent=2)+"\n")
    marker.unlink()
    print("STAGE13J CONDITIONAL NEW ISOLATED SHADOW SUCCESS",dest,flush=True)
    print("NOT DATM/AD400/Normal400 READY. ORIGINAL SOURCES UNCHANGED.",flush=True)
    return 0

def main():
    p=argparse.ArgumentParser()
    z=p.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","fetch","apply"):z.add_argument("--"+k,action="store_true")
    p.add_argument("--decision",type=Path)
    a=p.parse_args()
    print("STAGE13J CONDITIONAL OPERATOR SCOPE | "+VER,flush=True)
    assert sum(x[2] for x in SCOPE)==67
    assert not (pd.Timestamp(SCOPE[0][1])>=pd.Timestamp(SCOPE[1][0]))
    assert pd.Timestamp("2005-01-09")>pd.Timestamp(SCOPE[1][1])
    # Regression guard for the actual CDS coverage failure: a correctly
    # earlier Jan03 first timestamp MUST pass a Jan04-Jan10 coverage request.
    synthetic_good=pd.date_range("2005-01-03 00:00","2005-01-11 23:00",freq="h")
    assert verify_utc_coverage(synthetic_good)
    for invalid in (
         pd.date_range("2005-01-05 00:00","2005-01-11 23:00",freq="h"),
         pd.date_range("2005-01-03 00:00","2005-01-10 22:00",freq="h")):
        try:
            verify_utc_coverage(invalid)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Bad short CDS UTC source passed the regression test")
    print("STAGE13J SELF-TEST PASS | 27+40=67; CDS earlier-start range regression PASS",flush=True)
    if a.self_test:return
    if not a.decision:p.error("Require signed operator Stage13j --decision JSON")
    if a.fetch:download(a.decision);return
    patch,audit=science(a.decision)
    print("\n=== SCIENTIFIC GATE ===",flush=True)
    print(json.dumps(audit,indent=2,default=str),flush=True)
    if patch is not None:
        print("\n=== EXACT SCIENCE EVENT PREVIEW ===",flush=True)
        for key,group in patch.groupby(["event_start","event_end"]):
            print(key,"N",len(group),"pass",bool(group.event_science_pass.all()),
                  "physics_pass",int(group.source_native_physics_pass.sum()),flush=True)
            print(group[["source_native_time","original_Stage13g_TA_C","CDS_grid_ERA5Land_T_C",
                    "original_Stage13g_VPD_hPa","CDS_grid_ERA5Land_VPD_hPa",
                    "event_science_pass"]].head(4).to_string(index=False),flush=True)
    if a.check:
        print("STAGE13J CHECK ONLY: no source or forcing writes",flush=True)
        return
    return apply(a.decision,patch,audit)

if __name__=="__main__":
    try:
        rc=main()
        if isinstance(rc,int):raise SystemExit(rc)
    except Exception as error:
        print("STAGE13J STOP:",error,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

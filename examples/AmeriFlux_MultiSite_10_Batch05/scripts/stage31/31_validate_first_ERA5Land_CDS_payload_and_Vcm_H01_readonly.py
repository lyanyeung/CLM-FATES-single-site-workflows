#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage31: verify first actually downloaded ERA5-Land CDS
time-series payload and compare independent RETRIEVED reference with the
19 H01 US-Vcm 2007-Dec manually HELD original source half-hours.

CDS product: reanalysis-era5-land-timeseries, variables t2m/d2m in K,
hourly UTC. Can return ZIP containing separate parameter-group NetCDFs.
Original FLUXNET timestamps use local standard time with BIF UTC_OFFSET=-7
(2007 Vcm group has start date, lacks DATE_END; mapping PROVISIONAL).
No scientific approval, no original forcing modifications, no Slurm.
"""
import argparse,csv,hashlib,io,json,math,os,tempfile,zipfile
from pathlib import Path
from datetime import datetime,timedelta,timezone
from bisect import bisect_left

EXPECTED_SHA="abda0a706aef79dc0eb7a8b50db1b66ed427c8a756b81965d9bb3dba2e315646"
EVENT_SITE="US-Vcm"
H01_START="200712152100"
H01_END="200712160600"
H01_COUNT=19
TIME_OFFSET_HOURS=-7
REQUIRED18={"site","time_native","TA_F_C","VPD_F_hPa","RH_original_pct",
 "TA_F_QC","VPD_F_QC","TA_ERA_C","VPD_ERA_hPa","ERA_RH_Magnus_water_pct"}
REQUIREDHOLD={"site","native_time","hold_reason"}
ROW_FIELDS=("site","native_time","candidate_UTC","original_tower_T_C",
 "original_tower_VPD_hPa","original_tower_RH",
 "original_T_QC","original_VPD_QC","original_processed_ERA_T_C",
 "original_processed_ERA_VPD_hPa","original_processed_ERA_RH_pct",
 "ERA5L_interpolated_T_C","ERA5L_interpolated_Td_C",
 "ERA5L_RH_water_pct","ERA5L_grid_T_VPD_water_hPa",
 "ERA5L_T_minus_tower_T_C",
 "VPD_if_ERA5L_RH_carried_to_tower_T_hPa",
 "VPD_if_ERA5L_actual_vapour_pressure_carried_to_tower_T_hPa",
 "VPD_different_transport_hPa","ERA5L_grid_RH_minus_source_ERA_RH_pp",
 "reference_alignment","science_status")
VAR_ALIAS={
 "t2m":("t2m","2m_temperature","2mtemperature","temperature_2m"),
 "d2m":("d2m","2m_dewpoint_temperature","2mdewpointtemperature","dewpoint_temperature_2m")}
LAT_ALIASES=("latitude","lat")
LON_ALIASES=("longitude","lon")
TIME_ALIASES=("valid_time","time")

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()
def parse_native(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad native half-hour stamp "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def render_dt(d):return d.strftime("%Y-%m-%dT%H:%M:%SZ")
def number(s):
 try:
  x=float(s)
  if math.isfinite(x) and x not in (-9999.,-6999.):return x
 except (ValueError,TypeError):pass
 return None
def es_water(T):
 if T is None or not -80<=T<=60:raise ValueError("selected TA out of Magnus range")
 return 6.112*math.exp(17.67*T/(T+243.5))
def csv_rows(path,req):
 if not path.is_file() or path.is_symlink():raise ValueError("missing original file "+str(path))
 with path.open("r",newline="",encoding="utf-8-sig") as h:
  dr=csv.DictReader(h)
  if not req.issubset(dr.fieldnames or []):raise ValueError("original schema mismatch "+str(path))
  out=list(dr)
 if any(None in r or any(x is None for x in r.values()) for r in out):
  raise ValueError("malformed original csv "+str(path))
 return out
def extract_netcdfs(payload,temp):
 with payload.open("rb") as f:magic=f.read(8)
 container="UNKNOWN"
 files=[]
 if magic[:2]==b"PK":
  container="ZIP"
  with zipfile.ZipFile(payload) as z:
   info=[i for i in z.infolist() if not i.is_dir()]
   if not info:raise ValueError("empty CDS ZIP")
   if len(info)>30 or sum(i.file_size for i in info)>150*1024*1024:
    raise ValueError("CDS ZIP has unexpected content quantity/size")
   for j,i in enumerate(info):
    if not i.filename.lower().endswith((".nc",".nc4",".cdf")):
     raise ValueError("CDS ZIP entry is not NetCDF: "+i.filename)
    if i.file_size<256:raise ValueError("unexpectedly tiny NetCDF ZIP member")
    outfile=Path(temp)/("parameter_group_"+str(j)+".nc")
    with z.open(i) as src,outfile.open("xb") as dst:
     while True:
      part=src.read(1024*1024)
      if not part:break
      dst.write(part)
    files.append((outfile,i.filename))
 elif magic[:3]==b"CDF" or magic==b"\x89HDF\r\n\x1a\n":
  container="NETCDF"
  files=[(payload,payload.name)]
 else:raise ValueError("CDS file is not recognized ZIP/netCDF, first bytes="+repr(magic))
 return container,files

def inspect_reference(files):
 try:
  import xarray as xr
  import numpy as np
  import pandas as pd
 except ImportError as e:
  raise RuntimeError("Requires xarray, numpy, pandas and NetCDF engine (netcdf4 or h5netcdf): "+str(e))
 values={};metadata=[];coord={"latitude":[],"longitude":[]}
 for path,originalname in files:
  try:
   ds=xr.open_dataset(path,decode_times=True)
  except Exception as e:
   raise RuntimeError("Could not read CDS NetCDF member "+originalname+"; install netcdf4 or h5netcdf: "+str(e))
  with ds:
   meta={"member":originalname,"data_vars":list(ds.data_vars),
         "dimensions":{str(k):int(v) for k,v in ds.sizes.items()},
         "coordinate_names":list(ds.coords)}
   metadata.append(meta)
   for alias,options in VAR_ALIAS.items():
    present=[v for v in ds.data_vars if str(v).lower() in options]
    if not present:continue
    if alias in values or len(present)!=1:
     raise ValueError("CDS variable "+alias+" is duplicated or ambiguous")
    da=ds[present[0]]
    units=str(da.attrs.get("units","")).strip().lower()
    if units not in ("k","kelvin","degrees_k","degree_kelvin"):
     raise ValueError("CDS "+alias+" units NOT explicitly Kelvin: "+repr(units))
    tsname=next((x for x in TIME_ALIASES if x in da.dims),None)
    if tsname is None:
     raise ValueError("ERA5L variable no decoded time dimension "+str(da.dims))
    for dim in tuple(da.dims):
     if dim==tsname:continue
     if int(da.sizes[dim])!=1:
      raise ValueError("unexpected multi-point CDS dimension: "+dim+"="+str(da.sizes[dim]))
     da=da.isel({dim:0})
    if len(da.dims)!=1 or tsname not in da.dims:
     raise ValueError("CDS selected variable shape not 1-D time")
    timestamps=pd.to_datetime(da[tsname].values,utc=True)
    v=np.asarray(da.values,dtype=float).reshape(-1)
    if len(timestamps)!=len(v) or len(v)<24:
     raise ValueError("too few/mismatched CDS hourly records")
    if not np.all(np.isfinite(v)) or not np.all((v>170)&(v<350)):
     raise ValueError("CDS "+alias+" has invalid/missing/non-K meteorology")
    tuples=[(pd.Timestamp(t).to_pydatetime().replace(tzinfo=None),float(x)) for t,x in zip(timestamps,v)]
    if tuples!=sorted(tuples) or len({x[0] for x in tuples})!=len(tuples):
     raise ValueError("CDS "+alias+" UTC times nonmonotonic/duplicated")
    if any((b[0]-a[0])!=timedelta(hours=1) for a,b in zip(tuples,tuples[1:])):
     raise ValueError("CDS "+alias+" not continuous at exact UTC 1h steps")
    if any(t[0].minute!=0 or t[0].second!=0 for t in tuples):
     raise ValueError("CDS decoded UTC timestamps not on full hours")
    values[alias]=tuples
   for canonical,options in (("latitude",LAT_ALIASES),("longitude",LON_ALIASES)):
    for name in options:
     if name in ds.coords:
      x=np.asarray(ds.coords[name].values)
      if x.size==1 and np.isfinite(float(x.reshape(-1)[0])):
       coord[canonical].append(float(x.reshape(-1)[0]))
 if set(values)!={"t2m","d2m"}:
  raise ValueError("CDS payload lacks exact both 2m air temperature and 2m dewpoint: "+str(list(values)))
 if [t for t,v in values["t2m"]]!=[t for t,v in values["d2m"]]:
  raise ValueError("CDS T and dewpoint time coordinates disagree")
 lat=coord["latitude"];lon=coord["longitude"]
 if lat and max(lat)-min(lat)>1e-4:raise ValueError("CDS member lat inconsistent")
 if lon and max(lon)-min(lon)>1e-4:raise ValueError("CDS member lon inconsistent")
 return values,metadata,{"latitude":lat[0] if lat else None,
                         "longitude":lon[0] if lon else None}

def interp(t,series):
 times=[x[0] for x in series]
 if t<times[0] or t>times[-1]:
  raise ValueError("requested H01 UTC timestamp beyond CDS downloaded coverage")
 k=bisect_left(times,t)
 if k<len(times) and times[k]==t:return series[k][1],"EXACT_HOURLY_UTC"
 if k==0 or k==len(series):
  raise ValueError("no bounding hourly values around HH timestamp")
 a,va=series[k-1];b,vb=series[k]
 if b-a!=timedelta(hours=1):raise ValueError("missing hourly bracketing")
 alpha=(t-a).total_seconds()/(b-a).total_seconds()
 if not 0<alpha<1:raise ValueError("unexpected interpolation range")
 return va+(vb-va)*alpha,"LINEAR_HALF_HOURLY_FROM_TWO_UTC_HOURS"

def join_h01(d18,d24,reference):
 sourcefile=d18/"stage18_all_p1_original_6hour_context.csv"
 holdsfile=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 src=csv_rows(sourcefile,REQUIRED18)
 holds=csv_rows(holdsfile,REQUIREDHOLD)
 if len(src)!=775 or len(holds)!=46:raise ValueError("Stage18 or Stage24 original source population changed")
 h01_source={(r["site"],r["time_native"]):r for r in src
  if r["site"]=="US-Vcm" and H01_START<=r["time_native"]<=H01_END}
 h01_hold={(r["site"],r["native_time"]):r for r in holds
  if r["site"]=="US-Vcm" and H01_START<=r["native_time"]<=H01_END}
 if len(h01_source)!=H01_COUNT or len(h01_hold)!=H01_COUNT or set(h01_source)!=set(h01_hold):
  raise ValueError("H01 19 original manually held source half-hours not identical")
 result=[]
 for site,native in sorted(h01_hold):
  r=h01_source[site,native]
  if number(r["RH_original_pct"]) is not None:
   raise ValueError("H01 original source RH should remain missing")
  native_dt=parse_native(native)
  utc_dt=native_dt-timedelta(hours=TIME_OFFSET_HOURS)
  T,mode=interp(utc_dt,reference["t2m"])
  D,dmode=interp(utc_dt,reference["d2m"])
  if mode!=dmode:raise ValueError("CDS air/dewpoint time join method disagreement")
  T-=273.15;D-=273.15
  tower=number(r["TA_F_C"])
  if tower is None:raise ValueError("original tower TA missing for H01")
  reference_rh=100*es_water(D)/es_water(T)
  grid_vpd=es_water(T)-es_water(D)
  tower_vpd_rh=es_water(tower)*(1-reference_rh/100)
  tower_vpd_e=es_water(tower)-es_water(D)
  if reference_rh<0 or reference_rh>100.5:
   raise ValueError("CDS dewpoint reference yields nonphysical RH for H01")
  # If e_ERA exceeds es(tower T), negative VPD is NOT clipped or approved.
  source_RH=number(r["ERA_RH_Magnus_water_pct"])
  result.append(dict(
   site=site,native_time=native,candidate_UTC=render_dt(utc_dt),
   original_tower_T_C=tower,
   original_tower_VPD_hPa=r["VPD_F_hPa"],
   original_tower_RH=r["RH_original_pct"],
   original_T_QC=r["TA_F_QC"],original_VPD_QC=r["VPD_F_QC"],
   original_processed_ERA_T_C=r["TA_ERA_C"],
   original_processed_ERA_VPD_hPa=r["VPD_ERA_hPa"],
   original_processed_ERA_RH_pct=r["ERA_RH_Magnus_water_pct"],
   ERA5L_interpolated_T_C=round(T,6),
   ERA5L_interpolated_Td_C=round(D,6),
   ERA5L_RH_water_pct=round(reference_rh,6),
   ERA5L_grid_T_VPD_water_hPa=round(grid_vpd,8),
   ERA5L_T_minus_tower_T_C=round(T-tower,6),
   VPD_if_ERA5L_RH_carried_to_tower_T_hPa=round(tower_vpd_rh,8),
   VPD_if_ERA5L_actual_vapour_pressure_carried_to_tower_T_hPa=round(tower_vpd_e,8),
   VPD_different_transport_hPa=round(tower_vpd_rh-tower_vpd_e,8),
   ERA5L_grid_RH_minus_source_ERA_RH_pp=round(reference_rh-source_RH,6) if source_RH is not None else "",
   reference_alignment=mode,science_status="RESEARCH_ONLY_P1_H01_MANUAL_HOLD_UNCHANGED"))
 return result,sourcefile,holdsfile

def write(path,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=ROW_FIELDS,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 start=parse_native(H01_START);end=parse_native(H01_END)
 assert int((end-start).total_seconds()/1800)+1==19
 assert render_dt(start-timedelta(hours=-7))=="2007-12-16T04:00:00Z"
 ref=[(datetime(2007,12,16,4),270),(datetime(2007,12,16,5),272)]
 assert interp(datetime(2007,12,16,4,30),ref)==(271.0,"LINEAR_HALF_HOURLY_FROM_TWO_UTC_HOURS")
 assert 0<100*es_water(-9)/es_water(-5)<100
 print("STAGE31 SELF-TEST PASS | 19 exact H01 HOLD; local-UTC -7; hourly/30min interpolation; no original writes")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage30-fetch-dir",type=Path)
 p.add_argument("--stage18-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--out",type=Path)
 args=p.parse_args()
 if args.self_test:selftest();return
 if any(x is None for x in (args.stage30_fetch_dir,args.stage18_dir,args.stage24_dir,args.out)):
  p.error("Need --stage30-fetch-dir --stage18-dir --stage24-dir --out")
 d30,d18,d24=[x.expanduser().resolve() for x in (
  args.stage30_fetch_dir,args.stage18_dir,args.stage24_dir)]
 out=args.out.expanduser().resolve()
 if (not all(d.is_dir() for d in (d30,d18,d24)) or out.exists()
    or not out.parent.is_dir()
    or any(out==d or out in d.parents or d in out.parents for d in (d30,d18,d24))):
  p.error("new Stage31 output must be disjoint from input directories")
 payload=d30/"ERA5L_US_Vcm_200712.cds_download"
 manifest=d30/"stage30_summary.json"
 if not payload.is_file() or payload.is_symlink() or payload.stat().st_size!=20935 or sha(payload)!=EXPECTED_SHA:
  raise ValueError("first CDS pilot payload SHA256/size differs from verified user-reported result")
 m=json.loads(manifest.read_text())
 downloads=m.get("downloaded",[])
 if len(downloads)!=1 or downloads[0].get("request_id")!="ERA5L_US_Vcm_200712":
  raise ValueError("Stage30 must contain exactly first scientific pilot download")
 if downloads[0].get("sha256")!=EXPECTED_SHA or downloads[0].get("size_bytes")!=20935:
  raise ValueError("Stage30 original CDS manifest and downloaded payload disagree")
 if not m.get("BIF_UTC_OFFSET_DATE_END_missing") or m.get("science_approvals_new")!=0:
  raise ValueError("original source clock metadata status or science authorization changed")
 with tempfile.TemporaryDirectory(prefix="batch05_stage31_cdspayload_") as temp:
  fmt,files=extract_netcdfs(payload,temp)
  values,metadatas,coord=inspect_reference(files)
  rows,sourcefile,holdsfile=join_h01(d18,d24,values)
 if len(rows)!=19:raise ValueError("H01 original source 19 missing")
 grid_lat=coord["latitude"];grid_lon=coord["longitude"]
 if grid_lon is not None and grid_lon>180:grid_lon-=360
 req_lat,req_lon=35.8885,-106.5322
 if grid_lat is not None and abs(grid_lat-req_lat)>0.11:
  raise ValueError("ERA5-Land nearest grid latitude unexpectedly distant")
 if grid_lon is not None and abs(grid_lon-req_lon)>0.11:
  raise ValueError("ERA5-Land nearest grid longitude unexpectedly distant")
 for hour in ("t2m","d2m"):
  if len(values[hour])!=96 or values[hour][0][0]!=datetime(2007,12,14,0) or values[hour][-1][0]!=datetime(2007,12,17,23):
   raise ValueError("CDS requested four-day hourly UTC calendar coverage not exact")
 stats={
  "ERA5L_RH_pct_min":min(r["ERA5L_RH_water_pct"] for r in rows),
  "ERA5L_RH_pct_max":max(r["ERA5L_RH_water_pct"] for r in rows),
  "ERA5L_minus_tower_T_C_min":min(r["ERA5L_T_minus_tower_T_C"] for r in rows),
  "ERA5L_minus_tower_T_C_max":max(r["ERA5L_T_minus_tower_T_C"] for r in rows),
  "ERA5L_RH_grid_vs_source_ERA_pp_abs_max":max(abs(r["ERA5L_grid_RH_minus_source_ERA_RH_pp"]) for r in rows if r["ERA5L_grid_RH_minus_source_ERA_RH_pp"]!=""),
  "VPD_RH_transport_vs_e_transport_abs_max_hPa":max(abs(r["VPD_different_transport_hPa"]) for r in rows),
  "hypothetical_e_transfer_negative_VPD_count":sum(r["VPD_if_ERA5L_actual_vapour_pressure_carried_to_tower_T_hPa"]<0 for r in rows)
 }
 out.mkdir(exist_ok=False)
 write(out/"stage31_H01_19_HH_EXTERNAL_ERA5L_T_TD_RH_VPD_RESEARCH_ONLY.csv",rows)
 metadata=dict(
  stage="Stage31_H01_external_reference_first_CDS_pilot",
  original_CDS_product="reanalysis-era5-land-timeseries",
  original_CDS_file_sha256=sha(payload),original_CDS_file_size_bytes=payload.stat().st_size,
  CDS_container_format=fmt,CDS_NetCDF_member_structure=metadatas,
  grid_nearest_lat=grid_lat,grid_nearest_lon=grid_lon,
  source_requested_lat=req_lat,source_requested_lon=req_lon,
  grid_elevation_m="NOT_PRESENT_NOT_ASSUMED",
  first_reference_UTC_hour=render_dt(values["t2m"][0][0]),
  last_reference_UTC_hour=render_dt(values["t2m"][-1][0]),
  hourly_reference_observations=len(values["t2m"]),
  verified_source_H01_original_HOLD_half_hours=19,
  H01_tower_original_RH_present=0,
  BIF_UTC_OFFSET_hours=-7,
  BIF_DATE_END_verified=False,
  interpolated_reference_variables_from_K_to_C=True,
  reference_surface_saturation_formula="Magnus water 6.112 exp(17.67T/(T+243.5)) hPa; at subzero temperature water/ice phase sensitivity should be examined",
  science_source_reanalysis_not_in_situ=True,
  H01_user_HOLD_released=False,
  Stage24_166_approved_modified=False,
  P1_46_HOLD_modified=False,
  P2P3_1574_released=False,
  original_FLUXMET_changed=False,DATM_changed=False,Slurm_submitted=False,
  original_stage18_input_sha256=sha(sourcefile),
  original_stage24_hold_sha256=sha(holdsfile),
  science_screen_stats=stats)
 (out/"stage31_summary.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 md=["# Stage31 first real CDS ERA5-Land file — US-Vcm H01 original 19 manual HOLD half-hours","",
  "**Actual first CDS ZIP/NetCDF reference is extracted and SHA-verified, not only a request plan.**",
  "Native FLUXNET LST is converted to candidate UTC using BIF -7h, with missing original BIF END_DATE explicitly UNVERIFIED.",
  "CDS 2m temperature and 2m dewpoint are in Kelvin and converted to Celsius.",
  "CDS *UTC hourly* meteorology is linearly interpolated at native HH UTC timestamps; no automatic DST shift.",
  "Source original RH was absent for all 19; it is not reconstructed into original FLUXMET.",
  "Scientific comparison uses two distinct illustrative, **unapproved** ways of transporting reference moisture to original tower T:",
  "RH-conserving and actual-water-vapour-pressure-conserving. Neither is a validated elevation correction.",
  "At subzero temperatures saturation over ice differs from water; water convention is used for direct Stage18/22 consistency.",
  "Grid temperature differs from tower weather possibly because of 0.1° nearest cell, elevation/land cover, and actual atmospheric variation.","",
  "## Original CDS payload","",
  "- Container: **"+fmt+"**; NetCDF members: **"+str(len(metadatas))+"**",
  "- Hourly UTC coverage: **"+metadata["first_reference_UTC_hour"]+"** to **"+metadata["last_reference_UTC_hour"]+"**",
  "- Nearest grid location (if encoded): lat **"+str(grid_lat)+"**, lon **"+str(grid_lon)+"**",
  "- Original user sample hash: \`"+EXPECTED_SHA+"\`","",
  "## H01 summaries"]
 for k,v in stats.items():md.append("- **"+k+"**: "+str(v))
 md+=["","## All 19 user-held original half-hours: independent-reference comparison",
  "| Native LST | UTC | Tower TA C | Source ERA RH % | ERA5-L RH % | ERA5-L T C | ERA5-L Td C | Tower-ERA5L T diff C |",
  "|---|---|---:|---:|---:|---:|---:|---:|"]
 for r in rows:
  md.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
   r["native_time"],r["candidate_UTC"],
   r["original_tower_T_C"],r["original_processed_ERA_RH_pct"],
   r["ERA5L_RH_water_pct"],r["ERA5L_interpolated_T_C"],
   r["ERA5L_interpolated_Td_C"],round(-r["ERA5L_T_minus_tower_T_C"],4)))
 md+=["","**NO SCIENCE REPAIR APPROVAL.** Original RH remains missing and 19 H01 P1 records remain human HOLD.",
  "Next: compare each ERA5L RH/VPD candidate with original processed ERA/MDS, humidity phase",
  "and elevation-sensitive T differences; do not release an H01 overlay without explicit user scientific decision.",""]
 (out/"STAGE31_H01_INDEPENDENT_REFERENCE_ASSESSMENT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 print("STAGE31 SUCCESS | SHA verified",EXPECTED_SHA,"CONTAINER",fmt,
       "NETCDF_MEMBERS",len(metadatas),
       "UTC_HOURS",len(values["t2m"]),"H01_MATCHED_HH",len(rows))
 print("STAGE31 GRID_LOCATION",grid_lat,grid_lon)
 for k,v in stats.items():print("STAGE31",k,v)
 print("STAGE31_REPORT="+str(out/"STAGE31_H01_INDEPENDENT_REFERENCE_ASSESSMENT.md"))
 print("STAGE31_OUT="+str(out))
 print("STAGE31 H01_MANUAL_HOLD=19 REMAINS; APPROVED166/HOLD46/P2P3_1574/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

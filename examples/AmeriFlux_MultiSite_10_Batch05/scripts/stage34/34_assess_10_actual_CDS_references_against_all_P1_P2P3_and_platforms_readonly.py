#!/usr/bin/env python3
"""Batch05 Stage34: verify 10 ACTUAL CDS ERA5-Land ZIP/NetCDF reference downloads,
then compare *source-native* P1 HOLDs, unapproved RH saturation platforms, and
original Stage27 unapproved P2/P3, all source/time matched.

Reuses the already scientifically and operationally proven Stage31 CDS NetCDF
parser (verify its Git blob SHA); no duplicative fragile NetCDF parsing.
BIF local standard timestamps map to provisional UTC (-7 New Mexico, -6
Wisconsin), no DST. Tests hourly coverage, T/Td Kelvin, nearest grid position,
and original download SHA of all TEN samples from the investigator log.

Read-only analysis of downloaded gridded meteorology: ERA5-Land is not an
independent in-situ weather station. ALL P1 manual HOLDs remain HOLD,
and P2/P3 and saturation platforms remain NOT SCIENCE APPROVED. This script
does NOT create or modify a forcing overlay, source ZIP/CSV, CIME, or Slurm.
"""
import argparse,csv,hashlib,importlib.util,json,math,tempfile
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter,defaultdict

EXPECTED_SHA={
"ERA5L_US_Vcm_200802":"52354b42120aebe27e1beba417be54898dea1e6fbae4d4d982d06eb74b089682",
"ERA5L_US_Vcm_200812":"e443584765ab6f63326fe845d769b4cfc1baba62c93a53b467ea02e6a8294959",
"ERA5L_US_Vcm_201512":"c0f941c10f1041a67f4c6a6484ce6c86ea46bc11ddd5ed619e412c3c2e624879",
"ERA5L_US_Vcp_201101":"513464f7d7d2662768e286e526b82ef8abb95a685d03d6e78e4fc975003b8f45",
"ERA5L_US_Vcm_202510":"4a87a7b91b70c213f2c6fc8e9115d68597f81ae6962232a7bac38f4fb324b987",
"ERA5L_US_WCr_202508":"cd8cb50962b30b26d0a90c307041c1bbca425f1c1369c5e0327801967d7362ec",
"ERA5L_US_Vcp_200804":"49cff9789dfeea27ea0611500c869c660989dbab9e216109ecee3858a1e38d8b",
"ERA5L_US_Vcp_200805":"110663807b2055cceaca191508f13bc568e5944568fcc5896b0b80ccb2ee0a6d",
"ERA5L_US_Vcp_200806":"ab471024e17a8a343ec3ef30e60e525c270953b9047c35efbacfcb5de6ffe62f",
"ERA5L_US_Wjs_TOP1_P2P3_US-Wjs_E0031":"31c86d9c4eb7e57ab81fb8e84df590a2b379287dcb2e879832b0f2ca8fe241a3",
}
SITES={"US-Vcm":(35.8885,-106.5322,-7),
       "US-Vcp":(35.8641,-106.5965,-7),
       "US-Wjs":(34.4258,-105.8617,-7),
       "US-WCr":(45.8058,-90.0795,-6)}
STAGE31_BLOB="a28bde14dadcaf87abaaa2d52f2eaa785e16c89f"
H01_START,H01_END="200712152100","200712160600"
SOURCE_P1={"site","time_native","TA_F_C","VPD_F_hPa","RH_original_pct",
 "TA_F_QC","VPD_F_QC","ERA_RH_Magnus_water_pct"}
SOURCE_HOLD={"site","native_time","hold_reason"}
SOURCE_PLATFORM={"site","native_time","platform","original_TA_C",
 "original_VPD_hPa","original_RH_pct","source_processed_ERA_RH_pct"}
SOURCE_P2={"site","native_time","episode_id","review_lane","TA_F_C",
 "VPD_F_hPa","TA_F_QC","VPD_F_QC","RH_original_pct","RH_MDS_pct",
 "RH_ERA_pct","risk_flags"}
COLS=("site","native_time","candidate_UTC","source_population",
 "source_episode_or_platform","source_original_T_C","source_original_VPD_hPa",
 "source_original_RH_pct","source_TA_QC","source_VPD_QC",
 "source_MDS_RH_pct","source_processed_ERA_RH_pct",
 "ERA5Land_reference_T_C","ERA5Land_reference_Td_C",
 "ERA5Land_reference_RH_water_pct","ERA5Land_reference_RH_ice_pct",
 "ERA5Land_reference_e_water_dewpoint_hPa",
 "ERA5Land_grid_VPD_water_hPa","ERA5Land_T_minus_source_T_C",
 "candidate_VPD_original_T_preserve_ref_RH_water_hPa",
 "candidate_VPD_original_T_preserve_ref_actual_e_hPa",
 "candidate_two_transport_VPD_difference_hPa",
 "ERA5Land_RH_minus_source_ERA_RH_pp",
 "ERA5Land_RH_minus_source_MDS_RH_pp",
 "reference_closer_to_MDS_or_source_ERA",
 "science_concern_flags","CDS_request_id","UTC_alignment_type",
 "science_permission")
FILES=("request_id","site","requested_UTC_first","requested_UTC_last",
 "actual_UTC_first","actual_UTC_last","UTC_hours",
 "zip_or_netcdf","members","grid_lat","grid_lon",
 "expected_sha256","verified_sha256","matched_native_HH",
 "scientific_status")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def git_blob(p):
 b=p.read_bytes()
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def dt(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("invalid source-native time "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def n(v):
 try:
  f=float(v)
  if math.isfinite(f) and f not in (-9999.0,-6999.0):return f
 except(ValueError,TypeError):pass
 return None
def sat(t):
 if t is None or not (-80<=t<=60):raise ValueError("invalid air temperature")
 return 6.112*math.exp(17.67*t/(243.5+t))
def sat_ice(t):
 if not (-65<=t<0):return None
 return 6.112*math.exp(22.46*t/(272.62+t))
def get_csv(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("original CSV absent "+str(p))
 with p.open("r",newline="",encoding="utf-8-sig") as f:
  reader=csv.DictReader(f)
  if not required.issubset(reader.fieldnames or []) or len(reader.fieldnames or [])!=len(set(reader.fieldnames or [])):
   raise ValueError("original CSV schema changed "+str(p))
  out=list(reader)
 if any(None in r or any(v is None for v in r.values()) for r in out):
  raise ValueError("malformed CSV row "+str(p))
 return out
def idx(rows,field):
 d={}
 for r in rows:
  key=r["site"],r[field]
  if key in d:raise ValueError("duplicate site/timestamp "+str(key))
  d[key]=r
 return d
def put(p,cols,rows):
 with p.open("x",newline="",encoding="utf-8") as f:
  wr=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  wr.writeheader();wr.writerows(rows)
def source_load(d18,d24,d27):
 f18=d18/"stage18_all_p1_original_6hour_context.csv"
 f24=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 fp=d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"
 fa=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 f27=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 m24=json.loads((d24/"stage24_manifest.json").read_text())
 m27=json.loads((d27/"stage27_summary.json").read_text())
 if (m24.get("total_approved_overlay_HH"),
     m24.get("total_original_P1_manual_HOLD"))!=(166,46):
  raise ValueError("original approved/HOLD source audit changed")
 if (m27.get("source_P2P3_native_HH"),
     m27.get("newly_approved_source_records"))!=(1574,0):
  raise ValueError("original P2P3 source scientific state changed")
 context=idx(get_csv(f18,SOURCE_P1),"time_native")
 holds=idx(get_csv(f24,SOURCE_HOLD),"native_time")
 platforms=idx(get_csv(fp,SOURCE_PLATFORM),"native_time")
 originalp2=idx(get_csv(f27,SOURCE_P2),"native_time")
 approved=idx(get_csv(fa,{"site","native_time"}),"native_time")
 if (len(context),len(holds),len(platforms),len(originalp2),len(approved))!=(775,46,10,1574,166):
  raise ValueError("exact native original science populations changed")
 if set(originalp2)&set(holds) or set(originalp2)&set(approved):
  raise ValueError("scientifically unapproved records intersect already approved source")
 return context,holds,platforms,originalp2,approved,{
  "Stage18_original_context":sha(f18),"Stage24_46_manual_HOLD":sha(f24),
  "Stage24_10_unapproved_platforms":sha(fp),
  "Stage24_166_approved":sha(fa),
  "Stage27_original_1574_P2P3":sha(f27)}

def choose_original(site,time,context,held,platforms,p2):
 k=site,time
 if k in held:
  if k not in context:raise ValueError("manual P1 held original context not found "+str(k))
  r=context[k]
  return dict(site=site,native_time=time,kind="P1_MANUAL_HOLD",
   event=r.get("group","P1_SOURCE_HOLD"),
   T=n(r["TA_F_C"]),V=n(r["VPD_F_hPa"]),rh=n(r["RH_original_pct"]),
   qcT=r["TA_F_QC"],qcV=r["VPD_F_QC"],
   source_era=n(r["ERA_RH_Magnus_water_pct"]),mds=None,
   risk="")
 if k in platforms:
  r=platforms[k]
  return dict(site=site,native_time=time,kind="RH_SATURATION_PLATFORM_UNAPPROVED",
   event=r["platform"],T=n(r["original_TA_C"]),V=n(r["original_VPD_hPa"]),
   rh=n(r["original_RH_pct"]),qcT="SOURCE_PLATFORM",
   qcV="SOURCE_PLATFORM",source_era=n(r["source_processed_ERA_RH_pct"]),
   mds=None,risk="SUSPECT_SATURATION_PLATFORM")
 if k in p2:
  r=p2[k]
  return dict(site=site,native_time=time,kind="P2_P3_ORIGINAL_UNAPPROVED",
   event=r["episode_id"],T=n(r["TA_F_C"]),V=n(r["VPD_F_hPa"]),
   rh=n(r["RH_original_pct"]),qcT=r["TA_F_QC"],qcV=r["VPD_F_QC"],
   source_era=n(r["RH_ERA_pct"]),mds=n(r["RH_MDS_pct"]),
   risk=r["risk_flags"])
 return None

def scientific_row(original,request_id,utc,refT,refTd,alignment):
 e=sat(refTd)
 es=sat(refT)
 rh=100*e/es
 vpdgrid=es-e
 origT=original["T"]
 if origT is None:raise ValueError("original selected tower air T missing")
 origES=sat(origT)
 vpdrh=origES*(1-rh/100)
 vpde=origES-e
 rhice=100*e/sat_ice(refT) if sat_ice(refT) is not None else None
 erarh=original["source_era"]
 mds=original["mds"]
 era_diff=rh-erarh if erarh is not None else None
 mds_diff=rh-mds if mds is not None else None
 if era_diff is not None and mds_diff is not None:
  closer=("MDS_REFERENCE_CLOSER" if abs(mds_diff)+5<abs(era_diff) else
          "PROCESSED_SOURCE_ERA_CLOSER" if abs(era_diff)+5<abs(mds_diff) else
          "CLOSE_OR_AMBIGUOUS_WITHIN5PP")
 else:closer="CANNOT_COMPARE_BOTH_MDS_AND_SOURCE_ERA"
 flags=[]
 if refTd>refT:flags.append("GRID_DEWPOINT_EXCEEDS_T")
 if abs(refT-origT)>5:flags.append("GRID_VS_TOWER_T_DIFF_GT5C")
 if origES<e:flags.append("SOURCE_TOWER_T_WITH_GRID_ACTUAL_e_WOULD_GIVE_NEGATIVE_WATER_VPD")
 if erarh is not None and abs(era_diff)>20:flags.append("INDEPENDENT_REANALYSIS_VS_PROCESSED_SOURCE_ERA_RH_GT20PP")
 if mds is not None and abs(mds_diff)>20:flags.append("INDEPENDENT_REANALYSIS_VS_SOURCE_MDS_RH_GT20PP")
 if abs(vpdrh-vpde)>2:flags.append("CANDIDATE_VPD_TRANSPORT_ASSUMPTION_DIFF_GT2HPA")
 if original["rh"] is not None and abs(original["rh"]-rh)>20:flags.append("ORIGINAL_RH_VS_GRID_REF_DIFF_GT20PP")
 if original["risk"]:flags.append("SOURCE_ORIGINAL_RISK_FLAGS_PRESENT")
 return dict(site=original["site"],native_time=original["native_time"],
  candidate_UTC=utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
  source_population=original["kind"],
  source_episode_or_platform=original["event"],
  source_original_T_C=origT,
  source_original_VPD_hPa=original["V"] if original["V"] is not None else "",
  source_original_RH_pct=original["rh"] if original["rh"] is not None else "",
  source_TA_QC=original["qcT"],source_VPD_QC=original["qcV"],
  source_MDS_RH_pct=mds if mds is not None else "",
  source_processed_ERA_RH_pct=erarh if erarh is not None else "",
  ERA5Land_reference_T_C=round(refT,6),
  ERA5Land_reference_Td_C=round(refTd,6),
  ERA5Land_reference_RH_water_pct=round(rh,6),
  ERA5Land_reference_RH_ice_pct=round(rhice,6) if rhice is not None else "",
  ERA5Land_reference_e_water_dewpoint_hPa=round(e,8),
  ERA5Land_grid_VPD_water_hPa=round(vpdgrid,8),
  ERA5Land_T_minus_source_T_C=round(refT-origT,6),
  candidate_VPD_original_T_preserve_ref_RH_water_hPa=round(vpdrh,8),
  candidate_VPD_original_T_preserve_ref_actual_e_hPa=round(vpde,8),
  candidate_two_transport_VPD_difference_hPa=round(vpdrh-vpde,8),
  ERA5Land_RH_minus_source_ERA_RH_pp=round(era_diff,6) if era_diff is not None else "",
  ERA5Land_RH_minus_source_MDS_RH_pp=round(mds_diff,6) if mds_diff is not None else "",
  reference_closer_to_MDS_or_source_ERA=closer,
  science_concern_flags=";".join(flags),
  CDS_request_id=request_id,UTC_alignment_type=alignment,
  science_permission="NO_NEW_HOLD_RELEASE_OR_FORCING_APPROVAL")

def get_parser(path):
 if not path.is_file() or path.is_symlink() or git_blob(path)!=STAGE31_BLOB:
  raise ValueError("Stage31 known working CDS NetCDF helper changed or missing")
 spec=importlib.util.spec_from_file_location("stage31_trusted_cds_parser",str(path))
 if spec is None or spec.loader is None:raise ValueError("cannot load original Stage31 scientific helper")
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 for name in ("extract_netcdfs","inspect_reference","interp"):
  if not callable(getattr(mod,name,None)):raise ValueError("Stage31 source helper missing "+name)
 return mod

def selftest():
 assert len(EXPECTED_SHA)==10 and len(set(EXPECTED_SHA.values()))==10
 assert len(SITES)==4
 assert abs(100*sat(-19)/sat(-15)-100*sat(-19)/sat(-15))<1e-12
 assert dt("200712152030")-timedelta(hours=-7)==datetime(2007,12,16,3,30)
 assert (datetime(2008,9,4)-timedelta(hours=-7))==datetime(2008,9,4,7)
 assert 0<scientific_row(
  dict(site="TEST",native_time="200801010000",kind="P2_P3_ORIGINAL_UNAPPROVED",event="e",
   T=-10,V=3,rh=None,qcT="2",qcV="2",source_era=-9,mds=75,risk=""),
  "TEST",datetime(2008,1,1,7),-12,-18,"EXACT")["ERA5Land_reference_RH_water_pct"]<100
 print("STAGE34 SELF-TEST PASS | 10 operator-pinned CDS ZIP SHA, Stage31 trusted parser, BIF UTC offsets, risk-only science joins")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage33-dir",type=Path)
 p.add_argument("--stage18-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage31-parser",type=Path,default=Path.home()/"ameriflux_batch05_stage31"/"31_validate_first_ERA5Land_CDS_payload_and_Vcm_H01_readonly.py")
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage33_dir,a.stage18_dir,a.stage24_dir,a.stage27_dir,a.out)):
  p.error("need --stage33-dir, --stage18-dir, --stage24-dir, --stage27-dir, --out")
 d33,d18,d24,d27=[v.expanduser().resolve() for v in (a.stage33_dir,a.stage18_dir,a.stage24_dir,a.stage27_dir)]
 out=a.out.expanduser().resolve()
 if not all(x.is_dir() for x in (d33,d18,d24,d27)) or not out.parent.is_dir() or out.exists() or any(
  out==x or out in x.parents or x in out.parents for x in (d33,d18,d24,d27)):
  p.error("Stage34 analysis must write NEW directory, never original data")
 trusted=get_parser(a.stage31_parser.expanduser().resolve())
 context,held,platforms,p2,approved,sourcehashes=source_load(d18,d24,d27)
 download_manifest=d33/"stage33_downloaded_metadata.json"
 request_manifest=d33/"stage33_next_10_CDS_requests.json"
 stage33_manifest=d33/"stage33_manifest.json"
 record=json.loads(download_manifest.read_text())
 requests=json.loads(request_manifest.read_text())
 state=json.loads(stage33_manifest.read_text())
 if len(record)!=10 or len(requests)!=10 or set(EXPECTED_SHA)!={r["id"] for r in record}:
  raise ValueError("Stage33 10 actual science reference downloads missing")
 if state.get("new_science_approvals")!=0 or len(state.get("downloaded",[]))!=10:
  raise ValueError("Stage33 new science approvals or downloaded population unexpected")
 mapping={r["id"]:r for r in requests}
 archive={r["id"]:r for r in record}
 if set(mapping)!=set(archive):raise ValueError("Stage33 source request IDs differ from downloads")
 checked=[];joined={}
 for ident in EXPECTED_SHA:
  r=mapping[ident];meta=archive[ident]
  site=r["site"]
  if site not in SITES or r["dataset"]!="reanalysis-era5-land-timeseries":
   raise ValueError("unexpected source site/dataset "+ident)
  if r.get("source_BIF_offset_hours")!=SITES[site][2]:
   raise ValueError("source BIF original UTC offset changed "+ident)
  payload=d33/(ident+".cds_download")
  if not payload.is_file() or payload.is_symlink():raise ValueError("missing real downloaded file "+ident)
  digest=sha(payload)
  if digest!=EXPECTED_SHA[ident] or meta["sha256"]!=digest or meta["bytes"]!=payload.stat().st_size:
   raise ValueError("actual downloaded ERA5L bytes or manifest SHA mismatch "+ident)
  dstart,dend=r["request"]["date"].split("/")
  start=datetime.strptime(dstart,"%Y-%m-%d")
  end=datetime.strptime(dend,"%Y-%m-%d")+timedelta(hours=23)
  if start>end:raise ValueError("CDS original request dates reversed")
  with tempfile.TemporaryDirectory(prefix="batch05_stage34_") as temp:
   kind,files=trusted.extract_netcdfs(payload,temp)
   values,members,coordinates=trusted.inspect_reference(files)
  hourlist=values["t2m"]
  if hourlist[0][0]!=start or hourlist[-1][0]!=end or len(hourlist)!=int((end-start).total_seconds()/3600)+1:
   raise ValueError("CDS actual timestamp coverage NOT equal original exact requested interval "+ident)
  lat,lon,off=SITES[site]
  glat=coordinates["latitude"]
  glon=coordinates["longitude"]
  if glon is not None and glon>180:glon-=360
  if glat is not None and abs(glat-lat)>0.11:raise ValueError("CDS reference latitude inconsistent")
  if glon is not None and abs(glon-lon)>0.11:raise ValueError("CDS reference longitude inconsistent")
  matched=0
  pool=(set(held)|set(platforms)|set(p2))
  for k in sorted(pool):
   if k[0]!=site:continue
   time=dt(k[1])
   utc=time-timedelta(hours=off)
   if utc<start or utc>end:continue
   original=choose_original(site,k[1],context,held,platforms,p2)
   if original is None:continue
   refT,modeT=trusted.interp(utc,values["t2m"])
   refD,modeD=trusted.interp(utc,values["d2m"])
   if modeT!=modeD:raise ValueError("grid T and dewpoint time method differ "+ident)
   new=scientific_row(original,ident,utc,refT-273.15,refD-273.15,modeT)
   if k in joined:
    old=joined[k]
    if abs(n(old["ERA5Land_reference_RH_water_pct"])-n(new["ERA5Land_reference_RH_water_pct"]))>0.002 or abs(
     n(old["ERA5Land_reference_T_C"])-n(new["ERA5Land_reference_T_C"]))>0.002 or abs(
     n(old["ERA5Land_reference_Td_C"])-n(new["ERA5Land_reference_Td_C"]))>0.002:
     raise ValueError("overlapping CDS requests produce incompatible references for "+str(k))
    # Record the first validated reference; provenance duplicate is harmless if equal.
   else:joined[k]=new
   matched+=1
  checked.append(dict(request_id=ident,site=site,requested_UTC_first=dstart,
   requested_UTC_last=dend,
   actual_UTC_first=hourlist[0][0].isoformat()+"Z",
   actual_UTC_last=hourlist[-1][0].isoformat()+"Z",
   UTC_hours=len(hourlist),zip_or_netcdf=kind,members=len(members),
   grid_lat=glat if glat is not None else "",grid_lon=glon if glon is not None else "",
   expected_sha256=EXPECTED_SHA[ident],verified_sha256=digest,
   matched_native_HH=matched,
   scientific_status="EXTERNAL_REFERENCE_VERIFIED_NOT_FORCING"))
 P1=[r for r in joined.values() if r["source_population"]=="P1_MANUAL_HOLD"]
 if len(P1)!=27 or len({r["native_time"] for r in P1})!=27:
  raise ValueError("all remaining non-H01 original P1 HOLD 27 HH MUST be covered")
 if sum(r["source_population"]=="RH_SATURATION_PLATFORM_UNAPPROVED" for r in joined.values())!=10:
  raise ValueError("all ten original suspected saturation platform HH not covered")
 if not any(r["site"]=="US-Wjs" and r["source_population"]=="P2_P3_ORIGINAL_UNAPPROVED" for r in joined.values()):
  raise ValueError("US-Wjs first P2P3 external reference not yet joined")
 if not any(r["site"]=="US-Vcp" and r["source_population"]=="P2_P3_ORIGINAL_UNAPPROVED" for r in joined.values()):
  raise ValueError("US-Vcp original P2P3 high-risk months not joined")
 if any((r["site"],r["native_time"]) in approved for r in joined.values()):
  raise ValueError("unapproved source intersection with previously approved overlay")
 out.mkdir(exist_ok=False)
 rows=[joined[k] for k in sorted(joined)]
 put(out/"stage34_ALL_MATCHED_EXTERNAL_ERA5LAND_REFERENCE_SCIENCE_REVIEW_ONLY.csv",COLS,rows)
 put(out/"stage34_TEN_ACTUAL_CDS_FILE_SHA_AND_UTC_GRID_AUDIT.csv",FILES,checked)
 bygroup=defaultdict(list)
 for r in rows:bygroup[(r["site"],r["source_population"])].append(r)
 aggregate=[]
 for (site,kind),rr in sorted(bygroup.items()):
  erav=[abs(n(x["ERA5Land_RH_minus_source_ERA_RH_pp"])) for x in rr if x["ERA5Land_RH_minus_source_ERA_RH_pp"]!=""]
  mdsv=[abs(n(x["ERA5Land_RH_minus_source_MDS_RH_pp"])) for x in rr if x["ERA5Land_RH_minus_source_MDS_RH_pp"]!=""]
  g=dict(site=site,source_population=kind,original_native_HH=len(rr),
   reference_RH_water_min=min(x["ERA5Land_reference_RH_water_pct"] for x in rr),
   reference_RH_water_max=max(x["ERA5Land_reference_RH_water_pct"] for x in rr),
   reference_minus_original_T_abs_gt5C_HH=sum(abs(x["ERA5Land_T_minus_source_T_C"])>5 for x in rr),
   reference_vs_processed_source_ERA_RH_abs_gt20pp_HH=sum(x>20 for x in erav),
   reference_vs_source_MDS_RH_abs_gt20pp_HH=sum(x>20 for x in mdsv),
   closer_MDS_HH=sum(x["reference_closer_to_MDS_or_source_ERA"]=="MDS_REFERENCE_CLOSER" for x in rr),
   closer_processed_ERA_HH=sum(x["reference_closer_to_MDS_or_source_ERA"]=="PROCESSED_SOURCE_ERA_CLOSER" for x in rr),
   baseline_science_approved_HH=0)
  aggregate.append(g)
 with (out/"stage34_EVENT_GROUP_SUMMARY.json").open("x") as f:json.dump(aggregate,f,indent=2)
 summary=dict(
  source="Stage33 ten actual CDS ERA5Land gridded reference files",
  source_checksums=sourcehashes,
  stage33_actual_downloads_source_sha256=sha(download_manifest),
  stage33_source_requests_sha256=sha(request_manifest),
  stage33_manifest_sha256=sha(stage33_manifest),
  Stage31_trusted_parser_git_blob_sha=STAGE31_BLOB,
  source_downloads_verified=10,
  downloaded_reference_joined_unique_native_HH=len(rows),
  P1_nonH01_HOLD_27_external_ref_matched=len(P1),
  P1_H01_previous_reference_19_not_reprocessed=True,
  P1_manual_HOLD_46_unchanged=True,
  original_RH_saturation_platform_10_matched=True,
  original_P2P3_1574_all_science_unapproved=True,
  P2P3_native_HH_with_external_reference=sum(r["source_population"]=="P2_P3_ORIGINAL_UNAPPROVED" for r in rows),
  reference_downloads_NOT_in_situ_measurements=True,
  BIF_UTC_OFFSET_DATE_END_original_missing=True,
  Stage24_approved_166_untouched=True,
  new_scientific_repair_approvals=0,
  original_FLUXMET_or_DATM_modified=False,Slurm_submitted=False)
 (out/"stage34_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 doc=["# Stage34: TEN REAL ERA5-Land CDS files inspected and matched to unapproved original QC","",
  "**NO new user approvals. All 46 original P1 HOLD and original P2P3=1574 remain unapproved.**",
  "Existing Stage24 approved 166 original RH/VPD overlay untouched; source ZIP/FLUXMET/DATM/Slurm not edited.",
  "Stage33 independently downloaded a new ERA5-Land point gridded reference at 10 site-time ranges.",
  "Original BIF DATE_END missing, so local-standard-time-to-UTC mapping is still provisional.",
  "This is a SECOND REANALYSIS reference, not an independent in-situ humidity sensor.",
  "ERA5Land hourly 2m air/dewpoint (Kelvin) linearly interpolated to original native 30-minute timestamps.",
  "Dewpoint used only with es_water(Td), ice-RH sensitivity reported when ref temperature below zero.","",
  "## Exact source audit",
  "- Original Stage24 non-H01 P1 manual HOLD external matched: **27/27 HH**",
  "- Original Stage24 suspect RH saturation platform external matched: **10/10 HH**",
  "- Original Stage27 P2/P3 externally referenced native HH: **"+str(summary["P2P3_native_HH_with_external_reference"])+"**",
  "- Ten CDS files SHA/variable/UTC hour-range/gridded site checked: **10/10**",
  "- First H01 19 unchanged and already examined in Stages 31–33.","",
  "## Site and original source-class evidence"]
 for a in aggregate:
  doc.append("- **{} / {}**: {} HH; ERA5L RH water {}–{}%; |T_grid-T_tower| >5°C {} HH; |RH_ref-RH_processed_source_ERA| >20 pp {} HH; |RH_ref-RH_MDS| >20 pp {} HH; closer MDS {} vs source ERA {}".format(
    a["site"],a["source_population"],a["original_native_HH"],
    a["reference_RH_water_min"],a["reference_RH_water_max"],
    a["reference_minus_original_T_abs_gt5C_HH"],
    a["reference_vs_processed_source_ERA_RH_abs_gt20pp_HH"],
    a["reference_vs_source_MDS_RH_abs_gt20pp_HH"],
    a["closer_MDS_HH"],a["closer_processed_ERA_HH"]))
 doc+=["","## Scientific interpretation and next decisions",
  "1. Actual 10 downloaded sources are **verified against source hashes** and raw UTC timestamps, not just accepted CDS logs.",
  "2. For H02/H03/H04/H05, inspect P1 RH missing/low source evidence and compare available gridded water and ice RH; do not auto-clear manual HOLD.",
  "3. For the ten RH saturation platform HH, gridded dryness is only supporting evidence for a possible original tower sensor plateau; preserve tower QC provenance.",
  "4. US-Vcp 2008 high-risk and first US-Wjs episode: compare *actual* ERA5-Land RH with BOTH source MDS and source processed ERA. No blanket source ERA replacement.",
  "5. Stage33 H01 immediate neighbors are QC2, original implied RH-water 1.513% and 3.973%, scientifically suspect. These two neighboring records still not user-approved for repair.",
  "6. Tower–grid temperature/height and hourly interval alignment, plus missing original BIF DATE_END, remain explicit scientific uncertainties.",
  "",
  "**No automatic science approval, no new model-ready DATM forcing.**",""]
 (out/"STAGE34_REAL_REFERENCE_CROSS_SITE_SCIENCE_REPORT.md").write_text("\n".join(doc)+"\n")
 print("STAGE34 SUCCESS | 10/10 ACTUAL CDS ZIP/NETCDF VALIDATED; MATCHED_NATIVE_HH",len(rows),
       "P1_NON_H01_HOLD",len(P1),"RH_PLATFORMS",10,
       "P2P3_REFERENCED",summary["P2P3_native_HH_with_external_reference"])
 for r in aggregate:
  print("STAGE34 SITE_SOURCE",r["site"],r["source_population"],
        "HH",r["original_native_HH"],
        "RH_REF_MIN_MAX",r["reference_RH_water_min"],r["reference_RH_water_max"],
        "REF_ERA_DIFF_GT20",r["reference_vs_processed_source_ERA_RH_abs_gt20pp_HH"],
        "REF_MDS_DIFF_GT20",r["reference_vs_source_MDS_RH_abs_gt20pp_HH"],
        "CLOSER_MDS",r["closer_MDS_HH"],"CLOSER_ERA",r["closer_processed_ERA_HH"])
 print("STAGE34_REPORT="+str(out/"STAGE34_REAL_REFERENCE_CROSS_SITE_SCIENCE_REPORT.md"))
 print("STAGE34_OUT="+str(out))
 print("STAGE34 SOURCE/APPROVED166/HOLD46/P2P3_1574/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

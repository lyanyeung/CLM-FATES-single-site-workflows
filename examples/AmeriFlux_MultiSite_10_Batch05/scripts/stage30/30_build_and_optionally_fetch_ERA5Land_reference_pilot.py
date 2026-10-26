#!/usr/bin/env python3
"""Batch05 Stage30: build exact research-only ERA5-Land hourly T/dewpoint
CDS time-series request plan from original BIF native-to-UTC *candidates*.

Important: AmeriFlux original BIF UTC_OFFSET_DATE_END absent; -7 NM / -6 WCr
are strongly supported, *provisional* offsets, NOT metadata-complete verified
time mappings. All 27 pilot windows are conditional research requests only.

Default --run-plan ONLY: produces request JSON / window coverage / scientific
gates; NO network. Optional --fetch --acknowledge-provisional-bif-offsets
downloads a bounded number of files via user-owned CDS API (license accepted,
.cdsapirc preconfigured). Does not parse/model-assimilate downloads.
Never modifies original FLUXMET, Stage24 approved 166, 46 P1 HOLD,
Stage27 1,574 unapproved P2/P3, native QC, CIME or Slurm.
"""
import argparse,csv,hashlib,json,math
from collections import defaultdict,Counter
from datetime import datetime,timedelta
from calendar import monthrange
from pathlib import Path

DATASET="reanalysis-era5-land-timeseries"
VARIABLES=("2m_temperature","2m_dewpoint_temperature")
SITE={
 "US-Vcp":(35.8641,-106.5965,2501,"https://ameriflux.lbl.gov/sites/siteinfo/US-Vcp"),
 "US-Wjs":(34.4258,-105.8617,1931,"https://ameriflux.lbl.gov/sites/siteinfo/US-Wjs"),
 "US-Vcm":(35.8885,-106.5322,3043,"https://ameriflux.lbl.gov/sites/siteinfo/US-Vcm"),
 "US-WCr":(45.8058,-90.0795,520,"https://ameriflux.lbl.gov/sites/siteinfo/US-WCr")
}
NEED29={"source_event_type","site","episode_or_event","native_start","native_end",
 "native_context_start","native_context_end",
 "BIF_UTC_OFFSET_hours","UTC_context_start_CANDIDATE",
 "UTC_context_end_CANDIDATE","matching_GROUP_IDs",
 "UTC_OFFSET_group_coverage","ERA5_Land_request_status"}
NEEDG={"site","UTC_OFFSET_hours","group_UTC_OFFSET_hours"} # NOT USED
NEED28={"source_event_type","site","episode_or_event","native_start",
 "native_end","native_window_start_minus6h","native_window_end_plus6h"}
NEEDG29={"site","group_id","UTC_OFFSET_hours","UTC_OFFSET_DATE_START",
 "UTC_OFFSET_DATE_END","group_metadata_status"}
NEEDM29={"site","all_group_offsets_hours","group_UTC_offset_conflict"}
WCOL=("site","event","source_event_type","BIF_offset_hours",
 "BIF_group_date_coverage","native_context_start","native_context_end",
 "UTC_context_start_candidate","UTC_context_end_candidate",
 "UTC_hourly_alignment","CDS_request_id","reference_approval_status")
RCOL=("CDS_request_id","site","latitude","longitude","tower_elevation_m",
 "UTC_request_start_date","UTC_request_end_date",
 "BIF_offset_hours","coverage_status","original_events",
 "dataset","variables","data_format","API_request_JSON",
 "download_status")
def parse(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("malformed original date "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def label(d):return d.strftime("%Y%m%d%H%M")
def datestr(d):return d.strftime("%Y-%m-%d")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("missing regular input "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  rr=csv.DictReader(f);cols=rr.fieldnames or []
  if not required.issubset(cols) or len(cols)!=len(set(cols)):
   raise ValueError("bad original report headers "+str(p))
  rows=list(rr)
 if any(None in row or any(v is None for v in row.values()) for row in rows):
  raise ValueError("malformed source csv row "+str(p))
 return rows
def offset(s):
 try:v=float(s)
 except(ValueError,TypeError):raise ValueError("unknown source BIF offset "+repr(s))
 if not math.isfinite(v) or abs(v)>14 or abs(v*60-round(v*60))>1e-8:
  raise ValueError("bad BIF offset")
 return v
def months_cover(a,b):
 if b<a:raise ValueError("bad UTC window")
 cursor=datetime(a.year,a.month,1);last=datetime(b.year,b.month,1)
 while cursor<=last:
  first=datetime(cursor.year,cursor.month,1)
  lastday=monthrange(cursor.year,cursor.month)[1]
  end=datetime(cursor.year,cursor.month,lastday,23,59)
  yield (cursor.year,cursor.month,max(a,first),min(b,end))
  cursor=(cursor.replace(year=cursor.year+1,month=1) if cursor.month==12
          else cursor.replace(month=cursor.month+1))
def selftest():
 assert list(months_cover(datetime(2008,1,31,23),datetime(2008,2,1,1)))[0][:2]==(2008,1)
 assert len(list(months_cover(datetime(2008,1,31,23),datetime(2008,2,1,1))))==2
 assert label(parse("200805241500")-timedelta(hours=-7))=="200805242200"
 assert label(parse("202508250930")-timedelta(hours=-6))=="202508251530"
 print("STAGE30 SELF-TEST PASS | BIF local-to-UTC arithmetic, month crossing, site-specific offsets, no auto writes")
def get_inputs(d29,d28):
 win29=d29/"stage29_27_PILOT_NATIVE_TO_UTC_CANDIDATE_WINDOWS.csv"
 g29=d29/"stage29_ORIGINAL_BIF_UTC_OFFSET_ALL_GROUPS.csv"
 m29=d29/"stage29_FOUR_SITE_BIF_METADATA_GATE.csv"
 win28=d28/"stage28_27_TOP_EPISODE_HOLD_PLATEAU_NATIVE_WINDOWS.csv"
 info28=d28/"stage28_SITE_METADATA_AND_UTC_OFFSET_GATES.csv"
 stat29=json.loads((d29/"stage29_summary.json").read_text())
 if stat29.get("events")!=27 or stat29.get("ERA5_Land_downloaded") is not False:
  raise ValueError("Stage29 full 27-event source cohort changed")
 w29=read(win29,NEED29)
 g=read(g29,NEEDG29)
 sites=read(m29,NEEDM29)
 w28=read(win28,NEED28)
 i28=read(info28,{"site","official_site_lat","official_site_lon","official_site_elev_m"})
 if len(w29)!=27 or len(w28)!=27 or len(g)!=6 or len(sites)!=4:
  raise ValueError("Stage28/29 source populations 27/27/6/4 changed")
 if {(x["site"],x["episode_or_event"]) for x in w29} != {(x["site"],x["episode_or_event"]) for x in w28}:
  raise ValueError("Stage28 original native windows changed")
 if Counter(x["source_event_type"] for x in w29)!=Counter({
   "P2_P3_TOP_RISK_PILOT":20,"P1_MANUAL_HOLD_UNCHANGED":5,
   "RH_SATURATION_PLATFORM_UNAPPROVED":2}):
  raise ValueError("Stage29 native window categories changed")
 a={x["site"]:x for x in sites}
 if set(a)!=set(SITE) or any(x["group_UTC_offset_conflict"]!="False" for x in sites):
  raise ValueError("BIF UTC offset conflict or unexpected sites")
 expect={"US-Vcp":-7.0,"US-Wjs":-7.0,"US-Vcm":-7.0,"US-WCr":-6.0}
 for site,v in expect.items():
  offs={offset(x["UTC_OFFSET_hours"]) for x in g if x["site"]==site}
  if offs!={v} or a[site]["all_group_offsets_hours"]!=str(v):
   raise ValueError("BIF offset values changed "+site)
 # Original source start/end effective-dated records: CLOSED_DATED is absent.
 if any(x["UTC_OFFSET_DATE_END"] for x in g):
  raise ValueError("BIF offset end-date evidence changed: reassess science")
 if {x["site"] for x in i28}!={"US-Vcp","US-Wjs","US-Vcm"}:
  raise ValueError("Stage28 three site locations changed")
 for x in i28:
  lat,lon,elev,_=SITE[x["site"]]
  if abs(float(x["official_site_lat"])-lat)>0.0001 or abs(float(x["official_site_lon"])-lon)>0.0001:
   raise ValueError("original Stage28 public site latitude longitude mismatch")
 return w29,g,sites,win29,g29,m29,win28,info28

def plan(windows):
 wout=[];monthgroups=defaultdict(lambda:{"minstart":None,"maxend":None,"windows":[],"cov":set()})
 expectedcov={"OPEN_ENDED_START_DATED_REVIEW","ONLY_UNDATED_OR_END_ONLY_GROUP_REVIEW"}
 for r in windows:
  s=r["site"];off=offset(r["BIF_UTC_OFFSET_hours"])
  if r["UTC_OFFSET_group_coverage"] not in expectedcov:
   raise ValueError("unexpected Stage29 BIF date coverage: reassess source "+s)
  rawstart=parse(r["native_context_start"]);rawend=parse(r["native_context_end"])
  if rawend<rawstart:raise ValueError("reversed native window")
  utcstart=rawstart-timedelta(hours=off)
  utcend=rawend-timedelta(hours=off)
  if (label(utcstart),label(utcend))!=(r["UTC_context_start_CANDIDATE"],r["UTC_context_end_CANDIDATE"]):
   raise ValueError("Stage29 UTC candidate arithmetic changed "+s)
  for year,month,first,end in months_cover(utcstart,utcend):
   group=monthgroups[s,year,month]
   group["minstart"]=min(first,group["minstart"]) if group["minstart"] else first
   group["maxend"]=max(end,group["maxend"]) if group["maxend"] else end
   group["windows"].append(r["episode_or_event"])
   group["cov"].add(r["UTC_OFFSET_group_coverage"])
  wout.append(dict(site=s,event=r["episode_or_event"],
   source_event_type=r["source_event_type"],
   BIF_offset_hours=off,
   BIF_group_date_coverage=r["UTC_OFFSET_group_coverage"],
   native_context_start=r["native_context_start"],
   native_context_end=r["native_context_end"],
   UTC_context_start_candidate=label(utcstart),
   UTC_context_end_candidate=label(utcend),
   UTC_hourly_alignment="HOUR_BOUNDARIES_ONLY;FLUXNET_HALF_HOUR_NOT_RESAMPLED",
   CDS_request_id="SEE_REQUEST_BY_SITE_UTC_MONTH",
   reference_approval_status="RESEARCH_REVIEW_ONLY_BIF_DATE_END_MISSING"))
 manifest=[];raw=[]
 for (site,year,month),g in sorted(monthgroups.items()):
  lat,lon,elev,_=SITE[site]
  # An extra calendar day on each side supports unambiguous hour bracketing.
  start=(g["minstart"]-timedelta(days=1)).date()
  end=(g["maxend"]+timedelta(days=1)).date()
  request={"variable":list(VARIABLES),
    "date":[start.isoformat(),end.isoformat()],
    "location":{"longitude":lon,"latitude":lat},
    "data_format":"netcdf"}
  rid="ERA5L_"+site.replace("-","_")+"_"+str(year)+str(month).zfill(2)
  raw.append(dict(id=rid,site=site,latitude=lat,longitude=lon,
       tower_elevation_m=elev,utc_start_date=start.isoformat(),
       utc_end_date=end.isoformat(),
       source_BIF_offset_hours= -7 if site in ("US-Vcp","US-Vcm","US-Wjs") else -6,
       BIF_date_coverage=";".join(sorted(g["cov"])),
       native_events=sorted(set(g["windows"])),
       dataset=DATASET,request=request,source="Stage29_PROVISIONAL_NOT_DATE_END_VERIFIED",
       status="PLANNED_NOT_DOWNLOADED"))
  manifest.append(dict(CDS_request_id=rid,site=site,latitude=lat,longitude=lon,
   tower_elevation_m=elev,UTC_request_start_date=start.isoformat(),
   UTC_request_end_date=end.isoformat(),
   BIF_offset_hours=raw[-1]["source_BIF_offset_hours"],
   coverage_status=raw[-1]["BIF_date_coverage"],
   original_events=";".join(sorted(set(g["windows"]))),
   dataset=DATASET,variables=";".join(VARIABLES),
   data_format="netcdf",API_request_JSON=json.dumps(request,sort_keys=True),
   download_status="NOT_DOWNLOADED"))
 return wout,manifest,raw

def writetable(p,fields,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise");w.writeheader();w.writerows(rows)
def fetch_manifest(raw,out,max_fetch):
 if max_fetch<1 or max_fetch>len(raw):
  raise ValueError("max_fetch out of range")
 # Explicit CLI flag acknowledgement + user configured private CDS credentials
 # required; no tokens are logged or stored.
 import cdsapi
 client=cdsapi.Client()
 downloaded=[]
 for item in raw[:max_fetch]:
  dest=out/(item["id"]+".cds_download")
  if dest.exists():raise ValueError("refuse overwrite of downloaded source "+str(dest))
  client.retrieve(item["dataset"],item["request"],str(dest))
  if not dest.is_file() or dest.stat().st_size==0:
   raise ValueError("CDS returned missing or zero-byte file "+item["id"])
  downloaded.append({"request_id":item["id"],"file":str(dest),
    "size_bytes":dest.stat().st_size,"sha256":sha(dest),
    "data_encoding":"UNINSPECTED_CDS_RESPONSE_MAY_BE_ZIP_OR_NETCDF",
    "not_approved_for_forcing":True})
  print("STAGE30 FETCH_SUCCESS",item["id"],"BYTES",dest.stat().st_size,
        "SHA256",downloaded[-1]["sha256"],flush=True)
 return downloaded

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage29-dir",type=Path)
 p.add_argument("--stage28-dir",type=Path)
 p.add_argument("--out",type=Path)
 p.add_argument("--fetch",action="store_true")
 p.add_argument("--acknowledge-provisional-bif-offsets",action="store_true")
 p.add_argument("--max-fetch",type=int,default=1,
   help="When --fetch is explicitly enabled, retrieve at most this many site/month requests (default 1)")
 a=p.parse_args()
 if a.self_test:selftest();return
 if a.stage29_dir is None or a.stage28_dir is None or a.out is None:
  p.error("Need --stage29-dir --stage28-dir --out")
 if a.fetch and not a.acknowledge_provisional_bif_offsets:
  p.error("--fetch requires explicit --acknowledge-provisional-bif-offsets; BIF date_end is missing")
 if a.acknowledge_provisional_bif_offsets and not a.fetch:
  p.error("--acknowledge-provisional-bif-offsets applies only with explicit --fetch")
 d29=a.stage29_dir.expanduser().resolve()
 d28=a.stage28_dir.expanduser().resolve()
 out=a.out.expanduser().resolve()
 if (not d29.is_dir() or not d28.is_dir() or out.exists() or not out.parent.is_dir()
    or any(out==d or out in d.parents or d in out.parents for d in (d29,d28))):
  p.error("Stage30 must only write to new disjoint output directory")
 windows,groups,sites,f29,fg,fm,f28,fi=get_inputs(d29,d28)
 windowlist,man,request_json=plan(windows)
 if len(windowlist)!=27 or len(man)<1 or not all(x["original_events"] for x in man):
  raise ValueError("Stage30 pilot request completeness failed")
 out.mkdir(exist_ok=False)
 writetable(out/"stage30_27_NATIVE_UTC_EVIDENCE_WINDOWS.csv",WCOL,windowlist)
 writetable(out/"stage30_CDS_ERA5L_SITE_MONTH_REQUEST_PLAN.csv",RCOL,man)
 (out/"stage30_CDS_REQUESTS_DRYRUN.json").write_text(json.dumps(request_json,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 summary=dict(status="RESEARCH_ONLY_BIF_START_DATE_OR_UNDATED_AND_NO_DATE_END",
    pilot_windows=27,cds_site_month_requests_planned=len(man),
    science_approvals_new=0,source_stage29_group_count=6,
    stage24_approved_166_unchanged=True,
    stage24_P1_manual_HOLD_46_unchanged=True,
    source_P2P3_unapproved_1574_unchanged=True,
    original_FLUXMET_changed=False,DATM_changed=False,Slurm_submitted=False,
    BIF_UTC_OFFSET_DATE_END_missing=True,
    native_timezone_DST_applied=False,ERA5_Land_temporal_resolution="hourly_UTC",
    source_SHA256={"Stage29_27_UTC_windows":sha(f29),
      "Stage29_6_BIF_groups":sha(fg),"Stage29_4_site_metadata":sha(fm),
      "Stage28_27_native_events":sha(f28),"Stage28_original_site_metadata":sha(fi)},
    dataset=DATASET,source_external_reference="CDS ERA5-Land, NOT native source processed ERA",
    downloaded=[],
    notes="Download requires CDS licence acceptance and external API configured; metadata offsets provisional, not science-approved")
 report=["# Stage30 ERA5-Land reference pilot: research-only CDS acquisition plan","",
    "**Only native LST→UTC pilot time candidates are established; original BIF lacks UTC_OFFSET_DATE_END.**",
    "US-Vcp/Vcm/Wjs have matching original BIF UTC_OFFSET=-7; WCr has -6.",
    "No local DST adjustment. Stage30 prepares exact source-backed small site/month requests,",
    "with a calendar-day buffer for 30-minute interval bracketing against hourly UTC reanalysis.",
    "The time-series CDS endpoint returns nearest 0.1-degree grid cell; this is not a tower",
    "observation and must be checked for significant elevation/temperature mismatch.",
    "All 166 user-approved Stage24 overlay, 46 manual P1 holds, 1574 P2/P3 unapproved and",
    "10 suspect RH plateau HH remain unchanged.","",
    "## Planned reference requests: {}".format(len(man)),
    "| Request | Site | UTC first date | UTC last date | native events |",
    "|---|---|---|---|---|"]
 for row in man:
  report.append("| {} | {} | {} | {} | {} |".format(
    row["CDS_request_id"],row["site"],row["UTC_request_start_date"],
    row["UTC_request_end_date"],len(row["original_events"].split(";"))))
 report+=["",
  "## Optional EXPLICIT external download — only after reading the above plan",
  "1. Sign in to CDS and accept the ERA5-Land time-series product licence in your own account.",
  "2. Install cdsapi>=0.7.7 in a permitted networking environment, configure ~/.cdsapirc privately.",
  "3. Use the same command again with a NEW --out directory and flags:",
  "   --fetch --acknowledge-provisional-bif-offsets --max-fetch 1",
  "4. Verify actual downloaded payload (NetCDF or compressed archive), UTC time axis,",
  "   Kelvin temperature/dewpoint variables, grid elevation and nearest point.",
  "5. Do NOT integrate into DATM or release new science-approved RH/VPD from Stage30.",
  "6. If CDS API rejects request options, build a request in the CDS download form and",
  "   compare its Show API request code; do not silently change scientific dataset.",""]
 (out/"STAGE30_SOURCE_TIME_AND_CDS_PILOT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
 if a.fetch:
  try:
   summary["downloaded"]=fetch_manifest(request_json,out,a.max_fetch)
  finally:
   (out/"stage30_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 else:
  (out/"stage30_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("STAGE30 SUCCESS | 27 windows; CDS site-month plans",len(man),
       "DOWNLOADS",len(summary["downloaded"]),"RESEARCH_ONLY")
 for row in man:
  print("STAGE30 CDS_PLAN",row["CDS_request_id"],row["UTC_request_start_date"],
    row["UTC_request_end_date"],"EVENTS",len(row["original_events"].split(";")),
    "OFFSET",row["BIF_offset_hours"])
 print("STAGE30_PLAN="+str(out/"STAGE30_SOURCE_TIME_AND_CDS_PILOT.md"))
 print("STAGE30_OUT="+str(out))
 print("STAGE30 ORIGINAL/APPROVED166/HOLD46/P2P3_1574/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

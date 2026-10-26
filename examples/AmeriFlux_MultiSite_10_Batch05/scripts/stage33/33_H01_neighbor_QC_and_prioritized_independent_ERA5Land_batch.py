#!/usr/bin/env python3
"""Batch05 Stage33: source-based H01 adjacency decision gate + REAL next ERA5-Land
data requests for remaining H02/H03/H04/H05, two RH plateaus, three high-risk
Vcp 2008 months, and one ORIGINAL highest-risk Wjs P2/P3 episode.

Default read-only PLAN. With EXPLICIT --fetch --acknowledge-provisional-bif-offsets
--max-fetch N, fetch N new CDS reference files to NEW Stage33 report folder.
No source originals, approved166, held46, P2P3_1574, DATM, Slurm edits.
Missing original BIF UTC_OFFSET_DATE_END is clearly labeled PROVISIONAL.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter

REPO_RELEASE="Batch05_stage33_20261026_external_reference"
DATASET="reanalysis-era5-land-timeseries"
VARS=("2m_temperature","2m_dewpoint_temperature")
WJS_LAT=34.4258
WJS_LON=-105.8617
WJS_ELEV=1931
# Safe order: 4 remaining P1 HOLD windows, 2 RH platforms,
# US-Vcp high-risk 2008 conflict months, one Wjs high-risk P2/P3 episode.
NINE=[
 "ERA5L_US_Vcm_200802","ERA5L_US_Vcm_200812",
 "ERA5L_US_Vcm_201512","ERA5L_US_Vcp_201101",
 "ERA5L_US_Vcm_202510","ERA5L_US_WCr_202508",
 "ERA5L_US_Vcp_200804","ERA5L_US_Vcp_200805","ERA5L_US_Vcp_200806"
]
REQ_STAGE18={"site","time_native","TA_F_C","VPD_F_hPa","RH_original_pct",
 "TA_F_QC","VPD_F_QC","TA_ERA_C","VPD_ERA_hPa",
 "ERA_RH_Magnus_water_pct"}
REQ_STAGE32={"site","native_time","ERA5L_RH_over_water_pct",
 "TOWER_WATER_VPD_if_reference_RH_water_preserved_hPa",
 "TOWER_WATER_VPD_if_reference_actual_e_preserved_hPa"}
REQ_EP={"site","episode_id","original_native_start","original_native_end",
 "review_priority_rank","unapproved_HH"}
REQ_APPROVED={"site","native_time","modified_VPD_hPa"}
REQ_HELD={"site","native_time","hold_reason"}
NEIGHBOR_COLS=("site","native_time","relative_to_H01",
 "source_original_T_C","source_original_VPD_hPa",
 "source_original_RH_pct","RH_implied_original_T_and_VPD_water_pct",
 "source_original_T_QC","source_original_VPD_QC",
 "source_processed_ERA_RH_pct",
 "source_selected_status","currently_selected_VPD_hPa",
 "has_RH_below_1pct_or_negative","is_low_RH_plausibility_gate",
 "repair_permission")
REQ_COLS=("request_id","site","scientific_purpose",
 "utc_start_date","utc_end_date","events_in_source",
 "original_BIF_UTC_OFFSET_hours","utc_source_status",
 "latitude","longitude","cds_dataset","cds_request_json",
 "reference_file_status")

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for piece in iter(lambda:f.read(1024*1024),b""):h.update(piece)
 return h.hexdigest()
def n(s):
 try:
  x=float(s)
  if math.isfinite(x) and x not in (-9999,-6999):return x
 except (ValueError,TypeError):pass
 return None
def sat(T):
 if T is None or T<-80 or T>60:raise ValueError("invalid native source T")
 return 6.112*math.exp(17.67*T/(243.5+T))
def dt(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad native timestamp "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def read(path,need):
 if not path.is_file() or path.is_symlink():raise ValueError("missing regular original source "+str(path))
 with path.open("r",encoding="utf-8-sig",newline="") as f:
  rr=csv.DictReader(f)
  if not need.issubset(rr.fieldnames or []) or len(rr.fieldnames or [])!=len(set(rr.fieldnames or [])):
   raise ValueError("wrong original source CSV header "+str(path))
  rows=list(rr)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed original source row "+str(path))
 return rows
def indexed(rows,timekey):
 out={}
 for r in rows:
  k=r["site"],r[timekey]
  if k in out:raise ValueError("duplicate source site time "+str(k))
  out[k]=r
 return out
def output(path,cols,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def original_inputs(d18,d24,d32,d30,d27,d29):
 f18=d18/"stage18_all_p1_original_6hour_context.csv"
 f24=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 fh=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 f32=d32/"stage32_H01_19_water_ice_RH_and_four_VPD_trials_UNAPPROVED.csv"
 f30=d30/"stage30_CDS_REQUESTS_DRYRUN.json"
 fm30=d30/"stage30_summary.json"
 f27=d27/"stage27_ALL483_original_P2P3_episode_science_risk.csv"
 f29=d29/"stage29_FOUR_SITE_BIF_METADATA_GATE.csv"
 c18=indexed(read(f18,REQ_STAGE18),"time_native")
 approved=indexed(read(f24,REQ_APPROVED),"native_time")
 held=indexed(read(fh,REQ_HELD),"native_time")
 h01=indexed(read(f32,REQ_STAGE32),"native_time")
 episodes=read(f27,REQ_EP)
 met=read(f29,{"site","all_group_offsets_hours","group_UTC_offset_conflict"})
 request=json.loads(f30.read_text())
 m30=json.loads(fm30.read_text())
 m32=json.loads((d32/"stage32_manifest.json").read_text())
 if (len(c18),len(approved),len(held),len(h01),len(episodes))!=(775,166,46,19,483):
  raise ValueError("Stage18/24/27/32 original source populations changed")
 if m30.get("cds_site_month_requests_planned")!=11 or m30.get("science_approvals_new")!=0:
  raise ValueError("Stage30 original 11 CDS plans source changed")
 if m32.get("new_science_approvals")!=0 or m32.get("source_SHA256",{}).get("Stage18_original")!=sha(f18):
  raise ValueError("Stage32 original H01/Stage18 input provenance changed")
 if m32["source_SHA256"].get("Stage24_original_approved_166")!=sha(f24) or m32["source_SHA256"].get("Stage24_original_HOLD_46")!=sha(fh):
  raise ValueError("Stage24 source science state changed since Stage32")
 if len(request)!=11 or len({x["id"] for x in request})!=11:
  raise ValueError("Stage30 actual 11 request plan entries missing/duplicate")
 original={x["id"]:x for x in request}
 if set(NINE)-set(original):raise ValueError("Stage30 other-nine CDS site-month requests missing")
 for i in NINE:
  r=original[i]
  if not isinstance(r["request"]["date"],str) or r["request"]["date"].count("/")!=1:
   raise ValueError("Stage30 original request must have patched CDS date selector")
 if set((s["site"] for s in met))!={"US-Vcp","US-Wjs","US-Vcm","US-WCr"}:
  raise ValueError("original Stage29 four sites changed")
 offset={"US-Vcp":-7,"US-Wjs":-7,"US-Vcm":-7,"US-WCr":-6}
 for x in met:
  if x["group_UTC_offset_conflict"]!="False" or float(x["all_group_offsets_hours"])!=offset[x["site"]]:
   raise ValueError("Stage29 original BIF signed offsets changed")
 for a in h01:
  if a not in held or a in approved:raise ValueError("one original 19 H01 HOLD unexpectedly approved")
 hashes={"stage18_native_context":sha(f18),"stage24_166_overlay":sha(f24),
         "stage24_46_HOLD":sha(fh),"stage32_H01_external_phase":sha(f32),
         "stage30_CDS_original11":sha(f30),
         "stage27_original_483_episodes":sha(f27),"stage29_BIF_four_site":sha(f29)}
 return c18,approved,held,h01,episodes,original,offset,hashes

def inspect_edges(source,approved,held,h01):
 first=dt("200712152100")
 last=dt("200712160600")
 windows=[]
 for i in range(-6,19+6):
  t=(first+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
  k=("US-Vcm",t)
  if k not in source:continue
  r=source[k]
  T=n(r["TA_F_C"]);V=n(r["VPD_F_hPa"])
  if T is None or V is None:
   rh=None
  else:rh=100*(1-V/sat(T))
  orig_rh=n(r["RH_original_pct"])
  if k in held: state="ORIGINAL_P1_MANUAL_HOLD"
  elif k in approved:state="EXISTING_APPROVED166_OVERLAY"
  else:state="UNMODIFIED_ORIGINAL"
  sel=n(approved[k]["modified_VPD_hPa"]) if k in approved else V
  rel="H01" if first<=dt(t)<=last else "PRE_H01" if dt(t)<first else "POST_H01"
  screen=(rh is not None and (rh<1 or rh>100))
  windows.append(dict(
   site="US-Vcm",native_time=t,relative_to_H01=rel,
   source_original_T_C=r["TA_F_C"],source_original_VPD_hPa=r["VPD_F_hPa"],
   source_original_RH_pct=r["RH_original_pct"],
   RH_implied_original_T_and_VPD_water_pct=round(rh,6) if rh is not None else "",
   source_original_T_QC=r["TA_F_QC"],source_original_VPD_QC=r["VPD_F_QC"],
   source_processed_ERA_RH_pct=r["ERA_RH_Magnus_water_pct"],
   source_selected_status=state,
   currently_selected_VPD_hPa=sel if sel is not None else "",
   has_RH_below_1pct_or_negative=screen,
   is_low_RH_plausibility_gate=("RECHECK_SOURCE_OBSERVATION_QC_AND_NEIGHBOR_RH"
                                  if screen and rel!="H01" else "NOT_APPROVED"),
   repair_permission="NO_NEW_APPROVAL"))
 immediate=[r for r in windows if r["native_time"] in ("200712152030","200712160630")]
 if len(immediate)!=2:raise ValueError("both H01 immediate source neighbor half-hours missing")
 return windows,immediate

def build_requests(original,episodes):
 req=[]
 for i in NINE:
  r=original[i]
  req.append(dict(r,scientific_purpose=("P1_REMAINING_HOLD_OR_RH_PLATFORM_REFERENCE"
    if i not in NINE[-3:] else "HIGH_RISK_VCP_P2P3_MDS_ERA_CONFLICT_REFERENCE")))
 wjs=sorted((x for x in episodes if x["site"]=="US-Wjs" and dt(x["original_native_start"])>=dt("200705041330")),
            key=lambda x:(-int(x["review_priority_rank"]),
                 -int(x["unapproved_HH"]),x["original_native_start"]))
 if not wjs:raise ValueError("US-Wjs has no P2P3 episode covered by BIF DATE_START 200705041330")
 x=wjs[0]
 # Stage29 BIF Wjs UTC_OFFSET -7, native timestamps LST no DST,
 # original group has DATE_START, DATE_END absent => provisional.
 a=dt(x["original_native_start"])-timedelta(hours=-7)-timedelta(days=1)
 b=dt(x["original_native_end"])-timedelta(hours=-7)+timedelta(days=1)
 date=a.date().isoformat()+"/"+b.date().isoformat()
 request={"variable":list(VARS),"date":date,
          "location":{"longitude":WJS_LON,"latitude":WJS_LAT},"data_format":"netcdf"}
 req.append(dict(id="ERA5L_US_Wjs_TOP1_P2P3_"+x["episode_id"],
  site="US-Wjs",latitude=WJS_LAT,longitude=WJS_LON,
  tower_elevation_m=WJS_ELEV,
  utc_start_date=a.date().isoformat(),
  utc_end_date=b.date().isoformat(),
  source_BIF_offset_hours=-7,
  BIF_date_coverage="OPEN_ENDED_START_DATED_REVIEW",
  native_events=[x["episode_id"]],dataset=DATASET,
  request=request,source="Stage27_original_US_Wjs_max_risk_episode_and_Stage29_BIF_provisional",
  status="PLANNED_NOT_DOWNLOADED",
  scientific_purpose="FIRST_US_WJS_401_REMAINING_P2P3_INDEPENDENT_PILOT"))
 if len(req)!=10:raise ValueError("expected nine prior request + one original Wjs source episode")
 for x in req:
  if x["dataset"]!=DATASET or set(x["request"])!={"variable","date","location","data_format"}:
   raise ValueError("CDS source request changed")
  if not isinstance(x["request"]["date"],str) or x["request"]["date"].count("/")!=1:
   raise ValueError("CDS point time-series wrong range syntax")
 return req
def as_public_rows(req):
 rows=[]
 for r in req:
  rows.append(dict(request_id=r["id"],site=r["site"],
   scientific_purpose=r["scientific_purpose"],
   utc_start_date=r["utc_start_date"],utc_end_date=r["utc_end_date"],
   events_in_source=";".join(r["native_events"]),
   original_BIF_UTC_OFFSET_hours=r["source_BIF_offset_hours"],
   utc_source_status=r["BIF_date_coverage"],
   latitude=r["latitude"],longitude=r["longitude"],
   cds_dataset=r["dataset"],cds_request_json=json.dumps(r["request"],sort_keys=True),
   reference_file_status="NOT_YET_DOWNLOADED_OR_INSPECTED"))
 return rows

def fetch(req,out,max_fetch):
 if max_fetch<1 or max_fetch>len(req):raise ValueError("invalid max CDS downloads requested")
 import cdsapi
 client=cdsapi.Client()
 result=[]
 for r in req[:max_fetch]:
  p=out/(r["id"]+".cds_download")
  if p.exists():raise ValueError("refuse overwrite original CDS file "+str(p))
  client.retrieve(r["dataset"],r["request"],str(p))
  if not p.is_file() or p.stat().st_size<256:
   raise ValueError("CDS payload not created or too small for "+r["id"])
  with p.open("rb") as f:signature=f.read(8)
  is_nc=signature.startswith(b"CDF") or signature==b"\x89HDF\r\n\x1a\n"
  if not signature.startswith(b"PK") and not is_nc:
   raise ValueError("CDS unknown file type for "+r["id"])
  log=dict(id=r["id"],site=r["site"],bytes=p.stat().st_size,
    sha256=sha(p),magic_bytes_hex=signature.hex(),
    source_request=r["request"],raw_file=str(p),
    science_approval="NONE_RESEARCH_REFERENCE_ONLY")
  result.append(log)
  print("STAGE33 CDS_FETCH_PASS",r["id"],"BYTES",log["bytes"],
        "SHA256",log["sha256"],flush=True)
  (out/"stage33_downloaded_metadata.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 return result

def selftest():
 assert len(NINE)==9 and len(set(NINE))==9
 a=dt("200712152100");b=dt("200712160600")
 assert int((b-a).total_seconds()/1800)+1==19
 assert (dt("200712152030")+timedelta(minutes=30))==a
 assert (b+timedelta(minutes=30))==dt("200712160630")
 assert abs(100*(1-2.581/sat(-11.7)))<20
 assert (dt("200805241500")-timedelta(hours=-7)).strftime("%Y%m%d%H%M")=="200805242200"
 print("STAGE33 SELF-TEST PASS | 19 H01 and native neighbor QC, source site-month 9+Wjs new, no auto forcing writes")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage18-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--stage32-dir",type=Path)
 p.add_argument("--stage30-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage29-dir",type=Path)
 p.add_argument("--out",type=Path)
 p.add_argument("--fetch",action="store_true")
 p.add_argument("--acknowledge-provisional-bif-offsets",action="store_true")
 p.add_argument("--max-fetch",type=int,default=10)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage18_dir,a.stage24_dir,a.stage32_dir,a.stage30_dir,a.stage27_dir,a.stage29_dir,a.out)):
  p.error("all six original source directories and --out required")
 if a.fetch!=a.acknowledge_provisional_bif_offsets:
  p.error("download only if --fetch AND --acknowledge-provisional-bif-offsets set together")
 inp=[x.expanduser().resolve() for x in (a.stage18_dir,a.stage24_dir,a.stage32_dir,a.stage30_dir,a.stage27_dir,a.stage29_dir)]
 out=a.out.expanduser().resolve()
 if (not all(d.is_dir() for d in inp) or out.exists() or not out.parent.is_dir()
     or any(out==d or out in d.parents or d in out.parents for d in inp)):
  p.error("only NEW disjoint output, original sources immutable")
 original,approved,held,h01,episodes,prior,offset,hashes=original_inputs(*inp)
 neighbor,immediate=inspect_edges(original,approved,held,h01)
 req=build_requests(prior,episodes)
 out.mkdir(exist_ok=False)
 output(out/"stage33_H01_original_3h_neighbor_RH_VPD_and_QC_audit.csv",NEIGHBOR_COLS,neighbor)
 output(out/"stage33_next_10_science_reference_requests.csv",REQ_COLS,as_public_rows(req))
 (out/"stage33_next_10_CDS_requests.json").write_text(json.dumps(req,indent=2,sort_keys=True)+"\n")
 stats=dict(
  source_input_sha256=hashes,
  original_H01_manual_hold_half_hours=19,
  source_adjacent_unmodified_H01_half_hours=[x["native_time"] for x in immediate],
  immediate_neighbor_source_RH_derived={x["native_time"]:x["RH_implied_original_T_and_VPD_water_pct"] for x in immediate},
  immediate_neighbor_source_QC={x["native_time"]:[x["source_original_T_QC"],x["source_original_VPD_QC"]] for x in immediate},
  immediate_neighbor_low_RH_screen={x["native_time"]:x["has_RH_below_1pct_or_negative"] for x in immediate},
  additional_reference_requests=len(req),
  first_stage30_CDS_sample_existing_not_replaced=True,
  nine_other_prior_site_month_requests=9,
  newly_added_original_US_Wjs_top_episode=1,
  BIF_OFFSET_END_DATES_MISSING=True,
  downloaded=[],
  all_19_H01_HOLD_unchanged=True,all_46_P1_HOLD_unchanged=True,
  Stage24_166_approved_unchanged=True,
  P2P3_1574_science_unapproved_unchanged=True,
  source_FLUXMET_DATM_CIME_Slurm_unchanged=True,
  new_science_approvals=0)
 text_md=["# Stage33 — immediate human decision and new external meteorology references","",
 "**Do not approve H01 P1 until source neighbor humidity is reviewed.**",
 "Even Stage32's below-4-hPa repaired boundary change may connect to",
 "already-suspicious original pre/post native humidity values.",
 "",
 "## H01 original native immediate neighbors (from unmodified Stage18 source)"]
 for x in immediate:
  text_md.append("- {} TA={} °C, original VPD={} hPa, implied water RH={}%, source QC(T,V)=({},{})".format(
   x["native_time"],x["source_original_T_C"],x["source_original_VPD_hPa"],
   x["RH_implied_original_T_and_VPD_water_pct"],
   x["source_original_T_QC"],x["source_original_VPD_QC"]))
 text_md+=["",
  "If implied native water RH is near zero or negative, the source neighbor is not",
  "validated just because its VPD was outside original Stage16 P1 screen.",
  "A 4-hPa boundary threshold is a screening heuristic, not a sensor validity criterion.",
  "All source RH, VPD and QC are preserved; no H01 or neighbor fixes are authorized.",
  "",
  "## New external reference downloads (all RESEARCH ONLY)"]
 for r in req:
  text_md.append("- {} {} {}..{} {}".format(r["id"],r["site"],
    r["utc_start_date"],r["utc_end_date"],r["scientific_purpose"]))
 text_md+=["",
  "Includes 4 remaining P1 HOLD time windows (H02, H03, H04, H05),",
  "both original RH saturation platforms, US-Vcp 2008-04/05/06 conflicts,",
  "and one first US-Wjs episode selected by Stage27 original risk rank.",
  "Native FLUXNET timestamps use local standard time no DST. BIF UTC_OFFSET",
  "end dates missing: external request UTC offsets remain provisional.",
  "The source ERA companion is NOT an independent meteorological source.",
  "",
  "**Explicit human decision eventually needed: choose site/event humidity transport",
  "assumption and whether to expand the H01 suspect original-neighbor window.**",
  "No source/approved overlay/forcing/model files are edited."]
 (out/"STAGE33_NEXT_SCIENCE_ACTIONS_AND_NEIGHBOR_GATES.md").write_text("\n".join(text_md)+"\n")
 if a.fetch:
  try:
   stats["downloaded"]=fetch(req,out,a.max_fetch)
  finally:
   (out/"stage33_manifest.json").write_text(json.dumps(stats,indent=2,sort_keys=True)+"\n")
 else:
  (out/"stage33_manifest.json").write_text(json.dumps(stats,indent=2,sort_keys=True)+"\n")
 for x in immediate:
  print("STAGE33 H01_ADJACENT",x["native_time"],
    "TA",x["source_original_T_C"],"VPD",x["source_original_VPD_hPa"],
    "IMPLIED_RH_WATER",x["RH_implied_original_T_and_VPD_water_pct"],
    "QC",x["source_original_T_QC"],x["source_original_VPD_QC"],
    "SUSPECT",x["has_RH_below_1pct_or_negative"])
 print("STAGE33 SUCCESS | 19 H01 manual holds unchanged; 10 new research requests",len(stats["downloaded"]),"CDS files fetched")
 print("STAGE33_OUTPUT="+str(out))
 print("STAGE33_REPORT="+str(out/"STAGE33_NEXT_SCIENCE_ACTIONS_AND_NEIGHBOR_GATES.md"))
 print("STAGE33 SOURCE/APPROVED166/HOLD46/P2P3_1574/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

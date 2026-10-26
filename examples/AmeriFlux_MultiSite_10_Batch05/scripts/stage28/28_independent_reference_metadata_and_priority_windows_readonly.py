#!/usr/bin/env python3
"""Batch05 Stage28: real independent-weather-reference prerequisites, NOT more
source-RH candidate approvals. Extract site metadata evidence (if present)
from unmodified original AmeriFlux package ZIPs; generate ranked native-time
windows for the original Stage27 P2/P3 risks, 5 previously user-HOLD P1 events
and 2 unapproved saturation plateaus. No UTC conversion is performed without
release-specific verified BADM UTC_OFFSET. No ERA5-Land download is performed.

Original timestamps are FLUXNET local standard time without DST, not UTC.
Official AmeriFlux public site coordinates are cited as site-level references,
not a substitute for matching the release's own metadata.
"""
import argparse,csv,hashlib,json,re,zipfile
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter

SITES=("US-Vcp","US-Wjs","US-Vcm")
# Official AmeriFlux site pages, 2026-10-26 retrieval. Not inferred.
PUBLIC={
 "US-Vcp":(35.8641,-106.5965,2501,"https://ameriflux.lbl.gov/sites/siteinfo/US-Vcp"),
 "US-Wjs":(34.4258,-105.8617,1931,"https://ameriflux.lbl.gov/sites/siteinfo/US-Wjs"),
 "US-Vcm":(35.8885,-106.5322,3043,"https://ameriflux.lbl.gov/sites/siteinfo/US-Vcm")
}
HOLD_EVENTS=(
 ("H01","US-Vcm","200712152100","200712160600",19),
 ("H02","US-Vcm","200802060130","200802060800",12),
 ("H03","US-Vcm","200812272100","200812272130",2),
 ("H04","US-Vcm","201512060430","201512060930",10),
 ("H05","US-Vcp","201101010700","201101010800",3)
)
PLATEAUS=(
 ("SAT01_WCr_RH100_UNAPPROVED","US-WCr","202508250930","202508251200"),
 ("SAT02_Vcm_RH99.46_UNAPPROVED","US-Vcm","202510141200","202510141330")
)
EP={"site","episode_id","original_priority","unapproved_HH",
    "original_native_start","original_native_end","review_priority_rank",
    "dual_disagrees_gt20pp_HH","ERA_T_diff_gt5C_HH"}
HH={"site","native_time","episode_id","review_lane","risk_flags",
    "TA_F_C","VPD_F_hPa","RH_original_pct","RH_MDS_pct","RH_ERA_pct",
    "delta_RH_MDS_minus_ERA_pp","abs_selected_T_minus_ERA_T_C"}
HOLD={"site","native_time","hold_reason"}
PLATFORM={"site","native_time","platform"}
WINCOL=("priority_rank","source_event_type","site","episode_or_event",
        "native_start","native_end","native_window_start_minus6h",
        "native_window_end_plus6h","original_flagged_HH",
        "RH_MDS_ERA_conflict_gt20pp_HH",
        "original_selected_T_minus_source_ERA_gt5C_HH",
        "official_site_lat","official_site_lon","official_site_elev_m",
        "site_metadata_clock_status","independent_reference_status",
        "decision")
SITECOL=("site","official_site_lat","official_site_lon","official_site_elev_m",
         "public_coordinates_source_url","local_standard_time_without_DST",
         "source_release_zip","site_zip_status",
         "metadata_candidates_in_zip","found_UTC_OFFSET_text_in_metadata",
         "verified_release_UTC_OFFSET","site_UTC_reference_gate",
         "hourly_ERA5_Land_reference_request_authorized")
RAWCOLUMN=("site","episode_id","native_time","review_lane","risk_flags",
           "source_TA_C","source_VPD_hPa","source_RH_pct","source_MDS_RH_pct",
           "source_processed_ERA_RH_pct","MDS_minus_ERA_RH_delta_pp",
           "abs_selected_T_minus_ERA_T_C","source_science_status")
META_CANDIDATE=re.compile(r"(BADM|BIF|META|SITEINFO|SITE_INFO|GENERAL)",re.I)
UTC_REGEX=re.compile(r"(UTC[_ ]?OFFSET|GMT[_ ]?OFFSET|TIME[_ ]?ZONE)",re.I)

def stamp(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("malformed native date "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def fmt(d):return d.strftime("%Y%m%d%H%M")
def extend(a,b):
 if stamp(b)<stamp(a):raise ValueError("native window ends before start")
 return fmt(stamp(a)-timedelta(hours=6)),fmt(stamp(b)+timedelta(hours=6))
def checksum(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path,need):
 if not path.is_file() or path.is_symlink():
  raise ValueError("original report not present/nonregular "+str(path))
 with path.open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  if not need.issubset(rd.fieldnames or []) or len(set(rd.fieldnames or []))!=len(rd.fieldnames or []):
   raise ValueError("report missing columns "+str(path))
  rows=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed source report "+str(path))
 return rows
def put(path,cols,rows):
 with path.open("x",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=cols)
  writer.writeheader();writer.writerows(rows)
def original_source_metadata_scan(root,site):
 """Read only filenames and small metadata, never bulk source flux data."""
 path=root/site/"forcing"/"packages"
 zipfiles=sorted(p for p in path.glob("AMF_"+site+"_FLUXNET_*.zip")
                 if p.is_file() and not p.is_symlink())
 # Reject ambiguity, but do not impede independent-science priority manifest.
 if len(zipfiles)!=1:
  return ("", "ZIP_COUNT_"+str(len(zipfiles)),"", "")
 original_zip=zipfiles[0]
 candidates=[];times=[]
 try:
  with zipfile.ZipFile(original_zip) as z:
   for info in z.infolist():
    if info.is_dir() or info.file_size>2*1024*1024:
     continue
    if not META_CANDIDATE.search(info.filename):
     continue
    if not info.filename.lower().endswith((".csv",".txt",".tsv")):continue
    candidates.append(info.filename)
    if len(candidates)>30:break
    text=z.read(info).decode("utf-8-sig","replace")
    for line in text.splitlines():
     if UTC_REGEX.search(line):
      # Keep only metadata evidence snippets, NOT inferred UTC offsets.
      times.append(info.filename+" : "+line[:240])
      if len(times)>30:break
 except (OSError,zipfile.BadZipFile,RuntimeError) as e:
  return (str(original_zip),"ZIP_METADATA_READ_ERROR_"+type(e).__name__,"","")
 return str(original_zip),"ZIP_READ_ONLY_PASS","; ".join(candidates[:30])," || ".join(times[:30])

def verify(d27,d24):
 episode_file=d27/"stage27_ALL483_original_P2P3_episode_science_risk.csv"
 rawfile=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 holdfile=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 platformsfile=d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"
 m27=json.loads((d27/"stage27_summary.json").read_text())
 m24=json.loads((d24/"stage24_manifest.json").read_text())
 if (m27.get("source_P2P3_native_HH"),m27.get("original_P2P3_episodes"),
     m27.get("newly_approved_source_records"),
     m27.get("DATM_forcing_written"))!=(1574,483,0,False):
  raise ValueError("Stage27 actual source cohort or science state changed")
 if (m24.get("total_approved_overlay_HH"),
     m24.get("total_original_P1_manual_HOLD"))!=(166,46):
  raise ValueError("Stage24 approved and HOLD cohort changed")
 eps=read(episode_file,EP)
 raw=read(rawfile,HH)
 held=read(holdfile,HOLD)
 plate=read(platformsfile,PLATFORM)
 if (len(eps),len(raw),len(held),len(plate))!=(483,1574,46,10):
  raise ValueError("expected 483 episodes, 1574 HH, 46 held, 10 saturation candidates")
 expected=Counter({"US-Vcp":626,"US-Wjs":401,"US-Vcm":362})
 if Counter(r["site"] for r in raw if r["site"] in SITES)!=expected:
  raise ValueError("priority site original P2P3 cohort changed")
 if sum(sum(r["site"]==s and a<=r["native_time"]<=b for r in held)
        for _,s,a,b,_ in HOLD_EVENTS)!=46:
  raise ValueError("five original P1 HOLD windows changed")
 if sum(sum(r["site"]==s and a<=r["native_time"]<=b for r in plate)
        for _,s,a,b in PLATEAUS)!=10:
  raise ValueError("two suspicious plateaus population changed")
 idx={(r["site"],r["native_time"]):r for r in raw}
 if len(idx)!=1574:raise ValueError("native site-time duplicates")
 return eps,raw,held,plate,{
  "source_Stage27_483_episode_sha":checksum(episode_file),
  "source_Stage27_1574_raw_sha":checksum(rawfile),
  "original_Stage24_46_HOLD_sha":checksum(holdfile),
  "original_Stage24_10_platform_sha":checksum(platformsfile)}

def assemble(eps,raw,root,n=20):
 targets=sorted((e for e in eps if e["site"] in SITES),
                key=lambda r:(-int(r["review_priority_rank"]),
                   -int(r["unapproved_HH"]),r["site"],r["original_native_start"]))[:n]
 windows=[];sites=[];rank=0
 for e in targets:
  rank+=1
  site=e["site"];start=e["original_native_start"];end=e["original_native_end"]
  extstart,extend_=extend(start,end)
  lat,lon,elev,_=PUBLIC[site]
  windows.append(dict(priority_rank=rank,source_event_type="P2_P3_TOP_RISK_PILOT",
   site=site,episode_or_event=e["episode_id"],native_start=start,
   native_end=end,native_window_start_minus6h=extstart,
   native_window_end_plus6h=extend_,original_flagged_HH=e["unapproved_HH"],
   RH_MDS_ERA_conflict_gt20pp_HH=e["dual_disagrees_gt20pp_HH"],
   original_selected_T_minus_source_ERA_gt5C_HH=e["ERA_T_diff_gt5C_HH"],
   official_site_lat=lat,official_site_lon=lon,official_site_elev_m=elev,
   site_metadata_clock_status="UTC_OFFSET_FROM_RELEASE_BADM_NOT_YET_VERIFIED",
   independent_reference_status="NO_ERA5_LAND_FETCH_YET",
   decision="REQUIRE_RELEASE_BADM_NATIVE_UTC_MAPPING_BEFORE_ERA5_LAND"))
 for label,site,a,b,count in HOLD_EVENTS:
  rank+=1
  extstart,extend_=extend(a,b)
  if site in PUBLIC:lat,lon,elev,_=PUBLIC[site]
  else:lat=lon=elev=""
  windows.append(dict(priority_rank=rank,source_event_type="P1_MANUAL_HOLD_UNCHANGED",
   site=site,episode_or_event=label,native_start=a,native_end=b,
   native_window_start_minus6h=extstart,native_window_end_plus6h=extend_,
   original_flagged_HH=count,RH_MDS_ERA_conflict_gt20pp_HH="",
   original_selected_T_minus_source_ERA_gt5C_HH="",
   official_site_lat=lat,official_site_lon=lon,official_site_elev_m=elev,
   site_metadata_clock_status="UTC_OFFSET_FROM_RELEASE_BADM_NOT_YET_VERIFIED",
   independent_reference_status="NO_ERA5_LAND_FETCH_YET",
   decision="P1_HOLD_EXTERNAL_MET_VERIFY_NO_AUTOFILL"))
 for label,site,a,b in PLATEAUS:
  rank+=1
  extstart,extend_=extend(a,b)
  if site in PUBLIC:lat,lon,elev,_=PUBLIC[site]
  else:lat=lon=elev=""
  windows.append(dict(priority_rank=rank,source_event_type="RH_SATURATION_PLATFORM_UNAPPROVED",
   site=site,episode_or_event=label,native_start=a,native_end=b,
   native_window_start_minus6h=extstart,native_window_end_plus6h=extend_,
   original_flagged_HH="",RH_MDS_ERA_conflict_gt20pp_HH="",
   original_selected_T_minus_source_ERA_gt5C_HH="",
   official_site_lat=lat,official_site_lon=lon,official_site_elev_m=elev,
   site_metadata_clock_status="UTC_OFFSET_FROM_RELEASE_BADM_NOT_YET_VERIFIED",
   independent_reference_status="NO_ERA5_LAND_FETCH_YET",
   decision="SATURATION_PLATEAU_REVIEW_NO_AUTOFILL"))
 for site in SITES:
  lat,lon,elev,source=PUBLIC[site]
  zipname,zstatus,meta,offset_snippets=original_source_metadata_scan(root,site)
  sites.append(dict(site=site,official_site_lat=lat,official_site_lon=lon,
   official_site_elev_m=elev,public_coordinates_source_url=source,
   local_standard_time_without_DST="FLUXNET_CONVENTION",
   source_release_zip=zipname,site_zip_status=zstatus,
   metadata_candidates_in_zip=meta,found_UTC_OFFSET_text_in_metadata=offset_snippets,
   verified_release_UTC_OFFSET="",
   site_UTC_reference_gate="BLOCKED_UNTIL_SITE_BADM_UTC_OFFSET_VERIFIED",
   hourly_ERA5_Land_reference_request_authorized="NO"))
 ordered={(r["site"],r["episode_or_event"]) for r in windows}
 if len(ordered)!=len(windows):raise ValueError("unexpected duplicate target window")
 return windows,sites,targets

def selftest():
 assert set(PUBLIC)==set(SITES)
 assert sum(x[4] for x in HOLD_EVENTS)==46
 assert len(PLATEAUS)==2
 assert extend("202001010000","202001010030")==("201912311800","202001010630")
 print("STAGE28 SELF-TEST PASS | official 3-site coordinates, native ±6h, 46 manual HOLD, no invented UTC offset; no writes")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--site-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--pilot-episodes",type=int,default=20)
 p.add_argument("--out",type=Path)
 args=p.parse_args()
 if args.self_test:selftest();return
 if any(x is None for x in (args.stage27_dir,args.stage24_dir,args.out)):
  p.error("need --stage27-dir --stage24-dir --out")
 if not 1<=args.pilot_episodes<=483:p.error("--pilot-episodes must be 1..483")
 d27=args.stage27_dir.expanduser().resolve()
 d24=args.stage24_dir.expanduser().resolve()
 root=args.site_root.expanduser().resolve()
 out=args.out.expanduser().resolve()
 if (not d27.is_dir() or not d24.is_dir() or out.exists() or not out.parent.is_dir()
     or any(out==s or out in s.parents or s in out.parents for s in (d27,d24,root))):
  p.error("use existing original reports and new disjoint output folder")
 eps,raw,held,plat,hashes=verify(d27,d24)
 windows,sites,selected=assemble(eps,raw,root,args.pilot_episodes)
 chosen={(r["site"],r["episode_id"]) for r in selected}
 pilot=[r for r in raw if (r["site"],r["episode_id"]) in chosen]
 native_pilot=[
  dict(site=r["site"],episode_id=r["episode_id"],native_time=r["native_time"],
       review_lane=r["review_lane"],risk_flags=r["risk_flags"],
       source_TA_C=r["TA_F_C"],source_VPD_hPa=r["VPD_F_hPa"],
       source_RH_pct=r["RH_original_pct"],
       source_MDS_RH_pct=r["RH_MDS_pct"],
       source_processed_ERA_RH_pct=r["RH_ERA_pct"],
       MDS_minus_ERA_RH_delta_pp=r["delta_RH_MDS_minus_ERA_pp"],
       abs_selected_T_minus_ERA_T_C=r["abs_selected_T_minus_ERA_T_C"],
       source_science_status="HOLD_NOT_APPROVED") for r in pilot]
 out.mkdir(exist_ok=False)
 put(out/"stage28_SITE_METADATA_AND_UTC_OFFSET_GATES.csv",SITECOL,sites)
 put(out/"stage28_27_TOP_EPISODE_HOLD_PLATEAU_NATIVE_WINDOWS.csv",WINCOL,windows)
 put(out/"stage28_PILOT_ORIGINAL_P2P3_HH_FOR_INDEPENDENT_VALIDATION.csv",RAWCOLUMN,native_pilot)
 summary={
  "science_status":"HOLD_EXTERNAL_REFERENCE_PENDING",
  "pilot_highrisk_episodes":len(selected),
  "manual_P1_HOLD_five_groups":5,
  "manual_P1_HOLD_HH_unchanged":46,
  "saturation_platform_ranges_unmodified":2,
  "top_three_site_P2P3_original_HH":1389,
  "official_site_location_sources":{s:PUBLIC[s][3] for s in SITES},
  "site_metadata_clock_verification_complete":False,
  "UTC_offsets_approved_or_guessed":False,
  "external_reference_downloaded":False,
  "pilot_original_P2P3_HH":len(native_pilot),
  "source_report_SHA256":hashes,
  "original_FLUXMET_written":False,
  "approved_Stage24_166_changed":False,
  "manual_HOLD_46_changed":False,
  "model_DATM_or_Slurm_modified":False}
 (out/"stage28_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 lines=["# Batch05 Stage28 — actual independent-weather-reference acquisition gate",
  "","Stage27 original 1,574 P2/P3 research alternatives are unapproved; 483 original",
  "episodes ranked. This stage selects **{} high-risk P2/P3 episodes**".format(len(selected)),
  "from **US-Vcp, US-Wjs and US-Vcm** plus all five P1 HOLD source time ranges",
  "and two previously unapproved saturation plateaus.",
  "All times remain **native local standard time**, not UTC; +/-6 h is in native clock.",
  "FLUXNET time metadata must establish site-specific UTC_OFFSET before constructing",
  "a valid hourly ERA5-Land UTC request. Do not guess offset, do not apply DST.",
  "","## Official AmeriFlux publicly listed site locations",
  "| Site | Latitude | Longitude | Elevation m | ZIP scan | Source metadata UTC offset |",
  "|---|---:|---:|---:|---|---|"]
 for r in sites:
  lines.append("| {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["official_site_lat"],r["official_site_lon"],
   r["official_site_elev_m"],r["site_zip_status"],
   "unverified (see site metadata report)"))
 lines+=["","## Highest original science-risk episodes prepared"]
 for r in selected[:20]:
  lines.append("- {} / {} / {}→{} / HH={} / conflicts >20pp={} / large T diff HH={}".format(
   r["site"],r["episode_id"],r["original_native_start"],r["original_native_end"],
   r["unapproved_HH"],r["dual_disagrees_gt20pp_HH"],r["ERA_T_diff_gt5C_HH"]))
 lines+=["","## Required next actions",
  "1. Review \`stage28_SITE_METADATA_AND_UTC_OFFSET_GATES.csv\`: confirm site-specific release UTC_OFFSET against original BADM; ZIP may lack BADM.",
  "2. Only after verification convert native TIMESTAMP_START to UTC for ERA5-Land reference request.",
  "3. Obtain ERA5-Land hourly 2m air temperature and 2m dewpoint temperature, and if possible an independent in-situ station reference; account for tower elevation vs reanalysis grid elevation.",
  "4. Compare source MDS and processed ERA humidity with independent reference, paired with correct unit, timestamps, and phase; never blindly replace QC2 source ERA with itself.",
  "5. Make investigator decisions on event-group repair method, retain unresolved P1 HOLD and platforms. No forcing update yet.",
  "","**NO ERA5-Land downloaded, NO source data or official forcing modified.**"]
 (out/"STAGE28_METADATA_CLOCK_AND_REFERENCE_PILOT_PLAN.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
 print("STAGE28 SUCCESS | 3 official site locations, 483 original P2P3 episodes reviewed, top",len(selected),"pilot episodes selected")
 print("STAGE28 P1_MANUAL_HOLD 46 HH / 5 events; RH_SATURATION_PLATEAUS 2; unchanged")
 for r in sites:
  print("STAGE28 SITE",r["site"],"lat",r["official_site_lat"],"lon",r["official_site_lon"],
        "elev_m",r["official_site_elev_m"],"ZIP",r["site_zip_status"],
        "METADATA_UTC_OFFSET_LINES",bool(r["found_UTC_OFFSET_text_in_metadata"]),
        "UTC_VERIFIED NO")
 print("STAGE28 PILOT_NATIVE_WINDOWS",len(windows),"P2P3_HALF_HOURS",len(native_pilot))
 print("STAGE28 METADATA_GATES="+str(out/"stage28_SITE_METADATA_AND_UTC_OFFSET_GATES.csv"))
 print("STAGE28_REFERENCE_PILOT="+str(out/"STAGE28_METADATA_CLOCK_AND_REFERENCE_PILOT_PLAN.md"))
 print("STAGE28 ORIGINAL_SOURCE/APPROVED166/HOLD46/DATM/SLURM UNCHANGED; no ERA download")
if __name__=="__main__":main()

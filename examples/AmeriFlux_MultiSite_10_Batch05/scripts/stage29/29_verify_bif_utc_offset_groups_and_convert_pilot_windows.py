#!/usr/bin/env python3
"""Batch05 Stage29: read ORIGINAL release AmeriFlux BIF UTC_OFFSET group records,
verify grouped start/end metadata, and compute conditional native LST->UTC
pilot window conversions. DOES NOT retrieve ERA5-Land or edit forcing/models.

BIF has SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,DATAVALUE as documented
at https://ameriflux.lbl.gov/data/aboutdata/badm-data-product/ .
DATE_START without DATE_END or a timeless group is provisional: output UTC
conversion is marked NOT AUTHORIZED FOR EXTERNAL DATA REQUEST until reviewed.
No DST is added to FLUXNET local standard time.
"""
import argparse,csv,hashlib,io,json,re,zipfile
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta

SITES=("US-Vcp","US-Wjs","US-Vcm","US-WCr")
WCR=(45.8058,-90.0795,520,"https://ameriflux.lbl.gov/sites/siteinfo/US-WCr")
NEEDW={"site","source_event_type","episode_or_event","native_window_start_minus6h",
       "native_window_end_plus6h","native_start","native_end"}
NEEDM={"site","official_site_lat","official_site_lon","official_site_elev_m",
       "source_release_zip"}
GROUP_COLUMNS=("site","source_zip","source_zip_sha256","bif_member",
               "group_id","UTC_OFFSET_hours","UTC_OFFSET_DATE_START",
               "UTC_OFFSET_DATE_END","date_start_precision",
               "date_end_precision","group_metadata_status")
SITECOLS=("site","source_zip","bif_member","site_zip_sha256",
          "all_group_offsets_hours","number_UTC_OFFSET_groups",
          "group_UTC_offset_conflict","fully_dated_groups",
          "open_end_or_undated_groups","site_status")
WINCOL=("source_event_type","site","episode_or_event",
        "native_start","native_end","native_context_start","native_context_end",
        "BIF_UTC_OFFSET_hours","UTC_context_start_CANDIDATE",
        "UTC_context_end_CANDIDATE",
        "matching_GROUP_IDs","UTC_OFFSET_group_coverage",
        "ERA5_Land_request_status","science_approval")
def source_sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def read_csv(path,required):
 if not path.is_file() or path.is_symlink():raise ValueError("source report missing/non-regular "+str(path))
 with path.open(newline="",encoding="utf-8-sig") as f:
  rdr=csv.DictReader(f)
  if not required.issubset(rdr.fieldnames or []):
   raise ValueError("unexpected source report columns "+str(path))
  rows=list(rdr)
 if any(None in r for r in rows):raise ValueError("malformed source report")
 return rows
def datetime12(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad native clock "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def fmt(d):return d.strftime("%Y%m%d%H%M")
def parse_date(s,end=False):
 if not s:return None,"UNSPECIFIED"
 if not re.fullmatch(r"\d{4}(\d{2}(\d{2}(\d{4})?)?)?",s):
  raise ValueError("unsupported BADM UTC date precision "+repr(s))
 if len(s)==4: t=s+("12312359" if end else "01010000")
 elif len(s)==6:t=s+("312359" if end else "010000")
 elif len(s)==8:t=s+("2359" if end else "0000")
 elif len(s)==12:t=s
 else:raise ValueError("unexpected BADM UTC date precision "+s)
 # An end-month of February cannot simply be assumed to have 31 days.
 if end and len(s) in (4,6):
  if len(s)==4:
   t=s+"12312359"
  else:
   yy,mm=int(s[:4]),int(s[4:])
   if mm==12: nextm=datetime(yy+1,1,1)
   else:nextm=datetime(yy,mm+1,1)
   return nextm-timedelta(minutes=1),"YYYYMM"
 try:return datetime12(t),{"4":"YYYY","6":"YYYYMM","8":"YYYYMMDD","12":"YYYYMMDDHHMM"}[str(len(s))]
 except ValueError:raise ValueError("invalid BADM metadata date "+s)
def offset_number(s):
 if not re.fullmatch(r"[+-]?\d{1,2}(?:\.\d+)?",s or ""):
  raise ValueError("invalid BIF UTC_OFFSET "+repr(s))
 x=float(s)
 if abs(x)>14 or abs(x*60-round(x*60))>1e-8:
  raise ValueError("invalid time-zone UTC offset in hours "+repr(s))
 return x
def parse_bif(path,site):
 if not path.is_file() or path.is_symlink():return [],"", "ZIP_MISSING_OR_NONREGULAR"
 with zipfile.ZipFile(path) as z:
  files=[i for i in z.infolist() if re.fullmatch(
   r"AMF_"+re.escape(site)+r"_FLUXNET_BIF_.*[.]csv",Path(i.filename).name,re.I)]
  if len(files)!=1:return [],"","BIF_MEMBER_COUNT_"+str(len(files))
  info=files[0]
  if info.file_size>50*1024*1024:return [],info.filename,"BIF_SIZE_TOO_LARGE"
  grouped=defaultdict(dict)
  with z.open(info,"r") as f:
   rdr=csv.reader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
   header=next(rdr)
   if [x.strip().upper() for x in header]!=["SITE_ID","GROUP_ID","VARIABLE_GROUP","VARIABLE","DATAVALUE"]:
    raise ValueError("BIF official five-column header changed "+repr(header))
   for line in rdr:
    if len(line)!=5:
     raise ValueError("malformed original BIF row with non-five columns")
    s,g,group,key,v=[c.strip() for c in line]
    if s!=site or group.upper().removeprefix("GRP_")!="UTC_OFFSET":
     continue
    if key not in ("UTC_OFFSET","UTC_OFFSET_DATE_START","UTC_OFFSET_DATE_END"):
     continue
    if key in grouped[g] and grouped[g][key]!=v:
     raise ValueError("one BIF GROUP_ID contains conflicting "+key)
    grouped[g][key]=v
  entries=[]
  for group,r in sorted(grouped.items()):
   if "UTC_OFFSET" not in r:continue
   offset=offset_number(r["UTC_OFFSET"])
   st,precision_s=parse_date(r.get("UTC_OFFSET_DATE_START",""),end=False)
   en,precision_e=parse_date(r.get("UTC_OFFSET_DATE_END",""),end=True)
   if st and en and st>en:raise ValueError("BADM UTC_OFFSET date start after end")
   status=("CLOSED_DATED" if st and en else
           "OPEN_START_DATED" if st and not en else
           "END_ONLY_DATED" if en and not st else
           "UNBOUNDED_NO_DATES")
   entries.append(dict(site=site,group_id=group,UTC_OFFSET_hours=offset,
    UTC_OFFSET_DATE_START=r.get("UTC_OFFSET_DATE_START",""),
    UTC_OFFSET_DATE_END=r.get("UTC_OFFSET_DATE_END",""),
    date_start_precision=precision_s,date_end_precision=precision_e,
    group_metadata_status=status,_start=st,_end=en))
  return entries,info.filename,"BIF_READ_PASS"
def site_zip(site,original_root,stage28):
 if site in stage28:
  return Path(stage28[site]["source_release_zip"])
 root=original_root/site/"forcing"/"packages"
 paths=list(root.glob("AMF_"+site+"_FLUXNET_*.zip"))
 if len(paths)!=1:return Path("/__NOT_FOUND__/missing.zip")
 return paths[0]
def classify_window(site,entry,siteconf,start,end):
 if siteconf:return None,"CONFLICTING_GROUP_UTC_OFFSETS",[]
 if not entry:return None,"NO_SOURCE_BIF_UTC_OFFSET",[]
 offsets={x["UTC_OFFSET_hours"] for x in entry}
 if len(offsets)!=1:return None,"CONFLICTING_GROUP_UTC_OFFSETS",[]
 matches=[]
 for x in entry:
  if (x["_start"] is None or x["_start"]<=start) and (x["_end"] is None or x["_end"]>=end):
   matches.append(x)
 if not matches:return next(iter(offsets)),"NO_MATCHING_EFFECTIVE_DATE_RANGE",[]
 if any(x["group_metadata_status"]=="CLOSED_DATED" for x in matches):
  return next(iter(offsets)),"COVERED_CLOSED_DATED_GROUP",[x["group_id"] for x in matches]
 if any(x["group_metadata_status"]=="OPEN_START_DATED" for x in matches):
  return next(iter(offsets)),"OPEN_ENDED_START_DATED_REVIEW",[x["group_id"] for x in matches]
 return next(iter(offsets)),"ONLY_UNDATED_OR_END_ONLY_GROUP_REVIEW",[x["group_id"] for x in matches]
def test():
 x,p=parse_date("200705041330")
 assert (x,p)==(datetime(2007,5,4,13,30),"YYYYMMDDHHMM")
 assert parse_date("202402",True)[0]==datetime(2024,2,29,23,59)
 assert parse_date("2024",True)[0]==datetime(2024,12,31,23,59)
 assert fmt(datetime12("200805241500")+timedelta(hours=7))=="200805242200"
 a=[dict(group_id="4799",UTC_OFFSET_hours=-7,
         group_metadata_status="CLOSED_DATED",_start=datetime(2007,1,1),_end=datetime(2025,12,31))]
 assert classify_window("US-Vcp",a,False,datetime(2008,1,1),datetime(2008,1,2))[1]=="COVERED_CLOSED_DATED_GROUP"
 print("STAGE29 SELF-TEST PASS | BIF GROUP_ID dates + end-month leap day + UTC from LST; original source never written")
def write(path,headers,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=headers,extrasaction="raise");w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage28-dir",type=Path)
 p.add_argument("--site-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:test();return
 if a.stage28_dir is None or a.out is None:p.error("--stage28-dir and --out required")
 d=a.stage28_dir.expanduser().resolve()
 root=a.site_root.expanduser().resolve()
 out=a.out.expanduser().resolve()
 if not d.is_dir() or out.exists() or not out.parent.is_dir() or out in d.parents or out==d or d in out.parents:
  p.error("use already-generated Stage28 and a NEW output folder")
 sourcewin=d/"stage28_27_TOP_EPISODE_HOLD_PLATEAU_NATIVE_WINDOWS.csv"
 sourcemeta=d/"stage28_SITE_METADATA_AND_UTC_OFFSET_GATES.csv"
 windows=read_csv(sourcewin,NEEDW)
 metas=read_csv(sourcemeta,NEEDM)
 if len(windows)!=27 or Counter(w["source_event_type"] for w in windows)!=Counter(
   {"P2_P3_TOP_RISK_PILOT":20,"P1_MANUAL_HOLD_UNCHANGED":5,"RH_SATURATION_PLATFORM_UNAPPROVED":2}):
  raise ValueError("Stage28 pilot event population not exactly 20+5+2")
 bysite={r["site"]:r for r in metas}
 if set(bysite)!={"US-Vcp","US-Wjs","US-Vcm"}:
  raise ValueError("Stage28 original three sites changed")
 rowsgroup=[];rowsite=[];data={}
 for site in SITES:
  zfile=site_zip(site,root,bysite)
  groups,member,zipstatus=parse_bif(zfile,site)
  zsha=source_sha(zfile) if zipstatus=="BIF_READ_PASS" else ""
  offsets={g["UTC_OFFSET_hours"] for g in groups}
  conflict=len(offsets)>1
  for g in groups:
   rowsgroup.append({k:v for k,v in dict(g,source_zip=str(zfile),source_zip_sha256=zsha,
             bif_member=member).items() if k in GROUP_COLUMNS})
  rowsite.append(dict(site=site,source_zip=str(zfile),
   bif_member=member,site_zip_sha256=zsha,
   all_group_offsets_hours=";".join(str(x) for x in sorted(offsets)),
   number_UTC_OFFSET_groups=len(groups),
   group_UTC_offset_conflict=conflict,
   fully_dated_groups=sum(g["group_metadata_status"]=="CLOSED_DATED" for g in groups),
   open_end_or_undated_groups=sum(g["group_metadata_status"]!="CLOSED_DATED" for g in groups),
   site_status=zipstatus+("_CONFLICT" if conflict else "")))
  data[site]=(groups,member,conflict,zipstatus)
 results=[]
 for r in windows:
  site=r["site"]
  if site not in data:raise ValueError("unrecognized Stage28 event site")
  aa=datetime12(r["native_window_start_minus6h"])
  bb=datetime12(r["native_window_end_plus6h"])
  if aa>bb:raise ValueError("native window is reversed")
  group,member,conflict,zipstatus=data[site]
  offset,status,matches=classify_window(site,group,conflict,aa,bb)
  candidate_start=fmt(aa-timedelta(hours=offset)) if offset is not None else ""
  candidate_end=fmt(bb-timedelta(hours=offset)) if offset is not None else ""
  # No request gets authorized by Stage29 alone: metadata and external licence
  # still must be reviewed before requesting new independent sources.
  results.append(dict(source_event_type=r["source_event_type"],site=site,
   episode_or_event=r["episode_or_event"],native_start=r["native_start"],
   native_end=r["native_end"],
   native_context_start=r["native_window_start_minus6h"],
   native_context_end=r["native_window_end_plus6h"],
   BIF_UTC_OFFSET_hours=offset if offset is not None else "",
   UTC_context_start_CANDIDATE=candidate_start,
   UTC_context_end_CANDIDATE=candidate_end,
   matching_GROUP_IDs=";".join(matches),
   UTC_OFFSET_group_coverage=status,
   ERA5_Land_request_status="PENDING_SCIENTIST_METADATA_AND_LICENSE_REVIEW",
   science_approval="HOLD_NO_ORIGINAL_DATA_CHANGE"))
 out.mkdir(exist_ok=False)
 write(out/"stage29_ORIGINAL_BIF_UTC_OFFSET_ALL_GROUPS.csv",GROUP_COLUMNS,rowsgroup)
 write(out/"stage29_FOUR_SITE_BIF_METADATA_GATE.csv",SITECOLS,rowsite)
 write(out/"stage29_27_PILOT_NATIVE_TO_UTC_CANDIDATE_WINDOWS.csv",WINCOL,results)
 summary=dict(events=27,source_BIF_UTC_offset_groups=len(rowsgroup),
  source_UTC_offset_values_by_site={x["site"]:x["all_group_offsets_hours"] for x in rowsite},
  dated_coverage=Counter(x["UTC_OFFSET_group_coverage"] for x in results),
  raw_Stage28_27_windows_SHA256=source_sha(sourcewin),
  raw_Stage28_metadata_SHA256=source_sha(sourcemeta),
  P1_HOLD_original_46_unchanged=True,approved_Stage24_166_unchanged=True,
  original_FLUXMET_changed=False,DATM_changed=False,model_jobs_submitted=False,
  ERA5_Land_downloaded=False,science_approvals_new=0)
 (out/"stage29_summary.json").write_text(json.dumps(summary,indent=2,default=dict,sort_keys=True)+"\n")
 md=["# Stage29 — original AmeriFlux BIF GROUP_ID clock offsets and UTC candidate times",
  "","Source BADM Interchange Format has five fields and groups of related metadata by GROUP_ID.",
  "All original ZIPs were read-only. BIF metadata \`UTC_OFFSET=-7\` found in Stage28",
  "is evidence, but source release GROUP_ID effectivity is checked here.",
  "FLUXNET timestamps are LST, no DST; UTC candidate = local native time minus BIF signed offset.",
  "No automatic ERA5-Land retrieval, no new RH approval, no source changes.","",
  "## UTC group coverage on 27 native windows"]
 for k,v in sorted(summary["dated_coverage"].items()):md.append("- **{}**: {} windows".format(k,v))
 md+=["","## Site offset-source groups"]
 for s in rowsite:md.append("- {} offsets [{}], BIF group count={}, issue={}".format(
   s["site"],s["all_group_offsets_hours"],s["number_UTC_OFFSET_groups"],s["site_status"]))
 md+=["","**CLOSED_DATED_GROUP** is the only automatically well-bounded source coverage flag.",
  "Any open-ended/undated BIF group or unexpected conflict is reported with original",
  "group dates and needs documented scientist verification before external requests.",
  "WCr source time-zone metadata is checked separately because its saturation plateau",
  "lies in Wisconsin and **must not inherit -7** from New Mexico sites.",
  "","Recommended ERA5-Land variables once approved: 2 m air temperature and 2 m",
  "dewpoint (Kelvin), hourly UTC. Hourly-midpoint vs native 30-min temporal",
  "alignment must be documented; apply no implicit interpolation or DST.",""]
 (out/"STAGE29_UTC_SOURCE_GROUP_AUDIT_AND_REQUEST_GATES.md").write_text("\n".join(md)+"\n")
 print("STAGE29 SUCCESS | original BIF GROUP_ID dates checked, 27 native windows compared; NO ERA5_LAND DOWNLOAD")
 for s in rowsite:
  print("STAGE29 SITE",s["site"],"OFFSETS",s["all_group_offsets_hours"],
        "GROUPS",s["number_UTC_OFFSET_groups"],"CLOSED_DATED",s["fully_dated_groups"],
        "ZIP_STATUS",s["site_status"])
 for k,v in sorted(summary["dated_coverage"].items()):
  print("STAGE29 WINDOW_COVERAGE",k,v)
 print("STAGE29_GATE_REPORT="+str(out/"STAGE29_UTC_SOURCE_GROUP_AUDIT_AND_REQUEST_GATES.md"))
 print("STAGE29_OUTPUT="+str(out))
 print("STAGE29 SOURCE/BIF/APPROVED166/HOLD46/DATM/MODEL UNCHANGED")
if __name__=="__main__":main()

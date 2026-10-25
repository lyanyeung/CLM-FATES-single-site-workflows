#!/usr/bin/env python3
"""Batch05 Stage18: SHA-verified original P1 observation review; NO FORCING WRITES."""
import argparse,csv,hashlib,json,math,re
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SOURCES={
 "US-WCr":("1999-2025_v1.3_r1","f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506"),
 "US-Vcm":("2007-2025_v1.3_r1","c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c"),
 "US-Vcp":("2007-2025_v1.3_r1","eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42")}
# Pre-defined native-time review groups, not inferred UTC timestamps.
GROUPS=(
 ("G01_WCr_Aug2025","US-WCr","202508250700","202508260730"),
 ("G02_Vcm_Dec2007","US-Vcm","200712151500","200712161200"),
 ("G03_Vcm_Jan2007","US-Vcm","200701162200","200701171430"),
 ("G04_Vcm_Feb2008","US-Vcm","200802051930","200802061400"),
 ("G05_Vcm_Nov2024","US-Vcm","202411211300","202411230200"),
 ("G06_Vcm_Oct2025","US-Vcm","202510130930","202510141700"),
 ("G07_Vcp_Jan2011","US-Vcp","201101010100","201101011400"))
REQ_EP={"episode_id","site","native_start","native_end","half_hours","priority_tier",
 "qc0_measured_HH","qc2_ERA_HH","ERA_internal_nonphysical_HH","approval"}
REQ16={"site","time","TA_F_C","VPD_F_hPa","F_pair_RH_pct","TA_F_QC",
 "VPD_F_QC","source_pair_flag","ERA_pair_physical","science_status"}
REQ_SOURCE={"TIMESTAMP_START","TA_F","VPD_F","RH","TA_F_QC","VPD_F_QC",
 "TA_F_MDS","VPD_F_MDS","TA_F_MDS_QC","VPD_F_MDS_QC","TA_ERA","VPD_ERA"}
COL=("site","time_native","group","is_P1","episode","issue",
 "TA_F_C","VPD_F_hPa","RH_original_pct","RH_Magnus_water_pct",
 "TA_F_QC","VPD_F_QC","TA_MDS_C","VPD_MDS_hPa",
 "TA_MDS_QC","VPD_MDS_QC","TA_ERA_C","VPD_ERA_hPa",
 "ERA_RH_Magnus_water_pct","TA_F_minus_ERA_C","VPD_F_minus_ERA_hPa",
 "ERA_self_physics","optional_PA_F","optional_SW_IN_F","optional_P_F","decision")

def value(x):
 try:
  n=float(x)
  if math.isfinite(n) and n not in (-9999.0,-6999.0):return n
 except (ValueError,TypeError):pass
 return None
def calc_rh(t,v):
 if t is None or v is None or t< -80 or t>60:return None
 s=6.112*math.exp(17.67*t/(243.5+t))
 return 100*(1-v/s)
def dt(s):
 if not re.fullmatch(r"\d{12}",s or ""):raise ValueError("bad native timestamp "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def stamp(t):return t.strftime("%Y%m%d%H%M")
def sha_file(path):
 h=hashlib.sha256()
 with path.open("rb") as fh:
  for c in iter(lambda:fh.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def readcsv(path,required):
 if not path.is_file() or path.is_symlink():raise ValueError("missing original read-only report "+str(path))
 with path.open(encoding="utf-8-sig",newline="") as fh:
  reader=csv.DictReader(fh)
  if not required.issubset(reader.fieldnames or []):raise ValueError("source columns missing "+str(path))
  result=list(reader)
  if any(None in x or any(y is None for y in x.values()) for x in result):
   raise ValueError("malformed original report")
  return result
def readjson(path):
 if not path.is_file() or path.is_symlink():raise ValueError("missing source JSON "+str(path))
 return json.loads(path.read_text(encoding="utf-8"))
def original_csv(root,site):
 release,expected=SOURCES[site]
 folder=root/site/"forcing"/"raw"/("AMF_"+site+"_FLUXNET_"+release)
 if not folder.is_dir() or folder.is_symlink():raise ValueError("native FLUXMET directory missing")
 regex=re.compile("AMF_"+re.escape(site)+r"_FLUXNET_FLUXMET_HH_.+[.]csv",re.I)
 matches=[p for p in folder.iterdir() if regex.fullmatch(p.name)]
 if len(matches)!=1 or not matches[0].is_file() or matches[0].is_symlink():
  raise ValueError("not exactly one original native HH CSV "+site)
 f=matches[0]
 if sha_file(f)!=expected:raise ValueError("original source SHA differs "+site)
 return f
def inputs(d17,d16):
 ep=readcsv(d17/"stage17_episodes_evidence_requests.csv",REQ_EP)
 m17=readjson(d17/"stage17_summary.json")
 m16=readjson(d16/"stage16_summary.json")
 if len(ep)!=522 or m17.get("episode_count")!=522 or m17.get("stage16_original_events")!=1750:
  raise ValueError("Stage17 expected episode source report not found")
 if m16.get("events")!=1750 or m16.get("decision")!="HOLD_ALL_UNAPPROVED":
  raise ValueError("Stage16 source QA no longer unapproved")
 p1=[e for e in ep if e["priority_tier"]=="P1_MEASURED_OR_ERA_INVALID"]
 if len(p1)!=39 or Counter(e["site"] for e in p1)!=Counter({"US-Vcm":37,"US-WCr":1,"US-Vcp":1}):
  raise ValueError("Stage17 P1 exact 39 episode population differs")
 qa=readcsv(d16/"stage16_all_1750_source_pair_review.csv",REQ16)
 if len(qa)!=1750:raise ValueError("Stage16 source count != 1750")
 metadata={}
 for r in qa:
  key=(r["site"],r["time"])
  if key in metadata:raise ValueError("Stage16 repeated original key")
  metadata[key]=r
 target={};ranges=defaultdict(list)
 for e in p1:
  if e["approval"]!="HOLD_NOT_APPROVED":raise ValueError("P1 was approved elsewhere")
  a,b=dt(e["native_start"]),dt(e["native_end"])
  size=int(e["half_hours"])
  if (b-a)!=timedelta(minutes=30*(size-1)):raise ValueError("P1 episode not half-hour-contiguous")
  for step in range(size):
   when=stamp(a+timedelta(minutes=30*step))
   k=(e["site"],when)
   if k in target or k not in metadata:raise ValueError("missing/duplicate P1 native source stamp "+str(k))
   if metadata[k]["science_status"]!="HOLD_NOT_APPROVED":raise ValueError("source already approved")
   target[k]=e["episode_id"]
  ranges[e["site"]].append((stamp(a-timedelta(hours=6)),
                           stamp(b+timedelta(hours=6)),e["episode_id"]))
 return p1,metadata,target,ranges
def extract(root,metadata,target,ranges):
 records=[];p1rows=[];provenance={}
 for site in SOURCES:
  f=original_csv(root,site)
  provenance[site]=SOURCES[site][1]
  before=f.stat().st_size,f.stat().st_mtime_ns
  found=set()
  with f.open(encoding="utf-8-sig",newline="") as fh:
   rd=csv.DictReader(fh)
   if not REQ_SOURCE.issubset(rd.fieldnames or []):
    raise ValueError("original FLUXMET column schema missing "+site)
   for original in rd:
    ts=original["TIMESTAMP_START"]
    episodes=[eid for a,b,eid in ranges[site] if a<=ts<=b]
    if not episodes:continue
    k=(site,ts);flagged=k in target
    T,V=value(original["TA_F"]),value(original["VPD_F"])
    ET,EV=value(original["TA_ERA"]),value(original["VPD_ERA"])
    rh=calc_rh(T,V)
    row16=metadata.get(k) if flagged else None
    if flagged:
     if k in found:raise ValueError("duplicate original source HH "+str(k))
     found.add(k)
     if rh is None or rh>=1 or abs(rh-value(row16["F_pair_RH_pct"]))>0.002:
      raise ValueError("original/Stage16 derived RH failed "+str(k))
     if T is None or V is None or abs(T-value(row16["TA_F_C"]))>.002 or abs(V-value(row16["VPD_F_hPa"]))>.002:
      raise ValueError("original/Stage16 meteorology mismatch "+str(k))
     if (original["TA_F_QC"].strip(),original["VPD_F_QC"].strip())!=(
         row16["TA_F_QC"],row16["VPD_F_QC"]):
      raise ValueError("original QC disagreement "+str(k))
    group="|".join(g for g,s,a,b in GROUPS if s==site and a<=ts<=b)
    rec=dict(site=site,time_native=ts,group=group,is_P1=int(flagged),
      episode=target.get(k,"|".join(episodes)),
      issue=row16["source_pair_flag"] if flagged else "NATIVE_CONTEXT",
      TA_F_C=original["TA_F"],VPD_F_hPa=original["VPD_F"],
      RH_original_pct=original["RH"],
      RH_Magnus_water_pct=round(rh,6) if rh is not None else "",
      TA_F_QC=original["TA_F_QC"],VPD_F_QC=original["VPD_F_QC"],
      TA_MDS_C=original["TA_F_MDS"],VPD_MDS_hPa=original["VPD_F_MDS"],
      TA_MDS_QC=original["TA_F_MDS_QC"],VPD_MDS_QC=original["VPD_F_MDS_QC"],
      TA_ERA_C=original["TA_ERA"],VPD_ERA_hPa=original["VPD_ERA"],
      ERA_RH_Magnus_water_pct=(
       round(calc_rh(ET,EV),6) if calc_rh(ET,EV) is not None else ""),
      TA_F_minus_ERA_C=round(T-ET,5) if T is not None and ET is not None else "",
      VPD_F_minus_ERA_hPa=round(V-EV,5) if V is not None and EV is not None else "",
      ERA_self_physics=row16["ERA_pair_physical"] if flagged else "",
      optional_PA_F=original.get("PA_F",""),optional_SW_IN_F=original.get("SW_IN_F",""),
      optional_P_F=original.get("P_F",""),
      decision="HOLD_NOT_APPROVED" if flagged else "CONTEXT_NOT_FOR_DECISION")
    records.append(rec)
    if flagged:p1rows.append(rec)
  if before!=(f.stat().st_size,f.stat().st_mtime_ns):
   raise ValueError("original native file changed during scan")
  missing={k for k in target if k[0]==site}-found
  if missing:raise ValueError("missing original P1 source HH "+str(sorted(missing)[:3]))
  print("STAGE18_SITE",site,"P1_HH",len(found),"CONTEXT_HH",
        sum(r["site"]==site for r in records),"SHA256",provenance[site],flush=True)
 if set((r["site"],r["time_native"]) for r in p1rows)!=set(target):
  raise ValueError("not all P1 source records included")
 return records,p1rows,provenance
def cards(p1rows):
 parts=["# Batch05 P1 native original data — investigator decisions",
        "Original tower printed timestamps (NOT converted to UTC).",
        "TA in Celsius; VPD in hPa; RH in percent. Original -9999 denotes missing.",
        "Source QC0 measured, QC1 good MDS, QC2 processed ERA.",
        "Candidate repair is not supplied and original forcing was not changed.",
        "Decision options: KEEP_ORIGINAL / HOLD_MORE_EVIDENCE / REPLACE_VERIFIED_ONLY.",
        ""]
 all_covered=set()
 fields=("time_native","episode","TA_F_C","VPD_F_hPa","RH_original_pct",
         "RH_Magnus_water_pct","TA_F_QC","VPD_F_QC",
         "TA_MDS_C","VPD_MDS_hPa","TA_ERA_C","VPD_ERA_hPa","ERA_self_physics")
 for name,site,a,b in GROUPS:
  records=[r for r in p1rows if r["site"]==site and a<=r["time_native"]<=b]
  all_covered.update((r["site"],r["time_native"]) for r in records)
  parts+=["## "+name+" — "+str(len(records))+" original flagged half-hours",
          "Context window: "+a+" through "+b,
          "| "+" | ".join(fields)+" |",
          "| "+" | ".join("---" for _ in fields)+" |"]
  for r in records:
   parts.append("| "+" | ".join(str(r[x]).replace("|","/") for x in fields)+" |")
  parts+=["","Reviewer decision: [ ] KEEP_ORIGINAL   [ ] HOLD_MORE_EVIDENCE   [ ] REPLACE_VERIFIED_ONLY",
          "Evidence and replacement provenance: _______________________",""]
 rest=[r for r in p1rows if (r["site"],r["time_native"]) not in all_covered]
 parts+=["## Other P1 original records — "+str(len(rest))+" rows",
        "These records are additionally present in the all-39-P1 CSV.",
        "| "+" | ".join(("site",)+fields)+" |",
        "| "+" | ".join("---" for _ in range(len(fields)+1))+" |"]
 for r in rest:
  parts.append("| "+" | ".join(str(r[x]).replace("|","/") for x in ("site",)+fields)+" |")
 return "\n".join(parts)+"\n"
def selftest():
 assert len(GROUPS)==7 and len(set(e[0] for e in GROUPS))==7
 assert calc_rh(11.686,13.731)<0
 assert dt("202508260130")-dt("202508251300")==timedelta(hours=12,minutes=30)
 print("STAGE18 SELF-TEST PASS | seven original P1 review groups, physical units, native times; NO WRITES")
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--self-test",action="store_true")
 parser.add_argument("--stage17-dir",type=Path)
 parser.add_argument("--stage16-dir",type=Path)
 parser.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 parser.add_argument("--output-dir",type=Path)
 a=parser.parse_args()
 if a.self_test:selftest();return
 if any(v is None for v in (a.stage17_dir,a.stage16_dir,a.output_dir)):
  parser.error("need --stage17-dir --stage16-dir --output-dir")
 d17=a.stage17_dir.expanduser().resolve()
 d16=a.stage16_dir.expanduser().resolve()
 root=a.sites_root.expanduser().resolve()
 out=a.output_dir.expanduser().resolve()
 if not all(p.is_dir() for p in (d17,d16,root)):parser.error("source directories missing")
 if out.exists() or not out.parent.is_dir() or any(
   out==p or out in p.parents or p in out.parents for p in (d17,d16,root)):
  parser.error("output must be a NEW location not within input sources")
 episodes,metadata,target,ranges=inputs(d17,d16)
 records,p1rows,shas=extract(root,metadata,target,ranges)
 out.mkdir(exist_ok=False)
 def writefile(name,fields,rows):
  with (out/name).open("x",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 writefile("stage18_39_episode_index.csv",list(episodes[0]),episodes)
 writefile("stage18_all_p1_original_6hour_context.csv",COL,records)
 writefile("stage18_all_p1_original_flagged_HH.csv",COL,p1rows)
 with (out/"stage18_7_priority_review_cards.md").open("x",encoding="utf-8") as f:
  f.write(cards(p1rows))
 summary=dict(P1_episodes=39,P1_original_HH=len(p1rows),
              context_rows=len(records),science_approved=0,
              source_hashes=shas,original_clock="native FLUXMET printed timestamp",
              review_groups=7)
 with (out/"stage18_summary.json").open("x",encoding="utf-8") as f:
  json.dump(summary,f,indent=2,sort_keys=True)
 for name,site,start,end in GROUPS:
  arr=[r for r in p1rows if r["site"]==site and start<=r["time_native"]<=end]
  print("STAGE18_PRIORITY",name,"FLAGGED_HH",len(arr),flush=True)
  if len(arr)>8:arr=arr[:4]+arr[-4:]
  for r in arr:
   print("ORIGINAL",r["time_native"],"TA="+str(r["TA_F_C"]),
         "VPD="+str(r["VPD_F_hPa"]),"RH="+str(r["RH_original_pct"]),
         "RHcalc="+str(r["RH_Magnus_water_pct"]),
         "QC="+str(r["TA_F_QC"])+"/"+str(r["VPD_F_QC"]),
         "MDS_T/V="+str(r["TA_MDS_C"])+"/"+str(r["VPD_MDS_hPa"]),
         "ERA_T/V="+str(r["TA_ERA_C"])+"/"+str(r["VPD_ERA_hPa"]),flush=True)
 print("STAGE18 SUMMARY P1_episodes=39 flagged_HH={} context_HH={} cards=7 approved=0 reports={}".format(
   len(p1rows),len(records),out),flush=True)
 print("ONLY NEW HUMAN REVIEW CSV/MD/JSON; NO ORIGINAL/FORCING/MODEL/SLURM WRITES")
if __name__=="__main__":main()

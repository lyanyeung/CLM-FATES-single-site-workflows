#!/usr/bin/env python3
"""Batch05 Stage19: source-grounded P1 BEFORE / DURING / AFTER comparison.

Uses the existing SHA-verified original Stage18 775 native context half-hours.
Exports seven priority-group tables, all 39 episode tables, and long-form CSV.
TA_F/VPD_F are ORIGINAL *SELECTED* FLUXMET values, NOT necessarily measured.
QC0 means measured, QC1 MDS, QC2 source downscaled ERA. TA_ERA/VPD_ERA
are source-supplied processed ERA columns: NOT independently downloaded ERA5.
No external weather is fetched. NO forcing, source, Slurm, or science edits.
"""
import argparse, csv, json, math
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

EXPECTED_EP=39
EXPECTED_P1=176
EXPECTED_CONTEXT=775
GROUPS=(
 ("G01_WCr_Aug2025","US-WCr","202508250700","202508260730"),
 ("G02_Vcm_Dec2007","US-Vcm","200712151500","200712161200"),
 ("G03_Vcm_Jan2007","US-Vcm","200701162200","200701171430"),
 ("G04_Vcm_Feb2008","US-Vcm","200802051930","200802061400"),
 ("G05_Vcm_Nov2024","US-Vcm","202411211300","202411230200"),
 ("G06_Vcm_Oct2025","US-Vcm","202510130930","202510141700"),
 ("G07_Vcp_Jan2011","US-Vcp","201101010100","201101011400"),
)
NEEDED={
 "site","time_native","group","is_P1","episode","issue",
 "TA_F_C","VPD_F_hPa","RH_original_pct","RH_Magnus_water_pct",
 "TA_F_QC","VPD_F_QC","TA_MDS_C","VPD_MDS_hPa",
 "TA_MDS_QC","VPD_MDS_QC","TA_ERA_C","VPD_ERA_hPa",
 "ERA_RH_Magnus_water_pct","TA_F_minus_ERA_C","VPD_F_minus_ERA_hPa",
 "decision"
}
EP_NEEDED={"episode_id","site","native_start","native_end","half_hours",
           "priority_tier","approval"}
DISPLAY=("time_native","phase","TA_F_C","TA_F_QC","VPD_F_hPa","VPD_F_QC",
         "RH_original_pct","RH_Magnus_water_pct","TA_ERA_C",
         "VPD_ERA_hPa","ERA_RH_Magnus_water_pct","TA_MDS_C","VPD_MDS_hPa",
         "TA_MDS_QC","VPD_MDS_QC")
EXTRA=("review_id","selected_episode","phase","time_native","source_TA_F_C",
       "source_TA_F_QC","source_VPD_F_hPa","source_VPD_F_QC",
       "original_RH_pct","derived_RH_Magnus_water_pct",
       "TA_MDS_C","VPD_MDS_hPa","TA_MDS_QC","VPD_MDS_QC",
       "processed_TA_ERA_C","processed_VPD_ERA_hPa",
       "processed_ERA_RH_Magnus_water_pct","F_T_minus_ERA_T_C",
       "F_VPD_minus_ERA_VPD_hPa","P1_flag",
       "human_decision","decision_evidence")
def parse(s):
 if len(s)!=12 or not s.isdigit(): raise ValueError("invalid native time "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def clock(t):return t.strftime("%Y%m%d%H%M")
def readcsv(path,fields):
 if not path.is_file() or path.is_symlink():raise ValueError("missing non-symlink CSV "+str(path))
 with path.open("r",encoding="utf-8-sig",newline="") as f:
  r=csv.DictReader(f)
  if not fields.issubset(r.fieldnames or []) or len(r.fieldnames)!=len(set(r.fieldnames)):
   raise ValueError("Stage18 missing/duplicate fields")
  data=list(r)
  if any(None in x or any(v is None for v in x.values()) for x in data):
   raise ValueError("malformed Stage18 CSV")
 return data
def readjson(path):
 if not path.is_file() or path.is_symlink():raise ValueError("missing Stage18 JSON")
 return json.loads(path.read_text(encoding="utf-8"))
def as_num(s):
 try:
  n=float(s)
  return n if math.isfinite(n) and n not in (-9999.,-6999.) else None
 except (TypeError,ValueError):
  return None
def display(x):
 if x=="" or x is None or x=="-9999":return "—"
 return str(x)
def phase(row,lo,hi):
 ts=row["time_native"]
 if ts<lo:return "BEFORE"
 if ts>hi:return "AFTER"
 if row["is_P1"]=="1":return "P1"
 return "BETWEEN"
def emit_record(row,group,ph):
 return dict(review_id=group,selected_episode=row["episode"],
    phase=ph,time_native=row["time_native"],
    source_TA_F_C=row["TA_F_C"],source_TA_F_QC=row["TA_F_QC"],
    source_VPD_F_hPa=row["VPD_F_hPa"],source_VPD_F_QC=row["VPD_F_QC"],
    original_RH_pct=row["RH_original_pct"],
    derived_RH_Magnus_water_pct=row["RH_Magnus_water_pct"],
    TA_MDS_C=row["TA_MDS_C"],VPD_MDS_hPa=row["VPD_MDS_hPa"],
    TA_MDS_QC=row["TA_MDS_QC"],VPD_MDS_QC=row["VPD_MDS_QC"],
    processed_TA_ERA_C=row["TA_ERA_C"],
    processed_VPD_ERA_hPa=row["VPD_ERA_hPa"],
    processed_ERA_RH_Magnus_water_pct=row["ERA_RH_Magnus_water_pct"],
    F_T_minus_ERA_T_C=row["TA_F_minus_ERA_C"],
    F_VPD_minus_ERA_VPD_hPa=row["VPD_F_minus_ERA_hPa"],
    P1_flag=row["is_P1"],human_decision="HOLD_NOT_APPROVED",
    decision_evidence="")
def markdown(title,source,lo,hi,records):
 lines=[
   "# "+title,"",
   "**Evidence:** SHA-verified original FLUXMET selected \`TA_F\`/\`VPD_F\` and",
   "its original source-supplied \`TA_ERA\`/\`VPD_ERA\` columns.",
   "No separately fetched ERA5/ERA5-Land was used; source ERA identity/version",
   "must be confirmed before calling it a new independent ERA5 comparison.",
   "All time labels are original native tower timestamps, **not UTC**.",
   "Temperature °C; VPD hPa; RH %. Missing original RH shown as —.",
   "**A row is genuinely measured only for each variable where its corresponding QC=0.**",
   "QC=1 MDS and QC=2 processed ERA are not tower measurements.",
   "Derived RH from Magnus water formula is only a diagnostic; it is not proof",
   "of source sensor error. No corrections are approved.","",
   "Review period: "+lo+" through "+hi+" (original native time).",
   "Rows: "+str(len(records))+"; flagged P1 HH: "+
       str(sum(r["is_P1"]=="1" for r in records))+".","",
   "| "+ " | ".join(DISPLAY)+" |",
   "| "+" | ".join("---" for _ in DISPLAY)+" |"
 ]
 for row in records:
  vals=dict(row)
  vals["phase"]=phase(row,lo,hi)
  lines.append("| "+" | ".join(display(vals[c]).replace("|","/") for c in DISPLAY)+" |")
 lines+=["",
   "## Investigator decision","",
   "- [ ] KEEP original — cite original sensor and processing evidence",
   "- [ ] REPLACE with independently verified candidate — exact variable, source, and timestamps required",
   "- [ ] HOLD — source/clock/algorithm/reference remains unverified","",
   "**Current status: HOLD_NOT_APPROVED; NO changes applied.**",
   "",
   "Science evidence, rationale and approved source: __________________",
   ""]
 return "\n".join(lines)
def examine(input_dir):
 meta=readjson(input_dir/"stage18_summary.json")
 if meta.get("P1_episodes")!=EXPECTED_EP or meta.get("P1_original_HH")!=EXPECTED_P1 or meta.get("context_rows")!=EXPECTED_CONTEXT or meta.get("science_approved")!=0:
  raise ValueError("Stage18 original run counts/status mismatch")
 eps=readcsv(input_dir/"stage18_39_episode_index.csv",EP_NEEDED)
 data=readcsv(input_dir/"stage18_all_p1_original_6hour_context.csv",NEEDED)
 flags=readcsv(input_dir/"stage18_all_p1_original_flagged_HH.csv",NEEDED)
 if len(eps)!=EXPECTED_EP or len(data)!=EXPECTED_CONTEXT or len(flags)!=EXPECTED_P1:
  raise ValueError("Stage18 old reports cohort mismatch")
 unique={}
 for r in data:
  key=r["site"],r["time_native"]
  if key in unique:raise ValueError("Stage18 duplicated original source context "+str(key))
  if r["TA_F_QC"] not in ("0","1","2") or r["VPD_F_QC"] not in ("0","1","2"):
   raise ValueError("QC source must distinguish measured vs filled")
  parse(r["time_native"])
  unique[key]=r
 want={(r["site"],r["time_native"]) for r in flags}
 if len(want)!=EXPECTED_P1 or want!={k for k,r in unique.items() if r["is_P1"]=="1"}:
  raise ValueError("P1 source HH not faithfully mapped")
 for ep in eps:
  if ep["priority_tier"]!="P1_MEASURED_OR_ERA_INVALID" or ep["approval"]!="HOLD_NOT_APPROVED":
   raise ValueError("prior P1 scientific hold missing")
 return eps,data,flags
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage18-dir",type=Path)
 p.add_argument("--output-dir",type=Path)
 a=p.parse_args()
 if a.self_test:
  assert phase({"time_native":"202001010000","is_P1":"0"},"202001010030","202001010130")=="BEFORE"
  assert phase({"time_native":"202001010100","is_P1":"1"},"202001010030","202001010130")=="P1"
  assert phase({"time_native":"202001010200","is_P1":"0"},"202001010030","202001010130")=="AFTER"
  assert parse("202508260130")-parse("202508251300")==timedelta(hours=12,minutes=30)
  print("STAGE19 SELF-TEST PASS | native pre/P1/between/post, QC source and provenance labels; no writes")
  return
 if not a.stage18_dir or not a.output_dir:p.error("--stage18-dir and --output-dir required")
 src=a.stage18_dir.expanduser().resolve()
 dest=a.output_dir.expanduser().resolve()
 if not src.is_dir() or dest.exists() or not dest.parent.is_dir() or dest==src or src in dest.parents or dest in src.parents:
  p.error("read-only input Stage18 required; output must be new and separate")
 eps,data,flags=examine(src)
 dest.mkdir(exist_ok=False)
 summary={"status":"ALL_HOLD_UNAPPROVED","source_ERA_is_independently_downloaded_ERA5":False,
   "P1_episodes":39,"P1_flagged_HH":176,"original_unique_context_HH":775}
 epdir=dest/"all_39_episodes";epdir.mkdir()
 groupdir=dest/"seven_priority_groups";groupdir.mkdir()
 master=[]
 for ep in sorted(eps,key=lambda x:(x["site"],x["native_start"])):
  site=ep["site"];lo=ep["native_start"];hi=ep["native_end"]
  start=clock(parse(lo)-timedelta(hours=6))
  finish=clock(parse(hi)+timedelta(hours=6))
  part=sorted((r for r in data if r["site"]==site and start<=r["time_native"]<=finish),
              key=lambda r:r["time_native"])
  f=[r for r in part if r["is_P1"]=="1" and lo<=r["time_native"]<=hi]
  if len(f)!=int(ep["half_hours"]):
   raise ValueError("Stage18 episode original P1 coverage mismatch "+ep["episode_id"])
  (epdir/(ep["episode_id"]+".md")).write_text(
   markdown(ep["episode_id"],site,lo,hi,part),encoding="utf-8")
  master.extend(emit_record(r,ep["episode_id"],phase(r,lo,hi)) for r in part)
 print("STAGE19_ALL39 episodes=39 flagged_HH=176; each episode +/-6 h original native context",flush=True)
 for group,site,start,end in GROUPS:
  part=sorted((r for r in data if r["site"]==site and
        start<=r["time_native"]<=end and group in r["group"].split("|")),
       key=lambda r:r["time_native"])
  if not part:raise ValueError("Stage18 group context absent "+group)
  relevant=[r for r in part if r["is_P1"]=="1"]
  if not relevant:raise ValueError("Stage18 group has no P1 observations "+group)
  lo=relevant[0]["time_native"];hi=relevant[-1]["time_native"]
  (groupdir/(group+".md")).write_text(markdown(group,site,lo,hi,part),encoding="utf-8")
  counter=Counter(phase(r,lo,hi) for r in part)
  print("STAGE19_GROUP",group,"ROWS",len(part),"BEFORE",counter["BEFORE"],
       "P1",counter["P1"],"BETWEEN",counter["BETWEEN"],"AFTER",counter["AFTER"],flush=True)
  summary[group]={"rows":len(part),"flagged_HH":len(relevant),
                   "before":counter["BEFORE"],"after":counter["AFTER"]}
 with (dest/"stage19_all_episode_before_during_after_long.csv").open("x",encoding="utf-8",newline="") as fh:
  w=csv.DictWriter(fh,fieldnames=EXTRA);w.writeheader();w.writerows(master)
 with (dest/"stage19_summary.json").open("x",encoding="utf-8") as fh:
  json.dump(summary,fh,indent=2,sort_keys=True)
 print("STAGE19 SUMMARY 39_episode_MD 7_group_MD original_Stage18_context=775 P1_HH=176 approved=0 reports="+str(dest),flush=True)
 print("Only NEW CSV/MD/JSON created. NO ORIGINAL/STAGE18/FORCING/MODEL/SLURM WRITES.",flush=True)
if __name__=="__main__":main()

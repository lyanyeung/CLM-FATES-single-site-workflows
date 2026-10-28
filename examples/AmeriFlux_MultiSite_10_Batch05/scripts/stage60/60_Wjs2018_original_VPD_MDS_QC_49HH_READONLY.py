#!/usr/bin/env python3
"""Batch05 Stage60 | US-Wjs March 2018 ORIGINAL VPD_F_MDS vs VPD_F.
Read Stage59 original 49-native-HH FLUXMET field extraction and Stage58/56
source-verified reports. DO NOT treat MDS (marginal distribution sampling)
as independent tower-observed humidity, even when MDS and VPD_F agree.
NO source forcing/model edits and NO new science approvals.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

SITE="US-Wjs"
START="201803111200"
END="201803121200"
LEFT="201803111900"
FIRST="201803111930"
LAST="201803121000"
RIGHT="201803121030"
COLUMNS=("site","native_time","phase","TA_F_C","TA_F_QC","original_VPD_F_hPa",
         "original_VPD_F_QC","original_VPD_F_MDS_hPa","original_VPD_F_MDS_QC",
         "VPD_F_minus_VPD_F_MDS_hPa","source_VPD_ERA_hPa",
         "original_source_RH_pct","RH_implied_from_VPD_F_pct",
         "RH_implied_from_VPD_F_MDS_pct","P_F","P_F_QC",
         "SW_IN_F","SW_IN_F_QC","LW_IN_F","WS_F","PA_F",
         "LE_F_MDS","LE_F_MDS_QC",
         "MDS_agrees_with_selected_within_0p002hPa",
         "original_VPD_physical_RH_lt0","MDS_VPD_physical_RH_lt0",
         "science_status")

def stamp(x):
 if len(x)!=12 or not x.isdigit():raise ValueError("invalid original native timestamp "+repr(x))
 return datetime.strptime(x,"%Y%m%d%H%M")

def interval(a,b):
 lo,hi=stamp(a),stamp(b)
 if hi<lo or (hi-lo).total_seconds()%1800:raise ValueError("not a 30min range")
 return [(lo+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M") for i in range(int((hi-lo).total_seconds()//1800)+1)]

def num(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.0,-6999.0) else None
 except(TypeError,ValueError):return None

def sat(t):
 if t is None or not -80<=t<=60:raise ValueError("invalid original air temperature")
 return 6.112*math.exp(17.67*t/(t+243.5))

def rh(t,v):
 return 100*(1-v/sat(t)) if t is not None and v is not None else None

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
 return h.hexdigest()

def read(path):
 if not path.is_file() or path.is_symlink():raise ValueError("regular original report missing "+str(path))
 with path.open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  if not rd.fieldnames or len(set(rd.fieldnames))!=len(rd.fieldnames):
   raise ValueError("bad source columns "+str(path))
  data=list(rd)
 if any(None in r or any(x is None for x in r.values()) for r in data):
  raise ValueError("malformed CSV source "+str(path))
 return data

def write(path,cols,rows):
 with path.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader()
  w.writerows(rows)

def fmt(x):
 v=num(x)
 return "NA" if v is None else f"{v:.3f}"

def selftest():
 assert len(interval(START,END))==49
 assert len(interval(FIRST,LAST))==30
 assert len(interval("201803111500",LEFT))==9
 assert abs(sat(-0.401)-6.0)<.2
 assert rh(-.401,5.398)<15
 assert num("-9999") is None
 print("STAGE60 SELF-TEST PASS | 49 exact native HH, 30 unapproved VPD-QC1, MDS/source selected provenance; READONLY")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage59-dir",type=Path)
 p.add_argument("--stage58-dir",type=Path)
 p.add_argument("--stage56-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(v is None for v in (a.stage59_dir,a.stage58_dir,a.stage56_dir,a.out)):
  p.error("need Stage59/58/56 report dirs and NEW output dir")
 d59,d58,d56,out=(x.expanduser().resolve() for x in
                   (a.stage59_dir,a.stage58_dir,a.stage56_dir,a.out))
 if not all(d.is_dir() for d in (d59,d58,d56)) or not out.parent.is_dir() or out.exists():
  p.error("report source directories must exist; output must be new")
 if any(out==d or d in out.parents or out in d.parents for d in (d59,d58,d56)):
  p.error("output must not overwrite or be nested in previous reports")
 f59=d59/"stage59_49_HH_ORIGINAL_SOURCE_ALL_AVAILABLE_HUMIDITY_WEATHER.csv"
 f58=d58/"stage58_30HH_FOUR_RESEARCH_HUMIDITY_METHODS_UNAPPROVED.csv"
 f56=d56/"stage56_VERSIONED_174_approved_RH_VPD_native_overlay.csv"
 m59=json.loads((d59/"stage59_manifest.json").read_text())
 m58=json.loads((d58/"stage58_manifest.json").read_text())
 m56=json.loads((d56/"stage56_manifest.json").read_text())
 original=read(f59)
 existing174=read(f56)
 trials=read(f58)
 if (len(original)!=49 or len(existing174)!=174 or len(trials)!=30 or
     m59.get("output_sha256",{}).get(f59.name)!=sha(f59) or
     m58.get("outputs_sha256",{}).get(f58.name)!=sha(f58) or
     m56.get("outputs_sha256",{}).get(f56.name)!=sha(f56) or
     m59.get("science_HOLD_30HH_unchanged") is not True or
     m59.get("approved_overlay_174_unchanged") is not True or
     m58.get("scientific_approvals_new")!=0 or
     m56.get("versioned_total_approved_HH")!=174 or
     m59.get("stage56_174_sha256")!=sha(f56) or
     m59.get("stage58_sha256")!=sha(f58)):
  raise ValueError("Stage59/58/56 report provenance or original populations drift")
 required={"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
           "VPD_F_MDS","VPD_F_MDS_QC","VPD_ERA","RH","P_F","SW_IN_F",
           "WS_F","LW_IN_F","PA_F","PHASE"}
 if not required.issubset(set(original[0])):
  raise ValueError("original Stage59 FLUXMET VPD-MDS QC and weather columns missing")
 bytime={}
 for row in original:
  time=row["TIMESTAMP_START"]
  if time in bytime or time not in set(interval(START,END)):
   raise ValueError("duplicate or unexpected original native source time")
  bytime[time]=row
 if set(bytime)!=set(interval(START,END)):
  raise ValueError("49 original half hours missing")
 held=set(interval(FIRST,LAST))
 if any(r["site"]==SITE and r["native_time"] in held for r in existing174):
  raise ValueError("2018 30-HH HOLD overlaps previous 174 approved overlay")
 if set(r["native_time"] for r in trials)!=held or any(r["site"]!=SITE for r in trials):
  raise ValueError("Stage58 30-HH trial identity drift")
 for ts in held:
  r=bytime[ts]
  if r["TA_F_QC"]!="0" or r["VPD_F_QC"]!="1" or num(r["RH"]) is not None:
   raise ValueError("protected 2018 original QC/HOLD missing-RH drift "+ts)
 for ts in (LEFT,RIGHT):
  r=bytime[ts]
  if r["TA_F_QC"]!="0" or r["VPD_F_QC"]!="0" or num(r["RH"]) is None:
   raise ValueError("original QC0 tower RH boundary drift")
 summary={}
 samples=[]
 for ts in interval(START,END):
  r=bytime[ts]
  T,V,M=num(r["TA_F"]),num(r["VPD_F"]),num(r["VPD_F_MDS"])
  if T is None or V is None or M is None:
   raise ValueError("one of 49 original VPD_F_MDS/T/VPD source data missing "+ts)
  diff=V-M
  vr,mr=rh(T,V),rh(T,M)
  stage="HOLD_2018" if ts in held else ("QC0_ANCHOR" if ts in (LEFT,RIGHT) else "CONTEXT")
  rec=dict(site=SITE,native_time=ts,phase=stage,TA_F_C=r["TA_F"],
    TA_F_QC=r["TA_F_QC"],original_VPD_F_hPa=r["VPD_F"],
    original_VPD_F_QC=r["VPD_F_QC"],original_VPD_F_MDS_hPa=r["VPD_F_MDS"],
    original_VPD_F_MDS_QC=r["VPD_F_MDS_QC"],
    VPD_F_minus_VPD_F_MDS_hPa=f"{diff:.10f}",
    source_VPD_ERA_hPa=r["VPD_ERA"],
    original_source_RH_pct=r["RH"],
    RH_implied_from_VPD_F_pct=f"{vr:.8f}",
    RH_implied_from_VPD_F_MDS_pct=f"{mr:.8f}",
    P_F=r.get("P_F",""),P_F_QC=r.get("P_F_QC",""),
    SW_IN_F=r.get("SW_IN_F",""),SW_IN_F_QC=r.get("SW_IN_F_QC",""),
    LW_IN_F=r.get("LW_IN_F",""),WS_F=r.get("WS_F",""),PA_F=r.get("PA_F",""),
    LE_F_MDS=r.get("LE_F_MDS",""),LE_F_MDS_QC=r.get("LE_F_MDS_QC",""),
    MDS_agrees_with_selected_within_0p002hPa=int(abs(diff)<=.002),
    original_VPD_physical_RH_lt0=int(vr<0),
    MDS_VPD_physical_RH_lt0=int(mr<0),
    science_status="SOURCE_PROVENANCE_ONLY_NO_NEW_SCIENCE_APPROVAL")
  samples.append(rec)
 hs=[r for r in samples if r["phase"]=="HOLD_2018"]
 outside=[r for r in samples if r["phase"]!="HOLD_2018"]
 qc_counts=dict(sorted(Counter(r["original_VPD_F_MDS_QC"] for r in hs).items()))
 match_count=sum(int(r["MDS_agrees_with_selected_within_0p002hPa"]) for r in hs)
 badselected=sum(int(r["original_VPD_physical_RH_lt0"]) for r in hs)
 badmds=sum(int(r["MDS_VPD_physical_RH_lt0"]) for r in hs)
 maxdiff=max(abs(float(r["VPD_F_minus_VPD_F_MDS_hPa"])) for r in hs)
 precipvals=[num(r["P_F"]) for r in hs]
 if any(v is None for v in precipvals):
  precip_note="PARTLY_MISSING_NO_SUM"
  precipitation=None
 else:
  precipitation=sum(precipvals)
  precip_note="VALID_SOURCE_RECORDS_NO_INDEPENDENT_QC"
 result=dict(
   original_source_sha256=m59.get("original_source_sha256"),
   stage59_original49_sha256=sha(f59),stage58_original30_sha256=sha(f58),
   stage56_original174_sha256=sha(f56),
   original_49_HH=49,original_2018_HOLD_HH=30,
   original_2018_HOLD_MDS_QC_distribution=qc_counts,
   original_2018_HOLD_VPD_equals_MDS_within_0p002_HH=match_count,
   original_2018_HOLD_VPD_vs_MDS_largest_abs_difference_hPa=maxdiff,
   original_2018_HOLD_original_negative_implied_RH_HH=badselected,
   original_2018_HOLD_MDS_negative_implied_RH_HH=badmds,
   original_2018_HOLD_source_P_F_30HH_sum=precipitation,
   original_2018_HOLD_precipitation_sum_note=precip_note,
   original_QC0_anchor_MDS_QC={t:bytime[t]["VPD_F_MDS_QC"] for t in (LEFT,RIGHT)},
   VPD_F_MDS_not_independent_tower_observation=True,
   no_source_sensor_manual_verified=True,science_approvals_new=0,
   original_174_approved_overlay_unchanged=True,
   original_2018_HOLD_30HH_unchanged=True,original_sources_modified=False,
   DATM_modified=False,Slurm_jobs_submitted=0)
 out.mkdir(exist_ok=False)
 fnew=out/"stage60_49HH_original_VPD_F_MDS_vs_VPD_F_and_weather.csv"
 write(fnew,COLUMNS,samples)
 result["output_sha256"]={fnew.name:sha(fnew)}
 (out/"stage60_manifest.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print("STAGE60 SUCCESS | US-Wjs 49 HH original MDS source comparison, 30 HH 2018 science HOLD; prior 174 intact")
 print("STAGE60 2018 HOLD 30 HH MDS_QC_COUNTS",json.dumps(qc_counts,sort_keys=True))
 print("STAGE60 2018 HOLD 30 HH MDS_AND_SELECTED_EQUAL_WITHIN_0.002",match_count,"/30 MAX_ABS_DIFF_hPa",f"{maxdiff:.6f}")
 print("STAGE60 2018 HOLD NEGATIVE_RH source_SELECTED",badselected,"source_MDS",badmds)
 print("STAGE60 2018 HOLD SOURCE_PRECIP_TOTAL",precipitation,precip_note)
 print("STAGE60 QC0 LEFT_ANCHOR MDS_QC",bytime[LEFT]["VPD_F_MDS_QC"],"RIGHT_ANCHOR MDS_QC",bytime[RIGHT]["VPD_F_MDS_QC"])
 print("STAGE60 EXACT 30HH SOURCE AND MDS VALUES | original native time | T C | VPD selected | QC | MDS VPD | MDS QC | ERA VPD | MDS-derived RH | P_F | LE_MDS")
 for r in hs:
  print("STAGE60 HOLD",r["native_time"],"|",fmt(r["TA_F_C"]),"|",
    fmt(r["original_VPD_F_hPa"]),"|",r["original_VPD_F_QC"],"|",
    fmt(r["original_VPD_F_MDS_hPa"]),"|",r["original_VPD_F_MDS_QC"],"|",
    fmt(r["source_VPD_ERA_hPa"]),"|",fmt(r["RH_implied_from_VPD_F_MDS_pct"]),"|",
    fmt(r["P_F"]),"|",fmt(r["LE_F_MDS"]))
 print("STAGE60 ANCHOR AND SATURATION CONTEXT | native time | VPD selected | QC | MDS VPD | MDS QC | P_F | SW_IN_F | WS_F")
 for r in outside:
  if r["native_time"] in set(interval("201803111400",LEFT)+interval(RIGHT,"201803121100")):
   print("STAGE60 CONTEXT",r["native_time"],"|",
     fmt(r["original_VPD_F_hPa"]),"|",r["original_VPD_F_QC"],"|",
     fmt(r["original_VPD_F_MDS_hPa"]),"|",r["original_VPD_F_MDS_QC"],"|",
     fmt(r["P_F"]),"|",fmt(r["SW_IN_F"]),"|",fmt(r["WS_F"]))
 print("STAGE60_OUT="+str(out))
 print("STAGE60 NO APPROVAL OR ORIGINAL/174/30HH_HOLD/DATM/SLURM CHANGES")
if __name__=="__main__":
 main()

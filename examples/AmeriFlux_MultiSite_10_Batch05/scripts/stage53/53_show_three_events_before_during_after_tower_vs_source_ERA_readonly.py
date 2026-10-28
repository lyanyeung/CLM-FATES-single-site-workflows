#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage53. PRINT actual source TA/VPD/RH and source ERA
variables before, during, after three Stage51 source problem events.
Original time window = two preceding original half-hours, ALL event HH,
two following half-hours; per-product source ZIP/CSV verified against Stage52.

IMPORTANT: TA_ERA and VPD_ERA inside AmeriFlux FLUXMET are *source-processed
ERA companion variables*, NOT independent downloaded ERA5-Land.
RH derived from T/VPD is diagnostic, NOT measured original tower RH.
No changing original data, approved 166, P1HOLD46, RH-plateau10, P2P31574,
model forcing, DATM, CIME, Slurm or Claude's 108 source cases.
"""
import argparse
import csv
import io
import json
import math
import hashlib
import zipfile
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timedelta

TARGETS={
 "US-UMB_E0003":("US-UMB",1),
 "US-Wjs_E0079":("US-Wjs",3),
 "US-Wjs_E0114":("US-Wjs",4),
}
REQUIRED_META={"site","source_file","source_member","source_file_SHA256",
 "source_kind","timestamp_column","target_times_matched"}
REQ_NATIVE={"site","episode_id","native_time","original_T_C",
 "original_VPD_hPa","original_VPD_QC","original_ERA_RH_pct",
 "hypothesis_RH_pct","science_approval","DATM_permission"}
REQ_EVENT={"site","episode_id","original_event_native_HH",
 "first_original_native","last_original_native",
 "science_state","production_DATM_authorized"}
FIELDS=("site","episode_id","role","native_time","product",
 "tower_TA_C","tower_TA_QC","tower_VPD_hPa","tower_VPD_QC",
 "tower_RH_observed_pct","tower_RH_filled_pct",
 "tower_RH_implied_from_TA_VPD_pct",
 "ERA_TA_C","ERA_VPD_hPa","ERA_RH_product_pct",
 "ERA_RH_derived_from_TA_VPD_pct",
 "source_ERA_RH_Stage51_pct",
 "original_tower_source_match","missing_input_columns",
 "source_file","source_member","source_sha256",
 "science_approval","DATM_permission")
CANDIDATES=("TA_F","TA_F_QC","TA","TA_QC","VPD_F","VPD_F_QC","VPD","VPD_QC",
 "RH","RH_QC","RH_F","RH_F_QC","TA_ERA","VPD_ERA","RH_ERA")
def read(p,need):
 if not p.is_file() or p.is_symlink():raise ValueError("read-only source report missing "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f)
  names=r.fieldnames or []
  if not need.issubset(names) or len(set(names))!=len(names):
   raise ValueError("required original source fields missing "+str(p))
  out=list(r)
 if any(None in x or any(v is None for v in x.values()) for x in out):
  raise ValueError("malformed original source report "+str(p))
 return out
def fingerprint(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def parse(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("original local native timestamp invalid "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def clk(t,minutes):
 return (parse(t)+timedelta(minutes=minutes)).strftime("%Y%m%d%H%M")
def numeric(x):
 try:
  z=float(x)
  if math.isfinite(z) and z not in (-9999.,-6999.):return z
 except(TypeError,ValueError):pass
 return None
def saturation(t):
 if t is None or not -80<=t<=60:return None
 return 6.112*math.exp(17.67*t/(243.5+t))
def derived_rh(ta,vpd):
 t=numeric(ta);v=numeric(vpd)
 e=saturation(t)
 if e is None or v is None:return ""
 return round(100*(1-v/e),3)
def fmt(x):
 if x is None:return "NA"
 if x=="":return "NA"
 if isinstance(x,bool):return "yes" if x else "no"
 n=numeric(x)
 if n is not None:return f"{n:.3f}".rstrip("0").rstrip(".")
 if str(x).strip() in ("-9999","-9999.0","-6999","-6999.0"):return "NA(-9999)"
 return str(x)
def get(row,k):
 return row.get(k,"")
def read_product(p,member,times,col):
 if p.suffix.lower()==".zip":
  with zipfile.ZipFile(p) as z:
   if member not in z.namelist():raise ValueError("Stage52 source member absent "+member)
   with z.open(member) as f:
    return extract(f,times,col)
 with p.open("rb") as f:return extract(f,times,col)
def extract(f,times,col):
 rows={}
 r=csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
 fields=r.fieldnames or []
 if col not in fields or len(fields)!=len(set(fields)):
  raise ValueError("original source product clock/headers no longer valid")
 for row in r:
  t=row[col]
  if t not in times:continue
  if t in rows:raise ValueError("duplicate original source native HH "+t)
  rows[t]=row
 return rows,fields
def selftest():
 assert derived_rh(20,0)==100
 assert clk("200905191130",-60)=="200905191030"
 assert clk("201803121000",60)=="201803121100"
 assert sum(x[1] for x in TARGETS.values())==8
 print("STAGE53 SELF-TEST PASS | 3 original source events, 8 event HH + 12 context HH, direct TA/VPD/RH and source ERA; no writes to forcing")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage51-dir",type=Path)
 p.add_argument("--stage52-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage51_dir,a.stage52_dir,a.out)):
  p.error("original --stage51-dir, --stage52-dir and NEW --out required")
 d51,d52,out=(x.expanduser().resolve() for x in (a.stage51_dir,a.stage52_dir,a.out))
 if not d51.is_dir() or not d52.is_dir() or out.exists() or not out.parent.is_dir():
  p.error("original report directories must exist and new --out must not exist")
 if any(out in d.parents or d in out.parents or out==d for d in (d51,d52)):
  p.error("cannot overwrite original reports")
 f51event=d51/"stage51_THREE_NUMERIC_EVENT_HYPOTHESES_NEED_TOWER_VALIDATION.csv"
 f51native=d51/"stage51_THREE_EVENT_ALL_NATIVE_HH_UNAPPROVED_EVIDENCE.csv"
 f52product=d52/"stage52_THREE_EVENT_RAW_SOURCE_PRODUCT_INVENTORY.csv"
 original_events=read(f51event,REQ_EVENT)
 original_hh=read(f51native,REQ_NATIVE)
 products=read(f52product,REQUIRED_META)
 if len(original_events)!=3 or len(original_hh)!=8:
  raise ValueError("source 3 events, 8 original half-hours drifted")
 for r in original_events:
  if r["episode_id"] not in TARGETS or r["site"]!=TARGETS[r["episode_id"]][0] or int(r["original_event_native_HH"])!=TARGETS[r["episode_id"]][1]:
   raise ValueError("source originally validated event IDs/Half-hour drift")
  if r["science_state"]!="NUMERIC_ONLY_MUST_VALIDATE_ORIGINAL_STATION_METEO" or r["production_DATM_authorized"]!="NO":
   raise ValueError("source original event unexpectedly science-approved")
 if any(r["science_approval"]!="NO" or r["DATM_permission"]!="NO" for r in original_hh):
  raise ValueError("original native science approval unexpectedly changed")
 hh_index={(r["site"],r["native_time"]):r for r in original_hh}
 if len(hh_index)!=8:raise ValueError("repeated original site/native HH")
 windows={}
 events_by_site=defaultdict(list)
 for e in original_events:
  event=e["episode_id"];site=e["site"]
  first,last=e["first_original_native"],e["last_original_native"]
  if first not in [r["native_time"] for r in original_hh if r["episode_id"]==event]:
   raise ValueError("event source first native HH changed")
  native=[clk(first,30*i) for i in range(int(e["original_event_native_HH"]))]
  if native[-1]!=last or any((site,t) not in hh_index or hh_index[site,t]["episode_id"]!=event for t in native):
   raise ValueError("event original source clock/Half-hour continuity changed")
  before=[clk(first,-60),clk(first,-30)]
  after=[clk(last,30),clk(last,60)]
  windows[event]=[(t,"BEFORE" if t in before else "AFTER" if t in after else "EVENT") for t in before+native+after]
  events_by_site[site].append(event)
 product_rows=[]
 selected={}
 per_product_report=[]
 for site,events in sorted(events_by_site.items()):
  clocks={t for e in events for t,_ in windows[e]}
  opts=[x for x in products if x["site"]==site and int(x["target_times_matched"])>0]
  if not opts:raise ValueError("Stage52 original source product not found for "+site)
  for m in opts:
   path=Path(m["source_file"])
   if path.is_symlink() or not path.is_file():raise ValueError("Stage52 original raw source product no longer exists "+str(path))
   if fingerprint(path)!=m["source_file_SHA256"]:
    raise ValueError("original raw source scientific SHA changed "+str(path))
   member=m["source_member"]
   got,fields=read_product(path,member,clocks,m["timestamp_column"])
   name=(member or path.name).upper()
   # Product with original FLUXMET met is preferred; do not blend products.
   score=(int("TA_ERA" in fields)+int("VPD_ERA" in fields))*20+(
     10 if "FLUXMET_HH" in name else 5 if "FULLSET_HH" in name else 0)
   for event in events:
    for t,role in windows[event]:
     x=got.get(t,{})
     t_f=get(x,"TA_F");v_f=get(x,"VPD_F")
     source=hh_index.get((site,t))
     match=""
     if source:
      T=numeric(t_f);V=numeric(v_f)
      srcT=numeric(source["original_T_C"]);srcV=numeric(source["original_VPD_hPa"])
      match=("MATCH" if None not in (T,V,srcT,srcV) and
       abs(T-srcT)<=.002 and abs(V-srcV)<=.002 and
       get(x,"VPD_F_QC")==source["original_VPD_QC"] else "MISMATCH_OR_MISSING")
     row=dict(site=site,episode_id=event,role=role,native_time=t,
      product=member or path.name,tower_TA_C=t_f,tower_TA_QC=get(x,"TA_F_QC"),
      tower_VPD_hPa=v_f,tower_VPD_QC=get(x,"VPD_F_QC"),
      tower_RH_observed_pct=get(x,"RH"),tower_RH_filled_pct=get(x,"RH_F"),
      tower_RH_implied_from_TA_VPD_pct=derived_rh(t_f,v_f),
      ERA_TA_C=get(x,"TA_ERA"),ERA_VPD_hPa=get(x,"VPD_ERA"),
      ERA_RH_product_pct=get(x,"RH_ERA"),
      ERA_RH_derived_from_TA_VPD_pct=derived_rh(get(x,"TA_ERA"),get(x,"VPD_ERA")),
      source_ERA_RH_Stage51_pct=source["original_ERA_RH_pct"] if source else "",
      original_tower_source_match=match,
      missing_input_columns=";".join(y for y in ("TA_F","VPD_F","TA_ERA","VPD_ERA") if y not in fields),
      source_file=str(path),source_member=member,source_sha256=m["source_file_SHA256"],
      science_approval="NO",DATM_permission="NO")
     product_rows.append(row)
     key=(event,t)
     prev=selected.get(key)
     if x and (prev is None or score>prev[0]):
      selected[key]=(score,row)
   per_product_report.append((site,member or path.name,len(got),score))
 # Explicitly prevent silently mixing source products or inferring ERA5-Land
 mainrows=[]
 for event in sorted(windows):
  for t,role in windows[event]:
   item=selected.get((event,t))
   if item is None:
    mainrows.append(dict((k,"") for k in FIELDS))
    mainrows[-1].update(site=TARGETS[event][0],episode_id=event,role=role,
       native_time=t,product="SOURCE_MISSING",science_approval="NO",DATM_permission="NO")
   else:mainrows.append(item[1])
 if len(mainrows)!=20:raise ValueError("3 events require 8 event + 12 context HH")
 if any(r["role"]=="EVENT" and r["original_tower_source_match"]!="MATCH" for r in mainrows):
  raise ValueError("chosen original product does not match verified Stage51 T/VPD/QC")
 # The source ERA is NOT an independently downloaded ERA5-Land dataset.
 out.mkdir(exist_ok=False)
 for filename,rs in [
  ("stage53_20_HH_BEFORE_DURING_AFTER_PRIMARY_TOWER_SOURCE_ERA.csv",mainrows),
  ("stage53_ALL_RAW_PRODUCTS_EXACT_NATIVE_ROWS.csv",product_rows)]:
  with (out/filename).open("x",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");w.writeheader();w.writerows(rs)
 manifest=dict(stage51_SHA256={str(p):fingerprint(p) for p in (f51event,f51native)},
  stage52_inventory_SHA256=fingerprint(f52product),
  source_products=[{"file":p[1],"site":p[0],"matched_HH":p[2],"priority":p[3]} for p in per_product_report],
  source_original_event_HH=8,source_before_after_context_HH=12,
  primary_total_HH=20,original_scientific_approvals=0,
  original_FLUXMET_DATM_CIME_Slurm_modified=False,
  independent_ERA5_Land_observation_downloaded=False)
 (out/"stage53_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 display=["# AmeriFlux Batch05 — original tower vs source ERA before/during/after",
  "Source original local-native half-hour clock; one hour before + one hour after each event.",
  "**SOURCE TA_ERA/VPD_ERA is AmeriFlux's processed ERA companion, not an independent ERA5-Land extraction.**",
  "**Tower RH=-9999 means missing. RH implied from original TA_F/VPD_F is calculated, not a measured RH sensor.**"]
 display_cols=[("native_time","HH"),("role","Phase"),("tower_TA_C","Tower TA °C"),
   ("tower_TA_QC","TA QC"),("tower_VPD_hPa","Tower VPD hPa"),
   ("tower_VPD_QC","VPD QC"),("tower_RH_observed_pct","Tower RH raw"),
   ("tower_RH_implied_from_TA_VPD_pct","RH from Tower TA/VPD"),
   ("ERA_TA_C","Source TA_ERA °C"),("ERA_VPD_hPa","Source VPD_ERA hPa"),
   ("ERA_RH_product_pct","Source RH_ERA raw"),
   ("ERA_RH_derived_from_TA_VPD_pct","RH from ERA TA/VPD")]
 for event in sorted(windows):
  info=[x for x in original_events if x["episode_id"]==event][0]
  display+=["","## "+event+" — "+info["first_original_native"]+" to "+info["last_original_native"],
   "| "+" | ".join(x[1] for x in display_cols)+" |",
   "| "+" | ".join("---" for x in display_cols)+" |"]
  for x in mainrows:
   if x["episode_id"]!=event:continue
   display.append("| "+" | ".join(fmt(x.get(k,"")) for k,v in display_cols)+" |")
 display+=["","**All original model-input edits remain forbidden. No scientific approvals.**",
  "Original tower/T/VPD source event records were cross-verified against Stage51; all other context rows are original raw source product readings.",
  "If TA_ERA/VPD_ERA not supplied, values are NA and separate ERA5-Land extraction is required.",
  ""]
 (out/"STAGE53_SHOW_TOWER_AND_SOURCE_ERA_CONTEXT_3_EVENTS.md").write_text("\n".join(display)+"\n",encoding="utf-8")
 print("STAGE53 SUCCESS | 3 source events 8 original HH and 12 adjacent context HH | read-only")
 print("STAGE53 RAW_PRODUCTS",json.dumps(per_product_report))
 print("\n".join(display),flush=True)
 print("STAGE53_OUT="+str(out))
 print("STAGE53 ORIGINAL/166 APPROVED/46 P1 HOLD/10 RH PLATEAU/1574 P2P3/CLAUDE108/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

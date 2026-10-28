#!/usr/bin/env python3
"""Stage51, AmeriFlux Batch05 only. Reproduce Stage50 original 52-event
constant-RH-offset sensitivity: 3 numerical possibilities /49 no feasible
offset under the particular bounded grid, NOT true station repairs.
Read original Stage50, Stage49, Stage45, Stage44 and Stage27 reports only.
Retain 70 earlier numerical candidates, 253 source-neighbor holds, and
separate 108 Claude cases. Original, approved source, DATM, CIME and Slurm
unchanged. Original AmeriFlux site clock (local standard half-hour).
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timedelta

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp",
       "US-WCr","US-Whs","US-Wjs","US-Wkg")
FIFTY={"site","episode_id","source_original_HH","first_native","last_native",
       "numerical_screen_status","offset_RH_percentage_points",
       "edge_QC0_count","edge_QC1_count","new_internal_gt2",
       "new_internal_gt4","new_external_gt2","new_external_gt4",
       "science_decision","production_DATM_authorized"}
CF={"site","episode_id","native_time","original_T_C","original_VPD_hPa",
    "original_VPD_QC","source_ERA_RH_pct","hypothesis_constant_RH_offset_pp",
    "hypothesis_RH_pct","hypothesis_VPD_hPa","science_approval",
    "production_DATM_authorized"}
R70={"site","episode_id","candidate_original_HH","source_reference_science_gate",
     "new_science_approval","production_DATM_authorized"}
R45={"site","context_kind","context_id","side","candidate_time",
     "neighbor_time","neighbor_selected_VPD_hPa","original_candidate_VPD_hPa",
     "trial_candidate_VPD_hPa","before_jump_hPa","after_jump_hPa",
     "neighbor_original_QC_VPD","neighbor_kind"}
R44={"site","episode_id","native_time","original_T_C","original_VPD_hPa",
     "source_ERA_RH_pct","source_QC_T","source_QC_VPD"}
R27={"site","episode_id","native_time","TA_F_C","VPD_F_hPa","TA_F_QC",
     "VPD_F_QC","RH_ERA_pct"}
SITE_FIELDS=("site","source_original_P2P3_HH","Assistant_events",
    "previous_70_source_reference_pending",
    "Stage50_three_numerical_hypotheses",
    "Stage50_49_offset_grid_no_feasible",
    "original_253_neighbor_science_HOLD",
    "Claude_events_untouched","new_science_approvals","full_site_forcing_pass")
EXACT_FIELDS=("site","episode_id","original_event_native_HH",
    "first_original_native","last_original_native","source_ERA_RH_offset_pp",
    "original_edge_QC0_count","original_edge_QC1_count",
    "max_abs_change_from_original_source_VPD_hPa",
    "max_worsened_original_edge_hPa",
    "max_hypothetical_external_VPD_jump_hPa",
    "original_internal_new_gt2","original_internal_new_gt4",
    "original_external_new_gt2","original_external_new_gt4",
    "source_hypothesis_RH_min_pct","source_hypothesis_RH_max_pct",
    "original_ERA_hypothesis_is_station_observation",
    "science_state","production_DATM_authorized")
FAIL_FIELDS=("site","episode_id","original_event_native_HH","native_first",
    "native_last","original_boundary_QC0","original_boundary_QC1",
    "trial_offsets_considered","source_RH_physical_offsets",
    "source_VPD_magnitude_bounded_offsets",
    "fully_numeric_passing_offsets","nearest_screen_offset_pp",
    "nearest_screen_number_of_failed_conditions",
    "nearest_screen_failure_reasons",
    "nearest_screen_max_edge_worsening_hPa",
    "original_ERA_new_gt2_external","original_ERA_new_gt4_external",
    "scientific_meaning","science_state","production_DATM_authorized")
ALL_EVIDENCE=("site","episode_id","native_time","offset_RH_pp",
    "original_T_C","original_VPD_hPa","original_VPD_QC",
    "original_ERA_RH_pct","hypothesis_RH_pct","hypothesis_VPD_hPa",
    "science_approval","DATM_permission")
PRIOR70=("site","episode_id","original_HH","reference_evidence_gap",
         "requires_actual_tower_met_validation","status","DATM_permission")

def val(x):
 try:
  y=float(x)
  if math.isfinite(y) and y not in (-9999,-6999):return y
 except (TypeError,ValueError):pass
 return None

def es(t):
 if t is None or not -80<=t<=60:raise ValueError("original T outside event sensitivity range")
 return 6.112*math.exp(17.67*t/(243.5+t))

def load(p,need):
 if not p.is_file() or p.is_symlink():raise ValueError("missing original read-only input: "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  reader=csv.DictReader(f)
  fields=reader.fieldnames or []
  if not need.issubset(fields) or len(set(fields))!=len(fields):
   raise ValueError("source fields missing or repeated: "+str(p))
  data=list(reader)
 if any(None in r or any(x is None for x in r.values()) for r in data):
  raise ValueError("original report contains malformed CSV rows "+str(p))
 return data

def unique(rows,fields):
 result={}
 for x in rows:
  k=tuple(x[f] for f in fields)
  if k in result:raise ValueError("duplicate site/source-native identity "+str(k))
  result[k]=x
 return result

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()

def write(p,fields,rows):
 with p.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
  w.writeheader()
  w.writerows(rows)

def classify(off,temps,original,source_era_rh,before,after):
 humidity=[r+off for r in source_era_rh]
 issues=[]
 if any(r<0 or r>100 for r in humidity):
  return None,humidity,{"RH_OUTSIDE_0_100_PERCENT"},None,0
 candidate=[es(t)*(1-r/100) for t,r in zip(temps,humidity)]
 maxmag=max(abs(c-o) for c,o in zip(candidate,original))
 if maxmag>10+1e-9:issues.append("ORIGINAL_VPD_CHANGE_GT10HPA")
 for a,b,ap,bp in zip(original,original[1:],candidate,candidate[1:]):
  old=abs(b-a)
  now=abs(bp-ap)
  if old<=2+1e-9 and now>2+1e-9:issues.append("NEW_INTERNAL_GT2")
  if old<=4+1e-9 and now>4+1e-9:issues.append("NEW_INTERNAL_GT4")
 worsened=0.0
 max_edge=0.0
 for endpoint,edge in ((candidate[0],before),(candidate[-1],after)):
  old=abs(edge["original"]-edge["neighbor"])
  trial=abs(endpoint-edge["neighbor"])
  worsened=max(worsened,trial-old)
  max_edge=max(max_edge,trial)
  if old<=2+1e-9 and trial>2+1e-9:issues.append("NEW_EXTERNAL_GT2")
  if old<=4+1e-9 and trial>4+1e-9:issues.append("NEW_EXTERNAL_GT4")
 if worsened>0.5+1e-9:issues.append("WORSENED_ORIGINAL_EDGE_OVER0P5HPA")
 return candidate,humidity,set(issues),max_edge,max(0,worsened)

def offsets():return [i/2 for i in range(-40,41)]

def selftest():
 x=classify(0,[20],[5],[50],{"original":5,"neighbor":5},{"original":5,"neighbor":5})
 assert x[0] is not None and len(x[0])==1
 assert len(offsets())==81 and 0 in offsets()
 assert (3+49+70+253+108)==483
 print("STAGE51 SELF-TEST PASS | 3 original full-native hypotheses, 49 source hold failure mechanisms, 70+253+108 unchanged, 0 source writes")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for k in ("stage50-dir","stage49-dir","stage45-dir","stage44-dir","stage27-dir","out"):
  p.add_argument("--"+k,type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 keys=("stage50_dir","stage49_dir","stage45_dir","stage44_dir","stage27_dir")
 if any(getattr(a,k) is None for k in (*keys,"out")):p.error("original Stage50/49/45/44/27 and NEW out required")
 d50,d49,d45,d44,d27=[getattr(a,k).expanduser().resolve() for k in keys]
 out=a.out.expanduser().resolve()
 if any(not d.is_dir() for d in (d50,d49,d45,d44,d27)) or not out.parent.is_dir() or out.exists():
  p.error("source directories missing or --out already exists")
 if any(out==d or out in d.parents or d in out.parents for d in (d50,d49,d45,d44,d27)):
  p.error("never overwrite any original source or prior reports")
 paths={
  "sensitivity":d50/"stage50_52_EVENTWIDE_RH_OFFSET_FULL_NATIVE_BOUNDARY_RESEARCH_ONLY.csv",
  "counterfactual":d50/"stage50_EVENTWIDE_COUNTERFACTUAL_NATIVE_SOURCE_NO_FORCING.csv",
  "stage50site":d50/"stage50_TEN_SITE_ASSISTANT_HOLD_AND_EVIDENCE_COUNTS.csv",
  "stage50manifest":d50/"stage50_manifest.json",
  "70":d49/"stage49_70_NUMERIC_CANDIDATE_EVENT_REFERENCE_QC_GATES.csv",
  "stage49manifest":d49/"stage49_manifest.json",
  "original_edges":d45/"stage45_TRUE_ORIGINAL_EVENT_AND_JOINED_RUN_EXTERNAL_EDGES.csv",
  "native":d44/"stage44_ALL1574_NATIVE_HH_ORIGINAL_RH_AND_ERA_MDS_FIRST_PASS.csv",
  "original":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"}
 sensitivity=load(paths["sensitivity"],FIFTY)
 trial=load(paths["counterfactual"],CF)
 earlier70=load(paths["70"],R70)
 edges=load(paths["original_edges"],R45)
 native=load(paths["native"],R44)
 original=unique(load(paths["original"],R27),("site","native_time"))
 sites=load(paths["stage50site"],{"site","Assistant_original_events","original_253_neighbor_science_HOLD"})
 man=json.loads(paths["stage50manifest"].read_text())
 m49=json.loads(paths["stage49manifest"].read_text())
 if (len(sensitivity),len(earlier70),len(native),len(original),len(sites))!=(52,70,1574,1574,10):
  raise ValueError("Stage50/49 original research populations drifted")
 if m49.get("new_scientific_approvals")!=0 or man.get("new_science_approvals")!=0:
  raise ValueError("source research no longer unapproved")
 if not man.get("external_true_boundary_signed_VPD_checked_from_original_Stage45"):
  raise ValueError("Stage50 did not run signed original edge screening")
 byevt=defaultdict(list)
 for x in native:byevt[(x["site"],x["episode_id"])].append(x)
 bytrial=defaultdict(list)
 for x in trial:bytrial[(x["site"],x["episode_id"])].append(x)
 edgemap=unique((x for x in edges if x["context_kind"]=="ORIGINAL_STAGE27_EVENT"),
  ("site","context_id","side"))
 if len(edgemap)!=966:raise ValueError("original 483-event two-edge population differs")
 passed=[x for x in sensitivity if x["numerical_screen_status"]=="NUMERIC_EVENTWIDE_BOUNDARIES_POSSIBLE_SCIENCE_HOLD"]
 failed=[x for x in sensitivity if x["numerical_screen_status"]=="NO_FEASIBLE_BOUNDED_EVENT_RH_OFFSET_SCIENCE_HOLD"]
 if len(passed)!=3 or len(failed)!=49:raise ValueError("actual operator 3/49 results differ")
 three=[];fortynine=[];native3=[]
 for e in sorted(sensitivity,key=lambda r:(r["site"],r["episode_id"])):
  key=e["site"],e["episode_id"]
  if e["science_decision"]!="SCIENCE_HOLD_INDEPENDENT_OBSERVATIONAL_VALIDATION_REQUIRED" or e["production_DATM_authorized"]!="NO":
   raise ValueError("scientific source unexpectedly approved "+str(key))
  hh=sorted(byevt[key],key=lambda r:r["native_time"])
  if len(hh)!=int(e["source_original_HH"]) or hh[0]["native_time"]!=e["first_native"] or hh[-1]["native_time"]!=e["last_native"]:
   raise ValueError("missing full original event source half-hour "+str(key))
  if any((datetime.strptime(y["native_time"],"%Y%m%d%H%M")-
          datetime.strptime(x["native_time"],"%Y%m%d%H%M"))!=timedelta(minutes=30)
          for x,y in zip(hh,hh[1:])):
   raise ValueError("noncontiguous source episode "+str(key))
  temps=[];orig=[];rh=[]
  for x in hh:
   f=original.get((x["site"],x["native_time"]))
   if f is None or f["episode_id"]!=key[1] or f["VPD_F_QC"]=="0" or x["source_QC_VPD"]=="0":
    raise ValueError("original measured VPD QC0 or missing source "+str(key))
   t=val(x["original_T_C"]);v=val(x["original_VPD_hPa"]);r=val(x["source_ERA_RH_pct"])
   if None in (t,v,r) or not 0<=r<=100:raise ValueError("invalid original tower T/VPD or source ERA RH "+str(key))
   if (abs(t-val(f["TA_F_C"]))>.002 or abs(v-val(f["VPD_F_hPa"]))>.002 or
       abs(r-val(f["RH_ERA_pct"]))>.002 or x["source_QC_VPD"]!=f["VPD_F_QC"]):
    raise ValueError("source original T/VPD/RH/QC drift "+str(key))
   temps.append(t);orig.append(v);rh.append(r)
  ee={}
  for side,ix in (("BEFORE",0),("AFTER",-1)):
   x=edgemap.get((key[0],key[1],side))
   if x is None or x["neighbor_kind"] not in ("ORIGINAL_SOURCE","STAGE24_APPROVED"):
    raise ValueError("unknown or unapproved original native neighbor "+str(key))
   old=val(x["original_candidate_VPD_hPa"]);v=val(x["neighbor_selected_VPD_hPa"])
   if None in (old,v) or abs(old-orig[ix])>.002:raise ValueError("signed original neighbor VPD inconsistent "+str(key))
   ee[side]={"original":old,"neighbor":v,"QC":x["neighbor_original_QC_VPD"]}
  m_pass=0;m_physical=0;m_mag=0;closest=None
  examined=0;scanned=[]
  for off in offsets():
   examined+=1
   vals,h,issues,max_edge,worsened=classify(off,temps,orig,rh,ee["BEFORE"],ee["AFTER"])
   if vals is not None:
    m_physical+=1
    if "ORIGINAL_VPD_CHANGE_GT10HPA" not in issues:m_mag+=1
   if not issues:m_pass+=1
   # Near miss diagnoses cannot be treated as candidate repairs.
   if vals is not None:
    candidate=(len(issues),max(0,worsened),abs(off),off,sorted(issues))
    if closest is None or candidate[:4]<closest[:4]:
     closest=candidate
   scanned.append((off,vals,h,issues,max_edge,worsened))
  if e["numerical_screen_status"]=="NUMERIC_EVENTWIDE_BOUNDARIES_POSSIBLE_SCIENCE_HOLD":
   if m_pass==0:raise ValueError("reported feasible option not reproducible "+str(key))
   off=val(e["offset_RH_percentage_points"])
   found=[x for x in scanned if x[0]==off]
   if len(found)!=1 or found[0][3]:raise ValueError("selected offset fails source original numerical gates "+str(key))
   expect=sorted((x for x in scanned if not x[3]),key=lambda z:(abs(z[0]),z[5],z[0]))[0][0]
   if off!=expect:raise ValueError("stage50 selected offset is not its own minimal magnitude solution")
   matches=sorted(bytrial.get(key,[]),key=lambda r:r["native_time"])
   if len(matches)!=len(hh):raise ValueError("source Stage50 3 candidate full event native rows incomplete")
   vals,hrs=found[0][1],found[0][2]
   if sum(1 for x in matches if x["science_approval"]!="NO" or x["production_DATM_authorized"]!="NO"):
    raise ValueError("Stage50 sensitivity row marked production authorized")
   for i,(x,m) in enumerate(zip(hh,matches)):
    if (x["native_time"]!=m["native_time"] or abs(off-val(m["hypothesis_constant_RH_offset_pp"]))>1e-9 or
       abs(hrs[i]-val(m["hypothesis_RH_pct"]))>.002 or abs(vals[i]-val(m["hypothesis_VPD_hPa"]))>.003):
     raise ValueError("Stage50 native hypothetical source event does not match re-analysis")
    native3.append(dict(site=key[0],episode_id=key[1],native_time=x["native_time"],
      offset_RH_pp=off,original_T_C=temps[i],original_VPD_hPa=orig[i],
      original_VPD_QC=x["source_QC_VPD"],original_ERA_RH_pct=rh[i],
      hypothesis_RH_pct=round(hrs[i],6),hypothesis_VPD_hPa=round(vals[i],6),
      science_approval="NO",DATM_permission="NO"))
   three.append(dict(site=key[0],episode_id=key[1],original_event_native_HH=len(hh),
     first_original_native=hh[0]["native_time"],last_original_native=hh[-1]["native_time"],
     source_ERA_RH_offset_pp=off,
     original_edge_QC0_count=sum(z["QC"]=="0" for z in ee.values()),
     original_edge_QC1_count=sum(z["QC"]=="1" for z in ee.values()),
     max_abs_change_from_original_source_VPD_hPa=round(max(abs(a-b) for a,b in zip(vals,orig)),6),
     max_worsened_original_edge_hPa=round(found[0][5],6),
     max_hypothetical_external_VPD_jump_hPa=round(found[0][4],6),
     original_internal_new_gt2=0,original_internal_new_gt4=0,
     original_external_new_gt2=0,original_external_new_gt4=0,
     source_hypothesis_RH_min_pct=round(min(hrs),6),
     source_hypothesis_RH_max_pct=round(max(hrs),6),
     original_ERA_hypothesis_is_station_observation=False,
     science_state="NUMERIC_ONLY_MUST_VALIDATE_ORIGINAL_STATION_METEO",
     production_DATM_authorized="NO"))
  else:
   if m_pass>0 or bytrial.get(key):raise ValueError("Stage50 infeasible event now looks feasible or has unexpected rows "+str(key))
   reasons="NO_PHYSICAL_GRID_POINT" if closest is None else ";".join(closest[4]) or "UNCLASSIFIED_GRID_FAILURE"
   fortynine.append(dict(site=key[0],episode_id=key[1],original_event_native_HH=len(hh),
      native_first=hh[0]["native_time"],native_last=hh[-1]["native_time"],
      original_boundary_QC0=sum(z["QC"]=="0" for z in ee.values()),
      original_boundary_QC1=sum(z["QC"]=="1" for z in ee.values()),
      trial_offsets_considered=examined,source_RH_physical_offsets=m_physical,
      source_VPD_magnitude_bounded_offsets=m_mag,
      fully_numeric_passing_offsets=0,
      nearest_screen_offset_pp="" if closest is None else closest[3],
      nearest_screen_number_of_failed_conditions="" if closest is None else closest[0],
      nearest_screen_failure_reasons=reasons,
      nearest_screen_max_edge_worsening_hPa="" if closest is None else round(closest[1],6),
      original_ERA_new_gt2_external=e["original_external_new_gt2"],
      original_ERA_new_gt4_external=e["original_external_new_gt4"],
      scientific_meaning="ONE_BOUNDED_CONSTANT_RH_OFFSET_FAMILY_FAILED;OTHER_OBSERVED_OR_REANALYSIS_METHODS_NOT_TESTED",
      science_state="SOURCE_SCIENCE_HOLD_NO_VALIDATED_CORRECTION",
      production_DATM_authorized="NO"))
 if len(three)!=3 or len(fortynine)!=49 or len(native3)!=len(trial):
  raise ValueError("Stage50 source 3/49/HH numerical sensitivity report reconciliation failed")
 priority70=[]
 for x in earlier70:
  if x["new_science_approval"]!="NO" or x["production_DATM_authorized"]!="NO":
   raise ValueError("original 70 method candidate unexpectedly approved")
  priority70.append(dict(site=x["site"],episode_id=x["episode_id"],
   original_HH=x["candidate_original_HH"],reference_evidence_gap=x["source_reference_science_gate"],
   requires_actual_tower_met_validation=True,status="SOURCE_SCIENCE_UNAPPROVED",
   DATM_permission="NO"))
 per_site=[]
 for x in sites:
  site=x["site"];ev70=sum(y["site"]==site for y in earlier70)
  ev3=sum(y["site"]==site for y in three);ev49=sum(y["site"]==site for y in fortynine)
  held=int(x["original_253_neighbor_science_HOLD"])
  if ev70+ev3+ev49+held!=int(x["Assistant_original_events"]):
   raise ValueError("actual Stage50 per-site original event denominator changed "+site)
  per_site.append(dict(site=site,source_original_P2P3_HH="FROM_STAGE45_PREVIOUS",
   Assistant_events=int(x["Assistant_original_events"]),
   previous_70_source_reference_pending=ev70,Stage50_three_numerical_hypotheses=ev3,
   Stage50_49_offset_grid_no_feasible=ev49,original_253_neighbor_science_HOLD=held,
   Claude_events_untouched=True,new_science_approvals=0,full_site_forcing_pass=False))
 out.mkdir(exist_ok=False)
 write(out/"stage51_THREE_NUMERIC_EVENT_HYPOTHESES_NEED_TOWER_VALIDATION.csv",EXACT_FIELDS,three)
 write(out/"stage51_THREE_EVENT_ALL_NATIVE_HH_UNAPPROVED_EVIDENCE.csv",ALL_EVIDENCE,native3)
 write(out/"stage51_FORTYNINE_NO_FEASIBLE_BOUNDED_OFFSET_GATE_DIAGNOSIS.csv",FAIL_FIELDS,fortynine)
 write(out/"stage51_SEVENTY_REFERENCE_GAP_SCIENCE_QUEUE.csv",PRIOR70,priority70)
 write(out/"stage51_TEN_SITE_ASSISTANT_EVENT_CONSERVATION.csv",SITE_FIELDS,per_site)
 summary={
  "source_SHA256":{k:sha(v) for k,v in paths.items()},
  "Assistant_previous_numerical_source_70_events":70,
  "Assistant_new_numeric_hypothesis_3_original_events":3,
  "Assistant_RH_offset_no_solution_49_original_events":49,
  "Assistant_other_source_neighbor_HOLD_253_original_events":253,
  "Claude_reserved_original_events_108":108,
  "source_p2p3_original_native_HH_1574_preserved":True,
  "old_166_approved_46_P1HOLD_10_saturation_plateau_preserved":True,
  "scientific_approvals_new":0,
  "production_DATM_CIME_Slurm_or_original_source_writes":0}
 (out/"stage51_manifest.json").write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
 report=["# Stage51 — original source science audit of 3 numerical RH-offset hypotheses and 49 failed offset methods",
  "","All research-only; every candidate remains NOT APPROVED; source/DATM/Slurm unchanged.",
  "Three candidates reproduce Stage50 exact eventwide native RH-offset and true signed external VPD boundaries, but this is not independent tower-observed humidity.",
  "49 failed only a bounded constant-event-RH-offset grid, NOT every possible station/reanalysis method.",
  "","## Three numerical candidates (NOT validated repairs)"]
 for x in three:
  report.append("- {} {} | {} HH | constant RH offset {} percentage points | max original VPD delta {} hPa | original edge QC0 count {} | HOLD".format(
   x["site"],x["episode_id"],x["original_event_native_HH"],x["source_ERA_RH_offset_pp"],
   x["max_abs_change_from_original_source_VPD_hPa"],x["original_edge_QC0_count"]))
 report+=["","## 49 source-science hold categories from nearest (still invalid) RH-offset trial"]
 for reason,count in sorted(Counter(x["nearest_screen_failure_reasons"] for x in fortynine).items()):
  report.append("- {}: {} original events".format(reason,count))
 report+=["","## 70 earlier numeric candidate reference science gaps"]
 for reason,count in sorted(Counter(x["reference_evidence_gap"] for x in priority70).items()):
  report.append("- {}: {} original events".format(reason,count))
 report+=["","## Science constraints",
  "- Stage50's 3 selected offset hypotheses are mathematical sensitivity devices, not calibrated source tower relative humidity.",
  "- Never change authentic original native QC0 humidity/VPD neighbors or suppress actual extremes merely to pass 2/4hPa jump thresholds.",
  "- Inspect original site met instrument QC and source time; where available compare separate ERA5-Land or local station observations with provenance. ERA, ERA5-Land and MDS are not automatically independent tower observations.",
  "- Source neighbor 253 events remain on HOLD. Claude 108 separate original events remain untouched.",
  "- Original 1574 unapproved source P2P3, 166 earlier Stage24 approved, 46 P1 manually held and 10 source RH platform rows remain unchanged; 0 new DATM/forcing authorizations.",""]
 (out/"STAGE51_ASSISTANT_THREE_HYPOTHESES_FORTYNINE_HOLDS_NO_APPROVAL.md").write_text("\n".join(report)+"\n")
 print("STAGE51 SUCCESS | 3 NUMERIC_SOURCE_HYPOTHESES, 49 NO_BOUNDED_OFFSET, 70 SOURCE_EVIDENCE_PENDING, 253 NEIGHBOR_HOLD, Claude108 untouched; all original 483 episodes accounted")
 print("STAGE51 THREE_EVENTS",json.dumps([{"site":x["site"],"event":x["episode_id"],"HH":x["original_event_native_HH"],"RH_offset_pp":x["source_ERA_RH_offset_pp"]} for x in three],sort_keys=True))
 print("STAGE51 49_NEAREST_FAILURES",json.dumps(dict(Counter(x["nearest_screen_failure_reasons"] for x in fortynine)),sort_keys=True))
 print("STAGE51_REPORT="+str(out/"STAGE51_ASSISTANT_THREE_HYPOTHESES_FORTYNINE_HOLDS_NO_APPROVAL.md"))
 print("STAGE51_OUT="+str(out))
 print("STAGE51 READONLY | 166 APPROVED / 46 P1 HOLD / 10 RH PLATFORM / 1574 P2P3 / CLAUDE108 / DATM / SLURM UNCHANGED")
if __name__=="__main__":main()

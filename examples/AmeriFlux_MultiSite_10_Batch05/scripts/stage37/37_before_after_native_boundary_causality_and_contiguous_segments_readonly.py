#!/usr/bin/env python3
"""Stage37 Batch05: original VPD jumps BEFORE vs AFTER the 251 isolated
Stage36 research-only RH repairs. Never approve a forcing replacement.

Scientific purpose: Stage36 reported 65/65 original episodes with boundary
or unapproved-neighbor review, 94 trial external transitions >2 hPa, 21 >4.
Those counts ALONE cannot distinguish preexisting source jumps from new
trial-introduced jumps. Stage37 compares ORIGINAL candidate VPD against the
EXACT SAME adjacent selected native neighbor (original FLUXMET or previously
approved Stage24 value) and repeats with the Stage36 research trial VPD.

Explicitly separate:
* new threshold crossings, already-large jumps improved or worsened;
* neighbor original VPD QC0 versus QC2/other, implied native RH<10%;
* neighbor P2/P3, manual P1 HOLD, original RH saturation platform;
* partial source episodes and contiguous run/fragment boundaries.

Output is read-only report, *never* a modification of the 166 already
approved Stage24 records or original 46 human P1 HOLD/1574 P2P3.
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

COLUMNS_C={"site","native_time","episode_id","original_VPD_hPa",
 "hypothetical_VPD_preserve_processed_source_ERA_RH_hPa",
 "original_VPD_QC","existing_QC0_VPD_sensor_record_protected",
 "original_relative_humidity_plausibility"}
COLUMNS_E={"site","episode_id","trial_native_time","adjacent_side",
 "adjacent_native_time","adjacent_original_VPD_hPa",
 "adjacent_original_VPD_QC","adjacent_implied_RH_water_pct",
 "adjacent_status","adjacent_current_selected_VPD_hPa",
 "trial_source_ERA_RH_VPD_hPa","trial_vs_adjacent_selected_VPD_jump_hPa",
 "neighbor_QC2_or_not_measured","neighbor_RH_below10pct_or_unphysical",
 "neighbor_is_unapproved_P2P3"}
COLUMNS_EP={"site","episode_id","original_episode_unapproved_HH",
 "trial_selected_HH","boundary_jump_gt2hPa","boundary_jump_gt4hPa",
 "partial_original_episode_not_fully_selected"}
COLUMNS35={"site","native_time","review_lane","original_VPD_hPa",
 "tower_VPD_trial_keep_source_ERA_RH_hPa"}
ECOLS=("site","episode_id","candidate_native","adjacent_side",
 "neighbor_native","neighbor_source_class",
 "neighbor_original_VPD_QC","neighbor_original_RH_water_pct",
 "candidate_original_VPD_hPa","candidate_trial_VPD_hPa",
 "neighbor_selected_VPD_hPa",
 "original_chronological_signed_jump_hPa",
 "trial_chronological_signed_jump_hPa",
 "original_abs_jump_hPa","trial_abs_jump_hPa",
 "absolute_jump_change_trial_minus_original_hPa",
 "source_original_above2","source_trial_above2",
 "source_original_above4","source_trial_above4",
 "NEW_threshold2_crossing","NEW_threshold4_crossing",
 "WORSENED_gt0_5hPa","IMPROVED_at_least0_5hPa",
 "original_neighbor_QC0_measured",
 "original_neighbor_QC2_or_not_measured",
 "neighbor_RH_below10pct_or_unphysical",
 "neighbor_is_unapproved_P2P3",
 "border_review_decision")
SEG_COLS=("site","episode_id","segment_number_within_episode",
 "segment_first_native","segment_last_native","segment_native_HH",
 "original_episode_unapproved_HH","total_episode_selected_HH",
 "episode_is_only_partially_selected",
 "before_boundary_original_abs_jump_hPa",
 "before_boundary_trial_abs_jump_hPa",
 "after_boundary_original_abs_jump_hPa",
 "after_boundary_trial_abs_jump_hPa",
 "new_gt2_boundary_count","new_gt4_boundary_count",
 "improved_boundary_count","worsened_boundary_count",
 "QC2_or_other_nonmeasured_neighbor_count",
 "unapproved_P2P3_neighbor_count",
 "original_neighbor_RH_below10pct_count",
 "segment_science_gate")
EVENT_COLS=("site","episode_id","original_episode_unapproved_HH",
 "trial_selected_HH","number_of_contiguous_trial_segments",
 "partial_original_episode",
 "external_edges_checked","original_gt2_edges","trial_gt2_edges",
 "original_gt4_edges","trial_gt4_edges",
 "new_gt2_edges","new_gt4_edges",
 "improved_edges_gt0_5","worsened_edges_gt0_5",
 "unapproved_external_P2P3_neighbors",
 "QC2_or_other_nonmeasured_external_neighbors",
 "suspicious_RH_external_neighbors",
 "event_science_gate")
GT2,GT4=2.0,4.0
EPS=1e-7
DELTA=0.5

def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def num(s):
 try:
  v=float(s)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except (TypeError,ValueError):pass
 return None
def validdate(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad native time "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def tadd(s,mins):return (validdate(s)+timedelta(minutes=mins)).strftime("%Y%m%d%H%M")
def boolstr(x):
 if x not in ("True","False"):raise ValueError("expected explicit boolean, got "+repr(x))
 return x=="True"
def read(path,needed):
 if not path.is_file() or path.is_symlink():raise ValueError("Original report missing or symlink "+str(path))
 with path.open("r",newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f)
  fields=r.fieldnames or []
  if not needed.issubset(fields) or len(fields)!=len(set(fields)):
   raise ValueError("Source schema drift "+str(path))
  rows=list(r)
 if any(None in x or any(v is None for v in x.values()) for x in rows):
  raise ValueError("bad source CSV "+str(path))
 return rows
def idx(rows,keyfields):
 result={}
 for row in rows:
  k=tuple(row[x] for x in keyfields)
  if k in result:raise ValueError("duplicate source key "+str(k))
  result[k]=row
 return result
def record_before_after(candidate,edge):
 side=edge["adjacent_side"]
 if side not in ("BEFORE","AFTER"):raise ValueError("unknown original side")
 if edge["site"]!=candidate["site"] or edge["episode_id"]!=candidate["episode_id"] or edge["trial_native_time"]!=candidate["native_time"]:
  raise ValueError("Stage36 source trial/edge mismatch")
 expected=tadd(candidate["native_time"],-30 if side=="BEFORE" else 30)
 if edge["adjacent_native_time"]!=expected:raise ValueError("original FLUXMET native time not adjacent")
 source=num(candidate["original_VPD_hPa"])
 trial=num(candidate["hypothetical_VPD_preserve_processed_source_ERA_RH_hPa"])
 neighbor=num(edge["adjacent_current_selected_VPD_hPa"])
 if None in (source,trial,neighbor):raise ValueError("source/trial/adjacent VPD missing")
 if abs(num(edge["trial_source_ERA_RH_VPD_hPa"])-trial)>0.00001:
  raise ValueError("Stage36 actual trial VPD changed")
 if edge["adjacent_status"]=="ADJACENT_SAME_TRIAL_CANDIDATE":
  return None
 # For edge BEFORE: candidate minus previous neighbor; for AFTER:
 # next neighbor minus candidate. Sign is chronological, unlike Stage36's
 # reversed sign convention; thresholds use absolute values regardless.
 orig_jump=(source-neighbor) if side=="BEFORE" else (neighbor-source)
 new_jump=(trial-neighbor) if side=="BEFORE" else (neighbor-trial)
 orig=abs(orig_jump);new=abs(new_jump)
 if abs(new-abs(num(edge["trial_vs_adjacent_selected_VPD_jump_hPa"])))>0.00001:
  raise ValueError("Stage36 signed boundary magnitude vs recompute mismatch")
 change=new-orig
 new2=orig<=GT2+EPS and new>GT2+EPS
 new4=orig<=GT4+EPS and new>GT4+EPS
 worsened=change>DELTA+EPS
 improved=change<-DELTA-EPS
 qc=edge["adjacent_original_VPD_QC"]
 if boolstr(edge["neighbor_QC2_or_not_measured"]) != (qc!="0"):
  raise ValueError("QC flag from Stage36 changed")
 low=boolstr(edge["neighbor_RH_below10pct_or_unphysical"])
 neighbor_rh=num(edge["adjacent_implied_RH_water_pct"])
 if low != (neighbor_rh is None or not 10<=neighbor_rh<=100):
  raise ValueError("original neighbor RH physical screen changed")
 unapproved=boolstr(edge["neighbor_is_unapproved_P2P3"])
 if unapproved != (edge["adjacent_status"]=="ADJACENT_OTHER_P2P3_ORIGINAL_UNAPPROVED_DIAGNOSTIC"):
  raise ValueError("external P2P3 neighbor status and flag mismatch")
 state=("NEW_GT4_AFTER_TRIAL" if new4 else
        "NEW_GT2_AFTER_TRIAL" if new2 else
        "WORSENED_ABS_GT0_5" if worsened else
        "IMPROVED_ABS_AT_LEAST0_5" if improved else
        "STABLE_OR_SMALL_CHANGE_STILL_PROVENANCE_REVIEW")
 return dict(site=candidate["site"],episode_id=candidate["episode_id"],
  candidate_native=candidate["native_time"],adjacent_side=side,
  neighbor_native=edge["adjacent_native_time"],
  neighbor_source_class=edge["adjacent_status"],
  neighbor_original_VPD_QC=qc,
  neighbor_original_RH_water_pct=neighbor_rh if neighbor_rh is not None else "",
  candidate_original_VPD_hPa=source,candidate_trial_VPD_hPa=trial,
  neighbor_selected_VPD_hPa=neighbor,
  original_chronological_signed_jump_hPa=round(orig_jump,8),
  trial_chronological_signed_jump_hPa=round(new_jump,8),
  original_abs_jump_hPa=round(orig,8),trial_abs_jump_hPa=round(new,8),
  absolute_jump_change_trial_minus_original_hPa=round(change,8),
  source_original_above2=orig>GT2+EPS,source_trial_above2=new>GT2+EPS,
  source_original_above4=orig>GT4+EPS,source_trial_above4=new>GT4+EPS,
  NEW_threshold2_crossing=new2,NEW_threshold4_crossing=new4,
  WORSENED_gt0_5hPa=worsened,IMPROVED_at_least0_5hPa=improved,
  original_neighbor_QC0_measured=qc=="0",
  original_neighbor_QC2_or_not_measured=qc!="0",
  neighbor_RH_below10pct_or_unphysical=low,
  neighbor_is_unapproved_P2P3=unapproved,
  border_review_decision=state+"__NOT_FORCING_APPROVED")

def segments(candidates):
 groups=defaultdict(list)
 for r in candidates:groups[r["site"],r["episode_id"]].append(r)
 out=[]
 for key,rr in sorted(groups.items()):
  sorted_rows=sorted(rr,key=lambda x:x["native_time"])
  chunk=[]
  for r in sorted_rows:
   if chunk and tadd(chunk[-1]["native_time"],30)!=r["native_time"]:
    out.append((key,len([x for x in out if x[0]==key])+1,chunk))
    chunk=[]
   chunk.append(r)
  if chunk:out.append((key,len([x for x in out if x[0]==key])+1,chunk))
 return out

def write(path,fields,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def check_source(d36,d35):
 fcan=d36/"stage36_251_ISOLATED_TRIAL_ONLY_source_ERA_RH_at_original_T.csv"
 fe=d36/"stage36_502_ORIGINAL_ZIP_NATIVE_NEIGHBOR_VPD_QC_TRANSITIONS.csv"
 fep=d36/"stage36_ALL_EPISODE_RISK_AND_TRIAL_DECISION_MATRIX.csv"
 f35=d35/"stage35_429_NATIVE_TOWER_VPD_TWO_ERA_METHODS_REVIEW_ONLY.csv"
 m=json.loads((d36/"stage36_manifest.json").read_text())
 m35=json.loads((d35/"stage35_manifest.json").read_text())
 if (m.get("native_candidate_trial_HH"),m.get("source_matched_original_neighbor_comparisons"),
     m.get("original_episode_groups"),m.get("new_scientific_approvals"))!=(251,502,65,0):
  raise ValueError("Stage36 source original cohort / science state changed")
 if m.get("Stage35_source_SHA256",{}).get("Stage35_429_research_VPD")!=digest(f35):
  raise ValueError("Stage36 and actual original Stage35 source SHA disagree")
 if (m35.get("trial_native_HH_count"),m35.get("review_lanes",{}).get(
  "P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF"))!=(429,251):
  raise ValueError("Stage35 source 429/251 classification changed")
 can=read(fcan,COLUMNS_C)
 raw=read(fe,COLUMNS_E)
 eps=read(fep,COLUMNS_EP)
 all35=idx(read(f35,COLUMNS35),("site","native_time"))
 if (len(can),len(raw),len(eps),len(all35))!=(251,502,65,429):
  raise ValueError("Stage36/35 source CSV counts changed")
 ci=idx(can,("site","native_time"))
 episodes=idx(eps,("site","episode_id"))
 if any(r["existing_QC0_VPD_sensor_record_protected"]!="False" for r in can):
  raise ValueError("unexpected QC0 original science record in low risk 251")
 for c in can:
  k=c["site"],c["native_time"]
  s=all35.get(k)
  if (s is None or s["review_lane"]!="P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF"
      or abs(num(s["tower_VPD_trial_keep_source_ERA_RH_hPa"])-num(c["hypothetical_VPD_preserve_processed_source_ERA_RH_hPa"]))>0.00001
      or abs(num(s["original_VPD_hPa"])-num(c["original_VPD_hPa"]))>0.00001):
   raise ValueError("Stage36 trial candidate differs from exact Stage35 source "+str(k))
 edges=idx(raw,("site","trial_native_time","adjacent_side"))
 if len(edges)!=502:
  raise ValueError("original two native edges per candidate expected")
 for c in can:
  for side in ("BEFORE","AFTER"):
   if (c["site"],c["native_time"],side) not in edges:
    raise ValueError("missing one true original boundary "+str(c))
 return can,raw,eps,ci,episodes,edges,{
  "Stage36_original_trial251":digest(fcan),
  "Stage36_original_502_boundaries":digest(fe),
  "Stage36_original_65_episodes":digest(fep),
  "Stage36_original_manifest":digest(d36/"stage36_manifest.json"),
  "Stage35_original429_source":digest(f35)}

def selftest():
 c=dict(site="US-Vcp",episode_id="E",native_time="200805241500",
  original_VPD_hPa="6",hypothetical_VPD_preserve_processed_source_ERA_RH_hPa="2")
 e=dict(site="US-Vcp",episode_id="E",trial_native_time="200805241500",
  adjacent_side="BEFORE",adjacent_native_time="200805241430",
  adjacent_current_selected_VPD_hPa="1",trial_source_ERA_RH_VPD_hPa="2",
  trial_vs_adjacent_selected_VPD_jump_hPa="-1",
  adjacent_original_VPD_QC="2",neighbor_QC2_or_not_measured="True",
  adjacent_implied_RH_water_pct="55",
  neighbor_RH_below10pct_or_unphysical="False",
  neighbor_is_unapproved_P2P3="False",
  adjacent_status="ADJACENT_UNMODIFIED_SOURCE_ORIGINAL")
 z=record_before_after(c,e)
 assert z["original_abs_jump_hPa"]==5
 assert z["trial_abs_jump_hPa"]==1
 assert z["IMPROVED_at_least0_5hPa"]
 c2=dict(c,original_VPD_hPa="1.2",hypothetical_VPD_preserve_processed_source_ERA_RH_hPa="6.3")
 e2=dict(e,trial_source_ERA_RH_VPD_hPa="6.3",
  trial_vs_adjacent_selected_VPD_jump_hPa="-5.3")
 z2=record_before_after(c2,e2)
 assert z2["NEW_threshold4_crossing"] and z2["WORSENED_gt0_5hPa"]
 assert not z2["IMPROVED_at_least0_5hPa"]
 assert tadd("200812312330",30)=="200901010000"
 print("STAGE37 SELF-TEST PASS | original-vs-trial jump causality, threshold crossing, exact 30-min clock, zero forcing changes")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage36-dir",type=Path)
 p.add_argument("--stage35-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if a.stage36_dir is None or a.stage35_dir is None or a.out is None:
  p.error("--stage36-dir, --stage35-dir, --out required")
 d36=a.stage36_dir.expanduser().resolve()
 d35=a.stage35_dir.expanduser().resolve()
 out=a.out.expanduser().resolve()
 if (not d36.is_dir() or not d35.is_dir() or out.exists() or not out.parent.is_dir()
     or any(out==d or out in d.parents or d in out.parents for d in (d36,d35))):
  p.error("only new disjoint report directory allowed")
 can,original_edges,orig_episodes,ci,events,edges,hashes=check_source(d36,d35)
 comparisons=[]
 for row in original_edges:
  candidate=ci[row["site"],row["trial_native_time"]]
  z=record_before_after(candidate,row)
  if z is not None:comparisons.append(z)
 if not comparisons:raise ValueError("no true external boundaries; unexpected 65 source episode science statuses")
 if len(comparisons)==0 or len(comparisons)>502:raise ValueError("invalid external boundary count")
 if sum(r["source_trial_above2"] for r in comparisons)!=94 or sum(
    r["source_trial_above4"] for r in comparisons)!=21:
  raise ValueError("Stage36 published 94/21 external boundary diagnostic mismatch")
 grouped=defaultdict(list)
 for r in comparisons:grouped[r["site"],r["episode_id"]].append(r)
 runs=segments(can)
 seg_out=[]
 for (site_eid,index,rr) in runs:
  site,eid=site_eid
  left,right=rr[0]["native_time"],rr[-1]["native_time"]
  before=next((r for r in comparisons if r["site"]==site and r["episode_id"]==eid and
         r["candidate_native"]==left and r["adjacent_side"]=="BEFORE"),None)
  after=next((r for r in comparisons if r["site"]==site and r["episode_id"]==eid and
         r["candidate_native"]==right and r["adjacent_side"]=="AFTER"),None)
  # This segment definition is maximal contiguous trial half-hours in the
  # same ORIGINAL source episode. Each run has two external neighbor edges.
  if before is None or after is None:
   raise ValueError("maximal native contiguous run has no two external boundaries "+str(site_eid))
  boundaries=[before,after]
  epi=events[site,eid]
  count=int(epi["original_episode_unapproved_HH"])
  coverage=int(epi["trial_selected_HH"])
  risks=dict(new2=sum(x["NEW_threshold2_crossing"] for x in boundaries),
    new4=sum(x["NEW_threshold4_crossing"] for x in boundaries),
    improved=sum(x["IMPROVED_at_least0_5hPa"] for x in boundaries),
    worsened=sum(x["WORSENED_gt0_5hPa"] for x in boundaries),
    qc_nonmeas=sum(x["original_neighbor_QC2_or_not_measured"] for x in boundaries),
    p2=sum(x["neighbor_is_unapproved_P2P3"] for x in boundaries),
    rh_low=sum(x["neighbor_RH_below10pct_or_unphysical"] for x in boundaries))
  label=("NEW_OR_WORSENED_GT4_BOUNDARY_REVIEW" if risks["new4"] or any(
    x["source_trial_above4"] and x["WORSENED_gt0_5hPa"] for x in boundaries) else
    "NEW_OR_WORSENED_GT2_BOUNDARY_REVIEW" if risks["new2"] or any(
    x["source_trial_above2"] and x["WORSENED_gt0_5hPa"] for x in boundaries) else
    "ALREADY_SUSPICIOUS_OR_UNAPPROVED_NEIGHBOR_REVIEW" if risks["p2"] or risks["rh_low"] or risks["qc_nonmeas"] else
    "PARTIAL_EPISODE_OR_UNCERTAIN_EVENT_REVIEW" if coverage!=count else
    "NUMERIC_BOUNDARY_SCREEN_REDUCED_NOT_APPROVED")
  seg_out.append(dict(
   site=site,episode_id=eid,segment_number_within_episode=index,
   segment_first_native=left,segment_last_native=right,
   segment_native_HH=len(rr),
   original_episode_unapproved_HH=count,
   total_episode_selected_HH=coverage,
   episode_is_only_partially_selected=coverage!=count,
   before_boundary_original_abs_jump_hPa=before["original_abs_jump_hPa"],
   before_boundary_trial_abs_jump_hPa=before["trial_abs_jump_hPa"],
   after_boundary_original_abs_jump_hPa=after["original_abs_jump_hPa"],
   after_boundary_trial_abs_jump_hPa=after["trial_abs_jump_hPa"],
   new_gt2_boundary_count=risks["new2"],new_gt4_boundary_count=risks["new4"],
   improved_boundary_count=risks["improved"],
   worsened_boundary_count=risks["worsened"],
   QC2_or_other_nonmeasured_neighbor_count=risks["qc_nonmeas"],
   unapproved_P2P3_neighbor_count=risks["p2"],
   original_neighbor_RH_below10pct_count=risks["rh_low"],
   segment_science_gate=label))
 if sum(int(r["segment_native_HH"]) for r in seg_out)!=251:
  raise ValueError("original source candidate segmented count mismatch")
 if 2*len(seg_out)!=len(comparisons):
  raise ValueError("two external boundaries per segment verification failed")
 ep_out=[]
 seg_per=Counter((s["site"],s["episode_id"]) for s in seg_out)
 for ep in orig_episodes:
  key=ep["site"],ep["episode_id"]
  if key not in seg_per:raise ValueError("stage36 original event unexpectedly absent "+str(key))
  rr=grouped.get(key,[])
  if not rr:raise ValueError("original event has no external boundaries")
  if sum(x["source_trial_above2"] for x in rr)!=int(ep["boundary_jump_gt2hPa"]) or sum(
      x["source_trial_above4"] for x in rr)!=int(ep["boundary_jump_gt4hPa"]):
   raise ValueError("Stage36 original event abnormal jump accounting changed")
  def count(prop):return sum(bool(x[prop]) for x in rr)
  new2=count("NEW_threshold2_crossing")
  new4=count("NEW_threshold4_crossing")
  worsened=count("WORSENED_gt0_5hPa")
  improved=count("IMPROVED_at_least0_5hPa")
  qc=count("original_neighbor_QC2_or_not_measured")
  low=count("neighbor_RH_below10pct_or_unphysical")
  unapproved=count("neighbor_is_unapproved_P2P3")
  original4=count("source_original_above4")
  trial4=count("source_trial_above4")
  label=("NEW_GT4_AT_EVENT_BOUNDARY" if new4 else
    "WORSENED_GT4" if trial4 and worsened else
    "NEW_GT2_AT_EVENT_BOUNDARY" if new2 else
    "WORSENED_GT2" if count("source_trial_above2") and worsened else
    "SOURCE_NEIGHBOR_QC_OR_OTHER_P2P3_UNRESOLVED" if qc or low or unapproved else
    "OLD_JUMP_PERSISTED_BUT_NO_NEW_THRESHOLDS" if count("source_trial_above2") else
    "LOWER_NUMERIC_RISK_STILL_NOT_APPROVED")
  ep_out.append(dict(site=key[0],episode_id=key[1],
    original_episode_unapproved_HH=ep["original_episode_unapproved_HH"],
    trial_selected_HH=ep["trial_selected_HH"],
    number_of_contiguous_trial_segments=seg_per[key],
    partial_original_episode=boolstr(ep["partial_original_episode_not_fully_selected"]),
    external_edges_checked=len(rr),
    original_gt2_edges=count("source_original_above2"),
    trial_gt2_edges=count("source_trial_above2"),
    original_gt4_edges=original4,trial_gt4_edges=trial4,
    new_gt2_edges=new2,new_gt4_edges=new4,
    improved_edges_gt0_5=improved,worsened_edges_gt0_5=worsened,
    unapproved_external_P2P3_neighbors=unapproved,
    QC2_or_other_nonmeasured_external_neighbors=qc,
    suspicious_RH_external_neighbors=low,event_science_gate=label))
 if len(ep_out)!=65:raise ValueError("expected 65 original source events")
 if sum(r["external_edges_checked"] for r in ep_out)!=len(comparisons):
  raise ValueError("external boundary event matrix accounting mismatch")
 counts=dict(
  original_external_jump_gt2=sum(x["source_original_above2"] for x in comparisons),
  trial_external_jump_gt2=sum(x["source_trial_above2"] for x in comparisons),
  original_external_jump_gt4=sum(x["source_original_above4"] for x in comparisons),
  trial_external_jump_gt4=sum(x["source_trial_above4"] for x in comparisons),
  newly_crossed_2hPa=sum(x["NEW_threshold2_crossing"] for x in comparisons),
  newly_crossed_4hPa=sum(x["NEW_threshold4_crossing"] for x in comparisons),
  improved_abs_jump_by_at_least0_5hPa=sum(x["IMPROVED_at_least0_5hPa"] for x in comparisons),
  worsened_abs_jump_by_gt0_5hPa=sum(x["WORSENED_gt0_5hPa"] for x in comparisons),
  neighbor_original_QC2_or_unmeasured=sum(x["original_neighbor_QC2_or_not_measured"] for x in comparisons),
  neighbor_still_unapproved_P2P3=sum(x["neighbor_is_unapproved_P2P3"] for x in comparisons),
  neighbor_implied_RH_below10_or_unphysical=sum(x["neighbor_RH_below10pct_or_unphysical"] for x in comparisons))
 manifest=dict(stage="Stage37",SHA256_exact_previous_sources=hashes,
  source_trial_original_native_HH=251,
  original_episode_count=65,
  contiguous_trial_segments=len(seg_out),
  external_physical_boundaries=len(comparisons),
  boundary_delta_method="Same neighbor selected original/Stage24-approved VPD held fixed; compare raw candidate original versus hypothetical source-ERA-RH trial. No repairs enacted.",
  threshold_units="hPa",screen_thresholds_not_acceptance_rules={"jump": [2,4],"difference":0.5},
  science_counts=counts,
  episode_review_lanes=dict(Counter(r["event_science_gate"] for r in ep_out)),
  segment_review_lanes=dict(Counter(r["segment_science_gate"] for r in seg_out)),
  original_source_251_forcing_approvals=0,
  original_P2P3_1574_still_unapproved=True,
  Stage24_approved_166_preserved=True,
  original_P1_manual_HOLD_46_preserved=True,
  original_10_saturation_platform_untouched=True,
  BIF_UTC_OFFSET_DATE_END_missing=True,
  original_FLUXMET_DATM_CIME_Slurm_changed=False)
 out.mkdir(exist_ok=False)
 write(out/"stage37_EXTERNAL_NATIVE_BOUNDARIES_ORIGINAL_VS_TRIAL_CAUSALITY.csv",ECOLS,comparisons)
 write(out/"stage37_251_NATIVE_CONTIGUOUS_TRIAL_SEGMENT_GATES.csv",SEG_COLS,seg_out)
 write(out/"stage37_65_EPISODES_BEFORE_AFTER_PRIORITIES.csv",EVENT_COLS,ep_out)
 (out/"stage37_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 report=["# Stage37 — before-vs-after original/isolated-trial source VPD edges",
  "","**Source and DATM forcing unchanged; NO science approvals**.",
  "Stage36 had 251 possible trials in 65 original US-Vcp P2/P3 events. Its",
  "94 external >2 hPa and 21 external >4 hPa are *hypothetical AFTER-TRIAL* jumps;",
  "they do not by themselves prove whether a repair created a new discontinuity.",
  "This stage compares absolute original VPD jump to hypothetical post-trial jump",
  "against exactly the same source-native adjacent half-hour. Existing approved",
  "Stage24 overlay neighboring VPD is held fixed for this *diagnostic*, not rewritten.",
  "Source native QC2/unapproved P2P3 neighbors may themselves be physically bad;",
  "lowering a jump to them is not evidence of actual tower humidity.",
  "All native times remain original local standard time, with original BIF DATE_END missing.",
  "","## 251 native HH / 65 original episodes — evidence"]
 for key,value in counts.items():report.append("- **"+key+"**: "+str(value))
 report+=["","## 65 original episode risk grouping"]
 for key,v in sorted(manifest["episode_review_lanes"].items()):
  report.append("- **{}**: {} episodes".format(key,v))
 report+=["","## Maximal contiguous trial run/segments"]
 for key,v in sorted(manifest["segment_review_lanes"].items()):
  report.append("- **{}**: {} contiguous segments".format(key,v))
 report+=["","## Human review ordering",
  "1. Compare \`newly_crossed_4hPa\` and \`worsened_abs_jump_by_gt0_5hPa\` against the old original jumps: prioritize genuine trial-created worsening.",
  "2. If original and trial boundaries both already large, investigate the *original adjacent QC2 / P2P3 source* before expanding a trial. No adjacent record is automatically amended.",
  "3. Separate contiguous trial segments from partially selected 65 original episodes; do NOT join distant dates or interpolate across unapproved records.",
  "4. H01 US-Vcm two suspicious QC2 original neighbors, H02-H05 P1 46 original HOLD total, RH platforms 10 and remaining P2P3 1574 are excluded from this Stage37 US-Vcp trial.",
  "5. A lower boundary jump is a numerical diagnostic, not independent observed meteorological proof or authorization to produce a new versioned overlay.",
  "","**All 166 prior-approved source overlay HH remain unchanged.**",""]
 # no escaped Markdown backticks in Python strings.
 (out/"STAGE37_BEFORE_AFTER_EDGE_AND_SEGMENT_DECISION.md").write_text("\n".join(report)+"\n",encoding="utf-8")
 print("STAGE37 SUCCESS | original251 vs hypothetical251; 65 original episodes;",
       len(seg_out),"contiguous source segments;",len(comparisons),"UNIQUE external native edges")
 print("STAGE37 ACTUAL_OLD_VS_HYPOTHETICAL_TRIAL",json.dumps(counts,sort_keys=True))
 print("STAGE37 EPISODE_LANES",json.dumps(manifest["episode_review_lanes"],sort_keys=True))
 print("STAGE37 SEGMENT_LANES",json.dumps(manifest["segment_review_lanes"],sort_keys=True))
 print("STAGE37_REPORT="+str(out/"STAGE37_BEFORE_AFTER_EDGE_AND_SEGMENT_DECISION.md"))
 print("STAGE37_OUT="+str(out))
 print("STAGE37 ALL_SOURCE/APPROVED166/P1HOLD46/P2P3_1574/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

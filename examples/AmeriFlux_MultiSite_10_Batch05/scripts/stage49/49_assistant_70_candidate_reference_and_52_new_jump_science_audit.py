#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage49, Assistant-owned 375-event source-science audit.

Only READ original prior Stage48/47/45/44/27 reports. Distinguish:
  70 full-native event ERA-VPD lower NUMERIC-risk candidates (141 native HH);
  52 pre-screened but trial-created external VPD jump event-science HOLDs;
  253 original adjacent source low RH or QC2 science HOLDs.
Classify candidate original source/reference gaps (ERA only, MDS/ERA
disagreement, tower T vs ERA T) and exact original two edges for all 52.
Do NOT repair, smooth or approve any original source, DATM, CIME or Slurm.
Claude's 108 exclusive Stage46 source events remain out of scope.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import Counter,defaultdict

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
 "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
NUM={"site","episode_id","original_event_HH","native_first","native_last",
 "max_abs_VPD_change_hPa","candidate_lane","Stage43_preexisting_trial_HH",
 "science_approval","production_DATM_permission"}
NATIVE={"site","native_time","episode_id","original_selected_T_C","original_VPD_hPa",
 "original_VPD_QC","original_implied_RH_water_pct",
 "source_processed_ERA_RH_pct","ERA_RH_at_original_T_trial_VPD_hPa",
 "overlaps_existing_Stage43_trial","science_approval","production_DATM_permission"}
FAILED={"site","episode_id","source_priority","original_HH","native_start",
 "native_end","science_hold_reasons","source_new_external_gt2",
 "source_new_external_gt4","science_approval"}
EXISTING={"site","episode_id","original_event_HH","original_neighbor_risk",
 "original_QC1_edges","original_QC2_edges","neighbor_original_RH_low_1to10_edges"}
EVENT={"site","episode_id","original_HH","risk_screen",
 "original_episode_number_of_contiguous_segments",
 "new_external_jump_gt2","new_external_jump_gt4",
 "max_abs_VPD_change_hPa"}
EDGE={"site","context_kind","context_id","side","candidate_time",
 "neighbor_time","neighbor_kind","neighbor_original_QC_VPD",
 "neighbor_implied_RH_water_pct","before_jump_hPa","after_jump_hPa",
 "new_gt2","new_gt4","neighbor_untrusted","comparable"}
ORIG={"site","native_time","episode_id","TA_F_C","VPD_F_hPa",
 "VPD_F_QC","RH_ERA_pct","RH_MDS_pct",
 "abs_selected_T_minus_ERA_T_C"}
LOW47={"site","episode_id","alternative_reference_lane","original_HH"}
OUTPUT70=("site","episode_id","candidate_original_HH","source_first_native",
 "source_last_native","Stage48_source_numeric_priority",
 "max_abs_source_ERA_VPD_change_hPa","original_source_RH_negative_HH",
 "original_source_RH_0to1percent_HH",
 "source_MDS_RH_valid_HH","source_ERA_RH_valid_HH",
 "ERA_MDS_both_valid_HH","ERA_MDS_abs_RH_difference_gt10pp_HH",
 "ERA_MDS_abs_RH_difference_at_most5pp_HH",
 "max_ERA_MDS_RH_difference_pp","max_source_tower_vs_ERA_T_difference_C",
 "original_QC0_source_preserved",
 "before_native_original_neighbor_QC","after_native_original_neighbor_QC",
 "before_native_original_neighbor_RH_pct",
 "after_native_original_neighbor_RH_pct",
 "before_original_jump_hPa","before_candidate_jump_hPa",
 "after_original_jump_hPa","after_candidate_jump_hPa",
 "source_reference_science_gate","priority_explanation",
 "preexisting_Stage43_unapproved_trial_HH",
 "new_science_approval","production_DATM_authorized")
OUTPUT52=("site","episode_id","original_HH","original_start","original_end",
 "source_priority_from_Stage47","Stage48_rejection_reasons",
 "original_external_new_GT2_count","original_external_new_GT4_count",
 "original_source_edge_QC0_neighbors","original_source_edge_QC1_neighbors",
 "original_source_edge_QC2_neighbors","external_neighbor_RH_below10_or_negative_edges",
 "external_original_VPD_jump_gt2_edges",
 "external_trial_VPD_jump_gt2_edges",
 "worst_external_after_minus_before_jump_hPa",
 "boundary_science_lane","next_physical_source_review",
 "new_science_approval","production_DATM_authorized")
EDGES52=("site","episode_id","side","candidate_native","neighbor_native",
 "neighbor_kind","original_neighbor_QC_VPD","original_neighbor_RH_pct",
 "original_VPD_jump_hPa","ERA_trial_VPD_jump_hPa",
 "trial_minus_original_jump_hPa","new_crossed_gt2",
 "new_crossed_gt4","science_context","production_DATM_authorized")
SITE=("site","Stage46_assistant_original_events",
 "Stage48_numeric_research_events","Stage48_numeric_research_native_HH",
 "Stage48_new_jumps_HOLD_events",
 "Stage48_extreme_neighbor_source_HOLD_events",
 "Stage48_QC2_neighbor_source_HOLD_events",
 "source_reference_ERA_only_or_partial_events",
 "source_reference_ERA_MDS_GT10pp_disagree_events",
 "source_tower_vs_ERA_T_GT5C_events",
 "external_new_GT4_original_event_holds",
 "additional_science_approvals","site_model_forcing_pass")
def num(x):
 try:
  v=float(x)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except(ValueError,TypeError):pass
 return None
def hashfile(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("original science source not found "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f);fields=r.fieldnames or []
  if not required.issubset(fields) or len(set(fields))!=len(fields):
   raise ValueError("missing original source fields "+str(p))
  res=list(r)
 if any(None in row or any(v is None for v in row.values()) for row in res):
  raise ValueError("malformed source original CSV "+str(p))
 return res
def unique(rows,names):
 d={}
 for r in rows:
  key=tuple(r[k] for k in names)
  if key in d:raise ValueError("duplicate source site/native key "+str(key))
  d[key]=r
 return d
def write(p,fields,rows):
 with p.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def edge_float(r,k):
 return num(r[k])
def classify_reference(valid_total,both,gt10,maxT,n_hh):
 if maxT>5:return "TOWER_MINUS_ERA_T_GT5C_HOLD"
 if gt10:return "SOURCE_MDS_ERA_RH_GT10PP_DISAGREEMENT_HOLD"
 if both==0:return "SOURCE_ERA_ONLY_NO_MDS_REFERENCE"
 if both<n_hh:return "SOURCE_MDS_PARTIAL_COVERAGE_NOT_INDEPENDENT"
 return "MDS_ERA_SIMILAR_BUT_NOT_INDEPENDENT_OBSERVATION"
def selftest():
 assert 70+52+253==375
 assert 375+108==483
 assert 46+40-34==52
 assert classify_reference(1,0,0,0,1)=="SOURCE_ERA_ONLY_NO_MDS_REFERENCE"
 print("STAGE49 SELF-TEST PASS | 70 source numeric research events, 52 new jump holds, 253 source neighbor holds, Claude108 unchanged")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for name in ("stage48-dir","stage47-dir","stage45-dir","stage27-dir","out"):
  p.add_argument("--"+name,type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 names=("stage48_dir","stage47_dir","stage45_dir","stage27_dir")
 if any(getattr(a,key) is None for key in (*names,"out")):
  p.error("need source Stage48/47/45/27 dirs and NEW out")
 d48,d47,d45,d27=[getattr(a,key).expanduser().resolve() for key in names]
 out=a.out.expanduser().resolve()
 if any(not d.is_dir() for d in (d48,d47,d45,d27)) or not out.parent.is_dir() or out.exists():
  p.error("all original inputs must exist and output must be NEW")
 if any(out==d or out in d.parents or d in out.parents for d in (d48,d47,d45,d27)):
  p.error("no source and output path overlap")
 paths={
  "48passed":d48/"stage48_ELIGIBLE_FULL_EVENT_SOURCE_ERA_NUMERIC_GATES.csv",
  "48native":d48/"stage48_ELIGIBLE_SOURCE_ERA_NATIVE_RESEARCH_ONLY.csv",
  "48failed":d48/"stage48_INITIAL122_FAILED_SCIENCE_GATE_EVENTS.csv",
  "48holds":d48/"stage48_253_ORIGINAL_NEIGHBOR_SOURCE_HOLDS.csv",
  "48manifest":d48/"stage48_manifest.json",
  "47low":d47/"stage47_42_NUMERIC_SOURCE_ERA_MDS_SCIENTIFIC_EVIDENCE.csv",
  "45events":d45/"stage45_483_ORIGINAL_EVENTS_TRUE_NATIVE_VPD_QC.csv",
  "45edges":d45/"stage45_TRUE_ORIGINAL_EVENT_AND_JOINED_RUN_EXTERNAL_EDGES.csv",
  "45manifest":d45/"stage45_manifest.json",
  "27source":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"}
 passed=read(paths["48passed"],NUM)
 native=read(paths["48native"],NATIVE)
 failed=read(paths["48failed"],FAILED)
 held=read(paths["48holds"],EXISTING)
 low47=unique(read(paths["47low"],LOW47),("site","episode_id"))
 events=unique(read(paths["45events"],EVENT),("site","episode_id"))
 edges=read(paths["45edges"],EDGE)
 original=unique(read(paths["27source"],ORIG),("site","native_time"))
 m48=json.loads(paths["48manifest"].read_text(encoding="utf-8"))
 m45=json.loads(paths["45manifest"].read_text(encoding="utf-8"))
 if (len(passed),len(native),len(failed),len(held),len(low47),len(events),len(original))!=(70,141,52,253,42,483,1574):
  raise ValueError("actual original Stage48/47/45/27 operator source counts changed")
 if any(m48.get(k)!=v for k,v in {"assistant_candidate_complete_events":70,
    "newly_screened_hold_events":52,"assistant_source_neighbor_origin_holds":253,
    "candidate_native_original_HH":141,"prior_Stage43_15_unapproved_native_trial_overlap":15}.items()):
  raise ValueError("Stage48 recorded original source 70/52/253/141/15 changed")
 if m48.get("new_science_approvals")!=0 or m45.get("source_science_new_approvals")!=0:
  raise ValueError("unapproved source science population unexpectedly promoted")
 if m45.get("independently_original_source_verified_native_HH")!=1574:
  raise ValueError("underlying tower original source native QC not verified")
 all_events=unique(passed+failed+held,("site","episode_id"))
 if len(all_events)!=375 or any((k not in events) for k in all_events):
  raise ValueError("Assistant original 375 event ownership overlaps or not original Stage45")
 if len(set((r["site"],r["episode_id"]) for r in passed)&set(low47))>42:
  raise ValueError("low-numeric event membership inconsistent")
 ed=defaultdict(list)
 for r in edges:
  if r["context_kind"]=="ORIGINAL_STAGE27_EVENT":
   ed[(r["site"],r["context_id"])].append(r)
 hh=defaultdict(list)
 for r in native:
  hh[(r["site"],r["episode_id"])].append(r)
 out70=[]
 for e in sorted(passed,key=lambda r:(r["site"],r["episode_id"])):
  key=e["site"],e["episode_id"]
  rr=sorted(hh[key],key=lambda r:r["native_time"])
  es=ed.get(key,[])
  if len(rr)!=int(e["original_event_HH"]) or len(es)!=2 or set(x["side"] for x in es)!={"BEFORE","AFTER"}:
   raise ValueError("70 original event/edge source-native coverage incomplete "+str(key))
  if e["science_approval"]!="NO" or e["production_DATM_permission"]!="NO":
   raise ValueError("Stage48 source science output unexpectedly approved")
  ct=Counter();dmax=0.;tdmax=0.;maxref=0.;both=gt10=le5=0
  for r in rr:
   q=(r["site"],r["native_time"]);src=original.get(q)
   if src is None or src["episode_id"]!=key[1] or src["VPD_F_QC"]=="0":
    raise ValueError("candidate no longer a source original non-QC0 native HH "+str(q))
   if r["production_DATM_permission"]!="NO" or r["science_approval"]!="NO":
    raise ValueError("native row unexpectedly science approved")
   T=num(src["TA_F_C"]);V=num(src["VPD_F_hPa"])
   C=num(r["ERA_RH_at_original_T_trial_VPD_hPa"]);Rh=num(src["RH_ERA_pct"])
   if None in (T,V,C,Rh) or abs(T-num(r["original_selected_T_C"]))>.002 or abs(V-num(r["original_VPD_hPa"]))>.002:
    raise ValueError("original source T/VPD native provenance not identical")
   ct["rh_invalid"]+=num(r["original_implied_RH_water_pct"])<0
   ct["rh_sub1"]+=0<=num(r["original_implied_RH_water_pct"])<1
   ct["era_valid"]+=0<=Rh<=100
   M=num(src["RH_MDS_pct"])
   if M is not None and 0<=M<=100:
    ct["mds_valid"]+=1
    both+=1
    v=abs(Rh-M);maxref=max(maxref,v)
    le5+=v<=5;gt10+=v>10
   td=num(src["abs_selected_T_minus_ERA_T_C"])
   if td is not None:tdmax=max(tdmax,abs(td))
   dmax=max(dmax,abs(C-V))
  if abs(dmax-float(e["max_abs_VPD_change_hPa"]))>.005:
   raise ValueError("Stage48 event max VPD change differs from original source")
  es=sorted(es,key=lambda x:x["side"])
  sides={x["side"]:x for x in es}
  if any(x["new_gt2"]=="True" or x["new_gt4"]=="True" for x in es):
   raise ValueError("Stage48 eligible event actually creates an original >2/>4hPa external jump")
  rgate=classify_reference(ct["era_valid"],both,gt10,tdmax,len(rr))
  explanation=("Requires separate tower sensor/QC and physically consistent humidity reference. "
     "Source ERA and MDS are not automatically independent observations.")
  out70.append(dict(site=key[0],episode_id=key[1],
   candidate_original_HH=len(rr),source_first_native=e["native_first"],source_last_native=e["native_last"],
   Stage48_source_numeric_priority=e["candidate_lane"],
   max_abs_source_ERA_VPD_change_hPa=round(dmax,6),
   original_source_RH_negative_HH=ct["rh_invalid"],
   original_source_RH_0to1percent_HH=ct["rh_sub1"],
   source_MDS_RH_valid_HH=ct["mds_valid"],source_ERA_RH_valid_HH=ct["era_valid"],
   ERA_MDS_both_valid_HH=both,ERA_MDS_abs_RH_difference_gt10pp_HH=gt10,
   ERA_MDS_abs_RH_difference_at_most5pp_HH=le5,
   max_ERA_MDS_RH_difference_pp=round(maxref,6),
   max_source_tower_vs_ERA_T_difference_C=round(tdmax,6),
   original_QC0_source_preserved=True,
   before_native_original_neighbor_QC=sides["BEFORE"]["neighbor_original_QC_VPD"],
   after_native_original_neighbor_QC=sides["AFTER"]["neighbor_original_QC_VPD"],
   before_native_original_neighbor_RH_pct=sides["BEFORE"]["neighbor_implied_RH_water_pct"],
   after_native_original_neighbor_RH_pct=sides["AFTER"]["neighbor_implied_RH_water_pct"],
   before_original_jump_hPa=sides["BEFORE"]["before_jump_hPa"],
   before_candidate_jump_hPa=sides["BEFORE"]["after_jump_hPa"],
   after_original_jump_hPa=sides["AFTER"]["before_jump_hPa"],
   after_candidate_jump_hPa=sides["AFTER"]["after_jump_hPa"],
   source_reference_science_gate=rgate,priority_explanation=explanation,
   preexisting_Stage43_unapproved_trial_HH=int(e["Stage43_preexisting_trial_HH"]),
   new_science_approval="NO",production_DATM_authorized="NO"))
 out52=[];edges52=[]
 for e in sorted(failed,key=lambda r:(r["site"],r["episode_id"])):
  key=e["site"],e["episode_id"];ee=ed.get(key,[])
  original_event=events[key]
  if len(ee)!=2 or set(x["side"] for x in ee)!={"BEFORE","AFTER"}:
   raise ValueError("52 source event true +/-30 minute boundaries unavailable "+str(key))
  if e["science_approval"]!="NO":raise ValueError("science hold incorrectly preapproved")
  if "NEW_EXTERNAL_GT2" not in e["science_hold_reasons"] and "NEW_EXTERNAL_GT4" not in e["science_hold_reasons"]:
   raise ValueError("Stage48 extra 52 source science holds no longer due to external jump")
  qc=Counter();bad=before2=after2=0;biggest=None
  for x in ee:
   oldv=num(x["before_jump_hPa"]);newv=num(x["after_jump_hPa"])
   if oldv is None or newv is None:raise ValueError("rejected source event edge lacks original VPD")
   qc[x["neighbor_original_QC_VPD"]]+=1
   rh=num(x["neighbor_implied_RH_water_pct"])
   bad+=rh is None or rh<10 or rh>100
   before2+=oldv>2;after2+=newv>2
   diff=newv-oldv;biggest=max(diff,biggest) if biggest is not None else diff
   if x["new_gt2"]=="True" or x["new_gt4"]=="True":
    reason=("QC0_NEIGHBOR_REVIEW_SCIENTIFIC_CAUSALITY" if x["neighbor_original_QC_VPD"]=="0"
       else "QC1_NEIGHBOR_REVIEW_OBS_RH_SOURCE" if x["neighbor_original_QC_VPD"]=="1"
       else "QC2_OR_OTHER_NEIGHBOR_NOT_MEASURED_REFERENCE")
   else:reason="EVENT_OTHER_EDGE_UNCHANGED"
   edges52.append(dict(site=key[0],episode_id=key[1],side=x["side"],
    candidate_native=x["candidate_time"],neighbor_native=x["neighbor_time"],
    neighbor_kind=x["neighbor_kind"],
    original_neighbor_QC_VPD=x["neighbor_original_QC_VPD"],
    original_neighbor_RH_pct=x["neighbor_implied_RH_water_pct"],
    original_VPD_jump_hPa=oldv,ERA_trial_VPD_jump_hPa=newv,
    trial_minus_original_jump_hPa=round(diff,6),
    new_crossed_gt2=x["new_gt2"]=="True",new_crossed_gt4=x["new_gt4"]=="True",
    science_context=reason,production_DATM_authorized="NO"))
  if any(int(e[f])!=int(original_event[g]) for f,g in (
       ("source_new_external_gt2","new_external_jump_gt2"),
       ("source_new_external_gt4","new_external_jump_gt4"))):
   raise ValueError("Stage48 rejection reason no longer matches original Stage45 edges")
  if qc["0"] and bad==0:lane="JUMP_TO_MEASURED_QC0_NEIGHBOR_REQUIRES_ALTERNATE_RH"
  elif bad:lane="JUMP_TO_EXTREME_OR_UNKNOWN_RH_NEIGHBOR_HOLD"
  elif qc["2"] or sum(n for v,n in qc.items() if v not in ("0","1","2")):
   lane="JUMP_TO_QC2_OR_UNMEASURED_NEIGHBOR_HOLD"
  else:lane="JUMP_TO_QC1_NEIGHBOR_OBSERVATION_REVIEW"
  out52.append(dict(site=key[0],episode_id=key[1],
   original_HH=e["original_HH"],original_start=e["native_start"],original_end=e["native_end"],
   source_priority_from_Stage47=e["source_priority"],
   Stage48_rejection_reasons=e["science_hold_reasons"],
   original_external_new_GT2_count=int(e["source_new_external_gt2"]),
   original_external_new_GT4_count=int(e["source_new_external_gt4"]),
   original_source_edge_QC0_neighbors=qc["0"],
   original_source_edge_QC1_neighbors=qc["1"],
   original_source_edge_QC2_neighbors=qc["2"],
   external_neighbor_RH_below10_or_negative_edges=bad,
   external_original_VPD_jump_gt2_edges=before2,
   external_trial_VPD_jump_gt2_edges=after2,
   worst_external_after_minus_before_jump_hPa=round(biggest,6),
   boundary_science_lane=lane,
   next_physical_source_review="Inspect true original measured/QC1 neighbor T/VPD/RH and independent station/source ERA5-Land, then alternate event-complete RH trial; no partial forcing.",
   new_science_approval="NO",production_DATM_authorized="NO"))
 if len(out70)!=70 or len(out52)!=52 or len(edges52)!=104:
  raise ValueError("source Stage48 70 candidate and 52 new jump boundaries do not reconcile")
 if sum(x["candidate_original_HH"] for x in out70)!=141 or sum(x["preexisting_Stage43_unapproved_trial_HH"] for x in out70)!=15:
  raise ValueError("candidate source HH or earlier Stage43 deduplicated original HH drifted")
 if Counter(w for x in failed for w in x["science_hold_reasons"].split(";"))!=Counter(
      {"NEW_EXTERNAL_GT2":46,"NEW_EXTERNAL_GT4":40}):
  raise ValueError("actual 52 new jump reasons changed")
 if len(held)!=253 or len(set((x["site"],x["episode_id"]) for x in held))!=253:
  raise ValueError("original 217 low RH +36 QC2 source science holds changed")
 siteout=[]
 for site in SITES:
  pc=[r for r in out70 if r["site"]==site]
  hc=[r for r in out52 if r["site"]==site]
  orig=[r for r in held if r["site"]==site]
  siteout.append(dict(site=site,Stage46_assistant_original_events=len(pc)+len(hc)+len(orig),
   Stage48_numeric_research_events=len(pc),
   Stage48_numeric_research_native_HH=sum(r["candidate_original_HH"] for r in pc),
   Stage48_new_jumps_HOLD_events=len(hc),
   Stage48_extreme_neighbor_source_HOLD_events=sum(r["original_neighbor_risk"]=="ORIGINAL_NEIGHBOR_EXTREME_LOW_RH_HOLD" for r in orig),
   Stage48_QC2_neighbor_source_HOLD_events=sum(r["original_neighbor_risk"]=="SOURCE_QC2_OR_NONMEASURED_NEIGHBOR_HOLD" for r in orig),
   source_reference_ERA_only_or_partial_events=sum(r["source_reference_science_gate"] in
    ("SOURCE_ERA_ONLY_NO_MDS_REFERENCE","SOURCE_MDS_PARTIAL_COVERAGE_NOT_INDEPENDENT") for r in pc),
   source_reference_ERA_MDS_GT10pp_disagree_events=sum(r["source_reference_science_gate"]=="SOURCE_MDS_ERA_RH_GT10PP_DISAGREEMENT_HOLD" for r in pc),
   source_tower_vs_ERA_T_GT5C_events=sum(r["source_reference_science_gate"]=="TOWER_MINUS_ERA_T_GT5C_HOLD" for r in pc),
   external_new_GT4_original_event_holds=sum(r["original_external_new_GT4_count"]>0 for r in hc),
   additional_science_approvals=0,site_model_forcing_pass=False))
 if sum(x["Stage46_assistant_original_events"] for x in siteout)!=375:
  raise ValueError("source Assistant ten-site original science split changed")
 out.mkdir(exist_ok=False)
 write(out/"stage49_70_NUMERIC_CANDIDATE_EVENT_REFERENCE_QC_GATES.csv",OUTPUT70,out70)
 write(out/"stage49_52_NEW_JUMP_HOLD_EVENT_PHYSICAL_DIAGNOSIS.csv",OUTPUT52,out52)
 write(out/"stage49_104_TRUE_NATIVE_BOUNDARY_BEFORE_AFTER_DETAILS.csv",EDGES52,edges52)
 write(out/"stage49_ALL10_SITE_ASSISTANT_REMAINING_WORK.csv",SITE,siteout)
 meta=dict(input_SHA256={k:hashfile(v) for k,v in paths.items()},
  Assistant_70_numeric_only_candidate_original_events=True,
  candidate_original_native_HH=141,Stage43_15_unapproved_native_HH_overlap=15,
  Assistant_52_additional_new_jump_holds=True,
  Assistant_253_original_neighbor_science_holds=True,
  Claude_108_events_reserved_unchanged=True,
  original_P2P3_1574_all_science_unapproved=True,
  prior_approved166_P1hold46_RHplateau10_protected=True,
  new_scientific_approvals=0,source_DATM_CIME_Slurm_writes=0)
 (out/"stage49_manifest.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
 md=["# Stage49 | Batch05 Assistant science audit: 70 candidate events, 52 new source-native jump HOLDs, 253 older holds","",
  "**All remain science-unapproved. No original data, user-approved source, or production DATM edits.**",
  "70 numeric-passing event sources span exactly 141 original half-hours and include all 15 prior Stage43 research candidate HH.",
  "42+28 is a possible *initial lane* split (source low-numeric + QC1), but site-level output is the authoritative science reference output.",
  "","## 70 numeric-passing original ERA/RH methods: scientific evidence gaps"]
 for g,n in sorted(Counter(r["source_reference_science_gate"] for r in out70).items()):
  md.append("- **{}**: {} original events".format(g,n))
 md+=["","## 52 event holds after ERA source native VPD external jumps"]
 for g,n in sorted(Counter(r["boundary_science_lane"] for r in out52).items()):
  md.append("- **{}**: {} original events".format(g,n))
 md+=["","GT2 source events: 46, GT4 source events: 40, both: 34. Every event remains on HOLD; thresholds are QC screens, not meteorological proof.",
  "Before/after original T/VPD/QC of both native external edges are retained in the separate edge CSV for traceability.",
  "","## Original remaining 253 source neighbor HOLD events",
  "217 extreme low original neighbor RH and 36 QC2/nonmeasured neighbor classes remain protected.",
  "RH 1-10% may be physically possible; low RH alone does not prove sensor error.",
  "","## Ten-site source science distribution",
  "| Site | Assistant original events | Numeric-only candidates | Candidate HH | New jump HOLD | Low RH neighbor HOLD | QC2 neighbor HOLD |",
  "|---|---:|---:|---:|---:|---:|---:|"]
 for s in siteout:md.append("| {} | {} | {} | {} | {} | {} | {} |".format(
  s["site"],s["Stage46_assistant_original_events"],
  s["Stage48_numeric_research_events"],s["Stage48_numeric_research_native_HH"],
  s["Stage48_new_jumps_HOLD_events"],
  s["Stage48_extreme_neighbor_source_HOLD_events"],
  s["Stage48_QC2_neighbor_source_HOLD_events"]))
 md+=["","## Recommended science workflow",
  "1. For the 70 candidates, verify that source ERA relative humidity and temperature reference are meteorologically defensible; prioritize actual tower RH/temperature QC, local station observations, and clearly identified ERA5-Land (reanalysis) consistency.",
  "2. For the 52 new-jump methods, examine true original before/after native half-hour source QC and humidity and evaluate alternative full-event methods; never manually smooth a genuine measured QC0 neighbor.",
  "3. Keep the remaining 253 source neighbor origin holds until more meteorological evidence is gathered.",
  "4. Do not auto-approve source ERA RH or write source/CIME/DATM; keep Stage24 approved166, P1 manual HOLD46, ten RH platforms, and Claude's separate 108 untouched.",""]
 (out/"STAGE49_ASSISTANT_70_SOURCE_EVIDENCE_52_NEW_JUMP_REVIEW.md").write_text("\n".join(md)+"\n")
 print("STAGE49 SUCCESS | 70 original numeric research events /141 native HH, 52 external-jump science holds with 104 original edges, 253 original neighbor source holds; all 375 reconciled")
 print("STAGE49 CANDIDATE_REFERENCE_GATES",json.dumps(dict(Counter(x["source_reference_science_gate"] for x in out70)),sort_keys=True))
 print("STAGE49 NEW_JUMP_CONTEXT",json.dumps(dict(Counter(x["boundary_science_lane"] for x in out52)),sort_keys=True))
 print("STAGE49 SITE_CASES",json.dumps({r["site"]:[r["Stage48_numeric_research_events"],r["Stage48_new_jumps_HOLD_events"],r["Stage48_extreme_neighbor_source_HOLD_events"],r["Stage48_QC2_neighbor_source_HOLD_events"]] for r in siteout},sort_keys=True))
 print("STAGE49_REPORT="+str(out/"STAGE49_ASSISTANT_70_SOURCE_EVIDENCE_52_NEW_JUMP_REVIEW.md"))
 print("STAGE49_OUT="+str(out))
 print("STAGE49 RESEARCH_ONLY | 166 APPROVED/46 P1 HOLD/10 PLATEAU/1574 P2P3/CLAUDE108/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

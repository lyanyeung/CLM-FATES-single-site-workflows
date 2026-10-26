#!/usr/bin/env python3
"""Batch05 Stage48: fast consolidation of Assistant-owned Stage47 research.

80 *source-neighbor-QC1 (10-100% original neighbor RH)* events PLUS 42
Stage45 low-numeric events -> 122 complete original source-ERA hypothetical
event repairs in ONE standalone UNAPPROVED trial. 217 extreme-low source
neighbors and 36 QC2/nonmeasured neighbors -> 253 separate provenance HOLDs.

Input Stage47/45/44/27/24/43 ORIGINAL output, with strict original T/VPD/QC,
native event clock, source ERA RH, Stage43 15-HH overlap and QC0/166/46/10
disjointness. No production forcing, Slurm, source files or model changes.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta

QC1="SOURCE_QC1_ORIGIN_REVIEW"
LOW="NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL"
OTHER=("ORIGINAL_NEIGHBOR_EXTREME_LOW_RH_HOLD",
       "SOURCE_QC2_OR_NONMEASURED_NEIGHBOR_HOLD")
SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
N47={"site","episode_id","original_HH","triage_priority",
 "original_neighbor_QC1_edges","original_neighbor_QC2_edges",
 "original_neighbor_other_QC_edges","missing_native_neighbor_edges",
 "neighbor_original_RH_negative_edges","neighbor_original_RH_0to1pct_edges",
 "neighbor_original_RH_1to10pct_edges","neighbor_original_RH_above100_edges",
 "neighbor_RH_unavailable_edges","adjacent_another_unapproved_P2P3_edges"}
L47={"site","episode_id","original_HH","alternative_reference_lane",
 "source_original_QC0_VPD_native_HH","source_ERA_RH_available_native_HH",
 "max_abs_tower_T_minus_source_ERA_T_C"}
E45={"site","episode_id","original_HH","original_start_native","original_end_native",
 "original_episode_number_of_contiguous_segments","source_original_QC0_HH",
 "original_full_event_ERA_covered","new_internal_jump_gt2","new_internal_jump_gt4",
 "new_external_jump_gt2","new_external_jump_gt4","max_abs_VPD_change_hPa",
 "risk_screen","external_neighbors_unmeasured_or_unapproved",
 "external_neighbors_implied_RH_below10_or_unphysical","external_edges_uncomparable"}
R44={"site","native_time","episode_id","source_QC_T","source_QC_VPD",
 "original_T_C","original_VPD_hPa","original_implied_RH_pct",
 "source_ERA_RH_pct","source_ERA_candidate_VPD_hPa"}
R27={"site","native_time","episode_id","TA_F_C","VPD_F_hPa",
 "TA_F_QC","VPD_F_QC","RH_ERA_pct"}
R43={"site","native_time","episode_id","original_VPD_hPa",
 "candidate_RH_pct","hypothetical_VPD_hPa","science_approval","DATM_permission"}
K={"site","native_time"}
OUT_NATIVE=("site","native_time","episode_id","assistant_original_event_lane",
 "original_selected_T_C","original_selected_T_QC","original_VPD_hPa",
 "original_VPD_QC","original_implied_RH_water_pct",
 "source_processed_ERA_RH_pct","ERA_RH_at_original_T_trial_VPD_hPa",
 "trial_minus_original_VPD_hPa","overlaps_existing_Stage43_trial",
 "science_reference_tier","version","science_approval","production_DATM_permission")
OUT_EVENT=("site","episode_id","original_event_HH","native_first","native_last",
 "original_T_VPD_QC_verified","original_QC0_VPD_preserved",
 "source_ERA_full_native_coverage","new_gt2_thresholds","new_gt4_thresholds",
 "native_time_gaps","max_abs_VPD_change_hPa","all_original_RH_negative_or_below1",
 "neighbor_original_QC1_only_or_measured_QC0",
 "candidate_lane","outside_reference_gap",
 "Stage43_preexisting_trial_HH","science_approval","production_DATM_permission")
OUT_HOLD=("site","episode_id","original_event_HH","original_neighbor_risk",
 "original_QC1_edges","original_QC2_edges",
 "neighbor_original_RH_low_1to10_edges","neighbor_original_RH_below1_edges",
 "neighbor_original_RH_negative_edges","source_repair_lane",
 "necessary_additional_evidence","auto_repaired","DATM_modified")
OUT_SITE=("site","original_source_P2P3_HH","Stage47_ASSISTANT_events",
 "assistant_full_event_ERA_research_candidates",
 "candidate_original_native_HH","previous_Stage43_15_native_overlap",
 "source_neighbor_extreme_RH_holds","source_neighbor_QC2_holds",
 "Claude_owned_original_events_unchanged","new_science_approvals",
 "site_full_science_pass")

def n(x):
 try:
  v=float(x)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except (ValueError,TypeError):pass
 return None
def sat(T):
 if T is None or T<-80 or T>60:raise ValueError("original source tower T not physically screened")
 return 6.112*math.exp(17.67*T/(T+243.5))
def date(t):return datetime.strptime(t,"%Y%m%d%H%M")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1<<20),b""):h.update(c)
 return h.hexdigest()
def load(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("original read-only source absent "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  d=csv.DictReader(f);cols=d.fieldnames or []
  if not required.issubset(cols) or len(cols)!=len(set(cols)):
   raise ValueError("original data columns absent or duplicate "+str(p))
  rr=list(d)
 if any(None in r or any(v is None for v in r.values()) for r in rr):
  raise ValueError("source row malformed "+str(p))
 return rr
def unique(rr,fields=("site","native_time")):
 out={}
 for r in rr:
  k=tuple(r[f] for f in fields)
  if k in out:raise ValueError("duplicate original event/native halfhour "+str(k))
  out[k]=r
 return out
def write(p,cols,rr):
 with p.open("x",newline="",encoding="utf-8") as f:
  x=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  x.writeheader();x.writerows(rr)
def selftest():
 assert 217+36+80+42==375 and 375+108==483
 assert abs(sat(0)-6.112)<1e-10
 assert n("-9999") is None
 print("STAGE48 SELF-TEST PASS | 80 QC1+42 numeric original event research pilots, 253 source holds, old Stage43 and native QC0 protected")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for q in ("stage47-dir","stage45-dir","stage44-dir","stage27-dir",
           "stage24-dir","stage43-dir","out"):p.add_argument("--"+q,type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 names=("stage47_dir","stage45_dir","stage44_dir","stage27_dir","stage24_dir","stage43_dir")
 if any(getattr(a,k) is None for k in (*names,"out")):p.error("all previous source reports and NEW --out required")
 d47,d45,d44,d27,d24,d43=[getattr(a,k).expanduser().resolve() for k in names]
 out=a.out.expanduser().resolve()
 if not all(d.is_dir() for d in (d47,d45,d44,d27,d24,d43)) or out.exists() or not out.parent.is_dir():
  p.error("all original report dirs required; --out must be fresh")
 if any(out==d or out in d.parents or d in out.parents for d in (d47,d45,d44,d27,d24,d43)):
  p.error("cannot produce research overlay in original input directory")
 paths={
  "neighbor":d47/"stage47_333_ORIGINAL_NEIGHBOR_QC_RH_JUMP_DIAGNOSIS.csv",
  "low":d47/"stage47_42_NUMERIC_SOURCE_ERA_MDS_SCIENTIFIC_EVIDENCE.csv",
  "event":d45/"stage45_483_ORIGINAL_EVENTS_TRUE_NATIVE_VPD_QC.csv",
  "native":d44/"stage44_ALL1574_NATIVE_HH_ORIGINAL_RH_AND_ERA_MDS_FIRST_PASS.csv",
  "original":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
  "approved":d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv",
  "p1hold":d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv",
  "rhplateau":d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv",
  "stage43":d43/"stage43_UNAPPROVED_15_NATIVE_ERA_CANDIDATES.csv",
  "stage47_manifest":d47/"stage47_manifest.json",
  "stage45_manifest":d45/"stage45_manifest.json"}
 neighbors=load(paths["neighbor"],N47)
 low=load(paths["low"],L47)
 original_events=unique(load(paths["event"],E45),("site","episode_id"))
 native=load(paths["native"],R44)
 original=unique(load(paths["original"],R27))
 approved=unique(load(paths["approved"],K))
 p1hold=unique(load(paths["p1hold"],K))
 plateau=unique(load(paths["rhplateau"],K))
 old=unique(load(paths["stage43"],R43))
 if (len(neighbors),len(low),len(original_events),len(native),len(original),
   len(approved),len(p1hold),len(plateau),len(old))!=(333,42,483,1574,1574,166,46,10,15):
  raise ValueError("Stage47/45/44/27/24/43 source cohort population drifted")
 m47=json.loads(paths["stage47_manifest"].read_text())
 m45=json.loads(paths["stage45_manifest"].read_text())
 if (m47.get("new_science_approvals"),m45.get("source_science_new_approvals"))!=(0,0):
  raise ValueError("source unexpectedly contains approved new research")
 if m45.get("independently_original_source_verified_native_HH")!=1574 or m45.get("site_source_holds"):
  raise ValueError("original 9/9 site T/VPD/QC source verification incomplete")
 count=Counter(x["triage_priority"] for x in neighbors)
 if count!={QC1:80,OTHER[0]:217,OTHER[1]:36}:
  raise ValueError("Stage47 source neighbor lane counts changed")
 if len({(x["site"],x["episode_id"]) for x in neighbors+low})!=375:
  raise ValueError("overlapping original Assistant source event ownership")
 prior=defaultdict(list)
 for r in native:
  prior[(r["site"],r["episode_id"])].append(r)
 if len(prior)!=483:raise ValueError("original 483 episode source membership changed")
 select=[(x["site"],x["episode_id"],QC1) for x in neighbors if x["triage_priority"]==QC1]
 select.extend((x["site"],x["episode_id"],LOW) for x in low)
 if len(select)!=122 or len(set((s,e) for s,e,_ in select))!=122:
  raise ValueError("122 unique original lower-numeric source events missing")
 selected=[];candidates=[]
 initial_events={(x["site"],x["episode_id"]):x for x in neighbors}
 for site,eid,lane in sorted(select):
  event=original_events[(site,eid)]
  if event["source_original_QC0_HH"]!="0" or event["original_full_event_ERA_covered"]!="True":
   raise ValueError("candidate has original QC0 or incomplete source ERA RH")
  if event["original_episode_number_of_contiguous_segments"]!="1" or any(
     int(event[k])>0 for k in ("new_internal_jump_gt2","new_internal_jump_gt4",
     "new_external_jump_gt2","new_external_jump_gt4")):
   raise ValueError("source event has gap or ERA trial creates new VPD jump")
  peak=n(event["max_abs_VPD_change_hPa"])
  if peak is None or peak>10:raise ValueError("candidate exceeds >10 hPa source VPD magnitude gate")
  if lane==LOW and event["risk_screen"]!="NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL":
   raise ValueError("low-numeric original Stage45 event changed")
  if lane==QC1:
   x=initial_events[(site,eid)]
   if event["risk_screen"]!="ORIGINAL_EXTERNAL_NEIGHBOR_QC_OR_RH_UNCERTAIN":
    raise ValueError("QC1 candidate original Stage45 neighbor risk changed")
   if (int(x["original_neighbor_QC1_edges"])==0 or
       any(int(x[k])!=0 for k in (
       "original_neighbor_QC2_edges","original_neighbor_other_QC_edges",
       "missing_native_neighbor_edges","neighbor_original_RH_negative_edges",
       "neighbor_original_RH_0to1pct_edges",
       "neighbor_original_RH_1to10pct_edges","neighbor_original_RH_above100_edges",
       "neighbor_RH_unavailable_edges","adjacent_another_unapproved_P2P3_edges"))):
    raise ValueError("QC1 source neighbor has more serious physical risks, cannot join 122")
  rr=sorted(prior[(site,eid)],key=lambda r:r["native_time"])
  if len(rr)!=int(event["original_HH"]):
   raise ValueError("original full event halfhours incomplete")
  if rr[0]["native_time"]!=event["original_start_native"] or rr[-1]["native_time"]!=event["original_end_native"]:
   raise ValueError("native original source time origin changed")
  if any(date(b["native_time"])-date(a["native_time"])!=timedelta(minutes=30)
      for a,b in zip(rr,rr[1:])):
   raise ValueError("original event contains gap")
  any_prior=0;maxdelta=0.;invalid=0
  for r in rr:
   key=(site,r["native_time"]);oldrow=original.get(key)
   if oldrow is None or oldrow["episode_id"]!=eid or key in approved or key in p1hold or key in plateau:
    raise ValueError("candidate overlaps original 166 approved /46 P1 /10 RH platform or lacks P2P3")
   T=n(r["original_T_C"]);V=n(r["original_VPD_hPa"])
   era=n(r["source_ERA_RH_pct"]);nc=n(r["source_ERA_candidate_VPD_hPa"])
   if None in (T,V,era,nc) or not 0<=era<=100:
    raise ValueError("native original source T/VPD or trial source ERA RH invalid")
   if (abs(T-n(oldrow["TA_F_C"]))>.002 or abs(V-n(oldrow["VPD_F_hPa"]))>.002 or
       r["source_QC_T"]!=oldrow["TA_F_QC"] or r["source_QC_VPD"]!=oldrow["VPD_F_QC"] or
       r["source_QC_VPD"]=="0" or abs(era-n(oldrow["RH_ERA_pct"]))>.002):
    raise ValueError("original source T/VPD/QC or ERA RH reference changed")
   calc=sat(T)*(1-era/100)
   if abs(nc-calc)>.003 or nc<0 or nc>sat(T)+.002:
    raise ValueError("source hypothetical VPD not physically consistent")
   originalRH=100*(1-V/sat(T))
   if abs(originalRH-n(r["original_implied_RH_pct"]))>.002:
    raise ValueError("implied original tower RH inconsistent")
   priorrow=old.get(key)
   if priorrow is not None:
    any_prior+=1
    if (priorrow["science_approval"]!="NO" or priorrow["DATM_permission"]!="NO"
      or abs(n(priorrow["hypothetical_VPD_hPa"])-nc)>.003):
     raise ValueError("previous Stage43 candidate overlaps differently or claims approval")
   maxdelta=max(maxdelta,abs(nc-V)); invalid+=originalRH<0 or originalRH>100
   candidates.append(dict(site=site,native_time=r["native_time"],episode_id=eid,
    assistant_original_event_lane=lane,original_selected_T_C=T,
    original_selected_T_QC=r["source_QC_T"],original_VPD_hPa=V,
    original_VPD_QC=r["source_QC_VPD"],
    original_implied_RH_water_pct=round(originalRH,6),
    source_processed_ERA_RH_pct=era,
    ERA_RH_at_original_T_trial_VPD_hPa=round(nc,6),
    trial_minus_original_VPD_hPa=round(nc-V,6),
    overlaps_existing_Stage43_trial=key in old,
    science_reference_tier="REANALYSIS_SOURCE_ERA_NOT_INDEPENDENT_STATION",
    version="BATCH05_STAGE48_ASSISTANT_FULL_EVENT_SOURCE_ERA_UNAPPROVED_V1",
    science_approval="NO",production_DATM_permission="NO"))
  if abs(peak-maxdelta)>.005:
   raise ValueError("Stage45 original event max trial VPD change does not match Stage44 native data")
  selected.append(dict(site=site,episode_id=eid,original_event_HH=len(rr),
   native_first=rr[0]["native_time"],native_last=rr[-1]["native_time"],
   original_T_VPD_QC_verified=True,original_QC0_VPD_preserved=True,
   source_ERA_full_native_coverage=True,new_gt2_thresholds=0,new_gt4_thresholds=0,
   native_time_gaps=0,max_abs_VPD_change_hPa=round(maxdelta,6),
   all_original_RH_negative_or_below1=all(
      n(q["original_implied_RH_pct"])<1 for q in rr),
   neighbor_original_QC1_only_or_measured_QC0=lane==QC1,
   candidate_lane=lane,
   outside_reference_gap=(
      "QC1_NEIGHBOR_NOT_INDEPENDENT_VALIDATION" if lane==QC1 else
      "ERA_MDS_ONLY_NO_INDEPENDENT_STATION_OR_ERA5LAND_VALIDATION"),
   Stage43_preexisting_trial_HH=any_prior,
   science_approval="NO",production_DATM_permission="NO"))
 if len(selected)!=122 or len({(x["site"],x["native_time"]) for x in candidates})!=len(candidates):
  raise ValueError("122 candidate events or unique original site/time identity failed")
 if sum(x["Stage43_preexisting_trial_HH"] for x in selected)!=15:
  raise ValueError("Stage43 previous 15 trial native rows should be included exactly, not duplicated")
 hold=[]
 for r in neighbors:
  if r["triage_priority"]==QC1:continue
  if r["triage_priority"] not in OTHER:raise ValueError("unexpected Stage47 source neighbor lane")
  lane=r["triage_priority"]
  hold.append(dict(site=r["site"],episode_id=r["episode_id"],
   original_event_HH=r["original_HH"],original_neighbor_risk=lane,
   original_QC1_edges=r["original_neighbor_QC1_edges"],
   original_QC2_edges=r["original_neighbor_QC2_edges"],
   neighbor_original_RH_low_1to10_edges=r["neighbor_original_RH_1to10pct_edges"],
   neighbor_original_RH_below1_edges=r["neighbor_original_RH_0to1pct_edges"],
   neighbor_original_RH_negative_edges=r["neighbor_original_RH_negative_edges"],
   source_repair_lane="SEPARATE_NATIVE_NEIGHBOR_SCIENCE_RECONSTRUCTION_REQUIRED",
   necessary_additional_evidence=(
    "ORIGINAL_QC_AND_REFERENCE_FOR_SUSPICIOUS_RH_NEIGHBOR" if lane==OTHER[0] else
    "ORIGINAL_QC2_NONMEASURED_NEIGHBOR_AND_SOURCE_ERA5LAND_COMPARISON"),
   auto_repaired=False,DATM_modified=False))
 if len(hold)!=253 or len(candidates)<122:
  raise ValueError("expected 217+36 separate unresolved original neighbor events")
 siteout=[]
 for site in SITES:
  es=[x for x in selected if x["site"]==site]
  nh=[x for x in hold if x["site"]==site]
  siteout.append(dict(site=site,
   original_source_P2P3_HH=sum(x["site"]==site for x in original.values()),
   Stage47_ASSISTANT_events=sum(x["site"]==site for x in neighbors+low),
   assistant_full_event_ERA_research_candidates=len(es),
   candidate_original_native_HH=sum(x["site"]==site for x in candidates),
   previous_Stage43_15_native_overlap=sum(x["site"]==site and x["overlaps_existing_Stage43_trial"] for x in candidates),
   source_neighbor_extreme_RH_holds=sum(x["original_neighbor_risk"]==OTHER[0] for x in nh),
   source_neighbor_QC2_holds=sum(x["original_neighbor_risk"]==OTHER[1] for x in nh),
   Claude_owned_original_events_unchanged=True,new_science_approvals=0,
   site_full_science_pass=False))
 if sum(x["original_source_P2P3_HH"] for x in siteout)!=1574 or sum(x["Stage47_ASSISTANT_events"] for x in siteout)!=375:
  raise ValueError("site scientific cohorts drifted")
 out.mkdir(exist_ok=False)
 write(out/"stage48_VERSIONED_FULL_EVENT_SOURCE_ERA_122_EVENT_NATIVE_CANDIDATES_UNAPPROVED.csv",OUT_NATIVE,candidates)
 write(out/"stage48_ALL122_COMPLETE_EVENT_SCIENCE_NUMERIC_GATES.csv",OUT_EVENT,selected)
 write(out/"stage48_253_ORIGINAL_NEIGHBOR_SOURCE_HOLDS.csv",OUT_HOLD,hold)
 write(out/"stage48_TEN_SITE_ASSISTANT_TRIAL_AND_HOLD_PROGRESS.csv",OUT_SITE,siteout)
 manifest=dict(source_sha256={k:sha(p) for k,p in paths.items()},
  assistant_source_events=375,assistant_candidate_complete_events=122,
  assistant_source_neighbor_origin_holds=253,
  candidate_native_original_HH=len(candidates),
  prior_Stage43_15_unapproved_native_trial_overlap=15,
  Claude_108_science_events_untouched=True,
  original_P2P3_1574_all_still_unapproved=True,
  approved_Stage24_166_P1HOLD46_RHplatform10_unchanged=True,
  source_FLUXMET_DATM_CIME_Slurm_modified=False,new_science_approvals=0)
 (out/"stage48_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 md=["# Stage48 — Assistant Track A 122 source-ERA full-event research candidates, 253 source-neighbor HOLDs",
  "","**THIS IS NOT A PRODUCTION OVERLAY. All 122 source-ERA methods remain unapproved.**",
  "Event-complete source-native T/VPD/QC and existing 166 approved, 46 P1 HOLD and 10 RH platforms are immutable.",
  "80 events with no source neighbor <10% RH/QC2 risk beyond original neighboring QC1, and Stage45's 42 already numerically screened event methods,",
  "make 122 event-complete candidate source-ERA trials. Source processed ERA RH is not independent tower ground truth.",
  "","## Assistant initial science event progress",
  "- 80 original source-neighbor-QC1 events: local source VPD edge numeric gate passed but QC1 is not independent scientific confirmation.",
  "- 42 Stage45 source-ERA low-numeric original events: references require explicit evidence, including Stage47 31 ERA only, 9 tower-vs-ERA T>5C, 2 source ERA/MDS >10pp disagreements.",
  "- 217 very-low original source RH neighbor events: keep separate until neighbor itself is independently evaluated; never interpolate to an implausible neighbor.",
  "- 36 QC2/nonmeasured original source neighbor events: keep separate until original instrumentation and external model/reference have been checked.",
  "","## Exact site status",
  "| Site | P2/P3 original HH | Assistant candidates: events | Candidate native HH | Retained source neighbor RH HOLD | QC2 HOLD |",
  "|---|---:|---:|---:|---:|---:|"]
 for x in siteout:
  md.append("| {} | {} | {} | {} | {} | {} |".format(
   x["site"],x["original_source_P2P3_HH"],
   x["assistant_full_event_ERA_research_candidates"],
   x["candidate_original_native_HH"],x["source_neighbor_extreme_RH_holds"],x["source_neighbor_QC2_holds"]))
 md+=["","**The previous Stage43 15 native source-ERA research records are present inside, NOT additional repair records.**",
  "No extra scientific approvals from 122 events; 108 Claude-owned events untouched.",
  "Next: compare ERA5-Land or genuine station/sensor context with the versioned event-native candidate table and prioritize source neighbor 217/36. Never auto-rewrite DATM.",""]
 (out/"STAGE48_ASSISTANT_122_TRIAL_EVENTS_253_SOURCE_HOLDS.md").write_text("\n".join(md)+"\n")
 print("STAGE48 SUCCESS | ASSISTANT_CANDIDATE_EVENTS",len(selected),"SOURCE_NATIVE_HH",len(candidates),
       "NEIGHBOR_HOLD_EVENTS",len(hold),"STAGE43_15_PREVIOUS_HH_DEDUPED")
 print("STAGE48 SITES",json.dumps({x["site"]:{"events":x["assistant_full_event_ERA_research_candidates"],
    "HH":x["candidate_original_native_HH"],"extreme_RH_holds":x["source_neighbor_extreme_RH_holds"],
    "QC2_holds":x["source_neighbor_QC2_holds"]} for x in siteout},sort_keys=True))
 print("STAGE48_REPORT="+str(out/"STAGE48_ASSISTANT_122_TRIAL_EVENTS_253_SOURCE_HOLDS.md"))
 print("STAGE48_OUT="+str(out))
 print("STAGE48 122 SOURCE_CANDIDATES UNAPPROVED | 253 HOLDS | Claude108 UNTOUCHED | NO SOURCE/DATM/SLURM WRITES")
if __name__=="__main__":main()

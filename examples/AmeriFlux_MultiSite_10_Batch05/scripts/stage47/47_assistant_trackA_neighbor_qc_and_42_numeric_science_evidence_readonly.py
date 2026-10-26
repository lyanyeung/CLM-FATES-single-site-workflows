#!/usr/bin/env python3
"""Batch05 Stage47 - Assistant-owned Track A, original science EVIDENCE ONLY.

For all 333 original events whose +/-30 minute source-neighbor QC/RH was
uncertain, classify independently: original physical RH, VPD source QC,
source event adjacency, measured QC0 vs QC1 vs QC2, and before-vs-trial
boundary jumps. Do not smooth a repair toward a physically bad neighbor.

For all 42 lower-numeric-risk source-ERA events, audit exact original native
HH, source ERA/MDS alternative reference agreement and gaps, temperature
coherence and candidate >5hPa changes. These remain UNAPPROVED even if
the local VPD continuity numerical screen passed.

ONLY read original Stage46/45/44/27 reports. New output reports/CSVs; NO
source changes, no forced approval, no Slurm/DATM/model writes.
"""
import argparse,csv,json,hashlib,math
from pathlib import Path
from collections import Counter,defaultdict

OWNER_NEIGH="ASSISTANT_NEIGHBOR_PROVENANCE"
OWNER_LOW="ASSISTANT_NUMERIC_PILOT"
SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
       "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
R46={"owner_lane","site","episode_id","original_native_start","original_native_end",
 "original_HH","Stage45_priority_gate","max_abs_VPD_change_hPa",
 "untrusted_original_neighbor_count","extreme_original_neighbor_RH_count"}
R45={"site","context_kind","context_id","side","neighbor_time","neighbor_kind",
 "neighbor_original_QC_VPD","neighbor_implied_RH_water_pct","before_jump_hPa",
 "after_jump_hPa","new_gt2","new_gt4","neighbor_untrusted","comparable"}
R44={"site","native_time","episode_id","source_QC_T","source_QC_VPD",
 "original_T_C","original_VPD_hPa","original_implied_RH_pct",
 "source_ERA_RH_pct","source_MDS_RH_pct","source_ERA_candidate_VPD_hPa",
 "source_ERA_humidity_valid","source_MDS_humidity_valid"}
R27={"site","native_time","episode_id","RH_ERA_e_pct",
 "abs_selected_T_minus_ERA_T_C","RH_ERA_pct","RH_MDS_pct"}
R45EVENT={"site","episode_id","original_HH","risk_screen",
 "original_episode_number_of_contiguous_segments",
 "source_original_QC0_HH","original_full_event_ERA_covered",
 "new_internal_jump_gt2","new_external_jump_gt2",
 "new_internal_jump_gt4","new_external_jump_gt4"}
NEIGH_COLUMNS=("site","episode_id","start_native","end_native","original_HH",
 "native_edge_count","adjacent_another_unapproved_P2P3_edges",
 "approved_Stage24_neighbor_edges","missing_native_neighbor_edges",
 "original_neighbor_QC0_edges","original_neighbor_QC1_edges",
 "original_neighbor_QC2_edges","original_neighbor_other_QC_edges",
 "neighbor_original_RH_negative_edges","neighbor_original_RH_0to1pct_edges",
 "neighbor_original_RH_1to10pct_edges","neighbor_original_RH_above100_edges",
 "neighbor_RH_unavailable_edges","original_neighbor_old_jump_gt2_edges",
 "candidate_neighbor_trial_jump_gt2_edges",
 "old_to_trial_jump_improved_at_least0p5_edges",
 "old_to_trial_jump_worsened_over0p5_edges",
 "numeric_trial_max_delta_VPD_hPa",
 "triage_priority","science_decision_recommended",
 "source_safety_verified","production_DATM_authorized")
LOW_COLUMNS=("site","episode_id","start_native","end_native","original_HH",
 "original_source_RH_negative_native_HH",
 "original_source_RH_sub1pct_native_HH",
 "source_original_QC0_VPD_native_HH",
 "source_ERA_RH_available_native_HH","source_MDS_RH_available_native_HH",
 "ERA_MDS_both_available_native_HH","ERA_MDS_agreement_at_most5pp_HH",
 "ERA_MDS_disagreement_over10pp_HH",
 "max_abs_ERA_minus_MDS_RH_pp",
 "max_abs_tower_T_minus_source_ERA_T_C",
 "max_abs_original_vs_ERA_candidate_VPD_hPa",
 "source_before_trial_edge_untrusted","alternative_reference_lane",
 "required_independent_evidence","scientific_status",
 "production_DATM_authorized")
SITE_COLUMNS=("site","original_Stage46_assistant_neighbor_events",
 "original_Stage46_assistant_low_numeric_events","neighbor_nonphysical_RH_events",
 "neighbor_low_extreme_RH_events","neighbor_unmeasured_QC_events",
 "neighbor_other_original_P2P3_events","low_numeric_events_WITH_MDS_comparable",
 "low_numeric_events_ERA_only","new_science_approvals",
 "full_forcing_site_pass")
EDGE_COLUMNS=("site","episode_id","boundary_side","neighbor_native_time",
 "original_neighbor_QC","neighbor_kind","original_neighbor_RH_water_pct",
 "neighbor_RH_category","original_jump_hPa","trial_jump_hPa",
 "jump_delta_hPa","science_priority")
def num(s):
 try:
  v=float(s)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except (ValueError,TypeError):pass
 return None
def checksum(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()
def read(p,cols):
 if not p.is_file() or p.is_symlink():raise ValueError("missing original scientific report "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  reader=csv.DictReader(f);headers=reader.fieldnames or []
  if not cols.issubset(headers) or len(headers)!=len(set(headers)):
   raise ValueError("missing or duplicate original columns: "+str(p))
  out=list(reader)
 if any(None in x or any(v is None for v in x.values()) for x in out):
  raise ValueError("original report contains malformed CSV row "+str(p))
 return out
def unique(rows,keyfields):
 out={}
 for r in rows:
  k=tuple(r[x] for x in keyfields)
  if k in out:raise ValueError("duplicate original native scientific key "+str(k))
  out[k]=r
 return out
def write(p,cols,rows):
 with p.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def category(rh):
 if rh is None:return "RH_MISSING"
 if rh<0:return "RH_NEGATIVE_PHYSICAL_INCONSISTENCY"
 if rh<1:return "RH_BELOW1_PERCENT"
 if rh<10:return "RH_1TO10_PERCENT"
 if rh>100:return "RH_ABOVE100_PHYSICAL_INCONSISTENCY"
 return "RH_WITHIN_PHYSICAL_RANGE"
def neigh_lane(counts):
 if counts["negative"] or counts["above100"]:return "NONPHYSICAL_ADJACENT_ORIGINAL_RH_HOLD"
 if counts["missing"]:return "ORIGINAL_NATIVE_NEIGHBOR_MISSING_HOLD"
 if counts["otherP2"]:return "OTHER_UNAPPROVED_P2P3_NEIGHBOR_HOLD"
 if counts["low1"] or counts["low10"]:return "ORIGINAL_NEIGHBOR_EXTREME_LOW_RH_HOLD"
 if counts["QC2"] or counts["otherQC"]:return "SOURCE_QC2_OR_NONMEASURED_NEIGHBOR_HOLD"
 if counts["QC1"]:return "SOURCE_QC1_ORIGIN_REVIEW"
 return "UNCLASSIFIED_ADJACENT_SOURCE_RISK_REVIEW"
def selftest():
 assert category(-1).startswith("RH_NEGATIVE")
 assert category(.5)=="RH_BELOW1_PERCENT"
 assert category(100.01).startswith("RH_ABOVE100")
 assert neigh_lane(Counter(negative=1))=="NONPHYSICAL_ADJACENT_ORIGINAL_RH_HOLD"
 print("STAGE47 SELF-TEST PASS | 333 native-neighbor events plus 42 numeric provenance cases, source-QC0/P2P3 holds, no writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for f in ("stage46-dir","stage45-dir","stage44-dir","stage27-dir","out"):
  p.add_argument("--"+f,type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,k) is None for k in ("stage46_dir","stage45_dir","stage44_dir","stage27_dir","out")):
  p.error("must supply original source Stage46/45/44/27 dirs and NEW --out")
 d46,d45,d44,d27=[getattr(a,k).expanduser().resolve() for k in
  ("stage46_dir","stage45_dir","stage44_dir","stage27_dir")]
 out=a.out.expanduser().resolve()
 if out.exists() or not out.parent.is_dir() or any(not d.is_dir() for d in (d46,d45,d44,d27)):
  p.error("all input dirs required, --out must be NEW")
 if any(out==d or out in d.parents or d in out.parents for d in (d46,d45,d44,d27)):
  p.error("science input and output path overlap")
 paths={
  "owned":d46/"stage46_ASSISTANT_333_NEIGHBOR_QC_AND_42_NUMERIC_EVENTS.csv",
  "other":d46/"stage46_CLAUDE_108_GT10_AND_NEW_JUMP_EVENT_CASES.csv",
  "edge":d45/"stage45_TRUE_ORIGINAL_EVENT_AND_JOINED_RUN_EXTERNAL_EDGES.csv",
  "event":d45/"stage45_483_ORIGINAL_EVENTS_TRUE_NATIVE_VPD_QC.csv",
  "native":d44/"stage44_ALL1574_NATIVE_HH_ORIGINAL_RH_AND_ERA_MDS_FIRST_PASS.csv",
  "source":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
  "manifest46":d46/"stage46_manifest.json",
  "manifest45":d45/"stage45_manifest.json"}
 owned=read(paths["owned"],R46)
 other=read(paths["other"],R46)
 edges=read(paths["edge"],R45)
 events=unique(read(paths["event"],R45EVENT),("site","episode_id"))
 native=read(paths["native"],R44)
 source=unique(read(paths["source"],R27),("site","native_time"))
 man46=json.loads(paths["manifest46"].read_text(encoding="utf-8"))
 man45=json.loads(paths["manifest45"].read_text(encoding="utf-8"))
 if (len(owned),len(other),len(events),len(native),len(source))!=(375,108,483,1574,1574):
  raise ValueError("actual Stage46/45/44/27 source populations not identical to operator results")
 if man46.get("new_scientific_approvals")!=0 or man45.get("source_science_new_approvals")!=0:
  raise ValueError("unexpected real science approval in original Stage46/45")
 if man45.get("independently_original_source_verified_native_HH")!=1574:
  raise ValueError("original source T/VPD/QC not wholly verified")
 if (Counter(r["owner_lane"] for r in owned)!=Counter({
       OWNER_NEIGH:333, OWNER_LOW:42})):
  raise ValueError("Assistant track not exactly 333 neighbor and 42 low-numeric events")
 eidx={}
 for r in edges:
  if r["context_kind"]!="ORIGINAL_STAGE27_EVENT":continue
  key=(r["site"],r["context_id"])
  eidx.setdefault(key,[]).append(r)
 hidx=defaultdict(list)
 for r in native:
  k=(r["site"],r["episode_id"])
  if k not in events:raise ValueError("Stage44 native source references unknown original Stage45 episode")
  hidx[k].append(r)
 if len(hidx)!=483:raise ValueError("Stage44 original 483 event source membership lost")
 neighborout=[]; lowout=[]; edgeout=[]
 for r in sorted(owned,key=lambda x:(x["site"],x["original_native_start"])):
  key=(r["site"],r["episode_id"])
  e=events.get(key)
  if e is None or e["risk_screen"]!=r["Stage45_priority_gate"]:
   raise ValueError("owned original source episode not identical to Stage45")
  hh=hidx[key]; ee=eidx.get(key,[])
  if len(hh)!=int(r["original_HH"]) or len(ee)<2:
   raise ValueError("original native episode lacks source timestamps or original external edges")
  if e["original_episode_number_of_contiguous_segments"]!="1":
   raise ValueError("assistant lane source event not one contiguous actual native interval")
  if any(s["native_time"] not in source for s in []):
   raise ValueError("unreachable")
  if r["owner_lane"]==OWNER_NEIGH:
   ct=Counter()
   oldj=[];newj=[]
   for ed in ee:
    c=ed["neighbor_original_QC_VPD"];nk=ed["neighbor_kind"]
    rh=num(ed["neighbor_implied_RH_water_pct"])
    cat=category(rh)
    ct["QC0"]+=c=="0";ct["QC1"]+=c=="1"
    ct["QC2"]+=c=="2";ct["otherQC"]+=c not in ("0","1","2")
    ct["missing"]+=not (ed["comparable"]=="True")
    ct["otherP2"]+=nk=="UNAPPROVED_P2P3"
    ct["approved"]+=nk=="STAGE24_APPROVED"
    ct["negative"]+=rh is not None and rh<0
    ct["low1"]+=rh is not None and 0<=rh<1
    ct["low10"]+=rh is not None and 1<=rh<10
    ct["above100"]+=rh is not None and rh>100
    ct["unavailableRH"]+=rh is None
    o=num(ed["before_jump_hPa"]);t=num(ed["after_jump_hPa"])
    if o is not None and t is not None:
     ct["old_gt2"]+=o>2;ct["trial_gt2"]+=t>2
     ct["improved"]+=o-t>=.5
     ct["worsened"]+=t-o>.5
     oldj.append(o);newj.append(t)
    edgeout.append(dict(site=key[0],episode_id=key[1],
     boundary_side=ed["side"],neighbor_native_time=ed["neighbor_time"],
     original_neighbor_QC=c,neighbor_kind=nk,
     original_neighbor_RH_water_pct=rh if rh is not None else "",
     neighbor_RH_category=cat,
     original_jump_hPa=o if o is not None else "",
     trial_jump_hPa=t if t is not None else "",
     jump_delta_hPa=round(t-o,6) if o is not None and t is not None else "",
     science_priority="CHECK_ORIGINAL_NEIGHBOR_NOT_SMOOTH_TOWARD_BAD_RH"))
   lane=neigh_lane(ct)
   neighborout.append(dict(site=key[0],episode_id=key[1],
    start_native=r["original_native_start"],end_native=r["original_native_end"],
    original_HH=r["original_HH"],native_edge_count=len(ee),
    adjacent_another_unapproved_P2P3_edges=ct["otherP2"],
    approved_Stage24_neighbor_edges=ct["approved"],
    missing_native_neighbor_edges=ct["missing"],
    original_neighbor_QC0_edges=ct["QC0"],
    original_neighbor_QC1_edges=ct["QC1"],
    original_neighbor_QC2_edges=ct["QC2"],
    original_neighbor_other_QC_edges=ct["otherQC"],
    neighbor_original_RH_negative_edges=ct["negative"],
    neighbor_original_RH_0to1pct_edges=ct["low1"],
    neighbor_original_RH_1to10pct_edges=ct["low10"],
    neighbor_original_RH_above100_edges=ct["above100"],
    neighbor_RH_unavailable_edges=ct["unavailableRH"],
    original_neighbor_old_jump_gt2_edges=ct["old_gt2"],
    candidate_neighbor_trial_jump_gt2_edges=ct["trial_gt2"],
    old_to_trial_jump_improved_at_least0p5_edges=ct["improved"],
    old_to_trial_jump_worsened_over0p5_edges=ct["worsened"],
    numeric_trial_max_delta_VPD_hPa=r["max_abs_VPD_change_hPa"],
    triage_priority=lane,
    science_decision_recommended="VERIFY_ACTUAL_NATIVE_NEIGHBOR_WITH_OBS_QC_AND_INDEPENDENT_REFERENCE",
    source_safety_verified=False,production_DATM_authorized=False))
  elif r["owner_lane"]==OWNER_LOW:
   orig_neg=orig_sub1=era_available=mds_available=both=agree5=disagree10=qc0=0
   largest_diff=0.;max_delta=0.;max_Tdiff=0.
   for h in hh:
    o=source.get((h["site"],h["native_time"]))
    if o is None or o["episode_id"]!=key[1]:
     raise ValueError("original Stage27 source-native timestamp mismatch")
    rh=num(h["original_implied_RH_pct"])
    era=num(h["source_ERA_RH_pct"]);mds=num(h["source_MDS_RH_pct"])
    diff=num(h["source_ERA_change_VPD_hPa"]) if "source_ERA_change_VPD_hPa" in h else None
    td=num(o["abs_selected_T_minus_ERA_T_C"])
    qc0+=h["source_QC_VPD"]=="0"
    orig_neg+=rh is not None and rh<0
    orig_sub1+=rh is not None and 0<=rh<1
    era_available+=era is not None and 0<=era<=100
    mds_available+=mds is not None and 0<=mds<=100
    if era is not None and mds is not None and 0<=era<=100 and 0<=mds<=100:
     both+=1;delta=abs(era-mds)
     agree5+=delta<=5;disagree10+=delta>10
     largest_diff=max(largest_diff,delta)
    if td is not None:max_Tdiff=max(max_Tdiff,abs(td))
    if diff is not None:max_delta=max(max_delta,abs(diff))
   if qc0 or era_available!=len(hh) or e["original_full_event_ERA_covered"]!="True":
    raise ValueError("Stage45 42 low-numeric candidate is not full or contains QC0")
   if both==len(hh) and disagree10==0: lane="MDS_ERA_CONCORDANT_BUT_REANALYSIS_PROVENANCE_PENDING"
   elif both and disagree10:lane="MDS_ERA_DISAGREEMENT_REQUIRES_INDEPENDENT_REFERENCE"
   elif both==0:lane="SOURCE_ERA_ONLY_NO_INDEPENDENT_TOWER_REFERENCE"
   else:lane="PARTIAL_MDS_COMPARISON_NO_INDEPENDENT_REFERENCE"
   if max_Tdiff>5:lane="SOURCE_TOWER_VS_ERA_T_DELTA_GT5C_HOLD"
   lowout.append(dict(site=key[0],episode_id=key[1],
    start_native=r["original_native_start"],end_native=r["original_native_end"],
    original_HH=len(hh),
    original_source_RH_negative_native_HH=orig_neg,
    original_source_RH_sub1pct_native_HH=orig_sub1,
    source_original_QC0_VPD_native_HH=qc0,
    source_ERA_RH_available_native_HH=era_available,
    source_MDS_RH_available_native_HH=mds_available,
    ERA_MDS_both_available_native_HH=both,
    ERA_MDS_agreement_at_most5pp_HH=agree5,
    ERA_MDS_disagreement_over10pp_HH=disagree10,
    max_abs_ERA_minus_MDS_RH_pp=round(largest_diff,6),
    max_abs_tower_T_minus_source_ERA_T_C=round(max_Tdiff,6),
    max_abs_original_vs_ERA_candidate_VPD_hPa=round(max_delta,6),
    source_before_trial_edge_untrusted=any(ed["neighbor_untrusted"]!="False" for ed in ee),
    alternative_reference_lane=lane,
    required_independent_evidence="RAW_TOWER_MET_SENSOR_QC_OR_INDEPENDENT_ERA5LAND_GRID_AND_TIME_MATCH",
    scientific_status="UNAPPROVED_EVENT_SCIENCE_REVIEW",
    production_DATM_authorized=False))
  else:raise ValueError("unexpected event owner")
 if len(neighborout)!=333 or len(lowout)!=42:
  raise ValueError("Assistant lane actual 333 + 42 science evidence count incorrect")
 siteout=[]
 for site in SITES:
  aa=[x for x in neighborout if x["site"]==site];bb=[x for x in lowout if x["site"]==site]
  ct=Counter(x["triage_priority"] for x in aa)
  siteout.append(dict(site=site,
   original_Stage46_assistant_neighbor_events=len(aa),
   original_Stage46_assistant_low_numeric_events=len(bb),
   neighbor_nonphysical_RH_events=ct["NONPHYSICAL_ADJACENT_ORIGINAL_RH_HOLD"],
   neighbor_low_extreme_RH_events=ct["ORIGINAL_NEIGHBOR_EXTREME_LOW_RH_HOLD"],
   neighbor_unmeasured_QC_events=ct["SOURCE_QC2_OR_NONMEASURED_NEIGHBOR_HOLD"],
   neighbor_other_original_P2P3_events=ct["OTHER_UNAPPROVED_P2P3_NEIGHBOR_HOLD"],
   low_numeric_events_WITH_MDS_comparable=sum(x["ERA_MDS_both_available_native_HH"]>0 for x in bb),
   low_numeric_events_ERA_only=sum(x["ERA_MDS_both_available_native_HH"]==0 for x in bb),
   new_science_approvals=0,full_forcing_site_pass=False))
 out.mkdir(exist_ok=False)
 write(out/"stage47_333_ORIGINAL_NEIGHBOR_QC_RH_JUMP_DIAGNOSIS.csv",NEIGH_COLUMNS,neighborout)
 write(out/"stage47_ALL333_NATIVE_ORIGINAL_NEIGHBOR_EDGE_EVIDENCE.csv",EDGE_COLUMNS,edgeout)
 write(out/"stage47_42_NUMERIC_SOURCE_ERA_MDS_SCIENTIFIC_EVIDENCE.csv",LOW_COLUMNS,lowout)
 write(out/"stage47_TEN_SITE_ASSISTANT_OWNER_WORKLOAD.csv",SITE_COLUMNS,siteout)
 summary=dict(input_SHA256={k:checksum(v) for k,v in paths.items()},
  original_source_events_483=True,original_P2P3_1574_not_yet_approved=True,
  Assistant_source_neighbor_events=len(neighborout),
  Assistant_low_numeric_event_candidates=len(lowout),
  Claude_108_cases_not_modified=True,
  stage24_approved_166_and_P1_HOLD_46_and_RH_plateaus_10_preserved=True,
  new_science_approvals=0,original_FLUXMET_DATM_Slurm_modified=False)
 (out/"stage47_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 doc=["# Batch05 Stage47 — Assistant track A: 333 source-neighbor issues and 42 numeric candidate methods",
  "","**SOURCE/FORMAL DATM UNCHANGED. 0 new science approvals.**",
  "Stage45 original source was fully verified but the 333 events had at least one uncertain adjacent source QC or RH. No smoothing to a physically inconsistent neighbor.",
  "","## 333 adjacent original source event classifications"]
 for lane,n in sorted(Counter(x["triage_priority"] for x in neighborout).items()):
  doc.append("- **{}**: {} source events".format(lane,n))
 doc+=["","## 42 source-ERA low-numeric event alternative-reference evidence"]
 for lane,n in sorted(Counter(x["alternative_reference_lane"] for x in lowout).items()):
  doc.append("- **{}**: {} original events".format(lane,n))
 doc+=["","## Ten sites"]
 for x in siteout:
  doc.append("- {}: 333-neighbor events {} and low-numeric events {}; MDS comparable in {} low events".format(
   x["site"],x["original_Stage46_assistant_neighbor_events"],
   x["original_Stage46_assistant_low_numeric_events"],
   x["low_numeric_events_WITH_MDS_comparable"]))
 doc+=["","## Next scientific decisions",
  "1. Original RH <0 or >100 on a neighboring half-hour means the NEIGHBOR is not a safe interpolation anchor.",
  "2. Preserve original native QC0 measurements and compare raw source QC1/QC2 with physical temperature and outside sources; a non-QC0 neighbor is not independently validated observation.",
  "3. Even MDS vs ERA agreement is not independent field confirmation; the 42 low numerical risk events remain NOT approved.",
  "4. Claude owns the separate 108 large-change and new-jump events, not these 375; never merge overlay without user science consent.",
  "5. Source Stage24 approved166, P1 HOLD46, RH plateau10 and original 1574 P2/P3 stay exactly unchanged.",""]
 (out/"STAGE47_ASSISTANT_SOURCE_NEIGHBOR_AND_42_PILOT_SCIENCE.md").write_text("\n".join(doc)+"\n",encoding="utf-8")
 print("STAGE47 SUCCESS | ASSISTANT_NEIGHBOR_EVENTS",len(neighborout),
       "LOW_NUMERIC_EVENTS",len(lowout),
       "CLAUDE_108 untouched; new scientific approvals ZERO")
 print("STAGE47 NEIGHBOR_LANES",json.dumps(dict(Counter(x["triage_priority"] for x in neighborout)),sort_keys=True))
 print("STAGE47 LOW_NUMERIC_EVIDENCE",json.dumps(dict(Counter(x["alternative_reference_lane"] for x in lowout)),sort_keys=True))
 print("STAGE47_REPORT="+str(out/"STAGE47_ASSISTANT_SOURCE_NEIGHBOR_AND_42_PILOT_SCIENCE.md"))
 print("STAGE47_OUT="+str(out))
 print("STAGE47 ORIGINAL_166_APPROVED/46_P1HOLD/10_RHPLATEAU/1574_P2P3/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

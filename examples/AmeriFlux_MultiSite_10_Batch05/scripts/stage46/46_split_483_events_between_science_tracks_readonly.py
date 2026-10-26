#!/usr/bin/env python3
"""Batch05 Stage46: split real Stage45 483 source P2P3 events for parallel
human-reviewed research. Never write production forcing, approve new science,
submit Slurm jobs, or modify source/approved166/P1 HOLD46/RH platforms10.

Assistant lane: 333 untrusted adjacent native source observations + 42
numerically lower-risk ERA source methods, ALL STILL UNAPPROVED.
Claude lane: 77 >10hPa VPD source corrections + 22 new >2hPa jumps +
9 new >4hPa discontinuities. Read-only prioritized review and alternative
hypotheses. Output exact native event evidence, site summary and work briefs.
"""
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

LANES={
 "ORIGINAL_EXTERNAL_NEIGHBOR_QC_OR_RH_UNCERTAIN":"ASSISTANT_NEIGHBOR_PROVENANCE",
 "NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL":"ASSISTANT_NUMERIC_PILOT",
 "LARGE_VPD_CHANGE_GT10HPA_REVIEW":"CLAUDE_LARGE_RECONSTRUCTION",
 "NEW_EXTERNAL_OR_INTERNAL_GT2HPA_HOLD":"CLAUDE_NEW_GT2_DISCONTINUITY",
 "NEW_EXTERNAL_OR_INTERNAL_GT4HPA_HOLD":"CLAUDE_NEW_GT4_DISCONTINUITY"}
COUNTS=dict(ORIGINAL_EXTERNAL_NEIGHBOR_QC_OR_RH_UNCERTAIN=333,
 NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL=42,
 LARGE_VPD_CHANGE_GT10HPA_REVIEW=77,
 NEW_EXTERNAL_OR_INTERNAL_GT2HPA_HOLD=22,
 NEW_EXTERNAL_OR_INTERNAL_GT4HPA_HOLD=9)
SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
RE={"site","episode_id","original_HH","original_start_native",
 "original_end_native","max_abs_VPD_change_hPa","risk_screen",
 "external_neighbors_unmeasured_or_unapproved",
 "external_neighbors_implied_RH_below10_or_unphysical",
 "external_edges_uncomparable","source_original_QC0_HH",
 "new_internal_jump_gt2","new_internal_jump_gt4",
 "new_external_jump_gt2","new_external_jump_gt4"}
RE_E={"site","context_kind","context_id","side",
 "candidate_time","neighbor_time","neighbor_kind","neighbor_original_QC_VPD",
 "neighbor_implied_RH_water_pct","before_jump_hPa","after_jump_hPa",
 "new_gt2","new_gt4","neighbor_untrusted",
 "neighbor_unphysical_or_lt10","comparable"}
RE_S={"site","original_P2P3_native_HH","original_Stage27_episodes",
 "full_source_verified","event_low_numeric_risk_science_pending"}
RE_43={"site","episode","method","native_HH"}
REPORT=("owner_lane","site","episode_id","original_native_start","original_native_end",
 "original_HH","Stage45_priority_gate","max_abs_VPD_change_hPa",
 "new_internal_gt2_count","new_internal_gt4_count",
 "new_external_gt2_count","new_external_gt4_count",
 "untrusted_original_neighbor_count","extreme_original_neighbor_RH_count",
 "uncomparable_neighbor_count","original_neighbor_QC0_count",
 "original_neighbor_QC1_count","original_neighbor_QC2_count",
 "original_neighbor_QCother_or_missing_count","neighbor_RH_below10_or_invalid",
 "original_external_before_gt2_count","hypothetical_external_after_gt2_count",
 "full_event_edge_count","previous_Stage43_pilot_event",
 "recommended_science_action","source_file_and_DATM_changes_allowed")
SITEOUT=("site","original_P2P3_HH_unapproved","original_episodes",
 "assistant_neighbor_events","assistant_low_numeric_events",
 "claude_gt10_VPD_events","claude_new_gt2_events","claude_new_gt4_events",
 "Stage43_prior_numeric_event_count","science_approved_new","full_forcing_science_pass")
def hashfile(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def read(p,cols):
 if not p.is_file() or p.is_symlink():raise ValueError("source not found "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f);fields=r.fieldnames or []
  if not cols.issubset(fields) or len(fields)!=len(set(fields)):
   raise ValueError("source columns absent "+str(p))
  out=list(r)
 if any(None in x or any(v is None for v in x.values()) for x in out):
  raise ValueError("source malformed "+str(p))
 return out
def wr(p,columns,rs):
 with p.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=columns,extrasaction="raise")
  w.writeheader();w.writerows(rs)
def science_action(g):
 return {
 "ORIGINAL_EXTERNAL_NEIGHBOR_QC_OR_RH_UNCERTAIN":
   "Identify original adjacent QC1/QC2 or invalid RH, compare tower/source met vs source ERA/MDS/independent ERA5-Land; do not smooth to unmeasured neighbor.",
 "NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL":
   "Audit independent reanalysis/in-situ provenance and original QC; if supported, prepare explicit science-approval request, not DATM edits.",
 "LARGE_VPD_CHANGE_GT10HPA_REVIEW":
   "Review temperature and humidity units/QC/timestamp; independent ERA5-Land or station RH vs full source event; large change scientifically unapproved.",
 "NEW_EXTERNAL_OR_INTERNAL_GT2HPA_HOLD":
   "Compare raw source event and +/-30min native neighbors, examine full-event alternate reanalysis humidity; forbid new >2hPa threshold crossing.",
 "NEW_EXTERNAL_OR_INTERNAL_GT4HPA_HOLD":
   "Highest priority: new >4hPa discontinuity; inspect paired source T/RH/VPD QC, time alignment and neighboring source.",
 }[g]
def selftest():
 assert sum(COUNTS.values())==483
 assert sum(v for k,v in COUNTS.items() if LANES[k].startswith("CLAUDE"))==108
 assert len(SITES)==10
 print("STAGE46 SELF-TEST PASS | 483 original events 375 assistant lane/108 Claude lane, event evidence provenance, zero writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage45-dir",type=Path)
 p.add_argument("--stage43-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage45_dir,a.stage43_dir,a.out)):
  p.error("--stage45-dir --stage43-dir --out required")
 d45,d43=a.stage45_dir.expanduser().resolve(),a.stage43_dir.expanduser().resolve()
 out=a.out.expanduser().resolve()
 if not d45.is_dir() or not d43.is_dir() or out.exists() or not out.parent.is_dir():
  p.error("source dirs required; --out must be NEW")
 if any(out==x or out in x.parents or x in out.parents for x in (d45,d43)):
  p.error("output overlaps original source science reports")
 files={
  "events":d45/"stage45_483_ORIGINAL_EVENTS_TRUE_NATIVE_VPD_QC.csv",
  "edges":d45/"stage45_TRUE_ORIGINAL_EVENT_AND_JOINED_RUN_EXTERNAL_EDGES.csv",
  "sites":d45/"stage45_ALL10_SITE_REAL_SOURCE_BATCH_PROGRESS.csv",
  "manifest":d45/"stage45_manifest.json",
  "stage43":d43/"stage43_TEN_NUMERIC_EVENTS.csv"}
 events=read(files["events"],RE)
 edges=read(files["edges"],RE_E)
 sites=read(files["sites"],RE_S)
 prev=read(files["stage43"],RE_43)
 m=json.loads(files["manifest"].read_text())
 if (len(events),len(sites),len(prev))!=(483,10,10):
  raise ValueError("actual Stage45/43 source populations differ")
 if m.get("expected_original_P2P3_HH")!=1574 or m.get("expected_original_events")!=483:
  raise ValueError("Stage45 provenance manifest differs")
 if m.get("source_science_new_approvals")!=0 or m.get("site_source_holds"):
  raise ValueError("unexpected Stage45 source-science approvals or source holds")
 if m.get("independently_original_source_verified_native_HH")!=1574 or m.get("original_episodes_source_verified")!=483:
  raise ValueError("original source-native T/VPD/QC verification is incomplete")
 c=Counter(x["risk_screen"] for x in events)
 if dict(c)!=COUNTS:raise ValueError("actual Stage45 483 event gate population differs")
 keys={(x["site"],x["episode_id"]) for x in events}
 if len(keys)!=483:raise ValueError("duplicate original event key")
 earlier={(x["site"],x["episode"]) for x in prev}
 if len(earlier)!=10:raise ValueError("Stage43 original ten numeric events differ")
 all_edges=defaultdict(list)
 for x in edges:
  if x["context_kind"]=="ORIGINAL_STAGE27_EVENT":
   k=(x["site"],x["context_id"])
   if k not in keys:raise ValueError("unlinked original source edge "+str(k))
   all_edges[k].append(x)
 records=[]
 for e in events:
  k=e["site"],e["episode_id"]
  ev=all_edges[k]
  if len(ev)<2:raise ValueError("original source event external evidence missing "+str(k))
  qc=Counter(x["neighbor_original_QC_VPD"] for x in ev)
  bad=sum(x["neighbor_unphysical_or_lt10"]=="True" for x in ev)
  numeric=lambda s:sum(float(x[s])>2 for x in ev if x[s] not in ("","nan"))
  records.append(dict(owner_lane=LANES[e["risk_screen"]],site=k[0],episode_id=k[1],
   original_native_start=e["original_start_native"],original_native_end=e["original_end_native"],
   original_HH=int(e["original_HH"]),
   Stage45_priority_gate=e["risk_screen"],
   max_abs_VPD_change_hPa=float(e["max_abs_VPD_change_hPa"]),
   new_internal_gt2_count=int(e["new_internal_jump_gt2"]),
   new_internal_gt4_count=int(e["new_internal_jump_gt4"]),
   new_external_gt2_count=int(e["new_external_jump_gt2"]),
   new_external_gt4_count=int(e["new_external_jump_gt4"]),
   untrusted_original_neighbor_count=int(e["external_neighbors_unmeasured_or_unapproved"]),
   extreme_original_neighbor_RH_count=int(e["external_neighbors_implied_RH_below10_or_unphysical"]),
   uncomparable_neighbor_count=int(e["external_edges_uncomparable"]),
   original_neighbor_QC0_count=qc["0"],
   original_neighbor_QC1_count=qc["1"],
   original_neighbor_QC2_count=qc["2"],
   original_neighbor_QCother_or_missing_count=sum(v for q,v in qc.items() if q not in ("0","1","2")),
   neighbor_RH_below10_or_invalid=bad,
   original_external_before_gt2_count=numeric("before_jump_hPa"),
   hypothetical_external_after_gt2_count=numeric("after_jump_hPa"),
   full_event_edge_count=len(ev),
   previous_Stage43_pilot_event=k in earlier,
   recommended_science_action=science_action(e["risk_screen"]),
   source_file_and_DATM_changes_allowed=False))
 records.sort(key=lambda x:(x["site"],x["original_native_start"],x["episode_id"]))
 siteoutput=[]
 for x in sites:
  site=x["site"];rs=[r for r in records if r["site"]==site]
  siteoutput.append(dict(site=site,original_P2P3_HH_unapproved=int(x["original_P2P3_native_HH"]),
   original_episodes=int(x["original_Stage27_episodes"]),
   assistant_neighbor_events=sum(r["owner_lane"]=="ASSISTANT_NEIGHBOR_PROVENANCE" for r in rs),
   assistant_low_numeric_events=sum(r["owner_lane"]=="ASSISTANT_NUMERIC_PILOT" for r in rs),
   claude_gt10_VPD_events=sum(r["owner_lane"]=="CLAUDE_LARGE_RECONSTRUCTION" for r in rs),
   claude_new_gt2_events=sum(r["owner_lane"]=="CLAUDE_NEW_GT2_DISCONTINUITY" for r in rs),
   claude_new_gt4_events=sum(r["owner_lane"]=="CLAUDE_NEW_GT4_DISCONTINUITY" for r in rs),
   Stage43_prior_numeric_event_count=sum(r["previous_Stage43_pilot_event"] for r in rs),
   science_approved_new=0,full_forcing_science_pass=False))
 if sum(r["original_P2P3_HH_unapproved"] for r in siteoutput)!=1574:
  raise ValueError("per-site native P2P3 counts changed")
 mine=[x for x in records if x["owner_lane"].startswith("ASSISTANT")]
 claude=[x for x in records if x["owner_lane"].startswith("CLAUDE")]
 low=[x for x in records if x["owner_lane"]=="ASSISTANT_NUMERIC_PILOT"]
 if len(mine)!=375 or len(claude)!=108 or len(low)!=42:
  raise ValueError("source event split incorrect")
 out.mkdir(exist_ok=False)
 wr(out/"stage46_ASSISTANT_333_NEIGHBOR_QC_AND_42_NUMERIC_EVENTS.csv",REPORT,mine)
 wr(out/"stage46_ASSISTANT_42_NUMERIC_SCIENCE_APPROVAL_CANDIDATES.csv",REPORT,low)
 wr(out/"stage46_CLAUDE_108_GT10_AND_NEW_JUMP_EVENT_CASES.csv",REPORT,claude)
 wr(out/"stage46_ALL483_EXACT_SCIENCE_RESPONSIBILITY_MATRIX.csv",REPORT,records)
 wr(out/"stage46_ALL10_SITE_HH_AND_EVENT_COUNTS_BY_OWNER.csv",SITEOUT,siteoutput)
 meta=dict(input_SHA256={name:hashfile(p) for name,p in files.items()},
  original_P2P3_1574_HH_unapproved=True,original_483_events=True,
  source_site_origin_verified_nine_nine=True,
  assistant_333_neighbor_and_42_low_numeric_events=375,
  claude_77_gt10_and_22_new_gt2_and_9_new_gt4_events=108,
  stage43_old_10_numeric_method_events=len(earlier),
  all_previous_166_approved_preserved=True,
  P1_46_HOLD_and_RH10_platform_preserved=True,
  new_scientific_approvals=0,source_FLUXMET_DATM_CIME_Slurm_modified=False)
 (out/"stage46_manifest.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 md=["# Stage46 — actual 483 event parallel work handoff",
  "","**Original source/forcing untouched. 1,574 P2P3 original native HH still science-unapproved.**",
  "The 483 event lanes are mutually exclusive according to Stage45 priority; the same original event can contain overlapping physical risk mechanisms.",
  "Stage45 483 connected native runs also total 483 (no earlier original events were joined), therefore no artificial merging benefit was observed in THIS operator result.",
  "","## Separate investigator work",
  "**Assistant track A: 333 uncertain native neighbors + 42 numerical source checks (375 original events).**",
  "Inspect original neighbor QC1/QC2, physically impossible or <10% RH, relative change and independent reference. Only 42 low-numerical-risk source-ERA candidates are eligible for explicit science approval review. None is approved.",
  "**Claude track B: 77 ERA VPD changes >10 hPa + 22 new >2 hPa discontinuities + 9 new >4 hPa (108 events).**",
  "Investigate paired original tower T/VPD/QC, timestamp and unit conventions, reanalysis/site provenance; propose an alternative full-event physical RH mechanism without modifying originals. Return an evidence table and protected HOLDs.",
  "","## Exact ten-site split"]
 for x in siteoutput:
  md.append("- {}: {} original P2P3 HH, {} original events; Assistant neighbor {} + numerical {}, Claude >10hPa {} + new >2hPa {} + new >4hPa {}".format(
   x["site"],x["original_P2P3_HH_unapproved"],x["original_episodes"],
   x["assistant_neighbor_events"],x["assistant_low_numeric_events"],
   x["claude_gt10_VPD_events"],x["claude_new_gt2_events"],x["claude_new_gt4_events"]))
 md+=["","## Science approval gates",
  "1. Source reanalysis ERA covering 483 events does not establish physically accurate tower humidity. Never auto-approve or rewrite DATM.",
  "2. Existing Stage24 approved 166, P1 manually HOLD 46, 10 RH saturation records remain unchanged and out-of-scope to source-P2P3 science lanes.",
  "3. Each lane must retain original site/native time, original T/VPD/QC, source document SHA, before-vs-after edge comparison and scientific uncertainty.",
  "4. Site UiD has zero original P2P3 source HH but is not established as completely full-forcing validated.",
  "5. BE-Bra SourceMods missing and DK-Sor 2025 merge/QC logs are other projects; do not mix their status with these 10 AmeriFlux sites.",""]
 (out/"STAGE46_PARALLEL_ASSISTANT_CLAUDE_SCIENCE_HANDOFF.md").write_text("\n".join(md)+"\n")
 print("STAGE46 SUCCESS | 483 original events partitioned, ASSISTANT 333 neighbor+42 low-numeric, CLAUDE 77 large+22 new>2+9 new>4")
 print("STAGE46 SITE_SPLIT",json.dumps({r["site"]:{"HH":r["original_P2P3_HH_unapproved"],"assistant_neigh":r["assistant_neighbor_events"],"assistant_low":r["assistant_low_numeric_events"],"claude_large":r["claude_gt10_VPD_events"],"claude_gt2":r["claude_new_gt2_events"],"claude_gt4":r["claude_new_gt4_events"]} for r in siteoutput},sort_keys=True))
 print("STAGE46 OUTPUT="+str(out))
 print("STAGE46 ORIGINAL/P1HOLD46/RHPLATFORM10/APPROVED166/P2P3_1574/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

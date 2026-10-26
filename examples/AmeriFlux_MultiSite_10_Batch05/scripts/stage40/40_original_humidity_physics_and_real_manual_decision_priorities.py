#!/usr/bin/env python3
"""Batch05 Stage40, read-only. Identify which of the 15 original science
events / 16 Stage39 methods truly require HUMAN investigator judgement by
checking ORIGINAL tower RH implied from original T and VPD, source MDS and
source ERA RH, and actual trial magnitude. Hard QC0 and all P1 HOLD remain.
A contiguous VPD candidate with no NEW >2/4 hPa jumps is NOT scientific
validation when RH modification is 5--18 hPa.

Also show the 13 actual US-UMB source file+ZIP member names from Stage39.
All outputs new research review only; NO original/approved/forcing writes.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta
R39={"site","episode_id","method","original_first_native",
 "original_last_native","original_episode_HH","method_count_for_same_episode",
 "max_abs_candidate_VPD_change_hPa","production_authorized"}
R38={"site","episode_id","native_time","research_method",
 "original_source_T_C","original_source_VPD_hPa","original_VPD_QC",
 "research_RH_source_pct","research_VPD_at_original_T_hPa",
 "research_VPD_change_vs_original_hPa","production_forcing_authorization"}
R27={"site","episode_id","native_time","TA_F_C","VPD_F_hPa","TA_F_QC",
 "VPD_F_QC","RH_ERA_pct","RH_MDS_pct"}
RINV={"site","relative_source_path","kind","sha256",
 "matching_FLUXMET_HH_members","other_FLUXMET_like_members"}
RSTATUS={"site","original_P2P3_remaining_unapproved_HH"}
EVENT_COLS=("site","original_episode","method","original_start_native",
 "original_end_native","original_HH","original_QC0_HH","source_QC2_or_other_HH",
 "source_original_implied_RH_below0_HH","source_original_implied_RH_below5_HH",
 "source_original_implied_RH_below10_HH","source_original_implied_RH_above100_HH",
 "original_implied_RH_min_pct","original_implied_RH_max_pct",
 "source_ERA_vs_MDS_RH_max_abs_diff_pp",
 "candidate_RH_min_pct","candidate_RH_max_pct",
 "max_abs_change_VPD_hPa","mean_abs_change_VPD_hPa",
 "original_VPD_max_hPa","hypothetical_VPD_max_hPa",
 "unchanged_VPD_native_HH","same_episode_two_method_choices",
 "science_review_priority","specific_investigator_decision",
 "scientific_status","production_forcing_authorized")
DETAIL_COLS=("site","native_time","episode_id","method",
 "original_T_C","original_VPD_hPa","original_QC_T","original_QC_VPD",
 "original_implied_RH_water_pct","source_ERA_RH_pct",
 "source_MDS_RH_pct","trial_RH_pct","trial_VPD_hPa",
 "trial_minus_original_VPD_hPa","original_implied_RH_category",
 "trial_original_comparison","production_forcing_authorized")
UMB_COLS=("original_source_file","kind","sha256","exact_UMB_FLUXMET_HH_members",
 "other_FLUXMET_or_MET_members","source_verification_status")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def num(x):
 try:
  v=float(x)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except(TypeError,ValueError):pass
 return None
def es(t):
 if t is None or not -80<=t<=60:raise ValueError("source T invalid saturation")
 return 6.112*math.exp(17.67*t/(243.5+t))
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("source file absent "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f)
  if not required.issubset(r.fieldnames or []) or len(r.fieldnames or [])!=len(set(r.fieldnames or [])):
   raise ValueError("original source CSV fields wrong "+str(p))
  rows=list(r)
 if any(None in x or any(v is None for v in x.values()) for x in rows):
  raise ValueError("malformed original source CSV "+str(p))
 return rows
def keyed(rows,names):
 d={}
 for x in rows:
  k=tuple(x[q] for q in names)
  if k in d:raise ValueError("duplicate original source key "+str(k))
  d[k]=x
 return d
def wcsv(p,cols,rows):
 with p.open("x",newline="",encoding="utf-8") as f:
  r=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  r.writeheader();r.writerows(rows)
def classify_rh(r):
 if r<0:return "ORIGINAL_RH_NEGATIVE_PHYSICALLY_IMPOSSIBLE"
 if r<5:return "ORIGINAL_RH_BELOW5_PERCENT_SUSPECT"
 if r<10:return "ORIGINAL_RH_BELOW10_PERCENT_EXTREME"
 if r>100:return "ORIGINAL_RH_ABOVE100_PERCENT_PHYSICALLY_IMPOSSIBLE"
 return "ORIGINAL_RH_IN_PHYSICAL_RANGE"
def selftest():
 assert classify_rh(100*(1-11/es(-10)))=="ORIGINAL_RH_NEGATIVE_PHYSICALLY_IMPOSSIBLE"
 assert classify_rh(70)=="ORIGINAL_RH_IN_PHYSICAL_RANGE"
 assert es(-10)>es(-20)
 print("STAGE40 SELF-TEST PASS | source-derived RH validity, 16 source method cases, large-Delta-VPD science gates, no source writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage39-dir",type=Path)
 p.add_argument("--stage38-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage39_dir,a.stage38_dir,a.stage27_dir,a.out)):
  p.error("specify original --stage39-dir --stage38-dir --stage27-dir --out")
 d39,d38,d27=[x.expanduser().resolve() for x in (a.stage39_dir,a.stage38_dir,a.stage27_dir)]
 out=a.out.expanduser().resolve()
 if any(not x.is_dir() for x in (d39,d38,d27)) or not out.parent.is_dir() or out.exists() or any(
  out==x or out in x.parents or x in out.parents for x in (d39,d38,d27)):
  p.error("create only a NEW disjoint report directory")
 paths={
  "stage39":d39/"stage39_EXACT16_ORIGINAL_EVENT_METHOD_REVIEW.csv",
  "stage38":d38/"stage38_RESEARCH_ONLY_FULL_SOURCE_EPISODE_NATIVE_RH_VPD_CANDIDATES.csv",
  "stage27":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
  "sites":d39/"stage39_ALL10_SITE_NEXT_ACTIONS.csv",
  "umb":d39/"stage39_US_UMB_READONLY_REAL_FILE_AND_ZIP_MEMBER_INVENTORY.csv"}
 shortlisted=read(paths["stage39"],R39)
 native=read(paths["stage38"],R38)
 originals=keyed(read(paths["stage27"],R27),("site","native_time"))
 sites=read(paths["sites"],RSTATUS)
 umb=read(paths["umb"],RINV)
 manifest=json.loads((d39/"stage39_manifest.json").read_text())
 if (len(shortlisted),len(originals),len(sites),len(umb))!=(16,1574,10,13):
  raise ValueError("Stage39 original scientific populations 16/1574/10/13 changed")
 if manifest.get("exact_numeric_shortlist_methods")!=16 or manifest.get("new_scientific_approvals")!=0:
  raise ValueError("Stage39 original science approval state unexpected")
 if manifest.get("isolated_research_only_native_preview_HH")!=20:
  raise ValueError("Stage39 original 20 unique-method research native HH changed")
 native_index=keyed(native,("site","episode_id","research_method","native_time"))
 by_method=defaultdict(list)
 for r in native:by_method[(r["site"],r["episode_id"],r["research_method"])].append(r)
 by_event=Counter((r["site"],r["episode_id"]) for r in shortlisted)
 rows=[];events=[]
 for x in sorted(shortlisted,key=lambda a:(a["site"],a["episode_id"],a["method"])):
  site,eid,method=x["site"],x["episode_id"],x["method"]
  rrs=sorted(by_method.get((site,eid,method),[]),key=lambda r:r["native_time"])
  if not rrs or len(rrs)!=int(x["original_episode_HH"]):
   raise ValueError("Stage38 original full-method trial HH mismatch for "+str((site,eid,method)))
  if len(rrs)!=int(x["original_episode_HH"]) or rrs[0]["native_time"]!=x["original_first_native"] or rrs[-1]["native_time"]!=x["original_last_native"]:
   raise ValueError("Stage39 original episode time range changed")
  implied=[];changes=[];candrh=[];orivpd=[];candvpd=[];era_mds=[]
  cat=Counter();unchanged=0;qco=0;nonqco=0
  for r in rrs:
   k=(site,r["native_time"]);raw=originals.get(k)
   if raw is None or raw["episode_id"]!=eid:
    raise ValueError("original Stage27 source missing matching event "+str(k))
   t=num(raw["TA_F_C"]);v=num(raw["VPD_F_hPa"])
   trh=num(r["research_RH_source_pct"]);cand=num(r["research_VPD_at_original_T_hPa"])
   era=num(raw["RH_ERA_pct"]);mds=num(raw["RH_MDS_pct"])
   if None in (t,v,trh,cand) or not 0<=trh<=100 or not 0<=cand<=es(t)+.001:
    raise ValueError("invalid tower T/original VPD or trial RH/VPD")
   if abs(cand-es(t)*(1-trh/100))>.002 or abs(t-num(r["original_source_T_C"]))>.002 or abs(v-num(r["original_source_VPD_hPa"]))>.002:
    raise ValueError("source-original vs Stage38 trial values drifted")
   if raw["VPD_F_QC"]!=r["original_VPD_QC"] or raw["VPD_F_QC"]=="0":
    raise ValueError("source original QC0 or source VPD QC mismatch in 16 option shortlist")
   if r["production_forcing_authorization"]!="NO":raise ValueError("trial already contains unexpected forcing permission")
   rh=100*(1-v/es(t))
   cls=classify_rh(rh)
   cat[cls]+=1
   if rh<5:cat["CUMULATIVE_RH_BELOW5"]+=1
   if rh<10:cat["CUMULATIVE_RH_BELOW10"]+=1
   delta=cand-v
   implied.append(rh);changes.append(abs(delta));candrh.append(trh);orivpd.append(v);candvpd.append(cand)
   if abs(delta)<.01:unchanged+=1
   if era is not None and mds is not None:era_mds.append(abs(era-mds))
   nonqco+=1
   rows.append(dict(site=site,native_time=r["native_time"],episode_id=eid,method=method,
    original_T_C=t,original_VPD_hPa=v,original_QC_T=raw["TA_F_QC"],
    original_QC_VPD=raw["VPD_F_QC"],
    original_implied_RH_water_pct=round(rh,6),
    source_ERA_RH_pct=era if era is not None else "",
    source_MDS_RH_pct=mds if mds is not None else "",
    trial_RH_pct=trh,trial_VPD_hPa=cand,
    trial_minus_original_VPD_hPa=round(delta,8),
    original_implied_RH_category=cls,
    trial_original_comparison=(
      "NO_NUMERIC_CHANGE" if abs(delta)<.01 else
      "LARGE_CHANGE_GT10HPA_REVIEW" if abs(delta)>10 else
      "CHANGE_GT5HPA_REVIEW" if abs(delta)>5 else
      "CHANGE_2_TO5HPA_REVIEW" if abs(delta)>2 else
      "LOWER_CHANGE_STILL_NO_APPROVAL"),
    production_forcing_authorized="NO"))
  maxdelta=max(changes)
  if by_event[(site,eid)]>1:
   lane="METHOD_AMBIGUOUS_SCIENCE_DECISION_HOLD"
   human="Compare original-source MDS no-op vs reconstructed ERA; choose after source sensor/provenance evidence, do not silently replace."
  elif cat["ORIGINAL_RH_NEGATIVE_PHYSICALLY_IMPOSSIBLE"] or cat["ORIGINAL_RH_ABOVE100_PERCENT_PHYSICALLY_IMPOSSIBLE"]:
   lane="PHYSICALLY_IMPOSSIBLE_SOURCE_HUMIDITY_REQUIRES_EVENT_DECISION"
   human="Original T+VPD imply RH outside [0,100]; investigate original source filling/provenance and select a supported event-level RH method."
  elif maxdelta>10:
   lane="SEVERE_VPD_RECONSTRUCTION_GT10HPA_REVIEW"
   human="Candidate changes VPD by >10 hPa. Inspect source QC2 and independent humidity evidence before permitting repair."
  elif cat["ORIGINAL_RH_BELOW5_PERCENT_SUSPECT"] or maxdelta>5:
   lane="LARGE_VPD_OR_ORIGINAL_RH_SUSPECT_REVIEW"
   human="Original humidity extreme or VPD reconstruction >5 hPa. Test ERA reference/source MDS vs tower context; no automatic approval."
  elif maxdelta>2:
   lane="MODERATE_VPD_CHANGE_2_TO5HPA_REVIEW"
   human="No new >2/4 hPa boundary crossing in Stage38 but source-magnitude still needs review."
  else:
   lane="LOW_DELTA_SCREEN_PASSED_UNAPPROVED"
   human="Source physically plausible and reconstruction difference <=2 hPa; eligible for investigator review, still unapproved."
  events.append(dict(site=site,original_episode=eid,method=method,
   original_start_native=rrs[0]["native_time"],original_end_native=rrs[-1]["native_time"],
   original_HH=len(rrs),original_QC0_HH=qco,source_QC2_or_other_HH=nonqco,
   source_original_implied_RH_below0_HH=cat["ORIGINAL_RH_NEGATIVE_PHYSICALLY_IMPOSSIBLE"],
   source_original_implied_RH_below5_HH=cat["CUMULATIVE_RH_BELOW5"],
   source_original_implied_RH_below10_HH=cat["CUMULATIVE_RH_BELOW10"],
   source_original_implied_RH_above100_HH=cat["ORIGINAL_RH_ABOVE100_PERCENT_PHYSICALLY_IMPOSSIBLE"],
   original_implied_RH_min_pct=round(min(implied),6),
   original_implied_RH_max_pct=round(max(implied),6),
   source_ERA_vs_MDS_RH_max_abs_diff_pp=round(max(era_mds),6) if era_mds else "",
   candidate_RH_min_pct=round(min(candrh),6),
   candidate_RH_max_pct=round(max(candrh),6),
   max_abs_change_VPD_hPa=round(maxdelta,6),
   mean_abs_change_VPD_hPa=round(sum(changes)/len(changes),6),
   original_VPD_max_hPa=round(max(orivpd),6),
   hypothetical_VPD_max_hPa=round(max(candvpd),6),
   unchanged_VPD_native_HH=unchanged,
   same_episode_two_method_choices=by_event[(site,eid)]>1,
   science_review_priority=lane,
   specific_investigator_decision=human,
   scientific_status="READ_ONLY_RESEARCH_NOT_APPROVED",
   production_forcing_authorized="NO"))
 if len(events)!=16 or len(by_event)!=15 or sum(n>1 for n in by_event.values())!=1:
  raise ValueError("Expected exactly 16 original method choices, 15 events and one ambiguous event")
 inventory=[dict(original_source_file=x["relative_source_path"],kind=x["kind"],
  sha256=x["sha256"],
  exact_UMB_FLUXMET_HH_members=x["matching_FLUXMET_HH_members"],
  other_FLUXMET_or_MET_members=x["other_FLUXMET_like_members"],
  source_verification_status="UNVERIFIED_SOURCE_FILE_INVENTORY_ONLY")
  for x in umb]
 out.mkdir(exist_ok=False)
 wcsv(out/"stage40_EXACT16_EVENT_SOURCE_HUMIDITY_PHYSICS_AND_SCIENCE_DECISION.csv",EVENT_COLS,events)
 wcsv(out/"stage40_ALL_NATIVE_OPTIONS_ORIGINAL_RH_ERA_MDS_VPD_TRIAL.csv",DETAIL_COLS,rows)
 wcsv(out/"stage40_US_UMB_13_EXISTING_ARCHIVE_NAMES_AND_MEMBERS.csv",UMB_COLS,inventory)
 lanes=Counter(r["science_review_priority"] for r in events)
 summary=dict(source_sha256={key:sha(path) for key,path in paths.items()},
  original_16_method_cases=len(events),original_distinct_events=len(by_event),
  original_15_event_1_ambiguous=True,
  original_source_native_option_rows=len(rows),
  original_20_unique_method_research_preview_HH_unchanged=True,
  grouped_human_review_lanes=dict(lanes),
  original_US_UMB_source_files_inventoried=len(inventory),
  original_P2P3_unapproved_1574=True,Stage24_166_approved_unchanged=True,
  P1_original_46_manual_HOLD_unchanged=True,
  scientific_approvals_new=0,production_DATM_forcing_changes=False,
  source_data_changed=False,Slurm_submitted=False)
 (out/"stage40_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 report=["# Stage40 — original humidity physics: 16 candidate methods, 15 events","",
  "**No new science or forcing approvals.** Stage39 continuity alone cannot validate large VPD substitutions.",
  "RH is derived from ORIGINAL selected tower T and ORIGINAL VPD under water saturation;",
  "RH <0 or >100 indicates a physically inconsistent ORIGINAL pair, while low but positive RH alone",
  "is extreme/suspect, not proof that the original tower data are invalid.","",
  "## Event-level science priorities"]
 for lane,n in sorted(lanes.items()):report.append("- **{}**: {} method options".format(lane,n))
 report+=["","| Site | Original event | Method | Native HH | Original RH water min % | Max delta VPD hPa | Scientific state |",
 "|---|---|---|---:|---:|---:|---|"]
 for r in events:
  report.append("| {} | {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["original_episode"],r["method"],r["original_HH"],
   r["original_implied_RH_min_pct"],r["max_abs_change_VPD_hPa"],
   r["science_review_priority"]))
 report+=["","## Actual US-UMB source files (filenames, no invented raw source)",
  "Exact original UMB FLUXMET_HH member found in Stage39 inventory: **{}**".format(
    sum(bool(x["matching_FLUXMET_HH_members"]) for x in umb))]
 for r in inventory:report.append("- {} | {} | members: {}".format(
  r["original_source_file"],r["kind"],
  r["other_FLUXMET_or_MET_members"] or r["exact_UMB_FLUXMET_HH_members"] or "(none)"))
 report+=["","## Progression without asking to approve 16 cases individually",
  "1. **No-change trial**: if one candidate leaves original VPD unchanged, that is not an actual repair. If original source RH is physically invalid, retaining it is not sufficient.",
  "2. **Severe >10 hPa changes**: source evidence and meteorological context needed before one may approve replacing the old VPD, even with zero new screened boundary jumps.",
  "3. **Lower delta**: may enter further separate Post-v5 isolated numerical forcing QC, but no user science authorization is implied.",
  "4. **US-UMB**: original FLUXMET_HH absent in site ZIP/CSV inventory; obtain/verify correct native source before accepting its 23 source anomalies. Do not fake a derived original source.",
  "5. Existing Stage24 166 approved, original P1 manual 46 HOLD and P2/P3 1574 unchanged; no DATM model or Slurm writes.",""]
 (out/"STAGE40_TRUE_HUMAN_REVIEW_AND_SAFE_PILOT_QUEUE.md").write_text("\n".join(report)+"\n")
 print("STAGE40 SUCCESS | EXACT 16 source method options, 15 original events; original tower RH physics checked; no forcing")
 print("STAGE40 SCIENCE_LANES",json.dumps(dict(lanes),sort_keys=True))
 for r in events:
  print("STAGE40 CASE",r["site"],r["original_episode"],r["method"],
        "RH_MIN",r["original_implied_RH_min_pct"],
        "MAX_DVPD",r["max_abs_change_VPD_hPa"],r["science_review_priority"])
 print("STAGE40 US_UMB_FILE_INVENTORY",len(inventory))
 print("STAGE40_REPORT="+str(out/"STAGE40_TRUE_HUMAN_REVIEW_AND_SAFE_PILOT_QUEUE.md"))
 print("STAGE40_OUT="+str(out))
 print("STAGE40 ORIGINAL_166_APPROVED/46_HOLD/1574_P2P3/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

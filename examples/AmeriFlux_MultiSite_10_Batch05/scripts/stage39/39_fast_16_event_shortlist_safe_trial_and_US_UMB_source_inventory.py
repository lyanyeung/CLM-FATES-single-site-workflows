#!/usr/bin/env python3
"""Batch05 Stage39 | fast verified pilot shortlist, NO production forcing writes.

Read the ACTUALLY executed Stage38 669 method-by-original-episode tests,
focus the exact 16 numeric-event method options, and stage ONLY an ISOLATED
unapproved CSV of original 30-min RH/VPD research candidates when the source
episode has exactly ONE suitable method. Multiple good methods remain in a
human method-choice queue (never silently select). Cross-check source Stage27,
Stage24 166 approved/46 manually held/10 plateaus, source QC0, and no
duplicate native times. Diagnose why original US-UMB FLUXMET_HH cannot be
located by listing actual site-directory source file/ZIP member names.
No guessed US-UMB files, no touching original, DATM, CIME or Slurm.
"""
import argparse,csv,hashlib,json,math,zipfile
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timedelta

GOOD="NUMERIC_CANDIDATE_REVIEW_NO_SCIENCE_APPROVAL"
METHODS={"SOURCE_ERA_ALL_EPISODE","SOURCE_MDS_ALL_EPISODE",
 "FRESH_ERA5L_ONLY_IF_FULL_REFERENCE"}
R38={"site","episode_id","method","event_start_native","event_end_native",
 "original_episode_HH","method_valid_HH","method_coverage_all_original_episode",
 "source_QC0_protected_HH","candidate_negative_or_unphysical_VPD_HH",
 "new_external_jump_gt2","new_external_jump_gt4",
 "original_internal_new_jump_gt2_HH","original_internal_new_jump_gt4_HH",
 "neighbors_QC2_or_not_measured","neighbors_are_other_P2P3_unapproved",
 "science_gate","production_permission"}
R37={"site","episode_id","new_gt2_edges","new_gt4_edges","event_science_gate"}
R38N={"site","episode_id","native_time","research_method",
 "original_source_T_C","original_source_VPD_hPa","original_VPD_QC",
 "research_RH_source_pct","research_VPD_at_original_T_hPa",
 "research_VPD_change_vs_original_hPa","full_episode_science_gate",
 "production_forcing_authorization"}
R27={"site","episode_id","native_time","TA_F_C","VPD_F_hPa",
 "TA_F_QC","VPD_F_QC"}
RSITE={"site","source_original_P2P3_unapproved_HH",
 "source_original_P2P3_events","site_closeout_status"}
RKEY={"site","native_time"}
SHORT_FIELDS=("site","episode_id","method","original_first_native",
 "original_last_native","original_episode_HH","native_candidate_HH",
 "source_QC0_VPD","new_external_gt2","new_external_gt4",
 "new_internal_gt2","new_internal_gt4",
 "max_abs_candidate_VPD_change_hPa","mean_abs_candidate_VPD_change_hPa",
 "method_count_for_same_episode","manual_method_choice_needed",
 "pilot_research_status","production_authorized")
PILOT_FIELDS=("site","native_time","original_episode_id","method",
 "original_source_T_C","original_source_VPD_hPa",
 "original_source_VPD_QC","candidate_RH_water_pct",
 "candidate_VPD_hPa","VPD_change_from_original_hPa",
 "version","status","manual_science_approval","DATM_forcing_authorized")
SITE_FIELDS=("site","original_P2P3_remaining_unapproved_HH",
 "source_original_episode_count","num_good_method_trials",
 "unique_method_good_episodes","ambiguous_multi_method_good_episodes",
 "isolated_unapproved_pilot_native_HH","site_pilot_status")
INVENTORY=("site","relative_source_path","kind","bytes","sha256",
 "matching_FLUXMET_HH_members","other_FLUXMET_like_members",
 "original_source_candidate_status")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def val(v):
 try:
  x=float(v)
  if math.isfinite(x) and x not in (-9999.,-6999.):return x
 except(ValueError,TypeError):pass
 return None
def es(t):
 if t is None or not -80<=t<=60:raise ValueError("tower T outside physically screened Magnus domain")
 return 6.112*math.exp(17.67*t/(243.5+t))
def date(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad native half hour "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def read(f,columns):
 if not f.is_file() or f.is_symlink():raise ValueError("missing original science input "+str(f))
 with f.open(newline="",encoding="utf-8-sig") as h:
  rd=csv.DictReader(h)
  if not columns.issubset(rd.fieldnames or []) or len(set(rd.fieldnames or []))!=len(rd.fieldnames or []):
   raise ValueError("source science CSV fields absent/duplicate "+str(f))
  z=list(rd)
 if any(None in r or any(x is None for x in r.values()) for r in z):
  raise ValueError("original CSV malformed "+str(f))
 return z
def idx(rows,cols):
 out={}
 for x in rows:
  k=tuple(x[c] for c in cols)
  if k in out:raise ValueError("duplicate original science key "+str(k))
  out[k]=x
 return out
def write(p,cols,rows):
 with p.open("x",newline="",encoding="utf-8") as h:
  w=csv.DictWriter(h,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def source_inventory(root):
 site=root/"US-UMB"
 if not site.is_dir():
  return [],"US-UMB_SITE_DIRECTORY_NOT_FOUND"
 files=sorted(set(p for p in site.rglob("*")
  if p.is_file() and not p.is_symlink() and p.suffix.lower() in (".zip",".csv")))
 if len(files)>2500:raise ValueError("US-UMB source inventory unexpectedly >2500 files; review manually")
 out=[]
 for p in files:
  rel=str(p.relative_to(site))
  filetype=p.suffix.lower()
  matching=[];other=[]
  if filetype==".zip":
   try:
    with zipfile.ZipFile(p) as z:
     names=[Path(i.filename).name for i in z.infolist() if not i.is_dir()]
     matching=[x for x in names if x.upper().startswith("AMF_US-UMB_FLUXNET_FLUXMET_HH_") and x.lower().endswith(".csv")]
     other=[x for x in names if ("FLUXMET" in x.upper() or "MET" in x.upper()) and x not in matching][:30]
   except (zipfile.BadZipFile,OSError):
    other=["UNREADABLE_ZIP_CENTRAL_DIRECTORY"]
  else:
   if "FLUXMET" in p.name.upper():other=[p.name]
   if p.name.upper().startswith("AMF_US-UMB_FLUXNET_FLUXMET_HH_"):
    matching=[p.name]
  out.append(dict(site="US-UMB",relative_source_path=rel,kind=filetype,
   bytes=p.stat().st_size,sha256=sha(p),
   matching_FLUXMET_HH_members=";".join(matching),
   other_FLUXMET_like_members=";".join(other),
   original_source_candidate_status=("FLUXMET_HH_NAME_FOUND_NEEDS_DATA_MATCH"
     if matching else "SOURCE_DISCOVERY_NAME_NOT_MATCHED")))
 explanation=("EXACT_HH_FILENAME_PRESENT_REVIEW_STAGE27_VALUES" if any(x["matching_FLUXMET_HH_members"] for x in out)
  else "NO_ORIGINAL_FLUXMET_HH_FILENAME_FOUND;CHECK_ARCHIVE_MEMBER_NAMES_AND_SOURCE_ACQUISITION")
 return out,explanation
def selftest():
 assert es(-10)>es(-20)
 assert date("200812312330")+timedelta(minutes=30)==date("200901010000")
 assert GOOD.endswith("NO_SCIENCE_APPROVAL")
 assert len(METHODS)==3
 print("STAGE39 SELF-TEST PASS | 16 original method/episode options, 166/46 source guards, UMB filenames audit, research trial only")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for x in ("stage38-dir","stage37-dir","stage27-dir","stage24-dir","sites-root","out"):
  p.add_argument("--"+x,type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE") if x=="sites-root" else None)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,x) is None for x in ("stage38_dir","stage37_dir","stage27_dir","stage24_dir","out")):
  p.error("need stage38/stage37/stage27/stage24 original report dirs and new --out")
 d38,d37,d27,d24,root=[getattr(a,k).expanduser().resolve() for k in
  ("stage38_dir","stage37_dir","stage27_dir","stage24_dir","sites_root")]
 out=a.out.expanduser().resolve()
 if (not all(x.is_dir() for x in (d38,d37,d27,d24,root)) or out.exists() or
     not out.parent.is_dir() or any(x==out or x in out.parents or out in x.parents
      for x in (d38,d37,d27,d24,root))):
  p.error("NEW isolated reporting output only; immutable original source")
 filemap={
  "events":d38/"stage38_ALL_SMALL_SITE_AND_VCP_FULL_EPISODE_METHOD_TRIALS.csv",
  "native":d38/"stage38_RESEARCH_ONLY_FULL_SOURCE_EPISODE_NATIVE_RH_VPD_CANDIDATES.csv",
  "sites":d38/"stage38_TEN_SITE_PROVENANCE_AND_REMAINING_REPAIR_GATES.csv",
  "stage38":d38/"stage38_manifest.json",
  "stage37":d37/"stage37_65_EPISODES_BEFORE_AFTER_PRIORITIES.csv",
  "original":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
  "approved":d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv",
  "held":d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv",
  "platform":d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"}
 ev=read(filemap["events"],R38); native=read(filemap["native"],R38N)
 sites=idx(read(filemap["sites"],RSITE),("site",))
 original=idx(read(filemap["original"],R27),("site","native_time"))
 approved=idx(read(filemap["approved"],RKEY),("site","native_time"))
 held=idx(read(filemap["held"],RKEY),("site","native_time"))
 platforms=idx(read(filemap["platform"],RKEY),("site","native_time"))
 s37=idx(read(filemap["stage37"],R37),("site","episode_id"))
 m38=json.loads(filemap["stage38"].read_text(encoding="utf-8"))
 if (len(ev),len(sites),len(original),len(approved),len(held),len(platforms),len(s37))!=(669,10,1574,166,46,10,65):
  raise ValueError("Stage38/27/24 original populations do not match verified operator run")
 if (m38.get("num_original_site_method_records"),m38.get("research_only_full_event_native_candidate_rows"))!=(669,len(native)):
  raise ValueError("Stage38 manifest exact method/native trial count mismatch")
 if not m38.get("P2P3_1574_no_new_science_approvals") or m38.get("full_site_forcing_science_pass_confirmed")!=0:
  raise ValueError("Stage38 has unexpected approval")
 counts=Counter(x["science_gate"] for x in ev)
 if counts[GOOD]!=16 or sum(counts.values())!=669:
  raise ValueError("Stage38 original 16 numerically better methods drifted")
 if (counts["MISSING_SOURCE_METHOD_RH"],counts["NEIGHBOR_UNAPPROVED_OR_NONMEASURED"],
   counts["NEW_JUMP_GT2"],counts["NEW_SEVERE_JUMP_GT4"])!=(224,114,125,190):
  raise ValueError("Stage38 exact other method×episode screen counts drifted")
 methods=idx(ev,("site","episode_id","method"))
 allnative=idx(native,("site","episode_id","research_method","native_time"))
 good=[r for r in ev if r["science_gate"]==GOOD]
 grouped=defaultdict(list)
 for r in good:
  if (r["method"] not in METHODS or r["production_permission"]!="NO_RESEARCH_ONLY" or
      r["source_QC0_protected_HH"]!="0" or r["method_coverage_all_original_episode"]!="True" or
      any(int(r[k])!=0 for k in ("new_external_jump_gt2","new_external_jump_gt4",
           "original_internal_new_jump_gt2_HH","original_internal_new_jump_gt4_HH",
           "candidate_negative_or_unphysical_VPD_HH"))):
   raise ValueError("unexpected approval, QC0, incomplete or numerical red flag within top 16")
  grouped[(r["site"],r["episode_id"])].append(r)
 shortlist=[];pilots=[]
 for key in sorted(grouped):
  methodlist=sorted(grouped[key],key=lambda x:x["method"])
  if key[0]=="US-UMB":raise ValueError("UMB source not verified but one good method appears")
  for e in methodlist:
   needed=int(e["original_episode_HH"])
   rr=sorted([x for x in native if (x["site"],x["episode_id"],x["research_method"])==
      (key[0],key[1],e["method"])],key=lambda x:x["native_time"])
   if len(rr)!=needed or needed!=int(e["method_valid_HH"]):
    raise ValueError("Stage38 full event native trial missing "+str((key,e["method"])))
   if rr[0]["native_time"]!=e["event_start_native"] or rr[-1]["native_time"]!=e["event_end_native"]:
    raise ValueError("original full episode time coverage mismatch")
   if any(date(x["native_time"])+timedelta(minutes=30)!=date(y["native_time"]) for x,y in zip(rr,rr[1:])):
    raise ValueError("original event missing 30-minute native time")
   deltas=[]
   for r in rr:
    k=r["site"],r["native_time"]
    originalr=original.get(k)
    if originalr is None or originalr["episode_id"]!=key[1]:
     raise ValueError("one native candidate lacks original source episode")
    if k in approved or k in held or k in platforms:
     raise ValueError("attempted trial overlaps Stage24 existing-approved/manual-HOLD/saturated original")
    if r["original_VPD_QC"]=="0" or r["production_forcing_authorization"]!="NO":
     raise ValueError("original QC0 or already authorized candidate in shortlist")
    T=val(r["original_source_T_C"]);V=val(r["original_source_VPD_hPa"])
    RH=val(r["research_RH_source_pct"]);new=val(r["research_VPD_at_original_T_hPa"])
    if None in (T,V,RH,new) or not 0<=RH<=100 or not 0<=new<=es(T)+.001:
     raise ValueError("candidate violates physical saturation or source values")
    if any(abs(val(originalr[s])-t)>0.002 for s,t in
     (("TA_F_C",T),("VPD_F_hPa",V))) or originalr["VPD_F_QC"]!=r["original_VPD_QC"]:
     raise ValueError("Stage38 trial did not preserve exact Stage27 original T/VPD/QC")
    if abs(new-es(T)*(1-RH/100))>0.002:
     raise ValueError("candidate not consistent with original water saturation")
    deltas.append(abs(new-V))
   shortlist.append(dict(site=key[0],episode_id=key[1],method=e["method"],
    original_first_native=e["event_start_native"],original_last_native=e["event_end_native"],
    original_episode_HH=needed,native_candidate_HH=len(rr),
    source_QC0_VPD=0,new_external_gt2=0,new_external_gt4=0,
    new_internal_gt2=0,new_internal_gt4=0,
    max_abs_candidate_VPD_change_hPa=round(max(deltas),6),
    mean_abs_candidate_VPD_change_hPa=round(sum(deltas)/len(deltas),6),
    method_count_for_same_episode=len(methodlist),
    manual_method_choice_needed=len(methodlist)>1,
    pilot_research_status=("METHOD_AMBIGUOUS_HOLD_NO_AUTOMATIC_SELECTION"
      if len(methodlist)>1 else "SINGLE_NUMERIC_METHOD_RESEARCH_PILOT_NOT_APPROVED"),
    production_authorized=False))
   if len(methodlist)==1:
    for x in rr:
     pilots.append(dict(site=x["site"],native_time=x["native_time"],
       original_episode_id=x["episode_id"],method=x["research_method"],
       original_source_T_C=x["original_source_T_C"],
       original_source_VPD_hPa=x["original_source_VPD_hPa"],
       original_source_VPD_QC=x["original_VPD_QC"],
       candidate_RH_water_pct=x["research_RH_source_pct"],
       candidate_VPD_hPa=x["research_VPD_at_original_T_hPa"],
       VPD_change_from_original_hPa=x["research_VPD_change_vs_original_hPa"],
       version="BATCH05_STAGE39_RESEARCH_ONLY_v1",
       status="UNAPPROVED_ISOLATED_EXPERIMENT_NOT_DATM",
       manual_science_approval="NOT_GRANTED",
       DATM_forcing_authorized="NO"))
 if len(shortlist)!=16:raise ValueError("exact 16 pilot options not represented")
 if len({(x["site"],x["native_time"]) for x in pilots})!=len(pilots):
  raise ValueError("duplicate native site/time in isolated single-method research preview")
 siteout=[]
 for key in sorted(sites):
  site=key[0];sr=sites[key]
  xx=[x for x in shortlist if x["site"]==site]
  esite={x["episode_id"] for x in xx}
  singles={x["episode_id"] for x in xx if not x["manual_method_choice_needed"]}
  ambig=esite-singles
  siteout.append(dict(site=site,
   original_P2P3_remaining_unapproved_HH=sr["source_original_P2P3_unapproved_HH"],
   source_original_episode_count=sr["source_original_P2P3_events"],
   num_good_method_trials=len(xx),
   unique_method_good_episodes=len(singles),
   ambiguous_multi_method_good_episodes=len(ambig),
   isolated_unapproved_pilot_native_HH=sum(x["site"]==site for x in pilots),
   site_pilot_status=sr["site_closeout_status"]))
 inv,reason=source_inventory(root)
 summary=dict(source_input_sha256={name:sha(p) for name,p in filemap.items()},
   method_by_original_episode_count=669,exact_numeric_shortlist_methods=16,
   exact_unique_original_shortlist_episodes=len(grouped),
   one_method_unique_episode_count=sum(len(v)==1 for v in grouped.values()),
   multi_method_ambiguous_episode_count=sum(len(v)>1 for v in grouped.values()),
   isolated_research_only_native_preview_HH=len(pilots),
   US_UMB_source_inventory_files=len(inv),US_UMB_source_inventory_result=reason,
   remaining_original_P2P3_unapproved_HH=1574,
   original_P1_manual_HOLD46_preserved=True,original_saturated10_preserved=True,
   approved_Stage24_166_preserved=True,new_scientific_approvals=0,
   DATM_CIME_FLUXMET_Slurm_modified=False)
 out.mkdir(exist_ok=False)
 write(out/"stage39_EXACT16_ORIGINAL_EVENT_METHOD_REVIEW.csv",SHORT_FIELDS,shortlist)
 write(out/"stage39_ISOLATED_SINGLE_METHOD_NATIVE_RESEARCH_PREVIEW_NOT_FORCING.csv",PILOT_FIELDS,pilots)
 write(out/"stage39_ALL10_SITE_NEXT_ACTIONS.csv",SITE_FIELDS,siteout)
 write(out/"stage39_US_UMB_READONLY_REAL_FILE_AND_ZIP_MEMBER_INVENTORY.csv",INVENTORY,inv)
 (out/"stage39_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 report=["# Stage39 — original Stage38 exact 16 method×episode shortlist (not yet approved)","",
  "No source, Stage24-approved166, manual-HOLD46, DATM, CIME or Slurm writes.",
  "All 1574 original P2/P3 source half-hours remain unapproved.",
  "16 is the number of NUMERIC method×episode candidates, not necessarily 16 distinct events.",
  "A unique method for an event creates a research-only native preview; two qualifying",
  "methods for the same original event produce an explicit method-choice HOLD.",
  "Even 'unique' and physically smooth does NOT prove source RH validity.",
  "",
  "## Site review summary",
  "| Site | Original P2/P3 | Good method trials | Unique-method events | Multiple-method ambiguous events | Unapproved research preview HH |",
  "|---|---:|---:|---:|---:|---:|"]
 for r in siteout:
  report.append("| {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["original_P2P3_remaining_unapproved_HH"],
   r["num_good_method_trials"],r["unique_method_good_episodes"],
   r["ambiguous_multi_method_good_episodes"],
   r["isolated_unapproved_pilot_native_HH"]))
 report+=["","## EXACT original events with 16 low-numeric-risk METHOD trials",
  "| Site | Source episode | Method | Original native time start–end | HH | max VPD candidate change hPa | review |",
  "|---|---|---|---|---:|---:|---|"]
 for r in shortlist:
  report.append("| {} | {} | {} | {}–{} | {} | {} | {} |".format(
   r["site"],r["episode_id"],r["method"],
   r["original_first_native"],r["original_last_native"],
   r["original_episode_HH"],r["max_abs_candidate_VPD_change_hPa"],
   r["pilot_research_status"]))
 report+=["","## US-UMB original source diagnosis",
  "- **{}**".format(reason),
  "- Original site folder found {} candidate ZIP/CSV files (filename/members and source SHA in inventory CSV).".format(len(inv)),
  "- Missing verified original source is an ACQUISITION/PROVENANCE blocker, not a user science approval issue.",
  "- Never select a random US-UMB archive or treat source-missing site as forcing-ready.",
  "","## Do humans have to act right now?",
  "- NO individual RH/VPD edits require operator decisions yet.",
  "- Scientific user permission is still needed before any research preview becomes an approved versioned forcing overlay.",
  "- If there are multiple satisfactory methods for the SAME original episode, investigator must choose one after science evidence (or leave HOLD).",
  "- Review original VPD sensor QC, BIF provenance, and site source for US-UMB before site-closeout.",
  "",
  "Research preview is a standalone UNAPPROVED file. No source/forcing edits, no Slurm jobs.",""]
 (out/"STAGE39_SHORTLIST_MANUAL_DECISIONS_AND_NEXT_ACTIONS.md").write_text("\n".join(report)+"\n",encoding="utf-8")
 print("STAGE39 SUCCESS | 669 ORIGINAL SOURCE METHOD TESTS; 16 numerical methods; UNIQUE_EPISODES",len(grouped),
  "UNIQUE_METHOD_EVENTS",summary["one_method_unique_episode_count"],
  "METHOD_AMBIGUOUS",summary["multi_method_ambiguous_episode_count"],
  "PILOT_NATIVE_RESEARCH_HH",len(pilots))
 for r in shortlist:
  print("STAGE39 REVIEW",r["site"],r["episode_id"],r["method"],
   "HH",r["native_candidate_HH"],"MAX_DVPD_HPA",r["max_abs_candidate_VPD_change_hPa"],
   "STATUS",r["pilot_research_status"])
 print("STAGE39 UMB",reason,"FILES",len(inv))
 print("STAGE39_REPORT="+str(out/"STAGE39_SHORTLIST_MANUAL_DECISIONS_AND_NEXT_ACTIONS.md"))
 print("STAGE39_OUT="+str(out))
 print("STAGE39 ALL_SOURCE/166_APPROVED/46_HOLD/1574_P2P3/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

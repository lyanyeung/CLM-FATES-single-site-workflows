#!/usr/bin/env python3
"""Batch05 Stage36 | SCIENCE TRIAL ONLY, NEVER production forcing.

Select exactly 251 source-ERA / actually-downloaded ERA5-Land concordant,
small-temperature-difference Stage35 original P2/P3 half-hours. Read the
ORIGINAL authenticated AmeriFlux FLUXNET ZIPs for all original neighbour
half-hours, reconstruct source VPD and QC across boundaries, and write
a separate 251-row HYPOTHETICAL candidate overlay for investigator review.
No existing approved Stage24 overlay is modified or merged, no original
FLUXMET/DATM files changed, no HOLD released, no Slurm jobs submitted.
"""
import argparse,csv,hashlib,io,json,math,re,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SELECT="P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF"
ZIP_SHA={
 "US-Vcp":("2007-2025_v1.3_r1","3cae4d7e148dba9ac5e1850cbfb41c1cda80ff0420a352709be324b187162329"),
 "US-Wjs":("2007-2025_v1.3_r1","75c7132fe8695a61f32dd4ad64235e97dccc786fcea75eb09a37d4ac1ea9ccda"),
 "US-Vcm":("2007-2025_v1.3_r1","2f336f2ade57f39ec575b0f3e7186ba2a36e3242d3fa5212cac20d474f3e604c")}
REQ35={"site","native_time","original_source_population","source_event_or_episode",
 "original_TA_C","original_VPD_hPa","original_TA_QC","original_VPD_QC",
 "source_processed_ERA_RH_pct","fresh_ERA5Land_grid_RH_pct",
 "fresh_ERA5Land_grid_T_C","ERA5Land_minus_original_T_C",
 "tower_VPD_trial_keep_source_ERA_RH_hPa",
 "tower_VPD_trial_keep_fresh_ERA5Land_RH_hPa",
 "source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp","review_lane",
 "forcing_patch_authorized"}
REQ27={"site","native_time","episode_id","TA_F_C","VPD_F_hPa",
 "TA_F_QC","VPD_F_QC","human_science_decision"}
REQEP={"site","episode_id","unapproved_HH","original_native_start","original_native_end"}
REQ24={"site","native_time","modified_VPD_hPa"}
REQHOLD={"site","native_time"}
REQRAW={"TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"}
CANDIDATE_COLS=("site","native_time","episode_id",
 "original_source_FLUXMET_archive_SHA256","original_TA_C","original_VPD_hPa",
 "original_TA_QC","original_VPD_QC","proposed_TA_C_UNCHANGED",
 "hypothetical_RH_from_processed_source_ERA_pct",
 "hypothetical_VPD_preserve_processed_source_ERA_RH_hPa",
 "alternative_fresh_ERA5Land_RH_pct",
 "alternative_VPD_preserve_fresh_grid_RH_hPa",
 "source_ERA_fresh_grid_RH_diff_pp",
 "hypothetical_VPD_minus_original_VPD_hPa",
 "original_implied_RH_water_pct",
 "existing_QC0_VPD_sensor_record_protected",
 "original_relative_humidity_plausibility",
 "science_status","production_DATM_authorization")
EDGE_COLS=("site","episode_id","trial_native_time",
 "adjacent_side","adjacent_native_time","adjacent_original_TA_C",
 "adjacent_original_VPD_hPa","adjacent_original_TA_QC",
 "adjacent_original_VPD_QC","adjacent_implied_RH_water_pct",
 "adjacent_status","adjacent_current_selected_VPD_hPa",
 "trial_source_ERA_RH_VPD_hPa",
 "trial_vs_adjacent_selected_VPD_jump_hPa",
 "abs_trial_jump_gt2_hPa","abs_trial_jump_gt4_hPa",
 "neighbor_QC2_or_not_measured","neighbor_RH_below10pct_or_unphysical",
 "neighbor_is_unapproved_P2P3","boundary_science_state")
EVENT_COLS=("site","episode_id","original_episode_unapproved_HH",
 "original_episode_native_start","original_episode_native_end",
 "trial_selected_HH","partial_original_episode_not_fully_selected",
 "trial_QC0_VPD_HH","trial_original_implied_RH_below10pct_HH",
 "trial_abs_VPD_change_gt2hPa_HH",
 "trial_abs_VPD_change_gt4hPa_HH",
 "trial_non_trivial_external_RH_diff_gt5pp_HH",
 "boundary_transitions","boundary_jump_gt2hPa","boundary_jump_gt4hPa",
 "boundary_neighbor_QC2_or_unmeasured",
 "boundary_neighbor_extreme_or_unphysical_RH",
 "boundary_neighbor_still_unapproved_P2P3_HH",
 "science_screen_decision")
NEIGHBOR_WINDOW=30

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()
def n(s):
 try:
  v=float(s)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except(TypeError,ValueError):pass
 return None
def stamp(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("invalid original HH date "+str(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def fmt(d):return d.strftime("%Y%m%d%H%M")
def es(t):
 if t is None or not -80<=t<=60:raise ValueError("original air T outside saturation range")
 return 6.112*math.exp(17.67*t/(t+243.5))
def rh(T,V):
 if T is None or V is None:return None
 return 100*(1-V/es(T))
def read(path,required):
 if not path.is_file() or path.is_symlink():raise ValueError("original file absent/nonregular "+str(path))
 with path.open("r",newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f)
  if not required.issubset(r.fieldnames or []) or len(set(r.fieldnames or []))!=len(r.fieldnames or []):
   raise ValueError("source field schema mismatch "+str(path))
  z=list(r)
 if any(None in row or any(x is None for x in row.values()) for row in z):
  raise ValueError("malformed original source CSV "+str(path))
 return z
def keyed(rows,time="native_time"):
 d={}
 for r in rows:
  k=r["site"],r[time]
  if k in d:raise ValueError("duplicate original source time "+str(k))
  d[k]=r
 return d
def write(path,cols,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def original_zip_for_site(root,site):
 rel,expected=ZIP_SHA[site]
 p=root/site/"forcing"/"packages"/("AMF_"+site+"_FLUXNET_"+rel+".zip")
 if not p.is_file() or p.is_symlink() or sha(p)!=expected:
  raise ValueError("original AmeriFlux ZIP absent or source SHA changed "+str(p))
 return p,expected
def read_raw_neighbor_times(root,site,needed):
 archive,source_hash=original_zip_for_site(root,site)
 result={}
 with zipfile.ZipFile(archive) as z:
  matches=[i for i in z.infolist() if re.fullmatch(
   "AMF_"+re.escape(site)+r"_FLUXNET_FLUXMET_HH_.+[.]csv",
   Path(i.filename).name,re.I)]
  if len(matches)!=1:raise ValueError("not exact one original FLUXMET_HH in "+str(archive))
  info=matches[0]
  if info.file_size>900*1024*1024:raise ValueError("original source CSV unexpectedly large")
  with z.open(info) as h:
   table=csv.DictReader(io.TextIOWrapper(h,encoding="utf-8-sig",newline=""))
   if not REQRAW.issubset(table.fieldnames or []):
    raise ValueError("raw FLUXMET_HH missing original VPD or QC fields")
   for r in table:
    if None in r:raise ValueError("malformed FLUXMET_HH original source")
    t=r["TIMESTAMP_START"]
    if t in needed:
     if t in result:raise ValueError("duplicate native time in original source "+site+" "+t)
     result[t]=dict(site=site,native_time=t,T=n(r["TA_F"]),
        V=n(r["VPD_F"]),TA_QC=r["TA_F_QC"],VPD_QC=r["VPD_F_QC"])
 if result.keys()!=needed:raise ValueError("original FLUXMET missing candidate/neighbor native dates "+site+
   " missing="+str(sorted(needed-set(result))[:12]))
 return result,source_hash
def validate_inputs(d35,d27,d24):
 f35=d35/"stage35_429_NATIVE_TOWER_VPD_TWO_ERA_METHODS_REVIEW_ONLY.csv"
 f27=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 fep=d27/"stage27_ALL483_original_P2P3_episode_science_risk.csv"
 fa=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 fh=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 fp=d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"
 m35=json.loads((d35/"stage35_manifest.json").read_text())
 m24=json.loads((d24/"stage24_manifest.json").read_text())
 if (m35.get("trial_native_HH_count"),m35.get("trial_P2P3_HH_count"),
     m35.get("human_science_approvals_new"))!=(429,392,0):
  raise ValueError("Stage35 reported native source scientific population changed")
 if m35.get("review_lanes",{}).get(SELECT)!=251:
  raise ValueError("Stage35 source 251 candidate population changed")
 if (m24.get("total_approved_overlay_HH"),m24.get("total_original_P1_manual_HOLD"))!=(166,46):
  raise ValueError("original approved/HOLD science population changed")
 raw35=read(f35,REQ35);allp2=keyed(read(f27,REQ27))
 episodes={(r["site"],r["episode_id"]):r for r in read(fep,REQEP)}
 approved=keyed(read(fa,REQ24));held=keyed(read(fh,REQHOLD))
 platforms=keyed(read(fp,REQHOLD))
 if (len(raw35),len(allp2),len(episodes),len(approved),len(held),len(platforms))!=(429,1574,483,166,46,10):
  raise ValueError("original episode/source overlay count changed")
 selected=[x for x in raw35 if x["review_lane"]==SELECT]
 if len(selected)!=251 or any(x["original_source_population"]!="P2_P3_ORIGINAL_UNAPPROVED" for x in selected):
  raise ValueError("Stage35 source ERA screening lane is not 251 P2/P3 HH")
 for row in selected:
  k=row["site"],row["native_time"]
  if row["site"] not in ZIP_SHA or k not in allp2 or k in approved or k in held or k in platforms:
   raise ValueError("candidate conflicts with approved or original user-held source "+str(k))
  src=allp2[k]
  if (src["episode_id"]!=row["source_event_or_episode"]
     or (row["site"],src["episode_id"]) not in episodes
     or abs(n(src["TA_F_C"])-n(row["original_TA_C"]))>0.002
     or abs(n(src["VPD_F_hPa"])-n(row["original_VPD_hPa"]))>0.002):
   raise ValueError("original Stage27 source tower T/VPD/episode does not match Stage35")
  if src["TA_F_QC"]!=row["original_TA_QC"] or src["VPD_F_QC"]!=row["original_VPD_QC"]:
   raise ValueError("Stage27 original source QC changed")
  if row["forcing_patch_authorized"]!="NO_VERSIONED_RESEARCH_TRIAL_ONLY":
   raise ValueError("Stage35 trial candidate unexpectedly authorized for production forcing")
 return selected,allp2,episodes,approved,held,platforms,{
  "Stage35_429_research_VPD":sha(f35),"Stage35_manifest":sha(d35/"stage35_manifest.json"),
  "Stage27_1574_original_source":sha(f27),"Stage27_483_episodes":sha(fep),
  "Stage24_166_approved":sha(fa),"Stage24_46_manual_HOLD":sha(fh),
  "Stage24_10_suspect_RH_platform":sha(fp)}

def selftest():
 assert rh(-11.136,2.581)>1 and rh(-11.136,2.581)<2
 assert fmt(stamp("200805241500")+timedelta(minutes=30))=="200805241530"
 assert abs(es(-20)*(1-70/100)-(es(-20)*.3))<1e-9
 assert len(ZIP_SHA)==3
 print("STAGE36 SELF-TEST PASS | 251 exact trial cohort, raw ZIP boundary QC, 0 source/forcing writes")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage35-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage35_dir,a.stage27_dir,a.stage24_dir,a.out)):
  p.error("--stage35-dir --stage27-dir --stage24-dir --out required")
 d35,d27,d24,root=[v.expanduser().resolve() for v in
   (a.stage35_dir,a.stage27_dir,a.stage24_dir,a.sites_root)]
 out=a.out.expanduser().resolve()
 if (not all(d.is_dir() for d in (d35,d27,d24,root))
    or out.exists() or not out.parent.is_dir() or any(
     out==d or out in d.parents or d in out.parents for d in (d35,d27,d24,root))):
  p.error("Stage36 read only original folders, new disjoint output only")
 selected,allp2,episodes,approved,held,platforms,sources=validate_inputs(d35,d27,d24)
 cand={(x["site"],x["native_time"]):x for x in selected}
 need=defaultdict(set)
 for site,time in cand:
  d=stamp(time)
  for step in (-1,0,1):need[site].add(fmt(d+timedelta(minutes=step*NEIGHBOR_WINDOW)))
 native={}
 rawhash={}
 for site,required in sorted(need.items()):
  rows,digest=read_raw_neighbor_times(root,site,required)
  native.update({(site,t):v for t,v in rows.items()})
  rawhash[site]=digest
 candidates=[]
 for k,x in sorted(cand.items()):
  raw=native[k]
  original_T=n(x["original_TA_C"])
  original_V=n(x["original_VPD_hPa"])
  src_RH=n(x["source_processed_ERA_RH_pct"])
  rh_grid=n(x["fresh_ERA5Land_grid_RH_pct"])
  new_V=n(x["tower_VPD_trial_keep_source_ERA_RH_hPa"])
  new_ref=n(x["tower_VPD_trial_keep_fresh_ERA5Land_RH_hPa"])
  if None in (original_T,original_V,src_RH,rh_grid,new_V,new_ref):
   raise ValueError("selected Stage35 case has missing source or candidate data")
  if not (0<=src_RH<=100 and 0<=rh_grid<=100.5):
   raise ValueError("selected source ERA RH or downloaded ERA RH not physically bounded")
  if raw["T"] is None or raw["V"] is None or abs(raw["T"]-original_T)>0.002 or abs(raw["V"]-original_V)>0.002:
   raise ValueError("Original FLUXMET selected T/VPD differs from prior source audit "+str(k))
  if raw["TA_QC"]!=x["original_TA_QC"] or raw["VPD_QC"]!=x["original_VPD_QC"]:
   raise ValueError("Original FLUXMET QC differs from prior audit "+str(k))
  if abs(new_V-es(original_T)*(1-src_RH/100))>0.002:
   raise ValueError("Stage35 source ERA RH-to-tower VPD calculation changed")
  if abs(new_ref-es(original_T)*(1-rh_grid/100))>0.002:
   raise ValueError("Stage35 new reference RH-to-tower VPD calculation changed")
  if abs(src_RH-rh_grid)>10 or abs(n(x["ERA5Land_minus_original_T_C"]))>5 or abs(new_ref-original_V)>5:
   raise ValueError("Stage35 low-risk lane scientific criteria changed")
  original_rh=rh(original_T,original_V)
  measured=(raw["VPD_QC"]=="0")
  plausible=(original_rh is not None and 0<=original_rh<=100)
  candidates.append(dict(
   site=k[0],native_time=k[1],episode_id=x["source_event_or_episode"],
   original_source_FLUXMET_archive_SHA256=rawhash[k[0]],
   original_TA_C=original_T,original_VPD_hPa=original_V,
   original_TA_QC=raw["TA_QC"],original_VPD_QC=raw["VPD_QC"],
   proposed_TA_C_UNCHANGED=original_T,
   hypothetical_RH_from_processed_source_ERA_pct=round(src_RH,6),
   hypothetical_VPD_preserve_processed_source_ERA_RH_hPa=round(new_V,8),
   alternative_fresh_ERA5Land_RH_pct=round(rh_grid,6),
   alternative_VPD_preserve_fresh_grid_RH_hPa=round(new_ref,8),
   source_ERA_fresh_grid_RH_diff_pp=round(src_RH-rh_grid,6),
   hypothetical_VPD_minus_original_VPD_hPa=round(new_V-original_V,8),
   original_implied_RH_water_pct=round(original_rh,6) if original_rh is not None else "",
   existing_QC0_VPD_sensor_record_protected=measured,
   original_relative_humidity_plausibility=plausible,
   science_status="ISOLATED_SOURCE_ERA_RH_TRIAL_UNAPPROVED",
   production_DATM_authorization="NO"))
 testmap={(x["site"],x["native_time"]):x for x in candidates}
 edges=[]
 for k,c in sorted(testmap.items()):
  time=stamp(k[1])
  for side,sign in (("BEFORE",-1),("AFTER",1)):
   neigh=(k[0],fmt(time+timedelta(minutes=NEIGHBOR_WINDOW*sign)))
   orig=native[neigh]
   if neigh in testmap:
    neighbor_v=n(testmap[neigh]["hypothetical_VPD_preserve_processed_source_ERA_RH_hPa"])
    status="ADJACENT_SAME_TRIAL_CANDIDATE"
   elif neigh in approved:
    neighbor_v=n(approved[neigh]["modified_VPD_hPa"])
    status="ADJACENT_EXISTING_166_USER_APPROVED_OVERLAY"
   elif neigh in held:
    neighbor_v=orig["V"]
    status="ADJACENT_P1_MANUAL_HOLD_UNAPPROVED_USE_ORIGINAL_FOR_DIAGNOSTIC_ONLY"
   elif neigh in platforms:
    neighbor_v=orig["V"]
    status="ADJACENT_RH_SATURATION_PLATFORM_UNAPPROVED_DIAGNOSTIC"
   elif neigh in allp2:
    neighbor_v=orig["V"]
    status="ADJACENT_OTHER_P2P3_ORIGINAL_UNAPPROVED_DIAGNOSTIC"
   else:
    neighbor_v=orig["V"]
    status="ADJACENT_UNMODIFIED_SOURCE_ORIGINAL"
   a_v=n(c["hypothetical_VPD_preserve_processed_source_ERA_RH_hPa"])
   diff=(a_v-neighbor_v)*(-1 if sign==-1 else 1) if neighbor_v is not None else None
   neighbor_rh=rh(orig["T"],orig["V"])
   edges.append(dict(site=k[0],episode_id=c["episode_id"],
    trial_native_time=k[1],adjacent_side=side,adjacent_native_time=neigh[1],
    adjacent_original_TA_C=orig["T"] if orig["T"] is not None else "",
    adjacent_original_VPD_hPa=orig["V"] if orig["V"] is not None else "",
    adjacent_original_TA_QC=orig["TA_QC"],
    adjacent_original_VPD_QC=orig["VPD_QC"],
    adjacent_implied_RH_water_pct=round(neighbor_rh,6) if neighbor_rh is not None else "",
    adjacent_status=status,
    adjacent_current_selected_VPD_hPa=neighbor_v if neighbor_v is not None else "",
    trial_source_ERA_RH_VPD_hPa=a_v,
    trial_vs_adjacent_selected_VPD_jump_hPa=round(diff,8) if diff is not None else "",
    abs_trial_jump_gt2_hPa=abs(diff)>2 if diff is not None else "",
    abs_trial_jump_gt4_hPa=abs(diff)>4 if diff is not None else "",
    neighbor_QC2_or_not_measured=orig["VPD_QC"]!="0",
    neighbor_RH_below10pct_or_unphysical=neighbor_rh is None or not 10<=neighbor_rh<=100,
    neighbor_is_unapproved_P2P3=(neigh in allp2 and neigh not in testmap),
    boundary_science_state="TRIAL_CONTEXT_NOT_APPROVED"))
 if len(edges)!=502:raise ValueError("expected 2 neighbor comparisons per 251 candidate")
 grouped=defaultdict(list)
 egroup=defaultdict(list)
 for c in candidates:grouped[c["site"],c["episode_id"]].append(c)
 for e in edges:egroup[e["site"],e["episode_id"]].append(e)
 events=[]
 for k,cs in sorted(grouped.items()):
  epi=episodes[k];ne=egroup[k]
  outstanding=int(epi["unapproved_HH"])
  qc0=sum(c["existing_QC0_VPD_sensor_record_protected"] for c in cs)
  big_v2=sum(abs(n(c["hypothetical_VPD_minus_original_VPD_hPa"]))>2 for c in cs)
  big_v4=sum(abs(n(c["hypothetical_VPD_minus_original_VPD_hPa"]))>4 for c in cs)
  diff5=sum(abs(n(c["source_ERA_fresh_grid_RH_diff_pp"]))>5 for c in cs)
  # Screen only real external boundaries where adjacent HH does not belong to trial.
  external=[r for r in ne if r["adjacent_status"]!="ADJACENT_SAME_TRIAL_CANDIDATE"]
  fail2=sum(x["abs_trial_jump_gt2_hPa"] is True for x in external)
  fail4=sum(x["abs_trial_jump_gt4_hPa"] is True for x in external)
  riskqc=sum(x["neighbor_QC2_or_not_measured"] for x in external)
  riskrh=sum(x["neighbor_RH_below10pct_or_unphysical"] for x in external)
  riskp2=sum(x["neighbor_is_unapproved_P2P3"] for x in external)
  # No automatic science approval even for a numerically low-risk event.
  label=("QC0_ORIGINAL_PROTECTED_REVIEW" if qc0 else
   "BOUNDARY_OR_UNAPPROVED_NEIGHBOR_REVIEW" if fail2 or riskrh or riskp2 else
   "PARTIAL_EVENT_OR_SOURCE_QC_REVIEW" if len(cs)!=outstanding or riskqc else
   "LOW_SCREEN_RISK_ISOLATED_TRIAL_ONLY")
  events.append(dict(site=k[0],episode_id=k[1],
   original_episode_unapproved_HH=outstanding,
   original_episode_native_start=epi["original_native_start"],
   original_episode_native_end=epi["original_native_end"],
   trial_selected_HH=len(cs),
   partial_original_episode_not_fully_selected=len(cs)!=outstanding,
   trial_QC0_VPD_HH=qc0,
   trial_original_implied_RH_below10pct_HH=sum(c["original_implied_RH_water_pct"]!="" and n(c["original_implied_RH_water_pct"])<10 for c in cs),
   trial_abs_VPD_change_gt2hPa_HH=big_v2,
   trial_abs_VPD_change_gt4hPa_HH=big_v4,
   trial_non_trivial_external_RH_diff_gt5pp_HH=diff5,
   boundary_transitions=len(external),
   boundary_jump_gt2hPa=fail2,boundary_jump_gt4hPa=fail4,
   boundary_neighbor_QC2_or_unmeasured=riskqc,
   boundary_neighbor_extreme_or_unphysical_RH=riskrh,
   boundary_neighbor_still_unapproved_P2P3_HH=riskp2,
   science_screen_decision=label))
 manifest=dict(
  Stage35_source_SHA256=sources,
  original_verified_site_ZIP_SHA256=rawhash,
  native_candidate_trial_HH=len(candidates),
  source_matched_original_neighbor_comparisons=len(edges),
  original_episode_groups=len(events),
  original_P2P3_1574_unapproved_preserved=True,
  original_P1_46_manual_HOLD_untouched=True,
  original_10_sat_platform_unapproved=True,
  existing_Stage24_166_approved_unchanged=True,
  new_scientific_approvals=0,
  isolated_research_candidates_not_production_forcing=True,
  original_FLUXMET_ZIP_or_CSV_modified=False,
  original_DATM_CIME_Slurm_modified=False,
  method="Preserve processed-source ERA RH and original selected tower T; compare fresh externally fetched ERA5Land RH; original source ZIP boundary diagnostics",
  caveat="Source ERA and freshly fetched ERA5-Land are both reanalysis-related. Even numerically concordant RH is not independent in-situ verification; original BIF UTC_OFFSET_DATE_END absent.",
  episode_science_screen_counts=dict(Counter(r["science_screen_decision"] for r in events)))
 out.mkdir(exist_ok=False)
 write(out/"stage36_251_ISOLATED_TRIAL_ONLY_source_ERA_RH_at_original_T.csv",CANDIDATE_COLS,candidates)
 write(out/"stage36_502_ORIGINAL_ZIP_NATIVE_NEIGHBOR_VPD_QC_TRANSITIONS.csv",EDGE_COLS,edges)
 write(out/"stage36_ALL_EPISODE_RISK_AND_TRIAL_DECISION_MATRIX.csv",EVENT_COLS,events)
 (out/"stage36_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 md=["# Stage36 — actual source FLUXMET ZIP-boundary verification of 251 isolated RH/VPD research trials","",
  "**NO source or production DATM forcing patches. No scientific approvals.**",
  "251 original Stage35 low-screen-risk P2/P3 native half-hours only.",
  "Original AmeriFlux FLUXMET packages were SHA-verified and read without extraction or edits.",
  "Keep T tower unchanged; hypothetical VPD uses processed-source ERA RH, versus separately fetched gridded ERA5-Land RH.",
  "Source processed ERA and ERA5-Land reanalysis are NOT independent original-tower humidity observations.",
  "Original source QC0 VPD is protected; never assume low statistical risk authorizes modifying measured values.",
  "Every candidate compared to original neighboring half-hours from the original ZIP.",
  "Adjacent previously-approved overlay values are used for diagnostics only; adjacent",
  "unapproved P2/P3, original P1 HOLD and RH saturation are explicitly flagged.",
  "Original BIF UTC_OFFSET_DATE_END is still missing; no unvalidated production time shifts.",
  "","## Numerical trial screening"]
 for k,v in manifest["episode_science_screen_counts"].items():
  md.append("- **{}**: {} original episode groups".format(k,v))
 md+=["","## Site / original P2/P3 trial counts"]
 for site in sorted(rawhash):
  site_rows=[r for r in candidates if r["site"]==site]
  md.append("- {}: {} research-only native candidate HH".format(site,len(site_rows)))
 md+=["","## Reviewer action",
  "1. Inspect `stage36_ALL_EPISODE_RISK_AND_TRIAL_DECISION_MATRIX.csv` for the risk-screen categories, not individual 251 approvals.",
  "2. Inspect `stage36_502_ORIGINAL_ZIP_NATIVE_NEIGHBOR_VPD_QC_TRANSITIONS.csv` for true original-source boundaries and other unapproved neighboring anomalies.",
  "3. **Do not** feed `stage36_251_ISOLATED_TRIAL_ONLY_source_ERA_RH_at_original_T.csv` directly to DATM, models or an existing approved overlay. This is not a versioned approval.",
  "4. Original 46 P1 manually HELD (H01 etc.), 10 RH saturation platforms and other 1323 original P2/P3 remain unapproved.",
  "5. After reviewing event categories, investigator may explicitly authorize a separate versioned experiment overlay with Post-v5 physical and boundary QC, still preserving original source and Stage24-approved overlay.",
  "","**NO automatic science approval was made.**",""]
 (out/"STAGE36_ORIGINAL_FLUXMET_BOUNDARY_AND_TRIAL_SCIENCE_REPORT.md").write_text("\n".join(md)+"\n")
 print("STAGE36 SUCCESS | 251 isolated research-only candidate HH; original source ZIP SHA verified; 502 native ±30min comparisons")
 print("STAGE36 TRIAL_SITES",json.dumps(dict(Counter(x["site"] for x in candidates)),sort_keys=True))
 print("STAGE36 EPISODES",len(events),"SCREEN",json.dumps(manifest["episode_science_screen_counts"],sort_keys=True))
 print("STAGE36 ORIGINAL_QC0_VPD_PROTECTED",sum(c["existing_QC0_VPD_sensor_record_protected"] for c in candidates))
 print("STAGE36 EXTERNAL_BOUNDARY_GT2_HPA",sum(e["boundary_jump_gt2hPa"] for e in events),"GT4",sum(e["boundary_jump_gt4hPa"] for e in events))
 print("STAGE36_REPORT="+str(out/"STAGE36_ORIGINAL_FLUXMET_BOUNDARY_AND_TRIAL_SCIENCE_REPORT.md"))
 print("STAGE36_OUTPUT="+str(out))
 print("STAGE36 ALL_HOLDS/APPROVED166/ORIGINAL_FLUXMET/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

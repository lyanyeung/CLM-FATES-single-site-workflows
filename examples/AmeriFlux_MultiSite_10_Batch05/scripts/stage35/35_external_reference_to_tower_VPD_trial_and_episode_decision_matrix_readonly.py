#!/usr/bin/env python3
"""Batch05 Stage35: actual Stage34 429 native original anomalies/held/platform
against new ERA5-Land point meteorology, with exact Stage27 P2/P3 source joins.

Produces RESEARCH-ONLY physically bounded native-tower-temperature VPD
hypotheses using (a) existing processed-source ERA RH and (b) newly fetched
ERA5-Land grid RH. Groups 392 P2/P3 and 27 P1 HOLD + 10 saturation-platform
half-hours into SCIENCE REVIEW LANES by independent meteorological *source*
agreement and uncertainty. Reanalysis agreements are NOT independent field
observations or a forcing science approval. No existing 166 approved RH
overlay changes, NO 46 manual P1 holds cleared, NO 1574 P2/P3 approvals.
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path

TOTAL=429
CATEGORIES={"P1_MANUAL_HOLD":27,"RH_SATURATION_PLATFORM_UNAPPROVED":10,
            "P2_P3_ORIGINAL_UNAPPROVED":392}
TOWER_COLS={"site","native_time","candidate_UTC","source_population","source_episode_or_platform",
 "source_original_T_C","source_original_VPD_hPa","source_original_RH_pct","source_TA_QC",
 "source_VPD_QC","source_MDS_RH_pct","source_processed_ERA_RH_pct",
 "ERA5Land_reference_T_C","ERA5Land_reference_RH_water_pct",
 "ERA5Land_T_minus_source_T_C",
 "candidate_VPD_original_T_preserve_ref_RH_water_hPa",
 "candidate_VPD_original_T_preserve_ref_actual_e_hPa",
 "reference_closer_to_MDS_or_source_ERA","science_concern_flags",
 "CDS_request_id","science_permission"}
P2_COLS={"site","native_time","episode_id","review_lane","RH_ERA_pct","RH_MDS_pct",
 "TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC","risk_flags"}
P1_COLS={"site","native_time","hold_reason"}
PLATFORM_COLS={"site","native_time","platform"}
APPROVED_COLS={"site","native_time"}
NEIGH_COLS={"site","native_time","relative_to_H01",
 "source_original_T_C","source_original_VPD_hPa",
 "RH_implied_original_T_and_VPD_water_pct",
 "source_original_T_QC","source_original_VPD_QC",
 "source_selected_status"}
CSV_FIELDS=("site","native_time","original_source_population","source_event_or_episode",
 "original_TA_C","original_VPD_hPa","original_TA_QC","original_VPD_QC",
 "original_RH_pct","source_MDS_RH_pct","source_processed_ERA_RH_pct",
 "fresh_ERA5Land_grid_RH_pct","fresh_ERA5Land_grid_T_C",
 "ERA5Land_minus_original_T_C","CDS_request_id",
 "tower_VPD_trial_keep_source_ERA_RH_hPa",
 "tower_VPD_trial_keep_fresh_ERA5Land_RH_hPa",
 "tower_VPD_trial_keep_fresh_ERA5Land_actual_e_hPa",
 "source_ERA_RH_minus_fresh_ERA5Land_RH_pp",
 "MDS_RH_minus_fresh_ERA5Land_RH_pp",
 "source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp",
 "source_MDS_RH_vs_fresh_ERA5L_abs_diff_pp",
 "fresh_ERA5Land_RH_vs_MDS_ERA_source_closer",
 "tower_VPD_source_ERA_minus_fresh_grid_RH_trial_hPa",
 "tower_VPD_trial_fresh_RH_minus_original_VPD_hPa",
 "fresh_ERA5Land_grid_RH_transfer_vs_actual_e_hPa",
 "source_phase_or_time_conflict_flags",
 "review_lane","review_reason",
 "manual_science_approval","forcing_patch_authorized")
EP_FIELDS=("site","episode_id","matched_P2P3_native_HH",
 "source_ERA_grid_agreement_le10pp_HH",
 "source_ERA_grid_agreement_le5pp_HH",
 "MDS_grid_agreement_le10pp_HH",
 "reanalysis_ERA_closer_than_MDS_HH",
 "MDS_closer_than_processed_ERA_HH",
 "grid_tower_temperature_delta_gt5C_HH",
 "fresh_grid_RH_trial_vs_original_VPD_gt5hPa_HH",
 "source_ERA_vpd_trial_vs_fresh_grid_vpd_trial_gt2hPa_HH",
 "screen_lane_priority","science_decision")
SITE_FIELDS=("site","population","native_HH",
 "ERA_reference_missing_rh_or_T_HH","source_ERA_grid_RH_diff_abs_gt20pp_HH",
 "source_MDS_grid_RH_diff_abs_gt20pp_HH",
 "processed_ERA_matches_grid_le10pp_HH",
 "grid_T_tower_T_diff_gt5C_HH","first_native","last_native")
LANE_ORDER=("P1_HOLD_GRID_REFERENCE_REVIEW",
 "SUSPECT_SATURATED_RH_PLATFORM_REVIEW",
 "P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF",
 "P2P3_REANALYSIS_ERA_CONCORDANT_LARGE_T_OR_SOURCE_CHANGE",
 "P2P3_SOURCE_MDS_MORE_CONCORDANT_REVIEW",
 "P2P3_REANALYSIS_SOURCE_CONFLICT_OR_UNCERTAIN")

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()
def number(x):
 try:
  y=float(x)
  if math.isfinite(y) and y not in (-9999.,-6999.):return y
 except(ValueError,TypeError):pass
 return None
def es(T):
 if T is None or not -80<=T<=60:raise ValueError("unusable original tower air T")
 return 6.112*math.exp(17.67*T/(243.5+T))
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("source missing/nonregular "+str(p))
 with p.open("r",newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f)
  if not required.issubset(r.fieldnames or []) or len(set(r.fieldnames or []))!=len(r.fieldnames or []):
   raise ValueError("source CSV structure change "+str(p))
  rows=list(r)
 if any(None in x or any(v is None for v in x.values()) for x in rows):
  raise ValueError("malformed original source record")
 return rows
def ix(rows):
 d={}
 for r in rows:
  key=(r["site"],r["native_time"])
  if key in d:raise ValueError("native duplicate "+str(key))
  d[key]=r
 return d
def categorize(typ,Tdiff,originalV,vtrial,rh_era,rh_grid,rh_mds):
 if typ=="P1_MANUAL_HOLD":return "P1_HOLD_GRID_REFERENCE_REVIEW"
 if typ=="RH_SATURATION_PLATFORM_UNAPPROVED":
  return "SUSPECT_SATURATED_RH_PLATFORM_REVIEW"
 if rh_era is None or rh_grid is None:
  return "P2P3_REANALYSIS_SOURCE_CONFLICT_OR_UNCERTAIN"
 era_diff=abs(rh_era-rh_grid)
 if rh_mds is not None and abs(rh_mds-rh_grid)+5<era_diff:
  return "P2P3_SOURCE_MDS_MORE_CONCORDANT_REVIEW"
 if era_diff<=10:
  if abs(Tdiff)<=5 and abs(vtrial-originalV)<=5:
   return "P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF"
  return "P2P3_REANALYSIS_ERA_CONCORDANT_LARGE_T_OR_SOURCE_CHANGE"
 return "P2P3_REANALYSIS_SOURCE_CONFLICT_OR_UNCERTAIN"

def transform(r,p2):
 typ=r["source_population"]
 if typ not in CATEGORIES:raise ValueError("unexpected original science population")
 site,time=r["site"],r["native_time"]
 T=number(r["source_original_T_C"])
 originalV=number(r["source_original_VPD_hPa"])
 Tgrid=number(r["ERA5Land_reference_T_C"])
 rhgrid=number(r["ERA5Land_reference_RH_water_pct"])
 rh_era=number(r["source_processed_ERA_RH_pct"])
 rh_mds=number(r["source_MDS_RH_pct"])
 rh_orig=number(r["source_original_RH_pct"])
 if None in (T,originalV,Tgrid,rhgrid) or not 0<=rhgrid<=100.5:
  raise ValueError("source original/reference T, VPD and RH required "+str((site,time)))
 p2row=p2.get((site,time))
 if typ=="P2_P3_ORIGINAL_UNAPPROVED":
  if p2row is None or p2row["episode_id"]!=r["source_episode_or_platform"]:
   raise ValueError("Stage34 original episode unmatched with Stage27 "+str((site,time)))
  if abs(number(p2row["RH_ERA_pct"])-rh_era)>0.01:
   raise ValueError("Stage34 original processed source ERA vs Stage27 mismatch")
  if number(p2row["RH_MDS_pct"]) is not None and abs(number(p2row["RH_MDS_pct"])-rh_mds)>0.01:
   raise ValueError("Stage34 original MDS versus Stage27 source mismatch")
  if abs(number(p2row["TA_F_C"])-T)>0.002:
   raise ValueError("Stage34 original tower T and Stage27 native source mismatch")
 else:
  if p2row is not None:raise ValueError("P1 or platform intersects original P2P3 cohort")
 esT=es(T)
 v_era=esT*(1-rh_era/100) if rh_era is not None and 0<=rh_era<=100 else None
 v_grid=esT*(1-rhgrid/100)
 v_grid_e=number(r["candidate_VPD_original_T_preserve_ref_actual_e_hPa"])
 v_original_ref=number(r["candidate_VPD_original_T_preserve_ref_RH_water_hPa"])
 if v_grid_e is None or v_original_ref is None or abs(v_original_ref-v_grid)>0.002:
  raise ValueError("original Stage34 ERA5-Land VPD trial changed "+str((site,time)))
 Tdiff=Tgrid-T
 lane=categorize(typ,Tdiff,originalV,v_grid,rh_era,rhgrid,rh_mds)
 flags=[]
 if abs(Tdiff)>5:flags.append("FRESH_GRID_VS_TOWER_T_GT5C")
 if v_era is None:flags.append("INVALID_OR_MISSING_ORIGINAL_PROCESSED_SOURCE_ERA_RH")
 if abs(v_grid-originalV)>5:flags.append("FRESH_GRID_VPD_TRIAL_VS_ORIGINAL_GT5HPA")
 if v_era is not None and abs(v_era-v_grid)>2:flags.append("TOWER_VPD_SOURCE_ERA_VS_FRESH_GRID_RH_GT2HPA")
 if v_grid_e<0:flags.append("FRESH_GRID_ACTUAL_VAPOUR_PRESSURE_EXCEEDS_TOWER_WATER_SATURATION")
 if rh_mds is not None and abs(rh_mds-rhgrid)>20:flags.append("MDS_VS_FRESH_GRID_RH_GT20PP")
 if rh_era is not None and abs(rh_era-rhgrid)>20:flags.append("SOURCE_ERA_VS_FRESH_GRID_RH_GT20PP")
 if typ=="RH_SATURATION_PLATFORM_UNAPPROVED":
  if rh_orig is None or rh_orig<99:flags.append("SATURATION_ORIGINAL_SENSOR_PROVENANCE_UNCONFIRMED")
 if typ=="P1_MANUAL_HOLD":flags.append("MANUALLY_HELD_P1_NEVER_AUTOMATICALLY_RELEASE")
 reason={
  "P1_HOLD_GRID_REFERENCE_REVIEW":"External gridded RH supports event-level source recheck only, P1 investigator HOLD",
  "SUSPECT_SATURATED_RH_PLATFORM_REVIEW":"Original RH saturation platform sensor provenance and duration must be examined",
  "P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF":"Gridded reference RH and source processed ERA RH agree to 10pp; low T/VPD change screen ONLY",
  "P2P3_REANALYSIS_ERA_CONCORDANT_LARGE_T_OR_SOURCE_CHANGE":"Reanalysis-source RH agree, but tower T or original VPD change large",
  "P2P3_SOURCE_MDS_MORE_CONCORDANT_REVIEW":"Gridded RH closer to source MDS than processed source ERA by at least 5pp",
  "P2P3_REANALYSIS_SOURCE_CONFLICT_OR_UNCERTAIN":"Reanalysis RH, MDS, or processed source ERA unresolved; require event QC review"
 }[lane]
 return dict(site=site,native_time=time,original_source_population=typ,
  source_event_or_episode=r["source_episode_or_platform"],original_TA_C=T,
  original_VPD_hPa=originalV,original_TA_QC=r["source_TA_QC"],
  original_VPD_QC=r["source_VPD_QC"],
  original_RH_pct=rh_orig if rh_orig is not None else "",
  source_MDS_RH_pct=rh_mds if rh_mds is not None else "",
  source_processed_ERA_RH_pct=rh_era if rh_era is not None else "",
  fresh_ERA5Land_grid_RH_pct=rhgrid,
  fresh_ERA5Land_grid_T_C=Tgrid,
  ERA5Land_minus_original_T_C=round(Tdiff,6),
  CDS_request_id=r["CDS_request_id"],
  tower_VPD_trial_keep_source_ERA_RH_hPa=round(v_era,8) if v_era is not None else "",
  tower_VPD_trial_keep_fresh_ERA5Land_RH_hPa=round(v_grid,8),
  tower_VPD_trial_keep_fresh_ERA5Land_actual_e_hPa=round(v_grid_e,8),
  source_ERA_RH_minus_fresh_ERA5Land_RH_pp=round(rh_era-rhgrid,6) if rh_era is not None else "",
  MDS_RH_minus_fresh_ERA5Land_RH_pp=round(rh_mds-rhgrid,6) if rh_mds is not None else "",
  source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp=round(abs(rh_era-rhgrid),6) if rh_era is not None else "",
  source_MDS_RH_vs_fresh_ERA5L_abs_diff_pp=round(abs(rh_mds-rhgrid),6) if rh_mds is not None else "",
  fresh_ERA5Land_RH_vs_MDS_ERA_source_closer=r["reference_closer_to_MDS_or_source_ERA"],
  tower_VPD_source_ERA_minus_fresh_grid_RH_trial_hPa=round(v_era-v_grid,8) if v_era is not None else "",
  tower_VPD_trial_fresh_RH_minus_original_VPD_hPa=round(v_grid-originalV,8),
  fresh_ERA5Land_grid_RH_transfer_vs_actual_e_hPa=round(v_grid-v_grid_e,8),
  source_phase_or_time_conflict_flags=";".join(flags),
  review_lane=lane,review_reason=reason,
  manual_science_approval="PENDING_EXPLICIT_INVESTIGATOR_DECISION",
  forcing_patch_authorized="NO_VERSIONED_RESEARCH_TRIAL_ONLY")
def episode_rows(trials):
 grouped=defaultdict(list)
 for r in trials:
  if r["original_source_population"]=="P2_P3_ORIGINAL_UNAPPROVED":
   grouped[(r["site"],r["source_event_or_episode"])].append(r)
 out=[]
 for (site,eid),rr in sorted(grouped.items()):
  n_=lambda r,k:number(r[k])
  approx_era=sum(r["source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp"]!="" and n_(r,"source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp")<=10 for r in rr)
  close5=sum(r["source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp"]!="" and n_(r,"source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp")<=5 for r in rr)
  closeM=sum(r["source_MDS_RH_vs_fresh_ERA5L_abs_diff_pp"]!="" and n_(r,"source_MDS_RH_vs_fresh_ERA5L_abs_diff_pp")<=10 for r in rr)
  era_closer=sum(r["fresh_ERA5Land_RH_vs_MDS_ERA_source_closer"]=="PROCESSED_SOURCE_ERA_CLOSER" for r in rr)
  mds_closer=sum(r["fresh_ERA5Land_RH_vs_MDS_ERA_source_closer"]=="MDS_REFERENCE_CLOSER" for r in rr)
  tlarge=sum(abs(n_(r,"ERA5Land_minus_original_T_C"))>5 for r in rr)
  vlarge=sum(abs(n_(r,"tower_VPD_trial_fresh_RH_minus_original_VPD_hPa"))>5 for r in rr)
  methods=sum(r["tower_VPD_source_ERA_minus_fresh_grid_RH_trial_hPa"]!="" and abs(n_(r,"tower_VPD_source_ERA_minus_fresh_grid_RH_trial_hPa"))>2 for r in rr)
  lane=("CONCORDANT_SOURCE_ERA_TRIAL_EVENT_REVIEW" if approx_era==len(rr) and tlarge==0 and vlarge==0 and methods==0
       else "PARTIAL_CONFLICT_OR_TOWER_MISMATCH_EVENT_HOLD_REVIEW")
  out.append(dict(site=site,episode_id=eid,matched_P2P3_native_HH=len(rr),
   source_ERA_grid_agreement_le10pp_HH=approx_era,
   source_ERA_grid_agreement_le5pp_HH=close5,
   MDS_grid_agreement_le10pp_HH=closeM,
   reanalysis_ERA_closer_than_MDS_HH=era_closer,
   MDS_closer_than_processed_ERA_HH=mds_closer,
   grid_tower_temperature_delta_gt5C_HH=tlarge,
   fresh_grid_RH_trial_vs_original_VPD_gt5hPa_HH=vlarge,
   source_ERA_vpd_trial_vs_fresh_grid_vpd_trial_gt2hPa_HH=methods,
   screen_lane_priority=lane,
   science_decision="NOT_SCIENTIFICALLY_APPROVED_NO_FORCING_WRITE"))
 return sorted(out,key=lambda r:(r["site"],r["episode_id"]))
def write(p,fields,rows):
 with p.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise");w.writeheader();w.writerows(rows)
def selftest():
 assert categorize("P2_P3_ORIGINAL_UNAPPROVED",0,3,2.9,40,43,98)=="P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF"
 assert categorize("P2_P3_ORIGINAL_UNAPPROVED",7,3,2.9,40,43,98)=="P2P3_REANALYSIS_ERA_CONCORDANT_LARGE_T_OR_SOURCE_CHANGE"
 assert categorize("P2_P3_ORIGINAL_UNAPPROVED",0,3,2.9,40,70,73)=="P2P3_SOURCE_MDS_MORE_CONCORDANT_REVIEW"
 assert categorize("P1_MANUAL_HOLD",0,0,1,None,55,None)=="P1_HOLD_GRID_REFERENCE_REVIEW"
 assert es(-10)>es(-20)
 print("STAGE35 SELF-TEST PASS | actual Stage34 429 source classifications, source ERA vs fresh gridded RH VPD science trials, zero approvals")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage34-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--stage33-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(v is None for v in (a.stage34_dir,a.stage27_dir,a.stage24_dir,a.stage33_dir,a.out)):
  p.error("Need --stage34-dir --stage27-dir --stage24-dir --stage33-dir --out")
 d34,d27,d24,d33=[x.expanduser().resolve() for x in (a.stage34_dir,a.stage27_dir,a.stage24_dir,a.stage33_dir)]
 out=a.out.expanduser().resolve()
 if (not all(x.is_dir() for x in (d34,d27,d24,d33)) or out.exists() or not out.parent.is_dir()
     or any(out==d or out in d.parents or d in out.parents for d in (d34,d27,d24,d33))):
  p.error("Stage35 NEW directory required; source reports immutable")
 f34=d34/"stage34_ALL_MATCHED_EXTERNAL_ERA5LAND_REFERENCE_SCIENCE_REVIEW_ONLY.csv"
 f27=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 fhold=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 fplatform=d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"
 fapproved=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 fneigh=d33/"stage33_H01_original_3h_neighbor_RH_VPD_and_QC_audit.csv"
 meta34=json.loads((d34/"stage34_manifest.json").read_text())
 meta24=json.loads((d24/"stage24_manifest.json").read_text())
 if (meta34.get("downloaded_reference_joined_unique_native_HH"),
     meta34.get("P1_nonH01_HOLD_27_external_ref_matched"),
     meta34.get("P2P3_native_HH_with_external_reference"),
     meta34.get("new_scientific_repair_approvals"))!=(429,27,392,0):
  raise ValueError("Stage34 exact 429/27/392 science cohort changed")
 if (meta24.get("total_approved_overlay_HH"),meta24.get("total_original_P1_manual_HOLD"))!=(166,46):
  raise ValueError("Stage24 science counts changed")
 actual=ix(read(f34,TOWER_COLS))
 source27=ix(read(f27,P2_COLS))
 held=ix(read(fhold,P1_COLS))
 platform=ix(read(fplatform,PLATFORM_COLS))
 approved=ix(read(fapproved,APPROVED_COLS))
 neighbors=ix(read(fneigh,NEIGH_COLS))
 if (len(actual),len(source27),len(held),len(platform),len(approved))!=(429,1574,46,10,166):
  raise ValueError("original source cohorts changed")
 if set(actual)&set(approved):
  raise ValueError("Stage34 unapproved source intersects Stage24 previously approved overlay")
 cats=Counter(x["source_population"] for x in actual.values())
 if cats!=Counter(CATEGORIES):raise ValueError("Stage34 original population classes changed")
 for (site,time),row in actual.items():
  if row["source_population"]=="P1_MANUAL_HOLD" and (site,time) not in held:
   raise ValueError("non H01 P1 HOLD source not original user-held")
  if row["source_population"]=="RH_SATURATION_PLATFORM_UNAPPROVED" and (site,time) not in platform:
   raise ValueError("saturation record not original suspect platform")
 for v in ("200712152030","200712160630"):
  r=neighbors.get(("US-Vcm",v))
  if r is None or r["source_original_T_QC"]!="2" or r["source_original_VPD_QC"]!="2":
   raise ValueError("H01 two original QC2 neighbor evidence not preserved")
 trial=[transform(r,source27) for key,r in sorted(actual.items())]
 if Counter(t["review_lane"] for t in trial).total()!=429:raise ValueError("science trial classification missing")
 if any(t["forcing_patch_authorized"]!="NO_VERSIONED_RESEARCH_TRIAL_ONLY" for t in trial):
  raise ValueError("any source marked approved unexpectedly")
 episodes=episode_rows(trial)
 group=defaultdict(list)
 for r in trial:group[r["site"],r["original_source_population"]].append(r)
 stats=[]
 for (site,pop),rr in sorted(group.items()):
  stats.append(dict(site=site,population=pop,native_HH=len(rr),
   ERA_reference_missing_rh_or_T_HH=0,
   source_ERA_grid_RH_diff_abs_gt20pp_HH=sum(
    r["source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp"]!="" and number(r["source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp"])>20 for r in rr),
   source_MDS_grid_RH_diff_abs_gt20pp_HH=sum(
    r["source_MDS_RH_vs_fresh_ERA5L_abs_diff_pp"]!="" and number(r["source_MDS_RH_vs_fresh_ERA5L_abs_diff_pp"])>20 for r in rr),
   processed_ERA_matches_grid_le10pp_HH=sum(
    r["source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp"]!="" and number(r["source_ERA_RH_vs_fresh_ERA5L_abs_diff_pp"])<=10 for r in rr),
   grid_T_tower_T_diff_gt5C_HH=sum(abs(number(r["ERA5Land_minus_original_T_C"]))>5 for r in rr),
   first_native=min(r["native_time"] for r in rr),
   last_native=max(r["native_time"] for r in rr)))
 # H01 immediate neighbors should be visibly included as REVIEW, never approved.
 adjacent=[]
 for t in ("200712152030","200712160630"):
  r=neighbors["US-Vcm",t]
  adjacent.append(dict(site="US-Vcm",native_time=t,
   original_tower_T_C=r["source_original_T_C"],
   original_tower_VPD_hPa=r["source_original_VPD_hPa"],
   implied_native_RH_water_pct=r["RH_implied_original_T_and_VPD_water_pct"],
   original_TA_QC=r["source_original_T_QC"],
   original_VPD_QC=r["source_original_VPD_QC"],
   manual_decision="REVIEW_EXTENDING_H01_ONLY;NO_SOURCE_WRITE"))
 manifest=dict(source_sha256={
  "Stage34_429_exact_reference":sha(f34),"Stage34_manifest":sha(d34/"stage34_manifest.json"),
  "Stage27_1574_original":sha(f27),"Stage24_46_manual_hold":sha(fhold),
  "Stage24_166_approved":sha(fapproved),"Stage24_10_platform":sha(fplatform),
  "Stage33_original_H01_neighbors":sha(fneigh)},
  newly_downloaded_reanalysis_reference_samples_validated_by_stage34=10,
  actual_native_HH_with_external_reference=429,
  P1_nonH01_user_HOLD_review_only=27,
  P1_H01_previous_19_still_HOLD=True,
  P1_H01_original_neighbors_QC2_2_under_review=True,
  RH_platform_10_still_unapproved=True,
  original_P2P3_1574_science_unapproved=True,
  Stage24_original_166_approved_unchanged=True,
  trial_native_HH_count=429,
  trial_P2P3_HH_count=392,
  trial_P2P3_episode_count=len(episodes),
  review_lanes=dict(Counter(r["review_lane"] for r in trial)),
  BIF_original_UTC_OFFSET_DATE_END_missing=True,
  fresh_ERA5Land_not_in_situ_and_not_statistically_independent_of_source_reanalysis=True,
  human_science_approvals_new=0,
  any_original_source_or_DATM_or_Slurm_modified=False)
 out.mkdir(exist_ok=False)
 write(out/"stage35_429_NATIVE_TOWER_VPD_TWO_ERA_METHODS_REVIEW_ONLY.csv",CSV_FIELDS,trial)
 write(out/"stage35_REFERENCED_P2P3_ORIGINAL_EPISODE_DECISION_MATRIX.csv",EP_FIELDS,episodes)
 write(out/"stage35_ALL_SITE_SOURCE_CLASS_REVIEW_SUMMARY.csv",SITE_FIELDS,stats)
 write(out/"stage35_H01_TWO_SUSPECT_QC2_NEIGHBORS_NOT_APPROVED.csv",
  ("site","native_time","original_tower_T_C","original_tower_VPD_hPa",
   "implied_native_RH_water_pct","original_TA_QC","original_VPD_QC","manual_decision"),adjacent)
 (out/"stage35_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 doc=["# Stage35 — real downloaded ERA5-Land vs original source ERA/MDS: repair decision matrix",
  "","**No source science approval or forcing write. All original P1 46 HOLD and P2/P3 1574 unapproved.**",
  "This is the first review of *actual* 429 source-native matched half-hours as potential",
  "versioned overlay trial candidates, not a new approved RH/VPD forcing overlay.",
  "Source-processed ERA humidity and fresh ERA5-Land both originate from reanalysis-related",
  "systems; consistency is support, NOT independent in-situ validation.",
  "All original BIF timezone metadata lack DATE_END; tower/nearest-grid elevation",
  "differences, native half-hour averages vs UTC hourly time interpolants remain uncertainties.",
  "The source application may require water-based VPD; ice-based RH not silently substituted.",
  "Use fresh ERA5L RH-to-tower-T as a *trial*; preserving grid actual e is a DIFFERENT",
  "unapproved alternative. Physically unbounded source RH never becomes a production replacement.","",
  "## Read-only review lanes"]
 for k in LANE_ORDER:doc.append("- **{}**: {} original HH".format(k,manifest["review_lanes"].get(k,0)))
 doc+=["","## Seven site × population source summaries",
  "| Site | Original source | Matched HH | Fresh grid vs source ERA RH >20pp | Fresh grid vs MDS RH >20pp | Processed source ERA RH agrees <=10pp | Tower/grid T >5 C |",
  "|---|---|---:|---:|---:|---:|---:|"]
 for r in stats:
  doc.append("| {} | {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["population"],r["native_HH"],
   r["source_ERA_grid_RH_diff_abs_gt20pp_HH"],
   r["source_MDS_grid_RH_diff_abs_gt20pp_HH"],
   r["processed_ERA_matches_grid_le10pp_HH"],
   r["grid_T_tower_T_diff_gt5C_HH"]))
 doc+=["","## Event/episode findings",
  "- P1 H02/H03/H04/H05 **27 original HH** remain unchanged HOLD. Source processed ERA RH may be invalid, and grid RH is a research reference, not user-approved RH replacement.",
  "- RH saturation **10 original HH** remain unapproved. Stage34 gridded moisture is lower than original platforms in several cases; review sensor metadata and prolonged 100% RH explicitly.",
  "- P2/P3 stage34 covered **392/1574 original HH**, divided by event into **{}** original Stage27 episodes.".format(len(episodes)),
  "- Stage33 H01 source neighbor **2007-12-15 20:30 QC2 RH 1.513015%** and **2007-12-16 06:30 QC2 RH 3.973442%**: suspect even though old screening flagged false; **do not silently expand H01 repair**.",
  "- Event suitability cannot be decided by single-point RH agreement alone: source QC, source temperature provenance, contiguous physical VPD and native clock alignment must be validated.",
  "","## Next decision, in priority order",
  "1. Compare detailed source-ERA and fresh-grid tower-temperature VPD trials with original selected VPD; review records without large T mismatch first, but do NOT auto-approve them.",
  "2. Present compact event-scoped investigator options (not 392 individual approvals) for Vcp original 2008 and Wjs 2008 conflicts.",
  "3. Validate H02–H05 P1 and two saturation platforms separately from P2/P3 methods; do not automatically clear 46 held P1 records.",
  "4. Determine whether to extend H01 native time range to two QC2 neighbors based on source/reanalysis meteorology, independent station evidence where available, and sensor metadata.",
  "5. Once explicit user method authorization exists, create a NEW isolated forcing overlay trial, then run Post-v5 QC. Nothing in Stage35 authorizes this.",
  "","**NO original FLUXMET, existing Stage24 166, P1 HOLD 46, DATM, CIME, or Slurm changes.**",""]
 (out/"STAGE35_EVENT_METHOD_CHOICE_AND_REVIEW_SUMMARY.md").write_text("\n".join(doc)+"\n")
 print("STAGE35 SUCCESS | 429 original native HH; P1 HOLD 27; RH platforms 10; P2P3 392; science approvals 0")
 print("STAGE35 REVIEW_LANES",json.dumps(manifest["review_lanes"],sort_keys=True))
 for r in stats:
  print("STAGE35 SITE",r["site"],r["population"],"HH",r["native_HH"],
   "ERA_GRID_LE10PP",r["processed_ERA_matches_grid_le10pp_HH"],
   "SOURCE_ERA_GRID_DIFF_GT20",r["source_ERA_grid_RH_diff_abs_gt20pp_HH"],
   "MDS_GRID_DIFF_GT20",r["source_MDS_grid_RH_diff_abs_gt20pp_HH"])
 print("STAGE35 EPISODES",len(episodes))
 print("STAGE35_REPORT="+str(out/"STAGE35_EVENT_METHOD_CHOICE_AND_REVIEW_SUMMARY.md"))
 print("STAGE35_OUTPUT="+str(out))
 print("STAGE35 SOURCE/APPROVED166/HOLD46/P2P3_1574/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

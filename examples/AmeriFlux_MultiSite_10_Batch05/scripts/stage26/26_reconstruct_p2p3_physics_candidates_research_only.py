#!/usr/bin/env python3
"""Batch05 Stage26: 1,574 P2/P3 ORIGINAL anomalous native HH, scientifically
distinct source-RH, MDS-pair RH, processed ERA-pair RH and ERA vapor-pressure
shadow candidates. ALL CANDIDATES ARE RESEARCH ONLY, NEVER SCIENCE APPROVED.

Does not use independent ERA5/ERA5-Land data and never asserts source
processed TA_ERA/VPD_ERA are independently validated reanalysis. No source,
forcing, CIME or Slurm writes. A physically bounded RH/VPD is NOT proof that
the humidity or its scientific provenance is correct.

Separate preserving relative humidity versus preserving ERA specific actual
vapor pressure when selected tower T differs from original source ERA T.
Never combine unmodified VPD_ERA directly with non-ERA selected tower T.
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp",
       "US-WCr","US-Whs","US-Wjs","US-Wkg")
EVIDENCE={
 "UNRESOLVED_PHYSICS_SOURCE_PROVENANCE_INDEPENDENT_MET_REQUIRED":924,
 "SOURCE_ERA_QC2_PHYSICAL_SHADOW_VERIFY_REFERENCES_NOT_AUTO_APPROVED":607,
 "MDS_QC1_PHYSICAL_SHADOW_VERIFY_QC_AND_CLOCK_NOT_AUTO_APPROVED":38,
 "NATIVE_SOURCE_RH_PRESENT_VERIFY_RH_PROVENANCE_AND_TRANSITION":5,
}
NEED16={"site","time","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC",
 "original_RH_pct","F_pair_RH_pct","TA_MDS_C","VPD_MDS_hPa",
 "TA_MDS_QC","VPD_MDS_QC","MDS_pair_physical","MDS_pair_RH_pct",
 "TA_ERA_C","VPD_ERA_hPa","ERA_pair_physical","ERA_pair_RH_pct",
 "ERA_e_plus_F_T_physical","ERA_e_plus_F_T_RH_pct",
 "ERA_implied_e_hPa","source_pair_flag","science_status"}
NEED25={"site","native_time","episode_id","tier","source_VPD_QC",
 "source_TA_QC","next_evidence","automatic_replacement_allowed"}
FLAG25={"site","native_time","original_tier","current_source_anomaly_decision"}
OPTIONS=("ORIGINAL_RH_WITH_SELECTED_T","SOURCE_MDS_RH_WITH_SELECTED_T",
         "SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T",
         "SOURCE_ERA_IMPLIED_ACTUAL_VAPOR_PRESSURE_WITH_SELECTED_T")
DETAIL_COL=("site","native_time","episode_id","original_priority_tier",
 "original_TA_C","original_VPD_hPa","TA_QC","VPD_QC","original_source_RH_pct",
 "MDS_TA_C","MDS_VPD_hPa","MDS_TA_QC","MDS_VPD_QC","MDS_pair_is_physical",
 "source_ERA_TA_C","source_ERA_VPD_hPa","source_ERA_pair_is_physical",
 "delta_selected_T_minus_ERA_T_C","delta_selected_T_minus_MDS_T_C",
 "stage25_evidence_group","number_of_physically_bounded_options",
 "available_option_labels","evidence_subgroup","high_risk_T_difference_gt5C",
 "independent_weather_needed","final_science_status")
OPT_COL=("site","native_time","episode_id","option_name",
 "original_selected_TA_C","original_selected_VPD_hPa",
 "source_option_RH_pct","research_candidate_VPD_hPa",
 "candidate_minus_original_VPD_hPa",
 "source_T_used_to_derive_RH_C","original_TA_QC","original_VPD_QC",
 "source_option_T_QC","source_option_VPD_QC",
 "selected_T_minus_option_T_C",
 "source_category","scientific_caveat","approved_for_forcing")
SUBCOL=("site","evidence_subgroup","original_VPD_QC","count_HH",
 "count_distinct_original_episodes","total_options","T_diff_gt5_HH",
 "requires_independent_weather","status")
SITE_COL=("site","remaining_P2_P3_HH","with_original_RH_option",
 "with_MDS_RH_option","with_processed_ERA_RH_option",
 "with_ERA_actual_vapor_pressure_option","no_source_derived_physical_option",
 "T_minus_ERA_gt5C_HH","unique_original_episodes","independent_met_required_HH")

def val(s):
 try:
  x=float(s)
  if math.isfinite(x) and x not in (-9999.0,-6999.0):return x
 except (TypeError,ValueError):pass
 return None
def es(t):
 if t is None or not (-80<=t<=60):return None
 return 6.112*math.exp(17.67*t/(243.5+t))
def clock(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("malformed original native timestamp "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def checksum(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def records(p,required):
 if not p.is_file() or p.is_symlink():
  raise ValueError("missing original report "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  rr=csv.DictReader(f)
  if not required.issubset(rr.fieldnames or []) or len(set(rr.fieldnames or []))!=len(rr.fieldnames or []):
   raise ValueError("bad input report schema "+str(p))
  rows=list(rr)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed report row "+str(p))
 return rows
def indexed(rows,keytime):
 out={}
 for row in rows:
  k=row["site"],row[keytime]
  clock(k[1])
  if k in out:raise ValueError("duplicate site/native half-hour "+str(k))
  out[k]=row
 return out
def load(d16,d25,d24):
 f16=d16/"stage16_all_1750_source_pair_review.csv"
 f25=d25/"stage25_remaining_P2_P3_evidence_worklist.csv"
 fc=d25/"stage25_all1750_exact_tier_overlay_hold_crosswalk.csv"
 fa=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 m16=json.loads((d16/"stage16_summary.json").read_text())
 m25=json.loads((d25/"stage25_summary.json").read_text())
 m24=json.loads((d24/"stage24_manifest.json").read_text())
 if m16.get("events")!=1750 or m16.get("decision")!="HOLD_ALL_UNAPPROVED":
  raise ValueError("Stage16 original full source cohort changed")
 if m25.get("P2_P3_unapproved_worklist_HH")!=1574 or m25.get("original_anomaly_half_hours")!=1750:
  raise ValueError("Stage25 remaining P2/P3 exact worklist count changed")
 if m24.get("total_approved_overlay_HH")!=166 or m24.get("total_original_P1_manual_HOLD")!=46:
  raise ValueError("Stage24 approved/HOLD cohort mismatch")
 if m25["source_hashes"].get("original_stage16_source")!=checksum(f16) or m25["source_hashes"].get("approved_stage24_overlay")!=checksum(fa):
  raise ValueError("Stage16/Stage24 originals changed since Stage25")
 source=indexed(records(f16,NEED16),"time")
 work=indexed(records(f25,NEED25),"native_time")
 cross=indexed(records(fc,FLAG25),"native_time")
 approved=indexed(records(fa,{"site","native_time"}),"native_time")
 if tuple(map(len,(source,work,cross,approved)))!=(1750,1574,1750,166):
  raise ValueError("exact source/work/cross/approved count mismatch")
 if not set(work).issubset(source) or set(work)&set(approved):
  raise ValueError("worklist overlaps approved or outside original 1750")
 expected=Counter({"UNRESOLVED_PHYSICS_SOURCE_PROVENANCE_INDEPENDENT_MET_REQUIRED":924,
                   "SOURCE_ERA_QC2_PHYSICAL_SHADOW_VERIFY_REFERENCES_NOT_AUTO_APPROVED":607,
                   "MDS_QC1_PHYSICAL_SHADOW_VERIFY_QC_AND_CLOCK_NOT_AUTO_APPROVED":38,
                   "NATIVE_SOURCE_RH_PRESENT_VERIFY_RH_PROVENANCE_AND_TRANSITION":5})
 if Counter(r["next_evidence"] for r in work.values())!=expected:
  raise ValueError("Stage25 four science evidence populations changed")
 for k,r in work.items():
  src=source[k];crosswalk=cross[k]
  if not r["tier"].startswith(("P2_","P3_")) or crosswalk["original_tier"]!=r["tier"]:
   raise ValueError("original P2/P3 source tier changed "+str(k))
  if r["automatic_replacement_allowed"]!="NO" or crosswalk["current_source_anomaly_decision"]!="NOT_SCIENTIFICALLY_APPROVED":
   raise ValueError("unapproved science state changed "+str(k))
  if r["source_VPD_QC"]!=src["VPD_F_QC"] or r["source_TA_QC"]!=src["TA_F_QC"]:
   raise ValueError("original P2/P3 source QC changed "+str(k))
  if abs(val(r["original_TA_C"])-val(src["TA_F_C"]))>0.002 or abs(
     val(r["original_VPD_hPa"])-val(src["VPD_F_hPa"]))>0.002:
   raise ValueError("original P2/P3 source meteorology changed "+str(k))
 return source,work,cross,approved,{"stage16_full":checksum(f16),
         "stage25_remaining":checksum(f25),"stage25_crosswalk":checksum(fc),
         "stage24_approved":checksum(fa)}

def trial(r,name,T,sourceRH,sourceT,sourceTQC,sourceVQC):
 Tsv=es(T)
 if Tsv is None or sourceRH is None or not 0<=sourceRH<=100:return None
 v=Tsv*(1-sourceRH/100)
 if not -1e-10<=v<=Tsv+1e-10:raise ValueError("mathematical RH/VPD range false")
 label=("Original source RH is valid mathematically but native observation/sensor origin may need verification"
        if name==OPTIONS[0] else
        "MDS source RH reconstructed from internally paired MDS T,VPD; not independently measured"
        if name==OPTIONS[1] else
        "Processed source ERA RH has no independent source verification, especially if tower and ERA T disagree"
        if name==OPTIONS[2] else
        "Conserves processed ERA actual vapor pressure e_ERA, NOT same assumption as conserving source ERA RH; may diverge materially")
 return dict(
  site=r["site"],native_time=r["time"],episode_id="",
  option_name=name,original_selected_TA_C=r["TA_F_C"],
  original_selected_VPD_hPa=r["VPD_F_hPa"],
  source_option_RH_pct=round(sourceRH,9),
  research_candidate_VPD_hPa=round(v,10),
  candidate_minus_original_VPD_hPa=round(v-val(r["VPD_F_hPa"]),10),
  source_T_used_to_derive_RH_C=sourceT if sourceT is not None else "",
  original_TA_QC=r["TA_F_QC"],original_VPD_QC=r["VPD_F_QC"],
  source_option_T_QC=sourceTQC,source_option_VPD_QC=sourceVQC,
  selected_T_minus_option_T_C=(round(T-sourceT,6) if sourceT is not None else ""),
  source_category=name,scientific_caveat=label,approved_for_forcing="NO")
def variants(r):
 T=val(r["TA_F_C"]);V=val(r["VPD_F_hPa"])
 if es(T) is None or V is None:
  raise ValueError("original selected TA/VPD missing")
 nativeRH=val(r["original_RH_pct"])
 Tm=val(r["TA_MDS_C"]);Vm=val(r["VPD_MDS_hPa"])
 Te=val(r["TA_ERA_C"]);Ve=val(r["VPD_ERA_hPa"])
 mRH=val(r["MDS_pair_RH_pct"])
 eRH=val(r["ERA_pair_RH_pct"])
 ans=[]
 def add(name,rh,originT,tqc,vqc):
  z=trial(r,name,T,rh,originT,tqc,vqc)
  if z is not None:ans.append(z)
 # Proposals are independently tagged; no proposal itself authorizes forcing.
 if nativeRH is not None and 0<=nativeRH<=100:
  add(OPTIONS[0],nativeRH,None,"ORIGINAL_RH_SENSOR_PROVENANCE_UNVERIFIED","ORIGINAL_RH_SENSOR_PROVENANCE_UNVERIFIED")
 if r["MDS_pair_physical"]=="PHYSICAL":
  if None in (Tm,Vm,mRH) or es(Tm) is None:
   raise ValueError("Stage16 original MDS physically valid but data missing")
  if not 0<=mRH<=100 or abs(mRH-100*(1-Vm/es(Tm)))>0.25:
   raise ValueError("original Stage16 MDS source RH inconsistent")
  add(OPTIONS[1],mRH,Tm,r["TA_MDS_QC"],r["VPD_MDS_QC"])
 if r["ERA_pair_physical"]=="PHYSICAL":
  if None in (Te,Ve,eRH) or es(Te) is None:
   raise ValueError("original processed ERA physically valid but missing values")
  if not 0<=eRH<=100 or abs(eRH-100*(1-Ve/es(Te)))>0.25:
   raise ValueError("original Stage16 processed ERA source RH inconsistent")
  add(OPTIONS[2],eRH,Te,"ERA_SOURCE_PROCESSED","ERA_SOURCE_PROCESSED")
 if r["ERA_e_plus_F_T_physical"]=="PHYSICAL":
  era_e=val(r["ERA_implied_e_hPa"])
  if era_e is None or era_e<0 or era_e>es(T)+1e-7:
   raise ValueError("ERA implied e with selected T marked feasible but numerically invalid")
  rh=100*era_e/es(T)
  if not 0<=rh<=100+1e-7:raise ValueError("ERA implied e RH invalid")
  add(OPTIONS[3],min(100,rh),Te,"ERA_SOURCE_PROCESSED","ERA_SOURCE_PROCESSED")
 return ans

def pack(source,work):
 details=[];options=[];by_site=defaultdict(lambda:{
  "count":0,"episodes":set(),"native":0,"mds":0,"era":0,"era_e":0,
  "none":0,"gt5":0,"independent":0
 });subgroups=defaultdict(lambda:dict(count=0,episodes=set(),opts=0,tempgt5=0,needs=0))
 for key,row in sorted(work.items()):
  r=source[key]
  opts=variants(r)
  for o in opts:o["episode_id"]=row["episode_id"]
  options.extend(opts)
  found={x["option_name"] for x in opts}
  dtemp=(val(r["TA_F_C"])-val(r["TA_ERA_C"])
         if val(r["TA_F_C"]) is not None and val(r["TA_ERA_C"]) is not None else None)
  dm=(val(r["TA_F_C"])-val(r["TA_MDS_C"])
      if val(r["TA_F_C"]) is not None and val(r["TA_MDS_C"]) is not None else None)
  has_native=OPTIONS[0] in found
  has_mds=OPTIONS[1] in found
  has_era=OPTIONS[2] in found
  has_era_e=OPTIONS[3] in found
  # Distinguish physical candidate existence from true availability of
  # independently corroborated air humidity. All groups remain HOLD.
  if not opts: sub="NO_VALID_NATIVE_MDS_ERA_OR_ERA_E_OPTION"
  elif has_native:sub="NATIVE_ORIGINAL_RH_EXISTS_CHECK_SENSOR_PROVENANCE"
  elif has_mds and has_era:sub="DUAL_SOURCE_MDS_AND_ERA_RH_OPTIONS_DIFFERENCE_CHECK"
  elif has_mds:sub="ONLY_MDS_RH_SOURCE_OPTION_OR_ERA_E_SHADOW"
  elif has_era:sub="ONLY_PROCESSED_ERA_RH_SOURCE_OPTION_OR_ERA_E_SHADOW"
  else:sub="ONLY_ERA_E_WITH_SELECTED_T_SHADOW"
  need=not has_native and not has_mds and not has_era
  gt5=dtemp is not None and abs(dtemp)>5
  details.append(dict(
   site=key[0],native_time=key[1],episode_id=row["episode_id"],
   original_priority_tier=row["tier"],
   original_TA_C=r["TA_F_C"],original_VPD_hPa=r["VPD_F_hPa"],
   TA_QC=r["TA_F_QC"],VPD_QC=r["VPD_F_QC"],
   original_source_RH_pct=r["original_RH_pct"],
   MDS_TA_C=r["TA_MDS_C"],MDS_VPD_hPa=r["VPD_MDS_hPa"],
   MDS_TA_QC=r["TA_MDS_QC"],MDS_VPD_QC=r["VPD_MDS_QC"],
   MDS_pair_is_physical=r["MDS_pair_physical"],
   source_ERA_TA_C=r["TA_ERA_C"],source_ERA_VPD_hPa=r["VPD_ERA_hPa"],
   source_ERA_pair_is_physical=r["ERA_pair_physical"],
   delta_selected_T_minus_ERA_T_C=round(dtemp,5) if dtemp is not None else "",
   delta_selected_T_minus_MDS_T_C=round(dm,5) if dm is not None else "",
   stage25_evidence_group=row["next_evidence"],
   number_of_physically_bounded_options=len(opts),
   available_option_labels=";".join(x["option_name"] for x in opts),
   evidence_subgroup=sub,high_risk_T_difference_gt5C=gt5,
   independent_weather_needed="YES_TO_VALIDATE_BEFORE_FORCING",
   final_science_status="HOLD_RESEARCH_PROPOSALS_NOT_APPROVED"))
  ss=by_site[key[0]]
  ss["count"]+=1
  ss["episodes"].add(row["episode_id"])
  ss["native"]+=int(has_native)
  ss["mds"]+=int(has_mds)
  ss["era"]+=int(has_era)
  ss["era_e"]+=int(has_era_e)
  ss["none"]+=int(not opts)
  ss["gt5"]+=int(gt5)
  ss["independent"]+=int(need)
  g=(key[0],sub,r["VPD_F_QC"])
  sg=subgroups[g]
  sg["count"]+=1;sg["episodes"].add(row["episode_id"])
  sg["opts"]+=len(opts);sg["tempgt5"]+=int(gt5);sg["needs"]+=int(need)
 if len(details)!=1574:raise ValueError("P2/P3 science candidates population not 1574")
 st_rows=[]
 for site in SITES:
  c=by_site[site]
  st_rows.append(dict(site=site,remaining_P2_P3_HH=c["count"],
    with_original_RH_option=c["native"],
    with_MDS_RH_option=c["mds"],
    with_processed_ERA_RH_option=c["era"],
    with_ERA_actual_vapor_pressure_option=c["era_e"],
    no_source_derived_physical_option=c["none"],
    T_minus_ERA_gt5C_HH=c["gt5"],
    unique_original_episodes=len(c["episodes"]) if isinstance(c["episodes"],set) else 0,
    independent_met_required_HH=c["independent"]))
 groups=[]
 for (site,sub,q),g in sorted(subgroups.items()):
  groups.append(dict(site=site,evidence_subgroup=sub,original_VPD_QC=q,
    count_HH=g["count"],count_distinct_original_episodes=len(g["episodes"]),
    total_options=g["opts"],T_diff_gt5_HH=g["tempgt5"],
    requires_independent_weather=g["needs"],
    status="SCIENCE_HOLD_NOT_APPROVED"))
 return details,options,st_rows,groups
def write(path,fields,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert len(EVIDENCE)==4 and sum(EVIDENCE.values())==1574
 test={"site":"US-Z","time":"202601010000","TA_F_C":"10","VPD_F_hPa":"18",
       "TA_F_QC":"0","VPD_F_QC":"1","original_RH_pct":"-9999",
       "TA_MDS_C":"10","VPD_MDS_hPa":"4","TA_MDS_QC":"1",
       "VPD_MDS_QC":"1","MDS_pair_physical":"PHYSICAL",
       "MDS_pair_RH_pct":str(100*(1-4/es(10))),
       "TA_ERA_C":"8","VPD_ERA_hPa":"3","ERA_pair_physical":"PHYSICAL",
       "ERA_pair_RH_pct":str(100*(1-3/es(8))),
       "ERA_e_plus_F_T_physical":"PHYSICAL",
       "ERA_implied_e_hPa":str(es(8)-3)}
 opts=variants(test)
 assert len(opts)==3
 assert all(o["approved_for_forcing"]=="NO" and 0<=o["source_option_RH_pct"]<=100 for o in opts)
 assert abs(opts[1]["research_candidate_VPD_hPa"]-opts[2]["research_candidate_VPD_hPa"])>0.01
 print("STAGE26 SELF-TEST PASS | ERA RH vs ERA actual vapor pressure distinct, coherent MDS/ERA research candidates, NO science approvals")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage16-dir",type=Path)
 p.add_argument("--stage25-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(v is None for v in (a.stage16_dir,a.stage25_dir,a.stage24_dir,a.out)):
  p.error("Need --stage16-dir --stage25-dir --stage24-dir --out")
 srcdirs=[x.expanduser().resolve() for x in (a.stage16_dir,a.stage25_dir,a.stage24_dir)]
 dst=a.out.expanduser().resolve()
 if (not all(p.is_dir() for p in srcdirs) or dst.exists() or not dst.parent.is_dir()
     or any(dst==p or dst in p.parents or p in dst.parents for p in srcdirs)):
  p.error("report output must be a NEW directory disjoint from inputs")
 source,work,cross,approved,hashes=load(*srcdirs)
 details,options,sites,subgroups=pack(source,work)
 if sum(int(r["remaining_P2_P3_HH"]) for r in sites)!=1574:
  raise ValueError("10 site total not 1574")
 dst.mkdir(exist_ok=False)
 write(dst/"stage26_ALL_1574_P2P3_candidate_feasibility.csv",DETAIL_COL,details)
 write(dst/"stage26_RESEARCH_ONLY_source_RH_MDS_ERA_and_ERA_e_options.csv",OPT_COL,options)
 write(dst/"stage26_all10_sites_candidate_feasibility.csv",SITE_COL,sites)
 write(dst/"stage26_scientific_subgroups_by_site.csv",SUBCOL,subgroups)
 flags=Counter(x["evidence_subgroup"] for x in details)
 counts=Counter(x["option_name"] for x in options)
 met=Counter(x["stage25_evidence_group"] for x in details)
 report={"original_P2_P3_unapproved":1574,"stage24_approved_overlay_preserved":166,
         "manual_P1_HOLD_preserved":46,"science_approvals_new":0,
         "external_ERA5_Land_downloaded":False,
         "physical_source_candidates_are_not_independent_met":True,
         "source_RH_MDS_ERA_option_rows_total":len(options),
         "distinct_native_HH_with_any_candidate":sum(x["number_of_physically_bounded_options"]>0 for x in details),
         "no_valid_original_source_candidate":flags["NO_VALID_NATIVE_MDS_ERA_OR_ERA_E_OPTION"],
         "stage25_input_evidence":dict(met),
         "candidate_counts_not_mutually_exclusive":dict(counts),
         "mutually_exclusive_subgroups":dict(flags),
         "input_file_sha256":hashes,"FLUXMET_changed":False,
         "DATM_forcing_changed":False,"Slurm_submitted":False}
 (dst/"stage26_summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 md=["# Stage26 P2/P3 — 1,574 unresolved native anomalous HH",
     "","**RESEARCH OPTIONS ONLY. Zero automatic science approvals or forcing replacements.**",
     "Processed source ERA is not externally acquired ERA5-Land. All native time stamps remain",
     "unmapped to UTC. Native original QC0/1/2 must not be relabelled measured when reconstructing.",
     "",
     "## Mechanism/subgroup split (mutually exclusive)",
     ""]
 for k,n in flags.most_common():
  md.append("- **"+k+"**: "+str(n)+" anomalous HH")
 md+=["","## Distinct research option coverage (OVERLAPPING, not additive)", ""]
 for k,n in counts.most_common():
  md.append("- **"+k+"**: "+str(n)+" original HH")
 md+=["","## 10-site source physical candidate coverage","",
      "| Site | remaining HH | native RH | MDS | ERA RH | ERA e shadow | no option | ERA T differs >5°C |",
      "|---|---:|---:|---:|---:|---:|---:|---:|"]
 for r in sites:
  md.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["remaining_P2_P3_HH"],r["with_original_RH_option"],
   r["with_MDS_RH_option"],r["with_processed_ERA_RH_option"],
   r["with_ERA_actual_vapor_pressure_option"],
   r["no_source_derived_physical_option"],r["T_minus_ERA_gt5C_HH"]))
 md+=["","## Scientific decision gates",
      "1. No usable original-source physical candidate -> independent T, dewpoint/reference source required.",
      "2. MDS versus processed ERA source RH options disagree -> examine source QC, episodic context and sensor provenance.",
      "3. ERA RH conserved vs ERA vapor-pressure conserved are different temperature adjustment assumptions.",
      "4. Original RH physically valid -> verify provenance, especially if corresponding selected VPD is formula-invalid.",
      "5. Only after validated external references/UTC/site metadata should an investigator authorize a versioned actual forcing.",
      "6. 46 already-user-HOLD P1 and ten saturation-platform HH from Stage24 remain excluded.",""]
 (dst/"STAGE26_SCIENCE_DECISIONS_AND_CANDIDATES.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 print("STAGE26 SUCCESS | 1574 P2/P3 original native HH; zero forcing approvals")
 print("STAGE26 DISTINCT_SOURCE_OPTIONS",json.dumps(dict(counts),sort_keys=True))
 print("STAGE26 MUTUALLY_EXCLUSIVE_SUBGROUPS",json.dumps(dict(flags),sort_keys=True))
 print("STAGE26 SOURCE_HH_WITH_SOME_PHYSICAL_CANDIDATE",report["distinct_native_HH_with_any_candidate"],
       "NO_SOURCE_PHYSICAL_CANDIDATE",report["no_valid_original_source_candidate"])
 for r in sites:
  print("STAGE26 SITE",r["site"],"UNRESOLVED",r["remaining_P2_P3_HH"],
        "NATIVE",r["with_original_RH_option"],"MDS",r["with_MDS_RH_option"],
        "ERA_RH",r["with_processed_ERA_RH_option"],"ERA_e",r["with_ERA_actual_vapor_pressure_option"],
        "NONE",r["no_source_derived_physical_option"],"T_ERA_GT5",r["T_minus_ERA_gt5C_HH"])
 print("STAGE26_REVIEW="+str(dst/"STAGE26_SCIENCE_DECISIONS_AND_CANDIDATES.md"))
 print("STAGE26 ORIGINAL FLUXMET/APPROVED STAGE24/DATM/MODELS UNCHANGED; no Slurm")
if __name__=="__main__":
 main()

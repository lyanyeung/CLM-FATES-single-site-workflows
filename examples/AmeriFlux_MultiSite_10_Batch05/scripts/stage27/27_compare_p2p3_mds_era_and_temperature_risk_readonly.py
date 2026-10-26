#!/usr/bin/env python3
"""Batch05 Stage27: compare 1,574 original P2/P3 RH/VPD research options by native HH.

Evaluate source (MDS vs processed ERA) RH disagreement, reconstruction
magnitude and relative-humidity vs actual-vapor-pressure ERA assumptions.
Generate original-episode-level human review priority, small concordant
research-only shortlist, and external-validation queue. NO data scientifically
approved by this script. NO source/DATM/CIME/Slurm modifications.
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path

OPTS={
 "ORIGINAL_RH_WITH_SELECTED_T":"native",
 "SOURCE_MDS_RH_WITH_SELECTED_T":"mds",
 "SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T":"era",
 "SOURCE_ERA_IMPLIED_ACTUAL_VAPOR_PRESSURE_WITH_SELECTED_T":"era_e",
}
SOURCE_COLS={"site","native_time","episode_id","original_priority_tier","original_TA_C",
"original_VPD_hPa","TA_QC","VPD_QC","original_source_RH_pct",
"MDS_TA_C","MDS_VPD_hPa","MDS_TA_QC","MDS_VPD_QC",
"source_ERA_TA_C","source_ERA_VPD_hPa","delta_selected_T_minus_ERA_T_C",
"evidence_subgroup","final_science_status"}
OPTION_COLS={"site","native_time","episode_id","option_name","source_option_RH_pct",
"research_candidate_VPD_hPa","approved_for_forcing"}
SITE_NAMES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp",
"US-WCr","US-Whs","US-Wjs","US-Wkg")
HH_FIELDS=("site","native_time","episode_id","source_original_priority",
"TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC",
"RH_original_pct","RH_MDS_pct","RH_ERA_pct","RH_ERA_e_pct",
"delta_RH_MDS_minus_ERA_pp","delta_VPD_MDS_minus_ERA_hPa",
"delta_VPD_ERA_RH_vs_ERA_e_hPa","delta_VPD_ERA_candidate_minus_original_hPa",
"abs_selected_T_minus_ERA_T_C","MDS_TA_QC","MDS_VPD_QC",
"option_count","review_lane","risk_flags",
"human_science_decision")
EP_FIELDS=("site","episode_id","original_priority","unapproved_HH",
"original_native_start","original_native_end","dual_option_HH",
"dual_agrees_le5pp_HH","dual_disagrees_gt10pp_HH",
"dual_disagrees_gt20pp_HH","ERA_T_diff_gt5C_HH",
"ERA_RH_vs_ERA_e_candidate_VPD_gt2hPa_HH",
"ERA_candidate_delta_original_gt5hPa_HH","max_abs_MDS_ERA_RH_delta_pp",
"max_abs_selected_T_minus_ERA_T_C","review_priority_rank",
"scientific_status")
SITE_FIELDS=("site","original_P2P3_unapproved_HH","dual_agree_le5pp_HH",
"dual_disagree_gt10pp_HH","dual_disagree_gt20pp_HH",
"native_original_RH_HH","only_ERA_option_HH","Tdiff_gt5C_HH",
"ERA_RH_vs_ERA_e_VPD_gt2hPa_HH","ERA_candidate_delta_original_gt5hPa_HH",
"original_episodes")
LANES=("NATIVE_RH_PRESENT_PROVENANCE",
       "DUAL_AGREES_LE5PP_REVIEW",
       "DUAL_DISAGREES_5_TO20PP",
       "DUAL_CONFLICT_GT20PP",
       "ERA_ONLY_SOURCE_REFERENCE_REQUIRED")
def n(s):
 try:
  x=float(s)
  if math.isfinite(x) and x not in (-9999.,-6999.):return x
 except (ValueError,TypeError):pass
 return None
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path,required):
 if not path.is_file() or path.is_symlink():raise ValueError("missing original report "+str(path))
 with path.open(newline="",encoding="utf-8-sig") as h:
  rd=csv.DictReader(h)
  if not required.issubset(rd.fieldnames or []) or len(set(rd.fieldnames or []))!=len(rd.fieldnames or []):
   raise ValueError("source CSV columns missing/repeated "+str(path))
  rows=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed source CSV "+str(path))
 return rows
def idx(rows):
 out={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in out:raise ValueError("duplicate native source site/time "+str(k))
  out[k]=r
 return out
def load(d26,d25,d24):
 f26=d26/"stage26_ALL_1574_P2P3_candidate_feasibility.csv"
 fo=d26/"stage26_RESEARCH_ONLY_source_RH_MDS_ERA_and_ERA_e_options.csv"
 f25=d25/"stage25_remaining_P2_P3_evidence_worklist.csv"
 f24=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 h24=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 s26=json.loads((d26/"stage26_summary.json").read_text())
 s25=json.loads((d25/"stage25_summary.json").read_text())
 s24=json.loads((d24/"stage24_manifest.json").read_text())
 if (s26.get("original_P2_P3_unapproved"),s26.get("science_approvals_new"),
     s26.get("stage24_approved_overlay_preserved"),s26.get("manual_P1_HOLD_preserved"))!=(1574,0,166,46):
  raise ValueError("Stage26 exact no-science-approval source cohort has drifted")
 if s25.get("P2_P3_unapproved_worklist_HH")!=1574:
  raise ValueError("Stage25 source unapproved cohort changed")
 if s24.get("total_approved_overlay_HH")!=166:
  raise ValueError("Stage24 approved native overlay changed")
 if s26["input_file_sha256"].get("stage25_remaining")!=sha(f25) or s26["input_file_sha256"].get("stage24_approved")!=sha(f24):
  raise ValueError("Stage26 original input hash provenance no longer matches Stage25 or Stage24")
 details=idx(read(f26,SOURCE_COLS))
 opts=read(fo,OPTION_COLS)
 work=idx(read(f25,{"site","native_time","episode_id","tier","automatic_replacement_allowed"}))
 approved=idx(read(f24,{"site","native_time"}))
 held=idx(read(h24,{"site","native_time"}))
 if (len(details),len(work),len(approved),len(held))!=(1574,1574,166,46):
  raise ValueError("source population mismatch")
 if set(details)!=set(work) or set(details)&(set(approved)|set(held)):
  raise ValueError("Stage26 worklist includes previously approved or held native HH")
 if len(opts)!=3589:
  raise ValueError("expected 5 original + 551 MDS + 1574 ERA RH + 1459 ERA e options")
 grouped=defaultdict(dict)
 count=Counter()
 for r in opts:
  k=(r["site"],r["native_time"]); name=r["option_name"]
  if k not in details or name not in OPTS or r["approved_for_forcing"]!="NO":
   raise ValueError("research option outside original unapproved scope")
  if name in grouped[k]:raise ValueError("duplicate same scientific option for HH "+str(k))
  if r["episode_id"]!=work[k]["episode_id"]:
   raise ValueError("Stage26 source episode membership changed "+str(k))
  rh=n(r["source_option_RH_pct"]);v=n(r["research_candidate_VPD_hPa"])
  if rh is None or v is None or not (0<=rh<=100 and v>=0):
   raise ValueError("candidate not mathematically physical "+str(k))
  grouped[k][name]=(rh,v)
  count[name]+=1
 if count!=Counter(dict(zip(OPTS.keys(),[5,551,1574,1459]))):
  raise ValueError("unexpected source option composition")
 for k in details:
  if "SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T" not in grouped[k]:
   raise ValueError("missing universal processed-source ERA candidate "+str(k))
  if details[k]["episode_id"]!=work[k]["episode_id"]:
   raise ValueError("Stage26 original episode ID changed "+str(k))
  if not work[k]["tier"].startswith(("P2","P3")):
   raise ValueError("original P2/P3 tier changed")
  if work[k]["automatic_replacement_allowed"]!="NO" or details[k]["final_science_status"]!="HOLD_RESEARCH_PROPOSALS_NOT_APPROVED":
   raise ValueError("source science HOLD improperly overwritten")
 return details,grouped,{
  "stage26_detail":sha(f26),"stage26_options":sha(fo),
  "stage25_remaining":sha(f25),"stage24_166":sha(f24),"stage24_46_HOLD":sha(h24)
 }

def lane(options):
 native="ORIGINAL_RH_WITH_SELECTED_T" in options
 mds="SOURCE_MDS_RH_WITH_SELECTED_T" in options
 era="SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T" in options
 if not era:raise ValueError("processed original ERA candidate missing")
 if native:return "NATIVE_RH_PRESENT_PROVENANCE"
 if mds:
  delta=abs(options["SOURCE_MDS_RH_WITH_SELECTED_T"][0]-options["SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T"][0])
  if delta<=5:return "DUAL_AGREES_LE5PP_REVIEW"
  if delta<=20:return "DUAL_DISAGREES_5_TO20PP"
  return "DUAL_CONFLICT_GT20PP"
 return "ERA_ONLY_SOURCE_REFERENCE_REQUIRED"

def screen(details,opts):
 rows=[];site=defaultdict(Counter);episode=defaultdict(list)
 for k in sorted(details):
  r=details[k];o=opts[k]
  ec=site[k[0]]
  rc=o.get("ORIGINAL_RH_WITH_SELECTED_T")
  md=o.get("SOURCE_MDS_RH_WITH_SELECTED_T")
  er=o["SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T"]
  ee=o.get("SOURCE_ERA_IMPLIED_ACTUAL_VAPOR_PRESSURE_WITH_SELECTED_T")
  rh_delta=md[0]-er[0] if md else None
  v_delta=md[1]-er[1] if md else None
  v_era_e=er[1]-ee[1] if ee else None
  original=n(r["original_VPD_hPa"])
  tdiff=n(r["delta_selected_T_minus_ERA_T_C"])
  if original is None or tdiff is None:
   raise ValueError("expected original selected VPD and ERA T differ available "+str(k))
  evpd=er[1]-original
  cat=lane(o)
  flags=[]
  if abs(tdiff)>5:flags.append("ORIGINAL_T_MINUS_ERA_T_GT5C")
  if rh_delta is not None and abs(rh_delta)>10:flags.append("MDS_ERA_RH_DISAGREES_GT10PP")
  if rh_delta is not None and abs(rh_delta)>20:flags.append("MDS_ERA_RH_DISAGREES_GT20PP")
  if v_era_e is None:flags.append("ERA_E_WITH_ORIGINAL_T_NOT_PHYSICAL")
  elif abs(v_era_e)>2:flags.append("ERA_RH_VS_ERA_E_VPD_DIFF_GT2HPA")
  if abs(evpd)>5:flags.append("ERA_RH_CANDIDATE_CHANGES_VPD_GT5HPA")
  if abs(evpd)>10:flags.append("ERA_RH_CANDIDATE_CHANGES_VPD_GT10HPA")
  if rc:flags.append("NATIVE_ORIGINAL_RH_EXISTS_VERIFY_PROVENANCE")
  if not md:flags.append("NO_MDS_RH_CROSS_CHECK")
  row=dict(site=k[0],native_time=k[1],episode_id=r["episode_id"],
   source_original_priority=r["original_priority_tier"],
   TA_F_C=r["original_TA_C"],VPD_F_hPa=r["original_VPD_hPa"],
   TA_F_QC=r["TA_QC"],VPD_F_QC=r["VPD_QC"],
   RH_original_pct=rc[0] if rc else "",
   RH_MDS_pct=md[0] if md else "",
   RH_ERA_pct=er[0],
   RH_ERA_e_pct=ee[0] if ee else "",
   delta_RH_MDS_minus_ERA_pp=round(rh_delta,6) if rh_delta is not None else "",
   delta_VPD_MDS_minus_ERA_hPa=round(v_delta,7) if v_delta is not None else "",
   delta_VPD_ERA_RH_vs_ERA_e_hPa=round(v_era_e,7) if v_era_e is not None else "",
   delta_VPD_ERA_candidate_minus_original_hPa=round(evpd,7),
   abs_selected_T_minus_ERA_T_C=round(abs(tdiff),5),
   MDS_TA_QC=r["MDS_TA_QC"],MDS_VPD_QC=r["MDS_VPD_QC"],
   option_count=len(o),review_lane=cat,risk_flags=";".join(flags),
   human_science_decision="HOLD_NOT_APPROVED_EXTERNAL_DATA_OR_SOURCE_VALIDATION_REQUIRED")
  rows.append(row);episode[r["episode_id"]].append(row)
  ec["total"]+=1
  ec["episode_"+r["episode_id"]]=1
  ec[cat]+=1
  ec["native"]+=int(bool(rc))
  ec["tdiff"]+=int(abs(tdiff)>5)
  ec["e_differ_gt2"]+=int(v_era_e is not None and abs(v_era_e)>2)
  ec["era_vdiff_gt5"]+=int(abs(evpd)>5)
  ec["mds_disagree10"]+=int(rh_delta is not None and abs(rh_delta)>10)
  ec["mds_disagree20"]+=int(rh_delta is not None and abs(rh_delta)>20)
 if len(rows)!=1574:raise ValueError("Stage27 row count not original P2/P3")
 return rows,site,episode

def episodes(rows):
 result=[]
 for key,group in rows.items():
  a=group[0];s=a["site"]
  if any(r["site"]!=s for r in group):raise ValueError("episode spans different sites")
  med=[n(r["delta_RH_MDS_minus_ERA_pp"]) for r in group]
  med=[abs(x) for x in med if x is not None]
  tdiff=[n(r["abs_selected_T_minus_ERA_T_C"]) for r in group]
  num20=sum(x>20 for x in med);num10=sum(x>10 for x in med)
  tt=sum(x>5 for x in tdiff)
  ee=sum("ERA_RH_VS_ERA_E_VPD_DIFF_GT2HPA" in r["risk_flags"].split(";") for r in group)
  ev=sum("ERA_RH_CANDIDATE_CHANGES_VPD_GT5HPA" in r["risk_flags"].split(";") for r in group)
  dual=sum(bool(r["RH_MDS_pct"]!="") for r in group)
  agree=sum(n(r["delta_RH_MDS_minus_ERA_pp"]) is not None and abs(n(r["delta_RH_MDS_minus_ERA_pp"]))<=5 for r in group)
  # Priority based on science-risk information, not claim of bad data:
  # risk non-unique across HH, small episodes can still be important.
  score=(8*num20+4*num10+3*tt+2*ee+2*ev)
  result.append(dict(site=s,episode_id=key,
    original_priority=a["source_original_priority"],
    unapproved_HH=len(group),
    original_native_start=min(x["native_time"] for x in group),
    original_native_end=max(x["native_time"] for x in group),
    dual_option_HH=dual,dual_agrees_le5pp_HH=agree,
    dual_disagrees_gt10pp_HH=num10,dual_disagrees_gt20pp_HH=num20,
    ERA_T_diff_gt5C_HH=tt,
    ERA_RH_vs_ERA_e_candidate_VPD_gt2hPa_HH=ee,
    ERA_candidate_delta_original_gt5hPa_HH=ev,
    max_abs_MDS_ERA_RH_delta_pp=round(max(med),5) if med else "",
    max_abs_selected_T_minus_ERA_T_C=round(max(tdiff),5),
    review_priority_rank=score,
    scientific_status="NO_AUTOMATIC_APPROVAL"))
 return sorted(result,key=lambda x:(-x["review_priority_rank"],-x["unapproved_HH"],x["site"],x["original_native_start"]))
def site_summary(si):
 res=[]
 for name in SITE_NAMES:
  c=si[name]
  res.append(dict(site=name,original_P2P3_unapproved_HH=c["total"],
   dual_agree_le5pp_HH=c["DUAL_AGREES_LE5PP_REVIEW"],
   dual_disagree_gt10pp_HH=c["mds_disagree10"],
   dual_disagree_gt20pp_HH=c["mds_disagree20"],
   native_original_RH_HH=c["native"],
   only_ERA_option_HH=c["ERA_ONLY_SOURCE_REFERENCE_REQUIRED"],
   Tdiff_gt5C_HH=c["tdiff"],
   ERA_RH_vs_ERA_e_VPD_gt2hPa_HH=c["e_differ_gt2"],
   ERA_candidate_delta_original_gt5hPa_HH=c["era_vdiff_gt5"],
   original_episodes=sum(v for k,v in c.items() if str(k).startswith("episode_"))))
 return res
def write(path,cols,rows):
 with path.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
def selftest():
 a={ "SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T":(70,4),
     "SOURCE_MDS_RH_WITH_SELECTED_T":(73,3.7)}
 assert lane(a)=="DUAL_AGREES_LE5PP_REVIEW"
 a["SOURCE_MDS_RH_WITH_SELECTED_T"]=(55,5.5)
 assert lane(a)=="DUAL_DISAGREES_5_TO20PP"
 a["SOURCE_MDS_RH_WITH_SELECTED_T"]=(39,6.4)
 assert lane(a)=="DUAL_CONFLICT_GT20PP"
 del a["SOURCE_MDS_RH_WITH_SELECTED_T"]
 assert lane(a)=="ERA_ONLY_SOURCE_REFERENCE_REQUIRED"
 assert sum((5,551,1574,1459))==3589
 print("STAGE27 SELF-TEST PASS | four exact scientific review lanes, valid threshold boundaries, no auto approvals")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage26-dir",type=Path)
 p.add_argument("--stage25-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage26_dir,a.stage25_dir,a.stage24_dir,a.out)):
  p.error("requires --stage26-dir --stage25-dir --stage24-dir --out")
 ds=[x.expanduser().resolve() for x in (a.stage26_dir,a.stage25_dir,a.stage24_dir)]
 out=a.out.expanduser().resolve()
 if (not all(d.is_dir() for d in ds) or not out.parent.is_dir() or out.exists()
     or any(out==d or out in d.parents or d in out.parents for d in ds)):
  p.error("use existing source reports and a NEW separate output directory")
 details,options,hashes=load(*ds)
 rows,sites,episodes_grouped=screen(details,options)
 epi=episodes(episodes_grouped)
 site=site_summary(sites)
 total_episodes=len(epi)
 if total_episodes!=483 or sum(x["original_P2P3_unapproved_HH"] for x in site)!=1574:
  raise ValueError("Stage17 P2/P3 exact 483-episode cohort unexpected")
 lanes=Counter(r["review_lane"] for r in rows)
 if lanes["NATIVE_RH_PRESENT_PROVENANCE"]!=5 or sum(lanes.values())!=1574:
  raise ValueError("mutually-exclusive primary provenance partition changed")
 if (lanes["DUAL_AGREES_LE5PP_REVIEW"]+lanes["DUAL_DISAGREES_5_TO20PP"]+
     lanes["DUAL_CONFLICT_GT20PP"]!=546 or lanes["ERA_ONLY_SOURCE_REFERENCE_REQUIRED"]!=1023):
  raise ValueError("Stage26 original native/MDS/ERA overlap changed")
 # No report can turn physics and agreement into automatic source approval.
 summary=dict(source_P2P3_native_HH=1574,
  original_P2P3_episodes=total_episodes,
  P1_approved_unchanged=130,P1_HOLD_unchanged=46,
  Stage24_166_approved_unchanged=True,
  newly_approved_source_records=0,
  mutually_exclusive_review_lanes=dict(lanes),
  source_tower_minus_processed_ERA_T_gt5C=sum(x["Tdiff_gt5C_HH"] for x in site),
  ERA_RH_vs_ERA_e_candidate_VPD_diff_gt2hPa=sum(x["ERA_RH_vs_ERA_e_VPD_gt2hPa_HH"] for x in site),
  ERA_RH_candidate_vs_original_VPD_gt5hPa=sum(x["ERA_candidate_delta_original_gt5hPa_HH"] for x in site),
  input_SHA256=hashes,
  independent_reference_met_extracted=False,
  source_QC_and_native_clock_UTC_verified=False,
  FLUXMET_changed=False,DATM_forcing_written=False,Slurm_submitted=False)
 out.mkdir(exist_ok=False)
 write(out/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",HH_FIELDS,rows)
 write(out/"stage27_ALL483_original_P2P3_episode_science_risk.csv",EP_FIELDS,epi)
 write(out/"stage27_ALL10_site_science_conflict_status.csv",SITE_FIELDS,site)
 dual=[r for r in rows if r["review_lane"]=="DUAL_AGREES_LE5PP_REVIEW"]
 write(out/"stage27_DUAL_AGREEMENT_REVIEW_ONLY_NOT_APPROVED.csv",HH_FIELDS,dual)
 attention=[r for r in rows if r["risk_flags"] or r["review_lane"]=="ERA_ONLY_SOURCE_REFERENCE_REQUIRED"]
 write(out/"stage27_EXTERNAL_VALIDATION_AND_CONFLICT_QUEUE.csv",HH_FIELDS,attention)
 (out/"stage27_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 md=["# Batch05 Stage27 — P2/P3 source comparison and scientific conflict review",
     "","**ALL 1,574 original P2/P3 RH/VPD candidate records remain unapproved.**",
     "Source processed ERA (TA_ERA/VPD_ERA) is NOT independently downloaded ERA5-Land.",
     "MDS and ERA internally reconstructed RH agreement indicates only source concordance, not independent truth.",
     "Do not overwrite original source, the 166 user-approved native overlay rows,",
     "46 investigator HOLD rows, ten suspect RH plateaus, DATM, CIME or Slurm.","",
     "## Mutually exclusive review lanes"]
 for name in LANES:md.append("- **{}**: {} HH".format(name,lanes[name]))
 md+=["",
 "Risk thresholds in this report are screening values, **not scientific acceptance standards**:",
 "MDS-vs-source-ERA RH Δ≤5 percentage points: review concordance (not auto-approve);",
 "RH disagreement >10/>20 percentage points: conflict; selected-vs-ERA T Δ>5°C;",
 "source ERA RH-conserving vs ERA vapor-pressure-conserving VPD Δ>2 hPa;",
 "ERA-derived replacement VPD vs original >5 hPa.","",
 "## Overall additional quantitative flags",
 "- Selected minus source processed ERA temperature >5°C: **{} HH**".format(summary["source_tower_minus_processed_ERA_T_gt5C"]),
 "- ERA RH versus ERA actual vapor pressure assumption VPD gap >2 hPa: **{} HH**".format(summary["ERA_RH_vs_ERA_e_candidate_VPD_diff_gt2hPa"]),
 "- Source ERA RH candidate vs original VPD change >5 hPa: **{} HH**".format(summary["ERA_RH_candidate_vs_original_VPD_gt5hPa"]),
 "",
 "## Site-specific comparisons",
 "| Site | P2/P3 | MDS–ERA agreement ≤5 pp | MDS–ERA >10 pp | MDS–ERA >20 pp | ERA only | Tdiff >5°C | ERA assumptions VPD >2hPa |",
 "|---|---:|---:|---:|---:|---:|---:|---:|"]
 for r in site:
  md.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["original_P2P3_unapproved_HH"],r["dual_agree_le5pp_HH"],
   r["dual_disagree_gt10pp_HH"],r["dual_disagree_gt20pp_HH"],
   r["only_ERA_option_HH"],r["Tdiff_gt5C_HH"],
   r["ERA_RH_vs_ERA_e_VPD_gt2hPa_HH"]))
 md+=["","## Top 20 original P2/P3 episodes by exploratory risk flags",
 "| Site | Episode | HH | RH conflict >20 pp | Tower/ERA T >5°C | ERA assumption ΔVPD >2 hPa | Rank score |",
 "|---|---|---:|---:|---:|---:|---:|"]
 for r in epi[:20]:
  md.append("| {} | {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["episode_id"],r["unapproved_HH"],
   r["dual_disagrees_gt20pp_HH"],r["ERA_T_diff_gt5C_HH"],
   r["ERA_RH_vs_ERA_e_candidate_VPD_gt2hPa_HH"],r["review_priority_rank"]))
 md+=["","## Next scientific decisions",
 "1. Prioritize **US-Vcp, US-Wjs, US-Vcm**. Obtain independent weather reference, source native clock offset and field coordinates/elevation.",
 "2. Check MDS/ERA provenance and episodes with >20 percentage-point RH disagreement before selecting a replacement source.",
 "3. Where MDS and ERA agree, compare with independent station/reference and adjacent original source meteorology; agreement alone does not authorize replacement.",
 "4. Decide whether conserving processed ERA RH or its vapor pressure is suitable for a given temperature mismatch, not by numerical convenience.",
 "5. Preserve 46 P1 HOLD and ten near-saturated platform records; no full DATM forcing or production model submission until broader provenance QA is closed.",""]
 (out/"STAGE27_DECISION_BRIEF_AND_EPISODE_PRIORITIES.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 print("STAGE27 SUCCESS | P2/P3=1574 original HH, original episodes=483; no science approvals")
 print("STAGE27 REVIEW_LANES",json.dumps(dict(lanes),sort_keys=True))
 print("STAGE27 T_DIFF_GT5",summary["source_tower_minus_processed_ERA_T_gt5C"])
 print("STAGE27 ERA_RH_VS_ERA_E_DIFF_GT2",summary["ERA_RH_vs_ERA_e_candidate_VPD_diff_gt2hPa"])
 print("STAGE27 ERA_CANDIDATE_VPD_CHANGE_GT5",summary["ERA_RH_candidate_vs_original_VPD_gt5hPa"])
 for r in site:
  print("STAGE27 SITE",r["site"],"UNAPPROVED",r["original_P2P3_unapproved_HH"],
        "DUAL_AGREE_LE5",r["dual_agree_le5pp_HH"],
        "DUAL_CONFLICT_GT20",r["dual_disagree_gt20pp_HH"],
        "ONLY_ERA",r["only_ERA_option_HH"],"T_DIFF_GT5",r["Tdiff_gt5C_HH"])
 print("STAGE27_REVIEW="+str(out/"STAGE27_DECISION_BRIEF_AND_EPISODE_PRIORITIES.md"))
 print("STAGE27 SOURCE/APPROVED_OVERLAY/HOLD/DATM/SLURM UNCHANGED; zero new science approvals")
if __name__=="__main__":main()

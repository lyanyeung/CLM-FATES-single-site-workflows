#!/usr/bin/env python3
"""Batch05 Stage25: exact 1,750 native anomaly half-hours crossed with 166 approved
Stage24 RH/VPD overlay, 46 still-manual-HOLD, and original Stage17 522 episode tiers.

This is an evidence and bookkeeping report, NOT scientific auto-approval or DATM
forcing. Source already-processed ERA is NOT independent ERA5-Land. Exact source
clock remains native/unverified UTC conversion.

Reports:
 - all1750_exact_priority_and_disposition.csv
 - 522_original_episode_status_with_coverage.csv
 - remaining_P2_P3_by_science_evidence_priority.csv
 - site_status_summary.csv
 - manifest and human-readable next steps
All preexisting inputs, original FLUXMET, models, Slurm remain untouched.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta
SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
       "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
SRC={"site","time","TA_F_QC","VPD_F_QC","TA_F_C","VPD_F_hPa",
     "original_RH_pct","ERA_pair_physical","MDS_pair_physical",
     "ERA_e_plus_F_T_physical","F_pair_RH_pct","science_status"}
EPS={"episode_id","site","native_start","native_end","half_hours","priority_tier"}
APP={"site","native_time","source_TA_C","source_VPD_hPa","modified_VPD_hPa"}
HOLD={"site","native_time","hold_reason"}
PLATFORM={"site","native_time","platform"}
OUTCOL=("site","native_time","original_episode_id","original_tier",
 "VPD_F_QC","TA_F_QC","original_source_TA_C","original_source_VPD_hPa",
 "original_source_RH_pct","original_derived_RH_pct",
 "original_ERA_pair_physical","original_MDS_pair_physical",
 "original_ERA_e_with_selected_T_physical",
 "current_source_anomaly_decision","candidate_new_VPD_hPa",
 "next_evidence_group","explicit_science_approval")
EPCOL=("episode_id","site","tier","start_native","end_native",
       "original_flagged_HH","approved_overlay_flagged_HH",
       "manual_hold_flagged_HH","other_unresolved_flagged_HH",
       "unresolved_QC0_HH","unresolved_QC1_HH","unresolved_QC2_HH",
       "unresolved_ERA_nonphysical_HH","unresolved_MDS_nonphysical_HH",
       "unresolved_original_RH_present_HH",
       "science_gate")
SITE_COL=("site","original_anomalous_HH","approved_overlay_HH",
          "manual_hold_HH","unresolved_other_HH",
          "P1_original_HH","P2_original_HH","P3_original_HH",
          "P2_P3_remaining_HH")
def num(s):
 try:
  z=float(s)
  return z if math.isfinite(z) and z not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None
def clock(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("invalid native time "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def hh_range(a,b):
 aa=clock(a);bb=clock(b)
 if bb<aa:raise ValueError("episode end before start")
 minutes=int((bb-aa).total_seconds()//60)
 if minutes%30:raise ValueError("episode timestamp not aligned to HH")
 return [(aa+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
         for i in range(minutes//30+1)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(path,required):
 if not path.is_file() or path.is_symlink():raise ValueError("source CSV missing "+str(path))
 with path.open(newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f)
  cols=rd.fieldnames or []
  if not required.issubset(cols) or len(cols)!=len(set(cols)):
   raise ValueError("source CSV schema or duplicate header "+str(path))
  r=list(rd)
 if any(None in x or any(v is None for v in x.values()) for x in r):
  raise ValueError("source CSV malformed "+str(path))
 return r
def unique(rows,timefield):
 d={}
 for row in rows:
  k=(row["site"],row[timefield])
  clock(k[1])
  if k in d:raise ValueError("source site+time duplicates "+str(k))
  d[k]=row
 return d
def join_sources(d16,d17,d24):
 f16=d16/"stage16_all_1750_source_pair_review.csv"
 f17=d17/"stage17_episodes_evidence_requests.csv"
 f24=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 fh=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 fp=d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"
 m16=json.loads((d16/"stage16_summary.json").read_text())
 m17=json.loads((d17/"stage17_summary.json").read_text())
 m24=json.loads((d24/"stage24_manifest.json").read_text())
 if m16.get("events")!=1750 or m16.get("decision")!="HOLD_ALL_UNAPPROVED":
  raise ValueError("original Stage16 population changed")
 if m24.get("total_approved_overlay_HH")!=166 or m24.get("total_original_P1_manual_HOLD")!=46:
  raise ValueError("Stage24 approved/HOLD population changed")
 if m24.get("raw_original_FLUXMET_changed") is not False or m24.get("DATM_forcing_changed") is not False:
  raise ValueError("Stage24 original/forcing modification unexpectedly reported")
 src=unique(read(f16,SRC),"time")
 eps=read(f17,EPS)
 app=unique(read(f24,APP),"native_time")
 hold=unique(read(fh,HOLD),"native_time")
 plate=unique(read(fp,PLATFORM),"native_time")
 if tuple(map(len,(src,eps,app,hold,plate)))!=(1750,522,166,46,10):
  raise ValueError("exact source population 1750/522/166/46/10 failed")
 if set(app)&set(hold) or set(plate)&set(hold) or set(plate)&set(app):
  raise ValueError("approved/HOLD/platform source overlap")
 if not set(hold).issubset(src):
  raise ValueError("all 46 original P1 HOLD must be in source anomaly cohort")
 if any(s not in SITES for s,t in src):
  raise ValueError("unknown site in Stage16")
 # Episode exact coverage and per-site original tier mapping
 tier={}
 epi={}
 recorded_counts=Counter()
 for e in eps:
  a=e["native_start"];b=e["native_end"]
  t=e["priority_tier"]
  if t not in ("P1_MEASURED_OR_ERA_INVALID","P2_MIX_OR_LONG_EPISODE",
             "P3_CONTEXT_AND_INDEPENDENT_REFERENCE"):
   raise ValueError("unrecognized Stage17 priority tier "+str(t))
  covered=hh_range(a,b)
  if len(covered)!=int(e["half_hours"]):
   raise ValueError("Stage17 episode half-hours mismatch "+e["episode_id"])
  recorded_counts[t]+=1
  for stamp in covered:
   k=e["site"],stamp
   if k in tier or k not in src:raise ValueError("original episode source coverage duplicate/missing "+str(k))
   tier[k]=t;epi[k]=e["episode_id"]
 if len(tier)!=1750 or recorded_counts!=Counter({
   "P1_MEASURED_OR_ERA_INVALID":39,
   "P2_MIX_OR_LONG_EPISODE":89,
   "P3_CONTEXT_AND_INDEPENDENT_REFERENCE":394}):
  raise ValueError("Stage17 522 episode tier groups drift")
 p1={k for k in tier if tier[k].startswith("P1")}
 if len(p1)!=176 or len(p1 & set(app))!=130 or p1 & set(hold)!=set(hold):
  raise ValueError("Stage24 P1 original accounting no longer 130 approved + 46 hold")
 # Confirm every approved native half-hour is consistent with original Stage16
 for k in (set(app)&set(src)):
  old=src[k];new=app[k]
  if abs(num(old["TA_F_C"])-num(new["source_TA_C"]))>0.002 or abs(
       num(old["VPD_F_hPa"])-num(new["source_VPD_hPa"]))>0.002:
   raise ValueError("approved overlay source no longer matches the Stage16 original "+str(k))
 return src,eps,app,hold,plate,tier,epi,dict(
  original_stage16_source=sha(f16),original_stage17_episodes=sha(f17),
  approved_stage24_overlay=sha(f24),unchanged_manual_HOLD=sha(fh),
  unapproved_source_platforms=sha(fp))
def action(r):
 qc=r["VPD_F_QC"]
 raw=num(r["original_RH_pct"])
 if qc=="0":
  return "MEASURED_QC0_TOWER_SENSOR_AND_FORMULA_VALIDATION"
 if r["ERA_pair_physical"]=="NONPHYSICAL":
  return "ORIGINAL_SOURCE_ERA_PAIR_NONPHYSICAL_INDEPENDENT_WEATHER"
 if raw is not None and 0<=raw<=100:
  return "NATIVE_SOURCE_RH_PRESENT_VERIFY_RH_PROVENANCE_AND_TRANSITION"
 if qc=="1" and r["MDS_pair_physical"]=="PHYSICAL":
  return "MDS_QC1_PHYSICAL_SHADOW_VERIFY_QC_AND_CLOCK_NOT_AUTO_APPROVED"
 if qc=="2" and r["ERA_pair_physical"]=="PHYSICAL":
  return "SOURCE_ERA_QC2_PHYSICAL_SHADOW_VERIFY_REFERENCES_NOT_AUTO_APPROVED"
 return "UNRESOLVED_PHYSICS_SOURCE_PROVENANCE_INDEPENDENT_MET_REQUIRED"
def crosswalk(src,eps,app,hold,plate,tier,episode):
 joined=[]
 epcount=defaultdict(Counter)
 sitecount=defaultdict(Counter)
 work=[]
 for k,r in sorted(src.items()):
  tiername=tier[k];e=episode[k]
  if k in app:
   state="APPROVED_IN_STAGE24_VERSIONED_OVERLAY_ONLY"
   proposed=app[k]["modified_VPD_hPa"]
   follow="ALREADY_APPROVED_DO_NOT_DUPLICATE_ORIGINAL_VALUES"
  elif k in hold:
   state="EXPLICIT_MANUAL_HOLD_UNCHANGED"
   proposed=""
   follow="USER_MANUAL_HOLD_REQUIRE_EXTERNAL_EVIDENCE"
  else:
   state="NOT_SCIENTIFICALLY_APPROVED"
   proposed=""
   follow=action(r)
  if k in plate and state!="NOT_SCIENTIFICALLY_APPROVED":
   raise ValueError("saturation platform was accidentally approved")
  joined.append(dict(site=k[0],native_time=k[1],original_episode_id=e,
    original_tier=tiername,VPD_F_QC=r["VPD_F_QC"],
    TA_F_QC=r["TA_F_QC"],original_source_TA_C=r["TA_F_C"],
    original_source_VPD_hPa=r["VPD_F_hPa"],
    original_source_RH_pct=r["original_RH_pct"],
    original_derived_RH_pct=r["F_pair_RH_pct"],
    original_ERA_pair_physical=r["ERA_pair_physical"],
    original_MDS_pair_physical=r["MDS_pair_physical"],
    original_ERA_e_with_selected_T_physical=r["ERA_e_plus_F_T_physical"],
    current_source_anomaly_decision=state,
    candidate_new_VPD_hPa=proposed,next_evidence_group=follow,
    explicit_science_approval="OVERLAY_ONLY" if k in app else "NONE"))
  ec=epcount[e];sc=sitecount[k[0]]
  sc["total"]+=1;sc[tiername[:2]]+=1
  if k in app: ec["approved"]+=1;sc["approved"]+=1
  elif k in hold:ec["hold"]+=1;sc["hold"]+=1
  else:
   ec["other"]+=1;sc["other"]+=1
   ec["unresolved_QC"+r["VPD_F_QC"]]+=1
   ec["era_invalid"]+=int(r["ERA_pair_physical"]=="NONPHYSICAL")
   ec["mds_invalid"]+=int(r["MDS_pair_physical"]=="NONPHYSICAL")
   ec["native_RH_present"]+=int(num(r["original_RH_pct"]) is not None)
   if tiername.startswith("P2") or tiername.startswith("P3"):
    sc["P2P3_unresolved"]+=1
    work.append(dict(site=k[0],native_time=k[1],episode_id=e,
      tier=tiername,source_VPD_QC=r["VPD_F_QC"],source_TA_QC=r["TA_F_QC"],
      original_TA_C=r["TA_F_C"],original_VPD_hPa=r["VPD_F_hPa"],
      original_RH_pct=r["original_RH_pct"],
      original_ERA_pair_physical=r["ERA_pair_physical"],
      original_MDS_pair_physical=r["MDS_pair_physical"],
      next_evidence=follow,automatic_replacement_allowed="NO"))
 ep_rows=[]
 for ep in eps:
  key=ep["episode_id"];c=epcount[key]
  original=int(ep["half_hours"])
  if original!=c["approved"]+c["hold"]+c["other"]:
   raise ValueError("episode native timestamp partition unexpected "+key)
  ep_rows.append(dict(episode_id=key,site=ep["site"],tier=ep["priority_tier"],
     start_native=ep["native_start"],end_native=ep["native_end"],
     original_flagged_HH=original,
     approved_overlay_flagged_HH=c["approved"],
     manual_hold_flagged_HH=c["hold"],
     other_unresolved_flagged_HH=c["other"],
     unresolved_QC0_HH=c["unresolved_QC0"],
     unresolved_QC1_HH=c["unresolved_QC1"],
     unresolved_QC2_HH=c["unresolved_QC2"],
     unresolved_ERA_nonphysical_HH=c["era_invalid"],
     unresolved_MDS_nonphysical_HH=c["mds_invalid"],
     unresolved_original_RH_present_HH=c["native_RH_present"],
     science_gate="NONE" if c["other"]==0 and c["hold"]==0
                  else "HOLD_REQUIRES_SCIENTIFIC_EVIDENCE"))
 site_rows=[]
 for site in SITES:
  c=sitecount[site]
  site_rows.append(dict(site=site,original_anomalous_HH=c["total"],
   approved_overlay_HH=c["approved"],manual_hold_HH=c["hold"],
   unresolved_other_HH=c["other"],P1_original_HH=c["P1"],
   P2_original_HH=c["P2"],P3_original_HH=c["P3"],
   P2_P3_remaining_HH=c["P2P3_unresolved"]))
 if len(joined)!=1750 or len(ep_rows)!=522:
  raise ValueError("crosswalk output population mismatch")
 if sum(int(r["original_anomalous_HH"]) for r in site_rows)!=1750:
  raise ValueError("10-site total missing original half-hours")
 work.sort(key=lambda r:(r["tier"],r["next_evidence"],r["site"],r["native_time"]))
 return joined,ep_rows,site_rows,work
def write(path,cols,data):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(data)
def selftest():
 a=hh_range("202601010000","202601010100")
 assert a==["202601010000","202601010030","202601010100"]
 assert action(dict(VPD_F_QC="2",original_RH_pct="-9999",
                    ERA_pair_physical="NONPHYSICAL",
                    MDS_pair_physical="PHYSICAL")).startswith("ORIGINAL_SOURCE_ERA_PAIR_NONPHYSICAL")
 assert 39+89+394==522
 print("STAGE25 SELF-TEST PASS | exact source HH joins, episode tiers, P1 accounting, no auto approvals")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage16-dir",type=Path)
 p.add_argument("--stage17-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(v is None for v in (a.stage16_dir,a.stage17_dir,a.stage24_dir,a.out)):
  p.error("must provide --stage16-dir --stage17-dir --stage24-dir --out")
 paths=[v.expanduser().resolve() for v in (a.stage16_dir,a.stage17_dir,a.stage24_dir)]
 out=a.out.expanduser().resolve()
 if (not all(p.is_dir() for p in paths) or out.exists() or not out.parent.is_dir()
     or any(out==p or out in p.parents or p in out.parents for p in paths)):
  p.error("only write to a new disjoint Stage25 directory")
 src,eps,app,hold,plate,tier,episode,sha_inputs=join_sources(*paths)
 joined,epi,sites,work=crosswalk(src,eps,app,hold,plate,tier,episode)
 overlay_flagged=len(set(src)&set(app))
 manual_flagged=len(set(src)&set(hold))
 overlay_outside=len(set(app)-set(src))
 if manual_flagged!=46 or overlay_flagged+overlay_outside!=166:
  raise ValueError("current approved 166 / all manual 46 cohort mismatch")
 site_status=Counter(r["current_source_anomaly_decision"] for r in joined)
 if site_status["EXPLICIT_MANUAL_HOLD_UNCHANGED"]!=46:
  raise ValueError("explicit HOLD count changed")
 p2p3_total=sum(1 for k in src if not tier[k].startswith("P1"))
 if p2p3_total!=1574 or len(work)!=sum(
     r["current_source_anomaly_decision"]=="NOT_SCIENTIFICALLY_APPROVED" and
     not r["original_tier"].startswith("P1") for r in joined):
  raise ValueError("P2+P3 total/remaining mismatch")
 out.mkdir(exist_ok=False)
 write(out/"stage25_all1750_exact_tier_overlay_hold_crosswalk.csv",OUTCOL,joined)
 write(out/"stage25_all522_episode_overlay_status.csv",EPCOL,epi)
 keys=("site","native_time","episode_id","tier","source_VPD_QC",
       "source_TA_QC","original_TA_C","original_VPD_hPa",
       "original_RH_pct","original_ERA_pair_physical",
       "original_MDS_pair_physical","next_evidence","automatic_replacement_allowed")
 write(out/"stage25_remaining_P2_P3_evidence_worklist.csv",keys,work)
 write(out/"stage25_all10_site_progress.csv",SITE_COL,sites)
 counts=dict(
  original_anomaly_half_hours=1750,original_episodes=522,
  Stage24_overlay_all_HH=166,
  Stage24_overlay_flagged_HH=overlay_flagged,
  Stage24_overlay_outside_original_1750_screen_HH=overlay_outside,
  original_P1_flagged=176,
  original_P1_approved=130,original_P1_hold=46,
  P2_P3_original_HH=p2p3_total,
  P2_P3_unapproved_worklist_HH=len(work),
  P2_P3_already_in_approved_overlay_HH=p2p3_total-len(work),
  source_status=dict(site_status),source_hashes=sha_inputs,
  independent_ERA5_Land_downloaded=False,model_ready_forcing_generated=False,
  origin_FLUXMET_or_DATM_changed=False,Slurm_submitted=False,
  source_native_clock_UTC_alignment_verified=False)
 (out/"stage25_summary.json").write_text(json.dumps(counts,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 report=[
  "# Batch05 Stage25 full 1750 anomaly priority/approval crosswalk","",
  "This is an **exact join**, not new science approval. Original P2/P3 unapproved records",
  "must be addressed with source meteorological evidence rather than copying source ERA blindly.","",
  "Original 176 P1 = 130 approved overlay + 46 manual HOLD.",
  "Stage24 all approved=166, but some are transitions outside Stage16's 1750 original screen;",
  "thus coverage below is computed from exact site/time keys rather than subtracting 166 from 1750.","",
  "Stage16 1750 screen inside Stage24 overlay: **"+str(overlay_flagged)+"**.",
  "Stage24 overlay outside original 1750 screen: **"+str(overlay_outside)+"**.",
  "Original P2/P3 1574 HH: already in approved overlay **"+str(p2p3_total-len(work))+
    "**, still unapproved **"+str(len(work))+"**.","",
  "## Ten-site summary",
  "| Site | Original flagged | In approved overlay | Manual HOLD | Other unapproved | P2/P3 remaining |",
  "|---|---:|---:|---:|---:|---:|"]
 for r in sites:
  report.append("| {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["original_anomalous_HH"],r["approved_overlay_HH"],
   r["manual_hold_HH"],r["unresolved_other_HH"],r["P2_P3_remaining_HH"]))
 report+=["","## Remaining evidence groups (P2/P3 only)"]
 groups=Counter(r["next_evidence"] for r in work)
 for k,v in groups.most_common():
  report.append("- **{}**: {} native anomaly HH".format(k,v))
 report+=["","**No automatic original RH/VPD replacement is authorized by this report.**",
          "Separate original source QC, UTC/native time matching, independent weather ",
          "reference and final Post-v5 checks remain prerequisites before DATM. Reporting only."]
 (out/"STAGE25_PROGRESS_AND_QC_WORKLIST.md").write_text("\n".join(report)+"\n",encoding="utf-8")
 print("STAGE25 SUCCESS | 1750 original HH -> 522 original episodes; 166 approved overlay & 46 manual holds crosswalk")
 print("STAGE25 P1 176 = 130 approved + 46 manual HOLD")
 print("STAGE25 APPROVED_INSIDE_1750",overlay_flagged,
       "APPROVED_TRANSITIONS_OUTSIDE_1750",overlay_outside)
 print("STAGE25 P2_P3 ORIGINAL=1574 ALREADY_APPROVED_IN_OVERLAY",
       p2p3_total-len(work),"STILL_UNAPPROVED",len(work))
 for r in sites:
  print("STAGE25 SITE",r["site"],"P2P3_UNAPPROVED",r["P2_P3_remaining_HH"],
        "P1_HOLD",r["manual_hold_HH"])
 print("STAGE25_REVIEW="+str(out/"STAGE25_PROGRESS_AND_QC_WORKLIST.md"))
 print("NO original FLUXMET / QA / DATM forcing / CIME / Slurm writes")
if __name__=="__main__":main()

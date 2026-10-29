#!/usr/bin/env python3
"""Batch05 Stage63: EXACT original 1750 HH vs newest user-approved 204 HH,
with original P1 manual HOLD46, saturated RH platform HOLD10 and remaining
P2/P3 events. Audits ten-site site/native-time crosswalk, never subtracts
204 blindly from 1574. No original source/model/DATM/Slurm modifications.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp",
       "US-WCr","US-Whs","US-Wjs","US-Wkg")
SITES_SET=set(SITES)
INPUT25=("site","native_time","original_episode_id","original_tier",
         "VPD_F_QC","TA_F_QC","current_source_anomaly_decision")
SCHEMA=("site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct",
 "modified_TA_C","modified_RH_pct","modified_VPD_hPa",
 "delta_VPD_hPa","replacement_RH_provenance","new_VPD_derivation",
 "source_QC_provenance_only","overlay_status")
SITE_COLS=("site","original_P1_HH","original_P2P3_HH",
 "approved_204_overlay_all_HH","approved_204_inside_original_1750_HH",
 "approved_204_outside_original_1750_HH",
 "approved_P1_HH","approved_P2P3_HH","remaining_original_P2P3_HH",
 "remaining_original_P2P3_events","remaining_original_P1_HOLD_HH",
 "unapproved_original_RH_saturation_platform_HH",
 "remaining_original_flagged_HH_after_204",
 "original_P2P3_science_screen","full_forcing_approved")
REMAIN_COLS=("site","native_time","episode_id","original_tier",
 "TA_F_QC","VPD_F_QC","current_source_anomaly_decision",
 "latest_status","science_next_action")
EVENT_COLS=("site","episode_id","original_tier","original_P2P3_HH",
 "remaining_P2P3_HH","approved_P2P3_HH",
 "science_status")
EDGE_COLS=("site","native_time","platform","original_RH_pct","original_VPD_QC","review_status")
P1_COLS=("site","native_time","hold_reason","action","latest_status")

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()

def read(path,required):
 if not path.is_file() or path.is_symlink():
  raise ValueError("original science report not regular source "+str(path))
 with path.open("r",newline="",encoding="utf-8-sig") as f:
  rdr=csv.DictReader(f)
  head=rdr.fieldnames or []
  if not set(required).issubset(head) or len(set(head))!=len(head):
   raise ValueError("upstream source schema incomplete/duplicate "+str(path))
  data=list(rdr)
 if any(None in row or any(v is None for v in row.values()) for row in data):
  raise ValueError("malformed original science report "+str(path))
 return data

def key(row):
 return row["site"],row["native_time"]

def indexed(rows):
 d={}
 for r in rows:
  k=key(r)
  if k in d or k[0] not in SITES_SET or len(k[1])!=12 or not k[1].isdigit():
   raise ValueError("non-unique/malformed exact source site/native HH "+str(k))
  d[k]=r
 return d

def write(path,cols,rows):
 with path.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader()
  w.writerows(rows)

def selftest():
 assert len(SITES)==10 and len(set(SITES))==10
 assert 1750==176+1574
 assert 204==174+30
 assert 483==89+394
 assert sum([0,23,15,62,362,626,62,1,401,22])==1574
 print("STAGE63 SELF-TEST PASS | exact 10-site cohort, P1/P2P3 separately, 204 crosswalk, NO FORCING WRITE")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage25-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--stage62-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage25_dir,a.stage24_dir,a.stage62_dir,a.out)):
  p.error("need --stage25-dir --stage24-dir --stage62-dir and NEW --out")
 d25,d24,d62,out=(x.expanduser().resolve() for x in
                  (a.stage25_dir,a.stage24_dir,a.stage62_dir,a.out))
 if not all(x.is_dir() for x in (d25,d24,d62)) or not out.parent.is_dir() or out.exists():
  p.error("original report dirs must exist, new output dir required")
 if any(out==d or d in out.parents or out in d.parents for d in (d25,d24,d62)):
  p.error("refuse writing into any earlier report directory")
 f25=d25/"stage25_all1750_exact_tier_overlay_hold_crosswalk.csv"
 m25=d25/"stage25_summary.json"
 f24=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 h24=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 s24=d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"
 m24=d24/"stage24_manifest.json"
 f62=d62/"stage62_VERSIONED_204_APPROVED_RH_VPD_native_overlay.csv"
 m62=d62/"stage62_manifest.json"
 a25=json.loads(m25.read_text())
 a24=json.loads(m24.read_text())
 a62=json.loads(m62.read_text())
 old=read(f24,SCHEMA)
 approved=read(f62,SCHEMA)
 source=read(f25,INPUT25)
 hold=read(h24,("site","native_time","hold_reason","action"))
 platform=read(s24,("site","native_time","platform","original_RH_pct","original_VPD_QC","review_status"))
 if (len(source),len(approved),len(old),len(hold),len(platform))!=(1750,204,166,46,10):
  raise ValueError("upstream exact 1750/204/166/46/10 source cohort changed")
 if (a25.get("original_anomaly_half_hours")!=1750 or
     a25.get("original_P1_flagged")!=176 or
     a25.get("P2_P3_original_HH")!=1574 or
     a25.get("Stage24_overlay_all_HH")!=166 or
     a25.get("P2_P3_unapproved_worklist_HH")!=1574 or
     a24.get("total_approved_overlay_HH")!=166 or
     a24.get("total_original_P1_manual_HOLD")!=46 or
     a24.get("platforms_unapproved_records")!=10 or
     a24.get("output_sha256")!=sha(f24) or
     a24.get("manual_HOLD_46_source_sha256")!=sha(h24) or
     a62.get("total_versioned_approved_candidate_HH")!=204 or
     a62.get("newly_approved_2018_HH")!=30 or
     a62.get("existing_approved_174_HH_unchanged") is not True or
     a62.get("previous_174_approved_overlay_file_unchanged") is not True or
     a62.get("production_DATM_authorization") is not False or
     a62.get("output_sha256",{}).get(f62.name)!=sha(f62)):
  raise ValueError("original Stage24/25/62 population, manifest or SHA drift")
 original=indexed(source)
 o24=indexed(old)
 o62=indexed(approved)
 h=indexed(hold)
 plat=indexed(platform)
 if not set(o24).issubset(o62) or any(o24[k]!=o62[k] for k in o24):
  raise ValueError("204 overlay changed original 166 exact approved records")
 if (set(o62)&set(h)) or (set(o62)&set(plat)) or (set(h)&set(plat)):
  raise ValueError("old P1 HOLD or original RH platform illegally approved")
 if sum(r["original_tier"].startswith("P1") for r in source)!=176 or sum(
    not r["original_tier"].startswith("P1") for r in source)!=1574:
  raise ValueError("original 1750 science tier exact composition drift")
 if any(not original[k]["original_tier"].startswith("P1") for k in h):
  raise ValueError("P1 manual HOLD not in original P1 source")
 # Original P1 exactly 130 approved + 46 still unapproved.
 p1=set(k for k,r in original.items() if r["original_tier"].startswith("P1"))
 if len(p1 & set(o62))!=130 or len(p1 & set(h))!=46 or p1!=((p1&set(o62))|(p1&set(h))):
  raise ValueError("P1 source 130 approved + 46 manual HOLD exact contract drift")
 p23=set(original)-p1
 if sum(x["original_tier"].startswith("P2") for x in source)+sum(
    x["original_tier"].startswith("P3") for x in source)!=1574:
  raise ValueError("original P2/P3 source tier labels differ from expected")
 latest=p23-set(o62)
 if len(latest)+len(p23&set(o62))!=1574:
  raise ValueError("P2/P3 remaining not conserved after exact join")
 if len(set(o62)-set(o24))!=38:
  raise ValueError("new eight plus thirty versioned approvals not conserved")
 if sum(r["site"]=="US-Wjs" and r["native_time"]>="201803111930" and
        r["native_time"]<="201803121000" for r in approved)!=30:
  raise ValueError("explicit Wjs2018 30HH not retained in latest overlay")
 # Group per actual original event, not per timestamp and not Stage48 Track A/B counts.
 grouped=defaultdict(list)
 for k in p23:
  r=original[k]
  eid=r["original_episode_id"]
  if not eid:
   raise ValueError("original P2/P3 missing exact episode identity")
  grouped[(k[0],eid)].append(k)
 if len(grouped)!=483:
  raise ValueError("original P2/P3 exact 483 episode group count changed")
 event_records=[]
 for (site,eid), keys in sorted(grouped.items()):
  pending=sum(k in latest for k in keys)
  if len(keys)>0:
   event_records.append(dict(site=site,episode_id=eid,
    original_tier=original[keys[0]]["original_tier"],
    original_P2P3_HH=len(keys),
    remaining_P2P3_HH=pending,
    approved_P2P3_HH=len(keys)-pending,
    science_status="NEEDS_SOURCE_SCIENCE_REVIEW" if pending else
     "ALL_ORIGINAL_FLAGGED_HH_HAVE_APPROVED_OVERLAY_NOT_PRODUCTION"))
 remaining=[]
 for k in sorted(latest):
  r=original[k]
  remaining.append(dict(site=k[0],native_time=k[1],
   episode_id=r["original_episode_id"],original_tier=r["original_tier"],
   TA_F_QC=r["TA_F_QC"],VPD_F_QC=r["VPD_F_QC"],
   current_source_anomaly_decision=r["current_source_anomaly_decision"],
   latest_status="UNAPPROVED_P2P3_SCIENCE_HOLD",
   science_next_action="SOURCE_MET_SENSOR_QC_AND_INDEPENDENT_REFERENCE_EVIDENCE"))
 progress=[]
 for site in SITES:
  src={k for k in original if k[0]==site}
  hp={k for k in h if k[0]==site}
  pp={k for k in plat if k[0]==site}
  ap={k for k in o62 if k[0]==site}
  p1s=p1&src
  p23s=p23&src
  rem=latest&src
  n_events=sum(x["site"]==site and int(x["remaining_P2P3_HH"])>0 for x in event_records)
  progress.append(dict(site=site,
   original_P1_HH=len(p1s),original_P2P3_HH=len(p23s),
   approved_204_overlay_all_HH=len(ap),
   approved_204_inside_original_1750_HH=len(ap&src),
   approved_204_outside_original_1750_HH=len(ap-src),
   approved_P1_HH=len(ap&p1s),
   approved_P2P3_HH=len(ap&p23s),
   remaining_original_P2P3_HH=len(rem),
   remaining_original_P2P3_events=n_events,
   remaining_original_P1_HOLD_HH=len(hp),
   unapproved_original_RH_saturation_platform_HH=len(pp),
   remaining_original_flagged_HH_after_204=len(src-ap),
   original_P2P3_science_screen="P2P3_NONE_OR_COVERED" if not rem else "P2P3_PENDING",
   full_forcing_approved="NO"))
 if sum(int(r["original_P2P3_HH"]) for r in progress)!=1574 or sum(int(r["approved_204_overlay_all_HH"]) for r in progress)!=204:
  raise ValueError("site summary does not reconcile latest 204 and original P2/P3")
 if sum(int(r["remaining_original_P1_HOLD_HH"]) for r in progress)!=46 or sum(int(r["unapproved_original_RH_saturation_platform_HH"]) for r in progress)!=10:
  raise ValueError("P1 manual or RH platform HOLD site reconciliation failed")
 if sum(int(r["remaining_original_P2P3_HH"]) for r in progress)!=len(latest):
  raise ValueError("P2/P3 site remaining count failed")
 total_sites_remaining_p23=sum(int(r["remaining_original_P2P3_HH"])>0 for r in progress)
 total_sites_other_holds=sum(int(r["remaining_original_P1_HOLD_HH"])+int(r["unapproved_original_RH_saturation_platform_HH"])>0 for r in progress)
 original_pending_sites=sum(int(r["remaining_original_flagged_HH_after_204"])+int(r["unapproved_original_RH_saturation_platform_HH"])>0 for r in progress)
 event_remaining=sum(int(e["remaining_P2P3_HH"])>0 for e in event_records)
 summary=dict(
  stage="63",scope="Batch05 all exact ten original site/native HH",
  all_sites=10,original_flagged_1750_HH=1750,
  original_P1_HH=176,original_P2P3_HH=1574,
  approved_versioned_overlay_HH=204,
  approved_inside_original_1750_HH=len(set(o62)&set(original)),
  approved_outside_original_1750_HH=len(set(o62)-set(original)),
  approved_P1_HH=len(set(o62)&p1),
  approved_P2P3_HH=len(set(o62)&p23),
  remaining_original_P2P3_HH=len(latest),
  remaining_original_P2P3_events=event_remaining,
  original_P2P3_total_events=483,
  remaining_sites_with_P2P3=total_sites_remaining_p23,
  remaining_sites_with_separate_P1_or_RH_platform_HOLD=total_sites_other_holds,
  sites_with_any_original_flagged_or_platform_HOLD=original_pending_sites,
  manual_P1_HOLD_HH=46,RH_plateau_science_HOLD_HH=10,
  remaining_original_P1_HOLD_HH=len(h),
  no_site_production_forcing_pass=True,
  other_unflagged_full_meteorology_unassessed=True,
  old_174_still_preserved_per_Stage62=True,
  source_originals_modified=False,latest_204_changed=False,
  DATM_CIME_modified=False,Slurm_jobs_submitted=0,
  inputs_sha256={
   f25.name:sha(f25),f24.name:sha(f24),h24.name:sha(h24),
   s24.name:sha(s24),f62.name:sha(f62)})
 # All checks precede NEW report creation; don't write into any science source root.
 out.mkdir(exist_ok=False)
 fsite=out/"stage63_EXACT_TEN_SITE_REMAINING_AFTER_204.csv"
 fhh=out/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"
 fevent=out/"stage63_ALL483_ORIGINAL_P2P3_EVENTS_AFTER_204.csv"
 fp1=out/"stage63_UNCHANGED_46_P1_HOLD_SOURCE_LEDGER.csv"
 fplat=out/"stage63_UNCHANGED_10_RH_PLATFORM_HOLD_SOURCE_LEDGER.csv"
 write(fsite,SITE_COLS,progress)
 write(fhh,REMAIN_COLS,remaining)
 write(fevent,EVENT_COLS,event_records)
 write(fp1,P1_COLS,[dict(site=r["site"],native_time=r["native_time"],
   hold_reason=r["hold_reason"],action=r["action"],
   latest_status="P1_ORIGINAL_HOLD_UNCHANGED") for r in hold])
 write(fplat,EDGE_COLS,[dict(site=r["site"],native_time=r["native_time"],
   platform=r["platform"],original_RH_pct=r["original_RH_pct"],
   original_VPD_QC=r["original_VPD_QC"],review_status=r["review_status"]) for r in platform])
 summary["outputs_sha256"]={f.name:sha(f) for f in (fsite,fhh,fevent,fp1,fplat)}
 (out/"stage63_manifest.json").write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 md=["# Batch05 exact ten-site source-science progress after 204 approved candidate HH","",
 "Counts based on exact **(site, native time)** joins, not subtracting 204 from P2/P3.",
 "Approval means versioned candidate; no model-ready forcing or Slurm authority.","",
 "| Site | P2/P3 original | P2/P3 approved | P2/P3 remain | Pending P2/P3 events | P1 HOLD | RH platform HOLD | 204 overlay all |",
 "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
 for rr in sorted(progress,key=lambda x:int(x["remaining_original_P2P3_HH"]),reverse=True):
  md.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
   rr["site"],rr["original_P2P3_HH"],rr["approved_P2P3_HH"],
   rr["remaining_original_P2P3_HH"],rr["remaining_original_P2P3_events"],
   rr["remaining_original_P1_HOLD_HH"],rr["unapproved_original_RH_saturation_platform_HH"],
   rr["approved_204_overlay_all_HH"]))
 md+=["",
  "Remaining original P2/P3 flagged HH: **{}** across **{} sites** and **{} original events**.".format(
    len(latest),total_sites_remaining_p23,event_remaining),
  "46 original P1 manual HOLD and 10 original RH platform HOLD remain untouched.",
  "Site flagged-HH queues are only one part of full forcing assessment; never claim site ready based on zero P2/P3 alone.",
  "Original sources, old overlays, DATM/CIME, Slurm unchanged."]
 (out/"STAGE63_TEN_SITE_REMAINING_APPROVAL_AND_HOLD_REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 print("STAGE63 SUCCESS | EXACT 10-SITE 1750 original flagged vs 204 user-approved versioned candidate overlay")
 print("STAGE63 P2P3 REMAINING_HH",len(latest),"ORIGINAL_1574 APPROVED_OVERLAP",len(p23&set(o62)),
       "REMAINING_SITES",total_sites_remaining_p23,"REMAINING_EVENTS",event_remaining)
 print("STAGE63 P1 ORIGINAL 176 APPROVED 130 MANUAL_HOLD 46 | RH_PLATFORM_HOLD 10")
 print("STAGE63 APPROVED_204 INSIDE_ORIGINAL_1750",len(set(o62)&set(original)),
       "OUTSIDE_ORIGINAL_1750",len(set(o62)-set(original)))
 print("STAGE63 SITES | site originalP2P3 approvedP2P3 pendingP2P3 pendingEvents P1HOLD RHplateau totalApproved204")
 for r in sorted(progress,key=lambda r:int(r["remaining_original_P2P3_HH"]),reverse=True):
  print("STAGE63 SITE",r["site"],r["original_P2P3_HH"],r["approved_P2P3_HH"],
     r["remaining_original_P2P3_HH"],r["remaining_original_P2P3_events"],
     r["remaining_original_P1_HOLD_HH"],r["unapproved_original_RH_saturation_platform_HH"],
     r["approved_204_overlay_all_HH"])
 print("STAGE63 REPORT="+str(out/"STAGE63_TEN_SITE_REMAINING_APPROVAL_AND_HOLD_REPORT.md"))
 print("STAGE63_REPORTS="+str(out))
 print("STAGE63 READONLY ORIGINAL_SOURCE/204/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

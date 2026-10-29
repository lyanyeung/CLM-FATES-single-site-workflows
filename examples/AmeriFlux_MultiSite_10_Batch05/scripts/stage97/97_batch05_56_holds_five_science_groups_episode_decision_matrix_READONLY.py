#!/usr/bin/env python3
"""Batch05 Stage97 compact triage of 56 original protected science HOLD HH.

Read only the actual Stage96 strict-source-SHA audit reports. Verify all 56
site/native source records, the exactly five source evidence categories,
and create a per-run scientific action plan. No automatic edits/approval.
The 35 negative-RH source records must not be "repaired" with the SAME
physically invalid source-processed ERA humidity pair. The P1 near-zero
RH and RH-platform records remain possible observations, not reclassified
as source QC0 scientific truth without independent validation.
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
EXPECTED={
 "P1_SOURCE_QC2_NEGATIVE_AND_SAME_PROCESSED_ERA_INVALID":35,
 "P1_SOURCE_RH_POSITIVE_NO_BOTH_QC0_ANCHORS":10,
 "P1_SOURCE_RH_POSITIVE_WITH_BOTH_QC0_ANCHORS":1,
 "PLATFORM_VCM_NEAR_99_46_ORIGINAL_QC0":4,
 "PLATFORM_WCR_EXACT_100_ORIGINAL_QC0":6}
APPROVED_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
CLASS={
 "P1_NO_TWO_SIDED_SOURCE_VPD_QC0_HUMIDITY_ANCHORS_KEEP_HOLD":10,
 "P1_TWO_ORIGINAL_VPD_QC0_PHYSICAL_DONORS_SENSITIVITY_ONLY_KEEP_HOLD":1,
 "PLATFORM_HISTORICAL_FLAG_BUT_INSTANT_RH_NOT_99_5_KEEP_HOLD":4,
 "PLATFORM_NEAR_SATURATION_SOURCE_ORIGIN_REVIEW_KEEP_HOLD":6,
 "SOURCE_DERIVED_RH_NONPHYSICAL_OR_UNASSESSABLE_KEEP_HOLD":35}
DETAIL_FIELDS=("site","native_time","review_group","original_source_T_QC",
 "original_source_VPD_QC","source_implied_RH_pct",
 "source_processed_ERA_implied_RH_pct","original_source_RH_field_pct",
 "two_sided_original_VPD_QC0_physical_RH_anchors",
 "source_original_hold_reason","science_evidence_summary",
 "proposed_release_policy","requires_external_validation",
 "original_HOLD_unchanged","main_1675_unchanged")
RUN_FIELDS=("site","review_group","first_native_HH","last_native_HH",
 "contiguous_HH","source_RH_min_pct","source_RH_max_pct",
 "source_ERA_RH_min_pct","source_ERA_RH_max_pct",
 "science_action")
ACTIONS={
 "P1_SOURCE_QC2_NEGATIVE_AND_SAME_PROCESSED_ERA_INVALID":
 "DO_NOT_REUSE_INVALID_SOURCE_ERA_RH; use genuine independent met reference or scientifically justified gapfill, keep HOLD",
 "P1_SOURCE_RH_POSITIVE_NO_BOTH_QC0_ANCHORS":
 "Review measured-source near-zero RH vs meteorology and instrument QA, retain original QC/provenance; HOLD",
 "P1_SOURCE_RH_POSITIVE_WITH_BOTH_QC0_ANCHORS":
 "Review actual two-sided source QC0 RH donor values and target P1 physics; candidate sensitivity only, HOLD",
 "PLATFORM_VCM_NEAR_99_46_ORIGINAL_QC0":
 "Review repeated original 99.46% RH source plateau against neighboring RH and sensor metadata; no arbitrary desaturation, HOLD",
 "PLATFORM_WCR_EXACT_100_ORIGINAL_QC0":
 "Review exact repeated source RH100 and native RH sensor saturation/wetness plausibility, do not replace with ERA merely because different, HOLD"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()
def number(s):
 try:
  v=float(s)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def read(p,need):
 if not p.is_file() or p.is_symlink():raise ValueError("required source report absent "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as f:
  r=csv.DictReader(f);h=r.fieldnames or []
  if len(h)!=len(set(h)) or not set(need).issubset(h):
   raise ValueError("Stage96 source field schema changed "+str(p))
  rows=list(r)
 if any(None in x or any(v is None for v in x.values()) for x in rows):
  raise ValueError("Stage96 CSV malformed row "+str(p))
 return rows
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def classify(r):
 typ=r["risk_type"]
 v=number(r["source_derived_RH_pct"])
 era=number(r["source_processed_ERA_derived_RH_pct"])
 Tq=r["source_T_QC"];Vq=r["source_VPD_QC"]
 if typ=="P1":
  if v is None or not 0<=v<=100:
   if (v is None or era is None or abs(v-era)>.002 or v>=0 or
       Tq!="2" or Vq!="2"):
    raise ValueError("negative P1 same-invalid-source-ERA QC2 physical provenance drift "+r["site"]+"/"+r["native_time"])
   return "P1_SOURCE_QC2_NEGATIVE_AND_SAME_PROCESSED_ERA_INVALID"
  if r["two_sided_QC0_VPD_RH_physical_donors_within_2h"]=="True":
   if Tq!="0" or Vq!="0":
    raise ValueError("source P1 two-sided measured QB source unexpected")
   return "P1_SOURCE_RH_POSITIVE_WITH_BOTH_QC0_ANCHORS"
  return "P1_SOURCE_RH_POSITIVE_NO_BOTH_QC0_ANCHORS"
 if typ=="PLATFORM" and Tq=="0" and Vq=="0" and v is not None:
  if r["site"]=="US-Vcm" and 99.4<=v<99.5:
   return "PLATFORM_VCM_NEAR_99_46_ORIGINAL_QC0"
  if r["site"]=="US-WCr" and abs(v-100)<1e-6:
   return "PLATFORM_WCR_EXACT_100_ORIGINAL_QC0"
 raise ValueError("protected platform source scientific class changed "+r["site"]+"/"+r["native_time"])
def selftest():
 assert sum(EXPECTED.values())==56 and sum(CLASS.values())==56
 assert len(ACTIONS)==5
 assert datetime.strptime("201512060930","%Y%m%d%H%M")<datetime.strptime("201512061000","%Y%m%d%H%M")
 print("STAGE97 SELF-TEST PASS | exact five scientific groups 35+10+1+4+6 of 56 source-protected HOLD HH; no automatic source science approvals")
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage96",type=Path)
 ap.add_argument("--out",type=Path)
 o=ap.parse_args()
 if o.self_test:selftest();return
 if o.stage96 is None or o.out is None:
  ap.error("require exact successful Stage96 report directory and NEW output")
 d=o.stage96.expanduser().resolve();out=o.out.expanduser().resolve()
 if not d.is_dir() or out.exists() or not out.parent.is_dir() or out==d or out in d.parents or d in out.parents:
  ap.error("Stage96 original evidence missing or Stage97 output not a new disjoint directory")
 ff=d/"stage96_P1_46_RH_PLATFORM_10_ORIGINAL_SOURCE_FOCUSED_SCIENCE_REVIEW.csv"
 fc=d/"stage96_56_HH_PLUS_MINUS_2H_NATIVE_T_VPD_QC_RH_SOURCE_CONTEXT.csv"
 fs=d/"stage96_THREE_SITE_P1_PLATFORM_COUNTS.csv"
 mf=d/"stage96_P1_PLATFORM_HISTORICAL_SCIENCE_HOLD_MANIFEST.json"
 manifest=json.loads(mf.read_text())
 if (manifest.get("stage")!=96 or manifest.get("distinct_original_HOLD_source_HH")!=56
     or manifest.get("P1_HOLD_unchanged_HH")!=46
     or manifest.get("RH_platform_HOLD_unchanged_HH")!=10
     or manifest.get("protected_main_1675_research_overlay_SHA256")!=APPROVED_SHA
     or manifest.get("direct_source_automatically_approved_HH")!=0
     or manifest.get("P1_platform_HOLDs_overridden_HH")!=0
     or manifest.get("science_screen_counts")!=CLASS
     or any(manifest.get("output_SHA256",{}).get(f.name)!=sha(f) for f in (ff,fc,fs))):
  raise ValueError("Stage96 actual operator immutable source/provenance SHA result drift")
 rows=read(ff,["site","native_time","risk_type","source_T_QC","source_VPD_QC",
   "source_derived_RH_pct","source_processed_ERA_derived_RH_pct",
   "source_RH_field_pct","two_sided_QC0_VPD_RH_physical_donors_within_2h",
   "original_hold_reason","source_science_preliminary_class","final_science_HOLD_status",
   "prior_1675_research_overlay_overlap"])
 if len(rows)!=56 or len({(r["site"],r["native_time"]) for r in rows})!=56:
  raise ValueError("Stage96 56 unique original source site-native HOLD keys changed")
 actual=Counter()
 details=[];groups=defaultdict(list)
 for r in sorted(rows,key=lambda x:(x["site"],x["native_time"])):
  g=classify(r)
  actual[g]+=1;groups[(r["site"],g)].append(r)
  if (r["final_science_HOLD_status"]!="HOLD_UNCHANGED_NEEDS_SOURCE_PROVENANCE_SCIENTIFIC_REVIEW"
      or r["prior_1675_research_overlay_overlap"]!="False"):
   raise ValueError("Stage96 original source unapproved hold/status lost")
  details.append(dict(site=r["site"],native_time=r["native_time"],
   review_group=g,original_source_T_QC=r["source_T_QC"],
   original_source_VPD_QC=r["source_VPD_QC"],
   source_implied_RH_pct=r["source_derived_RH_pct"],
   source_processed_ERA_implied_RH_pct=r["source_processed_ERA_derived_RH_pct"],
   original_source_RH_field_pct=r["source_RH_field_pct"],
   two_sided_original_VPD_QC0_physical_RH_anchors=r["two_sided_QC0_VPD_RH_physical_donors_within_2h"],
   source_original_hold_reason=r["original_hold_reason"],
   science_evidence_summary=r["source_science_preliminary_class"],
   proposed_release_policy=ACTIONS[g],
   requires_external_validation="True",
   original_HOLD_unchanged="True",
   main_1675_unchanged="True"))
 if actual!=EXPECTED:raise ValueError("Stage97 actual 56 science groups differ "+repr(actual))
 runs=[]
 for (site,g),v in sorted(groups.items()):
  partitions=[];curr=[]
  for r in v:
   if curr and (datetime.strptime(r["native_time"],"%Y%m%d%H%M")-
      datetime.strptime(curr[-1]["native_time"],"%Y%m%d%H%M"))!=timedelta(minutes=30):
    partitions.append(curr);curr=[]
   curr.append(r)
  if curr:partitions.append(curr)
  for rrs in partitions:
   rhvals=[number(x["source_derived_RH_pct"]) for x in rrs
           if number(x["source_derived_RH_pct"]) is not None]
   eravals=[number(x["source_processed_ERA_derived_RH_pct"]) for x in rrs
           if number(x["source_processed_ERA_derived_RH_pct"]) is not None]
   runs.append(dict(site=site,review_group=g,first_native_HH=rrs[0]["native_time"],
    last_native_HH=rrs[-1]["native_time"],contiguous_HH=len(rrs),
    source_RH_min_pct="" if not rhvals else f"{min(rhvals):.6f}",
    source_RH_max_pct="" if not rhvals else f"{max(rhvals):.6f}",
    source_ERA_RH_min_pct="" if not eravals else f"{min(eravals):.6f}",
    source_ERA_RH_max_pct="" if not eravals else f"{max(eravals):.6f}",
    science_action=ACTIONS[g]))
 if sum(int(x["contiguous_HH"]) for x in runs)!=56:
  raise ValueError("historical science hold time runs did not conserve 56 source HH")
 out.mkdir(exist_ok=False)
 fdetails=out/"stage97_56_ORIGINAL_HOLD_HH_SCIENCE_DECISION_MATRIX.csv"
 fruns=out/"stage97_SOURCE_HOLD_CONTIGUOUS_SCIENCE_EPISODES.csv"
 m=out/"stage97_SOURCE_PROTECTED_HOLDS_CLOSURE_GATE_MANIFEST.json"
 write(fdetails,DETAIL_FIELDS,details);write(fruns,RUN_FIELDS,runs)
 summary=dict(stage=97,source_HOLDs_verified=56,
  science_groups=dict(actual),source_contiguous_episodes=len(runs),
  operator_original_hold_approved_HH=0,
  original_source_p1_46_and_platform_10_HOLD_unchanged=True,
  source_processed_ERA_qc2_invalid_cannot_be_reused_as_RH=True,
  stage96_original_manifest_sha256=sha(mf),
  stage96_original_details_sha256=sha(ff),
  protected_stage84_1675_sha256=APPROVED_SHA,
  release_gate="BLOCKED_REQUIRES_INDEPENDENT_HUMIDITY_REFERENCE_OR_EXPLICIT_HOLD_EXCLUSION_POLICY_AND_ERA_PROXY_AUDIT",
  source_original_unmodified=True,source_QC_unmodified=True,
  approved_1675_unmodified=True,datm_cime_unmodified=True,slurm_submitted=0,
  output_SHA256={p.name:sha(p) for p in (fdetails,fruns)})
 m.write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
 print("STAGE97 SUCCESS | 56 original science holds split 5 source-provenance groups, no RH/T QC/approved overlay edits")
 print("STAGE97 GROUPS",json.dumps(dict(actual),sort_keys=True))
 print("STAGE97 EPISODES",len(runs))
 for e in runs:
  print("STAGE97 EPISODE",e["site"],e["first_native_HH"],e["last_native_HH"],
    e["contiguous_HH"],e["review_group"],"RH",e["source_RH_min_pct"],e["source_RH_max_pct"])
 print("STAGE97 RELEASE_GATE",summary["release_gate"])
 print("STAGE97_REPORTS="+str(out))
 print("STAGE97 READONLY | ORIGINAL_QC/HOLDS/MAIN1675/STAGE89/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":
 main()

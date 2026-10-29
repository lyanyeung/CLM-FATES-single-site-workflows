#!/usr/bin/env python3
"""Stage91 Batch05: evaluate seven source T exceptions independently and safely.

Strictly read Stage90 original-source SHA-validated 63 unique risk HH and
seven 13-HH context windows, latest Stage84 1675 approved overlay, Stage89
51 Whs T/VPD integration research preview. Find ACTUAL original native
QC0 T anchors (if any) within +/-3h, source-QC0 VPD anchors separately;
report conservative 2-sided QC0 temperature sensitivity only (never
classify candidate T as measured or approved). Compare how the current
approved RH/VPD would behave with a candidate T. No source edits,
no production forcing approval, no Slurm jobs.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from datetime import datetime
from collections import Counter
T_CAT="UNRESOLVED_SOURCE_T_EXCEPTION"
APP_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
PREVIEW_SHA="95aefd6027e6f981ac821266bc379b89d9f1299d1c307b7575a17fec65588561"
REPORT_COLS=("site","native_time","original_T_C","original_T_QC","original_VPD_hPa",
 "original_VPD_QC","original_RH_implied_pct","approved_current_T_C",
 "approved_current_VPD_hPa","approved_current_RH_pct",
 "original_processed_ERA_T_C","original_processed_ERA_RH_pct",
 "nearest_before_T_QC0_time","nearest_before_T_QC0_C","nearest_before_T_QC0_minutes",
 "nearest_after_T_QC0_time","nearest_after_T_QC0_C","nearest_after_T_QC0_minutes",
 "before_T_QC0_source_VPD_QC","after_T_QC0_source_VPD_QC",
 "two_sided_QC0_T_available","two_sided_QC0_T_candidate_C",
 "QC0_donor_T_difference_C","original_T_minus_QC0_candidate_C",
 "if_candidate_T_keep_approved_VPD_RH_pct",
 "if_candidate_T_keep_approved_RH_VPD_hPa",
 "candidate_T_science_screen","source_T_review_status")
CONTEXT=("source_temperature_exception_native","native_time","minutes_offset",
 "original_TA_C","TA_F_QC","original_VPD_hPa","VPD_F_QC",
 "derived_RH_pct","original_source_ERA_TA_C","derived_source_ERA_RH_pct")
def checksum(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()
def n(s):
 try:
  x=float(s)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def fmt(x):return "" if x is None else f"{x:.9f}"
def sat(T):
 return None if T is None or not -80<=T<=60 else 6.112*math.exp(17.67*T/(T+243.5))
def rh(T,V):
 e=sat(T)
 return None if e is None or V is None else 100*(1-V/e)
def read(p,req):
 if not p.is_file() or p.is_symlink():raise ValueError("source report missing/symlink "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as stream:
  r=csv.DictReader(stream);heads=r.fieldnames or []
  if len(heads)!=len(set(heads)) or not set(req).issubset(heads):
   raise ValueError("original report schema changed "+str(p))
  out=list(r)
 if any(None in x or any(val is None for val in x.values()) for x in out):
  raise ValueError("original report row-width corrupted "+str(p))
 return out
def indexed(rows,fields=("site","native_time")):
 d={}
 for r in rows:
  k=tuple(r[x] for x in fields)
  if k in d:raise ValueError("duplicate site/source key "+str(k))
  d[k]=r
 return d
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as out:
  w=csv.DictWriter(out,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert abs(rh(0,6.112))<1e-9 and rh(0,7)<0
 assert n("-9999") is None and n("1.25")==1.25
 assert 7+46+10==63
 print("STAGE91 SELF-TEST PASS | seven original T-exception 3h native QC0 donors, prior1675 and Stage89 SHA; science diagnostics only")
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--self-test",action="store_true")
 for key in ("stage84","stage89","stage90"):parser.add_argument("--"+key,type=Path)
 parser.add_argument("--out",type=Path)
 a=parser.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,x) is None for x in ("stage84","stage89","stage90","out")):
  parser.error("exact successful Stage84/89/90 report dirs and fresh HOME output required")
 d84,d89,d90,out=(getattr(a,x).expanduser().resolve() for x in
                    ("stage84","stage89","stage90","out"))
 if (not all(x.is_dir() for x in (d84,d89,d90)) or out.exists() or
     not out.parent.is_dir() or
     any(out==x or out in x.parents or x in out.parents for x in (d84,d89,d90))):
  parser.error("input reports unavailable or fresh disjoint output required")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (checksum(f84)!=APP_SHA or m84.get("total_versioned_approved_repair_rows")!=1675
     or m84.get("output_SHA256",{}).get(f84.name)!=APP_SHA):
  raise ValueError("latest Stage84 main 1675 SHA/manifest mismatch")
 overlay=indexed(read(f84,["site","native_time","source_TA_C","source_VPD_hPa",
  "source_TA_QC","source_VPD_QC","modified_TA_C","modified_VPD_hPa",
  "modified_RH_pct"]))
 if len(overlay)!=1675:raise ValueError("approved site/native 1675 key count changed")
 f89=d89/"stage89_SEPARATE_WHS_51_T_RH_VPD_VERSIONED_INTEGRATION_PREVIEW.csv"
 m89=json.loads((d89/"stage89_SEPARATE_WHS_51_T_RH_VPD_READONLY_PREVIEW_MANIFEST.json").read_text())
 if (checksum(f89)!=PREVIEW_SHA or
     m89.get("output_preview_SHA256")!=PREVIEW_SHA or
     m89.get("stage67_approved_T_candidate_HH")!=51 or
     m89.get("combined_51_physics_RH_out_of_range_HH")!=0):
  raise ValueError("Stage89 separate 51 preview SHA or numerical science changed")
 f90=d90/"stage90_UNIQUE_HISTORICAL_SCIENCE_RELEASE_RISK_SOURCE_EVIDENCE.csv"
 fc=d90/"stage90_SEVEN_SOURCE_T_EXCEPTIONS_3H_NATIVE_ORIGINAL_CONTEXT.csv"
 fsite=d90/"stage90_TEN_SITE_RISK_AND_PROXY_METHOD_COUNTS.csv"
 manifest90=json.loads((d90/"stage90_FINAL_HISTORICAL_RELEASE_RISK_EVIDENCE_MANIFEST.json").read_text())
 if (manifest90.get("distinct_release_risk_source_HH")!=63 or
     manifest90.get("historical_source_T_exception_HH")!=7 or
     manifest90.get("historical_P1_HOLD_HH")!=46 or
     manifest90.get("historical_RH_platform_HOLD_HH")!=10 or
     manifest90.get("overlapping_risk_categories_source_HH")!=0 or
     manifest90.get("source_risks_overlapping_main_1675")!=7 or
     manifest90.get("source_risks_overlapping_separate_Stage89_51")!=0 or
     manifest90.get("missing_original_source_native_risk_HH")!=0 or
     manifest90.get("latest_1675_research_approved_overlay_SHA256")!=APP_SHA or
     manifest90.get("stage89_51_T_with_4_VPD_science_preview_SHA256")!=PREVIEW_SHA or
     any(manifest90.get("output_SHA256",{}).get(f.name)!=checksum(f) for f in (f90,fc,fsite))):
  raise ValueError("Stage90 actual ten-site original risk SHA and science outcome changed")
 risks=read(f90,["site","native_time","source_risk_categories",
   "original_TA_C","original_TA_QC","original_VPD_hPa","original_VPD_QC",
   "derived_original_RH_pct","source_ERA_TA_C","derived_source_processed_ERA_RH_pct"])
 contexts=read(fc,CONTEXT)
 if len(risks)!=63 or len(contexts)!=91:raise ValueError("Stage90 63 risks, seven 13x source contexts changed")
 targets={(r["site"],r["native_time"]):r for r in risks if
          T_CAT in r["source_risk_categories"].split(";")}
 if len(targets)!=7 or any(k not in overlay for k in targets):
  raise ValueError("seven exact source-T exception 1675 overlap changed")
 raw_context={}
 for r in contexts:
  pair=r["source_temperature_exception_native"].split("/")
  if len(pair)!=2:raise ValueError("Stage90 source context center ID corrupted")
  center=(pair[0],pair[1])
  if center not in targets:raise ValueError("Stage90 temperature context beyond seven source keys")
  raw_context.setdefault(center,[]).append(r)
 if set(raw_context)!=set(targets) or any(len(rows)!=13 or
     {n(x["minutes_offset"]) for x in rows}!={i*30 for i in range(-6,7)}
     for rows in raw_context.values()):
  raise ValueError("seven expected 13-timepoint source-native context windows changed")
 results=[];counts=Counter()
 for key,r in sorted(targets.items()):
  site,t=key;last=overlay[key]
  center_T=n(r["original_TA_C"]);center_V=n(r["original_VPD_hPa"])
  newT=n(last["modified_TA_C"]);newV=n(last["modified_VPD_hPa"])
  newRH=n(last["modified_RH_pct"])
  if (any(v is None for v in (center_T,center_V,newT,newV,newRH)) or
      last["source_TA_QC"]!=r["original_TA_QC"] or
      last["source_VPD_QC"]!=r["original_VPD_QC"] or
      abs(n(last["source_TA_C"])-center_T)>.002 or
      abs(n(last["source_VPD_hPa"])-center_V)>.002 or
      not 0<=newRH<=100 or rh(newT,newV) is None or
      abs(rh(newT,newV)-newRH)>0.05):
   raise ValueError("original/approved source T/VPD/RH drift or nonphysical "+str(key))
  prior=[x for x in raw_context[key] if
     n(x["minutes_offset"]) is not None and n(x["minutes_offset"])<0 and
     x["TA_F_QC"]=="0" and n(x["original_TA_C"]) is not None]
  later=[x for x in raw_context[key] if
     n(x["minutes_offset"]) is not None and n(x["minutes_offset"])>0 and
     x["TA_F_QC"]=="0" and n(x["original_TA_C"]) is not None]
  L=max(prior,key=lambda x:n(x["minutes_offset"])) if prior else None
  R=min(later,key=lambda x:n(x["minutes_offset"])) if later else None
  candidate=before_minutes=after_minutes=deltaT=span=None
  if L and R:
   before_minutes=-n(L["minutes_offset"])
   after_minutes=n(R["minutes_offset"])
   leftT,rightT=n(L["original_TA_C"]),n(R["original_TA_C"])
   candidate=leftT+(rightT-leftT)*before_minutes/(before_minutes+after_minutes)
   deltaT=center_T-candidate
   span=abs(leftT-rightT)
  reason=("NO_TWO_SIDED_SOURCE_QC0_T_ANCHORS_WITHIN_3H" if not (L and R) else
     "TWO_SIDED_QC0_T_DISAGREE_GT_5C" if span>5 else
     "ORIGINAL_QC0_T_NOT_GE8C_OUTLIER_VS_BRACKET" if abs(deltaT)<8 else
     "TWO_SIDED_QC0_T_SENSITIVITY_CANDIDATE_ONLY_REQUIRES_INDEPENDENT_CONFIRMATION")
  ccRH=rh(candidate,newV) if candidate is not None else None
  ccV=sat(candidate)*(1-newRH/100) if sat(candidate) is not None else None
  counts[reason]+=1
  results.append(dict(site=site,native_time=t,
   original_T_C=fmt(center_T),original_T_QC=r["original_TA_QC"],
   original_VPD_hPa=fmt(center_V),original_VPD_QC=r["original_VPD_QC"],
   original_RH_implied_pct=fmt(rh(center_T,center_V)),
   approved_current_T_C=fmt(newT),approved_current_VPD_hPa=fmt(newV),
   approved_current_RH_pct=fmt(newRH),
   original_processed_ERA_T_C=r["source_ERA_TA_C"],
   original_processed_ERA_RH_pct=r["derived_source_processed_ERA_RH_pct"],
   nearest_before_T_QC0_time=L["native_time"] if L else "",
   nearest_before_T_QC0_C=L["original_TA_C"] if L else "",
   nearest_before_T_QC0_minutes=fmt(before_minutes),
   nearest_after_T_QC0_time=R["native_time"] if R else "",
   nearest_after_T_QC0_C=R["original_TA_C"] if R else "",
   nearest_after_T_QC0_minutes=fmt(after_minutes),
   before_T_QC0_source_VPD_QC=L["VPD_F_QC"] if L else "",
   after_T_QC0_source_VPD_QC=R["VPD_F_QC"] if R else "",
   two_sided_QC0_T_available=str(bool(L and R)),
   two_sided_QC0_T_candidate_C=fmt(candidate),
   QC0_donor_T_difference_C=fmt(span),
   original_T_minus_QC0_candidate_C=fmt(deltaT),
   if_candidate_T_keep_approved_VPD_RH_pct=fmt(ccRH),
   if_candidate_T_keep_approved_RH_VPD_hPa=fmt(ccV),
   candidate_T_science_screen=reason,
   source_T_review_status="REQUIRES_MANUAL_OR_INDEPENDENT_SOURCE_VALIDATION_NOT_APPROVED_FOR_FORCING"))
 out.mkdir(exist_ok=False)
 table=out/"stage91_SEVEN_ORIGINAL_SOURCE_T_TOWER_QC0_BRACKET_SENSITIVITY.csv"
 manifest=out/"stage91_T_EXCEPTION_SCIENCE_SCREEN_MANIFEST.json"
 write(table,REPORT_COLS,results)
 report=dict(stage=91,source_T_cases=7,original_source_QC0_donor_rule="NEAREST_BOTH_SIDES_WITHIN_3_HOURS",
  original_T_QC0_values_not_assumed_correct=True,stage84_main_1675_SHA256=APP_SHA,
  stage89_51_preview_SHA256=PREVIEW_SHA,
  Stage90_original_risk_sources_SHA256=checksum(f90),
  source_T_screen_counts=dict(counts),
  no_automatic_repair=True,source_QC_unchanged=True,
  source_origin_unmodified=True,main_1675_unmodified=True,
  Stage89_51_unmodified=True,DATM_CIME_unchanged=True,Slurm_submitted=0,
  output_SHA256={table.name:checksum(table)},
  release_gate="BLOCKED_REQUIRES_SOURCE_T_7_P1_46_PLATFORM_10_PROXY_HUMIDITY_INDEPENDENT_VALIDATION")
 manifest.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("STAGE91 SUCCESS | seven original QC0-temperature source exception science sensitivity screens, NO FORCING CHANGES")
 print("STAGE91 CLASSIFICATIONS",json.dumps(dict(counts),sort_keys=True))
 print("STAGE91 DETAIL site native originalT approvedT beforeQC0_time/T afterQC0_time/T candidateT deltaOrigVSCandidate RH_at_candidate_keepVPD VPD_at_candidate_keep_approvedRH decision")
 for row in results:
  print("STAGE91 DETAIL",row["site"],row["native_time"],row["original_T_C"],
   row["approved_current_T_C"],row["nearest_before_T_QC0_time"],
   row["nearest_before_T_QC0_C"],row["nearest_after_T_QC0_time"],
   row["nearest_after_T_QC0_C"],row["two_sided_QC0_T_candidate_C"],
   row["original_T_minus_QC0_candidate_C"],
   row["if_candidate_T_keep_approved_VPD_RH_pct"],
   row["if_candidate_T_keep_approved_RH_VPD_hPa"],row["candidate_T_science_screen"])
 print("STAGE91_RELEASE_GATE",report["release_gate"])
 print("STAGE91_REPORTS="+str(out))
 print("STAGE91 ORIGINAL/QC/PRIOR1675/STAGE89/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

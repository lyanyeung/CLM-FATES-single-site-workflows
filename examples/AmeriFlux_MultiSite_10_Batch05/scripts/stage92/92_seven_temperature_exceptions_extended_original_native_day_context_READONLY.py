#!/usr/bin/env python3
"""Batch05 Stage92: precise extended source-native context for seven T anomalies.

Revalidate Stage91 source-T classifications and Stage90/Stage84 immutable
science, then inspect full +/-12 hours of source-native TA/VPD/QC and
source-processed ERA at four original sites. Characterize isolated
source-T departures, nearest real QC0 T anchors within 12h, T/VPD/RH
compatibility with approved RH reconstructions. No proposal is auto-approved,
no original QC/T/VPD or DATM/CIME/Slurm mutation.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path

APPROVED_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
SOURCE_SITES={
 "US-Vcm":("2007-2025_v1.3_r1","c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c"),
 "US-Vcp":("2007-2025_v1.3_r1","eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42"),
 "US-Wjs":("2007-2025_v1.3_r1","9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6"),
 "US-Wkg":("2004-2025_v1.3_r1","f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"),
}
TARGETS={
 "US-Vcm":("201409062330",),
 "US-Vcp":("200805221530","201404262330"),
 "US-Wjs":("202203310330","202504191600"),
 "US-Wkg":("202503071230","202509101300"),
}
EXT_FIELDS=("site","center_native","native_time","minutes_offset",
 "TA_F_C","TA_F_QC","VPD_F_hPa","VPD_F_QC","derived_RH_pct",
 "source_processed_ERA_T_C","source_processed_ERA_VPD_hPa","source_processed_ERA_RH_pct",
 "source_P_F","source_SW_IN_F")
FOCUS_FIELDS=("site","native_time","source_original_T_C","source_original_T_QC",
 "source_original_VPD_hPa","source_original_VPD_QC","source_original_RH_pct",
 "current_approved_T_C","current_approved_VPD_hPa","current_approved_RH_pct",
 "source_processed_ERA_T_C","source_processed_ERA_RH_pct",
 "Stage91_original_science_classification",
 "immediate_before_T_C","immediate_before_T_QC",
 "immediate_after_T_C","immediate_after_T_QC",
 "immediate_source_T_neighbor_mean_C","original_T_minus_immediate_mean_C",
 "nearest_prior_QC0_T_native_within_12h","nearest_prior_QC0_T_C","nearest_prior_QC0_distance_HH",
 "nearest_after_QC0_T_native_within_12h","nearest_after_QC0_T_C","nearest_after_QC0_distance_HH",
 "nearest_two_QC0_T_difference_C",
 "nearest_two_QC0_T_candidate_C","original_T_minus_QC0_candidate_C",
 "source_ERA_T_minus_QC0_candidate_C",
 "RH_IF_candidateT_keeps_approvedVPD_pct",
 "VPD_IF_candidateT_keeps_approvedRH_hPa",
 "preliminary_source_T_evidence_category",
 "source_temperature_repair_approved","production_DATM_permission")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()
def n(x):
 try:
  x=float(x)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def es(t):
 return None if t is None or not -80<=t<=60 else 6.112*math.exp(17.67*t/(t+243.5))
def rh(t,v):
 e=es(t)
 return None if e is None or v is None else 100*(1-v/e)
def f(x):return "" if x is None else f"{x:.9f}"
def dt(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid native site timestamp "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def shift(t,i):return (dt(t)+timedelta(minutes=i*30)).strftime("%Y%m%d%H%M")
def read(p,req):
 if not p.is_file() or p.is_symlink():raise ValueError("missing immutable report "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  rd=csv.DictReader(h);names=rd.fieldnames or []
  if len(names)!=len(set(names)) or not set(req).issubset(names):
   raise ValueError("source report schema drift "+str(p))
  rows=list(rd)
 if any(None in x or any(v is None for v in x.values()) for x in rows):
  raise ValueError("source report record width mismatch "+str(p))
 return rows
def index(rows):
 d={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in d:raise ValueError("original source key duplicated "+str(k))
  d[k]=r
 return d
def write(p,heads,rows):
 with p.open("x",encoding="utf-8",newline="") as h:
  w=csv.DictWriter(h,fieldnames=heads,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert sum(map(len,TARGETS.values()))==7
 assert shift("202509101300",-1)=="202509101230"
 assert shift("202509101300",1)=="202509101330"
 assert rh(0,7)<0 and abs(rh(0,6.112))<1e-9
 assert n("-9999") is None and n("4.2")==4.2
 print("STAGE92 SELF-TEST PASS | seven original-T science exceptions extended +/-12h source native, exact original SHA, prior1675, Stage90/91 read-only")
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--self-test",action="store_true")
 for x in ("stage84","stage90","stage91"):
  parser.add_argument("--"+x,type=Path)
 parser.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 parser.add_argument("--out",type=Path)
 o=parser.parse_args()
 if o.self_test:selftest();return
 if any(getattr(o,x) is None for x in ("stage84","stage90","stage91","out")):
  parser.error("require successful Stage84, Stage90, Stage91 report dirs and fresh output")
 d84,d90,d91,out=(getattr(o,x).expanduser().resolve() for x in
                   ("stage84","stage90","stage91","out"))
 root=o.sites_root.expanduser().resolve()
 if (not all(x.is_dir() for x in (d84,d90,d91,root)) or out.exists() or
     not out.parent.is_dir() or any(out==x or out in x.parents or x in out.parents
      for x in (d84,d90,d91,root))):
  parser.error("missing successful science reports or output not fresh/disjoint")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(f84)!=APPROVED_SHA or m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=APPROVED_SHA):
  raise ValueError("Stage84 approved source versioned SHA mismatch")
 approved=index(read(f84,["site","native_time","modified_TA_C","modified_VPD_hPa",
  "modified_RH_pct","source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC"]))
 if len(approved)!=1675:raise ValueError("previous 1675 source science ledger changed")
 f90=d90/"stage90_UNIQUE_HISTORICAL_SCIENCE_RELEASE_RISK_SOURCE_EVIDENCE.csv"
 m90=json.loads((d90/"stage90_FINAL_HISTORICAL_RELEASE_RISK_EVIDENCE_MANIFEST.json").read_text())
 if (m90.get("distinct_release_risk_source_HH")!=63 or
     m90.get("historical_source_T_exception_HH")!=7 or
     m90.get("source_risks_overlapping_main_1675")!=7 or
     m90.get("missing_original_source_native_risk_HH")!=0 or
     m90.get("latest_1675_research_approved_overlay_SHA256")!=APPROVED_SHA or
     m90.get("output_SHA256",{}).get(f90.name)!=sha(f90)):
  raise ValueError("Stage90 actual original source seven exception risk evidence not validated")
 r90=read(f90,["site","native_time","source_risk_categories","original_TA_C",
     "original_TA_QC","original_VPD_hPa","original_VPD_QC"])
 flagged={(r["site"],r["native_time"]):r for r in r90 if
   "UNRESOLVED_SOURCE_T_EXCEPTION" in r["source_risk_categories"].split(";")}
 expected={(site,t) for site,times in TARGETS.items() for t in times}
 if set(flagged)!=expected or not expected.issubset(approved):
  raise ValueError("Stage90 original seven exact source time/QC keys changed")
 f91=d91/"stage91_SEVEN_ORIGINAL_SOURCE_T_TOWER_QC0_BRACKET_SENSITIVITY.csv"
 m91=json.loads((d91/"stage91_T_EXCEPTION_SCIENCE_SCREEN_MANIFEST.json").read_text())
 if (m91.get("stage")!=91 or m91.get("source_T_cases")!=7 or
     m91.get("stage84_main_1675_SHA256")!=APPROVED_SHA or
     m91.get("no_automatic_repair") is not True or
     m91.get("output_SHA256",{}).get(f91.name)!=sha(f91)):
  raise ValueError("Stage91 actual science screening SHA/manifest changed")
 r91=index(read(f91,["site","native_time","candidate_T_science_screen"]))
 if set(r91)!=expected:raise ValueError("Stage91 7 original native source keys changed")
 expected_cls={"NO_TWO_SIDED_SOURCE_QC0_T_ANCHORS_WITHIN_3H":4,
  "ORIGINAL_QC0_T_NOT_GE8C_OUTLIER_VS_BRACKET":2,
  "TWO_SIDED_QC0_T_DISAGREE_GT_5C":1}
 if m91.get("source_T_screen_counts")!=expected_cls:
  raise ValueError("Stage91 original source 4/2/1 strict evidence classification changed")
 needed={}
 for site,targets in TARGETS.items():
  clocks={shift(t,i) for t in targets for i in range(-24,25)}
  needed[site]=clocks
 originals={}
 for site,(release,source_hash) in SOURCE_SITES.items():
  folder=root/site/"forcing"/"raw"/("AMF_"+site+"_FLUXNET_"+release)
  if not folder.is_dir() or folder.is_symlink():raise ValueError("original source folder missing "+site)
  files=[p for p in folder.iterdir() if re.fullmatch(
   "AMF_"+site+r"_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",p.name,re.I)]
  if len(files)!=1 or not files[0].is_file() or files[0].is_symlink() or sha(files[0])!=source_hash:
   raise ValueError("Stage05 original native source SHA drift "+site)
  source={}
  with files[0].open("r",encoding="utf-8-sig",newline="") as h:
   rd=csv.DictReader(h)
   if not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(rd.fieldnames or []):
    raise ValueError("missing original source met columns "+site)
   for r in rd:
    t=r["TIMESTAMP_START"]
    if t in needed[site]:
     if t in source:raise ValueError("duplicate original time "+site+"/"+t)
     source[t]=r
  originals[site]=source
 extended=[];summary=[];cats=Counter()
 for site,t in sorted(expected):
  rows=originals[site]
  x=rows.get(t)
  if x is None:raise ValueError("missing actual 7 source time "+site+"/"+t)
  oldT=n(x["TA_F"]);oldV=n(x["VPD_F"])
  overlay=approved[(site,t)];reported=flagged[(site,t)]
  if (oldT is None or oldV is None or
      abs(oldT-n(reported["original_TA_C"]))>.002 or
      abs(oldV-n(reported["original_VPD_hPa"]))>.002 or
      x["TA_F_QC"]!=reported["original_TA_QC"] or
      x["VPD_F_QC"]!=reported["original_VPD_QC"] or
      abs(oldT-n(overlay["source_TA_C"]))>.002 or
      abs(oldV-n(overlay["source_VPD_hPa"]))>.002):
   raise ValueError("source native exact T/QC/VPD vs Stage90/84 changed "+site+"/"+t)
  center_info={}
  for i in range(-24,25):
   time=shift(t,i);row=rows.get(time)
   if row is None:continue
   sourceT=n(row["TA_F"]);sourceV=n(row["VPD_F"])
   eraT=n(row["TA_ERA"]);eraV=n(row["VPD_ERA"])
   extended.append(dict(site=site,center_native=t,native_time=time,minutes_offset=i*30,
    TA_F_C=row["TA_F"],TA_F_QC=row["TA_F_QC"],VPD_F_hPa=row["VPD_F"],
    VPD_F_QC=row["VPD_F_QC"],derived_RH_pct=f(rh(sourceT,sourceV)),
    source_processed_ERA_T_C=row["TA_ERA"],
    source_processed_ERA_VPD_hPa=row["VPD_ERA"],
    source_processed_ERA_RH_pct=f(rh(eraT,eraV)),
    source_P_F=row.get("P_F",""),source_SW_IN_F=row.get("SW_IN_F","")))
   if i in (-1,1):center_info[i]=row
  early=[(i,rows[shift(t,i)]) for i in range(-1,-25,-1)
       if shift(t,i) in rows and rows[shift(t,i)]["TA_F_QC"]=="0" and n(rows[shift(t,i)]["TA_F"]) is not None]
  late=[(i,rows[shift(t,i)]) for i in range(1,25)
       if shift(t,i) in rows and rows[shift(t,i)]["TA_F_QC"]=="0" and n(rows[shift(t,i)]["TA_F"]) is not None]
  left=early[0] if early else None;right=late[0] if late else None
  cand=span=delta=era_delta=None
  if left and right:
   il,l=left;ir,r=right
   leftT,rightT=n(l["TA_F"]),n(r["TA_F"])
   cand=leftT+(rightT-leftT)*(-il)/(ir-il)
   span=abs(leftT-rightT)
   delta=oldT-cand
   era_delta=n(x["TA_ERA"])-cand if n(x["TA_ERA"]) is not None else None
  before=center_info.get(-1);after=center_info.get(1)
  bT=n(before["TA_F"]) if before else None
  aT=n(after["TA_F"]) if after else None
  middle=(bT+aT)/2 if bT is not None and aT is not None else None
  candidate_rh=rh(cand,n(overlay["modified_VPD_hPa"])) if cand is not None else None
  candidate_vpd=es(cand)*(1-n(overlay["modified_RH_pct"])/100) if
    cand is not None and es(cand) is not None and n(overlay["modified_RH_pct"]) is not None else None
  # Scientific hypotheses, NOT temperature replacement approvals.
  if (cand is not None and abs(oldT-cand)<=0.1 and
      left[0]>=-2 and right[0]<=2):
   classification="NEAR_QC0_BRACKET_RETAIN_ORIGINAL_T_CANDIDATE"
  elif (cand is not None and abs(oldT-cand)>=10 and
        n(x["TA_ERA"]) is not None and abs(n(x["TA_ERA"])-cand)<5):
   classification="STRONG_ORIGINAL_T_OUTLIER_EVIDENCE_T_QC0_AND_SOURCE_ERA_AGREE_NEEDS_LOCAL_APPROVAL"
  elif cand is None:
   classification="NO_TWO_SIDED_SOURCE_QC0_WITHIN_12H_INDEPENDENT_SOURCE_NEEDED"
  elif span is not None and span>5:
   classification="TWO_QC0_SOURCE_T_DONORS_DISAGREE_NEEDS_LOCAL_CONTEXT"
  else:
   classification="SOURCE_T_REVIEW_UNRESOLVED_NO_AUTOMATIC_REPLACEMENT"
  cats[classification]+=1
  summary.append(dict(site=site,native_time=t,
   source_original_T_C=f(oldT),source_original_T_QC=x["TA_F_QC"],
   source_original_VPD_hPa=f(oldV),source_original_VPD_QC=x["VPD_F_QC"],
   source_original_RH_pct=f(rh(oldT,oldV)),
   current_approved_T_C=overlay["modified_TA_C"],
   current_approved_VPD_hPa=overlay["modified_VPD_hPa"],
   current_approved_RH_pct=overlay["modified_RH_pct"],
   source_processed_ERA_T_C=x["TA_ERA"],
   source_processed_ERA_RH_pct=f(rh(n(x["TA_ERA"]),n(x["VPD_ERA"]))),
   Stage91_original_science_classification=r91[(site,t)]["candidate_T_science_screen"],
   immediate_before_T_C=before["TA_F"] if before else "",
   immediate_before_T_QC=before["TA_F_QC"] if before else "",
   immediate_after_T_C=after["TA_F"] if after else "",
   immediate_after_T_QC=after["TA_F_QC"] if after else "",
   immediate_source_T_neighbor_mean_C=f(middle),
   original_T_minus_immediate_mean_C=f(oldT-middle if middle is not None else None),
   nearest_prior_QC0_T_native_within_12h=shift(t,left[0]) if left else "",
   nearest_prior_QC0_T_C=left[1]["TA_F"] if left else "",
   nearest_prior_QC0_distance_HH=-left[0] if left else "",
   nearest_after_QC0_T_native_within_12h=shift(t,right[0]) if right else "",
   nearest_after_QC0_T_C=right[1]["TA_F"] if right else "",
   nearest_after_QC0_distance_HH=right[0] if right else "",
   nearest_two_QC0_T_difference_C=f(span),
   nearest_two_QC0_T_candidate_C=f(cand),
   original_T_minus_QC0_candidate_C=f(delta),
   source_ERA_T_minus_QC0_candidate_C=f(era_delta),
   RH_IF_candidateT_keeps_approvedVPD_pct=f(candidate_rh),
   VPD_IF_candidateT_keeps_approvedRH_hPa=f(candidate_vpd),
   preliminary_source_T_evidence_category=classification,
   source_temperature_repair_approved="False",production_DATM_permission="NO"))
 if len(summary)!=7 or len({(x["site"],x["native_time"]) for x in summary})!=7:
  raise ValueError("unexpected source T-seven reconciliation")
 out.mkdir(exist_ok=False)
 fsum=out/"stage92_SEVEN_T_EXCEPTION_EVIDENCE_HYPOTHESES_AND_QC0_ANCHORS.csv"
 fctx=out/"stage92_SEVEN_T_EXCEPTION_EXTENDED_12H_NATIVE_SOURCE_CONTEXT.csv"
 man=out/"stage92_EXTENDED_SOURCE_T_EVIDENCE_MANIFEST.json"
 write(fsum,FOCUS_FIELDS,summary);write(fctx,EXT_FIELDS,extended)
 manifest=dict(stage=92,stage91_verified_4_2_1_classification=True,
  original_source_exception_count=7,source_extended_native_rows=len(extended),
  original_Site05_CSV_SHA256={k:v[1] for k,v in SOURCE_SITES.items()},
  approved_stage84_1675_SHA256=APPROVED_SHA,
  original_stage91_source_report_SHA256=sha(f91),
  output_SHA256={f.name:sha(f) for f in (fsum,fctx)},
  evidence_hypothesis_counts=dict(cats),automatic_T_repair_approved_HH=0,
  previous_1675_unmodified=True,original_sources_QC_unchanged=True,
  DATM_CIME_unchanged=True,Slurm_submitted=0,
  release_gate="BLOCKED_SOURCE_T_INDEPENDENT_LOCAL_SCIENCE_REVIEW_AND_P1_PLATFORM_PROXY")
 man.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 print("STAGE92 SUCCESS | seven original source-T 12h context scientific evidence collected, source SHA exact, 0 automatic repairs")
 print("STAGE92 CLASSIFICATIONS",json.dumps(dict(cats),sort_keys=True))
 print("STAGE92 DETAIL site native sourceT immediatePreT/QC immediatePostT/QC QC0beforeT/distance QC0afterT/distance candidateT source_minus_candidateT ERA_minus_candidateT conclusion")
 for r in summary:
  print("STAGE92 DETAIL",r["site"],r["native_time"],r["source_original_T_C"],
   r["immediate_before_T_C"]+"/"+r["immediate_before_T_QC"],
   r["immediate_after_T_C"]+"/"+r["immediate_after_T_QC"],
   r["nearest_prior_QC0_T_C"]+"/"+str(r["nearest_prior_QC0_distance_HH"]),
   r["nearest_after_QC0_T_C"]+"/"+str(r["nearest_after_QC0_distance_HH"]),
   r["nearest_two_QC0_T_candidate_C"],
   r["original_T_minus_QC0_candidate_C"],
   r["source_ERA_T_minus_QC0_candidate_C"],
   r["preliminary_source_T_evidence_category"])
 print("STAGE92 RELEASE_GATE",manifest["release_gate"])
 print("STAGE92_REPORTS="+str(out))
 print("STAGE92 READONLY | ORIGINAL/QC/PRIOR1675/STAGE90/STAGE91/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Batch05 Stage96: original-source P1 46 + RH platform 10 HOLD review.

Exactly 56 distinct held site/native HH (Vcm 43 P1+4 platform,
Vcp 3 P1, WCr 6 platform). Read original SHA pinned Stage05 FLUXMET
at these three sites, Stage63 P1/platform historical HOLD source-ledgers,
Stage90 risk source audit, Stage84 protected 1675 research overlay.
Produce source T/VPD/QC/RH, original native RH field, source processed
ERA proxy, plus +/-2h context and reliable donor classifications.
Any source RH/ERA values are diagnosis, NOT permission to repair HOLDs.
No changes to original source, original QC, 1675 approved research
overlay, Stage89 separate 51 HH, forcing, DATM/CIME or Slurm.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

PREV_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
SITE_FILES={
 "US-Vcm":("2007-2025_v1.3_r1","c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c"),
 "US-Vcp":("2007-2025_v1.3_r1","eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42"),
 "US-WCr":("1999-2025_v1.3_r1","f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506")}
EXPECT={("US-Vcm","P1"):43,("US-Vcm","PLATFORM"):4,
 ("US-Vcp","P1"):3,("US-WCr","PLATFORM"):6}
FOCUS=("site","native_time","risk_type","original_hold_reason","hold_policy","platform_label",
 "original_reported_platform_RH_pct","source_original_T_C","source_T_QC",
 "source_original_VPD_hPa","source_VPD_QC",
 "source_derived_RH_pct","source_RH_field_pct",
 "source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_derived_RH_pct",
 "left_nearest_source_VPD_QC0_time","left_nearest_source_QC0_derived_RH_pct",
 "right_nearest_source_VPD_QC0_time","right_nearest_source_QC0_derived_RH_pct",
 "two_sided_QC0_VPD_RH_physical_donors_within_2h",
 "nearest_donor_RH_difference_pct",
 "surrounding_native_RH_max_pct","surrounding_native_RH_min_pct",
 "surrounding_RH_ge_99_5_HH",
 "original_source_numeric_RH_physical",
 "P1_source_T_VPD_RH_nonphysical",
 "prior_1675_research_overlay_overlap",
 "source_science_preliminary_class","final_science_HOLD_status")
CTX=("site","center_native","risk_type","native_time","relative_minutes","source_T_C","source_T_QC",
 "source_VPD_hPa","source_VPD_QC","source_derived_RH_pct","source_RH_field_pct",
 "source_processed_ERA_T_C","source_processed_ERA_derived_RH_pct")
SITE_SUM=("site","P1_HOLD","PLATFORM_HOLD","two_sided_source_VPD_QC0_RH_donors",
 "original_source_derived_RH_nonphysical","original_RH_field_ge_99_5",
 "research_overlay_overlap")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for part in iter(lambda:stream.read(1<<20),b""):h.update(part)
 return h.hexdigest()
def n(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None
def es(t):
 return None if t is None or not -80<=t<=60 else 6.112*math.exp(17.67*t/(t+243.5))
def rh(t,v):
 e=es(t)
 return None if e is None or v is None else 100*(1-v/e)
def fmt(x):return "" if x is None else f"{x:.9f}"
def dt(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid source timestamp "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def shift(t,i):
 return (dt(t)+timedelta(minutes=i*30)).strftime("%Y%m%d%H%M")
def csvread(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("required historical source/report unavailable "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as h:
  rdr=csv.DictReader(h);heads=rdr.fieldnames or []
  if len(heads)!=len(set(heads)) or not set(required).issubset(heads):
   raise ValueError("historical source CSV schema drift "+str(p))
  rr=list(rdr)
 if any(None in row or any(v is None for v in row.values()) for row in rr):
  raise ValueError("historical source CSV malformed width "+str(p))
 return rr
def key(rows):
 out={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in out:raise ValueError("source native time duplicate "+str(k))
  out[k]=r
 return out
def csvwrite(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as h:
  writer=csv.DictWriter(h,fieldnames=cols,extrasaction="raise")
  writer.writeheader();writer.writerows(rows)
def selftest():
 assert sum(EXPECT.values())==56 and len(SITE_FILES)==3
 assert shift("201409062330",1)=="201409070000"
 assert rh(0,7)<0 and abs(rh(0,6.112))<1e-8
 assert n("-9999") is None and n("2.3")==2.3
 print("STAGE96 SELF-TEST PASS | 46 original P1 and 10 RH platform distinct source HOLDs, exact 3-site Stage05 original SHA, prior1675 immutable; read-only")
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--self-test",action="store_true")
 for k in ("stage63","stage84","stage90"):parser.add_argument("--"+k,type=Path)
 parser.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 parser.add_argument("--out",type=Path)
 a=parser.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,k) is None for k in ("stage63","stage84","stage90","out")):
  parser.error("require actual Stage63/84/90 report dirs and NEW output directory")
 d63,d84,d90,out=(getattr(a,k).expanduser().resolve() for k in ("stage63","stage84","stage90","out"))
 root=a.sites_root.expanduser().resolve()
 if (not all(x.is_dir() for x in (d63,d84,d90,root))
     or out.exists() or not out.parent.is_dir()
     or any(out==x or out in x.parents or x in out.parents for x in (d63,d84,d90,root))):
  parser.error("input sources missing or output not a new disjoint report folder")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(f84)!=PREV_SHA or m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=PREV_SHA):
  raise ValueError("protected main 1675 research source/manifest SHA changed")
 approved=key(csvread(f84,("site","native_time")))
 if len(approved)!=1675:raise ValueError("original main approved 1675 scope drift")
 fp1=d63/"stage63_UNCHANGED_46_P1_HOLD_SOURCE_LEDGER.csv"
 fplat=d63/"stage63_UNCHANGED_10_RH_PLATFORM_HOLD_SOURCE_LEDGER.csv"
 m63=json.loads((d63/"stage63_manifest.json").read_text())
 if (m63.get("manual_P1_HOLD_HH")!=46 or
     m63.get("RH_plateau_science_HOLD_HH")!=10 or
     any(m63.get("outputs_sha256",{}).get(p.name)!=sha(p) for p in (fp1,fplat))):
  raise ValueError("Stage63 immutable 46/10 original HOLD ledgers changed")
 p1=key(csvread(fp1,("site","native_time","hold_reason","action","latest_status")))
 platform=key(csvread(fplat,("site","native_time","platform","original_RH_pct",
   "original_VPD_QC","review_status")))
 if len(p1)!=46 or len(platform)!=10 or set(p1)&set(platform):
  raise ValueError("historical source P1/platform holds not exactly 56 separate source HH")
 f90=d90/"stage90_UNIQUE_HISTORICAL_SCIENCE_RELEASE_RISK_SOURCE_EVIDENCE.csv"
 m90=json.loads((d90/"stage90_FINAL_HISTORICAL_RELEASE_RISK_EVIDENCE_MANIFEST.json").read_text())
 if (m90.get("distinct_release_risk_source_HH")!=63 or
     m90.get("historical_P1_HOLD_HH")!=46 or
     m90.get("historical_RH_platform_HOLD_HH")!=10 or
     m90.get("overlapping_risk_categories_source_HH")!=0 or
     m90.get("latest_1675_research_approved_overlay_SHA256")!=PREV_SHA or
     m90.get("source_risks_overlapping_main_1675")!=7 or
     m90.get("output_SHA256",{}).get(f90.name)!=sha(f90)):
  raise ValueError("Stage90 actual 63 original risk source/overlay status drift")
 risks=key(csvread(f90,("site","native_time","source_risk_categories",
   "source_data_status","prior_1675_research_overlay_present",
   "original_TA_C","original_VPD_hPa","original_TA_QC","original_VPD_QC")))
 if len(risks)!=63 or not set(p1)|set(platform)<=set(risks):
  raise ValueError("Stage90 risk keys lost any P1 / original RH plateau timepoint")
 for k in p1:
  if risks[k]["source_risk_categories"]!="P1_HISTORICAL_HOLD":
   raise ValueError("Stage90 original P1 source HOLD category drift")
 for k in platform:
  if risks[k]["source_risk_categories"]!="RH_SATURATION_PLATFORM_HOLD":
   raise ValueError("Stage90 original RH plateau source HOLD category drift")
 holds={}
 for k,r in p1.items():holds[k]=("P1",r)
 for k,r in platform.items():holds[k]=("PLATFORM",r)
 if len(holds)!=56 or any(k in approved for k in holds):
  raise ValueError("56 historical HOLD source HH unexpectedly in 1675 research approved overlay")
 tally=Counter((site,typ) for (site,t),(typ,r) in holds.items())
 if tally!=EXPECT:raise ValueError("56 source P1/plateau per-site cohort drift "+str(tally))
 needed=defaultdict(set)
 for site,t in holds:
  for j in range(-4,5):needed[site].add(shift(t,j))
 source={}
 scanned_sha={}
 for site,(release,expectedsha) in SITE_FILES.items():
  folder=root/site/"forcing"/"raw"/("AMF_"+site+"_FLUXNET_"+release)
  if not folder.is_dir() or folder.is_symlink():raise ValueError("original site raw folder missing "+site)
  candidates=[p for p in folder.iterdir() if re.fullmatch(
    "AMF_"+re.escape(site)+r"_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",p.name,re.I)]
  if len(candidates)!=1 or not candidates[0].is_file() or candidates[0].is_symlink():
   raise ValueError("original site-native FLUXMET source file ambiguous "+site)
  checksum=sha(candidates[0])
  if checksum!=expectedsha:raise ValueError("original Stage05 source SHA drift "+site)
  scanned_sha[site]=checksum
  found={}
  with candidates[0].open("r",encoding="utf-8-sig",newline="") as h:
   rd=csv.DictReader(h)
   columns=rd.fieldnames or []
   if len(columns)!=len(set(columns)) or not {
     "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(columns):
    raise ValueError("source original FLUXMET native column drift "+site)
   for r in rd:
    t=r["TIMESTAMP_START"]
    if t in needed[site]:
     if t in found:raise ValueError("duplicate source native time "+site+"/"+t)
     found[t]=r
  source[site]=found
  if any((site,t) in holds and t not in found for t in needed[site]):
   raise ValueError("original HOLD source center HH missing "+site)
 summary=[]
 contexts=[]
 counts=Counter()
 bysite=defaultdict(Counter)
 for (site,t),(typ,h) in sorted(holds.items()):
  org=source[site][t];prev=risks[(site,t)]
  T,V=n(org["TA_F"]),n(org["VPD_F"])
  sourceRH=rh(T,V)
  esrh=rh(n(org["TA_ERA"]),n(org["VPD_ERA"]))
  if (org["TA_F_QC"]!=prev["original_TA_QC"] or
      org["VPD_F_QC"]!=prev["original_VPD_QC"] or
      (T is None)!=(n(prev["original_TA_C"]) is None) or
      (V is None)!=(n(prev["original_VPD_hPa"]) is None) or
      (T is not None and abs(T-n(prev["original_TA_C"]))>.002) or
      (V is not None and abs(V-n(prev["original_VPD_hPa"]))>.002) or
      prev["prior_1675_research_overlay_present"]!="False" or
      prev["source_data_status"]!="ORIGINAL_NATIVE_VERIFIED"):
   raise ValueError("exact historical 56 source values/QC status drift "+site+"/"+t)
  rr=[]
  for j in range(-4,5):
   nt=shift(t,j);r=source[site].get(nt)
   if r is None:continue
   rt,rv=n(r["TA_F"]),n(r["VPD_F"])
   currentRH=rh(rt,rv)
   rr.append((j,r,currentRH))
   contexts.append(dict(site=site,center_native=t,risk_type=typ,
    native_time=nt,relative_minutes=j*30,
    source_T_C=r["TA_F"],source_T_QC=r["TA_F_QC"],
    source_VPD_hPa=r["VPD_F"],source_VPD_QC=r["VPD_F_QC"],
    source_derived_RH_pct=fmt(currentRH),source_RH_field_pct=r.get("RH",""),
    source_processed_ERA_T_C=r["TA_ERA"],
    source_processed_ERA_derived_RH_pct=fmt(rh(n(r["TA_ERA"]),n(r["VPD_ERA"])))))
  left=[x for x in rr if x[0]<0 and x[1]["VPD_F_QC"]=="0" and x[2] is not None and 1<=x[2]<=100]
  right=[x for x in rr if x[0]>0 and x[1]["VPD_F_QC"]=="0" and x[2] is not None and 1<=x[2]<=100]
  L=max(left,key=lambda x:x[0]) if left else None
  R=min(right,key=lambda x:x[0]) if right else None
  both=bool(L and R)
  spread=abs(L[2]-R[2]) if both else None
  surrounding=[x[2] for x in rr if x[2] is not None and 0<=x[2]<=100]
  nnear=sum(x[2]>=99.5 for x in rr if x[2] is not None and 0<=x[2]<=100)
  originalRH=n(org.get("RH"))
  measured_RH_extreme=originalRH is not None and originalRH>=99.5
  derived_physical=sourceRH is not None and 0<=sourceRH<=100
  physical_problem=sourceRH is not None and not 0<=sourceRH<=100
  if not derived_physical:
   cls="SOURCE_DERIVED_RH_NONPHYSICAL_OR_UNASSESSABLE_KEEP_HOLD"
  elif typ=="PLATFORM":
   cls=("PLATFORM_NEAR_SATURATION_SOURCE_ORIGIN_REVIEW_KEEP_HOLD"
        if measured_RH_extreme or sourceRH>=99.5 else
        "PLATFORM_HISTORICAL_FLAG_BUT_INSTANT_RH_NOT_99_5_KEEP_HOLD")
  elif both:
   cls="P1_TWO_ORIGINAL_VPD_QC0_PHYSICAL_DONORS_SENSITIVITY_ONLY_KEEP_HOLD"
  else:
   cls="P1_NO_TWO_SIDED_SOURCE_VPD_QC0_HUMIDITY_ANCHORS_KEEP_HOLD"
  counts[cls]+=1;bysite[site][typ]+=1
  if both:bysite[site]["two_sided"]+=1
  if physical_problem:bysite[site]["nonphysical"]+=1
  if measured_RH_extreme:bysite[site]["RH_extreme"]+=1
  summary.append(dict(site=site,native_time=t,risk_type=typ,
   original_hold_reason=h.get("hold_reason",""),hold_policy=h.get("action",""),
   platform_label=h.get("platform",""),
   original_reported_platform_RH_pct=h.get("original_RH_pct",""),
   source_original_T_C=org["TA_F"],source_T_QC=org["TA_F_QC"],
   source_original_VPD_hPa=org["VPD_F"],source_VPD_QC=org["VPD_F_QC"],
   source_derived_RH_pct=fmt(sourceRH),source_RH_field_pct=org.get("RH",""),
   source_processed_ERA_T_C=org["TA_ERA"],
   source_processed_ERA_VPD_hPa=org["VPD_ERA"],
   source_processed_ERA_derived_RH_pct=fmt(esrh),
   left_nearest_source_VPD_QC0_time=L[1]["TIMESTAMP_START"] if L else "",
   left_nearest_source_QC0_derived_RH_pct=fmt(L[2]) if L else "",
   right_nearest_source_VPD_QC0_time=R[1]["TIMESTAMP_START"] if R else "",
   right_nearest_source_QC0_derived_RH_pct=fmt(R[2]) if R else "",
   two_sided_QC0_VPD_RH_physical_donors_within_2h=str(both),
   nearest_donor_RH_difference_pct=fmt(spread),
   surrounding_native_RH_max_pct=fmt(max(surrounding) if surrounding else None),
   surrounding_native_RH_min_pct=fmt(min(surrounding) if surrounding else None),
   surrounding_RH_ge_99_5_HH=nnear,
   original_source_numeric_RH_physical=str(derived_physical),
   P1_source_T_VPD_RH_nonphysical=str(physical_problem),
   prior_1675_research_overlay_overlap="False",
   source_science_preliminary_class=cls,
   final_science_HOLD_status="HOLD_UNCHANGED_NEEDS_SOURCE_PROVENANCE_SCIENTIFIC_REVIEW"))
 if len(summary)!=56 or len({(r["site"],r["native_time"]) for r in summary})!=56:
  raise ValueError("historical P1/plateau exact 56 independent source HH not conserved")
 out.mkdir(exist_ok=False)
 fsummary=out/"stage96_P1_46_RH_PLATFORM_10_ORIGINAL_SOURCE_FOCUSED_SCIENCE_REVIEW.csv"
 fcontext=out/"stage96_56_HH_PLUS_MINUS_2H_NATIVE_T_VPD_QC_RH_SOURCE_CONTEXT.csv"
 fsite=out/"stage96_THREE_SITE_P1_PLATFORM_COUNTS.csv"
 fmanifest=out/"stage96_P1_PLATFORM_HISTORICAL_SCIENCE_HOLD_MANIFEST.json"
 rows=[dict(site=site,P1_HOLD=bysite[site]["P1"],PLATFORM_HOLD=bysite[site]["PLATFORM"],
   two_sided_source_VPD_QC0_RH_donors=bysite[site]["two_sided"],
   original_source_derived_RH_nonphysical=bysite[site]["nonphysical"],
   original_RH_field_ge_99_5=bysite[site]["RH_extreme"],research_overlay_overlap=0)
  for site in SITE_FILES]
 csvwrite(fsummary,FOCUS,summary)
 csvwrite(fcontext,CTX,contexts)
 csvwrite(fsite,SITE_SUM,rows)
 manifest=dict(stage=96,original_source_sites=3,
   distinct_original_HOLD_source_HH=56,
   P1_HOLD_unchanged_HH=46,RH_platform_HOLD_unchanged_HH=10,
   previously_approved_1675_source_overlap=0,
   original_source_SHA256_by_site=scanned_sha,
   protected_main_1675_research_overlay_SHA256=PREV_SHA,
   Stage90_original_63_risk_source_SHA256=sha(f90),
   science_screen_counts=dict(counts),
   direct_source_automatically_approved_HH=0,
   P1_platform_HOLDs_overridden_HH=0,
   explicit_original_source_QC_retained=True,
   source_processed_ERA_not_independent_tower_RH=True,
   release_gate="BLOCKED_P1_46_PLATFORM_10_SEPARATE_SOURCE_AND_PROCESSING_POLICY",
   original_and_QC_unmodified=True,main_1675_unmodified=True,
   DATM_CIME_unmodified=True,Slurm_submitted=0,
   output_SHA256={p.name:sha(p) for p in (fsummary,fcontext,fsite)})
 fmanifest.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 print("STAGE96 SUCCESS | original P1 46 + RH saturation platform 10 source-native 56 HH source SHA verified; NO REPAIR/NO FORCING WRITES")
 print("STAGE96 CLASSIFICATIONS",json.dumps(dict(counts),sort_keys=True))
 print("STAGE96 SITE site P1 platform twoSidedSourceQC0VPD physBad sourceRHge99.5 researchOverlap")
 for row in rows:
  print("STAGE96 SITE",row["site"],row["P1_HOLD"],row["PLATFORM_HOLD"],
    row["two_sided_source_VPD_QC0_RH_donors"],
    row["original_source_derived_RH_nonphysical"],
    row["original_RH_field_ge_99_5"],row["research_overlay_overlap"])
 print("STAGE96 P1_REASONS",json.dumps(dict(Counter(r["original_hold_reason"] for r in summary if r["risk_type"]=="P1")),sort_keys=True))
 print("STAGE96 PLATFORM_LABELS",json.dumps(dict(Counter(r["platform_label"] for r in summary if r["risk_type"]=="PLATFORM")),sort_keys=True))
 print("STAGE96 SOURCE_SAMPLE site native type T/QC VPD/QC originalRH sourceERA_RH QC0TwoSided decision")
 for row in summary:
  print("STAGE96 SOURCE",row["site"],row["native_time"],row["risk_type"],
   row["source_original_T_C"]+"/"+row["source_T_QC"],
   row["source_original_VPD_hPa"]+"/"+row["source_VPD_QC"],
   row["source_derived_RH_pct"],row["source_processed_ERA_derived_RH_pct"],
   row["two_sided_QC0_VPD_RH_physical_donors_within_2h"],
   row["source_science_preliminary_class"])
 print("STAGE96 RELEASE_GATE",manifest["release_gate"])
 print("STAGE96_REPORTS="+str(out))
 print("STAGE96 READONLY | ORIGINAL/QC/MAIN1675/STAGE89/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

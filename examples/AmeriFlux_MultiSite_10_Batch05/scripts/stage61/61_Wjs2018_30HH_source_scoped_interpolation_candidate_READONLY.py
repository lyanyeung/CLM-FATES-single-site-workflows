#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage61: physically bounded, source/QC-protected
30-HH US-Wjs March 2018 INTERPOLATION RESEARCH CANDIDATE ONLY.
No new scientific approval: do NOT merge these 30 into Stage56 approved 174.
Original TA preserved, original QC0 source RH anchors at local native
2018-03-11 19:00 (100%) and 2018-03-12 10:30 (92.127%).
No original source, prior 174, official forcing, CIME, DATM or Slurm writes.
"""
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

SITE="US-Wjs"
LEFT="201803111900"
RIGHT="201803121030"
FIRST="201803111930"
LAST="201803121000"
DATA_COLS=(
 "site","native_time","scope","original_TA_F_C","original_TA_F_QC",
 "original_VPD_F_hPa","original_VPD_F_QC","original_VPD_F_MDS_hPa",
 "original_VPD_F_MDS_QC","original_RH_source_field",
 "original_source_ERA_VPD_hPa","independent_ERA5L_RH_pct",
 "linear_QC0_RH_candidate_pct","linear_QC0_VPD_candidate_hPa",
 "delta_candidate_minus_original_VPD_hPa",
 "original_QC0_left","original_QC0_right","RH_interpolation_method",
 "independent_RH_inside_30HH_validated","user_science_approval",
 "versioned_174_inclusion","production_DATM_permission")
EDGE_COLS=("site","before_native","after_native","before_VPD_hPa",
 "after_VPD_hPa","delta_VPD_hPa","abs_jump_gt2hPa","abs_jump_gt4hPa")

def parse(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid native timestamp "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")

def times(a,b):
 lo,hi=parse(a),parse(b)
 sec=(hi-lo).total_seconds()
 if sec<0 or sec%1800:raise ValueError("invalid native halfhour window")
 return [(lo+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M") for i in range(int(sec//1800)+1)]

def n(v):
 try:
  x=float(v)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None

def sat(t):
 if t is None or not -80<=t<=60:raise ValueError("unphysical TA_F source")
 return 6.112*math.exp(17.67*t/(243.5+t))

def rh(t,v):
 return 100*(1-v/sat(t))

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
 return h.hexdigest()

def load(path):
 if path.is_symlink() or not path.is_file():raise ValueError("verified upstream source missing "+str(path))
 with path.open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  if not rd.fieldnames or len(set(rd.fieldnames))!=len(rd.fieldnames):
   raise ValueError("upstream original CSV duplicate/missing headings")
  rows=list(rd)
  if any(None in r or any(v is None for v in r.values()) for r in rows):
   raise ValueError("upstream original source CSV malformed")
 return rows

def writer(path,columns,rows):
 with path.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=columns,extrasaction="raise")
  w.writeheader()
  w.writerows(rows)

def selftest():
 assert len(times(FIRST,LAST))==30 and len(times(LEFT,RIGHT))==32
 assert (parse(RIGHT)-parse(LEFT)).total_seconds()/3600==15.5
 assert abs(sat(0)*(1-100/100))<1e-10
 assert rh(-.230,6.222)<0
 assert abs(rh(-.057,0)-100)<1e-9
 print("STAGE61 SELF-TEST PASS | exact 30HH source interpolation, original 174 protected, scientific approval NO, no original writes")

def run():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage60-dir",type=Path)
 p.add_argument("--stage58-dir",type=Path)
 p.add_argument("--stage56-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage60_dir,a.stage58_dir,a.stage56_dir,a.out)):
  p.error("require --stage60-dir --stage58-dir --stage56-dir --out")
 d60,d58,d56,out=(x.expanduser().resolve() for x in (a.stage60_dir,a.stage58_dir,a.stage56_dir,a.out))
 if not all(x.is_dir() for x in (d60,d58,d56)) or not out.parent.is_dir() or out.exists():
  p.error("source report folders must exist and --out must be NEW")
 if any(out==d or out in d.parents or d in out.parents for d in (d60,d58,d56)):
  p.error("never write inside prior report directories")
 f60=d60/"stage60_49HH_original_VPD_F_MDS_vs_VPD_F_and_weather.csv"
 f58=d58/"stage58_30HH_FOUR_RESEARCH_HUMIDITY_METHODS_UNAPPROVED.csv"
 f56=d56/"stage56_VERSIONED_174_approved_RH_VPD_native_overlay.csv"
 m60=json.loads((d60/"stage60_manifest.json").read_text())
 m58=json.loads((d58/"stage58_manifest.json").read_text())
 m56=json.loads((d56/"stage56_manifest.json").read_text())
 rows60,rows58,rows56=load(f60),load(f58),load(f56)
 if (len(rows60)!=49 or len(rows58)!=30 or len(rows56)!=174 or
     m60.get("output_sha256",{}).get(f60.name)!=sha(f60) or
     m60.get("stage58_original30_sha256")!=sha(f58) or
     m60.get("stage56_original174_sha256")!=sha(f56) or
     m60.get("original_2018_HOLD_HH")!=30 or
     m60.get("original_2018_HOLD_MDS_QC_distribution")!={"1":30} or
     m60.get("original_2018_HOLD_VPD_equals_MDS_within_0p002_HH")!=30 or
     m60.get("original_2018_HOLD_original_negative_implied_RH_HH")!=4 or
     m60.get("original_2018_HOLD_MDS_negative_implied_RH_HH")!=4 or
     m58.get("outputs_sha256",{}).get(f58.name)!=sha(f58) or
     m58.get("scientific_approvals_new")!=0 or
     m56.get("outputs_sha256",{}).get(f56.name)!=sha(f56) or
     m56.get("versioned_total_approved_HH")!=174):
  raise ValueError("source-QC, stage60/58/56 SHA or population gate failed")
 original={r["native_time"]:r for r in rows60}
 prior={r["native_time"]:r for r in rows58}
 alltimes=times(LEFT,RIGHT)
 if len(original)!=49 or len(prior)!=30 or set(prior)!=set(alltimes[1:-1]):
  raise ValueError("30 exact held native HH not matched")
 if any(r.get("site")==SITE and r.get("native_time") in prior for r in rows56):
  raise ValueError("existing 174 overlaps original 2018 HOLD")
 L,R=original[LEFT],original[RIGHT]
 if any(x["original_VPD_F_QC"]!="0" or x["TA_F_QC"]!="0" for x in (L,R)):
  raise ValueError("original source RH anchor QC0 changed")
 lr,rr=n(L["original_source_RH_pct"]),n(R["original_source_RH_pct"])
 if lr is None or rr is None or not 0<=lr<=100 or not 0<=rr<=100:
  raise ValueError("original RH anchor fields missing")
 if abs(lr-100)>.001 or abs(rr-92.127)>.001:
  raise ValueError("original RH anchor science values drift")
 if abs(rh(n(L["TA_F_C"]),n(L["original_VPD_F_hPa"]))-lr)>.07 or abs(
     rh(n(R["TA_F_C"]),n(R["original_VPD_F_hPa"]))-rr)>.07:
  raise ValueError("original QC0 anchor physical RH/T/VPD changed")
 candidates=[]
 joined={LEFT:n(L["original_VPD_F_hPa"]),RIGHT:n(R["original_VPD_F_hPa"])}
 neg_count=0
 for t in alltimes[1:-1]:
  orig=original[t]
  trial=prior[t]
  T,V,M=n(orig["TA_F_C"]),n(orig["original_VPD_F_hPa"]),n(orig["original_VPD_F_MDS_hPa"])
  if (orig["phase"]!="HOLD_2018" or orig["original_VPD_F_QC"]!="1" or
      orig["original_VPD_F_MDS_QC"]!="1" or orig["TA_F_QC"]!="0" or
      n(orig["original_source_RH_pct"]) is not None or
      T is None or V is None or M is None or abs(M-V)>.002 or
      abs(V-n(trial["original_VPD_hPa"]))>.002):
   raise ValueError("original exact 30-HH source MDS/QC/observations changed "+t)
  neg_count+=int(rh(T,V)<0)
  frac=(parse(t)-parse(LEFT)).total_seconds()/(parse(RIGHT)-parse(LEFT)).total_seconds()
  targetrh=lr+(rr-lr)*frac
  new=sat(T)*(1-targetrh/100)
  if not 0<=new<=sat(T) or abs(targetrh-n(trial["linear_RH_pct"]))>1e-6 or abs(
      new-n(trial["linear_VPD_hPa"]))>1e-6:
   raise ValueError("Stage58 independent saved research interpolation not reproducible "+t)
  joined[t]=new
  candidates.append(dict(site=SITE,native_time=t,
   scope="2018_30HH_SOURCE_MDS_INVALID_SCIENCE_HOLD",
   original_TA_F_C=orig["TA_F_C"],original_TA_F_QC=orig["TA_F_QC"],
   original_VPD_F_hPa=orig["original_VPD_F_hPa"],original_VPD_F_QC=orig["original_VPD_F_QC"],
   original_VPD_F_MDS_hPa=orig["original_VPD_F_MDS_hPa"],original_VPD_F_MDS_QC=orig["original_VPD_F_MDS_QC"],
   original_RH_source_field=orig["original_source_RH_pct"],
   original_source_ERA_VPD_hPa=orig["source_VPD_ERA_hPa"],
   independent_ERA5L_RH_pct=trial["independent_ERA5Land_RH"],
   linear_QC0_RH_candidate_pct=f"{targetrh:.9f}",
   linear_QC0_VPD_candidate_hPa=f"{new:.10f}",
   delta_candidate_minus_original_VPD_hPa=f"{new-V:.10f}",
   original_QC0_left=LEFT,original_QC0_right=RIGHT,
   RH_interpolation_method="15p5h_LINEAR_NATIVE_RH_FROM_TWO_ORIGINAL_QC0_ENDS_PRESERVE_TA",
   independent_RH_inside_30HH_validated="NO",
   user_science_approval="PENDING_NOT_APPROVED",
   versioned_174_inclusion="NO",
   production_DATM_permission="NO"))
 if len(candidates)!=30 or neg_count!=4:
  raise ValueError("exact original 30 HH and 4 physically impossible MDS VPD not conserved")
 edges=[]
 for a,b in zip(alltimes,alltimes[1:]):
  va,vb=joined[a],joined[b]
  diff=vb-va
  edges.append(dict(site=SITE,before_native=a,after_native=b,
   before_VPD_hPa=f"{va:.10f}",after_VPD_hPa=f"{vb:.10f}",
   delta_VPD_hPa=f"{diff:.10f}",abs_jump_gt2hPa=int(abs(diff)>2),
   abs_jump_gt4hPa=int(abs(diff)>4)))
 maxjump=max(abs(float(x["delta_VPD_hPa"])) for x in edges)
 if len(edges)!=31 or any(int(x["abs_jump_gt2hPa"]) for x in edges):
  raise ValueError("research-only candidate has new local jump >2 hPa")
 # All approval/source/read-only checks are complete before creating any outputs.
 out.mkdir(exist_ok=False)
 fc=out/"stage61_Wjs2018_EXACT_30HH_UNAPPROVED_RH_LINEAR_INTERPOLATION_CANDIDATES.csv"
 fe=out/"stage61_Wjs2018_ALL31_ADJACENT_BOUNDARY_PAIRS_RESEARCH.csv"
 writer(fc,DATA_COLS,candidates)
 writer(fe,EDGE_COLS,edges)
 manifest=dict(
  original_HOLD_2018_HH=30,original_MDS_VPDQC1_HH=30,
  original_negative_RH_HH=4,
  source_RH_QC0_left_original_pct=lr,source_RH_QC0_right_original_pct=rr,
  candidate_RH_method="Linear interpolation between source QC0 RH endpoints",
  candidate_RH_not_observed_inside_HOLD=True,
  science_approved_new_HH=0,science_status="30HH_PRESERVED_HOLD_UNAPPROVED_CANDIDATE",
  previously_approved_versioned_HH=174,possible_combined_HH_IF_LATER_APPROVED=204,
  merged_204_overlay_written=False,
  original_174_unchanged=True,original_2018_HOLD_unchanged=True,
  actual_ERA5L_used_only_as_reference=True,
  max_candidate_adjacent_VPD_jump_hPa=maxjump,
  approved_for_production_DATM=False,original_sources_written=False,slurm_jobs_submitted=0,
  input_sha256={"stage60_source_QC":sha(f60),"stage58_full_30HH":sha(f58),"stage56_174":sha(f56)},
  output_sha256={fc.name:sha(fc),fe.name:sha(fe)})
 (out/"stage61_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("STAGE61 SUCCESS | 30 MDS-invalid US-Wjs original HH | LINEAR RH RESEARCH CANDIDATE ONLY | no new scientific approval")
 print("STAGE61 BOUNDARIES 31 MAX_ABS_ADJACENT_VPD_JUMP",f"{maxjump:.8f}","GT2=0")
 print("STAGE61 PREVIOUS_APPROVED_OVERLAY=174 UNCHANGED | CANDIDATE=30_UNAPPROVED | MERGED204=NO")
 print("STAGE61 ANCHORS",LEFT,"RH",f"{lr:.3f}",RIGHT,"RH",f"{rr:.3f}","SPAN_HOURS=15.5")
 print("native time | TA_F C | original=MDS VPD hPa | interpolated RH pct | trial VPD hPa | source ERA VPD hPa | external ERA5L RH pct")
 for z in candidates:
  print("STAGE61 CANDIDATE",z["native_time"],"|",z["original_TA_F_C"],"|",z["original_VPD_F_hPa"],
   "|",z["linear_QC0_RH_candidate_pct"],"|",z["linear_QC0_VPD_candidate_hPa"],
   "|",z["original_source_ERA_VPD_hPa"],"|",z["independent_ERA5L_RH_pct"])
 print("STAGE61_REPORTS="+str(out))
 print("STAGE61 NO ORIGINAL/174/HOLD/DATM/SLURM CHANGES")
if __name__=="__main__":
 run()

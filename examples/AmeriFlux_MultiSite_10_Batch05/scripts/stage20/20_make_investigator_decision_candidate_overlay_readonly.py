#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage20 — user-directed humidity/VPD replacement candidates.

Reads ORIGINAL Stage18 SHA-verified extracts; creates NEW candidate-only CSV/JSON.
Does not edit original FLUXMET, DATM, cases, forcing, source QC, or Slurm.
User decisions:
 G01: 26 native original WCr RH~0 -> processed source ERA RH, T_F retained, recompute VPD.
 G03: 34 source-RH-present native HH including BEFORE/P1/AFTER transition ->
      original RH and selected T_F; recalc VPD, conserve original QC.
 G05: 26 flagged native Vcm low-RH QC0 HH -> processed source ERA RH,
      preserve selected T_F/QC0; recalc VPD.
 G06: 23 flagged native Vcm low-RH QC0 HH -> processed source ERA RH,
      preserve selected T_F/QC0; recalc VPD.
 G06 supplemental: 8 native source RH~0.3 QC1/MDS HH are separately
      flagged candidate provenance to honor ALL source RH<1% replacements;
      selected MDS air T retained while VPD is rederived from the user-chosen
      source ERA RH. Original MDS VPD retained in the audit for comparison.
 G02/G04/G07: original RH missing, processed ERA RH nonphysical or <=1%:
      no inferred repair. Print evidence holds.
 Every suggested VPD obeys VPD=es_water(T_F)*(1-RH_target/100).
 This diagnostic assumes processed source ERA is acceptable reference only in
 user-selected candidate zones, NOT verified separately against ERA5-Land.
"""
import argparse,csv,json,math,hashlib
from pathlib import Path
from collections import Counter

SOURCE_COLS=("site","time_native","is_P1","TA_F_C","VPD_F_hPa",
             "TA_F_QC","VPD_F_QC","RH_original_pct","TA_ERA_C",
             "VPD_ERA_hPa","ERA_RH_Magnus_water_pct")
GROUPS={
 "G01_WCr_Aug2025":("US-WCr","202508251300","202508260130",26),
 "G03_Vcm_Jan2007":("US-Vcm","200701162200","200701171430",34),
 "G05_Vcm_Nov2024":("US-Vcm","202411211900","202411222000",26),
 "G06_Vcm_Oct2025":("US-Vcm","202510131200","202510141100",31),
}
HOLDS={
 "G02_Vcm_Dec2007":("US-Vcm","200712152100","200712160600",19),
 "G04_Vcm_Feb2008":("US-Vcm","200802060130","200802060800",12),
 "G07_Vcp_Jan2011":("US-Vcp","201101010700","201101010800",3),
}
FIELDS=("site","time_native","decision_group","decision_scope",
 "TA_F_C_original","TA_F_QC_original","VPD_F_hPa_original",
 "VPD_F_QC_original","RH_original_pct","TA_ERA_C",
 "VPD_ERA_hPa","ERA_RH_derived_pct","candidate_RH_pct",
 "candidate_VPD_hPa_with_original_TA","delta_VPD_hPa",
 "candidate_source","candidate_decision","original_data_unchanged")
KEEP_FIELDS=("site","time_native","group","TA_F_QC","VPD_F_QC",
             "RH_original_pct","ERA_RH_Magnus_water_pct","VPD_F_hPa",
             "reason","decision")
def val(x):
 try:
  v=float(x)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except (ValueError,TypeError):pass
 return None
def es(t):
 if t is None or not -80<=t<=60:return None
 return 6.112*math.exp(17.67*t/(t+243.5))
def rho(t,v):
 s=es(t)
 return 100*(1-v/s) if s is not None and v is not None else None
def readcsv(p,req):
 if not p.is_file() or p.is_symlink():raise ValueError("source read-only report missing "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  if not set(req).issubset(rd.fieldnames or []):raise ValueError("missing report columns")
  rows=list(rd)
 if any(None in x or any(y is None for y in x.values()) for x in rows):raise ValueError("malformed original row")
 return rows
def finddata(src):
 meta=json.loads((src/"stage18_summary.json").read_text())
 if meta.get("P1_episodes")!=39 or meta.get("P1_original_HH")!=176 or meta.get("context_rows")!=775:
  raise ValueError("Stage18 original SHA-verified input summary mismatch")
 rows=readcsv(src/"stage18_all_p1_original_6hour_context.csv",SOURCE_COLS)
 if len(rows)!=775:raise ValueError("original context unexpected cohort")
 ix={}
 for row in rows:
  k=row["site"],row["time_native"]
  if k in ix:raise ValueError("duplicate original half hour "+str(k))
  ix[k]=row
 return ix
def overlay(ix):
 repairs=[];holds=[];warnings=[];counts=Counter()
 for group,(site,start,end,expected) in GROUPS.items():
  entries=sorted((r for (s,t),r in ix.items() if s==site and start<=t<=end),
                 key=lambda r:r["time_native"])
  selected=[]
  for r in entries:
   is_p1=(r["is_P1"]=="1")
   orig_rh=val(r["RH_original_pct"])
   if group=="G03_Vcm_Jan2007":
    # Every native HH with source RH, including QC0, QC1 and QC2 transition.
    if orig_rh is None:raise ValueError("G03 source native RH missing")
    scope="ALL_NATIVE_SOURCE_RH_INCLUDING_TRANSITION"
   elif group=="G06_Vcm_Oct2025" and not is_p1:
    # Eight original RH≈0.3% samples occur during selected MDS QC1/1.
    # User explicitly approved replacing *all* these low source RH records.
    # Create separate QC1 provenance candidate, with VPD recomputed at
    # selected QC1 T to ensure the RH/VPD pair stays self-consistent.
    # Do NOT mislabel revised MDS VPD as original measured QC0.
    if (orig_rh is not None and 0<=orig_rh<1 and
        r["TA_F_QC"]=="1" and r["VPD_F_QC"]=="1"):
     scope="ORIGINAL_SOURCE_RH_LT1_QC1_MDS_RECONSTRUCT_PER_USER"
     counts["G06_QC1_low_RH_original_reconstructed"]+=1
    else:
     continue
   else:
    if not is_p1:continue
    if r["TA_F_QC"]!="0" or r["VPD_F_QC"]!="0":
     raise ValueError("candidate group flagged native target must be measured QC0/0")
    scope="P1_FLAGGED_MEASURED_HH_ONLY"
   t=val(r["TA_F_C"]);old=val(r["VPD_F_hPa"]);e=val(r["ERA_RH_Magnus_water_pct"])
   if t is None or old is None or e is None:raise ValueError("missing native candidate numeric source")
   if group=="G03_Vcm_Jan2007":
    target=orig_rh
    src_name="ORIGINAL_NATIVE_RH_FIELD"
   else:
    target=e
    src_name="SOURCE_PROCESSED_ERA_RH_FROM_ORIGINAL_TA_ERA_VPD_ERA"
   if target is None or not 0<=target<=100:
    raise ValueError("selected source RH not physically allowed "+group+" "+r["time_native"])
   s=es(t)
   if s is None:raise ValueError("native tower selected T out of formula range")
   new=s*(1-target/100)
   if not 0<=new<=s+1e-9:raise ValueError("candidate re-computed VPD not physical")
   if abs(rho(t,new)-target)>1e-9:
    raise ValueError("candidate RH/VPD consistency error")
   rec=dict(site=site,time_native=r["time_native"],decision_group=group,
      decision_scope=scope,TA_F_C_original=r["TA_F_C"],
      TA_F_QC_original=r["TA_F_QC"],VPD_F_hPa_original=r["VPD_F_hPa"],
      VPD_F_QC_original=r["VPD_F_QC"],RH_original_pct=r["RH_original_pct"],
      TA_ERA_C=r["TA_ERA_C"],VPD_ERA_hPa=r["VPD_ERA_hPa"],
      ERA_RH_derived_pct=r["ERA_RH_Magnus_water_pct"],
      candidate_RH_pct=round(target,7),
      candidate_VPD_hPa_with_original_TA=round(new,7),
      delta_VPD_hPa=round(new-old,7),
      candidate_source=src_name,
      candidate_decision="USER_DIRECTED_CANDIDATE_NOT_APPLIED",
      original_data_unchanged="TRUE")
   repairs.append(rec);selected.append(rec)
  if group=="G06_Vcm_Oct2025":
   if len(selected)!=31:raise ValueError("G06 exact 23 QC0 + 8 QC1 raw low-RH source flags missing")
   if counts["G06_QC1_low_RH_original_reconstructed"]!=8:
    raise ValueError("G06 exact 8 QC1 source RH reconstructed count missing")
  elif len(selected)!=expected:
   raise ValueError("expected original native subgroup count "+group+" got "+str(len(selected)))
  counts[group]=len(selected)
 for group,(site,start,end,count) in HOLDS.items():
  part=sorted((r for (s,t),r in ix.items() if s==site and start<=t<=end and r["is_P1"]=="1"),
              key=lambda r:r["time_native"])
  if len(part)!=count:raise ValueError("source hold count differs "+group)
  for r in part:
   original=val(r["RH_original_pct"])
   if original is not None:raise ValueError("supposed missing source RH unexpectedly present "+group)
   e=val(r["ERA_RH_Magnus_water_pct"])
   status="NEGATIVE_ERA_DERIVED_RH" if e is not None and e<0 else "ERA_DERIVED_RH_UNDER_1"
   holds.append(dict(site=site,time_native=r["time_native"],group=group,
     TA_F_QC=r["TA_F_QC"],VPD_F_QC=r["VPD_F_QC"],
     RH_original_pct=r["RH_original_pct"],
     ERA_RH_Magnus_water_pct=r["ERA_RH_Magnus_water_pct"],
     VPD_F_hPa=r["VPD_F_hPa"],reason="Original RH absent; "+status,
     decision="HOLD_NO_REPLACEMENT_SOURCE"))
  counts[group+"_HOLD"]=len(part)
 if len(repairs)!=117:raise ValueError("approved scope 117 primary candidate HH mismatch")
 if len(holds)!=34:raise ValueError("expected G02/G04/G07 34 missing-RH holds")
 if len({(x["site"],x["time_native"]) for x in repairs})!=117:
  raise ValueError("duplicate original target half-hours")
 return repairs,holds,counts
def selftest():
 for t,rh in [(10,40),(-15,90),(20,70)]:
  s=es(t);v=s*(1-rh/100)
  assert abs(rho(t,v)-rh)<1e-10
 assert rho(-13.087,2.514)<0
 print("STAGE20 SELF-TEST PASS | original source RH and processed ERA RH -> coherent VPD(T_F), exact immutable user decision scopes")
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage18-dir",type=Path)
 ap.add_argument("--output-dir",type=Path)
 args=ap.parse_args()
 if args.self_test:selftest();return
 if args.stage18_dir is None or args.output_dir is None:
  ap.error("requires --stage18-dir and --output-dir")
 src=args.stage18_dir.expanduser().resolve()
 dest=args.output_dir.expanduser().resolve()
 if not src.is_dir() or dest.exists() or not dest.parent.is_dir() or dest==src or dest in src.parents or src in dest.parents:
  ap.error("existing immutable Stage18 source + NEW disjoint target dir required")
 repairs,holds,counts=overlay(finddata(src))
 dest.mkdir(exist_ok=False)
 for name,fields,records in (
  ("stage20_approved_scope_candidate_TA_RH_VPD.csv",FIELDS,repairs),
  ("stage20_original_RH_missing_and_QC1_context_holds.csv",KEEP_FIELDS,holds)):
  with (dest/name).open("x",encoding="utf-8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
 summary={
   "source_original_sha_verified_by":"Stage18 original immutable source hash validation",
   "base_report":str(src),
   "original_FLUXMET_written":False,
   "forcing_written":False,"slurm_job_submitted":False,
   "candidate_only":True,
   "retained_selected_TA_F_exactly":True,
   "original_QC_flags_overwritten":False,
   "actual_ERA5_independent_downloaded":False,
   "processed_ERA_provenance":"Original source columns TA_ERA, VPD_ERA; not verified independently as ERA5-Land",
   "scope_counts":dict(counts),"candidate_rows":len(repairs),
   "unresolved_rows":len(holds),
   "G03_original_RH_native_including_transitions":True,
   "G05_G06_original_tower_T_preserved":True,
   "G06_extra_QC1_source_RH_low_reconstructed_separately":True}
 with (dest/"stage20_summary.json").open("x",encoding="utf-8") as f:
  json.dump(summary,f,indent=2,sort_keys=True)
 print("STAGE20 SCIENCE DECISION COUNTS",json.dumps(dict(counts),sort_keys=True),flush=True)
 for group in GROUPS:
  aa=[r for r in repairs if r["decision_group"]==group]
  print("STAGE20_CANDIDATE",group,"COUNT",len(aa),flush=True)
  for r in (aa[:2]+aa[-2:]):
   print("  ",r["time_native"],"TA_F",r["TA_F_C_original"],
     "originalVPD",r["VPD_F_hPa_original"],
     "candidateRH",r["candidate_RH_pct"],
     "candidateVPD",r["candidate_VPD_hPa_with_original_TA"],flush=True)
 print("STAGE20 SUMMARY proposed_candidate_HH=117 source_RH_unresolved_HH=34 forcing_written=0 reports="+str(dest),flush=True)
 print("NO ORIGINAL FLUXMET / EXISTING FORCING / ORIGINAL QC / MODEL / SLURM WRITES")
if __name__=="__main__":main()

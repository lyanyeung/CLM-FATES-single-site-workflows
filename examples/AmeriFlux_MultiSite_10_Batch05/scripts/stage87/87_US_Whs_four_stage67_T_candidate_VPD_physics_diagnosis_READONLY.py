#!/usr/bin/env python3
"""Batch05 Stage87 exact science exception diagnosis, read-only.

Stage86 says four of 51 independent Stage67 user-approved US-Whs
temperature-only interpolations are nonphysical when combined with
UNMODIFIED ORIGINAL VPD. Resolve evidence before a temperature/forcing
merge; do not silently repair or promote to production.

Checks Stage84 overlay SHA, Stage86 ten-site release-gate report, Stage67
candidate/manifest SHA and original immutable Stage05 source-native CSV
SHA. For all 51 candidate half-hours, calculate original/source-ERA RH,
candidate T + original VPD RH and two explicitly counterfactual VPDs.
For the four scientifically inconsistent times, output full ±3-hour
original native T,VPD,QC, RH, processed-source ERA and any original
measured-QC0 physical RH anchors. All outputs are new HOME audits only.
"""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from datetime import datetime,timedelta

SITE="US-Whs"
RAW_SHA="653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca"
ZIP_SHA="0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767"
APPROVED_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
RELEASE="AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1"
REPORT_FIELDS=("site","native_time","source_run_id","original_T_C","source_T_QC",
 "candidate_T_C","original_VPD_hPa","source_VPD_QC",
 "original_RH_pct","candidate_T_with_original_VPD_RH_pct",
 "source_ERA_T_C","source_ERA_VPD_hPa","source_ERA_RH_pct",
 "candidate_VPD_hPa_IF_keeping_original_RH",
 "candidate_VPD_hPa_IF_using_processed_source_ERA_RH",
 "original_implied_absolute_vapor_pressure_hPa",
 "candidate_implied_absolute_vapor_pressure_hPa",
 "candidate_implied_RH_nonphysical","reason","production_disposition")
CONTEXT_FIELDS=("flagged_center_native","native_time","relative_offset_minutes",
 "original_T_C","TA_F_QC","original_VPD_hPa","VPD_F_QC",
 "original_RH_pct","source_ERA_T_C","source_ERA_VPD_hPa",
 "source_ERA_RH_pct","original_measured_VPD_QC0_RH_physical")
def hashfile(p):
 h=hashlib.sha256()
 with p.open("rb") as file:
  for b in iter(lambda:file.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def number(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def es(T):
 if T is None or T < -80 or T>60:return None
 return 6.112*math.exp(17.67*T/(T+243.5))
def RH(T,V):
 e=es(T)
 if e is None or V is None:return None
 return 100*(1-V/e)
def fmt(x):return "" if x is None else f"{x:.9f}"
def dt(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("unexpected source native HH "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def shift(t,i):
 return (dt(t)+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
def read(p,columns):
 if not p.is_file() or p.is_symlink():raise ValueError("source/report file missing/symlink "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as file:
  r=csv.DictReader(file);names=r.fieldnames or []
  if len(names)!=len(set(names)) or not set(columns).issubset(names):
   raise ValueError("source/report field schema drift "+str(p))
  rows=list(r)
 if any(None in row or any(v is None for v in row.values()) for row in rows):
  raise ValueError("source/report malformed CSV "+str(p))
 return rows
def keyed(rows):
 result={}
 for row in rows:
  key=(row["site"],row["native_time"])
  if key in result:raise ValueError("duplicate original native site/time "+str(key))
  result[key]=row
 return result
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as file:
  w=csv.DictWriter(file,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert len(RAW_SHA)==len(ZIP_SHA)==len(APPROVED_SHA)==64
 assert RH(0,7)<0 and abs(RH(0,6.112))<1e-9
 assert shift("201205260000",-1)=="201205252330"
 assert 0<=RH(20,2)<=100
 print("STAGE87 SELF-TEST PASS | 51 Stage67 Whs T candidates, exact four negative/invalid T+unchanged-VPD physics issues source context, read-only")

def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument("--self-test",action="store_true")
 a.add_argument("--stage67",type=Path)
 a.add_argument("--stage84",type=Path)
 a.add_argument("--stage86",type=Path)
 a.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 a.add_argument("--out",type=Path)
 opt=a.parse_args()
 if opt.self_test:selftest();return
 if any(x is None for x in (opt.stage67,opt.stage84,opt.stage86,opt.out)):
  a.error("exact successful Stage67/84/86 report dirs plus NEW output required")
 d67,d84,d86,out=(x.expanduser().resolve() for x in
                   (opt.stage67,opt.stage84,opt.stage86,opt.out))
 root=opt.sites_root.expanduser().resolve()
 rawdir=root/SITE/"forcing"/"raw"/RELEASE
 if (not all(d.is_dir() for d in (d67,d84,d86,rawdir)) or
     out.exists() or not out.parent.is_dir() or
     any(out==d or out in d.parents or d in out.parents
         for d in (d67,d84,d86,rawdir))):
  a.error("prior reports or source original unavailable, NEW disjoint output required")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (hashfile(f84)!=APPROVED_SHA or
     m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=APPROVED_SHA):
  raise ValueError("Stage84 actually approved 1675 source hash mismatch")
 approved=keyed(read(f84,["site","native_time"]))
 if len(approved)!=1675:raise ValueError("Stage84 approved source keys not unique")
 f67=d67/"stage67_USER_SELECTED_TA_INTERPOLATION_CANDIDATE_ONLY.csv"
 h67=d67/"stage67_UNREPAIRABLE_QC_BRACKET_HOLDS.csv"
 e67=d67/"stage67_ALL30_TARGETED_QC_TRANSITIONS_AND_DECISIONS.csv"
 m67=json.loads((d67/"stage67_manifest.json").read_text())
 if (m67.get("original_ZIP_SHA256")!=ZIP_SHA or
     m67.get("final_candidate_repaired_TA_HH")!=51 or
     any(m67.get("output_sha256",{}).get(f.name)!=hashfile(f) for f in (f67,h67,e67))):
  raise ValueError("Stage67 full 51 candidate science provenance changed")
 candidate=keyed(read(f67,["site","native_time","source_run_id",
    "original_source_TA_F_C","candidate_TA_F_C","source_QC_unchanged",
    "source_VPD_F_hPa_unchanged","source_VPD_F_QC_unchanged"]))
 holds=read(h67,["decision"])
 edges=read(e67,["decision"])
 if (len(candidate)!=51 or len(holds)!=10 or len(edges)!=30 or
     any(k[0]!=SITE for k in candidate) or
     set(candidate)&set(approved)):
  raise ValueError("Stage67 51 source T candidate / 10 pass-original / 30 edges / no overlap changed")
 f86=d86/"stage86_FINAL_TEN_SITE_RESEARCH_QC_RELEASE_GATES.json"
 risk86=d86/"stage86_FOCUSED_SOURCE_SCIENCE_AND_RELEASE_RISKS.csv"
 m86=json.loads(f86.read_text(encoding="utf-8"))
 if (m86.get("stage")!=86 or
     m86.get("stage67_T_candidate_original_VPD_physics_issues")!=4 or
     m86.get("Stage67_separate_approved_TA_candidate_HH")!=51 or
     m86.get("Stage67_T_candidate_overlapping_main_overlay_HH")!=0 or
     m86.get("final_versioned_research_approved_HH")!=1675 or
     m86.get("current_overlay_SHA256")!=APPROVED_SHA or
     m86.get("current_overlay_corrected_physics_issues")!=0):
  raise ValueError("Stage86 actual operator success + four T/VPD science issues not verified")
 risk=read(risk86,["site","native_time","category"])
 stage86_bad={(x["site"],x["native_time"]) for x in risk if
     x["category"]=="STAGE67_T_CANDIDATE_VPD_PHYSICS_ISSUE"}
 if len(stage86_bad)!=4 or not stage86_bad.issubset(candidate):
  raise ValueError("Stage86 4 original Stage67 physics exception keys absent/duplicated")
 pat=re.compile(r"AMF_US-Whs_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",re.I)
 p=[x for x in rawdir.iterdir() if pat.fullmatch(x.name)]
 if len(p)!=1 or p[0].is_symlink() or not p[0].is_file() or hashfile(p[0])!=RAW_SHA:
  raise ValueError("Stage05 immutable Whs original CSV strict SHA mismatch")
 wanted={shift(t,j) for _,t in candidate for j in range(-6,7)}
 original={}
 with p[0].open("r",encoding="utf-8-sig",newline="") as file:
  reader=csv.DictReader(file)
  hdr=reader.fieldnames or []
  if len(hdr)!=len(set(hdr)) or not {
    "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
    "TA_ERA","VPD_ERA"}.issubset(hdr):
   raise ValueError("Stage05 original FLUXMET CSV fields drift")
  for r in reader:
   t=r["TIMESTAMP_START"]
   if t in wanted:
    if t in original:raise ValueError("duplicate Whs original native HH "+t)
    original[t]=r
 if any(k[1] not in original for k in candidate):
  raise ValueError("some of 51 stage67 original native source HH absent")
 rows=[];bad=[];context=[]
 for key,c in sorted(candidate.items()):
  t=key[1];o=original[t]
  T,V=num(o["TA_F"]),num(o["VPD_F"])
  oldT=num(c["original_source_TA_F_C"])
  newT=num(c["candidate_TA_F_C"])
  oldV=num(c["source_VPD_F_hPa_unchanged"])
  if (any(x is None for x in (T,V,oldT,newT,oldV)) or
      abs(T-oldT)>0.002 or abs(V-oldV)>0.002 or
      o["TA_F_QC"]!=c["source_QC_unchanged"] or
      o["VPD_F_QC"]!=c["source_VPD_F_QC_unchanged"]):
   raise ValueError("Stage67 candidate-original T/VPD/native QC provenance drift "+t)
  originalRH=RH(T,V)
  candidateRH=RH(newT,V)
  eraT,eraV=num(o["TA_ERA"]),num(o["VPD_ERA"])
  eraRH=RH(eraT,eraV)
  if candidateRH is None:
   isbad=True;issue="NONFINITE_CANDIDATE_T_ORIGINAL_VPD_RH"
  elif candidateRH<0:
   isbad=True;issue="CANDIDATE_T_ORIGINAL_VPD_NEGATIVE_RH"
  elif candidateRH>100:
   isbad=True;issue="CANDIDATE_T_ORIGINAL_VPD_RH_GT_100"
  else:
   isbad=False;issue="NUMERICALLY_PHYSICAL_NOT_INDEPENDENTLY_VALIDATED"
  preserveRH_vpd=(es(newT)*(1-originalRH/100)
     if originalRH is not None and 0<=originalRH<=100 and es(newT) is not None else None)
  proxy_vpd=(es(newT)*(1-eraRH/100)
     if eraRH is not None and 0<=eraRH<=100 and es(newT) is not None else None)
  row=dict(site=SITE,native_time=t,source_run_id=c["source_run_id"],
    original_T_C=o["TA_F"],source_T_QC=o["TA_F_QC"],
    candidate_T_C=c["candidate_TA_F_C"],
    original_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
    original_RH_pct=fmt(originalRH),
    candidate_T_with_original_VPD_RH_pct=fmt(candidateRH),
    source_ERA_T_C=o["TA_ERA"],source_ERA_VPD_hPa=o["VPD_ERA"],
    source_ERA_RH_pct=fmt(eraRH),
    candidate_VPD_hPa_IF_keeping_original_RH=fmt(preserveRH_vpd),
    candidate_VPD_hPa_IF_using_processed_source_ERA_RH=fmt(proxy_vpd),
    original_implied_absolute_vapor_pressure_hPa=fmt(
      es(T)-V if es(T) is not None else None),
    candidate_implied_absolute_vapor_pressure_hPa=fmt(
      es(newT)-V if es(newT) is not None else None),
    candidate_implied_RH_nonphysical=str(isbad),reason=issue,
    production_disposition=("BLOCK_COMBINED_T_VPD_UNTIL_RH_OR_VPD_METHOD_VALIDATED"
      if isbad else "TA_CANDIDATE_SEPARATE_VERSIONED_RESEARCH_ONLY_NOT_FORCE_APPROVED"))
  rows.append(row)
  if not isbad:continue
  bad.append(row)
  for j in range(-6,7):
   tt=shift(t,j);obs=original.get(tt)
   if obs is None:
    context.append(dict(flagged_center_native=t,native_time=tt,
      relative_offset_minutes=j*30,original_T_C="",TA_F_QC="",
      original_VPD_hPa="",VPD_F_QC="",original_RH_pct="",
      source_ERA_T_C="",source_ERA_VPD_hPa="",source_ERA_RH_pct="",
      original_measured_VPD_QC0_RH_physical="SOURCE_TIMESTAMP_MISSING"))
    continue
   origRH=RH(num(obs["TA_F"]),num(obs["VPD_F"]))
   erRH=RH(num(obs["TA_ERA"]),num(obs["VPD_ERA"]))
   qc0_meas=(obs["VPD_F_QC"]=="0" and origRH is not None and 1<=origRH<=100)
   context.append(dict(flagged_center_native=t,native_time=tt,
     relative_offset_minutes=j*30,original_T_C=obs["TA_F"],TA_F_QC=obs["TA_F_QC"],
     original_VPD_hPa=obs["VPD_F"],VPD_F_QC=obs["VPD_F_QC"],
     original_RH_pct=fmt(origRH),source_ERA_T_C=obs["TA_ERA"],
     source_ERA_VPD_hPa=obs["VPD_ERA"],source_ERA_RH_pct=fmt(erRH),
     original_measured_VPD_QC0_RH_physical=str(qc0_meas)))
 computed_bad={(x["site"],x["native_time"]) for x in bad}
 if computed_bad!=stage86_bad or len(bad)!=4 or len(rows)!=51:
  raise ValueError("original four Stage86 physics exceptions did not reproduce exactly")
 # These four physics failures are independent of the separate source-T
 # anomalous seven and 46 P1 /10 platform holds. No hidden approval.
 out.mkdir(exist_ok=False)
 allfile=out/"stage87_ALL51_WHS_STAGE67_CANDIDATE_T_ORIGINAL_VPD_PHYSICS.csv"
 badfile=out/"stage87_FOUR_WHS_NONPHYSICAL_T_PLUS_VPD_LOCAL_EXCEPTIONS.csv"
 contextfile=out/"stage87_FOUR_WHS_3H_NATIVE_ORIGINAL_CONTEXT.csv"
 write(allfile,REPORT_FIELDS,rows)
 write(badfile,REPORT_FIELDS,bad)
 write(contextfile,CONTEXT_FIELDS,context)
 manifest=dict(stage=87,site=SITE,stage67_candidates_verified=51,
  stage67_original_vpd_nonphysical=4,exact_same_four_as_stage86=True,
  stage67_current_1675_overlay_collisions=0,
  original_Whs_FLUXMET_CSV_SHA256=RAW_SHA,
  stage67_provenance_ZIP_SHA256=ZIP_SHA,latest_1675_overlay_SHA256=APPROVED_SHA,
  stage86_release_gate="BLOCKED",source_QC_unchanged=True,
  previous_1675_overlay_unchanged=True,production_DATM_CIME_unchanged=True,
  Slurm_submitted=0,output_SHA256={x.name:hashfile(x) for x in
      (allfile,badfile,contextfile)})
 (out/"stage87_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 print("STAGE87 SUCCESS | Stage67 51/51 source T candidates verified, 4 original Tcandidate+unchanged VPD RH NONPHYSICAL")
 print("STAGE87 PHYSICS_EXCEPTIONS match Stage86 exact 4/4; no 1675-overlay overlap")
 print("STAGE87 EXCEPTION native originalTA QC candidateTA originalVPD QC RH_original RH_candidate RH_source_ERA VPD_keeping_old_RH VPD_using_source_ERA_RH")
 for b in bad:
  print("STAGE87 EXCEPTION",b["native_time"],b["original_T_C"],b["source_T_QC"],
    b["candidate_T_C"],b["original_VPD_hPa"],b["source_VPD_QC"],
    b["original_RH_pct"],b["candidate_T_with_original_VPD_RH_pct"],
    b["source_ERA_RH_pct"],
    b["candidate_VPD_hPa_IF_keeping_original_RH"],
    b["candidate_VPD_hPa_IF_using_processed_source_ERA_RH"])
 print("STAGE87 SOURCE_CONTEXT | original +/-3h per each flagged center")
 for c in context:
  print("STAGE87 CONTEXT",c["flagged_center_native"],c["native_time"],
    c["original_T_C"],c["TA_F_QC"],c["original_VPD_hPa"],c["VPD_F_QC"],
    c["original_RH_pct"],c["source_ERA_RH_pct"],
    "measured_QC0_RH="+c["original_measured_VPD_QC0_RH_physical"])
 print("STAGE87 NO_DIRECT_PRODUCTION_REPAIR | COUNTERFACTUAL_VPD_COLUMNS_ARE_DIAGNOSTICS_ONLY")
 print("STAGE87_REPORTS="+str(out))
 print("STAGE87 SOURCE/QC/PRIOR1675/STAGE67_T/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

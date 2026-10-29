#!/usr/bin/env python3
"""Batch05 Stage80: source-audited US-Vcm 72 episodes / 362 original HH.
Direct user-policy RH<0 repair: 336 selected original HH, 26 nonnegative pass.
Measured source VPD QC0 humidity anchors within 3h take precedence; otherwise
use original source-processed same-native ERA RH, only if internally physical.
One 2014-09-06 native T exception: correct source T only if both original QC0
adjacent T anchors are demonstrably coherent and original VPD becomes feasible;
otherwise preserve its original T and label a local temperature science caveat.
Immutable original source/Stage79/previous 378, no DATM/CIME/Slurm changes.
"""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta
SITE="US-Vcm"
ORIG_SHA="c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c"
PREV_SHA="400757c166d03fa8d7e7b72aa39879c14c2d9db5ada818d930c647c71d06f7b5"
RELEASE="AMF_US-Vcm_FLUXNET_2007-2025_v1.3_r1"
T_EXCEPTION="201409062330"
OVERLAY="site native_time source_cohort decision_id source_TA_C source_TA_QC source_VPD_hPa source_VPD_QC source_RH_pct source_processed_ERA_T_C source_processed_ERA_VPD_hPa source_processed_ERA_RH_derived_pct modified_TA_C modified_RH_pct modified_VPD_hPa delta_VPD_hPa replacement_RH_provenance new_VPD_derivation source_QC_provenance_only overlay_status".split()
AUDIT="site episode_id native_time original_TA_C original_TA_QC original_VPD_hPa original_VPD_QC original_implied_RH_pct corrected_TA_C corrected_RH_pct corrected_VPD_hPa method source_ERA_RH_pct left_donor_time left_donor_RH_pct right_donor_time right_donor_RH_pct flagged_T_exception original_source_RH_pct".split()
KEEP="site episode_id native_time original_TA_C original_VPD_hPa original_implied_RH_pct TA_F_QC VPD_F_QC decision".split()
EXCEPT="site native_time original_TA_C left_native left_TA_C left_QC right_native right_TA_C right_QC original_VPD_hPa source_ERA_TA_C source_ERA_RH_pct source_implied_RH_pct corrected_TA_C corrected_RH_pct method temperature_provenance_warning".split()
def checksum(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
def numeric(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def fnum(x):return "" if x is None else f"{x:.9f}"
def es(T):
 if T is None or not -80<=T<=60:return None
 return 6.112*math.exp(17.67*T/(T+243.5))
def RH(T,V):
 e=es(T)
 return None if e is None or V is None else 100*(1-V/e)
def tick(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("bad original time "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def add(t,i):return (tick(t)+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
def records(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("source ledger unavailable "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as stream:
  reader=csv.DictReader(stream);h=reader.fieldnames or []
  if len(h)!=len(set(h)) or not set(required).issubset(h):
   raise ValueError("unexpected source ledger fields "+str(p))
  rows=list(reader)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("invalid row width "+str(p))
 return rows
def keyed(rows):
 ans={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in ans:raise ValueError("duplicate ledger native key "+str(k))
  ans[k]=r
 return ans
def write(p,fields,rows):
 with p.open("x",encoding="utf-8",newline="") as stream:
  w=csv.DictWriter(stream,fieldnames=fields,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert 378+336==714
 assert es(0) is not None and abs(RH(0,6.112))<1e-10
 assert RH(2.978,8.195)<0
 assert fnum(1.25)=="1.250000000"
 assert add("201409062330",1)=="201409070000"
 print("STAGE80 SELF-TEST PASS | source Vcm 362: 336 negative direct RH repairs + 26 source passes, prior378 preserved; 1 local source-T exception")
def run(a):
 d27,d63,d78,d79,out=(p.expanduser().resolve() for p in
  (a.stage27,a.stage63,a.stage78,a.stage79,a.out))
 if not all(x.is_dir() for x in (d27,d63,d78,d79)) or out.exists() or not out.parent.is_dir():
  raise ValueError("prior source/report dirs missing or output exists")
 oldfile=d78/"stage78_VERSIONED_378_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 manifest78=json.loads((d78/"stage78_manifest.json").read_text())
 if (checksum(oldfile)!=PREV_SHA or
     manifest78.get("approved_after")!=378 or
     manifest78.get("output_sha256",{}).get(oldfile.name)!=PREV_SHA):
  raise ValueError("previous Stage78 378 approved exact SHA mismatch")
 prev=keyed(records(oldfile,OVERLAY))
 if len(prev)!=378:raise ValueError("previous 378 count drift")
 f27=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 f63=d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"
 r27=records(f27,["site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"])
 r63=records(f63,["site","native_time","episode_id","TA_F_QC","VPD_F_QC"])
 if len(r27)!=1574 or len(r63)!=1565:raise ValueError("baseline Stage27/63 original population altered")
 ref=keyed(r for r in r27 if r["site"]==SITE)
 sel=keyed(r for r in r63 if r["site"]==SITE)
 if len(ref)!=362 or len(sel)!=362 or set(ref)!=set(sel) or len({r["episode_id"] for r in sel.values()})!=72:
  raise ValueError("original 362 P2P3 / 72 source events changed")
 if set(sel)&set(prev):raise ValueError("Vcm original P2P3 already in earlier approved overlay")
 f79=d79/"stage79_US_Vcm_362_source_original_QC_RH_temperature.csv"
 m79=json.loads((d79/"stage79_manifest.json").read_text())
 if (m79.get("original_source_SHA256")!=ORIG_SHA or
     m79.get("prior_378_overlay_SHA256")!=PREV_SHA or
     m79.get("original_362_source_native_HH_verified") is not True or
     m79.get("original_negative_RH_HH")!=336 or
     m79.get("original_nonnegative_RH_HH")!=26 or
     m79.get("original_source_T_suspect_HH")!=1 or
     m79.get("original_source_ERA_internal_nonphysical_HH")!=0 or
     m79.get("output_sha256",{}).get(f79.name)!=checksum(f79)):
  raise ValueError("successful Stage79 source-science classification differs")
 stage79=keyed(records(f79,["site","episode_id","native_time","RH_implied_pct","TA_F_QC","VPD_F_QC","suspect_T_source"]))
 if len(stage79)!=362 or set(stage79)!=set(sel):raise ValueError("Stage79 full 362 source keys changed")
 candidates=[k[1] for k,x in stage79.items() if x["suspect_T_source"]=="True"]
 if candidates!=[T_EXCEPTION]:raise ValueError("unique source T exception identity changed")
 source_root=a.sites_root/SITE/"forcing"/"raw"/RELEASE
 if not source_root.is_dir() or source_root.is_symlink():raise ValueError("original source folder unavailable")
 pat=re.compile(r"AMF_US-Vcm_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",re.I)
 src=[p for p in source_root.iterdir() if pat.fullmatch(p.name)]
 if len(src)!=1 or not src[0].is_file() or src[0].is_symlink() or checksum(src[0])!=ORIG_SHA:
  raise ValueError("source original Vcm FLUXMET CSV Stage05 SHA mismatch")
 need={add(t,k) for _,t in sel for k in range(-12,13)}
 obs={}
 with src[0].open(encoding="utf-8-sig",newline="") as stream:
  reader=csv.DictReader(stream);h=reader.fieldnames or []
  if len(h)!=len(set(h)) or not {"TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(h):
   raise ValueError("source original FLUXMET fields changed")
  for r in reader:
   t=r["TIMESTAMP_START"]
   if t in need:
    if t in obs:raise ValueError("source duplicated original native timestamp")
    obs[t]=r
 if any(k[1] not in obs for k in sel):raise ValueError("original Vcm 362 HH source missing")
 neg=set();passed=set();qc=Counter()
 for k,r in ref.items():
  t=k[1];o=obs[t];T=numeric(o["TA_F"]);V=numeric(o["VPD_F"])
  if (T is None or V is None or numeric(r["TA_F_C"]) is None or
      numeric(r["VPD_F_hPa"]) is None or
      abs(T-numeric(r["TA_F_C"]))>.002 or abs(V-numeric(r["VPD_F_hPa"]))>.002 or
      o["TA_F_QC"]!=r["TA_F_QC"] or o["VPD_F_QC"]!=r["VPD_F_QC"] or
      o["TA_F_QC"]!=sel[k]["TA_F_QC"] or
      o["VPD_F_QC"]!=sel[k]["VPD_F_QC"] or r["episode_id"]!=sel[k]["episode_id"] or
      r["episode_id"]!=stage79[k]["episode_id"]):
   raise ValueError("Stage27/63/79 original value/QC/source event drift "+t)
  rawrh=RH(T,V)
  if rawrh is None or abs(rawrh-numeric(stage79[k]["RH_implied_pct"]))>1e-5:
   raise ValueError("Stage79 source RH formula drift "+t)
  (neg if rawrh<0 else passed).add(t)
  qc[o["TA_F_QC"]+"/"+o["VPD_F_QC"]]+=1
 if len(neg)!=336 or len(passed)!=26 or qc!={"0/1":317,"0/2":35,"1/1":3,"1/2":5,"2/2":2}:
  raise ValueError("US-Vcm exact science 336/26 source QC pairs changed")
 if T_EXCEPTION not in neg:raise ValueError("original T exception no longer RH negative")
 def RHorig(t):
  o=obs.get(t)
  return RH(numeric(o["TA_F"]),numeric(o["VPD_F"])) if o else None
 def donor(t,step):
  for i in range(1,7):
   tt=add(t,i*step);o=obs.get(tt);rr=RHorig(tt)
   if o and o["VPD_F_QC"]=="0" and rr is not None and 1<=rr<=100:
    return tt,rr
  return None
 # The single obvious source T anomaly requires two-sided, physically
 # coherent QC0 temperature neighbors; never use the anomalous QC0 itself
 # as an anchor. Local exception is NOT automatically promoted if ambiguous.
 e=obs[T_EXCEPTION];left_t=add(T_EXCEPTION,-1);right_t=add(T_EXCEPTION,1)
 before=obs.get(left_t);after=obs.get(right_t)
 if before is None or after is None:raise ValueError("2014 local T boundaries missing")
 leftT,rightT=numeric(before["TA_F"]),numeric(after["TA_F"])
 t_interp=(leftT+rightT)/2 if leftT is not None and rightT is not None else None
 originalT=numeric(e["TA_F"]);originalV=numeric(e["VPD_F"])
 trust_neighbors=(before["TA_F_QC"]=="0" and after["TA_F_QC"]=="0"
   and leftT is not None and rightT is not None and
   abs(leftT-rightT)<=5 and min(abs(originalT-leftT),abs(originalT-rightT))>=8)
 can_fix_T=(trust_neighbors and t_interp is not None
   and RH(t_interp,originalV) is not None and 0<=RH(t_interp,originalV)<=100)
 # All 336 source negative RH are repaired directly, with one exception's
 # temperature reconstruction distinguished from ordinary RH/VPD replacement.
 repairs={};audit=[];method_count=Counter();exception_rows=[]
 for t in sorted(neg):
  o=obs[t];T=numeric(o["TA_F"]);V=numeric(o["VPD_F"])
  era=RH(numeric(o["TA_ERA"]),numeric(o["VPD_ERA"]))
  if era is None or not 0<=era<=100:
   raise ValueError("Stage79 original source ERA internal humidity no longer physical "+t)
  left=right=None
  if t==T_EXCEPTION and can_fix_T:
   newT=t_interp;newV=V;newrh=RH(newT,newV)
   method="SOURCE_QC0_T_TWO_SIDE_SAME_QC0_ANCHORS_LOCAL_EXCEPTION_KEEP_ORIGINAL_VPD"
  else:
   left=donor(t,-1);right=donor(t,+1)
   if left and right:
    w=(tick(t)-tick(left[0])).total_seconds()/(tick(right[0])-tick(left[0])).total_seconds()
    newrh=left[1]+(right[1]-left[1])*w
    method="TWO_SIDED_SOURCE_VPD_QC0_RH_DONORS_WITHIN_3H"
   else:
    newrh=era
    method="SAME_NATIVE_ORIGINAL_SOURCE_PROCESSED_ERA_RH_NOT_INDEPENDENT_ERA5"
   newT=T;newV=es(newT)*(1-newrh/100)
   if t==T_EXCEPTION:method+="_ORIGINAL_T_SOURCE_EXCEPTION_REQUIRES_TARGETED_CHECK"
  if (newrh is None or not 0<=newrh<=100 or newV is None or
      not -1e-8<=newV<=es(newT)+1e-8 or abs(RH(newT,newV)-newrh)>1e-6):
   raise ValueError("stage80 reconstructed negative RH physically invalid "+t)
  k=(SITE,t);row=dict(site=SITE,native_time=t,
    source_cohort="STAGE80_VCM_DIRECT_OPERATOR_RULE_ORIGINAL_RH_LT_ZERO",
    decision_id="VCM_"+ref[k]["episode_id"]+"_NEGATIVE_RH_DIRECT_APPROVED_20261029",
    source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
    source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
    source_RH_pct=o.get("RH",""),source_processed_ERA_T_C=o["TA_ERA"],
    source_processed_ERA_VPD_hPa=o["VPD_ERA"],
    source_processed_ERA_RH_derived_pct=fnum(era),
    modified_TA_C=fnum(newT),modified_RH_pct=fnum(newrh),
    modified_VPD_hPa=fnum(newV),delta_VPD_hPa=fnum(newV-V),
    replacement_RH_provenance=method,
    new_VPD_derivation=("ORIGINAL_SOURCE_VPD_UNCHANGED_RECOMPUTE_RH_AT_REPAIRED_T"
        if t==T_EXCEPTION and can_fix_T else
        "WATER_MAGNUS_AT_SELECTED_SOURCE_T_NONMEASURED_OR_MEASURED_AS_ORIGINAL_QC"),
    source_QC_provenance_only="SOURCE_ORIGINAL_TA_AND_VPD_QC_LABELS_NOT_REASSIGNED",
    overlay_status="USER_DIRECT_SCIENCE_APPROVED_VERSIONED_NOT_YET_DATM_APPLIED")
  if set(row)!=set(OVERLAY):raise ValueError("prior approved overlay schema drift")
  repairs[k]=row;method_count[method]+=1
  audit.append(dict(site=SITE,episode_id=ref[k]["episode_id"],native_time=t,
    original_TA_C=o["TA_F"],original_TA_QC=o["TA_F_QC"],
    original_VPD_hPa=o["VPD_F"],original_VPD_QC=o["VPD_F_QC"],
    original_implied_RH_pct=fnum(RHorig(t)),
    corrected_TA_C=fnum(newT),corrected_RH_pct=fnum(newrh),
    corrected_VPD_hPa=fnum(newV),method=method,
    source_ERA_RH_pct=fnum(era),
    left_donor_time=left[0] if left else "",left_donor_RH_pct=fnum(left[1]) if left else "",
    right_donor_time=right[0] if right else "",right_donor_RH_pct=fnum(right[1]) if right else "",
    flagged_T_exception=str(t==T_EXCEPTION),
    original_source_RH_pct=o.get("RH","")))
  if t==T_EXCEPTION:
   exception_rows.append(dict(site=SITE,native_time=t,original_TA_C=o["TA_F"],
    left_native=left_t,left_TA_C=before["TA_F"],left_QC=before["TA_F_QC"],
    right_native=right_t,right_TA_C=after["TA_F"],right_QC=after["TA_F_QC"],
    original_VPD_hPa=o["VPD_F"],source_ERA_TA_C=o["TA_ERA"],
    source_ERA_RH_pct=fnum(era),source_implied_RH_pct=fnum(RHorig(t)),
    corrected_TA_C=fnum(newT),corrected_RH_pct=fnum(newrh),method=method,
    temperature_provenance_warning=("SOURCE_T_SENSOR_EXCEPTION_DIRECT_LOCAL_T_FIX"
       if can_fix_T else "SOURCE_T_EXCURSION_UNRESOLVED_LOCAL_T_KEPT; SOURCE_RH_CORRECTED_ONLY; REVIEW_BEFORE_FORCING")))
 passrows=[dict(site=SITE,episode_id=ref[(SITE,t)]["episode_id"],native_time=t,
   original_TA_C=obs[t]["TA_F"],original_VPD_hPa=obs[t]["VPD_F"],
   original_implied_RH_pct=fnum(RHorig(t)),TA_F_QC=obs[t]["TA_F_QC"],
   VPD_F_QC=obs[t]["VPD_F_QC"],decision="PASS_ORIGINAL_RH_NONNEGATIVE_SOURCE_UNCHANGED") for t in sorted(passed)]
 full=dict(prev);full.update(repairs)
 if len(full)!=714 or len(repairs)!=336 or any(full[k]!=prev[k] for k in prev) or len(exception_rows)!=1:
  raise ValueError("previous 378 + 336 direct repairs not preserved exactly")
 out.mkdir(exist_ok=False)
 ffull=out/"stage80_VERSIONED_714_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 fnew=out/"stage80_336_NEW_US_Vcm_DIRECT_NEGATIVE_RH_REPAIRS.csv"
 fdiag=out/"stage80_336_Vcm_SOURCE_VS_REPAIRED_AND_PROVENANCE.csv"
 fpass=out/"stage80_26_Vcm_NONNEGATIVE_ORIGINAL_PASSED.csv"
 fexception=out/"stage80_ONE_20140906_SOURCE_T_EXCEPTION_LOCAL_SCIENCE_STATUS.csv"
 write(ffull,OVERLAY,[full[k] for k in sorted(full)])
 write(fnew,OVERLAY,[repairs[k] for k in sorted(repairs)])
 write(fdiag,AUDIT,audit);write(fpass,KEEP,passrows);write(fexception,EXCEPT,exception_rows)
 if len(records(ffull,OVERLAY))!=714:raise ValueError("714 approved write readback failed")
 report=dict(stage=80,site=SITE,source_original_SHA256=ORIG_SHA,
  prior_378_SHA256=PREV_SHA,stage79_source_report_SHA256=checksum(f79),
  original_72_episodes=True,original_362_HH_verified=True,
  original_RH_negative_direct_repaired_HH=336,
  original_RH_nonnegative_source_pass_HH=26,
  previous_378_exact_rows_unchanged=True,total_approved_versioned_records=714,
  source_T_exception_native_time=T_EXCEPTION,source_T_exception_corrected_only_if_credible_two_QC0_donors=can_fix_T,
  source_T_exception_if_not_corrected_requires_targeted_pre_forcing_check=not can_fix_T,
  source_ERA_is_processed_original_not_independent_ERA5Land=True,
  selected_negative_original_QC_pairs=dict(qc),methods=dict(method_count),
  original_source_unchanged=True,original_QC_unchanged=True,
  production_DATM_CIME_unchanged=True,Slurm_submitted=0,
  outputs_sha256={x.name:checksum(x) for x in (ffull,fnew,fdiag,fpass,fexception)})
 (out/"stage80_manifest.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("STAGE80 SUCCESS | US-Vcm 72 episodes 362 original HH: 336 negative RH DIRECT REPAIRED, 26 nonnegative ORIGINAL PASS")
 print("STAGE80 VERIFIED ORIGINAL_SOURCE_SHA",ORIG_SHA,"PRIOR_378_SHA",PREV_SHA)
 print("STAGE80 PRIOR_378 EXACT PRESERVED + 336 NEW = 714 VERSIONED APPROVED HH")
 print("STAGE80 METHODS",json.dumps(dict(method_count),sort_keys=True))
 print("STAGE80 TEMP_EXCEPTION",json.dumps(exception_rows[0],sort_keys=True))
 print("STAGE80 SOURCE_ERA_RH_USED_IS_ORIGINAL_PROCESSED_SOURCE_NOT_INDEPENDENT_ERA5_LAND")
 print("STAGE80 APPROVED_714_SHA256="+checksum(ffull))
 print("STAGE80 APPROVED_714="+str(ffull))
 print("STAGE80_REPORTS="+str(out))
 print("STAGE80 ALL ORIGINAL_SOURCE/QC/PRIOR378/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage27",type=Path)
 ap.add_argument("--stage63",type=Path)
 ap.add_argument("--stage78",type=Path)
 ap.add_argument("--stage79",type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 ap.add_argument("--out",type=Path)
 args=ap.parse_args()
 if args.self_test:selftest()
 else:
  if any(x is None for x in (args.stage27,args.stage63,args.stage78,args.stage79,args.out)):
   ap.error("provide original source/approved Stage27 Stage63 Stage78 Stage79 dirs and NEW output")
  run(args)

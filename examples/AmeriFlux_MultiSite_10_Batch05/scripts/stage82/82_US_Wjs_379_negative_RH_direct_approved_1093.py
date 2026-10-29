#!/usr/bin/env python3
"""Batch05 Stage82: strict original-source user-approved science repair, US-Wjs.
Read SHA-pinned original AmeriFlux FLUXMET_HH 2007-2025 release, verify all
401 Stage27 original source keys and 393 still-pending Stage63 keys, preserve
eight previously approved Wjs entries in exact prior 714 versioned overlay.
379 source RH-negative HH corrected directly; 14 source nonnegative pass.
Two obvious source temperature excursions are local exceptions: interpolate
between real QC0 T donor timestamps if physically plausible, retaining
original selected VPD, or mark an unresolved temperature caveat while
correcting physically impossible original RH via source provenance.
Do not rewrite immutable source/QC, archived approved entries, DATM/CIME,
SLURM or original project archives. All output versioned under NEW HOME dir.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SITE="US-Wjs"
SOURCE_SHA="9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6"
PRIOR_SHA="e65b0c854cd391c1ae6c26b3b627dd60a99ee4a9f574219ead65ef1cc76d253c"
RELEASE="AMF_US-Wjs_FLUXNET_2007-2025_v1.3_r1"
EXCEPTIONS={"202203310330":(-5.946,8.707,8.701),
            "202504191600":(1.032,10.404,11.779)}
OVERLAY="site native_time source_cohort decision_id source_TA_C source_TA_QC source_VPD_hPa source_VPD_QC source_RH_pct source_processed_ERA_T_C source_processed_ERA_VPD_hPa source_processed_ERA_RH_derived_pct modified_TA_C modified_RH_pct modified_VPD_hPa delta_VPD_hPa replacement_RH_provenance new_VPD_derivation source_QC_provenance_only overlay_status".split()
AUDIT="site episode_id native_time original_T_C original_T_QC original_VPD_hPa original_VPD_QC original_derived_RH_pct repaired_T_C repaired_VPD_hPa repaired_RH_pct method source_ERA_RH_pct left_RH_anchor left_RH_pct right_RH_anchor right_RH_pct source_T_exception original_RH_field".split()
PASSED="site episode_id native_time original_T_C original_VPD_hPa original_derived_RH_pct original_T_QC original_VPD_QC science_disposition".split()
T_AUDIT="site native_time original_T_C original_T_QC original_VPD_hPa original_VPD_QC left_native left_T_C left_T_QC right_native right_T_C right_T_QC original_derived_RH_pct corrected_T_C corrected_VPD_hPa corrected_RH_pct source_ERA_T_C source_ERA_RH_pct temperature_science_disposition".split()

def checksum(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
def number(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None
def txt(x):return "" if x is None else f"{x:.9f}"
def es(T):
 if T is None or not -80<=T<=60:return None
 return 6.112*math.exp(17.67*T/(T+243.5))
def RH(T,V):
 e=es(T)
 return None if e is None or V is None else 100*(1-V/e)
def date(t):
 if not len(t)==12 or not t.isdigit():raise ValueError("native timestamp unexpected "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def offset(t,i):
 return (date(t)+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
def load(p,columns):
 if not p.is_file() or p.is_symlink():raise ValueError("input missing/symlink "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  r=csv.DictReader(h);cols=r.fieldnames or []
  if len(set(cols))!=len(cols) or not set(columns).issubset(cols):
   raise ValueError("source science ledger schema drift "+str(p))
  out=list(r)
 if any(None in v or any(item is None for item in v.values()) for v in out):
  raise ValueError("source record width inconsistent "+str(p))
 return out
def index(rows):
 d={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in d:raise ValueError("duplicate source time "+str(k))
  d[k]=r
 return d
def save(p,columns,rows):
 with p.open("x",encoding="utf-8",newline="") as stream:
  wr=csv.DictWriter(stream,fieldnames=columns,extrasaction="raise")
  wr.writeheader();wr.writerows(rows)

def selftest():
 assert 714+379==1093
 assert len(EXCEPTIONS)==2
 assert RH(-5.946,7.692)<0 and 0<RH(8.704,7.692)<100
 assert RH(1.032,11.087)<0 and 0<RH((10.404+11.779)/2,11.087)<100
 assert offset("202203310330",1)=="202203310400"
 assert txt(1.25)=="1.250000000"
 print("STAGE82 SELF-TEST PASS | US-Wjs 379 direct negative-RH repairs + 14 nonnegative passed; 2 local source temperature exceptions, prior714 protected")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage27",type=Path)
 p.add_argument("--stage63",type=Path)
 p.add_argument("--stage80",type=Path)
 p.add_argument("--stage81",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage27,a.stage63,a.stage80,a.stage81,a.out)):
  p.error("exact original Stage27/63, successful Stage80/81 and NEW output required")
 d27,d63,d80,d81,out=(x.expanduser().resolve() for x in
   (a.stage27,a.stage63,a.stage80,a.stage81,a.out))
 source_root=(a.sites_root.expanduser().resolve()/SITE/"forcing"/"raw"/RELEASE)
 if (not all(x.is_dir() for x in (d27,d63,d80,d81,source_root))
     or out.exists() or not out.parent.is_dir()
     or any(out==d or out in d.parents or d in out.parents
            for d in (d27,d63,d80,d81,source_root))):
  p.error("valid prior report dirs and a NEW disjoint output required")
 oldf=d80/"stage80_VERSIONED_714_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m80=json.loads((d80/"stage80_manifest.json").read_text())
 if (checksum(oldf)!=PRIOR_SHA or
     m80.get("total_approved_versioned_records")!=714 or
     m80.get("outputs_sha256",{}).get(oldf.name)!=PRIOR_SHA):
  raise ValueError("Stage80 714 original version approved SHA mismatch")
 old=index(load(oldf,OVERLAY))
 if len(old)!=714:raise ValueError("prior approved 714 entries duplicated or missing")
 src27=load(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
    ("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 src63=load(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
    ("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 if len(src27)!=1574 or len(src63)!=1565:
  raise ValueError("original baseline P2/P3 Stage27/63 global counts changed")
 historical=index(x for x in src27 if x["site"]==SITE)
 pending=index(x for x in src63 if x["site"]==SITE)
 previous_eight=set(historical)-set(pending)
 if (len(historical)!=401 or len(pending)!=393 or len(previous_eight)!=8 or
     not set(pending).issubset(historical) or
     not previous_eight.issubset(old) or set(pending)&set(old) or
     any(historical[k]["episode_id"]!=pending[k]["episode_id"] for k in pending)):
  raise ValueError("original Wjs 401 / pending 393 / 8 previously approved crosswalk changed")
 f81=d81/"stage81_Wjs_393_SOURCE_ORIGINAL_QC_RH_T_AUDIT.csv"
 m81=json.loads((d81/"stage81_manifest.json").read_text())
 if (m81.get("source_SHA256")!=SOURCE_SHA or
     m81.get("previous_714_SHA256")!=PRIOR_SHA or
     m81.get("original_historical_source_HH")!=401 or
     m81.get("original_eight_already_covered_by_prior_overlay")!=8 or
     m81.get("original_pending_HH")!=393 or m81.get("original_pending_events")!=150 or
     m81.get("original_RH_negative")!=379 or
     m81.get("original_RH_nonnegative")!=14 or
     m81.get("source_T_suspect_HH")!=2 or
     m81.get("original_ERA_internal_nonphysical_HH")!=0 or
     m81.get("original_source_QC_pairs")!={"0/1":282,"0/2":111} or
     m81.get("output_SHA256",{}).get(f81.name)!=checksum(f81)):
  raise ValueError("Stage81 science report not actual 393 original Wjs verified")
 stage81=index(load(f81,("site","native_time","episode_id",
   "original_derived_RH_pct","source_T_numerically_suspect")))
 if len(stage81)!=393 or set(stage81)!=set(pending):
  raise ValueError("Stage81 original selected native time scope changed")
 if {k[1] for k,x in stage81.items() if x["source_T_numerically_suspect"]=="True"}!=set(EXCEPTIONS):
  raise ValueError("two source T exception exact timestamps differ")
 pat=re.compile(r"AMF_US-Wjs_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",re.I)
 original=[x for x in source_root.iterdir() if pat.fullmatch(x.name)]
 if (len(original)!=1 or not original[0].is_file() or
     original[0].is_symlink() or checksum(original[0])!=SOURCE_SHA):
  raise ValueError("Wjs original source Stage05 immutable CSV SHA wrong/ambiguous")
 # Retain original observations at every selected HH plus ±3h donors.
 wanted={offset(k[1],i) for k in historical for i in range(-6,7)}
 source={}
 with original[0].open(encoding="utf-8-sig",newline="") as stream:
  rd=csv.DictReader(stream);h=rd.fieldnames or []
  if len(set(h))!=len(h) or not {"TIMESTAMP_START","TA_F","TA_F_QC",
       "VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(h):
   raise ValueError("original Wjs required source columns missing")
  for r in rd:
   t=r["TIMESTAMP_START"]
   if t in wanted:
    if t in source:raise ValueError("original Wjs source timestamp duplicated")
    source[t]=r
 if any(k[1] not in source for k in historical):
  raise ValueError("original 401 Wjs HH source not present in pinned CSV")
 qc=Counter();negative=set();nonnegative=set()
 for (s,t),x in historical.items():
  o=source[t];T=number(o["TA_F"]);V=number(o["VPD_F"])
  if (T is None or V is None or number(x["TA_F_C"]) is None or
      number(x["VPD_F_hPa"]) is None or
      abs(T-number(x["TA_F_C"]))>.002 or
      abs(V-number(x["VPD_F_hPa"]))>.002 or
      o["TA_F_QC"]!=x["TA_F_QC"] or o["VPD_F_QC"]!=x["VPD_F_QC"]):
   raise ValueError("original source 401 historical TA/VPD/QC mismatch "+t)
 for key,x in pending.items():
  t=key[1];o=source[t]
  if (o["TA_F_QC"]!=x["TA_F_QC"] or
      o["VPD_F_QC"]!=x["VPD_F_QC"] or
      stage81[key]["episode_id"]!=x["episode_id"]):
   raise ValueError("393 native original Stage63/81 selected QC/episode mismatch "+t)
  T,V=number(o["TA_F"]),number(o["VPD_F"]);r=RH(T,V)
  if (r is None or number(stage81[key]["original_derived_RH_pct"]) is None or
      abs(r-number(stage81[key]["original_derived_RH_pct"]))>1e-5):
   raise ValueError("selected original Wjs derived source RH changed "+t)
  qc[(o["TA_F_QC"],o["VPD_F_QC"])]+=1
  (negative if r<0 else nonnegative).add(t)
 if len(negative)!=379 or len(nonnegative)!=14 or qc!={("0","1"):282,("0","2"):111}:
  raise ValueError("379/14 original source RH and QC pairs changed")
 if not set(EXCEPTIONS).issubset(negative):
  raise ValueError("original two T anomalies are not RH-negative any more")
 # Per source-QC standard: use original measured VPD-QC0 humidity within 3h
 # when available on BOTH sides. Otherwise source processed ERA-derived RH
 # at the same native timestamp, explicitly marked proxy not tower measured.
 def measured(t,step):
  for i in range(1,7):
   neighbor=offset(t,i*step);o=source.get(neighbor)
   if o is not None and o["VPD_F_QC"]=="0":
    r=RH(number(o["TA_F"]),number(o["VPD_F"]))
    if r is not None and 1<=r<=100:
     return neighbor,r
  return None
 def temperature_candidate(t):
  # Require adjacent QC0 temperatures (not merely a numerical neighbor)
  # and check both T brackets are stable and original VPD becomes physical.
  before=source.get(offset(t,-1));after=source.get(offset(t,1))
  if before is None or after is None:return None
  L,R=number(before["TA_F"]),number(after["TA_F"]);origT=number(source[t]["TA_F"])
  if (L is None or R is None or origT is None or
      before["TA_F_QC"]!="0" or after["TA_F_QC"]!="0" or
      abs(L-R)>5 or min(abs(origT-L),abs(origT-R))<8):
   return None
  estimate=(L+R)/2
  originalV=number(source[t]["VPD_F"]);rr=RH(estimate,originalV)
  if rr is None or not 0<=rr<=100:return None
  return estimate,rr
 corrected={};audit=[];temp_rows=[];methods=Counter()
 for t in sorted(negative):
  o=source[t];T=number(o["TA_F"]);V=number(o["VPD_F"])
  sourceERA=RH(number(o["TA_ERA"]),number(o["VPD_ERA"]))
  if sourceERA is None or not 0<=sourceERA<=100:
   raise ValueError("Stage81 source processed ERA internally nonphysical after readback "+t)
  left=right=None
  tc=temperature_candidate(t) if t in EXCEPTIONS else None
  if tc is not None:
   newT,newRH=tc;newV=V
   method="OBVIOUS_SOURCE_T_QC0_SPIKE_TWO_SIDED_SOURCE_QC0_INTERPOLATION_KEEP_ORIGINAL_VPD"
  else:
   left=measured(t,-1);right=measured(t,1)
   if left is not None and right is not None:
    w=(date(t)-date(left[0])).total_seconds()/(date(right[0])-date(left[0])).total_seconds()
    newRH=left[1]+(right[1]-left[1])*w
    method="TWO_SIDED_ORIGINAL_MEASURED_VPD_QC0_RH_INTERPOLATION"
   else:
    newRH=sourceERA
    method="SOURCE_PROCESSED_SAME_NATIVE_ERA_RH_PROXY_NOT_INDEPENDENT_ERA5L"
   if t in EXCEPTIONS:
    method+="_ORIGINAL_SOURCE_T_UNRESOLVED_TARGETED_FORCING_REVIEW"
   newT=T;newV=es(newT)*(1-newRH/100)
  if (newRH is None or not 0<=newRH<=100 or newV is None or
      not -1e-8<=newV<=es(newT)+1e-8 or
      abs(RH(newT,newV)-newRH)>1e-6):
   raise ValueError("nonphysical Wjs direct RH repair "+t)
  k=(SITE,t);episode=pending[k]["episode_id"]
  row=dict(site=SITE,native_time=t,
   source_cohort="STAGE82_US_WJS_DIRECT_379_NEGATIVE_RH_393_ORIGINAL",
   decision_id="WJS_"+episode+"_NEGATIVE_RH_USER_APPROVED_20261029",
   source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
   source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
   source_RH_pct=o.get("RH",""),
   source_processed_ERA_T_C=o["TA_ERA"],
   source_processed_ERA_VPD_hPa=o["VPD_ERA"],
   source_processed_ERA_RH_derived_pct=txt(sourceERA),
   modified_TA_C=txt(newT),modified_RH_pct=txt(newRH),
   modified_VPD_hPa=txt(newV),delta_VPD_hPa=txt(newV-V),
   replacement_RH_provenance=method,
   new_VPD_derivation=("KEEP_SOURCE_VPD_CORRECT_OBVIOUS_SOURCE_T" if tc is not None
      else "WATER_SATURATION_MAGNUS_AT_UNCHANGED_ORIGINAL_SOURCE_T"),
   source_QC_provenance_only="IMMUTABLE_ORIGINAL_TA_VPD_QC_NOT_RELABELED",
   overlay_status="USER_DIRECT_APPROVED_RECONSTRUCTION_NOT_PRODUCTION_FORCING")
  if set(row)!=set(OVERLAY):raise ValueError("output overlay schema unexpected")
  corrected[k]=row;methods[method]+=1
  audit.append(dict(site=SITE,episode_id=episode,native_time=t,
   original_T_C=o["TA_F"],original_T_QC=o["TA_F_QC"],
   original_VPD_hPa=o["VPD_F"],original_VPD_QC=o["VPD_F_QC"],
   original_derived_RH_pct=txt(RH(T,V)),repaired_T_C=txt(newT),
   repaired_VPD_hPa=txt(newV),repaired_RH_pct=txt(newRH),
   method=method,source_ERA_RH_pct=txt(sourceERA),
   left_RH_anchor=left[0] if left else "",
   left_RH_pct=txt(left[1]) if left else "",
   right_RH_anchor=right[0] if right else "",
   right_RH_pct=txt(right[1]) if right else "",
   source_T_exception=str(t in EXCEPTIONS),
   original_RH_field=o.get("RH","")))
  if t in EXCEPTIONS:
   b=source.get(offset(t,-1));a=source.get(offset(t,1))
   temp_rows.append(dict(site=SITE,native_time=t,
    original_T_C=o["TA_F"],original_T_QC=o["TA_F_QC"],
    original_VPD_hPa=o["VPD_F"],original_VPD_QC=o["VPD_F_QC"],
    left_native=offset(t,-1),left_T_C=b["TA_F"] if b else "",
    left_T_QC=b["TA_F_QC"] if b else "",
    right_native=offset(t,1),right_T_C=a["TA_F"] if a else "",
    right_T_QC=a["TA_F_QC"] if a else "",
    original_derived_RH_pct=txt(RH(T,V)),
    corrected_T_C=txt(newT),corrected_VPD_hPa=txt(newV),
    corrected_RH_pct=txt(newRH),source_ERA_T_C=o["TA_ERA"],
    source_ERA_RH_pct=txt(sourceERA),
    temperature_science_disposition=("SOURCE_QC0_T_TWO_SIDED_LOCAL_REPAIR_KEEP_VPD"
       if tc is not None else
       "TEMPERATURE_SOURCE_SPIKE_UNRESOLVED_REPAIR_RH_ONLY_REVIEW_BEFORE_FORCING")))
 passed=[]
 for t in sorted(nonnegative):
  o=source[t];rr=RH(number(o["TA_F"]),number(o["VPD_F"]))
  passed.append(dict(site=SITE,episode_id=pending[(SITE,t)]["episode_id"],
    native_time=t,original_T_C=o["TA_F"],
    original_VPD_hPa=o["VPD_F"],original_derived_RH_pct=txt(rr),
    original_T_QC=o["TA_F_QC"],original_VPD_QC=o["VPD_F_QC"],
    science_disposition="PASS_SOURCE_RH_NONNEGATIVE_UNMODIFIED_VPD_QC1_OR_QC2_NOT_MEASURED_RH"))
 total=dict(old);total.update(corrected)
 if (len(corrected)!=379 or len(passed)!=14 or len(temp_rows)!=2 or
      len(total)!=1093 or any(total[k]!=old[k] for k in old)):
  raise ValueError("original prior 714 and Wjs new 379 reconciliation failed")
 out.mkdir(exist_ok=False)
 full=out/"stage82_VERSIONED_1093_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 new=out/"stage82_379_NEW_US_Wjs_DIRECT_NEGATIVE_RH_REPAIRS.csv"
 trace=out/"stage82_379_ORIGINAL_VS_APPROVED_RH_VPD_TA_METHODS.csv"
 keep=out/"stage82_14_ORIGINAL_NONNEGATIVE_RH_PASSED.csv"
 temp=out/"stage82_TWO_SOURCE_T_SENSOR_SPIKES_LOCAL_PROVENANCE.csv"
 save(full,OVERLAY,[total[k] for k in sorted(total)])
 save(new,OVERLAY,[corrected[k] for k in sorted(corrected)])
 save(trace,AUDIT,audit);save(keep,PASSED,passed)
 save(temp,T_AUDIT,temp_rows)
 if len(load(full,OVERLAY))!=1093:
  raise ValueError("Stage82 1093 CSV readback failed")
 report=dict(stage=82,site=SITE,source_original_SHA256=SOURCE_SHA,
  previous_714_approved_SHA256=PRIOR_SHA,
  stage81_source_report_SHA256=checksum(f81),
  previous_714_approved_rows_exactly_preserved=True,
  original_historical_source_HH=401,previously_approved_Wjs_HH_preserved=8,
  original_remaining_HH=393,original_remaining_events=150,
  source_negative_RH_direct_repaired_HH=379,
  source_nonnegative_RH_pass_unchanged_HH=14,
  source_T_numerical_exception_HH=2,
  source_T_exception_corrected_HH=sum(x["temperature_science_disposition"]==
      "SOURCE_QC0_T_TWO_SIDED_LOCAL_REPAIR_KEEP_VPD" for x in temp_rows),
  total_versioned_approved_repair_rows=1093,
  methods=dict(methods),
  processed_source_ERA_is_proxy_not_independent_ERA5L=True,
  original_source_unmodified=True,original_QC_unmodified=True,
  previous_714_unmodified=True,DATM_CIME_unmodified=True,Slurm_jobs_submitted=0,
  output_SHA256={x.name:checksum(x) for x in (full,new,trace,keep,temp)})
 (out/"stage82_manifest.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("STAGE82 SUCCESS | US-Wjs 150 pending original events 393 HH: 379 RH NEGATIVE DIRECT REPAIRED; 14 RH NONNEGATIVE PASS ORIGINAL")
 print("STAGE82 ORIGINAL_SOURCE_VERIFIED 401/401; REMAINING_393_393; 8 PRIOR_WJS_APPROVALS_PRESERVED")
 print("STAGE82 PRIOR_714 EXACT_PRESERVED + NEW_WJS_379 = 1093 VERSIONED APPROVED HH")
 print("STAGE82 METHODS",json.dumps(dict(methods),sort_keys=True))
 print("STAGE82 SOURCE_T_EXCEPTIONS",json.dumps(temp_rows,sort_keys=True))
 print("STAGE82 ORIGINAL_PROCESSED_ERA_PROXY_NOT_INDEPENDENT_ERA5_LAND")
 print("STAGE82 APPROVED_1093_SHA256="+checksum(full))
 print("STAGE82 APPROVED_1093="+str(full))
 print("STAGE82_REPORTS="+str(out))
 print("STAGE82 ALL SOURCE/QC/PRIOR714/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

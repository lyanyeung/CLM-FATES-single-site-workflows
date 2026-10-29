#!/usr/bin/env python3
"""Batch05 Stage76 user-directed direct approval US-WCr:
61 Stage75 RH-negative original P2/P3 HH (59 VPD-only, 2 T correction);
one nonnegative original HH pass unchanged. Separate obviously corrupted
2016-10-01 source temperature segment: 08:30,09:30,10:30 extra source HH,
plus 10:00,11:30 already among the 61. Correct these 5 original TA
temperatures in a versioned overlay from local physically credible native
neighbors, keeping original VPD (incl QC2) unchanged. Stage74 previous 259
approved rows and all original FLUXMET/QC protected. 259+64=323 approval
overlay; no Slurm/DATM/CIME. Other intervals passed per operator policy.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter,defaultdict

SITE="US-WCr"
PIN="f13c3a26a051bbe351fe5aa66a2cd7eef3849b33645732810bfc74a34c5e6f75"
SOURCE_ERA_SCIENCE="SOURCE_PROCESSED_ERA_NOT_INDEPENDENT_ERA5_LAND"
T_FIX={
 "201610010830":("201610010800","201610010900"),
 "201610010930":("201610010900","201610011100"),
 "201610011000":("201610010900","201610011100"),
 "201610011030":("201610010900","201610011100"),
 "201610011130":("201610011100","201610011200"),
}
SCHEMA=("site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct",
 "modified_TA_C","modified_RH_pct","modified_VPD_hPa",
 "delta_VPD_hPa","replacement_RH_provenance","new_VPD_derivation",
 "source_QC_provenance_only","overlay_status")
AUD=("site","episode_id","native_time","source_TA_C","source_TA_QC",
 "source_VPD_hPa","source_VPD_QC","original_derived_RH_pct",
 "approved_TA_C","approved_RH_pct","approved_VPD_hPa",
 "scientific_method","left_anchor_native","left_anchor_QC",
 "left_anchor_TA_C","left_anchor_RH_pct","right_anchor_native",
 "right_anchor_QC","right_anchor_TA_C","right_anchor_RH_pct",
 "source_ERA_T_C","source_ERA_VPD_hPa","is_original_62_flagged",
 "decision")
PASS=("site","episode_id","native_time","original_TA_C",
 "original_VPD_hPa","original_RH_pct","science_disposition")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def num(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def fmt(x):return "" if x is None else f"{x:.9f}"
def clock(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid original timestamp "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def sh(t,k):
 return (clock(t)+timedelta(minutes=30*k)).strftime("%Y%m%d%H%M")
def es(T):
 if T is None or not -80<=T<=60:raise ValueError("invalid air temperature")
 return 6.112*math.exp(17.67*T/(T+243.5))
def rh(T,V):
 if T is None or V is None:return None
 return 100*(1-V/es(T))
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("prior source/approval missing "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as handle:
  rd=csv.DictReader(handle);hd=rd.fieldnames or []
  if len(hd)!=len(set(hd)) or not set(required).issubset(hd):
   raise ValueError("prior source schema drift "+str(p))
  rows=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("source CSV malformed")
 return rows
def keyed(rows):
 d={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in d:raise ValueError("duplicate source key "+repr(k))
  d[k]=r
 return d
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as handle:
  w=csv.DictWriter(handle,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert len(T_FIX)==5 and sh("201610011000",2)=="201610011100"
 assert 259+61+3==323
 assert rh(-13.734,2.496)<0 and 0<rh(13.878,2.496)<100
 assert rh(-13.734,4.334)<0 and 0<rh(16.4825,4.334)<100
 assert 11.701+(16.055-11.701)*2/4==13.878
 assert fmt(1.5)=="1.500000000"
 print("STAGE76 SELF-TEST PASS | direct 59 RH/VPD corrections + 2 2016 originally negative RH via temperature repair + 3 obvious source temperature context, no source overwrite")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage63-dir",type=Path)
 p.add_argument("--stage74-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(v is None for v in (a.stage27_dir,a.stage63_dir,a.stage74_dir,a.out)):
  p.error("require original Stage27/63, completed Stage74 259, NEW output")
 d27,d63,d74,root,out=(v.expanduser().resolve() for v in
                         (a.stage27_dir,a.stage63_dir,a.stage74_dir,a.sites_root,a.out))
 if (not all(q.is_dir() for q in (d27,d63,d74,root)) or out.exists()
    or not out.parent.is_dir() or
    any(out==q or out in q.parents or q in out.parents for q in (d27,d63,d74,root))):
  p.error("source reports must exist, output new and disjoint")
 fprev=d74/"stage74_VERSIONED_259_APPROVED_RH_VPD_TA_native_overlay.csv"
 m74=json.loads((d74/"stage74_manifest.json").read_text())
 if (m74.get("total_versioned_approved_HH")!=259 or
     m74.get("output_sha256",{}).get(fprev.name)!=sha(fprev) or
     sha(fprev)!="c94e0adc96df846b682f69e3c85d2be8247d23ba7debed686a3462bb5927fc6f" or
     m74.get("previous_240_approved_rows_preserved_exactly") is not True):
  raise ValueError("stage74 actual 259 user approved SHA changed")
 old=keyed(read(fprev,SCHEMA))
 if len(old)!=259:raise ValueError("Stage74 259 approved rows count changed")
 f27=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 f63=d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"
 rows27=read(f27,("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 rows63=read(f63,("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 s27=[r for r in rows27 if r["site"]==SITE]
 s63=[r for r in rows63 if r["site"]==SITE]
 if (len(rows27),len(rows63),len(s27),len(s63))!=(1574,1565,62,62):
  raise ValueError("original 62 US-WCr P2/P3 Stage27/63 source identity drift")
 original=keyed(s27)
 selected=keyed(s63)
 if set(original)!=set(selected) or len(set(r["episode_id"] for r in s63))!=24:
  raise ValueError("24 original WCr episode/source keys no longer exact")
 if any(k in old for k in original):raise ValueError("already approved WCr original key overlap")
 base=root/SITE/"forcing"
 packs=[z for z in base.rglob("*.zip") if z.is_file() and not z.is_symlink() and sha(z)==PIN]
 if len(packs)!=1:raise ValueError("source original WCr pinned archive missing/duplicated")
 required_t=set(r["native_time"] for r in s63)|set(T_FIX)
 # 3-day native context on both sides for RH bracket interpolation (also
 # screens original source adjacent negatives without modifying extra HH).
 for target in list(required_t):
  for n in range(-144,145):required_t.add(sh(target,n))
 actual={}
 with zipfile.ZipFile(packs[0]) as archive:
  matches=[m for m in archive.infolist() if
   Path(m.filename).name.startswith("AMF_US-WCr_FLUXNET_FLUXMET_HH_") and
   m.filename.endswith(".csv")]
  if len(matches)!=1 or matches[0].file_size>900*1024*1024:
   raise ValueError("original immutable WCr HH member missing/ambiguous")
  with archive.open(matches[0]) as raw:
   with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as reader:
    csvr=csv.DictReader(reader);head=csvr.fieldnames or []
    if len(head)!=len(set(head)) or not {
      "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(head):
     raise ValueError("original source required variables missing")
    for r in csvr:
     t=r["TIMESTAMP_START"]
     if t in required_t:
      if t in actual:raise ValueError("duplicate source native timestamp")
      actual[t]=r
 if any(k[1] not in actual for k in selected) or any(t not in actual for t in T_FIX):
  raise ValueError("source original 62 + five local corrupted T records missing")
 for (s,t),r in original.items():
  o=actual[t]
  if (num(o["TA_F"]) is None or num(o["VPD_F"]) is None or
      abs(num(o["TA_F"])-num(r["TA_F_C"]))>.002 or
      abs(num(o["VPD_F"])-num(r["VPD_F_hPa"]))>.002 or
      o["TA_F_QC"]!=r["TA_F_QC"] or o["VPD_F_QC"]!=r["VPD_F_QC"] or
      selected[(s,t)]["episode_id"]!=r["episode_id"]):
   raise ValueError("exact original WCr Stage27/63 T/VPD/QC mismatch "+t)
 def original_rh(t):
  o=actual.get(t)
  return rh(num(o["TA_F"]),num(o["VPD_F"])) if o is not None else None
 neg={t for _,t in selected if original_rh(t) is not None and original_rh(t)<0}
 ok={t for _,t in selected if original_rh(t) is not None and original_rh(t)>=0}
 if len(neg)!=61 or len(ok)!=1 or ok!={"201105260800"}:
  raise ValueError("original 61 RH negative + one 201105260800 valid RH discrepancy")
 if not {"201610011000","201610011130"}.issubset(neg):raise ValueError("2016 2 RH-negative wrong-TA anomaly source changed")
 if any((SITE,t) in old for t in T_FIX):raise ValueError("2016 extra T context would overwrite historical approval")
 # Objectively invalid QC0 temp (source -43.523°C) is NOT a valid donor.
 # Fixed local boundary temperatures all based on native SOURCE timestamps,
 # and known 2016 source original values independently printed by Stage75.
 anchors={"201610010800":(11.783,"0"),"201610010900":(11.701,"1"),
          "201610011100":(16.055,"0"),"201610011200":(16.910,"2")}
 for t,(v,q) in anchors.items():
  o=actual.get(t)
  if o is None or abs(num(o["TA_F"])-v)>.002 or o["TA_F_QC"]!=q:
   raise ValueError("source 2016 credible local anchor changed "+t)
 known_bad={"201610010830":(1.178,"0"),"201610010930":(-21.173,"1"),
           "201610011000":(-13.734,"1"),"201610011030":(-43.523,"0"),
           "201610011130":(-13.734,"1")}
 for t,(v,q) in known_bad.items():
  o=actual[t]
  if abs(num(o["TA_F"])-v)>.002 or o["TA_F_QC"]!=q:
   raise ValueError("source exact 2016 anomalous T/QC changed "+t)
 t_values={}
 for t,(left,right) in T_FIX.items():
  L,R=actual[left],actual[right]
  span=(clock(right)-clock(left)).total_seconds()
  wt=(clock(t)-clock(left)).total_seconds()/span
  v=num(L["TA_F"])*(1-wt)+num(R["TA_F"])*wt
  if not 0<wt<1 or not 10<=v<=20:raise ValueError("2016 interpolated original T not plausible "+t)
  t_values[t]=(v,left,right,wt)
 if sorted(t_values)!=sorted(T_FIX):raise ValueError("2016 source T correction incomplete")
 # Ordinary negative RH: two-sided original neighbor physical RH interpolation
 # over actual elapsed time, searching at most 72h. Fallback to source
 # processed ERA RH when no complete finite natural bracket exists, not a HOLD.
 def nearest(t,step):
  for k in range(1,145):
   z=sh(t,k*step)
   o=actual.get(z)
   if o is None:break
   rv=original_rh(z)
   if rv is not None and 0<=rv<=100:
    return z,rv
  return None,None
 modifications={}
 print("STAGE76 SOURCE VERIFIED",SITE,"62/62","24/24","ORIGINAL_SHA",PIN)
 for t in sorted(set(neg)|set(T_FIX)):
  o=actual[t]
  T,V=num(o["TA_F"]),num(o["VPD_F"])
  if t in t_values:
   newT,left,right,_=t_values[t];newV=V;newR=rh(newT,newV)
   if newR is None or not 0<=newR<=100:
    raise ValueError("2016 T correction failed physics "+t)
   method="SOURCE_QC_MIXED_OBVIOUS_T_SENSOR_ANOMALY_LOCAL_NATIVE_BOUNDED_INTERPOLATION_KEEP_VPD"
   L,R=actual[left],actual[right]
   LR,RR=original_rh(left),original_rh(right)
  else:
   left,LR=nearest(t,-1);right,RR=nearest(t,+1)
   if left is not None and right is not None:
    frac=(clock(t)-clock(left)).total_seconds()/(clock(right)-clock(left)).total_seconds()
    newR=LR+(RR-LR)*frac
    method="DIRECT_NEGATIVE_RH_LINEAR_FROM_TWO_NEAREST_NONNEGATIVE_ORIGINAL_SOURCE_RH"
   else:
    et,ev=num(o["TA_ERA"]),num(o["VPD_ERA"])
    newR=rh(et,ev)
    if newR is None or not 0<=newR<=100:
     raise ValueError("neither physically valid RH neighbors nor same-native source processed ERA humidity "+t)
    method="DIRECT_NEGATIVE_RH_FROM_SAME_NATIVE_SOURCE_PROCESSED_ERA_RH_NOT_NATIVE_ERA5"
    left=right=None;LR=RR=None
   newT=T;newV=es(T)*(1-newR/100)
   L=actual.get(left) if left else None;R=actual.get(right) if right else None
  if (newR is None or not 0<=newR<=100 or not 0<=newV<=es(newT) or
      abs(rh(newT,newV)-newR)>1e-6):
   raise ValueError("candidate source physics infeasible "+t)
  modifications[t]=(newT,newV,newR,left,right,LR,RR,L,R,method)
 if len(modifications)!=64 or len(set(modifications)-set(neg))!=3:
  raise ValueError("exact original 61 negative plus 3 local additional source T records")
 approved={};audit=[]
 for t in sorted(modifications):
  o=actual[t];T,V=num(o["TA_F"]),num(o["VPD_F"])
  newT,newV,newR,left,right,LR,RR,L,R,method=modifications[t]
  episod=original.get((SITE,t),{}).get("episode_id","20161001_LOCAL_TA_EXCEPTION_EXTRA")
  er=rh(num(o["TA_ERA"]),num(o["VPD_ERA"]))
  oldr=original_rh(t)
  row=dict(site=SITE,native_time=t,
   source_cohort="STAGE76_US_WCr_DIRECT_61_RH_NEGATIVE_PLUS_3_OBVIOUS_TA_CONTEXT",
   decision_id="WCR_"+episod+"_DIRECT_SCIENCE_REPAIR_20261029",
   source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
   source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
   source_RH_pct=o.get("RH",""),source_processed_ERA_T_C=o["TA_ERA"],
   source_processed_ERA_VPD_hPa=o["VPD_ERA"],
   source_processed_ERA_RH_derived_pct=fmt(er),
   modified_TA_C=fmt(newT),modified_RH_pct=fmt(newR),
   modified_VPD_hPa=fmt(newV),delta_VPD_hPa=fmt(newV-V),
   replacement_RH_provenance=method,
   new_VPD_derivation=("SOURCE_VPD_UNCHANGED_TA_RECALCULATED_RH" if t in T_FIX
       else "SOURCE_RH_RECOMPUTED_VPD_AT_UNCHANGED_TOWER_TA"),
   source_QC_provenance_only="SOURCE_TA_VPD_QC_HISTORICAL_LABELS_UNMODIFIED_REPAIR_IN_SEPARATE_VERSIONED_OVERLAY",
   overlay_status="USER_DIRECT_APPROVED_BATCH05_RULE_20261029_RESEARCH_VERSION_NOT_YET_MODEL_FORCING")
  if set(row)!=set(SCHEMA):raise ValueError("Stage76 versioned overlay schema drift")
  approved[(SITE,t)]=row
  audit.append(dict(site=SITE,episode_id=episod,native_time=t,
   source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
   source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
   original_derived_RH_pct=fmt(oldr),
   approved_TA_C=fmt(newT),approved_RH_pct=fmt(newR),
   approved_VPD_hPa=fmt(newV),scientific_method=method,
   left_anchor_native=left or "",left_anchor_QC=L["TA_F_QC"] if L else "",
   left_anchor_TA_C=L["TA_F"] if L else "",left_anchor_RH_pct=fmt(LR),
   right_anchor_native=right or "",right_anchor_QC=R["TA_F_QC"] if R else "",
   right_anchor_TA_C=R["TA_F"] if R else "",right_anchor_RH_pct=fmt(RR),
   source_ERA_T_C=o["TA_ERA"],source_ERA_VPD_hPa=o["VPD_ERA"],
   is_original_62_flagged="YES" if (SITE,t) in original else "NO_EXTRA_TA_QC_CONTEXT",
   decision="DIRECT_ACCEPTED_REPAIR_NOT_YET_APPLIED_TO_MODEL_FORCING"))
 passed_t=next(iter(ok));pass_o=actual[passed_t]
 passes=[dict(site=SITE,episode_id=original[(SITE,passed_t)]["episode_id"],
   native_time=passed_t,original_TA_C=pass_o["TA_F"],
   original_VPD_hPa=pass_o["VPD_F"],original_RH_pct=fmt(original_rh(passed_t)),
   science_disposition="PASS_ORIGINAL_PHYSICAL_RH_NONNEGATIVE_NO_REPAIR")]
 combined=dict(old);combined.update(approved)
 if (len(combined)!=323 or len(approved)!=64 or
     any(combined[k]!=old[k] for k in old)):
  raise ValueError("old 259 exact preserved + 64 = 323 failed")
 out.mkdir(exist_ok=False)
 fall=out/"stage76_VERSIONED_323_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 fnew=out/"stage76_64_NEW_WCr_APPROVED_NATIVE_REPAIR_RECORDS.csv"
 faudit=out/"stage76_64_ORIGINAL_VS_REPAIRED_T_VPD_RH_AUDIT.csv"
 fpass=out/"stage76_ONE_WCr_NONNEGATIVE_HH_PASSED_ORIGINAL.csv"
 write(fall,SCHEMA,[combined[k] for k in sorted(combined)])
 write(fnew,SCHEMA,[approved[k] for k in sorted(approved)])
 write(faudit,AUD,audit);write(fpass,PASS,passes)
 if len(read(fall,SCHEMA))!=323:raise ValueError("323 output CSV validation failed")
 methods=Counter(x["scientific_method"] for x in audit)
 manifest=dict(stage="76",site=SITE,original_ZIP_SHA256=PIN,
  stage74_prev259_SHA256=sha(fprev),previous_259_approved_rows_exactly_preserved=True,
  original_62_stage75_flagged=62,original_61_RH_negative=61,
  original_1_RH_nonnegative_pass_unchanged=1,
  native_T_QC0_or_QC1_obviously_faulty_20161001_extra_context_HH=3,
  new_direct_versioned_approved_records=64,
  new_RH_VPD_only_at_original_TA_records=59,
  new_20161001_TA_only_preserve_VPD_records=5,
  total_versioned_approved_records=323,
  source_processed_ERA_RH_is_not_independent_native_ERA5=True,
  methods=methods,original_source_and_QC_modified=False,
  previous_259_modified=False,DATM_CIME_forcing_modified=False,
  Slurm_jobs_submitted=0,outputs_sha256={x.name:sha(x) for x in (fall,fnew,faudit,fpass)})
 (out/"stage76_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2,default=dict)+"\n")
 print("STAGE76 SUCCESS | US-WCr ORIGINAL 24 EVENTS / 62 FLAGGED: 61 RH<0 DIRECT REPAIR, 1 RH>=0 PASS UNCHANGED")
 print("STAGE76 61 FLAGGED REPAIRS + 3 IN_SAME_SOURCE_20161001_OBVIOUS_TA_CONTEXT = 64 NEW ROWS")
 print("STAGE76 259 PREVIOUS APPROVED EXACT UNCHANGED + 64 WCr NEW = 323 VERSIONED APPROVED HH")
 print("STAGE76 REPAIR_METHODS",dict(methods))
 print("STAGE76 20161001_SOURCE_TA_EXCEPTION source_time originalT repairedT originalV repairedV RH")
 for x in audit:
  if x["native_time"].startswith("20161001"):
   print("STAGE76 TA_EXCEPTION",x["native_time"],x["source_TA_C"],
    f"{float(x['approved_TA_C']):.3f}",x["source_VPD_hPa"],
    f"{float(x['approved_VPD_hPa']):.3f}",
    f"{float(x['approved_RH_pct']):.2f}")
 print("STAGE76 64 DIRECT_APPROVAL_EXACT_TIME_AUDIT",str(faudit))
 print("STAGE76 APPROVED_323_SHA256="+sha(fall))
 print("STAGE76 APPROVED_323="+str(fall))
 print("STAGE76_REPORTS="+str(out))
 print("STAGE76 ORIGINAL/QC/OLD259/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":
 main()

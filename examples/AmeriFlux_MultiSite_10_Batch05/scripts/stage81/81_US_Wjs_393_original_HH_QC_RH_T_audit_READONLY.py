#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage81: original source-science read-only audit for
US-Wjs's 393 pending P2/P3 native HH. Verify 401 historical Stage27 source
times, exact 393 Stage63 remaining, eight historical already-approved keys,
Stage05 source original full CSV SHA, and successful Stage80 approved 714
overlay SHA. Write reports only under a fresh HOME directory. No model jobs.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SITE="US-Wjs"
RELEASE="AMF_US-Wjs_FLUXNET_2007-2025_v1.3_r1"
SOURCE_SHA="9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6"
PRIOR_SHA="e65b0c854cd391c1ae6c26b3b627dd60a99ee4a9f574219ead65ef1cc76d253c"
AUDIT_COLUMNS=("site","episode_id","native_time","source_TA_C","source_TA_QC",
 "source_VPD_hPa","source_VPD_QC","original_derived_RH_pct",
 "source_original_RH_pct","source_ERA_TA_C","source_ERA_VPD_hPa",
 "source_ERA_derived_RH_pct","source_ERA_internally_nonphysical",
 "source_P_F","source_SW_IN_F","previous_TA_C","previous_TA_QC",
 "following_TA_C","following_TA_QC","source_T_numerically_suspect",
 "RH_original_below_zero","science_disposition")
EP_COLUMNS=("site","episode_id","original_pending_HH","native_start","native_end",
 "derived_RH_negative_HH","derived_RH_nonnegative_HH","source_T_suspect_HH",
 "source_ERA_nonphysical_HH","original_QC_pair_counts")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
def num(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def fmt(x):return "" if x is None else f"{x:.9f}"
def es(T):
 if T is None or not -80<=T<=60:return None
 return 6.112*math.exp(17.67*T/(243.5+T))
def rh(T,V):
 e=es(T)
 return None if e is None or V is None else 100*(1-V/e)
def dt(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid source native HH "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def at(t,steps):
 return (dt(t)+timedelta(minutes=steps*30)).strftime("%Y%m%d%H%M")
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("missing source/report "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as h:
  rd=csv.DictReader(h);hd=rd.fieldnames or []
  if len(set(hd))!=len(hd) or not set(required).issubset(hd):
   raise ValueError("required original ledger columns missing "+str(p))
  rr=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in rr):
  raise ValueError("original source ledger row malformed "+str(p))
 return rr
def index(rows):
 d={}
 for r in rows:
  key=(r["site"],r["native_time"])
  if key in d:raise ValueError("duplicate exact source time "+str(key))
  d[key]=r
 return d
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as h:
  writer=csv.DictWriter(h,fieldnames=cols,extrasaction="raise")
  writer.writeheader();writer.writerows(rows)
def selftest():
 assert at("202001010000",-1)=="201912312330"
 assert rh(10,20)<0 and 0<rh(10,2)<100
 assert len(SOURCE_SHA)==len(PRIOR_SHA)==64
 assert 401-393==8
 print("STAGE81 SELF-TEST PASS | Wjs original 401 source /393 remaining, prior714 SHA, QC-RH-T original audit only")
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage27",type=Path)
 ap.add_argument("--stage63",type=Path)
 ap.add_argument("--stage80",type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage27,a.stage63,a.stage80,a.out)):
  ap.error("pass Stage27/Stage63 original reports, successful Stage80, and a NEW output")
 d27,d63,d80,out=(x.expanduser().resolve() for x in (a.stage27,a.stage63,a.stage80,a.out))
 if (not all(d.is_dir() for d in (d27,d63,d80)) or out.exists() or
      not out.parent.is_dir()):
  ap.error("source reports missing or output not a fresh disjoint directory")
 prev=d80/"stage80_VERSIONED_714_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m80=json.loads((d80/"stage80_manifest.json").read_text())
 if (sha(prev)!=PRIOR_SHA or
     m80.get("total_approved_versioned_records")!=714 or
     m80.get("outputs_sha256",{}).get(prev.name)!=PRIOR_SHA):
  raise ValueError("latest completed Stage80 714 original SHA has drifted")
 old=index(read(prev,("site","native_time")))
 if len(old)!=714:raise ValueError("prior approved overlay 714 duplicate/size drift")
 r27=read(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
          ("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 r63=read(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
          ("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 if len(r27)!=1574 or len(r63)!=1565:
  raise ValueError("original 1574/1565 global source cohorts altered")
 historical=index(r for r in r27 if r["site"]==SITE)
 pending=index(r for r in r63 if r["site"]==SITE)
 if len(historical)!=401 or len(pending)!=393 or not set(pending).issubset(historical):
  raise ValueError("Wjs exact original 401 and pending 393 source keys changed")
 previous_eight=set(historical)-set(pending)
 if len(previous_eight)!=8 or not previous_eight.issubset(old) or set(pending)&set(old):
  raise ValueError("Wjs historical eight previously approved and remaining 393 crosswalk differs")
 if any(historical[k]["episode_id"]!=pending[k]["episode_id"] for k in pending):
  raise ValueError("Wjs original event identity changed")
 original_folder=a.sites_root/SITE/"forcing"/"raw"/RELEASE
 if not original_folder.is_dir() or original_folder.is_symlink():
  raise ValueError("Stage05 source folder missing "+str(original_folder))
 pat=re.compile(r"AMF_US-Wjs_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",re.I)
 cs=[p for p in original_folder.iterdir() if pat.fullmatch(p.name)]
 if len(cs)!=1 or not cs[0].is_file() or cs[0].is_symlink() or sha(cs[0])!=SOURCE_SHA:
  raise ValueError("original native Wjs CSV failed Stage05 SHA strict validation")
 src=cs[0]
 # Include original ±3-hour native source context for all 393 pending keys;
 # original historical eight are also read so Stage27 SHA joins check 401/401.
 required={at(k[1],j) for k in pending for j in range(-6,7)}
 required.update(k[1] for k in historical)
 vals={}
 with src.open(encoding="utf-8-sig",newline="") as stream:
  rd=csv.DictReader(stream);hd=rd.fieldnames or []
  if len(hd)!=len(set(hd)) or not {
    "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
    "TA_ERA","VPD_ERA"}.issubset(hd):
   raise ValueError("native source HH schema unexpected")
  for r in rd:
   time=r["TIMESTAMP_START"]
   if time in required:
    if time in vals:raise ValueError("duplicate original FLUXMET half-hour "+time)
    vals[time]=r
 if not all(k[1] in vals for k in historical):
  raise ValueError("original source 401 original audit records incomplete")
 for k,r in historical.items():
  t=k[1];v=vals[t];T=num(v["TA_F"]);V=num(v["VPD_F"])
  if (T is None or V is None or
      num(r["TA_F_C"]) is None or num(r["VPD_F_hPa"]) is None or
      abs(T-num(r["TA_F_C"]))>.002 or abs(V-num(r["VPD_F_hPa"]))>.002 or
      v["TA_F_QC"]!=r["TA_F_QC"] or v["VPD_F_QC"]!=r["VPD_F_QC"]):
   raise ValueError("Wjs original Stage27 401/401 native T/VPD/QC source mismatch "+t)
 # Stage81 only reports original pending 393; previous eight are left intact.
 rows=[];byep=defaultdict(list)
 original_qc=Counter();neg=0;pos=0;era_bad=0;badT=[];nearzero=[]
 for k,p in sorted(pending.items()):
  t=k[1];v=vals[t]
  if v["TA_F_QC"]!=p["TA_F_QC"] or v["VPD_F_QC"]!=p["VPD_F_QC"]:
   raise ValueError("original Stage63 source QC mismatch "+t)
  T,V=num(v["TA_F"]),num(v["VPD_F"])
  R=rh(T,V)
  if R is None:raise ValueError("invalid original T/VPD source units "+t)
  er=rh(num(v["TA_ERA"]),num(v["VPD_ERA"]))
  isbadERA=(er is None or er<0 or er>100)
  epre=vals.get(at(t,-1));epost=vals.get(at(t,1))
  preT=num(epre["TA_F"]) if epre else None
  postT=num(epost["TA_F"]) if epost else None
  erT=num(v["TA_ERA"])
  temperature_flag=(
   (preT is not None and postT is not None and min(abs(T-preT),abs(T-postT))>=8)
   or (T==0 and preT is not None and postT is not None and
       min(abs(preT),abs(postT))>5)
   or (erT is not None and abs(T-erT)>=15 and
       preT is not None and postT is not None and
       max(abs(T-preT),abs(T-postT))>=6))
  qc=(v["TA_F_QC"],v["VPD_F_QC"]);original_qc[qc]+=1
  neg+=R<0;pos+=R>=0;era_bad+=isbadERA
  if 0<=R<1:nearzero.append((t,R))
  row=dict(site=SITE,episode_id=p["episode_id"],native_time=t,
   source_TA_C=v["TA_F"],source_TA_QC=v["TA_F_QC"],
   source_VPD_hPa=v["VPD_F"],source_VPD_QC=v["VPD_F_QC"],
   original_derived_RH_pct=fmt(R),
   source_original_RH_pct=v.get("RH",""),
   source_ERA_TA_C=v["TA_ERA"],source_ERA_VPD_hPa=v["VPD_ERA"],
   source_ERA_derived_RH_pct=fmt(er),
   source_ERA_internally_nonphysical=str(isbadERA),
   source_P_F=v.get("P_F",""),source_SW_IN_F=v.get("SW_IN_F",""),
   previous_TA_C=fmt(preT),previous_TA_QC=epre["TA_F_QC"] if epre else "",
   following_TA_C=fmt(postT),following_TA_QC=epost["TA_F_QC"] if epost else "",
   source_T_numerically_suspect=str(temperature_flag),
   RH_original_below_zero=str(R<0),
   science_disposition=("SOURCE_T_NUMERICAL_EXCEPTION_INSPECT_LOCALLY"
      if temperature_flag else "DIRECT_REPAIR_NEGATIVE_RH_WITH_QC_PROVENANCE"
      if R<0 else "PASS_ORIGINAL_NONNEGATIVE_RH_NO_REPAIR"))
  if set(row)!=set(AUDIT_COLUMNS):raise ValueError("Stage81 output original schema drift")
  if temperature_flag:badT.append(row)
  byep[p["episode_id"]].append(row)
  rows.append(row)
 events=[]
 for ep,ev in sorted(byep.items()):
  ev.sort(key=lambda x:x["native_time"])
  events.append(dict(site=SITE,episode_id=ep,original_pending_HH=len(ev),
   native_start=ev[0]["native_time"],native_end=ev[-1]["native_time"],
   derived_RH_negative_HH=sum(x["RH_original_below_zero"]=="True" for x in ev),
   derived_RH_nonnegative_HH=sum(x["RH_original_below_zero"]=="False" for x in ev),
   source_T_suspect_HH=sum(x["source_T_numerically_suspect"]=="True" for x in ev),
   source_ERA_nonphysical_HH=sum(x["source_ERA_internally_nonphysical"]=="True" for x in ev),
   original_QC_pair_counts=json.dumps(dict(Counter(
       x["source_TA_QC"]+"/"+x["source_VPD_QC"] for x in ev)),sort_keys=True)))
 if len(rows)!=393 or neg+pos!=393:
  raise ValueError("Wjs original 393 source audit tally drift")
 out.mkdir(exist_ok=False)
 frows=out/"stage81_Wjs_393_SOURCE_ORIGINAL_QC_RH_T_AUDIT.csv"
 fev=out/"stage81_Wjs_ORIGINAL_EVENT_SUMMARY.csv"
 fexc=out/"stage81_Wjs_SOURCE_T_AND_ERA_NUMERICAL_EXCEPTIONS.csv"
 write(frows,AUDIT_COLUMNS,rows);write(fev,EP_COLUMNS,events)
 write(fexc,AUDIT_COLUMNS,[r for r in rows if r["source_T_numerically_suspect"]=="True"
                               or r["source_ERA_internally_nonphysical"]=="True"])
 report=dict(stage=81,site=SITE,source_SHA256=SOURCE_SHA,
  previous_714_SHA256=PRIOR_SHA,original_historical_source_HH=401,
  original_eight_already_covered_by_prior_overlay=8,
  original_pending_HH=393,original_pending_events=len(events),
  original_RH_negative=neg,original_RH_nonnegative=pos,
  original_source_QC_pairs={a+"/"+b:c for (a,b),c in original_qc.items()},
  original_ERA_internal_nonphysical_HH=era_bad,source_T_suspect_HH=len(badT),
  original_RH_nonnegative_below_1pct_HH=len(nearzero),
  all_original_sources_and_QC_unchanged=True,previous_714_unchanged=True,
  DATM_CIME_unchanged=True,Slurm_submitted=0,
  output_SHA256={x.name:sha(x) for x in (frows,fev,fexc)})
 (out/"stage81_manifest.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print("STAGE81 ORIGINAL SOURCE SHA VERIFIED",SOURCE_SHA)
 print("STAGE81 STAGE27 SOURCE 401/401; STAGE63 REMAINING 393/393; PRIOR714 EIGHT WJS APPROVALS SHA VERIFIED",PRIOR_SHA)
 print("STAGE81 SUMMARY EVENTS",len(events),"ORIGINAL_REMAINING_HH",393,
       "NEGATIVE_RH",neg,"NONNEGATIVE_RH",pos)
 print("STAGE81 QC_PAIRS",json.dumps(report["original_source_QC_pairs"],sort_keys=True))
 print("STAGE81 SOURCE_ERA_NONPHYSICAL",era_bad,"SOURCE_T_EXCEPTIONS",len(badT),
       "NONNEGATIVE_RH_BELOW_1PCT",len(nearzero))
 print("STAGE81 LARGEST_EVENTS event pending negative nonnegative T_exception source_ERA_nonphysical")
 for x in sorted(events,key=lambda x:(-x["original_pending_HH"],x["episode_id"]))[:30]:
  print("STAGE81 EVENT",x["episode_id"],x["original_pending_HH"],
   x["derived_RH_negative_HH"],x["derived_RH_nonnegative_HH"],
   x["source_T_suspect_HH"],x["source_ERA_nonphysical_HH"])
 print("STAGE81 SOURCE_T_EXCEPTIONS_DETAIL")
 for x in badT[:80]:
  print("STAGE81 T_EXCEPTION",x["native_time"],"T",x["source_TA_C"],
   "QC",x["source_TA_QC"],"VPD",x["source_VPD_hPa"],"RH",x["original_derived_RH_pct"],
   "BEFORE_T",x["previous_TA_C"],"AFTER_T",x["following_TA_C"],
   "SOURCE_ERA_T",x["source_ERA_TA_C"])
 print("STAGE81 REPORTS="+str(out))
 print("STAGE81 READONLY AUDIT SUCCESS | ORIGINAL/QC/PRIOR714/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

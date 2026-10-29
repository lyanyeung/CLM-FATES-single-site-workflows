#!/usr/bin/env python3
"""Batch05 Stage79 US-Vcm exact 362 Stage63 original P2/P3 half-hours.
Use Stage05 SHA-pinned, unmodified FLUXMET native HH/HR CSV, compare Stage27
native T,VPD,QC with Stage63 episode identity, then classify original source
RH<0 vs RH>=0 and measured/fill/ERA QC pairs. Review source temperature
and source ERA internal physics separately; do not fabricate replacements.
Writes NEW audit reports under HOME only; NO original/QC/approved/forcing/
CIME/Slurm changes. Production approval is NOT implied by this audit.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
SITE="US-Vcm"
SOURCE_SHA="c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c"
SOURCE_FOLDER="AMF_US-Vcm_FLUXNET_2007-2025_v1.3_r1"
OVERLAY_SHA="400757c166d03fa8d7e7b72aa39879c14c2d9db5ada818d930c647c71d06f7b5"
FIELD_NAMES=("site","episode_id","native_time","flagged","TA_F_C","TA_F_QC",
 "VPD_F_hPa","VPD_F_QC","RH_implied_pct","RH_original_source_pct",
 "TA_ERA_C","VPD_ERA_hPa","RH_ERA_derived_pct","ERA_pair_nonphysical",
 "P_F","SW_IN_F","native_T_minus_ERA_C","before_30m_T_C",
 "after_30m_T_C","before_30m_T_QC","after_30m_T_QC",
 "suspect_T_source","science_action")
EPISODE_COLS=("site","episode_id","selected_HH","native_start","native_end",
 "original_negative_RH_HH","original_nonnegative_RH_HH",
 "original_T_VPD_QC_pairs","source_T_suspect_HH",
 "original_ERA_nonphysical_HH","source_measured_pair_QC00_HH")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
def num(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None
def fmt(x):return "" if x is None else f"{x:.9f}"
def s(t):
 if t is None or not -80<=t<=60:return None
 return 6.112*math.exp(17.67*t/(243.5+t))
def rh(T,V):
 z=s(T)
 return 100*(1-V/z) if z is not None and V is not None else None
def when(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid HH stamp "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def off(t,k):
 return (when(t)+timedelta(minutes=k*30)).strftime("%Y%m%d%H%M")
def table(p,columns):
 if not p.is_file() or p.is_symlink():raise ValueError("missing original source report "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as stream:
  r=csv.DictReader(stream);hdr=r.fieldnames or []
  if len(hdr)!=len(set(hdr)) or not set(columns).issubset(hdr):
   raise ValueError("original report columns mismatch "+str(p))
  a=list(r)
 if any(None in x or any(v is None for v in x.values()) for x in a):
  raise ValueError("malformed original report "+str(p))
 return a
def write(p,cols,records):
 with p.open("x",encoding="utf-8",newline="") as stream:
  w=csv.DictWriter(stream,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(records)
def selftest():
 assert abs(rh(0,6.112))<1e-9
 assert rh(0,7)<0
 assert off("201601010000",-1)=="201512312330"
 assert len(SOURCE_SHA)==64 and len(OVERLAY_SHA)==64
 print("STAGE79 SELF-TEST PASS | source-pinned US-Vcm 362 native HH, QC+RH+temp+ERA event science screen; reports only")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage63-dir",type=Path)
 p.add_argument("--stage78-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage27_dir,a.stage63_dir,a.stage78_dir,a.out)):
  p.error("provide exact Stage27,Stage63,successful Stage78 directories and NEW output")
 d27,d63,d78,out=(x.expanduser().resolve() for x in
   (a.stage27_dir,a.stage63_dir,a.stage78_dir,a.out))
 if not all(x.is_dir() for x in (d27,d63,d78)) or out.exists() or not out.parent.is_dir():
  p.error("missing original reports or output already exists")
 approved=d78/"stage78_VERSIONED_378_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 approved_rows=table(approved,("site","native_time"))
 if len(approved_rows)!=378 or sha(approved)!=OVERLAY_SHA:
  raise ValueError("Stage78 approved versioned 378 SHA drifted")
 original27=table(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
                   ("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 pending63=table(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
                   ("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 if len(original27)!=1574 or len(pending63)!=1565:
  raise ValueError("original 1574 Stage27/1565 Stage63 roster changed")
 mine27=[r for r in original27 if r["site"]==SITE]
 mine63=[r for r in pending63 if r["site"]==SITE]
 if len(mine27)!=362 or len(mine63)!=362:
  raise ValueError("US-Vcm original 362 exact records changed")
 ref={(r["site"],r["native_time"]):r for r in mine27}
 pending={(r["site"],r["native_time"]):r for r in mine63}
 past={(r["site"],r["native_time"]) for r in approved_rows}
 if (len(ref)!=362 or len(pending)!=362 or set(ref)!=set(pending) or
     set(ref)&past or any(ref[k]["episode_id"]!=pending[k]["episode_id"] for k in ref)):
  raise ValueError("Vcm source original/approved key/episode reconciliation failed")
 rawfolder=a.sites_root/SITE/"forcing"/"raw"/SOURCE_FOLDER
 if not rawfolder.is_dir() or rawfolder.is_symlink():
  raise ValueError("original Stage05 source release missing "+str(rawfolder))
 pat=re.compile(r"AMF_US-Vcm_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",re.I)
 files=[x for x in rawfolder.iterdir() if pat.fullmatch(x.name)]
 if len(files)!=1 or not files[0].is_file() or files[0].is_symlink():
  raise ValueError("Stage05 original FLUXMET HH/HR CSV ambiguous")
 csvfile=files[0]
 if sha(csvfile)!=SOURCE_SHA:
  raise ValueError("US-Vcm source original Stage05 SHA mismatch "+str(csvfile))
 # Exactly the original flagged hours plus native immediate context to avoid
 # relying on processed ERA as if it were independently observed tower RH.
 selected={k[1] for k in ref}
 wanted={off(t,j) for t in selected for j in range(-6,7)}
 obs={}
 with csvfile.open(encoding="utf-8-sig",newline="") as stream:
  rr=csv.DictReader(stream);columns=rr.fieldnames or []
  if len(set(columns))!=len(columns) or not {
   "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
   "TA_ERA","VPD_ERA"}.issubset(columns):
   raise ValueError("original FLUXMET source fields changed")
  for r in rr:
   stamp=r["TIMESTAMP_START"]
   if stamp in wanted:
    if stamp in obs:raise ValueError("duplicate original native timestamp "+stamp)
    obs[stamp]=r
 if not selected.issubset(obs):
  raise ValueError("source original selected HH missing "+str(len(selected-set(obs))))
 episodes=defaultdict(list);rows=[];negative=[];positive=[];suspects=[]
 qc=Counter();era_nonphys=0
 for _,t in sorted(ref):
  orig=obs[t];src=ref[(SITE,t)];p63=pending[(SITE,t)]
  T,V=num(orig["TA_F"]),num(orig["VPD_F"])
  if (T is None or V is None or
      abs(T-num(src["TA_F_C"]))>.002 or
      abs(V-num(src["VPD_F_hPa"]))>.002 or
      src["TA_F_QC"]!=orig["TA_F_QC"] or
      src["VPD_F_QC"]!=orig["VPD_F_QC"] or
      p63["TA_F_QC"]!=orig["TA_F_QC"] or
      p63["VPD_F_QC"]!=orig["VPD_F_QC"]):
   raise ValueError("Stage27/63 source T,VPD,QC drift "+t)
  RH=rh(T,V)
  if RH is None:raise ValueError("invalid original temperature physics "+t)
  et,ev=num(orig["TA_ERA"]),num(orig["VPD_ERA"])
  er=rh(et,ev)
  is_era_bad=er is None or er<0 or er>100
  if is_era_bad:era_nonphys+=1
  br=obs.get(off(t,-1));ar=obs.get(off(t,+1))
  bt=num(br["TA_F"]) if br is not None else None
  at=num(ar["TA_F"]) if ar is not None else None
  delta_era=abs(T-et) if et is not None else None
  looks_bad=(
   (bt is not None and at is not None and min(abs(T-bt),abs(T-at))>=8)
   or (bt is not None and at is not None and T==0 and min(abs(bt),abs(at))>5)
   or (delta_era is not None and delta_era>=15 and
       bt is not None and at is not None and max(abs(T-bt),abs(T-at))>=6))
  QC=(orig["TA_F_QC"],orig["VPD_F_QC"])
  qc[QC]+=1
  (negative if RH<0 else positive).append((t,RH))
  ep=src["episode_id"]
  row=dict(site=SITE,episode_id=ep,native_time=t,flagged="YES",
   TA_F_C=orig["TA_F"],TA_F_QC=orig["TA_F_QC"],
   VPD_F_hPa=orig["VPD_F"],VPD_F_QC=orig["VPD_F_QC"],
   RH_implied_pct=fmt(RH),
   RH_original_source_pct=orig.get("RH",""),
   TA_ERA_C=orig["TA_ERA"],VPD_ERA_hPa=orig["VPD_ERA"],
   RH_ERA_derived_pct=fmt(er),ERA_pair_nonphysical=str(is_era_bad),
   P_F=orig.get("P_F",""),SW_IN_F=orig.get("SW_IN_F",""),
   native_T_minus_ERA_C=fmt(T-et) if et is not None else "",
   before_30m_T_C=fmt(bt),after_30m_T_C=fmt(at),
   before_30m_T_QC=br["TA_F_QC"] if br else "",
   after_30m_T_QC=ar["TA_F_QC"] if ar else "",
   suspect_T_source=str(looks_bad),
   science_action=("REVIEW_ORIGINAL_T_SOURCE_EXCEPTION" if looks_bad
     else "DIRECT_RH_LT_ZERO_QC_DEPENDENT_REPAIR" if RH<0
     else "PASS_RH_NONNEGATIVE_SOURCE_UNCHANGED"))
  if looks_bad:suspects.append(row)
  episodes[ep].append(row)
  rows.append(row)
 summary=[]
 for ep,seq in sorted(episodes.items()):
  seq.sort(key=lambda x:x["native_time"])
  summary.append(dict(site=SITE,episode_id=ep,
   selected_HH=len(seq),native_start=seq[0]["native_time"],
   native_end=seq[-1]["native_time"],
   original_negative_RH_HH=sum(float(x["RH_implied_pct"])<0 for x in seq),
   original_nonnegative_RH_HH=sum(float(x["RH_implied_pct"])>=0 for x in seq),
   original_T_VPD_QC_pairs=json.dumps(dict(Counter(
     x["TA_F_QC"]+"/"+x["VPD_F_QC"] for x in seq)),sort_keys=True),
   source_T_suspect_HH=sum(x["suspect_T_source"]=="True" for x in seq),
   original_ERA_nonphysical_HH=sum(x["ERA_pair_nonphysical"]=="True" for x in seq),
   source_measured_pair_QC00_HH=sum(x["TA_F_QC"]=="0" and x["VPD_F_QC"]=="0" for x in seq)))
 out.mkdir(exist_ok=False)
 fh=out/"stage79_US_Vcm_362_source_original_QC_RH_temperature.csv"
 fe=out/"stage79_US_Vcm_original_event_summary.csv"
 fm=out/"stage79_US_Vcm_critical_source_T_and_ERA_examples.csv"
 write(fh,FIELD_NAMES,rows);write(fe,EPISODE_COLS,summary)
 write(fm,FIELD_NAMES,[x for x in rows if x["suspect_T_source"]=="True" or
       x["ERA_pair_nonphysical"]=="True" or
       (x["TA_F_QC"]=="0" and x["VPD_F_QC"]=="0" and float(x["RH_implied_pct"])<1)])
 m=dict(stage=79,site=SITE,original_source_SHA256=SOURCE_SHA,
  source_file=str(csvfile),prior_378_overlay_SHA256=OVERLAY_SHA,
  original_362_source_native_HH_verified=True,original_episodes=len(summary),
  original_negative_RH_HH=len(negative),original_nonnegative_RH_HH=len(positive),
  original_QC_pairs={a+"/"+b:n for (a,b),n in qc.items()},
  original_source_ERA_internal_nonphysical_HH=era_nonphys,
  original_source_T_suspect_HH=len(suspects),
  all_original_and_approved_source_unchanged=True,
  DATM_CIME_unchanged=True,Slurm_jobs=0,
  output_sha256={x.name:sha(x) for x in (fh,fe,fm)})
 (out/"stage79_manifest.json").write_text(json.dumps(m,sort_keys=True,indent=2)+"\n")
 print("STAGE79 US-Vcm EXACT SOURCE SHA VERIFIED",SOURCE_SHA)
 print("STAGE79 SOURCE MATCH STAGE27/63 362/362; PRIOR378 EXACT SHA VERIFIED",OVERLAY_SHA)
 print("STAGE79 SUMMARY EVENTS",len(summary),"FLAGGED_HH",len(rows),
   "RH_NEGATIVE",len(negative),"RH_NONNEGATIVE",len(positive))
 print("STAGE79 ORIGINAL_QC_PAIRS",json.dumps(m["original_QC_pairs"],sort_keys=True))
 print("STAGE79 SOURCE_ERA_INTERNAL_NONPHYSICAL",era_nonphys,
   "SOURCE_T_NUMERICAL_EXCEPTIONS",len(suspects))
 print("STAGE79 MEASURED_QC00_NEGATIVE_NEAR_ZERO",
   sum(x["TA_F_QC"]=="0" and x["VPD_F_QC"]=="0" and
       float(x["RH_implied_pct"])<0 for x in rows))
 print("STAGE79 EVENT_SUMMARY ID selected negative positive source_T_exceptions ERA_nonphys QCpairs")
 for x in summary:
  print("STAGE79 EVENT",x["episode_id"],x["selected_HH"],
   x["original_negative_RH_HH"],x["original_nonnegative_RH_HH"],
   x["source_T_suspect_HH"],x["original_ERA_nonphysical_HH"],
   x["original_T_VPD_QC_pairs"])
 print("STAGE79 EXCEPTION_TIMES native T QC VPD QC derivedRH sourceERA_RH")
 for x in suspects[:60]:
  print("STAGE79 T_EXCEPTION",x["native_time"],x["TA_F_C"],x["TA_F_QC"],
   x["VPD_F_hPa"],x["VPD_F_QC"],
   f"{float(x['RH_implied_pct']):.2f}",x["RH_ERA_derived_pct"])
 print("STAGE79 REPORTS="+str(out))
 print("STAGE79 SCIENCE_CLASSIFICATION_ONLY | ORIGINAL/QC/PRIOR378/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

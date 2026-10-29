#!/usr/bin/env python3
"""Stage77 US-Var exact 37 original Batch05 episodes / 62 remaining P2/P3 HH.
Read SHA-verified original AmeriFlux FLUXMET HH ZIP and original Stage63/27
immutable source records. Print 3-hour contexts per event + consolidated
classification: RH<0 direct-repair rule; RH>=0 pass original, unusual source
temperature exceptions. Never write source/overlay/DATM or run Slurm.
"""
import argparse,csv,hashlib,io,math,zipfile
from collections import defaultdict,Counter
from datetime import datetime,timedelta
from pathlib import Path

SITE="US-Var"
PIN="2e0ff6fe7f7de6dfde3ebfd2e822266e899bd80f1ad0377f78fde34efcb410f2"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def number(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def fmt(x):
 v=number(x)
 return "NA" if v is None else f"{v:.3f}"
def rh(t,v):
 t,v=number(t),number(v)
 if t is None or v is None or not -80<=t<=60:return None
 return 100*(1-v/(6.112*math.exp(17.67*t/(t+243.5))))
def rfmt(t,v):
 value=rh(t,v)
 return "NA" if value is None else f"{value:.2f}"
def native(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("bad source half-hour timestamp "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def around(t,n):
 return (native(t)+timedelta(minutes=30*n)).strftime("%Y%m%d%H%M")
def tab(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("original science input missing "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  head=rd.fieldnames or []
  if len(set(head))!=len(head) or not set(required).issubset(head):
   raise ValueError("science ledger missing required fields "+str(p))
  out=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in out):
  raise ValueError("malformed source ledger "+str(p))
 return out
def selftest():
 assert (native("201503010000")-native("201502282330")).total_seconds()==1800
 assert rh(10,20)<0
 assert 0<rh(10,2)<100
 assert number("-9999") is None
 print("STAGE77 SELF-TEST PASS | original US-Var 37 events, 62 HH; direct RH-negative scientific screening, no writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage63-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 a=p.parse_args()
 if a.self_test:selftest();return
 if a.stage63_dir is None or a.stage27_dir is None:
  p.error("need source report dirs --stage63-dir and --stage27-dir")
 d63,d27,root=(x.expanduser().resolve() for x in
               (a.stage63_dir,a.stage27_dir,a.sites_root))
 pending=tab(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
  ("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 prior=tab(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
  ("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 u=[r for r in pending if r["site"]==SITE]
 old=[r for r in prior if r["site"]==SITE]
 if (len(pending),len(prior),len(u),len(old))!=(1565,1574,62,62):
  raise ValueError("original Stage63/Stage27 US-Var 62 source HH drift")
 ref={(r["site"],r["native_time"]):r for r in old}
 if len(ref)!=62 or {(r["site"],r["native_time"]) for r in u}!=set(ref):
  raise ValueError("Stage27 exact 62 selected source timestamps do not match Stage63")
 events=defaultdict(set)
 for r in u:
  if ref[(SITE,r["native_time"])]["episode_id"]!=r["episode_id"]:
   raise ValueError("Stage63 original event identity drift")
  events[r["episode_id"]].add(r["native_time"])
 if len(events)!=37:raise ValueError("original US-Var 37 episodes changed")
 base=root/SITE/"forcing"
 archive=[p for p in base.rglob("*.zip")
          if p.is_file() and not p.is_symlink() and sha(p)==PIN]
 if len(archive)!=1:raise ValueError("original pinned US-Var FLUXMET ZIP missing/nonunique")
 wanted={around(t,k) for times in events.values() for t in times for k in range(-6,7)}
 data={}
 with zipfile.ZipFile(archive[0]) as z:
  entries=[m for m in z.infolist() if
   Path(m.filename).name.startswith("AMF_US-Var_FLUXNET_FLUXMET_HH_")
   and m.filename.endswith(".csv")]
  if len(entries)!=1 or entries[0].file_size>900*1024*1024:
   raise ValueError("original FLUXMET_HH member missing/ambiguous")
  with z.open(entries[0]) as fb,io.TextIOWrapper(fb,encoding="utf-8-sig",newline="") as handle:
   rd=csv.DictReader(handle);hd=rd.fieldnames or []
   required={"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}
   if len(hd)!=len(set(hd)) or not required.issubset(hd):
    raise ValueError("original FLUXMET schema mismatch")
   for r in rd:
    t=r["TIMESTAMP_START"]
    if t in wanted:
     if t in data:raise ValueError("duplicate original native HH "+t)
     data[t]=r
 flagged={r["native_time"] for r in u}
 if not flagged.issubset(set(data)):
  raise ValueError("missing original HH in source archive")
 qc=Counter()
 neg=[];positive=[];temp_issues=[]
 for t in sorted(flagged):
  r=data[t];o=ref[(SITE,t)]
  T,V=number(r["TA_F"]),number(r["VPD_F"])
  if (T is None or V is None or r["TA_F_QC"]!=o["TA_F_QC"]
      or r["VPD_F_QC"]!=o["VPD_F_QC"]
      or abs(T-number(o["TA_F_C"]))>.002
      or abs(V-number(o["VPD_F_hPa"]))>.002):
   raise ValueError("original Stage27 selected native TA/VPD/QC changed "+t)
  qc[(r["TA_F_QC"],r["VPD_F_QC"])]+=1
  RH=rh(T,V)
  if RH is None:raise ValueError("missing original derived RH "+t)
  if RH<0:neg.append((t,RH))
  else:positive.append((t,RH))
  # Screening, not an automatic verdict on storm-induced cooling:
  before,after=data.get(around(t,-1)),data.get(around(t,1))
  if before is not None and after is not None:
   bT,aT=number(before["TA_F"]),number(after["TA_F"])
   era=number(r["TA_ERA"])
   diffs=[abs(T-z) for z in (bT,aT) if z is not None]
   if ((len(diffs)==2 and min(diffs)>=8) or
       (T==0 and bT is not None and aT is not None
        and abs(bT)>5 and abs(aT)>5) or
       (era is not None and abs(T-era)>=15 and len(diffs)==2
        and max(diffs)>=6)):
    temp_issues.append((t,T,era,bT,aT))
 print("STAGE77 ORIGINAL_US_Var_SHA256",PIN)
 print("STAGE77 VERIFIED ORIGINAL STAGE27 SOURCE HH",len(ref),"EVENTS",len(events),"FLAGGED",len(flagged))
 print("STAGE77 CLASSIFIED original_RH_negative",len(neg),"original_RH_nonnegative",len(positive))
 print("STAGE77 FLAGGED_TA_VPD_QC_PAIRS",dict(qc))
 print("STAGE77 TEMPERATURE_NUMERICAL_EXCEPTIONS",len(temp_issues))
 for t,T,E,b,a in temp_issues:
  print("STAGE77 CHECK_SOURCE_TA",t,"TA_F",fmt(T),"TA_ERA",fmt(E),"prev_TA",fmt(b),"next_TA",fmt(a))
 for eid,times in sorted(events.items()):
  extent=sorted({around(t,k) for t in times for k in range(-6,7)})
  event_neg=sum(t in {v[0] for v in neg} for t in times)
  print("\n========",eid,"| flagged_HH",len(times),"RH_negative",event_neg,
        "RH_nonnegative",len(times)-event_neg,"========")
  print("TIME | FLAG | TA_F | TA_QC | VPD_F | VPD_QC | RH_% | TA_ERA | VPD_ERA | RH_ERA_% | P_F | SW_IN_F")
  for t in extent:
   r=data.get(t)
   if r is None:
    print(t,"| ORIGINAL_NATIVE_MISSING");continue
   print(" | ".join([t,"***" if t in times else "",
     fmt(r.get("TA_F")),r.get("TA_F_QC",""),
     fmt(r.get("VPD_F")),r.get("VPD_F_QC",""),
     rfmt(r.get("TA_F"),r.get("VPD_F")),
     fmt(r.get("TA_ERA")),fmt(r.get("VPD_ERA")),
     rfmt(r.get("TA_ERA"),r.get("VPD_ERA")),
     fmt(r.get("P_F")),fmt(r.get("SW_IN_F"))]))
 print("\nSTAGE77 NEGATIVE_RH_TIMES",",".join(t for t,_ in neg))
 print("STAGE77 SOURCE_VALID_RH_TIMES",",".join(t for t,_ in positive))
 print("STAGE77 COMPLETE READONLY | NO ORIGINAL SOURCE/QC/APPROVED259/DATM/CIME/SLURM MODIFICATIONS")
if __name__=="__main__":main()

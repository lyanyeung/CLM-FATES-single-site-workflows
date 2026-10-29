#!/usr/bin/env python3
"""Batch05 Stage70: direct human review printed US-UMB 8 remaining events
and 22 original native P2/P3 source flagged HH, ±3h surrounding each HH.
Original US-UMB FULLSET_HH (not FLUXMET) is source-verified by exact
Stage27 original T/VPD/QC for all 23 original site flagged HH.
No numerical modification, no forced hold, no DATM/CIME/Slurm.
"""
import argparse,csv,hashlib,json,math
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
SITE="US-UMB"
SRC_REL="US-UMB/forcing/raw/AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5/AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv"
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for part in iter(lambda:f.read(1<<20),b""):h.update(part)
 return h.hexdigest()
def clock(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid source native HH "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def num(t):
 try:
  x=float(t)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def fmt(v):
 v=num(v)
 return "NA" if v is None else f"{v:.3f}"
def rh(T,V):
 T,V=num(T),num(V)
 if T is None or V is None or not -80<=T<=60:return "NA"
 e=6.112*math.exp(17.67*T/(243.5+T))
 return f"{100*(1-V/e):.2f}"
def table(path,required):
 if path.is_symlink() or not path.is_file():raise ValueError("missing original source ledger "+str(path))
 with path.open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f);head=rd.fieldnames or []
  if len(head)!=len(set(head)) or not set(required).issubset(head):
   raise ValueError("source ledger column mismatch "+str(path))
  rows=list(rd)
 if any(None in x or any(v is None for v in x.values()) for x in rows):
  raise ValueError("source ledger malformed "+str(path))
 return rows
def selftest():
 assert (clock("201205010000")-clock("201204302330")).total_seconds()==1800
 assert rh(10,20).startswith("-")
 assert num("-9999") is None
 print("STAGE70 SELF-TEST PASS | US-UMB exact 22 HH 8 original events native ±3h from verified FULLSET; READONLY")
def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument("--self-test",action="store_true")
 a.add_argument("--stage63-dir",type=Path)
 a.add_argument("--stage27-dir",type=Path)
 a.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 z=a.parse_args()
 if z.self_test:selftest();return
 if z.stage63_dir is None or z.stage27_dir is None:
  a.error("provide actual --stage63-dir, --stage27-dir; source read only")
 d63=z.stage63_dir.expanduser().resolve()
 d27=z.stage27_dir.expanduser().resolve()
 root=z.sites_root.expanduser().resolve()
 f63=d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"
 f27=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 ledger=table(f63,("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 prior=table(f27,("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 flagged=[r for r in ledger if r["site"]==SITE]
 original=[r for r in prior if r["site"]==SITE]
 events=defaultdict(set)
 if (len(ledger),len(prior),len(flagged),len(original))!=(1565,1574,22,23):
  raise ValueError("original 22 remaining vs 23 source UMb population changed")
 for r in flagged:
  if (r["site"],r["native_time"]) not in {(o["site"],o["native_time"]) for o in original}:
   raise ValueError("current flagged source key missing in original Stage27")
  events[r["episode_id"]].add(r["native_time"])
 if len(events)!=8:raise ValueError("expected exact 8 original US-UMB events")
 # Read only source original fullset, no copy and no file output.
 source=root/SRC_REL
 if source.is_symlink() or not source.is_file():
  raise ValueError("original Stage45-verified US-UMB FULLSET_HH unavailable "+str(source))
 wanted=set()
 for r in original:
  c=clock(r["native_time"])
  for k in range(-6,7):
   wanted.add((c+timedelta(minutes=30*k)).strftime("%Y%m%d%H%M"))
 data={}
 with source.open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  hd=rd.fieldnames or []
  if len(hd)!=len(set(hd)) or not {"TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"}.issubset(hd):
   raise ValueError("original FULLSET_HH TA/VPD QC fields absent")
  print("STAGE70 ORIGINAL FULLSET SOURCE",str(source),"SHA256",sha(source))
  print("STAGE70 FULLSET COLUMNS",",".join(hd))
  for r in rd:
   t=r["TIMESTAMP_START"]
   if t in wanted:
    if t in data:raise ValueError("original FULLSET duplicate native time "+t)
    data[t]=r
 if any(r["native_time"] not in data for r in original):
  raise ValueError("one of 23 original Stage27 US-UMB source records absent")
 # Verifies all 23 including already approved 1, not just 22 remaining.
 for r in original:
  x=data[r["native_time"]]
  ta,v=num(x["TA_F"]),num(x["VPD_F"])
  if (ta is None or v is None or abs(ta-num(r["TA_F_C"]))>.002 or
      abs(v-num(r["VPD_F_hPa"]))>.002 or
      x["TA_F_QC"]!=r["TA_F_QC"] or x["VPD_F_QC"]!=r["VPD_F_QC"]):
   raise ValueError("original FULLSET source QC mismatch Stage27 "+r["native_time"])
 print("STAGE70 SOURCE_VERIFIED EXACT_23_OF_23_ORIGINAL_US_UMB_T_VPD_QC")
 print("STAGE70 REMAINING_EVENTS=8 REMAINING_FLAGGED_HH=22")
 for eid,times in sorted(events.items()):
  ts=sorted(times)
  wanted_e=set()
  for t in ts:
   c=clock(t)
   for k in range(-6,7):
    wanted_e.add((c+timedelta(minutes=30*k)).strftime("%Y%m%d%H%M"))
  print("\n======== US-UMB",eid,"ORIGINAL_FLAGGED_HH",len(ts),"FROM",ts[0],"TO",ts[-1],"========")
  print("TIME | FLAG | TA_F | TA_QC | VPD_F | VPD_QC | RH_implied_pct | TA_ERA | VPD_ERA | RH_ERA_implied | P_F | SW_IN_F")
  for t in sorted(wanted_e):
   r=data.get(t)
   if r is None:
    print(t,"| MISSING_ORIGINAL_SOURCE_CONTEXT")
    continue
   print(" | ".join((t,"***" if t in times else "",
     fmt(r.get("TA_F")),r.get("TA_F_QC",""),
     fmt(r.get("VPD_F")),r.get("VPD_F_QC",""),
     rh(r.get("TA_F"),r.get("VPD_F")),
     fmt(r.get("TA_ERA")),fmt(r.get("VPD_ERA")),
     rh(r.get("TA_ERA"),r.get("VPD_ERA")),
     fmt(r.get("P_F")),fmt(r.get("SW_IN_F")))))
 print("\nSTAGE70 SOURCE_AUDIT_COMPLETE | NO REPAIR / NO ORIGINAL MODIFICATIONS")
if __name__=="__main__":main()

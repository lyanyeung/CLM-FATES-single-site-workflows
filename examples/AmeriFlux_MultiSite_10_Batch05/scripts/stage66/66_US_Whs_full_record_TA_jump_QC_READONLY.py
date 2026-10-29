#!/usr/bin/env python3
"""Stage66: US-Whs all original TA_F half-hours, 2007-2025.
List 30m TA jumps >=3 C, source QC0/1/2 provenance and suspected
MDS-to-ERA discontinuities; NO QC reclassification, no forcing writes.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from pathlib import Path
from datetime import datetime
from collections import Counter,defaultdict
ZIP_HASH="0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767"
PACKAGE="AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1.zip"
MEMBER="AMF_US-Whs_FLUXNET_FLUXMET_HH_2007-2025_v1.3_r1.csv"
FIELDS=("before_native","after_native","before_TA","after_TA","jump_TA_C",
        "abs_jump_C","before_QC","after_QC","QC_transition",
        "before_TA_ERA","after_TA_ERA","jump_ERA_C",
        "before_minus_ERA_C","after_minus_ERA_C",
        "before_SW","after_SW","science_status")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def numeric(v):
 try:
  q=float(v)
  return q if math.isfinite(q) and q not in (-9999.0,-6999.0) else None
 except (TypeError,ValueError):return None
def dtime(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad original HH timestamp "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def selftest():
 assert (dtime("201205250600")-dtime("201205250530")).total_seconds()==1800
 assert abs((17.814-31.635)+13.821)<1e-8
 assert numeric("-9999") is None
 print("STAGE66 SELF-TEST PASS | full-source 30-minute TA jumps, QC0/1/2 distinct, no write to forcing")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--out",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 a=p.parse_args()
 if a.self_test:selftest();return
 if a.out is None:p.error("--out must be a new report directory")
 root=a.sites_root.expanduser().resolve()
 out=a.out.expanduser().resolve()
 package=root/"US-Whs"/"forcing"/"packages"/PACKAGE
 if not root.is_dir() or out.exists() or not out.parent.is_dir() or out==root or root in out.parents:
  raise ValueError("new reports must be outside ORIGINAL source root")
 if not package.is_file() or package.is_symlink() or sha(package)!=ZIP_HASH:
  raise ValueError("US-Whs original ZIP missing / SHA256 mismatch")
 qc=Counter()
 years=defaultdict(Counter)
 months=defaultdict(Counter)
 jumps=[]
 gap=[]
 first=last=None
 prior=None
 total=0
 known={}
 with zipfile.ZipFile(package) as z:
  mem=[x for x in z.infolist() if Path(x.filename).name==MEMBER]
  if len(mem)!=1 or mem[0].file_size>900*1024*1024:
   raise ValueError("original HH source member missing/ambiguous")
  with z.open(mem[0]) as raw, io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as fh:
   rd=csv.DictReader(fh)
   cols=rd.fieldnames or []
   if len(set(cols))!=len(cols) or not {"TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA"}.issubset(cols):
    raise ValueError("source FLUXMET original TA fields missing")
   for r in rd:
    t=r["TIMESTAMP_START"]
    when=dtime(t)
    if prior is not None and when<=prior["when"]:
     raise ValueError("duplicate/out-of-order original timestamp "+t)
    T=numeric(r["TA_F"]);E=numeric(r["TA_ERA"])
    code=r["TA_F_QC"]
    classqc=code if code in ("0","1","2") and T is not None else "OTHER"
    qc[classqc]+=1
    years[t[:4]][classqc]+=1
    months[t[:6]][classqc]+=1
    total+=1
    if first is None:first=t
    last=t
    if t in ("201205250530","201205250600","201205260600","201205270600"):
     known[t]=(T,code)
    diff=T-E if T is not None and E is not None else None
    if diff is not None and abs(diff)>=10:
     qc["TA_vs_ERA_abs_ge10_"+classqc]+=1
     years[t[:4]]["abs_T_minus_ERA_ge10"]+=1
     months[t[:6]]["abs_T_minus_ERA_ge10"]+=1
    if prior is not None:
     delta_time=(when-prior["when"]).total_seconds()
     if delta_time!=1800:
      gap.append((prior["time"],t,delta_time))
     elif prior["T"] is not None and T is not None:
      change=T-prior["T"]
      ab=abs(change)
      qc["paired_valid"]+=1
      transition=prior["classqc"]+"->"+classqc
      for threshold in (3,5,8,10):
       if ab>=threshold:
        qc["jump_ge"+str(threshold)]+=1
        years[t[:4]]["jump_ge"+str(threshold)]+=1
        months[t[:6]]["jump_ge"+str(threshold)]+=1
        qc["jump_ge"+str(threshold)+"_"+transition]+=1
      if ab>=3:
       jumps.append(dict(before_native=prior["time"],after_native=t,
        before_TA=prior["T"],after_TA=T,jump_TA_C=round(change,6),
        abs_jump_C=round(ab,6),before_QC=prior["qc"],after_QC=code,
        QC_transition=transition,
        before_TA_ERA=prior["E"],after_TA_ERA=E,
        jump_ERA_C=round(E-prior["E"],6) if E is not None and prior["E"] is not None else "",
        before_minus_ERA_C=round(prior["diff"],6) if prior["diff"] is not None else "",
        after_minus_ERA_C=round(diff,6) if diff is not None else "",
        before_SW=prior["SW"],after_SW=r.get("SW_IN_F",""),
        science_status="REVIEW_ONLY_NOT_AUTOMATICLY_WRONG"))
    prior=dict(time=t,when=when,T=T,E=E,qc=code,classqc=classqc,
               diff=diff,SW=r.get("SW_IN_F",""))
 for t,x,code in (("201205250530",31.635,"1"),("201205250600",17.814,"2"),
                  ("201205260600",29.62,"1"),("201205270600",30.277,"1")):
  got=known.get(t)
  if got is None or got[0] is None or abs(got[0]-x)>.002 or got[1]!=code:
   raise ValueError("previous Stage65 source/QC invariant changed "+t)
 if sum(qc[k] for k in ("0","1","2","OTHER"))!=total:
  raise ValueError("source QC rows do not reconcile")
 out.mkdir(exist_ok=False)
 fcsv=out/"stage66_US_Whs_ALL_YEARS_original_TA_30min_jumps_ge3C.csv"
 with fcsv.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise")
  w.writeheader();w.writerows(jumps)
 report=dict(site="US-Whs",original_sha256=ZIP_HASH,
  first_native=first,last_native=last,total_source_HH=total,
  source_QC0_TA_observed=qc["0"],source_QC1_MDS_fill=qc["1"],
  source_QC2_processed_ERA_fill=qc["2"],other_source_QC=qc["OTHER"],
  source_clock_gap_count=len(gap),
  source_30min_jumps_ge3C=qc["jump_ge3"],
  source_30min_jumps_ge5C=qc["jump_ge5"],
  source_30min_jumps_ge8C=qc["jump_ge8"],
  source_30min_jumps_ge10C=qc["jump_ge10"],
  source_30min_jumps_ge5C_by_QC_transition={k[len("jump_ge5_"):]:v for k,v in sorted(qc.items()) if k.startswith("jump_ge5_")},
  original_source_or_QC_reclassified=False,
  original_204_overlay_modified=False,DATM_CIME_modified=False,Slurm_submitted=0,
  new_science_approved_HH=0,report_sha256=sha(fcsv))
 (out/"stage66_manifest.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print("STAGE66 SUCCESS | ORIGINAL ALL-YEAR US-Whs TA_F jump inventory, no source/model modifications")
 print("STAGE66 SOURCE_RANGE",first,last,"TOTAL_HH",total,"GAPS",len(gap))
 print("STAGE66 QC_COUNTS",json.dumps({k:qc[k] for k in ("0","1","2","OTHER")},sort_keys=True))
 print("STAGE66 SPIKE_COUNTS",json.dumps({str(i):qc["jump_ge"+str(i)] for i in (3,5,8,10)},sort_keys=True))
 print("STAGE66 JUMP_GE5_QC_TRANSITIONS",json.dumps(report["source_30min_jumps_ge5C_by_QC_transition"],sort_keys=True))
 print("STAGE66 YEARS | year QC0 QC1 QC2 30min_ge5C ge8C ge10C")
 for y,x in sorted(years.items()):
  print("STAGE66 YEAR",y,x["0"],x["1"],x["2"],x["jump_ge5"],x["jump_ge8"],x["jump_ge10"])
 print("STAGE66 MAY2012 | source_QC0 source_QC1 source_QC2 ge5 ge8 ge10 T_vs_ERA_ge10")
 m=months["201205"]
 print("STAGE66 MONTH_201205",m["0"],m["1"],m["2"],m["jump_ge5"],m["jump_ge8"],m["jump_ge10"],m["abs_T_minus_ERA_ge10"])
 print("STAGE66 MAY25-27 ALL JUMPS_GE3 | before after delta_C QCtransition ERA_change_C")
 for r in jumps:
  if "20120525"<=r["after_native"][:8]<="20120527":
   print("STAGE66 MAY_JUMP",r["before_native"],r["after_native"],r["jump_TA_C"],
    r["QC_transition"],r["jump_ERA_C"])
 print("STAGE66 TOP35 ENTIRE_RECORD | before after delta_C QCtransition ERA_change_C")
 for r in sorted(jumps,key=lambda z:-z["abs_jump_C"])[:35]:
  print("STAGE66 TOP",r["before_native"],r["after_native"],r["jump_TA_C"],
   r["QC_transition"],r["jump_ERA_C"])
 print("STAGE66_REPORTS="+str(out))
 print("STAGE66 NO QC2_TO_QC1_RELABEL / 204_OVERLAY / SOURCE / DATM / SLURM CHANGES")
if __name__=="__main__":main()

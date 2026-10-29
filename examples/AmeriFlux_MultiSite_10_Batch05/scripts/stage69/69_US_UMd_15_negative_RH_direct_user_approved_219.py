#!/usr/bin/env python3
"""Batch05 Stage69: directly APPLY investigator-approved US-UMd <0% RH
repairs as a new VERSIONED APPROVED RH/VPD overlay (204+15=219).
Use immediate physically valid source-neighbor RH interpolation and
source measured QC0 TA_F. This is an approved data-repair overlay, NOT
a tentative candidate decision; do not rewrite original AmeriFlux ZIP,
historical QC, other records, prior 204 rows or production DATM.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime,timedelta

SITE="US-UMd"
PKG_SHA="27095ccd71a1c28cee5e730ca2ad99d0acb6fba7a4be07ffaa8cff7a41f2e3c5"
SCHEMA=("site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct",
 "modified_TA_C","modified_RH_pct","modified_VPD_hPa",
 "delta_VPD_hPa","replacement_RH_provenance","new_VPD_derivation",
 "source_QC_provenance_only","overlay_status")
AUDIT=("site","episode_id","native_time","source_TA_C","source_TA_QC",
 "source_VPD_hPa","source_VPD_QC","source_implied_RH_pct",
 "left_native","left_RH_pct","left_source_VPD_QC","right_native",
 "right_RH_pct","right_source_VPD_QC",
 "approved_RH_pct","approved_VPD_hPa","source_ERA_T_C",
 "source_ERA_VPD_hPa","approved_scope")

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
def when(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("invalid original native HH "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def es(t):
 if t is None or not -80<=t<=60:raise ValueError("invalid measured TA")
 return 6.112*math.exp(17.67*t/(243.5+t))
def rh(t,v):
 if t is None or v is None:return None
 return 100*(1-v/es(t))
def fmt(v):
 return "" if v is None else f"{v:.9f}"
def read(p,cols):
 if p.is_symlink() or not p.is_file():raise ValueError("missing prior original report "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f);hd=rd.fieldnames or []
  if not set(cols).issubset(hd) or len(hd)!=len(set(hd)):
   raise ValueError("source report columns drift "+str(p))
  rows=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed source report "+str(p))
 return rows
def keyed(data):
 out={}
 for r in data:
  k=(r["site"],r["native_time"])
  if k in out or len(k[1])!=12:raise ValueError("duplicate/malformed source record "+str(k))
  out[k]=r
 return out
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert abs(es(7.062)-10.0577)<.15
 assert abs(rh(7.062,10.671)-(-6.1))<.1
 left,right=25.90,9.10
 assert 9.1<(left+right)/2<25.9
 assert 204+15==219
 print("STAGE69 SELF-TEST PASS | exact US-UMd 15 negative RH QC0 TA + QC1 VPD; direct approved overlay; original untouched")

def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument("--self-test",action="store_true")
 a.add_argument("--stage63-dir",type=Path)
 a.add_argument("--stage62-dir",type=Path)
 a.add_argument("--stage27-dir",type=Path)
 a.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 a.add_argument("--out",type=Path)
 z=a.parse_args()
 if z.self_test:selftest();return
 if any(x is None for x in (z.stage63_dir,z.stage62_dir,z.stage27_dir,z.out)):
  a.error("require exact Stage63 Stage62 Stage27 source dirs and NEW output dir")
 d63,d62,d27,root,out=(x.expanduser().resolve() for x in
  (z.stage63_dir,z.stage62_dir,z.stage27_dir,z.sites_root,z.out))
 if (not all(p.is_dir() for p in (d63,d62,d27,root)) or out.exists()
     or not out.parent.is_dir() or any(out==p or out in p.parents or p in out.parents for p in (d63,d62,d27,root))):
  a.error("existing source report dirs required; new output separate from sources")
 oldcsv=d62/"stage62_VERSIONED_204_APPROVED_RH_VPD_native_overlay.csv"
 m62=json.loads((d62/"stage62_manifest.json").read_text())
 if (m62.get("total_versioned_approved_candidate_HH")!=204 or
     m62.get("output_sha256",{}).get(oldcsv.name)!=sha(oldcsv)):
  raise ValueError("previous 204 overlay no longer matches approved Stage62 SHA")
 old=keyed(read(oldcsv,SCHEMA))
 if len(old)!=204:raise ValueError("prior 204 overlay count changed")
 f63=d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"
 fsite=d63/"stage63_EXACT_TEN_SITE_REMAINING_AFTER_204.csv"
 f27=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 ledger=read(f63,("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 p63=read(fsite,("site","remaining_original_P2P3_HH","remaining_original_P2P3_events"))
 prior=read(f27,("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 if len(ledger)!=1565 or len(p63)!=10 or len(prior)!=1574:
  raise ValueError("original 63/27 source cohort drift")
 umd=[r for r in ledger if r["site"]==SITE]
 umd_site=[r for r in p63 if r["site"]==SITE]
 if (len(umd)!=15 or len(set(r["episode_id"] for r in umd))!=6 or
     len(umd_site)!=1 or umd_site[0]["remaining_original_P2P3_HH"]!="15" or
     umd_site[0]["remaining_original_P2P3_events"]!="6"):
  raise ValueError("original remaining US-UMd 15 HH / six episode identity drift")
 reference={(r["site"],r["native_time"]):r for r in prior if r["site"]==SITE}
 if len(reference)!=15 or set(reference)!={(SITE,r["native_time"]) for r in umd}:
  raise ValueError("actual Stage27 15 UMd original timestamps no longer exact")
 keys={(SITE,r["native_time"]) for r in umd}
 if keys & set(old):raise ValueError("one approved 204 already overlaps US-UMd 15")
 base=root/SITE/"forcing"
 archives=[]
 for p in sorted(base.rglob("*.zip")):
  if p.is_file() and not p.is_symlink() and sha(p)==PKG_SHA:archives.append(p)
 if len(archives)!=1:raise ValueError("expected one exact original US-UMd FLUXMET ZIP with pinned Stage45 SHA; found "+str(len(archives)))
 package=archives[0]
 times={r["native_time"] for r in umd}
 need=set(times)
 for t in times:
  a=when(t)
  for k in (-1,1):
   need.add((a+timedelta(minutes=30*k)).strftime("%Y%m%d%H%M"))
 raw={}
 with zipfile.ZipFile(package) as zp:
  member=[m for m in zp.infolist() if
          Path(m.filename).name.startswith("AMF_US-UMd_FLUXNET_FLUXMET_HH_") and
          Path(m.filename).suffix.lower()==".csv"]
  if len(member)!=1 or member[0].file_size>900*1024*1024:
   raise ValueError("original US-UMd FLUXMET HH source ambiguous")
  with zp.open(member[0]) as b, io.TextIOWrapper(b,encoding="utf-8-sig",newline="") as f:
   rd=csv.DictReader(f);hd=rd.fieldnames or []
   need_cols={"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}
   if not need_cols.issubset(hd) or len(hd)!=len(set(hd)):
    raise ValueError("original source T/VPD/QC/ERA columns missing")
   for r in rd:
    t=r["TIMESTAMP_START"]
    if t in need:
     if t in raw:raise ValueError("duplicate original HH "+t)
     raw[t]=r
 if not need.issubset(raw):
  raise ValueError("original US-UMd one-HH science context records missing "+str(sorted(need-set(raw))))
 for r in umd:
  k=(SITE,r["native_time"])
  o=raw[r["native_time"]];rr=reference[k]
  if (rr["episode_id"]!=r["episode_id"] or o["TA_F_QC"]!="0" or o["VPD_F_QC"]!="1" or
      rr["TA_F_QC"]!="0" or rr["VPD_F_QC"]!="1" or
      abs(num(o["TA_F"])-num(rr["TA_F_C"]))>.002 or
      abs(num(o["VPD_F"])-num(rr["VPD_F_hPa"]))>.002):
   raise ValueError("original source Stage27 T/VPD/QC altered at "+r["native_time"])
 flagged=set(times)
 # Each original event consists of contiguous original negative-RH times.
 events=defaultdict(list)
 for r in umd:events[r["episode_id"]].append(r["native_time"])
 expected_sizes=sorted([1,1,2,2,4,5])
 if sorted(map(len,events.values()))!=expected_sizes:
  raise ValueError("original US-UMd event sizes changed")
 approved={};audit=[]
 for eid,ts in sorted(events.items()):
  ts=sorted(ts)
  if any((when(ts[i+1])-when(ts[i])).total_seconds()!=1800 for i in range(len(ts)-1)):
   raise ValueError("original event noncontiguous "+eid)
  left=(when(ts[0])-timedelta(minutes=30)).strftime("%Y%m%d%H%M")
  right=(when(ts[-1])+timedelta(minutes=30)).strftime("%Y%m%d%H%M")
  lrow,rrow=raw[left],raw[right]
  lt,lv=num(lrow["TA_F"]),num(lrow["VPD_F"])
  rt,rv=num(rrow["TA_F"]),num(rrow["VPD_F"])
  l,r=rh(lt,lv),rh(rt,rv)
  # QC1 VPD anchors are filled and not measured, but are explicit original
  # source continuous neighbor RH values approved by the operator for this repair.
  if (l is None or r is None or not 0<=l<=100 or not 0<=r<=100 or
      lrow["VPD_F_QC"]!="1" or rrow["VPD_F_QC"]!="1"):
   raise ValueError("one event lacks two QC1 finite nonnegative direct neighbor RH anchors "+eid)
  for j,t in enumerate(ts,1):
   o=raw[t]
   T,V=num(o["TA_F"]),num(o["VPD_F"])
   pre=rh(T,V)
   if (T is None or V is None or pre is None or pre>=0 or o["TA_F_QC"]!="0"
       or o["VPD_F_QC"]!="1"):
    raise ValueError("negative RH original QC0/1 user approval criterion failed "+t)
   interp=l+(r-l)*j/(len(ts)+1)
   newv=es(T)*(1-interp/100)
   if not (0<=interp<=100 and 0<=newv<=es(T) and abs(rh(T,newv)-interp)<1e-8):
    raise ValueError("direct interpolated RH or VPD nonphysical "+t)
   et,ev=num(o.get("TA_ERA")),num(o.get("VPD_ERA"))
   era_rh=rh(et,ev)
   cohort="STAGE69_USER_APPROVED_UMD_NEGATIVE_RH_DIRECT_REPAIR"
   record=dict(
    site=SITE,native_time=t,source_cohort=cohort,
    decision_id="UMD_15HH_NEGATIVE_RH_USER_DIRECT_APPROVAL_20261029_"+eid,
    source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
    source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
    source_RH_pct=o.get("RH",""),
    source_processed_ERA_T_C=o["TA_ERA"],
    source_processed_ERA_VPD_hPa=o["VPD_ERA"],
    source_processed_ERA_RH_derived_pct=fmt(era_rh),
    modified_TA_C=o["TA_F"],modified_RH_pct=fmt(interp),
    modified_VPD_hPa=fmt(newv),delta_VPD_hPa=fmt(newv-V),
    replacement_RH_provenance="OPERATOR_APPROVED_INTERPOLATION_BETWEEN_IMMEDIATE_SOURCE_QC1_VPD_IMPLIED_NONNEGATIVE_RH_NOT_OBSERVED",
    new_VPD_derivation="MAGNUS_WATER_AT_ORIGINAL_MEASURED_TA_QC0",
    source_QC_provenance_only="ORIGINAL_TA_QC0_AND_VPD_QC1_RETAINED_NO_QC_RELABEL",
    overlay_status="USER_DIRECT_APPROVED_20261029_VERSIONED_REPAIR_NOT_YET_DATM_APPLIED")
   if set(record)!=set(SCHEMA) or (SITE,t) in approved:
    raise ValueError("approved row schema/duplicate "+t)
   approved[(SITE,t)]=record
   audit.append(dict(site=SITE,episode_id=eid,native_time=t,
    source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
    source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
    source_implied_RH_pct=fmt(pre),left_native=left,left_RH_pct=fmt(l),
    left_source_VPD_QC=lrow["VPD_F_QC"],right_native=right,
    right_RH_pct=fmt(r),right_source_VPD_QC=rrow["VPD_F_QC"],
    approved_RH_pct=fmt(interp),approved_VPD_hPa=fmt(newv),
    source_ERA_T_C=o["TA_ERA"],source_ERA_VPD_hPa=o["VPD_ERA"],
    approved_scope="DIRECT_OPERATOR_APPROVAL_IN_NEW_VERSIONED_219_RH_VPD_OVERLAY"))
 if len(approved)!=15 or len(audit)!=15:raise ValueError("approved 15/15 reconciliation failed")
 together=dict(old);together.update(approved)
 if len(together)!=219 or any(together[k]!=old[k] for k in old):
  raise ValueError("original 204 approved exact text no longer preserved")
 out.mkdir(exist_ok=False)
 fall=out/"stage69_VERSIONED_219_USER_APPROVED_RH_VPD_native_overlay.csv"
 fnew=out/"stage69_EXACT_15_NEW_DIRECT_APPROVED_UMd_RH_VPD_REPAIRS.csv"
 fa=out/"stage69_15_ORIGINAL_AND_REPAIRED_NATIVE_HH_WITH_RH_ANCHORS.csv"
 write(fall,SCHEMA,[together[k] for k in sorted(together)])
 write(fnew,SCHEMA,[approved[k] for k in sorted(approved)])
 write(fa,AUDIT,audit)
 if len(read(fall,SCHEMA))!=219:raise ValueError("219 versioned overlay readback failed")
 manifest=dict(site=SITE,stage="69",
  original_FLUXMET_SHA256=PKG_SHA,prior_204_SHA256=sha(oldcsv),
  source_stage63_SHA256=sha(f63),source_stage27_SHA256=sha(f27),
  previous_204_approved_versioned_HH_unchanged=True,
  new_operator_directly_approved_negative_RH_HH=15,
  original_6_episodes_directly_approved=6,total_user_approved_versioned_HH=219,
  replacement_method="linear RH between original immediate nonnegative source QC1 implied RH anchors, rescale VPD at original measured TA",
  moisture_source_anchors_are_source_QC1_filled_not_measured=True,
  source_TA_QC0_protected=True,original_TA_VPD_QC_provenance_preserved=True,
  approved_repair_is_versioned_overlay_not_original_source_rewrite=True,
  original_FLUXMET_changed=False,previous_204_overlay_changed=False,
  DATM_CIME_forcing_changed=False,Slurm_jobs_submitted=0,
  outputs_sha256={p.name:sha(p) for p in (fall,fnew,fa)})
 (out/"stage69_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("STAGE69 SUCCESS | USER DIRECT APPROVAL | US-UMd 6 events 15 ORIGINAL RH<0 HH fixed")
 print("STAGE69 APPROVAL PRIOR 204 UNCHANGED + NEW UMD 15 = 219 VERSIONED APPROVED RH/VPD")
 print("STAGE69 DIRECT_REPAIRS native_time old_RH new_RH old_VPD new_VPD original_T_QC original_VPD_QC")
 for r in audit:
  print("STAGE69 APPROVED",r["native_time"],
   f"{float(r['source_implied_RH_pct']):.3f}",f"{float(r['approved_RH_pct']):.3f}",
   r["source_VPD_hPa"],f"{float(r['approved_VPD_hPa']):.3f}",
   r["source_TA_QC"],r["source_VPD_QC"])
 print("STAGE69 APPROVED_219="+str(fall))
 print("STAGE69 APPROVED_219_SHA256="+sha(fall))
 print("STAGE69_REPORTS="+str(out))
 print("STAGE69 ORIGINAL/QC/OLD204/DATM/CIME/SLURM UNCHANGED; VERSIONED APPROVED REPAIR FILE CREATED")
if __name__=="__main__":main()

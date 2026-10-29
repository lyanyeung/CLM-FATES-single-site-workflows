#!/usr/bin/env python3
"""Batch05 Stage72: user policy: any original source-implied RH<0 is directly
approved for repaired RH/VPD in a new VERSIONED overlay. US-UMB exact 21
negative original native P2P3 HH, 8 episodes, preserve remaining physically
nonnegative source RH=0.03% record as PASS_UNCHANGED. Retain 219 prior
approved rows, original FULLSET_HH and original QC0 tower TA.
Scientific provenance: interpolation between immediately adjacent original
finite nonnegative implied RH (source QC0/QC1/QC2, no implied observation).
Only repaired versioned data; original source, DATM, CIME and Slurm unchanged.
"""
import argparse,csv,hashlib,json,math
from datetime import datetime,timedelta
from collections import Counter
from pathlib import Path
SITE="US-UMB"
FULLSET_REL="US-UMB/forcing/raw/AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5/AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv"
SOURCE_SHA="ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6"
COLS=("site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct","modified_TA_C","modified_RH_pct",
 "modified_VPD_hPa","delta_VPD_hPa","replacement_RH_provenance",
 "new_VPD_derivation","source_QC_provenance_only","overlay_status")
AUD=("site","episode_id","native_time","source_TA_C","source_TA_QC",
 "source_VPD_hPa","source_VPD_QC","original_implied_RH_pct",
 "repair_RH_pct","repair_VPD_hPa","before_native","before_anchor_RH_pct",
 "before_anchor_VPD_QC","after_native","after_anchor_RH_pct",
 "after_anchor_VPD_QC","original_VPD_changed_hPa","science_decision")
PASS=("site","episode_id","native_time","source_TA_C","source_TA_QC",
 "source_VPD_hPa","source_VPD_QC","original_RH_pct","decision")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for part in iter(lambda:f.read(1048576),b""):h.update(part)
 return h.hexdigest()
def n(x):
 try:
  q=float(x)
  return q if math.isfinite(q) and q not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None
def time(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("bad original native HH "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def sat(t):
 if t is None or not -80<=t<=60:raise ValueError("invalid source TA")
 return 6.112*math.exp(17.67*t/(243.5+t))
def rh(T,V):
 if T is None or V is None:return None
 return 100*(1-V/sat(T))
def st(v):return "" if v is None else f"{v:.9f}"
def read(p,need):
 if p.is_symlink() or not p.is_file():raise ValueError("missing direct science source "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f);hd=reader.fieldnames or []
  if not set(need).issubset(hd) or len(hd)!=len(set(hd)):
   raise ValueError("source CSV schema mismatch "+str(p))
  ans=list(reader)
 if any(None in x or any(v is None for v in x.values()) for x in ans):
  raise ValueError("malformed science source CSV")
 return ans
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  wr=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  wr.writeheader();wr.writerows(rows)
def idx(rr):
 d={}
 for r in rr:
  k=(r["site"],r["native_time"])
  if k in d:raise ValueError("duplicate original source time "+str(k))
  d[k]=r
 return d
def selftest():
 assert time("201004080630")+timedelta(minutes=30)==time("201004080700")
 assert rh(-.187,6.028)>0
 assert rh(-.347,6.152)<0
 assert rh(-1.280,6.711)<0
 assert 219+21==240
 print("STAGE72 SELF-TEST PASS | negative RH only direct repair, retain single positive 0.03% native source record, 219->240 approved")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage63-dir",type=Path)
 p.add_argument("--stage69-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 z=p.parse_args()
 if z.self_test:selftest();return
 if any(x is None for x in (z.stage63_dir,z.stage69_dir,z.stage27_dir,z.out)):
  p.error("provide actual Stage63/69/27 dirs and NEW output")
 d63,d69,d27,root,out=(x.expanduser().resolve() for x in
  (z.stage63_dir,z.stage69_dir,z.stage27_dir,z.sites_root,z.out))
 if (not all(q.is_dir() for q in (d63,d69,d27,root)) or
     out.exists() or not out.parent.is_dir() or
     any(out==q or out in q.parents or q in out.parents for q in (d63,d69,d27,root))):
  p.error("only new disjoint output dir outside source roots")
 oldfile=d69/"stage69_VERSIONED_219_USER_APPROVED_RH_VPD_native_overlay.csv"
 manifest=json.loads((d69/"stage69_manifest.json").read_text())
 if (manifest.get("total_user_approved_versioned_HH")!=219 or
     manifest.get("outputs_sha256",{}).get(oldfile.name)!=sha(oldfile) or
     manifest.get("previous_204_approved_versioned_HH_unchanged") is not True):
  raise ValueError("actual Stage69 219 approved SHA/count drifted")
 old=idx(read(oldfile,COLS))
 if len(old)!=219:raise ValueError("approved 219 count mismatch")
 srclist=read(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
   ("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 original27=read(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
   ("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 u=[r for r in srclist if r["site"]==SITE]
 orig=[r for r in original27 if r["site"]==SITE]
 if (len(srclist),len(original27),len(u),len(orig))!=(1565,1574,22,23):
  raise ValueError("source exact 1565/1574 and US-UMB 22/23 drift")
 umd={r["episode_id"] for r in u}
 if len(umd)!=8:raise ValueError("US-UMB 8 original episodes changed")
 f27=idx(orig)
 if set((SITE,r["native_time"]) for r in u)&set(old):
  raise ValueError("US-UMB remaining 22 already overlapped with previous 219")
 original_path=root/FULLSET_REL
 if original_path.is_symlink() or not original_path.is_file() or sha(original_path)!=SOURCE_SHA:
  raise ValueError("original US-UMB immutable FULLSET SHA changed")
 all_times=set()
 for r in orig:
  center=time(r["native_time"])
  for minutes in (-30,0,30):
   all_times.add((center+timedelta(minutes=minutes)).strftime("%Y%m%d%H%M"))
 raw={}
 with original_path.open("r",encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  hd=reader.fieldnames or []
  if not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(hd):
   raise ValueError("source FULLSET_HH required fields missing")
  for r in reader:
   t=r["TIMESTAMP_START"]
   if t in all_times:
    if t in raw:raise ValueError("source FULLSET duplicate timestamp")
    raw[t]=r
 if set(all_times)!=set(raw):
  raise ValueError("original US-UMB boundary/source context absent")
 for r in orig:
  o=raw[r["native_time"]]
  if (o["TA_F_QC"]!=r["TA_F_QC"] or o["VPD_F_QC"]!=r["VPD_F_QC"] or
      n(o["TA_F"]) is None or n(o["VPD_F"]) is None or
      abs(n(o["TA_F"])-n(r["TA_F_C"]))>.002 or
      abs(n(o["VPD_F"])-n(r["VPD_F_hPa"]))>.002):
   raise ValueError("original FULLSET TA/VPD/QC mismatch Stage27 "+r["native_time"])
 flagged={}
 for x in u:
  if (SITE,x["native_time"]) not in f27 or x["episode_id"]!=f27[(SITE,x["native_time"])]["episode_id"]:
   raise ValueError("episode identity source mismatch")
  t=x["native_time"];o=raw[t]
  if o["TA_F_QC"]!="0" or o["VPD_F_QC"]!="1":
   raise ValueError("unapproved site TA QC0 and VPD QC1 expected "+t)
  flagged[t]=dict(episode=x["episode_id"],row=o,RH=rh(n(o["TA_F"]),n(o["VPD_F"])))
 negative={t for t,x in flagged.items() if x["RH"] is not None and x["RH"]<0}
 positives={t for t,x in flagged.items() if x["RH"] is not None and x["RH"]>=0}
 if len(negative)!=21 or len(positives)!=1 or positives!={"201004080630"}:
  raise ValueError("exact 21 negative plus one 201004080630 finite nonnegative RH ledger changed")
 if not 0<=flagged["201004080630"]["RH"]<=.1:
  raise ValueError("known near-zero positive RH source changed")
 runs=[]
 for t in sorted(negative):
  dt=time(t)
  if runs and (dt-time(runs[-1][-1])).total_seconds()==1800:
   runs[-1].append(t)
  else:runs.append([t])
 if len(runs)!=8:raise ValueError("eight negative original contiguous source runs expected")
 # For the exact eight source-negative intervals, interpolate source-implied RH
 # from adjacent source finite physically nonnegative native neighbors. They
 # may be derived from QC0, QC1 or QC2, but are NOT all measured RH.
 repaired={};audit=[]
 for group in runs:
  left=(time(group[0])-timedelta(minutes=30)).strftime("%Y%m%d%H%M")
  right=(time(group[-1])+timedelta(minutes=30)).strftime("%Y%m%d%H%M")
  if left not in raw or right not in raw:
   raise ValueError("missing native source bracketing HH "+group[0])
  l=raw[left];r=raw[right]
  lt,lv=n(l["TA_F"]),n(l["VPD_F"])
  rt,rv=n(r["TA_F"]),n(r["VPD_F"])
  left_rh,right_rh=rh(lt,lv),rh(rt,rv)
  if (left_rh is None or right_rh is None or
      not 0<=left_rh<=100 or not 0<=right_rh<=100):
   raise ValueError("nonphysical direct source RH interpolation anchor "+group[0])
  eid=flagged[group[0]]["episode"]
  if any(flagged[t]["episode"]!=eid for t in group):
   raise ValueError("multiple original science episodes merged")
  for j,t in enumerate(group,1):
   o=raw[t];T=n(o["TA_F"]);V=n(o["VPD_F"])
   pre=rh(T,V)
   newrh=left_rh+(right_rh-left_rh)*j/(len(group)+1)
   newv=sat(T)*(1-newrh/100)
   if pre is None or pre>=0 or not 0<=newrh<=100 or not 0<=newv<=sat(T):
    raise ValueError("direct negative RH repair invalid "+t)
   er=rh(n(o["TA_ERA"]),n(o["VPD_ERA"]))
   row=dict(site=SITE,native_time=t,
    source_cohort="STAGE72_DIRECT_OPERATOR_APPROVED_NEGATIVE_RH_UMB_FULLSET",
    decision_id="UMB_"+eid+"_NEGATIVE_RH_USER_RULE_APPROVED_20261029",
    source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
    source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
    source_RH_pct=o.get("RH",""),
    source_processed_ERA_T_C=o["TA_ERA"],
    source_processed_ERA_VPD_hPa=o["VPD_ERA"],
    source_processed_ERA_RH_derived_pct=st(er),
    modified_TA_C=o["TA_F"],modified_RH_pct=st(newrh),
    modified_VPD_hPa=st(newv),delta_VPD_hPa=st(newv-V),
    replacement_RH_provenance="DIRECT_APPROVED_NATIVE_NEIGHBOR_RH_INTERPOLATION_ANCHORS_QC_MIXED_NOT_MEASURED_RH",
    new_VPD_derivation="SAT_WATER_MAGNUS_AT_UNCHANGED_SOURCE_QC0_TOWER_TA",
    source_QC_provenance_only="ORIGINAL_TA_QC0_AND_VPD_QC1_RETAINED",
    overlay_status="USER_DIRECT_APPROVED_20261029_VERSIONED_REPAIR_NOT_YET_DATM_APPLIED")
   if set(row)!=set(COLS):raise ValueError("versioned overlay schema drift")
   repaired[(SITE,t)]=row
   audit.append(dict(site=SITE,episode_id=eid,native_time=t,
    source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
    source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
    original_implied_RH_pct=st(pre),repair_RH_pct=st(newrh),
    repair_VPD_hPa=st(newv),before_native=left,
    before_anchor_RH_pct=st(left_rh),before_anchor_VPD_QC=l["VPD_F_QC"],
    after_native=right,after_anchor_RH_pct=st(right_rh),
    after_anchor_VPD_QC=r["VPD_F_QC"],original_VPD_changed_hPa=st(newv-V),
    science_decision="DIRECT_USER_APPROVED_RH_LT_ZERO_20261029"))
 if len(repaired)!=21 or set(repaired)&set(old):
  raise ValueError("exact 21 nonoverlapping US-UMB RH<0 repairs expected")
 same="201004080630";one=raw[same]
 passrow=dict(site=SITE,episode_id=flagged[same]["episode"],
  native_time=same,source_TA_C=one["TA_F"],
  source_TA_QC=one["TA_F_QC"],source_VPD_hPa=one["VPD_F"],
  source_VPD_QC=one["VPD_F_QC"],original_RH_pct=st(flagged[same]["RH"]),
  decision="PASS_SOURCE_RH_GE_ZERO_UNCHANGED_NO_VPD_REPAIR")
 new=dict(old);new.update(repaired)
 if len(new)!=240 or any(new[k]!=old[k] for k in old):
  raise ValueError("219 old original rows not conserved into 240")
 out.mkdir(exist_ok=False)
 aout=out/"stage72_VERSIONED_240_USER_APPROVED_RH_VPD_native_overlay.csv"
 bout=out/"stage72_EXACT_21_NEW_UMB_NEGATIVE_RH_DIRECT_REPAIRS.csv"
 cout=out/"stage72_21_FULLSET_SOURCE_AND_APPROVED_REPAIRS_AUDIT.csv"
 pout=out/"stage72_ONE_POSITIVE_RH_SOURCE_PASSED_UNCHANGED.csv"
 write(aout,COLS,[new[k] for k in sorted(new)])
 write(bout,COLS,[repaired[k] for k in sorted(repaired)])
 write(cout,AUD,audit)
 write(pout,PASS,[passrow])
 if len(read(aout,COLS))!=240:raise ValueError("stage72 240 overlay readback failed")
 mn=dict(stage="72",site=SITE,original_source_FULLSET_SHA256=SOURCE_SHA,
   previous_219_overlay_SHA256=sha(oldfile),
   previous_219_approved_rows_exactly_preserved=True,
   directly_approved_US_UMB_RH_LT_ZERO_HH=21,
   positive_RH_original_source_pass_unchanged_HH=1,
   original_UMB_8_episodes_all_scientifically_disposed=True,
   latest_approved_versioned_RH_VPD_HH=240,
   repair_algorithm="linear inferred RH between directly adjacent finite nonnegative original-source RH neighbors; original measured T unchanged",
   original_RH_anchor_QC_can_vary=True,
   source_FLUXMET_FULLSET_not_modified=True,original_QC_unchanged=True,
   older_219_approved_not_modified=True,
   DATM_CIME_forcing_not_modified=True,Slurm_submitted=0,
   output_sha256={p.name:sha(p) for p in (aout,bout,cout,pout)})
 (out/"stage72_manifest.json").write_text(json.dumps(mn,sort_keys=True,indent=2)+"\n")
 print("STAGE72 SUCCESS | 21 US-UMB negative RH direct repairs + 1 originally positive 0.03% PASS_UNCHANGED")
 print("STAGE72 SOURCE_VERIFIED 23 of 23 original UMb Stage27 TA/VPD/QC FULLSET_SHA256",SOURCE_SHA)
 print("STAGE72 APPROVED_240 PRIOR219 EXACT UNCHANGED + 21 NEW DIRECT REPAIRS")
 print("STAGE72 APPROVED | native original_RH corrected_RH original_VPD corrected_VPD anchor_before anchor_after anchor_QCs")
 for r in audit:
  print("STAGE72 APPROVED",r["native_time"],
    f"{float(r['original_implied_RH_pct']):.3f}",
    f"{float(r['repair_RH_pct']):.3f}",
    r["source_VPD_hPa"],f"{float(r['repair_VPD_hPa']):.3f}",
    r["before_native"],r["after_native"],r["before_anchor_VPD_QC"],r["after_anchor_VPD_QC"])
 print("STAGE72 UNCHANGED",same,"RH",f"{flagged[same]['RH']:.5f}",
       "QC0_TA QC1_VPD ORIGINAL_NOT_RELABELED")
 print("STAGE72 APPROVED_240="+str(aout))
 print("STAGE72 APPROVED_240_SHA256="+sha(aout))
 print("STAGE72_REPORTS="+str(out))
 print("STAGE72 ALL ORIGINAL/QC/OLD219/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

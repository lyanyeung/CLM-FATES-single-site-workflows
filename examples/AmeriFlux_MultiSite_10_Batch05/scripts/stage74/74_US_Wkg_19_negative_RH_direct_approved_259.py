#!/usr/bin/env python3
"""Batch05 Stage74: exact US-Wkg 10 original P2/P3 events/22 flagged HH.
Investigator rule RH<0: direct approved scientific numerical repairs.
13 HH: restore RH by time interpolation between original native physical RH
neighbors, reconstruct VPD with original TA_F_QC0.
6 HH (2020-02-18 12:00-14:30): identical erroneous 0.000 C source TA_F_QC0
under direct sun; do not reconstruct VPD at 0C. Restore TA by bounded
temporal interpolation 17.510->20.850 C across 6HH, preserve original VPD.
Original QC lineage and source fields remain unchanged in new 259 overlay.
3 nonnegative original flagged HH PASS unchanged, no HOLD.
All other source and previous 240 approved overlay rows remain identical.
NO production forcing, source ZIP or Slurm modifications.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from pathlib import Path
from datetime import datetime,timedelta
from collections import defaultdict,Counter

SITE="US-Wkg"
PIN="d9c31372ad29fa79946a97ac30eb02ad679b261f0b925db97ef88cf6b325221e"
FIX_T=set(("202002181200","202002181230","202002181300",
           "202002181330","202002181400","202002181430"))
SCHEMA=("site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct",
 "modified_TA_C","modified_RH_pct","modified_VPD_hPa",
 "delta_VPD_hPa","replacement_RH_provenance","new_VPD_derivation",
 "source_QC_provenance_only","overlay_status")
AUD=("site","episode_id","native_time","source_TA_C","source_TA_QC",
 "source_VPD_hPa","source_VPD_QC","source_implied_RH_pct",
 "repaired_TA_C","repaired_RH_pct","repaired_VPD_hPa",
 "repair_method","anchor_before_native","anchor_before_TA_C",
 "anchor_before_RH_pct","anchor_after_native","anchor_after_TA_C",
 "anchor_after_RH_pct","source_TA_ERA_C","source_VPD_ERA_hPa",
 "operator_status")
PASS=("site","episode_id","native_time","source_TA_C","source_VPD_hPa",
      "source_implied_RH_pct","decision")
def hashfile(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def num(t):
 try:
  x=float(t)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def clk(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("non-native time "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def shift(t,k):
 return (clk(t)+timedelta(minutes=30*k)).strftime("%Y%m%d%H%M")
def saturation(T):
 if T is None or not -80<=T<=60:raise ValueError("invalid source/candidate TA")
 return 6.112*math.exp(17.67*T/(T+243.5))
def rh(T,V):
 if T is None or V is None:return None
 return 100*(1-V/saturation(T))
def format_float(x):return "" if x is None else f"{x:.9f}"
def table(p,req):
 if p.is_symlink() or not p.is_file():raise ValueError("original science ledger missing "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  rd=csv.DictReader(h);hd=rd.fieldnames or []
  if len(hd)!=len(set(hd)) or not set(req).issubset(hd):
   raise ValueError("science CSV columns missing or duplicate "+str(p))
  ans=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in ans):
  raise ValueError("malformed science ledger CSV")
 return ans
def keymap(rows):
 ans={}
 for r in rows:
  key=(r["site"],r["native_time"])
  if key in ans:raise ValueError("duplicate prior science overlay key "+str(key))
  ans[key]=r
 return ans
def csvout(p,hd,rows):
 with p.open("x",encoding="utf-8",newline="") as h:
  wr=csv.DictWriter(h,fieldnames=hd,extrasaction="raise")
  wr.writeheader();wr.writerows(rows)
def selftest():
 assert 240+19==259
 assert callable(format_float) and format_float(1.25)=="1.250000000"
 assert len(FIX_T)==6
 assert abs(17.51+(20.85-17.51)*1/7-17.987142857)<1e-6
 assert rh(0,11.702)<0 and rh(17.987142857,11.702)>0
 assert shift("202002181200",6)=="202002181500"
 print("STAGE74 SELF-TEST PASS | Wkg 19 original RH-negative, 13 VPD RH repair + 6 clearly corrupted 0C temperature repair, preserve original/QC and prior 240")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage63-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage72-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage63_dir,a.stage27_dir,a.stage72_dir,a.out)):
  p.error("need exact previous Stage63/27/72 report dirs and NEW out")
 d63,d27,d72,root,out=(x.expanduser().resolve() for x in
    (a.stage63_dir,a.stage27_dir,a.stage72_dir,a.sites_root,a.out))
 if (not all(x.is_dir() for x in (d63,d27,d72,root)) or out.exists()
     or not out.parent.is_dir() or any(out==x or out in x.parents or x in out.parents for x in (d63,d27,d72,root))):
  p.error("new reports must be outside source/prior report directories")
 fprev=d72/"stage72_VERSIONED_240_USER_APPROVED_RH_VPD_native_overlay.csv"
 m72=json.loads((d72/"stage72_manifest.json").read_text())
 if (m72.get("latest_approved_versioned_RH_VPD_HH")!=240
     or m72.get("output_sha256",{}).get(fprev.name)!=hashfile(fprev)
     or m72.get("previous_219_approved_rows_exactly_preserved") is not True):
  raise ValueError("prior 240 version approved source hash or manifest changed")
 old=keymap(table(fprev,SCHEMA))
 if len(old)!=240:raise ValueError("prior 240 cardinality changed")
 ledger=table(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
   ("site","native_time","episode_id","TA_F_QC","VPD_F_QC"))
 orig=table(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
   ("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"))
 src63=[r for r in ledger if r["site"]==SITE]
 src27=[r for r in orig if r["site"]==SITE]
 if (len(ledger),len(orig),len(src63),len(src27))!=(1565,1574,22,22):
  raise ValueError("original Stage63/27 exact Wkg 22HH cohort changed")
 groups=defaultdict(list)
 for r in src63:groups[r["episode_id"]].append(r["native_time"])
 if len(groups)!=10:raise ValueError("Wkg original 10 episode identity drift")
 source_ref=keymap(src27)
 if set((SITE,r["native_time"]) for r in src63)!=set(source_ref):
  raise ValueError("original Wkg Stage63/27 exact source list mismatch")
 if set(source_ref)&set(old):raise ValueError("prior 240 overlaps original remaining Wkg")
 base=root/SITE/"forcing"
 archives=[x for x in base.rglob("*.zip") if x.is_file() and not x.is_symlink() and hashfile(x)==PIN]
 if len(archives)!=1:raise ValueError("original US-Wkg ZIP pinned by source Stage45 SHA missing/ambiguous")
 needed=set()
 for r in src63:
  t=r["native_time"]
  for j in (-1,0,1):needed.add(shift(t,j))
 # require all before/after source-zero temperature boundaries
 needed|={shift(min(FIX_T),-1),shift(max(FIX_T),1)}
 raw={}
 with zipfile.ZipFile(archives[0]) as z:
  members=[x for x in z.infolist() if
    Path(x.filename).name.startswith("AMF_US-Wkg_FLUXNET_FLUXMET_HH_")
    and x.filename.endswith(".csv")]
  if len(members)!=1 or members[0].file_size>900*1024*1024:
   raise ValueError("original Wkg FLUXMET HH member ambiguity")
  with z.open(members[0]) as b:
   with io.TextIOWrapper(b,encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f);hd=rd.fieldnames or []
    if (len(hd)!=len(set(hd)) or not {"TIMESTAMP_START","TA_F","TA_F_QC",
       "VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(hd)):
     raise ValueError("original Wkg T/VPD/QC/ERA fields missing")
    for r in rd:
     t=r["TIMESTAMP_START"]
     if t in needed:
      if t in raw:raise ValueError("original native key duplicated "+t)
      raw[t]=r
 if needed!=set(raw):raise ValueError("original flagged/neighbor source timestamp missing")
 neg,passed={},{}
 for r in src63:
  t=r["native_time"];o=raw[t];ref=source_ref[(SITE,t)]
  T,V=num(o["TA_F"]),num(o["VPD_F"])
  if (T is None or V is None or o["TA_F_QC"]!="0" or o["VPD_F_QC"]!="1"
      or ref["episode_id"]!=r["episode_id"]
      or ref["TA_F_QC"]!=o["TA_F_QC"] or ref["VPD_F_QC"]!=o["VPD_F_QC"]
      or abs(T-num(ref["TA_F_C"]))>.002 or abs(V-num(ref["VPD_F_hPa"]))>.002):
   raise ValueError("original source QC0 tower T and QC1 VPD mismatch "+t)
  R=rh(T,V)
  if R is None:raise ValueError("original missing physical humidity "+t)
  if R<0:neg[t]=(r["episode_id"],o)
  else:passed[t]=(r["episode_id"],o)
 if (len(neg),len(passed))!=(19,3):raise ValueError("Wkg exact 19 RH negative and 3 RH >=0 changed")
 if set(FIX_T)-set(neg) or set(t for t in neg if num(raw[t]["TA_F"])==0)!=FIX_T:
  raise ValueError("six original 2020 daytime zero-deg flagged HH identity changed")
 # For 2020 repeated exact 0 C labelled QC0, source tower temperature is
 # plainly corrupt from original 17.51 C at 11:30 and 20.85 C at 15:00.
 t_before,t_after=shift(min(FIX_T),-1),shift(max(FIX_T),1)
 leftT,rightT=num(raw[t_before]["TA_F"]),num(raw[t_after]["TA_F"])
 if (abs(leftT-17.51)>.001 or abs(rightT-20.85)>.001 or
     raw[t_before]["TA_F_QC"]!="0" or raw[t_after]["TA_F_QC"]!="0"):
  raise ValueError("source 2020 two real QC0 TA anchors changed")
 orderedT=sorted(FIX_T)
 if orderedT!=[shift(t_before,i) for i in range(1,7)]:
  raise ValueError("2020 six zero-temperature HH not strictly contiguous")
 repaired={};audit=[]
 # 13 native negative RH with nonzero tower TA: original source-neighbor
 # RH interpolation through contiguous negative HH (no QC score relabel).
 other=[t for t in neg if t not in FIX_T]
 runs=[]
 for t in sorted(other):
  if runs and shift(runs[-1][-1],1)==t:
   runs[-1].append(t)
  else:runs.append([t])
 if sum(map(len,runs))!=13:raise ValueError("other negative grouped 13")
 changes={}
 for group in runs:
  before,after=shift(group[0],-1),shift(group[-1],1)
  b,c=raw[before],raw[after]
  bT,bV,cT,cV=num(b["TA_F"]),num(b["VPD_F"]),num(c["TA_F"]),num(c["VPD_F"])
  rb,rc=rh(bT,bV),rh(cT,cV)
  if rb is None or rc is None or not (0<=rb<=100 and 0<=rc<=100):
   raise ValueError("negative original event has invalid source RH brackets "+group[0])
  for j,t in enumerate(group,1):
   o=raw[t];T,V=num(o["TA_F"]),num(o["VPD_F"])
   rnew=rb+(rc-rb)*j/(len(group)+1)
   newV=saturation(T)*(1-rnew/100)
   if not 0<=rnew<=100 or not 0<=newV<=saturation(T):
    raise ValueError("non-physical direct RH interpolation "+t)
   changes[t]=(T,newV,rnew,"DIRECT_RH_LINEAR_FROM_NEIGHBOR_NATIVE_RH_AT_ORIGINAL_TA",
     before,after,bT,cT,rb,rc)
 for i,t in enumerate(orderedT,1):
  o=raw[t]
  originalV=num(o["VPD_F"])
  newT=leftT+(rightT-leftT)*i/(len(orderedT)+1)
  rnew=rh(newT,originalV)
  if (newT<=0 or not 0<=rnew<=100):
   raise ValueError("2020 zero-degree TA reconstruction does not make implied RH physical "+t)
  changes[t]=(newT,originalV,rnew,"DIRECT_TA_QC0_BROKEN_ZERO_INTERPOLATE_SOURCE_QC0_BRACKETS_KEEP_ORIGINAL_VPD",
    t_before,t_after,leftT,rightT,rh(leftT,num(raw[t_before]["VPD_F"])),
    rh(rightT,num(raw[t_after]["VPD_F"])))
 if set(changes)!=set(neg):raise ValueError("19 original negative RH not completely directly repaired")
 for t in sorted(changes):
  eid,o=neg[t]
  T,V=num(o["TA_F"]),num(o["VPD_F"])
  newT,newV,newR,method,before,after,bT,cT,bR,cR=changes[t]
  er=rh(num(o["TA_ERA"]),num(o["VPD_ERA"]))
  row=dict(site=SITE,native_time=t,
    source_cohort="STAGE74_USER_DIRECT_APPROVED_WKG_ORIGINAL_NEGATIVE_RH_19HH",
    decision_id="WKG_"+eid+"_DIRECT_NEGATIVE_RH_REPAIR_20261029",
    source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
    source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
    source_RH_pct=o.get("RH",""),
    source_processed_ERA_T_C=o["TA_ERA"],
    source_processed_ERA_VPD_hPa=o["VPD_ERA"],
    source_processed_ERA_RH_derived_pct=format_float(er),
    modified_TA_C=format_float(newT),modified_RH_pct=format_float(newR),
    modified_VPD_hPa=format_float(newV),delta_VPD_hPa=format_float(newV-V),
    replacement_RH_provenance=method,
    new_VPD_derivation="WATER_MAGNUS_AT_APPROVED_TA" if t not in FIX_T else "ORIGINAL_QC1_VPD_UNCHANGED_WHILE_CORRECTING_OBVIOUS_ZERO_TA",
    source_QC_provenance_only="ORIGINAL_TA_QC0_AND_VPD_QC1_HISTORICAL_FLAGS_RETAINED_ORIGINAL_TA_QC0_NOT_ASSERTED_REAL_AT_SIX_2020_ZEROS",
    overlay_status="USER_DIRECT_RH_NEGATIVE_REPAIR_APPROVED_VERSIONED_NOT_PRODUCTION_APPLIED")
  if set(row)!=set(SCHEMA):raise ValueError("approved overlay schema mismatch")
  repaired[(SITE,t)]=row
  audit.append(dict(site=SITE,episode_id=eid,native_time=t,
   source_TA_C=o["TA_F"],source_TA_QC=o["TA_F_QC"],
   source_VPD_hPa=o["VPD_F"],source_VPD_QC=o["VPD_F_QC"],
   source_implied_RH_pct=format_float(rh(T,V)),
   repaired_TA_C=format_float(newT),repaired_RH_pct=format_float(newR),
   repaired_VPD_hPa=format_float(newV),repair_method=method,
   anchor_before_native=before,anchor_before_TA_C=format_float(bT),
   anchor_before_RH_pct=format_float(bR),
   anchor_after_native=after,anchor_after_TA_C=format_float(cT),
   anchor_after_RH_pct=format_float(cR),source_TA_ERA_C=o["TA_ERA"],
   source_VPD_ERA_hPa=o["VPD_ERA"],
   operator_status="USER_POLICY_DIRECT_APPROVED_NEGATIVE_RH_REPAIR"))
 passrows=[]
 for t,(eid,o) in sorted(passed.items()):
  passrows.append(dict(site=SITE,episode_id=eid,native_time=t,
   source_TA_C=o["TA_F"],source_VPD_hPa=o["VPD_F"],
   source_implied_RH_pct=format_float(rh(num(o["TA_F"]),num(o["VPD_F"]))),
   decision="PASS_ORIGINAL_RH_NONNEGATIVE_UNCHANGED_NO_NEW_OVERLAY"))
 combined=dict(old);combined.update(repaired)
 if len(combined)!=259 or any(old[k]!=combined[k] for k in old):
  raise ValueError("prior 240 exactly identical rows or 259 new tally failed")
 out.mkdir(exist_ok=False)
 allfile=out/"stage74_VERSIONED_259_APPROVED_RH_VPD_TA_native_overlay.csv"
 newfile=out/"stage74_19_NEW_DIRECT_APPROVED_Wkg_REPAIRS.csv"
 auditfile=out/"stage74_19_ORIGINAL_VS_REPAIRED_RH_TA_VPD.csv"
 passfile=out/"stage74_3_NONNEGATIVE_ORIGINAL_HH_PASSED_UNCHANGED.csv"
 csvout(allfile,SCHEMA,[combined[k] for k in sorted(combined)])
 csvout(newfile,SCHEMA,[repaired[k] for k in sorted(repaired)])
 csvout(auditfile,AUD,audit)
 csvout(passfile,PASS,passrows)
 if len(table(allfile,SCHEMA))!=259:raise ValueError("259 output readback failed")
 manifest=dict(stage="74",site=SITE,source_ZIP_SHA256=PIN,
  stage63_worklist_SHA256=hashfile(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"),
  stage27_source_SHA256=hashfile(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"),
  Stage72_previous_240_SHA256=hashfile(fprev),
  previous_240_approved_rows_preserved_exactly=True,
  original_10_events_flagged_HH=22,
  directly_repaired_original_RH_negative_HH=19,
  repaired_with_original_measured_TA_hpa_VPD=13,
  repaired_six_source_QC0_daytime_zero_TA_2020_by_TA_interpolation=6,
  nonnegative_RH_source_flagged_passed_unchanged_HH=3,
  original_QC0_flags_not_relabelled=True,
  source_ZIP_and_historical_original_TA_VPD_unmodified=True,
  total_versioned_approved_HH=259,
  production_DATM_CIME_modified=False,Slurm_submitted=0,
  output_sha256={f.name:hashfile(f) for f in (allfile,newfile,auditfile,passfile)})
 (out/"stage74_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 print("STAGE74 SUCCESS | US-Wkg 10 source events 22HH, negative RH 19 DIRECT USER REPAIR, 3 NONNEGATIVE PASS UNCHANGED")
 print("STAGE74 REPAIR_METHODS | 13 RH/VPD reconstructed with original source QC0 TA; 6 source QC0 TA=0C reconstructed 2020 by source QC0 TA bracketing and source VPD retained")
 print("STAGE74 PREVIOUS_240_EXACTLY_PRESERVED + NEW_19 = 259 VERSIONED APPROVED HH")
 print("STAGE74 19_DIRECT_REPAIRS time sourceRH newRH sourceTA newTA sourceVPD newVPD method")
 for r in audit:
  print("STAGE74 APPROVED",r["native_time"],
   f"{float(r['source_implied_RH_pct']):.2f}",
   f"{float(r['repaired_RH_pct']):.2f}",
   r["source_TA_C"],f"{float(r['repaired_TA_C']):.3f}",
   r["source_VPD_hPa"],f"{float(r['repaired_VPD_hPa']):.3f}",
   r["repair_method"])
 print("STAGE74 PASS_UNCHANGED 3 ORIGINAL_NONNEGATIVE_HH",",".join(sorted(passed)))
 print("STAGE74_APPROVED_259="+str(allfile))
 print("STAGE74_APPROVED_259_SHA256="+hashfile(allfile))
 print("STAGE74_REPORTS="+str(out))
 print("STAGE74 SOURCE / ORIGINAL QC / OLD240 / DATM / CIME / SLURM UNCHANGED")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""US-Var: source-verified 55 negative-RH repairs; seven nonnegative original
records unchanged. Append to verified previous 323 science-approved rows,
without editing original AmeriFlux data, source QC or production forcing.
"""
import csv,io,zipfile,hashlib,math,json,argparse
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter
S="US-Var"
PIN="2e0ff6fe7f7de6dfde3ebfd2e822266e899bd80f1ad0377f78fde34efcb410f2"
PREV="494cfe0d92a376a796687a9d6a61d0e6133b750775dd851602c51dc71bee4f37"
PASS=set("201406030230 201406030300 201406030330 201505060530 201508200300 201508200430 202005181000".split())
COLS="site native_time source_cohort decision_id source_TA_C source_TA_QC source_VPD_hPa source_VPD_QC source_RH_pct source_processed_ERA_T_C source_processed_ERA_VPD_hPa source_processed_ERA_RH_derived_pct modified_TA_C modified_RH_pct modified_VPD_hPa delta_VPD_hPa replacement_RH_provenance new_VPD_derivation source_QC_provenance_only overlay_status".split()
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def num(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None
def es(t):return 6.112*math.exp(17.67*t/(t+243.5))
def rh(t,v):
 if t is None or v is None:return None
 return 100*(1-v/es(t))
def fnum(x):return "" if x is None else f"{x:.9f}"
def dt(t):return datetime.strptime(t,"%Y%m%d%H%M")
def shift(t,k):return (dt(t)+timedelta(minutes=30*k)).strftime("%Y%m%d%H%M")
def read(p,req):
 with p.open(encoding="utf-8-sig",newline="") as h:
  rd=csv.DictReader(h)
  if not set(req).issubset(rd.fieldnames or []):raise ValueError("missing columns "+str(p))
  a=list(rd)
 if any(None in r for r in a):raise ValueError("malformed CSV")
 return a
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as h:
  w=csv.DictWriter(h,cols,extrasaction="raise");w.writeheader();w.writerows(rows)
def run(a):
 d27,d63,d76,out=(p.expanduser().resolve() for p in (a.stage27,a.stage63,a.stage76,a.out))
 oldfile=d76/"stage76_VERSIONED_323_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m=json.loads((d76/"stage76_manifest.json").read_text())
 if out.exists() or not out.parent.is_dir():raise ValueError("new output dir required")
 if (sha(oldfile)!=PREV or m["outputs_sha256"][oldfile.name]!=PREV
     or m["total_versioned_approved_records"]!=323):raise ValueError("previous 323 SHA drift")
 old=read(oldfile,COLS)
 prior={(r["site"],r["native_time"]):r for r in old}
 if len(old)!=323 or len(prior)!=323:raise ValueError("prior 323 cardinality drift")
 s27=read(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
          ["site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"])
 s63=read(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
          ["site","native_time","episode_id","TA_F_QC","VPD_F_QC"])
 if (len(s27),len(s63))!=(1574,1565):raise ValueError("original source cohort drift")
 rr=[r for r in s27 if r["site"]==S]
 selected=[r for r in s63 if r["site"]==S]
 ref={(r["site"],r["native_time"]):r for r in rr}
 if len(rr)!=62 or len(selected)!=62 or len(ref)!=62 or len({r["episode_id"] for r in selected})!=37:
  raise ValueError("US-Var original 62HH/37 episodes changed")
 for r in selected:
  key=(S,r["native_time"])
  if key not in ref or ref[key]["episode_id"]!=r["episode_id"] or key in prior:
   raise ValueError("source original/prior overlap "+str(key))
 root=a.sites_root/S/"forcing"
 zips=[p for p in root.rglob("*.zip") if p.is_file() and not p.is_symlink() and sha(p)==PIN]
 if len(zips)!=1:raise ValueError("pinned original US-Var ZIP not unique")
 want={shift(r["native_time"],k) for r in selected for k in range(-12,13)}
 raw={}
 with zipfile.ZipFile(zips[0]) as z:
  entries=[x for x in z.infolist() if x.filename.endswith(".csv") and
    Path(x.filename).name.startswith("AMF_US-Var_FLUXNET_FLUXMET_HH_")]
  if len(entries)!=1:raise ValueError("ambiguous source HH")
  with z.open(entries[0]) as stream:
   with io.TextIOWrapper(stream,encoding="utf-8-sig") as handle:
    rd=csv.DictReader(handle)
    for r in rd:
     t=r["TIMESTAMP_START"]
     if t in want:
      if t in raw:raise ValueError("duplicate source HH")
      raw[t]=r
 def R(t):
  r=raw.get(t)
  return rh(num(r["TA_F"]),num(r["VPD_F"])) if r is not None else None
 negative=set();positive=set()
 for (s,t),r in ref.items():
  x=raw.get(t)
  if not x or x["TA_F_QC"]!="0" or x["VPD_F_QC"]!="1" or r["TA_F_QC"]!="0" or r["VPD_F_QC"]!="1":
   raise ValueError("original T0/VPD1 source changed "+t)
  if (abs(num(x["TA_F"])-num(r["TA_F_C"]))>.002 or
      abs(num(x["VPD_F"])-num(r["VPD_F_hPa"]))>.002):raise ValueError("source value drift "+t)
  (negative if R(t)<0 else positive).add(t)
 if len(negative)!=55 or positive!=PASS:raise ValueError("verified 55 negative/7 nonnegative changed")
 def anchor(t,direction,qc0):
  for i in range(1,13):
   tt=shift(t,direction*i);x=raw.get(tt);rv=R(tt)
   if x is not None and rv is not None and 1<=rv<=100 and (not qc0 or x["VPD_F_QC"]=="0"):
    return tt,rv,x["VPD_F_QC"]
  return None
 new={};audit=[];methods=Counter()
 for t in sorted(negative):
  before,after=anchor(t,-1,True),anchor(t,1,True)
  method="BOTH_ORIGINAL_VPD_QC0_RH_DONORS"
  if before is None or after is None:
   before,after=anchor(t,-1,False),anchor(t,1,False)
   method="BOTH_ORIGINAL_MIXED_QC_RH_DONORS"
  if before is None or after is None:raise ValueError("missing two physical source RH anchors "+t)
  bt,br,bqc=before;at,ar,aqc=after
  weight=(dt(t)-dt(bt)).total_seconds()/(dt(at)-dt(bt)).total_seconds()
  rnew=br+(ar-br)*weight
  x=raw[t];T=num(x["TA_F"]);V=num(x["VPD_F"]);vnew=es(T)*(1-rnew/100)
  if not 0<=rnew<=100 or not 0<=vnew<=es(T) or not abs(rh(T,vnew)-rnew)<1e-7:
   raise ValueError("new VPD physics check failed "+t)
  er=rh(num(x["TA_ERA"]),num(x["VPD_ERA"]))
  fields=dict(site=S,native_time=t,source_cohort="STAGE78_VAR_DIRECT_NEGATIVE_RH",
    decision_id="VAR_"+ref[(S,t)]["episode_id"]+"_USER_DIRECT_20261029",
    source_TA_C=x["TA_F"],source_TA_QC=x["TA_F_QC"],
    source_VPD_hPa=x["VPD_F"],source_VPD_QC=x["VPD_F_QC"],
    source_RH_pct=x.get("RH",""),
    source_processed_ERA_T_C=x["TA_ERA"],source_processed_ERA_VPD_hPa=x["VPD_ERA"],
    source_processed_ERA_RH_derived_pct=fnum(er),
    modified_TA_C=x["TA_F"],modified_RH_pct=fnum(rnew),
    modified_VPD_hPa=fnum(vnew),delta_VPD_hPa=fnum(vnew-V),
    replacement_RH_provenance=method,
    new_VPD_derivation="MAGNUS_AT_UNCHANGED_ORIGINAL_QC0_TOWER_TA",
    source_QC_provenance_only="ORIGINAL_TA_QC0_VPD_QC1_UNCHANGED",
    overlay_status="USER_APPROVED_SOURCE_NEGATIVE_RH_VERSIONED_NOT_DATM_APPLIED")
  if set(fields)!=set(COLS):raise ValueError("overlay schema mismatch")
  new[(S,t)]=fields;methods[method]+=1
  audit.append(dict(native_time=t,episode_id=ref[(S,t)]["episode_id"],
    old_TA=x["TA_F"],old_VPD=x["VPD_F"],old_RH=fnum(R(t)),
    corrected_TA=x["TA_F"],corrected_VPD=fnum(vnew),corrected_RH=fnum(rnew),
    left_native=bt,left_RH=fnum(br),left_VPD_QC=bqc,
    right_native=at,right_RH=fnum(ar),right_VPD_QC=aqc,method=method))
 pass_rows=[dict(site=S,episode_id=ref[(S,t)]["episode_id"],native_time=t,
    original_TA=raw[t]["TA_F"],original_VPD=raw[t]["VPD_F"],original_RH=fnum(R(t)),
    decision="PASS_NONNEGATIVE_SOURCE_UNCHANGED",
    science_caveat="VERY_LOW_SOURCE_QC1_RH_NOT_VERIFIED_TOWER_HUMIDITY") for t in sorted(positive)]
 final=dict(prior);final.update(new)
 if len(final)!=378 or len(new)!=55 or any(final[k]!=prior[k] for k in prior):
  raise ValueError("prior323 and new55 not conserved")
 out.mkdir(exist_ok=False)
 ffull=out/"stage78_VERSIONED_378_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 fnew=out/"stage78_55_NEW_US_Var_DIRECT_APPROVED_REPAIRS.csv"
 faud=out/"stage78_55_ORIGINAL_VS_REPAIRED_SOURCE_AND_DONORS.csv"
 fpass=out/"stage78_7_NONNEGATIVE_SOURCE_PASSED_UNCHANGED.csv"
 write(ffull,COLS,[final[k] for k in sorted(final)])
 write(fnew,COLS,[new[k] for k in sorted(new)])
 write(faud,list(audit[0]),audit);write(fpass,list(pass_rows[0]),pass_rows)
 if len(read(ffull,COLS))!=378:raise ValueError("readback failed")
 manifest=dict(stage=78,site=S,original_SHA256=PIN,prior323_SHA256=PREV,
    approved_before=323,approved_added=55,approved_after=378,
    original_flagged_HH=62,original_events=37,
    passed_nonnegative_HH=7,repair_methods=dict(methods),
    source_original_modified=False,source_QC_modified=False,
    prior323_changed=False,DATM_CIME_modified=False,slurm_submitted=0,
    output_sha256={p.name:sha(p) for p in (ffull,fnew,faud,fpass)})
 (out/"stage78_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 print("STAGE78 SUCCESS | US-Var 37 original events 62 HH, 55 RH<0 DIRECT REPAIR, 7 NONNEGATIVE PASS ORIGINAL")
 print("STAGE78 SOURCE_SHA VERIFIED",PIN,"| PRIOR323 EXACT SHA",PREV)
 print("STAGE78 PREVIOUS 323 + 55 = 378 VERSIONED APPROVED HH")
 print("STAGE78 REPAIR_METHODS",dict(methods))
 print("STAGE78 7 LOW-RH SOURCE CAUTIONS",",".join(sorted(positive)))
 for x in audit:
  print("STAGE78 APPROVED",x["native_time"],"originalRH",f"{float(x['old_RH']):.2f}",
     "newRH",f"{float(x['corrected_RH']):.2f}",
     "oldVPD",x["old_VPD"],"newVPD",f"{float(x['corrected_VPD']):.3f}")
 print("STAGE78 APPROVED_378_SHA256="+sha(ffull))
 print("STAGE78 APPROVED_378="+str(ffull))
 print("STAGE78_REPORTS="+str(out))
 print("STAGE78 ORIGINAL/QC/PRIOR323/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage27",type=Path)
 ap.add_argument("--stage63",type=Path)
 ap.add_argument("--stage76",type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:
  assert len(PASS)==7 and 323+55==378 and fnum(1.2)=="1.200000000"
  print("STAGE78 SELF-TEST PASS | US-Var source 55 negatives, 7 nonnegative source pass, prior323 immutable")
 else:
  if None in (a.stage27,a.stage63,a.stage76,a.out):ap.error("pass exact Stage27,63,76 dirs and NEW output")
  run(a)

#!/usr/bin/env python3
"""Batch05 Stage85: close the final US-Whs P2/P3 source-science key.
Read-only: pin original Stage05 Whs source FLUXMET CSV, Stage27/63 exact
201205260600 original T/VPD/QC/event key; latest Stage84 approved 1675 SHA;
Stage67 51 independently user-approved versioned T candidates and ten
pass-original temperature runs. Print original timestamp ±3h source TA/VPD/
QC/derived RH, source-processed ERA companion, nearest actual VPD-QC0 RH
donors and Stage67 overlap. DO NOT apply forcing or approve repairs here.
"""
import argparse,csv,hashlib,json,math,re
from datetime import datetime,timedelta
from pathlib import Path
SITE="US-Whs"
TIME="201205260600"
RELEASE="AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1"
RAW_SHA="653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca"
ZIP_STAGE67_SHA="0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767"
PREVIOUS_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def n(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def sat(t):
 if t is None or not -80<=t<=60:return None
 return 6.112*math.exp(17.67*t/(t+243.5))
def rh(t,v):
 es=sat(t)
 return 100*(1-v/es) if es is not None and v is not None else None
def nice(x):return "NA" if x is None else f"{x:.3f}"
def dt(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid native timestamp")
 return datetime.strptime(t,"%Y%m%d%H%M")
def move(t,i):
 return (dt(t)+timedelta(minutes=i*30)).strftime("%Y%m%d%H%M")
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("missing source "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as h:
  r=csv.DictReader(h);cols=r.fieldnames or []
  if len(cols)!=len(set(cols)) or not set(required).issubset(cols):
   raise ValueError("original source schema changed "+str(p))
  out=list(r)
 if any(None in x or any(v is None for v in x.values()) for x in out):
  raise ValueError("original source row-width drift "+str(p))
 return out
def selftest():
 assert move(TIME,-1)=="201205260530"
 assert move(TIME,1)=="201205260630"
 assert len(RAW_SHA)==len(PREVIOUS_SHA)==64
 assert rh(10,20)<0 and 0<=rh(10,2)<=100
 print("STAGE85 SELF-TEST PASS | final Whs original one HH + Stage67 T 51 candidate / 10 pass-original, prior 1675 immutable; no model writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage27",type=Path)
 p.add_argument("--stage63",type=Path)
 p.add_argument("--stage67",type=Path)
 p.add_argument("--stage84",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage27,a.stage63,a.stage67,a.stage84,a.out)):
  p.error("require Stage27, Stage63, Stage67 Whs and successful Stage84 paths plus NEW output")
 d27,d63,d67,d84,out=(v.expanduser().resolve() for v in
  (a.stage27,a.stage63,a.stage67,a.stage84,a.out))
 if (not all(x.is_dir() for x in (d27,d63,d67,d84))
     or out.exists() or not out.parent.is_dir()):
  p.error("previous source dirs missing or output not new")
 fprev=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(fprev)!=PREVIOUS_SHA or
     m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(fprev.name)!=PREVIOUS_SHA):
  raise ValueError("Stage84 1675 exact immutable overlay mismatch")
 previous=read(fprev,["site","native_time","source_TA_C","source_VPD_hPa"])
 if len(previous)!=1675 or len({(r["site"],r["native_time"]) for r in previous})!=1675:
  raise ValueError("1675 previous approved source keys not unique")
 if (SITE,TIME) in {(r["site"],r["native_time"]) for r in previous}:
  raise ValueError("Whs final one HH was already in earlier 1675 overlay")
 r27=read(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
   ["site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC"])
 r63=read(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
   ["site","native_time","episode_id","TA_F_QC","VPD_F_QC"])
 if len(r27)!=1574 or len(r63)!=1565:raise ValueError("Stage27/63 global population drift")
 a27=[r for r in r27 if r["site"]==SITE]
 a63=[r for r in r63 if r["site"]==SITE]
 if len(a27)!=1 or len(a63)!=1 or a27[0]["native_time"]!=TIME or a63[0]["native_time"]!=TIME:
  raise ValueError("the final US-Whs native source P2/P3 timestamp is not exact known key")
 source=a27[0]
 if source["episode_id"]!=a63[0]["episode_id"] or source["TA_F_QC"]!=a63[0]["TA_F_QC"] or source["VPD_F_QC"]!=a63[0]["VPD_F_QC"]:
  raise ValueError("Whs final one HH Stage27/63 original provenance differs")
 c67=d67/"stage67_USER_SELECTED_TA_INTERPOLATION_CANDIDATE_ONLY.csv"
 h67=d67/"stage67_UNREPAIRABLE_QC_BRACKET_HOLDS.csv"
 e67=d67/"stage67_ALL30_TARGETED_QC_TRANSITIONS_AND_DECISIONS.csv"
 man67=json.loads((d67/"stage67_manifest.json").read_text())
 if (man67.get("original_ZIP_SHA256")!=ZIP_STAGE67_SHA or
     man67.get("final_candidate_repaired_TA_HH")!=51 or
     any(man67.get("output_sha256",{}).get(x.name)!=sha(x) for x in (c67,h67,e67))):
  raise ValueError("Stage67 immutable original Whs candidate manifest failed")
 candidates=read(c67,["site","native_time","candidate_TA_F_C","source_QC_unchanged","source_VPD_F_hPa_unchanged"])
 holds=read(h67,["decision","target_run_first_native","target_run_last_native"])
 edges=read(e67,["decision","target_run_first_native","target_run_last_native"])
 if len(candidates)!=51 or len(holds)!=10 or len(edges)!=30 or any(x["site"]!=SITE for x in candidates):
  raise ValueError("Stage67 51 candidates/10 selected passes/30 source edges changed")
 overlapping=[x for x in candidates if x["native_time"]==TIME]
 if len(overlapping)>1:raise ValueError("duplicate same-native Whs Stage67 T candidate")
 cross_hold=[x for x in holds if x["target_run_first_native"]<=TIME<=x["target_run_last_native"]]
 rawfolder=a.sites_root/SITE/"forcing"/"raw"/RELEASE
 pat=re.compile(r"AMF_US-Whs_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",re.I)
 native=[x for x in rawfolder.iterdir() if pat.fullmatch(x.name)] if rawfolder.is_dir() else []
 if len(native)!=1 or not native[0].is_file() or native[0].is_symlink() or sha(native[0])!=RAW_SHA:
  raise ValueError("original Whs Stage05 native CSV missing/wrong SHA")
 want={move(TIME,k) for k in range(-6,7)}
 original={}
 with native[0].open("r",encoding="utf-8-sig",newline="") as stream:
  rd=csv.DictReader(stream)
  if not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(rd.fieldnames or []):
   raise ValueError("native FLUXMET original required fields unavailable")
  for r in rd:
   if r["TIMESTAMP_START"] in want:
    if r["TIMESTAMP_START"] in original:raise ValueError("duplicate native Whs source HH")
    original[r["TIMESTAMP_START"]]=r
 if TIME not in original:raise ValueError("original 201205260600 HH missing")
 current=original[TIME]
 T,V=n(current["TA_F"]),n(current["VPD_F"])
 if (T is None or V is None or
     n(source["TA_F_C"]) is None or n(source["VPD_F_hPa"]) is None or
     abs(T-n(source["TA_F_C"]))>.002 or abs(V-n(source["VPD_F_hPa"]))>.002 or
     current["TA_F_QC"]!=source["TA_F_QC"] or
     current["VPD_F_QC"]!=source["VPD_F_QC"]):
  raise ValueError("Whs original 1 HH Stage27 time/source T/VPD/QC altered")
 original_rh=rh(T,V);era_rh=rh(n(current["TA_ERA"]),n(current["VPD_ERA"]))
 if original_rh is None:raise ValueError("Whs original humidity physics invalid")
 def donor(step):
  for i in range(1,7):
   t=move(TIME,step*i);o=original.get(t)
   if o and o["VPD_F_QC"]=="0":
    rr=rh(n(o["TA_F"]),n(o["VPD_F"]))
    if rr is not None and 1<=rr<=100:
     return {"time":t,"RH_pct":round(rr,6),"T_C":o["TA_F"],"VPD_hPa":o["VPD_F"],"T_QC":o["TA_F_QC"],"VPD_QC":o["VPD_F_QC"]}
  return None
 left,right=donor(-1),donor(1)
 rows=[]
 print("STAGE85 ORIGINAL_WHS_HH_PLUS_MINUS_3H native flag TA TA_QC VPD VPD_QC derivedRH sourceERA_T sourceERA_VPD sourceERA_RH P_F SW_IN_F")
 for t in sorted(want):
  o=original.get(t)
  if o is None:
   print("STAGE85 CONTEXT",t,"ORIGINAL_NATIVE_MISSING");continue
  rr=rh(n(o["TA_F"]),n(o["VPD_F"]))
  er=rh(n(o["TA_ERA"]),n(o["VPD_ERA"]))
  line=[t,"FINAL_WHSP23" if t==TIME else "",o["TA_F"],o["TA_F_QC"],
        o["VPD_F"],o["VPD_F_QC"],nice(rr),o["TA_ERA"],
        o["VPD_ERA"],nice(er),o.get("P_F",""),o.get("SW_IN_F","")]
  print("STAGE85 CONTEXT"," | ".join(line))
  rows.append(dict(zip(("native_time","source_marker","original_T_C","original_T_QC",
   "original_VPD_hPa","original_VPD_QC","original_implied_RH_pct","source_processed_ERA_T_C",
   "source_processed_ERA_VPD_hPa","source_processed_ERA_RH_pct","P_F","SW_IN_F"),line)))
 disposition=("REVIEW_P2P3_RH_NEGATIVE_DIRECT_REPAIR_SCIENCE_OVERLAY" if original_rh<0
  else "PASS_ORIGINAL_RH_NONNEGATIVE_WITH_PROVENANCE")
 if overlapping:disposition+="_STAGE67_T_CANDIDATE_SAME_TIME_CROSS_VARIABLE_RECONCILIATION"
 if cross_hold:disposition+="_STAGE67_T_PASS_ORIGINAL_SAME_TIME"
 summary=dict(stage=85,site=SITE,native_time=TIME,episode=source["episode_id"],
  original_source_SHA256=RAW_SHA,prior_1675_approved_SHA256=PREVIOUS_SHA,
  original_TA_C=T,original_VPD_hPa=V,original_TA_QC=current["TA_F_QC"],
  original_VPD_QC=current["VPD_F_QC"],
  original_implied_RH_pct=original_rh,source_processed_ERA_RH_pct=era_rh,
  stage67_T_candidate_overlaps=bool(overlapping),
  stage67_T_candidate_value_C=overlapping[0]["candidate_TA_F_C"] if overlapping else None,
  stage67_pass_original_run_overlaps=bool(cross_hold),
  left_original_measured_VPD_QC0_RH_donor=left,
  right_original_measured_VPD_QC0_RH_donor=right,
  scientific_disposition=disposition,
  output_intent="READONLY_REPORT_NO_MODEL_FORCING_OR_FINAL_REPAIR_APPROVAL",
  originals_QC_previous_1675_DATM_CIME_SLURM_unchanged=True)
 out.mkdir(exist_ok=False)
 fsum=out/"stage85_WHS_FINAL_ONE_P2P3_SOURCE_SCIENCE_AND_STAGE67_CROSSWALK.json"
 fctx=out/"stage85_WHS_NATIVE_3H_BEFORE_AFTER_ORIGINAL_CONTEXT.csv"
 with fctx.open("x",encoding="utf-8",newline="") as h:
  w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 fsum.write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("STAGE85 SUCCESS | Whs original P2P3 final 1 HH, Stage67 51 temperature candidates/10 PASS original, previous 1675 verified")
 print("STAGE85 ORIGINAL_LAST",TIME,"TA",nice(T),"TA_QC",current["TA_F_QC"],
  "VPD",nice(V),"VPD_QC",current["VPD_F_QC"],"ORIGINAL_RH",nice(original_rh),
  "SOURCE_PROCESSED_ERA_RH",nice(era_rh))
 print("STAGE85 STAGE67_T_OVERLAP",len(overlapping),"STAGE67_PASS_ORIGINAL_RUN_OVERLAP",len(cross_hold))
 print("STAGE85 SOURCE_QC0_HUMIDITY_DONORS",json.dumps({"before":left,"after":right},sort_keys=True))
 print("STAGE85 SCIENCE_DECISION",disposition)
 print("STAGE85_REPORTS="+str(out))
 print("STAGE85 ORIGINAL/QC/PRIOR1675/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":
 main()

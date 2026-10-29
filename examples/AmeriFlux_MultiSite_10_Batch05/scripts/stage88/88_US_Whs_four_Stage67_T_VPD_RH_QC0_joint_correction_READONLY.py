#!/usr/bin/env python3
"""Batch05 Stage88: reconcile FOUR original Stage67 Whs QC1 T candidate RH<0.
Produce separate versioned four-HH joint T/RH/VPD numerical science overlay,
NOT a mutation of the approved Stage67 51 T or Stage84 1675 RH/VPD records
and NOT a model forcing release. Both immediate original T/VPD QC0 source
humidity donors must exist and be physically valid, and two independently
computed methods (native QC0 RH interpolated at approved T; direct QC0 VPD
interpolated) must agree within 0.05 hPa. Fail closed otherwise.
"""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from collections import Counter
from datetime import datetime,timedelta

SITE="US-Whs"
ORIG_SHA="653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca"
APPROVED_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
FOUR=("200910290430","200910300200","200910301100","201303081100")
RELEASE="AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1"
FIELDS=("site","native_time","stage67_T_candidate_original_run_id",
 "original_T_C","original_T_QC","source_original_VPD_hPa","source_original_VPD_QC",
 "approved_stage67_T_C","original_source_implied_RH_pct",
 "reconstructed_RH_pct","reconstructed_VPD_hPa",
 "direct_two_QC0_source_VPD_interpolation_hPa",
 "difference_thermodynamic_vs_direct_VPD_hPa",
 "left_original_QC0_time","left_original_QC0_T_C",
 "left_original_QC0_VPD_hPa","left_original_QC0_RH_pct",
 "right_original_QC0_time","right_original_QC0_T_C",
 "right_original_QC0_VPD_hPa","right_original_QC0_RH_pct",
 "original_source_processed_ERA_RH_pct",
 "science_method","science_status",
 "source_QC_labels_unchanged","production_DATM_permission")
SUMMARY_FIELDS=("site","native_time","accepted_stage67_T_C",
 "original_QC1_VPD_hPa","candidate_T_original_VPD_RH_pct",
 "final_versioned_VPD_hPa","final_versioned_RH_pct",
 "cross_variable_scope","research_science_status")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
def n(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def es(t):
 return None if t is None or not -80<=t<=60 else 6.112*math.exp(17.67*t/(t+243.5))
def rh(t,v):
 e=es(t)
 return None if e is None or v is None else 100*(1-v/e)
def f(x):return "" if x is None else f"{x:.9f}"
def dt(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid native source time "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def shift(t,i):
 return (dt(t)+timedelta(minutes=i*30)).strftime("%Y%m%d%H%M")
def read(p,req):
 if not p.is_file() or p.is_symlink():raise ValueError("missing original science input "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  reader=csv.DictReader(h);columns=reader.fieldnames or []
  if len(columns)!=len(set(columns)) or not set(req).issubset(columns):
   raise ValueError("input CSV column schema changed "+str(p))
  rows=list(reader)
 if any(None in row or any(v is None for v in row.values()) for row in rows):
  raise ValueError("malformed original science input "+str(p))
 return rows
def key(rows):
 d={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in d:raise ValueError("duplicate original source/native key "+str(k))
  d[k]=r
 return d
def write(p,headers,rows):
 with p.open("x",encoding="utf-8",newline="") as stream:
  w=csv.DictWriter(stream,fieldnames=headers,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert len(FOUR)==4 and len(set(FOUR))==4
 assert shift(FOUR[0],-1)=="200910290400"
 assert shift(FOUR[2],1)=="200910301130"
 assert abs(rh(0,6.112))<1e-9 and rh(0,8)<0
 for t,T,b,a in (("200910290430",-1.3455,52.517632611,51.248940710),
                 ("200910300200",-0.4015,48.990918755,51.284851532),
                 ("200910301100",9.545,20.840124044,17.538099371),
                 ("201303081100",11.425,59.163735287,62.394532708)):
  V=es(T)*(1-(a+b)/200)
  assert V is not None and 0<=rh(T,V)<=100
 assert n("2.5")==2.5 and n("-9999") is None
 print("STAGE88 SELF-TEST PASS | 4 exact Stage87 Whs T/VPD RH failures; two immediate original QC0 RH donors, dual VPD sanity checks, no forcing writes")

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--self-test",action="store_true")
 for x in ("stage67","stage84","stage86","stage87"):
  parser.add_argument("--"+x,type=Path)
 parser.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 parser.add_argument("--out",type=Path)
 o=parser.parse_args()
 if o.self_test:selftest();return
 if any(getattr(o,x) is None for x in ("stage67","stage84","stage86","stage87","out")):
  parser.error("Stage67/84/86/87 actual report dirs and fresh output required")
 d67,d84,d86,d87,out=(getattr(o,x).expanduser().resolve() for x in
                       ("stage67","stage84","stage86","stage87","out"))
 source_root=o.sites_root.expanduser().resolve()/SITE/"forcing"/"raw"/RELEASE
 if not all(x.is_dir() for x in (d67,d84,d86,d87,source_root)) or out.exists() or not out.parent.is_dir():
  parser.error("source/reports missing or output existing")
 if any(out==x or out in x.parents or x in out.parents for x in
        (d67,d84,d86,d87,source_root)):
  parser.error("output intersects a protected report/source directory")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(f84)!=APPROVED_SHA or m84.get("total_versioned_approved_repair_rows")!=1675
     or m84.get("output_SHA256",{}).get(f84.name)!=APPROVED_SHA):
  raise ValueError("Stage84 original approved overlay SHA drift")
 prev=key(read(f84,["site","native_time"]))
 if len(prev)!=1675 or any((SITE,t) in prev for t in FOUR):
  raise ValueError("the four new Whs times overlap approved 1675 research overlay")
 f67=d67/"stage67_USER_SELECTED_TA_INTERPOLATION_CANDIDATE_ONLY.csv"
 h67=d67/"stage67_UNREPAIRABLE_QC_BRACKET_HOLDS.csv"
 e67=d67/"stage67_ALL30_TARGETED_QC_TRANSITIONS_AND_DECISIONS.csv"
 m67=json.loads((d67/"stage67_manifest.json").read_text())
 if (m67.get("final_candidate_repaired_TA_HH")!=51 or
     any(m67.get("output_sha256",{}).get(p.name)!=sha(p) for p in (f67,h67,e67))):
  raise ValueError("Stage67 51 T candidate SHA/manifest changed")
 cands=key(read(f67,["site","native_time","candidate_TA_F_C",
                     "original_source_TA_F_C","source_VPD_F_hPa_unchanged",
                     "source_VPD_F_QC_unchanged","source_QC_unchanged","source_run_id"]))
 if len(cands)!=51 or not all((SITE,t) in cands for t in FOUR):
  raise ValueError("Stage67 candidate set no longer includes exact four")
 m86=json.loads((d86/"stage86_FINAL_TEN_SITE_RESEARCH_QC_RELEASE_GATES.json").read_text())
 if (m86.get("stage67_T_candidate_original_VPD_physics_issues")!=4
     or m86.get("current_overlay_SHA256")!=APPROVED_SHA
     or m86.get("Stage67_T_candidate_overlapping_main_overlay_HH")!=0):
  raise ValueError("Stage86 four original Whs physics issue result drifted")
 m87=json.loads((d87/"stage87_manifest.json").read_text())
 f_all=d87/"stage87_ALL51_WHS_STAGE67_CANDIDATE_T_ORIGINAL_VPD_PHYSICS.csv"
 f_bad=d87/"stage87_FOUR_WHS_NONPHYSICAL_T_PLUS_VPD_LOCAL_EXCEPTIONS.csv"
 f_ctx=d87/"stage87_FOUR_WHS_3H_NATIVE_ORIGINAL_CONTEXT.csv"
 if (m87.get("stage67_candidates_verified")!=51 or
     m87.get("stage67_original_vpd_nonphysical")!=4 or
     m87.get("exact_same_four_as_stage86") is not True or
     m87.get("latest_1675_overlay_SHA256")!=APPROVED_SHA or
     m87.get("original_Whs_FLUXMET_CSV_SHA256")!=ORIG_SHA or
     any(m87.get("output_SHA256",{}).get(p.name)!=sha(p) for p in (f_all,f_bad,f_ctx))):
  raise ValueError("Stage87 original four science exception source SHA/manifest mismatch")
 all51=key(read(f_all,["site","native_time","source_run_id","original_T_C",
    "source_T_QC","candidate_T_C","original_VPD_hPa","source_VPD_QC",
    "candidate_T_with_original_VPD_RH_pct","candidate_implied_RH_nonphysical"]))
 bad=key(read(f_bad,["site","native_time","candidate_T_C","original_VPD_hPa",
    "candidate_T_with_original_VPD_RH_pct"]))
 ctx=read(f_ctx,["flagged_center_native","native_time","original_T_C",
   "TA_F_QC","original_VPD_hPa","VPD_F_QC","original_RH_pct",
   "original_measured_VPD_QC0_RH_physical"])
 if (len(all51)!=51 or len(bad)!=4 or {k[1] for k in bad}!=set(FOUR) or
     len(ctx)!=52 or {x["flagged_center_native"] for x in ctx}!=set(FOUR)):
  raise ValueError("Stage87 exact 4×13 original contexts or 51 candidates differ")
 if any((SITE,t) not in all51 for t in FOUR) or any(
     {x["site"] for x in all51.values()}!={SITE} for _ in (0,)):
  raise ValueError("Stage87 51 original candidate site keys differ")
 for t in FOUR:
  x=bad[(SITE,t)]
  if x["candidate_T_with_original_VPD_RH_pct"]=="" or n(x["candidate_T_with_original_VPD_RH_pct"])>=0:
   raise ValueError("four original 2019/2013 nonphysical candidate RH no longer negative "+t)
 rawfiles=[x for x in source_root.iterdir() if x.is_file() and not x.is_symlink() and
   re.fullmatch(r"AMF_US-Whs_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",x.name,re.I)]
 if len(rawfiles)!=1 or sha(rawfiles[0])!=ORIG_SHA:
  raise ValueError("original native Whs Stage05 CSV provenance SHA changed")
 original={}
 want={t for t in FOUR}
 for t in FOUR:want|={shift(t,-1),shift(t,1)}
 with rawfiles[0].open("r",encoding="utf-8-sig",newline="") as src:
  rd=csv.DictReader(src)
  if not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"}.issubset(rd.fieldnames or []):
   raise ValueError("source WHS original native source columns absent")
  for r in rd:
   if r["TIMESTAMP_START"] in want:
    if r["TIMESTAMP_START"] in original:raise ValueError("duplicated source HH")
    original[r["TIMESTAMP_START"]]=r
 if set(original)!=want:raise ValueError("missing original center or immediate QC0 anchor source HH")
 context={(r["flagged_center_native"],r["native_time"]):r for r in ctx}
 if len(context)!=len(ctx):raise ValueError("duplicated Stage87 native context")
 four=[];summary=[]
 for t in FOUR:
  keyt=(SITE,t);r=original[t];p=cands[keyt];e=all51[keyt]
  T,V=n(r["TA_F"]),n(r["VPD_F"])
  candidateT=n(p["candidate_TA_F_C"])
  if (T is None or V is None or candidateT is None or
      abs(T-n(p["original_source_TA_F_C"]))>0.002 or
      abs(V-n(p["source_VPD_F_hPa_unchanged"]))>0.002 or
      abs(candidateT-n(e["candidate_T_C"]))>0.002 or
      abs(V-n(e["original_VPD_hPa"]))>0.002 or
      r["TA_F_QC"]!="1" or r["VPD_F_QC"]!="1" or
      p["source_QC_unchanged"]!="1" or p["source_VPD_F_QC_unchanged"]!="1"):
   raise ValueError("original Whs T,VPD,QC vs Stage67/87 source mismatch "+t)
  before=shift(t,-1);after=shift(t,1)
  b=original[before];a=original[after]
  cb=context.get((t,before));ca=context.get((t,after))
  if cb is None or ca is None:raise ValueError("Stage87 immediate source QC0 context missing "+t)
  rb,ra=rh(n(b["TA_F"]),n(b["VPD_F"])),rh(n(a["TA_F"]),n(a["VPD_F"]))
  if (b["TA_F_QC"]!="0" or a["TA_F_QC"]!="0" or
      b["VPD_F_QC"]!="0" or a["VPD_F_QC"]!="0" or
      cb["original_measured_VPD_QC0_RH_physical"]!="True" or
      ca["original_measured_VPD_QC0_RH_physical"]!="True" or
      rb is None or ra is None or not 1<=rb<=100 or not 1<=ra<=100 or
      abs(rb-n(cb["original_RH_pct"]))>1e-5 or
      abs(ra-n(ca["original_RH_pct"]))>1e-5):
   raise ValueError("original two QC0 observed-source VPD/RH anchors absent or changed "+t)
  w=(dt(t)-dt(before)).total_seconds()/(dt(after)-dt(before)).total_seconds()
  newrh=rb+(ra-rb)*w
  ev=es(candidateT)
  newv=ev*(1-newrh/100)
  linearV=n(b["VPD_F"])+(n(a["VPD_F"])-n(b["VPD_F"]))*w
  difference=newv-linearV
  if (not 0<w<1 or not 0<=newrh<=100 or ev is None or
      not 0<=newv<=ev or abs(rh(candidateT,newv)-newrh)>1e-7 or
      abs(difference)>0.05 or rh(candidateT,V) is None or rh(candidateT,V)>=0):
   raise ValueError("source QC0 dual-method validation FAILED; preserve source until reviewed "+t)
  four.append(dict(site=SITE,native_time=t,stage67_T_candidate_original_run_id=p["source_run_id"],
   original_T_C=r["TA_F"],original_T_QC=r["TA_F_QC"],
   source_original_VPD_hPa=r["VPD_F"],source_original_VPD_QC=r["VPD_F_QC"],
   approved_stage67_T_C=f(candidateT),original_source_implied_RH_pct=f(rh(T,V)),
   reconstructed_RH_pct=f(newrh),reconstructed_VPD_hPa=f(newv),
   direct_two_QC0_source_VPD_interpolation_hPa=f(linearV),
   difference_thermodynamic_vs_direct_VPD_hPa=f(difference),
   left_original_QC0_time=before,left_original_QC0_T_C=b["TA_F"],
   left_original_QC0_VPD_hPa=b["VPD_F"],left_original_QC0_RH_pct=f(rb),
   right_original_QC0_time=after,right_original_QC0_T_C=a["TA_F"],
   right_original_QC0_VPD_hPa=a["VPD_F"],right_original_QC0_RH_pct=f(ra),
   original_source_processed_ERA_RH_pct=e.get("source_ERA_RH_pct",""),
   science_method="IMMEDIATE_TWO_SIDED_ORIGINAL_MEASURED_QC0_RH_LINEAR_AT_APPROVED_STAGE67_QC1_T_WITH_DIRECT_QC0_VPD_CONSISTENCY",
   science_status="STAGE88_SOURCE_ANCHORED_RESEARCH_CANDIDATE_NOT_PRODUCTION_APPROVED",
   source_QC_labels_unchanged="True",production_DATM_permission="NO"))
  summary.append(dict(site=SITE,native_time=t,accepted_stage67_T_C=f(candidateT),
   original_QC1_VPD_hPa=r["VPD_F"],
   candidate_T_original_VPD_RH_pct=e["candidate_T_with_original_VPD_RH_pct"],
   final_versioned_VPD_hPa=f(newv),final_versioned_RH_pct=f(newrh),
   cross_variable_scope="STAGE67_T_APPROVED_SEPARATE_RH_VPD_JOINT_PROPOSED",
   research_science_status="TWO_ORIGINAL_QC0_HUMIDITY_DONORS_DUAL_VPD_CHECK_PASS"))
 if len(four)!=4 or len(summary)!=4 or len({r["native_time"] for r in four})!=4:
  raise ValueError("four exact science source records not conserved")
 out.mkdir(exist_ok=False)
 results=out/"stage88_FOUR_US_WHS_QC0_ANCHORED_JOINT_T_RH_VPD_SCIENCE_CANDIDATES.csv"
 mini=out/"stage88_FOUR_CROSS_VARIABLE_PHYSICS_DISPOSITION.csv"
 write(results,FIELDS,four);write(mini,SUMMARY_FIELDS,summary)
 manifest=dict(stage=88,site=SITE,stage67_approved_T_candidate_cohort_HH=51,
   stage87_original_unphysical_four_HH=4,stage88_two_original_QC0_source_RH_donors_repaired_proposals_HH=4,
   max_absolute_difference_vs_QC0_direct_VPD_interpolation_hPa=max(
    abs(float(r["difference_thermodynamic_vs_direct_VPD_hPa"])) for r in four),
   source_original_Whs_CSV_SHA256=ORIG_SHA,
   previous_1675_research_approved_overlay_SHA256=APPROVED_SHA,
   previous_1675_overlay_unchanged=True,Stage67_51_accepted_T_unchanged=True,
   Stage86_research_release_gate_blocked=True,
   independent_tower_RH_at_target_verified=False,
   source_QC_unchanged=True,production_DATM_CIME_modified=False,Slurm_submitted=0,
   output_SHA256={p.name:sha(p) for p in (results,mini)})
 (out/"stage88_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 print("STAGE88 SUCCESS | 4/4 Stage67 Whs approved T candidate+old VPD negative RH, immediate original T0/VPD0 both-sided donor science repairs PASS")
 print("STAGE88 FOUR_SOURCE_QC0_DUAL_METHOD_VPD_ABS_DIFF_MAX",f(manifest["max_absolute_difference_vs_QC0_direct_VPD_interpolation_hPa"]))
 print("STAGE88 SCIENCE_RECORD native approvedT oldVPD donorRH newRH newVPD directOriginalQC0VPD discrepancy")
 for q in four:
  print("STAGE88 VERIFIED",q["native_time"],q["approved_stage67_T_C"],q["source_original_VPD_hPa"],
   q["left_original_QC0_RH_pct"]+"->"+q["right_original_QC0_RH_pct"],
   q["reconstructed_RH_pct"],q["reconstructed_VPD_hPa"],
   q["direct_two_QC0_source_VPD_interpolation_hPa"],
   q["difference_thermodynamic_vs_direct_VPD_hPa"])
 print("STAGE88 FOUR_HH_SCIENCE_CANDIDATE_SHA256="+sha(results))
 print("STAGE88_REPORTS="+str(out))
 print("STAGE88 RESEARCH_NUMERIC_CANDIDATE_ONLY | ORIGINAL/QC/PRIOR1675/STAGE67_51/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

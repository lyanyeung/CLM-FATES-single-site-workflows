#!/usr/bin/env python3
"""Batch05 Stage93 US-Wkg 2025-09-10 13:00: focused source-native diagnosis.

Investigate the one Stage92 strong original QC0 temperature spike hypothesis
(source 12.89 C; neighbors 29.52, 23.47 C; candidate 26.495 C).
Audit full +/-12h original site-native TA/VPD/QC, processed-source ERA
and humidity/radiation/precipitation context, and compare only explicit
counterfactual thermodynamic cases. No original source, QC, approved
1675 HH, DATM/CIME or Slurm changes. Never auto-approve corrected T.
"""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from datetime import datetime,timedelta

SITE="US-Wkg"
TARGET="202509101300"
RELEASE="AMF_US-Wkg_FLUXNET_2004-2025_v1.3_r1"
SOURCE_SHA="f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"
APPROVED_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
CTX_FIELDS=("native_time","relative_minutes","source_TA_C","TA_QC",
 "source_VPD_hPa","VPD_QC","derived_RH_pct","source_ERA_T_C",
 "source_ERA_VPD_hPa","source_ERA_RH_pct","original_P_F",
 "original_SW_IN_F")
OPTION_FIELDS=("science_scenario","candidate_T_C","candidate_VPD_hPa",
 "candidate_RH_pct","methodology","input_original_QC0_VPD_donors",
 "scientific_status")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()
def number(x):
 try:
  y=float(x)
  return y if math.isfinite(y) and y not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def fmt(x):return "" if x is None else f"{x:.9f}"
def sat(t):
 return None if t is None or not -80<=t<=60 else 6.112*math.exp(17.67*t/(t+243.5))
def rh(t,v):
 e=sat(t)
 return None if e is None or v is None else 100*(1-v/e)
def dt(t):return datetime.strptime(t,"%Y%m%d%H%M")
def shift(t,j):return (dt(t)+timedelta(minutes=30*j)).strftime("%Y%m%d%H%M")
def read(p,cols):
 if not p.is_file() or p.is_symlink():raise ValueError("missing original source report "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as f:
  rdr=csv.DictReader(f);heads=rdr.fieldnames or []
  if len(heads)!=len(set(heads)) or not set(cols).issubset(heads):
   raise ValueError("original report schema changed "+str(p))
  rr=list(rdr)
 if any(None in row or any(x is None for x in row.values()) for row in rr):
  raise ValueError("malformed source CSV rows "+str(p))
 return rr
def write(p,cols,rr):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rr)
def selftest():
 assert shift(TARGET,-1)=="202509101230"
 assert shift(TARGET,1)=="202509101330"
 assert rh(0,7)<0 and abs(rh(0,6.112))<1e-9
 assert abs((29.52+23.47)/2-26.495)<1e-8
 assert number("2.3")==2.3 and number("-9999") is None
 print("STAGE93 SELF-TEST PASS | Wkg 202509101300 source T 12.89 vs immediate original QC0 29.52/23.47, no forcing writes")
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage84",type=Path)
 ap.add_argument("--stage92",type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage84,a.stage92,a.out)):
  ap.error("need actual Stage84/Stage92 and a fresh output directory")
 d84,d92,out=(x.expanduser().resolve() for x in (a.stage84,a.stage92,a.out))
 folder=a.sites_root.expanduser().resolve()/SITE/"forcing"/"raw"/RELEASE
 if (not all(x.is_dir() for x in (d84,d92,folder)) or
     out.exists() or not out.parent.is_dir() or
     any(out==x or out in x.parents or x in out.parents for x in (d84,d92,folder))):
  ap.error("input reports/source missing or output not fresh/disjoint")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(f84)!=APPROVED_SHA or m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=APPROVED_SHA):
  raise ValueError("latest 1675 approval source SHA/manifest drift")
 approved=[r for r in read(f84,("site","native_time","modified_TA_C",
       "modified_VPD_hPa","modified_RH_pct","source_TA_C","source_VPD_hPa",
       "source_TA_QC","source_VPD_QC","replacement_RH_provenance"))
       if r["site"]==SITE and r["native_time"]==TARGET]
 if len(approved)!=1:raise ValueError("Wkg source temperature exception not precisely in approved main overlay")
 approved=approved[0]
 s92=d92/"stage92_SEVEN_T_EXCEPTION_EVIDENCE_HYPOTHESES_AND_QC0_ANCHORS.csv"
 c92=d92/"stage92_SEVEN_T_EXCEPTION_EXTENDED_12H_NATIVE_SOURCE_CONTEXT.csv"
 m92=json.loads((d92/"stage92_EXTENDED_SOURCE_T_EVIDENCE_MANIFEST.json").read_text())
 if (m92.get("stage")!=92 or
     m92.get("original_source_exception_count")!=7 or
     m92.get("approved_stage84_1675_SHA256")!=APPROVED_SHA or
     m92.get("automatic_T_repair_approved_HH")!=0 or
     m92.get("original_Site05_CSV_SHA256",{}).get(SITE)!=SOURCE_SHA or
     any(m92.get("output_SHA256",{}).get(p.name)!=sha(p) for p in (s92,c92))):
  raise ValueError("Stage92 actually verified source T evidence SHA/manifest drift")
 seven=read(s92,("site","native_time","source_original_T_C","source_original_T_QC",
   "nearest_two_QC0_T_candidate_C","preliminary_source_T_evidence_category"))
 if len(seven)!=7:raise ValueError("Stage92 seven science exceptions changed")
 s=[r for r in seven if r["site"]==SITE and r["native_time"]==TARGET]
 if len(s)!=1 or s[0]["preliminary_source_T_evidence_category"]!="STRONG_ORIGINAL_T_OUTLIER_EVIDENCE_T_QC0_AND_SOURCE_ERA_AGREE_NEEDS_LOCAL_APPROVAL":
  raise ValueError("Stage92 Wkg 13:00 source-T science classification changed")
 rows92=[r for r in read(c92,("site","center_native","native_time","TA_F_C",
       "TA_F_QC","VPD_F_hPa","VPD_F_QC","source_processed_ERA_T_C",
       "source_processed_ERA_VPD_hPa","source_P_F","source_SW_IN_F"))
       if r["site"]==SITE and r["center_native"]==TARGET]
 if len(rows92)!=49:raise ValueError("Stage92 original 49-row Wkg source context changed")
 reference={r["native_time"]:r for r in rows92}
 if len(reference)!=49 or set(reference)!={shift(TARGET,j) for j in range(-24,25)}:
  raise ValueError("Stage92 Wkg 49 native HH timestamps changed")
 matches=[p for p in folder.iterdir() if re.fullmatch(
  r"AMF_US-Wkg_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",p.name,re.I)]
 if len(matches)!=1 or matches[0].is_symlink() or not matches[0].is_file() or sha(matches[0])!=SOURCE_SHA:
  raise ValueError("original US-Wkg 2004-25 source SHA changed")
 actual={}
 with matches[0].open("r",encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"}.issubset(reader.fieldnames or []):
   raise ValueError("Wkg original native FLUXMET columns absent")
  for r in reader:
   t=r["TIMESTAMP_START"]
   if t in reference:
    if t in actual:raise ValueError("duplicate native Wkg original HH")
    actual[t]=r
 if set(actual)!=set(reference):raise ValueError("Wkg original 49 native HH missing")
 context=[]
 for j in range(-24,25):
  t=shift(TARGET,j);r=actual[t];old=reference[t]
  for a,b in (("TA_F","TA_F_C"),("VPD_F","VPD_F_hPa"),
              ("TA_ERA","source_processed_ERA_T_C"),
              ("VPD_ERA","source_processed_ERA_VPD_hPa"),
              ("TA_F_QC","TA_F_QC"),("VPD_F_QC","VPD_F_QC")):
   v=r.get(a,"");w=old.get(b,"")
   if a.endswith("_QC"):
    if v!=w:raise ValueError("Stage92 native original QC changed "+t+" "+a)
   elif number(v) is None or number(w) is None:
    if not (number(v) is None and number(w) is None):
     raise ValueError("Stage92 native source meteorological missing changed "+t+" "+a)
   elif abs(number(v)-number(w))>.002:
    raise ValueError("Stage92 original source meteorological value changed "+t+" "+a)
  context.append(dict(native_time=t,relative_minutes=j*30,
   source_TA_C=r["TA_F"],TA_QC=r["TA_F_QC"],
   source_VPD_hPa=r["VPD_F"],VPD_QC=r["VPD_F_QC"],
   derived_RH_pct=fmt(rh(number(r["TA_F"]),number(r["VPD_F"]))),
   source_ERA_T_C=r["TA_ERA"],source_ERA_VPD_hPa=r["VPD_ERA"],
   source_ERA_RH_pct=fmt(rh(number(r["TA_ERA"]),number(r["VPD_ERA"]))),
   original_P_F=r.get("P_F",""),original_SW_IN_F=r.get("SW_IN_F","")))
 center,left,right=(actual[shift(TARGET,j)] for j in (0,-1,1))
 originalT=number(center["TA_F"]);originalV=number(center["VPD_F"])
 oldT=number(approved["source_TA_C"]);oldV=number(approved["source_VPD_hPa"])
 nowT=number(approved["modified_TA_C"])
 nowV=number(approved["modified_VPD_hPa"]);nowRH=number(approved["modified_RH_pct"])
 if (any(x is None for x in (originalT,originalV,oldT,oldV,nowT,nowV,nowRH)) or
     abs(originalT-12.89)>.002 or abs(originalT-oldT)>.002 or abs(originalV-oldV)>.002 or
     abs(nowT-originalT)>.002 or
     center["TA_F_QC"]!="0" or
     left["TA_F_QC"]!="0" or right["TA_F_QC"]!="0" or
     center["VPD_F_QC"]!=approved["source_VPD_QC"] or
     abs(rh(nowT,nowV)-nowRH)>.05):
  raise ValueError("Wkg actual immutable original and approved 1675 physical values changed")
 lt,rt=number(left["TA_F"]),number(right["TA_F"])
 if lt is None or rt is None or abs(lt-29.52)>.002 or abs(rt-23.47)>.002:
  raise ValueError("original Wkg immediate T QC0 donors changed")
 cand=(lt+rt)/2
 if abs(cand-26.495)>.002 or abs(cand-number(s[0]["nearest_two_QC0_T_candidate_C"]))>.002:
  raise ValueError("source Wkg prospective T original QC0 midpoint changed")
 # Alternative T/VPD/RH pathways are nonapproved counterfactuals.
 options=[]
 def add(name,T,V,method,sourceQC0):
  rr=rh(T,V)
  options.append(dict(science_scenario=name,candidate_T_C=fmt(T),
   candidate_VPD_hPa=fmt(V),candidate_RH_pct=fmt(rr),
   methodology=method,input_original_QC0_VPD_donors=str(sourceQC0),
   scientific_status="NONPRODUCTION_SENSITIVITY_ONLY_NO_AUTOMATIC_T_OR_VPD_REPLACEMENT"))
 add("KEEP_SOURCE_T_AND_APPROVED_RH_VPD",nowT,nowV,
     "current 1675 HH approved research reconstructed RH/VPD + original source T",False)
 add("CANDIDATE_T_KEEP_APPROVED_VPD",cand,nowV,
     "source QC0 T midpoint; VPD unchanged from research approved 1675; RH recomputed",False)
 add("CANDIDATE_T_KEEP_APPROVED_RH",cand,sat(cand)*(1-nowRH/100),
     "source QC0 T midpoint; preserve old approved RH; recompute VPD",False)
 leftRH=rh(number(left["TA_F"]),number(left["VPD_F"]))
 rightRH=rh(number(right["TA_F"]),number(right["VPD_F"]))
 has_QC0V=(left["VPD_F_QC"]=="0" and right["VPD_F_QC"]=="0" and
   leftRH is not None and rightRH is not None and
   1<=leftRH<=100 and 1<=rightRH<=100)
 if has_QC0V:
  interpRH=(leftRH+rightRH)/2
  interpV=(number(left["VPD_F"])+number(right["VPD_F"]))/2
  add("CANDIDATE_T_QC0_HUMIDITY_RH_MIDPOINT",cand,
      sat(cand)*(1-interpRH/100),
      "native immediate two-sided VPD_QC0/T_QC0 original inferred RH midpoint; not measured target RH",True)
  add("CANDIDATE_T_QC0_SOURCE_VPD_MIDPOINT",cand,interpV,
      "native two-sided VPD_QC0 original VPD direct midpoint; independent numeric sensitivity",True)
 if len(options)<3:raise ValueError("missing essential original source Wkg T/RH/VPD counterfactuals")
 report=dict(stage=93,site=SITE,native_time=TARGET,
  original_T_C=originalT,original_T_QC=center["TA_F_QC"],
  original_VPD_hPa=originalV,original_VPD_QC=center["VPD_F_QC"],
  before_T_C=lt,before_T_QC=left["TA_F_QC"],before_VPD_QC=left["VPD_F_QC"],
  after_T_C=rt,after_T_QC=right["TA_F_QC"],after_VPD_QC=right["VPD_F_QC"],
  two_T_QC0_neighbors_disagreement_C=abs(lt-rt),
  native_QC0_candidate_T_C=cand,source_T_minus_candidate_T_C=originalT-cand,
  source_processed_ERA_T_C=number(center["TA_ERA"]),
  original_QC0_VPD_donors_both_valid=bool(has_QC0V),
  source_original_CSV_SHA256=SOURCE_SHA,source_Stage92_context_SHA256=sha(c92),
  previous_1675_approved_SHA256=APPROVED_SHA,
  source_T_replacement_approved=False,source_original_QC_unchanged=True,
  prior_1675_approved_research_overlay_unchanged=True,
  DATM_CIME_unchanged=True,Slurm_submitted=0,
  science_disposition="SOURCE_T_HYPOTHESIS_STRONG_BUT_DONORS_DISAGREE_GT_5C_INDEPENDENT_LOCAL_EVIDENCE_REQUIRED",
  forcing_release_permission="NO")
 out.mkdir(exist_ok=False)
 fcontext=out/"stage93_WKG_SEPT2025_12H_ORIGINAL_NATIVE_T_VPD_ERA_P_SW.csv"
 foptions=out/"stage93_WKG_SEPT2025_ORIGINAL_VS_T_AND_HUMIDITY_SCENARIOS_READONLY.csv"
 manifest=out/"stage93_WKG_SEPT2025_LOCAL_SCIENCE_MANIFEST.json"
 write(fcontext,CTX_FIELDS,context)
 write(foptions,OPTION_FIELDS,options)
 report["output_SHA256"]={f.name:sha(f) for f in (fcontext,foptions)}
 manifest.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("STAGE93 SUCCESS | Wkg 2025-09-10 13:00 native original T anomaly, SHA and 49 original HH verified, no T/VPD forcing edits")
 print("STAGE93 ORIGINAL",TARGET,"TA",fmt(originalT),"QC",center["TA_F_QC"],
   "VPD",fmt(originalV),"QC",center["VPD_F_QC"],
   "source_ERA_T",center["TA_ERA"],"source_ERA_RH",
   fmt(rh(number(center["TA_ERA"]),number(center["VPD_ERA"]))))
 print("STAGE93 QC0_T_ANCHORS",shift(TARGET,-1),fmt(lt),shift(TARGET,1),fmt(rt),
   "candidate_T",fmt(cand),"donor_disagreement",fmt(abs(lt-rt)))
 print("STAGE93 ORIGINAL_QC0_HUMIDITY_BOTH_VALID",has_QC0V,
   "beforeVPD",left["VPD_F"],"beforeQC",left["VPD_F_QC"],
   "afterVPD",right["VPD_F"],"afterQC",right["VPD_F_QC"])
 print("STAGE93 SCENARIO scenario T VPD RH original_QC0VPD_donors")
 for rr in options:
  print("STAGE93 SCENARIO",rr["science_scenario"],
    rr["candidate_T_C"],rr["candidate_VPD_hPa"],
    rr["candidate_RH_pct"],rr["input_original_QC0_VPD_donors"])
 print("STAGE93 ORIGINAL_CONTEXT_6H native TA T_QC VPD VPD_QC RH ERA_T ERA_RH P SW")
 for r in context:
  if abs(r["relative_minutes"])<=360:
   print("STAGE93 CONTEXT",r["native_time"],r["source_TA_C"],r["TA_QC"],
     r["source_VPD_hPa"],r["VPD_QC"],r["derived_RH_pct"],
     r["source_ERA_T_C"],r["source_ERA_RH_pct"],
     r["original_P_F"],r["original_SW_IN_F"])
 print("STAGE93 SCIENCE_DISPOSITION",report["science_disposition"])
 print("STAGE93_REPORTS="+str(out))
 print("STAGE93 READONLY SCIENCE ONLY | ORIGINAL/QC/PRIOR1675/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":
 main()

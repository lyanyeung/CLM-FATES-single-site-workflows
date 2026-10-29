#!/usr/bin/env python3
"""Batch05 Stage89 scientific release-preflight, READ ONLY.

Preview one CONSISTENT separate native US-Whs 51 HH T/RH/VPD research
overlay: all 51 operator-accepted Stage67 T interpolations, four Stage88
QC0-bracketed VPD/RH research reconstruction proposals, 47 ORIGINAL VPD
retained (numeric RH physical only). Strict original source SHA, Stage67,
Stage84 approved 1675, Stage86 release gate, Stage88 four source SHAs.
Never update original QC, Stage67, 1675 main RH/VPD overlay, DATM/CIME or
Slurm; output is NOT production or automatic Stage88 user approval.
"""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from collections import Counter

SITE="US-Whs"
RAW_SHA="653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca"
PREV_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
RELEASE="AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1"
FOUR={"200910290430","200910300200","200910301100","201303081100"}
COLS="site native_time source_T_QC source_VPD_QC original_T_C approved_Stage67_T_C original_VPD_hPa proposed_joint_VPD_hPa source_original_RH_pct combined_RH_pct combined_VPD_method scientific_status source_stage67_run_id stage88_four_source_QC0_repair_overlay production_permission".split()
def checksum(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def n(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def sat(T):
 return None if T is None or not -80<=T<=60 else 6.112*math.exp(17.67*T/(T+243.5))
def rh(T,V):
 e=sat(T)
 return None if e is None or V is None else 100*(1-V/e)
def fmt(v):return "" if v is None else f"{v:.9f}"
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("missing immutable source/report "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  rd=csv.DictReader(h);cols=rd.fieldnames or []
  if len(cols)!=len(set(cols)) or not set(required).issubset(cols):
   raise ValueError("source/report schema mismatch "+str(p))
  records=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in records):
  raise ValueError("invalid original CSV source width "+str(p))
 return records
def indexed(rows):
 d={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in d:raise ValueError("duplicate site/native time "+str(k))
  d[k]=r
 return d
def write(p,headers,rows):
 with p.open("x",encoding="utf-8",newline="") as h:
  writer=csv.DictWriter(h,fieldnames=headers,extrasaction="raise")
  writer.writeheader();writer.writerows(rows)
def selftest():
 assert 47+4==51 and len(FOUR)==4
 assert abs(rh(0,6.112))<1e-9 and rh(0,7)<0
 assert n("2.0")==2.0 and n("-9999") is None
 print("STAGE89 SELF-TEST PASS | Whs 51 Stage67 accepted TA HH, 4 Stage88 joint T/VPD proposals +47 original VPD; source and prior1675 preserved")
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 for k in ("stage67","stage84","stage86","stage88"):
  ap.add_argument("--"+k,type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,k) is None for k in ("stage67","stage84","stage86","stage88","out")):
  ap.error("provide verified Stage67/84/86/88 directories and NEW output")
 d67,d84,d86,d88,out=(getattr(a,k).expanduser().resolve() for k in
                      ("stage67","stage84","stage86","stage88","out"))
 original_dir=a.sites_root.expanduser().resolve()/SITE/"forcing"/"raw"/RELEASE
 if (not all(x.is_dir() for x in (d67,d84,d86,d88,original_dir)) or
     out.exists() or not out.parent.is_dir() or
     any(out==x or out in x.parents or x in out.parents for x in
         (d67,d84,d86,d88,original_dir))):
  ap.error("prior inputs or fresh disjoint output directory unavailable")
 prevf=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 prevmanifest=json.loads((d84/"stage84_manifest.json").read_text())
 if (checksum(prevf)!=PREV_SHA or prevmanifest.get("total_versioned_approved_repair_rows")!=1675
     or prevmanifest.get("output_SHA256",{}).get(prevf.name)!=PREV_SHA):
  raise ValueError("last approved Stage84 1675 versioned research overlay hash drift")
 prev=indexed(read(prevf,["site","native_time"]))
 if len(prev)!=1675:raise ValueError("previous 1675 original site/time unique keys changed")
 cf=d67/"stage67_USER_SELECTED_TA_INTERPOLATION_CANDIDATE_ONLY.csv"
 ef=d67/"stage67_ALL30_TARGETED_QC_TRANSITIONS_AND_DECISIONS.csv"
 hf=d67/"stage67_UNREPAIRABLE_QC_BRACKET_HOLDS.csv"
 cm=json.loads((d67/"stage67_manifest.json").read_text())
 if (cm.get("final_candidate_repaired_TA_HH")!=51 or
     any(cm.get("output_sha256",{}).get(x.name)!=checksum(x) for x in (cf,ef,hf))):
  raise ValueError("Stage67 accepted T candidates source evidence changed")
 candidates=indexed(read(cf,["site","native_time","original_source_TA_F_C",
     "candidate_TA_F_C","source_QC_unchanged",
     "source_VPD_F_hPa_unchanged","source_VPD_F_QC_unchanged","source_run_id"]))
 if (len(candidates)!=51 or {k[0] for k in candidates}!={SITE} or
     any(k in prev for k in candidates)):
  raise ValueError("Stage67 all 51 original target HH unique/site/separate scope failed")
 m86=json.loads((d86/"stage86_FINAL_TEN_SITE_RESEARCH_QC_RELEASE_GATES.json").read_text())
 if (m86.get("stage")!=86 or m86.get("final_versioned_research_approved_HH")!=1675
     or m86.get("stage67_T_candidate_original_VPD_physics_issues")!=4
     or m86.get("Stage67_T_candidate_overlapping_main_overlay_HH")!=0
     or m86.get("historical_P1_HOLD_HH")!=46
     or m86.get("historical_RH_platform_HOLD_HH")!=10
     or m86.get("source_T_pending_science_exception_HH")!=7
     or m86.get("current_overlay_SHA256")!=PREV_SHA):
  raise ValueError("Stage86 actual ten-site blocked science release-gate differs")
 ff=d88/"stage88_FOUR_US_WHS_QC0_ANCHORED_JOINT_T_RH_VPD_SCIENCE_CANDIDATES.csv"
 mf=d88/"stage88_manifest.json"
 m88=json.loads(mf.read_text())
 cf88=d88/"stage88_FOUR_CROSS_VARIABLE_PHYSICS_DISPOSITION.csv"
 if (m88.get("stage")!=88 or
     m88.get("stage88_two_original_QC0_source_RH_donors_repaired_proposals_HH")!=4 or
     m88.get("previous_1675_research_approved_overlay_SHA256")!=PREV_SHA or
     m88.get("Stage67_51_accepted_T_unchanged") is not True or
     m88.get("source_original_Whs_CSV_SHA256")!=RAW_SHA or
     any(m88.get("output_SHA256",{}).get(p.name)!=checksum(p) for p in (ff,cf88))):
  raise ValueError("Stage88 actual four exact-source QC0 science proposal manifest mismatch")
 joint=indexed(read(ff,["site","native_time","approved_stage67_T_C",
     "source_original_VPD_hPa","source_original_VPD_QC","reconstructed_RH_pct",
     "reconstructed_VPD_hPa","production_DATM_permission"]))
 if (len(joint)!=4 or {k[1] for k in joint}!=FOUR or
     not set(joint).issubset(candidates)):
  raise ValueError("Stage88 four joint native source keys incorrect")
 raw=[x for x in original_dir.iterdir() if x.is_file() and not x.is_symlink()
      and re.fullmatch(r"AMF_US-Whs_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",x.name,re.I)]
 if len(raw)!=1 or checksum(raw[0])!=RAW_SHA:
  raise ValueError("original Whs Stage05 native FLUXMET CSV strict SHA changed")
 original={}
 want={k[1] for k in candidates}
 with raw[0].open(encoding="utf-8-sig",newline="") as h:
  rd=csv.DictReader(h);heads=rd.fieldnames or []
  if len(heads)!=len(set(heads)) or not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"}.issubset(heads):
   raise ValueError("original source Whs native schema drift")
  for row in rd:
   t=row["TIMESTAMP_START"]
   if t in want:
    if t in original:raise ValueError("duplicate source time "+t)
    original[t]=row
 if len(original)!=51:raise ValueError("original source 51 native source HH missing")
 outcomes=[];count=Counter()
 for k in sorted(candidates):
  c=candidates[k];o=original[k[1]]
  oldT,oldV=n(o["TA_F"]),n(o["VPD_F"])
  T=n(c["candidate_TA_F_C"])
  if (any(v is None for v in (oldT,oldV,T)) or
      n(c["original_source_TA_F_C"]) is None or
      n(c["source_VPD_F_hPa_unchanged"]) is None or
      abs(oldT-n(c["original_source_TA_F_C"]))>0.002 or
      abs(oldV-n(c["source_VPD_F_hPa_unchanged"]))>0.002 or
      o["TA_F_QC"]!=c["source_QC_unchanged"] or
      o["VPD_F_QC"]!=c["source_VPD_F_QC_unchanged"]):
   raise ValueError("Stage67 approved source original TA/VPD/QC differs from Stage05 native "+k[1])
  j=joint.get(k);chosenV=oldV
  method="STAGE67_T_CANDIDATE_UNCHANGED_SOURCE_VPD_WITH_PHYSICAL_RH_ONLY"
  status="STAGE67_USER_APPROVED_T_ONLY_RH_PHYSICAL_NOT_INDEPENDENTLY_HUMIDITY_VALIDATED"
  if j:
   if (j["production_DATM_permission"]!="NO" or
       abs(n(j["approved_stage67_T_C"])-T)>1e-5 or
       abs(n(j["source_original_VPD_hPa"])-oldV)>0.002 or
       j["source_original_VPD_QC"]!=o["VPD_F_QC"]):
    raise ValueError("Stage88 separate Whs source original VPD/approved T provenance changed "+k[1])
   chosenV=n(j["reconstructed_VPD_hPa"])
   if chosenV is None or abs(rh(T,chosenV)-n(j["reconstructed_RH_pct"]))>1e-5:
    raise ValueError("Stage88 joint VPD / RH / Stage67 T physical mismatch "+k[1])
   method="STAGE88_TWO_IMMEDIATE_ORIGINAL_QC0_RH_DONORS_RECONSTRUCT_VPD_AT_STAGE67_T"
   status="STAGE88_USER_DIRECTED_RESEARCH_PROPOSAL_NEEDS_FINAL_MERGE_APPROVAL"
  selectedRH=rh(T,chosenV)
  if selectedRH is None or not 0<=selectedRH<=100 or not 0<=chosenV<=sat(T):
   raise ValueError("Stage89 combined 51 T/VPD RH physically impossible "+k[1])
  count["stage88_joint" if j else "stage67_T_only"]+=1
  outcomes.append(dict(site=SITE,native_time=k[1],
   source_T_QC=o["TA_F_QC"],source_VPD_QC=o["VPD_F_QC"],
   original_T_C=o["TA_F"],approved_Stage67_T_C=fmt(T),
   original_VPD_hPa=o["VPD_F"],proposed_joint_VPD_hPa=fmt(chosenV),
   source_original_RH_pct=fmt(rh(oldT,oldV)),combined_RH_pct=fmt(selectedRH),
   combined_VPD_method=method,scientific_status=status,
   source_stage67_run_id=c["source_run_id"],
   stage88_four_source_QC0_repair_overlay="YES" if j else "NO",
   production_permission="NO"))
 if len(outcomes)!=51 or count!={"stage67_T_only":47,"stage88_joint":4}:
  raise ValueError("Stage89 full 51 candidate 47+4 count drift")
 out.mkdir(exist_ok=False)
 f51=out/"stage89_SEPARATE_WHS_51_T_RH_VPD_VERSIONED_INTEGRATION_PREVIEW.csv"
 fsummary=out/"stage89_SEPARATE_WHS_51_T_RH_VPD_READONLY_PREVIEW_MANIFEST.json"
 write(f51,COLS,outcomes)
 report=dict(stage=89,site=SITE,previous_main_RH_repair_overlay_HH=1675,
  stage67_approved_T_candidate_HH=51,
  stage88_QC0_RH_derived_VPD_joint_reconstruction_HH=4,
  stage67_T_only_original_source_VPD_retained_HH=47,
  combined_51_physics_RH_out_of_range_HH=0,
  original_Whs_CSV_SHA256=RAW_SHA,previous_main_overlay_SHA256=PREV_SHA,
  stage88_four_joint_candidate_sha256=checksum(ff),output_preview_SHA256=checksum(f51),
  downstream_release_gate="BLOCKED_P1_46_RH_PLATFORM_10_T_EXCEPTIONS_7_SOURCE_ERA_PROXY_VALIDATION",
  separate_integration_preview_not_production_or_user_final_merge_approval=True,
  stage67_original_51_T_and_Stage88_four_unchanged=True,
  original_data_QC_unchanged=True,main_1675_unchanged=True,
  DATM_CIME_unchanged=True,Slurm_submitted=0)
 fsummary.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("STAGE89 SUCCESS | Whs SEPARATE 51 TA source science: 47 original VPD physically feasible + 4 Stage88 original QC0-anchored new VPD, 0 RH invalid")
 print("STAGE89 EXACT 1675 MAIN APPROVED OVERLAY SOURCE SHA VERIFIED",PREV_SHA)
 print("STAGE89 SCIENCE_COUNTS",json.dumps(dict(count),sort_keys=True))
 print("STAGE89 PREVIEW_SHA256="+checksum(f51))
 print("STAGE89 RELEASE_GATE",report["downstream_release_gate"])
 print("STAGE89_REPORTS="+str(out))
 print("STAGE89 PREVIEW ONLY | ORIGINAL/QC/PRIOR1675/STAGE67_51/STAGE88_FOUR/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

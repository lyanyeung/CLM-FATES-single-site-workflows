#!/usr/bin/env python3
"""Batch05 DIRECT AD400 READINESS ONLY: no AD5 trial, no Normal stage.

Scientific source work:
 - Stage84: immutable main research overlay 1675 HH SHA.
 - Stage86: ten-site original P2/P3 1574 disposed and 1266 ERA-source
   research reconstruction proxies (not independent humidity observations).
 - Stage89: Whs additional 51 T research preview (47 original VPD+4 new).
 - Stage90: exactly 63 distinct source science risk HH, including seven T.
 - Stage97: exactly 56 held P1/platform source HH, 10 contiguous groups.

HPC inventory: ten exact FLUXNET source directories from Stage05; selected
DATM, surface and case directory presence; check documented CIME setup
if a Batch05-named case exists. Never assume non-Batch05 cases belong
to Batch05. Never build or modify case/forcing/surface; never Slurm submit.

The intended DIRECT AD400 means submit a completed CIME case once, with
STOP_N=5 REST_N=5 RESUBMIT=79 (80*5=400 accelerated years), without
a separate AD5 pilot. No submission unless independent science review,
all ten production DATM science audits, appropriate PFT/soil/surface,
and exact CIME case/preflight are eventually PASS.
"""
import argparse,csv,hashlib,json,re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

B=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
SOURCE=B/"sites/MY_EC_SITE"
CASES=B/"cases"
OUTPUTS=Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
APP_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
PREVIEW_SHA="95aefd6027e6f981ac821266bc379b89d9f1299d1c307b7575a17fec65588561"
SITES=[
 ("US-UiD","AMF_US-UiD_FLUXNET_2008-2024_v1.3_r1",2008,2024,"FLUXMET"),
 ("US-UMB","AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5",2007,2021,"FULLSET"),
 ("US-UMd","AMF_US-UMd_FLUXNET_2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 ("US-Var","AMF_US-Var_FLUXNET_2000-2025_v1.3_r1",2000,2025,"FLUXMET"),
 ("US-Vcm","AMF_US-Vcm_FLUXNET_2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 ("US-Vcp","AMF_US-Vcp_FLUXNET_2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 ("US-WCr","AMF_US-WCr_FLUXNET_1999-2025_v1.3_r1",1999,2025,"FLUXMET"),
 ("US-Whs","AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 ("US-Wjs","AMF_US-Wjs_FLUXNET_2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 ("US-Wkg","AMF_US-Wkg_FLUXNET_2004-2025_v1.3_r1",2004,2025,"FLUXMET")]
CSV_FIELDS=("site","source_start","source_end","intended_direct_AD400_start","intended_AD400_end",
 "source_native_HH_CSV_present","source_native_HH_CSV_size_bytes",
 "source_native_Stage05_SHA_reverified_in_this_stage",
 "reviewed_research_overlay_HH","source_processed_ERA_proxy_research_HH",
 "source_T_risk_HH","historical_P1_HOLD_HH","historical_RH_platform_HOLD_HH",
 "candidate_DATM_file_count_unverified","candidate_surface_file_count_unverified",
 "existing_Batch05_named_CIME_case_count","existing_Batch05_case_names",
 "case_AD400_config_checked","production_DATM_science_approved","PFT_surface_soil_approved",
 "AD400_submit_gate")
CHECKLIST=(
 "1. Original-source exception policy: seven T source anomalies: explicit KEEP/MASK/"
 "separately justified locally verified substitute, preserving original source & QC.",
 "2. Original 56 HOLD source HH: 35 QC2 negative RH and matching invalid processed-ERA pair"
 " require independent reference/gapfill or permitted exclusion; 11 P1 very-low RH"
 " and 10 platform records need science decisions, not automatic replacements.",
 "3. Audit all source-processed ERA RH proxy repairs in research 1675 against truly"
 " independent ERA5-Land or tower evidence; do not treat same-source companion as independent.",
 "4. Produce NEW versioned complete meteorological forcing candidates at original site clocks"
 " with humidity/T/VPD/P/FSDS/FLDS/pressure/height units, missing values,"
 " QC/source, 1:1 timestamp and overlap checks; do not rewrite original FLUXMET ZIP/CSV.",
 "5. Validate correct site PFT composition/bare/soil/coordinates and build NEW"
 " explicitly named Batch05 surface files; never reuse another cohort without audited equivalence.",
 "6. Prepare 10 distinct Batch05 CIME cases and exact DATM streams; check ZBOT,"
 " source clock/UTC, forcing cycle years, CO2, FATES active competition policy,"
 " 1x1 surf/mesh, file manifests and executable.",
 "7. Intended direct accelerated AD400 case config: RUN_TYPE=startup,"
 " CLM_ACCELERATED_SPINUP=on, STOP_OPTION=nyears, STOP_N=5,"
 " REST_OPTION=nyears, REST_N=5, RESUBMIT=79,"
 " RESUBMIT_SETS_CONTINUE_RUN=TRUE; 80 consecutive segments (not standalone AD5 trial).",
 "8. Submission guard on IRIDIS6 when and only when PASS: inheritable stack >=65536 KiB;"
 " clean new case and no pre-existing submission; write ATTEMPTED receipt before one"
 " CIME case.submit; never retry blindly after uncertain outcome. Audit archive"
 " dependencies, restart years, and spinup_state after job execution.")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def load(p,needed):
 if not p.is_file() or p.is_symlink():raise ValueError("missing SHA-verified source/report "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as h:
  rd=csv.DictReader(h);heads=rd.fieldnames or []
  if len(heads)!=len(set(heads)) or not set(needed).issubset(heads):
   raise ValueError("science report schema drift "+str(p))
  rows=list(rd)
 if any(None in r or any(x is None for x in r.values()) for r in rows):
  raise ValueError("science report CSV malformed "+str(p))
 return rows
def xmlvars(path):
 result={}
 if not path.is_file():return result
 try:root=ET.parse(path).getroot()
 except (ET.ParseError, OSError):return {"_XML_PARSE_ERROR":"TRUE"}
 for e in root.iter("entry"):
  k=e.attrib.get("id")
  if k:result[k]=e.attrib.get("value",e.text or "")
 return result
def csvwrite(p,headers,rr):
 with p.open("x",encoding="utf-8",newline="") as stream:
  w=csv.DictWriter(stream,fieldnames=headers,extrasaction="raise")
  w.writeheader();w.writerows(rr)
def count_directory_children(directory,patterns):
 if not directory.is_dir() or directory.is_symlink():return 0
 return len({str(p) for pattern in patterns for p in directory.glob(pattern)
            if p.is_file() and not p.is_symlink()})
def selftest():
 assert len(SITES)==10 and len({s[0] for s in SITES})==10
 assert all(e>=s and e-s<100 for _,_,s,e,_ in SITES)
 assert 80*5==400 and 80-1==79
 assert len(CHECKLIST)==8
 print("BATCH05 DIRECT AD400 PREFLIGHT SELF-TEST PASS | target 400y = 80x5y once, no 5y pilot, no CIME/Slurm mutations")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for k in ("stage84","stage86","stage89","stage90","stage97"):
  p.add_argument("--"+k,type=Path)
 p.add_argument("--source-root",type=Path,default=SOURCE)
 p.add_argument("--case-root",type=Path,default=CASES)
 p.add_argument("--output-root",type=Path,default=OUTPUTS)
 p.add_argument("--out",type=Path)
 o=p.parse_args()
 if o.self_test:selftest();return
 if any(getattr(o,k) is None for k in ("stage84","stage86","stage89","stage90","stage97","out")):
  p.error("successful exact Stage84/86/89/90/97 actual reports and NEW output required")
 ds={k:getattr(o,k).expanduser().resolve() for k in
     ("stage84","stage86","stage89","stage90","stage97")}
 out=o.out.expanduser().resolve()
 source=o.source_root.expanduser().resolve()
 cases=o.case_root.expanduser().resolve()
 output_root=o.output_root.expanduser().resolve()
 if (any(not x.is_dir() for x in ds.values()) or out.exists() or
     not out.parent.is_dir() or
     any(out==d or out in d.parents or d in out.parents for d in
         (*ds.values(),source,cases,output_root))):
  p.error("original science reports missing or output not new/disjoint")
 d84,d86,d89,d90,d97=(ds[x] for x in ("stage84","stage86","stage89","stage90","stage97"))
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(f84)!=APP_SHA or m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=APP_SHA):
  raise ValueError("Stage84 protected 1675 source SHA/manifest drift")
 approved=load(f84,("site","native_time"))
 if len(approved)!=1675 or len({(r["site"],r["native_time"]) for r in approved})!=1675:
  raise ValueError("Stage84 source native 1675 unique keys invalid")
 f86=d86/"stage86_FINAL_TEN_SITE_RESEARCH_QC_RELEASE_GATES.json"
 m86=json.loads(f86.read_text())
 if (m86.get("stage")!=86 or m86.get("current_overlay_SHA256")!=APP_SHA
     or m86.get("original_source_P2P3_HH") not in (1574,None)
     or m86.get("historical_P1_HOLD_HH")!=46
     or m86.get("historical_RH_platform_HOLD_HH")!=10
     or m86.get("source_T_pending_science_exception_HH")!=7
     or m86.get("current_overlay_corrected_physics_issues")!=0):
  raise ValueError("Stage86 ten-site original science release status drift")
 f89=d89/"stage89_SEPARATE_WHS_51_T_RH_VPD_VERSIONED_INTEGRATION_PREVIEW.csv"
 m89=json.loads((d89/"stage89_SEPARATE_WHS_51_T_RH_VPD_READONLY_PREVIEW_MANIFEST.json").read_text())
 if (sha(f89)!=PREVIEW_SHA or m89.get("output_preview_SHA256")!=PREVIEW_SHA
     or m89.get("stage67_approved_T_candidate_HH")!=51
     or m89.get("stage88_QC0_RH_derived_VPD_joint_reconstruction_HH")!=4
     or m89.get("combined_51_physics_RH_out_of_range_HH")!=0):
  raise ValueError("Stage89 51 T-VPD source-science preview drift")
 f90=d90/"stage90_UNIQUE_HISTORICAL_SCIENCE_RELEASE_RISK_SOURCE_EVIDENCE.csv"
 m90=json.loads((d90/"stage90_FINAL_HISTORICAL_RELEASE_RISK_EVIDENCE_MANIFEST.json").read_text())
 if (m90.get("distinct_release_risk_source_HH")!=63
     or m90.get("historical_P1_HOLD_HH")!=46
     or m90.get("historical_RH_platform_HOLD_HH")!=10
     or m90.get("historical_source_T_exception_HH")!=7
     or m90.get("overlapping_risk_categories_source_HH")!=0
     or m90.get("latest_1675_research_approved_overlay_SHA256")!=APP_SHA
     or m90.get("output_SHA256",{}).get(f90.name)!=sha(f90)):
  raise ValueError("Stage90 distinct 63 source-risk manifest/SHA drift")
 f97=d97/"stage97_56_ORIGINAL_HOLD_HH_SCIENCE_DECISION_MATRIX.csv"
 fruns=d97/"stage97_SOURCE_HOLD_CONTIGUOUS_SCIENCE_EPISODES.csv"
 m97=json.loads((d97/"stage97_SOURCE_PROTECTED_HOLDS_CLOSURE_GATE_MANIFEST.json").read_text())
 expected_groups={"P1_SOURCE_QC2_NEGATIVE_AND_SAME_PROCESSED_ERA_INVALID":35,
  "P1_SOURCE_RH_POSITIVE_NO_BOTH_QC0_ANCHORS":10,
  "P1_SOURCE_RH_POSITIVE_WITH_BOTH_QC0_ANCHORS":1,
  "PLATFORM_VCM_NEAR_99_46_ORIGINAL_QC0":4,
  "PLATFORM_WCR_EXACT_100_ORIGINAL_QC0":6}
 if (m97.get("stage")!=97 or m97.get("source_HOLDs_verified")!=56
     or m97.get("source_contiguous_episodes")!=10
     or m97.get("science_groups")!=expected_groups
     or m97.get("operator_original_hold_approved_HH")!=0
     or m97.get("protected_stage84_1675_sha256")!=APP_SHA
     or any(m97.get("output_SHA256",{}).get(p.name)!=sha(p) for p in (f97,fruns))):
  raise ValueError("Stage97 exact user operator 10 episodes 56 protected HH science status drift")
 risks=load(f90,("site","native_time","source_risk_categories"))
 holds=load(f97,("site","native_time","review_group"))
 if len(risks)!=63 or len(holds)!=56:
  raise ValueError("Stage90/97 original risk source row scope changed")
 overlay_count=Counter(r["site"] for r in approved)
 proxy_by_site=m86.get("site_proxy_method_counts",{})
 if not isinstance(proxy_by_site,dict):
  raise ValueError("Stage86 source ERA-proxy research method inventory unavailable")
 riskcnt=Counter()
 for r in risks:
  for cat in r["source_risk_categories"].split(";"):
   riskcnt[(r["site"],cat)]+=1
 if not source.is_dir():
  raise ValueError("Stage05 original source folder tree absent (no source audit)")
 candidate_cases={}
 if cases.is_dir():
  for c in cases.iterdir():
   if not c.is_dir() or c.is_symlink():continue
   if any(x in c.name.upper() for x in ("B05","BATCH05")):
    candidate_cases[c.name]=c
 inventories=[]
 for site,release,start,end,product in SITES:
  raw_dir=source/site/"forcing"/"raw"/release
  regex=re.compile(r"AMF_"+re.escape(site)+r"_FLUXNET_"+product+r"_(HH|HR)_.+[.]csv",re.I)
  raw=[v for v in raw_dir.iterdir() if v.is_file() and not v.is_symlink() and regex.fullmatch(v.name)] if raw_dir.is_dir() else []
  raw_ok=len(raw)==1
  forcing=source/site/"forcing"
  dcount=count_directory_children(forcing/"datm",("*.nc","*/*.nc"))
  dcount+=count_directory_children(forcing/"selected",("*.nc","*/*.nc"))
  dcount+=count_directory_children(forcing/"processed",("*.nc","*/*.nc"))
  surf=source/site
  scount=count_directory_children(surf,("surfdata*.nc","surface*.nc","*/*surfdata*.nc"))
  cases_for_site=[(name,path) for name,path in candidate_cases.items()
     if name.startswith(site+"_") or name.startswith(site+"-")]
  selected=[]
  checked=False
  for name,c in cases_for_site:
   xml=xmlvars(c/"env_run.xml")
   if (xml.get("STOP_OPTION")=="nyears" and xml.get("STOP_N")=="5"
       and xml.get("REST_OPTION")=="nyears" and xml.get("REST_N")=="5"
       and xml.get("RESUBMIT")=="79"
       and xml.get("RUN_TYPE")=="startup"
       and xml.get("CLM_ACCELERATED_SPINUP")=="on"
       and xml.get("RESUBMIT_SETS_CONTINUE_RUN","").lower()=="true"):
    checked=True
   selected.append(name)
  if not raw_ok:
   print("BATCH05 SOURCE WARNING",site,"original native source count",len(raw))
  inventories.append(dict(site=site,source_start=start,source_end=end,
    intended_direct_AD400_start=start,intended_AD400_end=start+400,
    source_native_HH_CSV_present=str(raw_ok),
    source_native_HH_CSV_size_bytes=raw[0].stat().st_size if raw_ok else "",
    source_native_Stage05_SHA_reverified_in_this_stage="False",
    reviewed_research_overlay_HH=overlay_count[site],
    source_processed_ERA_proxy_research_HH=proxy_by_site.get(site,0),
    source_T_risk_HH=riskcnt[(site,"UNRESOLVED_SOURCE_T_EXCEPTION")],
    historical_P1_HOLD_HH=riskcnt[(site,"P1_HISTORICAL_HOLD")],
    historical_RH_platform_HOLD_HH=riskcnt[(site,"RH_SATURATION_PLATFORM_HOLD")],
    candidate_DATM_file_count_unverified=dcount,
    candidate_surface_file_count_unverified=scount,
    existing_Batch05_named_CIME_case_count=len(selected),
    existing_Batch05_case_names=";".join(sorted(selected)),
    case_AD400_config_checked=str(checked),
    production_DATM_science_approved="False",
    PFT_surface_soil_approved="False",
    AD400_submit_gate="BLOCKED_SCIENCE_AND_INPUT_CASE_AUDITS"))
 if sum(x["reviewed_research_overlay_HH"] for x in inventories)!=1675:
  raise ValueError("all ten site approved overlay does not crosswalk to inventory")
 if sum(x["historical_P1_HOLD_HH"] for x in inventories)!=46 or sum(
     x["historical_RH_platform_HOLD_HH"] for x in inventories)!=10 or sum(
     x["source_T_risk_HH"] for x in inventories)!=7:
  raise ValueError("all ten site original 56/7 release risk tally changed")
 report=dict(stage=98,scope="Batch05 direct AD400 readiness; no AD5 trial",
  sites=10,accelerated_years=400,one_submit_chain=True,
  segment_years=5,segment_count=80,
  intended_CIME_STOP_N=5,intended_CIME_REST_N=5,intended_CIME_RESUBMIT=79,
  explicit_separate_AD5_pilot_required=False,
  original_P2P3_HH_dispositioned=1574,
  main_research_approved_HH=1675,main_overlay_sha256=APP_SHA,
  separate_Whs_T_VPD_preview_HH=51,preview_SHA256=PREVIEW_SHA,
  originally_held_P1_HH=46,original_RH_platform_HH=10,
  source_temperature_exception_HH=7,
  original_held_source_events=10,
  processed_source_ERA_proxy_research_HH=sum(proxy_by_site.values()),
  research_proxy_independently_validated_for_production=False,
  original_hold_source_science_closed=False,
  source_T_exception_policy_for_production_approved=False,
  new_complete_DATM_science_approved=False,
  new_site_specific_PFT_soil_surface_approved=False,
  Batch05_independent_CIME_cases_approved=False,
  attempted_job_submission=False,Slurm_submitted=0,
  direct_AD400_submit_permission=False,
  readiness="BLOCKED_PRODUCTION_SCIENCE_FORCING_SURFACE_CIME",
  science_inputs_SHA256={f.name:sha(f) for f in (f84,f86,f89,f90,f97,fruns)},
  checked_original_stage05_CSV_SHA_again=False)
 out.mkdir(exist_ok=False)
 ff=out/"stage98_BATCH05_TEN_SITE_DIRECT_AD400_PREP_INVENTORY.csv"
 fj=out/"stage98_DIRECT_AD400_PREP_PLAN_AND_SCIENCE_RELEASE_GATES.json"
 ft=out/"stage98_DIRECT_AD400_SCIENTIFIC_AND_CIME_READINESS_CHECKLIST.txt"
 csvwrite(ff,CSV_FIELDS,inventories)
 report["outputs_SHA256"]={ff.name:sha(ff)}
 fj.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 ft.write_text("BATCH05 DIRECT AD400, NOT A 5-YEAR PILOT\n\n"+"\n\n".join(CHECKLIST)+
 "\n\nCURRENT SCIENCE RELEASE: BLOCKED; DO NOT SUBMIT OR BUILD PRODUCTION FORCING\n")
 print("STAGE98 SUCCESS | 10-site direct AD400 80x5 design, source/overlay evidence reconciled, model prep inventory READONLY")
 print("STAGE98 DESIGN DIRECT AD400 | STOP_N=5 REST_N=5 RESUBMIT=79; one CIME submit; no standalone AD5 pilot")
 print("STAGE98 HOLD_COUNTS P1=46 PLATFORM=10 T_SOURCE=7 P2P3_REMAIN=0")
 print("STAGE98 ERA_PROXY_RESEARCH_HH",report["processed_source_ERA_proxy_research_HH"],"INDEPENDENTLY_VALIDATED_FOR_MODEL",False)
 print("STAGE98 SITE site year_start year_end original_csv_present DATM_candidates_unverified SURF_candidates_unverified B05_cases")
 for x in inventories:
  print("STAGE98 SITE",x["site"],x["intended_direct_AD400_start"],x["intended_AD400_end"],
    x["source_native_HH_CSV_present"],x["candidate_DATM_file_count_unverified"],
    x["candidate_surface_file_count_unverified"],x["existing_Batch05_named_CIME_case_count"])
 print("STAGE98 RELEASE_GATE",report["readiness"])
 print("STAGE98_REPORTS="+str(out))
 print("STAGE98 READONLY | NO ORIGINAL/QC/HOLD/APPROVED_OVERLAY/DATM/SURFACE/CIME/SLURM WRITES")
if __name__=="__main__":main()

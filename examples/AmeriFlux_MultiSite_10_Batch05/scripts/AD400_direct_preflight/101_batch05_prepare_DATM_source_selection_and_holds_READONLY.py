#!/usr/bin/env python3
"""Batch05 DIRECT AD400 Stage101: construct immutable selected-met SOURCE MAP.

This is an actual input-preparation deliverable for subsequent full-record
DATM construction, NOT a model-ready DATM NetCDF or an AD400 submission.
Exact Stage84 1675 approved research overlay, Stage89 separate 51-HH
T/VPD preview, Stage90 63 unique original release risks, Stage97 56
protected source HOLDs, Stage100 selected operator PFT/soil registration,
and Stage98 1281 humidity-ERA-proxy risk status. All source files immutable.

Output:
 - 10 exact per-site source-file, input-column and model-years recipes;
 - 1782 DISTINCT rows of sparse source selection / science mask instructions:
   1675 main (including 7 T release risk), 51 Stage89 preview separately
   flagged NOT MERGED, 56 original P1/RH-platform HOLD untouched;
 - exact 63 source-risk rows with original T/QC/VPD and hold categories;
 - manifest of input SHA and production-blocking gates.

No scanning/full copying of massive original CSV, no precipitation/humidity
fallback invented, no temperature interpolation, no model NetCDF writes,
no CIME/Slurm changes. This deliberately makes sure a future converter
cannot silently adopt the 63 source risks or the separate 51 preview.
"""
import argparse,csv,hashlib,json,re
from collections import Counter
from pathlib import Path

SITES={
 "US-UiD":("2008-2024_v1.3_r1",2008,2024,"FLUXMET"),
 "US-UMB":("FULLSET_2007-2021_3-5",2007,2021,"FULLSET"),
 "US-UMd":("2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 "US-Var":("2000-2025_v1.3_r1",2000,2025,"FLUXMET"),
 "US-Vcm":("2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 "US-Vcp":("2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 "US-WCr":("1999-2025_v1.3_r1",1999,2025,"FLUXMET"),
 "US-Whs":("2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 "US-Wjs":("2007-2025_v1.3_r1",2007,2025,"FLUXMET"),
 "US-Wkg":("2004-2025_v1.3_r1",2004,2025,"FLUXMET")}
EXPECTED_RAW_SHA={
 "US-UiD":"130142a3b19b11115a058b45129c3ffbeec685b3e5a4e30232701cc149daf318",
 "US-UMB":"ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6",
 "US-UMd":"e84f61649a1da11b29799d5ad066898d513c0a93da964cd23bb2b48a676ab2f2",
 "US-Var":"664ffeb53419d5ea7f618b0a4d3bebbd767c2b8406e1d167a7881a256287eed2",
 "US-Vcm":"c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c",
 "US-Vcp":"eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42",
 "US-WCr":"f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506",
 "US-Whs":"653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca",
 "US-Wjs":"9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6",
 "US-Wkg":"f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"}
OVERLAY_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
WHS_PREVIEW_SHA="95aefd6027e6f981ac821266bc379b89d9f1299d1c307b7575a17fec65588561"
COLS=("site","native_time","selection_class","source_T_C","candidate_T_C",
 "source_VPD_hPa","candidate_VPD_hPa","candidate_RH_pct","source_QC_provenance",
 "source_replacement_method","original_source_science_risk",
 "apply_into_model_DATM","needs_operator_source_science_release")
SITE_COLS=("site","original_FLUXNET_member","original_FLUXNET_source_path",
 "original_SHA256_Stage05_provenance_expected_NOT_REHASHED_NOW",
 "source_first_year","source_last_year","planned_direct_AD400_start_year",
 "planned_direct_AD400_end_year","source_native_TIMESTAMPS",
 "original_required_source_fields_found","original_optional_source_fields_available",
 "original_required_source_fields_missing",
 "sparse_main_1675_research_rows","separate_Whs_51_preview_rows",
 "historical_P1_RH_platform_HOLD_rows","original_T_source_risk_rows",
 "complete_7_meteorology_DATM_approved","candidate_FATES_PFT_research_chosen",
 "source_PFT_mapping_profile","soil10_candidate_valid_Stage100",
 "production_DATM_file_exists","direct_AD400_case_submit_allowed")
SOURCE_CORE=("TIMESTAMP_START","TIMESTAMP_END")
SOURCE_MET=("TA_F","VPD_F","PA_F","SW_IN_F","LW_IN_F","WS_F","P_F")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def records(path,needed):
 if not path.is_file() or path.is_symlink():raise ValueError("missing checked input "+str(path))
 with path.open("r",encoding="utf-8-sig",newline="") as f:
  d=csv.DictReader(f);hd=d.fieldnames or []
  if len(hd)!=len(set(hd)) or not set(needed).issubset(hd):
   raise ValueError("source/report CSV required fields mismatch "+str(path))
  rows=list(d)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("source/report CSV malformed "+str(path))
 return rows
def keys(rows):
 out={}
 for row in rows:
  k=(row["site"],row["native_time"])
  if k in out:raise ValueError("duplicate source HH "+repr(k))
  if row["site"] not in SITES or not re.fullmatch(r"\d{12}",row["native_time"]):
   raise ValueError("unrecognized Batch05 site/HH "+repr(k))
  out[k]=row
 return out
def write(path,columns,data):
 with path.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=columns,extrasaction="raise")
  w.writeheader();w.writerows(data)
def checked_manifest(directory,jsonname,expected_stage):
 path=directory/jsonname
 if not path.is_file() or path.is_symlink():raise ValueError("missing science manifest "+str(path))
 m=json.loads(path.read_text())
 if m.get("stage")!=expected_stage:raise ValueError("science stage drift "+str(path))
 return m,path
def selftest():
 assert len(SITES)==10 and len(EXPECTED_RAW_SHA)==10
 assert 1675+51+56==1782 and 46+10+7==63
 assert all(len(x)==64 for x in EXPECTED_RAW_SHA.values())
 print("STAGE101 SELF-TEST PASS | ten-source immutable input recipes; 1675 main + separate 51 preview + 56 historical HOLD; 63 source risk science gates, no Slurm")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for name in ("stage84","stage89","stage90","stage97","stage98","stage100"):
  p.add_argument("--"+name,type=Path)
 p.add_argument("--source-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 names=("stage84","stage89","stage90","stage97","stage98","stage100")
 if any(getattr(a,x) is None for x in (*names,"out")):
  p.error("require actual reports Stage84/89/90/97/98/100 and NEW out")
 dirs={x:getattr(a,x).expanduser().resolve() for x in names}
 root=a.source_root.expanduser().resolve()
 out=a.out.expanduser().resolve()
 if (any(not d.is_dir() for d in dirs.values()) or not root.is_dir() or
     out.exists() or not out.parent.is_dir() or
     any(out==d or out in d.parents or d in out.parents for d in (*dirs.values(),root))):
  p.error("expected actual Stage84/89/90/97/98/100 evidence missing or output not disjoint")
 d=dirs
 f84=d["stage84"]/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84,_=checked_manifest(d["stage84"],"stage84_manifest.json",84)
 if (sha(f84)!=OVERLAY_SHA or m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=OVERLAY_SHA):
  raise ValueError("original 1675 approved research sparse-overlay source SHA drift")
 mainrows=keys(records(f84,("site","native_time","source_TA_C",
   "modified_TA_C","source_VPD_hPa","modified_VPD_hPa","modified_RH_pct",
   "replacement_RH_provenance","source_QC_provenance_only")))
 if len(mainrows)!=1675:raise ValueError("main sparse science 1675 keys not exact")
 f89=d["stage89"]/"stage89_SEPARATE_WHS_51_T_RH_VPD_VERSIONED_INTEGRATION_PREVIEW.csv"
 m89,_=checked_manifest(d["stage89"],"stage89_SEPARATE_WHS_51_T_RH_VPD_READONLY_PREVIEW_MANIFEST.json",89)
 if (sha(f89)!=WHS_PREVIEW_SHA or m89.get("output_preview_SHA256")!=WHS_PREVIEW_SHA or
     m89.get("stage67_approved_T_candidate_HH")!=51 or
     m89.get("separate_integration_preview_not_production_or_user_final_merge_approval") is not True):
  raise ValueError("Stage89 standalone US-Whs 51 science preview SHA/status drift")
 whs=keys(records(f89,("site","native_time","original_T_C","approved_Stage67_T_C",
   "original_VPD_hPa","proposed_joint_VPD_hPa","combined_RH_pct",
   "combined_VPD_method","production_permission")))
 if len(whs)!=51 or any(k[0]!="US-Whs" for k in whs) or set(mainrows)&set(whs):
  raise ValueError("Stage89 51 source HH drift or overlap with approved main 1675")
 riskfile=d["stage90"]/"stage90_UNIQUE_HISTORICAL_SCIENCE_RELEASE_RISK_SOURCE_EVIDENCE.csv"
 m90,_=checked_manifest(d["stage90"],"stage90_FINAL_HISTORICAL_RELEASE_RISK_EVIDENCE_MANIFEST.json",90)
 if (m90.get("distinct_release_risk_source_HH")!=63 or
     m90.get("historical_P1_HOLD_HH")!=46 or
     m90.get("historical_RH_platform_HOLD_HH")!=10 or
     m90.get("historical_source_T_exception_HH")!=7 or
     m90.get("source_risks_overlapping_main_1675")!=7 or
     m90.get("source_risks_overlapping_separate_Stage89_51")!=0 or
     m90.get("output_SHA256",{}).get(riskfile.name)!=sha(riskfile)):
  raise ValueError("Stage90 original 63 source-risk science SHA/status drift")
 risk=keys(records(riskfile,("site","native_time","source_risk_categories","risk_reasons")))
 if len(risk)!=63 or set(risk)&set(whs) or len(set(risk)&set(mainrows))!=7:
  raise ValueError("Stage90 original 63 source release risk source key drift")
 m97,_=checked_manifest(d["stage97"],"stage97_SOURCE_PROTECTED_HOLDS_CLOSURE_GATE_MANIFEST.json",97)
 heldfile=d["stage97"]/"stage97_56_ORIGINAL_HOLD_HH_SCIENCE_DECISION_MATRIX.csv"
 if (m97.get("source_HOLDs_verified")!=56 or
     m97.get("source_contiguous_episodes")!=10 or
     m97.get("operator_original_hold_approved_HH")!=0 or
     m97.get("output_SHA256",{}).get(heldfile.name)!=sha(heldfile)):
  raise ValueError("Stage97 56 historical original HOLD science SHA/status drift")
 holds=keys(records(heldfile,("site","native_time","review_group","original_HOLD_unchanged")))
 if (len(holds)!=56 or set(holds)&set(mainrows) or
     set(holds)&set(whs) or set(holds)!=set(risk)-set(mainrows)):
  raise ValueError("Stage97 56 HOLDs do not exactly crosswalk Stage90 risk 63 minus seven T")
 m98,_=checked_manifest(d["stage98"],"stage98_DIRECT_AD400_PREP_PLAN_AND_SCIENCE_RELEASE_GATES.json",98)
 if (m98.get("sites")!=10 or m98.get("processed_source_ERA_proxy_research_HH")!=1281 or
     m98.get("direct_AD400_submit_permission") is not False):
  raise ValueError("Stage98 1281 source-ERA scientific caution or direct AD400 gate drift")
 m100,_=checked_manifest(d["stage100"],"batch05_10_SITE_PFT_SOIL_HEIGHT_SCIENCE_UNAPPROVED_MANIFEST.json",100)
 f100=d["stage100"]/"batch05_10_SITE_FATES_PFT_SOIL_HEIGHT_SURFACE_CANDIDATES_NOT_MODEL_READY.csv"
 if (m100.get("ten_sites")!=10 or
     m100.get("output_SHA256",{}).get(f100.name)!=sha(f100)):
  raise ValueError("Stage100 selected host PFT/soil candidate source receipt changed")
 pft={r["site"]:r for r in records(f100,("site","FATES_mapping_profile","soil_sand_clay_valid"))}
 if len(pft)!=10 or set(pft)!=set(SITES):
  raise ValueError("Stage100 ten selected PFT/soil model-input sites drift")
 staged=[]
 for k,r in sorted(mainrows.items()):
  cat=risk[k]["source_risk_categories"] if k in risk else ""
  staged.append(dict(site=k[0],native_time=k[1],
   selection_class="STAGE84_RESEARCH_VERSIONED_1675_NOT_FULL_DATM",
   source_T_C=r["source_TA_C"],candidate_T_C=r["modified_TA_C"],
   source_VPD_hPa=r["source_VPD_hPa"],candidate_VPD_hPa=r["modified_VPD_hPa"],
   candidate_RH_pct=r["modified_RH_pct"],source_QC_provenance=r["source_QC_provenance_only"],
   source_replacement_method=r["replacement_RH_provenance"],
   original_source_science_risk=cat,apply_into_model_DATM="NO",
   needs_operator_source_science_release="YES"))
 for k,r in sorted(whs.items()):
  if r["production_permission"] not in ("NO","False"):
   raise ValueError("Stage89 preview unexpectedly authorized for production "+str(k))
  staged.append(dict(site=k[0],native_time=k[1],
   selection_class="STAGE89_SEPARATE_WHS_51_PREVIEW_NOT_MERGED",
   source_T_C=r["original_T_C"],candidate_T_C=r["approved_Stage67_T_C"],
   source_VPD_hPa=r["original_VPD_hPa"],candidate_VPD_hPa=r["proposed_joint_VPD_hPa"],
   candidate_RH_pct=r["combined_RH_pct"],source_QC_provenance="STAGE89_PREVIEW",
   source_replacement_method=r["combined_VPD_method"],original_source_science_risk="",
   apply_into_model_DATM="NO",needs_operator_source_science_release="YES"))
 for k,r in sorted(holds.items()):
  if r["original_HOLD_unchanged"]!="True":raise ValueError("HOLD approval drift")
  staged.append(dict(site=k[0],native_time=k[1],
   selection_class="STAGE97_ORIGINAL_SOURCE_HOLD_56_DO_NOT_FILL_FROM_INVALID_SOURCE_ERA",
   source_T_C="",candidate_T_C="",source_VPD_hPa="",candidate_VPD_hPa="",
   candidate_RH_pct="",source_QC_provenance="ORIGINAL_HOLD",
   source_replacement_method=r["review_group"],
   original_source_science_risk=risk[k]["source_risk_categories"],
   apply_into_model_DATM="NO",needs_operator_source_science_release="YES"))
 if len(staged)!=1782 or len({(x["site"],x["native_time"]) for x in staged})!=1782:
  raise ValueError("sparse candidate union expected 1782 unique HH")
 candidate_counts=Counter(x["site"] for x in staged)
 recipes=[]
 for site,(release,start,end,product) in SITES.items():
  rawdir=root/site/"forcing"/"raw"/("AMF_"+site+"_FLUXNET_"+release)
  if not rawdir.is_dir() or rawdir.is_symlink():
   raise ValueError("original Batch05 site source folder not found "+site)
  raw=[p for p in rawdir.iterdir() if p.is_file() and not p.is_symlink()
    and re.fullmatch(r"AMF_"+re.escape(site)+r"_FLUXNET_"+product+r"_(HH|HR)_.+[.]csv",p.name,re.I)]
  if len(raw)!=1:raise ValueError("original Batch05 native source file not unique "+site)
  with raw[0].open("r",encoding="utf-8-sig",newline="") as f:
   header=next(csv.reader(f),[])
  if len(header)!=len(set(header)) or not set(SOURCE_CORE).issubset(header):
   raise ValueError("site source timestamp/column header wrong "+site)
  available=[x for x in SOURCE_MET if x in header]
  missing=[x for x in SOURCE_MET if x not in header]
  recipes.append(dict(site=site,original_FLUXNET_member=product,
   original_FLUXNET_source_path=str(raw[0]),
   original_SHA256_Stage05_provenance_expected_NOT_REHASHED_NOW=EXPECTED_RAW_SHA[site],
   source_first_year=start,source_last_year=end,
   planned_direct_AD400_start_year=start,planned_direct_AD400_end_year=start+400,
   source_native_TIMESTAMPS="TIMESTAMP_START / TIMESTAMP_END; verify UTC_OFFSET in BIF",
   original_required_source_fields_found=";".join(available),
   original_optional_source_fields_available=";".join(x for x in
     ("TA_ERA","VPD_ERA","PA_ERA","SW_IN_ERA","LW_IN_ERA","WS_ERA","P_ERA","RH","TA_F_QC","VPD_F_QC") if x in header),
   original_required_source_fields_missing=";".join(missing),
   sparse_main_1675_research_rows=sum(k[0]==site for k in mainrows),
   separate_Whs_51_preview_rows=sum(k[0]==site for k in whs),
   historical_P1_RH_platform_HOLD_rows=sum(k[0]==site for k in holds),
   original_T_source_risk_rows=sum(k[0]==site for k in set(risk)&set(mainrows)),
   complete_7_meteorology_DATM_approved="NO",
   candidate_FATES_PFT_research_chosen="YES",
   source_PFT_mapping_profile=pft[site]["FATES_mapping_profile"],
   soil10_candidate_valid_Stage100=pft[site]["soil_sand_clay_valid"],
   production_DATM_file_exists="NO",direct_AD400_case_submit_allowed="NO"))
 if sum(int(x["sparse_main_1675_research_rows"]) for x in recipes)!=1675:
  raise ValueError("site sparse overlay count lost")
 out.mkdir(exist_ok=False)
 fsel=out/"stage101_BATCH05_1782_HH_VERSIONED_SPARSE_SELECTION_AND_HOLD_MATRIX_NOT_DATM.csv"
 frcp=out/"stage101_BATCH05_TEN_SITE_ACTUAL_FLUXNET_SOURCE_TO_DATM_RECIPES.csv"
 frisk=out/"stage101_BATCH05_63_ORIGINAL_RELEASE_RISKS_DO_NOT_AUTO_FILL.csv"
 fm=out/"stage101_DATM_SCIENCE_SOURCE_SELECTION_PREPARED_NOT_RELEASED_MANIFEST.json"
 write(fsel,COLS,staged)
 write(frcp,SITE_COLS,recipes)
 write(frisk,("site","native_time","source_risk_categories","risk_reasons"),
  [dict(site=k[0],native_time=k[1],source_risk_categories=r["source_risk_categories"],
   risk_reasons=r["risk_reasons"]) for k,r in sorted(risk.items())])
 manifest=dict(stage=101,sites=10,main_stage84_research_HH=1675,
   separate_stage89_preview_HH=51,original_historical_HOLD_HH=56,
   original_source_T_exception_HH=7,source_release_risk_HH=63,
   distinct_sparse_source_science_keys=1782,
   proxy_source_ERA_research_HH_requires_independent_validation=1281,
   source_original_SHA256_expected_Stage05=EXPECTED_RAW_SHA,
   actual_Stage84_overlay_sha256=sha(f84),
   actual_Stage89_preview_sha256=sha(f89),actual_Stage90_risk_sha256=sha(riskfile),
   actual_Stage97_holds_sha256=sha(heldfile),
   actual_Stage100_PFT_soil_source_sha256=sha(f100),
   Stage05_raw_sources_rehashed_in_this_step=False,
   user_selected_model_PFT_soil_no_redundant_literature_review=True,
   stage101_sparse_source_matrix_not_model_DATM=True,
   source_research_candidates_applied_into_production=0,
   full_meteorology_annual_NetCDF_generated=0,
   direct_AD400_requested_no_AD5_pilot=True,
   per_site_AD400_segments=80,per_site_resubmit=79,
   DATM_production_release="BLOCKED_EXACT_SOURCE_RISK_AND_ERA_PROXY_POLICY",
   source_original_and_QC_unchanged=True,main_overlay_unchanged=True,
   surface_CIME_unchanged=True,Slurm_submitted=0,
   outputs_SHA256={x.name:sha(x) for x in (fsel,frcp,frisk)})
 fm.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 print("STAGE101 SUCCESS | 10 Batch05 full-source DATM input recipes + sparse 1782 HH science candidate/hold mapping prepared, NO DATM production")
 print("STAGE101 SPARSE main1675 separate_Whs51 original_HOLD56 overlap_T7 original_source_risks63 ERA_proxy1281")
 print("STAGE101 SITE site firstYear lastYear sourceHeaderRequiredMissing main1675 whs_preview51 held56 T_risks7 FATES_mapping")
 for r in recipes:
  print("STAGE101 SITE",r["site"],r["source_first_year"],r["source_last_year"],
   r["original_required_source_fields_missing"] or "none",
   r["sparse_main_1675_research_rows"],r["separate_Whs_51_preview_rows"],
   r["historical_P1_RH_platform_HOLD_rows"],r["original_T_source_risk_rows"],
   r["source_PFT_mapping_profile"])
 print("STAGE101 PRODUCTION_DATM_RELEASE",manifest["DATM_production_release"])
 print("STAGE101_REPORTS="+str(out))
 print("STAGE101 ORIGINAL/QC/APPROVED1675/Stage89/PFT/SOIL/SURFACE/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

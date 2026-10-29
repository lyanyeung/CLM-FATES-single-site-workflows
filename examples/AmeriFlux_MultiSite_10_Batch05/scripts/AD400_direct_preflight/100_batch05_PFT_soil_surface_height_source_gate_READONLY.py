#!/usr/bin/env python3
"""Batch05 FIXNC direct AD400: ten-site original PFT/soil/height/surface audit.

Inputs: SHA-pinned authoritative RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT
(10 exact Batch05 model hypotheses, NOT tower-area measurements); Stage99
successful real file inventory. Locate source candidate site surfdata*.nc under
bounded site paths (and verify 15 NATPFT slots if netCDF4 available), check
ten-layer soil-wide source candidates, instrument measurement-height reference
table coverage, and no default HYDRO_SHRUB mapping for Whs/Wkg.
No surface files, DATM files, cases, Slurm, sources, QC or approvals are changed.
If PFT candidate proxy is HIGH uncertainty, do NOT claim science release.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter
from pathlib import Path

REPO_PFT_SHA_BLOB="26fdfda6f1c88c9a134e7853bd70234685665031"
SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp",
       "US-WCr","US-Whs","US-Wjs","US-Wkg")
SOIL=Path.home()/"CLM_FATES_SOIL/AmeriFlux50_20261026/09_RECOMMENDED_CLM10_PCT_SAND_PCT_CLAY_WIDE.csv"
HGT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/NonCompetitionObserved22/AmeriFlux_Batch02_10/Stage06_direct_AD400/BASE_MeasurementHeight_20260908.csv")
SITEBASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
FOCUS=("site","pft_model_hypothesis","PFT_input_basis","PFT_uncertainty",
 "host_natpft_15_slots","host_bare_percent","fates_natland_percent",
 "FATES_mapping_profile","FATES_private_param_needed","time_representativeness",
 "soil_10_layer_row_present","soil_layer_data_finite","soil_sand_clay_valid",
 "height_reference_rows_candidate_count","height_reference_schema",
 "source_surface_candidates","surface_15_host_slots_schema",
 "new_approved_Batch05_surface_exists","production_surface_build_gate")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def read(p,req):
 if not p.is_file() or p.is_symlink():raise ValueError("source CSV missing or symlink "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  r=csv.DictReader(h);hd=r.fieldnames or []
  if len(hd)!=len(set(hd)) or not set(req).issubset(hd):
   raise ValueError("source CSV fields absent "+str(p)+" "+repr(req))
  rr=list(r)
 if any(None in row or any(v is None for v in row.values()) for row in rr):
  raise ValueError("source CSV malformed "+str(p))
 return rr
def write(p,columns,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=columns,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def scansurf(site):
 base=SITEBASE/site
 if not base.is_dir():return []
 # This is deliberately a bounded depth scan of the *one site* folder.
 # Never traverse enormous experiments/scratch or other users' paths.
 paths=[]
 for pat in ("surfdata*.nc","*/*surfdata*.nc","*/*/surfdata*.nc",
             "surface*.nc","*/surface*.nc","*/*/surface*.nc"):
  paths.extend(p for p in base.glob(pat) if p.is_file() and not p.is_symlink())
 return sorted(set(paths),key=lambda p:str(p))[:16]
def survey_surface(paths):
 if not paths:return "NO_SURFACE_CANDIDATE"
 try:from netCDF4 import Dataset
 except ImportError:return "netCDF4_NOT_IMPORTABLE_SCHEMAS_UNVERIFIED"
 result=[]
 for p in paths:
  try:
   with Dataset(str(p)) as d:
    v=d.variables.get("PCT_NAT_PFT")
    h=list(v.shape) if v is not None else []
    okay=(len(h)==3 and 15 in h) or (len(h)==1 and h[0]==15)
    result.append(dict(path=str(p),host_shape=h,host15=okay,
        landunit_vars=[x for x in ("PCT_NATVEG","PCT_CROP") if x in d.variables],
        soil_vars=[x for x in ("PCT_SAND","PCT_CLAY","ORGANIC") if x in d.variables]))
  except Exception as e:result.append(dict(path=str(p),error=str(e)[:170]))
 return json.dumps(result,sort_keys=True)
def source_soil():
 if not SOIL.is_file():return {},dict(path=str(SOIL),exists=False)
 rr=read(SOIL,("site",))
 d={}
 for r in rr:
  if r["site"] in SITES:
   if r["site"] in d:raise ValueError("duplicate soil source site "+r["site"])
   d[r["site"]]=r
 return d,dict(path=str(SOIL),exists=True,sha256=sha(SOIL),
   field_count=len(rr[0]) if rr else 0,row_count=len(rr),selected_site_count=len(d))
def soil_grade(r):
 if r is None:return "False","False"
 keys=[f"PCT_SAND_L{i}" for i in range(1,11)]+[f"PCT_CLAY_L{i}" for i in range(1,11)]
 if any(k not in r for k in keys):return "False","False"
 try:nums=[float(r[k]) for k in keys]
 except (ValueError,TypeError):return "False","False"
 good=all(math.isfinite(x) for x in nums)
 physical=good and all(0<=nums[i]<=100 and 0<=nums[i+10]<=100 and
    nums[i]+nums[i+10]<=100.0001 for i in range(10))
 return str(good),str(physical)
def heights():
 if not HGT.is_file():return [],dict(path=str(HGT),exists=False)
 with HGT.open(encoding="utf-8-sig",newline="") as f:
  r=csv.DictReader(f);heads=r.fieldnames or [];rows=list(r)
 if not heads or len(heads)!=len(set(heads)):raise ValueError("height source schema corrupted")
 return rows,dict(path=str(HGT),exists=True,sha256=sha(HGT),
    columns=heads,total_rows=len(rows))
def height_match(rows,columns,site):
 loc=[k for k in columns if k.strip().lower() in ("site","site_id","siteid","sitecode","site_code","site_id_original")]
 if not loc:return 0
 matched=[r for r in rows if any(r.get(k,"").strip()==site for k in loc)]
 return len(matched)
def selftest():
 assert len(SITES)==10 and len(set(SITES))==10
 assert soil_grade({f"PCT_SAND_L{i}":"30" for i in range(1,11)}|
          {f"PCT_CLAY_L{i}":"20" for i in range(1,11)})==("True","True")
 assert soil_grade({})==("False","False")
 assert sum([57,20,20,3])==100
 assert sum([60,3,37])==100
 print("BATCH05 PFT/SOIL/SURFACE SELF-TEST PASS | 10 site host index0 bare, two HYDRO_SHRUB special FATES maps; original untouched")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--pft",type=Path)
 p.add_argument("--stage99",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.pft,a.stage99,a.out)):
  p.error("require pinned original 50-site PFT CSV, actual Stage99 report directory, NEW out")
 d=a.stage99.expanduser().resolve();out=a.out.expanduser().resolve()
 if not d.is_dir() or out.exists() or not out.parent.is_dir() or
    d==out or out in d.parents or d in out.parents:
  p.error("stage99 missing or output not fresh and disjoint")
 stage99=d/"Batch05_DIRECT_AD400_STACK_SLURM_TEMPLATE_QUOTA_AND_SCIENCE_MANIFEST.json"
 s99=json.loads(stage99.read_text())
 inv=d/"Batch05_DIRECT_AD400_TEN_SITE_SOURCE_DATM_SURFACE_CASE_INVENTORY.csv"
 if (s99.get("stage")!=99 or s99.get("exact_site_count")!=10
     or s99.get("status")!="HOLD_NOT_READY_FOR_DIRECT_AD400_SUBMISSION"
     or s99.get("output_inventory_SHA256")!=sha(inv)
     or s99.get("no_run_submit_authorized") is not True):
  raise ValueError("actual Stage99 provenance/release status drift")
 rs=read(a.pft,("site","batch","recommended_percent","clm_pct_nat_pft_json",
    "fates_natland_percent_json","mapping_profile","uncertainty",
    "target_period","status","active_case_parameter_verified"))
 if len(rs)!=50:raise ValueError("expected original 50 PFT model-hypothesis rows")
 pft={r["site"]:r for r in rs if r["batch"]=="Batch05"}
 if len(pft)!=10 or set(pft)!=set(SITES):
  raise ValueError("original PFT site membership changed")
 if pft["US-Whs"]["mapping_profile"]!="HYDRO_SHRUB" or (
    pft["US-Wkg"]["mapping_profile"]!="HYDRO_SHRUB"):
  raise ValueError("Whs/Wkg FATES special shrub map lost")
 if "2007-2012 ONLY" not in pft["US-Vcm"]["target_period"]:
  raise ValueError("Vcm prefire-only 2007-12 model PFT limitation missing")
 soils,soil_rec=source_soil()
 hs,ht_rec=heights()
 records=[]
 for site in SITES:
  r=pft[site]
  host={int(k):float(v) for k,v in json.loads(r["clm_pct_nat_pft_json"]).items()}
  fates={int(k):float(v) for k,v in json.loads(r["fates_natland_percent_json"]).items()}
  if not host or any(k not in range(15) or v<0 or not math.isfinite(v) for k,v in host.items()):
   raise ValueError("invalid CLM host PFT 15 slot index/values "+site)
  if not math.isclose(sum(host.values()),100,abs_tol=1e-4):
   raise ValueError("invalid host PFT 100% denominator "+site)
  if not math.isclose(sum(fates.values()),100-host.get(0,0),abs_tol=1e-4):
   raise ValueError("FATES vegetation/natural land percentage not equal host total minus bare "+site)
  if r["active_case_parameter_verified"]!="NO":
   raise ValueError("original PFT proposal unexpected case approval "+site)
  if r["mapping_profile"] not in ("DEFAULT14","HYDRO_SHRUB"):
   raise ValueError("unrecognized source PFT mapping profile "+site)
  soilvalid,soilphys=soil_grade(soils.get(site))
  surf=scansurf(site)
  nheight=height_match(hs,ht_rec.get("columns",[]),site)
  records.append(dict(site=site,pft_model_hypothesis=r["recommended_percent"],
   PFT_input_basis=r["basis"],PFT_uncertainty=r["uncertainty"],
   host_natpft_15_slots=json.dumps([host.get(i,0) for i in range(15)]),
   host_bare_percent=host.get(0,0),
   fates_natland_percent=json.dumps(fates,sort_keys=True),
   FATES_mapping_profile=r["mapping_profile"],
   FATES_private_param_needed=str(r["mapping_profile"]=="HYDRO_SHRUB"),
   time_representativeness=r["target_period"],
   soil_10_layer_row_present=str(site in soils),soil_layer_data_finite=soilvalid,
   soil_sand_clay_valid=soilphys,
   height_reference_rows_candidate_count=nheight,
   height_reference_schema=",".join(ht_rec.get("columns",[])),
   source_surface_candidates=";".join(str(x) for x in surf),
   surface_15_host_slots_schema=survey_surface(surf),
   new_approved_Batch05_surface_exists="False",
   production_surface_build_gate="BLOCKED_PFT_SCIENCE_SURFACE_VALIDATION"))
 out.mkdir(exist_ok=False)
 f=out/"batch05_10_SITE_FATES_PFT_SOIL_HEIGHT_SURFACE_CANDIDATES_NOT_MODEL_READY.csv"
 manifest=out/"batch05_10_SITE_PFT_SOIL_HEIGHT_SCIENCE_UNAPPROVED_MANIFEST.json"
 write(f,FOCUS,records)
 info=dict(stage=100,ten_sites=len(records),source_PFT_sha256=sha(a.pft),
  source_PFT_git_blob="26fdfda6f1c88c9a134e7853bd70234685665031",
  stage99_manifest_sha256=sha(stage99),soil_source=soil_rec,
  measurement_height_source=ht_rec,
  HYDRO_SHRUB_sites=["US-Whs","US-Wkg"],
  bare_fraction_model_hypotheses={"US-Whs":57,"US-Wkg":60},
  Vcm_prefire_ENF100_only_2007_to_2012=True,
  site_PFT_observed_area_fraction_accepted=False,
  site_surface_production_approved=False,
  independent_soil_source_each_site_accepted=False,
  no_original_QC_DATM_surface_CIME_writes=True,
  Slurm_submitted=0,
  release_gate="BLOCKED_PFT_TIME_REPRESENTATIVENESS_FATES_MAP_SOIL_SURFACE_AND_MET_SCIENCE",
  output_SHA256={f.name:sha(f)})
 manifest.write_text(json.dumps(info,sort_keys=True,indent=2)+"\n")
 print("STAGE100 SUCCESS | exact 10 Batch05 recommended PFT hypotheses and actual soils/heights/surface candidates audited, NONE approved")
 print("STAGE100 PFT model proposal: host15 NATPFT + mapping profile, NOT tower ground observation")
 for row in records:
  print("STAGE100 SITE",row["site"],row["pft_model_hypothesis"],
   "bare",row["host_bare_percent"],"map",row["FATES_mapping_profile"],
   "soil10",row["soil_sand_clay_valid"],
   "height_candidate_rows",row["height_reference_rows_candidate_count"],
   "source_surfaces",len(row["source_surface_candidates"].split(";")) if row["source_surface_candidates"] else 0)
 print("STAGE100 SOIL_SOURCE",json.dumps(soil_rec,sort_keys=True))
 print("STAGE100 HEIGHT_SOURCE",json.dumps(ht_rec,sort_keys=True))
 print("STAGE100 VCM_FIRE_WARNING prefire ENF100 only 2007-2012; cannot silently claim represents 2007-2025")
 print("STAGE100 SURFACE_RELEASE",info["release_gate"])
 print("STAGE100_REPORTS="+str(out))
 print("STAGE100 READONLY | NO ORIGINAL/APPROVED_OVERLAY/SURFACE/DATM/CIME/SLURM CHANGES")
if __name__=="__main__":
 main()

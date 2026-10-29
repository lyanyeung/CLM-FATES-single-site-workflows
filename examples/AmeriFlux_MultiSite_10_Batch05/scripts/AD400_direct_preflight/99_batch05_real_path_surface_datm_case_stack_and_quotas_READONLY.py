#!/usr/bin/env python3
"""Batch05 ten-site direct AD400: deeper HPC prep audit, no model operations.

Cross-references proven 2026 Batch01/Batch02/Batch03/Batch04 IRIDIS6 lessons:
  * stack soft >=65536 KiB and Slurm STACK/ALL propagation (same submit process
    must call batch05_direct_ad400_stack_guard.require_for_submission())
  * 80 x 5-year segments, RESUBMIT=79, first run startup, FATES AD state=2
  * no pilot AD5, no Normal; a direct 400y case should submit exactly ONCE
  * actual selected DATM TBOT QBOT PSRF FSDS FLDS WIND PRECTmms annual netCDF,
    source clock/local-to-UTC/no-leap/time-center, humidity QA, ZBOT/PTS
  * measured PFT/bare/soil and exact FATES PFT mapping, original ground truth
  * archive/restart chain, job dependencies, Slurm request, disk/inode limits
  * duplicate case/submission protections, source/approved SHA provenance

This inventory reads historical Stage98/90/97 successful manifests and local
HPC config/files, searches possible site-specific assets WITHOUT declaring them
scientifically valid. No forcing, source, surface, case, XML, jobs are changed.
Outputs only a NEW report folder under HOME.

STAGE98's zero count only means none found at its chosen locations; do not
infer globally absent DATM/surface from it.
"""
import argparse,csv,hashlib,json,os,re,resource,subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import batch05_direct_ad400_stack_guard as stack

B=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
SOURCE=B/"sites/MY_EC_SITE"
CASES=B/"cases"
OUTPUTS=Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
RESEARCH=B/"experiments/AmeriFlux_MultiSite_10_Batch05"
EXPECTED_SITES={
 "US-UiD":2008,"US-UMB":2007,"US-UMd":2007,"US-Var":2000,
 "US-Vcm":2007,"US-Vcp":2007,"US-WCr":1999,"US-Whs":2007,
 "US-Wjs":2007,"US-Wkg":2004}
REQUIRED_MET=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms")
SOURCE_MET=("TA_F","TA_F_QC","VPD_F","VPD_F_QC",
 "PA_F","SW_IN_F","LW_IN_F","WS_F","P_F")
FIELDS=("site","source_start","AD400_end","source_csv_path",
 "source_raw_has_REQUIRED_source_met_columns","source_raw_missing_source_fields",
 "raw_source_SHA_verified_prior_Stage90","possible_DATM_NC_paths_unverified",
 "possible_surface_NC_paths_unverified","possible_Batch05_CIME_cases_unverified",
 "cross_batch_templates_ONLY","proven_Batch05_DATM","proven_Batch05_surface",
 "proven_Batch05_CIME","ready_for_submit")
TEMPLATE_NAMES=("CA-Ca3_AMF_FIXNC_AD400_UTC_V2_PTS_AD5",
 "CA-TP4_AMF_FIXNC_AD400_UTC_V3_PTS_AD5",
 "IT-Noe_B02_FIXNC_GPPNPP_HISTFIX_AD400")
PATH_HINTS=(
 "source FATES/CTSM repository /iridisfs/scratch/ly3n24/CLM_FATES/CTSM",
 "independent prior CASE template is reference ONLY; never alter or reuse actual jobs",
 "input data per-site point surface with correct PCT_NAT_PFT, PCT_NATVEG/PCT_CROP, PCT_SAND/PCT_CLAY and ORGANIC",
 "soil CLM10: $HOME/CLM_FATES_SOIL/AmeriFlux50_20261026*/09_RECOMMENDED_CLM10_PCT_SAND_PCT_CLAY_WIDE.csv",
 "tower ZBOT measurement heights: experiments/NonCompetitionObserved22/AmeriFlux_Batch02_10/Stage06_direct_AD400/BASE_MeasurementHeight_20260908.csv",
 "CO2 source: experiments/NonCompetitionObserved22/AmeriFlux_Batch02_10/Stage06_direct_AD400/co2_annmean_gl.csv",
 "DATM: selected source chemistry and meteorology TA/PA/VPD/WS/P/SW/LW -> TBOT/QBOT/PSRF/WIND/PRECTmms/FSDS/FLDS",
 "DATM: correct NO_LEAP 365-day annual timestep/UTC and source local offset; verify source year cycle and timestamps",
 "forcing: 1281 source-product ERA humidity-proxy research HH still not independently released",
 "science: 35 invalid source P1 QC2 RH cannot be replaced with identical source processed-ERA RH",
 "science: 10 low-positive P1 and one donor-supported P1; 10 RH plateaus; seven source-T decision policy",
 "build: FATES fixed-biogeography no-competition, exact FATES parameter map and private spinup_state 2 namelist consistency",
 "CIME: RUN_TYPE startup, CLM_ACCELERATED_SPINUP on, STOP_N 5 REST_N 5 RESUBMIT 79, RESUBMIT_SETS_CONTINUE_RUN TRUE",
 "jobs: one MPI task, srun --mpi=pmix; audit 8G memory + actual 5yr runtime before setting walltime; no unverified time assumptions",
 "archive: DOUT_S TRUE, archived CLM/DATM/CPL restarts and rpointers, 80 segments, archive dependencies",
 "stack: >=65536 KiB in the SAME Python subprocess that calls case.submit; target 300000 KiB if needed; never lower high/unlimited",
 "Slurm: STACK or ALL propagation; CIME automatic resubmit may regenerate namelist without persistent --skip-preview-namelist",
 "submission: one submission ATTEMPTED ledger first, never retry uncertain case.submit, avoid duplicated site case names",
 "scratch/RFS: check storage capacity AND inode quota before creating many annual NetCDF and job logs")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def load(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("required evidence missing "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  rr=csv.DictReader(h);cols=rr.fieldnames or []
  if len(cols)!=len(set(cols)) or not set(required).issubset(cols):
   raise ValueError("evidence CSV schema drift "+str(p))
  rows=list(rr)
 if any(None in row or any(v is None for v in row.values()) for row in rows):
  raise ValueError("malformed evidence CSV "+str(p))
 return rows
def write(p,fields,rows):
 with p.open("x",encoding="utf-8",newline="") as h:
  w=csv.DictWriter(h,fieldnames=fields,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def xml(path):
 out={}
 if not path.is_file():return out
 try:
  tree=ET.parse(path)
  for x in tree.getroot().iter("entry"):
   k=x.get("id");v=x.get("value")
   if k:out[k]=v
 except (ET.ParseError,OSError):out["_ERROR"]="XML_NOT_PARSEABLE"
 return out
def peek_first_line(p):
 if not p.is_file() or p.is_symlink():return []
 with p.open("r",encoding="utf-8-sig",newline="") as stream:
  return next(csv.reader(stream),[])
def children_nc(root,limit=120):
 if not root.is_dir() or root.is_symlink():return []
 out=[]
 # Bounded 0,1,2 directory levels. Prevent 600000-inode filesystem walks.
 levels=[root]
 for depth in range(3):
  next_levels=[]
  for parent in levels:
   try:
    for ent in os.scandir(parent):
     if ent.name.startswith(".") or ent.is_symlink():continue
     if ent.is_file(follow_symlinks=False) and ent.name.endswith(".nc"):
      out.append(ent.path)
     elif ent.is_dir(follow_symlinks=False) and depth<2:
      next_levels.append(Path(ent.path))
     if len(out)>=limit:return sorted(out)
   except OSError:continue
  levels=next_levels
  if len(levels)>150:break
 return sorted(out)
def quota(root):
 try:
  v=os.statvfs(root)
  return dict(path=str(root),blocks_available=v.f_bavail,
    block_size_bytes=v.f_frsize,free_inodes=v.f_favail,
    total_inodes=v.f_files)
 except OSError as e:return dict(path=str(root),error=str(e))
def live_preflight():
 d={}
 try:
  d["stack"]=stack.inspect_stack(raise_current_soft=False)
 except Exception as e:d["stack_error"]=str(e)
 try:
  d["slurm"]=stack.slurm_propagation()
 except Exception as e:d["slurm_error"]=str(e)
 for name,cmd in (
    ("sinfo",["sinfo","-h","-o","%P %a %l %D"]),
    ("squeue",["squeue","-h","-u","ly3n24","-o","%i %t %j"])):
  try:
   p=subprocess.run(cmd,capture_output=True,text=True,timeout=12,check=False)
   d[name]=dict(exit=p.returncode,output=p.stdout.splitlines()[:25],
               error=p.stderr[-120:] if p.returncode else "")
  except (OSError,subprocess.TimeoutExpired) as e:d[name]=dict(error=str(e))
 return d
def selftest():
 stack.selftest()
 assert len(EXPECTED_SITES)==10 and sum(EXPECTED_SITES.values())>20000
 assert 80*5==400 and 79==80-1 and len(REQUIRED_MET)==7
 assert len(TEMPLATE_NAMES)==3
 print("BATCH05 DIRECT AD400 DEEP READINESS SELFTEST PASS | 10 site, 80*5 one-submit, stack/Slurm guard, no pilot, no file or model writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage98",type=Path)
 p.add_argument("--stage90",type=Path)
 p.add_argument("--out",type=Path)
 o=p.parse_args()
 if o.self_test:selftest();return
 if o.stage98 is None or o.stage90 is None or o.out is None:
  p.error("actual Stage98 and Stage90 reports, new output directory required")
 d98,d90,out=(x.expanduser().resolve() for x in (o.stage98,o.stage90,o.out))
 if (not d98.is_dir() or not d90.is_dir() or out.exists() or
     not out.parent.is_dir() or out==d98 or out==d90 or
     out in d98.parents or out in d90.parents or
     d98 in out.parents or d90 in out.parents):
  p.error("science evidence paths or fresh disjoint output invalid")
 f98=d98/"stage98_BATCH05_TEN_SITE_DIRECT_AD400_PREP_INVENTORY.csv"
 m98=json.loads((d98/"stage98_DIRECT_AD400_PREP_PLAN_AND_SCIENCE_RELEASE_GATES.json").read_text())
 if (m98.get("stage")!=98 or m98.get("sites")!=10 or
     m98.get("accelerated_years")!=400 or
     m98.get("segment_count")!=80 or
     m98.get("intended_CIME_RESUBMIT")!=79 or
     m98.get("direct_AD400_submit_permission") is not False or
     m98.get("main_research_approved_HH")!=1675 or
     m98.get("processed_source_ERA_proxy_research_HH")!=1281 or
     m98.get("outputs_SHA256",{}).get(f98.name)!=sha(f98)):
  raise ValueError("actual Stage98 operator result, no-submit status, or evidence SHA changed")
 sites=load(f98,("site","source_start","source_end","source_native_HH_CSV_present"))
 if len(sites)!=10 or {x["site"] for x in sites}!=set(EXPECTED_SITES):
  raise ValueError("stage98 ten original Batch05 sites source cohort drift")
 f90=d90/"stage90_FINAL_HISTORICAL_RELEASE_RISK_EVIDENCE_MANIFEST.json"
 m90=json.loads(f90.read_text())
 if (m90.get("distinct_release_risk_source_HH")!=63 or
     m90.get("historical_P1_HOLD_HH")!=46 or
     m90.get("historical_RH_platform_HOLD_HH")!=10 or
     m90.get("historical_source_T_exception_HH")!=7 or
     len(m90.get("original_source_verified_SHA256_by_site",{}))!=10):
  raise ValueError("original Stage90 ten-site SHA-verified source science status drift")
 original_sha=m90["original_source_verified_SHA256_by_site"]
 baseline={r["site"]:r for r in sites}
 references={}
 for name in TEMPLATE_NAMES:
  case=CASES/name
  refs=dict(case=str(case),case_exists=case.is_dir())
  if case.is_dir():
   flags={}
   for fp in ("env_run.xml","env_case.xml","env_build.xml","env_mach_pes.xml"):
    flags.update(xml(case/fp))
   keys=("RUN_STARTDATE","RUN_TYPE","CONTINUE_RUN","CLM_ACCELERATED_SPINUP",
    "STOP_N","REST_N","RESUBMIT","RESUBMIT_SETS_CONTINUE_RUN","CALENDAR",
    "ATM_NCPL","DATM_MODE","BUILD_COMPLETE","MPI_RUN_COMMAND",
    "EXEROOT","RUNDIR","DOUT_S","DOUT_S_ROOT","PTS_LAT","PTS_LON")
   refs["reference_values"]={k:flags.get(k,"NOT_IN_REFERENCE") for k in keys}
   exe=Path(flags.get("EXEROOT",""))/"cesm.exe" if flags.get("EXEROOT") else None
   refs["reference_executable_exists"]=bool(exe and exe.is_file())
   refs["CaseDocs_lnd_in_exists"]=(case/"CaseDocs/lnd_in").is_file()
   refs["CaseDocs_datm_stream_exists"]=(case/"CaseDocs/datm.streams.xml").is_file()
   if (case/"CaseDocs/lnd_in").is_file():
    l=(case/"CaseDocs/lnd_in").read_text(errors="replace")
    refs["private_FATES_AD_state_2"]=bool(re.search(r"(?m)^\s*spinup_state\s*=\s*2\s*(?:!.*)?$",l))
    refs["nocompetition"]=bool(re.search(r"(?m)^\s*use_fates_nocomp\s*=\s*\.true\.",l,re.I))
   refs["status"]="REFERENCE_ONLY_NO_CROSS_SITE_APPROVAL"
  references[name]=refs
 all_cases={}
 if CASES.is_dir():
  for case in CASES.iterdir():
   if not case.is_dir() or case.is_symlink():continue
   upper=case.name.upper()
   if ("B05" in upper or "BATCH05" in upper) and any(
     case.name.startswith(site+"_") for site in EXPECTED_SITES):
    all_cases[case.name]=case
 soil_paths=[
  Path.home()/"CLM_FATES_SOIL/AmeriFlux50_20261026/09_RECOMMENDED_CLM10_PCT_SAND_PCT_CLAY_WIDE.csv",
  Path.home()/"CLM_FATES_SOIL/AmeriFlux50_20261026_full_BADM/09_RECOMMENDED_CLM10_PCT_SAND_PCT_CLAY_WIDE.csv"]
 zbot=B/"experiments/NonCompetitionObserved22/AmeriFlux_Batch02_10/Stage06_direct_AD400/BASE_MeasurementHeight_20260908.csv"
 co2=B/"experiments/NonCompetitionObserved22/AmeriFlux_Batch02_10/Stage06_direct_AD400/co2_annmean_gl.csv"
 assets=dict(CTSM_source_exists=(B/"CTSM").is_dir(),
  FATES_default_params=(B/"CTSM/src/fates/parameter_files/fates_params_default.json").is_file(),
  soil_candidates=[dict(path=str(x),exists=x.is_file()) for x in soil_paths],
  ZBOT_measurement_height_table=dict(path=str(zbot),exists=zbot.is_file()),
  NOAA_global_CO2_table=dict(path=str(co2),exists=co2.is_file()),
  PFT_50_site_recommended_LOCAL_SOURCE_UNKNOWN=True)
 inventory=[]
 for site, start in EXPECTED_SITES.items():
  original=baseline[site]
  if (int(original["source_start"])!=start or
      original["source_native_HH_CSV_present"]!="True"):
   raise ValueError("Stage98 exact native site source/year/presence drift "+site)
  sroot=SOURCE/site
  forcing=sroot/"forcing"
  rawdir=forcing/"raw"
  source_candidates=sorted(p for folder in rawdir.glob("*") if folder.is_dir()
    for p in folder.glob("*_HH_*.csv") if p.is_file() and not p.is_symlink())
  interesting=[p for p in source_candidates if re.search(r"(FLUXMET|FULLSET)_HH_",p.name)]
  valid_count=len(interesting)
  # Stage98 verified original CSV presence, source hashes were verified by Stage90.
  # Do not perform huge rehash on busy HPC login as part of this inventory.
  datm_candidates=children_nc(forcing,limit=100)
  surfaces=children_nc(sroot,limit=100)
  surfaces=[x for x in surfaces if re.search(r"surfdata|surface|surf_",str(x),re.I)]
  case_list=sorted(k for k in all_cases if k.startswith(site+"_"))
  inventory.append(dict(site=site,source_start=start,AD400_end=start+400,
   source_csv_path=";".join(str(x) for x in interesting[:4]),
   source_raw_has_REQUIRED_source_met_columns=str(
     valid_count==1 and all(c in peek_first_line(interesting[0]) for c in SOURCE_MET)),
   source_raw_missing_source_fields=";".join(
     c for c in SOURCE_MET if valid_count==1 and c not in peek_first_line(interesting[0])),
   raw_source_SHA_verified_prior_Stage90=original_sha[site],
   possible_DATM_NC_paths_unverified=";".join(datm_candidates[:15]),
   possible_surface_NC_paths_unverified=";".join(surfaces[:15]),
   possible_Batch05_CIME_cases_unverified=";".join(case_list),
   cross_batch_templates_ONLY=";".join(TEMPLATE_NAMES),
   proven_Batch05_DATM="False",proven_Batch05_surface="False",
   proven_Batch05_CIME="False",ready_for_submit="False"))
 live=live_preflight()
 qdata={str(p):quota(p) for p in (Path("/iridisfs/scratch/ly3n24"),Path("/scratch/ly3n24"),
                                  Path("/research/xclimatetbm/ly3n24")) if p.exists()}
 manifest=dict(stage=99,source="actual Stage98+Stage90 science & present HPC files",
  operator_direct_AD400=True,no_separate_AD5=True,no_Normal_required=True,
  segments=80,years_per_segment=5,RESUBMIT=79,
  exact_site_count=10,actual_Batch05_named_CIME_case_count=len(all_cases),
  same_process_stack_guard_module="batch05_direct_ad400_stack_guard.py",
  same_process_stack_guard_required_for_future_real_submit=True,
  stack_min_KiB=65536,preferred_raise_KiB=300000,
  live_runtime=live,
  prior_CIME_reference_cases=references,
  ancillary_inputs=assets,
  scratch_and_RFS_filesystem_observation=qdata,
  site_original_sha_verified_Stage90=original_sha,
  stage98_operator_report_SHA256=sha(f98),
  stage90_source_manifest_SHA256=sha(f90),
  requirement_notes=list(PATH_HINTS),
  no_run_submit_authorized=True,
  current_blockers=["P1_PLATFORM_T_SOURCE_POLICY",
     "ERA_SOURCE_PROXY_INDEPENDENT_VALIDATION_1281_HH",
     "TEN_COMPLETE_SCIENCE_APPROVED_DATM_STREAMS",
     "TEN_APPROVED_SURFACE_SOIL_PFT_AND_ZBOT",
     "TEN_PINNED_BATCH05_CIME_AD400_CASES",
     "SLURM_WALLTIME_MEM_STACK_ARCHIVE_INODE_PREFLIGHT"],
  no_original_source_mutation=True,no_CIME_mutation=True,no_hrs_submission=True,
  no_fates_namelist_mutation=True,
  status="HOLD_NOT_READY_FOR_DIRECT_AD400_SUBMISSION")
 out.mkdir(exist_ok=False)
 table=out/"Batch05_DIRECT_AD400_TEN_SITE_SOURCE_DATM_SURFACE_CASE_INVENTORY.csv"
 report=out/"Batch05_DIRECT_AD400_STACK_SLURM_TEMPLATE_QUOTA_AND_SCIENCE_MANIFEST.json"
 checklist=out/"Batch05_DIRECT_AD400_READINESS_ACTIONS.txt"
 write(table,FIELDS,inventory)
 manifest["output_inventory_SHA256"]=sha(table)
 report.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 checklist.write_text("BATCH05 DIRECT AD400: do not run independent AD5 smoke\n\n"+
  "\n".join(f"{i}. {x}" for i,x in enumerate(PATH_HINTS,1))+
  "\n\nSubmission gate remains BLOCKED until science + DATM + site PFT + CIME all PASS.\n")
 print("STAGE99 SUCCESS | actual 10-site source paths, stack/Slurm and historical model template inputs inventoried; no Slurm/CIME/source writes")
 print("STAGE99 STACK",json.dumps(live.get("stack",live.get("stack_error")),sort_keys=True))
 print("STAGE99 SLURM_STACK_PROPAGATION",json.dumps(live.get("slurm",live.get("slurm_error")),sort_keys=True))
 print("STAGE99 ANCILLARY_INPUTS",json.dumps(assets,sort_keys=True))
 print("STAGE99 TEMPLATES")
 for k,v in references.items():
  print("STAGE99 REFERENCE",k,"exists",v["case_exists"],
    "exe",v.get("reference_executable_exists"),"nocomp",v.get("nocompetition"),
    "AD_state_2",v.get("private_FATES_AD_state_2"))
 print("STAGE99 SITE site native_source_count possible_DATM_NC possible_surface_NC Batch05_cases missing_original_meteorology_columns")
 for row in inventory:
  print("STAGE99 SITE",row["site"],
    len(row["source_csv_path"].split(";")) if row["source_csv_path"] else 0,
    len(row["possible_DATM_NC_paths_unverified"].split(";")) if row["possible_DATM_NC_paths_unverified"] else 0,
    len(row["possible_surface_NC_paths_unverified"].split(";")) if row["possible_surface_NC_paths_unverified"] else 0,
    len(row["possible_Batch05_CIME_cases_unverified"].split(";")) if row["possible_Batch05_CIME_cases_unverified"] else 0,
    row["source_raw_missing_source_fields"])
 print("STAGE99 STORAGE",json.dumps(qdata,sort_keys=True))
 print("STAGE99 DIRECT_AD400_PLAN 10 site cases, 400y 80x5, RESUBMIT=79, no AD5 pilot; stack in SAME Python submit process")
 print("STAGE99 RELEASE_GATE",manifest["status"])
 print("STAGE99_REPORTS="+str(out))
 print("STAGE99 READONLY | NO SOURCE/QC/HOLD/OVERLAY/DATM/PFT/CIME/SLURM WRITES")
if __name__=="__main__":main()

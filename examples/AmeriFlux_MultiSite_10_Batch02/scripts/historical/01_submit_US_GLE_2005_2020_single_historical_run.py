#!/usr/bin/env python3
"""Submit ONE exploratory US-GLE CLM-FATES 2005-2020 historical-met run.

User-approved policy: no further spinup-window experiments or synthetic seam
smoothing. Use the 16 Stage106 real-date ERA restored UTC-midpoint NetCDF
years ONCE, sequentially from 2005-01-01 to 2021-01-01. 4-year Slurm
segments with RESUBMIT=3 comprise ONE continuous CIME case/trajectory.
This is EXPLORATORY (cold-start as configured), not spinup-equilibrated.
Fixed CO2=378.98ppm (2005 NOAA global annual mean), constant 2000 surface,
original site gridded crop 7.5144%; NOT fully historical land-use/CO2,
not observed tower vegetation PFT/age/disturbance.
Residual cycle-edge 2020->2005 is documented but never intentionally
sampled in a once-through 2005-2020 run (except potential CIME
interpolation at the final boundary, to verify from runtime logs).
Original prior cases, source NC and metadata are never modified.

USAGE: python3 -B script.py --submit
--check runs source + model checks only (no case creation/jobs).
Requires unmodified Stage103 implementation colocated in same directory.
"""
import argparse, fcntl, hashlib, importlib.util, json, os, re, subprocess
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
EXP=ROOT/"experiments/AmeriFlux_MultiSite_10_Batch02"
S106=EXP/"reports/stage106_GLE_ERA_2004LST_14HH_backfilled_UTCmid_16NC_20261026T125959Z_bfa2ba7f"
SOURCE=ROOT/"cases/GF-Guy_FATES_SURF2000_CO2405_1PT"
STAGE103="103_GLE_seam_CIME_detached_namelist_preflight.py"
STAGE103_BLOB="c67aa9c5c4e358b0c2efba99da46e08d8a8341c5"
NAME="US-GLE_FATES_HISTMET_2005_2020_STAGE106"
CASE=ROOT/"cases"/NAME
OUT=Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
RUNDIR=OUT/NAME/"run"
ARCHIVE=OUT/"archive"/NAME
FIRST,LAST=2005,2020
SEGMENT=4
RESUBMIT=3
CO2_PPMV="378.98"  # NOAA global annual mean for 2005, FIXED
FIELDS=("PRECTmms","FSDS","ZBOT","TBOT","WIND","QBOT","PSRF","FLDS")

def fail(message):
    raise RuntimeError(message)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()
def gitblob(p):
    z=Path(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(z)).encode()+b"\0"+z).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2,default=str)+"\n")
def tool(cmd,where,log,seconds=360):
    with log.open("a") as f:
        f.write("CMD="+repr(cmd)+" CWD="+str(where)+"\n");f.flush()
        r=subprocess.run(cmd,cwd=str(where),stdout=f,stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL,timeout=seconds)
        f.write("RETURN="+str(r.returncode)+"\n");f.flush()
    if r.returncode:
        fail("CIME command failed "+repr(cmd)+"; "+str(log))
def query(field):
    p=subprocess.run(["./xmlquery",field,"--value"],cwd=str(CASE),
            stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=45)
    if p.returncode:fail("Cannot read CIME XML field "+field+": "+p.stderr)
    return p.stdout.strip()
def change(name,value,log):
    tool(["./xmlchange",f"{name}={value}"],CASE,log,seconds=90)
    if query(name)!=str(value):
        # numeric XML may normalize 378.98 to 378.980000.
        if name=="CCSM_CO2_PPMV" and abs(float(query(name))-float(value))<1e-7:
            return
        fail("CIME xmlchange mismatch "+name+" "+str(value)+" actual "+query(name))

def module():
    p=Path(__file__).resolve().parent/STAGE103
    if not p.is_file() or gitblob(p)!=STAGE103_BLOB:
        fail("Verified prior Stage103 module missing/changed, fetch pinned peer script")
    spec=importlib.util.spec_from_file_location("gle_original_case_recipe",str(p))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for v in ("source_case","site_surface","create_isolated_case","original_stream"):
        if not hasattr(m,v):fail("Historical CIME recipe lacks "+v)
    return m

def inputs():
    if os.getuid()==0 or os.environ.get("USER")!="ly3n24":
        fail("Run only as ly3n24 on IRIDIS6 login/submit node")
    m=read(S106/"manifest.json")
    if not (m.get("schema")=="BATCH02_STAGE106_GLE_TRUE_DATED_ERA_LST_PREHISTORY_16UTC_MID_NC"
        and m.get("16_year_new_NC_count")==16
        and m.get("2004_LST_ERA_replaced_UTC_first_slots")==14
        and m.get("all_original_2005_later_and_other_15_year_values_unchanged") is True
        and m.get("source_2020_synthetic_weather_seam_removed") is True
        and m.get("science_DATM_approved") is False
        and m.get("Slurm_jobs_submitted") is False
        and not (S106/"INCOMPLETE_DO_NOT_USE").exists()
        and (S106/"SCIENCE_HOLD_NO_CIME_MODEL_OR_SPINUP").is_file()):
        fail("Original Stage106 science-hold source contract is invalid")
    for file,digest in m["out_sha256"].items():
        if sha(S106/file)!=digest:fail("Original Stage106 receipt mismatch "+file)
    yrs=sorted(read(S106/"16_year_independent_NC_receipts.json"),
               key=lambda x:x["year"])
    if len(yrs)!=16 or [d["year"] for d in yrs]!=list(range(2005,2021)):
        fail("2005–2020 Stage106 source years missing or out of order")
    for x in yrs:
        if (sha(x["new"])!=x["sha256"] or
            sha(x["source_Stage102"])!=x["source_sha256"] or
            x["changed_original_samples"]!=(14 if x["year"]==2005 else 0)):
            fail("Original Stage106 year has unapproved value changes: "+str(x["year"]))
    return yrs,m

def check_land_doc(surf):
    lnd=CASE/"CaseDocs/lnd_in"
    if not lnd.is_file() or Path(surf["surface"]).name not in lnd.read_text():
        fail("Generated GLE CaseDocs does not use original local GLE surface")
    raw=lnd.read_text(errors="replace")
    match=re.search(r"^\s*finidat\s*=\s*['\"]?([^'\"\s,!]+)",raw,re.M|re.I)
    if match and match.group(1).strip().lower() not in ("","none","null"):
        fail("Unexpected land initial condition FINIDAT on historical cold-start "+match.group(1))
    if not re.search(r"^\s*use_excess_ice\s*=\s*\.false\.",raw,re.M|re.I):
        fail("Successful GF-Guy excess-ice setting missing")
    return sha(lnd)

def prepare(m,source,log):
    if CASE.exists():fail("Refuse to overwrite or accidentally re-submit existing historical case "+str(CASE))
    if RUNDIR.exists():fail("Refuse existing historical RUNDIR")
    SOURCE_EXE=subprocess.run(["./xmlquery","EXEROOT","--value"],
          cwd=str(SOURCE),capture_output=True,text=True,timeout=45,check=True).stdout.strip()
    if not (Path(SOURCE_EXE)/"cesm.exe").is_file():
        fail("Proven GF-Guy compiled cesm.exe not found; do not use unbuilt clone")
    surf=m.site_surface()
    m.source_case()
    histroot=CASE.parent
    CASE.parent.mkdir(parents=True,exist_ok=True)
    original=m.original_stream(source)
    if (original.count("/2005.nc")!=1 or original.count("/2020.nc")!=1
        or "QBOT Sa_shum" not in original or "ZBOT Sa_z" not in original):
        fail("Original 16x unique Stage106 DATM stream source not correct")
    # Same case recipe already passed for GLE Stage103. Do not enable model
    # until ALL Stage106-verified paths checked & clone CIME preview succeeds.
    receipt=m.create_isolated_case(CASE,Path(surf["mods"]),source,
        (41.3665,253.7601),surf,log)
    if (CASE/"user_nl_datm_streams").read_text()!=original:
        fail("New single historical case points to wrong CIME DATM sources")
    updates={
        "RUN_TYPE":"startup",
        "CONTINUE_RUN":"FALSE",
        "RUN_STARTDATE":"2005-01-01",
        "CALENDAR":"NO_LEAP",
        "ATM_NCPL":"48",
        # A 4-year CIME segment automatically continues via restart.
        # ONE case / ONE historical trajectory, not repeated spinup.
        "STOP_OPTION":"nyears",
        "STOP_N":str(SEGMENT),
        "REST_OPTION":"nyears",
        "REST_N":str(SEGMENT),
        "RESUBMIT":str(RESUBMIT),
        "DOUT_S":"TRUE",
        "DOUT_S_ROOT":str(ARCHIVE),
        "RUNDIR":str(RUNDIR),
        "CLM_CO2_TYPE":"constant",
        "CCSM_CO2_PPMV":CO2_PPMV,
    }
    for name,val in updates.items():change(name,val,log)
    if query("EXEROOT")!=SOURCE_EXE:fail("Clone EXEROOT not shared with valid tested GF-Guy")
    if query("BUILD_COMPLETE")!="TRUE":
        change("BUILD_COMPLETE","TRUE",log)  # only because verified GF-Guy exe is reused
    if not (CASE/".case.run").is_file():fail("Missing prepared CIME run script")
    tool(["./preview_namelists"],CASE,log,seconds=240)
    land_hash=check_land_doc(surf)
    stream=(CASE/"user_nl_datm_streams").read_text()
    if (stream!=original or "CLM_USRDAT.UNSET:year_first = 2005" not in stream or
        "CLM_USRDAT.UNSET:year_last = 2020" not in stream or
        "CLM_USRDAT.UNSET:year_align = 2005" not in stream):
        fail("CIME model forcing year mapping differs from 2005–2020 single historical")
    if (query("STOP_N")!="4" or query("RESUBMIT")!="3" or
        query("RUN_STARTDATE")!="2005-01-01" or query("CLM_CO2_TYPE")!="constant"):
        fail("Final CIME historical run controls differ")
    tool(["./check_input_data"],CASE,log,seconds=240)
    report={
        "case":str(CASE),"source_Stage106_manifest_SHA256":sha(S106/"manifest.json"),
        "model_GLE_years":"2005-01-01 to 2021-01-01 exclusive",
        "DATM_year_first":2005,"DATM_year_last":2020,
        "DATM_16_source_NC_SHA256":[[r["year"],r["sha256"]] for r in source],
        "spatial_surface":surf["surface"],
        "land_CaseDocs_SHA256":land_hash,
        "source_reference_CIME_EXEROOT":SOURCE_EXE,
        "experiment":"one continuous historical METEOROLOGY simulation, not spin-up",
        "segments":"4 consecutive 4-year jobs in same CIME case, 3 automated resubmits",
        "CO2":"fixed NOAA 2005 global mean 378.98 ppm; NOT transient CO2",
        "initial_condition":"CIME startup; no external tower-age inventory or PFT fitted",
        "original_PFT_ENF_observation":"85% Engelmann spruce +15% subalpine fir (species shares); full tower footprint unknown",
        "site_gridded_crop_pct":7.514438754520235,
        "beetle_2008_mortality":"85% of forest basal area, NOT 85% areal PFT loss; model not explicitly disturbed",
        "2020_to_2005_periodic_boundary_issue":"3.877K / 259Pa / 4.617mps source wrap; not knowingly used in a single 2005-2020 trajectory",
        "ZBOT_thermodynamic_m":23.4,"wind_measurement_height_m":22.65,
        "model_results_scientific_observation_match_approved":False,
        "run_log":str(log),
    }
    note=CASE/"HISTORICAL_2005_2020_KNOWN_LIMITATIONS.json"
    save(note,report)
    print("GLE HIST2005-2020 PREPARED | source Stage106 16/16; GLE original surface, 4×4-year continuation, fixed CO2 378.98ppm")
    print("GLE HIST2005-2020 CASE",CASE)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    args=parser.add_mutually_exclusive_group(required=True)
    args.add_argument("--check",action="store_true")
    args.add_argument("--submit",action="store_true")
    mode=parser.parse_args()
    m=module()
    source,meta=inputs()
    m.source_case()
    surf=m.site_surface()
    print("GLE HIST2005-2020 SOURCE PASS | 16 Stage106 yearly NC SHA, 2005 genuine ERA backfill, BIF original surface",flush=True)
    print("GLE HIST2005-2020 MODEL POLICY | ONE 2005-2020 run; fixed CO2 378.98ppm; cold-start exploratory; raw land PFT preserved; no spinup",flush=True)
    if mode.check:
        if CASE.exists():fail("Target historical case exists; refuse a second run")
        print("GLE HIST2005-2020 CHECK PASS | no source/case/job writes",flush=True)
        return
    lock=ROOT/"cases/.gle_hist2005_2020_run.lock"
    with lock.open("w") as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:fail("GLE historical launch already in progress")
        case_log=Path.home()/"GLE_hist2005_2020_onecase_submit.log"
        report=prepare(m,source,case_log)
        # User explicitly asked to submit ONE historical simulation now.
        print("GLE HIST2005-2020 SUBMITTING | 4y x4 continuous trajectory",flush=True)
        tool(["./case.submit"],CASE,case_log,seconds=240)
        report["submission_returned_successfully"]=True
        report["CaseStatus_tail"]=(CASE/"CaseStatus").read_text(errors="replace").splitlines()[-16:]
        save(CASE/"HISTORICAL_2005_2020_KNOWN_LIMITATIONS.json",report)
        print("GLE HIST2005-2020 SUBMITTED | one CIME case, four 4-year sequential segments; 2005-2020",flush=True)
        print("GLE HIST2005-2020 CASE",CASE,flush=True)
        print("GLE HIST2005-2020 LOG",case_log,flush=True)
        print("GLE HIST2005-2020 STATUS use squeue -u ly3n24; tail -30 "+str(CASE/"CaseStatus"),flush=True)

if __name__=="__main__":
    main()

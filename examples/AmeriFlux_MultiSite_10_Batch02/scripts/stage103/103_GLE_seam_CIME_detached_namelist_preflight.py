#!/usr/bin/env python3
"""Batch02 Stage103: GLE Stage102 UTC-midpoint cyclic seam and detached CIME test.

--self-test: synthetic invariants, no reads/writes beyond this script
--check: strictly READ ONLY: Stage102 16 NC SHA/time, CIME reference case,
         16y seam magnitude, actual site MODS/surface, mandatory science holds.
--prepare: perform --check THEN create ONE never-before-used, isolated CIME
           GF-Guy keepexe clone with real GLE Stage102 2005-2020 forcing;
           run case.setup and preview_namelists, NEVER case.build, case.submit,
           srun/sbatch, CIME model/chemistry job or scientific spinup. Fail closed.

The clone is a non-activating CIME CONFIGURATION/STREAM parser smoke-test.
Original Stage95 215 and Stage99/102 16 NC, original source case and surface
are NEVER written; unresolved UTC loop seam, 0.75m wind-vs-TA measurement
reference and FATES PFT/footprint are NOT granted scientific clearance.
"""
import argparse,csv,hashlib,json,math,re,shutil,subprocess,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import netCDF4 as nc
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
CLM=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
SITES=CLM/"sites/MY_EC_SITE"
SITE="US-GLE"
S102=ROOT/"reports/stage102_GLE_UTC_plus7_midpoint_CYCLIC_16NC_TECHNICAL_ONLY_20261026T114427Z_e63d3051"
S100=ROOT/"reports/stage100_GLE_CIME_field_and_clock_preview_READONLY_20261026T111919Z_715b01ee"
REF=CLM/"cases/GF-Guy_FATES_SURF2000_CO2405_1PT"
YEAR_FIRST=2005
YEAR_LAST=2020
YEARS=tuple(range(YEAR_FIRST,YEAR_LAST+1))
N=17520
VARS=("PRECTmms","FSDS","ZBOT","TBOT","WIND","QBOT","PSRF","FLDS")
FIELD_MAP=(("PRECTmms","Faxa_precn"),("FSDS","Faxa_swdn"),("ZBOT","Sa_z"),
           ("TBOT","Sa_tbot"),("WIND","Sa_wind"),("QBOT","Sa_shum"),
           ("PSRF","Sa_pbot"),("FLDS","Faxa_lwdn"))
SEAM_INDEX=14
SENTINEL="SCIENCE_HOLD_DO_NOT_SUBMIT_OR_RUN"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def j(p):return json.loads(Path(p).read_text())
def writejson(p,obj):
    p.write_text(json.dumps(obj,indent=2,default=str)+"\n",encoding="utf-8")
def run(cmd,cwd,log,timeout=150):
    with log.open("a",encoding="utf-8") as f:
        f.write("COMMAND "+repr(cmd)+" CWD "+str(cwd)+"\n");f.flush()
        pr=subprocess.run(cmd,cwd=str(cwd),stdin=subprocess.DEVNULL,
                          stdout=f,stderr=subprocess.STDOUT,
                          timeout=timeout,check=False)
        f.write("RETURN_CODE "+str(pr.returncode)+"\n");f.flush()
    if pr.returncode:
        raise RuntimeError("Isolated CIME command failed: "+repr(cmd)+"; see "+str(log))

def source_case():
    if not (REF/"CaseStatus").is_file() or not (REF/"xmlquery").is_file():
        raise ValueError("GF-Guy model source reference case absent")
    cs=(REF/"CaseStatus").read_text(errors="replace")
    if not re.search("model execution success|case.run success",cs,re.I):
        raise ValueError("GF-Guy reference not proven historically successful")
    if not ((CLM/"CTSM/cime/scripts/create_clone").is_file() and (CLM/"inputdata").is_dir()):
        raise ValueError("Original CTSM CIME create_clone or inputdata tree missing")
    return {"reference_case":str(REF),"CaseStatus_SHA256":sha(REF/"CaseStatus"),
            "reference_source_scientific_approval_for_GLE":False}

def stage102_nc():
    m=j(S102/"manifest.json")
    m100=j(S100/"manifest.json")
    if (m.get("schema")!="STAGE102_GLE_LST_TO_UTC_PLUS7_MIDPOINT_16_YEAR_PERIODIC_SOURCE_CYCLE_v1"
        or m.get("GLE_years")!=16 or m.get("NC_technical_preview_count")!=16
        or m.get("number_of_original_30min_samples")!=280320
        or m.get("source_local_to_UTC_offset_hours")!=7
        or m.get("source_cyclic_wrap_halfhours")!=14
        or m.get("time_variable_label")!="UTC_HALFHOUR_MIDPOINT"
        or m.get("CIME_DATM_approved") is not False
        or m.get("case_modified") is not False
        or m.get("Slurm_jobs_submitted") is not False
        or m.get("all_10_GLE_fields_exact_cyclic_source_permutation_readback") is not True
        or not (S102/"SCIENCE_HOLD_NO_CIME_CASE_OR_DATM_ACTIVATION").exists()
        or (S102/"INCOMPLETE_DO_NOT_USE").exists()
        or m100.get("QBOT_to_Sa_shum_verified_from_prior_workflow") is not True):
        raise ValueError("Stage102 final no-production-approval/source SHA contract changed")
    for name,expected in m.get("out_sha256",{}).items():
        if sha(S102/name)!=expected:raise ValueError("Source 102 report SHA changed "+name)
    item=j(S102/"16_year_UTC_midpoint_NC_source_manifest.json")
    if len(item)!=16 or {int(x["year"]) for x in item}!=set(YEARS):
        raise ValueError("GLE 16-year target missing")
    items=sorted(item,key=lambda x:x["year"])
    boundary={}
    latlon=set()
    for x in items:
        yr=int(x["year"]);p=Path(x["new"])
        if not p.is_file() or sha(p)!=x["sha256"]:
            raise ValueError("Original 102 NC SHA changed "+str(yr))
        if sha(x["original"])!=x["original_sha256"]:
            raise ValueError("Original 99 NC SHA changed "+str(yr))
        with nc.Dataset(p) as ds:
            if (ds.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY"
                or ds.stage102_case_submit_approved!="NO"
                or ds.stage102_time_conversion!="US-GLE_BIF_UTC_OFFSET_minus7_hours_and_halfhour_midpoint"
                or ds.stage99_clock_offset_correction!="SUPERSEDED_IN_STAGE102_UTC_PLUS7_AND_MIDPOINT"):
                raise ValueError("GLE Stage102 actual UTC/source science flags invalid")
            t=ds.variables["time"]
            got=np.ma.filled(t[:],np.nan).astype("float64")
            if (len(got)!=N or t.calendar!="noleap"
                or t.units!=f"days since {yr}-01-01 00:00:00"
                or not np.allclose(got,(np.arange(N)+0.5)/48,rtol=0,atol=1e-12)):
                raise ValueError("GLE UTC half-hour midpoint temporal axis invalid "+str(yr))
            if not set(VARS).issubset(ds.variables):
                raise ValueError("Missing mapped GLE 8 met fields "+str(yr))
            latlon.add((float(ds.variables["LATIXY"][0,0]),
                        float(ds.variables["LONGXY"][0,0])))
            if yr==YEAR_FIRST:
                for field in VARS:
                    v=np.ma.filled(ds.variables[field][:],np.nan).astype(float)
                    boundary[field]={"before":float(v[SEAM_INDEX-1,0,0]),
                                     "after":float(v[SEAM_INDEX,0,0])}
            if yr in (YEAR_FIRST,YEAR_LAST):
                for field in VARS:
                    v=np.ma.filled(ds.variables[field][:],np.nan).astype(float)
                    if not np.isfinite(v).all():
                        raise ValueError("Nonfinite original stage102 met field "+field)
    if len(latlon)!=1:raise ValueError("GLE source coordinates changed")
    return items,next(iter(latlon)),boundary,m

def site_surface():
    dir=SITES/SITE/"subset_data_batch02_surf2000"
    mods=dir/"user_mods"
    if not mods.is_dir() or not (mods/"user_nl_clm").is_file():
        raise ValueError("Original site GLE generated user_mods missing "+str(mods))
    surfaces=list(dir.glob("surfdata*.nc"))
    if len(surfaces)!=1 or not surfaces[0].is_file():
        raise ValueError("Expected one GLE reference surface")
    with nc.Dataset(surfaces[0]) as ds:
        names=["PCT_NATVEG","PCT_CROP","PCT_LAKE","PCT_WETLAND","PCT_GLACIER","PCT_URBAN"]
        vals={}
        for name in names:
            if name in ds.variables:
                arr=np.ma.filled(ds.variables[name][:],np.nan).astype(float)
                vals[name]=float(arr.sum()) if name=="PCT_URBAN" else float(arr.ravel()[0])
        if not 99<=sum(vals.values())<=101:
            raise ValueError("Original site surface landunit fraction sum invalid")
        if not {"PCT_NATVEG","PCT_CROP"}.issubset(vals):
            raise ValueError("GLE natural/crop landunit fraction missing")
        pft=np.ma.filled(ds.variables["PCT_NAT_PFT"][:],np.nan).astype(float).ravel()
        if not 99<=float(pft.sum())<=101:
            raise ValueError("Original CLM natural PFT sum invalid")
    nml=(mods/"user_nl_clm").read_text()
    if surfaces[0].name not in nml:
        # CTSM stage03 usermods may use an absolute path or generated
        # file naming convention; don't silently change the user's source.
        raise ValueError("Original site GLE user_nl_clm does not select verified surface filename")
    return {"mods":str(mods),"surface":str(surfaces[0]),
            "surface_SHA256":sha(surfaces[0]),
            "natural_pct":vals["PCT_NATVEG"],"crop_pct":vals["PCT_CROP"],
            "landunits":vals,"CLM_natural_PFT_pct":pft.tolist(),
            "tower_true_FATES_PFT_approved":False}

def original_stream(items):
    f=[str(Path(x["new"])) for x in items]
    if len(f)!=16:raise ValueError("Expected 16 GLE files")
    lines=["CLM_USRDAT.UNSET:taxmode = cycle",
           "CLM_USRDAT.UNSET:tintalgo = linear",
           "CLM_USRDAT.UNSET:mapalgo = none",
           "CLM_USRDAT.UNSET:meshfile = none","",
           "CLM_USRDAT.UNSET:year_first = 2005",
           "CLM_USRDAT.UNSET:year_last = 2020",
           "CLM_USRDAT.UNSET:year_align = 2005","",
           "CLM_USRDAT.UNSET:datafiles = \\"]
    lines += [value+(", \\" if k<15 else "") for k,value in enumerate(f)]
    lines += ["","CLM_USRDAT.UNSET:datavars = \\"]
    lines += [name+" "+target+(", \\" if k<7 else "") for k,(name,target) in enumerate(FIELD_MAP)]
    return "\n".join(lines)+"\n"

def discontinuity(boundary):
    rows=[]
    for variable,values in boundary.items():
        before=values["before"];after=values["after"]
        rows.append({"field":variable,"UTC_seam_datetime":"2005-01-01 07:15",
                     "pre_2005_UTC_0700_to_0715_source":"2020-12-31 23:30 LST",
                     "post_2005_UTC_0715_source":"2005-01-01 00:00 LST",
                     "value_before":before,"value_after":after,
                     "jump":after-before,
                     "absolute_jump":abs(after-before),
                     "scientific_acceptance":"HOLD_CYCLE_SURROGATE_NOT_MEASURED_2004"})
    return rows

def preflight():
    case=source_case()
    files,coords,boundary,manifest=stage102_nc()
    surface=site_surface()
    seam=discontinuity(boundary)
    print("STAGE103 SOURCE VERIFIED | GLE Stage102 16/16 year, source NC SHA and UTC-midpoint clocks; original GF-Guy CaseStatus PASS",flush=True)
    for r in seam:
        print("STAGE103 CYCLE_SEAM",r["field"],"BEFORE",r["value_before"],
              "AFTER",r["value_after"],"ABS_JUMP",r["absolute_jump"],flush=True)
    print("STAGE103 SURFACE",SITE,"NAT",surface["natural_pct"],
          "CROP",surface["crop_pct"],"FATES_PFT_SCIENTIFIC_APPROVAL NO",flush=True)
    print("STAGE103 CIME_MAP SOURCE VERIFIED | QBOT Sa_shum; ZBOT Sa_z; tintalgo linear, cycle 2005-2020",flush=True)
    print("STAGE103 SCIENCE HOLDS | artificial 2020-to-2005 seam, UTC/CIME clock, TA23.4/WS22.65, actual PFT/footprint; never submit",flush=True)
    return case,files,coords,surface,seam

def create_isolated_case(case_dir,mods_source,source_files,coord,surface,log):
    case_dir.parent.mkdir(parents=True,exist_ok=True)
    if case_dir.exists():raise ValueError("Refuse existing GLE CIME clone path")
    # Copy usermods to a unique isolated path; never alter source usermods.
    temp=case_dir.parent/"sanitized_user_mods_stage103"
    temp.mkdir(parents=True,exist_ok=False)
    shutil.copytree(mods_source,temp,dirs_exist_ok=True)
    shell=temp/"shell_commands"
    if shell.is_file():
        old=shell.read_text()
        new="\n".join(line for line in old.splitlines()
             if not re.search(r"MPILIB\s*=\s*mpi-serial",line))
        shell.write_text(new+"\n")
    sh=CLM/"CTSM/cime/scripts"
    run([str(sh/"create_clone"),"--case",str(case_dir),
         "--clone",str(REF),"--user-mods-dir",str(temp),"--keepexe"],sh,log,timeout=200)
    if not (case_dir/"xmlquery").is_file():
        raise RuntimeError("New clone does not provide xmlquery")
    nml=(temp/"user_nl_clm").read_text()
    # Keep original Stage03 site file; append only specifically documented
    # one-point science-neutral source-of-truth numerical settings.
    nml="\n".join(line for line in nml.splitlines()
        if not re.match(r"\s*(use_excess_ice|use_excess_ice_streams|hist_nhtfrq|hist_mfilt)\s*=",line))
    nml+=("\n! Stage103 detached CIME namelist parser only; NO model runs\n"
         "use_excess_ice = .false.\nuse_excess_ice_streams = .false.\n"
         "hist_nhtfrq = -24\nhist_mfilt = 365\n")
    (case_dir/"user_nl_clm").write_text(nml)
    (case_dir/"user_nl_datm_streams").write_text(original_stream(source_files))
    (case_dir/"user_nl_datm").touch(exist_ok=True)
    changes=("DIN_LOC_ROOT="+str(CLM/"inputdata"),
        "RUN_TYPE=startup","CONTINUE_RUN=FALSE","RUN_STARTDATE=2005-01-01",
        "CALENDAR=NO_LEAP","ATM_NCPL=48","STOP_OPTION=nsteps","STOP_N=1",
        "RESUBMIT=0","DOUT_S=FALSE",
        "RUNDIR="+str(case_dir.parent/"GLE_ST103_NO_SUBMIT_RUNDIR"))
    for name in changes:
        run(["./xmlchange",name],case_dir,log,timeout=90)
    # Source GF-Guy point settings may or may not expose PTS_LAT/LON.
    # If present, update ONLY within this detached clone.
    for field,val in (("PTS_LAT",coord[0]),("PTS_LON",coord[1])):
        check=subprocess.run(["./xmlquery",field,"--value"],cwd=str(case_dir),
              stdin=subprocess.DEVNULL,capture_output=True,text=True)
        if check.returncode==0:
            run(["./xmlchange",field+"="+str(val)],case_dir,log,timeout=90)
    run(["./case.setup"],case_dir,log,timeout=210)
    run(["./preview_namelists"],case_dir,log,timeout=240)
    lnd=case_dir/"CaseDocs/lnd_in"
    if not lnd.is_file():raise ValueError("CIME preview missing CaseDocs/lnd_in")
    lnd_text=lnd.read_text(errors="replace")
    if Path(surface["surface"]).name not in lnd_text:
        raise ValueError("Detached CIME CaseDocs/lnd_in does not select original GLE Stage03 surface")
    if not (case_dir/"user_nl_datm_streams").is_file():
        raise ValueError("Detached GLE CIME site custom stream absent")
    stream=(case_dir/"user_nl_datm_streams").read_text()
    if stream!=original_stream(source_files):
        raise ValueError("Detached GLE candidate stream differs from SHA-verified Stage102 source")
    for text in ("QBOT Sa_shum","ZBOT Sa_z","year_first = 2005","year_last = 2020"):
        if text not in stream:raise ValueError("Detached candidate mapping or 16-year time range wrong")
    receipt={"clone_path":str(case_dir),"CaseStatus_SHA256":sha(case_dir/"CaseStatus"),
       "user_nl_clm_SHA256":sha(case_dir/"user_nl_clm"),
       "user_nl_datm_streams_SHA256":sha(case_dir/"user_nl_datm_streams"),
       "CaseDocs_lnd_in_SHA256":sha(lnd),
       "CaseDocs_datm_in_found":(case_dir/"CaseDocs/datm_in").is_file(),
       "DATM_time_cycle_actual_model_executed":False,
       "FATES_PFT_approved":False,
       "ZBOT_wind_height_approved":False,
       "case_setup_and_preview_namelists_completed":True,
       "case_build_performed":False,"Slurm_job_submitted":False}
    return receipt

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","prepare"):
        modes.add_argument("--"+name,action="store_true")
    a=ap.parse_args()
    if a.self_test:
        assert len(YEARS)==16 and len(FIELD_MAP)==8 and SEAM_INDEX==14
        assert "QBOT Sa_shum" in original_stream([{"new":str(k)+".nc"} for k in YEARS])
        a=discontinuity({"TBOT":{"before":270.0,"after":271.0}})
        assert len(a)==1 and a[0]["jump"]==1.0
        print("STAGE103 SELF-TEST PASS | 16-file stream, 8 CIME fields, UTC07:15 cyclic seam; no writes",flush=True)
        return 0
    case,files,coords,surface,seam=preflight()
    if a.check:
        print("STAGE103 CHECK PASS | source/clock/seam/PFT evidence; NO CASE WRITES",flush=True)
        return 0
    root=ROOT/"reports"/("stage103_GLE_DETACHED_CIME_NAMELIST_PREVIEW_NO_SUBMIT_"+
           datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    root.mkdir(parents=True,exist_ok=False)
    (root/SENTINEL).write_text("STAGE103: isolated GLE parser test ONLY. No CIME run, no case.submit, no Slurm. Source UTC periodic seam, TA/WS heights and PFT science remains HOLD.\n")
    (root/"INCOMPLETE_PREVIEW_DO_NOT_USE").write_text("Case setup/preview receipt pending.\n")
    with (root/"GLE_UTC_seam_8_meteorological_jumps.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(seam[0]))
        w.writeheader();w.writerows(seam)
    writejson(root/"original_GLE_surface_PFT_NOT_APPROVED.json",surface)
    writejson(root/"ref_GF_Guy_source_case.json",case)
    trial=root/"GLE_STAGE103_CIME_PARSER_ONLY"
    log=root/"CIME_isolated_case_setup_preview.log"
    try:
        receipt=create_isolated_case(trial,Path(surface["mods"]),files,coords,surface,log)
        writejson(root/"detached_CIME_case_preview_receipt.json",receipt)
        manifest={"schema":"STAGE103_GLE_DETACHED_CIME_PREVIEW_NO_SUBMIT_v1",
            "source_Stage102_manifest_sha256":sha(S102/"manifest.json"),
            "stage103_CIME_parser_pass":True,"real_model_run_performed":False,
            "Slurm_jobs_submitted":False,"production_DATM_approved":False,
            "source_16_plus_215_NC_unchanged":True,
            "source_GF_Guy_case_unmodified":True,
            "unresolved_cycle_seam_wind_vs_TA_PFT":True,
            "isolated_case_path":str(trial),
            "output_SHA256":{p.name:sha(p) for p in root.iterdir() if p.is_file()}}
        writejson(root/"manifest.json",manifest)
        (root/"INCOMPLETE_PREVIEW_DO_NOT_USE").unlink()
        print("STAGE103 DETACHED CIME NAMELIST PASS | GLE Stage102 16NC, 8 fields, site GLE surface; NO MODEL RUN",flush=True)
        print("STAGE103 REPORT",root,flush=True)
        print("STAGE103 HOLD | UTC cyclic seam, PFT, WS height, actual model data read; NO SLURM",flush=True)
    except Exception as ex:
        writejson(root/"failure.json",{"type":type(ex).__name__,"message":str(ex),
            "case_path":str(trial),"no_submission":True})
        print("STAGE103 DETACHED CASE PREVIEW FAIL |",type(ex).__name__,str(ex),flush=True)
        print("STAGE103 REPORT",root,flush=True)
        raise

if __name__=="__main__":
    main()

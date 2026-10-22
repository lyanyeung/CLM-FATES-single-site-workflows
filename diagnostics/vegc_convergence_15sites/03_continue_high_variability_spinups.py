#!/usr/bin/env python3
"""Controlled checkpoint continuation: IL-Yat, CZ-Stn, GL-ZaH ONLY.

Modes: inspect (read-only), prepare SITE (backups and sets RESUBMIT; no submit),
       submit SITE SESSION (one-shot submit; no repeat allowed).
Manual permission is required at prepare/submit. Refuse live/unarchived cases.
IL-Yat already has a historical 3000-year continuation; if its CIME RESUBMIT
is nonzero or a job exists, do NOT replace that workflow.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime,timezone

USER="ly3n24"
CASES=Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases")
OUT=Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
HOME=Path.home()
# A ~300y incremental follow-up for 1000y sites, rounded UP to 5-y
# segments and a complete forcing cycle: CZ-Stn 1305, GL-ZaH 1300.
# IL-Yat already has an existing 3000y CIME target; preserve that target.
SITES={
  "IL-Yat":dict(case="IL-Yat_FATES_SPINUP500",start=2000,target=3000,forcing=25),
  "CZ-Stn":dict(case="CZ-Stn_FATES_SPINUP500_11P",start=2010,target=1305,forcing=15),
  "GL-ZaH":dict(case="GL-ZaH_FATES_SPINUP500_11P",start=2000,target=1300,forcing=26),
}
PARTS={"cpl":"cpl.r","atm":"datm.r","lnd":"clm2.r"}
SCI=("user_nl_clm","user_nl_datm_streams")
BACKUP=("CaseStatus","env_run.xml","env_batch.xml","env_build.xml",
        "env_archive.xml","env_case.xml","env_mach_pes.xml",
        ".case.run","case.st_archive",*SCI)

class Stop(Exception): pass

def run(args,cwd=None):
    p=subprocess.run(args,cwd=str(cwd) if cwd else None,capture_output=True,text=True,timeout=120)
    if p.returncode:
        raise Stop(f"command {args!r} failed:\n{(p.stdout+p.stderr)[-1500:]}")
    return p.stdout.strip()

def filehash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def xval(case,key):
    return run(["./xmlquery",key,"--value"],case).strip()

def queue(name):
    out=run(["squeue","-h","-u",USER,"-o","%i|%.150j|%T|%R"])
    jobs=[]
    for line in out.splitlines():
        parts=line.split("|",3)
        if len(parts)==4 and parts[1] in ("run."+name,"st_archive."+name):
            jobs.append({"jobid":parts[0],"jobname":parts[1],"state":parts[2],"reason":parts[3]})
    return jobs

def validnc(p):
    if p.is_symlink() or not p.is_file() or p.stat().st_size<1024:return False
    with p.open("rb") as f:h=f.read(8)
    return h[:3]==b"CDF" or h==b"\x89HDF\r\n\x1a\n"

def pointer(p):
    if not p.is_file() or p.is_symlink():return None
    return p.read_text(errors="replace").splitlines()[0].strip().removeprefix("./")

def checkpoint(site):
    d=SITES[site]
    name=d["case"]; start=d["start"];target=d["target"]
    case=CASES/name; run_dir=OUT/name/"run"; archive=OUT/"archive"/name/"rest"
    for folder in (case,run_dir,archive):
        if not folder.is_dir():raise Stop(f"{site}: missing directory {folder}")
    if (case/".git/index.lock").exists():raise Stop(f"{site}: CIME git/index.lock exists")
    for f in ("xmlquery","xmlchange","case.submit","preview_run","CaseStatus",*SCI):
        if not (case/f).is_file():raise Stop(f"{site}: missing {f}")
    jobs=queue(name)
    if jobs:raise Stop(f"{site}: Slurm already has current run/archive job(s): {jobs}; do not submit")
    expected=dict(CASE=name,RUN_STARTDATE=f"{start}-01-01",RUN_TYPE="startup",
                  CONTINUE_RUN="TRUE",STOP_OPTION="nyears",STOP_N="5",
                  REST_OPTION="nyears",REST_N="5",DOUT_S="TRUE",CALENDAR="NO_LEAP",
                  ATM_NCPL="48",RUNDIR=str(run_dir),DOUT_S_ROOT=str(archive.parent),
                  BUILD_COMPLETE="TRUE")
    for key,value in expected.items():
        got=xval(case,key)
        if got.upper()!=value.upper():raise Stop(f"{site}: {key}={got!r}, expected {value!r}")
    if xval(case,"MPILIB").lower()!="openmpi":raise Stop(f"{site}: unexpected MPILIB")
    for component in ("ATM","LND","CPL"):
        for key in (f"NTASKS_{component}",f"NTHRDS_{component}"):
            if xval(case,key)!="1":raise Stop(f"{site}: {key} must be 1")
    exe=Path(xval(case,"EXEROOT"))/"cesm.exe"
    if not exe.is_file():raise Stop(f"{site}: compiled executable missing {exe}")
    for f in SCI:
        if (case/f).is_symlink():raise Stop(f"{site}: science input symlink {f}")
    candidates=sorted((p.name for p in archive.iterdir()
                       if p.is_dir() and re.fullmatch(r"\d{4}-01-01-00000",p.name)),reverse=True)
    if not candidates:raise Stop(f"{site}: no archived restart")
    stamp=candidates[0]
    done=int(stamp[:4])-start
    if done<5 or done%5 or done>target:raise Stop(f"{site}: invalid checkpoint {stamp} = {done}y")
    if (target-done)%5:raise Stop(f"{site}: target {target} incompatible with 5y segments")
    refs={}
    for comp,kind in PARTS.items():
        filename=f"{name}.{kind}.{stamp}.nc"
        nc=archive/stamp/filename
        ptr=archive/stamp/f"rpointer.{comp}.{stamp}"
        if pointer(ptr)!=filename or not validnc(nc):
            raise Stop(f"{site}: latest archive checkpoint incomplete: {comp} {stamp}")
        refs[comp]=dict(src=str(nc),dst=str(run_dir/filename),ptr=str(run_dir/("rpointer."+comp)),name=filename,sha=filehash(nc))
    # Stop if ANY newer unarchived restart exists: do not roll back model state.
    for comp,kind in PARTS.items():
        for p in run_dir.glob(f"{name}.{kind}.*.nc"):
            m=re.search(r"(\d{4}-\d\d-\d\d-\d{5})\.nc$",p.name)
            if m and m.group(1)>stamp:
                raise Stop(f"{site}: newer run restart {p.name}: review before any change")
    # Also stop when newer history exists: avoid changing state with unsaved progress.
    for p in run_dir.glob(f"{name}.clm2.h*.nc"):
        m=re.search(r"\.(\d{4})-\d\d-",p.name)
        if m and int(m.group(1))>=int(stamp[:4]):
            raise Stop(f"{site}: unarchived history {p.name}; review before any change")
    status=(case/"CaseStatus").read_text(errors="replace")
    submits=list(re.finditer(r"case\.submit success",status))
    archives=list(re.finditer(r"st_archive success",status))
    if not submits or not archives or archives[-1].start()<submits[-1].start():
        raise Stop(f"{site}: CaseStatus has an unarchived/newer submission, not safe to reuse")
    config_resubmit=int(xval(case,"RESUBMIT"))
    if config_resubmit!=0:
        raise Stop(f"{site}: RESUBMIT={config_resubmit} still nonzero: existing continuation may be blocked/unfinished; inspect it instead of overwriting")
    if "srun --mpi=pmix" not in xval(case,"MPI_RUN_COMMAND"):
        raise Stop(f"{site}: MPI_RUN_COMMAND not proven PMIx srun; review before modification")
    remaining=(target-done)//5
    info=dict(site=site,name=name,case=str(case),run=str(run_dir),stamp=stamp,
              archived_years=done,target=target,segments_left=remaining,
              resubmit=max(0,remaining-1),refs=refs,
              science_sha={f:filehash(case/f) for f in SCI},
              casestatus_sha=filehash(case/"CaseStatus"),
              env_run_sha=filehash(case/"env_run.xml"))
    return info

def backup_and_copy(src,dst):
    dst=Path(dst);src=Path(src)
    if dst.is_symlink():raise Stop(f"Refusing symlink destination: {dst}")
    fd,tmp=tempfile.mkstemp(prefix=".continuation_",dir=dst.parent)
    os.close(fd)
    try:
        shutil.copy2(src,tmp);os.replace(tmp,dst)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def prepare(site):
    d=checkpoint(site)
    if d["segments_left"]==0:raise Stop(f"{site}: already reached target")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    session=HOME/"CLM_FATES_high_volatility_extensions"/f"{stamp}_{site}"
    session.mkdir(parents=True,exist_ok=False)
    case=Path(d["case"]);run_dir=Path(d["run"])
    originals=session/"original_files";originals.mkdir()
    for f in BACKUP:
        if (case/f).is_file():shutil.copy2(case/f,originals/f)
    original_run=session/"original_run_pointers";original_run.mkdir()
    for comp in PARTS:
        dst=run_dir/("rpointer."+comp)
        if dst.exists():shutil.copy2(dst,original_run/dst.name)
    (session/"CHECKPOINT_INSPECT.json").write_text(json.dumps(d,indent=2)+"\n")
    for comp,ref in d["refs"].items():
        dst=Path(ref["dst"]);src=Path(ref["src"])
        if dst.exists() and filehash(dst)!=ref["sha"]:
            raise Stop(f"{site}: checkpoint-named run restart differs from archive: {dst}; inspect manually")
        if not dst.exists():backup_and_copy(src,dst)
        if filehash(dst)!=ref["sha"]:raise Stop(f"{site}: staged restart hash mismatch {comp}")
    for comp,ref in d["refs"].items():
        ptr=Path(ref["ptr"])
        fd,tmp=tempfile.mkstemp(prefix=".rpointer_",dir=ptr.parent)
        with os.fdopen(fd,"w") as f:f.write(ref["name"]+"\n")
        os.replace(tmp,ptr)
        if pointer(ptr)!=ref["name"]:raise Stop(f"{site}: active pointer mismatch {comp}")
    run(["./xmlchange",f"RESUBMIT={d['resubmit']}"],case)
    if xval(case,"RESUBMIT")!=str(d["resubmit"]):raise Stop(f"{site}: RESUBMIT change failed")
    for f,sha in d["science_sha"].items():
        if filehash(case/f)!=sha:raise Stop(f"{site}: scientific input changed {f}")
    preview=run(["./preview_run"],case)
    (session/"preview_run.log").write_text(preview+"\n")
    if "srun --mpi=pmix" not in preview:
        raise Stop(f"{site}: preview_run lacks expected PMIx launcher")
    d["prepared_sha"]={f:filehash(case/f) for f in SCI+("CaseStatus","env_run.xml")}
    (session/"PREPARED.json").write_text(json.dumps(d,indent=2)+"\n")
    print(f"PREPARED {site}, target={d['target']} from {d['archived_years']} years; NO JOB SUBMITTED")
    print("SESSION",session)
    print(f"NEXT: python {Path(__file__).resolve()} submit {site} {session}")

def submit(site,session):
    session=Path(session).expanduser().resolve()
    canonical=HOME/"CLM_FATES_high_volatility_extensions"
    if session.parent!=canonical or session.name.split("_")[-1]!=site:
        raise Stop("Unexpected session path; use exact SESSION output from prepare")
    prepared=session/"PREPARED.json"
    if not prepared.is_file():raise Stop("No prepared manifest")
    info=json.loads(prepared.read_text())
    if info["site"]!=site:raise Stop("Session/site mismatch")
    case=Path(info["case"]);run_dir=Path(info["run"])
    if queue(info["name"]):raise Stop("New run/archive Slurm job appeared; refusing submit")
    if xval(case,"RESUBMIT")!=str(info["resubmit"]):
        raise Stop("Case RESUBMIT differs from prepared manifest")
    for f,sha in info["prepared_sha"].items():
        if filehash(case/f)!=sha:raise Stop("Case changed since prepare: "+f)
    for comp,ref in info["refs"].items():
        if pointer(Path(ref["ptr"]))!=ref["name"] or filehash(Path(ref["dst"]))!=ref["sha"]:
            raise Stop("Staged restart changed since prepare: "+comp)
    current_stamp=sorted(p.name for p in (OUT/"archive"/info["name"]/"rest").iterdir()
                         if p.is_dir() and re.fullmatch(r"\d{4}-01-01-00000",p.name))[-1]
    if current_stamp!=info["stamp"]:raise Stop("Archived checkpoint changed since prepare")
    flag=session/"SUBMIT_ATTEMPTED"
    with flag.open("x") as f:f.write(datetime.now(timezone.utc).isoformat()+"\n")
    p=subprocess.run(["./case.submit"],cwd=case,text=True,capture_output=True,timeout=240)
    (session/"case_submit.log").write_text(p.stdout+"\n"+p.stderr+f"\nRETURN_CODE={p.returncode}\n")
    if p.returncode:raise Stop("CIME submission failed; inspect case_submit.log; DO NOT retry blindly")
    print(f"SUBMITTED {site}. This means only that CIME accepted the first segment, NOT that it completed.")
    print("LOG",session/"case_submit.log")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("inspect","prepare","submit"))
    parser.add_argument("site",nargs="?",choices=tuple(SITES))
    parser.add_argument("session",nargs="?")
    args=parser.parse_args()
    if run(["id","-un"])!=USER:raise Stop("Wrong IRIDIS user")
    if args.mode=="inspect":
        for site in (args.site,) if args.site else SITES:
            try:
                info=checkpoint(site)
                print("READY",site,f"archived={info['archived_years']}, target={info['target']}, "
                      f"segments={info['segments_left']}, resubmit={info['resubmit']}")
            except Stop as e:print("BLOCKED",site,str(e))
    elif args.mode=="prepare":
        if not args.site or args.session:parser.error("prepare SITE only")
        prepare(args.site)
    else:
        if not args.site or not args.session:parser.error("submit SITE SESSION required")
        submit(args.site,args.session)

if __name__=="__main__":
    try:main()
    except (Stop,OSError,ValueError,subprocess.TimeoutExpired) as e:
        print("STOP:",e,file=sys.stderr);sys.exit(2)

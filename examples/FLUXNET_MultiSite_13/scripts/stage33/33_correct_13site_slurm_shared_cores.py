#!/usr/bin/env python3
"""Correct Stage31 mistaken node-exclusive submissions to shared-node, distinct Slurm cores.

--audit (default): READ ONLY.  --apply: first validate ALL 26 initial jobs are
PENDING, then cancel ONLY those 26, patch ONLY those 13 case configs, and
resubmit using CIME (NOT sbatch directly).  Never touch existing other jobs.

This is a correction for IRIDIS6 Stage31's --batch-args=--exclusive mistake,
not a new model setup or a change in MET/DATM/1000-year parameters.
"""
from __future__ import annotations
import argparse
import configparser
import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

USER_ID='ly3n24'
CASES=Path('/iridisfs/scratch/ly3n24/CLM_FATES/cases')
SITES=['DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR','FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor']
SUFFIX='_FATES_SPINUP1000_S30EXCL'
INITIAL_FIRST_RUN=4396937


def run(args,cwd=None,check=True):
    p=subprocess.run([str(x) for x in args],cwd=cwd,stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
    if check and p.returncode:
        raise RuntimeError(f'Failed {args}, rc={p.returncode}:\n{p.stdout[-1500:]}')
    return p.stdout


def require(ok,message):
    if not ok: raise RuntimeError(message)


def prepare_xml_edit(content,where):
    """Remove ONLY an XML directive whose sole payload is --exclusive."""
    lines=content.splitlines(keepends=True)
    result=[]
    n=0
    for line in lines:
        if '--exclusive' not in line:
            result.append(line);continue
        # No removal of unrelated scheduler arguments, comments or other text.
        if re.fullmatch(r'\s*<([\w:-]+)(?:\s+[^>]*)?>\s*(?:#SBATCH\s+)?--exclusive\s*</\1>\s*',line.strip()):
            n+=1
            continue
        raise RuntimeError(f'{where}: unrecognized --exclusive XML entry. Aborting before cancel. Line={line!r}')
    candidate=''.join(result)
    ET.fromstring(candidate)
    return candidate,n


def prepare_submit_options(content,where):
    if '--exclusive' not in content: return content
    cp=configparser.RawConfigParser()
    cp.read_string(content)
    require(cp.has_section('SubmitOptions'),f'{where}: unexpected .submit_options format')
    val=cp.get('SubmitOptions','batch_args',fallback='')
    require(val.strip()=='--exclusive',f'{where}: cannot safely edit mixed batch_args={val!r}')
    # Retain unrelated config keys. Text edit avoids changing CIME's formatting.
    replacement=[]
    hit=0
    for line in content.splitlines(keepends=True):
        if re.match(r'^\s*batch_args\s*=',line,re.I):
            replacement.append(re.sub(r'^([ \t]*batch_args\s*=).*(\r?\n)?$',
                lambda m:m.group(1)+'\n',line))
            hit+=1
        else:replacement.append(line)
    require(hit==1,f'{where}: expected exactly one batch_args= line')
    new=''.join(replacement)
    require('--exclusive' not in new,f'{where}: --exclusive remained')
    return new


def status(jobid,case):
    state=run(['squeue','-h','-j',str(jobid),'-o','%T']).strip().splitlines()
    require(len(state)==1 and state[0]=='PENDING',
        f'Job {jobid} not safely PENDING: {state!r}; do NOT cancel running work')
    info=run(['scontrol','show','job',str(jobid),'-o'])
    require(str(case) in info,f'Job {jobid} not proven to belong to {case}; abort')
    return state[0]


def xml_value(case,key):
    return run(['./xmlquery',key,'--value'],cwd=case).strip().splitlines()[-1].strip()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--audit',action='store_true',help='Read-only validation (default)')
    ap.add_argument('--apply',action='store_true',help='Cancel ONLY initial 13 run/archive pairs and resubmit on separate allocated cores')
    a=ap.parse_args()
    require(not (a.audit and a.apply),'Choose --audit or --apply')
    require(os.environ.get('USER')==USER_ID, f'Expected user {USER_ID}')
    require(shutil.which('squeue') and shutil.which('scontrol') and shutil.which('scancel'),
        'Run this on the IRIDIS6 login node')
    staged=[]
    print('=== READ-ONLY PREFLIGHT 13 CASES / 26 INITIAL JOBS ===',flush=True)
    for i,site in enumerate(SITES):
        case=CASES/(site+SUFFIX)
        require(case.is_dir() and (case/'case.submit').exists(),f'Missing case {case}')
        start=INITIAL_FIRST_RUN+2*i
        archive=start+1
        status(start,case);status(archive,case)
        require(xml_value(case,'RESUBMIT')=='199',f'{site} RESUBMIT already changed; first segment may have run')
        require(xml_value(case,'STOP_N')=='5',f'{site} STOP_N changed')
        require(xml_value(case,'CONTINUE_RUN').upper()=='FALSE',f'{site}: already continuing')
        cs=(case/'CaseStatus').read_text(errors='replace')
        require(not re.search('case.run starting|case.run success|model execution starting|model execution success',cs,re.I),
            f'{site}: model seems to have started; do not alter')
        envfile=case/'env_batch.xml'
        require(envfile.is_file(),f'Missing {envfile}')
        envnew,n=prepare_xml_edit(envfile.read_text(),envfile)
        opts=case/'.submit_options'
        require(opts.is_file(),f'Missing {opts}')
        optnew=prepare_submit_options(opts.read_text(),opts)
        require('--exclusive' not in optnew,f'{site}: exclusive persists in options')
        old_run=(case/'.case.run').read_text(errors='replace')
        # CIME normally defines resource allocation in env_batch / generated scripts.
        # Re-generated .case.run must be rechecked after case.setup --reset.
        print(f'{site:7} run={start} archive={archive} PENDING, '
              f'env_batch exclusive removed={n}, submit_options fixed={optnew!=opts.read_text()}, '
              f'generated_script_exclusive={"--exclusive" in old_run}',flush=True)
        staged.append(dict(site=site,case=case,run=start,archive=archive,
                           envfile=envfile,envnew=envnew,opts=opts,optnew=optnew))
    print('ALL 13 SAFETY CHECKS PASS: no running model or non-Stage31 Slurm job selected')
    if not a.apply:
        print('READ ONLY. To correct these pending initial submissions: --apply')
        return
    backup=Path.home()/('FLUXNET13_stage31_shared_core_fix_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True,exist_ok=False)
    # Capture original XML/scripts/options BEFORE cancellations for rollback/audit.
    for entry in staged:
        case=entry['case'];dst=backup/entry['site'];dst.mkdir()
        for name in ['env_batch.xml','.submit_options','.case.run','case.st_archive','env_mach_pes.xml']:
            if (case/name).is_file():shutil.copy2(case/name,dst/name.lstrip('.'))
    (backup/'README.txt').write_text('Original config snapshots for exact 13 Stage31 cases. '
          'Previous Slurm job IDs 4396937..4396962 were pending. No changes '
          'to meteorology, model restart state or other running jobs.\n')
    # Second state gate immediately before cancellation, then cancel explicit IDs only.
    for entry in staged:
        status(entry['run'],entry['case']);status(entry['archive'],entry['case'])
    ids=[str(j) for e in staged for j in (e['run'],e['archive'])]
    print('CANCEL ONLY 26 INITIAL PENDING JOBS:', ' '.join(ids),flush=True)
    run(['scancel',*ids])
    # Reconfigure and resubmit via CIME, preserving automatic 199 resubmits.
    for i,e in enumerate(staged,1):
        site=e['site'];case=e['case']
        print(f'[{i}/13] FIX AND RESUBMIT {site}',flush=True)
        e['envfile'].write_text(e['envnew'])
        e['opts'].write_text(e['optnew'])
        out=run(['./case.setup','--reset'],cwd=case)
        (backup/site/'case.setup.reset.log').write_text(out)
        for name in ('.case.run','case.st_archive'):
            script=case/name
            require(script.exists(),f'{site}: {name} not regenerated')
            require('--exclusive' not in script.read_text(errors='replace'),
                f'{site}: {name} still has --exclusive. Manual case batch config review required.')
        require('--exclusive' not in e['envfile'].read_text() and
                '--exclusive' not in e['opts'].read_text(),
                f'{site}: exclusive still appears in CIME config')
        # Check site MPI/OMP count is one core; no blind change to model physics.
        for k in ('NTASKS_CPL','NTHRDS_CPL'):
            v=xml_value(case,k)
            require(v=='1',f'{site}: {k}={v}, not one core; stop to avoid CPU contention')
        out=run(['./case.submit'],cwd=case)
        (backup/site/'resubmit.log').write_text(out)
        require('Submitted job case.run with id' in out,
                f'{site}: CIME did not confirm new case.run job ID')
        require('--exclusive' not in out and '--exclusive' not in e['opts'].read_text(),
                f'{site}: --exclusive persists in new submit/options; STOP')
        print(' '.join(re.findall(r'Submitted job (?:case\.run|case\.st_archive) with id \d+',out)),flush=True)
    print('\n=== COMPLETE: 13 Stage31 CASES REQUEUED TO SHARED-NODE SLURM ===')
    print('Original 26 PENDING job IDs cancelled; new CIME job IDs created.')
    print('New jobs may coexist on one node, but Slurm assigns distinct cores.')
    print('Backup / submit logs:',backup)
    print('Inspect: squeue -u ly3n24 -o "%.18i %.32j %.2t %.8C %.8D %.20R"')


if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STOP:',type(e).__name__,str(e),file=sys.stderr,flush=True)
        sys.exit(1)

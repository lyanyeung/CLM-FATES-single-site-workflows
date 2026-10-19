#!/usr/bin/env python3
"""Stage35: repair 13 EXISTING, prepared Stage34 S30SHARED CIME cases.

Audit (default): read-only preflight and show exact Slurm --exclusive directives.
Apply: remove exclusive-node directives from ONLY the 13 prepared CIME cases,
       preserve timestamped backups, verify ALL 13 before submitting ANY,
       then submit each case once by ./case.submit (no batch args).

Never cancels jobs, reruns Stage34, rebuilds, deletes run/archive, touches other
cases, or modifies global CTSM batch templates. No implicit retries.

Intended for the Stage34 failure immediately after ALL_13_PREPARED, before any
S30SHARED initial job had been submitted. ABORTS on unknown/running cases.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import fcntl
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

UID = "ly3n24"
CASE_ROOT = Path(f"/iridisfs/scratch/{UID}/CLM_FATES/cases")
MANIFEST = Path(f"/iridisfs/scratch/{UID}/CLM_FATES/experiments/FLUXNET_13_ZBOT_DATM_STAGE30_20261018_055940_1008203/reports/04_consolidated_13site_271_DATM_SHA256_manifest.csv")
SITES = (
    "DE-Lnf", "DE-Obe", "ES-Agu", "ES-LJu", "IT-Col", "DE-Gri", "DE-RuR",
    "FI-Hyy", "FI-Let", "FR-Pue", "GF-Guy", "IT-MBo", "IT-Tor"
)
SUFFIX = "_FATES_SPINUP1000_S30SHARED"
OLD_SUFFIX = "_FATES_SPINUP1000_S30EXCL"
FILES = (".case.run", "case.st_archive", "env_batch.xml", ".submit_options")
EXCL = re.compile(r"(?<![A-Za-z0-9_-])--exclusive(?:=(?:user|mcs|topo))?(?![A-Za-z0-9_=-])")
STATES = re.compile(r"case\.submit success|model execution starting|case\.run starting", re.I)


def insist(x, message):
    if not x:
        raise RuntimeError(message)


def run(args, cwd=None, check=True):
    p = subprocess.run(list(map(str,args)), cwd=cwd, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"{' '.join(map(str,args))} failed ({p.returncode}):\n{(p.stdout+p.stderr)[-1600:]}")
    return p


def xml(case, key):
    p = run(["./xmlquery", key, "--value"], cwd=case)
    x = p.stdout.strip().splitlines()
    return x[-1].strip() if x else ""


def in_queue():
    p = run(["squeue", "--noheader", "-u", UID, "-o", "%i|%j|%T"])
    active=[]
    target={"run."+s+SUFFIX for s in SITES}|{"st_archive."+s+SUFFIX for s in SITES}
    old={"run."+s+OLD_SUFFIX for s in SITES}|{"st_archive."+s+OLD_SUFFIX for s in SITES}
    for line in p.stdout.splitlines():
        parts=line.split("|", 2)
        if len(parts)!=3: continue
        job, name, state=(k.strip() for k in parts)
        if name in target or name in old:
            active.append((job,name,state))
    return active


def plan_edit(path:Path, text:str):
    """Return (new_text, changed_lines); refuse unknown exclusive uses."""
    if '--exclusive' not in text:
        return text, []
    if path.name in ('.case.run', 'case.st_archive'):
        out=[]; changes=[]
        for number,line in enumerate(text.splitlines(keepends=True), 1):
            if '--exclusive' not in line:
                out.append(line)
                continue
            if line.lstrip().startswith('#SBATCH'):
                original=line.rstrip('\r\n')
                # Remove the exact, standalone Slurm argument, not general content.
                if not EXCL.search(original):
                    raise RuntimeError(f'{path}:{number}: unsupported exclusive option: {original}')
                new=EXCL.sub('',original).rstrip()
                if '--exclusive' in new:
                    raise RuntimeError(f'{path}:{number}: another exclusive token remains')
                if new.strip()=='#SBATCH':
                    changes.append((number, original, '<REMOVE DIRECTIVE>'))
                    continue
                changes.append((number,original,new))
                out.append(new + ('\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''))
            else:
                raise RuntimeError(f'{path}:{number}: --exclusive outside an #SBATCH directive: {line.strip()}')
        result=''.join(out)
    elif path.name in ('env_batch.xml','.submit_options'):
        # These are case-local CIME settings. The only alteration is removing
        # standalone --exclusive flags; never replace other resource settings.
        if '--exclusive' in text and not EXCL.search(text):
            raise RuntimeError(f'{path}: exclusive occurrence is not a standalone supported flag')
        result=EXCL.sub('',text)
        changes=[(0, 'standalone --exclusive', '<REMOVED FROM CASE-LOCAL CIME OPTIONS>')]
        if path.name=='env_batch.xml':
            ET.fromstring(result)  # refuse malformed XML
    else:
        raise RuntimeError(f'Unexpected path: {path}')
    insist('--exclusive' not in result, f'{path}: exclusive remains after patch')
    return result,changes


def slurm_allocation_sane(path, content):
    # Validate that the scripts are not using node exclusivity by another
    # route or requesting all available CPUs with memory=0.
    bad=[]
    for i,line in enumerate(content.splitlines(),1):
        if not line.lstrip().startswith('#SBATCH'):
            continue
        if re.search(r'--oversubscribe\b|--overcommit\b',line):
            bad.append(f'{path}:{i}: explicit overcommit/oversubscribe')
        if re.search(r'--(?:mem|mem-per-cpu)(?:=|\s+)0(?:\s|$)',line):
            bad.append(f'{path}:{i}: mem=0 reserves full node memory')
        for expr in (r'--ntasks(?:=|\s+)(\d+)',r'--ntasks-per-node(?:=|\s+)(\d+)',r'--cpus-per-task(?:=|\s+)(\d+)',r'(?<!\S)-n\s*(\d+)',r'(?<!\S)-c\s*(\d+)'):
            m=re.search(expr,line)
            if m and int(m.group(1))>1:
                bad.append(f'{path}:{i}: CPU allocation asks for {m.group(1)} (>1): {line.strip()}')
    insist(not bad, '\n'.join(bad))


def check_manifest():
    insist(MANIFEST.is_file(),f'Missing Stage30 manifest: {MANIFEST}')
    with MANIFEST.open(newline='') as f:
        reader=csv.DictReader(f)
        insist({'site','year','datm_nc','sha256'}<=set(reader.fieldnames or ()), 'Stage30 manifest columns mismatch')
        records=list(reader)
    insist(len(records)==271 and {r['site'] for r in records}==set(SITES), 'Stage30 manifest no longer matches 271 files/13 sites')
    insist(all(Path(r['datm_nc']).is_file() for r in records), 'A selected DATM file is missing; do not submit')
    return records


def preflight():
    insist(os.environ.get('USER')==UID, 'Wrong IRIDIS account; refusing')
    insist(shutil.which('squeue') and shutil.which('sbatch'), 'Slurm commands unavailable')
    check_manifest()
    active=in_queue()
    for job,name,state in active:
        print('ACTIVE_CONFLICT',job,state,name,flush=True)
    insist(not active,'S30SHARED or old S30EXCL jobs found in Slurm; do not duplicate a run. No jobs canceled.')
    prepared={}; edits={}; total_lines=0
    for site in SITES:
        case=CASE_ROOT/(site+SUFFIX)
        insist(case.is_dir() and (case/'xmlquery').is_file(),f'{site}: Stage34 prepared case missing: {case}')
        status=case/'CaseStatus'
        insist(status.is_file(),f'{site}: CaseStatus missing')
        s=status.read_text(errors='replace')
        insist(not STATES.search(s),f'{site}: a case was previously submitted/started; refuse duplicate')
        for key,want in [('STOP_N','5'),('REST_N','5'),('RESUBMIT','199'),('ATM_NCPL','48'),('BUILD_COMPLETE','TRUE'),('NTASKS_CPL','1'),('NTHRDS_CPL','1')]:
            have=xml(case,key)
            insist(have.upper()==want.upper(),f'{site}: {key}={have}, expected {want}')
        insist(xml(case,'RUN_TYPE').lower()=='startup',f'{site}: RUN_TYPE not startup')
        insist(xml(case,'CLM_CO2_TYPE').lower()=='constant',f'{site}: CO2 not fixed')
        insist((case/'CaseDocs/lnd_in').is_file(),f'{site}: lnd_in missing')
        stream=(case/'user_nl_datm_streams').read_text(errors='replace')
        insist('taxmode = cycle' in stream and 'ZBOT Sa_z' in stream and 'PRECTmms Faxa_precn' in stream,
               f'{site}: DATM stream setup invalid')
        insist((case/'.case.run').is_file() and (case/'case.st_archive').is_file(),f'{site}: .case.run or archive missing')
        edited=[]
        for name in FILES:
            path=case/name
            if not path.is_file():continue
            raw=path.read_text(errors='replace')
            result,changes=plan_edit(path,raw)
            if name in ('.case.run','case.st_archive'):
                slurm_allocation_sane(path,result)
            if changes: edited.append((path,raw,result,changes));total_lines+=len(changes)
        edits[site]=edited
        prepared[site]=case
        pretty=[f'{p.name}:{len(c)}' for p,_,_,c in edited]
        print(f'PREPARED {site:<7s} casesafe=YES exclusivity_fixes={",".join(pretty) if pretty else "NONE"}',flush=True)
    print(f'PREFLIGHT_OK: 13 unsubmitted cases; {total_lines} exclusive directives/options to remove; no Slurm jobs canceled',flush=True)
    return prepared,edits


def write_atomic(path,text):
    original_mode=path.stat().st_mode
    fd,temp=tempfile.mkstemp(prefix='.stage35.',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as f:
            f.write(text)
            f.flush();os.fsync(f.fileno())
        os.chmod(temp, original_mode & 0o777)
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def apply(prepared,edits):
    stamp=dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    backs=[]
    try:
        for site in SITES:
            for path,original,updated,changes in edits[site]:
                back=path.with_name(path.name+f'.stage35_before_shared_fix_{stamp}.bak')
                insist(not back.exists(),f'Backup path exists: {back}')
                shutil.copy2(path,back)
                backs.append((path,back))
                write_atomic(path,updated)
                print(f'FIXED {site:<7s} {path.name}: {len(changes)} change(s); backup {back.name}',flush=True)
        # Confirm ALL cases before any sbatch/CIME action.
        for site in SITES:
            case=prepared[site]
            for name in FILES:
                p=case/name
                if p.is_file():
                    insist('--exclusive' not in p.read_text(errors='replace'),f'{site}: exclusive remains: {p}')
            insist(not STATES.search((case/'CaseStatus').read_text(errors='replace')),
                   f'{site}: case state changed during patch')
        insist(not in_queue(),'Stage31/34 jobs appeared during pre-submit verification')
    except Exception:
        print('PATCH_FAILURE: reverting backups; NOTHING submitted yet',file=sys.stderr,flush=True)
        for path,back in reversed(backs):
            shutil.copy2(back,path)
        raise
    print('ALL_13_PATCHED_AND_VALIDATED: safe to start initial submissions',flush=True)
    report=Path.home()/('FLUXNET_13_stage35_submission_'+stamp+'.tsv')
    with report.open('x',encoding='utf-8') as f:
        f.write('site\tcase\tjobid\tstatus\n')
    print('SUBMISSION_MANIFEST:',report,flush=True)
    done=0
    for site in SITES:
        case=prepared[site]
        print(f'SUBMITTING {done+1}/13 {site} using ./case.submit (NO --exclusive)',flush=True)
        p=run(['./case.submit'],cwd=case,check=False)
        log=report.with_name(report.stem+'_'+site+'_submit.log')
        log.write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
        job=re.search(r'Submitted job case\.run with id\s+(\d+)',p.stdout)
        bad=(p.returncode!=0 or '--exclusive' in (p.stdout+p.stderr) or not job)
        with report.open('a',encoding='utf-8') as f:
            f.write(f'{site}\t{case}\t{job.group(1) if job else ""}\t{("FAILED_NEEDS_REVIEW" if bad else "SUBMITTED_SHARED") }\n')
        if bad:
            print(f'STOP: {site} submission failed or exclusive reappeared; earlier submissions NOT canceled. LOG: {log}',file=sys.stderr,flush=True)
            raise RuntimeError(f'{site}: unexpected case.submit behaviour rc={p.returncode}; see {log}')
        done+=1
        print(f'  SUBMITTED {site} job={job.group(1)}',flush=True)
    print('=== STAGE35 ALL 13 FIRST SEGMENTS SUBMITTED ===',flush=True)
    print('SUBMISSION_MANIFEST:',report,flush=True)
    print('Already running model years: UNKNOWN; target 1000 years/site; check restart and archive.',flush=True)
    q=run(['squeue','-u',UID,'-o','%.18i %.35j %.2t %.8C %.10D %.20R'],check=False)
    print(q.stdout[-8000:],flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--audit',action='store_true',help='READ ONLY, check prepared cases and patch plan')
    m.add_argument('--apply',action='store_true',help='Fix 13 prepared cases in place; submit all first segments')
    a=p.parse_args()
    insist(CASE_ROOT.is_dir(),'Case root not found')
    lock=CASE_ROOT/'.stage35_shared_repair_and_submit.lock'
    with lock.open('a+') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        prepared,edits=preflight()
        if a.audit:
            print('READ_ONLY_AUDIT_OK: NOTHING CHANGED OR SUBMITTED',flush=True)
            return
        apply(prepared,edits)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STAGE35 ERROR:',type(e).__name__,str(e),file=sys.stderr,flush=True)
        sys.exit(1)

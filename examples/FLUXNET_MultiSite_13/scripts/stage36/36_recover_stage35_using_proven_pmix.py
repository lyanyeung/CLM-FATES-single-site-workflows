#!/usr/bin/env python3
"""Stage36: safely recover the thirteen PREPARED S30SHARED cases.

Based on tested 8-site shared-node/PMIx and 11-site Stage17/18 scripts.
--audit: READ ONLY, display queue, source of previous Stage35 result,
         CaseStatus evidence and Slurm resource configuration.
--run:   never cancel; skip cases with ANY credible evidence of a prior
         submission; repair only clearly UNSUBMITTED cases from env_batch.xml,
         regenerate with CIME case.setup --reset, validate ALL remaining cases,
         and submit remaining once. Stops on any ambiguity rather than duplicate.

Do NOT run Stage31, Stage33, Stage34, or Stage35 again.
No changes to MET, DATM, surface, restart, archive, or other case families.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import fcntl
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

USER = 'ly3n24'
ROOT = Path(f'/iridisfs/scratch/{USER}/CLM_FATES/cases')
HOME = Path(f'/iridisfs/home/{USER}')
SUFFIX = '_FATES_SPINUP1000_S30SHARED'
SITES = ('DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR',
         'FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor')
MPI_CMD = 'srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
SOURCE = ROOT/'GF-Guy_FATES_SURF2000_CO2405_1PT'
SUBMITTED = re.compile(r'case\.submit success|case\.run (starting|success)|model execution (starting|success)|st_archive success',re.I)
RUN_ID = re.compile(r'(?:Submitted job case\.run with id\s+|Submitted job id is\s+)(\d+)',re.I)
BATCH = ('--nodes=1','--ntasks-per-node=1','--cpus-per-task=1','--mem=8G')

class Stop(RuntimeError): pass

def require(cond,msg):
    if not cond: raise Stop(msg)

def cmd(argv,cwd=None,allow=False):
    p=subprocess.run(list(map(str,argv)),cwd=cwd,text=True,capture_output=True)
    if p.returncode and not allow:
        raise Stop(f'{argv} rc={p.returncode}: {(p.stdout+p.stderr)[-1800:]}')
    return p

def xval(case,key):
    p=cmd(['./xmlquery',key,'--value'],cwd=case)
    return p.stdout.strip().splitlines()[-1].strip() if p.stdout.strip() else ''

def queue():
    p=cmd(['squeue','-h','-u',USER,'-o','%i|%j|%T'])
    names={f'{kind}.{site}{SUFFIX}' for site in SITES for kind in ('run','st_archive')}
    found={site:[] for site in SITES}
    for line in p.stdout.splitlines():
        v=[x.strip() for x in line.split('|',2)]
        if len(v)!=3: continue
        jid,name,state=v
        if name not in names: continue
        site=next(s for s in SITES if name.endswith(s+SUFFIX))
        # Verify Slurm work really belongs to THIS case; no matching-name accident.
        info=cmd(['scontrol','show','job',jid,'-o'],allow=True)
        if info.returncode==0:
            require(str(ROOT/(site+SUFFIX)) in info.stdout,
                    f'Job {jid} name matches {site} but path does not; STOP')
        found[site].append((jid,name,state,info.stdout.strip()))
    return found

def old_submit_log(site):
    if site!='DE-Lnf': return None
    matches=sorted(HOME.glob('FLUXNET_13_stage35_submission_*_DE-Lnf_submit.log'))
    return matches[-1] if matches else None

def review_state(site,jobs):
    case=ROOT/(site+SUFFIX)
    require(case.is_dir() and (case/'case.submit').is_file(),f'{site}: missing prepared CIME case')
    status=(case/'CaseStatus').read_text(errors='replace') if (case/'CaseStatus').exists() else ''
    if SUBMITTED.search(status): return 'ALREADY_SUBMITTED_CASESTATUS','CaseStatus',case
    if jobs: return 'ALREADY_SUBMITTED_SLURM',','.join(j[0] for j in jobs),case
    if (case/'.stage36_submit_attempt').exists():
        return 'UNCERTAIN_STAGE36_ATTEMPT','Stage36 prior attempt marker',case
    log=old_submit_log(site)
    if log:
        data=log.read_text(errors='replace')
        ids=RUN_ID.findall(data)
        if ids: return 'ALREADY_SUBMITTED_STAGE35_LOG',','.join(ids),case
        if re.search(r'\bsbatch\s+.*\.case\.run',data):
            return 'UNCERTAIN_STAGE35_SUBMISSION','Stage35 sbatch attempted; no verified run ID',case
        if data.strip():
            # rc=0 already known from Stage35; old log may use a different job-id format.
            return 'UNCERTAIN_STAGE35_LOG','read '+str(log),case
    return 'UNSUBMITTED','no queue/CaseStatus/submission-log evidence',case

def text_diff_planned(site,case):
    batch=case/'env_batch.xml'
    require(batch.is_file(),f'{site}: missing env_batch.xml')
    orig=batch.read_text()
    fixed,n=re.subn(r'(?m)^[ \t]*<directive>[ \t]*--exclusive[ \t]*</directive>[ \t]*\r?\n','',orig)
    require(n in (0,1,2),f'{site}: abnormal exclusive count={n}')
    require('--exclusive' not in fixed,f'{site}: unknown exclusive text in env_batch.xml')
    needle='<directive>--cpus-per-task={{ thread_count }}</directive>'
    require(fixed.count(needle)==1,f'{site}: expected one CIME cpus-per-task template')
    mem='<directive>--mem=8G</directive>'
    memory=re.findall(r'<directive>\s*--mem(?:=|\s).*?</directive>',fixed)
    if not memory: fixed=fixed.replace(needle,needle+'\n        '+mem,1)
    else: require(len(memory)==1 and memory[0]==mem,
                  f'{site}: unexpected memory specification {memory}; refuse overwrite')
    ET.fromstring(fixed)
    options=case/'.submit_options'
    if options.exists():
        require('--exclusive' not in options.read_text(errors='replace'),
                f'{site}: CIME .submit_options still requests --exclusive; manual review')
    return orig,fixed

def batch_ok(case,site):
    for fname,jobprefix in (('.case.run','run.'),('case.st_archive','st_archive.')):
        p=case/fname
        require(p.is_file(),f'{site}: missing {fname}')
        text=p.read_text(errors='replace')
        require('--exclusive' not in text,f'{site}: --exclusive persists in {fname}')
        for flag in BATCH:
            require(bool(re.search(r'^#SBATCH\s+'+re.escape(flag)+r'\s*$',text,re.M)),
                    f'{site}: {fname} missing {flag}; differs from successful 8/11 site setup')
        require(f'--job-name={jobprefix}{site}{SUFFIX}' in text,
                f'{site}: {fname} wrong Slurm job name')

def base_ok(site,case):
    for key,val in [('CASE',site+SUFFIX),('RUN_TYPE','startup'),('CONTINUE_RUN','FALSE'),
                    ('CALENDAR','NO_LEAP'),('ATM_NCPL','48'),('STOP_N','5'),('REST_N','5'),
                    ('RESUBMIT','199'),('BUILD_COMPLETE','TRUE'),('NTASKS_ATM','1'),
                    ('NTASKS_LND','1'),('NTASKS_CPL','1'),('NTHRDS_ATM','1'),
                    ('NTHRDS_LND','1'),('NTHRDS_CPL','1')]:
        actual=xval(case,key)
        require(actual.upper()==val.upper(),f'{site}: {key}={actual}, expected={val}')
    require(xval(case,'EXEROOT')==xval(SOURCE,'EXEROOT'),
            f'{site}: executable path differs from known GF-Guy binary')
    require((Path(xval(case,'EXEROOT'))/'cesm.exe').is_file(),f'{site}: cesm.exe missing')
    stream=(case/'user_nl_datm_streams').read_text(errors='replace')
    for token in ('taxmode = cycle','ZBOT Sa_z','PRECTmms Faxa_precn'):
        require(token in stream,f'{site}: DATM stream missing {token}')
    require((case/'CaseDocs/lnd_in').is_file(),f'{site}: land namelist not prepared')

def snapshot(case,out):
    out.mkdir(parents=True,exist_ok=False)
    for name in ('env_batch.xml','env_run.xml','env_mach_pes.xml','.case.run','case.st_archive',
                 'CaseStatus','user_nl_clm','user_nl_datm_streams'):
        p=case/name
        if p.exists(): shutil.copy2(p,out/name.lstrip('.'))

def repair_one(site,case,backup):
    base_ok(site,case)
    orig,fixed=text_diff_planned(site,case)
    snapshot(case,backup)
    if fixed!=orig: (case/'env_batch.xml').write_text(fixed)
    if xval(case,'MPI_RUN_COMMAND')!=MPI_CMD:
        cmd(['./xmlchange','MPI_RUN_COMMAND='+MPI_CMD],cwd=case)
    p=cmd(['./case.setup','--reset'],cwd=case)
    (backup/'case_setup_reset.log').write_text(p.stdout+'\n'+p.stderr)
    if xval(case,'BUILD_COMPLETE')!='TRUE':
        require((Path(xval(case,'EXEROOT'))/'cesm.exe').is_file(),f'{site}: executable missing')
        cmd(['./xmlchange','BUILD_COMPLETE=TRUE'],cwd=case)
    p=cmd(['./preview_namelists'],cwd=case)
    (backup/'preview_namelists.log').write_text(p.stdout+'\n'+p.stderr)
    p=cmd(['./check_input_data'],cwd=case)
    (backup/'check_input_data.log').write_text(p.stdout+'\n'+p.stderr)
    p=cmd(['./preview_run'],cwd=case)
    (backup/'preview_run.log').write_text(p.stdout+'\n'+p.stderr)
    require(MPI_CMD in p.stdout,f'{site}: preview_run not using proven PMIx launcher')
    base_ok(site,case)
    require(xval(case,'MPI_RUN_COMMAND')==MPI_CMD,f'{site}: MPI launcher reverted after reset')
    batch_ok(case,site)
    print('REPAIRED '+site+': 1 CPU, 8G, PMIx srun; CIME reset + preview passed',flush=True)


def campaign(mode):
    require(os.environ.get('USER')==USER,'Wrong login, refuse to alter any cases')
    require(SOURCE.is_dir(),'Missing known successful GF-Guy source case')
    require(shutil.which('squeue') and shutil.which('sbatch') and shutil.which('scontrol'),
            'Slurm tools missing')
    lock=ROOT/'.stage36_recover_shared_spinup.lock'
    with lock.open('a+') as fh:
        fcntl.flock(fh,fcntl.LOCK_EX|fcntl.LOCK_NB)
        jobs=queue()
        states={}
        print('=== S30SHARED CASES / SLURM ACTUAL STATE ===')
        for site in SITES:
            kind,detail,case=review_state(site,jobs[site])
            states[site]=(kind,detail,case)
            print(f'{site:<7s} {kind:<34s} {detail}',flush=True)
            for j in jobs[site]:
                flat=j[3]
                match=re.search(r'\b(?:Shared|OverSubscribe|NumCPUs|NumNodes|TRES|NodeList)=\S+',flat)
                print('  SLURM',j[0],j[2],match.group(0) if match else '(details in scontrol)',flush=True)
        firstlog=old_submit_log('DE-Lnf')
        if firstlog:
            d=firstlog.read_text(errors='replace')
            print('\n=== DE-Lnf STAGE35 REAL SUBMISSION OUTPUT ===')
            print('LOG:',firstlog)
            print('\n'.join(d.splitlines()[-45:]))
            print('PREVIOUS_STAGE35_SUCCESS_GUARD:',
                  'exclusive_string='+str('--exclusive' in d),
                  'CIME_job_id_match='+str(bool(re.search(r'Submitted job case\.run with id\s+(\d+)',d))),
                  flush=True)
        print('\n=== PREPARED CASE DIRECTIVES ===')
        for site in SITES:
            case=states[site][2]
            fn=case/'.case.run'
            if fn.is_file():
                flags=[x.strip() for x in fn.read_text(errors='replace').splitlines() if x.lstrip().startswith('#SBATCH')]
                print(site,','.join(x.replace('#SBATCH','').strip() for x in flags if any(k in x for k in ('exclusive','cpus','mem=','ntasks','nodes='))))
        if mode=='audit':
            print('\nAUDIT_FINISHED_NO_CHANGES. Do not duplicate any previously submitted case.')
            return
        uncertain=[s for s,(k,_,_) in states.items() if k.startswith('UNCERTAIN')]
        require(not uncertain,f'Ambiguous prior submit state at {uncertain}; STOP, no edits or new submissions')
        pending=[s for s,(k,_,_) in states.items() if k=='UNSUBMITTED']
        already=[s for s in SITES if s not in pending]
        print('Already submitted (will NOT touch):',','.join(already) or 'NONE',flush=True)
        print('Unsubmitted to repair/submit:',','.join(pending) or 'NONE',flush=True)
        if not pending:
            print('ALL CASES ALREADY SUBMITTED OR RUNNING; NOTHING TO DO')
            return
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
        backup=HOME/('FLUXNET_13_stage36_recovery_'+stamp)
        require(not backup.exists(),'Backup collision')
        backup.mkdir(parents=True)
        # Preflight every candidate before editing any.
        for s in pending:
            case=states[s][2]
            base_ok(s,case)
            text_diff_planned(s,case)
        print('ALL_UNSUBMITTED_PREFLIGHT_OK:',len(pending),flush=True)
        for s in pending:
            repair_one(s,states[s][2],backup/s)
        # Ensure the queue has not gained jobs during preparation.
        now=queue()
        for s in pending:
            require(not now[s],f'{s}: job appeared while preparing, refuse duplicate submit')
            k,info,_=review_state(s,now[s])
            require(k=='UNSUBMITTED',f'{s}: state became {k}, no submit')
            batch_ok(states[s][2],s)
        print('ALL_REPAIRED_UNSUBMITTED_VALIDATED. Starting CIME first submissions.',flush=True)
        manifest=backup/'submission_status.tsv'
        manifest.write_text('site\tstate\tjobid\tcomment\n')
        for s in already:
            with manifest.open('a') as f:f.write(f'{s}\tALREADY_SUBMITTED\t\tSKIPPED\n')
        for s in pending:
            case=states[s][2]
            # Recheck one last time before irreversible CIME submission.
            require(not queue()[s],f'{s}: new job in Slurm, STOP')
            k,info,_=review_state(s,[])
            require(k=='UNSUBMITTED',f'{s}: now {k}; STOP')
            marker=case/'.stage36_submit_attempt'
            marker.write_text('Submission attempted '+datetime.now().isoformat()+'; do not repeat without inspecting CaseStatus\n')
            p=cmd(['./case.submit'],cwd=case,allow=True)
            log=backup/s/'case_submit.log'
            log.write_text(p.stdout+'\n'+p.stderr)
            ids=RUN_ID.findall(p.stdout)
            actual_exclusive=bool(re.search(r'\bsbatch\b[^\n]*--exclusive',p.stdout+'\n'+p.stderr))
            opts=case/'.submit_options'
            if opts.is_file() and '--exclusive' in opts.read_text(errors='replace'):
                actual_exclusive=True
            have_status=bool(SUBMITTED.search((case/'CaseStatus').read_text(errors='replace')))
            queue_exists=bool(queue()[s])
            jobid=ids[0] if ids else ''
            state='SUBMITTED' if p.returncode==0 and (have_status or queue_exists or ids) and not actual_exclusive else 'UNKNOWN_CHECK_LOG'
            with manifest.open('a') as f:f.write(f'{s}\t{state}\t{jobid}\trc={p.returncode};exclusive_in_sbatch={actual_exclusive}\n')
            print(f'SUBMISSION {s}: {state} rc={p.returncode} run_id={jobid or "not printed"} exclusive={actual_exclusive}',flush=True)
            require(state=='SUBMITTED',f'{s}: ambiguous or exclusive Slurm submission; DO NOT REPEAT; inspect {log}')
        print('\n=== STAGE36 SUBMISSION VERIFIED ===')
        print('Previously submitted:',len(already),'new submitted:',len(pending),flush=True)
        print('NOTE: 1000 model years are a TARGET (200 x 5), not yet complete.')
        print('REPORT:',backup,flush=True)
        print(cmd(['squeue','-u',USER,'-o','%.18i %.38j %.2t %.8C %.8D %.20R'],allow=True).stdout[-12000:])

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    grp=ap.add_mutually_exclusive_group(required=True)
    grp.add_argument('--audit',action='store_true',help='READ ONLY; print real Stage35 submit log and all actual queue states')
    grp.add_argument('--run',action='store_true',help='Repair only unsubmitted cases and submit once with proven 1-core/8G/srun setup')
    args=ap.parse_args()
    try: campaign('run' if args.run else 'audit')
    except Exception as ex:
        print('STAGE36 STOP:',type(ex).__name__,ex,file=sys.stderr,flush=True)
        sys.exit(1)

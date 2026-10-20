#!/usr/bin/env python3
"""Safely resume existing FLUXNET_MultiSite_8 CIME spin-ups on IRIDIS6.

Usage: python3 THIS_SCRIPT inspect | prepare SITE | submit SESSION
       python3 THIS_SCRIPT list

Seven sites target 1000 cumulative model years; FR-Hes targets 500.
Never starts from year zero, never deletes old restarts, and never submits
another site's case. The user explicitly runs each site's submit step.
"""
from __future__ import annotations

import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime

CASE_ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/cases')
OUTPUT_ROOT = Path('/scratch/ly3n24/CTSM_FATES_OUTPUTS')
BACKUPS = OUTPUT_ROOT / 'recovery_backups/FLUXNET_MultiSite_8/after_inode_quota_20261020'
MPI = 'srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
# source: repository Stage-07 and 500-to-1000 continuation scripts
SITES = {
    'CZ-BK1': (2004, 2025, 376.95, 1000),
    'IT-Ren': (1999, 2025, 367.80, 1000),
    'FR-Hes': (1997, 2025, 363.04, 500),
    'FR-FBn': (2008, 2024, 385.02, 1000),
    'DE-Hzd': (2010, 2025, 388.75, 1000),
    'CH-Dav': (1997, 2025, 363.04, 1000),
    'BE-Vie': (1996, 2025, 361.93, 1000),
    'IT-Lav': (2003, 2020, 375.14, 1000),
}
KINDS = {'cpl': 'cpl.r', 'atm': 'datm.r', 'lnd': 'clm2.r'}

class Blocked(Exception):
    pass

def stop(message):
    raise Blocked(message)

def run(*args, cwd=None, allow_fail=False):
    result = subprocess.run(args, cwd=str(cwd) if cwd else None,
                            capture_output=True, text=True)
    if result.returncode and not allow_fail:
        stop('Command failed: ' + ' '.join(map(str, args)) + '\n' +
             (result.stdout + result.stderr)[-1400:])
    return result

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            buf = f.read(4 * 1024 * 1024)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()

def xml(case, key):
    return run('./xmlquery', key, '--value', cwd=case).stdout.strip()

def paths(site):
    name = site + '_FATES_SPINUP500'
    return name, CASE_ROOT/name, OUTPUT_ROOT/name/'run', OUTPUT_ROOT/'archive'/name/'rest'

def jobs(site):
    name = site + '_FATES_SPINUP500'
    output = run('squeue', '-h', '-u', 'ly3n24', '-o', '%.100j|%T|%i').stdout
    return [line for line in output.splitlines() if name in line.split('|', 1)[0]]

def expected(name, comp, stamp):
    return f'{name}.{KINDS[comp]}.{stamp}.nc'

def pointer(path):
    if not path.is_file():
        stop(f'Missing restart pointer: {path}')
    lines = path.read_text(errors='replace').splitlines()
    if not lines:
        stop(f'Empty restart pointer: {path}')
    return lines[0].strip().removeprefix('./')

def valid_nc(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size < 1024:
        return False
    with path.open('rb') as f:
        head = f.read(8)
    return head.startswith((b'CDF\x01', b'CDF\x02', b'CDF\x05')) or head == b'\x89HDF\r\n\x1a\n'

def check_archive(site):
    name, case, rundir, archive = paths(site)
    if not archive.is_dir():
        stop('Archived restart directory missing: ' + str(archive))
    all_stamps = sorted(p.name for p in archive.iterdir()
                        if p.is_dir() and re.fullmatch(r'\d{4}-01-01-00000', p.name))
    if not all_stamps:
        stop('No archived checkpoint directories')
    stamp = all_stamps[-1]
    year = int(stamp[:4])
    start, last, co2, target = SITES[site]
    completed = year - start
    if completed < 0 or completed % 5 != 0 or completed > target:
        stop(f'Archive checkpoint {stamp}: unexpected completed years={completed} (target {target})')
    if site != 'FR-Hes' and completed < 500:
        stop('Seven-site 500-year baseline not yet complete; inspect separately')
    refs = {}
    for comp in KINDS:
        file = expected(name, comp, stamp)
        pref = archive/stamp/f'rpointer.{comp}.{stamp}'
        if pointer(pref) != file:
            stop(f'{stamp} archive {comp} pointer mismatch')
        src = archive/stamp/file
        if not valid_nc(src):
            stop(f'Archived NetCDF missing/truncated/invalid header: {src}')
        refs[comp] = src
    return stamp, completed, refs

def verify_case(site, require_idle=True):
    if os.environ.get('USER') != 'ly3n24':
        stop('This script is specific to IRIDIS6 user ly3n24')
    if site not in SITES:
        stop('Unknown site: ' + site)
    active = jobs(site)
    if require_idle and active:
        stop('Already queued/running jobs:\n' + '\n'.join(active))
    name, case, rundir, archive = paths(site)
    if not case.is_dir() or not rundir.is_dir():
        stop('CIME case or RUNDIR is missing')
    if (case/'.git/index.lock').exists():
        stop('Case .git/index.lock exists; investigate active Git/CIME before proceeding')
    stamp, done, refs = check_archive(site)
    start, last, co2, target = SITES[site]
    wanted = {
        'CASE': name, 'RUN_STARTDATE': f'{start}-01-01', 'RUN_TYPE': 'startup',
        'CONTINUE_RUN': 'TRUE', 'STOP_OPTION': 'nyears', 'STOP_N': '5',
        'REST_OPTION': 'nyears', 'REST_N': '5', 'DOUT_S': 'TRUE',
        'BUILD_COMPLETE': 'TRUE', 'MPILIB': 'openmpi', 'CALENDAR': 'NO_LEAP',
        'ATM_NCPL': '48', 'CLM_CO2_TYPE': 'constant',
        'RUNDIR': str(rundir), 'DOUT_S_ROOT': str(archive.parent),
    }
    for key, value in wanted.items():
        found = xml(case, key)
        if found != value:
            stop(f'{key} mismatch: {found!r} (expected {value!r})')
    found_co2 = float(xml(case, 'CCSM_CO2_PPMV'))
    if abs(found_co2 - co2) > .011:
        stop(f'Unexpected fixed CO2 {found_co2} (expected {co2})')
    if not (Path(xml(case, 'EXEROOT'))/'cesm.exe').is_file():
        stop('Compiled cesm.exe is missing')
    for comp in ('ATM', 'LND', 'CPL'):
        if xml(case, f'NTASKS_{comp}') != '1' or xml(case, f'NTHRDS_{comp}') != '1':
            stop('MPI/thread layout not single-rank: ' + comp)
    datm = (case/'user_nl_datm_streams').read_text(errors='replace')
    for attr, val in [('first', start), ('last', last), ('align', start)]:
        if not re.search(r'^CLM_USRDAT\.UNSET:year_' + attr +
                         r'\s*=\s*' + str(val) + r'\s*$', datm, re.M):
            stop('DATM cycling year_' + attr + ' changed')
    if not re.search(r'^CLM_USRDAT\.UNSET:taxmode\s*=\s*cycle\s*$', datm, re.M):
        stop('DATM cycling setup changed')
    last_lines = (case/'CaseStatus').read_text(errors='replace').splitlines()
    last_archive = max((i for i,s in enumerate(last_lines) if 'st_archive success' in s), default=-1)
    last_model = max((i for i,s in enumerate(last_lines) if 'model execution success' in s), default=-1)
    if last_model > last_archive:
        stop('There is a model execution success newer than the last archive success; repair archive first')
    pattern = re.compile(re.escape(name) + r'\.(?:clm2|datm|cpl)\.r\.(\d{4})-')
    newer = []
    for file in rundir.iterdir():
        m = pattern.search(file.name)
        if m and int(m.group(1)) > int(stamp[:4]):
            newer.append(file.name)
    if newer:
        stop('Newer *unarchived* restart files present; do not roll back: ' + ', '.join(newer[:5]))
    return {'site': site, 'name': name, 'stamp': stamp, 'done': done,
            'target': target, 'segments': (target-done)//5,
            'current_resubmit': xml(case, 'RESUBMIT'),
            'mpi': xml(case, 'MPI_RUN_COMMAND'),
            'refs': refs}

def inspect():
    print('EIGHT-SITE CHECKPOINT AUDIT — READ ONLY; no job submissions', flush=True)
    print(f"{'SITE':<9}{'DONE':>8}{'TARGET':>9}{'SEGMENTS':>10}{'RESUB':>9}  RESULT")
    for site in SITES:
        try:
            current_jobs = jobs(site)
            if current_jobs:
                try:
                    stamp, done, _ = check_archive(site)
                    detail = f'ACTIVE; checkpoint={stamp}; ' + '; '.join(current_jobs)
                    print(f'{site:<9}{done:>8}{SITES[site][3]:>9}{"-":>10}{"-":>9}  {detail}')
                except Blocked as e:
                    print(f'{site:<9}{"-":>8}{SITES[site][3]:>9}{"-":>10}{"-":>9}  ACTIVE; {e}')
                continue
            info = verify_case(site)
            status = ('COMPLETE — no submission' if not info['segments'] else
                      f"READY; checkpoint={info['stamp']}; MPI={info['mpi']}")
            print(f"{site:<9}{info['done']:>8}{info['target']:>9}"
                  f"{info['segments']:>10}{info['current_resubmit']:>9}  {status}")
        except (Blocked, OSError, ValueError) as e:
            print(f'{site:<9}{"-":>8}{SITES[site][3]:>9}{"-":>10}{"-":>9}  REVIEW: {e}')
    print('A READY site still requires prepare, review, and separate submit.')

def prepare(site):
    info = verify_case(site)
    if info['segments'] == 0:
        stop(f'{site} already reached {info["target"]} years; no submit needed')
    name, case, rundir, archive = paths(site)
    session = BACKUPS / site / ('recovery_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    session.mkdir(parents=True, exist_ok=False)
    (session/'case').mkdir()
    (session/'pointers').mkdir()
    (session/'partial_history').mkdir()
    print('SESSION=' + str(session), flush=True)
    for file in ('CaseStatus', '.case.run', 'case.st_archive', 'env_run.xml',
                 'env_case.xml', 'env_batch.xml', 'env_build.xml', 'env_archive.xml',
                 'env_mach_specific.xml', 'env_mach_pes.xml', 'user_nl_clm',
                 'user_nl_datm_streams'):
        if (case/file).is_file():
            shutil.copy2(case/file, session/'case'/file)
    for comp in KINDS:
        old = rundir/('rpointer.'+comp)
        if old.is_file():
            shutil.copy2(old, session/'pointers'/old.name)
    existing_science = {f: sha(case/f) for f in ('user_nl_clm','user_nl_datm_streams')}
    source_hash = {comp: sha(src) for comp, src in info['refs'].items()}
    pattern = re.compile(re.escape(name) + r'\.clm2\.h[^.]*\.(\d{4})-')
    partial = []
    for file in rundir.iterdir():
        m = pattern.match(file.name)
        if m and int(m.group(1)) >= int(info['stamp'][:4]):
            if file.is_symlink() or not file.is_file():
                stop('Unexpected partial history path ' + str(file))
            partial.append(file)
    for file in partial:
        shutil.move(str(file), str(session/'partial_history'/file.name))
    print(f'Saved {len(partial)} failed-segment history NetCDF files')
    for comp, src in info['refs'].items():
        dest = rundir/src.name
        if dest.is_symlink():
            stop('Refusing to overwrite symlink ' + str(dest))
        if dest.exists() and sha(dest) != source_hash[comp]:
            stop('Conflicting existing restart file: ' + str(dest))
        if not dest.exists():
            tmp = rundir/(src.name + '.recovery-tmp')
            if tmp.exists():
                stop('Temporary recovery copy already exists: ' + str(tmp))
            shutil.copy2(src, tmp)
            if sha(tmp) != source_hash[comp]:
                stop('Restart SHA256 error while staging ' + str(src))
            os.replace(tmp, dest)
    for comp in KINDS:
        ref = expected(name, comp, info['stamp'])
        dest = rundir/('rpointer.'+comp)
        if dest.is_symlink():
            stop('Refusing to modify symlink pointer: ' + str(dest))
        tmp = rundir/('rpointer.' + comp + '.recovery-tmp')
        if tmp.exists():
            stop('Temporary pointer already exists: ' + str(tmp))
        tmp.write_text(ref + '\n')
        os.replace(tmp, dest)
        if pointer(dest) != ref or sha(rundir/ref) != source_hash[comp]:
            stop('Pointer or staged restart verification failed: ' + comp)
    desired_resubmit = info['segments'] - 1
    if info['mpi'] != MPI:
        run('./xmlchange', 'MPI_RUN_COMMAND=' + MPI, cwd=case)
    run('./xmlchange', 'RESUBMIT=' + str(desired_resubmit), cwd=case)
    if xml(case, 'RESUBMIT') != str(desired_resubmit) or xml(case, 'MPI_RUN_COMMAND') != MPI:
        stop('MPI or RESUBMIT update did not persist')
    for file, old_sha in existing_science.items():
        if sha(case/file) != old_sha:
            stop('Scientific namelist changed: ' + file)
    preview = run('./preview_run', cwd=case, allow_fail=True)
    (session/'preview_run.log').write_text(preview.stdout + '\n' + preview.stderr)
    if preview.returncode:
        stop('preview_run failed; inspect session/preview_run.log')
    if MPI not in (preview.stdout + preview.stderr):
        stop('preview_run does not show expected MPI launcher')
    post_hash = {f: sha(case/f) for f in ('CaseStatus', 'env_run.xml', 'env_batch.xml',
                                          'user_nl_clm', 'user_nl_datm_streams')}
    manifest = {
        'site': site, 'case': name, 'checkpoint': info['stamp'],
        'completed': info['done'], 'target': info['target'],
        'segments': info['segments'], 'resubmit': desired_resubmit,
        'source_sha256': source_hash, 'prepared_sha256': post_hash,
        'prepared_at': datetime.now().isoformat(),
    }
    (session/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (session/'PREPARED').write_text('Prepared without submitting Slurm jobs.\n')
    print(f"PREPARED {site}: {info['done']}/{info['target']} years; "
          f"{info['segments']} segments left; RESUBMIT={desired_resubmit}")
    print('NO JOBS SUBMITTED. SESSION=' + str(session))
    print('Next after review: python3 SCRIPT submit ' + str(session))

def submit(session_str):
    session = Path(session_str).resolve()
    if not (session/'PREPARED').is_file() or not (session/'manifest.json').is_file():
        stop('Missing session PREPARED/manifest; no submission')
    manifest = json.loads((session/'manifest.json').read_text())
    site = manifest['site']
    if site not in SITES or session.parent != (BACKUPS/site).resolve():
        stop('Recovery session is not from the expected eight-site backup root')
    if (session/'SUBMIT_STARTED').exists():
        stop('One-shot session already attempted submission; do NOT retry')
    info = verify_case(site)
    if info['stamp'] != manifest['checkpoint'] or info['done'] != manifest['completed']:
        stop('Archive checkpoint changed since prepare')
    if info['segments'] != manifest['segments'] or info['target'] != manifest['target']:
        stop('Remaining spin-up segments changed since prepare')
    name, case, rundir, archive = paths(site)
    if xml(case, 'RESUBMIT') != str(manifest['resubmit']) or xml(case, 'MPI_RUN_COMMAND') != MPI:
        stop('RESUBMIT or MPI configuration changed since prepare')
    for file, digest in manifest['prepared_sha256'].items():
        if sha(case/file) != digest:
            stop('Case file changed since prepare: ' + file)
    for comp, src in info['refs'].items():
        ref = expected(name, comp, info['stamp'])
        if pointer(rundir/('rpointer.'+comp)) != ref:
            stop('Working run pointer mismatch: ' + comp)
        if sha(src) != manifest['source_sha256'][comp] or sha(rundir/ref) != manifest['source_sha256'][comp]:
            stop('Restart SHA256 mismatch: ' + comp)
    # Guard before case.submit, so partial submission cannot be repeated blindly.
    (session/'SUBMIT_STARTED').write_text(datetime.now().isoformat() + '\n')
    print(f'SUBMIT {site} ONLY: {info["done"]}->{info["target"]}, RESUBMIT={manifest["resubmit"]}', flush=True)
    result = run('./case.submit', cwd=case, allow_fail=True)
    (session/'case_submit.log').write_text(result.stdout + '\n' + result.stderr)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode:
        stop('case.submit failed; DO NOT rerun this SESSION. Inspect case_submit.log, CaseStatus and sacct')
    (session/'SUBMITTED').write_text('CIME case.submit exited 0; model not yet verified.\n')
    print(f'SUBMISSION ACCEPTED for {site}. Verify squeue, CaseStatus, sacct and next archived checkpoint.')


def main():
    try:
        if len(sys.argv) == 2 and sys.argv[1] in ('inspect', 'list'):
            inspect()
        elif len(sys.argv) == 3 and sys.argv[1] in ('prepare', 'submit'):
            # Prevent two concurrent invocations of this helper on the same account.
            with (Path.home()/'.FLUXNET8_recovery.lock').open('a+') as lock:
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    stop('Another FLUXNET8 recovery operation is in progress')
                if sys.argv[1] == 'prepare':
                    prepare(sys.argv[2])
                else:
                    submit(sys.argv[2])
        else:
            print('Usage: python3 SCRIPT inspect | prepare SITE | submit SESSION', file=sys.stderr)
            sys.exit(2)
    except (Blocked, OSError, ValueError, KeyError) as exc:
        print('STOP: ' + str(exc), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
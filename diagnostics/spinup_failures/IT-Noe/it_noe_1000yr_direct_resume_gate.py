#!/usr/bin/env python3
"""READ-ONLY gate for DIRECT IT-Noe 1000-year CIME continuation.

The operator chose to skip an isolated short CIME run AFTER a complete,
scientifically reviewed, versioned 22-year forcing replacement is available.
This tool NEVER edits DATM, CIME, restart, Slurm, approvals or GitHub. It
refuses a production-ready status on an unapproved May-only sensitivity trial.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

BASE = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing')
CASE = Path('/iridisfs/scratch/ly3n24/CLM_FATES/cases/IT-Noe_ERA5_ABW_BRANCH2009')
ARCH = Path('/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/IT-Noe_ERA5_ABW_BRANCH2009/rest/2054-01-01-00000')
YEARS = range(2004, 2026)
STAMP = '2054-01-01-00000'
CNAME = 'IT-Noe_ERA5_ABW_BRANCH2009'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as src:
        for b in iter(lambda: src.read(2**20), b''):
            h.update(b)
    return h.hexdigest()


def xval(case: Path, name: str) -> str:
    try:
        r = subprocess.run(
            ['./xmlquery', name, '--value'], cwd=case, capture_output=True,
            text=True, timeout=30, check=False)
        return r.stdout.strip() if r.returncode == 0 else 'QUERY_FAILED'
    except (OSError, subprocess.TimeoutExpired):
        return 'QUERY_FAILED'


def run():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', type=Path, default=CASE)
    ap.add_argument('--forcing', type=Path, default=BASE / 'datm_11_IT-Noe_corrected_v2')
    ap.add_argument('--approval', type=Path,
                    help='Approved source/QC manifest JSON for final 22-year forcing')
    ap.add_argument('--archive', type=Path, default=ARCH)
    args = ap.parse_args()
    blockers = []
    warnings = []
    print('========== IT-Noe 1000-YEAR DIRECT-RESUME GATE ==========')
    print('READ ONLY. THIS PROGRAM NEVER SUBMITS A JOB.')
    print('CASE=' + str(args.case))
    print('FORCING=' + str(args.forcing))
    print('ARCHIVE=' + str(args.archive))
    print('APPROVAL=' + str(args.approval or 'NOT_PROVIDED'))
    print('EXPECTED: 50/1000 complete; 950 left; 190 five-year segments; RESUBMIT=189')

    if not args.case.is_dir():
        blockers.append('Existing CIME case missing')
    else:
        expected = {
            'RUN_TYPE': 'branch',
            'RUN_REFDATE': '2009-01-01',
            'RUN_STARTDATE': '2004-01-01',
            'CONTINUE_RUN': 'TRUE',
            'STOP_OPTION': 'nyears',
            'STOP_N': '5',
            'REST_OPTION': 'nyears',
            'REST_N': '5',
            'RESUBMIT': '189',
            'ATM_NCPL': '48',
        }
        for key, want in expected.items():
            have = xval(args.case, key)
            print(f'XML {key}={have}')
            if have.upper() != want.upper():
                blockers.append(f'Incorrect {key}: {have}; expected {want}')

        stream = args.case / 'user_nl_datm_streams'
        if not stream.is_file():
            blockers.append('Missing user_nl_datm_streams')
        else:
            content = stream.read_text(errors='replace')
            all_files = re.findall(r'(/[^,\s\\]+/IT-Noe_DATM_(\d{4})\.nc)', content)
            years = {int(y) for _, y in all_files}
            if years != set(YEARS) or len(all_files) != len(YEARS):
                blockers.append('DATM streams do not list exactly 22 distinct 2004-2025 files')
            else:
                mismatches = [
                    (int(y), p) for p, y in all_files
                    if Path(p) != args.forcing / f'IT-Noe_DATM_{y}.nc'
                ]
                if mismatches:
                    blockers.append('Production case STILL references other forcing. '
                                    + f'Example year {mismatches[0][0]}: {mismatches[0][1]}')
                else:
                    print('DATM STREAM: all 22 annual file paths reference target forcing')
            if 'sensitivity_' in content or 'diagnostic_' in content:
                blockers.append('Production stream contains sensitivity/diagnostic forcing path')

    archived = args.archive
    if not archived.is_dir():
        blockers.append('2054 archive directory missing')
    else:
        for part, ptr in [('clm2', 'lnd'), ('cpl', 'cpl'), ('datm', 'atm')]:
            name = f'{CNAME}.{part}.r.{STAMP}.nc'
            nc = archived / name
            p = archived / f'rpointer.{ptr}.{STAMP}'
            if not nc.is_file() or nc.stat().st_size < 1024:
                blockers.append('Missing 2054 restart: ' + name)
            if not p.is_file() or not p.read_text(errors='replace').strip().splitlines()[0].strip().removeprefix('./') == name:
                blockers.append('Missing/wrong 2054 restart pointer: ' + p.name)
        if not blockers:
            print('CHECKPOINT: three component files and dated pointers exist (structure only)')
    if args.forcing.resolve() == (BASE / 'datm_11_provisional_dynamic_zbot_v1').resolve():
        blockers.append('Target forcing resolves to original uncorrected directory')
    if not args.forcing.is_dir():
        blockers.append('Complete approved versioned forcing directory DOES NOT EXIST')
    else:
        for year in YEARS:
            p = args.forcing / f'IT-Noe_DATM_{year}.nc'
            if not p.is_file() or p.stat().st_size < 1024:
                blockers.append('Missing corrected forcing file: ' + p.name)

    manifest = None
    if args.approval is None:
        blockers.append('No source-approved full-cycle production manifest (--approval)')
    elif not args.approval.is_file():
        blockers.append('Production approval manifest missing: ' + str(args.approval))
    else:
        try:
            manifest = json.loads(args.approval.read_text())
        except (OSError, ValueError) as exc:
            blockers.append('Cannot parse approval manifest: ' + str(exc))

    if isinstance(manifest, dict):
        if (manifest.get('site') != 'IT-Noe'
                or manifest.get('status') != 'APPROVED_FOR_PRODUCTION'
                or Path(str(manifest.get('forcing_directory', '/MISSING')))
                   .resolve() != args.forcing.resolve()
                or manifest.get('source_review_complete') is not True
                or manifest.get('boundary_review_complete') is not True
                or manifest.get('full_cycle_qc_complete') is not True):
            blockers.append('Approval manifest does not attest full-cycle scientific/source/QC review')
        hashes = manifest.get('year_sha256')
        if not isinstance(hashes, dict) or set(hashes) != {str(y) for y in YEARS}:
            blockers.append('Approval manifest requires SHA256 for all 22 annual NetCDF files')
        elif args.forcing.is_dir():
            for y in YEARS:
                file = args.forcing / f'IT-Noe_DATM_{y}.nc'
                if file.is_file() and sha256(file) != hashes[str(y)]:
                    blockers.append(f'NetCDF hash does not match scientific approval manifest: {y}')
        warnings.append('Even an approved full-cycle forcing does NOT retroactively correct 2004–2054 model states; document historical-state caveat.')
    try:
        q = subprocess.run(['squeue', '-h', '-u', 'ly3n24', '-o', '%i|%j|%T|%R'],
                           capture_output=True, text=True, check=False, timeout=30)
        if q.returncode:
            blockers.append('Could not query Slurm jobs')
        else:
            relevant = [line for line in q.stdout.splitlines()
                        if ('run.' + CNAME) in line or ('st_archive.' + CNAME) in line]
            for line in relevant:
                print('SLURM ' + line)
            for line in relevant:
                parts = line.split('|', 3)
                if len(parts) != 4 or parts[2] != 'PENDING' or 'DependencyNeverSatisfied' not in parts[3]:
                    blockers.append('Active or unusual Slurm job still exists: ' + line)
            if relevant:
                warnings.append('Old dead-dependency archive jobs must be cleared with the existing safe recovery workflow after all gates pass; not by this script.')
    except (OSError, subprocess.TimeoutExpired):
        blockers.append('Slurm query failed')
    print('========== RESULTS ==========')
    for message in warnings:
        print('WARNING: ' + message)
    for message in blockers:
        print('BLOCKED: ' + message)
    print('BLOCKER_COUNT=' + str(len(blockers)))
    if blockers:
        print('READY_FOR_DIRECT_RESUME=NO')
        print('No CIME configuration, files or Slurm jobs changed.')
        return 2
    print('READY_FOR_DIRECT_RESUME=TECHNICAL_INPUT_GATE_PASSED')
    print('NOT model completion and NOT a guarantee of scientific validity.')
    print('Use a separate audited recovery procedure to stage the 2054 restart and submit remaining 950 model years.')
    print('No CIME configuration, files or Slurm jobs changed.')
    return 0


if __name__ == '__main__':
    sys.exit(run())

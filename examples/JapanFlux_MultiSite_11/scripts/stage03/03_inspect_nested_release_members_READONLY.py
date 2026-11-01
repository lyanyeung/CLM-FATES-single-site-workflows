#!/usr/bin/env python3
"""JapanFlux Stage03: inspect nested JPF and direct JapanFLUX ZIP data in memory.

Read-only source audit: no extraction, no persistent outputs, no ZIP modification,
no model forcing, no Slurm. Redirect stdout to HOME to preserve the JSON report.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
JPF_SITES = {'JP-Api', 'JP-Fhk', 'JP-Fjy', 'JP-Khw', 'JP-Spp', 'JP-Tak', 'JP-Tef', 'JP-Tmd', 'JP-Yms'}
JP_SPECIAL = {'JP-Tom', 'JP-Tgf'}
IMPORTANT = ('TIMESTAMP', 'TA', 'RH', 'VPD', 'PA', 'SW_IN', 'LW_IN', 'P_', 'P_RAIN',
             'WS', 'WIND', 'NEE', 'GPP', 'RECO', 'CO2', 'QC', 'ZBOT', 'SWC', 'TS_', 'LE_', 'H_')


def csv_header(zf: zipfile.ZipFile, info: zipfile.ZipInfo, cap: int = 196608) -> dict:
    with zf.open(info) as f:
        raw = f.read(cap)
    for enc in ('utf-8-sig', 'cp932', 'shift_jis', 'latin-1'):
        try:
            lines = raw.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
        if not lines:
            return {'encoding_candidate': enc, 'column_count': 0}
        first = next(csv.reader([lines[0]]), [])
        second = next(csv.reader([lines[1]]), []) if len(lines) > 1 else []
        cols = [c.strip() for c in first]
        chosen = [c for c in cols if any(c.upper().startswith(p) for p in IMPORTANT)]
        return {
            'encoding_candidate': enc,
            'column_count': len(cols),
            'first_columns': cols[:28],
            'meteorology_and_QC_columns': chosen[:120],
            'second_line_first_cells': second[:8],
            'header_sample_complete': '\n' in raw.decode(enc),
        }
    return {'encoding_candidate': 'UNKNOWN', 'column_count': None}


def check_name(name: str) -> bool:
    p = PurePosixPath(name.replace('\\', '/'))
    return not p.is_absolute() and '..' not in p.parts and not any(':' in bit for bit in p.parts)


def member_priority(info: zipfile.ZipInfo) -> tuple:
    name = info.filename.upper()
    tags = ('FLUXMET_HH', 'COREVARS_HH', 'ALLVARS_HH', '_HH_', '_HR_',
            'FLUXMET_HR', '_ERA5_', 'BIF', 'MET', 'FLUX')
    rank = next((i for i, tag in enumerate(tags) if tag in name), len(tags))
    return (rank, info.filename)


def summarize_zip(zf: zipfile.ZipFile, max_csv: int) -> dict:
    infos = [i for i in zf.infolist() if not i.is_dir()]
    members = []
    for info in infos:
        members.append({
            'path': info.filename,
            'size_uncompressed': info.file_size,
            'suffix': PurePosixPath(info.filename).suffix.lower(),
            'safe_relative_path': check_name(info.filename),
        })
    candidates = sorted([i for i in infos if PurePosixPath(i.filename).suffix.lower() in ('.csv', '.tsv')
                         and check_name(i.filename)], key=member_priority)
    selected = []
    for i in candidates[:max_csv]:
        try:
            selected.append({'path': i.filename, **csv_header(zf, i)})
        except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
            selected.append({'path': i.filename, 'read_error': str(exc)})
    return {
        'inner_member_count': len(infos),
        'inner_uncompressed_total_bytes': sum(i.file_size for i in infos),
        'members': members,
        'csv_header_samples': selected,
        'csv_count': len(candidates),
        'csv_headers_truncated': len(candidates) > len(selected),
        'unsafe_names': [m['path'] for m in members if not m['safe_relative_path']],
    }


def inspect(row: dict, root: Path, max_bytes: int, max_csv: int) -> dict:
    site, package = row['site'], row['package']
    path = root / site / 'forcing' / 'packages' / (package + '.zip')
    result = {'site': site, 'outer_path': str(path), 'source_package': package,
              'reported_years': [row['first_year'], row['last_year']]}
    if not path.is_file() or path.is_symlink():
        return {**result, 'status': 'ERROR', 'error': 'Missing outer ZIP or symlink'}
    try:
        with zipfile.ZipFile(path) as outer:
            outer_files = [i for i in outer.infolist() if not i.is_dir()]
            result['outer_members_count'] = len(outer_files)
            if site in JPF_SITES:
                nested = [i for i in outer_files
                          if PurePosixPath(i.filename).name == (package + '.zip')]
                if len(nested) != 1:
                    raise ValueError('Expected exactly one inner ZIP with exact package name; got '+str(len(nested)))
                member = nested[0]
                if not check_name(member.filename):
                    raise ValueError('Unsafe inner ZIP entry path')
                if member.file_size > max_bytes:
                    raise ValueError(f'Inner ZIP {member.file_size} exceeds --max-nested-mib limit; no read')
                # Stream outer ZIP member into an in-memory BytesIO for random access.
                # No filesystem extraction, no scratch inode and no outer ZIP mutation.
                with io.BytesIO() as mem, outer.open(member) as raw:
                    total = 0
                    while True:
                        chunk = raw.read(4 * 1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > max_bytes:
                            raise ValueError('Inner archive exceeded memory size cap')
                        mem.write(chunk)
                    mem.seek(0)
                    with zipfile.ZipFile(mem) as inner:
                        inner_data = summarize_zip(inner, max_csv)
                result.update({'format': 'DOUBLE_ZIP', 'nested_member': member.filename,
                               'nested_zip_bytes': total, **inner_data})
            elif site in JP_SPECIAL:
                result.update({'format': 'DIRECT_JAPANFLUX_ZIP', **summarize_zip(outer, max_csv)})
            else:
                raise ValueError('Unknown site; no source format assumption')
        result['status'] = 'INVENTORIED_HEADER_ONLY'
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, EOFError, MemoryError) as exc:
        result.update({'status': 'ERROR', 'error': str(exc)})
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--site', choices=sorted(JPF_SITES | JP_SPECIAL), help='Optional single-site pilot')
    p.add_argument('--max-nested-mib', type=int, default=256)
    p.add_argument('--max-csv-headers', type=int, default=60)
    a = p.parse_args()
    if not 64 <= a.max_nested_mib <= 1024 or not 0 <= a.max_csv_headers <= 200:
        p.error('Expected --max-nested-mib 64..1024 and --max-csv-headers 0..200')
    with a.manifest.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    if len(rows) != 11 or {r['site'] for r in rows} != JPF_SITES | JP_SPECIAL:
        p.error('Manifest does not match exact eleven JapanFlux sites')
    selected = [r for r in rows if a.site is None or r['site'] == a.site]
    res = {'stage': 'JapanFlux Stage03', 'mode': 'READ_ONLY_NESTED_IN_MEMORY_NO_EXTRACTION',
           'sites': [inspect(r, a.root, a.max_nested_mib * (1024 ** 2), a.max_csv_headers)
                     for r in selected]}
    res['pass_count'] = sum(s['status'] == 'INVENTORIED_HEADER_ONLY' for s in res['sites'])
    res['expected_count'] = len(selected)
    res['passes'] = res['pass_count'] == res['expected_count']
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res['passes'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

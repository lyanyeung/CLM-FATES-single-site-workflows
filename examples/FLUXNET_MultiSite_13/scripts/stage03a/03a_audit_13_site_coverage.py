#!/usr/bin/env python3
"""Read-only, release-pinned, half-hour FLUXNET input audit for thirteen CTSM-FATES sites.

Based on the year-coverage screening used by FLUXNET_MultiSite_8.
Does not modify raw, surface, forcing, DATM or model output files.
Requires pandas/numpy (clm_fates_env). Reports provisional completeness, NOT scientific QC.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
SITES = {
    'DE-Lnf': ('EUF_DE-Lnf_FLUXNET_2002-2024_v1.3_r1', 2002, 2024, 'v1.3'),
    'DE-Obe': ('EUF_DE-Obe_FLUXNET_2008-2025_v1.3_r1', 2008, 2025, 'v1.3'),
    'ES-Agu': ('EUF_ES-Agu_FLUXNET_2006-2024_v1.3_r1', 2006, 2024, 'v1.3'),
    'ES-LJu': ('EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1', 2004, 2024, 'v1.3'),
    'IT-Col': ('FLX_IT-Col_FLUXNET2015_FULLSET_1996-2014_1-4', 1996, 2014, '2015'),
    'DE-Gri': ('ICOS_DE-Gri_FLUXNET_2004-2025_v1.3_r1', 2004, 2025, 'v1.3'),
    'DE-RuR': ('ICOS_DE-RuR_FLUXNET_2011-2025_v1.3_r1', 2011, 2025, 'v1.3'),
    'FI-Hyy': ('ICOS_FI-Hyy_FLUXNET_1997-2026_v1.3_r1', 1997, 2025, 'v1.3'),
    'FI-Let': ('ICOS_FI-Let_FLUXNET_2010-2025_v1.3_r1', 2010, 2025, 'v1.3'),
    'FR-Pue': ('ICOS_FR-Pue_FLUXNET_2000-2026_v1.3_r1', 2000, 2025, 'v1.3'),
    'GF-Guy': ('ICOS_GF-Guy_FLUXNET_2004-2025_v1.3_r1', 2004, 2025, 'v1.3'),
    'IT-MBo': ('ICOS_IT-MBo_FLUXNET_2003-2026_v1.3_r1', 2003, 2025, 'v1.3'),
    'IT-Tor': ('ICOS_IT-Tor_FLUXNET_2008-2025_v1.3_r1', 2008, 2025, 'v1.3'),
}
NEEDED_FOR_V5 = ['TA_F', 'VPD_F', 'PA_F', 'SW_IN_F', 'LW_IN_F', 'WS_F', 'P_F']
# A 2015 FULLSET may have different columns; absent inputs will be listed for review,
# not silently substituted or represented as measured data.
MISSING_SENTINEL = -9990.0
EXPECTED_PER_YEAR = 17520  # 365 * 48, after removing Feb 29


def exactly_one(folder, pattern):
    paths = list(folder.glob(pattern))
    if len(paths) != 1:
        raise RuntimeError(f'Expected one {pattern}, found {len(paths)} in {folder}')
    return paths[0]


def scan(site, root, audit_rows, year_rows):
    release, first, last, kind = SITES[site]
    source = root / site / 'forcing' / 'raw' / release
    if not source.is_dir():
        raise RuntimeError(f'Pinned release directory does not exist: {source}')
    primary = exactly_one(source, '*FLUXMET_HH*.csv' if kind == 'v1.3' else '*FULLSET_HH*.csv')
    companion = exactly_one(source, '*ERA5_HH*.csv' if kind == 'v1.3' else '*ERAI_HH*.csv')
    metadata = list(source.glob('*_BIF_*.csv'))
    header = list(pd.read_csv(primary, nrows=0).columns)
    era_header = list(pd.read_csv(companion, nrows=0).columns)
    if 'TIMESTAMP_START' not in header:
        raise RuntimeError(f'TIMESTAMP_START absent from {primary.name}')
    present = [v for v in NEEDED_FOR_V5 if v in header]
    absent = [v for v in NEEDED_FOR_V5 if v not in header]
    print(f'  Main: {primary.name}')
    print(f'  Companion: {companion.name}')
    print(f'  BIF: {len(metadata)} (expected 0 for legacy IT-Col)')
    print(f'  v5 required columns: {len(present)}/{len(NEEDED_FOR_V5)}, missing: {absent if absent else "none"}')
    print(f'  Companion columns: {len(era_header)}')
    if kind == '2015':
        print('  Legacy FULLSET meteorological alternatives:',
              [x for x in header if x.startswith(('TA_', 'VPD_', 'PA_', 'SW_IN_', 'LW_IN_', 'WS_', 'P_'))][:70])
    valid = defaultdict(lambda: defaultdict(int))
    seen = defaultdict(set)
    duplicate = defaultdict(int)
    invalid_stamp = 0
    off_grid = defaultdict(int)
    invalid_numeric = defaultdict(lambda: defaultdict(int))
    read_cols = ['TIMESTAMP_START'] + present
    for chunk in pd.read_csv(primary, usecols=read_cols, dtype={'TIMESTAMP_START': str},
                             chunksize=100000, low_memory=False):
        textstamp = chunk['TIMESTAMP_START'].str.strip().str.replace(r'\.0$', '', regex=True)
        ts = pd.to_datetime(textstamp, format='%Y%m%d%H%M', errors='coerce')
        invalid_stamp += int(ts.isna().sum())
        keep = ts.notna() & ts.dt.year.between(first, last) & ~((ts.dt.month == 2) & (ts.dt.day == 29))
        if not keep.any():
            continue
        data = chunk.loc[keep, present].copy()
        dt = ts.loc[keep]
        for yr in sorted(dt.dt.year.unique()):
            positions = dt.dt.year == yr
            times = dt.loc[positions]
            count = len(times)
            valid[yr]['rows'] += count
            ticks = set(times.astype('int64').tolist())
            duplicate[yr] += count - len(ticks.difference(seen[yr]))
            seen[yr].update(ticks)
            off_grid[yr] += int(((times.dt.minute != 0) & (times.dt.minute != 30)).sum())
            for col in present:
                values = pd.to_numeric(data.loc[positions, col], errors='coerce')
                okay = np.isfinite(values.to_numpy(dtype=float)) & (values.to_numpy(dtype=float) > MISSING_SENTINEL)
                valid[yr][col] += int(okay.sum())
                invalid_numeric[yr][col] += count - int(okay.sum())
    problems = []
    for yr in range(first, last + 1):
        n = len(seen[yr]); denom = EXPECTED_PER_YEAR
        fractions = {col: round(100 * valid[yr][col] / denom, 2) if col in present else None
                     for col in NEEDED_FOR_V5}
        min_pct = min((v for v in fractions.values() if v is not None), default=0.0)
        flag = []
        if n != denom: flag.append(f'timestamps={n}/{denom}')
        if duplicate[yr]: flag.append(f'duplicates={duplicate[yr]}')
        if off_grid[yr]: flag.append(f'off-grid={off_grid[yr]}')
        if absent: flag.append(f'columns_missing={len(absent)}')
        if min_pct < 90: flag.append(f'min_valid={min_pct:.1f}%')
        status = 'REVIEW' if flag else 'STRUCTURE_CANDIDATE'
        if flag:
            problems.append(f'{yr}: {", ".join(flag)}')
        year_rows.append(dict(site=site, release=release, product=kind, year=yr,
                              timestamp_count=n, duplicate_count=duplicate[yr],
                              off_grid_count=off_grid[yr], malformed_timestamps=invalid_stamp,
                              minimum_available_pct=min_pct, status=status,
                              **{f'{col}_valid_pct': fractions[col] for col in NEEDED_FOR_V5}))
    audit_rows.append(dict(site=site, release=release, product=kind, year_start=first,
                           year_end=last, primary_file=str(primary), companion_file=str(companion),
                           metadata_bif_count=len(metadata), missing_v5_columns=','.join(absent),
                           primary_columns=','.join(header), companion_columns=','.join(era_header),
                           years_needing_review=len(problems), malformed_timestamps=invalid_stamp,
                           status='REVIEW' if problems or invalid_stamp else 'STRUCTURE_CANDIDATE'))
    print(f'  Checked {first}-{last}; annual review years: {len(problems)}')
    for msg in problems[:20]:
        print('  REVIEW', msg)
    if len(problems) > 20: print(f'  ...and {len(problems)-20} more years; inspect CSV')
    if invalid_stamp: print(f'  WARNING: {invalid_stamp} malformed TIMESTAMP_START values')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--output-dir', type=Path, default=Path.home() / 'FLUXNET_13_input_audit')
    p.add_argument('--sites', nargs='+', choices=sorted(SITES), default=list(SITES))
    a = p.parse_args()
    audit_rows, year_rows = [], []
    failures = []
    for site in a.sites:
        print(f'\n======== {site} ========', flush=True)
        try:
            scan(site, a.root, audit_rows, year_rows)
        except Exception as e:
            failures.append((site, str(e)))
            print('  ERROR:', str(e), flush=True)
            audit_rows.append(dict(site=site, status='ERROR', error=str(e)))
    a.output_dir.mkdir(parents=True, exist_ok=True)
    annual = a.output_dir / 'annual_coverage.csv'
    summary = a.output_dir / 'site_input_summary.csv'
    pd.DataFrame(year_rows).to_csv(annual, index=False)
    pd.DataFrame(audit_rows).to_csv(summary, index=False)
    print('\n=== FINAL INPUT AUDIT ===')
    for item in audit_rows:
        print(f"{item['site']:8s} {item['status']:19s} years_review={item.get('years_needing_review', '-')}, missing_v5_cols={item.get('missing_v5_columns', '-')}")
    print('Annual report:', annual)
    print('Site report:', summary)
    print('AUDITED:', len(a.sites) - len(failures), '/', len(a.sites), 'sites')
    print('CAUTION: STRUCTURE_CANDIDATE is NOT a meteorological-QC, PFT or spin-up pass.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
#!/usr/bin/env python3
"""Read-only audit of IT-Noe multi-source TA/VPD/PA vs independent ICOS ERA5.

Does not alter existing raw files, candidate CSV, DATM NetCDF, CIME cases, or restarts.
Creates reports under the user's home directory (unless --out is supplied).
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

DEFAULT_ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing')


def read_selected_csv(path, columns, years, source_time=False):
    header = pd.read_csv(path, nrows=0).columns.tolist()
    if source_time:
        tcol = 'TIMESTAMP_START' if 'TIMESTAMP_START' in header else 'TIMESTAMP_END' if 'TIMESTAMP_END' in header else None
    else:
        tcol = 'time' if 'time' in header else None
    if tcol is None:
        raise ValueError(f'Missing timestamp in {path}')
    missing = set(columns) - set(header)
    if missing:
        raise ValueError(f'Missing variables {sorted(missing)} in {path}')
    acc = []
    for chunk in pd.read_csv(path, usecols=[tcol] + columns, dtype={tcol: 'string'}, chunksize=100000, low_memory=False):
        if source_time:
            stamps = chunk[tcol].str.strip().str.replace(r'\.0$', '', regex=True)
            times = pd.to_datetime(stamps, format='%Y%m%d%H%M', errors='coerce')
            if tcol == 'TIMESTAMP_END':
                times -= pd.Timedelta(minutes=30)
        else:
            times = pd.to_datetime(chunk[tcol], errors='coerce')
        if times.isna().any():
            raise ValueError(f'Unparseable timestamp in {path}')
        keep = times.dt.year.isin(years) & ~((times.dt.month == 2) & (times.dt.day == 29))
        if keep.any():
            part = chunk.loc[keep, columns].copy()
            part.insert(0, 'time', times.loc[keep].to_numpy())
            acc.append(part)
    if not acc:
        raise ValueError(f'No target years in {path}')
    df = pd.concat(acc, ignore_index=True).sort_values('time')
    if df['time'].duplicated().any():
        raise ValueError(f'Duplicate timestamps in {path}')
    return df


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--out', type=Path, default=Path.home() / 'IT-Noe_source_diagnosis' / 'era_comparison_v1')
    parser.add_argument('--years', type=int, nargs='+', default=[2010, 2024, 2025])
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    candidate = args.root / 'merged_multisource_11_v07a' / 'IT-Noe_multisource_HH_2004_2025_candidate.csv'
    era = args.root / 'raw_multisource_v1' / 'ICOS' / 'ICOS_IT-Noe_FLUXNET_ERA5_HH_1981-2026_v1.3_r1.csv'
    for p in (candidate, era):
        if not p.is_file():
            raise SystemExit(f'MISSING INPUT: {p}')
    ccols = ['TA_F', 'VPD_F', 'PA_F', 'TA_F_SOURCE', 'TA_F_QC',
             'VPD_F_SOURCE', 'VPD_F_QC', 'PA_F_SOURCE', 'PA_F_QC',
             'RH_IMPLIED_PCT', 'PAIR_STATUS']
    d = read_selected_csv(candidate, ccols, args.years)
    e = read_selected_csv(era, ['TA_ERA', 'VPD_ERA', 'PA_ERA'], args.years, source_time=True)
    d = d.merge(e, on='time', how='left', validate='one_to_one')
    for col in ['TA_F', 'VPD_F', 'PA_F', 'TA_ERA', 'VPD_ERA', 'PA_ERA', 'RH_IMPLIED_PCT']:
        d[col] = pd.to_numeric(d[col], errors='coerce')
        d.loc[d[col] <= -9990, col] = np.nan
    for col in ['TA_F_QC', 'VPD_F_QC', 'PA_F_QC']:
        d[col] = pd.to_numeric(d[col], errors='coerce')
    completeness = 100 * d['TA_ERA'].notna().mean()
    print('Candidate:', candidate)
    print('Independent ERA5:', era)
    print('Rows:', len(d), 'ERA TA matching coverage: %.2f%%' % completeness)
    if completeness < 95:
        raise SystemExit('STOP: fewer than 95% ERA matches. Check timestamp convention and inputs before interpreting the comparison.')
    d['year'] = d.time.dt.year
    d['TA_minus_ERA_C'] = d.TA_F - d.TA_ERA
    d['TA_jump_30min_C'] = d.groupby('year').TA_F.diff()
    d['FLAG_TA_below_minus8C'] = d.TA_F < -8
    d['FLAG_TA_jump_over8C'] = d.TA_jump_30min_C.abs() > 8
    d['FLAG_TA_ERA_disagree15C'] = d.TA_minus_ERA_C.abs() > 15
    d['FLAG_RH_below10pct'] = d.RH_IMPLIED_PCT < 10
    flags = [c for c in d if c.startswith('FLAG_')]
    d['ANY_REVIEW_FLAG'] = d[flags].any(axis=1)
    summary = d.groupby('year')[flags + ['ANY_REVIEW_FLAG']].sum().astype(int)
    summary['rows'] = d.groupby('year').size()
    summary['ERA_matches'] = d.groupby('year').TA_ERA.count()
    summary['median_abs_TA_ERA_diff_C'] = d.groupby('year').TA_minus_ERA_C.apply(lambda x: x.abs().median()).round(3)
    summary.to_csv(args.out / 'yearly_QC_vs_ERA_summary.csv')
    d.to_csv(args.out / 'selected_years_joined_readonly.csv', index=False)
    flagged = d.loc[d.ANY_REVIEW_FLAG].copy()
    flagged.to_csv(args.out / 'review_events_not_approved_for_replacement.csv', index=False)
    print('\n========== ANNUAL FLAG COUNTS ==========')
    print(summary.to_string())
    print('\n========== FLAGS BY SELECTED CANDIDATE SOURCE ==========')
    print(flagged.groupby(['year', 'TA_F_SOURCE'], dropna=False).size().to_string() if len(flagged) else 'No flagged records')
    print('\n========== QC COUNTS FOR FLAGGED EVENTS ==========')
    print(flagged.groupby(['year', 'TA_F_QC'], dropna=False).size().to_string() if len(flagged) else 'No flagged records')
    for year in args.years:
        subset = flagged.loc[flagged.year == year].copy()
        subset['absolute_TA_difference'] = subset.TA_minus_ERA_C.abs()
        subset = subset.sort_values('absolute_TA_difference', ascending=False).head(15)
        print(f'\n========== {year} TOP 15 TA vs ERA DISAGREEMENTS ==========')
        cols = ['time', 'TA_F', 'TA_ERA', 'TA_minus_ERA_C', 'TA_jump_30min_C',
                'TA_F_SOURCE', 'TA_F_QC', 'VPD_F_QC', 'RH_IMPLIED_PCT']
        print(subset[cols].sort_values('time').to_string(index=False) if len(subset) else 'No flagged records')
    near = d.loc[(d.time >= '2010-05-27 18:00') & (d.time <= '2010-05-28 10:00')].copy()
    print('\n========== MODEL-FAILURE CONTEXT (NOT EXACT ABORT TIME) ==========')
    print(near[['time', 'TA_F', 'TA_ERA', 'TA_minus_ERA_C', 'VPD_F', 'VPD_ERA',
                'TA_F_QC', 'VPD_F_QC', 'RH_IMPLIED_PCT']].to_string(index=False))
    print('\nREPORT DIRECTORY:', args.out)
    print('Review-only flags; no data corrected, no CIME jobs submitted.')


if __name__ == '__main__':
    main()

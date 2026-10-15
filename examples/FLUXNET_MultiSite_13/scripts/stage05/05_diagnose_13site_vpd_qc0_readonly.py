#!/usr/bin/env python3
"""Read-only, decision-focused diagnostic for 13-site FLUXNET QC-v5 candidates.

Outputs: all official QC=0 modifications, ES-LJu review-by-year/reason,
ES-LJu detailed original/final/ERA humidity context, contiguous 30-min episodes,
and largest candidate VPD modifications. Does not change candidate forcing or raw data.

NOT an automatic scientific approval or a replacement forcing generator.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SITES = [
    'DE-Lnf', 'DE-Obe', 'ES-Agu', 'ES-LJu', 'IT-Col', 'DE-Gri',
    'DE-RuR', 'FI-Hyy', 'FI-Let', 'FR-Pue', 'GF-Guy', 'IT-MBo', 'IT-Tor',
]
DEFAULT_ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_qc_v5_candidate_20261014')
DEFAULT_OUT = Path.home() / 'FLUXNET_13_targeted_VPD_QC0_review_20261014'


def load_csv(path, required):
    if not path.is_file():
        raise FileNotFoundError(str(path))
    frame = pd.read_csv(path, low_memory=False)
    absent = set(required).difference(frame.columns)
    if absent:
        raise ValueError(f'{path} missing columns {sorted(absent)}')
    return frame


def saturation_hpa(t_c):
    return 6.112 * np.exp(17.67 * t_c / (t_c + 243.5))


def rh_from_t_vpd(t_c, vpd_hpa):
    sat = saturation_hpa(t_c)
    return 100 * (sat - vpd_hpa) / sat


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate-root', type=Path, default=DEFAULT_ROOT)
    p.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    root = args.candidate_root.expanduser().resolve()
    out = args.out.expanduser().resolve()
    if not root.is_dir():
        p.error(f'Candidate root missing: {root}')
    if out == root or out in root.parents or root in out.parents:
        p.error('Output must be separate from the candidate root')
    if out.exists() and any(out.iterdir()):
        p.error('Refusing to overwrite diagnostic outputs; choose a NEW --out path')

    all_qc0, site_counts = [], []
    for site in SITES:
        q = root / site / 'forcing' / 'qc_v5'
        e = load_csv(q / f'{site}_replacement_events.csv',
                     ['time', 'variable', 'original_value', 'final_value', 'official_qc', 'reason'])
        e['official_qc'] = pd.to_numeric(e['official_qc'], errors='coerce')
        if 'site' in e.columns and not e['site'].eq(site).all():
            raise ValueError(f'{site}: unexpected site value in replacement events')
        e['site'] = site
        subset = e.loc[e['official_qc'].eq(0)].copy()
        all_qc0.append(subset)
        site_counts.append({'site': site, 'changes': len(e), 'QC0_changes': len(subset)})
    nonempty = [x for x in all_qc0 if not x.empty]
    all_qc0 = pd.concat(nonempty, ignore_index=True) if nonempty else pd.DataFrame(
        columns=['site', 'time', 'variable', 'original_value', 'final_value', 'official_qc', 'reason'])
    counts = pd.DataFrame(site_counts)
    print('\n=== ALL SITES: CHANGES TO OFFICIAL QC=0 ===')
    print(counts.to_string(index=False))
    print(f'TOTAL official QC=0 changes: {len(all_qc0)}')

    site = 'ES-LJu'
    q = root / site / 'forcing' / 'qc_v5'
    status = json.loads((q / f'{site}_status.json').read_text())
    source = Path(status.get('primary_file', ''))
    if not source.is_file():
        raise FileNotFoundError('Pinned ES-LJu original FLUXMET file missing in status.json: ' + str(source))
    reviews = load_csv(q / f'{site}_manual_review.csv',
                       ['time', 'variable', 'reason', 'final_value', 'era_value', 'official_qc'])
    events = load_csv(q / f'{site}_replacement_events.csv',
                      ['time', 'variable', 'reason', 'original_value', 'final_value', 'official_qc'])
    if reviews.duplicated(['time', 'variable']).any():
        raise ValueError('ES-LJu reviews have duplicate (time, variable) keys: needs separate handling')
    if events.duplicated(['time', 'variable']).any():
        raise ValueError('ES-LJu changes have duplicate (time, variable) keys: needs separate handling')
    if len(reviews) != int(status.get('manual_review_records', -1)):
        raise ValueError('ES-LJu review row count inconsistent with status.json')
    if len(events) != int(status.get('changes', -1)):
        raise ValueError('ES-LJu event row count inconsistent with status.json')

    # Preserve all manual reviews, including low-but-positive RH that has not been modified.
    details = reviews.copy()
    ev = events[['time', 'variable', 'original_value', 'final_value', 'reason', 'final_source']].copy()
    ev = ev.rename(columns={'final_value': 'event_final_value', 'reason': 'event_reason'})
    details = details.merge(ev, on=['time', 'variable'], how='left', validate='one_to_one')
    details['time'] = pd.to_datetime(details['time'], errors='raise')
    details['year'] = details['time'].dt.year
    details['month'] = details['time'].dt.strftime('%Y-%m')
    details['official_qc'] = pd.to_numeric(details['official_qc'], errors='coerce')

    original_header = pd.read_csv(source, nrows=0).columns.to_list()
    raw_cols = ['TIMESTAMP_START', 'TA_F', 'VPD_F', 'TA_ERA', 'VPD_ERA', 'TA_F_QC', 'VPD_F_QC', 'RH']
    raw_cols = [x for x in raw_cols if x in original_header]
    if not set(['TIMESTAMP_START', 'TA_F', 'VPD_F']).issubset(raw_cols):
        raise ValueError('ES-LJu original FLUXMET has no required raw meteorological columns')
    raw = pd.read_csv(source, usecols=raw_cols, low_memory=False, dtype={'TIMESTAMP_START': str})
    raw['time'] = pd.to_datetime(raw.pop('TIMESTAMP_START').str.strip().str.replace(r'\.0$', '', regex=True),
                                 format='%Y%m%d%H%M', errors='raise')
    raw = raw[raw['time'].isin(details['time'])].copy()
    if raw.duplicated(['time']).any():
        raise ValueError('Duplicate source times among reviewed ES-LJu records')
    if len(raw) != details['time'].nunique():
        raise ValueError(f'Source join incomplete: {len(raw)} source rows vs {details.time.nunique()} reviewed times')
    raw = raw.rename(columns={x: 'raw_' + x for x in raw.columns if x != 'time'})
    details = details.merge(raw, on='time', how='left', validate='many_to_one')

    # Candidate TA may differ from raw TA; get the actual final TA/VPD used in forcing.
    forcing_path = Path(status.get('forcing_csv', ''))
    if not forcing_path.is_file():
        raise FileNotFoundError('ES-LJu candidate forcing CSV missing: ' + str(forcing_path))
    forc = pd.read_csv(forcing_path, usecols=['time', 'TA_USE', 'VPD_USE'], low_memory=False)
    forc['time'] = pd.to_datetime(forc['time'], errors='raise')
    forc = forc.loc[forc['time'].isin(details['time'])].copy()
    if forc.duplicated(['time']).any() or len(forc) != details.time.nunique():
        raise ValueError('Candidate forcing timestamp join is incomplete/duplicated')
    forc.rename(columns={'TA_USE': 'candidate_TA_C', 'VPD_USE': 'candidate_VPD_hPa'}, inplace=True)
    details = details.merge(forc, on='time', how='left', validate='many_to_one')
    if not np.allclose(pd.to_numeric(details['candidate_VPD_hPa'], errors='coerce'),
                       pd.to_numeric(details['final_value'], errors='coerce'), rtol=0, atol=1e-6, equal_nan=True):
        raise ValueError('ES-LJu manual-review VPD and candidate forcing VPD are inconsistent')
    for v in ['raw_TA_F', 'raw_VPD_F', 'raw_TA_ERA', 'raw_VPD_ERA', 'raw_RH',
              'candidate_TA_C', 'candidate_VPD_hPa',
              'final_value', 'original_value', 'event_final_value']:
        if v in details:
            details[v] = pd.to_numeric(details[v], errors='coerce')
            if v.startswith('raw_'):
                details.loc[details[v] <= -9990, v] = np.nan

    # Recompute raw/source and candidate RH using the tower temperature.
    details['raw_implied_RH_pct'] = rh_from_t_vpd(details['raw_TA_F'], details['raw_VPD_F'])
    details['candidate_implied_RH_pct'] = rh_from_t_vpd(details['candidate_TA_C'], details['candidate_VPD_hPa'])
    if 'raw_TA_ERA' in details and 'raw_VPD_ERA' in details:
        details['ERA_implied_RH_pct'] = rh_from_t_vpd(details['raw_TA_ERA'], details['raw_VPD_ERA'])
    details['delta_VPD_hPa'] = details['final_value'] - details['raw_VPD_F']
    details['abs_delta_VPD_hPa'] = details['delta_VPD_hPa'].abs()
    details['review_reason'] = details['reason']

    reason = (details.groupby('review_reason', dropna=False)
              .agg(review_rows=('time', 'size'),
                   official_QC0=('official_qc', lambda x: int(x.eq(0).sum())),
                   median_abs_delta_VPD_hPa=('abs_delta_VPD_hPa', 'median'),
                   max_abs_delta_VPD_hPa=('abs_delta_VPD_hPa', 'max'))
              .reset_index().sort_values('review_rows', ascending=False))
    year_reason = (details.groupby(['year', 'review_reason'], dropna=False)
                   .agg(review_rows=('time', 'size'),
                        official_QC0=('official_qc', lambda x: int(x.eq(0).sum())),
                        median_abs_delta_VPD_hPa=('abs_delta_VPD_hPa', 'median'))
                   .reset_index().sort_values(['review_rows', 'year'], ascending=[False, True]))

    # Consecutive 30-min intervals for each reason (avoid combining distinct reasons).
    episode_list = []
    for what, group in details.sort_values('time').groupby('review_reason'):
        group = group.sort_values('time').copy()
        split = group['time'].diff().ne(pd.Timedelta(minutes=30)).cumsum()
        for _, seg in group.groupby(split):
            episode_list.append({
                'reason': what, 'start': seg['time'].iloc[0], 'end': seg['time'].iloc[-1],
                'half_hours': len(seg), 'hours': len(seg) * 0.5,
                'official_QC0': int(seg['official_qc'].eq(0).sum()),
                'maximum_abs_delta_VPD_hPa': seg['abs_delta_VPD_hPa'].max(),
            })
    episodes = pd.DataFrame(episode_list).sort_values(['half_hours', 'start'], ascending=[False, True])
    largest = details.sort_values('abs_delta_VPD_hPa', ascending=False).head(30)

    # No partial reports are written until all read-only input and validation steps succeed.
    out.mkdir(parents=True, exist_ok=True)
    counts.to_csv(out / 'all_site_counts.csv', index=False)
    all_qc0.sort_values(['site', 'time', 'variable']).to_csv(out / 'all_sites_official_QC0_modifications.csv', index=False)
    details.sort_values('time').to_csv(out / 'ES-LJu_review_details_with_raw_RH.csv', index=False)
    reason.to_csv(out / 'ES-LJu_review_by_reason.csv', index=False)
    year_reason.to_csv(out / 'ES-LJu_review_by_year_reason.csv', index=False)
    episodes.to_csv(out / 'ES-LJu_contiguous_review_episodes.csv', index=False)
    largest.to_csv(out / 'ES-LJu_largest_30_VPD_differences.csv', index=False)

    print('\n=== ES-LJu REVIEW CATEGORIES ===')
    print(reason.to_string(index=False))
    print('\n=== ES-LJu TOP 20 YEAR x REASON ===')
    print(year_reason.head(20).to_string(index=False))
    print('\n=== ES-LJu LONGEST 12 EPISODES ===')
    print(episodes.head(12).to_string(index=False))
    print('\nReports written to:', out)
    print('No original FLUXNET files, QC candidate files, DATM or active spin-ups have been changed.')
    print('WARNING: These diagnostics do NOT automatically approve ERA humidity repairs or official-QC=0 changes.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
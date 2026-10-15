#!/usr/bin/env python3
"""READ-ONLY audit of 13-site QC-v5 candidate outputs.

Aligned with FLUXNET_MultiSite_8/scripts/04_audit_eight_site_qc_v5.py.
Does NOT modify input/raw/processed forcing and does NOT approve meteorological QC.
Writes condensed review reports to a separate home-directory report folder.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

DEFAULT_ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_qc_v5_candidate_20261014')
DEFAULT_OUT = Path.home() / 'FLUXNET_13_QC_v5_review_audit_20261014'
SITES = [
    'DE-Lnf', 'DE-Obe', 'ES-Agu', 'ES-LJu', 'IT-Col', 'DE-Gri',
    'DE-RuR', 'FI-Hyy', 'FI-Let', 'FR-Pue', 'GF-Guy', 'IT-MBo', 'IT-Tor',
]


def get_table(file_path, needed):
    if not file_path.is_file():
        raise FileNotFoundError('Missing QC audit CSV: ' + str(file_path))
    df = pd.read_csv(file_path, low_memory=False)
    absent = sorted(set(needed) - set(df.columns))
    if absent:
        raise ValueError(f'{file_path}: missing columns {absent}')
    return df


def rows_by_keys(df, keys, site, measure):
    if df.empty:
        return pd.DataFrame(columns=['site', *keys, measure, 'unique_half_hours', 'official_QC0'])
    d = df.copy()
    d['official_qc'] = pd.to_numeric(d['official_qc'], errors='coerce')
    d['is_qc0'] = d['official_qc'].eq(0).astype(int)
    # Group using the exact audit reason without making subjective decisions.
    result = d.groupby(keys, dropna=False).agg(
        **{measure: ('time', 'size')},
        unique_half_hours=('time', 'nunique'),
        official_QC0=('is_qc0', 'sum')
    ).reset_index()
    result.insert(0, 'site', site)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT, help='Existing 13-site QC candidate root')
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT, help='New, empty directory for diagnostic CSVs')
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.expanduser().resolve()
    if not root.is_dir():
        parser.error('Candidate root does not exist: ' + str(root))
    if out == root or out in root.parents or root in out.parents:
        parser.error('Output directory must be separate from the candidate root')
    if out.exists() and any(out.iterdir()):
        parser.error('Refusing to overwrite existing audit directory; choose a fresh --out path: ' + str(out))

    site_summaries = []
    review_reason = []
    review_year = []
    review_reason_year = []
    modifications_reason = []
    qc0_edited = []
    complete_manual = []
    source_provenance = []
    problems = []

    for site in SITES:
        print(f'\n===== {site} =====', flush=True)
        q = root / site / 'forcing/qc_v5'
        status_file = q / f'{site}_status.json'
        try:
            if not status_file.is_file():
                raise FileNotFoundError('Missing ' + str(status_file))
            status = json.loads(status_file.read_text())
            if status.get('site') != site:
                raise ValueError(f'Unexpected site in status.json: {status.get("site")}')
            events = get_table(q / f'{site}_replacement_events.csv',
                               ['time', 'variable', 'reason', 'official_qc', 'original_value', 'final_value'])
            reviews = get_table(q / f'{site}_manual_review.csv',
                                ['time', 'variable', 'reason', 'official_qc', 'final_value', 'era_value'])
            sources = get_table(q / f'{site}_qc_summary.csv',
                                ['variable', 'count', 'changed_count', 'original_missing', 'final_missing'])
            sources.insert(0, 'site', site)
            source_provenance.append(sources)
            events['official_qc'] = pd.to_numeric(events['official_qc'], errors='coerce')
            reviews['official_qc'] = pd.to_numeric(reviews['official_qc'], errors='coerce')
            n_mod_qc0 = int(events['official_qc'].eq(0).sum())
            n_review_qc0 = int(reviews['official_qc'].eq(0).sum())
            # Verify recorded status counters against their actual CSV rows.
            n_status_mod = status.get('changes')
            n_status_review = status.get('manual_review_records')
            mismatch = (n_status_mod is not None and int(n_status_mod) != len(events)) or \
                       (n_status_review is not None and int(n_status_review) != len(reviews))

            summaries = {
                'site': site,
                'status': status.get('status', 'UNKNOWN'),
                'years': f"{status.get('first_year', '?')}-{status.get('last_year', '?')}",
                'modifications': len(events),
                'modified_official_QC0': n_mod_qc0,
                'modified_unique_half_hours': events['time'].nunique(),
                'manual_review_rows': len(reviews),
                'review_official_QC0': n_review_qc0,
                'review_unique_half_hours': reviews['time'].nunique(),
                'status_count_mismatch': mismatch,
                'product': status.get('product', 'unspecified'),
                'reanalysis': status.get('reanalysis', 'unspecified'),
            }
            site_summaries.append(summaries)
            print(f"{summaries['status']}: {len(events)} changes "+
                  f'({n_mod_qc0} original QC=0); {len(reviews)} review rows '+
                  f'({n_review_qc0} original QC=0); mismatched counts={mismatch}', flush=True)

            review_reason.append(rows_by_keys(reviews, ['variable', 'reason'], site, 'review_rows'))
            modifications_reason.append(rows_by_keys(events, ['variable', 'reason'], site, 'modifications'))
            if not reviews.empty:
                reviews = reviews.copy()
                reviews['site'] = site
                reviews['year'] = reviews['time'].astype(str).str[:4]
                complete_manual.append(reviews)
                review_year.append(rows_by_keys(reviews, ['year'], site, 'review_rows'))
                review_reason_year.append(rows_by_keys(reviews, ['year', 'variable', 'reason'], site, 'review_rows'))
            if n_mod_qc0:
                a = events.loc[events['official_qc'].eq(0)].copy()
                a.insert(0, 'site', site)
                qc0_edited.append(a)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            message = f'{site}: {type(exc).__name__}: {exc}'
            problems.append(message)
            print('ERROR:', message, file=sys.stderr, flush=True)

    if problems:
        print('\nAUDIT INCOMPLETE; nothing written. Errors:', *problems, sep='\n  ', file=sys.stderr)
        return 1

    out.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(site_summaries)
    summary.to_csv(out / 'site_qc_summary.csv', index=False)

    def output_list(frames, name):
        if frames:
            df = pd.concat(frames, ignore_index=True)
            df.to_csv(out / name, index=False)
            return df
        pd.DataFrame().to_csv(out / name, index=False)
        return pd.DataFrame()

    reason_df = output_list(review_reason, 'review_by_reason.csv')
    output_list(review_year, 'review_by_year.csv')
    output_list(review_reason_year, 'review_by_year_reason.csv')
    output_list(modifications_reason, 'modifications_by_reason.csv')
    output_list(qc0_edited, 'official_QC0_modifications.csv')
    output_list(complete_manual, 'manual_reviews_all.csv')
    output_list(source_provenance, 'variable_source_provenance.csv')

    print('\n=== 13-SITE QC v5 AUDIT ===')
    show = ['site', 'status', 'modifications', 'modified_official_QC0',
            'manual_review_rows', 'review_official_QC0', 'review_unique_half_hours']
    print(summary[show].to_string(index=False))
    print('\nTOTAL modifications:', int(summary['modifications'].sum()))
    print('TOTAL original QC=0 modifications:', int(summary['modified_official_QC0'].sum()))
    print('TOTAL manual review rows:', int(summary['manual_review_rows'].sum()))
    if not reason_df.empty:
        print('\n=== REVIEW REASONS (top 20) ===')
        display = reason_df.sort_values(['review_rows', 'site'], ascending=[False, True])
        print(display[['site', 'variable', 'reason', 'review_rows', 'official_QC0']].head(20).to_string(index=False))
    print('\nSaved read-only source audit reports in:', out)
    print('Audit only. Do NOT equate PASS with complete scientific verification.')
    return 0 if not summary['status_count_mismatch'].any() else 2


if __name__ == '__main__':
    sys.exit(main())
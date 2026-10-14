#!/usr/bin/env python3
"""Read-only site BIF VAR_INFO_DATE/HEIGHT timeline inspection; no DATM writes.

Only FLUXNET BIFVARINFO_HH inputs are inspected, avoiding duplicate DD/MM tables.
Before first BIF height, an earliest-height backfill is DIAGNOSTIC ONLY, not approved.
"""
from collections import defaultdict
from pathlib import Path
import argparse
import csv
import sys
import pandas as pd
import numpy as np

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
YEARS = {
    'BE-Bra': (1996, 2025), 'FR-Fon': (2005, 2025),
    'GL-ZaH': (2000, 2025), 'IT-Noe': (2004, 2025),
    'AT-Neu': (2002, 2020), 'FI-Sod': (2001, 2025),
    'CH-Aws': (2006, 2024), 'CH-Cha': (2005, 2024),
    'CH-Fru': (2005, 2024), 'CH-Lae': (2004, 2024),
    'CZ-Stn': (2010, 2024),
}

def read_bif(path):
    values = defaultdict(lambda: defaultdict(set))
    invalid = []
    with path.open(encoding='utf-8-sig', errors='replace', newline='') as handle:
        reader = csv.DictReader(handle)
        needed = {'VARIABLE', 'DATAVALUE', 'GROUP_ID'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError(f'Not a grouped BIF file (missing {needed}): {path}')
        groups = defaultdict(dict)
        for line, row in enumerate(reader, start=2):
            key = (row.get('VARIABLE_GROUP', ''), row.get('GROUP_ID', ''))
            var = (row.get('VARIABLE') or '').strip().upper()
            if var:
                groups[key][var] = (row.get('DATAVALUE') or '').strip()
        for key, b in groups.items():
            var = b.get('VAR_INFO_VARNAME', '').upper()
            if var not in ('TA_F', 'WS_F'):
                continue
            date, h = b.get('VAR_INFO_DATE', ''), b.get('VAR_INFO_HEIGHT', '')
            try:
                stamp = pd.to_datetime(date, format='%Y%m%d%H%M', errors='raise')
                height = float(h)
                if pd.isna(stamp) or not np.isfinite(height) or not (0 < height <= 200):
                    raise ValueError('missing/invalid date or height')
            except (ValueError, OverflowError, TypeError) as exc:
                invalid.append(f'{path.name} {key} {var} date={date} height={h}: {exc}')
                continue
            values[var][stamp].add(height)
    return values, invalid

def diagnostic_height(history, times):
    bound = np.array([stamp.to_datetime64() for stamp, _ in history])
    heights = np.array([h for _, h in history], dtype=float)
    ix = np.searchsorted(bound, times.to_numpy(), side='right') - 1
    early = ix < 0
    return heights[np.maximum(ix, 0)], int(early.sum())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--out', type=Path, default=Path.home()/'FLUXNET_MultiSite_11/stage13_zbot_BIF_review')
    opt=p.parse_args()
    opt.out.mkdir(parents=True, exist_ok=True)
    summary, detail, issues = [], [], []
    for site, (first, last) in YEARS.items():
        forcing = opt.root/site/'forcing'
        paths = sorted(q for q in forcing.rglob('*.csv')
                       if 'BIFVARINFO_HH' in q.name.upper()
                       and any(x.lower().startswith('raw')
                               for x in q.relative_to(forcing).parts[:-1]))
        hits = defaultdict(lambda: defaultdict(set))
        warnings = []
        for src in paths:
            try:
                recs, invalid = read_bif(src)
                warnings += invalid
                for var, events in recs.items():
                    for timestamp, vals in events.items():
                        hits[var][timestamp].update(vals)
            except Exception as exc:
                warnings.append(f'{src.name}: {type(exc).__name__}: {exc}')
        histories = {}
        for var in ('TA_F', 'WS_F'):
            d = hits[var]
            conflicts = [(str(t), sorted(v)) for t, v in d.items() if len(v) > 1]
            if conflicts:
                warnings.append(f'{var} conflicting heights at same timestamp: {conflicts[:5]}')
            histories[var] = sorted((t, next(iter(v))) for t, v in d.items() if len(v) == 1)
            if not histories[var]:
                warnings.append(f'NO valid {var} BIF height history')
            for stamp, h in histories[var]:
                detail.append(dict(site=site, variable=var, effective_from=str(stamp), height_m=h))
        row = dict(site=site, years=f'{first}-{last}', HH_BIF_files=len(paths),
                   TA_events=len(histories['TA_F']), WS_events=len(histories['WS_F']))
        times = pd.date_range(f'{first}-01-01', f'{last}-12-31 23:30', freq='30min')
        times = times[~((times.month == 2) & (times.day == 29))]
        arrays = {}
        for var in ('TA_F', 'WS_F'):
            history = histories[var]
            row[var+'_first_date'] = str(history[0][0]) if history else ''
            row[var+'_last_date'] = str(history[-1][0]) if history else ''
            row[var+'_heights_m'] = ';'.join(str(h) for h in sorted(set(h for _,h in history)))
            if history:
                arr, early = diagnostic_height(history, times)
                row[var+'_before_first_BIF_halfhours'] = early
                arrays[var] = arr
                if early:
                    warnings.append(f'{var}: {early} half-hours BEFORE first BIF height (NO approval to extrapolate)')
            else:
                row[var+'_before_first_BIF_halfhours'] = len(times)
        if len(arrays) == 2:
            mismatch = int(np.count_nonzero(np.abs(arrays['TA_F']-arrays['WS_F']) > 3))
            row['TA_WS_height_diff_gt3m_halfhours_DIAGNOSTIC'] = mismatch
            if mismatch:
                warnings.append(f'{mismatch} half-hours have >3m TA/WS height mismatch; no wind adjustment applied')
        else:
            row['TA_WS_height_diff_gt3m_halfhours_DIAGNOSTIC'] = None
        row['status'] = ('REVIEW_REQUIRED' if warnings else 'HEIGHT_METADATA_PRESENT_REVIEW_ONLY')
        row['warnings'] = ' | '.join(warnings)
        summary.append(row)
        for w in warnings: issues.append(dict(site=site, issue=w))
        print(f'{site:7s}  BIF_HH={len(paths)} TA={row["TA_events"]} WS={row["WS_events"]} '
              f'early_TA={row["TA_F_before_first_BIF_halfhours"]} '
              f'WS_mismatch={row["TA_WS_height_diff_gt3m_halfhours_DIAGNOSTIC"]}  {row["status"]}',flush=True)
    pd.DataFrame(summary).to_csv(opt.out/'01_BIF_height_summary.csv',index=False)
    pd.DataFrame(detail,columns=['site','variable','effective_from','height_m']).to_csv(opt.out/'02_BIF_height_history.csv',index=False)
    pd.DataFrame(issues,columns=['site','issue']).to_csv(opt.out/'03_review_issues.csv',index=False)
    print('\nREPORT:',opt.out)
    print('READ ONLY. No height was accepted for dates earlier than first BIF metadata; no DATM generated.')

if __name__=='__main__':
    main()

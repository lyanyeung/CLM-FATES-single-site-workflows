#!/usr/bin/env python3
"""Stage24: inspect 13-site dated BIF TA_F/WS_F evidence; do not assign ZBOT.

Uses the Stage23 read-only CSV outputs, deduplicates repeated HH/DD/MM BIF
records, recomputes *NO_LEAP* half-hour history gaps, and inventories alternate
TA sensor labels at two missing-height sites. Does not revise any input.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SITES = {
    'DE-Lnf': (2002, 2024), 'DE-Obe': (2008, 2025),
    'ES-Agu': (2006, 2024), 'ES-LJu': (2004, 2024),
    'IT-Col': (1996, 2014), 'DE-Gri': (2004, 2025),
    'DE-RuR': (2011, 2025), 'FI-Hyy': (1997, 2025),
    'FI-Let': (2010, 2025), 'FR-Pue': (2000, 2025),
    'GF-Guy': (2004, 2025), 'IT-MBo': (2003, 2025),
    'IT-Tor': (2008, 2025),
}
BASE = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
STAGE23 = Path.home() / 'FLUXNET_13_stage23_BIF_20261018_034917_060345'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(c)
    return h.hexdigest()


def count_noleap_earlier(first: int, last: int, t: pd.Timestamp | None):
    """True number of half-hour intervals before first valid BIF, excluding 29 Feb."""
    if t is None:
        return None
    start, stop = pd.Timestamp(f'{first}-01-01'), pd.Timestamp(f'{last+1}-01-01')
    if t <= start:
        return 0
    limit = min(stop, t)
    if t.minute not in (0, 30) or t.second or t.microsecond:
        raise ValueError(f'BIF height time not half-hour aligned: {t}')
    times = pd.date_range(start, limit - pd.Timedelta(minutes=30), freq='30min')
    times = times[~((times.month == 2) & (times.day == 29))]
    return len(times)


def find_bif_sources(site: str, root: Path):
    folder = root / site / 'forcing'
    if not folder.is_dir():
        return []
    ans = []
    for p in folder.rglob('*.csv'):
        if 'BIF' not in p.name.upper():
            continue
        try:
            folders = p.relative_to(folder).parts[:-1]
        except ValueError:
            continue
        if any(x.lower().startswith('raw') for x in folders):
            ans.append(p)
    return sorted(ans)


def inventory_bif_aliases(site: str, root: Path):
    """Inventory raw BIF sensor labels; *not* proof of a TA_F height match."""
    candidates = []
    for f in find_bif_sources(site, root):
        with f.open('r', encoding='utf-8-sig', errors='replace', newline='') as handle:
            rows = csv.DictReader(handle)
            if not rows.fieldnames or not {'VARIABLE', 'DATAVALUE', 'GROUP_ID'} <= set(rows.fieldnames):
                continue
            groups = defaultdict(dict)
            for r in rows:
                group = (str(r.get('VARIABLE_GROUP') or ''), str(r.get('GROUP_ID') or ''))
                key = str(r.get('VARIABLE') or '').strip().upper()
                if key:
                    groups[group][key] = str(r.get('DATAVALUE') or '').strip()
            for group, values in groups.items():
                var = values.get('VAR_INFO_VARNAME', '').upper().strip()
                if not var:
                    continue
                # Diagnostic only: may describe another sensor/height/depth.
                looks_like_air_temp = bool(re.search(r'(^TA(?:$|[_-]))|T[_-]?AIR|AIR[_-]?TEMP', var))
                if not looks_like_air_temp:
                    continue
                candidates.append({
                    'site': site, 'bif_variable_name': var,
                    'raw_height': values.get('VAR_INFO_HEIGHT', ''),
                    'raw_effective_date': values.get('VAR_INFO_DATE', ''),
                    'instrument_group': ':'.join(group), 'source': str(f),
                    'interpretation': 'UNVERIFIED_ALIAS_NOT_YET_ZBOT',
                })
    return candidates


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage23', type=Path, default=STAGE23)
    ap.add_argument('--root', type=Path, default=BASE)
    ap.add_argument('--out', type=Path,
                    default=Path.home() / ('FLUXNET_13_stage24_BIF_unique_NOLEAP_' +
                    datetime.now().strftime('%Y%m%d_%H%M%S_%f')))
    a = ap.parse_args()
    evid_path = a.stage23 / '02_all_TA_WS_height_evidence.csv'
    sum_path = a.stage23 / '04_cross_source_earliest_height_summary.csv'
    for p in (evid_path, sum_path):
        if not p.is_file():
            raise FileNotFoundError(p)
    e = pd.read_csv(evid_path, dtype=str).fillna('')
    _ = pd.read_csv(sum_path)
    required = {'site', 'variable', 'time', 'height_m', 'source'}
    if required - set(e):
        raise ValueError(f'Incomplete Stage23 evidence: {required - set(e)}')
    if set(e.site) - set(SITES):
        raise ValueError(f'Unexpected sites in BIF evidence: {set(e.site)-set(SITES)}')
    e['time'] = pd.to_datetime(e.time, errors='raise')
    e['height_m'] = pd.to_numeric(e.height_m, errors='raise')
    if not e['variable'].isin(['TA_F', 'WS_F']).all():
        raise ValueError('Unexpected BIF variable names in Stage23 evidence')
    if not e.height_m.between(.5, 150).all():
        raise ValueError('Invalid BIF sensor height in Stage23 evidence')

    unique, conflicts = [], []
    for (site, var, time), group in e.groupby(['site', 'variable', 'time'], sort=True):
        heights = sorted(group.height_m.unique())
        if len(heights) != 1:
            conflicts.append({'site':site, 'variable':var, 'effective_from':str(time),
                              'heights_m':';'.join(map(str, heights)),
                              'status':'CONFLICT_SAME_DATE_BLOCKED'})
            continue
        unique.append({'site':site, 'variable':var, 'effective_from':str(time),
                       'height_m':float(heights[0]), 'raw_BIF_repeats':len(group),
                       'distinct_source_files':group.source.nunique(),
                       'date_precision':';'.join(sorted(set(group.get('date_precision', pd.Series('', index=group.index)).astype(str)))),
                       'status':'OBSERVED_DATED_BIF_EVIDENCE_NOT_APPROVED_ZBOT'})
    u = pd.DataFrame(unique, columns=[
        'site','variable','effective_from','height_m','raw_BIF_repeats',
        'distinct_source_files','date_precision','status'])
    if not u.empty:
        u = u.sort_values(['site','variable','effective_from'])
    summary, requests = [], []
    for site, (yr0, yr1) in SITES.items():
        subset = u[u.site == site]
        tr = subset[subset.variable == 'TA_F']
        wr = subset[subset.variable == 'WS_F']
        ta0 = pd.Timestamp(tr.iloc[0].effective_from) if len(tr) else None
        ws0 = pd.Timestamp(wr.iloc[0].effective_from) if len(wr) else None
        miss = count_noleap_earlier(yr0, yr1, ta0)
        block_conflict = any(r['site'] == site for r in conflicts)
        action = ('STOP_MISSING_TA_BIF' if ta0 is None else
                  'STOP_BIF_DATE_CONFLICT' if block_conflict else
                  'NEEDS_EARLY_HEIGHT_POLICY' if miss else
                  'BIF_TA_DATED_HISTORY_PRESENT')
        summary.append({
            'site':site, 'first_year':yr0, 'last_year':yr1,
            'unique_TA_dates':len(tr), 'unique_WS_dates':len(wr),
            'first_TA_date':str(ta0) if ta0 is not None else '',
            'first_TA_m':float(tr.iloc[0].height_m) if len(tr) else '',
            'first_WS_date':str(ws0) if ws0 is not None else '',
            'first_WS_m':float(wr.iloc[0].height_m) if len(wr) else '',
            'NOLEAP_early_TA_halfhours':miss if miss is not None else '',
            'has_conflicting_BIF_date':block_conflict,
            'next_action':action,
            'BIF_status':'SOURCE_EVIDENCE_ONLY_NOT_A_HEIGHT_POLICY',
        })
        requests.append({'site':site, 'request':action,
                         'guidance':{
                           'STOP_MISSING_TA_BIF':'Seek site-team / network verified TA sensor heights. WS/EC heights are NOT interchangeable with TA.',
                           'STOP_BIF_DATE_CONFLICT':'Resolve conflicting same-date sensor heights with primary source.',
                           'NEEDS_EARLY_HEIGHT_POLICY':'Propose first-observed TA height backfill as explicit assumption, subject to user approval.',
                           'BIF_TA_DATED_HISTORY_PRESENT':'Review dates and heights before freezing a ZBOT policy.',
                         }[action]})
        print(f'{site:7s} TA_epochs={len(tr)} WS_epochs={len(wr)} '
              f'first_TA_m={summary[-1]["first_TA_m"]!s:<7s} '
              f'NOLEAP_early_HH={str(miss):>7s} {action}', flush=True)

    aliases = []
    for site in ['DE-Lnf','IT-Col']:
        aliases.extend(inventory_bif_aliases(site, a.root))
    alias_df = pd.DataFrame(aliases, columns=[
        'site','bif_variable_name','raw_height','raw_effective_date',
        'instrument_group','source','interpretation'])
    a.out.mkdir(parents=True,exist_ok=False)
    u.to_csv(a.out / '01_unique_dated_TA_WS_height_events.csv',index=False)
    pd.DataFrame(summary).to_csv(a.out/'02_13site_NOLEAP_height_gap_summary.csv',index=False)
    pd.DataFrame(conflicts, columns=['site','variable','effective_from','heights_m','status']).to_csv(
        a.out/'03_conflicting_same_date_heights.csv',index=False)
    alias_df.to_csv(a.out/'04_DE-Lnf_IT-Col_possible_TA_aliases_UNVERIFIED.csv',index=False)
    pd.DataFrame(requests).to_csv(a.out/'05_actions_before_ZBOT_policy.csv',index=False)
    meta = {
        'purpose':'READ_ONLY 13-site BIF unique epochs + NOLEAP missing coverage',
        'source_stage23':str(a.stage23),
        'source_stage23_evidence_sha256':sha256(evid_path),
        'source_stage23_summary_sha256':sha256(sum_path),
        'date':datetime.now(timezone.utc).isoformat(),
        'out':str(a.out),
        'no_height_policy_approved':True,
        'BIF_ZBOT_DATM_or_spinup_written':False,
        'limitations':'Aliases unverified; historic TA height missing at two sites; local standard time policy must be confirmed; BIF repeats are not independent.'}
    (a.out/'06_provenance_and_limitations.json').write_text(json.dumps(meta, indent=2)+'\n')
    print('\n=== STAGE24 SUMMARY ===')
    print(pd.DataFrame(summary)[['site','unique_TA_dates','first_TA_m','NOLEAP_early_TA_halfhours','next_action']].to_string(index=False))
    print('\nPOSSIBLE UNVERIFIED TA ALIASES DE-Lnf and IT-Col:')
    if alias_df.empty:print('NONE FOUND in currently downloaded BIF sources')
    else:print(alias_df[['site','bif_variable_name','raw_height','raw_effective_date']].drop_duplicates().to_string(index=False))
    print('\nREPORTS:',a.out)
    print('READ ONLY: no forcing, BIF, ZBOT, DATM, or model cases modified.')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Read-only v5 summary; never edits raw or processed forcing."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

root = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
sites = ['DE-Hai', 'RU-Fyo', 'DE-Tha', 'DK-Sor', 'NL-Loo', 'IL-Yat']
summary = []

for site in sites:
    qc = root / site / 'forcing/qc_v5'
    status_file = qc / f'{site}_status.json'
    if not status_file.exists():
        print(f'\n{site}: v5 not run')
        continue
    status = json.loads(status_file.read_text())
    print(f'\n========== {site} ==========', flush=True)
    if status.get('status') == 'FAIL':
        print('FAIL:', status.get('error'))
        continue
    e = pd.read_csv(qc / f'{site}_replacement_events.csv')
    r = pd.read_csv(qc / f'{site}_manual_review.csv')
    low = pd.read_csv(qc / f'{site}_low_RH_diagnostic.csv')
    e['official_qc'] = pd.to_numeric(e['official_qc'], errors='coerce')
    qc0 = e[e['official_qc'] == 0]
    print('Status:', status['status'])
    print('Changed site-variable records:', len(e))
    print('Changed official-measured QC=0:', len(qc0))
    print('QC=0 changes per variable:', qc0.variable.value_counts().to_dict())
    print('Review rows:', len(r), '| unique half-hours:', r.time.nunique())
    print('Review reasons:', r.reason.value_counts().head(8).to_dict())
    print('Remaining RH<1%:', len(low))
    if 'near_zero_TA_and_6p110' in low:
        near = low[low.near_zero_TA_and_6p110.fillna(False).astype(bool)].copy()
    else:
        near = low.iloc[0:0].copy()
    print('Remaining TA≈0 VPD≈6.110:', len(near))
    summary.append({'site': site, 'status': status['status'],
                    'changes': len(e), 'changed_qc0': len(qc0),
                    'review_rows': len(r), 'review_unique_times': r.time.nunique(),
                    'remaining_rh_lt_1': len(low), 'remaining_zero_plateau': len(near)})
    if site == 'NL-Loo' and len(near):
        ta = pd.to_numeric(near['TA_ERA_C'], errors='coerce')
        era_vpd = pd.to_numeric(near['VPD_ERA_hPa'], errors='coerce')
        es = 6.112 * np.exp(17.67 * ta / (ta + 243.5))
        near['ERA_RH_pct'] = 100 * (1 - era_vpd / es)
        near = near.sort_values('time')
        dest = Path.home() / 'NL-Loo_remaining_zero_plateau_v5.csv'
        near.to_csv(dest, index=False)
        print('ERA RH ≥ 50% among remaining zero-plateau:',
              int((near['ERA_RH_pct'] >= 50).sum()))
        print('Year counts:', near['time'].str[:4].value_counts().to_dict())
        print('Details saved:', dest)

if summary:
    out = Path.home() / 'six_site_qc_v5_final_audit.csv'
    pd.DataFrame(summary).to_csv(out, index=False)
    print('\nSIX SITE SUMMARY')
    print(pd.DataFrame(summary).to_string(index=False))
    print('Saved:', out)

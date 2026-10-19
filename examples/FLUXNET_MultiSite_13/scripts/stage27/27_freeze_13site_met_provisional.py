#!/usr/bin/env python3
"""Checkpoint the 13-site Stage26-selected MET candidate without modifying forcing.

This is an immutable, read-only-derived PROVISIONAL inventory, NOT science
approval. Requires Stage22/24/26 reports and verifies all candidate SHA256.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SITES = [
    'DE-Lnf', 'DE-Obe', 'ES-Agu', 'ES-LJu', 'IT-Col', 'DE-Gri',
    'DE-RuR', 'FI-Hyy', 'FI-Let', 'FR-Pue', 'GF-Guy', 'IT-MBo', 'IT-Tor',
]
FOCUS = {'DE-Lnf','FI-Hyy','IT-Tor'}
PRIORITY = {
    'DE-Lnf': 'retain original QC0 temperature; review 2 jumps and 4 near-zero RH; TA height absent',
    'DE-Obe': 'retain rainfall pending independent intensity/time-accumulation confirmation',
    'ES-Agu': 'review extraordinary 2018-09-15 rainfall / aggregation before science acceptance',
    'ES-LJu': 'review 6 temperature jumps and heavy rainfall 23:00 timing',
    'IT-Col': 'review 2 temperature jumps; TA sensor height metadata absent',
    'DE-Gri': '49 Stage22 MDS blocks without full trial; preserve uncertainty',
    'DE-RuR': 'review the 2012-07-27 measured rain event; no auto edit',
    'FI-Hyy': 'one provisional VPD edit in Stage26; review 10-HH T MDS vs ERA, 3 near-zero RH, long VPD gapfill',
    'FI-Let': '20 Stage22 MDS blocks without full trial; preserve uncertainty',
    'FR-Pue': 'review intense rain provenance and accumulation',
    'GF-Guy': 'review convective rain provenance, accumulation time',
    'IT-MBo': 'review 3 temperature jumps and exceptional rainfall',
    'IT-Tor': 'review 2025-10/11 QC1 vs QC2 source discontinuities, 1458-HH fill interval',
}


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for part in iter(lambda: f.read(4*1024*1024), b''):
            h.update(part)
    return h.hexdigest()


def check_exact_set(df, name):
    if 'site' not in df or len(df)!=13 or set(df.site)!=set(SITES) or df.site.duplicated().any():
        raise ValueError(f'{name}: expected 13 unique sites, got {df.site.tolist()}')


def main():
    home=Path.home()
    base=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments')
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage26', type=Path, default=base/'FLUXNET_MultiSite_13_MET_stage26_20261018_050050_967884'/'reports')
    ap.add_argument('--stage22', type=Path, default=base/'FLUXNET_MultiSite_13_stage22_retry_20261018_041156_893243'/'reports')
    ap.add_argument('--stage24', type=Path, default=home/'FLUXNET_13_stage24_BIF_unique_NOLEAP_20261018_040135_133053')
    ap.add_argument('--out', type=Path, required=True)
    a=ap.parse_args()
    files={
        'stage26_manifest':a.stage26/'01_selected_13site_stage26_provisional_manifest.csv',
        'stage26_qc':a.stage26/'02_all13_numeric_QC_after_trial.csv',
        'stage26_ledger':a.stage26/'05_exact_stage26_trial_ledger.csv',
        'stage22_blocks':a.stage22/'07_82_MDS_blocks_after_stage22.csv',
        'stage22_rain':a.stage22/'INHERITED_STAGE21_05_precipitation_provenance_summary.csv',
        'stage24_height':a.stage24/'02_13site_NOLEAP_height_gap_summary.csv',
    }
    for name,path in files.items():
        if not path.is_file():raise FileNotFoundError(f'{name}: {path}')
    m=pd.read_csv(files['stage26_manifest'])
    q=pd.read_csv(files['stage26_qc'])
    rain=pd.read_csv(files['stage22_rain'])
    height=pd.read_csv(files['stage24_height'])
    blocks=pd.read_csv(files['stage22_blocks'])
    ledger=pd.read_csv(files['stage26_ledger'])
    check_exact_set(m, 'Stage26 manifest')
    check_exact_set(q, 'Stage26 QC')
    check_exact_set(height, 'Stage24 BIF')
    if 'site' not in rain or set(rain.site)!=set(SITES):
        raise ValueError('Rain report missing sites')
    if len(blocks)!=82:raise ValueError('Stage22 block count is not 82')
    if len(ledger)!=1 or set(ledger.site)!={'FI-Hyy'}:
        raise ValueError('Stage26 expected one FI-Hyy trial edit; inspect source reports')
    if 'scientific_MET_approved' not in m:
        raise ValueError('Missing scientific approval field')
    if m['scientific_MET_approved'].astype(str).str.lower().isin(['true','1','yes']).any():
        raise ValueError('Unexpected scientific approval: do not declare scientific pass')
    if pd.to_numeric(q.numeric_hard_failures, errors='raise').sum()!=0:
        raise ValueError('Numeric QC is not all zero')
    q=q.set_index('site');height=height.set_index('site');rain=rain.set_index('site')
    pending_names={'NO_STAGE22_EDIT_STILL_PENDING','STAGE22_PARTIAL_FLAGGED_BLOCK_STILL_PENDING'}
    pending=blocks[blocks.stage22_action.isin(pending_names)].groupby('site').size().to_dict()
    rows=[]
    for site in SITES:
        r=m.loc[m.site==site].iloc[0]
        path=Path(str(r.forcing_path))
        if not path.is_file():raise FileNotFoundError(path)
        actual=digest(path)
        if actual!=str(r.sha256):raise ValueError(f'{site}: SHA256 mismatch {path}')
        z=height.loc[site]
        qc=q.loc[site]
        rn=rain.loc[site]
        status='PROVISIONAL_NUMERIC_PASS_SCIENCE_OPEN'
        priority=('HIGH_HOLD_SCIENCE' if site in FOCUS or pending.get(site,0)>0 else
                  'EVENT_EVIDENCE_REVIEW')
        first_height=z.get('first_TA_m')
        lack_height=pd.isna(first_height) or str(first_height).strip()==''
        rows.append({
            'site':site,'forcing_path':str(path),'sha256':actual,
            'lineage':'Stage26 selected manifest (inherits Stage22 except 1 FI-Hyy VPD trial)',
            'met_status':status,'science_approved':False,
            'priority':priority,'remaining_MDS_original_blocks':int(pending.get(site,0)),
            'TA_step_gt12C':int(qc.TA_step_gt_12C),
            'RH_below1pct':int(qc.RH_below_1pct),
            'rain_gt18mm_HH':int(rn.rain_above18_mm_HH),
            'rain_gt40mm_HH':int(rn.rain_above40_mm_HH),
            'rain_gt18_at23h':int(rn.rain_above18_at_23h00),
            'TA_BIF_first_height_m':None if lack_height else float(first_height),
            'TA_BIF_missing':bool(lack_height),
            'TA_BIF_early_gap_NOLEAP_HH':None if pd.isna(z.get('NOLEAP_early_TA_halfhours')) else int(z.NOLEAP_early_TA_halfhours),
            'BIF_action':str(z.next_action),
            'next_science_action':PRIORITY[site],
        })
        print(f'{site:<7} SHA_OK | hard=0 | MDS_pending={pending.get(site,0):2} | '
              f'T>12={int(qc.TA_step_gt_12C):2} | RH<1={int(qc.RH_below_1pct):2} | '
              f'BIF_TA_missing={lack_height}', flush=True)
    out=a.out
    if out.exists():raise FileExistsError(f'Output exists, refusing overwrite: {out}')
    out.mkdir(parents=True, exist_ok=False)
    summary=pd.DataFrame(rows)
    summary.to_csv(out/'01_13site_PROVISIONAL_met_frozen_manifest.csv',index=False)
    summary.drop(columns=['forcing_path','sha256']).to_csv(out/'02_13site_science_and_BIF_gates.csv',index=False)
    proven={name:{'path':str(path),'sha256':digest(path)} for name,path in files.items()}
    meta={'state':'PROVISIONAL_NUMERIC_PASS_NOT_SCIENCE_APPROVAL',
          'created_utc':datetime.now(timezone.utc).isoformat(),
          'site_count':13,'numeric_pass_count':13,'scientific_pass_count':0,
          'new_stage26_edit_count':len(ledger),
          'pending_stage22_original_MDS_blocks':sum(pending.values()),
          'provenance':proven,
          'usage_limit':'Diagnostic DATM/smoke tests only after appropriate BIF assumptions. No production spinup or publication claims.',
          'source_safety':'No original flux tower files or forcing files copied or overwritten.'}
    (out/'03_checkpoint_provenance.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
    (out/'README_LIMITATIONS.md').write_text(
        '# 13-site provisional MET checkpoint after Stage26\n\n'
        '**NUMERICAL PASS 13/13 DOES NOT EQUAL SCIENTIFIC PASS.**\n\n'
        'Files in this folder are index, status and provenance only. All referenced original'
        ' and trial forcing CSVs remain unchanged on IRIDIS6. No source files are copied.\n\n'
        'Stage26 contributes exactly one FI-Hyy VPD-only candidate edit at 2003-04-25 10:30.'
        ' It remains scientifically provisional. Remaining FI-Hyy 10 half-hours of MDS temperature'
        ' differ greatly from ERA; DE-Lnf has two QC0 temperature jumps and four RH<1% records;'
        ' IT-Tor has a 1458-HH QC1/2 gapfill interval and four jump events.'
        ' ERA and FLUXNET site-ERA values are not independent ground truth.\n\n'
        'DE-Gri and FI-Let retain 49 and 20 original MDS blocks without full repair trials.'
        ' Strong precipitation events at other sites are retained with source/time uncertainties.'
        ' Before production-grade spinup, science review and explicit BIF/ZBOT decisions remain required.'
        ' DE-Lnf and IT-Col have missing TA sensor height evidence.\n',encoding='utf-8')
    print('\n=== MET CHECKPOINT CREATED ===')
    print('Forcing SHA256 verified: 13/13')
    print('Numeric PASS: 13/13; Scientific PASS: 0/13')
    print('One Stage26 VPD candidate retained at FI-Hyy; no new edits made')
    print('MDS pending original blocks:',sum(pending.values()))
    print('CHECKPOINT:',out)
    print('READ ONLY on raw / MET forcing / previous stage outputs')

if __name__=='__main__':main()

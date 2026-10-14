#!/usr/bin/env python3
"""Stage 07: conservative, versioned PA-only QC trial for 11 FLUXNET sites.

Never alters raw data, the Stage03 baseline, surfaces, or DATM files.
Default: preflight only. --write-trial creates a new folder for three affected sites.
This is a candidate scientific-review product, NOT accepted/approved forcing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

DEFAULT_ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
YEARS={
 'BE-Bra':(1996,2025),'FR-Fon':(2005,2025),'GL-ZaH':(2000,2025),
 'IT-Noe':(2004,2025),'AT-Neu':(2002,2020),'FI-Sod':(2001,2025),
 'CH-Aws':(2006,2024),'CH-Cha':(2005,2024),'CH-Fru':(2005,2024),
 'CH-Lae':(2004,2024),'CZ-Stn':(2010,2024)
}
PATCH_SITES={'CH-Fru':6,'CH-Lae':3,'CZ-Stn':3}
MET=('TA','VPD','PA','SW_IN','LW_IN','WS','P')
HARD={'TA':(-80,65),'VPD':(-.1,125),'PA':(50,110),'SW_IN':(-5,1600),
      'LW_IN':(60,800),'WS':(-.1,75),'P':(-.001,300)}

def saturation_hpa(t):
    with np.errstate(over='ignore',under='ignore',invalid='ignore',divide='ignore'):
        x=17.67*t/(t+243.5)
        return 6.112*np.exp(np.clip(x,-100,100))

def metrics(df):
    a={v:pd.to_numeric(df[v+'_F'],errors='coerce').to_numpy(dtype='float64') for v in MET}
    e=saturation_hpa(a['TA']); actual=e-a['VPD']
    ps=a['PA']*1000.0
    with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
        q=.622*(actual*100)/(ps-.378*(actual*100))
        rh=100*actual/e
    range_ok=np.ones(len(df),dtype=bool)
    for v,(lo,hi) in HARD.items():
        range_ok &= np.isfinite(a[v])&(a[v]>=lo)&(a[v]<=hi)
    humidity_ok=(np.isfinite(rh)&np.isfinite(q)&(actual>0)&(rh<=100.05)&
                 (q>=0)&(q<=.08))
    return a, rh, q, actual, range_ok, humidity_ok

def hash_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(2**22),b''): h.update(block)
    return h.hexdigest()

def find_candidate(root,site,tag):
    first,last=YEARS[site]
    d=root/site/'forcing'/f'merged_multisource_11_{tag}'
    f=d/f'{site}_multisource_HH_{first}_{last}_candidate.csv'
    if not f.is_file():raise FileNotFoundError(f'Create Stage03 baseline first: {f}')
    return f

def time_check(df,site):
    first,last=YEARS[site]
    if 'time' not in df:raise RuntimeError(f'{site}: missing time')
    times=pd.to_datetime(df['time'],errors='raise')
    idx=pd.DatetimeIndex(times)
    expected=pd.date_range(f'{first}-01-01',f'{last}-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(idx)!=len(expected) or not idx.equals(expected):
        raise RuntimeError(f'{site}: not exact NO_LEAP HH chronology: {len(idx)} versus {len(expected)}')
    return idx

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    ap.add_argument('--proposal',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage06_science_diagnostics/05_pressure_repair_PROPOSALS_NOT_APPLIED.csv')
    ap.add_argument('--source-tag',default='v07a',help='Stage03 baseline version tag')
    ap.add_argument('--trial-tag',default='pressure07a',help='NEW output tag for PA-only trial')
    ap.add_argument('--report',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage07_pressure_trial')
    ap.add_argument('--write-trial',action='store_true',help='Write NEW REVIEW-ONLY CSVs for three PA sites')
    args=ap.parse_args()
    if not (args.source_tag.isalnum() and args.trial_tag.isalnum() and args.source_tag!=args.trial_tag):
        ap.error('Tags must be distinct alphanumeric names')
    if not args.proposal.is_file():raise SystemExit(f'Cannot read proposal: {args.proposal}')
    proposals=pd.read_csv(args.proposal)
    required={'site','time','variable','original_kPa','proposed_kPa','original_QC','left_boundary_time','right_boundary_time','left_boundary_kPa','right_boundary_kPa','approval'}
    if not required.issubset(proposals.columns):raise SystemExit(f'Proposal columns missing: {required-set(proposals.columns)}')
    if set(proposals.site)!=set(PATCH_SITES):raise SystemExit('Unexpected proposal sites; manually inspect before proceeding')
    if len(proposals)!=sum(PATCH_SITES.values()):raise SystemExit(f'Expected exactly 12 pressure proposals, got {len(proposals)}')
    if proposals.duplicated(['site','time']).any():raise SystemExit('Duplicated proposal site/times')
    for site,num in PATCH_SITES.items():
        if (proposals.site==site).sum()!=num:raise SystemExit(f'{site}: expected {num} proposals')
    if not (proposals.variable=='PA_F').all():raise SystemExit('Only PA_F replacements may be proposed')
    if not (proposals.approval=='NOT_APPROVED_DO_NOT_USE_IN_DATM').all():
        raise SystemExit('Proposal approvals unexpected: inspect the source')

    # Preflight ALL baselines and all output directories before modifying anything.
    baselines={site:find_candidate(args.root,site,args.source_tag) for site in YEARS}
    if args.write_trial:
        for site in PATCH_SITES:
            output=args.root/site/'forcing'/f'merged_multisource_11_{args.trial_tag}'
            if output.exists():raise SystemExit(f'Refusing to overwrite existing trial directory: {output}')
    args.report.mkdir(parents=True,exist_ok=True)
    all_rows=[]; ledger=[]; unresolved=[]
    for site,source_file in baselines.items():
        print(f'\n=== {site} ===',flush=True)
        df=pd.read_csv(source_file,low_memory=False)
        idx=time_check(df,site)
        if any(v+'_F' not in df for v in MET):raise RuntimeError(f'{site}: missing required candidate meteorology')
        selected=proposals.loc[proposals.site==site].copy()
        if len(selected):
            selected['time']=pd.to_datetime(selected.time)
            current_positions={t:i for i,t in enumerate(idx)}
            for row in selected.itertuples(index=False):
                t=pd.Timestamp(row.time)
                if t not in current_positions:raise RuntimeError(f'{site}: proposed time absent: {t}')
                i=current_positions[t]
                old=float(df.loc[i,'PA_F'])
                if not np.isfinite(old) or abs(old-float(row.original_kPa))>0.0011:
                    raise RuntimeError(f'{site}: baseline PA mismatch {t}: {old} vs {row.original_kPa}')
                if not (50<float(row.proposed_kPa)<110):raise RuntimeError(f'{site}: proposed PA not plausible {t}')
                if str(df.loc[i,'PA_F_SOURCE'])!='EUF_F':
                    raise RuntimeError(f'{site}: expected EUF_F PA source at {t}, got {df.loc[i,"PA_F_SOURCE"]}')
                oldqc=float(df.loc[i,'PA_F_QC'])
                if not np.isfinite(oldqc) or abs(oldqc-float(row.original_QC))>1e-6:
                    raise RuntimeError(f'{site}: official QC does not match proposal at {t}')
                # Exact interpolation boundary data must also still match the baseline.
                lt,rt=pd.Timestamp(row.left_boundary_time),pd.Timestamp(row.right_boundary_time)
                if lt not in current_positions or rt not in current_positions:
                    raise RuntimeError(f'{site}: PA interpolation boundary missing for {t}')
                lv=float(df.loc[current_positions[lt],'PA_F'])
                rv=float(df.loc[current_positions[rt],'PA_F'])
                if abs(lv-float(row.left_boundary_kPa))>0.0011 or abs(rv-float(row.right_boundary_kPa))>0.0011:
                    raise RuntimeError(f'{site}: interpolation boundaries have changed at {t}')
                fraction=(t-lt)/(rt-lt)
                interp=lv+(rv-lv)*fraction
                if abs(interp-float(row.proposed_kPa))>0.0011:
                    raise RuntimeError(f'{site}: proposal does not match interpolation {t}')
                ledger.append({'site':site,'time':t,'variable':'PA_F',
                     'old_kPa':old,'trial_kPa':interp,'original_QC':oldqc,
                     'old_source':str(df.loc[i,'PA_F_SOURCE']),
                     'new_source':'LOCAL_PRESSURE_INTERPOLATION_TRIAL',
                     'left_time':lt,'right_time':rt,'left_kPa':lv,'right_kPa':rv,
                     'reason':'evident_short_ERAbased_pressure_corruption_with_valid_adjacent_pressure',
                     'approval':'REVIEW_ONLY_NOT_APPROVED_FOR_DATM'})
            # Validation succeeded, apply all edits in memory only to a new candidate.
            df['PA_F_BEFORE_TRIAL']=np.nan
            df['PA_F_SOURCE_BEFORE_TRIAL']=''
            df['PA_TRIAL_FLAG']=False
            for x in [r for r in ledger if r['site']==site]:
                i=current_positions[x['time']]
                df.loc[i,'PA_F_BEFORE_TRIAL']=x['old_kPa']
                df.loc[i,'PA_F_SOURCE_BEFORE_TRIAL']=x['old_source']
                df.loc[i,'PA_F']=x['trial_kPa']
                df.loc[i,'PA_F_SOURCE']='LOCAL_PRESSURE_INTERPOLATION_TRIAL'
                df.loc[i,'PA_TRIAL_FLAG']=True
        _,rh,q,ea,range_ok,humidity_ok=metrics(df)
        complete=np.ones(len(df),dtype=bool)
        for v in MET:complete&=np.isfinite(pd.to_numeric(df[v+'_F'],errors='coerce').to_numpy(dtype=float))
        numerical_ok=complete&range_ok&humidity_ok
        if len(selected):
            df['RH_IMPLIED_PCT']=rh
            df['QBOT_DIAGNOSTIC_KG_KG']=q
            df['PAIR_STATUS']=df['PAIR_STATUS'].astype(str)
            df.loc[df['PA_TRIAL_FLAG'] & humidity_ok,'PAIR_STATUS']='PA_LOCAL_INTERPOLATION_TRIAL_HUMIDITY_OK'
            df.loc[df['PA_TRIAL_FLAG'] & ~humidity_ok,'PAIR_STATUS']='PA_LOCAL_INTERPOLATION_TRIAL_STILL_INVALID'
        # Other meteorological variables may still be missing (CH-Lae).
        # Validate only the repaired pressure and triplet here; a separate QC gate
        # below continues to BLOCK a file with any remaining unrelated gaps.
        if len(selected) and not humidity_ok[np.flatnonzero(df['PA_TRIAL_FLAG'].to_numpy())].all():
            raise RuntimeError(f'{site}: PA trial still has invalid humidity, refuse to write')
        problem=np.flatnonzero(~numerical_ok)
        for i in problem:
            if len(unresolved)<5000: # no truncation for current known 559+2; guard report size
                missing=';'.join(v for v in MET if not np.isfinite(float(df.iloc[i][v+'_F'])))
                unresolved.append({'site':site,'time':idx[i], 'pair_status':df.iloc[i].get('PAIR_STATUS',''),
                    'TA_C':df.iloc[i]['TA_F'],'VPD_hPa':df.iloc[i]['VPD_F'],'PA_kPa':df.iloc[i]['PA_F'],
                    'RH_pct':rh[i],'QBOT_kgkg':q[i], 'missing_met':missing,
                    'range_ok':bool(range_ok[i]),'humidity_ok':bool(humidity_ok[i])})
        status=('BLOCKED_HUMIDITY' if int((~humidity_ok&complete).sum()) else
                'BLOCKED_MISSING' if int((~complete).sum()) else
                'BLOCKED_RANGE' if int((~range_ok).sum()) else
                'CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW')
        all_rows.append({'site':site,'first':YEARS[site][0],'last':YEARS[site][1],
              'stage03_baseline':str(source_file),'pressure_trial_rows':int(len(selected)),
              'missing_any_met':int((~complete).sum()),
              'range_invalid':int((~range_ok&complete).sum()),
              'humidity_invalid':int((~humidity_ok&complete).sum()),
              'all_nonpass_numeric_rows':int((~numerical_ok).sum()),
              'status':status,'ready_for_DATM':False})
        print(f'  trial_pressure={len(selected)} missing={int((~complete).sum())} '
              f'humidity_invalid={int((~humidity_ok&complete).sum())} status={status}',flush=True)
        if args.write_trial and site in PATCH_SITES:
            outdir=args.root/site/'forcing'/f'merged_multisource_11_{args.trial_tag}'
            outdir.mkdir(parents=False,exist_ok=False)
            f=outdir/f'{site}_multisource_HH_{YEARS[site][0]}_{YEARS[site][1]}_candidate.csv'
            tmp=outdir/(f.name+'.partial')
            try:
                df.to_csv(tmp,index=False)
                tmp.replace(f)
                metadata={'site':site,'status':status,'stage':'PA_LOCAL_INTERPOLATION_REVIEW_ONLY',
                     'baseline_file':str(source_file),'baseline_sha256':hash_file(source_file),
                     'trial_file':str(f),'trial_sha256':hash_file(f),
                     'modified_pressure_records':int(len(selected)),
                     'scientific_approval':'NOT_APPROVED_FOR_DATM_OR_SPINUP'}
                (outdir/'status.json').write_text(json.dumps(metadata,indent=2))
            finally:
                tmp.unlink(missing_ok=True)
    pd.DataFrame(all_rows).to_csv(args.report/'01_eleven_site_numeric_status.csv',index=False)
    pd.DataFrame(ledger).to_csv(args.report/'02_pressure_trial_ledger.csv',index=False)
    pd.DataFrame(unresolved).to_csv(args.report/'03_remaining_unresolved_rows.csv',index=False)
    print('\n=== FINAL SUMMARY ===',flush=True)
    print(pd.DataFrame(all_rows)[['site','pressure_trial_rows','missing_any_met','humidity_invalid','status']].to_string(index=False),flush=True)
    print('All pressure modifications are provisional and have NOT been scientifically approved.',flush=True)
    print('CH-Aws negative humidity remains blocked. No DATM generated.',flush=True)
    print('Report:',args.report,flush=True)

if __name__=='__main__':
    try:main()
    except Exception as ex:
        print('ERROR:',repr(ex),file=sys.stderr,flush=True)
        raise

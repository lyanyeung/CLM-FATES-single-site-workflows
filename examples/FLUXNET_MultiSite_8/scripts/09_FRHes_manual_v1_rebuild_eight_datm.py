#!/usr/bin/env python3
"""Human-reviewed FR-Hes 3 timestamp ERA pair correction, rebuild eight-site DATM.

Read-only raw/QC v5; creates versioned FR-Hes forcing and correction ledger.
Moves old FR-Hes NetCDFs into a backup directory; regenerates 8 site candidates.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
HOME = Path.home()
SITE = 'FR-Hes'
FIRST, LAST = 1997, 2025
EVENTS = {
    '2022-07-03 17:00:00': (18.690, 1, 2),
    '2022-07-03 18:00:00': (18.690, 1, 1),
    '2022-07-03 18:30:00': (18.380, 1, 1),
}
EXPECTED_YEARS = {
    'CZ-BK1': (2004, 2025), 'IT-Ren': (1999, 2025),
    'FR-Hes': (1997, 2025), 'FR-FBn': (2008, 2024),
    'DE-Hzd': (2010, 2025), 'CH-Dav': (1997, 2025),
    'BE-Vie': (1996, 2025), 'IT-Lav': (2003, 2020),
}


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def source_rows(path, column_names):
    available = set(pd.read_csv(path, nrows=0).columns)
    if 'TIMESTAMP_START' not in available:
        raise ValueError(f'Missing TIMESTAMP_START: {path}')
    use = ['TIMESTAMP_START', *[c for c in column_names if c in available]]
    df = pd.read_csv(path, usecols=use, dtype={'TIMESTAMP_START': str}, low_memory=False)
    stamp = df['TIMESTAMP_START'].str.strip().str.replace(r'\.0$', '', regex=True)
    df['time'] = pd.to_datetime(stamp, format='%Y%m%d%H%M', errors='raise')
    df = df[df.time.isin(pd.to_datetime(list(EVENTS)))].copy()
    if len(df) != len(EVENTS) or df.time.duplicated().any():
        raise RuntimeError(f'Missing/duplicate event times in {path}')
    return df.set_index('time')


def finite(val):
    x = pd.to_numeric(val, errors='coerce')
    return float(x) if pd.notna(x) and np.isfinite(x) and x > -9990 else np.nan


def assemble_event_inputs():
    raw = ROOT / SITE / 'forcing/raw'
    flux = list(raw.rglob('*FLUXMET_HH*.csv'))
    era = list(raw.rglob('*ERA5_HH*.csv'))
    if len(flux) != 1 or len(era) != 1:
        raise RuntimeError(f'FR-Hes expected 1 FLUXMET and 1 ERA5 CSV, found {len(flux)}, {len(era)}')
    f = source_rows(flux[0], ['TA_F', 'TA_F_QC', 'VPD_F', 'VPD_F_QC', 'TA_ERA', 'VPD_ERA'])
    e = source_rows(era[0], ['TA_ERA', 'VPD_ERA'])
    for col in ['TA_F', 'TA_F_QC', 'VPD_F', 'VPD_F_QC']:
        if col not in f:
            raise RuntimeError(f'Missing FLUXMET column {col}')
    for col in ['TA_ERA', 'VPD_ERA']:
        if col not in f:
            f[col] = np.nan
        if col not in e:
            raise RuntimeError(f'Missing ERA5 column {col}')
        for t in f.index:
            if not np.isfinite(finite(f.loc[t, col])):
                f.loc[t, col] = e.loc[t, col]
    return f, str(flux[0]), str(era[0])


def save_corrected_forcing():
    forcing = ROOT / SITE / 'forcing'
    original_path = forcing / 'processed_v5' / f'{SITE}_CLM_forcing_{FIRST}_{LAST}.csv'
    if not original_path.is_file():
        raise RuntimeError(f'Missing v5 forcing: {original_path}')
    original_sha = sha256(original_path)
    original = pd.read_csv(original_path, low_memory=False)
    needed = {'time','TA_USE','VPD_USE','TBOT','QBOT','PSRF'}
    if not needed.issubset(original.columns):
        raise RuntimeError(f'Missing processed-v5 columns: {needed-set(original.columns)}')
    times = pd.to_datetime(original.time, errors='raise')
    if len(original) != (LAST-FIRST+1)*17520 or times.duplicated().any():
        raise RuntimeError('FR-Hes original forcing is not a complete unique 29-year NOLEAP time series')
    met, flux_file, era_file = assemble_event_inputs()
    modified = original.copy()
    ledger=[]
    for time_string,(expected_TA, expected_TAQC, expected_VPDQC) in EVENTS.items():
        t = pd.Timestamp(time_string)
        indices = np.flatnonzero((times == t).to_numpy())
        if len(indices)!=1:
            raise RuntimeError(f'Expected one forcing row at {t}, got {len(indices)}')
        i=int(indices[0]); row=met.loc[t]
        ta_original = finite(row['TA_F'])
        ta_qc = finite(row['TA_F_QC'])
        vpd_qc = finite(row['VPD_F_QC'])
        ta_era = finite(row['TA_ERA'])
        vpd_era = finite(row['VPD_ERA'])
        if not np.isclose(ta_original, expected_TA, atol=0.002) or ta_qc != expected_TAQC or vpd_qc != expected_VPDQC:
            raise RuntimeError(f'Unexpected raw record at {t}: TA={ta_original}, TA_QC={ta_qc}, VPD_QC={vpd_qc}')
        if not np.isclose(original.at[i,'TA_USE'], ta_original, atol=0.002):
            raise RuntimeError(f'Unexpected existing TA_USE at {t}; stop rather than overwrite previous edits')
        if not (np.isfinite(ta_era) and np.isfinite(vpd_era) and 0 <= vpd_era < 125):
            raise RuntimeError(f'ERA temperature or VPD missing/invalid at {t}')
        if abs(ta_era - ta_original) < 5:
            raise RuntimeError(f'TA mismatch unexpectedly <5 C at {t}')
        es_hpa=6.112*np.exp(17.67*ta_era/(ta_era+243.5))
        if not (0 <= vpd_era < es_hpa):
            raise RuntimeError(f'ERA pair physically impossible at {t}: TA={ta_era} VPD={vpd_era} es={es_hpa}')
        ea_pa=(es_hpa-vpd_era)*100
        psrf=float(original.at[i,'PSRF'])
        qbot=0.622*ea_pa/(psrf-0.378*ea_pa)
        if not (0 <= qbot < 0.08):
            raise RuntimeError(f'Calculated QBOT invalid at {t}: {qbot}')
        old_t=float(original.at[i,'TA_USE'])
        old_v=float(original.at[i,'VPD_USE'])
        old_q=float(original.at[i,'QBOT'])
        modified.at[i,'TA_USE']=ta_era
        modified.at[i,'VPD_USE']=vpd_era
        modified.at[i,'TBOT']=ta_era+273.15
        modified.at[i,'QBOT']=qbot
        ledger.append({
            'site':SITE,'time':t.isoformat(),
            'TA_original_C':ta_original,'TA_official_QC':int(ta_qc),
            'TA_previous_v5_C':old_t,'TA_manual_v1_C':ta_era,
            'VPD_original_hPa':finite(row['VPD_F']),
            'VPD_official_QC':int(vpd_qc),
            'VPD_previous_v5_hPa':old_v,'VPD_manual_v1_hPa':vpd_era,
            'QBOT_previous_v5_kgkg':old_q,'QBOT_manual_v1_kgkg':qbot,
            'RH_manual_v1_pct':100*(1-vpd_era/es_hpa),
            'source':'FLUXNET site-downscaled TA_ERA and VPD_ERA',
            'decision':'manual_review_accepted_pairwise_ERA_at_isolated_TA_gapfill_discontinuities',
        })
    outdir=forcing/'processed_v5_manual_v1'
    outdir.mkdir(parents=True,exist_ok=True)
    target=outdir/original_path.name
    if target.exists():
        # An existing manual file should be left alone if a prior run generated it.
        existing=pd.read_csv(target, low_memory=False)
        if list(existing.columns) != list(modified.columns) or len(existing) != len(modified):
            raise RuntimeError(f'Existing manual forcing has different dimensions: {target}')
        for col in modified.columns:
            if col == 'time':
                same = existing[col].astype(str).equals(modified[col].astype(str))
            else:
                same = np.allclose(pd.to_numeric(existing[col], errors='coerce'),
                                   pd.to_numeric(modified[col], errors='coerce'),
                                   rtol=1e-10, atol=1e-12, equal_nan=True)
            if not same:
                raise RuntimeError(f'Existing edited forcing differs at {col}; investigate: {target}')
    else:
        tmp=target.with_suffix('.csv.partial')
        if tmp.exists():
            raise RuntimeError(f'Stale temporary forcing: {tmp}')
        try:
            modified.to_csv(tmp,index=False)
            reread=pd.read_csv(tmp,low_memory=False)
            for t in EVENTS:
                i=int(np.flatnonzero((times==pd.Timestamp(t)).to_numpy())[0])
                for k in ['TA_USE','VPD_USE','TBOT','QBOT']:
                    if not np.isclose(reread.at[i,k],modified.at[i,k],rtol=1e-10,atol=1e-12):
                        raise RuntimeError(f'Roundtrip mismatch {t} {k}')
            tmp.replace(target)
        finally:
            if tmp.exists():tmp.unlink()
    corrected_sha=sha256(target)
    auditdir=HOME/'eight_site_FRHes_manual_v1_review'
    auditdir.mkdir(exist_ok=True)
    pd.DataFrame(ledger).to_csv(auditdir/'FR-Hes_three_manual_corrections.csv',index=False)
    manifest={
        'site':SITE, 'version':'manual_v1', 'source_processed_v5_path':str(original_path),
        'source_processed_v5_sha256':original_sha,
        'corrected_forcing_path':str(target),
        'corrected_forcing_sha256':corrected_sha,
        'fluxmet_path':flux_file,'era_path':era_file,
        'changed_timestamps':list(EVENTS), 'changed_fields':['TA_USE','VPD_USE','TBOT','QBOT'],
        'unchanged':'All other forcing records and variables, original QC files, raw data',
        'reason':'Three isolated TA_F_QC=1 cold fill artefacts embedded in warm ERA-driven hours. Use corresponding TA_ERA and VPD_ERA as physically consistent pairs.',
        'status':'USER_MANUAL_REVIEW_ACCEPTED_FOR_PROVISIONAL_DATM',
        'DE-Hzd_warning':'User elected to retain official precipitation. Annual total ~2.1-4.1 m remains unverified.'
    }
    (auditdir/'FR-Hes_manual_v1_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print('\n=== FR-Hes 3 manual changes (only new version; source v5 untouched) ===',flush=True)
    print(pd.DataFrame(ledger)[['time','TA_previous_v5_C','TA_manual_v1_C','VPD_previous_v5_hPa','VPD_manual_v1_hPa','RH_manual_v1_pct']].round(3).to_string(index=False),flush=True)
    print('Original SHA256:', original_sha, '\nNew SHA256:',corrected_sha,flush=True)
    print('Manual revision:',target,flush=True)
    return target, corrected_sha


def make_builder():
    src=HOME/'07_make_eight_site_datm_timevarying_zbot.py'
    dst=HOME/'07_make_eight_site_datm_FRHes_manual_v1.py'
    if not src.is_file():
        raise RuntimeError(f'Existing eight-site generator missing: {src}')
    text=src.read_text()
    old="    f = site_root / 'forcing' / 'processed_v5' / f'{site}_CLM_forcing_{first}_{last}.csv'"
    new="    folder = 'processed_v5_manual_v1' if site == 'FR-Hes' else 'processed_v5'\n    f = site_root / 'forcing' / folder / f'{site}_CLM_forcing_{first}_{last}.csv'"
    if text.count(old)!=1:
        raise RuntimeError('Cannot uniquely patch eight-site generator. No raw scripts overwritten.')
    text=text.replace(old,new)
    compile(text,str(dst),'exec')
    if dst.exists() and dst.read_text()!=text:
        raise RuntimeError(f'Existing customized builder differs: {dst}')
    dst.write_text(text)
    print('Created version-aware generator:',dst,flush=True)
    return dst


def backup_stale_FRHes_datm(corrected_sha):
    folder=ROOT/SITE/'forcing/datm_v5_candidate_timevarying_zbot'
    backup=ROOT/SITE/'forcing/datm_v5_before_manual_v1_backup'
    moved=[];already=[]
    for year in range(FIRST,LAST+1):
        old=folder/f'{SITE}_DATM_{year}.nc'
        if not old.exists():continue
        with Dataset(old) as nc:
            existing_hash=getattr(nc,'source_processed_csv_sha256','')
        if existing_hash==corrected_sha:
            already.append(year)
            continue
        backup.mkdir(parents=True,exist_ok=True)
        dest=backup/old.name
        if dest.exists():
            raise RuntimeError(f'Backup filename already exists; prevent overwrite: {dest}')
        shutil.move(str(old),str(dest))
        moved.append(year)
    print(f'FR-Hes: preserved {len(moved)} OLD DATM files under {backup}',flush=True)
    print(f'FR-Hes: {len(already)} already match manual_v1 SHA256',flush=True)
    return backup


def verify_datm(corrected_sha, corrected_path):
    found=0;problems=[]
    for site,(start,end) in EXPECTED_YEARS.items():
        datmdir=ROOT/site/'forcing/datm_v5_candidate_timevarying_zbot'
        ok=0
        for year in range(start,end+1):
            target=datmdir/f'{site}_DATM_{year}.nc'
            if not target.is_file():
                problems.append(f'MISSING {target}');continue
            try:
                with Dataset(target) as nc:
                    if len(nc.dimensions['time'])!=17520 or getattr(nc['time'],'calendar','') not in ('noleap','365_day'):
                        raise ValueError('Not 17520 NOLEAP half-hour records')
                    if getattr(nc,'site','')!=site or int(getattr(nc,'forcing_year',-1))!=year:
                        raise ValueError('Mismatched site or year attributes')
                    if site=='FR-Hes':
                        if getattr(nc,'source_processed_csv_sha256','')!=corrected_sha:
                            raise ValueError('FR-Hes NetCDF not sourced from revised CSV')
                        if getattr(nc,'source_processed_csv','')!=str(corrected_path):
                            raise ValueError('FR-Hes NetCDF source path does not match manual_v1')
                        if year==2022:
                            df=pd.read_csv(corrected_path)
                            df['time']=pd.to_datetime(df['time'])
                            for ts in EVENTS:
                                dtime=pd.Timestamp(ts)
                                index=(dtime.dayofyear-1)*48+dtime.hour*2+dtime.minute//30
                                row=df[df.time==dtime]
                                if len(row)!=1:
                                    raise ValueError(f'No corrected CSV row {ts}')
                                for key in ('TBOT','QBOT'):
                                    a=float(nc[key][index,0,0]); b=float(row[key].iloc[0])
                                    if not np.isclose(a,b,rtol=1e-5,atol=1e-7):
                                        raise ValueError(f'{ts} {key}: NC={a}, CSV={b}')
                ok+=1
            except Exception as e:
                problems.append(f'{target}: {e}')
        found+=ok
        print(f'{site:7} verified {ok:2}/{end-start+1}',flush=True)
    print(f'TOTAL VERIFIED {found}/188',flush=True)
    if problems:
        print('First problems:',*problems[:12],sep='\n  ',flush=True)
        raise RuntimeError(f'{len(problems)} DATM verification issues')


def main():
    corrected, newhash=save_corrected_forcing()
    generator=make_builder()
    backup_stale_FRHes_datm(newhash)
    print('\n=== Building/verifying 8 sites, 188 annual provisional DATM files ===',flush=True)
    cmd=[sys.executable,str(generator),'--allow-review','--allow-early-extrapolation']
    print(' '.join(cmd),flush=True)
    subprocess.run(cmd,check=True)
    print('\n=== Independent verification ===',flush=True)
    verify_datm(newhash,corrected)
    print('\nSUCCESS: Eight-site provisional DATM complete; FR-Hes revised, CZ-BK1 unchanged.',flush=True)
    print('NOTE: DE-Hzd original high precipitation retained per user; not scientifically validated.',flush=True)
    audit=HOME/'08_audit_eight_site_datm_surface.py'
    if audit.exists():
        print('Running existing 08 eight-site full surface / DATM audit...',flush=True)
        subprocess.run([sys.executable,str(audit)],check=True)
    else:
        print('Full Surface/PFT audit script is absent: run 08_audit_eight_site_datm_surface.py once prepared.',flush=True)

if __name__=='__main__':
    main()

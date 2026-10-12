#!/usr/bin/env python3
"""Read-only diagnostics of eight-site QC-v5 humidity and longwave review events.

Inputs: eight_site_manual_review_register.csv, original FLUXMET_HH and ERA5_HH,
        and processed_v5 forcing CSV.
Outputs: /home/<user>/eight_site_targeted_review/{summary.csv,context.csv,figures/}
NO writes to raw, processed_v5, qc_v5, or DATM.
"""
from pathlib import Path
import re
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
HOME = Path.home()
OUT = HOME / 'eight_site_targeted_review'
YEARS = {'CZ-BK1': (2004, 2025), 'IT-Ren': (1999, 2025),
         'FR-Hes': (1997, 2025), 'IT-Lav': (2003, 2020)}
RAW_COLS = ['TA_F','VPD_F','LW_IN_F','SW_IN_F','TA_F_QC','VPD_F_QC','LW_IN_F_QC',
            'TA_ERA','VPD_ERA','LW_IN_ERA']
ERA_COLS = ['TA_ERA','VPD_ERA','LW_IN_ERA']
PROC_COLS = ['TA_USE','VPD_USE','FLDS']


def unique(path, pattern):
    found = sorted(path.rglob(pattern))
    if len(found) != 1:
        raise RuntimeError(f'Expected one {pattern} under {path}; found {len(found)}')
    return found[0]


def numeric(x):
    a = pd.to_numeric(x, errors='coerce')
    return a.mask(~np.isfinite(a) | (a <= -9990))


def parse_stamp(x):
    return pd.to_datetime(x.astype(str).str.strip().str.replace(r'\.0$', '',regex=True),
                          format='%Y%m%d%H%M', errors='raise')


def selected_data(path, columns, intervals, timestamp_col):
    hdr = list(pd.read_csv(path, nrows=0).columns)
    if timestamp_col not in hdr:
        raise RuntimeError(f'{path}: {timestamp_col} missing')
    available = [x for x in columns if x in hdr]
    parts = []
    for chunk in pd.read_csv(path, usecols=[timestamp_col, *available],
                             dtype={timestamp_col: 'str'}, chunksize=100000,
                             low_memory=False):
        if timestamp_col == 'TIMESTAMP_START':
            t = parse_stamp(chunk[timestamp_col])
        else:
            t = pd.to_datetime(chunk[timestamp_col], errors='raise')
        keep = pd.Series(False, index=chunk.index)
        for begin, end in intervals:
            keep |= t.between(begin, end)
        if keep.any():
            block = chunk.loc[keep, available].copy()
            block['time'] = t.loc[keep].to_numpy()
            parts.append(block)
    if not parts:
        raise RuntimeError(f'No records in reviewed windows for {path}')
    df = pd.concat(parts, ignore_index=True).sort_values('time')
    if df['time'].duplicated().any():
        raise RuntimeError(f'Duplicate timestamps in selected records: {path}')
    return df.set_index('time'), available


def load_data(site, times):
    raw_dir = ROOT / site / 'forcing' / 'raw'
    raw_path = unique(raw_dir, '*FLUXMET_HH*.csv')
    proc_path = (ROOT / site / 'forcing' / 'processed_v5' /
                 f'{site}_CLM_forcing_{YEARS[site][0]}_{YEARS[site][1]}.csv')
    if not proc_path.is_file():
        raise RuntimeError(f'Missing processed forcing: {proc_path}')
    intervals = [(t-pd.Timedelta(hours=12), t+pd.Timedelta(hours=12)) for t in times]
    raw, raw_available = selected_data(raw_path, RAW_COLS, intervals, 'TIMESTAMP_START')
    missing_core = [x for x in ['TA_F','VPD_F','LW_IN_F'] if x not in raw_available]
    if missing_core:
        raise RuntimeError(f'{site} missing raw {missing_core}')
    missing_era = [x for x in ERA_COLS if x not in raw_available]
    if missing_era:
        era_path = unique(raw_dir, '*ERA5_HH*.csv')
        era, ea = selected_data(era_path, missing_era, intervals, 'TIMESTAMP_START')
        raw = raw.join(era[ea], how='left', validate='one_to_one')
    proc, pc = selected_data(proc_path, PROC_COLS, intervals, 'time')
    if set(PROC_COLS) - set(pc):
        raise RuntimeError(f'{site} missing processed columns {set(PROC_COLS)-set(pc)}')
    joined = raw.join(proc, how='left', validate='one_to_one')
    for col in RAW_COLS + PROC_COLS:
        if col not in joined.columns:
            joined[col] = np.nan
        joined[col] = numeric(joined[col])
    return joined, raw_path, proc_path


def saturation(t):
    return 6.112 * np.exp(17.67 * t/(t+243.5))


def relative_humidity(t, vpd):
    return 100.0 * (1.0 - vpd / saturation(t))


def fmt(x, digits=3):
    return 'NA' if not np.isfinite(x) else f'{x:.{digits}f}'


def plot_event(window, site, stamp, var, path):
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                             gridspec_kw={'height_ratios':[2,1]})
    if var == 'LW_IN_F':
        series = [('LW original', 'LW_IN_F'), ('LW QC v5', 'FLDS'),
                  ('LW ERA', 'LW_IN_ERA')]
        for label, col in series:
            axes[0].plot(window.index, window[col], marker='.', markersize=3, label=label)
        axes[0].set_ylabel('LW downward [W m$^{-2}$]')
        axes[1].plot(window.index, window['TA_F'],label='Tower TA',marker='.',markersize=3)
        axes[1].plot(window.index, window['TA_ERA'],label='ERA TA',alpha=.7)
        axes[1].set_ylabel('TA [deg C]')
    else:
        for label, col in [('VPD original', 'VPD_F'),('VPD QC v5', 'VPD_USE'),
                           ('VPD ERA', 'VPD_ERA')]:
            axes[0].plot(window.index, window[col], marker='.', markersize=3, label=label)
        axes[0].set_ylabel('VPD [hPa]')
        if window['TA_F'].notna().any():
            axes[1].plot(window.index, relative_humidity(window.TA_F,window.VPD_F),
                         label='RH original', marker='.',markersize=2)
        axes[1].plot(window.index, relative_humidity(window.TA_USE,window.VPD_USE),
                     label='RH QC v5',marker='.',markersize=2)
        axes[1].plot(window.index, relative_humidity(window.TA_ERA,window.VPD_ERA),
                     label='RH ERA',alpha=.8)
        axes[1].axhline(0,color='gray',lw=.7,ls=':')
        axes[1].axhline(100,color='gray',lw=.7,ls=':')
        axes[1].set_ylabel('Implied RH [%]')
    for ax in axes:
        ax.axvline(stamp, color='black',ls='--',lw=.8)
        ax.grid(alpha=.2)
        ax.legend(fontsize=8, loc='best')
    axes[0].set_title(f'{site}  {stamp}  {var}  (QC v5 review only)')
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=135)
    plt.close(fig)


def main():
    path = HOME / 'eight_site_manual_review_register.csv'
    if not path.is_file():
        raise RuntimeError(f'Missing review register: {path}')
    reg = pd.read_csv(path)
    req = {'site','time','variable','reason'}
    if not req.issubset(reg.columns):
        raise RuntimeError(f'Review register columns missing: {req-set(reg.columns)}')
    reg['time'] = pd.to_datetime(reg.time,errors='raise')
    reg = reg.sort_values(['site','time','variable']).reset_index(drop=True)
    if not set(reg.site).issubset(YEARS):
        raise RuntimeError(f'Unexpected sites: {set(reg.site)-set(YEARS)}')
    if len(reg) != 15:
        print(f'WARNING: expected 15 review entries, found {len(reg)}')
    if reg.duplicated(['site','time','variable']).any():
        raise RuntimeError('Duplicate site/time/variable in review register')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'figures').mkdir(exist_ok=True)
    summaries, nearby = [], []
    for site, selection in reg.groupby('site', sort=True):
        data, raw_path, proc_path = load_data(site, selection.time.tolist())
        print(f'\n{site}: {len(selection)} review events')
        for event in selection.itertuples(index=False):
            t = event.time
            if t not in data.index:
                raise RuntimeError(f'{site}: no raw timestamp at {t}')
            a = data.loc[t]
            if not np.isfinite(a['TA_USE']) or not np.isfinite(a['VPD_USE']) or not np.isfinite(a['FLDS']):
                raise RuntimeError(f'{site} {t}: missing QC v5 value at review timestamp')
            context = data.loc[t-pd.Timedelta(hours=12):t+pd.Timedelta(hours=12)].copy()
            # Include every reviewed half-hour +/-2h in a machine-readable context file.
            local = context.loc[t-pd.Timedelta(hours=2):t+pd.Timedelta(hours=2)].copy()
            for time, rec in local.iterrows():
                row = {'site':site, 'review_time':t.isoformat(), 'time':time.isoformat()}
                row.update({col:rec[col] for col in RAW_COLS+PROC_COLS})
                nearby.append(row)
            if event.variable == 'VPD_F':
                original = a['VPD_F']; corrected = a['VPD_USE']; era = a['VPD_ERA']
                rh_orig = relative_humidity(a['TA_F'],original)
                rh_final = relative_humidity(a['TA_USE'],corrected)
                rh_era = relative_humidity(a['TA_ERA'],era)
                if not np.isfinite(rh_orig):
                    diagnostic = 'RAW_MISSING_CHECK_SOURCE'
                elif rh_orig < -0.05 or rh_orig > 100.05:
                    diagnostic = 'RAW_PHYSICALLY_INCONSISTENT'
                elif rh_orig < 1.0:
                    diagnostic = 'EXTREMELY_LOW_RH_REVIEW'
                else:
                    diagnostic = 'RAW_PHYSICALLY_POSSIBLE_REVIEW_REASON'
                if rh_final < -0.05 or rh_final > 100.05 or not np.isfinite(rh_final):
                    diagnostic = 'FINAL_PHYSICALLY_INVALID'
                # Signal if the record was not actually changed: a retained value is still a review.
                other = {'TA_tower_C':a['TA_F'],'TA_ERA_C':a['TA_ERA'],
                         'RH_original_pct':rh_orig,'RH_final_pct':rh_final,
                         'RH_ERA_pct':rh_era,'LW_neighbour_median':np.nan,
                         'LW_raw_blackbody_ratio':np.nan}
            elif event.variable == 'LW_IN_F':
                original=a['LW_IN_F']; corrected=a['FLDS']; era=a['LW_IN_ERA']
                neighbors = data.loc[t-pd.Timedelta(hours=2):t+pd.Timedelta(hours=2),'LW_IN_F'].drop(index=t,errors='ignore')
                neighbor_median = neighbors.median()
                bb = 5.670374419e-8 * (a['TA_F']+273.15)**4
                diagnostic = 'MEASURED_LW_CHANGED_REVIEW'
                other={'TA_tower_C':a['TA_F'],'TA_ERA_C':a['TA_ERA'],
                       'RH_original_pct':np.nan,'RH_final_pct':np.nan,'RH_ERA_pct':np.nan,
                       'LW_neighbour_median':neighbor_median,
                       'LW_raw_blackbody_ratio': original/bb if np.isfinite(bb) and bb>0 else np.nan}
            else:
                raise RuntimeError(f'Unexpected review variable: {event.variable}')
            original_qc = a[f'{event.variable}_QC']
            if 'official_qc' in reg.columns and pd.notna(getattr(event,'official_qc',np.nan)):
                if not np.isclose(original_qc, event.official_qc, equal_nan=True):
                    raise RuntimeError(f'{site} {t}: QC in register differs from original file')
            plot_file = OUT/'figures'/f'{site}_{t:%Y%m%d_%H%M}_{event.variable}.png'
            plot_event(context, site, t, event.variable, plot_file)
            summaries.append({'site':site,'time':t.isoformat(),'variable':event.variable,
                              'official_qc':original_qc,'original_FLUXMET':original,
                              'qc_v5_final':corrected,'ERA_reference':era,
                              'was_modified':bool(np.isfinite(original) and not np.isclose(original,corrected,atol=1e-5))
                                if np.isfinite(original) else None,
                              'difference_final_minus_raw': corrected-original,
                              'difference_raw_minus_ERA': original-era,
                              'diagnostic':diagnostic,'review_reason':event.reason,
                              'plot':str(plot_file),**other})
            print(f'  {t} {event.variable:7s} QC={fmt(original_qc,0):>2} '
                  f'raw={fmt(original):>9} final={fmt(corrected):>9} ERA={fmt(era):>9} '
                  f'RH_raw={fmt(other["RH_original_pct"],1):>5} '
                  f'RH_final={fmt(other["RH_final_pct"],1):>5} '
                  f'RH_ERA={fmt(other["RH_ERA_pct"],1):>5} [{diagnostic}]')
    summary = pd.DataFrame(summaries)
    summary.to_csv(OUT/'summary_15_events.csv',index=False)
    pd.DataFrame(nearby).to_csv(OUT/'context_2h_each_event.csv',index=False)
    print(f'\nREVIEW EVENTS: {len(summary)}')
    print(f'Diagnostic counts: {summary.diagnostic.value_counts().to_dict()}')
    print('Outputs:')
    print('  ', OUT/'summary_15_events.csv')
    print('  ', OUT/'context_2h_each_event.csv')
    print('  ', OUT/'figures')
    print('Note: diagnostic categories do not approve corrections. No source/forcing files changed.')

if __name__=='__main__':
    main()

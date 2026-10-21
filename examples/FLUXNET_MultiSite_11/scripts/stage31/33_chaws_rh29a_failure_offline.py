#!/usr/bin/env python3
"""Read-only post-mortem of CH-Aws RH29A job 4508890 (no CIME/Slurm changes).

Uses the actual failed land log and 2007 Stage29 v5 DATM NetCDF. The latest
history *file name* may be 2007-01-02 while its time dimension is EMPTY.
nstep=24048 at ATM_NCPL=48 suggests ~501 model days after 2006-01-01
(~2007-05-17) but is not proof of the precise crashing timestep.

Produces a small summary CSV under HOME and stdout. In particular, forcing
RH is not the 2-m model-diagnostic RH; no forcing-only statistic proves root
cause. This script does NOT suggest a blanket RH floor or edit source data.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime,timedelta
from netCDF4 import Dataset,num2date
import numpy as np
import pandas as pd
import re

RUN=Path('/scratch/ly3n24/CTSM_FATES_OUTPUTS/CH-Aws_FATES_SPINUP1000_RH29A/run')
BASE=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing')
V5=BASE/'datm_11_stage29_all77_rh_sensitivity_v5/CH-Aws_DATM_2007.nc'
V3=BASE/'datm_11_landrh25a_dynamic_zbot_v3/CH-Aws_DATM_2007.nc'
OUT=Path.home()/'FLUXNET_MultiSite_11/stage31_CH_Aws_RH29A_failure'
JOB='4508890'

def require(ok,why):
    if not ok:raise RuntimeError('STOP: '+why)

def sat_w(t):
    return 611.2*np.exp(np.clip(17.67*t/(t+243.5),-100,100))

def sat_ice(t):
    return 611.2*np.exp(np.clip(22.46*t/(t+272.62),-100,100))

def main():
    logs=list(RUN.glob(f'lnd.log.{JOB}.*'))
    require(logs,'Missing land log for job 4508890')
    log=max(logs,key=lambda x:x.stat().st_mtime)
    txt=log.read_text(errors='replace')
    hits=re.findall(r'at nstep\s*=\s*(\d+)',txt)
    require(hits,'No nstep markers in land log')
    step=int(hits[-1])
    inferred=datetime(2006,1,1)+timedelta(days=step/48)
    print('=== FAILURE CONTEXT ===')
    print('Land log:',log)
    print('Logged final history nstep:',step)
    print('Inferred corresponding simulation time (NOT exact abort):',inferred)
    fails=re.findall(r'rh\s*=\s*(-?\d+(?:\.\d+)?(?:[EeDd][+-]?\d+)?)',txt)
    print('Last model RH warning:',fails[-1] if fails else 'not present')
    print('Negative RH abort confirmed:', 'ERROR RH is negative' in txt)
    require(V5.is_file() and V3.is_file(),'2007 forcing missing or broken annual symlink')

    with Dataset(V5) as nc, Dataset(V3) as old:
        t=nc['time']
        all_times=pd.DatetimeIndex([
            str(x)[:19] for x in num2date(t[:],t.units,calendar=getattr(t,'calendar','noleap'))])
        require(len(all_times)==17520 and all_times.is_unique,
                'Unexpected 2007 half-hour forcing timeline')
        names=('TBOT','PSRF','QBOT','WIND','FSDS','FLDS','ZBOT','PRECTmms')
        for name in names:
            require(name in nc.variables,f'Missing v5 variable {name}')
        allv={name:np.asarray(nc[name][:,0,0],dtype=float) for name in names}
        old_q=np.asarray(old['QBOT'][:,0,0],dtype=np.float32)
        new_q=np.asarray(nc['QBOT'][:,0,0],dtype=np.float32)

    q=allv['QBOT'];p=allv['PSRF'];t_c=allv['TBOT']-273.15
    ea=q*p/(0.622+0.378*q)
    rh_w=ea/sat_w(t_c)*100
    rh_ice=ea/sat_ice(t_c)*100
    data=pd.DataFrame({
        'time':all_times,'TBOT_C':t_c,'PSRF_Pa':p,
        'QBOT_kgkg':q,'input_RH_water_pct':rh_w,
        'input_RH_ice_pct':rh_ice,
        'WIND_ms':allv['WIND'],'ZBOT_m':allv['ZBOT'],
        'FSDS_Wm2':allv['FSDS'],'FLDS_Wm2':allv['FLDS'],
        'PRECTmms':allv['PRECTmms'],
        'Stage29_changed_vs_v3':new_q!=old_q
    })
    require(np.isfinite(rh_w).all() and np.isfinite(q).all(),
            '2007 humidity contains nonfinite values')
    lo=pd.Timestamp(inferred)-pd.Timedelta(days=3)
    hi=pd.Timestamp(inferred)+pd.Timedelta(days=2)
    window=data[(data.time>=lo)&(data.time<=hi)].copy()
    require(not window.empty,'No forcing records near inferred abort date')
    print('\n=== 2007 ANNUAL FORCING ===')
    print('Minimum QBOT:',float(q.min()),'kg/kg')
    print('Minimum atmospheric input RH (water):',float(rh_w.min()),'%')
    print('Modified vs RH25A v3 in full 2007:',int((new_q!=old_q).sum()))
    altered=data.loc[data.Stage29_changed_vs_v3,'time']
    print('2007 altered forcing timestamps:',list(map(str,altered)))
    print('\n=== WINDOW near inferred abort ===')
    print('Window start/end:',window.time.min(),window.time.max())
    print('Input RH water min/max:',float(window.input_RH_water_pct.min()),
          float(window.input_RH_water_pct.max()))
    print('Input RH ice min/max:',float(window.input_RH_ice_pct.min()),
          float(window.input_RH_ice_pct.max()))
    print('QBOT min/max:',float(window.QBOT_kgkg.min()),float(window.QBOT_kgkg.max()))
    print('TBOT C min/max:',float(window.TBOT_C.min()),float(window.TBOT_C.max()))
    print('ZBOT min/max:',float(window.ZBOT_m.min()),float(window.ZBOT_m.max()))
    print('Stage29 modifications within window:',int(window.Stage29_changed_vs_v3.sum()))
    print('\n25 driest atmospheric INPUT records within window (not 2-m diagnosed RH):')
    cols=['time','TBOT_C','QBOT_kgkg','input_RH_water_pct','input_RH_ice_pct',
          'WIND_ms','ZBOT_m','Stage29_changed_vs_v3']
    print(window.nsmallest(25,'input_RH_water_pct')[cols].to_string(index=False,
                                                               float_format=lambda v:f'{v:.6g}'))

    # Print up to the last few hourly forcing records before inferred history boundary;
    # history writes may precede the true abort clock.
    last=window[(window.time>=pd.Timestamp(inferred)-pd.Timedelta(hours=6))
                &(window.time<=pd.Timestamp(inferred)+pd.Timedelta(hours=3))]
    print('\n=== FORCING ±6h/3h around inferred history boundary ===')
    print(last[cols].to_string(index=False,float_format=lambda v:f'{v:.6g}'))

    # Optional verify if h0a file already exists but is unflushed/empty:
    hist=list(RUN.glob('*.clm2.h0a.2007*.nc'))
    print('\n=== 2007 h0a history availability ===')
    for f in sorted(hist):
        try:
            with Dataset(f) as h:
                print(f.name,'time records:',len(h.dimensions['time']))
        except Exception as exc:
            print(f.name,'unreadable:',str(exc)[:100])
    OUT.mkdir(parents=True,exist_ok=True)
    dst=OUT/'01_2007_forcing_near_failure_readonly.csv'
    window.to_csv(dst,index=False,float_format='%.12g')
    print('\nSaved small read-only diagnostic table:',dst)
    print('NO model restart or CIME changes; NO Slurm jobs submitted.')
    print('Scientific caveat: forcing RH != prognostic/diagnostic q_ref2m RH.')

if __name__=='__main__':
    main()

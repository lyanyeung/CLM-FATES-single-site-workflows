#!/usr/bin/env python3
"""Read-only diagnosis of repeat negative *model 2-m* RH in CH-Aws RH21A.

Reads existing run logs, 2006 DATM v1/v2, Stage21 candidate CSV and, if present,
Stage09 cached ERA5/ERA5-Land hourly references. Never changes input, case or job.
"""
from __future__ import annotations
import json, re
from pathlib import Path
import numpy as np
import pandas as pd
from netCDF4 import Dataset

HOME=Path.home()
CASE='CH-Aws_FATES_SPINUP1000_RH21A'
RUN=Path('/scratch/ly3n24/CTSM_FATES_OUTPUTS')/CASE/'run'
ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing')
F2006='CH-Aws_DATM_2006.nc'
V1=ROOT/'datm_11_provisional_dynamic_zbot_v1'/F2006
V2=ROOT/'datm_11_landrh21a_dynamic_zbot_v2'/F2006
CAND=ROOT/'merged_multisource_11_landrh21a'/'CH-Aws_multisource_HH_2006_2024_candidate.csv'
CACHE=HOME/'FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo'

def log_latest(prefix):
    return max(RUN.glob(prefix+'.log.*'), key=lambda p:p.stat().st_mtime,default=None)

def sat(t):
    return 6.112*np.exp(np.clip(17.67*np.asarray(t,dtype=float)/(np.asarray(t,dtype=float)+243.5),-100.,100.))

def derived_rh(tk,q,p):
    # Diagnostic water-saturation convention used by Stage15/22; not CLM's computed 2-m RH.
    t=np.asarray(tk,dtype=float)-273.15
    vp=(np.asarray(q,dtype=float)*np.asarray(p,dtype=float))/(0.622+0.378*np.asarray(q,dtype=float))/100.
    return 100.*vp/sat(t)

def reference(model,times):
    p=CACHE/f'{model}_2006.json'
    if not p.is_file():return np.full(len(times),np.nan)
    obj=json.loads(p.read_text());h=obj['hourly']
    idx=pd.DatetimeIndex(pd.to_datetime(h['time']))+pd.Timedelta(hours=1)
    d=pd.DataFrame({'T':pd.to_numeric(h['temperature_2m'],errors='coerce'),
                    'Td':pd.to_numeric(h['dew_point_2m'],errors='coerce')},index=idx)
    if d.index.has_duplicates:raise ValueError('Duplicate reference times: '+str(p))
    expanded=d.reindex(d.index.union(times)).sort_index().interpolate(method='time',limit=1,limit_area='inside').reindex(times)
    return 100.*sat(expanded['Td'])/sat(expanded['T'])

def read_log():
    print('=== MODEL ERROR AND CLOCK ===')
    print('Run directory:',RUN)
    lnd=log_latest('lnd');atm=log_latest('atm')
    if lnd is not None:
        txt=lnd.read_text(errors='replace')
        print('Last LND log:',lnd.name)
        rh=re.findall(r'(?im)^\s*rh\s*=\s*([-+0-9.eEdD]+)',txt)
        if rh:print('Negative model-diagnosed 2m RH (%):',rh[-1])
        last_nstep=re.findall(r'(?s)nstep\s*=\s*(\d+)',txt)
        if last_nstep:print('Last written history timestep:',last_nstep[-1], '(not necessarily failure timestep)')
        if 'ERROR RH is negative' not in txt:print('NOTE: Latest LND log does not have the expected RH error')
    else:print('No LND log found')
    if atm is not None:
        txt=atm.read_text(errors='replace')
        print('Last ATM log:',atm.name)
        datetimes=[]
        for y,sec in re.findall(r'(?m)atm\s*:\s*model date\s+(\d{8})\s+(\d+)',txt):
            try:datetimes.append(pd.Timestamp(y)+pd.Timedelta(seconds=int(sec)))
            except ValueError:pass
        if datetimes:
            print('Final 8 ATM model dates (may be slightly ahead of land model):')
            for x in datetimes[-8:]:print(' ',x)
            return datetimes[-1]
        print('No parseable atm model dates')
    else:print('No ATM log found')
    return None

def main():
    for path in [V1,V2,CAND]:
        if not path.is_file():raise FileNotFoundError(path)
    when=read_log()
    if when is None:when=pd.Timestamp('2006-01-12 00:00:00')
    with Dataset(V1) as f,Dataset(V2) as g:
        values={}
        for key in ('TBOT','QBOT','PSRF','ZBOT'):
            values[key]=np.asarray(g[key][:,0,0],dtype=float)
        qold=np.asarray(f['QBOT'][:,0,0],dtype=float)
        for key in ('TBOT','PSRF','ZBOT'):
            if not np.array_equal(np.asarray(f[key][:,0,0]),np.asarray(g[key][:,0,0])):
                raise RuntimeError('Unexpected v1/v2 change: '+key)
        print('\nStage22 provenance:',getattr(g,'source_candidate_tag','not reported'))
        print('v2 ZBOT min/max (m):',values['ZBOT'].min(),values['ZBOT'].max())
    tt=pd.date_range('2006-01-01','2006-12-31 23:30:00',freq='30min')
    if len(tt)!=17520:raise AssertionError('Unexpected 2006 timestep count')
    df=pd.DataFrame(values,index=tt)
    df['QBOT_v1']=qold
    df['RH_v2_input_pct']=derived_rh(df.TBOT,df.QBOT,df.PSRF)
    df['RH_v1_input_pct']=derived_rh(df.TBOT,df.QBOT_v1,df.PSRF)
    df['QBOT_delta']=df.QBOT-df.QBOT_v1
    print('\n=== 2006 FULL-YEAR FORCING SUMMARY ===')
    print('QBOT changed v1 -> v2:',int(np.count_nonzero(df.QBOT_delta)))
    print('RH_v2 forcing min/max (%):',df.RH_v2_input_pct.min(),df.RH_v2_input_pct.max())
    for threshold in (1,5,10,20):
        print(f'RH_v2 input < {threshold}%:',int((df.RH_v2_input_pct<threshold).sum()))
    print('Lowest RH_v2 forcing rows:')
    print(df.nsmallest(12,'RH_v2_input_pct')[['TBOT','PSRF','QBOT','RH_v2_input_pct','QBOT_v1','RH_v1_input_pct','ZBOT']].to_string(float_format=lambda x:f'{x:.7g}'))
    names=['time','TA_F','PA_F','VPD_F','VPD_F_SOURCE','VPD_F_QC',
           'STAGE21_RH_TRIAL_FLAG','RH_LAND_TRIAL_FLAG']
    candidate=pd.read_csv(CAND,usecols=lambda k:k in names,low_memory=False)
    candidate['time']=pd.to_datetime(candidate.time)
    candidate=candidate.loc[candidate.time.dt.year==2006].set_index('time')
    if not candidate.index.equals(df.index):raise RuntimeError('2006 CSV timestamps not identical to DATM timestamps')
    for flag in ('STAGE21_RH_TRIAL_FLAG','RH_LAND_TRIAL_FLAG'):
        if flag in candidate:candidate[flag]=candidate[flag].astype('boolean').fillna(False)
    df=df.join(candidate[['VPD_F','VPD_F_SOURCE','VPD_F_QC','STAGE21_RH_TRIAL_FLAG','RH_LAND_TRIAL_FLAG']],how='left')
    start=when-pd.Timedelta(hours=18)
    stop=when+pd.Timedelta(hours=12)
    win=df.loc[start:stop].copy()
    print('\n=== WINDOW AROUND LATEST ATM CLOCK (18h before, 12h after) ===')
    print('Clock:',when,'; selection:',start,'to',stop)
    win['ERA5_RH']=reference('era5',win.index)
    win['ERA5Land_RH']=reference('era5_land',win.index)
    cols=['TBOT','QBOT','RH_v2_input_pct','RH_v1_input_pct','ZBOT',
          'VPD_F_QC','VPD_F_SOURCE','STAGE21_RH_TRIAL_FLAG','ERA5_RH','ERA5Land_RH']
    print(win[cols].to_string(float_format=lambda x:f'{x:.5g}',max_rows=90))
    if len(win):
        print('\nWindow RH_v2 min:',win.RH_v2_input_pct.min())
        print('Window Stage21 edited rows:',int(win.STAGE21_RH_TRIAL_FLAG.sum()))
        print('Window RH_v2 < 10%:',int((win.RH_v2_input_pct<10).sum()))
        print('Window 2-hour max RH jump (pp):',float(win.RH_v2_input_pct.diff(4).abs().max()))
    print('\n=== OPTIONAL MODEL HISTORY VARIABLES ===')
    recent_hist=max(RUN.glob('*.clm2.h0i.*.nc'),key=lambda p:p.stat().st_mtime,default=None)
    if recent_hist:
        with Dataset(recent_hist) as f:
            relevant=[k for k in f.variables if re.search(r'QREF|Q2M|RH2M|RHREF|TREF|T2M|QSOIL|QVEG|QFLX',k,re.I)]
            print('Recent history:',recent_hist.name,'; selected variable names:',relevant[:35])
    print('\nThis compares forcing RH only. Negative CLM 2m RH comes from an internal surface-layer diagnostic and cannot be attributed to a single forcing value from this report alone.')
    print('READ-ONLY: no case, NetCDF, source CSV, Slurm job or executable modified.')

if __name__=='__main__':main()

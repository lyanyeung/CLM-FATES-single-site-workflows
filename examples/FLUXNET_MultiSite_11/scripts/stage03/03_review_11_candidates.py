#!/usr/bin/env python3
"""Read-only secondary scientific screening of new 11-site candidate meteorology.

Does NOT change values, re-label QC as PASS, convert to DATM, or submit any job.
Thresholds here are *review triggers*, not proof a measured extreme is erroneous.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
SITES={'BE-Bra':(1996,2025),'FR-Fon':(2005,2025),'GL-ZaH':(2000,2025),
       'IT-Noe':(2004,2025),'AT-Neu':(2002,2020),'FI-Sod':(2001,2025),
       'CH-Aws':(2006,2024),'CH-Cha':(2005,2024),'CH-Fru':(2005,2024),
       'CH-Lae':(2004,2024),'CZ-Stn':(2010,2024)}
VARS=['TA','VPD','PA','SW_IN','LW_IN','WS','P']
REVIEW={'TA':(-55,52),'VPD':(-0.01,100),'PA':(50,110),
        'SW_IN':(-1,1400),'LW_IN':(100,700),'WS':(-0.01,45),'P':(-0.001,40)}

def one(site,src):
    first,last=SITES[site]
    cols=['time','PAIR_STATUS','RH_IMPLIED_PCT','QBOT_DIAGNOSTIC_KG_KG'] + \
          [v+'_F' for v in VARS]+[v+'_F_SOURCE' for v in VARS]
    h=set(pd.read_csv(src,nrows=0).columns)
    absent=set(cols)-h
    if absent:raise ValueError('Missing columns: '+repr(sorted(absent)))
    d=pd.read_csv(src,usecols=cols,dtype={'time':'string'},low_memory=False)
    t=pd.to_datetime(d.time,errors='raise')
    expected=pd.date_range(f'{first}-01-01',f'{last}-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(d)!=len(expected) or not np.array_equal(t.to_numpy(dtype='datetime64[ns]'), expected.to_numpy()):
        raise ValueError('Time axis does not match full ordered NO_LEAP study period')
    records=[];counts=[]
    for yr in range(first,last+1):
        ix=np.flatnonzero(t.dt.year.to_numpy()==yr)
        z=d.iloc[ix].reset_index(drop=True)
        dt=pd.DatetimeIndex(t.iloc[ix])
        flags={}
        def flag(name,mask):
            mask=np.asarray(mask,dtype=bool)
            count=int(mask.sum());flags[name]=count
            if count:
                for i in np.flatnonzero(mask)[:15]:
                    records.append({'site':site,'year':yr,'time':str(dt[i]),'flag':name,
                                    'TA_C':z.TA_F.iloc[i],'VPD_hPa':z.VPD_F.iloc[i],
                                    'PA_kPa':z.PA_F.iloc[i],'RH_pct':z.RH_IMPLIED_PCT.iloc[i],
                                    'TA_source':z.TA_F_SOURCE.iloc[i], 'P_source':z.P_F_SOURCE.iloc[i]})
        flag('invalid_humidity_pair',z.PAIR_STATUS!='VALID_PAIR')
        rh=z.RH_IMPLIED_PCT
        flag('very_low_RH_below_1pct',rh.notna()&(rh>0)&(rh<1))
        for v,(lo,hi) in REVIEW.items():
            x=pd.to_numeric(z[v+'_F'],errors='coerce')
            flag(v+'_outside_review_range',x.notna()&~x.between(lo,hi))
        for v,threshold in [('TA',15.),('VPD',20.),('PA',2.),('LW_IN',150.)]:
            x=pd.to_numeric(z[v+'_F'],errors='coerce')
            # Annual chunks never interpolate or count jumps over the year boundary.
            jump=x.diff().abs()>threshold
            flag(v+'_30min_large_jump',jump)
        source=z.TA_F_SOURCE.astype('string').fillna('')
        switch=(source!=source.shift(1)).fillna(False)
        if len(switch):switch.iloc[0]=False
        flag('TA_VPD_PA_source_switch',switch)
        precip=float(np.nansum(pd.to_numeric(z.P_F,errors='coerce')))
        rec={'site':site,'year':yr,'precip_mm_year':round(precip,2),
             'station_humidity_pair_pct':round(100*source.str.contains('_F$',regex=True).mean(),2),
             'reanalysis_humidity_pair_pct':round(100*source.str.contains('ERA',regex=False).mean(),2),
             'annual_precip_over_2500mm_review_only':precip>2500}
        rec.update(flags); counts.append(rec)
    return counts,records

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tag',default='v1')
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--out',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage03_candidate_scientific_review')
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    yearly=[];events=[];failures=[]
    for site,(first,last) in SITES.items():
        p=a.root/site/'forcing'/f'merged_multisource_11_{a.tag}'/f'{site}_multisource_HH_{first}_{last}_candidate.csv'
        if not p.exists():
            failures.append({'site':site,'problem':'candidate missing','path':str(p)})
            print(site,'MISSING CANDIDATE');continue
        try:
            rows,samples=one(site,p)
            yearly.extend(rows);events.extend(samples)
            print(site,'DONE:',len(rows),'years,',len(samples),'sampled review events')
        except Exception as exc:
            failures.append({'site':site,'problem':str(exc),'path':str(p)})
            print(site,'ERROR:',exc)
    pd.DataFrame(yearly).to_csv(a.out/'annual_review_flags.csv',index=False)
    pd.DataFrame(events,columns=['site','year','time','flag','TA_C','VPD_hPa','PA_kPa','RH_pct','TA_source','P_source']).to_csv(a.out/'review_examples.csv',index=False)
    pd.DataFrame(failures,columns=['site','problem','path']).to_csv(a.out/'errors.csv',index=False)
    if yearly:
        d=pd.DataFrame(yearly)
        g=d.groupby('site').agg({'invalid_humidity_pair':'sum','TA_30min_large_jump':'sum','LW_IN_30min_large_jump':'sum','P_outside_review_range':'sum','TA_VPD_PA_source_switch':'sum','annual_precip_over_2500mm_review_only':'sum'})
        print('\n=== REVIEW FLAGS BY SITE ===\n'+g.to_string())
    print('\nReview report:',a.out,'\nNo files changed or approved for model.')
    if failures:raise SystemExit(2)

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Full-year read-only screening for suspect FLUXNET MDS meteorology in DE-Gri and FI-Let.

NO replacements are computed/applied. Generates candidate *review* windows with
local measured(QC0)-vs-ERA bias calibration, plus original QC provenance,
repeated MDS TA/VPD pairs and calendar year summary. The ERA companion is a
separate modeled reference (not independent tower ground truth).

Input: ~/FLUXNET_13_input_audit/site_input_summary.csv
Output: NEW ~/FLUXNET_13_stage16_fullsite_MDS_audit_20261014 (no overwrites).
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

DEFAULT_INPUT=Path.home()/"FLUXNET_13_input_audit/site_input_summary.csv"
DEFAULT_OUTPUT=Path.home()/"FLUXNET_13_stage16_fullsite_MDS_audit_20261014"
SITES=("DE-Gri","FI-Let")
REQUIRED=("TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC","VPD_ERA")
OPTIONAL=("TA_F_MDS","TA_F_MDS_QC","VPD_F_MDS","VPD_F_MDS_QC")

def sha256(p):
    dig=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): dig.update(chunk)
    return dig.hexdigest()

def read(site,m):
    rows=m.loc[m.site.eq(site)]
    if len(rows)!=1: raise ValueError(f'{site}: expected exactly one metadata row; got {len(rows)}')
    src=Path(str(rows.iloc[0].primary_file))
    if not src.is_file():raise FileNotFoundError(f'{site}: {src}')
    columns=set(pd.read_csv(src,nrows=0).columns)
    needed=set(REQUIRED)-columns
    if needed:raise RuntimeError(f'{site}: required raw FLUXMET columns missing: {needed}')
    use=list(REQUIRED)+[c for c in OPTIONAL if c in columns]
    df=pd.read_csv(src,usecols=use,dtype={'TIMESTAMP_START':str},low_memory=False)
    df['time']=pd.to_datetime(df['TIMESTAMP_START'].astype(str).str.replace(r'\.0$','',regex=True),format='%Y%m%d%H%M',errors='raise')
    df=df.drop(columns='TIMESTAMP_START').sort_values('time',kind='stable').reset_index(drop=True)
    if df.time.duplicated().any():raise RuntimeError(f'{site}: duplicate raw time indices')
    for c in df.columns:
        if c=='time':continue
        df[c]=pd.to_numeric(df[c],errors='coerce')
        df.loc[(df[c]<=-9990)|(~np.isfinite(df[c])),c]=np.nan
    first=int(rows.iloc[0].year_start)
    last=int(rows.iloc[0].year_end)
    df=df.loc[df.time.dt.year.between(first,last)].copy().reset_index(drop=True)
    if df.empty:raise RuntimeError(f'{site}: empty raw FLUXMET {first}-{last}')
    return df,src

def thermo(t,v):
    es=6.112*np.exp(17.67*t/(t+243.5))
    return 100*(es-v)/es

def analyze(site,df):
    delta=df.TA_F-df.TA_ERA
    era_ok=df.TA_ERA.between(-55,55)&df.VPD_ERA.ge(0)&df.VPD_ERA.le(thermo_inverse_es(df.TA_ERA)*0.99)
    measured=(df.TA_F_QC.eq(0)&df.TA_F.between(-55,55)&era_ok&delta.notna())
    is_MDS=df.TA_F_QC.eq(1)
    flag=(is_MDS&df.TA_F.between(-55,55)&era_ok&delta.abs().gt(8))
    breaks=flag.ne(flag.shift(fill_value=False)) | df.time.diff().ne(pd.Timedelta(minutes=30))
    group=breaks.cumsum()
    f=df.loc[flag,['time','TA_F','TA_F_QC','TA_ERA','VPD_F','VPD_F_QC','VPD_ERA']].copy()
    f['block']=group.loc[flag].to_numpy()
    f['delta_TA_minus_ERA_C']=delta.loc[flag].to_numpy()
    if 'TA_F_MDS_QC' in df:f['TA_F_MDS_QC']=df.loc[flag,'TA_F_MDS_QC'].to_numpy()
    if 'VPD_F_MDS_QC' in df:f['VPD_F_MDS_QC']=df.loc[flag,'VPD_F_MDS_QC'].to_numpy()
    if len(f):
        f['RH_MDS_pct']=thermo(f.TA_F,f.VPD_F)
        f['RH_ERA_pct']=thermo(f.TA_ERA,f.VPD_ERA)
    # A measured residual baseline is computed independently for EACH anomalous block,
    # from all available nearby (±30d) QC0 observations. Not used to edit values.
    observed_time=df.loc[measured,'time'].to_numpy(dtype='datetime64[ns]')
    observed_delta=delta.loc[measured].to_numpy(dtype=float)
    block_rows=[]
    for block,sub in f.groupby('block',sort=False):
        start,end=sub.time.iloc[0],sub.time.iloc[-1]
        midpoint=start+(end-start)/2
        lo=np.searchsorted(observed_time,np.datetime64(midpoint-pd.Timedelta(days=30)),side='left')
        hi=np.searchsorted(observed_time,np.datetime64(midpoint+pd.Timedelta(days=30)),side='right')
        sample=observed_delta[lo:hi]
        local_n=len(sample)
        local_median=float(np.median(sample)) if local_n else np.nan
        local_q05=float(np.quantile(sample,.05)) if local_n else np.nan
        local_q95=float(np.quantile(sample,.95)) if local_n else np.nan
        median_delta=float(sub.delta_TA_minus_ERA_C.median())
        max_difference=float(sub.delta_TA_minus_ERA_C.abs().max())
        # Strong separation from measured envelope is REVIEW priority, never auto deletion.
        separated=(local_n>=48 and
                   ((median_delta>local_q95+3.0) or (median_delta<local_q05-3.0)) and
                   abs(median_delta-local_median)>8.0)
        rh_flag=int((~sub.RH_ERA_pct.between(1,100)).sum()) if len(sub) else 0
        mds_rh_bad=int((~sub.RH_MDS_pct.between(0,100.05)).sum()) if len(sub) else 0
        block_rows.append({'site':site,'start':start,'end':end,'half_hours':len(sub),
             'span_hours':len(sub)*0.5,
             'median_delta_MDS_minus_ERA_C':round(median_delta,3),
             'max_abs_delta_C':round(max_difference,3),
             'mean_MDS_TA_C':round(float(sub.TA_F.mean()),3),
             'mean_ERA_TA_C':round(float(sub.TA_ERA.mean()),3),
             'nearby_measured_QC0_n_60d':local_n,
             'nearby_QC0_median_TA_minus_ERA_C':round(local_median,3),
             'nearby_QC0_p05_C':round(local_q05,3),
             'nearby_QC0_p95_C':round(local_q95,3),
             'ERA_RH_below1_or_above100_count':rh_flag,
             'MDS_RH_outside0_100_count':mds_rh_bad,
             'separated_from_nearby_measured':bool(separated),
             'review_priority':('HIGH_SUSPECT_MDS' if separated and len(sub)>=2 and rh_flag==0
                                else 'INVESTIGATE_NO_AUTO_CHANGE'),
             'scientific_decision':'PENDING', 'proposed_replacement':'NONE'})
    blocks=pd.DataFrame(block_rows)
    if blocks.empty:
        blocks=pd.DataFrame(columns=['site','start','end','half_hours','review_priority','scientific_decision'])
    # All QC1 paired TA/VPD values are rounded in the product; recurrent exact pairs
    # across days may be artifacts of donor recycling, but this is not definitive.
    q=df.loc[is_MDS & df.TA_F.notna() & df.VPD_F.notna(),['time','TA_F','VPD_F']].copy()
    if len(q):
        q['day']=q.time.dt.strftime('%Y-%m-%d')
        pairs=q.groupby(['TA_F','VPD_F'],dropna=False).agg(n=('time','size'),distinct_days=('day','nunique'),first=('time','min'),last=('time','max')).reset_index()
        pairs=pairs.loc[(pairs.n>=4)&(pairs.distinct_days>=2)].copy().sort_values(['n','distinct_days'],ascending=False)
    else:
        pairs=pd.DataFrame(columns=['TA_F','VPD_F','n','distinct_days','first','last'])
    pairs.insert(0,'site',site)
    years=[]
    for yr,sub in df.groupby(df.time.dt.year,sort=True):
        selection=df.time.dt.year.eq(yr)
        yr_blocks=blocks.loc[blocks.start.dt.year.eq(yr)] if len(blocks) else blocks
        years.append({'site':site,'year':int(yr),'rows':len(sub),
          'TA_QC0':int(sub.TA_F_QC.eq(0).sum()),'TA_QC1':int(sub.TA_F_QC.eq(1).sum()),
          'TA_QC2':int(sub.TA_F_QC.eq(2).sum()),
          'QC1_with_abs_TA_minus_ERA_gt8':int((flag & selection).sum()),
          'QC1_flag_percent':round(100*int((flag & selection).sum())/max(1,int((is_MDS & selection).sum())),2),
          'high_suspect_blocks_started_this_year':int(yr_blocks.review_priority.eq('HIGH_SUSPECT_MDS').sum())
        })
    print(f'\n=== {site} WHOLE-SITE SCREEN ===')
    print(f'QC0 measured={int(measured.sum()):,}; QC1={int(is_MDS.sum()):,}; '
          f'QC1 |TA_F-TA_ERA|>8C={int(flag.sum()):,}; contiguous flagged blocks={len(blocks):,}; '
          f'high-priority blocks={int(blocks.review_priority.eq("HIGH_SUSPECT_MDS").sum())}')
    if len(blocks):
        ranking=blocks.sort_values(['half_hours','max_abs_delta_C'],ascending=False).head(20)
        print(ranking[['start','end','half_hours','median_delta_MDS_minus_ERA_C',
                       'nearby_QC0_median_TA_minus_ERA_C','nearby_measured_QC0_n_60d',
                       'review_priority']].to_string(index=False))
    if len(pairs):
        print('\nMOST REPEATED QC1 EXACT TA/VPD PAIRS:')
        print(pairs.head(8).to_string(index=False))
    f.insert(0,'site',site)
    return f,blocks,pairs,pd.DataFrame(years)

def thermo_inverse_es(t):
    return 6.112*np.exp(17.67*t/(t+243.5))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=DEFAULT_INPUT)
    ap.add_argument('--out',type=Path,default=DEFAULT_OUTPUT)
    args=ap.parse_args()
    if args.out.exists():raise FileExistsError(f'Output directory exists; no overwrite: {args.out}')
    if not args.manifest.is_file():raise FileNotFoundError(args.manifest)
    manifest=pd.read_csv(args.manifest)
    if not {'site','primary_file','year_start','year_end'}.issubset(manifest.columns):
        raise RuntimeError('Input manifest lacks metadata columns')
    payload={}; provenance={}
    for site in SITES:
        df,p=read(site,manifest)
        payload[site]=analyze(site,df)
        provenance[site]={'raw_path':str(p),'sha256':sha256(p),'n_rows':len(df)}
    args.out.mkdir(parents=True,exist_ok=False)
    parts=['flagged_QC1_records.csv','all_suspect_QC1_blocks_DECISIONS_PENDING.csv',
           'repeated_MDS_TA_VPD_pairs.csv','fullsite_QC1_summary_by_year.csv']
    for index,name in enumerate(parts):
        data=pd.concat([payload[s][index] for s in SITES],ignore_index=True)
        data.to_csv(args.out/name,index=False)
    (args.out/'raw_input_manifest_SHA256.json').write_text(json.dumps(provenance,indent=2))
    (args.out/'README.txt').write_text(
      'READ ONLY. This is evidence for manual decision; no FLUXNET, MDS, '
      'ERA or CLM-FATES forcing modified.\n'
      'MDS bias vs station-downscaled ERA is not proof of wrong values.\n'
      'A high-priority flag requires multiple consecutive QC1 records, '
      'reference thermodynamic sanity and disagreement with nearby QC0 bias distribution.\n'
      'SCIENTIFIC_DECISION remains PENDING for every candidate block.\n'
      'Manual source validation required before any paired TA/VPD replacements.\n')
    print(f'\nAUDIT COMPLETE: all years DE-Gri and FI-Let; {args.out}')
    print('NO FORCING MODIFIED; ALL SCIENTIFIC DECISIONS PENDING')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'FATAL {type(exc).__name__}: {exc}',file=sys.stderr)
        sys.exit(1)
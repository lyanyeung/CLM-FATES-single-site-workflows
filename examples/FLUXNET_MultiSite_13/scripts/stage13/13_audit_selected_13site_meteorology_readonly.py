#!/usr/bin/env python3
"""Read-only comprehensive meteorological screen, 13 selected candidate forcings.

Run before BIF/ZBOT and DATM. Uses Stage12 for ES-Agu, ES-LJu, DE-Lnf,
otherwise Stage03 QC-v5. Writes audit CSVs only into a NEW report directory.
All thresholds are diagnostic screens, not automatic replacement instructions.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd

EX=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments')
V5=EX/'FLUXNET_MultiSite_13_qc_v5_candidate_20261014'
V12=EX/'FLUXNET_MultiSite_13_targeted_TA_PA_trial_v1_20261014'
MANIFEST=Path.home()/'FLUXNET_13_input_audit/site_input_summary.csv'
REPORT=Path.home()/'FLUXNET_13_meteorology_stage13_audit_20261014'
STAGE12_SITES={'ES-Agu','ES-LJu','DE-Lnf'}
METS=['TA_USE','VPD_USE','TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms']
EXTRA_SOURCE=['TA_F','TA_F_QC','VPD_F','VPD_F_QC','PA_F','PA_F_QC',
              'TA_ERA','PA_ERA','VPD_ERA','LW_IN_F','LW_IN_F_QC',
              'SW_IN_F','SW_IN_F_QC','WS_F','WS_F_QC','P_F','P_F_QC']

# These are manually selected points for context, NOT approved change targets.
KNOWN={
 'DE-Lnf':['2023-06-22 06:30','2023-06-22 07:30'],
 'ES-Agu':['2011-12-16 23:00','2014-06-26 14:30','2014-06-26 15:00',
           '2016-10-10 02:00'],
 'ES-LJu':['2015-09-13 14:30','2023-10-28 08:00'],
 'DE-Gri':['2011-06-13 06:30','2011-06-13 07:00','2011-06-14 05:30',
           '2011-06-14 06:00'],
 'FI-Let':['2019-02-22 07:30','2021-01-15 06:00']
}

def es_hpa(t):
    return 6.112*np.exp(17.67*t/(t+243.5))

def timestamps(s):
    return pd.to_datetime(s.astype(str).str.strip().str.replace(r'\.0$','',regex=True),
                          format='%Y%m%d%H%M',errors='raise')

def source_data(record,first,last):
    src=Path(record['primary_file'])
    companion=Path(record['companion_file'])
    if not src.is_file() or not companion.is_file():
        raise FileNotFoundError(f'Raw source missing: {src} or {companion}')
    h=set(pd.read_csv(src,nrows=0).columns)
    cols=['TIMESTAMP_START']+[x for x in EXTRA_SOURCE if x in h]
    s=pd.read_csv(src,usecols=cols,dtype={'TIMESTAMP_START':str},low_memory=False)
    s['time']=timestamps(s.TIMESTAMP_START)
    s=s.drop(columns='TIMESTAMP_START')
    missing=[x for x in ('TA_ERA','PA_ERA','VPD_ERA') if x not in s]
    if missing:
        eh=set(pd.read_csv(companion,nrows=0).columns)
        available=[x for x in missing if x in eh]
        if available:
            ec=pd.read_csv(companion,usecols=['TIMESTAMP_START',*available],
                           dtype={'TIMESTAMP_START':str})
            ec['time']=timestamps(ec.TIMESTAMP_START)
            if ec.time.duplicated().any(): raise ValueError('Companion ERA duplicate timestamps')
            s=s.merge(ec.drop(columns='TIMESTAMP_START'),on='time',how='left',validate='one_to_one')
    s=s.loc[s.time.dt.year.between(first,last)]
    s=s.loc[~((s.time.dt.month==2)&(s.time.dt.day==29))]
    s=s.sort_values('time').reset_index(drop=True)
    if s.time.duplicated().any(): raise ValueError('Primary raw duplicate timestamps')
    for col in EXTRA_SOURCE:
        if col not in s: s[col]=np.nan
        s[col]=pd.to_numeric(s[col],errors='coerce')
        s.loc[s[col]<=-9990,col]=np.nan
    return s

def selected_path(site,first,last,v5,v12):
    if site in STAGE12_SITES:
        return v12/f'{site}_CLM_forcing_{first}_{last}_targeted_trial.csv','Stage12'
    return v5/site/'forcing/processed_v5'/f'{site}_CLM_forcing_{first}_{last}.csv','QC_v5'

def finite_and_range(d, field, lo, hi):
    x=d[field]
    return ~np.isfinite(x) | ~x.between(lo,hi)

def build_site(site,rec,v5,v12):
    first,last=int(rec['year_start']),int(rec['year_end'])
    fpath,version=selected_path(site,first,last,v5,v12)
    if not fpath.is_file(): raise FileNotFoundError(f'Candidate missing: {fpath}')
    h=set(pd.read_csv(fpath,nrows=0).columns)
    missing=set(METS+['time'])-h
    if missing: raise RuntimeError(f'Candidate missing columns {missing}: {fpath}')
    d=pd.read_csv(fpath,usecols=['time',*METS],low_memory=False)
    d['time']=pd.to_datetime(d.time,errors='raise')
    for c in METS: d[c]=pd.to_numeric(d[c],errors='coerce')
    s=source_data(rec,first,last)
    expected=pd.date_range(f'{first}-01-01',f'{last}-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if not (len(d)==len(s)==len(expected) and
            np.array_equal(d.time.to_numpy(),expected.to_numpy()) and
            np.array_equal(s.time.to_numpy(),expected.to_numpy())):
        raise ValueError(f'NO_LEAP raw/candidate alignment failed: candidate {len(d)}, raw {len(s)}, expected {len(expected)}')
    n=len(d)
    t=d.TA_USE; v=d.VPD_USE; ps=d.PSRF
    ea=es_hpa(t)-v
    rh=100*ea/es_hpa(t)
    q_calc=.622*(ea*100)/(ps-.378*(ea*100))
    qbad=~np.isclose(d.QBOT.to_numpy(),q_calc.to_numpy(),atol=1e-9,rtol=1e-5,equal_nan=False)
    tbad=~np.isclose(d.TBOT.to_numpy(),(t+273.15).to_numpy(),atol=1e-5,rtol=0,equal_nan=False)
    step=d.time.diff().eq(pd.Timedelta(minutes=30))
    tdelta=t.diff().abs().where(step)
    pdelta=ps.diff().abs().where(step)
    lwdelta=d.FLDS.diff().abs().where(step)
    # A 25-half-hour (12.5h) *local median* is intentionally short enough
    # to catch 1.5h 2016 ES-Agu pressure faults; long faulty plateaus also
    # flagged by jumps at boundaries. No automatic local-median corrections.
    localp=ps.rolling(25,center=True,min_periods=8).median()
    local_t=t.rolling(25,center=True,min_periods=8).median()
    qccross=s.TA_F_QC.ne(s.TA_F_QC.shift(1)) & s.TA_F_QC.notna() & s.TA_F_QC.shift(1).notna() & step
    ref_ok=s.TA_ERA.between(-75,60) & s.PA_ERA.between(50,112)
    refbad=(s.TA_ERA.notna() & ~s.TA_ERA.between(-75,60)) | (s.PA_ERA.notna() & ~s.PA_ERA.between(50,112))
    flag={
      'PRESSURE_STEP_GT_3000_PA':pdelta>3000,
      'PRESSURE_LOCAL_GT_5000_PA':(ps-localp).abs()>5000,
      'PRESSURE_RAW_ERA_REF_INVALID':refbad,
      'TA_STEP_GT_12C':tdelta>12,
      'TA_LOCAL_GT_12C':(t-local_t).abs()>12,
      'TA_ERA_DIFF_GT_20C_REF_VALID':(t-s.TA_ERA).abs().gt(20) & ref_ok,
      'TA_QC_SOURCE_SWITCH_STEP_GT_8C':qccross & tdelta.gt(8),
      'VPD_RH_OUTSIDE_0_100':~np.isfinite(rh) | rh.lt(0) | rh.gt(100.05) | v.lt(0),
      'VPD_RH_LT_1PCT':rh.ge(0)&rh.lt(1),
      'TBOT_TA_CLOSURE_FAIL':pd.Series(tbad,index=d.index),
      'QBOT_HUMIDITY_CLOSURE_FAIL':pd.Series(qbad,index=d.index),
      'LW_JUMP_GT_140_WM2':lwdelta>140,
      'LW_BELOW_100_WM2':d.FLDS.lt(100),
      'SW_ABOVE_1400_OR_BELOW_MINUS1':d.FSDS.gt(1400)|d.FSDS.lt(-1),
      'WIND_ABOVE_40MS':d.WIND.gt(40),
      'PRECIP_ABOVE_18MM_PER_30MIN':d.PRECTmms.gt(0.01),
      'ANY_FORCING_NONFINITE':~np.isfinite(d[METS]).all(axis=1),
    }
    categories=[]
    for label, m in flag.items():
        ix=np.flatnonzero(m.fillna(False).to_numpy())
        for i in ix:
            categories.append((site,label,int(i)))
    # The precise candidate values are audited, but source/ERA-only issues
    # are not to be mistaken for errors in the selected forcing.
    summary={'site':site,'version':version,'first_year':first,'last_year':last,
             'records':n,'TA_min_C':float(t.min()),'TA_max_C':float(t.max()),
             'PSRF_min_Pa':float(ps.min()),'PSRF_max_Pa':float(ps.max()),
             'RH_min_pct':float(rh.min()),'RH_max_pct':float(rh.max()),
             'source_file':str(fpath),
             **{label:int(m.fillna(False).sum()) for label,m in flag.items()}}
    # Score urgency separate from warning counts.
    urgent=['PRESSURE_STEP_GT_3000_PA','PRESSURE_LOCAL_GT_5000_PA',
            'VPD_RH_OUTSIDE_0_100','TBOT_TA_CLOSURE_FAIL',
            'QBOT_HUMIDITY_CLOSURE_FAIL','ANY_FORCING_NONFINITE']
    summary['numeric_priority']='P0_REVIEW' if any(summary[x] for x in urgent) else 'SCREEN_OK_WITH_REVIEW_FLAGS'
    event=[]
    for sid,kind,i in categories:
        event.append({'site':sid,'flag':kind,'time':str(d.at[i,'time']),
                      'TA_C':float(t.iloc[i]),'raw_TA_C':float(s.TA_F.iloc[i]) if pd.notna(s.TA_F.iloc[i]) else np.nan,
                      'raw_TA_QC':s.TA_F_QC.iloc[i],
                      'TA_ERA_C':s.TA_ERA.iloc[i],
                      'TA_step_C':tdelta.iloc[i],
                      'PSRF_Pa':float(ps.iloc[i]),'raw_PA_kPa':s.PA_F.iloc[i],
                      'raw_PA_QC':s.PA_F_QC.iloc[i],
                      'PA_ERA_kPa':s.PA_ERA.iloc[i],
                      'PA_step_Pa':pdelta.iloc[i],
                      'pressure_vs_local_median_Pa':float((ps-localp).iloc[i]),
                      'VPD_hPa':float(v.iloc[i]),'raw_VPD_hPa':s.VPD_F.iloc[i],
                      'raw_VPD_QC':s.VPD_F_QC.iloc[i],
                      'RH_pct':float(rh.iloc[i]),
                      'QBOT':float(d.QBOT.iloc[i]),'FLDS':float(d.FLDS.iloc[i]),
                      'FSDS':float(d.FSDS.iloc[i]),'WIND':float(d.WIND.iloc[i]),
                      'PRECTmms':float(d.PRECTmms.iloc[i])})
    # Focused 2h context, preserving original source flags. Explicitly
    # add previous/next half-hours and reproduce selected repaired values.
    known=[]
    for center in KNOWN.get(site,[]):
        c=pd.Timestamp(center)
        ix=np.flatnonzero(d.time.between(c-pd.Timedelta(hours=2),c+pd.Timedelta(hours=2)).to_numpy())
        if not len(ix):
            raise RuntimeError(f'Known event outside period {site} {center}')
        for i in ix:
            known.append({'site':site,'event_center':center,'time':str(d.at[i,'time']),
                          'TA_use_C':t.iloc[i],'raw_TA_C':s.TA_F.iloc[i],
                          'TA_original_QC':s.TA_F_QC.iloc[i],
                          'TA_ERA_C':s.TA_ERA.iloc[i],
                          'VPD_use_hPa':v.iloc[i], 'raw_VPD_hPa':s.VPD_F.iloc[i],
                          'VPD_original_QC':s.VPD_F_QC.iloc[i],
                          'PSRF_Pa':ps.iloc[i],'raw_PA_kPa':s.PA_F.iloc[i],
                          'PA_original_QC':s.PA_F_QC.iloc[i],
                          'PA_ERA_kPa':s.PA_ERA.iloc[i],
                          'RH_pct':rh.iloc[i],'QBOT':d.QBOT.iloc[i],
                          'FLDS':d.FLDS.iloc[i],'FSDS':d.FSDS.iloc[i],
                          'WIND':d.WIND.iloc[i],'PRECTmms':d.PRECTmms.iloc[i]})
    annual=[]
    for year in range(first,last+1):
        mask=d.time.dt.year.eq(year)
        annual.append({'site':site,'year':year,'TA_min_C':float(t[mask].min()),
                       'TA_max_C':float(t[mask].max()),'TA_mean_C':float(t[mask].mean()),
                       'PSRF_min_Pa':float(ps[mask].min()),'PSRF_median_Pa':float(ps[mask].median()),
                       'annual_precip_mm':float(d.PRECTmms[mask].sum()*1800),
                       'FLDS_min_Wm2':float(d.FLDS[mask].min()),
                       'FSDS_max_Wm2':float(d.FSDS[mask].max()),
                       'WIND_max_ms':float(d.WIND[mask].max())})
    print(f'{site:7s} {version:7s} T=[{t.min():6.1f},{t.max():6.1f}] '
          f'Pmin={ps.min():8.0f} Pa  Psteps={summary["PRESSURE_STEP_GT_3000_PA"]:4d} '
          f'Pmedian={summary["PRESSURE_LOCAL_GT_5000_PA"]:4d} '
          f'Tjumps={summary["TA_STEP_GT_12C"]:4d} '
          f'badERA={summary["PRESSURE_RAW_ERA_REF_INVALID"]:4d} '
          f'RHbad={summary["VPD_RH_OUTSIDE_0_100"]:3d}',flush=True)
    return summary,event,known,annual

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=MANIFEST)
    parser.add_argument('--out',type=Path,default=REPORT)
    parser.add_argument('--v5',type=Path,default=V5)
    parser.add_argument('--v12',type=Path,default=V12)
    parser.add_argument('--sites',nargs='*',default=None)
    args=parser.parse_args()
    if args.out.exists():
        raise RuntimeError(f'Report path exists; choose NEW --out: {args.out}')
    if not args.manifest.is_file():
        raise FileNotFoundError(f'Missing existing Stage03a manifest: {args.manifest}')
    meta=pd.read_csv(args.manifest)
    required={'site','primary_file','companion_file','year_start','year_end'}
    if not required.issubset(meta.columns): raise RuntimeError('Input audit manifest columns changed')
    if meta.site.duplicated().any(): raise RuntimeError('Duplicate sites in manifest')
    if args.sites:
        wanted=args.sites
        if len(set(wanted))!=len(wanted) or not set(wanted).issubset(set(meta.site)):
            raise RuntimeError('Invalid --sites values')
        meta=meta.set_index('site').loc[wanted].reset_index()
    if len(meta)<1: raise RuntimeError('Empty input manifest')
    summaries=[]; flagged=[]; contexts=[]; annual=[]
    for _,r in meta.iterrows():
        a,b,c,e=build_site(r.site,r,args.v5,args.v12)
        summaries.append(a); flagged.extend(b); contexts.extend(c);annual.extend(e)
    # Refuse partial audit: write outputs only after ALL requested sites passed
    # source alignment and analysis.
    args.out.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(summaries).to_csv(args.out/'13site_meteorology_summary.csv',index=False)
    pd.DataFrame(flagged).to_csv(args.out/'all_meteorology_flagged_events.csv',index=False)
    pd.DataFrame(contexts).to_csv(args.out/'known_problem_context_2h.csv',index=False)
    pd.DataFrame(annual).to_csv(args.out/'annual_meteorology_ranges.csv',index=False)
    (args.out/'README.txt').write_text(
        'READ-ONLY candidate meteorological QC. These flags are prompts for science review, NOT changes.\n'
        'Pressure thresholds are local/temporal, NOT sea-level absolute cutoffs.\n'
        'Raw FLUXNET ERA and companion references may share the same errors.\n'
        'Stage12 selected: DE-Lnf, ES-Agu, ES-LJu; other stations: QC v5.\n'
        'BIF/ZBOT/PFT/DATM/Spin-up are intentionally excluded.\n')
    print('\nAUDIT SUCCESS:',len(summaries),'selected sites; NO forcing written.')
    print('Reports:',args.out)
    print('Next: review P0 pressure/physics; 2h known-event context; temperature QC source switches; radiative extremes.')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('AUDIT ERROR:',type(e).__name__,str(e),file=sys.stderr)
        sys.exit(1)
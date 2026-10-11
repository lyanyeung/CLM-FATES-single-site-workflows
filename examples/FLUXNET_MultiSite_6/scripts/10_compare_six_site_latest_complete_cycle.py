#!/usr/bin/env python3
"""Read-only six-site diagnostic: most recent *complete* DATM cycle vs EC GPP/NEE.

Matches ES-LJu 09_compare_fates_ec.py conventions. No case or input modifications.
For a model start year S and N-year forcing cycle, the aligned complete cycles
are [S+k*N, S+(k+1)*N-1]. Only archived, complete h0a years are considered.
Model dates are remapped to the corresponding EC year by their cycle position.

Requires: conda activate clm_fates_env (netCDF4, numpy, pandas, matplotlib).
Usage: python ~/10_compare_six_site_latest_complete_cycle.py
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import traceback
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

SITES = {
    'DE-Hai': (2000, 2025),
    'RU-Fyo': (1998, 2025),
    'DE-Tha': (1996, 2025),
    'DK-Sor': (1996, 2024),
    'NL-Loo': (1997, 2025),
    'IL-Yat': (2000, 2024),
}
EC_TO_GCD = 86400.0 * 12.0107e-6  # µmol CO2 m-2 s-1 => g C m-2 d-1
FATES_TO_GCD = 86400.0 * 1000.0  # kg C m-2 s-1 => g C m-2 d-1
YLABEL = r'g C m$^{-2}$ d$^{-1}$'
YEAR_RE = re.compile(r'\.clm2\.h0a\.(\d{4})-01-0[12]-00000\.nc$')


def point_array(var):
    a = var[:]
    if np.ma.isMaskedArray(a):
        a = a.filled(np.nan)
    a = np.asarray(a, dtype=float)
    dims = list(var.dimensions)
    if 'time' not in dims:
        raise ValueError(f'{var.name}: no time dimension ({dims})')
    a = np.moveaxis(a, dims.index('time'), 0)
    a = a.reshape(a.shape[0], -1)
    if a.shape[1] != 1:
        raise ValueError(f'{var.name}: expected a single site point, shape={a.shape}')
    return a[:, 0]


def nc_dates(ds):
    t = ds.variables['time']
    if 'time_bounds' in ds.variables:
        val = ds.variables['time_bounds'][:, 0]
    elif 'time_bnds' in ds.variables:
        val = ds.variables['time_bnds'][:, 0]
    else:
        raise ValueError('No time_bounds/time_bnds. Refusing ambiguous end-of-interval dates.')
    # cftime supports model years beyond 2262; remap to EC years before pandas.
    return num2date(val, t.units, calendar=getattr(t, 'calendar', 'noleap'),
                    only_use_cftime_datetimes=True)


def history_index(archive, case_name):
    hist = archive / case_name / 'lnd' / 'hist'
    if not hist.is_dir():
        raise FileNotFoundError(f'No archive history directory: {hist}')
    found = {}
    for p in hist.glob(f'{case_name}.clm2.h0a.*.nc'):
        m = YEAR_RE.search(p.name)
        if not m:
            continue
        year = int(m.group(1))
        if year in found:
            raise ValueError(f'Duplicate model-year history for {year}')
        found[year] = p
    if not found:
        raise FileNotFoundError(f'No annual h0a NetCDF files under {hist}')
    return found


def latest_complete_cycle(found, first, last):
    n = last - first + 1
    if max(found) < first + n - 1:
        raise ValueError(f'Not enough archived years for one {n}-year cycle')
    k_max = (max(found) - first + 1) // n - 1
    for k in range(k_max, -1, -1):
        start = first + k*n
        years = list(range(start, start+n))
        if all(y in found for y in years):
            return k, years
    raise ValueError('No complete, aligned historic forcing cycle in archived h0a files')


def fates_daily(paths, first, last):
    n = last-first+1
    rows = []
    for model_year, path in paths:
        ec_year = first + (model_year - first) % n
        with Dataset(path) as ds:
            for name in ('FATES_GPP', 'FATES_NEP'):
                if name not in ds.variables:
                    raise KeyError(f'{path}: {name} unavailable')
                u = getattr(ds.variables[name], 'units', '').replace(' ', '')
                # ES-LJu precedent: FATES fluxes are kg C m-2 s-1; block different units.
                if u and ('kg' not in u.lower() or 's-1' not in u.lower()
                          and '/s' not in u.lower() and 's^-1' not in u.lower()):
                    raise ValueError(f'{path.name} {name} units={u!r}, check factor')
            dates = nc_dates(ds)
            gpp = point_array(ds.variables['FATES_GPP']) * FATES_TO_GCD
            nee = -point_array(ds.variables['FATES_NEP']) * FATES_TO_GCD
            if not (len(dates) == len(gpp) == len(nee) == 365):
                raise ValueError(f'{path.name}: expected 365 daily samples; got '
                                 f'{len(dates)}, {len(gpp)}, {len(nee)}')
            dates_ec = []
            for d in dates:
                if d.year != model_year or (d.month, d.day) == (2, 29):
                    raise ValueError(f'{path.name}: incompatible daily date {d}')
                dates_ec.append(pd.Timestamp(ec_year, d.month, d.day))
            if len(set(dates_ec)) != 365:
                raise ValueError(f'{path.name}: duplicate model daily dates')
            rows.append(pd.DataFrame({'date': dates_ec, 'FATES_GPP': gpp,
                                      'FATES_NEE': nee, 'model_year': model_year}))
    model = pd.concat(rows, ignore_index=True).sort_values('date')
    if model['date'].duplicated().any():
        raise ValueError('Duplicated mapped EC dates; check cycle alignment')
    return model


def find_flux_file(raw, preferred_gpp, override=None):
    if override:
        p = Path(override).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f'EC file override not found: {p}')
        candidates = [p]
    else:
        if not raw.exists():
            raise FileNotFoundError(f'Raw FLUXNET directory missing: {raw}')
        # The forcing FLUXMET_HH file is *not* assumed to contain EC carbon fluxes.
        candidates = [p for p in raw.rglob('*.csv') if any(k in p.name.upper()
                      for k in ('FLUX_HH', 'FULLSET_HH', 'FLUXMET_HH', 'FLUXES_HH'))]
    valid = []
    for p in candidates:
        try:
            with p.open('r', encoding='latin-1', newline='') as f:
                header = next(csv.reader(f))
        except Exception:
            continue
        cols = set(header)
        if 'TIMESTAMP_START' not in cols or 'NEE_VUT_REF' not in cols:
            continue
        gpp = preferred_gpp if preferred_gpp in cols else (
            'GPP_NT_VUT_REF' if 'GPP_NT_VUT_REF' in cols else
            'GPP_DT_VUT_REF' if 'GPP_DT_VUT_REF' in cols else None)
        if not gpp:
            continue
        name = p.name.upper()
        score = (0 if 'FLUX_HH' in name or 'FLUXES_HH' in name else
                 1 if 'FULLSET_HH' in name else 2)
        valid.append((score, p, gpp))
    if not valid:
        detail = '\n'.join('  '+str(x) for x in candidates[:12])
        raise FileNotFoundError('No raw HH flux CSV containing NEE_VUT_REF and '
                                'GPP_DT/NT_VUT_REF. Candidates:\n'+detail)
    valid.sort(key=lambda x:(x[0], str(x[1])))
    best = [x for x in valid if x[0] == valid[0][0]]
    if len(best) > 1 and not override:
        raise ValueError('Multiple equivalent EC flux CSVs; select explicitly with '
                         '--obs-csv SITE=/full/path.csv: '+str([str(x[1]) for x in best]))
    return valid[0][1], valid[0][2]


def ec_daily(path, gpp_col, first, last, min_halfhour):
    raw = pd.read_csv(path, usecols=['TIMESTAMP_START',gpp_col,'NEE_VUT_REF'],
                      dtype={'TIMESTAMP_START':'str'}, low_memory=False, encoding='latin-1')
    s = raw['TIMESTAMP_START'].str.strip().str.replace(r'\.0$', '',regex=True)
    if s.str.fullmatch(r'\d{12}').all():
        dates = pd.to_datetime(s, format='%Y%m%d%H%M',errors='raise')
    else:
        dates = pd.to_datetime(s,errors='raise')
    raw['date'] = dates
    raw = raw.loc[raw['date'].dt.year.between(first,last)].copy()
    raw = raw.loc[~((raw['date'].dt.month==2)&(raw['date'].dt.day==29))]
    if raw['date'].duplicated().any():
        raise ValueError(f'EC time duplicates in {path}')
    if raw.empty:
        raise ValueError(f'EC flux timestamps do not overlap {first}-{last}: {path}')
    raw = raw.set_index('date').sort_index()
    pieces=[]
    for col,new in ((gpp_col,'EC_GPP'), ('NEE_VUT_REF','EC_NEE')):
        vals=pd.to_numeric(raw[col],errors='coerce').astype(float)
        vals[(vals<=-9990)|(~np.isfinite(vals))]=np.nan
        daily_mean=vals.resample('D').mean()
        daily_n=vals.resample('D').count()
        daily_mean[daily_n < min_halfhour]=np.nan
        pieces.append(daily_mean.mul(EC_TO_GCD).rename(new))
    return pd.concat(pieces,axis=1).reset_index().rename(columns={'date':'date'})


def paired_monthly(daily,obs,mod,min_days):
    x=daily[['date',obs,mod]].dropna().set_index('date')
    m=x.resample('MS').mean()
    nd=x[obs].resample('MS').count()
    m.loc[nd<min_days,[obs,mod]]=np.nan
    m[f'{obs}_NDAY']=nd
    return m.reset_index()


def metrics(obs,mod):
    x=np.asarray(obs,float);y=np.asarray(mod,float)
    good=np.isfinite(x)&np.isfinite(y);x=x[good];y=y[good]
    out={'N':len(x),'R':np.nan,'R2':np.nan,'RMSE':np.nan,
         'MAE':np.nan,'Bias':np.nan}
    if len(x)<2:
        return out
    diff=y-x
    den=np.sum((x-np.mean(x))**2)
    out.update(R=float(np.corrcoef(x,y)[0,1]) if np.std(x)>0 and np.std(y)>0 else np.nan,
               R2=float(1-np.sum(diff**2)/den) if den>0 else np.nan,
               RMSE=float(np.sqrt(np.mean(diff**2))),
               MAE=float(np.mean(np.abs(diff))),Bias=float(np.mean(diff)))
    return out


def plot_flux(data,site,flux,a,b,model_first,model_last,out):
    obs,mod=(f'EC_{flux}',f'FATES_{flux}')
    x=data.loc[data['date'].dt.year.between(a,b)].copy()
    fig,ax=plt.subplots(figsize=(15,5))
    ax.plot(x['date'],x[obs],label='EC tower',linewidth=1.5)
    ax.plot(x['date'],x[mod],label='FATES',linewidth=1.5)
    if flux=='NEE':
        ax.axhline(0,linestyle='--',linewidth=0.8,color='gray')
    ax.set_xlabel('Year')
    ax.set_ylabel(f'{flux} ({YLABEL})')
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlim(pd.Timestamp(a,1,1),pd.Timestamp(b+1,1,1))
    ax.legend(frameon=False)
    ax.grid(alpha=.2)
    ax.set_title(f'{site} monthly {flux}: EC tower vs FATES ({a}-{b})\n'
                 f'Last complete archived forcing cycle: model {model_first}-{model_last} '
                 '[interim spin-up diagnostic]')
    fig.tight_layout()
    outfile=out/f'{site}_{flux}_monthly_{a}_{b}.png'
    fig.savefig(outfile,dpi=300,bbox_inches='tight');plt.close(fig)
    return outfile


def plot_overview(monthly,site,first,last,model_first,model_last,out):
    fig,axes=plt.subplots(2,1,figsize=(16,8),sharex=True)
    for ax,flux in zip(axes,('GPP','NEE')):
        ax.plot(monthly['date'],monthly[f'EC_{flux}'],label='EC tower',linewidth=1.3)
        ax.plot(monthly['date'],monthly[f'FATES_{flux}'],label='FATES',linewidth=1.3)
        if flux=='NEE':
            ax.axhline(0,color='gray',linestyle='--',linewidth=.8)
        ax.set_ylabel(f'{flux} ({YLABEL})');ax.grid(alpha=.2)
        ax.legend(frameon=False)
    axes[-1].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    axes[-1].set_xlim(pd.Timestamp(first,1,1),pd.Timestamp(last+1,1,1))
    axes[-1].set_xlabel('EC observation year')
    fig.suptitle(f'{site}: EC tower vs FATES (monthly means, {first}-{last})\n'
                 f'Archived complete model cycle {model_first}-{model_last}; '
                 'interim spin-up diagnostic',fontsize=13)
    fig.tight_layout()
    outfile=out/f'{site}_GPP_NEE_monthly_overview.png'
    fig.savefig(outfile,dpi=250,bbox_inches='tight');plt.close(fig)
    return outfile


def verify_stream(case_path, first, last):
    p = case_path / 'user_nl_datm_streams'
    if not p.is_file():
        raise FileNotFoundError(f'Missing DATM stream: {p}')
    content = p.read_text()
    expected = {'taxmode':'cycle', 'year_first':str(first),
                'year_last':str(last), 'year_align':str(first)}
    for key, val in expected.items():
        matches = re.findall(
            rf'(?m)^\s*CLM_USRDAT\.UNSET:{key}\s*=\s*(\S+)', content)
        if matches != [val]:
            raise ValueError(f'{p}: expected {key}={val}; got {matches}')


def process_site(site,args,override):
    first,last=SITES[site]
    n=last-first+1
    case_name=f'{site}_FATES_SPINUP500'
    verify_stream(args.cases_root/case_name, first, last)
    found=history_index(args.archive_root,case_name)
    k,years=latest_complete_cycle(found,first,last)
    mod_first,mod_last=years[0],years[-1]
    print(f'  Archived h0a files: {len(found)}; latest model year: {max(found)}',flush=True)
    print(f'  Latest COMPLETE {n}-year cycle: model {mod_first}-{mod_last}'
          f' -> EC {first}-{last}',flush=True)
    site_root=args.sites_root/site
    obs_file,gpp_col=find_flux_file(site_root/'forcing'/'raw',args.gpp_preference,override)
    print(f'  EC file: {obs_file}; GPP column: {gpp_col}',flush=True)
    model=fates_daily([(y,found[y]) for y in years],first,last)
    obs=ec_daily(obs_file,gpp_col,first,last,args.min_halfhour)
    daily=model.merge(obs,on='date',how='left',validate='one_to_one')
    if len(daily) != n*365:
        raise ValueError('Mapped model daily output is not a full NO_LEAP cycle')
    gpp_m=paired_monthly(daily,'EC_GPP','FATES_GPP',args.min_days)
    nee_m=paired_monthly(daily,'EC_NEE','FATES_NEE',args.min_days)
    monthly=gpp_m.merge(nee_m,on='date',how='outer',validate='one_to_one')
    for flux in ('GPP','NEE'):
        matched = int((monthly[f'EC_{flux}'].notna() & monthly[f'FATES_{flux}'].notna()).sum())
        if matched < 2:
            raise ValueError(f'Only {matched} monthly EC-vs-FATES pairs for {flux}; '
                             'check EC product, model output and units')
    out=site_root/'validation'/'spinup_latest_complete_cycle'
    out.mkdir(parents=True,exist_ok=True)
    # Records model-year provenance as well as the aligned EC comparison years.
    daily.to_csv(out/f'{site}_daily_FATES_vs_EC.csv',index=False)
    monthly.to_csv(out/f'{site}_monthly_FATES_vs_EC.csv',index=False)
    mrows=[]
    for scale,data in (('daily',daily),('monthly',monthly)):
        for flux in ('GPP','NEE'):
            row={'Site':site,'Scale':scale,'Flux':flux,
                 'ModelCycleStart':mod_first,'ModelCycleEnd':mod_last,
                 'ECStart':first,'ECEnd':last,'ECGPPColumn':gpp_col}
            row.update(metrics(data[f'EC_{flux}'],data[f'FATES_{flux}']))
            mrows.append(row)
    pd.DataFrame(mrows).to_csv(out/f'{site}_FATES_vs_EC_metrics.csv',index=False)
    graphics=[plot_overview(monthly,site,first,last,mod_first,mod_last,out)]
    for a in range(first,last+1,10):
        b=min(a+9,last)
        for flux in ('GPP','NEE'):
            graphics.append(plot_flux(monthly,site,flux,a,b,mod_first,mod_last,out))
    meta={'site':site,'status':'OK','comparison_type':'interim_last_complete_aligned_cycle',
          'ec_years':[first,last],'model_years':[mod_first,mod_last],
          'forcing_cycle_years':n,'complete_cycle_index_zero_based':k,
          'archived_annual_hist_files':len(found),'max_archived_model_year':max(found),
          'ec_file':str(obs_file),'ec_gpp_column':gpp_col,
          'model_gpp':'FATES_GPP','model_nee':'-FATES_NEP',
          'ec_nee':'NEE_VUT_REF','unit':'g C m-2 d-1',
          'plots':[x.name for x in graphics],
          'warning':'Interim spin-up output; not a claim of convergence or site-surface validity.'}
    (out/f'{site}_provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    for row in mrows:
        if row['Scale']=='monthly':
            print(f"  {row['Flux']} monthly matched months={row['N']}; "
                  f"R2={row['R2']:.3f}; RMSE={row['RMSE']:.3f}",flush=True)
    print(f'  Saved {len(graphics)} PNG charts and CSV/JSON to: {out}',flush=True)
    return {'site':site,'status':'OK','model_cycle_first':mod_first,
            'model_cycle_last':mod_last,'EC_years':f'{first}-{last}',
            'archived_hist_files':len(found),'output_dir':str(out),
            'gpp_source':gpp_col,
            'GPP_monthly_pairs':next(r['N'] for r in mrows if r['Scale']=='monthly' and r['Flux']=='GPP'),
            'NEE_monthly_pairs':next(r['N'] for r in mrows if r['Scale']=='monthly' and r['Flux']=='NEE')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sites',nargs='+',choices=tuple(SITES),default=list(SITES))
    p.add_argument('--user',default='ly3n24')
    p.add_argument('--sites-root',type=Path,default=None)
    p.add_argument('--cases-root',type=Path,default=None)
    p.add_argument('--archive-root',type=Path,default=None)
    p.add_argument('--obs-csv',nargs='*',default=[],metavar='SITE=/path/to/FLUX_HH.csv',
                   help='Override EC flux CSV auto-detection for one or more sites')
    p.add_argument('--gpp-preference',choices=['GPP_DT_VUT_REF','GPP_NT_VUT_REF'],
                   default='GPP_DT_VUT_REF')
    p.add_argument('--min-halfhour',type=int,default=40)
    p.add_argument('--min-days',type=int,default=20)
    args=p.parse_args()
    if args.sites_root is None:
        args.sites_root=Path(f'/iridisfs/scratch/{args.user}/CLM_FATES/sites/MY_EC_SITE')
    if args.cases_root is None:
        args.cases_root=Path(f'/iridisfs/scratch/{args.user}/CLM_FATES/cases')
    if args.archive_root is None:
        args.archive_root=Path(f'/scratch/{args.user}/CTSM_FATES_OUTPUTS/archive')
    overrides={}
    for a in args.obs_csv:
        if '=' not in a:
            p.error(f'Invalid --obs-csv {a}: expected SITE=/path.csv')
        site,_,path=a.partition('=')
        if site not in SITES or not path:
            p.error(f'Invalid --obs-csv {a}')
        overrides[site]=path
    summary=[]
    for site in args.sites:
        print('\n'+'='*22+' '+site+' '+'='*22,flush=True)
        try:
            row=process_site(site,args,overrides.get(site))
        except Exception as e:
            print(f'  ERROR [{site}]: {type(e).__name__}: {e}',flush=True)
            traceback.print_exc()
            row={'site':site,'status':'ERROR','error':str(e)}
        summary.append(row)
    dest=Path.home()/'six_site_last_cycle_comparison'
    dest.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(summary).to_csv(dest/'site_summary.csv',index=False)
    print('\n'+'='*20+' SUMMARY '+'='*20,flush=True)
    print(pd.DataFrame(summary).to_string(index=False),flush=True)
    print(f'Summary: {dest / "site_summary.csv"}')
    if any(x['status']!='OK' for x in summary):
        sys.exit(1)

if __name__=='__main__':
    main()

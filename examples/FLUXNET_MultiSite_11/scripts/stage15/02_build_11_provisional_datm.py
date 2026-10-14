#!/usr/bin/env python3
"""Eleven-site candidate DATM with dated TA_F ZBOT and explicit early-height backfill.

Default: read-only preflight of all 11 selected candidate CSVs, BIF policy,
all 7 meteorological fields, humidity thermodynamics and surface coordinates.
--write-provisional: create NEW, uniquely named review-only annual NetCDFs.
Never approves forcing for a production CLM-FATES spin-up.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
POLICY=Path.home()/'FLUXNET_MultiSite_11'/'stage15_provisional_DATM'/'height_policy_v1.json'
REPORT=Path.home()/'FLUXNET_MultiSite_11'/'stage15_provisional_DATM'
TAG='datm_11_provisional_dynamic_zbot_v1'
REQUIRED=['time','TA_F','VPD_F','PA_F','SW_IN_F','LW_IN_F','WS_F','P_F']
UNITS={
  'TBOT':'K','QBOT':'kg/kg','PSRF':'Pa','FSDS':'W/m2',
  'FLDS':'W/m2','WIND':'m/s','PRECTmms':'mm/s', 'ZBOT':'m',
}
DESCRIPTIONS={
  'TBOT':'air temperature at reference height',
  'QBOT':'specific humidity derived from VPD, TA and PA',
  'PSRF':'surface atmospheric pressure',
  'FSDS':'downward shortwave radiation',
  'FLDS':'downward longwave radiation',
  'WIND':'wind speed, not height normalized',
  'PRECTmms':'precipitation rate derived from half-hour amount',
  'ZBOT':'time-varying TA_F BIF observation height with explicitly backfilled early gaps',
}


def sha256(path):
    d=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(4*1024*1024),b''):d.update(c)
    return d.hexdigest()


def time_axis(start,end):
    idx=pd.date_range(f'{start}-01-01 00:00',f'{end}-12-31 23:30',freq='30min')
    return idx[~((idx.month==2)&(idx.day==29))]


def height_timeline(records,times):
    rec=records['recorded_history']
    if not rec:return None,None
    stamps=np.array([pd.Timestamp(x['effective_from']).to_datetime64() for x in rec],dtype='datetime64[ns]')
    h=np.array([float(x['height_m']) for x in rec])
    loc=np.searchsorted(stamps,times.to_numpy(dtype='datetime64[ns]'),side='right')-1
    early=loc<0
    values=h[np.maximum(loc,0)]
    assert int(early.sum())==int(records['early_noleap_halfhours']), 'Height backfill count changed'
    if early.any():
        allowed=records['early_fill_m']
        if allowed is None or abs(allowed-h[0])>1e-8:
            raise ValueError('Explicit earliest height backfill not authorized / inconsistent')
    return values,early


def surface_info(sitepath):
    from netCDF4 import Dataset
    surfaces=sorted((sitepath/'subset_data').rglob('surfdata*.nc'))
    if len(surfaces)!=1:raise ValueError(f'expect exactly one surface, found {len(surfaces)}')
    surf=surfaces[0]
    with Dataset(surf) as nc:
        def scalar(names):
            for name in names:
                if name in nc.variables:
                    x=np.asarray(np.ma.filled(nc[name][:],np.nan),dtype=float).ravel()
                    if x.size==1 and np.isfinite(x[0]):return float(x[0])
            raise ValueError(f'{surf}: could not read single-cell coordinate from {names}')
        lat=scalar(['LATIXY','lat','latitude'])
        lon=scalar(['LONGXY','lon','longitude'])
        crop=scalar(['PCT_CROP']) if 'PCT_CROP' in nc.variables else None
    if not (-90<=lat<=90 and -180<=lon<=360):raise ValueError('Invalid surface lat/lon')
    if lon>180:lon-=360
    return {'lat':lat,'lon':lon,'surface':str(surf),'crop_pct':crop}


def inspect_site(root,site,policy):
    d=policy['sites'][site]
    start,end=d['years'];tag=d['candidate_tag']
    where=root/site/'forcing'/f'merged_multisource_11_{tag}'
    candidate=where/f'{site}_multisource_HH_{start}_{end}_candidate.csv'
    status=where/'status.json'
    if not candidate.is_file() or not status.is_file():
        raise ValueError(f'Candidate/status missing: {candidate}')
    meta=json.loads(status.read_text())
    if meta.get('site')!=site:raise ValueError('Site name mismatch in candidate status')
    checksum=sha256(candidate)
    # Stage07 pressure07a uses trial_sha256; Stage03/08/11 use candidate_sha256.
    # Verify the real CSV against the original immutable source manifest; never reset it.
    digest_field = 'trial_sha256' if tag == 'pressure07a' else 'candidate_sha256'
    expected_digest = meta.get(digest_field)
    if not isinstance(expected_digest, str) or len(expected_digest) != 64:
        raise ValueError(f'Missing/invalid {digest_field} in {status}')
    if checksum != expected_digest:
        raise ValueError(f'CSV SHA256 mismatch ({digest_field}): actual={checksum}, recorded={expected_digest}')
    if tag == 'pressure07a':
        expected_pressure_edits = {'CH-Fru': 6, 'CZ-Stn': 3}
        if (site not in expected_pressure_edits or
            meta.get('stage') != 'PA_LOCAL_INTERPOLATION_REVIEW_ONLY' or
            meta.get('modified_pressure_records') != expected_pressure_edits[site]):
            raise ValueError(f'{site}: unexpected Stage07 pressure trial metadata')
    if site=='CH-Aws' and checksum!='130df2cd6c0bf9b89fc4895bca19145e1aca8bf0d4e5d7f48edb85df22035239':
        raise ValueError('CH-Aws unexpected post-Stage11 candidate digest')
    f=pd.read_csv(candidate,usecols=lambda c:c in REQUIRED,low_memory=False)
    missing=set(REQUIRED)-set(f.columns)
    if missing:raise ValueError('Missing source variables '+','.join(sorted(missing)))
    times=pd.DatetimeIndex(pd.to_datetime(f.time,errors='raise'))
    expected=time_axis(start,end)
    if not times.equals(expected):raise ValueError('Half-hour NO_LEAP time axis differs')
    vals={x:pd.to_numeric(f[x],errors='coerce').to_numpy(dtype='float64') for x in REQUIRED[1:]}
    for x,arr in vals.items():
        if not np.isfinite(arr).all():raise ValueError(f'{x}: missing/nonfinite values')
    ta=vals['TA_F'];vpd=vals['VPD_F'];p=vals['PA_F'];sw=vals['SW_IN_F'];lw=vals['LW_IN_F'];wind=vals['WS_F'];rain=vals['P_F']
    constraints=[('TA_F',ta,-80,65),('PA_F',p,50,110),('VPD_F',vpd,-.1,125),
                 ('SW_IN_F',sw,0,1600),('LW_IN_F',lw,60,800),('WS_F',wind,0,75),('P_F',rain,0,300)]
    for name,x,low,high in constraints:
        bad=(x<low)|(x>high)
        if bad.any():
            first_bad=str(times[np.flatnonzero(bad)[0]])
            raise ValueError(f'{name} {int(bad.sum())} values outside DATM [{low},{high}], earliest {first_bad}; do not silently clip')
    with np.errstate(invalid='ignore',over='ignore',divide='ignore'):
        es=6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-100,100))
        ea=es-vpd
        pressure=p*1000
        rh=100*ea/es
        q=.622*(ea*100)/(pressure-.378*(ea*100))
        qsat=.622*(es*100)/(pressure-.378*(es*100))
    if not np.all(np.isfinite(q)&(ea>0)&(rh>0)&(rh<=100.05)&(q>=0)&(q<=qsat*1.001)):
        raise ValueError('Humidity is nonphysical under the selected water-saturation convention')
    met={
       'TBOT':ta+273.15,'QBOT':q,'PSRF':pressure,
       'FSDS':sw,'FLDS':lw,'WIND':wind,'PRECTmms':rain/1800.0,
    }
    z,early=height_timeline(d['TA_F'],times)
    if z is None or not np.all(np.isfinite(z)&(z>=.5)&(z<=150)):
        raise ValueError('TA_F ZBOT absent or outside height bounds')
    wz,windearly=height_timeline(d['WS_F'],times)
    both_documented=(~early)&(~windearly) if wz is not None else np.zeros(len(times),dtype=bool)
    known_mismatch=int((both_documented&(np.abs(z-wz)>3)).sum()) if wz is not None else None
    surface=surface_info(root/site)
    return {'site':site,'years':[start,end],'candidate':str(candidate),
            'candidate_sha256':checksum,'selected_tag':tag,'times':times,
            'met':met,'zbot':z,'early':early,'wind_height':wz,'wind_early':windearly,
            'known_mismatch_gt3m':known_mismatch,'surface':surface,
            'precip_first_last_year_mm':[
                round(float(sum(rain[times.year==yr])),2) for yr in (start,end)],
            'chaws_high_uncertainty_events':33 if site=='CH-Aws' else 0}


def annual_nc(path,site,year,data,policy_hash):
    from netCDF4 import Dataset
    mask=data['times'].year==year
    z=data['zbot'][mask]
    if len(z)!=17520:raise ValueError(f'{site} {year} did not have 17520 records')
    if path.exists() or path.with_suffix('.nc.partial').exists():
        raise FileExistsError(f'Do not overwrite {path}')
    tmp=path.with_suffix('.nc.partial')
    try:
        with Dataset(tmp,'w',format='NETCDF4_CLASSIC') as nc:
            nc.createDimension('time',17520)
            nc.createDimension('lat',1)
            nc.createDimension('lon',1)
            v=nc.createVariable('time','f8',('time',))
            v.units=f'days since {year}-01-01 00:00:00'
            v.calendar='noleap';v.long_name='model time on NO_LEAP calendar'
            v[:]=np.arange(17520,dtype=np.float64)/48.
            la=nc.createVariable('lat','f8',('lat',));la.units='degrees_north';la[:]=data['surface']['lat']
            lo=nc.createVariable('lon','f8',('lon',));lo.units='degrees_east';lo[:]=data['surface']['lon']
            laxy=nc.createVariable('LATIXY','f8',('lat','lon'));laxy.units='degrees_north';laxy[:,:]=data['surface']['lat']
            loxy=nc.createVariable('LONGXY','f8',('lat','lon'));loxy.units='degrees_east';loxy[:,:]=data['surface']['lon']
            for key,values in [*data['met'].items(),('ZBOT',data['zbot'])]:
                dtype='f8' if key=='ZBOT' else 'f4'
                v=nc.createVariable(key,dtype,('time','lat','lon'),zlib=True,complevel=1,fill_value=1e36)
                v.units=UNITS[key];v.long_name=DESCRIPTIONS[key]
                v[:,0,0]=values[mask].astype('float64' if key=='ZBOT' else 'float32')
            nc.site=site
            nc.forcing_year=int(year)
            nc.calendar='noleap';nc.time_resolution='30 minutes'
            nc.provenance_status='PROVISIONAL_FOR_SCIENTIFIC_REVIEW_NOT_APPROVED_FOR_SPINUP'
            nc.source_candidate=data['candidate']
            nc.source_candidate_sha256=data['candidate_sha256']
            nc.source_candidate_tag=data['selected_tag']
            nc.zbot_height_policy_sha256=policy_hash
            nc.zbot_source='dated TA_F BIF height; earliest BIF height explicitly backfilled before first event'
            nc.zbot_early_backfill_halfhours=int(data['early'][mask].sum())
            nc.wind_height_source='WS_F BIF only; WIND values unchanged, not vertically normalized'
            nc.wind_height_missing_all=int(data['wind_height'] is None)
            nc.ta_ws_documented_height_mismatch_gt3m_halfhours=(
                int(((~data['early'])&(~data['wind_early'])&(np.abs(data['zbot']-data['wind_height'])>3))[mask].sum())
                if data['wind_height'] is not None else -1)
            nc.surface_file=data['surface']['surface']
            nc.precip_conversion='P_F millimetres per half-hour divided by 1800 seconds -> PRECTmms mm/s'
            if site=='CH-Aws':
                nc.humidity_warning='559 ERA5-Land-based winter humidity trial values; 33 ERA5/ERA5-Land high disagreement; no qualified winter tower reference'
        with Dataset(tmp) as verify:
            assert len(verify.dimensions['time'])==17520
            assert np.array_equal(np.asarray(verify['ZBOT'][:,0,0]),z)
            assert np.allclose(np.asarray(verify['time'][:]),np.arange(17520)/48)
            assert verify.source_candidate_sha256==data['candidate_sha256']
            for key in UNITS:
                assert key in verify.variables
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--policy',type=Path,default=POLICY)
    p.add_argument('--report',type=Path,default=REPORT)
    p.add_argument('--sites',nargs='+')
    p.add_argument('--write-provisional',action='store_true')
    a=p.parse_args()
    if not a.policy.exists():raise SystemExit(f'Missing frozen height policy: {a.policy}')
    policy=json.loads(a.policy.read_text())
    if policy.get('format')!='eleven_site_zbot_policy_v1':
        raise SystemExit('Invalid ZBOT policy format')
    selected=a.sites or list(policy['sites'])
    if len(set(selected))!=len(selected) or any(x not in policy['sites'] for x in selected):
        raise SystemExit('Site selection is invalid')
    policy_hash=sha256(a.policy)
    # Preflight EVERY requested site before any NetCDF is written.
    reports=[]
    errors=[]
    for site in selected:
        try:
            d=inspect_site(a.root,site,policy)
            r={k:d[k] for k in ('site','years','candidate_sha256','selected_tag','known_mismatch_gt3m','precip_first_last_year_mm')}
            r.update({'status':'PREFLIGHT_NUMERIC_AND_ZBOT_OK_SCIENCE_REVIEW',
                      'expected_netcdf':d['years'][1]-d['years'][0]+1,
                      'zbot_early_halfhours':int(d['early'].sum()),
                      'wind_height_missing_all':d['wind_height'] is None,
                      'surface_crop_pct':d['surface']['crop_pct']})
            print(f"{site:<7s} {r['selected_tag']:<16s} years={r['expected_netcdf']:>2d} "
                  f"early_ZBOT={r['zbot_early_halfhours']:>7d} "
                  f"crop={str(r['surface_crop_pct']):>6s} PREFLIGHT_OK_SCIENCE_REVIEW",flush=True)
            reports.append(r)
        except Exception as e:
            errors.append((site,str(e)))
            print(site,'BLOCKED:',str(e),flush=True)
    print(f'SUMMARY: {len(reports)}/{len(selected)} NUMERIC/ZBOT preflight pass; scientific review remains.')
    if errors:raise SystemExit('No DATM files written; resolve blocking cases: '+repr(errors))
    if not a.write_provisional:
        print('READ-ONLY: no NetCDF or source files changed. Use --write-provisional only for explicitly labelled test inputs.')
        return
    for site in selected:
        target=a.root/site/'forcing'/TAG
        if target.exists():raise SystemExit(f'Existing target directory: {target}; refusing entire write operation')
    a.report.mkdir(parents=True,exist_ok=True)
    total=0
    for i,site in enumerate(selected,1):
        d=inspect_site(a.root,site,policy)
        target=a.root/site/'forcing'/TAG
        target.mkdir(parents=True,exist_ok=False)
        first,last=d['years']
        for year in range(first,last+1):
            annual_nc(target/f'{site}_DATM_{year}.nc',site,year,d,policy_hash)
            total+=1
        reports[i-1]['status']='PROVISIONAL_WRITTEN_SCIENCE_REVIEW_REQUIRED'
        reports[i-1]['output_directory']=str(target)
        print(f'{site}: wrote {last-first+1} yearly NetCDF (PROVISIONAL)',flush=True)
    out=a.report/'datm_11_provisional_summary_v1.json'
    if out.exists():raise SystemExit(f'Summary already exists: {out}')
    with out.open('x') as f:
        json.dump({'policy_sha256':policy_hash,'files_expected':total,
                   'status':'PROVISIONAL_NOT_APPROVED_FOR_SPINUP','sites':reports},f,indent=2)
    print('WRITTEN:',total,'annual NetCDF. Run independent audit; DO NOT submit spin-up yet.')

if __name__=='__main__':main()

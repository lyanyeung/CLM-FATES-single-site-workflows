#!/usr/bin/env python3
"""CH-Aws exploratory 77-row ERA5-Land RH full-cycle DATM sensitivity.

Default --audit reads inputs but writes no forcing. --write requires explicit
acknowledgment, creates independent 19-year overlay (7 modified annual
NetCDFs + 12 symlinks to RH25A v3), never overwrites. --verify is read-only.
No Slurm job, CIME edits, or proven numerical/meteorological correction.
"""
from pathlib import Path
from netCDF4 import Dataset, num2date
import pandas as pd
import numpy as np
import shutil, tempfile, hashlib, json, os, argparse

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing')
V3 = ROOT/'datm_11_landrh25a_dynamic_zbot_v3'
V4 = ROOT/'datm_11_stage28_jan14_trial_v4/CH-Aws_DATM_2006.nc'
CSV = ROOT/'merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv'
REF = Path.home()/'FLUXNET_MultiSite_11/stage20_CH_Aws_RH_QC_expansion_audit/01_low_and_boundary_events_review.csv'
CACHE = Path.home()/'FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo'
OUT = ROOT/'datm_11_stage29_all77_rh_sensitivity_v5'

def require(cond, why):
    if not cond: raise RuntimeError('STOP: '+why)

def sha(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for x in iter(lambda:f.read(1<<20), b''): h.update(x)
    return h.hexdigest()

def sat(t):
    t = np.asarray(t,dtype=float)
    return 6.112*np.exp(np.clip(17.67*t/(t+243.5),-100,100))

def reference_2014(model, dates):
    path = CACHE/f'{model}_2014.json'
    require(path.is_file(), f'2014 reference missing: {path}; run Stage29 30 --fetch')
    data = json.loads(path.read_text())
    require(data.get('utc_offset_seconds') == 0, 'Reference not UTC')
    hourly = data['hourly']
    utc = pd.DatetimeIndex(pd.to_datetime(hourly['time'],errors='raise'))
    required = pd.date_range('2014-01-01','2014-12-31 23:00',freq='h')
    require(utc.equals(required),'Incorrect 2014 hourly UTC axis')
    x = pd.DataFrame({
        'T':pd.to_numeric(pd.Series(hourly['temperature_2m']),errors='coerce').to_numpy(),
        'Td':pd.to_numeric(pd.Series(hourly['dew_point_2m']),errors='coerce').to_numpy(),
    },index=utc+pd.Timedelta(hours=1))
    x = x.reindex(x.index.union(dates)).sort_index().interpolate(
        method='time',limit=1,limit_area='inside').reindex(dates)
    require(x[['T','Td']].notna().all().all(),f'2014 reference gap: {model}')
    return pd.Series(100*sat(x['Td'].to_numpy())/sat(x['T'].to_numpy()),index=dates)

def main(mode):
    if mode=='write':require(not OUT.exists(),f'Output already exists: {OUT}')
    if mode=='verify':require(OUT.is_dir(),f'No v5 directory: {OUT}')
    for p in (CSV,REF,V4):require(p.is_file(),f'Missing input: {p}')
    for year in range(2006,2025):
        require((V3/f'CH-Aws_DATM_{year}.nc').is_file(),f'Missing RH25A v3 year {year}')
    status=CSV.parent/'status.json'
    require(status.is_file() and json.loads(status.read_text()).get('candidate_sha256')==sha(CSV),
            'RH25A candidate source SHA mismatch')
    df=pd.read_csv(CSV,usecols=['time','TA_F','PA_F','VPD_F_SOURCE','VPD_F_QC','RH_IMPLIED_PCT'],low_memory=False)
    df['time']=pd.to_datetime(df['time'],errors='raise')
    expected=pd.date_range('2006-01-01','2024-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    require(pd.DatetimeIndex(df.time).equals(expected),'Wrong full 19yr noleap timeline')
    df['VPD_F_QC']=pd.to_numeric(df.VPD_F_QC,errors='coerce')
    sel=df.loc[(df.VPD_F_SOURCE=='EUF_F')&(df.VPD_F_QC==2)&(df.RH_IMPLIED_PCT<10)].copy().set_index('time').sort_index()
    require(len(sel)==77,'Expected 77 QC2 EUF_F RH<10 records')
    jan=pd.date_range('2006-01-14 14:30','2006-01-14 18:30',freq='30min')
    require(sel.index.isin(jan).sum()==9,'Expected nine Stage28 v4 rows')
    r=pd.read_csv(REF,low_memory=False)
    r['time']=pd.to_datetime(r['time_local_standard_UTCplus1'],errors='raise')
    require(r.time.is_unique,'Duplicate Stage20 reference events')
    r=r.set_index('time')
    for model,col in [('era5','era5_RH_pct'),('era5_land','era5_land_RH_pct')]:
        sel[model+'_RH_pct']=pd.to_numeric(r[col],errors='coerce').reindex(sel.index)
        idx=sel.index[sel.index.year==2014]
        sel.loc[idx,model+'_RH_pct']=reference_2014(model,idx).to_numpy()
    for col in ('era5_RH_pct','era5_land_RH_pct'):
        a=sel[col].to_numpy(float)
        require(np.isfinite(a).all()&((a>0)&(a<100)).all(),f'Invalid {col}')
    land=sel.era5_land_RH_pct.to_numpy(float)
    orig=sel.RH_IMPLIED_PCT.to_numpy(float)
    gap=np.abs(sel.era5_RH_pct.to_numpy(float)-land)
    print('ERA5/ERA5-Land disagreement >15 percentage points:',int((gap>15).sum()))
    print('ERA5-Land RH <= input RH:',int((land<=orig).sum()))
    # All-row wetter-air experiment is not appropriate if the proposed
    # replacement would dry any of these low-RH events even further.
    require(np.all(land>orig),'Some proposed ERA5-Land RH <= input RH: review those rows; no automatic edits')
    ea_pa=sat(sel.TA_F.to_numpy(float))*land  # hPa x percent -> Pa
    p_pa=sel.PA_F.to_numpy(float)*1000
    qnew=.622*ea_pa/(p_pa-.378*ea_pa)
    require(np.isfinite(qnew).all()&((qnew>0)&(qnew<0.08)).all(),'Invalid new specific humidity')
    sel['QBOT_v5_kgkg']=qnew
    sel['ERA_gap_pp']=gap
    sel['science_status']='EXPLORATORY_REANALYSIS_SENSITIVITY_NOT_OBSERVATION_VALIDATED'
    print('Candidate changes by year:')
    print(sel.groupby(sel.index.year).size().to_string())
    if mode=='audit':
        print('AUDIT ONLY: no forcing written and no Slurm jobs')
        return
    if mode=='verify':
        with Dataset(V4) as ds:q4=np.asarray(ds['QBOT'][:,0,0],dtype=np.float32)
        for year in range(2006,2025):
            f=OUT/f'CH-Aws_DATM_{year}.nc'
            original=V3/f.name
            require(f.is_file(),f'Missing v5 year {year}')
            subset=sel.loc[sel.index.year==year]
            if subset.empty:
                require(f.is_symlink() and f.resolve()==original.resolve(),f'{year}: expected v3 symlink')
                continue
            require(not f.is_symlink(),f'{year}: expected independent NetCDF')
            with Dataset(original) as old,Dataset(f) as new:
                t=new['time']
                axis=pd.DatetimeIndex([str(d)[:19] for d in num2date(t[:],t.units,calendar=getattr(t,'calendar','noleap'))])
                ix=axis.get_indexer(subset.index)
                require((ix>=0).all(),f'{year}: missing timestamps')
                require(set(old.variables)==set(new.variables),f'{year} variable inventory changed')
                for name in old.variables:
                    if name!='QBOT':require(np.ma.allequal(old[name][:],new[name][:]),f'{year} other variable changed: {name}')
                qa=np.asarray(old['QBOT'][:,0,0],dtype=np.float32)
                qb=np.asarray(new['QBOT'][:,0,0],dtype=np.float32)
                require(set(np.flatnonzero(qa!=qb))==set(ix),f'{year}: unexpected QBOT changes')
                require(np.allclose(qb[ix],subset.QBOT_v5_kgkg.to_numpy(float),rtol=0,atol=1e-8),
                        f'{year}: edited QBOT mismatch')
                if year==2006:
                    ji=axis.get_indexer(jan)
                    require(np.array_equal(qb[ji],q4[ji]),'Existing Stage28 nine values changed')
            print(f'VERIFIED {year}: {len(ix)} QBOT edits')
        print('VERIFY SUCCESS: 77 QBOT edits across 19-year overlay, remaining vars unchanged')
        return
    work=Path(tempfile.mkdtemp(prefix='.CH_Aws_stage29_',dir=ROOT))
    try:
        summary={}
        ledger=work/'stage29_77record_sensitivity_ledger.csv'
        sel.to_csv(ledger,float_format='%.12g')
        ledger_sha=sha(ledger)
        for year in range(2006,2025):
            filename=f'CH-Aws_DATM_{year}.nc'
            parent=V3/filename
            target=work/filename
            subset=sel.loc[sel.index.year==year]
            if subset.empty:
                target.symlink_to(parent)
                summary[str(year)]={'source':'v3_symlink','modified_vs_v3':0}
                continue
            base=V4 if year==2006 else parent
            shutil.copy2(base,target)
            with Dataset(parent) as old,Dataset(target,'r+') as nc:
                t=nc['time']
                axis=pd.DatetimeIndex([str(d)[:19] for d in num2date(t[:],t.units,calendar=getattr(t,'calendar','noleap'))])
                require(len(axis)==17520 and axis.is_unique,f'{year}: invalid time axis')
                ix=axis.get_indexer(subset.index)
                require((ix>=0).all(),f'{year}: missing timestamps')
                before=np.asarray(old['QBOT'][:,0,0],dtype=np.float32)
                tb=np.asarray(old['TBOT'][ix,0,0],dtype=float)
                ps=np.asarray(old['PSRF'][ix,0,0],dtype=float)
                rh=100*(before[ix]*ps/(.622+.378*before[ix]))/(100*sat(tb-273.15))
                require(np.allclose(rh,subset.RH_IMPLIED_PCT.to_numpy(float),rtol=0,atol=.25),
                        f'{year}: CSV-v3 humidity mismatch')
                q=np.asarray(nc['QBOT'][:,0,0],dtype=np.float32)
                proposal=subset.QBOT_v5_kgkg.to_numpy(dtype=np.float32)
                if year==2006:
                    nine=subset.index.isin(jan)
                    require(nine.sum()==9,'2006 Stage28 time count changed')
                    require(np.allclose(q[ix[nine]],proposal[nine],rtol=0,atol=1e-8),
                            'Stage28 v4 values differ from current reanalysis reference')
                    q[ix[~nine]]=proposal[~nine]  # preserve nine existing values bitwise
                else:
                    q[ix]=proposal
                nc['QBOT'][:,0,0]=q
                nc.setncattr('stage29_status','EXPLORATORY_REANALYSIS_SENSITIVITY_NOT_QC_APPROVED')
                nc.setncattr('stage29_ledger_path',str(OUT/ledger.name))
                nc.setncattr('stage29_ledger_sha256',ledger_sha)
                nc.setncattr('stage29_parent_v3_sha256',sha(parent))
                nc.setncattr('stage29_modified_QBOT_rows_vs_v3',int(len(ix)))
                nc.setncattr('stage29_note','Provenance follows Stage29 ledger; prior v3/v4 QBOT attrs refer to historical parents')
            with Dataset(parent) as old,Dataset(target) as new:
                require(set(old.variables)==set(new.variables),f'{year}: variable list differs')
                for name in old.variables:
                    if name!='QBOT':require(np.ma.allequal(old[name][:],new[name][:]),f'{year}: changed {name}')
                qb=np.asarray(new['QBOT'][:,0,0],dtype=np.float32)
                require(set(np.flatnonzero(before!=qb))==set(ix),f'{year}: unexpected QBOT edits')
                require(np.allclose(qb[ix],subset.QBOT_v5_kgkg.to_numpy(float),rtol=0,atol=1e-8),
                        f'{year}: edited humidity mismatch')
            summary[str(year)]={'source':'v4_2006_plus_remaining' if year==2006 else 'v3',
                                'modified_vs_v3':len(subset)}
            print(f'VERIFIED {year}: {len(subset)} changed QBOT values')
        require(sum(e['modified_vs_v3'] for e in summary.values())==77,'Incorrect total changes')
        manifest={'site':'CH-Aws','version':'STAGE29_FULL_77_QBOT_SENSITIVITY_V5',
                  'scientific_status':'UNVALIDATED_EXPLORATORY_DO_NOT_CLAIM_CORRECTION',
                  'changed_vs_RH25A_v3':77,'v4_nine_row_candidate_preserved':True,
                  '2014_refs':{m:sha(CACHE/f'{m}_2014.json') for m in ('era5','era5_land')},
                  'reference_stage20_sha256':sha(REF),'parent_csv_sha256':sha(CSV),
                  'stage29_ledger_sha256':ledger_sha,'by_year':summary,
                  'note':'Unchanged annual symlinks require original RH25A v3 directory. No model validation.'}
        (work/'stage29_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        os.rename(work,OUT)
        print('SUCCESS: independent Stage29 19-year forcing overlay:',OUT)
        print('77 QBOT edited rows across 7 annual files; 12 unchanged annual symlinks')
        print('No v3/v4 overwrite; no CIME/Slurm; model stability not established')
    finally:
        if work.exists():shutil.rmtree(work)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group()
    group.add_argument('--audit',action='store_true',help='Default read-only')
    group.add_argument('--verify',action='store_true',help='Verify existing v5')
    group.add_argument('--write',action='store_true',help='Build non-overwriting v5')
    p.add_argument('--acknowledge-reanalysis-uncertainty',action='store_true')
    a=p.parse_args()
    mode='write' if a.write else 'verify' if a.verify else 'audit'
    if mode=='write' and not a.acknowledge_reanalysis_uncertainty:
        p.error('--write requires --acknowledge-reanalysis-uncertainty')
    main(mode)

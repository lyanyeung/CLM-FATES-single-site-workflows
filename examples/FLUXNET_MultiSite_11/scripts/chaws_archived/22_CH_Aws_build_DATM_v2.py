#!/usr/bin/env python3
"""CH-Aws Stage22: non-overwriting v2 DATM from the verified Stage21 RH trial.

Only the 779 flagged QBOT time steps are replaced. Every other time/variable,
including dated ZBOT, is copied verbatim from the validated Stage15 NetCDF.
--audit is non-mutating, --write creates a NEW folder atomically, --verify
independently checks EVERY year against the source CSV and v1 NetCDF.
This is an exploratory reanalysis-based trial, not science QC approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np
import pandas as pd
from netCDF4 import Dataset

USER = 'ly3n24'
ROOT = Path('/iridisfs/scratch')/USER/'CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing'
OLD = ROOT/'datm_11_provisional_dynamic_zbot_v1'
NEW = ROOT/'datm_11_landrh21a_dynamic_zbot_v2'
TRIAL = ROOT/'merged_multisource_11_landrh21a'
PARENT = ROOT/'merged_multisource_11_landrh11a'
NAME = 'CH-Aws_multisource_HH_2006_2024_candidate.csv'
OLD_SHA = '130df2cd6c0bf9b89fc4895bca19145e1aca8bf0d4e5d7f48edb85df22035239'
NEW_SHA = '14c481cc7abd3ddeb9e1dabf615b4d694ce73b3dd0347d30dba257afeb479ed8'
POLICY = Path.home()/'FLUXNET_MultiSite_11/stage15_provisional_DATM/height_policy_v1.json'
POLICY_SHA = '4eff9273d6aa73bc71f4b6104470b9189fb3d5491ea2393698564720f6764068'
YEAR0, YEAR1 = 2006, 2024
VARS = ('TBOT','PSRF','FSDS','FLDS','WIND','PRECTmms','ZBOT')
QVAR = 'QBOT'
N_CHANGED = 779

def sha(path: Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as fd:
        for piece in iter(lambda:fd.read(1024*1024),b''):h.update(piece)
    return h.hexdigest()

def assert_that(cond, msg):
    if not cond:raise RuntimeError('STOP: '+msg)

def expected_times():
    t=pd.date_range('2006-01-01 00:00','2024-12-31 23:30',freq='30min')
    return t[~((t.month==2)&(t.day==29))]

def read_candidates():
    assert_that(POLICY.is_file() and sha(POLICY)==POLICY_SHA,'ZBOT height policy changed')
    for d,expected in ((PARENT,OLD_SHA),(TRIAL,NEW_SHA)):
        f=d/NAME; j=d/'status.json'
        assert_that(f.is_file() and j.is_file(),f'Missing Stage21 source/status: {d}')
        meta=json.loads(j.read_text())
        assert_that(sha(f)==expected and meta.get('candidate_sha256')==expected, f'CSV/status hash mismatch: {d}')
    sm=json.loads((TRIAL/'status.json').read_text())
    assert_that(sm.get('parent_sha256')==OLD_SHA and sm.get('changed_VPD_records')==N_CHANGED,
                'Stage21 provenance/count not as expected')
    usecols=['time','TA_F','PA_F','VPD_F','STAGE21_RH_TRIAL_FLAG',
             'RH_LAND_TRIAL_FLAG','VPD_F_SOURCE']
    df=pd.read_csv(TRIAL/NAME,usecols=usecols,low_memory=False)
    parent=pd.read_csv(PARENT/NAME,usecols=['time','TA_F','PA_F','VPD_F'],low_memory=False)
    t=expected_times()
    dtime=pd.DatetimeIndex(pd.to_datetime(df['time'],errors='raise'))
    assert_that(len(df)==len(parent)==len(t)==332880,'Wrong 19yr row count')
    assert_that(dtime.equals(t) and pd.DatetimeIndex(pd.to_datetime(parent['time'])).equals(t),
                'Old/new CSV time axis mismatch, expected NO_LEAP every 30 minutes')
    flags=df.STAGE21_RH_TRIAL_FLAG.astype('boolean').fillna(False).to_numpy(bool)
    original=df.RH_LAND_TRIAL_FLAG.astype('boolean').fillna(False).to_numpy(bool)
    assert_that(int(flags.sum())==N_CHANGED and int(original.sum())==559,'Stage11/21 flag counts unexpected')
    assert_that(not np.any(flags & original),'Stage21 must not overwrite Stage11 humidity edits')
    for key in ('TA_F','PA_F'):
        assert_that(np.array_equal(df[key].to_numpy(float),parent[key].to_numpy(float)),f'Unexpected {key} changes')
    # Permit only negligible CSV floating-point roundtrip differences.
    a = df.loc[~flags, 'VPD_F'].to_numpy(float)
    b = parent.loc[~flags, 'VPD_F'].to_numpy(float)
    delta = np.abs(a - b)

    assert_that(np.all(np.isfinite(delta)),
                'Non-finite VPD differences outside Stage21 flags')

    max_delta = float(delta.max())
    print('Unedited VPD: differing float values =',
          int(np.count_nonzero(delta)),
          'max absolute difference (hPa) =', max_delta)

    assert_that(max_delta <= 1e-10,
                f'Material VPD changes outside Stage21 flags: {max_delta} hPa')
    assert_that(np.all(df.loc[flags,'VPD_F_SOURCE'].astype(str).to_numpy()==
                       'ERA5_LAND_RH_AT_SITE_T_STAGE21_TRIAL'),'Revisions not tagged with Stage21 source')
    temp=df.TA_F.to_numpy(float)
    vp=df.VPD_F.to_numpy(float)
    p=df.PA_F.to_numpy(float)
    es=6.112*np.exp(np.clip(17.67*temp/(temp+243.5),-100,100))
    ea=es-vp
    q=.622*(ea*100)/(p*1000-.378*ea*100)
    rh=100*ea/es
    assert_that(np.all(np.isfinite(q)&(q>0)&(q<.08)&np.isfinite(rh)&(rh>0)&(rh<=100.05)),
                'New candidate contains invalid humidity')
    print(f'Source validated: {len(t)} half-hours, {int(flags.sum())} new edits, 559 prior edits preserved')
    print('New RH min/max:',float(rh.min()),float(rh.max()))
    return t,flags,q.astype('f4'),rh

def scan_old(t,flags,q):
    for year in range(YEAR0,YEAR1+1):
        f=OLD/f'CH-Aws_DATM_{year}.nc'
        assert_that(f.is_file(),f'Old DATM missing: {f}')
        ids=np.flatnonzero(t.year==year)
        assert_that(len(ids)==17520,f'Old DATM {year} record count wrong')
        with Dataset(f) as nc:
            assert_that(nc.getncattr('source_candidate_sha256')==OLD_SHA,f'{year} input v1 incorrect parent SHA')
            assert_that(nc.getncattr('zbot_height_policy_sha256')==POLICY_SHA,f'{year} old DATM ZBOT policy differs')
            assert_that(nc.variables['time'].calendar=='noleap',f'{year} time calendar not noleap')
            assert_that(len(nc.dimensions['time'])==17520,f'{year} time length differs')
            for name in (*VARS,QVAR):assert_that(name in nc.variables,f'{year}: missing {name}')
            oldq=np.asarray(nc[QVAR][:,0,0],dtype=np.float32)
        mask=flags[ids]
        qnew=q[ids]
        assert_that(np.allclose(oldq[~mask],qnew[~mask],rtol=0,atol=1e-8),
                    f'{year}: unedited QBOT disagrees with recalculated candidate')
        print(f'YEAR {year}: old DATM valid, changed RH trial rows={int(mask.sum())}')

def write_new(t,flags,q,rh):
    assert_that(not NEW.exists(),f'New output already exists; refusing overwrite: {NEW}')
    work=Path(tempfile.mkdtemp(prefix='.CH_Aws_DATM_v2_PARTIAL_',dir=ROOT))
    try:
        summary={}
        for year in range(YEAR0,YEAR1+1):
            ids=np.flatnonzero(t.year==year)
            mask=flags[ids]
            src=OLD/f'CH-Aws_DATM_{year}.nc'
            dst=work/src.name
            shutil.copy2(src,dst)
            with Dataset(dst,'r+') as nc:
                vals=np.asarray(nc[QVAR][:,0,0],dtype=np.float32)
                vals[mask]=q[ids][mask]
                nc[QVAR][:,0,0]=vals
                nc.setncattr('source_candidate',str(TRIAL/NAME))
                nc.setncattr('source_candidate_sha256',NEW_SHA)
                nc.setncattr('source_candidate_tag','landrh21a')
                nc.setncattr('provenance_status','EXPLORATORY_REANALYSIS_HUMIDITY_TRIAL_NOT_SCIENCE_APPROVED')
                nc.setncattr('humidity_warning',
                              '559 Stage11 RH edits plus 779 Stage21 QC2 EUF_F low-RH trial edits; modelled references, not observed')
                nc.setncattr('stage21_replaced_QBOT_records_in_year',int(mask.sum()))
                nc.setncattr('stage21_replaced_QBOT_records_total',N_CHANGED)
                nc.setncattr('stage22_parent_DATM_file',str(src))
                nc.setncattr('stage22_preservation_rule',
                              'Verbatim copy of DATM v1; only flagged QBOT time steps modified')
            summary[str(year)]=int(mask.sum())
        assert_that(sum(summary.values())==N_CHANGED,'Output manifest changed count unexpected')
        manifest={'site':'CH-Aws','stage':'STAGE22_DATM_V2','scientific_status':'TRIAL_ONLY',
                  'source_trial_sha256':NEW_SHA,'parent_candidate_sha256':OLD_SHA,
                  'height_policy_sha256':POLICY_SHA,'qbot_edits_total':N_CHANGED,
                  'qbot_edits_by_year':summary,'years':[YEAR0,YEAR1],
                  'reference_origin':'Stage21 ERA5-Land RH using local site temperature, not field observation'}
        (work/'stage22_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        verify_folder(work,t,flags,q)
        os.rename(work,NEW)
        print('NEW DATM V2:',NEW)
        print('19 annual NetCDFs; original v1 and source CSVs untouched.')
    finally:
        if work.exists():shutil.rmtree(work)

def verify_folder(folder,t,flags,q):
    assert_that(folder.is_dir(),'New DATM folder missing')
    assert_that((folder/'stage22_manifest.json').is_file(),'Missing stage22 manifest')
    m=json.loads((folder/'stage22_manifest.json').read_text())
    assert_that(m.get('source_trial_sha256')==NEW_SHA and m.get('qbot_edits_total')==N_CHANGED,
                'Stage22 manifest unexpected')
    count=0
    for year in range(YEAR0,YEAR1+1):
        a=OLD/f'CH-Aws_DATM_{year}.nc'
        b=folder/f'CH-Aws_DATM_{year}.nc'
        assert_that(a.is_file() and b.is_file(),f'{year}: missing v1/v2')
        ids=np.flatnonzero(t.year==year)
        mask=flags[ids]
        with Dataset(a) as old,Dataset(b) as new:
            assert_that(len(new.dimensions['time'])==17520,f'{year}: wrong timestep count')
            assert_that(new.getncattr('source_candidate_sha256')==NEW_SHA,f'{year}: wrong source sha')
            assert_that(new.getncattr('zbot_height_policy_sha256')==POLICY_SHA,f'{year}: wrong ZBOT policy')
            assert_that(int(new.getncattr('stage21_replaced_QBOT_records_in_year'))==int(mask.sum()),
                        f'{year}: wrong expected edits')
            assert_that(set(old.variables)==set(new.variables),f'{year}: v2 variables different')
            for name in old.variables:
                if name == QVAR:continue
                x=np.asarray(old[name][:]);y=np.asarray(new[name][:])
                assert_that(np.array_equal(x,y,equal_nan=True),f'{year}: other variable changed: {name}')
            oldq=np.asarray(old[QVAR][:,0,0],dtype=np.float32)
            newq=np.asarray(new[QVAR][:,0,0],dtype=np.float32)
            assert_that(np.array_equal(newq[~mask],oldq[~mask],equal_nan=True),
                        f'{year}: QBOT changed outside approved timestamps')
            assert_that(np.array_equal(newq[mask],q[ids][mask]),
                        f'{year}: new QBOT does not match selected CSV')
        count+=int(mask.sum())
        print(f'VERIFIED {year}: {int(mask.sum())} edits; all other values identical',flush=True)
    assert_that(count==N_CHANGED,f'Verified edit total {count} vs {N_CHANGED}')
    print(f'VERIFIED ALL 19 YEARS: {count} intended QBOT edits, zero other data edits')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--audit',action='store_true');m.add_argument('--write',action='store_true');m.add_argument('--verify',action='store_true')
    args=p.parse_args()
    t,flags,q,rh=read_candidates()
    scan_old(t,flags,q)
    if args.audit:
        print('AUDIT ONLY. No forcing file was changed.');return
    if args.write:
        assert_that(os.environ.get('ACK_PROVISIONAL_SCIENCE')=='YES',
                    'For experimental DATM v2 write, set ACK_PROVISIONAL_SCIENCE=YES')
        write_new(t,flags,q,rh)
    elif args.verify:
        verify_folder(NEW,t,flags,q)

if __name__=='__main__':main()

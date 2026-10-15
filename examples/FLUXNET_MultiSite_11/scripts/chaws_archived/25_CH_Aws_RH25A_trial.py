#!/usr/bin/env python3
"""CH-Aws stage25: EXTENDED HIGH-UNCERTAINTY humidity *trial*, not observation QC.

Select previously UNEDITED EUF_F QC=2 RH<10% records in 2006-2013 for
additional review IF BOTH ERA5/ERA5-Land estimate 20..100% RH,
ERA5-Land minus original >=20pp, and two reanalyses differ (15,20]pp.
The (15,20]pp bracket explicitly supersedes stage21's <=15pp screen;
this is an experiment to assess a numerical model failure, NOT proof
of meteorological truth. Never modify existing candidates or CIME cases.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing')
OLD=BASE/'merged_multisource_11_landrh21a'
NEW=BASE/'merged_multisource_11_landrh25a'
REVIEW=Path.home()/'FLUXNET_MultiSite_11/stage20_CH_Aws_RH_QC_expansion_audit/01_low_and_boundary_events_review.csv'
REPORT=Path.home()/'FLUXNET_MultiSite_11/stage25_CH_Aws_high_disagreement_trial'
FILENAME='CH-Aws_multisource_HH_2006_2024_candidate.csv'
PARENT_SHA='14c481cc7abd3ddeb9e1dabf615b4d694ce73b3dd0347d30dba257afeb479ed8'
STAGE11_SHA='130df2cd6c0bf9b89fc4895bca19145e1aca8bf0d4e5d7f48edb85df22035239'
FAIL_TIMES=pd.DatetimeIndex(['2006-01-12 03:30:00','2006-01-12 04:00:00'])

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for x in iter(lambda:f.read(4*1024*1024),b''):h.update(x)
    return h.hexdigest()

def check(ok,reason):
    if not ok:raise RuntimeError('STOP: '+reason)

def sat(x):
    x=np.asarray(x,dtype=float)
    return 6.112*np.exp(np.clip(17.67*x/(x+243.5),-100,100))

def prepare():
    p=OLD/FILENAME
    check(p.is_file() and (OLD/'status.json').is_file() and REVIEW.is_file(),'Missing Stage21 source or Stage20 review')
    m=json.loads((OLD/'status.json').read_text())
    check(sha(p)==PARENT_SHA and m.get('candidate_sha256')==PARENT_SHA and m.get('parent_sha256')==STAGE11_SHA,
          'Stage21 parent provenance SHA mismatch')
    df=pd.read_csv(p,low_memory=False)
    times=pd.DatetimeIndex(pd.to_datetime(df.time,errors='raise'))
    exp=pd.date_range('2006-01-01','2024-12-31 23:30',freq='30min')
    exp=exp[~((exp.month==2)&(exp.day==29))]
    check(len(df)==332880 and times.equals(exp),'19-year NO_LEAP halfhour dates changed')
    df.index=times
    check({'TA_F','VPD_F','PA_F','VPD_F_QC','VPD_F_SOURCE','RH_LAND_TRIAL_FLAG','STAGE21_RH_TRIAL_FLAG'}.issubset(df),
          'Stage21 columns missing')
    s11=df.RH_LAND_TRIAL_FLAG.astype('boolean').fillna(False).to_numpy(bool)
    s21=df.STAGE21_RH_TRIAL_FLAG.astype('boolean').fillna(False).to_numpy(bool)
    check(s11.sum()==559 and s21.sum()==779 and not np.any(s11&s21),'Earlier revisions count or overlap wrong')
    ref=pd.read_csv(REVIEW,parse_dates=['time_local_standard_UTCplus1']).set_index('time_local_standard_UTCplus1')
    check(len(ref)==1080 and not ref.index.has_duplicates and ref.index.isin(df.index).all(),
          'Unexpected Stage20 review')
    idx=df.index.get_indexer(ref.index)
    x=df.iloc[idx]
    rh=100*(sat(x.TA_F.to_numpy(float))-x.VPD_F.to_numpy(float))/sat(x.TA_F.to_numpy(float))
    orig=pd.to_numeric(ref.RH_input_pct,errors='coerce').to_numpy(float)
    untouched=~(s11[idx]|s21[idx])
    check(np.allclose(rh[untouched],orig[untouched],rtol=0,atol=0.0003),
          'Stage20 reviewed RH changed outside prior trial records')
    qc=pd.to_numeric(x.VPD_F_QC,errors='coerce').to_numpy(float)
    src=x.VPD_F_SOURCE.fillna('').astype(str).to_numpy()
    r5=pd.to_numeric(ref.era5_RH_pct,errors='coerce').to_numpy(float)
    rl=pd.to_numeric(ref.era5_land_RH_pct,errors='coerce').to_numpy(float)
    diff=np.abs(r5-rl)
    proposed=(untouched & (qc==2)&(src=='EUF_F') &
              (np.isfinite(rh)&(rh>=0)&(rh<10)) &
              (np.isfinite(r5)&np.isfinite(rl)&(r5>=20)&(r5<=100)&(rl>=20)&(rl<=100)) &
              (diff>15)&(diff<=20)&((rl-rh)>=20))
    proposed_idx=ref.index[proposed]
    check(len(proposed_idx)>0,'No additional high-disagreement candidates')
    for stamp in FAIL_TIMES:
        check(stamp in proposed_idx,f'Failure-window {stamp} must be explicitly selected')
    ledger=pd.DataFrame(index=proposed_idx)
    ledger.index.name='time_local_standard_UTCplus1'
    ledger['VPD_original_hPa']=x.VPD_F.to_numpy(float)[proposed]
    ledger['RH_before_pct']=rh[proposed]
    ledger['ERA5_RH_pct']=r5[proposed]
    ledger['ERA5_Land_RH_pct']=rl[proposed]
    ledger['ERA5_vs_Land_diff_pp']=diff[proposed]
    ta=x.TA_F.to_numpy(float)[proposed]
    p=x.PA_F.to_numpy(float)[proposed]*1000
    vnew=sat(ta)*(1-rl[proposed]/100.)
    ea=sat(ta)-vnew
    qnew=.622*(ea*100.)/(p-.378*ea*100.)
    check(np.all(np.isfinite(vnew)&(vnew>=0)&np.isfinite(qnew)&(qnew>0)&(qnew<.08)),
          'Invalid candidate new VPD/QBOT')
    ledger['VPD_new_hPa']=vnew
    ledger['QBOT_new_kgkg']=qnew
    ledger['decision']='HIGH_UNCERTAINTY_EXPANDED_SCREEN_NOT_OBSERVATION_VALIDATED'
    # Full-year QC: report unresolved low-RH events BEFORE writing
    allrh=100*(sat(df.TA_F.to_numpy(float))-df.VPD_F.to_numpy(float))/sat(df.TA_F.to_numpy(float))
    allqc=pd.to_numeric(df.VPD_F_QC,errors='coerce').to_numpy(float)
    remain=((allrh<1)&(allqc==2)&(~df.index.isin(proposed_idx)))
    print('STAGE25 REVIEW: parent=landrh21a sha=',PARENT_SHA,flush=True)
    print('Stage11 edits preserved:',int(s11.sum()),'Stage21 edits preserved:',int(s21.sum()),flush=True)
    print('NEW eligible high-disagreement 15..20pp proposals:',len(ledger),flush=True)
    print('New proposal years:',ledger.groupby(ledger.index.year).size().to_dict(),flush=True)
    print('Model failure records:',flush=True)
    print(ledger.loc[FAIL_TIMES].to_string(),flush=True)
    print('Unresolved RH<1% QC2 records, all 19 years, after this screen:',int(remain.sum()),flush=True)
    REPORT.mkdir(parents=True,exist_ok=True)
    ledger.to_csv(REPORT/'01_stage25_new_proposal_ledger.csv',float_format='%.12g')
    remain_df=pd.DataFrame({'time':df.index[remain].astype(str),'RH_pct':allrh[remain],
                            'source':df.VPD_F_SOURCE.to_numpy()[remain]})
    remain_df.to_csv(REPORT/'02_unresolved_input_RH_below_1pct.csv',index=False)
    return df,proposed_idx,ledger

def write(df,pos,ledger):
    check(not NEW.exists(),f'Output exists, refuse overwrite: {NEW}')
    work=Path(tempfile.mkdtemp(prefix='.stage25_CH_Aws_',dir=BASE))
    try:
        copy=df.copy()
        copy['STAGE25_RH_TRIAL_FLAG']=False
        copy['STAGE25_VPD_BEFORE_hPa']=np.nan
        copy['STAGE25_ERA5_RH_pct']=np.nan
        copy['STAGE25_ERA5_LAND_RH_pct']=np.nan
        copy['STAGE25_ERA_DIFF_pp']=np.nan
        copy.loc[pos,'STAGE25_RH_TRIAL_FLAG']=True
        copy.loc[pos,'STAGE25_VPD_BEFORE_hPa']=ledger.VPD_original_hPa.to_numpy(float)
        copy.loc[pos,'STAGE25_ERA5_RH_pct']=ledger.ERA5_RH_pct.to_numpy(float)
        copy.loc[pos,'STAGE25_ERA5_LAND_RH_pct']=ledger.ERA5_Land_RH_pct.to_numpy(float)
        copy.loc[pos,'STAGE25_ERA_DIFF_pp']=ledger.ERA5_vs_Land_diff_pp.to_numpy(float)
        copy.loc[pos,'VPD_F']=ledger.VPD_new_hPa.to_numpy(float)
        copy.loc[pos,'VPD_F_QC']=np.nan
        copy.loc[pos,'VPD_F_SOURCE']='ERA5_LAND_RH_AT_SITE_T_STAGE25_HIGH_DISAGREEMENT_TRIAL'
        copy.loc[pos,'PAIR_STATUS']='ERA5_LAND_STAGE25_HIGH_DISAGREEMENT_TRIAL'
        origV=df.VPD_F.to_numpy(float)
        revisedV=copy.VPD_F.to_numpy(float)
        untouched=~df.index.isin(pos)
        check(np.array_equal(origV[untouched],revisedV[untouched]),'Unexpected VPD edit outside proposals')
        es=sat(copy.TA_F.to_numpy(float));ea=es-revisedV
        rh=100*ea/es
        pa=copy.PA_F.to_numpy(float)*1000
        q=.622*(ea*100)/(pa-.378*ea*100)
        check(np.all(np.isfinite(q)&np.isfinite(rh)&(q>0)&(rh>0)&(rh<=100.05)),
              'All-year humidity invalid')
        if 'RH_IMPLIED_PCT' in copy:copy['RH_IMPLIED_PCT']=rh
        if 'QBOT_DIAGNOSTIC_KG_KG' in copy:copy['QBOT_DIAGNOSTIC_KG_KG']=q
        cp=work/FILENAME
        copy.to_csv(cp,index=False)
        verify=pd.read_csv(cp,usecols=['time','VPD_F'])
        check(len(verify)==len(copy) and np.allclose(verify.VPD_F.to_numpy(float),revisedV,rtol=0,atol=1e-10),
              'Output CSV round trip did not preserve VPD')
        m={'site':'CH-Aws','stage':'STAGE25_HIGH_DISAGREEMENT_REANALYSIS_HUMIDITY_TRIAL',
           'source_tag':'landrh21a','output_tag':'landrh25a','candidate_sha256':sha(cp),
           'parent_sha256':PARENT_SHA,'previous_stage11_edits':559,'previous_stage21_edits':779,
           'changed_VPD_records':len(pos),'scientific_status':'EXPLORATORY_NOT_APPROVED',
           'selection_rule':'QC2 EUF_F, 0<=RH<10%, both reanalyses RH 20..100%, ERA gap 15<diff<=20pp, ERA5-Land at least 20pp wetter',
           'limitations':['ERA5 and ERA5-Land are not independent observations','Terrain/ice-saturation uncertain',
                          'Change may or may not prevent internal model negative RH','2014-2024 have no corresponding reference']}
        (work/'status.json').write_text(json.dumps(m,indent=2)+'\n')
        ledger.to_csv(work/'CH-Aws_stage25_revision_ledger.csv',float_format='%.12g')
        os.rename(work,NEW)
        print('TRIAL WRITTEN:',NEW,flush=True)
        print('NEW CSV SHA256:',m['candidate_sha256'],flush=True)
        print('New VPD edits:',len(pos),'prior 779+559 preserved; no old files touched',flush=True)
    finally:
        if work.exists():shutil.rmtree(work)

def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--review',action='store_true')
    pa.add_argument('--write-trial',action='store_true')
    pa.add_argument('--acknowledge-reanalysis-uncertainty',action='store_true')
    a=pa.parse_args()
    check(not (a.review and a.write_trial),'Use --review or --write-trial')
    df,pos,ledger=prepare()
    if a.write_trial:
        check(a.acknowledge_reanalysis_uncertainty,'--write-trial requires --acknowledge-reanalysis-uncertainty')
        write(df,pos,ledger)
    else:print('REVIEW ONLY; no source CSV or NetCDF changed.',flush=True)
if __name__=='__main__':main()

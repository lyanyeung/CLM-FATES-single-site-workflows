#!/usr/bin/env python3
"""Stage21 CH-Aws: reference-guided *trial*, not certified meteorology.

Uses the already completed Stage20 event review and the immutable Stage11
candidate. Default --review produces a read-only-to-forcing proposal report.
--write-trial (with explicit acknowledgment) creates NEW landrh21a trial CSV,
status and audit ledger; never touches Stage11, DATM v1, any CIME case or Slurm.

Conservative PROPOSAL screen (not a universal physical RH rule):
  * original source is EUF_F, VPD QC=2, unmodified by Stage11;
  * reconstructed station RH in [0,10)%;
  * cached ERA5 and ERA5-Land both give RH in [20,100]%, agree <=15 pp;
  * ERA5-Land RH exceeds station RH by >=20 percentage points.
  * evidence available only for years 2006-2013.

No rows are changed simply for RH<10. Every change has a matching ledger row.
Even proposed changes can be wrong in high alpine terrain and MUST be reviewed.
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

SITE='CH-Aws'
BASE=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing')
REVIEW=Path.home()/'FLUXNET_MultiSite_11'/'stage20_CH_Aws_RH_QC_expansion_audit'
REPORT=Path.home()/'FLUXNET_MultiSite_11'/'stage21_CH_Aws_reference_guided_review'
NAME='CH-Aws_multisource_HH_2006_2024_candidate.csv'
PARENT_SHA='130df2cd6c0bf9b89fc4895bca19145e1aca8bf0d4e5d7f48edb85df22035239'
ORIGINAL_SHA='61374db9f1cbafcd22c0a4e74eb20d47d213faa59148cb597f284608ff89ccb3'
TAG='landrh21a'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for buf in iter(lambda:f.read(4*1024*1024),b''):h.update(buf)
    return h.hexdigest()


def sat(t):
    x=np.asarray(t,dtype=float)
    return 6.112*np.exp(np.clip(17.67*x/(x+243.5),-100,100))


def check_source(tag, expected):
    directory=BASE/f'merged_multisource_11_{tag}'
    path=directory/NAME
    status=directory/'status.json'
    if not path.is_file() or not status.is_file():
        raise RuntimeError(f'Missing source: {directory}')
    meta=json.loads(status.read_text())
    value=sha(path)
    if value!=expected or meta.get('candidate_sha256')!=expected or meta.get('site')!=SITE:
        raise RuntimeError(f'SHA256/status mismatch for {tag}; refusing to continue')
    return path


def check_time(df):
    expected=pd.date_range('2006-01-01 00:00','2024-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    ts=pd.DatetimeIndex(pd.to_datetime(df['time'],errors='raise'))
    if len(df)!=332880 or not ts.equals(expected):
        raise RuntimeError('Candidate does not match 2006-2024 NO_LEAP HH dates')
    return ts


def proposal():
    parent=check_source('landrh11a',PARENT_SHA)
    check_source('v07a',ORIGINAL_SHA)
    rfile=REVIEW/'01_low_and_boundary_events_review.csv'
    if not rfile.is_file():raise FileNotFoundError(f'Missing Stage20 review {rfile}')
    print('Verified Stage11 candidate and original SHA256; Stage20 review:',rfile,flush=True)
    df=pd.read_csv(parent,low_memory=False)
    ts=check_time(df)
    df.index=ts
    needed={'TA_F','VPD_F','PA_F','VPD_F_QC','VPD_F_SOURCE','PAIR_STATUS','RH_LAND_TRIAL_FLAG'}
    if not needed.issubset(df.columns):
        raise RuntimeError('Stage11 candidate missing '+str(needed-set(df.columns)))
    flagged=df['RH_LAND_TRIAL_FLAG'].astype('boolean').fillna(False).to_numpy(dtype=bool)
    if int(flagged.sum())!=559:raise RuntimeError('Stage11 must contain exactly 559 previous revisions')
    col='time_local_standard_UTCplus1'
    review=pd.read_csv(rfile,parse_dates=[col]).set_index(col)
    if review.index.has_duplicates or not review.index.isin(df.index).all():
        raise RuntimeError('Stage20 review contains duplicate/unknown event time')
    if len(review)!=1080:raise RuntimeError(f'Expected 1080 Stage20 review rows, found {len(review)}')
    cols={'RH_input_pct','official_VPD_QC','VPD_SOURCE','STAGE11_RECONSTRUCTED',
          'era5_RH_pct','era5_land_RH_pct','era5_vs_land_diff_pp','REF_AGREE_LE15PP'}
    if not cols.issubset(review.columns):raise RuntimeError('Stage20 review missing '+str(cols-set(review.columns)))
    # Cross-validate reviewed RH against full Stage11 candidate to prevent mismatch.
    sel=df.loc[review.index]
    old_rh=100.*(sat(sel.TA_F.to_numpy(float))-sel.VPD_F.to_numpy(float))/sat(sel.TA_F.to_numpy(float))
    from_review=review.RH_input_pct.to_numpy(float)
    if not np.allclose(old_rh,from_review,rtol=0,atol=0.0002):
        raise RuntimeError('Stage20 RH does not match Stage11 full candidate')
    qc=pd.to_numeric(sel.VPD_F_QC,errors='coerce').to_numpy(float)
    from_qc=pd.to_numeric(review.official_VPD_QC,errors='coerce').to_numpy(float)
    if not np.allclose(qc,from_qc,rtol=0,atol=1e-8,equal_nan=True):
        raise RuntimeError('Stage20 QC differs from Stage11 full source')
    source=sel.VPD_F_SOURCE.fillna('').astype(str).to_numpy()
    if not np.array_equal(source,review.VPD_SOURCE.fillna('').astype(str).to_numpy()):
        raise RuntimeError('Stage20 VPD_SOURCE differs from Stage11 full source')
    if not np.array_equal(flagged[df.index.get_indexer(review.index)],review.STAGE11_RECONSTRUCTED.astype(bool).to_numpy()):
        raise RuntimeError('Stage20 Stage11 flags inconsistent')
    r5=pd.to_numeric(review.era5_RH_pct,errors='coerce').to_numpy(float)
    rl=pd.to_numeric(review.era5_land_RH_pct,errors='coerce').to_numpy(float)
    gap=np.abs(r5-rl)
    stored_gap=pd.to_numeric(review.era5_vs_land_diff_pp,errors='coerce').to_numpy(float)
    if not np.allclose(gap,stored_gap,rtol=0,atol=0.0002,equal_nan=True):
        raise RuntimeError('Stage20 ERA5/ERA5-Land disagreement inconsistent')
    no_ref=~np.isfinite(r5)&~np.isfinite(rl)
    if np.any(~no_ref & (~np.isfinite(r5)|~np.isfinite(rl))):
        raise RuntimeError('Asymmetric ERA5/ERA5-Land reference availability')
    candidates=(~review.index.year.isin(range(2014,2025))) & (qc==2) & (source=='EUF_F') & \
        (~review.STAGE11_RECONSTRUCTED.astype(bool).to_numpy()) & \
        (np.isfinite(old_rh)&(old_rh>=0)&(old_rh<10)) & \
        (np.isfinite(r5)&np.isfinite(rl)&(r5>=20)&(r5<=100)&(rl>=20)&(rl<=100)) & \
        (gap<=15)&((rl-old_rh)>=20)
    review['STAGE21_TRIAL_PROPOSAL']=candidates
    review['STAGE21_EVIDENCE']=''
    review.loc[candidates,'STAGE21_EVIDENCE']='QC2_EUF_F_RH_LT10_REANALYSES_AGREE_AND_GE20PP_DRIER'
    pos=review.index[candidates]
    if len(pos)==0:raise RuntimeError('No Stage21 proposal rows; nothing to trial')
    # The actual model failure boundary must be included; prevents an unrelated trial.
    critical=pd.Timestamp('2006-01-10 04:30:00')
    if critical not in pos:raise RuntimeError('Critical CH-Aws 2006-01-10 04:30 record not eligible; stop')
    print('Stage20 suspects:',len(review),'   Stage21 evidence-screened proposals:',len(pos))
    print('References unavailable after 2013: these years remain UNCHANGED.')
    print('Existing 559 Stage11 revisions preserved; only new EUF_F QC2 low-RH proposals considered.')
    print('First 2006-01-10 proposals:')
    print(review.loc['2006-01-10 01:00':'2006-01-10 05:00',
        ['RH_input_pct','era5_RH_pct','era5_land_RH_pct','STAGE21_TRIAL_PROPOSAL']].to_string())
    return df,parent,review,candidates,pos


def make_reports(df,parent,review,candidates,pos,out):
    out.mkdir(parents=True,exist_ok=True)
    review.to_csv(out/'01_all_stage20_events_with_stage21_proposal.csv',float_format='%.9g')
    ledger=review.loc[pos].copy()
    x=df.loc[pos]
    rnew=ledger.era5_land_RH_pct.to_numpy(float)
    es=sat(x.TA_F.to_numpy(float))
    vnew=es*(1.-rnew/100.)
    ea=es-vnew
    p=x.PA_F.to_numpy(float)*1000
    qnew=.622*(ea*100.)/(p-.378*ea*100.)
    if not np.all(np.isfinite(vnew)&(vnew>=0)&(vnew<125)&
                  np.isfinite(qnew)&(qnew>0)&(qnew<.08)):
        raise RuntimeError('Proposed VPD / QBOT is not physically valid')
    ledger['VPD_before_hPa']=x.VPD_F.to_numpy(float)
    ledger['VPD_trial_hPa']=vnew
    ledger['QBOT_trial_kgkg']=qnew
    ledger['trial_RH_pct']=rnew
    ledger['decision']='TRIAL_CANDIDATE_ONLY_NOT_OBSERVATION_VALIDATED'
    ledger.to_csv(out/'02_stage21_new_revision_ledger.csv',float_format='%.10g')
    counts=ledger.groupby(ledger.index.year).size()
    y=pd.DataFrame({'year':counts.index.to_numpy(), 'proposed_changes':counts.to_numpy()})
    y.to_csv(out/'03_stage21_proposals_per_year.csv',index=False)
    report={'site':SITE,'stage':'STAGE21_LOW_POSITIVE_RH_REVIEW',
            'parent_sha256':PARENT_SHA,'stage20_review_sha256':sha(REVIEW/'01_low_and_boundary_events_review.csv'),
            'new_proposals':int(candidates.sum()),'existing_stage11_revisions':559,
            'stage20_suspect_rows':len(review),'reference_years':[2006,2013],
            'scientific_approval':'NOT_APPROVED_FOR_PRODUCTION',
            'selection_policy':'QC2 EUF_F, RH <10%, ERA5 & ERA5-Land 20..100%, agree <=15pp, ERA5-Land at least 20pp wetter',
            'known_limitations':['No valid winter tower RH references for Stage11 events',
                                 'ERA5 and ERA5-Land are dependent reanalyses',
                                 'High alpine terrain/ice vs water saturation and height mismatch',
                                 '2014-2024 no matching reference in Stage09 cache',
                                 'Model 2m RH can be negative despite nonnegative input RH']}
    (out/'status.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Report:',out)
    return ledger,report,vnew


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',action='store_true',help='Default: write Stage21 proposal reports; do not change forcing')
    parser.add_argument('--write-trial',action='store_true',help='Create NEW versioned experimental CH-Aws CSV after review')
    parser.add_argument('--acknowledge-reanalysis-uncertainty',action='store_true')
    a=parser.parse_args()
    if a.review and a.write_trial:parser.error('Choose one mode')
    df,parent,review,candidates,pos=proposal()
    report_dir=REPORT
    report_dir.mkdir(parents=True,exist_ok=True)
    ledger,report,vnew=make_reports(df,parent,review,candidates,pos,report_dir)
    if not a.write_trial:
        print('REVIEW ONLY COMPLETE. No site forcing, DATM, or CIME files modified.')
        return
    if not a.acknowledge_reanalysis_uncertainty:
        raise SystemExit('STOP: --write-trial needs --acknowledge-reanalysis-uncertainty; no forcing changed')
    dest=BASE/f'merged_multisource_11_{TAG}'
    if dest.exists():raise SystemExit(f'STOP: refuse overwrite existing {dest}')
    staged=Path(tempfile.mkdtemp(prefix='.stage21_',dir=BASE))
    try:
        trial=df.copy()
        trial['STAGE21_RH_TRIAL_FLAG']=False
        trial['VPD_BEFORE_STAGE21_hPa']=np.nan
        trial['VPD_STAGE21_ORIGINAL_QC']=np.nan
        trial['VPD_STAGE21_PREVIOUS_SOURCE']=''
        trial['STAGE21_ERA5_RH_pct']=np.nan
        trial['STAGE21_ERA5_LAND_RH_pct']=np.nan
        trial.loc[pos,'STAGE21_RH_TRIAL_FLAG']=True
        trial.loc[pos,'VPD_BEFORE_STAGE21_hPa']=df.loc[pos,'VPD_F'].to_numpy(float)
        trial.loc[pos,'VPD_STAGE21_ORIGINAL_QC']=df.loc[pos,'VPD_F_QC'].to_numpy(float)
        trial.loc[pos,'VPD_STAGE21_PREVIOUS_SOURCE']=df.loc[pos,'VPD_F_SOURCE'].to_numpy()
        trial.loc[pos,'STAGE21_ERA5_RH_pct']=ledger.era5_RH_pct.to_numpy(float)
        trial.loc[pos,'STAGE21_ERA5_LAND_RH_pct']=ledger.era5_land_RH_pct.to_numpy(float)
        trial.loc[pos,'VPD_F']=vnew
        trial.loc[pos,'VPD_F_QC']=np.nan
        trial.loc[pos,'VPD_F_SOURCE']='ERA5_LAND_RH_AT_SITE_T_STAGE21_TRIAL'
        trial.loc[pos,'PAIR_STATUS']='ERA5_LAND_STAGE21_RECONSTRUCTION_TRIAL'
        if int(trial.STAGE21_RH_TRIAL_FLAG.sum())!=len(pos):
            raise RuntimeError('Incorrect Stage21 flag count')
        keep=df.index.difference(pos)
        if not np.array_equal(trial.loc[keep,'VPD_F'].to_numpy(float),df.loc[keep,'VPD_F'].to_numpy(float)):
            raise RuntimeError('Unexpected VPD changes outside proposed timestamps')
        if not (trial.loc[keep,'VPD_F_SOURCE'].astype(str).to_numpy()==df.loc[keep,'VPD_F_SOURCE'].astype(str).to_numpy()).all():
            raise RuntimeError('Unexpected provenance changes outside proposed timestamps')
        t=trial.TA_F.to_numpy(float);vp=trial.VPD_F.to_numpy(float);press=trial.PA_F.to_numpy(float)
        vap=sat(t)-vp;rh=100*vap/sat(t)
        q=.622*(vap*100)/(press*1000-.378*vap*100)
        # Stage11 saved these full-record diagnostic columns. Keep them consistent
        # with the revised trial VPD rather than leaving stale old humidity values.
        if 'RH_IMPLIED_PCT' in trial.columns:
            trial['RH_IMPLIED_PCT']=rh
        if 'QBOT_DIAGNOSTIC_KG_KG' in trial.columns:
            trial['QBOT_DIAGNOSTIC_KG_KG']=q
        if not np.all(np.isfinite(q)&np.isfinite(rh)&(vap>0)&(rh>0)&(rh<=100.05)&(q>=0)&(q<.08)):
            raise RuntimeError('Complete candidate fails full humidity QC')
        path=staged/NAME
        trial.to_csv(path,index=False)
        chk=pd.read_csv(path,usecols=['time','TA_F','VPD_F','PA_F'],low_memory=False)
        check_time(chk)
        stored=chk.VPD_F.to_numpy(float)
        if not np.allclose(stored,vp,rtol=0,atol=1e-8):
            raise RuntimeError('CSV round trip changed VPD values')
        meta=dict(report)
        meta.update({'stage':'STAGE21_ERA5_LAND_LOW_RH_TRIAL',
                     'status':'TRIAL_CANDIDATE_SCIENCE_REVIEW_REQUIRED',
                     'parent_csv':str(parent),'parent_sha256':sha(parent),
                     'candidate_csv':str(dest/NAME),'candidate_sha256':sha(path),
                     'changed_VPD_records':len(pos),'source_tag':'landrh11a',
                     'output_tag':TAG})
        (staged/'status.json').write_text(json.dumps(meta,indent=2)+'\n')
        ledger.to_csv(staged/'CH-Aws_stage21_revision_ledger.csv',float_format='%.10g')
        os.rename(staged,dest)
        print('NEW EXPERIMENTAL TRIAL:',dest)
        print('CSV SHA256:',meta['candidate_sha256'])
        print('Only CH-Aws Stage21 candidate written; original / Stage11 / DATM / CIME untouched.')
        print('WARNING: Stage15 DATM script is PINNED to old Stage11 SHA; do not rerun it for this trial.')
    finally:
        if staged.exists():shutil.rmtree(staged)


if __name__=='__main__':main()

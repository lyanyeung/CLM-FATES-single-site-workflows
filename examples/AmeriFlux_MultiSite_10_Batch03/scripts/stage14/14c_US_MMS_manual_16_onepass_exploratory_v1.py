#!/usr/bin/env python3
"""US-MMS: isolated one-pass exploratory humidity scenario; NOT DATM approved.

16 missing hourly values: 6 March-2000 use companion ERA RH at retained T;
5 Sep-2014 missing included in whole 47-QC1 48h ERA-RH replacement;
5 cold QC2 gaps interpolate ice-relative RH between physically valid
selected-source anchors. Never touch original Stage12G or tower input.
"""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03')
OLD = ROOT/'science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f'
MAN = ROOT/'qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json'
AUD = ROOT/'reports/us_mms_16hour_onepass_manual_science_20261029T031440Z_b66bdf1c'
FN = 'US-MMS_STAGE12G_INCOMPLETE_NOLEAP.csv'
MARCH = '200003051700 200003061600 200003061700 200003061800 200003061900 200003062000'.split()
SEPT = '201409220700 201409220900 201409221000 201409230700 201409230800'.split()
COLD = '201502240700 201901301000 201901301100 201901301200 201901301300'.split()
GAPS = set(MARCH + SEPT + COLD)
FIELDS = 'time TBOT QBOT PSRF FSDS FLDS WIND PRECTmms TA_USE VPD_USE'.split()

def ensure(flag, message):
    if not bool(flag):
        raise RuntimeError('US-MMS STOP (no input changed): ' + message)

def digest(path):
    p = Path(path)
    ensure(p.is_file() and not p.is_symlink(), 'required pinned file '+str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def esw(t):
    t = np.asarray(t, float)
    return 6.112*np.exp(17.67*t/(t+243.5))

def esi(t):
    t = np.asarray(t, float)
    return 6.112*np.exp(22.46*t/(t+272.62))

def qcalc(e,p):
    return 0.622*(100*e)/(p-0.378*100*e)

def main():
    ensure(len(GAPS)==16 and 25*365*24==219000 and esi(-20)<esw(-20), 'internal self-test')
    ensure(pd.Series(['200001010000',None]).equals(pd.Series(['200001010000',None])) and
           pd.Series([1.,np.nan]).equals(pd.Series([1.,np.nan])),
           'mixed string/numeric no-mutation comparison regression')
    old_receipt = json.loads((OLD/'stage12g_research_only_sha_receipt.json').read_text())
    ensure(old_receipt['output_sha256'][FN]==digest(OLD/FN), 'Stage12G source SHA')
    ensure(old_receipt['Postv5_approved']==0, 'Stage12G model status changed')
    aud_receipt = json.loads((AUD/'US_MMS_readonly_source_science_SHA_receipt.json').read_text())
    audit = AUD/'US_MMS_16_missing_hour_manual_science_decisions.csv'
    ensure(aud_receipt['outputs_SHA256'][audit.name]==digest(audit), 'Stage14B signed audit SHA')
    manifest = json.loads(MAN.read_text())
    info = next(s for s in manifest['sites'] if s['site']=='US-MMS')
    ensure(int(info['native_minutes'])==60, 'native source must be hourly')
    for var in ('primary','era'):
        p = Path(info[var])
        ensure(manifest['input_sha256'][str(p.resolve())]==digest(p), 'original '+var+' SHA')
    source = pd.read_csv(info['primary'], usecols=['TIMESTAMP_START','TA_F_QC','VPD_F_QC'],
                         dtype={'TIMESTAMP_START':str}).set_index('TIMESTAMP_START')
    era = pd.read_csv(info['era'], usecols=['TIMESTAMP_START','TA_ERA','VPD_ERA'],
                      dtype={'TIMESTAMP_START':str}).set_index('TIMESTAMP_START')
    base = pd.read_csv(OLD/FN)
    ensure(len(base)==219000 and list(base.columns)==FIELDS, 'original 219000 schema')
    base.index = pd.to_datetime(base.time).dt.strftime('%Y%m%d%H%M')
    ensure(base.index.is_unique and set(base.index[base.VPD_USE.isna()])==GAPS and
           set(base.index[base.QBOT.isna()])==GAPS, 'exact original 16 gaps')
    trial = base.copy(deep=True)
    edits = []
    def put(k,v,method,details=None):
        ensure(k not in {z['native_key'] for z in edits}, 'duplicate patch '+k)
        t=float(base.at[k,'TA_USE']); p=float(base.at[k,'PSRF'])
        e=float(esw(t))-float(v); q=float(qcalc(e,p))
        ensure(np.isfinite([t,p,v,e,q]).all() and 50000<p<110000 and
               0<=v<float(esw(t)) and e>0 and 0<q<.08 and
               (t>=0 or e/float(esi(t))<=1.001), 'physical candidate '+k)
        row=dict(native_key=k,original_VPD=base.at[k,'VPD_USE'],
                 original_QBOT=base.at[k,'QBOT'],new_VPD=float(v),new_QBOT=q,
                 method=method,T_QC=int(source.at[k,'TA_F_QC']),
                 VPD_QC=int(source.at[k,'VPD_F_QC']),
                 RH_water_pct=100*e/float(esw(t)),
                 RH_ice_pct=100*e/float(esi(t)),
                 scenario_not_measured=True,scientific_approval=False)
        if details:row.update(details)
        edits.append(row)
        trial.at[k,'VPD_USE']=float(v);trial.at[k,'QBOT']=q
    def transfer(k,label):
        t=float(base.at[k,'TA_USE']); ta=float(era.at[k,'TA_ERA'])
        ve=float(era.at[k,'VPD_ERA']);rh=1-ve/float(esw(ta))
        ensure(np.isfinite([t,ta,rh]).all() and 0<rh<1,'paired ERA RH invalid '+k)
        v=float(esw(t)*(1-rh))
        put(k,v,label,dict(ERA_RH_pct=100*rh,tower_minus_ERA_T_C=t-ta))
    window = pd.date_range('2014-09-22','2014-09-23 23:00',freq='h').strftime('%Y%m%d%H%M')
    qcs=source.loc[window,'VPD_F_QC']
    ensure(len(window)==48 and int(qcs.eq(1).sum())==47 and int(qcs.eq(2).sum())==1 and
           int(qcs.eq(0).sum())==0 and
           set(base.loc[window].index[base.loc[window,'VPD_USE'].isna()])==set(SEPT),
           '2014 47-QC1 / 5 missing scope changed')
    for k in window:
        if int(qcs.loc[k])==1:
            ensure(int(source.at[k,'TA_F_QC']) in (0,1), '2014 source T QC unsupported '+k)
            transfer(k,'2014_48H_ALL_47_VPD_QC1_ERA_RH_SCENARIO')
    for k in MARCH:
        ensure(int(source.at[k,'TA_F_QC'])==1 and int(source.at[k,'VPD_F_QC'])==2,
               '2000 T QC1 VPD QC2 provenance '+k)
        transfer(k,'2000_6H_ERA_RH_T_QC1_HIGH_UNCERTAINTY')
    t=trial.TA_USE.to_numpy(float);p=trial.PSRF.to_numpy(float)
    v=trial.VPD_USE.to_numpy(float);q=trial.QBOT.to_numpy(float)
    e=esw(t)-v;rhi=e/esi(t)
    valid=(np.isfinite(rhi)&np.isfinite(q)&(e>0)&(rhi>0)&(rhi<=1.01)&
           np.isclose(q,qcalc(e,p),rtol=1e-5,atol=1e-8))
    indexes={k:i for i,k in enumerate(trial.index)}
    for episode in ([COLD[0]],COLD[1:]):
        a=indexes[episode[0]];b=indexes[episode[-1]]
        before=[i for i in range(max(0,a-48),a) if valid[i]]
        after=[i for i in range(b+1,min(len(trial),b+49)) if valid[i]]
        ensure(bool(before) and bool(after),'no two-sided existing source humidity '+episode[0])
        l=before[-1];r=after[0]
        start=pd.Timestamp(trial.iloc[l].time);end=pd.Timestamp(trial.iloc[r].time)
        ensure(pd.Timedelta(0)<end-start<=pd.Timedelta(hours=97),'source anchors too distant')
        for k in episode:
            ensure(int(source.at[k,'VPD_F_QC'])==2 and base.at[k,'TA_USE']<0,
                   'cold source QC2/tower T changed '+k)
            f=float((pd.Timestamp(base.at[k,'time'])-start)/(end-start))
            rr=float(rhi[l]*(1-f)+rhi[r]*f)
            rh=float(np.clip(rr,0.01,0.98))
            ev=float(esi(base.at[k,'TA_USE'])*rh)
            vv=float(esw(base.at[k,'TA_USE'])-ev)
            put(k,vv,'COLD_INTERPOLATED_ICE_RH_LOW_CONFIDENCE',
                dict(left_key=trial.index[l],right_key=trial.index[r],
                     left_VPD_QC=int(source.at[trial.index[l],'VPD_F_QC']),
                     right_VPD_QC=int(source.at[trial.index[r],'VPD_F_QC']),
                     RHice_unbounded_pct=100*rr,RHice_bounded=abs(rr-rh)>1e-12))
    log=pd.DataFrame(edits)
    mask=base.index.isin(set(log.native_key))
    ensure(len(log)==58 and log.native_key.nunique()==58 and
           int(log.original_VPD.isna().sum())==16 and
           int(log.original_VPD.notna().sum())==42, 'exact 58 edit scope drift')
    for col in FIELDS:
        # pandas Series.equals handles both the string time column and numeric NaNs.
        # np.array_equal(..., equal_nan=True) raises TypeError for string/object arrays.
        allowed=np.ones(len(base),dtype=bool) if col not in ('VPD_USE','QBOT') else ~mask
        ensure(base.loc[allowed,col].equals(trial.loc[allowed,col]),
               'off-target selected field changed '+col)
    ensure(not trial[FIELDS[1:]].isna().any().any(), 'numerical gaps remain')
    t=trial.TA_USE.to_numpy(float); p=trial.PSRF.to_numpy(float)
    v=trial.VPD_USE.to_numpy(float); q=trial.QBOT.to_numpy(float)
    e=esw(t)-v
    physical=(np.isfinite(e)&np.isfinite(q)&(e>0)&(v>=0)&(v<esw(t))&
              np.isclose(q,qcalc(e,p),atol=1e-8,rtol=1e-5))
    ensure(bool(physical.all()),'whole 219000 site water/QBOT closure')
    out=ROOT/'science_trials'/('US_MMS_MANUAL_16H_ISOLATED_SENSITIVITY_'+
         datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    files={'US_MMS_219000_HR_NUMERIC_SCENARIO_NOT_DATM.csv':trial,
           'US_MMS_58_EDITS_MANUAL_PROVENANCE.csv':log}
    hashes={}
    for filename,df in files.items():
        df.to_csv(out/filename,index=False)
        hashes[filename]=digest(out/filename)
    # Preserve the original 10-column CSV format (no accidental index column).
    reread=pd.read_csv(out/'US_MMS_219000_HR_NUMERIC_SCENARIO_NOT_DATM.csv')
    ensure(len(reread)==219000 and list(reread.columns)==FIELDS and
           not reread[FIELDS[1:]].isna().any().any(),
           'serialized output column/row/NaN consistency')
    (out/'NOT_APPROVED_FOR_DATM').write_text('Exploratory humidity; not independently measured or production approved. No Slurm.\n')
    hashes['NOT_APPROVED_FOR_DATM']=digest(out/'NOT_APPROVED_FOR_DATM')
    summary=dict(site='US-MMS',native_hourly_rows=219000,old_missing=16,new_missing=0,
                 old_finite_QC1_changed=42,QC1_2014_replaced=47,total_changed=58,
                 selected_parent_sha256=digest(OLD/FN),output_sha256=hashes,
                 method_validated=False,DATM=False,Postv5=False,Slurm=False)
    (out/'US_MMS_SHA_receipt.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('US-MMS ACTUAL 16 ORIGINAL GAPS RECONSTRUCTED (EXPLORATORY ONLY)')
    print(log[log.native_key.isin(GAPS)][['native_key','method','new_VPD','new_QBOT']].to_string(index=False))
    print('US-MMS 16/16 NUMERICALLY FILLED; 47 ORIGINAL QC1 RECONSTRUCTED; ALL 219000 WATER/QBOT PASS')
    print('US-MMS ISOLATED NEW RESEARCH DIR:',out)
    print('US-MMS SUCCESS — ORIGINAL SOURCE/SHADOW UNCHANGED, NO SLURM')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('US-MMS FAIL CLOSED:',exc,file=sys.stderr)
        raise

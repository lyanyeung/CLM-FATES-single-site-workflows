#!/usr/bin/env python3
"""Recover four sealed ERA5-Land sensitivities after the verified US-Me2 clock.

Read original sources, the executed Stage14a receipt and the sealed Stage10b
table. Recompute candidate physics from the recorded grid T/dewpoint and verify
the unchanged external product hash. This does not decode NetCDF again, edit
forcing, approve four replacements, or validate terrain/height transfers.
--check writes nothing; --run creates only a new isolated review report.
"""
import argparse
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import sys
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03')
CLOCK=ROOT/'reports/stage14a_US_Me2_documented_clock_20261026T193531Z_985d2919/clock_verification.json'
RAW=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Me2/forcing/raw/AMF_US-Me2_FLUXNET_FULLSET_2002-2022_4-6')
PRIMARY='AMF_US-Me2_FLUXNET_FULLSET_HH_2002-2022_4-6.csv'
ERA='AMF_US-Me2_FLUXNET_ERA5_HH_1981-2023_4-6.csv'
PINS={PRIMARY:'5b29b04da37960a1640c19b75fc2a8ffbffd703ada89ba6c36689d86f834ae3e',
      ERA:'ad0ce6a1d934bb965d939375c1c8588ed643f3513c3ac7e31afed6ca993d3115'}
ROWS=[227899,227900,227901,227902]
STARTS=pd.date_range('2014-12-31 20:30',periods=4,freq='30min')


def sha(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Missing or symlink file: '+str(path))
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def water(t):return 6.112*np.exp(17.67*np.asarray(t)/(243.5+np.asarray(t)))
def ice(t):return 6.112*np.exp(22.46*np.asarray(t)/(272.62+np.asarray(t)))
def qbot(e,p):return .622*np.asarray(e)*100/(np.asarray(p)-.378*np.asarray(e)*100)


def utc_midpoints(starts):return pd.DatetimeIndex(starts)+pd.Timedelta(hours=8,minutes=15)


def candidates(t,p,gt,gd):
    t,p,gt,gd=map(lambda a:np.asarray(a,dtype=float),(t,p,gt,gd))
    grh=100*water(gd)/water(gt);es=water(t)
    ea_relative=es*grh/100;ea_absolute=water(gd)
    rec=pd.DataFrame({'tower_T_C':t,'retained_PA_F_Pa':p,'grid_T_C':gt,'grid_dewpoint_C':gd,
        'grid_RH_water_pct':grh,'tower_minus_grid_T_C':t-gt})
    valid=(np.isfinite(t)&np.isfinite(p)&np.isfinite(gt)&np.isfinite(gd)&
           (t>=-80)&(t<=65)&(p>=50000)&(p<=110000)&(gd<=gt+.1)&(grh>0)&(grh<=100.05))
    for name,e in [('relative',ea_relative),('absolute',ea_absolute)]:
        v=es-e;rh=100*e/es;q=qbot(e,p)
        rec[name+'_VPD_hPa']=v;rec[name+'_RH_water_pct']=rh;rec[name+'_QBOT_kgkg']=q
        rec[name+'_RH_ice_pct']=100*e/np.where(t<0,ice(t),es)
        rec[name+'_water_physical_pass']=valid&np.isfinite(q)&(v>=0)&(v<=125)&(rh>0)&(rh<=100.05)&(q>0)&(q<=.08)
        rec[name+'_ice_supersaturation_caution']=(t<0)&(rec[name+'_RH_ice_pct'].to_numpy()>100)
    rec['tower_grid_T_absdiff_gt5C_caution']=np.abs(t-gt)>5
    rec['humidity_repair_approved']=False
    return rec


def read_context(path,primary):
    wanted=['TIMESTAMP_START','TIMESTAMP_END','TA_F','TA_F_QC','TA_F_MDS','TA_F_MDS_QC',
            'VPD_F','VPD_F_QC','VPD_F_MDS','VPD_F_MDS_QC','TA_ERA','VPD_ERA','PA_F','PA_F_QC','PA_ERA','RH']
    # Select by names; primary FULLSET and paired ERA have different columns.
    frame=pd.read_csv(path,usecols=lambda c:c in wanted)
    frame.insert(0,'source_csv_row',np.arange(len(frame))+2)
    frame['local_start']=pd.to_datetime(frame.TIMESTAMP_START.astype(str),format='%Y%m%d%H%M')
    lo=STARTS[0]-pd.Timedelta(hours=24);hi=STARTS[-1]+pd.Timedelta(hours=24)
    frame=frame.loc[frame.local_start.between(lo,hi)].copy()
    frame['utc_midpoint']=utc_midpoints(frame.local_start)
    if primary:
        for col in wanted[2:]:
            if col in frame:frame.loc[frame[col]<=-9990,col]=np.nan
        e=water(frame.TA_F)-frame.VPD_F
        frame['raw_RH_from_T_VPD_pct']=100*e/water(frame.TA_F)
        frame['raw_QBOT_kgkg']=qbot(e,frame.PA_F*1000)
        frame['raw_humidity_physical']=(e>0)&(frame.raw_RH_from_T_VPD_pct<=100.05)&np.isfinite(frame.raw_QBOT_kgkg)&(frame.raw_QBOT_kgkg>0)&(frame.raw_QBOT_kgkg<=.08)
        frame['adjacent_T_change_C']=frame.TA_F.diff()
    return frame


def boundary_review(context,review):
    d=context.set_index('source_csv_row');replacement=dict(zip(ROWS,review.relative_VPD_hPa))
    physical=dict(zip(ROWS,review.relative_water_physical_pass))
    edges=[]
    for left in range(ROWS[0]-1,ROWS[-1]+1):
        right=left+1;a=d.loc[left];b=d.loc[right]
        va=replacement.get(left,a.VPD_F);vb=replacement.get(right,b.VPD_F)
        left_ok=bool(physical[left]) if left in replacement else bool(a.raw_humidity_physical)
        right_ok=bool(physical[right]) if right in replacement else bool(b.raw_humidity_physical)
        both=left_ok and right_ok
        bad_candidate=(left in physical and not physical[left]) or (right in physical and not physical[right])
        delta=float(vb-va)
        edges.append({'left_source_csv_row':left,'right_source_csv_row':right,
            'left_local_start':str(a.local_start),'right_local_start':str(b.local_start),
            'four_only_hypothetical_VPD_change_hPa':delta,'absolute_change_le4hPa':bool(abs(delta)<=4),
            'both_endpoints_raw_or_candidate_physical':both,
            'boundary_status':('HOLD_CANDIDATE_WATER_PHYSICS_FAIL' if bad_candidate else
                'REVIEW_NUMERIC_EDGE_ONLY' if both else 'HOLD_ADJACENT_RAW_HUMIDITY_INVALID'),
            'production_continuity_validated':False})
    return pd.DataFrame(edges)


def analyze(args):
    inputs={}
    for name,expected in PINS.items():
        actual=sha(args.raw_dir/name)
        if actual!=expected:raise ValueError('Original source SHA differs: '+name)
        inputs[str(args.raw_dir/name)]=actual
    clock=json.loads(args.clock_report.read_text());inputs[str(args.clock_report)]=sha(args.clock_report)
    if (clock['status']!='CLUSTER_SOURCE_AND_FOUR_CLOCK_HOLDS_VERIFIED' or
        clock['UTC_OFFSET_hours']!=-8 or clock['daylight_saving'] is not False or
        [r['source_csv_row'] for r in clock['legacy_events']]!=ROWS):raise ValueError('Executed Stage14a scope differs')
    for row,start in zip(clock['legacy_events'],STARTS):
        if pd.Timestamp(row['local_start'])!=start or pd.Timestamp(row['utc_midpoint'])!=utc_midpoints([start])[0].tz_localize('UTC'):
            raise ValueError('Clock event timestamp differs')
    folders=[args.stage10b] if args.stage10b else sorted(ROOT.glob('reports/stage10b_external_humidity_*'))
    if len(folders)!=1:raise ValueError('Specify exact --stage10b sealed report; found '+str(len(folders)))
    folder=folders[0];receipt_path=folder/'provenance_and_science_hold.json';receipt=json.loads(receipt_path.read_text())
    inputs[str(receipt_path)]=sha(receipt_path)
    for name,expected in receipt['output_SHA256'].items():
        if Path(name).name!=name:raise ValueError('Unsafe output receipt filename')
        actual=sha(folder/name)
        if actual!=expected:raise ValueError('Stage10b sealed output SHA mismatch: '+name)
        inputs[str(folder/name)]=actual
    history=pd.read_csv(folder/'humidity_external_sensitivity_1924.csv')
    if len(history)!=1924:raise ValueError('Stage10b scope differs from 1924 events')
    selected=history.loc[history.site=='US-Me2'].sort_values('source_csv_row').copy()
    if list(selected.source_csv_row)!=ROWS:raise ValueError('Expected exactly four original Me2 events')
    if not pd.DatetimeIndex(pd.to_datetime(selected.time)).equals(STARTS):raise ValueError('Historical original local times differ')
    if not selected.clock_offset_hours_hypothesis.eq(-8).all():raise ValueError('Historical tested offset differs')
    if not pd.DatetimeIndex(pd.to_datetime(selected.utc_midpoint_hypothesis)).equals(utc_midpoints(STARTS)):
        raise ValueError('Historical UTC midpoint differs from documented clock')
    for _,row in selected.iterrows():
        path=Path(row.external_file);expected=str(row.external_sha256)
        if path.parent!=ROOT/'external_evidence/era5land_timeseries/US-Me2/2014':raise ValueError('External product directory differs')
        if receipt['external_product_SHA256'].get('US-Me2:2014')!=expected:raise ValueError('External product receipt differs')
        if str(path) not in inputs:
            actual=sha(path)
            if actual!=expected:raise ValueError('External product SHA changed')
            inputs[str(path)]=actual
    context=read_context(args.raw_dir/PRIMARY,True)
    companion=read_context(args.raw_dir/ERA,False)
    raw=context.set_index('source_csv_row').loc[ROWS].copy()
    if not raw.TA_F_QC.eq(0).all() or not raw.VPD_F_QC.eq(1).all():raise ValueError('Expected measured TA / MDS VPD scope changed')
    if raw.RH.notna().any():raise ValueError('Original RH now available; review measured source first')
    for col,hist in [('TA_F','TA_before_fallback_C'),('PA_F','PA_before_fallback_kPa')]:
        if not np.allclose(raw[col],selected[hist],rtol=0,atol=1e-10):raise ValueError('Retained T/P differs from original source')
    review=candidates(raw.TA_F.to_numpy(),raw.PA_F.to_numpy()*1000,selected.grid_temperature_C.to_numpy(),selected.grid_dewpoint_C.to_numpy())
    for prefix in ['relative','absolute']:
        for dest,old in [('VPD_hPa','vpd_at_tower_T_hPa'),('QBOT_kgkg','qbot_at_tower_P_kgkg')]:
            if not np.allclose(review[prefix+'_'+dest],selected[prefix+'_'+old],rtol=0,atol=1e-9):raise ValueError('Recalculated candidate differs from sealed Stage10b')
    review.insert(0,'source_csv_row',ROWS);review.insert(1,'local_start',list(STARTS));review.insert(2,'utc_midpoint',list(utc_midpoints(STARTS)))
    review['raw_VPD_F_hPa']=raw.VPD_F.to_numpy();review['raw_RH_from_T_VPD_pct']=raw.raw_RH_from_T_VPD_pct.to_numpy()
    review['raw_TA_F_QC']=raw.TA_F_QC.to_numpy();review['raw_VPD_F_QC']=raw.VPD_F_QC.to_numpy();review['raw_PA_F_QC']=raw.PA_F_QC.to_numpy()
    review['paired_ERA_RH_at_ERA_T_pct']=100*(1-raw.VPD_ERA.to_numpy()/water(raw.TA_ERA.to_numpy()))
    return review,context,companion,boundary_review(context,review),inputs


def self_test():
    assert str(utc_midpoints([STARTS[0]])[0])=='2015-01-01 04:45:00'
    t=np.array([-14.463,-14.7,-14.817,-14.727]);v=np.array([2.202,2.214,2.226,2.237])
    assert (100*(1-v/water(t))<0).all()
    c=candidates(t,np.full(4,86681),t+1,t-3)
    assert c.relative_water_physical_pass.all() and not c.humidity_repair_approved.any()
    bad=candidates([-15],[86681],[-14],[-10]);assert not bad.relative_water_physical_pass.any()
    print('ME2 FOUR HUMIDITY SELF-TEST PASS: cross-year midpoint, negative raw RH, candidate closure, invalid dewpoint rejected; zero approvals')


def main():
    p=argparse.ArgumentParser(description=__doc__);mode=p.add_mutually_exclusive_group(required=True)
    for name in ['self-test','check','run']:mode.add_argument('--'+name,action='store_true')
    p.add_argument('--raw-dir',type=Path,default=RAW);p.add_argument('--clock-report',type=Path,default=CLOCK)
    p.add_argument('--stage10b',type=Path);p.add_argument('--report-root',type=Path,default=ROOT/'reports')
    args=p.parse_args()
    if args.self_test:self_test();return
    review,context,companion,edges,inputs=analyze(args)
    print('\nFOUR SOURCE/CANDIDATE ROWS\n'+review.to_string(index=False),flush=True)
    print('\nFOUR-ONLY HYPOTHETICAL BOUNDARIES\n'+edges.to_string(index=False),flush=True)
    anchors=context.loc[context.TA_F_QC.eq(0)&context.VPD_F_QC.eq(0)&context.raw_humidity_physical]
    print('\nRAW QC0 T+VPD ANCHORS WITHIN 24H\n'+anchors[['source_csv_row','local_start','TA_F','VPD_F','RH']].to_string(index=False),flush=True)
    print('\nRAW TEMPERATURE STEPS >5C/30MIN\n'+context.loc[context.adjacent_T_change_C.abs()>5,['source_csv_row','local_start','TA_F','TA_F_QC','adjacent_T_change_C']].to_string(index=False),flush=True)
    if args.run:
        out=args.report_root/('stage14b_US_Me2_four_humidity_REVIEW_ONLY_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]);out.mkdir(parents=True,exist_ok=False)
        tables={'four_candidates_REVIEW_ONLY.csv':review,'native_48h_source_context.csv':context,'paired_ERA_48h_context.csv':companion,'four_only_hypothetical_boundaries.csv':edges}
        for name,frame in tables.items():frame.to_csv(out/name,index=False)
        receipt={'status':'FOUR_NUMERIC_SENSITIVITIES_REVIEW_ONLY','inputs_SHA256':inputs,'source_rows':ROWS,
          'grid_evidence':'Recorded Stage10b grid T/dewpoint recomputed; external product bytes verified, not decoded again.',
          'external_evidence_year_label':2014,'event_UTC_date':'2015-01-01','hourly_padding_coverage':'Historical Stage09b/09f request extends through 2015-01-03; no new download requested.',
          'humidity_repair_approvals':0,'forcing_changes':0,'model_jobs_submitted':0,'production_continuity_validated':False,
          'output_SHA256':{name:sha(out/name) for name in tables}}
        (out/'review_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print('ME2 FOUR HUMIDITY REPORT',out,flush=True)
    print('ME2 FOUR HUMIDITY SUMMARY rows=4 clock_documented=TRUE forcing_changes=0 approvals=0 jobs=0',flush=True)


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError) as exc:print('ME2 FOUR HUMIDITY STOP:',str(exc),file=sys.stderr);sys.exit(2)

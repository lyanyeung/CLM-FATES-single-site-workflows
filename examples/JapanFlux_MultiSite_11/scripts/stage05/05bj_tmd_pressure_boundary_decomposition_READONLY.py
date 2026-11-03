#!/usr/bin/env python3
"""Decompose selected Tmd PA left jumps using already-pasted hourly context.

Grid midpoints are approximate interpolations from six-decimal reported hourly
values, not tower measurements. No downloads, ZIP reads, forcing or approvals.
"""
import argparse
import csv
import hashlib
import math
import sys
from datetime import datetime,timedelta
from pathlib import Path

INPUTS={'hourly':'abe5fa975129cc6d57f20ecae81d70cc451150755d073307a25864685fb13f3c',
        'selected':'409e0e9df7155be57bbdc0d18b7c7397b011328292a500806315737296fbd9a6',
        'ledger':'35f9f064983bec73c16fac44a8259093ffa7ec36f23caa4b28c93e44113677f2'}
EVENTS=['200508120230','201112170630','202204090230']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(s):return datetime.strptime(s,'%Y%m%d%H%M')
def interp(hourly,instant):
    hour=instant.replace(minute=0,second=0,microsecond=0)
    fraction=(instant-hour).total_seconds()/3600
    return hourly[hour]*(1-fraction)+hourly[hour+timedelta(hours=1)]*fraction
def parts(left,grid_left,grid_first,median,selected):
    if not all(math.isfinite(x) for x in (left,grid_left,grid_first,median,selected)):raise ValueError('nonfinite')
    grid_change=grid_first-grid_left
    residual_change=median-(left-grid_left)
    total=selected-left
    if abs((grid_change+residual_change)-total)>1e-6:raise ValueError('decomposition mismatch')
    return grid_change,residual_change,total
def selftest():
    hours={datetime(2022,1,1,0):100,datetime(2022,1,1,1):98}
    assert interp(hours,datetime(2022,1,1,0,15))==99.5
    a,b,c=parts(99.232,99.88556125,99.87348375,-0.77563375,99.09785)
    assert abs(a+0.0120775)<1e-7 and abs(b+0.1220725)<1e-7 and abs(c+0.13415)<1e-7
    try:parts(1,1,1,0,2)
    except ValueError:pass
    else:raise AssertionError('arithmetic mismatch accepted')
    print('STAGE05BJ SELF-TEST PASS; APPROXIMATE GRID CONTEXT; ALL HOLD')
def parse_hourly(path):
    hours={};section=''
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('FILE '):section=line.split()[-1].rsplit('/',1)[-1]
        elif section=='stage05au_Tmd_20050811_9h_three_variable_ERA5Land_hourly_context.tsv' and line.startswith('2005-'):
            p=line.split();hours[datetime.strptime(p[0],'%Y-%m-%dT%H:%MZ')]=float(p[1])
        elif section=='stage05av_remaining_4_CDS_days_26_model_hour_variable_context.tsv' and line.startswith('JP-Tmd'):
            p=line.split()
            if p[3]=='sp':hours[datetime.strptime(p[2],'%Y-%m-%dT%H:%MZ')]=float(p[5])
    if len(hours)!=27 or not all(math.isfinite(v) for v in hours.values()):raise ValueError('hourly context scope')
    return hours
def read(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def run(hourly_path,selected_path,ledger_path):
    paths={'hourly':hourly_path,'selected':selected_path,'ledger':ledger_path}
    if any(sha(p)!=INPUTS[n] for n,p in paths.items()):raise ValueError('input SHA256 mismatch')
    hourly=parse_hourly(hourly_path);selected=read(selected_path);ledger=read(ledger_path)
    w=csv.writer(sys.stdout,delimiter='\t',lineterminator='\n')
    w.writerow(['Tmd_PA_group_start','left_source_QC2_kPa','left_grid_interp_kPa','first_grid_context_kPa',
                'median_QC2_minus_grid_kPa','left_QC2_minus_grid_kPa','grid_change_kPa',
                'residual_transition_kPa','first_selected_minus_left_kPa','status'])
    for event in EVENTS:
        a=[r for r in selected if r['site']=='JP-Tmd' and r['variable']=='PA' and r['native_start']==event]
        b=[r for r in ledger if r['site']=='JP-Tmd' and r['variable']=='PA' and r['native_start']==event]
        if len(a)!=1 or len(b)!=1 or a[0]['science_status']!='HOLD_NO_APPROVED_REPLACEMENT':raise ValueError('scope/HOLD')
        r=a[0];start=t(event);left=float(b[0]['left_QC2_F']);grid0=interp(hourly,start-timedelta(minutes=30)-timedelta(hours=9)+timedelta(minutes=15))
        grid1=float(r['grid_context']);approx1=interp(hourly,start-timedelta(hours=9)+timedelta(minutes=15))
        if abs(grid1-approx1)>1e-6:raise ValueError('existing grid does not match reported hourly interpolation')
        median=float(r['qc2_background_median_source_minus_grid']);value=float(r['selected_grid_plus_QC2_median_NOT_APPROVED'])
        dg,dr,total=parts(left,grid0,grid1,median,value)
        w.writerow([event,left,grid0,grid1,median,left-grid0,dg,dr,total,'DIAGNOSTIC_ONLY_ALL_HOLD'])
    if any(sha(p)!=INPUTS[n] for n,p in paths.items()):raise ValueError('input changed')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--hourly-paste',type=Path);p.add_argument('--selected',type=Path);p.add_argument('--ba-ledger',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if any(x is None for x in (a.hourly_paste,a.selected,a.ba_ledger)):p.error('three inputs required')
    run(a.hourly_paste,a.selected,a.ba_ledger)
if __name__=='__main__':main()

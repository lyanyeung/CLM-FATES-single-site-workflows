#!/usr/bin/env python3
"""Fetch at most three NEW ERA5-Land days for non-event Tmd QC0 controls.

Requires --submit for network; only fresh diagnostic directory is written.
Does not repeat 45 anomaly comparisons, modify source/forcing or approve values.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SAMPLE_SHA='1eafeb78c609aee5dbe3673473d5d916fb1fda6e81c84aca00f3f4c8d6b3f23b'
SELECTED_SHA='bd36ee5d5f8297f4edd8a5c08562473e2110fe6da6354dbaaf0754aaa5ad434f'
GROUP_SHA='ed5597796982bafd86a253f670870e90ebabb67212706b0f185d6ee147e7cd61'
HELPER_SHA='14909c294dea5ed17a9e0f3981a9ca2900b2ee8698dcf45902588fb0179f23cc'
DATASET='reanalysis-era5-land-timeseries';SITE='JP-Tmd';OFFSETS=(510.,540.,570.,141.523147*4)
SPECS={'TA':('200508120230','200508120330',1375,'t2m','2m_temperature'),
       'LW_IN':('200508120200','200508120230',69,'strd','surface_thermal_radiation_downwards')}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def checked(p,expected):
    if p.is_symlink() or not p.is_file() or sha(p)!=expected:raise ValueError('missing/symlink/SHA mismatch '+str(p))
def stamp(s):return datetime.strptime(s,'%Y%m%d%H%M')
def table(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f,delimiter='\t');fields=r.fieldnames or []
        if not fields or len(fields)!=len(set(fields)):raise ValueError('invalid TSV header')
        return list(r)
def valid_clock_support(native,day):
    for offset in OFFSETS:
        start=native-timedelta(minutes=offset)
        if start<day or start+timedelta(minutes=30)>day+timedelta(hours=23):return False
    return True
def choose_days(samples):
    """Predeclared: max n, earliest tie; only timestamp/QC, never values."""
    buckets=defaultdict(list)
    for var,entries in samples.items():
        start,end,_,_,_=SPECS[var];event=stamp(start);event_end=stamp(end)
        for t,value in entries:
            utc=t-timedelta(hours=9);day=utc.replace(hour=0,minute=0,second=0,microsecond=0)
            if t<=event_end+timedelta(hours=24) or not valid_clock_support(t,day):continue
            phase='near' if t<=event_end+timedelta(days=7) else 'later'
            buckets[(var,phase,day)].append((t,value))
    selected=[]
    for var,phase in [('TA','near'),('TA','later'),('LW_IN','later')]:
        minimum=16 if var=='TA' else 4
        options=[(day,values) for (v,p,day),values in buckets.items() if v==var and p==phase and len(values)>=minimum]
        if not options:raise ValueError('no >='+str(minimum)+' eligible QC0 controls for '+var+' '+phase+'; no CDS requests submitted')
        day,values=min(options,key=lambda item:(-len(item[1]),item[0]))
        selected.append((var,phase,day,values))
    return selected
def selftest():
    day=datetime(2005,8,13);t=datetime(2005,8,13,10)
    assert valid_clock_support(t,day) and not valid_clock_support(day+timedelta(hours=9),day)
    src={'TA':[(datetime(2005,8,13,12)+timedelta(minutes=30*i),20.) for i in range(16)]+
              [(datetime(2005,8,22,12)+timedelta(minutes=30*i),20.) for i in range(16)],
         'LW_IN':[(datetime(2005,9,10,12)+timedelta(minutes=30*i),300.) for i in range(16)]}
    groups=choose_days(src);assert len(groups)==3 and groups[0][1]=='near' and groups[2][0]=='LW_IN'
    assert hashlib.sha256(b'abc').hexdigest()=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    print('STAGE05BM SELF-TEST PASS; NON-EVENT CONTROLS ONLY; ALL HOLD')
def get_helper(path):
    checked(path,HELPER_SHA);spec=importlib.util.spec_from_file_location('az_ref',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def inputs(a):
    for p,h in ((a.samples,SAMPLE_SHA),(a.selected,SELECTED_SHA),(a.groups,GROUP_SHA),(a.helper,HELPER_SHA)):checked(p,h)
    samples=defaultdict(list);seen=set()
    for r in table(a.samples):
        if r['site']!=SITE or r['variable'] not in SPECS:raise ValueError('unexpected QC0 sample')
        var=r['variable'];s=stamp(r['native']);start,end,count,_,_=SPECS[var]
        k=(var,s)
        if k in seen or r['group_start']!=start or r['status']!='HOLD_NO_APPROVAL' or r['role']!='MEASURED_SOURCE_OTHER_TIME_NOT_EVENT_TRUTH':raise ValueError('QC0 key/provenance')
        seen.add(k);value=float(r['source_measured_F_QC0'])
        if not math.isfinite(value) or not (stamp(start)-timedelta(days=30)<=s<=stamp(end)+timedelta(days=30)):raise ValueError('sample outside verified window')
        if not ((-70<=value<=65) if var=='TA' else (70<=value<=650)):raise ValueError('sample range')
        samples[var].append((s,value))
    if any(len(samples[v])!=spec[2] for v,spec in SPECS.items()):raise ValueError('QC0 population mismatch')
    selected=table(a.selected);offsets={}
    if len(selected)!=45:raise ValueError('selected field population')
    for var,(start,_,_,_,_) in SPECS.items():
        vals=[r for r in selected if r['site']==SITE and r['variable']==var and r['native_start']==start]
        if len(vals)!=1 or vals[0]['status']!='HOLD_NO_APPROVED_REPLACEMENT' or vals[0]['method']!='GRID_PLUS_SAME_RELEASE_QC2_MEDIAN':raise ValueError('selected method/HOLD')
        offsets[(var,540.)]=float(vals[0]['qc2_background_median'])
    rows=table(a.groups)
    if len(rows)!=38:raise ValueError('AZ group scope')
    for var,(start,_,_,_,_) in SPECS.items():
        for offset in OFFSETS:
            x=[r for r in rows if r['site']==SITE and r['variable']==var and r['native_start']==start and abs(float(r['offset_minutes'])-offset)<1e-5]
            if len(x)!=1 or x[0]['scientific_status']!='HOLD_NO_APPROVAL_GRID_ELEVATION_UNVERIFIED' or int(x[0]['qc2_paired_count'])<1:raise ValueError('AZ group median/HOLD')
            value=float(x[0]['qc2_source_minus_grid_median'])
            if not math.isfinite(value):raise ValueError('invalid median')
            if offset==540 and abs(value-offsets[(var,540.)])>1e-8:raise ValueError('selected median mismatch')
            offsets[(var,offset)]=value
    return samples,offsets
def get_request(day,variables):
    return {'variable':sorted(variables),'date':day.strftime('%Y-%m-%d')+'/'+day.strftime('%Y-%m-%d'),
            'data_format':'csv','location':{'latitude':42.735911,'longitude':141.523147}}
def write_tsv(path,rows):
    if not rows:raise ValueError('empty output')
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def run(a,fetch=None):
    samples,offsets=inputs(a);helper=get_helper(a.helper);choices=choose_days(samples)
    vars_by_day=defaultdict(set)
    for var,phase,day,rows in choices:vars_by_day[day].add(var)
    if len(vars_by_day)>3 or any(day.strftime('%Y%m%d')=='20050811' for day in vars_by_day):raise ValueError('control request count/date scope')
    base=Path.home()/'japanflux_stage05bm'
    if base.is_symlink() or (base.exists() and not base.is_dir()) or a.out.parent.resolve()!=base.resolve() or a.out.exists() or a.out.is_symlink():raise ValueError('fresh ~/japanflux_stage05bm child required')
    plan=[{'variable':v,'phase':p,'utc_day':d.strftime('%Y-%m-%d'),'qc0_samples':len(r),'selection':'MOST_QC0_TIMESTAMPS_EARLIEST_TIE_NO_VALUE_FITTING'} for v,p,d,r in choices]
    requests={day:get_request(day,{SPECS[var][4] for var in vv}) for day,vv in vars_by_day.items()}
    print('STAGE05BM PREDEFINED NON-EVENT CONTROL PLAN',json.dumps(plan),flush=True)
    if not a.submit:
        print('PREFLIGHT ONLY; NO CDS REQUEST; ALL HOLD');return
    if fetch is None:
        if not (Path.home()/'.cdsapirc').is_file():raise ValueError('missing CDS configuration')
        import cdsapi
        client=cdsapi.Client()
        def fetch(req,path):client.retrieve(DATASET,req).download(str(path))
    base.mkdir(exist_ok=True);a.out.mkdir()
    with (a.out/'plan_HOLD.json').open('x',encoding='utf-8') as f:json.dump({'plan':plan,'requests':[requests[d] for d in sorted(requests)],'status':'ALL_HOLD_NO_APPROVAL'},f,indent=2);f.write('\n')
    grids={};metadata=[]
    for day in sorted(vars_by_day):
        req=requests[day];label=day.strftime('%Y%m%d');partial=a.out/('CDS_Tmd_'+label+'.zip.partial');final=a.out/('CDS_Tmd_'+label+'.zip')
        if partial.exists() or final.exists() or partial.is_symlink() or final.is_symlink():raise ValueError('output collision')
        print('CDS_NEW_CONTROL_DAY',label,'VARIABLES',','.join(req['variable']),flush=True)
        fetch(req,partial)
        expected=tuple(SPECS[v][3] for v in sorted(vars_by_day[day]))
        grid,members,coords=helper.parse_cds(partial.read_bytes(),SITE,label,expected,(42.7,141.5))
        partial.rename(final);grids[day]=grid
        metadata.append({'utc_day':label,'variables':list(expected),'request':req,'sha256':sha(final),'grid':coords,'members':members})
    comparisons=[];grouped=defaultdict(list)
    for var,phase,day,points in choices:
        for native,tower in points:
            for offset in OFFSETS:
                grid,support,matching=helper.reference(grids[day],var,native,offset)
                if grid is None:raise ValueError('control lacks matching support')
                estimate=grid+offsets[(var,offset)];err=estimate-tower
                r={'site':SITE,'variable':var,'phase':phase,'native':native.strftime('%Y%m%d%H%M'),
                   'UTC_day':day.strftime('%Y%m%d'),'offset_minutes':offset,'source_QC0':tower,
                   'grid_context':grid,'event_QC2_median':offsets[(var,offset)],'grid_plus_event_median':estimate,
                   'prediction_minus_QC0':err,'support_UTC':support,'matching':matching,
                   'status':'CONTROL_OTHER_TIME_HOLD_NO_APPROVAL'}
                comparisons.append(r);grouped[(var,phase,day,offset)].append(err)
    summary=[]
    for (var,phase,day,offset),err in sorted(grouped.items()):
        ordered=sorted(abs(x) for x in err)
        summary.append({'variable':var,'phase':phase,'UTC_day':day.strftime('%Y%m%d'),'offset_minutes':offset,'n':len(err),
            'mean_prediction_minus_QC0':statistics.mean(err),'median_prediction_minus_QC0':statistics.median(err),
            'mean_absolute_error':statistics.mean(ordered),'p95_abs_error_descriptive':ordered[round((len(ordered)-1)*.95)],
            'status':'DESCRIPTIVE_NOT_EVENT_VALIDATION_HOLD'})
    for p,h in ((a.samples,SAMPLE_SHA),(a.selected,SELECTED_SHA),(a.groups,GROUP_SHA),(a.helper,HELPER_SHA)):checked(p,h)
    write_tsv(a.out/'qc0_control_pairs_HOLD.tsv',comparisons);write_tsv(a.out/'qc0_control_summary_HOLD.tsv',summary)
    report={'status':'NON_EVENT_QC0_CONTROLS_ALL_45_HOLD','approved_replacements':0,'selected_method_unchanged':True,
        'control_plan':plan,'new_CDS_request_count':len(metadata),'new_CDS_sources':metadata,
        'original_45_reference_comparisons_repeated':False,'original_zip_forcing_pft_soil_model_slurm_modified':False,
        'clock_warning':'four diagnostic offsets; publisher archive README solar versus ICOS local-standard conflict remains',
        'limits':'QC0 at later times is not anomaly truth; site/grid differences; temporal autocorrelation; no acceptance threshold',
        'output_sha256':{n:sha(a.out/n) for n in ('qc0_control_pairs_HOLD.tsv','qc0_control_summary_HOLD.tsv')}}
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print('STAGE05BM NON-EVENT QC0 CONTROLS COMPLETE; ALL 45 HOLD; ZERO APPROVED');print('OUTPUT',a.out)
    print(json.dumps(report,indent=2));print('CONTROL_SUMMARY_TSV')
    with (a.out/'qc0_control_summary_HOLD.tsv').open(encoding='utf-8') as f:print(f.read(),end='')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true');p.add_argument('--submit',action='store_true')
    for x in ('samples','selected','groups','helper','out'):p.add_argument('--'+x,type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(getattr(a,x) is None for x in ('samples','selected','groups','helper','out')):p.error('all inputs and fresh output required')
    run(a)
if __name__=='__main__':main()

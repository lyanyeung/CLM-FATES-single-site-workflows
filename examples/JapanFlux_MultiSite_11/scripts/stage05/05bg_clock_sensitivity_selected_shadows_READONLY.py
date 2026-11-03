#!/usr/bin/env python3
"""Recalculate selected grid+QC2-median shadows for saved clock scenarios.

Only reads hash-pinned operator-pasted Stage05AZ output and local Stage05BE
selected ledger. No source ZIP or network. All scenarios remain HOLD.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PASTE_SHA='bd96cc5f0d80fe440c2db3540a8492d75c2641b8ee7bf95b810765f64925a26c'
SELECTED_SHA='409e0e9df7155be57bbdc0d18b7c7397b011328292a500806315737296fbd9a6'
LONGITUDE={'JP-Tef':142.107122,'JP-Tmd':141.523147}
STEP=timedelta(minutes=30)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp(s):return datetime.strptime(s,'%Y%m%d%H%M')
def finite(s):
    v=float(s)
    if not math.isfinite(v) or v<=-9990:raise ValueError('invalid value')
    return v
def label(site,minutes):
    if abs(minutes-510)<1e-7:return 'UTC_PLUS_08_30_SENSITIVITY'
    if abs(minutes-540)<1e-7:return 'UTC_PLUS_09_00_HYPOTHESIS'
    if abs(minutes-570)<1e-7:return 'UTC_PLUS_09_30_SENSITIVITY'
    if abs(minutes-LONGITUDE[site]*4)<1e-5:return 'LONGITUDE_MEAN_SOLAR_DIAGNOSTIC_NOT_PROVEN'
    raise ValueError('unexpected offset')
def selftest():
    assert label('JP-Tmd',540)=='UTC_PLUS_09_00_HYPOTHESIS'
    assert label('JP-Tef',142.107122*4)=='LONGITUDE_MEAN_SOLAR_DIAGNOSTIC_NOT_PROVEN'
    assert statistics.median([1,3,2])==2
    try:label('JP-Tef',500)
    except ValueError:pass
    else:raise AssertionError('unsupported clock accepted')
    print('STAGE05BG SELF-TEST PASS; CLOCK SENSITIVITY ONLY; ALL HOLD')

def run(paste,selected,out):
    if sha(paste)!=PASTE_SHA or sha(selected)!=SELECTED_SHA:raise ValueError('input SHA256 mismatch')
    with selected.open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    targets={}
    for r in rows:
        k=(r['site'],r['variable'],stamp(r['native_start']))
        if k in targets or r['science_status']!='HOLD_NO_APPROVED_REPLACEMENT':raise ValueError('selected key/HOLD')
        targets[k]=r
    if len(targets)!=45:raise ValueError('selected scope mismatch')
    flags=sorted(k for k in targets if k[0] in LONGITUDE)
    if len(flags)!=18:raise ValueError('solar-site scope mismatch')
    groups=[]
    for k in flags:
        if groups and groups[-1][-1][:2]==k[:2] and k[2]-groups[-1][-1][2]==STEP:groups[-1].append(k)
        else:groups.append([k])
    if len(groups)!=7:raise ValueError('solar-site group count')
    groupkey={k:(g[0][0],g[0][1],g[0][2]) for g in groups for k in g}
    sections=defaultdict(list);section=None
    for line in paste.read_text(encoding='utf-8').splitlines():
        if line.startswith('FILE '):section=line.split()[-1].rsplit('/',1)[-1]
        elif section and line.startswith('JP-'):sections[section].append(line.split())
    if len(sections['candidate_hourly_context_HOLD.tsv'])!=99 or len(sections['background_pairs_READONLY.tsv'])!=1936:
        raise ValueError('pasted table coverage mismatch')
    backgrounds=defaultdict(list);seen=set()
    for p in sections['background_pairs_READONLY.tsv']:
        if p[0] not in LONGITUDE:continue
        g=(p[0],p[1],stamp(p[2]));offset=float(p[3]);scenario=label(p[0],offset);t=stamp(p[5])
        if p[7]!='2' or not p[-1].endswith('QC2_SAME_RELEASE_ERA_DERIVED'):
            raise ValueError('unexpected background source')
        unique=(g,scenario,t)
        if unique in seen:raise ValueError('duplicate background')
        seen.add(unique);source=finite(p[6]);grid=finite(p[8]);delta=float(p[9])
        if not math.isfinite(delta) or abs(source-grid-delta)>1e-6:raise ValueError('background arithmetic')
        backgrounds[(g,scenario)].append(delta)
    candidates={}
    for p in sections['candidate_hourly_context_HOLD.tsv']:
        if p[0] not in LONGITUDE:continue
        k=(p[0],p[1],stamp(p[2]));scenario=label(p[0],float(p[3]))
        if k not in groupkey or (k,scenario) in candidates or 'HOLD_NO_APPROVED_REPLACEMENT' not in p:
            raise ValueError('candidate key/HOLD')
        matching=[i for i,x in enumerate(p) if 'HOUR_END_MEAN_WEIGHTED_OVERLAP_APPROX' in x or 'INSTANT_INTERPOLATED_TO_MIDPOINT_APPROX' in x]
        if len(matching)!=1 or abs(finite(p[matching[0]+1])-finite(targets[k]['original_F']))>1e-6:
            raise ValueError('original F or matching marker differs')
        g=groupkey[k];data=backgrounds[(g,scenario)]
        if not data:raise ValueError('missing paired background')
        median=statistics.median(data);grid=finite(p[6]);value=grid+median
        if not math.isfinite(value):raise ValueError('invalid candidate')
        candidates[(k,scenario)]={'selected':value,'median':median,'n':len(data),'grid':grid}
    scenarios=('UTC_PLUS_08_30_SENSITIVITY','UTC_PLUS_09_00_HYPOTHESIS','UTC_PLUS_09_30_SENSITIVITY','LONGITUDE_MEAN_SOLAR_DIAGNOSTIC_NOT_PROVEN')
    if len(candidates)!=72 or any((k,s) not in candidates for k in flags for s in scenarios):raise ValueError('scenario coverage mismatch')
    result=[]
    for k in flags:
        base=candidates[(k,scenarios[1])]['selected']
        if abs(base-finite(targets[k]['selected_grid_plus_QC2_median_NOT_APPROVED']))>1e-6:
            raise ValueError('UTC9 candidate differs from chosen 05BE value')
        r={'site':k[0],'variable':k[1],'native_start':k[2].strftime('%Y%m%d%H%M')}
        for s in scenarios:
            x=candidates[(k,s)];r[s+'_value']=x['selected'];r[s+'_delta_vs_UTC9']=x['selected']-base
            r[s+'_background_n']=x['n'];r[s+'_background_median']=x['median']
        vals=[candidates[(k,s)]['selected'] for s in scenarios]
        r['four_scenario_spread_not_uncertainty']=max(vals)-min(vals)
        r['science_status']='HOLD_NO_APPROVED_REPLACEMENT';result.append(r)
    summary=[]
    for g in groups:
        matching=[r for r in result if (r['site'],r['variable'],stamp(r['native_start'])) in g]
        summary.append({'site':g[0][0],'variable':g[0][1],'group_start':g[0][2].strftime('%Y%m%d%H%M'),
            'fields':len(g),'max_four_scenario_spread':max(r['four_scenario_spread_not_uncertainty'] for r in matching),
            'max_abs_mean_solar_minus_UTC9':max(abs(r['LONGITUDE_MEAN_SOLAR_DIAGNOSTIC_NOT_PROVEN_delta_vs_UTC9']) for r in matching),
            'status':'HOLD_CLOCK_UNRESOLVED'})
    if sha(paste)!=PASTE_SHA or sha(selected)!=SELECTED_SHA:raise ValueError('input changed')
    if out.parent.name!='japanflux_stage05bg' or out.parent.is_symlink() or out.exists() or out.is_symlink():
        raise ValueError('output must be a fresh child of japanflux_stage05bg')
    out.mkdir(parents=True)
    files=[('clock_scenarios_18_fields_HOLD.tsv',result),('clock_scenarios_7_groups_HOLD.tsv',summary)]
    for name,data in files:
        with (out/name).open('x',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=data[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(data)
    meta={'status':'CLOCK_SENSITIVITY_ALL_HOLD','fields':18,'groups':7,'scenarios_per_field':4,'approved_values':0,
          'input_paste_sha256':PASTE_SHA,'input_selected_sha256':SELECTED_SHA,
          'interpretation':'time shift and recalibrated same-source QC2 background; NOT bounds, validation, or proof of actual clock',
          'outputs_sha256':{n:sha(out/n) for n,_ in files},'source_zip_or_forcing_modified':False}
    with (out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(meta,f,indent=2);f.write('\n')
    print('STAGE05BG 18 FIELDS, 7 GROUPS, FOUR CLOCK SCENARIOS; ALL HOLD; ZERO APPROVED')
    print('OUTPUT',out)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--az-paste',type=Path);p.add_argument('--selected',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(x is None for x in (a.az_paste,a.selected,a.out)):p.error('all inputs and fresh output required')
    run(a.az_paste,a.selected,a.out)
if __name__=='__main__':main()

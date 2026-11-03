#!/usr/bin/env python3
"""Prepare the user's selected grid-plus-QC2-median method as HOLD shadows.

Inputs are locally exported, hash-pinned derived evidence; this does not inspect
IRIDIS source ZIPs. Creates only a fresh shadow audit directory, never forcing.
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

EXPECTED = {
    'preview': '81eaab3abff605991fe3fe1321eabea740279b8c09f629ce2aa664670953d8a7',
    'alternatives': '67547a7cce5aaf10b776e44c2b4e683bf742f3bb0ea3306034a9dbc43b2d021c',
    'ba_ledger': '35f9f064983bec73c16fac44a8259093ffa7ec36f23caa4b28c93e44113677f2',
}
COUNTS = {'PA': 27, 'TA': 6, 'LW_IN': 12}
LIMITS = {'PA': (50, 115), 'TA': (-70, 65), 'LW_IN': (70, 650)}
UNITS = {'PA': 'kPa', 'TA': 'deg C', 'LW_IN': 'W m-2'}
STEP = timedelta(minutes=30)
EXCLUSION = timedelta(hours=2)
SIGMA = 5.670374419e-8

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def number(x):
    v = float(x)
    if not math.isfinite(v) or v <= -9990:
        raise ValueError('missing or nonfinite source value')
    return v

def timestamp(x):
    return datetime.strptime(x, '%Y%m%d%H%M')

def physical_screen(var, value):
    lo, hi = LIMITS[var]
    return lo <= value <= hi

def selftest():
    assert physical_screen('PA', 98) and not physical_screen('PA', 0)
    assert physical_screen('TA', 20) and not physical_screen('TA', -200)
    assert physical_screen('LW_IN', 400) and not physical_screen('LW_IN', 20)
    assert timestamp('202212312330') + STEP == timestamp('202301010000')
    assert abs(400/(SIGMA*(20+273.15)**4)-0.9551875663445483) < 1e-12
    print('STAGE05BE SELF-TEST PASS; SELECTED METHOD SHADOW ONLY; ALL HOLD')

def table(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def key(row, time_field):
    return row['site'], row['variable'], timestamp(row[time_field])

def source_qc2(row):
    return row['original_F_QC'] == '2' and abs(number(row['original_F'])-number(row['original_same_release_ERA'])) < 1e-6

def read_inputs(preview, alternatives, ba_ledger):
    paths = {'preview':preview, 'alternatives':alternatives, 'ba_ledger':ba_ledger}
    for label, path in paths.items():
        if sha(path) != EXPECTED[label]:
            raise ValueError(label+' SHA256 mismatch')
    windows, choices, ledger = {}, {}, {}
    for row in table(preview):
        k = key(row, 'native')
        if k in windows or row['science_status'] != 'HOLD_NO_APPROVED_REPLACEMENT' or row['flagged'] not in ('True','False'):
            raise ValueError('preview duplicate or status mismatch')
        number(row['original_F']); windows[k] = row
    for row in table(alternatives):
        k = key(row, 'native_start')
        if k in choices or row['status'] != 'HOLD_NO_APPROVAL':
            raise ValueError('alternative duplicate or status mismatch')
        choices[k] = row
    for row in table(ba_ledger):
        k = key(row, 'native_start')
        if k in ledger or row['science_status'] != 'HOLD_NO_APPROVED_REPLACEMENT':
            raise ValueError('BA duplicate or status mismatch')
        ledger[k] = row
    flags = {k for k, row in windows.items() if row['flagged']=='True'}
    if (len(windows)!=1677 or len(flags)!=45 or set(choices)!=flags or set(ledger)!=flags
        or Counter(k[1] for k in flags)!=COUNTS or len({(k[0],k[2]) for k in flags})!=35):
        raise ValueError('input coverage mismatch')
    for k in flags:
        p, a, b = windows[k], choices[k], ledger[k]
        if not source_qc2(p) or abs(number(p['original_F'])-number(a['original_F']))>1e-7 or abs(number(p['original_F'])-number(b['original_F']))>1e-7:
            raise ValueError('original source or QC mismatch')
        candidate = number(a['grid_plus_QC2_background_median_NOT_APPROVED'])
        grid = number(b['grid_context_UTC9_hypothesis'])
        offset = float(a['background_QC2_median_source_minus_grid'])
        if not math.isfinite(offset) or abs(candidate-(grid+offset))>1e-6 or not physical_screen(k[1], candidate):
            raise ValueError('candidate arithmetic or basic plausibility screen failed')
    return windows, choices, ledger, flags

def groups_for(flags):
    groups = []
    for k in sorted(flags):
        if groups and k[:2] == groups[-1][-1][:2] and k[2]-groups[-1][-1][2] == STEP:
            groups[-1].append(k)
        else:
            groups.append([k])
    if len(groups)!=17 or Counter(map(len,groups))!={2:6, 3:11}:
        raise ValueError('group scope mismatch')
    return groups

def p95(values):
    ordered = sorted(values)
    return ordered[round((len(ordered)-1)*0.95)] if ordered else None

def run(preview, alternatives, ba_ledger, output):
    windows, choices, ledger, flags = read_inputs(preview, alternatives, ba_ledger)
    groups = groups_for(flags)
    selected = {k:number(choices[k]['grid_plus_QC2_background_median_NOT_APPROVED']) for k in flags}
    ledger_out = []
    for k in sorted(flags):
        a,b = choices[k],ledger[k]
        ledger_out.append({'site':k[0], 'variable':k[1], 'native_start':k[2].strftime('%Y%m%d%H%M'),
            'unit':UNITS[k[1]], 'original_F':windows[k]['original_F'],
            'selected_grid_plus_QC2_median_NOT_APPROVED':selected[k],
            'grid_context':b['grid_context_UTC9_hypothesis'],
            'qc2_background_median_source_minus_grid':a['background_QC2_median_source_minus_grid'],
            'qc2_background_n':a['background_QC2_n'], 'clock':a['grid_scenario_clock'],
            'original_F_QC':'2', 'selected_method':'USER_SELECTED_GRID_PLUS_SAME_RELEASE_QC2_MEDIAN',
            'basic_range_screen':'PASS_NOT_SCIENCE_APPROVAL', 'science_status':'HOLD_NO_APPROVED_REPLACEMENT'})
    preview_out = []
    for k,p in sorted(windows.items()):
        flag=k in flags
        preview_out.append({'site':k[0],'variable':k[1],'native':k[2].strftime('%Y%m%d%H%M'),
            'original_F':p['original_F'], 'selected_shadow_F_NOT_APPROVED':str(selected[k]) if flag else p['original_F'],
            'original_F_QC':p['original_F_QC'],'original_same_release_ERA':p['original_same_release_ERA'],
            'flagged':flag,'science_status':'HOLD_NO_APPROVED_REPLACEMENT'})
    if any(x['original_F']!=x['selected_shadow_F_NOT_APPROVED'] for x in preview_out if not x['flagged']):
        raise ValueError('non-event source identity failed')
    audit=[]
    for group in groups:
        site,var,start=group[0]; end=group[-1][2]
        left=(site,var,start-STEP);right=(site,var,end+STEP)
        if left not in windows or right not in windows or not source_qc2(windows[left]) or not source_qc2(windows[right]):
            raise ValueError('missing QC2 group endpoints')
        values=[number(windows[left]['original_F'])]+[selected[k] for k in group]+[number(windows[right]['original_F'])]
        jumps=[abs(b-a) for a,b in zip(values,values[1:])]
        bridge_values=[number(windows[left]['original_F'])]+[number(ledger[k]['shadow_value_NOT_APPROVED']) for k in group]+[number(windows[right]['original_F'])]
        bridge_max=max(abs(b-a) for a,b in zip(bridge_values,bridge_values[1:]))
        local=[]
        for (s,v,t),p in windows.items():
            if (s,v)!=(site,var) or not (start-timedelta(hours=24)<=t<=end+timedelta(hours=24)):
                continue
            prev=(s,v,t-STEP)
            if prev not in windows or any(abs(x-f[2])<=EXCLUSION for x in (t,t-STEP) for f in group):
                continue
            q=windows[prev]
            if source_qc2(p) and source_qc2(q) and physical_screen(var,number(p['original_F'])) and physical_screen(var,number(q['original_F'])):
                local.append(abs(number(p['original_F'])-number(q['original_F'])))
        if not local:
            raise ValueError('no clean local jump context')
        audit.append({'site':site,'variable':var,'native_group_start':start.strftime('%Y%m%d%H%M'),
            'native_group_end':end.strftime('%Y%m%d%H%M'),'unit':UNITS[var],
            'left_boundary_abs_jump':jumps[0],'within_group_max_abs_jump':max(jumps[1:-1]),
            'right_boundary_abs_jump':jumps[-1],'group_max_abs_jump':max(jumps),
            'prior_bridge_group_max_abs_jump':bridge_max,
            'local_QC2_jumps_n':len(local),'local_QC2_jump_p95_descriptive':p95(local),
            'selected_max_jump_above_observed_QC2_p95':max(jumps)>p95(local),
            'note':'OVERLAPPING_SAME_SOURCE_DESCRIPTIVE_NOT_APPROVAL','status':'HOLD_NO_APPROVAL'})
    co=[]
    for site,t in sorted({(k[0],k[2]) for k in flags}):
        target=next(k for k in sorted(flags) if k[0]==site and k[2]==t)
        p=windows[target]; item={'site':site,'native_start':t.strftime('%Y%m%d%H%M')}
        for var in ('PA','TA','LW_IN'):
            original=p['original_co_'+var+'_F']; q=p['original_co_'+var+'_F_QC']; sk=(site,var,t)
            if sk in flags and abs(number(original)-number(windows[sk]['original_F']))>1e-6:
                raise ValueError('co-variable source mismatch')
            try: value=selected[sk] if sk in flags else number(original)
            except ValueError: value=None
            item[var+'_context_or_shadow']=value if value is not None else ''
            item[var+'_provenance']='SELECTED_GRID_QC2_MEDIAN_HOLD' if sk in flags else 'ORIGINAL_F_QC_'+q
            item[var+'_broad_screen']=('MISSING' if value is None else 'PASS' if physical_screen(var,value) else 'OUTSIDE')
        ta=item['TA_context_or_shadow']; lw=item['LW_IN_context_or_shadow']
        item['LW_over_sigma_airT4_descriptive']=lw/(SIGMA*(ta+273.15)**4) if isinstance(ta,(int,float)) and isinstance(lw,(int,float)) and ta>-273.15 else ''
        item['note']='APPARENT_RATIO_NOT_ATMOSPHERIC_EMISSIVITY_OR_APPROVAL';item['status']='HOLD_NO_APPROVAL'
        co.append(item)
    if len(co)!=35:raise ValueError('co-variable scope mismatch')
    input_paths={'preview':preview,'alternatives':alternatives,'ba_ledger':ba_ledger}
    if any(sha(path)!=EXPECTED[label] for label,path in input_paths.items()):
        raise ValueError('input changed during computation')
    if output.parent.name!='japanflux_stage05be' or output.parent.is_symlink() or output.exists() or output.is_symlink():
        raise ValueError('output must be a fresh child of japanflux_stage05be')
    output.mkdir(parents=True)
    files=[('selected_45_HOLD.tsv',ledger_out),('selected_window_preview_NOT_FORCING.tsv',preview_out),
           ('boundary_sensitivity_17_groups_HOLD.tsv',audit),('covariable_context_35_times_HOLD.tsv',co)]
    for name,rows in files:
        with (output/name).open('x',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,rows[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    if any(sha(path)!=EXPECTED[label] for label,path in input_paths.items()):
        raise ValueError('input changed while writing; incomplete output is not usable')
    meta={'selected_method':'GRID_PLUS_LOCAL_QC2_MEDIAN','science_status':'ALL_45_HOLD','approved_values':0,
          'selected_fields':45,'group_count':17,'site_times':35,'preview_rows':1677,'unflagged_F_textually_identical':True,
          'broad_physical_screen':'45 PASS; NOT VALIDATION OR APPROVAL',
          'jump_flags_above_descriptive_p95':sum(x['selected_max_jump_above_observed_QC2_p95'] for x in audit),
          'covariable_note':'Original values unless flagged; range and LW/sigma(Tair)^4 are descriptive only',
          'input_sha256_pre_and_post_verified':EXPECTED,'outputs_sha256':{n:sha(output/n) for n,_ in files},
          'source_integrity':'pinned derived files only; source ZIPs not re-read',
          'production_forcing_original_zip_modified':False}
    with (output/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(meta,f,indent=2);f.write('\n')
    print('STAGE05BE 45 SELECTED SHADOWS, 17 GROUPS, 35 COTIMES; ALL HOLD; ZERO APPROVED')
    print('GROUP_JUMPS_ABOVE_QC2_DESCRIPTIVE_P95',meta['jump_flags_above_descriptive_p95'])
    print('OUTPUT',output)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--preview',type=Path);p.add_argument('--alternatives',type=Path);p.add_argument('--ba-ledger',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(x is None for x in (a.preview,a.alternatives,a.ba_ledger,a.out)):p.error('all three inputs and fresh output required')
    run(a.preview,a.alternatives,a.ba_ledger,a.out)

if __name__=='__main__':main()

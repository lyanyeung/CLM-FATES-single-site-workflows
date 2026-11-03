#!/usr/bin/env python3
"""Stage05AY: original-source, native-clock numerical screens; all science HOLD.

Requires the pinned Stage05AX helper, the actual Stage05AW ledger and summary,
Stage05K metadata, original 11-site manifest, and original ZIPs. No network,
forcing, source data or existing reports are modified. See companion protocol.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

AX_BLOB = '7cc202ff9a15fd4f78bba84d33cf65faeb4b3e07'
MANIFEST_BLOB = '344ce4d822f3a0393da7b7e2ef5ece6d6204104f'
ZIP_SHA256 = {
 'JP-Fjy':'205660bb8203bf7b16466041183ec9a1598f609727ef042ff4bceb800da949b9',
 'JP-Khw':'712ab4695704a695c28056eb0cfae0697af8a673228407dbc856088ad83bac79',
 'JP-Yms':'6bda3beb4fd9b580ef036e4b50f9c3162ca17b82b2b28466820e665bdedbf6f7',
 'JP-Tef':'315c825b64669aa03daff1d969f58a0a1cf3b574c43400ea1f84588df7f6d684',
 'JP-Tmd':'3ef287018725cb2b5b4c78130804febbe022dad66415807e70f628b756a13479',
}
BOUNDS = {'PA':(50.,115.), 'TA':(-70.,65.), 'LW_IN':(70.,650.)}
STEP = timedelta(minutes=30)

def blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def load_ax(path):
    if blob(path) != AX_BLOB:
        raise ValueError('Stage05AX helper Git blob mismatch')
    spec = importlib.util.spec_from_file_location('stage05ax_pinned', path)
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module

def number(s):
    try:
        n = float(s)
        return n if math.isfinite(n) and n > -9990 else None
    except (ValueError, TypeError, OverflowError):
        return None

def screen(var, value):
    n = number(value)
    if n is None:
        return 'UNKNOWN_MISSING'
    lo, hi = BOUNDS[var]
    return 'INSIDE_SCREEN_NOT_VALIDATED' if lo <= n <= hi else 'OUTSIDE_SCREEN'

def stamp(value):
    return datetime.strptime(value, '%Y%m%d%H%M')

def episode(rows, index, var, flag_keys):
    """Contiguous OUTSIDE_SCREEN, censored by missing/window edges.

    Inside bounds is a screen only. Unknown values do not establish boundaries.
    """
    if screen(var, rows[index][2]['source_F_value']) != 'OUTSIDE_SCREEN':
        return {'status':'FLAG_INSIDE_SCREEN_BOUNDARY_UNRESOLVED', 'length':'',
                'start':'', 'end':'', 'left':'', 'right':'', 'left_rec':{}, 'right_rec':{},
                'route':'HOLD_MANUAL', 'shadow':None}
    left = right = index
    while left > 0 and rows[left-1][0] == rows[left][0]-1 and screen(var, rows[left-1][2]['source_F_value']) == 'OUTSIDE_SCREEN':
        left -= 1
    while right+1 < len(rows) and rows[right+1][0] == rows[right][0]+1 and screen(var, rows[right+1][2]['source_F_value']) == 'OUTSIDE_SCREEN':
        right += 1
    a = rows[left-1] if left > 0 and rows[left-1][0] == rows[left][0]-1 else None
    b = rows[right+1] if right+1 < len(rows) and rows[right+1][0] == rows[right][0]+1 else None
    bounded = (a is not None and b is not None and
               screen(var,a[2]['source_F_value']) == 'INSIDE_SCREEN_NOT_VALIDATED' and
               screen(var,b[2]['source_F_value']) == 'INSIDE_SCREEN_NOT_VALIDATED')
    n = right-left+1
    verified_flags = all((r[1],var) in flag_keys for r in rows[left:right+1])
    def source_qc2(rec):
        f = number(rec['source_F_value']); e = number(rec['same_release_ERA'])
        return number(rec['source_F_QC']) == 2 and f is not None and e is not None and math.isclose(f,e,rel_tol=1e-10,abs_tol=1e-6)
    eligible = bounded and n <= 4 and verified_flags and source_qc2(a[2]) and source_qc2(b[2])
    candidate = None
    if eligible:
        av = number(a[2]['source_F_value']); bv = number(b[2]['source_F_value'])
        candidate = av + (bv-av)*(index-left+1)/(n+1)
    return {'status':'BOUNDED_SCREEN_ONLY' if bounded else 'CENSORED_OR_UNKNOWN_BOUNDARY',
            'length':n, 'start':rows[left][1], 'end':rows[right][1],
            'left':a[1] if a else '', 'right':b[1] if b else '',
            'left_rec':a[2] if a else {}, 'right_rec':b[2] if b else {},
            'route':'QC2_SHADOW_BRIDGE_REVIEW_ONLY' if eligible else 'HOLD_MANUAL',
            'shadow':candidate}

def write_tsv(path, rows, columns):
    with path.open('x',encoding='utf-8',newline='') as f:
        w = csv.DictWriter(f,fieldnames=columns,delimiter='\t',extrasaction='ignore')
        w.writeheader(); w.writerows(rows)

def run(a):
    ax = load_ax(a.ax)
    # Capture co-timed TA/PA/LW fields without a second original HH scan.
    snapshot = ax.point_field_snapshot
    def with_cross_variables(row,var,header):
        result = snapshot(row,var,header)
        for v in ('TA','PA','LW_IN'):
            for suffix in ('_F','_F_QC','_ERA','_F_MDS','_F_MDS_QC',''):
                name = v+suffix
                result['co_'+name] = row.get(name,'') if name in header else ''
                result['co_'+name+'_present'] = name in header
            result['co_'+v+'_F_screen'] = screen(v,result['co_'+v+'_F'])
        return result
    ax.point_field_snapshot = with_cross_variables
    if blob(a.manifest) != MANIFEST_BLOB:
        raise ValueError('sites.tsv Git blob mismatch')
    records = ax.table(a.fields); report = ax.jread(a.summary)
    ax.ledger_gate(report,records)
    packages = ax.original_manifest(a.manifest)
    # Output is a fresh child of this dedicated directory, not an input path.
    base = Path.home() / 'japanflux_stage05ay'
    if base.is_symlink() or (base.exists() and not base.is_dir()):
        raise ValueError('Unsafe Stage05AY output root')
    if a.out_dir.parent.resolve() != base.resolve() or a.out_dir.exists() or a.out_dir.is_symlink():
        raise ValueError('Output must be a fresh direct child of ~/japanflux_stage05ay')
    inputs = {'stage05aw_fields_sha256':ax.digest(a.fields),
              'stage05aw_summary_sha256':ax.digest(a.summary),
              'manifest_git_blob':MANIFEST_BLOB, 'stage05ax_git_blob':AX_BLOB}
    all_events=[]; all_windows=[]; evidence=[]
    for site in ax.SITES:
        source = a.root/site/'forcing'/'packages'/(packages[site]+'.zip')
        if source.is_symlink() or not source.is_file() or ax.digest(source) != ZIP_SHA256[site]:
            raise ValueError('Original outer ZIP SHA256 mismatch: '+site)
        expected,meta = ax.original_stage05k_readme(site,a.stage05k_dir)
        events={(r['site'],r['native_source_halfhour_start'],r['variable']):r for r in records if r['site']==site}
        observed=ax.read_site_source(site,packages[site],events,a.root,512,expected)
        if ax.digest(source) != ZIP_SHA256[site]:
            raise ValueError('Original ZIP changed during read: '+site)
        flag_keys={(key[1],key[2]) for key in events}
        evidence.append({'site':site,'outer_zip_sha256':ZIP_SHA256[site],
                         'readme_sha256':observed['original_source_readme_sha256'],
                         'stage05k_metadata_sha256':ax.digest(meta),
                         'source_hh_rows_scanned':observed['source_HH_rows_scanned'],
                         'source_hh_columns':observed['full_source_header']})
        for key in sorted(events):
            _,native,var=key
            rows=sorted(observed['source_window_rows'][key])
            offsets=[r[0] for r in rows]
            if len(offsets)!=len(set(offsets)) or offsets.count(0)!=1:
                raise ValueError('Duplicate or absent original window target '+repr(key))
            for off,ts,rec in rows:
                if stamp(ts) != stamp(native)+off*STEP:
                    raise ValueError('Window time mismatch '+repr(key))
                all_windows.append({'site':site,'flag_native':native,'variable':var,
                    'offset_halfhours':off,'native':ts,**rec,
                    'screen':screen(var,rec['source_F_value']),
                    'is_preexisting_45_flag':(ts,var) in flag_keys})
            result=episode(rows,offsets.index(0),var,flag_keys)
            arow=events[key]
            left=result['left_rec']; right=result['right_rec']
            all_events.append({'site':site,'native':native,'variable':var,
                 'original_F':arow['original_source_F_QC2'],
                 'independent_context_prior_outside':arow['outside_independent_hourly_envelope'],
                 'time_basis':arow['time_basis_provenance'],
                 'status':result['status'],'screen_run_start':result['start'],
                 'screen_run_end':result['end'],'screen_run_observed_HH':result['length'],
                 'immediate_left_native':result['left'],'immediate_right_native':result['right'],
                 'immediate_left_F':left.get('source_F_value',''),
                 'immediate_left_QC':left.get('source_F_QC',''),
                 'immediate_left_ERA':left.get('same_release_ERA',''),
                 'immediate_right_F':right.get('source_F_value',''),
                 'immediate_right_QC':right.get('source_F_QC',''),
                 'immediate_right_ERA':right.get('same_release_ERA',''),
                 'method_screen':result['route'],'shadow_value_not_approved':result['shadow'],
                 'external_ERA5L_method':'HOLD_NEEDS_TIME_ALIGNMENT_AND_VALIDATION',
                 'science_status':'HOLD_NO_APPROVED_REPLACEMENT'})
    if len(all_events)!=45 or len({(r['site'],r['native']) for r in all_events})!=35:
        raise ValueError('Final scope mismatch')
    clusters=defaultdict(list)
    for r in all_events:
        clusters[r['native'][:8]].append(r)
    cross=[{'native_date':day,'fields':len(rows),'sites':','.join(sorted({r['site'] for r in rows})),
            'variables':','.join(sorted({r['variable'] for r in rows})),
            'interpretation':'NATIVE_DATE_CO_OCCURRENCE_ONLY_NOT_PROOF_OF_COMMON_CAUSE'}
           for day,rows in sorted(clusters.items())]
    base.mkdir(exist_ok=True)
    a.out_dir.mkdir()
    write_tsv(a.out_dir/'events_HOLD.tsv',all_events,list(all_events[0]))
    write_tsv(a.out_dir/'native_windows.tsv',all_windows,list(all_windows[0]))
    write_tsv(a.out_dir/'native_date_clusters.tsv',cross,list(cross[0]))
    result={'stage':'JapanFlux Stage05AY','status':'DIAGNOSTIC_ONLY_NOT_SCIENCE_APPROVAL',
            'input_hashes':inputs,'site_source_evidence':evidence,
            'fields':45,'site_native_halfhours':35,
            'screen_status_counts':dict(Counter(x['status'] for x in all_events)),
            'method_screen_counts':dict(Counter(x['method_screen'] for x in all_events)),
            'source_clock':'Tef/Tmd local solar README conflicts with operator JST+9 hypothesis',
            'screen_bounds_not_validation':BOUNDS,'original_QC2_run_is_not_numerical_episode':True,
            'approved_replacements':0,'all_45_science_hold':True,
            'shadow_values_are_same_release_ERA_derived_not_QC0':True,
            'era5land':'Previously assessed hourly envelopes only; no new download or half-hour reconstruction',
            'cross_variable':'Window export includes co-timed PA/TA/LW fields when present and broad single-variable screens; physical coupling requires manual review',
            'source_zip_or_forcing_modified':False}
    with (a.out_dir/'summary_HOLD.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print('STAGE05AY DIAGNOSTIC COMPLETE; 45/45 SCIENCE HOLD; 0 APPROVED')
    print('SCREEN_STATUS',result['screen_status_counts'])
    print('METHOD_SCREENS',result['method_screen_counts'])
    print('OUTPUT',a.out_dir)
    print('NO ERA5L RERUN; NO SOURCE/FORCING/MODEL/SLURM MODIFICATION')

def self_test():
    def r(off,value,q='2',era=None):
        return (off,(datetime(2022,1,1)+off*STEP).strftime('%Y%m%d%H%M'),
                {'source_F_value':str(value),'source_F_QC':q,'same_release_ERA':str(value if era is None else era)})
    rows=[r(-1,100),r(0,0),r(1,100)]
    flags={(rows[1][1],'PA')}
    e=episode(rows,1,'PA',flags)
    assert e['status']=='BOUNDED_SCREEN_ONLY' and e['length']==1 and e['shadow']==100
    assert episode([r(0,0),r(1,100)],0,'PA',flags)['shadow'] is None
    assert episode([r(-1,'-9999'),r(0,0),r(1,100)],1,'PA',flags)['status']=='CENSORED_OR_UNKNOWN_BOUNDARY'
    assert episode([r(-1,100,'1'),r(0,0),r(1,100)],1,'PA',flags)['shadow'] is None
    assert episode([r(-1,100,era=99),r(0,0),r(1,100)],1,'PA',flags)['shadow'] is None
    assert episode([r(-1,100),r(0,0),r(1,49),r(2,100)],1,'PA',flags)['shadow'] is None
    assert episode([r(-1,100),r(0,99),r(1,100)],1,'PA',flags)['status']=='FLAG_INSIDE_SCREEN_BOUNDARY_UNRESOLVED'
    assert screen('PA','nan')=='UNKNOWN_MISSING' and screen('TA','-284.222')=='OUTSIDE_SCREEN'
    assert stamp('202212312330')+STEP==stamp('202301010000')
    print('STAGE05AY SELF-TEST PASS: bounds, censoring, QC2 provenance, scope and year boundary; ALL HOLD')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--ax',type=Path); p.add_argument('--manifest',type=Path)
    p.add_argument('--fields',type=Path); p.add_argument('--summary',type=Path)
    p.add_argument('--stage05k-dir',type=Path); p.add_argument('--out-dir',type=Path)
    p.add_argument('--root',type=Path,default=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
    a=p.parse_args()
    if a.self_test: self_test(); return
    if any(getattr(a,k) is None for k in ('ax','manifest','fields','summary','stage05k_dir','out_dir')):
        p.error('all input paths and fresh --out-dir required')
    run(a)
if __name__=='__main__': main()

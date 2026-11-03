#!/usr/bin/env python3
"""Rebuild 45 selected shadows from existing IRIDIS TSVs, never production forcing.

No CDS requests or ERA5-Land re-comparisons; no Slurm, PFT, soil or model writes.
Input files and five original source ZIPs are hashed before and after processing.
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

AW_SHA='6b717bdf8232388f59af849da01dbc316a8166e0a07305d3d2567d2d7d55e6ad'
WINDOW_SHA='89e9b41055b782da97ebcbda9c6ddb55a3c6bf6426ad40fdd2bb865e98a687d9'
AZ_SHA={'candidate_hourly_context_HOLD.tsv':'e7b3ca99f28e27e7b0a508697c607241767d238548dc3405f9231620737be785',
        'group_source_grid_residuals_HOLD.tsv':'ed5597796982bafd86a253f670870e90ebabb67212706b0f185d6ee147e7cd61',
        'background_pairs_READONLY.tsv':'6ff971ca857be54cc9eff1253087cc3179b19a53f2215672bced6e865a9b199b'}
CANONICAL_SELECTED_SHA='5fd381ddefac2d08a3cee7ed8548c73477c115a342f5895b4673b325768803ae'
SOURCE={
 'JP-Fjy':('2001-2021','205660bb8203bf7b16466041183ec9a1598f609727ef042ff4bceb800da949b9'),
 'JP-Khw':('2000-2021','712ab4695704a695c28056eb0cfae0697af8a673228407dbc856088ad83bac79'),
 'JP-Yms':('2000-2023','6bda3beb4fd9b580ef036e4b50f9c3162ca17b82b2b28466820e665bdedbf6f7'),
 'JP-Tef':('2001-2023','315c825b64669aa03daff1d969f58a0a1cf3b574c43400ea1f84588df7f6d684'),
 'JP-Tmd':('2005-2023','3ef287018725cb2b5b4c78130804febbe022dad66415807e70f628b756a13479')}
SITES=Counter({'JP-Fjy':6,'JP-Khw':11,'JP-Yms':10,'JP-Tef':4,'JP-Tmd':14})
VARS=Counter({'PA':27,'TA':6,'LW_IN':12})
LIMITS={'PA':(50.,115.),'TA':(-70.,65.),'LW_IN':(70.,650.)}
STEP=timedelta(minutes=30)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk)
    return h.hexdigest()
def checked(path,expected):
    if path.is_symlink() or not path.is_file() or digest(path)!=expected:
        raise ValueError('missing, symlink or SHA256 mismatch: '+str(path))
def num(x):
    value=float(x)
    if not math.isfinite(value) or value<=-9990:raise ValueError('invalid finite source value')
    return value
def ts(x):return datetime.strptime(x,'%Y%m%d%H%M')
def tsv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f,delimiter='\t')
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):raise ValueError('invalid TSV header')
        return list(r)
def canonical(rows):
    body=''.join('{}\t{}\t{}\t{:.6f}\n'.format(r['site'],r['variable'],r['native_start'],r['selected_value'])
                 for r in sorted(rows,key=lambda x:(x['site'],x['variable'],x['native_start'])))
    return hashlib.sha256(body.encode('ascii')).hexdigest()
def selftest():
    assert ts('202212312330')+STEP==ts('202301010000')
    assert hashlib.sha256(b'abc').hexdigest()=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    assert canonical([{'site':'A','variable':'PA','native_start':'202201010000','selected_value':1.}])==hashlib.sha256(b'A\tPA\t202201010000\t1.000000\n').hexdigest()
    try:num('nan')
    except ValueError:pass
    else:raise AssertionError('nonfinite accepted')
    print('STAGE05BF SELF-TEST PASS; READONLY SOURCE VERIFICATION; ALL HOLD')

def load_windows(records,events):
    unique={};offsets=defaultdict(set)
    fields=('source_F_value','source_F_QC','same_release_ERA','is_preexisting_45_flag',
            'co_PA_F','co_PA_F_QC','co_TA_F','co_TA_F_QC','co_LW_IN_F','co_LW_IN_F_QC')
    for r in records:
        target=(r['site'],r['variable'],ts(r['flag_native'])); t=ts(r['native']);off=int(r['offset_halfhours'])
        if target not in events or t!=target[2]+off*STEP or off in offsets[target]:raise ValueError('window time/flag mismatch')
        offsets[target].add(off);k=(r['site'],r['variable'],t)
        p={name:r[name] for name in fields}
        if p['is_preexisting_45_flag'] not in ('True','False'):raise ValueError('invalid flag')
        if k in unique and unique[k]!=p:raise ValueError('overlapping windows mismatch')
        unique[k]=p
    if set(offsets)!=set(events) or any(o!=set(range(-48,49)) for o in offsets.values()) or len(unique)!=1677:
        raise ValueError('window coverage mismatch')
    flags={k for k,p in unique.items() if p['is_preexisting_45_flag']=='True'}
    if flags!=set(events):raise ValueError('window flags mismatch')
    for k in flags:
        p=unique[k]; f=num(p['source_F_value']); era=num(p['same_release_ERA'])
        if num(p['source_F_QC'])!=2 or abs(f-era)>1e-6 or abs(f-num(events[k]['original_source_F_QC2']))>1e-6:
            raise ValueError('flag QC2/source F mismatch')
    return unique

def groups_for(flags):
    out=[]
    for k in sorted(flags):
        if out and out[-1][-1][:2]==k[:2] and k[2]-out[-1][-1][2]==STEP:out[-1].append(k)
        else:out.append([k])
    if len(out)!=17 or Counter(map(len,out))!={2:6,3:11}:raise ValueError('group scope mismatch')
    return out

def run(a):
    aw=a.aw;windows=a.ay/'native_windows.tsv';az=a.az
    sources=[]
    for site,(span,sha) in sorted(SOURCE.items()):
        path=a.source_root/site/'forcing'/'packages'/('JPF_'+site+'_FLUXNET_'+span+'_v1.3_r1.zip')
        sources.append((path,sha))
    inputs=[(aw,AW_SHA),(windows,WINDOW_SHA)]+[(az/name,sha) for name,sha in AZ_SHA.items()]+sources
    for path,sha in inputs:
        if path.suffix=='.zip':print('CHECK_ORIGINAL_ZIP',path.name,flush=True)
        checked(path,sha)
    summary_path=az/'summary_HOLD.json'
    if summary_path.is_symlink() or not summary_path.is_file():raise ValueError('missing or symlink AZ summary')
    summary_hash=digest(summary_path)
    with summary_path.open(encoding='utf-8') as f:summary=json.load(f)
    expected_summary={'status':'DIAGNOSTIC_ONLY_ALL_45_HOLD','approved_replacements':0,
                      'source_outer_zip_count_sha256_verified_twice':5,'cds_zip_count_sha256_crc_schema_24h_grid_verified':16,
                      'source_ledger_sha256':AW_SHA,'source_windows_sha256':WINDOW_SHA,'flags':45,'groups':17,'candidate_scenario_rows':99}
    if any(summary.get(k)!=v for k,v in expected_summary.items()):raise ValueError('AZ summary gate mismatch')
    events={}
    for r in tsv(aw):
        k=(r['site'],r['variable'],ts(r['native_source_halfhour_start']))
        if k in events or r['original_QC']!='2' or r['science_approval_status']!='HOLD_NO_APPROVED_30MIN_REPLACEMENT':raise ValueError('AW key/HOLD')
        events[k]=r
    if len(events)!=45 or Counter(k[0] for k in events)!=SITES or Counter(k[1] for k in events)!=VARS or len({(k[0],k[2]) for k in events})!=35:
        raise ValueError('AW scope mismatch')
    original=load_windows(tsv(windows),events);groups=groups_for(events)
    candidates={};all_candidates=tsv(az/'candidate_hourly_context_HOLD.tsv')
    if len(all_candidates)!=99:raise ValueError('candidate row count mismatch')
    for r in all_candidates:
        if num(r['offset_minutes'])!=540:continue
        k=(r['site'],r['variable'],ts(r['native']))
        if k in candidates or r['science_status']!='HOLD_NO_APPROVED_REPLACEMENT':raise ValueError('candidate key/HOLD')
        candidates[k]=r
    if set(candidates)!=set(events):raise ValueError('candidate coverage mismatch')
    group_rows=tsv(az/'group_source_grid_residuals_HOLD.tsv'); backgrounds=tsv(az/'background_pairs_READONLY.tsv')
    if len(group_rows)!=38 or len(backgrounds)!=1936:raise ValueError('AZ table row counts mismatch')
    bg=defaultdict(list);summary_groups={}
    for r in group_rows:
        if num(r['offset_minutes'])==540:
            k=(r['site'],r['variable'],ts(r['native_start']))
            if k in summary_groups:raise ValueError('duplicate group summary')
            summary_groups[k]=r
    for r in backgrounds:
        if num(r['offset_minutes'])!=540:continue
        k=(r['site'],r['variable'],ts(r['group_start']));t=ts(r['native'])
        if r['source_F_QC']!='2' or r['source_status']!='QC2_SAME_RELEASE_ERA_DERIVED':raise ValueError('non QC2 background')
        source=num(r['source_F']);grid=num(r['grid_context']);delta=float(r['source_minus_grid'])
        if not math.isfinite(delta) or abs(source-grid-delta)>1e-6:raise ValueError('background arithmetic')
        p=original[(k[0],k[1],t)]
        if p['is_preexisting_45_flag']!='False' or num(p['source_F_QC'])!=2 or abs(source-num(p['source_F_value']))>1e-6 or abs(source-num(p['same_release_ERA']))>1e-6:
            raise ValueError('background original mismatch')
        if any(abs(t-e[2])<=timedelta(hours=2) for e in events if e[:2]==k[:2]):raise ValueError('event exclusion')
        bg[k].append((t,delta))
    result=[];boundary=[];selected={}
    for group in groups:
        site,var,start=group[0];end=group[-1][2];g=(site,var,start)
        s=summary_groups[g];values=bg[g]
        if len({t for t,_ in values})!=len(values) or len(values)!=int(s['qc2_paired_count']) or not values:
            raise ValueError('background duplicate/count mismatch')
        med=statistics.median(d for _,d in values)
        if abs(med-float(s['qc2_source_minus_grid_median']))>1e-6:raise ValueError('background median mismatch')
        for k in group:
            r=candidates[k];grid=num(r['grid_context_NOT_HALF_HOUR_TRUTH']);value=grid+med
            lo,hi=LIMITS[var]
            if not lo<=value<=hi or abs(num(r['original_F'])-num(original[k]['source_F_value']))>1e-6:raise ValueError('candidate range/source mismatch')
            selected[k]=value
            result.append({'site':site,'variable':var,'native_start':k[2].strftime('%Y%m%d%H%M'),
                'original_F':original[k]['source_F_value'],'grid_context':grid,'qc2_background_median':med,
                'qc2_background_n':len(values),'selected_value':value,
                'clock':'UTC_PLUS9_HYPOTHESIS' if site in ('JP-Tef','JP-Tmd') else 'SOURCE_STANDARD_UTC_PLUS9',
                'method':'GRID_PLUS_SAME_RELEASE_QC2_MEDIAN','status':'HOLD_NO_APPROVED_REPLACEMENT'})
        left=original[(site,var,start-STEP)];right=original[(site,var,end+STEP)]
        for p in (left,right):
            if p['is_preexisting_45_flag']!='False' or num(p['source_F_QC'])!=2 or abs(num(p['source_F_value'])-num(p['same_release_ERA']))>1e-6:raise ValueError('invalid endpoint')
        seq=[num(left['source_F_value'])]+[selected[k] for k in group]+[num(right['source_F_value'])]
        jumps=[abs(b-a) for a,b in zip(seq,seq[1:])]
        boundary.append({'site':site,'variable':var,'native_start':start.strftime('%Y%m%d%H%M'),
            'left_jump':jumps[0],'within_max_jump':max(jumps[1:-1]),'right_jump':jumps[-1],
            'max_abs_jump':max(jumps),'status':'HOLD_NO_APPROVAL'})
    if canonical(result)!=CANONICAL_SELECTED_SHA:raise ValueError('selected values differ from local 45-field shadow at six decimals')
    preview=[]
    for (site,var,t),p in sorted(original.items()):
        k=(site,var,t);flag=k in selected
        preview.append({'site':site,'variable':var,'native':t.strftime('%Y%m%d%H%M'),
            'original_F':p['source_F_value'],'selected_shadow_NOT_APPROVED':str(selected[k]) if flag else p['source_F_value'],
            'original_F_QC':p['source_F_QC'],'flagged':flag,'status':'HOLD_NO_APPROVAL'})
    if any(r['original_F']!=r['selected_shadow_NOT_APPROVED'] for r in preview if not r['flagged']):raise ValueError('non-event F altered')
    for path,sha in inputs:
        if path.suffix=='.zip':print('RECHECK_ORIGINAL_ZIP',path.name,flush=True)
        checked(path,sha)
    if digest(summary_path)!=summary_hash:raise ValueError('AZ summary changed during read')
    root=Path.home()/'japanflux_stage05bf'
    if root.is_symlink() or (root.exists() and not root.is_dir()) or a.out.parent.resolve()!=root.resolve() or a.out.exists() or a.out.is_symlink():
        raise ValueError('output must be a fresh direct child of ~/japanflux_stage05bf')
    root.mkdir(exist_ok=True);a.out.mkdir()
    for name,rows in [('selected_45_HOLD.tsv',result),('selected_window_preview_NOT_FORCING.tsv',preview),('boundary_17_groups_HOLD.tsv',boundary)]:
        with (a.out/name).open('x',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,rows[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    report={'stage':'05BF','status':'ALL_45_HOLD','approved_values':0,'selected_fields':45,'groups':17,
        'native_site_times':35,'preview_rows':1677,'unflagged_F_text_identical':True,
        'canonical_six_decimal_selected_sha256':canonical(result),'original_source_zip_sha256_checked_before_after':5,
        'AZ_reported_16_CDS_integrity_gates':'RECORDED_IN_EXISTING_SUMMARY_NOT_REEXECUTED',
        'AZ_summary_sha256_observed':summary_hash,'AZ_summary_gate_fields':expected_summary,
        'output_sha256':{n:digest(a.out/n) for n in ('selected_45_HOLD.tsv','selected_window_preview_NOT_FORCING.tsv','boundary_17_groups_HOLD.tsv')},
        'clock_warning':'Tef/Tmd UTC+9 is diagnostic hypothesis; publisher local solar clock unresolved',
        'production_forcing_source_zip_modified':False}
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print('STAGE05BF PASS: 45 SELECTED SHADOWS; 17 GROUPS; 35 SITE-TIMES; ALL HOLD; ZERO APPROVED')
    print('5 SOURCE ZIP SHA256 VERIFIED BEFORE AND AFTER; EXISTING AZ SUMMARY RECORDED 16 CDS GATES; NO CDS RECHECK')
    print('CANONICAL_SELECTED_SHA256',canonical(result));print('OUTPUT',a.out)
    print('NO CDS DOWNLOAD; NO FORCING, ORIGINAL ZIP, PFT, SOIL, MODEL OR SLURM MODIFICATION')
    print(json.dumps(report,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--aw',type=Path);p.add_argument('--ay',type=Path);p.add_argument('--az',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--source-root',type=Path,default=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(x is None for x in (a.aw,a.ay,a.az,a.out)):p.error('--aw --ay --az --out required')
    run(a)
if __name__=='__main__':main()

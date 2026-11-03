#!/usr/bin/env python3
"""Find genuine selected-QC0 source data near 17 held JapanFlux groups.

Read only five pinned original nested JPF ZIPs and existing AW/05BF ledgers.
Scans the original FLUXMET HH once per site; no CDS requests, forcing edits,
PFT/soil/model changes, scheduler or approvals. 30-day samples are context,
not event truth and not a validation of the selected grid-plus-median method.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path,PurePosixPath

AW_SHA='6b717bdf8232388f59af849da01dbc316a8166e0a07305d3d2567d2d7d55e6ad'
SELECTED_SHA='bd36ee5d5f8297f4edd8a5c08562473e2110fe6da6354dbaaf0754aaa5ad434f'
SITES=Counter({'JP-Fjy':6,'JP-Khw':11,'JP-Yms':10,'JP-Tef':4,'JP-Tmd':14})
VARS=Counter({'PA':27,'TA':6,'LW_IN':12})
SOURCE={
 'JP-Fjy':('2001-2021','205660bb8203bf7b16466041183ec9a1598f609727ef042ff4bceb800da949b9'),
 'JP-Khw':('2000-2021','712ab4695704a695c28056eb0cfae0697af8a673228407dbc856088ad83bac79'),
 'JP-Yms':('2000-2023','6bda3beb4fd9b580ef036e4b50f9c3162ca17b82b2b28466820e665bdedbf6f7'),
 'JP-Tef':('2001-2023','315c825b64669aa03daff1d969f58a0a1cf3b574c43400ea1f84588df7f6d684'),
 'JP-Tmd':('2005-2023','3ef287018725cb2b5b4c78130804febbe022dad66415807e70f628b756a13479')}
LIMITS={'PA':(50.,115.),'TA':(-70.,65.),'LW_IN':(70.,650.)}
STEP=timedelta(minutes=30);DAYS=timedelta(days=30);MAX_INNER=512*1024*1024
ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(2*1024*1024),b''):h.update(block)
    return h.hexdigest()
def checked(path,expected):
    if path.is_symlink() or not path.is_file() or sha(path)!=expected:raise ValueError('missing/symlink/SHA256 mismatch '+str(path))
def stamp(s):return datetime.strptime(s,'%Y%m%d%H%M')
def num(s):
    try:v=float(s)
    except (ValueError,TypeError):return None
    return v if math.isfinite(v) and v>-9990 else None
def good(var,value,q):
    n=num(value);quality=num(q);lo,hi=LIMITS[var]
    return quality==0 and n is not None and lo<=n<=hi
def table(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f,delimiter='\t')
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):raise ValueError('TSV header')
        return list(r)
def group_events(events):
    groups=[]
    for k in sorted(events):
        if groups and groups[-1][-1][:2]==k[:2] and k[2]-groups[-1][-1][2]==STEP:groups[-1].append(k)
        else:groups.append([k])
    if len(groups)!=17 or Counter(map(len,groups))!={2:6,3:11}:raise ValueError('group scope')
    return groups
def measured_blocks(q0,group):
    """Overlapping same-source QC0 masks; not independent grid validation."""
    n=len(group);errors=[];blocks=0
    for start in sorted(q0):
        ts=[start+i*STEP for i in range(n)];left=start-STEP;right=start+n*STEP
        points=[left,*ts,right]
        if any(t not in q0 for t in points):continue
        if any(abs(t-k[2])<=timedelta(hours=2) for t in points for k in group):continue
        a,b=q0[left],q0[right];blocks+=1
        errors.extend(abs((a+(b-a)*(i+1)/(n+1))-q0[t]) for i,t in enumerate(ts))
    return blocks,errors
def selftest():
    base=stamp('202212312330');assert base+STEP==stamp('202301010000')
    assert good('PA','100','0') and not good('PA','0','0') and not good('TA','20','1')
    q={base+i*STEP:float(i) for i in range(5)}
    blocks,errors=measured_blocks(q,[('JP-X','PA',base+timedelta(days=2))]*3)
    assert blocks==1 and max(errors)==0
    print('STAGE05BL SELF-TEST PASS; QC0 CONTEXT ONLY; ALL HOLD')

def load_ledgers(aw,selected):
    checked(aw,AW_SHA);checked(selected,SELECTED_SHA);events={};sel={}
    for r in table(aw):
        k=(r['site'],r['variable'],stamp(r['native_source_halfhour_start']))
        if k in events or r['original_QC']!='2' or r['science_approval_status']!='HOLD_NO_APPROVED_30MIN_REPLACEMENT':raise ValueError('AW key/HOLD')
        events[k]=r
    for r in table(selected):
        k=(r['site'],r['variable'],stamp(r['native_start']))
        if k in sel or r['status']!='HOLD_NO_APPROVED_REPLACEMENT' or r['method']!='GRID_PLUS_SAME_RELEASE_QC2_MEDIAN':raise ValueError('05BF key/HOLD/method')
        sel[k]=r
    if (len(events)!=45 or set(events)!=set(sel) or Counter(k[0] for k in events)!=SITES or Counter(k[1] for k in events)!=VARS
        or len({(k[0],k[2]) for k in events})!=35):raise ValueError('45 field scope')
    for k in events:
        if num(events[k]['original_source_F_QC2']) is None or num(sel[k]['original_F'])!=num(events[k]['original_source_F_QC2']):raise ValueError('source ledger disagreement')
    return events,sel

def scan_site(site,root,groups,events):
    span,expected=SOURCE[site];name=f'JPF_{site}_FLUXNET_{span}_v1.3_r1.zip';outer=root/site/'forcing'/'packages'/name
    print('SCAN_SOURCE',site,flush=True);checked(outer,expected)
    relevant=[g for g in groups if g[0][0]==site];byvar=defaultdict(list)
    for g in relevant:
        byvar[g[0][1]].append((g,(g[0][2]-DAYS).strftime('%Y%m%d%H%M'),(g[-1][2]+DAYS).strftime('%Y%m%d%H%M')))
    samples={g[0]:{} for g in relevant};found=set();rows=0;prev=''
    with zipfile.ZipFile(outer) as z:
        match=[x for x in z.infolist() if x.filename==name and not x.is_dir()]
        if len(match)!=1 or not 0<match[0].file_size<=MAX_INNER:raise ValueError('nested ZIP scope '+site)
        buf=io.BytesIO()
        with z.open(match[0]) as f:
            for block in iter(lambda:f.read(2*1024*1024),b''):
                buf.write(block)
                if buf.tell()>MAX_INNER:raise ValueError('nested ZIP too large')
        buf.seek(0)
        with zipfile.ZipFile(buf) as inner:
            wanted=name.replace('.zip','').replace('_FLUXNET_', '_FLUXNET_FLUXMET_HH_')+'.csv'
            files=[x for x in inner.infolist() if not x.is_dir() and PurePosixPath(x.filename).name==wanted]
            if len(files)!=1:raise ValueError('FLUXMET HH member scope '+site)
            with inner.open(files[0]) as binary,io.TextIOWrapper(binary,encoding='utf-8-sig',newline='') as text:
                reader=csv.DictReader(text);header=reader.fieldnames or []
                required={'TIMESTAMP_START','TIMESTAMP_END'} | {v+s for v in byvar for s in ('_F','_F_QC','_ERA')}
                if not required<=set(header) or len(header)!=len(set(header)):raise ValueError('HH source schema')
                for row in reader:
                    rows+=1;s=row['TIMESTAMP_START']
                    if len(s)!=12 or not s.isdigit() or (prev and s<=prev):raise ValueError('source timestamp order')
                    prev=s
                    for var,sets in byvar.items():
                        target=[g for g,lo,hi in sets if lo<=s<=hi]
                        if not target:continue
                        when=stamp(s)
                        if row['TIMESTAMP_END']!=(when+STEP).strftime('%Y%m%d%H%M'):raise ValueError('HH interval')
                        k=(site,var,when)
                        if k in events:
                            f=num(row[var+'_F']);era=num(row[var+'_ERA'])
                            if k in found or num(row[var+'_F_QC'])!=2 or f is None or era is None or abs(f-era)>1e-6 or abs(f-num(events[k]['original_source_F_QC2']))>1e-6:
                                raise ValueError('flagged F/ERA/QC changed')
                            found.add(k)
                        if good(var,row[var+'_F'],row[var+'_F_QC']):
                            for g in target:samples[g[0]][when]=num(row[var+'_F'])
    checked(outer,expected)
    if found!={k for k in events if k[0]==site}:raise ValueError('missing flagged source keys')
    return samples,rows

def result_rows(groups,samples):
    summary=[];exports=[]
    for g in groups:
        site,var,start=g[0];end=g[-1][2];q=samples[g[0]]
        left=[x for x in q if x<start];right=[x for x in q if x>end]
        left_t=max(left) if left else None;right_t=min(right) if right else None
        within7=sum(start-timedelta(days=7)<=t<=end+timedelta(days=7) for t in q)
        blocks,errors=measured_blocks(q,g)
        err=sorted(errors);p95=err[round((len(err)-1)*.95)] if err else ''
        summary.append({'site':site,'variable':var,'group_start':start.strftime('%Y%m%d%H%M'),
            'group_end':end.strftime('%Y%m%d%H%M'),'flagged_fields':len(g),
            'qc0_broad_range_screened_count_30d':len(q),'qc0_broad_range_screened_count_7d':within7,
            'nearest_left_qc0_native':left_t.strftime('%Y%m%d%H%M') if left_t else '',
            'nearest_left_qc0_distance_hours':(start-left_t).total_seconds()/3600 if left_t else '',
            'nearest_right_qc0_native':right_t.strftime('%Y%m%d%H%M') if right_t else '',
            'nearest_right_qc0_distance_hours':(right_t-end).total_seconds()/3600 if right_t else '',
            'overlapping_qc0_blocks_with_qc0_endpoints':blocks,
            'qc0_bridge_mask_mae_same_source_not_grid_validation':statistics.mean(errors) if errors else '',
            'qc0_bridge_mask_p95_not_confidence_interval':p95,
            'clock':'UTC_PLUS9_UNRESOLVED_README_CONFLICT' if site in ('JP-Tef','JP-Tmd') else 'SOURCE_README_STANDARD_UTC9',
            'status':'HOLD_NO_APPROVAL'})
        for t,value in sorted(q.items()):
            exports.append({'site':site,'variable':var,'group_start':start.strftime('%Y%m%d%H%M'),
                'native':t.strftime('%Y%m%d%H%M'),'source_measured_F_QC0':value,
                'role':'MEASURED_SOURCE_OTHER_TIME_NOT_EVENT_TRUTH','status':'HOLD_NO_APPROVAL'})
    return summary,exports

def run(a):
    events,selected=load_ledgers(a.aw,a.selected);groups=group_events(events)
    base=Path.home()/'japanflux_stage05bl'
    if base.is_symlink() or (base.exists() and not base.is_dir()) or a.out.parent.resolve()!=base.resolve() or a.out.exists() or a.out.is_symlink():
        raise ValueError('output must be a fresh direct child of ~/japanflux_stage05bl')
    samples={};scans={}
    for site in sorted(SOURCE):
        q,n=scan_site(site,a.source_root,groups,events);samples.update(q);scans[site]=n
    checked(a.aw,AW_SHA);checked(a.selected,SELECTED_SHA)
    summary,exports=result_rows(groups,samples)
    if len(summary)!=17:raise ValueError('summary scope')
    base.mkdir(exist_ok=True);a.out.mkdir()
    for name,rows in [('qc0_17_group_summary_HOLD.tsv',summary),('qc0_30day_measured_samples_READONLY.tsv',exports)]:
        fields=list(rows[0]) if rows else ['site','variable','group_start','native','source_measured_F_QC0','role','status']
        with (a.out/name).open('x',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    report={'status':'MEASURED_CONTEXT_ALL_45_HOLD','approved_values':0,'fields':45,'groups':17,
        'source_rows_by_site':scans,'groups_with_broad_range_screened_qc0_30d':sum(r['qc0_broad_range_screened_count_30d']>0 for r in summary),
        'groups_with_qc0_mask_blocks':sum(r['overlapping_qc0_blocks_with_qc0_endpoints']>0 for r in summary),
        'qc0_sample_rows':len(exports),'selected_method_unchanged':'GRID_PLUS_SAME_RELEASE_QC2_MEDIAN',
        'interpretation':'Counts are QC0 values passing broad screens, not all QC0 values. QC0 at other times is not event truth; bridge masking does not validate chosen grid method; matched independent grid data are not requested',
        'original_zip_forcing_pft_soil_model_slurm_modified':False,
        'output_sha256':{n:sha(a.out/n) for n in ('qc0_17_group_summary_HOLD.tsv','qc0_30day_measured_samples_READONLY.tsv')}}
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print('STAGE05BL COMPLETE; 17 GROUPS; ALL 45 HOLD; ZERO APPROVED');print('OUTPUT',a.out)
    print(json.dumps(report,indent=2));print('GROUP_SUMMARY_TSV')
    with (a.out/'qc0_17_group_summary_HOLD.tsv').open(encoding='utf-8') as f:print(f.read(),end='')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true');p.add_argument('--aw',type=Path)
    p.add_argument('--selected',type=Path);p.add_argument('--out',type=Path);p.add_argument('--source-root',type=Path,default=ROOT);a=p.parse_args()
    if a.self_test:selftest();return
    if any(x is None for x in (a.aw,a.selected,a.out)):p.error('--aw --selected --out required')
    run(a)
if __name__=='__main__':main()

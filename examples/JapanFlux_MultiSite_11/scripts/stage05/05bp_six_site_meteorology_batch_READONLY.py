#!/usr/bin/env python3
"""Six-site source-aware QC batch. Diagnostic only; no model/forcing writes."""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
HELPER_SHA='b26fb4792fd353137a0856b0b45068f1083de2e8c1e8526d6797efc69506c6ca'
SOURCES={
 'JP-Api':('JPF_JP-Api_FLUXNET_2000-2022_v1.3_r2','dab9de152210d4f95d88c79c7b9e67bd5ccde19fee86304bee093634f000342b',403248),
 'JP-Fhk':('JPF_JP-Fhk_FLUXNET_2006-2023_v1.3_r1','20abdd06ed23de7d599841e8ac64a21b2378a169deae6f3f891f6230e4a31667',315552),
 'JP-Spp':('JPF_JP-Spp_FLUXNET_2000-2018_v1.3_r1','6941f9bf4c6f7f2e80c9a7c991fde1b2c92bc3d7a111321ae50bd7d370d35aaf',333120),
 'JP-Tak':('JPF_JP-Tak_FLUXNET_1998-2021_v1.3_r1','cf1da393c026deb35dcc9b328bf5c7ae7ca9eea22dbbf8a095907e06373dc151',420768),
 'JP-Tom':('A20241210-015v200','ea3e5a3583b1defc722d44ee8343acdca6d902eb7e688268d44b2d47efcd193e',None),
 'JP-Tgf':('A20241210-013_2.00_selected','d0476fff16f6bce8f53a0d640668dc28d0df7e6fbfda86565a26b247f267c204',None)}
JPF=('JP-Api','JP-Fhk','JP-Spp','JP-Tak')
SPECIAL=('JP-Tom','JP-Tgf')
EXPECTED={('JP-Tom','HR'):35064,('JP-Tom','HH'):192864,('JP-Tgf','HH'):368160}
EVENTS={'JP-Fhk':(8,12),'JP-Spp':(6,9),'JP-Tak':(9,6)}
FIELDS=('TA_F','RH_F','VPD_F','PA_F','SW_IN_F','LW_IN_F','P_F','WS_F')
EPS=1e-9

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def checked(path,expected=None):
    if path.is_symlink() or not path.is_file():raise ValueError('missing or symlink input: '+str(path))
    value=sha(path)
    if expected is not None and value!=expected:raise ValueError('SHA256 mismatch: '+str(path))
    return value
def num(s):
    try:x=float(s)
    except (ValueError,TypeError):return None
    return x if math.isfinite(x) and x>-6999 else None
def native(value):
    if len(value)!=12 or not value.isdigit():raise ValueError('bad native timestamp')
    return datetime.strptime(value,'%Y%m%d%H%M')
def safe(name):
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name
def meta_helper(path):
    checked(path,HELPER_SHA)
    spec=importlib.util.spec_from_file_location('stage05k',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def source(root,site):
    return root/site/'forcing'/'packages'/(SOURCES[site][0]+'.zip')
def load_json(p):
    with p.open(encoding='utf-8') as f:return json.load(f)
def stage04(path):
    obj=load_json(path)
    if obj.get('stage')!='JapanFlux Stage04' or obj.get('read_only') is not True or not obj.get('full_scan_requested') or obj.get('screened')!=11 or obj.get('expected')!=11:raise ValueError('not complete Stage04 report')
    sites={x['site']:x for x in obj['sites']}
    if len(sites)!=11 or any(sites[s]['status']!='READONLY_SCREEN_DONE' for s in SOURCES):raise ValueError('Stage04 site status')
    return sites
def review_derived(site,stage,sd,sf):
    parts=stage['files']
    if len(parts)!=1 or parts[0]['rows']!=SOURCES[site][2] or parts[0].get('truncated_by_max_rows'):raise ValueError('JPF source coverage')
    part=parts[0]
    if any(v for k,v in part['time'].items() if k!='examples' and isinstance(v,int)):raise ValueError('JPF time screen')
    flags={f:q.get('screen_counts',{}) for f,q in part['fields'].items() if q.get('screen_counts')}
    if flags:raise ValueError('JPF Stage04 unexpectedly has threshold flags')
    if sd.get('stage')!='JapanFlux Stage05D' or sd.get('site')!=site or sd.get('read_only') is not True or sd.get('status')!='ERA5_FULL_SCAN_COMPLETED':raise ValueError('bad Stage05D')
    count=sd['flagged_unique_native_starts']
    if site=='JP-Api':
        if count!=0:raise ValueError('Api ERA screen mismatch')
        impact={'status':'NO_FLAGGED_COMPANION_EVENTS_UNDER_STAGE05D_SCREEN'}
    else:
        if sf.get('stage')!='JapanFlux Stage05F' or sf.get('site')!=site or sf.get('status')!='READONLY_SOURCE_IMPACT_SCREEN_COMPLETE':raise ValueError('bad Stage05F')
        inside,outside=EVENTS[site]
        if count!=inside+outside or sf.get('ERA5_event_starts_inside_FLUXMET_source')!=inside or len(sf.get('ERA5_event_starts_outside_FLUXMET_source',[]))!=outside or sf.get('selected_F_screen_flagged_by_field'):raise ValueError('prior event impact mismatch')
        impact={'ERA_flagged_native_starts_inside_selected_coverage':inside,'outside':outside,
            'selected_F_flags_by_field':sf['selected_F_screen_flagged_by_field'],
            'selected_F_vs_same_release_ERA_raw_comparisons':sf.get('ERA_event_source_matches',{}),
            'QC_raw_histograms':sf.get('ERA_event_selected_F_QC_raw_histogram',{}),
            'scope':'PRIOR_EXACT_EVENT_AND_SAMPLED_CONTEXT_ONLY_NOT_ALL_TIME'}
    return {'site':site,'selected_source_rows':part['rows'],'stage04_selected_threshold_flags':flags,
        'companion_ERA_screened_flagged_starts':count,'companion_event_impact':impact,
        'missing_columns':part.get('missing_fields',[]),'field_summaries':part['fields'],
        'status':'INITIAL_SCREENS_REVIEW_ONLY_NO_SCIENTIFIC_CLEARANCE'}

def metadata_summary(item):
    info=item['release_metadata']['BIFVARINFO_HH']
    metas=item['release_metadata']['site_metadata_and_readme']
    hints=[{'member':m['member'],'sha256':m['sha256'],'hints':m['first_90_time_unit_hints']}
           for m in metas if m['first_90_time_unit_hints']]
    groups=[]
    for g in info['focus_variable_groups']:
        relevant=[r for r in g['source_fields'] if any(k in r['key'].upper() for k in ('VARNAME','UNIT','DEFINITION'))]
        if relevant:groups.append({'matching_names':g['matching_names'],'fields':relevant})
    return {'BIFVARINFO_HH_sha256':info['sha256'],'coverage':info['coverage'],
            'focus_variable_evidence':groups,'time_unit_hints':hints}

def diagnose(site,cadence,reader,expected_rows=None,stage_part=None):
    names=reader.fieldnames or []
    required={'TIMESTAMP_START','TIMESTAMP_END'}|set(FIELDS)|{f+'_QC' for f in FIELDS}
    if len(names)!=len(set(names)) or not required.issubset(names):raise ValueError('missing/duplicate COREVARS header')
    n=0;prev_end=None;first=None;last=None;counts=Counter();by_year=defaultdict(Counter)
    hist=defaultdict(Counter); anomalies=[]; contexts=[]; pending=[]; history=deque(maxlen=2)
    minima={f:None for f in FIELDS};maxima={f:None for f in FIELDS}
    extremes={'lowest_vpd':None,'highest_rh':None}
    for row in reader:
        if None in row or any(v is None for v in row.values()):raise ValueError('CSV row width mismatch')
        s=row['TIMESTAMP_START'];e=row['TIMESTAMP_END'];dt=native(s);end=native(e)
        if end-dt!=timedelta(minutes=60 if cadence=='HR' else 30) or (prev_end is not None and dt!=prev_end):raise ValueError('source interval mismatch/gap/overlap')
        prev_end=end;n+=1
        if first is None:first=[s,e]
        last=[s,e];v={f:num(row[f]) for f in FIELDS}
        for f,x in v.items():
            if x is not None:
                minima[f]=x if minima[f] is None else min(minima[f],x)
                maxima[f]=x if maxima[f] is None else max(maxima[f],x)
        rh,deficit,rain,pressure,short=(v['RH_F'],v['VPD_F'],v['P_F'],v['PA_F'],v['SW_IN_F'])
        keys=[]
        if rh is not None and deficit is not None:
            keys.append('valid_RH_VPD_pair')
            over=rh>100;negative=deficit<0;material=deficit < -EPS
            if over:keys.append('RH_above_100_pct')
            if negative:keys.append('VPD_negative_any')
            if material:keys.append('VPD_negative_below_minus_1e-9')
            if negative and not material:keys.append('VPD_negative_tiny_ge_minus_1e-9')
            if over and material:keys.append('RH_above_100_and_VPD_material_negative')
            if over and not negative:keys.append('RH_above_100_and_VPD_nonnegative')
            if not over and material:keys.append('RH_not_above_100_and_VPD_material_negative')
        else:
            if rh is not None and rh>100:keys.append('RH_above_100_pct')
            if deficit is not None and deficit<0:
                keys.append('VPD_negative_any')
                keys.append('VPD_negative_below_minus_1e-9' if deficit < -EPS else 'VPD_negative_tiny_ge_minus_1e-9')
        if rain is not None and rain<0:keys.append('P_negative_any');keys.append('P_negative_below_minus_1e-9' if rain < -EPS else 'P_negative_tiny_ge_minus_1e-9')
        if pressure is not None and pressure<50:keys.append('PA_below_50_assumed_kPa')
        if short is not None and short < -20:keys.append('SW_below_minus_20_assumed_Wm2')
        for k in keys:counts[k]+=1;by_year[s[:4]][k]+=1
        for f,x in v.items():
            if x is not None:hist[f][row[f+'_QC'].strip() or '<blank>']+=1
        info={'site':site,'cadence':cadence,'native_start':s,'native_end':e}
        for f in FIELDS:info[f]=row[f];info[f+'_QC_raw']=row[f+'_QC']
        active=[k for k in keys if k!='valid_RH_VPD_pair']
        if active:
            anomalies.append({**info,'screen_tags':'|'.join(active),'status':'SCREEN_ONLY_NO_APPROVAL'})
            if len(anomalies)>100000:raise ValueError('anomaly export cap exceeded')
        for f,label,order in (('RH_F','highest_rh',1),('VPD_F','lowest_vpd',-1)):
            x=v[f]
            if x is not None and (extremes[label] is None or order*x>order*extremes[label][0]):extremes[label]=(x,info)
        for item in pending:
            if item['remaining']>0:item['rows'].append(info);item['remaining']-=1
        pending=[item for item in pending if item['remaining']>0]
        if 'PA_below_50_assumed_kPa' in keys or 'SW_below_minus_20_assumed_Wm2' in keys:
            item={'event_native_start':s,'flags':[k for k in keys if k.startswith(('PA_','SW_'))],
                  'rows':list(history)+[info],'remaining':2,'left_context_censored':len(history)<2}
            contexts.append(item);pending.append(item)
            if len(contexts)>32:raise ValueError('unexpected number of isolated events')
        history.append(info)
    if expected_rows is not None and n!=expected_rows:raise ValueError('source row count mismatch')
    if stage_part is not None:
        for field,tag,key in (('RH_F','GT_100_pct','RH_above_100_pct'),('VPD_F','LT_0_hPa','VPD_negative_any'),
                              ('P_F','LT_0_native_precip_unit','P_negative_any'),('PA_F','LT_50_kPa','PA_below_50_assumed_kPa'),
                              ('SW_IN_F','LT_-20_W_m2','SW_below_minus_20_assumed_Wm2')):
            if stage_part['fields'][field].get('screen_counts',{}).get(tag,0)!=counts[key]:raise ValueError('Stage04 count mismatch '+site+' '+cadence+' '+field)
    for item in contexts:
        item['right_context_censored']=item.pop('remaining')>0
    result={'site':site,'cadence':cadence,'rows':n,'first_interval':first,'last_interval':last,'counts':dict(counts),
        'counts_by_native_year':{k:dict(v) for k,v in sorted(by_year.items())},
        'field_minima':minima,'field_maxima':maxima,'QC_raw_histograms':{k:dict(v) for k,v in hist.items()},
        'extremes':{k:({'value':v[0],'source_row':v[1]} if v else None) for k,v in extremes.items()},
        'isolated_PA_SW_context':contexts,'status':'SCREEN_AND_SOURCE_CONTEXT_ONLY_NO_APPROVAL'}
    return result,anomalies

def selftest():
    assert num('-9999') is None and num('NaN') is None and num('-1e-15')==-1e-15
    assert native('200312312330')+timedelta(minutes=30)==native('200401010000')
    assert SOURCES['JP-Tgf'][1].startswith('d0476fff')
    print('STAGE05BP SELF-TEST PASS; SIX-SITE SOURCE SCREEN ONLY; ZERO APPROVALS')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--stage04',type=Path);p.add_argument('--stage05d',type=Path);p.add_argument('--stage05f',type=Path)
    p.add_argument('--helper',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(getattr(a,x) is None for x in ('stage04','stage05d','stage05f','helper','out')):p.error('all report paths, helper and output required')
    run(a)

def run(a):
    base=Path.home()/'japanflux_stage05bp'
    if base.is_symlink() or (base.exists() and not base.is_dir()) or a.out.parent.resolve()!=base.resolve() or a.out.exists() or a.out.is_symlink():raise ValueError('fresh ~/japanflux_stage05bp child required')
    inputs=[a.stage04,a.helper]+[a.stage05d/(s+'_ERA5_audit.json') for s in JPF]+[a.stage05f/(s+'_impact.json') for s in EVENTS]
    observed={str(p):checked(p,HELPER_SHA if p==a.helper else None) for p in inputs}
    stages=stage04(a.stage04);helper=meta_helper(a.helper)
    for site in SOURCES:
        print('CHECK_ORIGINAL_SOURCE_SHA256',site,flush=True);checked(source(ROOT,site),SOURCES[site][1])
    jpf=[]
    for site in JPF:
        print('REVIEW_EXISTING_AND_METADATA',site,flush=True)
        sd=load_json(a.stage05d/(site+'_ERA5_audit.json'))
        sf=None if site=='JP-Api' else load_json(a.stage05f/(site+'_impact.json'))
        item=review_derived(site,stages[site],sd,sf)
        item['release_metadata']=helper.inspect(ROOT,site,SOURCES[site][0],256*1024*1024,4*1024*1024)
        jpf.append(item)
    special=[];all_anomalies=[]
    for site in SPECIAL:
        print('SCAN_SOURCE_COREVARS',site,flush=True)
        with zipfile.ZipFile(source(ROOT,site)) as z:
            infos=[i for i in z.infolist() if not i.is_dir() and safe(i.filename)]
            for cadence in (('HR','HH') if site=='JP-Tom' else ('HH',)):
                pattern='_COREVARS_'+cadence+'_'
                matches=[i for i in infos if pattern in PurePosixPath(i.filename).name and i.filename.lower().endswith('.csv')]
                if len(matches)!=1:raise ValueError('expected exactly one COREVARS '+site+' '+cadence)
                original=[x for x in stages[site]['files'] if x['member']==matches[0].filename]
                if len(original)!=1 or original[0].get('truncated_by_max_rows'):raise ValueError('Stage04 COREVARS identity')
                with z.open(matches[0]) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as f:
                    result,anomalies=diagnose(site,cadence,csv.DictReader(f),EXPECTED[(site,cadence)],original[0])
                result['source_member']=matches[0].filename;special.append(result);all_anomalies.extend(anomalies)
    tom={x['cadence']:x for x in special if x['site']=='JP-Tom'}
    if tom['HR']['last_interval'][1]!=tom['HH']['first_interval'][0]:raise ValueError('Tom HR-HH boundary mismatch')
    for site in SOURCES:
        print('RECHECK_ORIGINAL_SOURCE_SHA256',site,flush=True);checked(source(ROOT,site),SOURCES[site][1])
    for path in inputs:
        if checked(path)!=observed[str(path)]:raise ValueError('derived input changed during run')
    base.mkdir(exist_ok=True);a.out.mkdir()
    data=a.out/'special_derived_screen_events_HOLD.tsv'
    if not all_anomalies:raise ValueError('unexpected no special events')
    with data.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,all_anomalies[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(all_anomalies)
    summary={'stage':'05BP','status':'SIX_SITE_SOURCE_DIAGNOSTICS_ALL_HOLD','approved_replacements':0,
        'source_zip_sha256_pre_post':{s:SOURCES[s][1] for s in SOURCES},
        'derived_input_sha256_observed_pre_post':observed,
        'input_hash_note':'Stage04/05D/05F observed before/after, not previously pinned; semantic gates enforced',
        'jpf_four_site_reviews':jpf,'special_three_stream_reviews':special,
        'Tom_HR_HH_native_boundary_abuts':True,'special_unique_stream_timestamp_event_rows':len(all_anomalies),
        'output_sha256':{'special_derived_screen_events_HOLD.tsv':sha(data)},
        'limits':'Raw QC labels, units/time unverified; no scientific clearance; tiny tolerance classification is not a correction',
        'original_zip_forcing_pft_soil_model_slurm_modified':False}
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(summary,f,indent=2,ensure_ascii=False);f.write('\n')
    print('STAGE05BP COMPLETE; SIX SITES SCREENED; NO SITE SCIENCE APPROVED')
    print('OUTPUT',a.out)
    concise={'status':summary['status'],'approved_replacements':0,
       'source_zip_sha256_pre_post':summary['source_zip_sha256_pre_post'],
       'derived_input_sha256_observed_pre_post':observed,
       'jpf_four_site_reviews':[{**{k:x[k] for k in ('site','selected_source_rows','stage04_selected_threshold_flags','companion_ERA_screened_flagged_starts','companion_event_impact','missing_columns','status')},
                                'metadata_review':metadata_summary(x)} for x in jpf],
       'special_three_stream_reviews':[{k:x[k] for k in ('site','cadence','rows','first_interval','last_interval','counts','counts_by_native_year','field_minima','field_maxima','QC_raw_histograms','extremes','isolated_PA_SW_context','status')} for x in special],
       'Tom_HR_HH_native_boundary_abuts':True,'special_unique_stream_timestamp_event_rows':len(all_anomalies),
       'output_sha256':summary['output_sha256'],'summary_json_sha256':sha(a.out/'summary_HOLD.json'),'limits':summary['limits']}
    print(json.dumps(concise,indent=2,ensure_ascii=False))
if __name__=='__main__':main()

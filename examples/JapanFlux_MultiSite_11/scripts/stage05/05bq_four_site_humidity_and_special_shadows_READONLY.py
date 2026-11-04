#!/usr/bin/env python3
"""Four JPF humidity feasibility screen and special-site held shadow ledger."""
import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path,PurePosixPath

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
BP_SUMMARY_SHA='dbbd436cfb1ab40fca58ed6d7905a5477ccc92e55902f8d332df36e55069be5f'
BP_EVENTS_SHA='dbf35b76fea6623241239f94dfdb22277c4ae10e05d40f7bbc14ec0fcaa944d0'
SITES={
 'JP-Api':('JPF_JP-Api_FLUXNET_2000-2022_v1.3_r2','dab9de152210d4f95d88c79c7b9e67bd5ccde19fee86304bee093634f000342b',403248),
 'JP-Fhk':('JPF_JP-Fhk_FLUXNET_2006-2023_v1.3_r1','20abdd06ed23de7d599841e8ac64a21b2378a169deae6f3f891f6230e4a31667',315552),
 'JP-Spp':('JPF_JP-Spp_FLUXNET_2000-2018_v1.3_r1','6941f9bf4c6f7f2e80c9a7c991fde1b2c92bc3d7a111321ae50bd7d370d35aaf',333120),
 'JP-Tak':('JPF_JP-Tak_FLUXNET_1998-2021_v1.3_r1','cf1da393c026deb35dcc9b328bf5c7ae7ca9eea22dbbf8a095907e06373dc151',420768)}
EXPECTED={('JP-Tom','RH'):6583,('JP-Tgf','RH'):9493,('JP-Tom','VPD'):753,('JP-Tgf','VPD'):21,
          ('JP-Tom','P'):4322,('JP-Tgf','P'):3,('JP-Tgf','PA'):1,('JP-Tgf','SW'):1}
EVENTS={'PA_F':('200312312330',0.0),'SW_IN_F':('201512151430',-70.11575)}
EPS=1e-9
EVENT_ROW_COUNT=21177

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def check(path,expected):
    if path.is_symlink() or not path.is_file() or sha(path)!=expected:raise ValueError('missing/symlink/hash mismatch '+str(path))
def num(value):
    try:x=float(value)
    except (ValueError,TypeError):return None
    return x if math.isfinite(x) and x>-6999 else None
def stamp(s):
    if len(s)!=12 or not s.isdigit():raise ValueError('invalid timestamp')
    return datetime.strptime(s,'%Y%m%d%H%M')
def q_diagnostic(temp_c,pressure_kpa,vpd_hpa):
    """Bolton water es and q are approximate diagnostics, not forcing."""
    if not all(math.isfinite(v) for v in (temp_c,pressure_kpa,vpd_hpa)) or not -70<=temp_c<=60 or not 50<=pressure_kpa<=115:
        return 'INPUT_OUTSIDE_BROAD_DOMAIN',None,None
    es=6.112*math.exp(17.67*temp_c/(temp_c+243.5))
    vapour=es-vpd_hpa;p=pressure_kpa*10
    if vpd_hpa < -EPS:return 'NEGATIVE_VPD_OVER_SATURATION',es,vapour
    if -EPS<=vpd_hpa<0:return 'TINY_NEGATIVE_VPD',es,vapour
    if vapour<0:return 'NEGATIVE_VAPOUR_APPROX',es,vapour
    if vapour>=p or p-.378*vapour<=0:return 'VAPOUR_AT_OR_ABOVE_PRESSURE',es,vapour
    q=.622*vapour/(p-.378*vapour)
    if not 0<=q<1:return 'Q_OUTSIDE_ZERO_TO_ONE',es,vapour
    return 'APPROX_FEASIBLE_NOT_APPROVAL',es,q

def scan(site,path):
    pkg,expected,n_expected=SITES[site];check(path,expected)
    counts=Counter();qmin=None;qmax=None;examples=[];by_year=defaultdict(Counter)
    with zipfile.ZipFile(path) as outer:
        inner=[x for x in outer.infolist() if not x.is_dir() and x.filename==pkg+'.zip']
        if len(inner)!=1 or inner[0].file_size>256*1024*1024:raise ValueError('nested ZIP scope/cap')
        with outer.open(inner[0]) as source:
            raw=source.read(256*1024*1024+1)
        if len(raw)>256*1024*1024:raise ValueError('nested ZIP cap')
        with zipfile.ZipFile(io.BytesIO(raw)) as nested:
            members=[x for x in nested.infolist() if not x.is_dir() and '_FLUXMET_HH_' in PurePosixPath(x.filename).name and x.filename.lower().endswith('.csv')]
            if len(members)!=1:raise ValueError('FLUXMET HH member scope')
            member=members[0].filename
            with nested.open(members[0]) as binary,io.TextIOWrapper(binary,encoding='utf-8-sig',newline='') as text:
                reader=csv.DictReader(text);fields=reader.fieldnames or []
                required={'TIMESTAMP_START','TIMESTAMP_END','TA_F','PA_F','VPD_F','TA_F_QC','PA_F_QC','VPD_F_QC'}
                if len(fields)!=len(set(fields)) or not required.issubset(fields):raise ValueError('missing/duplicate met columns')
                prev=None;n=0
                for row in reader:
                    if None in row or any(x is None for x in row.values()):raise ValueError('row width mismatch')
                    s=row['TIMESTAMP_START'];e=row['TIMESTAMP_END']
                    if stamp(e)-stamp(s)!=timedelta(minutes=30) or (prev and s!=prev):raise ValueError('timestamp continuity')
                    prev=e;n+=1
                    t,p,v=map(num,(row['TA_F'],row['PA_F'],row['VPD_F']))
                    if t is None or p is None or v is None:category='MISSING_INPUT';es=x=None
                    else:category,es,x=q_diagnostic(t,p,v)
                    counts[category]+=1;by_year[s[:4]][category]+=1
                    if category=='APPROX_FEASIBLE_NOT_APPROVAL':
                        qmin=x if qmin is None else min(qmin,x);qmax=x if qmax is None else max(qmax,x)
                    elif len(examples)<20:
                        examples.append({'native_start':s,'native_end':e,'TA_F':row['TA_F'],'TA_F_QC_raw':row['TA_F_QC'],
                            'PA_F':row['PA_F'],'PA_F_QC_raw':row['PA_F_QC'],'VPD_F':row['VPD_F'],'VPD_F_QC_raw':row['VPD_F_QC'],
                            'category':category,'water_es_hPa':es,'third_result':x})
                if n!=n_expected:raise ValueError('JPF row count mismatch '+site)
    check(path,expected)
    return {'site':site,'rows':n,'member':member,'counts':dict(counts),'counts_by_native_year':{k:dict(v) for k,v in sorted(by_year.items())},
        'q_approx_min':qmin,'q_approx_max':qmax,'diagnostic_examples_first_20':examples,
        'status':'ASSUMED_WATER_FORMULA_ONLY_NOT_SITE_CLEARANCE'}

def events(path,summary):
    totals=Counter();seen=set();tiny=[];badrows={};rh_qc=defaultdict(Counter);annual=defaultdict(Counter)
    with path.open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f,delimiter='\t');hdr=reader.fieldnames or []
        needed={'site','cadence','native_start','native_end','status','RH_F','RH_F_QC_raw','VPD_F','VPD_F_QC_raw',
                'P_F','P_F_QC_raw','PA_F','PA_F_QC_raw','SW_IN_F','SW_IN_F_QC_raw'}
        if len(hdr)!=len(set(hdr)) or not needed.issubset(hdr):raise ValueError('event TSV schema')
        for r in reader:
            site=r['site'];t=stamp(r['native_start']);key=(site,r['cadence'],t)
            if site not in ('JP-Tom','JP-Tgf') or r['cadence']!='HH' or stamp(r['native_end'])-t!=timedelta(minutes=30) or key in seen or r['status']!='SCREEN_ONLY_NO_APPROVAL':raise ValueError('event scope/key')
            seen.add(key);rh=num(r['RH_F']);vpd=num(r['VPD_F']);p=num(r['P_F']);pa=num(r['PA_F']);sw=num(r['SW_IN_F'])
            if None in (rh,vpd,p,pa,sw):raise ValueError('missing selected event value')
            if rh>100:
                if vpd>=-EPS:raise ValueError('unexpected RH/VPD pairing')
                totals[(site,'RH')]+=1;annual[(site,t.year)]['RH_gt_100']+=1
                rh_qc[site][r['RH_F_QC_raw']]+=1
            if -EPS<=vpd<0:
                totals[(site,'VPD')]+=1
                tiny.append(shadow(r,'VPD_F',vpd,0.,'TINY_NUMERICAL_ZERO_SHADOW_NOT_APPROVED'))
            if p<0:
                if p<=-1e-12:raise ValueError('precipitation not within strict tiny window')
                totals[(site,'P')]+=1
                tiny.append(shadow(r,'P_F',p,0.,'TINY_NUMERICAL_ZERO_SHADOW_NOT_APPROVED'))
            for field,value,tag in (('PA_F',pa,'PA'),('SW_IN_F',sw,'SW')):
                if (field=='PA_F' and value<50) or (field=='SW_IN_F' and value<-20):
                    if site!='JP-Tgf' or r['native_start']!=EVENTS[field][0] or abs(value-EVENTS[field][1])>1e-8:raise ValueError('unexpected isolated candidate')
                    totals[(site,tag)]+=1;badrows[field]=r
    if len(seen)!=EVENT_ROW_COUNT or any(totals[k]!=n for k,n in EXPECTED.items()):raise ValueError('event population mismatch')
    x=[g for g in summary['special_three_stream_reviews'] if g['site']=='JP-Tgf' and g['cadence']=='HH']
    if len(x)!=1:raise ValueError('Tgf summary scope')
    contexts=x[0]['isolated_PA_SW_context'];decisions=[]
    for field in EVENTS:
        matches=[c for c in contexts if c['event_native_start']==EVENTS[field][0]]
        if len(matches)!=1 or matches[0]['left_context_censored'] or matches[0]['right_context_censored']:raise ValueError('isolated source context missing')
        rows=matches[0]['rows'];idx=[i for i,r in enumerate(rows) if r['native_start']==EVENTS[field][0]]
        if len(idx)!=1 or idx[0]==0 or idx[0]==len(rows)-1:raise ValueError('missing immediate neighbors')
        i=idx[0];left,mid,right=rows[i-1:i+2]
        if stamp(mid['native_start'])-stamp(left['native_start'])!=timedelta(minutes=30) or stamp(right['native_start'])-stamp(mid['native_start'])!=timedelta(minutes=30):raise ValueError('neighbor time')
        a=num(left[field]);b=num(right[field]);original=num(mid[field])
        if a is None or b is None or abs(original-EVENTS[field][1])>1e-8 or mid[field]!=badrows[field][field]:raise ValueError('neighbor source mismatch')
        proposed=(a+b)/2
        candidate=shadow(badrows[field],field,original,proposed,'ALTERNATE_LINEAR_SENSITIVITY_NOT_SELECTED_OR_APPROVED')
        candidate['left_value']=a;candidate['right_value']=b;candidate['left_QC_raw']=left[field+'_QC_raw'];candidate['right_QC_raw']=right[field+'_QC_raw']
        candidate['left_native_start']=left['native_start'];candidate['right_native_start']=right['native_start']
        decisions.append(candidate)
    return {'selected_event_rows':len(seen),'counts':{s+'_'+v:n for (s,v),n in sorted(totals.items())},
            'RH_gt_100_raw_QC':{s:dict(c) for s,c in rh_qc.items()},
            'RH_gt_100_by_native_year':{s+'_'+str(y):dict(c) for (s,y),c in sorted(annual.items())},
            'isolated_sensitivity_scenarios':decisions},tiny+decisions
def shadow(r,field,original,proposed,method):
    return {'site':r['site'],'cadence':r['cadence'],'native_start':r['native_start'],'native_end':r['native_end'],
        'field':field,'source_value':original,'source_QC_raw':r[field+'_QC_raw'],'shadow_value_NOT_APPROVED':proposed,
        'method':method,'left_native_start':'','left_value':'','left_QC_raw':'','right_native_start':'','right_value':'','right_QC_raw':'',
        'status':'HOLD_NO_APPROVED_REPLACEMENT'}
def selftest():
    status,es,q=q_diagnostic(20.,100.,10.)
    assert status=='APPROX_FEASIBLE_NOT_APPROVAL' and es>20 and 0<q<.02
    assert q_diagnostic(20.,100.,100.)[0]=='NEGATIVE_VAPOUR_APPROX'
    assert q_diagnostic(20.,100.,-1e-12)[0]=='TINY_NEGATIVE_VPD'
    assert abs((100.67+100.55)/2-100.61)<1e-8
    print('STAGE05BQ SELF-TEST PASS; HUMIDITY DIAGNOSTICS AND SHADOWS ONLY; ALL HOLD')
def run(a):
    base=Path.home()/'japanflux_stage05bq'
    if base.is_symlink() or (base.exists() and not base.is_dir()) or a.out.parent.resolve()!=base.resolve() or a.out.exists() or a.out.is_symlink():raise ValueError('fresh ~/japanflux_stage05bq child required')
    check(a.summary,BP_SUMMARY_SHA);check(a.events,BP_EVENTS_SHA)
    with a.summary.open(encoding='utf-8') as f:summary=json.load(f)
    if summary['status']!='SIX_SITE_SOURCE_DIAGNOSTICS_ALL_HOLD' or summary['approved_replacements']!=0 or summary['special_unique_stream_timestamp_event_rows']!=EVENT_ROW_COUNT:raise ValueError('BP summary scope/HOLD')
    for site,(pkg,h,n) in SITES.items():
        if summary['source_zip_sha256_pre_post'][site]!=h:raise ValueError('BP source hash mismatch')
    special,shadows=events(a.events,summary)
    jpf=[]
    for site,(pkg,h,n) in SITES.items():
        print('SCAN_JPF_HUMIDITY',site,flush=True)
        jpf.append(scan(site,ROOT/site/'forcing'/'packages'/(pkg+'.zip')))
    check(a.summary,BP_SUMMARY_SHA);check(a.events,BP_EVENTS_SHA)
    base.mkdir(exist_ok=True);a.out.mkdir()
    data=a.out/'special_shadow_candidates_HOLD.tsv'
    with data.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,shadows[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(shadows)
    report={'stage':'05BQ','status':'FOUR_SITE_HUMIDITY_AND_SPECIAL_SHADOWS_ALL_HOLD',
        'approved_replacements':0,'new_sites_scientifically_cleared':0,'BP_summary_sha256':BP_SUMMARY_SHA,'BP_event_sha256':BP_EVENTS_SHA,
        'jpf_four_humidity_diagnostics':jpf,'special_event_review':special,
        'shadow_rows':len(shadows),'shadow_sha256':sha(data),
        'shadow_note':'Zero for strictly tiny values and two exploratory bridge sensitivities; no RH/VPD supersaturation clip; no forcing writes',
        'formula_limits':'Bolton es over liquid water; VPD hPa and PA kPa assumed from release metadata; ice/units/support may change result; no q forcing produced',
        'original_zip_forcing_pft_soil_model_slurm_modified':False}
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print('STAGE05BQ COMPLETE; SHADOW ONLY; ZERO APPROVED; ALL HOLD')
    print('OUTPUT',a.out);print(json.dumps({**report,'summary_sha256':sha(a.out/'summary_HOLD.json')},indent=2))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    for name in ('summary','events','out'):p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(getattr(a,k) is None for k in ('summary','events','out')):p.error('summary, events and out required')
    run(a)
if __name__=='__main__':main()

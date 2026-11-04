#!/usr/bin/env python3
"""Stage05BS: JP-Tom/JP-Tgf humidity, tiny-negative and isolated-value forensics. Read-only; every candidate HOLD.

1. Regenerates the Stage05BP special-site event table, the Stage05BQ shadow table and the Stage05BQ summary
   with the repository 05BP/05BQ code (pinned by SHA-256) and compares their bytes with the operator-reported
   IRIDIS SHA-256s.
2. Audits the 5,099 tiny-negative zero shadows cell by cell against the original COREVARS streams: key, end
   offset, QC text, value window, complete two-way coverage and identity of every non-target cell.
3. RH/VPD/P forensics from ALLVARS channels (BADM heights), raw ERA5_HH, yearly AUXMETEO regressions, the
   Tgf PA=0 and SW=-70 rows, a clear-day clock test, and q impacts of HOLD-only RH scenarios.
No source, forcing, PFT, soil, case, Slurm or AD400 change; no value is approved.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import zipfile
from array import array
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath

IRIDIS_ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
SOURCES={'JP-Tom':('A20241210-015v200','ea3e5a3583b1defc722d44ee8343acdca6d902eb7e688268d44b2d47efcd193e',192864),
         'JP-Tgf':('A20241210-013_2.00_selected','d0476fff16f6bce8f53a0d640668dc28d0df7e6fbfda86565a26b247f267c204',368160)}
# JapanFlux2024 Table 1 coordinates (Ueyama et al. 2025, ESSD 17, 3807).
LOCATION={'JP-Tom':(42.698906,141.571488),'JP-Tgf':(36.11353,140.09488)}
PINS={'05bp':('05bp_six_site_meteorology_batch_READONLY.py','130bda27c320084cf61dc57fc61e1ff2055b3480cb54722c9f5d5be307b74264'),
      '05bq':('05bq_four_site_humidity_and_special_shadows_READONLY.py','12ff4ba55b6ff1b80d139815bd9d333c69199d083951229dd18eaf4181d31dd2'),
      '05br':('05br_nine_site_jpf_forcing_variable_qc_READONLY.py','67ecfb0dbfeda1599986de7d995aadf581570022450b5c5055fae6cc8a1f30cb')}
OPERATOR={'05bp_events':'dbf35b76fea6623241239f94dfdb22277c4ae10e05d40f7bbc14ec0fcaa944d0',
          '05bq_shadow':'c0fc10d15eb1a9e997ecf0f3b0d8aa6d40534e3c532682585ea74ae582d4ca35',
          '05bq_summary':'21b36f7a329da6a5d4a3994b988fbde5bf6d3ab7d020929a23951d35c0586675'}
TINY_COUNTS={('JP-Tom','P_F'):4322,('JP-Tom','VPD_F'):753,('JP-Tgf','P_F'):3,('JP-Tgf','VPD_F'):21}
CORE=('TA_F','TA_F_QC','RH_F','RH_F_QC','VPD_F','VPD_F_QC','PA_F','PA_F_QC','P_F','P_F_QC','SW_IN_F','SW_IN_F_QC','SW_IN_POT','LW_IN_F','WS_F')
CHANNELS={'JP-Tom':('TA_1_1_1','RH_1_1_1','SW_IN_1_1_1','P_RAIN_1_1_1','RH_ERA5','TA_ERA5','P_ERA5','P_RAIN_F'),
          'JP-Tgf':('TA_1_1_1','TA_1_2_1','TA_1_3_1','TA_2_1_1','TA_multiple','RH_1_1_1','RH_1_2_1','RH_1_3_1','RH_2_1_1','RH_multiple',
                    'PA_1_1_1','SW_IN_1_1_1','SW_IN_2_1_1','SW_IN_1_1_2','SW_IN_multiple','PPFD_1_1_1','SW_OUT_1_1_1','P_1_1_1',
                    'WS_1_1_1','WS_2_1_1','RH_ERA5','TA_ERA5','PA_ERA5','SW_IN_ERA5','P_ERA5')}
# BADM Instrument_Ops (submitted 2024-11-15): installation 2002-01-01, RH-Capac, unheated; heights in m.
RH_HEIGHT={'JP-Tgf':{'RH_1_1_1':29.5,'RH_1_2_1':12.5,'RH_1_3_1':1.6,'RH_2_1_1':2.0},
           'JP-Tom':{'RH_1_1_1':19.0}}  # Tom BADM Instrument_Ops (2024-10-30): TA/RH JPTOM-TE01 at 19 m since 1999-01-01
ERA_RAW=('TA_ERA5','RH_ERA5','VPD_ERA5','PA_ERA5','SW_ERA5','P_ERA5')
ISOLATED={'PA_F':'200312312330','SW_IN_F':'201512151430'}

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def check(path,expected):
    if path.is_symlink() or not path.is_file() or sha(path)!=expected:raise ValueError('missing/symlink/hash mismatch '+str(path))
def load_module(key):
    name,expected=PINS[key];path=Path(__file__).with_name(name);check(path,expected)
    spec=importlib.util.spec_from_file_location('stage'+key,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
def num(v):
    try:x=float(v)
    except (TypeError,ValueError):return math.nan
    return x if math.isfinite(x) and x>-9990 else math.nan
def finite(x):return not math.isnan(x)
def stamp(s):
    if len(s)!=12 or not s.isdigit():raise ValueError('invalid timestamp '+repr(s))
    return datetime.strptime(s,'%Y%m%d%H%M')
def source(root,layout,site):
    pkg=SOURCES[site][0]
    return root/site/'forcing'/'packages'/(pkg+'.zip') if layout=='iridis' else root/site/(pkg+'.zip')
def member(z,token,folder=None):
    found=[i for i in z.infolist() if not i.is_dir() and token in PurePosixPath(i.filename).name and i.filename.endswith('.csv')
           and 'ERA5_FILL' not in i.filename and (folder is None or ('/'+folder+'/') in '/'+i.filename)]
    if len(found)!=1:raise ValueError('member scope %s %s: %d'%(token,folder,len(found)))
    return found[0]

# ---------- 1. byte regeneration of 05BP events, 05BQ shadows and 05BQ summary ----------
def write_rows(path,rows):
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def regenerate(bp,bq,root,layout,out):
    special=[];anomalies=[]
    for site in ('JP-Tom','JP-Tgf'):
        path=source(root,layout,site);check(path,SOURCES[site][1])
        with zipfile.ZipFile(path) as z:
            infos=[i for i in z.infolist() if not i.is_dir() and bp.safe(i.filename)]
            for cadence in (('HR','HH') if site=='JP-Tom' else ('HH',)):
                pattern='_COREVARS_'+cadence+'_'
                matches=[i for i in infos if pattern in PurePosixPath(i.filename).name and i.filename.lower().endswith('.csv')]
                if len(matches)!=1:raise ValueError('expected exactly one COREVARS '+site+' '+cadence)
                with z.open(matches[0]) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as f:
                    result,rows=bp.diagnose(site,cadence,csv.DictReader(f),bp.EXPECTED[(site,cadence)],None)
                result['source_member']=matches[0].filename;special.append(result);anomalies.extend(rows)
    events=out/'regenerated_05bp_special_derived_screen_events_HOLD.tsv';write_rows(events,anomalies)
    review,shadows=bq.events(events,{'special_three_stream_reviews':special})
    data=out/'regenerated_05bq_special_shadow_candidates_HOLD.tsv';write_rows(data,shadows)
    jpf=[]
    for site,(pkg,h,n) in bq.SITES.items():
        print('STAGE05BS REGENERATE_05BQ_JPF_SCAN',site,flush=True)
        p=root/site/'forcing'/'packages'/(pkg+'.zip') if layout=='iridis' else root/site/(pkg+'.zip')
        jpf.append(bq.scan(site,p))
    # Field order and strings copied from 05BQ run(); any drift changes the hash and is reported, not hidden.
    report={'stage':'05BQ','status':'FOUR_SITE_HUMIDITY_AND_SPECIAL_SHADOWS_ALL_HOLD',
        'approved_replacements':0,'new_sites_scientifically_cleared':0,'BP_summary_sha256':bq.BP_SUMMARY_SHA,'BP_event_sha256':bq.BP_EVENTS_SHA,
        'jpf_four_humidity_diagnostics':jpf,'special_event_review':review,
        'shadow_rows':len(shadows),'shadow_sha256':sha(data),
        'shadow_note':'Zero for strictly tiny values and two exploratory bridge sensitivities; no RH/VPD supersaturation clip; no forcing writes',
        'formula_limits':'Bolton es over liquid water; VPD hPa and PA kPa assumed from release metadata; ice/units/support may change result; no q forcing produced',
        'original_zip_forcing_pft_soil_model_slurm_modified':False}
    summ=out/'regenerated_05bq_summary_HOLD.json'
    with summ.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    got={'05bp_events':sha(events),'05bq_shadow':sha(data),'05bq_summary':sha(summ)}
    return {'regenerated_sha256':got,'operator_reported_sha256':OPERATOR,
            'byte_identical':{k:got[k]==OPERATOR[k] for k in got},'event_rows':len(anomalies),'shadow_rows':len(shadows)},shadows

# ---------- 2. cell-level audit of the tiny-negative zero shadows ----------
def audit_tiny(site,z,shadows,era):
    tiny=[s for s in shadows if s['site']==site and s['method']=='TINY_NUMERICAL_ZERO_SHADOW_NOT_APPROVED']
    target={}
    for s in tiny:
        k=(s['native_start'],s['field'])
        if k in target or s['cadence']!='HH' or s['status']!='HOLD_NO_APPROVED_REPLACEMENT' or float(s['shadow_value_NOT_APPROVED'])!=0.:raise ValueError('shadow key/status')
        if stamp(s['native_end'])-stamp(s['native_start'])!=timedelta(minutes=30):raise ValueError('shadow end offset')
        target[k]=s
    found=set();changed=0;h0=hashlib.sha256();h1=hashlib.sha256();qc=defaultdict(Counter);era_sign=Counter();rh_at_vpd=Counter();minmax={}
    with z.open(member(z,'_COREVARS_HH_','COREVARS')) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
        reader=csv.reader(text);header=next(reader);col={c:header.index(c) for c in header}
        for row in reader:
            if len(row)!=len(header):raise ValueError('row width')
            start=row[col['TIMESTAMP_START']];applied=list(row)
            p=num(row[col['P_F']]);v=num(row[col['VPD_F']])
            rule=[]
            if finite(p) and p<0:rule.append('P_F')
            if finite(v) and -1e-9<=v<0:rule.append('VPD_F')
            for f in rule:
                k=(start,f);found.add(k)
                if k not in target:raise ValueError('source tiny cell without shadow '+repr(k))
                s=target[k];x=num(row[col[f]])
                if float(s['source_value'])!=x or s['source_QC_raw']!=row[col[f+'_QC']] or s['native_end']!=row[col['TIMESTAMP_END']]:raise ValueError('shadow source mismatch '+repr(k))
                if f=='P_F' and not -1e-12<x<0:raise ValueError('P outside tiny window')
                applied[col[f]]='0';changed+=1;qc[f][row[col[f+'_QC']]]+=1
                lo,hi=minmax.get(f,(x,x));minmax[f]=(min(lo,x),max(hi,x))
                if f=='P_F':
                    e=era.get(start)
                    era_sign['ERA5_P_missing' if e is None or not finite(e[5]) else 'ERA5_P_negative' if e[5]<0 else 'ERA5_P_zero' if e[5]==0 else 'ERA5_P_positive']+=1
                else:rh_at_vpd[row[col['RH_F']]]+=1
            h0.update(('\t'.join(row)+'\n').encode());h1.update(('\t'.join(applied)+'\n').encode())
    if found!=set(target):raise ValueError('shadow set differs from source rule set')
    counts=Counter(f for _,f in target)
    for f,n in counts.items():
        if TINY_COUNTS[(site,f)]!=n:raise ValueError('tiny count mismatch')
    return {'shadow_cells':len(target),'source_rule_cells':len(found),'changed_cells_in_applied_copy':changed,
            'non_target_cells_identical':changed==len(target),'by_field':dict(sorted(counts.items())),
            'source_QC_text_by_field':{f:dict(sorted(c.items())) for f,c in sorted(qc.items())},
            'value_min_max_by_field':{f:[repr(a),repr(b)] for f,(a,b) in sorted(minmax.items())},
            'raw_ERA5_P_sign_at_tiny_P_rows':dict(sorted(era_sign.items())),
            'RH_F_text_at_tiny_VPD_rows_top10':dict(sorted(rh_at_vpd.items(),key=lambda kv:(-kv[1],kv[0]))[:10]),
            'source_stream_sha256':h0.hexdigest(),'shadow_applied_stream_sha256_NOT_WRITTEN':h1.hexdigest()}

# ---------- 3. forensics ----------
def load_core(z,site,n_expected):
    with z.open(member(z,'_COREVARS_HH_','COREVARS')) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
        reader=csv.DictReader(text);times=[];d={c:array('d') for c in CORE};prev=None
        for r in reader:
            s=stamp(r['TIMESTAMP_START'])
            if stamp(r['TIMESTAMP_END'])-s!=timedelta(minutes=30) or (prev and s!=prev+timedelta(minutes=30)):raise ValueError('core continuity')
            prev=s;times.append(r['TIMESTAMP_START'])
            for c in CORE:d[c].append(num(r[c]))
    if len(times)!=n_expected:raise ValueError('core rows')
    return times,d
def load_allvars(z,site,times):
    with z.open(member(z,'_ALLVARS_HH_','ALLVARS')) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
        reader=csv.DictReader(text);missing=[c for c in CHANNELS[site] if c not in (reader.fieldnames or [])]
        if missing:raise ValueError('ALLVARS missing '+','.join(missing))
        d={c:array('d') for c in CHANNELS[site]};i=0
        for r in reader:
            if i>=len(times) or r['TIMESTAMP_START']!=times[i]:raise ValueError('ALLVARS/COREVARS timestamps differ')
            for c in CHANNELS[site]:d[c].append(num(r[c]))
            i+=1
    if i!=len(times):raise ValueError('ALLVARS rows')
    return d
def load_era(z,first,last):
    out={}
    with z.open(member(z,'_ERA5_HH_','ALLVARS')) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
        for r in csv.DictReader(text):
            s=r['TIMESTAMP_START']
            if first<=s<=last:out[s]=tuple(num(r[c]) for c in ERA_RAW)
    return out
def load_aux(z):
    out=defaultdict(dict)
    with z.open(member(z,'_COREVARS_AUXMETEO_','COREVARS')) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
        for r in csv.DictReader(text):
            if r['VARIABLE']=='RH':out[r['TIMESTAMP']][r['PARAMETER']]=num(r['VALUE'])
    return out

def humidity_forensics(br,site,times,d,ch,era,aux):
    n=len(times);years=[int(t[:4]) for t in times]
    by=defaultdict(Counter);rhq0=defaultdict(list);bias=defaultdict(lambda:defaultdict(list))
    bins=((0,60),(60,80),(80,90),(90,95),(95,101))
    for i in range(n):
        rh=d['RH_F'][i];q=d['RH_F_QC'][i];y=years[i]
        if not finite(rh):by[y]['missing']+=1;continue
        tag='QC%d'%q if finite(q) else 'QC?';by[y][tag]+=1
        if rh>100:by[y]['RH_gt_100_'+tag]+=1
        if q==0:
            rhq0[y].append(rh)
            e=era.get(times[i])
            if e and finite(e[1]):
                for lo,hi in bins:
                    if lo<=e[1]<hi:bias[y]['%d_%d'%(lo,hi)].append(rh-e[1])
                bias[y]['all'].append(rh-e[1])
    table=[]
    for y in sorted(by):
        a=aux.get(str(y),{});s=a.get('ERA_SLOPE');b=a.get('ERA_INTERCEPT')
        v=rhq0.get(y,[])
        extra=set(by[y])-{p+t for p in ('','RH_gt_100_') for t in ('QC0','QC1','QC2','QC3')}-{'missing'}
        if extra:raise ValueError('unexpected RH QC classes '+repr(sorted(extra)))
        table.append({'site':site,'year':y,**{p+t:by[y][p+t] for p in ('','RH_gt_100_') for t in ('QC0','QC1','QC2','QC3')},'missing':by[y]['missing'],
            'RH_QC0_max':br.r6(max(v)) if v else None,'RH_QC0_p99':br.r6(br.quant(v,.99)),'RH_QC0_frac_ge_99':br.r6(sum(1 for x in v if x>=99)/len(v)) if v else None,
            'AUX_RH_slope':s,'AUX_RH_intercept':b,'AUX_corrected_ERA_RH_at_90':br.r6(s*90+b) if s is not None and finite(s) else None,
            'AUX_corrected_ERA_RH_at_95':br.r6(s*95+b) if s is not None and finite(s) else None,
            **{'median_RH_QC0_minus_rawERA5_'+k:br.r6(br.quant(bias[y][k],.5)) for k in ['all']+['%d_%d'%bb for bb in bins]},
            **{'n_RH_QC0_rawERA5_'+k:len(bias[y][k]) for k in ['all']+['%d_%d'%bb for bb in bins]}})
    # RH>100 rows
    hi=[i for i in range(n) if finite(d['RH_F'][i]) and d['RH_F'][i]>100]
    hist=Counter(int(math.floor(d['RH_F'][i])) for i in hi);month=Counter(times[i][4:6] for i in hi);hour=Counter(times[i][8:10] for i in hi)
    chan={}
    for c in [x for x in ch if x.startswith('RH_') and x!='RH_ERA5']:
        vals=[ch[c][i] for i in hi]
        chan[c]={'available':sum(1 for x in vals if finite(x)),'gt_100':sum(1 for x in vals if finite(x) and x>100),
                 'equal_RH_F_within_1e-6':sum(1 for i in hi if finite(ch[c][i]) and abs(ch[c][i]-d['RH_F'][i])<1e-6),
                 'height_m_BADM':RH_HEIGHT[site].get(c)}
    wet=sum(1 for i in hi if finite(d['P_F'][i]) and d['P_F'][i]>0)
    ta=[d['TA_F'][i] for i in hi if finite(d['TA_F'][i])]
    # Linear-RH-regression test for QC1 rows. The paper fills RH from gap-filled vapour pressure and TA, so a low
    # match rate is expected and only rules out a direct RH regression; it is not evidence of a defect.
    mech={}
    for lag in (-2,-1,0,1,2):
        ok=tot=0
        for i in range(n):
            if d['RH_F_QC'][i]!=1 or not finite(d['RH_F'][i]):continue
            j=i+lag
            if not 0<=j<n:continue
            e=era.get(times[j]);a=aux.get(times[i][:4],{})
            if not e or not finite(e[1]) or 'ERA_SLOPE' not in a:continue
            tot+=1;ok+=abs(d['RH_F'][i]-(a['ERA_SLOPE']*e[1]+a['ERA_INTERCEPT']))<.05
        mech[str(lag)]={'QC1_rows_tested':tot,'match_within_0.05pct':ok}
    # VPD formula from RH_F/VPD_F (QC0 both)
    ratios=defaultdict(list)
    for i in range(n):
        rh=d['RH_F'][i];v=d['VPD_F'][i];t=d['TA_F'][i]
        if d['RH_F_QC'][i]==0 and d['VPD_F_QC'][i]==0 and finite(t) and 10<rh<90 and v>1:
            for f in br.ES_FORMULAS:ratios[f].append(abs(math.log(v/(1-rh/100)/br.es(t,f))))
    score={f:br.r6(br.quant(v,.5)) for f,v in ratios.items()}
    best=min(score,key=score.get) if score else 'oneflux_qc_auto'
    res=[abs(d['VPD_F'][i]-br.es(d['TA_F'][i],best)*(1-d['RH_F'][i]/100)) for i in hi if finite(d['VPD_F'][i]) and finite(d['TA_F'][i])]
    return {'by_year':table,'RH_gt_100_rows':len(hi),'RH_gt_100_floor_histogram':{str(k):v for k,v in sorted(hist.items())},
            'RH_gt_100_by_month':dict(sorted(month.items())),'RH_gt_100_by_hour':dict(sorted(hour.items())),
            'RH_gt_100_with_P_F_positive':wet,'RH_gt_100_TA_F_summary':br.summary(ta),'RH_gt_100_channels':chan,
            'QC1_RH_linear_regression_of_rawERA5_test_by_lag_halfhours':mech,
            'VPD_formula_median_abs_log_ratio':score,'VPD_best_formula':best,
            'RH_gt_100_VPD_minus_es_best_times_1_minus_RH_abs':br.summary(res)},best

def tgf_channels(br,times,ch):
    years=[int(t[:4]) for t in times];out=defaultdict(dict)
    pairs={'RH_2_1_1_minus_RH_1_3_1':('RH_2_1_1','RH_1_3_1'),'RH_1_1_1_minus_RH_1_3_1':('RH_1_1_1','RH_1_3_1'),
           'RH_1_2_1_minus_RH_1_3_1':('RH_1_2_1','RH_1_3_1'),'RH_multiple_minus_RH_1_3_1':('RH_multiple','RH_1_3_1')}
    acc=defaultdict(lambda:defaultdict(list));cnt=defaultdict(lambda:defaultdict(Counter))
    for i in range(len(times)):
        y=years[i]
        for c in ('RH_1_1_1','RH_1_2_1','RH_1_3_1','RH_2_1_1','RH_multiple'):
            x=ch[c][i]
            if finite(x):
                cnt[y][c]['n']+=1
                if x>100:cnt[y][c]['gt_100']+=1
                if x>=99:cnt[y][c]['ge_99']+=1
        for k,(a,b) in pairs.items():
            if finite(ch[a][i]) and finite(ch[b][i]):acc[y][k].append(ch[a][i]-ch[b][i])
    for y in sorted(cnt):
        out[str(y)]={'counts':{c:dict(sorted(v.items())) for c,v in sorted(cnt[y].items())},
                     'median_differences':{k:br.r6(br.quant(v,.5)) for k,v in sorted(acc[y].items())}}
    return dict(out)

def isolated(times,d,ch,era,site):
    rows=[]
    for field,t0 in ISOLATED.items():
        i0=times.index(t0)
        for i in range(i0-3,i0+4):
            r={'site':site,'event_field':field,'event_native_start':t0,'native_start':times[i],'offset_halfhours':i-i0}
            for c in CORE:r[c]=repr(d[c][i])
            for c in CHANNELS[site]:r['ALLVARS_'+c]=repr(ch[c][i])
            e=era.get(times[i])
            for k,c in enumerate(ERA_RAW):r['rawERA5_'+c]=repr(e[k]) if e else 'nan'
            rows.append(r)
    return rows

def zero_scan(times,d,ch=None):
    exact=[];yearend=[];raw=[c for c in ('TA_1_1_1','TA_1_3_1','TA_2_1_1','RH_1_1_1','RH_1_3_1','PA_1_1_1') if ch and c in ch]
    for i,t in enumerate(times):
        if d['PA_F'][i]==0 or (d['TA_F'][i]==0 and d['RH_F'][i]==100 and d['VPD_F'][i]==0):
            exact.append([t,d['TA_F'][i],d['TA_F_QC'][i],d['RH_F'][i],d['RH_F_QC'][i],d['VPD_F'][i],d['PA_F'][i],d['PA_F_QC'][i],
                          d['TA_F'][i-1] if i else None,d['TA_F'][i+1] if i+1<len(times) else None]+[[c,ch[c][i]] for c in raw])
        if t.endswith('12312330'):
            yearend.append([t,d['TA_F'][i],d['TA_F_QC'][i],d['RH_F'][i],d['VPD_F'][i],d['PA_F'][i],d['PA_F_QC'][i]])
    return {'exact_zero_PA_or_TA0_RH100_VPD0_rows':exact,'dec31_2330_rows':yearend}

def clock(br,times,d,era,site):
    lat,lon=LOCATION[site];first=stamp(times[0]);n=len(times)
    toa=[br.toa_mean(first+timedelta(minutes=30*i),lat,lon,9.) for i in range(n)]
    per=defaultdict(list);by_year=defaultdict(list)
    for start in range(0,n-47,48):
        day=range(start,start+48);top=[toa[i] for i in day]
        lit=[i for i in day if toa[i]>0]
        if sum(top)<=0 or any(d['SW_IN_F_QC'][i]!=0 or not finite(d['SW_IN_F'][i]) for i in lit):continue
        sw=[d['SW_IN_F'][i] if finite(d['SW_IN_F'][i]) else 0. for i in day]
        if sum(sw)/sum(top)<.6:continue
        c0=br.centroid(top);c=br.centroid([max(x,0.) for x in sw]);per['SW_IN_F'].append(c-c0);by_year[times[start][:4]].append(c-c0)
        pot=br.centroid([max(d['SW_IN_POT'][i],0.) if finite(d['SW_IN_POT'][i]) else 0. for i in day])
        if pot is not None:per['SW_IN_POT'].append(pot-c0)
        ev=[era.get(times[i]) for i in day]
        if all(e is not None and finite(e[4]) for e in ev):per['raw_ERA5_SW'].append(br.centroid([max(e[4],0.) for e in ev])-c0)
    return {'location_JapanFlux2024_Table1':[lat,lon],'expected_offset_min_if_local_mean_solar_time':br.r6(4*(lon-135)),
            'centroid_offset_min_vs_UTCplus9_TOA':{k:br.summary(v) for k,v in sorted(per.items())},
            'SW_IN_F_offset_by_year':{y:br.summary(v) for y,v in sorted(by_year.items())}}

def clock_hr(br,z,site):
    """Hourly COREVARS (JP-Tom 1999-2003) clear-day SW centroid versus UTC+9 TOA; bins are 60 min."""
    lat,lon=LOCATION[site];off=[];by_year=defaultdict(list)
    with z.open(member(z,'_COREVARS_HR_','COREVARS')) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
        rows=list(csv.DictReader(text))
    for start in range(0,len(rows)-23,24):
        day=rows[start:start+24]
        if day[0]['TIMESTAMP_START'][8:]!='0000':raise ValueError('HR day alignment')
        t0=stamp(day[0]['TIMESTAMP_START'])
        top=[(br.toa_mean(t0+timedelta(hours=k),lat,lon,9.)+br.toa_mean(t0+timedelta(hours=k,minutes=30),lat,lon,9.))/2 for k in range(24)]
        lit=[k for k in range(24) if top[k]>0];sw=[num(r['SW_IN_F']) for r in day]
        if any(num(day[k]['SW_IN_F_QC'])!=0 or not finite(sw[k]) for k in lit):continue
        sw=[max(x,0.) if finite(x) else 0. for x in sw]
        if sum(sw)/sum(top)<.6:continue
        c=lambda v:sum(x*(60*k+30) for k,x in enumerate(v))/sum(v)
        off.append(c(sw)-c(top));by_year[day[0]['TIMESTAMP_START'][:4]].append(off[-1])
    return {'SW_IN_F_HR_centroid_offset_min_vs_UTCplus9_TOA':br.summary(off),'by_year':{y:br.summary(v) for y,v in sorted(by_year.items())}}

def scenarios(br,site,times,d,era,best,affected_threshold=100):
    """HOLD-only q impacts: S1 caps RH at 100 (VPD>=0); S2 removes a year offset in high-humidity tower-minus-ERA5 RH."""
    n=len(times);years=[int(t[:4]) for t in times];hi=Counter(years[i] for i in range(n) if finite(d['RH_F'][i]) and d['RH_F'][i]>100)
    affected=sorted(y for y,c in hi.items() if c>=affected_threshold);ref=sorted(set(years)-set(hi))
    def hb(ys):
        v=[]
        for i in range(n):
            if years[i] in ys and d['RH_F_QC'][i]==0 and finite(d['RH_F'][i]):
                e=era.get(times[i])
                if e and finite(e[1]) and e[1]>=90:v.append(d['RH_F'][i]-e[1])
        return br.quant(v,.5),len(v)
    ref_med,ref_n=hb(set(ref))
    def q_of(t,p,vpd):
        e=br.es(t,best)-vpd;return .622*e/(p*10-.378*e)
    rows=[]
    for y in affected:
        ym,yn=hb({y});off=None if ym is None or ref_med is None else ym-ref_med
        s1=[];s2=[];cap0=0;cnt=0;dat=[]
        for i in range(n):
            if years[i]!=y:continue
            t=d['TA_F'][i];p=d['PA_F'][i];v=d['VPD_F'][i];rh=d['RH_F'][i]
            if not (finite(t) and finite(p) and finite(v) and finite(rh)):continue
            q0=q_of(t,p,v);cnt+=1
            ed=br.datm_esat_hpa(t);qs=.622*ed/(p*10-.378*ed)
            if q0>qs:cap0+=1
            s1.append(q_of(t,p,max(v,0.))-q0)
            if off is not None and d['RH_F_QC'][i]==0:
                rh2=min(rh-off,100.);s2.append(q_of(t,p,br.es(t,best)*(1-rh2/100))-q0)
        rows.append({'site':site,'year':y,'rows':cnt,'RH_gt_100_rows':hi[y],'reference_years':','.join(map(str,ref)),
            'reference_high_humidity_median_RH_minus_ERA5':br.r6(ref_med),'reference_n':ref_n,
            'year_high_humidity_median_RH_minus_ERA5':br.r6(ym),'year_n':yn,'S2_offset_pct_EXPLORATORY':br.r6(off),
            'S0_rows_DATM_would_cap_to_qsat':cap0,
            'S1_cap_RH100_changed_rows':sum(1 for x in s1 if x!=0),'S1_mean_dq_gkg_all_rows':br.r6(1000*sum(s1)/len(s1)) if s1 else None,
            'S1_min_dq_gkg':br.r6(1000*min(s1)) if s1 else None,
            'S2_QC0_rows':len(s2),'S2_mean_dq_gkg_QC0_rows':br.r6(1000*sum(s2)/len(s2)) if s2 else None,
            'status':'HOLD_SCENARIO_ONLY_NOT_SELECTED_OR_APPROVED'})
    return rows

def selftest():
    assert stamp('200312312330')+timedelta(minutes=30)==stamp('200401010000')
    assert sha_bytes(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    assert num('-9999')!=num('-9999') and num('-1.3e-15')==-1.3e-15
    print('STAGE05BS SELF-TEST PASS; TOM/TGF FORENSICS READ-ONLY; ZERO APPROVALS')

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out under an existing real directory required')
    bp=load_module('05bp');bq=load_module('05bq');br=load_module('05br')
    a.out.mkdir()
    regen,shadows=regenerate(bp,bq,a.root,a.layout,a.out)
    print('STAGE05BS REGENERATION',json.dumps(regen['byte_identical']),flush=True)
    report={'stage':'05BS','status':'TOM_TGF_FORENSICS_ALL_HOLD','approved_replacements':0,'regeneration':regen,'sites':{}}
    iso_rows=[];scen_rows=[];year_rows=[]
    for site in ('JP-Tom','JP-Tgf'):
        print('STAGE05BS FORENSICS',site,flush=True)
        path=source(a.root,a.layout,site);check(path,SOURCES[site][1])
        with zipfile.ZipFile(path) as z:
            times,d=load_core(z,site,SOURCES[site][2]);ch=load_allvars(z,site,times);era=load_era(z,times[0],times[-1]);aux=load_aux(z)
            tiny=audit_tiny(site,z,shadows,era);hr_clock=clock_hr(br,z,site) if site=='JP-Tom' else None
        check(path,SOURCES[site][1])
        hum,best=humidity_forensics(br,site,times,d,ch,era,aux);year_rows.extend(hum.pop('by_year'))
        item={'rows':len(times),'first':times[0],'last':times[-1],'tiny_negative_shadow_audit':tiny,'humidity':hum,
              'zero_scan':zero_scan(times,d,ch),'clock':clock(br,times,d,era,site),'clock_HR_1999_2003':hr_clock,'source_zip_sha256_pre_post':SOURCES[site][1]}
        if site=='JP-Tgf':
            item['rh_channels_by_year']=tgf_channels(br,times,ch);iso_rows.extend(isolated(times,d,ch,era,site))
        scen_rows.extend(scenarios(br,site,times,d,era,best))
        report['sites'][site]=item
    # Fingerprint first: the scenario table uses exp(), so its bytes may differ in the last digit between libm builds.
    report['fingerprint_integers_strings']=br.fingerprint(report);report['output_tsv_sha256']={}
    for name,rows in (('isolated_tgf_windows_HOLD.tsv',iso_rows),('rh_scenarios_by_year_HOLD.tsv',scen_rows),('rh_by_year_HOLD.tsv',year_rows)):
        write_rows(a.out/name,rows);report['output_tsv_sha256'][name]=sha(a.out/name)
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE05BS COMPLETE; FORENSICS ONLY; ZERO APPROVED; ALL HOLD')
    print('OUTPUT',a.out)
    print(json.dumps({'regeneration':regen,'fingerprint':report['fingerprint_integers_strings'],'summary_sha256':sha(a.out/'summary_HOLD.json')},indent=1))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--root',type=Path,default=IRIDIS_ROOT);p.add_argument('--layout',choices=('iridis','local'),default='iridis')
    p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if a.out is None:p.error('--out required')
    run(a)
if __name__=='__main__':main()

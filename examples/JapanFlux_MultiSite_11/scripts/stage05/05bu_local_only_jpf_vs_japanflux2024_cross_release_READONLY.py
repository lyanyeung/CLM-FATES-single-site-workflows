#!/usr/bin/env python3
"""Stage05BU (LOCAL-ONLY evidence): JPF FLUXNET v1.3 versus JapanFlux2024 v2.00 for the eight JPF sites whose
JapanFlux2024 packages exist on the operator workstation (not on IRIDIS6). Read-only; nothing approved.

Per site: (1) same-release JPF P_ERA versus JapanFlux2024 raw ERA5 P_ERA5 at -2..+2 half-hour lags (total
ratio and share of wet half-hours within 1 % of 3.6); (2) JPF TA_F versus JapanFlux2024 TA_F, both QC0,
first-difference correlation by lag and median absolute difference at lag 0; (3) clear-day SW_IN_F centroid of
the JapanFlux2024 COREVARS versus UTC+9 TOA. Every package is SHA-256 checked before and after.
The A20241022-030 package in the operator's JP-Tmd folder is JP-KaL, not JP-Tmd, and is deliberately excluded.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import zipfile
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

JPF={'JP-Api':('JPF_JP-Api_FLUXNET_2000-2022_v1.3_r2','dab9de152210d4f95d88c79c7b9e67bd5ccde19fee86304bee093634f000342b'),
 'JP-Fhk':('JPF_JP-Fhk_FLUXNET_2006-2023_v1.3_r1','20abdd06ed23de7d599841e8ac64a21b2378a169deae6f3f891f6230e4a31667'),
 'JP-Fjy':('JPF_JP-Fjy_FLUXNET_2001-2021_v1.3_r1','205660bb8203bf7b16466041183ec9a1598f609727ef042ff4bceb800da949b9'),
 'JP-Khw':('JPF_JP-Khw_FLUXNET_2000-2021_v1.3_r1','712ab4695704a695c28056eb0cfae0697af8a673228407dbc856088ad83bac79'),
 'JP-Spp':('JPF_JP-Spp_FLUXNET_2000-2018_v1.3_r1','6941f9bf4c6f7f2e80c9a7c991fde1b2c92bc3d7a111321ae50bd7d370d35aaf'),
 'JP-Tak':('JPF_JP-Tak_FLUXNET_1998-2021_v1.3_r1','cf1da393c026deb35dcc9b328bf5c7ae7ca9eea22dbbf8a095907e06373dc151'),
 'JP-Tef':('JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1','315c825b64669aa03daff1d969f58a0a1cf3b574c43400ea1f84588df7f6d684'),
 'JP-Yms':('JPF_JP-Yms_FLUXNET_2000-2023_v1.3_r1','6bda3beb4fd9b580ef036e4b50f9c3162ca17b82b2b28466820e665bdedbf6f7')}
JF2024={'JP-Api':('A20241022-001_2.00_selected','9508400c085aa3055cc153f5201dc84b3eae2f538b448cf094e57415eacf0641'),
 'JP-Fhk':('A20241210-002_2.00_selected','81edc48f219ff68f42793b90bac0b32f7addcba4b80e54faf969b7945f80f06d'),
 'JP-Fjy':('A20241022-002_2.00_selected','bdbd27fd4e95fef34081dbfc9be27b00f73fddb1b15e54e01514327ddd26864b'),
 'JP-Khw':('A20241210-005_2.00_selected','7331f721c8cc472b4b4d3cc39dc3688f7bf3e547f6b481243f0dd571bd2ae602'),
 'JP-Spp':('A20241210-010_2.00_selected','8021fbc84c6f6ff168e72234a280c3d33fd106071244788fa9264724b9ff344c'),
 'JP-Tak':('A20241022-021_2.00_selected','d0c5c72b15fa6eaf6a3217a622f537c5a7381c7c5301752b64cd9e2506e747f0'),
 'JP-Tef':('A20241210-016_2.00_selected','164b417569b0fa5b57316091556de922be7fd44b3d8b9921710429d41e137d36'),
 'JP-Yms':('A20241022-024_2.00_selected','a112e8650592040b92698280416ac4b308a214ff1c5af8b8ee8d6e1ecf55d37d')}
BR_PIN=('05br_nine_site_jpf_forcing_variable_qc_READONLY.py','67ecfb0dbfeda1599986de7d995aadf581570022450b5c5055fae6cc8a1f30cb')
LAGS=(-2,-1,0,1,2)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def check(path,expected):
    if path.is_symlink() or not path.is_file() or sha(path)!=expected:raise ValueError('missing/symlink/hash mismatch '+str(path))
def num(v):
    try:x=float(v)
    except (TypeError,ValueError):return None
    return x if math.isfinite(x) and x>-9990 else None
def load_br():
    path=Path(__file__).with_name(BR_PIN[0]);check(path,BR_PIN[1])
    spec=importlib.util.spec_from_file_location('stage05br',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def csv_rows(z,name):
    with z.open(name) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:yield from csv.DictReader(text)
def one(names,token,folder):
    found=[n for n in names if token in n.rsplit('/',1)[-1] and ('/'+folder+'/') in '/'+n and 'ERA5_FILL' not in n and n.endswith('.csv')]
    if len(found)!=1:raise ValueError('member scope '+token)
    return found[0]

def load_jpf(path,pkg):
    with zipfile.ZipFile(path) as outer:raw=outer.read(pkg+'.zip')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist();met=[n for n in names if '_FLUXMET_HH_' in n];era=[n for n in names if '_ERA5_HH_' in n]
        if len(met)!=1 or len(era)!=1:raise ValueError('JPF member scope')
        ta={r['TIMESTAMP_START']:num(r['TA_F']) for r in csv_rows(z,met[0]) if r['TA_F_QC']=='0'}
        p={r['TIMESTAMP_START']:num(r['P_ERA']) for r in csv_rows(z,era[0])}
    return ta,p
def load_jf(path,site):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        core=list(csv_rows(z,one(names,'_COREVARS_HH_','COREVARS')))
        p={r['TIMESTAMP_START']:num(r['P_ERA5']) for r in csv_rows(z,one(names,'_ERA5_HH_','ALLVARS'))}
    return core,p

def p_ratio(a,b):
    keys=sorted(set(a)&set(b));out={}
    for lag in LAGS:
        sa=sb=0.;wet=0;near=0
        for i in range(max(0,-lag),len(keys)-max(0,lag)):
            x=a[keys[i]];y=b[keys[i+lag]]
            if x is None or y is None:continue
            sa+=x;sb+=y
            if y>.2:wet+=1;near+=abs(x/y/3.6-1)<.01
        out[str(lag)]={'total_ratio_JPF_over_JF2024_raw':round(sa/sb,6) if sb else None,'wet_halfhours':wet,'share_within_1pct_of_3.6':round(near/wet,6) if wet else None}
    return out
def ta_lag(a,core):
    b={r['TIMESTAMP_START']:num(r['TA_F']) for r in core if r['TA_F_QC'] in ('0','0.0')}
    keys=sorted(set(a)|set(b));out={};diffs=[]
    idx={k:i for i,k in enumerate(keys)}
    for lag in LAGS:
        sx=sy=sxx=syy=sxy=0.;m=0
        for k,i in idx.items():
            j=i+lag
            if not (0<=j<len(keys)-1 and i<len(keys)-1):continue
            x0=a.get(k);x1=a.get(keys[i+1]);y0=b.get(keys[j]);y1=b.get(keys[j+1])
            if None in (x0,x1,y0,y1):continue
            u=x1-x0;v=y1-y0;sx+=u;sy+=v;sxx+=u*u;syy+=v*v;sxy+=u*v;m+=1
        den=math.sqrt(max(sxx-sx*sx/m,0)*max(syy-sy*sy/m,0)) if m else 0
        out[str(lag)]=round((sxy-sx*sy/m)/den,6) if den else None
    for k,x in a.items():
        y=b.get(k)
        if x is not None and y is not None:diffs.append(abs(x-y))
    diffs.sort()
    return {'diff_corr_JPF_t_vs_JF2024_t_plus_lag':out,'pairs_lag0':len(diffs),
            'median_abs_TA_difference_lag0':round(diffs[len(diffs)//2],6) if diffs else None,
            'share_identical_within_0.01C':round(sum(1 for x in diffs if x<=.01)/len(diffs),6) if diffs else None}
def jf_clock(br,core,lat,lon):
    first=br.stamp(core[0]['TIMESTAMP_START']);off=[]
    if first.hour or first.minute:raise ValueError('JF2024 HH must start at 00:00')
    for start in range(0,len(core)-47,48):
        day=core[start:start+48];t0=br.stamp(day[0]['TIMESTAMP_START'])
        top=[br.toa_mean(t0+timedelta(minutes=30*k),lat,lon,9.) for k in range(48)]
        lit=[k for k in range(48) if top[k]>0];sw=[num(r['SW_IN_F']) for r in day]
        if sum(top)<=0 or any(day[k]['SW_IN_F_QC'] not in ('0','0.0') or sw[k] is None for k in lit):continue
        sw=[max(x,0.) if x is not None else 0. for x in sw]
        if sum(sw)/sum(top)<.6:continue
        off.append(br.centroid(sw)-br.centroid(top))
    return br.summary(off)

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir():raise ValueError('fresh --out required')
    br=load_br();sites=[s for s in a.sites.split(',') if s]
    if any(s not in JPF for s in sites):raise ValueError('unknown site')
    report={'stage':'05BU','status':'LOCAL_ONLY_CROSS_RELEASE_EVIDENCE_ALL_HOLD','approved_replacements':0,'sites':{}}
    for s in sites:
        print('STAGE05BU',s,flush=True)
        jp=a.root/s/(JPF[s][0]+'.zip');jf=a.root/s/(JF2024[s][0]+'.zip');check(jp,JPF[s][1]);check(jf,JF2024[s][1])
        ta,p=load_jpf(jp,JPF[s][0]);core,pjf=load_jf(jf,s)
        with zipfile.ZipFile(jp) as outer:raw=outer.read(JPF[s][0]+'.zip')
        meta=br.bif_metadata(raw,JPF[s][0]);lat=float(meta['bif']['LOCATION_LAT'][0]);lon=float(meta['bif']['LOCATION_LONG'][0])
        report['sites'][s]={'JPF_zip_sha256':JPF[s][1],'JF2024_zip_sha256':JF2024[s][1],'P_ERA_ratio_by_lag':p_ratio(p,pjf),
                            'TA_QC0_cross_release':ta_lag(ta,core),'JF2024_SW_IN_F_clear_day_centroid_offset_min_UTC9':jf_clock(br,core,lat,lon)}
        check(jp,JPF[s][1]);check(jf,JF2024[s][1])
    a.out.mkdir()
    with (a.out/'summary_LOCAL_ONLY_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE05BU COMPLETE; LOCAL-ONLY; ALL HOLD');print(json.dumps(report,indent=1,sort_keys=True))

def selftest():
    r=p_ratio({'201001010000':3.6,'201001010030':7.2},{'201001010000':1.,'201001010030':2.})
    assert r['0']['share_within_1pct_of_3.6']==1.0 and abs(r['0']['total_ratio_JPF_over_JF2024_raw']-3.6)<1e-9
    assert 'JP-Tmd' not in JF2024
    print('STAGE05BU SELF-TEST PASS; LOCAL-ONLY CROSS-RELEASE EVIDENCE; ZERO APPROVALS')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--root',type=Path,default=Path('/mnt/d/Fluxes_Tower_Experiment/JapanFlux'))
    p.add_argument('--sites',default=','.join(JPF));p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if a.out is None:p.error('--out required')
    run(a)
if __name__=='__main__':main()

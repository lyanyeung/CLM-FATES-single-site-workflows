#!/usr/bin/env python3
"""Batch05 Stage54 | read-only inspect QC0 brackets around the three Stage53 events.
Original source clock/ZIP/file SHA pinned by Stage52/53. Maximum search +/-24h.
Exploratory interpolation is NEVER scientific approval or a forcing change.
"""
import argparse
import csv
import hashlib
import io
import math
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

EVENTS = ('US-UMB_E0003', 'US-Wjs_E0079', 'US-Wjs_E0114')
EXPECTED = {'US-UMB_E0003': 1, 'US-Wjs_E0079': 3, 'US-Wjs_E0114': 4}

def num(s):
    try:
        v = float(s)
        return v if math.isfinite(v) and v not in (-9999.0, -6999.0) else None
    except (TypeError, ValueError): return None

def sat(t):
    return 6.112*math.exp(17.67*t/(243.5+t)) if t is not None and -80 <= t <= 60 else None

def rh(t, v):
    e = sat(t)
    return 100*(1-v/e) if e and v is not None else None

def stamp(s): return datetime.strptime(s, '%Y%m%d%H%M')
def ts(d): return d.strftime('%Y%m%d%H%M')
def fmt(v):
    if v is None: return 'NA'
    return f'{v:.3f}' if isinstance(v, (int,float)) else str(v)

def read_csv(p):
    with p.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def fingerprint(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''): h.update(chunk)
    return h.hexdigest()

def source_stream(p, member):
    if p.suffix.lower() == '.zip':
        z = zipfile.ZipFile(p)
        if member not in z.namelist():
            z.close(); raise ValueError('original source ZIP member missing '+member)
        return z, io.TextIOWrapper(z.open(member), encoding='utf-8-sig', newline='')
    return None, p.open(encoding='utf-8-sig', newline='')

def self_test():
    assert rh(20,0)==100 and rh(2,9)<0 and num('-9999') is None
    assert ts(stamp('201803120900')-timedelta(minutes=30))=='201803120830'
    assert sum(EXPECTED.values())==8
    print('STAGE54 SELF-TEST PASS | exact three original events; no writes')

def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--self-test', action='store_true')
    a.add_argument('--stage53-dir', type=Path)
    a.add_argument('--stage52-dir', type=Path)
    args = a.parse_args()
    if args.self_test: self_test(); return
    if not args.stage53_dir or not args.stage52_dir: a.error('Stage53/Stage52 dirs required')
    p53 = args.stage53_dir/'stage53_20_HH_BEFORE_DURING_AFTER_PRIMARY_TOWER_SOURCE_ERA.csv'
    p52 = args.stage52_dir/'stage52_THREE_EVENT_RAW_SOURCE_PRODUCT_INVENTORY.csv'
    if not p53.is_file() or not p52.is_file(): a.error('verified Stage52/53 files missing')
    selected, inventory = read_csv(p53),read_csv(p52)
    if len(selected)!=20: raise ValueError('Stage53 original context denominator drift')
    events = {e:sorted((r for r in selected if r['episode_id']==e and r['role']=='EVENT'), key=lambda r:r['native_time']) for e in EVENTS}
    if any(len(events[e])!=EXPECTED[e] for e in EVENTS): raise ValueError('original event HH drift')
    requests={}
    for e in EVENTS:
        rr=events[e]
        if len({(r['source_file'],r['source_member'],r['source_sha256']) for r in rr})!=1:
            raise ValueError('source product mixed within '+e)
        r=rr[0]
        found=[m for m in inventory if m['site']==r['site'] and m['source_file']==r['source_file']
               and m['source_member']==r['source_member'] and m['source_file_SHA256']==r['source_sha256']]
        if not found or len({m['timestamp_column'] for m in found})!=1:
            raise ValueError('Stage52 original native clock missing/ambiguous '+e)
        key=(r['source_file'],r['source_member'],r['source_sha256'],found[0]['timestamp_column'])
        requests.setdefault(key,[]).append(e)
    values={}
    for (filename,member,sha,clock),ids in requests.items():
        p=Path(filename)
        if not p.is_file() or p.is_symlink() or fingerprint(p)!=sha:
            raise ValueError('original raw source SHA mismatch '+filename)
        intervals={}
        for e in ids:
            lo,hi=stamp(events[e][0]['native_time']),stamp(events[e][-1]['native_time'])
            intervals[e]=(lo-timedelta(hours=24),hi+timedelta(hours=24))
            values[e]={}
        z,f=source_stream(p,member)
        try:
            rd=csv.DictReader(f)
            required={clock,'TA_F','TA_F_QC','VPD_F','VPD_F_QC'}
            if not required.issubset(rd.fieldnames or []): raise ValueError('original source columns missing')
            for row in rd:
                raw=row.get(clock,'')
                if len(raw)!=12 or not raw.isdigit(): continue
                t=stamp(raw)
                for e,(lo,hi) in intervals.items():
                    if lo<=t<=hi:
                        if t in values[e]: raise ValueError('duplicate original native HH '+raw)
                        values[e][t]=row
        finally:
            f.close()
            if z: z.close()
    print('STAGE54 ACTUAL ORIGINAL QC0 BRACKETS | +/-24 HOURS | NO ORIGINAL WRITES')
    for e in EVENTS:
        data=values[e]
        start,end=stamp(events[e][0]['native_time']),stamp(events[e][-1]['native_time'])
        for original in events[e]:
            r=data.get(stamp(original['native_time']))
            if r is None or num(r.get('TA_F')) is None or num(r.get('VPD_F')) is None:
                raise ValueError('original event not found '+e)
            if (abs(num(r['TA_F'])-float(original['tower_TA_C']))>.002 or
                abs(num(r['VPD_F'])-float(original['tower_VPD_hPa']))>.002 or
                r['VPD_F_QC']!=original['tower_VPD_QC']):
                raise ValueError('source event provenance drift '+e)
        def qc0(r):
            return (r.get('TA_F_QC')=='0' and r.get('VPD_F_QC')=='0' and
                num(r.get('TA_F')) is not None and num(r.get('VPD_F')) is not None)
        before=max((t for t,r in data.items() if t<start and qc0(r)),default=None)
        after=min((t for t,r in data.items() if t>end and qc0(r)),default=None)
        print('\n###',e,'EVENT',ts(start),'to',ts(end),'HH',len(events[e]))
        print('LEFT_QC0',ts(before) if before else 'NOT_FOUND','RIGHT_QC0',ts(after) if after else 'NOT_FOUND')
        if before and after:
            window=sorted((t,r) for t,r in data.items() if before<=t<=after)
            print('BRACKET_HH',len(window),'NON_QC0_HH',sum(not qc0(r) for _,r in window))
            if len(window)>80:
                print('WIDE_BRACKET: interpolation risky; only subset of rows shown')
                shown=[(t,r) for t,r in window if (t-before)<=timedelta(hours=2) or
                    (after-t)<=timedelta(hours=2) or
                    start-timedelta(hours=1)<=t<=end+timedelta(hours=1)]
            else: shown=window
        else:
            window=[]
            shown=sorted((t,r) for t,r in data.items()
               if start-timedelta(hours=1)<=t<=end+timedelta(hours=1))
            print('HOLD no complete verified QC0 bracket within +/-24h')
        print('native HH | role | TA QC | T C | VPD QC | VPD hPa | RH source field | RH from TA/VPD | ERA T C | ERA VPD hPa | ERA derived RH')
        for t,r in shown:
            T,V=num(r.get('TA_F')),num(r.get('VPD_F'))
            Te,Ve=num(r.get('TA_ERA')),num(r.get('VPD_ERA'))
            role='EVENT' if start<=t<=end else 'QC0_ANCHOR' if t in (before,after) else 'CONTEXT'
            print(ts(t),'|',role,'|',r.get('TA_F_QC','NA'),'|',fmt(T),'|',
                r.get('VPD_F_QC','NA'),'|',fmt(V),'|',fmt(num(r.get('RH'))),
                '|',fmt(rh(T,V)),'|',fmt(Te),'|',fmt(Ve),'|',fmt(rh(Te,Ve)))
        if before and after:
            L,R=data[before],data[after]
            rl,rr=num(L.get('RH')),num(R.get('RH'))
            if rl is None or rr is None or not 0<=rl<=100 or not 0<=rr<=100:
                print('HOLD original RH source fields at endpoints unavailable; no trial')
                continue
            print('PREVIEW_ONLY: LINEAR RH interpolation between source-field QC0 endpoints (NOT an independent RH sensor validation)')
            for t,r in window[1:-1]:
                if qc0(r): continue
                T=num(r.get('TA_F')); es=sat(T)
                frac=(t-before).total_seconds()/(after-before).total_seconds()
                RH=rl+(rr-rl)*frac
                VPD=es*(1-RH/100) if es is not None else None
                print('TRIAL',ts(t),'T',fmt(T),'RH%',fmt(RH),'newVPD',fmt(VPD),'rawVPD',fmt(num(r.get('VPD_F'))),'ERA_VPD',fmt(num(r.get('VPD_ERA'))))
    print('\nSTAGE54 READONLY END | approvals=0 | forcing/DATM/CIME/Slurm unchanged')

if __name__=='__main__': main()

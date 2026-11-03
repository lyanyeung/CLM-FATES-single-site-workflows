#!/usr/bin/env python3
"""Analyze pasted prior hourly tables and AY windows; no source/forcing writes."""
import csv,hashlib,importlib.util,math,statistics,sys
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path

here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('az',here/'05az_bulk_existing_era5l_source_clock_audit_READONLY.py')
az=importlib.util.module_from_spec(spec);spec.loader.exec_module(az)
EXPECTED={'stage05at':'76150a3759de8877972dc6c7f883c582d8901346e7eb5b55616bfb9034db3566',
          'stage05au':'b495a5ec81e9da2e427bb870c8b6a53c105bfbe1d797d7445ff84221d5e00182',
          'stage05av':'37b86b556ad7239e693dde8dfdc6e6bf36a89c619ab204199ea0a60fa66c4e68'}
def parse_hour(s):return datetime.strptime(s,'%Y-%m-%dT%H:%MZ')
def parse_saved(s):
    grid=defaultdict(dict);source=None;hashes={};counts=defaultdict(int)
    for line in s.splitlines():
        if line.startswith('FILE '):
            path=line.split(maxsplit=1)[1];source=next((k for k in EXPECTED if '/japanflux_'+k+'/' in path),None)
            if source is None:raise ValueError('unexpected source table')
            continue
        p=line.split()
        if len(p)>=2 and source and p[0]==EXPECTED[source]:hashes[source]=p[0];continue
        if source=='stage05at' and p and p[0].startswith('2011-'):
            key=('JP-Tef','strd',parse_hour(p[0]));val=float(p[1]);counts[source]+=1
            grid[key[0]][key[1:]]=val
        elif source=='stage05au' and p and p[0].startswith('2005-'):
            t=parse_hour(p[0]);counts[source]+=1
            for col,value in zip(('sp','t2m','strd'),p[1:4]):grid['JP-Tmd'][(col,t)]=float(value)
        elif source=='stage05av' and p and p[0] in ('JP-Tef','JP-Tmd'):
            site,year,ts,col=p[:4];key=(site,col,parse_hour(ts));counts[source]+=1
            if key[1:] in grid[site]:raise ValueError('duplicate saved hour')
            grid[site][key[1:]]=float(p[-2])
    if hashes!=EXPECTED or dict(counts)!={'stage05at':8,'stage05au':9,'stage05av':26}:
        raise ValueError('operator-reported table hashes or counts differ')
    if any(not math.isfinite(v) for values in grid.values() for v in values.values()):raise ValueError('nonfinite grid')
    return grid
def run(window_text,hour_text):
    if 'INPUT_SHA256 '+az.WINDOW_SHA not in window_text or 'FULL_WINDOWS 45 UNIQUE_ROWS 1677' not in window_text:
        raise ValueError('source windows provenance/coverage header')
    points={}
    for line in window_text.splitlines():
        if not line.startswith('JP-'):continue
        p=line.split()
        if len(p)!=16 or p[-1] not in ('True','False'):raise ValueError('window row malformed')
        site,var,native,f,q,era=p[:6];key=(site,var,az.stamp(native))
        if key in points:raise ValueError('duplicate window key')
        points[key]={'f':az.number(f),'q':az.number(q),'era':az.number(era),'flag':p[-1]=='True'}
    flags={k for k,v in points.items() if v['flag']}
    if len(points)!=1677 or len(flags)!=45:raise ValueError('scope')
    groups=az.groups({k:{} for k in flags});grid=parse_saved(hour_text)
    output=[]
    for (site,var),ks in groups:
        if site not in ('JP-Tef','JP-Tmd'):continue
        start,end=ks[0][2],ks[-1][2];left=points[(site,var,start-az.STEP)];right=points[(site,var,end+az.STEP)]
        if any(p['flag'] or p['q']!=2 or p['f'] is None or p['era'] is None or abs(p['f']-p['era'])>1e-6 for p in (left,right)):
            raise ValueError('anchor invalid')
        shadows=az.bridge(left['f'],right['f'],len(ks))
        for off in (510,540,570,az.SOLAR_LONGITUDE[site]*4):
            event=[]
            for k,shadow in zip(ks,shadows):
                ref,support,method=az.reference(grid[site],var,k[2],off)
                event.append({'native':k[2].strftime('%Y%m%d%H%M'),'shadow':round(shadow,5),
                              'grid':None if ref is None else round(ref,5),
                              'shadow_minus_grid':None if ref is None else round(shadow-ref,5),
                              'support_UTC':support,'matching':method})
            diffs=defaultdict(list)
            for k,p in points.items():
                if k[:2]!=(site,var) or not start-timedelta(hours=24)<=k[2]<=end+timedelta(hours=24):continue
                if p['flag'] or p['f'] is None or p['q'] not in (0,1,2):continue
                lo,hi=az.BOUNDS[var]
                if not lo<=p['f']<=hi or any(abs((k[2]-f[2]).total_seconds())<=7200 for f in flags if f[:2]==(site,var)):continue
                ref,_,_=az.reference(grid[site],var,k[2],off)
                if ref is not None:diffs[int(p['q'])].append(p['f']-ref)
            def brief(q):
                a=diffs[q]
                return None if not a else {'n':len(a),'median':round(statistics.median(a),4),'min':round(min(a),4),'max':round(max(a),4)}
            output.append({'site':site,'variable':var,'group_start':start.strftime('%Y%m%d%H%M'),
                           'fixed_offset_minutes':off,'clock':'HYPOTHESIS_NOT_SOURCE_VERIFIED',
                           'event':event,'background_F_minus_grid_by_QC':{'0':brief(0),'1':brief(1),'2':brief(2)}})
    if len(output)!=28 or any(r['grid'] is None for x in output if x['fixed_offset_minutes']==540 for r in x['event']):
        raise ValueError('unexpected support/clock scenario scope')
    return output
def main():
    if len(sys.argv)==2 and sys.argv[1]=='--self-test':
        az.selftest()
        try:parse_saved('FILE /unexpected')
        except ValueError:pass
        else:raise AssertionError('unidentified hourly source accepted')
        print('PRECOMPUTED PASTE SELF-TEST PASS; ALL HOLD')
        return
    if len(sys.argv)!=3:raise SystemExit('Usage: script WINDOWS_PASTE HOURS_PASTE')
    paths=[Path(p) for p in sys.argv[1:]];blobs=[p.read_bytes() for p in paths]
    print('PASTED_INPUT_SHA256',*[hashlib.sha256(x).hexdigest() for x in blobs])
    print('TABLE_HASHES_OPERATOR_REPORTED_NOT_RECALCULATED_FROM_RAW_FILES',EXPECTED)
    import json
    print(json.dumps(run(*(b.decode('utf8') for b in blobs)),indent=2,ensure_ascii=False))
    print('NOT INDEPENDENT TOWER VALIDATION; 45/45 HOLD; ZERO APPROVED')
if __name__=='__main__':main()

"""Analyze the operator's de-duplicated full-window text, no network or source writes."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import math
import statistics
import sys

STEP=timedelta(minutes=30)
BOUNDS={'PA':(50.,115.),'TA':(-70.,65.),'LW_IN':(70.,650.)}
SITES=Counter({'JP-Fjy':6,'JP-Khw':11,'JP-Yms':10,'JP-Tef':4,'JP-Tmd':14})
VARS=Counter({'PA':27,'TA':6,'LW_IN':12})
def number(value):
    try:
        x=float(value)
        return x if math.isfinite(x) and x > -9990 else None
    except ValueError: return None
def time(s): return datetime.strptime(s,'%Y%m%d%H%M')
def pct(a,p):
    a=sorted(a)
    if not a: return None
    return a[round((len(a)-1)*p)]
def bridge(left,right,n):
    return [left+(right-left)*(i+1)/(n+1) for i in range(n)]
def pseudogaps(samples,n,flags,lo,hi):
    errors=[];eligible=0
    for i in range(1,len(samples)-n):
        block=samples[i-1:i+n+1]
        if len(block)!=n+2 or any(block[j+1]['t']-block[j]['t']!=STEP for j in range(len(block)-1)):
            continue
        if any(any(abs((r['t']-t).total_seconds())<=7200 for t in flags) for r in block):continue
        if any(r['q']!='2' or r['f'] is None or r['era'] is None or abs(r['f']-r['era'])>1e-6 or not lo<=r['f']<=hi for r in block):continue
        eligible+=1
        for r,pred in zip(block[1:-1],bridge(block[0]['f'],block[-1]['f'],n)):
            errors.append(abs(pred-r['f']))
    return eligible,errors
def selftest():
    assert bridge(98.,102.,3)==[99.,100.,101.]
    t=datetime(2020,1,1)
    a=[{'t':t+i*STEP,'q':'2','f':float(i),'era':float(i)} for i in range(10)]
    n,e=pseudogaps(a,2,[],0,20)
    assert n==7 and len(e)==14 and max(e)<1e-12
    n,e=pseudogaps(a,2,[t+4*STEP],0,20)
    assert n==0 and not e
    a[4]['q']='1'
    n,e=pseudogaps(a,2,[],0,20)
    assert n==3
    assert number('-9999') is None and number('nan') is None
    print('FULL WINDOW SELF-TEST PASS; SHADOW ONLY; ZERO APPROVALS')
if len(sys.argv)==2 and sys.argv[1]=='--self-test':
    selftest();sys.exit(0)
if len(sys.argv)!=2:raise SystemExit('Usage: python -B SCRIPT --self-test | PASTED_TEXT')
path=Path(sys.argv[1]); data=path.read_bytes(); text=data.decode('utf8')
if 'FULL_WINDOWS 45 UNIQUE_ROWS 1677' not in text:
    raise ValueError('Input does not attest complete 45 x 97 windows')
print('PASTED_TEXT_SHA256',hashlib.sha256(data).hexdigest())
reported=next((x.split()[1] for x in text.splitlines() if x.startswith('INPUT_SHA256 ')),'NOT_REPORTED')
if reported!='89e9b41055b782da97ebcbda9c6ddb55a3c6bf6426ad40fdd2bb865e98a687d9':
    raise ValueError('Unexpected operator-reported original window SHA256')
print('OPERATOR_REPORTED_NATIVE_WINDOWS_SHA256_NOT_INDEPENDENTLY_VERIFIED',reported)
print('DIAGNOSTIC ONLY; ALL 45 SCIENCE HOLD; ZERO APPROVED REPLACEMENTS')
rows=[]
for line in text.splitlines():
    if not line.startswith('JP-'): continue
    p=line.split()
    if len(p)!=16: raise ValueError('Unexpected token count: '+line[:200])
    site,var,native,f,q,era,raw,mds,mdsq,pa,paq,ta,taq,lw,lwq,flag=p
    if var not in BOUNDS or flag not in ('True','False'):raise ValueError('Unexpected variable or flag')
    rows.append({'site':site,'var':var,'t':time(native),'f':number(f),'q':q,
                 'era':number(era),'raw':number(raw),'mds':number(mds),'mdsq':mdsq,
                 'pa':number(pa),'paq':paq,'ta':number(ta),'taq':taq,
                 'lw':number(lw),'lwq':lwq,'flag':flag=='True'})
if len(rows)!=1677: raise ValueError('Expected 1677 de-duplicated rows')
index={(r['site'],r['var'],r['t']):r for r in rows}
if len(index)!=len(rows):raise ValueError('duplicate keys')
flags=[r for r in rows if r['flag']]
if len(flags)!=45 or Counter(r['site'] for r in flags)!=SITES or Counter(r['var'] for r in flags)!=VARS:
    raise ValueError('Original flag populations mismatch')
if len({(r['site'],r['t']) for r in flags})!=35:raise ValueError('35 native times mismatch')
if any(r['q']!='2' or r['f'] is None or r['era'] is None or abs(r['f']-r['era'])>1e-6 for r in flags):
    raise ValueError('Original flag provenance mismatch')
groups=[]
for key in sorted({(r['site'],r['var']) for r in flags}):
    ordered=sorted((r for r in flags if (r['site'],r['var'])==key),key=lambda r:r['t'])
    for r in ordered:
        if not groups or groups[-1][0]!=key or r['t']-groups[-1][1][-1]['t']!=STEP:
            groups.append((key,[r]))
        else:groups[-1][1].append(r)
if len(groups)!=17:raise ValueError('Expected 17 flagged contiguous groups')
print('TOTAL',len(rows),'TARGETS',len(flags),'GROUPS',len(groups))
print('UNIQUE_ROW_QC_BY_VAR',dict(Counter((r['var'],r['q']) for r in rows)))
print('ALL_UNFLAGGED_OUTSIDE',dict(Counter((r['site'],r['var']) for r in rows if not r['flag'] and r['f'] is not None and not (BOUNDS[r['var']][0]<=r['f']<=BOUNDS[r['var']][1]))))
co={}
for r in rows:
    for v,val,q in [('PA',r['pa'],r['paq']),('TA',r['ta'],r['taq']),('LW_IN',r['lw'],r['lwq'])]:
        k=(r['site'],v,r['t']); datum=(val,q)
        if k in co and co[k]!=datum:raise ValueError('Inconsistent co-variable values '+str(k))
        co[k]=datum
    if co[(r['site'],r['var'],r['t'])] != (r['f'],r['q']):
        raise ValueError('Target/co-variable value mismatch')
targetkeys={(r['site'],r['var'],r['t']) for r in flags}
outside_co=[(k,v) for k,v in co.items() if v[0] is not None and not (BOUNDS[k[1]][0]<=v[0]<=BOUNDS[k[1]][1]) and k not in targetkeys]
print('CO_VARIABLE_OUTSIDE_NOT_PREVIOUSLY_FLAGGED',len(outside_co),[(k[0],k[1],k[2].strftime('%Y%m%d%H%M'),v) for k,v in outside_co])
for (site,var),g in groups:
    lo,hi=BOUNDS[var]; start=g[0]['t']; end=g[-1]['t']; n=len(g)
    s=[r for r in rows if r['site']==site and r['var']==var and start-timedelta(hours=24)<=r['t']<=end+timedelta(hours=24)]
    s.sort(key=lambda r:r['t'])
    expected=int((end-start)/STEP)+97
    if len(s)!=expected:raise ValueError('Full-window coverage mismatch '+str((site,var,start,len(s),expected)))
    if s[0]['t']!=start-timedelta(hours=24) or s[-1]['t']!=end+timedelta(hours=24) or any(s[i+1]['t']-s[i]['t']!=STEP for i in range(len(s)-1)):
        raise ValueError('Window contains a timestamp gap')
    clean=[r for r in s if not r['flag'] and r['f'] is not None]
    outside=[r for r in clean if not lo<=r['f']<=hi]
    missing=sum(r['f'] is None for r in s)
    left=index[(site,var,start-STEP)];right=index[(site,var,end+STEP)]
    if any(r['flag'] or r['q']!='2' or r['f'] is None or r['era'] is None or abs(r['f']-r['era'])>1e-6 or not lo<=r['f']<=hi for r in (left,right)):
        raise ValueError('Flagged or invalid QC2 group anchor '+str((site,var,start)))
    shadows=bridge(left['f'],right['f'],n)
    # Synthetic masked gaps in nearby unflagged same-release QC2. Exclude a
    # two-hour guard around all known flags, including endpoints. These are
    # correlated sensitivity checks, not independent tower observations.
    allflags=[r['t'] for r in flags if r['site']==site and r['var']==var]
    eligible,errors=pseudogaps(s,n,allflags,lo,hi)
    print('GROUP',site,var,start.strftime('%Y%m%d%H%M'),end.strftime('%Y%m%d%H%M'),
          'HH',n,'WINDOW',len(s),'QC',dict(Counter(r['q'] for r in s)),
          'MISSING',missing,'UNFLAGGED_OUTSIDE',[(r['t'].strftime('%m%d%H%M'),r['f']) for r in outside],
          'UNFLAGGED_RANGE',round(min(r['f'] for r in clean),3) if clean else None,round(max(r['f'] for r in clean),3) if clean else None,
          'BOUNDARY',left['f'],right['f'],'SHADOW_UNAPPROVED',[round(v,3) for v in shadows],
          'PSEUDO_BLOCKS',eligible,'PSEUDO_MAE',round(statistics.mean(errors),4) if errors else None,
          'PSEUDO_P95_ABS',round(pct(errors,.95),4) if errors else None,
          'PSEUDO_MAX_ABS',round(max(errors),4) if errors else None)

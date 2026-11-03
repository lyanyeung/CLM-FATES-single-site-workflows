#!/usr/bin/env python3
"""Read two operator-pasted Stage05AY/AW outputs; all shadow values stay HOLD.

The SHA256 strings printed by the operator refer to remote files and cannot be
independently verified from pasted text. This script performs no network access,
does not modify source data or create forcing, and prints contextual comparisons.
"""
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import hashlib,math,sys

SITES=Counter({'JP-Fjy':6,'JP-Khw':11,'JP-Yms':10,'JP-Tef':4,'JP-Tmd':14})
VARS=Counter({'PA':27,'TA':6,'LW_IN':12})
BOUNDS={'PA':(50.,115.),'TA':(-70.,65.),'LW_IN':(70.,650.)}
STEP=timedelta(minutes=30)
AW_SHA='6b717bdf8232388f59af849da01dbc316a8166e0a07305d3d2567d2d7d55e6ad'
WINDOW_SHA='89e9b41055b782da97ebcbda9c6ddb55a3c6bf6426ad40fdd2bb865e98a687d9'
def dt(s): return datetime.strptime(s,'%Y%m%d%H%M')
def finite(s):
    x=float(s)
    if not math.isfinite(x) or x<=-9990:raise ValueError('invalid numeric input')
    return x
def compare(v,lo,hi):
    if lo>hi:raise ValueError('reference envelope reversed')
    return ('BELOW',v-lo) if v<lo else ('ABOVE',v-hi) if v>hi else ('INSIDE',0.)
def selftest():
    assert compare(2,3,4)==('BELOW',-1)
    assert compare(4,3,4)==('INSIDE',0)
    assert compare(5,3,4)==('ABOVE',1)
    try:compare(1,4,3)
    except ValueError:pass
    else:raise AssertionError('reversed envelope accepted')
    assert dt('202212312330')+STEP==dt('202301010000')
    print('SELF-TEST PASS: comparison, inclusivity, reversed bounds, calendar; ALL HOLD')
if len(sys.argv)==2 and sys.argv[1]=='--self-test':selftest();sys.exit(0)
if len(sys.argv)!=3:raise SystemExit('Usage: script --self-test | WINDOWS_PASTE AW_PASTE')
paths=[Path(x) for x in sys.argv[1:]]
contents=[x.read_bytes() for x in paths]
text=[x.decode('utf8') for x in contents]
if 'INPUT_SHA256 '+WINDOW_SHA not in text[0] or 'FULL_WINDOWS 45 UNIQUE_ROWS 1677' not in text[0]:
    raise ValueError('window export provenance/coverage header mismatch')
if 'STAGE05AW_SHA256 '+AW_SHA not in text[1]:raise ValueError('Stage05AW provenance header mismatch')
print('WINDOWS_PASTE_SHA256',hashlib.sha256(contents[0]).hexdigest())
print('AW_PASTE_SHA256',hashlib.sha256(contents[1]).hexdigest())
print('REMOTE_FILE_SHA256_REPORTED_BY_OPERATOR_NOT_INDEPENDENTLY_VERIFIED',WINDOW_SHA,AW_SHA)
rows=[]
for line in text[0].splitlines():
    if not line.startswith('JP-'):continue
    p=line.split()
    if len(p)!=16 or p[-1] not in ('True','False'):raise ValueError('window record malformed')
    site,var,t,f,q,era,raw,mds,mdsq,pa,paq,ta,taq,lw,lwq,flag=p
    if var not in VARS:raise ValueError('unsupported variable')
    rows.append({'site':site,'var':var,'t':dt(t),'f':finite(f),'q':q,'era':finite(era),'flag':flag=='True'})
if len(rows)!=1677:raise ValueError('window row count mismatch')
idx={(r['site'],r['var'],r['t']):r for r in rows}
if len(idx)!=len(rows):raise ValueError('duplicate native window key')
flags=[r for r in rows if r['flag']]
if len(flags)!=45 or Counter(x['site'] for x in flags)!=SITES or Counter(x['var'] for x in flags)!=VARS:
    raise ValueError('flag scope mismatch')
if len({(r['site'],r['t']) for r in flags})!=35:raise ValueError('native timestamp count mismatch')
groups=[]
for key in sorted({(r['site'],r['var']) for r in flags}):
    for r in sorted((r for r in flags if (r['site'],r['var'])==key),key=lambda x:x['t']):
        if not groups or groups[-1][0]!=key or r['t']-groups[-1][1][-1]['t']!=STEP:groups.append((key,[r]))
        else:groups[-1][1].append(r)
if len(groups)!=17:raise ValueError('group scope mismatch')
shadow={}
for key,g in groups:
    site,var=key;n=len(g)
    a=idx[(site,var,g[0]['t']-STEP)];b=idx[(site,var,g[-1]['t']+STEP)]
    if any(x['flag'] or x['q']!='2' or abs(x['f']-x['era'])>1e-6 or not BOUNDS[var][0]<=x['f']<=BOUNDS[var][1] for x in (a,b)):
        raise ValueError('invalid same-release QC2 shadow anchor')
    for j,r in enumerate(g,1):
        if r['q']!='2' or abs(r['f']-r['era'])>1e-6:raise ValueError('flag provenance mismatch')
        shadow[(site,var,r['t'])]=a['f']+(b['f']-a['f'])*j/(n+1)
aw={}
for line in text[1].splitlines():
    if not line.startswith('JP-'):continue
    p=line.split()
    if len(p) not in (11,12):raise ValueError('Stage05AW display record malformed')
    site,native,var,original=p[:4]
    utc,clock,lo,hi,tier,hold=p[-6:]
    unit=' '.join(p[4:-6])
    if unit!={'PA':'kPa','TA':'deg C','LW_IN':'W m-2'}.get(var):raise ValueError('unit mismatch')
    if hold!='HOLD_NO_APPROVED_30MIN_REPLACEMENT':raise ValueError('original HOLD missing')
    if dt(native)-dt(utc)!=timedelta(hours=9):raise ValueError('candidate clock mapping changed')
    expected='OPERATOR_JST_PLUS9_DIAGNOSTIC_README_SOLAR_CONFLICT' if site in ('JP-Tef','JP-Tmd') else 'ORIGINAL_SOURCE_README_JST_PLUS9_VERIFIED'
    if clock!=expected:raise ValueError('clock provenance changed')
    k=(site,var,dt(native))
    if k in aw:raise ValueError('duplicate Stage05AW field')
    aw[k]={'original':finite(original),'lo':finite(lo),'hi':finite(hi),'clock':clock,'tier':tier}
if set(aw)!=set(shadow):raise ValueError('AW/AY source keys mismatch')
out=[]
for k in sorted(shadow):
    r=idx[k];a=aw[k]
    if abs(a['original']-r['f'])>1e-6:raise ValueError('source values disagree')
    if a['lo']<=a['original']<=a['hi']:raise ValueError('original source was not outside prior envelope')
    status,delta=compare(shadow[k],a['lo'],a['hi'])
    out.append({'site':k[0],'var':k[1],'native':k[2].strftime('%Y%m%d%H%M'),
                'shadow':shadow[k],'lo':a['lo'],'hi':a['hi'],'status':status,'signed_gap':delta,
                'clock':a['clock'],'tier':a['tier']})
print('FIELD_COUNTS',dict(Counter(r['status'] for r in out)))
print('BY_SITE_VARIABLE',dict(Counter((r['site'],r['var'],r['status']) for r in out)))
print('site\tvar\tnative\tshadow_not_approved\tenvelope_min\tenvelope_max\tposition\tsigned_gap\tclock\tevidence_tier')
for r in out:
    print('\t'.join(str(r[k]) for k in ('site','var','native','shadow','lo','hi','status','signed_gap','clock','tier')))
print('CONTEXT ONLY; NOT MATCHED HALF-HOUR TRUTH; ALL 45 HOLD; ZERO APPROVED')

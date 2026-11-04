#!/usr/bin/env python3
"""Stage05BT: same-release ERA artifact companions and QC2-background clock-offset sensitivity. Read-only; all HOLD.

companion: from the Stage05BR artifact-window table, every F cell that is QC2 at a gross ERA artifact hour but is
  NOT one of the 45 earlier fields (e.g. WS_F, VPD_F, P_F) is tested for the zero-centre/half-flank pattern and
  given an unapproved QC2-bridge shadow with its neighbours and QC.
lag: reuses the existing 16 CDS ZIPs, Stage05AW ledger and Stage05AY windows through the SHA-pinned Stage05AZ
  functions, and recomputes the user-selected grid + QC2-median candidates for fixed native-to-UTC offsets of
  8:00-11:00 h. The UTC+9 row must reproduce the Stage05BF canonical SHA-256 before anything is written.
  Offsets are diagnostics of the same-release ERA time support, not clock proof; the user's method is unchanged.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

STEP=timedelta(minutes=30)
AZ_PIN=('05az_bulk_existing_era5l_source_clock_audit_READONLY.py','14909c294dea5ed17a9e0f3981a9ca2900b2ee8698dcf45902588fb0179f23cc')
ARTIFACT_TSV_SHA='0e61a27488b86c8d3cb439fb96eb9a441b513aab64b5d0724e28ad94d4d63b78'
SELECTED_CANONICAL_SHA='5fd381ddefac2d08a3cee7ed8548c73477c115a342f5895b4673b325768803ae'
OFFSETS=(480,510,540,570,600,630,660)
ERA={'TA_F':'TA_ERA','PA_F':'PA_ERA','VPD_F':'VPD_ERA','SW_IN_F':'SW_IN_ERA','LW_IN_F':'LW_IN_ERA','WS_F':'WS_ERA','P_F':'P_ERA'}
INSTANT=('TA_F','PA_F','VPD_F','WS_F')
INTERVAL=('SW_IN_F','LW_IN_F','P_F')
# The 45 earlier fields: (site, variable, native group start, length) from Stage05BD.
FORTY_FIVE={('JP-Fjy','PA_F','200508120230',3),('JP-Fjy','PA_F','201112170630',3),('JP-Khw','LW_IN_F','200508120200',2),
 ('JP-Khw','PA_F','200508120230',3),('JP-Khw','PA_F','201112170630',3),('JP-Khw','TA_F','200508120230',3),
 ('JP-Tef','LW_IN_F','201112170600',2),('JP-Tef','LW_IN_F','202204090200',2),('JP-Tmd','LW_IN_F','200508120200',2),
 ('JP-Tmd','PA_F','200508120230',3),('JP-Tmd','PA_F','201112170630',3),('JP-Tmd','PA_F','202204090230',3),
 ('JP-Tmd','TA_F','200508120230',3),('JP-Yms','LW_IN_F','200508120200',2),('JP-Yms','LW_IN_F','201112170600',2),
 ('JP-Yms','PA_F','200508120230',3),('JP-Yms','PA_F','201112170630',3)}

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def check(path,expected):
    if path.is_symlink() or not path.is_file() or sha(path)!=expected:raise ValueError('missing/symlink/hash mismatch '+str(path))
def stamp(s):return datetime.strptime(s,'%Y%m%d%H%M')
def num(s):
    try:x=float(s)
    except (TypeError,ValueError):return None
    return x if math.isfinite(x) and x>-9990 else None
def fresh(out):
    if out.exists() or out.is_symlink() or not out.parent.is_dir() or out.parent.is_symlink():raise ValueError('fresh --out under an existing real directory required')
def write(path,rows):
    if not rows:raise ValueError('no rows for '+path.name)
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def forty_five_cells():
    cells=set()
    for site,var,start,n in FORTY_FIVE:
        for k in range(n):cells.add((site,var,(stamp(start)+k*STEP).strftime('%Y%m%d%H%M')))
    if len(cells)!=45:raise ValueError('45-field scope')
    return cells

# ---------- companion ----------
def companion_rows(rows):
    """Group artifact rows per site window; test each non-45 QC2 cell for the half-value/zero pattern."""
    known=forty_five_cells();bysite=defaultdict(list)
    for r in rows:bysite[r['site']].append(r)
    out=[]
    for site,rs in sorted(bysite.items()):
        rs.sort(key=lambda r:r['native_start']);windows=[]
        for r in rs:
            if windows and stamp(r['native_start'])-stamp(windows[-1][-1]['native_start'])==STEP:windows[-1].append(r)
            else:windows.append([r])
        for w in windows:
            ta=[i for i,r in enumerate(w) if num(r['TA_ERA']) is not None and num(r['TA_ERA'])<-60]
            # Interval (hour-mean) artifact pair: LW_IN_ERA below half the window median; the regression intercept
            # of the zeroed hour differs by site (e.g. 67 W m-2 at Tak), so an absolute limit would miss pairs.
            lwv=sorted(num(r['LW_IN_ERA']) for r in w if num(r['LW_IN_ERA']) is not None)
            half=.5*lwv[len(lwv)//2] if lwv else None
            lw=[i for i,r in enumerate(w) if half is not None and num(r['LW_IN_ERA']) is not None and num(r['LW_IN_ERA'])<half]
            for var in INSTANT+INTERVAL:
                idx=ta if var in INSTANT else lw
                if not idx or idx[0]==0 or idx[-1]==len(w)-1 or idx!=list(range(idx[0],idx[-1]+1)):continue
                cells=[w[i] for i in idx];prev=w[idx[0]-1];nxt=w[idx[-1]+1]
                qc2=[int(c[var+'_QC'])==2 for c in cells]
                if not any(qc2):continue
                e=[num(c[ERA[var]]) for c in cells];ep=num(prev[ERA[var]]);en=num(nxt[ERA[var]])
                if var in INSTANT and len(e)==3 and None not in e+[ep,en]:
                    tol=.002+1e-3*max(abs(x) for x in e+[ep,en])
                    ok=abs(e[0]-(ep+e[1])/2)<=tol and abs(e[2]-(e[1]+en)/2)<=tol
                    pattern='HALF_FLANK_PATTERN_CONFIRMED' if ok else 'PATTERN_NOT_MATCHED'
                elif var in INTERVAL and len(e)==2 and None not in e+[ep,en]:
                    if e[0]!=e[1]:pattern='PAIR_NOT_EQUAL'
                    elif var=='P_F' and e[0]==0 and ep==0 and en==0:pattern='ZERO_PAIR_INDETERMINATE_DRY_CONTEXT'
                    elif var=='SW_IN_F' and e[0]==0 and ep==0 and en==0:pattern='NIGHT_ZERO_INDETERMINATE'
                    else:pattern='EQUAL_PAIR_DIFFERS_FROM_NEIGHBOURS'
                else:pattern='INSUFFICIENT_CONTEXT'
                fp=num(prev[var]);fn=num(nxt[var]);n=len(cells)
                for j,c in enumerate(cells):
                    in45=(site,var,c['native_start']) in known
                    bridge=None if fp is None or fn is None else fp+(fn-fp)*(j+1)/(n+1)
                    out.append({'site':site,'variable':var,'native_start':c['native_start'],'artifact_group_first':cells[0]['native_start'],
                        'in_earlier_45':in45,'source_F':c[var],'source_F_QC':c[var+'_QC'],'same_release_ERA':c[ERA[var]],
                        'prev_native':prev['native_start'],'prev_F':prev[var],'prev_F_QC':prev[var+'_QC'],
                        'next_native':nxt['native_start'],'next_F':nxt[var],'next_F_QC':nxt[var+'_QC'],
                        'pattern_test':pattern,'bridge_shadow_NOT_APPROVED':'' if bridge is None or int(c[var+'_QC'])!=2 else repr(round(bridge,6)),
                        'status':'IN_EARLIER_45_SEE_SELECTED_METHOD' if in45 else ('NEW_COMPANION_HOLD' if int(c[var+'_QC'])==2 else 'NOT_QC2_SOURCE_PROTECTED')})
    return out

def run_companion(a):
    fresh(a.out);check(a.artifact_tsv,ARTIFACT_TSV_SHA)
    with a.artifact_tsv.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f,delimiter='\t'))
    out=companion_rows(rows)
    seen=Counter((r['site'],r['variable'],r['native_start']) for r in out)
    if any(v>1 for v in seen.values()):raise ValueError('duplicate companion cell')
    got45={(r['site'],r['variable'],r['native_start']) for r in out if r['in_earlier_45']}
    if len(got45)!=45:raise ValueError('artifact table does not reproduce the 45 earlier cells: %d'%len(got45))
    check(a.artifact_tsv,ARTIFACT_TSV_SHA)
    a.out.mkdir();write(a.out/'companion_artifact_cells_HOLD.tsv',out)
    new=[r for r in out if r['status']=='NEW_COMPANION_HOLD']
    summary={'stage':'05BT-companion','status':'ALL_HOLD','approved_replacements':0,'artifact_tsv_sha256':ARTIFACT_TSV_SHA,
             'cells':len(out),'earlier_45_reproduced':len(got45),'new_companion_QC2_cells':len(new),
             'new_by_site_variable_pattern':{'|'.join(k):v for k,v in sorted(Counter((r['site'],r['variable'],r['pattern_test']) for r in new).items())},
             'protected_non_QC2_cells':sum(1 for r in out if r['status']=='NOT_QC2_SOURCE_PROTECTED'),
             'companion_tsv_sha256':sha(a.out/'companion_artifact_cells_HOLD.tsv')}
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(summary,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE05BT COMPANION COMPLETE; ALL HOLD');print(json.dumps(summary,indent=1,sort_keys=True))

# ---------- lag ----------
def load_az(path):
    check(path,AZ_PIN[1])
    spec=importlib.util.spec_from_file_location('stage05az',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def canonical(rows):
    body=''.join('{}\t{}\t{}\t{:.6f}\n'.format(*r) for r in sorted(rows))
    return hashlib.sha256(body.encode('ascii')).hexdigest()
def offset_table(az,unique,events,grid):
    groups=az.groups(events);table=[];cands=defaultdict(dict)
    for (site,var),keys in groups:
        start=keys[0][2];end=keys[-1][2];lo,hi=az.BOUNDS[var]
        left=unique[(site,var,start-STEP)];right=unique[(site,var,end+STEP)]
        for off in OFFSETS:
            res=defaultdict(list)
            for k,p in sorted(unique.items()):
                if k[:2]!=(site,var) or not start-timedelta(hours=24)<=p['t']<=end+timedelta(hours=24):continue
                if p['flag'] or p['f'] is None or p['q'] not in (0,1,2) or not lo<=p['f']<=hi:continue
                if any(abs((p['t']-q[2]).total_seconds())<=7200 for q in events if q[:2]==(site,var)):continue
                ref=az.reference(grid[site],var,p['t'],off)[0]
                if ref is not None:res[int(p['q'])].append(p['f']-ref)
            med=statistics.median(res[2]) if res[2] else None
            mad=statistics.median([abs(x-med) for x in res[2]]) if res[2] else None
            vals=[]
            for k in keys:
                ref=az.reference(grid[site],var,k[2],off)[0]
                vals.append(None if ref is None or med is None else ref+med);cands[off][k]=vals[-1]
            seq=[left['f']]+vals+[right['f']]
            jump=None if None in seq else max(abs(seq[i+1]-seq[i]) for i in range(len(seq)-1))
            table.append({'site':site,'variable':var,'group_start':start.strftime('%Y%m%d%H%M'),'offset_minutes':off,
                'qc2_pairs':len(res[2]),'qc2_median_source_minus_grid':med,'qc2_MAD':mad,'qc0_pairs':len(res[0]),
                'qc0_median_source_minus_grid':statistics.median(res[0]) if res[0] else None,
                'candidates_NOT_APPROVED':','.join('' if v is None else repr(round(v,6)) for v in vals),
                'max_adjacent_jump_with_QC2_flanks':jump,'status':'HOLD_DIAGNOSTIC_OFFSET_NOT_CLOCK_PROOF'})
    return table,cands
def run_lag(a):
    fresh(a.out);az=load_az(Path(__file__).with_name(AZ_PIN[0]))
    az.checked(a.aw,az.AW_SHA);az.checked(a.ay,az.WINDOW_SHA)
    sources=[]
    for site,(span,h) in az.SOURCE.items():
        p=a.source_root/site/'forcing'/'packages'/f'JPF_{site}_FLUXNET_{span}_v1.3_r1.zip';az.checked(p,h);sources.append((p,h))
    grid=defaultdict(dict);cds=[]
    for (site,day),(which,h,variables) in sorted(az.CDS.items()):
        p=(a.early if which=='early' else a.late)/f'{site}_ERA5Land_timeseries_{day}_CSV_response.zip';az.checked(p,h)
        values,_,_=az.parse_cds(p.read_bytes(),site,day,variables,az.GRIDS[site])
        for k,v in values.items():
            if k in grid[site]:raise ValueError('duplicate CDS hour')
            grid[site][k]=v
        cds.append((p,h))
    unique,events=az.windows(az.table(a.ay),az.table(a.aw))
    table,cands=offset_table(az,unique,events,grid)
    base=[(k[0],k[1],k[2].strftime('%Y%m%d%H%M'),v) for k,v in cands[540].items()]
    if any(r[3] is None for r in base) or canonical(base)!=SELECTED_CANONICAL_SHA:raise ValueError('UTC+9 row does not reproduce the Stage05BF selected canonical SHA-256')
    for p,h in [(a.aw,az.AW_SHA),(a.ay,az.WINDOW_SHA)]+sources+cds:az.checked(p,h)
    a.out.mkdir();write(a.out/'offset_sensitivity_17_groups_HOLD.tsv',table)
    best={}
    for r in table:
        k=(r['site'],r['variable'],r['group_start'])
        if r['qc2_MAD'] is not None and r['qc2_pairs']>=12 and (k not in best or r['qc2_MAD']<best[k][1]):best[k]=(r['offset_minutes'],r['qc2_MAD'],r['qc2_pairs'])
    summary={'stage':'05BT-lag','status':'ALL_HOLD','approved_replacements':0,'selected_UTC9_canonical_sha256_reproduced':SELECTED_CANONICAL_SHA,
             'offsets_minutes':list(OFFSETS),'groups':len({(r['site'],r['variable'],r['group_start']) for r in table}),
             'min_QC2_MAD_offset_by_group':{'|'.join(k):v for k,v in sorted(best.items())},
             'min_QC2_MAD_offset_counts':dict(sorted(Counter(v[0] for v in best.values()).items())),
             'offset_tsv_sha256':sha(a.out/'offset_sensitivity_17_groups_HOLD.tsv'),
             'note':'grid at native minus offset; 540=user UTC+9 candidate; a smaller QC2 MAD at another offset indicates same-release ERA time support, not tower clock'}
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(summary,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE05BT LAG COMPLETE; UTC+9 SELECTED VALUES REPRODUCED; ALL HOLD');print(json.dumps(summary,indent=1,sort_keys=True))

def selftest():
    assert len(forty_five_cells())==45 and stamp('202204090230')+STEP==stamp('202204090300')
    w=[{'site':'X','native_start':(datetime(2005,8,12,1,30)+i*STEP).strftime('%Y%m%d%H%M'),'TA_ERA':str(t),'LW_IN_ERA':str(l),
        'WS_F':str(ws),'WS_F_QC':'2','WS_ERA':str(ws),**{v:'1' for v in ('TA_F','PA_F','VPD_F','SW_IN_F','LW_IN_F','P_F')},
        **{v+'_QC':'0' for v in ('TA_F','PA_F','VPD_F','SW_IN_F','LW_IN_F','P_F')},**{e:'1' for e in ('PA_ERA','VPD_ERA','SW_IN_ERA','P_ERA')}}
       for i,(t,l,ws) in enumerate([(20,400,1.),(20,40,1.),(-120,40,.5),(-270,400,0.),(-120,400,.5),(20,400,1.)])]
    out=[r for r in companion_rows(w) if r['variable']=='WS_F']
    assert len(out)==3 and all(r['pattern_test']=='HALF_FLANK_PATTERN_CONFIRMED' and r['status']=='NEW_COMPANION_HOLD' for r in out)
    assert out[1]['bridge_shadow_NOT_APPROVED']=='1.0'
    assert canonical([('A','PA','202201010000',1.)])==hashlib.sha256(b'A\tPA\t202201010000\t1.000000\n').hexdigest()
    print('STAGE05BT SELF-TEST PASS; COMPANION AND OFFSET DIAGNOSTICS ONLY; ZERO APPROVALS')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('mode',nargs='?',choices=('companion','lag'))
    p.add_argument('--artifact-tsv',type=Path);p.add_argument('--aw',type=Path);p.add_argument('--ay',type=Path)
    p.add_argument('--early',type=Path);p.add_argument('--late',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--source-root',type=Path,default=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
    a=p.parse_args()
    if a.self_test:selftest();return
    if a.mode=='companion':
        if a.artifact_tsv is None or a.out is None:p.error('companion needs --artifact-tsv and --out')
        run_companion(a)
    elif a.mode=='lag':
        if any(getattr(a,k) is None for k in ('aw','ay','early','late','out')):p.error('lag needs --aw --ay --early --late --out')
        run_lag(a)
    else:p.error('mode required')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Stage06C: humidity (E1) and JP-Tgf clock (E2) forensics with proposed values. Read-only; NOT APPROVED.

Input: the Stage05CB approved tables (pinned through Stage06A) and the original ZIPs (same-release ERA for the JPF
sites, JapanFlux2024 ERA5_FILL for Tgf). Reference humidity is the one already approved for D9/D9b: JPF ERA RH at
t+1h (decision C3), Tgf ERA5_FILL RH at t. Rules proposed here (user decides):
  E2   Tgf windows where the daily clear-sky SW centroid runs >15 min late or early (15-day running median, >=30 days,
       gaps of <=14 days bridged) and confirmed by an independent variable (window SW median >=25 min and TA diurnal
       phase lag versus ERA5_FILL >=15 min beyond the same calendar span in other years); unconfirmed windows are
       reported only:
       a QC0 TA/RH/VPD/SW cell takes the original value labelled 30 min later (late clock, E2_..._M30) or earlier
       (early clock, E2_..._P30) when that cell is QC0 and inside the window (same pattern as C2); the window cell
       without a source keeps its value.
  E1A  humid outlier: tower dew point >=28 C and >=3 C above the reference -> humidity from the reference RH at the
       tower TA (VPD for JPF; RH and VPD for Tgf).
  E1B  dry outlier: tower RH <5 % while the reference RH >=15 % -> same replacement.
  E1C  stuck saturation: run of >=6 half-hours with tower RH >=99.5 %, mean TA >=25 C and median reference RH <80 %
       -> same replacement for the whole run.
E1 is evaluated after E2. Every other cell must stay byte-identical to Stage05CB (checked cell by cell). Also writes
per-year humidity drift statistics (evidence for documenting, not for changing values) and Tgf clock diagnostics.
Writes only to a new directory; no forcing, case, Slurm or source change.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

A6_PIN=('06a_build_utc_noleap_datm_candidates_GUARDED.py','88ff83e3f7fb6ec42c0b70eaf9d12019b70826851fe6132961dde08c0dc633cc')
JPF=('JP-Api','JP-Fhk','JP-Fjy','JP-Khw','JP-Spp','JP-Tak','JP-Tef','JP-Tmd','JP-Yms')
E2_VARS=('TA_F','RH_F','VPD_F','SW_IN_F')
TD_HUMID=28.;TD_EXCESS=3.;RH_DRY=5.;RH_REF_DRY=15.;SAT=99.5;RUN_MIN=6;RUN_TA=25.;RUN_REF=80.
CLOCK_LATE=15.;CLOCK_HALF=7;CLOCK_MIN_DAYS=30;CLOCK_GAP=14;E2_SW_MIN=25.;E2_TA_EXCESS=15.

def load_a6():
    name,expected=A6_PIN;here=Path(__file__).parent
    for path in (here/name,here.parent/'stage06'/name):
        if path.is_file() and not path.is_symlink():break
    else:raise ValueError('pinned 06A script not found')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 06A hash mismatch')
    spec=importlib.util.spec_from_file_location('stage06a',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
a6=load_a6();bz=a6.cb.bz;br=bz.br;bw=bz.bw;bs=bz.bs;num=br.num;fmt=bw.fmt

def dew(e):l=math.log(e/6.112);return 243.5*l/(17.67-l)

def runs(flags):
    """Maximal runs of True as (start, stop) index pairs."""
    out=[];i=0
    while i<len(flags):
        if flags[i]:
            j=i
            while j<len(flags) and flags[j]:j+=1
            out.append((i,j));i=j
        else:i+=1
    return out

def late_windows(daily,sign=1):
    """{date: SW centroid offset or None} -> [(first, last)] where sign * centred running median exceeds CLOCK_LATE
    (sign +1: clock late, -1: clock early)."""
    days=sorted(daily);late=[]
    for k,d in enumerate(days):
        near=[daily[x] for x in days[max(0,k-CLOCK_HALF):k+CLOCK_HALF+1] if daily[x] is not None]
        late.append(len(near)>=5 and sign*statistics.median(near)>CLOCK_LATE)
    merged=[]
    for a,b in runs(late):   # a logger clock error is continuous: bridge gaps of <=CLOCK_GAP days left by cloudy spells
        if merged and (days[a]-merged[-1][1]).days<=CLOCK_GAP:merged[-1][1]=days[b-1]
        else:merged.append([days[a],days[b-1]])
    return [(x,y) for x,y in merged if (y-x).days+1>=CLOCK_MIN_DAYS]

def daily_offsets(rows,col,qcc,lat,lon):
    """Daily clear-sky SW centroid minus TOA centroid (minutes) on UTC+9 for days with >=44 QC0 SW half-hours."""
    by=defaultdict(list)
    for i,r in enumerate(rows):by[r[0][:8]].append(i)
    out={};m=[(k+.5)*30 for k in range(48)]
    for d,ix in by.items():
        key=date(int(d[:4]),int(d[4:6]),int(d[6:]))
        if len(ix)!=48 or sum(rows[i][qcc['SW_IN_F']]=='0' for i in ix)<44:out[key]=None;continue
        sw=[max(num(rows[i][col['SW_IN_F']]),0.) for i in ix];toa=[br.toa_mean(br.stamp(rows[i][0]),lat,lon,9.) for i in ix]
        out[key]=None if sum(sw)<.2*sum(toa) else sum(a*b for a,b in zip(sw,m))/sum(sw)-sum(a*b for a,b in zip(toa,m))/sum(toa)
    return out

def composite_lags(rows,idx,col,qcc,ref,pairs):
    """First-harmonic phase lag (minutes, + = tower later) of the QC0 mean diurnal cycle versus the reference."""
    acc={v:[[0.]*48,[0.]*48,[0]*48] for v,_ in pairs}
    for i in idx:
        r=rows[i];s=int(r[0][8:10])*2+int(r[0][10:12])//30
        for v,c in pairs:
            if r[qcc[v]]!='0':continue
            x=num(r[col[v]]);e=num(ref[r[0]][c])
            if math.isfinite(x) and math.isfinite(e):a=acc[v];a[0][s]+=x;a[1][s]+=e;a[2][s]+=1
    def phase(xs):return math.atan2(-sum(x*math.sin(2*math.pi*k/48) for k,x in enumerate(xs)),sum(x*math.cos(2*math.pi*k/48) for k,x in enumerate(xs)))
    out={}
    for v,(t,e,n) in acc.items():
        if min(n)<20:continue
        dp=phase([a/b for a,b in zip(e,n)])-phase([a/b for a,b in zip(t,n)]);dp=(dp+math.pi)%(2*math.pi)-math.pi
        out[v]=round(dp/(2*math.pi)*1440,1)
    return out

def window_evidence(rows,col,qcc,ref,daily,wins):
    """Per (sign, first, last) window: median SW offset, and TA/SW lag inside minus the lag over the same calendar span
    in other years; proposed only when both point the same way by at least E2_SW_MIN / E2_TA_EXCESS."""
    pairs=(('TA_F','TA_ERA5'),('SW_IN_F','SW_IN_ERA5'));inside=lambda t,x,y:x.strftime('%Y%m%d')<=t[:8]<=y.strftime('%Y%m%d');out=[]
    for sign,x,y in wins:
        a,b=x.strftime('%m%d'),y.strftime('%m%d');whole=(y-x).days>=365
        span=lambda md:whole or (a<=md<=b if a<=b else (md>=a or md<=b))
        win=[i for i,r in enumerate(rows) if inside(r[0],x,y)]
        other=[i for i,r in enumerate(rows) if span(r[0][4:8]) and not any(inside(r[0],p,q) for _,p,q in wins)]
        lw=composite_lags(rows,win,col,qcc,ref,pairs);lo=composite_lags(rows,other,col,qcc,ref,pairs)
        med=statistics.median(v for d,v in daily.items() if x<=d<=y and v is not None)
        exc={v:round(lw[v]-lo[v],1) for v in lw if v in lo}
        out.append({'clock':'late' if sign>0 else 'early','first':str(x),'last':str(y),'days':(y-x).days+1,'sw_centroid_median_min':round(med,1),
                    'lag_excess_vs_other_years_min':exc,'proposed':sign*med>=E2_SW_MIN and sign*exc.get('TA_F',0)>=E2_TA_EXCESS})
    return out

class Table:
    def __init__(self,key,header,variables,rows,listing):
        self.key=key;self.header=header;self.variables=variables;self.rows=rows;self.listing=listing;self.counts=Counter()
        self.col={v:1+3*j for j,v in enumerate(variables)};self.qcc={v:c+1 for v,c in self.col.items()};self.tagc={v:c+2 for v,c in self.col.items()}
    def put(self,i,v,val,rule,evidence=''):
        r=self.rows[i];self.listing.append([self.key,v,r[0],r[self.col[v]],val,rule,r[self.tagc[v]],evidence])
        r[self.col[v]]=val;r[self.tagc[v]]='PROPOSED_'+rule+'_NOT_APPROVED|'+r[self.tagc[v]];self.counts[(v,rule)]+=1

def e2_shift(t,lo,hi,sign=1):
    """Inside [lo, hi): QC0 cell <- original value labelled 30 min later (clock late, sign +1) or earlier (clock early,
    sign -1) if that cell is QC0 and inside the window; the window cell without a source keeps its value.
    TA/RH/VPD move together (all QC0 at both labels) so the humidity triple stays consistent; SW moves on its own."""
    ix=[i for i,r in enumerate(t.rows) if lo<=r[0]<hi];orig={(i,v):t.rows[i][t.col[v]] for i in ix for v in E2_VARS}
    rule='E2_TGF_CLOCK_M30' if sign>0 else 'E2_TGF_CLOCK_P30'
    for i in (ix[:-1] if sign>0 else ix[1:]):
        for group in (E2_VARS[:3],E2_VARS[3:]):
            if all(t.rows[k][t.qcc[v]]=='0' for k in (i,i+sign) for v in group):
                for v in group:t.put(i,v,orig[(i+sign,v)],rule)

def e1(t,formula,ref):
    """ref[i] = (TA_ref, RH_ref) for row i. Returns per-year drift statistics."""
    rows=t.rows;n=len(rows);tower=[]
    for r in rows:
        ta=num(r[t.col['TA_F']]);vpd=num(r[t.col['VPD_F']]);es=br.es(ta,formula);tower.append((ta,100*(es-vpd)/es,es-vpd))
    pick={}
    for i in range(n):
        ta,rh,e=tower[i];tr,rr=ref[i];er=rr/100*br.es(ta,formula)
        if dew(e)>=TD_HUMID and dew(e)-dew(br.es(tr,formula)*rr/100)>=TD_EXCESS:pick[i]='E1A_HUMID_OUTLIER'
        elif rh<RH_DRY and rr>=RH_REF_DRY:pick[i]='E1B_DRY_OUTLIER'
    for a,b in runs([x[1]>=SAT for x in tower]):
        if b-a>=RUN_MIN and statistics.fmean(tower[i][0] for i in range(a,b))>=RUN_TA and statistics.median(ref[i][1] for i in range(a,b))<RUN_REF:
            for i in range(a,b):pick.setdefault(i,'E1C_STUCK_SATURATION')
    for i,rule in sorted(pick.items()):
        ta,rh,e=tower[i];tr,rr=ref[i];ev='TA %.2f refTA %.2f RH %.1f refRH %.1f Td %.1f refTd %.1f'%(ta,tr,rh,rr,dew(e),dew(br.es(tr,formula)*rr/100))
        if 'RH_F' in t.col:t.put(i,'RH_F',fmt(rr),rule+'_RH_REF',ev)
        t.put(i,'VPD_F',fmt(br.es(ta,formula)*(1-rr/100)),rule+'_VPD_REF_RH_AT_TOWER_TA',ev)
    years=defaultdict(lambda:{'n':0,'d':[],'tower_sat_TA20':0,'ref_RH97_TA20':0})
    for i,r in enumerate(rows):
        if r[t.qcc['VPD_F']]!='0':continue
        ta,rh,e=tower[i];tr,rr=ref[i];y=years[r[0][:4]];y['n']+=1;y['d'].append(rh-rr)
        y['tower_sat_TA20']+=(rh>=SAT and ta>=20);y['ref_RH97_TA20']+=(rr>=97 and tr>=20)
    return {y:{'QC0_rows':v['n'],'median_RH_tower_minus_ref':round(statistics.median(v['d']),2) if v['d'] else None,
               'tower_RH_ge_99p5_TA_ge_20':v['tower_sat_TA20'],'ref_RH_ge_97_TA_ge_20':v['ref_RH97_TA20']} for y,v in sorted(years.items())}

def jpf_reference(site,root,layout,rows):
    era=bz.era_after(site,root,layout,[r[0] for r in rows]);out=[]
    for r in rows:
        e=era[r[0]];te=num(e['TA_ERA']);ve=num(e['VPD_ERA'])
        out.append((te,min(100.,max(1.,100*(1-ve/br.es(te,'oneflux_qc_auto'))))))
    return out

def tgf_reference(root,layout):
    _,expected,_=bs.SOURCES['JP-Tgf'];path=bs.source(root,layout,'JP-Tgf');br.check(path,expected)
    with zipfile.ZipFile(path) as z:
        fill=[x for x in z.namelist() if 'ERA5_FILL' in x and '_HH_' in x][0]
        era={r['TIMESTAMP_START']:r for r in bw.csv_rows(z,fill)}
    br.check(path,expected);return era

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    a.out.mkdir();listing=[];report={'stage':'06C','status':'PROPOSED_VALUES_NOT_APPROVED','tables':{},'humidity_by_year':{}}
    for key in JPF+('JP-Tgf_HH',):
        print('STAGE06C',key,flush=True)
        site=key.split('_')[0];header,variables,rows=bz.read_table(a.cb_dir/a6.TABLE_NAME.format(key),a6.TABLES[key])
        before=[list(r) for r in rows];t=Table(key,header,variables,rows,listing);formula=a6.SITES[site][6];extra={}
        if key=='JP-Tgf_HH':
            era=tgf_reference(a.root,a.layout);lat,lon=bs.LOCATION[site]
            daily=daily_offsets(rows,t.col,t.qcc,lat,lon)
            wins=sorted([(1,x,y) for x,y in late_windows(daily,1)]+[(-1,x,y) for x,y in late_windows(daily,-1)],key=lambda w:w[1])
            extra['E2_windows']=window_evidence(rows,t.col,t.qcc,era,daily,wins)
            extra['daily_offsets_by_month']={m:round(statistics.median(v),1) for m,v in sorted(
                ((m,[x for d,x in daily.items() if x is not None and d.strftime('%Y-%m')==m]) for m in sorted({d.strftime('%Y-%m') for d in daily})),key=lambda z:z[0]) if v}
            for w in extra['E2_windows']:
                if w['proposed']:e2_shift(t,w['first'].replace('-','')+'0000',(date.fromisoformat(w['last'])+timedelta(days=1)).strftime('%Y%m%d0000'),
                                          1 if w['clock']=='late' else -1)
            ref=[(num(era[r[0]]['TA_ERA5']),min(100.,max(1.,num(era[r[0]]['RH_ERA5'])))) for r in rows]
        else:ref=jpf_reference(site,a.root,a.layout,rows)
        report['humidity_by_year'][key]=e1(t,formula,ref)
        identical=all(b[c]==r[c] for b,r in zip(before,rows) for v in variables for c in (t.col[v],t.qcc[v],t.tagc[v]) if not r[t.tagc[v]].startswith('PROPOSED_E'))
        if not identical:raise ValueError('a cell changed without a proposal in '+key)
        entry={'rows':len(rows),'proposed_by_variable_rule':{v+'|'+k:c for (v,k),c in sorted(t.counts.items())},**extra}
        if t.counts:
            w=bw.Writer(a.out/(key+'_E_proposed_NOT_APPROVED.tsv.gz'),header)
            for r in rows:w.line(r)
            entry['uncompressed_tsv_sha256'],_=w.close()
        report['tables'][key]=entry
    with (a.out/'approval_list_E_NOT_APPROVED.tsv').open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['table','variable','native_start','value_in_05CB','proposed_value','rule','05CB_tag','evidence']);w.writerows(listing)
    with (a.out/'humidity_by_year.tsv').open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['table','year','QC0_rows','median_RH_tower_minus_ref','tower_RH_ge_99p5_TA_ge_20','ref_RH_ge_97_TA_ge_20'])
        for k,ys in report['humidity_by_year'].items():
            for y,v in ys.items():w.writerow([k,y]+list(v.values()))
    report['approval_list_rows']=len(listing);report['approval_list_sha256']=br.sha(a.out/'approval_list_E_NOT_APPROVED.tsv')
    report['rule_totals']=dict(sorted(Counter(r[5] for r in listing).items()))
    report['fingerprint_integers_strings']=br.fingerprint(report)
    with (a.out/'summary_E_NOT_APPROVED.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06C COMPLETE; PROPOSED VALUES ONLY; NOTHING APPROVED OR WRITTEN TO FORCING');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'rule_totals':report['rule_totals'],'approval_list_rows':len(listing),
        'tgf_E2_windows':report['tables']['JP-Tgf_HH']['E2_windows']}))

def selftest():
    assert runs([0,1,1,0,1])==[(1,3),(4,5)] and runs([])==[]
    d0=date(2016,1,1);daily={d0+timedelta(days=k):(32. if 10<=k<60 else 2.) for k in range(90)};daily[d0+timedelta(days=30)]=None
    w=late_windows(daily);assert len(w)==1 and abs((w[0][0]-(d0+timedelta(days=10))).days)<=1 and abs((w[0][1]-(d0+timedelta(days=59))).days)<=1,w
    for k in range(33,41):daily[d0+timedelta(days=k)]=2.   # an 8-day dip inside the window is bridged
    w=late_windows(daily);assert len(w)==1 and abs((w[0][1]-(d0+timedelta(days=59))).days)<=1,w
    hdr=['TIMESTAMP_START']+[c for v in E2_VARS for c in (v,v+'_QC_ORIGINAL',v+'_TAG')];listing=[]
    rows=[[s]+[c for v in E2_VARS for c in (str(k),'0','ORIGINAL')] for k,s in enumerate(('201601010000','201601010030','201601010100','201601010130'))]
    rows[2][2]='1';t=Table('T',hdr,list(E2_VARS),rows,listing);e2_shift(t,'201601010000','201601010130')
    assert rows[0][1]=='1' and rows[1][1]=='1' and rows[2][1]=='2' and rows[3][1]=='3' and rows[0][3].startswith('PROPOSED_E2')
    assert rows[0][4]=='1' and rows[1][4]=='1' and rows[1][10]=='2'   # RH moves with TA (QC1 TA at label 3 blocks the triple); SW alone
    rows=[[s]+[c for v in E2_VARS for c in (str(k),'0','ORIGINAL')] for k,s in enumerate(('201601010000','201601010030','201601010100'))]
    t=Table('T',hdr,list(E2_VARS),rows,[]);e2_shift(t,'201601010000','201601010130',-1)
    assert rows[0][1]=='0' and rows[1][1]=='0' and rows[2][1]=='1' and rows[2][3].startswith('PROPOSED_E2_TGF_CLOCK_P30')
    early={d0+timedelta(days=k):(-31. if 10<=k<60 else 2.) for k in range(90)};assert len(late_windows(early,-1))==1 and not late_windows(early,1)
    assert abs(dew(6.112))<1e-12 and 27.9<dew(br.es(28.,'bolton1980'))<28.1
    print('STAGE06C SELF-TEST PASS: runs, late-window detection, E2 shift edge rules, dew point; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true');p.add_argument('--cb-dir',type=Path);p.add_argument('--root',type=Path)
    p.add_argument('--layout',choices=('iridis','local'));p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if None in (a.cb_dir,a.root,a.layout,a.out):p.error('--cb-dir, --root, --layout and --out required')
    run(a)
if __name__=='__main__':main()

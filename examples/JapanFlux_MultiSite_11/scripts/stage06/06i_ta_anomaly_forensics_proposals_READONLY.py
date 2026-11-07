#!/usr/bin/env python3
"""Stage06I: tower air-temperature anomalies against the reference (G2). Read-only; proposed values NOT APPROVED.

Stage05BR listed one-point TA spikes against the neighbouring half-hours (not resolved by any rule); Stage06H showed
short warm, saturated cells (JP-Khw 2021-08-12/13: 35-39 C after midnight, reference 23 C) that remain after E1A.
Inside the forcing years of every Stage06E table, d = TA_F - TA_ref, where TA_ref is the reference already approved
for gaps: same-release ERA at t+1h for the JPF sites (C3) and JapanFlux2024 ERA5_FILL at t for Tgf and Tom (D9b);
same-release ERA artifact rows (TA_ERA < -60 C) are masked. The baseline of d is its median at the same time of day
within +-15 days, which removes the systematic tower-reanalysis offset of complex terrain and its seasonal and
diurnal shape; a = d - baseline. An episode is a run of cells with |a| >= A_EDGE containing a cell with |a| >= A_CORE.
  G2A short TA fault: the episode holds measured (QC0) cells, lasts <= SPIKE_HOURS and has |a| >= A_SPIKE, or a
      warm anomaly >= A_CORE with tower RH >= RH_SAT (a wetted or heated probe; no weather departs this far from the
      reanalysis and returns within two hours).
  G2B gap-fill departure: every cell is gap-filled (QC1 MDS), so no measurement is lost.
  Proposed for both: the cells are treated as gaps; TA_F and VPD_F (and RH_F where present) take the reference
  values, exactly as C3/D9b fill gaps. Every other episode (mostly winter nights at the mountain sites, where the
  tower stands above cold pools that the reanalysis puts at the surface) is reported for review only.
Every cell outside a proposal must stay byte-identical to Stage06E (checked). Writes only to a new directory.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import warnings
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

F_PIN=('06f_build_approved_utc_noleap_datm_GUARDED.py','b974671f5f5dcc7a1e87a1f7c0403086839807a5de785fb8d8a76e6ed17b7f40')
C6_PIN=('06c_humidity_and_tgf_clock_forensics_proposals_READONLY.py','7e5f9def0392d31cad50d5a2186882c0364f745cf090ca43b052f485b4eb6a0c')
HALF_WINDOW_DAYS=15;MIN_BASE=10
A_CORE=8.;A_EDGE=4.;A_SPIKE=10.;SPIKE_HOURS=2.;RH_SAT=95.;REF_MIN=-60.

def load(pin,modname):
    name,expected=pin;path=Path(__file__).with_name(name)
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned script missing or hash mismatch '+name)
    spec=importlib.util.spec_from_file_location(modname,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f6=load(F_PIN,'stage06f_for_06i');c6=load(C6_PIN,'stage06c_for_06i');bz=c6.bz;br=c6.br;bw=c6.bw;bs=c6.bs;num=br.num

def baseline(d,spd):
    """d (n,) with NaN -> median of d at the same slot of day within +-HALF_WINDOW_DAYS (>= MIN_BASE values) else NaN."""
    n=d.size;days=-(-n//spd);x=np.full(days*spd,np.nan);x[:n]=d;x=x.reshape(days,spd)
    pad=np.full((HALF_WINDOW_DAYS,spd),np.nan);w=np.lib.stride_tricks.sliding_window_view(np.vstack([pad,x,pad]),2*HALF_WINDOW_DAYS+1,axis=0)
    cnt=np.isfinite(w).sum(-1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning);b=np.nanmedian(w,axis=-1)   # all-NaN windows -> NaN
    b[cnt<MIN_BASE]=np.nan
    return b.reshape(-1)[:n]

def runs(core,edge):
    """Index runs: maximal stretches of edge cells that contain at least one core cell."""
    out=[];i=0;n=len(edge)
    while i<n:
        if not edge[i]:i+=1;continue
        j=i
        while j<n and edge[j]:j+=1
        if core[i:j].any():out.append((i,j))
        i=j
    return out

def jf2024_fill(site,root,layout,hourly):
    _,expected,_=bs.SOURCES[site];path=bs.source(root,layout,site);br.check(path,expected)
    with zipfile.ZipFile(path) as z:
        name=[x for x in z.namelist() if 'ERA5_FILL' in x and ('_HR_' if hourly else '_HH_') in x]
        if len(name)!=1:raise ValueError('ERA5_FILL member %s'%site)
        out={r['TIMESTAMP_START']:r for r in bw.csv_rows(z,name[0])}
    br.check(path,expected);return out

def references(key,site,root,layout,rows,hourly):
    """Per row (TA_ref, VPD_ref, RH_ref or None, source label)."""
    if site in c6.JPF:
        era=bz.era_after(site,root,layout,[r[0] for r in rows])
        return [(num(era[r[0]]['TA_ERA']),num(era[r[0]]['VPD_ERA']),None) for r in rows],'ERA_T_PLUS_1H'
    fill=jf2024_fill(site,root,layout,hourly)
    return [(num(fill[r[0]]['TA_ERA5']),num(fill[r[0]]['VPD_ERA5']),min(100.,max(1.,num(fill[r[0]]['RH_ERA5'])))) for r in rows],'ERA5_FILL'

def classify(ep):
    """Episode -> G2 rule name (proposal) or REVIEW_* (reported only)."""
    if not ep['reference_complete']:return 'REVIEW_REFERENCE_INCOMPLETE'
    if ep['n_QC0']==0:return 'G2B_GAPFILL_DEPARTS'                        # MDS fill (QC1), not a measurement
    warm_saturated=ep['peak_anomaly']>=A_CORE and ep['peak_RH']>=RH_SAT
    if ep['hours']<=SPIKE_HOURS and (abs(ep['peak_anomaly'])>=A_SPIKE or warm_saturated):return 'G2A_SHORT_TA_FAULT'
    if warm_saturated:return 'REVIEW_WARM_SATURATED'                     # long: mountain cloud or fog is possible
    return 'REVIEW_ONLY'

def value(x):
    """Proposed value as table text; must read back as the same finite number."""
    s=bw.fmt(float(x))
    if not math.isfinite(num(s)) or num(s)!=round(float(x),6):raise ValueError('proposed value does not read back: %r'%s)
    return s

def dew_vpd(ta,vpd,formula):
    e=br.es(ta,formula)-vpd
    return c6.dew(e) if e>0 else float('nan')

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    a.out.mkdir();listing=[];episodes=[];report={'stage':'06I','status':'PROPOSED_VALUES_NOT_APPROVED',
        'thresholds':{'half_window_days':HALF_WINDOW_DAYS,'A_core':A_CORE,'A_edge':A_EDGE,'A_spike':A_SPIKE,'spike_hours':SPIKE_HOURS,'RH_sat':RH_SAT,'ref_min':REF_MIN},'tables':{}}
    for site,(keys,y0,y1,*_,formula) in f6.a6.SITES.items():
        y0,y1=f6.YEARS.get(site,(y0,y1))
        for key in keys:
            print('STAGE06I',key,flush=True)
            header,variables,rows=bz.read_table(a.table_dir/f6.TABLE_NAME.format(key),f6.TABLES[key])
            before=[list(r) for r in rows];t=c6.Table(key,header,variables,rows,listing)
            step=br.stamp(rows[1][0])-br.stamp(rows[0][0]);hourly=step.total_seconds()==3600;spd=24 if hourly else 48
            ref,label=references(key,site,a.root,a.layout,rows,hourly)
            ta=np.array([num(r[t.col['TA_F']]) for r in rows]);tr=np.array([x[0] if x[0]>=REF_MIN else np.nan for x in ref])   # ERA artifact rows
            inside=np.array([y0<=int(r[0][:4])<=y1 for r in rows]);d=ta-tr;base=baseline(d,spd);an=d-base
            stats={'cells':int(inside.sum()),'baseline_missing':int((inside&~np.isfinite(base)).sum())}
            ok=inside&np.isfinite(an);aa=np.where(ok,np.abs(an),0.)
            for q in (99.,99.9,99.99):stats['abs_anomaly_p%g'%q]=round(float(np.percentile(aa[ok],q)),2) if ok.any() else None
            for thr in (6,8,10,12):stats['abs_anomaly_ge_%d'%thr]=int((aa>=thr).sum())
            proposed=0
            for i,j in runs(aa>=A_CORE,aa>=A_EDGE):
                peak=int(np.argmax(aa[i:j]))+i;vp=num(rows[peak][t.col['VPD_F']]);tdp=dew_vpd(ta[peak],vp,formula);tdr=dew_vpd(tr[peak],ref[peak][1],formula)
                ep={'table':key,'first':rows[i][0],'last':rows[j-1][0],'cells':j-i,'hours':round((j-i)*24/spd,1),
                    'n_QC0':sum(rows[k][t.qcc['TA_F']]=='0' for k in range(i,j)),'TA_QC':''.join(sorted(set(rows[k][t.qcc['TA_F']] for k in range(i,j)))),
                    'reference_complete':bool(all(np.isfinite(tr[k]) and math.isfinite(ref[k][1]) for k in range(i,j))),
                    'peak_time':rows[peak][0],'peak_TA':round(float(ta[peak]),2),'peak_ref_TA':round(float(tr[peak]),2),'peak_anomaly':round(float(an[peak]),2),
                    'baseline_at_peak':round(float(base[peak]),2),'peak_RH':round(100*(1-vp/br.es(ta[peak],formula)),1),
                    'peak_Td':round(tdp,2) if math.isfinite(tdp) else None,'peak_ref_Td':round(tdr,2) if math.isfinite(tdr) else None}
                ep['class']=classify(ep);ep['proposed']=ep['class'].startswith('G2');episodes.append(ep)
                if not ep['proposed']:continue
                rule=ep['class']+'_'+label;ev='episode %s..%s peak a %+.1f C'%(ep['first'],ep['last'],ep['peak_anomaly'])
                for k in range(i,j):
                    # float(): repr of a NumPy scalar is 'np.float64(...)', which reads back as missing
                    t.put(k,'TA_F',value(tr[k]),rule,ev);t.put(k,'VPD_F',value(ref[k][1]),rule,ev)
                    if 'RH_F' in t.col:t.put(k,'RH_F',value(ref[k][2]),rule,ev)
                    proposed+=1
            identical=all(b[c]==r[c] for b,r in zip(before,rows) for v in variables for c in (t.col[v],t.qcc[v],t.tagc[v]) if not r[t.tagc[v]].startswith('PROPOSED_G2'))
            if not identical:raise ValueError('a cell changed without a proposal in '+key)
            entry={'forcing_years':[y0,y1],'reference':label,'anomaly_stats':stats,'proposed_rows':proposed,
                   'proposed_by_variable_rule':{v+'|'+k:c for (v,k),c in sorted(t.counts.items())}}
            if t.counts:
                w=bw.Writer(a.out/(key+'_G2_proposed_NOT_APPROVED.tsv.gz'),header)
                for r in rows:w.line(r)
                entry['uncompressed_tsv_sha256'],_=w.close()
            report['tables'][key]=entry
    with (a.out/'approval_list_G2_NOT_APPROVED.tsv').open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['table','variable','native_start','value_in_06E','proposed_value','rule','06E_tag','evidence']);w.writerows(listing)
    cols=list(episodes[0]) if episodes else ['table']
    with (a.out/'ta_anomaly_episodes.tsv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,cols,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(episodes)
    report['episodes']=len(episodes);report['episodes_proposed']=sum(e['proposed'] for e in episodes)
    report['approval_list_rows']=len(listing);report['approval_list_sha256']=br.sha(a.out/'approval_list_G2_NOT_APPROVED.tsv')
    report['rule_totals']=dict(sorted(Counter(r[5] for r in listing).items()));report['fingerprint_integers_strings']=br.fingerprint(report)
    with (a.out/'summary_G2_NOT_APPROVED.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06I COMPLETE; PROPOSED VALUES ONLY; NOTHING APPROVED OR WRITTEN TO FORCING');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'episodes':len(episodes),'episodes_proposed':report['episodes_proposed'],
        'rule_totals':report['rule_totals'],'per_table':{k:{'proposed_rows':v['proposed_rows'],**v['anomaly_stats']} for k,v in report['tables'].items()}}))

def selftest():
    spd=4;d=np.tile([0.,1.,2.,1.],40).astype(float);d[50]=20.;b=baseline(d,spd)
    assert b[50]==2. and np.isnan(baseline(d[:8],spd)).all()
    core=np.array([0,0,1,0,0,1,1,0],bool);edge=np.array([0,1,1,1,0,1,1,1],bool)
    assert runs(core,edge)==[(1,4),(5,8)] and runs(np.zeros(3,bool),np.ones(3,bool))==[]
    ep=lambda **k:{'reference_complete':True,'n_QC0':1,'hours':0.5,'peak_anomaly':12.,'peak_RH':50.,**k}
    assert classify(ep())=='G2A_SHORT_TA_FAULT' and classify(ep(peak_anomaly=-10.5))=='G2A_SHORT_TA_FAULT'
    assert classify(ep(peak_anomaly=9.,peak_RH=97.))=='G2A_SHORT_TA_FAULT' and classify(ep(peak_anomaly=-9.,peak_RH=97.))=='REVIEW_ONLY'
    assert classify(ep(hours=2.5))=='REVIEW_ONLY' and classify(ep(hours=10.,peak_anomaly=9.,peak_RH=99.))=='REVIEW_WARM_SATURATED'
    assert classify(ep(n_QC0=0,hours=40.))=='G2B_GAPFILL_DEPARTS' and classify(ep(reference_complete=False,n_QC0=0))=='REVIEW_REFERENCE_INCOMPLETE'
    assert value(np.float64(-6.5751))=='-6.5751' and value(np.array([12.25])[0])=='12.25' and value(3)=='3.0'
    for bad in (np.nan,np.inf):
        try:value(bad)
        except ValueError:pass
        else:raise AssertionError('non-finite proposal accepted')
    print('STAGE06I SELF-TEST PASS: slot-of-day baseline, episode runs, episode classes, proposed values read back; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true');p.add_argument('--table-dir',type=Path,help='Stage06E output');p.add_argument('--root',type=Path)
    p.add_argument('--layout',choices=('iridis','local'));p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if None in (a.table_dir,a.root,a.layout,a.out):p.error('--table-dir, --root, --layout and --out required')
    run(a)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Stage06M: remaining forcing variables against physics and the reference (H rules). Read-only; NOT APPROVED.

Stage06I screened TA only. Inside the forcing years of every Stage06J table (Stage06K years), this stage checks:
  H1 LW_IN physical bound: effective sky emissivity LW_IN / (sigma (TA+273.15)^4) outside [EPS_LO, EPS_HI] (clear,
     very dry and cold air is about 0.56-0.6), in episodes of <= 6 h. Site-years with >= 50 such cells, or whose median
     QC0 LW_IN minus reference is >= 30 W m-2 or >= 20 W m-2 from the site's other years, are a sensor or calibration
     matter decided per site-year: reported (REVIEW_LW_SYSTEMATIC), not proposed cell by cell.
  H2 SW_IN physical bound: SW_IN above the largest top-of-atmosphere irradiance within the interval +-30 min plus
     SW_MARGIN, or above SW_NIGHT while that window is entirely night (the +-30 min pad covers the accepted
     sub-slot clock limits). Night SW recurring on >= 5 days with gaps <= 15 days points to a logger or processing
     error over a window (REVIEW_NIGHT_SW_RECURRING, reported with the median daily SW centroid offset) and is decided
     per window, not cell by cell. The daily centroid alone is not used to find clock windows: cloud timing moves it
     by 15-30 min at every site.
  H3 gap-fill departure (as G2B): for VPD, LW_IN, WS and PA, d = tower - reference, baseline = median of d at the same
     time of day within +-15 days (Stage06I), a = d - baseline; an episode of |a| >= edge containing |a| >= core whose
     cells are all gap-filled (QC1 MDS), so no measurement is lost.
  H4 PA short fault: an H3-type PA episode with measured (QC0) cells lasting <= 2 h.
  Reference: the approved gap source, same-release ERA at t+1h for the JPF sites (C3) and JapanFlux2024 ERA5_FILL at t
  for Tgf/Tom (D9b); ERA artifact rows (TA < -60 C, PA < 50 kPa, LW < 60 W m-2) are masked.
  Proposed values (cells treated as gaps): LW_IN, SW_IN, WS, PA take the reference value; VPD takes the reference
  RH at the tower TA (approved D9/E1 method), with RH_F = reference RH where present. Every other episode is
  reported for review only. Every cell outside a proposal must stay byte-identical to Stage06J (checked).
Writes only to a new directory; no forcing, case, Slurm or source change.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np

K_PIN=('06k_build_approved_utc_noleap_datm_GUARDED.py','d8d7edce6008afc4028a9a727cee61db462ce2cad75a4efc29298280d581f66e')
I_PIN=('06i_ta_anomaly_forensics_proposals_READONLY.py','bb142d5b621c06158d500b0e1a4fa684c9af5b1fd8b843f5cf5f37c7c20862bf')
SIGMA=5.670374419e-8
EPS_LO=0.55;EPS_HI=1.15
SW_MARGIN=50.;SW_NIGHT=20.;TOA_PAD_MIN=30;NIGHT_GAP_DAYS=15;NIGHT_CLUSTER_DAYS=5
H1_MAX_HOURS=6.;H1_SYS_CELLS=50;LW_SYS_REL=20.;LW_SYS_ABS=30.
GAP={'VPD_F':(10.,5.),'LW_IN_F':(100.,50.),'WS_F':(6.,3.),'PA_F':(1.,.5)}   # (core, edge) |a| in hPa, W m-2, m s-1, kPa
PA_FAULT_HOURS=2.
VARS=('TA_F','PA_F','VPD_F','SW_IN_F','LW_IN_F','WS_F')
REFCOL={'ERA_T_PLUS_1H':{'TA_F':'TA_ERA','PA_F':'PA_ERA','VPD_F':'VPD_ERA','SW_IN_F':'SW_IN_ERA','LW_IN_F':'LW_IN_ERA','WS_F':'WS_ERA'},
        'ERA5_FILL':{'TA_F':'TA_ERA5','PA_F':'PA_ERA5','VPD_F':'VPD_ERA5','SW_IN_F':'SW_IN_ERA5','LW_IN_F':'LW_ERA5','WS_F':'WS_ERA5','RH_F':'RH_ERA5'}}

def load(pin,modname):
    name,expected=pin;path=Path(__file__).with_name(name)
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned script missing or hash mismatch '+name)
    spec=importlib.util.spec_from_file_location(modname,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
k6=load(K_PIN,'stage06k_for_06m');i6=load(I_PIN,'stage06i_for_06m');c6=i6.c6;bz=c6.bz;br=c6.br;bw=c6.bw;num=br.num

def es(t,formula):
    a,b,c=br.ES_FORMULAS[formula];return a*np.exp(b*t/(t+c))

def references(site,root,layout,rows,hourly,formula):
    """{variable: array} of the approved gap reference per row (artifact rows NaN) and its label."""
    if site in c6.JPF:
        era=bz.era_after(site,root,layout,[r[0] for r in rows]);src=[era[r[0]] for r in rows];label='ERA_T_PLUS_1H'
    else:
        fill=i6.jf2024_fill(site,root,layout,hourly);src=[fill[r[0]] for r in rows];label='ERA5_FILL'
    ref={v:np.array([num(s[c]) for s in src]) for v,c in REFCOL[label].items()}
    for x in ref.values():x[~np.isfinite(x)|(x<=-9990)]=np.nan
    bad=~(ref['TA_F']>=-60)|~(ref['PA_F']>=50)|~(ref['LW_IN_F']>=60)
    for x in ref.values():x[bad]=np.nan
    if 'RH_F' not in ref:ref['RH_F']=np.clip(100*(1-ref['VPD_F']/es(ref['TA_F'],'oneflux_qc_auto')),1,100)
    else:ref['RH_F']=np.clip(ref['RH_F'],1,100)
    return ref,label

def toa_window(stamps,lat,lon,step_min):
    """Largest top-of-atmosphere irradiance within [start - pad, start + step + pad] for local (UTC+9) interval starts
    (same solar formulas as Stage06A toa_utc), every 5 min."""
    t0=np.array(['%s-%s-%sT%s:%s'%(s[:4],s[4:6],s[6:8],s[8:10],s[10:12]) for s in stamps],dtype='datetime64[m]')
    best=np.zeros(len(stamps))
    for off in range(-TOA_PAD_MIN,step_min+TOA_PAD_MIN+1,5):best=np.maximum(best,toa_at(t0,lat,lon,off))
    return best,toa_at(t0,lat,lon,step_min/2)

def toa_at(t0,lat,lon,off):
    """Instantaneous top-of-atmosphere irradiance at local (UTC+9) times t0 + off minutes."""
    u=t0+np.timedelta64(int(round(off*60))-9*3600,'s');day=u.astype('datetime64[D]')
    doy=(day-u.astype('datetime64[Y]')).astype(int)+1;hu=(u-day).astype('timedelta64[s]').astype(int)/3600.
    g=2*np.pi/365*(doy-1+(hu-12)/24)
    eot=229.18*(.000075+.001868*np.cos(g)-.032077*np.sin(g)-.014615*np.cos(2*g)-.040849*np.sin(2*g))
    dec=(.006918-.399912*np.cos(g)+.070257*np.sin(g)-.006758*np.cos(2*g)+.000907*np.sin(2*g)-.002697*np.cos(3*g)+.00148*np.sin(3*g))
    ha=np.radians((hu*60+eot+4*lon)/4-180);phi=np.radians(lat);cz=np.sin(phi)*np.sin(dec)+np.cos(phi)*np.cos(dec)*np.cos(ha)
    return 1361*(1+.033*np.cos(2*np.pi*doy/365))*np.maximum(cz,0.)

def daily_offsets(sw,toa_c,qc,stamps,spd):
    """{date: SW centroid minus TOA centroid in minutes, or None} per local day (>= 90 % QC0 SW, daily SW >= 20 % of TOA),
    as Stage06C for Tgf."""
    n=len(sw)//spd*spd;S=np.clip(np.nan_to_num(sw[:n]),0,None).reshape(-1,spd);T=toa_c[:n].reshape(-1,spd);Q=(qc[:n]=='0').reshape(-1,spd)
    m=(np.arange(spd)+.5)*1440./spd
    with np.errstate(invalid='ignore',divide='ignore'):off=(S*m).sum(1)/S.sum(1)-(T*m).sum(1)/T.sum(1)
    good=(Q.sum(1)>=.9*spd)&(T.sum(1)>0)&(S.sum(1)>=.2*T.sum(1))
    return {date(int(stamps[d*spd][:4]),int(stamps[d*spd][4:6]),int(stamps[d*spd][6:8])):(float(off[d]) if good[d] else None) for d in range(n//spd)}

def night_clusters(days):
    """Sorted dates with night SW -> clusters (gaps <= NIGHT_GAP_DAYS) of >= NIGHT_CLUSTER_DAYS dates: a recurring
    sunrise/sunset signature points to a logger clock error, not to isolated sensor faults."""
    groups=[]
    for d in days:
        if groups and (d-groups[-1][-1]).days<=NIGHT_GAP_DAYS:groups[-1].append(d)
        else:groups.append([d])
    return [g for g in groups if len(g)>=NIGHT_CLUSTER_DAYS]

def lw_by_year(lw,ref,qc,years):
    """{year: median LW_IN - reference over QC0 rows (>= 1000)}, and the years that are systematically off (decision level)."""
    out={}
    for y in sorted(set(years.tolist())):
        sel=(years==y)&(qc=='0')&np.isfinite(lw)&np.isfinite(ref)
        if sel.sum()>=1000:out[int(y)]=round(float(np.median(lw[sel]-ref[sel])),1)
    if not out:return out,set()
    mid=float(np.median(list(out.values())))
    return out,{y for y,v in out.items() if abs(v-mid)>=LW_SYS_REL or abs(v)>=LW_SYS_ABS}

def classify(check,n_qc0,hours,complete,is_reference=False,flag=None):
    if not complete:return 'REVIEW_REFERENCE_INCOMPLETE'
    if is_reference:return 'REVIEW_VALUE_IS_REFERENCE'                    # e.g. JPF QC2 = ERA at t+1h already (C3)
    if flag:return 'REVIEW_'+flag                                         # decided per site-year or window, not per cell
    if check=='H1':return 'H1' if hours<=H1_MAX_HOURS else 'REVIEW_ONLY'
    if check=='H2':return 'H2'
    if n_qc0==0:return 'H3'
    if check=='PA_F' and hours<=PA_FAULT_HOURS:return 'H4'
    return 'REVIEW_ONLY'
RULE={'H1':'H1_LW_IMPLAUSIBLE','H2':'H2_SW_IMPLAUSIBLE','H3':'H3_GAPFILL_DEPARTS','H4':'H4_PA_SHORT_FAULT'}

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    a.out.mkdir();listing=[];episodes=[];report={'stage':'06M','status':'PROPOSED_VALUES_NOT_APPROVED','tables':{},
        'thresholds':{'eps_lo':EPS_LO,'eps_hi':EPS_HI,'sw_margin':SW_MARGIN,'sw_night':SW_NIGHT,'toa_pad_min':TOA_PAD_MIN,'gap_core_edge':GAP,
                      'pa_fault_hours':PA_FAULT_HOURS,'baseline_half_window_days':i6.HALF_WINDOW_DAYS}}
    for site,(keys,y0,y1,lat,lon,_,formula) in k6.a6.SITES.items():
        y0,y1=k6.YEARS.get(site,(y0,y1))
        for key in keys:
            print('STAGE06M',key,flush=True)
            header,variables,rows=bz.read_table(a.table_dir/k6.TABLE_NAME.format(key),k6.TABLES[key])
            before=[list(r) for r in rows];t=c6.Table(key,header,variables,rows,listing)
            step=int((br.stamp(rows[1][0])-br.stamp(rows[0][0])).total_seconds()//60);spd=1440//step
            ref,label=references(site,a.root,a.layout,rows,step==60,formula)
            inside=np.array([y0<=int(r[0][:4])<=y1 for r in rows])
            X={v:np.array([num(r[t.col[v]]) for r in rows]) for v in VARS}
            stamps=[r[0] for r in rows];years=np.array([int(s[:4]) for s in stamps])
            eps=X['LW_IN_F']/(SIGMA*(X['TA_F']+273.15)**4);toa,toa_c=toa_window(stamps,lat,lon,step)
            lwy,lw_sys=lw_by_year(X['LW_IN_F'],ref['LW_IN_F'],np.array([r[t.qcc['LW_IN_F']] for r in rows]),np.where(inside,years,0))
            lwy.pop(0,None);lw_sys.discard(0)
            h1=inside&np.isfinite(eps)&((eps<EPS_LO)|(eps>EPS_HI))
            h1_years=Counter(years[h1].tolist());lw_sys|={y for y,n in h1_years.items() if n>=H1_SYS_CELLS}
            night=inside&(toa==0)&(X['SW_IN_F']>SW_NIGHT)
            daily=daily_offsets(X['SW_IN_F'],toa_c,np.array([r[t.qcc['SW_IN_F']] for r in rows]),stamps,spd)
            clusters=night_clusters(sorted({date(int(stamps[k][:4]),int(stamps[k][4:6]),int(stamps[k][6:8])) for k in np.flatnonzero(night)}))
            recurring_days={d for c in clusters for d in c}
            ok=inside&np.isfinite(eps);stats={'cells':int(inside.sum()),'LW_tower_minus_ref_median_by_year_QC0':{str(y):v for y,v in lwy.items()},
                'LW_implausible_cells_by_year':{str(y):n for y,n in sorted(h1_years.items())},'LW_systematic_years':sorted(lw_sys),
                'SW_night_clusters':[{'first':str(c[0]),'last':str(c[-1]),'days_with_night_SW':len(c),
                    'median_daily_SW_centroid_offset_min':(lambda v:round(float(np.median(v)),1) if v else None)([daily[d] for d in c if daily.get(d) is not None])} for c in clusters],
                'LW_emissivity_percentiles':{q:round(float(np.percentile(eps[ok],float(q))),3) for q in ('0.01','0.1','1','99','99.9','99.99')} if ok.any() else {},
                'LW_eps_lt_lo':int((ok&(eps<EPS_LO)).sum()),'LW_eps_gt_hi':int((ok&(eps>EPS_HI)).sum()),
                'SW_above_TOA':int((inside&(X['SW_IN_F']>toa+SW_MARGIN)).sum()),'SW_at_night':int((inside&(toa==0)&(X['SW_IN_F']>SW_NIGHT)).sum())}
            h2=inside&((X['SW_IN_F']>toa+SW_MARGIN)|night)
            checks=[('H1','LW_IN_F',h1,h1,None,np.abs(np.nan_to_num(eps,nan=.85)-.85)),('H2','SW_IN_F',h2,h2,None,np.nan_to_num(X['SW_IN_F']-toa))]
            for v,(core,edge) in GAP.items():
                d=X[v]-ref[v];an=d-i6.baseline(d,spd);aa=np.where(inside&np.isfinite(an),np.abs(an),0.)
                stats['%s_abs_anomaly_ge_core'%v]=int((aa>=core).sum());checks.append((v,v,aa>=core,aa>=edge,an,aa))
            for check,v,core,edge,an,metric in checks:
                for i,j in i6.runs(core,edge):
                    if any(rows[k][t.tagc[v]].startswith('PROPOSED_H') for k in range(i,j)):continue   # already proposed by an earlier check
                    n0=sum(rows[k][t.qcc[v]]=='0' for k in range(i,j));hours=(j-i)*step/60.
                    complete=bool(all(np.isfinite(ref[v][k]) and (v!='VPD_F' or np.isfinite(ref['RH_F'][k])) for k in range(i,j)))
                    same=complete and bool(np.allclose(X[v][i:j],ref[v][i:j],rtol=0,atol=1e-6))
                    days={date(int(rows[k][0][:4]),int(rows[k][0][4:6]),int(rows[k][0][6:8])) for k in range(i,j)}
                    flag=('LW_SYSTEMATIC' if check=='H1' and any(int(rows[k][0][:4]) in lw_sys for k in range(i,j)) else
                          'NIGHT_SW_RECURRING' if check=='H2' and night[i:j].all() and days&recurring_days else None)
                    cls=classify(check,n0,hours,complete,same,flag);peak=i+int(np.argmax(metric[i:j]))
                    ep={'table':key,'variable':v,'check':check,'class':cls,'first':rows[i][0],'last':rows[j-1][0],'cells':j-i,'hours':hours,'n_QC0':n0,
                        'QC':''.join(sorted(set(rows[k][t.qcc[v]] for k in range(i,j)))),'peak_time':rows[peak][0],'peak_value':round(float(X[v][peak]),3),
                        'peak_ref':None if not np.isfinite(ref[v][peak]) else round(float(ref[v][peak]),3),'peak_anomaly':None if an is None else round(float(an[peak]),3),
                        'peak_eps':round(float(eps[peak]),3) if np.isfinite(eps[peak]) else None,'peak_TOA':round(float(toa[peak]),1),'proposed':cls in RULE}
                    episodes.append(ep)
                    if not ep['proposed']:continue
                    rule=RULE[cls]+'_'+label;ev='%s episode %s..%s'%(check,ep['first'],ep['last'])
                    for k in range(i,j):
                        if v=='VPD_F':
                            t.put(k,'VPD_F',i6.value(es(X['TA_F'][k],formula)*(1-ref['RH_F'][k]/100)),rule+'_REF_RH_AT_TOWER_TA',ev)
                            if 'RH_F' in t.col:t.put(k,'RH_F',i6.value(ref['RH_F'][k]),rule,ev)
                        else:t.put(k,v,i6.value(ref[v][k]),rule,ev)
            identical=all(b[c]==r[c] for b,r in zip(before,rows) for v in variables for c in (t.col[v],t.qcc[v],t.tagc[v]) if not r[t.tagc[v]].startswith('PROPOSED_H'))
            if not identical:raise ValueError('a cell changed without a proposal in '+key)
            entry={'forcing_years':[y0,y1],'reference':label,'stats':stats,'proposed_by_variable_rule':{v+'|'+k:c for (v,k),c in sorted(t.counts.items())},
                   'episodes_by_check_class':dict(sorted(Counter(e['check']+'|'+e['class'] for e in episodes if e['table']==key).items()))}
            if t.counts:
                w=bw.Writer(a.out/(key+'_H_proposed_NOT_APPROVED.tsv.gz'),header)
                for r in rows:w.line(r)
                entry['uncompressed_tsv_sha256'],_=w.close()
            report['tables'][key]=entry
    with (a.out/'approval_list_H_NOT_APPROVED.tsv').open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['table','variable','native_start','value_in_06J','proposed_value','rule','06J_tag','evidence']);w.writerows(listing)
    with (a.out/'h_screen_episodes.tsv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(episodes[0]) if episodes else ['table'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(episodes)
    report['episodes']=len(episodes);report['episodes_proposed']=sum(e['proposed'] for e in episodes)
    report['episodes_by_check_class']=dict(sorted(Counter(e['check']+'|'+e['class'] for e in episodes).items()))
    report['approval_list_rows']=len(listing);report['approval_list_sha256']=br.sha(a.out/'approval_list_H_NOT_APPROVED.tsv')
    report['rule_totals']=dict(sorted(Counter(r[1]+'|'+r[5] for r in listing).items()));report['fingerprint_integers_strings']=br.fingerprint(report)
    with (a.out/'summary_H_NOT_APPROVED.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06M COMPLETE; PROPOSED VALUES ONLY; NOTHING APPROVED OR WRITTEN TO FORCING');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'episodes':len(episodes),'episodes_proposed':report['episodes_proposed'],
        'approval_list_rows':len(listing),'episodes_by_check_class':report['episodes_by_check_class'],'rule_totals':report['rule_totals'],
        'stats':{k:v['stats'] for k,v in report['tables'].items()}}))

def selftest():
    toa,mid=toa_window(['201606211200','201606210000','201612211200'],36.,140.,30)      # local noon / midnight near Tsukuba
    assert 1100<toa[0]<1361*1.034 and toa[1]==0 and 500<toa[2]<toa[0] and mid[1]==0 and 0<mid[0]<=toa[0]
    # daily clock: TOA itself gives 0; SW one hour late gives about +60 min
    st=['20160621%02d%02d'%(h,m) for h in range(24) for m in (0,30)];c=toa_window(st,36.,140.,30)[1]
    assert abs(daily_offsets(c,c,np.array(['0']*48),st,48)[date(2016,6,21)])<1e-6
    assert 55<daily_offsets(np.roll(c,2),c,np.array(['0']*48),st,48)[date(2016,6,21)]<65
    yrs=np.repeat([2001,2002,2003],1500);qc=np.array(['0']*4500);lw=np.r_[np.full(1500,300.),np.full(1500,300.),np.full(1500,260.)]
    by,sysy=lw_by_year(lw,np.full(4500,302.),qc,yrs);assert by=={2001:-2.,2002:-2.,2003:-42.} and sysy=={2003}
    assert classify('H1',3,1.,True)=='H1' and classify('H1',3,8.,True)=='REVIEW_ONLY' and classify('H1',3,1.,True,False,'LW_SYSTEMATIC')=='REVIEW_LW_SYSTEMATIC'
    assert classify('H2',3,1.,True,False,'NIGHT_SW_RECURRING')=='REVIEW_NIGHT_SW_RECURRING' and classify('H2',3,1.,True)=='H2'
    d0=date(2009,2,1);cl=night_clusters([d0+__import__('datetime').timedelta(days=k) for k in (0,3,9,20,30,80,200,201)])
    assert len(cl)==1 and len(cl[0])==5 and cl[0][-1]==date(2009,3,3)
    assert classify('PA_F',0,40.,True)=='H3' and classify('PA_F',2,1.5,True)=='H4'
    assert classify('PA_F',2,3.,True)=='REVIEW_ONLY' and classify('WS_F',1,1.,True)=='REVIEW_ONLY' and classify('LW_IN_F',0,1.,False)=='REVIEW_REFERENCE_INCOMPLETE'
    assert classify('H1',0,1.,True,True)=='REVIEW_VALUE_IS_REFERENCE'
    assert abs(es(np.array([20.]),'oneflux_qc_auto')[0]-br.es(20.,'oneflux_qc_auto'))<1e-12
    t=273.15+10;assert abs(SIGMA*t**4-364.)<1.
    print('STAGE06M SELF-TEST PASS: TOA window, daily clock offset, LW systematic years, episode classes, es, Stefan-Boltzmann; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true');p.add_argument('--table-dir',type=Path,help='Stage06J output');p.add_argument('--root',type=Path)
    p.add_argument('--layout',choices=('iridis','local'));p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if None in (a.table_dir,a.root,a.layout,a.out):p.error('--table-dir, --root, --layout and --out required')
    run(a)
if __name__=='__main__':main()

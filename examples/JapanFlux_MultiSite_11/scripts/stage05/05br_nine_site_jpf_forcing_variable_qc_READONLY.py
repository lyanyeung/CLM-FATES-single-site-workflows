#!/usr/bin/env python3
"""Stage05BR: nine-site JPF forcing-variable QC evidence. Read-only; no forcing, case or Slurm writes.

Per site it streams the original nested FLUXMET_HH once and reports, for the seven
DATM-relevant variables (TA_F, PA_F, VPD_F, SW_IN_F, LW_IN_F, WS_F, P_F): exact BIFVARINFO
unit/definition text, QC composition by year, broad physical limits, flatlines and spikes,
pressure versus elevation and ERA, precipitation totals by source, PPFD/SW ratio, the
saturation-vapour-pressure formula implied by raw RH/VPD, QBOT feasibility, and two clock
tests (clear-day SW centroid versus solar geometry; TA first-difference lag versus same-file
ERA). Gross same-release ERA artifact windows are listed with every F field and QC.
The clock tests are statistics with stated assumptions, not proof of a logger clock.
Output JSON/TSV carry no paths or run times so a rerun on byte-identical ZIPs reproduces
the integer fingerprint exactly.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from array import array
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath

IRIDIS_ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
SITES={
 'JP-Api':('JPF_JP-Api_FLUXNET_2000-2022_v1.3_r2','dab9de152210d4f95d88c79c7b9e67bd5ccde19fee86304bee093634f000342b',403248),
 'JP-Fhk':('JPF_JP-Fhk_FLUXNET_2006-2023_v1.3_r1','20abdd06ed23de7d599841e8ac64a21b2378a169deae6f3f891f6230e4a31667',315552),
 'JP-Fjy':('JPF_JP-Fjy_FLUXNET_2001-2021_v1.3_r1','205660bb8203bf7b16466041183ec9a1598f609727ef042ff4bceb800da949b9',368160),
 'JP-Khw':('JPF_JP-Khw_FLUXNET_2000-2021_v1.3_r1','712ab4695704a695c28056eb0cfae0697af8a673228407dbc856088ad83bac79',385728),
 'JP-Spp':('JPF_JP-Spp_FLUXNET_2000-2018_v1.3_r1','6941f9bf4c6f7f2e80c9a7c991fde1b2c92bc3d7a111321ae50bd7d370d35aaf',333120),
 'JP-Tak':('JPF_JP-Tak_FLUXNET_1998-2021_v1.3_r1','cf1da393c026deb35dcc9b328bf5c7ae7ca9eea22dbbf8a095907e06373dc151',420768),
 'JP-Tef':('JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1','315c825b64669aa03daff1d969f58a0a1cf3b574c43400ea1f84588df7f6d684',403200),
 'JP-Tmd':('JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1','3ef287018725cb2b5b4c78130804febbe022dad66415807e70f628b756a13479',333072),
 'JP-Yms':('JPF_JP-Yms_FLUXNET_2000-2023_v1.3_r1','6bda3beb4fd9b580ef036e4b50f9c3162ca17b82b2b28466820e665bdedbf6f7',420768)}
VARS=('TA_F','PA_F','VPD_F','SW_IN_F','LW_IN_F','WS_F','P_F')
REQUIRED=('TIMESTAMP_START','TIMESTAMP_END','SW_IN_POT','TA_ERA','SW_IN_ERA','LW_IN_ERA','VPD_ERA','PA_ERA','P_ERA','WS_ERA')+VARS+tuple(v+'_QC' for v in VARS)
OPTIONAL=('RH','PA','P','WS','PPFD_IN','NIGHT')
EXPECTED_UNITS={'TA_F':'deg C','PA_F':'kPa','VPD_F':'hPa','SW_IN_F':'W m-2','LW_IN_F':'W m-2','WS_F':'m s-1','P_F':'mm'}
# es(T)=a*exp(b*T/(T+c)) hPa over water; candidate producer formulas for the RH/VPD inversion test.
# oneflux_qc_auto is ONEFlux qc_auto set_vpd (main.c L668-670, tag v1.3.7-rc): 6.11*exp(17.26938818*T/(237.3+T)).
ES_FORMULAS={'oneflux_qc_auto':(6.11,17.26938818,237.3),'bolton1980':(6.112,17.67,243.5),'tetens_fao56':(6.108,17.27,237.3),
             'alduchov1996':(6.1094,17.625,243.04),'buck1981':(6.1121,17.502,240.97)}
# CDEPS cdeps1.0.113 datm_datamode_clmncep_mod.F90 datm_eSat: hPa polynomials, ice when TBOT<273.15 K; DATM caps QBOT at this qsat.
DATM_WATER=(6.107799961,4.436518521e-01,1.428945805e-02,2.650648471e-04,3.031240396e-06,2.034080948e-08,6.136820929e-11)
DATM_ICE=(6.109177956,5.034698970e-01,1.886013408e-02,4.176223716e-04,5.824720280e-06,4.838803174e-08,1.838826904e-10)
SIGMA=5.670374419e-8
CAP=512*1024*1024

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def check(path,expected):
    if path.is_symlink() or not path.is_file() or sha(path)!=expected:raise ValueError('missing/symlink/hash mismatch '+str(path))
def num(value):
    try:x=float(value)
    except (ValueError,TypeError):return math.nan
    return x if math.isfinite(x) and x>-9990 else math.nan
def qc(value):
    x=num(value)
    return -1 if math.isnan(x) else int(round(x))
def stamp(s):
    if len(s)!=12 or not s.isdigit():raise ValueError('invalid timestamp '+repr(s))
    return datetime.strptime(s,'%Y%m%d%H%M')
def r6(x):
    return None if x is None or (isinstance(x,float) and not math.isfinite(x)) else round(x,6)
def es(t,formula='bolton1980'):
    a,b,c=ES_FORMULAS[formula]
    return a*math.exp(b*t/(t+c))
def datm_esat_hpa(t):
    c=DATM_ICE if t<0 else DATM_WATER;x=min(50.,max(-50.,t));v=0.
    for a in reversed(c):v=v*x+a
    return v
def p_standard(z):
    return 101.325*(1-2.25577e-5*z)**5.25588
def quant(xs,q):
    if not xs:return None
    s=sorted(xs);k=(len(s)-1)*q;i=int(math.floor(k));j=min(i+1,len(s)-1)
    return s[i]+(s[j]-s[i])*(k-i)
def summary(xs):
    return {'n':len(xs),'median':r6(quant(xs,.5)),'p25':r6(quant(xs,.25)),'p75':r6(quant(xs,.75)),
            'p05':r6(quant(xs,.05)),'p95':r6(quant(xs,.95))} if xs else {'n':0}

def toa_mean(dt,lat,lon,tz,steps=6):
    """Mean top-of-atmosphere irradiance (W m-2) over [dt,dt+30min) for a clock of UTC+tz hours."""
    total=0.
    for j in range(steps):
        u=dt+timedelta(minutes=30*(j+.5)/steps)-timedelta(hours=tz)
        doy=u.timetuple().tm_yday;hu=u.hour+u.minute/60+u.second/3600
        g=2*math.pi/365*(doy-1+(hu-12)/24)
        eot=229.18*(.000075+.001868*math.cos(g)-.032077*math.sin(g)-.014615*math.cos(2*g)-.040849*math.sin(2*g))
        dec=(.006918-.399912*math.cos(g)+.070257*math.sin(g)-.006758*math.cos(2*g)+.000907*math.sin(2*g)
             -.002697*math.cos(3*g)+.00148*math.sin(3*g))
        ha=math.radians((hu*60+eot+4*lon)/4-180);phi=math.radians(lat)
        cz=math.sin(phi)*math.sin(dec)+math.cos(phi)*math.cos(dec)*math.cos(ha)
        total+=1361*(1+.033*math.cos(2*math.pi*doy/365))*max(cz,0.)
    return total/steps

def bif_metadata(raw,pkg):
    """Exact unit/definition/QC text for the seven variables plus BIF location and UTC offset."""
    out={'variables':{},'qc_definitions':{},'bif':{}}
    with zipfile.ZipFile(io.BytesIO(raw)) as nested:
        names={PurePosixPath(i.filename).name:i for i in nested.infolist() if not i.is_dir()}
        info=[n for n in names if '_BIFVARINFO_HH_' in n];bif=[n for n in names if '_FLUXNET_BIF_' in n]
        if len(info)!=1 or len(bif)!=1 or 'README.txt' not in names:raise ValueError('BIF/BIFVARINFO/README scope')
        readme=nested.read(names['README.txt'])
        out['README_sha256']=hashlib.sha256(readme).hexdigest()
        out['README_time_sentence']=[ln.strip() for ln in readme.decode('utf-8','replace').splitlines() if 'time is expressed' in ln]
        groups=defaultdict(dict)
        for r in csv.DictReader(io.TextIOWrapper(nested.open(names[info[0]]),encoding='utf-8-sig',newline='')):
            groups[r['GROUP_ID']][r['VARIABLE']]=r['DATAVALUE']
        for g in groups.values():
            v=g.get('VAR_INFO_VARNAME','')
            if v in VARS:
                out['variables'].setdefault(v,[]).append({k:g.get(k,'') for k in ('VAR_INFO_UNIT','VAR_INFO_DATE','VAR_INFO_HEIGHT','VAR_INFO_MODEL','VAR_INFO_DEFINITION')})
            elif v in tuple(x+'_QC' for x in VARS):
                out['qc_definitions'][v]=g.get('VAR_INFO_DEFINITION','')
        for v in out['variables']:out['variables'][v].sort(key=lambda b:(b['VAR_INFO_DATE'],b['VAR_INFO_HEIGHT'],b['VAR_INFO_MODEL']))
        for r in csv.DictReader(io.TextIOWrapper(nested.open(names[bif[0]]),encoding='utf-8-sig',newline='')):
            if r['VARIABLE'] in ('UTC_OFFSET','LOCATION_LAT','LOCATION_LONG','LOCATION_ELEV','PRODUCT_ONEFLUX_VERSION','PRODUCT_PROCESSING_DATE'):
                out['bif'].setdefault(r['VARIABLE'],set()).add(r['DATAVALUE'].strip())
    out['bif']={k:sorted(v) for k,v in sorted(out['bif'].items())}
    for k in ('UTC_OFFSET','LOCATION_LAT','LOCATION_LONG','LOCATION_ELEV'):
        if len(out['bif'].get(k,[]))!=1:raise ValueError('BIF must give exactly one '+k)
    units={v:sorted({b['VAR_INFO_UNIT'] for b in blocks}) for v,blocks in out['variables'].items()}
    out['unit_check']={v:('MATCH' if units.get(v)==[u] else 'MISMATCH:'+repr(units.get(v))) for v,u in EXPECTED_UNITS.items()}
    return out

def load(raw,pkg,n_expected):
    with zipfile.ZipFile(io.BytesIO(raw)) as nested:
        members=[i for i in nested.infolist() if not i.is_dir() and '_FLUXMET_HH_' in PurePosixPath(i.filename).name and i.filename.lower().endswith('.csv')]
        if len(members)!=1:raise ValueError('FLUXMET_HH member scope')
        with nested.open(members[0]) as b,io.TextIOWrapper(b,encoding='utf-8-sig',newline='') as text:
            reader=csv.reader(text);header=next(reader)
            if len(header)!=len(set(header)) or not set(REQUIRED).issubset(header):raise ValueError('missing/duplicate required FLUXMET columns')
            cols=[c for c in REQUIRED[2:]+OPTIONAL if c in header];idx={c:header.index(c) for c in cols}
            data={c:(array('b') if c.endswith('_QC') else array('d')) for c in cols}
            i0=header.index('TIMESTAMP_START');i1=header.index('TIMESTAMP_END');first=None;prev=None;n=0
            for row in reader:
                if len(row)!=len(header):raise ValueError('row width mismatch')
                s=stamp(row[i0]);e=stamp(row[i1])
                if e-s!=timedelta(minutes=30) or (prev is not None and s!=prev):raise ValueError('timestamp continuity at '+row[i0])
                if first is None:first=s
                prev=e;n+=1
                for c in cols:data[c].append(qc(row[idx[c]]) if c.endswith('_QC') else num(row[idx[c]]))
    if n!=n_expected:raise ValueError('row count %d != %d'%(n,n_expected))
    if first.hour or first.minute:raise ValueError('series must start at 00:00')
    return members[0].filename,first,n,data

def finite(x):return not math.isnan(x)

def analyse(site,raw,pkg,n_expected):
    meta=bif_metadata(raw,pkg)
    lat=float(meta['bif']['LOCATION_LAT'][0]);lon=float(meta['bif']['LOCATION_LONG'][0]);elev=float(meta['bif']['LOCATION_ELEV'][0])
    tz=float(meta['bif']['UTC_OFFSET'][0])
    member,first,n,d=load(raw,pkg,n_expected)
    times=[first+timedelta(minutes=30*i) for i in range(n)]
    years=[t.year for t in times]
    toa=array('d',(toa_mean(t,lat,lon,tz) for t in times))
    res={'site':site,'member':member,'rows':n,'first_start':times[0].strftime('%Y%m%d%H%M'),'last_start':times[-1].strftime('%Y%m%d%H%M'),
         'leap_day_rows':sum(1 for t in times if t.month==2 and t.day==29),'metadata':meta,'optional_columns_present':[c for c in OPTIONAL if c in d]}
    # QC composition by year
    comp={}
    for v in VARS:
        c=defaultdict(Counter)
        for i in range(n):c[years[i]][str(d[v+'_QC'][i]) if finite(d[v][i]) else 'value_missing']+=1
        comp[v]={str(y):dict(sorted(c[y].items())) for y in sorted(c)}
    res['qc_composition_by_year']=comp
    # physical limits and cross-variable checks
    flags=Counter();examples=defaultdict(list);ranges={}
    def flag(key,i,val):
        flags[key+':QC'+str(d[key.split(':')[0]+'_QC'][i])]+=1
        if len(examples[key])<5:examples[key].append([times[i].strftime('%Y%m%d%H%M'),r6(val),int(d[key.split(':')[0]+'_QC'][i])])
    p0=p_standard(elev)
    for v in VARS:
        lo=hi=None
        for i in range(n):
            x=d[v][i]
            if finite(x):
                if lo is None or x<lo[0]:lo=(x,i)
                if hi is None or x>hi[0]:hi=(x,i)
        ranges[v]={'min':r6(lo[0]) if lo else None,'min_start':times[lo[1]].strftime('%Y%m%d%H%M') if lo else None,
                   'max':r6(hi[0]) if hi else None,'max_start':times[hi[1]].strftime('%Y%m%d%H%M') if hi else None}
    for i in range(n):
        ta,pa,vpd,sw,lw,ws,p=(d[v][i] for v in VARS)
        if finite(ta) and not -45<=ta<=45:flag('TA_F:outside_-45_45C',i,ta)
        if finite(pa) and abs(pa-p0)>5:flag('PA_F:more_than_5kPa_from_standard_atmosphere_at_BIF_elevation',i,pa)
        if finite(vpd):
            if vpd<0:flag('VPD_F:negative',i,vpd)
            if vpd>80:flag('VPD_F:above_80hPa',i,vpd)
            if finite(ta) and -70<ta<60 and vpd>=es(ta):flag('VPD_F:at_or_above_water_es_TA_F',i,vpd)
        if finite(sw):
            if sw<0:flag('SW_IN_F:negative',i,sw)
            if sw>toa[i]+20:flag('SW_IN_F:above_TOA_plus_20',i,sw)
            if toa[i]==0 and sw>5:flag('SW_IN_F:above_5_when_TOA_zero',i,sw)
        if finite(lw):
            if not 100<=lw<=600:flag('LW_IN_F:outside_100_600',i,lw)
            elif finite(ta) and -45<=ta<=45:
                eps=lw/(SIGMA*(ta+273.15)**4)
                if not .5<=eps<=1.2:flag('LW_IN_F:LW_over_sigmaT4_outside_0.5_1.2',i,lw)
        if finite(ws) and not 0<=ws<=35:flag('WS_F:outside_0_35',i,ws)
        if finite(p):
            if p<0:flag('P_F:negative',i,p)
            if p>50:flag('P_F:above_50mm_per_half_hour',i,p)
    res['value_ranges']=ranges;res['physical_flags']=dict(sorted(flags.items()));res['physical_flag_examples']={k:examples[k] for k in sorted(examples)}
    res['clock_tests']=clock_tests(times,d,toa,lat,lon,tz,n)
    res['humidity']=humidity(d,n)
    res['pressure']=pressure(d,years,n,p0,elev)
    res['precipitation']=precipitation(d,years,n)
    res['ppfd_sw_ratio_by_year']=ppfd_ratio(d,years,n)
    res['sw_source_phase']=sw_source_phase(d,years,toa,n)
    res['flatlines']=flatlines(times,d,toa,n)
    res['spikes']=spikes(times,d,n)
    res['era_artifact_windows'],rows=artifacts(site,times,d,n)
    return res,rows

def centroid(vals):
    s=sum(vals)
    return None if s<=0 else sum(v*(30*k+15) for k,v in enumerate(vals))/s
def clock_tests(times,d,toa,lat,lon,tz,n):
    """Clear-day centroid offsets (minutes) relative to UTC+tz solar geometry, and TA-vs-ERA lag."""
    out={'hypothesis_clock_utc_offset_h':tz,'expected_offset_min_if_local_mean_solar_time':r6(4*(lon-15*tz)),
         'method':'per day with all TOA>0 half-hours SW_IN_F_QC=0 and daily SW/TOA>=0.6; centroid=sum(x*mid)/sum(x)'}
    per=defaultdict(list);by_year=defaultdict(list);by_season=defaultdict(list)
    for start in range(0,n-47,48):
        day=range(start,start+48);top=[toa[i] for i in day]
        if sum(top)<=0:continue
        lit=[i for i in day if toa[i]>0]
        if any(d['SW_IN_F_QC'][i]!=0 or not finite(d['SW_IN_F'][i]) for i in lit):continue
        sw=[d['SW_IN_F'][i] if finite(d['SW_IN_F'][i]) else 0. for i in day]
        if sum(sw)/sum(top)<.6:continue
        c0=centroid(top)
        for key,col in (('SW_IN_F','SW_IN_F'),('SW_IN_POT','SW_IN_POT'),('SW_IN_ERA','SW_IN_ERA'),('PPFD_IN','PPFD_IN')):
            if col not in d:continue
            vals=[d[col][i] for i in day]
            if col=='PPFD_IN' and any(not finite(d[col][i]) for i in lit):continue
            c=centroid([max(v,0.) if finite(v) else 0. for v in vals])
            if c is not None:per[key].append(c-c0)
        off=per['SW_IN_F'][-1];t=times[start];by_year[t.year].append(off)
        by_season[{12:'DJF',1:'DJF',2:'DJF',3:'MAM',4:'MAM',5:'MAM',6:'JJA',7:'JJA',8:'JJA'}.get(t.month,'SON')].append(off)
    out['centroid_offset_min_vs_UTCplus_tz_TOA']={k:summary(v) for k,v in sorted(per.items())}
    out['SW_IN_F_offset_by_year']={str(y):summary(v) for y,v in sorted(by_year.items())}
    out['SW_IN_F_offset_by_season']={k:summary(by_season[k]) for k in ('DJF','MAM','JJA','SON') if by_season[k]}
    # TA first-difference correlation with same-file TA_ERA shifted by k half-hours
    corr={}
    for k in range(-4,5):
        sx=sy=sxx=syy=sxy=0.;m=0
        for i in range(max(0,-k),min(n-1,n-1-k)):
            if d['TA_F_QC'][i]!=0 or d['TA_F_QC'][i+1]!=0:continue
            a=d['TA_F'][i+1]-d['TA_F'][i];b=d['TA_ERA'][i+k+1]-d['TA_ERA'][i+k]
            if not (finite(a) and finite(b)):continue
            sx+=a;sy+=b;sxx+=a*a;syy+=b*b;sxy+=a*b;m+=1
        den=math.sqrt(max(sxx-sx*sx/m,0)*max(syy-sy*sy/m,0)) if m else 0
        corr[k]=(sxy-sx*sy/m)/den if den else None
    out['TA_diff_corr_by_lag_halfhours']={str(k):r6(v) for k,v in corr.items()}
    good={k:v for k,v in corr.items() if v is not None}
    if good:
        k=max(good,key=good.get);frac=0.
        if -4<k<4 and corr[k-1] is not None and corr[k+1] is not None:
            den=corr[k-1]-2*corr[k]+corr[k+1]
            frac=.5*(corr[k-1]-corr[k+1])/den if den else 0.
        out['TA_peak_lag_min_tower_vs_ERA']=r6(30*(k+frac))
    out['interpretation_rule']='offset ~0 supports UTC+tz labels; offset ~expected_offset_min_if_local_mean_solar_time supports LMST; pyranometer tilt, shading and diurnal cloud asymmetry can bias SW; ERA time support adds up to +-15 min to the TA lag'
    return out

def humidity(d,n):
    """Implied es from raw RH and VPD_F at TA_F (both QC0), q feasibility and formula sensitivity."""
    bins=((-60,-10),(-10,0),(0,10),(10,20),(20,45))
    ratios={f:defaultdict(list) for f in ES_FORMULAS};used=0
    if 'RH' in d:
        for i in range(n):
            rh=d['RH'][i];v=d['VPD_F'][i];t=d['TA_F'][i]
            if d['VPD_F_QC'][i]!=0 or d['TA_F_QC'][i]!=0 or not (finite(rh) and finite(v) and finite(t)) or not 10<rh<90 or v<1:continue
            impl=v/(1-rh/100);used+=1
            for lo,hi in bins:
                if lo<=t<hi:
                    for f in ES_FORMULAS:ratios[f]['%g_%g'%(lo,hi)].append(impl/es(t,f))
    formula_fit={f:{b:summary(v) for b,v in sorted(ratios[f].items())} for f in ES_FORMULAS}
    score={f:quant([abs(math.log(x)) for b in ratios[f].values() for x in b],.5) for f in ES_FORMULAS} if used else {}
    cats=Counter();qmin=qmax=None;dq_abs=0.;dq_rel=0.;infeasible=Counter();cap=Counter();cap_rel=0.
    for i in range(n):
        t=d['TA_F'][i];p=d['PA_F'][i];v=d['VPD_F'][i]
        if not (finite(t) and finite(p) and finite(v)):cats['MISSING_INPUT']+=1;continue
        e=es(t,'oneflux_qc_auto')-v
        if v<0:cats['NEGATIVE_VPD']+=1;continue
        if e<=0:cats['NONPOSITIVE_VAPOUR']+=1;continue
        q=.622*e/(p*10-.378*e)
        if not 0<q<.04:cats['Q_OUTSIDE_0_0.04']+=1;continue
        cats['FEASIBLE']+=1;qmin=q if qmin is None else min(qmin,q);qmax=q if qmax is None else max(qmax,q)
        ed=datm_esat_hpa(t);qs=.622*ed/(p*10-.378*ed)
        if q>qs:
            cap['TA_below_0C' if t<0 else 'TA_0C_or_above']+=1;cap_rel=max(cap_rel,(q-qs)/q)
        for f in ES_FORMULAS:
            e2=es(t,f)-v
            if f=='oneflux_qc_auto':continue
            if e2<=0:infeasible[f]+=1
            else:
                q2=.622*e2/(p*10-.378*e2);dq_abs=max(dq_abs,abs(q2-q));dq_rel=max(dq_rel,abs(q2-q)/q)
    return {'raw_RH_rows_used_for_formula_test':used,'implied_es_over_formula_ratio_by_TA_bin':formula_fit,
            'median_abs_log_ratio_by_formula':{f:r6(s) for f,s in sorted(score.items())},
            'best_formula_by_median_abs_log_ratio':min(score,key=score.get) if score else None,
            'q_formula':'oneflux_qc_auto water es, e=es-VPD, q=0.622e/(p-0.378e)','q_categories':dict(sorted(cats.items())),
            'rows_DATM_would_cap_to_qsat_by_TA_class':dict(sorted(cap.items())),'max_relative_q_reduction_by_DATM_cap':r6(cap_rel),'q_min_kgkg':r6(qmin),'q_max_kgkg':r6(qmax),
            'nonpositive_vapour_rows_by_formula_among_oneflux_feasible':{f:infeasible[f] for f in ES_FORMULAS},
            'max_abs_q_change_between_candidate_water_formulas_kgkg':r6(dq_abs),'max_rel_q_change_between_candidate_water_formulas':r6(dq_rel)}

def pressure(d,years,n,p0,elev):
    by=defaultdict(lambda:defaultdict(list));diff=defaultdict(list)
    for i in range(n):
        x=d['PA_F'][i]
        if finite(x):by[years[i]][str(d['PA_F_QC'][i])].append(x)
        if d['PA_F_QC'][i]==0 and finite(x) and finite(d['PA_ERA'][i]):diff[years[i]].append(x-d['PA_ERA'][i])
    return {'BIF_elevation_m':elev,'standard_atmosphere_kPa_at_BIF_elevation':r6(p0),
            'annual_median_PA_F_by_QC':{str(y):{q:r6(quant(v,.5)) for q,v in sorted(c.items())} for y,c in sorted(by.items())},
            'annual_PA_F_QC0_minus_PA_ERA':{str(y):summary(v) for y,v in sorted(diff.items())}}

def precipitation(d,years,n):
    tot=defaultdict(Counter);wet=defaultdict(Counter);era=Counter();mx=None
    for i in range(n):
        p=d['P_F'][i];q=str(d['P_F_QC'][i])
        if finite(p):
            tot[years[i]][q]+=p
            if p>0:wet[years[i]][q]+=1
            if mx is None or p>mx[0]:mx=(p,i,q)
        if finite(d['P_ERA'][i]):era[years[i]]+=d['P_ERA'][i]
    return {'annual_P_F_mm_by_QC':{str(y):{q:r6(v) for q,v in sorted(c.items())} for y,c in sorted(tot.items())},
            'annual_wet_halfhours_by_QC':{str(y):dict(sorted(c.items())) for y,c in sorted(wet.items())},
            'annual_P_ERA_mm':{str(y):r6(v) for y,v in sorted(era.items())},
            'max_halfhour_P_F_mm':r6(mx[0]) if mx else None,'max_halfhour_P_F_QC':mx[2] if mx else None,'max_row_index':mx[1] if mx else None}

def ppfd_ratio(d,years,n):
    if 'PPFD_IN' not in d:return {}
    by=defaultdict(list)
    for i in range(n):
        sw=d['SW_IN_F'][i];pp=d['PPFD_IN'][i]
        if d['SW_IN_F_QC'][i]==0 and finite(sw) and finite(pp) and sw>200 and pp>0:by[years[i]].append(pp/sw)
    return {str(y):summary(v) for y,v in sorted(by.items())}

def sw_source_phase(d,years,toa,n):
    """Share of SW_IN_F energy by QC class falling in half-hours whose UTC+tz TOA is zero (after sunset/before sunrise)."""
    tot=Counter();dark=Counter();rows=defaultdict(Counter)
    for i in range(n):
        x=d['SW_IN_F'][i];q=str(d['SW_IN_F_QC'][i])
        if not finite(x):continue
        rows[years[i]][q]+=1;tot[q]+=x
        if toa[i]==0:dark[q]+=x
    night=defaultdict(list)
    for i in range(n):
        if toa[i]==0 and d['SW_IN_F_QC'][i]==0 and finite(d['SW_IN_F'][i]):night[years[i]].append(d['SW_IN_F'][i])
    return {'night_SW_IN_F_QC0_when_TOA_zero_by_year':{str(y):summary(v) for y,v in sorted(night.items())},
            'SW_IN_F_sum_Wm2_halfhours_by_QC':{q:r6(v) for q,v in sorted(tot.items())},
            'fraction_of_SW_IN_F_sum_when_TOA_zero_by_QC':{q:r6(dark[q]/tot[q]) if tot[q] else None for q in sorted(tot)},
            'SW_IN_F_rows_by_year_QC':{str(y):dict(sorted(c.items())) for y,c in sorted(rows.items())}}

def flatlines(times,d,toa,n,minimum=12):
    """Runs of identical consecutive QC0 values (>=6 h); zero runs excluded for SW/WS/P/VPD."""
    out={}
    for v in ('TA_F','PA_F','VPD_F','SW_IN_F','LW_IN_F','WS_F'):
        runs=[];i=0
        while i<n:
            x=d[v][i]
            if d[v+'_QC'][i]!=0 or not finite(x) or (v in ('SW_IN_F','WS_F','VPD_F') and x==0) or (v=='SW_IN_F' and toa[i]==0):i+=1;continue
            j=i
            while j+1<n and d[v+'_QC'][j+1]==0 and d[v][j+1]==x and not (v=='SW_IN_F' and toa[j+1]==0):j+=1
            if j-i+1>=minimum:runs.append((j-i+1,times[i].strftime('%Y%m%d%H%M'),r6(x)))
            i=j+1
        runs.sort(key=lambda r:(-r[0],r[1]))
        out[v]={'runs_ge_6h':len(runs),'longest_10':[list(r) for r in runs[:10]]}
    return out

def spikes(times,d,n):
    lim={'TA_F':4.,'PA_F':.3,'LW_IN_F':60.}
    out={}
    for v,L in lim.items():
        hits=[]
        for i in range(1,n-1):
            if d[v+'_QC'][i-1]!=0 or d[v+'_QC'][i]!=0 or d[v+'_QC'][i+1]!=0:continue
            a,x,b=d[v][i-1],d[v][i],d[v][i+1]
            if finite(a) and finite(x) and finite(b) and abs(x-a)>L and abs(x-b)>L and (x-a)*(x-b)>0:hits.append([times[i].strftime('%Y%m%d%H%M'),r6(x)])
        out[v]={'threshold':L,'count':len(hits),'first_10':hits[:10]}
    return out

def artifacts(site,times,d,n):
    """Gross same-release ERA rows (TA_ERA<-60, PA_ERA<50, LW_IN_ERA<60) with +-3 rows and every F/QC/ERA field."""
    core=[i for i in range(n) if (finite(d['TA_ERA'][i]) and d['TA_ERA'][i]<-60) or (finite(d['PA_ERA'][i]) and d['PA_ERA'][i]<50)
          or (finite(d['LW_IN_ERA'][i]) and d['LW_IN_ERA'][i]<60)]
    groups=[]
    for i in core:
        if groups and i-groups[-1][-1]<=4:groups[-1].append(i)
        else:groups.append([i])
    era={'TA_F':'TA_ERA','PA_F':'PA_ERA','VPD_F':'VPD_ERA','SW_IN_F':'SW_IN_ERA','LW_IN_F':'LW_IN_ERA','WS_F':'WS_ERA','P_F':'P_ERA'}
    rows=[];summaries=[]
    for g in groups:
        lo=max(0,g[0]-3);hi=min(n-1,g[-1]+3);uses=Counter()
        for i in range(lo,hi+1):
            row={'site':site,'native_start':times[i].strftime('%Y%m%d%H%M'),'core_era_artifact_row':int(i in g)}
            for v in VARS:
                row[v]=r6(d[v][i]);row[v+'_QC']=int(d[v+'_QC'][i]);row[era[v]]=r6(d[era[v]][i])
                if i in g and row[v+'_QC']==2:uses[v]+=1
            rows.append(row)
        summaries.append({'first_core_start':times[g[0]].strftime('%Y%m%d%H%M'),'last_core_start':times[g[-1]].strftime('%Y%m%d%H%M'),
                          'core_rows':len(g),'core_rows_where_F_is_QC2_by_variable':dict(sorted(uses.items()))})
    return summaries,rows

def fingerprint(obj):
    """Hash of integers and strings only, robust to last-digit libm differences between machines."""
    def walk(x):
        if isinstance(x,dict):return {k:walk(v) for k,v in sorted(x.items())}
        if isinstance(x,list):return [walk(v) for v in x]
        if isinstance(x,float):return None
        return x
    return hashlib.sha256(json.dumps(walk(obj),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def source(root,layout,site):
    pkg=SITES[site][0]
    return root/site/'forcing'/'packages'/(pkg+'.zip') if layout=='iridis' else root/site/(pkg+'.zip')

def run_site(root,layout,site):
    pkg,expected,rows=SITES[site];path=source(root,layout,site);check(path,expected)
    with zipfile.ZipFile(path) as outer:
        inner=[x for x in outer.infolist() if not x.is_dir() and x.filename==pkg+'.zip']
        if len(inner)!=1 or inner[0].file_size>CAP:raise ValueError('nested ZIP scope/cap')
        raw=outer.read(inner[0])
    result,windows=analyse(site,raw,pkg,rows)
    check(path,expected)
    result['source_zip_sha256_pre_post']=expected
    return result,windows

def selftest():
    assert abs(datm_esat_hpa(0.)-6.107799961)<1e-12 and abs(datm_esat_hpa(-1e-9)-6.109177956)<1e-6 and datm_esat_hpa(-10.)<es(-10.)
    assert abs(es(20.,'oneflux_qc_auto')-6.11*math.exp(17.26938818*20/257.3))<1e-12
    assert abs(es(0.)-6.112)<1e-12 and abs(es(20.,'tetens_fao56')-23.383)<.002
    assert abs(p_standard(0)-101.325)<1e-9 and 89<p_standard(1043)<90
    noon=[toa_mean(datetime(2011,6,21,0,0)+timedelta(minutes=30*k),36.,135.,9.) for k in range(48)]
    c=centroid(noon);assert abs(c-(720-(-1.7)))<3,c   # 135E on UTC+9: solar noon ~12:02 JST near the June solstice
    assert num('-9999')!=num('-9999') and qc('') == -1 and qc('2')==2
    assert summary([1.,2.,3.])['median']==2.
    print('STAGE05BR SELF-TEST PASS; READ-ONLY JPF FORCING-VARIABLE EVIDENCE; ZERO APPROVALS')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--root',type=Path,default=IRIDIS_ROOT);p.add_argument('--layout',choices=('iridis','local'),default='iridis')
    p.add_argument('--sites',default=','.join(SITES));p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if a.out is None:p.error('--out required')
    sites=[s for s in a.sites.split(',') if s]
    if not sites or any(s not in SITES for s in sites) or len(set(sites))!=len(sites):p.error('unknown/duplicate site')
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out under an existing real directory required')
    results=[];windows=[]
    for s in sites:
        print('STAGE05BR SCAN',s,flush=True)
        r,w=run_site(a.root,a.layout,s);results.append(r);windows.extend(w)
    a.out.mkdir()
    tsv=a.out/'era_artifact_windows_all_F_fields_HOLD.tsv'
    with tsv.open('x',encoding='utf-8',newline='') as f:
        if windows:
            w=csv.DictWriter(f,list(windows[0].keys()),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(windows)
    report={'stage':'05BR','status':'READ_ONLY_EVIDENCE_NO_SITE_CLEARED_BY_SCRIPT','approved_replacements':0,'sites':results,
            'artifact_window_rows':len(windows),'artifact_window_tsv_sha256':sha(tsv),
            'original_zip_forcing_pft_soil_model_slurm_modified':False}
    report['integer_string_fingerprint']=fingerprint(report)
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE05BR COMPLETE; EVIDENCE ONLY; ZERO APPROVED; ALL REPAIRS HOLD')
    print('OUTPUT',a.out)
    print(json.dumps({'integer_string_fingerprint':report['integer_string_fingerprint'],'summary_sha256':sha(a.out/'summary_HOLD.json'),
                      'artifact_window_tsv_sha256':report['artifact_window_tsv_sha256'],'artifact_window_rows':len(windows)},indent=1))
if __name__=='__main__':main()

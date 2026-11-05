#!/usr/bin/env python3
"""Stage06A: UTC-aligned NOLEAP CDEPS/DATM forcing CANDIDATES for the 11 JapanFlux sites. Guarded writer.

Input: the twelve Stage05CB final pre-forcing tables (user-approved 2026-11-05; gzip SHA-256 pinned below).
Convention (Non-Competition AmeriFlux_Batch01_10 stage11; OzFlux_MultiSite_09 stage12): one file per year with a
UTC interval-centre time axis, (k+0.5)/48 days since <year>-01-01 00:00 on the noleap calendar, and every
meteorological field moved by the whole number of slots that separates UTC from the source clock. CTSM computes the
solar hour angle from model (UTC) time and longitude, so local-time data would put the sun 9 h out of phase.

The tables carry TIMESTAMP_START labels on UTC+9 (Tef/Tmd: working assumption, decision C1). After dropping local
Feb 29 rows, UTC slot i of year y takes local slot i+18 (half-hourly) or i+9 (JP-Tom hourly 1999-2002). The last
9 h of each UTC year come from the first 9 h of the next local year; for the final year they come from the first
year, because the forcing cycle wraps (TECHNICAL CYCLE BOUNDARY, not an observation). Where the next year has a
different cadence (JP-Tom 2002->2003 and the 2010->1999 wrap), the 9 h are converted: half-hour pairs are averaged,
hourly values are repeated.

Fields: TBOT=TA+273.15 K; PSRF=PA*1000 Pa; QBOT=0.622e/(p-0.378e) with e=es(TA)-VPD and the producer's es formula
(Stage05BR C5); FSDS=max(SW_IN,0); FLDS=LW_IN; WIND=WS; PRECTmms=P/dt; ZBOT=TA sensor height (BIF/BADM).
Checks: approved tags only, continuous full years, no missing values, e>0, physical ranges, exact UTC permutation,
and an independent FSDS solar-centroid test on the UTC axis (|median| <= 20 min).

--self-test               synthetic checks, no files
--cb-dir D                check only: reads, converts and tests all sites, writes nothing
--cb-dir D --out NEW --write --ack-utc-plus9-cyclic-shift
                          also writes NetCDF candidates, stream plans and summaries to a brand-new directory
No case, stream activation, Slurm or model run. The candidates are not production forcing until separately accepted.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import warnings
from datetime import timedelta
from pathlib import Path

import netCDF4
import numpy as np

# netCDF4 1.7 reshapes arrays internally on write (NumPy 2.5 deprecation); every write is checked by read-back.
warnings.filterwarnings('ignore',message='Setting the shape on a NumPy array',category=DeprecationWarning)

CB_PIN=('05cb_finalize_approved_preforcing_tables_READONLY.py','47ffb987fbe2bdce16539996eca16929ae5d9d43ba9aabeb5ab6bccaa2edfd81')
TABLES={'JP-Api':'f97ad3ff74dd803c7ac491f171653007fa9c120d7e021ea5902f330c9849104f','JP-Fhk':'b1a7a0b870140016721c0a1f3cc8b87575ddf1903e159bc6495e2a5bc4ce8bcb',
 'JP-Fjy':'86e45a31e0f7f1a86a5467c7deaf7eeba56fdcaac9b176745b370fed96a4557d','JP-Khw':'8be7fcdb886bd443c028cffecb658bdd65c82bfa91de4106968bce93b67f6ce7',
 'JP-Spp':'adfa7311ac09201fe073469c4d76a0318930ac66a26578b4b46f0654ca200c72','JP-Tak':'4535ead71238ea698cb4c8e9e1c724a4450d8563706900511156b1a6d004143c',
 'JP-Tef':'a745ea2f704d5ee63ee018b38fb0c19fb1b084c590dfa319a000bc8335a61cb8','JP-Tmd':'12981895f344318fb511e05e10911f9d5c11d918497566603e8724d040414651',
 'JP-Yms':'428d9cf32d65efea4057c1ee510e1732617787fe47906149ca3a8f747bd97c2d','JP-Tgf_HH':'7fd04cb06f85dcad98e6489f7e73aed2222e6e9f482c7897d4abd3b40dea81b0',
 'JP-Tom_HH':'03ce4521d0bb5c2e5031bf418acc1535e632d801b66e6f4bdfdc296126e54b95','JP-Tom_HR':'59fba16a38dad2afd3da28bb782335873ff0b235610e71026299ee35de75dc29'}
TABLE_NAME='{}_final_preforcing_APPROVED_20261105.tsv.gz'
# site: (tables, first year, last year, lat, lon, ZBOT m, es formula)
# lat/lon: BIF LOCATION_LAT/LONG (Stage05BR, JPF) or JapanFlux2024 BADM (Stage05BS, Tom/Tgf).
# ZBOT: TA_F sensor height, BIF VAR_INFO_HEIGHT (JPF); Tgf BADM INSTOM_HEIGHT TA_1_1_1 29.5 m; Tom BADM JPTOM-TE01 19 m.
# es: producer VPD formula (Stage05BR C5): ONEFlux qc_auto for JPF; Bolton for Tmd and JapanFlux2024 (Fhk unverifiable,
#     JPF default). Years: full approved table range; JP-Tom 1999-2010 (D3b).
SITES={'JP-Api':(('JP-Api',),2000,2022,40.00135858,140.9365859,31.0,'oneflux_qc_auto'),
       'JP-Fhk':(('JP-Fhk',),2006,2023,35.4435557694444,138.764693061111,32.0,'oneflux_qc_auto'),
       'JP-Fjy':(('JP-Fjy',),2001,2021,35.45454,138.76225,32.0,'oneflux_qc_auto'),
       'JP-Khw':(('JP-Khw',),2000,2021,33.13658,130.70834,51.0,'oneflux_qc_auto'),
       'JP-Spp':(('JP-Spp',),2000,2018,42.986843,141.385331,33.5,'oneflux_qc_auto'),
       'JP-Tak':(('JP-Tak',),1998,2021,36.14616667,137.4231111,25.0,'oneflux_qc_auto'),
       'JP-Tef':(('JP-Tef',),2001,2023,45.055808,142.107122,32.0,'oneflux_qc_auto'),
       'JP-Tmd':(('JP-Tmd',),2005,2023,42.735911,141.523147,2.6,'bolton1980'),
       'JP-Yms':(('JP-Yms',),2000,2023,34.790278,135.840939,25.7,'oneflux_qc_auto'),
       'JP-Tgf':(('JP-Tgf_HH',),2002,2022,36.11353,140.09488,29.5,'bolton1980'),
       'JP-Tom':(('JP-Tom_HR','JP-Tom_HH'),1999,2010,42.698906,141.571488,19.0,'bolton1980')}
CLOCK={'JP-Tef':'UTC+9 is a diagnostic working assumption (README local solar time conflicts with BIF UTC_OFFSET 9; decision C1)',
       'JP-Tmd':'UTC+9 is a diagnostic working assumption (README local solar time conflicts with BIF UTC_OFFSET 9; decision C1)',
       'JP-Tom':'BADM UTC_OFFSET 9; tower TA/RH/VPD/SW moved -1 h in Stage05BW (decision C2)'}
TZ_HOURS=9
FIELDS=(('TBOT','K','temperature at the lowest atmospheric level'),('QBOT','kg/kg','specific humidity at the lowest atmospheric level'),
        ('PSRF','Pa','surface pressure'),('FSDS','W/m**2','incident shortwave radiation'),('FLDS','W/m**2','incident longwave radiation'),
        ('WIND','m/s','wind speed at the lowest atmospheric level'),('PRECTmms','mm/s','precipitation rate'))
RANGES={'TBOT':(200.,330.),'QBOT':(0.,0.05),'PSRF':(6e4,1.1e5),'FSDS':(0.,1500.),'FLDS':(50.,650.),'WIND':(0.,75.),'PRECTmms':(0.,0.2)}
COVERAGE_VARS=('TA_F','VPD_F','SW_IN_F')
FILE='{}_JP11_UTC_NOLEAP_DATM_CANDIDATE_{}.nc'

def load_cb():
    name,expected=CB_PIN;here=Path(__file__).parent
    for path in (here/name,here.parent/'stage05'/name):
        if path.is_file() and not path.is_symlink():break
    else:raise ValueError('pinned 05CB script not found')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 05CB hash mismatch')
    spec=importlib.util.spec_from_file_location('stage05cb',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
cb=load_cb();br=cb.br

def read_local(path,expected):
    """Approved table -> per local year {spd, values{var: f8 array}, qc0_pct{var}} with local Feb 29 removed."""
    header,variables,rows=cb.bz.read_table(path,expected)
    for r in rows:
        for c in range(3,len(r),3):
            if 'NOT_APPROVED' in r[c] or r[c].split('|')[0].startswith(('HOLD','PROPOSED')):raise ValueError('unapproved tag %s %s'%(r[0],r[c]))
    ts=[r[0] for r in rows];t0=br.stamp(ts[0]);step=br.stamp(ts[1])-t0
    if step not in (timedelta(minutes=30),timedelta(minutes=60)) or ts[0][4:]!='01010000':raise ValueError('table must start on Jan 1 00:00 with a 30/60 min step')
    if any(ts[i]!=(t0+i*step).strftime('%Y%m%d%H%M') for i in range(len(ts))):raise ValueError('time axis not continuous')
    spd=int(timedelta(days=1)/step);years={}
    for i,t in enumerate(ts):
        if t[4:8]!='0229':years.setdefault(int(t[:4]),[]).append(i)
    out={}
    for y,ix in years.items():
        if len(ix)!=365*spd:raise ValueError('incomplete year %d'%y)
        vals={v:np.array([br.num(rows[i][1+3*j]) for i in ix]) for j,v in enumerate(variables)}
        if not all(np.isfinite(x).all() for x in vals.values()):raise ValueError('missing value in %d'%y)
        out[y]={'spd':spd,'values':vals,'qc0_pct':{v:round(100.*sum(rows[i][2+3*j]=='0' for i in ix)/len(ix),1) for j,v in enumerate(variables)}}
    return out

def derive(vals,formula,dt):
    """Approved table variables -> DATM fields (float64)."""
    ta,pa=vals['TA_F'],vals['PA_F'];a,b,c=br.ES_FORMULAS[formula]
    if vals['VPD_F'].min()<0:raise ValueError('negative VPD')
    e=a*np.exp(b*ta/(ta+c))-vals['VPD_F']
    if not (e>0).all():raise ValueError('non-positive vapour pressure at %d cells'%int((~(e>0)).sum()))
    sw=vals['SW_IN_F']
    return {'TBOT':ta+273.15,'QBOT':0.622*e/(pa*10.-0.378*e),'PSRF':pa*1000.,'FSDS':np.where(sw>0,sw,0.),
            'FLDS':vals['LW_IN_F'],'WIND':vals['WS_F'],'PRECTmms':vals['P_F']/dt}

def q_from_rh(vals,formula):
    a,b,c=br.ES_FORMULAS[formula];e=vals['RH_F']/100.*a*np.exp(b*vals['TA_F']/(vals['TA_F']+c))
    return 0.622*e/(vals['PA_F']*10.-0.378*e)

def humidity_screen(f,formula):
    """Counts of meteorologically implausible humidity (decision E1 is open; values are not changed here)."""
    t=f['TBOT']-273.15;q=f['QBOT'];e=q*(f['PSRF']/100.)/(0.622+0.378*q);a,b,c=br.ES_FORMULAS[formula]
    rh=e/(a*np.exp(b*t/(t+c)));l=np.log(e/6.112);td=243.5*l/(17.67-l)
    return {'Td_ge_28C':int((td>=28).sum()),'saturated_TA_ge_28C':int(((rh>=.995)&(t>=28)).sum()),'RH_lt_5pct':int((rh<.05).sum())}

def first_hours(x,spd_from,spd_to,hours=TZ_HOURS):
    """First `hours` of a local year at cadence spd_to (pair means for 48->24, repeats for 24->48)."""
    first=x[:hours*spd_from//24]
    if spd_from==spd_to:return first,''
    if spd_from==2*spd_to:return first.reshape(-1,2).mean(axis=1),'_HALFHOUR_PAIR_MEAN'
    if 2*spd_from==spd_to:return np.repeat(first,2),'_HOURLY_REPEATED'
    raise ValueError('unsupported cadence change')

def utc_years(local):
    """[(year, spd, fields)] in calendar order (local clock) -> [(year, spd, fields, tail)] on UTC, cycle-wrapped."""
    out=[]
    for k,(y,spd,f) in enumerate(local):
        ny,nspd,nf=local[(k+1)%len(local)];s=TZ_HOURS*spd//24;g={};note=''
        for v,x in f.items():
            tail,note=first_hours(nf[v],nspd,spd);g[v]=np.concatenate([x[s:],tail])
        source=('CYCLE_WRAP_FROM_FIRST_YEAR_%d'%ny if k==len(local)-1 else 'NEXT_LOCAL_YEAR_%d'%ny)+note
        out.append((y,spd,g,{'tail_slots':s,'tail_source':source}))
    return out

def toa_utc(spd,lat,lon):
    """Top-of-atmosphere irradiance at UTC slot centres of a 365-day year (same formulas as Stage05BR toa_mean)."""
    k=np.arange(365*spd);doy=k//spd+1;hu=(k%spd+.5)*24./spd
    g=2*np.pi/365*(doy-1+(hu-12)/24)
    eot=229.18*(.000075+.001868*np.cos(g)-.032077*np.sin(g)-.014615*np.cos(2*g)-.040849*np.sin(2*g))
    dec=(.006918-.399912*np.cos(g)+.070257*np.sin(g)-.006758*np.cos(2*g)+.000907*np.sin(2*g)-.002697*np.cos(3*g)+.00148*np.sin(3*g))
    ha=np.radians((hu*60+eot+4*lon)/4-180);phi=np.radians(lat)
    cz=np.sin(phi)*np.sin(dec)+np.cos(phi)*np.cos(dec)*np.cos(ha)
    return 1361*(1+.033*np.cos(2*np.pi*doy/365))*np.maximum(cz,0.)

def centroid_offsets(fsds,toa,spd,lon):
    """Daily FSDS minus TOA centroid (minutes) in windows starting at local solar midnight; days with FSDS>20% TOA."""
    start=int(round(((24-lon/15.)%24)*spd/24))%spd
    f=fsds[start:start+364*spd].reshape(364,spd);t=toa[start:start+364*spd].reshape(364,spd);m=(np.arange(spd)+.5)*1440./spd
    ok=(t.sum(1)>0)&(f.sum(1)>.2*t.sum(1))
    return ((f*m).sum(1)[ok]/f.sum(1)[ok])-((t*m).sum(1)[ok]/t.sum(1)[ok])

def datm_qsat(tbot,psrf):
    """CDEPS datm_eSat (ice below 0 C) -> saturation specific humidity; DATM caps QBOT at this value."""
    x=np.clip(tbot-273.15,-50.,50.);e=np.zeros_like(x)
    for cw,ci in zip(reversed(br.DATM_WATER),reversed(br.DATM_ICE)):e=e*x+np.where(x<0,ci,cw)
    return 0.622*e/(psrf/100.-0.378*e)

def hashes(arrays):
    return {k:hashlib.sha256(np.ascontiguousarray(v,dtype=v.dtype.newbyteorder('<')).tobytes()).hexdigest() for k,v in sorted(arrays.items())}

def write_nc(path,site,year,spd,f,lat,lon,zbot,attrs):
    n=365*spd
    with netCDF4.Dataset(str(path),'w',format='NETCDF4_CLASSIC') as nc:
        nc.createDimension('time',n);nc.createDimension('lat',1);nc.createDimension('lon',1)
        t=nc.createVariable('time','f8',('time',));t.units='days since %04d-01-01 00:00:00'%year;t.calendar='noleap'
        t.long_name='UTC interval centre';t[:]=(np.arange(n)+.5)/spd
        v=nc.createVariable('lat','f8',('lat',));v.units='degrees_north';v[:]=np.array([lat])
        v=nc.createVariable('lon','f8',('lon',));v.units='degrees_east';v[:]=np.array([lon])
        v=nc.createVariable('LATIXY','f8',('lat','lon'));v.units='degrees_north';v[:]=np.full((1,1),lat)
        v=nc.createVariable('LONGXY','f8',('lat','lon'));v.units='degrees_east';v[:]=np.full((1,1),lon)
        v=nc.createVariable('ZBOT','f8',('time','lat','lon'));v.units='m';v.long_name='TA sensor height used as forcing reference height';v[:]=np.full((n,1,1),zbot)
        for name,unit,longname in FIELDS:
            v=nc.createVariable(name,'f4',('time','lat','lon'),fill_value=np.float32(1e36));v.units=unit;v.long_name=longname
            v[:]=f[name].astype(np.float32).reshape(n,1,1)
        for k,val in attrs.items():nc.setncattr(k,val)
    with netCDF4.Dataset(str(path)) as nc:
        nc.set_auto_mask(False);back={k:np.asarray(nc.variables[k][:]).reshape(-1) for k in ('time','ZBOT')+tuple(x[0] for x in FIELDS)}
    for name,_,_ in FIELDS:
        if not np.array_equal(back[name],f[name].astype(np.float32)):raise ValueError('read-back mismatch '+name)
    return hashes(back)

def build_site(a,site):
    keys,y0,y1,lat,lon,zbot,formula=SITES[site]
    if site in a.years:y0,y1=a.years[site]
    local=[];coverage={};extra={}
    for key in keys:
        for y,d in read_local(a.cb_dir/TABLE_NAME.format(key),TABLES[key]).items():
            if y0<=y<=y1:
                if y in coverage:raise ValueError('year %d in two tables'%y)
                spd=d['spd'];local.append((y,spd,derive(d['values'],formula,86400./spd)));coverage[y]=d['qc0_pct']
                if 'RH_F' in d['values']:
                    dq=np.abs(q_from_rh(d['values'],formula)-local[-1][2]['QBOT']);extra[y]=float(dq.max())
    local.sort(key=lambda x:x[0])
    if [x[0] for x in local]!=list(range(y0,y1+1)):raise ValueError('years must be contiguous %d-%d'%(y0,y1))
    utc=utc_years(local)
    # exact permutation check, independent of utc_years: per cadence block, UTC = local rolled by the shift
    if len({x[1] for x in local})==1:
        s=TZ_HOURS*local[0][1]//24
        for name,_,_ in FIELDS:
            if not np.array_equal(np.concatenate([u[2][name] for u in utc]),np.roll(np.concatenate([x[2][name] for x in local]),-s)):raise ValueError('UTC permutation '+name)
    else:
        for k,(y,spd,f) in enumerate(local):
            s=TZ_HOURS*spd//24
            for name,_,_ in FIELDS:
                if not np.array_equal(utc[k][2][name][:365*spd-s],f[name][s:]):raise ValueError('UTC body '+name)
    rows=[];offsets=[]
    for y,spd,f,tail in utc:
        for name,(lo,hi) in RANGES.items():
            if not (np.isfinite(f[name]).all() and f[name].min()>=lo and f[name].max()<=hi):raise ValueError('%s %d range %s'%(site,y,name))
        off=centroid_offsets(f['FSDS'],toa_utc(spd,lat,lon),spd,lon);offsets.extend(off.tolist())
        med=float(np.median(off))
        if abs(med)>90:raise ValueError('%s %d FSDS solar centroid %.1f min off UTC'%(site,y,med))
        cov=coverage[y];low=[v for v in COVERAGE_VARS if cov.get(v,0)<50];hum=humidity_screen(f,formula)
        rows.append({**{'humidity_'+k:v for k,v in hum.items()},'site':site,'year':y,'steps_per_day':spd,'records':365*spd,'tail_slots':tail['tail_slots'],'tail_source':tail['tail_source'],
            'fsds_centroid_minus_toa_min_median':round(med,1),'fsds_days':int(off.size),'clock_review':'YES' if abs(med)>15 else 'NO',
            'P_total_mm':round(float(f['PRECTmms'].sum()*86400./spd),1),'TBOT_mean_C':round(float(f['TBOT'].mean()-273.15),2),
            'QBOT_mean_gkg':round(float(f['QBOT'].mean()*1000),3),'PSRF_mean_kPa':round(float(f['PSRF'].mean()/1000),2),
            'FSDS_mean':round(float(f['FSDS'].mean()),1),'FLDS_mean':round(float(f['FLDS'].mean()),1),'WIND_mean':round(float(f['WIND'].mean()),2),
            'datm_qsat_cap_cells':int((f['QBOT']>datm_qsat(f['TBOT'],f['PSRF'])).sum()),
            'local_year_QC0_pct':';'.join('%s=%g'%(v.replace('_F',''),p) for v,p in sorted(cov.items())),
            'low_tower_coverage':'YES:'+','.join(low) if low else 'NO','max_abs_q_rh_minus_q_vpd':'%.2e'%extra[y] if y in extra else ''})
    site_med=float(np.median(offsets))
    if abs(site_med)>20:raise ValueError('%s FSDS solar centroid median %.1f min off UTC'%(site,site_med))
    return utc,rows,site_med,(y0,y1,lat,lon,zbot,formula)

def stream_plan(site,y0,y1,utc):
    mixed=len({u[1] for u in utc})>1
    return {'site':site,'status':'PLAN_NOT_ACTIVATED','stream':'CLM_USRDAT','year_first':y0,'year_last':y1,'year_align':y0,
        'taxmode':'cycle','tintalgo':'linear','offset':0,'dtlimit':2.1 if mixed else 1.5,
        'dtlimit_note':'hourly 1999-2002 and half-hourly 2003-2010 in one stream: CDEPS default dtlimit 1.5 would abort' if mixed else 'CDEPS default',
        'datavars':['ZBOT Sa_z','TBOT Sa_tbot','QBOT Sa_shum','WIND Sa_wind','PRECTmms Faxa_precn','FSDS Faxa_swdn','PSRF Sa_pbot','FLDS Faxa_lwdn'],
        'files':[FILE.format(site,u[0]) for u in utc]}

def run(a):
    write=a.out is not None
    if write:
        if not a.ack:raise ValueError('--write needs --ack-utc-plus9-cyclic-shift')
        if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
        if a.cb_dir.resolve() in (a.out.resolve(),*a.out.resolve().parents):raise ValueError('--out inside the source directory')
        a.out.mkdir()
    report={'stage':'06A','status':'UTC_NOLEAP_DATM_CANDIDATES_NOT_ACTIVATED' if write else 'CHECK_ONLY_NOTHING_WRITTEN',
        'input':'Stage05CB final pre-forcing tables approved 2026-11-05','table_gzip_sha256':TABLES,'sites':{}}
    allrows=[]
    for site in a.sites:
        print('STAGE06A',site,flush=True)
        utc,rows,site_med,(y0,y1,lat,lon,zbot,formula)=build_site(a,site)
        flagged=sum(r[k] for r in rows for k in r if k.startswith('humidity_'))
        entry={'years':[y0,y1],'lat':lat,'lon':lon,'zbot_m':zbot,'es_formula':formula,'clock':CLOCK.get(site,'BIF UTC_OFFSET 9'),
               'fsds_centroid_minus_toa_min_site_median':round(site_med,1),'humidity_screen_cells':flagged,
               'humidity_status':'OPEN_E1' if flagged else 'CLEAN','clock_review_years':[r['year'] for r in rows if r['clock_review']=='YES'],'files':{}}
        if write:
            d=a.out/site;d.mkdir()
            for (y,spd,f,tail),row in zip(utc,rows):
                attrs={'title':'JapanFlux MultiSite 11 UTC NOLEAP DATM forcing CANDIDATE (not activated)','site':site,'forcing_year':y,
                    'source_tables':','.join('%s sha256 %s'%(k,TABLES[k]) for k in SITES[site][0]),
                    'qc_approval':'Stage05CB: all repair rules approved by the user on 2026-11-05 (D1-D14) and 2026-11-04 (D1, D2, C1-C3)',
                    'science_status':'QC_APPROVED_INPUT; DATM_CANDIDATE_NOT_ACTIVATED','model_submission_authorised':'FALSE',
                    'time_reference':'UTC interval centre; source TIMESTAMP_START on UTC+9 moved -9 h by whole slots',
                    'clock_basis':entry['clock'],'time_boundary_policy':'last %d slots from %s'%(tail['tail_slots'],tail['tail_source']),
                    'calendar_policy':'noleap; local Feb 29 rows removed before the UTC shift',
                    'humidity':'QBOT=0.622e/(p-0.378e), e=es(TA)-VPD, es=%s; DATM caps QBOT at its own qsat'%formula,
                    'radiation_precipitation':'FSDS=max(SW_IN_F,0); FLDS=LW_IN_F; PRECTmms=P_F/%d s'%(86400//spd),
                    'zbot_evidence':'TA_F sensor height %.1f m (BIF/BADM)'%zbot,'low_tower_coverage':row['low_tower_coverage'],
                    'clock_check':'FSDS centroid minus TOA %.1f min on the UTC axis; review %s (open item E2 if YES)'%(
                        row['fsds_centroid_minus_toa_min_median'],row['clock_review']),
                    'humidity_screen':'site %s; this year Td>=28C %d, saturated at TA>=28C %d, RH<5%% %d (values unchanged)'%(
                        entry['humidity_status'],row['humidity_Td_ge_28C'],row['humidity_saturated_TA_ge_28C'],row['humidity_RH_lt_5pct'])}
                p=d/FILE.format(site,y);h=write_nc(p,site,y,spd,f,lat,lon,zbot,attrs)
                row['file']=p.name;row['file_sha256']=br.sha(p);row['data_sha256_by_variable']=h
                entry['files'][p.name]={'file_sha256':row['file_sha256'],'data_sha256_by_variable':h}
            with (d/'stream_plan_NOT_ACTIVATED.json').open('x',encoding='utf-8') as f:json.dump(stream_plan(site,y0,y1,utc),f,indent=1);f.write('\n')
        report['sites'][site]=entry;allrows.extend(rows)
        print(json.dumps({'site':site,'years':[y0,y1],'files':len(rows),'fsds_offset_min':round(site_med,1),'humidity':entry['humidity_status'],
            'humidity_cells':flagged,'clock_review_years':entry['clock_review_years'],'low_coverage_years':[r['year'] for r in rows if r['low_tower_coverage']!='NO']}),flush=True)
    view={s:{'years':e['years'],'files':{n:{k:v for k,v in x['data_sha256_by_variable'].items() if k!='QBOT'} for n,x in e['files'].items()}} for s,e in report['sites'].items()}
    report['fingerprint_without_QBOT_and_file_bytes']=br.fingerprint(view)
    report['site_year_rows']=[{k:v for k,v in r.items() if k!='data_sha256_by_variable'} for r in allrows]
    if write:
        cols=[k for k in allrows[0] if k not in ('data_sha256_by_variable',)]
        with (a.out/'site_year_summary_CANDIDATE.tsv').open('x',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,cols,delimiter='\t',extrasaction='ignore');w.writeheader();w.writerows(allrows)
        with (a.out/'summary_CANDIDATE.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06A COMPLETE;',('CANDIDATES WRITTEN TO '+str(a.out)) if write else 'CHECK ONLY, NOTHING WRITTEN','; NO CASE, NO SLURM')
    print(json.dumps({'fingerprint':report['fingerprint_without_QBOT_and_file_bytes'],'files':len(allrows)}))

def selftest():
    # 3 synthetic half-hourly years: UTC slot 0 = local slot 18; the final year's tail wraps to the first year
    local=[(y,48,{'TBOT':np.arange(17520.)+1e5*k}) for k,y in enumerate((2001,2002,2003))]
    utc=utc_years(local)
    assert utc[0][2]['TBOT'][0]==18 and utc[0][2]['TBOT'][-1]==1e5+17 and utc[2][2]['TBOT'][-1]==17
    assert utc[2][3]['tail_source']=='CYCLE_WRAP_FROM_FIRST_YEAR_2001'
    assert np.array_equal(np.concatenate([u[2]['TBOT'] for u in utc]),np.roll(np.concatenate([x[2]['TBOT'] for x in local]),-18))
    # hourly -> half-hourly boundary: pair means one way, repeats on the wrap
    mixed=utc_years([(2002,24,{'X':np.arange(8760.)}),(2003,48,{'X':np.arange(17520.)})])
    assert mixed[0][2]['X'].size==8760 and mixed[0][2]['X'][-9]==.5 and mixed[0][3]['tail_source'].endswith('_HALFHOUR_PAIR_MEAN')
    assert mixed[1][2]['X'].size==17520 and list(mixed[1][2]['X'][-18:-14])==[0,0,1,1]
    # vectorised es and DATM esat match the Stage05BR scalar functions
    t=np.array([-30.,-0.5,0.,12.3,35.])
    for f in ('oneflux_qc_auto','bolton1980'):
        a,b,c=br.ES_FORMULAS[f];assert np.allclose(a*np.exp(b*t/(t+c)),[br.es(x,f) for x in t],rtol=1e-12)
    q=datm_qsat(t+273.15,np.full(5,1e5));e=np.array([br.datm_esat_hpa(x) for x in t])
    assert np.allclose(q,0.622*e/(1000.-0.378*e),rtol=1e-12)
    # QBOT: VPD=0 gives saturation; non-positive vapour pressure is refused
    v={'TA_F':np.array([20.]),'PA_F':np.array([100.]),'VPD_F':np.array([0.]),'SW_IN_F':np.array([-1.]),'LW_IN_F':np.array([300.]),'WS_F':np.array([1.]),'P_F':np.array([1.8])}
    d=derive(v,'oneflux_qc_auto',1800.);assert abs(d['QBOT'][0]-0.622*br.es(20.,'oneflux_qc_auto')/(1000-0.378*br.es(20.,'oneflux_qc_auto')))<1e-15
    assert d['FSDS'][0]==0 and d['PRECTmms'][0]==.001 and d['TBOT'][0]==293.15 and d['PSRF'][0]==1e5
    v['VPD_F']=np.array([30.])
    try:derive(v,'oneflux_qc_auto',1800.)
    except ValueError:pass
    else:raise AssertionError('negative vapour pressure accepted')
    hot=derive({**v,'TA_F':np.array([35.]),'VPD_F':np.array([0.])},'bolton1980',1800.)
    assert humidity_screen(hot,'bolton1980')=={'Td_ge_28C':1,'saturated_TA_ge_28C':1,'RH_lt_5pct':0}
    # solar centroid: TOA itself gives 0; local-time data (9 h late on the UTC axis) is detected
    toa=toa_utc(48,40.,140.9);assert abs(np.median(centroid_offsets(toa,toa,48,140.9)))<1e-9
    assert abs(np.median(centroid_offsets(np.roll(toa,18),toa,48,140.9)))>120
    print('STAGE06A SELF-TEST PASS: UTC shift and cycle wrap, cadence boundary, es/qsat, QBOT guard, solar centroid; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true');p.add_argument('--cb-dir',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--write',action='store_true');p.add_argument('--ack-utc-plus9-cyclic-shift',dest='ack',action='store_true')
    p.add_argument('--sites',default=','.join(SITES));p.add_argument('--years',action='append',default=[],help='SITE=FIRST-LAST override')
    a=p.parse_args()
    if a.self_test:selftest();return
    if a.cb_dir is None or a.write!=(a.out is not None):p.error('--cb-dir required; --write and --out go together')
    a.sites=a.sites.split(',')
    if not set(a.sites)<=set(SITES):p.error('unknown site')
    a.years={s:tuple(int(x) for x in r.split('-')) for s,r in (y.split('=') for y in a.years)}
    run(a)
if __name__=='__main__':main()

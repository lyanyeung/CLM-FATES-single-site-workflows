#!/usr/bin/env python3
"""Batch reuse of 16 existing CDS ZIPs and original 45-field native windows.

READ ONLY except new diagnostic files under ~/japanflux_stage05az. No network,
downloads, model jobs, raw-source/forcing modifications or approved repairs.
Solar-site UTC offsets are explicit sensitivity scenarios, not clock proof.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,statistics,sys,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path,PurePosixPath

STEP=timedelta(minutes=30)
SITES=Counter({'JP-Fjy':6,'JP-Khw':11,'JP-Yms':10,'JP-Tef':4,'JP-Tmd':14})
VARS=Counter({'PA':27,'TA':6,'LW_IN':12})
BOUNDS={'PA':(50.,115.),'TA':(-70.,65.),'LW_IN':(70.,650.)}
RAW={'PA':'sp','TA':'t2m','LW_IN':'strd'}
GRIDS={'JP-Fjy':(35.5,138.8),'JP-Khw':(33.1,130.7),'JP-Yms':(34.8,135.8),
       'JP-Tef':(45.1,142.1),'JP-Tmd':(42.7,141.5)}
# Original BIF longitude, in degrees east; longitude × 4 min gives local
# MEAN solar offset. This does not prove the release's clock convention.
SOLAR_LONGITUDE={'JP-Tef':142.107122,'JP-Tmd':141.523147}
AW_SHA='6b717bdf8232388f59af849da01dbc316a8166e0a07305d3d2567d2d7d55e6ad'
WINDOW_SHA='89e9b41055b782da97ebcbda9c6ddb55a3c6bf6426ad40fdd2bb865e98a687d9'
SOURCE={
 'JP-Fjy':('2001-2021','205660bb8203bf7b16466041183ec9a1598f609727ef042ff4bceb800da949b9'),
 'JP-Khw':('2000-2021','712ab4695704a695c28056eb0cfae0697af8a673228407dbc856088ad83bac79'),
 'JP-Yms':('2000-2023','6bda3beb4fd9b580ef036e4b50f9c3162ca17b82b2b28466820e665bdedbf6f7'),
 'JP-Tef':('2001-2023','315c825b64669aa03daff1d969f58a0a1cf3b574c43400ea1f84588df7f6d684'),
 'JP-Tmd':('2005-2023','3ef287018725cb2b5b4c78130804febbe022dad66415807e70f628b756a13479')}
# Source ZIP hashes are operator-reported in prior Stage05S/Z/AJ/AT/AU/AV reports.
CDS={
 ('JP-Fjy','20050811'):('early','0c51e921a3c35b15dae2c33576517e93ca49b2e0ab584212fc8d505fa3efaad3',('sp',)),
 ('JP-Fjy','20111216'):('early','cc172d7c18e7b7b5199aa7cccc8b941c6115863861860f0618d8b33d4f577c9a',('sp',)),
 ('JP-Fjy','20111217'):('early','f553e574a72e409c988460f7052100496c264321a65a46e5a80a636982d3deed',('sp',)),
 ('JP-Khw','20050811'):('early','111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0',('sp','t2m','strd')),
 ('JP-Khw','20111216'):('early','fb2d7677d7c8a38fe4d5d31eb0af37434cfe0932a59343e36601f61b7e407821',('sp',)),
 ('JP-Khw','20111217'):('early','f590c32432ffac5c10460ea074ea8fc05fb9b8742af96f8301e9d35ed6fb6188',('sp',)),
 ('JP-Yms','20050811'):('early','4bf228a3a53ab7fc6751b8e7438fb459570536ce6f54af2f81de5afc083b59d5',('sp','strd')),
 ('JP-Yms','20111216'):('early','edd1b8acd84b31d8a04f214850dd9f51d9471dbffb91664fa76a54a9b7539c0c',('sp','strd')),
 ('JP-Yms','20111217'):('early','bb50100065193cff70429c626603cd60e957882624db5fbee056f97a23b032f6',('sp','strd')),
 ('JP-Tef','20111216'):('late','533b462fa0804a3d34428b6dd5f9b38b8a9e70dbc705af481c18ec614ea16148',('strd',)),
 ('JP-Tef','20111217'):('late','81043becb8ccce9936164d7e1e3afdc56c55a84b077b314c4672339f3a81f532',('strd',)),
 ('JP-Tef','20220408'):('late','eaa4a4e522dfa18e07e8e52a54fccb2a48bec4fd8b7e9b017adfd9c04e492bd3',('strd',)),
 ('JP-Tmd','20050811'):('late','cd722e173c24154ccb5d28a632683cb39473389ac163b12439cce8e870721fe6',('sp','t2m','strd')),
 ('JP-Tmd','20111216'):('late','a719ed536b1860fa46c1217ed09b8509232312ef949589951d6e2cf0b4754763',('sp',)),
 ('JP-Tmd','20111217'):('late','a0e17f4da7f855b5f98c8ea109dca0994889caf074ed48e0b43a91dd9a892a18',('sp',)),
 ('JP-Tmd','20220408'):('late','315a75242e2db2692c3f80d076702a3d88b87e061c21ceae1b04397d924259c2',('sp',))}

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def checked(p,expected):
    if p.is_symlink() or not p.is_file() or digest(p)!=expected:
        raise ValueError('Missing/symlink/SHA256 mismatch: '+str(p))
def stamp(s):return datetime.strptime(s,'%Y%m%d%H%M')
def number(s):
    try:
        x=float(s)
        return x if math.isfinite(x) and x>-9990 else None
    except (TypeError,ValueError):return None
def table(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f,delimiter='\t')
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):raise ValueError('TSV header malformed')
        return list(r)
def parse_cds(data,site,day,expected,grid):
    """Validate original ZIP, CRC, CSV schema, 24 UTC hours and grid."""
    if not 0<len(data)<=2_000_000:raise ValueError('CDS ZIP size')
    seen={};grids=set(); names=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members=[x for x in z.infolist() if not x.is_dir()]
        if not 1<=len(members)<=len(expected) or z.testzip() is not None:raise ValueError('CDS ZIP/CRC/members')
        for info in members:
            path=PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in info.filename or not info.filename.lower().endswith('.csv') or info.file_size>1_000_000:
                raise ValueError('CDS member unsafe')
            reader=csv.DictReader(io.StringIO(z.read(info).decode('utf-8-sig')))
            fields=reader.fieldnames or []; base={'valid_time','latitude','longitude'}
            columns=set(fields)-base
            if len(fields)!=len(set(fields)) or not base<=set(fields) or not columns or not columns<=set(expected):
                raise ValueError('CDS schema')
            records=list(reader)
            if len(records)!=24:raise ValueError('CDS CSV is not 24 hours')
            for rec in records:
                t=datetime.strptime(rec['valid_time'],'%Y-%m-%d %H:%M:%S')
                if t.strftime('%Y%m%d')!=day or t.minute or t.second:raise ValueError('CDS time')
                lat=float(rec['latitude']);lon=float(rec['longitude'])
                if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat-grid[0])>.001 or abs(lon-grid[1])>.001:raise ValueError('CDS grid')
                grids.add((lat,lon))
                for col in columns:
                    x=number(rec[col]);key=(col,t)
                    if key in seen or x is None:raise ValueError('CDS duplicate/nonfinite')
                    if col=='sp' and not 0<x/1000<120:raise ValueError('CDS sp')
                    if col=='t2m' and not 180<x<340:raise ValueError('CDS t2m')
                    if col=='strd' and not 0<=x/3600<1500:raise ValueError('CDS strd')
                    seen[key]=x/1000 if col=='sp' else x-273.15 if col=='t2m' else x/3600
            names.append(info.filename)
    start=datetime.strptime(day,'%Y%m%d')
    if set(seen)!={(v,start+timedelta(hours=h)) for v in expected for h in range(24)} or len(grids)!=1:
        raise ValueError('CDS missing variables/hours or inconsistent grid')
    return seen,sorted(names),list(next(iter(grids)))
def reference(grid,var,local_start,offset_minutes):
    """Return grid context and support; no extrapolation or half-hour truth.

    sp/t2m: linear grid instant values to source interval midpoint, an
    approximation to an interval mean. strd: already deaccumulated hour-ending
    energy / 3600; weighted overlap assumes each hourly mean is constant within
    that hour, which is an approximation, not known half-hour radiation.
    """
    start=local_start-timedelta(minutes=offset_minutes);mid=start+timedelta(minutes=15)
    floor=mid.replace(minute=0,second=0,microsecond=0)
    if var=='LW_IN':
        cursor=start;end=start+STEP;total=0.;supports=[]
        while cursor<end:
            hour_end=cursor.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
            cut=min(end,hour_end);seconds=(cut-cursor).total_seconds()
            value=grid.get(('strd',hour_end))
            if value is None:return None,hour_end.isoformat()+'Z','HOUR_END_OVERLAP_MISSING'
            total+=value*seconds;supports.append(hour_end.isoformat()+'Z@'+str(round(seconds,3))+'s')
            cursor=cut
        return total/STEP.total_seconds(),','.join(supports),'HOUR_END_MEAN_WEIGHTED_OVERLAP_APPROX'
    a=grid.get((RAW[var],floor));b=grid.get((RAW[var],floor+timedelta(hours=1)))
    if a is None or b is None:return None,mid.isoformat()+'Z','INSTANT_MIDPOINT_NO_BRACKET'
    frac=(mid-floor).total_seconds()/3600
    return a+(b-a)*frac,mid.isoformat()+'Z','INSTANT_INTERPOLATED_TO_MIDPOINT_APPROX'
def bridge(a,b,n):return [a+(b-a)*i/(n+1) for i in range(1,n+1)]
def clock_label(site,offset_minutes):
    if site not in SOLAR_LONGITUDE:return 'SOURCE_README_STANDARD_UTC_PLUS9'
    if abs(offset_minutes-540)<1e-9:return 'OPERATOR_JST_PLUS9_HYPOTHESIS'
    if abs(offset_minutes-SOLAR_LONGITUDE[site]*4)<1e-9:return 'LOCAL_MEAN_SOLAR_LONGITUDE_DIAGNOSTIC_NOT_PROVEN'
    return 'HYPOTHETICAL_FIXED_OFFSET_SENSITIVITY'
def windows(records,ledger):
    byflag=defaultdict(dict);unique={}; events={}
    for row in ledger:
        key=(row['site'],row['variable'],stamp(row['native_source_halfhour_start']))
        if key in events or row['original_QC']!='2' or row['science_approval_status']!='HOLD_NO_APPROVED_30MIN_REPLACEMENT':raise ValueError('AW HOLD/key')
        events[key]=row
    if len(events)!=45 or Counter(k[0] for k in events)!=SITES or Counter(k[1] for k in events)!=VARS or len({(k[0],k[2]) for k in events})!=35:
        raise ValueError('AW scope')
    for row in records:
        site,var=row['site'],row['variable'];target=(site,var,stamp(row['flag_native']))
        when=stamp(row['native']);off=int(row['offset_halfhours'])
        if target not in events or when!=target[2]+off*STEP or off in byflag[target]:raise ValueError('source window key/time')
        q=number(row['source_F_QC']); f=number(row['source_F_value']); era=number(row['same_release_ERA'])
        if row['is_preexisting_45_flag'] not in ('True','False'):raise ValueError('source flag')
        if q==2 and f is not None and (era is None or abs(f-era)>1e-6):raise ValueError('QC2 source F/ERA mismatch in window')
        point={'site':site,'var':var,'t':when,'f':f,'q':q,'era':era,'flag':row['is_preexisting_45_flag']=='True',
               'raw_sensor':number(row.get('source_raw_sensor')),
               'mds':number(row.get('source_F_MDS')),'mds_qc':number(row.get('source_F_MDS_QC')),
               'co':{v:{'f':number(row.get('co_'+v+'_F')),'q':number(row.get('co_'+v+'_F_QC')),
                        'field_present':row.get('co_'+v+'_F_present','False')=='True'} for v in ('PA','TA','LW_IN')}}
        if point['co'][var]['field_present'] and (point['co'][var]['f']!=f or point['co'][var]['q']!=q):
            raise ValueError('Target and co-variable values differ')
        k=(site,var,when)
        if k in unique and unique[k]!=point:raise ValueError('source overlapping windows differ')
        unique[k]=point;byflag[target][off]=point
    if set(byflag)!=set(events) or any(set(v)!=set(range(-48,49)) for v in byflag.values()):raise ValueError('not full 45 ±24h windows')
    for k,e in events.items():
        p=unique[k]
        if not p['flag'] or p['q']!=2 or p['f'] is None or p['era'] is None or abs(p['f']-p['era'])>1e-6 or abs(p['f']-float(e['original_source_F_QC2']))>1e-6:
            raise ValueError('AW source event mismatch')
    if {k for k,v in unique.items() if v['flag']}!=set(events):raise ValueError('flag scope mismatch')
    return unique,events
def groups(events):
    out=[]
    for site,var in sorted({k[:2] for k in events}):
        for k in sorted(k for k in events if k[:2]==(site,var)):
            if not out or out[-1][0]!=(site,var) or k[2]-out[-1][1][-1][2]!=STEP:out.append(((site,var),[k]))
            else:out[-1][1].append(k)
    if len(out)!=17:raise ValueError('17 group scope')
    return out
def write_tsv(path,rows):
    if not rows:raise ValueError('No output rows')
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
def run(a):
    checked(a.ledger,AW_SHA);checked(a.windows,WINDOW_SHA)
    source_paths=[]
    for site,(span,sha) in SOURCE.items():
        path=a.source_root/site/'forcing'/'packages'/f'JPF_{site}_FLUXNET_{span}_v1.3_r1.zip'
        checked(path,sha);source_paths.append((path,sha))
    grid=defaultdict(dict);cds_meta=[];cds_paths=[]
    for (site,day),(which,sha,variables) in sorted(CDS.items()):
        path=(a.early if which=='early' else a.late)/f'{site}_ERA5Land_timeseries_{day}_CSV_response.zip'
        checked(path,sha); data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('CDS changed during read')
        values,members,coords=parse_cds(data,site,day,variables,GRIDS[site])
        for k,v in values.items():
            if k in grid[site]:raise ValueError('duplicate CDS site/variable/hour')
            grid[site][k]=v
        cds_paths.append((path,sha));cds_meta.append({'site':site,'day':day,'sha256':sha,'variables':list(variables),'grid':coords,'members':members})
    unique,events=windows(table(a.windows),table(a.ledger));grps=groups(events)
    points=[];summary=[];background=[]
    for (site,var),keys in grps:
        start=keys[0][2];end=keys[-1][2];n=len(keys);lo,hi=BOUNDS[var]
        left=unique[(site,var,start-STEP)];right=unique[(site,var,end+STEP)]
        for p in (left,right):
            if p['flag'] or p['q']!=2 or p['f'] is None or p['era'] is None or abs(p['f']-p['era'])>1e-6 or not lo<=p['f']<=hi:
                raise ValueError('flagged/invalid QC2 anchor')
        shadow=bridge(left['f'],right['f'],n)
        offsets=(510,540,570,SOLAR_LONGITUDE[site]*4) if site in SOLAR_LONGITUDE else (540,)
        for off in offsets:
            clock=clock_label(site,off)
            counts=Counter(); diffs=defaultdict(list); sides=defaultdict(list); sample_times=defaultdict(list)
            for k,p in sorted(unique.items()):
                if k[:2]!=(site,var) or not start-timedelta(hours=24)<=p['t']<=end+timedelta(hours=24):continue
                if p['flag'] or p['f'] is None or p['q'] not in (0,1,2) or not lo<=p['f']<=hi:continue
                if any(abs((p['t']-q[2]).total_seconds())<=7200 for q in events if q[:2]==(site,var)):continue
                ref,support,method=reference(grid[site],var,p['t'],off)
                if ref is None:continue
                quality=int(p['q']);counts[quality]+=1;diffs[quality].append(p['f']-ref)
                sides[(quality,'left' if p['t']<start else 'right')].append(p['f']-ref)
                sample_times[quality].append(p['t'])
                background.append({'site':site,'variable':var,'group_start':start.strftime('%Y%m%d%H%M'),
                    'offset_minutes':off,'clock':clock,'native':p['t'].strftime('%Y%m%d%H%M'),
                    'source_F':p['f'],'source_F_QC':quality,'grid_context':ref,
                    'source_minus_grid':p['f']-ref,'grid_support_UTC':support,'matching':method,
                    'source_status':'QC0_MEASURED' if quality==0 else 'QC1_GAPFILLED' if quality==1 else 'QC2_SAME_RELEASE_ERA_DERIVED'})
            def med(q):return statistics.median(diffs[q]) if diffs[q] else None
            for j,k in enumerate(keys):
                ref,support,method=reference(grid[site],var,k[2],off)
                delta=None if ref is None else shadow[j]-ref
                ledger=events[k]
                emin=float(ledger['independent_ERA5L_hourly_min']);emax=float(ledger['independent_ERA5L_hourly_max'])
                env=('INSIDE' if emin<=shadow[j]<=emax else 'BELOW' if shadow[j]<emin else 'ABOVE') if off==540 else 'NOT_COMPARABLE_OFFSET_NOT_UTC_PLUS9'
                source=unique[k]
                entry={'site':site,'variable':var,'native':k[2].strftime('%Y%m%d%H%M'),
                    'offset_minutes':off,'clock':clock,'candidate_shadow_NOT_APPROVED':shadow[j],
                    'grid_context_NOT_HALF_HOUR_TRUTH':ref,'shadow_minus_grid':delta,
                    'shadow_minus_grid_minus_background_QC2_median':None if delta is None or med(2) is None else delta-med(2),
                    'prior_UTC9_hourly_envelope_min':emin,'prior_UTC9_hourly_envelope_max':emax,
                    'prior_envelope_position_NOT_APPROVAL':env,
                    'grid_support_UTC':support,'matching':method,'original_F':source['f'],
                    'original_raw_sensor':source['raw_sensor'],'original_F_MDS':source['mds'],
                    'original_F_MDS_QC_DISTINCT_FROM_F_QC':source['mds_qc'],
                    'science_status':'HOLD_NO_APPROVED_REPLACEMENT'}
                for v in ('PA','TA','LW_IN'):
                    c=source['co'][v];entry['co_'+v+'_F']=c['f'];entry['co_'+v+'_F_QC']=c['q']
                    entry['co_'+v+'_field_present']=c['field_present']
                    entry['co_'+v+'_is_previously_flagged']=(site,v,k[2]) in events
                points.append(entry)
            record={'site':site,'variable':var,'native_start':start.strftime('%Y%m%d%H%M'),
                'native_end':end.strftime('%Y%m%d%H%M'),'flagged_HH':n,'offset_minutes':off,'clock':clock,
                'scientific_status':'HOLD_NO_APPROVAL_GRID_ELEVATION_UNVERIFIED'}
            for q in (0,1,2):
                vals=diffs[q];record[f'qc{q}_paired_count']=counts[q]
                record[f'qc{q}_source_minus_grid_median']=med(q)
                record[f'qc{q}_source_minus_grid_min']=min(vals) if vals else None
                record[f'qc{q}_source_minus_grid_max']=max(vals) if vals else None
                record[f'qc{q}_native_first']=min(sample_times[q]).strftime('%Y%m%d%H%M') if vals else None
                record[f'qc{q}_native_last']=max(sample_times[q]).strftime('%Y%m%d%H%M') if vals else None
                for side in ('left','right'):
                    a_side=sides[(q,side)]
                    record[f'qc{q}_{side}_paired_count']=len(a_side)
                    record[f'qc{q}_{side}_median']=statistics.median(a_side) if a_side else None
            summary.append(record)
    if len({(r['site'],r['variable'],r['native']) for r in points})!=45:raise ValueError('output coverage')
    if any(r['grid_context_NOT_HALF_HOUR_TRUTH'] is None for r in points if r['offset_minutes']==540):raise ValueError('base time lacks reference support')
    # Repeat source and derived-file hash gates before producing output.
    checked(a.ledger,AW_SHA);checked(a.windows,WINDOW_SHA)
    for p,sha in source_paths+cds_paths:checked(p,sha)
    base=Path.home()/'japanflux_stage05az'
    if base.is_symlink() or (base.exists() and not base.is_dir()) or a.out.parent.resolve()!=base.resolve() or a.out.exists() or a.out.is_symlink():
        raise ValueError('Output must be fresh direct child of ~/japanflux_stage05az')
    base.mkdir(exist_ok=True);a.out.mkdir()
    write_tsv(a.out/'candidate_hourly_context_HOLD.tsv',points)
    write_tsv(a.out/'group_source_grid_residuals_HOLD.tsv',summary)
    write_tsv(a.out/'background_pairs_READONLY.tsv',background)
    meta={'status':'DIAGNOSTIC_ONLY_ALL_45_HOLD','approved_replacements':0,
          'source_outer_zip_count_sha256_verified_twice':len(source_paths),
          'cds_zip_count_sha256_crc_schema_24h_grid_verified':len(cds_meta),
          'source_ledger_sha256':AW_SHA,'source_windows_sha256':WINDOW_SHA,'cds_provenance':cds_meta,
          'flags':45,'groups':17,'candidate_scenario_rows':len(points),
          'grid_elevation':'UNVERIFIED','solar_offsets':'FIXED AND LONGITUDE-BASED MEAN SOLAR SENSITIVITY ONLY, NOT SOURCE CLOCK PROOF',
          'matching':'instantaneous PA/TA at interval midpoint approximation; strd hourly mean weighted overlap assumes within-hour constancy',
          'background':'quality-separated, flags and ±2h excluded; QC2 derived, not independent measurements',
          'no_bias_correction_applied':True,'source_zip_forcing_model_pft_slurm_changed':False}
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(meta,f,indent=2);f.write('\n')
    print('STAGE05AZ BULK READONLY COMPLETE; 45/45 HOLD; 0 APPROVED')
    print('OUTPUT',a.out,'GROUP_SCENARIOS',len(summary),'CANDIDATE_SCENARIOS',len(points),'BACKGROUND_PAIRS',len(background))
    print('SOURCE_ZIPS',len(source_paths),'CDS_ZIPS',len(cds_meta),'GRID_ELEVATION_UNVERIFIED')
    print('PRINT_GROUP_SUMMARY_AND_CANDIDATE_TABLE_FOR_REVIEW; NO NETWORK/DOWNLOAD/FORCING/MODEL/SLURM')

def selftest():
    data={('sp',datetime(2020,1,1,0)):100.,('sp',datetime(2020,1,1,1)):102.,
          ('strd',datetime(2020,1,1,1)):300.}
    t=datetime(2020,1,1,9)
    assert reference(data,'PA',t,540)[0]==100.5
    assert reference(data,'PA',t+STEP,540)[0]==101.5
    assert reference(data,'LW_IN',t,540)[0]==300 and reference(data,'LW_IN',t+STEP,540)[0]==300
    cross={('strd',datetime(2020,1,1,0)):250.,('strd',datetime(2020,1,1,1)):300.}
    assert abs(reference(cross,'LW_IN',t,540.1)[0]-(250*6+300*1794)/1800)<1e-9
    assert reference(data,'PA',t-timedelta(hours=1),540)[0] is None
    assert bridge(98,102,3)==[99.,100.,101.]
    assert clock_label('JP-Tef',SOLAR_LONGITUDE['JP-Tef']*4)=='LOCAL_MEAN_SOLAR_LONGITUDE_DIAGNOSTIC_NOT_PROVEN'
    assert clock_label('JP-Tmd',540)=='OPERATOR_JST_PLUS9_HYPOTHESIS'
    assert clock_label('JP-Yms',540)=='SOURCE_README_STANDARD_UTC_PLUS9'
    assert reference({('strd',datetime(2020,1,1,0)):250.},'LW_IN',datetime(2020,1,1,8,30),540)[0]==250.
    day='20200101';text='valid_time,latitude,longitude,sp\n'+''.join(f'2020-01-01 {h:02d}:00:00,35.5,138.8,100000\n' for h in range(24))
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:z.writestr('x.csv',text)
    vals,names,loc=parse_cds(buf.getvalue(),'JP-Fjy',day,('sp',),(35.5,138.8))
    assert len(vals)==24 and vals[('sp',datetime(2020,1,1))]==100.
    try:parse_cds(buf.getvalue(),'JP-Fjy',day,('sp','strd'),(35.5,138.8))
    except ValueError:pass
    else:raise AssertionError('missing CDS variable accepted')
    assert len(CDS)==16 and sum(SITES.values())==45
    print('STAGE05AZ SELF-TEST PASS: CDS ZIP/schema/grid, fractional-hour overlap, midpoint, midnight, missing data; ALL HOLD')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--ledger',type=Path);p.add_argument('--windows',type=Path)
    p.add_argument('--early',type=Path);p.add_argument('--late',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--source-root',type=Path,default=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(getattr(a,k) is None for k in ('ledger','windows','early','late','out')):p.error('all source inputs and fresh output required')
    run(a)
if __name__=='__main__':main()

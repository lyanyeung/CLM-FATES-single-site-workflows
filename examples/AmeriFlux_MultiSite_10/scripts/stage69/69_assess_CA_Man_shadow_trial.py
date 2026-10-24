#!/usr/bin/env python3
"""Stage69: independently assess CA-Man Stage68 temperature SHADOW trial.

--self-test verifies thermodynamics and synthetic changed cells without HPC.
--check validates Stage68/Stage61 inputs and independently compares full
15-year original and shadow forcing; writes nothing.
--audit additionally writes only NEW diagnostic reports, never forcing.
Science and production acceptance remain HOLD, even after a successful run.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import tempfile
from collections import Counter
from datetime import datetime,timedelta,timezone
from itertools import zip_longest
from pathlib import Path

EXP=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
ORIGINAL_SHA='fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705'
CHANGED={'TBOT','TA_USE','VPD_USE'}
COLS=['site','episode_id','timestamp','original_T_C','shadow_T_C',
      'delta_T_C','original_RH_pct','shadow_RH_pct','delta_RH_pp',
      'original_VPD_hPa','shadow_VPD_hPa','delta_VPD_hPa',
      'QBOT_unchanged','PSRF_unchanged','original_local_jumps',
      'shadow_local_jumps','provisional_ERA5_T_C','original_abs_ERA_error_C',
      'shadow_abs_ERA_error_C','RH_delta_ge25pp','shadow_RH_below20',
      'VPD_delta_ge10hPa','ERA_error_worse_ge2C',
      'moisture_science_review','science_decision']

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):
            h.update(chunk)
    return h.hexdigest()

def read_csv(path,required):
    if not path.is_file():raise RuntimeError('Missing CSV: '+str(path))
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        head=reader.fieldnames or []
        if len(head)!=len(set(head)) or not set(required).issubset(head):
            raise RuntimeError('Unexpected CSV schema '+str(path)+': '+str(set(required)-set(head)))
        return list(reader)

def number(x):
    try:
        z=float(x)
        return z if math.isfinite(z) and z > -9990 else None
    except (TypeError,ValueError):
        return None

def stamp(x):
    return datetime.fromisoformat(x.strip())

def physics(row):
    tc=float(row['TBOT'])-273.15
    q=float(row['QBOT']); p=float(row['PSRF'])
    es=6.112*math.exp(17.67*tc/(tc+243.5))
    vapour=q*(p/100)/(0.622+0.378*q)
    rh=100*vapour/es;vpd=es-vapour
    if not all(math.isfinite(v) for v in (rh,vpd)):
        raise RuntimeError('Nonfinite thermodynamic state')
    if abs(float(row['TA_USE'])-tc)>0.02 or abs(float(row['VPD_USE'])-vpd)>0.02:
        raise RuntimeError('Inconsistent TBOT, TA_USE or VPD_USE state')
    return tc,rh,vpd

def verify_manifests(s68,s61):
    manifest=s68/'manifest.json'
    info=json.loads(manifest.read_text(encoding='utf-8'))
    necessary={'stage':68,'site':'CA-Man','science_approved':False,
               'production_approved':False,'source_clock_verified':False,
               'original_forcing_modified':False,'auto_submitted_jobs':False,
               'modified_rows':19}
    for key,expected in necessary.items():
        if info.get(key)!=expected:
            raise RuntimeError('Stage68 manifest differs: '+key)
    if info.get('original_sha256')!=ORIGINAL_SHA:
        raise RuntimeError('Pinned original CA-Man SHA mismatch in manifest')
    old=Path(info['original_path']).resolve(strict=True)
    shadow=Path(info['trial_path']).resolve(strict=True)
    if not shadow.is_relative_to(s68.resolve(strict=True)) or 'NOT_PRODUCTION' not in shadow.name:
        raise RuntimeError('Not a stage68 contained, clearly shadow-labeled trial')
    if old==shadow or sha(old)!=ORIGINAL_SHA or sha(shadow)!=info.get('trial_sha256'):
        raise RuntimeError('Original or shadow SHA validation failed')
    src61=s61/'P1_context_source_comparisons.csv'
    if sha(src61)!=info.get('input_reports_sha256',{}).get('Stage61_context'):
        raise RuntimeError('Pinned Stage61 context SHA validation failed')
    ledger=read_csv(s68/'scoped_temperature_trial_edit_ledger.csv',
                    ['site','episode_id','timestamp','original_TBOT_K',
                     'trial_TBOT_K','original_TA_USE_C','trial_TA_USE_C',
                     'original_VPD_USE_hPa','trial_VPD_USE_hPa',
                     'unchanged_QBOT_kg_kg','unchanged_PSRF_Pa','science_status'])
    if len(ledger)!=19 or len({x['timestamp'] for x in ledger})!=19:
        raise RuntimeError('Expected exactly 19 distinct ledger records')
    if {x['episode_id'] for x in ledger}!=set(info.get('target_event_ids',[])):
        raise RuntimeError('Stage68 ledger episode list inconsistent')
    if any(x['site']!='CA-Man' or x['science_status']!='SHADOW_SENSITIVITY_ONLY_NOT_APPROVED'
           for x in ledger):
        raise RuntimeError('Stage68 ledger contains approved/non CA-Man changes')
    f0=info.get('original_scanner',{}).get('flags',{})
    f1=info.get('trial_scanner',{}).get('flags',{})
    if (f0.get('ta_step_over10C'),f1.get('ta_step_over10C'))!=(185,150):
        raise RuntimeError('Stage68 temperature jump census changed')
    return info,old,shadow,ledger,src61

def review(s68,s61):
    info,old,shadow,ledger,src61=verify_manifests(s68,s61)
    keyed={stamp(x['timestamp']):x for x in ledger}
    watch={t+timedelta(minutes=30*i) for t in keyed for i in (-1,0,1)}
    near={};seen=set();count=0
    with old.open(newline='',encoding='utf-8-sig') as f0,shadow.open(newline='',encoding='utf-8-sig') as f1:
        r0=csv.DictReader(f0);r1=csv.DictReader(f1)
        if r0.fieldnames!=r1.fieldnames:
            raise RuntimeError('Original vs shadow CSV schema differs')
        if not {'time','TBOT','TA_USE','VPD_USE','PSRF','QBOT'}.issubset(r0.fieldnames or []):
            raise RuntimeError('Missing model meteorological fields')
        for a,b in zip_longest(r0,r1):
            if a is None or b is None or a['time']!=b['time']:
                raise RuntimeError('Original/shadow row/time mismatch')
            count+=1;t=stamp(a['time'])
            modified={k for k in r0.fieldnames if a[k]!=b[k]}
            if t in keyed:
                if modified!=CHANGED:
                    raise RuntimeError('Incorrect field whitelist for edited timestamp '+a['time'])
                led=keyed[t]
                for col,k0,k1 in [
                    ('TBOT','original_TBOT_K','trial_TBOT_K'),
                    ('TA_USE','original_TA_USE_C','trial_TA_USE_C'),
                    ('VPD_USE','original_VPD_USE_hPa','trial_VPD_USE_hPa'),
                    ('QBOT','unchanged_QBOT_kg_kg','unchanged_QBOT_kg_kg'),
                    ('PSRF','unchanged_PSRF_Pa','unchanged_PSRF_Pa')]:
                    if abs(float(a[col])-float(led[k0]))>2e-5 or abs(float(b[col])-float(led[k1]))>2e-5:
                        raise RuntimeError('Ledger / forcing cell mismatch '+a['time']+' '+col)
                physics(a);physics(b)
                if t in seen:raise RuntimeError('Duplicate edited timestamp')
                seen.add(t)
            elif modified:
                raise RuntimeError('Non-target original forcing cells differ '+a['time'])
            if t in watch:
                if t in near:raise RuntimeError('Duplicate context time')
                near[t]=(a,b)
    if count!=262800 or seen!=set(keyed) or not watch.issubset(near):
        raise RuntimeError('Full-year row census or edited-context coverage mismatch')
    ctx=read_csv(src61,['site','episode_id','timestamp','candidate_TA_C','ERA5_TA_ERA_C'])
    by_key={}
    for line in ctx:
        k=(line['site'],line['episode_id'],line['timestamp'])
        if k in by_key:raise RuntimeError('Duplicate Stage61 context key '+str(k))
        by_key[k]=line
    results=[]
    for t,led in sorted(keyed.items()):
        a,b=near[t]
        p0,p1=near[t-timedelta(minutes=30)]
        n0,n1=near[t+timedelta(minutes=30)]
        t0,h0,v0=physics(a);t1,h1,v1=physics(b)
        jump_old=(t0-(float(p0['TBOT'])-273.15),(float(n0['TBOT'])-273.15)-t0)
        jump_new=(t1-(float(p1['TBOT'])-273.15),(float(n1['TBOT'])-273.15)-t1)
        local_old=sum(abs(x)>10 for x in jump_old)
        local_new=sum(abs(x)>10 for x in jump_new)
        source=by_key.get(('CA-Man',led['episode_id'],led['timestamp']))
        if source is None or abs(float(source['candidate_TA_C'])-t0)>.02:
            raise RuntimeError('Edited time not independently confirmed by Stage61 '+led['timestamp'])
        era=number(source['ERA5_TA_ERA_C'])
        d0=abs(t0-era) if era is not None else None
        d1=abs(t1-era) if era is not None else None
        dh=h1-h0;dv=v1-v0
        big_rh=abs(dh)>=25
        low_rh=h1<20
        big_vpd=abs(dv)>=10
        risk=big_rh or low_rh or big_vpd
        results.append({
          'site':'CA-Man','episode_id':led['episode_id'],'timestamp':led['timestamp'],
          'original_T_C':round(t0,5),'shadow_T_C':round(t1,5),
          'delta_T_C':round(t1-t0,5),'original_RH_pct':round(h0,5),
          'shadow_RH_pct':round(h1,5),'delta_RH_pp':round(dh,5),
          'original_VPD_hPa':round(v0,5),'shadow_VPD_hPa':round(v1,5),
          'delta_VPD_hPa':round(dv,5),
          'QBOT_unchanged':a['QBOT']==b['QBOT'],
          'PSRF_unchanged':a['PSRF']==b['PSRF'],
          'original_local_jumps':local_old,'shadow_local_jumps':local_new,
          'provisional_ERA5_T_C':era if era is not None else '',
          'original_abs_ERA_error_C':round(d0,5) if d0 is not None else '',
          'shadow_abs_ERA_error_C':round(d1,5) if d1 is not None else '',
          'RH_delta_ge25pp':big_rh,'shadow_RH_below20':low_rh,
          'VPD_delta_ge10hPa':big_vpd,
          'ERA_error_worse_ge2C':d0 is not None and d1-d0>=2,
          'moisture_science_review':risk,'science_decision':'SHADOW_SENSITIVITY_HOLD'
        })
    return results,info,old,shadow

def present(result,info):
    print('STAGE69 | CA-Man STAGE68 SHADOW TEMPERATURE SCIENCE ASSESSMENT')
    print('Confirmed edited half-hours:',len(result))
    print('Full forcing >10C steps: original',info['original_scanner']['flags']['ta_step_over10C'],
          'shadow',info['trial_scanner']['flags']['ta_step_over10C'])
    print('Local >10C steps around edits: original',sum(x['original_local_jumps'] for x in result),
          'shadow',sum(x['shadow_local_jumps'] for x in result))
    for label,key in [('RH shifts >=25 percentage points','RH_delta_ge25pp'),
                      ('Shadow RH below 20 percent','shadow_RH_below20'),
                      ('VPD shifts >=10 hPa','VPD_delta_ge10hPa'),
                      ('ERA residual worsened >=2C PROVISIONAL','ERA_error_worse_ge2C'),
                      ('Manual moisture-science review','moisture_science_review')]:
        print(label+':',sum(x[key] for x in result))
    print('All 19 edits ranked by absolute RH shift:')
    for x in sorted(result,key=lambda r:abs(r['delta_RH_pp']),reverse=True):
        print(' ',x['timestamp'],x['episode_id'],
              f"T {x['original_T_C']:.2f}->{x['shadow_T_C']:.2f}C",
              f"RH {x['original_RH_pct']:.1f}->{x['shadow_RH_pct']:.1f}%",
              f"VPD {x['original_VPD_hPa']:.2f}->{x['shadow_VPD_hPa']:.2f}hPa",
              f"jumps {x['original_local_jumps']}->{x['shadow_local_jumps']}",
              'MOISTURE_REVIEW' if x['moisture_science_review'] else 'PHYSICS_SCREEN_OK')
    print('SCIENTIFIC STATUS: HOLD; 15 Stage68 rejected cases still excluded; no production approval.')

def output(out,result,info,old,shadow,stage68,stage61):
    out.mkdir(exist_ok=False)
    def write(name,rows):
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=COLS,extrasaction='raise')
            w.writeheader();w.writerows(rows)
    write('all_19_shadow_T_RH_VPD_impacts.csv',result)
    write('moisture_science_review.csv',[x for x in result if x['moisture_science_review']])
    receipt={'stage':69,'site':'CA-Man','reviewed_shadow_edits':len(result),
             'input_sha256':{
                 'stage68_manifest':sha(stage68/'manifest.json'),
                 'stage68_ledger':sha(stage68/'scoped_temperature_trial_edit_ledger.csv'),
                 'stage61_context':sha(stage61/'P1_context_source_comparisons.csv'),
                 'original_forcing':sha(old),'shadow_forcing':sha(shadow)},
             'RH_shift_ge25pp':sum(x['RH_delta_ge25pp'] for x in result),
             'shadow_RH_below20pct':sum(x['shadow_RH_below20'] for x in result),
             'manual_moisture_review':sum(x['moisture_science_review'] for x in result),
             'original_T_step_flags':185,'shadow_T_step_flags':150,
             'original_modified':False,'shadow_modified':False,'auto_repair':False,
             'source_clock_verified':False,'science_approved':False,
             'production_approved':False,'model_jobs_submitted':False,
             'limitations':[
              'The 19 edits are hypothetical temperature interpolation, not independently verified repairs.',
              'Fifteen Stage68 moisture-physics-rejected cases remain excluded.',
              'Unchanged QBOT with changed TA modifies RH and VPD and can introduce ecological biases.',
              'ERA5 comparisons are provisional context, not independent proof of correctness.',
              'Full science review and separate low-RH/other-temperature gates remain HOLD.']}
    (out/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out)
    print('Only new science reports written. Original and shadow forcing unchanged.')

def self_test():
    with tempfile.TemporaryDirectory(prefix='stage69_test_') as d:
        root=Path(d);original=root/'old.csv';shadow=root/'new.csv'
        names=['time','TBOT','TA_USE','QBOT','PSRF','VPD_USE']
        a=[];b=[]
        for i,tc in enumerate((10.,10.,24.,10.,10.)):
            es=6.112*math.exp(17.67*tc/(tc+243.5))
            vap=.006*1013.25/(.622+.378*.006)
            record={'time':str(i),'TBOT':str(tc+273.15),
                    'TA_USE':str(tc),'QBOT':'.006','PSRF':'101325',
                    'VPD_USE':str(es-vap)}
            a.append(record)
            revised=dict(record)
            if i==2:
                tc1=10.
                e1=6.112*math.exp(17.67*tc1/(tc1+243.5))
                revised['TBOT']=str(tc1+273.15)
                revised['TA_USE']=str(tc1)
                revised['VPD_USE']=str(e1-vap)
            b.append(revised)
        for path,records in ((original,a),(shadow,b)):
            with path.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=names)
                w.writeheader();w.writerows(records)
        assert len(read_csv(original,{'TBOT','TA_USE'}))==5
        assert sha(original)!=sha(shadow)
        assert abs(physics(a[2])[0]-24)<1e-8
        assert abs(physics(b[2])[0]-10)<1e-8
        assert {k for k in names if a[2][k]!=b[2][k]}==CHANGED
        assert a[2]['QBOT']==b[2]['QBOT']
    print('SELF-TEST PASS: synthetic shadow forcing, three-column changes and T/RH/VPD algebra')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--self-test',action='store_true')
    m.add_argument('--check',action='store_true')
    m.add_argument('--audit',action='store_true')
    p.add_argument('--stage68-dir',type=Path)
    p.add_argument('--stage61-dir',type=Path)
    p.add_argument('--experiment-root',type=Path,default=EXP)
    a=p.parse_args()
    if a.self_test:self_test();return
    if a.stage68_dir is None or a.stage61_dir is None:
        p.error('--stage68-dir and --stage61-dir required')
    s68=a.stage68_dir.resolve(strict=True)
    s61=a.stage61_dir.resolve(strict=True)
    result,manifest,original,shadow=review(s68,s61)
    present(result,manifest)
    if a.check:
        print('CHECK PASS: 262800 original/trial forcing rows independently compared; zero writes')
        return
    root=a.experiment_root.resolve(strict=True)/'reports'
    if not root.is_dir():raise RuntimeError('Missing report parent')
    out=root/('stage69_CA-Man_shadow_science_assessment_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output(out,result,manifest,original,shadow,s68,s61)

if __name__=='__main__':
    main()

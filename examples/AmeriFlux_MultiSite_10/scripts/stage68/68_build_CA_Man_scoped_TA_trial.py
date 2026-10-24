#!/usr/bin/env python3
"""Stage68 — first scoped CA-Man temperature repair TRIAL, never production.

Read-only --check finds 1–2-point QC1 gaps bounded on both sides by QC0
observations. --trial creates a *separate* temperature-only sensitivity
forcing CSV under a new stage68_* directory; original forcing is immutable.
For accepted patch points: update TBOT [K], TA_USE [C] and VPD_USE [hPa],
keep QBOT and all other variables unchanged; reject RH saturation violations.
Linear interpolation is only an explicit experimental hypothesis, not proof.
No automatic scientific approval, case update, DATM or job submission.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from itertools import zip_longest
from pathlib import Path

EXP=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
ORIGINAL_REL=(Path('stage54_era_vapour_2_candidate')/'CA-Man'/'forcing'/
              'processed_v7_era_vapour2'/'CA-Man_CLM_forcing_1994_2008.csv')
EXPECTED_ORIGINAL_SHA='fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705'
MODIFIABLE={'TBOT','TA_USE','VPD_USE'}
LEDGER_FIELDS=(
    'site','episode_id','timestamp','gap_count','left_QC0_time',
    'right_QC0_time','left_observed_T_C','right_observed_T_C',
    'original_TBOT_K','trial_TBOT_K','original_TA_USE_C','trial_TA_USE_C',
    'original_VPD_USE_hPa','trial_VPD_USE_hPa',
    'unchanged_QBOT_kg_kg','unchanged_PSRF_Pa',
    'original_RH_percent','trial_RH_percent','method',
    'science_status'
)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):
            h.update(part)
    return h.hexdigest()

def rows(path,required):
    if not path.is_file():
        raise RuntimeError('Missing report: '+str(path))
    with path.open(newline='',encoding='utf-8-sig') as f:
        r=csv.DictReader(f)
        cols=r.fieldnames or []
        if len(cols)!=len(set(cols)) or not set(required).issubset(cols):
            raise RuntimeError('Unexpected CSV fields: '+str(path)+' missing '+str(set(required)-set(cols)))
        return list(r)

def numeric(value):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (ValueError,TypeError):
        return None

def timestamp(value):
    return datetime.fromisoformat(value.strip())

def stamp(t):
    return t.strftime('%Y-%m-%d %H:%M:%S')

def source_qc(row):
    x=str(row.get('FLUXMET_TA_F_QC','')).strip()
    return x.removesuffix('.0')

def physics(temp_c,q,p):
    """Same water-vapour calculation as pinned Stage58; PSRF is Pa."""
    tk=temp_c+273.15
    if not 180<=tk<=340 or not 0<q<0.08 or not 49000<=p<=111000:
        raise ValueError('Out-of-range thermodynamic inputs')
    es=6.112*math.exp(17.67*temp_c/(temp_c+243.5))
    e=q*(p/100.0)/(0.622+0.378*q)
    rh=100*e/es
    vpd=es-e
    if not all(map(math.isfinite,(rh,vpd))) or rh<1 or rh>100.1 or vpd < -0.05:
        raise ValueError('RH/VPD trial violates physical hold gates')
    return rh,vpd

def get_reports(s61,s64,s67):
    m64=json.loads((s64/'manifest.json').read_text(encoding='utf-8'))
    m67=json.loads((s67/'manifest.json').read_text(encoding='utf-8'))
    if (m64.get('stage'),m64.get('P1_events'),m64.get('science_approved'))!=(64,96,False):
        raise RuntimeError('Stage64 manifest mismatch')
    if (m67.get('stage'),m67.get('event_count'),m67.get('science_approved'),
        m67.get('auto_repair'))!=(67,60,False,False):
        raise RuntimeError('Stage67 manifest mismatch')
    events=rows(s64/'all_96_transition_persistence.csv',
                {'site','episode_id','timestamp','QC_direction',
                 'post_QC_run_points_in_context','post_QC_run_reaches_context_edge'})
    native=rows(s67/'CA-Man_36_gapfill_boundaries.csv',
                {'site','episode_id','timestamp','QC_direction','native_evidence',
                 'native_before_agrees_with_FLUXMET_count_1C'})
    context=rows(s61/'P1_context_source_comparisons.csv',
                 {'site','episode_id','timestamp','candidate_TA_C','FLUXMET_TA_F_QC'})
    ca=[e for e in events if e['site']=='CA-Man' and e['QC_direction']=='0->1']
    if len(ca)!=36 or len(native)!=36:
        raise RuntimeError('Expected 36 CA-Man QC0->QC1 P1 source transitions')
    native_by={}
    for n in native:
        k=(n['site'],n['episode_id'])
        if k in native_by:raise RuntimeError('Duplicate Stage67 source event')
        native_by[k]=n
    context_by=defaultdict(dict)
    for r in context:
        k=(r['site'],r['episode_id'])
        t=timestamp(r['timestamp'])
        if t in context_by[k]:raise RuntimeError('Duplicate Stage61 context time')
        context_by[k][t]=r
    eligible=[]
    skips=Counter()
    for e in ca:
        k=(e['site'],e['episode_id'])
        n=native_by.get(k)
        if n is None or n['timestamp']!=e['timestamp'] or n['native_evidence']!='BASE_BEFORE_ONLY_GAPFILL_BOUNDARY':
            raise RuntimeError('Stage67 CA-Man provenance mismatch '+str(k))
        # Native before-side agreement is contextual evidence, not sensor identity.
        if int(n['native_before_agrees_with_FLUXMET_count_1C'])<1:
            skips['NO_NATIVE_BEFORE_ANCHOR_AGREEMENT']+=1;continue
        length=int(e['post_QC_run_points_in_context'])
        if length not in (1,2) or e['post_QC_run_reaches_context_edge'].lower()!='false':
            skips['UNBOUNDED_OR_LONGER_THAN_TWO_QC1']+=1;continue
        t=timestamp(e['timestamp'])
        c=context_by[k]
        left=t-timedelta(minutes=30)
        right=t+timedelta(minutes=30*length)
        times=[left]+[t+timedelta(minutes=30*i) for i in range(length)]+[right]
        if any(x not in c for x in times):
            skips['MISSING_30MIN_CONTEXT']+=1;continue
        if source_qc(c[left])!='0' or source_qc(c[right])!='0' or any(
                source_qc(c[x])!='1' for x in times[1:-1]):
            skips['NOT_QC0_QC1_QC0']+=1;continue
        lc=numeric(c[left]['candidate_TA_C']);rc=numeric(c[right]['candidate_TA_C'])
        if lc is None or rc is None:
            skips['ANCHOR_TEMPERATURE_MISSING']+=1;continue
        if abs(rc-lc)>3.0*(length+1):
            skips['ANCHOR_CHANGE_GT3C_PER_30MIN']+=1;continue
        eligible.append({'episode_id':e['episode_id'],'time':t,'length':length,
                         'left':left,'right':right,'left_c':lc,'right_c':rc,
                         'target_times':times[1:-1],
                         'expected_source_context':c})
    return eligible,skips

def build_plan(events, original):
    wanted=set()
    for e in events:
        wanted.update(e['target_times'])
        wanted.update((e['left'],e['right']))
    source={}
    with original.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        cols=reader.fieldnames or []
        required={'time','TBOT','TA_USE','QBOT','PSRF','VPD_USE'}
        if not required.issubset(cols) or len(cols)!=len(set(cols)):
            raise RuntimeError('Original forcing field schema mismatch')
        seen=set()
        for r in reader:
            t=timestamp(r['time'])
            if t in wanted:
                if t in seen:raise RuntimeError('Duplicate forcing timestamp '+stamp(t))
                seen.add(t);source[t]=r
    missing=wanted-set(source)
    if missing:
        raise RuntimeError('Missing required original forcing records: '+str(sorted(missing)[:5]))
    patches={}
    ledger=[]
    rejected=Counter()
    selected=[]
    for e in events:
        length=e['length'];lc=e['left_c'];rc=e['right_c']
        leftrow=source[e['left']];rightrow=source[e['right']]
        if any(abs(float(row['TBOT'])-273.15-val)>.02
               for row,val in ((leftrow,lc),(rightrow,rc))):
            rejected['ORIGINAL_ANCHORS_DIFFER_FROM_STAGE61']+=1;continue
        proposal=[];reason=None
        for i,t in enumerate(e['target_times'],1):
            old=source[t]
            expected=numeric(e['expected_source_context'][t]['candidate_TA_C'])
            temp0=numeric(old.get('TBOT'))
            q=numeric(old.get('QBOT'));p=numeric(old.get('PSRF'))
            if None in (expected,temp0,q,p) or abs(temp0-273.15-expected)>.02:
                reason='STAGE61_SOURCE_FORCING_MISMATCH';break
            tc=lc+(rc-lc)*i/(length+1)
            if abs(tc-(temp0-273.15))<4:
                reason='EDIT_BELOW4C_REVIEW_THRESHOLD';break
            if abs(tc-(temp0-273.15))>20:
                reason='EDIT_GT20C_REQUIRES_MANUAL_REVIEW';break
            try:
                rh0,_=physics(temp0-273.15,q,p)
                rh1,vpd=physics(tc,q,p)
            except ValueError:
                reason='QBOT_PSRF_RH_VPD_PHYSICS_HOLD';break
            new=dict(old)
            new['TBOT']=f'{tc+273.15:.6f}'
            new['TA_USE']=f'{tc:.6f}'
            new['VPD_USE']=f'{vpd:.6f}'
            if any(new[k]!=old[k] for k in cols_except(MODIFIABLE, old)):
                raise RuntimeError('Unexpected extra field change')
            proposal.append((t,new,{
                'site':'CA-Man','episode_id':e['episode_id'],
                'timestamp':stamp(t),'gap_count':length,
                'left_QC0_time':stamp(e['left']),'right_QC0_time':stamp(e['right']),
                'left_observed_T_C':lc,'right_observed_T_C':rc,
                'original_TBOT_K':old['TBOT'],'trial_TBOT_K':new['TBOT'],
                'original_TA_USE_C':old['TA_USE'],'trial_TA_USE_C':new['TA_USE'],
                'original_VPD_USE_hPa':old['VPD_USE'],
                'trial_VPD_USE_hPa':new['VPD_USE'],
                'unchanged_QBOT_kg_kg':old['QBOT'],
                'unchanged_PSRF_Pa':old['PSRF'],
                'original_RH_percent':round(rh0,5),'trial_RH_percent':round(rh1,5),
                'method':'QC0_BRACKET_LINEAR_TA_QBOT_FIXED_VPD_RECOMPUTED',
                'science_status':'SHADOW_SENSITIVITY_ONLY_NOT_APPROVED'
            }))
        if reason is not None:
            rejected[reason]+=1;continue
        if any(t in patches for t,_,_ in proposal):
            raise RuntimeError('Overlapping proposed patch times')
        for t,new,log in proposal:
            patches[t]=new;ledger.append(log)
        selected.append(e['episode_id'])
    return patches,ledger,selected,rejected

def cols_except(excluded,row):
    return (key for key in row if key not in excluded)

def write_trial(original, dest, patches):
    seen=set();n=0
    with original.open(newline='',encoding='utf-8-sig') as src, dest.open(
            'w',newline='',encoding='utf-8') as dst:
        reader=csv.DictReader(src)
        writer=csv.DictWriter(dst,fieldnames=reader.fieldnames,
                              lineterminator='\n',extrasaction='raise')
        writer.writeheader()
        for row in reader:
            n+=1;t=timestamp(row['time'])
            proposal=patches.get(t)
            if proposal is not None:
                seen.add(t)
                writer.writerow(proposal)
            else:
                writer.writerow(row)
    if seen!=set(patches):
        raise RuntimeError('Not all proposed patch timestamps were written')
    return n

def verify_exact_changes(original, trial, patches):
    seen=set();n=0
    with original.open(newline='',encoding='utf-8-sig') as a, trial.open(
            newline='',encoding='utf-8-sig') as b:
        old,new=csv.DictReader(a),csv.DictReader(b)
        if old.fieldnames!=new.fieldnames:
            raise RuntimeError('Trial schema changed')
        for r0,r1 in zip_longest(old,new):
            if r0 is None or r1 is None or r0['time']!=r1['time']:
                raise RuntimeError('Trial row count/order changed')
            n+=1;t=timestamp(r0['time'])
            differences={col for col in old.fieldnames if r0[col]!=r1[col]}
            if t in patches:
                if differences!=MODIFIABLE:
                    raise RuntimeError('Unexpected trial columns changed '+stamp(t)+' '+str(differences))
                seen.add(t)
            elif differences:
                raise RuntimeError('Non-target original forcing changed '+stamp(t))
    if seen!=set(patches):
        raise RuntimeError('Trial patch set mismatch')
    return n

def stage58_full_gate(original,trial,expected_edited_count):
    script=Path(__file__).resolve().parents[1]/'stage58'/'58_audit_selected_forcing_candidates.py'
    if not script.is_file():
        raise RuntimeError('Stage58 audit dependency missing: '+str(script))
    spec=importlib.util.spec_from_file_location('stage58_temp_trial_gate',str(script))
    if spec is None or spec.loader is None:
        raise RuntimeError('Cannot import Stage58 scanner')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    orig=module.scan(original,1994,2008);candidate=module.scan(trial,1994,2008)
    if orig['structural_gate']!='PASS_REVIEW_ONLY' or candidate['structural_gate']!='PASS_REVIEW_ONLY':
        raise RuntimeError('Original or trial Stage58 structural gate failed')
    if candidate['rows']!=orig['rows'] or candidate['rows']!=262800:
        raise RuntimeError('Unexpected row counts in Stage58 scan')
    f0=orig['flags'];f1=candidate['flags']
    for flag in ('rh_below1','rh_above100','nonfinite_rows','vpd_closure_warning',
                 'bad_calendar','invalid_humidity','leap_day'):
        if f1.get(flag,0)>f0.get(flag,0):
            raise RuntimeError('Trial introduced new '+flag)
    if f1.get('ta_step_over10C',0)>f0.get('ta_step_over10C',0):
        raise RuntimeError('Trial increases >10 C half-hour temperature steps')
    return orig,candidate

def self_test():
    assert physics(20,0.008,101325)[0]>0
    assert abs(physics(20,0.008,101325)[1]-
               (6.112*math.exp(17.67*20/(20+243.5))-0.008*1013.25/(0.622+0.378*0.008)))<1e-10
    with tempfile.TemporaryDirectory(prefix='stage68_unit_') as d:
        root=Path(d)
        original=root/'original.csv';trial=root/'trial.csv'
        fields=['time','TBOT','TA_USE','QBOT','PSRF','VPD_USE','FSDS']
        start=datetime(2001,1,1)
        data=[]
        for i in range(6):
            t=start+timedelta(minutes=30*i);tc=[10,10,24,10,10,10][i]
            v=physics(tc,.006,101325)[1]
            data.append({'time':stamp(t),'TBOT':str(tc+273.15),'TA_USE':str(tc),
                         'QBOT':'.006','PSRF':'101325','VPD_USE':str(v),'FSDS':'100'})
        with original.open('w',newline='') as out:
            w=csv.DictWriter(out,fieldnames=fields);w.writeheader();w.writerows(data)
        e={'episode_id':'demo','time':start+timedelta(minutes=60),
           'length':1,'left':start+timedelta(minutes=30),
           'right':start+timedelta(minutes=90),
           'left_c':10.,'right_c':10.,
           'target_times':[start+timedelta(minutes=60)],
           'expected_source_context':{start+timedelta(minutes=60):{'candidate_TA_C':'24'}}}
        patches,ledger,chosen,rejected=build_plan([e],original)
        assert len(patches)==1 and len(ledger)==1 and chosen==['demo'] and not rejected
        write_trial(original,trial,patches)
        assert verify_exact_changes(original,trial,patches)==6
        with trial.open() as stream:
            output=list(csv.DictReader(stream))
        assert abs(float(output[2]['TBOT'])-283.15)<1e-5
        assert output[2]['QBOT']=='.006' and output[2]['FSDS']=='100'
    print('SELF-TEST PASS: single QC1 gap, coupled TBOT/TA_USE/VPD, untouched QBOT and row-level verification')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--self-test',action='store_true')
    modes.add_argument('--check',action='store_true')
    modes.add_argument('--trial',action='store_true')
    p.add_argument('--stage61-dir',type=Path)
    p.add_argument('--stage64-dir',type=Path)
    p.add_argument('--stage67-dir',type=Path)
    p.add_argument('--experiment-root',type=Path,default=EXP)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if None in (a.stage61_dir,a.stage64_dir,a.stage67_dir):
        p.error('Provide exact Stage61, Stage64, Stage67 report paths')
    root=a.experiment_root.resolve(strict=True)
    original=root/ORIGINAL_REL
    if not original.is_file() or sha(original)!=EXPECTED_ORIGINAL_SHA:
        raise RuntimeError('STOP: original CA-Man forcing SHA is not the pinned Stage58 candidate')
    s61=a.stage61_dir.resolve(strict=True)
    s64=a.stage64_dir.resolve(strict=True)
    s67=a.stage67_dir.resolve(strict=True)
    events,skips=get_reports(s61,s64,s67)
    patches,ledger,chosen,rejected=build_plan(events,original)
    print('STAGE68 | CA-Man FIRST SCOPED TEMPERATURE REPAIR TRIAL')
    print('Pinned original SHA:',EXPECTED_ORIGINAL_SHA)
    print('CA-Man initial P1 QC0->QC1 source boundaries:',36)
    print('Within 1-2 QC1 observations and two QC0 anchors:',len(events))
    print('Skipped scientific gates:',dict(skips))
    print('Trial eligible EVENT IDs:',len(chosen))
    print('Proposed modified half-hour rows:',len(patches))
    print('Rejected from eligible:',dict(rejected))
    for row in ledger[:15]:
        print(' ',row['episode_id'],row['timestamp'],
              'original_T_C',row['original_TA_USE_C'],
              'trial_T_C',row['trial_TA_USE_C'],
              'original_RH',row['original_RH_percent'],
              'trial_RH',row['trial_RH_percent'])
    if a.check:
        print('CHECK PASS: original forcing unchanged; no candidate files created.')
        return
    if not ledger:
        print('NO ELIGIBLE TRIAL REPAIRS; original retained. No files written.')
        return
    reportdir=root/'reports'
    if not reportdir.is_dir():
        raise RuntimeError('Missing reports directory')
    out=reportdir/('stage68_CA-Man_shadow_TA_trial_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    trial=out/'CA-Man_CLM_forcing_1994_2008_TA_SHADOW_TRIAL_NOT_PRODUCTION.csv'
    row_count=write_trial(original,trial,patches)
    assert verify_exact_changes(original,trial,patches)==row_count
    original_gate,trial_gate=stage58_full_gate(original,trial,len(ledger))
    if sha(original)!=EXPECTED_ORIGINAL_SHA:
        raise RuntimeError('Original SHA changed unexpectedly')
    with (out/'scoped_temperature_trial_edit_ledger.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=LEDGER_FIELDS)
        writer.writeheader();writer.writerows(ledger)
    with (out/'manifest.json').open('w') as f:
        json.dump({
            'stage':68,'site':'CA-Man','purpose':'SCIENTIFIC_TEMPERATURE_SENSITIVITY_ONLY',
            'original_path':str(original),'original_sha256':sha(original),
            'trial_path':str(trial),'trial_sha256':sha(trial),
            'input_reports_sha256':{
                'Stage61_context':sha(s61/'P1_context_source_comparisons.csv'),
                'Stage64_events':sha(s64/'all_96_transition_persistence.csv'),
                'Stage67_CA-Man':sha(s67/'CA-Man_36_gapfill_boundaries.csv')},
            'target_event_ids':chosen,'modified_rows':len(ledger),
            'modified_fields':sorted(MODIFIABLE),'unmodified_fields':'ALL_OTHERS',
            'original_scanner':original_gate,
            'trial_scanner':trial_gate,'science_approved':False,
            'production_approved':False,'source_clock_verified':False,
            'original_forcing_modified':False,'auto_submitted_jobs':False,
            'warning':'One- or two-point QC1 interpolation is an exploratory alternative, not verified tower observation. Never use for production without manual approval and time/metadata validation.'
        },f,indent=2)
        f.write('\n')
    print('TRIAL REPORT:',out)
    print('Trial forcing:',trial)
    print('Original >10C steps:',original_gate['flags'].get('ta_step_over10C',0))
    print('Trial >10C steps:',trial_gate['flags'].get('ta_step_over10C',0))
    print('Only NEW shadow trial and ledger written; original forcing unchanged.')

if __name__=='__main__':
    main()

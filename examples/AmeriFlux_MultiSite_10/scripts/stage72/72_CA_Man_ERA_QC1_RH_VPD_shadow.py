#!/usr/bin/env python3
"""Stage72 — CA-Man ERA TA at isolated QC1 times: RH/VPD sensitivity + shadow.

This is a controlled experiment, NOT an approved meteorological correction.
Reads the Stage70B 36-event review and Stage61 source context. Stage71 showed
35 candidate points with <=10C entry and exit change; the remaining date,
2007-03-10 11:30, is deliberately held. Validate again using the original
SHA-pinned 262800-row forcing. --check performs all calculations, no writes.
--trial produces a NEW shadow CSV only for physical-gate passing rows, plus a
35-row diagnostics ledger, WITHOUT changing original forcing or model cases.
FLUXNET TA_ERA is NOT necessarily uncorrected native grid ERA5; alignment
and source independence are unverified. Do not submit jobs or approve repairs.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from itertools import zip_longest
from pathlib import Path

EXP=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
ORIGINAL_REL=Path('stage54_era_vapour_2_candidate/CA-Man/forcing/processed_v7_era_vapour2/CA-Man_CLM_forcing_1994_2008.csv')
ORIGINAL_SHA='fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705'
S61_NAME='P1_context_source_comparisons.csv'
S70_NAME='36_CA-Man_review_EDIT_DECISIONS_MANUALLY.csv'
HOLD=datetime(2007,3,10,11,30)
CHANGED={'TBOT','TA_USE','VPD_USE'}
FIELDS=[
    'site','episode_id','timestamp','stage70b_category',
    'original_T_C','ERA_candidate_T_C','delta_T_C',
    'original_T_before_C','original_T_after_C',
    'before_QC','after_QC','original_step_before_C','original_step_after_C',
    'ERA_step_before_C','ERA_step_after_C',
    'QBOT_original_kgkg','PSRF_original_Pa',
    'RH_original_pct','RH_fixedQ_ERA_pct','delta_RH_fixedQ_pp',
    'RH_before_pct','RH_after_pct',
    'RH_jump_entry_original_pp','RH_jump_exit_original_pp',
    'RH_jump_entry_trial_pp','RH_jump_exit_trial_pp',
    'VPD_original_hPa','VPD_fixedQ_ERA_hPa','delta_VPD_fixedQ_hPa',
    'VPD_before_hPa','VPD_after_hPa',
    'VPD_jump_entry_original_hPa','VPD_jump_exit_original_hPa',
    'VPD_jump_entry_trial_hPa','VPD_jump_exit_trial_hPa',
    'RH_preserving_QBOT_kgkg','RH_preserving_QBOT_pct_change',
    'VPD_preserving_QBOT_kgkg','VPD_preserving_QBOT_pct_change',
    'physics_gate','shadow_action','source_clock_verified',
    'source_independent','science_approved'
]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1048576),b''):
            h.update(part)
    return h.hexdigest()

def read_csv(path,needed):
    if not path.is_file():raise RuntimeError('Missing report: '+str(path))
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames or []
        if len(fields)!=len(set(fields)) or not set(needed).issubset(fields):
            raise RuntimeError('Unexpected CSV fields '+str(path)+': '+str(sorted(set(needed)-set(fields))))
        return list(reader)

def num(x):
    try:
        z=float(x)
        return z if math.isfinite(z) and z > -9990 else None
    except (TypeError,ValueError):
        return None

def when(s):
    return datetime.fromisoformat(str(s).strip())

def qc(s):
    return str(s or '').strip().removesuffix('.0')

def vapor_e(tc):
    return 6.112*math.exp(17.67*tc/(tc+243.5))

def state(tc,q,p):
    if not (180 < tc+273.15 < 340 and 0 < q < .08 and 49000 < p < 111000):
        raise ValueError('T/Q/P out-of-range')
    es=vapor_e(tc)
    ev=q*(p/100)/(.622+.378*q)
    rh=100*ev/es
    vpd=es-ev
    if not all(math.isfinite(v) for v in (rh,vpd)):
        raise ValueError('nonfinite thermo state')
    return rh,vpd,ev

def q_from_ev(ev,p):
    denominator=p/100-.378*ev
    if ev<=0 or denominator<=0:return None
    q=.622*ev/denominator
    return q if math.isfinite(q) else None

def derived_Q(target_T,old_RH,old_VPD,p):
    result=[]
    for ev in (vapor_e(target_T)*old_RH/100,
               vapor_e(target_T)-old_VPD):
        v=q_from_ev(ev,p)
        if v is None or not 0<v<.08:
            result.append(None)
            continue
        try:
            rh,vpd,_=state(target_T,v,p)
        except ValueError:
            result.append(None)
            continue
        result.append(v if 1<=rh<=100.1 and vpd>=-.05 else None)
    return result

def scan_context(stage61,events):
    raw=read_csv(stage61/S61_NAME,
                 {'site','episode_id','timestamp','candidate_TA_C',
                  'FLUXMET_TA_F_QC','ERA5_TA_ERA_C'})
    wanted={(e['site'],e['episode_id']) for e in events}
    contexts=defaultdict(dict)
    for r in raw:
        k=(r['site'],r['episode_id'])
        if k not in wanted:continue
        t=when(r['timestamp'])
        if t in contexts[k]:raise RuntimeError('Duplicate stage61 context row '+str(k))
        contexts[k][t]=r
    return contexts

def select(stage70b,stage61):
    report=read_csv(stage70b/S70_NAME,
                    {'site','episode_id','event_time','review_group',
                     'original_T_at_C','ERA5_T_at_C'})
    if len(report)!=36 or len({(r['site'],r['episode_id']) for r in report})!=36:
        raise RuntimeError('Expected exactly 36 distinct Stage70B cases')
    if any(x['site']!='CA-Man' for x in report):
        raise RuntimeError('Stage70B foreign site')
    ctx=scan_context(stage61,report)
    selected=[]
    held=[]
    for r in report:
        t=when(r['event_time'])
        d=ctx.get((r['site'],r['episode_id']),{})
        a,b=t-timedelta(minutes=30),t+timedelta(minutes=30)
        if not all(x in d for x in (a,t,b)):
            raise RuntimeError('Missing 3-point Stage61 context for '+r['episode_id'])
        if [qc(d[x]['FLUXMET_TA_F_QC']) for x in (a,t,b)]!=['0','1','0']:
            raise RuntimeError('Unexpected original QC0-QC1-QC0 around '+r['episode_id'])
        candidate=num(d[t]['ERA5_TA_ERA_C'])
        base=num(d[t]['candidate_TA_C'])
        prev=num(d[a]['candidate_TA_C']); nxt=num(d[b]['candidate_TA_C'])
        if None in (candidate,base,prev,nxt):
            raise RuntimeError('Missing temperature in 3-point source context')
        if abs(candidate-float(r['ERA5_T_at_C']))>.03 or abs(base-float(r['original_T_at_C']))>.03:
            raise RuntimeError('Stage61/70B temperature disagreement')
        before=abs(candidate-prev)
        after=abs(candidate-nxt)
        entry=(r,t,candidate,base,prev,nxt,d)
        if t==HOLD:
            if before<=10:raise RuntimeError('Special HOLD no longer fails 10C gate')
            held.append(entry)
        elif before<=10 and after<=10:
            selected.append(entry)
        else:
            held.append(entry)
    if len(selected)!=35 or len(held)!=1 or held[0][1]!=HOLD:
        raise RuntimeError('Stage71 35 passing + one date HOLD census changed')
    return selected,held

def original_cells(original,times):
    data={}
    with original.open(newline='',encoding='utf-8-sig') as f:
        rr=csv.DictReader(f)
        fields=rr.fieldnames or []
        required={'time','TBOT','TA_USE','QBOT','PSRF','VPD_USE','FSDS','FLDS','WIND','PRECTmms'}
        if len(fields)!=len(set(fields)) or not required.issubset(fields):
            raise RuntimeError('Original forcing column mismatch')
        for r in rr:
            t=when(r['time'])
            if t not in times:continue
            if t in data:raise RuntimeError('Duplicate forcing timestamp')
            data[t]=r
    if set(data)!=times:
        raise RuntimeError('Original forcing context times missing')
    return data

def validate_original_row(row,tc):
    t=num(row['TBOT'])
    tuv=num(row['TA_USE'])
    if t is None or tuv is None or abs(t-273.15-tc)>.03 or abs(t-273.15-tuv)>.03:
        raise RuntimeError('Original selected forcing TA mismatch Stage61')
    q=num(row['QBOT']);p=num(row['PSRF'])
    if q is None or p is None:raise RuntimeError('Invalid original Q/P')
    rh,vpd,_=state(tc,q,p)
    measured_vpd=num(row['VPD_USE'])
    if measured_vpd is None or abs(measured_vpd-vpd)>.03:
        raise RuntimeError('Original forcing VPD closure mismatch')
    return q,p,rh,vpd

def audit(selected,original):
    times={t+timedelta(minutes=30*i) for _,t,*_ in selected for i in (-1,0,1)}
    data=original_cells(original,times)
    results=[];patches={}
    for e,t,ref,orig,prev,nxt,ctx in selected:
        left=data[t-timedelta(minutes=30)]
        mid=data[t]
        right=data[t+timedelta(minutes=30)]
        validate_original_row(left,prev)
        q,p,old_rh,old_vpd=validate_original_row(mid,orig)
        validate_original_row(right,nxt)
        before_rh,before_vpd,_=state(prev,float(left['QBOT']),float(left['PSRF']))
        after_rh,after_vpd,_=state(nxt,float(right['QBOT']),float(right['PSRF']))
        try:
            fixed_rh,fixed_vpd,_=state(ref,q,p)
            physics='PASS' if 1<=fixed_rh<=100.1 and fixed_vpd>=-.05 else 'HOLD_NONPHYSICAL_RH_VPD'
        except ValueError:
            fixed_rh=fixed_vpd=None
            physics='HOLD_NONPHYSICAL_T_Q_P'
        qa,qb=derived_Q(ref,old_rh,old_vpd,p)
        approved=physics=='PASS'
        if approved:
            revised=dict(mid)
            revised['TBOT']=f'{ref+273.15:.6f}'
            revised['TA_USE']=f'{ref:.6f}'
            revised['VPD_USE']=f'{fixed_vpd:.6f}'
            if any(revised[k]!=mid[k] for k in mid if k not in CHANGED):
                raise RuntimeError('Unexpected shadow field modification')
            if {k for k in mid if revised[k]!=mid[k]}!=CHANGED:
                raise RuntimeError('Expected three changed forcing fields')
            patches[t]=revised
        results.append(dict(
            site='CA-Man',episode_id=e['episode_id'],timestamp=e['event_time'],
            stage70b_category=e['review_group'],original_T_C=round(orig,5),
            ERA_candidate_T_C=round(ref,5),delta_T_C=round(ref-orig,5),
            original_T_before_C=round(prev,5),original_T_after_C=round(nxt,5),
            before_QC='0',after_QC='0',
            original_step_before_C=round(abs(orig-prev),5),
            original_step_after_C=round(abs(orig-nxt),5),
            ERA_step_before_C=round(abs(ref-prev),5),
            ERA_step_after_C=round(abs(ref-nxt),5),
            QBOT_original_kgkg=mid['QBOT'],PSRF_original_Pa=mid['PSRF'],
            RH_original_pct=round(old_rh,5),
            RH_fixedQ_ERA_pct=round(fixed_rh,5) if fixed_rh is not None else '',
            delta_RH_fixedQ_pp=round(fixed_rh-old_rh,5) if fixed_rh is not None else '',
            RH_before_pct=round(before_rh,5),RH_after_pct=round(after_rh,5),
            RH_jump_entry_original_pp=round(abs(old_rh-before_rh),5),
            RH_jump_exit_original_pp=round(abs(old_rh-after_rh),5),
            RH_jump_entry_trial_pp=round(abs(fixed_rh-before_rh),5) if fixed_rh is not None else '',
            RH_jump_exit_trial_pp=round(abs(fixed_rh-after_rh),5) if fixed_rh is not None else '',
            VPD_original_hPa=round(old_vpd,5),
            VPD_fixedQ_ERA_hPa=round(fixed_vpd,5) if fixed_vpd is not None else '',
            delta_VPD_fixedQ_hPa=round(fixed_vpd-old_vpd,5) if fixed_vpd is not None else '',
            VPD_before_hPa=round(before_vpd,5),VPD_after_hPa=round(after_vpd,5),
            VPD_jump_entry_original_hPa=round(abs(old_vpd-before_vpd),5),
            VPD_jump_exit_original_hPa=round(abs(old_vpd-after_vpd),5),
            VPD_jump_entry_trial_hPa=round(abs(fixed_vpd-before_vpd),5) if fixed_vpd is not None else '',
            VPD_jump_exit_trial_hPa=round(abs(fixed_vpd-after_vpd),5) if fixed_vpd is not None else '',
            RH_preserving_QBOT_kgkg=round(qa,9) if qa is not None else '',
            RH_preserving_QBOT_pct_change=round(100*(qa-q)/q,4) if qa is not None else '',
            VPD_preserving_QBOT_kgkg=round(qb,9) if qb is not None else '',
            VPD_preserving_QBOT_pct_change=round(100*(qb-q)/q,4) if qb is not None else '',
            physics_gate=physics,
            shadow_action='SHADOW_FIXED_Q_ONLY_NOT_PRODUCTION' if approved else 'HOLD_NO_EDIT',
            source_clock_verified=False,source_independent=False,science_approved=False
        ))
    return results,patches

def write_shadow(original,destination,patches):
    seen=set();count=0
    with original.open(newline='',encoding='utf-8-sig') as inp,destination.open('w',newline='',encoding='utf-8') as out:
        reader=csv.DictReader(inp)
        writer=csv.DictWriter(out,fieldnames=reader.fieldnames,lineterminator='\n',extrasaction='raise')
        writer.writeheader()
        for r in reader:
            count+=1
            t=when(r['time'])
            if t in patches:
                writer.writerow(patches[t]);seen.add(t)
            else:
                writer.writerow(r)
    if seen!=set(patches) or count!=262800:
        raise RuntimeError('Shadow creation completeness failure')
    return count

def verify_shadow(original,trial,patches):
    seen=set();n=0
    with original.open(newline='',encoding='utf-8-sig') as fa,trial.open(newline='',encoding='utf-8-sig') as fb:
        a=csv.DictReader(fa);b=csv.DictReader(fb)
        if a.fieldnames!=b.fieldnames:raise RuntimeError('Shadow column/schema mismatch')
        for x,y in zip_longest(a,b):
            if x is None or y is None or x['time']!=y['time']:
                raise RuntimeError('Shadow row/time ordering differs')
            n+=1;t=when(x['time'])
            diff={k for k in x if x[k]!=y[k]}
            if t in patches:
                if diff!=CHANGED:raise RuntimeError('Unexpected shadow columns at '+x['time'])
                seen.add(t)
            elif diff:raise RuntimeError('Non-target forcing cell edited at '+x['time'])
    if n!=262800 or seen!=set(patches):raise RuntimeError('Shadow full row-level check failure')
    return n

def show(result):
    print('STAGE72 | 35 CA-Man isolated QC1 ERA temperature hypotheses | FIXED QBOT')
    print('35 of 36 events screen as temperature boundary continuous; 2007-03-10 remains HOLD.')
    print('Physical gates:',dict(Counter(x['physics_gate'] for x in result)))
    print('ERA shadow rows proposed:',sum(x['shadow_action'].startswith('SHADOW_') for x in result))
    print('RH change >=25pp:',sum(x['delta_RH_fixedQ_pp']!='' and abs(x['delta_RH_fixedQ_pp'])>=25 for x in result))
    print('Shadow RH <20%:',sum(x['RH_fixedQ_ERA_pct']!='' and x['RH_fixedQ_ERA_pct']<20 for x in result))
    print('VPD change >=10hPa:',sum(x['delta_VPD_fixedQ_hPa']!='' and abs(x['delta_VPD_fixedQ_hPa'])>=10 for x in result))
    print('RH-preserving QBOT change >=25%:',sum(x['RH_preserving_QBOT_pct_change']!='' and abs(x['RH_preserving_QBOT_pct_change'])>=25 for x in result))
    print('VPD-preserving QBOT change >=25%:',sum(x['VPD_preserving_QBOT_pct_change']!='' and abs(x['VPD_preserving_QBOT_pct_change'])>=25 for x in result))
    print(f"{'time':19} {'origT':>7} {'ERAT':>7} {'RH0':>7} {'RHera':>7} {'dRH':>7} {'VPD0':>7} {'VPDera':>7} {'Q_RHchg%':>9} {'Q_VPDchg%':>10} {'gate':>8}")
    for x in sorted(result,key=lambda e:e['timestamp']):
        def f(v,n=1):return f'{v:.{n}f}' if isinstance(v,(float,int)) else 'NA'
        print(f"{x['timestamp']:19} {f(x['original_T_C']):>7} {f(x['ERA_candidate_T_C']):>7} "
              f"{f(x['RH_original_pct']):>7} {f(x['RH_fixedQ_ERA_pct']):>7} "
              f"{f(x['delta_RH_fixedQ_pp']):>7} {f(x['VPD_original_hPa']):>7} "
              f"{f(x['VPD_fixedQ_ERA_hPa']):>7} "
              f"{f(x['RH_preserving_QBOT_pct_change']):>9} "
              f"{f(x['VPD_preserving_QBOT_pct_change']):>10} "
              f"{x['physics_gate']:>8}")
    print('SOURCE STATUS: unverified FLUXNET ERA clock; no scientific repair approvals')

def self_test():
    assert derived_Q(25,60,10,100000)[0] is not None
    q=.007;p=100000;t0=10;t1=20
    rh,vpd,_=state(t0,q,p)
    a,b=derived_Q(t1,rh,vpd,p)
    ar,av,_=state(t1,a,p);br,bv,_=state(t1,b,p)
    assert abs(ar-rh)<1e-8 and abs(bv-vpd)<1e-8
    assert state(10,.006,100000)[0]>0
    assert derived_Q(-30,60,25,p)[1] is None
    print('SELF-TEST PASS: fixed-Q RH/VPD, RH-preserving and VPD-preserving QBOT, physical HOLD')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--self-test',action='store_true')
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--trial',action='store_true')
    ap.add_argument('--experiment-root',type=Path,default=EXP)
    ap.add_argument('--stage61-dir',type=Path,default=EXP/'reports/stage61_P1_source_evidence_20261024T053231392029Z')
    ap.add_argument('--stage70b-dir',type=Path,default=EXP/'reports/stage70b_CA-Man_human_review_20261024T075415647388Z')
    a=ap.parse_args()
    if a.self_test:self_test();return
    root=a.experiment_root.resolve(strict=True)
    original=root/ORIGINAL_REL
    if not original.is_file() or sha(original)!=ORIGINAL_SHA:
        raise RuntimeError('Pinned Stage58 original CA-Man forcing SHA mismatch')
    s61=a.stage61_dir.resolve(strict=True)
    s70=a.stage70b_dir.resolve(strict=True)
    selected,held=select(s70,s61)
    results,patches=audit(selected,original)
    if len(results)!=35 or len(held)!=1:
        raise RuntimeError('Not all 35 ERA targets covered')
    show(results)
    if a.check:
        print('CHECK PASS: no files created; original forcing unchanged')
        return
    report=root/'reports'
    if not report.is_dir():raise RuntimeError('Missing report root')
    dest=report/('stage72_CA-Man_ERA_QC1_T_RH_VPD_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(exist_ok=False)
    with (dest/'35_event_ERA_RH_VPD_screen.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='raise')
        writer.writeheader();writer.writerows(results)
    if patches:
        trial=dest/'CA-Man_ERA_QC1_FIXEDQ_SHADOW_NOT_PRODUCTION.csv'
        write_shadow(original,trial,patches)
        verify_shadow(original,trial,patches)
        trial_digest=sha(trial)
    else:
        trial=None;trial_digest=None
    if sha(original)!=ORIGINAL_SHA:raise RuntimeError('Original CA-Man forcing changed unexpectedly')
    (dest/'manifest.json').write_text(json.dumps({
        'stage':72,'site':'CA-Man','candidate_events':35,'special_hold_event':'2007-03-10 11:30:00',
        'source_report_Stage61_sha256':sha(s61/S61_NAME),
        'review_Stage70B_sha256':sha(s70/S70_NAME),
        'original_forcing_path':str(original),'original_forcing_sha256':ORIGINAL_SHA,
        'shadow_path':str(trial) if trial else None,'shadow_sha256':trial_digest,
        'shadow_modified_rows':len(patches),'candidate_physics':dict(Counter(x['physics_gate'] for x in results)),
        'changed_columns':sorted(CHANGED),'unchanged_fields':['QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms'],
        'source_clock_verified':False,'source_independent':False,'science_approved':False,
        'production_approved':False,'original_forcing_modified':False,'jobs_submitted':False,
        'warnings':['This is a hypothetical FLUXNET TA_ERA substitution, not raw ERA5-Land.',
                    'Humidity impacts must be reviewed using independent observed RH/dewpoint/VPD.',
                    'A physically passing RH/VPD value does not prove a scientifically valid replacement.',
                    'Hold all physically invalid candidates and QC0 anchors.']
    },indent=2)+'\n',encoding='utf-8')
    print('REPORT:',dest)
    print('SHADOW:',trial if trial else 'NONE (no physics-passing candidate)')
    print('Trial rows modified:',len(patches))
    print('Original forcing unchanged; no job submitted')

if __name__=='__main__':main()

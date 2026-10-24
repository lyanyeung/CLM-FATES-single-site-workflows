#!/usr/bin/env python3
"""Stage70: non-writing T/Q/RH/VPD counterfactual comparison for CA-Man.

Uses all 34 Stage68 short bounded-gap QC1 episodes (19 fixed-Q trial cases
and 15 physically rejected fixed-Q cases). Never automatically approves a
moisture prescription or produces new forcing, DATM/CIME, or Slurm jobs.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

EXP=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
STAGE68_BLOB='900ca57172b80da2586125be408a51707117985b'
SCENARIOS=('FIXED_QBOT','PRESERVE_ORIGINAL_RH','PRESERVE_ORIGINAL_VPD')
FIELDS=('site','episode_id','timestamp','gap_length','original_T_C',
        'interpolated_T_C','scenario','original_QBOT_kgkg',
        'scenario_QBOT_kgkg','delta_QBOT_kgkg','QBOT_pct_change',
        'original_RH_pct','scenario_RH_pct','original_VPD_hPa',
        'scenario_VPD_hPa','source_FLUXMET_VPD_hPa_provisional',
        'source_ERA5_VPD_hPa_provisional','VPD_error_vs_FLUXMET_hPa_provisional',
        'VPD_error_vs_ERA5_hPa_provisional','physical_gate',
        'stage68_shadow_edit','science_approved','clock_verified',
        'independent_humidity_evidence_verified')

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1048576),b''):h.update(part)
    return h.hexdigest()

def read_csv(path,required):
    if not path.is_file():raise RuntimeError('Required input missing: '+str(path))
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        head=reader.fieldnames or []
        if len(head)!=len(set(head)) or not set(required).issubset(head):
            raise RuntimeError('Incorrect CSV columns: '+str(path)+' '+str(set(required)-set(head)))
        return list(reader)

def num(x):
    try:
        v=float(x)
        return v if math.isfinite(v) and v>-9990 else None
    except (ValueError,TypeError):return None

def es(tc):
    return 6.112*math.exp(17.67*tc/(tc+243.5))

def q_from_e(e,p):
    denom=p/100-.378*e
    return .622*e/denom if e>0 and denom>0 else None

def humidity(tc,q,p):
    vap=q*(p/100)/(.622+.378*q)
    return 100*vap/es(tc),es(tc)-vap,vap

def alternatives(told,tnew,q,p):
    rh0,vpd0,e0=humidity(told,q,p)
    targets=(q,q_from_e(es(tnew)*rh0/100,p),
             q_from_e(es(tnew)-vpd0,p))
    rows=[]
    for label,qn in zip(SCENARIOS,targets):
        if qn is None or not (0<qn<.08):
            rows.append((label,None,None,None,'REJECT_INVALID_QBOT_OR_VAPOUR'))
            continue
        rh,vpd,_=humidity(tnew,qn,p)
        state=('PASS_COUNTERFACTUAL_ONLY'
               if all(math.isfinite(v) for v in (rh,vpd)) and 1<=rh<=100.1 and vpd>=-.05
               else 'REJECT_RH_VPD_PHYSICAL')
        rows.append((label,qn,rh,vpd,state))
    return rh0,vpd0,rows

def stage68_module(path):
    raw=path.read_bytes()
    blob=b'blob '+str(len(raw)).encode()+b'\0'+raw
    if hashlib.sha1(blob).hexdigest()!=STAGE68_BLOB:
        raise RuntimeError('Stage68 local source does not match pinned GitHub blob')
    spec=importlib.util.spec_from_file_location('stage68_pinned_for_stage70',str(path))
    if spec is None or spec.loader is None:raise RuntimeError('Cannot load Stage68 script')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load(stage59,stage61,stage64,stage67,stage68,stage69,script):
    dirs=[stage59,stage61,stage64,stage67,stage68,stage69]
    for i,d in zip((59,61,64,67,68,69),dirs):
        m=json.loads((d/'manifest.json').read_text(encoding='utf-8'))
        expected='59' if i==59 else i
        if m.get('stage')!=expected:raise RuntimeError('Stage report mismatch: '+str(i)+'; observed '+repr(m.get('stage')))
    m68=json.loads((stage68/'manifest.json').read_text(encoding='utf-8'))
    m69=json.loads((stage69/'manifest.json').read_text(encoding='utf-8'))
    if (m68.get('modified_rows'),m68.get('science_approved'),
        m68.get('production_approved'))!=(19,False,False):
        raise RuntimeError('Stage68 trial science gate mismatch')
    if (m69.get('reviewed_shadow_edits'),m69.get('science_approved'),
        m69.get('production_approved'))!=(19,False,False):
        raise RuntimeError('Stage69 assessment science gate mismatch')
    if m69.get('input_sha256',{}).get('stage68_manifest')!=sha(stage68/'manifest.json'):
        raise RuntimeError('Stage69-to-68 manifest SHA mismatch')
    if m69.get('input_sha256',{}).get('stage68_ledger')!=sha(stage68/'scoped_temperature_trial_edit_ledger.csv'):
        raise RuntimeError('Stage69-to-68 ledger SHA mismatch')
    module=stage68_module(script)
    original=EXP/module.ORIGINAL_REL
    if not original.is_file() or sha(original)!=module.EXPECTED_ORIGINAL_SHA:
        raise RuntimeError('Stage58 pinned CA-Man original SHA mismatch')
    if sha(original)!=m68.get('original_sha256'):
        raise RuntimeError('Stage68 original file changed')
    events,skips=module.get_reports(stage61,stage64,stage67)
    if len(events)!=34 or skips.get('ANCHOR_CHANGE_GT3C_PER_30MIN')!=2:
        raise RuntimeError('Stage68 short-gap census changed')
    patches,ledger,selected,rejected=module.build_plan(events,original)
    if (len(patches),len(ledger),len(selected),
        rejected.get('QBOT_PSRF_RH_VPD_PHYSICS_HOLD'))!=(19,19,19,15):
        raise RuntimeError('Recomputed Stage68 case count differs')
    recorded=read_csv(stage68/'scoped_temperature_trial_edit_ledger.csv',
                      {'episode_id','timestamp'})
    if {(r['episode_id'],r['timestamp']) for r in recorded}!={(r['episode_id'],r['timestamp']) for r in ledger}:
        raise RuntimeError('Stage68 event ledger modified')
    source={}
    source_rows=read_csv(stage59/'bulk_temperature_review.csv',
                         {'site','timestamp','event_type','source_FLUXMET_VPD_F_hPa',
                          'source_ERA5_VPD_ERA_hPa'})
    for x in source_rows:
        if x['site']!='CA-Man' or x['event_type']!='TA_STEP_GT10':continue
        if x['timestamp'] in source:raise RuntimeError('Duplicate Stage59 event time')
        source[x['timestamp']]=x
    targets={t for e in events for t in e['target_times']}
    records={}
    with original.open(newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            t=module.timestamp(row['time'])
            if t in targets:
                if t in records:raise RuntimeError('Duplicate forcing time')
                records[t]=row
    if set(records)!=targets:raise RuntimeError('Forcing missing selected short-gap time')
    return events,records,source,set(selected),module.EXPECTED_ORIGINAL_SHA

def analyze(events,records,source,selected):
    result=[]
    for ev in events:
        n=ev['length']
        for i,t in enumerate(ev['target_times'],1):
            r=records[t]
            orig=float(r['TBOT'])-273.15
            q=float(r['QBOT']);p=float(r['PSRF'])
            trial=ev['left_c']+(ev['right_c']-ev['left_c'])*i/(n+1)
            expected=num(ev['expected_source_context'][t]['candidate_TA_C'])
            if expected is None or abs(orig-expected)>.02:
                raise RuntimeError('Forcing differs from Stage61 time context '+str(t))
            rh0,vpd0,options=alternatives(orig,trial,q,p)
            ref=source.get(t.strftime('%Y-%m-%d %H:%M:%S'),{})
            fv=num(ref.get('source_FLUXMET_VPD_F_hPa'))
            er=num(ref.get('source_ERA5_VPD_ERA_hPa'))
            for label,qn,rh1,vpd1,gate in options:
                result.append({
                   'site':'CA-Man','episode_id':ev['episode_id'],
                   'timestamp':t.strftime('%Y-%m-%d %H:%M:%S'),'gap_length':n,
                   'original_T_C':round(orig,5),'interpolated_T_C':round(trial,5),
                   'scenario':label,'original_QBOT_kgkg':q,
                   'scenario_QBOT_kgkg':round(qn,9) if qn is not None else '',
                   'delta_QBOT_kgkg':round(qn-q,9) if qn is not None else '',
                   'QBOT_pct_change':round(100*(qn-q)/q,4) if qn is not None else '',
                   'original_RH_pct':round(rh0,4),
                   'scenario_RH_pct':round(rh1,4) if rh1 is not None else '',
                   'original_VPD_hPa':round(vpd0,4),
                   'scenario_VPD_hPa':round(vpd1,4) if vpd1 is not None else '',
                   'source_FLUXMET_VPD_hPa_provisional':fv if fv is not None else '',
                   'source_ERA5_VPD_hPa_provisional':er if er is not None else '',
                   'VPD_error_vs_FLUXMET_hPa_provisional':round(abs(vpd1-fv),4) if fv is not None and vpd1 is not None else '',
                   'VPD_error_vs_ERA5_hPa_provisional':round(abs(vpd1-er),4) if er is not None and vpd1 is not None else '',
                   'physical_gate':gate,'stage68_shadow_edit':ev['episode_id'] in selected,
                   'science_approved':False,'clock_verified':False,
                   'independent_humidity_evidence_verified':False})
    return result

def report(result):
    print('STAGE70 | CA-MAN 34 QC1 GAP T/Q HYPOTHESES | NO FORCING WRITES')
    print('Event groups:',len({r['episode_id'] for r in result}),
          'half-hour records:',len({r['timestamp'] for r in result}),
          'counterfactual scenario rows:',len(result))
    for scenario in SCENARIOS:
        rr=[r for r in result if r['scenario']==scenario]
        print(' ',scenario,'pass=',sum(r['physical_gate']=='PASS_COUNTERFACTUAL_ONLY' for r in rr),
              'reject=',sum(r['physical_gate']!='PASS_COUNTERFACTUAL_ONLY' for r in rr),
              'QBOT change >=25%=',sum(r['QBOT_pct_change']!='' and abs(r['QBOT_pct_change'])>=25 for r in rr),
              'FLUXMET VPD contextual matches=',sum(r['source_FLUXMET_VPD_hPa_provisional']!='' for r in rr))
    print('Scientific gate: ALL COUNTERFACTUALS HOLD. No scenario approved by source data.')

def self_test():
    q=.006;p=101325
    rh0,vpd0,a=alternatives(10,24,q,p)
    assert len(a)==3
    assert abs(a[0][1]-q)<1e-12
    assert abs(a[1][2]-rh0)<1e-9
    assert abs(a[2][3]-vpd0)<1e-9
    for label,qnew,rh,vpd,gate in a:
        assert gate=='PASS_COUNTERFACTUAL_ONLY'
        vap=qnew*(p/100)/(.622+.378*qnew)
        assert abs(q_from_e(vap,p)-qnew)<1e-12
    assert alternatives(25,-30,q,p)[2][2][4].startswith('REJECT_')
    print('SELF-TEST PASS: exact Q conversion, RH/VPD-preserving counterfactuals and impossible vapour state')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    m=parser.add_mutually_exclusive_group(required=True)
    m.add_argument('--self-test',action='store_true')
    m.add_argument('--check',action='store_true')
    m.add_argument('--audit',action='store_true')
    for i in (59,61,64,67,68,69):parser.add_argument('--stage'+str(i)+'-dir',type=Path)
    parser.add_argument('--stage68-script',type=Path)
    parser.add_argument('--experiment-root',type=Path,default=EXP)
    a=parser.parse_args()
    if a.self_test:self_test();return
    inputs=[getattr(a,'stage'+str(i)+'_dir') for i in (59,61,64,67,68,69)]+[a.stage68_script]
    if any(v is None for v in inputs):parser.error('Provide Stage59/61/64/67/68/69 dirs and pinned --stage68-script')
    args=[x.resolve(strict=True) for x in inputs]
    events,records,source,selected,original_sha=load(*args)
    result=analyze(events,records,source,selected)
    report(result)
    if a.check:
        print('CHECK PASS: 0 writes, pinned original SHA validated')
        return
    root=a.experiment_root.resolve(strict=True)/'reports'
    if not root.is_dir():raise RuntimeError('Reports parent missing')
    out=root/('stage70_CA-Man_T_Q_hypotheses_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    def save(name,content):
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='raise')
            w.writeheader();w.writerows(content)
    save('all_joint_hypotheses.csv',result)
    for scenario in SCENARIOS:
        save(scenario+'.csv',[x for x in result if x['scenario']==scenario])
    receipt={'stage':70,'source_original_sha256':original_sha,
             'stage68_manifest_sha256':sha(args[4]/'manifest.json'),
             'stage69_manifest_sha256':sha(args[5]/'manifest.json'),
             'stage59_bulk_sha256':sha(args[0]/'bulk_temperature_review.csv'),
             'eligible_events':34,'stage68_shadow_events':19,
             'stage68_fixed_Q_physics_rejected':15,
             'counterfactual_rows':len(result),'science_approved':False,
             'original_forcing_modified':False,'shadow_forcing_modified':False,
             'new_forcing_created':False,'clock_verified':False,
             'independent_moisture_evidence_verified':False,
             'warning':'RH-preserving and VPD-preserving changes in QBOT are mathematical experiments, never automatically scientifically justified; source VPD values have provisional clocks and may share provenance.'}
    (out/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out)
    print('Only counterfactual CSV reports written. No forcing or Slurm changes.')

if __name__=='__main__':main()

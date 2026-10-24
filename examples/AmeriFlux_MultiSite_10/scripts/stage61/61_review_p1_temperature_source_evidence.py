#!/usr/bin/env python3
"""Stage61: read-only-input, P1 temperature source-evidence review for AmeriFlux Batch01.

Reads completed Stage59/Stage60 reports and original FLUXMET_HH/ERA5_HH data.
On --audit writes ONLY NEW versioned CSV/JSON reports; never repairs forcing.
Lag tests [-60,-30,0,+30,+60] minutes are diagnostic: neither the best
offset nor ERA5 is independent evidence of a bad tower observation.
Scientific status stays HOLD. Requires explicit --stage59-dir --stage60-dir.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_EXP=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
DEFAULT_RAW=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
LAGS=(-60,-30,0,30,60)
N_P1=96
EXPECTED_SITES={'BR-Ma2':0,'CA-Ca3':0,'CA-Cbo':7,'CA-LP1':11,'CA-Man':47,
                'CA-TP1':3,'CA-TP3':3,'CA-TP4':3,'US-Aud':2,'US-Bar':20}
EP_FIELDS=[
    'site','episode_id','start_time','end_time','step_flags',
    'rapid_reversal_step_flags','max_abs_step_C','review_category',
    'source_evidence','provisional_best_FLUXMET_lag_min',
    'provisional_lag_status','FLUXMET_TA_F_C','FLUXMET_TA_QC',
    'FLUXMET_delta30_C','ERA5_TA_ERA_C','ERA5_delta30_C',
    'candidate_delta30_C','step_agrees_with_FLUXMET',
    'step_agrees_with_ERA5','source_stamp_used',
    'priority','science_decision','next_action'
]
ALIGN_FIELDS=['site','offset_minutes','reference_context_rows','matched_rows',
              'median_abs_candidate_vs_FLUXMET_C','p90_abs_C','lag_status']
CONTEXT_FIELDS=['site','episode_id','timestamp','candidate_TA_C','candidate_RH_pct',
                'candidate_flagged_at_time','raw_timestamp_queried',
                'FLUXMET_TA_F_C','FLUXMET_TA_F_QC','ERA5_TA_ERA_C',
                'provisional_lag_minutes','lag_status']

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as fp:
        for block in iter(lambda:fp.read(1048576),b''):
            h.update(block)
    return h.hexdigest()

def num(value):
    try:
        x=float(value)
        return x if math.isfinite(x) and x > -9990 else None
    except (ValueError,TypeError):
        return None

def data_csv(path,required):
    if not path.is_file():
        raise RuntimeError('Missing input file: '+str(path))
    # Site manifests are TSV; Stage59/60 reports are ordinary CSV.
    delimiter='\t' if path.suffix.lower()=='.tsv' else ','
    with path.open(newline='',encoding='utf-8-sig') as fp:
        reader=csv.DictReader(fp,delimiter=delimiter)
        fields=reader.fieldnames or []
        if len(fields)!=len(set(fields)) or not set(required).issubset(fields):
            raise RuntimeError('Invalid CSV schema: '+str(path)+', missing='+str(set(required)-set(fields)))
        return list(reader)

def write_csv(path, rows, fields):
    with path.open('w',newline='',encoding='utf-8') as fp:
        writer=csv.DictWriter(fp,fieldnames=fields,extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

def canonical(t):
    return t.strftime('%Y%m%d%H%M')

def exact_ts(s):
    return datetime.fromisoformat(s.strip())

def source_path(raw,site,package,kind):
    d=raw/site/'forcing'/'raw'/package
    found=sorted(p for p in d.glob('*.csv') if kind in p.name.upper())
    if len(found)!=1:
        return None
    return found[0]

def selected_rows(path,wanted,fields):
    if path is None:
        return {}, 'MISSING_OR_AMBIGUOUS_FILE'
    ret={}
    with path.open(newline='',encoding='utf-8-sig') as fp:
        reader=csv.DictReader(fp)
        headers=reader.fieldnames or []
        if 'TIMESTAMP_START' not in headers or any(x not in headers for x in fields):
            return {}, 'MISSING_REQUIRED_COLUMNS'
        for row in reader:
            key=(row.get('TIMESTAMP_START') or '').strip().removesuffix('.0')
            if key in wanted:
                if key in ret:
                    raise RuntimeError('Duplicate raw timestamp '+str(path)+' '+key)
                ret[key]={field:row.get(field,'') for field in fields}
    return ret,'MATCHES_UNVERIFIED_CLOCK'

def read_inputs(args):
    s59=args.stage59_dir.resolve(strict=True)
    s60=args.stage60_dir.resolve(strict=True)
    manifest59=s59/'manifest.json'
    manifest60=s60/'manifest.json'
    for p in (manifest59,manifest60):
        if not p.is_file():
            raise RuntimeError('Missing manifest: '+str(p))
    m59=json.loads(manifest59.read_text(encoding='utf-8'))
    m60=json.loads(manifest60.read_text(encoding='utf-8'))
    if (m59.get('stage'),m59.get('ta_step_total'),m59.get('auto_repair_performed'))!=( '59', 422, False ):
        raise RuntimeError('Stage59 manifest mismatch')
    if (m60.get('stage'),m60.get('flags'),m60.get('auto_repair'))!=(60,422,False):
        raise RuntimeError('Stage60 manifest mismatch')
    if m60.get('rapid_reversal_step_flags')!=127 or m60.get('grouped_episodes')!=280:
        raise RuntimeError('Stage60 unexpected episode counts')
    p1=data_csv(s60/'prioritized_temperature_episodes.csv',
                ['site','episode_id','priority','start_time','end_time',
                 'largest_step_timestamp','rapid_reversal_step_flags','max_abs_step_C'])
    p1=[x for x in p1 if x['priority']=='P1_BATCH_REVIEW']
    if len(p1)!=N_P1:
        raise RuntimeError('Expected 96 P1 episodes, got '+str(len(p1)))
    totals=Counter(x['site'] for x in p1)
    if any(totals[site]!=value for site,value in EXPECTED_SITES.items()):
        raise RuntimeError('P1 site distribution changed: '+str(totals))
    if len(set((e['site'],e['episode_id']) for e in p1))!=len(p1):
        raise RuntimeError('Duplicate P1 episode IDs')
    steps=data_csv(s60/'temperature_step_provenance.csv',
                   ['site','episode_id','timestamp','delta_T_C','event_class'])
    by_event={(x['site'],x['timestamp']):x for x in steps}
    if len(steps)!=422 or len(by_event)!=422:
        raise RuntimeError('Expected 422 unique temperature-step flags')
    context=data_csv(s59/'event_context_4h.csv',
                     ['site','timestamp','temperature_C','RH_percent','flagged_at_time'])
    by_context={(x['site'],x['timestamp']):x for x in context}
    if len(by_context)!=len(context):
        raise RuntimeError('Duplicate Stage59 context timestamps')
    pinned=m59.get('selected_candidates',{})
    if set(pinned)!=set(EXPECTED_SITES):
        raise RuntimeError('Ten-site candidate provenance missing')
    meta=data_csv(args.sites_tsv,['site','package'])
    sites={row['site']:row for row in meta}
    if set(sites)!=set(EXPECTED_SITES):
        raise RuntimeError('Ten-site package manifest mismatch')
    return s59,s60,p1,by_event,by_context,sites,m59,m60

def lag_metrics(site,contexts,source):
    candidates=[]
    reference=[(t,num(row['temperature_C'])) for (s,t),row in contexts.items()
               if s==site and row.get('flagged_at_time')=='NO'
               and num(row.get('temperature_C')) is not None]
    for offset in LAGS:
        residuals=[]
        for stamp,value in reference:
            key=canonical(exact_ts(stamp)+timedelta(minutes=offset))
            obs=num(source.get(key,{}).get('TA_F'))
            if obs is not None:
                residuals.append(abs(value-obs))
        residuals.sort()
        med=statistics.median(residuals) if residuals else None
        p90=residuals[max(0,math.ceil(len(residuals)*0.9)-1)] if residuals else None
        candidates.append({'site':site,'offset_minutes':offset,
                           'reference_context_rows':len(reference),
                           'matched_rows':len(residuals),
                           'median_abs_candidate_vs_FLUXMET_C':round(med,4) if med is not None else '',
                           'p90_abs_C':round(p90,4) if p90 is not None else '',
                           'lag_status':'DIAGNOSTIC_UNVERIFIED'})
    valid=sorted((row for row in candidates if row['matched_rows']>=30),
                 key=lambda x:(x['median_abs_candidate_vs_FLUXMET_C'], -x['matched_rows']))
    best=None
    status='INSUFFICIENT_OR_MISSING_EVIDENCE'
    if valid:
        best=valid[0]['offset_minutes']
        if (len(valid)>1 and valid[0]['median_abs_candidate_vs_FLUXMET_C']<=1.5
            and valid[1]['median_abs_candidate_vs_FLUXMET_C']-valid[0]['median_abs_candidate_vs_FLUXMET_C']>=0.25):
            status='PROVISIONAL_DISTINCT_MINIMUM_NOT_VERIFIED'
        else:
            status='AMBIGUOUS_LAG_NOT_VERIFIED'
    for row in candidates:
        row['lag_status']=status
    return candidates,best,status

def build(args):
    s59,s60,p1,by_event,by_context,sites,m59,m60=read_inputs(args)
    sourceroot=args.raw_root.resolve(strict=True)
    e_records=[]
    align_records=[]
    ctx_records=[]
    raw_provenance={}
    p1.sort(key=lambda e:(e['site'],e['start_time']))
    groups=defaultdict(list)
    for e in p1:
        groups[e['site']].append(e)
    for site,episodes in sorted(groups.items()):
        # All Stage59 context points for this site are used for clock screening.
        # Raw source reads are streamed once per site, not per event.
        refs={exact_ts(t) for (s,t) in by_context if s==site}
        if not refs:
            raise RuntimeError('Missing candidate context for '+site)
        wanted={canonical(t+timedelta(minutes=m)) for t in refs for m in LAGS}
        pkg=sites[site]['package']
        fluxpath=source_path(sourceroot,site,pkg,'FLUXMET_HH')
        erapath=source_path(sourceroot,site,pkg,'ERA5_HH')
        flux,fstatus=selected_rows(fluxpath,wanted,('TA_F','TA_F_QC','VPD_F'))
        era,estatus=selected_rows(erapath,wanted,('TA_ERA','VPD_ERA'))
        raw_provenance[site]={
            'FLUXMET_HH':str(fluxpath) if fluxpath else 'NOT_FOUND_OR_AMBIGUOUS',
            'ERA5_HH':str(erapath) if erapath else 'NOT_FOUND_OR_AMBIGUOUS',
            'FLUXMET_status':fstatus,'ERA5_status':estatus,
            'FLUXMET_matched_rows':len(flux),'ERA5_matched_rows':len(era)
        }
        metrics,lag,status=lag_metrics(site,by_context,flux)
        align_records.extend(metrics)
        for ep in episodes:
            t=exact_ts(ep['largest_step_timestamp'])
            base=by_event.get((site,ep['largest_step_timestamp']))
            if base is None:
                raise RuntimeError('Missing largest flagged step: '+str((site,t)))
            lag_use=lag if status=='PROVISIONAL_DISTINCT_MINIMUM_NOT_VERIFIED' else None
            def srcval(raw,col,when):
                if lag_use is None: return None
                return num(raw.get(canonical(when+timedelta(minutes=lag_use)),{}).get(col))
            source_stamp=canonical(t+timedelta(minutes=lag_use)) if lag_use is not None else ''
            x1=srcval(flux,'TA_F',t)
            x0=srcval(flux,'TA_F',t-timedelta(minutes=30))
            y1=srcval(era,'TA_ERA',t)
            y0=srcval(era,'TA_ERA',t-timedelta(minutes=30))
            dx=x1-x0 if x1 is not None and x0 is not None else None
            dy=y1-y0 if y1 is not None and y0 is not None else None
            candidate_d=num(base.get('delta_T_C'))
            def concords(d):
                return (d is not None and candidate_d is not None and
                        candidate_d*d>0 and abs(d)>=0.7*abs(candidate_d))
            agrees_f=concords(dx)
            agrees_e=concords(dy)
            if lag_use is None:
                evidence='CLOCK_OFFSET_AMBIGUOUS_REQUIRES_REVIEW'
            elif dx is None:
                evidence='FLUXMET_SOURCE_CONTEXT_MISSING'
            elif agrees_f:
                evidence='FLUXMET_REPRODUCES_JUMP_PROVISIONAL'
            elif abs(dx)<3:
                evidence='CANDIDATE_JUMP_NOT_IN_FLUXMET_AT_TESTED_LAG'
            else:
                evidence='SOURCE_AND_CANDIDATE_MIXED'
            qc=flux.get(source_stamp,{}).get('TA_F_QC','') if source_stamp else ''
            record={
                'site':site,'episode_id':ep['episode_id'],
                'start_time':ep['start_time'],'end_time':ep['end_time'],
                'step_flags':ep['step_flags'],
                'rapid_reversal_step_flags':ep['rapid_reversal_step_flags'],
                'max_abs_step_C':ep['max_abs_step_C'],
                'review_category':ep.get('review_category',''),
                'source_evidence':evidence,
                'provisional_best_FLUXMET_lag_min':lag if lag is not None else '',
                'provisional_lag_status':status,
                'FLUXMET_TA_F_C':x1 if x1 is not None else '',
                'FLUXMET_TA_QC':qc,
                'FLUXMET_delta30_C':round(dx,4) if dx is not None else '',
                'ERA5_TA_ERA_C':y1 if y1 is not None else '',
                'ERA5_delta30_C':round(dy,4) if dy is not None else '',
                'candidate_delta30_C':candidate_d,
                'step_agrees_with_FLUXMET':'YES_PROVISIONAL' if agrees_f else 'NOT_SHOWN',
                'step_agrees_with_ERA5':'YES_PROVISIONAL' if agrees_e else 'NOT_SHOWN',
                'source_stamp_used':source_stamp,
                'priority':'P1_REVIEW_NOT_REPAIR',
                'science_decision':'HOLD_NOT_APPROVED',
                'next_action':'Check actual tower clock/sensor/QC and +/-4h context; compare true independent sources; no blanket ERA replacement'
            }
            e_records.append(record)
            start=exact_ts(ep['start_time'])-timedelta(hours=4)
            stop=exact_ts(ep['end_time'])+timedelta(hours=4)
            for (s,st),v in by_context.items():
                if s!=site: continue
                moment=exact_ts(st)
                if not start<=moment<=stop: continue
                rawkey=canonical(moment+timedelta(minutes=lag_use)) if lag_use is not None else ''
                q=flux.get(rawkey,{}) if rawkey else {}
                z=era.get(rawkey,{}) if rawkey else {}
                ctx_records.append({
                    'site':site,'episode_id':ep['episode_id'],'timestamp':st,
                    'candidate_TA_C':v['temperature_C'],'candidate_RH_pct':v['RH_percent'],
                    'candidate_flagged_at_time':v['flagged_at_time'],
                    'raw_timestamp_queried':rawkey,
                    'FLUXMET_TA_F_C':q.get('TA_F',''),'FLUXMET_TA_F_QC':q.get('TA_F_QC',''),
                    'ERA5_TA_ERA_C':z.get('TA_ERA',''),
                    'provisional_lag_minutes':lag_use if lag_use is not None else '',
                    'lag_status':status
                })
        print('SITE',site,'P1',len(episodes),'best_lag',lag,'status',status,
              'FLUXMET_matches',len(flux),'ERA_matches',len(era),flush=True)
    if len(e_records)!=N_P1:
        raise RuntimeError('Expected 96 P1 evidence rows')
    return s59,s60,e_records,align_records,ctx_records,raw_provenance

def self_test():
    """Test TSV/CSV input parsing and source-clock sensitivity without HPC files."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix='stage61_test_') as temporary:
        folder=Path(temporary)
        tsv=folder/'sites.tsv'
        tsv.write_text('site\tpackage\tfirst_year\tlast_year\n'
                       'CA-Man\tAMF_CA-Man_FLUXNET\t1994\t2008\n'
                       'US-Bar\tAMF_US-Bar_FLUXNET\t2004\t2023\n',
                       encoding='utf-8')
        parsed=data_csv(tsv,['site','package'])
        assert len(parsed)==2 and parsed[0]['site']=='CA-Man'
        assert parsed[1]['package']=='AMF_US-Bar_FLUXNET'
        csvp=folder/'review.csv'
        csvp.write_text('site,package\nCA-Man,example\n',encoding='utf-8')
        assert data_csv(csvp,['site','package'])[0]['package']=='example'
        context={}
        source={}
        zero=datetime(2018,1,1)
        for i in range(60):
            t=zero+timedelta(minutes=30*i)
            val=10+4*math.sin(i*0.3)
            context[('CA-Man',t.strftime('%Y-%m-%d %H:%M:%S'))]={
                'temperature_C':str(val),'flagged_at_time':'NO'}
            source[canonical(t)]={'TA_F':str(val)}
        rows,best,status=lag_metrics('CA-Man',context,source)
        assert len(rows)==5 and best==0
        assert status=='PROVISIONAL_DISTINCT_MINIMUM_NOT_VERIFIED'
    print('SELF-TEST PASS: TSV site manifest, CSV review and clock offsets')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--audit',action='store_true')
    mode.add_argument('--self-test',action='store_true')
    p.add_argument('--stage59-dir',type=Path)
    p.add_argument('--stage60-dir',type=Path)
    p.add_argument('--sites-tsv',type=Path,default=Path(__file__).resolve().parents[2]/'sites.tsv')
    p.add_argument('--raw-root',type=Path,default=DEFAULT_RAW)
    p.add_argument('--experiment-root',type=Path,default=DEFAULT_EXP)
    a=p.parse_args()
    if a.self_test:
        self_test()
        return
    if a.stage59_dir is None or a.stage60_dir is None:
        p.error('--stage59-dir and --stage60-dir are required for --check/--audit')
    root=a.experiment_root.resolve(strict=True)
    s59,s60,p1,steps,ctx,packages,m59,m60=read_inputs(a)
    print('STAGE61 P1 EVIDENCE | READ-ONLY INPUTS')
    print('Stage59:',s59)
    print('Stage60:',s60)
    print('P1 event groups:',len(p1),'across',len({x['site'] for x in p1}),'sites')
    if a.check:
        print('CHECK PASS: report inputs are consistent. No files created.')
        return
    s59,s60,evidence,alignment,context,provenance=build(a)
    root_reports=root/'reports'
    if not root_reports.is_dir(): raise RuntimeError('Missing experiment reports directory')
    target=root_reports/('stage61_P1_source_evidence_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    target.mkdir(exist_ok=False)
    write_csv(target/'P1_episode_source_evidence.csv',evidence,EP_FIELDS)
    write_csv(target/'FLUXMET_candidate_clock_offset_sensitivity.csv',alignment,ALIGN_FIELDS)
    write_csv(target/'P1_context_source_comparisons.csv',context,CONTEXT_FIELDS)
    receipt={
        'stage':61,'P1_event_groups':len(evidence),'science_approved':False,
        'auto_repair':False,'source_time_alignment_validated':False,
        'selected_inputs':{
            'stage59_dir':str(s59),'stage60_dir':str(s60),
            'stage59_manifest_sha256':sha(s59/'manifest.json'),
            'stage60_manifest_sha256':sha(s60/'manifest.json'),
            'stage59_context_sha256':sha(s59/'event_context_4h.csv'),
            'stage60_episode_sha256':sha(s60/'prioritized_temperature_episodes.csv'),
            'stage60_step_provenance_sha256':sha(s60/'temperature_step_provenance.csv')
        },
        'raw_inputs':provenance,
        'source_evidence_categories':dict(Counter(r['source_evidence'] for r in evidence)),
        'warnings':[
            'Best lag is diagnostic and must not be equated to verified tower timestamp alignment.',
            'FLUXMET and companion ERA5 may share reanalysis-derived content; corroboration is not independent.',
            'Source agreement/disagreement is not proof of a valid or invalid tower measurement.',
            'P1 priority and rapid reversal are not authorization to change forcing.'
        ]
    }
    (target/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',target)
    print('Only NEW report files written; NO source/forcing/DATM/CIME/PFT/Slurm changes.')

if __name__=='__main__':
    main()

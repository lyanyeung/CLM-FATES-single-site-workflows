#!/usr/bin/env python3
"""Read existing 05BM pairs; compare grid and selected correction. All HOLD."""
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PAIR_SHA = 'b9bafeed81f68f30512277baaad5fc20df584ea90174e1f52829aa72358b83e3'
LEDGER_SHA = 'bd36ee5d5f8297f4edd8a5c08562473e2110fe6da6354dbaaf0754aaa5ad434f'
OFFSETS = (510., 540., 566.092588, 570.)
SCOPES = {('TA','near','20050814'):44, ('TA','later','20050819'):44,
          ('LW_IN','later','20050910'):35}
BM_JST = {('TA','near'): (-.7543189772727236, .811104431818178),
          ('TA','later'): (.915345795454546, .915345795454546),
          ('LW_IN','later'): (-16.83639841269842,16.859061904761912)}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk)
    return h.hexdigest()

def check(path, expected):
    if path.is_symlink() or not path.is_file() or sha(path) != expected:
        raise ValueError('missing/symlink/input SHA mismatch: '+str(path))

def table(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f,delimiter='\t')
        if not r.fieldnames or len(set(r.fieldnames)) != len(r.fieldnames): raise ValueError('invalid TSV header')
        return list(r)

def values(row):
    try: vals = [float(row[k]) for k in ('source_QC0','grid_context','event_QC2_median',
                                          'grid_plus_event_median','prediction_minus_QC0')]
    except (ValueError, KeyError) as e: raise ValueError('invalid numeric pair') from e
    if not all(math.isfinite(x) for x in vals): raise ValueError('nonfinite pair')
    obs, grid, offset, corrected, error = vals
    if abs(grid+offset-corrected)>1e-8 or abs(corrected-obs-error)>1e-8:
        raise ValueError('pair arithmetic inconsistent')
    return vals

def calculate(rows):
    buckets=defaultdict(list); seen=set(); populations=defaultdict(set)
    for row in rows:
        var,phase,day=row['variable'],row['phase'],row['UTC_day']
        scope=(var,phase,day); clock=float(row['offset_minutes'])
        if row['site']!='JP-Tmd' or scope not in SCOPES or clock not in OFFSETS or row['status']!='CONTROL_OTHER_TIME_HOLD_NO_APPROVAL':
            raise ValueError('unexpected pair scope/status')
        native=datetime.strptime(row['native'],'%Y%m%d%H%M')
        key=(scope,clock,native)
        if key in seen: raise ValueError('duplicate control pair')
        seen.add(key); populations[(scope,clock)].add(native)
        obs,grid,offset,corrected,error=values(row)
        buckets[(scope,clock,'ALL')].append((obs,grid,offset,corrected))
        if 120 <= native.hour*60+native.minute < 240:
            buckets[(scope,clock,'NATIVE_0200_TO_BEFORE_0400')].append((obs,grid,offset,corrected))
    if len(rows)!=sum(SCOPES.values())*len(OFFSETS):raise ValueError('control row count')
    for scope,n in SCOPES.items():
        sets=[populations[(scope,c)] for c in OFFSETS]
        if any(len(s)!=n for s in sets) or any(s!=sets[0] for s in sets[1:]):raise ValueError('clock sample alignment')
    result=[]
    for scope in sorted(SCOPES):
        for clock in OFFSETS:
            for subset in ('ALL','NATIVE_0200_TO_BEFORE_0400'):
                data=buckets[(scope,clock,subset)]
                item={'variable':scope[0], 'phase':scope[1], 'utc_day':scope[2],
                      'offset_minutes':clock,'subset':subset,'n':len(data)}
                if data:
                    if max(x[2] for x in data)-min(x[2] for x in data)>1e-8:raise ValueError('background varies within group')
                    raw=[g-o for o,g,b,c in data]; corrected=[c-o for o,g,b,c in data]
                    item.update({'event_QC2_minus_grid_median':data[0][2],
                        'grid_mean_error':statistics.mean(raw),
                        'grid_mae':statistics.mean(abs(x) for x in raw),
                        'selected_mean_error':statistics.mean(corrected),
                        'selected_mae':statistics.mean(abs(x) for x in corrected),
                        'selected_minus_grid_mae':statistics.mean(abs(x) for x in corrected)-statistics.mean(abs(x) for x in raw),
                        'control_median_QC0_minus_grid_DESCRIPTIVE':statistics.median(-x for x in raw)})
                    if clock==540. and subset=='ALL':
                        mean,mae=BM_JST[(scope[0],scope[1])]
                        if abs(item['selected_mean_error']-mean)>1e-8 or abs(item['selected_mae']-mae)>1e-8:
                            raise ValueError('mismatch with operator BM summary')
                else:
                    item.update({k:'' for k in ('event_QC2_minus_grid_median','grid_mean_error','grid_mae',
                        'selected_mean_error','selected_mae','selected_minus_grid_mae','control_median_QC0_minus_grid_DESCRIPTIVE')})
                item['status']='POST_HOC_NON_EVENT_DESCRIPTIVE_ALL_HOLD'
                result.append(item)
    return result

def selftest():
    x={'source_QC0':'300','grid_context':'280','event_QC2_median':'6',
       'grid_plus_event_median':'286','prediction_minus_QC0':'-14'}
    assert values(x)==[300.,280.,6.,286.,-14.]
    x['prediction_minus_QC0']='-13'
    try: values(x)
    except ValueError: pass
    else: raise AssertionError('arithmetic tampering accepted')
    print('STAGE05BN SELF-TEST PASS; POST-HOC CONTROL DIAGNOSTICS; ALL HOLD')

def run(pairs,ledger,out):
    for p,h in ((pairs,PAIR_SHA),(ledger,LEDGER_SHA)):check(p,h)
    selected=table(ledger)
    if len(selected)!=45 or any(r['status']!='HOLD_NO_APPROVED_REPLACEMENT' or r['method']!='GRID_PLUS_SAME_RELEASE_QC2_MEDIAN' for r in selected):
        raise ValueError('selected ledger/HOLD mismatch')
    records=calculate(table(pairs))
    base=Path.home()/'japanflux_stage05bn'
    if base.is_symlink() or (base.exists() and not base.is_dir()) or out.parent.resolve()!=base.resolve() or out.exists() or out.is_symlink():
        raise ValueError('fresh ~/japanflux_stage05bn child required')
    for p,h in ((pairs,PAIR_SHA),(ledger,LEDGER_SHA)):check(p,h)
    base.mkdir(exist_ok=True);out.mkdir()
    path=out/'control_grid_vs_selected_posthoc_HOLD.tsv'
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,records[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(records)
    report={'status':'POST_HOC_CONTROL_ONLY_ALL_45_HOLD','approved_values':0,
        'input_pairs_sha256':PAIR_SHA,'selected_ledger_sha256':LEDGER_SHA,'output_sha256':sha(path),
        'limits':'Controls are other times; selected offset fixed from event QC2. Post-hoc subset is not event truth, uncertainty, method selection, or approval.',
        'CDS_requests':0,'original_zip_forcing_pft_soil_model_slurm_modified':False}
    with (out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print('STAGE05BN COMPLETE; POST-HOC CONTROL ONLY; ALL 45 HOLD; ZERO APPROVED')
    print('OUTPUT',out);print(json.dumps(report,indent=2))
    print('CONTROL_GRID_VS_SELECTED_TSV')
    with path.open(encoding='utf-8') as f:print(f.read(),end='')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    for name in ('pairs','ledger','out'):p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(getattr(a,n) is None for n in ('pairs','ledger','out')):p.error('pairs, ledger and out are required')
    run(a.pairs,a.ledger,a.out)
if __name__=='__main__':main()

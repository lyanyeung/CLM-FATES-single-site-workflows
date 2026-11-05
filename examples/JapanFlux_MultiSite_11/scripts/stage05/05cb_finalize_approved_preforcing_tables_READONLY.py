#!/usr/bin/env python3
"""Stage05CB: final pre-forcing tables after the user approved every Stage05BZ proposal (2026-11-05). Read-only.

Reads the twelve Stage05BZ tables and the approval list (SHA-256 pinned; byte-identical locally and on IRIDIS6),
rewrites each 'PROPOSED_<rule>_NOT_APPROVED|...' tag as 'APPROVED_20261105_<rule>|...' without touching any value,
and requires that no HOLD or NOT_APPROVED tag remains and that the number of rewritten cells equals the approval list.
Tom keeps its 2011-2013 rows (values unchanged) but its approved forcing period is 1999-2010 (rule D3b).
Also reports, per table and year, the cells that are missing or non-numeric, so the DATM builder can choose complete
years. Writes nothing to forcing, cases, Slurm or sources.
"""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

BZ_PIN=('05bz_proposed_resolution_of_hold_cells_READONLY.py','8ef4b3826383005e16304f4447fce5648b1900da1bba68afeba5b8dbaf34ebbc')
BZ_TABLES={'JP-Api':'2f79636b3cb23329f8b0f1ffc6fe5517a2bd51e511ae45d7735fa7f3c2dfed40','JP-Fhk':'b1a7a0b870140016721c0a1f3cc8b87575ddf1903e159bc6495e2a5bc4ce8bcb',
 'JP-Fjy':'38178a91ec4071da5b5fd15c4aa37ca32d7c1ac7354e4ba37c60983f6a18ddc2','JP-Khw':'02644b0f8bb241ef2ada30d7071ae670d9512ef25698e645a2bede85cb07b30a',
 'JP-Spp':'b82bb289f4635b0c92ca8c872ca8e1f407be24285e40d859f36d50b3f167745e','JP-Tak':'60fd58d0203e9da65e9b6c38baecf5d3127bdc1d130bd4130d91aac4927f88f1',
 'JP-Tef':'f87f7a989c9abd364f9d6e5566782648d2904daecdbe1c01ca8ff3dcc1ec5ef9','JP-Tmd':'0c7fc79810cf9ad1669083eba6032fdccc9e17d68f7752494d2cec2c1917def1',
 'JP-Yms':'c6a5c095624cc2f4780d9e037f943bab887adfab640a3ed25143aca039e13a94','JP-Tgf_HH':'f83c20bf606294ffc8549494023e8f84653e9ddcb6dc785dcec95a1ca8987ad9',
 'JP-Tom_HH':'561c392baad933a42485af465072aa4902b7b0e9cf887e0c3e1cf80c87a9a353','JP-Tom_HR':'59fba16a38dad2afd3da28bb782335873ff0b235610e71026299ee35de75dc29'}
APPROVAL_LIST_SHA='5a7d855167097014f9ff97de61ed579e4ea995e7ac50854905cd4af881af4b9e'
APPROVAL_LIST_ROWS=145855
APPROVED='APPROVED_20261105_'
FORCING_PERIOD={'JP-Tom':(1999,2010)}

def load_bz():
    name,expected=BZ_PIN;path=Path(__file__).with_name(name)
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 05BZ hash mismatch')
    spec=importlib.util.spec_from_file_location('stage05bz',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
bz=load_bz();br=bz.br;bw=bz.bw;num=br.num;finite=br.finite

def approve(tag):
    """'PROPOSED_<rule>_NOT_APPROVED|<history>' -> 'APPROVED_20261105_<rule>|<history>'; other tags unchanged."""
    if not tag.startswith('PROPOSED_'):return tag,False
    head,_,history=tag.partition('|')
    if not head.endswith('_NOT_APPROVED'):raise ValueError('malformed proposal tag '+tag)
    return APPROVED+head[len('PROPOSED_'):-len('_NOT_APPROVED')]+('|'+history if history else ''),True

def finalize(rows):
    n=0
    for r in rows:
        for c in range(3,len(r),3):
            r[c],changed=approve(r[c]);n+=changed
            if 'HOLD' in r[c].split('|')[0] or 'NOT_APPROVED' in r[c]:raise ValueError('unresolved tag '+r[c])
    return n

def missing_by_year(variables,rows):
    out=defaultdict(Counter)
    for r in rows:
        for i,v in enumerate(variables):
            if not finite(num(r[1+3*i])):out[r[0][:4]][v]+=1
    return {y:dict(sorted(c.items())) for y,c in sorted(out.items())}

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    br.check(a.bz_dir/'approval_list_NOT_APPROVED.tsv',APPROVAL_LIST_SHA)
    with (a.bz_dir/'approval_list_NOT_APPROVED.tsv').open(encoding='utf-8',newline='') as f:listed=sum(1 for _ in f)-1
    if listed!=APPROVAL_LIST_ROWS:raise ValueError('approval list rows')
    a.out.mkdir();report={'stage':'05CB','status':'FINAL_PREFORCING_TABLES_APPROVED_20261105_NO_FORCING_WRITTEN',
        'approval':'user approved all Stage05BZ proposals on 2026-11-05; D1/D2 approved and clock decisions delegated on 2026-11-04',
        'approval_list_sha256':APPROVAL_LIST_SHA,'forcing_period_overrides':{k:list(v) for k,v in FORCING_PERIOD.items()},'tables':{}}
    total=0
    for key,expected in BZ_TABLES.items():
        print('STAGE05CB',key,flush=True)
        header,variables,rows=bz.read_table(a.bz_dir/(key+'_proposed_NOT_APPROVED.tsv.gz'),expected)
        values=[[r[c] for c in range(len(r)) if (c-3)%3] for r in rows]
        n=finalize(rows);total+=n
        if values!=[[r[c] for c in range(len(r)) if (c-3)%3] for r in rows]:raise ValueError('a value changed while finalizing '+key)
        w=bw.Writer(a.out/(key+'_final_preforcing_APPROVED_20261105.tsv.gz'),header)
        for r in rows:w.line(r)
        digest,m=w.close()
        report['tables'][key]={'rows':m,'first':rows[0][0],'last':rows[-1][0],'uncompressed_tsv_sha256':digest,'approved_cells':n,
            'missing_or_nonnumeric_by_year':missing_by_year(variables,rows),
            'approved_tag_counts':dict(sorted(Counter(r[c].split('|')[0] for r in rows for c in range(3,len(r),3) if r[c].startswith(APPROVED)).items()))}
    if total!=APPROVAL_LIST_ROWS:raise ValueError('approved cells %d != approval list %d'%(total,APPROVAL_LIST_ROWS))
    report['approved_cells_total']=total;report['fingerprint_integers_strings']=br.fingerprint(report)
    with (a.out/'summary_APPROVED_20261105.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE05CB COMPLETE; FINAL PRE-FORCING TABLES; NO FORCING WRITTEN');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'approved_cells_total':total,
        'missing_by_table':{k:{y:c for y,c in v['missing_or_nonnumeric_by_year'].items()} for k,v in report['tables'].items() if v['missing_or_nonnumeric_by_year']}},indent=1))

def selftest():
    assert approve('PROPOSED_D7_WS_ERA_T_PLUS_1H_NOT_APPROVED|HOLD_D7_WS_STUCK')==('APPROVED_20261105_D7_WS_ERA_T_PLUS_1H|HOLD_D7_WS_STUCK',True)
    assert approve('C3_QC2_ERA_SHIFTM60')==('C3_QC2_ERA_SHIFTM60',False)
    rows=[['t','1','0','PROPOSED_D6_GAUGE_SPIKE_ZERO_NOT_APPROVED|HOLD_D6_SPP_GAUGE_SPIKE']];assert finalize(rows)==1
    try:finalize([['t','1','0','HOLD_D7_WS_STUCK']])
    except ValueError:pass
    else:raise AssertionError('HOLD accepted')
    print('STAGE05CB SELF-TEST PASS; APPROVAL TAGGING ONLY; VALUES UNCHANGED')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--bz-dir',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if a.bz_dir is None or a.out is None:p.error('--bz-dir and --out required')
    run(a)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Stage06J: final pre-forcing tables after the user approved Stage06I G2A/G2B and G1/R (2026-11-06). Read-only.

Inputs (SHA-256 pinned): the twelve Stage06E tables (byte-identical in both IRIDIS6 Stage06G runs) and the nine
Stage06I proposal tables and approval list as corrected on 2026-11-07. The Stage06G version wrote the 2,948 proposed TA
values as 'np.float64(x)' text, which the Stage06A guard read as missing; the corrected version has the same rows,
cells, rules and episodes with the same numbers written plainly.
  G2A short TA faults and G2B gap-fill departures: every leading 'PROPOSED_G2<rule>_NOT_APPROVED' segment of a tag
      becomes 'APPROVED_20261106_G2<rule>'; values are not touched.
  G1 (Tgf forcing years 2004-2022) and R (other TA departures kept as measured) change no table value; Stage06K
      applies them when building the forcing.
Checks, cell by cell: replaying the approval list on Stage06E (old value, old tag, new value, rule, in list order)
gives exactly the proposed cell, every list row is used once, every other cell (value, QC, tag) equals Stage06E, and
no proposal or HOLD tag remains. The tables without proposals (Fhk, Tom) are copied byte for byte. All twelve are
written under one name to a brand-new directory. Writes nothing to forcing, cases, Slurm or sources.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

F_PIN=('06f_build_approved_utc_noleap_datm_GUARDED.py','b974671f5f5dcc7a1e87a1f7c0403086839807a5de785fb8d8a76e6ed17b7f40')
# Stage06I as corrected 2026-11-07 (TA values written as plain numbers; cells, rules and episodes unchanged)
G2_TABLES={'JP-Api':'dfb07a34dbc797d40aa357e631dcf62b4684547010fd1e486dcca1db6c144997','JP-Fjy':'479aba56e73048782b5f06d40e794a147ec27be61a2bd974c6ee29abbe416d72',
 'JP-Khw':'5c069a79f886d832a274e2b2302544b2fb7176522e08f78372618584ab2bb41a','JP-Spp':'136c89cf56c7637d519640a93d6e8bd2ee79da9821e69376a97859ecf2246fff',
 'JP-Tak':'9476a772db9e8e7ead29d3439c941611993bfd86de4313aaba3fbfd693b81013','JP-Tef':'f1220e07dd0a7ff7ba28105c3609a002555822b9c70854f34fe365408423629b',
 'JP-Tgf_HH':'0fa3bad27ac6f0df31d38984c90ac25b42be4f32537138983796fd0b8374a396','JP-Tmd':'bef36270641ba7e730d3d6a09324ff9b8654000e48e47cbcb916f719ac1aaa6e',
 'JP-Yms':'064e74d103c8ac562f8fecba90dad04c8b864d8237d23c1823008b48c985ec9e'}
G2_LIST='approval_list_G2_NOT_APPROVED.tsv'
G2_LIST_SHA='170cea394b5f8af37e104d3f80a7657ca86c9e7a316184f2119f1c68872663f8'
G2_LIST_ROWS=5904
APPROVED='APPROVED_20261106_'
TABLE_NAME='{}_final_preforcing_APPROVED_20261106_G2.tsv.gz'

def load_f6():
    name,expected=F_PIN;path=Path(__file__).with_name(name)
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 06F script missing or hash mismatch')
    spec=importlib.util.spec_from_file_location('stage06f_for_06j',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f6=load_f6();cb=f6.a6.cb;bz=cb.bz;br=bz.br;bw=bz.bw

def approve(tag):
    """Leading 'PROPOSED_G2<rule>_NOT_APPROVED' segments -> 'APPROVED_20261106_G2<rule>'; returns (tag, segments rewritten)."""
    parts=tag.split('|');n=0
    while n<len(parts) and parts[n].startswith('PROPOSED_G2'):
        if not parts[n].endswith('_NOT_APPROVED'):raise ValueError('malformed proposal tag '+tag)
        parts[n]=APPROVED+parts[n][len('PROPOSED_'):-len('_NOT_APPROVED')];n+=1
    return '|'.join(parts),n

def replay(base,chain):
    """06E (value, tag) and the approval-list rows of one cell, in list order -> expected (value, tag) after Stage06I."""
    value,tag=base
    for old,new,rule,old_tag in chain:
        if old!=value or old_tag!=tag:raise ValueError('approval list does not follow the cell history')
        value,tag=new,'PROPOSED_'+rule+'_NOT_APPROVED|'+tag
    return value,tag

def finalize_table(key,variables,rows,base,cells):
    """rows: Stage06I table; base: Stage06E rows; cells: {(variable, time): [(old, new, rule, old tag)]} for this table.
    Checks rows against base and cells, approves in place and returns (approved cells, approved segments)."""
    if [r[0] for r in rows]!=[r[0] for r in base]:raise ValueError('time axis differs from 06E '+key)
    used=0;segments=0
    for r,b in zip(rows,base):
        for j,v in enumerate(variables):
            c=1+3*j;chain=cells.get((v,r[0]))
            if chain is None:
                if r[c:c+3]!=b[c:c+3]:raise ValueError('cell changed without a proposal %s %s %s'%(key,v,r[0]))
                continue
            if r[c+1]!=b[c+1] or (r[c],r[c+2])!=replay((b[c],b[c+2]),chain):raise ValueError('proposed cell differs from the approval list %s %s %s'%(key,v,r[0]))
            if not math.isfinite(br.num(r[c])):raise ValueError('approved value is not a finite number %s %s %s %r'%(key,v,r[0],r[c]))
            r[c+2],n=approve(r[c+2])
            if n!=len(chain):raise ValueError('tag segments %d != list rows %d %s %s %s'%(n,len(chain),key,v,r[0]))
            used+=1;segments+=n
    if used!=len(cells):raise ValueError('approval-list cells not found in '+key)
    if cb.finalize(rows):raise ValueError('a proposal tag survived approval in '+key)
    return used,segments

def read_list(path):
    br.check(path,G2_LIST_SHA);cells=defaultdict(lambda:defaultdict(list));rules=defaultdict(Counter);n=0
    with path.open(encoding='utf-8',newline='') as f:
        r=csv.reader(f,delimiter='\t')
        if next(r)[:7]!=['table','variable','native_start','value_in_06E','proposed_value','rule','06E_tag']:raise ValueError('approval list header')
        for key,v,t,old,new,rule,old_tag,*_ in r:cells[key][(v,t)].append((old,new,rule,old_tag));rules[key][v+'|'+rule]+=1;n+=1
    if n!=G2_LIST_ROWS or set(cells)!=set(G2_TABLES):raise ValueError('approval list rows or tables')
    return cells,rules

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    cells,rules=read_list(a.g2_dir/G2_LIST)
    a.out.mkdir();report={'stage':'06J','status':'FINAL_PREFORCING_TABLES_APPROVED_20261106_G2_NO_FORCING_WRITTEN',
        'approval':'user approved Stage06I G2A and G2B, G1 (Tgf forcing years 2004-2022) and R (other TA departures kept) on 2026-11-06',
        'approval_list_sha256':G2_LIST_SHA,'tables':{}}
    total=0
    for key,expected in f6.TABLES.items():
        print('STAGE06J',key,flush=True);src=a.e_dir/f6.TABLE_NAME.format(key);dst=a.out/TABLE_NAME.format(key)
        if key not in G2_TABLES:
            data=src.read_bytes()
            if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('06E hash mismatch '+key)
            with dst.open('xb') as f:f.write(data)
            report['tables'][key]={'source':'Stage06E, byte copy','gzip_sha256':br.sha(dst)};continue
        h0,_,base=bz.read_table(src,expected)
        header,variables,rows=bz.read_table(a.g2_dir/(key+'_G2_proposed_NOT_APPROVED.tsv.gz'),G2_TABLES[key])
        if header!=h0:raise ValueError('header differs from 06E '+key)
        n,segments=finalize_table(key,variables,rows,base,cells[key]);total+=segments
        w=bw.Writer(dst,header)
        for r in rows:w.line(r)
        digest,m=w.close()
        report['tables'][key]={'source':'Stage06E + approved Stage06I G2 rules','rows':m,'uncompressed_tsv_sha256':digest,'gzip_sha256':br.sha(dst),
            'approved_cells':n,'approved_list_rows':segments,'approved_by_variable_rule':dict(sorted(rules[key].items()))}
    if total!=G2_LIST_ROWS:raise ValueError('approved %d != approval list %d'%(total,G2_LIST_ROWS))
    report['approved_list_rows_total']=total;report['fingerprint_integers_strings']=br.fingerprint(report)
    with (a.out/'summary_APPROVED_20261106_G2.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06J COMPLETE; FINAL PRE-FORCING TABLES; NO FORCING WRITTEN');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'approved_list_rows_total':total,
        'approved_cells':{k:v['approved_cells'] for k,v in report['tables'].items() if 'approved_cells' in v},
        'gzip_sha256':{k:v['gzip_sha256'] for k,v in report['tables'].items()}},indent=1))

def selftest():
    assert approve('PROPOSED_G2A_SHORT_TA_FAULT_ERA_T_PLUS_1H_NOT_APPROVED|APPROVED_20261105_E1A_X|C3_Y')==(
        'APPROVED_20261106_G2A_SHORT_TA_FAULT_ERA_T_PLUS_1H|APPROVED_20261105_E1A_X|C3_Y',1)
    assert approve('APPROVED_20261105_E1A_X|ORIGINAL')==('APPROVED_20261105_E1A_X|ORIGINAL',0)
    chain=[('31.5','24.1','G2A_SHORT_TA_FAULT_ERA_T_PLUS_1H','ORIGINAL')]
    base=[['t0','31.5','0','ORIGINAL'],['t1','5','0','ORIGINAL']]
    rows=[['t0','24.1','0','PROPOSED_G2A_SHORT_TA_FAULT_ERA_T_PLUS_1H_NOT_APPROVED|ORIGINAL'],['t1','5','0','ORIGINAL']]
    assert finalize_table('T',['TA_F'],rows,base,{('TA_F','t0'):chain})==(1,1) and rows[0][3].startswith('APPROVED_20261106_G2A')
    for bad,cells in (([['t0','31.5','0','ORIGINAL'],['t1','6','0','ORIGINAL']],{}),                          # change without a proposal
                      ([['t0','20.0','0','PROPOSED_G2A_SHORT_TA_FAULT_ERA_T_PLUS_1H_NOT_APPROVED|ORIGINAL'],['t1','5','0','ORIGINAL']],{('TA_F','t0'):chain}),
                      ([['t0','31.5','0','ORIGINAL'],['t1','5','0','ORIGINAL']],{('TA_F','t0'):chain}),          # listed cell not proposed
                      ([['t0','24.1','1','PROPOSED_G2A_SHORT_TA_FAULT_ERA_T_PLUS_1H_NOT_APPROVED|ORIGINAL'],['t1','5','0','ORIGINAL']],{('TA_F','t0'):chain}),   # QC changed
                      ([['t0','np.float64(24.1)','0','PROPOSED_G2A_SHORT_TA_FAULT_ERA_T_PLUS_1H_NOT_APPROVED|ORIGINAL'],['t1','5','0','ORIGINAL']],
                       {('TA_F','t0'):[('31.5','np.float64(24.1)','G2A_SHORT_TA_FAULT_ERA_T_PLUS_1H','ORIGINAL')]})):          # value unreadable
        try:finalize_table('T',['TA_F'],bad,base,cells)
        except ValueError:pass
        else:raise AssertionError('accepted '+repr(bad))
    try:approve('PROPOSED_G2A_X|ORIGINAL')
    except ValueError:pass
    else:raise AssertionError('malformed tag accepted')
    print('STAGE06J SELF-TEST PASS: G2 approval, list replay, unlisted change, value/QC mismatch, unreadable value and malformed tag refused; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter);p.add_argument('--self-test',action='store_true')
    p.add_argument('--e-dir',type=Path,help='Stage06E output');p.add_argument('--g2-dir',type=Path,help='Stage06I output');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if None in (a.e_dir,a.g2_dir,a.out):p.error('--e-dir, --g2-dir and --out required')
    run(a)
if __name__=='__main__':main()

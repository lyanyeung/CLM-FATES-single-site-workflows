#!/usr/bin/env python3
"""Stage06E: final pre-forcing tables after the user approved Stage06C F1-F4 (2026-11-05). Read-only.

Inputs (SHA-256 pinned; byte-identical locally and on IRIDIS6, Stage06D): the twelve Stage05CB tables, the five
Stage06C proposal tables (Fjy, Khw, Tak, Yms, Tgf) and the Stage06C approval list.
  F1 E2 Tgf clock windows, F2 E1A humid outliers, F3 E1B dry outliers: every leading 'PROPOSED_E<rule>_NOT_APPROVED'
     segment of a tag becomes 'APPROVED_20261105_E<rule>' (Stage05CB approve()); values are not touched. A Tgf cell
     moved by E2 and then replaced by E1 carries two such segments.
  F4 multi-year humidity drift and saturation clipping: no value changes; recorded in the Stage06F forcing attributes.
Checks, cell by cell: replaying the approval list on Stage05CB (old value, old tag, new value, rule, in list order)
gives exactly the proposed cell, every list row is used once, and every other cell (value, QC, tag) equals Stage05CB.
The seven tables without proposals are copied byte for byte. All twelve are written under one name to a brand-new
directory. Writes nothing to forcing, cases, Slurm or sources.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

A6_PIN=('06a_build_utc_noleap_datm_candidates_GUARDED.py','88ff83e3f7fb6ec42c0b70eaf9d12019b70826851fe6132961dde08c0dc633cc')
E_TABLES={'JP-Fjy':'f512fe610d131d214cae884c6e63cea7a29076cf942c0224d8b12a3ed6c73f26','JP-Khw':'7499745a4b068be4913225800b40d86dded98e100edba9b46ac651c01d79ffee',
 'JP-Tak':'86b9768c4b2ca501daa296a16a4a8b27315885edc94d708faa351bc9f0460c22','JP-Tgf_HH':'2d56a60a649806a36f634b6dd862ce7cec4127aaf1412f4a086d0ffa303715c3',
 'JP-Yms':'95211ba392dafb63f5cc8c1667a4135b1d3fa952206d120380aba1d4ce537bbc'}
E_LIST='approval_list_E_NOT_APPROVED.tsv'
E_LIST_SHA='841fc01b8c4940cbd95f71cc99d97602bba57a1dc274782c05c769f5a70bf7a4'
E_LIST_ROWS=160285
TABLE_NAME='{}_final_preforcing_APPROVED_20261105_E.tsv.gz'

def load_a6():
    name,expected=A6_PIN;here=Path(__file__).parent
    for path in (here/name,here.parent/'stage06'/name):
        if path.is_file() and not path.is_symlink():break
    else:raise ValueError('pinned 06A script not found')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 06A hash mismatch')
    spec=importlib.util.spec_from_file_location('stage06a',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
a6=load_a6();cb=a6.cb;bz=cb.bz;br=bz.br;bw=bz.bw

def approve(tag):
    """Leading 'PROPOSED_E<rule>_NOT_APPROVED' segments -> 'APPROVED_20261105_E<rule>'; returns (tag, segments rewritten)."""
    parts=tag.split('|');n=0
    while n<len(parts) and parts[n].startswith('PROPOSED_E'):
        parts[n],_=cb.approve(parts[n]);n+=1
    return '|'.join(parts),n

def replay(base,chain):
    """05CB (value, tag) and the approval-list rows of one cell, in list order -> expected (value, tag) after Stage06C."""
    value,tag=base
    for old,new,rule,old_tag in chain:
        if old!=value or old_tag!=tag:raise ValueError('approval list does not follow the cell history')
        value,tag=new,'PROPOSED_'+rule+'_NOT_APPROVED|'+tag
    return value,tag

def finalize_table(key,variables,rows,base,cells):
    """rows: Stage06C table; base: Stage05CB rows; cells: {(variable, time): [(old, new, rule, old tag)]} for this table.
    Checks rows against base and cells, approves in place and returns (approved cells, approved segments)."""
    if [r[0] for r in rows]!=[r[0] for r in base]:raise ValueError('time axis differs from 05CB '+key)
    used=0;segments=0
    for r,b in zip(rows,base):
        for j,v in enumerate(variables):
            c=1+3*j;chain=cells.get((v,r[0]))
            if chain is None:
                if r[c:c+3]!=b[c:c+3]:raise ValueError('cell changed without a proposal %s %s %s'%(key,v,r[0]))
                continue
            if r[c+1]!=b[c+1] or (r[c],r[c+2])!=replay((b[c],b[c+2]),chain):raise ValueError('proposed cell differs from the approval list %s %s %s'%(key,v,r[0]))
            r[c+2],n=approve(r[c+2])
            if n!=len(chain):raise ValueError('tag segments %d != list rows %d %s %s %s'%(n,len(chain),key,v,r[0]))
            used+=1;segments+=n
    if used!=len(cells):raise ValueError('approval-list cells not found in '+key)
    if cb.finalize(rows):raise ValueError('a proposal tag survived approval in '+key)
    return used,segments

def read_list(path):
    br.check(path,E_LIST_SHA);cells=defaultdict(lambda:defaultdict(list));rules=defaultdict(Counter);n=0
    with path.open(encoding='utf-8',newline='') as f:
        r=csv.reader(f,delimiter='\t')
        if next(r)[:7]!=['table','variable','native_start','value_in_05CB','proposed_value','rule','05CB_tag']:raise ValueError('approval list header')
        for key,v,t,old,new,rule,old_tag,*_ in r:cells[key][(v,t)].append((old,new,rule,old_tag));rules[key][v+'|'+rule]+=1;n+=1
    if n!=E_LIST_ROWS or set(cells)!=set(E_TABLES):raise ValueError('approval list rows or tables')
    return cells,rules

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    cells,rules=read_list(a.e_dir/E_LIST)
    a.out.mkdir();report={'stage':'06E','status':'FINAL_PREFORCING_TABLES_APPROVED_20261105_E_NO_FORCING_WRITTEN',
        'approval':'user approved Stage06C F1 (E2 Tgf clock windows), F2 (E1A), F3 (E1B) and F4 (keep and record drift) on 2026-11-05',
        'approval_list_sha256':E_LIST_SHA,'tables':{}}
    total=0
    for key,expected in a6.TABLES.items():
        print('STAGE06E',key,flush=True);src=a.cb_dir/a6.TABLE_NAME.format(key);dst=a.out/TABLE_NAME.format(key)
        if key not in E_TABLES:
            data=src.read_bytes()
            if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('05CB hash mismatch '+key)
            with dst.open('xb') as f:f.write(data)
            report['tables'][key]={'source':'Stage05CB, byte copy','gzip_sha256':br.sha(dst)};continue
        h0,_,base=bz.read_table(src,expected)
        header,variables,rows=bz.read_table(a.e_dir/(key+'_E_proposed_NOT_APPROVED.tsv.gz'),E_TABLES[key])
        if header!=h0:raise ValueError('header differs from 05CB '+key)
        n,segments=finalize_table(key,variables,rows,base,cells[key]);total+=segments
        w=bw.Writer(dst,header)
        for r in rows:w.line(r)
        digest,m=w.close()
        report['tables'][key]={'source':'Stage05CB + approved Stage06C E rules','rows':m,'uncompressed_tsv_sha256':digest,'gzip_sha256':br.sha(dst),
            'approved_cells':n,'approved_list_rows':segments,'approved_by_variable_rule':dict(sorted(rules[key].items()))}
    if total!=E_LIST_ROWS:raise ValueError('approved %d != approval list %d'%(total,E_LIST_ROWS))
    report['approved_list_rows_total']=total;report['fingerprint_integers_strings']=br.fingerprint(report)
    with (a.out/'summary_APPROVED_20261105_E.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06E COMPLETE; FINAL PRE-FORCING TABLES; NO FORCING WRITTEN');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'approved_list_rows_total':total,
        'approved_cells':{k:v['approved_cells'] for k,v in report['tables'].items() if 'approved_cells' in v},
        'gzip_sha256':{k:v['gzip_sha256'] for k,v in report['tables'].items()}},indent=1))

def selftest():
    tag='PROPOSED_E1A_HUMID_OUTLIER_RH_REF_NOT_APPROVED|PROPOSED_E2_TGF_CLOCK_M30_NOT_APPROVED|APPROVED_20261105_D9b_X|C3_Y'
    assert approve(tag)==('APPROVED_20261105_E1A_HUMID_OUTLIER_RH_REF|APPROVED_20261105_E2_TGF_CLOCK_M30|APPROVED_20261105_D9b_X|C3_Y',2)
    assert approve('APPROVED_20261105_D9b_X')==('APPROVED_20261105_D9b_X',0)
    chain=[('1','2','E2_TGF_CLOCK_M30','ORIGINAL'),('2','3','E1A_HUMID_OUTLIER_RH_REF','PROPOSED_E2_TGF_CLOCK_M30_NOT_APPROVED|ORIGINAL')]
    assert replay(('1','ORIGINAL'),chain)==('3','PROPOSED_E1A_HUMID_OUTLIER_RH_REF_NOT_APPROVED|PROPOSED_E2_TGF_CLOCK_M30_NOT_APPROVED|ORIGINAL')
    base=[['t0','1','0','ORIGINAL'],['t1','5','0','ORIGINAL']]
    rows=[['t0','3','0','PROPOSED_E1A_HUMID_OUTLIER_RH_REF_NOT_APPROVED|PROPOSED_E2_TGF_CLOCK_M30_NOT_APPROVED|ORIGINAL'],['t1','5','0','ORIGINAL']]
    assert finalize_table('T',['RH_F'],rows,base,{('RH_F','t0'):chain})==(1,2) and rows[0][3].startswith('APPROVED_20261105_E1A')
    for bad,cells in (([['t0','1','0','ORIGINAL'],['t1','6','0','ORIGINAL']],{}),                         # change without a proposal
                      ([['t0','4','0','PROPOSED_E2_TGF_CLOCK_M30_NOT_APPROVED|ORIGINAL'],['t1','5','0','ORIGINAL']],{('RH_F','t0'):chain[:1]}),  # value differs
                      ([['t0','1','0','ORIGINAL'],['t1','5','0','ORIGINAL']],{('RH_F','t0'):chain[:1]})):  # listed cell not proposed
        try:finalize_table('T',['RH_F'],bad,base,cells)
        except ValueError:pass
        else:raise AssertionError('accepted '+repr(bad))
    print('STAGE06E SELF-TEST PASS: chained approval, list replay, unlisted change and value mismatch refused; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter);p.add_argument('--self-test',action='store_true')
    p.add_argument('--cb-dir',type=Path,help='Stage05CB output');p.add_argument('--e-dir',type=Path,help='Stage06C output');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if None in (a.cb_dir,a.e_dir,a.out):p.error('--cb-dir, --e-dir and --out required')
    run(a)
if __name__=='__main__':main()

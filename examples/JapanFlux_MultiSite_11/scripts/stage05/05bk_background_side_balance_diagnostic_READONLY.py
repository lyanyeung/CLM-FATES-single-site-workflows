#!/usr/bin/env python3
"""Diagnose pre/post QC2 background imbalance, without changing any shadow.

Uses only pinned operator-pasted Stage05AZ pairs and Stage05BA group ledger.
Side-balanced midpoint of side medians is a sensitivity, not an approved fit.
"""
import argparse
import csv
import hashlib
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

PASTE_SHA='bd96cc5f0d80fe440c2db3540a8492d75c2641b8ee7bf95b810765f64925a26c'
GROUP_SHA='6fe0969e0ed1ecbdb9e8dd8ff55eb148b5dd343b637ec7de6de11e07cf01bb6b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def side_summary(left,right):
    if not left or not right or not all(math.isfinite(x) for x in left+right):raise ValueError('missing or invalid side')
    l=statistics.median(left);r=statistics.median(right);overall=statistics.median(left+right)
    return l,r,overall,(l+r)/2
def selftest():
    l,r,all_,balanced=side_summary([0,0,0],[10])
    assert (l,r,all_,balanced)==(0,10,0,5)
    try:side_summary([1],[])
    except ValueError:pass
    else:raise AssertionError('missing side accepted')
    print('STAGE05BK SELF-TEST PASS; DESCRIPTIVE ONLY; ALL HOLD')
def run(paste,groups):
    if sha(paste)!=PASTE_SHA or sha(groups)!=GROUP_SHA:raise ValueError('input SHA256 mismatch')
    with groups.open(encoding='utf-8',newline='') as f:ledger=list(csv.DictReader(f,delimiter='\t'))
    if len(ledger)!=17 or any(r['science_status']!='HOLD_NO_APPROVED_REPLACEMENT' for r in ledger):raise ValueError('group/HOLD scope')
    mapping={(r['site'],r['variable'],r['native_start']):r for r in ledger}
    if len(mapping)!=17:raise ValueError('duplicate groups')
    pairs=defaultdict(lambda:{'left':[],'right':[]});seen=set();section='';total=0
    for line in paste.read_text(encoding='utf-8').splitlines():
        if line.startswith('FILE '):section=line.split()[-1].rsplit('/',1)[-1]
        elif section=='background_pairs_READONLY.tsv' and line.startswith('JP-'):
            p=line.split()
            if p[3]!='540':continue
            k=(p[0],p[1],p[2]);unique=(*k,p[5])
            if k not in mapping or unique in seen or p[7]!='2' or not p[-1].endswith('QC2_SAME_RELEASE_ERA_DERIVED'):
                raise ValueError('background source/key/duplicate')
            seen.add(unique);f=float(p[6]);grid=float(p[8]);delta=float(p[9])
            if not all(math.isfinite(x) for x in (f,grid,delta)) or abs(f-grid-delta)>1e-6:raise ValueError('background arithmetic')
            pairs[k]['left' if p[5]<p[2] else 'right'].append(delta);total+=1
    if total!=897 or set(pairs)!=set(mapping):raise ValueError('background coverage')
    result=[]
    for k in sorted(mapping):
        r=mapping[k];left=pairs[k]['left'];right=pairs[k]['right'];l,rr,overall,balanced=side_summary(left,right)
        if len(left)+len(right)!=int(r['qc2_background_count']) or abs(overall-float(r['qc2_background_median']))>1e-6:
            raise ValueError('background count/median mismatch')
        result.append({'site':k[0],'variable':k[1],'group_start':k[2],'n_left':len(left),'n_right':len(right),
            'left_median':l,'right_median':rr,'selected_overall_median':overall,'side_balanced_median_sensitivity':balanced,
            'balanced_minus_selected':balanced-overall,'source':'QC2_DERIVED_NOT_QC0',
            'status':'HOLD_SELECTED_METHOD_NOT_CHANGED'})
    if sha(paste)!=PASTE_SHA or sha(groups)!=GROUP_SHA:raise ValueError('input changed')
    w=csv.DictWriter(sys.stdout,fieldnames=result[0].keys(),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(result)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--az-paste',type=Path);p.add_argument('--groups',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if a.az_paste is None or a.groups is None:p.error('both inputs required')
    run(a.az_paste,a.groups)
if __name__=='__main__':main()

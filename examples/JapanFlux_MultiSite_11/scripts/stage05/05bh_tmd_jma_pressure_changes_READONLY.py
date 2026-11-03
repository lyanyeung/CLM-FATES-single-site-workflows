#!/usr/bin/env python3
"""Compare saved Tmd event-jump magnitudes with JMA hourly station context.

JMA is a different station 12.7 km away, not a paired tower measurement.
Native source clock and instrument elevations are unverified. No repairs.
"""
import argparse
import csv
import hashlib
import math
import sys
from pathlib import Path

INPUT_SHA='df630467aa393331c5c4116af687c988976d9b747b5ff1aed87ef3eea66fcb7e'
CLOCK_SHA='e48c673ad97f3345f2336d4636fc7cdfcddf7dc85dae2ab608db8afbc231675e'
LEDGER_SHA='35f9f064983bec73c16fac44a8259093ffa7ec36f23caa4b28c93e44113677f2'
JMA={
 '200508120230':('02,03,04',[1011.4,1011.3,1011.3]),
 '201112170630':('06,07,08',[1012.5,1012.8,1013.4]),
 '202204090230':('02,03,04',[1014.4,1014.4,1014.2]),
}
def hour_deltas_kpa(values):
    if len(values)!=3 or not all(math.isfinite(v) and v>0 for v in values):raise ValueError('invalid JMA input')
    return [(b-a)/10.0 for a,b in zip(values,values[1:])]
def clock_boundary_jumps(left,values):
    if not math.isfinite(left) or len(values)!=4 or not all(math.isfinite(v) for v in values):
        raise ValueError('invalid clock-scenario input')
    return [v-left for v in values]
def selftest():
    a=hour_deltas_kpa([1014.4,1014.4,1014.2]);assert abs(a[0])<1e-9 and abs(a[1]+0.02)<1e-9
    assert clock_boundary_jumps(100.,[99.,99.,99.,99.])==[-1.,-1.,-1.,-1.]
    try:hour_deltas_kpa([100,math.nan,100])
    except ValueError:pass
    else:raise AssertionError('nonfinite JMA value accepted')
    print('STAGE05BH SELF-TEST PASS; NOT MATCHED SITE/HALFHOUR; ALL HOLD')
def run(path,clock,ledger):
    paths={path:INPUT_SHA,clock:CLOCK_SHA,ledger:LEDGER_SHA}
    if any(hashlib.sha256(p.read_bytes()).hexdigest()!=h for p,h in paths.items()):raise ValueError('input SHA256 mismatch')
    with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f,delimiter='\t'))
    matched={r['native_group_start']:r for r in rows if r['site']=='JP-Tmd' and r['variable']=='PA'}
    if set(matched)!=set(JMA) or len(rows)!=17:raise ValueError('Tmd group scope mismatch')
    w=csv.writer(sys.stdout,delimiter='\t',lineterminator='\n')
    w.writerow(['Tmd_group_native_start','JMA_jst_hours','JMA_station_hPa','JMA_adjacent_hour_changes_kPa',
                'selected_max_halfhour_jump_kPa','selected_left_boundary_jump_kPa',
                'local_same_source_QC2_jump_p95_kPa','status'])
    for event in sorted(JMA):
        hours,press=JMA[event];delta=hour_deltas_kpa(press);r=matched[event]
        if r['status']!='HOLD_NO_APPROVAL':raise ValueError('missing science HOLD')
        w.writerow([event,hours,','.join(map(str,press)),','.join(f'{v:.4f}' for v in delta),
                    r['group_max_abs_jump'],r['left_boundary_abs_jump'],r['local_QC2_jump_p95_descriptive'],
                    'CONTEXT_DIFFERENT_SITE_AND_TIME_SUPPORT_ALL_HOLD'])
    with clock.open(encoding='utf-8',newline='') as f:clocks=list(csv.DictReader(f,delimiter='\t'))
    with ledger.open(encoding='utf-8',newline='') as f:ledgers=list(csv.DictReader(f,delimiter='\t'))
    event='202204090230'
    clock_rows=[r for r in clocks if r['site']=='JP-Tmd' and r['variable']=='PA' and r['native_start']==event]
    ledger_rows=[r for r in ledgers if r['site']=='JP-Tmd' and r['variable']=='PA' and r['native_start']==event]
    if len(clock_rows)!=1 or len(ledger_rows)!=1 or clock_rows[0]['science_status']!='HOLD_NO_APPROVED_REPLACEMENT':
        raise ValueError('clock or ledger scope/HOLD mismatch')
    c=clock_rows[0];left=float(ledger_rows[0]['left_QC2_F'])
    names=['UTC_PLUS_08_30_SENSITIVITY','UTC_PLUS_09_00_HYPOTHESIS','UTC_PLUS_09_30_SENSITIVITY','LONGITUDE_MEAN_SOLAR_DIAGNOSTIC_NOT_PROVEN']
    jumps=clock_boundary_jumps(left,[float(c[n+'_value']) for n in names])
    print('TMD_2022_FIRST_SELECTED_MINUS_LEFT_QC2_KPA_FOUR_DIAGNOSTIC_CLOCKS',','.join(f'{v:.6f}' for v in jumps))
    print('P95_COMPARISON_DESCRIPTIVE_ONLY',matched[event]['local_QC2_jump_p95_descriptive'],'NO_CLOCK_PROOF_OR_APPROVAL')
    if any(hashlib.sha256(p.read_bytes()).hexdigest()!=h for p,h in paths.items()):raise ValueError('input changed')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true');p.add_argument('--boundary',type=Path)
    p.add_argument('--clock-sensitivity',type=Path);p.add_argument('--ba-ledger',type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(x is None for x in (a.boundary,a.clock_sensitivity,a.ba_ledger)):p.error('all three input paths required')
    run(a.boundary,a.clock_sensitivity,a.ba_ledger)
if __name__=='__main__':main()

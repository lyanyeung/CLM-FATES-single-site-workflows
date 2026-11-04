#!/usr/bin/env python3
"""Illustrative sensitivity to historical JMA barometer height; all HOLD.

Read-only calculator from documented values; no network or source files.
Metadata heights are from a pinned third-party mirror of JMA's index, not a
direct official archive verification. See accompanying review document.
"""
import argparse
import csv
import math
import sys

# site, date, JMA station pressure hPa, air C, nominal ground height m,
# historical barometer height m (mirror), tower BIF ground m,
# selected event centre kPa, previous QC2 bridge centre kPa
DATA = [
 ('Tmd','2005-08-12',1011.3,19.9,6.,7.9,117.,98.98431,99.0085),
 ('Tmd','2011-12-17',1012.8,-7.6,6.,7.9,117.,98.997775,98.9625),
 ('Tmd','2022-04-09',1014.4,4.3,6.,7.9,117.,99.09934,99.195),
 ('Fjy','2005-08-12',916.8,21.,860.,860.5,1043.,89.9292475,89.987),
 ('Fjy','2011-12-17',916.9,-4.4,860.,861.3,1043.,90.0251625,89.999),
]

def hydro(p_hpa, temp_c, station_height, target_height):
    if not all(math.isfinite(x) for x in (p_hpa,temp_c,station_height,target_height)) or p_hpa <= 0 or temp_c <= -273.15:
        raise ValueError('invalid pressure/temperature/height')
    return p_hpa/10 * math.exp(-9.80665*(target_height-station_height)/(287.05*(temp_c+273.15)))

def results():
    for site,day,p,t,ground,baro,tower,selected,bridge in DATA:
        old=hydro(p,t,ground,tower);new=hydro(p,t,baro,tower)
        yield {'site':site,'event_date_native_assumed_JST':day,'JMA_station_hPa':p,
               'JMA_temperature_C':t,'JMA_nominal_ground_m':ground,
               'JMA_barometer_m_THIRD_PARTY_MIRROR':baro,'tower_BIF_ground_m_NOT_SENSOR':tower,
               'previous_ground_assumption_kPa':round(old,6),
               'barometer_height_illustrative_kPa':round(new,6),
               'height_assumption_change_kPa':round(new-old,6),
               'selected_centre_HOLD_kPa':selected,
               'selected_minus_barometer_illustration_kPa':round(selected-new,6),
               'prior_bridge_centre_HOLD_kPa':bridge,
               'status':'CONTEXT_ONLY_NOT_TOWER_TRUTH_ALL_HOLD'}

def selftest():
    assert hydro(1000,20,10,10)==100.
    assert hydro(1000,20,10,110)<100.
    assert abs(hydro(1011.3,19.9,7.9,117)-99.851893)<0.000001
    try:hydro(0,20,0,10)
    except ValueError:pass
    else:raise AssertionError('invalid pressure accepted')
    print('STAGE05BO SELF-TEST PASS; HEIGHT SENSITIVITY ONLY; ALL HOLD')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:selftest();return
    rows=list(results());w=csv.DictWriter(sys.stdout,rows[0].keys(),delimiter='\t',lineterminator='\n')
    w.writeheader();w.writerows(rows)
    print('CONTEXT ONLY: third-party metadata mirror, site height not sensor height; no approval',file=sys.stderr)
if __name__=='__main__':main()

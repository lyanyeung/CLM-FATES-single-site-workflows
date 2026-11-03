#!/usr/bin/env python3
"""Illustrative JMA–Tmd/Fjy pressure context from public JMA pages.

No station adjustment is applied to forcing or shadow values. The temperature,
height and horizontal-homogeneity assumptions are sensitivity scenarios, not
calibrated errors or approved corrections. All 45 source fields remain HOLD.
"""
import argparse,csv,math,sys

RD=287.05
G=9.80665
CASES=[
 {'site':'Tmd','station_elevation_m':6.,'site_elevation_m':117.,'date':'2005-08-12','native_centre':'03:00','jma_jst_hours':'02,03,04',
  'jma_local_hpa':[1011.4,1011.3,1011.3],'station_temperature_c':19.9,
  'grid_sp_kpa':99.658280,'shadow_kpa':99.0085},
 {'site':'Tmd','station_elevation_m':6.,'site_elevation_m':117.,'date':'2011-12-17','native_centre':'07:00','jma_jst_hours':'06,07,08',
  'jma_local_hpa':[1012.5,1012.8,1013.4],'station_temperature_c':-7.6,
  'grid_sp_kpa':99.717340,'shadow_kpa':98.9625},
 {'site':'Tmd','station_elevation_m':6.,'site_elevation_m':117.,'date':'2022-04-09','native_centre':'03:00','jma_jst_hours':'02,03,04',
  'jma_local_hpa':[1014.4,1014.4,1014.2],'station_temperature_c':4.3,
  'grid_sp_kpa':99.867445,'shadow_kpa':99.1950},
 {'site':'Fjy','station_elevation_m':860.,'site_elevation_m':1043.,'date':'2005-08-12','native_centre':'03:00','jma_jst_hours':'02,03,04',
  'jma_local_hpa':[916.5,916.8,916.7],'station_temperature_c':21.0,
  'grid_sp_kpa':None,'shadow_kpa':89.987},
 {'site':'Fjy','station_elevation_m':860.,'site_elevation_m':1043.,'date':'2011-12-17','native_centre':'07:00','jma_jst_hours':'06,07,08',
  'jma_local_hpa':[916.0,916.9,917.2],'station_temperature_c':-4.4,
  'grid_sp_kpa':None,'shadow_kpa':89.999}]
def estimate(station_kpa,dz_m,temperature_c):
    if not all(math.isfinite(x) for x in (station_kpa,dz_m,temperature_c)) or station_kpa<=0 or temperature_c<=-273.15:
        raise ValueError('Invalid pressure, height, or temperature')
    return station_kpa*math.exp(-G*dz_m/(RD*(temperature_c+273.15)))
def selftest():
    assert estimate(101.3,0,20)==101.3
    assert estimate(101.3,111,20)<101.3
    assert estimate(101.3,111,0)<estimate(101.3,111,20)
    try:estimate(100,1,-273.15)
    except ValueError:pass
    else:raise AssertionError('absolute-zero input accepted')
    print('STAGE05BB SELF-TEST PASS; ILLUSTRATIVE CONTEXT ONLY; ALL HOLD')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:selftest();return
    w=csv.writer(sys.stdout,delimiter='\t',lineterminator='\n')
    w.writerow(['site','date','native_centre','JMA_station_pressure_hPa','JMA_station_T_C',
        'JMA_illustrative_site_elevation_pressure_kPa','sensitivity_low_kPa','sensitivity_high_kPa',
        'shadow_kPa_NOT_APPROVED','shadow_minus_illustrative_kPa','ERA5L_grid_instant_kPa',
        'grid_minus_illustrative_kPa','status'])
    for row in CASES:
        station=row['jma_local_hpa'][1]/10
        T=row['station_temperature_c'];dz=row['site_elevation_m']-row['station_elevation_m']
        nominal=estimate(station,dz,T)
        scenario=[estimate(p/10,d,t) for p in row['jma_local_hpa'] for d in (dz-20,dz+20) for t in (T-10,T+10)]
        grid=row['grid_sp_kpa']
        w.writerow([row['site'],row['date'],row['native_centre'],row['jma_local_hpa'][1],T,
            round(nominal,5),round(min(scenario),5),round(max(scenario),5),row['shadow_kpa'],
            round(row['shadow_kpa']-nominal,5),grid if grid is not None else '',
            round(grid-nominal,5) if grid is not None else '', 'CONTEXT_ONLY_ALL_HOLD'])
if __name__=='__main__':main()

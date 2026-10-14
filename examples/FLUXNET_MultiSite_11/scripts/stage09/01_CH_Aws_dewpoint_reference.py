#!/usr/bin/env python3
"""Stage 09 CH-Aws: cross-check 559 impossible ERA-derived RH records.

fetch: Obtain separately served Open-Meteo ERA5 and ERA5-Land hourly T2m/Td2m
       (NOT the FLUXNET-downscaled VPD); cache immutable raw JSON by year.
assess: Compare model RH to each FLUXNET event, test time-alignment offsets,
        calculate candidate VPD/QBOT for REVIEW ONLY. NEVER write a corrected
        forcing, never modify inputs, no model submission.

Open-Meteo is a convenience delivery of reanalysis, not independent validation.
ERA5 and ERA5-Land are NOT independent observations; terrain mismatch matters.
All data are stored in a study-local stage09 report folder, not in model DATM.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

import numpy as np
import pandas as pd

SITE = 'CH-Aws'
FIRST, LAST = 2006, 2024
LAT, LON = 46.583111, 9.790639
RAW_YEARS = tuple(range(2006, 2014))
MODELS = ('era5', 'era5_land')
ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
OUT = Path.home() / 'FLUXNET_MultiSite_11' / 'stage09_CH_Aws'
API = 'https://archive-api.open-meteo.com/v1/archive'


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def sat(t):
    x = np.asarray(t, dtype=float)
    with np.errstate(invalid='ignore', over='ignore', divide='ignore'):
        return 6.112 * np.exp(np.clip(17.67 * x / (x + 243.5), -100., 100.))


def read_json_verify(path, year):
    j = json.loads(path.read_text())
    if j.get('error'):
        raise ValueError('API error in file ' + str(path) + ': ' + str(j.get('reason')))
    h = j.get('hourly', {})
    cols = ('time', 'temperature_2m', 'dew_point_2m')
    if any(c not in h for c in cols):
        raise ValueError(str(path) + ' missing required hourly variables')
    expected = 8784 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 8760
    if any(len(h[c]) != expected for c in cols):
        raise ValueError(str(path) + ' incomplete hourly series; expected ' + str(expected))
    t = pd.DatetimeIndex(pd.to_datetime(h['time'], errors='raise'))
    if (t[0] != pd.Timestamp(f'{year}-01-01 00:00') or
        t[-1] != pd.Timestamp(f'{year}-12-31 23:00') or
        not (t.to_series().diff().iloc[1:] == pd.Timedelta(hours=1)).all()):
        raise ValueError('Unexpected timestamps / timezone in ' + str(path))
    if int(j.get('utc_offset_seconds', 99999)) != 0:
        raise ValueError('Open-Meteo reference MUST be GMT/UTC with 0 offset')
    return j


def fetch(out):
    cache = out / 'raw_openmeteo'
    cache.mkdir(parents=True, exist_ok=True)
    print('Open-Meteo historical ERA5 and ERA5-Land, CH-Aws reference:', LAT, LON, flush=True)
    print('Years 2006-2013, UTC hourly; NO FLUXNET _ERA reuse', flush=True)
    problems = []
    for model in MODELS:
        for year in RAW_YEARS:
            path = cache / f'{model}_{year}.json'
            if path.exists():
                try:
                    read_json_verify(path, year)
                    print('CACHED', model, year, flush=True)
                    continue
                except Exception as e:
                    problems.append(f'{path}: cache invalid: {e}')
                    print('INVALID CACHE (kept unchanged)', path, flush=True)
                    continue
            params = {
                'latitude': LAT, 'longitude': LON,
                'start_date': f'{year}-01-01', 'end_date': f'{year}-12-31',
                'hourly': 'temperature_2m,dew_point_2m,relative_humidity_2m',
                'timezone': 'GMT', 'models': model,
            }
            url = API + '?' + urlencode(params)
            success = False
            for attempt in range(3):
                try:
                    req = Request(url, headers={'User-Agent':'CH-Aws-research-audit/1.0'})
                    with urlopen(req, timeout=55) as resp:
                        raw = resp.read()
                    obj = json.loads(raw)
                    temp = cache / f'.{model}_{year}.download'
                    temp.write_bytes(raw)
                    try:
                        read_json_verify(temp, year)
                    except Exception:
                        temp.unlink(missing_ok=True)
                        raise
                    temp.replace(path)
                    success = True
                    print('DOWNLOADED', model, year, 'bytes', len(raw), flush=True)
                    break
                except (URLError, HTTPError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as e:
                    print('FETCH WARNING', model, year, f'attempt {attempt+1}:', str(e)[:240], flush=True)
                    if attempt < 2:
                        time.sleep(2 * (attempt + 1))
            if not success:
                problems.append(f'{model} {year}: remote download failed; use WSL fallback')
    if problems:
        print('\nFETCH INCOMPLETE; files already downloaded are reusable:', *problems, sep='\n', flush=True)
        raise SystemExit(2)
    print('\nFETCH COMPLETE. Run: python 01_CH_Aws_dewpoint_reference.py assess', flush=True)


def load_reference(out):
    all_models = {}
    for model in MODELS:
        records = []
        for year in RAW_YEARS:
            path = out / 'raw_openmeteo' / f'{model}_{year}.json'
            if not path.exists():
                raise FileNotFoundError(f'Missing {path}. Run `fetch` first (or on WSL).')
            obj = read_json_verify(path, year)
            hourly = obj['hourly']
            temp = np.asarray([np.nan if x is None else x for x in hourly['temperature_2m']], dtype=float)
            dew = np.asarray([np.nan if x is None else x for x in hourly['dew_point_2m']], dtype=float)
            with np.errstate(invalid='ignore', divide='ignore'):
                rh = 100. * sat(dew) / sat(temp)
            df = pd.DataFrame({
                'utc': pd.DatetimeIndex(pd.to_datetime(hourly['time'])),
                'T_ref': temp, 'Td_ref': dew, 'RH_ref': rh,
                'grid_elevation_m': float(obj.get('elevation', float('nan'))),
                'source_year': year,
            })
            records.append(df)
        whole = pd.concat(records, ignore_index=True).set_index('utc').sort_index()
        if whole.index.has_duplicates:
            raise ValueError('reference contains duplicate UTC timestamps: ' + model)
        all_models[model] = whole
    return all_models


def get_candidate(root):
    directory = root / SITE / 'forcing' / 'merged_multisource_11_v07a'
    filename = directory / f'{SITE}_multisource_HH_{FIRST}_{LAST}_candidate.csv'
    status_path = directory / 'status.json'
    for p in (filename, status_path):
        if not p.is_file():
            raise FileNotFoundError(str(p))
    meta = json.loads(status_path.read_text())
    if meta.get('site') != SITE:
        raise ValueError('Candidate site metadata mismatch')
    if meta.get('candidate_sha256') != sha256(filename):
        raise ValueError('Candidate CSV SHA256 differs from Stage03 manifest: stop')
    d = pd.read_csv(filename, low_memory=False)
    idx = pd.DatetimeIndex(pd.to_datetime(d['time'], errors='raise'))
    expected = pd.date_range('2006-01-01','2024-12-31 23:30',freq='30min')
    expected = expected[~((expected.month == 2) & (expected.day == 29))]
    if not idx.equals(expected):
        raise ValueError(f'CH-Aws time axis invalid: {len(idx)} vs {len(expected)}')
    if any(c not in d for c in ['TA_F','VPD_F','PA_F','PAIR_STATUS','TA_F_QC','VPD_F_QC','PA_F_QC']):
        raise ValueError('Stage03 candidate lacks required variables/QCs')
    d.index = idx
    t = pd.to_numeric(d['TA_F'], errors='coerce').to_numpy(float)
    v = pd.to_numeric(d['VPD_F'], errors='coerce').to_numpy(float)
    p = pd.to_numeric(d['PA_F'], errors='coerce').to_numpy(float)
    rh = 100. * (sat(t)-v) / sat(t)
    flags = (d.PAIR_STATUS.astype(str) == 'INVALID_PAIR_REVIEW') & np.isfinite(rh) & (rh < 0)
    return d, flags, rh, meta


def interp_ref(reference, target_index, hours_local_offset):
    """Reference UTC timestamps -> nominal tower local STANDARD time; interpolate hourly T/Td to half hour.

    No DST applied. FLUXNET timestamps normally local standard time, but this MUST be checked.
    Interpolate RH from both ERA variables after time interpolation, not the hourly RH itself.
    """
    ref = reference[['T_ref', 'Td_ref']].copy()
    ref.index = ref.index + pd.Timedelta(hours=int(hours_local_offset))
    all_idx = ref.index.union(target_index)
    z = ref.reindex(all_idx).sort_index().interpolate(method='time', limit=1, limit_area='inside')
    z = z.reindex(target_index)
    z['RH_ref'] = 100. * sat(z['Td_ref'].to_numpy()) / sat(z['T_ref'].to_numpy())
    return z


def assess(out, root, utc_offset):
    d, flagged, rh_old, meta = get_candidate(root)
    references = load_reference(out)
    flagged_idx = d.index[flagged]
    if not len(flagged_idx):
        raise ValueError('No negative RH flagged events in candidate; confirm version')
    print('CH-Aws flagged event count:', len(flagged_idx), 'expected from prior Stage07: 559', flush=True)
    if len(flagged_idx) != 559:
        raise ValueError('Event count changed from verified 559; stop and inspect baseline')
    exact_qc = d.loc[flagged, ['TA_F_QC','VPD_F_QC','PA_F_QC']].apply(pd.to_numeric,errors='coerce')
    if not (exact_qc == 2).all().all():
        raise ValueError('Official QC no longer all 2 for selected CH-Aws events: stop')

    # Align weather clocks. This is only a DIAGNOSTIC, not an automatic offset selection.
    validation = []
    for model, hourly in references.items():
        for offset in (0, 1, 2):
            at = interp_ref(hourly, d.index, offset)
            site = pd.to_numeric(d.TA_F,errors='coerce')
            measured = pd.to_numeric(d.TA_F_QC,errors='coerce').isin((0,1))
            within = (d.index.year >= 2006)&(d.index.year <= 2013)
            valid = measured & within & np.isfinite(site) & np.isfinite(at.T_ref)
            # If site temperature is mostly ERA-derived, record comparable all-value metric too.
            allvalid = within & np.isfinite(site) & np.isfinite(at.T_ref)
            check = valid if valid.sum() >= 1000 else allvalid
            diff = site.loc[check].to_numpy(dtype=float)-at.loc[check,'T_ref'].to_numpy(dtype=float)
            if len(diff) > 2:
                corr = float(np.corrcoef(site.loc[check], at.loc[check,'T_ref'])[0,1])
                rmse = float(np.sqrt(np.mean(diff**2)))
                bias = float(np.mean(diff))
            else: corr=rmse=bias=float('nan')
            validation.append({'model':model,'utc_offset_hours':offset,'used_qc01':bool(valid.sum()>=1000),
                               'n':int(check.sum()),'temperature_correlation':round(corr,5),
                               'temperature_RMSE_C':round(rmse,4),'site_minus_grid_C':round(bias,4)})
    vtab = pd.DataFrame(validation)
    out.mkdir(parents=True,exist_ok=True)
    vtab.to_csv(out/'01_timezone_alignment.csv',index=False)
    print('\n=== TIME ALIGNMENT (NOT AUTO SELECTED) ===',flush=True)
    print(vtab.to_string(index=False),flush=True)
    print('Chosen input standard-time offset:',utc_offset,'hours relative to UTC, not DST',flush=True)

    # Double-model reconstruction of RH. Terrain difference: transfer relative humidity,
    # never copy grid dewpoint as station vapor pressure without vertical adjustment.
    data = pd.DataFrame(index=flagged_idx)
    data['TA_site_C'] = pd.to_numeric(d.loc[flagged,'TA_F'])
    data['VPD_original_hPa'] = pd.to_numeric(d.loc[flagged,'VPD_F'])
    data['PA_site_kPa'] = pd.to_numeric(d.loc[flagged,'PA_F'])
    data['RH_original_pct'] = rh_old[flagged.to_numpy()]
    data['official_TA_QC'] = pd.to_numeric(d.loc[flagged,'TA_F_QC'])
    data['official_VPD_QC'] = pd.to_numeric(d.loc[flagged,'VPD_F_QC'])
    data['official_PA_QC'] = pd.to_numeric(d.loc[flagged,'PA_F_QC'])
    for model, hourly in references.items():
        ref = interp_ref(hourly, flagged_idx, utc_offset)
        data[f'{model}_T2m_C'] = ref['T_ref']
        data[f'{model}_Td2m_C'] = ref['Td_ref']
        data[f'{model}_RH_pct'] = ref['RH_ref']
        rh_ref = ref['RH_ref'].to_numpy(dtype=float)
        es_site = sat(data['TA_site_C'].to_numpy(dtype=float))
        vpd_ref = es_site * (1-rh_ref/100)
        ea_ref = es_site-vpd_ref
        psite = data['PA_site_kPa'].to_numpy(dtype=float)*1000
        with np.errstate(divide='ignore',invalid='ignore'):
            qb = .622*(ea_ref*100)/(psite-.378*(ea_ref*100))
        data[f'{model}_candidate_VPD_hPa'] = vpd_ref
        data[f'{model}_candidate_QBOT_kgkg'] = qb
    rh1 = data['era5_RH_pct'].to_numpy(dtype=float)
    rh2 = data['era5_land_RH_pct'].to_numpy(dtype=float)
    differ = np.abs(rh1-rh2)
    checks = (np.isfinite(rh1)&np.isfinite(rh2)&(rh1>=1)&(rh1<=100)&
              (rh2>=1)&(rh2<=100)&(differ<=15))
    data['RH_two_model_absdiff_pctpoints'] = differ
    data['BOTH_MODELS_SUPPORT_REVIEW_CANDIDATE'] = checks
    data['decision'] = np.where(checks,'TWO_MODEL_REVIEW_ONLY_NO_CHANGE',
                                'INSUFFICIENT_AGREEMENT_OR_REFERENCE')
    data.insert(0,'time',flagged_idx.strftime('%Y-%m-%d %H:%M:%S'))
    data.to_csv(out/'02_CH_Aws_559_event_reference_comparison.csv',index=False)

    hist = pd.DataFrame({'year': flagged_idx.year,'models_agree':checks})
    summary_by_year = hist.groupby('year').agg(events=('models_agree','size'),model_supported=('models_agree','sum'))
    summary_by_year.to_csv(out/'03_event_year_summary.csv')
    print('\n=== CH-AWS EVENTS ===',flush=True)
    print('559 events; both models RH 1..100% and <=15 %-point disagreement:',int(checks.sum()),flush=True)
    print('Not yet supported:',int((~checks).sum()),flush=True)
    print(summary_by_year.to_string(),flush=True)
    print('\nFIRST 15 EVENTS:',flush=True)
    print(data[['time','TA_site_C','RH_original_pct','era5_RH_pct','era5_land_RH_pct',
                'RH_two_model_absdiff_pctpoints','decision']].head(15).round(3).to_string(index=False),flush=True)
    report = {
        'site':SITE,'source_candidate':str(root/SITE/'forcing'/'merged_multisource_11_v07a'),
        'source_candidate_sha256':meta['candidate_sha256'],
        'reference_provider':'Open-Meteo historical archive; explicitly models era5 and era5_land; NOT independent observations',
        'reference_time_UTC_offset_hours':int(utc_offset),
        'reference_time_rule':'FLUXNET local standard time=UTC+offset; DST NOT APPLIED; manual clock verification required',
        'reference_site_coords':{'lat':LAT,'lon':LON},
        'event_count':int(len(data)),
        'candidate_consistency_agreement_threshold_pct_points':15,
        'both_models_support_count':int(checks.sum()),
        'not_supported_count':int((~checks).sum()),
        'status':'REVIEW_ONLY_NO_FORCING_WRITTEN',
        'limitations':['hourly reference interpolated to half-hour','reference model topography and height mismatch',
                       'ERA5 and ERA5-Land are related reanalyses, not independent measurements',
                       'not approval of corrections, not a ready-to-use DATM']
    }
    (out/'04_stage09_status.json').write_text(json.dumps(report,indent=2))
    print('\nReports:',out,flush=True)
    print('NO forcing CSV changed; NO RH clipping; NO DATM.',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['fetch','assess'])
    p.add_argument('--out',type=Path,default=OUT)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--site-utc-offset-hours',type=int,choices=[0,1,2],default=1,
                   help='Swiss FLUXNET site LOCAL STANDARD time offset from UTC; default +1. No DST.')
    a=p.parse_args()
    if a.mode=='fetch':fetch(a.out)
    else:assess(a.out,a.root,a.site_utc_offset_hours)


if __name__=='__main__':
    main()

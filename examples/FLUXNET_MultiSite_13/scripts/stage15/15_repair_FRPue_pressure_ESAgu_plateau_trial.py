#!/usr/bin/env python3
"""Stage 15. Make a NON-DESTRUCTIVE, site-specific seven-record meteorology trial.

Input selection:
 - FR-Pue: 13-site QC v5
 - ES-Agu: Stage 12 candidate (already repaired 2016 pressure / 2014 15:00)

Repairs proposed, conditional on exact time/value/QC/neighbor checks:
 - FR-Pue 2006-07-13 15:30 and 16:00: PSRF linearly interpolated between
   15:00 and 16:30, preserving TA/VPD and updating QBOT.
 - FR-Pue 2006-07-25 19:00: PSRF interpolated between 18:30 and 19:30,
   preserving TA/VPD and updating QBOT.
 - ES-Agu 2014-06-26 13:00,13:30,14:00,14:30: interpolate paired TA/VPD
   between station 12:30 and Stage12's independently reviewed 15:00 ERA
   estimate, then update TBOT/QBOT. Four identical original QC=1 TA/VPD
   values are a suspected erroneous fill plateau.

--check writes NOTHING. --run requires a NEW destination under experiments.
This is not approval for use in production DATM or spin-up.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES')
EXPERIMENTS = ROOT / 'experiments'
STAGE12 = EXPERIMENTS / 'FLUXNET_MultiSite_13_targeted_TA_PA_trial_v1_20261014'
V5 = EXPERIMENTS / 'FLUXNET_MultiSite_13_qc_v5_candidate_20261014'
RAW_MANIFEST = Path.home() / 'FLUXNET_13_input_audit/site_input_summary.csv'
SELECTED = {
    'FR-Pue': (2000, 2025, V5 / 'FR-Pue/forcing/processed_v5/FR-Pue_CLM_forcing_2000_2025.csv'),
    'ES-Agu': (2006, 2024, STAGE12 / 'ES-Agu_CLM_forcing_2006_2024_targeted_trial.csv'),
}
REQUIRED = ['time', 'TA_USE', 'VPD_USE', 'TBOT', 'QBOT', 'PSRF',
            'FSDS', 'FLDS', 'WIND', 'PRECTmms']


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def assert_near(actual, expected, tolerance, description):
    if not np.isfinite(actual) or abs(float(actual) - expected) > tolerance:
        raise ValueError(f'{description}: got {actual}, expected {expected} ± {tolerance}. '
                         'Input/source version differs; aborting.')


def humidity(t_c, vpd_hpa, p_pa):
    es_hpa = 6.112 * np.exp(17.67 * t_c / (t_c + 243.5))
    ea_pa = (es_hpa - vpd_hpa) * 100.0
    rh = 100 * (es_hpa - vpd_hpa) / es_hpa
    q = 0.622 * ea_pa / (p_pa - 0.378 * ea_pa)
    return float(rh), float(q)


def load_selected(site):
    first, last, path = SELECTED[site]
    if not path.is_file():
        raise FileNotFoundError(f'Missing selected parent candidate: {path}')
    d = pd.read_csv(path, low_memory=False)
    missing = set(REQUIRED) - set(d.columns)
    if missing:
        raise RuntimeError(f'{site} forcing missing columns {missing} (ZBOT is deliberately NOT required)')
    d['time'] = pd.to_datetime(d['time'], errors='raise')
    calendar = pd.date_range(f'{first}-01-01', f'{last}-12-31 23:30', freq='30min')
    calendar = calendar[~((calendar.month == 2) & (calendar.day == 29))]
    if len(d) != len(calendar) or not np.array_equal(d.time.to_numpy(), calendar.to_numpy()):
        raise ValueError(f'{site} NO_LEAP chronology incorrect: got {len(d)}, expected {len(calendar)}')
    for c in REQUIRED[1:]:
        d[c] = pd.to_numeric(d[c], errors='raise')
        if not np.isfinite(d[c].to_numpy()).all():
            raise ValueError(f'{site}: parent forcing contains nonfinite {c}')
    # Spot-check full parent physics; do not silently stack a repair on inconsistent inputs.
    t = d.TA_USE.to_numpy(); v = d.VPD_USE.to_numpy(); p = d.PSRF.to_numpy()
    es = 6.112 * np.exp(17.67 * t / (t + 243.5))
    ea = es - v
    q = 0.622 * ea * 100 / (p - 0.378 * ea * 100)
    rh = 100 * ea / es
    if (not np.isclose(d.TBOT.to_numpy(), t + 273.15, atol=1e-5, rtol=0).all()
        or not np.isclose(d.QBOT.to_numpy(), q, atol=1e-9, rtol=1e-6).all()
        or not ((rh >= 0) & (rh <= 100.05)).all()):
        raise ValueError(f'{site} parent physics/QBOT/TBOT inconsistency detected')
    return d, path


def source(site, manifest):
    rows = manifest.loc[manifest.site.eq(site)]
    if len(rows) != 1:
        raise ValueError(f'Manifest needs exactly one row for {site}; found {len(rows)}')
    fp = Path(rows.iloc[0].primary_file)
    if not fp.is_file():
        raise FileNotFoundError(fp)
    columns = set(pd.read_csv(fp, nrows=0).columns)
    wanted = ['TIMESTAMP_START', 'TA_F', 'TA_F_QC', 'VPD_F', 'VPD_F_QC',
              'PA_F', 'PA_F_QC', 'PA_ERA', 'TA_ERA', 'VPD_ERA']
    use = [c for c in wanted if c in columns]
    if not {'TIMESTAMP_START', 'TA_F', 'TA_F_QC', 'VPD_F', 'VPD_F_QC', 'PA_F', 'PA_F_QC'}.issubset(use):
        raise ValueError(f'{site}: raw FLUXMET source missing required original QC fields')
    raw = pd.read_csv(fp, usecols=use, dtype={'TIMESTAMP_START': str}, low_memory=False)
    raw['time'] = pd.to_datetime(raw.TIMESTAMP_START.str.strip().str.replace(r'\.0$', '', regex=True),
                                 format='%Y%m%d%H%M', errors='raise')
    if raw.time.duplicated().any():
        raise ValueError(f'{site}: duplicate original timestamps')
    raw = raw.set_index('time').drop(columns='TIMESTAMP_START')
    for col in raw:
        raw[col] = pd.to_numeric(raw[col], errors='coerce')
        raw.loc[(raw[col] <= -9990) | ~np.isfinite(raw[col]), col] = np.nan
    return raw, fp


def index(d, timestamp, site):
    target = pd.Timestamp(timestamp)
    selected = d.index[d.time.eq(target)]
    if len(selected) != 1:
        raise RuntimeError(f'{site}: unexpected count for {timestamp}: {len(selected)}')
    return int(selected[0])


def apply(d, raw, site, timestamp, updates, rule, ledger):
    i = index(d, timestamp, site)
    dt = d.at[i, 'time']
    if dt not in raw.index:
        raise RuntimeError(f'{site}: original source missing {dt}')
    row = raw.loc[dt]
    if isinstance(row, pd.DataFrame):
        raise RuntimeError('Original timestamp duplicated')
    original = {c: float(d.at[i, c]) for c in ('TA_USE', 'VPD_USE', 'TBOT', 'QBOT', 'PSRF')}
    for field, value in updates.items():
        if field not in ('TA_USE', 'VPD_USE', 'PSRF'):
            raise ValueError('Attempted modification outside approved fields')
        d.at[i, field] = float(value)
    tc = float(d.at[i, 'TA_USE']); v = float(d.at[i, 'VPD_USE']); pressure = float(d.at[i, 'PSRF'])
    rh, q = humidity(tc, v, pressure)
    es = 6.112 * np.exp(17.67 * tc / (tc + 243.5))
    if not (-30 < tc < 45 and 0 <= v < es and 1 <= rh <= 100 and
            70000 <= pressure <= 110000 and 0 < q < 0.06):
        raise ValueError(f'{site} {timestamp}: proposed thermodynamics invalid: T={tc}, VPD={v}, P={pressure}, RH={rh}, Q={q}')
    d.at[i, 'TBOT'] = tc + 273.15
    d.at[i, 'QBOT'] = q
    modified = {c: float(d.at[i, c]) for c in original}
    record = {'site': site, 'time': dt.isoformat(sep=' '), 'rule': rule,
              'original_TA_F_QC': row.get('TA_F_QC', np.nan),
              'original_VPD_F_QC': row.get('VPD_F_QC', np.nan),
              'original_PA_F_QC': row.get('PA_F_QC', np.nan),
              'raw_TA_F': row.get('TA_F', np.nan), 'raw_VPD_F': row.get('VPD_F', np.nan),
              'raw_PA_F_kPa': row.get('PA_F', np.nan),
              'raw_PA_ERA_kPa': row.get('PA_ERA', np.nan),
              'raw_TA_ERA_C': row.get('TA_ERA', np.nan),
              'raw_VPD_ERA_hPa': row.get('VPD_ERA', np.nan),
              **{'old_' + c: val for c, val in original.items()},
              **{'trial_' + c: val for c, val in modified.items()},
              'trial_RH_pct': rh, 'scientific_status': 'REVIEW_NOT_APPROVED'}
    ledger.append(record)
    print(f'{site:6s} {timestamp} | {rule} | '
          f'P {original["PSRF"]:.1f}->{pressure:.1f} Pa; '
          f'T {original["TA_USE"]:.3f}->{tc:.3f} C; '
          f'VPD {original["VPD_USE"]:.3f}->{v:.3f} hPa; RH {rh:.1f}%')


def propose(manifest):
    parents = {}; outputs = {}; ledger = []; raw_inputs = {}
    for site in SELECTED:
        d, parent_path = load_selected(site)
        raw, raw_path = source(site, manifest)
        parents[site] = {'candidate_file': str(parent_path), 'candidate_sha256': sha256(parent_path),
                         'original_FLUXMET': str(raw_path), 'original_FLUXMET_sha256': sha256(raw_path)}
        outputs[site] = d.copy(deep=True)
        raw_inputs[site] = raw
    original_forcing = {site: d.copy(deep=True) for site, d in outputs.items()}

    # FR-Pue: two recorded pressure outliers in a 3-step block, use stable
    # uncontaminated 15:00 / 16:30 endpoints, do not interpolate 15:30 via 16:00.
    site = 'FR-Pue'; d = outputs[site]; raw = raw_inputs[site]
    left = index(d, '2006-07-13 15:00', site)
    right = index(d, '2006-07-13 16:30', site)
    assert_near(d.at[left, 'PSRF'], 98300, 0.1, 'Jul13 left pressure')
    assert_near(d.at[right, 'PSRF'], 98400, 0.1, 'Jul13 right pressure')
    for fraction, (ts, old) in enumerate((('2006-07-13 15:30', 94800),
                                           ('2006-07-13 16:00', 96900)), start=1):
        i = index(d, ts, site)
        assert_near(d.at[i, 'PSRF'], old, 0.1, f'FR-Pue {ts} existing pressure')
        if float(raw.loc[pd.Timestamp(ts), 'PA_F_QC']) != 0:
            raise ValueError('FR-Pue original pressure QC changed; refusing repair')
        estimate = (1 - fraction / 3) * d.at[left, 'PSRF'] + fraction / 3 * d.at[right, 'PSRF']
        apply(d, raw, site, ts, {'PSRF': estimate},
              'bounded_linear_PSRF_from_15:00_to_16:30_retain_TA_VPD', ledger)

    # FR-Pue July25: one isolated 94.7kPa against 98.6/98.5 at 18:30/19:30.
    left = index(d, '2006-07-25 18:30', site)
    right = index(d, '2006-07-25 19:30', site)
    i = index(d, '2006-07-25 19:00', site)
    assert_near(d.at[left, 'PSRF'], 98600, 0.1, 'Jul25 left pressure')
    assert_near(d.at[right, 'PSRF'], 98500, 0.1, 'Jul25 right pressure')
    assert_near(d.at[i, 'PSRF'], 94700, 0.1, 'Jul25 isolated pressure')
    if float(raw.loc[pd.Timestamp('2006-07-25 19:00'), 'PA_F_QC']) != 0:
        raise ValueError('FR-Pue original pressure QC changed; refusing repair')
    apply(d, raw, site, '2006-07-25 19:00',
          {'PSRF': (d.at[left, 'PSRF'] + d.at[right, 'PSRF']) / 2},
          'bounded_linear_PSRF_from_18:30_to_19:30_retain_TA_VPD', ledger)

    # ES-Agu: original 4x identical QC=1 TA and VPD, physically implausible
    # plateau bracketed by 12:30 QC=0 station and 15:00 Stage12 ERA-repaired pair.
    site = 'ES-Agu'; d = outputs[site]; raw = raw_inputs[site]
    left = index(d, '2014-06-26 12:30', site)
    right = index(d, '2014-06-26 15:00', site)
    for c, value in [('TA_USE', 27.987), ('VPD_USE', 24.160)]:
        assert_near(d.at[left, c], value, 0.001, 'ES-Agu left endpoint ' + c)
    for c, value in [('TA_USE', 27.259), ('VPD_USE', 23.068)]:
        assert_near(d.at[right, c], value, 0.001, 'ES-Agu repaired right endpoint ' + c)
    if (raw.loc[pd.Timestamp('2014-06-26 12:30'), 'TA_F_QC'] != 0 or
        raw.loc[pd.Timestamp('2014-06-26 12:30'), 'VPD_F_QC'] != 0):
        raise ValueError('ES-Agu left endpoint no longer official QC0')
    for j, ts in enumerate(('2014-06-26 13:00', '2014-06-26 13:30',
                             '2014-06-26 14:00', '2014-06-26 14:30'), start=1):
        i = index(d, ts, site)
        for c, value in [('TA_USE', 18.802), ('VPD_USE', 5.163)]:
            assert_near(d.at[i, c], value, 0.001, f'ES-Agu plateau {ts} {c}')
        row = raw.loc[pd.Timestamp(ts)]
        if any(float(row[f'{c}_F_QC']) != 1.0 for c in ['TA', 'VPD']):
            raise ValueError(f'ES-Agu {ts}: source QC not 1/1; refuse proposal')
        fraction = j / 5
        updates = {c: (1-fraction)*d.at[left, c] + fraction*d.at[right, c]
                   for c in ('TA_USE', 'VPD_USE')}
        apply(d, raw, site, ts, updates,
              'interpolate_paired_TA_VPD_between_QC0_12:30_and_Stage12_ERA_15:00', ledger)

    # Full invariance checks: EXACTLY 7 half-hours and only permitted fields.
    expected = {
        'FR-Pue': set(pd.to_datetime(['2006-07-13 15:30', '2006-07-13 16:00', '2006-07-25 19:00'])),
        'ES-Agu': set(pd.to_datetime(['2014-06-26 13:00', '2014-06-26 13:30',
                                     '2014-06-26 14:00', '2014-06-26 14:30'])),
    }
    for site, d in outputs.items():
        base = original_forcing[site]
        touched = np.zeros(len(d), dtype=bool)
        for c in d.columns:
            if c == 'time':
                if not d[c].equals(base[c]):
                    raise AssertionError(f'{site} timestamp changed')
                continue
            if c not in ('TA_USE', 'VPD_USE', 'TBOT', 'QBOT', 'PSRF'):
                if not d[c].equals(base[c]):
                    raise AssertionError(f'{site} unexpectedly altered other column {c}')
                continue
            touched |= ~np.isclose(d[c].to_numpy(dtype=float), base[c].to_numpy(dtype=float),
                                   rtol=0, atol=1e-12, equal_nan=True)
        found = set(d.time.loc[touched])
        if found != expected[site]:
            raise AssertionError(f'{site} expected changed {sorted(expected[site])} but got {sorted(found)}')
        for ts in expected[site]:
            i = index(d, ts, site)
            t = float(d.at[i, 'TA_USE']); v = float(d.at[i, 'VPD_USE']); p = float(d.at[i, 'PSRF'])
            rh, q = humidity(t, v, p)
            if not (1 <= rh <= 100 and
                    np.isclose(q, d.at[i, 'QBOT'], atol=1e-10, rtol=1e-8) and
                    np.isclose(d.at[i, 'TBOT'], t+273.15, atol=1e-9, rtol=0)):
                raise ValueError(f'{site} physical humidity check failed at {ts}')
    if len(ledger) != 7:
        raise AssertionError(f'Expected precisely 7 replacement records, got {len(ledger)}')
    return outputs, parents, pd.DataFrame(ledger)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--check', action='store_true', help='Read-only preflight; no output')
    g.add_argument('--run', action='store_true', help='Write NEW independently tagged candidate')
    p.add_argument('--out', type=Path, help='Unused new directory directly under experiments, required for --run')
    p.add_argument('--manifest', type=Path, default=RAW_MANIFEST)
    args = p.parse_args()
    if not args.manifest.is_file():
        raise FileNotFoundError(f'Missing existing Stage03a manifest: {args.manifest}')
    manifest = pd.read_csv(args.manifest)
    if not {'site', 'primary_file'}.issubset(manifest.columns):
        raise ValueError('Input manifest lacks site/primary_file columns')
    outputs, parents, ledger = propose(manifest)
    print('\nSTAGE15 CHECK: 2 sites, exactly 7 half-hours; thermodynamics and parent preservation PASS')
    print('FR-Pue: 3 pressure corrections. ES-Agu: 4 paired TA/VPD plateau corrections.')
    print('DE-Lnf, DE-Gri, FI-Let and the other sites remain unchanged and require source review.')
    if args.check:
        print('CHECK COMPLETE: read-only; no forcing/reports written.')
        return
    if args.out is None:
        raise ValueError('--run requires --out NEW_DIRECTORY')
    destination = args.out.resolve()
    allowed_parent = EXPERIMENTS.resolve()
    if destination.parent != allowed_parent:
        raise RuntimeError('--out must be a NEW direct child of the CLM_FATES/experiments directory')
    if destination.exists():
        raise FileExistsError(f'Cannot overwrite existing directory {destination}; use a new tag')
    destination.mkdir(parents=False, exist_ok=False)
    try:
        written = {}
        for site, frame in outputs.items():
            first, last, _ = SELECTED[site]
            fn = destination / f'{site}_CLM_forcing_{first}_{last}_stage15_trial.csv'
            frame.to_csv(fn, index=False, date_format='%Y-%m-%d %H:%M:%S')
            written[site] = {'path': str(fn), 'sha256': sha256(fn), 'rows': len(frame)}
        ledger.to_csv(destination / 'seven_record_provenance_ledger.csv', index=False)
        manifest_data = {
            'created_UTC': datetime.now(timezone.utc).isoformat(),
            'script_sha256': sha256(Path(__file__).resolve()),
            'status': 'CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW_NOT_APPROVED',
            'source_input': parents,
            'outputs': written,
            'changes': 7,
            'do_not_merge_into_old_QC_candidates': True,
            'remaining_issues': ['DE-Lnf 2023-06-22 surrounding TA irregularity',
                                 'DE-Gri repeated QC1 fill patterns and ERA source transitions',
                                 'FI-Let winter QC1/QC2 source transitions',
                                 'Other temperature flags and very-low RH records',
                                 'Rainfall extreme event/source QC audits',
                                 'BIF/ZBOT and surface/PFT checks later'],
        }
        (destination / 'input_output_SHA256_manifest.json').write_text(
            json.dumps(manifest_data, indent=2, ensure_ascii=False))
        (destination / 'SCIENCE_REVIEW_NOT_APPROVED.txt').write_text(
            'Experimental site-specific targeted QC candidate ONLY. Not approved for DATM or spin-up.\n')
        print(f'TRIAL COMPLETE: {destination}')
        print('SCIENCE STATUS: CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW_NOT_APPROVED')
    except Exception:
        print('Candidate output directory might be partially written. Do NOT reuse or overwrite it.', file=sys.stderr)
        raise


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'ERROR: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(1)
#!/usr/bin/env python3
"""READ-ONLY 1000-year diagnostics for five FLUXNET_MultiSite_6 spin-ups.

The 500->1000 continuation retains the ORIGINAL case name:
    <SITE>_FATES_SPINUP500

Reuse the tested repository script 10_compare_six_site_latest_complete_cycle.py
for archive indexing, full forcing-cycle alignment, EC conversions, and pairing.

Outputs (for each site):
  <SITE>_01_carbon_pools_annual_mean.png
  <SITE>_02_carbon_pools_last250years.png
  <SITE>_GPP_NEE_monthly_overview.png
  <SITE>_carbon_annual_means.csv
  <SITE>_convergence_metrics.csv
  <SITE>_monthly_FATES_vs_EC.csv
  <SITE>_monthly_metrics.csv
  <SITE>_metadata.json

The script NEVER alters CIME cases or model history/restart files.
Run on IRIDIS6 (prefer a Slurm compute node for thousands of NetCDF reads).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import sys
import traceback
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from netCDF4 import Dataset

SITES = {
    'RU-Fyo': (1998, 2025),
    'DE-Tha': (1996, 2025),
    'DK-Sor': (1996, 2024),
    'NL-Loo': (1997, 2025),
    'IL-Yat': (2000, 2024),
}
N_YEARS = 1000
CANDIDATES = [
    'TOTECOSYSC', 'TOTVEGC', 'TOTSOMC', 'TOTLITC',
    'FATES_VEGC', 'FATES_STOREC', 'FATES_STRUCTC',
    'TOTROOTC', 'SOILC', 'TOTSOILC', 'FATES_NONSTRUCTC',
    'DEADC', 'LIVESTEMC', 'LEAFC',
]


def get_reference_script(arg):
    """Find the existing GitHub script; do not silently download/modify it."""
    rel = Path('examples/FLUXNET_MultiSite_6/scripts/10_compare_six_site_latest_complete_cycle.py')
    candidates = []
    if arg.reference_script:
        candidates.append(arg.reference_script)
    if arg.repo:
        candidates.append(arg.repo / rel)
    candidates += [
        Path.cwd() / rel,
        Path.cwd() / 'scripts' / rel.name,
        Path.cwd() / rel.name,
        Path.home() / 'CLM-FATES-single-site-workflows' / rel,
        Path.home() / rel.name,
        Path(__file__).parent / rel.name,
    ]
    for path in candidates:
        if path.is_file():
            return path.resolve()
    raise FileNotFoundError(
        'Cannot locate existing reference plotting script 10_compare_six_site_latest_complete_cycle.py. '
        'Clone the GitHub repository and provide --repo /path/to/CLM-FATES-single-site-workflows, '
        'or provide --reference-script /absolute/path/10_compare_six_site_latest_complete_cycle.py.'
    )


def load_reference(path):
    spec = importlib.util.spec_from_file_location('six_site_reference_comparison', str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unit_type(units):
    """Convert carbon pool kg C / m2 to g C / m2; retain other units unchanged."""
    plain = units.lower().replace(' ', '').replace('**', '^').replace('_', '')
    if ('kg' in plain and ('c' in plain or 'carbon' in plain) and
            ('m-2' in plain or 'm^-2' in plain or '/m2' in plain or '/m^2' in plain)):
        return 1000.0, 'g C m$^{-2}$', 'g C m-2'
    if (('gc' in plain or 'gcarbon' in plain) and
            ('m-2' in plain or 'm^-2' in plain or '/m2' in plain or '/m^2' in plain)):
        return 1.0, 'g C m$^{-2}$', 'g C m-2'
    # If unit metadata are absent, never assert that raw numbers are in g C.
    return 1.0, units if units else 'unit not recorded', units if units else 'unknown'


def point_time_mean(v):
    """Annual mean of only scalar (single-point) history fields with time axis."""
    dims = v.dimensions
    if 'time' not in dims:
        return np.nan
    arr = np.ma.asarray(v[:], dtype=np.float64).filled(np.nan)
    arr = np.asarray(arr, dtype=np.float64)
    arr = np.moveaxis(arr, dims.index('time'), 0)
    if arr.ndim == 0 or not len(arr) or np.prod(arr.shape[1:]) != 1:
        return np.nan
    vals = arr.reshape(len(arr))
    vals = vals[np.isfinite(vals)]
    return float(vals.mean()) if len(vals) else np.nan


def contiguous_found(found, start, n):
    expected = list(range(start, start + n))
    missing = [y for y in expected if y not in found]
    if missing:
        raise RuntimeError(
            f'Incomplete archive: missing {len(missing)} of {n} annual h0a files; '
            f'first missing model years: {missing[:12]}. '
            'Do not interpret this as a complete 1000-year spin-up.'
        )
    return expected


def extract_annual_carbon(found, years, site):
    # Use exact candidate names where the variable has no cohort/PFT dimension.
    # The carbon pool history might use other names depending on FATES config.
    rows = []
    chosen = None
    unit_meta = {}
    skipped = set()
    for i, yr in enumerate(years):
        with Dataset(found[yr], 'r') as ds:
            if chosen is None:
                chosen = []
                for name in CANDIDATES:
                    if name not in ds.variables:
                        continue
                    v = ds.variables[name]
                    if 'time' in v.dimensions and np.prod([
                        ds.dimensions[d].size for d in v.dimensions if d != 'time'
                    ]) == 1:
                        units = str(getattr(v, 'units', '')).strip()
                        factor, plot_unit, csv_unit = unit_type(units)
                        chosen.append(name)
                        unit_meta[name] = {'original_units': units,
                                           'factor': factor,
                                           'plot_units': plot_unit,
                                           'csv_units': csv_unit}
                    else:
                        skipped.add(f'{name}: non-scalar dimensions {v.dimensions}')
                if not chosen:
                    available = [x for x in ds.variables if
                                 any(z in x.upper() for z in ('C', 'SOIL', 'VEG', 'FATES'))]
                    raise RuntimeError(
                        'No scalar carbon-pool variables among configured candidates. '
                        'Inspect `ncdump -h <first annual h0a file>`. '
                        f'Example variable names: {available[:60]}'
                    )
                print(f'  Carbon variables ({len(chosen)}): {chosen}', flush=True)
                for warn in sorted(skipped):
                    print(f'  SKIP {warn}', flush=True)
            row = {'Site': site, 'ModelYear': int(yr),
                   'SpinupYear': int(yr - years[0] + 1)}
            for name in chosen:
                if name not in ds.variables:
                    raise RuntimeError(f'{found[yr]} has no {name}: inconsistent history')
                original_units = str(getattr(ds.variables[name], 'units', '')).strip()
                if original_units != unit_meta[name]['original_units']:
                    raise RuntimeError(f'{name} units changed between annual files: '
                                       f'{original_units!r} vs {unit_meta[name]["original_units"]!r}')
                row[name] = point_time_mean(ds.variables[name]) * unit_meta[name]['factor']
            rows.append(row)
        if (i + 1) % 100 == 0:
            print(f'  Read {i + 1}/{len(years)} annual carbon files', flush=True)
    return pd.DataFrame(rows), chosen, unit_meta


def safe_relative_pct(new, old):
    if not np.isfinite(new) or not np.isfinite(old) or abs(old) < 1e-8:
        return float('nan')
    return 100.0 * (new - old) / abs(old)


def trend_last(series, window):
    a = np.asarray(series[-window:], dtype=float)
    x = np.arange(len(a), dtype=float)
    ok = np.isfinite(a)
    if ok.sum() < max(15, int(window * .8)):
        return float('nan'), float('nan')
    slope = float(np.polyfit(x[ok], a[ok], 1)[0])
    m = float(np.nanmean(a))
    relative = float('nan') if abs(m) < 1e-8 else 100.0 * slope * window / abs(m)
    return slope, relative


def cycle_end_at(total, n):
    """(start_idx, end_idx) of latest aligned complete cycle within total years."""
    completed = total // n
    if completed < 1:
        raise ValueError('No complete forcing cycles')
    start_idx = (completed - 1) * n
    return start_idx, start_idx + n


def compute_convergence(carbon, names, units, forcing_len):
    """All cycle comparisons use the SAME original forcing-year phase."""
    records = []
    n = len(carbon)
    last_start, last_end = cycle_end_at(n, forcing_len)
    prev_start, prev_end = last_start - forcing_len, last_start
    before_start, before_end = cycle_end_at(min(500, n), forcing_len)
    for name in names:
        v = carbon[name].to_numpy(dtype=float)
        at500 = v[499] if n >= 500 else np.nan
        at1000 = v[999] if n >= 1000 else np.nan
        sl30, rel30 = trend_last(v, 30)
        sl100, rel100 = trend_last(v, 100)
        if prev_start >= 0:
            prev, cur = v[prev_start:prev_end], v[last_start:last_end]
            valid = np.isfinite(prev) & np.isfinite(cur)
            # Difference between corresponding forcing years in neighbouring cycles.
            cycle_abs_pct = (100.0 * np.mean(np.abs(cur[valid] - prev[valid])) /
                             max(float(np.mean(np.abs(prev[valid]))), 1e-8)) if valid.sum() >= forcing_len * .8 else np.nan
            cur_mean = float(np.nanmean(cur))
            prev_mean = float(np.nanmean(prev))
        else:
            cycle_abs_pct, prev_mean, cur_mean = np.nan, np.nan, np.nan
        if before_start >= 0:
            before_mean = float(np.nanmean(v[before_start:before_end]))
        else:
            before_mean = np.nan
        records.append({
            'Variable': name,
            'Units': units[name]['csv_units'],
            'Value_at_spinup_year_500': at500,
            'Value_at_spinup_year_1000': at1000,
            'Unaligned_1000_vs_500_pct': safe_relative_pct(at1000, at500),
            'Last30y_slope_per_model_year': sl30,
            'Last30y_relative_trend_pct_per_30y': rel30,
            'Last100y_slope_per_model_year': sl100,
            'Last100y_relative_trend_pct_per_100y': rel100,
            'Last_two_complete_cycles_mean_abs_change_pct': cycle_abs_pct,
            'Last_cycle_mean': cur_mean,
            'Preceding_cycle_mean': prev_mean,
            'Latest_complete_cycle_mean_at_500y': before_mean,
            'Latest_complete_cycle_mean_at_1000y': cur_mean,
            'Aligned_cycle_means_change_500_to_1000_pct': safe_relative_pct(cur_mean, before_mean),
            'Last_complete_cycle_spinup_start': last_start + 1,
            'Last_complete_cycle_spinup_end': last_end,
            'Preceding_complete_cycle_spinup_start': prev_start + 1 if prev_start >= 0 else np.nan,
            'Preceding_complete_cycle_spinup_end': prev_end if prev_start >= 0 else np.nan,
            'At500_complete_cycle_spinup_start': before_start + 1,
            'At500_complete_cycle_spinup_end': before_end,
        })
    return pd.DataFrame(records)


def carbon_plot(carbon, names, units, site, out, years_to_plot, filename, title):
    preferred = names[:6]
    if not preferred:
        raise RuntimeError('No available carbon variables for plotting')
    ncols = 2
    nrows = math.ceil(len(preferred) / ncols)
    fig, axs = plt.subplots(nrows, ncols, figsize=(16, 4.0 * nrows),
                            sharex=True, squeeze=False)
    x = carbon['SpinupYear'].to_numpy()
    for ax, name in zip(axs.flat, preferred):
        ax.plot(x, carbon[name].to_numpy(), lw=1.35)
        ax.axvline(500, color='0.45', ls='--', lw=1, label='500-year checkpoint')
        ax.axvspan(900, 1000, color='0.8', alpha=.15)
        ax.set_title(name)
        ax.set_ylabel(units[name]['plot_units'])
        ax.set_xlim(years_to_plot)
        ax.grid(alpha=.22)
    for ax in list(axs.flat)[len(preferred):]:
        ax.set_visible(False)
    for ax in axs[-1]:
        ax.set_xlabel('Spin-up year (elapsed model years)')
    fig.suptitle(f'{site} | {title}\n500-year checkpoint dashed; last 100 years lightly shaded',
                 fontsize=14)
    fig.tight_layout()
    path = out / filename
    fig.savefig(path, dpi=230, bbox_inches='tight')
    plt.close(fig)
    return path


def monthly_overview(monthly, site, model_years, ec_years, out, core):
    fig, axs = plt.subplots(2, 1, figsize=(16, 8), sharex=True)
    stats = []
    for ax, flux in zip(axs, ('GPP', 'NEE')):
        obs, mod = f'EC_{flux}', f'FATES_{flux}'
        scores = core.metrics(monthly[obs], monthly[mod])
        stats.append({'Site': site, 'Flux': flux, 'Scale': 'monthly', **scores,
                      'ModelCycleFirst': model_years[0],
                      'ModelCycleLast': model_years[-1]})
        ax.plot(monthly['date'], monthly[obs], label='FLUXNET EC', lw=1.45)
        ax.plot(monthly['date'], monthly[mod], label='CLM-FATES', lw=1.45)
        if flux == 'NEE':
            ax.axhline(0, color='0.5', ls='--', lw=.8)
        ax.set_ylabel(f'{flux} (g C m$^{{-2}}$ d$^{{-1}}$)')
        ax.set_title(f'{flux} | monthly N={scores["N"]}, R²={scores["R2"]:.3f}, '
                     f'RMSE={scores["RMSE"]:.3f}')
        ax.grid(alpha=.2)
        ax.legend(frameon=False)
    import matplotlib.dates as mdates
    axs[-1].xaxis.set_major_locator(mdates.YearLocator(2))
    axs[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    axs[-1].set_xlim(pd.Timestamp(ec_years[0], 1, 1), pd.Timestamp(ec_years[1]+1, 1, 1))
    axs[-1].set_xlabel('Observed FLUXNET year (forcing chronology)')
    fig.suptitle(f'{site} | 1000-year spin-up: last COMPLETE forcing cycle\n'
                 f'Model years {model_years[0]}–{model_years[-1]} '
                 f'mapped to EC years {ec_years[0]}–{ec_years[1]}', fontsize=13)
    fig.tight_layout()
    path = out / f'{site}_GPP_NEE_monthly_overview.png'
    fig.savefig(path, dpi=250, bbox_inches='tight')
    plt.close(fig)
    return pd.DataFrame(stats), path


def process_site(site, args, core):
    first, last = SITES[site]
    case_name = f'{site}_FATES_SPINUP500'  # critical: DO NOT rename continuation case
    case_path = args.cases_root / case_name
    core.verify_stream(case_path, first, last)
    found = core.history_index(args.archive_root, case_name)
    years = contiguous_found(found, first, N_YEARS)
    print(f'  VERIFIED {N_YEARS} continuous annual h0a files ({years[0]}–{years[-1]}); '
          f'total archive index {len(found)}', flush=True)
    # Explicitly read exactly 1000 model years, even if the archive later grows.
    out = args.output_root / site
    out.mkdir(parents=True, exist_ok=True)
    carbon, names, units = extract_annual_carbon(found, years, site)
    csv_carbon = out / f'{site}_carbon_annual_means.csv'
    carbon.to_csv(csv_carbon, index=False)
    diag = compute_convergence(carbon, names, units, last-first+1)
    csv_diag = out / f'{site}_convergence_metrics.csv'
    diag.to_csv(csv_diag, index=False)
    carbon_plot(carbon, names, units, site, out, (1, 1000),
                f'{site}_01_carbon_pools_annual_mean.png',
                'annual mean carbon pools, years 1–1000')
    carbon_plot(carbon, names, units, site, out, (750, 1000),
                f'{site}_02_carbon_pools_last250years.png',
                'annual mean carbon pools, years 750–1000')

    model_cycle_index, model_years = core.latest_complete_cycle(
        {yr: found[yr] for yr in years}, first, last
    )
    print(f'  Latest COMPLETE forcing cycle: {model_years[0]}–{model_years[-1]} '
          f'(EC years {first}–{last}), cycle number {model_cycle_index+1}', flush=True)
    rawdir = args.sites_root / site / 'forcing' / 'raw'
    obs_path, gpp_col = core.find_flux_file(
        rawdir, args.gpp_preference, args.obs_csv.get(site)
    )
    model = core.fates_daily([(yr, found[yr]) for yr in model_years], first, last)
    obs = core.ec_daily(obs_path, gpp_col, first, last, args.min_halfhour)
    daily = model.merge(obs, on='date', how='left', validate='one_to_one')
    if len(daily) != (last-first+1)*365:
        raise RuntimeError('Expected 365 times forcing-cycle years daily values')
    gpp_m = core.paired_monthly(daily, 'EC_GPP', 'FATES_GPP', args.min_days)
    nee_m = core.paired_monthly(daily, 'EC_NEE', 'FATES_NEE', args.min_days)
    monthly = gpp_m.merge(nee_m, on='date', how='outer', validate='one_to_one')
    for flux in ('GPP', 'NEE'):
        if (monthly[f'EC_{flux}'].notna() & monthly[f'FATES_{flux}'].notna()).sum() < 2:
            raise RuntimeError(f'Insufficient paired monthly {flux} values')
    monthly.to_csv(out / f'{site}_monthly_FATES_vs_EC.csv', index=False)
    monthly_scores, path = monthly_overview(
        monthly, site, model_years, (first,last), out, core
    )
    monthly_scores.to_csv(out / f'{site}_monthly_metrics.csv', index=False)
    meta = {
        'site': site,
        'status': 'OK',
        'case_name': case_name,
        'spinup_years_verified': N_YEARS,
        'model_history_year_range': [years[0], years[-1]],
        'ec_forcing_year_range': [first, last],
        'latest_complete_model_cycle': [model_years[0], model_years[-1]],
        'observation_flux_csv': str(obs_path),
        'observation_gpp_column': gpp_col,
        'carbon_pool_units': units,
        'carbon_variable_names': names,
        'nee_definition': 'FATES_NEE=-FATES_NEP, EC_NEE=NEE_VUT_REF',
        'note': ('Completing 1000 years is not equivalent to equilibrium. '
                 '500 versus 1000 endpoint years are not forcing-phase matched; '
                 'prefer aligned complete-cycle metrics.'),
        'outputs': sorted(p.name for p in out.glob('*') if p.is_file()),
    }
    (out / f'{site}_metadata.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
    print('  MONTHLY GPP/NEE:', flush=True)
    print(monthly_scores[['Flux','N','R2','RMSE','Bias']].to_string(index=False), flush=True)
    print('  CONVERGENCE (percentages are diagnostics, not automatic pass/fail):', flush=True)
    interesting = diag[diag.Variable.isin(['TOTECOSYSC','TOTVEGC','TOTSOMC','TOTLITC','FATES_VEGC'])]
    if len(interesting):
        print(interesting[['Variable','Last100y_relative_trend_pct_per_100y',
                           'Last_two_complete_cycles_mean_abs_change_pct',
                           'Aligned_cycle_means_change_500_to_1000_pct']].to_string(index=False), flush=True)
    print(f'  Saved: {out}', flush=True)
    return {'Site':site,'Status':'OK','ArchiveYears':len(years),
            'ModelCycleStart':model_years[0], 'ModelCycleEnd':model_years[-1],
            'GPP_monthly_R2': float(monthly_scores.loc[monthly_scores.Flux=='GPP','R2'].iloc[0]),
            'NEE_monthly_R2': float(monthly_scores.loc[monthly_scores.Flux=='NEE','R2'].iloc[0]),
            'Directory':str(out)}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sites', nargs='+', choices=list(SITES), default=list(SITES))
    p.add_argument('--user', default='ly3n24')
    p.add_argument('--repo', type=Path,
                   help='Clone root containing examples/FLUXNET_MultiSite_6/')
    p.add_argument('--reference-script', type=Path,
                   help='Existing GitHub 10_compare_six_site_latest_complete_cycle.py')
    p.add_argument('--archive-root', type=Path)
    p.add_argument('--cases-root', type=Path)
    p.add_argument('--sites-root', type=Path)
    p.add_argument('--output-root', type=Path)
    p.add_argument('--obs-csv', nargs='*', default=[], metavar='SITE=/absolute/FLUX_HH.csv')
    p.add_argument('--gpp-preference', choices=['GPP_DT_VUT_REF','GPP_NT_VUT_REF'],
                   default='GPP_DT_VUT_REF')
    p.add_argument('--min-halfhour', type=int, default=40)
    p.add_argument('--min-days', type=int, default=20)
    args = p.parse_args()
    if args.archive_root is None:
        args.archive_root = Path(f'/scratch/{args.user}/CTSM_FATES_OUTPUTS/archive')
    if args.cases_root is None:
        args.cases_root = Path(f'/iridisfs/scratch/{args.user}/CLM_FATES/cases')
    if args.sites_root is None:
        args.sites_root = Path(f'/iridisfs/scratch/{args.user}/CLM_FATES/sites/MY_EC_SITE')
    if args.output_root is None:
        args.output_root = Path.home() / 'six_site_spinup1000_final'
    obs_args = args.obs_csv
    args.obs_csv = {}
    for item in obs_args:
        site, sep, path = item.partition('=')
        if not sep or site not in SITES or not path:
            p.error(f'Invalid --obs-csv {item}; expected SITE=/path/to/file.csv')
        args.obs_csv[site] = path
    return args


def main():
    args = parse_args()
    baseline = get_reference_script(args)
    print(f'Reusing reference FLUXNET comparison functions: {baseline}', flush=True)
    core = load_reference(baseline)
    args.output_root.mkdir(parents=True, exist_ok=True)
    rows=[]
    for site in args.sites:
        print('\n'+'='*18+f' {site} '+'='*18, flush=True)
        try:
            rows.append(process_site(site, args, core))
        except Exception as err:
            print(f'ERROR {site}: {type(err).__name__}: {err}', file=sys.stderr, flush=True)
            traceback.print_exc()
            rows.append({'Site':site,'Status':'ERROR','Error':str(err)})
    summary = pd.DataFrame(rows)
    summary.to_csv(args.output_root / 'five_site_spinup1000_summary.csv', index=False)
    print('\nFINAL SUMMARY\n'+summary.to_string(index=False), flush=True)
    print(f'\nOutput directory: {args.output_root}', flush=True)
    if any(x['Status'] != 'OK' for x in rows):
        raise SystemExit(1)


if __name__ == '__main__':
    main()

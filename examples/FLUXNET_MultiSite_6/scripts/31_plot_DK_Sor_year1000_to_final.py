#!/usr/bin/env python3
"""Plot DK-Sor years 1000 onward from stage-27 snapshot CSVs, without NetCDF.

Example: python plot_dk_sor_1000_to_final.py --input-dir input --output-dir figures
Use --qa-scripts PATH to run the optional nature-figure panel alignment check.
The input metadata and all three CSVs must be from the same snapshot.
"""
import argparse
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

SITE = 'DK-Sor'
POOLS = ['TOTECOSYSC', 'TOTSOMC', 'TOTLITC', 'FATES_VEGC', 'FATES_STOREC', 'FATES_STRUCTC']
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 10, 'pdf.fonttype': 42,
                     'svg.fonttype': 'none', 'axes.spines.top': False,
                     'axes.spines.right': False})


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def number(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float('nan')


def year_rows(data, start):
    years = [int(r['SpinupYear']) for r in data]
    if len(years) != len(set(years)) or years != sorted(years):
        raise ValueError('SpinupYear must be unique and sorted')
    if not years or start not in years:
        raise ValueError(f'Start year {start} is absent')
    expected = list(range(start, max(years) + 1))
    actual = [y for y in years if y >= start]
    if actual != expected:
        raise ValueError('Missing spin-up years in requested interval')
    return [r for r in data if int(r['SpinupYear']) >= start]


def save(fig, path, qa):
    fig.canvas.draw()
    if qa:
        sys.path.insert(0, str(qa))
        from audit_panel_alignment import require_matplotlib_panel_alignment
        require_matplotlib_panel_alignment(fig, json_out=str(path)+'.alignment.json',
                                          tolerance_pt=1.5, gutter_tolerance_pt=1.5,
                                          strict=True)
    fig.savefig(path.with_suffix('.png'), dpi=300)
    fig.savefig(path.with_suffix('.pdf'))
    fig.savefig(path.with_suffix('.svg'))
    plt.close(fig)


def carbon_plot(data, units, title, path, qa):
    variables = [n for n in POOLS if n in data[0] and n in units]
    if len(variables) != len(POOLS):
        raise ValueError('The six expected carbon pools or their unit metadata are missing')
    fig, axes = plt.subplots(3, 2, figsize=(12, 10), sharex=True)
    fig.subplots_adjust(left=.10, right=.97, bottom=.08, top=.91, hspace=.36, wspace=.28)
    x = [int(r['SpinupYear']) for r in data]
    for ax, name in zip(axes.flat, variables):
        ax.plot(x, [number(r[name]) for r in data], color='#28728b', lw=1.1)
        ax.set_title(name, loc='left', fontweight='bold')
        ax.set_ylabel(units[name]['output'])
        ax.grid(alpha=.2)
    for ax in axes[-1]:
        ax.set_xlabel('Elapsed spin-up year')
    fig.suptitle(title, fontsize=14)
    save(fig, path, qa)


def pft_plot(data, complete_data, path, qa):
    columns = [x for x in data[0] if x.startswith('PFT') and x.endswith('_VEGC_pct')]
    # Same selection rule as stage 27: six largest maxima in the complete snapshot.
    top = sorted(columns, key=lambda col: max((number(r[col]) for r in complete_data
                 if math.isfinite(number(r[col]))), default=-math.inf), reverse=True)[:6]
    top = [c for c in top if any(number(r[c]) > 1e-8 for r in complete_data)]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    fig.subplots_adjust(left=.09, right=.71, bottom=.13, top=.87)
    x = [int(r['SpinupYear']) for r in data]
    for col in top:
        label = col.removesuffix('_VEGC_pct').replace('_', ' ')
        ax.plot(x, [number(r[col]) for r in data], lw=1.3, label=label)
    ax.set(xlabel='Elapsed spin-up year', ylabel='Share of FATES vegetation carbon (%)',
           ylim=(0, 103), title='DK-Sor | PFT vegetation carbon share')
    ax.grid(alpha=.2)
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=8, frameon=False)
    save(fig, path, qa)


def monthly_plot(data, meta, path, qa):
    dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in data]
    cy = meta['flux']['cycle_model_years']
    forcing = meta['forcing_years']
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    fig.subplots_adjust(left=.10, right=.83, bottom=.11, top=.87, hspace=.34)
    for ax, flux in zip(axes, ['GPP', 'NEE']):
        ax.plot(dates, [number(r['EC_'+flux]) for r in data], label='EC', color='#555555', lw=1.1)
        ax.plot(dates, [number(r['FATES_'+flux]) for r in data], label='FATES', color='#28728b', lw=1.1)
        ax.set_ylabel(flux + ' (g C m-2 d-1)')
        ax.grid(alpha=.2)
        ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), frameon=False)
    axes[-1].xaxis.set_major_locator(mdates.YearLocator(5))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    axes[-1].set_xlabel('Observation / forcing year')
    fig.suptitle(f'DK-Sor | last complete forcing cycle: model {cy[0]}–{cy[1]} mapped to {forcing[0]}–{forcing[1]}', fontsize=12)
    save(fig, path, qa)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir', type=Path, default=Path(__file__).resolve().parent/'input')
    p.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent/'figures')
    p.add_argument('--start-year', type=int, default=1000, help='inclusive elapsed spin-up year')
    p.add_argument('--qa-scripts', type=Path, help='optional nature-figure scripts directory')
    args = p.parse_args()
    input_dir, out = args.input_dir, args.output_dir
    meta = json.loads((input_dir/f'{SITE}_metadata.json').read_text(encoding='utf-8'))
    all_carbon = rows(input_dir/f'{SITE}_carbon_annual_means.csv')
    all_pft = rows(input_dir/f'{SITE}_FATES_PFT_VEGC_annual_pct.csv')
    carbon = year_rows(all_carbon, args.start_year)
    pft = year_rows(all_pft, args.start_year)
    start = int(meta['initial_model_start_year'])
    if any(int(r['ModelYear']) != start + int(r['SpinupYear']) - 1 for r in all_carbon):
        raise ValueError('ModelYear and SpinupYear mapping is inconsistent')
    if int(carbon[-1]['ModelYear']) != int(meta['source_model_years'][-1]):
        raise ValueError('Carbon CSV and metadata have different snapshot endpoints')
    if [r['SpinupYear'] for r in carbon] != [r['SpinupYear'] for r in pft]:
        raise ValueError('Carbon and PFT years do not match')
    out.mkdir(parents=True, exist_ok=True)
    end = int(carbon[-1]['SpinupYear'])
    prefix = f'{SITE}_years{args.start_year}-{end}'
    carbon_plot(carbon, meta['carbon_units'], f'{SITE} | annual carbon pools | spin-up {args.start_year}–{end}', out/(prefix+'_carbon_pools'), args.qa_scripts)
    tail = carbon[-min(250, len(carbon)):]
    carbon_plot(tail, meta['carbon_units'], f'{SITE} | final {len(tail)} archived spin-up years', out/(prefix+'_carbon_last250years'), args.qa_scripts)
    pft_plot(pft, all_pft, out/(prefix+'_PFT_carbon_share'), args.qa_scripts)
    monthly_plot(rows(input_dir/f'{SITE}_monthly_FATES_vs_EC.csv'), meta, out/(prefix+'_GPP_NEE_last_complete_cycle'), args.qa_scripts)
    for name, data in [('carbon', carbon), ('PFT', pft)]:
        with (out/(prefix+'_'+name+'.csv')).open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    print(f'Plotted spin-up years {args.start_year}–{end}; model years {carbon[0]["ModelYear"]}–{carbon[-1]["ModelYear"]}.')
    print(f'Output: {out.resolve()}')


if __name__ == '__main__':
    main()

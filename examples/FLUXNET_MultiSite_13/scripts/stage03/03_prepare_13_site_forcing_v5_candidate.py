#!/usr/bin/env python3
"""Run the *actual* FLUXNET_MultiSite_8 QC-v5 method on 13 pinned releases.

This is an adaptation/driver, not a new meteorological QC algorithm. It imports
03_prepare_eight_site_forcing_v5.py, fixes 13 year windows and source selection,
and writes results to an isolated candidate experiment folder. It never changes
source packages, previous processed_v5, DATM NetCDF, surface files or cases.

For IT-Col, treat legacy FLUXNET2015 FULLSET_HH as the primary half-hour input
and ERAI_HH (ERA-Interim, not ERA5) as the reanalysis companion. Legacy use
of the v5 rules is an exploratory adaptation that requires scientific review.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT_DEFAULT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
OUTPUT_DEFAULT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_qc_v5_candidate_20261014')

# (site, release, years, source type)
SITES = {
    'DE-Lnf': ('EUF_DE-Lnf_FLUXNET_2002-2024_v1.3_r1', 2002, 2024, 'modern'),
    'DE-Obe': ('EUF_DE-Obe_FLUXNET_2008-2025_v1.3_r1', 2008, 2025, 'modern'),
    'ES-Agu': ('EUF_ES-Agu_FLUXNET_2006-2024_v1.3_r1', 2006, 2024, 'modern'),
    'ES-LJu': ('EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1', 2004, 2024, 'modern'),
    'IT-Col': ('FLX_IT-Col_FLUXNET2015_FULLSET_1996-2014_1-4', 1996, 2014, 'legacy'),
    'DE-Gri': ('ICOS_DE-Gri_FLUXNET_2004-2025_v1.3_r1', 2004, 2025, 'modern'),
    'DE-RuR': ('ICOS_DE-RuR_FLUXNET_2011-2025_v1.3_r1', 2011, 2025, 'modern'),
    'FI-Hyy': ('ICOS_FI-Hyy_FLUXNET_1997-2026_v1.3_r1', 1997, 2025, 'modern'),
    'FI-Let': ('ICOS_FI-Let_FLUXNET_2010-2025_v1.3_r1', 2010, 2025, 'modern'),
    'FR-Pue': ('ICOS_FR-Pue_FLUXNET_2000-2026_v1.3_r1', 2000, 2025, 'modern'),
    'GF-Guy': ('ICOS_GF-Guy_FLUXNET_2004-2025_v1.3_r1', 2004, 2025, 'modern'),
    'IT-MBo': ('ICOS_IT-MBo_FLUXNET_2003-2026_v1.3_r1', 2003, 2025, 'modern'),
    'IT-Tor': ('ICOS_IT-Tor_FLUXNET_2008-2025_v1.3_r1', 2008, 2025, 'modern'),
}
REQUIRED = ('TIMESTAMP_START', 'TA_F', 'VPD_F', 'PA_F', 'SW_IN_F',
            'LW_IN_F', 'WS_F', 'P_F')
ERA_REQUIRED = ('TIMESTAMP_START', 'TA_ERA', 'VPD_ERA', 'PA_ERA',
                'SW_IN_ERA', 'LW_IN_ERA', 'WS_ERA', 'P_ERA')


def base_script_candidates():
    home = Path.home()
    return [
        home / '03_prepare_eight_site_forcing_v5.py',
        home / 'CLM_FATES_scripts/03_prepare_eight_site_forcing_v5.py',
        home / 'CLM-FATES-single-site-workflows/examples/FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py',
        home / 'CLM-FATES-single-site-workflows/examples/FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py',
    ]


def choose_file(directory, pattern):
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1 or not matches[0].is_file():
        raise RuntimeError(f'Expected exactly one {pattern} under {directory}, found {len(matches)}')
    return matches[0]


def header(path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return set(next(csv.reader(f)))


def sources(site, root):
    release, first, last, kind = SITES[site]
    source = root / site / 'forcing' / 'raw' / release
    if not source.is_dir():
        raise RuntimeError(f'Release directory missing: {source}')
    primary = choose_file(source, '*FULLSET_HH*.csv' if kind == 'legacy' else '*FLUXMET_HH*.csv')
    companion = choose_file(source, '*ERAI_HH*.csv' if kind == 'legacy' else '*ERA5_HH*.csv')
    absent = sorted(set(REQUIRED) - header(primary))
    missing_era = sorted(set(ERA_REQUIRED) - (header(primary) | header(companion)))
    if absent or missing_era:
        raise RuntimeError(f'Columns missing in pinned release: main={absent}, reanalysis={missing_era}')
    return dict(site=site, release=release, first_year=first, last_year=last,
                product='FLUXNET2015_FULLSET' if kind == 'legacy' else 'FLUXNET_v1.3',
                reanalysis='ERAI_HH (ERA-Interim)' if kind == 'legacy' else 'ERA5_HH (FLUXNET site-downscaled)',
                primary_file=str(primary), companion_file=str(companion))


def load_v5(path):
    spec = importlib.util.spec_from_file_location('fluxnet8_v5_reference', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load reference QC v5: {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, 'parse_site', None)) or not isinstance(getattr(module, 'SITE_YEARS', None), dict):
        raise RuntimeError('Reference script is not the expected original eight-site v5')
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Only check inputs, run zero QC/writes')
    parser.add_argument('--run', action='store_true', help='Run original QC-v5 algorithms to isolated candidate output')
    parser.add_argument('--root', type=Path, default=ROOT_DEFAULT)
    parser.add_argument('--output-root', type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument('--base-script', type=Path, help='Original 03_prepare_eight_site_forcing_v5.py')
    parser.add_argument('--sites', nargs='+', choices=list(SITES), default=list(SITES))
    args = parser.parse_args()
    if args.check == args.run:
        parser.error('Specify exactly one of --check or --run')
    root = args.root.resolve()
    output_root = args.output_root.resolve()
    if output_root == root or root in output_root.parents:
        raise SystemExit('REFUSED: candidate output must be OUTSIDE MY_EC_SITE to protect old forcing')
    if not args.run and output_root.exists():
        print('NOTE: existing candidate output directory (check mode does not touch it):', output_root)

    base = args.base_script
    if base is None:
        base = next((p for p in base_script_candidates() if p.is_file()), None)
    if not base or not base.is_file():
        raise SystemExit('MISSING ORIGINAL v5: place 03_prepare_eight_site_forcing_v5.py in ~/CLM_FATES_scripts/\n'
                         'GitHub reference: examples/FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py')
    original = load_v5(base)
    source_hash = hashlib.sha256(base.read_bytes()).hexdigest()
    print('Reference QC method:', base)
    print('Reference SHA256:', source_hash)
    print('Data root:', root)
    print('Candidate output:', output_root)

    failures = {}
    manifest = {}
    # Preflight ALL selected sites before any candidate file is written.
    for site in args.sites:
        try:
            info = sources(site, root)
            manifest[site] = info
            print(f'CHECK OK {site:8s}: {info["first_year"]}-{info["last_year"]}  {info["product"]}  {info["reanalysis"]}', flush=True)
        except Exception as exc:
            failures[site] = str(exc)
            print(f'CHECK FAIL {site}: {exc}', flush=True)
    if failures:
        print('PRECHECK FAILED; no QC run started. Failed:', failures)
        return 1
    if args.check:
        print(f'CHECK SUCCESS: {len(manifest)}/{len(args.sites)} sites; no outputs written')
        return 0

    if output_root.exists() and any(output_root.iterdir()):
        raise SystemExit(f'REFUSED: candidate output already contains files: {output_root}\n'
                         'Choose a NEW --output-root for a fresh run; nothing overwritten.')
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / 'input_manifest.json').write_text(json.dumps({
        'v5_base_script': str(base), 'v5_base_sha256': source_hash,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_policy': 'explicit pinned release per site; never read earlier raw releases',
        'note': 'IT-Col ERAI_HH is ERA-Interim, not ERA5; candidate only',
        'sites': manifest}, indent=2))

    # Replace ONLY v5's file locator; never modify v5 physics, CSVs or old output.
    # Original v5 requires FLUXMET_HH/ERA5_HH names, whereas IT-Col is FULLSET_HH/ERAI_HH.
    def pinned_get_one(raw_root, pattern):
        site = raw_root.parent.parent.name
        if site not in manifest:
            raise RuntimeError(f'Unrecognized site folder: {raw_root}')
        if pattern == '*FLUXMET_HH*.csv':
            return Path(manifest[site]['primary_file'])
        if pattern == '*ERA5_HH*.csv':
            return Path(manifest[site]['companion_file'])
        raise RuntimeError(f'Unexpected original-v5 file selection pattern: {pattern}')

    original.get_one = pinned_get_one
    original.SITE_YEARS = {site: (info['first_year'], info['last_year']) for site, info in manifest.items()}
    outcomes = {}
    for site in args.sites:
        info = manifest[site]
        print(f'\n======== QC v5 candidate: {site} ========', flush=True)
        try:
            result = original.parse_site(site, root, output_root)
            status_path = output_root / site / 'forcing/qc_v5' / f'{site}_status.json'
            status = json.loads(status_path.read_text())
            status.update({
                'release': info['release'], 'primary_file': info['primary_file'],
                'companion_file': info['companion_file'],
                'product': info['product'], 'reanalysis': info['reanalysis'],
                'reference_v5_sha256': source_hash,
                'method_note': 'Eight-site v5 QC rules applied to pinned release; candidate, manual review required before DATM',
                'legacy_note': ('FLUXNET2015 FULLSET_HH and ERAI_HH adapted to v5; check ERA-Interim validity manually'
                                if site == 'IT-Col' else ''),
                'candidate_only': True,
            })
            status_path.write_text(json.dumps(status, indent=2))
            outcomes[site] = status['status']
            print(f'FINAL {site}: {status["status"]}; {status.get("changes")} modifications; '
                  f'{status.get("manual_review_records")} manual review rows', flush=True)
        except Exception as exc:
            outcomes[site] = 'FAIL'
            print(f'FAILED {site}: {exc}', flush=True)
            qc = output_root / site / 'forcing/qc_v5'
            qc.mkdir(parents=True, exist_ok=True)
            (qc / f'{site}_status.json').write_text(json.dumps({
                'site': site, 'status': 'FAIL', 'error': str(exc), **info}, indent=2))
    (output_root / 'run_summary.csv').write_text('site,status,release\n' + '\n'.join(
        f'{site},{outcomes[site]},{manifest[site]["release"]}' for site in args.sites) + '\n')
    print('\n===== THIRTEEN-SITE QC CANDIDATE SUMMARY =====', flush=True)
    for site in args.sites:
        print(f'{site:8s} {outcomes[site]}', flush=True)
    print('SUMMARY:', output_root / 'run_summary.csv')
    print('REMINDER: QC v5 PASS/REVIEW does not certify suitability for DATM or spin-up.')
    return 1 if 'FAIL' in outcomes.values() else 0


if __name__ == '__main__':
    sys.exit(main())
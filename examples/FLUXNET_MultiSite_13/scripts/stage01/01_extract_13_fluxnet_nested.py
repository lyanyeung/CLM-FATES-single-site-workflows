#!/usr/bin/env python3
"""Stage 01: recursively extract 13 new releases, without touching older forcing.

Adapted from examples/FLUXNET_MultiSite_8/scripts/01_extract_8_fluxnet_nested.py.
Does not write DATM, surfaces, processed forcing, or existing spin-up files.
"""
import argparse
from contextlib import suppress
from itertools import count
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile
import zlib

ROOT = Path(os.environ.get(
    'FLUXNET_SITES_ROOT',
    '/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE',
))
PACKAGES = {
    'DE-Lnf': 'EUF_DE-Lnf_FLUXNET_2002-2024_v1.3_r1',
    'DE-Obe': 'EUF_DE-Obe_FLUXNET_2008-2025_v1.3_r1',
    'ES-Agu': 'EUF_ES-Agu_FLUXNET_2006-2024_v1.3_r1',
    'ES-LJu': 'EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1',
    'IT-Col': 'FLX_IT-Col_FLUXNET2015_FULLSET_1996-2014_1-4',
    'DE-Gri': 'ICOS_DE-Gri_FLUXNET_2004-2025_v1.3_r1',
    'DE-RuR': 'ICOS_DE-RuR_FLUXNET_2011-2025_v1.3_r1',
    'FI-Hyy': 'ICOS_FI-Hyy_FLUXNET_1997-2026_v1.3_r1',
    'FI-Let': 'ICOS_FI-Let_FLUXNET_2010-2025_v1.3_r1',
    'FR-Pue': 'ICOS_FR-Pue_FLUXNET_2000-2026_v1.3_r1',
    'GF-Guy': 'ICOS_GF-Guy_FLUXNET_2004-2025_v1.3_r1',
    'IT-MBo': 'ICOS_IT-MBo_FLUXNET_2003-2026_v1.3_r1',
    'IT-Tor': 'ICOS_IT-Tor_FLUXNET_2008-2025_v1.3_r1',
}


def crc32_file(path):
    crc = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            crc = zlib.crc32(chunk, crc)
    return crc & 0xffffffff


def extract_csv(src, raw_dir, name, *, expected_size=None, expected_crc=None):
    # Use filename only: no extraction of arbitrary ZIP directory paths.
    name = PurePosixPath(name.replace('\\', '/')).name
    if not name.lower().endswith('.csv') or name.lower() in ('toc.csv', '!toc.csv'):
        return
    destination = raw_dir / name
    if destination.exists():
        if (expected_size is not None and expected_crc is not None
                and destination.is_file()
                and destination.stat().st_size == expected_size
                and crc32_file(destination) == expected_crc):
            print('  SKIP identical:', name, flush=True)
            return
        raise RuntimeError('CSV conflict (will NOT overwrite): ' + str(destination))

    temporary = raw_dir / (name + '.partial')
    if temporary.exists():
        raise RuntimeError('Stale partial exists; inspect first: ' + str(temporary))
    try:
        with temporary.open('xb') as output:
            shutil.copyfileobj(src, output, length=1024 * 1024)
        if expected_size is not None and temporary.stat().st_size != expected_size:
            raise RuntimeError('Size mismatch: ' + name)
        if expected_crc is not None and crc32_file(temporary) != expected_crc:
            raise RuntimeError('CRC mismatch: ' + name)
        temporary.replace(destination)
        print('  EXTRACTED:', name, flush=True)
    finally:
        with suppress(FileNotFoundError):
            temporary.unlink()


def extract_zip(zip_path, raw_dir, tmp_dir, serial, depth=0):
    if depth > 8:
        raise RuntimeError('Nested ZIP depth exceeded: ' + str(zip_path))
    with ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = PurePosixPath(info.filename.replace('\\', '/')).name
            if not name:
                continue
            if name.lower().endswith('.zip'):
                nested_path = tmp_dir / f'nested_{next(serial)}.zip'
                print('  NESTED ZIP:', name, flush=True)
                try:
                    with archive.open(info) as infile, nested_path.open('xb') as outfile:
                        shutil.copyfileobj(infile, outfile, length=1024 * 1024)
                    extract_zip(nested_path, raw_dir, tmp_dir, serial, depth + 1)
                finally:
                    with suppress(FileNotFoundError):
                        nested_path.unlink()
            elif name.lower().endswith('.csv'):
                with archive.open(info) as infile:
                    extract_csv(infile, raw_dir, name,
                                expected_size=info.file_size, expected_crc=info.CRC)


def process(site, package):
    source_dir = ROOT / site / 'forcing' / 'packages'
    raw_dir = ROOT / site / 'forcing' / 'raw' / package
    if not source_dir.is_dir():
        raise RuntimeError('Package directory missing: ' + str(source_dir))

    sources = []
    for entry in (source_dir / (package + '.zip'), source_dir / package):
        if entry.exists():
            sources.append(entry)
    if not sources:
        raise RuntimeError('Not found: ' + package + '.zip or folder ' + package)

    raw_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='fluxnet_unpack_', dir=str(source_dir)) as temp:
        tmp_dir = Path(temp)
        serial = count(1)
        for source in sources:
            if source.is_file():
                print('  SOURCE ZIP:', source.name, flush=True)
                extract_zip(source, raw_dir, tmp_dir, serial)
            elif source.is_dir():
                for file in sorted(source.rglob('*')):
                    if not file.is_file():
                        continue
                    if file.suffix.lower() == '.zip':
                        print('  SOURCE ZIP:', file.name, flush=True)
                        extract_zip(file, raw_dir, tmp_dir, serial)
                    elif file.suffix.lower() == '.csv':
                        with file.open('rb') as infile:
                            extract_csv(infile, raw_dir, file.name,
                                        expected_size=file.stat().st_size,
                                        expected_crc=crc32_file(file))

    files = list(raw_dir.glob('*.csv'))
    bif = [p for p in files if '_BIF_' in p.name.upper()]
    met = [p for p in files if 'FLUXMET_HH' in p.name.upper()]
    era = [p for p in files if 'ERA5_HH' in p.name.upper()]
    flux = [p for p in files if 'FLUXES_HH' in p.name.upper()]
    fullset = [p for p in files if 'FULLSET_HH' in p.name.upper()]
    print('  AUDIT: CSV={}, BIF={}, FLUXMET_HH={}, ERA5_HH={}, FLUXES_HH={}, FULLSET_HH={}'.format(
        len(files), len(bif), len(met), len(era), len(flux), len(fullset)), flush=True)
    if not bif:
        raise RuntimeError('BIF metadata not found: check source package')
    if site == 'IT-Col':
        if not fullset:
            raise RuntimeError('FLUXNET2015 FULLSET_HH not found for IT-Col')
        print('  NOTE: IT-Col uses FLUXNET2015 FULLSET_HH (not v1.3 FLUXMET_HH).', flush=True)
    elif not met:
        raise RuntimeError('FLUXMET_HH not found: check source package')
    if not era and site != 'IT-Col':
        print('  WARNING: ERA5_HH missing; later v5 forcing may need separate ERA data', flush=True)
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sites', nargs='*', choices=list(PACKAGES),
                        help='Optional subset; default is all 13 sites')
    args = parser.parse_args()
    selected = args.sites if args.sites else list(PACKAGES)
    failures = []
    for site in selected:
        package = PACKAGES[site]
        print('\n' + '=' * 72 + '\n' + site + ': ' + package + '\n' + '=' * 72, flush=True)
        try:
            count_files = process(site, package)
            print('  SUCCESS {}: {} CSV files'.format(site, count_files), flush=True)
        except (OSError, ValueError, RuntimeError, BadZipFile) as err:
            print('  FAILED {}: {}'.format(site, err), flush=True)
            failures.append(site)
    print('\nFINAL: {}/{} sites successful'.format(len(selected) - len(failures), len(selected)))
    if failures:
        print('FAILED SITES: ' + ', '.join(failures))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
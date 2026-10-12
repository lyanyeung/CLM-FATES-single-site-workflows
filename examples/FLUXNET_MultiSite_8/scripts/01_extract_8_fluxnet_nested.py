#!/usr/bin/env python3
"""Unpack eight FLUXNET network packages without rewriting source archives."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile
from tempfile import TemporaryDirectory
from itertools import count
from contextlib import suppress
import os
import shutil
import sys
import zlib

ROOT = Path(os.environ.get('FLUXNET_SITES_ROOT', '/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
PACKAGES = {
    'CZ-BK1': 'ICOS_CZ-BK1_FLUXNET_2004-2026_v1.3_r1',
    'IT-Ren': 'ICOS_IT-Ren_FLUXNET_1999-2026_v1.3_r1',
    'FR-Hes': 'ICOS_FR-Hes_FLUXNET_1997-2026_v1.3_r1',
    'FR-FBn': 'ICOS_FR-FBn_FLUXNET_2008-2024_v1.3_r1',
    'DE-Hzd': 'ICOS_DE-Hzd_FLUXNET_2010-2025_v1.3_r1',
    'CH-Dav': 'ICOS_CH-Dav_FLUXNET_1997-2026_v1.3_r1',
    'BE-Vie': 'ICOS_BE-Vie_FLUXNET_1996-2026_v1.3_r1',
    'IT-Lav': 'EUF_IT-Lav_FLUXNET_2003-2020_v1.3_r1',
}


def crc32_file(path):
    crc = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            crc = zlib.crc32(chunk, crc)
    return crc & 0xffffffff


def extract_csv(src, raw_dir, name, *, expected_size=None, expected_crc=None):
    # Flatten to filename like the existing six-site example; refuse collisions.
    name = PurePosixPath(name.replace('\\', '/')).name
    if not name.lower().endswith('.csv') or name.lower() in ('toc.csv', '!toc.csv'):
        return
    destination = raw_dir / name
    if destination.exists():
        if (expected_size is not None and expected_crc is not None
                and destination.stat().st_size == expected_size
                and crc32_file(destination) == expected_crc):
            print('  SKIP identical:', name, flush=True)
            return
        raise RuntimeError(f'Conflicting CSV filename; refusing to overwrite: {destination}')

    temporary = raw_dir / (name + '.partial')
    try:
        with temporary.open('wb') as output:
            shutil.copyfileobj(src, output, length=1024 * 1024)
        if expected_size is not None and temporary.stat().st_size != expected_size:
            raise RuntimeError(f'Size mismatch while extracting {name}')
        if expected_crc is not None and crc32_file(temporary) != expected_crc:
            raise RuntimeError(f'CRC mismatch while extracting {name}')
        temporary.replace(destination)
        print('  EXTRACTED:', name, flush=True)
    finally:
        with suppress(FileNotFoundError):
            temporary.unlink()


def extract_zip(zip_path, raw_dir, tmp_dir, serial, depth=0):
    if depth > 8:
        raise RuntimeError(f'Nested ZIP depth exceeded at {zip_path}')
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
                    with archive.open(info) as infile, nested_path.open('wb') as outfile:
                        shutil.copyfileobj(infile, outfile, length=1024 * 1024)
                    extract_zip(nested_path, raw_dir, tmp_dir, serial, depth + 1)
                finally:
                    with suppress(FileNotFoundError):
                        nested_path.unlink()
            elif name.lower().endswith('.csv'):
                with archive.open(info) as infile:
                    extract_csv(infile, raw_dir, name, expected_size=info.file_size, expected_crc=info.CRC)


def process(site, package):
    source_dir = ROOT / site / 'forcing' / 'packages'
    raw_dir = ROOT / site / 'forcing' / 'raw' / package
    if not source_dir.is_dir():
        raise RuntimeError('Package directory missing: ' + str(source_dir))
    # Either <package>.zip or an unpacked folder <package>/ containing ZIP/CSV.
    sources = []
    for entry in (source_dir / f'{package}.zip', source_dir / package):
        if entry.exists():
            sources.append(entry)
    if not sources:
        raise RuntimeError('Source not found: expected ' + package + '.zip or directory ' + package)

    raw_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='fluxnet_unpack_', dir=str(source_dir)) as temp:
        tmp_dir = Path(temp)
        serial = count(1)
        for source in sources:
            if source.is_file():
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
                            extract_csv(infile, raw_dir, file.name, expected_size=file.stat().st_size, expected_crc=crc32_file(file))

    files = list(raw_dir.glob('*.csv'))
    bif = [file for file in files if '_BIF_' in file.name.upper()]
    met = [file for file in files if 'FLUXMET_HH' in file.name.upper()]
    era = [file for file in files if 'ERA5_HH' in file.name.upper()]
    flux = [file for file in files if 'FLUXES_HH' in file.name.upper()]
    print(f'  AUDIT: CSV={len(files)}, BIF={len(bif)}, FLUXMET_HH={len(met)}, ERA5_HH={len(era)}, FLUXES_HH={len(flux)}', flush=True)
    if not bif or not met:
        raise RuntimeError('Expected BIF and FLUXMET_HH not found; check source release')
    if not era:
        print('  WARNING: ERA5_HH companion file not found (needed by prior v5 workflow)', flush=True)
    return len(files)


def main():
    failures = []
    for site, package in PACKAGES.items():
        print('\n' + '=' * 65 + f'\n{site}: {package}\n' + '=' * 65, flush=True)
        try:
            num = process(site, package)
            print(f'  SUCCESS {site}: {num} CSV files', flush=True)
        except (OSError, ValueError, RuntimeError, BadZipFile) as err:
            print(f'  FAILED {site}: {err}', flush=True)
            failures.append(site)
    print('\nFINAL: ' + str(len(PACKAGES) - len(failures)) + '/' + str(len(PACKAGES)) + ' sites successful')
    if failures:
        print('FAILED SITES: ' + ', '.join(failures))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

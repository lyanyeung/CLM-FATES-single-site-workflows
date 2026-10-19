#!/usr/bin/env python3
"""Read-only check of any CLM-FATES case's Scratch and Research Filestore history.

Example:
  python3 scripts/research_filestore/inspect_archive.py \
    --case RU-Fyo_FATES_SPINUP500 --collection FLUXNET_MultiSite_6 \
    --site RU-Fyo --start-year 1998 --years 1000

No copy, removal, or model changes. Does not certify data integrity.
"""
import argparse
from pathlib import Path
import re

def years_at(root, case):
    if not root.is_dir():
        return set()
    rx = re.compile(r'^' + re.escape(case) + r'\.clm2\.h0a\.(\d{4})-\d{2}-\d{2}-\d{5}\.nc$')
    return {int(m.group(1)) for p in root.glob('*.nc')
            if p.is_file() and (m := rx.fullmatch(p.name))}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', required=True, help='Exact CIME case name')
    p.add_argument('--collection', required=True, help='e.g. FLUXNET_MultiSite_6')
    p.add_argument('--site', required=True, help='e.g. RU-Fyo')
    p.add_argument('--start-year', required=True, type=int)
    p.add_argument('--years', required=True, type=int)
    p.add_argument('--scratch', default='/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive')
    p.add_argument('--research', default='/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives')
    args = p.parse_args()
    if args.years <= 0 or args.start_year < 1:
        p.error('years and start-year must be positive')
    src = Path(args.scratch) / args.case
    dst = Path(args.research) / args.collection / args.site / args.case
    hsrc = src / 'lnd/hist'
    hdst = dst / 'archive/lnd/hist'
    ys = years_at(hsrc, args.case)
    yd = years_at(hdst, args.case)
    expected = set(range(args.start_year, args.start_year + args.years))
    print('Case:', args.case)
    print('Scratch:', hsrc)
    print('Research:', hdst)
    print('Expected annual h0a:', len(expected))
    print('Scratch expected years:', len(ys & expected))
    print('Research expected years:', len(yd & expected))
    print('Missing at destination:', len(expected - yd))
    print('Research outside requested period:', len(yd - expected))
    print('Manifest present:', (dst / 'manifest_sha256.tsv').is_file())
    latest = sorted(p.name for p in (src / 'rest').glob('????-01-01-00000') if p.is_dir())
    print('Latest Scratch restart:', latest[-1] if latest else 'NONE')
    print('READ ONLY. Year counts and manifest presence do not prove checksums.')
if __name__ == '__main__':
    main()

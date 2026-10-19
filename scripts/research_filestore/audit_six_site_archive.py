#!/usr/bin/env python3
"""Read-only cross-check of six FLUXNET CIME spin-ups and the NFS archive."""
from pathlib import Path
import csv

SITES = {"DE-Hai": 2000, "RU-Fyo": 1998, "DE-Tha": 1996, "DK-Sor": 1996, "NL-Loo": 1997, "IL-Yat": 2000}
SCRATCH = Path('/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive')
RESEARCH = Path('/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/FLUXNET_MultiSite_6')

print('Site    1k model h0a on Scratch    NFS h0a     Scratch newest rest    NFS manifest     Status')
for site, start in SITES.items():
    name = f'{site}_FATES_SPINUP500'
    src = SCRATCH / name
    dst = RESEARCH / site / name
    src_hist = src / 'lnd/hist'
    dst_hist = dst / 'archive/lnd/hist'
    years_src = {int(f.name.split('.h0a.', 1)[1][:4]) for f in src_hist.glob(f'{name}.clm2.h0a.*.nc') if '.h0a.' in f.name and len(f.name.split('.h0a.',1)[1]) >= 4 and f.name.split('.h0a.',1)[1][:4].isdigit()} if src_hist.exists() else set()
    years_dst = {int(f.name.split('.h0a.', 1)[1][:4]) for f in dst_hist.glob(f'{name}.clm2.h0a.*.nc') if '.h0a.' in f.name and len(f.name.split('.h0a.',1)[1]) >= 4 and f.name.split('.h0a.',1)[1][:4].isdigit()} if dst_hist.exists() else set()
    expected = set(range(start, start+1000))
    latest = sorted(p.name for p in (src/'rest').glob('????-01-01-00000') if p.is_dir()) if (src/'rest').exists() else []
    manifest = dst / 'manifest_sha256.tsv'
    status = 'prior 1000y result' if site != 'DE-Hai' else 'backup only'
    actual = len(years_src & expected)
    print(f'{site:<7} {actual:>5}/1000 {len(years_src):>7} total   {len(years_dst):>7}   {(latest[-1] if latest else "NONE"):<24} {"YES" if manifest.is_file() else "NO":<7} {status}')
    if manifest.is_file():
        with manifest.open(newline='') as f:
            rows = list(csv.reader(f, delimiter='\t'))
        print(f'         Manifest records: {len(rows)}. Presence is not checksum verification.')
print('READ-ONLY: no transfer, no modification, no deletion.')

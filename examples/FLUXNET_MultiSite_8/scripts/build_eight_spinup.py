#!/usr/bin/env python3
"""Convert the six-site 500-year spin-up script to the eight-site version.
Run in IRIDIS after fetching the upstream six-site script from GitHub.
"""
from pathlib import Path
import re


src = Path.home()/"09_submit_six_site_spinup500_source.sh"
dst = Path.home()/"09_eight_site_spinup500.sh"
if not src.is_file():
    raise SystemExit(f"Missing reference script: {src}")
s = src.read_text()
for key in ['SOURCE_NAME="GF-Guy_FATES_SURF2000_CO2405_1PT"',
            'SITES=( DE-Hai RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat )',
            'TOTAL_YEARS=500', 'RESUBMITS=$((TOTAL_YEARS/YEARS_PER_JOB-1))',
            "announce 'PREPARE: SIX FATES CASES (no submissions yet)'",
            "announce 'SUBMIT SIX INDEPENDENT 500-YEAR SPIN-UPS'"]:
    if s.count(key)!=1:
        raise RuntimeError(f"Expected exactly one anchor: {key}, found {s.count(key)}")

spec = {
  'CZ-BK1':(2004,2025,'376.95',49.50207615,18.53688247),
  'IT-Ren':(1999,2025,'367.80',46.58686,11.43369),
  'FR-Hes':(1997,2025,'363.04',48.6741,7.06465),
  'FR-FBn':(2008,2024,'385.02',43.24079,5.67865),
  'DE-Hzd':(2010,2025,'388.75',50.96381,13.48978),
  'CH-Dav':(1997,2025,'363.04',46.81533,9.85591),
  'BE-Vie':(1996,2025,'361.93',50.304962,5.998099),
  'IT-Lav':(2003,2020,'375.14',45.9562,11.28132),
}

values={'FIRST':1,'LAST':2,'CO2':3,'LAT':4,'LON':5}
# The coordinates come from the eight-site DATM configuration. Verify independently against BIF before cloning.
for key, idx in values.items():
    new = 'declare -A '+key+'=( '+ ' '.join(f'[{site}]={v[idx-1]}' for site,v in spec.items())+' )'
    pattern=r'(?m)^declare -A '+key+r'=\(.*\)$'
    s, n = re.subn(pattern,lambda _:new,s)
    if n!=1:raise RuntimeError(f"Could not replace {key}: {n}")
site_str='SITES=( '+' '.join(spec.keys())+' )'
s=s.replace('SITES=( DE-Hai RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat )',site_str)
s=s.replace('six_site','eight_site').replace('SIX-SITE','EIGHT-SITE').replace('SIX SITE','EIGHT SITE').replace('SIX','EIGHT')
s=s.replace('DE-Hai_FATES_SPINUP500/CaseStatus','CZ-BK1_FATES_SPINUP500/CaseStatus')
s=s.replace('Six independent CTSM/CLM-FATES','Eight independent CTSM/CLM-FATES')
s=s.replace('All six', 'All eight').replace('all six','all eight').replace('six cases','eight cases')

s=s.replace('set -Eeuo pipefail\n','''set -Eeuo pipefail
MODE="${1:---preflight}"
case "$MODE" in
  --preflight|--prepare|--submit) ;;
  *) echo "Usage: bash $0 [--preflight|--prepare|--submit]" >&2; exit 2 ;;
esac
''',1)

prep="announce 'PREPARE: EIGHT FATES CASES (no submissions yet)'"
assert s.count(prep)==1
s=s.replace(prep,'''if [[ "$MODE" == "--preflight" ]]; then
  echo 'PREFLIGHT OK: no case created and no job submitted.'
  exit 0
fi
'''+prep)

sub="announce 'SUBMIT EIGHT INDEPENDENT 500-YEAR SPIN-UPS'"
assert s.count(sub)==1
s=s.replace(sub,'''if [[ "$MODE" == "--prepare" ]]; then
  echo 'PREPARATION OK: cases configured and checked; NO jobs submitted.'
  exit 0
fi
'''+sub)

# fail fast if the user is not in a Python environment that supports reading NetCDF
needle="  printf '%-8s DATM=%d years (%d-%d) CO2=%s ppm  Surface=%s\\n'"
assert s.count(needle)==1
# Independent check that the revised FR-Hes forcing was used in its DATM, not old 2022 files.
frcheck='''
  if [[ "$SITE" == "FR-Hes" ]]; then
    python3 - "${DATM}/FR-Hes_DATM_2022.nc" <<'PY_FR'
import sys, datetime
from netCDF4 import Dataset
path=sys.argv[1]
with Dataset(path) as ds:
    for stamp, expected in [('2022-07-03T17:00:00', 27.642),
                            ('2022-07-03T18:00:00', 27.456),
                            ('2022-07-03T18:30:00', 26.974)]:
        date=datetime.datetime.fromisoformat(stamp)
        day=(date.date()-datetime.date(2022,1,1)).days
        idx=day*48+date.hour*2+date.minute//30
        got=float(ds.variables['TBOT'][idx,0,0])-273.15
        if abs(got-expected)>0.02:
            raise SystemExit(f'FR-Hes manual correction missing {stamp}: TBOT={got:.3f}C expected={expected}C')
    if 'processed_v5_manual_v1' not in ds.getncattr('source_processed_csv'):
        raise SystemExit('FR-Hes 2022 DATM metadata not pointing to manual_v1 forcing')
print('FR-Hes manual-v1 forcing verified in 2022 DATM')
PY_FR
  fi
'''
s=s.replace(needle,frcheck+'\n'+needle)
# Verify latitude/longitude independently from FLUXNET BIF, so that a copied
# coordinate from the earlier eight-site DATM generator cannot silently persist.
geo_anchor='  [[ -s "${MODS}/user_nl_clm" ]]'
assert s.count(geo_anchor)==1
geo_check=r"""  python3 - "$SITE_ROOT" "${LAT[$SITE]}" "${LON[$SITE]}" "${DATM}/${SITE}_DATM_${FIRST_Y}.nc" <<'PY_GEO'
import csv,sys,math
from pathlib import Path
from netCDF4 import Dataset
site=Path(sys.argv[1]); script_lat=float(sys.argv[2]); script_lon=float(sys.argv[3]); ncpath=sys.argv[4]
paths=list((site/'forcing/raw').rglob('*_FLUXNET_BIF_*.csv'))
if not paths: raise SystemExit(f'{site.name}: BIF missing')
values={'LOCATION_LAT':[],'LOCATION_LONG':[]}
for path in paths:
    with path.open(encoding='utf-8-sig',errors='replace',newline='') as f:
        for row in csv.DictReader(f):
            key=(row.get('VARIABLE') or '').strip().upper()
            if key in values:
                try: values[key].append(float(row['DATAVALUE']))
                except (ValueError,TypeError): pass
if not all(values.values()): raise SystemExit(f'{site.name}: BIF coordinates missing')
lat=sum(values['LOCATION_LAT'])/len(values['LOCATION_LAT'])
lon=sum(values['LOCATION_LONG'])/len(values['LOCATION_LONG'])
if max(abs(x-lat) for x in values['LOCATION_LAT']) > 0.01 or max(abs(x-lon) for x in values['LOCATION_LONG']) > 0.01:
    raise SystemExit(f'{site.name}: conflicting BIF coordinate metadata')
if abs(script_lat-lat)>0.01 or abs(((script_lon-lon+180)%360)-180)>0.01:
    raise SystemExit(f'{site.name}: hardcoded site coordinates disagree with BIF: script=({script_lat},{script_lon}), BIF=({lat},{lon})')
with Dataset(ncpath) as ds:
    nc_lat=float(ds.variables['lat'][0]);nc_lon=float(ds.variables['lon'][0])
if abs(nc_lat-lat)>0.01 or abs(((nc_lon-lon+180)%360)-180)>0.01:
    raise SystemExit(f'{site.name}: DATM coordinates disagree with BIF')
print(f'{site.name} coordinates verified vs BIF and DATM: {lat:.6f}, {lon:.6f}')
PY_GEO
"""
s=s.replace(geo_anchor,geo_check+'\n'+geo_anchor,1)


# Explicitly warn at preflight about DE-Hzd P provenance. Do not silently claim it validated.
s=s.replace("  [[ -s \"${MODS}/user_nl_clm\" ]]",'''  if [[ "$SITE" == "DE-Hzd" ]]; then
    echo 'NOTE: DE-Hzd P_F 100% ERA; 2,134-4,136 mm/y suspect. Candidate spin-up only; do not call scientifically validated.'
  fi
  [[ -s "${MODS}/user_nl_clm" ]]''',1)

dst.write_text(s)
dst.chmod(0o755)
print('Created:',dst)
print('Run bash -n, then --preflight, --prepare and --submit in that order')

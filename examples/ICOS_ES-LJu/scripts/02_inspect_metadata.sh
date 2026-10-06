#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

RAW="${RAW_ROOT}"

echo "===== Raw files ====="
find "${RAW}" -maxdepth 1 -type f -printf '%f\n' | sort

BIF="${RAW}/EUF_ES-LJu_FLUXNET_BIF_2004-2024_v1.3_r1.csv"
BIFVAR="${RAW}/EUF_ES-LJu_FLUXNET_BIFVARINFO_HH_2004-2024_v1.3_r1.csv"
FLUXMET="${RAW}/EUF_ES-LJu_FLUXNET_FLUXMET_HH_2004-2024_v1.3_r1.csv"

echo
echo "===== Site metadata of interest ====="
grep -Ei 'LOCATION_LAT|LOCATION_LONG|LOCATION_ELEV|HEIGHTC' "${BIF}" || true

echo
echo "===== TA_F / WS_F measurement height ====="
grep -E '(^|,)TA_F(,|$)|(^|,)WS_F(,|$)' "${BIFVAR}" || true

echo
echo "===== FLUXMET columns ====="
python - "${FLUXMET}" <<'PY'
import pandas as pd, sys
f = sys.argv[1]
df = pd.read_csv(f, nrows=2)
for c in df.columns:
    print(c)
PY

echo
echo "Expected site constants:"
echo "lat=${SITE_LAT}"
echo "lon=${SITE_LON}"
echo "elevation=${SITE_ELEV} m"
echo "ZBOT=${ZBOT} m"

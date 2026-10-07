#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

BIF="${RAW_ROOT}/AMF_US-Ha1_FLUXNET_BIF_1991-2025_v1.3_r1.csv"
BIFVAR="${RAW_ROOT}/AMF_US-Ha1_FLUXNET_BIFVARINFO_HR_1991-2025_v1.3_r1.csv"
FLUXMET="${RAW_ROOT}/AMF_US-Ha1_FLUXNET_FLUXMET_HR_1991-2025_v1.3_r1.csv"

echo "===== Site metadata ====="
grep -Ei 'LOCATION_LAT|LOCATION_LONG|LOCATION_ELEV|HEIGHTC' "${BIF}" || true

echo
echo "===== Measurement heights ====="

python - "${BIFVAR}" <<'PY2'
import pandas as pd
import sys

df = pd.read_csv(sys.argv[1])

targets = [
    "TA_F", "TA_F_MDS",
    "VPD_F", "VPD_F_MDS",
    "PA", "PA_F",
    "WS", "WS_F",
    "P", "P_F",
]

for gid, g in df.groupby("GROUP_ID"):
    vals = dict(zip(g["VARIABLE"], g["DATAVALUE"]))
    var = vals.get("VAR_INFO_VARNAME", "")
    if var in targets:
        print(
            f"{var:12s} "
            f"HEIGHT={vals.get('VAR_INFO_HEIGHT','NA')} "
            f"UNIT={vals.get('VAR_INFO_UNIT','NA')} "
            f"MODEL={vals.get('VAR_INFO_MODEL','NA')}"
        )
PY2

echo
echo "===== FLUXMET columns ====="

python - "${FLUXMET}" <<'PY2'
import pandas as pd
import sys

df = pd.read_csv(sys.argv[1], nrows=2)
for c in df.columns:
    print(c)
PY2

echo
echo "Reference values used in this workflow:"
echo "TA_F height   = 27.9 m"
echo "VPD_F height  = 27.9 m"
echo "WS_F height   = 29.0 m"
echo "PA_F height   = 3.0 m"
echo "P_F height    = 1.0 m"
echo "CLM ZBOT      = 27.9 m"

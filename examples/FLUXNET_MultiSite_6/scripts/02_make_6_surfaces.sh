#!/usr/bin/env bash
set -euo pipefail

ROOT="/iridisfs/scratch/ly3n24/CLM_FATES"
CTSM="$ROOT/CTSM"
INPUTDATA="$ROOT/inputdata"
SITES_ROOT="$ROOT/sites/MY_EC_SITE"

SITES=(
  DE-Hai
  RU-Fyo
  DE-Tha
  DK-Sor
  NL-Loo
  IL-Yat
)

for SITE in "${SITES[@]}"; do

    echo
    echo "===================================="
    echo "Creating surface: $SITE"
    echo "===================================="

    SITE_ROOT="$SITES_ROOT/$SITE"
    OUT="$SITE_ROOT/subset_data"
    CFG="$SITE_ROOT/${SITE}_data.cfg"

    # Protect existing surface data
    if [[ -d "$OUT/user_mods" ]] || \
       compgen -G "$OUT/surfdata_${SITE}*" > /dev/null; then
        echo "Existing surface detected: $SITE"
        echo "SKIPPING to avoid overwrite"
        continue
    fi

    # Find site BIF metadata
    BIF=$(find "$SITE_ROOT/forcing/raw" \
      -type f -name '*FLUXNET_BIF_*.csv' \
      -print -quit)

    if [[ -z "$BIF" ]]; then
        echo "ERROR: BIF metadata missing for $SITE"
        exit 1
    fi

    # Extract latitude and longitude
    COORDS=$(python3 - "$BIF" <<'PY'
import csv
import sys

path = sys.argv[1]
values = {"LOCATION_LAT": [], "LOCATION_LONG": []}

with open(path, encoding="latin-1", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row.get("VARIABLE") or "").strip().upper()
        if key in values:
            try:
                values[key].append(float(row["DATAVALUE"]))
            except (ValueError, TypeError):
                pass

result = {}
for key, numbers in values.items():
    unique = sorted(set(numbers))
    if len(unique) != 1:
        raise RuntimeError(
            f"{key}: expected one unique value, got {unique}"
        )
    result[key] = unique[0]

lat = result["LOCATION_LAT"]
lon = result["LOCATION_LONG"]

if not (-90 <= lat <= 90 and -180 <= lon <= 180):
    raise RuntimeError("Invalid coordinates")

print(lat, lon)
PY
)

    read -r LAT LON <<< "$COORDS"

    echo "Latitude : $LAT"
    echo "Longitude: $LON"

    mkdir -p "$OUT"

    cd "$CTSM"

    cp tools/site_and_regional/default_data_2000.cfg "$CFG"

    # Same reference datasets as GF-Guy
    sed -i \
      's|dir = lnd/clm2/surfdata_esmf/ctsm5.4.0|dir = lnd/clm2/surfdata_esmf/ctsm5.3.0|g' \
      "$CFG"

    sed -i \
      's|surfdat_16pft = .*|surfdat_16pft = surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc|' \
      "$CFG"

    sed -i \
      's|mesh_surf = .*|mesh_surf = fv0.9x1.25_141008_ESMFmesh.nc|' \
      "$CFG"

    tools/site_and_regional/subset_data point \
      --lat "$LAT" \
      --lon "$LON" \
      --lon-type 180 \
      --site "$SITE" \
      --surf-year 2000 \
      --create-surface \
      --create-user-mods \
      --inputdata-dir "$INPUTDATA" \
      --cfg-file "$CFG" \
      --outdir "$OUT"

    echo "SURFACE COMPLETED: $SITE"

done

echo
echo "ALL SIX SURFACE DATASETS PROCESSED"

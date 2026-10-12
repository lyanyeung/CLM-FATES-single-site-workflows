#!/usr/bin/env bash
set -euo pipefail

ROOT="/iridisfs/scratch/ly3n24/CLM_FATES"
CTSM="$ROOT/CTSM"
INPUTDATA="$ROOT/inputdata"
SITES_ROOT="$ROOT/sites/MY_EC_SITE"

SITES=(
  CZ-BK1
  IT-Ren
  FR-Hes
  FR-FBn
  DE-Hzd
  CH-Dav
  BE-Vie
  IT-Lav
)

# Check CTSM and inputdata
[[ -f "$CTSM/tools/site_and_regional/default_data_2000.cfg" ]] || {
    echo "ERROR: CTSM directory or default config not found"
    exit 1
}

[[ -d "$INPUTDATA" ]] || {
    echo "ERROR: CTSM inputdata not found"
    exit 1
}

for SITE in "${SITES[@]}"; do

    echo
    echo "=========================================="
    echo "Creating surface: $SITE"
    echo "=========================================="

    SITE_ROOT="$SITES_ROOT/$SITE"
    OUT="$SITE_ROOT/subset_data"
    CFG="$SITE_ROOT/${SITE}_data.cfg"

    # Find BIF metadata
    BIF=$(find "$SITE_ROOT/forcing/raw" \
        -type f -name '*_FLUXNET_BIF_*.csv' \
        -print -quit 2>/dev/null || true)

    if [[ -z "$BIF" ]]; then
        echo "ERROR: BIF file missing for $SITE"
        exit 1
    fi

    echo "BIF: $BIF"

    # Get latitude and longitude
    COORDS=$(python - "$BIF" <<'PY'
import csv
import sys

path = sys.argv[1]

values = {
    "LOCATION_LAT": [],
    "LOCATION_LONG": []
}

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

    echo "Latitude:  $LAT"
    echo "Longitude: $LON"

    # Protect existing output
    SURF=""
    if [[ -d "$OUT" ]]; then
        SURF=$(find "$OUT" -maxdepth 1 \
            -type f -name 'surfdata*.nc' -print -quit)
    fi

    if [[ -n "$SURF" && -d "$OUT/user_mods" ]]; then
        echo "Surface and user_mods already exist."
        echo "SKIPPING: $SITE"
        continue
    fi

    if [[ -n "$SURF" || -e "$OUT/user_mods" ]]; then
        echo "ERROR: Incomplete existing surface output."
        echo "Inspect manually: $OUT"
        exit 1
    fi

    mkdir -p "$OUT"

    cd "$CTSM"

    # Copy the same reference config as the six-site workflow
    cp tools/site_and_regional/default_data_2000.cfg "$CFG"

    sed -i \
      's|dir = lnd/clm2/surfdata_esmf/ctsm5.4.0|dir = lnd/clm2/surfdata_esmf/ctsm5.3.0|g' \
      "$CFG"

    sed -i \
      's|surfdat_16pft = .*|surfdat_16pft = surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc|' \
      "$CFG"

    sed -i \
      's|mesh_surf = .*|mesh_surf = fv0.9x1.25_141008_ESMFmesh.nc|' \
      "$CFG"

    # Generate site-specific surface and user mods
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
echo "=========================================="
echo "ALL EIGHT SURFACE DATASETS PROCESSED"
echo "=========================================="

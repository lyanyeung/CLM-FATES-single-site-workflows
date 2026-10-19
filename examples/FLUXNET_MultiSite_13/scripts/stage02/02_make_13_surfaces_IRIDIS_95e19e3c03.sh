#!/usr/bin/env bash
# CLM-FATES 13 ICOS/EUF/FLUXNET2015 sites: point surfaces from site BIF + official IT-Col coordinates.
# Based on examples/FLUXNET_MultiSite_8/scripts/02_make_8_surfaces.sh (same subset_data settings).
# Source for IT-Col coordinates: https://fluxnet.org/sites/siteinfo/IT-Col
set -euo pipefail

MODE="${1:---check}"
if [[ "$MODE" != '--check' && "$MODE" != '--run' ]]; then
  echo "Usage: bash $0 [--check|--run]" >&2
  exit 2
fi
ROOT='/iridisfs/scratch/ly3n24/CLM_FATES'
CTSM="$ROOT/CTSM"
INPUTDATA="$ROOT/inputdata"
SITES_ROOT="$ROOT/sites/MY_EC_SITE"
SITES=(DE-Lnf DE-Obe ES-Agu ES-LJu IT-Col DE-Gri DE-RuR FI-Hyy FI-Let FR-Pue GF-Guy IT-MBo IT-Tor)

# Check tooling and inputdata *before* generating any outputs.
[[ -f "$CTSM/tools/site_and_regional/default_data_2000.cfg" ]] || { echo "ERROR: CTSM default cfg not found" >&2; exit 1; }
[[ -d "$INPUTDATA" ]] || { echo "ERROR: CTSM inputdata missing" >&2; exit 1; }
command -v python >/dev/null || { echo "ERROR: python missing" >&2; exit 1; }

# One exact network package per site; no accidental reuse of old forcing release.
declare -A PACKAGES=(
  [DE-Lnf]='EUF_DE-Lnf_FLUXNET_2002-2024_v1.3_r1'
  [DE-Obe]='EUF_DE-Obe_FLUXNET_2008-2025_v1.3_r1'
  [ES-Agu]='EUF_ES-Agu_FLUXNET_2006-2024_v1.3_r1'
  [ES-LJu]='EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1'
  [IT-Col]='FLX_IT-Col_FLUXNET2015_FULLSET_1996-2014_1-4'
  [DE-Gri]='ICOS_DE-Gri_FLUXNET_2004-2025_v1.3_r1'
  [DE-RuR]='ICOS_DE-RuR_FLUXNET_2011-2025_v1.3_r1'
  [FI-Hyy]='ICOS_FI-Hyy_FLUXNET_1997-2026_v1.3_r1'
  [FI-Let]='ICOS_FI-Let_FLUXNET_2010-2025_v1.3_r1'
  [FR-Pue]='ICOS_FR-Pue_FLUXNET_2000-2026_v1.3_r1'
  [GF-Guy]='ICOS_GF-Guy_FLUXNET_2004-2025_v1.3_r1'
  [IT-MBo]='ICOS_IT-MBo_FLUXNET_2003-2026_v1.3_r1'
  [IT-Tor]='ICOS_IT-Tor_FLUXNET_2008-2025_v1.3_r1'
)

success=0
skipped=0
for SITE in "${SITES[@]}"; do
  echo
  echo "======== $SITE ========"
  SITE_ROOT="$SITES_ROOT/$SITE"
  RELEASE="${PACKAGES[$SITE]}"
  RAW="$SITE_ROOT/forcing/raw/$RELEASE"
  OUT="$SITE_ROOT/subset_data"
  CFG="$SITE_ROOT/${SITE}_data.cfg"
  [[ -d "$RAW" ]] || { echo "ERROR: expected release folder missing: $RAW" >&2; exit 1; }

  if [[ "$SITE" == 'IT-Col' ]]; then
    # Official FLUXNET2015 siteinfo, not invented BIF metadata.
    LAT='41.8494'; LON='13.5881'
    SOURCE='FLUXNET official siteinfo: https://fluxnet.org/sites/siteinfo/IT-Col'
    [[ $(find "$RAW" -maxdepth 1 -type f -name '*FULLSET_HH*.csv' | wc -l) -eq 1 ]] || {
      echo "ERROR: IT-Col FULLSET_HH missing or ambiguous" >&2; exit 1;
    }
  else
    mapfile -t bif_files < <(find "$RAW" -maxdepth 1 -type f -name '*_FLUXNET_BIF_*.csv' -print)
    [[ ${#bif_files[@]} -eq 1 ]] || { echo "ERROR: expected 1 BIF for $SITE; found ${#bif_files[@]}" >&2; exit 1; }
    BIF="${bif_files[0]}"
    COORDS=$(python - "$BIF" <<'PY'
import csv, sys
values = {'LOCATION_LAT': set(), 'LOCATION_LONG': set()}
with open(sys.argv[1], encoding='latin-1', newline='') as f:
    for row in csv.DictReader(f):
        key = (row.get('VARIABLE') or '').strip().upper()
        if key in values:
            try:
                values[key].add(float(row['DATAVALUE']))
            except (ValueError, TypeError):
                continue
if any(len(v) != 1 for v in values.values()):
    raise SystemExit('BIF coordinates missing or ambiguous: ' + str(values))
lat, lon = next(iter(values['LOCATION_LAT'])), next(iter(values['LOCATION_LONG']))
if not (-90 <= lat <= 90 and -180 <= lon <= 180):
    raise SystemExit('Invalid BIF coordinates')
print(lat, lon)
PY
)
    read -r LAT LON <<< "$COORDS"
    SOURCE="$BIF"
  fi

  echo "Release: $RELEASE"
  echo "Coordinate source: $SOURCE"
  echo "Lat, Lon: $LAT, $LON"

  # Existing static surface is NOT the new meteorological forcing.
  existing_surf=$(find "$OUT" -maxdepth 1 -type f -name 'surfdata*.nc' -print -quit 2>/dev/null || true)
  if [[ -n "$existing_surf" && -d "$OUT/user_mods" ]]; then
    echo "SKIP EXISTING surface/user_mods (no modifications): $OUT"
    skipped=$((skipped + 1))
    continue
  fi
  if [[ -n "$existing_surf" || -e "$OUT/user_mods" ]]; then
    echo "ERROR: incomplete existing output at $OUT; refusing to overwrite" >&2
    exit 1
  fi
  if [[ -e "$OUT" ]] && [[ -n "$(ls -A "$OUT")" ]]; then
    echo "ERROR: nonempty output directory without completed surface: $OUT" >&2
    exit 1
  fi
  if [[ -e "$CFG" ]]; then
    echo "ERROR: existing site config found, no existing surface; inspect before proceeding: $CFG" >&2
    exit 1
  fi
  if [[ "$MODE" == '--check' ]]; then
    echo 'CHECK OK: would create new point surface (no files written)'
    success=$((success + 1))
    continue
  fi
  mkdir -p "$OUT"
  cp "$CTSM/tools/site_and_regional/default_data_2000.cfg" "$CFG"
  sed -i \
    -e 's|dir = lnd/clm2/surfdata_esmf/ctsm5.4.0|dir = lnd/clm2/surfdata_esmf/ctsm5.3.0|g' \
    -e 's|surfdat_16pft = .*|surfdat_16pft = surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc|' \
    -e 's|mesh_surf = .*|mesh_surf = fv0.9x1.25_141008_ESMFmesh.nc|' \
    "$CFG"
  (
    cd "$CTSM"
    tools/site_and_regional/subset_data point \
      --lat "$LAT" --lon "$LON" --lon-type 180 \
      --site "$SITE" --surf-year 2000 \
      --create-surface --create-user-mods \
      --inputdata-dir "$INPUTDATA" \
      --cfg-file "$CFG" --outdir "$OUT"
  )
  existing_surf=$(find "$OUT" -maxdepth 1 -type f -name 'surfdata*.nc' -print -quit 2>/dev/null || true)
  [[ -n "$existing_surf" && -d "$OUT/user_mods" ]] || {
    echo "ERROR: generation did not produce expected surfdata and user_mods for $SITE" >&2
    exit 1
  }
  echo "SURFACE COMPLETED: $SITE"
  success=$((success + 1))
done

echo
printf 'FINAL: %d sites %s; %d existing surfaces skipped; total %d/13\n' \
  "$success" "$MODE" "$skipped" "$((success + skipped))"

#!/usr/bin/env bash
set -euo pipefail

LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/ICOS'
REMOTE='ly3n24@iridis6.soton.ac.uk'
REMOTE_ROOT='/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'

PACKAGES=(
  'ICOS_CZ-BK1_FLUXNET_2004-2026_v1.3_r1'
  'ICOS_IT-Ren_FLUXNET_1999-2026_v1.3_r1'
  'ICOS_FR-Hes_FLUXNET_1997-2026_v1.3_r1'
  'ICOS_FR-FBn_FLUXNET_2008-2024_v1.3_r1'
  'ICOS_DE-Hzd_FLUXNET_2010-2025_v1.3_r1'
  'ICOS_CH-Dav_FLUXNET_1997-2026_v1.3_r1'
  'ICOS_BE-Vie_FLUXNET_1996-2026_v1.3_r1'
  'EUF_IT-Lav_FLUXNET_2003-2020_v1.3_r1'
)

[[ -d "$LOCAL_ROOT" ]] || { echo "Cannot find $LOCAL_ROOT" >&2; exit 1; }
command -v rsync >/dev/null || { echo 'rsync missing: sudo apt install rsync' >&2; exit 1; }

for pkg in "${PACKAGES[@]}"; do
  site="${pkg#*_}"
  site="${site%%_*}"
  archive="$(find "$LOCAL_ROOT" -maxdepth 1 -type f -iname "$pkg.zip" -print -quit)"
  folder="$LOCAL_ROOT/$pkg"
  target="$REMOTE_ROOT/$site/forcing/packages"

  if [[ -z "$archive" && ! -d "$folder" ]]; then
    echo "ERROR: missing $pkg.zip or directory $pkg" >&2
    exit 1
  fi
  echo "===== Uploading $site ====="
  ssh "$REMOTE" "mkdir -p '$target'"
  if [[ -n "$archive" ]]; then
    rsync -rtvP -- "$archive" "$REMOTE:$target/$pkg.zip"
  else
    rsync -rtvP -- "$folder/" "$REMOTE:$target/$pkg/"
  fi
done

echo 'All eight network packages uploaded.'

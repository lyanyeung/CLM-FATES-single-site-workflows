#!/usr/bin/env bash
# Stage 00: WSL -> IRIDIS6, following FLUXNET_MultiSite_8 layout.
set -euo pipefail

LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/ICOS'
REMOTE='ly3n24@iridis6.soton.ac.uk'
REMOTE_ROOT='/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
EXTRACTOR="$SCRIPT_DIR/01_extract_13_fluxnet_nested.py"

PACKAGES=(
  'EUF_DE-Lnf_FLUXNET_2002-2024_v1.3_r1'
  'EUF_DE-Obe_FLUXNET_2008-2025_v1.3_r1'
  'EUF_ES-Agu_FLUXNET_2006-2024_v1.3_r1'
  'EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1'
  'FLX_IT-Col_FLUXNET2015_FULLSET_1996-2014_1-4'
  'ICOS_DE-Gri_FLUXNET_2004-2025_v1.3_r1'
  'ICOS_DE-RuR_FLUXNET_2011-2025_v1.3_r1'
  'ICOS_FI-Hyy_FLUXNET_1997-2026_v1.3_r1'
  'ICOS_FI-Let_FLUXNET_2010-2025_v1.3_r1'
  'ICOS_FR-Pue_FLUXNET_2000-2026_v1.3_r1'
  'ICOS_GF-Guy_FLUXNET_2004-2025_v1.3_r1'
  'ICOS_IT-MBo_FLUXNET_2003-2026_v1.3_r1'
  'ICOS_IT-Tor_FLUXNET_2008-2025_v1.3_r1'
)

[[ -d "$LOCAL_ROOT" ]] || { echo "ERROR: Local directory missing: $LOCAL_ROOT" >&2; exit 1; }
[[ -f "$EXTRACTOR" ]] || { echo "ERROR: Place 01_extract_13_fluxnet_nested.py beside this script" >&2; exit 1; }
for command_name in ssh rsync sha256sum; do
  command -v "$command_name" >/dev/null || { echo "ERROR: command not installed: $command_name" >&2; exit 1; }
done

# Preflight *all* 13 packages before writing anything to IRIDIS.
declare -a SOURCES=()
declare -a FORMATS=()
fail=0
for pkg in "${PACKAGES[@]}"; do
  zip_file=''
  while IFS= read -r -d '' candidate; do
    zip_file="$candidate"
    break
  done < <(find "$LOCAL_ROOT" -maxdepth 1 -type f -iname "$pkg.zip" -print0)
  folder="$LOCAL_ROOT/$pkg"
  if [[ -n "$zip_file" ]]; then
    SOURCES+=("$zip_file")
    FORMATS+=(zip)
    if [[ -d "$folder" ]]; then
      echo "NOTICE: both ZIP and directory exist; using ZIP: $pkg"
    fi
  elif [[ -d "$folder" ]]; then
    SOURCES+=("$folder")
    FORMATS+=(dir)
  else
    echo "MISSING: $pkg (.zip or directory)" >&2
    SOURCES+=("")
    FORMATS+=(missing)
    fail=1
  fi
done
(( fail == 0 )) || { echo 'ABORT: missing input packages; nothing uploaded.' >&2; exit 1; }

echo "Preflight OK: ${#PACKAGES[@]} source packages found."
echo "Remote target: $REMOTE:$REMOTE_ROOT"
ssh "$REMOTE" 'echo "SSH connection OK: $(hostname)"'

for i in "${!PACKAGES[@]}"; do
  pkg="${PACKAGES[$i]}"
  site="${pkg#*_}"
  site="${site%%_*}"
  src="${SOURCES[$i]}"
  kind="${FORMATS[$i]}"
  target="$REMOTE_ROOT/$site/forcing/packages"
  echo
  echo "========= [$((i + 1))/${#PACKAGES[@]}] $site | $pkg ========="
  ssh "$REMOTE" "mkdir -p '$target'"
  if [[ "$kind" == zip ]]; then
    # Never silently overwrite a prior copy with the same release filename.
    rsync -rtv --progress --partial-dir=.rsync-partial --ignore-existing -- \
      "$src" "$REMOTE:$target/$pkg.zip"
    local_sha="$(sha256sum "$src" | awk '{print $1}')"
    remote_sha="$(ssh "$REMOTE" "sha256sum '$target/$pkg.zip'" | awk '{print $1}')"
    if [[ "$local_sha" != "$remote_sha" ]]; then
      echo "ERROR: SHA256 mismatch for $pkg; refusing to proceed" >&2
      exit 1
    fi
    echo "VERIFIED SHA256: $local_sha"
  else
    rsync -rtv --progress --partial-dir=.rsync-partial --ignore-existing -- \
      "$src/" "$REMOTE:$target/$pkg/"
    # Read-only checksum dry-run: nonempty output means a missing or different file.
    differences="$(rsync -rnc --out-format='%n' -- "$src/" "$REMOTE:$target/$pkg/")"
    if [[ -n "$differences" ]]; then
      printf 'ERROR: folder differs after upload (%s):\n%s\n' "$pkg" "$differences" >&2
      exit 1
    fi
    echo 'VERIFIED: remote files match local contents (rsync checksum scan)'
  fi
done

ssh "$REMOTE" 'mkdir -p "$HOME/CLM_FATES_scripts"'
rsync -rtv -- "$EXTRACTOR" "$REMOTE:CLM_FATES_scripts/01_extract_13_fluxnet_nested.py"
echo
echo 'SUCCESS: 13/13 source packages transferred and verified.'
echo 'NEXT on IRIDIS6:'
echo '  conda activate clm_fates_env'
echo '  python ~/CLM_FATES_scripts/01_extract_13_fluxnet_nested.py | tee ~/FLUXNET_13_extract.log'
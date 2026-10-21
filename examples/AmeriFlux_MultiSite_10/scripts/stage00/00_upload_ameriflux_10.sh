#!/usr/bin/env bash
# Stage 00: copy AmeriFlux source packages from a local WSL folder to IRIDIS6.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/../../sites.tsv"
LOCAL_ROOT="${LOCAL_ROOT:-/mnt/d/Fluxes_Tower_Experiment/AmeriFlux}"
REMOTE="${REMOTE:-ly3n24@iridis6.soton.ac.uk}"
REMOTE_ROOT="${REMOTE_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE}"

[[ -f "$MANIFEST" && -d "$LOCAL_ROOT" ]] || { echo "Missing manifest or LOCAL_ROOT=$LOCAL_ROOT" >&2; exit 2; }
for cmd in ssh rsync sha256sum find; do
    command -v "$cmd" >/dev/null || { echo "Missing command: $cmd" >&2; exit 2; }
done
declare -a SITES=() PACKAGES=() SOURCES=() KINDS=()
missing=0
while IFS=$'\t' read -r site package first_year last_year; do
    [[ -n "$site" && "$site" != "site" ]] || continue
    archive="$(find "$LOCAL_ROOT" -maxdepth 1 -type f -iname "$package.zip" -print -quit)"
    directory="$LOCAL_ROOT/$package"
    if [[ -n "$archive" ]]; then
        kind=zip
        source="$archive"
    elif [[ -d "$directory" ]]; then
        kind=dir
        source="$directory"
    else
        echo "MISSING: $site -> $package (.zip or directory)" >&2
        missing=1
        continue
    fi
    SITES+=("$site"); PACKAGES+=("$package"); SOURCES+=("$source"); KINDS+=("$kind")
    echo "FOUND: $site ($kind) $source"
done < "$MANIFEST"

if (( missing || ${#SITES[@]} != 10 )); then
    echo "ABORT: all 10 source releases are required. Nothing transferred." >&2
    exit 1
fi
echo "Preflight: 10/10 sources found."
ssh "$REMOTE" 'echo "IRIDIS hostname: $(hostname)"'

for i in "${!SITES[@]}"; do
    site="${SITES[$i]}"; package="${PACKAGES[$i]}"
    src="${SOURCES[$i]}"; kind="${KINDS[$i]}"
    dest="$REMOTE_ROOT/$site/forcing/packages"
    echo "========== [$((i+1))/10] $site =========="
    ssh "$REMOTE" "mkdir -p '$dest'"
    if [[ "$kind" == zip ]]; then
        rsync -rtv --progress --ignore-existing --partial-dir=.rsync-partial -- \
            "$src" "$REMOTE:$dest/$package.zip"
        lhs="$(sha256sum "$src" | awk '{print $1}')"
        rhs="$(ssh "$REMOTE" "sha256sum '$dest/$package.zip'" | awk '{print $1}')"
        [[ "$lhs" == "$rhs" ]] || { echo "SHA256 MISMATCH for $site; source not overwritten" >&2; exit 1; }
        echo "VERIFIED: $site SHA256=$lhs"
    else
        rsync -rtv --progress --ignore-existing --partial-dir=.rsync-partial -- \
            "$src/" "$REMOTE:$dest/$package/"
        differences="$(rsync -rnc --out-format='%n' -- "$src/" "$REMOTE:$dest/$package/")"
        [[ -z "$differences" ]] || { echo "CHECKSUM MISMATCH for $site: $differences" >&2; exit 1; }
        echo "VERIFIED: $site folder"
    fi
done
echo "UPLOAD VERIFIED: 10/10. Next run Stage 01 from your IRIDIS6 GitHub clone."

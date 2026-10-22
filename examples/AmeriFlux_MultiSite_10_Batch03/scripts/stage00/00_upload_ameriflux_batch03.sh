#!/usr/bin/env bash
# Run in LOCAL WSL. Copy originals; preserve local files and existing remote data.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/../../sites.tsv"
LOCAL_ROOT="${LOCAL_ROOT:-/mnt/d/Fluxes_Tower_Experiment/Ameriflux}"
REMOTE="${REMOTE:-ly3n24@iridis6.soton.ac.uk}"
REMOTE_ROOT="${REMOTE_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE}"

die() { echo "ERROR: $*" >&2; exit 1; }
for cmd in ssh rsync sha256sum find awk mktemp head; do
    command -v "$cmd" >/dev/null || die "Missing command: $cmd"
done
[[ -f "$MANIFEST" ]] || die "Missing manifest: $MANIFEST"
[[ -d "$LOCAL_ROOT" ]] || die "Missing LOCAL_ROOT: $LOCAL_ROOT (run in LOCAL WSL)"
[[ "$REMOTE" =~ ^[A-Za-z0-9_.-]+@[A-Za-z0-9.-]+$ ]] || die "REMOTE must be user@hostname"
[[ "$REMOTE_ROOT" =~ ^/[A-Za-z0-9_./-]+$ && "$REMOTE_ROOT/" != *'/../'* ]] || die "Invalid REMOTE_ROOT"
[[ "$(head -n 1 "$MANIFEST")" == $'site\tpackage\tfirst_year\tlast_year' ]] || die "Invalid manifest header"

declare -a SITES=() PACKAGES=() SOURCES=() KINDS=() HASHES=()
declare -A SEEN=()
missing=0
while IFS=$'\t' read -r site package first_year last_year extra; do
    [[ -n "$site" && "$site" != site ]] || continue
    [[ "$site" =~ ^US-[A-Za-z0-9]+$ && "$package" =~ ^AMF_US-[A-Za-z0-9_\.-]+$ \
        && "$first_year" =~ ^[0-9]{4}$ && "$last_year" =~ ^[0-9]{4}$ && -z "$extra" ]] || die "Invalid manifest row: $site"
    [[ "$package" == "AMF_${site}_FLUXNET_"* && -z "${SEEN[$site]:-}" ]] || die "Duplicate or inconsistent site: $site"
    SEEN[$site]=1
    mapfile -d '' -t archives < <(find "$LOCAL_ROOT" -maxdepth 1 -type f -iname "$package.zip" -print0)
    (( ${#archives[@]} <= 1 )) || die "Multiple ZIPs match $package"
    if (( ${#archives[@]} == 1 )); then
        kind=zip; source="${archives[0]}"
        [[ -s "$source" && -r "$source" ]] || die "Empty/unreadable archive: $source"
        hash="$(sha256sum < "$source" | awk '{print $1}')"
    elif [[ -d "$LOCAL_ROOT/$package" && ! -L "$LOCAL_ROOT/$package" ]]; then
        kind=dir; source="$LOCAL_ROOT/$package"; hash=''
        [[ -z "$(find "$source" -type l -print -quit)" ]] || die "Symlink in source folder: $source"
        [[ -n "$(find "$source" -type f -print -quit)" ]] || die "Empty source folder: $source"
    else
        echo "MISSING: $site -> $package (.zip or directory)" >&2
        missing=1
        continue
    fi
    SITES+=("$site"); PACKAGES+=("$package"); SOURCES+=("$source"); KINDS+=("$kind"); HASHES+=("$hash")
    echo "FOUND: $site ($kind) $source"
done < "$MANIFEST"
(( ! missing && ${#SITES[@]} == 10 )) || die "All 10 source releases are required. Nothing transferred."
echo "LOCAL PREFLIGHT: 10/10. ZIPs take priority over same-named extracted folders."

# Use a short, private Linux socket path, never a Windows /mnt/d socket.
# Only this master may prompt for credentials. Every later operation is batch-only.
SOCKET_DIR="$(mktemp -d /tmp/amf03.XXXXXX)"
SOCKET="$SOCKET_DIR/ssh"
cleanup() {
    ssh -S "$SOCKET" -O exit "$REMOTE" >/dev/null 2>&1 || true
    rm -f -- "$SOCKET"
    rmdir -- "$SOCKET_DIR" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
echo "Opening one SSH connection to $REMOTE; enter your password here if requested."
ssh -MNf -S "$SOCKET" -o ControlMaster=yes -o ControlPersist=no \
    -o BatchMode=no -o NumberOfPasswordPrompts=1 \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=30 "$REMOTE"
# ProxyCommand=false prevents a new network connection if the master disappears.
SSH_ARGS=(-S "$SOCKET" -o ControlMaster=no -o BatchMode=yes -o ProxyCommand=false)
RSYNC_SSH="ssh -S $SOCKET -o ControlMaster=no -o BatchMode=yes -o ProxyCommand=false"
remote() {
    ssh -S "$SOCKET" -O check "$REMOTE" >/dev/null 2>&1 || die "SSH master lost; rerun to resume. No password retry."
    ssh "${SSH_ARGS[@]}" "$REMOTE" "$@"
}
remote 'set -eu; command -v rsync >/dev/null; command -v sha256sum >/dev/null; printf "IRIDIS hostname: "; hostname'

for i in "${!SITES[@]}"; do
    site="${SITES[$i]}"; package="${PACKAGES[$i]}"
    src="${SOURCES[$i]}"; kind="${KINDS[$i]}"
    dest="$REMOTE_ROOT/$site/forcing/packages"
    echo "========== [$((i+1))/10] $site =========="
    # Refuse symlink packages and wrong file types at pre-existing destinations.
    remote "set -eu; mkdir -p '$dest'; test ! -L '$dest/$package.zip'; test ! -L '$dest/$package'; if test -e '$dest/$package.zip'; then test -f '$dest/$package.zip'; fi; if test -e '$dest/$package'; then test -d '$dest/$package'; fi"
    if [[ "$kind" == zip ]]; then
        rsync -rtv --progress --ignore-existing --partial-dir=.rsync-partial \
            -e "$RSYNC_SSH" -- "$src" "$REMOTE:$dest/$package.zip"
        lhs="${HASHES[$i]}"
        rhs="$(remote "sha256sum '$dest/$package.zip'" | awk '{print $1}')"
        [[ "$lhs" == "$rhs" ]] || die "SHA256 MISMATCH: $site. Existing remote file was preserved; inspect before retry."
        echo "VERIFIED: $site SHA256=$lhs"
    else
        rsync -rtv --progress --ignore-existing --partial-dir=.rsync-partial \
            -e "$RSYNC_SSH" -- "$src/" "$REMOTE:$dest/$package/"
        # --delete is dry-run ONLY: also detect unexpected extra remote files.
        differences="$(rsync -rcn --delete --itemize-changes --out-format='%i %n%L' \
            -e "$RSYNC_SSH" -- "$src/" "$REMOTE:$dest/$package/")"
        [[ -z "$differences" ]] || die "Folder CHECKSUM MISMATCH: $site: $differences (nothing deleted)"
        echo "VERIFIED: $site folder checksums"
    fi
done
echo "UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 03). Originals retained. No extraction or model jobs started."

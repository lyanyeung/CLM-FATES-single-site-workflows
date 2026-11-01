#!/usr/bin/env bash
# OzFlux MultiSite 09 Stage00: Windows WSL -> IRIDIS6, source-preserving.
# Transfer only. No renaming, overwriting, deleting, NetCDF editing or Slurm.
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${HERE}/../../sites.tsv"
LOCAL_ROOT="${LOCAL_ROOT:-/mnt/d/Fluxes_Tower_Experiment/Ozflux}"
REMOTE="${REMOTE:-ly3n24@iridis6.soton.ac.uk}"
REMOTE_ROOT="${REMOTE_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE}"

die() { printf 'STAGE00 ERROR: %s\n' "$*" >&2; exit 1; }
for cmd in ssh rsync sha256sum awk mktemp head; do
    command -v "$cmd" >/dev/null 2>&1 || die "Missing command: $cmd"
done
[[ $# -eq 0 || ( $# -eq 1 && "$1" == "--preflight-only" ) ]] || die "Usage: bash $0 [--preflight-only]"
[[ -f "$MANIFEST" ]] || die "Missing manifest: $MANIFEST"
[[ -d "$LOCAL_ROOT" ]] || die "LOCAL_ROOT missing: $LOCAL_ROOT (run on Windows WSL/Ubuntu, not IRIDIS)"
[[ "$REMOTE" =~ ^[A-Za-z0-9_.-]+@[A-Za-z0-9.-]+$ ]] || die "REMOTE must be user@host"
[[ "$REMOTE_ROOT" =~ ^/[A-Za-z0-9_./-]+$ && "$REMOTE_ROOT/" != *'/../'* ]] || die "Unsafe REMOTE_ROOT"
[[ "$(head -n 1 "$MANIFEST")" == $'site\tfilename' ]] || die "Unexpected manifest header"

declare -a SITES=() NAMES=() SOURCES=() HASHES=()
declare -A COUNT=() SEEN=()
expected=(AU-ASM AU-Cow AU-Cpr AU-DaS AU-Dry AU-Gin AU-How AU-Stp AU-Tum)
for site in "${expected[@]}"; do COUNT["$site"]=0; done

line_no=0
while IFS=    [[ "$site" =~ ^AU-[A-Za-z0-9]+$ && "$name" =~ ^[A-Za-z0-9_.-]+\.nc$ && -z "${extra:-}" ]] || die "Invalid manifest row: $site $name"
    [[ -v COUNT[$site] ]] || die "Unexpected site: $site"
    [[ ! -v SEEN[$site:$name] ]] || die "Duplicate filename: $site/$name"
    SEEN["$site:$name"]=1
    src="$LOCAL_ROOT/$site/$name"
    [[ -d "$LOCAL_ROOT/$site" && ! -L "$LOCAL_ROOT/$site" ]] || die "Missing/symlink site directory: $LOCAL_ROOT/$site"
    [[ -f "$src" && ! -L "$src" && -s "$src" && -r "$src" ]] || die "Missing/empty/unreadable/symlink: $src"
    hash="$(sha256sum < "$src" | awk '{print $1}')"
    [[ "$hash" =~ ^[a-f0-9]{64}$ ]] || die "Unable to hash: $src"
    SITES+=("$site"); NAMES+=("$name"); SOURCES+=("$src"); HASHES+=("$hash")
    COUNT["$site"]=$(( COUNT["$site"] + 1 ))
    printf 'LOCAL OK: %-7s %s SHA256=%s\n' "$site" "$name" "$hash"
done < "$MANIFEST"

[[ ${#SITES[@]} -eq 10 ]] || die "Expected exactly 10 source NetCDF files"
[[ ${#COUNT[@]} -eq 9 ]] || die "Expected 9 listed station directories"
for site in "${expected[@]}"; do
    want=1
    [[ "$site" == AU-ASM ]] && want=2
    [[ "${COUNT[$site]}" -eq "$want" ]] || die "Incorrect file count for $site: ${COUNT[$site]} expected $want"
done
printf 'LOCAL PREFLIGHT PASS: 9 station directories / 10 NetCDF files; originals untouched.\n'
if [[ "${1:-}" == "--preflight-only" ]]; then
    echo 'PREFLIGHT ONLY: no SSH connection or transfer.'
    exit 0
fi

# Single password/2FA handshake: require all later SSH and rsync calls to reuse it.
SOCKDIR="$(mktemp -d /tmp/ozflux09.XXXXXX)"
SOCKET="$SOCKDIR/master"
cleanup() {
    ssh -S "$SOCKET" -O exit "$REMOTE" >/dev/null 2>&1 || true
    rm -f -- "$SOCKET"
    rmdir -- "$SOCKDIR" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
echo "Opening SSH to $REMOTE (enter credentials if prompted)."
ssh -MNf -S "$SOCKET" -o ControlMaster=yes -o ControlPersist=no \
    -o BatchMode=no -o NumberOfPasswordPrompts=1 \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=30 "$REMOTE"
SSH_OPTS=(-S "$SOCKET" -o ControlMaster=no -o BatchMode=yes -o ProxyCommand=false)
RSYNC_SSH="ssh -S $SOCKET -o ControlMaster=no -o BatchMode=yes -o ProxyCommand=false"
remote() {
    ssh -S "$SOCKET" -O check "$REMOTE" >/dev/null 2>&1 || die 'SSH master lost; rerun script safely.'
    ssh "${SSH_OPTS[@]}" "$REMOTE" "$@"
}
remote 'set -eu; command -v rsync >/dev/null; command -v sha256sum >/dev/null; hostname'

for i in "${!SITES[@]}"; do
    site="${SITES[$i]}"
    name="${NAMES[$i]}"
    src="${SOURCES[$i]}"
    lhs="${HASHES[$i]}"
    dest="$REMOTE_ROOT/$site/forcing/raw"
    target="$dest/$name"
    printf '\n========== [%s/10] %s : %s ==========\n' "$((i+1))" "$site" "$name"
    remote "set -eu; mkdir -p '$dest'; test ! -L '$dest'; test ! -L '$target'; if test -e '$target'; then test -f '$target'; fi"
    exists="$(remote "if test -f '$target'; then echo YES; else echo NO; fi")"
    if [[ "$exists" == YES ]]; then
        rhs="$(remote "sha256sum '$target'" | awk '{print $1}')"
        [[ "$rhs" == "$lhs" ]] || die "REMOTE COLLISION $target: SHA256 differs. Original preserved; manual review required."
        echo "REMOTE EXISTS AND HASH MATCHES: $site/$name"
        continue
    fi
    rsync -rtv --progress --ignore-existing --partial-dir=.rsync-partial \
        -e "$RSYNC_SSH" -- "$src" "$REMOTE:$target"
    rhs="$(remote "sha256sum '$target'" | awk '{print $1}')"
    [[ "$rhs" == "$lhs" ]] || die "TRANSFER SHA256 MISMATCH: $target (no files removed/overwritten)"
    echo "TRANSFER SHA256 VERIFIED: $site/$name"
done
echo 'UPLOAD VERIFIED: 10/10 NetCDF files across 9 OzFlux sites. No model jobs submitted.'
\t' read -r site name extra || [[ -n "${site:-}" ]]; do
    line_no=$((line_no + 1))
    if (( line_no == 1 )); then
        [[ "$site" == site && "$name" == filename && -z "${extra:-}" ]] || die "Invalid manifest header row"
        continue
    fi
    [[ -n "${site:-}" ]] || continue
    [[ "$site" != "site" ]] || die "Duplicate manifest header"
    [[ "$site" =~ ^AU-[A-Za-z0-9]+$ && "$name" =~ ^[A-Za-z0-9_.-]+\.nc$ && -z "${extra:-}" ]] || die "Invalid manifest row: $site $name"
    [[ -v COUNT[$site] ]] || die "Unexpected site: $site"
    [[ ! -v SEEN[$site:$name] ]] || die "Duplicate filename: $site/$name"
    SEEN["$site:$name"]=1
    src="$LOCAL_ROOT/$site/$name"
    [[ -d "$LOCAL_ROOT/$site" && ! -L "$LOCAL_ROOT/$site" ]] || die "Missing/symlink site directory: $LOCAL_ROOT/$site"
    [[ -f "$src" && ! -L "$src" && -s "$src" && -r "$src" ]] || die "Missing/empty/unreadable/symlink: $src"
    hash="$(sha256sum < "$src" | awk '{print $1}')"
    [[ "$hash" =~ ^[a-f0-9]{64}$ ]] || die "Unable to hash: $src"
    SITES+=("$site"); NAMES+=("$name"); SOURCES+=("$src"); HASHES+=("$hash")
    COUNT["$site"]=$(( COUNT["$site"] + 1 ))
    printf 'LOCAL OK: %-7s %s SHA256=%s\n' "$site" "$name" "$hash"
done < "$MANIFEST"

[[ ${#SITES[@]} -eq 10 ]] || die "Expected exactly 10 source NetCDF files"
[[ ${#COUNT[@]} -eq 9 ]] || die "Expected 9 listed station directories"
for site in "${expected[@]}"; do
    want=1
    [[ "$site" == AU-ASM ]] && want=2
    [[ "${COUNT[$site]}" -eq "$want" ]] || die "Incorrect file count for $site: ${COUNT[$site]} expected $want"
done
printf 'LOCAL PREFLIGHT PASS: 9 station directories / 10 NetCDF files; originals untouched.\n'
if [[ "${1:-}" == "--preflight-only" ]]; then
    echo 'PREFLIGHT ONLY: no SSH connection or transfer.'
    exit 0
fi

# Single password/2FA handshake: require all later SSH and rsync calls to reuse it.
SOCKDIR="$(mktemp -d /tmp/ozflux09.XXXXXX)"
SOCKET="$SOCKDIR/master"
cleanup() {
    ssh -S "$SOCKET" -O exit "$REMOTE" >/dev/null 2>&1 || true
    rm -f -- "$SOCKET"
    rmdir -- "$SOCKDIR" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
echo "Opening SSH to $REMOTE (enter credentials if prompted)."
ssh -MNf -S "$SOCKET" -o ControlMaster=yes -o ControlPersist=no \
    -o BatchMode=no -o NumberOfPasswordPrompts=1 \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=30 "$REMOTE"
SSH_OPTS=(-S "$SOCKET" -o ControlMaster=no -o BatchMode=yes -o ProxyCommand=false)
RSYNC_SSH="ssh -S $SOCKET -o ControlMaster=no -o BatchMode=yes -o ProxyCommand=false"
remote() {
    ssh -S "$SOCKET" -O check "$REMOTE" >/dev/null 2>&1 || die 'SSH master lost; rerun script safely.'
    ssh "${SSH_OPTS[@]}" "$REMOTE" "$@"
}
remote 'set -eu; command -v rsync >/dev/null; command -v sha256sum >/dev/null; hostname'

for i in "${!SITES[@]}"; do
    site="${SITES[$i]}"
    name="${NAMES[$i]}"
    src="${SOURCES[$i]}"
    lhs="${HASHES[$i]}"
    dest="$REMOTE_ROOT/$site/forcing/raw"
    target="$dest/$name"
    printf '\n========== [%s/10] %s : %s ==========\n' "$((i+1))" "$site" "$name"
    remote "set -eu; mkdir -p '$dest'; test ! -L '$dest'; test ! -L '$target'; if test -e '$target'; then test -f '$target'; fi"
    exists="$(remote "if test -f '$target'; then echo YES; else echo NO; fi")"
    if [[ "$exists" == YES ]]; then
        rhs="$(remote "sha256sum '$target'" | awk '{print $1}')"
        [[ "$rhs" == "$lhs" ]] || die "REMOTE COLLISION $target: SHA256 differs. Original preserved; manual review required."
        echo "REMOTE EXISTS AND HASH MATCHES: $site/$name"
        continue
    fi
    rsync -rtv --progress --ignore-existing --partial-dir=.rsync-partial \
        -e "$RSYNC_SSH" -- "$src" "$REMOTE:$target"
    rhs="$(remote "sha256sum '$target'" | awk '{print $1}')"
    [[ "$rhs" == "$lhs" ]] || die "TRANSFER SHA256 MISMATCH: $target (no files removed/overwritten)"
    echo "TRANSFER SHA256 VERIFIED: $site/$name"
done
echo 'UPLOAD VERIFIED: 10/10 NetCDF files across 9 OzFlux sites. No model jobs submitted.'

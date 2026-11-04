#!/usr/bin/env bash
# Stage05BY: run in LOCAL WSL. Upload the JapanFlux2024 JP-Yms package (needed by Stage05BW rule D1 on IRIDIS6)
# with one SSH connection, never overwriting, and verify SHA-256 locally and remotely. The original is retained.
set -euo pipefail
SRC="${SRC:-/mnt/d/Fluxes_Tower_Experiment/JapanFlux/JP-Yms/A20241022-024_2.00_selected.zip}"
SHA=a112e8650592040b92698280416ac4b308a214ff1c5af8b8ee8d6e1ecf55d37d
REMOTE="${REMOTE:-ly3n24@iridis6.soton.ac.uk}"
DEST=/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/JP-Yms/forcing/packages/JapanFlux2024
NAME=A20241022-024_2.00_selected.zip
[ -f "$SRC" ] && [ ! -L "$SRC" ] || { echo "STOP: missing or symlink $SRC"; exit 1; }
echo "$SHA  $SRC" | sha256sum -c -
SOCKET_DIR="$(mktemp -d /tmp/jp11yms.XXXXXX)"; SOCKET="$SOCKET_DIR/ssh"
cleanup(){ ssh -S "$SOCKET" -O exit "$REMOTE" >/dev/null 2>&1 || true; rm -rf "$SOCKET_DIR"; }
trap cleanup EXIT
echo "Opening one SSH connection to $REMOTE; enter your password here if requested."
ssh -MNf -S "$SOCKET" -o ControlMaster=yes -o ControlPersist=no -o BatchMode=no -o NumberOfPasswordPrompts=1 \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=30 "$REMOTE"
R=(ssh -S "$SOCKET" -o ControlMaster=no -o BatchMode=yes -o ProxyCommand=false "$REMOTE")
"${R[@]}" "set -eu; mkdir -p '$DEST'; test ! -L '$DEST/$NAME'; if test -e '$DEST/$NAME'; then test -f '$DEST/$NAME'; fi"
rsync -tv --progress --ignore-existing --partial-dir=.rsync-partial \
    -e "ssh -S $SOCKET -o ControlMaster=no -o BatchMode=yes -o ProxyCommand=false" -- "$SRC" "$REMOTE:$DEST/$NAME"
RHS="$("${R[@]}" "sha256sum '$DEST/$NAME'" | awk '{print $1}')"
[ "$RHS" = "$SHA" ] || { echo "SHA256 MISMATCH on IRIDIS: $RHS (remote file preserved; inspect before retry)"; exit 1; }
echo "UPLOAD VERIFIED: JP-Yms JapanFlux2024 SHA256=$SHA at $DEST/$NAME"

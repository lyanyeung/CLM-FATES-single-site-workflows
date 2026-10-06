#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

# Run this script on LOCAL WSL, not on IRIDIS.

REMOTE_RAW="${RAW_ROOT}"

echo "Creating remote raw-data directory..."
ssh "${IRIDIS_USER}@${IRIDIS_HOST}" "mkdir -p '${REMOTE_RAW}'"

echo "Transferring ES-LJu raw package..."
rsync -avh --progress \
  "${LOCAL_RAW}/" \
  "${IRIDIS_USER}@${IRIDIS_HOST}:${REMOTE_RAW}/"

echo
echo "Transfer complete."
echo "Remote directory: ${REMOTE_RAW}"

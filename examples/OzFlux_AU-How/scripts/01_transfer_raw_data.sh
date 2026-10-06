#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

# Run on LOCAL WSL.
ssh "${IRIDIS_USER}@${IRIDIS_HOST}" \
  "mkdir -p '$(dirname "${REMOTE_RAW}")'"

rsync -avh --progress \
  "${LOCAL_RAW}" \
  "${IRIDIS_USER}@${IRIDIS_HOST}:${REMOTE_RAW}"

echo
echo "Transferred:"
echo "  ${LOCAL_RAW}"
echo "to:"
echo "  ${REMOTE_RAW}"

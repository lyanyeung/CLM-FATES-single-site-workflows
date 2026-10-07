#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

# Run on local WSL.

if [[ ! -f "${LOCAL_ZIP}" ]]; then
    echo "Missing local ZIP: ${LOCAL_ZIP}"
    exit 1
fi

ssh "${IRIDIS_USER}@${IRIDIS_HOST}" \
    "mkdir -p '${RAW_ROOT}'"

rsync -avh --progress \
    "${LOCAL_ZIP}" \
    "${IRIDIS_USER}@${IRIDIS_HOST}:${RAW_ROOT}/"

ssh "${IRIDIS_USER}@${IRIDIS_HOST}" \
    "cd '${RAW_ROOT}' && unzip -o '${RAW_ZIP_NAME}'"

echo "US-Ha1 AmeriFlux package transferred and extracted."

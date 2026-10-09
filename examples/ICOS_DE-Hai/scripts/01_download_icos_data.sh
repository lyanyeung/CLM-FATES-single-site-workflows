#!/usr/bin/env bash
# Run on an IRIDIS6 login node, not on a compute node.
# Usage: bash scripts/01_download_icos_data.sh [--dry-run]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

URL="https://data.icos-cp.eu/objects/${ICOS_PID}"
META_URL="https://meta.icos-cp.eu/objects/${ICOS_PID}"
EXPECTED="${ICOS_SHA256}"

printf 'Site:      %s\nProduct:   %s\nPID:       11676/%s\nDirectory: %s\n' \
    "${SITE}" "${RAW_PACKAGE_NAME}" "${ICOS_PID}" "${RAW_ROOT}"

if [[ "${1:-}" == "--dry-run" ]]; then
    printf 'Download:  %s\n' "${URL}"
    exit 0
fi
if [[ $# -ne 0 ]]; then
    printf 'Usage: bash %s [--dry-run]\n' "${0}" >&2
    exit 2
fi

for command in curl sha256sum unzip; do
    command -v "${command}" >/dev/null || {
        printf 'Missing required command: %s\n' "${command}" >&2
        exit 1
    }
done

mkdir -p "${RAW_ROOT}" "${SITE_ROOT}/forcing/processed" \
    "${SITE_ROOT}/obs" "${SITE_ROOT}/forcing/datm"

# Do not silently replace existing data. If the expected file exists and
# matches the published SHA-256, safely reuse it.
valid_zip=false
if [[ -f "${RAW_ZIP}" ]]; then
    actual="$(sha256sum "${RAW_ZIP}")"
    actual="${actual%% *}"
    if [[ "${actual}" != "${EXPECTED}" ]]; then
        printf 'Existing archive has an unexpected SHA-256: %s\n' "${RAW_ZIP}" >&2
        printf 'Expected: %s\nActual:   %s\n' "${EXPECTED}" "${actual}" >&2
        printf 'Move the existing archive aside manually before retrying.\n' >&2
        exit 1
    fi
    printf 'Already downloaded and SHA-256 verified.\n'
    valid_zip=true
fi

if [[ "${valid_zip}" == false ]]; then
    # ICOS requires the user's accepted data licence and short-lived
    # cpauthToken. Do not put credentials in source control or shell history.
    if [[ -z "${ICOS_TOKEN:-}" ]]; then
        if [[ ! -t 0 ]]; then
            printf 'Set ICOS_TOKEN for non-interactive use.\n' >&2
            exit 1
        fi
        read -r -s -p 'ICOS cpauthToken (hidden): ' ICOS_TOKEN
        printf '\n'
    fi
    # Accept both copied cookie formats: "VALUE" and "cpauthToken=VALUE".
    # ICOS documentation shows both conventions.
    ICOS_TOKEN="${ICOS_TOKEN//$'\r'/}"
    ICOS_TOKEN="${ICOS_TOKEN#"${ICOS_TOKEN%%[![:space:]]*}"}"
    ICOS_TOKEN="${ICOS_TOKEN%"${ICOS_TOKEN##*[![:space:]]}"}"
    if [[ "${ICOS_TOKEN}" == cpauthToken=* ]]; then
        ICOS_TOKEN="${ICOS_TOKEN#cpauthToken=}"
        printf 'Full cpauthToken= prefix detected; normalized automatically.\n'
    fi
    if [[ -z "${ICOS_TOKEN}" || "${ICOS_TOKEN}" == cpauthToken=* ]]; then
        printf 'Missing or malformed ICOS token.\n' >&2
        exit 1
    fi

    # Mode-600 curl config keeps the token out of process arguments.
    umask 077
    CURL_CONFIG="$(mktemp "${TMPDIR:-/tmp}/icos_curl.XXXXXXXX")"
    trap 'rm -f "${CURL_CONFIG}"' EXIT
    printf 'cookie = "cpauthToken=%s"\n' "${ICOS_TOKEN}" > "${CURL_CONFIG}"
    unset ICOS_TOKEN

    PART="${RAW_ZIP}.part"
    printf 'Downloading from ICOS on this login node...\n'
    curl --fail --location --retry 3 --connect-timeout 30 \
        --config "${CURL_CONFIG}" \
        --output "${PART}" "${URL}"

    # HTTP 200 may still be an ICOS Data Licence HTML page.
    if [[ "$(head -c 2 "${PART}")" != "PK" ]]; then
        if grep -qi '<title>Data Licence' "${PART}"; then
            printf 'ICOS returned the Data Licence page, not ZIP data.\n' >&2
            printf 'Check saved licence acceptance and API cookie authentication.\n' >&2
        else
            printf 'Downloaded response is not a ZIP. Inspect: file %s\n' "${PART}" >&2
        fi
        printf 'Response retained at: %s\n' "${PART}" >&2
        exit 1
    fi

    actual="$(sha256sum "${PART}")"
    actual="${actual%% *}"
    if [[ "${actual}" != "${EXPECTED}" ]]; then
        printf 'SHA-256 check FAILED. Do not use the downloaded file.\n' >&2
        printf 'Expected: %s\nActual:   %s\n' "${EXPECTED}" "${actual}" >&2
        printf 'Unverified file retained at: %s\n' "${PART}" >&2
        exit 1
    fi
    mv -- "${PART}" "${RAW_ZIP}"
    printf 'Download SHA-256 verified.\n'
fi

unzip -tqq "${RAW_ZIP}"
if [[ -d "${RAW_EXTRACTED}" ]] && \
   find "${RAW_EXTRACTED}" -type f -iname '*FLUXMET*HH*.csv' -print -quit | grep -q .; then
    printf 'Extraction directory already contains FLUXMET; not overwriting.\n'
else
    mkdir -p "${RAW_EXTRACTED}"
    unzip -q -n "${RAW_ZIP}" -d "${RAW_EXTRACTED}"
fi
if ! find "${RAW_EXTRACTED}" -type f -iname '*FLUXMET*HH*.csv' -print -quit | grep -q .; then
    printf 'No FLUXMET half-hourly CSV found after extraction; inspect archive structure.\n' >&2
    exit 1
fi

# Metadata are public and useful for source-data provenance.
if ! curl --fail --location --silent --show-error \
    -H 'Accept: application/json' \
    -o "${RAW_ROOT}/${RAW_PACKAGE_NAME}_metadata.json" "${META_URL}"; then
    printf 'Warning: Could not download supplemental JSON metadata.\n' >&2
fi

cat > "${RAW_ROOT}/${RAW_PACKAGE_NAME}_SOURCE.txt" <<SOURCE
Site: ${SITE}
ICOS product: ${RAW_PACKAGE_NAME}
PID: 11676/${ICOS_PID}
Landing page: ${META_URL}
Direct object URL: ${URL}
SHA-256 (verified): ${EXPECTED}
Years: ${START_YEAR}-${END_YEAR}
Source: ICOS Carbon Portal (see PID for licence/citation)
SOURCE

printf '\nDownloaded archive: %s\n' "${RAW_ZIP}"
printf 'Extracted data:    %s\n' "${RAW_EXTRACTED}"
printf '\nKey CSV files (possibly nested in the source archive):\n'
find "${RAW_EXTRACTED}" -type f \
    \( -iname '*FLUXMET*HH*.csv' -o -iname '*ERA5*HH*.csv' \
       -o -iname '*BIF*.csv' \) -print | head -25
printf '\nNext: inspect the extracted file paths and variable availability before writing DE-Hai forcing.\n'

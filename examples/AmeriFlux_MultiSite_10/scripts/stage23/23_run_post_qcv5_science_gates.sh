#!/usr/bin/env bash
# Version-pinned post-QCv5 gates, AmeriFlux Batch 01 (ten sites).
# Original FLUXNET_MultiSite_8 QCv5 engine is unchanged. Stages 21 and 22
# only inspect candidates and raw source. Downloads use a fixed GitHub commit.
set -Eeuo pipefail

usage() {
  cat <<'USAGE'
Usage: bash 23_run_post_qcv5_science_gates.sh check
       bash 23_run_post_qcv5_science_gates.sh audit

check: read-only preflight; audit: repeat Stage21 then Stage22 reports.
Both read Stage18's nine-site candidate and Stage20's isolated US-Bar candidate.
Audit writes new timestamped REPORTS ONLY; no source/forcing/DATM/CIME edits.

Optional environment:
  STAGE18_ROOT=<absolute original-QCv5 trial dir>
  STAGE20_ROOT=<absolute US-Bar scoped trial dir>
  PYTHON=<Python executable, default python3>
USAGE
}

if [[ $# -ne 1 || ( "$1" != "check" && "$1" != "audit" ) ]]; then
  usage >&2
  exit 2
fi

MODE="$1"
PYTHON="${PYTHON:-python3}"
STAGE18_ROOT="${STAGE18_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/qcv5_trial_20261021T232839Z}"
STAGE20_ROOT="${STAGE20_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/usbar_scoped_trial_20261021T234357Z}"
# Frozen tested Stage21/22 scripts, including Stage22 v2 end-year fix.
SOURCE_REV="1e2f259ac616b0bdc24e4f5ea5c2c6ea92d1d315"
URL_BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$SOURCE_REV/examples/AmeriFlux_MultiSite_10"

if [[ ! -d "$STAGE18_ROOT" || ! -d "$STAGE20_ROOT" ]]; then
  echo "ERROR: required historical Stage18/Stage20 trial directory missing" >&2
  exit 2
fi
if [[ "$STAGE18_ROOT" == "$STAGE20_ROOT" ]]; then
  echo "ERROR: trials must remain separated" >&2
  exit 2
fi

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ameriflux_postv5_XXXXXX")"
cleanup() { rm -rf -- "$TMP_ROOT"; }
trap cleanup EXIT
BATCH="$TMP_ROOT/examples/AmeriFlux_MultiSite_10"
mkdir -p "$BATCH/scripts/stage21" "$BATCH/scripts/stage22"
stage21="$BATCH/scripts/stage21/21_verify_ten_qcv5_candidates.py"
stage22="$BATCH/scripts/stage22/22_post_qcv5_extremes_source_switches.py"

curl -fLsS --retry 3 "$URL_BASE/sites.tsv" -o "$BATCH/sites.tsv"
curl -fLsS --retry 3 \
  "$URL_BASE/scripts/stage21/21_verify_ten_qcv5_candidates.py" -o "$stage21"
curl -fLsS --retry 3 \
  "$URL_BASE/scripts/stage22/22_post_qcv5_extremes_source_switches.py" -o "$stage22"

"$PYTHON" -m py_compile "$stage21" "$stage22"
grep -Fq '20261022_stage22_end_year_fix_v2' "$stage22" || {
  echo "ERROR: stage22 v2 source marker missing; stop" >&2
  exit 2
}
grep -Fq 'range(first,end_year+1)' "$stage22" || {
  echo "ERROR: stage22 end_year fix missing; stop" >&2
  exit 2
}

echo "POST-QCV5 RUNNER: $MODE"
echo "VERSION-PINNED AUDIT SOURCE COMMIT: $SOURCE_REV"
echo "STAGE18: $STAGE18_ROOT"
echo "STAGE20: $STAGE20_ROOT"
echo "Stage18 INCOMPLETE marker is expected because US-Bar is separately stored."
echo "Only read-only source/candidate access; new reports ONLY in audit mode."

echo "=== STAGE21 PREFLIGHT ==="
"$PYTHON" -B "$stage21" --check \
  --stage18-root "$STAGE18_ROOT" --stage20-root "$STAGE20_ROOT"
echo "=== STAGE22 PREFLIGHT ==="
"$PYTHON" -B "$stage22" --check \
  --stage18-root "$STAGE18_ROOT" --stage20-root "$STAGE20_ROOT"

if [[ "$MODE" == "check" ]]; then
  echo "POST-QCV5 CHECK OK. NO REPORTS OR CANDIDATES WRITTEN."
  exit 0
fi

echo "=== STAGE21 INDEPENDENT NUMERIC/PROVENANCE AUDIT ==="
"$PYTHON" -B "$stage21" --audit \
  --stage18-root "$STAGE18_ROOT" --stage20-root "$STAGE20_ROOT"
echo "=== STAGE22 SCIENCE/EXTREME/SOURCE AUDIT ==="
"$PYTHON" -B "$stage22" --audit \
  --stage18-root "$STAGE18_ROOT" --stage20-root "$STAGE20_ROOT"

echo "POST-QCV5 AUDIT COMPLETED. STILL NOT SCIENCE-APPROVED FOR DATM OR SPINUP."

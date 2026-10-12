#!/usr/bin/env bash
# WSL: bring the ACTUAL final IRIDIS scripts into this GitHub example, in one SSH session.
# Does not copy raw data, forcing CSV, generated NetCDF, logs or tokens.
set -euo pipefail

REMOTE="${IRIDIS_SSH:-ly3n24@iridis6.soton.ac.uk}"
REMOTE_HOME="${IRIDIS_HOME:-/home/ly3n24}"
DEST="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

command -v ssh >/dev/null || { echo 'ERROR: ssh missing' >&2; exit 2; }
command -v tar >/dev/null || { echo 'ERROR: tar missing' >&2; exit 2; }

# Remote script writes ONLY a tar stream to stdout; human messages go to stderr.
ssh "$REMOTE" "bash -s -- '$REMOTE_HOME'" <<'REMOTE_SCRIPT' | tar -xf - -C "$TMP"
set -euo pipefail
cd -- "$1"
required=(
  make_8_surfaces.sh
  03_prepare_eight_site_forcing_v5.py
  07_make_eight_site_datm_timevarying_zbot.py
  08_audit_eight_site_datm_surface.py
  09_FRHes_manual_v1_rebuild_eight_datm.py
)
optional=(
  extract_8_fluxnet_nested.py
  03a_check_8_site_coverage.py
  04_audit_eight_site_qc_v5.py
  04b_check_eight_site_era_usage.py
  04c_check_annual_era_usage.py
  04d_diagnose_DE_Hzd_precip.py
  04e_final_check_two_sites.py
  review_15_events_readonly.py
  07_make_eight_site_datm_FRHes_manual_v1.py
)
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "MISSING REQUIRED IRIDIS SCRIPT: $PWD/$f" >&2
    exit 2
  fi
done
present=("${required[@]}")
for f in "${optional[@]}"; do
  if [[ -f "$f" ]]; then present+=("$f"); else echo "Optional script absent: $f" >&2; fi
done
# No user data: only exact file names explicitly enumerated above.
tar -cf - -- "${present[@]}"
REMOTE_SCRIPT

copy_one() {
  local src="$1" dst="$2"
  if [[ -f "$TMP/$src" ]]; then
    if [[ -f "$DEST/$dst" ]] && cmp -s -- "$TMP/$src" "$DEST/$dst"; then
      echo "UNCHANGED $dst"
    else
      cp -f -- "$TMP/$src" "$DEST/$dst"
      echo "COPIED    $dst"
    fi
  fi
}
copy_one make_8_surfaces.sh 02_make_8_surfaces.sh
copy_one extract_8_fluxnet_nested.py 01_extract_8_fluxnet_nested.py
for f in \
  03_prepare_eight_site_forcing_v5.py \
  07_make_eight_site_datm_timevarying_zbot.py \
  08_audit_eight_site_datm_surface.py \
  09_FRHes_manual_v1_rebuild_eight_datm.py \
  03a_check_8_site_coverage.py \
  04_audit_eight_site_qc_v5.py \
  04b_check_eight_site_era_usage.py \
  04c_check_annual_era_usage.py \
  04d_diagnose_DE_Hzd_precip.py \
  04e_final_check_two_sites.py \
  review_15_events_readonly.py \
  07_make_eight_site_datm_FRHes_manual_v1.py; do
  copy_one "$f" "$f"
done

printf '\n=== Python syntax check ===\n'
python3 - "$DEST" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]); failures=0
for p in sorted(root.glob('*.py')):
    try: compile(p.read_bytes(), str(p), 'exec')
    except (SyntaxError, UnicodeError) as exc:
        print('FAIL',p.name,exc); failures+=1
    else: print('OK ',p.name)
if failures:sys.exit(1)
PY
printf '\nFinished. Please review git status/diff before committing.\n'

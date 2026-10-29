#!/usr/bin/env bash
set -euo pipefail

# ALL work remains in this subshell. Never lower an already-high stack.
before_soft="$(ulimit -s)"
if [ "$before_soft" != "unlimited" ]; then
  ulimit -s unlimited 2>/dev/null || true
fi
echo "BATCH05 STAGE99 SHELL_STACK before=$before_soft now=$(ulimit -s)"
BASE="$HOME/ameriflux_batch05_AD400_full_preparation"
mkdir -p "$BASE"
COMMIT="700e0e5e0e8af0939decf9e6f175c5b65679914c"
PREFIX="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch05/scripts/AD400_direct_preflight"
GUARD="$BASE/batch05_direct_ad400_stack_guard.py"
SCRIPT="$BASE/99_batch05_full_HPC_direct_AD400_inventory.py"
curl -fLsS --retry 3 "$PREFIX/batch05_direct_ad400_stack_guard.py" -o "$GUARD"
test "$(git hash-object "$GUARD")" = "89239f1b5f2e98ee7af8108c2d31df21e5e3ebab"
curl -fLsS --retry 3 "$PREFIX/99_batch05_real_path_surface_datm_case_stack_and_quotas_READONLY.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "b61b081209790deacb1b543ed15e02ba27d783bb"
echo "STAGE99 GITHUB BOTH PYTHON SOURCE SHA VERIFIED"
python3 -B -m py_compile "$GUARD" "$SCRIPT"
python3 -B "$GUARD" --self-test
python3 -B "$SCRIPT" --self-test
python3 -B "$GUARD" --check

STAGE98="$HOME/ameriflux_batch05_directAD400_preflight/readiness_20261029T080621Z_3578563"
STAGE90="$HOME/ameriflux_batch05_stage90/ten_site_remaining_risks_20261029T070834Z_2339016"
OUT="$BASE/preparation_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage98 "$STAGE98" --stage90 "$STAGE90" --out "$OUT" \
  2>&1 | tee "$BASE/stage99_preparation_audit.log"
echo "STAGE99_REPORTS=$OUT"
echo "STAGE99 10 SITE DIRECT AD400 (80x5) PREP ONLY | NO PILOT AD5, NO DATM/SURFACE/CIME/SLURM WRITES"

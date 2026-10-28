#!/usr/bin/env bash
# US-Me6 Stage13AK ORIGINAL source all-years QC0 / winter T donor check.
# NO REPAIRS, NO MODEL INPUT, NO SLURM. Fail closed on git source hash.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13ak"
mkdir -p "$BASE"
PIN="3c662eb2a16640d3033376bb3e9d2ef2a2ae6ada"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r BLOB FILE; do
 curl -fLsS --retry 3 "$RAW/$FILE" -o "$BASE/$FILE"
 test "$(git hash-object "$BASE/$FILE")" = "$BLOB"
done <<'SIX_PINNED_ORIGINAL_SOURCES'
a8b2556cc880d3ed3bab9fac56246d4a4921c9ab 13ak_Me6_19HH_multi_year_QC0_winter_temperature_donor_READONLY.py
62fb8b5225157f989d58c7a31d6a0a61237d4646 13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py
c0b7f0429d352c82a10becf8d59d8a5d62987edf 13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
SIX_PINNED_ORIGINAL_SOURCES
echo "STAGE13AK SIX ORIGINAL SCIENCE SOURCES VERIFIED"
python3 -B - "$BASE" <<'PY'
import sys
from pathlib import Path
for p in Path(sys.argv[1]).glob("*.py"):
    compile(p.read_text(),str(p),"exec")
print("STAGE13AK ALL SOURCES SYNTAX PASS | NO WRITES",flush=True)
PY
P="$BASE/13ak_Me6_19HH_multi_year_QC0_winter_temperature_donor_READONLY.py"
python3 -B "$P" --self-test
python3 -B "$P" --run 2>&1 | tee "$BASE/stage13ak_19HH_source_16year_QC0_T.log"
grep -qF "STAGE13AK 19HH 16YEAR ORIGINAL QC0 ERA TEMPERATURE DONOR REVIEW COMPLETE" \
  "$BASE/stage13ak_19HH_source_16year_QC0_T.log"
echo "STAGE13AK ORIGINAL QC0 SOURCE AUDIT DONE | NO MODEL/SLURM"

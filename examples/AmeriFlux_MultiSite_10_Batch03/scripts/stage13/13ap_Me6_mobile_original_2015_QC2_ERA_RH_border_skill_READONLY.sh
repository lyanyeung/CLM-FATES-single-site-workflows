#!/usr/bin/env bash
# Batch03 US-Me6 Stage13AP: two original source QC2 ERA temperature mismatched
# borders vs original ERA RH transfer to site T, QC0 donor skill; READONLY.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13ap"
mkdir -p "$B"
PIN="c9fc2913542e6c82c472acda1fbb78a0ac014759"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r BLOB FILE; do
  curl -fLsS --retry 3 "$RAW/$FILE" -o "$B/$FILE"
  test "$(git hash-object "$B/$FILE")" = "$BLOB"
done <<'NINE_ORIGINAL_SHA_SOURCE_FILES'
0c03987a8ef9324826beb809cafab438b9dbf7c6 13ap_Me6_2015_original_QC2_ERA_RH_border_donor_skill_READONLY.py
df561eb8904b0147fc4a5aa0f977a5ec66545477 13am_Me6_19HH_joint_QC0_bias_corrected_ERA_RH_event_PREVIEW_READONLY.py
440e02cd7fd54d2a3fc9661a977d55125c513dde 13al_Me6_19HH_joint_cold_and_ERA_Tbias_QC0_leave_year_out_READONLY.py
5e82bd31484a3949a43829264f3ceb4d6c0f7832 13ak_Me6_19HH_multi_year_QC0_winter_temperature_donor_READONLY.py
62fb8b5225157f989d58c7a31d6a0a61237d4646 13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py
c0b7f0429d352c82a10becf8d59d8a5d62987edf 13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
NINE_ORIGINAL_SHA_SOURCE_FILES
echo "STAGE13AP NINE ORIGINAL SCIENCE SOURCES GIT SHA VERIFIED"
python3 -B - "$B" <<'PY'
import sys
from pathlib import Path
for file in Path(sys.argv[1]).glob("*.py"):
    compile(file.read_text(),str(file),"exec")
print("STAGE13AP PYTHON SYNTAX PASS | NO SOURCE/MODEL WRITES",flush=True)
PY
SCRIPT="$B/13ap_Me6_2015_original_QC2_ERA_RH_border_donor_skill_READONLY.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --run 2>&1 | tee "$B/stage13ap_QC2_source_ERA_RH_border_QC0.log"
grep -qF "STAGE13AP TWO ORIGINAL QC2 BORDER ERA RH AND QC0 SKILL REVIEW COMPLETE" \
  "$B/stage13ap_QC2_source_ERA_RH_border_QC0.log"
echo "STAGE13AP SOURCE SCIENCE READONLY COMPLETE | 19HH HOLD, 45 HH MISSING, NO SLURM"

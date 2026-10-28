#!/usr/bin/env bash
# Batch03 US-Me6 Stage13AL: exact signed original 19HH cold event
# plus 2010-2025 measured QC0 matching BOTH tower T and site-ERA T.
# Read-only diagnostic: no source/research-shadow/DATM/Slurm modifications.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13al"
mkdir -p "$B"
PIN="190bf549b3e38e753ec4b8fdb5b9569f4a53e74a"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r BLOB NAME; do
 curl -fLsS --retry 3 "$RAW/$NAME" -o "$B/$NAME"
 test "$(git hash-object "$B/$NAME")" = "$BLOB"
done <<'ORIGINAL_SCIENCE_SHA_PINS'
440e02cd7fd54d2a3fc9661a977d55125c513dde 13al_Me6_19HH_joint_cold_and_ERA_Tbias_QC0_leave_year_out_READONLY.py
5e82bd31484a3949a43829264f3ceb4d6c0f7832 13ak_Me6_19HH_multi_year_QC0_winter_temperature_donor_READONLY.py
62fb8b5225157f989d58c7a31d6a0a61237d4646 13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py
c0b7f0429d352c82a10becf8d59d8a5d62987edf 13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
ORIGINAL_SCIENCE_SHA_PINS
echo "STAGE13AL SEVEN ORIGINAL SCIENCE GIT BLOBS VERIFIED"
python3 -B - "$B" <<'PY'
import sys
from pathlib import Path
for f in Path(sys.argv[1]).glob("*.py"):
    compile(f.read_text(),str(f),"exec")
print("STAGE13AL ALL PYTHON SYNTAX PASS | NO WRITES",flush=True)
PY
P="$B/13al_Me6_19HH_joint_cold_and_ERA_Tbias_QC0_leave_year_out_READONLY.py"
python3 -B "$P" --self-test
python3 -B "$P" --run 2>&1 | tee "$B/stage13al_joint_original_source_QC0.log"
grep -qF "STAGE13AL 19HH TRUE QC0 JOINT SOURCE TEMPERATURE DONOR REVIEW COMPLETE" \
  "$B/stage13al_joint_original_source_QC0.log"
echo "STAGE13AL 19HH SOURCE-ONLY CONDITIONAL EVIDENCE REPORT DONE | NO DATM/SLURM"

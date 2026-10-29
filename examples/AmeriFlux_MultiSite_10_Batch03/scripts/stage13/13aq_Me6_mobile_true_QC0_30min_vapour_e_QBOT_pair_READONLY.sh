#!/usr/bin/env bash
# US-Me6 Stage13AQ, strict consecutive original VPD_F/TA_F both QC0
# half-hour measurement pairs compared with unmodified QC2 event borders.
# READONLY. No approval, forcing, shadow, model, DATM, AD400 or Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13aq"
mkdir -p "$BASE"
PIN="4efb8f4b4ae707f27aa1de737d3166f43e09fb75"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r SHA F; do
  curl -fLsS --retry 3 "$RAW/$F" -o "$BASE/$F"
  test "$(git hash-object "$BASE/$F")" = "$SHA"
done <<'TEN_PINNED_SOURCES'
ff9bc87a9bd56e1365f2b93a55edc6d2b5a71aa4 13aq_Me6_2015_QC0_measured_30min_edge_vapour_transition_READONLY.py
0c03987a8ef9324826beb809cafab438b9dbf7c6 13ap_Me6_2015_original_QC2_ERA_RH_border_donor_skill_READONLY.py
df561eb8904b0147fc4a5aa0f977a5ec66545477 13am_Me6_19HH_joint_QC0_bias_corrected_ERA_RH_event_PREVIEW_READONLY.py
440e02cd7fd54d2a3fc9661a977d55125c513dde 13al_Me6_19HH_joint_cold_and_ERA_Tbias_QC0_leave_year_out_READONLY.py
5e82bd31484a3949a43829264f3ceb4d6c0f7832 13ak_Me6_19HH_multi_year_QC0_winter_temperature_donor_READONLY.py
62fb8b5225157f989d58c7a31d6a0a61237d4646 13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py
c0b7f0429d352c82a10becf8d59d8a5d62987edf 13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
TEN_PINNED_SOURCES
echo "STAGE13AQ TEN ORIGINAL SCIENCE SOURCES GIT SHA VERIFIED"
python3 -B - "$BASE" <<'PY'
import sys
from pathlib import Path
for f in Path(sys.argv[1]).glob("*.py"):
    compile(f.read_text(),str(f),"exec")
print("STAGE13AQ PYTHON SYNTAX PASS | NO MODEL WRITES",flush=True)
PY
SCRIPT="$BASE/13aq_Me6_2015_QC0_measured_30min_edge_vapour_transition_READONLY.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage13aq_true_QC0_30min_vapour_edge_pairs.log"
grep -qF "STAGE13AQ 19HH TWO QC2 BORDERS ORIGINAL QC0 MEASURED PAIR REVIEW COMPLETE" \
 "$BASE/stage13aq_true_QC0_30min_vapour_edge_pairs.log"
echo "STAGE13AQ READONLY SOURCE SCIENCE COMPLETE | 45 HH STILL HOLD | NO SLURM"

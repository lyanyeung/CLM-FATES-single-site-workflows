#!/usr/bin/env bash
# AmeriFlux Batch03 US-Me6 Stage13AM; *read-only* 19-HH event-specific
# QC0 bias corrected ERA water-RH donor preview and physical/edge diagnostics.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13am"
mkdir -p "$BASE"
PIN="d67e49ec9f183cf49369fb99af3acd5a8a143a51"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r GIT_SHA NAME; do
 curl -fLsS --retry 3 "$RAW/$NAME" -o "$BASE/$NAME"
 test "$(git hash-object "$BASE/$NAME")" = "$GIT_SHA"
done <<'SIGNED_SCIENCE_PYTHONS'
df561eb8904b0147fc4a5aa0f977a5ec66545477 13am_Me6_19HH_joint_QC0_bias_corrected_ERA_RH_event_PREVIEW_READONLY.py
440e02cd7fd54d2a3fc9661a977d55125c513dde 13al_Me6_19HH_joint_cold_and_ERA_Tbias_QC0_leave_year_out_READONLY.py
5e82bd31484a3949a43829264f3ceb4d6c0f7832 13ak_Me6_19HH_multi_year_QC0_winter_temperature_donor_READONLY.py
62fb8b5225157f989d58c7a31d6a0a61237d4646 13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py
c0b7f0429d352c82a10becf8d59d8a5d62987edf 13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
SIGNED_SCIENCE_PYTHONS
echo "STAGE13AM EIGHT ORIGINAL GIT-SHA SCIENCE SOURCES VERIFIED"
python3 -B - "$BASE" <<'PY'
from pathlib import Path
import sys
for x in Path(sys.argv[1]).glob("*.py"):
    compile(x.read_text(),str(x),"exec")
print("STAGE13AM SOURCE SYNTAX PASS | NO FORCING WRITES",flush=True)
PY
P="$BASE/13am_Me6_19HH_joint_QC0_bias_corrected_ERA_RH_event_PREVIEW_READONLY.py"
python3 -B "$P" --self-test
python3 -B "$P" --run 2>&1 | tee "$BASE/stage13am_original_19HH_QC0_donor_preview.log"
grep -qF "STAGE13AM NINETEEN HH JOINT QC0 BIAS PREVIEW COMPLETE" \
 "$BASE/stage13am_original_19HH_QC0_donor_preview.log"
echo "STAGE13AM 19HH PREVIEW COMPLETE | NO SHADOW/FORCING/DATM/AD400/SLURM"

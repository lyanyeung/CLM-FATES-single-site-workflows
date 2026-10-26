# Stage85 PASS → Stage86: identify actual complete Batch02 ten-site forcing before Ho1-2000 candidate overlay and DATM

Recorded 2026-10-26. Source of operator Stage85 verified success: `reports/stage85_Ho1_2000_MANUAL_KEEP_TOWER_T_humidity_candidate_20261025T235555Z_12086954` and its SHA manifest. Native Ho1 year-2000 original T remains unchanged 17,568/17,568; measured QC0 T preserved 17,294, 1,068 humidity-only remap, 32 original VPD kept, 274 non-QC0 T source HOLD, QBOT availability 17,294/17,294.

**Do not claim other nine sites have final forcing approval.** The currently documented Stage07 first-pass numerically selected five (BZS, CMW, Ha1, Ho2, Ho3) but failed five (EML 1327 humidity pairs, GLE 295, Ho1 937, ICh 169, ICt 2176). Subsequent science/ERA shadow Stages11–85 do NOT imply a ten-site source-validated selected forcing candidate exists, since the explicit Stage08 `COMPLETE_TEN_SELECTED_CANDIDATES_REVIEW_REQUIRED` and Stage09 Post-v5 must be checked on live HPC. Already approved Ho1 original QC0 temperature/humidity science decision is not subject to reopening.

**Next action**: use [Stage86](../scripts/stage86/86_batch02_ten_site_and_Stage85_preDATM_inventory_readonly.py) to SHA-verify all four Stage85 operator outputs, inventory all Stage08 `raw_RH_sensitivity_*` candidate roots, their chosen 10 exact sites and candidate forcing CSV SHA, and all existing Stage09 Post-v5 status reports. This ONLY prints audit status. It does not pick the 'latest' trial automatically, change any saved forcing, submit a job or claim an all-site scientific pass. As Stage08/09 currently cannot automatically incorporate the new Stage85 Ho1-2000 humidity-only decision, an actual integration/overlay step is still required even if a complete ten-site selection exists.

## IRIDIS6 — pinned one-paste read-only command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage86/86_batch02_ten_site_and_Stage85_preDATM_inventory_readonly.py"
  COMMIT="a74667fe1757ec0123838657fea4a57219627664"
  EXPECTED="0d88ba00946a70288d88b484f650dc213a5b40a8"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage86/86_batch02_ten_site_and_Stage85_preDATM_inventory_readonly.py" \
    -o "$TMP"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT"
    test "$(git hash-object "$SCRIPT")" = "$EXPECTED"
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
)
```

Stage86 success line: `STAGE86 CHECK PASS | original Stage85 output SHA verified; actual saved ten-site artifacts inventoried, NO WRITES/JOBS`. This proves the inventory executed, not that ten stations passed.

**Next branch based on real output:** `STAGE86 TEN-SITE STAGE08 CANDIDATE SET VERIFIED: 0` → complete source-selected numerical ten-site dataset, without discarding new Ho1 Stage85; >0 → pin the EXACT chosen Stage08 selection path and integrate Ho1 Stage85 by original native 2000 timestamp in a *new* forcing copy, ensuring TA_F never edited, 1,068 humid-only edits and 32 VPD untouched, 274 QC≠0 provenance still separate. Revalidate ten selected yearly source coverage & independent Post-v5 numeric/extremes; generate technical-preview NOLEAP annual NetCDF and unactivated stream templates using Batch01 Stage81 as software reference. Actual CIME DATM/CDEPS, ZBOT, historical offset, stream placement and test run remain separate production gates.

Do not directly run old Stage10 `build-and-audit` and assume it includes Stage85; the historical Stage08 algorithm predated that manual decision. Do not treat Stage64 9,389 and Stage74 15,199 science-only shadow rows as final approved model forcing. No Batch02 NetCDF were produced by Stage85.

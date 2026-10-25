# Operator manual decision APPROVED: US-Ho1 2000 keep original tower TA_F; Stage85 humidity-only candidate

Date: Sunday 25 October 2026. Operator explicitly states **do not investigate tower air-temperature deviations further; retain native original tower temperature TA_F; execute next step directly**. This decision supersedes prior automatic ERA5 replacement considerations for measured QC0 air T **at US-Ho1 in 2000 only**. Do not extend to US-BZS, other years, unmeasured/non-QC0 tower temperatures, or other AmeriFlux sites without their own explicit review.

## Adopted science rule (now executable)

1. **Temperature**: Keep **every original source TA_F unchanged**, including all 17,294 native measured-source QC0; the 505 QC0 large Ho1-vs-ERA5 T-difference original events, and both Jan 24–25 Stage84 manual-reviewed continuous periods. For original 274 non-QC0 source TA_F, preserve source product values but maintain their separate source-QC science HOLD; they are not automatically approved as tower-measured.
2. **Humidity**: In all original measured-QC0 rows where native ERA-sourced VPD_F is already physical at tower TA_F, **retain original VPD_F unchanged** (including original Stage84 32 ERA self-inconsistent at TA_ERA, which are physically possible at original TA_F). Derive RH directly from the retained original VPD and eswater(TA_F).
3. In precisely **1,068 original source QC0 half-hours** where native VPD_F(=VPD_ERA) is too large for original tower T, but VPD_F is physically bounded by companion ERA T, transfer the original ERA fractional saturation deficit to tower T:

`D=VPD_ERA / eswater(TA_ERA)`; `VPD_new=eswater(TA_F_original)*D`; `RH_new=100*(1-D)`. This changes **only the humidity value**, not the tower T. It preserves original ERA **relative saturation deficit**, not the original ERA VPD amplitude or specific humidity. This is an explicitly authorized humidity-processing *candidate method*, not a measured tower RH record.

4. Optionally compute physically paired model near-surface specific humidity with an original-source pressure field, preferring `PA_F`, then `PA_ERA` (FLUXNET FULLSET pressure in kPa, multiplied by 10 for hPa): `e=eswater(TA_F)-VPD_new`; `QBOT=0.622 e/(p-(1-0.622)e)`. When pressure is missing, do not invent it; leave QBOT missing and count the affected rows. Original 274 non-QC0 source T values have no automatically approved new RH/VPD/QBOT from this decision.

5. Export a **new immutable-sourced Stage85 candidate** under Batch02 reports only: 17,568 full original native time-step rows, exact 1,068 humidity adjustments, exact 32 unchanged manual-review rows, and 274 separate non-QC0 T/QC HOLD; SHA-provenance and operator-decision manifest. Existing original source and current model forcing/Slurm remain untouched. The human decision is recorded; the historic Stage49–84 scientific reports/counts are never rewritten.

### Why not keep raw VPD with cold tower T?

Stage83 and Stage84 established source VPD_F_QC2=ERA downscaled, VPD_F exactly VPD_ERA **17,568/17,568** HH, and 1,068 native QC0 tower T pairs for which original source VPD exceeds the water-saturation limit. Simply preserving TA_F while keeping ALL ERA VPD would perpetuate physically impossible pairings; hence Stage85 changes only those 1,068 humidity values by preserving ERA fractional deficit at tower T. The other 32 Stage84 ERA self-inconsistent with TA_ERA already have VPD≤eswater(TA_F_original) and require no direct edit under the manual decision.

### Next operational step (operator executes on IRIDIS6)

Source script: [Stage85 manual keep-tower-T humidity-only builder](../scripts/stage85/85_apply_manual_Ho1_2000_keep_tower_T_repair_humidity_candidate.py).

Original Stage83 code SHA pin: `8e2bdf99a404ba27dcb8832f734028bb084a8660`; source Stage84 report `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage84_Ho1_2000_32_raw_ERA_VPD_vs_ERA_T_source_20261025T225213Z_82b02e9f`. Both sources are sha-gated. The Stage85 script reads original primary FLUXNET FULLSET and archives scientific decisions to NEW folder only. On its first application, it will source-verify original Stage83/Stage84 archive and generate the candidate; this is not a request for another scientific investigation.

Stage85 source commit `982e1e8919b5b9bb9ce3998f067c577bd74ad40d`, blob `e09676acaf05b21fa10eff3aace38cdd47880e41`.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage85/85_apply_manual_Ho1_2000_keep_tower_T_repair_humidity_candidate.py"
  COMMIT="982e1e8919b5b9bb9ce3998f067c577bd74ad40d"
  EXPECTED="e09676acaf05b21fa10eff3aace38cdd47880e41"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage85/85_apply_manual_Ho1_2000_keep_tower_T_repair_humidity_candidate.py" \
    -o "$TMP"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT" && test "$(git hash-object "$SCRIPT")" = "$EXPECTED" || {
      echo "Refuse to overwrite an unexpected Stage85 script" >&2; exit 1;
    }
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -B "$SCRIPT" --apply-manual-decision \
     USER_APPROVED_KEEP_ORIGINAL_HO1_TA_F_2000_20261025 \
     2>&1 | tee "$HOME/Batch02_Stage85_Ho1_2000_manual_keep_T.log"
)
```

Expected print on actual HPC execution: `STAGE85 MANUAL DECISION APPLIED | original tower T unchanged 17568/17568; QC0 approved 17294`; `STAGE85 HUMIDITY-ONLY SATURATION-FRACTION REMAP 1068 QC0 HH`; `STAGE85 ORIGINAL VPD RETAINED FOR 32 ERA-SELF JAN SOURCE CASES`; `REPORT <new folder>`.

**Explicit scope and limitation:** This Stage85 action creates humidity candidates and a decision manifest; it does not silently rewrite current NetCDF/CIME/DATM input or submit a model run because existing model input mapping and 274 unapproved source T quality codes are outside the manually approved scope. Those later integration actions must use the Stage85 candidate and preserve provenance; do not convert all historical HOLDs into approvals. The user-requested manual temperature decision has been implemented; the actual HPC run of the GitHub script is not possible from GitHub alone and has not been claimed as done.

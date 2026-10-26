# AmeriFlux Batch02: actual Stage107 PASS and Stage108 detached CIME one-step PREPARATION

Date 26 October 2026. Stage107 real IRIDIS6 `EXIT_CODE=0`, 28 contiguous 10–16-year source-window candidates using original Stage106 UTC-midpoint 2005–2020 meteorology, with no modifications. Original Stage107 report: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage107_GLE_real_source_contiguous_cycle_selection_READONLY_20261026T131102Z_c4ad22bd`.

Recommended separation:
- **Candidate future spinup cycle: 2009–2019 (11y)**: lowest maximum native-P99-normalized T/P/W seam ratio 1.9032; +0.0476 K mean T and +1.776% mean precipitation vs full16. 2008 spruce beetle peak is omitted from the repeating spinup meteorology, and actual disturbance/forest stand initialization must be treated separately. This is a technical candidate, not proof of scientific suitability.
- **Alternative candidate: 2009–2020 (12y)**: seam ratio 2.32467, +0.0572K mean T, +0.003% mean precipitation, but 4.807m/s wind boundary jump.
- **Full source 2005–2020** stays intact, used ONCE for historical evaluation and initially for one-step data-reader smoke test. Full16 cycle max P99 ratio 4.17742 and boundary +3.877K/−259Pa/+4.617m/s.

[Stage108 independent detached CIME preparation](../scripts/stage108/108_GLE_stage106_detached_one_step_CIME_setup.py) pinned commit `8043ee89900ae2bbccbcd350c1f7b776291a6cd7`, blob `3a1de7b8e7a0e12504d9fe81135a50d5244d5bfc`:
1. Verifies original Stage106 16 annual SHA-pinned **2004-LST ERA 14-record prehistory repaired** NC, Stage107 28-window CSV and SHA receipts, plus the original known successful Stage103 CIME implementation (blob `c67aa9c5c4e358b0c2efba99da46e08d8a8341c5`).
2. `--check` read-only: original 2005–2020 source, real GLE surface and GF-Guy model case, exact tower coordinates and residual PFT science holds.
3. `--prepare` makes a **unique new** GF-Guy `create_clone --keepexe` GLE case with GLE true Stage106 2005–2020 files (not the older Stage102 artificial 2020 surrogate). It calls `case.setup`, `preview_namelists` only. Configuration is **nsteps=1, RESUBMIT=0, NO CIME MODEL EXECUTION, NO CASE.SUBMIT**. New GLE stream is pinned to 16 Stage106 files, `QBOT Sa_shum`, `ZBOT Sa_z`, `tintalgo=linear`, `taxmode=cycle`. An **UNACTIVATED** future 2009–2019 stream proposal is separately written in the report, with no changes to the one-step case.
4. All original 215 ten-site NC, original Stage99/102/106 GLE NC, source GF-Guy case, previous Stage103 detached case, and original point surface unchanged. Stage108 retains `SCIENCE_HOLD_DO_NOT_SUBMIT_OR_RUN` until user explicitly decides to exercise a real one-step model forcing read (separate instruction/action).

Science HOLD after Stage108 even if parser passes: actual model CIME/DATM data-read not performed, yearly forcing periodic edge, observed GLE tower forest ENF (85% Engelmann spruce/15% subalpine fir) versus original gridded 7.5144% crop, known spruce-beetle mortality around 2008, distinct temperature/humidity ZBOT 23.4m versus wind measurement height 22.65m.

One paste on IRIDIS6:

```bash
(
 set +e
 REV="8043ee89900ae2bbccbcd350c1f7b776291a6cd7"
 BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$REV/examples/AmeriFlux_MultiSite_10_Batch02/scripts"
 WORK="$HOME/Batch02_stage108_GLE"
 mkdir -p "$WORK"
 curl -fLsS --retry 3 "$BASE/stage108/108_GLE_stage106_detached_one_step_CIME_setup.py" -o "$WORK/108_GLE_stage106_detached_one_step_CIME_setup.py" || exit 1
 curl -fLsS --retry 3 "$BASE/stage103/103_GLE_seam_CIME_detached_namelist_preflight.py" -o "$WORK/103_GLE_seam_CIME_detached_namelist_preflight.py" || exit 1
 test "$(git hash-object "$WORK/108_GLE_stage106_detached_one_step_CIME_setup.py")" = "3a1de7b8e7a0e12504d9fe81135a50d5244d5bfc" || exit 1
 test "$(git hash-object "$WORK/103_GLE_seam_CIME_detached_namelist_preflight.py")" = "c67aa9c5c4e358b0c2efba99da46e08d8a8341c5" || exit 1
 SRC="$WORK/108_GLE_stage106_detached_one_step_CIME_setup.py"
 python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf8").read());print("SYNTAX PASS")' "$SRC" || exit 1
 python3 -B "$SRC" --self-test || exit 1
 python3 -B "$SRC" --check || exit 1
 LOG="$HOME/Batch02_Stage108_GLE_CIME_one_step_prepared.log"
 python3 -B "$SRC" --prepare 2>&1 | tee "$LOG"
 RC=${PIPESTATUS[0]}
 echo "STAGE108_EXIT_CODE=$RC"
 grep -E '^STAGE108 (GLE VERIFIED|SMOKE|FUTURE|WEATHER|CIME|CASE|REPORT|SCIENCE HOLD)' "$LOG"
)
```

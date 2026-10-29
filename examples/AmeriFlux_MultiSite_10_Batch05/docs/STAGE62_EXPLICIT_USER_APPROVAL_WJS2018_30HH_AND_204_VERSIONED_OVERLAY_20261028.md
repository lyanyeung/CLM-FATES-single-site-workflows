# Batch05 Stage62 — explicit approval: US-Wjs 2018 30-HH source RH interpolation, versioned 204 candidates

## Actual operator-verifiable source state, 28 October 2026

Stage56 actual operator **PASS**: original 166 user-approved records + 8 new US-UMB/US-Wjs2021 user-approved native HH = **174**, no forcing changes.

Stage57 actual CDS reference **PASS**, Stage58 four-method comparison **PASS**, Stage59 49 original source HH and saturated QC0 9-HH plateau audit **PASS**, Stage60 original VPD provenance **PASS**, Stage61 protected exact 30-HH linear RH trial **PASS**.

Original Stage60 result:
`/home/ly3n24/ameriflux_batch05_stage60/wjs2018_exact_original_MDS_QC_20261028T234456Z_908965`.

Stage60 original US-Wjs 2018 30-HH facts:
- `VPD_F` and `VPD_F_MDS` identical at **30/30** half-hours; both QC **1** for the exact 30; original TA QC **0**.
- Original relative-humidity source field missing for **30/30**; derived RH negative in four original MDS half-hours.
- Original source QC0 RH anchors: 2018-03-11 19:00 = **100%** and 2018-03-12 10:30 = **92.127%**.
- Freshly downloaded ERA5-Land is **33.237/33.906 RH percentage points drier** than QC0 original source anchors; direct gridded RH replacement or anchor-bias clipping (28/30 HH clipped to 100%) are not accepted as genuine tower humidity.
- Stage61 reconstructed 30 HH with original TA_F unchanged and linearly interpolated RH at **15.5-hour** source-native anchor distance. Actual Stage61 results show maximum adjacent VPD jump **0.09194391 hPa**, zero >2 hPa jumps, RH 99.746045484% → 92.381364516% and VPD 0.0150758147 → 0.5934296586 hPa. These are **constructed estimates**, not measured interior humidity.

Stage61 research report:
`/home/ly3n24/ameriflux_batch05_stage61/wjs2018_30HH_protected_linear_RH_shadow_20261028T235434Z_968717`.

## Explicit investigator approval — 2026-10-28

After reviewing the Stage61 exact values and method limitations, the investigator replied **"同一"** to the assistant's request for explicit approval of the **30 US-Wjs 2018 half-hours into a new versioned overlay 174+30=204**. This is interpreted as agreement to the precise method and source-native window above. Approval is **limited to creating a versioned science-repair candidate overlay and retaining original-source QC/MDS provenance**.

**This is NOT approval to alter any AmeriFlux original source, replace previous 174 rows, write production DATM/CIME forcing, alter model cases, or submit Slurm simulations.** New overlay rows remain marked as interpolated, not direct tower-observed RH; 15.5h meteorological gap is a scientific limitation.

## Stage62 reproducible science-preserving merge

[Stage62 Python](../scripts/stage62/62_merge_explicitly_approved_Wjs2018_30HH_into_versioned_204.py) immutable commit `c7bc5b37a4b46a6216aeb43f107454176e3f90f3`, Git blob `c501e2c4bd41abd705d015fa555e4bde8211e3fa`.

[Stage62 IRIDIS6 launcher](../scripts/stage62/run_stage62_iridis6.sh) immutable commit `5ff639a112703ac918ebbe172e2f2ded5be99a8d`, Git blob `25d7466224d3212706d1a0146d417b6e4dc322f4`.

Stage62 verifies the exact original raw FLUXMET source SHA `9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6`; SHA-checks upstream Stage53/56/59/60/61 files/manifest counts; independently reproduces all 30 Stage61 RH/VPD numbers; enforces QC0 anchors and 30 source QC1 + original MDS QC1; preserves original TA; confirms four originally negative inferred RH; independently rechecks the 31 transitions and zero >2hPa jumps; preserves all earlier **174 row values**; denies duplicate/overlap and any nonapproved timestamps. Only after all checks does it create **a new output directory**.

Expected new artifacts:
- `stage62_VERSIONED_204_APPROVED_RH_VPD_native_overlay.csv` (204 rows, the same 20-column schema as Stage56, original 174 rows unchanged)
- `stage62_EXACT_30_NEW_USER_APPROVED_Wjs2018_RECONSTRUCTIONS.csv`
- `stage62_EXACT_30_ORIGINAL_MDS_QC_AND_ERA5L_PROVENANCE.csv` (original QC/MDS, processed-source ERA and gridded ERA5-Land RH reference)
- `stage62_Wjs2018_ALL31_NEWLY_APPROVED_BOUNDARIES.csv`
- `stage62_manifest.json` (input/output SHA256 and approval status)

IRIDIS6 single-line pinned command:
```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/5ff639a112703ac918ebbe172e2f2ded5be99a8d/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage62/run_stage62_iridis6.sh" -o "$HOME/run_stage62.sh" && test "$(git hash-object "$HOME/run_stage62.sh")" = "25d7466224d3212706d1a0146d417b6e4dc322f4" && bash "$HOME/run_stage62.sh"
```

Status: Stage62 code and immutable launcher SHA verified on GitHub, **actual IRIDIS6 syntax/self-test/source checks and 204-row output still require operator execution**. No Slurm submission or official forcing change is part of Stage62.

## Stage62 first operator attempt: compile-only numeric-identifier failure

Operator logged:
```
STAGE62 SOURCE VERIFIED
File ".../stage62.py", line 320
    2018_new_boundary_count=len(boundary),
        ^
SyntaxError: invalid decimal literal
```

Root cause is **two** invalid manifest `dict(...)` keyword identifiers that begin with a number. Both were fixed together: `Wjs_2018_new_boundary_count` and `Wjs_2018_new_abs_jump_gt2hPa`. GitHub source was re-fetched; no remaining direct numeric-leading keyword assignment was found in the script. The first attempt stopped at Python compilation, **before opening original reports or creating the Stage62 output**, therefore the original 174-row overlay and other source files were untouched.

Corrected Stage62 Python source: commit `fef79c2e8e2386550871ca9700686875f13dbe3e`, Git blob `cd6bf50688faaa6300b0386ebccded2a95b3a902`.

Corrected Stage62 launcher: commit `59ba0d5ae1fe89b7f0ba172498b9b76f822ada94`, Git blob `8e4998008362de1fb4e8ecfc169a9188bbad3af2`, retains compulsory `python3 -B -m py_compile` and `--self-test` before any data writes.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/59ba0d5ae1fe89b7f0ba172498b9b76f822ada94/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage62/run_stage62_iridis6.sh" -o "$HOME/run_stage62.sh" && test "$(git hash-object "$HOME/run_stage62.sh")" = "8e4998008362de1fb4e8ecfc169a9188bbad3af2" && bash "$HOME/run_stage62.sh"
```

Corrected immutable GitHub SHA/pins verified. The corrected version has **not yet been executed on IRIDIS6**, so a 204-row output is not claimed until operator PASS. Model forcing and Slurm remain unauthorised.


## CONFIRMED: actual Stage62 IRIDIS6 operator PASS, 2026-10-29 00:17 UTC

**This verified run supersedes the earlier pending/compile-failure status above.** The investigator re-ran corrected, SHA-pinned Stage62 on IRIDIS6 `login6003` and provided the actual terminal output:

```text
STAGE62 SOURCE VERIFIED
STAGE62 SELF-TEST PASS | explicit Wjs2018 30HH approval, strict 174+30 to 204, original/prod write forbidden
STAGE62 SUCCESS | ORIGINAL_174_VERIFIED_UNCHANGED + WJS_2018_30_EXPLICIT_USER_APPROVED = VERSIONED_204
STAGE62 NEW_30 FIRST 201803111930 LAST 201803121000 SOURCE_VPD_QC1_MDS_QC1=30 ORIGINAL_NEGATIVE_RH=4
STAGE62 APPROVED_2018_BOUNDS 31 MAX_ADJACENT_ABS_VPD_JUMP 0.09194391 GT2=0
STAGE62 COUNTS OLD=174 NEW=30 TOTAL=204 SOURCE_ORIGINAL_UNCHANGED=True
STAGE62 USER_APPROVED_CANDIDATE_ONLY; DATM_NOT_AUTHORIZED; NO_SLURM_JOBS
STAGE62 NO SOURCE/PRIOR_174/DATM/CIME/SLURM MODIFICATIONS
```

Full actual operator report directory:
`/home/ly3n24/ameriflux_batch05_stage62/wjs2018_30HH_approved_versioned_204_20261029T001706Z_431668`
(resolves to `/iridisfs/home/ly3n24/...`).

**Verified versioned candidate output:**
`/iridisfs/home/ly3n24/ameriflux_batch05_stage62/wjs2018_30HH_approved_versioned_204_20261029T001706Z_431668/stage62_VERSIONED_204_APPROVED_RH_VPD_native_overlay.csv`

**Exact SHA256:**
`7d2b0b3c8018b9cc28c6d8a7ea2f28dd593204f96e2f279433b61d721689a5a7`.

Interpretation: **204 exact user-approved versioned RH/VPD candidate half-hours** (174 original, 30 new Wjs2018). Source RH during the 2018 30-HH gap is reconstructed by 15.5-hour QC0-endpoint interpolation, **not measured**. All prior approvals and original FLUXMET, historical QC fields, source MDS, existing Stage56 174 overlay, and unapproved P1/P2/P3 holds remain separate and unchanged. This operator run did **not** modify DATM forcing/CIME cases or schedule Slurm jobs. This is not a blanket science approval for other Batch05 events.

**Next suggested action:** an independent **read-only, exact-SHA inventory** of the new 204-row overlay versus all remaining source HOLD cohorts. Only after resolving relevant residual scientific holds and explicitly authorizing a forcing-specific operation should production DATM be modified.

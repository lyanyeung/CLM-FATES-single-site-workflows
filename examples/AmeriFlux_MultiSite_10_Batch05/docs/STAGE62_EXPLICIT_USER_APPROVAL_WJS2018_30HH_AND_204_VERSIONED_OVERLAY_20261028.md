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

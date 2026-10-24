# AmeriFlux Batch04 — Stage05 QCv5 candidate build VERIFIED (3 priority stations)

**Operator execution evidence date:** 2026-10-24. The operator provided the full IRIDIS6 Stage05 `--self-test`, default preview, and `--build-candidates` log. SHA-pinned outputs are on **IRIDIS6**, not uploaded to GitHub as data. Script and README exist in [Stage05](../scripts/stage05/05_build_batch04_qcv5_repair_candidates.py).

**Self-test**: `STAGE05 SELF-TEST PASS: max4 short-gap, no partial interpolation, ERA gates`.

**Preview and build yielded the same counts (zero runtime failures):**

| Site | Original FLUXMET HH rows | Variable-level candidate patch rows | HOLD rows | QCv5 short interpolation | New joint zero-temperature fix | ERA-RH/RH candidate rows | ERA-RH/VPD candidate rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-SP1 | 368,208 | 87 | 147 | 9 | 0 | 39 | 39 |
| US-Syv | 438,288 | 534 | 606 | 3 | 1 | 265 | 265 |
| US-Ton | 438,288 | 4,715 | 1 | 3 | 0 | 2,356 | 2,356 |
| **Total** | **1,244,784** | **5,336** | **754** | **15** | **1** | **2,660** | **2,660** |

Therefore there are **16** candidate TA/PA interpolation/joint-dropout variable entries and **5,320** ERA-reconstructed RH/VPD variable entries. **5,336 is the number of variable-level patch rows, not 5,336 unique half-hour timestamps.** Total of 2,660 candidate ERA humidity timestamps; exact unique union of interpolation and ERA target timestamps is not yet calculated independently.

**HOLD breakdown:**

- **US-SP1, 147:** `HOLD_SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID`.
- **US-Syv, 606:** `HOLD_SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID` 183; `HOLD_ERA_PAIR_HUMIDITY_INVALID` 419; `HOLD_ERA_RH_OUTSIDE_QCV5_USABLE_RANGE` 4.
- **US-Ton, 1:** `HOLD_SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID`.

This concentration in US-Syv is a real reason **not** to simply substitute all packaged ERA humidity. Both ERA component pair closure and native temperature suitability are required. Unresolved HOLD records need individual chronology/physics classification, including very cold periods, rather than automatic forcing replacement.

## Output provenance

Created directory:
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage05_candidates/candidate_20261024T103113Z/
```
Files should include:
- `candidate_patch.csv`: isolated sparse variable/time repairs, including original value, candidate, method, origin and science status.
- `unresolved_hold.csv`: source-native anomaly timestamps that could not pass interpolation or same-pair ERA source gates.
- `report.json`: original source and ERA CSV SHA256/size, candidates and report status, output patch SHA256.
- `README.txt`: incomplete/unapproved candidate warning.

**Only the stdout evidence of creation and successful report output is available in this conversation; the individual generated CSV/JSON bytes have not yet been independently read here.** An additional script should compare their counts and SHA256 on IRIDIS6, inspect extreme repair effects and new VPD jumps, then classify HOLD priority/causes before merging a new `processed_v5` copy.

## Rules upheld and pending

1. Historical QCv5 **max 4 native HH** local interpolation, no partial long-gap filling. User authorised obvious physical outlier interpolation.
2. ERA-humidity replacement candidates require physically consistent same-source `TA_ERA,VPD_ERA,PA_ERA`; preserve credible site temperature, reconstruct its `RH` and `VPD_F` consistently. User authorised RH reconstruction; this is **not automatic post-v5 acceptance**.
3. Packaged `*_ERA` are FLUXNET downscaled/calibrated ERA-derived data; this does **not** establish independent gridded ERA5-Land agreement. Do not reuse the known -243°C/-271°C ERA anomalies in candidate forcing.
4. Raw `RH` missing alone does not imply that the model's humidity is absent when usable `TA_F,VPD_F,PA_F` exist.
5. A small annual-mean change is not sufficient to approve new VPD discontinuities. Review both endpoints, native QC and retained temperature, especially when `RH<5%`, `RH>100%` and cold-water saturation conventions intersect.
6. **No original source ZIP/BIF/FLUXMET/ERA file was overwritten. No `processed_v5` materialisation, Post-v5 approval, DATM, CIME or CLM-FATES spin-up was recorded by this Stage05 run.**
7. Remaining **seven Batch04 stations** have not yet been through Stage03 scientific-extreme screening and Stage05 candidate generation.

**Operational status: `STAGE05_CANDIDATE_BUILD_VERIFIED_3_OF_10_SITES`, `POST_QCV5_HOLD_754`, `MODEL_NOT_AUTHORISED`.**

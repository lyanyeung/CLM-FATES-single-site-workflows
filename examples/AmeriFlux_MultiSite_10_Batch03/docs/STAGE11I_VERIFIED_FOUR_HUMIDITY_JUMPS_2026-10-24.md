# Batch03 — VERIFIED Stage11i full-site shadow comparison; four VPD jump science holds

**Date:** 2026-10-24. **Verified in operator-provided IRIDIS6 log:** Python syntax PASS, Stage11i independent self-test PASS, `--check` PASS and `--run` completed its numerical audit and emitted the report directory prefix (operator's message truncated the final path). No new forcing, CIME, DATM or Slurm changes.

[Stage11i source](../scripts/stage11/11i_three_site_shadow_impact_audit.py) independently compared the original SHA-sealed Stage07 processed-v5 forcing with the SHA-sealed [Stage11h shadow science trial](STAGE11H_VERIFIED_SHADOW_TRIAL_AND_STAGE11I_QA_2026-10-24.md). Both `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` markers must remain.

## Exactly verified scope

| Station | NO_LEAP half-hours | User selected ERA5-RH event IDs | Actually modified VPD | Maximum *ADDED* neighbour jump vs Stage07 (hPa) | Events added jump >2 hPa | Events added jump >5 hPa | Minimum full-site shadow RH (%) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-MOz | 315,360 | 0 | 0 | 0 | 0 | 0 | 2.206422 |
| US-Mpj | 315,360 | 4 | 2 | 2.286140 | 1 | 0 | 1.168592 |
| US-NC2 | 367,920 | 49 | 41 | 9.761132 | 3 | 2 | 1.439602 |
| **Total** | **998,640** | **53** | **43** | — | **4** | **2** | — |

The Stage11i `largest_ADDED_jump_hPa` is defined by comparing old vs shadow adjacent VPD differences at a target event. It is distinct from Stage11h's total adjacent jump.

All 6 user-selected Stage07 TA candidates and 3 selected Stage07 VPD candidates retained. No non-target forcing variable or timestamp changed beyond CSV-roundtrip tolerance.

## Four newly introduced VPD jump events requiring closer human source review

| Station | Exact SOURCE NATIVE time | Stage07 VPD (hPa) | Stage11h VPD (hPa) | Absolute selected-event change (hPa) | Maximum *added* neighbour jump (hPa) | Stage11h candidate RH (%) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| US-NC2 | 2025-03-23 12:30 | 20.621000 | 10.859868 | 9.761132 | **9.761132** | 47.793355 |
| US-NC2 | 2025-03-25 09:00 | 18.405000 | 9.331161 | 9.073839 | **8.227839** | 49.340146 |
| US-NC2 | 2025-03-18 19:00 | 11.198000 | 7.491284 | 3.706716 | **3.706716** | 33.210889 |
| US-Mpj | 2018-02-02 17:30 | 11.261000 | 8.974860 | 2.286140 | **2.286140** | 20.834339 |

These **four** all originate among the five previously held positive extremely-low RH cases (the remaining case US-Mpj 2018-02-02 19:00 has added adjacent jump 0.417373 hPa). **An introduced jump is a review trigger, not proof the ERA candidate is false.** If Stage07's low-RH values were erroneous, correcting an isolated high-VPD spike can improve true atmospheric plausibility while creating a mathematical discontinuity relative to *unrepaired neighbouring series*.

## Yearly mean impacts (within the Stage11h shadow trial only)

| Site-year | Actually modified half-hours | Shadow minus Stage07 annual mean VPD (hPa) | Annual mean RH change (percentage points) | Annual mean QBOT change (kg/kg) |
| --- | ---: | ---: | ---: | ---: |
| US-Mpj 2018 | 2 | −0.000244 | +0.002386 | +1.945065 × 10⁻⁷ |
| US-NC2 2025 | 41 | −0.001140 | +0.013852 | +7.027325 × 10⁻⁷ |

Small annual differences **cannot substitute** for an event-level source and local continuity assessment or independent tower humidity validation. They show only that 43 modified half-hours minimally influence annual averages.

## Stage11j: exact-time +/-3-hour four-event original-source context review

[Stage11j read-only source review script](../scripts/stage11/11j_four_jump_source_context_review.py) has been **committed but not yet executed on IRIDIS6**. It is strictly limited to the four observed >2 hPa *introduced* jump event IDs. It imports unchanged verified Stage11i and Stage11c modules by exact Git blob SHA and rechecks Stage07 and Stage11h evidence receipts/forcing/source SHA. It outputs:

- An itemized four-event source/ERA/Stage07/Stage11h comparison with source `TA_F` and `VPD_F` QC, original implied water-vapour pressure, companion site-downscaled ERA T/VPD/RH and both adjacent old-versus-shadow VPD jump magnitudes.
- **52 exact native half-hour source and shadow context rows**: 13 rows (centre ±3 hours) per event, including original, companion ERA and existing forcing candidate values.
- Separate immutable named `reports/stage11j_*` review CSV and SHA receipt only when `--run` is invoked, no meteorological writes; `--check` is strictly read-only.

Stage11j is a *source science context review*, not permission to auto-smooth, interpolate neighbouring unflagged values, clip humidity, change an already human-reviewed decision, or start model simulations. Any subsequent choice to keep/reject a hotspot remains subject to a new explicit human scientific decision, source/clock/height review and whole-site Post-v5 integration gates.

**Remaining overall Batch03 status:** 3/10 sites have research-level full-site numeric shadow candidate files; 0/10 sites formally Post-v5 approved; 7/10 still have 1,924 unresolved separate Stage08–10 source humidity blockers; no DATM or spinup authorization.

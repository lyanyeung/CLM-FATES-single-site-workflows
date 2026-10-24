# Stage11k v1 self-test passed; read-only audit STOPPED at an incorrect 18-row expectation — v2 reconciliation

**Date:** 2026-10-24. User-provided IRIDIS6 log: download, Python syntax and synthetic self-test passed, `--check` terminated at
`ValueError: Expected Stage11j review flag census 11 uncorrected + 3 Stage07 + 4 Stage11h`.
The `set -e` shell **did not execute `--run`**. No production meteorology, original FLUXMET, Stage07, Stage11h, Stage11j SHA reports, DATM, CIME or Slurm outputs were changed.

## Cause: the correct screen has 25 source context records, not 18

Using all 52 operator-shared Stage11j native 30-minute source-ERA context rows, recompute original water-phase RH at `TA_F, VPD_F` and select:
`original_RH<10%`, `ERA_RH>=20%`, `ERA_RH-original_RH>=20 percentage points`, `VPD_F_QC in {1,2}`.

**Exactly 25** rows satisfy these *review-only* criteria, in three mutually exclusive correction-provenance groups:

| Category | Count | Interpretation |
| --- | ---: | --- |
| Source original `VPD_F` unchanged in both Stage07 and Stage11h | **11** | Newly recognized, **NOT YET APPROVED** source-neighbour humidity review targets |
| Stage07 originally changed the source `VPD_F`, Stage11h did not further change it | **3** | Already handled by Stage07, do not count as new untreated rows |
| Stage11h changed Stage07 `VPD_USE`, regardless of whether Stage07 had itself altered original | **11** | **4** central reviewed hotspot samples **plus 7** other Stage11h-changed context samples |
| **Total passing review screen** | **25** | **No additional meteorological write permission** |

The v1 implementation erroneously asserted `11+3+4=18`, overlooking the **other 7 Stage11h-changed context rows**. This count is derived from the user's complete pasted Stage11j context rows, not from any new cluster run.

### Exactly seven previously changed neighbours excluded by v1

- US-Mpj **2018-02-02 19:00** (previously selected RH<1%, changed in Stage11h).
- US-NC2 **2025-03-23 09:30, 10:00, 10:30, 11:00, 11:30 and 12:00** (original source water vapour negative, previously repaired by Stage07 and then modified by Stage11h).

The source-neighbour **11 unchanged** native timestamps remain precisely those listed in
[Stage11j verified event-context report](STAGE11J_VERIFIED_FOUR_EVENT_CONTEXT_AND_UNREPAIRED_NEIGHBOURS_2026-10-24.md). The source-ERA discrepancy diagnostic identifies candidates for further review; it does not prove that ERA5 estimates are the true tower RH.

## Corrected script: new v2 file; immutable older v1 preserved

[**11k_v2_four_event_unrepaired_neighbour_RH_review.py**](../scripts/stage11/11k_v2_four_event_unrepaired_neighbour_RH_review.py) is committed as a **separate new script**; do not overwrite v1.

v2:
1. Keeps all original SHA-sealed Stage11j receipt and exact native clock checks, and full 52-row T/VPD/RH provenance consistency;
2. Enforces the three disjoint correction provenance classes **11 original untouched / 3 Stage07-only / 11 Stage11h-changed**, including exact known native IDs for the **seven additional Stage11h changes**, and ensures four central events belong to the latter;
3. Prints source screen counts before checking, and prints all mismatched rows rather than failing with an opaque count message;
4. Provides a new CSV for **7 already Stage11h-changed other context rows**, in addition to the original 11 new science holds, 3 Stage07-only repairs, 4 centres and the full 52-row context;
5. `--check` remains fully read-only; `--run` may write only a **new** `reports/stage11k_v2_reconciled_neighbour_RH_review_*` folder with SHA receipt. No forcing writes, no scientific approval.
6. Contains a regression self-test that covers both source-to-Stage07 and Stage07-to-Stage11h change directions.

**Status:** v2 code committed, but **not yet run on IRIDIS6**. The source data/sealed Stage07/Stage11h remain scientifically HELD. No automatic repair of the 11 unchanged neighbours is permitted. Post-v5 approvals=0, DATM-ready=0, spinup=0. The other seven Batch03 sites and their separate humidity blockers are unaffected.

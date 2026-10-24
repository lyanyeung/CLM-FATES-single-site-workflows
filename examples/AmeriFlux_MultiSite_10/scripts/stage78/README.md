# Stage78 — finalize **completed** 1,109-row native ERA5 candidate set and audit actual RH/T edges

## Actual Stage77 result (24 October 2026)

**User-supplied successful IRIDIS6 output:** all 45 native ERA5 downloads completed, `--check` passed **1,109/1,109**, and `--trial` generated and physically validated **all six complete forcing files** in:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage77_1109_RH_lt5_fixed_20261024T114333Z/`

- CA-Ca3 41 records (RH<1: 7 → 0)
- CA-Cbo 28 (RH<1: 2 → 0)
- CA-Man 121 (RH<1: 1 → 0; **baseline already incorporates the separate Stage74 18-row temperature/humidity operator trial**)
- CA-TP4 6 (RH<1: 0 → 0)
- US-Aud 874 (RH<1: 0 → 0; 65 reanalysis-substituted records still have 1–5% RH: these were **recomputed**, not skipped)
- US-Bar 39 (RH<1: 8 → 0)

The user **authorized replacing all original RH<5% events with native ERA5 temperature, 2m dewpoint and surface pressure, jointly updating five downstream MET fields**. These six standalone Stage77 trial files **already contain the replacements**. No extra downloads or reprocessing are required.

## Why a further automatic edge comparison is useful

Stage77 logged **179 records** with at least one large RH step (≥25 percentage points) **when the new value was compared to adjacent OLD original values**. This does **not** necessarily mean 179 *new* or scientifically worsened steps. If both adjacent half-hours were recomputed, the actual final candidate may have a much smaller difference. Even when only one is changed, the original RH may have had a larger discontinuity.

The Stage78 script **compares actual old-to-old versus new-to-new consecutive 30-minute edges across every complete forcing CSV**, including adjacent ERA replacements:

- Pin/check every original and trial forcing SHA and all six operator ledgers; no edit outside the 1,109 approved timestamps or the five coupled fields.
- Measure original vs trial absolute RH and T differences across affected 30-min edges.
- Classify `NEW_LARGE_RH_STEP`, `WORSENED_LARGE_RH_STEP`, `NEW_T_STEP_OVER10C`, `EXISTING_LARGE_RH_IMPROVED`, and other nonworsened events.
- Emit **only the new/worsened boundary cases** to the actionable targeted-human-review queue, rather than mistaking the Stage77 179 old-neighbor screens for 179 independent newly introduced errors.
- Prepare one SHA-pinned **10-site selected-candidate reference manifest**, pointing to the six already updated Stage77 files plus the four unchanged Stage75 candidates. **Pointers only**: no forcing files copied/overwritten and no model/CDS jobs.

## Usage

```bash
python3 -B 78_finalize_RH_lt5_candidate_and_boundary_audit.py --self-test
python3 -B 78_finalize_RH_lt5_candidate_and_boundary_audit.py --check
python3 -B 78_finalize_RH_lt5_candidate_and_boundary_audit.py --audit
```

Successful `--audit` creates only `reports/stage78_1109_operator_versioned_selected_boundary_*/` with:

1. `10_site_selected_candidate_manifest.csv` (new six + original four; immutable checksums)
2. `all_affected_RH_T_edges.csv` (fully recomputed adjacent-row comparison)
3. `new_or_worsened_boundary_edges_for_review.csv` (remaining targeted scientific warnings)
4. `manifest.json` (summary, stage provenance and scientific caveats)

**Human approval already applies to the 1,109 same-source ERA5 recomputation decisions; it need not be repeated record by record.** Remaining review, if any, is **only targeted genuinely worse boundary edges**, plus **independent LST↔UTC/interval-centering provenance** before model/production input use. The earlier Stage74 and Stage76 decisions must not re-override the user's final all-<5% instruction.

**No production release is implied by a PASS**. Existing active CIME/DATM cases and running Slurm jobs remain unchanged. Preserve original and trial versions and exact SHA receipts.

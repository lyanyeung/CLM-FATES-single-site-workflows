# Stage21: 13-site meteorological QC one-pass second pass (pre-BIF)

**Version:** 15 October 2026. **Scientific status:** new candidate trial / report only, NOT an approval for BIF, ZBOT, DATM or CLM-FATES production spin-up.

## Exactly what this does

One execution reads the Stage20 selected manifest and full-site numeric-QC reports, the Stage18 465-event / 82-block ERA5–ERA5-Land review, and the pinned original tower files. It rechecks the Stage20 parents' SHA256 and verifies that Stage20 had zero numeric hard failures. **No re-download.**

The script attempts two conservative additional repairs:

- **DE-Gri, FI-Let:** For the remaining 74 MDS review blocks, reconsider contiguous *original TA/VPD QC=1* subsets that independently passed the Stage18 two-model T+RH and nearby measured-QC0 screens. Never re-edit Stage20 rows. Stage18's ERA5 temperature plus humidity proposal is considered, with ERA5-Land as a corroboration. All left/right and interior jumps must meet explicit, strict temperature and VPD limits and the worst temperature boundary must improve by ≥0.5°C. Unsupported or disagreeing subsets remain unchanged.
- **Other 11 stations:** Detect only an *isolated* single half-hour sharp T peak/trough in *non-QC0 TA and VPD*. Only interpolate between two original QC0 observations if both VPD and T are supported by valid original-network ERA5/ERAI reference data and the thermodynamics remain physical. **Do not modify tower QC0.** The inherited 13-site IT-Col companion is ERA-Interim, not ERA5. Model/reference support is not independent ground truth.

The script recomputes TBOT and QBOT only for revised TA/VPD rows, retains PSRF unchanged, and proves all other columns and all unedited values are preserved. It regenerates all 13-site numeric QC tests using **the same Stage20 audit** to avoid a changed definition of pass/fail. It hashes each latest candidate.

All rainfall over 18 mm/30min is retained and flagged. For each event the script records the source `P_F`, source QC, original-vs-forcing conversion, neighboring rainfall, 23:00 concentration, and whether rain exceeds 40 mm/30min. **It does not overwrite rain just because a high event is detected.** Source agreement alone cannot establish whether a timestamp contains daily accumulated rainfall.

## Upload once and run once

From WSL, assuming the downloaded Python script is in your Windows Downloads folder:

```bash
SCRIPT=$(find /mnt/c/Users -maxdepth 4 -type f -name '21_onepass_13site_meteorology_remaining_preBIF.py' -print -quit)
test -n "$SCRIPT" && scp "$SCRIPT" ly3n24@iridis6.soton.ac.uk:~/
```

On IRIDIS6 (one line; preflight is built into `run`):

```bash
conda activate clm_fates_env
set -o pipefail
python ~/21_onepass_13site_meteorology_remaining_preBIF.py --mode run 2>&1 | tee ~/FLUXNET_13_stage21_onepass.log
```

Optionally test without any writes first:

```bash
python ~/21_onepass_13site_meteorology_remaining_preBIF.py --mode check
```

Stage21 by default writes:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage21_trial_v1_20261015/
    reports/
        stage21_selected_13site_meteorology_manifest.csv
        01_exact_stage21_new_T_VPD_QBOT_change_ledger.csv
        02_full13_meteorology_numeric_and_extremes.csv
        03_decisions_all_new_MDS_and_isolated_spikes.csv
        04_remaining_all13_flagged_events.csv
        05_precipitation_provenance_summary.csv
        06_all_precip_gt18mm_source_timing_review.csv
        07_site_version_and_change_counts.csv
        08_82_MDS_blocks_updated_action_pending.csv
        09_preBIF_gate_status.json
        TECHNICAL_METHOD_AND_PENDING_SCIENCE_DECISIONS.md
```

Existing Stage20/18 data, original ICOS/FLUXNET/FLUXNET2015 packages, ERA data, and all historical candidate files are never overwritten. Existing output directory causes the script to stop rather than silently overwrite.

## How to get the high-level result

```bash
tail -35 ~/FLUXNET_13_stage21_onepass.log
```

Interpret `numeric hard failures = 0` only as numerical/temporal validity **within the implemented tests**. The scientific review still needs a decision on residual MDS blocks, source switch temperature jumps, and precipitation temporal meaning. It is reasonable to retain plausible extremes with an explained reason. Stage21 intentionally keeps `BIF gate = CLOSED_PENDING_SCIENTIFIC_MET_QC` even if all automated screens are green.

If an interrupted execution leaves a partly filled Stage21 output, do **not** delete parent sources. Check its errors; either inspect/remove that **new trial directory only** after confirming contents, or rerun with `--out /iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage21_trial_v2_20261015` (the same Stage20 parent, not an incremental third pass). Further independent repairs should be built using the Stage21 selected manifest as parent in a separately versioned follow-on script.

Never upload licensed raw meteorology CSVs, per-timestamp tower measurements, ERA JSONs, or candidate forcing time series to a public GitHub repository; publish scripts, aggregate statistics and methodological decisions where licensing allows.

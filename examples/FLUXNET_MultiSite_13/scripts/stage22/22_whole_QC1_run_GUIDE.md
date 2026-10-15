# Stage 22 — one-pass pre-BIF meteorology follow-up

## Why another candidate, rather than relaxing Stage21 thresholds?

Stage21 records 82 rejection decisions: 45 `NO_STAGE18_SUPPORTED_UNTOUCHED_QC1_SUBSEGMENTS`, 33 `BOUNDARY_OR_INTERNAL_CONTINUITY_HOLD`, 2 `QC0_OR_UNSUPPORTED_SOURCE_KEEP`, 2 `SEGMENT_LONGER_THAN_CONFIGURED_MAX`. These are algorithmic decision records, not proof that each record is defective or that all 82 represent independent unresolved source blocks. Stage20 generated 58 model candidate half-hour edits; Stage21 did not add any. The selected Stage21 parent manifest is preserved.

Stage21 cut source anomaly blocks into *only* the half-hours that met pointwise Stage18 support, creating artificial boundaries inside contiguous MDS gapfills. Stage22 therefore identifies the whole continuous ORIGINAL FLUXNET paired-QC1 TA/VPD envelope containing each unresolved Stage21 abnormal block, stopping at original QC0/QC2 and existing Stage20/Stage21 edits. This is a different boundary topology, not indiscriminate threshold relaxation.

## Execution

After uploading `22_onepass_full_QC1_envelopes_preBIF.py` to IRIDIS home:

```bash
conda activate clm_fates_env
set -o pipefail
python ~/22_onepass_full_QC1_envelopes_preBIF.py --mode run 2>&1 | tee ~/FLUXNET_13_stage22_onepass.log
tail -45 ~/FLUXNET_13_stage22_onepass.log
```

An optional read-only preflight is `python ~/22_onepass_full_QC1_envelopes_preBIF.py --mode check`. No downloaded reanalysis is re-fetched.

## Inputs

- Stage21 selected 13 site forcing manifest, the final 82-block queue and numeric QC;
- original 13-site input-source manifest (read-only primary FLUXNET CSV, flags QC0/QC1);
- original Stage17 downloaded and SHA256-verified 30 ERA5/ERA5-Land cache JSONs;
- Stage17b source verification metadata;
- Stage20 numerical and physical full-site audit function;
- previously generated Stage21 precipitation provenance report (reused, not overwritten).

## New-candidate eligibility (conservative)

1. Original TA and VPD *both* have QC=1 on a complete unbroken candidate interval, of 2–144 halfhours (up to 72 hours). Original measured QC=0 and existing trial rows are never edited. Source values must exactly match the candidate parent to within numerical tolerance.
2. Both models supply valid and mutually consistent T and RH for **every** halfhour (model difference at most 5°C T and 15 percentage points RH), with >=96 local QC0 observations in both temperature and humidity within 60-day windows. Local calibrated QC0 temperature MAE <=3°C and RH MAE <=15 pp in both reanalyses.
3. At least 2 MDS values AND >=40% of the gapfill interval differ by at least 8°C from **both** independently served reanalyses' locally QC0-adjusted reference temperatures, consistently in sign.
4. Build the candidate using ERA5 T2m + local QC0 temperature median offset, and ERA5 Td-derived RH + local QC0 RH median offset, then VPD and QBOT from the resulting T, RH and the unchanged original forcing PSRF. ERA5-Land is a related model check, **not** an independent tower observation. Never use its invalid pressure.
5. Entire interval must be finite and physical, internal temperature change <=5°C/30min, internal VPD <=8 hPa/30min, and both external boundaries <=4°C/30min and <=5 hPa/30min. If a parent boundary exceeded these, the new candidate must improve it materially. All rates are **conservative numerical trial rules**, not universal scientific definitions of extremes.
6. Validated candidates are created only in a new versioned stage22 directory. Original data and past Stage12/15/20/21 files are immutable, SHA256-pinned. The saved candidate is independently re-read and audited across the entire site.

## Outputs

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage22_fullMDS_trial_v1_20261015/reports`

- `stage22_selected_13site_meteorology_manifest.csv` — latest version and SHA256 for all 13 sites.
- `01_exact_stage22_repair_trial_ledger.csv` — timestamp-by-timestamp new TA/VPD/TBOT/QBOT trial changes.
- `02_full_QC1_envelope_decisions.csv` — accepted and rejected gapfill envelopes and reason codes.
- `03_unmatched_MDS_blocks.csv` — source abnormal blocks without a candidate original QC1 envelope.
- `04_13site_fresh_numeric_QC.csv` — fresh complete NO_LEAP/numeric consistency checks.
- `05_13site_still_flagged_extremes.csv` — all remaining flags, including rain and T jumps.
- `06_status_and_method.json` — provenance metadata and summary counts.
- `07_82_MDS_blocks_after_stage22.csv` — reconcile prior source anomaly blocks with inherited/current trial changes.
- `INHERITED_STAGE21_05_precipitation_provenance_summary.csv`, `INHERITED_STAGE21_06_all_precip_gt18mm_source_timing_review.csv` — source rain review, no edits.
- `TECHNICAL_METHOD_PREBIF_STAGE22.md` — generated narrative for subsequent GitHub science documentation.

## Unresolved scientific issues

Stage22 is a **provisional numerical QC trial** and does NOT open the BIF gate. No method can certify the historical truth of a suspect gap using two related reanalysis products alone. Remaining MDS blocks, source transitions, isolated QC0 spikes, possible accumulated/daily precipitation values placed at fixed 23:00, tropical downpours, cold-region ice/water saturation formula sensitivity, local-standard-time conventions and landcover/height cannot be certified by this script. If any candidates are held, review `02_full_QC1_envelope_decisions.csv`, `03_unmatched_MDS_blocks.csv`, `05_13site_still_flagged_extremes.csv`, and then decide targeted second-pass corrections. Never automatically redistribute rainfall solely based on its magnitude.

Publish executable scripts, methodology and aggregate decision summaries to GitHub if allowed, **not** original ICOS/FLUXNET tower records, raw weather caches or licensed derived series.
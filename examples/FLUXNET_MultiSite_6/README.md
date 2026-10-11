# FLUXNET six-site workflow: input preparation and quality-control record

**Stage:** 01–03 scripts developed and executed on Southampton IRIDIS6; surface extraction completed for all six sites. **Meteorological QC is provisional** (five sites still have review records). DATM NetCDF production, site PFT/measurement-height validation, and independent 500-year spin-ups are **not** part of this stage and have **not** been certified by this record.

**Record updated:** 2026-10-11. This is a reproducibility / decision log, not a statement that all site forcing has passed scientific quality assurance.

## Sites and annual forcing windows

| Site | Network package | Latitude | Longitude | Forcing years for a `NO_LEAP` spin-up | Half-hour records after removing 29 Feb |
|---|---|---:|---:|---|---:|
| DE-Hai | ICOS FLUXNET | 51.079213 | 10.452168 | 2000–2025 | 455,520 |
| RU-Fyo | EUF FLUXNET | 56.4615278 | 32.9220833 | 1998–2025 | 490,560 |
| DE-Tha | ICOS FLUXNET | 50.962597 | 13.565333 | 1996–2025 | 525,600 |
| DK-Sor | ICOS FLUXNET | 55.4858694 | 11.6446444 | 1996–2024 | 508,080 |
| NL-Loo | ICOS FLUXNET | 52.16644722 | 5.74355 | 1997–2025 | 508,080 |
| IL-Yat | EUF FLUXNET | 31.345044585655 | 35.0519885122776 | 2000–2024 | 438,000 |

The DE-Tha and NL-Loo releases have timestamps through the end of 2026 but their final 6,288 half-hours are missing across the meteorological variables in the October 2026 audit. **Exclude 2026 from the cycling window** rather than using future-year gap fills. Row completeness is not equivalent to observed-data completeness: FLUXNET `_F` variables can already contain network gap fills.

## Layout and numbered stages

```text
examples/FLUXNET_MultiSite_6/
├── README.md
├── scripts/
│   ├── 01_extract_6_fluxnet_nested.py         # copied from IRIDIS home before committing
│   ├── 02_make_6_surfaces.sh                 # copied from IRIDIS home before committing
│   ├── 03_prepare_six_site_forcing_v5.py
│   ├── 04_audit_six_site_qc_v5.py
│   ├── 05_inspect_two_site_humidity.py
│   └── history/                            # earlier experimental QC versions v1–v4
└── .gitignore
```

### 01 — Raw package extraction

Unpack the six network downloads. Some outer ZIPs contain another ZIP, so extraction must recurse. The script is the **actual script used on IRIDIS**, copied from `~/extract_6_fluxnet_nested.py`. It checks that BIF metadata and half-hour FLUXMET files can be found after extraction. Source packages are not included in Git.

### 02 — Point surface generation

The actual six-site script, copied from `~/make_6_surfaces.sh`, reads BIF coordinates and runs CTSM `tools/site_and_regional/subset_data point` to construct site-specific surface datasets and user mods. All six sites printed `SURFACE COMPLETED` in the October 2026 execution. The `No dominant pft type is chosen` warning did **not** prevent generation, but land cover / PFT fractions have **not yet been validated** against station vegetation. Creation success does not establish ecological suitability. Static surface data do not depend on meteorological QC and do not need regenerating merely because forcing QA is updated.

### 03 — Meteorological forcing QC, experimental version 5

Use `03_prepare_six_site_forcing_v5.py` with FLUXNET `FLUXMET_HH` (`TA_F`, `VPD_F`, `PA_F`, `SW_IN_F`, `LW_IN_F`, `WS_F`, `P_F`) and the package's **`ERA5_HH` companion**. These are not independently downloaded ERA5-Land files. Retain reasonable consolidated `*_F` values, including network gap-filled data, and use `*_F_QC` to preserve reported data provenance. Apply targeted physical screens, very short interpolations when suitable, and ERA-based reconstruction when indicated. Retain replacement event and manual review logs. **A QC code of 0 does not guarantee a physical validity check will pass.**

Scripts contain site-specific IRIDIS absolute paths and were not made machine-independent. Review their settings and dependencies before reuse elsewhere. The experimental thresholds (including RH-based VPD reconstruction) are research decisions, not official FLUXNET QC rules. The resulting `processed_v5` values are **candidate forcing**, not yet approved for final spin-up.

Suggested IRIDIS execution from a clone (assuming the packages and CTSM input data already exist at configured paths):

```bash
python scripts/01_extract_6_fluxnet_nested.py
bash scripts/02_make_6_surfaces.sh
python scripts/03_prepare_six_site_forcing_v5.py --sites DE-Hai RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat
python scripts/04_audit_six_site_qc_v5.py
```

The original scripts were executed from IRIDIS home (`~/...`). Most stage-01/02 operations need **not** be repeated if inputs have already been generated.

## QC history: why versions v1–v5 exist

| Revision | Main issue / change | Interpretation |
|---|---|---|
| v1 | Physically inconsistent TA–VPD pairs could trigger joint TA and VPD substitution. | Overly aggressive for valid measured TA; NL-Loo had 3,748 site-variable modifications. |
| v2 | Prefer keeping TA and adjusting VPD; IL-Yat 10 ERA humidity pairs were diagnosed. | Improved preservation of measured TA but missed demonstrably bad zero-temperature stretches. |
| v3 | Detect warm-season `TA=0°C` artifacts and winter `TA≈0°C`, `VPD≈6.110 hPa` plateaus. | Incorrectly also replaced plausible winter TA at 311 NL-Loo half-hours. |
| v4 | Keep plausible winter TA; fix plateau VPD only, with explicit review tags. | NL-Loo TA modifications reduced to 15; 355 remaining very-low-RH cases identified. |
| v5 | Additional screening of near-zero actual vapour pressure with contrasting ERA humidity, preserving tower TA. | 367 NL-Loo and 14 IL-Yat candidate low-RH adjustments; all marked for scientific review. |

For cross-version comparisons, prefer site-variable modification events and unique half-hour timestamps over blindly comparing totals of different review categories. The archived versions document the development history, **not** alternative validated reference products.

## Six-site v5 audit snapshot (2026-10-11)

| Site | v5 status | Site-variable changes | Changed official `QC=0` records | Review rows | Remaining `RH<1%` | Remaining `TA≈0 & VPD≈6.110` |
|---|---|---:|---:|---:|---:|---:|
| DE-Hai | REVIEW | 23 | 0 | 24 | 0 | 0 |
| RU-Fyo | REVIEW | 21 | 13 | 127 | 0 | 0 |
| DE-Tha | REVIEW | 32 | 1 | 14 | 0 | 0 |
| DK-Sor | PASS | 4 | 0 | 0 | 0 | 0 |
| NL-Loo | REVIEW | 1,734 | 1,129 | 845 | 160 | 99 |
| IL-Yat | REVIEW | 991 | 4 | 154 | 69 | 0 |

**Total:** 2,925,840 half-hour records across six site-specific windows; 2,805 site-variable modification events. These counts come from the actual IRIDIS v5 output and `audit_six_site_qc_v5.py`. An event count is not a count of unique times or physical error events.

### Outstanding scientific review — MUST NOT silently discard

- **NL-Loo (highest priority):** 1,112 VPD and 13 TA changes affected official `QC=0` measurements (plus four LW changes). A further 160 times have computed RH below 1%, with 99 remaining `TA≈0 & VPD≈6.110` pairings; 89 of those had ERA RH at least 50% in the audit. Some 2022 warm-zero-temperature instances have been repaired using ERA. Confirm zero-plateau meaning and RH reconstruction against station metadata / original humidity observations; avoid automatically accepting all ERA substitutions.
- **RU-Fyo:** 127 `outside_review_range_kept_not_replaced` entries (likely radiation-focused, but exact variables/values require inspection); 13 modified official `QC=0` LW records. Determine whether these are real cold-region extremes or sensor/product errors.
- **IL-Yat:** 154 review rows (149 distinct half-hours); 69 very-low-RH residual records. Some 2011-04-18 ERA-sourced TA/VPD pairs yielded RH below zero; eight records were provisionally adjusted using an **assumed** 1% RH lower bound. The 2013-03-26 observed TA versus ERA-derived VPD mismatch is especially sensitive to humidity reconstruction. Desert/semi-arid extreme dryness should not be erased solely for differing from ERA.
- **DE-Tha:** 11 `outside_review_range_kept_not_replaced` entries and three reconstructed VPD review entries; one altered official `QC=0` LW value.
- **DE-Hai:** 23 reconstructed VPD review entries plus one retained out-of-review-range record.
- **DK-Sor:** automatic screening returned PASS, but site PFT and sensor height still require independent verification.

**Review policy:** ERA divergence alone does **not** prove tower measurements are wrong, particularly for heatwaves, drought, extreme precipitation, and radiation conditions. Where ambiguity remains, retain the item in `REVIEW`, record a justified choice, or conduct sensitivity tests; do not force an all-PASS label. `PASS` is an automated screen result, not complete scientific validation.

### Outputs not committed to Git

On IRIDIS, for each site under `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/`:

- `raw/` — original extracted flux/ERA files, never overwritten.
- `processed_v5/` — candidate forcing CSV.
- `qc_v5/` — replacement event logs, manual review files, summaries, and diagnostic tables.
- `subset_data/` — CTSM surface NetCDF and user modifications (at the **site root**, not inside `forcing/`).

The exact processed output file name should be read from the v5 script, not guessed. Do not add original FLUXNET packages, downloads, tokens, large CSVs, `.nc`, case `run/`, or archive files to this GitHub example. Network/source data redistribution conditions must be respected.

## Next scientific and modeling steps (not yet completed here)

1. Resolve or explicitly document high-impact QC review events (especially official QC=0 replacements and longwave outliers); archive versioned QC reports outside Git.
2. Verify the extracted surface PFT coverage against real site vegetation; obtain appropriate reference vegetation and soil information as needed.
3. Extract and verify per-site forcing/reference measurement height (`ZBOT`) from station metadata; distinguish measurement height from canopy height.
4. Build and validate annual CLM-FATES DATM NetCDFs with 17,520 records per `NO_LEAP` year and eight required variables: `TBOT`, `QBOT`, `PSRF`, `FSDS`, `FLDS`, `WIND`, `PRECTmms`, `ZBOT`.
5. Set up **independent** 500-year startup spin-ups using each site's *entire eligible forcing-year window* as `DATM taxmode=cycle`; separately configure a fixed atmospheric CO2 concentration associated with the site's first forcing year (verify concentrations and citation before using them).
6. Evaluate spin-up convergence using carbon pool trends and restarts; a successful job does not by itself demonstrate equilibrium or convergence.

## Related single-site examples

- [`../FLUXNET_GF-Guy/`](../FLUXNET_GF-Guy/) — GF-Guy surface/case/spin-up example.
- [`../ICOS_ES-LJu/`](../ICOS_ES-LJu/) — ES-LJu forcing QC and CLM-FATES workflow.

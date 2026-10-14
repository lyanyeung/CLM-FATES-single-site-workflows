# Eleven-site forcing QC: extension of eight-site v5 principles and manual-review ledger

**Study snapshot 2026-10-14 · Status: review-only.** This file is research provenance, **not** a grant of scientific approval. Distinguish an observed instrument datum (QC=0), gap-filled source (QC=1), ERA-derived product (QC=2), a programmatically rejected source value and a **new derived trial candidate**. A `_F` label does not necessarily mean a sensor reading; always read its `_F_QC` and origin field.

## Governing QC design principles

The earlier [eight-site v5 script](../../FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py) used: exceptionally broad hard-failure screens; station/event-specific interpretation; short-gap interpolation only with credible bracketing; `ERA` as a secondary non-independent source; preservation of original QC/variable values; per-timestep human-review ledgers; separation between structure, scientific validity and model input. The [record of eight-site decisions](../../FLUXNET_MultiSite_8/docs/QC_and_DATM_decisions.md) details FR-Hes revisions, IT-Lav longwave anomaly and other case-specific departures. This eleven-site effort **extends those guidelines but uses newly implemented Stage03–11 scripts**, not the identical eight-site `processed_v5` pipeline or final BIF/DATM writers.

## 0. Stage03 multisource baseline (`v07a`) and FI-Sod unit bug

Network combinations include FLX FULLSET_HH, ICOS/ICOSETC/EUF FLUXMET_HH, and separately downloaded network-provided `ERA5_HH`. A site-year-specific priority table is embedded in `scripts/stage03/01_merge_11_source_aware.py`; the algorithm never combines TA/VPD/PA from different products within one half-hour humidity calculation. Other meteorological variables are individually sourced. It records per-variable origin and official QC wherever available.

**FI-Sod:** In a prior FI-Sod bespoke merge calculation, PSRF was constructed with `PA_F*100`, while `PA_F` is supplied in kPa and PSRF must be in Pa. Correct is **`PA_F*1000`**. An original 49,331 flagged-event diagnostic was entirely cleared under the corrected conversion. This validates the unit diagnosis only; it does not prove every historical source observation is accurate. Stage03 baseline 2001–2025 selects FLX 2001–2014, companion ICOS ERA5 2015–2022, and newer ICOS sources 2023–2025 subject to available columns and quality. Do not embed the old faulty FI-Sod output in the repository.

Stage03 preflight reported valid fallback TA/VPD/PA triplets for BE-Bra **21**, IT-Noe **9**, AT-Neu **19**, CH-Aws **77**, CH-Fru **120** and other cases. These are provenance/screening events, not directly the 559 CH-Aws revisions or 12 PA edits; double counting is invalid. Other source fractions may include ERA-filled `_F_QC=2` records.

## 1. Pressure: 12 revised candidate half-hours, three different sites

Derived pressure errors affect *only* `PA_F`, not measured `TA_F` or `VPD_F` in the affected blocks. All 12 edited pressure cells came from `EUF_F` with original `PA_F_QC=2`. In Stage05 the corresponding companion `ERA5_HH` contained implausible cold/zero pressures, sometimes absurd temperatures, and could not simply replace the existing bad pressure. Stage06 checked a 48-hour local median for **detection only** (deviations >5 kPa, not a universal hard correction rule) and found complete normal boundary intervals. Stage07 validates original values, QC labels and exact boundary interpolation before writing a new trial under `pressure07a`.

| Site / UTC-free station-local time | Original PA (kPa) → candidate (kPa) | Local normal boundaries |
| --- | --- | --- |
| CH-Fru, 2011-12-16 22:30, 23:00, 23:30 | 44.123→88.24175; 0→88.23750; 44.114→88.23325 | 22:00 88.246; 00:00 88.229 |
| CH-Fru, 2016-10-10 01:30, 02:00, 02:30 | 45.315→90.61525; 0→90.60150; 45.287→90.58775 | 01:00 90.629; 03:00 90.574 |
| CH-Lae, 2004-12-04 06:30, 07:00, 07:30 | 54.727→93.834; 15.627→93.842; 54.743→93.850 | 06:00 93.826; 08:00 93.858 |
| CZ-Stn, 2011-12-16 22:30, 23:00, 23:30 | 53.329→92.69525; 13.990→92.72150; 53.382→92.74775 | 22:00 92.669; 00:00 92.774 |

**Important:** CH-Lae and CZ-Stn had additional pressure corruption above the original Stage03 `PA>=50 kPa` cutoff; they were identified only by local continuity checks and included in the expanded 12-record trial. They do **not** meet the definition of official sensor edits: this changes an ERA-derived candidate, not the original licensed CSV.

## 2. CH-Lae radiation: 2 derived longwave replacements

`2004-12-04 06:00` and `06:30`: original `_F` and `_ERA` both have **`LW_IN_F=42.34 W m^-2`**, official `LW_IN_F_QC=2`. Stage03 physical-range screen rejected both. Neighboring acceptable values were **271.581 W m^-2 at 05:30** and **277.980 W m^-2 at 07:00**. Stage08 writes a separate `pressurelw08a` candidate containing:

| Local time | Old rejected value | New trial interpolated value |
| --- | ---: | ---: |
| 2004-12-04 06:00 | 42.34 W m^-2 | **273.714 W m^-2** |
| 2004-12-04 06:30 | 42.34 W m^-2 | **275.847 W m^-2** |

Both are flagged in a review-only event ledger; the Stage07 three pressure edits are retained. The `pressure07a` status *remains* `BLOCKED_MISSING` because it is a **historical parent**, not the final selected CH-Lae trial. `pressurelw08a/status.json`: 367,920 half-hours and `numeric_invalid_after_trial=0`.

## 3. CH-Aws: exceptional winter VPD/RH reconstruction (559 records)

**Why this was not a generic RH floor or normal ERA replacement:** CH-Aws temperature, VPD and pressure in FLUXMET and companion `ERA5_HH` are *identical* at all **559** events and the official FLUXMET QC triplet is **2/2/2**, so copying `_ERA` would merely reproduce the same physically impossible RH. A liquid-water saturation-pressure diagnostic gave **43 episodes** with negative RH from about −0.011% to **−66.389%**. The longest was 36 contiguous half-hours (18 h). This is not a rounding artifact. No on-site winter QC=0/1 RH was available for model cross-validation during 2006–2013.

1. **Stage09 fetch:** separately served Open-Meteo archive API, `models=era5` and `models=era5_land`, hourly `temperature_2m` and `dew_point_2m`, coordinates **46.583111° N, 9.790639° E**, 2006–2013. Raw cache consists of **16 year/model JSON files**, *excluded from Git*. Distinguish these reference paths from the original ICOS/EUF downscaled FLUXNET `VPD_ERA`; they are nevertheless related reanalyses and **not two independent observations**.
2. **Clock:** official local **standard time UTC+1, no DST** (CH-Aws product UTC start 2005-12-31 23:00 corresponds to local 2006-01-01 00:00). UTC+0 gives higher tower-temperature correlation (ERA5 0.8841 vs 0.8648 at UTC+1), but is a *sensitivity test*, not a basis to override official timestamps. Stage09 ultimately used UTC+1.
3. **Stage10 validation:** in QC=0 or 1 combined tower TA/VPD periods, ERA5-Land RH correlation **0.606** vs ERA5 **0.590**; all-season MAE **14.563 pp** vs **14.530 pp**; summer RH MAE **12.865 pp** vs **13.001 pp**. Difference is modest and does not validate winter. Both grid-elevation fields were 1982 m; site 1978 m in the queried reports. Grid elevation similarity does **not** ensure identical exposure or humidity.
4. **Stage11 construction:** for *only* the 559 bad original records, derive ERA5-Land model RH from its T2m/Td2m (water-formula saturation pressure), linearly interpolate reference hourly RH to site half-hours, convert to `VPD_new = es(T_site) * (1 - RH_land/100)`, then `QBOT_new = 0.622 ea/(PSRF - 0.378 ea)`, with `ea` in Pa, `PSRF=PA_F*1000 Pa`. **Keep original station TA/PA**; replace derived VPD trial value, record its prior `_F_QC=2` in dedicated columns and set QC on the derived VPD to missing (do not masquerade as a tower measurement). Stage11 reproduces independent VPD and QBOT calculations before writing.
5. **Uncertainty:** 526 events have |RH(ERA5)−RH(ERA5-Land)| <= **15 percentage points**, and **33 events** exceed it (maximum in one cited case ~19.3 pp). Stage10 confirms all 559 model estimates are in the 1–100% range and *all* 559 would meet a looser 20-pp difference screen; **15 pp is an arbitrary review-priority screen, not ground truth**. Consequently **all 559 are marked REVIEW**, with 33 elevated for sensitivity analysis. The corrected 559-event VPD ranged **0.23449–1.94287 hPa**, QBOT **0.000455–0.001072 kg kg^-1**. The generated `landrh11a` candidate had **332,880** half-hour time steps, `numeric_invalid_after_trial=0`, parent and output SHA256 and two separate event ledgers.

**Potential science caveats:** Water vs ice saturation pressure below freezing; hourly to 30-min interpolation; severe high-alpine winter exposure; station versus gridded elevation/exposure, orographic effects; temporal interpolation methodology; ERA5 and ERA5-Land dependent meteorological forcing. No winter tower truth. Directly approving these 559 revisions for a CLM-FATES production spin-up would overstate the evidence. Compare alternative winter RH reconstruction methods/sensitivity runs and independently audit final forcing first.

## 4. File version chain and historical mistakes

| Stage | Original → new candidate | Output changed | Verification |
| --- | --- | --- | --- |
| Stage03 | RAW inputs → `v07a` (all 11 sites) | Fresh provenance-rich source-priority meteorological candidate | Original source SHA checks, noleap time grid, per-variable QC; **not final v5** |
| Stage04 | No changes | Corrected historical PFT audit from incorrectly assuming 16 PFT elements to accepting 15 as documented | `STRUCTURE_OK_SCIENCE_REVIEW` on all eleven surfaces |
| Stage05–06 | No changes | Event investigation and boundary interpolation proposals | Actual source values, QC, time and local-median checks |
| Stage07 | `v07a` → `pressure07a` (CH-Fru, CH-Lae, CZ-Stn only) | 12 PA replacements | 6/3/3 records, trial status, checksum and event ledger |
| Stage08 | `pressure07a` → `pressurelw08a` (CH-Lae only) | 2 LW replacements + retains 3 PA changes | 367,920 records, `numeric_invalid_after_trial=0` |
| Stage09–10 | No forcing changes | Reference fetch and winter RH source comparison | Official UTC+1, grid/tower comparison, 526/33 uncertainty classes |
| Stage11 | `v07a` → `landrh11a` (CH-Aws only) | 559 derived VPD replacements, changed provenance columns | 332,880 records, `numeric_invalid_after_trial=0`; 33 flagged |

All status files explicitly say `NOT_APPROVED_FOR_DATM_OR_SPINUP`. The scientific acceptance steps described in the parent eight-site work have **not** all been carried out here.

## 5. Provenance and reproducibility references

Documented input parent SHA256 for CH-Aws `v07a`: `61374db9f1cbafcd22c0a4e74eb20d47d213faa59148cb597f284608ff89ccb3`.
CH-Aws `landrh11a` candidate SHA256: `130df2cd6c0bf9b89fc4895bca19145e1aca8bf0d4e5d7f48edb85df22035239`.
CH-Aws Stage09 reference-event CSV SHA256: `47839d9f6099c74f2e297f6811b67a6b310d715d8c925a4103a30c4d62731e6f`.
CH-Lae `pressure07a` parent SHA256: `876cfa0f78afe8ebca444faebd36d28226cd37d0c33ac1a96e1041b7e5e2ad4b`.
CH-Lae `pressurelw08a` candidate SHA256: `8277baf092b36f537ef48ee5f3dc2a0aabbb100efa515795d014ae6fd24a1426`.

These checksums identify the user's trial candidates as reported by IRIDIS logs; only local source metadata and logs can fully verify them. No licensed flux-tower records are included in this repository.

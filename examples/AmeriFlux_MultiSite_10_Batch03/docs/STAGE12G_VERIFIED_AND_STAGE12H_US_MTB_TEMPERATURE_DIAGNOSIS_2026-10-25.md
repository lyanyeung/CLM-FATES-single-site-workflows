# Batch03 Stage12g VERIFIED; Stage12h investigate US-MtB severe tower-versus-grid air-temperature conflicts

Stage12g **PASSED** IRIDIS6 syntax, --self-test, --check and --run. The three original external site-year ERA5-Land downloads (US-MtB 2024 / 2022 / 2020) were SHA-verified: together **1,038** source-native humidity records had new, year-specific gridded evidence. Yet numerical RH replacement at preserved EC tower TA_USE and PSRF passed for **only THREE** native records.

The Stage12g numerical scientific hold partition for the three new source years is exact:

| Result | Native source half-hour cases |
| --- | ---: |
| Original tower air T vs ERA5-Land T2m differs by >5°C | **1031** |
| Water/ice RH physical inconsistency | **4** |
| Safe, newly admitted RH-only research changes | **3** |
| **Source events covered by new verified grid** | **1038** |

The other **1,772** Stage12e missing-year native RH cases have no Stage12f new-year source yet. Six-site Stage12g forcing remains **NOT READY**, with **3,901** total rows missing at least one valid forcing variable (includes original Stage12b physics holds). The new Stage12g full NO_LEAP shadow and reports are isolated at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12g_six_site_new_year_gridRH_science_20261024T233640Z_b3d74fae/`

No original tower T, source site clock, source humidity, original Stage12b/12c/d/e, DATM, CIME, Slurm or spinup was modified or scientifically released.

## Scientific decision

**Do not download the other US-MtB missing source years automatically yet.** A 3/1,038 = 0.29% pass rate under validated physical rules shows an extremely poor return for collecting more yearly ERA5-Land in that station, and specifically an unresolved systematic disagreement between original `TA_F` and gridded `T2M`. This is evidence of a **temperature source/time representation issue to investigate**, not proof of a broken tower sensor or of an actual time-zone error. The earlier BIF UTC offset remains a hypothesis only. Do NOT widen 5°C threshold, replace source `TA_USE/TBOT` with gridded T, reassign the source native timestamp or remove the 233 source-original physics holds.

## Stage12h read-only diagnostic

[Stage12h: source temperature and 13 offset sensitivity hypotheses](../scripts/stage12/12h_us_mtb_temperature_source_offset_diagnosis_READONLY.py) is **committed but not yet run on IRIDIS6**.

The script reopens the three **already downloaded, SHA-sealed** full hourly T2m/D2m/SP NetCDF evidence sets, original SHA-pinned FLUXMET `TA_F` and source temperature QC, exact native companion `TA_ERA`, and the Stage12e/Stage12g preserved `TA_USE` time-axis. It checks all 3 entire NO_LEAP original site years, and separately the exact 1,038 Stage12g native humidity targets. The comparison includes source minus gridded and source minus paired-site-ERA T; monthly and QC-class statistics; and thirteen **exploratory** relative UTC shifts from −6 through +6 hours around the original BIF offset, scored by mean absolute temperature disagreement and fraction outside 5°C. Reanalysis may be warmer/colder for legitimate canopy, elevation, or microclimate reasons. An apparent best offset is **not** proof of clock error and must not automatically change forcing.

`--self-test` and `--check` only inspect/run in-memory source audits and print source means, medians, discrepancy and best hypothetical offsets; `--run` creates only new isolated SHA-sealed diagnostic report files, no forcing. On failure, stop for targeted investigation rather than rerun blind CDS downloads. No new RH candidate, new clock approval, Post-v5, DATM, CIME or spinup is authorised.

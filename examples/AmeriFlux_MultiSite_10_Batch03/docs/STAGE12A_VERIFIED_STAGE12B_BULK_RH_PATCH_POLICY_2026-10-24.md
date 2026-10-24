# Batch03 Stage12a VERIFIED / Stage12b automated six-site research humidity patches

**2026-10-24 IRIDIS6 Stage12a status:** Syntax PASS, self-test PASS, source SHA --check PASS, --run PASS. One new read-only site-wide status report (not forcing) was sealed at `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12a_batch03_post11q_ten_site_status_20261024T114422Z_73dd434c/`.

## Source-verified partition

| Site | Original humidity blocked | Evidence only / no physics conflict | Physical-temperature conflict | Clock metadata hold |
| --- | ---: | ---: | ---: | ---: |
| US-NR3 | 1484 | 1312 | 172 | 0 |
| US-Kon | 229 | 227 | 2 | 0 |
| US-NR1 | 173 | 116 | 57 | 0 |
| US-MMS | 18 | 17 | 1 | 0 |
| US-MtB | 15 | 14 | 1 | 0 |
| US-Me6 | 1 | 1 | 0 | 0 |
| US-Me2 | 4 | 0 | 0 | 4 |
| **Total** | **1924** | **1687** | **233** | **4** |

US-MOz and US-Mpj remain SHA-protected Stage11h research shadows; US-NC2 remains SHA-protected Stage11q with 64 previous plus nine new research-only ERA RH target times (73), 367,920 source-native half-hours and fixed EC tower TA/TBOT. **None of the ten has Post-v5/DATM/spinup scientific acceptance.**

## Next bulk step: Stage12b

[Stage12b program](../scripts/stage12/12b_bulk_six_site_ERA5Land_RH_patch_candidates.py) is **committed but not yet executed on IRIDIS6**. It SHA-reloads exact Stage11a/Stage10d/10h/10k source evidence, including validated Stage07 original source-manifest hashes, and 12a report. It computes *event-level research candidate patch records* for the 1,687 lower-conflict rows at six sites using Stage10b method B: transfer ERA5-Land gridded RH to **unchanged original source site TA and site pressure**, recompute VPD and QBOT, verify source-conserved hourly/interpolated ERA5-Land gridded RH and specific humidity mass closure. Results remain time-indexed by original source-native timestamp; the assumed original Stage10b UTC offset is only a hypothesis and is never adopted as a tower clock rewrite.

**Strict limitation:** Stage12b does NOT create seven new complete NO_LEAP forcing files; the first step is a bulk **per-event patch ledger** with explicit source rows and values for six sites, plus a review hold ledger. It reserves 233 originally detected conflict records, all four US-Me2 clock-source events, and any additional failures of strict physical/numeric criteria for further science handling. These are not silently repaired. If the 1,687 candidate records reveal any unexpected physics or source-field invalidity, the program explicitly moves those records to numeric HOLD, reports the count, and still keeps the original trial untouched. Outputs are isolated, SHA-receipted, `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP`, and **do not launch CLM-FATES**.

Next *after* Stage12b: use the verified site-native patch ledger to construct NEW complete site forcing successors, without replacing original source QC-v5 files, with full years, boundary QA, pressure/QBOT physics and no new temperature changes; keep 233+4 genuinely unresolved scientific conflicts separate. Never mark site ready solely from a numeric grid-RH reconstruction.

Six-site source VPD provenance is QC1 gapfill or QC2 ERA-downscaled, NOT a direct QC0 measured tower humidity. ERA5-Land is ERA5-driven; transferring RH is a research method, not observational ground truth. No release-specific native UTC offset has been approved for use by Stage12b.

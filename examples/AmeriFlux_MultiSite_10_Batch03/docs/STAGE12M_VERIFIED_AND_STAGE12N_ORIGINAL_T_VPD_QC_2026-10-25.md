# Batch03 Stage12m VERIFIED — local-source science review before acquiring further ERA5-Land years

**2026-10-25 08:43 UTC — IRIDIS6:** source SHA/provenance, Stage12m AST and `--self-test`, full `--check`, and `--run` all PASSED. The exact **86 originally held native RH events** were read-only analyzed from nine Stage12g site-years (US-Me6 2015/2017, US-NR1 2022). New isolated SHA-receipted REPORT-ONLY output:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12m_nonMtB_NRI_Me6_original_T_VPD_HOLD_diagnosis_20261025T084300Z_b0d38d29/`

The exact prior science disposition remains US-Me6 **14/78 accepted numeric-only research patches**, **29 tower-to-grid T >5°C HOLD** and **35 adjacent VPD jump >4hPa HOLD**. US-NR1 **0/22 accepted**, **19 T HOLD** and **3 VPD jump HOLD**. All 86 holds remain sealed, all original 233 Stage12b physics holds unmodified. Nine-source-year Stage12g trial remains `INCOMPLETE`, with 3,766 six-site time rows lacking some forcing field.

## Read-only source pressure, temperature and original neighbor evidence

| Site/year/hold type | N | Mean tower minus ERA5-Land T2m | Median absolute tower-grid T discrepancy | Median grid minus tower pressure | Hypsometric site minus grid height proxy |
|---|---:|---:|---:|---:|---:|
| US-Me6 2015, VPD jump | 20 | -1.43°C | 1.85°C | -764 Pa | -70 m |
| US-Me6 2015, T mismatch | 19 | **-10.81°C** | **11.16°C** | -757 Pa | -65 m |
| US-Me6 2017, VPD jump | 15 | -2.16°C | 2.12°C | -781 Pa | -74 m |
| US-Me6 2017, T mismatch | 10 | -1.17°C mean | 6.38°C | -701 Pa | -58 m |
| US-NR1 2022, VPD jump | 3 | -3.13°C | 3.10°C | +2,098 Pa | +236 m |
| US-NR1 2022, T mismatch | 19 | **-7.75°C** | **7.90°C** | +2,089 Pa | +237 m |

**Scientific interpretation, not source proof:** US-NR1's modest ~237 m site-grid pressure-derived relative height may explain a small part, but NOT the whole ~7.8°C mean mismatch (6.5 K/km lapse would suggest ~1.5 K). In US-Me6 2015's 19 T held events, the grid **pressure is lower** than tower pressure, implying a grid slightly *higher*, rather than ~1km lower as at Mt Bigelow: terrain mismatch alone is particularly weak as an explanation of tower being colder by ~10.8°C. These are event-subset medians/means, not whole-year station comparisons. A source QC, paired TA_ERA, station-era temperature provenance or clock/scientific data-quality check is needed before treating any T as erroneous.

**Stage12m VPD check:** all 38 originally labeled >4hPa candidate jump holds (US-Me6 35, US-NR1 3) still have at least one finite immediate neighbor in the final Stage12g shadow; all 38 hypothetical rejected candidates exceed the 4 hPa difference from at least one such surviving neighbor. This supports HOLD, not removal. It does not reconstruct masked intermediate candidate pairs or establish whether measured original QC0 neighbors or model-filled neighbors drive the jumps. These are not new measured tower VPD values.

## Stage12n — original TA_F_QC, VPD_F_QC, paired source TA_ERA (no writes)

The new [Stage12n raw-source-QC and paired TA_ERA forensic audit](../scripts/stage12/12n_NR1_Me6_original_T_VPD_QC_source_audit_READONLY.py) has been **committed on GitHub but not yet run on IRIDIS6**.

It first SHA-verifies the *exact* original Stage12m report receipt and all three signed original output files, and uses the SHA-pinned original Stage12m->Stage12g source validation chain. For each original 86 signed held native timestamps, it compares unchanged Stage12g `TA_USE/PSRF`, original raw `TA_F`, published `TA_F_QC`, original native `VPD_F` and `VPD_F_QC`, the original year/time-matched companion `TA_ERA`, and the signed Stage12m ERA5-Land gridded T2m. It also checks original source QC of the immediately preceding/following native half-hour and whether surviving Stage12g adjacent VPD was the original Stage12e source value or a separately newly gridded research value. This is a SOURCE QUALITY investigation only, **NOT** an attempt to authorize replacing measured/QC0 T, relax <=5°C or <=4hPa gates, backfit a clock offset, or run Post-v5/DATM/CLM/Slurm.

Stage12n `--check` is zero-write; `--run` creates only one new separately SHA-receipted diagnostic report. Analysis can distinguish observed QC0 support from filled/unknown source values, and suggest a scientifically justified next step, but cannot prove grid-versus-tower origin solely from paired ERA which may share meteorological source assumptions.

**Download decision:** do not automatically download further US-NR1 2001/2021/2018 annual grid years before checking the 0/22 site source failure; US-MtB remains paused due independently failed measured cold QC0 humidity validation. No change to 233 protected original science holds, Stage12g site times, temperature, pressure, QC0 measurements or previously valid repairs. No Post-v5/DATM/spinup release.

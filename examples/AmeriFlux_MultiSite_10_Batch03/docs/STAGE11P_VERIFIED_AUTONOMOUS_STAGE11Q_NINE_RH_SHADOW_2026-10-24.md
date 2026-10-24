# Batch03 Stage11p verified; Stage11q automatically gated research successor

2026-10-24 US-NC2. Stage11p syntax, self-test, --check and --run PASSED on IRIDIS6. The sealed source ERA5-Land hourly T2M/D2M/SP was read without another download. Exactly 288 validated UTC hours, 9 targeted source-native half-hours by 3 hypothetical UTC offsets = 27 target comparisons, and 40 source context samples x 3 = 120 source comparisons.

SHA-sealed Stage11p report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11p_us_nc2_era5land_nine_RH_three_offsets_20261024T110530Z_5f148814/`

## Results (RH percentage point MAE)

| Assumed tower native UTC offset | 9 target ERA5-Land vs companion ERA RH | 9 target ERA5-Land vs current Stage11l RH | All 40 source contexts ERA5-Land vs companion ERA RH |
| --- | ---: | ---: | ---: |
| -6 hours | 11.833181 | 35.449860 | 10.917786 |
| -5 hours (published source convention, NOT automatically approved) | 6.908326 | 36.041270 | 6.538853 |
| -4 hours | 3.921694 | 37.161619 | 4.507975 |

Across all three clock hypotheses and all nine points, gridded ERA5-Land RH is much closer to the *paired source-companion ERA5* humidity than the extremely dry Stage11l candidate RH. These are **ERA5-driven products, not independent tower measurements**. A lowest MAE for -4 hours is NOT authority to adopt -4 as the station's true timestamp convention or shift original native keys. Compare source temperature and humidity independently before final Post-v5 release.

### Research-science decision and status

The user requested autonomous selection and immediate progress rather than repeated signoffs where evidence is adequate. Based on source QC1/QC2, original source implausibly extreme low RH, already tested nine-record source/ERA humidity sensitivity, and supporting gridded ERA5-Land evidence at all three tested clock hypotheses, proceed with a **new isolated Stage11q automatically justified science candidate for these EXACT 9 native times**. This is NOT a claim of individually user-signed science approvals and is NOT a production forcing release.

| Native US-NC2 2025 timestamps | Number | Previous Stage07 VPD altered? |
| --- | ---: | --- |
| 2025-03-18 17:30, 18:00 | 2 | Neither |
| 2025-03-23 07:30, 08:00, 08:30, 15:30, 16:00 | 5 | 07:30 and 08:00 |
| 2025-03-25 10:30, 11:00 | 2 | 10:30 |
| **Total** | **9** | **3 previously Stage07 amended** |

The prior 62 human choices, 11 newly human-selected Stage11l choices, and all Stage07/11h/11l SHA-sealed artifacts remain immutable. The Stage11q output is a **new shadow only**. Cumulative ERA-RH research candidate mask would be **53 Stage11h + 11 Stage11l + 9 Stage11q = 73** distinct native target half-hours. This does not imply 73 separate new signatures.

### Stage11q implementation safeguards

[11q_auto9_us_nc2_humidity_only_successor.py](../scripts/stage11/11q_auto9_us_nc2_humidity_only_successor.py), committed to GitHub, **not yet executed on IRIDIS6**.

* Imports exact SHA-pinned Stage11o and Stage11p Python science audit modules and **re-runs the original SHA source and 27/120 ERA5-Land evidence checks**, comparing Stage11p stored 27-point reports with recomputed original NetCDF-derived RH.
* Requires each of the 9 candidate source times to be closer to source-companion ERA RH than to the Stage11l candidate RH for all 3 clock hypotheses by more than 1 RH percentage point. This **does not adopt any UTC offset**.
* Reconstructs VPD and QBOT at **preserved EC tower Stage11l TA_USE/TBOT**, with unchanged pressure and all other variables. Writes neither gridded ERA temperature nor ERA time shifts into forcing.
* Confines changes to exactly **9 native US-NC2 half-hours**, and compares all **13** half-hour transitions affected by those 9 targets, not merely 10 selected Stage11o examples. **Stops** if any altered transition has new VPD jump >4 hPa or added jump >2 hPa.
* Validates water vapor and QBOT physical mass closure at **all 367,920 US-NC2 half-hour rows**. On `--check` everything is in-memory and no files are written. On `--run` writes a fresh science-trial directory with one US-NC2 CSV, exact nine-event evidence, 13 touched boundaries, two other SHA references, an INCOMPLETE marker and a receipt.
* Three Stage07-modified source-native timestamps are superseded **only in this new isolated successor**; original Stage07/11h/11l remain protected.
* No Post-v5, DATM, CIME, spinup, new human approval or clock approval is granted.

The other seven AmeriFlux Batch03 stations retain their separate meteorological scientific approval process. Completion of Stage11q numerical validation DOES NOT authorize model jobs.

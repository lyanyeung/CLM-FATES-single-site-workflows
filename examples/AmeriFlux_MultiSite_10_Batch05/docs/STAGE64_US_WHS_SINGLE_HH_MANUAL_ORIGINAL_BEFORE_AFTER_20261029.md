# AmeriFlux Batch05 — Stage64 US-Whs original one-HH manual audit

Stage63 actually completed 29 October 2026 at 02:53 UTC: 1,565 original P2/P3 native half-hours remain over nine sites and 479 original events, in addition to 46 P1 HOLD and ten RH saturation platform records. **US-Whs has only ONE original P2/P3 flagged HH** and zero earlier 204-overlay repairs, zero P1 HOLD, zero RH saturation platform HOLD.

The user requested **single-event human review** rather than a large new batch repair for sites with only a handful of anomalies.

[Stage64 single-event Python](../scripts/stage64/64_US_Whs_one_anomaly_original_before_after_manual_review_READONLY.py), commit `30a0dc9ef01b32ac388a289af5b7a03cfdd0c25c`, Git blob `a1e818105c008648eec8062265cdc23285ff82a7`.

[Stage64 launcher](../scripts/stage64/run_stage64_Whs_oneHH_iridis6.sh), commit `ae71126c78f67a921d7f4d53545540061d824cf1`, Git blob `c4f4f1c98e52f6602cfec257d4a11d2e399ce08d`.

Read only original FLUXMET ZIP at `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Whs/forcing/packages/AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1.zip`, pinned to the existing Stage45 original archive SHA256 `0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767`.

The target native half-hour is **read** (not guessed) from Stage63's single US-Whs remaining native HH, then checked against the actual Stage27 historical original site time, tower TA/VPD and QC. Output is original source 3 hours before through 3 hours after (13 HH) with original RH and RH inferred from original T/VPD; selected original tower TA, VPD QC; MDS and product processed ERA companion fields; and P, SW, LW, WS and pressure. Prints each row and original immediate-neighbor VPD jumps. No external ERA5-Land is downloaded, and source processed ERA fields are not considered independent sensor data.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ae71126c78f67a921d7f4d53545540061d824cf1/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage64/run_stage64_Whs_oneHH_iridis6.sh" -o "$HOME/run_stage64_Whs.sh" && test "$(git hash-object "$HOME/run_stage64_Whs.sh")" = "c4f4f1c98e52f6602cfec257d4a11d2e399ce08d" && bash "$HOME/run_stage64_Whs.sh"
```

Run status: GitHub source/launcher pinned, IRIDIS6 operator execution not yet reported. Full source never edited; previous 204 versioned repair candidate overlay intact and not promoted to DATM forcing. A sensor hypothesis or replacement value, if any, requires explicit review of printed 13 HH before approval.

## Actual IRIDIS6 operator PASS and manual decision (2026-10-29 ~02:59 UTC)

Actual operator stdout:
```text
STAGE64 WHS SOURCE VERIFIED
STAGE64 SELF-TEST PASS | US-Whs exact one original source anomaly, native ±3h, read-only
STAGE64 SUCCESS | ONE US-Whs original P2P3 HH manual review, 13 original HH
STAGE64 EXACT TARGET 201205260600 EPISODE US-Whs_E0001 TIER P3_CONTEXT_AND_INDEPENDENT_REFERENCE TA_QC 1 VPD_QC 1
STAGE64 TARGET SOURCE RISK DUAL_CONFLICT_GT20PP ORIGINAL_T_MINUS_ERA_T_GT5C;MDS_ERA_RH_DISAGREES_GT10PP;MDS_ERA_RH_DISAGREES_GT20PP;ERA_RH_VS_ERA_E_VPD_DIFF_GT2HPA;ERA_RH_CANDIDATE_CHANGES_VPD_GT5HPA;ERA_RH_CANDIDATE_CHANGES_VPD_GT10HPA
STAGE64 DIRECT NEIGHBOR VPD hPa BEFORE 40.304 TARGET 41.132 AFTER 39.549 JUMPS 0.828 -1.583
STAGE64 NO SOURCE/204/DATM/SLURM WRITES; source ERA NOT independent measured RH
```

Actual result directory:
`/home/ly3n24/ameriflux_batch05_stage64_Whs/Whs_one_original_HH_manual_20261029T025926Z_1934005`.

**Manual evidence table (all original TA_F and VPD_F are QC1, not direct observations; original RH = missing):**

| Native HH | TA_F °C | VPD_F hPa | Implied RH % (filled) | Product ERA TA °C | Product ERA RH % |
| --- | ---: | ---: | ---: | ---: | ---: |
| 201205260430 | 24.159 | 27.954 | 7.188 | 18.144 | 36.138 |
| 201205260500 | 24.179 | 28.062 | 6.941 | 18.061 | 35.446 |
| 201205260530 | 29.332 | 40.304 | 1.340 | 18.096 | 34.677 |
| **201205260600** | **29.620** | **41.132** | **0.974** | **18.131** | **33.912** |
| 201205260630 | 29.100 | 39.549 | 1.880 | 18.138 | 33.028 |
| 201205260700 | 31.105 | 43.651 | 3.492 | 18.145 | 32.140 |
| 201205260730 | 32.333 | 46.833 | 3.433 | 18.905 | 32.030 |

At 05:00→05:30 original filled TA jumps +5.153 °C; source product ERA TA changes +0.035 °C. Original selected VPD jumps +12.242 hPa. The target source filled VPD is 41.132 hPa, with implied RH 0.974% (not negative, thus not a strict impossible-value proof). Both selected TA and VPD source QC are **1 for all 13 inspected half-hours**, and original RH missing for all 13. Source processed ERA target RH 33.911853% applied to original selected TA gives target VPD 27.450752 hPa, creating **-12.853 hPa and +12.098 hPa** adjacent jumps when the selected QC1 neighbors are left unmodified.

**Manual review outcome:** **HOLD / no new science approval**. The original Stage63 1 HH P2/P3 screen flags just the target, but the surrounding 13-HH reconstructed meteorology may be broadly biased. Do not use a single-site one-HH interpolation between QC1 neighbors, do not equate source ERA with measured RH, and do not change original files or the user-approved 204 overlay. To resolve later, seek reliable source QC0 meteorology bracketing the full uncertain interval, source instrument records and independent site-consistent evidence; do not assume a 3h bracket with all QC1 is adequate. No DATM/CIME/Slurm production authorization.

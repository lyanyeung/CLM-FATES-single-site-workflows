# Stage11n verified: seven humidity-only what-if records

IRIDIS6 output dated 2026-10-24 confirms Python syntax, synthetic self-test, full read-only check, and scientific sensitivity report all passed. Source and Stage07/11h/11l forcing remain unchanged. No additional human choices were signed, and Post-v5, DATM and spinup approvals remain zero.

Sealed Stage11n report: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11n_seven_unapproved_RH_source_what_if_20261024T102858Z_4925810e/`.

## Four original discontinuities improve in the hypothetical all-seven scenario

| US-NC2 2025 half-hour boundary | Stage11l jump (hPa) | Hypothetical seven-source ERA-RH jump (hPa) |
|---|---:|---:|
| 03-18 18:00–18:30 | 4.997141 | 2.443450 |
| 03-23 08:30–09:00 | 9.467392 | 0.851464 |
| 03-23 15:00–15:30 | 4.812737 | 0.130257 |
| 03-25 10:00–10:30 | 5.859252 | 1.226889 |

However two discontinuities MOVE to new intervals if the seven are all treated:

- 03-18 17:30–18:00: **0.796000 to 3.349691 hPa** (+2.553691).
- 03-25 10:30–11:00: **0.051500 to 4.683863 hPa** (+4.632363).

The five March 23 targets appear most cohesive in the checked source-native context: 07:30, 08:00, 08:30, 15:30 and 16:00. The other two (Mar18 18:00; Mar25 10:30) need both-edge review. Three of the seven were already modified by Stage07; no override is authorized.

## Stage11o: read-only edge sentinel sensitivity

[Stage11o shifted-boundary sentinel script](../scripts/stage11/11o_two_shifted_boundary_sentinal_RH_READONLY.py) **PASSED IRIDIS6 syntax, --self-test, --check and --run on 2026-10-24**, and produced an SHA-sealed read-only report at `reports/stage11o_two_shifted_RH_boundaries_READ_ONLY_20261024T103620Z_6abc437f/` under the Batch03 IRIDIS6 experiment. It adds precisely **two unapproved source-native edge sentinels**, US-NC2 202503181730 and 202503251100, to the original seven hypothetical candidates. It uses the existing SHA-sealed Stage11m 40-row context and Stage11l full native forcing, derives humidity from paired ERA RH at retained site TA, and compares eight in-memory scenarios over ten adjacent boundaries. It does not change tower temperature, original forcing, processing masks, or production approval.

The boundary source data indicate Mar18 17:30 original RH 17.161738% versus companion 24.698346%, and Mar25 11:00 original RH 10.786306% versus companion 26.855384%. These differences warrant further review but do not establish that ERA is ground truth.

Scientific status: the original 64 ERA-RH candidate targets and 9 original TA/VPD KEEP choices remain unchanged; the seven and two sentinel candidates are unapproved. No Stage11o forcing output is permitted.


## VERIFIED Stage11o nine-event what-if result

Eight read-only scenarios and ten selected native adjacent intervals were compared, with EC tower temperature held fixed. Baseline Stage11l max selected jump was 9.467392 hPa, with five jumps >4 hPa. The all-seven-plus-two what-if scenario reduced the maximum to **2.691868 hPa**, with **zero selected jumps above 4 hPa**, and zero newly added jump greater than 2 hPa across the ten inspected edges. Seven-only max was 4.683863 hPa, revealing the shifted Mar25 10:30–11:00 jump.

Nine *unapproved* source-native US-NC2 hypothetical timestamps are: 202503181730, 202503181800, 202503230730, 202503230800, 202503230830, 202503231530, 202503231600, 202503251030, 202503251100. Three were already amended by Stage07 (202503230730, 202503230800, 202503251030) and cannot be silently overwritten. Numeric boundary continuity within ten selected edges does not establish independently reliable tower humidity or full-year science acceptance. The 64 previously approved ERA-RH trial target times and all sealed Stage07/11h/11l forcing remain unchanged; no Post-v5/DATM/spinup permissions.

Separate from this particular Stage11o: the repository contains a different `11o_us_nc2_2025_march_era5land_evidence.py` ERA5-Land evidence-acquisition workflow. The successful sentinel log alone does not establish the status of that download or its scientific validation.

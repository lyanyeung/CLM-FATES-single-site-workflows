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

[Stage11o script](../scripts/stage11/11o_two_shifted_boundary_sentinal_RH_READONLY.py) is committed but has not run on IRIDIS6. It adds precisely **two unapproved source-native edge sentinels**, US-NC2 202503181730 and 202503251100, to the original seven hypothetical candidates. It uses the existing SHA-sealed Stage11m 40-row context and Stage11l full native forcing, derives humidity from paired ERA RH at retained site TA, and compares eight in-memory scenarios over ten adjacent boundaries. It does not change tower temperature, original forcing, processing masks, or production approval.

The boundary source data indicate Mar18 17:30 original RH 17.161738% versus companion 24.698346%, and Mar25 11:00 original RH 10.786306% versus companion 26.855384%. These differences warrant further review but do not establish that ERA is ground truth.

Scientific status: the original 64 ERA-RH candidate targets and 9 original TA/VPD KEEP choices remain unchanged; the seven and two sentinel candidates are unapproved. No Stage11o forcing output is permitted.

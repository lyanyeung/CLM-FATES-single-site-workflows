# Batch02 Stage55 operator PASS and remaining work

Date: 2026-10-24. Evidence: operator-pasted IRIDIS6 Stage55 terminal output; the underlying CSV files have not been independently uploaded to GitHub.

## Exact verified results

- GitHub pinned Stage55 file blob `fed667b3f26bd36e4be01252a30a353c9d12d049` matched the file downloaded on IRIDIS6.
- Stage55 syntax, self-test, source check and full audit: **PASS**.
- Reused existing immutable Stage19 report:
  `/home/ly3n24/AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f`.
- Stage55 report:
  `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage55_4884_existing_ERA5_science_triage_20261024T102824Z_8a2c5021`.
- Stage53: **444** user-selected independent CDS ERA5 RH-only candidate patches; no forcing applied.
- Stage54: **0** overlap between those 444 and the **4,884** Stage11 HOLD site-local-time targets.
- Stage55: **4,884/4,884** existing Stage19 independent ERA5 RH/VPD/QBOT sensitivity records matched and were numerically valid; **0** science-approved forcing changes.

## Exclusive primary science-review routes

| Stage55 exclusive primary route | Count |
| --- | ---: |
| HOLD_ORIGINAL_TEMPERATURE_QC | 3,245 |
| HOLD_WATER_ICE_SATURATION | 689 |
| HOLD_TOWER_ERA5_T_DELTA_OVER_8C | 33 |
| HOLD_HO1_PROVISIONAL_LOCAL_UTC_OFFSET | 917 |
| **Total** | **4,884** |

These categories are prioritized *exclusive routes*, not independent sets. Other flags on the same record overlap: **all 4,884 records carry cold-water-saturation caution and non-QC0 original VPD QC**, as shown by the five-site detailed counts.

| Site | Stage11 HOLD | Numeric invalid | Original T QC not 0 | Original VPD QC not 0 | Abs(Ttower - TERA5) >8 C | Water-vs-ice caution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| US-EML | 1327 | 0 | 709 | 1327 | 27 | 1327 |
| US-GLE | 295 | 0 | 192 | 295 | 6 | 295 |
| US-Ho1 | 917 | 0 | 701 | 917 | 370 | 917 |
| US-ICh | 169 | 0 | 169 | 169 | 0 | 169 |
| US-ICt | 2176 | 0 | 2175 | 2176 | 30 | 2176 |
| **Total** | **4884** | **0** | **3946** | **4884** | **433** | **4884** |

The report's exclusive **33** temperature-difference route is not the same as the **433** overlapping abs-difference flags: many of the latter are already classified by an earlier-priority QC or Ho1 route. Keep each independent flag and preserve decision hierarchy.

## What remains before model-ready forcing

1. Set explicit reproducible science-policy decisions for all 4,884 Stage11 HOLD targets, particularly original T-QC handling, water/ice vapour convention, and US-Ho1 local UTC offset / source provenance. Numerical validity alone does not approve a meteorological replacement.
2. Join proposed 444 Stage53 RH repairs plus all separately approved Stage11 decisions **without collisions** and audit against the wider Stage48 original-source 26,332 hard-physics union and other Stage07/08 QC cohorts. These are different populations, so do not infer that 5,328 rows exhaust the original quality issues or subtract counts without exact identity joins.
3. Build isolated, native-resolution ten-site, NO_LEAP climate forcing only after science gates, then independently verify variables, signs/units, time steps, missingness, hashes and DATM integration. Other Batch02 experiment/surface/PFT/spinup prerequisites are separate.

**Status: Stage55 scientific triage complete, but original data/forcing and spinup not changed.** No reliable clock-time ETA exists from this evidence; the remaining work depends on scientific decisions, not just computations.

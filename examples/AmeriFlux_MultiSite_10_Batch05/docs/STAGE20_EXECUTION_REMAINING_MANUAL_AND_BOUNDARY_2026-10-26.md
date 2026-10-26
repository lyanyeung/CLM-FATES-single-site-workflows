# AmeriFlux Batch05 Stage20 — actual execution and unresolved scientific checks

## Provenanced operator execution (2026-10-26 01:16 UTC)

```text
SOURCE VERIFIED
STAGE20 SELF-TEST PASS
STAGE20 SCIENCE DECISION COUNTS:
G01_WCr_Aug2025=26
G03_Vcm_Jan2007=34
G05_Vcm_Nov2024=26
G06_Vcm_Oct2025=31 (8 QC1 original RH-only extreme-low data included)
G02_Vcm_Dec2007_HOLD=19
G04_Vcm_Feb2008_HOLD=12
G07_Vcp_Jan2011_HOLD=3
STAGE20 SUMMARY proposed_candidate_HH=117 source_RH_unresolved_HH=34 forcing_written=0
NO ORIGINAL FLUXMET / EXISTING FORCING / ORIGINAL QC / MODEL / SLURM WRITES
STAGE20_REPORTS=/home/ly3n24/ameriflux_batch05_stage20/decision_candidates_20261026T011616Z_1483029
```

**Do not misinterpret counts.** Stage20 generated **117 candidates**, but only **85** intersect the original Stage18 P1 176-HH cohort; the other **32** are the 24 G03 original-RH transition HH and 8 G06 original-RH≈0.3% QC1/MDS HH. Separately, 34 P1 are HOLD, and **57 other P1 remain not covered**. Thus 85+34+57=176 original P1 HH.

## Original 57 unhandled P1 HH (confirmed from the uploaded complete Stage18 review file)

Every one is site `US-Vcm`. These consist of **44 original source QC0/QC0** low-RH HH (18 distinct source episodes) and **13 QC2/QC2** ERA-derived low or negative RH HH (6 episodes).

- 44 QC0/QC0 measured: 2014-08-19 (1), 2015-12-06 (10), 2017-11-08/09 (13), 2017-12-11 (4), 2018-01-03 (4), 2018-03-07 (1), 2018-12-10/11 (8), 2024-12-16 (3). Source RH is generally 0–1%. Require investigator's explicit decision whether the exact G05/G06 humidity replacement source policy also applies to all other years; tower temperature would remain original in candidate.
- 13 source QC2/QC2 ERA anomalies: 2008-01-16 (4, original RH 79.58–88.56% exists), 2008-12-27 (2, original RH missing), 2011-01-01 (1, original RH 82.0% exists), 2011-12-06 (2, original RH 84.11% exists), 2018-12-29 (2, original RH 89.51–91.46% exists), 2023-02-16 (2, original RH 85.0% exists). Thus **11 HH have original native RH**, **2 HH have missing RH**. The 11 may be considered for G03-style reconstruction once original RH provenance is verified; the other 2 remain HOLD.

### Candidate edge-jump check (reconstructed in analysis from original Stage19 7-group native source tables)

For the 117-humidity candidate scope, reconstruct `VPD_candidate=6.112*exp(17.67*T_F/(T_F+243.5))*(1-RH_candidate/100)`; compare the immediately adjoining original unmodified half hours. Three endpoints exceed **4 hPa / 30 min**, and require review before writing forcing:

| Boundary native tower timestamps | Original selected VPD at boundary start → end, hPa | Candidate selection VPD at start → end, hPa | Candidate 30-min jump |
|---|---|---|---|
| WCr 2025-08-25 12:30→13:00 | 11.473→17.599 | **11.473→6.3668163** | -5.106 hPa |
| WCr 2025-08-26 01:30→02:00 | 11.059→7.463 | **1.0812138→7.463** | +6.382 hPa |
| Vcm 2025-10-14 11:00→11:30 | 11.068→7.075 | **2.6354826→7.075** | +4.440 hPa |

These are checks to expand/validate a candidate interval, **not proofs that adjacent QC0 data must be overwritten**. In particular, WCr 12:00 original TA=15.067°C, VPD=0.000 hPa, source RH=100%; at 12:30 TA=15.219°C, VPD=11.473 hPa, source RH=33.685%; 13:00 source RH=0%; 26th 02:00 source RH=32.357%, 02:30 97.414%. Entire transition, not just 26 exact-zero HH, merits science review. For Vcm 2025-10-14 11:30 original QC0 TA=8.903°C, VPD=7.075 hPa, RH=37.985%, source-ERA RH diagnostic=75.806%; at 12:00 QC0 RH=99.461%, ERA RH=75.38%. Do not extrapolate replacement without a time-window judgment.

Original 39 P1 total: 176 HH. Remaining Stage17 483 non-P1 episodes (P2=89 and P3=394) also remain **scientifically unapproved**, although many may qualify for rule-based source QC/provenance validation rather than manual decisions. They contain remaining 1,574 low-RH source HH; exact record-level dispositions require future screening, not a blanket ERA overwrite.

## Next controlled implementation gates

1. Obtain investigator decisions whether G05/G06 processed-ERA-RH candidate policy applies to other 44 source QC0 low-RH events, and whether G03 original-RH reconstruction applies to 11 source QC2 events with original RH. Validate source processing, especially winter water/ice formula and potential observed RH sensor semantics.
2. Investigate three quantified boundary jumps and whether requested replacement should extend to neighboring source observations. Any extension must be explicit and provenance recorded.
3. For 34 known RH-missing holds + 2 other missing-original-RH events, seek a separate independent weather reference (actual ERA5-Land 2m temperature/dewpoint, verified UTC conversion and elevation/site coordinates) or other tower metadata; do not reuse source ERA formula-negative RH.
4. Carry out screening of all remaining 483 non-P1 Stage17 episodes for original source validity, independent reference, baseline physical constraints and quantitative transition impacts.
5. Only then create a versioned **new** forcing candidate overlay (not original overwrite), verify original source hashes, realistic temperature/RH/VPD, UTC/native clock, source provenance and full data audit; do not submit CLM-FATES yet. Run post-v5 and model after science and integrity gates pass.

**Status:** Stage20 candidate-only successful, forcing_written=0, source data unchanged, no Slurm model work started.

# Batch05 Stage21 — operator run verified; remaining 57 P1 and boundary decision gate

**Operator execution (2026-10-26 01:34 UK):**
```text
SOURCE VERIFIED
STAGE21 SELF-TEST PASS
STAGE21 SUCCESS original P1=176 prior P1 candidate=85 held=34 remaining=57
STAGE21_SUMMARY remaining_P1=57 A=44 B=11 C=2 boundaries=3 source/forcing/model/Slurm_WRITES=0
STAGE21_REPORTS=/home/ly3n24/ameriflux_batch05_stage21/manual_review_20261026T013442Z_1394929
```
No source, forcing or CIME modifications.

## Original 57 P1 source time records from Stage21 operator printout

- **A: 44 US-Vcm QC0/QC0 observed native extreme-low RH.** Original source RH 0.07–1.02%; processed-source ERA-derived RH **3.856304–61.041529%**. 34/44 native selected-tower-T vs processed ERA temperature differ by >=5 °C and 11/44 differ by >10 °C. Therefore the source ERA-derived RH is not independent tower RH evidence; pending investigator approval can be candidate only, not blind forcing application.
  - 2014: 1 HH, source ERA RH 61.04%.
  - **2015 Dec 6: 10 HH, source ERA RH 3.856–20.716%; 9 HH source ERA RH<10%**. In this 2015 period, tower T (~2–6 °C) diverges from ERA T (~-9 to -5 °C) by ~11–13 °C for much of the event, so **recommend isolate as separate HOLD/independent temperature and humidity reference validation** rather than presume ERA substitution resolves it.
  - 2017: 17 HH, ERA RH 18.12–39.35%.
  - 2018: 13 HH, ERA RH 10.70–35.13%.
  - 2024 Dec 16: 3 HH, ERA RH 21.49–24.15%.
  - No original files have been edited. A manual decision is needed whether G05/G06 processed-ERA-RH reconstruction is authorized for all/selected of 44 and whether to defer 2015.

- **B: 11 US-Vcm QC2/QC2 ERA-derived VPD with present native original RH**, suitable for investigator-directed reconstruction as in Stage20 G03. List by event:
  - 2008-01-16 21:00–22:30, 4 HH: original RH 79.58–88.56%; processed ERA RH -23.84 to -36.96%; trial original-RH-on-source-selected-T VPD approx 0.223–0.360 hPa vs original ERA VPD ~2.39–2.41.
  - 2011-01-01 07:30, 1 HH: original RH 82.00%; processed ERA RH -73.65%; trial VPD 0.242 hPa vs 2.339.
  - 2011-12-06 08:30–09:00, 2 HH: original RH 84.11%; processed ERA RH -16.39 to -14.04%; trial VPD ~0.330–0.339.
  - 2018-12-29 09:30–10:00, 2 HH: original RH 89.51–91.46%; source ERA RH -7.55 to +0.04%; trial VPD 0.193–0.260.
  - 2023-02-16 07:30–08:00, 2 HH: original RH ~85.00–85.30%; processed ERA RH -0.63 to -0.61%; trial VPD 0.356–0.361.
  - **Need decide whether to extend each fix across original-RH-supported adjacent transitions (as for G03), not blindly span gaps or absent RH.**

- **C: 2 US-Vcm QC2/QC2, 2008-12-27 21:00 and 21:30**, source RH -9999; source ERA derived RH -4.053836%, -4.081064%. **HOLD** until separate reference data, not ERA itself.

## Three boundary jumps with exact operator values
| Boundary | Original neighbor site/native time | Original TA / VPD / RH | processed ERA TA / VPD / derived RH | Stage20 candidate VPD | Remaining VPD jump |
|---|---|---|---|---|---|
| WCr start | 2025-08-25 12:30 QC0 | 15.219°C / 11.473hPa / 33.68535% | 14.942°C / 5.926hPa / 65.093868% | Untouched 11.473 | -5.106184 to 13:00 candidate |
| WCr end | 2025-08-26 02:00 QC0 | 8.409°C / 7.463hPa / 32.35776% | 7.762°C / 0.852hPa / 91.924097% | Untouched 7.463 | +6.381786 from 01:30 candidate |
| Vcm Oct 2025 end | 2025-10-14 11:30 QC0 | 8.903°C / 7.075hPa / 37.98483% | 9.919°C / 2.953hPa / 75.805596% | Untouched 7.075 | +4.439517 from 11:00 candidate |

Strong edge discontinuity supports **review** of these three original QC0 neighboring points; does **not** itself approve their replacement. User should explicitly decide yes/no for each boundary extension.

## Current exact science accounting

176 original P1 = 85 already candidate (in Stage20) + 34 held original RH missing + 57 Stage21 remaining. The Stage20 candidate total 117 includes 32 non-P1 transition or QC1-raw-source-RH records.

If investigator approves B=11 and some/all of A=44, candidate scope expands accordingly, and the 2 C remain HOLD. Final production forcing generation still must wait on the current 34+2 missing-source-RH holds plus science screening of the Stage17 P2/P3 episodes. Reference names from original `TA_ERA/VPD_ERA` are NOT proof of independently downloaded ERA5-Land.

**Immediate next step:** obtain operator decisions for A (including special 2015 hold), B and 3 boundaries; then generate a versioned *NEW* candidate overlay and preflight boundary/physics/provenance. No overwrite of tower original source or provenance QC0. Only after complete science screening and unresolved RH repair can a new forcing version be approved.

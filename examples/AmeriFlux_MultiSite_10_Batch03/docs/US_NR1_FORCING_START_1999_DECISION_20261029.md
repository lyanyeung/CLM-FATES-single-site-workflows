# US-NR1: forcing starts on 1999-01-01 (user decision, 2026-10-29)

**Decision.** The US-NR1 single-site forcing starts on **1999-01-01 00:00**. All of 1998 is removed from the research shadow and from every product built from it. The user approved this on 2026-10-29 ("NR1驱动就从1999年开始，但是要在github上说清楚").

## Why

**Evidence.** The evidence comes from the CL02 source-coverage audit. It reads the pinned Stage12g FLUXMET primary file and the AmeriFlux BASE file (`AMF_US-NR1_BASE_HH_26-5.csv`). Report: `reports/cl02_US-NR1_alternatives_decision_20261029T043321Z_89ce56f5/coverage_first_two_years_by_month.csv`.

Each cell is the fraction of half-hours in that month:

| Year-month | TA QC0 | TA QC2 (ERA) | VPD QC0 | VPD QC2 (ERA) | SW_IN QC0 | LW_IN QC2 | any BASE TA | any BASE RH |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1998-01 … 1998-10 | 0.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 | 0.00 | 0.00 |
| 1998-11 | 0.67 | 0.23 | 0.66 | 0.24 | 0.76 | 1.00 | 0.67 | 0.68 |
| 1998-12 | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 1999 (year) | 0.92 | 0.04 | 0.92 | 0.04 | 0.95 | 0.54 | 0.92 | 0.93 |

**What 1998 contains.**
- For January–October 1998, the FLUXMET record is the ERA downscaled reanalysis, and no tower measurement exists. The tower began measuring in November 1998.
- Keeping 1998 would put ten months of pure reanalysis into a "tower-forced" run.
- It would also need 43 humidity fills in 1998 whose temperature is itself reanalysis. They are all in the Jan–Mar 1998 cold spells: VPD_ERA is floored near 2.15 hPa at −13 to −18 °C, so the companion vapour pressure is negative.

**Why not start on 1998-11-01 or 1998-12-01?** A partial first year would break the whole-year NOLEAP cycling used for spin-up, so the forcing starts on 1 January 1999.

**Known caveat for 1999.** LW_IN is ERA-filled for January–June 1999 (QC2 = 1.00 for each month). This is common in FLUXNET and is accepted. TA, VPD and SW are measured for 74–100 % of each 1999 month.

## Consequences

**Research shadow.** The CL03 shadow for US-NR1 (`science_trials/cl03_US-NR1_research_shadow_*`) begins at `1999-01-01 00:00:00`. Its receipt records `forcing_start_year: 1999` and the number of 1998 rows removed. The 1998 gap rows appear in `CL03_final_decision_table.csv` as `DROPPED_BEFORE_FORCING_START_1999`; none of them is filled.

**Later DATM / Post-v5 / CIME / spin-up products.** Any such product for US-NR1 has to use 1999 as its first year. That covers the stream year range, the `DATM_YR_START`/`DATM_YR_ALIGN`-type settings, and the spin-up cycle length. None of this is done here: DATM/Post-v5/Slurm jobs need separate user approval.

**Original files.** The original FLUXMET, ERA and BASE files are not changed. 1998 remains available there for anyone who needs it.

**Approved edits.** Earlier approved US-NR1 edits are all after 1998 and are preserved bit-for-bit:
- Stage12AF 2022-09-10 TA;
- the six 2022 VPD/QBOT values;
- the five 2004-12 PSRF/FLDS values.

CL03 checks this.

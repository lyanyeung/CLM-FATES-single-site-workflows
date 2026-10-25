# AmeriFlux Batch05 — Stage14 actual operator results (2026-10-25)

## Provenance and execution outcome

The operator successfully downloaded and verified the pinned Stage14 Git blob, passed syntax and the Stage14 independent Magnus/Buck/Tetens self-test, then executed the complete *report-only* original Stage12 context audit:

```text
SOURCE VERIFIED
STAGE14 SELF-TEST PASS | Magnus/Buck/Tetens near-boundary water RH; NO WRITES
STAGE14 SUMMARY sites=10/10 priority=382 context=4966 bracketed=229 nonphysical_bracketed=11 measured=27 approved=0 reports=/iridisfs/home/ly3n24/ameriflux_batch05_stage14/science_20261025T194317Z_1261521
ONLY NEW DIAGNOSTIC CSV/JSON; NO ORIGINAL/STAGE10/STAGE12/FORCING/MODEL/SLURM WRITES
```

The operator shell also printed the same report path under `/home/ly3n24/ameriflux_batch05_stage14/science_20261025T194317Z_1261521`. The full event-level review CSVs remain on IRIDIS6, **not in this GitHub repository**. They are `stage14_all_240_bracketed_risk.csv`, `stage14_27_measured_saturation_formulas.csv` and `stage14_summary.json`.

## All 240 bracketed interpolation trials: absolute difference from original VPD

The logged four groups add to **240**, which includes 229 mathematical feasibility candidates and 11 candidates known to remain nonphysical:

| abs(candidate VPD − consolidated VPD), hPa | Cases | Share of 240 |
|---|---:|---:|
| ≤1 | 25 | 10.4% |
| >1 to ≤5 | 42 | 17.5% |
| >5 to ≤10 | 122 | 50.8% |
| >10 | 51 | 21.3% |
| **TOTAL** | **240** | **100%** |

**173/240 (72.1%)** change the original VPD by more than 5 hPa. This indicates a consequential proposed alteration, not an automatic improvement. These 240 include the eleven *mathematically nonphysical* interpolated outcomes and have **not** been approved. The printed top cases are mainly US-Var and US-Wjs, e.g.:

| Tower | Native original timestamp | Original VPD (hPa) | Unapproved interpolated VPD (hPa) | Delta (hPa) | Anchor gap |
|---|---|---:|---:|---:|---:|
| US-Var | 2019-08-19 06:00 | 21.747 | 0.1127143 | -21.6342857 | 3.5 h |
| US-Var | 2019-06-14 05:30 | 22.658 | 1.2155714 | -21.4424286 | 3.5 h |
| US-Var | 2020-07-22 05:30 | 22.680 | 1.7372000 | -20.9428000 | 2.5 h |
| US-Wjs | 2020-06-24 05:00 | 16.543 | 0.0000000 | -16.5430000 | 2.0 h |

The sources are unchanged printed local-standard tower timestamps, not UTC. The record-level Stage14 full report is needed for a detailed per-site >5 hPa distribution; do not infer such counts from the displayed global summary.

## All 27 independently screened near-zero original QC0/0 records

**Measured-source cases: US-Vcm 1 and US-WCr 26.** Stage14 tests **three hypothetical saturation vapour pressure formulas over water** and compares their implied RH to populated source `RH`:

| Screening formula | RH ≥0% for 27 source records |
|---|---:|
| Magnus 6.112 exp(17.67 T/(T+243.5)) | 0 |
| Buck water formula | 1 |
| Tetens water formula | 1 |

The **only** case becoming nonnegative under Buck and Tetens is US-Vcm on native `2025-10-13 17:00`: original `TA_F=11.686 °C`, `VPD_F=13.731 hPa`, original `RH=0.08066284%`; calculated RH is Magnus **−0.02211901%**, Buck **+0.03899464%**, Tetens **+0.04382791%**.

At **US-WCr**, all 26 native QC0/0 records from **2025-08-25 13:00 to 2025-08-26 01:30** remain slightly negative under all three water-formula sensitivity curves. Reported source RH is essentially 0%, sometimes approximately ±7e-6%. Buck-derived RH examples range roughly **−0.032 to −0.047%**, compared with more negative Magnus examples around **−0.084 to −0.108%**. Such small discrepancy may include formula choice, rounding and the native data-processing floor, but the logs do **not** establish the precise underlying source method or independent RH-sensor provenance. **Zero relative humidity for an extended interval is itself a major scientific provenance/QA question**; do not clear these 26 on formula agreement alone.

## Scientific interpretation and next step

Stage14 independently reproduced all 229 originally mathematically feasible bracketed candidates and found 11 nonphysical interpolation results; **no candidate has been scientifically adopted**. Forty-seven hundred or more original meteorological context records are available from Stage12, but the other **1,368** flagged low-RH half-hours not among the 382 priority group have not undergone targeted Stage12 review; they remain unresolved in the earlier Stage10 report.

The next analysis should cover **all 1,750** original low-RH events in one mutually exclusive source-provenance triage table (`VPD_F_QC=0` measured, `=1` good MDS, `=2` ERA), cross-reference the Stage14 candidate magnitude and borderline observed-RH findings, and explicitly leave all rows `HOLD_NOT_APPROVED`. Do not automatically change `TA_F`, `VPD_F`, humidity phase convention or original forcing, and do not create new Slurm jobs.

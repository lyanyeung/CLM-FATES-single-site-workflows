# Eight-site CLM-FATES 500-year spin-up: initial submission record

This document records the actual eight-site submission on IRIDIS6, following the
existing six-site workflow and using the verified 188 annual provisional DATM
NetCDFs. **SUBMITTED means the first batch job was successfully submitted; it
is not proof that 500 years have completed or that carbon pools converged.**

## Configuration

- Base CIME case: `GF-Guy_FATES_SURF2000_CO2405_1PT`, cloned with `--keepexe`.
- Model mode: `RUN_TYPE=startup`; `CONTINUE_RUN=FALSE` initially.
- Calendar: `NO_LEAP`; forcing: 48 half-hour records per day (`ATM_NCPL=48`).
- Forcing source: per-site `forcing/datm_v5_candidate_timevarying_zbot/` files.
- DATM time axis: each site's full historical record, repeated with `taxmode=cycle`.
- CO2: constant per site, chosen for the first forcing year (not tower measurements).
- Segment controls: `STOP_N=5`, `REST_N=5`, `RESUBMIT=99`; intended 100 x 5 = 500 model years.
- Eight independent cases: `<SITE>_FATES_SPINUP500`.

## Site-specific settings from the actual IRIDIS manifest

| Site | Forcing cycle | Constant CO2 (ppm) | Segments | Recorded status |
| --- | --- | ---: | ---: | --- |
| CZ-BK1 | 2004–2025 | 376.95 | 100 | SUBMITTED |
| IT-Ren | 1999–2025 | 367.80 | 100 | SUBMITTED |
| FR-Hes | 1997–2025 | 363.04 | 100 | SUBMITTED |
| FR-FBn | 2008–2024 | 385.02 | 100 | SUBMITTED |
| DE-Hzd | 2010–2025 | 388.75 | 100 | SUBMITTED |
| CH-Dav | 1997–2025 | 363.04 | 100 | SUBMITTED |
| BE-Vie | 1996–2025 | 361.93 | 100 | SUBMITTED |
| IT-Lav | 2003–2020 | 375.14 | 100 | SUBMITTED |

## Reproduction and verification

- `scripts/build_eight_spinup.py` generated the site-specific shell script from
  the proven six-site implementation. Keep both files as provenance.
- `scripts/09_eight_site_spinup500.sh` was executed on IRIDIS with modes
  `--preflight`, then `--prepare`, then `--submit`.
- **Do not rerun `--submit` against cases that have already been submitted.**
  First examine the existing cases, `CaseStatus`, and Slurm jobs.
- The read-only commands for monitoring progress are:

```bash
squeue -u ly3n24
tail -30 /iridisfs/scratch/ly3n24/CLM_FATES/cases/FR-Hes_FATES_SPINUP500/CaseStatus
```

## Scientific limitations

- Initial submission is not 500-year completion, spin-up equilibrium, or
  convergence of `TOTECOSYSC`, slow carbon pools or FATES cohorts.
- FR-Hes uses the documented manually revised DATM; original v5 is preserved.
- CZ-BK1 humidity review remains documented; no additional edits were made.
- DE-Hzd precipitation is retained as supplied, despite an unresolved
  high-annual-precipitation concern; this is a forcing uncertainty.
- Site representativeness of PFT fractions and ZBOT/WS measurement-height
  differences remain documented in `QC_and_DATM_decisions.md`.
- The source network's meteorology, model NetCDFs, case directories, run logs,
  archives and data products are **not** included in this repository.

## Source-code integrity

- Executed script SHA256: `8d9dd4d9d6144bf05961af7cb128a1c673b9f4650ab4dafefbaca23d224cd4ab`
- Generator SHA256: `24469a79e5460ab7fe5cff13e1280272c9ad03c8fe469d855ae9320de7aba239`
- Record prepared: 2026-10-12

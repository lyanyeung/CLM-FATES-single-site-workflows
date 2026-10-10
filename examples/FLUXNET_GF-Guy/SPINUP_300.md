# GF-Guy — Stage 2: 300-year CLM-FATES spin-up

This directory records the **working GF-Guy 300-year spin-up setup** on
Southampton IRIDIS6, **after** the Stage 1 surface / first-year case in
[`README.md`](README.md). The methodology and previous errors are documented
so the setup can be reproduced without rerunning ad hoc commands.

**Current evidence:** the first 5-year segment completed successfully
(`4074247`, 9m28s), archive succeeded (`4074248`), the
`2022-01-01-00000` restart files were written, and a second 5-year segment
was automatically submitted (`4074360` / `4074361`). This verifies initial
execution, first restart, archiving and resubmission — **NOT that all 300
model years have completed or converged**. Do not describe the full
300-year experiment as validated until the final output is checked.

## Exact experiment

| Item | GF-Guy setting |
| --- | --- |
| Source successful one-year case | `GF-Guy_FATES_SURF2000_CO2405_1PT` |
| Independent spin-up case | `GF-Guy_FATES_SPINUP300_CO2405` |
| Atmospheric CO₂ | `CLM_CO2_TYPE=constant`, `CCSM_CO2_PPMV=405.0` |
| Repeated DATM files | `GF-Guy_DATM_2017.nc` to `GF-Guy_DATM_2021.nc` |
| DATM mode | `taxmode=cycle`; `year_first=2017`, `year_last=2021`, `year_align=2017` |
| Calendar and coupling | `NO_LEAP`; `ATM_NCPL=48` |
| Segment / restart length | 5 model years; `STOP_N=5`, `REST_N=5` |
| Resubmit | `RESUBMIT=59` (initial + 59 = 60 segments) |
| Total intended integration | 300 model years (`2017-01-01` → `2317-01-01`) |
| Startup | `RUN_TYPE=startup`, first run `CONTINUE_RUN=FALSE` |
| Continuation | CIME switches to `CONTINUE_RUN=TRUE` after the first segment |
| Excess Ice | `use_excess_ice=.false.`, `use_excess_ice_streams=.false.` |
| History | Daily `hist_nhtfrq=-24`, `hist_mfilt=365` |
| Executable | `create_clone --keepexe` reuses already compiled source `EXEROOT/cesm.exe` |

Model years 2022–2026 use the **2017–2021 climate forcing again**. Later
model dates are bookkeeping dates, not observations or climate projections.
This is a fixed-405-ppm modern-forcing equilibrium experiment. Using a
2000-reference CTSM surface does not mean using 2000 CO₂.

## Scripts

```text
scripts/
  00_config.sh               # Stage 1, already committed
  10_spinup_config.sh        # Stage 2 parameters (separate from 2017-2025 Stage 1)
  prepare_datm_cycle.py      # Strict DATM list rewrite, all five files required
  10_submit_spinup300.sh     # Create/repair unsubmitted clone and submit
  11_monitor_spinup300.sh    # READ ONLY status/progress/history/restart summary
  12_verify_spinup300.sh     # READ ONLY XML/DATM/CO2/executable audit

tests/
  test_prepare_datm_cycle.py # Local synthetic tests; no IRIDIS access needed
```

## Running from IRIDIS6

The files should be present on IRIDIS alongside the existing Stage 1 scripts.
They are intentionally **not** designed to run from WSL, which does not have
IRIDIS files, CIME and Slurm.

```bash
conda activate clm_fates_env
cd /path/to/CLM-FATES-single-site-workflows/examples/FLUXNET_GF-Guy

# On a new setup ONLY. THIS SUBMITS REAL JOBS:
bash scripts/10_submit_spinup300.sh \
  2>&1 | tee GF-Guy_spinup300_setup.log

# Safe at any time during or after the existing run:
bash scripts/11_monitor_spinup300.sh
bash scripts/12_verify_spinup300.sh

# Refresh status every 30 seconds, without touching running jobs:
watch -n 30 'bash scripts/11_monitor_spinup300.sh'
```

**The existing GF-Guy 300-year case was already submitted.** There is no
reason to copy and execute the submit script on that case now. If run again,
`10_submit_spinup300.sh` detects `case.submit success` / `model execution
starting` in CaseStatus and performs a read-only exit without `case.setup`,
`xmlchange`, or `case.submit`. Never rerun the source Stage 1 first-year
case merely to prepare the Stage 2 scripts for GitHub.

### Where the results live

```text
/iridisfs/scratch/ly3n24/CLM_FATES/cases/GF-Guy_FATES_SPINUP300_CO2405
/scratch/ly3n24/CTSM_FATES_OUTPUTS/GF-Guy_FATES_SPINUP300_CO2405/run
/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/GF-Guy_FATES_SPINUP300_CO2405/lnd/hist
/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/GF-Guy_FATES_SPINUP300_CO2405/rest
```

History from this case uses `*.clm2.h0a.*.nc` (and `*.clm2.h0i.*.nc`),
not necessarily `*.clm2.h0.*.nc`.

## Why this version differs from earlier unsuccessful attempts

1. **Existing case:** checks CaseStatus before doing anything. An already
   submitted case is never reset or submitted a second time. An unsubmitted
   clone can be repaired. Old results in run/archive directories block a
   fresh startup to prevent overwrite.
2. **CIME job not recognized:** `case.setup` is required after cloning when
   `.case.run` / `case.st_archive` are absent. `case.setup --reset` is only
   used to repair an unsubmitted case previously set up. It is never run
   unconditionally against an active simulation.
3. **Archive script spelling:** the real filename is `case.st_archive`
   (no leading period), whereas the run batch script is `.case.run`.
4. **`BUILD_COMPLETE=FALSE`:** for an already compiled `--keepexe` clone,
   setup reset can clear the CIME build flag. This workflow sets the flag
   `TRUE` **only after confirming** that source and clone have the *same*
   EXEROOT and an executable `cesm.exe`. It does not fake completion for
   an uncompiled model or silently rebuild a different executable.
5. **DATM file range:** Stage 1 has 2017–2025 source files; spin-up must use
   *exactly* 2017–2021, without duplicated/stray years. A Python helper
   preserves the source's working `datavars` and validates all five files.
6. **Site physics:** preserve the successful GF-Guy surface and
   `use_excess_ice = .false.`, `use_excess_ice_streams = .false.`.
7. **Restart continuity:** `REST_N=5`, `STOP_N=5`, `RESUBMIT=59`, archive
   enabled; `rpointer.*` and `2022-01-01-00000` restart files were observed
   after segment 1.
8. **Safe execution:** save to a `.sh` file and execute with `bash`; never
   paste a large script containing `exit` directly into an interactive SSH
   shell. A stopped shell can look like a model failure even when no job ran.

## Verify before claiming convergence

After the **last segment**, inspect Slurm/CaseStatus, last restart date,
NetCDF history coverage and carbon pools. In particular, track
`TOTECOSYSC`, `TOTSOMC`, and `FATES_VEGC`; consider absolute drift,
relative changes across corresponding *5-year forcing-cycle positions*, and
results across multiple final cycles. A numerical threshold and acceptable
spin-up duration must be justified for the scientific experiment; 300 years
does not guarantee equilibrium. Final-cycle GPP/NEE versus EC fluxes is a
separate validation step and not evidence of carbon-pool convergence on its
own. Convergence/EC plotting scripts are **not** included because they have
not yet been tested on the completed 300-year run.

## Code provenance and tests

- Stage 1 case: `examples/FLUXNET_GF-Guy/scripts/{00_config.sh,06_make_surface.sh,07_create_case.sh,08_build_and_submit.sh}`.
- Reference methodology: `examples/ICOS_ES-LJu/scripts/06_make_surface.sh`
  and `07_create_case.sh`.
- IRIDIS evidence: first segment model and archive `COMPLETED 0:0`,
  second segment queued/running, `CONTINUE_RUN=TRUE`, `RESUBMIT=58`,
  archived restart at `2022-01-01`, correct DATM settings.
- Local validation of these packaged *reconstructed* scripts:

```bash
bash -n scripts/10_submit_spinup300.sh
bash -n scripts/11_monitor_spinup300.sh
bash -n scripts/12_verify_spinup300.sh
python -m unittest discover -s tests -v
```

The archived experimental job shows this configuration succeeded in initial
practice; the exact packaged script has **not** been rerun on IRIDIS, and
results of the entire 300 years are not yet confirmed. Do not commit site
raw data, NetCDF files, Slurm logs, credentials, or large restart files.

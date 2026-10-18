# Five-site CLM-FATES spin-up: 1000 to 3000 years

Experiment date: 2026-10-18.

## Scope

Continue five existing FLUXNET single-site CLM-FATES
simulations from 1000 to 3000 cumulative model years.

Included sites:
- RU-Fyo
- DE-Tha
- DK-Sor
- NL-Loo
- IL-Yat

DE-Hai is excluded from this continuation.

## Simulation design

- Previously completed: 1000 model years per site
- Additional spin-up: 2000 model years per site
- Final target: 3000 cumulative model years
- STOP_OPTION: nyears
- STOP_N: 5
- REST_OPTION: nyears
- REST_N: 5
- Additional segments per site: 400
- Initial RESUBMIT: 399
- Calendar: NO_LEAP
- ATM_NCPL: 48

Existing case names remain:
<SITE>_FATES_SPINUP500

The continuation uses the fully archived 1000-year
restart. It does not initialize a new vegetation state.

## Restart targets

| Site | Initial checkpoint | Final target |
|---|---|---|
| RU-Fyo | 2998-01-01 | 4998-01-01 |
| DE-Tha | 2996-01-01 | 4996-01-01 |
| DK-Sor | 2996-01-01 | 4996-01-01 |
| NL-Loo | 2997-01-01 | 4997-01-01 |
| IL-Yat | 3000-01-01 | 5000-01-01 |

These are model-clock dates, not meteorological
forcing years.

## Scientific configuration

The continuation preserves the original:
- Site-specific DATM forcing cycle
- Constant atmospheric CO2
- Surface dataset
- FATES parameters
- Existing compiled executable
- Model restart state

No new forcing or surface datasets are generated.

## IRIDIS6 CPU and MPI configuration

Each model job requests:
- One node
- One CPU
- One MPI rank
- One thread
- 8 GB memory
- No exclusive node allocation

MPI launcher:

srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores

Slurm may allocate the five independent jobs to
the same node or to different nodes.

This configuration addresses previously observed
OpenMPI CPU-affinity problems.

## Scripts

20_five_site_spinup1000_plus2000_oneclick.sh
is the execution wrapper.

21_five_site_spinup1000_to3000_generated.sh
records the generated standalone continuation code.

The wrapper derives its logic from the existing
13_extend_six_site_spinup500_to1000.sh and verifies
the pinned Git blob before generating the new script.

## Execution on IRIDIS6

Run the wrapper from the IRIDIS login node:

bash scripts/20_five_site_spinup1000_plus2000_oneclick.sh all

WARNING: The all command submits real jobs.
Never repeat it blindly after submission.

Read-only status:

bash scripts/21_five_site_spinup1000_to3000_generated.sh status

## Safety and reproducibility

The workflow checks:
- Complete archived 1000-year checkpoints
- Restart pointers
- Model/archive success records
- Existing Slurm jobs
- Case configuration and science input checksums
- Slurm resources and MPI launcher

Backups and execution logs remain outside GitHub.

Completion and carbon-pool convergence are not
claimed by this documentation.

Convergence must be independently evaluated using
carbon pools, slow vegetation dynamics, and
forcing-cycle-aligned diagnostics.

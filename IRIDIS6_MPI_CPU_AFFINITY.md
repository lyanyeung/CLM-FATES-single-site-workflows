# IRIDIS6: Slurm CPU allocation vs OpenMPI process affinity

**Observed on University of Southampton IRIDIS6, 2026-10-13 to 2026-10-14.** Tested with an Intel Classic 2022.2 / OpenMPI 5.0.7 custom module stack, one MPI rank per job, Slurm `batch` partition, and single-point CLM-FATES (CIME). This is a reproducible **case-study** of a launch/binding mismatch, not a claim about every version of OpenMPI, Slurm, all users, or all HPC clusters.

## The short version

Asking Slurm for one CPU does not by itself establish that a separately launched OpenMPI child **runs on that CPU**. Check both the parent job allocation/affinity and the actual process's `Cpus_allowed_list` on the *same node*.

| Stage | Job A | Job B |
|---|---|---|
| Original `mpirun -n 1 --bind-to core --map-by socket`, node `red6129` | Slurm CPU **63** → MPI-launched child CPU **0** (job `4230650`) | Slurm CPU **16** → child CPU **0** (job `4230651`) |
| Validated `srun --mpi=pmix --cpu-bind=cores`, node `red6087` | Slurm CPU **71** → MPI_Init rank CPU **71** (job `4231258`) | Slurm CPU **110** → MPI_Init rank CPU **110** (job `4231259`) |

The first pair used `mpirun` launching a Bash process (`/bin/bash -c ...`), not a C program with `MPI_Init`. This establishes the child-process **affinity mismatch in that launch**, but is not proof that all eight historical `cesm.exe` processes had exactly the same affinity. The second pair used the actual C test program below with `MPI_Init`. A subsequent **real CLM-FATES** IT-Ren restart succeeded with `srun`, corroborating the choice of launcher.

## Why this mattered for eight CLM-FATES sites

There were **two different defects**:

1. **Allocation waste.** Two inherited `#SBATCH --exclusive` directives in the CIME batch configuration allocated an entire 192-core node to one-rank/one-thread model runs. Removing both and requesting `--cpus-per-task=1`, `--mem=8G` allowed nonexclusive sharing.
2. **CPU affinity mismatch.** The nonexclusive CIME jobs still launched `mpirun -n 1 --bind-to core --map-by socket cesm.exe`. All eight jobs shared node `red6082` and hit **`TIMEOUT` at about one hour** for **one** five-model-year segment. A single IT-Ren five-year run previously completed in 00:08:21. Logs for the eight concurrent jobs showed real model progress (IT-Ren 2048-05-20, CZ-BK1 2048-04-06), not an immediate MPI crash. The observed affinity mismatch is consistent with, though not uniquely proven as, the reason for the concurrent slowdown.

The timeouts caused `case.st_archive` to remain `PENDING (DependencyNeverSatisfied)` because it required successful `afterok` completion of the upstream `case.run`. Retain prior *complete* restarts, not partial history files. `sacct TotalCPU` near 1.5 seconds for these timed-out jobs was not representative of the visible multi-year model progression; Slurm step/process accounting needs contextual interpretation.

### CIME details

The historical `env_mach_specific.xml` contained:

```xml
<mpirun mpilib="openmpi">
  <executable>mpirun</executable>
  <arguments>
    <arg name="num_tasks">-n {{ total_tasks }}</arg>
    <arg name="bind">--bind-to core</arg>
    <arg name="map">--map-by socket</arg>
  </arguments>
</mpirun>
```

For **existing, stopped** single-rank CIME cases using the same tested OpenMPI build, override via the case configuration instead of modifying compiled source or rebuilding:

```bash
cd /path/to/existing/CIME-case
./xmlchange 'MPI_RUN_COMMAND=srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
./preview_run
```

Verify the `MPIRUN (job=case.run)` line displays the intended `srun` command plus the *existing* `cesm.exe`. The executable's compile-time MPI remains OpenMPI; only launch is changed. Do not change `MPILIB`, `EXEROOT`, `NTASKS_*`, FATES parameters, forcing, surface data, or restart science while fixing affinity. On IRIDIS6, `srun --mpi=list` reported `pmix` and `pmix_v5`. Test the exact PMIx plugin and MPI stack on your allocation before propagating a launch change.

## Reproduce the affinity comparison

Runnable sources: [`diagnostics/iridis6/mpi_affinity_test.c`](diagnostics/iridis6/mpi_affinity_test.c), [`probe_mpirun_binding.sh`](diagnostics/iridis6/probe_mpirun_binding.sh), [`probe_srun_pmix.sh`](diagnostics/iridis6/probe_srun_pmix.sh). Run the commands on **IRIDIS6**, never on a local WSL terminal.

### 1. Load the same stack as CIME

```bash
source /etc/profile.d/modules.sh
module load intel/2022.2.0.classic.custom
module load openmpi/5.0.7_classic.custom
command -v mpirun
mpirun --version
srun --mpi=list   # should list pmix and pmix_v5
```

An interactive `mpirun: command not found` (or exit 127 in a simple Slurm test) generally means the module stack was **not loaded in that shell/script**. The observed correct binary was `/iridisfs/i6software/openmpi/5.0.7/intel_classic/bin/mpirun`. The Intel Classic compiler's deprecation message did **not** indicate failure.

### 2. Compile an actual MPI test

```bash
# Run from the cloned repository root on IRIDIS6
mpicc -O0 diagnostics/iridis6/mpi_affinity_test.c -o "$HOME/mpi_affinity_test"
test -x "$HOME/mpi_affinity_test"
```

The C executable calls `MPI_Init`, reports `hostname`, `rank`, PID and the process's actual `Cpus_allowed_list`, then sleeps briefly so two test jobs can overlap.

### 3. Compare launch methods (two separate Slurm allocations)

```bash
# From the repository root on IRIDIS6:
sbatch diagnostics/iridis6/probe_mpirun_binding.sh
sbatch diagnostics/iridis6/probe_mpirun_binding.sh
sbatch diagnostics/iridis6/probe_srun_pmix.sh
sbatch diagnostics/iridis6/probe_srun_pmix.sh

squeue -u "$USER" -o '%.12i %.30j %.10T %.8C %R'
# After each test exits, read the corresponding output files in $HOME.
```

Job output includes parent-shell CPU affinity, child MPI-rank CPU affinity and, for `mpirun`, OpenMPI's `--report-bindings` report (in stderr). Compare *actual numeric CPUs* when two tasks land on the **same node**. If different nodes are assigned, that pair does not establish a same-node collision. `core:0` alone is a package-relative notation; the kernel `Cpus_allowed_list` is the decisive mask in this experiment. Tests should be repeated with the real production launch modules and settings; using `/bin/bash` without `MPI_Init` and using a compiled MPI program answer related but not identical questions.

Optional accounting and queue diagnostics:

```bash
squeue --start -j JOBID1,JOBID2
sacct -j JOBID1,JOBID2 -X --format=JobID,State,Elapsed,AllocCPUS,ReqMem,NodeList
sacct -j JOBID1,JOBID2 --format=JobID,State,Elapsed,TotalCPU,MaxRSS
```

`PENDING (Priority)` is ordinary Slurm scheduling, not a broken script. A missing `*.out` before the job starts is normal. Do **not** use `scancel` as a means of raising queue priority or cancel healthy unrelated experiments.

## Validated real-model result and rollout

IT-Ren's `MPI_RUN_COMMAND` was set to:

```text
srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores
```

With `RESUBMIT=0`, `STOP_N=5`, `CONTINUE_RUN=TRUE` and the complete `2044-01-01-00000` restart, the model **successfully simulated 2044–2049**:

- `4232435`: model started at 2026-10-14 01:20:19 BST, `model execution success` and `case.run success` at 01:28:31 (about 8m12s).
- `4232436`: `st_archive success` at 01:29:31.
- Coordinated restart present at `2049-01-01-00000` (50 out of 500 model years).

The complete eight-case recovery program is [`examples/FLUXNET_MultiSite_8/scripts/12_resume_eight_site_srun_pmix500.sh`](examples/FLUXNET_MultiSite_8/scripts/12_resume_eight_site_srun_pmix500.sh); read the [experiment-specific guide](examples/FLUXNET_MultiSite_8/docs/srun_pmix_resume_2026-10-14.md) before using it. Its October 14 `audit` succeeded for all eight sites, then the first `prepare` uncovered a `tee` directory-order bug. The published corrected version creates `"$SESSION/cases/$site"` before opening `prepare.log`. This is a preparation **code** fix, not evidence that the eight 500-year jobs have finished.

### Operational cautions

- `STOP_N=5` means five **model** years per Slurm job; `--time=01:00:00` is the walltime **limit for that single job**, not the whole 500-year run.
- Successful 5-year model execution does **not** imply successful archive. Inspect `CaseStatus` plus the fully coordinated restart directory.
- No automatic resubmission until science, resources, all station restart pointers and safe per-site `RESUBMIT` counts have passed. A single `prepare` marker does not indicate that 500 years completed.
- If a test/production job is `TIMEOUT`, check `atm.log`, `lnd.log`, `cesm.log`, and actual CPU masks before increasing walltime or cores.
- This is a single-rank workaround verified for the above compiler/MPI stack. Multi-rank or multi-node runs require separate performance and binding tests; do not apply hard-coded `--ntasks=1` blindly.
- No real flux-tower data, forcing NetCDFs, model outputs, checkpoints, or credentials are committed with this documentation.

## Upstream references

- [Open MPI v5 — Launching applications with Slurm](https://docs.open-mpi.org/en/v5.0.x/launching-apps/slurm.html)
- [Slurm — `srun` and `--cpu-bind`](https://slurm.schedmd.com/srun.html)
- [Slurm — `sacct` accounting fields](https://slurm.schedmd.com/sacct.html)
- [CIME repository and documentation](https://github.com/ESMCI/cime)

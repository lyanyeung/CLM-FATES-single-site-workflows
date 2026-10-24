# Four-batch CLM-FATES convergence and original EC comparison (24 October 2026)

## Scope and status

Per the operator's IRIDIS6 monitoring snapshot: 36 of 38 stations have >=1000 completed model years.
All 6 MultiSite_6, all 8 MultiSite_8, 9 MultiSite_11, and all 13 MultiSite_13 sites are included.
**IT-Noe (755/1000) and CH-Aws (695/1000) remain excluded.**
Monitor completion is not by itself proof of complete archived annual histories or ecological equilibrium.

The science and publication runner is [`31_crossbatch_convergence_ec_36sites.py`](31_crossbatch_convergence_ec_36sites.py).

## Scientific method and comparability

- Default: MultiSite_6 uses each site's latest verified archived three-component restart and histories (including DK-Sor at 2425 years); the other three batches use exactly the first 1000 complete model years.
- Add `--standard1000` to both audit and run for a uniform 1000-year comparison across *all* 36 sites.
- Original site forcing periods and original case names are preserved: `_FATES_SPINUP500` (batches 6/8), `_FATES_SPINUP500_11P` (batch 11) and `_FATES_SPINUP1000_S30SHARED` (batch 13).
- No annual NetCDF can be missing inside the selected analysis horizon. If the on-Scratch restart is unavailable (e.g., moved to RFS), history coverage can be analysed but restart verification is marked unavailable.
- Annual carbon pools (full trajectory and final 250 years), 100/250-year trends, phase-aligned adjacent forcing-cycle checks, actual FATES vegetation-carbon PFT shares, and monthly observed EC vs FATES GPP/NEE are generated using the **existing science routines** in batches 6 stage 10/14/27 and batch 11 stage 19.
- Model GPP = `FATES_GPP`; model NEE = `-FATES_NEP`; EC GPP prefers `GPP_DT_VUT_REF` (NT fallback if needed), EC NEE = `NEE_VUT_REF`.
- Paired monthly units: g C m^-2 d^-1, >=40 accepted half-hours per day and >=20 matched days per month; R2 is 1 - SSE/SST, not squared correlation.
- Always use the last **complete** 29/other-year site forcing cycle, aligned to the original observational calendar. Exclude incomplete trailing cycles from EC validation.
- The exploratory 1% convergence screen is not an equilibrium certificate. PFT vegetation-carbon proportions are not measured PFT cover or tree species shares.

## Outputs

Each batch writes a *new immutable timestamped snapshot* under its Research Filestore directory:

```text
/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_<6|8|11|13>/convergence_snapshots/<UTCstamp>_Batch<batch>_<latest|1000year>_science36/
```

Each site gets exactly four standard PNG figures and their derived annual-carbon, convergence, PFT, paired-monthly EC, monthly-metrics CSVs, plus metadata JSON. The batch root receives `batch_convergence_summary.csv` and `RUN_INFO.json`.

The GitHub publisher copies **only derived PNG/CSV/JSON and SHA256SUMS** to the matching `examples/FLUXNET_MultiSite_<batch>/figures/convergence_snapshots/<snapshot>/` path. It does not upload raw observations, forcing, surface inputs, NetCDF annual model histories, CIME files or restarts. Older figures are not overwritten.

## 24 October 2026 correction — run interactively on the login node

Job 4714875 failed after 3 seconds because the compute node reported that
`/research/xclimatetbm/ly3n24/CLM_FATES` was not writable/visible. This is
not evidence of a Python plotting error, missing model history, or GitHub
network failure. The revised Stage 31 script checks actual filesystem
writability, preferentially writes to Research Filestore, and stages derived
outputs under `~/FLUXNET36_derived` if Research Filestore is unavailable.

**The preferred procedure for this specific operator is direct foreground
execution on the login node, without submitting a Slurm job**, subject to
local login-node usage policy:

```bash
set -o pipefail
cd ~/CLM-FATES-single-site-workflows
git fetch origin main
git show origin/main:scripts/convergence/31_crossbatch_convergence_ec_36sites.py > "$HOME/FLUXNET36_analysis.py"
PY="$HOME/.conda/envs/clm_fates_env/bin/python"
"$PY" -m py_compile "$HOME/FLUXNET36_analysis.py"
"$PY" -u -B "$HOME/FLUXNET36_analysis.py" run --batch all --publish 2>&1 | tee "$HOME/FLUXNET36_analysis.log"
```

For a preflight first, execute `"$PY" -u -B "$HOME/FLUXNET36_analysis.py" audit --batch all`.
The `-u` flag streams annual-file progress live. Failed sites are explicitly
recorded and their batch is not published. The two unfinished sites are always
excluded. Publishing runs only after all required derived files in the given
batch are validated and accesses GitHub via the login node.

For any successful batch that had to stage its output under Home, transfer its
derived products to Research Filestore later (from a node with RFS access),
then publish if needed:

```bash
"$PY" -u -B "$HOME/FLUXNET36_analysis.py" sync --snapshot /home/ly3n24/FLUXNET36_derived/FLUXNET_MultiSite_<batch>/convergence_snapshots/<actual_snapshot> --dry-run
"$PY" -u -B "$HOME/FLUXNET36_analysis.py" sync --snapshot /home/ly3n24/FLUXNET36_derived/FLUXNET_MultiSite_<batch>/convergence_snapshots/<actual_snapshot>
```

Do not run the older Slurm step below; it is retained only as a historical
alternative and caused the recorded RFS mounting failure on job 4714875.

## Older IRIDIS6 Slurm instructions (superseded for this operator)

### A. Fetch and audit on login node (no git pull needed)

```bash
set -euo pipefail
cd ~/CLM-FATES-single-site-workflows
git fetch origin main
git show origin/main:scripts/convergence/31_crossbatch_convergence_ec_36sites.py > "$HOME/FLUXNET36_analysis.py"
PY="$HOME/.conda/envs/clm_fates_env/bin/python"
"$PY" -B "$HOME/FLUXNET36_analysis.py" audit --batch all 2>&1 | tee "$HOME/FLUXNET36_audit.log"
```

Resolve any `BLOCKED` site before generating the full 36-site set. The audit reads directory metadata and DATM stream settings, not all model values.

### B. Analyse on a Slurm compute node, not the login node

```bash
cat > "$HOME/FLUXNET36_analysis.sbatch" <<'BASH'
#!/usr/bin/env bash
#SBATCH --job-name=flux36_figures
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=12:00:00
set -euo pipefail
PY="$HOME/.conda/envs/clm_fates_env/bin/python"
"$PY" -B "$HOME/FLUXNET36_analysis.py" run --batch all 2>&1 | tee "$HOME/FLUXNET36_analysis.log"
BASH
sbatch "$HOME/FLUXNET36_analysis.sbatch"
```

If a station fails, its error is retained in the batch summary and that batch is **not** eligible for GitHub publication. Successfully analysed batches remain intact on Research Filestore. Slurm completion and science completion are distinct; inspect the printed summary.

### C. Publish on login node *after* analysis and verify GitHub success

```bash
set -euo pipefail
PY="$HOME/.conda/envs/clm_fates_env/bin/python"
SCRIPT="$HOME/FLUXNET36_analysis.py"
LOG="$HOME/FLUXNET36_analysis.log"
mapfile -t SNAPSHOTS < <(grep -E '^BATCH (6|8|11|13) SUMMARY:' "$LOG" | sed -E 's|^.*RFS=||')
[[ "${#SNAPSHOTS[@]}" -eq 4 ]] || { echo 'Expected exactly four snapshots'; exit 1; }
for d in "${SNAPSHOTS[@]}"; do
  "$PY" -B "$SCRIPT" publish --snapshot "$d" --dry-run
done
for d in "${SNAPSHOTS[@]}"; do
  "$PY" -B "$SCRIPT" publish --snapshot "$d"
done
```

Publication requires every expected station in its batch to be `Status=OK` with complete PFT and monthly GPP/NEE products, full-cycle provenance and >=1000 verified annual histories. It hashes and stages an explicit derived-file allowlist in a fresh temporary clone, avoiding the user's possibly conflicted working tree. A `GITHUB PUBLISH SUCCESS` message and commit SHA must be observed before claiming that the plots have been uploaded.

**GitHub presently contains the workflow, not the newly generated 36-site analysis files.** Those can only be published after the runner accesses the IRIDIS6 Research Filestore.

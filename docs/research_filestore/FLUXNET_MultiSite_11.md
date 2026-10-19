# FLUXNET_MultiSite_11: nine completed 1000-year spin-ups — Research Filestore archival

**Documented:** 2026-10-20. **Evidence:** user-supplied IRIDIS6 read-only progress report. Nine completed: BE-Bra, FR-Fon, GL-ZaH, AT-Neu, FI-Sod, CH-Cha, CH-Fru, CH-Lae, CZ-Stn. IT-Noe (5 archived years) and CH-Aws (0 archived years) **are excluded** from this transfer.

The nine successful cases each have 1000 archived annual `h0a` files, `RESUBMIT=0`, and successful `st_archive` status. This establishes the completed simulation length **only**. It does **not** certify carbon convergence, meteorological science quality or Research Filestore transfer completion.

## Storage layout

Source case naming remains `<SITE>_FATES_SPINUP500_11P`, despite 1000 model years.

- Original CIME archive: `/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/<CASE>/`
- Original run dir: `/scratch/ly3n24/CTSM_FATES_OUTPUTS/<CASE>/run/`
- Original CIME case: `/iridisfs/scratch/ly3n24/CLM_FATES/cases/<CASE>/`
- Research destination: `/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/FLUXNET_MultiSite_11/<SITE>/<CASE>/`

Per site, the script creates `archive/` (complete short-term archive including `lnd/hist` and `rest`), `run_snapshot/` (complete final run-directory snapshot), `case_snapshot/` (selected CIME configuration files), `manifest_sha256.tsv`, and `verification_receipt.json`. It does not copy full CIME case Git metadata nor raw forcing packages.

## Execute on IRIDIS6

Run on a login node with the Research Filestore mounted. Ensure there are no active jobs for these nine cases, and sufficient **space and file-count quota on the Research Filestore**. Because the procedure copies entire archive and run snapshots, inspect sizes before copying; the transfer may be substantial.

```bash
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only origin main

myfiles
df -h /research/xclimatetbm
squeue -u ly3n24 -o '%.12i %.65j %.10T %R'

# Check the nine complete consecutive annual history series without writing files
python3 scripts/research_filestore/archive_eleven_site_1000yr.py inspect

# Copy with rsync; verify every copied regular file's SHA-256, one site at a time
python3 -u scripts/research_filestore/archive_eleven_site_1000yr.py copy \
  2>&1 | tee ~/FLUXNET11_research_filestore_copy.log

# Independently repeat the complete byte-wise verification
python3 -u scripts/research_filestore/archive_eleven_site_1000yr.py verify \
  2>&1 | tee ~/FLUXNET11_research_filestore_verify.log

myfiles
```

For a cautious pilot, run only BE-Bra first with `inspect --sites BE-Bra`, then `copy --sites BE-Bra` and `verify --sites BE-Bra`. Resume the rest with `--sites FR-Fon GL-ZaH AT-Neu FI-Sod CH-Cha CH-Fru CH-Lae CZ-Stn`. A failed copy can be retried. There is **no** deletion mode.

**Before running:** `df -h` alone is not proof that a per-project quota or a file-count quota has headroom. If any transfer reports `quota exceeded`, stop, check the share quota with Research Filestore administrators, and do not remove Scratch originals.

## Interpretation and retention

The script checks all 1000 annual `h0a` years by filenames against the case's site-specific starting year, with no gaps or duplicates. It then copies, inventories source/destination, and compares SHA-256 file contents and symlink destinations. It writes receipt files **only after successful verification**. In `verify` mode it re-hashes the same files. Any mismatch aborts with nonzero exit status.

**Important:** Do not delete Scratch history, restart checkpoints, `rpointer.*`, case directories, active recovery snapshots, executables, or source forcing. Full CIME continuation may require more than an archived final-year output. Neither `inspect` nor completion receipts prove a scientifically converged spin-up. Confirm future continuation requirements before any separate cleanup. The two unfinished sites are deliberately untouched.

For storage policy and the earlier file-count quota incident, see [Research Filestore overview](README.md) and [six-site case study](FLUXNET_MultiSite_6.md). Raw NetCDFs and the original tower inputs are not published to GitHub.

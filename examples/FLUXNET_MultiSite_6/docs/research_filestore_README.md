# Research Filestore archive: first 1000 model years of the FLUXNET six-site CLM-FATES experiments

**Record date:** 2026-10-19. **Scope:** `examples/FLUXNET_MultiSite_6/`.

> **Evidence boundary.** The Southampton Research Filestore mount, storage statistics, Scratch quota failure, and previously published five-site 1000-year *model results* are established. **A completed file transfer, verified destination inventory, and Scratch cleanup have not been evidenced to this record**; migration claims must be confirmed from per-site checksums and live filesystem status. This document is the migration design and recovery runbook—not a falsely asserted completion certificate.

## 1. Context and objectives

The six-site experiment uses fixed initial-year atmospheric CO₂, site-specific half-hourly FLUXNET-derived forcing cycled over a `NO_LEAP` calendar, five-year CESM/CIME resubmission segments, and annually archived land-history files. The original cases are named `<SITE>_FATES_SPINUP500` **even after** successful extension from 500 to 1000 model years.

On 2026-10-18, many CLM-FATES model jobs failed within minutes and their dependent `st_archive` jobs became `DependencyNeverSatisfied`. CESM `cesm.log` showed `Disk quota exceeded` from ParallelIO (`PIOc_createfile`); some CIME Git operations could not create `.git/index.lock`. The subsequent `myfiles` output identified the cause:

```text
Home number of files used:       32,632 / 204,800
Scratch space used (GB):             629 / 2,000
Scratch number of files used:    614,400 / 614,400
```

**The Scratch file-count quota, rather than space capacity, was exhausted.** A different `mpirun` launch used by an unrelated DE-Lnf case is not evidence for the mass failures; that case also reported the same storage error.

The archival goal is to transfer completed 1000-year model-history data to Southampton's Research Filestore so large NetCDFs can be read by xarray for future carbon-pool convergence and tower GPP/NEE comparisons. Release of Scratch file-count quota should occur **only after verification**, without disturbing the five-station continuation toward 3000 model years.

## 2. Scientific status and station identities

The [main six-site README](../README.md) records five stations with 1000 complete annual `clm2.h0a` NetCDFs and published carbon-pool, convergence, and monthly GPP/NEE figures. **DE-Hai was excluded from this final five-site 1000-year release.** The latter is a *backup-only*, potentially incomplete case, not a sixth complete simulation.

| Station | Original CIME case | 1000-year result status | Retention approach |
|:--|:--|:--|:--|
| RU-Fyo | `RU-Fyo_FATES_SPINUP500` | Completed; figures + CSV published | Archive historical results; preserve active continuation state |
| DE-Tha | `DE-Tha_FATES_SPINUP500` | Completed; figures + CSV published | Same |
| DK-Sor | `DK-Sor_FATES_SPINUP500` | Completed; figures + CSV published | Same; check historical-CO₂ experiment dependencies |
| NL-Loo | `NL-Loo_FATES_SPINUP500` | Completed; figures + CSV published | Same |
| IL-Yat | `IL-Yat_FATES_SPINUP500` | Completed; figures + CSV published | Same; structural vegetation-carbon interpretation requires care |
| DE-Hai | `DE-Hai_FATES_SPINUP500` | **Not verified complete at 1000 years** | Copy what exists as backup only; **retain all originals** |

Model convergence must not be inferred from the fact that a 1000-year run finished. The related [1000→3000 continuation workflow](spinup1000_to3000_continuation_2026-10-18.md) adds 2000 years in 400 five-year segments and **reuses the same original case names**. Its script records the correct five-site membership (excluding DE-Hai).

Existing publishable plots and CSVs are already tracked at [`figures/spinup1000_final/`](../figures/spinup1000_final/), including each station's `*_01_carbon_pools_annual_mean.png`, `*_02_carbon_pools_last250years.png`, `*_GPP_NEE_monthly_overview.png`, `*_carbon_annual_means.csv`, `*_convergence_metrics.csv`, and `*_monthly_metrics.csv`. These plots **stay on GitHub**; raw time-series NetCDF files and full restart state **do not**.

## 3. Storage locations

| Role | Path |
|--|--|
| Original archive (IRIDIS6 Scratch) | `/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/<CASE>/` |
| CIME case (must remain intact) | `/iridisfs/scratch/ly3n24/CLM_FATES/cases/<CASE>/` |
| Active run directory (must remain intact) | `/scratch/ly3n24/CTSM_FATES_OUTPUTS/<CASE>/run/` |
| Research Filestore root | `/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/FLUXNET_MultiSite_6/` |
| Windows SMB share | `\\\\xclimatetbm.files.soton.ac.uk\\xclimatetbm` |

The Research Filestore was accessible via NFS on the checked IRIDIS6 login node. At inspection it showed approximately **2.5 TB total, 314 GB used and 2.2 TB available**. Global NFS inode statistics do not prove the absence of a separate project quota.

The intended destination structure is:

```text
/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/
└── FLUXNET_MultiSite_6/
    ├── RU-Fyo/RU-Fyo_FATES_SPINUP500/
    │   ├── archive/lnd/hist/*.nc
    │   ├── archive/rest/<checkpoint>/*
    │   ├── case_snapshot/{CaseStatus,env_*.xml,user_nl_*,...}
    │   └── manifest_sha256.tsv
    ├── DE-Tha/...
    ├── DK-Sor/...
    ├── NL-Loo/...
    ├── IL-Yat/...
    └── DE-Hai/...  # backup only; incomplete until separately verified
```

## 4. Practical usage on IRIDIS6

Start with a **read-only** inspection:

```bash
myfiles
df -h /research/xclimatetbm
df -i /research/xclimatetbm
squeue -u ly3n24 -o '%.12i %.72j %.2t %.35R'
python3 examples/FLUXNET_MultiSite_6/scripts/22_audit_research_filestore_sixsite.py
```

The checker below is read-only; run it from a repository checkout on IRIDIS6. It reports the 1000-year h0a inventory, latest restart timestamps, NFS contents and transfer-manifest status for each of the six stations. It never removes model data.

The previously prepared operational script `migrate_six_site_1000yr.py` (distributed outside GitHub pending further safety checks) has proposed modes `plan`, `copy`, `prune`, and `migrate`. **Do not run destructive `prune`/`migrate` automatically** just because the five-site scientific figures exist. That older script assumes particular checkpoint paths; its runtime preconditions must be validated against the *current* 1000→3000 continuation and the exact complete-year inventory first. This repository intentionally provides the read-only checker instead of uploading a deletion-capable script as the default example.

For individual completed sites, the following commands **copy only**; no deletes:

```bash
site=RU-Fyo
case="${site}_FATES_SPINUP500"
src="/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/$case/lnd/hist"
dst="/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/FLUXNET_MultiSite_6/$site/$case/archive/lnd/hist"
mkdir -p "$dst"
rsync -a --checksum --info=progress2 "$src/" "$dst/"
rsync -ani --checksum "$src/" "$dst/"   # should report no changed files
```

This copies *all* h0a/hist files in the source folder, including later 1000→3000 history if present. To archive **only** the first 1000 model years, first classify files by the original simulation start date and filename year. Inspect rather than blindly copy/delete when continuation is present.

## 5. Minimum retention safeguards before deleting anything from Scratch

1. Check `squeue` for each site; a pending `st_archive` with `DependencyNeverSatisfied` is a failed dependency, not proof the simulation is idle and safe for cleanup. Verify all related run and archive jobs.
2. Check all 1000 expected annual model years for five completed stations, plus *actual* available years for DE-Hai. The original first years are RU-Fyo 1998, DE-Tha 1996, DK-Sor 1996, NL-Loo 1997, IL-Yat 2000, DE-Hai 2000.
3. Compare source/destination filenames, sizes and SHA-256 hashes; keep a per-site manifest on Research Filestore. Validate netCDF readability.
4. **Never remove** source `case/`, `run/`, source inputs, the active restart checkpoint(s), `rpointer.*`, shared `cesm.exe`, or partial current-cycle output that might be needed for recovery.
5. Specifically preserve the **1000-year boundary checkpoint** and the latest full 1000→3000 continuation restart; the [continuation script](../scripts/21_five_site_spinup1000_to3000_generated.sh) stages and validates coordinated ATM/LND/CPL restart components.
6. **DE-Hai must remain backup-only.** Do not delete its Scratch originals on the basis of five-site reports.
7. Re-check `myfiles` after any explicitly approved cleanup. Deleting large files is not equivalent to releasing a large number of file-count slots; count the candidate files first.

## 6. Reading the moved NetCDFs for plotting

```python
from pathlib import Path
import xarray as xr

site = 'RU-Fyo'
case = f'{site}_FATES_SPINUP500'
base = Path('/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/FLUXNET_MultiSite_6')
hist = base / site / case / 'archive/lnd/hist'
files = sorted(hist.glob(f'{case}.clm2.h0a.*.nc'))
assert files, f'No h0a NetCDFs in {hist}'
with xr.open_dataset(files[0], decode_times=False) as ds:
    print(sorted(ds.data_vars))
```

The plotting implementation [`14_plot_five_site_spinup1000.py`](../scripts/14_plot_five_site_spinup1000.py) may need a configurable archive input root to use the NFS copy. Keep output figures/CSV in GitHub, but exclude all raw tower data, full NetCDF history, and restart files from Git.

## 7. Proof-of-migration checklist (pending live audit)

- [ ] Five sites have **exactly the intended first-1000-years** copied to NFS, with checksum inventories.
- [ ] DE-Hai has an explicitly identified **partial backup** and all its Scratch originals preserved.
- [ ] NFS files can be opened by xarray/netCDF4.
- [ ] Latest CIME continuation restart is untouched and usable.
- [ ] A post-cleanup `myfiles` report demonstrates that Scratch file-count usage dropped.
- [ ] The actual migration command output and manifest timestamp are recorded in this document.

**Do not mark the above boxes complete until the actual IRIDIS6 runs and checksums are available.**

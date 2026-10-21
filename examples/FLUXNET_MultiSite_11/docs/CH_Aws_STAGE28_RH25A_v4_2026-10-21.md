# CH-Aws Stage28 — nine-record humidity sensitivity candidate and remaining low-RH review

**Status: exploratory data candidate, not observation-validated meteorology and not a demonstrated CLM-FATES model fix.** Prepared on IRIDIS6 on 21 October 2026; subsequent repository scripts are reconstructed reproducibility tools and should not be misrepresented as the exact byte-identical scripts executed before publication.

## Model incident

- Failed 16-day CH-Aws run: `CH-Aws_FATES_RH25A_DIAG16D_20261020`, Slurm job `4496106`; `FAILED 1:0` after 26 s. Its `lnd.log` printed `rh = -1.07854999704740` and `ERROR RH is negative ERROR in HumanIndexMod.F90 at line 1019`. Stack implicated `BareGroundFluxesMod.F90` line 507. This reproduces the existing RH25A first-segment failure; it is **not** a completed 16-day or 1000-year run.
- History created: 328 `h0a` and 328 `h0i` NetCDFs (656 total) through the last historical file timestamp `2006-01-14-57600` (16:00), but do not assume the last successfully flushed time is precisely the fatal calculation timestamp.
- The last available `h0a` file contains approximate `TG=269.417 K`, `TSA=268.058 K`, `QSOIL=1.68096e-06 kg m-2 s-1`. These do not give instantaneous `qg`, moisture roughness `z0q`, or Monin–Obukhov stability.
- `FrictionVelocityMod.F90` uses different exchange coefficients at the forcing reference height (`temp2`) and diagnostic 2 m (`temp22m`). `BareGroundFluxesMod.F90` derives `q_ref2m = forc_q + (temp2/temp22m)*(forc_q - qg)*(1 - temp22m/temp2)` [algebraically `q_ref2m = (temp2/temp22m)*forc_q + (1 - temp2/temp22m)*qg`]. With provisional 1.5 m `ZBOT`, extrapolation to 2 m may contribute to negative `q_ref2m` in very dry air. This mechanism is **plausible, not proven**.

## Forcing provenance and observational limitations

At the critical boundary:

| Local standard time UTC+1 | RH from RH25A CSV (%) | Existing source | ERA5 RH (%) | ERA5-Land RH (%) |
| --- | ---: | --- | ---: | ---: |
| 2006-01-14 14:00 | 35.280 | Stage21 ERA5-Land trial | 20.699 | 35.280 |
| 2006-01-14 14:30 | 8.066 | EUF_F QC2 | 19.072 | 34.549 |
| 2006-01-14 15:00 | 8.282 | EUF_F QC2 | 17.570 | 33.833 |
| 2006-01-14 15:30 | 7.620 | EUF_F QC2 | 17.180 | 32.745 |
| 2006-01-14 16:00 | 7.062 | EUF_F QC2 | 16.798 | 31.686 |

Stage21 intentionally required both reference estimates >=20% RH and <=15 percentage-point separation. The 14:30–16:30 events therefore failed its conservative selection criteria. Two reanalyses differ by 14–16 pp; ERA5-Land should not be treated as direct tower RH evidence, particularly over complex mountain terrain. Input RH may also depend on saturation convention (water versus ice below 0 °C).

## Stage28 v4 sensitivity file

A **single independent** 2006 NetCDF was constructed:

`/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing/datm_11_stage28_jan14_trial_v4/CH-Aws_DATM_2006.nc`

Accompanying files on IRIDIS6: `CH-Aws_stage28_9row_ledger.csv` and `stage28_manifest.json`.

- Only `QBOT` at **nine** timestamps between **2006-01-14 14:30** and **18:30**, every 30 min, was changed, replacing reconstructed site-air moisture with ERA5-Land RH transferred to site `TA_F` and `PA_F`.
- Before: RH min/max across the nine rows **4.587% / 8.282%**; candidate after: **27.750% / 34.549%**.
- Independent IRIDIS6 validation printed **`VERIFY SUCCESS`**: exactly nine `QBOT` values changed; `time`, `lat`, `lon`, `LATIXY`, `LONGXY`, `TBOT`, `PSRF`, `FSDS`, `FLDS`, `WIND`, `PRECTmms`, and `ZBOT` were identical.
- Original 2006–2024 `datm_11_landrh25a_dynamic_zbot_v3` remains unmodified. There is **no** Stage28 CIME/DATM stream pointing at the new 2006 file, and **no** formal spin-up evidence for this candidate.
- **No site CSV, independent reference data, DATM NetCDF, CIME case, Slurm output, binary, credential, or licensed source dataset has been uploaded to GitHub.** Only methods/scripts/documentation are versioned.

## Pending records and next evidence gate

The current RH25A CSV contains **77** records across **19** periods satisfying `EUF_F`, `VPD_F_QC=2`, and `RH<10%`. The 9 independent v4 January candidates leave **68** still unaddressed:

| Year | Unresolved half-hour rows |
| --- | ---: |
| 2006 | 8 |
| 2007 | 2 |
| 2008 | 3 |
| 2010 | 1 |
| 2012 | 2 |
| 2013 | 29 |
| 2014 | 23 |

2006 remaining periods: 25 January and 7 November. Important later periods include **2013-12-03–04** and **2014-01-12–13**, **2014-03-09–13**. Stage20 cached ERA5/ERA5-Land comparison covers 2006–2013, **not 2014**. Do not automatically replace all 68 records. A low QC2 RH alone does not prove the forcing is wrong; the presence of reanalysis alternatives is evidence for a sensitivity analysis, not observational validation.

## Repository code and commands

From the repo on IRIDIS6:

```bash
cd /iridisfs/home/ly3n24/CLM-FATES-single-site-workflows
git pull --ff-only origin main
conda activate clm_fates_env

# Default is read-only; proposed 9-row forcing and source check:
python examples/FLUXNET_MultiSite_11/scripts/stage28/28_chaws_jan14_v4.py --audit

# Read-only independent recheck of ALREADY EXISTING independent 2006 v4:
python examples/FLUXNET_MultiSite_11/scripts/stage28/28_chaws_jan14_v4.py --verify

# Read-only 68-row future review; writes small summary CSV under HOME:
python examples/FLUXNET_MultiSite_11/scripts/stage28/29_chaws_remaining_rh_readonly.py
```

`28_chaws_jan14_v4.py --write --acknowledge-reanalysis-uncertainty` is **only** for reconstruction when v4 does **not** exist; the script refuses overwrites. Do not run it against existing v4. Before starting a formal spin-up, complete scientific source/clock and sensor-height assessment, decide treatment of remaining records, independently verify full multi-year DATM streams, and obtain an explicit run decision. Do not submit new diagnostic Slurm jobs as part of this workflow.

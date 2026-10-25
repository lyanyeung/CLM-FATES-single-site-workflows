# Batch03 Stage12g re-run VERIFIED: 121 additional US-Kon RH-only science candidates

**2026-10-25 08:02 UTC** — User ran the unchanged, Git-blob/SHA-pinned [Stage12g](../scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py) after the Stage12l successful external ERA5-Land CDS downloads for US-Kon 2008, 2011 and 2012. Python AST, `--self-test`, `--check`, exact verified-source assertions, and `--run` ALL PASSED. New **isolated, SHA-receipted, INCOMPLETE** six-site NOLEAP scientific forcing trial:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12g_six_site_new_year_gridRH_science_20261025T080248Z_bb717f66/`

## Exact site science results (do not interpret source-years as humidity approvals)

| Site | Previously missing-year native humidity records | New gridded year evidence coverage | New numerically valid Stage12g RH/QBOT candidates | Unverified source-year records remaining | Rows missing any forcing variable after Stage12g |
|---|---:|---:|---:|---:|---:|
| US-NR3 | 6 | 0 | 0 | 6 | 238 |
| US-Kon | 211 | **196** | **121** | 15 | **367** |
| US-NR1 | 135 | 0 | 0 | 135 | 238 |
| US-MMS | 15 | 0 | 0 | 15 | 16 |
| US-MtB | 2,363 | 1,038 | **3** (inherited from Stage12g first run) | 1,325 | 2,840 |
| US-Me6 | 80 | 0 | 0 | 80 | 81 |
| **Total** | **2,810** | **1,234** | **124 (121 US-Kon new; 3 previous US-MtB)** | **1,576** | **3,780** |

US-Kon **121/196 = 61.7347%** screened numeric repairs in the three newly verified yearly source slices, 75/196 still science-held:

| US-Kon hold reason after newly verified 3 years | Original native half-hours |
|---|---:|
| `HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA` | 34 |
| `HOLD_SITE_GRID_T_DIFF_GT5C` | 40 |
| `HOLD_ORIGINAL_QC_OR_SITE_T_P` | 1 |
| **Total newly verified-source site/year holds** | **75** |
| `MISSING_VERIFIED_STAGE12F_SOURCE_YEAR` (not yet downloaded) | **15 additional** |

Six-site missing forcing time rows fell from 3,901 at prior Stage12g to **3,780**. Five NON-US-MtB sites now have **940** incomplete time rows (US-Kon 367, US-NR1 238, US-NR3 238, US-MMS 16, US-Me6 81). US-MtB remains 2,840 incomplete, all 1,035 held T/ice events, prior Stage12j strict GRID_RH observational failure, and 233 original pre-Stage12b physics holds stay UNCHANGED.

Original EC tower TA, site PSRF, calendar source-native time, all existing Stage12b/c/d/e previously numeric repairs, original measured QC0 source RH, PFT/surface data and original source-provenance receipts are unchanged; Post-v5/DATM/spinup approvals **ZERO**. Numerically passing Stage12g rows are research-only candidates, not signed production-forcing replacements.

## Next action — reuse Stage12l with no new script

Original source evidence pool for five non-US-MtB sites: 447 records across 30 site-years, 196 verified source rows in 3 US-Kon year sources, **251 still missing evidence in 27 site-years**. The [unchanged Stage12l](../scripts/stage12/12l_five_site_non_MtB_year_source_priority.py) dynamically selects the next three unverified site/year sources (observed sorted queue from the 07:57 log, assuming no intervening download):

| Next ranked source | Original newly source-missing RH records |
|---|---:|
| US-Me6 2015 | 42 |
| US-Me6 2017 | 36 |
| US-NR1 2022 | 22 |
| **Total** | **100** |

First call Stage12l `--check` (strict zero writes) and inspect selection/receipts; then Stage12l `--download --max-new 3`, which uses the already SHA-pinned Stage12f CDS source-only validation implementation and excludes US-MtB. After all three verified, call the original Stage12g `--check` and confirm **9 verified new site-years, 1,334 original source-event coverage, 1,476 source-missing events remaining**, then `--run` to create a new **separate** incomplete six-site shadow. This second candidate count cannot be guessed; derive it from stage12g real site-wise result. The 40 US-Kon T misfit and 34 jump holds remain held pending separate scientific diagnosis, not threshold relaxation. 

**Avoid mistaken science gate:** Stage12l source download success is only provenance, not humidity acceptance. Stage12g site-relative offset remains provisional; measured QC0 never replaced, no changing source tower T and no DATM or spinup release.

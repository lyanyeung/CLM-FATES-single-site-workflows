# Batch03 Stage12e VERIFIED; Stage12f missing-year source acquisition

**2026-10-24 IRIDIS6:** Stage12e `--self-test`, `--check`, and `--run` all passed. The six existing source-native research shadows remain incomplete and SHA-sealed:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97/`

Stage12e added **702** grid-relative-humidity numerical research events at unchanged original EC tower temperature and surface pressure. Inherited research patch sources: 1,687 Stage12b, 3,792 Stage12d. Previously source-sealed original 233 water/ice/temperature holds persist. Another 3,670 additional humidity rows remain unresolved, and there are **3,904 distinct six-site native time rows without full valid forcing**, so NO Post-v5/DATM/spinup approval is granted.

## Why more than a single source is necessary

| Stage12e remaining extra humidity hold reason | Exact rows | Action |
| --- | ---: | --- |
| NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR | **2,810** | Priority: fetch missing year/site ERA5-Land original evidence in small, SHA-verified batches |
| HOLD_ERA5LAND_TOWER_T_DELTA_GT5C | **791** | Investigate full temperature source, site elevation and actual original clock; never relax automatically |
| HOLD_ICE_PHASE_WATER_RH_SUPERSATURATION | **20** | Check water/ice thermodynamics, keep held |
| HOLD_NEW_ADJACENT_VPD_JUMP_OVER4HPA | **49** | Event-level transition review, keep held |
| **Total** | **3,670** | |

The **2,810** no-year-source native half-hours by site: US-MtB **2,363**, US-Kon **211**, US-NR1 **135**, US-Me6 **80**, US-MMS **15**, US-NR3 **6**. These counts are from Stage12e's sealed source-native event ledger, not from a guess about which calendar years or time zones are missing.

## Stage12f safe yearly source queue

[12f_missing_year_ERA5Land_download_queue.py](../scripts/stage12/12f_missing_year_ERA5Land_download_queue.py), **committed but not executed on IRIDIS6**, uses the original SHA-verified Stage09a point-location metadata for all six sites, original Stage09f 32 verified site-year NetCDF sources, and the new Stage12e exactly 2,810 missing-year source events.

- `--check`: SHA-validates all input science receipts and current source files, produces a **ranked exact site/year/yearly event count request queue** on standard output, without any writes or CDS request.
- `--download --max-new 3`: by default downloads **at most three** highest-benefit missing site-years (optionally `--site US-MtB`); each original point-year source uses Stage09b's tested CDS ERA5-Land timeseries API request format and time coverage **December 29 of preceding year through January 3 of following year**, and the ORIGINAL SHA-proven site location (no invented lat/long).
- Writes sources ONLY under `external_evidence/era5land_timeseries_stage12f_missing_years/<site>/<year>/`, so the original 32 Stage09f evidence products are immutable. Uses `.download.partial` and `.validation.nc/.zip` intermediates, aborts on conflicting or interrupted previous files, validates exact UTC time span, gridded lat/lon, t2m/d2m/SP CF units, physical RH/dewpoint plausibility and SHA, then creates a `*.receipt.json` unique manifest. No overwrite/retry of partial files without investigation.
- Published source UTC offsets remain **unapproved time hypotheses**; Stage12f does not align downloaded hourly ERA5-Land to tower native time, regenerate VPD/QBOT, or write any forcing. No DATM/CIME/Slurm changes or scientific release.

**After** targeted missing-source years are retrieved and verified, the next step is a separate six-site science-gated successor using those new year data at unchanged source EC TA/PSRF plus the full already-performed Stage12b/c/d/e physical and boundary rules; exclude all 233 original holds and all previously valid humidity. The scientific gate cannot be skipped.


## Stage12f v2 regression fix, 2026-10-24

The first Stage12f IRIDIS6 syntax and self-test passed, but `--check` stopped before download with `Stage09f 32 earlier verified yearly sources changed`. This was a **script assertion bug, not evidence of altered source data**: the original SHA-verified Stage09a source plan contains 32 site-years across all **seven** blocked sites including US-Me2; the Stage12e `verify()` function intentionally returns an existing-source `catalog` filtered to the **six** sites under Stage12e/12f repair. The erroneous check compared the filtered catalog length to 32.

The new [Stage12f script](../scripts/stage12/12f_missing_year_ERA5Land_download_queue.py) validates the full original 32-entry seven-site plan, verifies all original source SHAs through Stage12e/Stage10b, and requires exact set-equality between the six-site filtered year catalog and the six-site subset of the full 32-entry plan. A dedicated self-test reproduces a 32-entry source inventory with 31 eligible plus one excluded US-Me2 source-year and rejects a missing six-site catalog. The initial failure occurred before listing/downloading site-years; no CDS request or forcing/source modification occurred. The exact actual six-site catalog count is intentionally derived from the stored 32-entry manifest on IRIDIS6 rather than assumed to be 31.

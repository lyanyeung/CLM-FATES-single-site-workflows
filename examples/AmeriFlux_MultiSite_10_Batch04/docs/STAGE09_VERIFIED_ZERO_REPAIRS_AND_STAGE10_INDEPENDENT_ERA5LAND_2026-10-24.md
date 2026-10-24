# Batch04 Stage09 VERIFIED zero repairs; Stage10 independent ERA5-Land full-CSV repair path

**Date:** 2026-10-24. Original evidence is the operator's complete IRIDIS6 Stage09 stdout.

## Stage09 exact result

```
STAGE09 SELF-TEST PASS
US-Rpf: 688 ERA_PAIR_HUMIDITY_INVALID events, 688 original source VPD physically invalid; 0 repairs; HOLD 688
US-SRM: 1 ERA_PAIR_HUMIDITY_INVALID event, 1 original source VPD physically invalid; 0 repairs; HOLD 1
STAGE09 APPLIED 0 variable patches, unresolved Stage08 HOLDs 696 of previous 696
NO ORIGINAL, STAGE07, STAGE08, DATM OR SLURM WRITES
```

Stage09 produced a new complete (unchanged) US-Rpf and US-SRM derived FLUXMET copy, not a repair. It confirmed why no changes can be made with the old policy: native VPD is physically invalid in all 689 targeted records, companion FLUXNET packaged ERA humidity pairs are invalid, and no targeted original VPD times satisfy max-four-HH trustworthy-neighbour interpolation.

**Directory:**
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage09_native_humidity_fallback/candidate_20261024T121412Z_94cc703f`

**Verified derived CSV SHA256 unchanged from Stage08:**
- US-Rpf `63b0316017b6584137c3800ad3a99650fb567ba2e6a28686d3cb4d53e9fc7e57`
- US-SRM `506b59a584ce446d5d6db15348b22b5346a515ee1a7cddc000c22598c865349f`

## Stage10 actual external-source repair method — committed, NOT yet run

[Stage10 script](../scripts/stage10/10_era5land_independent_humidity_fill.py) implements an **incremental real external CDS input and full derived CSV output**:

- Collect 689 exact Stage08 native HOLD timestamps, group by original site/year, prioritize years with more events.
- Get **exact original site BIF** `LOCATION_LAT`, `LOCATION_LONG`, `UTC_OFFSET`; abort rather than guessing if location or fixed LST offset ambiguous. FLUXNET reports local standard time (no DST), so UTC = native LST − published offset.
- Request `reanalysis-era5-land-timeseries` through CDS using `2m_temperature`, `2m_dewpoint_temperature` and `surface_pressure` for source site coordinates and each required year, with a small multi-day overlap either side. Download at most **3 missing site-years per invocation by default** (`--max-downloads` 1–5); repeat to get remaining years. Existing downloaded files are not overwritten. Every NetCDF/ZIP must pass CRC, exact hourly UTC coverage, source coordinate bounds, units K/K/Pa and dewpoint<=temperature sanity.
- Use gridded T/D2M ratio to derive **water-referenced RH**, linearly interpolate hourly gridded humidity to native half-hourly timestamps, then reconstruct `VPD=es_water(TA_F_tower)×(1-RH_grid/100)` at preserved site temperature. Preserve original PA_F, and refuse to repair if site temperature or pressure is grossly invalid, grid RH outside [1,100] or model physics invalid.
- For each run produce **two new complete native-length derived FLUXMET HH CSVs** (US-Rpf and US-SRM), a list of actually repaired timestamps/new RH/VPD, a separate remaining HOLD list, site-grid original and external SHA receipts and an `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker. Existing Stage07–09 remain intact.
- The site-year population and observed science repair count are **unknown until the first IRIDIS6 execution**. No claim of 689 successful repairs is made.

**Scientific caveat:** ERA5-Land grid (~0.1°) is a reanalysis source, not direct tower truth. Water-relative humidity differs from ice-relative humidity under freezing conditions; the calculated value is used in a **research candidate**, not automatically authorised model forcing. Annual climatology and episodic bias near a tower remain to be inspected before Post-v5 acceptance. The gridded point may be in a different elevation or land-cover context.

### Run

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/3d1d15e5a8d0c3403446fa67f0a9e32c4e2ea15d"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage10"
  SCRIPT="$BASE/scripts/stage10/10_era5land_independent_humidity_fill.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage10/10_era5land_independent_humidity_fill.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --run --max-downloads 3 2>&1 | tee "$BASE/stage10_run.log"
)
```

This makes at most three CDS requests per invocation. Users need a configured `~/.cdsapirc` and installed `cdsapi,numpy,netCDF4`. If the CDS returns a failed response, the partial file is kept and cannot be silently overwritten. When requests for all relevant years have downloaded and verified, rerun `--apply-existing` to make a new derived version with all available years and no network requests.

**No original source, DATM, CIME, case, Slurm or historical result modified by Stage10 code creation.** No successful operator execution of Stage10 has yet been reported.

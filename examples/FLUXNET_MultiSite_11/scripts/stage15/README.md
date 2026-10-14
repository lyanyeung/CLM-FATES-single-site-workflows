# FLUXNET_MultiSite_11 — Stage 15 provisional DATM with dynamic TA_F ZBOT

This code **follows** the eight-site experiment at `examples/FLUXNET_MultiSite_8/scripts/07_make_eight_site_datm_timevarying_zbot.py`, but uses the *eleven-site* versioned candidate CSVs and the corrected Stage13b BIF date parser. **It does not modify original source data or approved candidate forcing, and its generated DATM is explicitly PROVISIONAL, not approved for production spin-up.**

## User-approved missing-height policy (14 October 2026)

- Use the dated BIF `TA_F` history as ZBOT for all timestamps from the first effective date onwards.
- Prior to the first `TA_F` BIF date, hold the **first documented TA_F height constant backward to forcing start**. Mark those times as an *assumption*, not a historical measurement. No outside height search.
- Track `WS_F` independently for mismatches but **never** adjust the WIND column without an independent scientific choice. `CH-Aws` has no valid `WS_F` height, so keep WS unknown; never fabricate it. Missing WS height does not imply missing TA-derived ZBOT.
- A BIF `YYYYMMDD` date uses local midnight as the effective time. All time axes are site-local standard time (`NO_LEAP`), no DST correction.
- Keep an immutable, checksum-tracked height policy JSON. This policy is not an instrument metadata correction.

## Candidate tags

| Candidate tag | Sites |
| --- | --- |
| `v07a` | BE-Bra, FR-Fon, GL-ZaH, IT-Noe, AT-Neu, FI-Sod, CH-Cha |
| `pressure07a` | CH-Fru, CZ-Stn |
| `pressurelw08a` | CH-Lae |
| `landrh11a` | CH-Aws |

## Running on IRIDIS6

Requires `clm_fates_env` with `pandas`, `numpy`, `netCDF4`, and existing `~/FLUXNET_MultiSite_11/stage13b_ZBOT_policy_audit` results and unchanged BIF files.

```bash
conda activate clm_fates_env
set -o pipefail
cd ~/FLUXNET_MultiSite_11_stage15

# 1. Check original BIF hashes, Stage13b chronology, the earliest-height policy.
python 01_freeze_zbot_policy.py 2>&1 | tee ~/FLUXNET11_stage15_policy_preflight.log

# 2. Commit the user's explicit fixed-backfill height assumption to a NEW policy file.
python 01_freeze_zbot_policy.py --write-policy 2>&1 | tee ~/FLUXNET11_stage15_policy_write.log

# 3. Check source CSV SHA256, all NO_LEAP rows, 7 forcing fields, humidity, surface coords, ZBOT.
python 02_build_11_provisional_datm.py 2>&1 | tee ~/FLUXNET11_stage15_datm_preflight.log

# 4. Only if step 3 has all 11 PREFLIGHT_OK and 0 blocked sites,
#    write NEW, versioned yearly NetCDF test inputs. NOT production-approved.
python 02_build_11_provisional_datm.py --write-provisional \
  2>&1 | tee ~/FLUXNET11_stage15_datm_write.log

# 5. Independent audit of all annual NetCDF, time, units, source identity and per-step ZBOT.
python 03_verify_11_datm_readonly.py 2>&1 | tee ~/FLUXNET11_stage15_datm_audit.log
```

Expected 238 total annual files (sum of years across 11 sites) with exactly 17,520 half-hours each, no leap days. New output path:
`/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/datm_11_provisional_dynamic_zbot_v1/<SITE>_DATM_<YEAR>.nc`.

## Source units and conversions

- `TA_F` °C → `TBOT` K: `TA_F+273.15`.
- `PA_F` kPa → `PSRF` Pa: `PA_F*1000`.
- `VPD_F` hPa and `TA_F` → actual vapor pressure from saturation-over-water formula, then `QBOT` kg/kg with actual site pressure. Zero/negative vapor pressure **blocks** writing.
- `SW_IN_F` and `LW_IN_F` W/m² → `FSDS` and `FLDS` W/m².
- `WS_F` m/s → `WIND` m/s unchanged; no wind-height normalization.
- `P_F` mm per 30 min → `PRECTmms` mm/s: divide by 1800, per FLUXNET FULLSET HH variable definition. See https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ .
- Explicit preflight blocks negative `SW_IN_F` or `P_F` values rather than silently clipping them; earlier Stage03 numerical screens allowed small negative values. Handle any new blockers *separately and transparently*, never edit this script to ignore them blindly.

## Outstanding scientific decisions

A structural DATM pass is not a production science approval. Existing CH-Aws 559 ERA5-Land trial VPD records (33 high-disagreement) lack suitable winter tower confirmation. Gridded surface/PFT agricultural fractions may not represent tower footprints (especially BE-Bra, FR-Fon, CZ-Stn). Wind measurement height can differ from TA height (BE-Bra known +7m in documented overlap), without vertical correction. Long historical height backfills (e.g. 20+ yr) introduce model uncertainty. Site-by-site meteorological jumps/source switches/precipitation climatology still need review; use sensitivity runs where warranted.

## No-overwrite

The frozen height policy is created with exclusive mode. The DATM writer refuses existing site output directories and never modifies source CSV, BIF, original surface or original eight-site DATM. Only new `datm_11_provisional_dynamic_zbot_v1/` directories are written after an all-sites preflight. Audit tool never writes.

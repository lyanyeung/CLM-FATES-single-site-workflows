# Batch04 longwave science blocker — packaged FLUXNET ERA duplicates source error; independent ERA5-Land SYVH9

**2026-10-26 actual user IRIDIS6 operator log.** Previous SYVH7 `--assess` passed source SHA of all five original flux and paired ERA files (three Stage05: US-SP1/Syv/Ton, two Stage08: US-Slt/Uaf) and final ten-site research source manifest. It stopped at **US-SP1 2004-12-04 00:00** before any candidate writes.

## Observed failure and meaning

At US-SP1 native local-standard time:
- 2004-12-03 **23:00** and **23:30**: original/paired longwave `324.268 W/m²`, source `LW_IN_F_QC=2`.
- 2004-12-04 **00:00** and **00:30**: original `LW_IN_F =44.764 W/m²`, original `LW_IN_ERA=44.764 W/m²`, original `LW_IN_F_QC=2`.
- 2004-12-04 **01:00** and **01:30**: original and paired `328.392 W/m²`, source `LW_IN_F_QC=2`.

Thus the bad value is **already present in the original packaged FLUXNET ERA5-derived companion**. The earlier SYVH7 plan to replace native `LW_IN_F` with the SAME `LW_IN_ERA` has no corrective effect and correctly **failed closed**. Original files and all 297 Syv TA, 415 humidity, 18 RH-only approvals remained unchanged. Do **NOT** override this with a threshold change or replace the bad value with itself.

## Independent source to use

Copernicus ERA5-Land **hourly time-series** `reanalysis-era5-land-timeseries`, variable `surface_thermal_radiation_downwards` (`strd`), explicitly designated **de-accumulated** in CDS. Field units are hourly integrated `J m^-2`; `strd_Wm2 = strd_Jm2 / 3600` W/m²; do **not** divide an entire daily/forecast-step cumulative field by 3600 or assume a coincident instantaneous LW flux. Source references:
- <https://confluence.ecmwf.int/pages/viewpage.action?pageId=690470575> (official Product User Guide)
- <https://forum.ecmwf.int/t/new-variables-added-to-the-era5-and-era5-land-time-series-datasets-on-the-cds/14208> (the longwave variable added to CDS timeseries)
- <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries> (CDS dataset)

The original tower BIF supplies verified latitude, longitude and **UTC_OFFSET** (native local **standard** time, no DST). For a native half-hour beginning at local 00:00/00:30, the corresponding *hourly mean* ends at local 01:00; both native half-hours receive the one-hour-integrated `strd` divided by 3600. Use exact converted **UTC hourly-ending time**. This preserves the ERA5-Land hourly-integrated flux as two identical half-hour means and avoids half-hour interpolation inventions. Original source QC provenance is preserved in a separate ledger; newly ERA-filled candidate `LW_IN_F_QC=2` if such a field is present.

## New code: SYVH9 independent, source SHA- and UTC-locked, research only

[SYVH9 independently download and audit longwave 12 HH](../scripts/manual_review/stage_syvh9_independent_ERA5Land_12_low_LW_repair.py), pinned GitHub revision **`c56aa34056c2384487686573b2f2ce3e18737325`**, **committed but not yet run on IRIDIS6**.

It imports the unchanged, SHA-pinned existing [SYVH7](../scripts/manual_review/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py) source and full-file row-diff helpers, and the actual [SYVH5 and SYVH6](../scripts/manual_review/stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py) independent ten-site numerical Gate-0 reviewer. It never invokes the earlier SYVH7 `assess()` that failed because the paired longwave was contaminated.

1. `--self-test`: synthetic exact six-site-year/12-HH native source clock/hour-ending/deaccumulation check, no disk/CDS.
2. `--check`: original Stage05/08 native/processed ERA and ten-site SYVH3 SHA, exact 12 original source bad LW, paired ERA original provenance, unique BIF lat/lon/UTC offset, no candidate writes or downloads.
3. `--run`: requests only **six independent CDS site-year/windows**, not full 20+ years of raw data: US-SP1 2004 & 2016, US-Slt 2016, US-Syv/Ton/Uaf 2004. Each request is a narrow six-calendar-day `strd` time series near the anomaly, stored in isolated `reports/stage_SYVH9_independent_CDS_ERA5Land_longwave` directory with response SHA/units/grid/time/BIF receipt. Previously completed files are SHA-verified and reused, not overwritten. If partial CDS download is interrupted, script refuses to overwrite a leftover partial.
4. Before writing any derived met candidate, require finite deaccumulated `strd` with explicitly verified units `J m^-2`, exactly consecutive UTC hours and tower BIF grid coordinates; `60–700 W/m²` at all twelve candidate half-hours, no >180 W/m² transition to already-good native ±1HH, both HH map to a single independent UTC hourly mean. Failure stops without repairs.
5. Only after **all six independent site-year sources and 12 source native records pass**, create **five versioned full-length research CSVs** editing precisely 12 target `LW_IN_F` cells (and original `LW_IN_F_QC` to QC2 when that column exists), preserve original native source, prior SYVH3 Syv candidate SHA/297 T+415 VPD+18 RH science changes, and all ten other fields. Diff every old/new full file line by line, generate original/paired/independent source-provenance ledger and SHA-selected ten-site manifest.
6. Immediately reuse verified existing SYVH6 physical/NOLEAP checker on **all ten** selected final site sources. Expected numerical Gate-0 = **10/10** only if original source SHA/ERA location/time/field physics all pass. This does **not** approve Post-v5, DATM, CIME, ZBOT, surface/PFT or Slurm.

### One command, IRIDIS6 (no git pull)

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  OLD7="84c6c292ae8cda2064a8e349a80892f33328342f"
  OLD56="65ee7d0715d5f6ed5dc857214ea98a58fdf4d6f7"
  NEW9="c56aa34056c2384487686573b2f2ce3e18737325"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/$OLD7/$REL/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py" -o "$BASE/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py"
  for f in stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py; do
    curl -fLsS --retry 3 "$RAW/$OLD56/$REL/$f" -o "$BASE/$f"
  done
  SCRIPT="$BASE/stage_syvh9_independent_ERA5Land_12_low_LW_repair.py"
  curl -fLsS --retry 3 "$RAW/$NEW9/$REL/stage_syvh9_independent_ERA5Land_12_low_LW_repair.py" -o "$SCRIPT"
  python3 -B -m py_compile "$BASE"/stage_syvh{5,6,7,9}*.py
  python3 -u -B "$SCRIPT" --check 2>&1 | tee "$BASE/Batch04_SYVH9_12_LW_independent_source_check.log"
  python3 -u -B "$SCRIPT" --run 2>&1 | tee "$BASE/Batch04_SYVH9_12_LW_ERA5Land_research_apply_gate0.log"
)
```

**Actual status:** no independent CDS STRD results returned yet. Therefore no claim that these 12 points were repaired or ten-site Gate-0 revalidated. Any CDS API argument/unit/UTC location/source-boundary failure must be reported honestly; do not silently fall back to original low packaged ERA data. If the source evidence does not meet the requested physical/boundary conditions, a focused science judgement based on independent evidence will be needed. No model runs submitted.

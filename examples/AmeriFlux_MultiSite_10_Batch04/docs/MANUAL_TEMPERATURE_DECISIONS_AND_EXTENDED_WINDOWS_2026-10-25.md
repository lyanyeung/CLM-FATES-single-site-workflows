# Batch04 manual temperature review — user-directed alternatives, longer original windows

**2026-10-25 operator update:** The seven original temperature windows have now been **successfully executed/verified** on IRIDIS6: [expanded source observations and decisive four-day SP1 18:00 discontinuity](MANUAL_EXTENDED_T_OPERATOR_VERIFIED_2026-10-25.md). The first manual 3-point \`--assess\` failed in conda \`(base)\` due to missing NumPy. After \`conda activate clm_fates_env\`, the returned excerpt shows the script's self-test but not the final proposed temperatures; **exact assessment remains pending**. Original T/Stage14 remain intact. The commands below are preserved for reproduction.\n\n**Decision context (2026-10-25):** the operator explicitly requests a trial of (i) replacing the one isolated US-SRG 2019-03-19 12:00 value by interpolation of its flanking consolidated TA_F samples; and (ii) replacing US-SP1 2000-10-09 18:00/18:30 with the **exact independently receipt-verified ERA5-Land** temperatures. This is **not** permission to edit original FLUXNET/Stage14 or release production Post-v5 forcing. No code has yet been run on IRIDIS6 for this new request.

## Known source evidence and important label

| Site | Native local-standard timestamp | Original TA_F/QC | Comparison | Requested trial decision |
| --- | --- | --- | --- | --- |
| US-SRG | 2019-03-19 11:30 | 19.668°C / QC2 | TA_ERA =19.668°C | Earlier **ERA substituted** flank |
| US-SRG | 2019-03-19 12:00 | **0.718°C / QC0** | TA_ERA=20.399°C, independent ERA5-Land=18.865°C | **Interpolated TA_F (19.668+20.605)/2 = 20.1365°C, trial QC2** |
| US-SRG | 2019-03-19 12:30 | 20.605°C / QC2 | TA_ERA=20.605°C | Later **ERA substituted** flank |
| US-SP1 | 2000-10-09 17:30 | 11.000°C / QC0 | — | Retain |
| US-SP1 | 2000-10-09 18:00 | **−6.900°C / QC0** | ERA5-Land ~14.37°C from Stage15 source code comment (approximate only) | **EXACT ERA5-Land T2m at native timestamp, trial QC2** |
| US-SP1 | 2000-10-09 18:30 | **−7.100°C / QC0** | ERA5-Land ~13.78°C (approximate only) | **EXACT ERA5-Land T2m at native timestamp, trial QC2** |
| US-SP1 | 2000-10-09 19:00 | 17.545°C / QC1 | Filled, not independent measured TA | Retain |

**Critical limitation:** interpolation between the **two QC2** US-SRG neighbors yields **ERA-derived interpolated TA**, not independent raw tower truth. Do not mark it QC0 or treat the numerical result as validated. In the research alternative the new values have **trial QC2**, and the human-operator provenance ledger explicitly identifies their source. The original QC0 measurement remains available, unchanged, in the original/Stage14 files. **Do not delete the time row**; replace TA only within a separate complete half-hour continuous trial series, recalculating VPD to be thermodynamically consistent.

For US-SP1 2000-10-09 this proposed **ERA-only two-point scenario** is a separate experiment from **Stage15 tower-flank interpolation** (13.1816667°C and 15.3633333°C). Neither scenario is approved as measured tower truth or post-v5 forcing.

## Original source longer windows — read-only and no missing-temperature invention

[show_extended_native_temperature_windows_readonly.py](../scripts/manual_review/show_extended_native_temperature_windows_readonly.py) SHA-pins the original FLUXNET FLUXMET_HH files and prints original TA_F, QC, TA_F_MDS, TA_F_MDS_QC, TA_ERA, VPD_F, VPD_F_QC at **every 30 min** for:

| Site | Window | Why |
| --- | --- | --- |
| US-SP1 | 2007-10-15 05:00–21:00 | Includes >10 h **before 15:30**, plus sudden 17:30→18:00 +12.070°C rise |
| US-SP1 | 2007-10-16, 17, 18 each 08:00–20:00 | Review recurring midday low-vs-ERA episodes, one day at a time |
| US-SP1 | 2008-01-15 17:00–2008-01-17 14:00 | Covers both original Jan 16 temperatures and 22-h/13.5-h cold-vs-ERA episodes |
| US-SP1 | 2008-02-02 18:00–2008-02-04 12:00 | Covers 19-HH overnight discrepancy spanning Feb 2–3 |
| US-Seg | 2016-12-27 15:00–2016-12-28 10:00 | Explicitly shows **after 20:00**, with continuous original QC and TA_ERA |

This display script uses **original FLUXNET TA_ERA**, not the separately downloaded ERA5-Land grid. The exact independent ERA5-Land temperature is evaluated only for the 2000 trial decisions by the second script. No raw new 2007/2008/2016 half-hours outside earlier Stage17/18/19 printouts have yet been provided, so those exact numbers should **not be guessed** until the new read-only command returns.

### Run the read-only extended windows on IRIDIS6

~~~bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  NEW="adf6a8c00786110e151f080e382466a39e92f64a"
  mkdir -p "$BASE"
  SCRIPT="$BASE/show_extended_native_temperature_windows_readonly.py"
  curl -fLsS --retry 3 "$RAW/$NEW/$REL/show_extended_native_temperature_windows_readonly.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --inspect 2>&1 | tee "$BASE/extended_original_halfhour_temperatures.log"
)
~~~

## Build exactly three **trial-only** operator-proposed temperature changes

[build_manual_T_replacement_trial_only.py](../scripts/manual_review/build_manual_T_replacement_trial_only.py) source commit \`89cf6094982f7fdb0f7771555a4b94b6ba61d4a1\`. Downloads the previously verified Stage10 helper (not CDS records) to **read and SHA-verify already available existing ERA5-Land 2000 data**, interpolate hourly ERA5-Land T2m to original FLUXNET local-standard UTC time, and recompute VPD from the retained Stage14 RH values after each trial TA replacement. It generates 2 new complete research CSVs (US-SRG one edit and US-SP1 two edits), 10-site research manifest, a per-event full provenance ledger, a SHA receipt and an explicit no-model-use marker **only when --trial is called**; \`--assess\` makes no write. Other eight site paths and checksums retain Stage14 manifest values.

~~~bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts"
  NEW="89cf6094982f7fdb0f7771555a4b94b6ba61d4a1"
  OLD="9be06860ee3e9f14e08fb078d22d0090b49d58d4"
  mkdir -p "$BASE"
  SCRIPT="$BASE/build_manual_T_replacement_trial_only.py"
  curl -fLsS --retry 3 "$RAW/$NEW/$REL/manual_review/build_manual_T_replacement_trial_only.py" -o "$SCRIPT"
  curl -fLsS --retry 3 "$RAW/$OLD/$REL/stage10/10_era5land_independent_humidity_fill.py" \
    -o "$BASE/10_era5land_independent_humidity_fill.py"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --assess 2>&1 | tee "$BASE/manual_three_T_changes_assess.log"

  # Optionally CREATE ONE NEW trial after inspecting the exact --assess values:
  # python3 -B "$SCRIPT" --trial 2>&1 | tee "$BASE/manual_three_T_changes_trial.log"
)
~~~

**Scope guard:** Keep the last \`--trial\` line commented out until the operator has reviewed the exact three proposed temperatures, original QC and VPD/RH closure printed by \`--assess\`. The user's intended intervention is captured; only the entirely new independent research-alternative output will be written on explicit --trial invocation. No original/Stage14/Stage15 inputs are overwritten and no Post-v5, DATM/CIME or Slurm jobs are submitted. The original eight scientific source validity questions remain open, even though a *manual experimental alternative* is available.

## US-SP1 elevation question

The official AmeriFlux station page lists **50 m above sea level**, latitude 29.7381, longitude −82.2188, Florida (humid subtropical site). This low elevation makes an ordinary tower-versus-grid height lapse-rate correction an implausible explanation for a 10–20°C offset, but **ERA5-Land actual gridded surface elevation was not checked** by Stage17/20/21, so do not claim measured grid elevation agreement. Official site: https://ameriflux.lbl.gov/sites/siteinfo/US-SP1. Check height of specific air-temperature instrument versus 2-m gridded T as separate, unverified representativeness question.

**Next:** provide the two operator logs; before changing 2007/2008 or US-Seg native TA, first review extended source time series. Preserve 8 original temperature science HOLDs plus US-Syv 606 old HOLDs and 10 skipped Stage07 ERA endpoints.

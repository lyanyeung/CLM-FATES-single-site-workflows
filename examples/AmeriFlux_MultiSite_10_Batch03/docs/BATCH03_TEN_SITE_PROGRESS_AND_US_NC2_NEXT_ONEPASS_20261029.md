# AmeriFlux Batch03 — ten-site progress and one-pass US-NC2 next task

Prepared 2026-10-29 after **actual IRIDIS6 successful US-MMS Stage14C, US-MtB MtB04 and US-Mpj Stage14D**. This status separates numerical completeness from scientific model readiness, and older general ten-site snapshots from newer individual operator results.

## Numerical repair progress

| Site | Last verified or reported research-only missing source meteorology | Follow-up |
|---|---:|---|
| US-MMS | **0**, 219000 native HOURLY, Stage14C user output successful | Low-confidence source scenarios; no Post-v5/DATM |
| US-MtB | **0**, 280320 native HH, Claude MtB04 SHA-verified user run | 2668 COMPANION_E only 12/15 year-gate passes, 57 out-of-regime and 10 DATM saturation; not independent measured truth |
| US-Mpj | **0**, 315360 HH, Stage13O then actual Stage14D whole met closure passed | 610 low water RH warnings and 3791 ice-relative >100% warnings; do not bulk-clip; PFT/ZBOT/DATM still pending |
| US-MOz | **0** historically fully finite selected candidate; Stage13L approved 40HH applied | original **first 27 Jan2005 QC1 source episode** retained as scientific HOLD despite finite numerics, plus 2005 Jan09 source and ZBOT/surface |
| US-NC2 | **0** historically finite model-source/Stage11L | 13 original VPD source review cases, 2025 March four suspect boundaries, one 2019 original T event, source clock/BIF, PFT; Stage11Q actual run not yet confirmed in consulted GitHub note |
| US-Kon | **77 HH** latest Stage12AY research successor; not a new global cohort count | outstanding source QC/event humidity |
| US-Me6 | **45 HH** latest Stage13AI (19 winter + 26 other) | 2026-10-29 delegated new Claude scientific workstream |
| US-NR1 | **234 HH** after actual Stage13P | delegated new Claude scientific workstream |
| US-NR3 | **238 HH** signed older Stage12G | reserved for separate advanced reasoning model |
| US-Me2 | **unestablished comparable 21-year full selected source**, source 4 clock-border humidity events, fire/land/2020 | source input construction/validation rather than reporting 0 or an invented gap count |

**Count:** 5 sites have zero known missing meteorology in their recent selected/research numerical source; four other sites have quantified humidity gaps; one site (US-Me2) still lacks a comparable fully audited numerical time-series. Therefore **5 of 10 need further numerical gap closure or input construction**. In addition several numerically full sites still have science warnings, thus **0/10 currently verified full Post-v5 → DATM → AD400 admitted from this project**.

## Next easiest *science* target: US-NC2 (not repeat US-Mpj)

Existing source versions:
- Original native release `AMF_US-NC2_FLUXNET_2005-2025_v1.3_r1`; original FLUXMET/paired ERA SHA source via `qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json`.
- Stage11L actual signed research site `science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e/US-NC2_humidity_only_new_shadow_NOLEAP.csv`; 367920 native 30min rows, 11 user-approved additional 2025 RH candidate timestamps, two original source-preserve values.
- Stage11Q code proposes 9 more source RH reanalysis candidates. The 2026-10-24 documentation does **NOT** confirm successful actual IRIDIS6 Stage11Q generation. New site audit must choose actual version based on SHA receipt; do not claim Stage11Q applied without file. Both are research-only and do not approve a clock shift, production/model job.
- Official BIF original `UTC_OFFSET=-5` US-NC2; may be local standard clock, DO NOT interpret as automatically accepted data UTC or apply daylight saving/offset tuning.
- Four source-native March2025 transitions require joint provenance at 2025-03-18 18:00/18:30; 03-23 08:30/09:00; 03-23 15:00/15:30; 03-25 10:00/10:30. Previous Stage11L edge jumps 4.9971, 9.4674, 4.8127, 5.8593 hPa, respectively. Stage11Q might alter some; compare actual receipt and source values. Original QC1/QC2 is not independent measured humidity; source complete numerics does not close these science anomalies.
- Original source 2019 measured QC0 temperature event is already an operator-selected Stage07 interpolation, preserve original and corrected variants.

[Single-run US-NC2 Stage14E, source SHA signed read-only native QA](../scripts/stage14/14e_US_NC2_next_onepass_site_march2025_QC_READONLY.py). **Not executed on IRIDIS6 as of this file creation.** It chooses Stage11Q only if a complete single receipt and source SHA exist, else signed Stage11L. Reuses original raw tower/ERA source, audits all 367920 numeric rows and emits grouped 2025-03-18/23/25 raw source values and both QC flags, Q/VPD physics, nearest event transitions, 21-year RH/ice warnings and original source confidence. All output goes into a **new reports** folder, no selected forcing, original tower, PFT, case or Slurm change.

**Efficient next human decision:** after one run, give a single decision covering all four 2025 boundary groups. Preserve published original UTC−5 unless a separate actual source clock method is proven; do not invent new observed tower VPD truth or globally force smooth VPD. Separate research-numeric completion from final DATM & land-cover admission.

Operator copy/paste (pinned original SHA will be supplied in chat):

```bash
python3 -B US_NC2_onepass.py --run
```

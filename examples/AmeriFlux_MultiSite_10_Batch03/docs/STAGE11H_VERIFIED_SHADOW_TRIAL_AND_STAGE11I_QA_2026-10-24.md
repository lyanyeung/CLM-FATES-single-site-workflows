# AmeriFlux Batch03 — Stage11h verified unapproved science trial and Stage11i impact audit

**Verified on IRIDIS6:** 2026-10-24. User-supplied terminal output shows `PYTHON SYNTAX PASS`, Stage11h `--self-test PASS`, `--check PASS`, and `--run PASS`. **This is NOT a Post-v5 approved forcing release.**

## Exact Stage11h shadow trial location

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd/`

**Contents:** three separate SHA-sealed full-site NO_LEAP CSVs, 62-event delta provenance, the three-site summary and `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP`. Stage07 source and processed_v5 are preserved. Source method is the release-paired **FLUXNET site-downscaled companion ERA5 RH transferred to retained Stage07 site air temperature**, with VPD and QBOT recomputed. This trial did NOT use independent ERA5-Land gridded dewpoint.

| Site | NO_LEAP half-hours | User-selected ERA5 RH times | Actually different VPD values | Max absolute VPD change from Stage07 (hPa) | Max adjacent shadow VPD jump (hPa) | Minimum full-site shadow RH (%) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| US-MOz | 315,360 | 0 | 0 | 0 | 0 reported for eligible change windows | 2.206422 |
| US-Mpj | 315,360 | 4 | 2 | 2.286140 | 7.230951 | 1.168592 |
| US-NC2 | 367,920 | 49 | 41 | 9.761132 | 9.761132 | 1.439602 |
| **Total** | **998,640** | **53** | **43** | — | — | — |

The original user decisions are exactly **six KEEP existing Stage07 TA**, **53 ERA RH reconstruct VPD/QBOT**, **three KEEP existing Stage07 VPD**. Ten ERA-RH reconstruction event values did not differ from Stage07 within comparison tolerance. That does not imply skipped events.

**Important distinction:** Stage11h's `max_adjacent_trial_VPD_jump_hPa` reflects an absolute adjacent difference in the shadow product. It does *not* establish what portion of that jump was newly introduced versus already present in Stage07. A 7.23 or 9.76 hPa adjacent jump could be a continuity concern; no weather-accuracy conclusion can be drawn without comparing original and shadow jump magnitudes.

## Next independent Stage11i analysis — committed, not yet run on IRIDIS6

[11i_three_site_shadow_impact_audit.py](../scripts/stage11/11i_three_site_shadow_impact_audit.py) reads the exact SHA-sealed Stage11h folder and original Stage07 processed_v5 forcing in **read-only mode**. It checks:
- Full 998,640 native half-hour records, no leap day and preserved clock strings.
- All Stage07 and Stage11h receipt checksums and all six/53/three event choices, with 43 changed VPD values.
- Non-selected columns, non-selected timestamps, all six candidate TA and three VPD KEEP records must be identical numerically (allowing only tiny CSV float serialization differences).
- Mathematical closure of water-phase RH and QBOT over the **entire three-site series**.
- For each selected VPD event, the original adjacent half-hour VPD jump versus the shadow jump; reports the **newly added difference**, not only total jump.
- Annual mean VPD, RH and QBOT differences for every site-year, and year-specific changed-row counts.

`--self-test` uses synthetic figures. `--check` performs the complete audit with no writes. `--run` creates only a new `reports/stage11i_independent_shadow_impact_*` folder containing review tables and an SHA receipt, **no forcing writes, DATM or Slurm jobs**.

Stage11i cannot independently establish grid-to-tower height/elevation representativeness, native clock alignment or true tower humidity quality. Complete Post-v5 approval still requires these, source instrumentation/uncertainty, PFT/surface and CO2 protocol checks and a distinct formally reviewed model setup.

## Remaining Batch03 scope and status

- Three science-trial sites: 62/62 human review *directions* recorded; 53/53 ERA source RH transfers numerically feasible, 43 actual changes in new research-only trial.
- Seven other Batch03 stations remain scientifically held with 1,924 source humidity issues (Stage11a routes).
- Formal scientific Post-v5 sites = **0**; DATM-ready sites = **0**; spinup authorized = **0**.
- Never clear the Stage07 or Stage11h `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` markers on the basis of these test runs.

Evidence: the operator-provided Stage11h full execution log and sealed trial/report data on IRIDIS6.

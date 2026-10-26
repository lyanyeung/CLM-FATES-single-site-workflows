# Stage106 operator PASS → Stage107 GLE cyclic-year source-only comparison

Stage106 user-run (26 October 2026) PASS: 16/16 UTC-midpoint NC, true-dated 14 ERA 2004 local half-hour records replace artificial 2020 cyclic surrogate; other 280306 source time positions unchanged. Source report: stage106_GLE_ERA_2004LST_14HH_backfilled_UTCmid_16NC_20261026T125959Z_bfa2ba7f.

Internal 2005 Jan1 07:15 UTC boundary improved: pressure |delta| 665→30 Pa, temperature 4.332→2.423 K, wind 2.823→1.593 m/s; however the *real cycle* 2020→2005 source boundary now has pressure 259 Pa, temperature 3.877 K, wind 4.617 m/s. The old periodic edge's tiny jumps were due to the Dec2020 surrogate, not genuine climatological continuity. Humidity RH Jan1 internal jump increased to 9.42 percentage points and should be flagged, though physically valid source range passed.

Stage107 source-only no-modification script:
https://github.com/lyanyeung/CLM-FATES-single-site-workflows/blob/main/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage107/107_GLE_spinup_cycle_year_window_selection_readonly.py

Pinned raw commit ae83d3f11357d59c53072ebca25b0fcbd4ed17ca; Git blob bde14e0ff4fa85405c137c2909e69b87377f403d.

It SHA-checks all sixteen Stage106 source annual NC, original Stage102 receipt and no-production science HOLD; scans all 28 **contiguous 10–16-year** windows in the original 2005–2020 forcing. Reports each cycle-edge 8-field jump versus native 30-min P99 T/P/W variability. Reports cost of dropping years: changes in mean air temperature, precipitation and shortwave climatology. Full original 2005–2020 stays intact for the once-through historical transient model period; ranking is not automatic permission to shorten spinup forcing. No ERA overwrites, new forcing, CIME modifications or jobs.

CTSM DATM `taxmode=cycle` repeats data after stream end; `tintalgo=linear` cannot guarantee meteorological seam continuity. See https://escomp.github.io/CTSM/users_guide/setting-up-and-running-a-case/customizing-the-datm-namelist.html

Scientific holds after this step: chosen year window must retain representative climate/extremes and spruce beetle disturbance conditions; independently map BIF ENF 85% Engelmann spruce, 15% subalpine fir species shares versus site footprint/CTSM crop 7.514%; single model Sa_z 23.4m TA versus 22.65m wind; single-step actual CIME forcing data-read smoke test. DO NOT start long spinup from these reports.

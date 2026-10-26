# AmeriFlux Batch05 Stage40 — original source RH physical test on 16 method×episode science pilots

## Original Stage39 IRIDIS6 execution — proven

Stage39 source verified, self-test passed and scientific read-only execution completed at `/home/ly3n24/ameriflux_batch05_stage39/actual_shortlist_20261026T175318Z_1490492` on 26 October 2026.

- Stage38: **669** original method×episode tests (not 669 native HH), of which **16** pass *numerical screen*.
- Stage39: **16** methods, **15 distinct source events**, **14 unique-method research pilots** comprising **20 original native HH**, one original episode (`US-Var_E0017`) has two candidate methods.
- `US-Var_E0017`, original 2015-08-20 04:30: `SOURCE_MDS_ALL_EPISODE` changes original VPD **0 hPa**; `SOURCE_ERA_ALL_EPISODE` changes it **12.431942 hPa**. This is not a demonstrated observationally justified choice. Conserve the source in the production dataset (still unapproved original P2/P3) until source humidity provenance is examined; do not write the ERA trial to forcing.
- Other original event research trials can change original VPD greatly despite no new screened 2/4hPa jump: `US-Var_E0019` **12.725755 hPa**, `US-Var_E0033` **18.229752 hPa**, `US-Vcp_E0172` **11.486768 hPa**, and more. **Numerical continuity does not prove meteorological accuracy.**
- Proven site pilot counts: US-Var 5 native HH, US-Vcp 11, US-WCr 2, US-Wkg 2. No new true forcing admissions; **0/10 fully scientifically passed**.
- 46 original P1 manually HELD, 10 suspected RH saturation HH, 166 existing approved source overlay, **1574 original P2/P3 still unapproved** and production DATM/CIME/Slurm unchanged.
- US-UMB original FLUXMET_HH data are not identified in the 13 ZIP/CSV candidate files beneath its source-site root; this is **original source acquisition/provenance**, not operator permission to invent humidity data.

## Stage40: immediately resolve what actually needs human science decisions

[Stage40 code](../scripts/stage40/40_original_humidity_physics_and_real_manual_decision_priorities.py). Source commit pinned `6ae6899e00586fcfbfabe6924418263f7ff8a19c`, git blob SHA `6aa37fee2a4d3ed9c2726b0cc855ba6f06d9c099`.

[Stage40 one-click launcher](../scripts/stage40/run_stage40_iridis6.sh), source commit pinned `e27657e3806040b3c98aa2ae9cb482abc5a64d40`, git blob SHA `74936b1d602e1881e8ee16945172008496de20fc`.

Reads only ACTUAL Stage39 and Stage38 original operator outputs and the source-original Stage27 1574 native P2/P3 rows. For every half-hour in all 16 Stage39 methods it reconstructs native original RH over liquid water from *original selected tower T and original selected VPD* as `100*(1-VPD_original/esw(T_original))`, reports physically impossible RH <0%/>100%, original RH<5/<10%, source processed ERA/MDS RH difference, trial VPD and original-trial absolute delta, original tower QC. It clearly distinguishes a numerically smooth 18 hPa proposed change from genuinely validated humidity.

Science review lane ordering: original RH physically impossible; method ambiguity; original RH extreme / trial >10hPa; trial >5hPa; moderate 2–5hPa; small delta but still unapproved. One ambiguous method for the same source episode receives a method-choice HOLD. **Never treat MDS no-change as a repair**; when source is physical-impossible, the no-change option cannot be a solution.

Also opens the actual Stage39 US-UMB source-file inventory CSV to print the 13 real archive/CSV paths, ZIP member names and SHAs — not filenames guessed from folder dates.

Outputs in new report directory:
- `stage40_EXACT16_EVENT_SOURCE_HUMIDITY_PHYSICS_AND_SCIENCE_DECISION.csv`
- `stage40_ALL_NATIVE_OPTIONS_ORIGINAL_RH_ERA_MDS_VPD_TRIAL.csv`
- `stage40_US_UMB_13_EXISTING_ARCHIVE_NAMES_AND_MEMBERS.csv`
- `STAGE40_TRUE_HUMAN_REVIEW_AND_SAFE_PILOT_QUEUE.md`
- `stage40_manifest.json`

## IRIDIS6 one-click operator command

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/e27657e3806040b3c98aa2ae9cb482abc5a64d40/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage40/run_stage40_iridis6.sh" -o "$HOME/run_stage40.sh"
test "$(git hash-object "$HOME/run_stage40.sh")" = "74936b1d602e1881e8ee16945172008496de20fc"
bash "$HOME/run_stage40.sh"
```

**Stage40 source published; IRIDIS6 operator execution not yet confirmed.** No new scientific approvals or forcing files. User attention only after the original RH and event-method source discrepancies are shown.

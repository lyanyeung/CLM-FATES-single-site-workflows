# NL-Loo fixed-biogeography, no-competition FATES experiment

**Executable controller is maintained in a separate repository:** [Non-Competition-CLM-experiment](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/scripts/09_NL_Loo_V3_auto550.py). Do not copy controller logic here or launch from an outdated duplicate.

## V3 model sequence

- PRE50: normal mode, model 1997–2047 (50 years). On 2026-10-23 the final archived checkpoint `2047-01-01-00000` and successful model/archiver messages were reported.
- AD200: accelerated decomposition, model 2047–2247 (200 years), 5-year CIME segments.
- POST300: normal mode, model 2247–2547 (300 years), 5-year segments.

The watcher originally failed because `myfiles` was unavailable on a compute node (watch job 4671340). PRE50 itself completed. The controlled AD200 recovery entrypoint lives in the controller source above.

## Recovery from the existing PRE50 checkpoint

From a **login node**, in `~/Non-Competition-CLM-experiment`:

```bash
git pull --ff-only origin main
python3 -m py_compile scripts/09_NL_Loo_V3_auto550.py
python3 scripts/09_NL_Loo_V3_auto550.py status
command -v myfiles && myfiles
python3 scripts/09_NL_Loo_V3_auto550.py resume-ad200 --confirm RESUME_NL_LOO_V3_AD200_FROM_2047
```

The recovery checks controller state, PRE50 archive/checkpoint and spinup_state, the science configuration, and scratch inode quota before creating the AD200 case. It refuses to overwrite existing AD200 artifacts. It submits only the AD200 first **5-year** segment, then arranges a watcher; the remaining 195 years require a verified 2052 restart. DO NOT re-run `launch` or submit a duplicate model case. Compute nodes rely on a recently verified (under 24 hours) login-node inode receipt; update it from the login node if the automatic watcher stops due to expiry.

**Scientific caution:** Hybrid restart from normal spin-up to accelerated decomposition and back is not yet proven on this exact CTSM/FATES build. A successful 2052 checkpoint is a smoke test, not full scientific validation. Verify mode, restart metadata, model health, and carbon pools before treating the trajectory as valid.

Runtime files/restarts remain in IRIDIS scratch; none are committed to GitHub.

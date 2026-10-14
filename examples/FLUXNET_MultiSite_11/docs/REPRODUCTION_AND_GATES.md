# Reproduction, selected inputs, and scientific gates

**The eleven-site scripts are archival snapshots of the actual Stage02–11 code**. They assume the original site packages (not in Git), `clm_fates_env`, and the IRIDIS6 layout. Most code references `~/FLUXNET_MultiSite_11_stageXX` only in shell invocation; their file bodies are preserved in this example under `scripts/stageXX/`.

## Reproduction order (a new independent run)

1. Verify licensing, source versions, extracted raw HH files and 11 point surfaces. Model year ranges are in `scripts/stage03/01_merge_11_source_aware.py`. **Do not regenerate existing production data by overwriting paths.**
2. Run Stage03 baseline `01_merge_11_source_aware.py` without write for an audit; then `--write-candidates --tag <newtag>` for new versioned candidates. Historical completed baseline tag: `v07a`.
3. Surface PFT read-only audit: `scripts/stage04/00_reaudit_surface.py`. Do not use `scripts/historical_DO_NOT_USE/02_old_surface_pft_16class_bug.py` except to reproduce the old error.
4. Run Stage04–06 investigation scripts and review each event by original QC, independent reference and nearest time neighbors; pressure proposals must be produced on the right raw versions. The pressure proposal CSV is NOT embedded here.
5. Stage07 `01_pressure_trial_and_audit.py --source-tag v07a` (preflight) and then `--trial-tag pressure07a --write-trial` only when the original record-level evidence is reproduced and a **new absent destination directory** is selected. In existing cases, **do not rerun writes**.
6. Stage08 `01_CHLae_LW_trial.py` requires the exact CH-Lae pressure-trial input and 2004-12-04 two-point event evidence; writes `pressurelw08a` only once if absent.
7. Stage09 `01_CH_Aws_dewpoint_reference.py fetch`, then `assess --site-utc-offset-hours 1`. The Open-Meteo historical dataset is a moving upstream dependency; cache all response metadata and keep downloaded JSON out of Git. Keep UTC+0 calculations as sensitivity rather than redefining official station time.
8. Stage10 validation then Stage11 **read-only preflight**. Stage11 writes the versioned `landrh11a` only after exact fingerprint, count, event alignment, model agreement and numerical consistency checks; do not rerun into existing directories.
9. Run `scripts/12_verify_selected_trial_manifest.py` on current site folders to check expected tag selection, exact half-hour count, variable constraints and SHA256 of each selected output. The snapshot's `v07a` + three pressure tags + one LW tag + one humidity tag is **not** a joint input manifest stored in the original stage03 summary.

## Science/QC gates still open

- **Meteorological science QC gate:** station-by-station physical and temporal inspection of all seven meteorological drivers, sensor history, annual precipitation and source switches. Do not equate `CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW` with approved.
- **High-alpine CH-Aws gate:** 559 model-based RH changes, including 33 high-disagreement, and zero winter observations with suitable QC flags. ERA5-Land is a *prioritized estimate*, not independently proven correct. Evaluate alternative dewpoint/ice-saturation methods or external in-situ winter humidity data and uncertainty.
- **Surface/PFT gate:** 15-element `PCT_NAT_PFT` is structurally acceptable. Unusually high gridded `PCT_CROP` in forest station grid cells must be reviewed against site footprints, not simply ignored.
- **BIF/ZBOT gate:** dated heights and model measurement height consistency required for all 11 sites (as in eight-site `07_make_eight_site_datm_timevarying_zbot.py`). No final 11-site ZBOT/annual DATM script is included as completed.
- **Independent DATM gate:** only after earlier science review, write a model forcing NetCDF with `NO_LEAP` 17,520 half-hours/year and verify coordinates/time bounds/field units/physical checks; leave existing archives unchanged.
- **Spin-up gate:** 500-model-year runs, restart checks and convergence depend on physically credible final forcing, surfaces and model setup. This repository entry does **not** assert any eleven-site spin-up started or completed.

## No data in git

`.gitignore` excludes CSV, NetCDF, ZIP, JSON, caches and output folders to reduce accidental publication of licensed data. For this experiment upload only `README.md`, Markdown science decisions, and `.py`/`.sh` code. Never publish downloaded reanalysis JSON, site raw tables, corrected candidate tables, source-package archives, debug logs, machine tokens or model outputs. Consult network terms and attribution before distributing any result derived from site observations.


## Status update: Stage13b–15 completed; Stage16 read-only final check

The earlier section saying no 11-site DATM exists is a historical state, superseded by this dated update. As confirmed by IRIDIS6 logs on 2026-10-14:

- Stage13b correctly parsed eight- and twelve-digit BIF dates and corrected erroneous counts of undocumented heights; Stage14 inventory found duplicates across BIF resolution products but no earlier height dates.
- The user explicitly chose first-documented TA_F height held constant backwards before that BIF date; later height changes follow BIF dates. WS_F heights are diagnostics only; WIND remains unadjusted; CH-Aws WS_F is unknown.
- Stage15 height policy was written at `~/FLUXNET_MultiSite_11/stage15_provisional_DATM/height_policy_v1.json` with SHA256 `4eff9273d6aa73bc71f4b6104470b9189fb3d5491ea2393698564720f6764068`.
- CH-Fru/CZ-Stn Stage07 uses `trial_sha256`, so the Stage15 DATM writer must use the compatible checksum verification without bypassing it. Stage15 preflight passed 11/11 and wrote 238 **PROVISIONAL** annual DATM files. Independent audit verified 238/238. 11/11 site `user_nl_clm` paths exist; the GF-Guy source case directory exists.
- **Stage16 pre-spinup inspection (no case clone/build/submit)** needs to run on the IRIDIS6 copy of the scripts. This is a technical file/reference check, *not* a science approval.
- Large gridded crop percentages: FR-Fon 50.8%, CZ-Stn 47.8%, BE-Bra 37.4%, IT-Noe 30.5%, CH-Cha/CH-Lae 22.2%. Some natural-PFT vectors are dominated by grass or bare-ground indices; do not assert a forest site has forest-appropriate surface merely because a NetCDF has 15 PFT entries. Interpret PFT indices using actual NetCDF coordinate conventions, not a guessed 16-PFT mapping.
- CH-Aws 559 winter modeled humidity replacements remain scientifically uncertain, including 33 cases of >15 percentage-point ERA5 vs ERA5-Land disagreement.

See [BIF/ZBOT documentation](BIF_DYNAMIC_ZBOT_STAGE13_15.md), `scripts/stage13b/`, `scripts/stage14/`, `scripts/stage15/` and `scripts/stage16/`.

**Model run status: NOT STARTED. Do not submit 500-year spin-up until scientific and case configuration reviews are completed.**

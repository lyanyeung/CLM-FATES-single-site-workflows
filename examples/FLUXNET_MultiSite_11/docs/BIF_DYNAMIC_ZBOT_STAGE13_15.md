# Dated BIF TA_F heights, early fixed backfill and dynamic ZBOT (11 sites)

**Experiment snapshot: 2026-10-14.** The user explicitly authorized: where earlier TA_F/WS_F BIF heights are undocumented, retain the first documented height *backward* as a constant assumption. This is not a historical instrument measurement. Stage15 produced 238 PROVISIONAL annual DATM NetCDFs; independent audit returned **238/238 STRUCTURE_OK_SCIENCE_REVIEW**. No 500-year spin-up was submitted.

## Scientific distinction

- FLUXNET BIF `VAR_INFO_VARNAME=TA_F`, `VAR_INFO_HEIGHT`, `VAR_INFO_DATE` describe the TA measurement height. **DATM ZBOT is derived from the dated TA_F height history**, not the eddy-covariance sonic/anemometer measurement height and not automatically the WS sensor height.
- At/after each documented BIF effective date, ZBOT equals its most recent documented TA height (piecewise constant). Before the earliest recorded date, use that first known TA height, **only because the user explicitly accepted this model assumption** on 2026-10-14.
- `WS_F` heights are tracked and independently backfilled *for diagnostic comparison only*. `WIND` is not vertically normalized to `ZBOT`. CH-Aws has **no valid WS_F height**; retain unknown and never invent a value.
- BIF dates of format `YYYYMMDD` are interpreted as local-standard midnight (precision explicitly flagged); `YYYYMMDDHHMM` preserves recorded minutes. No DST conversion; source forcing timestamps are model NO_LEAP local-standard half hours.
- HH/DD/MM/WW/YY BIF files often repeat the same VAR_INFO records; multiple duplicate product files are not independent evidence of historical height continuity.
- The first Stage13 parser erroneously required 12-digit timestamps, causing FR-Fon, FI-Sod, CH-Aws, CH-Fru heights to appear missing; Stage13b corrected this. The original incorrect script is retained only as a historical, DO-NOT-USE artifact.
- Stage13 initially counted BE-Bra's TA-vs-WS 7-m height difference across periods where both heights had been extrapolated. Stage13b correctly reports **100,368 half-hour periods of documented TA/WS overlap with >3m mismatch**; earlier times are assumptions, not observed overlap.

## Exactly recorded histories and approved early backfills

The `early TA` counts are the number of **NO_LEAP** half-hour records earlier than the first TA BIF date. Year ranges and candidate tags were frozen in Stage15's `height_policy_v1.json`; hash reported by IRIDIS6: `4eff9273d6aa73bc71f4b6104470b9189fb3d5491ea2393698564720f6764068`. Do not publish the full locally generated JSON: it includes filesystem paths and source manifests.

| Site | Forcing years | TA first height/date | Early TA half-hours | WS first height/date | WS issue |
| --- | --- | --- | ---: | --- | --- |
| BE-Bra | 1996–2025 | 32.2 m · 2016-12-19 00:00 | 367,296 | 39.2 m · 2020-04-10 00:00 | TA/WS known overlap differs by 7 m |
| FR-Fon | 2005–2025 | 37.0 m · 2019-10-28 (date only) | 259,680 | 37.0 m · 2019-10-28 | early backfill assumed |
| GL-ZaH | 2000–2025 | 2.0 m · 2020-01-01 00:30 | 350,401 | 3.0 m · same date | early backfill assumed |
| IT-Noe | 2004–2025 | 1.6 m · 2022-01-01 00:30 | 315,361 | 3.6 m · same date | early backfill assumed |
| AT-Neu | 2002–2020 | 2.5 m · 2002-01-01 | 0 | 2.5 m · 2001-03-01 | fully documented TA period |
| FI-Sod | 2001–2025 | 25.1 m · 2023-04-20 (date only) | 390,672 | 25.1 m · same date | decades-long assumption |
| CH-Aws | 2006–2024 | 1.5 m · 2022-09-15 (date only) | 292,656 | **unknown** | no valid WS BIF height |
| CH-Cha | 2005–2024 | 2.0 m · 2005-09-01 | 11,664 | 2.41 m · 2005-01-01 | early TA backfill assumed |
| CH-Fru | 2005–2024 | 2.0 m · 2005-01-01 (date only) | 0 | 2.55 m · same date | TA fully covered |
| CH-Lae | 2004–2024 | 47.0 m · 2004-01-01 | 0 | 47.0 m · 2004-03-30 | early WS diagnostic backfill |
| CZ-Stn | 2010–2024 | 44.0 m · 2009-03-11 | 0 | 44.0 m · 2010-01-01; 2015-04-21 | two WS events, same height |

**Important:** Forcing starts well before recorded height for BE-Bra, FR-Fon, GL-ZaH, IT-Noe, FI-Sod and CH-Aws. Keeping first known height constant does **not** show that equipment actually remained unchanged. Consider sensitivity to assumed measurement height in future scientific analysis.

## Stage15 conversion and per-file provenance

- `TA_F` °C → `TBOT=TA_F+273.15` K; `PA_F` kPa → `PSRF=PA_F×1000` Pa.
- `QBOT` is derived from `TA_F`, `VPD_F` hPa, and `PA_F` via vapor pressure and specific-humidity relations; physical consistency is checked before writing.
- `SW_IN_F`/`LW_IN_F` W m⁻² → `FSDS`/`FLDS`; `WS_F` → unadjusted `WIND`; FLUXNET HH `P_F` mm per half hour → `PRECTmms=P_F/1800` mm s⁻¹.
- `ZBOT` is stored **every 30 minutes** with the dates/assumptions above. Forcing cycles across entire per-site available period; the 238 annual files use `calendar=noleap`, 17,520 half-hours/year.
- Provenance attributes include selected source CSV SHA256, version tag, approved-height-policy SHA256, early-backfilled counts, documented TA/WS mismatch count, missing-wind-height indicator and explicit `PROVISIONAL ... NOT_APPROVED_FOR_SPINUP` marker.

## Candidate integrity fix

Stage07 `pressure07a` generated `status.json` using `trial_sha256` instead of `candidate_sha256` for CH-Fru (six PA edits) and CZ-Stn (three PA edits). Stage15 was amended to read the correct field **and verify the actual candidate bytes against that stored digest**. No status file was overwritten and no checksum was bypassed. CH-Lae retains `pressurelw08a`; CH-Aws retains `landrh11a`. All 11 Stage15 preflights passed after the fix, and all 238 annual NetCDF files passed independent read-only verification.

## Reproduce: order and limitations

See repository `scripts/stage13b/`, `scripts/stage14/`, and `scripts/stage15/`, and the eight-site reference `../FLUXNET_MultiSite_8/scripts/07_make_eight_site_datm_timevarying_zbot.py`. Run Stage13b corrected BIF parser → Stage14 cross-product evidence inventory → Stage15 height policy freeze → Stage15 read-only source/DATM preflight → optional new, non-overwriting PROVISIONAL annual NetCDF creation → independent audit. Existing output folders are never rewritten.

**Remaining gates**: climate-driver scientific QC, CH-Aws 559 modeled humidity replacements (33 strong ERA5-vs-ERA5-Land disagreements), surface natural/managed landcover and FATES PFT assignment, CIME case preflight, short test simulation and convergence analysis. A 238/238 structural pass is not authorization for production spin-up.

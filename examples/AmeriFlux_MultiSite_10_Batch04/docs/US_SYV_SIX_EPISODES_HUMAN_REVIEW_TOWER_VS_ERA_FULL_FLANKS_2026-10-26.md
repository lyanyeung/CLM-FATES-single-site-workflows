# US-Syv — six suspected tower-temperature episodes: original consolidated TA_F/QC before/during/after, and same-native packaged FLUXNET ERA reference

**2026-10-26 — manual source evidence stage only.** The user explicitly requested the **before/after half-hour temperatures from both the tower product and ERA5 reference** in order to decide whether to retain observed T or replace anomalous periods. **No new US-Syv repair has been authorised or run.** This report preserves source-verified terminal triage numbers and introduces a full native HH side-by-side printing script; it does not invent values for the 2007 Feb08/09/12 episodes omitted from the previous top-12 sample.

## Critical QC/provenance interpretation

- Source `TA_F` is **consolidated FLUXNET tower data**: `TA_F_QC=0` means unfilled source/tower observation, `QC=1` is MDS gap-fill, **not directly observed tower sensor temperature**, and `QC=2` is ERA-origin fill. Do **not** claim the −27°C Feb10–12 `QC1` records were raw measured tower T: they are **filled original product values**.
- `TA_ERA` in the provided triage log is the **same-native-timestamp processed FLUXNET ERA-derived air temperature**, and **not an independently downloaded ERA5-Land T2m series**. There is no independent Syv ERA5-Land source verified or opened in the available model context; the compare table is correctly labelled `processed TA_ERA`.
- All temperatures below are original FLUXMET_HH/paired ERA values; Stage07 candidate `TA_F` at these example timestamps is unchanged.

## Exact values already supplied in the operator's real triage log (°C)

### 2007-02-10 17:30→2007-02-11 07:00 (28 HH)

| Time | Original TA_F | QC | Same-native TA_ERA | Interpretation |
| --- | ---: | ---: | ---: | --- |
| 02-10 16:30 | −11.332 | 2 | −11.332 | ERA-derived fill |
| 02-10 17:00 | −11.652 | 2 | −11.652 | filled flank |
| **02-10 17:30** | **−27.594** | **1** | **−11.920** | abrupt −15.942°C QC1 change |
| 02-10 18:00 | −27.592 | 1 | −12.187 | plateau starts |
| 02-10 18:30 | −27.587 | 1 | −12.845 | plateau |
| 02-11 00:30 | −27.446 | 1 | −14.432 | |
| 02-11 06:00 | −27.102 | 1 | −15.584 | |
| **02-11 07:00** | **−26.990** | **1** | **−15.594** | original HOLD endpoint |
| 02-11 07:30 | −15.770 | 2 | −15.770 | ERA-based fill returns |
| 02-11 08:00 | −15.945 | 2 | −15.945 | |

### 2007-02-11 17:30→2007-02-12 03:00 (20 HH)

| Time | Original TA_F | QC | Same-native TA_ERA |
| --- | ---: | ---: | ---: |
| 02-11 16:30 | −9.594 | 2 | −9.594 |
| 02-11 17:00 | −10.083 | 2 | −10.083 |
| **02-11 17:30** | **−26.966** | **1** | **−10.543** |
| 02-11 18:00 | −26.947 | 1 | −11.003 |
| 02-11 18:30 | −26.924 | 1 | −11.795 |
| 02-11 22:30 | −26.646 | 1 | −14.445 |
| **02-12 03:00** | **−26.227** | 1 | −18.040 |
| **02-12 03:30** | **−26.166** | 1 | −18.762 |
| 02-12 04:00 | −26.093 | 1 | −19.485 |

**Important: the original HOLD endpoint is not the demonstrated temperature recovery.** Continue the inspection until later 02-12 to find where the QC1 plateau ends before selecting a replacement interval.

### 2003-04-27 11:30→19:30 (17 HH)

| Time | Original TA_F | QC | Same-native TA_ERA |
| --- | ---: | ---: | ---: |
| 10:30 | 14.128 | 0 | 14.413 |
| **11:00** | **11.248** | 0 | **15.177** |
| **11:30** | **0.020** | 0 | **15.639** |
| 12:00 | 1.007 | 0 | 16.102 |
| 12:30 | −2.914 | 0 | 16.235 |
| 15:30 | 1.271 | 0 | 17.236 |
| 18:30 | −2.007 | 0 | 18.038 |
| 19:30 | 1.233 | 0 | 17.470 |
| **20:00** | **13.310** | 0 | **16.985** |
| 20:30 | 14.836 | 0 | 16.185 |

This 2003 episode is an **abrupt QC0 source temperature change**, unlike the 2007 February QC1 filled plateaux.

## All six highest-priority episodes to review, actual output pending

| Episode | Exact original source HOLD interval | HH |
| --- | --- | ---: |
| A | 2007-02-08 17:30–21:30 | 9 |
| B | 2007-02-09 17:30–23:30 | 13 |
| C | 2007-02-10 17:30–02-11 07:00 | 28 |
| D | 2007-02-11 17:30–02-12 03:00 | 20 |
| E | 2007-02-12 17:30–22:30 | 11 |
| F | 2003-04-27 11:30–19:30 | 17 |
| **Total** | **six episodes; 98 distinct HH** | **98** |

[Complete-native-time script](../scripts/manual_review/show_US_Syv_six_T_suspect_episodes_full_flanks_readonly.py), pinned GitHub revision **`99490b05f86ac320ab8db51522dc188fc4f854cb`**, **not executed by operator yet**. It SHA-checks original Stage05 report, original full US-Syv source and FLUXNET packaged ERA and Stage07 derived file, checks six source HOLD groups (exact **98** HH), **prints each HOLD half-hour and 2h before/after each interval**, and **also prints all 336 half-hours across the six complete 2007-02-08..13 days and the one complete 2003-04-27 day**. These full days prevent falsely declaring the Feb12 plateau over when original HOLD flags stop. `--report` additionally creates TWO **new read-only derivative reports under `$HOME/ameriflux_batch04_manual_review`**: episode/flank table CSV and complete 336-HH source/ERA/QC CSV. No original source or research candidate changes; **NO automatic ERA T replacement**.

Command:

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="99490b05f86ac320ab8db51522dc188fc4f854cb"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  mkdir -p "$BASE"
  SCRIPT="$BASE/show_US_Syv_six_T_suspect_episodes_full_flanks_readonly.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/show_US_Syv_six_T_suspect_episodes_full_flanks_readonly.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --report 2>&1 | tee "$BASE/US_Syv_all_2007Feb08_13_and_2003Apr27_T_ERA_review.log"
)
```

The user's decision is requested only after showing full before/during/after original temperature vs processed ERA with fill provenance. **Do not ask for a generic approval before numerical data is surfaced.**

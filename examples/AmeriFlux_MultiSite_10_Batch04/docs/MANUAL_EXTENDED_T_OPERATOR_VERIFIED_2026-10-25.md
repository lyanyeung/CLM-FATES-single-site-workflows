# Batch04 manual review — original extended US-SP1 and US-Seg 30-minute temperature series (OPERATOR-VERIFIED)

**Date:** 2026-10-25. **Source:** IRIDIS6 operator's complete output of [pinned extended temperature review script](../scripts/manual_review/show_extended_native_temperature_windows_readonly.py). The `--self-test` and `--inspect` passed for **7/7 date windows**, full original FLUXMET native HH sources/SHAs and all included HH rows; **read-only**. This is user-supplied terminal evidence rather than remote execution of IRIDIS6 through GitHub.

```text
MANUAL EXTENDED T SELF-TEST PASS: 7 original windows, 2 immutable native sources; no writes
SOURCE VERIFIED US-SP1 original_SHA256 d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963 full_HH_rows 368208
SOURCE VERIFIED US-Seg original_SHA256 2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d full_HH_rows 333120
MANUAL EXTENDED T DONE: READ ONLY; NO ORIGINAL/QC/ERA/MODEL FILE WRITES
```

**Scope of this output:** original AmeriFlux FLUXNET `TA_F`, `TA_F_QC`, `TA_F_MDS`, `TA_F_MDS_QC`, `TA_ERA`, `VPD_F`, `VPD_F_QC`, 30-minute native local-standard clock. `TA_ERA` is the **original processed FLUXNET ERA-derived** data, not the independently downloaded ERA5-Land dataset. **All 7 printed windows' temperature QC entries are original `TA_F_QC=0`**; `VPD_F_QC` differs by period. The same-value `TA_F=TA_F_MDS` with QC0 is product lineage, not sensor independence.

## 2007-10-15: earlier than 15:30 was already anomalously cool vs ERA

| Local clock 2007-10-15 | Original TA_F °C / QC | TA_ERA °C | Source VPD hPa / QC |
| --- | --- | --- | --- |
| 05:00 | 14.920 / 0 | 19.173 | 4.822 / 2 |
| 06:00 | 14.550 / 0 | 17.949 | 3.319 / 2 |
| 06:30 | 11.131 / 0 | 18.019 | 3.421 / 2 |
| 09:30 | 11.912 / 0 | 21.313 | 6.446 / 2 |
| 11:00 | 15.408 / 0 | 26.684 | 17.426 / 2 |
| 12:00 | 12.354 / 0 | 26.849 | 17.393 / 2 |
| 15:00 | 13.527 / 0 | 27.869 | 19.025 / 2 |
| 15:30 | 12.254 / 0 | 27.676 | 18.481 / 2 |
| 17:30 | 11.150 / 0 | 25.919 | 14.025 / 2 |
| 18:00 | 23.220 / 0 | 24.817 | 10.913 / 2 |
| 21:00 | 19.800 / 0 | 22.726 | 7.948 / 2 |

**New crucial finding: 18:00 systematic jump occurs on FOUR consecutive dates.** In all four cases original TA_F and TA_F_MDS have QC0, not a declared model gap-fill.

| Date Oct 2007 | 17:30 measured TA_F °C | 18:00 measured TA_F °C | ΔTA over 30 minutes °C | 17:30 source TA_ERA °C | 18:00 TA_ERA °C |
| --- | ---: | ---: | ---: | ---: | ---: |
| 15 | 11.150 | 23.220 | **+12.070** | 25.919 | 24.817 |
| 16 | 11.149 | 23.220 | **+12.071** | 26.276 | 25.258 |
| 17 | 11.169 | 23.710 | **+12.541** | 26.313 | 25.437 |
| 18 | 11.138 | 26.240 | **+15.102** | 27.470 | 26.963 |

At 08:00–17:30 across Oct 16–18, tower values are mostly ~11–15°C while the original processed ERA reference rises into ~20–30°C. At precisely 18:00, the original TA jumps back close to ERA. This **strongly suggests systematic time-of-day-specific processing/channel/instrument problems**, but does **not** prove a particular failure mechanism or validate ERA as true tower temperature. **Do not repair only the Oct 15 17:30 record** or automatically replace entire days. Request source-side measured TA instrumentation and timestamps or independently reviewed AmeriFlux BASE raw channels.

## US-SP1 January 2008: full 91-HH native source profile, not two isolated points

**Window:** 2008-01-15 17:00 through 2008-01-17 14:00, **91/91 HH**, original TA_QC0 throughout and original `VPD_F_QC=1` throughout.

| Local-standard clock | Original TA_F °C | TA_ERA °C |
| --- | ---: | ---: |
| Jan 15 17:00 | +6.037 | +13.842 |
| Jan 15 19:30 | −1.201 | +10.169 |
| Jan 16 00:00 | −5.664 | +8.137 |
| Jan 16 05:30 | −10.638 | +8.722 |
| Jan 16 07:00 | **−11.144** | +8.923 |
| Jan 16 08:00 (**HOLD**) | **−8.211** | +8.569 |
| Jan 16 08:30 (**HOLD**) | **−4.365** | +8.555 |
| Jan 16 10:00 | +1.978 | +9.850 |
| Jan 16 15:30 | +5.303 | +15.470 |
| Jan 17 00:00 | −4.006 | +14.154 |
| Jan 17 08:00 | −0.451 | +16.713 |
| Jan 17 13:00 | +8.400 | +19.345 |
| Jan 17 14:00 | +11.236 | +19.109 |

Original tower T exhibits a smooth multi-hour frost/warming trajectory on Jan 15–16 *and* a strongly discrepant additional overnight period Jan 16–17. A physiologically plausible-looking smoothly changing series is **not independent sensor validation**. Stage19 had previously found 27 HH and 44 HH respective long negative tower–ERA difference episodes; those 08:00/08:30 events overlap and must not be counted twice. This is a broader source problem candidate and cannot be resolved by overwriting two points only.

## US-SP1 February 2008: full 85-HH native source profile

**Window:** 2008-02-02 18:00 through 2008-02-04 12:00, **85/85 HH**, original TA_QC0 throughout and VPD_F_QC1 throughout.

| Local-standard clock | Original TA_F °C | TA_ERA °C |
| --- | ---: | ---: |
| Feb 2 18:00 | +15.556 | +19.429 |
| Feb 2 23:30 | +1.929 | +12.167 |
| Feb 3 03:00 | −2.961 | +9.936 |
| Feb 3 07:30 | **−6.588** | +11.163 |
| Feb 3 08:00 (**HOLD**) | **−3.613** | +11.410 |
| Feb 3 09:00 | +1.701 | +11.624 |
| Feb 3 12:00 | +14.708 | +19.536 |
| Feb 3 15:30 | +22.842 | +23.065 |
| Feb 3 16:30 | +23.331 | +23.386 |
| Feb 4 03:00 | +4.178 | +14.158 |
| Feb 4 08:00 | +5.825 | +14.243 |
| Feb 4 12:00 | +19.321 | +21.161 |

The two independent series converge closely during the afternoon of Feb 3 but diverge by >10°C overnight. This is a **time-varying systematic comparison issue**, not an isolated Feb 3 08:00 outlier. Keep the original TA under scientific review, and do not infer ERA is ground-truth without independent raw/source evidence.

## US-Seg: extended original TA after Dec 27 20:00

**Window:** 2016-12-27 15:00 to 2016-12-28 10:00, **39/39 HH**. All original TA_F and MDS QC=0; original VPD_F_QC=2 throughout.

| Local-standard clock | Original TA_F °C | TA_ERA °C |
| --- | ---: | ---: |
| Dec 27 18:00 (**HOLD**) | +0.015 | +8.273 |
| Dec 27 20:00 | −0.270 | +3.865 |
| Dec 27 20:30 | −1.223 | +3.384 |
| Dec 27 21:00 | −0.849 | +2.903 |
| Dec 27 22:00 | −1.398 | +2.707 |
| Dec 27 23:00 | −1.944 | +2.185 |
| Dec 27 23:30 | −2.705 | +2.682 |
| Dec 28 00:00 | −2.333 | +3.178 |
| Dec 28 01:00 | −3.308 | +2.865 |
| Dec 28 02:00 | −2.505 | +1.938 |
| Dec 28 03:00 | **−3.948** | +2.010 |
| Dec 28 04:00 | −1.142 | −0.936 |
| Dec 28 04:30 | +0.012 | −1.172 |
| Dec 28 06:00 | −2.542 | −1.626 |
| Dec 28 08:00 | −2.756 | −1.507 |
| Dec 28 10:00 | +3.411 | +2.044 |

The native tower cooling continues well beyond 20:00 and the gridded/processed ERA reference itself falls below zero by 04:00, with source series eventually close. There is a sharp 17:30→18:00 native temperature drop (**4.332→0.015°C**) but not a solitary one-cell spike. **Prefer retaining original source T pending met provenance** and separately fixing VPD/RH *physical closure* under the established Stage14 candidate; do not claim source science HOLD is fully cleared from this pattern alone.

## Manual 3-point alternative --assess environment status

The first `--assess` failed on the operator's **(base)** conda environment:

```text
ModuleNotFoundError: No module named 'numpy'
```

Operator then ran `conda activate clm_fates_env` and invoked the same script again; the returned excerpt shows `MANUAL TRIAL SELF-TEST PASS` but **no final `MANUAL PROPOSAL` or `MANUAL ASSESS ONLY` output** yet. Consequently, exact ERA5-Land 2000 temperatures have **NOT yet been verified by --assess**, and **no three-point research trial production is claimed**. Stage14/15 inputs and all 8 original TA science HOLDs retain their prior status. Prefer checking running-process/log status or re-invoking `--assess` with the correct interpreter after confirming that no process is currently running.

[Original manual review specification](MANUAL_TEMPERATURE_DECISIONS_AND_EXTENDED_WINDOWS_2026-10-25.md). [Manual three-point script](../scripts/manual_review/build_manual_T_replacement_trial_only.py). [Read-only window script](../scripts/manual_review/show_extended_native_temperature_windows_readonly.py).

**No original, candidate, DATM/CIME/Slurm or spinup files were changed by the extended-temperature inspection.** No site PI email or external BASE retrieval occurred in these logs.

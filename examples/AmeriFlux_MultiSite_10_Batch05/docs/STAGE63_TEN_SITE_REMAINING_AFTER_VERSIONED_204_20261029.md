# Batch05 Stage63 — what remains after user-approved 204 half-hour versioned repair candidates

## Confirmed source facts, 29 October 2026

- Exact Batch05 `sites.tsv` has ten original AmeriFlux sites: US-UiD, US-UMB, US-UMd, US-Var, US-Vcm, US-Vcp, US-WCr, US-Whs, US-Wjs, US-Wkg.
- Stage25 actual IRIDIS6 original science audit verified **1,750** flagged native original source half-hours: **176** P1 (130 approved and 46 manual HOLD) plus **1,574** P2/P3 across **483** original P2/P3 events. Earlier Stage25 found **zero P2/P3** covered by the then-approved 166 overlay.
- Stage62 actual operator success at **2026-10-29 00:17 UTC**: **204** versioned user-approved science repair candidate rows (previous 174 unchanged + exact US-Wjs 2018 30 new), with original FLUXMET and DATM/CIME/Slurm unchanged. Stage62 204 overlay SHA256 `7d2b0b3c8018b9cc28c6d8a7ea2f28dd593204f96e2f279433b61d721689a5a7`. These are not yet model-ready forcing.

### Ten-site original P2/P3 population (baseline, NOT remaining count)

| Site | Original P2/P3 flagged HH |
|---|---:|
| US-Vcp | 626 |
| US-Wjs | 401 |
| US-Vcm | 362 |
| US-Var | 62 |
| US-WCr | 62 |
| US-UMB | 23 |
| US-Wkg | 22 |
| US-UMd | 15 |
| US-Whs | 1 |
| US-UiD | 0 |
| **Total** | **1,574** |

Because the 204 newest candidate HH may include **P1**, **P2/P3**, and **unflagged context/edge records** outside the original 1,750-HH screen, **never calculate 1,574−204**. Determine the exact remaining count by joining on original `(site, native_time)` keys. Old P1 46 manual HOLD and the two RH saturation platform windows (10 HH in US-Vcm and US-WCr) must stay separate.

## Stage63 exact read-only remaining-work inventory

[Stage63 Python](../scripts/stage63/63_exact_204_overlay_vs_original_1750_ten_site_remaining_READONLY.py), source commit `08b0c12231d03ac56aaabc70ec934e10df65b880`, Git blob `a362989caba34c2d7bb6daf56ce4777d71abc789`.

[One-line IRIDIS6 launcher](../scripts/stage63/run_stage63_iridis6.sh), commit `27dc04c1be3f7ff0e02d81572995c2d8254b96f3`, Git blob `7f0be70f6e29b5f20dea7fe8b44115d8a24974d4`.

Runs only on existing Stage24, Stage25 and successful Stage62 operator reports. SHA-checks 204 exact-overlay manifest and immutable earlier Stage24 166, manual 46, plus original 1,750 native screen, original P1 130 approved/46 HOLD. Joins exact timestamps, reports covered vs remaining P2/P3 HH, remaining distinct 483-source-event counts per site, site status, original P1 46 and RH platform 10. No source, forcing or previous overlay changes.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/27dc04c1be3f7ff0e02d81572995c2d8254b96f3/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage63/run_stage63_iridis6.sh" -o "$HOME/run_stage63.sh" && test "$(git hash-object "$HOME/run_stage63.sh")" = "7f0be70f6e29b5f20dea7fe8b44115d8a24974d4" && bash "$HOME/run_stage63.sh"
```

Report outputs:
- `stage63_EXACT_TEN_SITE_REMAINING_AFTER_204.csv`
- `stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv`
- `stage63_ALL483_ORIGINAL_P2P3_EVENTS_AFTER_204.csv`
- `stage63_UNCHANGED_46_P1_HOLD_SOURCE_LEDGER.csv`
- `stage63_UNCHANGED_10_RH_PLATFORM_HOLD_SOURCE_LEDGER.csv`
- `STAGE63_TEN_SITE_REMAINING_APPROVAL_AND_HOLD_REPORT.md`
- `stage63_manifest.json`

**GitHub source/launcher blobs verified; operator IRIDIS6 run not yet reported**. Final number of original P2/P3 HH remaining, their exact episode counts, and all-site remaining queue must be taken from actual Stage63 output, not guessed.

Scientific next step after Stage63: prioritize real source-native QC/sensor and independent weather evidence for remaining US-Vcp, US-Wjs and US-Vcm events. Do not automatically substitute ERA5-Land, source-processed ERA, or MDS. Zero production-forcing site approvals are established solely from these repair audits.

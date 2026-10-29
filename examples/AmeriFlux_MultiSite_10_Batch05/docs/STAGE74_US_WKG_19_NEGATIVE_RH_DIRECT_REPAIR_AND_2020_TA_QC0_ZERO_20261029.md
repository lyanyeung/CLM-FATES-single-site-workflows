# AmeriFlux Batch05 US-Wkg Stage74 — 10 original events, 22 flagged HH

## Operator native-source evidence

The operator supplied exact original 30-minute TA_F, TA_F_QC, VPD_F, VPD_F_QC, original source processed TA_ERA/VPD_ERA, rain and incoming SW context for all 10 Stage63 original US-Wkg episodes with 22 flagged native HH. Archive SHA256 `d9c31372ad29fa79946a97ac30eb02ad679b261f0b925db97ef88cf6b325221e`, the Stage45 verified original US-Wkg AmeriFlux FLUXMET HH ZIP.

**Source tally: 19/22 flagged original implied RH<0%, three flagged with 0<=RH<=100%.** Every one of the 22 original flagged HH has source TA_F_QC=0 and VPD_F_QC=1. User's previous explicit science policy is that **RH<0 directly repair, not a candidate pending further approval; physically valid original RH values remain unchanged**.

| Event | Flagged HH | RH<0 HH | Original source RH>=0 HH | Treatment |
|---|---:|---:|---:|---|
| E0001 2011-08-23 08:00 | 1 | 0 | 1 (0.22%) | Pass unchanged |
| E0002 2011-08-24 07:00–08:00 | 3 | 3 | 0 | Repair VPD at original TA using RH linear interpolation |
| E0003 2011-08-24 09:30 | 1 | 0 | 1 (0.63%) | Pass unchanged |
| E0004 2011-08-24 21:30–22:00 | 2 | 2 | 0 | Repair VPD at original TA using RH linear interpolation |
| E0005 2011-08-24 23:00–2011-08-25 00:00 | 3 | 2 | 1 (0.33%) | Repair two negative, pass third unchanged |
| E0006 2018-10-16 09:00 | 1 | 1 | 0 | Repair VPD at original TA using RH linear interpolation |
| E0007 2018-10-16 10:00–11:00 | 3 | 3 | 0 | Repair VPD at original TA using RH linear interpolation |
| E0008 2020-02-18 12:00–14:30 | 6 | 6 | 0 | **Temperature error, not usual VPD error**: source TA_QC0 exactly 0.000°C throughout sunny 6HH; interpolate TA from two original native QC0 T anchors and retain selected original VPD |
| E0009 2025-03-07 12:30 | 1 | 1 | 0 | Repair VPD by neighboring original physical RH at original QC0 TA; preserve anomalous original temperature for separate temperature-specific audit |
| E0010 2025-09-10 13:00 | 1 | 1 | 0 | Repair VPD by neighboring original physical RH at original QC0 TA; preserve anomalous original temperature for separate temperature-specific audit |

## Critical 2020 original source error despite QC0 label

2020-02-18 at 11:30 TA_F=17.510°C QC0 and at 15:00 TA_F=20.850°C QC0. The **six intervening original 12:00–14:30 HH are 0.000°C, TA_F_QC=0, incoming SW 660–824 W m⁻²**. Source paired processed TA_ERA rises 16.374→19.394°C while the recorded 0.000°C persists. The original VPD_F_QC=1, VPD 11.089–11.756 hPa is not intrinsically excessive at ~18–20°C. Negative RH (−81.43% to −92.34%) in this six-point run is caused by evidently corrupted TA_F despite the source nominal QC0 flag. It would be physically misleading to reconstruct low VPD assuming the source zero-degree values were true measured temperatures.

The Stage74 numerical correction in a **versioned approved user-policy overlay only** therefore restores these six TA using exact uniform linear interpolation between the original source two QC0 measured boundary T anchors: 17.987143, 18.464286, 18.941429, 19.418571, 19.895714, 20.372857°C. Original source VPD_F/QC1 is preserved, resulting RH is approximately 43.22–52.41%. The original source ZIP and the recorded original QC=0 label are **not altered**. The new-version provenance explicitly states source-original QC0 cannot be taken at face value at those six corrupt 0°C records; this is a scientifically traceable exception to usual preservation of source QC0.

The user's direct RH-negative repair policy is recorded as the scientific trigger. Since an actual nominal QC0 TA is numerically corrected, this has separate provenance from the 13 VPD-only repairs and should be explicitly noted in reporting. No physical source TAR measurements are invented or represented as original observations.

## Other source TA_QC0 patterns that still deserve separate temperature checks

- 2025-03-07 12:00 TA=-1.708°C and 12:30 TA=-4.120°C while source processed ERA T≈10°C, surrounded by an atypical temperature plunge.
- 2025-09-10 12:30 TA=29.520°C, 13:00 TA=12.890°C, 13:30 TA=23.470°C, with rain around 12:30–13:00 and original source ERA TA≈29°C. The point may be storm sensor response or data corruption and is not silently overwritten under the present RH repair operation.
- 2011-08-24 and 2018-10-16 source QC1 VPD may be unusually dry even outside original negative RH flags. Under the explicit user policy nonnegative original implied RH is passed unchanged, not promoted as independently measured.

## Versioned approved repairs and operational safety

Stage74 script checks 22 exact pending Stage63 source times, 22 Stage27 historical time-specific TA/VPD/QC and archive SHA; verifies 19 negative and three nonnegative source RH classifications; checks six native 2020 zero-valued TA records and both QC0 boundary donor values; applies direct source-neighbor physical RH interpolation to 13 HH (source TA unchanged), and source-QC0 temperature interpolation to the six 2020 anomalous zero-valued HH (source VPD unchanged). It adds 19 new versioned approved records to the existing **240 HH** Stage72 overlay, producing **259 HH**. The prior 240 approved records remain value-identical, as do original ZIP, source QC, other original times, model forcing and Slurm jobs.

The attached user message showed successful Stage69 219 total plus US-UMB Stage70 source audit, but **no Stage72 execution result**, so the Stage74 launcher will detect and run the immutable Stage72 US-UMB 21-negative-RH rule first if its successful 240 report has not yet been created.

- [Stage74 US-Wkg direct 19 source repairs](../scripts/stage74/74_US_Wkg_19_negative_RH_direct_approved_259.py) commit `63c89683b350edcd36084c8a46df98d72910a706`, Git blob `be5cccabad5855fced375f8bd44d09b496363e82`.
- [Stage74 launcher](../scripts/stage74/run_stage74_Wkg_19_negative_RH_direct_approve_iridis6.sh) commit `be9c93a6568f0a680ba969dd4e45d3d1af947871`, Git blob `e6111f176d0b1d72bb106ff9a08a5e0a02adf807`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/be9c93a6568f0a680ba969dd4e45d3d1af947871/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage74/run_stage74_Wkg_19_negative_RH_direct_approve_iridis6.sh" -o "$HOME/run_stage74_Wkg.sh" && test "$(git hash-object "$HOME/run_stage74_Wkg.sh")" = "e6111f176d0b1d72bb106ff9a08a5e0a02adf807" && bash "$HOME/run_stage74_Wkg.sh"
```

**As authored:** stage74 script GitHub commit exists and launcher source SHA was verified. Actual IRIDIS6 Stage72/74 outputs are not yet reported in this conversation, thus "259 approved" is a post-run expected versioned state, not an already executed fact.

## Stage74 first-run TypeError and verified GitHub fix (29 October 2026)

Actual operator terminal evidence:
- Stage72 completed successfully; `219+21=240` versioned approved rows, preserving previous 219. SHA256 `b274ab45cbf3deb740faddbe26970a1d5c518d9feb5b5f2556694cd7ce609882`; reports `/home/ly3n24/ameriflux_batch05_stage72_UMB/UMB_240_20261029T041816Z_2340008/`.
- Immediately after Stage72, original Stage74 script encountered `TypeError: '_io.TextIOWrapper' object is not callable` in `source_processed_ERA_RH_derived_pct=f(er)` before creating any 259-row output. It was an **implementation variable shadowing bug**, not an input-science or SHA failure: the local CSV handle named `f` masked the numeric formatter function named `f`.
- Code fix: rename numeric formatter to `format_float` and all numeric formatter calls; add explicit unit self-test for formatting, no meteorological policy or original data changes. Fixed [Stage74 Python source](../scripts/stage74/74_US_Wkg_19_negative_RH_direct_approved_259.py) commit `ea27a85043521921449df75ed7cd6dd8d4e0e032`, Git blob `9c4f85dd636c52bb482b64f35e631e3ce9329924`. Updated [Stage74 SHA-pinned launcher](../scripts/stage74/run_stage74_Wkg_19_negative_RH_direct_approve_iridis6.sh) commit `5c798847cdb736dd52928a13479292efa62c9c40`, Git blob `4ba72efb09ac4db8c887609f4fd57d209b0636d3`. GitHub source/blob SHA verified, but **updated script has not yet been run on the operator IRIDIS6 cluster**.
- Stage74 launcher reuses the successful 240-row Stage72 output rather than recreating it, and creates a new output directory for the 259 expected version. The original 240 approved rows and source data are untouched.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/5c798847cdb736dd52928a13479292efa62c9c40/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage74/run_stage74_Wkg_19_negative_RH_direct_approve_iridis6.sh" -o "$HOME/run_stage74_Wkg_fixed.sh" && test "$(git hash-object "$HOME/run_stage74_Wkg_fixed.sh")" = "4ba72efb09ac4db8c887609f4fd57d209b0636d3" && bash "$HOME/run_stage74_Wkg_fixed.sh"
```

**Policy recorded separately** in [Batch05 README](../README.md): suspicious TA QC0→QC1 repairs use both QC0 bracketing observations for the whole QC1 run; QC1→QC2 repairs use original QC1 bracketing values for the whole QC2 run, maintaining original QC flags in source and an auditable versioned corrected overlay. This is the operator's general forward-looking Batch05 rule; it does not mean US-Wkg 2020 source QC0 zero-temperature corruption is a QC0→QC1 transition.

## Actual Stage74 operator success and latest default-acceptance policy

Actual IRIDIS6 Stage74 rerun from the corrected immutable GitHub source **SUCCEEDED**. The source original 10 events/22HH were handled as **19 direct RH-negative repair** (13 VPD-only at original TA, six correction of objectively corrupted 2020 native QC0 temperature zeros while VPD unchanged) plus **3 original RH>=0 HH passed unchanged**. Prior 240 approved records retained, new 259 total versioned approvals. SHA256 `c94e0adc96df846b682f69e3c85d2be8247d23ba7debed686a3462bb5927fc6f` at `/home/ly3n24/ameriflux_batch05_stage74_Wkg/Wkg_direct_19_negative_RH_20261029T042245Z_2362992/stage74_VERSIONED_259_APPROVED_RH_VPD_TA_native_overlay.csv`. Source ZIP, historical original QC, prior 240, DATM, CIME and Slurm unchanged. The earlier Stage74 formatter bug is fully resolved.

**Later investigator confirmation:** Accept routine negative RH corrections and suspect `QC0→QC1`/`QC1→QC2` contiguous-block repairs automatically using the existing original-source QC-priority rule; only source intervals with **obviously suspect original temperature or meteorology** receive a focused exception review. No repeated HOLD by default. Two outstanding native-source temperature *exceptions* (not automatic revocation of accepted 259 numerical overlay rows):

1. `2025-03-07 12:00–13:00`: source QC0 TA fell +6.315 to −1.708 then −4.120°C with product processed TA_ERA around +10°C; Stage74 numerical RH at 12:30 98.87% was obtained using the suspicious original −4.120°C and corrected VPD 0.051 hPa. Check local source temperature specifically before forcing promotion.
2. `2025-09-10 13:00`: source QC0 TA=12.890°C between 29.520°C and 23.470°C source QC0 native neighbors; source `TA_ERA`≈29.396°C; source original rainfall was recorded around the episode. Stage74 numerical negative RH correction gave VPD 8.404 hPa and RH 43.44% at **unchanged** suspect TA=12.890°C. Investigate this original T excursion locally without reopening all routine RH corrections.

This is a precisely scoped source-temperature scientific caveat, not proof that either source tower anomaly was meteorologically impossible, not permission to replace original QC0 by an arbitrary reanalysis product, and not a new site-wide HOLD.

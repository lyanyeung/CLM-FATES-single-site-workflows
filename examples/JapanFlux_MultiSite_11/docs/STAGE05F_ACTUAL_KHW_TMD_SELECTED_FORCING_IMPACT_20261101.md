# JapanFlux Stage05F — actual selected forcing-source impact on JP-Khw and JP-Tmd (2026-11-01)

## Source and status

Operator ran the published [Stage05F read-only selected-F vs source ERA event reviewer](../scripts/stage05/05f_source_event_selected_forcing_impact_READONLY.py) for **JP-Khw** and **JP-Tmd**. Both returned `READONLY_SOURCE_IMPACT_SCREEN_COMPLETE`; the scripts read the original source FLUXMET_HH through each nested release ZIP without editing any source. No Slurm and no physical reconstruction were used. Counts below are from the operator's **reported script summaries**; full event-level JSON `$HOME/japanflux_stage05f/JP-Khw_impact.json` and `JP-Tmd_impact.json` exist on IRIDIS but **have not been uploaded to GitHub**.

## Actual Stage05F results

| Metric | JP-Khw | JP-Tmd |
|---|---:|---:|
| Stage05D ERA5_HH unique anomalous source timestamps, all years | 20 | 20 |
| ERA anomalous timestamps inside native FLUXMET_HH tower range | 8 | 12 |
| ERA anomalous timestamps outside native FLUXMET_HH tower range | 12 | 8 |
| Selected `TA_F` physically anomalous at event contexts | 3 | 3 |
| Selected `PA_F` physically anomalous at event contexts | 6 | 9 |
| Selected `LW_IN_F` physically anomalous at event contexts | 2 | 2 |
| `TA_F` same as flagged `TA_ERA` | 3 | 3 |
| `TA_F` different from flagged `TA_ERA` | 3 | 6 |
| `LW_IN_F` same as flagged `LW_IN_ERA` | 2 | 2 |
| `LW_IN_F` different from flagged `LW_IN_ERA` | 2 | 4 |
| `PA_F` same as flagged `PA_ERA` | 6 | 9 |
| `PA_F` different from flagged `PA_ERA` | 0 | 0 |

### Exact original QC label histograms at selected ERA-flagged timestamps

- **JP-Khw**: `LW_IN_F_QC`: `2` ×2, `0` ×2; `TA_F_QC`: `2` ×3, `0` ×3; `PA_F_QC`: `2` ×6.
- **JP-Tmd**: `LW_IN_F_QC`: `2` ×2, `0` ×4; `TA_F_QC`: `2` ×3, `0` ×6; `PA_F_QC`: `2` ×9.

The match pattern is consistent with source-selected `*_F` being polluted by `*_ERA` where the native source selection is QC-labelled `2`, while `QC=0` selected tower values differ and avoid these particular physical screens. **However, QC code semantics must still be verified from original product documentation.** The Stage05F data demonstrate numeric equality and raw labels, not independent measurement truth.

### Scientific meaning and limitations

- **PA selected forcing is the priority**: all flagged ERA pressure cells checked inside the tower period also occur in `PA_F` at both sites, with original `PA_F_QC=2`. Pressure at the 2005 event minimum reaches 0 kPa in both; affected neighboring half-hours can fall around 49 kPa. Even when pressure neighbors do not cross the current <50 kPa screen, approximately half normal pressure remains physically suspect. Do not rely solely on the arbitrary cutoff.
- **TA and LW are conditional**: selected `TA_F` and `LW_IN_F` correctly avoid the defective ERA numeric values at several other timestamps, including previously examined 2011 examples with QC-labelled `0`. They require preservation rather than blanket time-window replacement.
- **Source flag timestamp count is not source-selected corruption count**: Khw's 20 source events imply 8 FLUXMET overlaps (1990, 1999, 2005, 2011, 2022: Khw 2000–2021 includes only 2005, 2011); Tmd's 12 includes 2005, 2011, 2022 (Tmd 2005–2023). Selected-force impact must be assessed per source variable and half-hour.
- **Khw 2005 `TA_F_MDS` remains questionable**: previously seen ~1°C MDS on hot ~23°C ERA neighboring periods; do not use it automatically for corrective overlays.
- **No repairs, forcing generation, source overwrites, model runs, or independent ECMWF ERA5 validation have been performed.** The source clock time basis and broader source QC semantics remain pending.
- **Selected_F flags** count variable-specific physical threshold triggers in the context rows. They may overlap each other in a half-hour and are not unique site×time counts.

## Next action

Finish [Stage05F](../scripts/stage05/05f_source_event_selected_forcing_impact_READONLY.py) for the other six JPF sites with anomalous ERA5 sources: **JP-Fhk, JP-Fjy, JP-Spp, JP-Tak, JP-Tef, JP-Yms**. Process one site at a time, on the command line, without Slurm. Preserve output `$HOME/japanflux_stage05f/<site>_impact.json`, validate JSON before claiming `READONLY_SOURCE_IMPACT_SCREEN_COMPLETE` and avoid overriding earlier successful files. JP-Api had 0 source-ERA threshold events and cannot run the Stage05F flag-only extractor without changing its intended scope; this is expected and not a failure.

Once eight station reports are complete, construct a variable/time-level science candidate register with separate categories `CONTAMINATED_SELECTED_F`, `ERA_ONLY_SELECTED_F_PRESERVED`, `OUTSIDE_TOWER_PERIOD`, `AMBIGUOUS_SOURCE` and independent physical-source/metadata verification requirements. The selection and replacement of any alternative values requires later scientific approval.

The **JP-Tom and JP-Tgf RH/VPD anomalies are separate** and remain pending.

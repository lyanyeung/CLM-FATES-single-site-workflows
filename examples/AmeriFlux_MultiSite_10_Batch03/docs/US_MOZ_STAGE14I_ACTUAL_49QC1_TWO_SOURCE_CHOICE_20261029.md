# US-MOz — actual Stage14I result (2026-10-29 04:38 UTC) and human source choice

The operator executed the pinned Stage14I [49 original source-QC1 two-ERA sensitivity script](../scripts/stage14/14i_US_MOz_Jan09_49QC1_two_source_isolated_onepass.py) on IRIDIS6. **Both alternatives were actually generated**, full **315,360** halfhour native model forcing fields complete and T/TBOT/VPD/QBOT thermodynamic closure passed. Original all-other source records and previously prepared source research **Jan05–06 27 ERA5-Land + one 19:30 QC1 bridge + separate user-approved Jan06–07 40** all preserved. Three Jan09 original QC2 and first Jan10 09:30 original measured QC0 records remain unchanged. No production, Slurm, DATM, AD400 authorization.

Actual new isolated output:
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_MOz_Jan09_49QC1_TWO_REANALYSIS_RESEARCH_ONLY_20261029T043831Z_397227c6
```

Both candidate scopes **6 + 3 + 40 = 49 native QC1/QC1** HH: Jan09 07:30–10:00 (6), Jan09 11:30–12:30 (3), Jan09 13:30–Jan10 09:00 (40). The entire remaining unaltered 139 HH QC1 Jan06–09 source run is NOT mass replaced. No source QC0 was observed on Jan09; three QC2 are exactly ERA-based and not an independent cross-validation target.

| Measured diagnostic | Original paired FLUXNET companion ERA variant | Signed independent CDS ERA5-Land variant |
|---|---:|---:|
| Jan09–10 modified original QC1 source halfhours | 49 | 49 |
| Whole native 315,360 water/VPD/QBOT/TBOT closure | PASS | PASS |
| Six external Jan09/Jan10 source-boundary T jumps >4°C | 0 | 0 |
| Six external VPD jumps >4 hPa | 0 | 0 |
| Maximum six boundary T jump | **2.466°C** | 3.236°C |
| Jan10 09:00→09:30 first original measured QC0 T jump | **0.075°C** | 1.240°C |
| Jan08–Jan10 total T jumps >4°C, including preexisting Jan08 | 2 | 2 |
| Jan08–Jan10 VPD jumps >4hPa | 0 | 0 |

Two ERA-linked products differ on 49 source target rows by mean absolute **1.777069°C T**, mean absolute **0.896027 hPa VPD**, and maximum absolute **3.282670°C T** / **1.360681 hPa VPD**. They are NOT two independent tower sensors. The excellent FLUXNET-companion continuity to original QC2 is partly expected **because QC2=the original companion ERA**; this is a continuity/model-source criterion, NOT empirical verification of tower truth.

**Human decision:** retain `FLUXNET_COMPANION_ERA_315360_FULL_RESEARCH_ONLY_NOT_DATM.csv` as the **main currently numerically complete exploratory Jan09 forcing**, retain `CDS_ERA5LAND_FIXED_BIF_UTC_MINUS6_315360_FULL_RESEARCH_ONLY_NOT_DATM.csv` as the competing sensitivity, never overwrite original Stage14G. Jan09's selected main case had no remaining >4°C external source boundary, and there is NO reason to globally modify Jan09 QC1 beyond exact 49.

**Only two selected >4°C Jan08 source-native halfhour transitions remain in Jan08–Jan10.** Earlier Stage14H actual rows: Jan08 13:00 original source QC1/1 selected T −0.907°C, ΔT −5.194°C; Jan08 14:00 original source QC1/1 selected T +4.606°C, ΔT +4.362°C. These are not Jan09 transition failures. Single halfhour source QC1 values must NOT be reinterpreted as measured QC0, and clipping to ±4°C is not scientific validation. Stage14J should inspect Jan08 11:00–15:30 and offer a strictly bounded QC-aware optional alternative, only if original QC/provenance and both external boundaries work; otherwise retain these as provenance cautions and close US-MOz numerically completed status.

**No Post-v5/DATM/CIME/AD400/Normal400/Slurm authorization**: PFT land/surface mapping, sensor ZBOT, native time and station source-product independence still to be checked in one model preflight.

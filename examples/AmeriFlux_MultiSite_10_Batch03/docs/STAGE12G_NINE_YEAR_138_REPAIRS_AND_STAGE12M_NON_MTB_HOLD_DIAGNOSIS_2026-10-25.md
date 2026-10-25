# Batch03 Stage12g nine-source-year VERIFIED — US-Me6 / US-NR1 divergent outcomes

**2026-10-25 08:32 UTC** — On IRIDIS6 the user executed the identical, Git-blob pinned Stage12g `--check` and `--run`, with all 9 original missing-year Stage12f gridded site/year sources SHA verified (US-MtB 2020/2022/2024, US-Kon 2008/2011/2012, US-Me6 2015/2017, US-NR1 2022). Source assertions **new_source_site_years_verified=9**, **new_source_native_event_coverage=1334**, and **still_missing_external_source_year_rows=1476** all passed.

The NEW isolated six-site SHA-receipted research-only, **INCOMPLETE NOLEAP**, source-only forcing shadow is:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/`

## Exact model/science results

| Site | Original Stage12e year-missing RH gaps | Newly gridded source-covered native RH events | Passing numerical RH/QBOT research candidates | Still missing annual ERA5-Land sources | Rows with at least one incomplete forcing field |
|---|---:|---:|---:|---:|---:|
| US-NR3 | 6 | 0 | 0 | 6 | 238 |
| US-Kon | 211 | 196 | 121 | 15 | 367 |
| US-NR1 | 135 | **22** | **0** | 113 | 238 |
| US-MMS | 15 | 0 | 0 | 15 | 16 |
| US-MtB | 2363 | 1038 | 3 (inherited prior) | 1325 | 2840 |
| US-Me6 | 80 | **78** | **14 (NEW)** | 2 | 67 |
| **Total** | **2810** | **1334** | **138 (14 newly gained this run)** | **1476** | **3766** |

The 100 newly source-covered native RH events across US-Me6/US-NR1 were not automatically accepted: **US-Me6 14/78 = 17.95%**, US-NR1 **0/22 = 0%**, together 14% yield.

Original SHA-sealed science-held events for these source years:

| Site | Source physically screened RH event class | Native half-hours |
|---|---|---:|
| US-Me6 | `HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA` | **35** |
| US-Me6 | `HOLD_SITE_GRID_T_DIFF_GT5C` | **29** |
| US-NR1 | `HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA` | **3** |
| US-NR1 | `HOLD_SITE_GRID_T_DIFF_GT5C` | **19** |
| **Total held with verified source** | | **86** |

These scientific holds are a warning against blindly downloading the highest-ranked **US-NR1 2001/2021/2018** annual sources before diagnosing the 0/22 acceptance. The old US-MtB 1,035 T/ice held source events and measured QC0 validation FAILED verdict remain unchanged. Old US-Kon 34 VPD jump and 40 source-grid T holds are not relaxed either. Original 233 Stage12b immutable physics holds remain protected. **No original EC tower TA, PSRF, source-native clock, original QC0 measurements, valid prior Stage12e numeric repairs, PFT or model jobs changed.** No Post-v5/DATM/spinup authorisation.

There are **926** total incomplete time rows among the five non-US-MtB trial sites (US-NR3 238, US-Kon 367, US-NR1 238, US-MMS 16, US-Me6 67), versus US-MtB 2,840. The **1476** year-source-missing RH events comprise **1325 US-MtB** plus **151 across the five non-MtB sites**. These are a narrower subset of the 3766 total incomplete source-native forcing rows and cannot be equated with total missing forcing. 

## Next stage: Stage12m existing-data diagnostic — NO new downloads

[Stage12m SHA-sealed read-only US-NR1/US-Me6 source temperature and VPD science hold diagnostic](../scripts/stage12/12m_us_nr1_me6_T_and_VPD_hold_diagnosis_READONLY.py) is **committed to GitHub but NOT YET EXECUTED on IRIDIS6**. It reads the new Stage12g 9-year receipt, re-verifies all 11 complete original output file SHAs, and calls the original Stage12g upstream source SHA-verifying `sources()`. It checks and conserves each of the **86** T/jump holds and 14 accepted Me6 research-only humidity values. It opens only the already-gridded sources, interpolating **T2m and surface pressure** to original EC native time under the same still-provisional BIF UTC offset; records tower-grid T difference and an approximate pressure-based grid-height proxy for each held event. For VPD >4hPa jump holds it reconstructs the *hypothetical pre-rejection candidate* from signed original gridded RH and unchanged tower temperature, and compares it against **finite final Stage12g neighboring VPD only**. The final output often masks both adjacent endpoints and CANNOT, by itself, fully reconstruct the exact original iterative first-rejection pair: any apparent missing adjacent extreme in final shadow **must NOT be interpreted as proof original VPD jump screening was wrong**.

Strict `--check` does not write files. `--run` writes only a NEW isolated SHA-receipted report; original T, P, UTC clock, VPD, QBOT and original old Stage12g gate are never rewritten. Existing `abs(Ttower - Tgrid)>5C` and 4 hPa neighboring guard continue as scientific HOLD. **Stage12m does not permit replacing new RH data or relaxing Stage12j/12g science gates.** Further CDS should depend on this source-quality finding or separately verified site science, not on sheer missing record count.

# AU-ASM Mulga1 Stage13 science register (2026-11-02)

## Verified by operator on IRIDIS6

The original L6 file SHA256 is `b9381c4ed0744d03ae609cfbf3805e30bbb9223851a05f4e5b63b149dd0b10eb`. Stage12 generated six PROVISIONAL 2013–2018 NOLEAP DATM files under `/iridisfs/home/ly3n24/ozflux_ASM_PROVISIONAL_DATM_20261101T182517Z`. Stage13 source-to-DATM audit succeeded 6/6 with exact float32 mapping of seven meteorological fields and no changes to source or candidates. Stage13 output `/iridisfs/home/ly3n24/ozflux_stage13_20261102T010205Z`.

- FSDS negative: 2014 **359 records**, all source `Fsd_QCFlag=420` (PyFluxPro ACCESS alternate); 2016 **1 record**, original QC source not yet included in pasted summary. All 360 have modelled solar elevation <=0 under the provisional UTC-center interpretation. **Number below -6 degrees not yet reviewed**.
- A single 2018 WIND record exceeds 15 m/s. Do not automatically filter a single extreme.
- Annual precipitation totals (mm), including candidate NOLEAP 2016 exclusion: 2013 142.8, 2014 376.4, 2015 315.6, 2016 635.4, 2017 363.2, 2018 106.8. The source Precip has unit mm and statistic_type sum, so provisional PRECTmms=Precip/1800.
- All six files remain scientifically **UNAPPROVED**. No AD400, Normal400 or new model case has been authorised.

## Read-only triage before any modified forcing variant

Use the existing Stage13 detailed TSV reports to recover: exact 2016 negative-FSDS QC code and solar elevation, 2014 ACCESS negative-point elevation distribution (night below -6 vs twilight -6..0), and the 2018 high-wind record with native Ws_QCFlag. Do not assume all below-horizon radiation is deep nighttime. If the science decision approves, create a **NEW separately named** provisional candidate differing *only* where FSDS<0 and modelled sun is below the horizon; preserve all six source-faithful DATMs and require exact source-index, annual energy-difference, and per-variable identity checks.

## PFT/soil/surface science requirements

- Site `-22.2828, 133.2493`; tower 13.7m; source-selected Ta/Ws 11.6m, Fsd/Fld 12.2m, source pressure tagged 23m, SH source height unspecified. **ZBOT 11.6m remains candidate**, not final scientific approval.
- L6 describes Mulga canopy `Acacia aneura` and `A. aptaneura`; C3 perennial grass and forbs/shrubs; C4 perennial and annual grasses; red kandosol / sandy loam; L6 canopy height 4.4m. Do not invent exact FATES PFT fractions from these species names.
- Recent TERN description reports **74% sand, 11% silt, 15% clay** and median 4.3m canopy height. Older OzFlux site page instead describes red sandy clay and a 6.5m mean canopy; reconcile period and method before treating descriptions as site-specific model input. A reported research-site Acacia cover of ~74.5% is NOT automatically the model grid-cell woody PFT cover.
- Retain **bare soil**, and distinguish woody Mulga, C3 herbaceous/shrub and C4 grass choices; validate FATES PFT indices/trait file and surface PFT fractions. Independently validate vertical soil texture, surface file, and native simulated 2016 NOLEAP chronology before any short trial or AD400.

Primary references:
- https://portal.tern.org.au/metadata/7d9d2f7f-794c-41f5-b5e1-d5b58fc08743
- https://ozflux.org.au/monitoringsites/alicesprings/alicesprings_description.html
- https://github.com/OzFlux/PyFluxPro/blob/main/scripts/pfp_gf.py

**Status:** Source data unchanged, six original provisional DATM files unchanged, science approval FALSE, no model submission.

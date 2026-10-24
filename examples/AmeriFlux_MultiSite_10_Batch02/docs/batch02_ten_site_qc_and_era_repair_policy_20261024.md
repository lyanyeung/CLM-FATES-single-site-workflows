# AmeriFlux Batch02 — Ten-site meteorology QC and external ERA humidity-repair policy

**Created 24 October 2026. Applies to all ten exact releases in sites.tsv. Scientific stage: screening and repair-eligibility, NOT final forcing/model approval.**

## Site-by-site operator summary

All ten original releases were uploaded, extracted and preflighted; reference CTSM surfaces (year 2000) were generated. This does not establish FATES vegetation composition, soil/permafrost representativeness or admissible model forcing.

| Site | IGBP | Stage07 outcome | Stage07 changed variable records | Stage07 original QC0 edits in candidate | Stage07 unresolved humidity rows | Pre-model scientific review |
|---|---|---|---:|---:|---:|---|
| US-BZS | ENF | Numeric candidate | 87 | 1 | 0 | Original QC0 edit, permafrost peat/forest footprint and PFT |
| US-CMW | DBF | Numeric candidate | 44 | 2 | 0 | Original QC0 edits, extensive low positive RH flags |
| US-EML | OSH | BLOCKED | — | — | 1,327 | Humidity source/MDS and winter, shrubland/OSH representation |
| US-GLE | ENF | BLOCKED | — | — | 295 | Site T/VPD phase checks, conflicting source humidity |
| US-Ha1 | DBF | Numeric candidate | 30 | 2 | 0 | QC0 edits; preserve native 60-minute (HR) resolution |
| US-Ho1 | ENF | BLOCKED | — | — | 937 | **Top priority** site-specific TA_ERA/QC2, original clock, humidity |
| US-Ho2 | ENF | Numeric candidate | 757 | 19 | 0 | **19** QC0 edits, sensor/source dependence with Ho1/Ho3 |
| US-Ho3 | ENF | Numeric candidate | 45 | 0 | 0 | Howland common-source dependence; no independent proof |
| US-ICh | OSH | BLOCKED | — | — | 169 | Ice/water phase humidity and shrub/tundra representation |
| US-ICt | OSH | BLOCKED | — | — | 2,176 | **Top priority** severe extensive humidity/ice issue and OSH |

**Denominator caveat:** Stage07's five BLOCKED sources total **4,904** initial humidity rows (1327 + 295 + 937 + 169 + 2176). Stage08's later strictly reconciled review list comprises **4,884** rows. Do not describe these different stages as identical lists or allocate 4,884 per-site counts without the exact Stage08 ledger. The five Stage07 numeric candidates together contain **963** changed variable records and **24** QC0 edits (87 + 44 + 30 + 757 + 45, with 1 + 2 + 2 + 19 + 0 original QC0). **All require review**; numeric pass is not an approved forcing. No Batch02 DATM/CIME or spinup has been approved.

## Scientific HOLD census from Stages 11–47

- Stage08/11 exact unresolved science cohort: **4,884** from the five humidity-blocked stations; zero approved forcing substitutions.
- Stage31 original retained-T provenance within 4,884: **938 QC0**, **3,945 QC2**, **1 QC1**. Strictly separate site-measured T from site-downscaled ERA T.
- Stage32 mutually exclusive review routes across 4,884: P0 Ho1 clock/source hold **917**; P1 negative dewpoint-transfer water-VPD at remaining sites **6**; P2 ice phase **2,773**; P3 temperature representativeness **818**; P4 unvalidated humidity **370**. NONE are approvals.
- Stages 35–47: Ho1 **425** negative water-VPD dewpoint-transfer conflicts using original QC2 T; 106 have any neighbouring original QC0 temperature, **319** have none (1998 64, 1999 25, 2001 230). The 319 are distributed original Ho1 TA_F=TA_ERA and have low-quality MDS source flag 3, not independent temperature verification.
- Stage40–41 independent-location Bangor GHCNh source-QC screen paired **316/319** Ho1 timestamps against **197** distinct weather reports, three equally-near conflicting reports excluded. Across unique NOAA reports, mean absolute difference to Ho1 QC2 T **12.881°C** versus CDS ERA5 T **1.274°C**. Bangor is ~46 km from Howland; forest microclimate and sensor lineage remain unresolved.
- Stage46–47: all **274,148** original Ho1 measured-coded consolidated TA_F_QC0 records are exactly numerically equal to original TA_F_MDS_QC0. Ho1 original QC0 vs processed TA_ERA empirical RMSE **7.7346°C**, Pearson r **0.71944**, versus AUXMETEO reported ERA_RMSE **4.66°C**, ERA_CORRELATION **0.72**. The calibration population is unknown. In the 319 held records original MDS_QC=3, MDS-vs-ERA MAE: 1998 **18.9695°C**, 1999 **17.3777°C**, 2001 **2.5314°C**. MDS_QC3 is not a substitute for observation.

## New Batch02 rule: negative VPD, nonphysical RH and extreme dryness

### Detection at native source resolution

| Condition | Operational label | Default action |
|---|---|---|
| Water-basis VPD < -0.005 hPa | HARD_NEG_VPD | Flag for automatic **external-ERA repair eligibility** only after T/QC and provenance gates |
| -0.005 <= VPD < 0 hPa | ROUNDING_OR_SUPERSAT_REVIEW | Keep original; review precision, fog and phase; do not silently convert to ERA |
| Raw primary RH < 0% | HARD_NEG_RH | Flag for external-ERA humidity replacement eligibility after source/time/temperature gates |
| Raw RH = 0% | ZERO_RH_REVIEW | Serious physical suspicion; require external validation and timestamp/QC check |
| 0% < raw RH < **1%** | EXTREME_DRY_P1 | **Manual-high** until independent corroboration; real very dry air is possible |
| 1% <= RH < 5% | DRY_P2 | Review and retain by default |
| 5% <= RH < 10% | DRY_P3 | Advisory only |
| Inferred water RH from T/VPD < 0% or actual vapour pressure <= 0 | HARD_NEG_ACTUAL_VAPOR | Flag hard inconsistent humidity pair; original T/VPD may come from different processing chains |
| Water-derived RH > 101%, or RH over ice >100% when T<0°C | PHASE_SUPERSAT_CAUTION | Review water vs ice, fog, phase convention and sensor source before any correction |

**Physical interpretation:** VPD and RH are defined relative to a saturation surface (water/ice). Small water-supersaturation and ice-supersaturation can be physically plausible. The -0.005 hPa tolerance is the previous Stage23 numerical water screen, NOT a universal atmospheric constant. Very small positive RH (1% and below) is unusual but not automatically impossible. Inferred RH from T/VPD is not independent RH sensor evidence. Do not count overlapping predicates as distinct affected timestamps.

### External source selection — MUST be independently retrieved and audited

1. Preferred: CDS ERA5 on the verified station/grid/UTC coordinate, containing **2 m air T (K), 2 m dewpoint (K), surface pressure (Pa)**. ERA5-Land is an allowed alternative only if the same validation gates pass, especially for OSH/tundra, snow, cold surfaces, site elevation and ~9 km representativeness. Neither source is universally closer to a tower.
2. Reject automatic use of a same-release FLUXNET companion `TA_ERA`, `VPD_ERA` or filename `ERA5_HH`: Stage44 proved Ho1 ERA5_HH `TA_ERA` was a **duplicate** of the FULLSET processed `TA_ERA` in all 52,560 target-year records.
3. Preserve exact source NetCDF/CSV SHA256, original timestamp/local-to-UTC evidence, metadata/BIF/BADM, variables, interpolation method and native HH/HR interval. Full year/site external data are **not verified available for all ten releases**; existing Stage15–19 ERA5 receipts cover targeted site-years of five blocked sites only. Do not silently extrapolate this coverage.
4. Compute ERA RH over water consistently from the ERA T and dewpoint. Before eligibility require physically valid original pressure, no invalid external T/Td/p, ERA Td <= ERA T or documented phase/supersaturation handling, and check T_site versus T_ERA. External source being numerical-valid is not proof it is ecologically representative.

### Candidate building (not source replacement)

- For **good observed-coded original T (QC0)** with independently verified UTC/site/source, plausible pressure and abs(T_site - T_ERA) <= 8°C: for a verified **hard humidity** defect, mark **CONDITIONAL_ERA_HUMIDITY_CANDIDATE_ONLY**. Preserve T_site, derive candidate VPD and QBOT from the *same* ERA T/Td RH and the site's retained T/pressure. Recompute and check saturation, 0 <= VPD, 0 < QBOT < 0.08, no changed PA/TA, native timestamps. This 8°C gate is a conservative review criterion inherited from historical V5, not a proven sensor accuracy bound.
- For raw positive RH <1%, **no unconditional replacement**. Candidate eligibility requires additional contrary external evidence, RH/QC/source and episode manual science review; do not turn true dry spells into wetter reanalysis simply because ERA RH differs.
- For original T **QC2**, suspect T, unresolved local-to-UTC/height or Ho1-like 319 cases: **MANUAL_T_AND_HUMIDITY_JOINT_REVIEW**. A humidity-only substitution at wrong T would preserve the physical contradiction; proposed joint ERA T+humidity+pressure changes require an independent temperature source evaluation and an auditable separate full-state candidate.
- All ten sites require exact native timestamp and historical source QC checks. Any low RH, VPD, sign/phase, UTC, resolution, spatial or origin conflict is a fail-closed HOLD, **not** an instruction to arbitrarily interpolate or clip RH.

### Implementation status and permissions

`scripts/stage48/48_audit_ten_site_vpd_rh_era_repair_rule.py` implements the thresholds, a pure ERA humidity candidate calculation with explicit source/UTC/elevation/T-QC requirements, and an original 10-site read-only scanner. Use the exact, existing SHA256-pinned Stage04b `source_inventory.json` for `--check` and `--audit`; source CSVs are hashed before full scan. It prints each site's raw-source anomaly categories and examples, **not** prospective model forcing or repair files. The Stage48 live ten-site counts are **pending IRIDIS6 audit**, so none have been invented here.

**Rule recorded; zero old Stage07/08 candidates or raw sources overwritten, no repair ledger accepted and no spinup approval.** To actually implement automatically repaired NetCDF/forcing, first review the Stage48 original-source count and prove independently sourced CDS ERA5/ERA5-Land coverage and physical/temporal equivalence for every proposed changed record. Keep source and candidate side by side with a timestamp/QC/source checksum ledger.

References: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ ; https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries ; https://confluence.ecmwf.int/pages/viewpage.action?pageId=690470575 .

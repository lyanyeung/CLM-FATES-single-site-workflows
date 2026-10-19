# Meteorological forcing: Stage 20–28 decisions and outstanding uncertainty

**Snapshot:** 18 October 2026. This record describes a *provisional research forcing* generated for 13 FLUXNET sites. Numerical pass, source integrity and successful NetCDF writing are not equivalent to scientific approval of all half-hourly measurements or gap fills.

## Inputs, lineage and retention of original observations

The 13-site pipeline initially reused the tested 8-site QC-v5 transformation. The historical stages 00–19 are retained in the parent README and scripts directories, with separate experimental alternatives for ES-LJu temperature/VPD and pressure. The subsequent selected Stage 28 meteorology is derived from Stage 26, itself inheriting selected Stage 22 results. It is **not** simply the original v5 product.

The Stage 20 experiment made 58 additional provisional site-variable / half-hour decisions for DE-Gri (11) and FI-Let (47); Stage 21 made no further edits. Its intermediate review left 74 MDS blocks unresolved. Stage 22 used a whole-contiguous-QC1-run method: it should **not** be confused with an earlier attempt that stopped due to an already-existing output directory. Stage 26 included a selected FI-Hyy VPD half-hour candidate. Stage 28 revisited seven sites — ES-LJu, DE-Gri, FI-Let, FR-Pue, GF-Guy, IT-MBo, IT-Col — and made **zero further bounded half-hour edits**. The remaining six sites inherited the Stage 26 selection.

For source lineage, use each stage's selected manifest and SHA256 files rather than inferring the parent from the newest script filename. The **selected Stage 28 reports** are under:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_MET_stage28_20261018_052344_851367/reports/`

Important files include `01_selected_13site_STAGE28_provisional_manifest.csv`, `02_all13_full_numeric_QC_after_stage28.csv`, `03_13site_science_risk_and_decisions.csv`, `04_exact_STAGE28_new_edits.csv`, `07_7site_heavy_rain_PROVENANCE_NO_EDITS.csv`, `08_DEGri_FILet_82_MDS_original_blocks_science_pending.csv` and `11_provenance_and_science_gates.json`. The originals live on IRIDIS and **are not distributed on GitHub**.

## Stage 28 numerical checks versus scientific review

Stage 28 reports **13/13 sites numeric hard-QC PASS** on the selected forcing. Its MDS ledger still holds **69 flagged original blocks**, **49 DE-Gri and 20 FI-Let**. A flagged MDS block is not automatically an incorrect tower measurement; source QC, contiguous run context, measured QC0 anchors and independent reanalysis agreement should all inform adjudication.

### Site-specific high-priority cases

| Site(s) | Issue requiring additional science review | Handling in selected forcing |
|---|---|---|
| **DE-Gri / FI-Let** | 49 / 20 remaining original MDS blocks; long filled runs and continuity at boundaries | Preserve conservative previous selection; no blanket forcing of unresolved blocks through reanalysis |
| **ES-LJu** | Very heavy precipitation and a suspicious concentration of rainfall at **23:00** that could reflect daily accumulation or timestamp conventions | **No automatic Stage 28 rainfall edits**; verify original instrument data/time intervals before time redistribution |
| **FR-Pue / GF-Guy / IT-MBo / IT-Tor** | Individual high precipitation values; check physical plausibility and accumulation periods | Retain flagged extremes as provisional rather than clipping on magnitude alone |
| **DE-Lnf / IT-Col** | Residual half-hourly temperature/humidity consistency flags | Keep numerical screens separate from the height-assumption decision |
| **FI-Hyy** | VPD candidate refinement and substantial air-temperature versus wind measurement-height mismatch | Candidate forcing retained; wind was not vertically extrapolated |
| **All sites** | QC=0 observations, humidity-derived QBOT, VPD and pressure interactions | A reanalysis discrepancy is supporting evidence, not proof of a tower error; do not assume all reconstructed humidity is directly observed |

Physical checks included (among others) large adjacent 30-minute air-temperature jumps, extreme/low reconstructed relative humidity, precipitation event thresholds and source/QC transitions. The Stage 28 records also document remaining large temperature jumps and >40 mm/30-minute precipitation events. A threshold exceedance is an audit flag, **not automatic grounds to delete an extreme**.

**Timezone caution:** a clock-time concentration of precipitation (e.g., 23:00) is a motivation to inspect the official site time convention and instrument accumulation period; do not make an unverified timezone conversion or split one record evenly across 48 half-hours.

**Original product caveat:** IT-Col uses FLUXNET2015 FULLSET HH with **ERAI_HH** (ERA-Interim companion), not the later ICOS ERA5_HH pairing used elsewhere in the study. Network `_F` and QC codes can describe gap-filled data, and individual site data rights apply.

## Status and scientific gate

Stage 28 **passed numeric hard-QC for all 13** and became the selected input to Stage 29b/30. **Scientific approval is NONE**. These provisional inputs can support transparent trial simulations, but final publication analyses should revisit precipitation timing (especially ES-LJu), original MDS gap-fill blocks, sensor-height representativeness, source continuity and sensitivity of ecosystem pools to forcing choices.

The GitHub code is provided to document exact decisions. Do not rerun into previous experiment directories, overwrite frozen source manifests, or publish licensed FLUXNET observations, processed forcing CSV/NetCDF, ERA caches or access information.

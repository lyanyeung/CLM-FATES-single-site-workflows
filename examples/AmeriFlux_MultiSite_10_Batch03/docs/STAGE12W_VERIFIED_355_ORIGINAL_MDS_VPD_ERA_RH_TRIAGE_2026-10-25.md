# Stage12w VERIFIED — 355 original MDS VPD invalidities, hypothetical ERA-RH triage (2026-10-25)

**Operator IRIDIS6 source SHA/syntax, --self-test, --check and --run PASS**, report only:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12w_355_original_MDS_VPD_companion_ERA_RH_physics_triage_20261025T192422Z_10358cc7/`

The exact original 355 QC1 MDS VPD versus measured QC0 T impossible values are preserved, original 86 science held events (38 VPD/48 T) plus earlier 233 physical holds stay protected. All 355 paired native companion ERA RH, below-zero phase and candidate QBOT/VPD basic physics checks pass, but other important guards reject hypothetical source transfers.

| Site/year | 355 original MDS invalid | Stage12w diagnostic available-neighbor pass, **not approved** | ERA temperature >5C mismatch | Candidate >4hPa difference to existing Stage12g neighbor | Stage12g preexisting finite |
|---|---:|---:|---:|---:|---:|
| US-Me6 2015 | 115 | 91 | 6 | 18 | 94 |
| US-Me6 2017 | 114 | 80 | 22 | 12 | 89 |
| US-NR1 2022 | 126 | 104 | 16 | 6 | 104 |
| **TOTAL** | **355** | **275** | **44** | **36** | **287** |

**Intersection reconstruction** from verified site-year/class counts: among Stage12g source population 287 finite and **68 missing**. Of the **275 diagnostic passes**, 274 were previously finite in Stage12g, and **one US-Me6 2017** remains missing. Among **44** ERA temperature mismatch, 12 preexisting finite Stage12g / 32 missing. Among **36** candidate >4hPa jump, 1 preexisting finite / 35 missing. **13** existing finite Stage12g values are flagged by the *different newly tested original companion ERA-RH candidate*; this is not evidence that earlier finite Stage12g method/value is wrong. Must compare each original source and historical D/E/G provenance before drawing conclusions.

The Stage12w candidate RH derives from paired original ERA `TA_ERA/VPD_ERA` at unchanged original tower T and Stage12g PSRF; existing Stage12g values may originate from Stage12c, Stage12d, or independent ERA5-Land grids. Passing only physically available immediate-neighbor tests is a **diagnostic**, NOT full-series, event, site or forcing approval. Zero source modifications, zero Post-v5/DATM/CIME/Slurm/spinup.

**Stage12x follow-up:** exact original source/provenance reconciliation of the 68 remaining missing Stage12g native rows and 13 already finite Stage12g source rows with new hypothetical-candidate warnings; inspect the sole diagnostic-pass-but-missing native row with signed ±6h native context. Keep 86+233 holds and all 4hPa, 5C, ice/QBOT safeguards unchanged.

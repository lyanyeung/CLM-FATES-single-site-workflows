# AmeriFlux Batch 04 — Stage01 verified extraction and structure inventory

**Operator execution evidence:** IRIDIS6 terminal output supplied on 2026-10-24. This record reports the operator output; it does not imply independent live access to the cluster.

**Status:** `BATCH04 SUMMARY: 10/10 PASS (extraction/structure only); failures: none`

- Original exact release packages: 10/10 found.
- Original ZIPs preserved in `forcing/packages/`, extracted CSVs in each site-specific `forcing/raw/<package>/`.
- 16 CSVs extracted per station, **160 CSVs** in total.
- Every station: 1 BIF, 1 FLUXMET_HH, 1 ERA5_HH; 0 FLUXMET_HR reported.
- ERA5_HH filename period is 1981–2025 for all ten; this is a file label, not assessed continuous valid observations.
- No FLUXES_HH/HR CSV found in these release packages; this is not evidence of a broken FLUXMET forcing package.
- Syntax and 10/10 source preflight passed before extraction.
- Stage01 only validated CSV extraction/size/CRC, product structure and first meteorology headers. It did **not** validate complete time series, QC physics, vegetation/PFT mapping, sensor heights or model readiness.

| Site | CSV | FLUXMET_HH columns | Result |
| --- | ---: | ---: | --- |
| US-Rpf | 16 | 251 | PASS |
| US-Seg | 16 | 218 | PASS |
| US-Ses | 16 | 218 | PASS |
| US-Slt | 16 | 222 | PASS |
| US-SP1 | 16 | 223 | PASS |
| US-SRG | 16 | 243 | PASS |
| US-SRM | 16 | 251 | PASS |
| US-Syv | 16 | 225 | PASS |
| US-Ton | 16 | 238 | PASS |
| US-Uaf | 16 | 211 | PASS |

**Native Stage01 JSON report on IRIDIS6:**

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/reports/stage01_extraction_20261024T081316Z_01886693.json
```

**Next step:** Run published **read-only** `scripts/stage02/02_check_batch04_metadata.py` (BIF coordinates, IGBP categories, height evidence, source first HH interval). Unresolved coordinates should be left as an explicit failure/review, not silently replaced by another site's values or a coarse grid.

**Stage01 approval boundary:** Extraction/structure PASS only. **Zero QC repairs approved**, no DATM/forcing generation, surface/PFT parameter assignment or CLM-FATES model execution.

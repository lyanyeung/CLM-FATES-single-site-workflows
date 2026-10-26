# Official US-GLE BIF 2026-09-08 — observed vegetation and historical forcing boundary

Source: user-supplied `AMF_US-GLE_BIF_20260908.xlsx`, sheet `AMF-BIF`, 322 metadata rows, SHA256 `9012ac6594cc10d0beb102abb8ee189837835b06ff0d595b122bacd17f231279`, AmeriFlux BASE US-GLE DOI `10.17190/AMF/1246056` version 9-5 (2026). This is the primary evidence, not a guessed gridded PFT map.

## Direct BIF facts
- `GRP_IGBP / IGBP = ENF`.
- `GRP_IGBP / IGBP_COMMENT = 85% Engelmann spruce 15% Subalpine fir`. These are two evergreen needleleaf conifers; under a coarse ENF-oriented FATES PFT system the **natural forest PFT candidate** is ENF=100%, species detail recorded as 85/15. **CAUTION:** BIF does **not specify whether 85/15 represents stem count, basal area, canopy cover, or standing forest area and gives no applicable measurement date**. Do not call these species percentages the fraction of *the entire tower footprint*.
- `GRP_DOM_DIST_MGMT = Pests and disease`.
- `GRP_SITE_DESC`: decade-long spruce-beetle outbreak peaking in **2008** caused **85% of forested basal area mortality**, NOT a statement that the site was 85% deforested or 85% crop.
- Forest age mixture spans very old trees (>400yr) and younger cohorts; do not infer a single initial age.
- `GRP_LOCATION`: LAT=41.3665, LON=-106.2399, ELEV=3197 m; **LOCATION_COMMENT = Change reflects location of new tower**. The source BIF release coordinates may not match every past flux-tower configuration. Compare these values against the exact 2005–2020 Stage102 forcing and CTSM surface coordinates before CIME case release; confirm any documented site relocation.
- `GRP_UTC_OFFSET = -7`, comment says added by AMF data-processing team for QAQC. Matches Stage101 solar evidence; original forcing local-standard-time and CIME clock remapping still subject to actual model interpretation.
- `GRP_FLUX_MEASUREMENTS`: EC CO2, H and H2O observations begin **1999** (does not mean single unchanged instrument position).
- `GRP_HEIGHTC`: **canopy height**, NOT sensor height. 2010 mean=8.2m (190 samples), 2011 mean=14.9m (271), 2018-08 mean=7.2m (217), 2019-09 mean=8.6m (414). Independent samples/definitions must be reviewed: these values cannot be treated as a directly comparable annual canopy-growth curve or substituted for `TA_F` ZBOT=23.4m and `WS_F` measurement height=22.65m.
- Actual Stage103 gridded reference landunits at US-GLE: NATVEG **92.485561%**, CROP **7.514439%**. This is **grid context**, not proof that the flux footprint contains crop. No reference surface change is authorized yet.

## Immediate next decision: remove artificial 2020 meteorological seam without pretending to have 2004 observations

Stage104 actual measured artificial UTC seam at `2005-01-01 07:15`: TBOT **+4.332K** (native P99 abs change 1.762K), PSRF **-665 Pa** (P99 62Pa), WIND **+2.823m/s** (P99 2.06783m/s). This is highly unusual, so DO NOT submit even a short model run on the Stage102 periodic surrogate before investigating.

Key conversion: the 14 unobserved model times `2005-01-01 00:15–06:45 UTC` correspond to original **2004-12-31 17:00–23:30 local standard time** at UTC-7. To fill them from reanalysis, one needs the **2005-01-01 00:00–06:30 UTC** ERA5/ERA5-Land hours, *not necessarily ERA data labeled 2004*. Existing Stage07 comparison `ERA5_HH` is aligned to source local timestamps and must not be mistaken for UTC without proof. A credible 7h ERA5 backfill requires exact UTC provenance, native variables and physical units, orography/pressure and measurement height reconciliation, and seam-to-observed checks.

The public [Copernicus ERA5-Land catalogue](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land) provides hourly records for January 2005. Prefer the original verified site-specific ERA source where it includes these UTC hours; otherwise issue a small CDS request. Reanalyzed values must remain separately labeled and the original 215+16 NC immutable. Site startup, FATES PFT and CIME timing remain scientific HOLD.

Official supporting site descriptions: https://ameriflux.lbl.gov/sites/siteinfo/US-GLE and https://research.fs.usda.gov/rmrs/projects/glees.

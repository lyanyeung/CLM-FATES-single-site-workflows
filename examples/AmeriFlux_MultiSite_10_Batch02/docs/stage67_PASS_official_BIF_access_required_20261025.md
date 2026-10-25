# Stage67 IRIDIS6 PASS — 254,579 BIF rows inspected; target BIF not locally available

Operator report: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage67_BIF_actual_source_forensic_and_official_staging_20261025T064106Z_91002c73`.

Stage67 pinned Git blob `36c9d2f5c2381e8cd140a8ed54ab04a0f8688514` passed SHA download, self-test, check, and audit. It independently interrogated the 64-file Stage66 inventory.

- Total BIF records actually parsed: **254,579**, across 37 files.
- Four `FILE_LARGER_THAN_PARSE_LIMIT` errors are big raw **US-Ho1 / US-BZS FLUXNET FULLSET and in-package ERA5 companion CSVs**, not BIF metadata; it is correct to avoid interpreting these as metadata.
- Actual `SITE_ID==US-Ho1` BIF rows: **0**; actual `SITE_ID==US-BZS` BIF rows: **0**; source-matched UTC offset groups: 0.
- New independent official BADM import directory `~/AmeriFlux_Batch02_official_BIF` did not exist at runtime. No official data downloaded. Neither existing 9,389 source-verified water humidity candidates nor 16,943 HOLDs were modified.

Scientific conclusion: Stop repeatedly scanning the same site folders or other-site ZIP packages. Missing BIF evidence, not water-humidity physics or a general CSV/XLSX decoding failure, is now the binding dependency for US-Ho1 (16,788 hard events) and US-BZS (86 hard events).

## Official BADM acquisition requirements

AmeriFlux documentation confirms published site-specific BIF `AMF_<SITE_ID>_BIF_YYYYMMDD.xlsx`, aggregated `AMF_AA-Flx_BIF_*` / `AMF_AA-Net_BIF_*`, and BADM packaged inside BASE-BADM. Download requires an AmeriFlux account and adherence to site data-use terms. Do not invent a direct downloadable URL or use credentials without user's explicit authorisation.

Official reference links:
- https://ameriflux.lbl.gov/data/badm/
- https://ameriflux.lbl.gov/data/aboutdata/badm-data-product/
- https://ameriflux.lbl.gov/data/download-data/
- https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1
- https://ameriflux.lbl.gov/sites/siteinfo/US-BZS
- https://search.r-project.org/CRAN/refmans/amerifluxr/html/amf_download_bif.html

Confirmed version identities for correspondence / access to **matching historical site timestamps**:
- US-Ho1 original FLUXNET-1F **3-6**, 1996–2023: https://doi.org/10.17190/AMF/2469453
- US-BZS original FLUXNET-1F **5-7**, 2010–2024: https://doi.org/10.17190/AMF/1881572

After user uses their authorised browser session to download official `AMF_US-Ho1_BIF_*.xlsx`, `AMF_US-BZS_BIF_*.xlsx`, `AMF_AA-Flx_BIF_*.xlsx`, or official BASE-BADM ZIP, stage the unmodified files at `~/AmeriFlux_Batch02_official_BIF` on IRIDIS6, preserving original filenames.

Then rerun existing Stage67 script with `--official-dir ~/AmeriFlux_Batch02_official_BIF --audit` (or `--check`). Stage67 parses and lists `UTC_OFFSET`, `UTC_OFFSET_DATE_START` / `GROUP_ID` but marks official publisher authentication and time applicability **not yet verified**. Before releasing Ho1/BZS time joins, verify official file receipt/source URL, downloadable product license, timestamp convention (local standard time), period coverage, and crosswalk with original source version/site.

**Do not automatically use UTC-5 for Ho1 or UTC-9 for BZS based only on geography.** BADM `UTC_OFFSET_DATE_START` can vary and all target source timestamps must be covered. The extra 69 source-temperature HOLD events remain a separate problem.

No original observation, downloaded independent CDS payload, DATM, NetCDF forcing, CIME/Slurm or spinup writes were performed.

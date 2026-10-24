# Stage64 verified PASS; Stage65 CSV/XLSX BIF and 69 T HOLD audit

Stage64 was run and verified by operator on IRIDIS6. Report:
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage64_9389_unique_ERA5_humidity_candidates_20261024T232045Z_c8678d94

Exactly 26,332 original hard humidity source events reconciled: 9,389 distinct original-T/PA plus independent CDS ERA5 water-humidity candidate replacements (4,411 Stage60 + 4,801 Stage62 +177 Stage63); 16,788 US-Ho1 original time provenance HOLD, 86 US-BZS missing source BIF HOLD and 69 original EC temperature QC HOLD (48 warm, 12 temporal discontinuity, 9 QC neighbor insufficiency). Original hard HOLD total 16,943. A separate 100 unique positive RH<1%-only source review events exist. All original and DATM forcing source files remain unchanged; no spinups authorized.

Official AmeriFlux BADM documents state site BIF can have the name AMF_SITE_BIF_YYYYMMDD.xlsx. Earlier scripts looked mainly for *_BIF_*.csv. Site timestamp is LOCAL STANDARD TIME, not daylight-saving time; actual per-release UTC_OFFSET still requires valid source metadata.
https://ameriflux.lbl.gov/data/aboutdata/badm-data-product/
https://ameriflux.lbl.gov/data/aboutdata/data-variables/
https://ameriflux.lbl.gov/sites/siteinfo/US-BZS
https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1

Stage65 source: scripts/stage65/65_find_official_release_BIF_xlsx_and_triage_69.py

Stage65 will verify Stage63/64 SHA manifests, then scan bounded original-source folders for CSV/XLSX BIF files and ZIP packages, parse SITE_ID, VARIABLE and DATAVALUE using Python standard library including XLSX ZIP/XML, require unique physically valid LOCATION_LAT, LOCATION_LONG and UTC_OFFSET, and only mark same-release BIF if the containing ZIP has the identical original FLUXNET primary CSV SHA256. Standalone/current BADM is evidence only, not proof of the exact source release. It also inventories all 69 T HOLD events and possible US-ICh sensor-bound plateaus without approving questionable temperatures.

Commit ec8f720b873b4445981be171e067b38726e499d8; Stage65 Git blob 6cef393ba8666e3ae9454dbb2b64822c3e8b76b7.

Run pinned script on IRIDIS6 with the existing clm_fates_env. Stage65 --self-test, --check, --audit are supported. Successful audit marker:
STAGE65 AUDIT PASS | searched real CSV/XLSX/ZIP BIF candidates; 69 temperature HOLD triaged

No original observation, CDS payload, DATM forcing, netCDF, CIME, Slurm or model run modified. Stage65 has been committed, but not executed on IRIDIS6.

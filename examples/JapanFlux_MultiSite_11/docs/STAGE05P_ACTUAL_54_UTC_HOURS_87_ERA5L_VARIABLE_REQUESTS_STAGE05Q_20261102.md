# JapanFlux Stage05P — actual three-site ERA5-Land hourly request-plan result (2026-11-02)

## Actual operator stdout

The operator executed [Stage05P](../scripts/stage05/05p_prepare_3site_ERA5Land_hourly_UTC_reference_request_NO_CDS.py) on IRIDIS6 using the Stage05O source-provenance-gated UTC and native-HOLD tables:

```
STAGE05P SELF-TEST PASS | 3-site UTC provenance, hour grid algebra, unit contracts; NO WRITES
STAGE05P REQUEST PLAN PASS | NO CDS API, NO ZIP, NO SLURM
UTC_VERIFIED_SITE_COUNT 3 /5
UTC_SOURCE_FIELDS 27 NATIVE_TIME_HOLD_FIELDS 18
UNIQUE_SITE_UTC_HOURS 54
VARIABLE_HOUR_PAIRS 87
VARIABLES {'surface_pressure': 54, '2m_temperature': 9, 'surface_thermal_radiation_downwards': 24}
SITE_COORDINATES HOLD_NOT_YET_ORIGIN_VERIFIED
EVENT_PLAN /home/ly3n24/japanflux_stage05p/run_20261102T021152Z/stage05p_27_source_UTC_event_ERA5L_mapping_plan.tsv
HOURLY_REQUEST_PLAN /home/ly3n24/japanflux_stage05p/run_20261102T021152Z/stage05p_hourly_ERA5L_request_plan_no_coordinates.tsv
SUMMARY /home/ly3n24/japanflux_stage05p/run_20261102T021152Z/stage05p_reference_request_summary.json
NO INDEPENDENT ERA VALUES ACQUIRED OR REPAIR APPROVED
```

**Interpretation:** the plan requires **54 distinct site×UTC hours**, and **87 site×UTC hour×variable combinations** (54 pressure, 9 air temperature, 24 downward longwave) because variables overlap some hours. It does **NOT** mean 87 grid cells, 87 source anomalies, or 54 observations already received. The three verified local-standard-time (BIF+README) source sites are JP-Fjy, JP-Khw and JP-Yms with **27 source-selected field candidates at 21 unique station×native-half-hour keys**. JP-Tef and JP-Tmd remain **18 fields / 14 station×native-half-hours native-only HOLD** because their original README explicitly says *local solar time* despite original BIF UTC_OFFSET=+9. The Stage05P output covers limited ±3-hour context for the three verified sites.

Original source archives, model forcing and cases remain untouched; **NO CDS or other independent ECMWF data retrieval yet**. All 45 original-source field candidates across 35 station×half-hours remain science HOLD.

## Next metadata gate: authoritative BADM source coordinates

Official FLUXNET/AmeriFlux BADM BIF format comprises **site ID, group ID, group name, variable name, and value** (https://fluxnet.org/badm-data-product/). The official BADM LOCATION group contains required `LOCATION_LAT` (WGS84 decimal degrees) and `LOCATION_LONG` (WGS84 decimal degrees), and optional `LOCATION_ELEV` (metres above sea level), plus `LOCATION_DATE_START` and `LOCATION_COMMENT` (https://ameriflux.lbl.gov/data/badm/badm-standards/LOCATION). Multiple LOCATION group instances can be provided for the same site, so **never blindly choose the first record** or infer a location from an unrelated website when authoritative original BIF data are available.

[Stage05Q original BIF coordinate forensic](../scripts/stage05/05q_three_site_source_BIF_LOCATION_coordinates_READONLY_NO_CDS.py) (committed code, **not yet run on real IRIDIS6 original ZIPs**) must read ONLY the small `*_FLUXNET_BIF_*.csv` source member from the original nested JPF packages (one site in RAM at a time). It verifies original source BIF SHA256 against the previously saved Stage05K source metadata, matches official `LOCATION_*` variables by shared original group ID and source line, verifies `UTC_OFFSET=9` in the original site BIF and all source metadata gate outcomes, then checks for contradictory/missing location values. Only if all three source coordinates and optional elevations are unambiguous does it write `stage05q_original_BIF_verified3_CDS_coordinate_roster.tsv`; it always writes an audit JSON and candidate location rows.

Coordinates identify the tower location, **not automatically the correct ERA5-Land grid-cell or representativeness**. Downscaled JPF `*_ERA` fields are not equivalent to unmodified ECMWF ERA5 or ERA5-Land. After Stage05Q succeeds, validate elevation/grid-cell implications and create a small externally sourced 54-hour reference extraction with verified UTC pairing and ERA5-Land unit handling. The user must have appropriate CDS credentials and applicable data permissions if actual CDS API retrieval is required. Do not print or commit secrets.

## Science status

- Stage05P: **PASS, request plan generated, no external data obtained**.
- Stage05Q: **Published, first IRIDIS6 execution pending**.
- Stage05L/O: **only three BIF+README local-standard-time sites verified**; Tef/Tmd solar vs standard wording remains HOLD.
- Stage05I: **45 field candidates / 35 station half-hours all HOLD**.
- JP-Tom/Tgf separate original humidity/VPD forensics pending. No Slurm, no source ZIP edits, no derived forcing replacement, no AD400/Normal400.

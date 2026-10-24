# Batch04 US-Seg — human-approved coordinate and elevation decision

**Approval date:** 2026-10-24  
**Decision authority:** user/operator explicit scientific decision in the project discussion.  
**Status:** APPROVED FOR SITE LOCATION METADATA; downstream surface/forcing science remains separately gated.

**Operator instruction:** "US-Seg经纬度和海拔直接就用BIF1495的信息，别的不管。" The operator has explicitly selected **only** original FLUXNET BIF `GROUP_ID=1495`.

| Field | Final value | Original BIF source |
| --- | ---: | --- |
| SITE_ID | US-Seg | FLUXNET 2007–2025 v1.3 r1 |
| GROUP_ID | **1495** | original release BIF |
| LOCATION_LAT | **34.3623** | group 1495, line 47 |
| LOCATION_LONG | **-106.7020** | group 1495, line 48 |
| LOCATION_ELEV | **1596 m** | group 1495, line 46 |
| LOCATION_DATE_START | **200701010000** | group 1495, line 45 |
| IGBP | GRA | original site BIF, independent of coordinate selection |

Machine-readable approval: [../coordinate_decisions.tsv](../coordinate_decisions.tsv).

Original BIF `GROUP_ID=1479` and any independent public coordinate source **must not be used as the Batch04 US-Seg operational site location**, and should not be averaged with the approved point. Historical metadata sources and comparisons are preserved only as provenance in the [Stage02B evidence](STAGE02B_US_SEG_PROVENANCE_VERIFIED_2026-10-24.md). Original ZIP and original extracted BIF are never edited.

The [read-only Stage02 checker](../scripts/stage02/02_check_batch04_metadata.py) now reads the independent approval TSV. It accepts group 1495 **only if the original BIF shows the exact approved paired latitude, longitude, elevation and start date**, failing closed otherwise. The other nine stations still follow the original unambiguous-BIF rule. The script does not write site data, surface files, CIME cases or DATM inputs.

**Execution status:** approval and code published on GitHub, but this revised Stage02 version still requires an IRIDIS6 operator rerun before claiming **10/10 post-approval PASS**. Previously executed Stage02 (prior to approval) remains a historical **9/10** result. Separately, Stage02C time continuity was 10/10 on all sites.

**Boundaries:** this approval is for site latitude, longitude and elevation ONLY. It is not approval of `HEIGHTC` or meteorological measurement height `ZBOT`, any FATES PFT fraction, any forcing repairs, ERA substitutions, surface regeneration or spin-up.

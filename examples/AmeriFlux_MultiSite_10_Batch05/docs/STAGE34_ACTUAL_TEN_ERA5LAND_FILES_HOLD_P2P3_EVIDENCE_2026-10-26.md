# Batch05 — Stage33 10/10 real ERA5-Land reference downloads; Stage34 immediate physics/QC joins

## Stage33 actual operator execution PASS (2026-10-26)

The investigator submitted the Stage33 CDS batch, and **all ten requests succeeded**. Real downloaded files and SHA256 as confirmed by CDS API and the operator:

| CDS original source ID | Actual downloaded size | SHA256 |
|---|---:|---|
| ERA5L_US_Vcm_200802 | 20,935 | 52354b42120aebe27e1beba417be54898dea1e6fbae4d4d982d06eb74b089682 |
| ERA5L_US_Vcm_200812 | 20,935 | e443584765ab6f63326fe845d769b4cfc1baba62c93a53b467ea02e6a8294959 |
| ERA5L_US_Vcm_201512 | 20,935 | c0f941c10f1041a67f4c6a6484ce6c86ea46bc11ddd5ed619e412c3c2e624879 |
| ERA5L_US_Vcp_201101 | 20,935 | 513464f7d7d2662768e286e526b82ef8abb95a685d03d6e78e4fc975003b8f45 |
| ERA5L_US_Vcm_202510 | 20,935 | 4a87a7b91b70c213f2c6fc8e9115d68597f81ae6962232a7bac38f4fb324b987 |
| ERA5L_US_WCr_202508 | 20,935 | cd8cb50962b30b26d0a90c307041c1bbca425f1c1369c5e0327801967d7362ec |
| ERA5L_US_Vcp_200804 | 26,439 | 49cff9789dfeea27ea0611500c869c660989dbab9e216109ecee3858a1e38d8b |
| ERA5L_US_Vcp_200805 | 33,612 | 110663807b2055cceaca191508f13bc568e5944568fcc5896b0b80ccb2ee0a6d |
| ERA5L_US_Vcp_200806 | 25,863 | ab471024e17a8a343ec3ef30e60e525c270953b9047c35efbacfcb5de6ffe62f |
| ERA5L_US_Wjs_TOP1_P2P3_US-Wjs_E0031 | 20,935 | 31c86d9c4eb7e57ab81fb8e84df590a2b379287dcb2e879832b0f2ca8fe241a3 |

Original Stage33 report directory:
`/home/ly3n24/ameriflux_batch05_stage33/H01_neighbors_and_external_refs_20261026T122415Z_3242355`.

The earlier Stage30 original first US-Vcm H01 sample was **also genuinely downloaded** and parsed in Stage31; there are now **11 actual downloaded CDS research reference products** in separate output folders. They are not field observations and have not been written into any forcing.

## H01 boundary science finding requiring event-scoped human decision

Original Stage33 source-neighbour audit:

| Site/native local standard time | Original tower TA | Original selected VPD | Implied original RH over water | Original TA QC / VPD QC |
|---|---:|---:|---:|---|
| US-Vcm 2007-12-15 20:30 | -11.136°C | 2.581 hPa | **1.513015%** | QC2/QC2 |
| US-Vcm 2007-12-16 06:30 | -10.784°C | 2.588 hPa | **3.973442%** | QC2/QC2 |

Both records were marked `SUSPECT False` in Stage33 **only because the earlier simplistic screen used RH<1%**. This **must not be interpreted as independently validated source humidity**. These are original source QC2 (not measured QC0), highly dry for cold winter conditions relative to the separately downloaded ERA5-Land H01 humidity (grid RH water 67.68–78.05%). The two neighbors must remain *unchanged but review-needed*, while original H01's 19 native half-hours remain manually HELD. Stage32 water/ice phase and ±4hPa boundary results are sensitivity evidence only, not automatic approval to expand the correction window.

**No new user science repair approvals**. No requirement for user to manually review all 1,574 P2/P3 records. The human choice is eventual event-scoped (H01 repairing original 19 and perhaps original QC2 neighbors; choice of reference-to-tower moisture transport/elevation and phase conventions).

## Stage34 next: actually open, validate and compare all 10 CDS datasets

[Stage34 operator source](../scripts/stage34/34_assess_10_actual_CDS_references_against_all_P1_P2P3_and_platforms_readonly.py).

Pinned original GitHub commit `70400f8132b657742502fd05887f324bffb840dc` and source Git blob SHA `7343fe3f10554d58171ef784b18123a71eb2a90c`.

Stage34 **imports the originally successful Stage31 real NetCDF interpreter**, pinned and self-checked at Git blob SHA `a28bde14dadcaf87abaaa2d52f2eaa785e16c89f`, rather than writing another untested CDS parser. The script requires ten exact source-download hashes above and their Stage33 download manifest, verifies each actual file is recognized ZIP or NetCDF, has valid 2 m air/dewpoint fields in Kelvin, has hourly UTC continuous time coordinates for the **full actual requested dates**, and returns a site-matched grid coordinate. Source native clocks convert with original BIF −7 (New Mexico Vcm/Vcp/Wjs) or −6 (Wisconsin WCr), without DST and with BIF DATE_END still missing (conditional matching, not final validated clock proof).

It joins **original P1 27 still manually HELD half hours excluding previously reviewed H01 19**, plus all **10 original suspect RH saturation plateau HH** (not approved), plus the subset of **1,574 original P2/P3 HH** covered in the gridded reference windows. For overlapping source requests it requires the actual T/Td/RH numerical values to agree within tolerance, otherwise fails rather than silently selecting one file.

At each native half-hour, compares actual ERA5-Land reference RH (derived from water dewpoint), original selected tower T/VPD/QC and original source-processed ERA RH; for P2/P3 with original MDS, additionally compares original MDS RH. Calculates two research-only reference-to-tower VPD transfers (preserve grid RH or water vapour pressure), site-source group RH differences and strongest scientific disagreements. **No quality code reclassification** and no automatic forcing repairs.

Outputs:
- `stage34_ALL_MATCHED_EXTERNAL_ERA5LAND_REFERENCE_SCIENCE_REVIEW_ONLY.csv` — exact original native time source and gridded RH/VPD/T reference joined.
- `stage34_TEN_ACTUAL_CDS_FILE_SHA_AND_UTC_GRID_AUDIT.csv` — each actual download size/hash, 2m T/Td UTC time coverage, grid coordinates and matched original HH.
- `stage34_EVENT_GROUP_SUMMARY.json` — concise 4-site source group counts, source processed ERA RH vs grid RH >20 pp, source MDS RH vs grid RH >20 pp, which one is relatively closer by >5 pp.
- `STAGE34_REAL_REFERENCE_CROSS_SITE_SCIENCE_REPORT.md` — operator-read science status, remaining decisions, QC limitations.
- `stage34_manifest.json` — original source SHA checks and science/forcing no-write guarantees.

### Ready to run on IRIDIS6

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage34"
  COMMIT="70400f8132b657742502fd05887f324bffb840dc"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/34_assess_10_actual_CDS_references_against_all_P1_P2P3_and_platforms_readonly.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage34/34_assess_10_actual_CDS_references_against_all_P1_P2P3_and_platforms_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "7343fe3f10554d58171ef784b18123a71eb2a90c"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/reference_validation_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" \
    --stage33-dir "$HOME/ameriflux_batch05_stage33/H01_neighbors_and_external_refs_20261026T122415Z_3242355" \
    --stage18-dir "$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929" \
    --stage24-dir "$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604" \
    --stage27-dir "$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604" \
    --stage31-parser "$HOME/ameriflux_batch05_stage31/31_validate_first_ERA5Land_CDS_payload_and_Vcm_H01_readonly.py" \
    --out "$OUT" 2>&1 | tee "$BASE/stage34.log"
  echo "STAGE34_REPORTS=$OUT"
  cat "$OUT/STAGE34_REAL_REFERENCE_CROSS_SITE_SCIENCE_REPORT.md"
)
```

**Stage34 is committed to GitHub, not yet actually executed on IRIDIS6.** Actual source-reference joined record counts and gridded physics must be read from Stage34 user output before making a site/event science decision. The script makes NO CDS downloads; all 10 are already present. Previously approved 166, 46 original P1 HOLD and all original P2/P3 still unchanged. BIF UTC_OFFSET_DATE_END remains not established.

# Batch02 Stage68 — two user-provided AmeriFlux BIF workbooks, exact SHA256 and safe UTC shadow

Date: 2026-10-25. The user supplied the two original, independently downloaded AmeriFlux BIF XLSX files to ChatGPT. They have both been parsed directly by `artifact_tool` (not guessed from filenames).

| Source workbook | SHA256 | BIF rows | published UTC offset | BIF group | latitude / longitude | UTC_OFFSET_DATE_START |
| --- | --- | ---: | ---: | ---: | --- | --- |
| AMF_US-Ho1_BIF_20260527.xlsx | `24fd0a35cf5f39e49cb70fa63af6fb962cfc1bd71652aec51bd29843593ba6f1` | 426 | `-5` | 11463 | 45.2040, -68.7402 | absent |
| AMF_US-BZS_BIF_20260715.xlsx | `9f7c46d81528505ef1586600fb68fb67fb87f88dc61cbbf04e8d0e4c17b48fac` | 62 | `-9` | 87183 | 64.6963, -148.3235 | absent |

The source BZS BIF also states exactly: `The -9 offset is for Alaska Standard Time.` The Ho1 BIF has one UTC_OFFSET value `-5`, without a date or comment. No overlapping or contradictory offsets were present in either file.

Original BIF sheets contain exactly the BADM columns: `SITE_ID`, `GROUP_ID`, `VARIABLE_GROUP`, `VARIABLE`, `DATAVALUE`. Sheet name: `AMF-BIF`.

The two workbooks contain AmeriFlux BASE DOI citations, NOT FLUXNET product DOIs: Ho1 `10.17190/AMF/1246061` (2026 BASE Ver. 15-5) and BZS `10.17190/AMF/1756434` (2025 BASE Ver. 5-5). These version labels must not be equated with the downloaded FLUXNET-1F source version strings Ho1 `3-6` (1996-2023) and BZS `5-7` (2010-2024). The date in the BIF filename is when the metadata was published, not `UTC_OFFSET_DATE_START`.

GitHub source-derived data:

- [Pinned original BIF time/location/DOI evidence JSON](../data/official_BIF_20261025/official_two_site_BIF_time_evidence.json) — exact filenames, original XLSX SHA256, site ID, GROUP_ID and literal source UTC offset. **This is extracted evidence, not the raw XLSX binary bytes.**
- [Stage68 read-only complete 16,874 original hard-event clock audit](../scripts/stage68/68_original_BIF_Ho1_BZS_UTC_clock_history_shadow.py) — consumes the pinned evidence JSON and the Stage64/67 original-source SHA manifests to generate provisional UTC crosswalks and year/physics summaries. Historical applicability remains a science HOLD pending independent full-period clock confirmation.

Scientific distinction: these BIFs resolve uncertainty about the **currently published site offset** (-5 and -9), not automatically all cases of invalid original VPD/RH/TA. Ho1 contains 16,788 original hard humidity physics events, 917 of which were earlier detailed temperature/time investigations. Even if full-period clock is verified, all humidity replacement candidates still need independent external ERA5/CDS coverages, original tower-T/PA physics checks, and overall DATM/forcing QA. No original EC measurements or model forcing have been altered.

Official AmeriFlux description: https://ameriflux.lbl.gov/data/aboutdata/badm-data-product/

## IRIDIS6 Stage68 one-paste pinned command

Stage68 code Git blob: `2c192fe450aa867432e48d4e24b8695862fd6626`.
Evidence Git blob: `444889041c37cdaa6b79d149053e5299756fdb8c`.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  FILE="$BASE/scripts/stage68/68_original_BIF_Ho1_BZS_UTC_clock_history_shadow.py"
  DATA="$BASE/data/official_BIF_20261025/official_two_site_BIF_time_evidence.json"
  COMMIT="a69bdeca8a09417e5b81b1ca164ed6ff71e76da8"
  mkdir -p "$(dirname "$FILE")" "$(dirname "$DATA")"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage68/68_original_BIF_Ho1_BZS_UTC_clock_history_shadow.py" -o "$FILE"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/data/official_BIF_20261025/official_two_site_BIF_time_evidence.json" -o "$DATA"
  test "$(git hash-object "$FILE")" = "2c192fe450aa867432e48d4e24b8695862fd6626"
  test "$(git hash-object "$DATA")" = "444889041c37cdaa6b79d149053e5299756fdb8c"
  "$PY" -m py_compile "$FILE"
  "$PY" -B "$FILE" --self-test
  "$PY" -B "$FILE" --check
  "$PY" -B "$FILE" --audit 2>&1 | tee "$HOME/Batch02_Stage68.log"
)
```

Expected completion marker: `STAGE68 AUDIT PASS | original Ho1 16788 + BZS 86 BIF clock shadow; historical source HOLD retained`.

The code and JSON are published on GitHub. The original XLSX files themselves are preserved as uploaded conversation attachments and are not yet checked into GitHub as binary XLSX objects. They can optionally be placed unchanged on IRIDIS6 and passed to Stage68 with `--bif-dir` to reverify their byte SHA256; never silently invent or regenerate original workbooks.

Stage68 has not yet been run on IRIDIS6. Do not auto-release historical offsets, source temperature QC, or independent ERA5 coverage merely because the current BIF offset is known.

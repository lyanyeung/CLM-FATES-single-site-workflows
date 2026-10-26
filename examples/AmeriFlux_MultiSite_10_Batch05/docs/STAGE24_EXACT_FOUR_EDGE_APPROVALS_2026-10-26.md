# AmeriFlux Batch05 — Stage24, exact investigator-approved four boundary repairs

**User's explicit instruction (2026-10-26):** approve only these four per-timestamp processed ERA-derived RH replacements, retaining selected original tower TA and recomputing VPD:

| Decision | Native FLUXMET site and timestamp (not assumed UTC) | Original source RH (%) | Approved processed-source ERA RH (%) | Original selected tower TA (°C) | Recomputed candidate VPD (hPa) |
|---|---|---:|---:|---:|---:|
| E01 | US-Vcm **2014-08-19 08:30** | 17.18377 | 56.194173 | 14.370 | ≈7.16727 |
| E02 | US-Vcm **2025-10-14 11:30** | 37.98483 | 75.805596 | 8.903 | ≈2.757924 |
| E03 | US-WCr **2025-08-25 12:30** | 33.68535 | 65.093868 | 15.219 | ≈6.032577 |
| E04 | US-WCr **2025-08-26 02:00** | 32.35776 | 91.924097 | 8.409 | ≈0.890308 |

The values in this table are from the original source Stage23 operator evidence; the new script *does not hardcode a replacement RH in place of source evidence*. It checks the original SHA-audited Stage18 source values and one matching Stage23 edge record for each approved site-time, then extracts the original `ERA_RH_Magnus_water_pct` and recalculates `VPD=es_water(TA_F)*(1-RH/100)`. Exact output is derived at full available precision. These original FLUXMET `TA_ERA/VPD_ERA` references are **processed source ERA counterparts, not independent ERA5-Land downloads**.

## Science scope: additions only, no broadening

- Stage22's **162 existing approved half-hours** must retain every original modified value exactly (checked in script).
- These **exact four new non-P1 boundary half-hours** increase the versioned candidate overlay to **166**. The original P1 cohort remains **130 approved + 46 held = 176**. Non-P1 approved transitions thus rise from 32 to 36.
- Stage22's **46 manual HOLD half-hours** (10 Dec 2015 and 36 missing original RH) are byte-identically copied into the new Stage24 output, with sha256 verification. **None of the 46 receives a reconstruction**.
- **US-Vcm 2025-10-14 12:00–13:30 (4 HH):** source RH ≈99.46% plateau; suspected sensor/data processing artifact **PENDING USER REVIEW**, not approved to replace.
- **US-WCr 2025-08-25 09:30–12:00 (6 HH):** source RH=100% plateau; suspected instrument/data processing plateau **PENDING USER REVIEW**, not approved to replace. This bounded excerpt does *not* imply that the full plateau begins at 09:30.
- Boundary review must be rerun after the four repairs. An additional jump can remain immediately before/after the new edge if the neighboring unchanged source RH is questionable. No automatic interpolation or expansion from threshold exceedance alone.
- P2/P3 separate 1,574 low-RH records remain **not yet science-approved**. No actual new model-ready DATM forcing, no Slurm submission.

## GitHub versioned script and safe operator command

[Stage24 exact-four versioned native overlay builder](../scripts/stage24/24_merge_four_approved_edge_RH_to_versioned_overlay.py)

Verified Git blob SHA of Stage24 script:
```text
86be2266af438f887a28c6319ebcbdd7b756f72f
```

Run on IRIDIS6 (write only to NEW Stage24 report folder; all source reports remain unmodified):

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage24"
  COMMIT="489ed5e424b27fa7b774edd77b1ce97a73e58a04"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/24_merge_four_approved_edge_RH_to_versioned_overlay.py"
  STAGE18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
  STAGE22="$HOME/ameriflux_batch05_stage22/approved_overlay_20261026T025303Z_1604360"
  STAGE23="$HOME/ameriflux_batch05_stage23/manual_evidence_20261026T030825Z_1617982"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage24/24_merge_four_approved_edge_RH_to_versioned_overlay.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "86be2266af438f887a28c6319ebcbdd7b756f72f"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/four_approved_edges_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" \
    --stage18-dir "$STAGE18" \
    --stage22-dir "$STAGE22" \
    --stage23-dir "$STAGE23" \
    --out "$OUT" 2>&1 | tee "$BASE/stage24.log"
  echo "STAGE24_REPORTS=$OUT"
)
```

Expected output is:
- `stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv` = **166** unique approved native RH/VPD reconstruction records; original 162 entries unaltered;
- `stage24_EXACT_4_newly_approved_edge_reconstructions.csv` = precisely 4 newly approved user-directed site-time rows;
- `stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv` = byte-for-byte copy of earlier 46 manual HOLD entries;
- `stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv` = 10 suspect saturated-plateau points for future scientific review, NO replacement;
- `stage24_all_current_overlay_boundary_transitions.csv` = regenerated 30-minute boundary screen after all 166 candidates;
- `stage24_manifest.json` = source and output SHA256, exact counted categories, no source-forcing-model writes, full data provenance.

**Status of this GitHub artifact:** Script and documentation committed, but **not yet run on operator's IRIDIS6**. An on-cluster `STAGE24 SUCCESS` and validation are required before stating 166 rows have been generated.

# AmeriFlux Batch05 — Stage24 operator success and Stage25 exact remaining-QC crosswalk

## Verified Stage24 operator execution (2026-10-26, reported by investigator)

```text
SOURCE VERIFIED
STAGE24 SELF-TEST PASS
STAGE24 VERIFIED: original context 775, Stage22 overlay 162, manual HOLD 46, Stage23 edge evidence
STAGE24 APPROVED_EDGE US-Vcm 201408190830 ORIGINAL_RH 17.18377 ERA_RH 56.194173 TA_UNCHANGED 14.37 VPD_ORIGINAL 13.564 VPD_NEW 7.1672695882
STAGE24 APPROVED_EDGE US-Vcm 202510141130 ORIGINAL_RH 37.98483 ERA_RH 75.805596 TA_UNCHANGED 8.903 VPD_ORIGINAL 7.075 VPD_NEW 2.7579244094
STAGE24 APPROVED_EDGE US-WCr 202508251230 ORIGINAL_RH 33.68535 ERA_RH 65.093868 TA_UNCHANGED 15.219 VPD_ORIGINAL 11.473 VPD_NEW 6.032576601
STAGE24 APPROVED_EDGE US-WCr 202508260200 ORIGINAL_RH 32.35776 ERA_RH 91.924097 TA_UNCHANGED 8.409 VPD_ORIGINAL 7.463 VPD_NEW 0.8903083871
STAGE24 PRIOR_APPROVED=162 NEW_EXACT_EDGES=4 TOTAL_OVERLAY=166 MANUAL_HOLD=46
STAGE24 UNAPPROVED_SATURATION_PLATFORMS=10 (Vcm4 WCr6), NO REPLACEMENT
STAGE24 EDGE_RECHECK 60 JUMPS_ABS_GT4hPa 1
STAGE24 LARGE_EDGE US-WCr 202508251200 202508251230 DELTA_VPD_hPa 6.032576601
STAGE24 SUCCESS | versioned RH/VPD overlay only, 46 HOLD unchanged, original FLUXMET/DATM/Slurm untouched
STAGE24_REPORTS=/home/ly3n24/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604
```

Stage24 is **executed successfully** on IRIDIS6, not merely uploaded to GitHub. It writes a versioned 166-site-native-HH approved overlay. **It is not an approved production forcing** and does not independently acquire ERA5-Land.

## Scientific gate unresolved

**One remaining abrupt >4 hPa / 30-min repaired boundary**: US-WCr 2025-08-25 12:00 (original QC0 RH=100% and VPD=0.000 hPa) → 12:30 (investigator-approved reconstructed source processed ERA RH=65.093868%, VPD=6.032576601 hPa). The original **WCr 09:30–12:00 RH 100% plateau (six HH)** and original **Vcm 2025-10-14 12:00–13:30 RH ~99.46% plateau (four HH)** are **unapproved for modification**. Their presence may indicate persistent sensor saturation or a real wetting/drying event and cannot be resolved by smoothing alone.

P1 original **176** half-hours = **130 approved original P1 + 46 manual HOLD**; the 46 include 36 original-RH-missing and 10 RH/T discordance points. Exact 5 HOLD source windows and future independent weather evidence remains necessary.

The remaining 1,574 Stage16 abnormal half hours belong to Stage17 P2/P3 episodes. **Some of Stage24's 36 non-P1 approved context/edge half hours may overlap this 1,574 cohort.** Do not blindly subtract 166 from 1,750 or assert that all 1,574 are still unapproved without joining exact site and native time.

## Stage25 script — source-native exact cohort and disposition

[Stage25 full 1,750 anomaly crosswalk into 522 original episodes](../scripts/stage25/25_crosswalk_1750_source_anomalies_with_166_approved_readonly.py)

At GitHub commit `6a96d5262a359634237e55f44b1885484e4c6a1c`, original Git file blob SHA: `1184b670ba873ed0aa96b59dfeb2528ee2f1b463`.

The Stage25 script reads ORIGINAL pre-existing Stage16 all-1750 native source review and Stage17 522 episodes; separately loads SUCCESSFUL Stage24's all-166 approved overlay, unchanged 46 manual HOLD and untouched two RH saturation platform windows. It checks population, tier and source numeric consistency and generates:

- `stage25_all1750_exact_tier_overlay_hold_crosswalk.csv` — one-to-one original anomaly site/native time, original P1/P2/P3, original source QC, *approved overlay* vs *manual HOLD* vs *still unapproved* status, without duplicate approval.
- `stage25_all522_episode_overlay_status.csv` — per episode exact original half-hour counts partitioned by current approved/HOLD/other unresolved and original QC-source.
- `stage25_remaining_P2_P3_evidence_worklist.csv` — only the genuinely still-unapproved P2/P3 source native HH, grouped by QC, physical ERA/MDS source evidence and original RH presence. **No automatic replacement**, including MDS pairs that are mathematically feasible.
- `stage25_all10_site_progress.csv` — all ten sites, original flags vs covered vs HOLD vs remaining work.
- `STAGE25_PROGRESS_AND_QC_WORKLIST.md` — summary site and evidence-group counts, and exact covered P2/P3 count.

Run on IRIDIS6, **without re-running Stage16, Stage17, Stage24**:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage25"
  COMMIT="6a96d5262a359634237e55f44b1885484e4c6a1c"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/25_crosswalk_1750_source_anomalies_with_166_approved_readonly.py"
  D16="$HOME/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407"
  D17="$HOME/ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407"
  D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage25/25_crosswalk_1750_source_anomalies_with_166_approved_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "1184b670ba873ed0aa96b59dfeb2528ee2f1b463"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/crosswalk_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" \
    --stage16-dir "$D16" \
    --stage17-dir "$D17" \
    --stage24-dir "$D24" \
    --out "$OUT" 2>&1 | tee "$BASE/stage25.log"
  echo "STAGE25_REPORTS=$OUT"
  cat "$OUT/STAGE25_PROGRESS_AND_QC_WORKLIST.md"
)
```

**Stage25 is committed to GitHub, but not yet executed by operator**; crosswalk P2/P3 coverage totals must come from actual Stage25 output. This script does not create a DATM forcing, infer tower-clock UTC mapping or download ERA5-Land. Site coordinates/elevation, actual external ERA5-Land dewpoint/temperature and source FLUXNET instrumentation/algorithm provenance remain independent science tasks.

**Next after Stage25:** choose batch P2/P3 QC data-source strategies based on tier/source-class distribution and verifiable independent alternatives, and separately resolve 46 manual P1 HOLD plus 10 plateau-review HH. Only after all applicable physical and provenance checks pass should a versioned full forcing / Post-v5 be generated.

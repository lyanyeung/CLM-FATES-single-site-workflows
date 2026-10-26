# AmeriFlux Batch05 — Stage32 scientifically checked; Stage33 H01 neighbor gate and 10 extra real-reference CDS pilots

## Actual Stage32 user/operator results (2026-10-26)

- **US-Vcm H01 exact original 19 P1 manually HELD native HH** (2007-12-15 21:00 → 2007-12-16 06:00) maintained. Exactly 8 boundary × trial comparisons, no new science approval, original Stage24 166 approved overlay/46 HELD/1574 P2P3 not altered.
- ERA5-Land downloaded gridded RH relative to liquid water **67.680539%–78.046519%** and to ice **78.804605%–92.834223%**; phase difference up to **14.787704 RH percentage points**. No ERA5-Land grid saturation relative to ice during the 19 points, and no negative tower ice VPD for grid-e transfer assumption.
- Original tower selected T is **2.4203–6.002364°C warmer** than actual fetched ERA5-Land 2 m T; maximum ERA5-Land RH trend over adjacent half-hours **1.238747 pp**.
- Four science-only H01 tower VPD methods (liquid/ice saturation × preserve grid RH or actual vapour pressure) produce no boundary discontinuity exceeding a **4 hPa screening threshold**. The original immediately adjacent, **UNMODIFIED** native VPD was **2.581 hPa at 2007-12-15 20:30** and **2.588 hPa at 2007-12-16 06:30**; this is not necessarily a trustworthy humidity observation. For original native air temperature near -12°C water saturation itself is roughly 2.45 hPa. **A small VPD jump is not proof that neighboring source humidity is valid or a scientific justification for releasing H01 HOLD.**

### Human decisions required

**No per-timestamp human approval is needed for external reference data collection or continued read-only evidence.** Before changing forcing: user must explicitly choose if suspicious H01 **neighboring original RH/VPD** should also be investigated/rewritten (Stage33 documents exact QC/native implied water RH), and which **reference-to-tower humidity transport** is scientifically supported (preserve grid RH vs actual vapour pressure, water vs ice saturation). Until then **all H01 19 stay HOLD**; no inferred approval for altering other 27 held P1 HH or P2/P3.

## Stage33 GitHub script

[Stage33 exact original-H01 neighbors, remaining Stage30 requests and first US-Wjs conflict reference](../scripts/stage33/33_H01_neighbor_QC_and_prioritized_independent_ERA5Land_batch.py)

Script commit: `12d6500292d896d26e54dd94c85676ccdec2fddd`; Git blob SHA: `55e10583f09b9ca51a5317a8fcf39d78566aabf4`.

Sources (exact original sources and SHA chain checked):
- Stage18 original 775 native context HH and their QC: `$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929`.
- Stage24 unchanged 166 approved versioned native RH/VPD and 46 manually held P1 HH: `$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604`.
- Stage32 successfully executed 19 actual ERA5L ice/water H01 trials: `$HOME/ameriflux_batch05_stage32/H01_phase_boundary_20261026T121337Z_3242355`.
- Stage30 actually fetched ONE prior H01 reference, and its 11 existing CDS original site-month requests updated to correct slash-separated ISO interval: `$HOME/ameriflux_batch05_stage30/one_reference_fetch_20261026T114508Z_3061960`.
- Stage27 actual 483 original P2P3 episodes and source risk ranks: `$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604`.
- Stage29 original BIF timezone science gate: `$HOME/ameriflux_batch05_stage29/bif_UTC_20261026T112153Z_2957771`.

Stage33 only checks original H01 adjacent 30-minute T/VPD mathematically reconstructed RH, original source QC and existing overlay selection; produces 3-hour context around H01, no new changes.

It then prepares **10 additional external reference CDS requests**, distinct from the ONE H01 reference already fetched:
1. Vcm Feb 2008 **H02 P1**; Vcm Dec 2008 **H03 P1**; Vcm Dec 2015 **H04 P1**; Vcp Jan 2011 **H05 P1**.
2. Vcm Oct 2025 original ~99.46% RH saturation platform; WCr Aug 2025 original 100% RH saturation platform.
3. Vcp Apr/May/Jun 2008 high risk P2/P3 episodes, including **339 original MDS–source ERA RH discrepancies >20 pp** in the full Vcp cohort.
4. **NEW original US-Wjs P2/P3 high-risk episode**, selected from actual Stage27 Wjs rows ranked highest, with original Wjs BIF `UTC_OFFSET=-7`; source episode DATE_START must be no earlier than official BIF group `2007-05-04 13:30`. This corrects Stage30's missed Wjs representation (US-Wjs has **401** original unapproved P2/P3 HH).

All UTC offsets remain **provisional** because original BIF groups lack DATE_END; preserve source native clock and no DST. All obtained reference files remain gridded ERA5-Land research evidence, not actual in-situ measurements.

### Single IRIDIS6 command: plan + optionally download all 10 extra files

The command below **explicitly downloads** the ten external meteorology research sources using the CDS account already connected and licensed by the operator. It does not touch existing source or original first download. To generate the plan only, omit `--fetch --acknowledge-provisional-bif-offsets --max-fetch 10`.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage33"
  COMMIT="12d6500292d896d26e54dd94c85676ccdec2fddd"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/33_H01_neighbor_QC_and_prioritized_independent_ERA5Land_batch.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage33/33_H01_neighbor_QC_and_prioritized_independent_ERA5Land_batch.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "55e10583f09b9ca51a5317a8fcf39d78566aabf4"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/H01_neighbors_and_external_refs_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" \
    --stage18-dir "$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929" \
    --stage24-dir "$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604" \
    --stage32-dir "$HOME/ameriflux_batch05_stage32/H01_phase_boundary_20261026T121337Z_3242355" \
    --stage30-dir "$HOME/ameriflux_batch05_stage30/one_reference_fetch_20261026T114508Z_3061960" \
    --stage27-dir "$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604" \
    --stage29-dir "$HOME/ameriflux_batch05_stage29/bif_UTC_20261026T112153Z_2957771" \
    --out "$OUT" \
    --fetch --acknowledge-provisional-bif-offsets --max-fetch 10 \
    2>&1 | tee "$BASE/stage33.log"
  echo "STAGE33_REPORTS=$OUT"
  cat "$OUT/STAGE33_NEXT_SCIENCE_ACTIONS_AND_NEIGHBOR_GATES.md"
)
```

If the user wants to limit the first group to the **four remaining P1 HOLD reference windows** before the conflict pilots, use `--max-fetch 4`. The script fetches source files sequentially and keeps a partial manifest of successful requests if CDS fails; rerun future requests in a **new output folder** (source files are never overwritten). CDS API credentials remain local, not uploaded to GitHub.

Outputs in new Stage33 folder:
- `stage33_H01_original_3h_neighbor_RH_VPD_and_QC_audit.csv` — original tower neighbor RH physically implied from original T/VPD and source QC.
- `stage33_next_10_science_reference_requests.csv` and `stage33_next_10_CDS_requests.json` — exact 10 requests.
- `stage33_downloaded_metadata.json` — obtained file hashes/sizes/ZIP or NetCDF signatures after actual downloads.
- `stage33_manifest.json` — SHA input chain, original HOLD/approved unchanged and count of CDS results.
- `STAGE33_NEXT_SCIENCE_ACTIONS_AND_NEIGHBOR_GATES.md` — investigator-scoped H01 neighbor choice and next real dataset science steps.

**Stage33 source committed; not yet executed by operator.** Existing Stage24 approvals 166 and human HOLD 46 unchanged; all original P2/P3 1574 still unapproved, 10 suspicious plateau HH not changed; no production forcing/Slurm run.

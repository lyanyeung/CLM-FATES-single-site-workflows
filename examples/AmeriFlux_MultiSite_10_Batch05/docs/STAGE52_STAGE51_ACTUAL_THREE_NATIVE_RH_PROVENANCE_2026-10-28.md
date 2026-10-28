# AmeriFlux Batch05 Stage52 — actual Stage51 results, original RH data provenance validation

## Actual IRIDIS6 science run — 28 October 2026

The corrected Stage51 code **actually ran successfully**:
```text
STAGE51 PATCHED SOURCE VERIFIED
STAGE51 SELF-TEST PASS
STAGE51 SUCCESS | 3 NUMERIC_SOURCE_HYPOTHESES, 49 NO_BOUNDED_OFFSET,
70 SOURCE_EVIDENCE_PENDING, 253 NEIGHBOR_HOLD, Claude108 untouched
STAGE51 THREE_EVENTS [{"HH":1,"RH_offset_pp":-11.5,"event":"US-UMB_E0003","site":"US-UMB"},
{"HH":3,"RH_offset_pp":-19.5,"event":"US-Wjs_E0079","site":"US-Wjs"},
{"HH":4,"RH_offset_pp":-9.0,"event":"US-Wjs_E0114","site":"US-Wjs"}]
```
IRIDIS6 original research output:
`/home/ly3n24/ameriflux_batch05_stage51/three_hypotheses_49_offset_holds_20261028T161922Z_2062563`.

All three are **source-ERA-RH plus an artificially selected constant whole-event relative-humidity offset** under an original signed VPD boundary screen. Their eight half-hours are NOT measured/validated RH improvements.

| Site event | Original HH | Exploratory RH offset (percentage points) | Largest original VPD adjustment (hPa) | QC0 neighbor count |
|---|---:|---:|---:|---:|
| US-UMB E0003 | 1 | −11.5 | 7.508847 | 1 |
| US-Wjs E0079 | 3 | −19.5 | 5.612099 | 1 |
| US-Wjs E0114 | 4 | −9.0 | 8.295339 | 1 |

The other **49** event-wide constant RH-offset methods failed under the fixed bounded ±20 percentage-point / 0.5pp grid **only**. Nearest missed conditions:
- 1: new external >2 hPa threshold
- 24: new >2 and >4 hPa, plus original edge worsened >0.5 hPa
- 15: new >2 hPa and edge worsened >0.5 hPa
- 2: new >4 hPa and edge worsened >0.5 hPa
- 7: edge worsened >0.5 hPa
Total 49; 48 have edge-worsening restriction in their nearest screen. This is NOT evidence that 49 source original events can never be repaired by independent meteorological information or physically documented alternative methods.

Previous **70** source ERA event-level numerical pilots, **253** original source neighbor RH/QC2 holds, and Claude's **108** separate source events remain unchanged. Assistant tracks exactly 70+3+49+253=375, across original 483 P2P3 site events. Source original 1,574 P2P3 original HH remain unapproved. Stage24 approved 166 rows, P1 manual HOLD46 and 10 RH platform source holds remain unchanged; no original forcing/DATM/CIME/Slurm modifications or scientific approvals have occurred.

## Stage52 — substantive new observational source audit

Instead of further adjusting RH numbers to pass a heuristic VPD discontinuity gate, **Stage52 reads the ORIGINAL site meteorological files** for the two stations hosting the three hypotheses:

[Stage52 original raw fullset/fluxmet HH exact native humidity-source inspection](../scripts/stage52/52_three_event_raw_humidity_provenance_and_49_source_holds_readonly.py) — pinned commit `b700ec732dc92ea33e277b91a8084ddf80b09d37`, blob `54596f1bdd15baecd7c9f3bb61178fab4d928053`.

[One-click IRIDIS6 source-only launcher](../scripts/stage52/run_stage52_iridis6.sh) — pinned commit `9bc2e6d3bfd4e22f58ad0dd8d4d167021836efc4`, blob `c5cc19a757807a508ab6f5f400ae1e3fbc22d5b5`.

Using a read-only scan of `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/{US-UMB,US-Wjs}/forcing/{raw,packages}`, the script finds original AmeriFlux FULLSET_HH and FLUXMET_HH CSV or ZIP products. For **exactly 8 original source-native timestamp rows** from the successful Stage51, it inventories available original RH/H2O/TA/VPD/PA/dewpoint field names and source values, paired source QC when present. It records SHA256 of the original package/source, original product filename/member, exact native timestamp matching, and whether original raw T/VPD/QC are consistent with the already verified source Stage51 values.

**No hour shifting, invented missing sensor values, filled-to-observed promotion, source edits or automatic science approval**. `RH_F` is a filled or processed field, `RH_ERA` reanalysis, `RH_MDS` a gap-filled/source estimate. Even an apparent unfilled `RH` source column is *only a possible original observation* until its documentation, sensor QC, units and timestamp basis are verified. If the original files have no usable unfilled RH at all, this is explicitly a source-evidence gap and the events remain HOLD.

Stage52 also carries forward the exact 49 failed-offset method event cases and 70 reference-science gap cases in independent reports, without touching Claude's 108 high-risk P2P3 cases.

### Three-line operator command / one-line mobile-safe command

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/9bc2e6d3bfd4e22f58ad0dd8d4d167021836efc4/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage52/run_stage52_iridis6.sh" -o "$HOME/run_stage52.sh" && test "$(git hash-object "$HOME/run_stage52.sh")" = "c5cc19a757807a508ab6f5f400ae1e3fbc22d5b5" && bash "$HOME/run_stage52.sh"
```

Expected original read-only output:
- `stage52_THREE_SOURCE_RAW_ORIGINAL_FIELD_VALUES_NOT_VALIDATED.csv`
- `stage52_THREE_EVENT_RAW_SOURCE_PRODUCT_INVENTORY.csv`
- `stage52_THREE_NUMERIC_EVENT_ORIGINAL_METEO_EVIDENCE_GAPS.csv`
- `stage52_49_NONFEASIBLE_OFFSET_NEED_SOURCE_EVIDENCE.csv`
- `stage52_70_ERA_REFERENCE_PENDING_SOURCE_EVIDENCE.csv`
- `STAGE52_THREE_ORIGINAL_HUMIDITY_SOURCE_AUDIT_AND_NEXT_EVIDENCE.md`
- `stage52_manifest.json`

**Stage52 script and launcher are committed to GitHub, and code/launcher blob pins were reviewed; actual IRIDIS6 execution is pending.**

> **CORRECTION (2026-10-26):** The first SYVH7 source check failed without writing because Stage05 has only three of the five sites. Corrected code pinned to `84c6c292ae8cda2064a8e349a80892f33328342f` uses Stage05 for SP1/Syv/Ton, and Stage08 for Slt/Uaf with original+ERA SHAs preserved. [Root-cause and corrected rerun](SYVH7_STAGE05_STAGE08_SOURCE_PROVENANCE_ROUTING_FIX_2026-10-26.md). The former GitHub pin must not be used.

# Batch04 — SYVH6 actual operator output: five sites / twelve extreme low LW_IN_F points, proposed SYVH7 + independent SYVH8 research trial

**Verified user-provided IRIDIS6 stdout 2026-10-26 04:34 UTC.** This report records actual SYVH6 checks, not an assertion that SYVH7/8 already ran.

## Actual SYVH6 all-seven-native-met Gate-0 output

- 10/10 sources sha256 PASS; 10/10 complete full-year native 30-minute chronology, `TIMESTAMP_END`, NOLEAP Feb29-removal and site years PASS.
- Core `TA_F, VPD_F, PA_F` humidity physics independently PASSED all ten, with **3 accepted-source-precision-only** exceptions (US-Rpf: 2008-02-06 07:00/09:00; US-Syv: 2008-03-09 13:00, all source VPD <=0.0005 hPa above water saturation). Preserve source and do NOT convert tiny negative model vapor pressure without a documented future output-only quantisation policy.
- Other met source fields `SW_IN_F`, `WS_F`, `P_F` numeric-range and provenance tests all pass; precipitation summary is the sum of native `P_F` in mm per half-hour, **not** evidence for ecological/hydrological realism or final model signoff.
- 5/10 whole-seven-meteorology **NUMERIC_READY**: US-Rpf, US-SRG, US-SRM, US-Seg, US-Ses.
- 5/10 **NUMERIC_BLOCKED** **only** because total **12** source values of downwelling `LW_IN_F` are below conservative 60 W/m² minimum: US-SP1 (4 HH), US-Slt (2), US-Syv (2), US-Ton (2), US-Uaf (2). No other seven-met numeric blocks.

## Twelve exact local-standard native half-hours from operator SYVH6

| Site | Original `LW_IN_F` W m−2 | Native local-standard source times | HH |
| --- | ---: | --- | ---: |
| US-SP1 | **44.764** | **2004-12-04 00:00 & 00:30; 2016-10-09 19:00 & 19:30** | 4 |
| US-Slt | **45.855** | 2016-10-09 19:00 & 19:30 | 2 |
| US-Syv | **43.388** | 2004-12-03 23:00 & 23:30 | 2 |
| US-Ton | **8.353** | 2004-12-03 21:00 & 21:30 | 2 |
| US-Uaf | **34.390** | 2004-12-03 20:00 & 20:30 | 2 |
| **Five sites** | | | **12** |

The repeated two-half-hour plateaux across multiple sites, with offsets that may correspond to different source clocks, are a **strong source-artifact hypothesis**, not proof of specific calibration or sensor error. The original paired source SHA and exact same-native `LW_IN_ERA` must be checked first. Never invent new values or assume all five sites have the same native timestamp/UTC reference.

## SYVH7 automatic source-safe repair gate — script published, NOT YET EXECUTED

[SYVH7 twelve exact low-longwave source + ERA preflight and research candidate](../scripts/manual_review/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py), source-pinned GitHub commit **`84c6c292ae8cda2064a8e349a80892f33328342f`**. Retains the latest **US-Syv SYVH3 SHA `9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa`** and the unchanged site candidates as input.

- `--self-test` checks exactly twelve specific HH and five sites without touching any source.
- `--assess` checks full SHA of **original Stage05 FLUXNET native and paired processed ERA sources**, selected ten-site source inputs, exactly source-origin 12 low LW entries and original QC; prints before, during and after values (± 1 hour) for **both source longwave and packaged processed `LW_IN_ERA`**, and applies fail-closed bounds: ERA 60–800 W/m², no implausible new within-pair >100 W/m² jump or after-replacement before/after >160 W/m² discontinuity. If data aren't verified, NO WRITE.
- `--apply` reruns the entire source preflight and, **only when verified**, writes five brand-new full-native-length research CSVs with precisely the twelve source `LW_IN_F` replacements. It marks modified `LW_IN_F_QC=2` when that field is in the derived CSV, retains original QC in separate source-vs-ERA 12HH immutable ledger, independently streams entire old/new files requiring **only `LW_IN_F` and ERA-QC field changes at exactly twelve HH**. Completely preserves all `TA_F,VPD_F,PA_F,RH,SW_IN_F,WS_F,P_F` and other original/candidate values; other five selected site files unchanged. Writes a final ten-site research selection manifest and receipt; **no original or model files edited**.
- Source is **the original packaged FLUXNET ERA5-derived `LW_IN_ERA`** (not separately retrieved independent ERA5-Land). If original paired file has no `LW_IN_ERA`, numbers are wrong or the transition remains too large, the script **stops safely**, and independent ERA5-Land thermal-radiation evidence with native clock matching becomes necessary. Do not alter script thresholds blindly to force a PASS.

## SYVH8 full independent ten-site numerical recheck

[SYVH8 verified final selected 10-site native seven-met NOLEAP independent Gate-0](../scripts/manual_review/stage_syvh8_after_12lw_final_ten_site_gate0_readonly.py), source-pinned GitHub commit **`e4559ea4dafc35d4ee531eb900747ff70416d383`**. Imports the exact pinned [SYVH5](../scripts/manual_review/stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py) and [SYVH6](../scripts/manual_review/stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py) scientific readers as siblings; independently verifies SYVH7 source manifest SHA, five new file SHA, source 12-row provenance, other five selected site pointers unchanged. Recalculates **all** 10 full source native 7-met + NOLEAP Gate-0 and explicitly retains **3 source VPD-quantisation** caveats.

When all ten have zero blockers, output `SYVH8 ALL TEN PRIMARY SEVEN MET NOLEAP NUMERIC GATE0 PASS`. This is a **numerical research gate, not** permission for Post-v5 DATM/CIME/Slurm. The selected seven-variable field conversion still requires actual ZBOT/time-centering, height, surfdata/domain/PFT and remaining source science signoffs. All results written only to new HOME audit JSON if requested.

## Exact IRIDIS6 shell run (copy and paste, no git pull)

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  SEVEN="84c6c292ae8cda2064a8e349a80892f33328342f"
  EIGHT="e4559ea4dafc35d4ee531eb900747ff70416d383"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  mkdir -p "$BASE"

  for f in stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py \
           stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py; do
    curl -fLsS --retry 3 "$RAW/$EIGHT/$REL/$f" -o "$BASE/$f"
  done
  curl -fLsS --retry 3 "$RAW/$SEVEN/$REL/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py" \
      -o "$BASE/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py"
  curl -fLsS --retry 3 "$RAW/$EIGHT/$REL/stage_syvh8_after_12lw_final_ten_site_gate0_readonly.py" \
      -o "$BASE/stage_syvh8_after_12lw_final_ten_site_gate0_readonly.py"

  python3 -B -m py_compile "$BASE"/stage_syvh{5,6,7,8}*.py
  python3 -u -B "$BASE/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py" --assess \
    2>&1 | tee "$BASE/Batch04_SYVH7_12LW_ERA_source_preflight.log"
  python3 -u -B "$BASE/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py" --apply \
    2>&1 | tee "$BASE/Batch04_SYVH7_12LW_five_site_research_apply.log"

  FINAL=$(sed -n 's/^SYVH7 12 LOW LW FIVE-SITE RESEARCH CANDIDATES FULL DIFF AUDIT PASS //p' \
    "$BASE/Batch04_SYVH7_12LW_five_site_research_apply.log" | tail -n1)
  test -n "$FINAL" && test -d "$FINAL"

  python3 -u -B "$BASE/stage_syvh8_after_12lw_final_ten_site_gate0_readonly.py" \
    --candidate-dir "$FINAL" --report \
    2>&1 | tee "$BASE/Batch04_SYVH8_10site_gate0_after_12LW.log"
)
```

**Status:** All scripts are GitHub-published and source/receipt logic has been inspected, but SYVH7 and SYVH8 have **not** been executed against real IRIDIS6 data. If an ERA physical or QC provenance gate fails, report the flagged timestamps; do not treat them as repaired or trigger model runs.

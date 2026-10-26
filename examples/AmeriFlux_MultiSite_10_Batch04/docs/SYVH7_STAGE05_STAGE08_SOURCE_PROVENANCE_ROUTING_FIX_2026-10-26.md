# Batch04 SYVH7 provenance bug and fix — Stage05 is only three sites; Stage08 supplies two more

**Operator's actual IRIDIS6 error, 2026-10-26:**

```
SYVH7 SELF-TEST PASS exact 12 low longwave native HH in 5 sites, source original unchanged
ValueError: Stage05 original native+ERA sources missing for affected 5 sites
```

**No input or research trial was modified by the aborted operator `--assess`**. The failure occurred in `pinned_inputs()` **before** any source LW/ERA comparisons or candidate write.

## Root cause confirmed directly against the GitHub Stage05/Stage08 builder and Stage11 manifest

Original Stage05 implementation [`05_build_batch04_qcv5_repair_candidates.py`](../scripts/stage05/05_build_batch04_qcv5_repair_candidates.py) has `PRIORITY = ("US-SP1", "US-Syv", "US-Ton")`, and its `report.json` source `sites` contains **these exact three**, not ten sites.

Stage08 [`08_build_remaining_seven_qcv5_candidates.py`](../scripts/stage08/08_build_remaining_seven_qcv5_candidates.py) has exact seven source sites `US-Rpf, US-Seg, US-Ses, US-Slt, US-SRG, US-SRM, US-Uaf`. [Stage11 source selection script](../scripts/stage11/11_register_latest_ten_derived_forcing_candidates.py) explicitly chooses three priority Stage07 results (whose original source provenance is Stage05) and other Stage08/Stage10 rows. The previous SYVH7 incorrectly assumed `set(EXPECTED).issubset(Stage05["sites"])`, which cannot be true as `EXPECTED` contains two Stage08 sites.

## Corrected exact source contract

| Low LW site | Actual source original FLUXMET and paired ERA provenance report |
| --- | --- |
| US-SP1 | `qcv5_stage05_candidates/candidate_20261024T103113Z/report.json` |
| US-Syv | Stage05 same as above |
| US-Ton | Stage05 same as above |
| US-Slt | `qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z/report.json` |
| US-Uaf | Stage08 same as above |

The patched SYVH7 script reads and independently SHA-verifies **both upstream immutable report site ensembles**, checks all five original FLUXMET/processed ERA full source hashes against each report's **own** `source_provenance.native.sha256` / `source_provenance.era.sha256`, verifies each selected full research forcing against the **final SYVH3 10-site manifest** (including the final Syv full SHA), then performs identical same-native `LW_IN_ERA` source comparisons, ±2hour native context and boundary checks before any candidate write.

**Corrected pinned code commit: `84c6c292ae8cda2064a8e349a80892f33328342f`** at [`stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py`](../scripts/manual_review/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py). The preexisting SYVH8 script commit `e4559ea4dafc35d4ee531eb900747ff70416d383` requires no change; it uses the receipt/manifest emitted by corrected SYVH7 and rechecks all ten native forcing streams.

## Re-execute on IRIDIS6 without touching source or restarting earlier science work

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="84c6c292ae8cda2064a8e349a80892f33328342f"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  mkdir -p "$BASE"
  SCRIPT="$BASE/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --self-test
  python3 -u -B "$SCRIPT" --assess 2>&1 | tee "$BASE/Batch04_SYVH7_12LW_ERA_source_preflight.log"
  python3 -u -B "$SCRIPT" --apply 2>&1 | tee "$BASE/Batch04_SYVH7_12LW_five_site_research_apply.log"
  FINAL=$(sed -n 's/^SYVH7 12 LOW LW FIVE-SITE RESEARCH CANDIDATES FULL DIFF AUDIT PASS //p' "$BASE/Batch04_SYVH7_12LW_five_site_research_apply.log" | tail -n1)
  test -n "$FINAL" && test -d "$FINAL"
  python3 -u -B "$BASE/stage_syvh8_after_12lw_final_ten_site_gate0_readonly.py" --candidate-dir "$FINAL" --report 2>&1 | tee "$BASE/Batch04_SYVH8_10site_gate0_after_12LW.log"
)
```

**SYVH8 prerequisite:** the SYVH5, SYVH6 and SYVH8 scripts must already have been fetched by the previous command block from the previously pinned GitHub commit; this correction fetches only the changed SYVH7. If they are not present, download all three from `e4559ea4dafc35d4ee531eb900747ff70416d383` before executing SYVH8.

**Status:** corrected code GitHub commit available, **not yet run on operator IRIDIS6**. Do not call the 12 LW records repaired or the 10-site Post-v5 Gate-0 complete until real operator output proves this. If original source != selected LW, the processed ERA lacks `LW_IN_ERA`, a boundary fails, or a source SHA changed, **STOP** and inspect rather than forcing a repair.

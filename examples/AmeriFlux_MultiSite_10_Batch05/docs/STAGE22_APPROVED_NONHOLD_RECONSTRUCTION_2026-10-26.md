# AmeriFlux Batch05 — Stage22 exact accepted decisions, source holds, new overlay

**Investigator instruction (2026-10-26):** “hold我人工审核，其他的按照你的决定修改。” Interpreted only for the current **original 176 P1 HH decision scope**. All earlier explicit G01/G03/G05/G06 source-RH pairing decisions are retained. Scientist opted to hold 2015 and missing-RH events for manual review, and accept the proposed Stage21 non-2015 A class and native-RH B class. In the preceding assistant recommendation, three boundary HH were described as **extend the review**, not as exact approved overwrite targets, so remain unmodified and explicitly flagged for the investigator.

## Exact approved scope

- **Stage20 117 native rows:** G01 WCr 26 using *source processed* ERA-derived RH + original tower selected T; G03 Vcm 34 using available **original source RH**, including all 24 native transitions; G05 Vcm 26 using processed ERA-derived RH + measured T; G06 Vcm 31 using processed ERA-derived RH + unchanged selected T (including 8 QC1/MDS T source rows).
- **Stage21 A, excluding 2015:** **34** additional native US-Vcm QC0/0 low original RH cases across 2014, 2017, 2018, 2024 use original source processed ERA-derived RH and **original measured tower TA**, recomputing VPD with Magnus water es(T).
- **Stage21 B:** **11** US-Vcm QC2/2 anomalous native source VPD points where RH_original exists: use **native source RH** with the selected original T and recompute VPD, recording the original QA flags. Extra transition hours beyond the specific 11 were **not authorized** in this decision; they must be reviewed separately.
- **Overall approved new RH/VPD overlay rows: 117+34+11=162**, including 32 non-P1 rows inherited from Stage20. Among original 176 P1 rows, 130 are approved to the overlay.

## Manual hold preserved unchanged

- **Stage20 34:** G02 Vcm 2007-12-15/16 19; G04 Vcm 2008-02-06 12; G07 Vcp 2011-01-01 3; native RH missing and processed ERA RH physical invalid/low.
- **Stage21 A 2015-12-06 10:** original QC0 tower T exceeds source ERA T by about 11–13 °C; source ERA-derived RH mostly under 10%. Real atmospheric conditions not independently established. User opts **HOLD and personally inspect**.
- **Stage21 C 2008-12-27 2:** original RH missing and processed ERA-derived RH negative; HOLD.
- **Overall 46 unique P1 half-hours unchanged and recorded in HOLD ledger.**
- Additional **three QC0 boundary half-hours** at WCr 2025-08-25 12:30, WCr 2025-08-26 02:00, Vcm 2025-10-14 11:30 **remain unmodified pending actual human decision**. Boundary jumps are diagnostics, not proof of bad source observations.

**Bookkeeping:** 176 P1 original = 130 approved P1 + 46 held P1. Stage20 117 approved includes 32 non-P1 original-RH transitions/QC1 source-RH-only records; final overlay total=162.

## Source semantics and write protection

Original FLUXMET source `TA_F`, `VPD_F`, `RH`, `TA_F_QC` and `VPD_F_QC` must never be overwritten; source QC=0 only denotes **original measurement**, not reconstructed RH/VPD. Stage22 exports a separate native-time RH+VPD overlay with explicit reconstruction provenance, separate manual holds, and all edge transition checks.

For target RH:
```text
processed source ERA RH = 100 * (1 - VPD_ERA/es_water(TA_ERA))
or original native source RH
VPD_reconstructed = es_water(original selected TA_F) * (1 - target RH / 100)
es_water(T in °C) = 6.112 * exp(17.67*T/(T+243.5)) [hPa]
```

The processed source `TA_ERA/VPD_ERA` are **NOT verified independent ERA5-Land data**; this reconstruction is not proof of independent source reliability. Output is scientifically approved for versioned candidate overlay only, **not an authorized final CLM-FATES DATM forcing**. 483 other non-P1 Stage17 episodes remain unapproved and full-set physical audit must be complete before model submission.

## Stage22 new versioned overlay

[Stage22 source-guarded non-HOLD candidate overlay builder](../scripts/stage22/22_apply_decisions_to_versioned_native_overlay.py)

Use the exact published script and verified Git blob SHA. It requires successful existing Stage18/20/21 source reports. It refuses input population changes, original RH/TA mismatch, invalid humidity or VPD, overlapping holds, missing native timestamps or accidental addition of non-approved P1.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage22"
  COMMIT="cca9d4e6f14492fda3e86836004c3245bb9698bc"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/22_apply_decisions_to_versioned_native_overlay.py"
  STAGE18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
  STAGE20="$HOME/ameriflux_batch05_stage20/decision_candidates_20261026T011616Z_1483029"
  STAGE21="$HOME/ameriflux_batch05_stage21/manual_review_20261026T013442Z_1394929"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage22/22_apply_decisions_to_versioned_native_overlay.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "b8b87b2182ccfae35f93020df8feeddb0505bd83"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/approved_overlay_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage18-dir "$STAGE18" --stage20-dir "$STAGE20" \
    --stage21-dir "$STAGE21" --out "$OUT" 2>&1 | tee "$BASE/stage22.log"
  echo "STAGE22_REPORTS=$OUT"
  cat "$OUT/STAGE22_OPERATOR_REVIEW.md"
)
```

Outputs:
- `stage22_VERSIONED_APPROVED_RH_VPD_native_overlay.csv` 162 approved rows, with original TA/RH/VPD, candidate RH/VPD, original QC and provenance; **actual new persisted versioned overlay**.
- `stage22_46_MANUAL_HOLD_P1_untouched.csv` all 46 held original P1 rows (NOT modified).
- `stage22_all_overlay_boundary_transitions.csv` actual mixed changed/original 30-min VPD jump screen, flags 3 investigator boundaries.
- `stage22_manifest.json` exact population/status/provenance/remaining-work metadata.
- `STAGE22_OPERATOR_REVIEW.md` readable science gate and critical transitions.

**Status:** code committed to GitHub; IRIDIS6 Stage22 **not yet executed by operator**. No source, forcing, cases or Slurm changed. To proceed to model-ready full forcing, independently verify manual holds and screen remaining 1,574 non-P1 low-RH source HH; join overlay only through a future provenance-safe forcing builder and post-v5 checks.


## Execution patch — Stage22 source-RH full-precision recomputation

The operator first ran the original Stage22 and got `ValueError: candidate pair incoherent` at `US-Vcm 200801162100`. **This was an overly strict checker applied to Stage21's six-decimal VPD CSV, not an erroneous humidity input.** For original `TA_F=-14.802°C`, original `RH=88.56054%`, Stage21 produced `VPD=0.222795 hPa` (six decimals). A rederived RH differs from 88.56054 by ~0.000023 percentage points, crossing Stage22's 0.000011 tolerance. The scientific physical-pair calculation is well defined at full precision.

[Patched Stage22 program](../scripts/stage22/22_apply_decisions_to_versioned_native_overlay.py) at GitHub commit `cca9d4e6f14492fda3e86836004c3245bb9698bc`, Git blob SHA `b8b87b2182ccfae35f93020df8feeddb0505bd83`, now:

1. Verifies the pre-rounded Stage20/21 RH candidate still matches **the immutable source-provenance RH** within 0.000012 percentage points;
2. Verifies the previously rounded VPD is within **0.000002 hPa** of the source-derived exact VPD (much stricter than typical meteorological uncertainty but above mere CSV rounding);
3. Recomputes the authoritative overlay VPD from full available original-source RH precision and `TA_F`; keeps physical RH/VPD checks and all approved/hold set membership checks;
4. Adds a self-test reproducing this *exact original failed* `US-Vcm` 2008 sample;
5. Writes original source, held cases, forcing, model, QC and Slurm **nowhere**; the initial operator execution failed before the new output directory was created.

**Patch execution not yet confirmed by the operator**. Retry with the updated pinned Git commit and SHA, always write to a new timestamped output folder. Do not merely relax physical consistency thresholds, do not touch HOLD rows.

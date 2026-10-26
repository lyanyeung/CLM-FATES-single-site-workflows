# Batch05 Stage23: actual operator Stage22 HOLD and boundary disposition

User supplied read-only Stage22 outputs (2026-10-26). Scientific overlay **162 new RH/VPD pairs successfully written to versioned overlay only**, source FLUXMET and official DATM forcing unchanged, **46 original P1 HOLD**, **60** overlay/original transitions screened, **4 >4 hPa per 30-min jumps**.

## Human review HOLD groups (five, not 46 independent manual decisions)

| Original/native event | Site | HOLD original HH | Native interval | Source RH |
|---|---|---:|---|---|
| H01 | US-Vcm | 19 | 2007-12-15 21:00 to 12-16 06:00 | all missing (-9999); source ERA RH inferred -12.21 to -0.71%, invalid |
| H02 | US-Vcm | 12 | 2008-02-06 01:30 to 08:00 | all missing; 11 source ERA RH negative and one ≈0.63% |
| H03 | US-Vcm | 2 | 2008-12-27 21:00–21:30 | all missing; source processed ERA RH ≈-4.05% |
| H04 | US-Vcm | 10 | 2015-12-06 04:30–09:30 | original RH exists ~0.087–0.787%, source ERA RH ~3.86–20.72%, original selected T 2–6°C vs source ERA T -9 to -5°C |
| H05 | US-Vcp | 3 | 2011-01-01 07:00–08:00 | all missing; processed ERA RH -6.00 to -6.42% |

The **36 missing-original-RH records require independent trustworthy meteorological reference or another scientifically supported imputation**. Do not reuse the same invalid processed `TA_ERA/VPD_ERA` pair as an independent replacement. For 2015, do not assume tower T or source ERA T is correct merely because one looks more plausible; investigate source metadata and separate reference. Native timestamps are not automatically UTC.

## The FOUR explicit edge checks from actual Stage22 output

| Site | Original native half-hour transition | Stage22 post-overlay VPD jump | Scientifically approved boundary expansion? |
|---|---|---:|---|
| US-Vcm | **2014-08-19 08:00→08:30** | **+7.2624627 hPa** | No — newly discovered by full Stage22 boundary check |
| US-Vcm | 2025-10-14 11:00→11:30 | +4.4395174 hPa | No |
| US-WCr | 2025-08-25 12:30→13:00 | -5.1061837 hPa | No |
| US-WCr | 2025-08-26 01:30→02:00 | +6.3817862 hPa | No |

The fourth/new 2014 boundary is currently the largest. This is **not evidence to discard the original 08:30 point automatically**; the original T, QC, raw RH and processed ERA comparison are needed before a user decision. Three earlier explicit boundaries remain untouched and are not among the 46 P1 missing/human HOLD rows; do not double-count.

## New evidence packaging stage

[Stage23 read-only operator script](../scripts/stage23/23_hold_5_windows_four_edges_source_evidence_readonly.py), GitHub commit `9acd4cb05733a47fa67d278d0f18398b0db55e28`, blob `d595ca38e8f9009ac19002b516f84c909b7e3a02`.

The script validates Stage18 exactly **775 native source context HH** and successful Stage22 **162 approved overlay / 46 HOLD / 60 boundary checks**, then provides:

- `stage23_five_holds_and_four_edges_full_review.md`: one complete, per-event original TA/VPD/RH QC0/1/2 and processed ERA TA/VPD/derived RH + MDS alternatives for every HOLD event with ±3 hours of original context, and all four significant boundary events with ±3h context. The hypothetical neighbor ERA-RH-with-original-TA option is **explicitly unapproved**.
- `stage23_four_edges_original_ERA_hypothetical.csv`: full machine-readable boundary evidence.
- `stage23_review_summary.json`: counts, provenance and no-writes metadata.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage23"
  COMMIT="9acd4cb05733a47fa67d278d0f18398b0db55e28"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/23_hold_5_windows_four_edges_source_evidence_readonly.py"
  D18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
  D22="$HOME/ameriflux_batch05_stage22/approved_overlay_20261026T025303Z_1604360"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage23/23_hold_5_windows_four_edges_source_evidence_readonly.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "d595ca38e8f9009ac19002b516f84c909b7e3a02"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/manual_evidence_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage18-dir "$D18" --stage22-dir "$D22" --out "$OUT" | tee "$BASE/stage23.log"
  echo "STAGE23_REVIEW=$OUT/stage23_five_holds_and_four_edges_full_review.md"
)
```

After operator execution, choose decisions for **H01–H05** and for all four edges; do not apply a scalar interpolation or blind ERA RH replacement to invalid source-ERA periods. P2/P3 lower-priority other **1,574 source low-RH HH across 483 episodes** also remain to be screened. Following resolved science approvals, build true versioned native-to-DATM forcing and Post-v5 QC. No Slurm model run is warranted yet.

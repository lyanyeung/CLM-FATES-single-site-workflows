# Batch04 Stage18 — pin six original temperature source/QC windows (next run)

**Status:** Stage17 **IRIDIS6 VERIFIED 6/6, 0 science holds cleared** ([actual findings](STAGE17_VERIFIED_SIX_TEMPERATURE_CONTEXT_2026-10-25.md)). Stage18 source has been committed to GitHub; **Stage18 `--audit` has NOT been run and has no operator results**.

**Purpose:** Before inventing a temperature correction, inspect the **original native FLUXMET** for temperature-related columns, especially `TA_F`, `TA_F_QC`, and `TA_ERA` *if present*; print exact original native half-hour readings within ±2 h of each of the 6 held timestamps, adjacent-event temperature slopes/QC, and same-clock readings ±1/±2 days. The script SHA-pins all original 3 site FLUXMET files and Stage14 candidate files and verifies Stage12/14 receipts, eight known temperature HOLDs and original BIF location/time offset. `TA_ERA` is optional; a missing field is reported as NA rather than invented. **No external temperature is treated as verified tower truth** and `QC2` neighbours are never assumed independent raw measurements.

## Runnable command on IRIDIS6 (no git pull)

```bash
(
  set -euo pipefail

  BASE="$HOME/ameriflux_batch04_stage18"
  ROOT="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts"
  NEW="7faec9a5d35d7d9db4a2adc506e277f21f34e1a7"
  OLD="9be06860ee3e9f14e08fb078d22d0090b49d58d4"

  mkdir -p "$BASE"
  SCRIPT="$BASE/18_original_tower_temperature_qc_source_lineage.py"

  curl -fLsS --retry 3 \
    "$ROOT/$NEW/$REL/stage18/18_original_tower_temperature_qc_source_lineage.py" \
    -o "$SCRIPT"

  curl -fLsS --retry 3 \
    "$ROOT/$OLD/$REL/stage12/12_repair_non_syv_science_holds.py" \
    -o "$BASE/12_repair_non_syv_science_holds.py"

  python3 -B -m py_compile "$SCRIPT"
  python3 -B -m py_compile "$BASE/12_repair_non_syv_science_holds.py"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --audit \
    2>&1 | tee "$BASE/stage18_original_T_QC_lineage_readonly.log"
)
```

## Planned review of the six events

| Site | Date and native time | Stage17 clue | Stage18 question |
| --- | --- | --- | --- |
| US-SP1 | 2007-10-15 17:30 | 11.150→23.220°C QC0 across next HH | Is this a whole original TA segment / provenance discontinuity? |
| US-SP1 | 2008-01-16 08:00 | Sustained cold QC0 cluster | Is the cold regime present on adjoining days? Are ERA-derived T fields present? |
| US-SP1 | 2008-01-16 08:30 | QC0 continuous warming | Is this a true contiguous segment rather than one bad point? |
| US-SP1 | 2008-02-03 08:00 | Multi-hour large tower/grid difference | Are native, ERA-derived and neighboring-day values internally consistent? |
| US-SRG | 2019-03-19 12:00 | 19.668 QC2, **0.718 QC0**, 20.605 QC2 | Can any independent raw tower T or source QC support/reject this single point? **QC2 is not independent raw tower proof.** |
| US-Seg | 2016-12-27 18:00 | 4.332, 0.015, −0.512, −0.863°C all QC0 | Does the cooling sequence occur as part of original instrument/meteorological data? |

This stage is a deterministic read-only original-product audit. It **does not** change the original, Stage14 baseline, Stage15 two-point alternative, or any other source, nor download CDS data, apply Post-v5, prepare CIME/DATM or submit SLURM jobs. All eight original temperature scientific HOLDs and the US-Syv 606 old HOLDs + 10 skipped edges stay unchanged.

**Next operator response:** the output at `~/ameriflux_batch04_stage18/stage18_original_T_QC_lineage_readonly.log`. Mark Stage18 PASS only after seeing its actual result; if any SHA or source-contract gate fails, retain the exception and do not bypass it.

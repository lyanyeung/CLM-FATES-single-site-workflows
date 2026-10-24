# Batch02 Stage62 full CDS pass and Stage63 next QC automation

24 October 2026 — **Operator-provided IRIDIS6 stdout** (not a staged
CSV uploaded to this repository):

- The pinned Stage62 SHA `0b68fa14a7e008bd7fb1b19153024e215f67c2bf` was verified.
- Stage62 Python syntax/self-test, source check, full `--auto`
  and final **STAGING PASS / AUTO PASS** succeeded.
- All **50/50** required independent CDS ERA5 grid-years were verified;
  **0** CDS grid-years remain missing for the eight original-BIF-
  verified non-Ho1 sites.
- Stage62 per-row outcome: **4,801** original-T/PA paired external
  water-RH/VPD/QBOT candidates, **246** original T vs ERA5 T2m
  differences >8°C, **86 US-BZS** original-release BIF provenance HOLD.
  These account for all **5,133** events exactly.
- The complete Stage62 report is:
  `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage62_nonHo1_5133_verified_CDS_stage_20261024T225848Z_db032320`.
- Stage60 independently added **4,411** further distinct selected water
  humidity candidates, bringing the total to **9,212**.
- Original US-Ho1 **16,788** hard-physics events were not aligned to ERA5:
  917 earlier target events are a **subset** of the 16,788.
- Original EC tower, source CSV, netCDF forcing, DATM, CIME, Slurm and
  spin-up were not modified. Neither Stage62 nor Stage60 grants model
  forcing permission.

## Stage63: independently validate original tower cold temperatures

The new [Stage63 script](../scripts/stage63/63_automatic_246_temperature_neighbor_and_metadata_triage.py)
requires exact Stage62 50/50 authenticated source checks and target
count 246. It reopens the original **Stage49/04b SHA-verified EC primary
files** and checks every exact `(site, TIMESTAMP_START, source_csv_row)` target:

- Original EC T and QA flags agree with Stage62 precisely.
- Original EC T below freezing, with finite pressure, matched independent
  ERA5 water RH, and exact ±one/±two native-step time context (30/60 min).
- Neighbor QC0/1, smooth ±one/±two steps with no individual 2–4°C
  jump, and original T–ERA5 discrepancy no greater than 25°C.
- QC2 records require a much stronger neighbor continuity test than
  QC0/1. Strong-consistency cold observations can **retain original EC
  T automatically** without blanket ERA5 T replacement; ambiguous
  or unstable observations remain HOLD and are displayed individually.
- For accepted records, produces **candidate** independent ERA5
  water-reference VPD and QBOT using original EC TA_F and PA_F;
  the candidate is not written into the DATM or forcing.
- Also scans source-adjacent original archived ZIPs for US-BZS
  and US-Ho1 BIF. Only exact original-primary SHA256 agreement with a
  decompressed ZIP primary and a valid BIF lat/long/UTC_OFFSET permit
  a **same-release metadata candidate**. It does not rewrite existing
  original BIF, nor blindly approve timezone changes.

### Run on IRIDIS6

Pinned commit: `7af5b9f4e243c8f42e4a207dd427a871f754e1e2`
Pinned blob SHA1: `b8f2ad755c7f4bcb7fbb998bd3a086db28e7032c`

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage63/63_automatic_246_temperature_neighbor_and_metadata_triage.py"
  COMMIT="7af5b9f4e243c8f42e4a207dd427a871f754e1e2"
  EXPECTED="b8f2ad755c7f4bcb7fbb998bd3a086db28e7032c"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage63/63_automatic_246_temperature_neighbor_and_metadata_triage.py" \
    -o "$TMP"
  ACTUAL="$(git hash-object "$TMP")"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $ACTUAL"
  test "$ACTUAL" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage63_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Successful marker:
`STAGE63 AUDIT PASS | 246 original T source-neighbor decisions recorded`

Isolated Stage63 outputs:
- `246_exact_original_temperature_neighbor_source_decisions.csv`
- `temperature_auto_decision_summary.csv`
- `BZS_Ho1_original_archive_BIF_discovery.json`
- `source_and_science_manifest.json`

No automated BIF candidate or temperature triage in this report
is an automatic DATM approval. Stage63 has been committed to
GitHub but **not yet run on IRIDIS6**.

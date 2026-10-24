# AmeriFlux Batch02 Stage63 PASS; Stage64 original hard-physics census consolidation

24 October 2026 — observed operator results from source-pinned IRIDIS6 audit.

## Stage63 verified 246 native tower original-temperature events

Pinned Stage63 Git blob `b8f2ad755c7f4bcb7fbb998bd3a086db28e7032c`
passed Python syntax/self-test, read-only check and isolated AUDIT.
Report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage63_246_temperature_auto_neighbor_QC_20261024T231206Z_b5fac2db`

Exactly **246** original EC air temperatures had previously been held
because |EC TA_F − independent CDS ERA5 T2m| >8 °C. Original primary
source row, station local TIMESTAMP_START, original TA_F and TA_F_QC,
and neighboring observations were all checked.

| Stage63 original tower T route | Records |
| --- | ---: |
| AUTO_KEEP_ORIGINAL_TA_F_SOURCE_NEIGHBOR_VALIDATED_COLD | **177** |
| HOLD_ORIGINAL_TA_OUTSIDE_COLD_POLICY | 48 |
| HOLD_TEMPORAL_JUMP_OR_NONSTATIONARY | 12 |
| HOLD_NEIGHBOR_QC_UNVERIFIED | 9 |
| **Total** | **246** |

- **177** very cold original tower temperatures had stable,
  checksum-confirmed source neighbor continuity and passed the
  strict no-spike/source QC test. The user delegated such cases to
  automatic application of water-reference ERA5 RH/VPD/QBOT at
  **original EC tower TA_F and PA_F**.
- **48** temperatures were at or above freezing and are outside the
  _cold-specific_ Stage63 auto-signoff rule. They are not
  automatically incorrect or approved.
- **12** have possible nonstationarity/jumps. Examples include
  US-ICh exactly −40 °C repeatedly and other sharp changes.
  No automatic replacement of EC tower temperature without
  wider and independent checks.
- **9** US-ICt very cold events have original QC2 but not enough
  verified neighbor QC0/1 context; they remain original source HOLD.
- **US-BZS and US-Ho1**: no original source-adjacent ZIP/BIF
  found by Stage63. Original release UTC_OFFSET remains a
  hard provenance gate. An official AmeriFlux BADM download
  exists at the site level, but release-specific matching is
  still necessary before ERA5 UTC joins.

### Stage64: merge accepted candidates, retain only unresolved blockers

Published [Stage64 script](../scripts/stage64/64_merge_9389_verified_ERA5_humidity_candidates.py)
merges these **177 Stage63** cold original T accepted candidates with
**4,801 Stage62** and **4,411 Stage60** independent CDS ERA5
water-humidity candidates. It verifies every input manifest SHA256,
the original Stage61/Stage49 **26,332 hard-event source census**,
and exact (site, native TIMESTAMP_START) identities for all three
disjoint candidate cohorts. It independently recalculates
water-reference VPD and QBOT from original tower T/PA and selected
CDS water RH. Any duplicate, source mismatch, numerical error
or missing original time fails closed.

Expected accounting:

| Original Stage49 hard humidity source events | n |
| --- | ---: |
| Stage60 candidate (existing) | 4,411 |
| Stage62 candidate (independent full CDS) | 4,801 |
| Stage63 additional cold-source T accepted candidate | 177 |
| **Total selected sparse correction candidates** | **9,389** |
| US-Ho1 original same-release time provenance HOLD | 16,788 |
| US-BZS original BIF/time provenance HOLD | 86 |
| Other Stage63 original source T evidence HOLD | 69 |
| **Total remaining original hard HOLD** | **16,943** |
| **Total original source hard events** | **26,332** |

There are also **100 unique positive raw RH <1% review-only
timestamps** outside the Stage49 26,332 hard-physics union.
They are not automatically considered erroneous and are not
silently replaced.

Stage64 generates a new **isolated**, SHA256-tracked candidate
ledger, a source-complete original hard census, a separate 69-row
T HOLD CSV and per-site summary. It does **not modify any**
original EC files, CDS original downloads/receipts, previous
Stage53–63 ledgers, NetCDF, DATM, CIME/Slurm or any model forcing.

### Pinned IRIDIS6 command

Git commit: `ff84f222012aa6b662751707828ba833dd8b5f74`

Git blob SHA1: `e44671127b427587ca6b823ce1a04dd31dd22cf9`

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage64/64_merge_9389_verified_ERA5_humidity_candidates.py"
  COMMIT="ff84f222012aa6b662751707828ba833dd8b5f74"
  EXPECTED="e44671127b427587ca6b823ce1a04dd31dd22cf9"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage64/64_merge_9389_verified_ERA5_humidity_candidates.py" \
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
    2>&1 | tee "$HOME/Batch02_Stage64_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

On success:

`STAGE64 AUDIT PASS | 9389 unique humidity candidates; 16943 hard source HOLDs`

Stage64 is committed and repository blob SHA checked, **not yet
executed on IRIDIS6**.

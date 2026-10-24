# Stage62 IRIDIS6 PASS, 22 independent CDS grid-years missing — automated continuation

24 October 2026. This evidence comes from user-pasted IRIDIS6 stdout.

## Verified current state

Operator's original Stage62 script (Git blob `7f0c32b619247333658db15f5e74abfa3b18ba24`)
passed Python syntax and self-test, source checks, and isolated **STAGING PASS**.
Original report on IRIDIS6:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage62_nonHo1_5133_verified_CDS_stage_20261024T120055Z_3489543f`.

The Stage61 residual has 5,133 hard original RH/VPD anomalies outside US-Ho1:
- **2,911**: independent CDS ERA5 already verified, original EC TA_F/PA_F kept and water-reference RH/VPD/QBOT candidate fully calculated.
- **1,970**: no verified CDS ERA5 grid-year in current cache (22 missing grid-years). They can be downloaded automatically using existing operator CDS credentials.
- **166**: independent ERA5 available but original EC T differs from ERA5 T2m by >8 C; need neighbor/context quality rule before original EC T scientific sign-off. **Do not blindly replace T.**
- **86 US-BZS**: exact original release BIF with station UTC_OFFSET not found in extracted source folder. Do not guess the UTC_OFFSET.
- The **16,788 US-Ho1 original hard humidity events**, which include the 917 Stage58 UTC-hold subset, are still excluded from automatic ERA5 time alignment.

The 50 required independent CDS grid-years (8 BIF-verified sites)
were **28 verified reusable + 22 missing**. Exactly 2 BZS site-years
(2011, 2012) remain BIF-blocked.

The upstream Stage60 set of **4,411 unique** ERA5 water-RH candidates is untouched.
Together, Stage60+Stage62 contain **7,322 source-disjoint numerically complete
humidity candidates** at this checkpoint, all still independent candidate
ledgers not yet applied to DATM/model forcing.

## Fully automated next action: rerun Stage62 --auto (NEW version)

The [Stage62 script](../scripts/stage62/62_reuse_or_fetch_CDS_ERA5_for_5133_nonHo1_hard_humidity.py)
now has **`--auto`**. It:
1. Rechecks the immutable Stage61 original source census, exact original
   site BIF and Stage50 script Git blob.
2. Reuses all 28 existing verified CDS grid-years.
3. Downloads the remaining 22 via bounded batches of eight, each
   with exact grid/year/calendar/variables/units/original payload/checksums.
   Re-runs verified receipt inventory after each batch and resumes on a later
   `--auto` call if a CDS request fails partway.
4. Once all source-verifiable grid-years exist, rebuilds the 5,133-row
   candidate status ledger in a new isolated SHA256-tracked report.
   Records without original T/PA validation or with >8 C site-vs-ERA5
   temperature differences are retained HOLD, not silently replaced.
5. Does not touch original CSV, previous stage output, model forcing,
   DATM NetCDF, CIME, Slurm or existing runs.

New Stage62 GitHub pinned commit:
`e97c4bd5eace3defeb6a597a40efd2227ce9c3f9`
Git blob SHA:
`0e39900b827d545f524f6e8e40e75a44d2e2312a`

### One-paste command, IRIDIS6

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage62/62_reuse_or_fetch_CDS_ERA5_for_5133_nonHo1_hard_humidity.py"
  COMMIT="e97c4bd5eace3defeb6a597a40efd2227ce9c3f9"
  EXPECTED="0e39900b827d545f524f6e8e40e75a44d2e2312a"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage62/62_reuse_or_fetch_CDS_ERA5_for_5133_nonHo1_hard_humidity.py" \
    -o "$TMP"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --auto --max-new 8 \
    2>&1 | tee "$HOME/Batch02_Stage62_auto_CDS_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Completion marker:
`STAGE62 AUTO PASS | verified all accessible CDS grid-years; full 5133 candidate/hold census generated`.

**CDS credentials and network access are held on IRIDIS6; GitHub publishing alone
cannot initiate these requests or modify the live cluster.**
The new Stage62 `--auto` script is GitHub-published, but has not yet been run
on IRIDIS6.

## No needless manual QC

- 2,911 already verified candidates require no repeated individual human review.
- 1,970 CDS-missing events are normal automatic data-retrieval work, not an
  operator science question.
- 166 >8°C temperature differences require *automated original tower
  temporal-neighbor review first*, and only exceptional unstable/source
  ambiguous data should be escalated for a user decision.
- 86 US-BZS and 16,788 US-Ho1 require version-matched source time metadata;
  official public site coordinates/timezones do not independently prove the
  exact processed release's station UTC_OFFSET.

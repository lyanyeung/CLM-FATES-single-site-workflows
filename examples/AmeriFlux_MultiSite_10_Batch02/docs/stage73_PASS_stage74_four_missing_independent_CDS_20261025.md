# Stage73 PASS — four cross-site same-grid receipts verified, Stage74 last four true CDS missing years

IRIDIS6 operator output 25 Oct 2026: the original Stage73 script Git blob `66af1ae518ff56ff55165c58f26afb5863b6688b` passed self-test, read-only plan, create-only immutable cross-site receipt bridge and full source shadow audit.

Stage73 complete report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage73_exact_grid_cross_site_verified_CDS_shadow_20261025T085440Z_4ca0e311`.

Four US-Ho1 cross-site original CDS receipts are **proved** by site-original receipt SHA, independent CDS payload SHA, NetCDF SHA, gridyear, actual CDS request coordinates/quarter-degree grid and original buffered UTC calendar. New separate bridge receipts were created for original US-Ho2 / US-Ho3 CDS sources: **2011 (1,366 hard events), 2016 (762), 2021 (46), 2023 (8)**. The original source receipts, original ERA5 and tower files were not changed. All four independent source years are now reusable without another CDS call.

The 16,874 original US-Ho1+BZS hard-humidity population is now:

| Status (Stage73 immutable independent CDS shadow) | Events |
| --- | ---: |
| Water RH/VPD/QBOT numeric shadow from independently SHA-verified CDS, original tower T/PA retained; BIF historical time applicability still HOLD | **13,606** |
| No verified independent CDS gridyear | **2,191** |
| Original tower temperature original QC nonzero | **995** |
| Original tower temperature versus independent ERA5 T >8°C | **82** |
| **Total original source-hard** | **16,874** |

Independent CDS coverage is **22 / 26** source-relevant site gridyears. The remaining four **genuinely absent** gridyear cohorts are:

| Site | Gridyear | Original hard source events | ERA5 quarter-degree center |
| --- | ---: | ---: | --- |
| US-Ho1 | 2000 | 1,069 | (45.25, -68.75) |
| US-Ho1 | 2008 | 1,036 | (45.25, -68.75) |
| US-BZS | 2012 | 79 | (64.75, -148.25) |
| US-BZS | 2011 | 7 | (64.75, -148.25) |

## Stage74 exact four-remaining-years independent CDS recovery

Stage74 script: `scripts/stage74/74_fetch_four_truly_missing_Ho1_BZS_CDS_gridyears.py`.

The code verifies Stage73 source-report schema and SHA, **26-year original cohort integrity**, four validated source bridge receipts, and exact four-year missing population. `--plan` does not write. `--fetch --max-new 4` requests **only** those four independent CDS ERA5 gridyears with Stage72's previously vetted, create-only fetch, SHA, unit/grid/time verification and Stage72 shared exclusive writer lock. New files are written **only** into `~/AmeriFlux_Batch02_Stage72_independent_CDS_ERA5_rescue`, never overwriting original Stage15/18/50/62 receipts or the four Stage73 bridges. Existing new-cache verified sources are reused; failed existing source evidence aborts rather than being overwritten.

After source retrieval, `--audit` reuses Stage71's original source physics with the Stage73 verified cross-site bridges and Stage72 independent data; it writes only a **new isolated source report**. The script never releases the remaining 995 original-T QC or 82 tower-vs-grid T holds, nor does it declare 2026 BIF publication to prove historical UTC applicability. The pre-existing Stage64 9,389 numeric candidates also remain unchanged. There is no automatic NetCDF forcing or DATM/CIME/SLURM modification.

Pinned script commit: `df99261dbccc44a63e68ec82770e553549c360a1`.
Verified Stage74 Git blob: `c21772aea4334b7e88997cca16df310012f9337b`.

## One-paste IRIDIS6 command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage74/74_fetch_four_truly_missing_Ho1_BZS_CDS_gridyears.py"
  COMMIT="df99261dbccc44a63e68ec82770e553549c360a1"
  EXPECTED="c21772aea4334b7e88997cca16df310012f9337b"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage74/74_fetch_four_truly_missing_Ho1_BZS_CDS_gridyears.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --plan
  "$PY" -B "$SCRIPT" --fetch --max-new 4 \
    2>&1 | tee "$HOME/Batch02_Stage74_fetch4.log"
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage74_audit.log"
)
```

Expected completion (only when operator Stage74 truly finishes):
`STAGE74 AUDIT PASS | four target years independently verified or held; full 16874 source shadow retained`.

If the CDS service or one downloaded payload fails source SHA/calendars, no existing files are overwritten. Run `--plan` to identify missing source years. Stage74 is committed but its full IRIDIS6 run is NOT YET verified.

Key remaining science tasks after complete independent source coverage: audit historical site BIF UTC_OFFSET effective period, independently review remaining tower-T QC and T/ERA discrepancy holds, then generate separate unmodified-source forcing candidates and conduct full NetCDF/DATM QA. Keep all original hard-event HOLD unchanged until science approval.

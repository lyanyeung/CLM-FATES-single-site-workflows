# AmeriFlux Batch02 — Stage60 PASS; next Stage61 exact original-source anomaly coverage

Date: 24 October 2026. This entry records user-pasted IRIDIS6
results, not the original Stage60 CSV bytes uploaded to GitHub.

## Stage60 successful live results

Pinned Git blob verified by operator:
`7affb6854f479eb008fd566c2f0e5320320a092f`.
Syntax, self-test, source check and isolated staging **all PASSED**.
Report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage60_4411_ERA5_water_RH_VPD_QBOT_unified_20261024T112137Z_950f7adf`

- **4,411** unique site/local-start-time proposed independent CDS ERA5
  water-RH/VPD/QBOT substitutions: **3,967** Stage58/59 humidity cases
  with accepted EC tower original T/PA + **444** Stage53 source raw
  RH=0/>100 candidates.
- Site counts: **US-EML 1,327; US-GLE 295; US-Ha1 398;
  US-Ho2 7; US-ICh 178; US-ICt 2,206**.
- Exactly **0** water-reference RH>100 and **0** negative
  water-reference VPD. **1,700** over-ice RH>100 remain phase
  diagnostics and **are not automatically defective or clipped**.
- The **917 US-Ho1** Stage11 target rows remain excluded:
  their independently verified same-release site UTC_OFFSET
  metadata are missing from the original extracted directory.
- **No original source, NetCDF, DATM, Slurm, CIME, spinup or
  forcing files changed.** Stage60 is a provenance-verified sparse
  correction proposal, not a completed full forcing.

## Why Stage61 is necessary

The original Stage48/49 batch census includes **3,462,624** original
native HH/HR tower rows, **26,332** hard humidity-physics screens,
and **26,432** unique original source review timestamps
(including positive RH<1% review cases).
The 4,411 Stage60 candidates and original 26,332 hard screens
are **not** interchangeable sets. The Stage11 4,884 science HOLD
cohort is also a different population. Without matching original
(site, local TIMESTAMP_START), subtraction of cohort totals is invalid.

[Stage61 exact source-coverage audit](../scripts/stage61/61_exact_original_humidity_hard_screen_vs_4411_repair_coverage.py)
automatically finds the existing Stage49 source report under
`reports/stage49_original_humidity_review_*/`,
requires original Stage49 census/codes, validates its original
source inventory SHA256, and pins Stage58 and Stage60 manifests and
candidate CSV by SHA256. Its classifications distinguish:

- Original hard source screens with a **matching Stage60 proposed
  replacement** (not yet applied to DATM).
- Original hard screens with **no matching Stage60 candidate yet**,
  including per-site and exact date/time and original T/VPD/PA/RH/QC.
- Stage60 candidate source timestamps that do not occur in the
  separate original source RH/VPD physics review census.
- US-Ho1 Stage11's **917 unverified-UTC records**, and their exact
  intersection with Stage49 original hard screens.
- Positive raw RH<1% original-source reviews (not automatically
  evidence that observed RH is impossible).

Stage61 is **read-only** with respect to all prior stages and model
forcing. Its new isolated audit outputs have their own SHA256 manifest.
The operator can then direct independent CDS humidity retrieval only
for true remaining invalid/uncorrected model-forcing cases, while
avoiding unnecessary blanket ERA substitution. A final ten-site forcing
audit still must reconcile existing Stage07/08 reconstruction and
the model's variable lineage before actual DATM writes.

### Exact pinned command on IRIDIS6

Stage61 corrected and pinned as
`332d7a553118fd29f1c55c8721d1841924a6abd6`
with Git blob
`9d67aafa960c4c5e6e41d9c67f7f2eaf60f25d1d`.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage61/61_exact_original_humidity_hard_screen_vs_4411_repair_coverage.py"
  COMMIT="332d7a553118fd29f1c55c8721d1841924a6abd6"
  EXPECTED="9d67aafa960c4c5e6e41d9c67f7f2eaf60f25d1d"
  mkdir -p "$BASE/scripts/stage61"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage61/61_exact_original_humidity_hard_screen_vs_4411_repair_coverage.py" \
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
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage61_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

On pass, look for:
`STAGE61 AUDIT PASS | original hard anomalies reconciled to selected 4411 exact times`.
Stage61 initially failed in its synthetic self-test due to the pandas `DataFrame.flags` property name collision (`t.flags`); the repository script was fixed to use `t["flags"]`. No original input or forcing was changed by the failed self-test. Only Stage61's actual output can establish how many original hard
screens remain unaddressed: the arithmetic 26,332−4,411 is **not**
a valid source-level answer without exact event-identity matching.

## US-Ho1 metadata

The official [AmeriFlux US-Ho1 page](https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1)
confirms the 1996–2023 FLUXNET product (Ver. 3-6) and
[the Fluxnet processing specification](https://fluxnet.org/data/fluxnet2015-dataset/)
confirms local **standard** time, without summer-time changes.
However, those public pages alone do not verify the original
released **site-specific UTC_OFFSET** for the 917 and other historic
Ho1 source events. An official same-release BADM/BIF file is
still needed for a permanent provenance release.

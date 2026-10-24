# Batch02 — Human review of all 63 extreme-cold EC temperatures: approve tower TA_F only

Date: 24 October 2026.
Operator explicitly approved all 63 EC tower air-temperature records during
the conversation after viewing the Stage57 read-only event table.
That review is an explicit **temperature-source decision**, NOT approval
of humidity/VPD physics, the model forcing, or any change to original data.

## Original Stage57 evidence (operator pasted the 63 rows)

| Site | Cases | Original tower temperature °C | Original TA_F QC | Original tower vs independent ERA5 T2m |
| --- | ---: | ---: | --- | --- |
| US-EML | 27 | −34.71 to −27.40 | all QC0 | +8.01 to +11.63 °C |
| US-GLE | 6 | −21.63 to −18.30 | all QC0 | +8.33 to +10.99 °C |
| US-ICt | 30 | −36.43 to −29.07 | all QC2 | +8.01 to +9.83 °C |
| **Total** | **63** | **all subzero** | 33 QC0, 30 QC2 | **ERA5 colder in every case** |

All 63 were marked by Stage57 as
`isolated_tower_spike_candidate=False` and
`neighbor_continuity_with_tower_within3C=True`.
These QC/source continuity facts support the user's specific judgment
to retain the EC tower TA_F despite a coarse-grid ERA5 discrepancy.
They do not establish the physical cause of the warmer local EC
temperature or validate the derived humidity fluxes.

The pasted log is from Stage57's **--check** (`STAGE57 CHECK PASS`);
there is no demonstrated Stage57 `--audit` output directory.
Stage58 therefore regenerates the original Stage57 63-row evidence
from exact SHA-pinned **same-release original tower files** and
Stage56/Stage19 source rather than requiring a Stage57 audit file.

## Stage58 deterministic application (temperature decision only)

[Stage58 script](../scripts/stage58/58_accept_63_manual_extreme_cold_tower_temperatures.py)

Its science and safety contract:

1. Imports the exact Stage57 Git blob SHA
   `4786751fb3500b3481a2505ccd778d2a4208a118` and
   re-verifies original tower file checksums, Stage56 full report,
   Stage55/Stage19 and Stage11/Stage54 provenance.
2. Requires **exactly 63** original tower records on three sites,
   original TA_F below zero, positive tower−ERA5 temperature
   >8 °C, matching QC (EML/GLE=0, ICt=2), smooth ±30 minute
   neighbors and zero Stage57 isolated-spike flags.
3. Compares the 63 unique tower-local start times exactly to
   Stage56's 63 `HOLD_TA_DIFF_FROM_ERA5_GT8C` entries.
4. Replaces only the *temperature-policy decision* in a new
   isolated Stage58 4,884-row ledger.
5. Final temperature decision counts: **3,904** retained under
   the original 8 °C screen + **63** explicitly human-accepted
   extreme-cold tower TA_F values = **3,967**. All **917
   US-Ho1** tower-time rows remain protected by provisional UTC.
6. Recomputes **candidate** CDS ERA5 water-RH-associated VPD and
   QBOT with retained ORIGINAL TA_F and original pressure on
   these 3,967 rows. This is numerical preparation, **not a
   final humidity method approval**.
7. Keeps all 4,884 original humidity/water-vs-ice caution flags
   and model forcing approvals **false**; does not modify any
   original tower file, pre-existing Stage07–57 artifact,
   DATM, NetCDF, Slurm or CIME job.

### Execute on IRIDIS6 (pinned GitHub blob)

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage58/58_accept_63_manual_extreme_cold_tower_temperatures.py"
  COMMIT="869332b02737d6dac2f071af52f150937b0718cb"
  EXPECTED="dbb270085e5ed60570090145d37e37037b0d0dfc"
  mkdir -p "$BASE/scripts/stage58"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage58/58_accept_63_manual_extreme_cold_tower_temperatures.py" \
    -o "$TMP"
  ACTUAL="$(git hash-object "$TMP")"
  printf 'EXPECTED: %s\nACTUAL:   %s\n' "$EXPECTED" "$ACTUAL"
  test "$ACTUAL" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage58_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Successful audited output includes:
`STAGE58 AUDIT PASS | 63 human-accepted cold TA + 3904 prior retained = 3967`

New SHA256-tracked reports:
- `63_original_tower_temperature_manual_acceptance.csv`
- `4884_final_original_tower_temperature_policy.csv`
- `five_site_temperature_policy_summary.csv`
- `manual_temperature_decision_manifest.json`

The script is published and pinned but **has not yet been executed on
IRIDIS6**, so no Stage58 results or forcing edits are asserted.

### Following scientific blocker

For the retained 3,967 original temperatures, the remaining issue
is **relative humidity reference to saturation over water versus ice**,
not original temperature QC. Site-specific vapour pressure, dewpoint
and specific humidity must be checked before scientific release of
any RH/VPD/QBOT forcing. US-Ho1's 917 rows still require verified
source UTC offset, independent of the temperature decision. Stage53
444 source RH zero/>100 replacement candidates remain isolated,
and Stage54 proved no exact local-time intersections with Stage11.

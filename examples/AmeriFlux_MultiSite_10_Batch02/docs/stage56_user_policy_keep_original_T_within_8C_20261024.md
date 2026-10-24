# Batch02 Stage56 — Keep original tower air temperature if it agrees with ERA5

Date: 2026-10-24. This is the **user's selected temperature policy**,
not a change to original flux data. Source: operator's Stage55 report PASS,
original Stage19/Stage11 and Stage54 verified zero-overlap evidence.

## Decision

- Compare the ORIGINAL FLUXNET `TA_F` (Celsius) to
  independently retrieved CDS **reanalysis-era5-single-levels-timeseries**
  `t2m` at the exact BIF-local-to-UTC-aligned tower timestamp.
- **If original TA_F is physically valid and
  |TA_F − ERA5 T2m| ≤ 8.0 C, retain original TA_F.**
  A reported `TA_F_QC=1 or =2` is NOT by itself a reason
  to replace a numerically plausible, ERA5-consistent temperature.
  Preserve and report original QC classification; this is a
  user-specified pragmatic screening policy, not proof that QC1/2
  observations equal independent tower measurements.
- If |difference| >8 C, original T invalid, or ERA5 T invalid,
  keep that row in temperature HOLD. QC codes outside 0/1/2/3 or
  missing are flagged but do not alone override a plausible TA_F. **Do not automatically
  replace TA_F with ERA5 T2m.**
- **US-Ho1** still has an unverified release BIF / UTC offset. Its
  independent ERA5 comparison is provisional and **all 917 rows remain
  time-alignment HOLD**, even if the apparent temperature difference
  happens to be small.
- If T is retained, use the already verified Stage19 external CDS ERA5
  *water-reference RH* together with original **TA_F and PA_F** to
  recalculate consistent VPD (hPa) and QBOT (kg/kg). If original PA_F
  is invalid, candidate VPD/QBOT are not released.
- As the Stage55 output shows, **all 4,884 Stage11 rows have cold
  water/ice caution** and original non-QC0 VPD flags. Those are retained
  as independent science gates even when original tower temperature is
  selected. Final forcing approval remains **zero**.
- The separately staged Stage53 444 RH records remain untouched.
  Stage54 already proved **zero** exact tower-time intersection.

## Important provenance distinction

Stage55's `T_site_minus_ERA5_C` comes from Stage19's
`retained_TA_C` value (a prior Stage11 target). Stage56
**does not assume that Stage11 retained_TA_C equals original TA_F**.
It checks the original `TA_F` from Stage19, reports any
disagreement with `retained_TA_C`, and computes all
new RH-coupled VPD/QBOT candidates from the original, retained TA_F
and original station pressure when valid.

A Stage56 source check reuses the *unchanged, pinned Stage55 code* to
re-verify Stage11, Stage19 CDS ERA5 data/receipts, Stage54
zero intersection, Stage55 manifest and per-row original timestamps.
It writes a new isolated report only on `--audit`.

## GitHub script and command

[Stage56 script](../scripts/stage56/56_keep_original_tower_T_when_ERA5_within_8C.py),
updated and pinned under commit
`1fee499b439e5bd9457edba4ab6726a3a5c3e9c9`,
Git blob `e9d48b73f948a1d34a516e841ed3c8d589f9494a`.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage56/56_keep_original_tower_T_when_ERA5_within_8C.py"
  COMMIT="1fee499b439e5bd9457edba4ab6726a3a5c3e9c9"
  EXPECTED="e9d48b73f948a1d34a516e841ed3c8d589f9494a"
  mkdir -p "$BASE/scripts/stage56"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage56/56_keep_original_tower_T_when_ERA5_within_8C.py" \
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
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage56_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected final message:
`STAGE56 AUDIT PASS | original TA_F retained when valid and ERA5 delta<=8C`.

Stage56 output (only after a successful *operator run*):
- `4884_keep_original_TA_under8C_with_ERA5_RH_VPD_QBOT.csv` — complete
  event ledger, original T/pressure/QC, ERA5 t2m/RH, T decision and
  original-TA-consistent RH/VPD/QBOT proposal.
- `five_site_temperature_retain_gate_summary.csv` — count retained
  original T, QC1/2 retained, excessive T discrepancies, provisional
  Ho1 offsets, invalid original pressure, and candidates per site.
- `temperature_decision_counts.csv` and `policy_manifest.json`
  with SHA256 of every generated artifact.

No source or forcing edits, no overwrite of earlier-stage reports, no
CIME/Slurm jobs, no automatic ERA5 T substitution or forcing approval.

**Current GitHub-published Stage56 has not yet been executed on IRIDIS6.**

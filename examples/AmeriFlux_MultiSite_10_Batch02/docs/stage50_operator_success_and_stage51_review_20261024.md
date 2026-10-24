# Stage50 operator completion and Stage51 444/27 science-review split

Date: 24 October 2026.
Source: operator IRIDIS6 terminal output for Stage50, run
`--build` on 2026-10-24 at 09:42:06 UTC (inferred from report directory name).
This archive is an *operator-reported summary*, not an uploaded copy of the
raw Stage50 patch or an independent execution of Stage51.

## Provenance / exact Stage50 result

- Original Stage49 audit completed: 444 selected raw-RH defects (RH=0: 39;
  RH>100: 405) across four tower sites.
- 10 / 10 required external CDS ERA5 grid-years independently covered and
  SHA256-verified by Stage50's receipt checks.
- Stage50 `BUILD PASS | exactly 444 CDS ERA5 RH patch candidates`.
- Output: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage50_unified_external_ERA5_RH_20261024T094206Z_7d901572`.
- Statuses exactly:
  - `CANDIDATE_ONLY_REVIEW_ZERO_RH`: 12
  - `CANDIDATE_ONLY_REVIEW_SUPERSAT_PHASE`: 405
  - `MANUAL_JOINT_T_AND_HUMIDITY_REVIEW`: 27
- **0 approved model forcing writes.** Original sources, old candidates,
  DATM/NetCDF, Slurm and CIME remain untouched.

**Interpretation:** All 444 have a verified ERA5-derived candidate *RH*.
Only the 12 zero-RH records with acceptable retained-tower T plus 405
supersaturation-review records reached the humidity-only candidate route.
The 27 others are NOT missing ERA5 humidity: original site temperature
QC/representativeness prevents blindly deriving model-ready VPD/QBOT
against retained site T.

## Stage51 — exact-read-only science review of 27 joint T cases

Script: [51_audit_444_RH_and_27_joint_temperature_candidates.py](../scripts/stage51/51_audit_444_RH_and_27_joint_temperature_candidates.py)

Reads the exact Stage50 report above, checks its 444-row SHA256-pinned
provenance, all linked original CDS ERA5 data/receipt hashes and exact 4-site
science categories. Computes an **alternative complete ERA5 T2m + RH +
VPD + QBOT bundle** for the 27 records, using precisely the same
interpolated Stage50 ERA5 *water-basis RH* and ERA5 T/pressure:

- water es(T) = 6.112 exp[17.67*T/(T+243.5)] hPa;
- VPD_joint = es(TERA) * (1 - RH_ERA/100) hPa;
- e_joint = es(TERA)*RH_ERA/100 hPa;
- QBOT_joint = 0.622 (100 e_joint) /
  (P_ERA - 0.378*100 e_joint), pressures in Pa.
- Also records a separate QBOT sensitivity based on original station
  pressure if physically valid; this is a comparison, NOT an automatic
  change of pressure boundary condition.

It writes new additive audit files:
- `27_joint_ERA5_T_RH_QBOT_review.csv` — exact 27 original records,
  temperature-QC and tower-minus-ERA temperature flags, ERA5-consistent
  joint T/RH/VPD/QBOT candidate, pressure sensitivity.
- `405_raw_RH_gt100_phase_review.csv` — all raw positive
  supersaturation records, including below-zero water/ice phase questions.
- `444_four_site_review_breakdown.csv` — per-site reasons.
- `review_provenance.json` with source and output hashes.

No approval is inferred, and no original source or already constructed
Stage50 artifact is rewritten. 4,884 Stage08 HOLD records and the
original 24 QC0 Stage07 edits are still separate science questions.

### IRIDIS6 verified GitHub-file download and read-only execution

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage51/51_audit_444_RH_and_27_joint_temperature_candidates.py"
  mkdir -p "$BASE/scripts/stage51"
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/$REL/scripts/stage51/51_audit_444_RH_and_27_joint_temperature_candidates.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "64f4888bd64de8ae7996fbfce5d1aac1c908ed7f"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage51_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected successful result begins with:
`STAGE51 AUDIT PASS | exact 444 source-pinned ERA5 RH candidates`.

**At present Stage51 is published but has not been run against the
operator's actual IRIDIS6 Stage50 output.** The 27-row ERA5 T/RH
alternative still requires explicit scientific choice before it could
ever enter forcing. After Stage51 audit, review whether to use the
observed Tsite for the 417 humidity-only proposals, how to treat the
27 joint-temperature proposal cases, and the >100% winter phase
and metadata distinctions. Do not silently approve all 444.

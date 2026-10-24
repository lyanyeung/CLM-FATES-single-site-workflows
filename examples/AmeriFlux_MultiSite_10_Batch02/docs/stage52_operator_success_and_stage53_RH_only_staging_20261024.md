# Batch02 — Stage52 verified science review and Stage53 same-ERA5 RH-only staging

Date: 2026-10-24.
Provenance: operator-pasted IRIDIS6 output. The underlying Stage52 CSV and
manifest are stored on IRIDIS6 and have NOT been uploaded to this repository.

## Stage52 operator result: PASS

Original Stage52 output on IRIDIS6:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage52_RH_gt100_phase_and_ICt_QC_review_20261024T095901Z_9b4118ce`

`STAGE52 AUDIT PASS | 405 RH>100 phase cases / 27 US-ICt T-QC cases`

| Site | Original RH=0 | Original RH>100 | RH>100 from 100–100.5 | 100.5–101 | 101–105 | >105 | RH>100 with T<0 C | Joint T-QC cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-Ha1 | 2 | 396 | 102 | 101 | 181 | 12 | 220 | 0 |
| US-Ho2 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| US-ICh | 0 | 9 | 9 | 0 | 0 | 0 | 9 | 0 |
| US-ICt | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 27 |
| **Total** | **39** | **405** | **111** | **101** | **181** | **12** | **229** | **27** |

- All **405** original RH>100 records have original VPD
  numerically near zero; US-Ha1's largest raw RH is **110.8%** and
  US-ICh's is **100.3%**. These represent some genuine numerical
  inconsistencies and some small oversaturations that may reflect
  water/ice phase, humidity instrumentation or model clipping.
  Do NOT assert all are known sensor faults.
- The **27** US-ICt original RH=0 temperature review records comprise
  original T **QC1=14** and **QC2=13**. None has
  |Tsite minus independently downloaded CDS ERA5 T2m| >8 C;
  observed maximum absolute difference is **5.192635498 C**.
  A small T difference alone does not validate original QC1/QC2 T.
- All **10/10** independent CDS ERA5 grid-years already verified
  for 444 target RH anomalies. Stage50 built all 444 RH candidates;
  Stage51 independently reconciled all source identities and prepared
  joint ERA5 T/RH/VPD/QBOT alternatives for the 27. Stage52 completed.
- The original Stage08 **4,884 scientific HOLD** rows and Stage07
  24 original QC0 modifications are distinct unresolved review cohorts.
- 0 scientific approvals for direct model input: source, model forcing,
  DATM, CIME, Slurm and archive files unchanged.

## User-selected scientific policy to stage next

The user's explicit instruction is to replace every source RH=0 or
source RH>100 with independently retrieved **same-source CDS ERA5 RH**.
This means **444/444 humidity choices**, including slight
supersaturation (with a retained phase-review flag).

**Important separation:** this policy selects a replacement *humidity*.
It does NOT order automatic replacement of original station air
temperature. The default proposal is to preserve **EC site T and PA**
for all 444, recomputing associated **VPD and QBOT consistently** from
the ERA5 RH with the original station T/PA. For the 27 US-ICt
QC1/QC2 cases, keep an explicit T provenance HOLD, with the existing
Stage51 full ERA5-T/RH comparison as a separate sensitivity alternative.
Do not silently switch to ERA5 T based only on QC1/QC2.

### Stage53 output and safety boundaries

[Stage53 Python script](../scripts/stage53/53_stage_user_selected_444_external_ERA5_RH_only_patch.py)

- Pin Stage50 source ledger and Stage52 full original
  source/phase/T-QC report by SHA256 and exact timestamp/source row;
- require exact 444 target site counts and 39/405 original RH split,
  12/405/27 Stage50 candidate status counts and 14/13 ICt QC1/QC2;
- verify that every recomputed original-T/PA water-VPD and QBOT
  agrees numerically with Stage50's same-ERA5-RH candidate;
- make a **new sparse 444-row staging ledger** with proposed RH/VPD/QBOT
  replacements and clear distinctions for 27 T-QC and 405 phase-review
  flags. Keep original T/PA and all original source provenance; no
  new CDS download required;
- **never modify original FLUXNET, Stage07–52 outputs,
  NetCDF forcing, DATM, CIME or Slurm**. Even after Stage53 PASS
  model-ready approvals remain false. This is isolated preparatory
  staging, not permission to spin up.

### IRIDIS6 commands

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage53/53_stage_user_selected_444_external_ERA5_RH_only_patch.py"
  mkdir -p "$BASE/scripts/stage53"
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/377c44ba810ff9be431970ec3ff073cec91077b3/$REL/scripts/stage53/53_stage_user_selected_444_external_ERA5_RH_only_patch.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = \
    "824f18c7868fa451274b1e359906ece2fd84a199"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --stage \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage53_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected: `STAGE53 STAGING PASS | all 444 same-ERA5 RH replacements with paired VPD/QBOT`.

The Stage53 script was published and its Git blob identity
verified in GitHub. It **has not yet passed live IRIDIS6 Python
syntax/self-test/source-data execution**. Thus no Stage53 output or
new forcing was claimed to exist at time of publication.

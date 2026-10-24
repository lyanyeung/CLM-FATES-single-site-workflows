# Batch02 Stage48 operator results and Stage49 science-review boundary

Date: 2026-10-24. Source: operator-provided IRIDIS6 log
/home/ly3n24/AmeriFlux_Batch02_Stage48_20261024T083544Z.log.
Status: Stage48 --self-test, --check and ten-primary --audit completed;
source SHA256 verified; Stage48 changed no primary, candidate, forcing,
DATM, CIME, surface or Slurm file. The original log bytes have not been
independently uploaded/checksummed into this repository.

## Exact Stage48 counts (original primary HH/HR products only)

| Site | Unique hard | Derived water RH <0 | Raw RH =0 | Raw RH >100 | 0<RH<1 | Hard with TA_QC0 |
|---|---:|---:|---:|---:|---:|---:|
| US-BZS | 86 | 86 | 0 | 0 | 0 | 84 |
| US-CMW | 42 | 42 | 0 | 0 | 4 | 40 |
| US-EML | 4,311 | 4,311 | 0 | 0 | 1 | 3,520 |
| US-GLE | 1,125 | 1,125 | 0 | 0 | 0 | 920 |
| US-Ha1 | 421 | 25 | 2 | 396 | 1 | 418 |
| US-Ho1 | 16,788 | 16,788 | 0 | 0 | 0 | 15,792 |
| US-Ho2 | 724 | 717 | 7 | 0 | 4 | 720 |
| US-Ho3 | 39 | 39 | 0 | 0 | 4 | 39 |
| US-ICh | 226 | 217 | 0 | 9 | 0 | 14 |
| US-ICt | 2,570 | 2,540 | 30 | 0 | 88 | 4 |
| **Total** | **26,332** | **25,890** | **39** | **405** | **102** | **21,551** |

- 3,462,624 original native rows; 3,460,200 prospective NO_LEAP rows.
- 0 significantly negative water VPD, 0 tiny negative water VPD and
  0 raw negative RH in the Stage48 source scans.
- Original RH is missing in 1,003,092 native rows. Missing raw RH does not
  imply the same timestamps lack VPD.
- Original 1–5% and 5–10% positive RH bins: 1,002 and 21,275 rows.
- The Stage48 ACTUAL_VAPOR_NONPOSITIVE and RH_INFERRED_LT0 groups are
  coextensive (25,890) here; do not sum them.
- These are original primary-source screens. Their hard union is NOT the
  Stage07 initial 4,904 blockers or the later Stage08 4,884 HOLD cohort.
  No exact timestamp-level intersection has yet been calculated.

## Interpretation and scientific gate

A large fraction of negative *inferred* humidity occurs when original VPD
exceeds saturation vapour pressure at original T. A zero negative-VPD count
does NOT demonstrate a valid TA/VPD pair.

US-Ho1 is first priority: 16,788 original hard screens. Its historical 319
temperature provenance conflicts and the full Stage08 4,884-case scientific
HOLD cohort are distinct sets pending exact joins. Original TA_QC0 is a
provenance code, not proof that T is physically correct; Stage47 found
substantial original Ho1 QC0 vs processed TA_ERA residuals.

Raw RH slightly over 100% needs phase/supersaturation investigation:
Ha1 includes RH=100.3% at below-zero air temperature. Water versus ice
saturation also matters for ICh/ICt. Raw 0<RH<1% is an important manual
review, not an unconditional replacement.

No candidate may use in-package ERA5_HH, TA_ERA or VPD_ERA as independently
retrieved CDS ERA5. Stage44 established identical processed aliases for Ho1.
External CDS ERA5/ERA5-Land T2m, Td2m, pressure, site UTC, elevation and
native timing must pass provenance and physics checks; suspect/QC2
temperatures require joint T/humidity review.

Scientific state: all 4,884 Stage08 cohort rows HOLD, 0 approved
replacements, 0 Batch02 forcing/model runs; five numerical Stage07 sites
still have 24 original QC0 modifications for separate manual review.

## Stage49: reproducible original-source row-level audit

Script: [Stage49 read-only ledger](../scripts/stage49/49_build_ten_site_original_humidity_review_ledger.py)

It imports the pinned Stage48 Git blob SHA1
8856b568d413e3d27c40fd6c6a014a4e755ecfb3, reads the exact
20-source Stage04b inventory, independently SHA256-checks each original
primary before/after scanning, and keeps Ha1 at native HR resolution.
The output is the unique HARD_PHYSICS or positive raw RH<1% event set,
with original source row/timestamp, T/VPD/PA/raw and derived RH,
temperature/VPD original QC, science route and false approval fields.

Fresh isolated reports contain:
- original_humidity_event_review.csv
- site_science_screen_summary.csv
- year_science_screen_summary.csv
- provenance_and_hold.json
- INCOMPLETE_DO_NOT_USE if the audit fails before final verification

Output labels are science *review* routes, never direct replacement approval.
This is not a Stage08 intersection join and does not edit original, prior
candidate, surface, forcing or model files.

### IRIDIS6 command

~~~bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  EXP="/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02"
  INV="$EXP/reports/stage04b_met_20261021T233344Z_ff3b9f20/source_inventory.json"
  mkdir -p "$BASE/scripts/stage48" "$BASE/scripts/stage49"
  for P in \
    scripts/stage48/48_audit_ten_site_vpd_rh_era_repair_rule.py \
    scripts/stage49/49_build_ten_site_original_humidity_review_ledger.py
  do
    curl -fLsS --retry 3 "$RAW/$REL/$P" -o "$BASE/$P"
  done
  test "$(git hash-object "$BASE/scripts/stage48/48_audit_ten_site_vpd_rh_era_repair_rule.py")" = \
    "8856b568d413e3d27c40fd6c6a014a4e755ecfb3"
  SCRIPT="$BASE/scripts/stage49/49_build_ten_site_original_humidity_review_ledger.py"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check --inventory "$INV"
  "$PY" -B "$SCRIPT" --audit --inventory "$INV" \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage49_$(date -u +%Y%m%dT%H%M%SZ).log"
)
~~~

Do not consume the CSV until STAGE49 AUDIT PASS is printed and
INCOMPLETE_DO_NOT_USE is absent. Stage49 has NOT yet run on live IRIDIS6
data; synthetic self-test and exact-source preflight remain the first gate.

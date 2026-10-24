# AmeriFlux Batch04 Stage07 — user-approved high-jump direct ERA5 VPD replacement

**User direction (24 October 2026):** Stop repeatedly reviewing the same visible VPD jumps. Directly replace the timestamps at the **210 Stage06 flagged 30-minute VPD boundaries** using contemporaneous ERA5 VPD, keeping original source releases untouched. This **new explicit instruction supersedes the earlier blanket QC0 preservation policy only for the explicitly flagged boundary endpoints**; physically consistent **US-Ton native VPD QC0 outside these jump endpoints remains protected**.

## Committed executable workflow

[Stage07 script](../scripts/stage07/07_apply_jump_ERA5_vpd_three_sites.py)

This is a genuine **full-length new derived FLUXMET HH source candidate** for each priority Batch04 site (US-SP1, US-Syv, US-Ton), not just another report. It uses the already built Stage05 5,336 variable-level candidate patch overlay and the Stage06 210 boundary list. The script verifies their stored SHA receipts, and verifies that original source FLUXMET and companion packaged ERA5 CSVs match the hashes recorded at Stage05.

- At **both exact native half-hour endpoints** of each Stage06 flagged boundary, use `VPD_ERA` from the **corresponding timestamp's** packaged `FLUXNET_ERA5_HH`. No row-number joins and no average of adjacent ERA times.
- The new RH is **derived at the retained tower (or previously Stage05 temperature-interpolated) TA** using `RH_new = 100 * [1 - ERA5_VPD/es_water(TA_tower)]`. When the site temperature makes the exact ERA VPD physically impossible or source `ERA5 TA/VPD/PA` components are invalid, skip that direct replacement and add a new safety hold. **Do not silently clamp VPD or borrow a neighbouring time.**
- Preserve Stage05's local TA/PA short-gap interpolations and unaffected physically permissible humidity candidates.
- **Outside flagged jump endpoints**, keep original physical US-Ton VPD QC0 values, dropping the paired Stage05 RH and VPD overrides to avoid internal inconsistency. Inside flagged endpoints, the user's newer explicit direct ERA5 instruction takes precedence, subject to physical admissibility.
- Original 754 Stage05 HOLDs remain an inherited ledger. 331 temperature mismatch/invalid tower-T holds are grouped for the user's neighbouring-tower rule (retain plausible tower TA). Physically invalid paired ERA at US-Syv (419) still remains held and is not allowed into derived data.

**Important provenance detail:** packaged `FLUXNET_ERA5_HH` is ERA5-derived/calibrated tower data; this operation does NOT fetch or claim separately gridded independent ERA5-Land. Directly replacing a Stage05 tower-temperature-normalized ERA RH candidate with exact `VPD_ERA` from the packaged ERA product can introduce different transitions. The accepted scope is **all eligible endpoints**, not a guarantee that the final half-hour VPD is smooth. The script produces exact counts and holds after actual operator execution.

## How to run on IRIDIS6

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/d83bc6d8d554c9bc19f099f3f274ba2a7d7b7e22"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage07"
  SCRIPT="$BASE/scripts/stage07/07_apply_jump_ERA5_vpd_three_sites.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage07/07_apply_jump_ERA5_vpd_three_sites.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --apply 2>&1 | tee "$BASE/stage07_apply.log"
)
```

The `--apply` mode will write one new `qcv5_stage07_applied/candidate_*` directory containing **three complete FLUXMET HH derived CSVs**, `stage07_applied_changes.csv`, `stage07_unsafe_ERA_target_holds.csv`, `stage07_inherited_754_holds.csv`, and `stage07_sha_receipt.json`. It creates an `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` safety marker. No original ZIP/BIF/CSV, Stage05 candidates, Stage06 reports, model cases, or Slurm jobs are modified.

**Current state: code published in GitHub, but no user Stage07 execution output yet.** No real-world count of valid direct ERA endpoints or unchanged QC0 can be certified until operator runs the script. Post-v5/DATM/spinup production approval is not implied by this isolated derived candidate.

# Batch04 — US-Syv SYVH3 final operator-PASS and ten-site source input QA next

**2026-10-26. Actual IRIDIS6 operator log received, not inferred.**

## Actual final US-Syv scientific data/forensic status

- **SYVH3 independent 438288-full-native-row audit PASS**.
- **18 exact 2021 half-hours** were amended in the **derived RH column only**, calculated from `RH = 100(1−VPD_F/e_s(TA_F))`. All original QC0 `TA_F` and original QC0 `VPD_F`, their QC columns and tower pressure **unchanged**; the final derived RH corrections are +0.787 to +1.497 percentage points. Historical raw Stage05/07 ERA-pair source-HOLD archive retained unchanged.
- **One source rounding-compatible oversaturation** remains documented: local 2008-03-09 13:00, original `TA_F=-6.234°C`, `VPD_F=3.842hPa`, `e_s(TA)=3.841976803313088hPa`, excess **`0.0000231966869hPa`**. Native VPD is stored with three decimal digits so this is below half the 0.001 hPa quantization unit. **Preserve original values; no blind zeroing/capping.** Other **438287** HH strictly pass the same saturation screen.
- All previous **297 user-approved original+filled site temperature substitutions** and **415 independently ERA5-Land reconstructed humidity points** preserved. Other nine sites' selected source paths/SHA remain unchanged.
- **Actually existing final output directory:**
  ```text
  /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved/candidate_20261026T034556Z_3372d66c
  ```
- **Final full native US-Syv CSV SHA256 `9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa`.**
- Exact ten-site source selector file:
  ```text
  /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved/candidate_20261026T034556Z_3372d66c/RESEARCH_TEN_SITE_MANIFEST.tsv
  ```
- Operator terminal results: `SYVH3 PREFLIGHT PASS`; `SYVH3 INDEPENDENT WHOLE SITE 438288 ROW DIFF AUDIT PASS exact_RH_only_reconciliations 18`; `SYVH3 18 ORIGINAL QC0 VPD RETAINED DERIVED RH CLOSED SCIENCE CANDIDATE PASS`.
- **All known 616 original US-Syv source HOLD timestamps now have their distinct numeric/science treatment recorded**, while all original source-HOLD provenance remains archived. This is a **research candidate only**, not a claim of final input approval or model run.

## Next independent ten-site selected forcing audit — not executed on IRIDIS yet

[SYVH4 ten-site read-only QA script](../scripts/manual_review/stage_syvh4_final_ten_site_manifest_readonly_gate.py), pinned GitHub commit **`5f58e37be6026e9db647d78e7df95bdac8acd361`**, performs:

1. Final SYVH3 receipt, final US-Syv source SHA, exact 10-site roster, exact prior nine source path+SHA unchanged and other provenance guards.
2. **SHA each of 10 selected full FLUXMET_HH CSVs**, stream and audit every native half-hour record for continuous 30min clock and TIMESTAMP_END, temperature and VPD physical consistency at the recorded T, RH range and closed humidity within source VPD quantisation tolerance, PA_F physical screening and missing/met QC counts. Log examples of any remaining issue; do not silently fix/discard.
3. Write only timestamped **small audit JSON and TSV under HOME** when requested; raw sources, previous full site candidates and input manifest untouched.
4. Keep site approvals / Post-v5 / DATM/CIME / Slurm / spinup explicitly **BLOCKED** until an independently verified all-ten-site science and technical sign-off. The nine other site temperature science issues and user decisions must not be accidentally marked fixed by finishing US-Syv.

Run:

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="5f58e37be6026e9db647d78e7df95bdac8acd361"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  FINAL="/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved/candidate_20261026T034556Z_3372d66c"
  mkdir -p "$BASE"
  SCRIPT="$BASE/stage_syvh4_final_ten_site_manifest_readonly_gate.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/stage_syvh4_final_ten_site_manifest_readonly_gate.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --manifest-dir "$FINAL" --report \
    2>&1 | tee "$BASE/US_Syv_SYVH4_Batch04_TEN_SITE_READONLY_QA.log"
)
```

Expected terminal milestones:
- `FINAL SYVH3 SOURCE VERIFIED 9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa`
- Ten `SITE <id> FULL_HH ... SOURCE_SHA_PASS ...` lines and optional scientifically salient example excerpts
- `TEN SITE SCIENTIFIC QA TOTALS ... PRODUCTION_GATE NOT_APPROVED_RESEARCH_CANDIDATES`
- `TEN SITE FULL SOURCE CHECK COMPLETE; source and candidate immutable; no model jobs submitted`

**Scientist manual decision:** No new SYVH3 source-level RH/QC0/VPD decision required from operator log. **Whether any of the other 9 sites still has a source science gate requiring user human judgement remains unknown** until SYVH4 has actually run on these selected site files and the pre-existing manual temperature resolution ledger is reviewed. Never promise a model run for this check.

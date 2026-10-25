# Batch04 — manual 3-T research alternative CREATED by operator, full-source read-only verification next

**Date:** 2026-10-25. **Research-only output CREATED by operator; independent full-source audit NOW VERIFIED PASS** on IRIDIS6: 2 full site CSVs; 3 exact HH; 9 changed field cells only; original inputs/other eight site selections retained. Full original/derived science holds remain unresolved. See [operator-verified full-source audit and SHA values](MANUAL_THREE_T_FULL_SOURCE_AUDIT_VERIFIED_2026-10-25.md).

```text
MANUAL TRIAL SELF-TEST PASS: 3 HH isolated, QC2 ERA-derived provenance, no original overwrite
MANUAL PROPOSAL US-SP1 200010091800 ORIGINAL_T -6.9 ORIGINAL_QC0 TRIAL_T 14.370813 TRIAL_QC2 TRIAL_VPD 10.194556 METHOD EXACT_RECEIPT_VERIFIED_ERA5LAND_T2M_INTERPOLATED_TO_NATIVE_UTC
MANUAL PROPOSAL US-SP1 200010091830 ORIGINAL_T -7.1 ORIGINAL_QC0 TRIAL_T 13.776224 TRIAL_QC2 TRIAL_VPD 9.445459 METHOD EXACT_RECEIPT_VERIFIED_ERA5LAND_T2M_INTERPOLATED_TO_NATIVE_UTC
MANUAL PROPOSAL US-SRG 201903191200 ORIGINAL_T 0.718 ORIGINAL_QC0 TRIAL_T 20.1365 TRIAL_QC2 TRIAL_VPD 17.060332 METHOD MANUAL_INTERPOLATION_BETWEEN_TWO_QC2_ERA_SUBSTITUTED_FLANKS
MANUAL SCIENCE: ORIGINAL 8/8 TEMPERATURE HOLDS STILL UNRESOLVED; US-Syv 606+10 DEFERRED
MANUAL TRIAL RESEARCH DATA CREATED /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_temperature_alternative_not_approved/candidate_20261025T183441Z_254f8181
MANUAL TRIAL EXACTLY THREE HALF-HOURS; ORIGINAL FLUXMET/Stage14/Stage15/OTHER EIGHT SITES UNCHANGED
NOT APPROVED FOR POST-v5, DATM, CIME, SLURM, SPINUP
```

**Candidate path:** `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_temperature_alternative_not_approved/candidate_20261025T183441Z_254f8181`

This is a **separate** independent research scenario from Stage15's 2000 US-SP1 two-point *tower-neighbor interpolation* scenario (13.1816667 and 15.3633333°C with trial QC1). It is **not** an update of instrument-observed temperature QC; in the Stage14 source the three source measurements remain QC0. In the research alternative, all three edited TA use trial QC2 due to ERA provenance; VPD is recomputed at retained Stage14 RH. US-SRG's neighbors were themselves **QC2 ERA-substituted**, so its interpolation is not independent measured tower truth.

**Status distinction:** independent full row-by-row audit is now **operator-VERIFIED PASS**, as recorded in the report linked above. Before considering this trial technically verified, compare the two full proposed site CSVs to both pinned Stage14 full CSVs, and check exact 3 native timestamps × only 3 altered columns (`TA_F,TA_F_QC,VPD_F`), timestamp and row preservation (368,208+315,600 HH), full output SHA256/receipt/provenance, the 10-site manifest and 8 other unchanged site entries, and thermodynamic VPD closure. The pinned **read-only verification script** below performs this independent check.

## Reproduction: independent full-source read-only audit (COMPLETED PASS on IRIDIS6)

Script: [verify_manual_three_T_trial_full_source_readonly.py](../scripts/manual_review/verify_manual_three_T_trial_full_source_readonly.py), committed as GitHub SHA `212ef265089c65c4854568e129da12b370085ab7`.

Run on IRIDIS6 with the existing `clm_fates_env`; this only uses Python standard library (`csv`, `json`, `hashlib`, `math`) and does **not** need numpy, netCDF4, network downloads or additional CDS queries:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  URL="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="212ef265089c65c4854568e129da12b370085ab7"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"

  mkdir -p "$BASE"
  SCRIPT="$BASE/verify_manual_three_T_trial_full_source_readonly.py"
  curl -fLsS --retry 3 \
    "$URL/$COMMIT/$REL/verify_manual_three_T_trial_full_source_readonly.py" \
    -o "$SCRIPT"

  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --self-test
  python3 -u -B "$SCRIPT" --audit \
    2>&1 | tee "$BASE/manual_three_T_full_source_audit.log"
)
```

**Success gate:** `MANUAL AUDIT PASS 2/2 FULL-SOURCE CSV, 3/3 HALF-HOURS, EXACTLY 9 CELLS`; `8/8 OTHER-SITE MANIFEST ENTRIES IDENTICAL`; `ERA-ORIGIN QC2`, RH physical closure and SHA256 verification all PASS. The operator returned the expected **PASS** for complete row, field, SHA256, VPD/RH, QC2 and unchanged other-eight-site checks. This establishes **technical research-file integrity, not scientific validation of an original-source repair**. No Post-v5/DATM/CIME/Slurm/spinup approval.

**Original research science gates remain:** eight source-temperature science HOLDs; US-Syv 606 older holds and 10 ERA edge cases deferred. There is **no Post-v5/DATM/CIME/Slurm/spinup approval**.

**Unrelated mixed log:** The same operator paste contains AmeriFlux **Batch03** Stage12T source VPD water-physics check. It was read-only on 3 site-years (US-Me6 2015/2017 and US-NR1 2022) and should not be interpreted as Batch04 temperature evidence.

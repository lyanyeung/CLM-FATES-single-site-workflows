# Stage74 complete 26/26 independent CDS gridyears — Stage75 source temperature scientific triage

Date: 25 October 2026. IRIDIS6 operator confirms the exact Stage74 blob `c21772aea4334b7e88997cca16df310012f9337b` passed syntax, self-test, 4-source-year plan, successful CDS download and original payload/NetCDF SHA+grid/calendar verification for all four, and final `STAGE74 AUDIT PASS`.

Original Stage74 immutable report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage74_four_missing_years_16874_Ho1_BZS_CDS_SHADOW_20261025T090751Z_d0953fbc`.

Final independent CDS newly verified source-years:

| Site | Year | Relevant original hard events | Independent NetCDF SHA256 |
| --- | ---: | ---: | --- |
| US-Ho1 | 2000 | 1,069 | `b51ca5ae84865b0e90d3c1034601b1b4461e9211ca3ed9bab2def8488156f747` |
| US-Ho1 | 2008 | 1,036 | `394fa99634cb439fe00f83157cc686c07f2e722af50be7412af7499265c3169e` |
| US-BZS | 2012 | 79 | `bc8d89ba42248a581255e78958c0f73e4abd2a5e868818233828fa6ca7231b9a` |
| US-BZS | 2011 | 7 | `842ff9cc6791d02561ca0d3697ebd46f4f0c166d17f1b0231fada9c2e6c3d7da` |

All **26 / 26** independent CDS ERA5 quarter-degree grid-years are now complete for the original Ho1/BZS hard source subpopulation. There are ZERO source-event holds caused by missing external CDS gridyear.

| Full original-source hard events | Status count |
| --- | ---: |
| Physically/numerically plausible RH/VPD/QBOT SHADOW candidates retaining original tower TA_F/PA, historical BADM UTC still HOLD | **15,199** |
| Source native TA_F QC nonzero; requires source-T confidence/neighbor investigation | **998** |
| Original TA_F is native QC0 but differs from independent CDS ERA5 t2m by more than 8 degrees Celsius | **677** |
| **All original Ho1+BZS hard humidity events** | **16,874** |

The 677 tower-vs-ERA holds were **82 at Stage73**, but rose with complete gridyear retrieval. These are *not* new errors introduced by CDS downloads; they were previously not evaluated due to absent independent year files. The 998 native T QC holds were likewise 995 at Stage73. 1,675 original source events remain in temperature-science HOLD; the other 15,199 are only numeric shadow candidates, not DATM-approved forcing patches.

## Pinned Stage75 read-only science audit

[Stage75 source](../scripts/stage75/75_full_26_gridyear_original_temperature_hold_science_triage.py) strictly checks the Stage74 26-year report, every original output SHA256, exactly 16,874 original site/time/source-row identities and the 15,199/998/677 breakdown. It verifies one-to-one BIF nominal local-to-UTC shadow but **does not certify historical offset dates**.

Stage75 produces a fresh isolated 1,675-event source-temperature science triage, with original FLUXNET native TA_F and TA_F_QC, independent CDS ERA5 T2M and processed FLUXNET TA_ERA (not independent of other ERA-derived information). Diagnostics include QC1/QC2/other original T provenance, native T vs CDS and source TA_ERA comparisons, original VPD source QC, per-year/season severity and exact contiguous 30-minute source-HOLD episodes. A difference between tower T and ERA5 T does NOT prove a tower sensor fault, particularly in cold weather, heterogeneous canopy/site or terrain mismatch. No replacement or correction is approved by Stage75.

Authoritative FLUXNET documentation states local standard timestamps without daylight saving time, with site UTC offset carried in metadata and explicit start/end averaging period timestamps: https://fluxnet.org/data/fluxnet2015-dataset/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/. The user-uploaded 2026 official site BIFs give nominal US-Ho1 UTC-5 and BZS UTC-9 but have no UTC_OFFSET_DATE_START: do not treat the workbook publication date as the historical offset's effective start. Check original source product notes/metadata for any special historical clock correction before model time-source release.

Stage75 script commit `e350e1492c852ea00ed7575f1b9c79a255464620`, Git blob `723cb02fb331cc8b5150442043e04b045a44af10`.

## One-paste IRIDIS6

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage75/75_full_26_gridyear_original_temperature_hold_science_triage.py"
  COMMIT="e350e1492c852ea00ed7575f1b9c79a255464620"
  EXPECTED="723cb02fb331cc8b5150442043e04b045a44af10"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage75/75_full_26_gridyear_original_temperature_hold_science_triage.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage75.log"
)
```

Expected final completion: `STAGE75 AUDIT PASS | 1675 original Ho1/BZS temperature holds classified, 15199 numerical humidity candidates retained`.

Stage75 is committed and lexically checked from exact GitHub source blob. It has not been executed on IRIDIS6. No original tower observations, Stage64-74 reports, old CDS files, formal NetCDF forcing, DATM, CIME, Slurm or model states are changed. The old Stage64 9,389 additional independent numeric humidity candidates across the rest of Batch02 are untouched.

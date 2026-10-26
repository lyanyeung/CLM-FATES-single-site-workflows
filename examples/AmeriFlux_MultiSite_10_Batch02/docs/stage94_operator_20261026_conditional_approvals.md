# Stage94 user approved conditional rules (26 October 2026)

User's explicitly stated science decisions:
1. Accept a proposed original-QC0 **temperature** correction only when the candidate is similar to the original native temperature immediately before AND after.
2. For US-Ho1 on **2000-12-27 09:00** (original 09:00 T -15.4 C QC1, 09:30 T 3.346 C QC2), replace original 09:00 temperature with ERA ONLY IF temperature BEFORE 09:00 is approximately 0 C.
3. For remaining episodes follow previously proposed evidence-qualified treatment: accept Ho2 wet ERA humidity and isolated longwave candidates when supported; accept original negative implied-RH VPD corrections if corrected candidate is physically valid. HOLD original US-ICt 2016-05-21–23 87 consecutive QC0 VPD until source/sensor validity is confirmed. Do not treat ERA disagreement alone as proof of a bad measured tower value.

The [Stage94 code](../scripts/stage94/94_qc0_final_operator_decision_table.py), commit `edf1071e27a76c2cb3f60b740e4ed9b8d4d7415f`, Git blob `9193bc91a92e27b0deca87030697ae222919b65a`, implements these user decisions as **an isolated immutable original-source QC0 decision ledger** from the actual Stage93 manifest (all 122 original QC0 values/30 time-contiguous episodes). It does not overwrite any original, prior forcing, technical NC, CIME or model job. Existing Stage87/92 technical NetCDF still contain earlier science-unapproved candidate edits. Explicit HOLD means not production-eligible.

Numerical operationalizations to make the user's qualitative rules reproducible:
- Temperature: candidate within **4 C of each original native neighbor**, those originals within **6 C of each other**, and original-candidate change >=5 C.
- Ho1 "around zero": **both** 08:00 and 08:30 original (not repaired candidate) temperature within **[-2,+2] C**. This is a deliberately conservative interpretation. **Prior Stage89 review recorded preceding last original QC0 T about -15.1 C**, suggesting condition may be false; run the exact Stage93 source-boundary check, do not assume.
- Longwave: original isolated spike >=120 W/m2 against neighbor midpoint, neighbor spread <=55 W/m2, candidate within35 W/m2 of midpoint and within80 W/m2 of ERA.
- Ho2 humidity: candidate VPD physically valid at original measured T and the original QC event identifies the strong independent ERA wet repair.
- Other VPD: approve only if every original native T/VPD implies RH<0% and every candidate physical; 87-HH ICt stays HOLD even if ERA candidate looks plausible.

Unresolved cases may require later specific scientific decision; **Stage94 approved conditional candidate records are decisions about already-existing candidate CSV values, NOT activation of any NC for model use**. Ho1 conditional replacement needs a coherent separate versioned T+VPD/QBOT overlay if the pre-09 evidence qualifies; it is not silently applied by Stage94.

## One paste IRIDIS6

```bash
(
  set +e
  COMMIT="edf1071e27a76c2cb3f60b740e4ed9b8d4d7415f"
  BLOB="9193bc91a92e27b0deca87030697ae222919b65a"
  REL="examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage94/94_qc0_final_operator_decision_table.py"
  OUT="$HOME/Batch02_stage94_operator.py"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$OUT"
  test "$(git hash-object "$OUT")" = "$BLOB" || exit 1
  python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf8").read());print("SYNTAX PASS")' "$OUT" || exit 1
  python3 -B "$OUT" --self-test || exit 1
  python3 -B "$OUT" --audit 2>&1 | tee "$HOME/Batch02_stage94_user_decisions.log"
  RC=${PIPESTATUS[0]}
  echo "STAGE94_EXIT_CODE=$RC"
  grep -E 'STAGE94 HO1 PREVIOUS|STAGE94 REVIEW CATEGORY COUNTS|STAGE94 OPERATOR APPROVAL|STAGE94 APPROVE|STAGE94 REPORT|STAGE94 USER CONDITIONAL|REVIEW B02-94-' "$HOME/Batch02_stage94_user_decisions.log" | tail -44
)
```

Outputs in new `reports/stage94_*`: `30_QC0_episodes_operator_DECISION_TEMPLATE.csv`, `operator_approved_conditional_QC0_episodes.csv`, `operator_remaining_QC0_HOLD_episodes.csv`, `Ho1_2000_Dec27_0900_user_conditional_ERA.json` and checksum manifest. `production_DATM_approved=False`.

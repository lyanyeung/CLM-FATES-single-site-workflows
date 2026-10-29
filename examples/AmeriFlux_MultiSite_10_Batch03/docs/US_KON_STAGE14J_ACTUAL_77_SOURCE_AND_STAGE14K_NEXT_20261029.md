# US-Kon — 2026-10-29 actual Stage14J 77 exact source-QC results; one Stage14K 68+9 followup

## ACTUAL operator IRIDIS6 results, not guessed

Stage14J pinned original/QC full source analysis **SUCCESS**, 2026-10-29 04:44 UTC. Site 2005–2020 native **280320 30-minute NOLEAP rows** (exact immutable parent), latest sealed Stage12AY output:

\`\`\`
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12ay_Kon_FINAL_science_candidates_and_sealed_HOLDS_20261026T132804Z_87d94e7a
\`\`\`

Actual Stage14J signed-only report:

\`\`\`
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/US_Kon_77_original_QC_and_ERA_research_candidates_20261029T044439Z_c1845aab
\`\`\`

Original verified Stage12AY SHA256 receipt \`ce95d631f87b01c68e5373e99f671f050c61f781311fdd20dbdd7a9410cdf011\`, original tower input SHA256 \`f228c7be096f5b79462d5281c80a15a0768c3ef6264853af93753889882777c0\`, original companion ERA SHA256 \`3aacd53fae73f18e4c7ea305195a246d977969d4548cd0e461aa64bb461c25c9\`.

- **77** total remaining selected \`VPD_USE\` and \`QBOT\` identical missing native halfhours, partitioned into **35** exact source-native discontinuous/consecutive events.
- **68** routine missing HH: original paired ERA humidity evaluated at selected site T+PSRF creates finite, water/ice physically consistent VPD and QBOT at **all 68/68** individual times. Method is still low-confidence reanalysis hypothesis, not true measured humidity or yet an observation/source QC0 cross-validation.
- **9 protected scientific source holds** are exact native keys:
  \`201102220830\`, \`201102220900\`, \`201102220930\`, \`201105261100\`, \`201109291830\`, \`201110150730\`, \`201110230730\`, \`201202251030\`, \`201208050900\`.
  Their original T QC includes QC0 and QC1; original VPD QC1 except \`201109291830\` original VPD QC2. The T−ERA differences reach **+5.405°C** (201102220900) and **−6.374°C** (201109291830). Some source T is reliable QC0 but VPD is QC1; others are T/VPD mixed. **Do not treat QC0 temperature as QC0 VPD; do not bulk ERA-replace these 9.**
- **0** original tower VPD QC0 among these 77 missing cases. Many routine 2014 source gaps are source VPD QC2 (ERA-linked), and Stage14J explicitly protected original measurements and source QC. Individual physics pass does NOT guarantee bounded temporal halfhour joins or scientifically independent evidence.

## Explicit one-pass next research decision

[Stage14K 68 routine source-humidity transfer, nine source hard holds untouched](../scripts/stage14/14k_US_Kon_68_ERA_RH_only_9HOLD_isolated_onepass.py). Using the **actual verified fixed Stage12AY and actual Stage14J full source ledger**, in one run:
1. Require both exact signed receipts, 77 matching native timestamp keys, 9 original protected keys, 68 one-to-one source candidate values, all original source years and model columns. Preserve all old nonmissing source and other meteorology exactly.
2. Insert \`VPD_USE/QBOT\` in exactly **68 previously missing routine** HH, derived previously from companion ERA *relative humidity* transferred to original selected site TA/PSRF; no T/PSRF/source QC edits.
3. Keep **exactly 9** original protected source events missing, and never claim resulting incomplete file is DATM-ready.
4. For **all 35 original missing-event groups**, audit each native 30-min boundary and interior VPD/RHwater/QBOT jumps; explicitly report every >4hPa, >20pp and >0.003 kg/kg discontinuity and any neighbouring still-missing hard holds. The model-water closure of newly modified rows must pass. Also report existing source physics issues rather than rejecting prior signed records unrelated to the 68 new edits.
5. Save a new isolated \`science_trials/US_Kon_68_ERA_RH_9HARD_HOLD_SCENARIO_*\` CSV and original QC/ERA source/hold ledger, event/boundary tables and a SHA receipt. **No originals overwritten, no CIME, Slurm, DATM, AD400**.

As of this document **Stage14K is NOT confirmed executed on IRIDIS6**. GitHub source fixed at \`cdabe4980f41ac91a6e8126e92e345690b76014f\`, Git blob \`b7b9f475ef4551a19f6dd4aba43811fe69bbeec5\`. Its SHA has been verified via GitHub but full HPC source input execution must be observed.

\`\`\`bash
(
 set -euo pipefail
 F="$HOME/US_Kon_68_9_once.py"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/cdabe4980f41ac91a6e8126e92e345690b76014f/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14k_US_Kon_68_ERA_RH_only_9HOLD_isolated_onepass.py" -o "$F"
 test "$(git hash-object "$F")" = "b7b9f475ef4551a19f6dd4aba43811fe69bbeec5"
 python3 -B -c 'import pathlib,sys; f=pathlib.Path(sys.argv[1]); compile(f.read_text(),str(f),"exec"); print("SYNTAX PASS")' "$F"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_Kon_68_9_once.log"
)
\`\`\`

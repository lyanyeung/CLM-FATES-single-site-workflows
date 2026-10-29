# US-MOz — 2026-10-29 actual Stage14G QC-aware original 19:30 bridge PASS; Jan09 final source task

## Operator's ACTUAL 14G successful IRIDIS6 stdout

- Original FLUXMET native original source at 2005-01-05 19:00, 19:30, 20:00 = **TA_F_QC1 and VPD_F_QC1** at all three hours. First 27-HH reanalysis event ending 2005-01-06 09:00 = QC1/QC1; 09:30 = QC2/QC2. No original QC0 source anchor for this episode.
- User's explicitly requested **one half-hour QC1 interpolation at 2005-01-05 19:30** was actually applied in an **independent Stage14G research sensitivity only**, using native 19:00 original QC1 and native 20:00 Stage14F ERA5-Land research candidate, interpolating original-temperature and actual water vapor e, then regenerating VPD/TBOT/QBOT.
- One real changed native halfhour: **original 19:30 T=+5.185°C -> +2.186743°C, VPD=0.243 -> 0.087334 hPa, QBOT=0.005432 -> 0.004465 kg/kg**, interpolated actual e=7.065627 hPa.
- All **three** actual source-native edges are now below 4°C and 4hPa: 19:00→19:30 **ΔT=2.886257°C, ΔVPD=0.144666 hPa**; 19:30→20:00 **2.886257°C and 0.123976 hPa**; 2005-01-06 09:00→09:30 **1.445860°C and 0.009262 hPa**.
- **315360** full 18-year model input halfhours: zero coupled water-based TA/TBOT/VPD/QBOT closure failures. Exactly 27 earlier Stage14F reanalysis numeric sensitivity slots and 40 separately operator-approved Stage13L slots **unchanged**. Original source, earlier signed trial, case, model and Slurm unchanged.

Actual Stage14G independent output:
\`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_MOz_14G_QC1_LEFT_EDGE_ONE_HH_SENSITIVITY_20261029T042521Z_dcda1a16\`.

**Decision:** Preserve this as the current numerically complete research sensitivity for US-MOz. Stage14G solves the selected one-hour joined discontinuity, but physical smoothness is not proof that QC1 is independently measured true tower T or VPD. Do not classify 27 previously unapproved reanalysis rows or the 1 newly interpolated source hour as measured observational repairs merely from this pass. Post-v5, DATM, AD400/Normal400 remain unapproved.

## Last remaining original-source US-MOz Jan09 question — consolidated ONE read-only action

Historical original signed Stage13I source inventory shows:
- 2005-01-06 13:00→2005-01-09 10:00 **139 contiguous source T QC1 halfhours**, mixed positive and negative tower-versus-ERA discrepancy;
- two later Jan09/Jan10 source T QC1 original intervals: Jan09 11:30–12:30 (**3 halfhours**) and Jan09 13:30–Jan10 09:00 (**40 halfhours**), latter with original T−ERA down to −18.14°C.
- Do not assume these are 139+3+40 extra *missing* hourly values: the **numeric full research source already has zero missing**; this is a source-provenance science issue.
- Do not auto mass-edit 139+3+40 original source QC1, or assume the adjacent QC2 ERA downscaling is independent measured QC0. The user's policy requires source-specific original QC0/QC1/QC2 inspection, not just smooth artificial model joins.

[Single-use Stage14H original source Jan09 full 384-HH Jan03–10 read-only QC classifier](../scripts/stage14/14h_US_MOz_Jan09_original_QC_onepass_final_triage_READONLY.py). It uses the actual signed Stage14G parent and original release FLUXMET/ERA manifests. It will print all **48 Jan09** native source/QC/selected comparisons, 139/3/40 source QC runs and negative/positive T source disagreements with actual timestamps, all Jan08–Jan10 native QC-grade transitions and >4°C/hPa boundaries. It writes only a new SHA-receipted **report**, no forcing edits. One human final disposition then: preserve valid QC0, classify QC1 and ERA-dependent QC2 separately, and decide whether any exact subset is defensible to reconstruct as low-confidence research only. This avoids random new per-hour repair waves. **Stage14H has NOT YET been run on IRIDIS6**.

Pinned source: Git commit \`b817cf8bd96823c62167f6bbf3c20791cdb23f9e\`, Git blob \`ad59c3614c0e32e57fa5f6f038de31df940ecbfa\`.

\`\`\`bash
(
 set -euo pipefail
 F="$HOME/US_MOz_Jan09_last_onepass.py"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/b817cf8bd96823c62167f6bbf3c20791cdb23f9e/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14h_US_MOz_Jan09_original_QC_onepass_final_triage_READONLY.py" -o "$F"
 test "$(git hash-object "$F")" = "ad59c3614c0e32e57fa5f6f038de31df940ecbfa"
 python3 -B -c 'import pathlib,sys; f=pathlib.Path(sys.argv[1]); compile(f.read_text(),str(f),"exec"); print("SYNTAX PASS")' "$F"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_MOz_Jan09_last_onepass.log"
)
\`\`\`

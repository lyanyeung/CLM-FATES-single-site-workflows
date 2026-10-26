# US-Syv: operator authorises ERA-derived replacement of ALL remaining anomalous T — QC0 and QC1

**User explicit direction 2026-10-26:** "US-Syv全部用ERA5的来代替异常的TA，第一类和第二类都是。然后继续给我们修复。"

This **supersedes** the earlier advisory to retain 2001-Oct02 (two original QC0 HH) and 2007-Mar29 (two original QC0 HH) on the strength of the source-minus-grid discrepancy; the operator explicitly chooses to substitute **both classes**, including all **24 original-source QC0** and **61 original-source QC1** remaining old temperature science HOLDs, **85 half-hours in 30 contiguous runs**. The **106 previously authorised** six US-Syv ERA-temperature intervals **remain untouched**, as do prior full source alternatives for US-SP1 and US-SRG and all original FLUXNET raw datasets.

## Provenance distinction and exact scientific replacement

The source chosen is the **exact local-standard native half-hour `TA_ERA`** from the original FLUXNET **paired processed ERA-derived meteorology**. This is **not the separately retrieved independent ERA5-Land archive**. It is the same ERA-origin source already selected for the operator-verified 106 US-Syv replacements. New temperature is `TA_F_trial=TA_ERA`, with `TA_F_QC_trial=2`; **no daily/site bias fit**, and no editing of `TA_F_MDS` or its QC provenance.

Source-verified original temperature error inventory:

| Group | Source code / evidence | Original HOLD HH | Current user decision |
| --- | --- | ---: | --- |
| First group: anomalous **QC0** original observations, including previously advised 4 ambiguous 2001-Oct02 & 2007-Mar29 observations | 12 original contiguous source-HOLD groups | **24** | Replace with same-native FLUXNET processed `TA_ERA` |
| Second group: anomalous **QC1** MDS-filled source `TA_F`, 18 runs, including original 2001 Nov, 2002 May, 2007 May, 2008 Apr events | 18 original contiguous source-HOLD groups | **61** | Replace with same-native FLUXNET processed `TA_ERA` |
| **All newly approved old source-T holds** | **30** continuous original HOLD runs | **85** | **YES** |
| Previously approved US-Syv six source-T anomalies | full original 106-HH file SHA already verified | **106** | **PRESERVE** |

**Crucial extension protection:** the original source HOLD intervals did not cover some untrustworthy adjacent TA values (e.g. 2003-May30 after original 10:30 source-HOLD end, QC1 2002-May and 2008-Apr source fill tails). The new research-only script therefore extends from the **85 original exact seed HH**, in both directions **only** through contiguous original QC0/QC1 half-hours with source `TA_F−paired TA_ERA ≤ −8°C`. It **stops** on a healthy/nonmatching HH, on QC2, or at a previously approved 106-HH selection. A **±96h original-source flank** must fully encompass each continuous anomaly, otherwise the script *fails before any write* instead of inventing a boundary. It additionally caps automatic extensions at **1,600 HH** and refuses an output with a **greater than 11°C** immediately adjacent corrected-vs-retained boundary jump. These are explicit conservative *implementation constraints*, **not a proof of instrumental error**; no arbitrary other QC0 points elsewhere in the 438288-HH record are touched. The runtime reports **exact extension count and each corrected episode** before writing. If boundary/source checks fail, revisit the evidence and revise selection rather than forcing an unsafe output.

For all selected temperature points: use the same-native source-packaged `VPD_ERA` **only if** nonnegative and no greater than saturation at the new ERA T; otherwise retain already physically valid prior trial VPD; otherwise preserve unchanged prior VPD/RH and mark as **explicit humidity HOLD**. An admissible VPD produces `RH=100(1−VPD/e_s(T))`, with `e_s(T)` over liquid water, bounded within [0,100]. No cap-based fabrication of VPD or humidity values. Validate all full-file 438288 original native rows after writing; all unapproved timestamps must retain **identical original parent candidate bytes in each CSV field**.

## Source pinned run instructions (IRIDIS6; no git pull)

[New standalone 85HH+continuation source-guarded implementation](../scripts/manual_review/apply_US_Syv_remaining_85_T_holds_with_evidence_extensions.py), GitHub pinned commit **`13f811be3780ced19fde6d826a7e562af7b05cd3`**:

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="13f811be3780ced19fde6d826a7e562af7b05cd3"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  SCRIPT="$BASE/apply_US_Syv_remaining_85_T_holds_with_evidence_extensions.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/apply_US_Syv_remaining_85_T_holds_with_evidence_extensions.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --apply 2>&1 | tee "$BASE/US_Syv_all_85_QC0_QC1_ERA_T_apply.log"
)
```

**Expected terminal markers, subject to actual IRIDIS6 results:**

- `US-SYV 85 ORIGINAL QC0+QC1 USER APPROVAL SELF-TEST PASS`
- `USER-APPROVED US-SYV ALL QC0/QC1 T HOLD PREFLIGHT PASS` plus exact added contiguous HH, all source/QC/VPD categories and boundary audit
- `INDEPENDENT US-SYV FULL OUTPUT SCIENCE AUDIT PASS` with 438288 halfhours
- `US-SYV ALL REMAINING USER T APPROVALS REPAIR FULL AUDIT PASS`, complete source SHA and new 10-site research manifest path

Output path will be under `manual_US_Syv_remaining_T_all_QC0_QC1_ERA_research_candidate_not_approved/candidate_...`, with a full **438288-HH Syv** source candidate, 10-site exact input manifest retaining other nine site selections, new per-HH source/ERA/QC/RH provenance ledger and science receipt. **Do not infer output files exist before user runs this script on IRIDIS6.**

## Remaining scientific work after this stage

- **US-Syv humidity:** prior 106-HH repair introduced **zero new humidity HOLDs**, but before this stage the old source HOLD ledger still had **518 distinct old HH**, of which **500** were physically invalid for VPD saturation at their retained T and **18** passed this one physical check. These sets overlap the **85** newly approved T science HOLDs, so do not subtract 85 from 500 without auditing the *new candidate* and the source H/H timestamp union. Physically screened humidity-only repair for the residual records is next; generic direct `VPD_ERA` copying is prohibited when `VPD_ERA>e_s(T)`. An independent ERA5-Land dewpoint/RH correction can be used where previously independently verified sources exist and native clock offsets match.
- **Other nine Batch04 sites:** no new original source-temperature decisions demonstrated by latest Batch04 source checks. Preserve earlier US-SP1 2008 retain-original-TA user decision and US-Seg provisional retain-TA Stage14 humidity-only alternative. Those are separate historical scientific decisions, not overridden by this **US-Syv-only** order.
- **Science gate:** no source-blind release of existing candidates into Post-v5/DATM/CIME/Slurm/CLM-FATES spinup until a separate 10-site final quality-control and physics audit.

**Execution status:** Code & manual policy published to GitHub; **not run on IRIDIS6 in the current conversation**. The actual candidate validity/counts must be taken from user execution logs, not inferred.

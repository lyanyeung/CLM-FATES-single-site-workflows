# Batch04 US-Syv — operator verified six direct ERA-temperature runs / 106 HH and exact remaining manual-science gate

**Source:** operator-provided complete IRIDIS6 execution stdout dated **2026-10-26**. This confirms the last user-approved research alternative was actually built, not just preflighted. It DOES NOT authorise the ten-site candidate as ready for Post-v5/DATM/CIME/spinup.

## Successfully completed, source-verified research alternative

- Six exact manually authorised US-Syv local-standard-time native HH windows: **2007-Feb08 17:30–21:30 (9), Feb09 17:30–23:30 (13), Feb10 17:30→Feb11 07:00 (28), Feb11 17:30→Feb12 07:00 (28), Feb12 17:30–22:30 (11), 2003-Apr27 11:30–19:30 (17) = 106 HH**.
- Written **2017-02-10/11** was resolved to **2007-02-10/11** based on actual source hold year as described in the user-authorised contract.
- Complete 438288-HH original Stage07-derived parent and new candidate comparison: **`INDEPENDENT FULL FILE SOURCE AUDIT PASS`**, 106 selected native HH, **319 field-cell changes**. Out of six approved periods, **17 original `TA_F_QC=0`** (original observed) and **89 original `TA_F_QC=1`** (filled, NOT raw observed). New candidate `TA_F` at all 106 is same-native packaged processed FLUXNET ERA `TA_ERA`, research `TA_F_QC=2` (ERA-origin fill).
- **`HUMIDITY_TREATMENT_COUNTS {'PAIRED_FLUXNET_ERA_VPD_VALID_AT_REPLACED_ERA_T': 106}`**, 0 extra humidity HOLD from these replacements, VPD and RH checked at new TA. Paired packaged `VPD_ERA` is verified against `e_s(TA_new)` in this specific selection; this does **NOT** imply packaged `VPD_ERA` is safe on the 500 untouched sites/times.
- Research-only full US-Syv candidate output directory:
  ```text
  /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_six_ERA_T_106HH_science_candidate_not_approved/candidate_20261026T010755Z_591ef88f
  ```
- New complete Syv candidate **SHA256 `8ac03873ad573e2885569f371ce6a413d4f3f230d7f473ece6c7e20bb7bf1b73`**.
- New ten-site research manifest under that directory: `RESEARCH_TEN_SITE_MANIFEST.tsv`. **Other nine site source references unchanged**, including verified US-SP1 137-HH Oct2007 and separate 2000 two-HH, plus US-SRG 2019 single-point alternative. No original FLUXMET, Stage05/07, prior science alternatives, model or DATM files overwritten.

## What still requires the researcher's *specific* manual judgement

**No more temperature decision is required for the just approved six Syv windows.** From **616 unique old Syv source-HOLD HH**, the direct user-authorised T substitute covered **98 exact old HOLD HH**, and another **8 newly user-authorised adjacent times** were outside the old HOLD ledger. **518 old HOLD HH** remain with original source science HOLDs. The output partitions these 518 as **500** stage07-derived **VPD basic physical saturation failures** and **18** samples whose T/VPD pass this *one basic check* but whose original reasons still need classification. These categories do not add to the 85 source-temperature-source discrepancy HOLDs; they overlap.

Of these **518 old HOLDs, exactly 85 HH** are original `SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID` cases, divided into **30 separate contiguous native half-hour runs**. The user has not authorised temperature changes in these separate intervals. **Only potentially unresolved science-temperature decisions are in these 30 runs**; they must be inspected using exact source T+QC, `TA_F_MDS`, paired `TA_ERA`, and before/after flanks before asking to replace T. Some cases likely source gap-fill artefacts and can be fixed conservatively by a new separate proposal after source verification, but the user has repeatedly required direct numeric flanks.

Examples of the **first** HH in different still-held temperature runs, from the current operator stdout (NOT enough by themselves to determine start/end outside current HOLD):

| Native episode first HH | Original TA_F (°C) | Same-native `TA_ERA` (°C) | Original TA QC | Run HH |
| --- | ---: | ---: | ---: | ---: |
| 2003-05-30 09:30 | **−29.101** | 10.859 | 0 | 3 |
| 2003-05-30 07:30 | −10.369 | 11.613 | 0 | 3 |
| 2002-05-22 19:30 | −0.475 | 18.080 | 1 | 11 |
| 2007-05-10 19:30 | 3.507 | 22.862 | 1 | 5 |
| 2003-05-08 11:30 | 5.528 | 16.407 | 0 | 6 |
| 2008-04-04 18:30 | −6.084 | 5.019 | 1 | 5 |
| 2001-11-01 20:00 | 1.523 | 12.343 | 1 | 8 |
| 2002-05-21 19:30 | −0.395 | 13.904 | 1 | 5 |
| 2001-08-14 10:30 | 0.000 | 20.472 | 0 | 1 |

Here **QC0** refers to original observed-source product, **QC1** to filled original product, **QC2** to ERA-origin fill. Grid/T source disagreement does not itself prove that a credible original tower observation is incorrect.

**Remaining 500 physically invalid VPD HH** (overlapping the 85 T anomalies) can be queued for humidity-source-independent corrections **only where** source validated paired ERA5-Land dewpoint/RH or other physically consistent VPD exists; **do not globally replace `VPD_F` with packaged `VPD_ERA`**, because those products are sometimes themselves above saturation at retained T. The 18 physically valid legacy HOLDs can be evaluated by original reason and source evidence and not automatically deleted from scientific provenance.

## Immediate next operator command: all 85 T HH with real before/during/after temperature, QC and packaged ERA

A new **read-only** GitHub source-pinned script: [`review_remaining_US_Syv_85_temperature_holds_30_runs_before_after.py`](../scripts/manual_review/review_remaining_US_Syv_85_temperature_holds_30_runs_before_after.py), commit **`90582c165e330b1f169269f26fdb6064fec718ca`**. It validates the exact final user-approved 106-HH Syv CSV SHA and receipt, original native/ERA SHA, earlier Stage07 parent, source Stage05 606 historical holds, then derives **85 untouched original T-discrepancy HH in 30 consecutive native timestamp episodes**. It prints all 85 source hold HH **plus ±2 h of original T/QC, MDS, source-packaged ERA and final Syv candidate T/VPD** around each run, records original QC0/1/2 distribution and makes an optional new CSV under HOME. **Do not guess missing before/after temperatures from one first-HH value**.

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="90582c165e330b1f169269f26fdb6064fec718ca"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  mkdir -p "$BASE"
  SCRIPT="$BASE/review_remaining_US_Syv_85_temperature_holds_30_runs_before_after.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/review_remaining_US_Syv_85_temperature_holds_30_runs_before_after.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --report 2>&1 | tee "$BASE/US_Syv_remaining_85_T_30_runs_full_source_review.log"
)
```

**Status:** This next read-only review script is committed and has not been executed on IRIDIS6 in supplied logs. **No next-source science decisions should be inferred until its exact before/after values are returned.**

Also preserve the user's other decisions: US-SP1 2008 Jan–Feb full cold episodes **retain `TA_F`**, US-SP1 2007 Oct 137-HH ERA-daily-bias research trial, US-SP1 2000 2-HH ERA5-Land alternative and US-SRG single-HH alternative, and US-Seg 2016 provisional tower T retention + Stage14 humidity-only closure. No model release.

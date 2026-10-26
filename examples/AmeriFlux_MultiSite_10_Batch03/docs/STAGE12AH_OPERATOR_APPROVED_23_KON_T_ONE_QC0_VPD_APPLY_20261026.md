# Stage12ah — 2026-10-26 direct operator approval, 23 US-Kon T and one exceptional QC0 VPD

**Operator explicitly approves** all **23** original US-Kon site-native `TA_F_QC=1` isolated temperature spikes documented in `docs/STAGE12AG_VERIFIED_KON_TEMP_QC_23_INTERPOLATION_CANDIDATES_20261026.md`. They must be interpolated only from exact immediately preceding and following **source measured `TA_F_QC=0`** 30-minute tower observations. This is a 23-row exact list of original-native timestamps — **not** a blanket policy to alter all QC1 T in the site. In a **new separate successor to sealed Stage12g**, update `TA_USE` °C and `TBOT` K accordingly, using full-precision original-source values; mark VPD_USE and QBOT science **HOLD** for exactly these new-T rows pending later coherent paired-original ERA-RH treatment. Original raw FLUXNET/ERA files and all original Stage12g source/HOLD bytes stay untouched. Do not alter the other 10 earlier identified QC1 source temperatures.

The operator separately explicitly approves one original `VPD_F_QC=0` **exception** at US-Kon `200809260530`, source original VPD 18.334 hPa vs original QC0 immediate-neighbor `200809260500`=2.744 and `200809260600`=2.858 hPa. Change only this existing G held humidity point in new source-native derivative to interpolated `VPD_USE` **2.801 hPa**, keeping original measured T/P; recompute `QBOT` from water saturation vapour pressure and specific humidity formula at original `TA_USE` and `PSRF`. Record original observed QC0 number and explicit authorized override. **No other measured source QC0 humidity changes.**

**The operator has NOT yet authorized** the 34 US-Kon QC1/QC2 center VPD event source-harmonization replacements or any other original QC0 anomaly. Preserve 34 old G center VPD holds. No model/DATM/Slurm/Spinup promotion; retain `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` and SHA manifest.

[Stage12ah operator-approved isolated successor application Python source](../scripts/stage12/12ah_apply_APPROVED_Kon_23_T_and_QC0_VPD_single_20261026.py).

**Pinned GitHub commit:** `c31e4f0c9e021833e89791ca0a6c87d9a3f99576`. **Source Git blob:** `852ac785d6cd8b07cbc99cde3024a41e13568a59`.

`--self-test` (no inputs), `--check` (SHA-check all sealed reports/original sources, 24 only source QC and physics validation, no writes), `--apply` (new self-contained SHA-sealed US-Kon full NOLEAP derived CSV and 23 + 1 provenance reports). The run has NOT yet been performed on IRIDIS6. Once the user provides actual PASS output, update status with the new absolute path and resulting VPD missing counts.

**Next scientifically required action:** reconcile the 34 old Kon center humidity holds **plus physically inconsistent QC1/2 existing neighbors at temperature-edited events**. Prepare separate read-only paired-original ERA-RH event/edge comparisons after source T repairs, then seek grouped operator decision and apply only approved humidity repair; do not extrapolate into QC0 source VPD.

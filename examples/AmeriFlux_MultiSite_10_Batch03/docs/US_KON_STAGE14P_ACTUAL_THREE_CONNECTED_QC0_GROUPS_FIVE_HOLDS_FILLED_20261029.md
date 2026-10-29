# US-Kon Stage14P — ACTUAL successful 3 grouped original-QC0-boundary sensitivities, four original humidity holds remain (2026-10-29 07:00 UTC)

The user executed the exact SHA-pinned [Stage14P original true-QC0 endpoint connected-group science script](../scripts/stage14/14p_US_Kon_three_QC0_connected_blocks_5of9_research.py) on IRIDIS6, and the actual results completed. **3/3 independent source event groups passed** their group-atomic 30min QC source, water/ice, T, VPD, RHwater and QBOT checks.

Output isolated research-only version:
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_Kon_14P_QC0_3_CONNECTED_GROUPS_4HOLD_RESEARCH_ONLY_20261029T070041Z_0ec4c927
```
Parent Stage14K full 280320 native NOLEAP 2004–2019 source SHA256 `050007998ea63c911c63eab42b23902be31f57135935b5a7135d45541d964acb`; original SHA-pinned FLUXMET manifest `a68e021f234b8efd9a0ad533dd3a8085193ce51a8234aa1e6e09335cb5d7ddca`; original field-level measured tower `TA_F/VPD_F` QC0 anchors protected.

| Source QC0 observation-bounded group | # original VPD source rows revised in research | # previous missing actually filled | # original source T QC1 additionally revised | Max ΔVPD per HH hPa | Max ΔRHwater pp | Max ΔQBOT kg/kg | Max ΔT °C | Actual numerical gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2011 Feb22 08:30–09:30 | 3 | 3 | 0 (prior 2 approved T edits retained) | 0.700235 | 6.147136 | 0.000105945 | 1.413 | PASS |
| 2011 Oct23 06:00–08:00 | 5 | 1 | 0 | 0.622526 | 0.129989 | 0.000786497 | 2.120 | PASS |
| 2012 Feb25 10:30–11:30 | 3 | 1 | 2 (original QC1 T only at 11:00/11:30) | 0.517619 | 2.152546 | 0.000123352 | 1.353 | PASS |
| **Total** | **11** | **5** | **2** | | | | | **3/3 PASS** |

Total initial 77 missing selected site VPD+QBOT after source scientist holds Stage12AY, Stage14K rebuilt 68, Stage14P rebuilt remaining **5** through observationally anchored **connected QC0** RH interpolations; selected research tape now has exactly **4 original source-HOLD HH**:
- `201105261100` (2011-05-26 11:00, TA QC0/VPD QC1) — source companion ERA RH 50.034%, separately downloaded ERA5-Land 49.218%. Strong source agreement at held *center*, but original 09:00–10:30 tower T QC1 spikes and native selected VPD source jump (~19.05 to source neighboring selected 10.05 hPa). Do not fill center alone.
- `201109291830` (2011-09-29 18:30, TA QC1/VPD QC2) — source companion ERA RH 24.536%, ERA5-Land 24.851%, but T QC1 15.617°C vs original companion ERA 21.991°C (−6.374°C). VPD QC2 derives from original ERA, and other nearby QC2 source-hour joins are inconsistent. No nearby independent source VPD QC0, protect.
- `201110150730` (2011-10-15 07:30, TA QC0/VPD QC1) — original VPD 12.032 hPa exceeds original QC0 T=8.344°C saturation, original before/after 07:00→08:00 VPD 5.352→8.325 hPa (both QC1) and corresponding T all original QC0; source companion ERA RH 64.375%, independent ERA5-Land RH 70.384%. A strictly lower-confidence **two-source QC1-neighbour RH interpolation** at the center only may be numerically viable but not independently measured.
- `201208050900` (2012-08-05 09:00, TA QC0/VPD QC1) — original VPD 37.465 exceeds T=25.986°C saturation, true original both-QC0 RH endpoints 2012-08-05 08:30=39.9709% and 11:30=30.185%, and original 09:30–11:00 T+VPD QC1 anomalously warm/dry (ERA5-Land T2m near 26.8–29.1°C vs source T QC1 near 31°C); **one whole connected QC0-observation RH plus T-QC0 interpolation** is needed, not a center-only fill.

Important scientific status: Stage14P source is numerically closed over the **three changed event groups**, but is still an **incomplete research sensitivity**, not independent measured RH at each inferred time, and other previously flagged source QA events remain. **NO CIME/AD400/DATM or Slurm approval**.

Next action: a *single*, bounded, SHA-gated, independent research-only Stage14Q candidate for the two most tractable source locations Oct15 single slot and Aug05 QC0-endpoint whole episode; the two long-range low-independent-QC0 events May26/Sep29 remain protected until actual independent source evidence or explicit low-confidence full-tape emulator. Never overwrite Stage14P or historical input. Do not claim four→two before real execution.

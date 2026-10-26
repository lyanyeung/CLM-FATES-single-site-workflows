# Batch04 US-Syv — operator VERIFIED read-only 616 unique HOLD half-hours and science review priority

**2026-10-26; operator returned actual IRIDIS6 stdout** for source-pinned [US-Syv 606+10 triage script](../scripts/manual_review/triage_US_Syv_606_holds_10_skipped_boundaries_readonly.py). Stage05/Stage06/Stage07 checksum + provenance checks passed; both original and Stage07 US-Syv **438,288 HH** and paired packaged ERA verified. **No modified candidate/source/model files** were created by this run.

## Exact census — distinction between physical invalidity and source-temperature validity

| Metric | Observed |
| --- | ---: |
| Original Stage05 inherited science HOLD rows | 606 |
| Stage07 newly skipped paired ERA VPD endpoints | 10 |
| Duplicated exact original HH across those two | **0** |
| Unique half-hour HOLD union | **616** |
| Stage07 candidate VPD exceeds water saturation at retained `TA_F` | **598 HH** |
| Stage07 candidate currently passes water-saturation T/VPD physics | **18 HH** |
| Full continuous half-hour episodes across all HOLDs | **86** |
| Longest episode | 85 HH = 42.5 hours |
| Episodes >24 HH | 5 |
| Same-native packaged ERA record matched | 931/931 context HH, 0 missed exact-HOLD HH |

Reasons `SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID`: **183**; `ERA_PAIR_HUMIDITY_INVALID`: **419**; `ERA_RH_OUTSIDE_QCV5_USABLE_RANGE`: **4**; Stage07 `ERA_VPD_EXCEEDS_SATURATION_AT_RETAINED_TOWER_T`: **10**. Totals add to 616 distinct HH. The **183 source-T/grid discrepancy labels are only investigation flags, not 183 confirmed wrong tower temperatures**. The source-boundary-physically-valid **18** still require source hold assessment by reason, but cannot be classified as a violation of basic VPD saturation physics.

## Operator science decision required: high-priority suspected temperature artefacts

| Episode, original native HH | Count | Source tower and processed ERA evidence | Triage |
| --- | ---: | --- | --- |
| **2007-02-10 17:30 through 2007-02-11 07:00** | **28 HH** | 2007-02-10 17:00 `TA_F=-11.652`°C; 17:30 **`TA_F=-27.594`°C/QC1 vs processed `TA_ERA=-11.920`°C**, and 2007-02-11 07:30 `TA_F=-15.770`°C/QC2 | ~16°C abrupt change to near-constant −27°C over 14h; strongest suspect TA replacement interval |
| **2007-02-11 17:30 through 2007-02-12 03:00** | **20 HH** | 17:00 `TA_F=-10.083`°C/QC2, 17:30 `TA_F=-26.966`°C/QC1 vs processed `TA_ERA=-10.543`°C | another huge 17:30 clock-locked drop; ~10-hour suspect TA interval |
| **2003-04-27 11:30 through 19:30** | **17 HH** | 11:00 `TA_F=11.248`°C/QC0, 11:30 `TA_F=0.020`°C/QC0, processed `TA_ERA=15.639`°C; 19:30 `TA_F=1.233`°C vs `TA_ERA=17.470`°C; 20:00 source `TA_F=13.310`°C/QC0 | hard 11:30 and 20:00 boundaries, likely contiguous spurious low T, despite source QC0 label |

**These are the first 3 complete contiguous anomalous candidates, 65 HH total**, but none has been automatically changed in Stage07. An extended search of **all 183 original T discrepancy holds** is needed to determine whether additional same-clock plateaux like 2007-02-08 17:30–21:30 (9 HH), 2007-02-09 17:30–23:30 (13 HH) and 2007-02-12 17:30–22:30 (11 HH) qualify under the same manual rule. These three further episodes add 33 HH, not yet independently bounded by neighbouring full source data in the current operator top-12 evidence.

Potential **conditional** science rule for user explicit approval only: select source-demonstrated anomalous T ranges; replace *only candidate* `TA_F` with independent ERA5-Land or same-native packaged `TA_ERA` plus a **healthy-flank/calibration residual if calibrated**, convert candidate TA QC to ERA-derived value, recheck onset/recovery jumps, and if needed adjust VPD/RH only with physically valid **and source-provenance-consistent** humidity data. For missing RH, physically valid original Stage07 VPD may be retained **only after checking VPD ≤ e_s(new T)**. Always preserve original source, previous final manually verified 2000/2007 US-SP1 scenario and 10-site candidate manifest, and do **not** imply production release.

## Other extreme cold events need RH/VPD physics, not a blanket tower-T substitution

| Episode | Count | Observation |
| --- | ---: | --- |
| **2007-02-03 14:30 through 2007-02-05 08:30** | **85 HH**, 42.5h | Original tower `-24.535°C` vs `TA_ERA=-22.795°C` at first HH, and near `-27.317°C` vs `-27.822°C` at last HH; `VPD_F=0.980/0.704 hPa` at endpoints exceeds tower-temperature saturation. **No established 16°C tower-T artefact here** |
| **2019-01-30 20:30 through 2019-01-31 17:30** | **43 HH**, 21.5h | At 20:30 original/Stage07 source T **-25.085°C/QC2**, `TA_ERA=-25.085°C`; `VPD_F=0.811 hPa` nonetheless above `e_s(T)`. Similar near-coincident T/ERA at other HH; source T is ERA-derived QC2, not observed QC0 |
| **2008-02-10 03:00–16:00** | **27 HH** | Initial tower/Stage07 `TA_F=-25.157°C/QC2` = `TA_ERA=-25.157°C`; `VPD_F=0.801 hPa` remains over saturation. **Humidity physics is primary** |
| **2004-01-28 22:00–Jan29 09:00** | **23 HH** | Site `-26.746°C/QC0` and ERA `-26.112°C` at start; site vs ERA difference 0.63°C but VPD 0.738 hPa over water saturation |
| **2003-04-27 11:30–19:30** | **17 HH** | **Exception**: abrupt T fall to `0.020°C/QC0` while ERA `15.639°C`; do not place blindly in all-temperature-retain group |

**Important physical nuance:** the screen compared positive VPD to **saturation vapour pressure over water**, `e_s(T)`. Most of the original invalid VPDs are positive and **too high at cold T**, not negative. Some `VPD_ERA` values derive from packaged FLUXNET ERA and are **identical to the invalid source `VPD_F`**, hence **directly copying `VPD_ERA` is NOT a valid generic repair** when VPD would still exceed saturation. A physically bounded RH saturation-deficit-fraction remap against ERA T may be considered **only** where both paired `TA_ERA` and `VPD_ERA` imply a physically valid, trustworthy grid-relative RH; otherwise needs actual independent ERA5-Land T/dewpoint or validated site flanks. The existing Stage07 script explicitly refused 10 paired ERA values that violated the site-temperature saturation bound.

## Manual decision recommended immediately

1. **Temperature source:** choose whether to construct a new *isolated research candidate* for **the two clear 2007-02-10/11 overnight −27°C plateaux (28+20=48 HH)** and **2003-04-27 daytime 17 HH**, with true anomaly boundaries anchored against source T and appropriate ERA healthy-flank calibration. Additional 2007-02-08/09/12 same-clock holds need their immediate before/after evidence before simply applying that broader rule.
2. **Wetness rule:** for all *remaining* physically invalid VPD samples where source `TA_F` follows ERA / is meteorologically plausible, **retain `TA_F` exactly**, repair **only VPD/RH** using physically verified independent ERA5-Land humidity, or a proven paired-ERA-grid-relative-humidity fraction projected onto retained site T, **never a blind native VPD_ERA copy**. Require exact physical 0≤VPD≤es(T) after changes. **This is a science recommendation, not yet user approval or run**.
3. **18 physically valid HOLDs:** retain original data but do not silently clear their historical science reasons. Review reason/QA before final production approval.

**Source integrity:** All 616 were **original and Stage07-derived read-only inspection only**, no repairs submitted on IRIDIS6 from this analysis. Full pipeline Stage12 repairs 148/156 non-US-Syv original targets, Stage14 8 humidity-only closures, and US-SP1 Oct2007 137-HH research candidate are already completed and must not be repeated. US-SP1 Jan/Feb2008 operator decision **retain original TA_F** also stands. No Post-v5/DATM/CIME/Slurm/spinup release until separate gate.

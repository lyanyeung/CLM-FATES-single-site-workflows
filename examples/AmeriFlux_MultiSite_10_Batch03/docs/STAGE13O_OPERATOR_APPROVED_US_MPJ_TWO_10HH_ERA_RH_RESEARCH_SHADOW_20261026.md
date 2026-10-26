# Stage13o — US-Mpj two 2014 original 10HH QC1 episodes: operator-approved group repair

## Operator approval (26 October 2026)

Operator explicitly approved BOTH original-source-native 2014 US-Mpj humidity QC1 intervals:

| Event | Exact source native `TIMESTAMP_START` | 30min QC1 rows | Prior operator-approved centers | Bookend source measured VPD QC0 |
| --- | --- | ---: | --- | --- |
| 1 | **2014-10-11 01:30 – 06:00**, inclusive | 10 | 02:30, 04:30 | 01:00, 06:30 |
| 2 | **2014-10-21 04:00 – 08:30**, inclusive | 10 | 08:30 | 03:30, 09:00 |

Operator has now approved **20 native halfhours total**, including **17 additional QC1 neighbors** not covered by Stage13m. The operator instructed: only apply after source tower/ERA SHA, exact native time/source QC1, complete episode VPD continuity, both original QC0 bookends, RH/QBOT physics **all** pass. On a failed gate leave **the entire failed episode HOLD**; no silent partial repairs. Keep original three Stage07 previously user-selected center VPD/QBOT unchanged, all original raw files and Stage07 forcing immutable, preserve the two original Feb2018 low-RH VPD and approved Feb2020 temperature, all surface/PFT, no model jobs.

[Stage13o separate exact operator-approved decision](../decisions/STAGE13O_OPERATOR_APPROVED_US_MPJ_TWO_2014_QC1_SEGMENTS_20HH_20261026.json). [Stage13o research-only source-pinned / gate-controlled application](../scripts/stage13/13o_US_Mpj_apply_two_10HH_operator_approved_ERA_RH_SHADOW.py).

## Science basis

Previous [Stage13n actual source QC1 episode report](STAGE13N_VERIFIED_MPJ_TWO_FULL_QC1_HUMIDITY_EPISODES_OPERATOR_REVIEW_20261026.md) verified 10/10 QC1 records per run, original measured VPD QC0 at all four event edges and 20/20 basic paired ERA-RH at retained site TA water physics. The two original 2014 Oct11 center VPD values would create unnatural ±7hPa native jumps if treated as isolated single-point repairs, because source-neighbor QC1 humidity remained ~8.2 hPa. Both original Oct11 center humidity reports were physically negative RH (−24.9078%, −1.2944%). Stage13n calculated minimal candidate segments for each center with max resultant adjacent VPD jump 1.345/1.414 hPa; the complete original Oct21 10HH run had max 1.443 hPa. These results are **source diagnostics**, not evidence of actual user-approved full-run source replacement until the current operator approval.

The replacement **transfers companion FLUXNET standalone downscaled ERA RH** to the signed *retained tower/site TA_USE*: `es(Tsite) * (1 - RH_ERA/100)`, leaving TA_USE, TBOT, PSRF, radiation, precipitation, wind and original site-native time unchanged. QBOT uses `0.622 * ea_Pa / (PSRF - 0.378*ea_Pa)`, `ea_Pa=100*(es(Tsite)-VPD)`. Original 3 previously approved center values are *already numerically in Stage07*, so only 17 neighboring model halfhours get new VPD/QBOT values (expected 17 + 17 = 34 changed model field cells). Source ERA is a reanalysis estimate, not an independent tower humidity measurement; all science claims retain this limitation.

Original signed source:
- Selected **Stage07 US-Mpj 2008–2025 315,360 halfhours** SHA256 `c227f65b800baca3160efe40442fee91ee83c5f04308a0453e0c22bd05d0f592`.
- Original tower FLUXMET SHA256 `11f4383dd6deebec8d8ec4f8d82ea00b94e2d4100144811f335f395925451e75`.
- Original paired source ERA SHA256 `fb9dc6954b585c125669fab10af1f6d1ca22f2ee84ef18b59f55c9d2449b7f2e`.
- Original signed Stage13n actual IRIDIS6 source-research evidence `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13n_Mpj_original_QC1_ERA_RH_episode_READONLY_20261026T201029Z_3b42b67d`.

## Exact fail-closed scope and command modes

The new Stage13o program reads verified original Stage13m source module Git blob `2eae8663e64739db78ce9dd305ae3aa4b840b06d`, validates Stage13d+Stage13m operator decision JSON and Stage13n existing SHA-signed report receipt and all report content, re-reads original tower/companion ERA and retained Stage07, and independently validates:

- exact two site-native 10HH source VPD QC1 events and original four QC0 neighbors; QC0 data must be numerically preserved;
- original site TA within 8°C of companion ERA TA, valid ERA RH/site RH strictly 0–100%, 0<VPD<es and physically reconstructed QBOT 0–0.08 kg/kg, unchanged site PSRF and TBOT;
- original three operator-approved Stage07 centers remain numerically *unchanged* and match the companion ERA RH reconstructed VPD and QBOT;
- each of 11 joined source-native 30min differences per event (including the two original measured QC0 boundaries) is **≤4.0 hPa**; no single-point discontinuous amendments;
- new 315,360-row NOLEAP source candidate changes only VPD_USE and QBOT at the **other exact 17 times**, no changes to 2018 original VPD 11.261/9.178 or approved 2020 TA_USE 1.1795°C, no other variable or native timestamp;
- full CSV re-read comparison; signed SHA receipt for original approved source, signed evidence, exact changes, candidate and reports. All post-v5, DATM, AD400, model job approval gates remain **false**.

`--self-test` is pure math/range synthetic only and no cluster writes; `--check` source/audit **read-only**; `--apply` repeats identical science audits and only on PASS writes one **new separately named research-only** source candidate under `science_trials/stage13o_Mpj_20HH_operator_approved_ERA_RH_*`. If either entire 10HH group fails, **no successor forcing is written at all** (stricter than partial acceptance).

**Submission status:** operator decision and GitHub code committed; **there is no reported Stage13o IRIDIS6 `--apply` run or successful output yet**. Any partial/numeric state from previous Stage13m still is original 0/3 held. Do not submit CIME/DATM/Slurm or claim production-readiness.

# US-Me2: decisions for the four legacy humidity events (Claude CL04, 2026-10-29)

**Scope.**
- US-Me2 only.
- The four events are native LST 2014-12-31 20:30, 21:00, 21:30 and 22:00 (UTC 2015-01-01 04:45–06:15 midpoints), original rows 227899–227902. The clock is UTC−8 without DST (Stage14a, site BADM).

**Approval state.** Nothing is approved. There is no US-Me2 Stage12 shadow, so this is a per-event research ledger, not a forcing change.

**Evidence.**
- Script: [`scripts/claude/CL04_Me2_four_humidity_events_READONLY.py`](../scripts/claude/CL04_Me2_four_humidity_events_READONLY.py), commit `9f5e95c`, sha256 `63df109d…5366`.
- Run by the operator with `--run`: `reports/cl04_US-Me2_four_events_20261029T064908Z_58edc7ad`.
- Inputs: original FULLSET HH 4-6 (SHA `5b29b04d…`, via the Stage07 manifest) and the existing ERA5-Land 2014 ZIP. It is padded to 2015-01-03 23:00 UTC, so it covers the events.
- **No Me2 BASE file exists on IRIDIS**, so no second measured height was available.

## What is wrong at the four events

| LST | TA_F (QC0) | VPD_F (QC1, MDS) | e = esw(TA_F) − VPD_F | TA_ERA | e of the ERA pair |
| --- | --- | --- | --- | --- | --- |
| 20:30 | −14.46 | 2.202 | −0.199 | −5.07 | −0.124 |
| 21:00 | −14.70 | 2.214 | −0.250 | −5.21 | −0.167 |
| 21:30 | −14.82 | 2.226 | −0.281 | −5.18 | −0.158 |
| 22:00 | −14.73 | 2.237 | −0.277 | −5.16 | −0.150 |

**Mechanism.**
- RH is missing for the whole afternoon and evening of 2014-12-31, and PA_F is constant at 86.681 kPa.
- MDS therefore filled VPD (QC1) with values of 2.1–3.6 hPa. These are thermodynamically impossible at the measured tower temperature of −13 to −15 °C (esw ≈ 1.96 hPa).
- The ERA pair is also negative, by the same independent-regression mechanism found at US-NR3.
- The tower is about 9.5 °C colder than ERA, consistent with a basin cold-air pool that ERA misses. ERA5-Land T2M is −10.4 to −10.7 °C. The neighbouring US-Me6 tower measured −16.6 to −18 °C the same night (cross-site context only).

**Not resolved without Me2 BASE.**
- At 00:00 on 2015-01-01, RH (29 %), pressure and VPD QC0 all return at once.
- At the same moment TA_F steps from −14.9 to −7.5 °C.
- ERA5-Land warms about 3 °C between 22:30 and 23:00.
- Whether the evening TA is fully representative, or a data-system change happened at the file boundary, needs the AmeriFlux BASE (multi-level TA/RH) or the PI.

## Validation on Me2 QC0 (344,983 dual-QC0 half-hours)

| Method | COLD (Dec/Jan night, TA_F ≤ −5 °C): N / MAE / bias / median rel. | Event T bin (−15:−10): MAE / median rel. | Formable at the events |
| --- | --- | --- | --- |
| INTERP (4-HH pseudo-gaps) | 5,723 / 0.061 / −0.029 / 1.3 % | 0.037 / 0.9 % | **no**: no dual-QC0 anchor within 4 HH before the gap |
| EMP_LOYO (month × 3-h × T bin, year excluded) | 5,727 / **0.319** / −0.013 / 8.6 % (gate **pass**) | 0.213 / 7.9 % | yes |
| GRID_A (ERA5-Land d2m) | 165 / 0.806 / +0.663 / 31 % (gate fail: grid only for 2014) | 0.214 / 12 % (N = 33) | yes |

## Decision under the predeclared rule

The rule order is: measured level, then INTERP, then the COLD-validated climatology or grid.

| LST | Decision | e (hPa) | VPD at TA_F (hPa) | QBOT (kg/kg) | Ice RH | GRID_A cross-check (e / ice RH) |
| --- | --- | --- | --- | --- | --- | --- |
| 20:30 | EMP_LOYO | 1.658 | 0.344 | 0.001191 | 95.5 % | 1.691 / 97.4 % |
| 21:00 | EMP_LOYO | 1.639 | 0.325 | 0.001177 | 96.5 % | 1.668 / 98.2 % |
| 21:30 | EMP_LOYO | 1.624 | 0.322 | 0.001166 | 96.6 % | 1.641 / 97.6 % |
| 22:00 | EMP_LOYO | 1.636 | 0.324 | 0.001175 | 96.5 % | 1.603 / 94.6 % |

- The two independent sources (Me2's own QC0 climatology and the ERA5-Land dewpoint) agree within 0.05 hPa.
- Both give near-ice-saturated air, about 96 % ice RH, which is physically consistent with a cold-air pool.
- No value exceeds DATM saturation, so no cap was applied.
- `APPROVED_FOR_NEW_VERSION = False`.

## Wider finding (outside the four)

**The same MDS inconsistency covers most of 2014-12-31.** From 12:00 to 23:30 LST, besides the four events:
- 17 more QC1 half-hours have e ≤ 0 at the QC0 tower temperature: 12:00–15:00, 17:00–20:00 and 22:30–23:30;
- 15:30–16:30 has e ≈ 0, i.e. ice RH < 7 %.

Earlier hours were not printed. These rows were not part of the legacy four only because of how the historical Stage08–10 selection was made.

**Implication.** Any future US-Me2 forcing needs a full-record scan for non-physical TA_F/VPD_F pairs, and the same decision rule applied to them.

## User decision and site BIF review (2026-10-29 06:51)

**Decision.** The user accepted the recommendations: "那就按照你说的做".
- The four events take the EMP_LOYO values above, as a research, low-confidence fill. They will be used when a US-Me2 shadow is built.
- A full-record scan was requested: CL05, `scripts/claude/CL05_Me2_full_record_nonphysical_humidity_scan_READONLY.py`, commit `3e4e1d4`.

**Site BIF.** Claude read `AMF_US-Me2_BIF_20260527.xlsx` (SHA `adcd983c…`, 770 rows, sheet AMF-BIF) directly.

It contains **no variable-level instrument metadata**: there is no `GRP_VAR_INFO` group, so no TA/RH sensor model, height or change dates. It cannot explain the midnight TA step.

Relevant site facts it does record:

| Item | Value |
| --- | --- |
| Tower type | walk-up |
| `TOWER_POWER` | **Solar panels**. Winter outages are plausible; this is consistent with the 2014-12-31 RH loss and the constant PA, but it is a hypothesis. |
| Canopy height | 16.5 m (2011; 16.49 m on 2014-04-29) |
| `UTC_OFFSET` | −8 |
| Location before the fire | 44.4523, −121.5574, 1253 m |
| Location after the fire (from 2022-08) | 44.4526, −121.5589 |
| Original tower | used until 2022-08-25; after that a new shorter tower centred on the regenerating footprint |
| Disturbance | Green Ridge Fire on **2020-08-20** (surface to full crown fire); salvage logging late March to April 2021 |

Instrument history needs the AmeriFlux BASE-BADM data package or the PI.

## CL05 full-record scan (operator run 2026-10-29 06:55)

Report: `reports/cl05_US-Me2_nonphysical_scan_20261029T065536Z_25495c8d`. It covers 368,160 rows, 344,983 of them dual-QC0.

**Flagged rows.**
- 291 have e ≤ 0 (non-physical) and 75 have RH below 5 % (implausibly dry).
- 1 is a QC0 measured row; it is counted only and never targeted.
- The **365** QC1/QC2 targets fall in 71 runs, all in 2006, 2008, 2011, 2014, 2017 and 2022.

**Results.**
- The four CL04 events reproduced exactly.
- **EMP_LOYO 122** (stratum-validated): 2008 winter (76), the whole of 2014-12-31 (45) and 2022 (1).
- **HOLD 243.** Almost all are warm-season morning runs of 8–14 HH at 3–21 °C, in 2006, 2011 and 2017 (plus 16 HH in 2008).
  - INTERP validates well (MAE 0.03–0.20 hPa) but is not formable for these runs (longer than 4 HH, no QC0 anchors).
  - The QC0 climatology fails the gates in warm bins.

**Proposed next step (not run).** Validate the companion-ERA vapour pressure capped at DATM saturation (CEC, as for US-Me6/NR1) and longer-gap INTERP on Me2 QC0 by month × TA_F bin, for the 243 HOLD rows.

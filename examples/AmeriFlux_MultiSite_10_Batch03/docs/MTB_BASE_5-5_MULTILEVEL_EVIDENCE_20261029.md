# US-MtB BASE 5-5 multi-level evidence (read-only, 2026-10-29)

**Source:** user-supplied `AMF_US-MtB_BASE_HH_5-5.csv`, sha256 `75be85401d1f7a3c8c1efff60244e60745a2ef19f3af2b4f71b7bb8c7c71d8ee`, 2009–2024, 280 512 HH.

**Sensor heights** (BASE_MeasurementHeight_20260908):

| Sensor | Height |
| --- | --- |
| TA/RH_1_1_1 | 31 m |
| TA/RH_1_2_1 | 24 m (from 2013-09-19) |
| TA/RH_1_3_1 | 16 m |
| TA/RH_1_4_1 | 8.75 m (from 2013-09-19) |
| TA/RH_1_5_1 | 1.5 m |
| T_SONIC | 29.8 m |

The canopy is about 10 m high. FLUXMET `TA_F` equals `TA_1_1_1` (31 m) at the checked times.

## Findings

1. **2022 cold fault is a two-level instrument failure.**
   - On 2022-10-22 11:30–13:30 and 2022-12-04 17:30 – 12-05 05:00, `TA_1_1_1` and `TA_1_2_1` both read about −39.3 °C, and `RH_1_1_1`/`RH_1_2_1` read 0.5–0.7 %.
   - At the same times the 16 m, 8.75 m and 1.5 m sensors read ordinary, mutually consistent temperatures (December: 7.1 → 3.7 °C).
   - Two recovery half-hours, 12-05 04:30 and 05:00, read −12.9 and −12.0 °C at 31 m against +3 °C at 16 m. MtB02 did not catch these two.
   - A measured replacement therefore exists (16 m), so the ERA bridge is not needed.
2. **The warm constant runs are 0.5 °F quantisation, not faults.**
   - Example: 2013-12-17 reads 12.78, 13.06, 13.33 × 7, 13.61, 13.89 °C, which is 55, 55.5, 56, 56.5 and 57 °F.
   - T_SONIC (29.8 m) varies between 12.3 and 11.9 °C at the same times.
   - These runs are consistent with a warm mountain-top night above a colder valley-based grid.
3. **The −10 °C floor is a 31 m / 24 m sensor limit.**
   - In 2013–2020 `TA_1_1_1` never goes below −10 °C; below that it becomes missing. Example: 2016-02-02, where 16 m falls to −11.5 °C.
   - `TA_1_2_1` behaves the same way.
   - `TA_1_3_1` to `TA_1_5_1` record down to about −12 °C.
   - FLUXMET therefore gap-filled those coldest hours.
4. **Measured humidity is available at other heights when the 31 m RH is missing.**
   - HH with `RH_1_1_1` missing but another level present, per year:

     | Year | HH | Main source |
     | --- | --- | --- |
     | 2010 | 1764 | mostly 1.5 m |
     | 2015 | 1474 | |
     | 2018 | 1308 | |
     | 2020 | 1215 | |
     | 2024 | 3765 | 3627 from 24 m |

   - Above-canopy levels (24 m, 16 m) are the candidates. Their overlap with 31 m allows level-transfer validation.
   - The four 2024-02-11 frozen-phase points have no RH at any level.

## Revised order (proposal, user decision)

**Temperature**
1. `TA_F` (31 m) where valid.
2. Where the 31 m sensor fails or is clipped below −10 °C: 16 m `TA_1_3_1` plus a locally calibrated offset, validated on the overlap.
3. Otherwise the ERA bridge, for gaps of 5 HH or less.
4. Otherwise HOLD.

**Humidity**
1. QC0 `VPD_F`.
2. Measured RH at 24 m, then 16 m, applied at the 31 m temperature, validated on the overlap with 31 m.
3. Otherwise `COMPANION_E`.
4. Otherwise HOLD.

## MtB03 (user approved both orders, 2026-10-29 03:01)

[MtB03](../scripts/mtb/MtB03_multilevel_BASE_T_and_humidity_fill_candidates_READONLY.py) implements both orders and writes **candidates only**.

**Local dry run (temperature part only, on the BASE file alone; FLUXMET and ERA are on IRIDIS)**
- The 31 m readings are flagged in 36 HH:
  - 30 HH in 2022 (both −39.3 °C episodes plus the 12-04 15:00 and 12-05 04:30/05:00 transients);
  - 6 isolated spikes in 2013–2018.
- 63 HH are clipped below −10 °C (2015–2020).
- The 16 m level transfer, on synthetic 31 m gaps of 1, 5 and 22 HH (2000 each), gives MAE 0.13 / 0.18 / 0.27 °C, bias ≤ 0.10 °C and ≤ 0.03 % of errors above 2 °C. This passes the predeclared gate.
- A first draft flagged 31 m as faulty whenever it was 5 °C warmer than the 16/8.75 m consensus. That draft would have flagged the real night inversions of 2022-01-02 and 2024-02-12, when 24 m was missing; one hour earlier on 2022-01-02, 24 m agreed with 31 m.
- The rule was therefore changed **before the IRIDIS run** so that a warm-side fault needs the 24 m sensor to disagree as well. A cold-side fault, with 31 m colder than the levels below by more than 5 °C, is unphysical in any regime and needs no 24 m.

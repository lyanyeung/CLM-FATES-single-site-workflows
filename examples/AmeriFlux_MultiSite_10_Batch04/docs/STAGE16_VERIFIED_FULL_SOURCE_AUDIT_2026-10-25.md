# Batch04 Stage16 — IRIDIS6 operator-verified full-source audit PASS (2026-10-25)

**Provenance:** exact operator stdout supplied on 2026-10-25 after running the published Stage16 read-only `--audit`. This page records that output; it does **not** claim that GitHub independently executed code on IRIDIS6.

## Verified gates

| Gate | Operator-reported result |
| --- | --- |
| Python standalone self-test | PASS |
| Stage14 US-SP1 input full CSV SHA256 | `3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806` |
| Stage15 alternative US-SP1 full CSV SHA256 | `0f10267c1e391aaba41189b1e8878ee2c06baa773a107772cf0081642ecb2294` |
| Full US-SP1 row-by-row comparison | **368,208/368,208** native half-hours; **exactly 2** rows modified |
| Only modified fields | `TA_F`, `VPD_F`, `TA_F_QC` at the two documented timestamps |
| Other nine site input paths & SHAs | IDENTICAL |
| Physical VPD/RH closure at proposed trial temperatures | PASS |
| Original source and candidate modifications | NONE (read-only audit) |
| Remaining original tower-temperature science HOLDs | **8 unresolved** |
| US-Syv old HOLDs | **606 deferred** |
| Post-v5/DATM/CIME/SLURM readiness | NOT APPROVED / NOT RUN |

## Exact measured changes

| Site | Native HH timestamp | Stage14 TA °C (original QC0) | Stage15 TA °C (trial QC1) | Stage14 VPD hPa | Stage15 VPD hPa |
| --- | --- | ---: | ---: | ---: | ---: |
| US-SP1 | 200010091800 | −6.9 | 13.1816666667 | 2.27462321445 | 9.43621423808 |
| US-SP1 | 200010091830 | −7.1 | 15.3633333333 | 2.15689710498 | 10.4653427308 |

## Exact relevant operator stdout

```text
STAGE16 SELF-TEST PASS: exactly 2 rows, 3 columns permitted; 10-site consistency
STAGE16 SELF-TEST PASS: exactly 2 rows, 3 columns permitted; 10-site consistency
STAGE16 VERIFIED SOURCE SHA Stage14 3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806
STAGE16 VERIFIED SOURCE SHA Stage15 0f10267c1e391aaba41189b1e8878ee2c06baa773a107772cf0081642ecb2294
STAGE16 FULL CSV ROWS 368208 US-SP1; exactly two native HH changed
STAGE16 ONLY CHANGE 200010091800 TA -6.9 -> 13.1816666667 VPD 2.27462321445 -> 9.43621423808 original_TA_QC0 -> trial_TA_QC1
STAGE16 ONLY CHANGE 200010091830 TA -7.1 -> 15.3633333333 VPD 2.15689710498 -> 10.4653427308 original_TA_QC0 -> trial_TA_QC1
STAGE16 OTHER 9 SITE PATHS & SHAs IDENTICAL
STAGE16 PHYSICAL HUMIDITY CLOSURE PASS AT BOTH TRIAL T VALUES
STAGE16 SCIENCE HOLD 8 UNRESOLVED; US-Syv deferred 606
STAGE16 READ ONLY: NO ORIGINAL, STAGE14/15, DATM, CIME, SLURM WRITES
```

**Interpretation:** source/manifest integrity, exact two-cell trial isolation and humidity physics **passed**. This does not establish whether the original QC0 tower-temperature readings were scientifically incorrect. The Stage14 temperature-retained baseline and Stage15 two-temperature sensitivity candidate must remain separate. Neither is approved as production forcing. Next, inspect the **other six** unresolved timestamps (four US-SP1, one US-SRG, one US-Seg) against nearby native observations and independent ERA5-Land without changing temperature values.

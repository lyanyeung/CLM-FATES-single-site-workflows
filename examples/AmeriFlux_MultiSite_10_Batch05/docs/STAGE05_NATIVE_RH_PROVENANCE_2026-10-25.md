# AmeriFlux Batch05 — Stage05 original-RH, TA/VPD, and subzero phase audit

Date: 2026-10-25. **Evidence:** complete operator-supplied terminal log of `05_native_RH_provenance_phase_screen.py`. `SOURCE_VERIFIED` matched the ten immutable native CSV fingerprints; self-test passed; final report: `STAGE05 SUMMARY audited=10/10 failed=none`. No scientific source data were modified, and no forcing/model jobs were launched.

## Complete source audit

- **3,541,632** native half-hour rows scanned across 10 sites.
- **503,174** RH missing; **3,038,458** RH populated.
- **3,037,160** native-RH rows met the inclusive [0,100]% screen and had comparable TA/VPD-derived RH.
- **2,875,185** of these agreed within 0.1 percentage points under `RH_water=100*(1-VPD_F/es_water(TA_F))`. This is evidence of *mathematical agreement*, **not** proof RH is an independent measurement.
- **60,513** differed by >5 percentage points; **47,267** differed by >10 percentage points.
- **1,750** water-formula derived RH below 1%, including **1,559** below 0%, unchanged from Stage04.
- **1,296** original RH>100%; **201** original RH<1%. Flags may overlap.
- **50,287** distinct rows were flagged by Stage05's expanded RH mismatch/out-of-bounds logic, distinct from Stage04's 3,129 unique narrower abnormal records.
- **503** subfreezing `RH_water<1%` rows were also **all 503** `RH_ice<1%` in the Stage05 ice sensitivity screen. Switching saturation phase did **not** make these rows physically plausible.
- **47,267** >10pp RH differences break down by TA/VPD QC: **1/1 = 38,278**, **2/2 = 8,981**, **1/2 = 8**. **0/0 = 0**. Interpretation of QC 0/1/2 requires published release documentation; the arithmetic alone cannot certify observation lineage.

## Per-site comparison

| Site | Native rows | RH missing | RH agreement diff>10pp | Native RH>100 | Native RH<1 | Derived RHwater<0 | Distinct Stage05 flagged |
|---|---:|---:|---:|---:|---:|---:|---:|
| US-UiD | 298,080 | 173,477 | 3,644 | 0 | 0 | 0 | 3,644 |
| US-UMB | 262,992 | 30,295 | 17 | 79 | 0 | 22 | 119 |
| US-UMd | 333,120 | 28,558 | 23 | 0 | 0 | 15 | 38 |
| US-Var | 455,856 | 29,353 | 282 | 1,163 | 69 | 55 | 1,507 |
| US-Vcm | 333,120 | 25,500 | 16,065 | 0 | 102 | 389 | 16,549 |
| US-Vcp | 333,120 | 25,893 | 10,509 | 0 | 4 | 585 | 11,138 |
| US-WCr | 473,376 | 116,241 | 12,425 | 0 | 26 | 87 | 12,512 |
| US-Whs | 333,120 | 36,562 | 0 | 14 | 0 | 0 | 15 |
| US-Wjs | 333,120 | 28,339 | 4,302 | 0 | 0 | 387 | 4,703 |
| US-Wkg | 385,728 | 8,956 | 0 | 40 | 0 | 19 | 62 |
| **TOTAL** | **3,541,632** | **503,174** | **47,267** | **1,296** | **201** | **1,559** | **50,287** |

The three highest severe-disagreement sites (**US-Vcm 16,065; US-Vcp 10,509; US-WCr 12,425**) sum to **38,999** (82.5% of batch >10pp disagreements). The >10pp source-RH discrepancy alone does NOT mean the processed TA/VPD is wrong or that the native RH is correct.

## Scientific observations

1. **US-Vcm:** 16,065 >10pp mismatches, chiefly `TA/VPD QC1/1=15,114` and `2/2=951`. For example at 2007-01-17 04:00 original RH=89.08233%, native TA_F=−14.254C, VPD_F=2.387hPa, computed water RH≈−17.17%; switching ice saturation yields ≈−34.80%, *not* a resolution. This raw RH may be measured or processed; its provenance has not been established.
2. **US-Vcp:** 10,509 >10pp mismatches, chiefly `1/1=9,425`, `2/2=1,084`. 585 derived negative-RH rows remain from Stage04; Stage02's conflicting coordinate/elevation metadata remain unresolved.
3. **US-WCr:** 12,425 >10pp mismatches (`1/1=9,379`, `1/2=8`, `2/2=3,038`). Original RH is missing in 116,241 source rows.
4. **US-UiD:** 3,644 severe RH discrepancies, mostly 3,428 in QC2/2 (2024 has 3,110); 173,477 RH missing. No earlier negative-RH flag is not evidence of forcing quality.
5. **US-Var:** 1,163 RH>100%, split **399 ≤100.5%**, **402 in (100.5,101]%**, and **362 >101%**. An additional 69 original RH<1% cases disagree with derived RH by ≥5 percentage points. These categories should not be indiscriminately set to 100 or filled from bundled ERA5.
6. **US-UMB:** original BIF is missing and must be sourced separately. 79 native RH>100 are small (≤100.5%); this is distinct from the 22 derived negative-RH cases with original RH missing.
7. **US-Whs/US-Wkg:** no >10pp original-vs-derived RH discrepancies, but some RH>100% (14/40) or derived <1% (1/22) remain.

### Unresolved quality controls / "no repair" rule

- The original `RH` column may or may not be independently observed. Identical derived RH for QC0 is consistent with either reconstructed RH or source coupling; do NOT adopt it without the original data documentation.
- QC flags 0/1/2 must be interpreted from the specific AmeriFlux release and variable documentation. Only numerical grouping was performed.
- Stage03 offsets are sparse exploratory temperature-correlation rankings, not approved UTC/local clock choices.
- At Stage04, 55 ERA companion humidity examples are nonphysical under the assumed water-saturation formula; 738 more cannot be paired unaltered with native TA. Do not indiscriminately copy `VPD_ERA`.
- The subzero ice test is formula sensitivity only, not release-specific RH reference convention.
- No PFT/ZBOT changes, DATM, overlay forcing, CIME case, or Slurm submission is approved by Stage05.

## Stage06 follow-up

[Stage06: exact SHA-verified RH discrepancy source/lineage/episode audit](../scripts/stage06/06_rh_disagreement_lineage_and_episodes.py) inventories >10pp **contiguous episodes**, optionally checks unsuffixed `TA`/`VPD` columns if they actually exist, and identifies *shadow-only* candidate cases requiring upstream source provenance. It does NOT approve RH-derived VPD repairs or write any meteorological data. Operator execution pending.

# AmeriFlux Batch05 — Stage09 full native low-RH triage (2026-10-25)

## Operator execution
Original script `scripts/stage09/09_low_RH_source_resolution_readonly.py` passed pinned-Git-blob verification, syntax, and self-test. Output ended `STAGE09 SUMMARY audited=10/10 failed=none`. All ten SHA256 original files verified, **no writes to any original source, no forcing, clock shift, or Slurm**. The operator run screened all 3,541,632 native HH values, selecting exactly **1,750** water-formula-derived RH<1% source timestamps.

## Complete source-separated results

| Site | Low-RH HH | Derived RH<0 | 0<=derived RH<1% | Original RH missing | ERA e paired with tower T mathematically feasible | MDS TA+VPD physically feasible |
|---|---:|---:|---:|---:|---:|---:|
| US-UiD | 0 | 0 | 0 | 0 | 0 | 0 |
| US-UMB | 23 | 22 | 1 | 23 | 23 | 1 |
| US-UMd | 15 | 15 | 0 | 15 | 15 | 0 |
| US-Var | 62 | 55 | 7 | 62 | 31 | 7 |
| US-Vcm | 509 | 389 | 120 | 391 | 455 | 190 |
| US-Vcp | 629 | 585 | 44 | 629 | 623 | 409 |
| US-WCr | 88 | 87 | 1 | 61 | 79 | 2 |
| US-Whs | 1 | 0 | 1 | 1 | 1 | 1 |
| US-Wjs | 401 | 387 | 14 | 401 | 332 | 87 |
| US-Wkg | 22 | 19 | 3 | 22 | 21 | 3 |
| **TOTAL** | **1,750** | **1,559** | **191** | **1,605** | **1,580** | **700** |

Among all 1,750, **115** ERA inferred vapour pressures cannot be paired with tower temperature while obeying the current water saturation formula; **55** ERA internal TA/VPD values are themselves physically inconsistent (52 US-Vcm; 3 US-Vcp); total 170 without physically feasible ERA pairing. The **1,580** feasible results are only *mathematical shadow candidates*, not validated replacement forcing.

MDS native intermediates are physical for **700** records and nonphysical for **1,050**. Importantly a sizeable portion of the 700 is the *same* measured/MDS consolidated humidity that is extremely low but nonnegative; and among QC2-sourced events MDS alternatives have lower quality `MDS_QC2/3`. No automatic MDS adoption.

### Consolidated source QC of 1,750 selected events

| TA_F_QC/VPD_F_QC | Counts | Meaning |
|---|---:|---|
| 0/0 | 119 | Both measured; 93 US-Vcm and 26 US-WCr |
| 0/1 | 961 | TA measured, VPD good MDS |
| 0/2 | 479 | TA measured, VPD ERA |
| 1/1 | 4 | TA and VPD good MDS |
| 1/2 | 128 | TA good MDS, VPD ERA |
| 2/2 | 59 | Both ERA |
| **TOTAL** | **1,750** | |

Exactly **666** abnormal source records use VPD_F_QC2 (479+128+59); their VPD_F_MDS candidates have QC2/3. **965** use good MDS VPD (961+4). **119** have measured VPD. Among the 119 both-measured records, **92** are nonnegative but <1%, **27** are slightly/strongly negative; these should receive **separate high-priority original tower QC review**. US-Vcm 0/0 has 92 nonnegative and 1 negative, whereas US-WCr 0/0 has 26 negative.

Of the 1,750, original RH status is **1,605 missing**, **116 <1%**, **1 in [1,5)%**, **26 ≥5%** (all counts are subject to original-RH provenance uncertainty). The presence of a populated original RH is not evidence the value is independent of VPD.

### Continuous episode findings

All sites combined: **522** distinct runs of consecutive half-hour records with derived water RH<1%. Longest:
- US-Vcm **55 half-hours** (27.5 h): 2020-09-10 12:30 through 2020-09-11 15:30; all strictly negative
- US-WCr **26 HH** (13 h): 2025-08-25 13:00 through 2025-08-26 01:30; all negative, source QC0/0 merits independent measured-episode examination
- US-Vcp **21 HH** (10.5 h): 2019-04-11 07:00 through 17:00; all negative
- US-Wjs **17 HH** (8.5 h): 2016-05-01 02:00 through 10:00; all negative

All times quoted are **unchanged native printed FLUXNET local-standard timestamps**, not approved UTC conversions.

### No automatic repairs

1. Water saturation is explicitly assumed in this diagnostic. Negative computed RH is impossible for internally consistent water-reference TA/VPD, but the exact release phase/sensor formula still requires checking.
2. `RH` has no `RH_QC` in selected files and its independence/provenance is unresolved.
3. QC2 F values reproduce ERA, so copying ERA VPD does not repair those records.
4. `MDS_QC2/3` is not good-quality MDS; mathematical possibility does not justify promoting it.
5. Site BIF/coordinates are unresolved for US-UMB and US-Vcp.
6. Human review should triage measured-pair cases separately, then assess gapfill-physics conflicts with local measured anchors and independent ERA5-Land/BASE measurements where available.

## Stage10 plan

Create an **explicit, versioned report-only CSV per site** containing all 1,750 low-RH events with original TA/VPD/RH/QC, ERA humidity shadow, MDS QC, and nearest bracketing *source QC0/0 physically coherent* anchors within 3 h each side. Compute hypothetical time interpolation **only** if both anchors exist and resulting VPD remains physical; no replacement, no clipping, no forcing write. Such local extrapolations are diagnostic candidates pending science review, not an authorization to modify forcing.

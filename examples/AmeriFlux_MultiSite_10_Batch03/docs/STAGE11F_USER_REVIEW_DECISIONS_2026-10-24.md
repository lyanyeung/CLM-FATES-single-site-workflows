# Batch03 — user-directed Stage11f science decision ledger, 2026-10-24

**Type: user decision / intended method; NOT a completed forcing replacement, verified ERA5 file selection, source QC sign-off or Post-v5 approval.** Based on the user's explicit instruction in the current review discussion plus an operator-provided exhaustive 62-row Stage11f working-copy inspection. Source evidence on IRIDIS6 remains SHA sealed.

Exact sealed Stage11f report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11f_human_science_review_20261024T074958Z_6ae6d5d7/`

Operator independently verified `62_human_scientific_review_queue.csv` checksum; the separate working copy was created at `/home/ly3n24/AmeriFlux_Batch03_science_review_20261024/62_human_review_WORKING_COPY.csv`, but **this GitHub ledger has not been applied to that cluster file**. Never edit the sealed Stage11f report.

## Scope of explicit user decisions

The user directed:

1. **Six altered, original QC0-coded air temperatures `TA_F`: use the existing Stage07 candidate interpolated temperature.** This is a human choice of candidate for a future scientifically versioned forcing release; do not overwrite the source.
2. **All originally physically invalid humidity pairs and extremely low RH: replace humidity using ERA5.** For precision, *physically invalid* means source `e_a = e_s^{water}(TA_F) - VPD_F <= 0`, **not** negative `VPD_F`. Low RH means the Stage11e-v2 candidate has `0 < RH^{water} < 1%`. Record this as an **ERA5-based replacement method selected by user, but source product, derivation method, candidate physical verification and version still pending**, not as a completed repair.
3. Give a detailed assessment of all other cases for subsequent user judgment. Retain those as HOLD.

### Reconciled 62 distinct review IDs

| Disjoint decision class | Records | Human instruction | Implementation state |
| --- | ---: | --- | --- |
| Six original measured-QC0 TA modifications | 6 | Keep existing Stage07 candidate TA at these six exact native times | Decision recorded; no new writes |
| Source `TA_F+VPD_F` nonpositive implied water vapour pressure | 49 | Use ERA5-based humidity replacement candidate | Source/method validation pending; no new writes |
| Positive RH <1% at final Stage07 candidate, not already in preceding 49 | 4 | Use ERA5-based humidity replacement candidate | Source/method validation pending; no new writes |
| Three source-physically-positive near-zero water-vapour cases not within either class | 3 | Not decided; HOLD pending further human review | HOLD |
| **Total** | **62** | **59 have a user-specified method; 3 unresolved** | **Post-v5/DATM/spinup all unapproved** |

Stage11e-v2 source-physics counts: US-MOz 0 original nonpositive implied `e_a`, US-Mpj 2, US-NC2 47 = **49**. Five final candidate RH<1% IDs include **one overlap** with the original nonpositive-vapour set (US-NC2 `202503181900`). Thus humidity-method scope is `49+5-1=53` unique VPD events. Six TA choices are different review IDs. The other three all have original physically positive but near-zero implied water vapour pressure, and have been reconstructed by Stage07's ERA-RH method.

**Terminology:** an original `VPD_F` can be numerically positive even when `e_a=e_s(T)-VPD<=0`. Do not search only for negative VPD values.

### Exact six QC0 air-temperature event IDs

| Site | Source-native `YYYYMMDDHHMM` | Source `TA_F` (°C) | Chosen existing Stage07 candidate (°C) | Immediate flanking source QC |
| --- | --- | ---: | ---: | --- |
| US-MOz | 201603172200 | -15.213 | 12.1715 | 0,0 |
| US-Mpj | 202002110630 | -17.667 | 1.1795 | 1,1 |
| US-NC2 | 201901031300 | -6.759 | 13.3525 | 1,1 |
| US-NC2 | 201901040330 | -14.342 | 9.3935 | 1,1 |
| US-NC2 | 201901041630 | -13.804 | 9.5665 | 1,0 |
| US-NC2 | 201901080330 | -11.506 | 7.5215 | 1,0 |

The instruction to keep candidates must be explicitly tracked as a reviewer choice rather than represented as independent sensor certification. Do not silently alter source QC labels.

## Detailed P1 "other manual humidity" inventory

The 13 `P1_MANUAL_HUMIDITY_SOURCE_REVIEW` records are **not** 13 additional unresolved cases. **Ten** belong to the user's original `e_a<=0` ERA5 instruction and **three** require an additional explicit decision.

| Source-native date/time | Site | `VPD_F_QC` | Source water physics | Stage07 candidate water RH (%) | Original Stage07 review reason | This ledger |
| --- | --- | ---: | --- | ---: | --- | --- |
| 2014-10-11 02:30 | US-Mpj | 1 | Nonpositive implied `e_a` | 84.365 | Large VPD/measurement reconstruction | ERA5 method selected |
| 2014-10-11 04:30 | US-Mpj | 1 | Nonpositive implied `e_a` | 85.579 | Large VPD/measurement reconstruction | ERA5 method selected |
| **2014-10-21 08:30** | **US-Mpj** | **1** | **Physically positive implied `e_a`** | **81.079** | **Near-zero vapour ERA-RH reconstruction** | **HOLD: undecided** |
| 2025-02-07 16:30 | US-NC2 | 2 | Nonpositive implied `e_a` | 24.925 | Large VPD/measurement reconstruction | ERA5 method selected |
| 2025-02-07 17:30 | US-NC2 | 2 | Nonpositive implied `e_a` | 27.920 | Large VPD/measurement reconstruction | ERA5 method selected |
| 2025-03-11 18:30 | US-NC2 | 2 | Nonpositive implied `e_a` | 30.953 | Large VPD/measurement reconstruction | ERA5 method selected |
| 2025-03-11 19:00 | US-NC2 | 2 | Nonpositive implied `e_a` | 28.056 | Large VPD/measurement reconstruction | ERA5 method selected |
| 2025-03-11 19:30 | US-NC2 | 2 | Nonpositive implied `e_a` | 33.756 | Large VPD/measurement reconstruction | ERA5 method selected |
| 2025-03-21 19:00 | US-NC2 | 1 | Nonpositive implied `e_a` | 33.160 | Large VPD/measurement reconstruction | ERA5 method selected |
| **2025-03-22 01:30** | **US-NC2** | **1** | **Physically positive implied `e_a`** | **58.708** | **Near-zero vapour ERA-RH reconstruction** | **HOLD: undecided** |
| 2025-03-23 06:30 | US-NC2 | 1 | Nonpositive implied `e_a` | 78.796 | Large VPD/measurement reconstruction | ERA5 method selected |
| 2025-03-23 07:00 | US-NC2 | 1 | Nonpositive implied `e_a` | 80.174 | Large VPD/measurement reconstruction | ERA5 method selected |
| **2025-03-27 07:30** | **US-NC2** | **1** | **Physically positive implied `e_a`** | **79.776** | **Near-zero vapour ERA-RH reconstruction** | **HOLD: undecided** |

The three bold rows have original **physically positive**, but very small, water vapour pressure; the Stage07 algorithm changed their VPD according to `near_zero_vapor_pressure_candidate_repaired_ERA_RH_review_required`. **The quoted RH of 81.079%, 58.708% and 79.776% is AFTER Stage07 correction, not the original RH**. To choose fairly, read original RH, candidate, source companion ERA/RH and ±2h neighbouring native values for these three before deciding.

## Further grouped source decisions

**38** original US-NC2 QC1 VPD with source `e_a<=0` form four contiguous original March 2025 episodes: 12, 7, 10 and 9 half-hour records, respectively, as confirmed by Stage11f. All fall in the 49-event ERA5-method instruction (they are not an additional disjoint block).

Five Stage11e-v2 extreme-positive RH candidate records:

| Native source time | Site | Candidate water RH (%) | Source water physics | Human direction |
| --- | --- | ---: | --- | --- |
| 2018-02-02 17:30 | US-Mpj | 0.668699 | Positive implied `e_a` | ERA5 method selected |
| 2018-02-02 19:00 | US-Mpj | 0.439167 | Positive implied `e_a` | ERA5 method selected |
| 2025-03-18 19:00 | US-NC2 | 0.163385 | **Nonpositive** implied source `e_a` | ERA5 method selected; **overlap**, counted once |
| 2025-03-23 12:30 | US-NC2 | 0.868664 | Positive implied `e_a` | ERA5 method selected |
| 2025-03-25 09:00 | US-NC2 | 0.077323 | Positive implied `e_a` | ERA5 method selected |

## Critical ERA5 source and method hold

Stage07's companion `ERA5_HH` is a native site-downscaled, release-associated ERA5 product; separately obtained ERA5-Land grid `T2m`/`Td2m` is **not** the same dataset. The user's wording "ERA5" does not yet pin which one, release/time conventions, height, or humidity conversion.

- The Stage07 `secondary_era_replacement` source and ERA-RH-at-retained-tower-TA transformations have different numerical results; *do not silently equate them*.
- For any elected VPD replacement at retained tower TA, recompute `e_a`, `RH_{water}`, `QBOT`/specific humidity and precipitation/time continuity; source reanalysis pair may itself be inconsistent.
- Do not invent a replacement by directly assigning unrelated `VPD_ERA` to retained tower `TA`. Confirm exact source, humidity/pressure derivation, original native timestamps, phase convention, height/elevation and uncertainty. Use a newly versioned isolated trial only after this method is frozen.
- The user's instruction applies to these **53 candidate VPD events only**, not automatically to the other seven Batch03 stations and their **1,924** unresolved source humidity anomaly events. Those remain separate science holds.

## Immutable scientific and model gates

**Nothing in this ledger has been applied to the user's `62_human_review_WORKING_COPY.csv` or to any forcing.** Stage11f's original SHA-locked report remains unchanged. This is explicit documentation of user-selected review direction for 59 event IDs, with three HOLD events. It is **not** independent observational validation or final Post-v5 certification.

Final flags unchanged: `post_v5_approved=0`, `DATM_ready=0`, `spinup_authorizations=0`; Stage07's `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker must remain.

Supporting verified source documents: [Stage11e-v2 science triage](STAGE11E_VERIFIED_AND_STAGE11F_HUMAN_GATE_2026-10-24.md), [Stage11f 62-row review](STAGE11F_VERIFIED_HUMAN_REVIEW_QUEUE_2026-10-24.md).

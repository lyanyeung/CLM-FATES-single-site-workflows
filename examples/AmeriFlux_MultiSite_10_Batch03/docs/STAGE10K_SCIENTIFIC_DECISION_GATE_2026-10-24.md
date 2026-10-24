# Batch03 Stage10k — verified results and scientific repair decision gate

**Evidence cut-off:** 2026-10-24, based on the operator's successful IRIDIS6 Stage10k `--self-test`, `--check`, and `--run` terminal output.  
**Experiment:** AmeriFlux_MultiSite_10_Batch03 (10 packages, 7 stations with unresolved humidity-source evidence).  
**Scope:** 1,924 immutable Stage08–10 residual humidity anomaly source-row IDs across 32 site-years.  
**Status:** **AUDIT COMPLETED; ZERO APPROVED HUMIDITY REPLACEMENTS; ZERO APPROVED UTC OFFSETS; DATM/SPINUP NOT AUTHORISED.**  
**Source of truth:** Original FLUXMET/FULLSET and ERA source archives, the Stage07 input SHA manifest, and SHA-receipted Stage08–10k reports retained on IRIDIS6. GitHub stores scripts and this operator-log-derived interpretation, not the full per-row evidence.

## 1. Stage10k: independent audit results

- Stage10k [reproducible script](../scripts/stage10/10k_exception_provenance_science_gate.py) passed synthetic self-test and SHA/checksum-linked read-only and full report runs.
- Exactly **1,924/1,924** original events preserved and cross-compared against Stage10j, with **zero** approvals or writes to forcing.
- The paired *original companion* `TA_ERA` and `VPD_ERA` imply negative water vapour pressure when combined using the Stage08c liquid-water saturation equation for **1,924/1,924** events. This is an **algebraic inconsistency in paired source-reanalysis-derived fields**, not a claim of negative actual atmospheric water vapour pressure.
- The Stage10j counterfactual arithmetic, independently reproduced in Stage10k, yields:

| Mutually exclusive class | Events | Meaning |
| --- | ---: | --- |
| Only grid dewpoint-derived VPD removes negative implied e | 1,736 | Using source ERA air temperature + grid-derived VPD changes the sign |
| Either grid temperature or grid VPD alone removes negative implied e | 186 | Both single-variable algebraic tests change the sign |
| Only grid temperature removes negative implied e | 2 | Grid VPD with original source air temperature still implies negative e |
| Neither single-variable counterfactual removes negative e | 0 | Not seen in this constrained set |
| **Total** | **1,924** | No repair approvals |

The VPD-only arithmetic yields nonnegative implied water vapour pressure in **1,922/1,924 (99.90%)**, compared with **188/1,924 (9.77%)** for the temperature-only arithmetic. Neither figure is a candidate acceptance rate: the original ERA companion and ERA5-Land evidence are related; mixing atmospheric variables from different products is not a valid automatically approved physical forcing recipe.

### Exact two remaining VPD-only algebraic exceptions

Both are US-NR3 in an affected year with **zero source-labeled TA_F/VPD_F QC0** observations, and both original VPD values have source QC2 (ERA-derived).

| Original native local time | Source row | Source TA_ERA (°C) | ERA5-Land T2m (°C) | Source VPD_ERA (hPa) | Grid Td-derived VPD (hPa) | e implied by grid VPD at original source T (hPa) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2018-02-21 09:30 | `195333` | -21.064 | -15.569540 | 1.572 | 1.179913 | -0.033131 |
| 2018-02-21 10:00 | `195334` | -19.050 | -13.880003 | 1.623 | 1.425444 | -0.061299 |

The ERA5-Land T2m is respectively **5.49446 °C and 5.169997 °C warmer** than the paired original ERA source air temperature at these native times. The grid dewpoint-derived VPD is internally compatible with **grid temperature** (positive e from grid dewpoint) but **not** with the substantially colder source ERA air temperature in these two illustrative rows. Do not interpret this as proving which temperature field is objectively correct or as permission to switch the source temperature.

Stage10k report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage10k_exception_provenance_20261024T061150Z_13a3a08a/`

Principal output CSVs: `exception_2_US-NR3_events.csv`, `1924_counterfactual_science_gate.csv`, `site_counterfactual_qc_reconciliation.csv`, `site_year_counterfactual_qc_reconciliation.csv`, and `scientific_hold_receipt.json`.

### Stage10k by-site reconciliation

| Site | Original anomaly events | Source VPD QC2 | VPD-only nonnegative | Temperature-only nonnegative |
| --- | ---: | ---: | ---: | ---: |
| US-Kon | 229 | 204 | 229 | 55 |
| US-MMS | 18 | 18 | 18 | 2 |
| US-Me2 | 4 | 0 | 4 | 0 |
| US-Me6 | 1 | 1 | 1 | 1 |
| US-MtB | 15 | 11 | 15 | 6 |
| US-NR1 | 173 | 148 | 173 | 1 |
| US-NR3 | 1,484 | 1,484 | 1,482 | 123 |
| **Total** | **1,924** | **1,866** | **1,922** | **188** |

Source labels: no selected residual event has measured VPD QC0; **58** have gap-filled VPD QC1 and **1,866** have original ERA-downscaled QC2. All 1,866 QC2 source VPD values were previously checked against the matching companion `VPD_ERA` within 0.01 hPa.

## 2. Scientific decision: do not write forcing yet

**No existing Stage08–10k calculation should be run as a production repair.** Provenance, physical plausibility, cross-dataset comparison and **scientific acceptance** are distinct gates.

| Candidate approach | What evidence supports it | Why not automatically approved | Required next review |
| --- | --- | --- | --- |
| Keep unmodified original `VPD_F` at the 1,924 blockers | Native release and provenance are SHA verified | Paired source `TA_ERA`/`VPD_ERA` imply negative e for this selected subset; unmodified humidity may not yield physically coherent QBOT | Verify final forcing representation and whether native provenance makes it eligible for targeted review, not unconditional acceptance |
| Use existing ERA5-Land **absolute vapour pressure** inferred from dewpoint at retained tower temperature/pressure (Stage10b A) | 1,897/1,924 passed liquid-water physical screen | 27 fail liquid-water VPD/RH; 170 exceed water-vapour saturation with respect to ice; height, spatial bias and source dependence remain | Analyse accepted subfreezing phase convention and retained T/P/height; do not clip failed rows silently |
| Transfer ERA5-Land **grid relative humidity** to retained tower T/P (Stage10b B) | 1,924/1,924 pass Stage10b water-phase mathematical limits | 78 ice-relative supersaturation cautions; a changed vapour amount may not match tower atmospheric humidity | Specify RH transfer physical assumptions, independent site checks, uncertainty and whether CLM/CTSM computes RH vs specific humidity consistently |
| Substitute **grid dewpoint-derived VPD** into original source `TA_ERA` (Stage10j) | Algebraic sign fixed in 1,922/1,924 | 2 clear failures; produces thermodynamic mismatch when source vs grid T differ; not source-independent | Use only as diagnostic; not an accepted forcing prescription |
| Source native MDS gap-fill | Source fields and time identities available | Stage10d found no case simultaneously passing native MDS pair-physical + QC0/1 rule; source MDS is not guaranteed independent | Resolve variable-specific provenance/quality and pair consistency, not QC label alone |
| Direct interpolate from nearby source QC0 | Rare high-priority clusters have dual-QC0 brackets within 7 days | 17/19 P0/P1 clusters lack both-side dual QC0 even within 7 days; 7-day bridging can erase winter extremes | Constrain gap duration and obtain reliable measured humidity evidence; do not authorize long-gap interpolation |
| Copy raw ERA5-Land T2m, Td2m and/or P directly to tower | Internally complete 32/32 grid-evidence year sites | Site elevation, height, release time convention, reanalysis dependence, different location/representativeness | Verify metadata, tower-grid elevation/height and full annual impact, especially US-MtB/US-NR1/US-NR3 |

## 3. Minimum acceptance gates BEFORE new versioned forcing

1. **Clock, source and event identity.** Confirm original native start/end conventions, fixed local standard time vs UTC, intervals, site coordinate/elevation and exact release-specific offset (US-Me2 `-8 h` is a *hypothesis*, not a BIF-approved fact). Preserve `source_csv_row`, `TIMESTAMP_START`, hashes, QC origin and method for every change.
2. **Source/independence classification.** Native QC0 must actually be original observation according to its product definition; QC1/QC2/MDS and ERA5-Land are not independently measured tower humidity merely because numerical values exist. Do not score ERA against ERA-dependent data as independent validation.
3. **Physical consistency at *retained* T and P.** Define the intended humidity phase convention and equation for `e_s(T)`, `e_a`, RH over water/ice, VPD, `QBOT`/specific humidity and pressure. Check positive absolute vapour pressure, finite `QBOT`, internal `VPD`–RH–temperature agreement, tolerances and any true ice supersaturation separately. Never automatically clamp and hide physically inconsistent cases.
4. **Time/space representativeness and uncertainty.** Verify tower height, ERA5-Land grid-cell elevation, spatial and meteorological bias, seasonality, neighbouring measured evidence and full-year changed distributions; check that an event fix does not alter neighbouring clean data or introduce unphysical discontinuity.
5. **Independent/retrospective validation.** Check source-timestamp and whole-site-year distributions, physically defensible near-event temporal continuity, and any independent measured dewpoint/RH where it actually exists. State explicit uncertainty and unresolved cases.
6. **Explicit scientific sign-off.** Only after reviewers accept the above, produce a **new versioned, isolated candidate** (never overwrite original or the Stage07 `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker). Preserve alternative rejected candidates and scientific ledger with accepted/rejected/held decisions per event and site-year.
7. **Post-v5 integration gate.** Re-audit native chronology, release lengths and NO_LEAP conversions, all forcing meteorological variables, QC0 preservation, source receipts, PFT/surface ecological suitability, 5-year forcing loop and fixed-vs-transient CO2 policy before any case setup or spinup.

**No generic formula, single dataset or numerical pass percentage is enough to satisfy steps 1–7.** Approval cannot be delegated to a boolean threshold.

## 4. Practical next deliverable (without another redundant physical test)

Create a human-reviewable **method decision matrix** with per-site-year rows and the explicit alternative statuses:

- `SOURCE_MEASURED_SUPPORTED`: only where actual measured and physically consistent site humidity can be established.
- `EXTERNAL_ERA_CANDIDATE_UNCERTAIN`: limited to diagnostic **candidate**, never automatic write.
- `CLOCK_METADATA_HOLD`: US-Me2 until exact-release clock verified.
- `PHYSICS_CONFLICT_HOLD`: any candidate with negative implied e, nonfinite/physically inconsistent QBOT, disallowed phase-relative saturation or unvalidated tower/grid T mismatch.
- `EVIDENCE_INSUFFICIENT_HOLD`: sites/episodes without independently adequate support.
- `APPROVED_FOR_NEW_VERSION`: **not set for any record now**; requires documented explicit scientific review and signed acceptance.

The decision matrix can be added as a versioned text/CSV science ledger with data-source references and quantified uncertainty. Do **not** create a new candidate forcing while every one of these 1,924 residual records remains on scientific hold.

## 5. Links and existing evidence

- [Batch03 README](../README.md)
- [Stage00–10d status and earlier scientific gate](SCIENTIFIC_REVIEW_STATUS_2026-10-24.md)
- [Stage10e–10j observations, QC and source algebra](STAGE10E_TO_10G_QC_EVIDENCE_2026-10-24.md)
- [Stage10k reproducible verification code](../scripts/stage10/10k_exception_provenance_science_gate.py)

**Decision:** Full Stage10k science audit passed; 0 humidity/clock approvals, 0 new forcing versions or model jobs. The next action is formal science/source evaluation and a reviewed method decision ledger, **not** the automatic use of ERA5-Land VPD in DATM.

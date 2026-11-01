# JapanFlux Stage05H actual four JP-Yms PA shoulders and Stage05I joint 45-record HOLD register — 2026-11-01

## Operator's actual Stage05H read-only result

The operator ran the [Stage05H relative PA/LW context checker](../scripts/stage05/05h_PA_LW_event_boundary_relative_screen_NO_ZIP_NO_SLURM.py) from existing Stage05F and Stage05G reports. It reported exactly **4 additional** `ADDITIONAL_RELATIVE_ANOMALY_REVIEW_ONLY` candidates, ALL **JP-Yms PA_F**, with `PA_F=PA_ERA` and original `PA_F_QC=2`:

| Site | Native start timestamp | PA_F (kPa) | Same-release PA_ERA (kPa) | F/raw QC | PA_F divided by local conservative flank baseline |
|---|---|---:|---:|---:|---:|
| JP-Yms | 2005-08-12 02:30 | 67.794 | 67.794 | 2 | 0.690064 |
| JP-Yms | 2005-08-12 03:30 | 67.801 | 67.801 | 2 | 0.690136 |
| JP-Yms | 2011-12-17 06:30 | 68.160 | 68.160 | 2 | 0.688735 |
| JP-Yms | 2011-12-17 07:30 | 68.202 | 68.202 | 2 | 0.689160 |

These are **about 31% lower than the event's conservative PA baseline**, yet they previously evaded the literal `PA_F<50` kPa screen. In the Stage05D source series, JP-Yms `PA_ERA=37.349` kPa occurs at the central 03:00 (2005) and 07:00 (2011). The observed shoulder values also strongly fit a 30-minute interpolation around the corrupted center:

- For 2005: `2*67.794 - 37.349 = 98.239` kPa, and `2*67.801 - 37.349 = 98.253` kPa.
- For 2011: `2*68.160 - 37.349 = 98.971` kPa, and `2*68.202 - 37.349 = 99.055` kPa.

These back-calculated plausible neighbor pressures reinforce a **time-interpolated bad source pressure** mechanism. The values are algebraic implications of the reported measurements, not independently recovered tower observations or an approved replacement. Exact native timestamp time zone and source metadata still need direct verification.

## Revised source-selected science-review scope

Earlier Stage05G: **41** field-specific original `*_F` source-matched anomalous rows across **33 distinct site×native half-hours**, all with `QC=2`. Stage05H: **4** additional PA_F neighbor candidates (all `QC=2` and `F=ERA`).

**Updated: 45 variable-level science-review candidates across 35 distinct station×half-hour keys.** The distinct time-point count rises by only **2**, not 4: JP-Yms 2005-08-12 02:30 and 2011-12-17 06:30 were already Stage05G-flagged in `LW_IN_F` on the same respective half-hours; 2005-08-12 03:30 and 2011-12-17 07:30 are the newly added station×time keys.

| Site | TA candidates | PA candidates | LW_IN candidates | Field candidates | Distinct site×time keys |
|---|---:|---:|---:|---:|---:|
| JP-Fjy | 0 | 6 | 0 | 6 | 6 |
| JP-Khw | 3 | 6 | 2 | 11 | 7 |
| JP-Tef | 0 | 0 | 4 | 4 | 4 |
| JP-Tmd | 3 | 9 | 2 | 14 | 10 |
| JP-Yms | 0 | **6** | 4 | **10** | **8** |
| **Total** | **6** | **27** | **12** | **45** | **35** |

**Science confidence:** these four JP-Yms PA records are strong, specific physical-source contamination **candidates** due to source equality (`F=ERA`), raw QC=2, `~0.69` flank relative pressure, and exact adjacency to the central 37.349-kPa abnormal pressure. It is not scientifically justified yet to substitute their values automatically. Avoid presuming Stage05H or Stage05G detects every possible physical defect outside the screened source-event contexts.

## Stage05I: combined fully traceable HOLD register, zero source reads

[Stage05I reproducible ledger merge](../scripts/stage05/05i_merge_41_absolute_plus_4_Yms_PA_shoulder_HOLD_NO_ZIP.py) consumes the **actual** Stage05G TSV (`stage05g_source_selected_event_ledger.tsv`) and Stage05H TSV (`stage05h_PA_LW_relative_context_screen.tsv`). It fails closed unless the existing 41 Stage05G rows and four exact new JP-Yms event keys match and their `QC2` and `F=ERA` numeric equality are consistent. It emits new **derived** TSV and JSON for all 45 field candidates, 35 unique site×times. New records retain native time, variable, selected F, original QC, embedded ERA, possible MDS, absolute vs relative rule, and unapproved source-review status. It does not read original ZIPs, run Slurm, perform data replacement, approve model forcing or submit CIME cases. The code is committed; **no operator IRIDIS6 execution of Stage05I has yet been reported**. Download from a pinned commit, run `--self-test`, then run against actual audit tables.

## Next science stage before any repairs

1. Confirm native JPF time basis and release-specific BIF/QC semantics (source `*_F` / `*_ERA` / MDS), plus quantity units for TA, PA and LW.
2. Verify suspect timestamps from **independently acquired** ERA5 or ERA5-Land, not the JPF `ERA5_HH` that is already defective. Compare adjacent original tower values and alternative sources (MDS requires its own tests, notably Khw's dubious ~1°C August value).
3. Create only reversible **derived forcing-copy overlay proposals** for accepted variable+native-time keys and show original/new values and provenance. Keep original ZIP and original QC0 `*_F` intact. Stage05I does not perform these steps.
4. JP-Tom and JP-Tgf humidity/negative-VPD source audits remain pending and are not covered by this JPF review register.

**Model status**: No AD400/Normal400 authorized.

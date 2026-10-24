# Stage74 — CA-Man operator-approved 18/17 **scientific triage** and same-source meteorology trial

## Explicit operator decision (24 October 2026)

Following Stages71–73, **36** isolated QC1 temperature anomalies at CA-Man were evaluated. Stage71 confirmed **35** could be smoothed with an ERA-like reference temperature without creating >10°C half-hour steps on either side; the **2007-03-10 11:30** QC0-anchor case remains HOLD. Stage73 recomputed **coherent T/VPD/pressure/RH/specific humidity** from the *same raw FLUXNET ERA5_HH record* and found **35/35** thermodynamically valid, but **17** had large RH/VPD/pressure discontinuity flags.

The operator has **explicitly elected**:

- **18 cases with `NO_LARGE_BOUNDARY_SHIFT_DETECTED`:** trial-replace all coupled fields in one new forcing CSV using the same-row `TA_ERA`, `VPD_ERA` and `PA_ERA`; recompute `QBOT`, and set `TBOT`, `TA_USE`, `QBOT`, `PSRF`, `VPD_USE` consistently. This is a **limited candidate/trial decision**: input clock and source independence remain unverified.
- **17 cases with `REVIEW_LARGE_BOUNDARY_SHIFT`:** **keep all original forcing fields exactly**. An existing sharp temperature jump is explicitly accepted rather than applying an alternative that may introduce implausible or unverified humidity. This is an **accepted unresolved temperature risk**, **not** a certification that the old RH/QBOT is true.
- **One March 2007 anchor case:** keep original and HOLD pending measured-anchor/source analysis.

**Re-use across this repository:** see the root [mandatory same-source meteorology and human-review precedent](../../../../README.md). Do not generalize this exact 18/17 split to other site data or equate the absence of a 25-percentage-point RH boundary jump with independent observation truth.

## Script and safeguards

`74_apply_CA_Man_18_same_source_operator_review.py` operates in three mutually exclusive modes: `--self-test`, `--check` (no writes) and `--trial` (writes only a **NEW timestamped report and isolated trial forcing file**). It requires the exact 35 Stage73 review events, the exact operator 18/17 partition, the pinned Stage73 source file SHA-256, the pinned original CA-Man forcing SHA-256, source thermodynamic closure, and the March-2007 HOLD. It writes:

- `36_operator_decision_ledger.csv`: 18 joint same-row replacements, 17 unchanged flagged original records, and one anchor HOLD
- `CA-Man_18_same_source_ERA_T_Q_P_VPD_TRIAL_NOT_PRODUCTION.csv`: full 262,800-row 1994–2008 NOLEAP candidate, **only 18 records changed** and only the specified coupled forcing columns
- `manifest.json`: source checksum, input ledger checksum, trial checksum, change restrictions and full-file Stage58 scanner results

It checks every original/trial row and runs the whole-file Stage58 temperature, RH, VPD, calendar, and structural gate. **It does not overwrite source archives, original forcing, selected model forcing, DATM, active CIME cases, Slurm jobs, restart files or Research Filestore files.**

**Provenance caveat:** FLUXNET `TA_ERA/VPD_ERA/PA_ERA` variables may have been separately downscaled/regressed; Stage61's source timestamp alignment is diagnostic but not independently verified. Thus the 18 modifications are an **operator-selected scientific trial**, not an automatic production or historical-run authorization. Any deployment to active or production cases requires separate review and permission.

**Commands on IRIDIS6** (after downloading/validating the script from GitHub):

```bash
python3 -B 74_apply_CA_Man_18_same_source_operator_review.py --self-test
python3 -B 74_apply_CA_Man_18_same_source_operator_review.py --check
python3 -B 74_apply_CA_Man_18_same_source_operator_review.py --trial
```

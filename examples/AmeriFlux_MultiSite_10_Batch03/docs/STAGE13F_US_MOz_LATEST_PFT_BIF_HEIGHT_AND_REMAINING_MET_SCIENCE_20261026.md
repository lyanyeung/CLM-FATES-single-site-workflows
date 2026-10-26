# US-MOz Batch03 final remaining science scope — 26 October 2026

## Scope and approved records

**All 6 of 6 original Stage07 US-MOz meteorological edits are already explicitly operator approved.** The scope is pinned in:

- [Stage13D: exact one US-MOz source-QC0 temperature approval](../decisions/STAGE13D_OPERATOR_APPROVED_SIX_QC0_TOWER_TA_INTERPOLATIONS_20261026.json).
- [Stage13E: five additional US-MOz TA/VPD approvals](../decisions/STAGE13E_OPERATOR_APPROVED_FIVE_ADDITIONAL_US_MOz_TA_VPD_FIXES_20261026.json).
- Stage13E audited output at `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13e_MOz_six_approved_09T_recheck_20261026T174412Z_3e98ca6c`.

These approvals **do not cover previously unmodified source records**.

## New operator-reviewed meteorology — four groups

Stage13E showed a multi-hour tower-vs-ERA source discrepancy (separate from three flagged isolated centers):

| Scope | Current tower TA and QC | Paired original ERA5 TA | Current decision |
| --- | --- | --- | --- |
| 2005-01-06 05:00–09:00 (9 half-hours) | +4.620 to +8.024 °C, tower `TA_F_QC=1` | −6.342 to −7.096 °C | **HOLD.** One multi-hour source-quality/clock/MDS episode. It MUST NOT be "fixed" by a single-point interpolation. At 09:30 tower TA switches to −7.189 °C, `QC=2`, exactly matching companion ERA5 |
| 2014-04-02 10:00 | +18.110 °C, `QC=0` | +7.879 °C | **HOLD**, Stage13E screened isolated temperature candidate |
| 2016-04-11 13:00 | +23.671 °C, `QC=0` | +12.214 °C | **HOLD**, Stage13E screened isolated temperature candidate |
| 2016-04-14 06:30 | +17.543 °C, `QC=0` | +6.433 °C | **HOLD**, Stage13E screened isolated temperature candidate |

The three screened QC0 centers have **not** been interpolated or approved. [Stage13f three-center independent read-only 2-hour neighborhood extraction](../scripts/stage13/13f_three_US_MOz_QC0_spike_neighbors_READONLY.py) reads the original Stage07 SHA-verified tower and standalone ERA source and prints the preceding/following tower and ERA conditions; only after that can the operator decide.

**Important:** In 2004, 10,960/17,520 tower-vs-companion ERA air-temperature half-hours are numerically *identical* (62.56%). Treat the "ERA" field in these periods as potentially non-independent, NOT as independent independent evidence of source errors. Stage13E is SHA verified but did not replace any 2005 05:00–09:00 temperatures.

## Confirmed current GitHub PFT recommendations (no old surface veto)

The new curated cross-batch 50-site PFT catalog is **present** and explicitly documents all three Batch03 sites:
`examples/Ameriflux_Site/Ameriflux_PFT/RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_20261026.csv`
and
`examples/Ameriflux_Site/Ameriflux_PFT/PFT_INPUT_VALIDATION_20261026.csv`.

- **US-MOz**: proposed model natural-landunit FATES PFT 2 ENF 10% + PFT 6 DBF 90%, host bare 0%, `DEFAULT14`. Primary PFT validation: `round_trip=PASS`, `natural_area_sum=100`.
- **US-Mpj**: ENF 60%, C4 20%, bare 20%; validated recommended model hypothesis.
- **US-NC2**: ENF 90% + DBF 10%; validated recommended model hypothesis.

Do **not** incorrectly cite Stage04a year-2000 gridded PFT as the operator's most recent proposed *model* biogeography. The latest 50-site prescriptions resolve **which PFT inputs to test**; however the same curated CSV explicitly states `active_case_parameter_verified=NO`, `case_surface_or_job_modified=NO`: the measured tower footprint percentages were not independently established. This is an **implementation/preflight verification**, not a request to re-research the station PFTs.

## User-uploaded original US-MOz BIF Excel (reviewed, not uploaded to GitHub)

`AMF_US-MOz_BIF_20230331.xlsx`, `AMF-BIF` sheet, columns SITE_ID/GROUP_ID/VARIABLE_GROUP/VARIABLE/DATAVALUE:

- Row 117: `US-MOz | 24325 | GRP_HEIGHTC | HEIGHTC | 24.2`.
- Row 118: `HEIGHTC_DATE = 20070407`.
- Row 119: `IGBP = DBF`.
- Row 112: `FLUX_MEASUREMENTS_METHOD = Eddy Covariance`, followed by `FLUX_MEASUREMENTS_VARIABLE = CO2`.
- The 439-row Excel does **not** include a per-`TA_F` or `WS_F` sensor height, instrument `ZBOT`, or variable-specific meteorological height history. `HEIGHTC=24.2 m` is CANOPY HEIGHT, not input wind/temperature measurement height.
- Independent Missouri Ozark literature `Gu et al. (2016), https://doi.org/10.1002/2015JG003302` documents a 32 m flux tower; `Yang et al. (2007), https://doi.org/10.1029/2006JD008243` describes multi-level air temperature/RH measurement. **A 32 m tower structure does not alone establish the actual vertical reference of the FLUXNET TA_F/WIND forcing stream.** `ZBOT` needs a variable-level sensor metadata source or an explicitly documented model hypothesis.

Do **not** ask the user to resend this BIF workbook, and do not re-open PFT research as if no recommended catalog existed.

## Current scientific gate

- US-MOz Stage07 numerical forcing: complete; 6 originally modified source events operator approved.
- Remaining meteorology: four groups above, source/QC provenance still unresolved.
- Model PFT: latest curated 90/10 ready for **proposed case input** (validate applied surface/case, not yet claimed applied).
- Tower geometry: 32m tower literature and 24.2m canopy BIF; exact variable-level `ZBOT` unresolved, and must NOT be invented.
- `Postv5_approved=False`; `DATM_ready=False`; `spinup_authorized=False`; no new Slurm jobs or original source modifications.

Next required operator decisions: the three exact QC0 source centers after Stage13f ±2h context; and policy for multi-hour 2005 05:00–09:00 suspect gap-fill/clock segment. Those are separate decisions.

# JapanFlux Stage04 full-row source QC — actual 11/11 operator summary (2026-11-01)

**Execution evidence**: operator-provided IRIDIS6 terminal summary of full Stage04 audit, after completed Slurm submission `4792682`. The separate operator summary reports `STAGE04: 11 / 11`, each `READONLY_SCREEN_DONE`, and empty `TIME QC: {}` for all native source files. The job's `sacct` status was **not independently supplied**; only the Stage04 JSON-derived summary establishes successful report creation. No correction/forcing/model work is claimed.

**Operator preference**: from now on, avoid Slurm for read-only data audits, use direct commands, compact source-aware checks on the login node and limit prolonged decompression. Do not submit further Slurm audit tasks by default. For the next decision, reuse the **existing** `$HOME/japanflux_stage04/full11_raw_source_qc.json` with Stage05A, which does not read original ZIPs at all.

## Full native source coverage and provisional threshold screens

| Site | Source stream | Rows | Years of TIMESTAMP_START | Missing RH_F column | Stage04 candidate flags |
|---|---|---:|---|---|---|
| JP-Api | FLUXMET_HH | 403248 | 2000–2022 | Yes | None |
| JP-Fhk | FLUXMET_HH | 315552 | 2006–2023 | Yes | None |
| JP-Fjy | FLUXMET_HH | 368160 | 2001–2021 | Yes | PA_F below 50 kPa: 6 |
| JP-Khw | FLUXMET_HH | 385728 | 2000–2021 | Yes | TA_F below −70°C: 3; PA_F below 50 kPa: 6; LW_IN_F below 50 W m−2: 2 |
| JP-Spp | FLUXMET_HH | 333120 | 2000–2018 | Yes | None |
| JP-Tak | FLUXMET_HH | 420768 | 1998–2021 | Yes | None |
| JP-Tef | FLUXMET_HH | 403200 | 2001–2023 | Yes | LW_IN_F below 50 W m−2: 4 |
| JP-Tmd | FLUXMET_HH | 333072 | 2005–2023 | Yes | TA_F below −70°C: 3; PA_F below 50 kPa: 9; LW_IN_F below 50 W m−2: 2 |
| JP-Yms | FLUXMET_HH | 420768 | 2000–2023 | Yes | PA_F below 50 kPa: 2; LW_IN_F below 50 W m−2: 4 |
| JP-Tom | COREVARS_HR | 35064 | 1999–2002 | No | None |
| JP-Tom | COREVARS_HH | 192864 | 2003–2013 | No | RH_F above 100%: 6583; VPD_F below 0 hPa: 7336; P_F below 0: 4322 |
| JP-Tgf | COREVARS_HH | 368160 | 2002–2022 | No | RH_F above 100%: 9493; VPD_F below 0 hPa: 9514; PA_F below 50 kPa: 1; SW_IN_F below −20 W m−2: 1; P_F below 0: 3 |

- Native-time screens returned **zero reported** timestamp parse errors, interval-duration mismatches, duplicates, gaps, overlaps or decreasing starts for **each native file**.
- Coverage above is **start-year coverage**, not an assurance of usable original measurements or time-zone correctness. Filename end years for JP-Tom/Tgf may denote a Jan 1 end boundary; first/last exact intervals from Stage04 JSON must be examined before claiming this.
- All listed `*_F` variables had nonmissing numeric values at every row according to Stage04's **numeric missing-value filter**. This does **NOT** prove original observed/tower data at each time; source processing may include gap-fill, and it does **NOT** prove physical plausibility. Raw QC labels and metadata must be examined.
- Nine JPF FLUXMET_HH inputs lack `RH_F` as an available column; later derive RH or humidity from `TA_F,VPD_F,PA_F` only after confirming pressure, temperature and VPD units and vapour pressure feasibility; `QBOT` requires humidity and pressure with explicit unit conversion.
- Stage04's ordinary physics threshold screen assumed conventional FLUXNET units and was **not a proof of native units**.

## Scientific findings and triage

1. **JPF candidate outliers: 41 variable flags across 5 sites.** Fjy 6; Khw 11; Tef 4; Tmd 14; Yms 6. Most severe reported extreme `TA_F`: **JP-Khw −268.276°C**, **JP-Tmd −284.222°C**. Pressure minima include Fjy 0.334 kPa, Khw 0 kPa, Tmd 0 kPa and Yms 37.349 kPa. Longwave minima include Khw 39.171 W m−2, Tef 26.164 W m−2, Tmd 28.519 W m−2, Yms 44.79 W m−2. These records require exact original-row / QC / ERA companion checks. Do **not** claim that they are good readings because the missing-value count is zero.
2. **JP-Tom 2003–2013:** 6583 RH_F >100%, 7336 VPD_F <0; minima/maxima RH 11–112%, VPD −2.913562… to 29.249338… hPa. **JP-Tgf 2002–2022:** 9493 RH_F >100%, 9514 VPD_F <0; RH max 120%, VPD min −4.979288… hPa. RH and VPD flags may overlap at timestamps. **Per-field totals must not be interpreted as unique half-hourly incidents**. Pair-by-time and inspect native raw RH sensors, `_QC` and ERA5 partners in a later Stage05 targeted forensic before any decisions.
3. **Negative precipitation is almost certainly numerical round-off candidate** at both special stations: Tom `P_F` minimum **−2.001218498331353e−15**, 4322 `<0` flags; Tgf `P_F` minimum **−1.3189366798869739e−15**, 3 `<0` flags. The full reported minima indicate every negative `P_F` is >−1e−9, assuming the min is correctly calculated from the same field. Treat these as a **numerical tolerance issue**, not thousands of substantive negative-rainfall events. No source changes permitted at this stage; any later zero-clamping must be explicit on a derived forcing copy.
4. JP-Tgf isolated additional `PA_F=0` at one time point and `SW_IN_F=-70.11575` W m−2 at one time point are real review candidates.
5. The source product `RH_F` is absent for all nine JPF streams; do **not** confuse absence of this column with all water vapour data missing.

## Recommended next step: no Slurm, no ZIP reading

Use [`05a_summarize_existing_stage04_QC_NO_ZIP_NO_SLURM.py`](../scripts/stage05/05a_summarize_existing_stage04_QC_NO_ZIP_NO_SLURM.py) to extract **actual timestamp-labelled** flagged source samples, raw `*_QC` label distributions and start/end intervals from the **existing** full Stage04 JSON report (Stage04 recorded only the first 12 anomalous samples per variable). It makes no edits and uses no extra computing allocation.

Suggested immediate order: JP-Khw and JP-Tmd (severe improbable T), JP-Fjy/JP-Yms/JP-Tef (isolated field issues), JP-Tom and JP-Tgf (humidity/VPD cross-link and original provenance). Then design targeted original/ERA comparison on only identified events, rather than a second blind full audit. Do not automatically substitute ERA5 or start AD400.

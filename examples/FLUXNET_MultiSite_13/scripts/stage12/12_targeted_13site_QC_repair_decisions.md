# FLUXNET MultiSite 13 — targeted temperature/pressure repair candidate

**Status:** candidate / scientific review. **No existing forcing, raw FLUXNET, surface, DATM NetCDF or spin-up is modified.**

## Parents

- ES-Agu / DE-Lnf: `FLUXNET_MultiSite_13_qc_v5_candidate_20261014` selected forcing.
- ES-LJu: `FLUXNET_MultiSite_13_ES-LJu_legacy_pair_trial_v1_20261014` (v7; reproduces the previously successful standalone forcing exactly).

## Candidate changes (six 30-minute records)

| Site | Time | Evidence | Trial change |
|---|---|---|---|
| ES-Agu | 2016-10-10 01:30 | PA_F 59.523 kPa with adjacent normal 98.905/98.867 kPa | PSRF 59,523 → **98,895.5 Pa**, preserve TA/VPD; recompute QBOT |
| ES-Agu | 2016-10-10 02:00 | raw PA_F 20.142 kPa; parent v5 already produced 59,513.5 Pa from corrupted neighbors | PSRF 59,513.5 → **98,886.0 Pa**, recompute QBOT |
| ES-Agu | 2016-10-10 02:30 | PA_F 59.504 kPa | PSRF 59,504 → **98,876.5 Pa**, recompute QBOT |
| ES-Agu | 2014-06-26 15:00 | TA_F 5.840°C, QC=0, while ERA 27.259°C and subsequent tower 26.359°C | Trial paired **TA_ERA=27.259°C/VPD_ERA**, after sanity gate; recompute QBOT |
| ES-LJu | 2015-09-13 14:30 | TA_F 7.004°C while adjacent 22.829 and 22.333°C; VPD_F also dips | Linear **TA=22.581°C** and **VPD=21.4215 hPa**, recompute QBOT |
| DE-Lnf | 2023-06-22 07:30 | isolated tower 0°C, adjacent 18.850 and 15.400°C; v5 already interpolated VPD | Linear **TA=17.125°C**, preserve validated v5 VPD=3.8345 hPa, recompute QBOT |

Pressure is interpolated **only between uncontaminated 01:00 (98.905 kPa) and 03:00 (98.867 kPa)**; no interpolation through invalid 01:30/02:00/02:30. In each corrected record, use `es(T)=6.112 exp(17.67 T/(T+243.5))` hPa, `ea=es−VPD` and `QBOT=0.622(100 ea)/(PSRF−0.378(100 ea))`. Source values and original official QC flags are retained in the correction ledger, not changed in raw files.

## Explicitly unresolved / do not auto-correct

- **DE-Gri:** 2011-06-13 06:30 and 2011-06-14 05:30 switch to QC=2 ERA at temperatures ~11–13°C amid QC=1 temperatures >20°C. The **identical** `TA_F=28.473°C` and `VPD_F=26.676 hPa` recur on two dates. Investigate the gap-filled product versus ERA and longer block before editing either source.
- **FI-Let:** 2019-02-22 and 2021-01-15 show QC=1 to QC=2 source switches, including jumps ~15–18°C. Because the two sources disagree sharply, do not infer a true tower temperature from one of the sources. Cross-validate with independent station / ERA5-Land and missingness.
- **DE-Lnf:** 2023-06-22 06:30 `TA_F=4.9°C` differs sharply from nearby station/ERA, despite not passing the >15°C half-hour jump screen. Requires wider time-window review.
- **ES-Agu:** 2014-06-26 14:30 `TA_F=18.802°C`, QC=1, is cooler than ERA ~27.529°C; review before defining repaired block extent. Also 2011-12-16 & 2016-10-10 FLUXNET companion **TA_ERA / PA_ERA are corrupted**. They are NOT valid reference measurements and must never be used to substitute valid `TA_F` or `PA_F`.
- Review all site pressure discontinuities/locally unrealistic pressure, all humidity/longwave flags, surface landcover/PFT and BIF/ZBOT before DATM or spin-up.

## Reproduction

```bash
conda activate clm_fates_env
python ~/12_targeted_13site_temperature_pressure_repairs_trial.py --check

OUT=/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_targeted_TA_PA_trial_v1_20261014
python ~/12_targeted_13site_temperature_pressure_repairs_trial.py --run --out "$OUT"
```

Never run to an existing destination. `--check` writes nothing. `--run` creates an exclusive new trial directory containing **three complete candidate forcing CSVs**, 6-event QC/provenance ledger with original flags, source/outputs SHA256 manifest and a `DO_NOT_USE_FOR_DATM_OR_SPINUP` marker.

**Relevant methodological precedents:** `examples/ICOS_ES-LJu/scripts/03_prepare_forcing.py` for paired TA/VPD repair; `examples/FLUXNET_MultiSite_11/docs/QC_v5_extension_and_site_decisions.md` for provenance-rich site-specific pressure interpolation and non-overwriting version tags. Neither previous forward simulation nor passing broad numerical bounds constitutes scientific approval.
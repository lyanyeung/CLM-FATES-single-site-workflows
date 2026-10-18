# DK-Sor observed CO2 forcing: 1996–2024

**Status: first-stage QC and candidate-file generator committed; no CO2 experiment submitted.**

The source is `forcing/raw/ICOS_DK-Sor_FLUXNET_1996-2024_v1.3_r1/ICOS_DK-Sor_FLUXNET_FLUXMET_HH_1996-2024_v1.3_r1.csv`, columns `CO2_F_MDS` and `CO2_F_MDS_QC`.

Other DD/MM/WW/YY files contain temporal aggregations of these data, not five independent observations. A second `raw_multisource_v1` copy is not additional independent evidence. Source filenames specify a nominal 1996–2024 period, **not verified per-month measurement coverage**.

## Goal

Evaluate whether a historical DK-Sor tower-measured CO2 forcing improves simulated GPP/NEE relative to (a) the 361.93 ppm fixed-CO2 historical run and (b) a separate historical background-CO2 run. All experiments will inherit the same 1000-year spin-up CLM/FATES state and cover 1996–2024 **once**, rather than repeating 500/1000 years.

EC tower CO2 is a locally influenced mole fraction, **not** necessarily a free-atmosphere dry mole fraction. QC, intake height, wet/dry reference and long-term calibration history must be examined; a nighttime canopy CO2 buildup is not automatically appropriate for gridcell photosynthesis forcing.

## Immediate command (IRIDIS6 login node)

```bash
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only origin main
python examples/FLUXNET_MultiSite_6/scripts/19_audit_DK_Sor_tower_CO2_and_make_forcing.py 2>&1 | tee ~/DK_Sor_tower_CO2_audit.log
```

The Python script needs the existing `clm_fates_env` environment with pandas, numpy and netCDF4; if absent, activate that environment first.

The script reads only the canonical HH CSV, filters missing values and QC, summarizes QC=0 daytime observations, and requires at least 40 half-hour observations on 10 distinct days in **every** month, using a conservative 300–600 ppm raw plausibility screen and 300–500 ppm monthly median screen. It writes local audit reports under `forcing/tower_co2_experiment/`. If any month fails, **it deliberately exits nonzero** and does not manufacture a full-period CO2 forcing. A 25-ppm adjacent-month median jump also halts production.

If the series passes all preliminary thresholds, a candidate 348-month NetCDF file is written to `forcing/tower_co2_experiment/`. This **does not** establish that the file is accepted by CDEPS. The CDEPS `co2tseries` stream fields, coordinates and interpolation behavior must be verified with the *installed* CTSM version, `preview_namelists`, `CaseDocs`, and an actual pilot log before any 29-year production submission. The candidate is intentionally never installed or automatically submitted.

## Subsequent controlled experiment design

1. Review missing months and independent CO2 sensor/inlet metadata. If the full 29-year record cannot be supported with QC0 data, either restrict to an adequately observed common period or build an explicitly labeled tower/background merged product with provenance and sensitivity checks, and never call the merged product entirely observed.
2. Confirm the installed `COMPSET`, `DATM_MODE`, `CCSM_BGC`, `DATM_CO2_TSERIES` and CDEPS CO2 stream requirements. Enabling `CLM_CO2_TYPE=diagnostic` alone does not prove time-varying CO2 is applied.
3. Create a **new case** from the same 2996-01-01 spin-up restart; do not alter the successful `DK-Sor_FATES_HIST1996_2024_TEST` or `DK-Sor_FATES_SPINUP500` cases.
4. Verify a one-year historical-CO2 pilot, including initial-value CO2, resulting photosynthetic and respiration fluxes, dates, and any restart shock.
5. Run the historical 1996–2024 CO2 experiment, a fixed-CO2 1996–2024 control, and preferably a documented background historical-CO2 control.
6. Compare daily/monthly EC GPP/NEE, RECO/Rh if available, and spin-up-year 500/1000 forcing-phase-matched model fluxes. Report ongoing SOC drift independently.

Avoid committing raw ICOS datasets, private source paths within downloaded records, CO2 observations themselves, NetCDF forcing, restart states, SSH keys or cluster job logs to a public GitHub repository.

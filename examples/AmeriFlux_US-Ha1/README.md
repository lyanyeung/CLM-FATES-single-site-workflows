# US-Ha1 AmeriFlux / FLUXNET example

This directory records the reproducible CTSM/CLM-FATES single-site
workflow used for the Harvard Forest EMS Tower (`US-Ha1`).

## Site and simulation

- Network: AmeriFlux / FLUXNET
- Site: `US-Ha1`
- Latitude: `42.5378`
- Longitude: `-72.1715`
- Elevation: `340 m`
- Simulation period: `1991-2025`
- Forcing resolution: hourly
- Calendar: `NO_LEAP`
- `ATM_NCPL=24`
- Compset: `I1PtClm60FatesRsGs`
- Grid: `CLM_USRDAT`

Raw AmeriFlux/FLUXNET data are intentionally not stored in this repository.

## Meteorological forcing

Primary consolidated variables:

- `TA_F` -> `TBOT`
- `TA_F + VPD_F` -> `QBOT`
- `PA_F` -> `PSRF`
- `SW_IN_F` -> `FSDS`
- `LW_IN_F` -> `FLDS`
- `WS_F` -> `WIND`
- `P_F / 3600` -> `PRECTmms`

Measurement-height metadata:

- `TA_F`: 27.9 m
- `VPD_F`: 27.9 m
- `WS_F`: 29.0 m
- `PA_F`: 3.0 m
- `P_F`: 1.0 m

`ZBOT=27.9 m` is used because temperature and humidity are both referenced
to 27.9 m and wind is measured at a nearly identical 29 m level.

## Important forcing QC

`03_prepare_forcing.py` is the script used in the successful workflow.

AmeriFlux missing flags (`<= -9990`) are converted to missing values.

Three isolated forcing errors were identified:

- `LW_IN_F`, 2004-12-04 00:00: 0 W m-2
- `PA_F`, 2004-12-04 01:00: 11.363 kPa
- `LW_IN_F`, 2016-10-09 19:00: 0 W m-2

These isolated values are replaced by the mean of the adjacent hours.

Temperature and VPD are also checked jointly. If calculated actual vapour
pressure is non-positive or relative humidity is below 1%, BOTH `TA_F`
and `VPD_F` are replaced by the corresponding `TA_ERA` and `VPD_ERA`.

The successful input dataset required this paired ERA replacement for
29 hourly records. The complete correction log contains 61 variable-value
changes.

See `expected/forcing_qc_reference.txt`.

## DATM

`05_make_datm.py` creates 35 annual files:

`US-Ha1_forcing_1991.nc` ... `US-Ha1_forcing_2025.nc`

Each contains 8760 hourly records on the `NO_LEAP` calendar.

DATM mapping:

- `PRECTmms` -> `Faxa_precn`
- `FSDS` -> `Faxa_swdn`
- `ZBOT` -> `Sa_z`
- `TBOT` -> `Sa_tbot`
- `WIND` -> `Sa_wind`
- `QBOT` -> `Sa_shum`
- `PSRF` -> `Sa_pbot`
- `FLDS` -> `Faxa_lwdn`

## Case

Case name:

`US-Ha1_FATES_1PT`

Runtime configuration:

- `RUN_STARTDATE=1991-01-01`
- `STOP_N=1`, `STOP_OPTION=nyears`
- `REST_N=1`, `REST_OPTION=nyears`
- `RESUBMIT=34`
- daily history: `hist_nhtfrq=-24`, `hist_mfilt=365`
- Intel + OpenMPI

The initial submission plus 34 automatic resubmissions covers 1991-2025.

## EC comparison

The comparison uses:

- EC GPP: `GPP_DT_VUT_REF`
- EC NEE: `NEE_VUT_REF`
- FATES GPP: `FATES_GPP`
- FATES NEE: `-FATES_NEP`

Because US-Ha1 input is hourly, a daily EC value requires at least
20 valid hourly observations. Monthly comparison requires at least
20 matched valid days.

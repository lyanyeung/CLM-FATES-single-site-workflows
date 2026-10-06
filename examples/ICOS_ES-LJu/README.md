# ES-LJu ICOS/FLUXNET example

This directory records the full ES-LJu workflow used for the successful CLM-FATES forward simulation.

## Site and period

- Site: `ES-LJu`
- Latitude: `36.926594`
- Longitude: `-2.752115`
- Elevation: `1600 m`
- Atmospheric measurement height used for DATM (`ZBOT`): `2.5 m`
- Raw package: `EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1`
- Simulation period: `2004-01-01` to `2024-12-31`
- Native forcing resolution: 30 min
- CTSM forcing calendar: `noleap`
- `ATM_NCPL=48`

Important metadata distinction: `HEIGHTC=0.3 m` is canopy/shrub height and is **not** `ZBOT`. The BIF variable metadata gives the atmospheric measurement height of 2.5 m for `TA_F` / `WS_F`, so `ZBOT=2.5 m`.


The successful IRIDIS raw-data layout was:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/ES-LJu/
└── forcing/raw/EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1/
    ├── EUF_ES-LJu_FLUXNET_FLUXMET_HH_2004-2024_v1.3_r1.csv
    ├── EUF_ES-LJu_FLUXNET_ERA5_HH_1981-2025_v1.3_r1.csv
    ├── EUF_ES-LJu_FLUXNET_BIF_2004-2024_v1.3_r1.csv
    └── ...
```

## Raw variables used

Atmospheric forcing:

- `TA_F`
- `VPD_F`
- `PA_F`
- `SW_IN_F`
- `LW_IN_F`
- `WS_F`
- `P_F`

Flux validation:

- GPP: `GPP_DT_VUT_REF`
- NEE: `NEE_VUT_REF`

ES-LJu does not provide the NT GPP family used at some other sites; this case therefore uses the DT GPP product.

## Workflow

Run the scripts in order.

```bash
# Local WSL
bash scripts/01_transfer_raw_data.sh

# IRIDIS6
cd /iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/ES-LJu
bash scripts/02_inspect_metadata.sh
python scripts/03_prepare_forcing.py
python scripts/04_validate_forcing.py
python scripts/05_make_datm.py
bash scripts/06_make_surface.sh
bash scripts/07_create_case.sh
bash scripts/08_build_and_submit.sh
python scripts/09_compare_fates_ec.py
```

The scripts use the environment variables in `scripts/00_config.sh`. Edit only that file if paths or software versions change.

## Site-specific forcing QC

The raw `TA_F` contains a clear corruption episode in 2023. Example behavior included values around `-40 °C` while ERA5 was around `+10–17 °C`, and one value around `46 °C`; the supplied QC flag did not reliably catch the problem.

The successful workflow used:

1. Standard missing-value mask: values `<= -9990` become missing.
2. Replace `TA_F` **and** `VPD_F` with ERA counterparts when:
   - `TA_F < -20 °C`, or
   - `TA_F > 40 °C`, or
   - in 2023 only, `abs(TA_F - TA_ERA) >= 15 °C`.
3. Recompute implied vapor pressure / RH.
4. If `VPD < 0`, vapor pressure is non-positive, or implied RH `< 1%`, replace **both** temperature and VPD with ERA values.
5. Recheck final vapor pressure and RH.
6. Remove 29 February before producing noleap forcing.

These thresholds are **site-specific QC choices for ES-LJu**, not generic FLUXNET rules.

## Conversion to DATM variables

```text
TBOT      = TA_USE + 273.15
PSRF      = PA_F * 1000                         # kPa -> Pa
es_hPa    = 6.112 * exp(17.67*T/(T+243.5))
ea_hPa    = es_hPa - VPD_USE
QBOT      = 0.622*(ea_hPa*100) /
            (PSRF - 0.378*(ea_hPa*100))
FSDS      = SW_IN_F
FLDS      = LW_IN_F
WIND      = WS_F
PRECTmms  = max(P_F, 0) / 1800                 # mm per 30 min -> mm s-1
ZBOT      = 2.5
```

## Accepted forcing QC result

The final processed forcing had exactly `367,920` rows (`21 × 17,520`) and no missing values.

Reference ranges from the successful run are stored in `expected/forcing_qc_reference.txt`.

## CTSM surface file

The successful workflow used:

- source surfdata:
  `lnd/clm2/surfdata_esmf/ctsm5.3.0/surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc`
- surface mesh:
  `share/meshes/fv0.9x1.25_141008_ESMFmesh.nc`
- CTSM utility:
  `tools/site_and_regional/subset_data point`

The generated ES-LJu file in the successful run was:

```text
surfdata_ES-LJu_hist_2000_16pfts_c261005.nc
```

A future rerun will receive a new creation-date suffix.

## FATES case

Case name:

```text
ES-LJu_FATES_1PT
```

The forward simulation is a startup run, one model year per CIME job:

- `RUN_STARTDATE=2004-01-01`
- `STOP_OPTION=nyears`
- `STOP_N=1`
- `REST_OPTION=nyears`
- `REST_N=1`
- `RESUBMIT=20`

Thus the initial submission runs 2004 and CIME automatically resubmits through 2024.

## EC comparison

The comparison follows the same conventions as the other site examples:

- EC missing values `<= -9990` -> NaN
- remove 29 February
- half-hourly EC -> daily only when at least `40 / 48` half-hours are valid
- daily -> monthly only when at least `20` valid matched days exist
- EC flux conversion:
  `mean(µmol CO2 m-2 s-1) × 86400 × 12.0107e-6`
  -> `g C m-2 d-1`
- FATES flux conversion:
  `kg C m-2 s-1 × 86400 × 1000`
  -> `g C m-2 d-1`
- FATES GPP: `FATES_GPP`
- FATES NEE: `-FATES_NEP`

Plots are deliberately split into windows of at most 10 years:

- 2004–2013
- 2014–2023
- 2024

Both EC and FATES series are solid lines. Only the NEE `y=0` reference line is dashed.

## Problems encountered and fixes

See `KNOWN_ISSUES.md`. The two most important safeguards are:

1. Never generate an ES-LJu DATM stream by naive text replacement from another site's file list. Generate the exact 2004–2024 list.
2. CLM history output for this case is `*.clm2.h0a.*.nc`, not `*.clm2.h0.*.nc`.

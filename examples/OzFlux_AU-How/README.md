# AU-How OzFlux example

This example records the successful Howard Springs (`AU-How`) CTSM/CLM-FATES
single-point forward workflow used on IRIDIS6.

## Site / source

- Network/data source: OzFlux / TERN Ecosystem Processes
- Site: Howard Springs (`AU-How`)
- Source file: `HowardSprings_L6.nc`
- Coordinates used in the successful run: `-12.4952, 131.15005`
- Elevation: `64 m`
- Tower / forcing height: `23 m`
- Native time step: 30 min
- Selected CLM-FATES period: 2003-2025
- Calendar used by CTSM: `NO_LEAP`
- `ATM_NCPL=48`

The source L6 metadata identifies a 23 m tower and 30-minute data. The L6
meteorological products are already gap-filled. This repository therefore does
not add a second arbitrary interpolation stage.

## Complete workflow

Run in order:

```bash
# local WSL
bash scripts/01_transfer_raw_data.sh

# IRIDIS
conda activate clm_fates_env
cd /iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/AU-How

bash scripts/02_inspect_metadata.sh
python scripts/03_prepare_forcing.py
python scripts/04_validate_forcing.py
python scripts/05_make_datm.py
bash scripts/06_make_surface.sh
bash scripts/07_create_case.sh
bash scripts/08_build_and_submit.sh
python scripts/09_compare_fates_ec.py
```

Edit `scripts/00_config.sh` if paths change.

## Forcing mapping

```text
OzFlux   CLM DATM
------   --------
Ta       TBOT       °C -> K
SH       QBOT       kg/kg, direct
ps       PSRF       kPa -> Pa
Fsd      FSDS       W/m2
Fld      FLDS       W/m2
Ws       WIND       m/s
Precip   PRECTmms   mm/30 min -> mm/s
         ZBOT       23 m
```

The processed CSV retains leap days and therefore has 403,248 records for
2003-2025. The annual DATM writer removes 29 February; every annual NetCDF then
has 17,520 half-hourly records.

## Surface file

The successful run used the same CTSM source assets as the ICOS example:

```text
lnd/clm2/surfdata_esmf/ctsm5.3.0/
  surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc

share/meshes/
  fv0.9x1.25_141008_ESMFmesh.nc
```

Successful generated surface file:

```text
surfdata_AU-How_hist_2000_16pfts_c260929.nc
```

A fresh run receives a new creation-date suffix.

## FATES case

```text
case            = AU-How_FATES_1PT
compset         = I1PtClm60FatesRsGs
grid            = CLM_USRDAT
compiler / MPI  = Intel / OpenMPI
RUN_STARTDATE   = 2003-01-01
STOP_N          = 1 year
RESUBMIT        = 22
```

That gives the initial 2003 run plus 22 automatic resubmissions through 2025.

## EC comparison

Use:

```text
OzFlux GPP = GPP_LT
OzFlux NEE = NEE_LT

FATES GPP  = FATES_GPP
FATES NEE  = -FATES_NEP
```

Rules:

- convert EC values `<= -9990` to NaN before aggregation
- remove 29 February
- daily EC value requires at least 40 of 48 half-hours
- monthly comparison requires at least 20 valid matched days
- EC flux conversion:
  `µmol CO2 m-2 s-1 * 86400 * 12.0107e-6`
- FATES conversion:
  `kg C m-2 s-1 * 86400 * 1000`

Plots are deliberately split into:

```text
2003-2012
2013-2022
2023-2025
```

Both EC and FATES are solid lines; only the NEE zero-reference line is dashed.

See `KNOWN_ISSUES.md` before adapting this case to another OzFlux site.

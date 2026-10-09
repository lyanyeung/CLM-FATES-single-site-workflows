# GF-Guy — Stage 1: single-site surface data and fixed-CO2 first-year case

This is a **reproducibility record / set of scripts** for the GF-Guy CLM-FATES first-year setup on Southampton IRIDIS6. Its structure and approach mirror [`examples/ICOS_ES-LJu`](../ICOS_ES-LJu/README.md), especially `06_make_surface.sh` and `07_create_case.sh`. **This is not the 300-year spin-up workflow.**

## GF-Guy settings

| Setting | Value |
|---|---|
| Site ID | GF-Guy |
| Location used for point extraction | 5.2788° N, −52.9249° E |
| Initial simulation date | 2017-01-01 |
| Meteorological DATM files expected | `GF-Guy_DATM_2017.nc` through `GF-Guy_DATM_2025.nc` (check on IRIDIS) |
| Atmospheric CO2 | **405.0 ppm, fixed** |
| Surface reference year | **2000** (distinct from the CO2/reference forcing year) |
| Simulation | Startup; 1 year; no automatic resubmit |
| Coupling / calendar | `ATM_NCPL=48`; `NO_LEAP` |
| CESM compset | `I1PtClm60FatesRsGs` |
| Grid | `CLM_USRDAT` |
| Machine, compiler, MPI | `iridis6`, `intel`, `openmpi` |
| Case | `GF-Guy_FATES_SURF2000_CO2405_1PT` |

**CO2 caveat:** 405 ppm is the intentional *fixed case setting*, approximately representative of atmospheric CO2 around the site's 2017 starting year. It is **not** a claim that the local EC site directly measured exactly 405.0 ppm, nor a time-varying record.

**Forcing caveat:** The successful case's logs showed data from 2017 and 2025; this record models the complete 2017–2025 file range. Verify its full actual DATM stream with `09_inspect_successful_case.sh` before asserting identical forcing provenance.

## Exact surface methodology copied from ES-LJu

1. Copy `CTSM/tools/site_and_regional/default_data_2000.cfg`.
2. Pin surface directory to `lnd/clm2/surfdata_esmf/ctsm5.3.0`.
3. Pin source surface to `surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc`.
4. Pin mesh to `fv0.9x1.25_141008_ESMFmesh.nc`.
5. Run `tools/site_and_regional/subset_data point` with GF-Guy coordinates, `--surf-year 2000`, `--create-surface` and `--create-user-mods`.
6. Remove any generated `MPILIB=mpi-serial` override; create a CLM_USRDAT FATES case using Intel/OpenMPI.
7. In `user_nl_clm`, set `use_excess_ice = .false.` and `use_excess_ice_streams = .false.`; keep daily history.
8. Set `CLM_CO2_TYPE=constant` and `CCSM_CO2_PPMV=405.0`, `RUN_STARTDATE=2017-01-01`, and run a single model year.

Unlike surface reference year 2000, CO2 is selected to approximate the *simulation starting year* 2017.

## Scripts

```text
scripts/
├── 00_config.sh                     # Site paths, coordinates, 2017, CO2=405
├── 06_make_surface.sh               # ES-LJu-style surface + user_mods
├── 07_create_case.sh                # DATM stream + first-year 405-ppm case
├── 08_build_and_submit.sh           # OPTIONAL: build + submit first year
└── 09_inspect_successful_case.sh    # READ-ONLY existing-case audit
```

## Important: the successful case already exists

The site already had a successful one-year run (`4073259`) and an independent 300-year case is being developed. **You do not need to rerun `06_make_surface.sh`, `07_create_case.sh`, or `08_build_and_submit.sh` simply to upload these source files to GitHub.** The scripts purposely refuse to overwrite existing site products or cases. No model output, raw EC data or local user credentials are included.

To *inspect* the existing one-year case without modifying anything on IRIDIS:

```bash
cd /path/to/repository/examples/FLUXNET_GF-Guy
bash scripts/09_inspect_successful_case.sh | tee GF-Guy_first_year_audit.txt
```

Before uploading an audit output, check it does not expose internal paths or other details you do not want published. It is **not necessary to upload the audit**.

## Future reproduction (only in an isolated scratch workspace)

Do **not** execute this against the current successful case. To recreate from scratch in a separate scratch location, change `CLM_ROOT`/`SITE_ROOT` and `CASE_NAME` inside `00_config.sh` appropriately, and ensure the annual DATM NetCDF forcing already exists:

```bash
bash scripts/06_make_surface.sh
bash scripts/07_create_case.sh
bash scripts/08_build_and_submit.sh
```

The scripts are sequential: `07_create_case.sh` checks for every required DATM NetCDF, and does not create missing forcing. Forcing preparation is handled upstream and is deliberately outside this Stage 1 snapshot.

## Scope and provenance

- Source method: actual `examples/ICOS_ES-LJu/scripts/{00_config.sh,06_make_surface.sh,07_create_case.sh,08_build_and_submit.sh}` in the repository.
- GF-Guy settings: coordinates, 2017 start, fixed CO2=405 ppm, successful workaround disabling Excess Ice, source surface-year 2000, selected from the established GF-Guy work in this project.
- The scripts here are reconstructed for documentation and **were not re-executed on IRIDIS in this packaging step**. `09_inspect_successful_case.sh` can be used to cross-check against the actual previously run one-year case.
- This package does **not** include nor submit the 300-year spin-up and does **not** change GitHub remotely.

# ES-LJu known issues and safeguards

## 1. `user_nl_datm_streams` must contain only 2004–2024

A naive `sed` replacement of the FI-Hyy stream file produced invalid ES-LJu entries for 1998–2003 and duplicate 2004 / 2024 files.

**Fix:** generate the full `datafiles` list from `seq 2004 2024`; `07_create_case.sh` does this.

Expected count:

```bash
grep -o 'ES-LJu_DATM_[0-9]\{4\}\.nc' user_nl_datm_streams | wc -l
# 21
```

## 2. Do not use `DATM_CLMNCEP_YR_*`

This compset uses `DATM%1PT`. The XML variables

```text
DATM_CLMNCEP_YR_START
DATM_CLMNCEP_YR_ALIGN
DATM_CLMNCEP_YR_END
```

do not exist.

Use `year_first`, `year_last`, and `year_align` in `user_nl_datm_streams`.

## 3. `DIN_LOC_ROOT`

A fresh case may default to:

```text
/iridisfs/cesm_input_data
```

The successful workflow uses:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/inputdata
```

Set `DIN_LOC_ROOT` before generating namelists. If it is changed after `Buildconf/*.input_data_list` already exists, rerun:

```bash
./preview_namelists
```

before `./check_input_data`.

## 4. OpenMPI vs generated `mpi-serial`

`subset_data --create-user-mods` may generate `MPILIB=mpi-serial` in `user_mods/shell_commands`.

Remove that line before `create_newcase`; the successful case uses `--mpilib openmpi`.

## 5. Model history filename

The archived daily history is matched with:

```text
*.clm2.h0a.*.nc
```

not:

```text
*.clm2.h0.*.nc
```

## 6. ES-LJu GPP product

Use:

```text
GPP_DT_VUT_REF
```

There is no NT GPP family in this package.

## 7. NEE sign

EC `NEE_VUT_REF` uses the tower NEE convention. FATES `FATES_NEP` is positive for net ecosystem production / uptake, so compare EC NEE with:

```text
-FATES_NEP
```

## 8. Plot windows

Do not create one unreadable 2004–2024 plot. Use at most 10 years per panel/file:

```text
2004–2013
2014–2023
2024
```

# AU-How known issues and safeguards

## 1. Do not reuse the earlier TCCAS time conversion

The earlier TCCAS Howard Springs workflow converted local OzFlux END timestamps
to UTC and shifted them by 30 minutes. The successful CLM-FATES AU-How forcing
workflow documented here did **not** use that transformation. It decoded the
OzFlux NetCDF time coordinate directly, selected 2003-2025, and used the
annual DATM writer with 30-minute interval-center timestamps.

Do not mix the two workflows.

## 2. Forcing mapping

The successful CLM-FATES mapping is:

```text
Ta      -> TBOT      (+273.15)
SH      -> QBOT      (direct, kg/kg)
ps      -> PSRF      (*1000, kPa -> Pa)
Fsd     -> FSDS
Fld     -> FLDS
Ws      -> WIND
Precip  -> PRECTmms  (/1800, mm per 30 min -> mm/s)
ZBOT    = 23 m
```

## 3. Leap days

The processed 2003-2025 CSV contains `403248` half-hourly records, including
six leap days. `05_make_datm.py` removes 29 February so every annual DATM file
has exactly `17520` records.

Expected noleap total: `402960`.

## 4. DATM time convention

The AU-How annual writer used 30-minute interval centers:

```text
00:15, 00:45, 01:15, ...
```

represented as:

```python
(np.arange(17520) + 0.5) / 48
```

days since January 1.

## 5. `DIN_LOC_ROOT`

A fresh CIME case may point at `/iridisfs/cesm_input_data`. The working IRIDIS
configuration uses:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/inputdata
```

Set it before `preview_namelists` / `check_input_data`.

## 6. OpenMPI

If `subset_data --create-user-mods` inserts `MPILIB=mpi-serial`, remove that
line before `create_newcase`. The successful forward case uses OpenMPI.

## 7. EC missing values

`GPP_LT` and `NEE_LT` use negative fill values. Values `<= -9990` must become
NaN **before** half-hourly -> daily -> monthly aggregation.

## 8. EC/model convention

```text
EC GPP   = GPP_LT
EC NEE   = NEE_LT
FATES GPP = FATES_GPP
FATES NEE = -FATES_NEP
```

Daily EC completeness: >=40/48 half-hours.
Monthly completeness: >=20 valid matched days.

## 9. History filename

The comparison script reads:

```text
*.clm2.h0a.*.nc
```

## 10. Plot windows

Use at most ten years per figure:

```text
2003-2012
2013-2022
2023-2025
```

Both EC and FATES are solid lines. Only the NEE zero-reference line is dashed.

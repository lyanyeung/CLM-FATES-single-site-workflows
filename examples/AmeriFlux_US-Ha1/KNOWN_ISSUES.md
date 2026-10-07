# US-Ha1 known issues and safeguards

## 1. Do not treat 100% complete `_F` variables as 100% tower observations

AmeriFlux consolidated `_F` variables combine measured/gap-filled data
and downscaled ERA data. In this downloaded product `LW_IN_F_QC=2`
throughout the record, so incoming longwave is ERA-derived.

## 2. Three isolated forcing values are physically invalid

The successful workflow corrects:

- 2004-12-04 00:00 `LW_IN_F=0`
- 2004-12-04 01:00 `PA_F=11.363 kPa`
- 2016-10-09 19:00 `LW_IN_F=0`

Only these isolated values are interpolated from adjacent hours.

## 3. TA and VPD must be checked jointly

Individual QC flags can look acceptable while the TA/VPD combination is
physically inconsistent.

The workflow computes vapour pressure and RH. If:

- `ea <= 0`, or
- `RH < 1%`

both TA and VPD are replaced together using `TA_ERA` and `VPD_ERA`.

Successful reference: 29 hours replaced.

## 4. Measurement heights differ

- TA/VPD: 27.9 m
- wind: 29 m
- pressure: 3 m
- precipitation: 1 m

`ZBOT=27.9 m` is used as the atmospheric reference height.

## 5. DATM uses QBOT, not RH

The default `CLM_USRDAT.UNSET` stream may request:

`RH Sa_rh`

The custom stream must instead use:

`QBOT Sa_shum`

because the prepared US-Ha1 forcing contains specific humidity.

## 6. DATM mode is hourly

US-Ha1 forcing is hourly:

`ATM_NCPL=24`

Each annual no-leap file must contain exactly 8760 records.

## 7. `user_nl_datm` may be required even when empty

On this CTSM/CDEPS configuration `preview_namelists` failed when
`user_nl_datm` did not exist. The case workflow therefore creates it
with `touch user_nl_datm`.

## 8. Keep OpenMPI

`subset_data` may place `MPILIB=mpi-serial` in generated user mods.
The workflow removes that line and creates the case with OpenMPI.

## 9. EC aggregation differs from half-hourly sites

US-Ha1 EC data are hourly. Daily EC values therefore require at least
20 of 24 valid hourly records, rather than the 40-of-48 rule used for
half-hourly sites.

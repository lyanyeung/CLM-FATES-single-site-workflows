# Stage81 — DATM NetCDF technical build from **completed** Stage80 forcing

**Current user-confirmed result:** Stage80 **PASS** on 24 October 2026, 10 site versions selected. Only **18 original RH<1% half-hours** were replaced by native ERA5 coupled T2m/Td2m/SP, all **1,091 original RH1–5% rows** were retained; four new full forcing CSVs, six original selected CSVs, and checksum manifest created at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage80_RH_lt1_final_20261024T123353Z/`

All ten original forcing files preserved. User approved retaining 17 RH/T boundary warnings from the 18 precise corrections. No further RH repair is needed.

## Actual SUCCESSFUL execution: IRIDIS6 24 October 2026

**User-confirmed HPC log**: `SOURCE PASS | SYNTAX PASS`, Stage81 NOLEAP/7-variable `SELF-TEST PASS`, ten-site SHA-pinned Stage80 source and existing-point-surface `CHECK PASS`, all ten `NETCDF BUILD PASS` lines, followed by `STAGE81 DATM NETCDF TECHNICAL PREVIEW COMPLETE`. Actual output root:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage81_DATM_technical_20261024T162235Z/`

| Site | Time span | NetCDF annual files |
|---|---|---:|
| BR-Ma2 | 1999–2016 | 18 |
| CA-Ca3 | 2001–2024 | 24 |
| CA-Cbo | 1996–2024 | 29 |
| CA-LP1 | 2007–2024 | 18 |
| CA-Man | 1994–2008 | 15 |
| CA-TP1 / CA-TP3 / CA-TP4 | 2002–2023 each | 22 each |
| US-Aud | 2002–2024 | 23 |
| US-Bar | 2004–2023 | 20 |
| **TOTAL** | **10 sites** | **213** |

A **per-file SHA-256 `manifest.json`** and **10 XML stream TEMPLATES, NOT ACTIVATED** were saved. The script did its designed annual NetCDF readback checks. GitHub contains scripts and provenance, **not** these raw NetCDF bytes; success here is evidenced by the operator's IRIDIS6 log. **Stage81 technical NetCDF creation is COMPLETE**, but neither the stream templates nor scientific spin-up are approved until the actual domain, DATM vs CDEPS stream format, sensor `ZBOT`, timestamp-support and site-model tests are verified. All printouts from Stage81 show `ZBOT=UNRESOLVED`, not validated tower height.

## What Stage81 actually builds

**[81_build_DATM_from_Stage80.py](81_build_DATM_from_Stage80.py)** consumes **only the completed Stage80 ten-site pointer manifest**. It SHA-verifies the source manifest and all 10 complete forcing CSVs before doing anything, and derives point-grid coordinates only from the *existing* site `subset_data/surfdata*.nc` files. It does NOT infer, guess, or silently inject station GPS coordinates or sensor heights.

- **10 site series** of annual `YYYY.nc` NETCDF4_CLASSIC files (one year per file, not ~2,800 monthly files; saves inode quota), with `time,lat,lon` dimensions, 1×1 point coordinates, and a **half-hour NOLEAP CF time coordinate** (17,520 records per year).
- Meteorological fields `FLDS`, `FSDS`, `PRECTmms`, `PSRF`, `TBOT`, `WIND`, and `SHUM` (the exact Stage80 `QBOT` values), plus `RH` derived independently from Stage80 `TBOT/QBOT/PSRF`, plus a `QBOT` traceability alias. **No source humidity recomputation or replacement.**
- A **legacy-CLM1PT-style stream XML TEMPLATE** for each site, with `fieldInfo` listing year files, `offset=0` for provisional time index, and clearly marked **site domain placeholder**. These templates are **NOT** written to a CIME case. The actual existing case may use modern CDEPS streams YAML, requiring adaptation.
- Per-site surface / forcing source SHA provenance, NetCDF readback checks, a master `manifest.json` listing every NC SHA, year, full input checksum, and the scientific caveats.
- No existing forcing, land surface, inputdata, CIME/DATM streams or Slurm job is modified.

Run:

```bash
SCRIPT="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10/scripts/stage81/81_build_DATM_from_Stage80.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --check
python3 -B "$SCRIPT" --build --outdir "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage81_DATM_technical_$(date -u +%Y%m%dT%H%M%SZ)"
```

Requirements: `numpy`, `netCDF4` (both already referenced by existing Stage33), the 10 selected CSVs and 10 existing site point surface files. `--check` identifies absent input/source packages early.

## Important distinction: file conversion vs running CLM-FATES

From the official CLM user guide, CLM1PT single-point meteorology can be hourly or half-hourly in NetCDF, with `SHUM` substituting for `RH`; `ZBOT` is optional to the **DATM data loader** but legacy DATM falls back to a **30-m height** if omitted. That model assumption is **not a scientifically validated tower sensor height**. In the previously recorded Batch01 source audit, **CA-Cbo and CA-Man** have unresolved FLUXNET temperature sensor-height crosswalks. Stage81 deliberately **does not write or invent ZBOT**, and the user **must not activate** these stream templates in full spin-up cases before verifying ZBOT or explicitly accepting an appropriate height treatment.

Time source values were saved by the original Batch01 workflow as half-hourly station-local labels; CLM1PT stream time centering for nearest interpolation is normally midpoint. Stage81 **does not fabricate LST–UTC offsets or shift timestamps by 15 minutes**. Its NetCDF time coordinate is mathematically NOLEAP-consistent but interval meaning must be independently confirmed before connection. Existing land surface/PFT and site scientific checks also remain separate.

Official reference: [CTSM DATM time offsets, CLM1PT and stream settings](https://escomp.github.io/CTSM/users_guide/setting-up-and-running-a-case/customizing-the-datm-namelist.html) and [CLM user guide atmosphere forcing fields and format](https://docs.cesm.ucar.edu/models/clm/4.0/models/lnd/clm/doc/UsersGuide/x9387.html).

**This Stage81 output is actual NetCDF meteorology data, not just a report, but is designated TECHNICAL_PREVIEW_ONLY until metadata/case-time integration is checked.**

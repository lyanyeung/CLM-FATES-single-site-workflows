# Stage77 — operator decision: recompute **ALL RH <5%** using native ERA5 T2m + dewpoint2m + pressure

> **SUPERSEDED AS THE CURRENT OPERATOR RULE BY STAGE80 (24 October 2026).** This Stage77 document remains an archival reproducibility record only. The user now explicitly requests **only 18 original RH<1% half-hours replaced by the already-computed native ERA5 T/D2m/P joint state; all 1,091 original RH 1–5% and every other Stage75 record remain unchanged**. Do not select the former Stage77 1,109-row trial as current forcing. See [Stage80](../stage80/README.md). Existing outputs and evidence are retained; no new ERA5 downloads required.


**Latest operator decision on 24 October 2026 OVERRIDES both the earlier Stage76 "accept RH 1–5% unchanged" decision and the earlier CA-Man accepted RH<1% risk for the specific low-RH records.** The scope is **1,109 half-hour records** across six sites in AmeriFlux Batch01, counted from the *Stage75 reviewed forcing versions*, **including the existing Stage74 CA-Man 18-event trial**. All sites not listed below are untouched.

| Site | Original RH<1% | RH 1–5% | Native ERA5 joint-recompute targets | Site coord (AmeriFlux) | Provisional UTC = local standard time + |
|---|---:|---:|---:|---|---|
| CA-Ca3 | 7 | 34 | **41** | 49.5346, −124.9004 | 480 min |
| CA-Cbo | 2 | 26 | **28** | 44.3184, −79.9341 | 300 min |
| CA-Man | 1 | 120 | **121** | 55.8796, −98.4808 | 360 min |
| CA-TP4 | 0 | 6 | **6** | 42.7102, −80.3574 | 300 min |
| US-Aud | 0 | 874 | **874** | 31.5907, −110.5104 | 420 min |
| US-Bar | 8 | 31 | **39** | 44.0646, −71.2881 | 300 min |
| **Total** | **18** | **1,091** | **1,109** | | |

## Scientific method — strictly source-coherent

Use the CDS dataset **[ERA5 hourly time-series on single levels](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries)** and request **`2m_temperature` (K), `2m_dewpoint_temperature` (K), `surface_pressure` (Pa)** at the same nearest grid point and UTC hours. Raw FLUXNET `TA_ERA`/`VPD_ERA` or a dewpoint inferred from VPD are **not substitutes for actual native ERA5 dewpoint**.

At half-hour times, interpolate **temperature (K)**, **actual vapour pressure** `e=e_s(Tdew)`, and **surface pressure (Pa)**; calculate from the resulting coherent state:

- `RH = 100*e/e_s(T)`
- `VPD = e_s(T)-e` in hPa
- `QBOT = 0.622*e / (p_hPa - 0.378*e)` in kg/kg
- `TBOT = T_K`, `TA_USE = T_K - 273.15`, `PSRF = p_Pa`, `VPD_USE = VPD`.

The script uses a **water-saturation formulation** and requires a follow-up ice/water convention check in winter, and flags meteorological discontinuities after replacement. **Do not retain original QBOT/PSRF/VPD_USE** when substituting ERA T. There is no FLUXNET fallback.

## 24 October 2026 actual IRIDIS6 execution and bug fix

**Confirmed user log:** all **45** CDS native ERA5 downloads finished and the merged native T2m/D2m/SP CSV and checksum manifest were saved under `reports/stage77_ERA5_native_20261024T100640Z/`. The `--check` recomputed exactly **1,109/1,109** targets with same-source thermodynamics (no selected forcing edits). The first `--trial` generated full-file, numerically validated CA-Ca3 (41 edits, RH<1: 7→0) and CA-Cbo (28 edits, RH<1: 2→0), then crashed on CA-Man at `int(src.stem.rsplit('_',2)[-2])`, because its Stage74 source filename is `...TRIAL_NOT_PRODUCTION.csv` and its second-to-last token is `NOT` (not a year). This is **a script filename-parser bug**, not a CDS/download or ERA5 physical-calculation failure.

**Fixed script:** derive `(first_year,last_year)` from the canonical Stage58 `SITES` metadata keyed by site, rather than parsing the filename. To finish the remaining six-site trial, **reuse the already downloaded `native_ERA5_all_1109_RH_lt5_hourly_T2m_D2m_SP.csv` and its manifest**, redownload the patched Stage77 script, and rerun `--check` then `--trial --outdir NEW_UNIQUE_DIRECTORY`. **Do not redownload the 45 ERA5 requests.** Keep the first partially populated trial folder for audit or manual cleanup, and do not reuse it as the fresh output directory.

**Science note:** the native ERA5 `--check` reported many large original-to-ERA RH boundary differences (e.g., 96/121 CA-Man targets and 35/41 CA-Ca3 targets), even though all substitutions are thermodynamically consistent. These changes need review before approving model use. The source clock offsets in this script remain provisional.

## Modes

`77_native_ERA5_all_RH_below5.py`:

- `--self-test`: pure internal physics / census tests
- `--plan`: inspect all six checksum-pinned Stage75 candidate inputs and list site/year CDS requests, **no writes**
- `--download --outdir NEW_DIRECTORY` (or `--download --resume --outdir EXISTING_DIRECTORY` to recheck/reuse previously saved raw downloads after interruption): actual remote CDS requests for all site/year windows that contain RH<5 events. Requires **cdsapi >=0.7.7**, the user's private `~/.cdsapirc` and accepted dataset licence. Requests cover only the actual flagged event range **±2 days** within each station/year bundle, rather than whole calendar years; `--resume` revalidates saved CDS source files before reuse. Writes raw CDS CSVs, canonical hourly native ERA5 CSV and source SHA manifest into **only the new directory**.
- `--check --native-csv PATH`: verify **all 1,109 matches**, compute all updated variables, report site summaries, **no writes**.
- `--trial --native-csv PATH --outdir NEW_DIRECTORY`: create six complete standalone **TRIAL_NOT_PRODUCTION** forcing CSVs; one change ledger per site, SHA-256 manifest, compare every cell/row, and run the complete Stage58 NOLEAP/physics/thermodynamic-closure audit per site. Only the 5 coupled met columns may change and only at the exact 1,109 original RH<5 timestamps.

**Do not apply production or start CLM-FATES based on `--trial`.** Even when physics passes, nearest ERA5 grid != in-situ tower; **provisional** standard-clock offsets above have not been independently verified from BIF/BADM or interval semantics. The user approves the *joint-recompute decision* and its scope, not an unverified timestamp or a model restart. Production release must preserve original checksums and separately review offset, discontinuities and any resulting RH<5 events. Existing Stage74 edits are retained in the CA-Man baseline; the one CA-Man RH<1 previously accepted risk is **now part of Stage77 replacement scope**.

## References
- [Copernicus ERA5 time-series documentation](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries)
- [CDS API setup](https://cds.climate.copernicus.eu/how-to-api)
- [AmeriFlux official site coordinates](https://ameriflux.lbl.gov/sites/site-search/)
- [Repository-level mandatory meteorological source consistency](../../../../README.md)

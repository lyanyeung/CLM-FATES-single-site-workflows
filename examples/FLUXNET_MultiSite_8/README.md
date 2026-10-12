# FLUXNET eight-site CLM-FATES workflow — upload, surface, QC v5 and dynamic-ZBOT DATM

**2026-10-12 snapshot:** Eight site datasets transferred and extracted on IRIDIS6; point surfaces created; forcing QC v5 run with targeted human reviews; three FR-Hes temperature/humidity time steps revised in a **separate** versioned forcing file. **188/188** annual candidate DATM NetCDF files validated. Each site has `STRUCTURE_OK_REVIEW`: this certifies structural/numerical checks, **not** complete scientific forcing, PFT or spin-up readiness.

This example parallels [`../FLUXNET_MultiSite_6/`](../FLUXNET_MultiSite_6/). It deliberately contains source scripts and decision documentation **only**. Do not commit or redistribute downloaded FLUXNET/ICOS/EUF ZIPs, raw or processed CSVs, weather data, output NetCDFs, or model archives. Respect each network's data licence and citation requirements.

## Sites

| Site | Release prefix and eligible period | Model forcing years | Annual DATM |
| --- | --- | --- | ---: |
| CZ-BK1 | ICOS (2004–2026) | 2004–2025 | 22 |
| IT-Ren | ICOS (1999–2026) | 1999–2025 | 27 |
| FR-Hes | ICOS (1997–2026) | 1997–2025 | 29 |
| FR-FBn | ICOS (2008–2024) | 2008–2024 | 17 |
| DE-Hzd | ICOS (2010–2025) | 2010–2025 | 16 |
| CH-Dav | ICOS (1997–2026) | 1997–2025 | 29 |
| BE-Vie | ICOS (1996–2026) | 1996–2025 | 30 |
| IT-Lav | EUF (2003–2020) | 2003–2020 | 18 |

## File layout

```text
examples/FLUXNET_MultiSite_8/
├── README.md
├── .gitignore
├── docs/
│   └── QC_and_DATM_decisions.md
└── scripts/
    ├── 00_upload_8_fluxnet_to_iridis.sh      # run in WSL, only if re-uploading sources
    ├── 00_sync_iridis_scripts.sh              # run in WSL to copy actual working scripts from IRIDIS
    ├── 01_extract_8_fluxnet_nested.py         # run on IRIDIS after upload
    ├── 02_make_8_surfaces.sh                   # copied from ~/make_8_surfaces.sh on IRIDIS
    ├── 03_prepare_eight_site_forcing_v5.py    # copied from actual IRIDIS version
    ├── 07_make_eight_site_datm_timevarying_zbot.py
    ├── 09_FRHes_manual_v1_rebuild_eight_datm.py
    ├── 08_audit_eight_site_datm_surface.py
    └── [additional optional QC and review scripts]
```

## Workflow: where commands are run

### 00 — Workstation WSL to IRIDIS6 (source data, one-time)

Source ZIPs expected in `D:\Fluxes_Tower_Experiment\ICOS` (`/mnt/d/Fluxes_Tower_Experiment/ICOS` in WSL). The script uploads to `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<site>/forcing/packages/` via SSH/rsync. Run **only if the source packages need uploading again**:

```bash
bash examples/FLUXNET_MultiSite_8/scripts/00_upload_8_fluxnet_to_iridis.sh
```

On IRIDIS, unpack nested archives once:

```bash
python scripts/01_extract_8_fluxnet_nested.py
```

The original package releases remain outside Git. Both scripts include eight hard-coded release names and IRIDIS directory defaults. Check them if datasets change.

### 01–03 — Surface and candidate meteorological forcing (IRIDIS6)

On IRIDIS, with `conda activate clm_fates_env` and this example available in a clone:

```bash
bash scripts/02_make_8_surfaces.sh
python scripts/03a_check_8_site_coverage.py                # when present
python scripts/03_prepare_eight_site_forcing_v5.py
python scripts/04_audit_eight_site_qc_v5.py                # when present
```

These stages have already been completed for the recorded October 2026 experiment. **Do not re-run them into existing production directories without verifying the current script and backup/versioning behaviour.** QC v5 is a candidate, provenance-preserving research screen: short interpolation, station-level ERA5_HH gap fills, RH repairs, and manual-review registers. It must not silently overwrite original FLUXMET measurements.

### 04–06 — Human revision, time-varying BIF ZBOT, and DATM (IRIDIS6)

- `07_make_eight_site_datm_timevarying_zbot.py` is the generic eight-site candidate writer, used before the FR-Hes revision.
- `09_FRHes_manual_v1_rebuild_eight_datm.py` is the **actual recorded final revision**. It produces `FR-Hes/forcing/processed_v5_manual_v1/`, preserves prior FR-Hes NetCDF files in a backup folder, creates the corresponding version-aware DATM generator and verifies 188/188 files. It expects the base script at `~/07_make_eight_site_datm_timevarying_zbot.py`, so copy these scripts back into IRIDIS home when reproducing from a Git clone.
- `08_audit_eight_site_datm_surface.py` applies the six-site NetCDF, surface, PFT and height audit standards. It records review notes; `STRUCTURE_OK_REVIEW` is normal when scientific caveats remain.

The **final FR-Hes DATM uses the `processed_v5_manual_v1` forcing**, not the original `processed_v5` CSV. Running the generic 07 writer by itself against the final FR-Hes NetCDF files will detect a source SHA mismatch: use the version-aware generator produced by 09, or explicitly configure the revised forcing source.

Example command to independently repeat read-only audit (only after NetCDFs are present):

```bash
python ~/08_audit_eight_site_datm_surface.py
```

### Scientific review summary

See [`docs/QC_and_DATM_decisions.md`](docs/QC_and_DATM_decisions.md) for each human decision, ERA provenance, FR-Hes change ledger, surface/PFT warnings, and the retained unverified high precipitation of DE-Hzd.

## Reproducibility scope

- Periods are intentionally site-specific, with 2026 excluded where incomplete/future.
- All candidate annual NetCDFs have 17,520 records and use `NO_LEAP`, half-hour forcing (`ATM_NCPL=48` when configuring a model case).
- Model startup/spin-up, CO2 assignment, landunit/FATES PFT suitability, meteorological validation against independent stations, and forest carbon convergence are **not yet certified by this example**.
- Avoid uploading logs, local paths containing tokens, original data, output CSVs or `.nc` files to GitHub. The `.gitignore` excludes the principal raw and generated file types.

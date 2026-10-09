# DE-Hai (Hainich): ICOS / FLUXNET acquisition

This is a **download-only first step**, designed to match the existing `examples/ICOS_ES-LJu/` workflow. It does **not** yet prepare, gap-fill, or validate CLM-FATES forcing.

## Source product

- Station: `DE-Hai` (51.079212 N, 10.452168 E; 438.7 m elevation)
- Period: **2000–2025**
- Primary product: `ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1.zip`
- ICOS PID: [`11676/VsQ1NTQTcEO5zRyfZjrBtkQa`](https://meta.icos-cp.eu/objects/VsQ1NTQTcEO5zRyfZjrBtkQa)
- SHA-256: `56c4353534137043b9cd1c9f663ac1b6441a3b533fbab163c1f3ab4a272abb50`
- Data terms: ICOS CCBY4 Data Licence (see source PID); download requires an ICOS user profile with data licence accepted.

We use the full FLUXNET archive instead of the separate `FLUXES_L2.zip` so that the input format follows the existing ES-LJu FLUXNET/ONEFlux workflow, including its meteorological and gap-filling files. **Do not assume that every forcing variable is complete or that the ES-LJu QC thresholds apply to DE-Hai.**

## Run on an IRIDIS6 login node

Transfer the scripts to IRIDIS (or clone/pull this repository there). From `examples/ICOS_DE-Hai`:

```bash
bash scripts/01_download_icos_data.sh --dry-run
bash scripts/01_download_icos_data.sh
```

When asked, paste a fresh `cpauthToken` from the [ICOS Carbon Portal account profile](https://www.icos-cp.eu/data-services/data-portal/how-to-use). Input is hidden. Do not commit or share the token. Run downloads on a **login node**, not a compute node.

## IRIDIS layout

```text
/iridisfs/scratch/ly3n24/CLM_FATES/
├── sites/MY_EC_SITE/DE-Hai/
│   ├── forcing/
│   │   ├── raw/
│   │   │   ├── ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1.zip
│   │   │   ├── ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1/  # extracted contents (may have nested source folders)
│   │   │   ├── ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1_metadata.json
│   │   │   └── ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1_SOURCE.txt
│   │   ├── processed/                              # later
│   │   └── datm/                                   # later
│   └── obs/                                        # later
└── cases/DE-Hai_FATES_1PT/                         # later
```

The scripts verify the **published SHA-256** before unzipping and will **not overwrite** a previously downloaded archive with the wrong hash. A valid existing archive is reused.

## Next development step

Once downloaded, inspect the actual CSV names/columns/measurement heights and missing-value rates. Then adapt `03_prepare_forcing.py`, `04_validate_forcing.py`, and `05_make_datm.py` from `examples/ICOS_ES-LJu/` for DE-Hai rather than blindly copying ES-LJu's site-specific QC. Forcing resolution is expected to be half-hourly (`ATM_NCPL=48`), but confirm with the source data before model setup. Determine `ZBOT` from DE-Hai variable metadata, not canopy height.

Only scripts and documentation belong in GitHub; the raw ZIP, unzipped CSV, processed forcing, NetCDF and history data remain on IRIDIS Scratch.

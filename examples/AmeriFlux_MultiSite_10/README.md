# AmeriFlux MultiSite 10 — Batch 01

**Stage: preparation only (21 October 2026).** These scripts reproduce the first two source-handling steps used in [FLUXNET MultiSite 13](../FLUXNET_MultiSite_13/scripts/). No upload, extraction, meteorological QC, DATM, land-surface preparation, CIME case creation, spin-up, or Slurm submission has been executed by this GitHub change.

## The ten source releases

| Site | Original release archive stem | Labelled release window |
| --- | --- | --- |
| BR-Ma2 | `AMF_BR-Ma2_FLUXNET_1999-2016_v1.3_r1` | 1999–2016 |
| CA-Ca3 | `AMF_CA-Ca3_FLUXNET_2001-2024_v1.3_r1` | 2001–2024 |
| CA-Cbo | `AMF_CA-Cbo_FLUXNET_1996-2024_v1.3_r1` | 1996–2024 |
| CA-LP1 | `AMF_CA-LP1_FLUXNET_2007-2024_v1.3_r1` | 2007–2024 |
| CA-Man | `AMF_CA-Man_FLUXNET_1994-2008_v1.3_r1` | 1994–2008 |
| CA-TP1 | `AMF_CA-TP1_FLUXNET_2002-2023_v1.3_r1` | 2002–2023 |
| CA-TP3 | `AMF_CA-TP3_FLUXNET_2002-2023_v1.3_r1` | 2002–2023 |
| CA-TP4 | `AMF_CA-TP4_FLUXNET_2002-2023_v1.3_r1` | 2002–2023 |
| US-Aud | `AMF_US-Aud_FLUXNET_2002-2024_v1.3_r1` | 2002–2024 |
| US-Bar | `AMF_US-Bar_FLUXNET_2004-2023_v1.3_r1` | 2004–2023 |

All exact names are in [sites.tsv](sites.tsv). The release-window labels are not independently checked data coverage; inspect BIF, meteorology, and missing years at the next stage. Do not assume a model-year spin-up target or a meteorological repeat cycle yet.

## Stage 00 — upload source archives (LOCAL WSL / VS Code)

The example assumes the ZIPs are in `/mnt/d/Fluxes_Tower_Experiment/AmeriFlux/`; override `LOCAL_ROOT` for your real folder. Files can be `<package>.zip` or extracted `<package>/` folders. All ten are preflight-checked before anything is uploaded. Existing remote ZIP files are not overwritten, and the transfer is checksum-verified.

```bash
# Execute on your LOCAL WSL terminal, not inside IRIDIS Remote SSH.
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only origin main
LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/AmeriFlux' \
  bash examples/AmeriFlux_MultiSite_10/scripts/stage00/00_upload_ameriflux_10.sh
```

Destination:
`/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/packages/<PACKAGE>.zip`.

If the remote file has the same name but differs from the local ZIP, the transfer stops at SHA256 verification; inspect manually rather than overwriting.

## Stage 01 — recursive extraction (IRIDIS6 / VS Code Remote SSH)

```bash
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only origin main
python3 examples/AmeriFlux_MultiSite_10/scripts/stage01/01_extract_ameriflux_10.py
```

The script looks in each site-specific `forcing/packages/` and `MY_EC_SITE/_incoming_zips/`. If ZIP files already exist somewhere else on IRIDIS, **skip Stage 00** and use:

```bash
python3 examples/AmeriFlux_MultiSite_10/scripts/stage01/01_extract_ameriflux_10.py \
  --incoming-dir /path/to/your/ameriflux_zip_folder
```

Single-site extraction and a later read-only validation are also supported:

```bash
python3 examples/AmeriFlux_MultiSite_10/scripts/stage01/01_extract_ameriflux_10.py --sites CA-Man US-Bar
python3 examples/AmeriFlux_MultiSite_10/scripts/stage01/01_extract_ameriflux_10.py --audit-only
```

CSV output: `MY_EC_SITE/<SITE>/forcing/raw/<PACKAGE>/*.csv`. The script expands nested ZIPs, validates size/CRC32, skips byte-identical existing CSVs, rejects conflicting existing CSVs, and checks BIF + FLUXMET_HH existence. Missing ERA5_HH is only a **warning**. All source ZIPs remain intact. A JSON inventory stays on IRIDIS at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage01_extraction_summary.json`

No model files are deleted or relocated. The next work item is a **scientific source audit**: actual temporal coverage, variable headers/QC, meteorological gaps, BIF tower-height metadata, land cover and FATES PFT decisions, followed by forcing/DATM development. `CA-Man`'s 1994–2008 label is relatively short and warrants specific coverage review.


## Stage 02: AmeriFlux BIF geolocation preflight (read-only)

Stage 01 extraction and structural inventory succeeded at all 10 sites according to operator-provided IRIDIS output (16 CSV files per site, including one BIF, one FLUXMET_HH and one ERA5_HH). This **does not validate meteorological forcing, PFT or temporal coverage**. Before following the older ICOS surface-generation example, inspect every station's BIF coordinates using the [Stage 02 read-only preflight](scripts/stage02/02_check_10_bif_coordinates.py).

```bash
BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10"
REPO="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
mkdir -p "$BASE/scripts/stage02"
curl -fL "$REPO/examples/AmeriFlux_MultiSite_10/scripts/stage02/02_check_10_bif_coordinates.py" -o "$BASE/scripts/stage02/02_check_10_bif_coordinates.py"
curl -fL "$REPO/examples/AmeriFlux_MultiSite_10/sites.tsv" -o "$BASE/sites.tsv"
python3 "$BASE/scripts/stage02/02_check_10_bif_coordinates.py" | tee "$HOME/AmeriFlux_10_stage02_bif.log"
```

The script does not create CTSM surfaces, modify ZIP/CSV input, or submit any Slurm jobs. It verifies that each release's BIF supplies one valid latitude/longitude pair, prints available IGBP labels, and highlights ambiguous metadata. Surface files should only be generated after coordinate and vegetation-representation review. CTSM year-2000 surface gridding does not establish EC footprint representativeness.

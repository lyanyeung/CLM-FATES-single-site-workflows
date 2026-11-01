# JapanFlux Stage00–01 actual transfer and archive discovery — 2026-11-01

## Operator-provided IRIDIS/WSL execution

**Stage00 upload VERIFIED 11/11**. One successful `rsync` transfer per exact original release was followed by **local versus remote SHA256 equality** for every station. Original local sources were retained. **No extraction or model jobs started.** Remote host reported `login6001`.

| Site | Exact uploaded archive | ZIP bytes | Source/remote SHA256 |
|---|---|---:|---|
| JP-Api | `JPF_JP-Api_FLUXNET_2000-2022_v1.3_r2.zip` | 215989034 | `dab9de152210d4f95d88c79c7b9e67bd5ccde19fee86304bee093634f000342b` |
| JP-Fhk | `JPF_JP-Fhk_FLUXNET_2006-2023_v1.3_r1.zip` | 171116107 | `20abdd06ed23de7d599841e8ac64a21b2378a169deae6f3f891f6230e4a31667` |
| JP-Fjy | `JPF_JP-Fjy_FLUXNET_2001-2021_v1.3_r1.zip` | 205414017 | `205660bb8203bf7b16466041183ec9a1598f609727ef042ff4bceb800da949b9` |
| JP-Khw | `JPF_JP-Khw_FLUXNET_2000-2021_v1.3_r1.zip` | 87837151 | `712ab4695704a695c28056eb0cfae0697af8a673228407dbc856088ad83bac79` |
| JP-Spp | `JPF_JP-Spp_FLUXNET_2000-2018_v1.3_r1.zip` | 189233993 | `6941f9bf4c6f7f2e80c9a7c991fde1b2c92bc3d7a111321ae50bd7d370d35aaf` |
| JP-Tak | `JPF_JP-Tak_FLUXNET_1998-2021_v1.3_r1.zip` | 177703265 | `cf1da393c026deb35dcc9b328bf5c7ae7ca9eea22dbbf8a095907e06373dc151` |
| JP-Tef | `JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1.zip` | 219153789 | `315c825b64669aa03daff1d969f58a0a1cf3b574c43400ea1f84588df7f6d684` |
| JP-Tmd | `JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1.zip` | 170842080 | `3ef287018725cb2b5b4c78130804febbe022dad66415807e70f628b756a13479` |
| JP-Yms | `JPF_JP-Yms_FLUXNET_2000-2023_v1.3_r1.zip` | 157790263 | `6bda3beb4fd9b580ef036e4b50f9c3162ca17b82b2b28466820e665bdedbf6f7` |
| JP-Tom | `A20241210-015v200.zip` | 182651607 | `ea3e5a3583b1defc722d44ee8343acdca6d902eb7e688268d44b2d47efcd193e` |
| JP-Tgf | `A20241210-013_2.00_selected.zip` | 1018861232 | `d0476fff16f6bce8f53a0d640668dc28d0df7e6fbfda86565a26b247f267c204` |

Paths match `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<site>/forcing/packages/<original-release>.zip`, but no filesystem inspection beyond the uploader's sha check is represented.

## Stage01 actual read-only ZIP inventory: 11/11 opened

Operator supplied terminal output of `01_inspect_japanflux_packages.py`. Each station was `INVENTORIED zip`:

| Sites | Outer ZIP file member count | Detected name substrings |
|---|---:|---|
| JP-Api, JP-Fhk, JP-Fjy, JP-Khw, JP-Spp, JP-Tak, JP-Tef, JP-Tmd, JP-Yms | 3 each | **none** of Stage01's conventional FLUXMET/ERA/BIF substrings |
| JP-Tom | 29 | `ERA5_HH` |
| JP-Tgf | 27 | `ERA5_HH` |

This is a **structural inventory only**, not a CRC pass (unless separately run), not a statement about file types, and certainly not proof that nine JPF archives lack usable meteorology. The generic-name detector did not match the **outer ZIP member names**. There could be nested archives or distinct naming systems. The two exceptional packages must remain source-schema-specific.

**Next immediate read-only action:** run `scripts/stage02/02_print_outer_members_and_headers_READONLY.py` to print each actual outer member name, extension, uncompressed length, signature and bounded text sample. If a member is a nested archive, stop and select an appropriate bounded nested inspection strategy. Do not write DATM or cases before source cadence, clock, variables, QC and scientific provenance audit.

**Not yet verified:** ZIP member CRC, true temporal coverage, data-table schema, timestamp convention (JST/UTC), QC, original flux/meteorological columns, site PFT/soil/ZBOT, DATM fitness, any Slurm or model run. No original tower release is committed to GitHub.

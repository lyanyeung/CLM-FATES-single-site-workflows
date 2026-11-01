# JapanFlux Stage02 — actual outer ZIP inspection (operator log, 2026-11-01)

## Result and source limitations

**ACTUAL OUTER ZIP INSPECTION 11/11, with no extraction or model submission.** This result is grounded in the operator's `20261101-043628` IRIDIS terminal output. The output printed ZIP member name, uncompressed size, first-line snippets and signature classifications, **not** full contents/CRC validation or whole-record data QC.

| Cohort | Site | Outer member count | Actual structural evidence |
|---|---|---:|---|
| Nine JPF releases | JP-Api, JP-Fhk, JP-Fjy, JP-Khw, JP-Spp, JP-Tak, JP-Tef, JP-Tmd, JP-Yms | 3 each | Outer members are a ZIP with **exact same package filename as the outer ZIP**, `!TOC.csv`, `!LICENCE.pdf`; the inner ZIP signature is verified from its first bytes but its content **has not been inspected** |
| JapanFLUX special | JP-Tom | 29 | Direct `COREVARS`, `ALLVARS`, `BADM` and ERA5 text files; no inner `*.zip` required for meteorology |
| JapanFLUX special | JP-Tgf | 27 | Direct `A20241210-013/DATA/{COREVARS,ALLVARS,BADM}`, plus PDF; direct half-hourly tower and ERA5 text files |

### Nine standard-name JPF data packages: exact observation

All nine outer ZIPs contain exactly these three **kinds of members**:

1. `JPF_JP-<site>_FLUXNET_<release>.zip` — `NESTED_ZIP_SIGNATURE`; the inner archive's actual file list and schemas remain unknown.
2. `!TOC.csv`, first line `Included,File name,PID,Landing page,Omission reason (if any)`.
3. `!LICENCE.pdf` (binary PDF).

This explains why Stage01's generic tag detector found no `FLUXMET_HH`/BIF names: the real data files are **one ZIP layer deeper**. This finding does *not* indicate that these nine station archives are empty or have no forcing variables. Preserve the original two-layer hierarchy and do not unzip onto Scratch during the preliminary metadata audit.

### JP-Tom direct source

- `COREVARS/FLX_JP-Tom_JapanFLUX2024_COREVARS_HR_1999-2003_1-4.csv`, hourly source.
- `COREVARS/FLX_JP-Tom_JapanFLUX2024_COREVARS_HH_2003-2014_1-4.csv`, half-hourly source. **2003 is in both release labels**, so do not automatically merge without real timestamp and overlap inspection.
- `ALLVARS/FLX_JP-Tom_JapanFLUX2024_ERA5_HH_1990-2024_1-4.csv`, independent ERA5 companion; other ALLVARS files and six BADM `*.xlsx` members.
- Observed `COREVARS_HR` / `COREVARS_HH` headers include `TIMESTAMP_START,TIMESTAMP_END,TA_F,TA_F_QC,SW_IN_F,SW_IN_F_QC,LW_IN_F,LW_IN_F_QC,RH_F,RH_F_QC,VPD_F,VPD_F_QC,PA_F,PA_F_QC,P_F,P_F_QC,WS_F,WS_F_QC`.
- ERA5_HH header: `TIMESTAMP_START,TIMESTAMP_END,TA_ERA5,RH_ERA5,VPD_ERA5,e_ERA5,e_sat_ERA5,WS_ERA5,PA_ERA5,SW_ERA5,LW_ERA5,P_ERA5`.

### JP-Tgf direct source

- `A20241210-013/DATA/COREVARS/FLX_JP-Tgf_JapanFLUX2024_COREVARS_HH_2002-2023_1-4.csv`.
- `A20241210-013/DATA/ALLVARS/FLX_JP-Tgf_JapanFLUX2024_ALLVARS_HH_2002-2023_1-4.csv`.
- `A20241210-013/DATA/ALLVARS/FLX_JP-Tgf_JapanFLUX2024_ERA5_HH_1990-2024_1-4.csv`; six BADM `*.xlsx` files and original PDF.
- `COREVARS_HH` header includes `TA_F,TA_F_QC,SW_IN_F,SW_IN_F_QC,LW_IN_F,LW_IN_F_QC,RH_F,RH_F_QC,VPD_F,VPD_F_QC,PA_F,PA_F_QC,P_F,P_F_QC,WS_F,WS_F_QC`.
- The `ALLVARS_HH` file has multiple channel indices (`TA_1_3_1`, `TA_1_2_1`, `TA_1_1_1`, etc.); no assumption about which individual sensor is model-representative is justified yet.

## Next read-only Stage03 step

Use [`03_inspect_nested_release_members_READONLY.py`](../scripts/stage03/03_inspect_nested_release_members_READONLY.py), which opens the nine nested ZIP members **in bounded process memory**, not on disk, and also inventories two direct-source packages. For each file it reports a canonical path, uncompressed byte count, safe/unsafe name, and bounded CSV header/initial timestamp preview. There is a default **256 MiB per-nested-archive cap** and optional `--site` to pilot one site. The inspection script underwent a Python syntax check and a synthetic 11-site nested/direct ZIP structural test **outside IRIDIS6**, but **it has not yet been executed against the real 11 remote site packages**.

Success of Stage03 will show only an inner-file inventory, not whole-record QC, verified measurement years, origin timezone/JST-vs-UTC, units, sensor heights, precipitation, humidity plausibility, ERA5 alignment, PFT, surface, DATM approval, or spin-up readiness.

### Operator command

```bash
set -euo pipefail
D="$HOME/japanflux_stage03"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/JapanFlux_MultiSite_11"
mkdir -p "$D"
curl -fLsS "$BASE/sites.tsv" -o "$D/sites.tsv"
curl -fLsS "$BASE/scripts/stage03/03_inspect_nested_release_members_READONLY.py" -o "$D/inspect.py"
python3 -B -m py_compile "$D/inspect.py"
python3 -B "$D/inspect.py" --manifest "$D/sites.tsv" --site JP-Api > "$D/JP-Api_pilot.json"
python3 -B "$D/inspect.py" --manifest "$D/sites.tsv" > "$D/all11_inventory.json"
```

**Scientific policy:** do not promote any complete ERA5 dataset as if it were observed tower forcing. Do not auto-merge 2003 hourly and half-hourly JP-Tom data. No original file editing or Slurm submission.

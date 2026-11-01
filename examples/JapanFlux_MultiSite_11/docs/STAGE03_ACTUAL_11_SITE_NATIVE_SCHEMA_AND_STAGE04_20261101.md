# JapanFlux Stage03 — actual inner ZIP and native schema audit (2026-11-01)

**Source:** operator-reported output of `03_inspect_nested_release_members_READONLY.py`, finishing `PASS: 11 / 11`. This establishes read-only member/header access to all 11 uploaded original releases, **not** full-record integrity or scientific QC. No extraction, source editing, forcing materialization or Slurm operation was reported.

## Main science-source inventory

| Site | Source structure | Main native source table | Columns | Native release-label years | ERA5 HH filename-label period |
| --- | --- | --- | ---: | --- | --- |
| JP-Api | Double ZIP: 18 inner members | FLUXMET_HH | 220 | 2000–2022 | 1981–2025 |
| JP-Fhk | Double ZIP: 18 inner members | FLUXMET_HH | 237 | 2006–2023 | 1981–2025 |
| JP-Fjy | Double ZIP: 18 inner members | FLUXMET_HH | 233 | 2001–2021 | 1981–2025 |
| JP-Khw | Double ZIP: 18 inner members | FLUXMET_HH | 190 | 2000–2021 | 1981–2025 |
| JP-Spp | Double ZIP: 18 inner members | FLUXMET_HH | 239 | 2000–2018 | 1981–2025 |
| JP-Tak | Double ZIP: 18 inner members | FLUXMET_HH | 187 | 1998–2021 | 1981–2025 |
| JP-Tef | Double ZIP: 18 inner members | FLUXMET_HH | 240 | 2001–2023 | 1981–2024 |
| JP-Tmd | Double ZIP: 18 inner members | FLUXMET_HH | 223 | 2005–2023 | 1981–2024 |
| JP-Yms | Double ZIP: 18 inner members | FLUXMET_HH | 178 | 2000–2023 | 1981–2025 |
| JP-Tom | Direct ZIP: 29 members | COREVARS_HR (50 columns) + COREVARS_HH (50 columns) | 50 / 50 | HR 1999–2003; HH 2003–2014 | 1990–2024 |
| JP-Tgf | Direct ZIP: 27 members | COREVARS_HH | 62 | 2002–2023 | 1990–2024 |

**Important:** all displayed periods are **product filename labels** and not proofs of actual continuous measured coverage, correct timestamps, or usable forcing.

For the nine JPF releases, each inner ZIP has 18 members: five FLUXMET resolution variants (`HH,DD,WW,MM,YY`); five corresponding ERA5 variants; `BIF`; five `BIFVARINFO` variants; `README.txt`; and `DATA_POLICY_LICENSE_AND_INSTRUCTIONS.txt`. The exact names share each site's original package basename and original version. This resolves the prior two-layer packaging question without extracting original ZIPs.

### Observed native meteorology source columns

Nine JPF `FLUXMET_HH` tables each contain `TIMESTAMP_START,TIMESTAMP_END,TA_F,TA_F_QC,SW_IN_F,SW_IN_F_QC,LW_IN_F,LW_IN_F_QC,VPD_F,VPD_F_QC` among many fields. The Stage03 printed `MET` arrays were **truncated to 25 columns in the operator's terminal summary**; hence absence of a field from that printed subset cannot be interpreted as missing from the full schema. JPF companion `ERA5_HH` tables explicitly list `TA_ERA,SW_IN_ERA,LW_IN_ERA,VPD_ERA,PA_ERA,P_ERA,WS_ERA`. Do not label all `_F` values as direct tower measurements without the actual source and quality descriptors.

JP-Tom has two separate native cadences: `COREVARS_HR_1999-2003` and `COREVARS_HH_2003-2014`. Both are 50-column tables featuring `TA_F,RH_F,VPD_F,PA_F,SW_IN_F,LW_IN_F,P_F,WS_F` and matching `_QC` fields. The year **2003 occurs in both file labels** and requires actual timestamp overlap verification before any splice. JP-Tgf `COREVARS_HH_2002-2023` has 62 columns with the same key meteorological fields, plus soil-related quantities. Its `ALLVARS_HH` has multiple indexed tower channels, e.g. `TA_1_3_1,TA_1_2_1,TA_1_1_1`; the correct tower sensor height and instrument selection require BADM provenance, not automatic assignment.

Both direct JapanFLUX releases contain `ERA5_HH_1990-2024` files and a separately named `ERA5_FILL` product. **Existing gap-filled products should be audited as processed sources, not automatically treated as original observations or scientific approved forcing.** BIF/BADM site metadata still need content review.

## Exact acceptance boundary

- **Passed:** 11/11 original archive member discovery and sample header reading; nine nested archives confirmed; native source-file paths identified.
- **Not yet passed:** complete full-record read/CRC; time intervals and coverage; UTC/JST interpretation; `_QC` semantic conventions; sources for gaps; full-column presence; measurement and reanalysis units; pressure/precipitation conversions; humidity/RH/VPD and physical-range QC; measurement-height metadata; PFT/soil; full DATM, CIME or AD400.
- **Next:** [Stage04 streaming read-only native timestamp and source QC audit](../scripts/stage04/04_audit_native_timestamps_and_source_QC_READONLY.py). This reads the full `FLUXMET_HH` and `COREVARS_HR/HH` tables without writing source data. It reports candidate anomalies and actual source QC labels **without changing or approving values**, and treats Tom's HR/HH sources separately.

## IRIDIS6 Stage04 command

```bash
set -euo pipefail
D="$HOME/japanflux_stage04"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/JapanFlux_MultiSite_11"
mkdir -p "$D"
curl -fLsS "$BASE/sites.tsv" -o "$D/sites.tsv"
curl -fLsS "$BASE/scripts/stage04/04_audit_native_timestamps_and_source_QC_READONLY.py" -o "$D/audit.py"
python3 -B "$D/audit.py" --manifest "$D/sites.tsv" --site JP-Api --max-rows 20000 > "$D/JP-Api_pilot_20k.json"
python3 -B "$D/audit.py" --manifest "$D/sites.tsv" > "$D/full11_raw_source_qc.json"
```

The pilot is deliberately **partial**, and the full command is deliberately **read-only**. Outputs are written to the user's HOME audit folder via shell redirection, not to original tower packages or CIME cases. A `screened=11/11` outcome indicates the source streams could be scanned; it does not mean there were zero anomalies or a scientific release.

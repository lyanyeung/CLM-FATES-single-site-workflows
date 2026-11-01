# OzFlux MultiSite 09 — source-preserving IRIDIS6 transfer and L6 scientific intake

**Status (2026-11-01): SOURCE AUDITS EXECUTED THROUGH STAGE11; STAGE12 STANDALONE PROVISIONAL DATM PREFLIGHT PUBLISHED, EXECUTION PENDING.** This cohort contains **9 station IDs and 10 original NetCDF files**. The operator executed Stages01–08 on IRIDIS6: Stage01–03 and Stage04 v2 inspected 10/10 original source files, Stage05 inspected 18 donor comparisons, Stage06A investigated 3 target sources, Stage07 classified 169 source-file calendar years (67 structural candidates; 102 REVIEW/HOLD), and Stage08 confirmed those annual classifications and the contiguous-year blocks; Stage09 assessed 2 first-cohort sites and found stronger NT-local-time solar consistency, plus 885 AU-DaS saturation alarms requiring scientific review. Stage10 confirmed all 19 candidate UTC-center year boundaries and reproduced 885 SH alarms (207 episodes), all native SH_QCFlag=0. Stage11 confirmed 6/6 ASM provisional UTC NOLEAP year views and found 40 extreme DaS SH/qsat alarms >=1.5, while source RH/VPD are available for investigation. Original NetCDFs were not modified. **No source science approval, DATM forcing conversion, CIME case, or Slurm model submission has occurred in this new cohort.**

This is a *new cohort* parallel to [JapanFlux MultiSite 11](../JapanFlux_MultiSite_11/), [AmeriFlux Batch03](../AmeriFlux_MultiSite_10_Batch03/) and the existing, previously run [OzFlux AU-How](../OzFlux_AU-How/). Keep scientific settings and decisions independent of those campaigns.

## 1. Exact source file manifest

Root on Windows: `D:\Fluxes_Tower_Experiment\Ozflux`; root in a typical Windows WSL shell: `/mnt/d/Fluxes_Tower_Experiment/Ozflux`.

The machine-readable `sites.tsv` stores the exact original basenames; do **not** rename filenames to match site codes or assume every NetCDF uses the same internal variable names.

| Site | Exact Windows source path |
| --- | --- |
| AU-ASM | `D:\Fluxes_Tower_Experiment\Ozflux\AU-ASM\AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc` |
| AU-ASM | `D:\Fluxes_Tower_Experiment\Ozflux\AU-ASM\AliceSpringsMulga2_20240821T0700_to_20260423T0000_L6.nc` |
| AU-Cow | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Cow\CowBay_20090101T0900_to_20260423T0000_L6.nc` |
| AU-Cpr | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Cpr\Calperum_L6.nc` |
| AU-DaS | `D:\Fluxes_Tower_Experiment\Ozflux\AU-DaS\DalyUncleared_20080101T0000_to_20260423T0000_L6.nc` |
| AU-Dry | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Dry\DryRiver_L6.nc` |
| AU-Gin | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Gin\Gingin_L6.nc` |
| AU-How | `D:\Fluxes_Tower_Experiment\Ozflux\AU-How\HowardSprings_L6.nc` |
| AU-Stp | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Stp\SturtPlains_L6.nc` |
| AU-Tum | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Tum\Tumbarumba1_L6.nc` |

**AU-ASM special case:** Mulga1 and Mulga2 are **two separate files and apparent acquisition periods**. The filenames suggest a discontinuity between March 2023 and August 2024, but actual chronology, timezone, sampling conventions, station geometry, instrument changes and eligibility for any later harmonisation must be verified from the original metadata. **Never concatenate or fill this gap automatically.**

File timestamps are release-label hints, not scientifically verified continuous observations. Other sites may contain multiple time periods, gaps or different measurement/derived-variable schemas despite the common L6 extension.

## 2. Stage00: batch transfer from local Windows PC (run in WSL/Ubuntu)

Run the following in **your own PC's Ubuntu/WSL**, not an IRIDIS login terminal. Requires `git`, `ssh`, `rsync`, `sha256sum`, `awk`, `mktemp`, and `head`.

```bash
# Keep the interactive WSL shell open if a preflight command reports an error.
ls -ld /mnt/d/Fluxes_Tower_Experiment/Ozflux
command -v git ssh rsync sha256sum

if [[ -d "$HOME/CLM-FATES-OzFlux-upload/.git" ]]; then
  git -C "$HOME/CLM-FATES-OzFlux-upload" pull --ff-only
else
  git clone --depth 1 https://github.com/lyanyeung/CLM-FATES-single-site-workflows.git \
    "$HOME/CLM-FATES-OzFlux-upload"
fi

UPLOADER="$HOME/CLM-FATES-OzFlux-upload/examples/OzFlux_MultiSite_09/scripts/stage00/00_upload_ozflux.sh"

# First: local complete 10-file preflight, checksum only; no network transfer.
bash "$UPLOADER" --preflight-only

# Then: transfer originals and independently verify IRIDIS-side SHA256.
bash "$UPLOADER" 2>&1 | tee "$HOME/ozflux_stage00_upload.log"
```

Default destination for every source file:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<AU-SITE>/forcing/raw/<ORIGINAL_FILENAME>.nc
```

For example, the two AU-ASM sources are stored *separately*:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/AU-ASM/forcing/raw/AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/AU-ASM/forcing/raw/AliceSpringsMulga2_20240821T0700_to_20260423T0000_L6.nc
```

The script internally uses `set -euo pipefail`; do not enable `set -e` in your interactive WSL terminal. If a source preflight fails, the script stops but WSL stays open. The uploader checks **all 10 local files before connecting**, uses a single SSH authentication for the batch, never rewrites an existing destination, permits rerun after an interrupted transfer, and verifies every original file against the IRIDIS-side SHA256. If an existing file (particularly AU-How) has a different hash, transfer **stops** and preserves it for manual review. Source files are never deleted or moved.

Expected final line:

```text
UPLOAD VERIFIED: 10/10 NetCDF files across 9 OzFlux sites. No model jobs submitted.
```

This line confirms a byte-for-byte transfer, **not scientific validation**. Do not claim completion before seeing it in the actual WSL log.

## 3. Stage01: read-only NetCDF inventory on IRIDIS6

**Critical Python import safeguard:** Never download this inspector as `inspect.py`, because `inspect` is a Python standard-library module imported by `netCDF4`. A previous Stage01 command did that and caused `AttributeError: module 'inspect' has no attribute 'cleandoc'` for every site *before any NetCDF data were inspected*. This was a script-name error, not source corruption. Existing generated `$HOME/ozflux_stage01/inspect.py` must be moved aside before rerunning. The source-controlled script is named `01_inspect_ozflux_nc.py`.

After Stage00 has independently verified all ten file SHA256 hashes, log into **IRIDIS6**. Run the commands below **without enabling `set -e` in the interactive shell**:

```bash
conda activate clm_fates_env
DIR="$HOME/ozflux_stage01"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/OzFlux_MultiSite_09"
mkdir -p "$DIR/old"
# Move only the previously misnamed inspector; leave all source NetCDF untouched.
if [[ -f "$DIR/inspect.py" ]]; then
  mv -n "$DIR/inspect.py" "$DIR/old/inspect.py"
fi
curl -fLsS "$BASE/sites.tsv" -o "$DIR/sites.tsv"
curl -fLsS "$BASE/scripts/stage01/01_inspect_ozflux_nc.py" -o "$DIR/ozflux_nc_metadata.py"
# Check both downloads succeeded before running the next commands.
python3 -c 'import inspect, netCDF4; print("inspect from", inspect.__file__); print("netCDF4", netCDF4.__version__)'
python3 -B "$DIR/ozflux_nc_metadata.py" --manifest "$DIR/sites.tsv" > "$DIR/inventory.json"
python3 - "$DIR/inventory.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
for s in x["files"]:
    print(s["site"], s["filename"], s["status"],
          "vars="+str(s.get("variable_count","?")),
          "time="+",".join(v["name"] for v in s.get("time_coordinates",[])))
    if "error" in s: print("  ERROR:", s["error"])
print("INVENTORIED", x["inventoried_count"], "/10")
PY
```

If `$DIR/old/inspect.py` already exists, manually choose an alternative name before moving the new one; do not overwrite previous logs or scripts. The Python `inspect.__file__` shown in the import test must point to the system/conda Python standard library, **not** to `$DIR/inspect.py`. Ignore a stale `__pycache__` subdirectory after the source has been moved.

This inspector reads original NetCDF headers, attributes and up to three scalar time samples per time coordinate. It does **not** modify site data, convert timezone, concatenate periods, produce forcing or submit jobs.

The published [OzFlux AU-How](../OzFlux_AU-How/) case is an **existing Howard Springs example**, not a generic permission to apply its 2003–2025, 23 m, zero-gap, 30-minute, NOLEAP, or DATM logic to every new site. In particular, its `05_make_datm.py` removes earlier matching output files and must **not** be executed on unreviewed source locations. No independently validated AU-Tum example currently exists under this repository's `examples/` tree.

Stage01 success requires `INVENTORIED 10 /10`. A successful metadata read alone does not approve meteorological physics or any forcing gap-filling decision.

## 3a. Stage02: source-time and meteorological/QC audit (read-only)

Stage01 was verified by the operator: **10/10 source files INVENTORIED**. The first AU-Tum interval was **60 minutes**, whereas all other file first steps were **30 minutes**; first-step cadence is not sufficient to establish complete-record continuity, so Stage02 checks full source time arrays. Original AU-ASM files remain separate. The new AU-How source coverage differs from the historical example; preserve the old successful case.

The Stage02 program is located at scripts/stage02/02_audit_ozflux_source_readonly.py and creates reports under HOME, never in the site source tree. Run on IRIDIS6:

~~~bash
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/OzFlux_MultiSite_09"
AUDIT_DIR="$HOME/ozflux_stage02_code"
OUT="$HOME/ozflux_stage02_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$AUDIT_DIR"
curl -fLsS "$BASE/sites.tsv" -o "$AUDIT_DIR/sites.tsv"
curl -fLsS "$BASE/scripts/stage02/02_audit_ozflux_source_readonly.py" \
  -o "$AUDIT_DIR/ozflux_stage02_source_audit.py"
python3 -B -m py_compile "$AUDIT_DIR/ozflux_stage02_source_audit.py"
python3 -B "$AUDIT_DIR/ozflux_stage02_source_audit.py" \
  --manifest "$AUDIT_DIR/sites.tsv" --out "$OUT" \
  2>&1 | tee "$HOME/ozflux_stage02_last.log"
echo "Stage02 report directory: $OUT"
~~~

Four outputs:
- **stage02_source_audit.json** — time metadata, all variable names, source QC candidates, physics alarms and annual counts.
- **stage02_file_summary.tsv** — full-record cadence, discontinuities and duplicate/backward time.
- **stage02_year_counts.tsv** — per-year sample counts and whole-year expected counts.
- **stage02_variable_summary.tsv** — nine candidate forcing/EC variables per source, units, missing/fill and broad physics alarms when units are recognised.

**Interpretation guardrails:** AUDITED 10/10 means the original files were read/screened, **not** physics/QC approval. Physical bounds are alerts rather than corrections. No timezone transformation, interpolation, concatenation, forcing output, changes to site files, or Slurm jobs. Never run the historical AU-How DATM writer on new unreviewed data; it deletes its matching old outputs.

## 3b. Stage03: exact gap-event and native QC flag provenance (read-only)

**Stage02 operator result (2026-11-01): 10/10 AUDITED_SOURCE_ONLY; 0 duplicate
timestamps and 0 noncanonical steps in each file.** Nine sources have 1800 s
(30 min) median steps; AU-Tum has 3600 s (1 h). Source completeness is not
scientific approval. Residual forcing gaps: ASM1 Ta 4; Cow SH 9/Ws 12; Cpr
Ta 110/Fld 17 plus one SH physical alarm; DaS Fsd 1/Fld 150; Dry Fsd 6;
Gin Fsd 1156/Ta 24/Fld 17; How Ws 345/Fsd 6; Stp ps 1233/Fsd 14; Tum
SH 658. ASM2 contains no missing values among the seven candidate meteorological
fields but its native vs filled provenance is still unverified.

A bug in the initial Stage02 physical-unit screening reported alarms=None
for Fsd/Fld units written as W/m^2. The latest Stage02 script has been
corrected; Stage03 independently screens W/m^2 radiation values. None
never meant zero anomalies.

Because these files are **OzFlux L6 processed products**, missing-free
meteorology can still have gap-filled values from other sources. Native
QC flags and their semantics must be independently investigated; the
Stage03 inspector reports source flag codes and distributions without
assuming flag 0 / nonzero are interchangeable with FLUXNET's QC tiers.
See the OzFlux data portal and PyFluxPro documentation.

Run on IRIDIS6, **do not pre-create the timestamped output directory**:

~~~bash
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage03_code"
OUT="$HOME/ozflux_stage03_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/sites.tsv" -o "$CODE/sites.tsv"
curl -fLsS "$BASE/scripts/stage03/03_source_gap_qc_events_readonly.py" \
    -o "$CODE/ozflux_stage03_gap_qc.py"
python3 -B -m py_compile "$CODE/ozflux_stage03_gap_qc.py"
python3 -B "$CODE/ozflux_stage03_gap_qc.py" \
    --manifest "$CODE/sites.tsv" --out "$OUT" \
    2>&1 | tee "$HOME/ozflux_stage03_last.log"
echo "Stage03 report directory: $OUT"
~~~

The new outputs are stage03_source_gap_qc.json (source QC candidates, code
frequency, selected longest event context), stage03_event_ledger.tsv (all
missing/physical-alarm intervals), and stage03_summary.tsv (per-file issues).

No NetCDF is edited, no data replaced or interpolated, no ERA5 injected, no
segments merged, no DATM generated, no Slurm submitted. Reports are under
HOME only. After review, create site-specific scientific decisions on
L6 flag provenance and on UTC/local timestamps, especially two
AU-ASM segments and hourly AU-Tum.

## 3c. Stage04: QCFlag codes and independent sensor candidates (read-only)

After the operator-confirmed Stage03 audit (10/10, 1,026 missing/physical-alarm episodes, science approval FALSE), Stage04 inspects original L6 files for:

- The original global FlagXX definitions and primary meteorological QCFlag code counts, with **no automatic QC tier interpretation**.
- Same-prefix candidate sensors (e.g. Fsd_1 / Fsd_7m or Ta_HMP_xx), recording whether they have finite values on target-source missing rows. Only exact same-unit candidates are numerically compared; sensor independence, station height and source-quality provenance remain manual HOLDs.
- Original Ta, SH, ps values and QCFlag context at the Calperum 2016-08-23 humidity physical alarm. No inference from a single out-of-range threshold is treated as a repair.

Run on IRIDIS6 (stage03 directory must be the operator's actual timestamped report):

~~~bash
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage04_code"
STAGE03="$HOME/ozflux_stage03_20261101T055354Z"
OUT="$HOME/ozflux_stage04_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/sites.tsv" -o "$CODE/sites.tsv"
curl -fLsS "$BASE/scripts/stage04/04_qcflag_donor_evidence_readonly.py" -o "$CODE/ozflux_stage04_qc_donors.py"
python3 -B -m py_compile "$CODE/ozflux_stage04_qc_donors.py"
python3 -B "$CODE/ozflux_stage04_qc_donors.py" --self-test
python3 -B "$CODE/ozflux_stage04_qc_donors.py" --manifest "$CODE/sites.tsv" --stage03 "$STAGE03" --out "$OUT"
echo "Stage04 evidence directory: $OUT"
~~~

Outputs: stage04_evidence.json and stage04_donor_candidates.tsv. No NetCDF mutation, candidate substitution, forcing, or model jobs. Source alternatives with plausible units are only REVIEW candidates, never direct approval.

## 3d. Stage04 v2 correction and operator evidence (2026-11-01)

Initial Stage04 execution completed 10/10 at `ozflux_stage04_20261101T055838Z`, with independent numerical donor candidates: Calperum Ta_HMP_2m 106/110; Ta_SONIC_Av 96/110 (overlapping, not additive); Gingin 10 Ta alternatives 0/24, two Fld alternatives 0/17; Howard Springs Ws_SONIC_Av 0/345. These counts indicate numeric availability only; QC code meanings and physical comparability remain unapproved.

**Stage04 v1 bug:** The candidate-filter excluded any full variable name containing substring `sd`, inadvertently excluding all `Fsd_*` names because `Fsd` contains `sd`. Thus the absence of Gingin Fsd donor rows was a false negative. Commit `d3e594c877b6d2143767525dab355da06b9272c4` fixes filtering to operate on suffix tokens only, and adds a self-test requiring Fsd_1 and Fsd_7m to survive. **Re-run the corrected Stage04 before assessing AU-Gin Fsd alternatives.** Prior result remains preserved.

Run the same Stage04 command above but set BASE to the following pinned commit, and use a *new* timestamped OUT directory:

~~~bash
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/d3e594c877b6d2143767525dab355da06b9272c4/examples/OzFlux_MultiSite_09"
~~~

Source evidence additionally identifies Calperum 2016-08-23 07:30:00 `SH=-0.0001619283944 kg/kg`, `Ta=5.131046 °C`, `ps=100.4991 kPa`, `SH_QCFlag=50`, `Ta_QCFlag=50`. Negative humidity is physically invalid. Do not translate code 50 or other QCFlag values 410/420/440 to site measurements/ERA provenance until examining each file's original FlagXX definitions.

## 3e. Stage05: PyFluxPro QC code provenance and donor comparability (READ ONLY)

Operator Stage04 v2 completed **10/10** on 2026-11-01:
- AU-Cpr Ta_HMP_2m finite in 106 of 110 missing Ta records; Ta_SONIC_Av finite in 96 of 110 (overlapping, not additive).
- AU-Gin Fsd_1 finite in 265 of 1,156 missing Fsd records (22.9%); Fsd_7m in 0. Remaining 891 without a verified in-file donor.
- AU-How Fsd_ARM finite in 1 of 6 missing Fsd; Ws_SONIC_Av 0 of 345.
- AU-Gin Ta 10 alternatives all 0/24; Fld_1 and Fld_7m both 0/17.

**Authoritative PyFluxPro codebook provenance**:
- OzFlux/PyFluxPro scripts/pfp_gf.py (function gfalternate_createdict_outputs) maps default=400, AWS=410, ACCESS=420, ERA-Interim=430, ERA5=440.
- OzFlux/PyFluxPro scripts/pfp_ts.py (function do_attributes) documents Flag00 good data, Flag10 linear correction, Flag50 interpolation.
- These are *software-code definitions*, not proof that this particular source product was processed with this exact software/configuration version. Verify original variable-level description_L1/L2/L3/L4/L5/L6 and original flag metadata before approval.

The Stage05 inspector compares each Stage04 candidate with its main series in (1) all finite overlap and (2) overlap where both native QC flags are exactly 0, plus (3) a Fsd high-irradiance proxy stratum where both values exceed 20 W/m^2. This controls low-radiation domination of RMSE. **QC=0 is a comparison stratum, not certification of an independent tower observation**. It inventories exact native timestamps, candidate values, donor flags, the before/after primary data context, and an exact QC histogram of gap-period candidate rows. It does not auto-fill.

On IRIDIS6:

~~~bash
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ce7372bb846d4f23e975f564dc375a3e8e2a4e86/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage05_code"
STAGE04="$HOME/ozflux_stage04_v2_20261101T060431Z"
OUT="$HOME/ozflux_stage05_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/sites.tsv" -o "$CODE/sites.tsv"
curl -fLsS "$BASE/scripts/stage05/05_qcflag_donor_independence_readonly.py" \
    -o "$CODE/ozflux_stage05_donor_science.py"
python3 -B -m py_compile "$CODE/ozflux_stage05_donor_science.py"
python3 -B "$CODE/ozflux_stage05_donor_science.py" --self-test
python3 -B "$CODE/ozflux_stage05_donor_science.py" \
    --manifest "$CODE/sites.tsv" --stage04 "$STAGE04" --out "$OUT"
echo "Stage05 output: $OUT"
~~~

Reports:
- stage05_qc_provenance.json: per-file metadata/QC histograms, donor statistics and codebook provenance.
- stage05_donor_comparison.tsv: target vs donor co-located source statistics across valid and QC0/QC0 overlap (high-Fsd proxy separate).
- stage05_candidate_gap_values.tsv: all donor-available gap record indices, native timestamps, source values, QC flags and nearest primary neighbours.

**Science gate:** no source edits, no QC tier approvals, no reanalysis injection, no DATM, no Slurm. Keep AU-ASM source segments separate and AU-Tum hourly. No spatially invariant ZBOT or PFT assumptions.

## 3f. Stage06A: targeted donor lineage and gap-boundary forensics (read-only)

**Operator Stage05 verified 10/10, 18 donor comparisons and 468 candidate
records (nonunique across donors). Stage05 source audit output:
`$HOME/ozflux_stage05_20261101T060943Z`.** No source edits or
science approvals.

The three high-priority evidence findings are:
1. AU-Cpr main Ta versus `Ta_HMP_2m` on 262,984 common native
   QC=0 records has **exactly zero RMSE**; 106/110 missing main Ta records
   have a valid donor value with donor QC=0. This suggests common lineage,
   NOT independent sensor validation. `Ta_SONIC_Av` has 96/110.
2. AU-Gin `Fsd_1` has 265/1,156 values available during
   primary Fsd gaps, all donor QC=0, **none exceed 20 W/m²**. This is low
   irradiance evidence, *not proven nighttime* until solar time/geolocation
   is independently checked. On simultaneous QC=0 Fsd data, Fsd_1
   RMSE 10.09 W/m² (both positive >20: 10.57).
3. AU-How `Fsd_ARM` is available at one of six primary
   Fsd gaps, native donor QC=0, but RMSE 88.30 W/m² on both QC0 data,
   126.96 W/m² when both >20. Do not substitute unconditionally.

Stage06A separately checks the exact source flags, exact/numerical agreement
of main and candidate in overlapping times, donor values at each target
gap, neighbouring original source records, and units/instrument/height
metadata. Native timestamps are labelled **unverified timezone**; there
is no automatic nighttime or independence conclusion.

Run on IRIDIS6 using this pinned version (no source modifications):

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/e6e8e6a078eac4a0d8a590c564a929f7b9258560/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage06_code"
STAGE05="$HOME/ozflux_stage05_20261101T060943Z"
OUT="$HOME/ozflux_stage06_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/sites.tsv" -o "$CODE/sites.tsv"
curl -fLsS "$BASE/scripts/stage06/06_targeted_donor_lineage_forensics_readonly.py" -o "$CODE/ozflux_stage06_lineage.py"
python3 -B -m py_compile "$CODE/ozflux_stage06_lineage.py"
python3 -B "$CODE/ozflux_stage06_lineage.py" --self-test
python3 -B "$CODE/ozflux_stage06_lineage.py" \
    --manifest "$CODE/sites.tsv" --stage05 "$STAGE05" --out "$OUT"
echo "Stage06A output: $OUT"
)
~~~

Expected: 3 original source files, 5 donor comparisons, detailed gap-row
evidence. Reports: `stage06_lineage_evidence.json`,
`stage06_donor_lineage_summary.tsv` and
`stage06_exact_candidate_records.tsv`. This is an investigative
subset of the larger 9-site cohort, not a waiver of other stations' HOLDs.

## 3g. Stage07: native-year forcing candidate assessment (strictly read-only)

**Stage06A operator output 2026-11-01:** 3/3 selected original sources, 5 donor comparisons, 468 candidate rows (including duplicate time indices across candidate sensors); no modifications. AU-Cpr Ta vs Ta_HMP_2m exact 262,984/262,984 during shared QC0 periods; donor 106/110 missing main Ta. AU-Gin Fsd_1 265/1,156 gap records with donor values -2.746366 to +4.295752 W/m²; no gap value above 20; Fsd_7m 0. AU-How Fsd_ARM one gap value 94.69449933 W/m², shared QC0 Fsd RMSE 88.301753 W/m². None of these are approved as independent meteorological repairs.

Because a repair cannot be approved before knowing the viable driving period, Stage07 scans **all ten** original L6 NetCDF files again to establish for every native calendar year: number of timestamps vs expected native cadence, strict midnight-label boundaries, each of seven meteorological missing values and broad physical alarms, and per-variable original QCFlag counts (0,10,50,400,410,420,430,440, other). It inventories source time zone/site metadata and source-level description attributes. This yields structural candidate years, **not scientific/model approval**. Year boundaries are native numeric labels only: interval-start/end/center and UTC/local-time semantics remain unverified. Retain two AU-ASM releases separately, and native AU-Tum hourly cadence; no resampling is authorised.

IRIDIS6 usage (download pinned script, do not pre-create its OUT folder):

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/db11c06fbc8290a04f28f622c390e6ac3f04c448/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage07_code"
OUT="$HOME/ozflux_stage07_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/sites.tsv" -o "$CODE/sites.tsv"
curl -fLsS "$BASE/scripts/stage07/07_native_year_forcing_readiness_readonly.py" -o "$CODE/ozflux_stage07_years.py"
python3 -B -m py_compile "$CODE/ozflux_stage07_years.py"
python3 -B "$CODE/ozflux_stage07_years.py" --self-test
python3 -B "$CODE/ozflux_stage07_years.py" --manifest "$CODE/sites.tsv" --out "$OUT"
echo "Stage07 output: $OUT"
)
~~~

Artifacts: stage07_file_summary.tsv; stage07_year_status.tsv; stage07_year_variable_qc.tsv; stage07_native_year_provenance.json. No source writes, no interpolation, no forcing, no output NetCDF and no model submissions. STRUCTURAL_CANDIDATE_ONLY_QC_UNAPPROVED is explicitly not a PASS for scientific source provenance, atmospheric height, time zone or DATM readiness.

## 3h. Stage08: classify annual HOLD reasons and identify contiguous structural-year blocks (read-only)

**Operator Stage07 result (2026-11-01): 10/10 original sources examined, 169 native file-year rows. 67 structural-only candidate years and 102 REVIEW/HOLD years; no source edits or science approval.** Per source-file structural years: ASM1 9/14; ASM2 1/3; Cow 12/18; Cpr 2/17; DaS 16/19; Dry 14/17; Gin 0/16; How 2/25; Stp 4/19; Tum 7/21.

Candidate year subsets in the latest Stage07 native-time labels include:

- AU-DaS 2009–2021 (13 consecutive native years), and 2023–2025.
- AU-Dry 2010–2018 (9), 2020–2024 (5).
- AU-ASM Mulga1 2013–2018 (6), 2020–2022 (3); Mulga2 separate 2025 (1). No cross-gap merge.
- AU-Cow 2015–2019 (5), 2022–2025 (4), and isolated earlier years.
- AU-How has only 2006 and 2007 meeting the new L6 source's conservative structural gate. This does not invalidate the historically successful AU-How case, which used a different source selection and QC assumptions.

The new Stage08 source does **not open original NetCDF** and uses three Stage07 report files plus sites.tsv. It validates row totals, native QC partition counts and per-year summations, and reports all per-year missing/physical/time reasons plus QC code fractions (native QC0 and 410 AWS, 420 ACCESS, 440 ERA5 hypotheses). It identifies maximal consecutive structural-year blocks; these are not science-approved or necessarily sufficient to support later DATM year-cycling.

Use the original operator Stage07 directory on IRIDIS6:

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/da3ea4d945ba5092afdc056a28dff61884f31120/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage08_code"
STAGE07="$HOME/ozflux_stage07_20261101T062633Z"
OUT="$HOME/ozflux_stage08_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/sites.tsv" -o "$CODE/sites.tsv"
curl -fLsS "$BASE/scripts/stage08/08_year_block_qc_triage_readonly.py" -o "$CODE/ozflux_stage08_triage.py"
python3 -B -m py_compile "$CODE/ozflux_stage08_triage.py"
python3 -B "$CODE/ozflux_stage08_triage.py" --self-test
python3 -B "$CODE/ozflux_stage08_triage.py" --manifest "$CODE/sites.tsv" --stage07 "$STAGE07" --out "$OUT"
echo "Stage08 output: $OUT"
)
~~~

Outputs: stage08_review_summary.json, stage08_year_reason_ledger.tsv, stage08_contiguous_candidate_blocks.tsv, stage08_source_qc_per_year.tsv. `CONTIGUOUS_NATIVE_STRUCTURAL_ONLY` is not a simulator-ready status. No forcing, netCDF, model experiment or Slurm job will be created.

## 3i. Stage09: first-cohort native-clock, solar and humidity gate (read-only)

**Operator Stage08 verified 2026-11-01:** 169 source-file years, 67
structural candidates, 102 REVIEW/HOLD. Breakdown of non-exclusive reasons:
19 native-year record-count mismatches, 19 incomplete year boundaries,
86 MET-missing source-years and 1 broad physics alarm; 67 structural-only
QC provenance HOLDs. The largest continuous native structural candidates:
AU-DaS 2009-2021 (13 years, 0.929446 native QC=0 across seven
meteorological fields), AU-Dry 2010-2018 (9 years, 0.751297),
AU-ASM Mulga1 2013-2018 (6 years, 0.975131); AU-Cow 2015-2019
(5 years, 0.927380). These are *not* source-lineage or model approvals.

**Important land-cover history:** TERN OzFlux's AU-DaS description records
clearing for crop development in November 2022. Do not assume that 2023-2025
and pre-2022 years use the same vegetation/PFT regime. Focus this Stage09
first-cohort science pilot on **AU-DaS 2009-2021** and independent
**AU-ASM Mulga1 2013-2018**. Keep Mulga2 separate and do not change
the successful AU-How case. Site reference:
https://tern-ozflux.odoo.com/daly-river .

**Native time warning:** PyFluxPro L1 documentation explicitly says
PyFluxPro does not use the time_zone metadata to convert timestamps
automatically; it leaves the original data timestamps intact. The
successful preexisting AU-How example used native OzFlux timestamps rather
than an earlier TCCAS local-to-UTC conversion, then wrote DATM with
30-minute interval centres. This cannot simply be copied without
verifying each new original source's local clock and interval convention.
See https://github-wiki-see.page/m/OzFlux/PyFluxPro/wiki/Level-1 .

Stage09 examines those two sites' original NetCDFs strictly in mode r,
revalidates selected Stage07 complete years, checks source latitude and
longitude against official OzFlux site descriptions, inventories time/height
and precip metadata, compares native timestamps against approximate solar
position for clock offsets 0 and +9.5 hours and exploratory +/-30 minute
interval shifts, and screens humidity against a diagnostic physical
saturation threshold. The 0 vs +9.5 candidate is *hypothesis testing*,
not an authorised time transformation. Neither solar correlation nor
preliminary native clock hypothesis grants official UTC or interval-centre
approval. ZBOT, units per precipitation interval and PFT/soil/site surface
also remain manual science gates.

Run on IRIDIS6:

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/498459f2ea84c929802cb50cdde5991e8f972bfc/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage09_code"
STAGE07="$HOME/ozflux_stage07_20261101T062633Z"
OUT="$HOME/ozflux_stage09_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/sites.tsv" -o "$CODE/sites.tsv"
curl -fLsS "$BASE/scripts/stage09/09_first_cohort_time_solar_physics_gate_readonly.py" -o "$CODE/ozflux_stage09.py"
python3 -B -m py_compile "$CODE/ozflux_stage09.py"
python3 -B "$CODE/ozflux_stage09.py" --self-test
python3 -B "$CODE/ozflux_stage09.py" \
  --manifest "$CODE/sites.tsv" --stage07 "$STAGE07" --out "$OUT"
echo "Stage09 report dir: $OUT"
)
~~~

Outputs: stage09_source_time_solar_physics.json, stage09_year_physics.tsv.
Only reports are written; no original NetCDF is modified and no
forcing/model case/Slurm jobs are created. The science approval remains
FALSE even if the solar clock hypothesis strongly favors one convention.

## 3j. Stage10: UTC-year boundary hypotheses and AU-DaS 885-event humidity forensic (READ ONLY)

**Operator-confirmed Stage09 output (2026-11-01): 2/2 target sources, 19
complete native source years.** Both AU-DaS 2009–2021 and AU-ASM Mulga1
2013–2018 show sharply better Fsd-vs-solar-position correlations if source
timestamps are interpreted as Australia/Darwin local labels (UTC+09:30):
DaS **r=0.946480** for local vs **r=-0.563873** for direct UTC;
ASM **r=0.946425** for local vs **r=-0.536661** for direct UTC.
The best sampled solar candidate is native end-label minus 15 min to the
interval midpoint, not evidence that the ORIGINAL source must be shifted.
PyFluxPro overview documents that it preserves input timestamps, that TERN
alternate meteorological data typically use local END-of-interval labels,
and that PyFluxPro makes no blanket assumption about input time semantics:
https://github-wiki-see.page/m/ternaustralia/PyFluxPro/wiki/Overview-of-PyFluxPro

**AU-DaS serious HOLD**: 885 native half-hours exceed 1.05 times
specific humidity saturation inferred from the simultaneous original
Ta and ps, in 2015 (1), 2016 (370), 2017 (5), 2018 (202),
2019 (77) and 2021 (230). AU-ASM has zero of this diagnostic type.
These source-derived physical consistency flags are not identical to
an instrument failure. QA/QC, height, pressure and L4 gap-fill
provenance must be investigated; never clamp SH, edit source or
automatically replace with ERA5.

Stage10 reads the two original files in mode='r' and the pinned Stage09
report, without any source writes. It checks three *numeric-view-only*
hypothetical interpretations of local clock values converted to UTC:
local end-label only (-9h30), candidate 30-min interval midpoint
(-9h45), and candidate start (-10h); it validates candidate
UTC calendar-year record counts and center stamps across the
year boundary using ALL original file records, including surrounding
years. These are NOT approved time transforms or DATM files.

For AU-DaS only, Stage10 reproduces and cross-checks all 885 events
with the exact Stage09 saturation calculation; writes each row with
native time, Ta, SH, ps, qsat and 3 original QCFlags, event-group
duration, year counts and potential original RH evidence. At no point
does it mark all 885 as repair-approved.

IRIDIS6 command (use pinned source; do NOT create OUT in advance):

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/5d9333609f6ba798ce49671eb615d4a8642d8265/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage10_code"
STAGE09="$HOME/ozflux_stage09_20261101T064744Z"
OUT="$HOME/ozflux_stage10_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage10/10_utc_boundary_and_das_humidity_forensics_readonly.py" \
  -o "$CODE/ozflux_stage10_forensics.py"
python3 -B -m py_compile "$CODE/ozflux_stage10_forensics.py"
python3 -B "$CODE/ozflux_stage10_forensics.py" --self-test
python3 -B "$CODE/ozflux_stage10_forensics.py" \
  --stage09 "$STAGE09" --out "$OUT"
echo "STAGE10 REPORT_DIR $OUT"
)
~~~

Reports: stage10_source_time_humidity.json,
stage10_hypothetical_UTC_year_bounds.tsv,
stage10_DaS_SH_885_exact_records.tsv,
stage10_DaS_SH_event_episodes.tsv,
stage10_DaS_SH_year_stats.tsv.
None are source/model/forcing files. Explicit human science sign-off
for clock semantics, PFT, soil and ZBOT remains required.

## 3k. Stage11: AU-DaS 885 humidity-source consistency and AU-ASM 6-year NOLEAP preflight (read-only)

**Operator Stage10 execution 2026-11-01:** source hash, syntax,
selftest and exact source forensic passed. Under the *unapproved*
Australia/Darwin local END-label -> hypothetical UTC interval-centre
interpretation, **19/19** complete native source-years remain complete
as UTC center-year windows (AU-DaS 2009–2021: 13/13;
AU-ASM Mulga1 2013–2018: 6/6). The assumption is strongly supported by
solar consistency but still requires source time metadata verification.

**Critical AU-DaS scientific HOLD:** Stage10 exactly recovered **885**
native half-hours with SH > 1.05 qsat, in **207 episodes**, and
**all 885 SH_QCFlag are 0**. This means the source variable's numeric
QC 0 alone did not capture cross-variable humidity physics failures.
The Feb 18–19 2021 episode (26 half-hours) has a peak SH/qsat of
3.4863, so this is not merely a small tolerable humidity excess.
Do not clip all values automatically to saturation or relabel QC0.
Preserve raw and investigate paired temperature and pressure sensors,
humidity transformation, optional RH/VPD and site-specific
instrument/processing lineage.

Stage11 is the *final source-physics/clock preflight* before either
candidate forcing artifact generation or an explicit site hold decision.
It **does not edit source data or create forcing**. It performs:
1. AU-DaS exact 885 original records: reproduce indices and SH-QC0,
   stratify severity by year, capture original Ta/ps QC, neighbouring
   measurements, and optional original RH/VPD. Optional RH/VPD
   from the **same processed L6 file are not independent validation**;
   retain metadata/units, compare only when units are recognised.
2. AU-ASM six hypothetical UTC center-years: recheck the Stage10
   6/6 boundary result with original source values and timestamp
   sample cadence; remove UTC Feb29 **in a temporary numerical view only**
   and verify 17,520 remaining half-hours each, zero residual missing
   among the seven meteorological forcing fields and zero
   SH >1.05 qsat events. Catalogue original PFT/ZBOT/time/precip
   metadata but **do not claim approval** of any.

IRIDIS6 command (pinned GitHub version and operator Stage10 report):

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/43d611892b8eb8ad48129f06ae02a82718a387c9/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage11_code"
STAGE10="$HOME/ozflux_stage10_20261101T065245Z"
OUT="$HOME/ozflux_stage11_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage11/11_das_humidity_and_asm_noleap_preflight_readonly.py" \
  -o "$CODE/ozflux_stage11_das_asm.py"
test "$(git hash-object "$CODE/ozflux_stage11_das_asm.py")" = \
  "25f48e12b34ba0177649414d766d4128319fd801"
python3 -B -m py_compile "$CODE/ozflux_stage11_das_asm.py"
python3 -B "$CODE/ozflux_stage11_das_asm.py" --self-test
python3 -B "$CODE/ozflux_stage11_das_asm.py" \
  --stage10 "$STAGE10" --out "$OUT"
echo "STAGE11 REPORT_DIR $OUT"
)
~~~

Outputs: `stage11_science_evidence.json`,
`stage11_DaS_885_cross_variable.tsv`,
`stage11_ASM_UTC_NOLEAP_preview.tsv`.
The 885 source records and six years are both strict reproducibility gates.
No model cases or Slurm submissions. AU-ASM remains provisional until
time semantics, source precipitation per-interval meaning, ZBOT,
PFT/surface/soil and file-writing provenance are independently signed off.

## 3l. Stage12: AU-ASM guarded PROVISIONAL DATM builder (audit-only by default)

**Operator Stage11 succeeded on IRIDIS6 (2026-11-01).**
- AU-ASM Mulga1 2013–2018 all six hypothetical UTC-centre years contain complete source records, no missing in the seven forcing variables and no SH >1.05 calculated qsat. 2013/14/15/17/18 native-view UTC source years have 17,520 records; 2016 17,568 with 48 hypothetical UTC Feb29 records removed to give 17,520 each.
- AU-DaS retains 885 independent source-physics flags even with SH_QCFlag=0, 207 grouped episodes; severity bands: 741 in 1.05–1.10, 81 in 1.10–1.20, 23 in 1.20–1.50 and **40 at or above 1.50 qsat**. Optional source RH and VPD exist but are from the same processed L6 product, not automatically independent measurements. Severe events involve unusual simultaneous Ta values around 0–4 C; must investigate temperature source/height/instrument and paired original humidity before attributing failure solely to SH.
- Stage11 reports reside at `$HOME/ozflux_stage11_20261101T065724Z`. No source edits or DATM generated.

**Independent external site evidence:** OzFlux's Alice Springs Mulga site description (https://ozflux.org.au/monitoringsites/alicesprings/alicesprings_description.html) gives coordinates -22.2828, 133.2493, a **13.7 m mast**, canopy average **6.5 m**, temperature and humidity **11.6 m above canopy**, wind speed **9.25 m**, downwelling radiation **12.2 m**, precipitation **2.5 m** and barometric pressure **1 m**. The tower height is not ZBOT. Using 11.6 m for the candidate atmospheric forcing reference height is a *source-informed candidate*, NOT automatic science approval; verify the actual selected L6 Ta/SH field metadata and modelling convention. Precip units mm require verification as *per-interval accumulation* before the established AU-How conversion mm/1800 s -> mm/s can be applied. The site's mulga canopy, understory grass and bare soil also require independent PFT/surface science decisions before CTSM case building.

The **new standalone Stage12 script** defaults to a preflight-only action.
It opens only original AU-ASM Mulga1 source read-only, checks Stage11 exact
6-year records, verifies hypothetical UTC-centre 30-min chronology,
zero residual gaps and broad physical consistency, and records native
time/height/source/precip metadata under a new HOME output directory.
No new NetCDF or model case is created by preflight.

To run preflight:

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/210bb542f03ec825e44e74298f3d10012c8438e8/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage12_code"
STAGE11="$HOME/ozflux_stage11_20261101T065724Z"
OUT="$HOME/ozflux_stage12_preflight_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage12/12_asm_provisional_DATM_builder_guarded.py" \
 -o "$CODE/ozflux_stage12_guarded.py"
test "$(git hash-object "$CODE/ozflux_stage12_guarded.py")" = \
 "600712bf17d1e6b59fe4fd43c91cf75066423ee6"
python3 -B -m py_compile "$CODE/ozflux_stage12_guarded.py"
python3 -B "$CODE/ozflux_stage12_guarded.py" --self-test
python3 -B "$CODE/ozflux_stage12_guarded.py" \
 --stage11 "$STAGE11" --preflight --out "$OUT"
echo "STAGE12 preflight report: $OUT/stage12_ASM_candidate_manifest.json"
)
~~~

**No write-candidate action is authorised yet.** The script's *separate*
write-candidate mode is guarded by exact confirmation text, reviewed
ZBOT value and evidence, reviewed source local END time semantics,
and reviewed per-30-minute Precip accumulation provenance. Write mode
requires a **new** output path outside all original source trees and
writes six independently named PROVISIONAL NetCDFs and a provenance
manifest, with no deletion and no Slurm. Science approval remains FALSE.
This is for model-input validation only after operator confirmation,
not production FATES spinup.

## 4. Future science decisions (still require explicit approvals)

The read-only source forensic stages above are implemented and have already run through Stage05. The following are future *decisions and separate write-authorised workflows*, not reruns of numbered Stage02–05 scripts:

1. Independently verify native timezone, site location and time semantics, L6 variable source descriptions, observation/gap-fill fraction and approved QC code interpretations; retain Mulga1/Mulga2 separately and AU-Tum hourly.
2. Determine science-approved site-specific handling of meteorological missing values and physical holds, considering independent tower donors before testing weather-station, ACCESS or ERA5 data. Keep original NetCDF immutable and record each proposed intervention.
3. Verify PFT, bare-ground/shrub fractions, soil properties, atmospheric measurement heights and original site surface assumptions independently per tower.
4. Only after QC sign-off, produce separately versioned candidate forcing and year-specific DATM/NOLEAP files, verify physics/time series and then decide whether to submit AD400/Normal400 experiments; do not touch previous AU-How runs.

## 5. Provenance and non-destructive rules

- File names, local paths and cohort selection: experiment operator, 2026-11-01.
- Layout and guarded batch-transfer workflow: [JapanFlux MultiSite 11](../JapanFlux_MultiSite_11/) and earlier AmeriFlux examples.
- Existing AU-How forward case and its nontrivial time convention: [README](../OzFlux_AU-How/README.md) and [KNOWN_ISSUES](../OzFlux_AU-How/KNOWN_ISSUES.md).
- Store only documentation, manifest and scripts on GitHub; **do not commit raw EC NetCDF files, generated DATM outputs or Slurm results**.
- Neither source files nor existing model experiments are modified by this new cohort's checked-in scripts.

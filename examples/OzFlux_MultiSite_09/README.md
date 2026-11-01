# OzFlux MultiSite 09 — source-preserving IRIDIS6 transfer and L6 scientific intake

**Status (2026-11-01): PREPARED, NOT EXECUTED.** This cohort contains **9 station IDs and 10 original NetCDF files**. The Windows D: file locations were supplied by the experiment operator; neither local files nor remote files have been opened by this repository change. Scripts are published, but **no upload, byte verification, NetCDF assessment, forcing conversion, CIME case or Slurm run is yet claimed**.

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

## 4. Subsequent scientific stages (not implemented/authorised yet)

1. **Stage02B — source provenance/time QC human review:** verify actual temporal coverage, time coordinate convention (UTC vs local, interval start/end/centre), timestep, gaps/duplicates, fill values, QA/QC flags, lat/lon, instrument/source changes and especially the two AU-ASM periods. Keep each source immutable.
2. **Stage03 — meteorological physics and forcing candidate:** evaluate OzFlux variable mapping per station, compare native data and observation QC, assess radiation/humidity/precipitation and site-specific height. Existing AU-How uses `Ta→TBOT`, `SH→QBOT`, `ps→PSRF`, `Fsd→FSDS`, `Fld→FLDS`, `Ws→WIND`, `Precip→PRECTmms`; **do not assume units, gap-filling status or mapping are identical for these other L6 products**.
3. **Stage04 — site vegetation/soil/surface:** scientific approval of each site's PFT fractions, shrub/bare ground, soil texture and correct surface/mesh. No copy of an unrelated site's vegetation or forcing height.
4. **Stage05 — independent DATM and NOLEAP audit; model preflight:** validate chronology, water and radiation physics and all required forcing fields. Only after sign-off, prepare site-specific CIME/FATES cases and consider the established staged spinup (AD and Normal) approach. **Stage00 and Stage01 submit no Slurm jobs.**

## 5. Provenance and non-destructive rules

- File names, local paths and cohort selection: experiment operator, 2026-11-01.
- Layout and guarded batch-transfer workflow: [JapanFlux MultiSite 11](../JapanFlux_MultiSite_11/) and earlier AmeriFlux examples.
- Existing AU-How forward case and its nontrivial time convention: [README](../OzFlux_AU-How/README.md) and [KNOWN_ISSUES](../OzFlux_AU-How/KNOWN_ISSUES.md).
- Store only documentation, manifest and scripts on GitHub; **do not commit raw EC NetCDF files, generated DATM outputs or Slurm results**.
- Neither source files nor existing model experiments are modified by this new cohort's checked-in scripts.

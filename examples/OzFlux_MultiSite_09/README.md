# OzFlux MultiSite 09 — source-preserving IRIDIS6 transfer and L6 scientific intake

**Status (2026-11-02): STAGES01–36 OPERATOR VERIFIED. Stage36 source/catalog preflight confirmed 111 original 2018-DERIVED stems (NOT independent 2018 measurements); the separate 2018 supersite.1041 ARDC URL returned HTTP 404 and legacy TERN URL redirected to the portal without this dataset, so no true 2018 stem-file bytes are verified. User has SELECTED GitHub review-accepted OzFlux v1.1 PFT source for all nine NEW non-competition cases: source branch `oz-jp-pft-guidance-20261102`, commit `d62c814585c4aa85731f77b4a555efe6ec9e94a3`; primary vectors have been snapshotted in [Non-Competition OzFlux_Batch01_09](https://github.com/lyanyeung/Non-Competition-CLM-experiment/tree/main/examples/OzFlux_Batch01_09/). PFT composition is now an OPERATOR-SELECTED FIXNC model hypothesis, not observed cover; no ORIGINAL source L6, DATM, surface or FATES parameters, old AU-How case, CIME or Slurm job has been changed. Non-Competition Stage01 and Stage02 operator PASSED: nine PFT snapshots, ten L6 original files and nine source L6 coordinate metadata records verified; a NEW ISOLATED AU-ASM v1.1 FIXNC point Surface CANDIDATE was created (SHA256 d06ad3111d93de69e7f2dd7f048b02a9161aee4ff853afafedcdfed71a54f3a1), preserving soil and all reference variables except PCT_NAT_PFT. Non-Competition Stage03 eight remaining CTSM reference and PFT site candidate builder PUBLISHED but operator run PENDING. Final per-site forcing/soil/effective-case science gates remain pending; AD5 and AD400 not submitted.** The cohort has **9 site IDs and 10 original L6 NetCDF files**. Stage07 classified 169 file-year rows (67 structural candidates, 102 REVIEW/HOLD). Stage09–11 established a strong provisional Australia/Darwin local-END to UTC-center time hypothesis and six complete AU-ASM NOLEAP calendar years; AU-DaS retains 885 SH supersaturation flags (40 >=1.5x saturation). Stage12 wrote six standalone provisional AU-ASM DATM NetCDFs without changing original sources. **Stage13 independently verified 6/6 exact source-to-DATM meteorological mappings**, and found 360 below-horizon negative FSDS records (2014: 359 QCFlag 420; 2016: 1 unresolved original QC code), plus 1 wind record >15 m/s in 2018. The next step is targeted negative-radiation QC and site-specific PFT/soil/surface assessment. **No final forcing-science approval, CIME case build, AD400/Normal400 model submission or changes to existing AU-How cases have occurred.**

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

## 3m. Stage12 operator preflight SUCCESS; guarded candidate DATM write eligible but NOT authorised automatically

2026-11-01 operator Stage12 preflight output:
`$HOME/ozflux_stage12_preflight_20261101T174552Z` .
Verified script source hash, syntax and self-test. `STAGE12 SOURCE_PREFLIGHT_ONLY FILES 0` (expected).
Original Mulga1 source SHA256 is
`b9381c4ed0744d03ae609cfbf3805e30bbb9223851a05f4e5b63b149dd0b10eb`.
2013–2018 UTC-center hypotheses all pass 17,520 NOLEAP half-hours;
2016 Feb29 removes exactly 48 half-hour records. No original source
NetCDF was changed. Original source metadata includes:
- lat -22.2828, lon 133.2493; `time_zone=Australia/Darwin`, `time_step=30`.
- `Ta` HMP45c 11.6m, average; `Ws` CSAT3/3B 11.6m, average.
- `SH` specific humidity kg/kg, "Merged with SH calculated from AH", no reported source height.
- `ps` kPa at source `height=23m` (must independently review provenance);
  Fsd/Fld W/m2 at source 12.2m; Precip at source 2m, `units=mm`,
  `statistic_type=sum`, source L4 fill includes AWS/ACCESS/ERA5.
- Vegetation is acacia mulga plus C3 forbs/shrubs, C3 grass and C4 grass;
  soil red kandosol, sandy loam; canopy_height 4.4m.
  These descriptions are not surface/PFT/soil parameter estimates.

**Next decision:** The existing Stage12 builder supports manually run
`--write-candidate` with reviewed `--zbot-m 11.6` (candidate, SH height unknown),
nonempty evidence strings for ZBOT, site-local END label/UTC midpoint
time interpretation, and per-30min accumulated Precip in mm, plus exact
`--confirm BUILD_AU_ASM_PROVISIONAL_2013_2018`. It writes
six **new provisional** yearly NetCDF files under a unique HOME output
folder with source SHA256 provenance, never overwrites/deletes original
source, and does not submit Slurm. The QC/science approval remains FALSE;
none of these records establish final approved source or vegetation,
soil, surface, ZBOT or CIME forcing conventions.

**AU-DaS independent operator excerpt**: All 885 SH/saturation ratio
alerts have source SH_QCFlag=0; 40 at ratio>=1.5. Severe records also
report RH as high as ~350 percent and negative VPD to -1.9 kPa, and
derived RH/VPD from Ta, SH and ps are similar. L6 RH/VPD may share
upstream Ta/SH processing and are not independently verifying data.
Unusually low paired Ta (~0-6 C in extreme events) makes temperature
sensor and source processing an urgent first diagnostic. Do not clip SH
or relabel QC0, and do not infer one instrument is solely responsible.

## 3n. Operator Stage12 six provisional DATM files VERIFIED; Stage13 independent mapping and negative-FSDS science QC

2026-11-01 Stage12 guarded `--write-candidate` operator execution succeeded for six years 2013–2018. Original source SHA256 was independently checked before/after:
`b9381c4ed0744d03ae609cfbf3805e30bbb9223851a05f4e5b63b149dd0b10eb`.
Candidate directory is
`/iridisfs/home/ly3n24/ozflux_ASM_PROVISIONAL_DATM_20261101T182517Z`.
Exactly six independent
`AU-ASM_PROVISIONAL_DATM_{year}.nc` files, 17,520 NOLEAP half-hours/year, 8 finite variables including
`ZBOT=11.6m`, full calendar and source SHA metadata, no model jobs.
2016 Feb29 was excluded in the *derived* candidate only. No original
files changed. Precip source `mm per 30 minutes` -> candidate
`mm/s` retained year totals: 2013 142.8, 2014 376.4, 2015
315.6, 2016 635.4, 2017 363.2, 2018 106.8 mm.

**Unresolved main blocker:** Original-derived candidate FSDS has negative
values on **359 half-hours in 2014** (minimum -4.886132 W/m2) and
**1 half-hour in 2016** (minimum -7.257903 W/m2); no such values in
2013/2015/2017/2018. The correct treatment needs original source
`Fsd_QCFlag`, precise UTC-hypothesis solar position and
day/night classification. Do not blindly clamp or directly launch AD400.
2018 wind maximum 16.296 m/s warrants basic source/QC investigation,
not automatic filtering.

**New Stage13** *reads original and all six candidate NetCDFs strictly in
read mode* and reconstructs the exact source-index mapping after
provisional local END minus 585 min and UTC Feb29 exclusion.
It demands exact float32 agreement for all seven transformed
meteorological forcing fields, correct NOLEAP time, lat/lon, ZBOT,
source SHA256 and annual precipitation conservation. It records all 360
source-negative-Fsd rows with the source QC and *provisional* UTC
solar elevation, plus any wind >15 m/s source records. It writes
**reports only** under a new HOME path and never overwrites or changes
the six candidates.

Execute Stage13:

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/455af424e62fe2ea4fc33a766f7865ff5cbc19fb/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage13_code"
OUT="$HOME/ozflux_stage13_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage13/13_asm_provisional_datm_byte_science_QC_readonly.py" -o "$CODE/ozflux_stage13_QC.py"
test "$(git hash-object "$CODE/ozflux_stage13_QC.py")" = "82daf98edf8e0ac7ea73634566c0194fe2cbbcc5"
python3 -B -m py_compile "$CODE/ozflux_stage13_QC.py"
python3 -B "$CODE/ozflux_stage13_QC.py" --self-test
python3 -B "$CODE/ozflux_stage13_QC.py" --out "$OUT"
echo "Stage13 output: $OUT"
)
~~~

Outputs:
- stage13_ASM_candidate_QC_summary.json
- stage13_ASM_annual_exact_validation.tsv
- stage13_ASM_360_negative_FSDS.tsv
- stage13_ASM_wind_gt15.tsv

Success remains **science_approval=false** and does not authorize
final forcing or AD400. Once the source-negative shortwave issue
is adjudicated, separately audit the site-observed Mulga
canopy/shrub/C3/C4 grass/bare-soil fractions and site's red
kandosol/sandy-loam soil against a candidate surface, plus
FATES-PFT and CIME/DATM streams. ZBOT=11.6m is supported by
reported source Ta/Ws heights but SH height remains undocumented,
and source ps height is recorded as 23m; preserve this uncertainty.

## 3o. Stage13 exact FSDS/QC event review completed; Stage14 NEW candidate variant guarded

**Operator 2026-11-02 Stage13 audit**: 6/6 DATM source mappings **exact**,
source SHA256 remained verified, and 360 negative FSDS entries originated
from original OzFlux L6. Detailed follow-up:
- **2014: 359 entries, all Fsd_QCFlag 420** (PyFluxPro ACCESS
  alternate source), negative Fsd -4.8861322 to -0.7414520 W/m².
  Under the provisional local Australia/Darwin END -> UTC center clock,
  345 entries are below solar elevation -6°, and 14 are between -6° and 0°;
  all negative values are below solar horizon, with peak elevation -0.18055°.
  Hypothetical FSDS=0 energy perturbation: **+3.07011177 MJ/m²**.
- **2016: 1 entry, original Fsd_QCFlag 50** (PyFluxPro interpolation
  metadata); original native local label 2016-05-27 07:00, provisional UTC
  center 2016-05-26 21:15, solar elevation **-5.43182°**, FSDS -7.2579031
  W/m². Zero floor would add **+0.01306423 MJ/m²**.
- Total 360 negative source values; all have provisional modelled solar elevation
  below 0°, with 345 below -6° and 15 between -6° and 0°. Combined
  zero-floor energy perturbation +3.083175996 MJ/m² across 2014 and 2016.
- **2018: 1 WIND=16.29613 m/s at local 2018-03-10 20:30,
  native Ws_QCFlag=0**; remains untouched. Do not reject extreme wind
  merely because it is above 15 m/s.

**Science disposition:** It is defensible to make a separate strictly
provisional FSDS0 candidate branch that sets only the 360
source-negative shortwave flux values to 0, because downward solar
irradiance cannot be negative as a physical model input. This is NOT proof
of sensor malfunction; twilight and ACCESS/interpolation provenance
remain documented. The time axis and source data are NOT changed.
Do not modify original L6, original six Stage12 DATM files, any humidity,
wind, precipitation, or model experiment. Do not submit AD400.

Stage14 is an explicit two-mode guarded script:
`scripts/stage14/14_asm_FSDS_zero_floor_provisional_guarded.py`
(pinned commit `d5cb27e12ecfd958f2758379a1821681614d3906`,
Git blob SHA `adaaa87a538cb508fcd371172869745f5b4d09e1`).
Its `--preview` creates only JSON/TSV reports, checks exact
360 year/QC/time/index/magnitude/solar records against Stage13 and all 6
source-faithful Stage12 candidate hashes. Its separately guarded
`--write-candidate --confirm CREATE_ONLY_AU_ASM_360_NIGHT_FSDS_ZERO_CANDIDATES`
copies the six source-faithful candidate files under a *new* directory,
modifies exactly those 360 FSDS entries to 0 and checks every
other original NetCDF variable at **native-dtype bitwise identity**.
It also verifies all original file hashes before and after, records
energy differences and annual output SHA256, and marks all outputs
as UNAPPROVED. No Slurm, no CIME case, no original overwrite.

IRIDIS6 command:

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/d5cb27e12ecfd958f2758379a1821681614d3906/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage14_code"
OUT="$HOME/ozflux_stage14_FSDS0_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage14/14_asm_FSDS_zero_floor_provisional_guarded.py" -o "$CODE/ozflux_stage14.py"
test "$(git hash-object "$CODE/ozflux_stage14.py")" = "adaaa87a538cb508fcd371172869745f5b4d09e1"
python3 -B -m py_compile "$CODE/ozflux_stage14.py"
python3 -B "$CODE/ozflux_stage14.py" --self-test
python3 -B "$CODE/ozflux_stage14.py" --write-candidate \
  --confirm CREATE_ONLY_AU_ASM_360_NIGHT_FSDS_ZERO_CANDIDATES --out "$OUT"
echo "Stage14 report and new provisional six candidates: $OUT"
)
~~~

Do not treat Stage14 as final surface/PFT/soil/stream science approval.
Proceed next to a site-specific Mulga PFT/soil/bare-ground/surface science
gate. See the register at
`science/AU-ASM_stage13_science_register_20261102.md`.

## 3p. Stage14 operator execution SUCCESS; Stage15 AU-ASM site PFT/soil/surface input inventory

**Stage14 operator confirmed 2026-11-02:** the `--preview` and
`--write-candidate` scientific gates both passed. Created exactly six
separately named FSDS0 provisional DATM files under
`/home/ly3n24/ozflux_stage14_FSDS0_20261102T012038Z`;
only 359 negative FSDS records from ACCESS QC420 in 2014 and
one negative FSDS from interpolation QC50 in 2016 were set to zero.
All seven meteorological variables other than FSDS, all timestamps,
coordinates and ZBOT remain identical at source native precision;
old Stage12 candidates and original OzFlux L6 remain untouched.
Energy increments +3.0701117705 MJ/m² (2014) and +0.0130642256 MJ/m² (2016).
No surface/PFT/case/Slurm activity. Stage14 new candidate SHA256 by year:
2013 0e722aec1d73d35ff4671ccd1c72fbf02c7e3af8f9fdd6cae291834741b2bffe;
2014 54345a6ae15ba8091b118dc62c891cff1fb851eda895178a47c8d3a23143871b;
2015 6d7b9cc4f0e24d6395f1f6d1ae3217f9fd70a67d93f41969eb6cdafe283447bf;
2016 8b5576e424625a0bf62f0fb0fa552230ff7c01e26e440a565242e169fe455c7f;
2017 634d8d395e95331cf9f13dcbf5d48edbc2e881af4ca913acb75abe1333032951;
2018 8ce901670486469358525c95f6a78db82698a5712312c4b1bf610aff744be55d.

**Now stop meteorological gap-repair iteration** and establish defensible
land-model inputs. Published TERN site data describe a mixed Acacia aneura
/ aptaneura evergreen woody Mulga canopy, several C3 shrub/forb and
perennial C3 grass groups, C4 grasses, patchy bare ground, and
a red Kandosol with 74:11:15 sand:silt:clay in recent metadata.
Older OzFlux describes different (50:50) sand:clay; soil depth,
sample coverage and source vintage must be reconciled before selecting
CLM soil layers. These are descriptive ecosystem observations, not a
measured 15-slot `PCT_NAT_PFT` vector or verified FATES PFT
mapping. Bare ground is host natural PFT **index 0**, but cannot be
treated as an FATES active canopy. An older academic 74.5% woody-area
estimate is NOT a ready-made EC-footprint or natland fraction.

**Stage15: inspect the existing IRIDIS6 point surface and reference
CTSM resources only**, source at
`scripts/stage15/15_asm_pft_soil_surface_source_inventory_readonly.py`
(commit `3e753d76783f2d7032b78db487c5facce7bfa58a`).
The inspector checks original six Stage12 and six Stage14 hashes
against the Stage14 operator manifest, scans a bounded AU-ASM site
folder for existing `surfdata*.nc` NetCDFs, inventories natural/host
PFT vector, gridded natveg, host bare index0, sand/clay soil layer
profiles, location and CTSM 2000 input templates. Existing CTSM grid
point surfdata is a **reference only**, not proven tower PFT/soil.

IRIDIS6 command (READ-ONLY, report under HOME):

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/3e753d76783f2d7032b78db487c5facce7bfa58a/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage15_code"
OUT="$HOME/ozflux_stage15_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage15/15_asm_pft_soil_surface_source_inventory_readonly.py" -o "$CODE/ozflux_stage15.py"
python3 -B -m py_compile "$CODE/ozflux_stage15.py"
python3 -B "$CODE/ozflux_stage15.py" --self-test
python3 -B "$CODE/ozflux_stage15.py" --out "$OUT"
echo "Stage15 report directory: $OUT"
)
~~~

Outputs `stage15_ASM_surface_PFT_soil_source_register.json` and
`stage15_existing_surface_candidates.tsv`. **Zero NetCDF writes**,
no PFT assignments or case preparation. Requires exact per-site
scientific PFT fractions, compiled model mapping, 10-layer soil profiles
and independently reviewed point-surface values before CIME submission.

## 3q. Stage15 operator SUCCESS and Stage16 isolated CTSM reference surface builder (not approved for FATES)

**Stage15 actual operator result 2026-11-02**: input script SHA and
self-test PASS; 6/6 Stage14 FSDS0 candidate file SHA/metadata verified;
**0** existing AU-ASM surfdata files found *within the bounded scan*
(does not prove absence globally). Verified that local CTSM, executable
`tools/site_and_regional/subset_data`, reference
`default_data_2000.cfg`, CTSM 5.3.0 16-PFT year-2000 global reference
surfdata and ESMF mesh all exist on IRIDIS6. Report:
`/home/ly3n24/ozflux_stage15_20261102T020625Z`.
Site vegetation/PFT/soil area fractions remain science HOLD; AD400 is
not permitted.

**Stage16 implementation** is
`scripts/stage16/16_asm_isolated_CTSM2000_reference_point_surface.py`.
It uses exactly the three existing proven AU-How / AmeriFlux Batch02
year-2000 reference config substitutions (surfdata 5.4->5.3,
`surfdat_16pft` and `mesh_surf`) and
`subset_data point --lat -22.2828 --lon 133.2493 --lon-type 180
--site AU-ASM --surf-year 2000 --create-surface --create-user-mods`.
No `--dompft`, no `--overwrite`. The output is an isolated fresh
direct child of the operator's HOME directory, **outside original AU-ASM,
AU-How, other site cases, forcing and inputdata**. Check mode performs
read-only tool/import/template and Stage15 source checks; reference
build mode needs exact operator confirmation. It inventories actual
newly generated `PCT_NAT_PFT` (host index0 bare), natural land fraction,
sand/clay and organic layers and records source SHA256 and output SHA256.
The output is **a gridded CTSM reference point subset**, not an observed
Mulga canopy/C3/C4/ground-cover or 10-layer site-specific soil
prescription, and no original point surface or model case is modified.

Recommended IRIDIS6 invocation (first `--check`, then OPTIONAL
reference-only build with explicit consent):

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/b2bdae2d68c39f5b14bed19fac06aa8b8490425b/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage16_code"
SCRIPT="$CODE/ozflux_stage16_surface.py"
OUT="$HOME/ozflux_stage16_reference_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage16/16_asm_isolated_CTSM2000_reference_point_surface.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "962c5d220b32b51c750654dd371f99e5e2e18aa0"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --check --out "$OUT"
# Only after successful read-only preflight, create a new REFERENCE surface:
python3 -B "$SCRIPT" --build-reference \
  --confirm CREATE_ISOLATED_AU_ASM_REFERENCE_SURFACE_ONLY --out "$OUT"
)
~~~

Outputs `stage16_AU_ASM_REFERENCE_SURFACE_NOT_MODEL_APPROVED.json`,
one `surfdata*.nc` and generated CTSM `user_mods` under `$OUT`.
Do not put the generated reference in an active CLM namelist,
nor modify its PFT or soil values without first choosing an explicitly
versioned site-science model-hypothesis vector. Before any CIME case,
compare actual reference bare/PFT/soil against independent Mulga site
observations, compiled FATES-PFT mapping and soil-layer evidence.

**Stage16 bugfix (2026-11-02, first operator check failed safely before any output):**
The original strict text.count of the literal `dir = .../ctsm5.4.0`
over the **entire** CTSM default template demanded exactly one occurrence.
Depending on installed CTSM, `[surfdat]` may already be `ctsm5.3.0`,
the config spacing may differ, or `[landuse]` may repeat the same
directory. This can fail even when the intended reference inputdata is
present. Updated Stage16 (commit `b2bdae2d68c39f5b14bed19fac06aa8b8490425b`,
blob `962c5d220b32b51c750654dd371f99e5e2e18aa0`) now edits
**only the unique `[surfdat]` section**: one `dir`, one
`surfdat_16pft`, one `mesh_surf`, pinning exact inputs already checked
by Stage15. Leaves `[landuse]` and all other config sections untouched.
The self-test now covers duplicate directory references in different
sections, an already 5.3.0 surface dir, spacing differences, and missing
required keys. **No reference surface was made during the failed check.**
## 3r. Stage16 reference surface SUCCESS; Stage17 exact PFT/soil vs Mulga science gate

**2026-11-02 Stage16 actual operator run SUCCESS** after the `[surfdat]`-scoped config fix. Pinned config SHA256 `e700b675bc9a461b53cf353d075250534515c5a965b343da2373554504abe254`. Independent isolated CTSM-2000 point surface under:
`/home/ly3n24/ozflux_stage16_reference_20261102T023647Z/surfdata_AU-ASM_hist_2000_16pfts_c261102.nc`.
SHA256 `18edace32d8e356c7d73269329dca7ed6338140e1ad1456f1a88691522c307fa`.
No `--dompft`, no PFT override, no source replacement, no CIME/Slurm, **science_approval=False**.

**Observed reference CTSM natural PFT vector** (all fractions percent of natural land, distinct from non-natural landunits): bare 34.88629579, all tree 2.60101737, shrubs 41.58592876, C3 grass 0.04086810, C4 grass 20.88588998. Landunits: PCT_NATVEG 99.99938922% and crop 0.00061078%. This is a gridded CTSM reference input, NOT a measured tower-footprint Acacia/shrub/bare composition. The ~2.6% generic grid-tree representation is in clear tension with a field plot survey cited in the thesis reporting ~74.5% of plot area occupied by Acacia, but **the survey and model host natural-PFT denominators, periods and sampling domains are different and must not be equated**.

**Reference 10-layer soil** is exceptionally sandy: sand [90,90,90,90,89,89,90,90,90,90]%; clay [6,6,6,6,7,7,7,7,7,7]%; ORGANIC [6.844117,6.844117,6.844117,6.844117,4.859421,3.795641,2.863758,1.688834,1.789572,1.789572] (CTSM units; not soil carbon %, see NetCDF attributes). A published Mulga site description reports red Kandosol sand:silt:clay 74:11:15; the older OzFlux website reports 50:50 sand:clay. Neither is a site-verified **10-layer** CLM texture vector. The reference gridded soil is internally valid but cannot automatically be called tower-representative.

**Stage17 science gate**: `scripts/stage17/17_asm_reference_surface_vs_site_PFT_soil_FATES_gate_readonly.py`, commit `8aee7e87a3b299550e75d4283f901dd41c1d499f`, blob `4aa1aac58d0847441983516d96a35af069866185`. It reads the exact hashed Stage16 surface and Stage16 receipt, writes a full host PFT 0–14 (or 15 when present) reference table, and a 10-layer soil reference-vs-site-bulk comparison. Optionally accepts `--fates-params /EXACT/PATH/fates_params.nc` to inspect **the actual** `fates_hlm_pft_map` matrix without guessing its orientation or active FATES PFT indices. Never edits source, surface, FATES parameters, or Slurm.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/8aee7e87a3b299550e75d4283f901dd41c1d499f/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage17_code"
OUT="$HOME/ozflux_stage17_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage17/17_asm_reference_surface_vs_site_PFT_soil_FATES_gate_readonly.py" -o "$CODE/ozflux_stage17.py"
test "$(git hash-object "$CODE/ozflux_stage17.py")" = "4aa1aac58d0847441983516d96a35af069866185"
python3 -B -m py_compile "$CODE/ozflux_stage17.py"
python3 -B "$CODE/ozflux_stage17.py" --self-test
python3 -B "$CODE/ozflux_stage17.py" --out "$OUT"
echo "STAGE17 report: $OUT"
)
~~~

Outputs: `stage17_AU_ASM_host_PFT_exact.tsv`, `stage17_AU_ASM_soil10_grid_vs_site_bulk.tsv`, `stage17_AU_ASM_PFT_soil_science_gate.json`. Stage17 **does not approve** PFT fractions, 10-layer soil or the active FATES HLM-PFT map.

Primary ecology refs: https://opus.lib.uts.edu.au/bitstream/10453/133258/2/02whole.pdf ; https://ozflux.org.au/monitoringsites/alicesprings/alicesprings_description.html . Host-to-FATES matrix ref: https://fates-users-guide.readthedocs.io/en/latest/user/HLM-FATES-PFT-map.html .

## 3s. Stage17 operator success; Stage18 actual FATES PFT parameter mapping gate

**Stage17 actual IRIDIS6 PASS 2026-11-02** with SHA-verified Stage16 reference surface and complete PFT/soil report in /home/ly3n24/ozflux_stage17_20261102T025047Z. Host natural PFT composition was 34.886295790% bare (host0), 0.839963621% tropical evergreen broadleaf tree (host4), 1.734531508% temperate evergreen broadleaf tree (host5), 0.026522242% deciduous temperate tree (host7), 41.585928756% **deciduous temperate shrub (host10)**, 0.040868100% C3 non-arctic grass (host13) and 20.885889983% C4 grass (host14). The grid host10 is not host9 evergreen shrub. The default FATES map may translate it to cold-deciduous shrub, which is not necessarily appropriate for arid-zone Mulga; **actual selected FATES parameter and simulation mode are unknown**.

Ten gridded soil layers: sand 90,90,90,90,89,89,90,90,90,90%; clay 6,6,6,6,7,7,7,7,7,7%. Layer means 89.8% sand, 6.6% clay vs published site-bulk 74% sand and 15% clay. Do not assign 74/15 to every model layer without independent profile evidence. The earlier plot-study Acacia cover 74.5% does not use the same denominator/domain as the host natural-PFT vector.

**Stage18 read-only discovery** at scripts/stage18/18_asm_actual_fates_parameter_map_and_surface_decision_readonly.py, pinned commit 17a34bfced799ca5d7bebc4fc624c89e5325a70c; Git blob SHA 24b07ce73aa2ea85f567d52d3e4da70f6bdc1eec. It SHA-verifies the Stage16/17 source reports, searches only bounded FATES parameter directories, understands .json/.nc/.cdl, inventories HLM-PFT mapping dimensions/nonzero entries and candidate source file hashes, and inspects an older AU-How case for **reference only**. Explicit --params and --case arguments allow known additional sources. No active AU-ASM parameter, map orientation or modeling mode is assumed, and no surface/forcing/CIME files are changed.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="17a34bfced799ca5d7bebc4fc624c89e5325a70c"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage18_code"
SCRIPT="$CODE/ozflux_stage18.py"
OUT="$HOME/ozflux_stage18_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage18/18_asm_actual_fates_parameter_map_and_surface_decision_readonly.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "24b07ce73aa2ea85f567d52d3e4da70f6bdc1eec"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "STAGE18 REPORT: $OUT"
)
~~~

Reference: https://fates-users-guide.readthedocs.io/en/latest/user/HLM-FATES-PFT-map.html and https://ncar.github.io/CESM-Tutorial/notebooks/challenge/clm_ctsm/clm_exercise_3.html . Science approval remains FALSE; no new surface or AD400 submission.

## 3t. Stage18 operator success; Stage19 FATES default JSON structure and model-mode forensics

**Stage18 operator output 2026-11-02:** `/home/ly3n24/ozflux_stage18_20261102T030211Z`. Stage16 reference surface SHA256 verified, and one local FATES parameter candidate actually exists:
`/iridisfs/scratch/ly3n24/CLM_FATES/CTSM/src/fates/parameter_files/fates_params_default.json`;
SHA256 `0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04`.
Stage18 reports `MAP FOUND: False` **only after checking top-level JSON keys**; this does not prove the JSON lacks nested mapping fields. One pre-existing reference case `AU-How_FATES_1PT` had its effective `CaseDocs/lnd_in` setting `fates_paramfile` to this exact path, with `use_fates_nocomp = .false.`; that setting is evidence for the **AU-How example ONLY**, not a newly selected AU-ASM run mode. No AU-ASM case or FATES parameter is approved.

FATES upstream documentation states that `fates_hlm_pft_map` is used for fixed biogeography and no-competition input mapping, whereas a full competition case may not prescribe the patch fractions the same way. A default mapping has host10 broadleaf deciduous temperate shrub potentially linked to cold-deciduous extratropical shrub, but **the model's actual parameter file has not yet demonstrated that map**. Do not silently assign the 41.5859% host10 fraction to an arid-zone hydrodeciduous Mulga shrub. Use `--params` only for exact known source path and continue separating host index labels from FATES PFT indices.

**Stage19 read-only**: `scripts/stage19/19_asm_fates_json_structure_and_mode_forensics_readonly.py`, commit `379afddaa5023b872fd5fc4f435601a132ce9a3d`, git blob SHA `b31830f2b8cac01e4034d9c01d4fbad1caa33a38`. Verifies the original JSON SHA256 and the Stage18 report and then recursively explores FATES parameter keys, including nested `fates_hlm_pft_map`, PFT names, PFT dimensions and selected init parameters. Reports **true missing** if absent at all inspected JSON levels. Reads older AU-How CaseDocs mode and param references, never assumes this applies to AU-ASM. Only new HOME JSON report is written, no Surface/FATES parameters/CIME/Slurm changes.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="379afddaa5023b872fd5fc4f435601a132ce9a3d"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage19_code"
SCRIPT="$CODE/ozflux_stage19.py"
OUT="$HOME/ozflux_stage19_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage19/19_asm_fates_json_structure_and_mode_forensics_readonly.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "b31830f2b8cac01e4034d9c01d4fbad1caa33a38"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "REPORT_DIR: $OUT"
)
~~~

Science gate remains **HOLD**: do not generate assumed Mulga PFT fractions or ten soil layers, do not launch CIME/Slurm. Next action is choose a transparent competition vs fixed mode and evaluate calibrated local woody PFT/soil scenarios, with separate source-preserving reference experiments.

## 3u. Stage19 actual FATES HLM 14x14 map FOUND; Stage20 mode and site-science decision

**Operator Stage19 SUCCESS (2026-11-02)**:
`/home/ly3n24/ozflux_stage19_20261102T031102Z`.
Verified local JSON SHA256 `0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04`.
The JSON top-level schema is exactly `attributes, dimensions, parameters`,
so Stage18 top-level-only map search returned a **false negative**.
The ACTUAL local mapping is at `parameters.fates_hlm_pft_map`,
dimensions `[fates_hlm_pftno, fates_pft]`,
shape **14×14**. The 14 exact FATES names are in
`parameters.fates_pftname.data`. The rows correspond to
host natpft indices **1–14**; host natpft0 is bare/nonvegetated and
has no row. Source matrix entries are pinned to the local JSON, **not
generic online docs**, which may reflect different versions.

Selected exact host-to-FATES assignments in this JSON:
- host4 (tropical evergreen broadleaf) -> 1-based FATES1
  `broadleaf_evergreen_tropical_tree`.
- host5 (temperate evergreen broadleaf) -> FATES4
  `broadleaf_evergreen_extratrop_tree`.
- host7 (temperate deciduous broadleaf) -> FATES6
  `broadleaf_colddecid_extratrop_tree`.
- host10 (temperate deciduous broadleaf shrub) -> **FATES9
  `broadleaf_colddecid_extratrop_shrub`** (0-based mapping row9,
  0-based FATES column8). **FATES8** in the same JSON is
  `broadleaf_hydrodecid_extratrop_shrub` but is **not the target
  for host10**. The initial Stage20 code mistakenly asserted column7;
  operator preflight correctly halted before writing reports or cases.
- host13 -> FATES13 `cool_c3_grass`; host14 -> FATES14
  `c4_grass`.
- Host11 (boreal deciduous shrub, 0% in this reference surface) splits
  three FATES shrub types with weights 0.1, 0.1 and 0.8,
  demonstrating this is a *fractional matrix*, not a universal
  one-to-one PFT number conversion.

Reference AU-How `CaseDocs/lnd_in` explicitly has
`use_fates=.true.`, `use_fates_fixed_biogeog=.false.`,
`use_fates_nocomp=.false.`: Full FATES with PFT
competition, **not** no-competition/fixed biogeography.
The **exact 14x14 fixed-biogeography map remains a valid potential
future fixed-PFT mapping, but the reference Surface's natural-PFT
percentages are NOT the fixed areas maintained by this Full FATES
competition configuration**. No AU-ASM CIME mode has been selected.

**Stage20 independent reconciliation** (read-only):
`scripts/stage20/20_asm_exact_host_to_fates_mapping_mode_and_soil_strategy_readonly.py`
CORRECTED pinned commit `6451009636a90de39a713cfed0fbf7a7678dfee4`,
Git blob `861dde532cd329ec37529c225d36361f1663b0fe`.
It compares SHA-pinned Stage19 JSON against exact Stage16 surface,
validates each of 14 mapping rows sums to 1,
prints the full host->FATES table and **hypothetical fixed-biogeography
areas only**; verifies existing AU-How's three namelist flags,
audits parameter PFT-dimensional trait names and records soil
reference-vs-field assumptions. No new Surface, FATES parameter, case
or Slurm job.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="6451009636a90de39a713cfed0fbf7a7678dfee4"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage20_code"
SCRIPT="$CODE/ozflux_stage20.py"
OUT="$HOME/ozflux_stage20_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS "$BASE/scripts/stage20/20_asm_exact_host_to_fates_mapping_mode_and_soil_strategy_readonly.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "861dde532cd329ec37529c225d36361f1663b0fe"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

Outputs: `stage20_AU_ASM_exact_host_to_FATES_mapping.tsv` and
`stage20_AU_ASM_exact_mode_PFT_soil_science_gate.json`.
After Stage20, prefer a deliberate scientific modeling choice:
(A) Full FATES competition *reference* trial consistent with AU-How's
mode, treating existing gridded site surface as a nonrepresentative
baseline; versus (B) prescribed-biogeography/nocomp hypotheses
requiring scientifically justified woody/C3/C4/bare fractions, ten-layer
soil and careful default traits. These are **experimental design
alternatives**, not pre-approved runs. Existing Stage14 FSDS0
forcing is preserved and not modified. **No AD400 authorisation**.

Official mode behavior:
https://fates-users-guide.readthedocs.io/projects/tech-doc/en/stable/fates_tech_note.html

**Stage20 first operator attempt (2026-11-02) STOPPED safely**:
code SHA, syntax and self-test passed, but the initial run halted with
`ValueError: Expected mapping entry drifted`. This was a **script
regression, not actual source drift**. The author had misread source
mapping row9/col8 as row9/col7. Corrected Stage20 now
requires source-verified host10 -> FATES9 colddeciduous shrub,
reports detailed per-row mappings for any future drift,
and regression-tests that FATES8 is not the actual host10 target.
Neither the failed preflight nor corrected code changes original
FATES JSON, Stage16 surface, DATM, CIME cases or Slurm.

## 3v. Stage20 actual SUCCESS; Stage21 FATES PFT trait and mode science review (READ ONLY)

**Operator Stage20 verified SUCCESS 2026-11-02**:
`/home/ly3n24/ozflux_stage20_20261102T032403Z`.
Pinned local FATES JSON SHA256 `0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04`
and CTSM reference surface SHA256
`18edace32d8e356c7d73269329dca7ed6338140e1ad1456f1a88691522c307fa`
both unchanged. The true 14x14 mapping has row sum 1 for every host1..14.
All 15 host natural-PFT fractions sum to 100; host0 is 34.88629579%
bare and the hypothetical fixed-biogeography FATES vegetated area
is 65.11370421% natural land. In the reference surface:
- host4 0.839963621 -> FATES1 broadleaf evergreen tropical tree;
- host5 1.734531508 -> FATES4 broadleaf evergreen extratropical tree;
- host7 0.026522242 -> FATES6 broadleaf cold-deciduous tree;
- host10 **41.585928756 -> FATES9 broadleaf cold-deciduous extratropical shrub**;
- host13 0.040868100 -> FATES13 cool C3 grass;
- host14 20.885889983 -> FATES14 C4 grass.
Those percentages apply ONLY under a hypothetical prescribed-areas
scenario. They are not predicted current/Future Full-FATES cover.
**214** parameter entries in the actual default JSON are dimensioned
by `fates_pft`.

The older AU-How case used `use_fates=.true.`,
`use_fates_fixed_biogeog=.false.`,
`use_fates_nocomp=.false.`: a Full FATES competition
example. This does NOT establish AU-ASM's run mode.
Official FATES documentation distinguishes:
- **Full FATES:** competition and dynamic vegetation; the 14x14
  matrix does not prescribe fixed area proportions.
- **Fixed biogeography with competition:** eligible PFTs constrained
  by inputs; competition can change area proportions.
- **Fixed biogeography + nocomp:** each PFT allocated prescribed area;
  the original host0 bare is non-vegetated, not a FATES canopy type.
See https://fates-users-guide.readthedocs.io/projects/tech-doc/en/stable/fates_tech_note.html .

**Science priority:** Since Acacia aneura/aptaneura is evergreen
woodland (not a northern-hemisphere winter-deciduous shrub) and
the site has C3/C4 understory plus seasonally bare ground, compare
actual FATES1/4 evergreen trees, FATES7 evergreen shrub,
FATES8 hydrodeciduous shrub, FATES9 colddeciduous shrub and FATES13/14
C3/C4 grasses in the **actual pinned JSON**, including
phenology, leaf hydraulics, root/allometry and drought/stomatal traits.
The gridded 89.8% sand/6.6% clay 10-layer reference and field red
Kandosol bulk ~74/11/15 (sand/silt/clay) should remain independent
input hypotheses, not silently substituted in every soil layer.
Acacia plot ~74.5% cover is a separate spatial denominator, NOT a
ready-made host PFT area vector.
Primary sources:
https://portal.tern.org.au/metadata/7d9d2f7f-794c-41f5-b5e1-d5b58fc08743 ;
https://opus.lib.uts.edu.au/bitstream/10453/133258/2/02whole.pdf ;
https://data.ozflux.org.au/pub/viewDatasetData.jspx?collection.id=152&collection.owner.id=101&dataset.id=3181165&viewType=anonymous .

**Stage21 code published, NOT yet run**:
`scripts/stage21/21_asm_mulga_FATES_actual_trait_mode_scenario_science_gate_READONLY.py`,
corrected commit `f7ffe64e7674b8fb4434f1f676d3afcb7caf3928`,
Git blob `231606efdb552960b751f67e23fdd5dc8ae3b8ae`.
This requires and rehashes Stage20 actual operator JSON, Stage14
forcing science manifest and the original FATES JSON source.
It creates an all-214-field TSV and a filtered phenology,
hydraulic, rooting, photosynthesis and allometry trait comparison
for FATES PFT1/4/7/8/9/13/14, plus three explicit
model experiment design hypotheses with approvals FALSE.
No NetCDF, JSON parameter, case or Slurm modification.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="f7ffe64e7674b8fb4434f1f676d3afcb7caf3928"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage21_code"
SCRIPT="$CODE/ozflux_stage21.py"
OUT="$HOME/ozflux_stage21_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage21/21_asm_mulga_FATES_actual_trait_mode_scenario_science_gate_READONLY.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "231606efdb552960b751f67e23fdd5dc8ae3b8ae"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "STAGE21 REPORT_DIR: $OUT"
)
~~~

Outputs: `stage21_all_214_FATES_traits_PFT1_4_7_8_9_13_14.tsv`,
`stage21_priority_FATES_phenology_hydraulics_trait_comparison.tsv`
and `stage21_AU_ASM_Mulga_trait_mode_science_gate.json`.
**No AU-ASM mode, Mulga surface fraction or 10-layer soil scenario
approved. No new cases and no AD400 submission.**

**Stage21 initial operator self-test FAILED SAFELY (2026-11-02):**
source SHA and syntax both passed, but `extract_pft_axis()`
attempted `selected.tolist()` on a Python scalar returned by
`np.take(object_dtype_array, scalar_index)`. This raised
`AttributeError` before **any** real FATES JSON parsing,
report creation, NetCDF write or model submission.
**No FATES trait result or Stage21 SUCCESS was established.**
Corrected Stage21 now converts via `np.asarray(selected).tolist()`,
handling native integer/float/string/bool scalar values as well
as arrays; regression tests cover fates_pft as first/last axis and
malformed shapes. The corrected source is pinned above. Stage20's
verified input science remains valid, without rerun.

## 3w. Stage21 operator SUCCESS — extract actual 8 phenology values before Mulga PFT choice

**2026-11-02 operator Stage21 actual PASS** (after native Python
scalar-to-list correction): source SHA verified, Python syntax PASS,
expanded 1-D/2-D regression self-test PASS, and the real original FATES
JSON SHA256 `0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04`
and Stage20 report SHA256
`76397fa3c93df57a99d57ca0cc1ee4c4c093d7e10c13493060b4d65507246ab9`
verified. Output:
`/home/ly3n24/ozflux_stage21_20261102T105344Z`.
**214 FATES PFT-dimensioned parameters extracted, 126 priority,
8 phenology, 0 extraction errors** from
`stage21_all_214_FATES_traits_PFT1_4_7_8_9_13_14.tsv`.
The narrowed `stage21_priority_FATES_phenology_hydraulics_trait_comparison.tsv`
was created too. All three experiment hypotheses still have
`approved_for_case=False`; no site-specific surface, CIME case or
Slurm job created. No AD400.

The **8 actual FATES phenology parameter names** are:
`fates_phen_cold_size_threshold`,
`fates_phen_drought_threshold`,
`fates_phen_flush_fraction`,
`fates_phen_fnrt_drop_fraction`,
`fates_phen_leaf_habit`,
`fates_phen_mindaysoff`,
`fates_phen_moist_threshold`,
`fates_phen_stem_drop_fraction`.

**Important evidence limit:** Stage21 operator pasted the parameter
names and successful counts, **not the individual values for FATES4,
7, 8 and 9**. Therefore it is premature to declare a new Acacia
PFT mapping, switch the cold-deciduous shrub to hydro-deciduous,
or approve a change in tree/shrub/bare-ground fractions. Next retrieve
the exact unmodified TSV columns with a read-only command and inspect
the relevant model phenology code/parameter definitions before making
a site-specific scenario. Avoid re-running Stages12–21.

The local fixed-biogeography host10 -> FATES9 cold-deciduous shrub
mapping is verified; the earlier AU-How example uses Full FATES
competition. Neither mode nor soil profile is selected for AU-ASM.
Site-level Kandosol texture 74/11/15 is not a ten-layer soil profile,
and the CTSM gridded sand ~89.8 / clay ~6.6 remains only a baseline
reference.

## 3x. Stage21 actual phenology values; Stage22 evergreen Mulga candidate functional traits

**Operator direct read of Stage21 TSV (2026-11-02):** All **8** FATES
phenology parameter values successfully reported for default
PFT4 evergreen extratropical broadleaf tree, PFT7 evergreen extratropical
broadleaf shrub, PFT8 hydrodeciduous extratropical shrub and PFT9
cold-deciduous extratropical shrub. In the original SHA-pinned JSON,
`fates_phen_leaf_habit` is respectively **1,1,3,2**:
1=evergreen, 2=cold-season deciduous, 3=hydro/stress deciduous.
`fates_phen_flush_fraction` is **null** for PFT4/PFT7,
0.5 for PFT8/PFT9; null is not scientific evidence for zero.
`fates_phen_drought_threshold` is -152957.4 (source units mm
water-column matric potential, **not** positive volumetric soil water)
for all four. `fates_phen_moist_threshold` is -122365.9;
cold-size threshold 0 cm; fine-root and stem phenology drop
fractions 0; minimum leafless days 100. The same numerical drought
threshold may be inactive under evergreen phenology; do NOT claim
all PFTs exhibit drought-triggered leaf-drop. As of Stage21, Mulga
PFT type, active model mode and all soil values remain unapproved.

Ecological interpretation: AU-ASM's dominant mixed Acacia canopy is
evergreen, median canopy height ~4.3m (TERN); PFT4 is the first
**tree-structure/evergreen** working candidate, PFT7 the
**shrub-structure/evergreen** sensitivity candidate. PFT8 is a
stress-deciduous shrub comparator; the gridded host10 -> FATES9
cold-deciduous shrub should NOT automatically represent evergreen
Mulga. This selects *candidates only*: foliage habit does not establish
root/hydraulic/allometric physiology, actual site PFT cover,
FATES competition dynamics or a complete 10-layer red Kandosol.
References: https://portal.tern.org.au/metadata/TERN/608dca79-0ec8-412d-9f13-71f7714affac ;
https://fates-users-guide.readthedocs.io/projects/tech-doc/en/stable/fates_tech_note.html .

**Stage22 read-only** `scripts/stage22/22_asm_mulga_evergreen_PFT4_vs_PFT7_actual_traits_gate_READONLY.py`
(commit `477de28c0056b2da83ec1ea4c244eae60d1ca074`,
git blob `6cf8029180927aeb139872b77e61cf6cfeeb7b9b`).
Checks Stage21 receipt SHA and source FATES JSON, loads the actual 214
extracted trait values, insists on leaf-habit 1/1/3/2 and null
flush for PFT4/7, then writes only a fresh HOME directory with an
exact selected PFT4/7/8/9 trait-value TSV and an unsigned science
decision JSON. The review focuses on height/crown allometry, fine-root
and hydraulic traits, Vcmax, stomatal response and water-stress
configuration before any arbitrary PFT fractions are chosen.
**No** NetCDF source or compiled JSON changes, new surface, model
case, Slurm or AD400.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="477de28c0056b2da83ec1ea4c244eae60d1ca074"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage22_code"
SCRIPT="$CODE/ozflux_stage22.py"
OUT="$HOME/ozflux_stage22_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage22/22_asm_mulga_evergreen_PFT4_vs_PFT7_actual_traits_gate_READONLY.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "6cf8029180927aeb139872b77e61cf6cfeeb7b9b"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

Review the actual values in
`stage22_actual_FATES4_7_8_9_trait_comparison.tsv` and science flags in
`stage22_AU_ASM_Mulga_evergreen_PFT_science_gate.json`.
Do not infer PFT area fractions from stand or plot-level Acacia
cover, nor set 74% sand, 15% clay into all 10 CLM soil layers without
vertical evidence. Stage14 FSDS0 forcing and Stage16 reference surface
remain provisional and immutable, and no AD400 is authorized.

## 3y. Stage22 operator actual SUCCESS; Stage23 source-code allometry/hydraulic forensic gate

**Stage22 actual operator SUCCESS 2026-11-02**:
`/iridisfs/home/ly3n24/ozflux_stage22_20261102T112126Z`.
Operator verified Stage21 TSV SHA256
`2ce8e2e0eba38bf284b67ddb73ffc54f4392105c6a35de0eeb44e49ec1c7b85d`.
Reviewed **35** actual PFT traits, **8** phenology. FATES4 vs
FATES7 differed in **11** fields: `allom_d2h1/2/3`,
`allom_dbh_maxheight`, `allom_fnrt_prof_b`,
`allom_zroot_min_dbh/max_dbh`, `leaf_slamax/slatop`,
`leaf_stomatal_slope_medlyn`, and `leaf_vcmax25top`.
FATES4 vs FATES7 evergreen leaf habit both 1, but major structural,
rooting and leaf geometry differences.

Exact selected values (FATES4 tree vs FATES7 shrub):
- `fates_allom_d2h1`: 104.3586841 vs 0.64
- `fates_allom_d2h2`: 1.1146973 vs 0.37
- `fates_allom_d2h3`: 160.6835089 vs **-999.9**
  (treat as possible sentinel until actual code/mode verified)
- `fates_allom_dbh_maxheight`: 1000 vs 3 **cm DBH** (not height)
- `fates_allom_fnrt_prof_b`: 1 vs 1.5
- `fates_leaf_slatop`: 0.009 vs 0.012 m2/gC
- `fates_leaf_slamax`: 0.0954 vs 0.012 m2/gC
- `fates_leaf_stomatal_slope_medlyn`: 4.1 vs 4.7
- `fates_leaf_vcmax25top`: [61] vs [62] µmol CO2 m-2 s-1

All four reviewed PFTs shared defaults
`fates_hydro_p50_gs=-1.5 MPa`,
`fates_hydro_p50_node=[-2.25,-2.25,-2.25,-2.25] MPa`,
`fates_hydro_kmax_node=[-999,3,-999,-999]`,
and `fates_leaf_stomatal_btran_model=1`.
This **does not** demonstrate that Acacia is actually represented
with site-realistic drought hydraulics, or that -999 values are active
physical traits. Root `zroot_min_z=max_z=100m` in defaults cannot
be interpreted as verified actual root depth. Need the active root/
hydraulic mode and source code before interpreting.

External study: Creek et al. (2018), doi 10.1111/pce.13418,
reported *Acacia aneura* leaf/stem/root Ψ50 respectively
-5.84/-8.46/-8.16 MPa. Treat only as **literature context**:
the dataset's species/site, the measured organ-specific conductivity
and FATES parameter's node/root/gs semantics are not established as
identical. Do NOT copy empirical P50 into all nodes; use it to
prioritize model-mode checks and site-specific calibration.
Ref: https://onlinelibrary.wiley.com/doi/full/10.1111/pce.13418 .
FATES mainline height allometry wrapper dispatches on
`allom_hmode` and uses `allom_dbh_maxheight` as a diameter cap,
not as maximum canopy height:
https://github.com/NGEET/fates/blob/main/biogeochem/FatesAllometryMod.F90 .
Actual IRIDIS6 checked-out source must be read before evaluating H(DBH).

**Stage23 read-only**:
`scripts/stage23/23_asm_Mulga_height_hydraulics_FATES_local_code_forensics_READONLY.py`,
commit `bb324aac04f8648c8d88821746ffbe0b74c09fee`,
Git blob `0c55ac00531e4a751f6091dc5304d1e91888372e`.
It verifies Stage21/22 evidence and original FATES JSON hashes,
reads the actual `fates_allom_hmode` and related allometry/root/
hydraulic parameters for PFT4,7,8,9, shallow-searches actual local
FatesAllometryMod and related Fortran modules, records their SHA256 and
matching code excerpts, and registers literature P50 strictly as an
unmatched research comparator. **No heights, PFT fractions or
soil layers are inferred; no FATES/Surface/source writes.**
Reports: `stage23_AU_ASM_PFT4_7_8_9_allometry_hydraulic_traits.tsv`,
`stage23_AU_ASM_actual_allometry_source_science_hold.json`.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="bb324aac04f8648c8d88821746ffbe0b74c09fee"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage23_code"
SCRIPT="$CODE/ozflux_stage23.py"
OUT="$HOME/ozflux_stage23_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage23/23_asm_Mulga_height_hydraulics_FATES_local_code_forensics_READONLY.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "0c55ac00531e4a751f6091dc5304d1e91888372e"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

**Experiment design gate remains HOLD:** standalone Full-FATES reference,
candidate Acacia evergreen PFT4 vs PFT7 traits, root hydraulics,
C3/C4/bare area assumptions, Kandosol 10-layer profiles and final
forcing science are not approved for CIME/AD400. Stage23 is discovery,
not simulation.

## 3z. Stage23 operator SUCCESS, exact local source SHA known; Stage24 formula-verified H(DBH) read-only

**Actual Stage23 operator PASS 2026-11-02**:
`/home/ly3n24/ozflux_stage23_20261102T114525Z`.
Stage21 214-trait TSV SHA256
`2ce8e2e0eba38bf284b67ddb73ffc54f4392105c6a35de0eeb44e49ec1c7b85d`
and default FATES JSON SHA256
`0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04`
verified. 20 targeted trait fields found, only
`fates_allom_rmode` missing from the optional target-name inventory.
This **does not establish absent root physics or erroneous source
parameters**; `fates_allom_fnrt_prof_mode` was present in Stage22.

**Actual modes**:
`FATES4 allom_hmode=5` (Martinez-Cano, evergreen
extrapropical tree), while `FATES7/8/9 allom_hmode=1` (O'Brien,
evergreen/hydro/cold shrub). Found local installed Fortran:
`/iridisfs/scratch/ly3n24/CLM_FATES/CTSM/src/fates/biogeochem/FatesAllometryMod.F90`,
SHA256
`8ad6c9eaaa9f5c40036f8aa099f6435b80f2a8e7248a48b6ddb3a978db3c7f16`.
Stage23 did not evaluate heights, modify anything, or authorize
model runs.

Independent upstream FATES `h_allom` source inspection finds
- Mode 1 `d2h_obrien`:
  `h = 10**(log10(min(d,dbh_maxh))*p1+p2)`
- Mode 5 `d2h_martcano`:
  `h = (p1*min(d,dbh_maxh)**p2)/(p3+min(d,dbh_maxh)**p2)`
- `d` is DBH in **cm**; `h` in **m**.
Source: https://github.com/NGEET/fates/blob/main/biogeochem/FatesAllometryMod.F90 .
**Do not compute actual source-validated curves unless the frozen
IRIDIS6 Fortran is independently checked to contain these exact
two functional statements and mode dispatch.** Upstream mainline
is not guaranteed identical to local pinned SHA.

**Stage24 published**:
`scripts/stage24/24_asm_local_FATES_verified_height_DBH_curve_READONLY.py`;
commit `0b9a61afc1b6b23b3dc0304d72fc2ed12b913578`,
Git blob `2284d17cfe6c7112605e3c1fea739b9fe141346c`.
It validates exact Stage23 receipt, local Fortran SHA and original JSON
SHA, then checks the mode 1 and 5 local dispatch and actual height
expression strings **before** evaluating the 0.5–50 cm DBH comparison.
It computes the inverse diameter for an illustrative 4.3m reference
canopy height and the FATES7 plateau at `dbh_maxheight=3cm`.
These are **structural allometry outputs**, not tower-measured DBH,
flux predictions or FATES growth/competition simulations.
If local code differs, Stage24 fails closed before report creation.
It writes only new HOME TSV + JSON, never original input/params/cases/
Slurm/AD400.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="0b9a61afc1b6b23b3dc0304d72fc2ed12b913578"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage24_code"
SCRIPT="$CODE/ozflux_stage24.py"
OUT="$HOME/ozflux_stage24_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage24/24_asm_local_FATES_verified_height_DBH_curve_READONLY.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "2284d17cfe6c7112605e3c1fea739b9fe141346c"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

After Stage24 compare both curves with site *canopy-height
distribution and measured DBH distribution*, not one site mean alone.
Record species-specific allometry uncertainties, and do not infer
FATES4 is objectively superior to FATES7 simply because the
model's generic allometric height crosses 4.3 m.
PFT fractions, source forcing QC signoff, soil ten-layer parameters
and AU-ASM CIME mode remain science HOLD.

## 3aa. Stage24 operator SUCCESS; field stem DBH and leaf traits now available for direct model evaluation

**Actual Stage24 operator PASS (2026-11-02)**:
`/home/ly3n24/ozflux_stage24_20261102T115254Z`.
FATES source Fortran SHA256
`8ad6c9eaaa9f5c40036f8aa099f6435b80f2a8e7248a48b6ddb3a978db3c7f16`;
original FATES JSON SHA256
`0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04`.
The installed **local** h_allom mode5 Martinez-Cano and mode1
O'Brien formulas and dispatch were verified before calculating curves.
At site canopy height reference **4.3 m**, model formula inverse DBH:
FATES4 5.660263445 cm, FATES7 2.580295600 cm.
FATES7 (O'Brien with `allom_dbh_maxheight=3cm`) has a
height plateau **4.735410175 m at DBH≥3cm**.
FATES4 can reach 4.3m at 5.66cm DBH. At 10cm DBH FATES4
predicts 7.823676m while FATES7 stays at 4.73541m.
These are structural model formula values, not measured DBH or model runs.
Stage24 writes no original sources and approves no case/AD400.

**New, more discriminating external site evidence**:
1. The TERN 2026_v3 Mulga flux collection reports **median canopy
   height 4.3m, tallest trees 8.9m**, mixed Acacia aneura/aptaneura
   woodland and **total standing biomass 32.5t/ha** (NOT automatically
   equivalent to aboveground woody biomass/cAGB).
   https://portal.tern.org.au/metadata/TERN/608dca79-0ec8-412d-9f13-71f7714affac
   The historical OzFlux site page separately says **mean height 6.5m**,
   which is not the same statistic/measurement period as the median.
   https://ozflux.org.au/monitoringsites/alicesprings/alicesprings_description.html
   The FATES7 default height plateau 4.735m CANNOT represent the
   highest 8.9m trees, while FATES4 reaches 8.9m at a structural-model
   DBH of ~11.339cm. This is stronger evidence of tree allometry
   suitability but does not itself validate the PFT.
2. A 2014 **direct DBH** core plot dataset located ~130–250m from
   tower within its footprint reports **200 stems** (>1cm DBH)
   from **86 trees**: 154 stems (1–5cm), 27 (5–10cm), 19 (>10cm).
   Source metadata:
   https://researchdata.edu.au/vegetation-data-direct-ha-2014/617073
   **Many stems per tree, not 200 independently measured trees**;
   the files/paired individual heights have not been fetched or QCed.
3. Another separate TERN **2014 stem diameter/height/woody biomass**
   release gives an original CSV and data dictionary:
   https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed
   Its documented diameter is **basal D20 at 20cm height, NOT DBH**.
   Comparing D20 directly against the FATES input DBH is invalid
   unless a field-supported conversion is available. The 2018 values
   may derive from increment estimates rather than remeasured stems;
   check release/lineage before using them.
4. TERN **Alice Mulga Leaf Functional Trait Data, 2014**:
   https://portal.tern.org.au/metadata/5e4f379d-0be6-4e40-b52c-9fa3e1e71a00
   Original CSV and dictionary cover sampled 2014 dry-season
   leaf net photosynthesis, stomatal conductance, LMA, nitrogen,
   phosphorus and respiration. These give potential constraints
   for FATES4/7, **but measured Amax/net photosynthesis is not
   directly Vcmax25; LMA needs verified units before converting SLA**.
   Remote public CSV attachment links are real TERN links; availability
   from IRIDIS6 has NOT been tested.

**Stage25** now prepared:
`scripts/stage25/25_asm_TERN_field_DBH_D20_leaf_traits_source_intake_READONLY.py`;
pinned commit `8a59c9384133644d65f7a29dea8329a19d5e32e0`,
Git blob `afccea2b716ddd05dd9cb02a94f4311000c404f9`.
The script verifies Stage24 receipt; attempts original TERN CSV + data
dictionary downloads for stem and leaf measurements into one NEW direct
HOME folder; records each source URL, SHA256, headers, first 3 rows,
row counts, data dictionaries and individual access failures. It does
**not** calculate height/trait residuals before reviewing actual field
definitions. A failed TERN attachment access is recorded as
`NOT_VERIFIED_ACCESS_OR_CSV_SCHEMA`, not evidence of absent data.
No overwrite of original FATES, Stage14 forcing, CTSM Surface or
model cases; no Slurm/AD400.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="8a59c9384133644d65f7a29dea8329a19d5e32e0"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage25_code"
SCRIPT="$CODE/ozflux_stage25.py"
OUT="$HOME/ozflux_stage25_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage25/25_asm_TERN_field_DBH_D20_leaf_traits_source_intake_READONLY.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "afccea2b716ddd05dd9cb02a94f4311000c404f9"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

Source inventory outputs only:
`stage25_AU_ASM_TERN_stem_leaf_intake_science_HOLD.json`
and any newly acquired source CSVs within the fresh HOME report
folder. **Do not commit the raw TERN files to GitHub**.
The scientific next step is data dictionary and sensor/plot provenance,
then paired model height-vs-field DBH and possibly leaf traits,
instead of generating more arbitrary PFT/soil parameter candidates.
All PFT/SURFACE/forcing approvals remain FALSE.

## 3ab. Stage25 operator SUCCESS; Stage26 measurement-point-aware field stem/leaf science

**2026-11-02 actual Stage25 SUCCESS:** source SHA, syntax and
self-test PASS, 4/4 public TERN original CSVs and field dictionaries
downloaded into the immutable operator report dir
`/home/ly3n24/ozflux_stage25_20261102T121025Z`.
Verified original CSV source SHA256 / rows:
- Stem 2014 release: `Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv`,
  SHA `7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55`,
  **222 rows**, includes `stemDiameter_centimeters`,
  `stemHeight_metres`, and crucially
  `stemDiameterPointOfMeasurement_metres`, `plantId`,
  `stemId`, `phenomenonTime`, `scientificName`, `plotId`.
- Stem dictionary:
  `Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv`,
  SHA `82c2d28b8616ee31f1c687ef600f4249592827503adbdcfce73e1e06b6da44fe`,
  **21 entries**.
- Leaf traits:
  `Alice_Mulga_functional_leaf_traits_data_mGiVbmq.csv`,
  SHA `d982b9217ac0ca641e7aca47e681c03f82d08e72215de30fe7ecb1b42952acf0`,
  **142 rows**, detailed species, date/season/branch/plant,
  2014 dry-season light-saturated net photosynthesis, leaf dark
  respiration, stomatal conductance, leaf VPD, PAR and
  LMA `meanLeafDryMassPerLeafAreaTrait_gramsPerSquareMeter`,
  nitrogen/phosphorus.
- Leaf dictionary:
  `Alice_Mulga_functional_trait_data_dictionary_S0G8tsI.csv`,
  SHA `1a6520517e6e2d694477ca45342c769d7ce275681d080d11b4e9aba79e387288`,
  **45 entries**.

The numerical site science remains unverified: `222` is original
**rows**, not guaranteed independent stems/trees; `142` is leaf
**records**, not necessarily unique plants. **D20 != DBH**; use
`stemDiameterPointOfMeasurement_metres` to classify each row.
Model Stage24 H(DBH) can be compared directly to observations only
where diameter measurement height is 1.30m (within declared tolerance)
and valid height/diameter coexist in the same field row. A basal D20
observation may still constrain height distribution but must NEVER be
used directly as FATES formula input. Measurements at other heights
are also excluded from DBH residual evaluation.

Leaf LMA is g dry-matter per m2, hence 1/LMA is m2/g **dry matter**,
not FATES m2/g **carbon**; the carbon mass fraction and canopy-level
traits would need independent verification before comparing model
`fates_leaf_slatop` values. Light-saturated net A is NOT Vcmax25
and measured stomatal conductance is NOT the Medlyn slope parameter;
record ambient CO2, VPD, leaf temp and PAR for future process
evaluation. Repeated stems of one plant and multiple branches can
induce pseudoreplication; preserve plant/plot grouping.

**Stage26 read-only source-grounded analysis is published**:
`scripts/stage26/26_asm_TERN_stem_measurement_height_and_leaf_trait_science_audit_READONLY.py`;
pinned commit `13f501ed772b43a85283f9e9ba0f5a173386b2ed`,
Git blob `10cd43b7678a1aa4d002efb41ae1e3f6f59dcdf7`.
It verifies all original four Stage25 CSV hashes and row counts,
checks Stage24 source-formula receipt, groups observations by
scientificName and exact measurement-height class
(`DIRECT_DBH_1P30M`, `BASAL_D20_0P20M_NOT_DBH`, other, missing),
computes *exploratory* FATES4/FATES7 height residuals ONLY for paired
1.30m DBH rows, reports species-specific field leaf LMA, A_net,
stomatal conductance, PAR, VPD and per-plant/branch identifiers,
and includes relevant dictionary entries. Outputs only three new
HOME files:
`stage26_all_TERN_stem_rows_height_measurement_class.tsv`,
`stage26_TERN_leaf_species_trait_summaries.tsv`,
`stage26_TERN_actual_D20_DBH_leaf_science_gate.json`.
No CIME/Slurm, new surface, FATES JSON modifications or final
science approval. External 2014 core DBH plot records remain
a separate source (not substituted for this D20 dataset).

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="13f501ed772b43a85283f9e9ba0f5a173386b2ed"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage26_code"
SCRIPT="$CODE/ozflux_stage26.py"
OUT="$HOME/ozflux_stage26_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage26/26_asm_TERN_stem_measurement_height_and_leaf_trait_science_audit_READONLY.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "10cd43b7678a1aa4d002efb41ae1e3f6f59dcdf7"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

**Stage26 not yet executed on IRIDIS6.** Do not assume any source DBH
count or species-specific leaf trait median until actual report output.
No source/forcing/surface/experiment files modified.

## 3ac. Stage26 operator SUCCESS: 222 D20-only stems, 142 leaf records, zero valid DBH pairs

**Operator Stage26 SUCCESS on 2026-11-02**:
`/home/ly3n24/ozflux_stage26_20261102T122636Z`.
Original 4 Stage25 TERN CSV files and Stage24 formula receipt verified.
**ALL 222 stem rows have `stemDiameterPointOfMeasurement_metres=0.2`**
(TERN D20 basal measurement): **ZERO** directly comparable 1.30m
DBH + height pairs, so Stage26 correctly reports `MAE4=None`,
`MAE7=None` without inventing a stem taper conversion.
The observed height distributions still independently test whether
a chosen PFT can reach the site heights.

Per-species valid stem HEIGHT (not independently counted trees):
- *Acacia aneura*: n=86, median 3.3m, max **8.5m**
- *Acacia aptaneura*: n=120, median 3.8m, max **8.5m**
- *Eremophila latrobei* ssp. *glabra*: n=2, median/max 1.9m
- *Psydrax latifolia*: n=14, median 4.6m, max **5.0m**
The exact local Stage24 FATES7 evergreen shrub height plateau is
4.735410175m at DBH≥3cm; **it cannot attain the observed 8.5m
Acacia stem heights under the current parameter and formula**.
This observation is stronger than comparing D20 to DBH (which would
be scientifically invalid). However, sample rows may span 2014 and
2018 derived increments, share the same plant/stem identities,
and were not independently QCed for time and footprint. Quantify
exceedances separately by observation year; avoid pseudoreplication.

Stage26 leaf records: **142**, seven species. Direct *Acacia aneura*
records **40** (TERN field PFT `Needle leaf tree`, NOT automatically
a FATES needleleaf conifer class): median LMA
**279.985 g dry mass m-2**; median light-saturated
**net** A 3.165 µmol CO2 m-2 s-1; measured gs 0.011
mol m-2 s-1. These do **not** measure Vcmax25 or Medlyn g1.
No *Acacia aptaneura* leaf trait record appears in this 142-row
release, so do not extrapolate field leaf trait values to both
dominant Acacia species without species evidence.

The field-measured LMA can be converted to SLA on a carbon-mass
basis only with **explicit assumed or measured leaf carbon mass
fraction**: `SLA_m2/gC = 1/(LMA_g dry/m2 * f_C)`.
For hypothetical `f_C=0.45..0.50`, the observed *A. aneura* LMA
median gives ~0.00794..0.00714 m2/gC. This is not a direct
FATES `fates_leaf_slatop` calibration because the source measures
2014 dry-season sampled leaves/phyllodes while the model parameter
is canopy-top SLA; the TERN source does NOT measure `f_C`.
Actual FATES4 top SLA default 0.009 m2/gC; FATES7 0.012.
Do not change them without defining the canopy/sampling and
leaf-carbon conversion.

**Independent 2014 TRUE DBH survey remains the next observational
resource**: `Vegetation Data, Direct Measure of Stems, Alice Mulga
SuperSite, Core 1ha, 2014`:
https://researchdata.edu.au/vegetation-data-direct-ha-2014/617073 .
TERN published metadata reports 1.3m breast-height diameters and
heights from **200 stems across 86 trees** in six sampled subplots
within the flux-tower footprint. This is a separate cohort from
the 222 D20 rows; the original individual DBH-height CSV/XLSX has
**not yet been directly verified/downloaded** and must not be
fabricated from the summaries. Metadata file names refer to
`asn_alic_veg_dbh-h_compliled_core_1ha_2014.csv` and a 2014 XLSX,
but no verified direct HTTPS attachment is yet available.

**Stage27 source-pinned, HOME-only, non-destructive analysis**
published at
`scripts/stage27/27_asm_observed_height_exceedance_and_Acacia_LMA_SLA_sensitivity_READONLY.py`,
commit `b4d3e2211cdfd7b76fe89cff35a415101e850cf5`,
Git blob `91c78ab5f5fee4790908af49dc850d1eb254bc48`.
It pins original Stage25 stem and leaf CSV SHA256, original Stage21
trait TSV SHA256, and actual Stage24 and Stage26 operator receipts.
It groups stem heights by species **and year** and reports height
record counts ABOVE the verified FATES7 4.735410m ceiling
without ever using D20 as DBH or treating derived 2018 data as
new independent surveys. For leaf trait comparisons it uses only
hypothetical `f_C=0.45` and `0.50`, converts measured LMA to
derived m2/gC SLA under those *explicit assumptions* and compares
to the actual FATES4 and FATES7 canopy-top model values as a
sensitivity screen, not calibration. Stage27 creates only new
HOME JSON and two TSV reports. No FATES parameter, surface, forcing,
CIME, Slurm or AD400 modification.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="b4d3e2211cdfd7b76fe89cff35a415101e850cf5"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage27_code"
SCRIPT="$CODE/ozflux_stage27.py"
OUT="$HOME/ozflux_stage27_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage27/27_asm_observed_height_exceedance_and_Acacia_LMA_SLA_sensitivity_READONLY.py" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "91c78ab5f5fee4790908af49dc850d1eb254bc48"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

Outputs:
`stage27_TERN_stem_height_above_FATES7_cap_by_year_species.tsv`,
`stage27_TERN_leaf_LMA_assumed_C_fraction_SLA_sensitivity.tsv`,
`stage27_AU_ASM_measured_structure_leaf_science_HOLD.json`.
Do not infer actual experimental PFT cover, a new 10-layer Kandosol
profile or publish model errors until an independently measured
DBH-height dataset has been secured.

## 3ad. Stage27 operator SUCCESS; false 2014-year flag and duplicated stem IDs

Stage27 actual operator result: /home/ly3n24/ozflux_stage27_20261102T123656Z .
Original TERN source CSV, Stage21 traits and Stage24/26 receipt hashes were verified.
FATES7 installed exact height ceiling 4.735410175384586 m.
Observed field height rows above this cap: Acacia aneura 18/86 (20.93%),
Acacia aptaneura 36/120 (30.0%), combined **54/206 rows (26.21%)**;
Psydrax latifolia 2/14; Eremophila latrobei ssp glabra 0/2.
All 222 raw diameter values correspond to basal D20 at 0.2 m, not DBH at 1.3 m.
Therefore Stage27 correctly did not compute any FATES H(DBH) fit error.

Important sampling issue: the Stage27 per-species table contains 222 raw
rows but only 111 unique stem keys and 92 unique plant keys. The 2:1
count *suggests* repeat/derived records but exact per-stem repeat counts
still need direct original-CSV reconciliation. Repeated stems are not
independent trees. TERN publisher states 2014 field measurements
and 2018 basal-area increments derived from dendrometers WITHOUT
independent repeat stem surveying.

Critical Stage27 BUG: its 2014 tall-stem flag FALSE is an artefact of
all 222 phenotypeTime row values yielding UNSPECIFIED years; the
filter looking for exactly year 2014 returned an empty selection.
FALSE DOES NOT MEAN NO TALL STEMS. Need inspect startVisitDate,
endVisitDate, phenomenonTime and 21-entry original data dictionary
before attributing individual rows to 2014 or 2018.
Publisher: https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed

Stage27 Acacia aneura leaf observations: 40 leaf records from 20 plant IDs;
LMA median 279.985 g dry mass/m2. Hypothetical carbon mass fractions
0.45/0.50 imply derived SLA 0.007936934/0.007143240 m2/gC, numerically
closer to FATES4 canopy-top 0.009 than FATES7 0.012. This is only
a sensitivity screen (carbon fraction not measured; phyllode position
and season not necessarily canopy top). No Acacia aptaneura leaf
measurements in the source. No model parameter calibration authorized.

**Stage28 read-only audit published, NOT run:**
scripts/stage28/28_asm_TERN_stem_duplicates_and_temporal_provenance_READONLY.py
pinned commit 62f6e17f5f3f5383400fd1054b3bee2d25cf73d5
Git blob afbb06c458b527282a649cd65ec97d8a3088d766.
Checks original 222-row CSV and 21-row dictionary SHA and the actual
Stage26/27 receipts; groups exact (siteId, plotId, plantId, stemId)
to count duplicate rows and classify FATES7 ceiling exceedances
only once per stem with a separate DISCORDANT classification.
Audits three original date fields and reports raw values, rather than
assuming 2014 for every row or incorrectly claiming 2014 had no tall trees.
Writes only new HOME JSON + two TSV files, never source/forcing/params/
surface/CIME/Slurm. AD400 stays blocked.

Stage28 outputs: stage28_TERN_unique_stem_height_and_provenance.tsv;
stage28_TERN_species_unique_stem_height_ceiling_summary.tsv;
stage28_TERN_time_and_duplicate_stem_science_HOLD.json.

Independent verified DBH survey metadata:
https://researchdata.edu.au/vegetation-data-direct-ha-2014/617073
reports 200 true 1.3m DBH stems from 86 trees (2014-01-21 to 2014-01-22)
inside tower footprint; direct individual original DBH-height source
NOT downloaded/validated and separate from the D20 TERN release.
## 3ae. Stage28 actual operator SUCCESS — date parse root cause and 111 unique stems

**Actual Stage28 operator success 2026-11-02**:
`/home/ly3n24/ozflux_stage28_20261102T124717Z`.
Original 222-row TERN D20 source SHA256 verified:
`7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55`.
Stage28 found **111 distinct original stem IDs, each exactly 2 rows**;
all original stem diameters were measured at D20=0.20m not DBH=1.30m.
Unique stem IDs by species: Acacia aneura 43 (33 plant IDs),
A. aptaneura 60 (53 plant IDs), Eremophila latrobei ssp glabra
1, Psydrax latifolia 7.

Height above FATES7 exact maximum 4.735410175384586m:
9/43 unique A. aneura stems, 18/60 A. aptaneura (combined **27/103**
distinct Acacia stem IDs, 26.21%); 1/7 Psydrax and 0/1 Eremophila.
ALL repeated heights for each unique stem fall on same side of cap
(0 discordant classes). This is not independent tree-count or flux
footprint-cover percentage, and 2018 may be increment-derived.

**Root cause Stage27 time bug RESOLVED AT SOURCE FORMAT LEVEL:**
Actual original CSV uses **day/month/year** strings (D/M/YYYY),
not ISO 8601. `startVisitDate` is 21/1/2014 for 111 records and
1/6/2018 for 111 records; endVisitDate 22/1/2014 and 2/6/2018.
`phenomenonTime` 21/1/2014 (12), 22/1/2014 (99),
1/6/2018 (111). Stage27's UNSPECIFIED 222 and
`TALL STEMS IN 2014: False` are invalid inferences from a
date-parser mismatch. Publisher's 2014 measurements and 2018
derived stem increment are NOT two independent field surveys.
No row has been edited, and Stage28 itself did not attempt to
assign year to each stem's two measurements. Its paired-stem
height-cap result is independent of D20 diameter.

**Stage29 first operator attempt FAILED SAFELY at self-test (2026-11-02):**
Source SHA and Python syntax passed; self-test raised
`ValueError: 111 exact independent stem identifiers expected` because
its one-stem (two-row) fixture erroneously called the same
`analyze()` function with a hard-coded production-only expectation
of 111 stems. This is an incorrect **test/production count coupling**,
not an original-source error, and the actual TERN science audit was
NOT entered. No report, source/model write or job was produced.
The corrected script (updated commit/blob below) passes
`expected_stems=1` for the fixture and explicitly enforces
`expected_stems=111` on the real 222-row input, with positive
1x2014/1x2018 and negative duplicate-year regression checks.
**GitHub source reviewed; rerun on IRIDIS6 is pending, not yet
claimed successful.**

**Stage29 read-only source-specified D/M/YYYY temporal reconciliation
code PUBLISHED (operator run pending):**
`scripts/stage29/29_asm_TERN_exact_2014_vs_2018_stem_pair_date_science_READONLY.py`
commit `5c4b136e75fc11e6a5e6025f1a3ac48a3887529d`,
blob `a45d514909e7af803e5628727f7660117f545827`.
Verifies Stage28 receipt and original CSV/dictionary SHA256;
uses strict D/M/YYYY calendar dates, checks each row's phenomenon
date lies within visit start/end, and fail-closes if any unique
stem lacks exactly one 2014 and one 2018 source row.
Outputs one row per exact (siteId,plotId,plantId,stemId), comparing
2014 field vs 2018 derived stem *height*, D20 diameter and
calculated AGB without pretending second independent remeasurement.
Reports the **2014-only** unique-stem above-cap number, true
height changes and year-specific missingness. No direct H(DBH)
residuals or FATES model runs, since all original diameters are D20.

```bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="5c4b136e75fc11e6a5e6025f1a3ac48a3887529d"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage29_code"
OUT="$HOME/ozflux_stage29_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage29/29_asm_TERN_exact_2014_vs_2018_stem_pair_date_science_READONLY.py" -o "$CODE/stage29.py.download"
test "$(git hash-object "$CODE/stage29.py.download")" = "a45d514909e7af803e5628727f7660117f545827"
mv "$CODE/stage29.py.download" "$CODE/stage29.py"
python3 -B -m py_compile "$CODE/stage29.py"
python3 -B "$CODE/stage29.py" --self-test
python3 -B "$CODE/stage29.py" --out "$OUT"
echo "REPORT_DIR $OUT"
)
```

Expected only new HOME reports:
`stage29_111_TERN_unique_stem_2014_measured_2018_derived_comparison.tsv`;
`stage29_TERN_true_DMY_dates_and_Acacia_height_science_HOLD.json`.
No case, site surface, parameter, data or original forcing change.

Separately, the older 2014 **true breast-height DBH** core
1ha field survey (200 stems across 86 trees) is documented at
https://researchdata.edu.au/vegetation-data-direct-ha-2014/617073
but the exact original paired H(DBH) CSV/XLSX remains
unobtained; do not substitute this D20 release.
## 3af. Stage29 operator actual SUCCESS: exact 2014 field/2018 derived 111-stem pairs; Stage30 anomaly audit

Stage29 first operator attempt failed at **self-test only** from the
hard-coded 111-stem expected count against a 1-stem fixture;
fixed in commit `5c4b136e75fc11e6a5e6025f1a3ac48a3887529d`
(blob `a45d514909e7af803e5628727f7660117f545827`).
**Corrected Stage29 real operator run SUCCESS on 2026-11-02:**
`/home/ly3n24/ozflux_stage29_20261102T131205Z`.
Original TERN stem CSV, original 21-row dictionary, Stage28 receipt
and true D/M/YYYY dates all verified. **222/222** dates valid,
**111** exact unique stem pairs; each stem has one 2014 field and
one 2018 *derived* record, and 111/111 stem height-cap
classes agree across source years. This resolves Stage27's
`TALL STEMS IN 2014: False` parsing artefact.

FATES7 local default height max **4.735410175384586m**.
From 2014 FIELD observed data, **9/43 A. aneura stems** (33 plant
IDs) and **18/60 A. aptaneura stems** (53 plant IDs) exceed
this ceiling; combined **27/103 Acacia unique stem IDs =26.21%**.
Other taxa: Psydrax latifolia 1/7; Eremophila latrobei ssp
glabra 0/1. These are not independent trees nor canopy-cover
fractions and do not imply FATES4's PFT parameter set has
been validated. All 222 source diameters are basal D20 at 0.20m,
not model DBH at 1.30m; no quantitative H(DBH) fit computed.

**2018 source is derived, not independently surveyed**,
per TERN publisher lineage:
https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed
Stem-level changes from Stage29: A. aneura 43 stems have height
deltas all zero; D20 delta median +0.700000cm, min +0.675210,
max +0.700000, AGB delta median +0.2733kg, min -60.7166,
max +51.2722kg. A. aptaneura 60 stems have 2 nonzero height
deltas (min -0.4m, max +0.4m), D20 delta median +0.700000cm
but min **-2.3cm**, max **+3.7cm**; AGB delta median +1.4057kg,
min **-289.3485kg**, max **+329.6728kg**.
Eremophila and Psydrax D20 delta approx +0.7cm, with some
negative derived AGB deltas. These are QC CANDIDATES:
do not directly interpret them as carbon loss, true stem
growth, mortality or a forcing/PFT failure. An ordinary increase
in basal diameter does not automatically imply every source
above-ground biomass allometric calculation increased. Need
check original exact values, species/plot/status and derivation.

**Stage30 source-level forensic script PUBLISHED, operator run pending**:
`scripts/stage30/30_asm_2018_derived_D20_AGB_outlier_source_reconciliation_READONLY.py`
commit `ee40e9bfd449b399a574b7a6b56d0ff610f05448`,
Git blob `a4ea0317f3179155ecf9a6f628bccf7a052f1f7c`.
Read-only, cross-verifies ALL 111 Stage29 paired stems against original
SHA-pinned 222-row CSV, checks exact 2014/2018 raw measurements,
computes D20 change and basal-area change **pi/4 * (D18^2-D14^2)**
in cm², compares measured/published derived height and AGB
without falsely calling D20 DBH or a 2018 derived estimate
independent field observation. Flags D20 decreases, >1cm gain,
departure from the nominal +0.7cm *screen* (not a physical
threshold), derived basal area decreases, height changes,
large or negative AGB deltas, and mismatched signs, preserving
exact stem IDs, source status and comments. These flags mean
**requires scientific review**, NEVER automatic exclusion or
data repair. Source paper says uniform *basal area* increment,
which cannot be conflated with uniform *diameter* increment.
Results only new HOME TSV/JSON, no FATES params, DATM forcing,
surface, CIME cases or Slurm changes.

```bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="ee40e9bfd449b399a574b7a6b56d0ff610f05448"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage30_code"
OUT="$HOME/ozflux_stage30_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage30/30_asm_2018_derived_D20_AGB_outlier_source_reconciliation_READONLY.py" -o "$CODE/stage30.py.download"
test "$(git hash-object "$CODE/stage30.py.download")" = "a4ea0317f3179155ecf9a6f628bccf7a052f1f7c"
mv "$CODE/stage30.py.download" "$CODE/stage30.py"
python3 -B -m py_compile "$CODE/stage30.py"
python3 -B "$CODE/stage30.py" --self-test
python3 -B "$CODE/stage30.py" --out "$OUT"
echo "REPORT_DIR $OUT"
)
```

Reports: `stage30_all_111_2014_field_2018_derived_original_stems.tsv`,
`stage30_flagged_D20_BA_height_AGB_source_stems.tsv`,
`stage30_AU_ASM_derived_2018_stem_increment_science_HOLD.json`.
Actual Stage30 execution on IRIDIS6 pending, and no science approval
or AD400/Normal400 authorized.
## 3ag. Stage30 operator SUCCESS: 48/111 derived AGB anomaly stems; Stage31 join/allometry association gate

**Actual Stage30 operator SUCCESS 2026-11-02:**
`/home/ly3n24/ozflux_stage30_20261102T131841Z`.
Original TERN 222-row D20 source SHA verified and 111 original
2014 field vs 2018 derived stem pair values independently
reconciled to Stage29. Stage30 reports **48 distinct stems**
with at least one source-QC REVIEW flag (overlapping categories):
**37** derived AGB decreases; **36** D20-up, height-stable but
2018 AGB down; **20** absolute AGB changes >50kg; exactly
**one** D20/basal-area decrease and two changed heights.
These flags are exploratory, NOT 48 proven source errors.

Species: A. aneura 43 stem IDs, D20 delta median +0.7cm
(min +0.67521, max +0.7), 19 derived AGB decreases and
3 changes abs >50kg. A. aptaneura 60 stems, D20 delta
median +0.7cm, min -2.3cm, max +3.7cm, 14 AGB decreases,
17 changes abs >50kg. Psydrax 4 AGB decreases in 7 stems;
Eremophila 1 stem no flags. The two exceptional D20 changes
occur within **A. aptaneura plant 29**, stem 1b (-2.3cm)
and stem 2b (+3.7cm), with opposite 0.4m height changes.
These may be stem identification/swap/derived processing issues;
no source edit or reinterpretation is justified yet.

Critical same-stem examples from original source:
A. aptaneura plant 13 stem 1b D20 26.0 to 26.7 cm,
H stable 7.8m, AGB 304.3746875 to 15.02621289kg;
plant 69 stem 1b D20 2.5 to 3.2cm,
H 3.1m stable, AGB 0.470644739 to 158.1053356kg;
plant 86 stem 2b D20 9.9 to 10.6cm, H 5.0m stable,
AGB 21.02976969 to 350.7026157kg.
These changes cannot be accepted as empirical carbon uptake/loss
without verifying 2018 AGB field mapping and the exact original
2018 biomass derivation pipeline.

TERN official dataset methodology:
https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed
explains the 2014 D20/height survey, 2018 independent
re-measurement **did not occur**, dendrometer-informed
*uniform basal-area increment* was applied,
AGB was calculated via Návar et al. (2013) allometry,
and source data were screened for potential outliers.
No per-stem coefficients or implementation are provided in the
metadata. Uniform basal area is not uniform diameter increment.
Stage30 source exhibits mostly +0.7cm D20, which should be
treated as an observed RELEASE PATTERN, not proof the
publisher used a fixed diameter increment.

**Stage31 first operator attempt failed at self-test only on 2026-11-02:**
Actual source SHA and syntax passed, but synthetic sample called
JSON field `2018_rank_corr_D20_AGB`, whereas the analysis correctly
produces `2018_derived_rank_corr_D20_AGB`.
Raised `KeyError: '2018_rank_corr_D20_AGB'` before any 111-stem
production audit, new report or model write.
Corrected script: commit `f3dc5b8113319d683c9eefe1d3063508e086bda9`,
Git blob `6e865af12dfd6d6ac4401cf2c07239161a4ae881`.
Extended the synthetic regression test to assert all four rank
report keys, repeated AGB summary, all emitted TSV column names,
and exact 2014 and 2018 original stem species and key matching.
**New actual IRIDIS6 selftest and original-data audit NOT YET RUN.**
**Stage31 new read-only audit published, operator execution PENDING:**
`scripts/stage31/31_asm_TERN_2018_AGB_join_formula_consistency_READONLY.py`;
pinned commit `f3dc5b8113319d683c9eefe1d3063508e086bda9`,
blob `6e865af12dfd6d6ac4401cf2c07239161a4ae881`.
Stage31 pins the source 222-row CSV SHA and checks the actual
Stage30 receipt (111 stems, 48 flagged, 36 mismatched direction,
37 negative AGB, 20 large AGB changes). Independently joins
exact original IDs and values and computes within-species
**D20-vs-AGB and height-vs-AGB Spearman rank correlations**
for 2014 field/derived baseline versus 2018 derived rows,
source AGB ratios, repeated identical 2018 AGB across different
stems, and same D20/height but different AGB candidate groups.
Any apparently unrelated 2018 AGB values are only a
**SUSPECTED join/formula/provenance issue**, never a proven
column permutation; rank screens are not a reconstruction
of Návar et al. model parameters. New HOME TSV + JSON only,
no original CSV, FATES JSON, surface, forcing, CIME/Slurm.

Run on IRIDIS6:
```bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="f3dc5b8113319d683c9eefe1d3063508e086bda9"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage31_code"
OUT="$HOME/ozflux_stage31_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage31/31_asm_TERN_2018_AGB_join_formula_consistency_READONLY.py" -o "$CODE/stage31.py.download"
test "$(git hash-object "$CODE/stage31.py.download")" = "6e865af12dfd6d6ac4401cf2c07239161a4ae881"
mv "$CODE/stage31.py.download" "$CODE/stage31.py"
python3 -B -m py_compile "$CODE/stage31.py"
python3 -B "$CODE/stage31.py" --self-test
python3 -B "$CODE/stage31.py" --out "$OUT"
echo "REPORT_DIR $OUT"
)
```

Outputs: stage31_all_111_stem_AGB_join_association_screens.tsv,
stage31_AU_ASM_derived_AGB_join_formula_science_HOLD.json.
Depending on whether 2018 per-stem AGB associates with D20/height,
look next for official site-level biomass source and the original
data product's 2018 AGB computation/mapping documentation; do
not use 2018 derived AGB as model calibration data yet.
2014 field tree heights and the separate observed FATES7 height
compatibility result are **not affected** by these derived
2018 AGB anomalies. PFT4/PFT7, soil, forcing and AD400 remain
scientific HOLD.
## 3ah. Stage31 operator SUCCESS: derived 2018 AGB association collapses; Stage32 hypothesis screen

**Corrected Stage31 actual IRIDIS6 operator SUCCESS** at
`/home/ly3n24/ozflux_stage31_20261102T183333Z`.
Source git blob, syntax and regression self-test PASS;
original TERN SHA256
`7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55`
and exact 111 unique stem rows / 48 Stage30 flagged confirmed.
Previous Stage31 first attempt had a self-test-only KeyError for an
old `2018_rank_corr_D20_AGB` key; the corrected pinned source is commit
`f3dc5b8113319d683c9eefe1d3063508e086bda9`,
blob `6e865af12dfd6d6ac4401cf2c07239161a4ae881`.

**Site original AGB source consistency breaks in 2018 derived records:**
- *A. aneura* (n=43): D20–AGB Spearman 2014 **0.9990556**,
  2018 **0.2371875**; height–AGB 0.81834 -> 0.18819.
  2018 AGB18/AGB14 ratio 0.02141 to 201.63, median 1.2535;
  10 distinct 2018 AGB value groups shared between stems;
  23 stem records have a repeated 2018 biomass value.
- *A. aptaneura* (n=60): D20–AGB Spearman 2014 **0.9452423**,
  2018 **0.3182653**; height–AGB 0.82885 -> 0.19236.
  2018 ratio 0.003725 to **865.445**, median 2.3437;
  8 distinct exact repeated AGB groups in 2018;
  21 stem rows have repeated 2018 biomass values.
- *Psydrax latifolia* (n=7): D20–AGB Spearman 0.99103 -> 0.37839;
  sample is too small for strong conclusions.
- Stage31 reports 55 source-review candidates with its different
  ratio/identical-D20-height screen. Do NOT add to the 48 Stage30
  distinct stem flags: overlapping flags and different definitions.
- Exact D20 and height pairs associated with different 2018 derived
  biomass values within same species also appear (2 groups in
  A. aneura and 6 in A. aptaneura). This is concerning for
  deterministic allometric calculations, but may reflect additional
  source variables not yet documented. These diagnostics do NOT
  establish a specific erroneous join or row permutation.

2018 AGB remains **SCIENCE HOLD / excluded from calibration**.
All 2014 FIELD measured heights and the 27/103 Acacia stems
beyond FATES7 cap are valid independently of 2018 AGB.
Do not treat 2014 original AGB as weighed field biomass;
TERN says it too was calculated by Návar et al. allometry.

Verified TERN metadata URL:
https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed
and published additional independent site-level AGB CSV link
`Alice_Mulga_site_level_biomass_data_v3pQRMW.csv` available on
this dataset's Access Data section. Site-level record definition,
scaling to tonnes/ha, and sum of individual stem footprints must
be checked before comparison; no site-level file has been
ingested in this Stage32 script.

**Stage32 source-grounded science screen published (not executed):**
`scripts/stage32/32_asm_2014_D20_AGB_empirical_baseline_vs_2018_derived_READONLY.py`;
commit `6ff9628dc6407fc82a4138bd79e533c52bd12b2f`,
git blob `f09378b05646206cb59487d3023eadd3f7a396e1`.
Reads exact source SHA-pinned 222-row TERN stem CSV and
actual Stage30 / Stage31 111-row source-audited reports,
checks every 2014/2018 original stem against identity and numeric
values. For each species with n>=4, fits an **in-sample**
exploratory log(2014 original allometric AGB kg) vs log(D20 cm)
linear reference, then computes corresponding 2018
**hypothetical** expected AGB from D20 2018, the actual-to-
reference ratio, within-species source AGB sum and 0.2x/5x
outlier counts. This is an IN-SAMPLE, structure-only diagnostic,
NOT actual Návar parameter reconstruction, observational
validation, 2018 corrected AGB, a growth-rate estimate, model
forcing, carbon flux or site-level t/ha. One-stem Eremophila
correctly skipped. No raw/model changes; output only fresh HOME
TSV/JSON. If 2014 in-sample R2 is low, treat reference model
as inadequate. If high 2014 R2 but 2018 residuals large,
evidence of a 2018 derived-variable inconsistency, not proof
of wrong source row mapping.

Run pinned script on IRIDIS6:
```bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="6ff9628dc6407fc82a4138bd79e533c52bd12b2f"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage32_code"
OUT="$HOME/ozflux_stage32_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage32/32_asm_2014_D20_AGB_empirical_baseline_vs_2018_derived_READONLY.py" -o "$CODE/stage32.py.download"
test "$(git hash-object "$CODE/stage32.py.download")" = "f09378b05646206cb59487d3023eadd3f7a396e1"
mv "$CODE/stage32.py.download" "$CODE/stage32.py"
python3 -B -m py_compile "$CODE/stage32.py"
python3 -B "$CODE/stage32.py" --self-test
python3 -B "$CODE/stage32.py" --out "$OUT"
echo "REPORT_DIR $OUT"
)
```

Expected reports:
`stage32_111_stem_2014_baseline_2018_derived_AGB_diagnostic.tsv`,
`stage32_AU_ASM_source_AGB_allometric_consistency_science_HOLD.json`.
Next is independent source/process validation: confirm publisher's
2018 biomass derivation and original `site_level_biomass` file,
or contact TERN field authors with reproducible source examples.
Do not use 2018 AGB for modeling or derive actual C stocks from
these source samples; PFT/soil/surface/forcing/AD400 remain blocked.
## 3ai. Stage32 operator SUCCESS — strong original 2014 D20–AGB baseline and extreme 2018 inconsistency; Stage33 independent site source

**Stage32 actual operator SUCCESS** (2026-11-02):
`/home/ly3n24/ozflux_stage32_20261102T185340Z`.
Git source hash, Python syntax, self-test, 222-row original stem CSV,
and Stage30/31 111-row science reports verified. Output original
2014 log(AGB)~log(D20) fits were IN-SAMPLE and used 2014 allometrically
**estimated** biomass, not measured/destructively weighed AGB.

| Taxon | Stem IDs | 2014 in-sample log R² | 2018 / reference median [min,max] | 2018 ratio <0.2x / >5x |
|---|---:|---:|---:|---:|
| Acacia aneura | 43 | 0.9999665 | 0.7464 [0.0181,69.5657] | 8 / 3 |
| Acacia aptaneura | 60 | 0.9481079 | 1.2135 [0.00368,269.9659] | 11 / 15 |
| Psydrax latifolia | 7 | 0.9997390 | 0.4918 [0.0562,5.9489] | 1 / 1 |
| Eremophila latrobei ssp glabra | 1 | not fit | not available | not fit |

The **37 of 103 Acacia stems** with derived 2018 AGB
outside the exploratory 0.2x–5x reference band demonstrate
strong internal inconsistency, but **DO NOT validate the 2014
allometric estimates**, recover Návar (2013) parameters,
identify a specific record swap, or authorize replacing 2018 AGB.
A. aneura original 111-stem-sample subgroup has
2014 AGB sum 299.103 kg vs 2018 derived 242.785 kg;
A. aptaneura 1881.777 kg vs 2344.063 kg. These are
**sums over the observed/derived subset only**, not tower site
t/ha or empirical NPP and must NOT be used to estimate ecosystem
carbon stock/flux trends. All original D are **D20 basal**
and NOT FATES DBH. The 2014 27/103 dominant Acacia tall-stem
result is completely independent of the derived-AGB issue.

**New verified external resource:** The same TERN dataset metadata,
https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed ,
publishes an official separate **site-level aboveground woody
biomass CSV** in Access Data, with known original HTTPS link
`https://shared.tern.org.au/attachment/c2968de2-1e8b-4a05-919f-46744b3171ed/Alice_Mulga_site_level_biomass_data_v3pQRMW.csv`.
The published lineage states site-level estimates were **scaled to
tonnes/hectare**; the actual CSV units, dates, sampled area,
plot definitions and stem cohort have **NOT been verified**.
Our initial web/container source fetch was unsuccessful, which
does not mean IRIDIS6 cannot download it (Stage25 public CSVs
did download successfully). TERN metadata page describes 2014
field D20 measurements and 2018 dendrometer-based derived uniform
basal-area increments, not repeated field survey.
Citation: Cleverly, J. (2022), Alice Mulga Stem Diameter, Height
and Aboveground Woody Biomass Data 2014, TERN, v1.0.

**Stage33 official site-level biomass source intake PUBLISHED
(operator execution pending):**
`scripts/stage33/33_asm_TERN_site_level_AGB_original_source_intake_READONLY.py`
pinned GitHub commit `6ff3c1cc4254beec943bf42d1fb0c75ba0f8297d`,
Git blob `4beb9ea03e8903e3e0a55183a17b0ce915241ce9`.
It verifies unchanged original Stage25 CSV and 21-field dictionary
SHAs and successful Stage31/32 receipts, attempts public TERN
site-level CSV acquisition into a fresh HOME folder, records
download URL and actual SHA256, original headers, row count,
potential time/biomass/unit/area/plot fields and raw samples,
and explicitly **does not perform any kg-to-t/ha conversion,
cross-source matching, or reinterpretation of the 111-stem set**.
If external HTTP access or CSV schema fails, a report with exact
failure is saved, not a false source-verification claim.
No source, FATES model, surface, forcing, CIME, Slurm or AD400 changes.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="6ff3c1cc4254beec943bf42d1fb0c75ba0f8297d"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage33_code"
OUT="$HOME/ozflux_stage33_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage33/33_asm_TERN_site_level_AGB_original_source_intake_READONLY.py" -o "$CODE/stage33.py.download"
test "$(git hash-object "$CODE/stage33.py.download")" = "4beb9ea03e8903e3e0a55183a17b0ce915241ce9"
mv "$CODE/stage33.py.download" "$CODE/stage33.py"
python3 -B -m py_compile "$CODE/stage33.py"
python3 -B "$CODE/stage33.py" --self-test
python3 -B "$CODE/stage33.py" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

Expected JSON: `stage33_TERN_original_site_level_biomass_intake_science_HOLD.json`.
If source HTTP download succeeds, raw CSV also saved in the
same NEW HOME folder. Need subsequent source-specific year/area/unit
crosswalk before comparing against 2014 allometric stem data.
PFT, soil, final forcing and AD400 science gates stay HOLD.

## 3aj. Stage33 operator SUCCESS: official 0.06ha sampled-stem vs core1ha site-level AGB mismatch hypothesis; Stage34 source proof

**Stage33 actual SUCCESS** on IRIDIS6 at
`/home/ly3n24/ozflux_stage33_20261102T191655Z`.
Official source CSV:
`Alice_Mulga_site_level_biomass_data_v3pQRMW.csv`,
SHA256
`f4fcfe46fd5132ed040187ae443441d37822e18c8deb48c01be667af51b9fea8`,
**2 rows x 11 columns**, original plotId
`Alice Mulga, core1ha`, plotLength=100m, plotWidth=100m.
2014 date 21/1/2014: source
`standBiomass_tonnesPerHectare=37.4168`.
2018 date 1/6/2018: `44.6277` t/ha (**DERIVED**).
2014 to 2018 absolute +7.2109 t/ha, relative +19.271824%;
this is **a difference between published calculated stand values**,
not independent measured biomass accrual, carbon uptake, NPP or
NEE. The 2018 source remains SCIENCE HOLD.

TERN official lineage in this SAME dataset states explicitly:
**All stems surveyed within a 0.06 ha subplot/sample** in
2014, 2018 re-derived using dendrometer basal-area increment;
site-level AGB was scaled to t/ha.
Source https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed
(**0.06 ha is NOT the 1ha `core1ha` labelled enclosing plot**).
The independent older true DBH survey also recorded six 10x10m
plots (=0.06ha), but this resemblance alone does NOT establish
identical stem-ID/plot cohorts.

**Scientific arithmetic hypothesis from Stage32 operator's source
four-species AGB summaries** (NOT yet independently recomputed
from original rows under Stage34):
2014 original 111 stem AGB = **2247.437182506 kg**,
2018 original 111 derived stem AGB = **2675.232142231 kg**.
At 0.06ha these correspond to **37.4572863751 t/ha**
and **44.5872023705 t/ha** respectively, whereas site-level
CSV reports **37.4168** and **44.6277 t/ha**:
stem-minus-site differences ≈ **+2.42918 kg** in 2014 and
**−2.42986 kg** in 2018, essentially equal/opposite.
The two-year combined sums agree within publisher's
4-decimal stand t/ha rounding precision.

One **2014 Eremophila latrobei ssp glabra original stem**
was reported by Stage32 with AGB **2.429615547kg**.
Transferring this single SOURCE 2014 value *hypothetically*
from the original 2014 stem aggregate to the original
2018 derived-stem aggregate yields site-level stand values
of **37.4167928 / 44.6276960 t/ha**, which round exactly
to published **37.4168 / 44.6277**.
This is a testable **potential cross-year source aggregation/
join issue**, not proof of a dataset bug or permission to
change a public source. It does NOT resolve the dramatic
per-stem 2018 derived AGB anomalies from Stage30–32.
Source/publisher AGB was ALLOMETRICALLY estimated, not
directly weighed; published stand is not an independent
stand-level census.

**Stage34 read-only source-reconciled arithmetic test PUBLISHED,
operator execution PENDING**:
`scripts/stage34/34_asm_TERN_006ha_stand_AGB_source_reconciliation_READONLY.py`
commit `c54cf65362fc42648281afcdf3a5465de5d02101`,
git blob `cc831a551a7f53cf3ecf3d37926217c2f18a5386`.
Stage34 SHA-verifies original 222-row TERN stem CSV and
official 2-row site AGB CSV, Stage32/33 operator receipts,
direct original stem IDs and D/M/YYYY per-row dates,
requires 111 unique 2014+2018 stem IDs, recovers original
site dates and geometry, sums original AGB by year using
Python Decimal, scales by explicitly **publisher 0.06ha
x 1000kg/t**, and tests ALL 111 original 2014 single-stem
biomass values for *both-year* 4-decimal exact stand
reconciliation. It reports every matching candidate
and original key, not just the previously suspected
Eremophila stem. Distinguishes arithmetic reconstruction
from validated source data-assembly process.
Writes only a new HOME JSON and candidate TSV,
no raw-source modification, model params, forcing,
surface, CIME/Slurm or AD400.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="c54cf65362fc42648281afcdf3a5465de5d02101"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage34_code"
OUT="$HOME/ozflux_stage34_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage34/34_asm_TERN_006ha_stand_AGB_source_reconciliation_READONLY.py" -o "$CODE/stage34.py.download"
test "$(git hash-object "$CODE/stage34.py.download")" = "cc831a551a7f53cf3ecf3d37926217c2f18a5386"
mv "$CODE/stage34.py.download" "$CODE/stage34.py"
python3 -B -m py_compile "$CODE/stage34.py"
python3 -B "$CODE/stage34.py" --self-test
python3 -B "$CODE/stage34.py" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

Outputs:
`stage34_TERN_0p06ha_stem_to_site_biomass_science_HOLD.json`,
`stage34_site_2014_stem_value_transfer_arithmetic_candidates.tsv`.
The 2014 field observed height finding **27/103 Acacia
stem IDs above default FATES7 cap** remains separate;
source 2018 derived AGB still not approved for model
calibration. Never substitute D20 at 0.2m for DBH
at 1.3m. PFT, soil, forcing and AD400 HOLD unchanged.

## 3ak. Stage34 operator SUCCESS — uniquely matched Plant99 1b source arithmetic; Stage35 original source provenance counterfactuals

**Actual Stage34 operator SUCCESS**:
`/home/ly3n24/ozflux_stage34_20261102T193337Z`.
SHA verified:
- original 222-row TERN basal D20 stem CSV `7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55`;
- original 2-row official TERN stand biomass CSV `f4fcfe46fd5132ed040187ae443441d37822e18c8deb48c01be667af51b9fea8`.

Exact original Decimal source arithmetic across **111 distinct stem keys,
2014 field vs 2018 derived (222 rows)** with TERN publisher's
**0.06ha actual sampled subplot** and 4-decimal stand t/ha:
- 2014 official stand 37.4168 t/ha (2245.008 kg implied);
  raw original 111 stem AGB total **2247.437182506 kg**,
  so stem-minus-stand **+2.429182506 kg**.
- 2018 official stand 44.6277 t/ha (2677.662 kg implied);
  raw original 111 derived stem AGB total **2675.232142231 kg**,
  so stem-minus-stand **−2.429857769 kg**.
- Pooled two-year mass difference from published rounded site
  totals only **−0.000675263 kg**, below 4dp site precision.
- Of all **111 original 2014 source stem AGB entries**, EXACTLY
  ONE produces both published stand AGB values to 4dp when
  hypothesizing *omission of its 2014 value from 2014*
  and *additional inclusion of that same 2014 value in
  the 2018 aggregate*:
  **`Eremophila latrobei ssp glabra`, site Alice Mulga,
  plot Alice Mulga, core1ha, Plant ID 99, Stem ID 1b,
  original phenomenonTime `22/1/2014`, AGB
  `2.429615547 kg`**.
  Two recalculated scenario stands:
  2014 **37.41679278265 t/ha -> 37.4168**;
  2018 **44.6276959629666667 t/ha -> 44.6277**.
  The match includes original output precision, not
  an invented adjustment. THIS IS **AN ARITHMETIC HYPOTHESIS**,
  not a verified publisher grouping/join error nor
  permission to edit TERN data.
- The underlying 2018 per-stem derived AGB itself remains
  scientifically questionable based on Stage30–32 and
  NOT APPROVED for model calibration. Official stand values
  are from the same dataset lineage and thus not independent
  biomass validation.

TERΝ dataset metadata cites a source 0.06ha stem subplot and
Návar (2013) AGB allometry; 2018 repeat individual field stem
census was not done for this product. Source:
https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed
Separate historical archived 2018 core1ha AGB dataset may
help a later independent cross-product comparison:
https://researchdata.edu.au/vegetation-data-direct-ha-2018/1340784
but its stems / units / survey methodology MUST be
separately inventoried and cannot be assumed identical.

**Stage35 original-Plant99 two-year source-row forensic and seven
counterfactual tests PUBLISHED, operator execution pending**:
`scripts/stage35/35_asm_Plant99_AGB_year_grouping_counterfactual_and_provenance_READONLY.py`
pinned GitHub commit `07029e39bc51da7c991ac200ec4e68b9626de039`
and git blob `76ecbdec3b27a69604091a1d67c697a7b895b4c4`.
A synthetic regression test was corrected before first operator release to use a nonzero 2018 stand fixture; an all-zero fixture would have been ambiguous with the omit-both case. The corrected source remains operator-UNTESTED.
It independently reopens all original sources and exact Stage34
one-candidate receipt, displays both raw 2014/2018 Plant99 1b
records including dates, stemStatus and comment, and computes
seven different original year inclusion/exclusion interpretations.
It explicitly distinguishes (a) omission only, (b) addition
only, (c) omit 2014 and add 2014 value to 2018,
(d) replace 2018 value with 2014 value, (e) add extra 2018
value, and (f) omit both years; only a mathematical source
arithmetic match is possible without the official code.
No source/model write, Slurm, or AD400.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="07029e39bc51da7c991ac200ec4e68b9626de039"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage35_code"
OUT="$HOME/ozflux_stage35_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage35/35_asm_Plant99_AGB_year_grouping_counterfactual_and_provenance_READONLY.py" -o "$CODE/stage35.py.download"
test "$(git hash-object "$CODE/stage35.py.download")" = "76ecbdec3b27a69604091a1d67c697a7b895b4c4"
mv "$CODE/stage35.py.download" "$CODE/stage35.py"
python3 -B -m py_compile "$CODE/stage35.py"
python3 -B "$CODE/stage35.py" --self-test
python3 -B "$CODE/stage35.py" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

Outputs:
`stage35_Plant99_seven_AGB_year_grouping_counterfactuals.tsv`
and `stage35_Plant99_original_source_stand_biomass_science_HOLD.json`.
Following operator success, ask dataset maintainers
`esupport@tern.org.au` for exact site-level grouping/filtering
steps / source code and biomass method, and direct DBH field
survey records, supplying only reproducible source IDs
and stand residuals. Do not assert a publisher defect
unless confirmed. No direct D20=DBH substitution,
science approval, FATES surface modification or AD400.

## 3al. Stage35 actual SUCCESS; evidence frozen for TERN curator inquiry (no further diagnostic stage)

**Stage35 operator result SUCCESS 2026-11-02**:
`/home/ly3n24/ozflux_stage35_20261102T194156Z`.
Pinned GitHub script SHA and regression selftest PASSED, and
original 222-row stem source, 21-row dictionary,
official 2-row stand source and Stage34 one-candidate receipt
were verified. Actual original Plant99 stem 1b has:

| Original source column | 2014 FIELD | 2018 DERIVED |
|---|---|---|
| Scientific name | Eremophila latrobei ssp glabra | same |
| Site / plot | Alice Mulga / Alice Mulga, core1ha | same |
| plantId, stemId | 99, 1b | 99, 1b |
| phenomenonTime | 22/1/2014 | 1/6/2018 |
| stemDiameter_centimeters (**D20 at 0.2m**) | 4.6 | 5.3 |
| stemHeight_metres | 1.9 | 1.9 |
| aboveGroundBiomass_kilograms | **2.429615547** | **3.713499951** |
| stemStatus / comment | Alive / NA | Alive / NA |

**Seven original-source arithmetic scenarios** were tested with
exact `Decimal` numerics and TERN's 0.06ha sampled stem area.
Exactly ONE of these seven tests reproduces both site-year
stand values after rounding to 4 decimal t/ha:
`OMIT_2014_AND_EXTRA_2014_AGB_IN_2018`.
2014: `(2247.437182506 - 2.429615547)/60`
= **37.41679278265 t/ha**, published **37.4168**;
2018: `(2675.232142231 + 2.429615547)/60`
= **44.6276959629666667 t/ha**, published **44.6277**.

The other six tested original-source inclusion/exclusion
hypotheses do not match BOTH published site-year values:
direct all rows, 2014 omit only, 2018 add only, 2018
replacement, extra 2018 derived value, omit both years.
This match is UNIQUE AMONG TESTED SCENARIOS ONLY:
not proof the actual data producer made this edit, not
proof of a row join error, and not a license to change
the original dataset or use 2018 derived AGB in FATES.
There could be legitimate hidden grouping, parameter,
source-version, QA or aggregation rules.

**Frozen reproducible technical evidence note:**
[STAGE35_TERN_AGB_PROVENANCE_QUERY_20261102.md](STAGE35_TERN_AGB_PROVENANCE_QUERY_20261102.md).
It contains exact dataset links, source SHA256s, 0.06ha
stand-stem reconciling arithmetic, Stem99 source identifiers,
the seven scenarios, separate Stage30–32 2018 AGB
association anomalies and focused factual questions
for the dataset authors. All source files / Stage35 reports
remain on IRIDIS6 (NOT committed as data to GitHub);
no email or public bug report has yet been SENT.

**Recommended resolution path:** Ask the dataset publisher or
TERN Data Support (official `esupport@tern.org.au`) for
the exact AGB computation formula and grouping/selection
code, site vs subplot area and source cohort, plus
2018 stem-to-AGB mapping/version history. Reconcile
with the *separate* original true 1.3m-DBH survey if
the data become available. Do not create additional
exploratory forensic stages unless the curator provides
new source evidence. The 2014 *measured* Mulga height
constraint (27/103 Acacia stems above FATES7 default
4.735410175m cap) remains independent of 2018 AGB.
PFT/surface/soil/final forcing science checks and full
AD400/Normal400 have NOT been approved.

## 3am. NEW OPERATOR PRIORITY 2026-11-02 — 2018-first, independent field source before derived AGB

**Operator explicitly requested 2018 latest relevant vegetation evidence
and GitHub-only synchronization (do not initiate more email).**
Source-priority evidence: [STAGE36_2018_FIRST_OBSERVATION_PRIORITY_20261102.md](STAGE36_2018_FIRST_OBSERVATION_PRIORITY_20261102.md).
The earlier Stage30–35 evidence is preserved, not reanalysed.

An **independently catalogued 2018** Alice Mulga Core 1ha standing
AGB/individual-stem dataset exists in ARDC/TERN historical metadata:
https://researchdata.edu.au/vegetation-data-direct-ha-2018/1340784 ,
original identifier **supersite.1041**, **edition 5**,
TERN SuperSite Network, Eamus.
The catalog describes **2018 measured D20 (20cm), height**, and
**2011–2018 dendrometer records**, allometric Paul et al. (2016)
and Návar et al. (2013). Its historical link to
`https://supersites.tern.org.au/knb/metacat/supersite.1041/html`
currently redirects or is inaccessible in search; the actual
2018 edition 5 ORIGINAL RAW FILES HAVE NOT BEEN OBTAINED.
Never invent a direct downloadable filename, interpret metadata
as data, or assume this archived survey shares the 111-stem
cohort and sampled area with Cleverly (2022)'s 2018-derived
table. The latter's metadata says **no individual stem survey
was repeated in 2018**, while the older independent catalog
says measurements **were taken in 2018**. Their lineage and
identities MUST be reconciled only after acquiring raw records.

**Stage36 2018-first read-only evidence intake PUBLISHED,
operator run pending:** 
`scripts/stage36/36_asm_2018_first_independent_survey_locator_and_source_audit_READONLY.py`,
GitHub commit `b7ec1abdcddff54f8c9001391f12e579c1ea8654`,
Git blob `f4ecf1e4f8a3f8e06de6e9da0e26bf7da3e18df9`.
It verifies original Stage25 stem SHA256, Stage33 stand SHA256,
and successful Stage35 receipt; extracts exact 111 published
**2018 DERIVED** individual stem rows into a read-only TSV
with the source tier clearly labelled SECONDARY, audits species,
D20/height and FATES7 cap counts (9/43 A. aneura and
18/60 A. aptaneura, but height not new independent
2018 field measurements), and probes ONLY the exact ARDC
2018 and legacy TERN metadata catalog URLs. Metadata probes
are NOT automated raw data downloads. Report marks raw
primary 2018 field source **NOT YET SHA VERIFIED**.
No model, original, surface, forcing, Slurm or AD400 edits.

~~~bash
(
set -euo pipefail
conda activate clm_fates_env
COMMIT="b7ec1abdcddff54f8c9001391f12e579c1ea8654"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/OzFlux_MultiSite_09"
CODE="$HOME/ozflux_stage36_code"
OUT="$HOME/ozflux_stage36_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CODE"
curl -fLsS --retry 3 "$BASE/scripts/stage36/36_asm_2018_first_independent_survey_locator_and_source_audit_READONLY.py" -o "$CODE/stage36.py.download"
test "$(git hash-object "$CODE/stage36.py.download")" = "f4ecf1e4f8a3f8e06de6e9da0e26bf7da3e18df9"
mv "$CODE/stage36.py.download" "$CODE/stage36.py"
python3 -B -m py_compile "$CODE/stage36.py"
python3 -B "$CODE/stage36.py" --self-test
python3 -B "$CODE/stage36.py" --out "$OUT"
echo "REPORT_DIR $OUT"
)
~~~

Expected new HOME outputs only:
`stage36_AU_ASM_2018_first_independent_survey_source_gate.json`;
`stage36_SECONDARY_2018_derived_111_stem_original_source_evidence.tsv`.
No direct 2018 independent field measurement scientifically approved
until its original archive source bytes and metadata are verified.
The 2018 derived *stand* 44.6277 t/ha is a source estimate,
**not** an approved empirical 2018 live biomass target.
If original 2018 field survey sources become accessible, intake
them first; then independently QC D20/height, taxonomic composition,
sampling area and temporal footprint before using for FATES
structure/biomass evaluation. D20 must never become DBH without
a site-specific evidenced transformation. Existing 2014 allometry
and 2018 AGB review remain documented, with NO further historic
forensic stages unless new source evidence emerges.

## 3an. Stage36 operator success and selected OzFlux09 FIXNC PFT v1.1 handoff

**Stage36 actual IRIDIS6 operator SUCCESS**:
`/home/ly3n24/ozflux_stage36_20261102T201012Z`.
Original 111 per-stem 2018 *derived* records and 44.6277 t/ha
published derived stand data SHA verified, but catalog probes
returned HTTP 404 for the separate ARDC independent 2018
survey and a generic TERN portal redirect for the legacy
`supersite.1041` URL. Thus NO original independent 2018 survey
table has been downloaded; do not treat catalog metadata as data.

**New user decision:** Use the accepted 2026-11-02 OzFlux 9-site
PFT v1.1 PRIMARY model-hypothesis values from source branch
`oz-jp-pft-guidance-20261102`, immutable commit
`d62c814585c4aa85731f77b4a555efe6ec9e94a3`,
`examples/OzFlux_JapanFlux_PFT/`. Main does NOT contain that
branch's PFT directory; the non-competition repository now
contains original-blob-pinned nine-site CLM 15-class host PFT,
FATES PFT and validation snapshots:
https://github.com/lyanyeung/Non-Competition-CLM-experiment/tree/main/examples/OzFlux_Batch01_09 .
All bare `host0` shares are RETAINED, PFT model mode FIXNC
(`use_fates_nocomp=.true.`,
`use_fates_fixed_biogeog=.true.`),
mapping DEFAULT14. The operator accepts the scientific
PFT allocation AS A MODEL SCENARIO, not a measured land-cover fact.
Do not continue historical AU-ASM PFT4/7 ambiguity as a blocker.

**Next real HPC action:** Run the nine-site source-PFT
Git blob and bounded original L6/Surface/DATM readiness inventory
from `Non-Competition-CLM-experiment/examples/OzFlux_Batch01_09/`.
It is read-only; after its operator PASS, create NEW PFT-specific
point surface candidates, retain original soil as an explicitly
stated reference where acceptable, independently verify exact
FATES per-case effective mappings and DATM physics, and then
start isolated **AD5** before AD400. No Slurm job is currently
authorized by Stage36 or the GitHub PFT numeric review alone.
AU-How's old competition case is NOT a FIXNC candidate and must
be retained unchanged. Forcing and surface readiness remain
independent per-site gates (the other 8 sites are not automatically
ready because AU-ASM has 6 candidate DATM years).

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

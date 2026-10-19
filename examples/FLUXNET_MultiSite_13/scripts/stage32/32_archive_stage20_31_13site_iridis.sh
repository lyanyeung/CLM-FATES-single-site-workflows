#!/usr/bin/env bash
# One-shot code-only publication of the REAL IRIDIS6 Stage20..31 scripts.
# Use on IRIDIS in the existing Git checkout. No simulations/data are modified.
set -Eeuo pipefail
trap 'rc=$?; echo "ERROR at line $LINENO, code $rc. No further Git action executed." >&2' ERR

REPO="${REPO:-$HOME/CLM-FATES-single-site-workflows}"
REL="examples/FLUXNET_MultiSite_13"
DEST="$REPO/$REL"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$HOME/FLUXNET13_GITHUB_STAGE20_31_${STAMP}.log"
SITES=(DE-Lnf DE-Obe ES-Agu ES-LJu IT-Col DE-Gri DE-RuR FI-Hyy FI-Let FR-Pue GF-Guy IT-MBo IT-Tor)

msg(){ printf '%s\n' "$*" | tee -a "$LOG"; }
fail(){ msg "STOP: $*" >&2; exit 1; }
[[ -d "$REPO/.git" && -d "$DEST" ]] || fail "Expected repository missing: $REPO"
command -v git >/dev/null || fail 'git missing'
cd "$REPO"
[[ "$(git branch --show-current)" == main ]] || fail 'Repository must be on main; no branch automatically switched'
[[ -n "$(git remote get-url origin)" ]] || fail 'Missing origin remote'
# Check remote connectivity BEFORE writing files/committing.
git ls-remote --exit-code origin refs/heads/main >/dev/null || fail 'origin/main unreachable or authentication denied'
git fetch --quiet origin main
if ! git merge-base --is-ancestor origin/main HEAD; then
  fail 'Local main is behind/diverged from origin/main. Reconcile first; refusing non-fast-forward push.'
fi
# Never swallow pre-existing staged changes from another experiment.
if git diff --cached --name-only | grep -q .; then
  fail 'Existing staged files found: git diff --cached --name-only. Commit/unstage them before this script.'
fi

mkdir -p "$DEST/scripts" "$DEST/docs"
msg "Repository: $REPO"
msg "Remote: $(git remote get-url origin)"
msg 'Source: actual IRIDIS HOME scripts; GitHub already contains historical stages 00-19.'

# Stage-to-filename mapping. Preserve stage24 read-only BIF and stage29 failed prototype for method history.
# Prefer actual files in HOME. If an identically named file is already tracked in this example,
# compare hashes and never replace it silently.
MAP=(
'20:20_onepass_13site_meteorology_preBIF.py'
'20:20_onepass_preBIF_README.md'
'21:21_onepass_13site_meteorology_remaining_preBIF.py'
'21:21_onepass_preBIF_GUIDE.md'
'22:22_onepass_full_QC1_envelopes_preBIF.py'
'22:22_whole_QC1_run_GUIDE.md'
'24:24_audit_13site_BIF_heights_preZBOT.py'
'25:25_batch_13site_MET_fasttrack_review.py'
'26:26_three_site_MET_conservative_trial.py'
'26:26_three_site_MET_GUIDE.md'
'27:27_freeze_13site_met_provisional.py'
'28:28_onepass_remaining7_MET_finalize.py'
'29:29_onepass_13site_BIF_ZBOT.py'
'29:29b_onepass_13site_dynamic_static_ZBOT_DATM.py'
'30:30_complete_2site_ZBOT_DATM.py'
'31:31_onepass_13site_spinup1000_exclusive.py'
)
missing=0; added=0; already=0; variants=0
for entry in "${MAP[@]}"; do
  stage="${entry%%:*}"; base="${entry#*:}"
  # Search HOME first; the user may also have placed downloaded scripts inside the repo.
  src="$HOME/$base"
  if [[ ! -f "$src" ]]; then
    candidate="$REPO/$REL/scripts/stage$(printf '%02d' "$stage")/$base"
    if [[ -f "$candidate" ]]; then src="$candidate"; fi
  fi
  if [[ ! -f "$src" ]]; then
    msg "MISSING $base (real original code not found; never fabricate code)"
    missing=$((missing+1))
    continue
  fi
  [[ "$base" == *.py || "$base" == *.sh || "$base" == *.md ]] || fail "Unexpected file extension: $base"
  [[ $(stat -c %s "$src") -le 524288 ]] || fail "Source >512KB; review before publication: $src"
  sub="stage$(printf '%02d' "$stage")"
  [[ "$base" == 29b_* ]] && sub="stage29b"
  target="$DEST/scripts/$sub/$base"
  mkdir -p "$(dirname "$target")"
  if [[ -e "$target" ]]; then
    if cmp -s "$src" "$target"; then
      msg "ALREADY $REL/scripts/$sub/$base"
      already=$((already+1))
      continue
    fi
    # No overwrite of existing committed or user-edited historical versions.
    target="$DEST/scripts/$sub/${base%.*}_IRIDIS_${STAMP}.${base##*.}"
    variants=$((variants+1))
    msg "DIFFERENT HISTORIC VERSION retained separately: $(realpath --relative-to="$REPO" "$target")"
  fi
  install -m 0644 "$src" "$target"
  msg "ADDED $(realpath --relative-to="$REPO" "$target")"
  added=$((added+1))
done

# Backfill a missing/renamed stage23 code if it is available in home: don't fake stage23.
shopt -s nullglob
stage23=("$HOME"/23*.py "$HOME"/23*.sh)
shopt -u nullglob
for src in "${stage23[@]}"; do
  [[ -f "$src" ]] || continue
  base="$(basename "$src")"
  [[ $(stat -c %s "$src") -le 524288 ]] || continue
  dest="$DEST/scripts/stage23/$base"
  mkdir -p "$(dirname "$dest")"
  if [[ ! -e "$dest" ]]; then
    install -m 0644 "$src" "$dest"
    msg "ADDED stage23 source $base"
    added=$((added+1))
  fi
done

# Source surface scripts from IRIDIS if not already present in GitHub tree.
shopt -s nullglob
surface_candidates=("$HOME"/02_make_13_surfaces.sh "$HOME"/make_13_surfaces.sh "$HOME"/02_make_13_surfaces.py "$HOME"/make_13_surfaces.py)
shopt -u nullglob
for src in "${surface_candidates[@]}"; do
  [[ -f "$src" ]] || continue
  base="$(basename "$src")"
  [[ $(stat -c %s "$src") -le 524288 ]] || continue
  dest="$DEST/scripts/stage02/$base"
  mkdir -p "$(dirname "$dest")"
  if [[ ! -e "$dest" ]]; then install -m 0644 "$src" "$dest"; msg "ADDED surface source $base"; fi
done

# Capture a small PUBLIC and READ-ONLY initial case configuration snapshot.
# Do not ingest runtime logs, outputs, licensed data, or user credentials.
CASE_ROOT="/iridisfs/scratch/${USER}/CLM_FATES/cases"
SNAP="$DEST/docs/stage31_13site_initial_case_settings.tsv"
{
 printf 'site\tcase\tinitial_forcing_year\tstop_n\trest_n\tresubmit_remaining_at_snapshot\tatm_ncpl\tcalendar\tco2_ppm\tcase_exists\n'
 for site in "${SITES[@]}"; do
   case="$CASE_ROOT/${site}_FATES_SPINUP1000_S30EXCL"
   if [[ -x "$case/xmlquery" ]]; then
     q(){ (cd "$case" && ./xmlquery "$1" --value 2>/dev/null | tr -d '\r\n[:space:]') || true; }
     first="$(q RUN_STARTDATE)"; stop="$(q STOP_N)"; rest="$(q REST_N)"
     re="$(q RESUBMIT)"; ncpl="$(q ATM_NCPL)"; cal="$(q CALENDAR)"; co2="$(q CCSM_CO2_PPMV)"
     printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tYES\n' "$site" "${site}_FATES_SPINUP1000_S30EXCL" "$first" "$stop" "$rest" "$re" "$ncpl" "$cal" "$co2"
   else
     printf '%s\t%s\t\t\t\t\t\t\t\tNO\n' "$site" "${site}_FATES_SPINUP1000_S30EXCL"
   fi
 done
} > "$SNAP"

# Do not upload sample records, forcing CSVs, EC observations, ERA files, NETCDFs, Slurm outputs.
# Append non-duplicating, method-specific README section; Stage30 may already be present.
README="$DEST/README.md"
[[ -f "$README" ]] || fail "Missing README.md: $README"
if ! grep -Fq '<!-- MET_BIF_DATM_SPINUP_13_20261018 -->' "$README"; then
cat >> "$README" <<'MD'

<!-- MET_BIF_DATM_SPINUP_13_20261018 -->
## October 2026 implementation update — MET, BIF/ZBOT, DATM and 1000-year spin-up

This section documents **the actual October 18, 2026 IRIDIS6 research run**, superseding earlier Stage22 planning or failed collision notes where later results exist. The scripts in `scripts/stage20` through `scripts/stage31` include successful revisions, **read-only audits, and explicitly marked experimental/failed prototypes**; not every historical script represents the selected forcing.

### Meteorology: Stage20–28

- Stage20 added 58 tentative QC1/2 half-hour replacements (DE-Gri 11; FI-Let 47). Stage21 performed no additional edits. Stage22 successfully added 76 tentative replacements (DE-Gri 7; FI-Let 69) using whole QC1 envelope checks. The full modification ledger and provenance remain on IRIDIS.
- Stage25 reviewed the source provenance of heavy rainfall and abnormal temperature; Stage26 produced one additional FI-Hyy VPD half-hour candidate. Stage28 screened seven remaining sites, added **zero** new bounded replacements and inherited Stage26 plus Stage22 candidates.
- All 13 Stage28 selections passed numeric hard QC. **Scientific MET approval remains open for every station.** There were 69 pending MDS flagged blocks (49 DE-Gri; 20 FI-Let), 20 half-hour temperature steps exceeding 12 °C, 9 RH records below 1%, and 14 half-hour rain events exceeding 40 mm in the Stage28 check. Flagged extremes are not automatically false observations.
- ES-LJu has 24 >18 mm/30-minute rain entries at 23:00, suggesting possible daily accumulation/timestamp semantics. Do not redistribute precipitation across half-hours without independent evidence. Reanalysis products are not independent tower ground truth.
- **Selected MET versions:** Stage28 provisional manifest on IRIDIS. Do not confuse automatic numeric PASS with scientific approval.

### Measurement height: Stage23–30

- Stage23/24 audited dated FLUXNET BIF air-temperature (TA_F) and wind (WS_F) sensor heights, deduplicating identical BIF records. The Stage29b implementation maps original non-halfhour BIF events to 30-minute forcing timestamps without silently rounding source metadata.
- Eleven sites use direct dated BIF TA heights: **five with time-varying heights** (DE-RuR, FI-Hyy, FI-Let, FR-Pue, IT-MBo) and **six with a single constant TA height** (DE-Obe, ES-Agu, ES-LJu, DE-Gri, GF-Guy, IT-Tor). Pre-first-height historical records use the first documented TA height under an **explicit provisional extrapolation assumption**.
- **DE-Lnf**: `ZBOT = 44 m` as a static candidate, based on Jürgensen et al. (2021), *Forests* **12**, 1693, https://doi.org/10.3390/f12121693, reporting an air-temperature/humidity sensor at 44 m. Treating this as unchanged over 2002–2024 is a historical assumption.
- **IT-Col**: `ZBOT = 32 m` is **only a site measurement-height proxy**, **not verified TA sensor height**; see Keenan et al. (2009), *Biogeosciences* **6**, 1423–1444, https://doi.org/10.5194/bg-6-1423-2009. Confirmation of the temperature sensor height is still outstanding.
- FI-Hyy has 122,640 half-hour records with a documented TA vs WS height separation above 3 m. Wind measurements were **not** vertically adjusted in the ZBOT workflow.

### DATM: Stage29b–30

- Stage29b created and verified 229 annual ZBOT-only and 229 annual full-DATM NetCDF files for 11 sites. Stage30 added DE-Lnf (23 annual files) and IT-Col (19 annual files). **The consolidated Stage30 manifest contains 271 annual DATM NetCDF files across all 13 stations.** Earlier 229 files were rechecked by SHA256 and not overwritten.
- Datetime convention: `NO_LEAP`, 48 half-hour records/day, 17,520 per model year. DATM includes TBOT, QBOT, PSRF, FSDS, FLDS, WIND, PRECTmms, and ZBOT. The MET input, surface NetCDFs, source BIF and DATM NetCDFs are not included in this repository.
- The 13-site surface existence check reported 13/13 `READY`; **file existence alone does not certify vegetation/PFT or soil representation**. The actual surface creation source is maintained under `scripts/stage02`.

### Stage31: initial 1000-model-year spin-up submission

- On **18 October 2026**, the 13 cases `${SITE}_FATES_SPINUP1000_S30EXCL` successfully submitted their initial Slurm run and archive jobs. **Submission is not completion or convergence.**
- Each site's intended duration is **1000 model years**, with 5-year segments (`STOP_N=5`, `REST_N=5`, `RESUBMIT=199`) and full-record `DATM taxmode=cycle`, `NO_LEAP`, `ATM_NCPL=48`, startup initialization and a fixed first-forcing-year global annual-average CO2 concentration.
- Initial submissions use `./case.submit --batch-args=--exclusive`: Slurm requests exclusive compute nodes for those jobs **but this does NOT enforce one site at a time**, and the behaviour of automatic re-submissions must be checked independently. Queue states `QOSMaxNodePerUserLimit` mean a user allocation limit and not a concurrent CPU oversubscription.
- The generated CIME cases and all model history/restart/output remain on IRIDIS, not in Git. Scientific review of MET extremes, height assumptions and PFT/land cover remains open; the spin-ups are provisional experiments.

### Reproduction order

`surface (stage02) → MET (stage20–28) → BIF height audit (stage23/24) → dynamic/static ZBOT and DATM (stage29b) → published-height assumptions (stage30) → CIME spin-up case creation/submission (stage31)`.

Do not run historic trial scripts blindly on existing experiment directories. Each selected input is pinned by its report manifest SHA256 on IRIDIS. Source scripts document procedures; no licensed FLUXNET observations, ERA files, forcing CSVs, NetCDF products, CIME run/archive files, HPC logs, or credentials are committed here.
MD
msg 'APPENDED README: validated provenance and source citations'
else
msg 'README appendix already exists; preserved as is'
fi

# Defensive staging: only source code (script files) and text docs under this exact example.
# Git ignore settings are not bypassed; display ignored files so incomplete archives are visible.
git add -- "$REL/README.md" "$REL/scripts" "$REL/docs/stage31_13site_initial_case_settings.tsv"
staged="$(git diff --cached --name-only)"
if [[ -z "$staged" ]]; then
  msg 'NO CHANGES to publish; existing GitHub content appears current.'
  exit 0
fi
while IFS= read -r file; do
  [[ "$file" == "$REL/"* ]] || fail "Unexpected staged path: $file"
  case "$file" in
    *.py|*.sh|*.md|*.tsv) ;;
    *) fail "Unsafe extension staged: $file";;
  esac
  case "$file" in
    *.nc|*.csv|*.zip|*.grib|*.npz|*.h5|*.log) fail "Data file staged: $file";;
  esac
  [[ $(stat -c %s "$REPO/$file") -le 524288 ]] || fail "Large file staged: $file"
done <<< "$staged"
msg '=== STAGED FILES ==='
git diff --cached --stat | tee -a "$LOG"
msg "Files newly copied: $added; existing identical: $already; different historic variants: $variants; missing originals: $missing"
# Fix imports/typos locally before pushing if necessary; do NOT run old scripts.
if command -v python >/dev/null; then
  while IFS= read -r f; do
    case "$f" in *.py) python -m py_compile "$REPO/$f" >/dev/null || fail "Python syntax invalid: $f";; esac
  done <<< "$staged"
fi
msg 'Committing code/doc files only (source-data and run outputs excluded)'
git commit -m "Archive FLUXNET 13-site MET BIF DATM and 1000-year CIME submission workflows"
git push origin main
msg '=== GITHUB PUBLICATION COMPLETED ==='
git log -1 --oneline | tee -a "$LOG"
msg "URL: https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/$REL"
msg "LOCAL_LOG: $LOG (not committed)"

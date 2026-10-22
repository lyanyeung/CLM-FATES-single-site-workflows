#!/usr/bin/env bash
# Upload only already-generated small diagnostics from frozen IRIDIS6 snapshots.
# Runs on LOGIN with mounted RFS + authenticated git remote.
# Safe from conflicted local repo: uses a fresh clone into a unique HOME directory.
# Modes: --audit (read only), --publish (clone/copy/commit/push; requires explicit action)
set -Eeuo pipefail
MODE="${1:---audit}"
[[ "$MODE" == --audit || "$MODE" == --publish ]] || { echo "Usage: bash $0 --audit|--publish" >&2; exit 2; }
ROOT="$HOME/CLM-FATES-single-site-workflows"
REPO_DIR=carbon_flux_convergence_diagnostics
RFS=/research/xclimatetbm/ly3n24/CLM_FATES
PHASE="$RFS/Spinup_Analysis/vegc_convergence_15site/phase_aligned/20261021T235330Z_15site_FullCycle_VegC"
BORDER="$RFS/Spinup_Analysis/vegc_convergence_15site/borderline_second_review/20261022T011032Z_four_site_review"
FLUX="$HOME/CLM_FATES_FluxStationarity/staging/20261022T012831Z_4site_NEE_then_GPP"
NINE="$RFS/FLUXNET_MultiSite_11/spinup1000_final"
SIX=(DE-Hai RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat)
ALL=(DE-Hai RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat AT-Neu BE-Bra CH-Cha CH-Fru CH-Lae CZ-Stn FI-Sod FR-Fon GL-ZaH)
FOUR=(DE-Tha NL-Loo BE-Bra FR-Fon)
check(){ [[ -f "$1" && ! -L "$1" ]] || { echo "MISSING/nonregular: $1" >&2; return 1; }; }
declare -a SOURCES=()
# Validate every needed source BEFORE git cloning and copying.
for site in "${ALL[@]}"; do
 for suffix in "_01_fullcycle_nested_VegC_trends.png" "_02_independent_blocks_and_cycle_drift.png" "_phase_aligned_metrics.csv" "_last4_aligned_cycle_pairs.csv"; do
   SOURCES+=("$PHASE/$site/$site$suffix")
 done
done
for file in all15_fullcycle_vegc_summary.csv PROVENANCE_AND_METHODS.json; do
  # Original phase script produced PROVENANCE_AND_METHODS.json? It used that exact name.
  SOURCES+=("$PHASE/$file")
done
for site in "${FOUR[@]}"; do
 for suffix in "_borderline_second_review.png" "_all_complete_cycle_signed_jumps.csv" "_last_four_phase_matched_pairs.csv"; do SOURCES+=("$BORDER/$site/$site$suffix");done
 for suffix in "_NEE_cycle_mean_stability.png" "_GPP_cycle_mean_stability.png" "_annual_model_fluxes.csv" "_complete_cycle_means.csv" "_paired_fullcycle_flux_differences.csv";do SOURCES+=("$FLUX/$site/$site$suffix");done
done
for file in four_site_borderline_second_review.csv METHODS_AND_PROVENANCE.json;do SOURCES+=("$BORDER/$file");done
for file in four_site_flux_stationarity_summary.csv PROVENANCE.json;do SOURCES+=("$FLUX/$file");done
for site in AT-Neu BE-Bra CH-Cha CH-Fru CH-Lae CZ-Stn FI-Sod FR-Fon GL-ZaH; do SOURCES+=("$NINE/$site/${site}_carbon_annual_means.csv");done
missing=0
for source in "${SOURCES[@]}"; do check "$source" || missing=1;done
if ((missing));then echo 'STOP: missing at least one source. No git action taken.' >&2;exit 2;fi
echo "PREFLIGHT OK: ${#SOURCES[@]} source files available."
[[ "$MODE" == --publish ]] || { echo "AUDIT ONLY; no data uploaded or changed."; exit 0; }
[[ -d "$ROOT/.git" ]] || { echo "Expected local repo not found: $ROOT" >&2;exit 2; }
REMOTE=$(git -C "$ROOT" remote get-url origin)
WORK=$(mktemp -d "$HOME/carbonflux_publish_XXXXXXXX")
echo "Fresh clone: $WORK"
git clone -q --single-branch --branch main "$REMOTE" "$WORK/repo"
cd "$WORK/repo"
[[ -f "$REPO_DIR/METHODS.md" ]] || { echo "New diagnostics folder missing on origin/main" >&2;exit 2; }
for site in "${ALL[@]}"; do
  mkdir -p "$REPO_DIR/cases/$site/figures" "$REPO_DIR/cases/$site/data"
  cp -p "$PHASE/$site/${site}_01_fullcycle_nested_VegC_trends.png" "$REPO_DIR/cases/$site/figures/phase_aligned_nested_300_200_100.png"
  cp -p "$PHASE/$site/${site}_02_independent_blocks_and_cycle_drift.png" "$REPO_DIR/cases/$site/figures/phase_aligned_blocks_and_cycle_drift.png"
  cp -p "$PHASE/$site/${site}_phase_aligned_metrics.csv" "$REPO_DIR/cases/$site/data/phase_aligned_metrics.csv"
  cp -p "$PHASE/$site/${site}_last4_aligned_cycle_pairs.csv" "$REPO_DIR/cases/$site/data/last4_aligned_cycle_pairs.csv"
done
cp -p "$PHASE/all15_fullcycle_vegc_summary.csv" "$REPO_DIR/data/15_site_fullsource_phase_aligned_vegc.csv"
cp -p "$PHASE/PROVENANCE_AND_METHODS.json" "$REPO_DIR/data/15_site_source_provenance.json"
for site in "${FOUR[@]}";do
 cp -p "$BORDER/$site/${site}_borderline_second_review.png" "$REPO_DIR/cases/$site/figures/second_round_vegc_review.png"
 cp -p "$BORDER/$site/${site}_all_complete_cycle_signed_jumps.csv" "$REPO_DIR/cases/$site/data/all_fullcycle_vegc_jumps.csv"
 cp -p "$BORDER/$site/${site}_last_four_phase_matched_pairs.csv" "$REPO_DIR/cases/$site/data/second_review_vegc_four_pairs.csv"
 for flux in NEE GPP; do
   cp -p "$FLUX/$site/${site}_${flux}_cycle_mean_stability.png" "$REPO_DIR/cases/$site/figures/${flux}_multicycle_stability.png"
 done
 cp -p "$FLUX/$site/${site}_annual_model_fluxes.csv" "$REPO_DIR/cases/$site/data/annual_model_fluxes.csv"
 cp -p "$FLUX/$site/${site}_complete_cycle_means.csv" "$REPO_DIR/cases/$site/data/flux_complete_cycle_means.csv"
 cp -p "$FLUX/$site/${site}_paired_fullcycle_flux_differences.csv" "$REPO_DIR/cases/$site/data/paired_flux_cycle_differences.csv"
done
cp -p "$BORDER/four_site_borderline_second_review.csv" "$REPO_DIR/data/4_site_fullsource_borderline_review.csv"
cp -p "$BORDER/METHODS_AND_PROVENANCE.json" "$REPO_DIR/data/4_site_source_vegc_provenance.json"
cp -p "$FLUX/four_site_flux_stationarity_summary.csv" "$REPO_DIR/data/4_site_fullsource_flux_stationarity.csv"
cp -p "$FLUX/PROVENANCE.json" "$REPO_DIR/data/4_site_source_flux_provenance.json"
for site in AT-Neu BE-Bra CH-Cha CH-Fru CH-Lae CZ-Stn FI-Sod FR-Fon GL-ZaH; do
 cp -p "$NINE/$site/${site}_carbon_annual_means.csv" "$REPO_DIR/cases/$site/data/carbon_annual_means.csv"
done
git add "$REPO_DIR"
git diff --cached --check
echo "=== Staged diff summary ==="
git diff --cached --stat | tail -20
git diff --cached --quiet && { echo "No changes to publish";exit 0; }
git commit -m "Publish frozen 15-site fullcycle VegC and four-site NEE/GPP diagnostic evidence"
# Fail if origin advanced; do not auto-rebase published data without review.
git push origin HEAD:main
echo "PUBLISHED and VERIFIED push success. Fresh clone: $WORK/repo"

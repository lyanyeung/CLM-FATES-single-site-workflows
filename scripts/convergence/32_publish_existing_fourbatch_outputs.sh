#!/usr/bin/env bash
# Publish existing FLUXNET batch 6/8/11/13 RFS science36 snapshots.
# Only verified derived figures and statistics; NO model jobs or reanalysis.
# Batch failures explicitly retained in GitHub PUBLISH_STATUS.json.
set -Eeuo pipefail

REPO="${HOME}/CLM-FATES-single-site-workflows"
LOG="${1:-${HOME}/FLUXNET36_analysis.log}"
PY="${HOME}/.conda/envs/clm_fates_env/bin/python"
RUNNER="${HOME}/FLUXNET36_analysis.py"

[[ -s "${LOG}" ]] || { echo "Missing analysis log: ${LOG}" >&2; exit 1; }
[[ -x "${PY}" ]] || { echo "Python environment missing: ${PY}" >&2; exit 1; }
[[ -d "${REPO}/.git" ]] || { echo "Git checkout missing: ${REPO}" >&2; exit 1; }

cd "${REPO}"
git fetch origin main
git show origin/main:scripts/convergence/31_crossbatch_convergence_ec_36sites.py > "${RUNNER}"
"${PY}" -m py_compile "${RUNNER}"

declare -a snapshots
for batch in 6 8 11 13; do
  snapshot="$(awk -v b="${batch}" '$1=="BATCH" && $2==b && $3=="SUMMARY:" {
    for(i=1;i<=NF;i++) {
      if(index($i,"OUTPUT=")==1) print substr($i,8)
    }
  }' "${LOG}" | tail -n 1)"
  if [[ -z "${snapshot}" || ! -d "${snapshot}" ]]; then
    echo "Missing existing snapshot for batch ${batch}; check ${LOG}" >&2
    exit 1
  fi
  case "${snapshot}" in
    */FLUXNET_MultiSite_"${batch}"/convergence_snapshots/*_Batch"${batch}"_*_science36) ;;
    *) echo "Refusing mismatched batch ${batch} snapshot: ${snapshot}" >&2; exit 1 ;;
  esac
  snapshots+=("${snapshot}")
done

echo "========== VALIDATE ALL FOUR EXISTING SNAPSHOTS =========="
for snapshot in "${snapshots[@]}"; do
  echo "CHECK: ${snapshot}"
  "${PY}" -u -B "${RUNNER}" publish \
    --snapshot "${snapshot}" --allow-partial --dry-run
done

echo
echo "========== PUBLISH VERIFIED PLOTS TO GITHUB =========="
for snapshot in "${snapshots[@]}"; do
  echo "PUBLISH: ${snapshot}"
  "${PY}" -u -B "${RUNNER}" publish \
    --snapshot "${snapshot}" --allow-partial
done
echo "ALL FOUR BATCHES PROCESSED; see each GitHub PUBLISH_STATUS.json."

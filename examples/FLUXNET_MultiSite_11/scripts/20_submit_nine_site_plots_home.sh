#!/usr/bin/env bash
# Reproducible 9-site 1000-year plotting on IRIDIS6 compute nodes.
# Home is the ONLY write target; model NetCDF/EC sources under Scratch are READ ONLY.
# Important: /research/xclimatetbm was not accessible from red6066 (20 Oct 2026).
set -Eeuo pipefail
umask 077

REPO="$(cd -- "$(dirname -- "$0")/../../.." && pwd -P)"
PLOT="$REPO/examples/FLUXNET_MultiSite_11/scripts/19_plot_nine_site_spinup1000.py"
PY="$HOME/.conda/envs/clm_fates_env/bin/python"
POINTER="$HOME/.plot11_1000_latest"

[[ -f "$PLOT" && -x "$PY" ]] || {
  echo "Missing plotter or Python: $PLOT | $PY" >&2; exit 1;
}
[[ ! -e "$POINTER" ]] || {
  echo "Existing run pointer: $POINTER; transfer/publish/clean that run before another submission." >&2
  exit 1
}
"$PY" -B -c 'import numpy, pandas, netCDF4, matplotlib' || exit 1

# Timestamp plus random suffix prevents accidental overwrite of a prior run.
WORK="$(mktemp -d "$HOME/plot11_1000_HOME_$(date +%Y%m%d_%H%M%S)_XXXXXX")"
OUTPUT="$WORK/results"
CACHE="$WORK/cache"
TMP_HOME="$WORK/tmp"
mkdir -p "$OUTPUT" "$WORK/logs" "$CACHE/matplotlib" "$CACHE/xdg" "$TMP_HOME"

export REPO PY WORK OUTPUT CACHE TMP_HOME
export PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg
export MPLCONFIGDIR="$CACHE/matplotlib" XDG_CACHE_HOME="$CACHE/xdg"
export TMPDIR="$TMP_HOME" TMP="$TMP_HOME" TEMP="$TMP_HOME"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2

JOBFILE="$WORK/plot_nine_site_1000.sbatch"
cat > "$JOBFILE" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=plot11_1000
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=10:00:00
set -Eeuo pipefail

# Never source ~/.bashrc under set -u: IRIDIS6 bashrc uses BASHRCSOURCED.
# Never set any cache/TMPDIR or Slurm stdout/stderr to /research or Scratch.
cd "$HOME"
test -d "$OUTPUT" && test -w "$OUTPUT"
test -d "$TMP_HOME" && test -w "$TMP_HOME"
echo "PLOTTING START: $(date) on $(hostname)"
echo "Home output: $OUTPUT"

"$PY" -B "$REPO/examples/FLUXNET_MultiSite_11/scripts/19_plot_nine_site_spinup1000.py" \
  --repo "$REPO" --output-root "$OUTPUT"

"$PY" -B - <<'PY'
import csv, os
from pathlib import Path

root = Path(os.environ["OUTPUT"])
sites = ["BE-Bra", "FR-Fon", "GL-ZaH", "AT-Neu", "FI-Sod",
         "CH-Cha", "CH-Fru", "CH-Lae", "CZ-Stn"]
with (root / "nine_site_spinup1000_summary.csv").open(newline="") as fh:
    rows = list(csv.DictReader(fh))
assert len(rows) == 9 and {r["Site"] for r in rows} == set(sites)
for row in rows:
    site = row["Site"]
    assert row["Status"] == "OK", (site, row["Status"], row.get("ECError"))
    assert int(row["ArchiveYears"]) == 1000, site
    expected = (
        f"{site}_01_carbon_pools_annual_mean.png",
        f"{site}_02_carbon_pools_last250years.png",
        f"{site}_GPP_NEE_monthly_overview.png",
        f"{site}_carbon_annual_means.csv",
        f"{site}_convergence_metrics.csv",
        f"{site}_monthly_FATES_vs_EC.csv",
        f"{site}_monthly_metrics.csv",
        f"{site}_metadata.json",
    )
    for name in expected:
        item = root / site / name
        assert item.is_file() and item.stat().st_size > 0, item
assert len(list(root.rglob("*.png"))) == 27
assert len([p for p in root.rglob("*") if p.is_file()]) == 73
print("VERIFIED: 9 sites; 1000 years each; 27 PNG; 73 result files", flush=True)
PY

touch "$WORK/PLOTS_VALIDATED"
echo "PLOTTING COMPLETED: $(date)"
SBATCH

chmod 700 "$JOBFILE"
cd "$HOME"
JOBID="$(sbatch --parsable --export=ALL --chdir="$HOME" \
  --output="$WORK/logs/plot_%j.out" --error="$WORK/logs/plot_%j.err" "$JOBFILE")"
JOBID="$(printf '%s' "$JOBID" | cut -d';' -f1)"
[[ "$JOBID" =~ ^[0-9]+$ ]] || { echo "Unexpected sbatch job id: $JOBID" >&2; exit 1; }
printf '%s\n' "$JOBID" > "$WORK/jobid.txt"
printf '%s\n' "$WORK" > "$POINTER"

echo "SUBMITTED: $JOBID"
echo "HOME RUN: $WORK"
echo "STATUS: squeue -j $JOBID"
echo "LOG: tail -f $WORK/logs/plot_$JOBID.out"
echo "ERROR: $WORK/logs/plot_$JOBID.err"
echo "NEXT (after COMPLETED 0:0): bash $REPO/examples/FLUXNET_MultiSite_11/scripts/21_transfer_nine_site_plots_to_rfs.sh"

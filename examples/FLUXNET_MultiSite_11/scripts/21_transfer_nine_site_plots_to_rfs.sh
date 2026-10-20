#!/usr/bin/env bash
# Login-node-only transfer from Home to Research Filestore. No Scratch writes/deletes.
set -Eeuo pipefail
umask 077
POINTER="$HOME/.plot11_1000_latest"
[[ -f "$POINTER" ]] || { echo "Missing run pointer; provide Home run location in pointer" >&2; exit 1; }
WORK="$(realpath -e "$(cat "$POINTER")")"
case "$WORK" in "$HOME"/plot11_1000_HOME_*) ;; *) echo "Unsafe Home path: $WORK" >&2; exit 1;; esac
[[ ! -L "$WORK" && -d "$WORK/results" ]] || exit 1
SRC="$WORK/results"
RFS="/research/xclimatetbm/ly3n24"
ROOT="$RFS/CLM_FATES/FLUXNET_MultiSite_11"
DEST="$ROOT/spinup1000_final"
[[ -d "$RFS" && -w "$RFS" && "$(stat -f -c %T "$RFS")" == nfs ]] || {
 echo "RFS inaccessible: run on an IRIDIS login node" >&2; exit 1;
}
if [[ -f "$WORK/jobid.txt" ]]; then
  JOBID="$(cat "$WORK/jobid.txt")"
  [[ "$JOBID" =~ ^[0-9]+$ ]] || exit 1
  STATE="$(sacct -n -X -j "$JOBID" -o State | head -1 | xargs)"
  [[ "$STATE" == COMPLETED ]] || { echo "Job $JOBID: $STATE, transfer refused" >&2; exit 1; }
else
  JOBID="historical"
fi
PY="$HOME/.conda/envs/clm_fates_env/bin/python"
export SRC DEST PYTHONDONTWRITEBYTECODE=1
"$PY" -B - <<'PY'
import csv, os
from pathlib import Path
root=Path(os.environ["SRC"])
sites=("BE-Bra","FR-Fon","GL-ZaH","AT-Neu","FI-Sod","CH-Cha","CH-Fru","CH-Lae","CZ-Stn")
with (root/"nine_site_spinup1000_summary.csv").open(newline="") as f:
    rows=list(csv.DictReader(f))
assert len(rows)==9 and {r["Site"] for r in rows}==set(sites)
for r in rows:
    s=r["Site"]
    assert r["Status"]=="OK" and int(r["ArchiveYears"])==1000, r
    for suffix in ("01_carbon_pools_annual_mean.png","02_carbon_pools_last250years.png",
                   "GPP_NEE_monthly_overview.png","carbon_annual_means.csv",
                   "convergence_metrics.csv","monthly_FATES_vs_EC.csv",
                   "monthly_metrics.csv","metadata.json"):
        p=root/s/(s+"_"+suffix)
        assert p.is_file() and p.stat().st_size>0, p
assert len(list(root.rglob("*.png")))==27
assert len([p for p in root.rglob("*") if p.is_file()])==73
print("PASS: Home 9 sites, 27 figures, 73 files")
PY
mkdir -p "$DEST" "$ROOT/joblogs/home_plot_$JOBID"
rsync -avh --stats "$SRC/" "$DEST/"
if [[ -d "$WORK/logs" ]]; then
    rsync -avh "$WORK/logs/" "$ROOT/joblogs/home_plot_$JOBID/"
fi
DIFFERENCE="$(rsync -rnc --out-format='%n' "$SRC/" "$DEST/")"
[[ -z "$DIFFERENCE" ]] || { echo "Checksum mismatch: $DIFFERENCE" >&2; exit 1; }

# Adjust just the published summary directory to point to final RFS location.
"$PY" -B - <<'PY'
import os,csv,hashlib,json,datetime
from pathlib import Path
src=Path(os.environ["SRC"]); dest=Path(os.environ["DEST"])
p=dest/"nine_site_spinup1000_summary.csv"
with p.open(newline="") as f:
    reader=csv.DictReader(f); headers=reader.fieldnames; rows=list(reader)
for r in rows: r["Directory"]=str(dest/r["Site"])
with p.open("w",newline="\n") as f:
    writer=csv.DictWriter(f,fieldnames=headers,lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
receipt={"verified_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "home_source":str(src),"research_destination":str(dest),
         "source_file_count":len([p for p in src.rglob("*") if p.is_file()]),
         "all_source_files_checksum_verified_before_summary_path_rewrite":True,
         "summary_rewritten_to_rfs_path":True}
(dest/"home_to_rfs_verification_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
PY
echo "TRANSFER VERIFIED: $DEST"
echo "Home data retained for separate approved cleanup: $WORK"

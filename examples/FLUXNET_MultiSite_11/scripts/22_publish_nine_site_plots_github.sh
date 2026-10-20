#!/usr/bin/env bash
# Publish reviewed figures and metrics from RFS; optionally clean Home only after verification.
set -Eeuo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd -P)"
cd "$REPO"
[[ -z "$(git status --porcelain)" ]] || { echo "Use a clean checkout" >&2; exit 1; }
[[ "$(git branch --show-current)" == main ]] || { echo "Use main branch" >&2; exit 1; }
REL="examples/FLUXNET_MultiSite_11"
RFS="/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_11/spinup1000_final"
PUB="$REPO/$REL/figures/spinup1000_final"
PY="$HOME/.conda/envs/clm_fates_env/bin/python"
export REPO REL RFS PYTHONDONTWRITEBYTECODE=1
[[ -f "$RFS/nine_site_spinup1000_summary.csv" ]] || exit 1
git pull --ff-only origin main
mkdir -p "$PUB"
for SITE in BE-Bra FR-Fon GL-ZaH AT-Neu FI-Sod CH-Cha CH-Fru CH-Lae CZ-Stn; do
 mkdir -p "$PUB/$SITE"
 for SUFFIX in 01_carbon_pools_annual_mean.png 02_carbon_pools_last250years.png GPP_NEE_monthly_overview.png convergence_metrics.csv monthly_metrics.csv metadata.json; do
  test -s "$RFS/$SITE/$SITE"_"$SUFFIX"
  cp "$RFS/$SITE/$SITE"_"$SUFFIX" "$PUB/$SITE/"
 done
done
cp "$RFS/nine_site_spinup1000_summary.csv" "$PUB/"
"$PY" -B - <<'PY'
from pathlib import Path
import os,csv
r=Path(os.environ["RFS"]); repo=Path(os.environ["REPO"]); rel=os.environ["REL"]
with (r/"nine_site_spinup1000_summary.csv").open(newline="") as f: rows=list(csv.DictReader(f))
sites={"BE-Bra","FR-Fon","GL-ZaH","AT-Neu","FI-Sod","CH-Cha","CH-Fru","CH-Lae","CZ-Stn"}
assert len(rows)==9 and {v["Site"] for v in rows}==sites
assert all(v["Status"]=="OK" and int(v["ArchiveYears"])==1000 for v in rows)
assert len(list(r.rglob("*.png")))==27
pub=repo/rel/"figures/spinup1000_final"
for p in pub.rglob("*.csv"):
 b=p.read_bytes(); p.write_bytes(b.replace(b"\r\n",b"\n").replace(b"\r",b"\n"))
readme=repo/rel/"README.md"; old=readme.read_text()
start="<!-- NINE_SITE_1000_FINAL_START -->"; end="<!-- NINE_SITE_1000_FINAL_END -->"
lines=[start,"## Nine-site 1000-year spin-up: convergence and EC comparisons","",
 "Nine completed 1000-year spin-ups. IT-Noe and CH-Aws excluded.","",
 "Models are compared with tower EC GPP and NEE over the last complete forcing cycle.","",
 "**Caveat:** 1000 years does not prove ecological convergence; forcing and EC coverage require scientific review.","",
 "| Site | GPP monthly R² | NEE monthly R² |","|---|---:|---:|"]
for v in rows: lines.append("| "+v["Site"]+" | "+format(float(v["GPP_monthly_R2"]),".3f")+" | "+format(float(v["NEE_monthly_R2"]),".3f")+" |")
lines.extend(["","[Summary CSV](figures/spinup1000_final/nine_site_spinup1000_summary.csv)",""])
for v in rows:
 s=v["Site"]; b="figures/spinup1000_final/"+s+"/"+s
 lines.extend(["### "+s,"",
 "![1000-year carbon]("+b+"_01_carbon_pools_annual_mean.png)","",
 "![250-year carbon]("+b+"_02_carbon_pools_last250years.png)","",
 "![Monthly GPP NEE]("+b+"_GPP_NEE_monthly_overview.png)","",
 "[Convergence metrics]("+b+"_convergence_metrics.csv) · [EC metrics]("+b+"_monthly_metrics.csv) · [Metadata]("+b+"_metadata.json)",""])
lines.extend(["Raw tower data and NetCDF are not published.","",end])
block="\n".join(lines)
if start in old and end in old: new=old.split(start,1)[0].rstrip()+"\n\n"+block+old.split(end,1)[1]
elif start not in old and end not in old: new=old.rstrip()+"\n\n"+block+"\n"
else: raise ValueError("README markers incomplete")
readme.write_text(new.rstrip()+"\n")
PY
git add "$REL/README.md"
git add -f "$REL/figures/spinup1000_final/"
git diff --cached --check
if ! git diff --cached --quiet; then git commit -m "Publish nine-site 1000-year convergence and EC figures"; fi
git push origin HEAD:main
git fetch --quiet origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || exit 1
echo "GitHub publishing verified."
if [[ "$#" -eq 1 && "$1" == "--cleanup-home-after-push" ]]; then
 POINTER="$HOME/.plot11_1000_latest"
 [[ -f "$POINTER" ]] || { echo "Already cleaned: no run pointer"; exit 0; }
 WORK="$(realpath -e "$(cat "$POINTER")")"
 case "$WORK" in "$HOME"/plot11_1000_HOME_*) ;; *) echo "Unsafe cleanup path" >&2; exit 1;; esac
 [[ ! -L "$WORK" && -d "$WORK/results" ]] || exit 1
 [[ -f "$RFS/home_to_rfs_verification_receipt.json" ]] || { echo "Missing RFS receipt" >&2; exit 1; }
 [[ "$(find "$RFS" -type f -name "*.png" | wc -l)" -eq 27 ]] || exit 1
 [[ -z "$(rsync -rnc --exclude=nine_site_spinup1000_summary.csv --out-format="%n" "$WORK/results/" "$RFS/")" ]] || exit 1
 du -sh "$WORK"
 cd "$HOME"; rm -rf -- "$WORK"; rm -f -- "$POINTER"
 echo "Home run directory cleaned; Git checkout retained."
else
 echo "Home preserved. For explicit cleanup, rerun with --cleanup-home-after-push"
fi

#!/usr/bin/env bash
# AmeriFlux Batch 01 - Stage 03: CTSM point surfaces from exact-release BIF.
# Consistent with FLUXNET_MultiSite_13/scripts/stage02/02_make_13_surfaces.sh.
# Default: --check (read-only). --run creates outputs but NEVER overwrites.
set -euo pipefail

MODE="${1:---check}"
if [[ "$#" -gt 1 || ( "$MODE" != "--check" && "$MODE" != "--run" ) ]]; then
  echo "Usage: bash $0 [--check|--run]" >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/../../sites.tsv"
ROOT="${CLM_FATES_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES}"
CTSM="$ROOT/CTSM"
INPUTDATA="$ROOT/inputdata"
SITES_ROOT="$ROOT/sites/MY_EC_SITE"
TEMPLATE="$CTSM/tools/site_and_regional/default_data_2000.cfg"
SUBSET="$CTSM/tools/site_and_regional/subset_data"

echo "MODE=$MODE"
echo "CTSM=$CTSM"
echo "INPUTDATA=$INPUTDATA"
test -f "$MANIFEST" || { echo "ERROR: manifest missing: $MANIFEST" >&2; exit 1; }
test -f "$TEMPLATE" || { echo "ERROR: template missing: $TEMPLATE" >&2; exit 1; }
test -d "$INPUTDATA" || { echo "ERROR: inputdata missing: $INPUTDATA" >&2; exit 1; }
test -x "$SUBSET" || { echo "ERROR: subset_data not executable: $SUBSET" >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 missing" >&2; exit 1; }

# Re-audit all ten exact BIF releases BEFORE writing any new output.
RECORDS="$(python3 - "$MANIFEST" "$SITES_ROOT" <<'PY'
import csv
import math
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
root = Path(sys.argv[2])
with manifest.open(newline="", encoding="utf-8") as src:
    rows = list(csv.DictReader(src, delimiter="\t"))
if len(rows) != 10 or len({r["site"] for r in rows}) != 10:
    sys.exit("ERROR: expected 10 distinct manifest sites")
if any(set(r) != {"site", "package", "first_year", "last_year"} for r in rows):
    sys.exit("ERROR: unexpected manifest schema")
records = []
for row in rows:
    site, package = row["site"], row["package"]
    raw = root / site / "forcing" / "raw" / package
    if not raw.is_dir():
        sys.exit("ERROR: missing exact extracted release: " + str(raw))
    bifs = [p for p in raw.glob("*.csv") if "_BIF_" in p.name.upper()]
    if len(bifs) != 1:
        sys.exit("ERROR: %s: expected 1 BIF; found %d" % (site, len(bifs)))
    vals = {"LOCATION_LAT": set(), "LOCATION_LONG": set()}
    igbp = set()
    with bifs[0].open(encoding="latin-1", newline="") as src:
        reader = csv.DictReader(src)
        if not reader.fieldnames or not {"VARIABLE", "DATAVALUE"}.issubset(reader.fieldnames):
            sys.exit("ERROR: %s has unexpected BIF schema" % site)
        for item in reader:
            key = (item.get("VARIABLE") or "").strip().upper()
            value = (item.get("DATAVALUE") or "").strip()
            if key in vals and value:
                try:
                    x = float(value)
                    if math.isfinite(x):
                        vals[key].add(x)
                except ValueError:
                    pass
            if key in {"IGBP", "IGBP_CLASS", "IGBP_VEGTYPE"} and value:
                igbp.add(value)
    if any(len(v) != 1 for v in vals.values()):
        sys.exit("ERROR: %s ambiguous or missing BIF lat/lon: %s" % (site, vals))
    lat, lon = next(iter(vals["LOCATION_LAT"])), next(iter(vals["LOCATION_LONG"]))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        sys.exit("ERROR: %s coordinate outside valid range" % site)
    labels = ",".join(sorted(igbp)) or "NOT_REPORTED"
    print("BIF VERIFIED: %s lat=%s lon=%s IGBP=%s" % (
        site, lat, lon, labels), file=sys.stderr)
    records.append((site, lat, lon, labels))
for site, lat, lon, labels in records:
    print("%s\t%s\t%s\t%s" % (site, lat, lon, labels))
PY
)" || { echo "ERROR: BIF preflight failed; no surfaces created." >&2; exit 1; }

# Preflight output directories across the entire batch.
# Mark existing COMPLETE sites as SKIP; refuse incomplete or ambiguous ones.
declare -A STATUS
checked=0
skipped=0
while IFS=$'\t' read -r SITE LAT LON IGBP; do
  [[ -n "$SITE" ]] || continue
  SITE_ROOT="$SITES_ROOT/$SITE"
  OUT="$SITE_ROOT/subset_data"
  CFG="$SITE_ROOT/${SITE}_data.cfg"
  surface=""
  if [[ -d "$OUT" ]]; then
    surface="$(find "$OUT" -maxdepth 1 -type f -name 'surfdata*.nc' -print -quit)"
  fi
  if [[ -n "$surface" && -d "$OUT/user_mods" && -f "$CFG" ]]; then
    STATUS["$SITE"]=skip
    skipped=$((skipped + 1))
    echo "SKIP EXISTING: $SITE | $surface"
    continue
  fi
  if [[ -n "$surface" || -e "$OUT/user_mods" || -e "$CFG" ]]; then
    echo "ERROR: partial/conflicting output for $SITE; inspect $OUT and $CFG" >&2
    exit 1
  fi
  if [[ -d "$OUT" && -n "$(ls -A "$OUT")" ]]; then
    echo "ERROR: nonempty directory must be inspected: $OUT" >&2
    exit 1
  fi
  if [[ -e "$OUT" && ! -d "$OUT" ]]; then
    echo "ERROR: output path is not a directory: $OUT" >&2
    exit 1
  fi
  STATUS["$SITE"]=new
  checked=$((checked + 1))
  echo "READY: $SITE | lat=$LAT lon=$LON IGBP=$IGBP"
done <<< "$RECORDS"

echo "PREFLIGHT: $checked ready + $skipped already complete = $((checked + skipped))/10"
if [[ "$MODE" == "--check" ]]; then
  echo "CHECK COMPLETE. READ-ONLY: no surfaces, files, or Slurm jobs created."
  echo "Use --run explicitly after reviewing IGBP and surface assumptions."
  exit 0
fi

# Same reference subset configuration as the existing ICOS batches.
generated=0
while IFS=$'\t' read -r SITE LAT LON IGBP; do
  [[ -n "$SITE" ]] || continue
  [[ "${STATUS[$SITE]}" == "new" ]] || continue
  SITE_ROOT="$SITES_ROOT/$SITE"
  OUT="$SITE_ROOT/subset_data"
  CFG="$SITE_ROOT/${SITE}_data.cfg"
  echo "========== GENERATE $SITE (BIF IGBP $IGBP) =========="
  mkdir -p "$OUT"
  cp "$TEMPLATE" "$CFG"
  sed -i \
    -e 's|dir = lnd/clm2/surfdata_esmf/ctsm5.4.0|dir = lnd/clm2/surfdata_esmf/ctsm5.3.0|g' \
    -e 's|surfdat_16pft = .*|surfdat_16pft = surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc|' \
    -e 's|mesh_surf = .*|mesh_surf = fv0.9x1.25_141008_ESMFmesh.nc|' \
    "$CFG"
  (
    cd "$CTSM"
    "$SUBSET" point \
      --lat "$LAT" --lon "$LON" --lon-type 180 \
      --site "$SITE" --surf-year 2000 \
      --create-surface --create-user-mods \
      --inputdata-dir "$INPUTDATA" \
      --cfg-file "$CFG" --outdir "$OUT"
  )
  new_surf="$(find "$OUT" -maxdepth 1 -type f -name 'surfdata*.nc' -print -quit)"
  [[ -n "$new_surf" && -d "$OUT/user_mods" ]] || {
    echo "ERROR: $SITE expected surface and user_mods not found; inspect manually." >&2
    exit 1
  }
  generated=$((generated + 1))
  echo "CREATED: $SITE | $new_surf"
done <<< "$RECORDS"
echo "SUMMARY: created=$generated skipped_existing=$skipped total=$((generated + skipped))/10"
echo "WARNING: CTSM surfdata is a reference-grid sample, NOT a validated site IGBP/PFT map."
echo "No DATM files or Slurm jobs were submitted."

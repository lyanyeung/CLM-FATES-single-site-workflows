# Stage11 — unresolved winter humidity, audit-only proposal

Stage08 leaves exactly **4,884** unresolved records: US-EML 1,327, US-GLE 295, US-Ho1 917, US-ICh 169, US-ICt 2,176. All have missing raw RH in the attempted fallback, and companion ERA-derived RH below -2%. They are not automatically bad measured tower VPD values. Original VPD QC0 modifications are zero in this blocked subset.

`11_review_cold_humidity.py` is deliberately **not** an automatic forcing repair. It builds a reproducible, review-only VPD and QBOT proposal based on valid same-site, same-month, temperature-matched companion ERA5 RH values (default RH 5–100%, minimum 60 donor records, within +/-10 °C of the target tower temperature). This empirical analogue is not independent and can be inappropriate across years or microclimates. Candidate values are created only when donor support and physical screening pass. All 4,884 target records are logged, including unsuccessful cases, with provenance, donor count and RH quartiles.

It pins every original Stage08 input and output by SHA256, requires exact known site counts, validates timestamp uniqueness and source files, writes a new report folder, and refuses existing report folders. It never overwrites Stage07/08, sources, forcing, surfaces, DATM, CIME cases, or Slurm jobs. Every report carries `DO_NOT_USE_FOR_DATM_OR_SPINUP`.

## IRIDIS6 run

```bash
(
  set -euo pipefail
  PY=/home/ly3n24/.conda/envs/clm_fates_env/bin/python
  RAW=https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main
  REL=examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage11
  DIR="$HOME/ameriflux_batch02_stage11"
  mkdir -p "$DIR"
  curl -fLsS --retry 3 "$RAW/$REL/11_review_cold_humidity.py" -o "$DIR/11_review_cold_humidity.py"
  "$PY" -m py_compile "$DIR/11_review_cold_humidity.py"
  "$PY" -B "$DIR/11_review_cold_humidity.py" --check
  "$PY" -B "$DIR/11_review_cold_humidity.py" |
    tee "$HOME/AmeriFlux_Batch02_stage11_$(date +%Y%m%d_%H%M%S).log"
)
```

## Review criteria and next scientific gate

- Prioritize an **independent moisture variable**: verify availability of ERA5 2-m temperature and dewpoint (or specific humidity) on the corresponding site clock. Compute vapor pressure from consistent temperature/dewpoint conventions; compare to flux-tower temperature under cold conditions. Do not equate an ERA5 TA/VPD artifact with a direct measured RH.
- Investigate whether source VPD is physically invalid at the original tower temperature, particularly below freezing, and whether ice-vs-water saturation and unit transformations account for discrepancies. Recompute under both conventions for a sensitivity, not silent substitution.
- Review donor median and IQR, stationarity, spatial/seasonal mismatches, and exact source QC semantics. Provisional proposals cannot be used as approved climatological forcing.
- After an independent physical audit, implement a separately versioned *candidate forcing* overlay with original-to-new per-variable event ledger, and rerun the independent numeric and Post-v5 checks. Do not manually mark Stage08 COMPLETE, bypass Stage09, or launch spin-up now.

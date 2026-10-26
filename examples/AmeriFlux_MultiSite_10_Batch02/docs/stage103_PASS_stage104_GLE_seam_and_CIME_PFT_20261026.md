# Stage103 completed on IRIDIS6; Stage104 read-only seam distribution and CIME evidence

Actual Stage103 operator `EXIT_CODE=0`, 2026-10-26: all sixteen US-GLE UTC-midpoint source NetCDF files verified; the detached GF-Guy-derived GLE case successfully completed `case.setup` and `preview_namelists` and selected the GLE surface. **No model run, compilation, or Slurm submission** took place.

Stage103 actual 2020→2005 artificial join at model UTC 2005-01-01 07:15 had these 30-minute changes:
- Air temperature TBOT +4.332 K
- Surface pressure PSRF -665 Pa
- Wind WIND +2.823 m/s
- Specific humidity QBOT +0.000381233 kg/kg
- Downwelling longwave FLDS +4.146 W/m2
- Precipitation PRECTmms +5.55556e-7 mm/s
- Downwelling shortwave FSDS 0 W/m2
- Thermodynamic reference height ZBOT 0 m

The source is a cyclic **technical simulation candidate**: initial 14 half-hours in 2005 UTC represent 2020 local late-year records instead of missing 2004 observations. The discontinuity is at UTC 07:15 **inside** the first candidate year; the file-boundary 2020→2005 is a different transition and should not be conflated with this artificial join.

[Stage104](../scripts/stage104/104_GLE_seam_native_variability_readonly.py), commit `70324cbf56f746f6d809515826ccdcb49bbb5cf2`, Git blob `f7c5eea7ccf4e32b68f0b3de5d789df979015776`, reads the original SHA-verified Stage102 16-year 280,320-interval forcing and the successful detached Stage103 case. It reports eight-variable absolute source 30-minute change P95/P99/P99.9, the synthetic jump's tail-frequency within real forcing (excluding the artificial join itself), and separately the true periodic datafile cycle boundary. It reads the detached `CaseDocs/datm_in`, `lnd_in`, and `user_nl_datm_streams` without writing to the case. It also preserves gridded natural vegetation **92.48556%** versus crop **7.51444%** evidence, not FATES tower vegetation fractions.

Official [AmeriFlux US-GLE site](https://ameriflux.lbl.gov/sites/siteinfo/US-GLE) classifies the tower as **ENF** and reports a severe spruce-beetle disturbance peaking around 2008 with substantial forest basal area mortality. Gridded 7.51% crop is **not** proof of tower crop management. Investigate actual EC footprint, observed PFT fractions, disturbance effects, and surface representation before science release.

Run on IRIDIS6:

```bash
(
  set +e
  REV="70324cbf56f746f6d809515826ccdcb49bbb5cf2"
  BLOB="f7c5eea7ccf4e32b68f0b3de5d789df979015776"
  SCRIPT="$HOME/Batch02_stage104_GLE_seam_readonly.py"
  LOG="$HOME/Batch02_stage104_GLE_seam.log"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$REV/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage104/104_GLE_seam_native_variability_readonly.py" -o "$SCRIPT" || exit 1
  test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
  python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf-8").read());print("SYNTAX PASS")' "$SCRIPT" || exit 1
  python3 -B "$SCRIPT" --self-test || exit 1
  python3 -B "$SCRIPT" --audit 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE104_EXIT_CODE=$RC"
  grep -E '^STAGE104 (SEAM|CIME|GLE|REPORT|PASS|SCIENCE HOLD)' "$LOG"
)
```

Keep **all** source, source surface/PFT, active CIME, reference case and Slurm job state unchanged. Next step after Stage104 is to evaluate the *scientific legitimacy of the unobserved 2004 14-record surrogate and the PFT representation*, then if justified an explicitly authorized **single-step actual model data read**, never a long spin-up automatically.

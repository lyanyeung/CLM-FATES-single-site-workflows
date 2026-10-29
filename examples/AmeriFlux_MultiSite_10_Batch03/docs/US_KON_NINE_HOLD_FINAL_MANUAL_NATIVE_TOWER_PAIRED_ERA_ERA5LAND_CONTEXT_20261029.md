# US-Kon — nine remaining protected humidity native hours, original tower/ERA/ERA5-Land context (2026-10-29)

**User request:** quickly review ALL nine source-HOLD native half-hours by hand, including abnormal rows and preceding/following conditions, **real source tower measurement QA (QC0), original FLUXNET companion ERA, and separately downloaded ERA5-Land**. No mass repair, no unverified values.

## Current facts, actual Stage14M/14N outputs

Stage14K selected research (280320 NOLEAP original 2004–2019 HH) left exactly nine original source humidity pairs (`VPD_USE/QBOT`) missing after 68 routine low-confidence ERA RH transfers. Original site T/PSRF is finite. Stage14M verified original source hashes and genuine both-QC0 tower RH context; Stage14N tested 3 near-QC0 interpolation candidates, **0/3 passed immediate two-sided native 30-minute VPD/RH/QBOT continuity**, hence none was inserted. No DATM/Post-v5/AD400/Slurm authorization. Original native times and source original TA_F (QC1 does NOT mean measured):

| Native YYYYMMDDHHMM | Original TA_F °C | Original TA_F_QC/VPD_F_QC | Prior/next *paired* original TA_F/VPD_F QC0 measured RH time gaps h | Known source risk |
|---|---:|---|---|---|
| 201102220830 | +7.860 | 1/1 | 0.5 / 1.5 | Original QC1 T outlier; previous Stage12AG QC0-based T suggestion −3.167 |
| 201102220900 | −1.754 | 0/1 | 1.0 / 1.0 | Original true T QC0, companion ERA temperature −7.159°C |
| 201102220930 | +8.623 | 1/1 | 1.5 / 0.5 | Original QC1 T outlier; Stage12AG QC0-based T suggestion −0.562 |
| 201105261100 | +16.777 | 0/1 | 699 / 16.5 | Actual T−companion ERA only −0.026°C, genuine RH anchors very remote |
| 201109291830 | +15.617 | 1/2 | 286.5 / 474.5 | Original source T QC1 vs companion ERA 21.991°C (−6.374°C), VPD QC2; no nearby true humidity QC0 |
| 201110150730 | +8.344 | 0/1 | 659.5 / 101.5 | Tower T QC0; original humidity VPD_F QC1, true RH anchors remote |
| 201110230730 | +9.801 | 0/1 | 2 / 1 | Original both-QC0 RH interpolation 67.0345%, BUT native neighbors differ by 44–50 pp and VPD 4.43/7.61hPa; not approved |
| 201202251030 | +0.626 | 0/1 | 0.5 / 1.5 | RH interpolation 52.8069%; left passes, right jump 5.296hPa/27.12pp; not approved |
| 201208050900 | +25.986 | 0/1 | 0.5 / 2.5 | RH interpolation 38.3399% versus companion ERA RH 60.7748%; right jump 15.121hPa; not approved |

**Scientific provenance:** QC0=published source measured field, QC1=source gapfilled, QC2=source ERA-dependent. Original `TA_F` and `VPD_F` can have different QCs: for example QC0 temperature **does not** mean original QC0 measured humidity at the missing center. When both TA and VPD are QC0, `100 × [1−VPD/esw(T)]` is derived RH from two observed tower fields, not the independently original RH sensor observation. Original FLUXNET paired `TA_ERA/VPD_ERA` and CDS ERA5-Land point `t2m/d2m/sp` are **distinct** source products and must have separate printed columns. BIF local standard source time UTC−6 requires using source native interval-start +15min +6h for UTC ERA5-Land source midpoint; this is a published BIF setting, **not** a production CIME/DATM clock approval.

## Exact SHA-pinned FINAL one-pass original/ERA5-Land source audit

[Stage14O direct 9-center and seven grouped ±2h original tower + companion ERA + SHA-verified ERA5-Land T2m/D2m/water RH/pressure source values](../scripts/stage14/14o_US_Kon_FINAL_nine_original_tower_ERA5Land_pm2h_READONLY.py). Git commit `30c4f7d3acdfe3df642ec83af756c67ebc547874`, Git blob `dabc868924ec46a5a2905ad3505a100fd1974e52`.

- Reads only signed immutable original AmeriFlux FLUXMET source and paired ERA SHA in Stage07 manifest, plus Stage14K research tape (nine intentional NaNs). No source modifications.
- Opens existing site/year 2011/2012 verified original ERA5-Land NetCDF or ZIP receipts (either Stage09f or Stage12f) where **actually present**; verifies SHA256, point coordinates, UTC hourly time coordinate, exact units and physical moisture. Does **not** invent/download missing ERA5-Land years. If a local source-year file is unavailable, prints `NO_SHA_VERIFIED_ERA5LAND_LOCAL_SOURCE_FOR_YEAR_` rather than substitute `TA_ERA` or construct a false number.
- Prints all **nine exact-center rows** and all original-native records ±2h in **seven grouped episodes**, showing actual TA_F/TA_F_QC, VPD_F/VPD_F_QC, paired TA_ERA/VPD_ERA + derived RH, separately gridded ERA5-Land T2m/D2m/RH/SP + grid-RH-at-tower T VPD, and retained Stage14K site temperature/VPD/QBOT. Prints explicitly which original humidity is QC0 measured. No Slurm, original, DATM, or report writes: terminal output/log only.
- **Script has been committed and GitHub source delimiters checked, but NOT YET RUN on IRIDIS6.** The full original pre/during/post numeric tables must come from this actual run; this document intentionally does not invent unavailable gridded values.

```bash
(
  set -euo pipefail
  F="$HOME/US_Kon_nine_tower_ERA5Land_pm2h.py"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/30c4f7d3acdfe3df642ec83af756c67ebc547874/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14o_US_Kon_FINAL_nine_original_tower_ERA5Land_pm2h_READONLY.py" -o "$F"
  test "$(git hash-object "$F")" = "dabc868924ec46a5a2905ad3505a100fd1974e52"
  python3 -B -c 'import pathlib,sys; f=pathlib.Path(sys.argv[1]); compile(f.read_text(),str(f),"exec"); print("SYNTAX PASS")' "$F"
  python3 -B "$F" --run 2>&1 | tee "$HOME/US_Kon_nine_tower_ERA5Land_pm2h.log"
)
```

After exact output, per event the human decides **retain original unknown source HOLD**, **test isolated source-only low-confidence sensitivity** (separate model input, not observed forcing), or **approve a source-QC-based edit** only when genuinely justified by the source context. Do not treat temporal interpolation artefacts as independent observations.

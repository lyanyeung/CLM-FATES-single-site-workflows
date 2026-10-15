# ES-LJu 2023 anomalous temperature: reproducible paired TA/VPD trial

## Decision and evidence

The original `EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1` contains 458 half-hour 2023 `TA_F` records below −25 °C (359 officially `TA_F_QC=0` and 99 `QC=1`). A long spell near −40 °C is incompatible with co-located FLUXNET downscaled ERA temperature. The previous 13-site QC v5 sometimes reconstructed VPD to make RH numerically positive while retaining −40 °C; do **not** treat that as a valid forcing.

`examples/ICOS_ES-LJu/scripts/03_prepare_forcing.py` in the user's GitHub repository documents an earlier successful ES-LJu-specific approach: for `TA_F<-20 °C`, `TA_F>40 °C`, or (in 2023) `abs(TA_F-TA_ERA)>=15 °C`, replace **both TA and VPD** with the matching ERA pair; then check vapor pressure, negative VPD and RH<1% and replace TA/VPD together for remaining failures. The previous successful input was 2004–2024, 367,920 half-hours, ZBOT 2.5 m, NO_LEAP. Note the original 2023 `>40 °C` episode mentioned in the README: targeting only negative 40 °C would miss it.

`examples/FLUXNET_MultiSite_11/docs/QC_v5_extension_and_site_decisions.md` advises against uncritical ERA replacement because `_F` and `_ERA` may share the same source (e.g. CH-Aws). It also stresses preserving original QC flags, recording every substituted record, using nonoverwriting candidate versions, validating physical/timestamp fields, and explicitly marking ERA-dependent estimates as scientific REVIEW, not as measured ground truth.

## New proposed method

`09_ES-LJu_legacy_pair_QC_isolated_trial.py`:

1. **Pins the existing official ES-LJu FLUXMET_HH and companion ERA5_HH**, examines all 2004–2024 half-hours, removes leap days and checks exact NO_LEAP time coverage. No generic temperature threshold is applied to other sites.
2. Uses the **old successful site-specific rule**, with a strict ERA pair sanity gate. Rejects the trial if the selected ERA TA/VPD itself gives nonsensical humidity.
3. **Replaces TA and VPD as a pair**, in memory only. Recomputes RH and vapor pressure. If RH<1%, vapor pressure<=0 or VPD<0, uses the ERA TA/VPD pair at those additional timestamps, subject to the same ERA sanity gate.
4. Computes TBOT, PSRF (`PA_F ×1000`), QBOT, FSDS, FLDS, WIND, PRECTmms (`P_F /1800`), ZBOT 2.5 m; validates broad limits and all 367,920 30-minute records.
5. Separately records original `TA_F_QC`, `VPD_F_QC`, individual reasons, original vs new values, all-timestep provenance, per-year counts, raw SHA256, and comparisons with the preexisting 13-site QC v5 candidate (when present).
6. **Never writes to raw, previous v5/v6, site-level DATM or spin-up folders**. `--check` does not write; `--run` requires an exclusive **new directory under CLM_FATES/experiments**. Even a partially populated old output is not overwritten.

## Commands

Upload the script to `~/09_ES-LJu_legacy_pair_QC_isolated_trial.py` on IRIDIS6. Then:

```bash
conda activate clm_fates_env

python ~/09_ES-LJu_legacy_pair_QC_isolated_trial.py --check \
  2>&1 | tee ~/ES-LJu_legacy_pair_v7_check.log

OUT=/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_ES-LJu_legacy_pair_trial_v1_20261014
test ! -e "$OUT" || { echo "Choose a new version tag: output exists"; exit 1; }

set -o pipefail
python ~/09_ES-LJu_legacy_pair_QC_isolated_trial.py --run --out "$OUT" \
  2>&1 | tee ~/ES-LJu_legacy_pair_v7_trial.log

cat "$OUT/summary.json"
cat "$OUT/ES-LJu_replacement_by_year.csv"
```

**Never delete** an existing trial directory only to make the script run again. Use a new tag such as `..._v2_20261014` after inspecting an old run.

## Generated files

- `ES-LJu_CLM_forcing_2004_2024_legacy_pair_trial.csv`: numerical trial, **NOT approved for DATM**.
- `ES-LJu_pair_replacement_ledger.csv`: original QA flags, trigger reason, original/candidate TA/VPD and candidate RH.
- `ES-LJu_all_timesteps_TA_VPD_sources.csv`: provenance for all half-hours; trial ERA replacements are explicitly distinguished from original observations.
- `ES-LJu_replacement_by_year.csv`: annual replacement and original QC=0 counts.
- `ES-LJu_diff_from_previous_v5.csv`: comparison with prior candidate, if available.
- `source_manifest.json`: source checksums and method references.
- `summary.json`, `DO_NOT_USE_FOR_DATM_OR_SPINUP.txt`.

## Gates remaining before accepting as new DATM

- Compare the new 2023 temperature and VPD time-series with ERA, original nearby uncorrupted observations, and the previous successful ES-LJu forcing; inspect the 2023 high-temperature anomalies too.
- Examine all original QC=0 edits, particularly whether the long 2023 segments and non-2023 humidity repairs are justified.
- Since companion FLUXNET ERA5 is **not independent ground truth**, evaluate independent local weather station or alternate reanalysis where feasible; do not infer scientific truth from passing physical checks.
- Verify the site surface/PFT, BIF measurement height (`ZBOT=2.5 m`) and DATM calendar/netCDF separately; use the revised forcing only after explicit scientific approval. Keep any existing ES-LJu cases and model archives untouched.

## GitHub references

- https://github.com/lyanyeung/CLM-FATES-single-site-workflows/blob/main/examples/ICOS_ES-LJu/README.md
- https://github.com/lyanyeung/CLM-FATES-single-site-workflows/blob/main/examples/ICOS_ES-LJu/scripts/03_prepare_forcing.py
- https://github.com/lyanyeung/CLM-FATES-single-site-workflows/blob/main/examples/FLUXNET_MultiSite_11/README.md
- https://github.com/lyanyeung/CLM-FATES-single-site-workflows/blob/main/examples/FLUXNET_MultiSite_11/docs/QC_v5_extension_and_site_decisions.md

Original licensed flux and reanalysis input files should **not** be committed to GitHub.
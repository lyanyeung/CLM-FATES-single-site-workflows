# Stage12j VERIFIED on IRIDIS6 — no US-MtB altitude-aware humidity method accepted

**2026-10-25 06:53 UTC:** Stage12j source SHA, Python AST, --self-test, --check and --run passed. The original Stage12i 1.06-km site-grid pressure-height proxy and original source measured QC0 humidity from **2020, 2022, 2024** were scientifically tested against four preregistered humidity transfer hypotheses. No method passed **all three** source measured QC0 cold-month analogue validation gates. **NO NEW VPD/QBOT REPAIR.** Previously SHA-sealed Stage12g three new grid-RH research values and 1035 original T/ice held times are unchanged; no source native timestamp, measured tower T/P or VPD_F_QC0 was modified. The safe isolated Stage12j science-only output is:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12j_US-MtB_QC0_elevation_aware_humidity_trial_20261025T065237Z_699cdb7f/`

## Exact original measured QC0 cold-analogue science results

| Method | 2020 MAE / >2hPa | 2022 MAE / >2hPa | 2024 MAE / >2hPa | 3-year pass |
|---|---|---|---|---|
| **GRID_RH** | **1.105 hPa / 15.31%** | **0.994 hPa / 10.31%** | **1.139 hPa / 14.80%** | **NO** |
| LAPSE_TD | 1.147 hPa / 16.47% | 1.037 hPa / 11.24% | 1.186 hPa / 17.01% | NO |
| GRID_Q | 1.182 hPa / 18.17% | 1.099 hPa / 13.83% | 1.271 hPa / 22.02% | NO |
| GRID_E | 1.439 hPa / 24.89% | 1.464 hPa / 25.39% | 1.795 hPa / 39.16% | NO |

GRID_RH is the least-bad hypothesis among the four in this specific validation: measured-QC0 predicted VPD MAE <1.5hPa for every year, near-zero signed bias (0.051,0.023,0.058 hPa), and valid fraction 79.3%,74.5%,82.0% respectively. But it fails the **predeclared maximum 10% fraction |error|>2hPa** in ALL THREE original years. The observational N is 3,459 (2020), 4,195 (2022) and 2,431 (2024), with candidate valid N 2,744 / 3,124 / 1,993.

The source cannot legitimately be described as **scientifically accepted humidity** for blocked source times. Do **NOT** quietly change the 10% criterion to 15%-16%, lower the absolute error cutoff, substitute `TA_ERA`/grid T for original `TA_F`, or expand the previously held 1035 target set without independent data evidence.

## Stage12k — identify large-error regimes without another automatic forcing repair

The [Stage12k GRID_RH measured QC0 large-error and target-support diagnostic](../scripts/stage12/12k_us_mtb_gridRH_QC0_error_regimes_READONLY.py) is committed to GitHub **but NOT executed on IRIDIS6 yet**. It SHA-verifies Stage12j and reopens the same three original source years; re-calculates and insists on numerical agreement with original Stage12j year-wise `GRID_RH` QC0 cold analogue counts/MAE/bias/fraction >2hPa **before** authoring a diagnostic.

It groups the **valid measured original QC0 cold** prediction errors by source-native month, original air T (-15/-10/-5/0/5C bins), source measured VPD bins and year, and lists runs of consecutive >2hPa QC0 errors. It also reports whether the earlier **1,035 held** source times fall in year-month-temperature bins with at least 20 matched QC0 cold source analogues. The withheld 1,035 have **no measured VPD target truth** and must NOT be treated as independent observed successful validation points. The native clock/UTC shift is unapproved; monthly bin counts do not validate time provenance.

Strict `--check` is read-only with NO reports, source or model writes. `--run` creates **only** new isolated SHA-receipted diagnostic tables. Stage12j's acceptance gate remains FAILED and no new repair is authorised by Stage12k, irrespective of how attractive a subgroup looks. All original Batch03 Post-v5/DATM/spinup approvals remain **ZERO**. If error tails align with distinct source failure regimes, a scientifically separate source-quality investigation is needed before any proposed revised protocol.

**Workstream prioritisation:** Because US-MtB remains unresolved even after full source elevation validation, avoid downloading the other 39 Stage12f source-years for US-MtB indiscriminately. The remaining five Batch03 blocked sites and existing US-MtB source science holds can be tracked separately; restoring valid historical forcing must not depend on relaxing instrument-source physical constraints.

## Stage12k v2 fix — warm source targets must not be dropped

First Stage12k v1 execution on IRIDIS6 passed Python syntax and self-test and processed original source years 2020, 2022 and 2024; it then stopped at `Stage12k target source-year month/temperature count differs` in the **source analogue-coverage table**, before any `--run` writes.

**Root cause in our Stage12k analysis program:** original `tbins` covered only source air temperature `[-100,5]` °C, appropriate for **cold measured QC0 analogue observation** validation, but was also applied to all **1,035 Stage12g held target times** without restricting those targets to the cold analogue domain. Targets at >5 °C or invalid temperatures were converted to missing `temperature_bin` and silently DROPPED from default Pandas `groupby` (which excludes NA keys). This wrongly made the 1,035 source identity count appear inconsistent. It does **not** imply source-file or checksum corruption, and does NOT justify discarding warm-target rows.

The [Stage12k corrected program](../scripts/stage12/12k_us_mtb_gridRH_QC0_error_regimes_READONLY.py) now uses exhaustive temperature bins `<=-15, -15:-10, -10:-5, -5:0, 0:5, >5, MISSING_OR_INVALID_T`, converting any nonfinite source temperature to an explicit last category. The measured-QC0 validation itself remains exclusively `source_T<=5°C` with the original >2hPa error threshold. It adds regression tests for warm, invalid and infinite source T values plus a full identity count, and prints the numbers of held targets **outside measured cold analogue validation**. Local synthetic regression of the binning logic passed; **the updated full script has not yet been executed on IRIDIS6**.

No Stage12j source measurement, original 1,035 held source events, existing correct humidity, forcing, DATM/CIME/Slurm or Post-v5 permission changed. The failed IRIDIS6 `--check` performed **no writes**.

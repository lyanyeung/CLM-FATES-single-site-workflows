# Methods: two-stage carbon and CO₂ flux stability screening

**Scientific purpose:** distinguish incomplete spin-up from climate-cycle-aligned demographic variability in single-site CTSM/CLM–FATES simulations, with the end use of eddy-covariance GPP and NEE comparisons. **Status:** exploratory diagnostics calibrated only on the 15 worked examples; **not** an official CTSM/FATES stopping criterion.

## Stage 0 — data-quality and chronology gate

For each case, verify `RUN_STARTDATE`, repeated DATM `year_first`/`year_last`, `taxmode=cycle`, noleap calendar, `FATES_VEGC` units, and a continuous annual source history (using the frozen analysis archive). Let `L = year_last - year_first + 1`; for `n` archived annual model years, use only `N = floor(n/L)*L` complete years and record `n-N` as an excluded partial tail. Note the meteorological forcing repeats at fixed phase; do not mix phases when comparing model cycles.

## Stage 1 — phase-aligned vegetation C

1. For each complete forcing cycle `j`, compute the mean of annual `FATES_VEGC` (kg C m⁻²), `Cbar_j=(1/L)*sum_i C_{j,i}`. Use all complete cycles without phase mixing.
2. For each target window `W = 100,200,300`, select `k = ceil(W/L)` latest completed cycles, fit OLS slope `b_W` of `Cbar_j` versus corresponding *model-year midpoint*, with `b_W` in kg C m⁻² per model year.
3. Report `S_W=1000*b_W` g C m⁻² per model year and `R_W = 10000*b_W/abs(mean(Cbar_j))` **percent per 100 model years** (when VegC mean is nonzero).
4. Partition latest `3*ceil(100/L)` cycles into 3 nonoverlapping blocks of equal cycle count; fit each 100+-year segment separately to detect reversals.
5. Last four adjacent cycle pairs: compare corresponding forcing-year phases `C[j,i]`. Compute (a) signed change `100*mean(C[j,i]-C[j-1,i])/mean(abs(C[j-1,i]))` percent; (b) mean absolute change `100*mean(abs(C[j,i]-C[j-1,i]))/mean(abs(C[j-1,i]))` percent. The latter quantifies variability; it is **not a net carbon-drift rate**. Signed relative change can be divided by cycle length and multiplied by 100 to express drift per 100 model years. Retain original signed and absolute indicators separately.
6. **Stage 1 study-defined low-drift screen:** all `abs(R_100),abs(R_200),abs(R_300) < 2` (% per 100 years) AND all last four phase-matched mean absolute differences <2%. Run a 1% sensitivity analysis; this screening is not a theorem about equilibrium. Four failing-but-marginal sites were sent to deeper review; three high-variability sites were prioritized for continued spin-up.

## Stage 2 — NEE before GPP (four borderline sites)

1. From verified annual `h0a` NetCDF files, use the final >=300 years of full forcing cycles only, ending at the same frozen end-year used for Stage 1.
2. Convert `FATES_NEP` and `FATES_GPP` from kg C m⁻² s⁻¹ into yearly integrated g C m⁻² yr⁻¹ using daily `time_bounds` duration and factor 1000 g/kg. Define model `NEE=-FATES_NEP` in the existing station code. **Negative NEE means net uptake**. Model field definitions should be checked if separate fire/harvest losses are being evaluated.
3. For each complete meteorological cycle, compute the average of its yearly integrated NEE and GPP. For each `W=100,200,300`, fit regression versus the physical midpoint model-year. Report NEE slope `b_{NEE,W}*100` as **g C m⁻² yr⁻¹ per 100 model years**. Unlike GPP, **never normalize NEE by near-zero mean NEE**.
4. **Operational user-selected NEE criterion:** `max_W abs(NEE_trend_W) < 10` g C m⁻² yr⁻¹ per 100 model years. A threshold on slope is not the same as a threshold on adjacent-cycle MAE or a bound on total carbon stock drift. Apply all 3 windows, not only last 100 years.
5. After NEE, assess GPP: normalize each trend by the mean GPP to percent per 100 years (formula above); require `max_W abs(GPP_trend_W) < 2%` per 100 years and all four most recent phase-matched absolute GPP differences <2% of reference cycle GPP.
6. Report the latest four phase-matched NEE differences separately as `g C m⁻² yr⁻¹` (both signed and absolute), and assess systematic direction, block contrasts, and model variability qualitatively. Do not claim that a NEE trend <10 is universally negligible or smaller than tower random uncertainty without an independently justified uncertainty analysis.
7. **Decision policy fixed for this example:** FR-Fon passes all three NEE trend windows and GPP screen → **RETAIN**; DE-Tha, NL-Loo, BE-Bra fail the latest ~100-year NEE trend at the 10-unit threshold → **CONTINUE SPIN-UP**. The 8 VegC low-drift sites remain **FLUX NOT TESTED**, not certified retained. IL-Yat, CZ-Stn, GL-ZaH continue based on high VegC variability as previously decided, not due to demonstrated NEE/GPP failure.

## Applied decisions are separate from HPC actions

These are **scientific/operator decisions**, not actual Slurm submissions, job success, archived 1300-year/3000-year outputs or validated post-continuation convergence. Before any extension, inspect current Slurm queue and complete coordinated ATM/LND/CPL restart; refuse duplicate submissions, Git locks, unarchived work, inconsistent `RESUBMIT`, or inadequate Scratch quota. DE-Tha, NL-Loo and IL-Yat were already assigned 3000-year targets historically; do not re-initiate those chain segments from 1000. For BE-Bra, choose the new target only after verifying current CIME case and a complete 1000-year coordinated archive. Keep any future re-spin-up with corrected PFT composition in a *different* case.

## Data limitations

The four-site flux extraction already ran on IRIDIS6 and produced the summary reproduced here. The complete phase-aligned time series, per-cycle NEE/GPP, last four signed changes, and second-round four-site VegC figures reside on Home/RFS and are staged by `07_publish_rfs_results.sh` before GitHub completeness is asserted.

## Reusable methods description (draft; verify against exported input data before paper submission)

“Single-site spin-up stability was first assessed using annual simulated vegetation carbon grouped into complete repetitions of site-specific meteorological forcing. We fitted trends to cycle-mean vegetation carbon over the most recent at least 100, 200 and 300 years and assessed nonoverlapping century-scale blocks and consecutive phase-matched cycle differences. For cases flagged as marginal, we separately assessed annual integrated modeled net ecosystem exchange (NEE) and gross primary productivity (GPP) over the same complete forcing cycles. We applied study-defined operational screening thresholds of <2% change per 100 model years in Vegetation C/GPP (with a <2% forcing-cycle variability screen) and an absolute NEE trend <10 g C m⁻² yr⁻¹ per 100 model years over all three time windows. These are project-specific decision thresholds, not established universal equilibrium criteria. Candidate acceptance also required review of serial changes and scientific site representation.”

> The paragraph above describes the algorithm and decision settings, but **should not yet be quoted as a final peer-reviewed method validation**; examine uncertainty, non-stationarity and sensitivity of conclusions to the chosen thresholds before publication.

# Phase-aligned VegC review pipeline — design and safeguards

**Status: design approved for review; Stages 03–05 not implemented or executed.** This document makes no claim that GPP, NEE or LAI stability has yet been demonstrated. The existing scripts **01** and **02** remain unchanged.

## Purpose and review cohort

Investigate the seven cases requiring closer inspection following the 15-site full-forcing-cycle diagnostic (21–22 October 2026):

- **Ambiguous / marginal (4)**: DE-Tha, NL-Loo, BE-Bra, FR-Fon.
- **Large variation (3)**: IL-Yat, CZ-Stn, GL-ZaH.
- **Lower-drift reference cases (8)**: DE-Hai, RU-Fyo, DK-Sor, AT-Neu, CH-Cha, CH-Fru, CH-Lae, FI-Sod. These are controls for flux testing, **not** certified equilibrated sites.

Keep **VegC stability**, **GPP/NEE stability**, **carbon-pool equilibrium**, and **tower/PFT realism** as separate questions. Do not block this diagnostic on PFT validation; constrained-PFT reruns belong to distinct CIME cases.

## Existing evidence

- [01: annual-data multiscale analysis](01_analyze_15site_vegc.py)
- [02: full-forcing-cycle phase-aligned analysis](02_phase_aligned_15site_vegc.py)
- Research Filestore existing output:
  `/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Analysis/vegc_convergence_15site/phase_aligned/20261021T235330Z_15site_FullCycle_VegC/`
- Full-cycle summary: `all15_fullcycle_vegc_summary.csv`.
- Seven site-specific `<SITE>_last4_aligned_cycle_pairs.csv` and `<SITE>_phase_aligned_metrics.csv` include signed %/century and corresponding-year absolute differences.
- Annual carbon CSVs on RFS: Batch 6 archived-snapshot folder and Batch 11 `spinup1000_final`. Source paths and SHA-256 checksums are recorded in previous run provenance.

## Review stages and proposed outputs

### Stage 00 — Immutable inventory and consistency check (no rerun)

1. Verify the seven site IDs, source metadata, case IDs, forcing start/end, forcing-cycle length and source checksums.
2. Determine `L` (forcing-cycle length) and last full-cycle year `floor(n/L)*L`. Never mix forcing phases. Record the ignored incomplete trailing years.
3. Check whether the archived annual `h0a` files for the **last five complete forcing cycles** exist; distinguish missing history from scientific nonconvergence.
4. Verify NetCDF field availability and units before any flux extraction: `FATES_GPP`, `FATES_NEP`, `FATES_LAI`, optional `FATES_HET_RESP`, `FATES_NPP`, `FATES_MORTALITY_CFLUX_CANOPY`, `FATES_MORTALITY_CFLUX_USTORY`, `FATES_DISTURBANCE_RATE_TREEFALL`. Optional fields must be checked, not assumed.

Output: `source_inventory.csv`, `netcdf_field_inventory.csv`, `provenance.json`.

### Stage 01 — VegC time-series deep dive (RFS derived CSV only)

For the seven sites, use `FATES_VEGC` annual means to produce:

- The final 300+ model years, with boundaries of all complete forcing cycles and the latest ~100/200/300-year cycle-mean regressions.
- All individual *full-cycle means* in the final 300+ years, not only a fitted line.
- Three independent equal-cycle-count ~100-year blocks (as currently implemented).
- Four last *adjacent* forcing-cycle signed changes and phase-aligned mean absolute differences. Report both **kg C m⁻²** and relative %. **Annualize signed change** to % per 100 years or g C m⁻² yr⁻¹; **do not annualize absolute difference and call it carbon drift**.
- Sign persistence (how many of the four signed changes share a sign), cycle-to-cycle reversals, the location of the maximum excursion, and rolling 4–6-cycle mean/OLS. Identify possible disturbance and recovery episodes visually; optional breakpoint analysis must not present 4-point fits as high-confidence evidence.
- Plot available `FATES_STOREC`, `FATES_STRUCTC`, `FATES_NONSTRUCTC` alongside VegC, preserving their definitions. **Do not assume they sum to all vegetation carbon.**

Output: `seven_site_vegc_review.csv`; two or three per-site PNGs; an event-candidate table with year/cycle, magnitude, duration and sign.

### Stage 02 — Mechanistic check for event candidates (conditional)

For any large VegC excursion, inspect the available (and *verified*) model output around that cycle:

- Plant mortality / structural turnover, growth and recruitment proxies, and `FATES_LAI`.
- `FATES_GPP`, `FATES_NPP`, `FATES_NEP`, and heterotrophic respiration when present.
- `FATES_VEGC`, `FATES_STOREC` and structural carbon before/during/after the event.

Separate **persistent drift** (several cycles moving in one direction) from **fluctuation/recovery** (sign changes, transient excursions, recovery towards a similar cycle mean). A one-time breakpoint is a review flag, not an objective determination of disturbance cause.

Output: per-event plots and `event_review.csv`; mark `UNVERIFIED_MECHANISM` if history fields are unavailable.

### Stage 03 — Independent flux stationarity test (requires archived h0a)

For each site, extract annual and (where available) monthly `FATES_GPP`, `FATES_NEP` and `FATES_LAI` from **at least the last five complete forcing cycles**, using read-only annual h0a files. Verify physical units and the NEE sign convention (`FATES_NEE=-FATES_NEP` in earlier comparison scripts), including limitations if fire/harvest or other losses matter. Integrate flux rates with correct model calendar and timestep rather than averaging a rate and treating it as annual carbon.

- Compare the same forcing-year phase in consecutive model cycles: annual integrated GPP, annual integrated NEE, seasonal/monthly profiles, and cycle-average LAI.
- For GPP, summarize signed bias between cycles, mean absolute difference, and relative difference at site level.
- For NEE, emphasize **absolute difference in g C m⁻² yr⁻¹**, since NEE may have a near-zero mean; compare with EC uncertainties only where those uncertainty products were actually retrieved and their coverage confirmed.
- Do **not** infer multi-cycle convergence from existing single-last-cycle EC validation graphics. NT/DT partitioning preferences are a separate future action (GitHub issue #3); flux-spinup stability here is assessed using model outputs first.
- Keep a flux-stationarity assessment separate from agreement with real EC measurements.

Output: `seven_site_gpp_nee_lai_cycle_metrics.csv`, phase-aligned monthly annual-cycle plots, `history_coverage.csv`.

### Stage 04 — Evidence-based decision (no automatic spin-up launch)

Assign *two independent* labels:

- **VEGC_LOW_DRIFT**, **VEGC_CYCLIC_VARIABILITY**, **VEGC_PERSISTENT_DRIFT**, **VEGC_EVENT_OR_RECOVERY**, **VEGC_INSUFFICIENT_DATA**.
- **FLUX_STABLE_CANDIDATE**, **FLUX_DRIFTING**, **FLUX_INSUFFICIENT_DATA**.

The legacy 1%/2% screens are **study-defined sensitivity tests**, NOT official CTSM/FATES equilibrium thresholds or automatic job submission triggers. A site can have stable fluxes with fluctuating VegC; conversely low VegC drift does not establish stable NEE.

Suggested decisions:
1. VegC low drift, flux stable → candidate for an EC-flux application, conditional on scientific site realism and uncertainty review.
2. VegC fluctuating / event-recovery, flux stable → retain as conditional flux candidate; document demographic variation.
3. Persistent VegC drift **and** meaningful GPP/NEE drift → diagnose cause and assess additional complete forcing cycles, not arbitrary extra 1000 model years.
4. History missing → `INSUFFICIENT_DATA`; do not substitute an inference.
5. High variation with model structural anomalies → diagnose first; extending the same model is not automatically a solution.

Output: `review_decisions.csv` with a human-readable evidence statement and recommended next experiment.

## Execution safety on IRIDIS6

- **All stages read-only** with respect to cases, forcing, NetCDF history and restart files. Never change `RESUBMIT`, never submit a CIME continuation or delete source output during review.
- The **RFS mount is usable from login nodes but was not available to tested compute nodes**. For lightweight annual-CSV stages, read/write RFS on login nodes. For expensive NetCDF extraction, run on a Slurm compute node reading accessible Scratch archive, write limited derived output to a new Home staging directory, then `rsync` and checksum-verify to RFS on a login node.
- Use versioned result directories; do not overwrite `20261021T235330Z_15site_FullCycle_VegC`, earlier nine-site figures or DT benchmark plots.
- Validate all requested model years and fields before analysis; report explicit `MISSING_HISTORY` or `MISSING_VARIABLE` per site. Preserve exact source case IDs and hashes.
- Never publish raw tower data, raw NetCDF, restarts, user credentials, or model log dumps to GitHub. Only derived summaries/plots after scientific review.

## CTSM methodology reference

CTSM BGC spin-up diagnostics inspect ecosystem carbon, vegetation carbon, soil carbon, GPP and LAI separately. Equilibration of fast vegetation/flux indicators and slow soil pools can occur at different times. The above choices of ~100/200/300 years, four adjacent cycle pairs and 1%/2% screens are **not official CTSM stopping rules**.

CTSM user's guide: https://escomp.github.io/CTSM/users_guide/running-special-cases/Spinning-up-the-biogeochemistry-Bgc-spinup.html

CTSM FATES history variable definitions:
https://escomp.github.io/CTSM/users_guide/setting-up-and-running-a-case/history_fields_fates.html

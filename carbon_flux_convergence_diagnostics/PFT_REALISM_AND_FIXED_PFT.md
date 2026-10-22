# Stage 0 — PFT realism gate before carbon/flux spin-up decisions

**Date: 22 October 2026. Evidence status: all 15 dominant FATES PFT outcomes verified by repository metadata and the reported IRIDIS6 read-only audit.**

## Why this is a prerequisite

Numerical stabilization of FATES vegetation carbon and NEE/GPP does **not** establish that simulated vegetation resembles the eddy-covariance (EC) tower footprint. Before allocating further HPC spin-up, check **(i)** actual FATES predicted PFT identity and dominant vegetation-C fraction; **(ii)** tower vegetation/land-cover and species mix; **(iii)** whether the model surface contains unrealistic host landunit fractions. The original carbon/NEE thresholds remain useful *within a vegetation-scientifically suitable model configuration*, but do not override a PFT mismatch.

**Do not equate** a CLM surface `PCT_NAT_PFT` index or `PCT_CROP` with prognostic FATES PFT area, and do not mistake `FATES_VEGC_PF` carbon percentage for canopy area fraction. Site IGBP only provides a broad vegetation class; it does not validate species mixture, management or actual tower footprint.

## Six modeled-PFT observations (from already committed per-site metadata)

| Site | EC IGBP | Dominant simulated FATES PFT | Its share of FATES vegetation C | Match | Decision |
|---|---|---|---:|---|---|
| DE-Hai | DBF | broadleaf_colddecid_extratrop_tree | 99.31% | Broad-type yes | Keep dynamic competition case |
| RU-Fyo | ENF | broadleaf_colddecid_extratrop_tree | 96.06% | **No** | Keep completed dynamic case as sensitivity; add fixed-PFT no-competition comparison |
| DE-Tha | ENF | broadleaf_colddecid_extratrop_tree | 99.58% | **No** | **Pause further dynamic-case extension** pending PFT-gated review; prioritize fixed-PFT comparison |
| DK-Sor | DBF | broadleaf_colddecid_extratrop_tree | 99.59% | Broad-type yes | Keep dynamic competition case |
| NL-Loo | ENF | broadleaf_colddecid_extratrop_tree | 99.47% | **No** | **Pause further dynamic-case extension** pending PFT-gated review; prioritize fixed-PFT comparison |
| IL-Yat | ENF | c4_grass | 100.00% | **Severe mismatch** | **Pause further dynamic-case extension**; prioritize vegetation-representation correction |

The six cases used `use_fates=.true.`, `use_fates_nocomp=.false.`, and `use_fates_fixed_biogeog=.false.` in their archived metadata. Their PFTs thus reflect the **dynamic full-FATES outcome**. These are **dominant percentages of VegC, not land area**.

An ENF/DBF match only certifies broad physiology; notably DE-Hai and DK-Sor could still differ from EC footprint stand age, species mixture, planting/management and fractions.

## Nine additional modeled-PFT outcomes — verified by the 22 October 2026 IRIDIS6 audit

The user's read-only auditor `08_audit_actual_fates_pft_15sites.py` completed without failures and reported the actual final archived `FATES_VEGC_PF` dominant type for these nine cases. Source run: `/home/ly3n24/CLM_FATES_PFT_15site_audit/20261022T021326Z_site_PFT_evidence`. Figures and percentages below come from the reported audit output. The underlying complete CSVs and provenance remain on IRIDIS6 Home until uploaded.

| Site | Tower class | Simulated dominant PFT | Dominant share of FATES VegC | Interpretation |
|---|---|---|---:|---|
| AT-Neu | GRA | broadleaf_colddecid_extratrop_tree | 99.08% | **Mismatch: modeled forest over grassland** |
| BE-Bra | MF | broadleaf_colddecid_extratrop_tree | 99.44% | Mixed forest composition needs tree-type inventory; single dominant broadleaf PFT likely misses mixture |
| CH-Cha | GRA | broadleaf_colddecid_extratrop_tree | 99.41% | **Mismatch: modeled forest over grassland** |
| CH-Fru | GRA | broadleaf_colddecid_extratrop_tree | 99.61% | **Mismatch: modeled forest over grassland** |
| CH-Lae | MF | broadleaf_colddecid_extratrop_tree | 99.21% | Mixed forest composition needs tree-type inventory |
| CZ-Stn | DBF | cool_c3_grass | 100.00% | **Severe mismatch: modeled grass over forest** |
| FI-Sod | ENF | broadleaf_colddecid_extratrop_tree | 91.72% | **Mismatch: modeled deciduous broadleaf over evergreen needleleaf forest** |
| FR-Fon | DBF | broadleaf_colddecid_extratrop_tree | 99.60% | Broad PFT type agrees; retain the *flux-screen* result, pending footprint/surface realism |
| GL-ZaH | GRA code / high-Arctic tundra | arctic_c3_grass | 69.83% | Arctic graminoid type plausible; cannot infer that shrubs, moss or tundra heterogeneity are represented correctly |

**Evidence interpretation:** 15/15 dominant-PFT outcomes are now measured from model output. Broad-type matching does **not** prove fractional canopy cover, species composition, flux-footprint representativeness, or crop landunit validity. In particular, BE-Bra and CH-Lae are MIXED forest cases requiring site-specific proportions. GL-ZaH is a tundra case, not generic temperate grassland.

### Revised experiment priorities

- **Hold additional dynamic-competition extensions and prioritize separate constrained-PFT experiments:** DE-Tha, NL-Loo, IL-Yat, CZ-Stn. Do not cancel active Slurm jobs without an operational status and archive audit.
- **Add constrained-PFT controls despite low VegC drift in the dynamic run:** RU-Fyo, AT-Neu, CH-Cha, CH-Fru, FI-Sod. Preserve original simulations as counterfactual references.
- **Conditionally retain existing dynamic runs subject to broader site realism:** DE-Hai, DK-Sor and FR-Fon. FR-Fon additionally passed project-defined NEE and GPP criteria.
- **Review site-specific mixtures before selecting fixed PFTs:** BE-Bra, CH-Lae; BE-Bra's prior NEE-based extension decision is put on hold pending this check.
- **Review high-Arctic vegetation structure before deciding continuation versus constrained experiment:** GL-ZaH; its high VegC variability still requires scientific investigation.

### CLM-host surface discrepancy needing separate audit

The earlier 11-site surface assessment reported high `PCT_CROP` in point surfaces relative to the tower vegetation class: approximately **BE-Bra 37.4%, FR-Fon 50.8%, CZ-Stn 47.8%**. These values are **host surface fractions**, not proof of active FATES crop vegetation (the landunit may be converted/disabled in the effective case). Verify the actual `CaseDocs/lnd_in` `fsurdat`, `create_crop_landunit`, `use_crop`, and FATES flags before interpreting them. See [11-site README](../examples/FLUXNET_MultiSite_11/README.md) (repository-root link: `examples/FLUXNET_MultiSite_11/README.md`).

## Integrated decision policy (supersedes the *unconditional* six-site continue flags)

1. **Stage 0: PFT / site realism.** Compare FATES predicted vegetation type, especially last-cycle `FATES_VEGC_PF`, with EC BIF and field species/landcover inventory. If clearly wrong, hold **additional dynamic competition spin-up**, and prioritize a *separate new* vegetation-constrained experiment. Do not stop/cancel a running Slurm chain blindly: inspect live jobs and coordinated restarts before any action.
2. **Stage 1: Vegetation carbon stability.** In each scientifically eligible case, use the existing full-meteorological-cycle 100/200/300-year VegC slope and recent four-cycle differences (exploratory 2% rule).
3. **Stage 2: NEE then GPP stability.** For marginal VegC cases, use NEE three-window slopes <10 g C m⁻² yr⁻¹ per 100 model years and GPP all-window trends / adjacent-period differences <2%. Existing choice: FR-Fon conditionally retained, DE-Tha/NL-Loo/BE-Bra were marked continue **before PFT review**.
4. **Parallel experiment:** for any apparently converged dynamic-case that has a credible PFT mismatch, preserve original run as a *reference*, and create a new fixed-PFT / no-inter-PFT-competition case as a separate counterfactual. RU-Fyo is a confirmed example. For a mixed forest, a single enforced PFT may be inappropriate; enforce a justified local mixture if supported, otherwise use separate trait/PFT sensitivity cases.
5. **Fixed-PFT settings require validation:** `use_fates_fixed_biogeog` and `use_fates_nocomp` are distinct FATES options and are NOT interchangeable. A no-competition setting alone does **not** prove fixed prescribed PFT shares or a correct EC footprint. Inspect CTSM version, actual FATES configuration, site-specific surface/trait files and `CaseDocs/lnd_in`; test a short separate pilot and independently verify FATES PFT fractions before launching long spin-up. Do not simply toggle these two switches in an active continuing case.
6. Re-evaluate VegC, NEE and GPP after the fixed-PFT experiment spin-up. Keep dynamic vs fixed PFT results labeled separately for publication.

## Evidence inventory

- Six-site PFT history and plots are included under `cases/<site>/data/FATES_PFT_VEGC_annual_pct.csv` and `cases/<site>/figures/FATES_PFT_VEGC_evolution.png` in this folder.
- Each six-site snapshot `cases/<site>/data/source_metadata.json` independently records `IGBP_from_original_BIF`, `fates_flags`, `PFT.dominant_PFT_name` and `PFT.dominant_VEGC_pct`.
- [15-site summary](data/15_site_pft_realism_screen.csv) records all 15 verified modeled outcomes, distinguishing broad-type matches, mismatches and field-composition review cases.
- [Read-only IRIDIS6 audit](scripts/08_audit_actual_fates_pft_15sites.py) checks a frozen year of the existing 15 CIME cases, effective surface / FATES parameter file and FATES_VEGC_PF for real PFT types. It writes to HOME; no CIME case, Slurm job, NetCDF or RFS is modified.
- Existing single-site and five-site PFT audit scripts: `examples/FLUXNET_MultiSite_6/scripts/25_audit_DE_Hai_PFT_vs_EC.py` and `26_audit_five_site_PFT_year1000_vs_EC.py`.

**Status:** All 15 final PFT dominant-type observations have now been reported by the IRIDIS6 audit. Actual field-specific stand mixtures, FATES fractional area, active crop-landunit handling and fixed-PFT pilot configurations remain unverified. No fixed-PFT case has been created or submitted as part of this documentation change.

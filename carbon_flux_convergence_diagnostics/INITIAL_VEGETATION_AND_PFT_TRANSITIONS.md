# Initial land-cover extraction vs year-one FATES vegetation

**Status 22 October 2026: all 15 sites have frozen final simulated PFT observations; year-one FATES shares are now recovered for all 15 sites (six from archived annual CSV, nine from 22 October 2026 h0a audit). Effective original CLM surface host PFT distributions, PCT_NATVEG and PCT_CROP have now been transcribed from the read-only IRIDIS6 audit into GitHub and decoded with the CTSM CLM5 standard PFT index table.**

There are **three different** "initial vegetation" concepts and they must not be conflated:

1. **Initial source / effective CLM surface:** site-specific point `fsurdat`, its `PCT_NATVEG`, `PCT_CROP`, `PCT_NAT_PFT` indexed fraction vector, and original product/provenance. The vector is CLM *host* natural vegetation, **not** the living full-FATES PFT composition. Its class labels require a version-verified CLM index scheme; the extracted index number alone cannot be called ENF/DBF. The original coarse gridded surface is also not necessarily the tower's actual footprint.
2. **FATES model-year 1 simulated state:** PFT-resolved `FATES_VEGC_PF` annual-average share after the first model year, **not an exact timestamp-zero seeded state**. These are percentages of carbon, not vegetation cover or stem numbers.
3. **FATES frozen end-state:** model output after 1000 to 1920 simulated years, separately verified; changes between (2) and (3) reflect simulated establishment/competition/turnover, **not necessarily a land-cover change in the forcing file**.

### Original CLM surface PFT distribution — 15 site source audit

The table below derives from `CaseDocs/lnd_in` → **effective `fsurdat`** and the user's read-only terminal output. `PCT_NAT_PFT` is the **percentage within the natural-vegetation landunit** (including bare ground index 0), whereas `PCT_NATVEG` and `PCT_CROP` describe percentages of the **whole site/grid cell**. These columns have distinct denominators.

The standard **CLM5 `natpft` (0–14)** mapping is cross-checked with the [CTSM CLM5 technical note](https://escomp.github.io/CTSM/release-clm5.0/tech_note/Ecosystem/CLM50_Tech_Note_Ecosystem.html) and [CESM staff indexing explanation](https://bb.cgd.ucar.edu/cesm/threads/how-to-obtain-the-indices-of-natural-pfts-of-each-grid-of-surface-data.6153/). This is **not** the PFT-slot numbering inside `fates_params_default.json`. Preserve the version/path of the actual `fsurdat` when changing the surface or code; custom surface definitions must be independently checked.

| Site | Tower class | Original CLM surface dominant natural PFT | Natural-unit share | PCT_NATVEG | PCT_CROP | FATES year 1, dominant VegC PFT | FATES frozen final VegC PFT |
|---|---|---|---:|---:|---:|---|---|
| DE-Hai | DBF | **C3_GRASS** (index 13) | 53.15% | 61.88% | 38.12% | Evergreen broadleaf tree 26.97% | Deciduous broadleaf tree 99.31% |
| RU-Fyo | ENF | **NET_TEMP** (index 1) | 45.39% | 96.69% | 3.31% | Evergreen broadleaf tree 32.92% | Deciduous broadleaf tree 96.06% |
| DE-Tha | ENF | **C3_GRASS** (index 13) | 55.79% | 62.67% | 37.33% | Evergreen broadleaf tree 29.96% | Deciduous broadleaf tree 99.58% |
| DK-Sor | DBF | **C3_GRASS** (index 13) | 73.45% | 55.40% | 44.60% | Evergreen broadleaf tree 28.90% | Deciduous broadleaf tree 99.59% |
| NL-Loo | ENF | **C3_GRASS** (index 13) | 71.63% | 66.84% | 33.16% | Evergreen broadleaf tree 27.98% | Deciduous broadleaf tree 99.47% |
| IL-Yat | ENF | **BARE** (index 0) | 52.23% | 81.60% | 18.40% | C4 grass 26.85% | C4 grass 100.00% |
| AT-Neu | GRA | **C3_ARCTIC** (index 12) | 43.53% | 95.81% | 4.19% | Evergreen broadleaf tree 30.91% | Deciduous broadleaf tree 99.08% |
| BE-Bra | MF | **C3_GRASS** (index 13) | 73.75% | 62.59% | 37.41% | Evergreen broadleaf tree 27.16% | Deciduous broadleaf tree 99.44% |
| CH-Cha | GRA | **C3_GRASS** (index 13) | 53.09% | 77.77% | 22.23% | Deciduous broadleaf tree 21.23% | Deciduous broadleaf tree 99.41% |
| CH-Fru | GRA | **C3_ARCTIC** (index 12) | 44.70% | 96.06% | 3.94% | Evergreen broadleaf tree 27.15% | Deciduous broadleaf tree 99.61% |
| CH-Lae | MF | **C3_GRASS** (index 13) | 53.09% | 77.77% | 22.23% | Evergreen broadleaf tree 27.80% | Deciduous broadleaf tree 99.21% |
| CZ-Stn | DBF | **C3_GRASS** (index 13) | 58.99% | 52.18% | 47.82% | Evergreen broadleaf tree 28.08% | Cool C3 grass 100.00% |
| FI-Sod | ENF | **NET_BOREAL** (index 2) | 54.78% | 99.82% | 0.18% | Evergreen broadleaf tree 33.23% | Deciduous broadleaf tree 91.72% |
| FR-Fon | DBF | **C3_GRASS** (index 13) | 71.84% | 49.20% | 50.80% | Deciduous broadleaf tree 20.06% | Deciduous broadleaf tree 99.60% |
| GL-ZaH | GRA / Arctic tundra | **BARE** (index 0) | 74.41% | 100.00% | 0.00% | Evergreen broadleaf tree 29.42% | Arctic C3 grass 69.83% |

**PFT key:** NET_TEMP = needleleaf evergreen temperate tree; NET_BOREAL = needleleaf evergreen boreal tree; C3_GRASS = non-Arctic C3 grass; C3_ARCTIC = Arctic C3 grass; BARE = bare soil. FATES first-year/final percentages are shares of **living vegetation carbon**; they are not CLM natural-landunit percentages or canopy-area shares.

**Main scientific findings:** The extracted CLM natural vegetation is dominated by **C3 non-Arctic grass** at DE-Hai, DE-Tha, DK-Sor, NL-Loo, BE-Bra, CH-Cha, CH-Lae, CZ-Stn and FR-Fon (9 sites). RU-Fyo and FI-Sod have natural-landunit PFTs led by **temperate and boreal evergreen needleleaf trees**, respectively, but dynamic FATES later strongly favored deciduous broadleaf trees. IL-Yat's extracted natural component is **52.23% bare ground**, with only **0.96% temperate evergreen needleleaf tree** even though the EC tower is ENF; dynamic FATES became entirely C4 grass. AT-Neu and CH-Fru are led by Arctic C3 grasses in the coarse CLM surface; this may be unsuitable for some managed alpine grasslands and must be checked against local vegetation. GL-ZaH's source is mainly bare ground plus Arctic C3 grass, broadly plausible for Arctic tundra, but canopy, bryophyte and shrub representation is unresolved. The reported `PCT_CROP` is unusually high at several forest sites; whether a separate crop landunit is active under full FATES depends on case flags and must not be inferred from surface data alone.

The source printout included **only PFT indices with share ≥0.1%**. The complete original vector may contain smaller entries that were not printed. [Full reported CLM PFT distribution](data/15_site_clm_surface_pft_distribution.csv); [mapped CLM index lookup](data/clm5_natpft_index_lookup.csv); [combined analysis CSV](data/15_site_initial_surface_vs_fates_summary.csv).

## First-year empirical evidence from existing archived six-site annual CSVs

| Site | Observed EC IGBP | Model year 1 dominant PFT | First-year vegetation C share | Frozen final dominant PFT |
|---|---|---|---:|---|
| DE-Hai | DBF | broadleaf_evergreen_extratrop_tree | 26.97% | broadleaf_colddecid_extratrop_tree (99.31%) |
| RU-Fyo | ENF | broadleaf_evergreen_extratrop_tree | 32.92% | broadleaf_colddecid_extratrop_tree (96.06%) |
| DE-Tha | ENF | broadleaf_evergreen_extratrop_tree | 29.96% | broadleaf_colddecid_extratrop_tree (99.58%) |
| DK-Sor | DBF | broadleaf_evergreen_extratrop_tree | 28.90% | broadleaf_colddecid_extratrop_tree (99.59%) |
| NL-Loo | ENF | broadleaf_evergreen_extratrop_tree | 27.98% | broadleaf_colddecid_extratrop_tree (99.47%) |
| IL-Yat | ENF | c4_grass | 26.85% | c4_grass (100.00%) |

**Transition observation:** in DE-Hai, RU-Fyo, DE-Tha, DK-Sor, NL-Loo, the second model year already has `broadleaf_colddecid_extratrop_tree` as the PFT with the largest share of vegetation C. By about model year 20, the deciduous broadleaf share generally exceeds 97%. IL-Yat increases from 26.85% C4 grass in year one to 85.14% in year two and 100% by approximately year 100. These are rapid shifts in *relative vegetation carbon*, and should be inspected together with **absolute PFT carbon** before inferring competitive exclusion or mortality. All values come from the previously published six-site `FATES_PFT_VEGC_annual_pct.csv`; the first model year is not a pre-run composition snapshot.

**The five forest sites' similar year-one PFT mixture and rapid convergence to deciduous broadleaf dominance suggest a shared model configuration/competitive advantage worth investigating.** This is a hypothesis, not proof that the original surface data were incorrectly extracted; testing original effective surfdata and the FATES initial cohort-seeding recipe is still necessary.

## Other nine sites: first-year, end-state and original surface now available

| Site | EC broad class | Frozen final PFT | First-year modeled PFT | Effective initial CLM surface |
|---|---|---|---|---|
| AT-Neu | GRA | broadleaf_colddecid_extratrop_tree (99.08%) | broadleaf_evergreen_extratrop_tree (30.91%) | See original CLM surface table above |
| BE-Bra | MF | broadleaf_colddecid_extratrop_tree (99.44%) | broadleaf_evergreen_extratrop_tree (27.16%) | Pending `fsurdat` read |
| CH-Cha | GRA | broadleaf_colddecid_extratrop_tree (99.41%) | broadleaf_colddecid_extratrop_tree (21.23%) | Pending `fsurdat` read |
| CH-Fru | GRA | broadleaf_colddecid_extratrop_tree (99.61%) | broadleaf_evergreen_extratrop_tree (27.15%) | Pending `fsurdat` read |
| CH-Lae | MF | broadleaf_colddecid_extratrop_tree (99.21%) | broadleaf_evergreen_extratrop_tree (27.80%) | Pending `fsurdat` read |
| CZ-Stn | DBF | cool_c3_grass (100.00%) | broadleaf_evergreen_extratrop_tree (28.08%) | Pending `fsurdat` read |
| FI-Sod | ENF | broadleaf_colddecid_extratrop_tree (91.72%) | broadleaf_evergreen_extratrop_tree (33.23%) | Pending `fsurdat` read |
| FR-Fon | DBF | broadleaf_colddecid_extratrop_tree (99.60%) | broadleaf_colddecid_extratrop_tree (20.06%) | Pending `fsurdat` read |
| GL-ZaH | GRA | arctic_c3_grass (69.83%) | broadleaf_evergreen_extratrop_tree (29.42%) | Pending `fsurdat` read |

## Reproducible next action

Run [`scripts/09_audit_initial_surface_vs_fates.py`](scripts/09_audit_initial_surface_vs_fates.py) on IRIDIS6 login. It reads the **effective** `CaseDocs/lnd_in` `fsurdat`, host landunit fractions and CLM `PCT_NAT_PFT` indices, and frozen FATES model years **1, 2, 5, 20, 100 and final** directly from annual `h0a`. Report first-year `MISSING_YEAR_H0A` explicitly rather than inventing a first-year PFT. The script never edits CIME, forcing, restarts, Slurm or GitHub.

```bash
cd ~/CLM-FATES-single-site-workflows
git fetch origin main
DIR="$HOME/vegc_15site_analysis"; mkdir -p "$DIR"
git show origin/main:carbon_flux_convergence_diagnostics/scripts/09_audit_initial_surface_vs_fates.py > "$DIR/09_audit_initial_surface_vs_fates.py"
PY=/home/ly3n24/.conda/envs/clm_fates_env/bin/python
"$PY" -m py_compile "$DIR/09_audit_initial_surface_vs_fates.py"
"$PY" "$DIR/09_audit_initial_surface_vs_fates.py" --preflight
"$PY" "$DIR/09_audit_initial_surface_vs_fates.py" --run 2>&1 | tee "$HOME/initial_vegetation_15sites.log"
```

### Decision implications

If the **original effective surface** conflicts with the tower type, fix the site surface/landunit inputs in an **independent new case** before re-running scientific conclusions; do not assume no-PFT-competition alone fixes the wrong input. If the surface is plausible but FATES first-year seeded mixture or subsequent dynamic PFT outcome conflicts with the tower, investigate FATES initialization and traits/competition, and test a **separate** vegetation-constrained case with a validated no-inter-PFT-competition setting. Keep the earlier dynamic experiments as a historical reference where useful. Never alter active CIME cases or cancel jobs merely because a PFT label differs.

Original 15-site PFT end-state evidence: [PFT_REALISM_AND_FIXED_PFT.md](PFT_REALISM_AND_FIXED_PFT.md). Initial-vs-final tabular record: [data/15_site_initial_surface_vs_fates_summary.csv](data/15_site_initial_surface_vs_fates_summary.csv).

> **Scientific warning:** even a `PCT_NAT_PFT` host-surface vector with a correct broad PFT classification does not impose corresponding FATES PFT area fractions under full-FATES dynamic mode. A successful first-year FATES type similarly does not prove tree-species or footprint matching.

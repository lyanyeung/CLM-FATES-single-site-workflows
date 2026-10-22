# Initial land-cover extraction vs year-one FATES vegetation

**Status 22 October 2026: all 15 sites have frozen final simulated PFT observations; year-one FATES shares are now recovered for all 15 sites (six from archived annual CSV, nine from 22 October 2026 h0a audit). Effective original CLM surface host PFT vectors have been extracted into a Home CSV but have not yet been synced to GitHub.**

There are **three different** "initial vegetation" concepts and they must not be conflated:

1. **Initial source / effective CLM surface:** site-specific point `fsurdat`, its `PCT_NATVEG`, `PCT_CROP`, `PCT_NAT_PFT` indexed fraction vector, and original product/provenance. The vector is CLM *host* natural vegetation, **not** the living full-FATES PFT composition. Its class labels require a version-verified CLM index scheme; the extracted index number alone cannot be called ENF/DBF. The original coarse gridded surface is also not necessarily the tower's actual footprint.
2. **FATES model-year 1 simulated state:** PFT-resolved `FATES_VEGC_PF` annual-average share after the first model year, **not an exact timestamp-zero seeded state**. These are percentages of carbon, not vegetation cover or stem numbers.
3. **FATES frozen end-state:** model output after 1000 to 1920 simulated years, separately verified; changes between (2) and (3) reflect simulated establishment/competition/turnover, **not necessarily a land-cover change in the forcing file**.

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

## Other nine sites: year-one and end-state verified; effective surface CSV awaiting upload

| Site | EC broad class | Frozen final PFT | First-year modeled PFT | Effective initial CLM surface |
|---|---|---|---|---|
| AT-Neu | GRA | broadleaf_colddecid_extratrop_tree (99.08%) | broadleaf_evergreen_extratrop_tree (30.91%) | Source CSV on IRIDIS6 Home; GitHub sync pending |
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

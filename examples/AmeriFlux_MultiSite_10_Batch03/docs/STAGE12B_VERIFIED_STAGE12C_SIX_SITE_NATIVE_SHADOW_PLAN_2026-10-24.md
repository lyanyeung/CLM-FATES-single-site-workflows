# Batch03 Stage12b VERIFIED, Stage12c full-timeline isolated research shadows

IRIDIS6 2026-10-24 Stage12b **syntax, --self-test, --check, --run ALL PASS**. It wrote:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12b_six_site_bulk_gridRH_numeric_patches_20261024T115336Z_baa77893/`

Exactly **1,687/1,687** evidence-insufficient and low-physical-conflict cases passed strict numeric gridded ERA5-Land RH transfer, and **zero additional numeric conflicts** arose. Exactly **233** ice-phase / water-physics / site-grid temperature conflicts and **four** US-Me2 native clock holds were preserved; no original forcing writes or model authorizations.

| Site | 12b eligible humidity-only numeric patches | unresolved original physics/clock events |
|---|---:|---:|
| US-NR3 | 1312 | 172 |
| US-Kon | 227 | 2 |
| US-NR1 | 116 | 57 |
| US-MMS | 17 | 1 |
| US-MtB | 14 | 1 |
| US-Me6 | 1 | 0 |
| US-Me2 | 0 | 4 |
| Total | **1687** | **237** |

## Stage12c — full native time scaffolds, NOT complete usable meteorology

[Stage12c source-native six-site builder](../scripts/stage12/12c_six_site_full_native_shadow_with_held_gaps.py) is committed but **has not run on IRIDIS6**. Because only US-MOz, US-Mpj and US-NC2 previously had full SHA-sealed Stage07 numerical candidate forcing, there is no valid six-site Stage07 forcing file to patch in place.

Stage12c therefore rebuilds each six-site source-native **NO_LEAP chronological scaffold** from SHA-pinned original FLUXMET and separately released exact-time companion ERA file, retaining all valid original `TA_F` values. Missing/out-of-range **other input** meteorological fields may be filled only from matching-time paired site ERA with a per-site count, and every remaining missing value explicitly flagged. Only the 1,687 SHA-sealed numeric-event RH patch cases transfer existing Stage10b **ERA5-Land grid RH** onto the **unchanged exact original site temperature and pressure** and reconstruct VPD/QBOT. It verifies complete original 30 or 60 minute source timeline, target/source native timestamp uniqueness, exact source site T/pressure, humidity equations, and immediately adjacent VPD jumps.

**Critical:** The remaining 233 science conflict humidity records will be written as explicit **NaN VPD_USE and QBOT**, not secretly filled with a guessed value. Further unphysical/absent original humidity and missing other meteorology are likewise flagged. Thus the output includes six full **time-indexed** CSVs but DOES NOT constitute full physically valid, model-ready site forcing. Output is a new isolated `science_trials/stage12c_*` directory with independent SHA receipt and an INCOMPLETE marker. US-Me2 is completely excluded pending verification of release clock metadata.

No site time convention or UTC offset is approved or changed; Stage10b gridded ERA5-Land temporal alignment remains a provisional scientific assumption. Independently measured tower RH is not established. **Post-v5/DATM/spinup remain zero.** The next genuinely required development is bulk isolation of 233 source conflicts and any newly surfaced full-year source gaps, not more review of the 1,687 successful event-level numeric patch calculations.

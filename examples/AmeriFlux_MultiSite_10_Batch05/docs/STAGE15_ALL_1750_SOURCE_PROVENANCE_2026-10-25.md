# AmeriFlux Batch05 — Stage15 complete original low-RH source provenance review

**Actual IRIDIS6 operator run, 2026-10-25 22:42 UTC:** pinned GitHub source verified, Python syntax and self-test passed. All ten Stage10 original meteorology rows cross-matched with the Stage14 experimental interpolation and water-saturation-formula outputs. Stage15 produced *new review CSV+JSON only*, without original source, existing reports, forcing, model, or Slurm changes:

```text
STAGE15 SUMMARY sites=10/10 reviewed=1750 negative=1559 measured=119 good_MDS=965 ERA=666 approved=0 reports=/iridisfs/home/ly3n24/ameriflux_batch05_stage15/triage_20261025T224213Z_1292191
ONLY NEW REVIEW CSV/JSON; NO ORIGINAL, STAGE10/14, FORCING, MODEL OR SLURM WRITES
```

Shell alias `/home/ly3n24/ameriflux_batch05_stage15/triage_20261025T224213Z_1292191` resolves to `/iridisfs/home/ly3n24/...` on the operator system. Outputs: `stage15_all_1750_science_holds.csv` and `stage15_summary.json`. Underlying source/large reports remain private on IRIDIS6 rather than committed to GitHub.

## Exhaustive, mutually exclusive VPD provenance

| VPD_F source | Low-derived-RH source records |
|---|---:|
| Original measured QC0 | 119 |
| Good MDS QC1 | 965 |
| ERA/downscaled QC2 | 666 |
| **TOTAL** | **1,750** |

The 1,750 consist of **1,559 water-formula negative RH** and **191 nonnegative RH below 1%**; original source RH is missing for **1,605**. Stage12 had 382 of 1,750 in targeted native temporal context, leaving **1,368 other records without targeted Stage12 context**. No science approval applies to any event.

## Exactly one review-priority class per record (priority ordering matters)

| Code | Review category | Rows |
|---|---|---:|
| 01 | Measured QC0/0 negative water-formula RH | 27 |
| 02 | ERA internal TA/VPD physically inconsistent under screened formula | 55 |
| 03 | Measured QC0/0 extreme low RH, 0–1% | 92 |
| 04 | Source-to-bracket-interpolation difference exceeds 10 hPa | 51 |
| 05 | ERA-implied vapor pressure not pairable with tower TA | 94 |
| 06 | Original good MDS QC1 VPD/humidity review | 822 |
| 07 | ERA QC2 VPD/humidity review | 609 |
| **TOTAL** | | **1,750** |

These *rank categories* are mutually exclusive, but underlying science conditions overlap. The 170 physical ERA holds from Stage14/Stage11 are **not identical** to 55 + 94 = 149 rank rows; other ERA holds may rank under #04. Likewise the 51 large original-to-bracket changes are a priority category, not automatic scientifically approved corrections.

### Site totals and largest review cohorts

| Site | All original low-RH events | Measured VPD QC0 | Good MDS QC1 | ERA VPD QC2 |
|---|---:|---:|---:|---:|
| US-UiD | 0 | 0 | 0 | 0 |
| US-UMB | 23 | 0 | 23 | 0 |
| US-UMd | 15 | 0 | 15 | 0 |
| US-Var | 62 | 0 | 62 | 0 |
| US-Vcm | 509 | 93 | 320 | 96 |
| US-Vcp | 629 | 0 | 172 | 457 |
| US-WCr | 88 | 26 | 60 | 2 |
| US-Whs | 1 | 0 | 1 | 0 |
| US-Wjs | 401 | 0 | 290 | 111 |
| US-Wkg | 22 | 0 | 22 | 0 |
| **TOTAL** | **1,750** | **119** | **965** | **666** |

### Scientific boundaries and next decision

- Mathematically feasible source-shadow MDS / ERA pairs, or bracketed interpolations, are not evidence that a proposed replacement is meteorologically accurate; in particular the original `VPD_F_QC2` is *already* ERA-derived, so reusing the identical `VPD_ERA` source cannot independently repair it.
- 27 source measured QC0/0 near-zero RH exceptions have <0.2 percentage point discrepancy under the current Magnus water formulation; source VPD/RH independence and native derivation formula are unverified. **Do not replace measured values automatically.**
- For the 822 source MDS-dominated unresolved priority records and 609 ERA-dominated records, the next useful science step is **source pair / temperature/ERA co-variability comparison and independent meteorological evidence** (with a verified tower site location, elevation, native clock, units and ERA5/ERA5-L origin), not another automatic numerical clipping rule.
- Prefer science-specific decisions with explicit recorded source, local time, units, QC0 anchors, independent validation, conservative unresolved **HOLD** states and no forcing alterations until an approved plan.

No model forcing is yet established as repaired; no Slurm jobs submitted.

# Batch03 Stage12f first 3 missing-year ERA5-Land sources VERIFIED; Stage12g candidate update

**2026-10-25 IRIDIS6 log:** Corrected Stage12f code passed Git-binary verification, AST syntax, regression self-test, original Stage12e/09a/09f source SHA verification, --check and --download --max-new 3. It detected precisely **2,810 original missing-year humidity events across 42 missing new site-years**, of which the first three priority site/year sources were requested at original SHA-pinned coordinates and returned by CDS successful, each physically/CF/UTC-hour/SHA verified. No site forcing or previously released source changed.

| Site | Year | Affected previously missing-year humidity events | Verified UTC hours | Verified original source SHA256 |
|---|---:|---:|---:|---|
| US-MtB | 2024 | 408 | 8928 | `f0a5fefe47922a221ef6cc76be62aa5eb4f202ffe9cff8b7e9c2e1266e3a7384` |
| US-MtB | 2022 | 328 | 8904 | `a50a36e7dadc491162fc4950a58d64b31f1869db0fabcee57fa833116c1a4dae` |
| US-MtB | 2020 | 302 | 8928 | `2f17efc227a46241fbcc4b54bf7b096ffa1f1f5d7661e8b76b9b6bcb4857744a` |
| **Total** | **3 new site-years** | **1,038 now supplied with gridded source** | | |

**Exactly 39 other site-years / 1,772 associated native humidity events remain without year-specific gridded source evidence.** This is not yet a forcing repair. The **original 233 science physics holds**, the 791 further tower/grid temperature mismatch, 20 ice phase, 49 excessive boundary cases, and all source clocks remain unchanged/held. The 1,687 Stage12b, 3,792 Stage12d and 702 Stage12e past numeric research candidates remain SHA-protected.

## Stage12g six-site fixed-temperature source application

[Stage12g SHA-verified newly downloaded yearly RH shadow script](../scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py) is committed, **not yet executed on IRIDIS6**. It re-verifies Stage12e's complete existing forcing and original Stage09a/09f/Stage12f receipts, source UTC coordinates and physically valid T2m/dewpoint/surface pressure. It reads 2,810 exactly identified Stage12e missing-year target records; only rows with **Stage12f verified new source-years** can be tested and patched.

The Stage12g method is strictly a **research-only humidity numerical replacement**: original VPD source must have QC1 or QC2, grid and retained EC tower T must agree within 5°C, surface pressures within 15 kPa, dewpoint and RH must be physically valid, subzero ice RH cannot exceed 100%, QBOT mass must close, and new VPD jumps >4 hPa are rejected. The **original EC tower TA_USE, TBOT, PSRF and native time index NEVER CHANGE**, and existing Stage12e good humidity values and original 233 held physics records are unaffected. Because source BIF UTC offsets are provisional, selected original-year ERA5-Land time alignment is still a hypothesis, not formal station-clock approval.

Run `--check` before `--run`; checks are in-memory with no writes. `--run` would create a wholly new, per-site full NO_LEAP six-site *INCOMPLETE* shadow, with per-target repair provenance, all 2,810 source holds classified, SHA receipt and reports, but **no DATM/CIME/Slurm/model release**. Follow the actual Stage12g candidate pass count before deciding whether downloading 39 more site-years is useful: US-MtB frequently had source ERA/grid temperature disagreement and a substantial share of new year evidence may not pass the fixed 5°C/ice/boundary guards. Do not blindly download all unverified years until evaluating these three.

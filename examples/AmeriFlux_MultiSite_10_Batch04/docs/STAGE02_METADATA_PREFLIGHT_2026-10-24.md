# AmeriFlux Batch04 — Stage02 coordinate/IGBP operator results (2026-10-24)

**Evidence:** user-supplied IRIDIS6 read-only Stage02 terminal output. Assistant has not independently accessed IRIDIS6.

**Result:** `STAGE02 SUMMARY: 9/10 coordinate + first-interval checks PASS; failures: US-Seg`. No original file, surface, forcing, CIME case or Slurm job changed.

| Site | Original BIF latitude | Original BIF longitude | BIF IGBP printed | First FLUXMET interval | Gate |
| --- | ---: | ---: | --- | --- | --- |
| US-Rpf | 65.1198 | -147.4290 | DBF | HH 30 min | PASS |
| US-Seg | 34.3623 | -106.7020 / -106.7019 | **NOT READ BY STAGE02** | **NOT CHECKED BY STAGE02** | REVIEW |
| US-Ses | 34.3349 | -106.7442 | OSH | HH 30 min | PASS |
| US-Slt | 39.9138 | -74.5960 | DBF | HH 30 min | PASS |
| US-SP1 | 29.7381 | -82.2188 | ENF | HH 30 min | PASS |
| US-SRG | 31.7894 | -110.8277 | GRA | HH 30 min | PASS |
| US-SRM | 31.8214 | -110.8661 | WSA | HH 30 min | PASS |
| US-Syv | 46.2420 | -89.3477 | MF | HH 30 min | PASS |
| US-Ton | 38.4309 | -120.9660 | WSA | HH 30 min | PASS |
| US-Uaf | 64.8663 | -147.8555 | ENF | HH 30 min | PASS |

## The US-Seg issue

The release BIF contains one latitude `34.3623` and two longitudes, `-106.7020` and `-106.7019` (about 9.18 m difference at the reported latitude). **Neither longitude has been approved as the sole operational coordinate.**

**External evidence, as found 2026-10-24, not a substitution:**
- [Research team site (Litvak Lab)](https://www.litvaklab.org/grassland---us-seg.html): `34.3623, -106.7019` (desert C4 grassland).
- [AmeriFlux current US-Seg site page](https://ameriflux.lbl.gov/sites/siteinfo/US-Seg): `34.3603, -106.7003`, IGBP GRA.
- Approximately 267–272 m separates the release BIF candidate points from the current AmeriFlux page coordinate. This does **not** prove tower relocation; metadata version, site conventions and source dates are still unknown.

**Next:** run the new Stage02B read-only coordinate-source inspector and review original `GROUP_ID` paired records, dates and comments; document an explicit provenance-based decision separately, not a silent auto-fix.

## Other scientific issues to preserve

- US-Rpf and US-Uaf: **0 height-related BIF entries** (not proof there are no tower height measurements elsewhere).
- US-Ton: **30 height-related BIF entries/fields**, including multiple `HEIGHTC` group records; not 30 independent tree-height measurements.
- Nonforest categories requiring model ecological review: US-Ses OSH, US-SRG GRA, US-SRM WSA and US-Ton WSA. Current official US-Seg GRA is an *external* label, not the Stage02 BIF-derived classification.
- `HEIGHTC` (canopy height) does not establish forcing `ZBOT` (meteorological measurement height).
- Stage02 only checks a first source interval per passing site, not full HH coverage, physical QC, climate forcing readiness, species/PFT fractions or DATM/spin-up convergence.

**Status boundary:** **0 forcing repairs, 0 site-coordinate approvals, 0 PFT/ZBOT approvals**.

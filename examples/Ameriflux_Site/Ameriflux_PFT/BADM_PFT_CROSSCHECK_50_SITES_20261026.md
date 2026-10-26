# Full AmeriFlux BADM vegetation evidence vs recommended PFT inputs (50 sites)

26 October 2026. The operator extracted the full BADM (`AMF_<SITE>_BIF_<date>.xlsx`, 50 of 50 files) with [scripts/03_extract_full_badm_vegetation.py](scripts/03_extract_full_badm_vegetation.py). The BADM groups read were IGBP, site description, overstory and understory species cover (`SPP_O` / `SPP_U`), and LAI, height and biomass context. Each site was then checked against [RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_20261026.csv](RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_20261026.csv).

Files:
- Per-site results: [BADM_VS_RECOMMENDED_PFT_50_SITES_20261026.csv](BADM_VS_RECOMMENDED_PFT_50_SITES_20261026.csv)
- Raw extraction: [metadata/full_badm_vegetation_50_20261026/](metadata/full_badm_vegetation_50_20261026/)
- Species-to-PFT map: [metadata/badm_species_to_pft_20261026.csv](metadata/badm_species_to_pft_20261026.csv)

**No recommended input was changed by this check.**

## Caveat on BADM percentages

None of the 50 files fills `SPP_PERC_UNIT`. The BADM standard defines that field as area, mass, number or estimated abundance. The comments show the basis varies from site to site, for example:
- basal area at US-WCr, US-Slt and the bracketed US-MOz values;
- biomass estimated from diameter at US-Ha1, US-UMB and US-UMd;
- inventory plots at the CA-TP sites and US-Bar.

So a BADM species percentage is a composition proxy, not a ground-area PFT fraction. The comparison below is made within the tree layer, plus the IGBP comments where these state cover or footprint shares.

## Result

| Verdict | Sites |
| --- | ---: |
| CONSISTENT: species or cover data agree | 23 |
| CONSISTENT_IGBP_ONLY: BADM gives only the IGBP class or a description, and it agrees | 19 |
| DIFFERENT_DENOMINATOR_OR_PERIOD: same forest, different metric or year; not an error | 5 (US-Bar, US-Ha1, US-Slt, US-UMB, US-UMd) |
| **CONFLICT_REVIEW** | **3 (US-Ho3, US-Syv, US-Wjs)** |

Batch01 (CA-TP1/3/4, CA-Ca3, CA-Man) matches BADM exactly. CA-TP4's ENF 93 / DBF 7 is the BADM inventory itself.

### Conflicts to decide

| Site | Recommended | BADM | Suggestion |
| --- | --- | --- | --- |
| US-Ho3 | ENF 90 / DBF 10 (regional prior) | IGBP comment "~80% ENF and 20% DBF in 200 m around tower"; 2005 FIA plots: hemlock 44, red spruce 20, red maple (no %) | ENF 80 / DBF 20 |
| US-Syv | ENF 50 / DBF 50 (hemlock dominates the surrounding 1 km²) | IGBP MF; tower plots (Tang et al. 2008): sugar maple 71, hemlock 14, yellow birch 7, basswood 8, ironwood 8 → ENF ≈ 13 | Choose the footprint scale: ~13/87 (tower plots) or 50/50 (1 km mixture); run both as a sensitivity |
| US-Wjs | ENF 15 / C4 85 (model precedent) | IGBP SAV; "Juniper savannah (~26% Juniper cover)" | ENF 26 / C4 74 |

### Same forest, different metric or year

| Site | Recommended | BADM | Note |
| --- | --- | --- | --- |
| US-Ha1 | ENF 27.3 (Richardson 2009 basal area) | 2010 overstory mass: ENF 17.4 | consider ENF 17 sensitivity |
| US-UMB | ENF 9 (Frasson 2015 basal area) | 2010 biomass: white pine 2.2 | biomass vs basal area |
| US-UMd | ENF 10 (2007 pre-girdling) | 2010 biomass: ENF 14 | after the 2008 girdling |
| US-Slt | ENF 38 (2018 state) | 2003–2008 basal area: pines 26.6 | matches the early-period alternative |
| US-Bar | ENF 17 | hemlock 17 of 61 listed, but IGBP comment "<10% total ENF" | BADM internally inconsistent; ENF 10 sensitivity |

## Per-site comparison

| Site | Recommended (GitHub) | BADM IGBP | BADM vegetation evidence | Verdict | Note |
| --- | --- | --- | --- | --- | --- |
| BR-Ma2 | TropEBF 100 | EBF | IGBP EBF; overstory species list (Dinizia excelsa, palms), no percentages | CONSISTENT |  |
| CA-Ca3 | ENF 100 | ENF | SPP_O PSME 75; IGBP comment Douglas-fir 75 / western red cedar 21 / grand fir 4 (all ENF) | CONSISTENT |  |
| CA-Cbo | ENF 18.6 / DBF 81.4 | DBF | IGBP DBF; "mixed deciduous forest from natural regrowth" | CONSISTENT_IGBP_ONLY | Recommended ENF share comes from 2006 stem counts; BADM has no species percentages |
| CA-LP1 | ENF 100 | ENF | IGBP ENF; "almost pure lodgepole pine stand" | CONSISTENT_IGBP_ONLY |  |
| CA-Man | ENF 100 | ENF | SPP_O PIMA (black spruce) 90; "occasional larch in poorly drained areas" | CONSISTENT | Remaining 10% unspecified; recommended uses 99% black-spruce basal area |
| CA-TP1 | ENF 100 | ENF | SPP_O PIST (white pine) 100 | CONSISTENT |  |
| CA-TP3 | ENF 99 / DBF 1 | ENF | SPP_O PIST 94; SPP_U PIBA2 (jack pine) 5, QUVE 1 → ENF 99 / DBF 1 | CONSISTENT | Identical to recommended |
| CA-TP4 | ENF 93 / DBF 7 | ENF | SPP_O PIST 82; SPP_U ABBA 11, ACRU 2, PRSE2 1, QUVE 4 → ENF 93 / DBF 7 | CONSISTENT | Identical to recommended |
| US-Aud | C4 70 / bare 30 | GRA | IGBP GRA | CONSISTENT_IGBP_ONLY |  |
| US-Bar | ENF 17 / DBF 83 | DBF | SPP_O from 12 FIA plots: ACRU 28, TSCA 17, BEPA 9, BEAL2 5, FAGR 2, POGR4 (no %); listed sum 61. IGBP comment "<10% total ENF" | DIFFERENT_DENOMINATOR_OR_PERIOD | BADM itself is inconsistent (hemlock 17% vs "<10% ENF"); recommended ENF 17 lies between. Keep, consider ENF 10 sensitivity |
| US-BZS | ENF 20 / ArcticEvergreenShrub 60 / ArcticDecidShrub 10 / ArcticC3 10 | ENF | IGBP ENF; "mature black spruce boreal forest on peat plateau" | CONSISTENT_IGBP_ONLY | Recommended ENF 20 = ~20% tree cover (point intercept); BADM gives no cover |
| US-CMW | DBF 74 / C4 26 | DBF | IGBP DBF; velvet mesquite woodland 7–10 m | CONSISTENT_IGBP_ONLY |  |
| US-EML | ArcticEvergreenShrub 20 / ArcticDecidShrub 30 / ArcticC3 50 | OSH | IGBP OSH; tundra on degrading permafrost | CONSISTENT_IGBP_ONLY |  |
| US-GLE | ENF 100 | ENF | IGBP comment: 85% Engelmann spruce, 15% subalpine fir (both ENF); 2008 beetle mortality 85% of basal area | CONSISTENT |  |
| US-Ha1 | ENF 27.3 / DBF 72.7 | DBF | SPP_O 2010 overstory (>10 cm DBH), mass estimated from diameter: red oak 45, red maple 20, hemlock 7.1, red pine 5.4, white pine 4.1, white spruce 0.7 → ENF 17.4 | DIFFERENT_DENOMINATOR_OR_PERIOD | Recommended ENF 27.3 is Richardson et al. (2009) basal area. Same forest, different metric/year; consider ENF 17 sensitivity |
| US-Ho1 | ENF 91.9 / DBF 8.1 | ENF | IGBP comment "~90% ENF and 10% DBF in 1 km around tower"; SPP_O PIRU 41, TSCA 25 (partial) | CONSISTENT |  |
| US-Ho2 | ENF 90 / DBF 10 | ENF | IGBP comment "~90% ENF and 10% DBF in 1 km around tower" | CONSISTENT |  |
| US-Ho3 | ENF 90 / DBF 10 | ENF | IGBP comment "~80% ENF and 20% DBF in 200 m around tower"; SPP_O TSCA 44, PIRU 20, ACRU (no %) (2005 FIA plots) | CONFLICT_REVIEW | Recommended ENF 90 / DBF 10 is a regional prior; BADM gives a tower-footprint 80 / 20 → suggest ENF 80 / DBF 20 |
| US-ICh | ArcticEvergreenShrub 30 / ArcticDecidShrub 20 / ArcticC3 50 | OSH | IGBP OSH; heath tundra | CONSISTENT_IGBP_ONLY |  |
| US-ICt | ArcticEvergreenShrub 15 / ArcticDecidShrub 25 / ArcticC3 60 | OSH | IGBP OSH; tussock tundra | CONSISTENT_IGBP_ONLY |  |
| US-Kon | CoolC3 10 / C4 90 | GRA | IGBP GRA; annually burned tallgrass prairie | CONSISTENT_IGBP_ONLY |  |
| US-Me2 | ENF 90 / EvergreenShrub 5 / HydrodecidShrub 5 | ENF | SPP_O ponderosa pine 100; sparse understory (LAI 0.2) manzanita / bitterbrush | CONSISTENT | Pre-2020-fire; fire and salvage logging 2020–2021 (recommended target period already pre-fire) |
| US-Me6 | ENF 80 / HydrodecidShrub 5 / CoolC3 15 | ENF | SPP_O ponderosa pine 100; SPP_U grass 13, bitterbrush 12, rabbitbrush 3, manzanita 1 | CONSISTENT |  |
| US-MMS | DBF 100 | DBF | IGBP DBF; 11 overstory species listed, all broadleaf deciduous, no percentages | CONSISTENT |  |
| US-MOz | ENF 10 / DBF 90 | DBF | SPP_O comments give basal area: white oak 39.5, Q. muehlenbergii 9.4, black oak 9.2, red cedar 9.0, sugar maple 7.0, hickory 6.1 → red cedar (ENF) 9.0% of total basal area | CONSISTENT | The SPP_O_PERC numbers themselves (e.g. red cedar 14.1) are a different metric; basal-area values agree with recommended ENF 10 |
| US-Mpj | ENF 60 / C4 20 / bare 20 | OSH; ENF; WSA | Pinyon + juniper >95% of tree cover, total tree cover ~60%; IGBP OSH/ENF → WSA after ~100% pinyon mortality 2013 | CONSISTENT | Recommended applies to 2008–2014; post-2013 state separate |
| US-MtB | ENF 100 | ENF | IGBP ENF; mixed evergreen conifer forest | CONSISTENT_IGBP_ONLY |  |
| US-NC2 | ENF 90 / DBF 10 | ENF | IGBP ENF; loblolly pine plantation (Pinus taeda), no percentages | CONSISTENT |  |
| US-NR1 | ENF 100 | ENF | SPP_O subalpine fir 46, Engelmann spruce 28, lodgepole pine 26 (all ENF); aspen outside main footprint | CONSISTENT |  |
| US-NR3 | ArcticC3 80 / bare 20 | GRA | IGBP GRA; snow-scoured alpine dry meadow | CONSISTENT_IGBP_ONLY |  |
| US-Rpf | DBF 80 / ColdDecidShrub 20 | DBF | IGBP DBF; birch and aspen with low shrubs after black-spruce fire | CONSISTENT_IGBP_ONLY |  |
| US-Seg | C4 60 / bare 40 | GRA; GRA | IGBP GRA; Chihuahuan Desert grassland; 2009 fire | CONSISTENT_IGBP_ONLY |  |
| US-Ses | EvergreenShrub 55 / C4 25 / bare 20 | OSH; OSH | IGBP OSH; creosote (Larrea) shrubland with C4 grasses | CONSISTENT_IGBP_ONLY |  |
| US-Slt | ENF 38 / DBF 62 | DBF | SPP_O 2003–2008 basal area: black oak 31.2, chestnut oak 24.5, white oak 17.6, pitch pine 15.4, shortleaf pine 11.2 → ENF 26.6 | DIFFERENT_DENOMINATOR_OR_PERIOD | Recommended ENF 38 is the 2018 post-defoliation state (Clark et al. 2022); BADM matches the early-period alternative |
| US-SP1 | ENF 85 / EvergreenShrub 15 | ENF | SPP_O longleaf pine 73, slash pine 27 (ENF) | CONSISTENT |  |
| US-SRG | DBF 11 / C4 44 / bare 45 | GRA | IGBP GRA; semidesert C4 grassland, less mesquite than US-SRM | CONSISTENT_IGBP_ONLY |  |
| US-SRM | DBF 35 / C4 20 / bare 45 | WSA | SPP_O velvet mesquite 35; IGBP comment ~35% mesquite canopy cover | CONSISTENT |  |
| US-Syv | ENF 50 / DBF 50 | MF | IGBP MF; SPP_O (Tang et al. 2008, 2002): sugar maple 71, hemlock 14, yellow birch 7, basswood 8, ironwood 8 → ENF ~13 | CONFLICT_REVIEW | Recommended ENF 50 / DBF 50 is a wider-footprint prior (hemlock dominates surrounding 1 km²); BADM tower-plot data give ~13 / 87. Choose footprint scale |
| US-Ton | DBF 43 / CoolC3 57 | WSA | Blue oak 40% of total vegetation; grey pine 3 trees/ha; IGBP WSA | CONSISTENT |  |
| US-Uaf | ENF 50 / ArcticEvergreenShrub 20 / ArcticDecidShrub 20 / ArcticC3 10 | ENF | IGBP ENF; open black spruce on dense shrub, sedge, moss understory | CONSISTENT_IGBP_ONLY |  |
| US-UiD | CoolC3 20 / C4 80 | GRA | IGBP GRA; restored native prairie | CONSISTENT_IGBP_ONLY |  |
| US-UMB | ENF 9 / DBF 91 | DBF | SPP_O 2010 biomass: bigtooth aspen 37.9, red oak 16.2, red maple 14, trembling aspen 12.5, paper birch 7.5, beech 4.2, sugar maple 2.3, white pine 2.2 → ENF 2.3 | DIFFERENT_DENOMINATOR_OR_PERIOD | Recommended ENF 9 uses Frasson et al. (2015) basal area (white pine 9%); biomass and basal area differ |
| US-UMd | ENF 10 / DBF 90 | DBF | SPP_O 2010 biomass (post-girdling): red oak 34.7, bigtooth aspen 28.5, white pine 10.9, red maple 10.7, red pine 3.1 → ENF 14 | DIFFERENT_DENOMINATOR_OR_PERIOD | Recommended ENF 10 is the 2007 pre-treatment state; BADM is after the 2008 girdling |
| US-Var | CoolC3 100 | GRA | IGBP GRA; annual C3 grasses and forbs (blue oak listed without %) | CONSISTENT |  |
| US-Vcm | ENF 100 | ENF; ENF | IGBP ENF; spruce, fir, pine; stand-replacing fire May 2013 | CONSISTENT | Recommended applies to 2007–2012 only |
| US-Vcp | ENF 100 | ENF; ENF | IGBP ENF; ponderosa pine overstory, Gambel oak understory | CONSISTENT | Recommended ENF 100 omits the oak understory (minor) |
| US-WCr | DBF 100 | DBF | SPP_O basal area: sugar maple 43.2, basswood 32.5, green ash 13.1, red oak 6.2, others <2 (all DBF) | CONSISTENT |  |
| US-Whs | EvergreenShrub 20 / HydrodecidShrub 20 / C4 3 / bare 57 | OSH | IGBP OSH; whitethorn acacia, creosote, tarbush shrubland | CONSISTENT_IGBP_ONLY |  |
| US-Wjs | ENF 15 / C4 85 | SAV | IGBP SAV; IGBP comment "Juniper savannah (~26% Juniper cover)"; C4 grass Bouteloua gracilis | CONFLICT_REVIEW | Recommended ENF 15 / C4 85 is a model precedent; BADM gives ~26% juniper cover → suggest ENF 26 / C4 74 |
| US-Wkg | HydrodecidShrub 3 / C4 37 / bare 60 | GRA | IGBP GRA; Bouteloua spp., Eragrostis lehmanniana | CONSISTENT_IGBP_ONLY |  |

## Disturbance and period notes from BADM

The recommended target periods already account for these events:
- US-Me2: fire in 2020, salvage logging in 2021.
- US-Vcm: stand-replacing fire in 2013.
- US-Mpj: pinyon mortality from 2013, with IGBP changing to WSA.
- US-GLE: beetle mortality peaking in 2008, killing 85% of basal area.
- US-Seg: fire in 2009.
- US-WCr: thinning in 2013–2014.
- US-UMd: girdling in 2008.

# Six sparse or open sites: PFT and bare-ground evidence for FIXNC surfaces

**Date:** 25 October 2026. **Scope:** GL-ZaH, IL-Yat, ES-LJu, IT-Noe (high priority), ES-Agu (medium), NL-Loo (low). **Machine-readable table:** [six_site_bare_ground_PFT_proposals_20261025.csv](six_site_bare_ground_PFT_proposals_20261025.csv). The master table carries the same proposals in its `BareGround_*` columns.

**Why this matters.** In FATES nocomp with fixed biogeography, `PCT_NAT_PFT` sets the area each PFT occupies. A sparse site written as 100% vegetation lets FATES grow a closed canopy on ground that is really rock, gravel or bare soil, inflating LAI, GPP, transpiration and carbon pools. Host natural-PFT index 0 (bare ground) must therefore carry measured non-vegetated ground. In nocomp mode the pinned FATES treats it as a bare-ground patch; this was verified in the source on IRIDIS6 for IL-Yat.

**Rules used.** Proposals keep each source's denominator. Unidentified **ground** is not silently given to grass. Mosses, lichens and biocrust have no FATES PFT, so they count as bare. Every number below is a named *proxy* for a model input, not a measured footprint-weighted map. The project's [residual-PFT policy](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/docs/PFT_UNKNOWN_RESIDUAL_POLICY.md) applies.

## Summary

| Site | Measured vegetation vs non-vegetated ground | Proposed `PCT_NAT_PFT` (primary) | Main open issue |
| --- | --- | --- | --- |
| **GL-ZaH** | Cassiope heath: vascular 57% (Cassiope 53, Salix 3), mosses 8, lichens 3; ~32% uncovered; heath LAI 0.2–0.3 | **Bare 43** / evergreen arctic dwarf shrub 53 / deciduous arctic shrub 3 / arctic C3 grass 1 | Default map cannot prescribe an evergreen arctic shrub |
| **IL-Yat** | Crown cover 48% (72 plots; 0.40–0.70); rock outcrop 36.8% | **Bare 52** / ENF 48 (now running as `IL-Yat_B03_FIXNC_BARE52_AD400`) | Crown cover is from the mid-2000s |
| **ES-LJu** | Bare soil + gravel + rock **49.1%**; Festuca 18.8, Hormathophylla 6.8, Genista 5.5; 19.8% vegetation unnamed | **Bare 49** / C3 grass 31 / evergreen shrub 20 | 19.8% unnamed vegetation; cushion-shrub phenology |
| **IT-Noe** | Ground cover **42–91%** across the site; juniper 53% and lentisk 22% *of vegetated surface* | **Bare 34** / evergreen shrub 66 (midpoint) | No footprint-weighted cover; juniper is a needleleaf *shrub* |
| **ES-Agu** | Vegetation **51%**; gravel, rock and bare soil **49%**; Macrochloa 57% of vegetation cover | **Bare 49** / C3 grass 29 / evergreen shrub 22 | Whether 57% is of vegetation or ground |
| **NL-Loo** | 500-m map: ENF 93.6, DBF 2.9, open 3.5% (heather and grass) | ENF 93.6 / DBF 2.9 / C3 grass 3.5 / **Bare 0** | No bare ground is evidenced |

## GL-ZaH (Zackenberg heath, NE Greenland) — HIGH

- **Vegetation plots.** Five 1997 Cassiope-heath plots give vascular cover 57% (*Cassiope tetragona* 53%, *Salix arctica* 3%, herbs < 1%), mosses 8% and lichens 3%. Dryas heath plots give vascular 62% (*Dryas* 58%, *Salix* 3%). Stones and boulders are reported only for a Vaccinium heath plot (20%). The heath plots do not list bare ground, so ~32% is the uncovered complement. ([Bay 1998 vegetation mapping](https://www.zackenberg.dk/fileadmin/Resources/DMU/GEM/Zackenberg/pdf/vegetation-mapping-zackenberg-valley_.pdf))
- **Tower setting.** The heath tower stands in a sparse heath dominated by Cassiope, Dryas and Vaccinium with patches of moss, Salix and Eriophorum. Peak-season single-sided LAI is only 0.2–0.3. The footprint lies roughly 200–500 m from the mast, inside the ~5.5-km² heath (31% of the valley). ([NERI PhD thesis on the heath site](https://www2.dmu.dk/Pub/phd_lgr.pdf))
- **Valley scale.** Below 200 m, heaths cover 30.6% of the valley, grassland 17.8%, fens 11.6%, willow snowbeds 19.2% and fell-field/barren 20.6%. ([valley scaling study](https://www.researchgate.net/publication/253453187)) The earlier CLM host surface had 74.41% bare ground, which reflects a coarse grid rather than the heath footprint.
- **Proposal.** Bare 43 (uncovered 32 + mosses/lichens 11) / evergreen arctic dwarf shrub 53 / deciduous arctic shrub 3 (HLM 11) / arctic C3 grass 1 (HLM 12). Sensitivity: Dryas-weighted bare ~38.
- **Blocking issue.** In the default `fates_hlm_pft_map`, no host index maps solely to `broadleaf_evergreen_arctic_shrub`; HLM 11 sends only 10% there and 80% to the deciduous arctic shrub. Representing Cassiope correctly needs a **private FATES parameter file** for this site, routing one host index (for example HLM 9) to the evergreen arctic shrub. Do not edit the shared parameter file.

## IL-Yat (Yatir, Israel) — HIGH, implemented

Mean crown cover is 48%, measured from crown widths in 72 plots (satellite FVC 0.40–0.70). Rock outcrop covers 36.8% of the surface, and the understory is minor and grazed. The case now runs as **bare 52 / ENF 48**. The AD5 was resubmitted on 25 October after the stack fix and is running. Full review: [IL-Yat bare-ground literature review](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/examples/Batch03_10/docs/IL_Yat_bare_ground_PFT_literature_20261025.md).

## ES-LJu (Llano de los Juanes, Sierra de Gádor, Spain) — HIGH

- **Ground cover.** Bare soil, gravel and rock make up 49.1% of the ground cover. Vegetation is sparse: *Festuca scariosa* 18.8%, *Hormathophylla spinosa* 6.8% and *Genista pumila* 5.5%. ([BG 7:859, 2010 site description citing Were et al. 2010](https://bg.copernicus.org/articles/7/859/2010/bg-7-859-2010.pdf); [Pérez Sánchez-Cañete thesis](https://www.ugr.es/~andyk/Theses/TesisKike.pdf)) The named species total 31.1%, which leaves 19.8% of vegetation unnamed.
- **Primary proposal.** Bare 49 / cool C3 grass 31 (HLM 13) / evergreen temperate shrub 20 (HLM 9). The unnamed 19.8% is known to be vegetation, so it is split pro rata to the named grass:shrub ratio (18.8:12.3) as a labelled proxy. **Strict alternative:** bare 49.1 / grass 18.8 / shrub 12.3 / unresolved 19.8 (HOLD).
- **Open choice.** Both shrubs are cushion chamaephytes. *Genista pumila* is largely green-stemmed, and the phenology of *Hormathophylla spinosa* was not verified. HLM 9 (evergreen) versus HLM 10 (cold-deciduous) is therefore a modelling choice; keep a sensitivity.

## IT-Noe (Arca di Noè – Le Prigionette, Sardinia) — HIGH

- **Evidence.** The site is a sparse maquis. Shrubs grow in patches with bare ground between them, and ground cover varies from **42 to 91%** across the site; a second description gives 45–95%. Juniper (*Juniperus phoenicea*) covers 53% and lentisk (*Pistacia lentiscus*) 22% of the **vegetated** surface; *Phillyrea* and *Chamaerops* occur as isolated elements. Maquis height is 0.9–1.8 m and LAI 2.7–3.0. ([Italian flux-site chapter, Noè section](https://openpub.fmach.it/bitstream/10449/25172/2/9783642324239-c2.pdf); [iForest macchia study](https://iforest.sisef.org/contents/?id=ifor0605-009))
- **Proposal.** Bare 34 / evergreen temperate shrub 66 (HLM 9), using the midpoint of the 42–91% range. The ends of the range give bare 58 / shrub 42 and bare 9 / shrub 91.
- **Mapping.** Juniper here is a ~1-m needleleaf **shrub**. FATES has no needleleaf shrub, so the whole maquis goes to `broadleaf_evergreen_extratrop_shrub`, not to an ENF tree.
- **Next evidence.** A footprint-weighted cover fraction, for example from orthophoto or LiDAR classification within the 80% footprint, would replace the midpoint.

## ES-Agu (Balsa Blanca, Cabo de Gata, Spain) — MEDIUM

- **Evidence.** Ground cover is gravel, rock and bare soil (49%) plus vegetation (51%), citing Rey et al. (2011). *Macrochloa tenacissima* dominates; other species are *Chamaerops humilis*, *Rhamnus lycioides*, *Pistacia lentiscus*, *Olea europaea* var. *sylvestris*, *Asparagus horridus* and *Rubia peregrina*. ([BG 23:2569, 2026](https://bg.copernicus.org/articles/23/2569/2026/)) The thesis gives *Macrochloa* "57% of vegetation cover" ([Pérez Sánchez-Cañete thesis](https://www.ugr.es/~andyk/Theses/TesisKike.pdf)).
- **Proposal.** Bare 49 / cool C3 grass 29 (HLM 13; *Macrochloa* is a C3 tussock grass) / evergreen temperate shrub 22 (HLM 9), reading 57% as a share of the 51% vegetation.
- **Unresolved.** The 57% denominator should be checked in Rey et al. (2011) Table 1. A remote-sensing source gives ~65% vegetation (bare ~35). Biocrust is present but not separated; it would count as bare.

## NL-Loo (Loobos, Netherlands) — LOW

- **Evidence.** Within 500 m of the tower: Scots pine 89%, Corsican/black pine 3.3%, Douglas fir 1.3%, birch 2.3%, oak 0.6%, and open area 3.5%, **mostly heather and grass** (Moors 2012, cited in the [Loobos ESSD dataset paper](https://essd.copernicus.org/articles/18/2023/2026/)). The 80% footprint has a radius of about 270–500 m. The 2023 ICOS inventory of trees > 5 cm DBH gives stems of pine 61%, *Prunus serotina* 20% (understory), *Quercus robur* 10% (two plots) and birch 4%. These are stem shares, not area. ([ICOS Loobos station paper, preprint](https://essd.copernicus.org/preprints/essd-2026-99/essd-2026-99.pdf))
- **Proposal.** ENF 93.6 / DBF 2.9 / cool C3 grass 3.5 / **bare 0**. The open area is not bare sand. A heather (HLM 9) versus grass split of the 3.5% is optional. NL-Loo stays a protected legacy example and is not altered.

## Recommended order

1. **IL-Yat:** done; check the AD5 output for a vegetation-free bare patch.
2. **ES-LJu and ES-Agu:** ground-cover evidence is direct (49% non-vegetated at both). Decide the shrub phenology and the ES-Agu 57% denominator, then build surfaces with the Batch03 bare-ground-capable builder.
3. **IT-Noe:** use the midpoint as an explicit proxy with range sensitivity, or first derive footprint cover from imagery.
4. **GL-ZaH:** needs a site-only FATES parameter map before any surface makes scientific sense.
5. **NL-Loo:** no change needed.

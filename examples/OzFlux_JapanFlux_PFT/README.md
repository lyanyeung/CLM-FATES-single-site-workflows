# OzFlux and JapanFlux PFT inputs — 20 stations (v1.1)

Fixed-composition (FIXNC) PFT inputs for the 9 OzFlux stations in [OzFlux_MultiSite_09](../OzFlux_MultiSite_09/) and the 11 JapanFlux stations in [JapanFlux_MultiSite_11](../JapanFlux_MultiSite_11/). The layout follows [Ameriflux_PFT](../Ameriflux_Site/Ameriflux_PFT/) and [ICOS_PFT](../ICOS_sites/ICOS_PFT/).

**Status, 2 November 2026: v1.1 final.** These are model hypotheses, not observations.

- **Review.** v1 was reviewed against the literature and field data the same day, and the operator accepted the review.
- **Six sites changed:** AU-ASM, AU-DaS, AU-How, JP-Yms, JP-Tef and JP-Tmd. Their v1 primaries are kept as `v1_primary_20261102` sensitivity rows.
- **No model inputs were touched:** no surface, parameter file, forcing, case or job was created or changed.

## Operator decisions (2 Nov 2026)

1. The review is accepted, and the tables below are the v1.1 primaries.
2. **Bare ground keeps its own share** wherever a site has open ground, as for the 50 AmeriFlux and 38 ICOS stations. It is never folded into vegetation or renormalised away.
3. **JP-Tef** uses the post-clearcut state.
4. **JP-Tmd** uses a trajectory compromise after a dedicated review. See [JP-Tmd: how the site changed](#jp-tmd-how-the-site-changed).

## Final vectors

Values are percent of the natural-vegetation landunit, including bare ground (host 0). FATES PFTs:

| Label | FATES PFT |
| --- | --- |
| TropEBT | 1 |
| ENF | 2 |
| DNF | 3 |
| EBT | 4 |
| HydrodecidTropTree | 5 |
| DBF | 6 |
| EvergreenShrub | 7 |
| ColdDecidShrub | 9 |
| CoolC3 | 13 |
| C4 | 14 |

| Network | Site | Ecosystem | v1.1 primary | Basis | Uncertainty | Changed |
| --- | --- | --- | --- | --- | --- | --- |
| OzFlux | AU-ASM | Mulga (*Acacia*) woodland, arid | EBT 65 / C4 4 / CoolC3 2 / bare 29 | crown cover + AusPlots point intercept | MEDIUM | yes |
| OzFlux | AU-Cow | Lowland tropical rainforest | TropEBT 100 | 1 ha census | LOW | |
| OzFlux | AU-Cpr | Mallee woodland, semi-arid | EBT 33 / EvergreenShrub 10 / C4 3 / bare 54 | NVIS strata cover | HIGH | |
| OzFlux | AU-DaS | Eucalypt savanna (uncleared) | TropEBT 37.5 / C4 42.5 / bare 20 | satellite FPC | HIGH | yes |
| OzFlux | AU-Dry | Eucalypt open-forest savanna | TropEBT 26.6 / C4 49.4 / bare 24 | satellite FPC | HIGH | |
| OzFlux | AU-How | Eucalypt open-forest savanna | TropEBT 39.8 / C4 44.3 / bare 15.9 | satellite FPC | MEDIUM | yes |
| OzFlux | AU-Gin | *Banksia* woodland | EBT 45 / EvergreenShrub 35 / bare 20 | prior only | HIGH | |
| OzFlux | AU-Stp | Mitchell grass (*Astrebla*) grassland | C4 65 / bare 35 | satellite FPC | MEDIUM | |
| OzFlux | AU-Tum | Tall wet sclerophyll eucalypt forest | EBT 100 | dominant type | MEDIUM | |
| JapanFlux | JP-Api | Beech (*Fagus crenata*) forest | DBF 100 | dominant type | LOW | |
| JapanFlux | JP-Fhk | Larch plantation | DNF 84.6 / ENF 7.7 / DBF 7.7 | basal area | MEDIUM | |
| JapanFlux | JP-Fjy | Red pine (*Pinus densiflora*) forest | ENF 100 | dominant type | MEDIUM | |
| JapanFlux | JP-Khw | Sugi/hinoki plantation | ENF 100 | stand identity | LOW | |
| JapanFlux | JP-Spp | Birch-oak secondary forest | DBF 100 | basal area / biomass | MEDIUM | |
| JapanFlux | JP-Tak | Cool-temperate deciduous forest | DBF 100 | basal area | LOW | |
| JapanFlux | JP-Tef | Post-clearcut larch strips + *Sasa* | DNF 50 / CoolC3 50 | planting-design area | MEDIUM | yes |
| JapanFlux | JP-Tmd | Windthrow regrowth: shrub → herb → birch | DBF 30 / CoolC3 60 / ColdDecidShrub 5 / bare 5 | LAI/biomass trajectory | HIGH | yes |
| JapanFlux | JP-Tom | Cool-temperate deciduous forest | DBF 100 | dominant type | MEDIUM | |
| JapanFlux | JP-Tgf | Mown C3/C4 grassland | CoolC3 40 / C4 60 | C3/C4 prior | HIGH | |
| JapanFlux | JP-Yms | Oak-dominated mixed secondary forest | DBF 66 / EBT 28 / ENF 6 | functional-group biomass | MEDIUM | yes |

The host matrix is in [OZ_JP_RECOMMENDED_CLM_PCT_NAT_PFT_20261102.csv](OZ_JP_RECOMMENDED_CLM_PCT_NAT_PFT_20261102.csv). The FATES matrices, one with bare and one vegetated-only, are in [OZ_JP_RECOMMENDED_FATES_PFT_PERCENT_20261102.csv](OZ_JP_RECOMMENDED_FATES_PFT_PERCENT_20261102.csv).

## How to read these numbers

- **Area, not cover.** FATES `use_fates_nocomp` gives each PFT its own patch, so overlapping strata cannot coexist. Grass under trees, *Sasa* under a canopy and forest understoreys are either dropped or given their own area. Forests follow the AmeriFlux convention: trees only, bare 0.
- **The source basis differs between sites:** stems, basal area, biomass, LAI, crown cover, field point intercept, satellite FPC or a planting design. The basis is named in the master CSV and never silently renormalised.
- **Bare** is a share of land, and it is not "bare soil" in a strict sense:
  - AU-ASM: field point intercept. The share includes litter and cryptogam crust.
  - Savannas and AU-Stp: ground uncovered at peak green cover.
  - AU-Cpr: land outside the listed vegetation strata.
  - JP-Tmd: a placeholder for stumps and debris.
- **Mapping.** All 20 sites use only one-to-one DEFAULT14 rows:

  | Host (CLM) | FATES PFT |
  | --- | --- |
  | 1 | 2 |
  | 3 | 3 |
  | 4 | 1 |
  | 5 | 4 |
  | 6 | 5 |
  | 7 | 6 |
  | 9 | 7 |
  | 10 | 9 |
  | 13 | 13 |
  | 14 | 14 |

  This is the `DEFAULT14` of the AmeriFlux B3_01 machinery. No site-private map is needed, but the parameter file of any new case must still be checked.
- **Period.** Each vector describes one stated period; see [Time-dependent sites](#time-dependent-sites).

## What each site is like

### OzFlux

**AU-ASM, Alice Springs Mulga: EBT 65 / C4 4 / CoolC3 2 / bare 29.**
- *Site.* Evergreen mulga (*Acacia aneura*, *A. aptaneura*), about 6.5 m tall. Basal area 8 m²/ha, about 3300 stems/ha. Red Kandosol.
- *Woody share.* Woody cover is 65 % by airborne lidar (pixels over 2 m; preprint), 74.5 % of land area (Cleverly et al. 2016) and 70–80 % on the TERN core plot. v1 had used 43, from an LAI ratio.
- *Herb vs bare.* TERN AusPlots point-intercept data from the two 1 ha plots beside the tower (1,010 points; March 2012 wet, July–August 2020 dry) split the remaining 35:
  - Herbs: 18 % of the points with no woody hit.
  - The rest (82 %) is bare ground: about a third bare soil, a third litter, a third cryptogam crust.
- *Herb pathway.* In the 2012 wet survey, grass was about 68 % C3 (*Thyridolepis mitchelliana*). In the 2020 dry survey, it was about 99 % C4 (*Paspalidium*, *Aristida*). The primary uses the four-visit mean of 35:65.
- *Model choices.* Mulga stays FATES4, as decided in OzFlux Stage21; FATES7 is a sensitivity run. Mulga1 and Mulga2 are separate records, and the 2018–2020 dieback is not represented.

**AU-Cow, Cow Bay: TropEBT 100.**
- *Site.* Complex mesophyll vine forest, canopy about 25 m.
- *Census (1 ha, 2012).* 625 stems ≥10 cm, basal area 34.1 m²/ha.
- *Palms.* 19 % of stems and 9.7 % of basal area, folded into TropEBT.
- *Not represented.* Cyclone Jasper (December 2023).

**AU-Cpr, Calperum: EBT 33 / EvergreenShrub 10 / C4 3 / bare 54.**
- *Site.* Multi-stem mallee eucalypts, about 4 m tall, basal area 4.3 m²/ha.
- *Strata (TERN NVIS 2012).* Tree mallee 33.4 %; chenopod plus *Maireana* shrubs 10.4 %; tussock grass 2.3 %; forbs 0.9 %. Lidar canopy cover is 43 %.
- *Grass.* *Triodia scariosa* (C4) is the only grass in the core plot, but its hummock cover was not measured and sits inside the 54 % bare.
- *Period.* The vector is the pre-fire state; a fire burnt part of the woodland in January 2014.

**AU-DaS, Daly River Uncleared: TropEBT 37.5 / C4 42.5 / bare 20.**
- *Site.* Savanna of *Eucalyptus tetrodonta*, *Corymbia latifolia* and semi-deciduous *Terminalia grandiflora*, over C4 *Sorghum* and *Heteropogon*.
- *Structure.* Basal area 8.3 m²/ha, 330 stems/ha, height 16.4 m.
- *Cover.* Tree and grass cover come from satellite FPC (Nijzink et al. 2022). The tree term is the dry-season minimum, which the paper calls the evergreen component, so all of it is TropEBT.
- *Deciduous trees.* Their foliage is inside the seasonal 42.5 term. v1 split the tree cover 80:20 using a ratio borrowed from Howard Springs; that split is dropped.
- *Bare.* 20 = ground uncovered at peak cover.

**AU-Dry, Dry River: TropEBT 26.6 / C4 49.4 / bare 24.**
- *Site.* Drier open-forest savanna of *E. tetrodonta*, *E. dichromophloia* and *C. terminalis*, all evergreen, over C4 *Sorghum*, *Themeda* and *Chrysopogon*.
- *Structure.* Basal area 5.4 m²/ha, LAI 0.58.
- *Cover.* From satellite FPC, as for AU-DaS.

**AU-How, Howard Springs: TropEBT 39.8 / C4 44.3 / bare 15.9.**
- *Site.* Open forest of *E. miniata* and *E. tetrodonta*, with *Erythrophleum* and *Terminalia* (50–100 % leaf drop), over tall C4 grass. Burnt every 1–3 years.
- *Structure.* 661 stems/ha, basal area 9.7 m²/ha, height 18.9 m.
- *Cover.* Same definition as AU-DaS. About 15 % of the overstorey is deciduous; see the sensitivity row `deciduous_15pct_from_seasonal`.
- *Bare.* The satellite cell includes seasonal lagoons, so the 15.9 bare is probably too high.
- *Existing case.* The AU-How case that already ran used full FATES competition; this FIXNC vector is a separate experiment.

**AU-Gin, Gingin: EBT 45 / EvergreenShrub 35 / bare 20 (provisional prior).**
- *Site.* *Banksia menziesii*, *B. attenuata* and *B. grandis* woodland, about 7 m tall, on deep sand. 99 understorey species.
- *Structure.* Basal area 11.6 m²/ha, LAI 0.8–1.3.
- *Evidence gap.* No cover number exists, so all three values are priors.
- *Not represented.* The 2023–24 dieback and a fuel-reduction burn.

**AU-Stp, Sturt Plains: C4 65 / bare 35.**
- *Site.* Treeless *Astrebla* (C4, NAD-ME) grassland on cracking clay; lightly grazed, frequent fire.
- *Cover.* Total peak cover is 65 %. Nijzink also counted all of it as grass.

**AU-Tum, Tumbarumba: EBT 100.**
- *Site.* *E. delegatensis* and *E. dalrympleana*, about 44 m tall, basal area 41.2 m²/ha.
- *Understorey.* Understorey LAI is about 1.5, similar to tree LAI 1.4; it is dropped by the forest convention.
- *Fire.* The fire of 31 December 2019 killed nearly all the ash, so post-2020 years are a different state.

### JapanFlux

**JP-Api, Appi: DBF 100.**
- *Site.* Nearly pure *Fagus crenata*, about 20 m, LAI up to 4.8, no understorey.
- *Not represented.* The 2007 caterpillar defoliation.

**JP-Fhk, Fuji Hokuroku: DNF 84.6 / ENF 7.7 / DBF 7.7.**
- *Site.* *Larix kaempferi* plantation; larch is 30.3 of 35.8 m²/ha basal area (2010).
- *Other trees.* The other 5.5 m²/ha is pine and fir (ENF) plus oak, birch and *Swida* (DBF), split equally by assumption.
- *Thinning.* May 2014 and March 2015 (409 → 249 stems/ha), inside the 2006–2023 record.

**JP-Fjy, Fujiyoshida: ENF 100.**
- *Site.* About 90-year *Pinus densiflora* on lava.
- *Not quantified.* The *Ilex pedunculosa* subtree layer.

**JP-Khw, Kahoku: ENF 100.**
- *Site.* Sugi (*Cryptomeria*) and hinoki (*Chamaecyparis*) plantation.
- *Fluxes.* Daytime fluxes are kept only for the sugi wind sector.

**JP-Spp, Sapporo: DBF 100.**
- *Site.* Birch-oak secondary forest; birch plus oak are over 75 % of basal area (2003).
- *Typhoon.* Songda (8 September 2004) removed 33 % of the canopy. Afterwards *Sasa* LAI (4.05) exceeded tree LAI.
- *Valid period.* The vector fits 2000–2004 only. The `sasa_c3_patch_placeholder` scenario represents the post-typhoon years.

**JP-Tak, Takayama: DBF 100.**
- *Site.* *Quercus crispula* and *Betula ermanii*/*platyphylla*; deciduous species are 97.2 % of basal area.
- *Understorey.* *Sasa senanensis* is about 24 % of LAI and is dropped.

**JP-Tef, Teshio CC-LaG: DNF 50 / CoolC3 50.**
- *History.* The mixed forest was clear-cut in January–March 2003. The *Sasa* was strip-cut in 4 m rows, and about 2500/ha hybrid larch were planted in the cut rows in October 2003.
- *Area split.* Cut and uncut rows each cover half of the area. This planting design is the only true area measurement in the JapanFlux set, so larch rows → DNF 50 and *Sasa* rows → CoolC3 50.
- *Sasa under larch.* Weeding stopped in 2007, and *Sasa* filled the gaps between the larch by 2008–2010. FIXNC drops that under-larch *Sasa*.
- *Growth.* Larch PAI rose from 0.9 (2004) to 1.7 (2013); *Sasa* PAI was 4.3–6.1.
- *Not represented.* The pre-harvest forest years 2001–2002. The weeded early years are the `weeded_strips_2004_2006` scenario.

**JP-Tmd, Tomakomai disturbed: DBF 30 / CoolC3 60 / ColdDecidShrub 5 / bare 5.**
- *History.* The former larch plantation (JP-Tmk) was blown down in 2004 and has regrown naturally.
- *Vector.* A compromise across a strongly changing record; see the next section.

**JP-Tom, Tomakomai Experimental Forest: DBF 100.**
- *Site.* *Quercus crispula*, *Betula platyphylla* and *Acer mono*, about 16 m, LAI 4–6, over dwarf bamboo.
- *Evidence gap.* No basal-area shares were found.

**JP-Tgf, Tsukuba grassland: CoolC3 40 / C4 60.**
- *Site.* C3 *Solidago altissima* dominates spring and early summer. C4 *Miscanthus* and *Imperata* dominate late summer and autumn, when biomass peaks (680–886 g/m²).
- *Support for the C4 lean.* C4 grasses produce about 63–67 % of autumn ecosystem respiration.
- *Evidence gap.* No measured cover split exists.
- *Management.* Mown twice a year since 2006.

**JP-Yms, Yamashiro: DBF 66 / EBT 28 / ENF 6.**
- *Site.* Secondary forest that followed the 1980s pine wilt.
- *Biomass shares (1999 living trees).* Deciduous broadleaf 66 % (*Q. serrata*), evergreen broadleaf 28 % (*Ilex pedunculosa*, a canopy tree) and conifer 6 % (*P. densiflora*).
- *v1 error.* The 6 % had been put into DBF.

## JP-Tmd: how the site changed

**Short answer: the effect on PFT composition is large.** The dominant life form changes twice within the 2005–2023 record. No area or cover fraction exists for any year, so every vector here uses LAI and biomass shares as proxies.

| Period | What happened | Evidence |
| --- | --- | --- |
| 8 Sep 2004 | Typhoon Songda blew down more than 90 % of the larch, mostly uprooted. Aboveground biomass before the storm was about 91 Mg/ha. | Sano et al. 2010 Sect. 2.1, 3.1 |
| 2004 – summer 2005 | Salvage logging removed the trunks (36 MgC/ha). Stumps, branches and 11 MgC/ha of coarse debris stayed. No replanting; no larch survived. | Sano et al. 2010 Sect. 4.2; Yazaki et al. 2016 Sect. 2.1, 3.1 |
| 2005–2009, shrub phase | *Rubus idaeus* (a deciduous shrub) dominated: about 60 % of biomass and 50 % of LAI in 2006. Grasses were about 20 % of LAI. Total understorey LAI was about 3.8, a nearly closed low canopy. | Sano et al. 2010 Sect. 3.1; Yazaki et al. 2016 Sect. 3.1, 3.3 |
| 2010–2014, herb phase | *Solidago gigantea* (C3 forb) took over, about 70 % of understorey biomass in 2011; *Rubus* almost disappeared by 2014. Birch saplings went from 3190/ha, 1.5 m, LAI 0.40 (2010) to 4380/ha, 2.0 m, LAI 0.76 (2014), and trees reached 48 % of aboveground biomass. Understorey LAI was 2.7–3.6. | Yazaki et al. 2016 Table 1, Table A1, Sect. 3.1–3.3, 4.1 |
| 2015–2023, birch phase | *Betula platyphylla* growth became "remarkable" (a 30 m tower was built in 2019), and the vegetation is described as Betula-dominated by about 2022. These are qualitative statements only. | CGER News 2023; NIES SR-132; ESJ69 |
| Dataset label | JapanFlux2024 labels the first 10 years after disturbance GRA and the period after that DBF. | Ueyama et al. 2025 Table 3 |

Period vectors are kept as sensitivity rows:

| Scenario | Vector |
| --- | --- |
| `early_Rubus_2005_2009` | CoolC3 40 / ColdDecidShrub 55 / bare 5 |
| `mid_Solidago_2010_2014` | DBF 15 / CoolC3 70 / ColdDecidShrub 10 / bare 5 |
| `late_Betula_2015_2023` | DBF 55 / CoolC3 40 / ColdDecidShrub 5 |

**The primary (DBF 30 / CoolC3 60 / ColdDecidShrub 5 / bare 5) is the mid state shifted toward trees.** Three reasons:
- Herbs dominated LAI through at least 2014.
- The shrub phase lasted only about five years.
- Year-round flux data exist only from 2013.

Recommended handling:
- **Evaluate 2005–2014 and 2015–2023 separately** rather than scoring one static vector against the whole record.
- **Bare 5** is a placeholder for stump pits and coarse debris.
- **The tower footprint may be mixed.** A patch about 0.2 km north had its topsoil scraped off in 2006 and regrew as larch on bare pumice. Whether that patch lies in the footprint is unknown.

## Sites whose PFT fractions remain uncertain

**Least certain: use with the stated caveat and prefer the listed scenarios for sensitivity.**
- **AU-Gin:** prior only.
- **JP-Tmd:** the vector changes within the record; nothing quantitative exists after 2014.
- **AU-Cpr:** *Triodia* and bare ground are not separated.
- **JP-Tgf:** the C3/C4 split is a prior.
- **AU-DaS:** the deciduous share is unknown.

**Moderately certain**
- **AU-ASM:** woody share 65 vs 74.5.
- **AU-How:** bare is probably too high (lagoons).
- **AU-Dry, AU-Stp:** satellite complement for bare.
- **JP-Spp:** valid for 2000–2004 only.
- **JP-Tef:** *Sasa* is approximated as C3 grass.
- **JP-Fhk:** the non-larch split is assumed.
- **JP-Yms:** basal area would give about 68/32.

**Well constrained**
- AU-Cow, AU-Tum, JP-Api, JP-Fjy, JP-Khw, JP-Tak, JP-Tom.
- Each still omits its understorey.

## Time-dependent sites

| Site | Event inside the record | Vector represents |
| --- | --- | --- |
| AU-ASM | 2018–2020 mulga dieback; Mulga1 and Mulga2 are separate files | pre-dieback woodland |
| AU-Cpr | Jan 2014 fire | pre-fire mallee |
| AU-Tum | 31 Dec 2019 fire | pre-fire forest |
| AU-Gin | 2023–24 dieback; fuel-reduction burn | intact woodland |
| JP-Api | 2007 defoliation | undisturbed stand |
| JP-Fhk | thinning 2014–15 | pre-thinning, 2006–2013 |
| JP-Spp | Typhoon Songda 2004 | pre-typhoon, 2000–2004 |
| JP-Tef | clear-cut 2003 | post-clearcut, 2004–2023 |
| JP-Tmd | windthrow 2004 and natural regrowth | trajectory compromise; see above |
| JP-Tgf | mowing twice a year since 2006 | mown grassland |

## Files

| File | Contents |
| --- | --- |
| [OZ_JP_RECOMMENDED_CLM_FATES_INPUT_PFT_20261102.csv](OZ_JP_RECOMMENDED_CLM_FATES_INPUT_PFT_20261102.csv) | Master table (v1.1): vectors, basis, rationale, residual and bare policy, HOLD flags, next evidence |
| [OZ_JP_RECOMMENDED_CLM_PCT_NAT_PFT_20261102.csv](OZ_JP_RECOMMENDED_CLM_PCT_NAT_PFT_20261102.csv) | CLM host `PCT_NAT_PFT_0..14` (0 = bare) |
| [OZ_JP_RECOMMENDED_FATES_PFT_PERCENT_20261102.csv](OZ_JP_RECOMMENDED_FATES_PFT_PERCENT_20261102.csv) | FATES `pct_natland` (with bare) and `pct_vegetated_only` |
| [OZ_JP_PFT_INPUT_SENSITIVITY_SCENARIOS_20261102.csv](OZ_JP_PFT_INPUT_SENSITIVITY_SCENARIOS_20261102.csv) | Alternatives, period states and the `v1_primary_20261102` rows |
| [OZ_JP_PFT_INPUT_VALIDATION_20261102.csv](OZ_JP_PFT_INPUT_VALIDATION_20261102.csv) | Sum / live-PFT / mapping check of every primary and scenario |
| [OZ_JP_PFT_EVIDENCE_LEDGER_20261102.csv](OZ_JP_PFT_EVIDENCE_LEDGER_20261102.csv) | Evidence rows with denominator, period, scope, source and verification (`REVIEW_*` = added 2 Nov) |
| [OZ_JP_PFT_REVIEW_20261102.csv](OZ_JP_PFT_REVIEW_20261102.csv) | Per-site review: v1, verdict, operator decision, final vector, reason, sources, read status |
| [OZ_JP_RECOMMENDED_INPUT_PFT_20_SITES_20261102.md](OZ_JP_RECOMMENDED_INPUT_PFT_20_SITES_20261102.md) | v1 per-site rationale (Chinese) with the v1.1 summary table and errata; this README is authoritative |
| [scripts/apply_review_v1_1.py](scripts/apply_review_v1_1.py) | How v1.1 was derived from the sha-pinned v1 files |
| [scripts/check_recommended_inputs.py](scripts/check_recommended_inputs.py) | Standard-library consistency check |

## Validation

```bash
python3 scripts/check_recommended_inputs.py
```

The check confirms, for every primary and scenario:
- the sum is 100;
- there are at most four live PFTs;
- the DEFAULT14 host-to-FATES mapping holds;
- both FATES denominators are correct;
- the text and the numbers agree;
- the three matrices agree;
- the review's final vectors equal the master;
- every revised site keeps its v1 primary.

It checks arithmetic only. It does not check the evidence, and it does not open a FATES parameter file.

## Main sources

Read status:
- **full:** full text or data file opened.
- **second-hand:** the value was taken from another paper that cites the original.
- **snippet:** only an abstract or search excerpt was seen.

Paywalled originals that were not read: Hutley et al. 2011, Cleverly et al. 2013, Eamus et al. 2013, Leuning et al. 2005, Takagi et al. 2009, Hirano et al. 2017.

| Source | Used for | Read |
| --- | --- | --- |
| [TERN AusPlots point intercept NTABRT0001/0002](http://swarmapi.ausplots.aekos.org.au/veg_pi?site_location_name=in.%28NTABRT0001,NTABRT0002,NTABRT0003%29) | AU-ASM herb/bare split, C3/C4 (recomputed from raw hits) | full |
| [Fischer et al. 2024, bioRxiv](https://www.biorxiv.org/content/10.1101/2024.03.27.586702), Table 1 | Lidar canopy cover, AU-ASM 65 %, AU-Cpr 43 % | full (preprint) |
| [Cleverly et al. 2016, AFM 220:151](https://papers.agrivy.com/webfiles/papers/2016-AFM-JAMES-CLEVERLY.pdf), Sect. 2.1 | AU-ASM *Acacia* cover 74.5 % of land area | full |
| [Khoshravesh et al. 2020, Plant Physiol 182:566](https://academic.oup.com/plphys/article/182/1/566/6116299) | *Thyridolepis* is C3 | full |
| [Nijzink et al. 2022, HESS 26:525](https://hess.copernicus.org/articles/26/525/2022/), Table 1, pp. 530–542 | Savanna FPC definition and values | full |
| [Whitley et al. 2016, BG 13:3245](https://bg.copernicus.org/articles/13/3245/2016/), Table 1 | Savanna structure (from Hutley 2011) | full / second-hand |
| [Moore et al. 2016, BG 13:2387](https://bg.copernicus.org/articles/13/2387/2016/) | AU-How deciduous share, stems | full |
| [Bristow et al. 2016, BGD](https://bg.copernicus.org/preprints/bg-2016-191/bg-2016-191.pdf), Table 1 | AU-DaS structure | full (preprint) |
| [Pinto et al. 2014, J. Exp. Bot.](https://pmc.ncbi.nlm.nih.gov/articles/PMC4085965/), Table 2 | *Astrebla* C4 | full |
| [TERN Calperum NVIS 2012](https://portal.tern.org.au/metadata/TERN/6c9f5bdc-c800-497f-ac5b-ffae848b3d82), [species 2013](https://portal.tern.org.au/metadata/TERN/170a547c-690c-4f7c-8794-35395a9f65c6) | AU-Cpr strata, grasses | full |
| [Stephens et al. 2025, GCB](https://pmc.ncbi.nlm.nih.gov/articles/PMC12291013/), Table 1 | Structure of Gin, Tum, Cpr, ASM | full |
| [van Gorsel et al., AMS 9A.4](https://ams.confex.com/ams/pdfpapers/139191.pdf) | AU-Tum understorey LAI | full |
| [TERN Cow Bay census](https://portal.tern.org.au/metadata/TERN/ad4c0487-b6c0-463c-bbf9-4dc0c52b28ef) | AU-Cow palm share | full |
| [Ueyama et al. 2025, ESSD 17:3807](https://essd.copernicus.org/articles/17/3807/2025/), Tables 1, 3 | JapanFlux IGBP, years, disturbance | full |
| [Sano et al. 2010, FEM 260:2214](https://eprints.lib.hokudai.ac.jp/dspace/bitstream/2115/45748/12/hirano2.pdf) | JP-Tmd windthrow, salvage, early understorey | full |
| [Yazaki et al. 2016, Forests 7:287](https://eprints.lib.hokudai.ac.jp/repo/huscap/all/64380/Forests7-11_287.pdf) | JP-Tmd regrowth 2006–2014 | full (Tables S5–S6 not retrieved) |
| [CGER News, Jul 2023](https://cger.nies.go.jp/cgernews/202307/392004.html); [NIES SR-132](https://www.nies.go.jp/kanko/tokubetu/pdf/sr-132.pdf) | JP-Tmd birch dominance | full (qualitative) |
| [Aguilos et al. 2014, AFM 197:26](https://eprints.lib.hokudai.ac.jp/repo/huscap/all/57455/Aguilos_AFM2014_HUSCUP.pdf) | JP-Tef strip geometry, *Sasa* | full |
| [Sun et al. 2020, J. Agric. Meteorol. 76:119](https://www.jstage.jst.go.jp/article/agrmet/76/3/76_D-19-00026/_pdf), Table 1 | JP-Tef PAI by year | full |
| [Takahashi et al. 2015, J. Agric. Meteorol. 71:302](https://www.jstage.jst.go.jp/article/agrmet/71/4/71_D-14-00009/_pdf) | JP-Fhk basal area | full |
| [Yamanoi et al. 2015, BG 12:6837](https://bg.copernicus.org/articles/12/6837/2015/) | JP-Spp typhoon, *Sasa* | full |
| Kominami et al. 2008, AFM 148:723 | JP-Yms functional-group biomass | full |
| Shimoda et al. 2005, SOLA 1:169; Ma et al. 2018, ESSD | JP-Tgf seasonality, mowing | full |

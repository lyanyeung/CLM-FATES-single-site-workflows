# Carbon state of the 20 OzFlux / JapanFlux sites (3 Nov 2026)

**Sources.** The full rows, with quotes, locators and verification levels, are in four files:
- [carbon_stock_evidence](data/carbon_stock_evidence_20261103.csv): 159 rows;
- [disturbance_management_events](data/disturbance_management_events_20261103.csv): 102 rows;
- [published_annual_fluxes](data/published_annual_fluxes_20261103.csv): 104 rows;
- [japanflux_package_metadata](data/japanflux_package_metadata_20261103.csv): 41 rows from our own JapanFLUX2024 packages.

**Units and conventions.**
- Carbon stocks are in kg C m⁻². Dry mass is converted with 0.5 where the source gives no fraction.
- Stephens et al. (2025) biomass in t ha⁻¹ is left unconverted, because its basis (above-ground or total, dry mass or carbon) is not stated.
- NEE is in g C m⁻² yr⁻¹, with negative = sink.

## Why this matters for the model

After AD400 → NORMAL400 with fixed vegetation, the model ecosystem is close to equilibrium. Its mean NEE is near zero, apart from a small sink driven by rising CO₂ in the observation run. The published tower NEE shows how far each site is from that state:

| Class | Meaning for evaluation | Sites |
| --- | --- | --- |
| **QUASI-STEADY** (\|NEE\| ≤ ~100) | An equilibrium spin-up is a fair start. Annual NEE can be evaluated directly | AU-ASM, AU-DaS, AU-Dry, AU-Stp, AU-Cpr (pre-fire), JP-Tgf (published values conflict) |
| **AGGRADING SINK** (−200 to −900) | The model will miss most of the sink. Evaluate the diurnal and seasonal cycle, year-to-year anomalies, and GPP and ER separately. The annual sum mainly measures the equilibrium bias | AU-Cow, AU-How, AU-Tum, AU-Gin, JP-Api, JP-Fhk, JP-Fjy, JP-Khw, JP-Tak, JP-Tom, JP-Yms, JP-Spp (2000–2003) |
| **RECOVERING SOURCE** (post-disturbance) | The evaluation window itself is post-disturbance. The equilibrium soil and wood pools are structurally wrong, and the model cannot reproduce the source phase | **JP-Tef** (2004–2023) and **JP-Tmd** (2005–2023). Also JP-Spp and AU-Cpr after their disturbances, outside their windows |

**For the two recovering sites a design decision is needed later.** One option is to evaluate only the seasonal pattern. The other is a disturbance-aware start: spin up the pre-disturbance stand, then apply the documented harvest or windthrow at its date (FATES logging, or an inventory initialisation).

## Per site

| Site | Vegetation C | Soil C | Stand age / origin | Key dated events | Published annual NEE | Class |
| --- | --- | --- | --- | --- | --- | --- |
| AU-ASM | biomass 9.9 t ha⁻¹ (Stephens, basis unstated). Cleverly 2022: 2014 census USE_WITH_CAUTION, 2018 values EXCLUDED_BY_DATA_PROVIDER | — | — | low cattle grazing; drought from 2017; regional mulga dieback 2018–20 | +30 (2010–14); −259 (wet 2010–11), then −34 to +25 | quasi-steady, pulse-driven |
| AU-Cow | AGB 15.7 / 15.7 / 15.5 (2012 / 2018 / 2023, stems ≥ 10 cm) | — | old growth (undated past selective logging) | Cyclone Rona 1999-02-11; Cyclone Jasper 2023-12-13 | −240 (2009–14) | aggrading / old-growth sink |
| AU-Cpr | burnt trunks 7.2 t ha⁻¹ (2015–16); regrowth 2.1 t ha⁻¹ (2018) | — | ~35 yr since a stand-replacing fire before 2014 | sheep grazing ended 1994; wildfire 2014-01-17 | −60 (2010–14) | quasi-steady (window 2011–13) |
| AU-DaS | AGB 3.06 (Bristow 2016) | nearby OC 0.5–0.7 % | — | fire in 5 of 13 years; grazing ~0.1 head ha⁻¹; clearing from 2022-11-01 | −11 to −50 | quasi-steady (fire regime) |
| AU-Dry | biomass 31.8 t ha⁻¹ (Stephens) | — | — | fire about 1 in 8 years; grazing ~0.5 head ha⁻¹; drought 2018-11 to 2020-10 | −90 (2008–14) | quasi-steady |
| AU-Gin | biomass 52.5 t ha⁻¹ (Stephens) | — | — | fuel-reduction burns about every 20 yr; nearby wildfire 2006; burn 2016 (extent unconfirmed); dieback by 2023 | −30 (2011–14); median −284 (2012–23); −397 (2023) | aggrading after 2016 |
| AU-How | total 5.29 (AGB 3.07, roots 1.93, litter 0.10, dead stems 0.09; Chen 2003) | 15.1 (0–1 m, 3-site mean) | recovering from the 1974 cyclone (Hutley 2022) | fire in 13 of 18 years (e.g. 2012-08-19, 2013-06-07, 2014-09-12); cyclones 1896 and 1974 | −380 to −528; mean −424 (2001–19) | aggrading sink |
| AU-Stp | biomass 1.4 t ha⁻¹; standing dead 163 g m⁻² | — | — | grazing < 0.1 head ha⁻¹; fire about 1 in 16 years | −20 (2008–14) | quasi-steady |
| AU-Tum | biomass 290.6 t ha⁻¹ (Stephens), 41.2 m² ha⁻¹, 44 m | — | ~40 yr without major disturbance; managed for wood > 100 yr | thinning 1991; insects 2003; **selective logging in the footprint 2004**; partial logging NE 2006–09; fire 2019-12-31 | −510 (2001–14) | aggrading sink (managed) |
| JP-Api | 17.2 (AGB 13.8 + roots 3.35; 2012) | 11 (0–20 cm mineral; secondary) | beech 70–80 yr | beech-caterpillar defoliation 2007-07/08 | −212 to −400; mean −375 (2000–22); −88 in 2007 | aggrading sink |
| JP-Fhk | — | — | planted ~1950 | thinning 2014-05 and 2015-03 (~39 % of larch; 409 → 249 trees ha⁻¹); possible typhoon damage autumn 2009 | **conflict:** −74 (2006–13, ESSD) vs −532 (2006–09, Takahashi 2015); −433 during the thinning period | aggrading (managed) |
| JP-Fjy | — | thin litter on lava | natural red pine ~90 yr, 18–22 m | undated windthrow | −331 to −516; mean −404 | aggrading sink |
| JP-Khw | — | — | sugi ~50 yr around 2005 (planted ~1955); 22–32 m (package 10 m is the bottom of a range) | typhoon 2015-08-25 (no flux late Aug–Dec 2015) | −620 (2011–15); mean −906 (ESSD) | aggrading sink |
| JP-Spp | 12.46 (2000–03) → 8.2 after 2004 | 18 (depth unstated; secondary) | after wildfires 1874–1888 | typhoon 2004-09-08 removed 28 % of tree biomass, no salvage; snow damage 2010; gypsy moth 2014 | −375 (2000–03); +79 to +365 (2006–11) | aggrading in the 2000–03 window, then source |
| JP-Tak | woody 6.1, foliage 0.18 | > 30 (0–1 m; secondary) | abandoned coppice ~60 yr | rising birch mortality 1999–2010; typhoon 2016-09 (analyser gap to mid-Nov, filled) | −210 to −342; mean −243 (1994–2011) | aggrading (dead wood, soil) |
| **JP-Tef** | 9.9 before the cut → 0.10 larch (2009) | 15.9 (0–1 m, 2002) | larch planted 2003-10 (2500 ha⁻¹) | clear-cut 2003-01 to 03 (~2.5 removed, 5.55 of residues left); Sasa strip-cut 2003-10; weeding 2004–06 | +569 (2003), +495 (2004) → −52 (2011); "after" mean −26 | **recovering source** |
| JP-Tgf | peak AGB 886 g dry m⁻² | — (OC 4.9 % at 0–20 cm) | field built ≤ 1977 (1–2 m loam fill) | mowing once a year in winter to 2005, twice a year since 2006 (clippings left) | **conflict:** −78 to +17 (2001–03) vs mean −291 (2002–22, ESSD) | managed, near steady |
| **JP-Tmd** | AGB ~4.5 before → ~0.5 total (2014) | — | larch planted 1957–59; post-2004 birch regrowth | windthrow 2004-09-08 > 90 %; salvage removed 3.6 by 2005-08; no replanting; new tower 2019 | +421 (first 10 yr), +89 after | **recovering source** |
| JP-Tom | AGB 3.13 (landscape mean) | 5.5 (0–1 m incl. O, tower basin) | since the 1954 typhoon (~54 yr in 2008) | typhoon 2004-09-08 (tower tilted; 836 ha damaged forest-wide) | −249 to −258 | aggrading sink |
| JP-Yms | 6.39 (1999); dead wood 0.93 | 3.0 (depth unstated) | bare until ~1900; broadleaf canopy ~70 yr (2017) | pine wilt 1975–84; **oak wilt 2015–16 (~10 % of biomass died)** | −91 to −223; mean −223 (2000–23) | aggrading, disturbed from 2015 |

## Consequences already applied

| Change | Where |
| --- | --- |
| Evaluation windows and notes updated: JP-Yms split at 2015 (oak wilt); AU-Tum 2004 logging and AU-Gin 2016 burn flagged inside their windows; JP-Khw 2015 gap, JP-Tak 2016 gap and the JP-Fhk NEE conflict noted | [post-spin-up site plan](../OzFlux_JapanFlux_PostSpinup/data/OZ_JP_POST_SPINUP_SITE_PLAN_20261103.csv) |
| Site SOC stocks (AU-How, JP-Api, JP-Tak, JP-Tef, JP-Tom) drive the `ORGANIC` recommendation | [SurfaceFields](../OzFlux_JapanFlux_SurfaceFields/) |

## Gaps

- **Missing stocks.** No tree biomass for JP-Fhk, JP-Fjy or JP-Khw. No soil carbon stock for nine sites. The JP-Spp and JP-Yms soil values have no depth.
- **Pre-fire AU-Cpr biomass** is missing.
- **AU-ASM footprint mortality** is undocumented. TERN's 2025/26 census of a new plot is pending; see README.
- **Not read:** several key papers were paywalled or blocked:
  - Keith 2009, Leuning 2005 and van Gorsel 2013 (AU-Tum);
  - Eamus 2013 (AU-ASM);
  - Hutley 2011 (AU-How);
  - Jia and Akiyama 2005 (JP-Tak soil);
  - Koarashi 2009 (JP-Api soil);
  - Ohtsuka 2007 (JP-Tak);
  - Tanabe 2003 (JP-Fjy);
  - the FFPRI site NEE papers of 2012.
- **Swapped rows.** In Ueyama et al. (ESSD), the JP-Spp and JP-Tef "before" and "disturbed" NEE rows look swapped; this is flagged in the flux file.

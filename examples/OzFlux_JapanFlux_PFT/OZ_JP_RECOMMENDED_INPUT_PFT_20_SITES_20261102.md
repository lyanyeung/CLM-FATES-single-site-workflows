# OzFlux 与 JapanFlux 20 站：建议的 CLM-FATES 固定输入 PFT 百分比 v1

**2026年11月2日。** 下表为全部 20 个站点（OzFlux 9 个站点 ID、JapanFlux 11 个站点）给出了闭合到 100% 的主推荐，另有若干敏感性/时段替代方案。这是建模建议表，不是观测。格式、PFT 编号和映射沿用 `Ameriflux_Site/Ameriflux_PFT` 的 v1 约定。

适用范围：独立 cold start、`use_fates_fixed_biogeog=.true.` 且 `use_fates_nocomp=.true.`（FIXNC）。百分比是**模型自然土壤 landunit 内的面积分配，含裸地 host0**，不等于观测足迹的实测覆盖率。竞争模式不能保证保持这些面积比例。本次只写建议表，没有改动任何 surface、参数文件或作业。

> **请先读这三点**
> 1. **没有一个站点有可直接当作面积占比的实测 PFT 向量。** 向量由株数/断面积/生物量/LAI/卫星覆盖度这类分母不同的证据，经过明示的规则转换而来，每行都写了转换规则和假设。
> 2. 有 **4 个站点（AU-ASM、AU-Gin、JP-Tef、JP-Tmd）** 的主推荐主要靠先验或 LAI 代理，不要当作有证据支持的输入，见“临时先验”列。“待核对项”列只表示还有未核实的来源或未解决的差异，不等于不可用。
> 3. **裸地、草本 C3/C4 比例、林下 Sasa** 在多数站点是模型分配，不是测量值。

## 文件

- `OZ_JP_RECOMMENDED_CLM_FATES_INPUT_PFT_20261102.csv`：完整总表：比例、依据、规则、分母、HOLD 标记、待补证据
- `OZ_JP_RECOMMENDED_CLM_PCT_NAT_PFT_20261102.csv`：CLM host `PCT_NAT_PFT_0`–`14`，每站合计 100；0 为裸地
- `OZ_JP_RECOMMENDED_FATES_PFT_PERCENT_20261102.csv`：FATES 两种分母：`pct_natland`（含 bare 合计 100）与 `pct_vegetated_only`（自身合计 100）
- `OZ_JP_PFT_INPUT_SENSITIVITY_SCENARIOS_20261102.csv`：敏感性/时段替代方案
- `OZ_JP_PFT_INPUT_VALIDATION_20261102.csv`：每行合计 100、活体 PFT≤4、DEFAULT14 往返映射核对
- `OZ_JP_PFT_EVIDENCE_LEDGER_20261102.csv`：证据台账：67 条，含分母、年份、空间范围、来源链接和核实状态

## 20 站主推荐（%）

`TropEBT`=FATES1 热带常绿阔叶树；`ENF`=FATES2 常绿针叶树；`DNF`=FATES3 落叶针叶树；`EBT`=FATES4 温带常绿阔叶树；`HydrodecidTropTree`=FATES5 热带干旱落叶阔叶树；`DBF`=FATES6 冷落叶阔叶树；`EvergreenShrub`=FATES7；`CoolC3`=FATES13；`C4`=FATES14。所有站点使用 DEFAULT14 映射，无需站点独立参数映射。`bare` 为模型裸地分配。

| 网络 | 站点 | 建议百分比：自然土壤面积，含 bare | 依据类型 | 不确定性 | 临时先验 | 待核对项 |
| --- | --- | --- | --- | --- | --- | --- |
| OzFlux | AU-ASM | EBT 43 / C4 22 / bare 35 | LAI_SHARE_PROXY_PLUS_MODEL_SURFACE_BARE_PRIOR | 高 | 是 | 有 |
| OzFlux | AU-Cow | TropEBT 100 | STAND_FUNCTIONAL_PROXY | 低 | 否 | 无 |
| OzFlux | AU-Cpr | EBT 33 / EvergreenShrub 10 / C4 3 / bare 54 | NVIS_STRATUM_COVER_PROXY | 高 | 否 | 有 |
| OzFlux | AU-DaS | TropEBT 30 / HydrodecidTropTree 7.5 / C4 42.5 / bare 20 | PUBLISHED_MODEL_COVER_PRECEDENT_PLUS_EXPLICIT_TREE_SPLIT | 高 | 否 | 有 |
| OzFlux | AU-Dry | TropEBT 26.6 / C4 49.4 / bare 24 | PUBLISHED_MODEL_COVER_PRECEDENT | 高 | 否 | 有 |
| OzFlux | AU-How | TropEBT 31.8 / HydrodecidTropTree 8 / C4 44.3 / bare 15.9 | BASAL_AREA_SPLIT_OF_SATELLITE_TREE_COVER | 中 | 否 | 有 |
| OzFlux | AU-Gin | EBT 45 / EvergreenShrub 35 / bare 20 | EXPLICIT_PRIOR_NO_COVER_DATA | 高 | 是 | 有 |
| OzFlux | AU-Stp | C4 65 / bare 35 | PUBLISHED_MODEL_COVER_PRECEDENT | 中 | 否 | 有 |
| OzFlux | AU-Tum | EBT 100 | DOMINANT_FOREST_PROXY | 中 | 否 | 有 |
| JapanFlux | JP-Api | DBF 100 | DOMINANT_FOREST_PROXY | 低 | 否 | 无 |
| JapanFlux | JP-Fhk | DNF 84.6 / ENF 7.7 / DBF 7.7 | EXPLICIT_NORMALIZED_BASAL_AREA_PROXY | 中 | 否 | 有 |
| JapanFlux | JP-Fjy | ENF 100 | DOMINANT_FOREST_PROXY | 中 | 否 | 无 |
| JapanFlux | JP-Khw | ENF 100 | STAND_FUNCTIONAL_PROXY | 低 | 否 | 无 |
| JapanFlux | JP-Spp | DBF 100 | STAND_FUNCTIONAL_PROXY | 低 | 否 | 有 |
| JapanFlux | JP-Tak | DBF 100 | STAND_FUNCTIONAL_PROXY | 低 | 否 | 有 |
| JapanFlux | JP-Tef | DNF 100 | PLANTATION_FUNCTIONAL_PROXY | 高 | 是 | 有 |
| JapanFlux | JP-Tmd | DBF 19 / CoolC3 81 | LAI_SHARE_PROXY | 高 | 是 | 有 |
| JapanFlux | JP-Tom | DBF 100 | DOMINANT_FOREST_PROXY | 中 | 否 | 有 |
| JapanFlux | JP-Tgf | CoolC3 40 / C4 60 | EXPLICIT_C3_C4_PRIOR | 高 | 否 | 有 |
| JapanFlux | JP-Yms | DBF 72 / EBT 28 | EXPLICIT_BIOMASS_SHARE_PROXY | 中 | 否 | 有 |

## 解读时最重要的几点

1. **转换规则按站点类型固定，不是逐站拍脑袋。** 森林：用断面积（或生物量）归一化的功能型份额，裸地 0，林下省略（沿用 AmeriFlux 森林约定）。热带稀树草原（AU-How/DaS/Dry）：用 Nijzink 等 2022 的卫星树/草覆盖度，裸地取其补数，再用已知的常绿/落叶树比例拆分树覆盖。草地（AU-Stp、JP-Tgf）：C4/C3 取证据支持的倾向，其余为先验。
2. **卫星覆盖度不是足迹实测。** AU-DaS、AU-Dry、AU-How、AU-Stp 的覆盖度来自 fPAR 投影覆盖（树=月最小覆盖，草=最大覆盖减树）。它们的补数当作 bare 是模型分配，不能写成实测裸地。
3. **常绿/落叶树的拆分是区域先验。** AU-DaS 与 AU-Dry 借用 Howard Springs 的断面积比 80:20；DaS 按株数则偏落叶，已作为替代方案给出。
4. **LAI 份额代理（AU-ASM、JP-Tef、JP-Tmd）不是面积。** 它只在缺少面积数据时作为明示的代理，对应替代方案同时给出。
5. **Sasa（矮竹）林下**在 JP-Spp/Tak/Tef/Tom 是常绿 C3 禾本代理，但 FIXNC 的互斥 patch 会挤占树面积。主推荐省略，替代方案中 25% 的 CoolC3 是占位值，不是测量。
6. **固定状态不重建扰动历史。** AU-Cpr（2014 火）、AU-Tum（2019 火）、JP-Fhk（2014–15 间伐）、JP-Spp（2004 台风）、JP-Tef（2003 皆伐）、JP-Tmd（2004 台风）、AU-ASM（2018–20 枯死）的主推荐只代表表中写明的时段，用完整 release 年份的气象驱动它们只能称为固定状态实验。
7. **HLM 映射。** 20 站全部落在 DEFAULT14 的一对一行上（host4→FATES1，host1→2，host3→3，host5→4，host6→5，host7→6，host9→7，host13→13，host14→14）。FATES5 通过 host6 到达；FATES8 与 host10→FATES9 的问题不涉及。每站活体 PFT 不超过默认 4 类上限。

## 需要你决定的事项

1. **模式**：AU-How 已有的成功 case 是 Full FATES 竞争（`fixed_biogeog=.false.`），与本表的 FIXNC 假设不同。这 20 站要全部走 FIXNC，还是 AU-How 保持竞争对照？
2. **AU-ASM mulga**：主推荐用 FATES4（Stage21 的首选工作候选）；默认 FATES7 高度上限 4.735 m 低于 26% 的 2014 年 Acacia 茎，所以 FATES7 只作敏感性。是否同意？
3. **热带稀树草原的 bare**：How/DaS/Dry 的 bare 是卫星覆盖补数。是否接受，还是改为 0 并另做对照？
4. **Sasa 林下**：是否在 JP 落叶林里用 CoolC3 占位，还是保持树单一 PFT？

## 每站决策与证据

### AU-ASM — EBT 43 / C4 22 / bare 35

站点：Alice Springs Mulga；IGBP 来源：SAV (FLUXNET); NVIS Acacia shrublands。
目标状态：Mulga woodland, pre-dieback reference；时段：Mulga1 2010-2023 and Mulga2 2024-2026 are separate files; dieback 2018-2020 not represented。

**依据与规则：** Evergreen Acacia aneura/A. aptaneura canopy -> FATES4 (Stage21 first working candidate; FATES7 kept as sensitivity). Vegetated area 65 is split woody:herb 66:34 from simulated overstory:understory LAI 0.25:0.13 (Chen 2014). Herb layer set to C4 because the L6 list has C4 perennial+annual grasses and the reference host surface is C4-dominated (20.9% C4 vs 0.04% C3).

**余项处理：** Woody:herb split is an LAI proxy, not a measured area split. C3 grass/forbs/shrubs listed in L6 are lumped into C4 in the primary; mixed scenario provided.
**裸地：** Bare 35 is taken from the Stage17 reference host surface (34.9% host0), a model-surface value, not a field measurement. No measured bare fraction found.
**原证据分母：** Basal area 7.0-8 m2/ha (1 ha core); simulated LAI overstory 0.25 / understory 0.13; '74% woody cover' denominator unclear and NOT used
**不确定性：** 高；证据等级：NUMERIC_STRUCTURE_COVER_UNRESOLVED。
**HOLD：** Mulga PFT4 vs PFT7, bare and woody:herb split and soil are not approved by Stage21-22; 27/103 Acacia stems exceed the FATES7 height cap 4.735 m
**待补证据：** Obtain TERN cover transect or Cleverly 2013 site table for woody/grass/bare ground cover; reconcile canopy_height 4.4 vs 6.5 vs 8.1 m.

替代方案：
- `mulga_as_shrub_FATES7`：EvergreenShrub 43 / C4 22 / bare 35。Evergreen shrub structure sensitivity; default FATES7 height cap 4.735 m is below 26% of 2014 Acacia stems.
- `mixed_C3_C4_herb`：EBT 43 / CoolC3 8 / C4 14 / bare 35。Splits herb 22 into C3 8 / C4 14 only as a trait sensitivity; the split is not measured.

证据要点（完整见证据台账）：
- species/life forms：Acacia aneura, A. aptaneura; C3 forbs/shrubs; C3 grass Thyridolepis mitchelliana; C4 Eragrostis eriopoda, Eriachne pulchella（qualitative；footprint；核实：REPO+AGENT_READ）[来源](https://object-store.rc.nectar.org.au/v1/AUTH_05bca33fce34447ba7033b9305947f11/data_submission_tool_attachments/6a03ff13-aa13-43b3-abe3-64e48e0649d8/Alice_Mulga_soil_description.pdf)
- basal area：7.0 (Stephens) / 8 (TERN) m2/ha（1 ha core plot; definition in Table S1 not read；1 ha；核实：AGENT_READ）[来源](https://pmc.ncbi.nlm.nih.gov/articles/PMC12291013/)
- LAI overstory / understory (simulated)：0.25 (0.12-0.35) / 0.13 (0.07-0.21)（simulated LAI, not cover；tower；核实：AGENT_READ）[来源](https://papers.agrivy.com/webfiles/papers/2014-JOH-CHEN-CHAO.pdf)
- 'woody cover' Mulga：74%（denominator unclear (research-site Acacia cover); NOT used；unclear；核实：SECONDARY）[来源](https://www.ozflux.org.au/events/september2014/monday/1_Cleverly.pdf)
- canopy height：4.4 (L6 2026_v3) / 6.5 (OzFlux page) / 8.1 (Stephens) m（various；tower；核实：REPO+AGENT_READ）[来源](https://www.ozflux.org.au/monitoringsites/alicesprings/alicesprings_description.html)
- reference host surface：bare 34.886, host4 0.840, host5 1.735, host7 0.027, host10 41.586, host13 0.041, host14 20.886 %（gridded CTSM surface, model not field；grid cell；核实：REPO）[来源](https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/examples/OzFlux_MultiSite_09)
- stems above FATES7 height cap：27/103 Acacia stems (26.2%) exceed 4.7354 m（unique stem IDs, 2014 field heights；1 ha stem survey；核实：REPO）[来源](https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/examples/OzFlux_MultiSite_09)
- dieback：regional mulga dieback Aug 2020; footprint mortality not found（qualitative；regional；核实：AGENT_READ）[来源](https://www.tern.org.au/news/site-of-the-month-alice-mulga-supersite/)

### AU-Cow — TropEBT 100

站点：Cow Bay (Daintree)；IGBP 来源：EBF。
目标状态：Intact complex mesophyll vine forest；时段：Census 2012, 2018, 2023; Cyclone Jasper (Dec 2023) not represented。

**依据与规则：** Evergreen broadleaf tropical rainforest; 1 ha census (>=10 cm DBH) is stable across 2012-2023 (BA 34.1-34.5 m2/ha). All dominant families are evergreen broadleaf -> FATES1.

**余项处理：** Palms (~19% of stems, ~2% of biomass) have no separate PFT and are folded into TropEBT. Understory and ground layer not quantified.
**裸地：** Model convention bare=0; no independent zero-bare measurement.
**原证据分母：** 1 ha core plot, live stems >=10 cm DBH; derived from TERN CSV, not a published table
**不确定性：** 低；证据等级：NUMERIC_CENSUS_FUNCTIONAL_PROXY。
**待补证据：** Peer-reviewed LAI and understory cover; cyclone canopy impact at the tower.

证据要点（完整见证据台账）：
- stems / basal area / biomass：659 stems, 34.1 m2/ha, 314.6 t/ha (2012); 613 stems, 34.1, 310.1 (2023)（1 ha, live stems >=10 cm DBH; derived from TERN CSV；1 ha core；核实：AGENT_READ+DERIVED）[来源](https://portal.tern.org.au/metadata/TERN/ad4c0487-b6c0-463c-bbf9-4dc0c52b28ef)
- family basal-area shares (2023)：Meliaceae 26, Lauraceae 12, Arecaceae 9, Fabaceae 6, Euphorbiaceae 6 %（basal area；1 ha；核实：AGENT_READ+DERIVED）[来源](https://portal.tern.org.au/metadata/TERN/ad4c0487-b6c0-463c-bbf9-4dc0c52b28ef)
- canopy height：22-26 m（various；tower；核实：AGENT_READ）[来源](https://ozflux.org.au/monitoringsites/cowbay/cowbay_description.html)

### AU-Cpr — EBT 33 / EvergreenShrub 10 / C4 3 / bare 54

站点：Calperum (mallee)；IGBP 来源：SAV (FLUXNET); closed shrubland in GMD 2018。
目标状态：Pre-fire mallee (before 17 Jan 2014)；时段：2012 strata survey; 2014 fire and regrowth separate。

**依据与规则：** Upper-stratum tree mallee 33.4% -> FATES4 33. Chenopod 6.0 + shrub 4.4 = 10.4 -> evergreen shrub FATES7 10. Tussock grass 2.3 + forb 0.9 = 3.2 -> C4 proxy 3 (lumped). Strata overlap so they are not a simplex.

**余项处理：** Residual 54 is assigned to bare as a model allocation; it contains unlisted Triodia hummock grass, litter and crust and is NOT measured bare ground.
**裸地：** Bare 54 = 100 minus listed strata cover; not a survey.
**原证据分母：** TERN NVIS strata cover, 1 ha, 23 Sep 2012; coverType NA, denominator unspecified; Stephens 2025 BA 4.3 m2/ha appears to be post-fire trunks
**不确定性：** 高；证据等级：NUMERIC_STRATA_COVER_DENOMINATOR_UNSPECIFIED。
**HOLD：** Post-fire regrowth state (2014-2018 stems ~6300/ha, 1.9 m) is not represented
**待补证据：** Confirm NVIS cover denominator with TERN; Triodia cover; whether the ALS-paper study area is the tower stand.

替代方案：
- `mallee_as_shrub_FATES7`：EvergreenShrub 43 / C4 3 / bare 54。Treats multistem mallee (3.9 m) as evergreen shrub; FATES7 height cap 4.735 m.
- `tree_only`：EBT 33 / bare 67。Only the measured upper stratum cover is kept.

证据要点（完整见证据台账）：
- strata cover：tree mallee 33.4, chenopod 6.0, shrub 4.4, tussock grass 2.3, forb 0.9 %（NVIS stratum cover; coverType NA; strata overlap；1 ha core；核实：AGENT_READ）[来源](https://shared.tern.org.au/attachment/6c9f5bdc-c800-497f-ac5b-ffae848b3d82/Calperum_Mallee_vegetation_structure_data_YUCbM0R.csv)
- canopy cover：54 +/- 24 %（ground-based, 1 ha reference; study area ~30 km from tower；1 ha；核实：AGENT_READ）[来源](https://link.springer.com/article/10.1007/s10666-023-09896-z)
- basal area / biomass / height：4.3 m2/ha / 7.2 t/ha / 3.9 m（likely post-fire standing trunks；site；核实：AGENT_READ）[来源](https://pmc.ncbi.nlm.nih.gov/articles/PMC12291013/)
- fire：17 Jan 2014, severe patchy; 2018 regrowth ~6317 stems/ha, 1.9 m（stem survey；site；核实：AGENT_READ）[来源](https://bg.copernicus.org/articles/13/5895/2016/bg-13-5895-2016.pdf)

### AU-DaS — TropEBT 30 / HydrodecidTropTree 7.5 / C4 42.5 / bare 20

站点：Daly River Uncleared；IGBP 来源：SAV。
目标状态：Uncleared eucalypt savanna；时段：~2008 plot survey reference; release 2008-2026。

**依据与规则：** Tree cover 37.5 and max grass cover 42.5 from Nijzink 2022 (fPAR projective cover); bare 20.0 = 100 minus tree minus grass. Tree cover split 80:20 evergreen eucalypt (FATES1) : semi/deciduous (FATES5) borrowed from the Howard Springs basal-area ratio (Hutley 2001), because DaS stems are 36% evergreen eucalypts, similar to How (~40%).

**余项处理：** The 80:20 split is a regional prior, not a DaS basal-area measurement. Understory is C4 (Sorghum, Heteropogon).
**裸地：** Bare 20 is the complement of satellite cover, a model allocation; no field bare fraction found.
**原证据分母：** Tree cover = minimum monthly projective cover (AVHRR fPAR/0.95); 2008 plot BA 9.38 m2/ha, 292 stems/ha, LAI 0.72
**不确定性：** 高；证据等级：REMOTE_SENSING_COVER_PLUS_STEM_SURVEY。
**HOLD：** Hutley 2011 plot table not read; FLUXNET page wrongly says cleared savanna
**待补证据：** Read Hutley 2011 site table for BA by species; confirm leaf habit of T. grandiflora at the site.

替代方案：
- `stem_based_split`：TropEBT 13.5 / HydrodecidTropTree 24 / C4 42.5 / bare 20。Uses stems (36% evergreen of 214 listed) rather than basal area; probably over-weights deciduous trees.
- `all_evergreen_tree`：TropEBT 37.5 / C4 42.5 / bare 20。All trees TropEBT.

证据要点（完整见证据台账）：
- stems/BA/LAI：292 stems/ha (330 total), BA 9.38 m2/ha, LAI 0.72 (0.41 over / 0.31 under), mean height 8.23 m（1 ha SPECIAL survey；1 ha；核实：SECONDARY）[来源](https://www.ozflux.org.au/events/jun2009/ozflux2009_beringer.pdf)
- stem counts/ha by species：T. grandiflora 94, E. tetrodonta 47, Erythrophleum 29, Corymbia latifolia 18, Planchonia 14, E. miniata 12（stems；1 ha；核实：SECONDARY）[来源](https://www.ozflux.org.au/events/jun2009/ozflux2009_beringer.pdf)
- satellite cover：tree 37.5 %, max grass 42.5 %（min monthly projective cover (fPAR/0.95); grass = max cover - tree；site；核实：AGENT_READ）[来源](https://hess.copernicus.org/articles/26/525/2022/hess-26-525-2022.pdf)

### AU-Dry — TropEBT 26.6 / C4 49.4 / bare 24

站点：Dry River；IGBP 来源：SAV。
目标状态：Open-forest savanna；时段：Long-term remote-sensing cover; release 2009-2026。

**依据与规则：** Tree cover 26.6 and max grass 49.4 (Nijzink 2022); bare 24.0 by complement. Overstory E. tetrodonta, E. dichromophloia, C. terminalis are evergreen -> FATES1. Understory Sorghum/Themeda/Chrysopogon -> C4.

**余项处理：** No deciduous trees are named in any source; C4 status is inferred from genus, not stated for this site.
**裸地：** Bare 24 is the complement of satellite cover.
**原证据分母：** Minimum monthly projective cover (tree) and max cover minus tree (grass), fPAR; no plot survey found
**不确定性：** 高；证据等级：REMOTE_SENSING_COVER_ONLY。
**HOLD：** No stem/basal-area/LAI table found
**待补证据：** Locate the Dry River row of the Hutley 2011 site table; any ground-based cover survey.

替代方案：
- `How_like_deciduous_share`：TropEBT 21.3 / HydrodecidTropTree 5.3 / C4 49.4 / bare 24。Applies the Howard Springs 80:20 evergreen:deciduous prior to the tree cover.

证据要点（完整见证据台账）：
- satellite cover：tree 26.6 %, max grass 49.4 %（same as above；site；核实：AGENT_READ）[来源](https://hess.copernicus.org/articles/26/525/2022/hess-26-525-2022.pdf)
- species：E. tetrodonta, E. dichromophloia, Corymbia terminalis; Sorghum, Themeda, Chrysopogon（qualitative; C4 by genus inference；site；核实：AGENT_READ）[来源](https://ozflux.org.au/monitoringsites/dryriver/dryriver_description.html)

### AU-How — TropEBT 31.8 / HydrodecidTropTree 8 / C4 44.3 / bare 15.9

站点：Howard Springs；IGBP 来源：WSA。
目标状态：Eucalypt open-forest savanna, fire every 1-3 yr；时段：Release 2001-2025; ~2008 plot survey。

**依据与规则：** Tree cover 39.8 and max grass 44.3 (Nijzink 2022); bare 15.9 by complement. Tree cover split by Hutley 2001 evergreen-eucalypt basal-area share ~80% -> FATES1 31.8, semi/deciduous Erythrophleum/Terminalia -> FATES5 8.0. Understory annual+perennial C4 grass.

**余项处理：** Applies a basal-area share to a satellite cover; the two denominators differ.
**裸地：** Bare 15.9 is the complement of satellite cover, not measured.
**原证据分母：** 661 stems/ha, BA 9.66 m2/ha (~2008, 1 ha); ground canopy cover ~50% (1998-99); satellite tree 39.8 / grass 44.3
**不确定性：** 中；证据等级：NUMERIC_BA_SHARE_PLUS_REMOTE_SENSING_COVER。
**HOLD：** Existing AU-How case used Full FATES competition with the default 16-PFT surface; this fixed vector is a separate experiment
**待补证据：** Read Hutley 2011 plot table; confirm the 2008 survey values at source.

替代方案：
- `Shi2025_model_precedent`：TropEBT 50 / ColdDecidShrub 25 / C4 25。Shi et al. 2025 EBT/DBS/C4 = 50/25/25; the deciduous-shrub mapping is a model choice, not an observation.
- `ground_canopy_cover_50`：TropEBT 40 / HydrodecidTropTree 10 / C4 50。Tree 50 (80:20 split), grass 50, bare 0; overlapping strata are collapsed.

证据要点（完整见证据台账）：
- stems/BA：661 stems/ha (684 all), BA 9.66 m2/ha（1 ha SPECIAL survey；1 ha；核实：SECONDARY）[来源](https://www.ozflux.org.au/events/jun2009/ozflux2009_beringer.pdf)
- evergreen eucalypt share：~80 % of overstory basal area（basal area；plot；核实：AGENT_READ）[来源](https://opus.lib.uts.edu.au/bitstream/10453/3660/3/2004004637.pdf)
- canopy cover：~50 % (ground); 50-60 %（ground canopy cover；site；核实：AGENT_READ）[来源](https://bg.copernicus.org/articles/13/2387/2016/bg-13-2387-2016.pdf)
- satellite cover：tree 39.8 %, max grass 44.3 %（fPAR projective cover；site；核实：AGENT_READ）[来源](https://hess.copernicus.org/articles/26/525/2022/hess-26-525-2022.pdf)
- LAI：over 0.9 wet / 0.6 dry; under 0.8 wet / 0.02 dry（LAI；site；核实：AGENT_READ）[来源](https://opus.lib.uts.edu.au/bitstream/10453/3660/3/2004004637.pdf)
- model PFT precedent：EBT/DBS/C4 = 50/25/25（model input, denominator undefined；site；核实：AGENT_READ）[来源](https://essd.copernicus.org/articles/17/117/2025/essd-17-117-2025.pdf)
- fire：every 1-3 yr（qualitative；site；核实：AGENT_READ）[来源](https://bg.copernicus.org/articles/13/2387/2016/bg-13-2387-2016.pdf)

### AU-Gin — EBT 45 / EvergreenShrub 35 / bare 20

站点：Gingin (banksia woodland)；IGBP 来源：WSA。
目标状态：Banksia woodland；时段：Release record; 2023-24 dieback and a fuel-reduction burn not represented。

**依据与规则：** Banksia menziesii/attenuata/grandis overstory (~7 m, evergreen sclerophyll) -> FATES4; diverse sclerophyll shrub understory -> FATES7. Tree 45 is the IGBP woody-savanna mid-range (30-60% tree cover), shrub 35 and bare 20 are priors.

**余项处理：** No cover, basal-area or stem data exist in the sources read; the three values are assumptions.
**裸地：** Bare 20 is a prior for sandy podosol; not measured.
**原证据分母：** Site-page structure only: canopy ~7 m, overstory LAI ~0.8; MODIS LAI 0.9
**不确定性：** 高；证据等级：QUALITATIVE_ONLY。
**HOLD：** PROVISIONAL: no composition numbers; do not treat as evidence-based
**待补证据：** TERN surveillance plots / Groom 2004 cover or stem data; fuel-reduction burn date.

替代方案：
- `tree_only`：EBT 100。Overstory-only forest convention.
- `shrub_heavy`：EBT 30 / EvergreenShrub 50 / bare 20。Understory shrub dominance sensitivity.

证据要点（完整见证据台账）：
- species/structure：Banksia menziesii/attenuata/grandis; canopy ~7 m, overstory LAI ~0.8; >99 understory species（qualitative + site page；site；核实：AGENT_READ）[来源](https://www.ozflux.org.au/monitoringsites/gingin/gingin_description.html)
- disturbance：fuel-reduction burn (date not found); 2023-24 canopy dieback patches（qualitative；site；核实：AGENT_READ）[来源](https://doi.org/10.1088/1748-9326/adb6c1)

### AU-Stp — C4 65 / bare 35

站点：Sturt Plains (Mitchell grass)；IGBP 来源：GRA。
目标状态：Natural Mitchell grassland；时段：Long-term satellite cover; lightly grazed, frequent low-intensity fires。

**依据与规则：** Text says no perennial overstory; Nijzink 2022 gives tree 7.4 and max grass 57.6, total max projective cover 65.0. The 7.4 persistent cover is read as perennial tussock, so C4 65 / bare 35.

**余项处理：** Astrebla = C4 is inferred from genus; no fetched source states it.
**裸地：** Bare 35 = 100 minus max projective cover; not field bare ground.
**原证据分母：** fPAR projective cover (Donohue 2013 basis); harvest live 0.00 / dead 163 g/m2 date unknown
**不确定性：** 中；证据等级：REMOTE_SENSING_COVER_ONLY。
**HOLD：** Satellite 'tree 7.4' conflicts with the written description
**待补证据：** Hutley 2011 / Verma 2017 for grass height and C4 status; harvest date.

替代方案：
- `literal_max_grass`：C4 57.6 / bare 42.4。Uses max grass cover only and treats the 7.4 persistent cover as bare.
- `full_cover`：C4 100。Bare 0 convention.

证据要点（完整见证据台账）：
- satellite cover：tree 7.4 %, max grass 57.6 %（fPAR projective cover；site；核实：AGENT_READ）[来源](https://hess.copernicus.org/articles/26/525/2022/hess-26-525-2022.pdf)
- vegetation：Astrebla Mitchell grassland, no perennial overstory; harvest live 0.00 / dead 163.42 g/m2（qualitative; harvest date unknown；site；核实：AGENT_READ）[来源](https://portal.tern.org.au/metadata/059746ef-6e37-4d17-8428-b22bd620c913)

### AU-Tum — EBT 100

站点：Tumbarumba；IGBP 来源：EBF。
目标状态：Pre-fire wet sclerophyll eucalypt forest；时段：Tumbarumba 1 (2002-2022); 31 Dec 2019 fire killed nearly all alpine ash。

**依据与规则：** E. delegatensis and E. dalrympleana, ~40 m evergreen broadleaf -> FATES4. No understory or grass numbers found.

**余项处理：** Understory present but not quantified and omitted (forest convention).
**裸地：** Model convention bare=0.
**原证据分母：** Qualitative; canopy ~40 m; in-situ LAI ~2.4 (MODIS 4.1 over-estimates)
**不确定性：** 中；证据等级：QUALITATIVE_DOMINANT_TYPE。
**HOLD：** Which tower/period the local L6 covers (Tum1 vs Tum2) is unconfirmed
**待补证据：** Leuning 2005 Sect. 2 for stem density/basal area; understory species.

证据要点（完整见证据台账）：
- species/structure：E. delegatensis, E. dalrympleana; ~40 m; in-situ LAI ~2.4 (MODIS 4.1)（qualitative；site；核实：AGENT_READ）[来源](https://doi.org/10.5194/gmd-9-223-2016)
- fire：31 Dec 2019 fire killed nearly all alpine ash; mountain gum resprouting（TERN release text；site；核实：AGENT_READ）[来源](https://researchdata.edu.au/tumbarumba-1-fluxnet-release-2026r1/4014617)

### JP-Api — DBF 100

站点：Appi；IGBP 来源：DBF。
目标状态：Beech secondary forest；时段：2000-2022; 2007 beech caterpillar defoliation not represented。

**依据与规则：** Nearly pure Fagus crenata, consistent across five sources -> FATES6.

**余项处理：** No species shares found; understory not listed.
**裸地：** Model convention bare=0.
**原证据分母：** Qualitative; LAI max 4.8 (2000-2006), canopy ~20 m
**不确定性：** 低；证据等级：QUALITATIVE_DOMINANT_TYPE。
**待补证据：** Stem/basal-area table from FFPRI plot data; outbreak year in JapanFlux2024.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：DBF 40.0014N 140.9366E 831 m（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- species/structure：Fagus crenata nearly pure; canopy ~20 m; max LAI 4.8; 70-80 yr（qualitative；site；核实：AGENT_READ）[来源](https://www2.ffpri.go.jp/labs/flux/data/API_2006_003a.pdf)
- outbreak：beech caterpillar defoliation 25 Jul-7 Aug 2007; damage fraction not given（qualitative；site；核实：AGENT_READ）[来源](https://www.ffpri.go.jp/thk/research/publication/thk/documents/fw_032_01-02.pdf)

### JP-Fhk — DNF 84.6 / ENF 7.7 / DBF 7.7

站点：Fuji Hokuroku；IGBP 来源：DNF。
目标状态：Pre-thinning larch plantation；时段：2006-2013 (thinning May 2014 and Mar 2015 not represented)。

**依据与规则：** Larix kaempferi 30.3 of 35.8 m2/ha total basal area (84.6%, 2010) -> FATES3. The 15.4% non-larch basal area (Pinus densiflora, Abies homolepis evergreen needleleaf; Quercus, Swida, Betula deciduous broadleaf) is split equally ENF/DBF because the source lists both groups without shares.

**余项处理：** Equal ENF/DBF split of the 15.4% non-larch share is an assumption.
**裸地：** Model convention bare=0; fern understory omitted.
**原证据分母：** 2010 tree basal area and stems (369/423 larch); Takahashi 2015 Sect. 2.1 (not re-opened this session)
**不确定性：** 中；证据等级：NUMERIC_BASAL_AREA。
**HOLD：** Takahashi 2015 numbers not independently re-verified
**待补证据：** Re-open Takahashi 2015 Sect. 2.1 to confirm; Teramoto 2019 Table 1 for post-thinning shares.

替代方案：
- `larch_only`：DNF 100。Dominant-type proxy.
- `stem_share`：DNF 87.2 / ENF 6.4 / DBF 6.4。Larch stem share 369/423 = 87.2%.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：DNF 35.4436N 138.7647E 1100 m; thinning（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- larch stems and basal area：369 of ~423 stems/ha (~87%, derived); 30.3 of ~35.8 m2/ha (~85%, derived)（all overstory stems / total basal area；stand；核实：AGENT_READ+DERIVED (not reopened: allowlist)）[来源](https://www.jstage.jst.go.jp/article/agrmet/71/4/71_D-14-00009/_pdf)
- other species：Pinus densiflora, Abies homolepis (evergreen needleleaf); Swida, Quercus serrata, Q. crispula, Betula platyphylla (deciduous broadleaf); shares not given（qualitative；stand；核实：AGENT_READ）[来源](https://www.jstage.jst.go.jp/article/agrmet/71/4/71_D-14-00009/_pdf)
- thinning：May 2014 and Mar 2015; stems 409 -> 249/ha (-39%)（stems/ha；stand；核实：AGENT_READ）[来源](https://db.cger.nies.go.jp/nies_data/10.17595/20210730.001/supplement/SiIn_FHK_2013-2023_03.pdf)

### JP-Fjy — ENF 100

站点：Fujiyoshida；IGBP 来源：ENF。
目标状态：Naturally regenerated red pine stand on lava；时段：2000-2021。

**依据与规则：** Pinus densiflora (~90 yr, ~20 m) overstory -> FATES2. NOT a larch site (larch is JP-Fhk).

**余项处理：** Ilex pedunculosa lower layer (evergreen broadleaf) and oaks are unquantified and omitted; no basal-area or stem data found.
**裸地：** Model convention bare=0.
**原证据分母：** Qualitative; PAI ~3-5
**不确定性：** 中；证据等级：QUALITATIVE_DOMINANT_TYPE。
**待补证据：** Ohtsuka 2013, Tanabe 2003, Okano & Arase 2007 for stand structure; whether Tanabe stand = tower stand.

替代方案：
- `ilex_lower_layer_prior`：ENF 80 / EBT 20。Placeholder for the Ilex lower layer; the 20 is NOT measured.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：ENF 35.4545N 138.7623E 1043 m（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- stand：Pinus densiflora ~90 yr, ~20 m, PAI ~3-5; Ilex pedunculosa lower layer（qualitative；stand；核实：AGENT_READ）[来源](https://www.zobodat.at/pdf/PHY_45_4_0073-0080.pdf)

### JP-Khw — ENF 100

站点：Kahoku Experiment Watershed；IGBP 来源：ENF。
目标状态：Sugi/hinoki plantation；时段：2000-2003 and 2007-2021 per ESSD Table 1。

**依据与规则：** Cryptomeria japonica and Chamaecyparis obtusa are both evergreen needleleaf, so the unknown sugi:hinoki ratio does not change the PFT -> FATES2.

**余项处理：** Gap broadleaf trees and evergreen Quercus/Castanopsis understory are unquantified and omitted.
**裸地：** Model convention bare=0.
**原证据分母：** Sugi plots only: 1575 and 904 trees/ha; BA 71.7 and 118.7 m2/ha; 318-321 m2 plots (plot scale)
**不确定性：** 低；证据等级：NUMERIC_PLOT_FUNCTIONAL_IDENTITY。
**待补证据：** Check 2004-2006 rows in local release; broadleaf share in footprint.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：ENF 33.1366N 130.7083E 196 m; 2000-2003, 2007-2021（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- sugi plot structure：1575 trees/ha, BA 71.7 m2/ha (upper); 904 trees/ha, BA 118.7 m2/ha (lower)（plots of 318-321 m2, sugi only；plot；核实：AGENT_READ）[来源](http://www.forest.kyushu-u.ac.jp/staff/kumagai/agfm0801.pdf)
- stand composition：Cryptomeria japonica ~50 yr main; Chamaecyparis obtusa 27-50 yr; no area shares（qualitative；stand；核实：AGENT_READ）[来源](http://www.forest.kyushu-u.ac.jp/staff/kumagai/tp0601.pdf)

### JP-Spp — DBF 100

站点：Sapporo；IGBP 来源：DBF。
目标状态：Pre-typhoon birch-oak secondary forest；时段：2000-2003 (Typhoon Songda 8 Sep 2004 damaged 40% of trees; not represented)。

**依据与规则：** Birch+oak >75% of 2003 basal area; birch 51.6% and oak 33.5% of biomass; other canopy species (Kalopanax, Acer mono, Tilia) are also deciduous broadleaf -> FATES6.

**余项处理：** Sasa understory (evergreen dwarf bamboo, LAI to 4.05 after typhoon) omitted in the primary.
**裸地：** Model convention bare=0.
**原证据分母：** 672 stems/ha (DBH>5 cm, 2003); biomass shares pre-disturbance
**不确定性：** 低；证据等级：NUMERIC_BASAL_AREA_BIOMASS_SHARE。
**HOLD：** Post-typhoon state (2005-2012) not represented
**待补证据：** Total basal area and pre-typhoon LAI; confirm 28% biomass loss.

替代方案：
- `sasa_c3_patch_placeholder`：DBF 75 / CoolC3 25。Sasa as cool C3 patch; the 25 is a sensitivity placeholder, not measured.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：DBF 42.9868N 141.3853E 173 m; windthrow（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- typhoon：8 Sep 2004; 40% of trees damaged（tree count；stand；核实：RECHECKED）[来源](https://bg.copernicus.org/articles/12/6837/2015/bg-12-6837-2015.html)
- birch+oak share：birch+oak >75% basal area (2003); biomass birch 51.6%, oak 33.5%（basal area / biomass；stand；核实：AGENT_READ）[来源](https://bg.copernicus.org/articles/12/6837/2015/bg-12-6837-2015.pdf)
- stems/height/Sasa：672 stems/ha (DBH>5 cm), 18.3 m (2003); Sasa LAI 4.05 (2007); biomass loss 28% and canopy loss 33% not re-verified (abstract gives 40% of trees only)（stems；stand；核实：AGENT_READ）[来源](https://bg.copernicus.org/articles/12/6837/2015/bg-12-6837-2015.pdf)

### JP-Tak — DBF 100

站点：Takayama；IGBP 来源：DBF。
目标状态：Cool-temperate deciduous broadleaf forest；时段：1998-2021; no disturbance recorded。

**依据与规则：** Deciduous species 97.2% of basal area (Q. crispula 26.9, B. ermanii 24.6, B. platyphylla 14.6) -> FATES6; the 2.8% remainder is unidentified and folded in.

**余项处理：** Dense Sasa senanensis floor (LAI ~1.7) omitted in the primary.
**裸地：** Model convention bare=0.
**原证据分母：** 1 ha plot, 2016 census, shares of total basal area; Cao 2024 (not re-opened this session)
**不确定性：** 低；证据等级：NUMERIC_BASAL_AREA_SHARE。
**HOLD：** Cao 2024 shares not independently re-verified
**待补证据：** Stem density and species-level LAI table.

替代方案：
- `sasa_c3_patch_placeholder`：DBF 75 / CoolC3 25。Sasa as cool C3 patch; the 25 is a sensitivity placeholder, not measured.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：DBF 36.1462N 137.4231E 1425 m（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- basal-area shares：Q. crispula 26.9, B. ermanii 24.6, B. platyphylla 14.6; deciduous total 97.2 %（share of total basal area；1 ha plot；核实：AGENT_READ）[来源](https://www.mdpi.com/1999-4907/15/4/725)
- LAI/height：tree LAI ~5.5, Sasa ~1.7; canopy 13-20 m（；site；核实：AGENT_READ）[来源](https://asiaflux.nies.go.jp/site-info/TKY.html)

### JP-Tef — DNF 100

站点：Teshio CC-LaG；IGBP 来源：DNF (time-varying: MIX -> clearcut -> larch)。
目标状态：Post-clearcut hybrid larch plantation；时段：Clearcut Jan-Mar 2003, planted Oct 2003; 2011-2023 composition not found。

**依据与规则：** Most of the 2001-2023 record is the planted larch (Larix gmelinii x kaempferi, ~2500/ha) -> FATES3, matching ESSD IGBP DNF. Sasa is omitted in the primary even though its PAI (8.0) greatly exceeds larch PAI (1.7) in 2010.

**余项处理：** Static single-PFT vector hides a large Sasa share; LAI-share scenario provided.
**裸地：** Model convention bare=0.
**原证据分母：** Pre-cut 50x50 m plot 2000: 155 trees, BA 21.8 m2/ha; 2010 PAI larch 1.7 / Sasa 8.0
**不确定性：** 高；证据等级：NUMERIC_EARLY_REGROWTH_ONLY。
**HOLD：** Composition changes during the record; pre-2003 mixed forest has no numeric shares
**待补证据：** Post-2012 larch and Sasa structure; pre-cut species basal-area shares.

替代方案：
- `sasa_PAI_share`：DNF 17.5 / CoolC3 82.5。PAI shares 1.7:8.0 (2010) used as area; a LAI proxy, not an area measurement.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：DNF 45.0558N 142.1071E 79.47 m; clearcut（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- pre-cut stand：155 trees (DBH>6 cm), BA 21.8 m2/ha; PAI canopy 3.2, Sasa 4.1（50x50 m plot；plot；核实：AGENT_READ）[来源](https://core.ac.uk/download/41877662.pdf)
- post-cut regrowth：~2500 hybrid larch/ha planted Oct 2003; 2010 larch PAI 1.7, Sasa PAI 8.0（PAI；13.7 ha；核实：AGENT_READ）[来源](https://core.ac.uk/download/41877662.pdf)

### JP-Tmd — DBF 19 / CoolC3 81

站点：Tomakomai (disturbed)；IGBP 来源：DBF (ESSD); GRA (ICOS)。
目标状态：Post-typhoon regrowth: sparse birch over herb layer；时段：2005-2014 (Typhoon Songda Sept 2004 ~90% damage); 2015-2023 not found; year-round data from 2013。

**依据与规则：** 2014 overstory LAI 0.76 (birch, B. platyphylla 67% of overstory biomass) versus understory LAI 2.71-3.85 (Rubus then Solidago gigantea, C3 herbs). Woody share 0.76/(0.76+3.28) = 19 used as DBF; remainder CoolC3. The pre-typhoon larch plantation is JP-Tmk, not in this cohort.

**余项处理：** LAI shares are not area shares; the understory midpoint 3.28 is an assumption.
**裸地：** Model convention bare=0.
**原证据分母：** 2014 overstory 4380 stems/ha, BA 1.12 m2/ha, height 2.0 m (Yazaki 2016, not re-opened)
**不确定性：** 高；证据等级：NUMERIC_LAI_SHARE_PROXY。
**HOLD：** ESSD and ICOS disagree on IGBP; pre-typhoon larch LAI split differs between sources (3.3/2.5 vs 2.7/3.1)
**待补证据：** 2015-2023 composition; reconcile Hirano and Yazaki pre-typhoon values.

替代方案：
- `birch_forest`：DBF 100。ESSD 'after' DBF label taken literally.
- `herb_only`：CoolC3 100。ESSD 'windthrow' GRA label.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：DBF 42.7359N 141.5231E 117 m; windthrow（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- pre-typhoon basal area and LAI (Hirano)：BA larch 19.6 + other 5.5 m2/ha (DBH>5 cm); max LAI 9.4 (trees 5.8: larch 3.3 + other 2.5; understory 3.6)（basal area / LAI；site；核实：RECHECKED）[来源](https://eprints.lib.hokudai.ac.jp/repo/huscap/all/45748/hirano2.pdf)
- pre-typhoon (Yazaki)：1179 stems/ha, BA 29.7 m2/ha, LAI 9.3 (larch 2.7, other 3.1, understory 3.5)（stems/BA/LAI；site；核实：AGENT_READ (conflicts with Hirano split)）[来源](https://eprints.lib.hokudai.ac.jp/repo/huscap/all/64380/Forests7-11_287.pdf)
- post-typhoon regrowth：2014: 4380 stems/ha, BA 1.12 m2/ha, 2.0 m; B. platyphylla 67% and birches 78% of overstory biomass; overstory LAI 0.76, understory LAI 2.71-3.85（stems/biomass/LAI；site；核实：AGENT_READ）[来源](https://eprints.lib.hokudai.ac.jp/repo/huscap/all/64380/Forests7-11_287.pdf)

### JP-Tom — DBF 100

站点：Tomakomai Experimental Forest；IGBP 来源：DBF。
目标状态：Cool-temperate deciduous broadleaf forest (not the larch site)；时段：1999-2013。

**依据与规则：** Q. crispula, B. platyphylla and Acer mono (all deciduous broadleaf), canopy 16 m, LAI 4-6 -> FATES6. Do not borrow the neighbouring JP-Toc old-oak structure.

**余项处理：** No shares; dwarf-bamboo understory omitted.
**裸地：** Model convention bare=0.
**原证据分母：** Site page only; stand ~54 yr in 2008 (1954 origin is an inference)
**不确定性：** 中；证据等级：QUALITATIVE_DOMINANT_TYPE。
**HOLD：** Site-page evidence only
**待补证据：** Open the local BADM vegetation-cover xlsx; Shibata 2005; ADS record.

替代方案：
- `sasa_c3_patch_placeholder`：DBF 75 / CoolC3 25。Sasa as cool C3 patch; the 25 is a placeholder.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：DBF 42.6989N 141.5715E 90 m（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- stand：Quercus crispula, Betula platyphylla, Acer mono; dwarf bamboo; 16 m; LAI 4-6; ~54 yr (2008)（qualitative；site；核实：SECONDARY）[来源](https://asiaflux.nies.go.jp/site-info/TOE.html)

### JP-Tgf — CoolC3 40 / C4 60

站点：Tsukuba grassland (TERC)；IGBP 来源：GRA。
目标状态：Mown C3/C4 mixed grassland；时段：2002-2022; annual winter mowing。

**依据与规则：** C3 Solidago altissima dominates spring to early summer; C4 Miscanthus sinensis and Imperata cylindrica dominate late summer to autumn when biomass peaks (680-886 g/m2). C4 60 / C3 40 is a prior leaning to the biomass-peak season.

**余项处理：** No cover or biomass shares found; the split is a prior.
**裸地：** Model convention bare=0.
**原证据分母：** LAI 1.7-1.9 growing period, 3.7-4.8 peak; biomass quadrats 2x2 m x80 (Shimoda 2005 Table 3)
**不确定性：** 高；证据等级：QUALITATIVE_SEASONAL_DOMINANCE。
**HOLD：** Earlier species list (Festuca, Imperata, Andropogon in 1993) suggests composition may have changed
**待补证据：** Shimoda 2009 for C3/C4 shares; local BADM vegetation-cover xlsx.

替代方案：
- `equal_C3_C4`：CoolC3 50 / C4 50。Neutral split.
- `C4_dominant`：CoolC3 20 / C4 80。C4-dominant sensitivity.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：GRA 36.1135N 140.0949E 27 m; mowing（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- C3/C4 phenology：C3 Solidago altissima spring-early summer; C4 Miscanthus sinensis, Imperata cylindrica late summer-autumn; mown once a year（qualitative；field；核实：AGENT_READ）[来源](https://doi.org/10.2151/sola.2005-044)
- LAI and biomass：growing-period LAI 1.7-1.9, peak 3.7-4.8; peak biomass 680-886 g/m2（80 quadrats 2x2 m；field；核实：AGENT_READ）[来源](https://doi.org/10.2151/sola.2005-044)

### JP-Yms — DBF 72 / EBT 28

站点：Yamashiro；IGBP 来源：DBF。
目标状态：Oak-dominated secondary forest after 1980s pine wilt；时段：2000-2023; no composition change documented。

**依据与规则：** 1999 biomass: Quercus serrata (deciduous) 66%, Ilex pedunculosa (evergreen broadleaf) 28%. The 6% residual (Alnus, Clethra, Lyonia deciduous; Eurya, Pinus evergreen) is assigned to DBF because the listed residual species are mostly deciduous.

**余项处理：** Residual 6% assignment is an assumption; normalized-named scenario provided.
**裸地：** Model convention bare=0.
**原证据分母：** Tree biomass DBH>=3 cm, 1999, 1.7 ha catchment (Kitao 2014, read via summary); BA 20.7 m2/ha, 105 t/ha (newsletter)
**不确定性：** 中；证据等级：NUMERIC_BIOMASS_SHARE。
**HOLD：** Kitao 2014 shares read via summary only; Kominami 2008 species table not read
**待补证据：** Kominami 2008 / Goto 2003 basal area by species.

替代方案：
- `normalized_named`：DBF 70.2 / EBT 29.8。Named 66+28 normalized to 100.
- `deciduous_only`：DBF 100。Dominant-type proxy.

证据要点（完整见证据台账）：
- site identity, IGBP, disturbance label：DBF 34.7903N 135.8409E 220 m（dataset table；site；核实：RECHECKED）[来源](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.pdf)
- biomass shares：Q. serrata 66%, Ilex pedunculosa 28%（tree biomass DBH>=3 cm；1.7 ha catchment；核实：AGENT_READ (summary only)）[来源](https://doi.org/10.1016/j.envpol.2013.09.023)
- basal area / biomass / LAI：BA 20.7 m2/ha, AGB 105 t/ha (1999); canopy ~12 m; LAI 4.42 summer / 2.70 winter（stems >3 cm DBH；1.6 ha watershed；核实：SECONDARY）[来源](https://www2.ffpri.go.jp/labs/flux/YMS_e.html)

## 验证

- 46 行（20 个主推荐 + 26 个替代方案）：每行自然土壤面积合计 100，活体 PFT 不超过 4，DEFAULT14 往返映射 46/46 PASS。往返映射用的是你们仓库 `recommended_hlm_profiles_v1_20261026.json` 里记录的 14×14 矩阵。
- 这只说明数字在该矩阵下自洽，**没有**检查你们实际 FATES 参数文件。`active_case_parameter_verified=NO`。

## 证据核实状态

证据台账的核实列含义：`RECHECKED` 表示我在本次会话中重新打开了来源；`AGENT_READ` 表示由调研子任务读取，我没有重新打开；`SECONDARY` 为幻灯片/站点页面/通讯等非同行评议来源；`REPO` 来自你们的仓库。**绝大多数数字属于 AGENT_READ，使用前请对照原文**，尤其是标注了“not reopened”和“summary only”的 JP-Fhk、JP-Tak、JP-Yms、JP-Tmd。
- 条目分布：AGENT_READ 44；RECHECKED 13；REPO 4；SECONDARY 6

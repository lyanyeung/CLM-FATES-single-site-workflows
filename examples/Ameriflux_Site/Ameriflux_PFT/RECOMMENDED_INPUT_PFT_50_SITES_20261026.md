# 50个AmeriFlux站点：建议的CLM-FATES输入PFT百分比 v1

**2026年10月26日。下表已为全部50站给出具体、闭合到100%的主推荐；另有35组敏感性/时段替代方案。** 这是建模建议表，原实测证据表保持不变。

适用范围：独立cold start、`use_fates_fixed_biogeog=.true.`且`use_fates_nocomp=.true.`（FIXNC）。下列百分比是**模型自然土壤landunit内的面积分配，含裸地host0**，不自动等于原始网格全部土地或观测足迹的实测覆盖率。竞争模式不能保证保持这些面积比例。

对新的理想化塔点，可将研究域定义为NATVEG100/CROP0的自然土壤点；这是另一个显式建模假设，不能因此改掉现有surface中的湖泊、湿地、农业等真实地类。本次只写建议表和参数映射配置，不写surface、现有parameter文件或作业。

## 可以直接查看的输入文件

- [完整50站建议总表CSV](RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_20261026.csv)：比例、目标状态、依据、余项处理、裸地假设及原始来源。
- [CLM host输入矩阵CSV](RECOMMENDED_50_SITE_CLM_PCT_NAT_PFT_20261026.csv)：`PCT_NAT_PFT_0`至`14`，每站合计100；0为裸地。若实际surface包含额外crop PFT槽位，先核对维度，不能盲目按15维重建变量。
- [FATES两种分母矩阵CSV](RECOMMENDED_50_SITE_FATES_PFT_PERCENT_20261026.csv)：`pct_natland`列加bare合计100；`pct_vegetated_only`列自身合计100。**不能将bare加到第二组再要求合计100。**
- [35组敏感性/时段替代CSV](PFT_INPUT_SENSITIVITY_SCENARIOS_20261026.csv)。
- [三种HLM映射配置](metadata/recommended_hlm_profiles_v1_20261026.json)：包括原始默认映射及建议的独立站点映射。

例如US-Aud：自然土壤面积中C4=70、bare=30；活体植被内部C4=100。对应host14=70、host0=30。不能先把host14归一成100而丢掉裸地。

## 50站主推荐（%）

`ENF`常绿针叶树；`DBF`落叶阔叶树；`DNF`落叶针叶树；`TropEBF`热带常绿阔叶树；`EvergreenShrub`常绿灌木；`HydrodecidShrub`旱季落叶灌木；`ColdDecidShrub`寒季落叶灌木；`ArcticEvergreenShrub/ArcticDecidShrub`北极型常绿/落叶灌木；`ArcticC3/CoolC3/C4`分别为北极型C3、非北极型C3和C4草本代理。`bare`为无植被地表的模型分配。

| 批次 | 站点 | 建议百分比：自然土壤面积，含bare | 依据类型 | 不确定性 |
| --- | --- | --- | --- | --- |
| Batch01 | BR-Ma2 | TropEBF 100 | PUBLISHED_MODEL_PRECEDENT | MEDIUM |
| Batch01 | CA-Ca3 | ENF 100 | STAND_FUNCTIONAL_PROXY | MEDIUM |
| Batch01 | CA-Cbo | ENF 18.6 / DBF 81.4 | EXPLICIT_NORMALIZED_STEM_PROXY | MEDIUM |
| Batch01 | CA-LP1 | ENF 100 | DOMINANT_FOREST_PROXY | HIGH |
| Batch01 | CA-Man | ENF 100 | BASAL_AREA_PROXY_WITH_RESIDUAL_ASSUMPTION | MEDIUM |
| Batch01 | CA-TP1 | ENF 100 | CATEGORICAL_TREE_TYPE_PROXY | MEDIUM |
| Batch01 | CA-TP3 | ENF 99 / DBF 1 | PUBLISHED_SPECIES_PROXY | MEDIUM |
| Batch01 | CA-TP4 | ENF 93 / DBF 7 | EXISTING_PROJECT_INPUT_PROXY | MEDIUM |
| Batch01 | US-Aud | C4 70 / bare 30 | EXISTING_OPERATOR_SELECTED_MODEL_PRECEDENT | MEDIUM |
| Batch01 | US-Bar | ENF 17 / DBF 83 | SPECIES_PROXY_WITH_EXPLICIT_CONIFER_RESIDUAL | HIGH |
| Batch02 | US-BZS | ENF 20 / ArcticEvergreenShrub 60 / ArcticDecidShrub 10 / ArcticC3 10 | PARTIAL_TREE_COVER_PLUS_EXPLICIT_PRIOR | HIGH |
| Batch02 | US-CMW | DBF 74 / C4 26 | CROWN_COVER_PLUS_UNDERSTORY_PRIOR | HIGH |
| Batch02 | US-EML | ArcticEvergreenShrub 20 / ArcticDecidShrub 30 / ArcticC3 50 | EXPLICIT_VASCULAR_PRIOR | HIGH |
| Batch02 | US-GLE | ENF 100 | TREE_FUNCTIONAL_PROXY | MEDIUM |
| Batch02 | US-Ha1 | ENF 27.3 / DBF 72.7 | EXPLICIT_NORMALIZED_BASAL_AREA_PROXY | MEDIUM |
| Batch02 | US-Ho1 | ENF 91.9 / DBF 8.1 | EXPLICIT_NORMALIZED_BASAL_AREA_PROXY | MEDIUM |
| Batch02 | US-Ho2 | ENF 90 / DBF 10 | EXPLICIT_POOLED_INVENTORY_PRIOR | HIGH |
| Batch02 | US-Ho3 | ENF 90 / DBF 10 | EXPLICIT_REGIONAL_FOREST_PRIOR | HIGH |
| Batch02 | US-ICh | ArcticEvergreenShrub 30 / ArcticDecidShrub 20 / ArcticC3 50 | COMMUNITY_CONTEXT_PLUS_EXPLICIT_VASCULAR_PRIOR | HIGH |
| Batch02 | US-ICt | ArcticEvergreenShrub 15 / ArcticDecidShrub 25 / ArcticC3 60 | COMMUNITY_CONTEXT_PLUS_EXPLICIT_VASCULAR_PRIOR | HIGH |
| Batch03 | US-Kon | CoolC3 10 / C4 90 | EXPLICIT_C3_C4_PRIOR | HIGH |
| Batch03 | US-Me2 | ENF 90 / EvergreenShrub 5 / HydrodecidShrub 5 | EXPLICIT_CANOPY_UNDERSTORY_PRIOR | HIGH |
| Batch03 | US-Me6 | ENF 80 / HydrodecidShrub 5 / CoolC3 15 | EXPLICIT_REGENERATION_PRIOR | HIGH |
| Batch03 | US-MMS | DBF 100 | DOMINANT_FOREST_PROXY | MEDIUM |
| Batch03 | US-MOz | ENF 10 / DBF 90 | PARTIAL_BASAL_AREA_PLUS_RESIDUAL_ASSUMPTION | MEDIUM |
| Batch03 | US-Mpj | ENF 60 / C4 20 / bare 20 | PUBLISHED_MODEL_PRECEDENT | MEDIUM |
| Batch03 | US-MtB | ENF 100 | DOMINANT_FOREST_PROXY | MEDIUM |
| Batch03 | US-NC2 | ENF 90 / DBF 10 | EXPLICIT_PLANTATION_UNDERSTORY_PRIOR | HIGH |
| Batch03 | US-NR1 | ENF 100 | TREE_FUNCTIONAL_PROXY | MEDIUM |
| Batch03 | US-NR3 | ArcticC3 80 / bare 20 | EXPLICIT_ALPINE_COVER_PRIOR | HIGH |
| Batch04 | US-Rpf | DBF 80 / ColdDecidShrub 20 | EXPLICIT_POSTFIRE_VEGETATION_PRIOR | HIGH |
| Batch04 | US-Seg | C4 60 / bare 40 | PUBLISHED_MODEL_PRECEDENT | MEDIUM |
| Batch04 | US-Ses | EvergreenShrub 55 / C4 25 / bare 20 | PUBLISHED_MODEL_PRECEDENT_WITH_SHRUB_MAPPING | HIGH |
| Batch04 | US-Slt | ENF 38 / DBF 62 | DATED_BASAL_AREA_PROXY | MEDIUM |
| Batch04 | US-SP1 | ENF 85 / EvergreenShrub 15 | EXPLICIT_OVERSTORY_UNDERSTORY_PRIOR | HIGH |
| Batch04 | US-SRG | DBF 11 / C4 44 / bare 45 | PUBLISHED_MODEL_PRECEDENT_WITH_HERB_PROXY | MEDIUM |
| Batch04 | US-SRM | DBF 35 / C4 20 / bare 45 | GROUND_COVER_RANGE_SCENARIO | MEDIUM |
| Batch04 | US-Syv | ENF 50 / DBF 50 | EXPLICIT_SPATIAL_MIXTURE_PRIOR | HIGH |
| Batch04 | US-Ton | DBF 43 / CoolC3 57 | CANOPY_COVER_PLUS_C3_UNDERSTORY_ASSUMPTION | HIGH |
| Batch04 | US-Uaf | ENF 50 / ArcticEvergreenShrub 20 / ArcticDecidShrub 20 / ArcticC3 10 | EXPLICIT_VASCULAR_PRIOR | HIGH |
| Batch05 | US-UiD | CoolC3 20 / C4 80 | EXPLICIT_C3_C4_PRIOR | HIGH |
| Batch05 | US-UMB | ENF 9 / DBF 91 | DATED_BASAL_AREA_PROXY | MEDIUM |
| Batch05 | US-UMd | ENF 10 / DBF 90 | EXPLICIT_PRETREATMENT_FOREST_PRIOR | HIGH |
| Batch05 | US-Var | CoolC3 100 | CATEGORICAL_HERBACEOUS_PROXY | MEDIUM |
| Batch05 | US-Vcm | ENF 100 | PUBLISHED_PREFIRE_MODEL_PRECEDENT | HIGH |
| Batch05 | US-Vcp | ENF 100 | PUBLISHED_MODEL_PRECEDENT | MEDIUM |
| Batch05 | US-WCr | DBF 100 | DOMINANT_BASAL_AREA_PROXY | MEDIUM |
| Batch05 | US-Whs | EvergreenShrub 20 / HydrodecidShrub 20 / C4 3 / bare 57 | COVER_GROUPS_PLUS_PHENOLOGY_PRIOR | HIGH |
| Batch05 | US-Wjs | ENF 15 / C4 85 | PUBLISHED_MODEL_PRECEDENT | MEDIUM |
| Batch05 | US-Wkg | HydrodecidShrub 3 / C4 37 / bare 60 | COVER_GROUPS_WITH_SHRUB_PHYSIOLOGY_PROXY | HIGH |

## HLM映射与实际代码约束

主推荐中DEFAULT14为41站，ARCTIC_PURE为5站，HYDRO_SHRUB为4站。后两类需要站点独立参数文件的映射改动，不能只改surface后沿用原参数。

| 配置 | 用途 | 修改范围 |
| --- | --- | --- |
| DEFAULT14 | 常规树木、常绿灌木、冷落叶灌木及草 | 保留项目已记录的14×14映射 |
| ARCTIC_PURE | BZS、EML、ICh、ICt、Uaf中的纯北极灌木 | host9→FATES10；host11→FATES11；其他行不变。host编号是映射选择器，实际植被性状由FATES列定义 |
| HYDRO_SHRUB | Me2、Me6、Whs、Wkg的旱季落叶灌木 | host10→FATES8；其他行不变。默认映射无法到达FATES8 |

默认host11混合映射为FATES9/10/11=10/10/80，并非纯落叶北极灌木；默认host10映射到FATES9，并非FATES8。表内已按目标映射生成CLM输入，并逐站正向计算回FATES面积核对。

项目所用代码仅在FIXNC中建立host0对应的固定裸地patch；固定生物地理＋竞争模式主要限制允许出现的PFT，整个column仍可用于竞争。现有restart不会因为替换surface自动重置面积。主推荐和替代方案均不超过默认primary land最多4个活体PFT的上限；裸地不计入这4类。

[已记录的项目映射](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/5165099b8daa47cc149b6b82750413d578cf0921/data/batch02_verified_HLM_FATES_map_20261025.json)；[所用FATES初始化代码](https://github.com/NGEET/fates/blob/121723f64e94be97fd91fc95cfd1ba72dfc191ee/main/EDInitMod.F90#L598-L658)；[裸地及面积初始化](https://github.com/NGEET/fates/blob/121723f64e94be97fd91fc95cfd1ba72dfc191ee/main/EDInitMod.F90#L855-L936)。这些代码依据不代表50个新case的实际parameter文件已经逐一检查。

## 采用建议时最重要的解释

1. **有观测数值也不自动是面积输入。** Borden、Harvard、Howland等使用株数/基面积作为面积代理；原始分母和归一化方法保存在CSV。Bartlett的3%余项在本建议中明确假定为其他针叶树，原始83/14/unknown3没有改写。
2. **森林只有一种PFT不等于实测全地表100%树冠。** ENF100/DBF100是理想化森林功能型方案；林下与冠层的垂直重叠不能逐层相加。Me6、SP1、NC2等的林下比例属于显式先验。
3. **苔原与泥炭地是高不确定性的维管植物投影。** Moss、lichen和biocrust没有独立PFT；没有把它们的观测份额改叫bare或grass。所列权重定义一个省略其显式功能的模型情景，不是完整生态系统地表分类；bare0只是该情景的约定。
4. **干旱地裸地来源逐站区别。** Aud70/30保留既有用户选择；SRM35/20/45位于已报告范围内；Ses、Seg、Mpj、Wjs采用文献模型先例。Whs57、Wkg60及SRG45为模型面积分配，不能重新标成独立实测裸地。NR3 bare20完全是假设，附0/40替代。
5. **物候和株型仍有近似。** 干旱落叶灌木用FATES8并配置独立映射；mesquite保持树型FATES6，但该默认类型的冷落叶性状并不等同于真实旱季落叶，后续需核对性状/根系。将苔草、阔叶草本合并到草PFT同样是功能代理。
6. **固定状态不重建整段历史。** Vcm主推荐仅代表2013火灾前；Me2仅代表2020火灾前；Slt主推荐代表2018虫害后；UMd主推荐代表2008处理前。完整release年份的气象循环可驱动一个固定状态实验，但不能据此声称模拟了真实扰动历史。

## 每站决策与来源

### BR-Ma2 — TropEBF 100

目标：Idealized intact K34 evergreen forest；时段：Intact-forest reference; release1999-2016。

依据及建议：Use tropical evergreen tree functional group, consistent with the existing BR-Ma2 technical forest-point pilot. 余项处理：Single-PFT forest hypothesis; botanical/footprint fractions remain unmeasured.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：ORCHIDEE MODEL ASSUMED FOREST COVER; NOT K34 MEASURED PFT AREA。原始来源：[source1](https://doi.org/10.1029/2018MS001565), [source2](https://ameriflux.lbl.gov/sites/siteinfo/BR-Ma2).

### CA-Ca3 — ENF 100

目标：HDF88 conifer forest；时段：2002-era stand reference。

依据及建议：The three reported tree species75/21/4 are all evergreen conifers. 余项处理：Treat sampled tree functional composition as a forest-point area proxy; exclude unquantified understory.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：SITE STAND TREE COVER TYPE; NOT FULL EC FOOTPRINT / INITIAL FATES BIOMASS。原始来源：[source1](https://doi.org/10.1029/2008JG000912).

### CA-Cbo — ENF 18.6 / DBF 81.4

目标：Borden mixed forest；时段：2006 census reference。

依据及建议：Normalize reported DBF81.6 and ENF18.7 by their rounded sum100.3, then round to0.1 percentage point. 余项处理：The normalization is a new model prescription, not a correction of the unchanged original100.3 stem percentages.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：2006 TREE STEM-COUNT SHARES; ROUNDED SUM=100.3 NOT AREA。原始来源：[source1](https://doi.org/10.1016/j.agrformet.2009.07.011), [source2](https://www.researchgate.net/publication/223845196_Eight_years_of_carbon_dioxide_exchange_above_a_mixed_forest_at_Borden_Ontario).

### CA-LP1 — ENF 100

目标：Lodgepole-pine tree-type experiment；时段：MPB-06 reference; beetle disturbance separate。

依据及建议：Near-pure lodgepole description supports conifer eligibility; the juvenile table alone does not quantify canopy area. 余项处理：Use a conifer-only forest hypothesis, not a juvenile-census extrapolation presented as observation.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：STEM DENSITIES FOR THREE TABLED SEEDLING/SAPLING SPECIES ONLY; NOT WHOLE OVERSTORY PFT COVER。原始来源：[source1](https://doi.org/10.1016/j.agrformet.2009.11.008), [source2](https://www.researchgate.net/publication/220009719_Impact_of_mountain_pine_beetle_on_the_net_ecosystem_production_of_lodgepole_pine_stands_in_British_Columbia).

### CA-Man — ENF 100

目标：Old black-spruce tree-type experiment；时段：1999-2000 canopy reference。

依据及建议：Black spruce accounts for99% of overstory basal area. 余项处理：Assign the unknown1% to the dominant ENF for baseline only; test ENF99/DNF1 separately. No claim the residual was observed larch.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：BLACK SPRUCE SHARE OF OVERSTORY BASAL AREA; NOT TOTAL LAND AREA。原始来源：[source1](https://doi.org/10.1029/2001JD000854).

### CA-TP1 — ENF 100

目标：White-pine plantation functional type；时段：Post-establishment2002 plantation reference。

依据及建议：All-white-pine tree-stand statement supports an ENF-only plantation scenario. 余项处理：Categorical tree composition converted to a forest-point hypothesis; age and planting structure remain separate.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：PUBLISHED TREE SPECIES COMPOSITION; DENOMINATOR IN SOURCE NOT FULLY VERIFIED。原始来源：[source1](https://doi.org/10.1186/s13717-021-00349-7).

### CA-TP3 — ENF 99 / DBF 1

目标：Mixed plantation tree-type proxy；时段：2019 stand reference。

依据及建议：White pine94 plus jack pine5 become ENF99; oak1 becomes DBF1. 余项处理：Use reported stand percentages as prescribed patch-area proxy; do not claim ground-cover measurement.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：PUBLISHED TREE SPECIES COMPOSITION; DENOMINATOR NOT VERIFIED AS COVER。原始来源：[source1](https://doi.org/10.1186/s13717-021-00349-7).

### CA-TP4 — ENF 93 / DBF 7

目标：Existing idealized plantation forest scenario；时段：2019 species reference; existing pilot policy。

依据及建议：Retain the existing CA-TP4 idealized forest inputENF93/DBF7 in the noncompetition project. 余项处理：Tree species ratio is explicitly used as area proxy; former coarse-grid crop share is not tower evidence.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：PUBLISHED TREE SPECIES COMPOSITION; DENOMINATOR NOT VERIFIED AS COVER。原始来源：[source1](https://doi.org/10.1186/s13717-021-00349-7).

### US-Aud — C4 70 / bare 30

目标：Audubon grass/bare modeling precedent；时段：Published2004-2009 reference。

依据及建议：Retain prior operator-selected C4grass70/bare30. 余项处理：C3/forb minority omitted in this published model simplification.

裸地：Bare30 is the published model assumption already selected by the operator, not a verified footprint survey. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：PUBLISHED ORCHIDEE SITE MODEL FRACTION ASSUMPTION; NOT EC TOWER FOOTPRINT SURVEY。原始来源：[source1](https://doi.org/10.1029/2021JG006400).

### US-Bar — ENF 17 / DBF 83

目标：Bartlett mixed-forest prescription；时段：Published2004-2016 characterization。

依据及建议：Named deciduous species83, hemlock14, and prose mentions minor other conifers. 余项处理：Assign all remaining3 points to other ENF as the recommended hypothesis. Original83/14/unknown3 remains unchanged; normalized-known85.6/14.4 is an alternative.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Published species-composition percentages; paper does not explicitly state stems, basal area or horizontal cover。原始来源：[source1](https://doi.org/10.1016/j.agrformet.2018.03.017), [source2](https://escholarship.org/content/qt1s69x9mm/qt1s69x9mm.pdf).

### US-BZS — ENF 20 / ArcticEvergreenShrub 60 / ArcticDecidShrub 10 / ArcticC3 10

目标：Sparse spruce plus dwarf-shrub vascular projection；时段：Permafrost-forest reference; survey period uncertain。

依据及建议：Tree20 is loosely anchored to reported canopy cover;60/10/10 shrub/graminoid split is a chosen prior. 余项处理：All non-tree weights are model hypotheses, not a measured80% remainder.

裸地：Bare0 is a vascular-projection convention, not an observed zero bare fraction. 非维管植物/地表约定：Vascular-only functional projection; moss/lichen/biocrust have no separate PFT here and are NOT relabeled as bare or grass. No inference that vascular cover occupies100% of observed ground.

原证据分母：Point-intercept cover: species hit at least once / all sampling points; multilayer total may exceed 100%. Four 100 m cardinal transects with points every 2 m.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-BZS), [source2](https://doi.org/10.1002/2014JG002683).

### US-CMW — DBF 74 / C4 26

目标：Mesquite over grass one-layer projection；时段：2001-2003 crown-cover reference。

依据及建议：Retain mesquite crown cover74 as area-allocation proxy; assign remaining26 to C4 sacaton/understory proxy. 余项处理：The26 is not independently measured; avoid combining unrelated80% total-cover description from another period.

裸地：Bare0 is the baseline closed-point convention; a bare10 sensitivity is supplied. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Mesquite crown projection / ground area within 100 m of flux tower; total vegetation estimate in Lee2021 uses another description and must not be subtracted directly.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-CMW), [source2](https://pubs.usgs.gov/sir/2005/5163/pdf/SIR2005-5163.pdf), [source3](https://doi.org/10.1029/2020WR028103).

### US-EML — ArcticEvergreenShrub 20 / ArcticDecidShrub 30 / ArcticC3 50

目标：Moist tundra vascular projection；时段：Eight Mile Lake reference, not a dated full-cover survey。

依据及建议：Eriophorum/sedges and evergreen/deciduous dwarf shrubs justify three types, not exact percentages. 余项处理：All50/30/20 weights are explicit provisional priors.

裸地：Bare0 is a projection convention, not measured. 非维管植物/地表约定：Vascular-only functional projection; moss/lichen/biocrust have no separate PFT here and are NOT relabeled as bare or grass. No inference that vascular cover occupies100% of observed ground.

原证据分母：No verified fractional denominator.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-EML), [source2](https://www2.nau.edu/schuurlab-p/EightMileLake.html), [source3](https://doi.org/10.1029/2011JG001836).

### US-GLE — ENF 100

目标：Spruce-fir forest functional-type experiment；时段：Historical tree census; beetle mortality separate。

依据及建议：Spruce84/fir16 by basal area both map to ENF. 余项处理：Do not convert85% beetle-killed basal area to85% bare ground; mortality/demography require a separate representation.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Tree stems and tree basal area; not horizontal land cover. Composition inventory cited to Speckman manuscript in preparation in Frank2014.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-GLE), [source2](https://doi.org/10.1002/2013JG002597).

### US-Ha1 — ENF 27.3 / DBF 72.7

目标：Harvard mixed forest；时段：Richardson2009 historical BA characterization。

依据及建议：Normalize DBF72 and ENF27 by99; round to0.1 point. 余项处理：Treat the missing1 point as rounding/unclassified and explicitly distribute pro rata for the model baseline; source data unchanged.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Basal area of the historical EMS stand; primary paper rounded species/group percentages.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ha1), [source2](https://doi.org/10.1093/treephys/tpn040), [source3](https://harvardforest1.fas.harvard.edu/exist/apps/datasets/showData.html?id=hf069), [source4](https://doi.org/10.6073/pasta/83d7c9df96f1a151b5375662d81784ad).

### US-Ho1 — ENF 91.9 / DBF 8.1

目标：Howland main tower mixed conifer forest；时段：Richardson2009 historical BA characterization。

依据及建议：Normalize conifer91 and hardwood8 by99; map conifer group to ENF in this baseline. 余项处理：The unknown/rounded1 point is allocated pro rata, not to grass or bare.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Historical stand tree basal area; rounded species/group proportions, not land area.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1), [source2](https://doi.org/10.1093/treephys/tpn040), [source3](https://doi.org/10.1111/j.1365-2486.2004.00847.x).

### US-Ho2 — ENF 90 / DBF 10

目标：Howland west tower mixture prior；时段：Historical pooled main/west inventory context。

依据及建议：Conifers dominate; choose90/10 as a west-tower hypothesis because the17% mixed-species group cannot be split exactly. 余项处理：Do not transfer the main-tower91.9/8.1 as a Ho2 observation.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Live tree basal area; composition is described jointly for two tower plot populations, not a separately tabulated Ho2 PFT partition.。原始来源：[source1](https://ameriflux.lbl.gov/doi/FLUXNET/US-Ho2/), [source2](https://doi.org/10.1111/j.1365-2486.2004.00847.x).

### US-Ho3 — ENF 90 / DBF 10

目标：Howland harvest-site forest-type prior；时段：Postharvest functional hypothesis, not age/biomass initialization。

依据及建议：Use conifer-dominant90/10 provisional mixture pending a tower-specific postharvest inventory. 余项处理：Neither composition nor fraction follows from the30% biomass removal; no bare30 prescription.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Absolute preharvest stand basal area and fraction of biomass removed, not species percentages or land-cover area.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ho3), [source2](https://research.fs.usda.gov/treesearch/15706), [source3](https://doi.org/10.1007/s00267-003-9114-5).

### US-ICh — ArcticEvergreenShrub 30 / ArcticDecidShrub 20 / ArcticC3 50

目标：Heath/tussock mosaic vascular projection；时段：Community mosaic in2017 paper。

依据及建议：Published20% heath/72% tussock communities guide a graminoid-rich prior; they are not species fractions. 余项处理：Weights30/20/50 are model assumptions;8% sedge-meadow/bare combined is not assigned to bare8.

裸地：Bare0 projection convention only. 非维管植物/地表约定：Vascular-only functional projection; moss/lichen/biocrust have no separate PFT here and are NOT relabeled as bare or grass. No inference that vascular cover occupies100% of observed ground.

原证据分母：Area proportions of vegetation community types around tower; mapping radius/precise footprint weighting not specified in the read paragraph.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-ICh), [source2](https://doi.org/10.5194/hess-21-1339-2017), [source3](https://doi.org/10.1111/gcb.16487).

### US-ICt — ArcticEvergreenShrub 15 / ArcticDecidShrub 25 / ArcticC3 60

目标：Tussock tundra vascular projection；时段：2017 community reference。

依据及建议：Tussock-community dominance suggests a graminoid-majority functional prior. 余项处理：Do not set grass95 from95% tussock community;15/25/60 split is assumed.

裸地：Bare0 projection convention only. 非维管植物/地表约定：Vascular-only functional projection; moss/lichen/biocrust have no separate PFT here and are NOT relabeled as bare or grass. No inference that vascular cover occupies100% of observed ground.

原证据分母：Area proportion of vegetation community type around the Tussock tower, not a sedge-only or vegetation-only PFT denominator.。原始来源：[source1](https://ameriflux.lbl.gov/doi/FLUXNET/US-ICt/), [source2](https://ameriflux.lbl.gov/sites/siteinfo/US-ICt), [source3](https://doi.org/10.5194/hess-21-1339-2017).

### US-Kon — CoolC3 10 / C4 90

目标：Annually burned tallgrass prairie；时段：Ungrazed watershed1D reference。

依据及建议：C4 grasses dominate species descriptions; choose90% C4 and10% C3/herb proxy. 余项处理：96% graminoid herbaceous biomass is not90% C4 area; C3/C4 split is assumed.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Oven-dried herbaceous biomass; excludes woody biomass and bare ground. 96% graminoids, approximately 4% non-graminoid herbaceous biomass by complement.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Kon), [source2](https://pmc.ncbi.nlm.nih.gov/articles/PMC3295284/), [source3](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2017jg004046).

### US-Me2 — ENF 90 / EvergreenShrub 5 / HydrodecidShrub 5

目标：Prefire mature pine with shrub proxies；时段：Before20August2020 fire; postfire alternative separate。

依据及建议：Evergreen conifer overstory plus Arctostaphylos and Purshia motivates90/5/5; all weights are assumptions. 余项处理：Do not derive cover from LAI2.1/0.2. Purshia drought-deciduous representation is a trait hypothesis.

裸地：Bare0 forest-point convention only. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：LAI per ground area, separate canopy strata; species dominance qualitative.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Me2), [source2](https://ameriflux.lbl.gov/doi/AmeriFlux/US-Me2/).

### US-Me6 — ENF 80 / HydrodecidShrub 5 / CoolC3 15

目标：Open regenerating pine/herbaceous projection；时段：2010-2011 young-stand reference。

依据及建议：Use ENF80, drought-deciduous shrub5 and cool C3 grass15 to retain identified understory. 余项处理：All weights are assumed; neither LAI0.8/0.1 nor density162/ha supplies these area fractions.

裸地：Bare0 baseline convention; open canopy need not be bare. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Leaf area per ground area and tree density; no percent-cover denominator.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Me6), [source2](https://bg.copernicus.org/articles/11/4139/2014/bg-11-4139-2014.pdf).

### US-MMS — DBF 100

目标：Deciduous tree-type forest proxy；时段：Published stand-characterization reference。

依据及建议：Named genera account for75% BA and are all DBF; use DBF-only baseline. 余项处理：Assume unresolved25% tree BA is also DBF for this forest-type control; test5% ENF separately. No grass residual.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Stand tree basal area; 75% combined named species/genera, 25% unspecified residual. Not percent of ground area.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-MMS), [source2](https://research.fs.usda.gov/download/treesearch/62689.pdf).

### US-MOz — ENF 10 / DBF 90

目标：Oak-hickory-juniper forest proxy；时段：2004-2010 observational context。

依据及建议：Retain named Juniperus10 ENF and assign remaining area to DBF90. 余项处理：Named DBF62 plus unknown28 is explicitly completed as DBF; not a measured90/10 full vector.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Species shares: total stand basal area. Separate 85–92%: total canopy cover around tower. Never merge these denominators or call canopy openings bare soil.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-MOz), [source2](https://scholarworks.iu.edu/dspace/bitstreams/04b5e119-09c9-4835-a0de-c1df14871005/download), [source3](https://pasteur.epa.gov/uploads/91/documents/Geron%20et%20al%202016%20Chemosphere.pdf).

### US-Mpj — ENF 60 / C4 20 / bare 20

目标：Pinyon-juniper savanna precedent；时段：Published2008-2014 reference; mortality separate。

依据及建议：Retain the published60ENF/20C4/20bare fCover; tree60 is consistent with official canopy description. 余项处理：Understory and bare shares are the published model design, not a new field extraction.

裸地：Bare20 is a model precedent, not100 minus tree cover. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：>95% uses total tree cover as denominator; approximately 60% uses site ground/canopy cover area. These statements are not a complete mutually exclusive PFT-area partition.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Mpj).

### US-MtB — ENF 100

目标：Mixed conifer tree-type forest proxy；时段：Mature stand reference。

依据及建议：Three dominant named tree species are evergreen conifers. 余项处理：Treat the forest as ENF-only; unquantified minor herbs and shrubs omitted, not observed absent.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：None: species dominance descriptions, not percent composition.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-MtB), [source2](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021JG006617), [source3](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2624.pdf).

### US-NC2 — ENF 90 / DBF 10

目标：Pine plantation with deciduous understory prior；时段：2005-2009 pre/post-thinning reference。

依据及建议：Pinus taeda dominates; retain a10% DBF Acer/understory proxy. 余项处理：90/10 is a modeling prior, not inferred from summer/winter LAI or thinning percentage.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Total projected LAI per ground area; no species fraction supplied in the read primary passage.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-NC2), [source2](https://ameriflux.lbl.gov/doi/AmeriFlux/US-NC2/), [source3](https://research.fs.usda.gov/download/treesearch/41896.pdf).

### US-NR1 — ENF 100

目标：Subalpine evergreen tree-type forest；时段：Published tree-stem census reference。

依据及建议：Fir46/spruce28/lodgepole26 all map to ENF. 余项处理：Stem composition collapsed to a forest-only area proxy; understory/ground fractions not inferred.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Tree stem density in stand description, not basal area or ground area.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-NR1), [source2](https://research.fs.usda.gov/download/treesearch/63425.pdf).

### US-NR3 — ArcticC3 80 / bare 20

目标：Alpine herbaceous/fellfield projection；时段：T-Van West dry-meadow reference。

依据及建议：Use Arctic/alpine C3 herb proxy80 and nonvegetated substrate20 as a central sensitivity hypothesis. 余项处理：No tower-specific cover survey constrains80/20; forbs lumped with C3 grass and possible shrubs omitted.

裸地：Bare20 is wholly assumed and lumps possible rock/nonvegetated substrate; alternatives0/40 supplied. It is not snow fraction. 非维管植物/地表约定：Moss/lichen unrepresented; no measured nonvascular fraction converted to bare. Assumed20 substrate remains a separate modeling sensitivity.

原证据分母：None: vegetation-community descriptions; no area fractions read for the exact tower footprint.。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-NR3), [source2](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016JG003704), [source3](https://doi.org/10.1029/2023JG007664).

### US-Rpf — DBF 80 / ColdDecidShrub 20

目标：Postfire aspen-birch/shrub mixture prior；时段：Young post2004-fire reference; not original spruce forest。

依据及建议：Assign80% DBF and20% cold-deciduous extratropical shrubs to represent named young forest and shrub components. 余项处理：All percentages assumed; no reuse of intact US-Prr spruce composition.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Not reported for composition。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Rpf), [source2](https://ameriflux.lbl.gov/community/publication/leaf-and-ecosystem-scale-photosynthetic-parameters-for-the-overstory-and-understory-of-boreal-forests-in-interior-alaska/), [source3](https://www.jstage.jst.go.jp/article/agrmet/74/2/74_D-17-00031/_article/-char/en).

### US-Seg — C4 60 / bare 40

目标：Black-grama grass/bare precedent；时段：Published2007-2014 reference;2009 fire separate。

依据及建议：Use published C4grass60/bare40 as explicit model baseline. 余项处理：A60% surface-cover description does not independently establish bare40 or a time-invariant postfire state.

裸地：Bare40 from model precedent; older live-plus-litter survey has different scope. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Surface area in Duman2021; older 60% value includes live vegetation plus litter and is not equivalent to living cover。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Seg), [source2](https://par.nsf.gov/servlets/purl/10255415), [source3](https://doi.org/10.1016/j.agrformet.2020.108246), [source4](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2009JD013529), [source5](https://research.fs.usda.gov/download/treesearch/47836.pdf).

### US-Ses — EvergreenShrub 55 / C4 25 / bare 20

目标：Creosote shrub/grass precedent；时段：Published2007-2014 model reference。

依据及建议：Translate source TeBE55 to evergreen SHRUB FATES7, retain C4grass25 and bare20. 余项处理：This model fCover is not the historical nearby30% vegetation survey or current tower species cover.

裸地：Bare20 from published model design; low-cover70 sensitivity provided. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：0.9 shrubs per m² (density, not percent); legacy ground area cover; Larrea percentage over two specific transects。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ses), [source2](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2009JD013529), [source3](https://research.fs.usda.gov/download/treesearch/47836.pdf).

### US-Slt — ENF 38 / DBF 62

目标：Postinfestation2018 oak-pine state；时段：2018 target; early2005 alternative separate。

依据及建议：Use measured pine38% live tree+sapling BA; non-pine62 interpreted as DBF for model input. 余项处理：62 is the non-pine complement with a functional classification assumption; not full measured ground cover.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Total basal area of inventoried live trees+saplings; not land surface cover or stem count。原始来源：[source1](https://ameriflux.lbl.gov/sites/site-search/), [source2](https://ameriflux.lbl.gov/sites/siteinfo/US-Slt), [source3](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0265955), [source4](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016JG003467).

### US-SP1 — ENF 85 / EvergreenShrub 15

目标：Pine flatwoods with evergreen understory prior；时段：2000s-2018 functional reference; burns/thinning separate。

依据及建议：All dominant pines share ENF; dense palmetto/gallberry/wax-myrtle motivates evergreen-shrub15. 余项处理：85/15 split is assumed; reported longleaf/slash ratios are within one ENF type and cannot supply the shrub share.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Bracho2023 total stand basal area at beginning of study; Silva2021 percentage of trees; Powell2005 stand basal area。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-SP1), [source2](https://www.fs.usda.gov/nrs/pubs/jrnl/2023/nrs_2023_bracho_001.pdf), [source3](https://doi.org/10.1016/j.foreco.2023.121408), [source4](https://research.fs.usda.gov/download/treesearch/19963.pdf), [source5](https://www.mdpi.com/1999-4907/12/1/38).

### US-SRG — DBF 11 / C4 44 / bare 45

目标：Mesquite grassland modeling precedent；时段：Published2009-2014 reference。

依据及建议：Retain source woody11, herb44 and modeled bare45; map woody mesquite to DBF tree and herbs to C4grass. 余项处理：44 includes forbs/succulents in field table; C4-only simplification and exclusive layer allocation are assumptions.

裸地：Bare45 is the published model allocation; not a separately observed residual measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Canopy cover percentage of ground by woody and perennial understory groups; separate layers may overlap。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-SRG), [source2](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2308.pdf), [source3](https://doi.org/10.1002/2015JG003181).

### US-SRM — DBF 35 / C4 20 / bare 45

目标：Mesquite savanna range-consistent prescription；时段：2004-2016 literature characterization。

依据及建议：Tree35/grass20/bare45 falls within reported30-35/15-25/40-50 cover ranges and closes100. 余项处理：Joint vector chosen as scenario; independent ranges/layers are not a measured simplex. Minor C3/succulent groups lumped.

裸地：Bare45 is chosen within explicitly reported40-50 range, not an arbitrary canopy complement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Ground-area cover by vegetation layers and bare soil; quoted ranges are independently approximate。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-SRM), [source2](https://doi.org/10.1029/2018WR023477), [source3](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2308.pdf), [source4](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2008JG000900).

### US-Syv — ENF 50 / DBF 50

目标：Footprint-mixture prior for old-growth mosaic；时段：Undated wider-footprint functional reference。

依据及建议：Use neutral50/50 DBF/ENF as provisional footprint mixture because local1ha and wider1km2 dominance differ. 余项处理：Do not present50/50 as observed; local-stem86/14 and hemlock-rich30/70 are required sensitivity alternatives.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Overstory stems in immediate1ha, not basal area, leaf area or ground cover。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Syv), [source2](https://ameriflux.lbl.gov/doi/FLUXNET/US-Syv/), [source3](https://co2.aos.wisc.edu/~adesai/documents/Desai-AFM-Sylvania.pdf), [source4](https://doi.org/10.1016/j.agrformet.2004.09.005).

### US-Ton — DBF 43 / CoolC3 57

目标：Oak savanna one-layer canopy projection；时段：IKONOS-era1km2 canopy reference。

依据及建议：Use woodland canopy43 as DBF-oak patch proxy and assign57 to C3 herbaceous patch. 余项处理：Canopy-understory overlap is collapsed into exclusive model patches. Minor grey pine omitted;3trees/ha is not3% area.

裸地：Bare0 convention;57 is not observed grass cover. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Woodland projected canopy fraction of1km² image; official40% total vegetation wording ambiguous; pine3trees/ha is density。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ton), [source2](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007WR006646).

### US-Uaf — ENF 50 / ArcticEvergreenShrub 20 / ArcticDecidShrub 20 / ArcticC3 10

目标：Spruce/shrub vascular projection；时段：Smith Lake reference; not North Campus surrogate。

依据及建议：Retain black spruce, evergreen/deciduous dwarf shrubs and C3graminoid functional components. 余项处理：All50/20/20/10 weights are assumed;4500trees/ha and complete moss floor do not imply these percentages.

裸地：Bare0 projection convention only. 非维管植物/地表约定：Vascular-only functional projection; moss/lichen/biocrust have no separate PFT here and are NOT relabeled as bare or grass. No inference that vascular cover occupies100% of observed ground.

原证据分母：Trees per hectare; combined forest-floor coverage described qualitatively, not split by species。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Uaf), [source2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11536150/), [source3](https://doi.org/10.1073/pnas.2414539121).

### US-UiD — CoolC3 20 / C4 80

目标：Restored native prairie C3/C4 prior；时段：Established perennial prairie; harvest dynamics separate。

依据及建议：Use C4grass80 and C3grass/forb proxy20 for mixed restored prairie. 余项处理：Entire80/20 split is a model prior, not seed-mix or measured cover; UiA/UiB are different fields.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：No observed PFT percentage。原始来源：[source1](https://cabbi.bio/datasets/university-of-illinois-ameriflux-measurements/), [source2](https://doi.org/10.1016/j.agee.2011.09.006), [source3](https://ameriflux.lbl.gov/sites/site-search/).

### US-UMB — ENF 9 / DBF 91

目标：2010 control-tower mixed forest；时段：2010 census target。

依据及建议：Aggregate the2010 species BA table to DBF91/ENF9; retains a complete listed tree mixture. 余项处理：Use BA as an area-allocation proxy;2001 two-point residual and later forest change remain outside this target.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Tree basal area from observational permanent-plot censuses; source fractions multiplied by100, not ground area。原始来源：[source1](https://ameriflux.lbl.gov/doi/AmeriFlux/US-UMB/), [source2](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2015JG003035).

### US-UMd — ENF 10 / DBF 90

目标：Pretreatment FASET forest mixture prior；时段：2007 before2008 girdling; mortality separate。

依据及建议：Use DBF90/ENF10 as nearby forest-type prior; it is not a measured US-UMd vector copied from US-UMB. 余项处理：39% aspen/birch BA affected by girdling is a structural mortality quantity, not bare39 or DBF39.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Pretreatment treatment-area basal area; not whole-site PFT area; leaf-area figures separate。原始来源：[source1](https://repository.library.noaa.gov/view/noaa/49508/noaa_49508_DS1.pdf), [source2](https://doi.org/10.1016/j.foreco.2016.06.001), [source3](https://www.mdpi.com/1999-4907/4/3/537).

### US-Var — CoolC3 100

目标：Mediterranean annual C3 herbaceous proxy；时段：Vaira wet-season annual community。

依据及建议：Map named C3 annual grasses and herbs into cool C3 grass in the baseline. 余项处理：Forbs/clover share is unmeasured; FATES grass physiology is an explicit herbaceous simplification.

裸地：Bare0 is potential vegetation patch convention; dry-season senescence is not permanent bare ground. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：No measured area percentage。原始来源：[source1](https://ameriflux.lbl.gov/doi/AmeriFlux/US-Var/).

### US-Vcm — ENF 100

目标：Prefire mixed-conifer forest precedent；时段：2007-2012 ONLY; not whole2007-2025 historical record。

依据及建议：Use the published prefire ENF100 scenario as the forest-state main recommendation. 余项处理：2013 stand replacement and postfire elderberry/aspen require separate states; no prefire trees assumed to survive by this table.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Tree mortality is a disturbance metric; not vegetation area。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Vcm), [source2](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2604.pdf), [source3](https://fluxnet.org/2014/04/30/thompson-ridge-wildfire-takes-out-ameriflux-core-site/).

### US-Vcp — ENF 100

目标：Ponderosa tree-type forest precedent；时段：Published2007-2014 model reference。

依据及建议：Retain published ENF100 as forest-state control; named Gambel oak is not observed absent. 余项处理：Minor oak/understory omitted in baseline; test ENF90/DBF10 separately.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：No measured area percentage。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Vcp), [source2](https://doi.org/10.1029/2021JG006400).

### US-WCr — DBF 100

目标：Willow Creek deciduous forest-type proxy；时段：Early inventory reference; later thinning separate。

依据及建议：Major named BA species are DBF; use DBF-only forest baseline. 余项处理：Unlisted/rounded minor tree fraction assigned DBF as hypothesis; no regional WLEF30% conifer transfer.

裸地：Model convention bare=0; no independent zero-bare measurement. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Percent of total tree basal area; total28m2/ha in poster。原始来源：[source1](https://www.researchgate.net/publication/241222633_Contributions_From_a_Deciduous_Forest_and_Shrub_Wetland_to_Regional_Carbon_Fluxes_in_Northern_Wisconsin), [source2](https://research.fs.usda.gov/treesearch/download/55333.pdf).

### US-Whs — EvergreenShrub 20 / HydrodecidShrub 20 / C4 3 / bare 57

目标：Mixed-phenology shrubland projection；时段：2012 woody40/herb3 reference。

依据及建议：Preserve woody total40; split evergreen20 and drought-deciduous20 as a trait uncertainty prior. 余项处理：20/20 is assumed, not species cover; herb3 lumped C4 and overlapping cover collapsed to exclusive patch areas.

裸地：Bare57 follows published model allocation; not an independently verified survey residual. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Ground canopy cover by vegetation stratum; not sum-to100 whole-ground classification。原始来源：[source1](https://doi.org/10.3390/soilsystems3010006), [source2](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2525.pdf).

### US-Wjs — ENF 15 / C4 85

目标：Juniper savanna published model baseline；时段：Published2008-2014 reference。

依据及建议：Retain15ENF/85C4 exactly as published model fCover; do not invent a new bare estimate in the main row. 余项处理：85%grass and absence of prescribed bare are modeling choices, not field-cover measurements.

裸地：Bare0 is published model convention; bare25 sensitivity is explicitly assumed. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：No measured whole-ground PFT fraction。原始来源：[source1](https://ameriflux.lbl.gov/sites/siteinfo/US-Wjs), [source2](https://www.litvaklab.org/juniper-savanna-us-wjs.html).

### US-Wkg — HydrodecidShrub 3 / C4 37 / bare 60

目标：C4grass with sparse dryland shrubs；时段：2017 woody3/herb37; historical model reference。

依据及建议：Use woody3 as drought-deciduous shrub proxy, herb37 as C4grass and model bare60. 余项处理：Woody species phenology is mixed and37 field group includes forbs; compare evergreen-shrub3 alternative.

裸地：Bare60 from published model allocation, not proof all uncovered ground is bare. 非维管植物/地表约定：Not separately represented; tree/grass patch convention does not measure every ground component.

原证据分母：Ground canopy cover by stratum; not species fraction or biomass。原始来源：[source1](https://doi.org/10.3390/soilsystems3010006), [source2](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2525.pdf), [source3](https://doi.org/10.1029/2010JG001348).

## 重建与验证

```bash
python3 scripts/build_recommended_inputs.py --build
python3 scripts/build_recommended_inputs.py --check
```

纯Python标准库。检查50个唯一站点、每批10个、所有主/替代方案面积闭合、活体PFT≤4、host→FATES精确回算、活体内部比例归一化，以及生成文件可重复。验证表列出全部85组方案。本次未修改已有模型输入或提交作业。

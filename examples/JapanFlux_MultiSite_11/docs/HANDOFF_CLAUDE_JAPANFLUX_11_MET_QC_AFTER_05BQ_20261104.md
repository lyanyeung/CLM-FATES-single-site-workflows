# 给 Claude 的交接：JapanFlux MultiSite 11 气象 QC 与安全修复

交接日期：2026-11-04。请完整阅读本文及所链接的实际运行报告，然后直接继续项目，主动完成能独立推进的工作。用户希望一次性多处理，不要每完成一个小检查就让用户重复操作。

仓库：<https://github.com/lyanyeung/CLM-FATES-single-site-workflows>。项目路径：`examples/JapanFlux_MultiSite_11`。请检查 GitHub main **当前最新提交**，不要覆盖其他会话或用户新增的改动。用户已明确说明 **PFT 与 Soil Texture 已经在 GitHub 更新，不需要重新寻找或返工**。不要修改非竞争实验仓库。

## 项目目标及权限

对 11 个站点的实际输入气象数据完成可复核、来源清楚的 QC、必要的修复方案和站点级通过/未通过清单，逐步准备可信的 CLM-FATES forcing。不能承诺有限筛查能证明“绝对没有任何问题”；应定义科学上有依据的通过标准和已知限制。

用户要求**能自助推进的直接做，人工审核集中做**。明确授权：读取仓库和公开来源；只读检查原始 ZIP；创建测试、文档、诊断和带原值/来源/哈希的 shadow 候选；将代码与报告同步 GitHub；用户可在 IRIDIS6 执行你提供的批量只读命令。

**硬性限制：**

1. 不自动修改或覆盖原始 ZIP、原始站点数据、正式生产 forcing、PFT、土壤、模型案例、Slurm 或 AD400；不自动提交 Slurm 或模型任务。中间结果只能写入全新、隔离的诊断目录；不得覆盖现有产物。
2. **没有充分证据和用户明确审批，不允许批准或应用任何半小时修复值。** 用户选定某个方法不等于逐值审批。可产生清楚标识 `HOLD / NOT_APPROVED` 的 shadow 和差异清单。若今后必须请求审批，先完成具体、可复核的结果、文件影响、验证和回滚方案；不要先空泛地请求权限。
3. 不要把 QC2 来源连续段当成整段物理异常；不要把 QC1/QC2 或 MDS 当作独立实测。不得把同产品 ERA、已填补数据或 QC0 标签简单等同于独立且正确的观测。
4. **不要重新执行已经完成的 45 条 ERA5-Land 独立对照，也不要重复下载已验证的参考数据。** 若要做新的、不同日期的验证，事先说明新数据与目的，复用可用结果。
5. 若不能直接访问 IRIDIS6，不得假称已经读取其文件或运行脚本。先在本地完成代码与合成测试、同步 GitHub，再提供一段可以直接粘贴的串行、安全、只读命令。命令锁定 commit 与 SHA-256，包含 self-test、测试、真实输入校验；用户执行后依据真实日志判断。遇到校验失败不得绕过。避免对共享登录节点并发长时间解压；按现有习惯串行 `nice -n 10`，遵守集群规则。
6. 写给用户的内容用中文，聚焦结论、剩余问题、真实执行状态和下一次批量动作；不必让用户上传原始站点 ZIP。除用户明确要求外，不通过邮件或其他渠道代发消息。

## 当前整体状态：11 个站点

真实 Stage04 已完成 11/11 站点原始数据初步扫描、原生时间轴基础检查，但这**不是 11 站正式通过**。目前没有文档记录任何站点已完成全部气象科学审核并获最终 forcing 清关。不要把“无初筛旗标”改写成“完美/可投产”。

| 类别 | 站点 | 当前状态 |
|---|---|---|
| 四站进入最后阶段的候选 | JP-Api、JP-Fhk、JP-Spp、JP-Tak | Stage04 选用字段未触发其粗阈值；原始 README 表示当地标准时间无 DST，BIF UTC_OFFSET=9；TA/PA/VPD 单位及 QC 说明有具体源元数据。Stage05BQ 全记录近似湿度可行性通过，但未检查一切来源/模型单位/物理问题，没有最终批准。 |
| 五站已识别 QC2 异常 | JP-Fjy、JP-Khw、JP-Yms、JP-Tef、JP-Tmd | 45 个变量字段、35 个站点×原生半小时、17 组；全部 HOLD。Fjy 6、Khw 11、Yms 10、Tef 4、Tmd 14。PA 27、TA 6、LW 12。 |
| 两站独立问题 | JP-Tom、JP-Tgf | JapanFlux2024 COREVARS，RH/VPD、微小负值、以及 Tgf 两个孤立变量异常；独立于上述 45 字段，全部候选保持未批准。 |

依据：[Stage04 实际 11 站](STAGE04_ACTUAL_FULL11_NATIVE_TIME_AND_QC_20261101.md)、[Stage05F 选用源影响](STAGE05F_ACTUAL_FINAL8_SELECTED_FORCING_IMPACT_20261101.md)、[Stage05BP 实际结果](STAGE05BP_ACTUAL_SIX_SITE_RESULTS_AND_05BQ_PROTOCOL.md)。Stage05E 配套 ERA 审核中，Api 在指定阈值下 0 个异常时间；Fhk/Spp/Tak 的配套同版本 ERA 分别有 20/15/15 个异常时间，其中覆盖原生 selected-F 年份的是 8/6/9。原先 Stage05F 指定事件处受检 selected F 与异常 ERA 数值不同，原始 QC 标签为 0；这只说明特定变量/时间点获得保护，不证明整个文件无异常。不可用出错的同版本 ERA 重新填充。

## 最新真实 Stage05BQ 操作员输出（2026-11-04）

用户刚运行 Stage05BQ，日志从执行命令开始，**没有包含其早先下载哈希或测试行**；不要声称亲眼看到了那些行。本地 self-test 和三项合成测试已通过，用户报 `STAGE05BQ COMPLETE; SHADOW ONLY; ZERO APPROVED; ALL HOLD`。日志粘贴 SHA256 `eccbfd424ceaf98d1ce93c5e30099f3c695864eb922cbe411d5c6f4d1a3f211b`。现有真实输出目录：

```text
/home/ly3n24/japanflux_stage05bq/run_20261104T032013Z_419230/
  summary_HOLD.json
    SHA256 21b36f7a329da6a5d4a3994b988fbde5bf6d3ab7d020929a23951d35c0586675
  special_shadow_candidates_HOLD.tsv
    SHA256 c0fc10d15eb1a9e997ecf0f3b0d8aa6d40534e3c532682585ea74ae582d4ca35
```

四站完整 FLUXMET_HH 的诊断行数及近似比湿范围（kg/kg）：

| 站 | 行数 | 在所选假设下计算可行行数 | 近似 q 范围 kg/kg |
|---|---:|---:|---:|
| Api | 403,248 | 403,248 | 0.0001775651–0.02075395 |
| Fhk | 315,552 | 315,552 | 0.0004578865–0.02319193 |
| Spp | 333,120 | 333,120 | 0.0005444384–0.01953842 |
| Tak | 420,768 | 420,768 | 0.0001247479–0.02089541 |

合计 **1,472,688 行**。使用 Bolton **液态水**饱和水汽压近似、`e=es−VPD` 和 `q=0.622e/(p−0.378e)`，PA 从 kPa 转 hPa；这是条件性可行性筛查，未生成模型 QBOT，不能推导“已经完成全部 QC”。冷条件冰/水饱和、源算法、测量高度/支持时间以及模型实际变量定义需继续核查。

Stage05BQ 生成 **5,101 条字段 shadow**：微小负值置零 5,099 条（Tom 4,322 降水 + 753 VPD；Tgf 3 降水 + 21 VPD），另外 **2 条 Tgf 线性插值仅作未选定敏感性场景**。全部未批准、未写正式 forcing。两条场景：Tgf 2003-12-31 23:30 PA 0 → 100.61 kPa（两侧 100.67/100.55，原始 QC 0/0）；Tgf 2015-12-15 14:30 SW −70.11575 → 90.5987686064 W/m²（左 165.3173 QC1、右 15.8802 QC0）。SW 变化可能受云影响，不得把线性值说成可信修复。PA 异常同一行 TA=0、RH=100、VPD=0，这些字段也需要审核，不能只看 PA。原始字段的数值与 QC 不能被改写。

高 RH 原始 QC 标签分布：Tom 6,583 次中 QC0=6,472、QC1=111；Tgf 9,493 次中 QC0=9,480、QC1=13。原始标签不是质量真值。Tom 6,583 次全部发生于 2013；Tgf 8,466/9,493 发生于 2016–2020。假设存在传感器或处理变化但**尚无证明**。RH>100 与负 VPD 在本数据处理链中相关，不是独立证据；不应盲目将全部 RH 截断至 100 或 VPD 设为 0。

## 核心文件和既有真实运行

仓库优先读：

- [原 45 条详细交接](HANDOFF_ADVANCED_MODEL_JAPANFLUX_45_QC2_POST_STAGE05AX_20261103.md)；它是 05AX 时点的历史，不覆盖本文件的新结果。
- [45 字段实际窗口与共同失真](STAGE05AY_ACTUAL_NATIVE_WINDOWS_SCIENCE_REVIEW.md)、[用户选定 grid+QC2 median 及边界](STAGE05BE_USER_SELECTED_GRID_QC2_SHADOW_AND_CONTINUITY.md)、[实际 05BF 与时间敏感性](STAGE05BG_ACTUAL_IRIDIS_05BF_AND_SELECTED_CLOCK_SENSITIVITY.md)。
- [05BL 五站实测点](STAGE05BL_ACTUAL_FIVE_SITE_30DAY_QC0_RESULTS.md)、[05BN 真实控制及 17 组审查与压力高度](STAGE05BN_ACTUAL_CONTROLS_AND_05BO_PRESSURE_HEIGHT_REVIEW.md)、[05BP 实际六站结果及 05BQ 方案](STAGE05BP_ACTUAL_SIX_SITE_RESULTS_AND_05BQ_PROTOCOL.md)。
- `scripts/stage05/05bp_six_site_meteorology_batch_READONLY.py`、`05bq_four_site_humidity_and_special_shadows_READONLY.py` 及对应测试；Stage05BQ 已真实运行，不要误读 README 中“planned”为当前状态。

操作员报告的其他 IRIDIS 文件：

```text
/home/ly3n24/japanflux_stage04/full11_raw_source_qc.json
  SHA256 f41f437c9df5d01b018f699bbca8c860f5c5b1de92e1062ac3dc1ed3cd46bebf
/home/ly3n24/japanflux_stage05bf/run_20261103T133027Z_2561848/selected_45_HOLD.tsv
  SHA256 bd36ee5d5f8297f4edd8a5c08562473e2110fe6da6354dbaaf0754aaa5ad434f
  six-decimal canonical numeric SHA256 5fd381ddefac2d08a3cee7ed8548c73477c115a342f5895b4673b325768803ae
/home/ly3n24/japanflux_stage05bf/run_20261103T133027Z_2561848/boundary_17_groups_HOLD.tsv
  SHA256 b14be602ef1bedb28721b099e6e9a2b413ab07fb5a91ae4d39b1627b7cbc033c
/home/ly3n24/japanflux_stage05bp/run_20261104T031424Z_359887/summary_HOLD.json
  SHA256 dbbd436cfb1ab40fca58ed6d7905a5477ccc92e55902f8d332df36e55069be5f
/home/ly3n24/japanflux_stage05bp/run_20261104T031424Z_359887/special_derived_screen_events_HOLD.tsv
  SHA256 dbf35b76fea6623241239f94dfdb22277c4ae10e05d40f7bbc14ec0fcaa944d0
/home/ly3n24/japanflux_stage05bl/run_20261103T182225Z_886037/qc0_30day_measured_samples_READONLY.tsv
  SHA256 1eafeb78c609aee5dbe3673473d5d916fb1fda6e81c84aca00f3f4c8d6b3f23b
/home/ly3n24/japanflux_stage05bm/run_20261104T025844Z_890800/qc0_control_pairs_HOLD.tsv
  SHA256 b9bafeed81f68f30512277baaad5fc20df584ea90174e1f52829aa72358b83e3
/home/ly3n24/japanflux_stage05bn/run_20261104T030255Z_297673/control_grid_vs_selected_posthoc_HOLD.tsv
  SHA256 98d58af445e267c6f1f9e28f52af80a24ce54775be30cc5076a59837d6d73354
/home/ly3n24/japanflux_stage05az/run_20261103T073924Z_2301092/group_source_grid_residuals_HOLD.tsv
  SHA256 ed5597796982bafd86a253f670870e90ebabb67212706b0f185d6ee147e7cd61
```

IRIDIS 上的原始包固定在 `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<site>/forcing/packages/`，逐站名称与 SHA256 见 [Stage00](STAGE00_01_VERIFIED_TRANSFER_AND_ZIP_INVENTORY_20261101.md)。报表哈希有的是操作员后来报告的 observed SHA，不一定能追溯证明创建时未曾改变；不要虚报更强的链条。

## 五站 45 字段：已有证据和用户方法选择

- 45/45 与已取得的独立 ERA5-Land 小时网格背景对照，超出各自参考范围；这是强异常证据，**并非站点半小时真值**。45/45 原始 F=同发行 ERA、QC2；在 ±24 h 没有同变量双侧 QC0 塔测锚点。
- 17 组为 9 个 PA 三点、2 个 TA 三点、6 个 LW 两点。PA/TA 三点两侧呈中点关系；LW 成对重复，支持共同处理/插值问题的假设，未证明上游原因。Yms PA 两侧虽然过绝对阈值，也已纳入 45，不能当作修复锚。
- 用户明确选择全部九组 PA、两组 TA、六组 LW 的 **ERA5-Land grid + 同发行 QC2 背景残差中位数**作为继续研究的 shadow 方法；Stage05BF 在 IRIDIS 重建了 45 个 HOLD 候选，未批准任何数值。不应擅自切换到其他方法。可并列评估相邻 QC2 桥接等替代 shadow，明确它们不是 QC0 实测。
- 11/17 组（9 PA + 2 Yms LW）的候选最大变化超过局部 QC2 变化的描述性 p95，p95 既非物理限制也非置信区间。Tmd 2022 PA 左边界约 −0.13415 kPa；Tmd/Fjy 的独立操作 JMA 站高度示意与当前候选有差别，站点相距、气压计/塔传感器实际高度、天气和潜在同化相关性限制解释。详细见 05BN/BO。
- 05BL：只有 Tmd 的 TA/LW 两组在所检查 ±30 d 内找到通过宽范围筛查的 QC0（1,375 和 69），最近分别在异常组结束后 33 h、686 h。05BM/BN 非异常时间控制：Tmd TA 两个日期候选 MAE 0.811/0.915°C；LW 某控制日原网格 23.174、候选 16.859 W/m²。不能将这些数字当作事件真值或其他站/变量的误差。
- Tef/Tmd 原始 README 写 local solar time；BIF UTC_OFFSET=9、ICOS 同版本独立半小时产品元数据和两个内 ZIP 与 ICOS 发行档案 SHA 身份支持 UTC+9 的诊断使用，但**原 README 与标准时间语言冲突未彻底消解**。UTC+8:30/+9/+9:30/经度平均太阳时仅是敏感性，不是置信区间。其他三站标准时间依据见对应 README/BIF。

## 建议直接做的下一批工作：多项合并

1. **四个候选站继续推进通过条件。** 从原始 BIFVARINFO、README、现有 Stage04/05BP/05BQ 和源记录核对 8 个模式必需气象量的单位、时间含义、P 与 SW/LW 辐射的时段支持、QBOT 推导、缺测来源、值域及明显的跨变量冲突；对伴随 ERA 的既知异常和未完全覆盖的肩部做来源敏感检查。尤其分别列出 *已证实、未证实、不适用*。禁止由于通过 05BQ 液水公式就自动宣布模型 forcing 合格。站点级证明达到事先制定的合理条件时，明确给出通过的具体范围和条件；未完成的有针对性继续检查，而不是无限制泛化每个数据点。
2. **Tom/Tgf 集中深审。** 基于现有 21,177 行事件台账与 summary 的 SHA，定位高 RH 的年份、月份、连续段、值分布、QC 和共同变量；从同源 ALLVARS 原始多通道、BADM、同包 ERA5 及官方产品说明，按时间抽样/精确关联，审查 2013 Tom、2016–2020 Tgf 和两个 Tgf 孤立事件。标签和各气象字段的来源规则以准确版本文档为准，不把论文对一般 flux MDS 质量旗标的描述不加验证套到所有气象字段。Tgf 原始通道可能很多，必须用 BADM 而不是随意指定传感器。负 VPD 可与超饱和/传感器误差/加工方案相关；将数据本身与模型对输入的要求分开。候选可评估 `RH≤100 / VPD≥0` 等情景，但必须说明物理假设及潜在水汽偏差，不能整批自动批准。微小负 P/VPD 有 5,099 条可复核的零值 shadow，先独立核对键、偏移、范围、对非目标行的完整恒等性；是否属于可接受的数值规范化须有明确科学规则和用户审批。
3. **五站 45 字段及两条 Tgf 孤立值。** 使用已经下载的参考与 17 组原始窗口，比较用户所选方法、边界、跨变量变化和合理的替代 shadow。优先 Tmd/Fjy 气压、Yms LW、Khw TA MDS 不一致、Tef/Tmd clock。保留独立 ERA5-Land 网格高度与半小时匹配等限制。查官方 JMA 历史仪器高度/塔站传感器高度时注意之前 05BO 读取的是第三方镜像，并非已验证的官方 ZIP。尽量一次构造审阅包：每一组 source/候选/来源/QC/证据/风险/处理建议及待用户明确的批准范围。
4. **工程验收与防护。** 设计站点级、变量级清单：时间连续且支持正确；单位与通量累计/平均、小时及半小时对齐（Tom HR 1999–2002 与 HH 2003–2013 原生边界已相接）；缺测、数值和物理约束；阴影修复的键、来源、原值、修改值、影响面与非目标恒等；整站不等于单一异常修复。对需要模型的 QBOT、降水、辐射转换核对 CLM/DATM 具体配置与权威文档，不能把每个 30 min 累计量直接当瞬时通量。只在明确允许的独立 shadow 中生成可验证的产品，严格禁止改正式 forcing。不要启动模型/AD400。

数据文献：[JapanFlux2024 产品说明](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.html)；[UCAR 水饱和气压及比湿公式](https://archive.eol.ucar.edu/projects/ceop/dm/documents/refdata_report/eqns.html)。引用精确发行版的源文件和 QC 定义；确认时间和统计覆盖。

## 交付标准

- 继续使用 GitHub 工具读取最新代码与报告；有工作能力时提交可复现的脚本、必要测试、实际结果与 README 更新，回报 commit SHA 和文件 SHA-256。
- 单次 IRIDIS 指令尽量批量、串行、只读并完整保护来源；保证测试真实覆盖缺失、重复、哈希改变、时间/单位边界、分组和非目标数据不变。不要输出大量原始数据给 GitHub。
- 每次区分真实已运行、本地合成测试、拟执行；引用运行目录和哈希。不能说“已直接读到 IRIDIS 文件”除非确有访问。
- 最终针对每站每变量给出明确状态与证据、风险/未决项、真实修复与未批准 shadow 的区别；有待批准的数值请集中成一个可审查清单。不得以“没有异常旗标”代替完整 QC，不得把 45 字段 HOLD 以外的 Tom/Tgf 隐藏掉。

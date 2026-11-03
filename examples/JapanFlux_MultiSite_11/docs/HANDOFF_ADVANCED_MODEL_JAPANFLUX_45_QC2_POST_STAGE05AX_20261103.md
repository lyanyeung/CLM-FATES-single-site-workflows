# JapanFlux MultiSite 11 — 高级模型交接指令（Stage05AX 后，2026-11-03）

## 一、仓库与范围

**代码仓库：** https://github.com/lyanyeung/CLM-FATES-single-site-workflows

**子项目：** https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/examples/JapanFlux_MultiSite_11

**主索引：** [README.md](../README.md)

**本次审核实际结果：** [Stage05AX 五站原始 QC0/QC1 邻近值审计](STAGE05AX_ACTUAL_FIVE_SITE_45_QC2_QC0_QC1_NATIVE_NEIGHBOR_AUDIT_PASS_20261103.md)

**此前独立 ERA5-Land 审核：** [Stage05AV 45/45](STAGE05AV_ACTUAL_45_OF_45_INDEPENDENT_CONTEXT_8_OF_8_OUTSIDE_20261102.md)；[Stage05AW 原始 45 条统一台账](STAGE05AW_ACTUAL_45_OF_45_UNIFIED_EVIDENCE_PASS_NEXT_STAGE05AX_20261103.md)。

**生产相关源仓库，勿混淆：** https://github.com/lyanyeung/Non-Competition-CLM-experiment 。本轮工作严格聚焦 JapanFlux 原始 JPF 气象强制数据与科学审计，**不触碰非竞争模拟，也不修改 PFT**。

## 二、迄今实际执行并验证的结果

- 源数据均是 JPF 原始 ZIP 中的 `FLUXMET_HH`、原始 BIF/README 和原始 QA/QC，项目里 `sites.tsv` 固定站点/版本；真实原始 ZIP 位于 IRIDIS6，**不在 GitHub 中**。
- 原始选用 `F` 等于同版本下采样 `_ERA` 且 `F_QC=2` 的异常变量记录 **45 条**、站点×原始半小时点 **35 个**：JP-Fjy6、JP-Khw11、JP-Yms10、JP-Tef4、JP-Tmd14；变量 PA27、TA6、LW_IN12。
- Stage05AL/AT/AU/AV/AW **实际 PASS**：45/45 原始源值与独立 ECMWF ERA5-Land *网格逐小时参考范围* 对照，45/45 均超出定义的参考范围。这仅说明强烈的异常证据，**不是可信的塔上半小时替代值**。原先 22 项为 `STRONG_CONTEXT`，其余 23 项为 `CONTEXT_ONLY`（Yms5 + Tef/Tmd18）。**45/45 仍 SCIENCE HOLD，批准修复值=0**。
- Stage05AX **五站运行与最终聚合实际 PASS**：原始源 `FLUXMET_HH` 扫描共 1,911,928 HH；±24 小时的同变量 QC0 实测邻近锚点**45/45 都没有双侧 QC0**；全部审慎分类 `LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED`。
- Stage05AX 站点统计：Fjy 6 个字段/6 个原始半小时、368160 HH、最长相关 QC2 来源段 262944；Khw 11/7、385728 HH、最长 385728；Yms 10/8、420768 HH、最长 325824；Tef 4/4、403200 HH、最长 315223；Tmd 14/10、333072 HH、最长 333072。
- **非常重要：长 QC2 连续段是“`F` 的来源类别”（ERA downscaled）持续时间，不是物理异常持续时间。** 例如 JP-Tmd 的 PA 全部 333072 HH 均为 QC2 来源，但识别的具体异常 PA 仅 9 条。JP-Khw PA 385728 HH 同理。
- 原始站点时区差异：JP-Fjy/Khw/Yms 的原始 README 为 local standard time without DST，`UTC_OFFSET=9`；JP-Tef/Tmd 原始 75 行 README 明确写 **local solar time**，与 BIF `UTC_OFFSET=9` 存在未解决的源时间约定冲突。现有 JP-Tef/Tmd `native−9h` 映射是操作员选择的 `JST_UTC_PLUS9_DIAGNOSTIC_ONLY` **诊断假设，不能表述为已证实**。
- QC0 是所选产品字段所标记的实测，QC1 是已填补值，QC2 是下采样 ERA 来源：QC1 / QC2 **都不可冒充独立的塔测 QC0**。
- **未修改任何原始 ZIP、forcing、PFT、CLM-FATES 模型或 Slurm/AD400 作业。**

## 三、必须先阅读并核对的代码、报告和实际输出

1. [`examples/JapanFlux_MultiSite_11/README.md`](../README.md)、[`sites.tsv`](../sites.tsv)、[`scripts/stage05/05ax_45_original_JPF_QC0_QC1_neighbor_and_QC2_run_READONLY.py`](../scripts/stage05/05ax_45_original_JPF_QC0_QC1_neighbor_and_QC2_run_READONLY.py)；Stage05AX 固定 Git blob `7cc202ff9a15fd4f78bba84d33cf65faeb4b3e07`，已在真实 IRIDIS6 上通过。
2. [Stage05AX 五站实际报告](STAGE05AX_ACTUAL_FIVE_SITE_45_QC2_QC0_QC1_NATIVE_NEIGHBOR_AUDIT_PASS_20261103.md)、[Stage05AW 实际统一证据](STAGE05AW_ACTUAL_45_OF_45_UNIFIED_EVIDENCE_PASS_NEXT_STAGE05AX_20261103.md)、[Stage05AV 独立气象来源](STAGE05AV_ACTUAL_45_OF_45_INDEPENDENT_CONTEXT_8_OF_8_OUTSIDE_20261102.md)。
3. IRIDIS6（**GitHub 中没有这些生成结果文件**）：
```text
/home/ly3n24/japanflux_stage05ax/aggregate_20261103T065006Z/stage05ax_45_original_QC2_native_source_quality_anchor_feasibility_NO_REPAIR.tsv
/home/ly3n24/japanflux_stage05ax/aggregate_20261103T065006Z/stage05ax_45_original_QC2_five_site_QC0_QC1_neighbor_HOLD_summary.json
/home/ly3n24/japanflux_stage05ax/site_results/JP-Fjy/
/home/ly3n24/japanflux_stage05ax/site_results/JP-Khw/
/home/ly3n24/japanflux_stage05ax/site_results/JP-Yms/
/home/ly3n24/japanflux_stage05ax/site_results/JP-Tef/
/home/ly3n24/japanflux_stage05ax/site_results/JP-Tmd/
/home/ly3n24/japanflux_stage05aw/run_20261103T061649Z/stage05aw_45_original_JPF_F_ERA_QC2_source_vs_ERA5L_independent_context_ALL_HOLD.tsv
/home/ly3n24/japanflux_stage05aw/run_20261103T061649Z/stage05aw_45_original_JPF_QC2_35_source_native_times_REPAIR_READINESS_NOT_APPROVED.json
/home/ly3n24/japanflux_stage05av/run_20261102T232904Z/stage05av_45_original_source_QC2_independent_hourly_context_completed_ALL_HOLD.json
/home/ly3n24/japanflux_stage05as/downloads/
```
所有路径为真实操作员报告中的固定路径；除非已通过工具取得远端连接，**不能声称自己已经实际读取或修改 IRIDIS6 文件**。必要时提供短小、可复制的 IRIDIS6 只读指令，由操作员执行并返回真实日志。

## 四、下一阶段任务：Stage05AY 科学修复可行性研究

**目标：** 对已锁定的 **45 条异常变量字段 / 35 站点×原始半小时点**，从“异常有独立证据”推进到“可辩护的、仅在 shadow 中的候选修复方法设计”。优先执行**只读**的原因归类/短时局部评估，而不是批量替换。

1. **原始同一变量相邻数值的物理连续性：** 在准确的原始本地时间轴上读取异常前后至少 ±24h `F` 值及其 QC0/1/2、`_ERA`、若存在的原始传感器/MDS 字段，量化局部突然偏差、缺测、左右桥接、非异常 QC2 值连续性、异常区间长度。**明确区分“异常数值长度”与“QC2 来源类别长度”。** 若使用相邻 QC2 非异常数值提出小缺口插值，也只能称 `same-release ERA-derived continuity shadow`，不能叫 QC0 塔测插值。
2. **跨站点同步异常**：2005-08-12、2011-12-17、2022-04-09 的类似离谱气压/气温/长波值出现在多个站点，研究是否为相同原始产品处理/下采样/边界填补错误、相同时间标签或同版本 ERA 数据处理问题；这目前只是**待检验假设**，不可宣布已证实。
3. **独立 ERA5-Land 支撑**：复用已下载、原始 ZIP SHA 可验证的逐小时 ERA5-Land `t2m`（K→℃）、`sp`（Pa→kPa）、`strd`（原始时间序列已按小时解累积，J m⁻² /3600→W m⁻²，**不可再次差分**）。注意产品小时结束时间与塔半小时时间的配准、最近网格与站点海拔、相邻时刻与其他变量物理约束。不可将网格小时值直接视作塔的实测 30 分钟替代值。
4. **时间约定**：对 Tef/Tmd 显式标注 `OPERATOR_JST_PLUS9_HYPOTHESIS / ORIGINAL_README_SOLAR_CONFLICT`，如有可靠原始发布文档再尝试消歧；**不可无声地宣称已证明 UTC+9**。
5. **shadow-only 方法比较**：若证据支持，可分别设计 (a) 邻近非异常 QC2 源值构建的短时局部连续性候选，(b) 独立 ERA5-Land 的受限偏差订正/小时→半小时上下文辅助候选，(c) 保持原值 HOLD 以待人工审核；逐事件评估边缘跳变、跨变量 T/PA/LW 物理范围、来源优先级、和所有非异常原始行恒等性。**初期仅提出方法/候选列表，不写入生产 forcing**。
6. **最小可复现交付**：在 GitHub 的 `examples/JapanFlux_MultiSite_11/scripts/stage05/` 增加 Stage05AY 的只读检查脚本 + 自检，在 `docs/` 增加科学评估/审批清单，并更新 README；锁定具体 Git commit + `git hash-object` SHA；提供适合手机/IRIDIS 粘贴的一段 Bash。每次先语法/自检/来源 SHA，再真实只读运行；出现异常必须停住诊断，**不要绕过 gate 或编造 PASS 日志**。

## 五、严格禁止

- 不得改动原始站点 ZIP、原始 FLUXMET/原始 QC 字段、生产 forcing、CLM-FATES cases、Slurm/AD400；不得重做已确认完成的 PFT；不得默认自动将所有 QC2 当作坏值，或整段 QC2 运行时段当异常时段。
- 不得把已审完的 45 条的源数据外部参考当作已经批准的修复；不得根据“不存在 ±24h QC0”就断定远处/其他源不存在 QC0；也不得假称 GitHub 存放了 IRIDIS 原始数据。
- 没有明确科学审批前，**45/45 保持 SCIENCE HOLD、0 approved replacement**。
- 不要重复下载已经核验的独立 CDS 文件；优先重用已有 ZIP 和 SHA 审核报告。不要自动提交大规模 Slurm 计算。

## 六、建议先交付给操作员的第一批结果

**先完成只读 Stage05AY：** 汇总每个实际数值异常 episode 的半小时长度、同产品非异常 QC2 邻居取值、源 `F` 与 `ERA` 一致性、是否存在 MDS 原始可用字段、跨站/跨年相同失真模式、可行候选方案等级（`QC2_SHADOW_BRIDGE` / `EXTERNAL_ERA5L_ASSISTED_SHADOW` / `HOLD_MANUAL`）。第一批结果不需要修复后的生产强制数据或 AD400 模型试跑。

最后回复请明确：① 已验证事实 ② 尚待核验的假设 ③ 仓库实际更改及 commit/SHA ④ 下一条操作员应运行的 IRIDIS6 命令。

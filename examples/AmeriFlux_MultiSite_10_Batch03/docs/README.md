# AmeriFlux 第三批文档与代码

[第三批总说明](../README.md) · [完整站点清单](../sites.tsv)

## US-Me2 四条湿度记录：下一步 Stage14b

原始四条实测温度（QC0）与 MDS VPD（QC1）组合产生约 **−10% 至 −14% RH**，原始 RH 全部缺失；配套原始 ERA 的 T/VPD 组合也无效。保留实测温度，进入四条湿度的来源与物理审核。[具体证据和 Stage14b 说明](US_ME2_FOUR_HUMIDITY_REVIEW_20261026.md) · [正式代码](../scripts/stage14/14b_US_Me2_four_humidity_REVIEW_ONLY.py) · [docs 内完整代码副本](code/14b_US_Me2_four_humidity_REVIEW_ONLY.py)。

Stage14b 复核既有 Stage10b 封存候选和外部文件 SHA256，重算候选物理量，输出原始前后 ±24 小时上下文及边界警告。旧 2014 年 ERA5-Land 产品带跨年缓冲，覆盖到 2015-01-03，可供这四个 UTC 2015-01-01 中点检查。代码已经过本地回归测试，**Stage14b 集群执行与真实候选数值审核尚未完成；没有修改 forcing 或批准修复**。若 `--run` 成功，贴回四条候选和边界表继续审核。

两份 Stage14b 代码 SHA256 均为 `d970de8a11672f6d73e86a2645934e776b6d4797ce89c57c9f2fa387c98560ba`。Stage14a 已完成，无需因开展湿度审核而重复运行。

## US-Me2 时钟问题：集群已核实

**2026-10-26 19:35 UTC，Stage14a 已在 IRIDIS6 执行通过。** US-Me2 的时钟元数据阻塞已解除，采用全年固定 `UTC_OFFSET=-8`，不加夏令时。依据为独立站点 BIF 的 `AMF-BIF!A767:E767`、`GROUP_ID=12976`，以及官方当地标准时规范。该 BIF 是独立补充元数据，不是原始 4-6 ZIP 内文件。

| 项目 | 已核实结果 |
| --- | --- |
| 原始 FULLSET HH | 368,160 条；SHA256、完整时间轴与 30 分钟区间通过 |
| 配套 ERA5 HH | 753,840 条；SHA256、完整时间轴与 30 分钟区间通过 |
| 原始 Stage07 来源 | 路径与 SHA256 匹配 |
| Stage11a 原始记录 | 4/4 条 sealed receipt 与原始 CSV 行号/时间匹配 |
| 时钟处理 | UTC = 当地标准时 + 8 小时；区间中点另外加 15 分钟 |
| 湿度处理 | 尚未修改，4 条记录进入湿度来源、物理一致性与连续性检查 |
| 模型准入 | `humidity_repairs=0`、`DATM=FALSE`、`jobs=0` |

这里的“4 条”指四条湿度事件记录，不是四项缺失的时间元数据。

| 原始 CSV 行号 | 当地开始时间 | UTC 中点 |
| ---: | --- | --- |
| 227899 | 2014-12-31 20:30 | 2015-01-01 04:45 |
| 227900 | 2014-12-31 21:00 | 2015-01-01 05:15 |
| 227901 | 2014-12-31 21:30 | 2015-01-01 05:45 |
| 227902 | 2014-12-31 22:00 | 2015-01-01 06:15 |

**跨年须保留：**原始数据属于当地 2014 年，外部数据应覆盖 UTC 2015-01-01 04:30–06:30。后续湿度分析必须按 UTC 时间核对实际覆盖，不能只按当地年份选择外部文件。

集群报告目录：

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage14a_US_Me2_documented_clock_20261026T193531Z_985d2919
```

## 证据、结果与可运行代码

- [时钟证据、适用范围、集群核实结果及下一步](US_ME2_CLOCK_EVIDENCE_20261026.md)
- [用户实际集群输出的结构化记录](US_ME2_CLOCK_CLUSTER_OPERATOR_RESULT_20261026.json)：转录用户提供的终端输出，集群报告文件 SHA256 未提供。
- [已执行的本地原始 ZIP 检查记录](US_ME2_CLOCK_LOCAL_SOURCE_VERIFICATION_20261026.json)
- [docs 内完整独立可运行代码副本](code/14a_US_Me2_documented_clock_READONLY.py)
- [正式 scripts 目录中的相同代码](../scripts/stage14/14a_US_Me2_documented_clock_READONLY.py)
- [回归测试](../tests/test_me2_clock.py)

两份 Python 代码内容完全一致，均不依赖自身在仓库中的相对位置，可单独下载执行。SHA256：

```text
5ea8ee372c733edb123e6cc029be2442a090e9bed1d252757fb831eeca4cbc89
```

以 `scripts/stage14/` 为维护源；更新时同步 `docs/code/` 副本和校验值。`docs` 副本保存完整代码，不是跳转链接或需要另外下载模块的包装程序。

## 如需复核：在 IRIDIS6 Login 执行

**已有上面所列成功报告，无需重复运行。** 以下用于之后的只读复核，不提交作业，也不改变 forcing。使用现有含 `pandas` 的 `clm_fates_env` 环境。

```bash
(
  set -euo pipefail
  CHECK="$HOME/check_US_Me2_clock_stage14a.py"
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/AmeriFlux_MultiSite_10_Batch03/docs/code/14a_US_Me2_documented_clock_READONLY.py" \
    -o "$CHECK"
  printf '%s  %s\n' \
    "5ea8ee372c733edb123e6cc029be2442a090e9bed1d252757fb831eeca4cbc89" \
    "$CHECK" | sha256sum -c -
  python3 -B "$CHECK" --self-test
  python3 -B "$CHECK" --check
)
```

成功摘要：

```text
ME2 CLOCK SUMMARY CLUSTER_SOURCE_AND_FOUR_CLOCK_HOLDS_VERIFIED UTC_OFFSET=-8 DST=FALSE legacy_events=4 humidity_repairs=0 DATM=FALSE jobs=0
```

`--check` 不写文件。只有需要新的证据报告时才用 `--run`，它仅新增独立报告目录。若检测到多个 Stage11a 目录，使用 `--stage11a /原始已封存报告的绝对路径` 明确指定。

## 下一步与历史记录

下一步检查这四条原始 TA/VPD/RH/气压及 QC、配套 ERA 和已有 ERA5-Land 在对应 UTC 时段的覆盖，再检验湿度物理一致性与前后连续性。时钟通过不代表湿度数值已修复，也不代表完整 forcing、PFT/土壤或模型运行已准入。2020 年火灾与植被历史仍需单独处理。

历史文档与 sealed reports 保留其执行时状态。旧文档中的 US-Me2“UTC−8 仅为假设”“时钟仍缺证据”已被本次 Stage14a 结果取代。其他站点的进展请参阅第三批总说明及对应阶段文档；本页不是新的十站完整 forcing 盘点。

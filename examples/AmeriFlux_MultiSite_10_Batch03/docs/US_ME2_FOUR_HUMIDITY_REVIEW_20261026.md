# US-Me2 四条湿度记录：Stage14b 只读审核

## 已确认的原始数据问题

Stage14a 已在 IRIDIS6 通过，固定 UTC−8、无夏令时，四条记录的行号和时间均已核实。PR #11 已于 **2026-10-26 19:40:52 UTC** 合并，merge commit 为 `b9e6b3a793b9d64c84f2fd7a3a4d21602e57f263`。合并前确认无冲突，合并后核对 main 的脚本、docs 代码副本和 README；后续 main 中这些证据文件仍保留。

读取原始 4-6 ZIP 的 FULLSET HH 成员，并确认其 SHA256 仍为 `5b29b04da37960a1640c19b75fc2a8ffbffd703ada89ba6c36689d86f834ae3e`，得到：

| 原始 CSV 行号 | 当地开始时间 | 实测 TA_F（°C） | VPD_F（hPa） | 用 TA_F/VPD_F 算出的水面 RH（%） |
| ---: | --- | ---: | ---: | ---: |
| 227899 | 2014-12-31 20:30 | -14.463 | 2.202 | -9.957 |
| 227900 | 2014-12-31 21:00 | -14.700 | 2.214 | -12.729 |
| 227901 | 2014-12-31 21:30 | -14.817 | 2.226 | -14.435 |
| 227902 | 2014-12-31 22:00 | -14.727 | 2.237 | -14.153 |

四条 TA_F 均为 **QC=0**，VPD_F 均为 **QC=1，且等于 VPD_F_MDS**。原始 RH 全部为缺测 `-9999`。负 RH 是变量组合的物理不一致，不是实测负湿度。保留实测温度，不通过调高温度、VPD 归零或任意 RH 下限消除错误。PA_F=86.681 kPa、QC=2，是已有 ERA 填补气压，不应称为实测气压。

配套原始 `TA_ERA` 与 `VPD_ERA` 在这四条记录也算出负 RH（约 -2.955%、-4.021%、-3.800%、-3.588%）。因此不能直接采用原发布包的 `VPD_ERA`。邻近的原始 MDS VPD 也存在物理问题，四条数值通过并不能证明与现有研究 forcing 的边界连续。

## Stage14b 做什么

[正式脚本](../scripts/stage14/14b_US_Me2_four_humidity_REVIEW_ONLY.py) 与 [docs 中相同的完整代码副本](code/14b_US_Me2_four_humidity_REVIEW_ONLY.py) 执行以下只读检查：

1. 原始 FULLSET/ERA 字节 SHA256 与已执行 Stage14a 四条行号、当地时间和 UTC 中点匹配。
2. 原 Stage10b 的 `humidity_external_sensitivity_1924.csv` 及封存输出 SHA256 校验，严格选择这四条 US-Me2 记录。
3. 核对旧试算的 UTC−8、中点和保留温度/气压，与当前已核实的时钟及原始数据一致。
4. 校验旧试算引用的真实 ERA5-Land 产品文件 SHA256。用原 Stage10b 已记录的 grid T/dewpoint 重新计算相对湿度与绝对水汽压两种候选，并与旧表逐值比较。本步骤**不重新解码 NetCDF**，不把历史试算变成新观测。
5. 检查水面 RH/QBOT/VPD 物理范围、冰面过饱和、塔站/网格温差，以及“四条替换假设”的五个相邻边界。原邻居无效或候选无效时继续 HOLD，不能误报生产 forcing 连续性已通过。
6. 导出前后 ±24 小时的原始塔站及配套 ERA 上下文、有效 QC0 T+VPD 锚点及超过 5°C/30min 的温度变化，供审核。这些温度变化只是提示，不自动判错或修改实测温度。

实际 UTC 中点为 **2015-01-01 04:45、05:15、05:45、06:15**。原 Stage09b/09f 的 **2014 年**外部请求包含缓冲，覆盖至 **2015-01-03 23:00 UTC**，因此产品目录名为 2014 不代表它缺少这四条 UTC 2015 时间。本次复用原来已封存的数据，不发起新下载。Stage14b 核对历史中点及对应文件字节，后续正式采用任何新来源仍须检验其实际时间轴。

## 执行与当前状态

Stage14b 已通过本地自检与回归测试，**尚未取得 IRIDIS6 Stage14b 执行输出**。当前仍无湿度修复批准、无 forcing 修改、无模型作业提交。自检使用合成 grid 数据，不是四条真实外部气象候选值。

在 IRIDIS6 的 `clm_fates_env` 中执行已下载脚本：

```bash
python3 -B 14b_US_Me2_four_humidity_REVIEW_ONLY.py --self-test
python3 -B 14b_US_Me2_four_humidity_REVIEW_ONLY.py --run
```

`--check` 只输出检查结果，不写文件。`--run` 只新建 `reports/stage14b_US_Me2_four_humidity_REVIEW_ONLY_*/`，包含四条候选、原始上下文、假设边界和 SHA256 receipt。不会创建完整 forcing 候选。若发现多个旧 Stage10b 报告，使用 `--stage10b /原始封存报告的绝对路径` 指定，不按修改时间猜测。

成功摘要仅表示审核程序完成：

```text
ME2 FOUR HUMIDITY SUMMARY rows=4 clock_documented=TRUE forcing_changes=0 approvals=0 jobs=0
```

将实际四条候选数值、冰面/温差警告和边界结果交回审核，再决定后续新的独立 forcing 候选。原来的已封存报告、QC0 温度和其他站点不受影响。

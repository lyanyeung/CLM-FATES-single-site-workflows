# Stage05BZ：剩余全部 HOLD 单元格的候选值与一次性审批包（2026-11-04）

**本文所有候选值均为 PROPOSED / NOT_APPROVED。** 没有写入任何 forcing、原始文件、案例、Slurm 或 AD400。这里的规则是此前审阅包（D3–D13）中的建议，加上本轮新发现的 D9b 和 D14。

## 1. IRIDIS Stage05BX 实际结果（操作员日志）

- 操作员从本地 WSL 上传了 JapanFlux2024 JP-Yms 包，本地与 IRIDIS 的 SHA-256 均为 `a112e865…`。
- Stage05BX 在 `login6003`（Python 3.12.13）运行，运行目录为 `/home/ly3n24/japanflux_stage05bx/run_20261104T053910Z_1424603`，控制台日志 SHA-256 为 `a9f2eb29…`。
- self-test 与 13 项单元测试通过。
- **两项检查均为 true**：D2 恰为 5,099 个单元格；影子表整数指纹 `2365a734…` 与本地一致。12 个 gzip 文件连压缩后的字节也与本地完全相同。

## 2. 更正：Yms 降水来源

核对时发现，JapanFlux2024 Yms 的 `P_F` 虽然标为 QC0，但**逐月等于其偏差校正 ERA5（`P_ERA5`）**，并非雨量计实测。例如 2007 年 8 月 `P_F`=`P_ERA5`=29.7 mm，而雨量计 `P_RAIN_1_1_1`=107.0 mm；2009 年 `P_F` 几乎每个半小时都有降水。真正的雨量计序列在 ALLVARS 的 `P_RAIN_1_1_1` 中：2001–2023 年绝大多数年份完整，缺测主要在 2000 年（4,367 个半小时）和 2017 年（3,141 个），年总量 896–1,767 mm。

为符合您批准的“Yms 用雨量计实测”，05BW 已改为：有 `P_RAIN_1_1_1` 时用雨量计（412,912 个半小时，占 98.1%），缺测时用 `P_F(t+1h)/3.6`（7,856 个）。年均 **1,382 mm**，发表值为 1,384 mm。其余 11 张影子表逐字节不变。上一轮 Yms 影子表（`3ff7a8a6…`）作废。此前文档中“Yms 为 QC0 雨量计实测”的说法是我的推断错误，已在此更正。

## 3. D8：45 个伪影单元格的逐组候选值

C3 纠正 ERA 时间后，伪影位于原位置提前 1 小时的单元格。候选值是您选定的“ERA5-Land 格点 + 同发行 QC2 背景中位残差”，取 05BT 在 600 分钟偏移下的结果（IRIDIS 打印值，05BT 表 SHA-256 `070732bc…`；IRIDIS 运行 05BZ 时逐值核对）。

| 组（原起点） | 540 分钟候选（原方案） | **600 分钟候选（建议）** | QC2 离散度 540→600 | 最大跳变 540→600 |
|---|---|---|---|---|
| Fjy PA 2005-08-12 02:30 | 89.925, 89.929, 89.952 | **89.954, 89.945, 89.931** | 0.016→0.007 | 0.060→0.058 kPa |
| Fjy PA 2011-12-17 06:30 | 89.994, 90.025, 90.055 | **89.946, 89.975, 90.006** | 0.042→0.020 | 0.083→0.081 |
| Khw LW 2005-08-12 02:00 | 406.86 ×2 | **401.34 ×2** | 3.94→1.21 | 5.92→1.27 W m⁻² |
| Khw PA 2005-08-12 02:30 | 97.770, 97.790, 97.827 | **97.772, 97.775, 97.777** | 0.015→0.012 | 0.053→0.067 |
| Khw PA 2011-12-17 06:30 | 99.092, 99.122, 99.138 | **99.023, 99.055, 99.099** | 0.018→0.012 | 0.079→0.044 |
| Khw TA 2005-08-12 02:30 | 23.90, 23.84, 23.81 | **23.72, 23.60, 23.50** | 0.98→0.25 | 0.86→0.55 °C |
| Tef LW 2011-12-17 06:00 | 204.18 ×2 | **209.90 ×2** | 5.49→3.12 | 1.10→5.39 |
| Tef LW 2022-04-09 02:00 | 257.41 ×2 | **270.29 ×2** | 12.54→5.24 | 14.62→14.92 |
| Tmd LW 2005-08-12 02:00 | 401.90 ×2 | **398.76 ×2** | 5.37→1.70 | 6.59→3.54 |
| Tmd PA 2005-08-12 02:30 | 98.982, 98.984, 98.991 | **98.997, 98.994, 98.993** | 0.024→0.011 | 0.022→0.020 |
| Tmd PA 2011-12-17 06:30 | 98.972, 98.998, 99.028 | **98.934, 98.959, 98.979** | 0.024→0.013 | 0.076→0.050 |
| Tmd PA 2022-04-09 02:30 | 99.098, 99.099, 99.114 | **99.146, 99.120, 99.108** | 0.018→0.014 | 0.134→0.086 |
| Tmd TA 2005-08-12 02:30 | 19.28, 19.22, 19.16 | **19.12, 19.06, 19.00** | 0.25→0.17 | 0.31→0.31 |
| Yms LW 2005-08-12 02:00 | 426.52 ×2 | **418.83 ×2** | 4.31→0.79 | 9.85→5.30 |
| Yms LW 2011-12-17 06:00 | 264.09 ×2 | **243.38 ×2** | 3.17→1.60 | 15.64→18.30 |
| Yms PA 2005-08-12 02:30 | 98.241, 98.251, 98.274 | **98.258, 98.261, 98.258** | 0.043→0.030 | 0.023→0.018 |
| Yms PA 2011-12-17 06:30 | 99.047, 99.079, 99.105 | **98.966, 98.993, 99.031** | 0.062→0.054 | 0.076→0.038 |

600 分钟时，QC2 背景离散度在 **17/17 组**都更小，最大跳变在 13/17 组更小。跳变变大的 4 组都在单一时间步的自然变化范围内：Khw PA 2005 为 +0.014 kPa；Tef LW 两组和 Yms LW 2011 的 LW 两侧本身就相差 13–17 W m⁻²，属于云量变化。**建议批准 600 分钟候选。**

## 4. 全部候选规则（一次批准）

| 编号 | 规则 | 单元格 | 依据与风险 |
|---|---|---:|---|
| D8 | 伪影 PA/TA/LW → 600 分钟格点 + QC2 中位残差 | 45 | 见第 3 节 |
| D13 | 其他伪影单元格 → 用相邻非 HOLD 值线性桥接 | 43（WS 12、VPD 9、P 18、夜间 SW 4） | 时长仅 1–1.5 小时；WS/VPD 原为半值/零值伪影 |
| D7 | 风速卡值（QC0，≥12 h 恒定且 <0.5 m/s）→ 同发行 `WS_ERA(t+1h)` | 5,225（Api 560、Khw 48、Tak 2,592、Tef 597、Tmd 1,428） | 疑似风杯冻结；ERA 风速平滑，但优于恒定低值 |
| D11 | Tef 2023 年实测 PA → `PA_ERA(t+1h)` | 16,292 | 实测比 ERA 高 1.34 kPa，两套产品中都有，属传感器偏移；对 q 的影响 <1.5% |
| D9 | JPF 中 VPD≥es → 用同发行 ERA 的 RH（t+1h）在塔测 TA 下重建 VPD，RH 下限 1% | 23（Fjy 7、Tef 1、Yms 15） | 与 FLUXNET_MultiSite_8 已用的做法一致 |
| D9b | Tom/Tgf 中 VPD≥es → 用 JapanFlux2024 ERA5 填补的 RH | 4 行（Tgf 2002-01-03 06:00–07:30） | 新发现：−1.5 °C 下 RH 仅 10–14%，VPD 超过饱和值 |
| D14 | Tom/Tgf 高太阳（天顶辐射 ≥200 W m⁻²）时 SW<−5 → JapanFlux2024 ERA5 填补 SW | 11（Tgf 2021-02-26 10:00–15:00） | 新发现：连续白天负值，属传感器故障；低太阳和夜间的负值由构建步骤截零 |
| D4 | Tgf 2003-12-31 23:30 的 TA/RH/PA → 线性桥接（1.622 °C、89.65%、100.61 kPa），VPD 由二者计算（0.711 hPa）；2015-12-15 14:30 的 SW → JapanFlux2024 ERA5 填补值 | 5 | 主记录器整行置零；SW 为恢复期的单通道负值 |
| D6 | Spp 2009-07-15 08:30 的 P=60.5 mm → 0 | 1 | 同时刻 SW 148 W m⁻²、RH 92.5%、ERA 为 0 |
| D3a | Tgf RH>100 → RH=100、VPD=0 | 9,493 行 | 主要是约 1% 的饱和过冲；T≥0 °C 时与 DATM 的截断等价 |
| D3b | Tom 2011–2013 年排除出 forcing 期（Tom 用 1999–2010 年） | 105,216 个 RH/VPD 单元格（数值保留） | RH 传感器自 2011 年偏湿 |

**不作改动、仅记录：**
- Khw 2008-08-17 18:00 的 52 mm/30 min：雷暴特征完整，保留。
- Tgf 夜间和低太阳时的负短波（23,073 个）：DATM 构建时 `FSDS=max(SW,0)`。
- Tmd 降水：按 D1 用原始 ERA5，比发表值低约 25%；要改用实测，需要获取正确的 JapanFlux2024 JP-Tmd 包（新下载，需您同意）。

**批准方式**：回复“批准 Stage05BZ 全部建议”即可；如有例外，写明编号，例如“D7 不批准”。批准后，我会把候选标签改为 APPROVED，生成最终的 forcing 前置表，再进入 DATM 构建与验证。

## 5. 本地运行与 IRIDIS 复现命令

本地（SHA 一致的原件）：05BW v2 指纹 `ea5951e51601a0386fb83056dc1102eae3ee8f6e6d4af333c4fe6aab6d1acc24`；05BZ 指纹 `9bc3512d077992d502a0dc263e12ddedcb1192c48ef2a82afaef359b384aae29`；审批清单 `approval_list_NOT_APPROVED.tsv`（145,855 行，SHA-256 `5a7d855167097014f9ff97de61ed579e4ea995e7ac50854905cd4af881af4b9e`），存放在 WSL `~/jp11_local_runs/05bz_final/`，不上传 GitHub。

IRIDIS 命令（串行、只读；重跑 05BW 的 Yms 更正，再运行 05BZ，并用 05BT 表逐值核对 D8）：

```bash
set -euo pipefail
C=07e5a602ddc55855fb393db9385e1ad8e6088911
B="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$C/examples/JapanFlux_MultiSite_11/scripts/stage05"
mkdir -p "$HOME/japanflux_stage05ca"; D="$HOME/japanflux_stage05ca/code_${C:0:12}"
[ -e "$D" ] && { echo "STOP: $D already exists"; exit 1; }; mkdir "$D"
for f in 05bq_four_site_humidity_and_special_shadows_READONLY.py 05br_nine_site_jpf_forcing_variable_qc_READONLY.py 05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py 05bw_decided_corrections_shadow_tables_READONLY.py 05bz_proposed_resolution_of_hold_cells_READONLY.py 05ca_iridis_readonly_batch_05bw_05bz.sh test_05br_nine_site_forcing_variable_qc.py test_05bs_tom_tgf_forensics.py test_05bw_decided_corrections.py test_05bz_proposed_resolution.py; do
  curl -fLsS "$B/$f" -o "$D/$f"
done
(cd "$D" && sha256sum -c - <<'EOF'
12ff4ba55b6ff1b80d139815bd9d333c69199d083951229dd18eaf4181d31dd2  05bq_four_site_humidity_and_special_shadows_READONLY.py
67ecfb0dbfeda1599986de7d995aadf581570022450b5c5055fae6cc8a1f30cb  05br_nine_site_jpf_forcing_variable_qc_READONLY.py
83555cd1b1ec81c6b42410fa5cee1327292862b104f03b4b50afda57e222baa2  05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py
444746ed0751fbb2f0bab71b2a3654ac3c7dbe9ba4e4d2719ce78ca6fda18fdc  05bw_decided_corrections_shadow_tables_READONLY.py
8ef4b3826383005e16304f4447fce5648b1900da1bba68afeba5b8dbaf34ebbc  05bz_proposed_resolution_of_hold_cells_READONLY.py
98d91f9063d79f966cb31cf4ca2ecda4f68b87bd4c6517e2746ec2eaf1a32114  05ca_iridis_readonly_batch_05bw_05bz.sh
2d485fe31d4fdc46b1df3d214da46fdb0056f958a0e1408c33bdf6b65b970dd7  test_05br_nine_site_forcing_variable_qc.py
a57268662f9d2fe8cb5797ff1d630bf127814c3ba6090df1435e6d84223b7ccf  test_05bs_tom_tgf_forensics.py
099638f402587e1921fa742af2f2213fec7aba060b7e0a3855c5653ed0e745e4  test_05bw_decided_corrections.py
62e987e92999e703e93400d438aded2a569c51f86c4aee5dabfaef56fada533a  test_05bz_proposed_resolution.py
EOF
)
bash "$D/05ca_iridis_readonly_batch_05bw_05bz.sh" "$D" 2>&1 | tee "$HOME/japanflux_stage05ca/console_${C:0:12}.log"
sha256sum "$HOME/japanflux_stage05ca/console_${C:0:12}.log"
```

## 6. IRIDIS Stage05CA 实际结果（2026-11-05，操作员日志）

运行环境为 `login6003`（Python 3.10.21），运行目录 `/home/ly3n24/japanflux_stage05ca/run_20261105T030635Z_2576314`，控制台日志 SHA-256 为 `51395a5ec69fc1525daea7dce2d4ae656c5111ddcedcad38e1ee8dc97bf916aa`。10 个脚本的 SHA-256 均核对通过，self-test 与 17 项单元测试通过。**4 项检查全部为 true**：

- 05BW 的 D2 恰为 5,099 个单元格。
- 05BW 指纹 `ea5951e5…` 与本地一致。Yms 影子表 `1b79b4df…` 和摘要 `1cdddf21…` 与本地逐字节相同。
- **05BZ 的 45 个 D8 值与 IRIDIS 上的 05BT 偏移表（`070732bc…`）逐值核对一致**。
- 05BZ 指纹 `9bc3512d…` 与本地一致。12 张候选表的 gzip 字节和审批清单 `5a7d8551…` 都与本地相同。摘要文件（`8aff419b…`）与本地不同，原因是其中“D8 已核对”标志在 IRIDIS 为 true、本地为 false，该标志不参与指纹计算。

终检结果与本地相同：只剩 Khw 2008-08-17 那次 52 mm 雷暴（保留），以及 Tgf 的 23,073 个夜间或低太阳负短波（构建时截零）。**所有候选值仍为 NOT_APPROVED，等待用户审批。**

## 7. 审批（2026-11-05）

用户回复“批准，下一步怎么做”，**全部建议获批准**。Stage05CB 已把 145,855 个单元格的标签改为 `APPROVED_20261105_<规则>`，数值不变。见 [Stage05CB/06A](STAGE05CB_06A_APPROVED_TABLES_AND_UTC_DATM_CANDIDATES_20261105.md)。

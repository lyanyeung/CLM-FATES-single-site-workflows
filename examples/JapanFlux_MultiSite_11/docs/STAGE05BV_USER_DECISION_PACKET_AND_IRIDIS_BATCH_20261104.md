# Stage05BV：需要用户决定的事项与 IRIDIS 批量命令（2026-11-04）

证据见 [Stage05BR–BU 报告](STAGE05BR_BU_ELEVEN_SITE_MET_QC_EVIDENCE_20261104.md)。**下列全部候选仍为 HOLD / NOT_APPROVED。** 您批准某项“方法”之后，我才会生成带原值、新值、来源、键、非目标恒等性检查和回滚说明的 shadow 文件；批准方法不等于批准逐个数值，数值清单会在生成后再交您确认。

## A. 需要决定的事项（按对模式的影响排序）

| 编号 | 站 / 变量 | 证据要点 | 选项 | 我的建议 |
|---|---|---|---|---|
| **D1** | Api、Tak、Tmd、Yms 的 P | JPF `P_F` 100% 为 QC2，比独立参考大约 3.6 倍；Api/Tak 半小时尺度精确为 3.600×（原始 ERA5，1 h 后） | A：`P_F(t+1h)/3.6`，即恢复原始 ERA5，不含站点偏差校正；B：采用 JapanFlux2024 `P_F`（Yms 为 QC0 雨量计实测，Api/Tak 与 A 相同）；C：引入外部雨量站（需新数据，未做） | Api/Tak/Tmd 用 A；Yms 用 B（有雨量计时段），缺测时段用 A。A 的年均预计为 Api 约 1,500、Tak 约 2,490、Yms 约 1,400、Tmd 约 1,310 mm（JapanFlux2024 发表值为 1,509/2,483/1,384/1,738）。Tmd 要采用 B，需要正确的 JapanFlux2024 Tmd 包，本地现有的那个是 JP-KaL |
| **D2** | Tom/Tgf 微小负 P 与 VPD，共 5,099 个 | 全部逐格审计通过；P 均对应原始 ERA5 负值，VPD 均出现在 RH=100.0 处 | 批准“`−1e-12<P<0`→0、`−1e-9≤VPD<0`→0”为数值规范化规则 / 不批准 | 批准为规则（物理上没有歧义，影响约 1e-15） |
| **D3** | Tom 2011–2013、Tgf 2016–2020 的 RH | Tom 传感器自 2011 年偏湿，2013 年高湿时段 +12%，2011–2012 年的偏差被读数上限掩盖；Tgf 以约 1% 的饱和过冲为主，2016–2020 年 29.5 m 通道上漂 3–5% | a：只截断到 100%（T≥0 °C 时与 DATM 的处理等价）；b：Tom 的 forcing 期限定为 1999–2010；c：扣除年度偏移（探索性）；d：受影响年份改用 ERA5 RH | Tgf 用 a，并把 2016–2020 年的漂移作为 ±0.5 g/kg 的不确定性记录；Tom 用 b，若需要 2011–2013 年数据则用 d |
| **D4** | Tgf 2003-12-31 23:30 的 TA/RH/VPD/PA；2015-12-15 14:30 的 SW | 主通道整行为 0；SW 为单通道、缺测后的过渡段 | PA 线性桥接 100.61（两侧均为 QC0）；TA 桥接 1.622 °C；RH 桥接 89.65%，对应 VPD 0.711 hPa；SW 可选桥接 90.60 / 按管线默认截为 0 / ERA 校正填补 | PA 用桥接（证据最强）；TA/RH 用桥接；SW 当作缺测处理，用 ERA 校正填补，不用线性桥接 |
| **D5** | Tom 全部实测变量的时钟 | 晴天 SW 晚 50–55 分钟（HH 与 HR 一致），而 Tgf 只晚 1.9 分钟；Tom 的 LW/PA/WS 全来自 ERA | a：保持原样并记录；b：实测变量整体前移 1 h；c：向生产方/PI 核实 | c，同时把 b 作为 HOLD 敏感性，确认前不改动 |
| **D6** | Spp 2009-07-15 08:30 的 P=60.5 mm（QC0） | 同时刻 SW 148 W/m²、PPFD 369、RH 92.5%，ERA 为 0；JapanFlux2024 原始通道也是 60.5（同一雨量计，不独立） | 置零 / 桥接（3.0 与 0.5）/ 保留 | 判为雨量计伪值并置零（HOLD） |
| **D7** | Tak、Tmd、Tef 等的 WS 长时间卡值 | Tak 有 317 段 ≥6 h，最长 59 h，0.12 m/s，冬季；Tmd 有 123 个半小时卡在 0.2 m/s | 规则：QC0 恒值 ≥12 h 且 <0.5 m/s 视为缺测，用 `WS_ERA` 填补（注意 ERA 相位）/ 保留 | 先生成命中清单交您确认，再决定是否采用该规则 |
| **D8** | 45 个原字段 | 方法维持您选定的“ERA5-Land 格点 + QC2 中位残差”；UTC+9 对 18 个 Tef/Tmd 字段有三至四条数据证据；同发行 ERA 相位约滞后 1 h | 等 05BT lag 在 IRIDIS 的结果出来后，逐组决定：维持 UTC+9 候选 / 使用与相位一致的偏移候选 / 桥接 | 先运行批量命令，再逐组审阅 |
| **D9** | Fjy 7 行、Yms 17 行 VPD≥es（MDS/ERA） | 水汽压为负，湿度不可行 | 用同发行 ERA 的 RH 在塔测 TA 下重建 / 截到 `0.99·es` | 用 ERA 的 RH 在塔测 TA 下重建，与项目已有的 FLUXNET_MultiSite_8 做法一致 |
| **D10** | 所有 JPF 站 QC2 段的 SW | 同发行 ERA 的 SW 晚 55–58 分钟；Khw 的 QC2 能量占 14.8%，其余站 0.15–5.8% | 保留 / ERA 来源段前移 1 h | 先对 Khw 做 1 h 前移的 HOLD 敏感性，其他站记录在案 |
| **D11** | Tef 2023 年 PA（QC0） | 比 ERA 高 1.34 kPa，其他年份约 −0.06；JapanFlux2024 中同样存在 | 2023 年改用 `PA_ERA` / 扣除年中位偏移 / 保留（对 q 的影响 <1.5%） | 改用 `PA_ERA`（HOLD） |
| **D12** | 项目级：DATM 时间标签 | 数据标在时段起点；CLM_USRDAT 流为 `linear` 插值、offset 0，CDEPS 在模式步长结束时刻取值 | 维持项目现有约定 / 统一引入 stream offset | 维持现状以保证与其他站点实验可比；如要改，应作为项目级决定，并在 CTSM 中单独验证 |
| **D13** | 49 个伴随单元格（WS 12、VPD 9、P 24、SW 4） | 详见 05BT companion 表 | 用 QC2 相邻值线性桥接 / 保留 | WS 与 VPD 用桥接；P 与夜间 SW 影响可忽略，可保留（HOLD） |

**无需决定、可以直接采用的结论**：Fhk 与 Spp 全部变量在所列限制下通过（Spp 只有 D6 一项）；Api 与 Tak 除 P 外的变量通过；7 个站的 QBOT 用 ONEFlux `qc_auto` 公式反推，Tmd 用 Bolton 公式。

## B. IRIDIS6 一次性只读批量命令

内容：串行执行、`nice -n 10`，先跑全部 self-test 和 17 项合成单元测试，再运行 05BR（9 个 JPF ZIP）、05BS（Tom/Tgf，并逐字节重建 05BP/05BQ）、05BT companion 和 05BT lag（复用已有的 16 个 CDS ZIP、AW 台账和 AY 窗口）。不下载任何数据，不提交 Slurm，不改动任何源文件或 forcing。预计耗时 15–25 分钟，峰值内存约 0.8 GB。

硬性检查（任一失败即停止并退出）：所有输入 SHA-256；05BR 伪影表与本地一致；05BP/05BQ 三份文件逐字节一致；05BT 在 UTC+9 下复现所选 45 值的规范哈希。软性检查（不一致时提示报告，不退出）：05BR/05BS 整数指纹与本地是否一致、05BT companion 表是否一致。

```bash
set -euo pipefail
C=4dfb02319090b95d7ecfaab5b8229e8a7d2bfc50
B="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$C/examples/JapanFlux_MultiSite_11/scripts/stage05"
mkdir -p "$HOME/japanflux_stage05bv"; D="$HOME/japanflux_stage05bv/code_${C:0:12}"
[ -e "$D" ] && { echo "STOP: $D already exists"; exit 1; }; mkdir "$D"
for f in 05az_bulk_existing_era5l_source_clock_audit_READONLY.py 05bp_six_site_meteorology_batch_READONLY.py \
  05bq_four_site_humidity_and_special_shadows_READONLY.py 05br_nine_site_jpf_forcing_variable_qc_READONLY.py \
  05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py 05bt_45_field_companion_artifacts_and_era_lag_sensitivity_READONLY.py \
  05bv_iridis_readonly_batch_05br_05bs_05bt.sh test_05bp_six_site_batch.py test_05bq_four_site_humidity_and_shadows.py \
  test_05br_nine_site_forcing_variable_qc.py test_05bs_tom_tgf_forensics.py test_05bt_companion_and_lag.py; do
  curl -fLsS "$B/$f" -o "$D/$f"
done
(cd "$D" && sha256sum -c - <<'EOF'
14909c294dea5ed17a9e0f3981a9ca2900b2ee8698dcf45902588fb0179f23cc  05az_bulk_existing_era5l_source_clock_audit_READONLY.py
130bda27c320084cf61dc57fc61e1ff2055b3480cb54722c9f5d5be307b74264  05bp_six_site_meteorology_batch_READONLY.py
12ff4ba55b6ff1b80d139815bd9d333c69199d083951229dd18eaf4181d31dd2  05bq_four_site_humidity_and_special_shadows_READONLY.py
67ecfb0dbfeda1599986de7d995aadf581570022450b5c5055fae6cc8a1f30cb  05br_nine_site_jpf_forcing_variable_qc_READONLY.py
83555cd1b1ec81c6b42410fa5cee1327292862b104f03b4b50afda57e222baa2  05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py
24785ec8a248491a08d017d60b5280c4fbc6899bc3434b80549ea15cb1eaee09  05bt_45_field_companion_artifacts_and_era_lag_sensitivity_READONLY.py
5bea1fda9f215c38b773ac033478fda8d2cbdd3092f5247e0a5e03499eb8894f  05bv_iridis_readonly_batch_05br_05bs_05bt.sh
d706f752e535c244ba1a22335620d875f2e479d90b4f7c95cfae1d9254a9c3f0  test_05bp_six_site_batch.py
4f1a09770207de5474baedced9cedd1b01c328836e5fa928fe68c3e958c3e4ad  test_05bq_four_site_humidity_and_shadows.py
2d485fe31d4fdc46b1df3d214da46fdb0056f958a0e1408c33bdf6b65b970dd7  test_05br_nine_site_forcing_variable_qc.py
a57268662f9d2fe8cb5797ff1d630bf127814c3ba6090df1435e6d84223b7ccf  test_05bs_tom_tgf_forensics.py
7d670a2d401aa8c3ca61e34c474c2c264d0b35b04f608a8d89678ecfa29ffd03  test_05bt_companion_and_lag.py
EOF
)
bash "$D/05bv_iridis_readonly_batch_05br_05bs_05bt.sh" "$D" 2>&1 | tee "$HOME/japanflux_stage05bv/console_${C:0:12}.log"
sha256sum "$HOME/japanflux_stage05bv/console_${C:0:12}.log"
```

请把从 `STAGE05BV RUN` 开始到最后 `sha256sum` 的**全部输出**贴回。我会核对硬性和软性检查，再根据 05BT lag 的逐组结果完成 D8 的审阅表。

## C. 回滚与边界

本批命令只在 `~/japanflux_stage05bv/` 下新建代码目录和带时间戳的运行目录，不改写任何已有文件；删除这两个目录即可完全回滚。原始 ZIP 和 Stage04–05BQ 的既有输出只被读取和计算哈希，不会被修改；生产 forcing、PFT、土壤、模型案例、Slurm 和 AD400 完全不涉及。

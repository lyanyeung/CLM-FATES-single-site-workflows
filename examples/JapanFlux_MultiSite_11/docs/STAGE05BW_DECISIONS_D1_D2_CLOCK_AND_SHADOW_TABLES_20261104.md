# Stage05BW：D1/D2 批准、时钟决定与影子表（2026-11-04）

## 1. 用户决定（2026-11-04）

- **D1 降水：批准**按审阅包建议处理。Api、Tak、Tmd 用 `P_F(t+1h)/3.6`；Yms 在 JapanFlux2024 雨量计 QC0 时段用该雨量计值，其余时段同样用 `P_F(t+1h)/3.6`。
- **D2 微小负值：批准**规则 `−1e-12<P<0 → 0`、`−1e-9≤VPD<0 → 0`，适用于已审计的 5,099 个单元格。
- **时钟问题：用户授权由我决定。** 决定如下（C1–C4）。

## 2. IRIDIS Stage05BV 实际结果（操作员日志）

操作员在 `login6003`（Python 3.10.21）运行了锁定 commit `4dfb0231` 的批处理，12 个文件的 SHA-256 全部通过，self-test 与 17 项单元测试通过。运行目录为 `/home/ly3n24/japanflux_stage05bv/run_20261104T045402Z_1120583`，控制台日志 SHA-256 为 `dd2e4d18434ff73676f24b33173512c2c925f6848449410ef6f6c2bb074ec54e`。**6 项检查全部为 true**：

- 05BR 伪影表 `0e61a274…` 与本地一致；整数指纹 `fcaa23c0…` 与本地一致。
- 05BS 对 05BP/05BQ 三份文件逐字节一致；05BS 指纹 `e1644c00…` 与本地一致。
- 05BT companion 表 `bac8381e…` 与本地一致（94 行，原 45 + 新 49）。
- 05BT lag 在 UTC+9 下复现了所选 45 值的规范哈希 `5fd381dd…`。

因此，此前在本地原件上得到的 05BR/05BS/05BT 结论**已在 IRIDIS 上逐位复现**。

05BT lag（`offset_sensitivity_17_groups_HOLD.tsv`，SHA-256 `070732bc…`）中各组 QC2 背景离散度最小的偏移：

| 最优偏移（分钟，本地时间−偏移=UTC） | 组数 | 组 |
|---:|---:|---|
| 600（UTC+10） | 10 | Fjy PA×2、Khw LW、Khw PA 2011、Tef LW 2011、Tmd LW、Tmd PA 2005/2011、Yms LW×2 |
| 630 | 3 | Khw TA、Tef LW 2022、Tmd PA 2022 |
| 660 | 2 | Tmd TA、Yms PA 2005 |
| 570 | 1 | Khw PA 2005 |
| 480 | 1 | Yms PA 2011 |

15/17 组的最优偏移 ≥ 600 分钟，即同发行 ERA 比本地时间晚约 1 小时。这与另外两项证据一致：降水精确晚 1 小时（Api/Tak），短波质心晚 55–58 分钟（9 站）。例外的两组都是 PA，PA 日变化小，偏移的判别力弱。

## 3. 时钟决定

| 编号 | 决定 | 依据 | 可逆性 |
|---|---|---|---|
| **C1** | Tef/Tmd 采用 UTC+9，不改时间标签 | 晴天短波、跨站伪影标签一致、README 模板换版；Tef 另有与 JapanFlux2024 气温逐值相同 | 若生产方另有说明，再改 |
| **C2** | Tom 的 TA、RH、VPD、SW：t 时刻取塔测标签 t+1h 的值（需为 QC0）；否则保留 JapanFlux2024 在 t 的 ERA5 校正值（与其 QC1 填补相同）。P、LW、PA、WS 不变 | 晴天短波晚 +50（HH）/+55（HR）分钟；Tom 气温相对原始 ERA5 比 Tgf 多晚约 50 分钟；QC1 单元格 100% 等于校正 ERA5（TA/RH/VPD/SW/LW/PA/WS）；P 混有 ERA 成分，且 1 小时相位对水量平衡影响很小，故不移 | 影子表保留原值与标签，可完全回退 |
| **C3** | 9 个 JPF 站所有 QC2 单元格改取同发行 ERA 在 t+1h 的值；Api/Tak/Tmd/Yms 的降水已在 D1 中包含同样的前移 | 见第 2 节三项证据 | 同上 |
| **C4** | DATM 时间标签维持项目约定（起点标签、`linear`、offset 0） | 与本实验其他站点保持可比；改动应作为项目级决定，并在 CTSM 中单独验证 | 不涉及数据 |

**C3 对 45 个字段的影响。** 纠正 ERA 时间后，伪影在影子表中整体提前 1 小时：原 45 个位置变为正常的 ERA 值，伪影转移到提前 1 小时的 QC2 单元格，标签为 `HOLD_ERA_ARTIFACT_SHIFTED`。这些新位置的候选值，正好等于 05BT 在 600 分钟偏移下算出的“格点 + QC2 中位残差”：格点取真实时刻（本地−9 h），残差在 ERA 滞后已被对齐的情况下计算，不再混入日变化。您选定的方法没有改变，只纠正了时间对齐。数值仍需您逐组确认（D8），下一批 IRIDIS 命令会打印这 17 组在 540/600 分钟下的候选值和边界跳变。

## 4. 本地影子表结果

本地在 SHA 一致的原件上运行（8 分 31 秒，峰值内存 0.88 GB），输出在 WSL `~/jp11_local_runs/05bw_v1/`，不上传 GitHub。整数指纹为 `2365a73416b9908f0d092b5e18f54dd317d555b8e1609eb9093d8fc9c2b76f9d`，摘要 SHA-256 为 `7e84c4db87b8d3c5240ef25fdf50a3d89082d5e8fa543cf80e9cdc41381dad1b`。每张影子表（`<site>_decided_shadow_HOLD.tsv.gz`）的每个单元格都保留原值、原 QC 和来源标签；未改动的单元格逐字节等于原始字符串。

**时间纠正的效果**（晴天 SW 质心相对 UTC+9 天顶辐射的中位偏差，分钟）：

| 站 | 塔测 | 同发行 ERA，纠正前 | 同发行 ERA，C3 纠正后 |
|---|---:|---:|---:|
| Api | −3.4 | +56.6 | −3.4 |
| Fhk | −5.4 | +55.2 | −4.8 |
| Fjy | −1.9 | +55.4 | −4.6 |
| Khw | +5.0 | +56.7 | −3.3 |
| Spp | −1.2 | +56.6 | −3.4 |
| Tak | +4.0 | +55.5 | −4.5 |
| Tef | +3.9 | +58.3 | −1.7 |
| Tmd | +2.4 | +55.9 | −4.1 |
| Yms | +1.1 | +56.5 | −3.5 |

Tom 塔测 SW：C2 前 +49.8 分钟，C2 后 −10.2 分钟（902 天）。60 分钟是最接近实测偏移约 50 分钟的整半小时步长；若只移 30 分钟，会留下约 +20 分钟的偏差。Tgf 不移，仍为 +1.9 分钟。

**D1 降水**（各年平均，mm/年）：

| 站 | 原 JPF | 影子表 | JapanFlux2024 发表值 | 说明 |
|---|---:|---:|---:|---|
| Api | 5,423 | **1,506** | 1,509 | 原始 ERA5 |
| Tak | 8,918 | **2,477** | 2,483 | 原始 ERA5 |
| Yms | 5,006 | **1,378** | 1,384 | 420,768 行全部来自 JapanFlux2024 雨量计（QC0） |
| Tmd | 4,717 | **1,310** | 1,738 | 原始 ERA5，比发表值低约 25%；要改用实测，需要正确的 JapanFlux2024 JP-Tmd 包（本地只有 JP-KaL），属新数据获取，未执行 |

**D2**：恰好 5,099 个单元格（Tom P 4,322 + VPD 753；Tgf P 3 + VPD 21）。Tom 的 VPD 随 C2 一起前移，标签为 `C2_TOM_TOWER_SHIFTM60+D2_TINY_ZERO`；其中 747 个落在 2011–2013 年，复合标签为 `HOLD_D3_TOM_RH_DRIFT+…+D2_TINY_ZERO`。

**C3 改动的 QC2 单元格**：各站各变量从数百到数十万个。例如 Khw 的 PA 有 385,722 个、LW 有 169,138 个；Tmd 的 PA 有 333,063 个。这些单元格都只是改取同发行 ERA 一小时后的值。

**仍为 HOLD 的单元格**：
- `HOLD_ERA_ARTIFACT_SHIFTED` 共 **88** 个。
  - **45** 个是原字段前移后的位置：PA 27（Fjy 6、Khw 6、Tmd 9、Yms 6）、TA 6、LW 12，数目逐一对应。
  - 另有 **43** 个伴随单元格：WS 12、VPD 9、P 18、夜间 SW 4。Yms 的 6 个降水伴随单元格已由雨量计实测替代。
  - 抽查 Khw 2005-08-12：03:00 起已为正常的 ERA 值（PA 97.844 kPa），伪影位于 01:30–02:30。
- 其余 HOLD 标签：
  - `HOLD_D7_WS_STUCK`：Api 560、Khw 48、Tak 2,592、Tef 597、Tmd 1,428。
  - `HOLD_D9_VPD_GE_ES`：Fjy 7、Tef 1、Yms 15。
  - `HOLD_D11_TEF_PA_2023`：16,292。
  - `HOLD_D6`：Spp 1。
  - `HOLD_D4`：Tgf 6 个字段。
  - `HOLD_D3`：Tom 2011–2013 年 RH/VPD 各 52,608；Tgf RH>100 处的 RH/VPD 各 9,493。

## 5. 下一步：上传 Yms 包并在 IRIDIS 复现影子表

**第 1 步：在本地 WSL 运行**（只上传一个文件，不覆盖已有文件，本地和远端各核对一次 SHA-256，需要输入一次 IRIDIS 密码）：

```bash
set -euo pipefail
C=2099438fe6074354ba878b40b975271b43f878c2; T="$(mktemp -d)"
curl -fLsS "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$C/examples/JapanFlux_MultiSite_11/scripts/stage05/05by_upload_jf2024_yms_package_LOCAL_WSL.sh" -o "$T/05by.sh"
echo "13b8c326f188609c8cc5ae0df6ed15c9d31979a57173abf452782bbad5f0abbb  $T/05by.sh" | sha256sum -c -
bash "$T/05by.sh"
```

**第 2 步：在 IRIDIS6 运行**（串行、只读；内容为 05BW self-test 和单元测试、11 站影子表、与本地指纹比对，并打印 05BT 在 540/600 分钟偏移下的 17 组候选值，供 D8 审阅）：

```bash
set -euo pipefail
C=2099438fe6074354ba878b40b975271b43f878c2
B="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$C/examples/JapanFlux_MultiSite_11/scripts/stage05"
mkdir -p "$HOME/japanflux_stage05bx"; D="$HOME/japanflux_stage05bx/code_${C:0:12}"
[ -e "$D" ] && { echo "STOP: $D already exists"; exit 1; }; mkdir "$D"
for f in 05bq_four_site_humidity_and_special_shadows_READONLY.py 05br_nine_site_jpf_forcing_variable_qc_READONLY.py 05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py 05bw_decided_corrections_shadow_tables_READONLY.py 05bx_iridis_readonly_batch_05bw.sh test_05br_nine_site_forcing_variable_qc.py test_05bs_tom_tgf_forensics.py test_05bw_decided_corrections.py; do
  curl -fLsS "$B/$f" -o "$D/$f"
done
(cd "$D" && sha256sum -c - <<'EOF'
12ff4ba55b6ff1b80d139815bd9d333c69199d083951229dd18eaf4181d31dd2  05bq_four_site_humidity_and_special_shadows_READONLY.py
67ecfb0dbfeda1599986de7d995aadf581570022450b5c5055fae6cc8a1f30cb  05br_nine_site_jpf_forcing_variable_qc_READONLY.py
83555cd1b1ec81c6b42410fa5cee1327292862b104f03b4b50afda57e222baa2  05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py
de4c70f723cd0e68725b04f36858ddf1478048ad7d444655f46c054171596c67  05bw_decided_corrections_shadow_tables_READONLY.py
6ecee5231300d90fc62db9df264d408b2b8464965c0fd156d1d18ae79f239966  05bx_iridis_readonly_batch_05bw.sh
2d485fe31d4fdc46b1df3d214da46fdb0056f958a0e1408c33bdf6b65b970dd7  test_05br_nine_site_forcing_variable_qc.py
a57268662f9d2fe8cb5797ff1d630bf127814c3ba6090df1435e6d84223b7ccf  test_05bs_tom_tgf_forensics.py
099638f402587e1921fa742af2f2213fec7aba060b7e0a3855c5653ed0e745e4  test_05bw_decided_corrections.py
EOF
)
bash "$D/05bx_iridis_readonly_batch_05bw.sh" "$D" 2>&1 | tee "$HOME/japanflux_stage05bx/console_${C:0:12}.log"
sha256sum "$HOME/japanflux_stage05bx/console_${C:0:12}.log"
```

预期结果：`STAGE05BX CHECKS` 中 `05BW_D2_5099` 和 `05BW_fingerprint_equals_local` 都为 true。指纹包含每张影子表未压缩内容的 SHA-256，因此指纹一致即表示 11 站全部单元格与本地逐位相同。

## 6. 仍待用户决定的事项

| 编号 | 状态 | 说明 |
|---|---|---|
| D8 | 等 05BX 打印的 17 组候选值 | 前移后伪影位置的候选值 = 05BT 600 分钟偏移下的“格点 + QC2 中位残差” |
| D13 | HOLD | 43 个伴随单元格（WS 12、VPD 9、P 18、夜间 SW 4）；建议用 QC2 相邻值桥接 |
| D3 | HOLD | Tom 2011–2013 年 RH 漂移；Tgf RH>100（以约 1% 过冲为主） |
| D4 | HOLD | Tgf 2003-12-31 23:30 整行置零（4 个字段）；2015-12-15 14:30 SW=−70 |
| D6 | HOLD | Spp 2009-07-15 08:30 的 60.5 mm |
| D7 | HOLD | 5 个站共 5,225 个 WS 卡值单元格 |
| D9 | HOLD | 23 个 VPD≥es 单元格 |
| D11 | HOLD | Tef 2023 年 PA 偏高 1.34 kPa |
| Tmd P | 已按 D1 执行，存在已知偏差 | 原始 ERA5 比发表值低约 25%；要改用实测，需要正确的 JapanFlux2024 JP-Tmd 包（新数据获取，需您同意） |

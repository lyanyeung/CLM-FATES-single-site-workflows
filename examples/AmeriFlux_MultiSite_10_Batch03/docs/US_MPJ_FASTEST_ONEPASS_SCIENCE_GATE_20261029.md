# US-Mpj — fastest remaining Batch03 station: one-pass full-site scientific meteorology gate

**2026-10-29, next operator task.** US-MtB and US-MMS now have numerically complete isolated research-only candidates. US-NR3 is reserved for the advanced model; US-Me6 and US-NR1 now have separate Claude handoffs. Continue **US-Mpj only**, without replaying earlier 2014 source repairs.

## Known actual IRIDIS6 scientific results

- Original FLUXNET-1F release: \`AMF_US-Mpj_FLUXNET_2008-2025_v1.3_r1\`; 2008–2025 = **315360 native 30-minute NOLEAP model records**.
- Exact operator-applied **Stage13O** succeeded on 2026-10-26 21:07 UTC: isolated signed source directory:
\`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13o_Mpj_20HH_operator_approved_ERA_RH_20261026T210746Z_5c3c8653\`.
- Both original October 2014 source \`VPD_F_QC=1\` ten-HH episodes have original source measured \`VPD_F_QC=0\` bookends and successfully applied scoped paired ERA RH at original tower T/P (source is ERA-derived, not measured tower RH). 20 source HH, **17 changed VPD_USE+QBOT HH**, 3 previously operator-accepted Stage07 centers numerically unchanged. Two original 2018-02-02 low-but-positive RH VPD slots 17:30=11.261 and 19:00=9.178 hPa were explicitly preserved. Prior Feb2020 temperature correction 2020-02-11 06:30=1.1795°C preserved. Stage13O full re-read+SHA audit was successful on IRIDIS6.
- No PFT, ZBOT, surface, DATM, CIME, Slurm or Post-v5 production decision has been granted. The user's already updated observed-PFT table is preferred; do not redo source literature research.

## ONE efficient action remaining

**[One-pass Python Stage14D: complete-source signed SHA and all 315360 model HH](../scripts/stage14/14d_US_Mpj_final_315360_science_gate_READONLY.py)** does an independent, *no-change* whole-site audit of the **actual latest Stage13O** against original Stage07:
1. Stage13O original research receipt SHA and every output SHA, original Stage07 parent SHA, 315360 rows × 10 model fields, exact 2008–2025 NOLEAP 30-minute chronology.
2. Only **17 VPD/QBOT** native source timestamps differ between Stage13O and original Stage07. The 3 old original 2014 centers, 2 2018 preserved original VPD, and 2020 corrected TA stay unchanged. Every other source variable unmodified.
3. For all 315360 HH: check all ten model fields finite, \`TBOT = TA_USE+273.15 K\`, \`QBOT = 0.622*e_Pa / (PSRF−0.378*e_Pa)\`, \`e_hPa = es_water(TA_USE)−VPD_USE\`, VPD nonnegative and at/below water saturation, pressure bounds, negative winds/rainfall/radiation, water RH <5% warning, and subzero ice RH >100% caution. Emits a grouped **annual** summary and only up to first 35 console exception rows, plus new standalone SHA-receipted CSVs.
4. **Interpretation:** if full-site physics and gap audit pass, scientific *meteorology numerical* review can close. Any warnings need human classification once, not 1–2 records per new Stage. This does **not** by itself prove sensor-provenance independence or validate PFT/surface/ZBOT. If output flags source anomalies, group by year/episode and treat science separately from numeric completion.

**No Stage14D IRIDIS6 execution has been reported yet**. No changes to any previous source, shadow, science approval, model case, PFT/surface or Slurm.

GitHub command example (use new pinned SHA from current GitHub script ref):

\`\`\`bash
(
 set -euo pipefail
 F="$HOME/US_Mpj_final_onepass.py"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/346720f0c665dcfeabaaa26918f2a039e606fca3/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14d_US_Mpj_final_315360_science_gate_READONLY.py" -o "$F"
 test "$(git hash-object "$F")" = "f1bef658ebd1c5aec899b4fc12c6297678f778c7"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_Mpj_final_onepass.log"
)
\`\`\`

The SHA-pinned Python audits the latest existing result, and writes only a new \`reports/us_mpj_315360_science_gate_READONLY_*\` folder. The user makes the later model-admission decision.

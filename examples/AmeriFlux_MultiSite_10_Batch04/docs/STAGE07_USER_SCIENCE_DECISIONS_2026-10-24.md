# Batch04 Stage07 user decisions — retain native US-Ton QC0; compare temperature neighbours

**User decision, 2026-10-24 (after successful Stage06).** These rules supersede automatic interpretation of the Stage05 proposal, but **do not mutate or retroactively approve** Stage05 source/patch files.

1. **US-Ton**: retain **native VPD_F where original VPD_F_QC=0** unless the actual original `TA_F,VPD_F` pair is physically impossible (negative VPD/negative implied water vapour pressure, nonfinite or missing variables). Original source `RH>100%` alone is insufficient reason to discard a valid native VPD, particularly when VPD=0 denotes saturation. A truly physically invalid native QC0 entry goes to HOLD/review; do not automatically adopt the Stage05 ERA candidate. Preserve all source values in immutable FLUXMET/ERA originals. Any corresponding RH field must remain internally consistent with the retained VPD or be explicitly tracked as a distinct derived-RH decision; never silently keep one half of an ERA RH+VPD pair while replacing the other.
2. **US-Syv**: defer the unresolved ERA-source physically invalid humidity pairs (419 cases) and related source-RH decisions to later scientific review; **do not** automatically repair from those invalid ERA pairs.
3. **US-SP1, US-Syv, US-Ton — 331 temperature-disagreement / invalid tower-T holds**: compare each flagged site's original tower `TA_F` to actual original preceding and following half-hourly `TA_F`, and corresponding paired ERA `TA_ERA`, with exact native time keys and original `TA_F_QC`. If surrounding trustworthy tower data support the present tower value, **retain the tower TA_F**, even if ERA differs by over 8°C. If the tower sample itself is impossible/missing or the surrounding context is ambiguous, HOLD it for genuine science review. This decision pertains to **TA selection**, not blanket authorization for an ERA-RH replacement on the same timestamp.
4. **Four stations? No — exactly three priority Batch04 stations** and their 210 Stage06 VPD edges: attribute added jumps to source-side vs ERA reconstruction boundaries. Do not threshold-smooth all edges, and keep old Stage05 candidate immutable for full comparison.

## Operator verified Stage06 context

- **US-Ton**: original native `VPD_F_QC=0` would be modified at 2,259 reconstructed humidity times; 179 VPD flagged edges; most extreme 2001-05-18 05:30→06:00 jump went from 0.986 to 16.404455 hPa (+15.418455).
- **US-SP1**: 19 flagged edges; notably 2008-03-23 07:00→07:30 jump 0.619→9.211947 hPa (+8.592947).
- **US-Syv**: 12 flagged edges; notably 2007-05-12 19:00→19:30 jump 0.686→5.542211 hPa (+4.856211).
- 754 distinct Stage05 HOLD entries: **331 temperature discrepancy/invalid tower T**, **419 ERA pair physics**, **4 ERA RH interval**.

The purpose of Stage07 is to quantify how many US-Ton original QC0 values are physically good, recommend when site TA is supported by neighbours, and compare exact **raw Stage05** vs **QC0-protection filtered** VPD jump metrics without committing repairs.

**Not approved**: any original overwrites, processed_v5 forcing release, Post-v5, DATM, CIME or spin-up.

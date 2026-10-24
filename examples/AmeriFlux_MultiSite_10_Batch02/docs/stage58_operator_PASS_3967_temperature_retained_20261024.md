# Stage58 operator PASS: Batch02 original EC temperature provenance

Date 2026-10-24. Based on the operator's full IRIDIS6 stdout (not uploaded source CSV).

Stage58 pinned GitHub blob `dbb270085e5ed60570090145d37e37037b0d0dfc` matched the retrieved file. Python syntax, self-test, source check, and AUDIT passed.

Report on IRIDIS6:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage58_63_manual_T_approved_3967_T_total_20261024T110141Z_e65bde6c`

- 3,904 original tower TA_F observations accepted under |TA_F−ERA5 T2m| ≤8°C.
- 63 original tower extreme-cold TA_F observations independently manually accepted after Stage57 evidence (EML 27; GLE 6; ICt 30).
- Combined: **3,967 / 4,884** original tower temperatures retained, each with numerically valid paired external CDS ERA5 RH and recomputed water-reference VPD and QBOT.
- US-Ho1: **917** still HOLD for provisional source UTC_OFFSET/time alignment.
- Per-site retained / total: US-EML **1,327 / 1,327**; US-GLE **295 / 295**; US-Ho1 **0 / 917**; US-ICh **169 / 169**; US-ICt **2,176 / 2,176**.
- Every original humidity/phase scientific HOLD remains. The separately staged Stage53 444 original RH=0/>100 repairs remain outside this cohort; Stage54 confirmed zero site-local-time overlap.
- **No original source, DATM forcing, CIME, Slurm, simulation or model-input edits.** This is a temperature-only science decision in an isolated staging ledger.

Next: read-only water-reference vs ice-reference saturation sensitivity for 3,967 numerically valid subzero humidity candidates, and independently verify US-Ho1 original release UTC offset. A subsequent full source-fidelity/Stage48 anomaly coverage and forcing integration gate is still required before model run. Not all Batch02 humidity issues are resolved by these 5,328 staged site/timestamp records.

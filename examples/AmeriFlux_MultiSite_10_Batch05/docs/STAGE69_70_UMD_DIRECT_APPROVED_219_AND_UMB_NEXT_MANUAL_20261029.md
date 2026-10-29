# Batch05 US-UMd direct user-approved repair → Stage69, then US-UMB manual Stage70

On 29 October 2026, the investigator explicitly instructed: **all US-UMd implied RH <0% anomalies directly repair without a further candidate approval cycle; move to the next site**.

The human supplied full original US-UMd records for 6 Stage63 original P2/P3 events (15 native HH). All 15 have original `TA_F_QC=0` (source measured TA) and `VPD_F_QC=1` (source filled VPD), and their calculated RH is physically negative. The source reference is Stage45-pinned original FLUXMET_HH ZIP SHA256 `27095ccd71a1c28cee5e730ca2ad99d0acb6fba7a4be07ffaa8cff7a41f2e3c5`.

## Direct user-approved repair rule

For each of the exact six original Stage63 episodes, preserve original source-measured TA, original VPD and QC lineage; calculate source-neighbor RH immediately before and after each negative-RH event using original source TA_F/VPD_F. Require `0 <= neighbor RH <=100` and original source neighbor `VPD_F_QC=1`. Interpolate RH linearly across the invalid HH and derive repaired `VPD = 6.112 * exp(17.67 * T/(T+243.5)) * (1-RH/100)` hPa at original measured T. The operator approved this direct source RH interpolation policy during Stage68 review, with no further per-event holds.

The Stage69 script checks the exact unchanged original Stage63 15HH/6 episodes, Stage27 original US-UMd 15 source values/T/VPD/QC, historical Stage62 **204 approved source-derived overlay rows** and SHA; it creates a **new 219-row versioned approved repair overlay** preserving the original 204 rows byte-for-byte in CSV fields and adding precisely 15 direct-user-approved US-UMd records. This is **NOT** a merely tentative candidate science decision. Its application is within the approved data-repair overlay. As with all prior versioned overlays, it does not overwrite the original AmeriFlux ZIP, change historical source QC flags or silently submit new production DATM/CIME/Slurm jobs.

Prior source-derived RH/VPD neighbors for the 6 events were reviewed: E0001 201504301000; E0002 201505010830–0900; E0003 201505040900–0930 (rain); E0004 201505041730; E0005 201505050730–0930; E0006 201505060730–0900. The numerical repair method is direct human-approved even though the bracketing VPD itself is source QC1, **not measured RH**.

**After successful Stage69 operator execution**: historical Stage63 1565 remaining original P2/P3 HH → 1550; 479 events → 473; 9 remaining P2/P3 sites → 8 (US-UMd original P2/P3 fully approved). Historical Stage63 files stay immutable snapshots.

## Next station US-UMB

Stage63 has **8 original episodes, 22 remaining native P2/P3 half-hours** for US-UMB, plus one original HH already in previous 204 approval overlay. Stage70 reads the original `US-UMB/forcing/raw/AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5/AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv` (US-UMB uses **FULLSET**, not FLUXMET). It first checks all 23 historical US-UMB Stage27 original flagged source native TA, VPD, QC exactly; then prints each remaining episode's flagged HH and ±3h original native timestamp context with tower TA/QC, VPD/QC, implied RH, paired source ERA, precipitation and SW. No data modifications or auto-science decisions for US-UMB.

## GitHub code and SHA

- [Stage69 direct source-repair approved 219](../scripts/stage69/69_US_UMd_15_negative_RH_direct_user_approved_219.py), commit `ce33ae843a59b05d63a93b9f37332db99b4a6ab9`, blob `0205f9433b44fc414c6eda79330fc9ff0437a315`.
- [Stage70 US-UMB 8 event/22HH read-only original review](../scripts/stage70/70_US_UMB_8events_22HH_original_context_print_READONLY.py), commit `b526a8f7773221e8f7f8853360f527b8c1b3db68`, blob `641b5da52040ce8fc6a0c766fad0aeaeed33a2be`.
- [Combined SHA-pinned one-line IRIDIS6 launcher](../scripts/stage71/run_stage69_UMd_direct_approve_and_stage70_UMB_manual_iridis6.sh), commit `5dbf19da8603962079b4ede901eb9691cb219797`, blob `aa543ba82633add823a239424bdf03e1cf016806`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/5dbf19da8603962079b4ede901eb9691cb219797/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage71/run_stage69_UMd_direct_approve_and_stage70_UMB_manual_iridis6.sh" -o "$HOME/run_stage71_UMd_UMB.sh" && test "$(git hash-object "$HOME/run_stage71_UMd_UMB.sh")" = "aa543ba82633add823a239424bdf03e1cf016806" && bash "$HOME/run_stage71_UMd_UMB.sh"
```

**Current status:** GitHub code and pinned SHA for the launcher verified; IRIDIS6 operator Stage69/70 execution not yet reported. Do not count site as actually done before Stage69 success output. Copy the resulting Stage69 approval summary and Stage70 source event rows to ChatGPT for subsequent human review and any approved US-UMB direct repair.

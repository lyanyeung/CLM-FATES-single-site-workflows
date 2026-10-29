# AmeriFlux Batch05 — Stage64 US-Whs original one-HH manual audit

Stage63 actually completed 29 October 2026 at 02:53 UTC: 1,565 original P2/P3 native half-hours remain over nine sites and 479 original events, in addition to 46 P1 HOLD and ten RH saturation platform records. **US-Whs has only ONE original P2/P3 flagged HH** and zero earlier 204-overlay repairs, zero P1 HOLD, zero RH saturation platform HOLD.

The user requested **single-event human review** rather than a large new batch repair for sites with only a handful of anomalies.

[Stage64 single-event Python](../scripts/stage64/64_US_Whs_one_anomaly_original_before_after_manual_review_READONLY.py), commit `30a0dc9ef01b32ac388a289af5b7a03cfdd0c25c`, Git blob `a1e818105c008648eec8062265cdc23285ff82a7`.

[Stage64 launcher](../scripts/stage64/run_stage64_Whs_oneHH_iridis6.sh), commit `ae71126c78f67a921d7f4d53545540061d824cf1`, Git blob `c4f4f1c98e52f6602cfec257d4a11d2e399ce08d`.

Read only original FLUXMET ZIP at `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Whs/forcing/packages/AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1.zip`, pinned to the existing Stage45 original archive SHA256 `0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767`.

The target native half-hour is **read** (not guessed) from Stage63's single US-Whs remaining native HH, then checked against the actual Stage27 historical original site time, tower TA/VPD and QC. Output is original source 3 hours before through 3 hours after (13 HH) with original RH and RH inferred from original T/VPD; selected original tower TA, VPD QC; MDS and product processed ERA companion fields; and P, SW, LW, WS and pressure. Prints each row and original immediate-neighbor VPD jumps. No external ERA5-Land is downloaded, and source processed ERA fields are not considered independent sensor data.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ae71126c78f67a921d7f4d53545540061d824cf1/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage64/run_stage64_Whs_oneHH_iridis6.sh" -o "$HOME/run_stage64_Whs.sh" && test "$(git hash-object "$HOME/run_stage64_Whs.sh")" = "c4f4f1c98e52f6602cfec257d4a11d2e399ce08d" && bash "$HOME/run_stage64_Whs.sh"
```

Run status: GitHub source/launcher pinned, IRIDIS6 operator execution not yet reported. Full source never edited; previous 204 versioned repair candidate overlay intact and not promoted to DATM forcing. A sensor hypothesis or replacement value, if any, requires explicit review of printed 13 HH before approval.

# AmeriFlux Batch05 — Stage60 verified MDS-fill anomaly and Stage61 unapproved candidate

## Verified user IRIDIS6 Stage60 execution, 28 October 2026

Original Stage60 output:
`/home/ly3n24/ameriflux_batch05_stage60/wjs2018_exact_original_MDS_QC_20261028T234456Z_908965`.

Actual operator results:
```text
STAGE60 SOURCE VERIFIED
STAGE60 SELF-TEST PASS
STAGE60 SUCCESS | US-Wjs 49 HH original MDS source comparison, 30 HH 2018 science HOLD; prior 174 intact
STAGE60 2018 HOLD 30 HH MDS_QC_COUNTS {"1": 30}
STAGE60 2018 HOLD 30 HH MDS_AND_SELECTED_EQUAL_WITHIN_0.002 30 /30 MAX_ABS_DIFF_hPa 0.000000
STAGE60 2018 HOLD NEGATIVE_RH source_SELECTED 4 source_MDS 4
STAGE60 2018 HOLD SOURCE_PRECIP_TOTAL 0.0 VALID_SOURCE_RECORDS_NO_INDEPENDENT_QC
STAGE60 QC0 LEFT_ANCHOR MDS_QC 0 RIGHT_ANCHOR MDS_QC 0
```

Original source VPD_F equals VPD_F_MDS at all 30 VPD-QC1 HH. These are selected MDS-filled VPD, not independent measured tower RH. Implied relative humidity from original tower TA_F and MDS VPD is physically negative at 2018-03-12 07:00 (-3.515%), 09:00 (-21.503%), 09:30 (-24.065%) and 10:00 (-3.592%). Across the 15-hour period, MDS-derived VPD is artificially sustained around 5.3 hPa for many hours and then spikes to 7-8hPa while no source RH field is provided.

The original 2018-03-11 19:00 anchor is QC0 RH 100% VPD 0 and the 2018-03-12 10:30 anchor is QC0 RH 92.127% VPD 0.672. Independent downloaded ERA5-Land RH is 33.237pp and 33.906pp lower than original source tower RH at the two boundaries, so replacing with raw ERA5-Land RH creates large artificial edges. ERA5-Land anchor-bias adjustment clipped RH to 100% for 28/30 original half-hours. Full 15.5-hour straight source QC0 RH interpolation instead produces numerically smooth VPD but **does not establish true humidity in the unobserved gap**, even when RH stays near saturation. No rain in source P_F is not definitive proof about fog, dew, or sensor behaviour.

## Stage61 action and science gate

[Stage61 Python](../scripts/stage61/61_Wjs2018_30HH_source_scoped_interpolation_candidate_READONLY.py), source commit `22d8a1fe5ce688e6b846ce1eafbff067190d5298`, Git blob `40bd1448f618cda0d03fd56c07692a6a8b9194e9`. [Hash-pinned launcher](../scripts/stage61/run_stage61_iridis6.sh), commit `ce1207df2f8624d6886726d7f06be9d11b10f002`, blob `b60f6c6bdffb5eed12c6ffb4553203d999bd244f`.

Stage61 creates one isolated **30-HH RESEARCH CANDIDATE**, explicitly **not scientist-approved**, using original-source RH endpoints and original tower TA_F, checks exact science/QC/MDS/negative-RH constraints against the successful Stage60 original 49-HH and Stage58 30-HH archived evidence, verifies the SHA of existing Stage56 174 records and no overlap, then exports 31 selected VPD boundary differences. It refuses any new >2hPa adjacent difference.

Run:
```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ce1207df2f8624d6886726d7f06be9d11b10f002/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage61/run_stage61_iridis6.sh" -o "$HOME/run_stage61.sh" && test "$(git hash-object "$HOME/run_stage61.sh")" = "b60f6c6bdffb5eed12c6ffb4553203d999bd244f" && bash "$HOME/run_stage61.sh"
```

Scientific use: the Stage61 30HH research candidate can be reviewed and explicitly approved by the scientist later. **No automatic 174+30=204 versioned merge**. Original 30HH Stage60 HOLD, 174 approved versioned overlay, source files, cases, forcing, CIME and Slurm must remain unmodified.

Status at publication: GitHub source and pinned launcher blobs checked. **Actual IRIDIS6 Stage61 syntax/self-test and execution not yet verified**.

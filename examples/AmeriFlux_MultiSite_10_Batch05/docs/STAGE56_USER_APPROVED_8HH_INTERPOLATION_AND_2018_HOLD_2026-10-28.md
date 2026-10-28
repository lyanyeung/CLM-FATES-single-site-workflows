# Batch05 Stage56 — exact user-approved eight native half-hours (28 October 2026)

The investigator approved **source-native RH linear interpolation** for exactly:
- **US-UMB 2009-05-19 11:00 and 11:30** (2 half-hours); RH anchors 10:30 97.193%, 12:00 95.568%; preserve original TA_F and recompute VPD using Magnus-water saturation vapour pressure.
- **US-Wjs 2021-11-02 06:00, 06:30, 07:00, 07:30, 08:00, 08:30** (6 half-hours); RH anchors 05:30 100%, 09:00 88.858%; preserve original TA_F and recompute VPD identically.

All eight original VPD records are QC1 with TA QC0, RH missing in the FLUXMET/FULLSET source fields. The anchor source RH fields coincide with the original TA/VPD-derived RH to within product rounding, but have not been independently sensor-qualified. The approval covers **versioned reconstructed candidates** and their method, **not** the promotion of filled RH to measured RH or automatic authorization of CLM-FATES production DATM forcing.

**US-Wjs 2018-03-11 19:30 through 2018-03-12 10:00** (30 half-hours) remains *science HOLD*. Original Wjs 2018 abrupt jump and 15-hour VPD QC1 source plateau must not be repaired by this 2021 approval. Independent ERA5-Land observations, if used later, must be distinguished from the original AmeriFlux `TA_ERA` and `VPD_ERA` processed companion columns.

## Stage56 output/protections

- SHA-pin the original Stage52 inventory, Stage53 comparison and Stage55 approved original US-UMB candidate data; re-read original raw source only after verifying file SHA.
- Exactly eight user-approved source-time candidate rows, unchanged native half-hour clock, original TA retained. Duplicate/unapproved target/overlap with prior Stage24 166 rows stops execution.
- Audit selected VPD over the 10 internal/outer boundary transitions; fail on newly computed adjacent jumps above 2 hPa.
- Verify protected 2018 30-HH VPD-QC1 source set and ensure none is in the new eight or the old 166 overlay.
- If a complete valid Stage24 166-row overlay and manifest are found, preserve its entire original set of 166 rows and generate a NEW combined 174-row overlay. Otherwise write only the eight-row candidate and explicitly state there is no 174-row merged version.
- Preserve original FLUXMET/FULLSET, existing Stage24 overlay, 46 P1 HOLD, 10 source RH plateau holds, other P2/P3 unapproved rows, Claude's separate cases, DATM/CIME/Slurm.

GitHub source:
- [Stage56 Python](../scripts/stage56/56_eight_user_approved_RH_interpolations_and_174_versioned_overlay.py); immutable source commit `b9c440cc82636b7fbab9a4f7c3c8ad3ff3436a47`; Git blob `ebcf495a3dfcf19bbf43f3362f53b6b8e204d56e`.
- [Stage56 IRIDIS6 launcher](../scripts/stage56/run_stage56_iridis6.sh); commit `359cfc8ae592e41a2fd71193efd5d9899ccf4f0d`; Git blob `e93ae4eaabfdb541e3d6b7dc39c0ca3ceea0631c`.

Run:

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/359cfc8ae592e41a2fd71193efd5d9899ccf4f0d/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage56/run_stage56_iridis6.sh" -o "$HOME/run_stage56.sh" && test "$(git hash-object "$HOME/run_stage56.sh")" = "e93ae4eaabfdb541e3d6b7dc39c0ca3ceea0631c" && bash "$HOME/run_stage56.sh"
```

Status: GitHub code and immutable hash-verified launcher committed; **actual IRIDIS6 Stage56 execution not yet confirmed**. No original forcing edits or Slurm jobs are authorized by this stage.
